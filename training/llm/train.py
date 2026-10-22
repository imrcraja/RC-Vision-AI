"""Train a tiny decoder-only Transformer from random initialization.

This is a research prototype, not a capable general-purpose assistant.
PyTorch is used only for tensor/autograd primitives; no pretrained weights,
tokenizer, model, or inference engine is downloaded or loaded.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, time
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F

class ByteTokenizer:
    """Reversible UTF-8 byte tokenizer; vocabulary is exactly 256 byte values."""
    vocab_size = 256
    def encode(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))
    def decode(self, tokens: list[int]) -> str:
        return bytes(max(0, min(255, int(t))) for t in tokens).decode("utf-8", errors="replace")

class CausalSelfAttention(nn.Module):
    def __init__(self, width: int, heads: int, dropout: float) -> None:
        super().__init__()
        if width % heads: raise ValueError("width must be divisible by heads")
        self.width, self.heads = width, heads
        self.qkv = nn.Linear(width, 3 * width, bias=False)
        self.proj = nn.Linear(width, width, bias=False)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, width = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        head_width = width // self.heads
        q = q.view(batch, length, self.heads, head_width).transpose(1, 2)
        k = k.view(batch, length, self.heads, head_width).transpose(1, 2)
        v = v.view(batch, length, self.heads, head_width).transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) / math.sqrt(head_width)
        mask = torch.ones(length, length, device=x.device, dtype=torch.bool).triu(1)
        scores = scores.masked_fill(mask, torch.finfo(scores.dtype).min)
        weights = self.dropout(F.softmax(scores, dim=-1))
        out = (weights @ v).transpose(1, 2).contiguous().view(batch, length, width)
        return self.dropout(self.proj(out))

class TransformerBlock(nn.Module):
    def __init__(self, width: int, heads: int, dropout: float) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(width)
        self.attn = CausalSelfAttention(width, heads, dropout)
        self.norm2 = nn.LayerNorm(width)
        self.ff = nn.Sequential(nn.Linear(width, 4 * width), nn.GELU(), nn.Linear(4 * width, width), nn.Dropout(dropout))
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        return x + self.ff(self.norm2(x))

class RCVisionLM(nn.Module):
    """Small decoder-only Transformer; all parameters start randomly initialized."""
    def __init__(self, width: int = 128, layers: int = 4, heads: int = 4, context: int = 128, dropout: float = 0.1) -> None:
        super().__init__()
        self.context = context
        self.token_embedding = nn.Embedding(256, width)
        self.position_embedding = nn.Embedding(context, width)
        self.blocks = nn.Sequential(*(TransformerBlock(width, heads, dropout) for _ in range(layers)))
        self.final_norm = nn.LayerNorm(width)
        self.output = nn.Linear(width, 256, bias=False)
        self.output.weight = self.token_embedding.weight
    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        _, length = tokens.shape
        if length > self.context: raise ValueError(f"sequence length {length} exceeds context {self.context}")
        positions = torch.arange(length, device=tokens.device)
        x = self.token_embedding(tokens) + self.position_embedding(positions)[None, :, :]
        return self.output(self.final_norm(self.blocks(x)))

def read_corpus(path: Path, tokenizer: ByteTokenizer) -> torch.Tensor:
    if not path.is_file(): raise FileNotFoundError(f"Corpus not found: {path}")
    raw = path.read_text(encoding="utf-8")
    if len(raw.strip()) < 100: raise ValueError("Corpus is too small; provide at least 100 non-whitespace characters.")
    ids = tokenizer.encode(raw)
    if len(ids) < 512: raise ValueError(f"Corpus contains only {len(ids)} UTF-8 bytes; at least 512 are required.")
    return torch.tensor(ids, dtype=torch.long)

def batches(data: torch.Tensor, batch_size: int, context: int, device: torch.device):
    max_start = len(data) - context - 1
    if max_start < 1: raise ValueError("Corpus must contain more bytes than context + 1.")
    starts = torch.randint(0, max_start, (batch_size,))
    x = torch.stack([data[i:i + context] for i in starts.tolist()]).to(device)
    y = torch.stack([data[i + 1:i + context + 1] for i in starts.tolist()]).to(device)
    return x, y

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True, help="UTF-8 text corpus you have permission to use")
    parser.add_argument("--output", type=Path, default=Path("artifacts/llm"))
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--context", type=int, default=128)
    parser.add_argument("--width", type=int, default=128)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    args = parser.parse_args()
    if min(args.steps, args.batch_size, args.context, args.width, args.layers, args.heads, args.checkpoint_every) < 1:
        parser.error("steps, batch-size, context, width, layers, heads and checkpoint-every must be positive")
    if args.width % args.heads: parser.error("width must be divisible by heads")
    random.seed(args.seed); torch.manual_seed(args.seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = ByteTokenizer()
    data = read_corpus(args.corpus, tokenizer)
    split = max(args.context + 2, int(len(data) * 0.9)); split = min(split, len(data) - 2)
    train_data, val_data = data[:split], data[split:]
    if len(val_data) <= args.context + 1: raise ValueError("Corpus needs a larger held-out validation section; add more text.")
    model = RCVisionLM(args.width, args.layers, args.heads, args.context).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    args.output.mkdir(parents=True, exist_ok=True)
    corpus_hash = hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    started = time.time(); last_loss = float("nan")
    print(f"Device: {device}; corpus bytes: {len(data)}; train: {len(train_data)}; validation: {len(val_data)}")
    print("Training from random initialization. No pretrained weights are loaded.")
    for step in range(1, args.steps + 1):
        model.train(); x, y = batches(train_data, args.batch_size, args.context, device)
        logits = model(x); loss = F.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
        last_loss = float(loss.detach().cpu())
        if step == 1 or step % args.checkpoint_every == 0 or step == args.steps:
            model.eval()
            with torch.no_grad():
                vx, vy = batches(val_data, min(args.batch_size, 4), args.context, device)
                val_loss = float(F.cross_entropy(model(vx).reshape(-1, 256), vy.reshape(-1)).cpu())
            checkpoint = {"format":"rc-vision-ai-byte-transformer-v1","step":step,
                "model_config":{"width":args.width,"layers":args.layers,"heads":args.heads,"context":args.context,"vocab_size":256},
                "model_state":model.state_dict(),"optimizer_state":optimizer.state_dict(),"seed":args.seed,
                "corpus_sha256":corpus_hash,"train_loss":last_loss,"validation_loss":val_loss,
                "elapsed_seconds":round(time.time()-started,2),
                "note":"Research checkpoint; not a general-purpose assistant."}
            target = args.output / f"checkpoint-{step:07d}.pt"; torch.save(checkpoint, target)
            metadata = {k:v for k,v in checkpoint.items() if k not in {"model_state","optimizer_state"}}
            (args.output / "latest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            print(f"step={step}/{args.steps} train_loss={last_loss:.4f} validation_loss={val_loss:.4f} checkpoint={target}")
    print("Finished. Loss is a research metric, not proof of useful conversational ability.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
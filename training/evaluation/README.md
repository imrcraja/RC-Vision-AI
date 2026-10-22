# RC Vision AI — red-team and sandbox evaluation

## Current threat model

The present LLM is a byte-level text generator. It has no tool-calling API, shell, browser, filesystem action API, or network permission. Its generated text cannot itself execute instructions. Therefore a prompt saying "escape the sandbox" cannot demonstrate a real escape: there is no agent/tool runtime to escape from yet.

## Checks included

Run:

```bash
python training/evaluation/sandbox_redteam.py
```

The static audit flags common network/process imports and shell/process calls in the training and generation source and verifies restricted checkpoint loading. CI runs this audit. It is a guardrail, not a full security boundary.

## Red-team plan before agent/tool integration

When a real agent runtime exists, test it in a disposable, network-disabled container with no secrets and a read-only base filesystem. Add explicit deny-by-default tool permissions, CPU/RAM/time limits, and an external supervisor. Test:
- direct and indirect prompt injection asking the model to ignore rules;
- requests to read files outside an allowlisted scratch directory;
- attempts to execute shell commands, start subprocesses, or open sockets;
- path traversal, symlinks, oversized outputs, and resource exhaustion;
- attempts to exfiltrate fake canary secrets (never real credentials);
- whether denied actions are blocked by the runtime rather than merely refused in generated text.

Record each test as blocked/allowed with logs. Never use real credentials or a production device for escape testing. Do not treat a refusal string as proof of containment.

## Model-size planning

The current 128-wide, 4-layer research configuration is under 1 million parameters, nowhere near a 700–1200 MB weight file. For FP32, 700–1200 MB of raw weights implies roughly 175–300 million parameters (decimal MB; actual file sizes vary). A 175M-parameter model needs much more suitable training data and compute than this repo's 7.5 KB smoke-test corpus and free CPU workflow. Optimizer states and activations increase training memory substantially. Do not scale the workflow blindly: first establish a rights-cleared corpus, GPU/compute budget, stable validation split, and checkpoint-resume support. A large checkpoint trained on a tiny corpus would mostly memorize it and still not be a capable assistant.

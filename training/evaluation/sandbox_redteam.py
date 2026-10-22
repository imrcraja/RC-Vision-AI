"""Static red-team guardrails for the current text-only research prototype.

This is NOT an operating-system sandbox or proof of security. It checks that
the current model/inference source has not quietly gained common process or
network execution paths. Re-run and extend before adding tools or plugins.
"""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (ROOT / "training/llm/train.py", ROOT / "training/llm/generate.py")
BLOCKED_IMPORT_ROOTS = {
    "socket", "subprocess", "requests", "httpx", "urllib", "ftplib",
    "telnetlib", "paramiko", "pexpect",
}
BLOCKED_CALLS = {"exec", "eval", "system", "popen", "Popen", "run", "check_call", "check_output"}

def dotted_name(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))

def audit(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in BLOCKED_IMPORT_ROOTS:
                    issues.append(f"{path.relative_to(ROOT)} imports blocked module {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in BLOCKED_IMPORT_ROOTS:
                issues.append(f"{path.relative_to(ROOT)} imports blocked module {node.module}")
        elif isinstance(node, ast.Call):
            name = dotted_name(node.func)
            leaf = name.rsplit(".", 1)[-1]
            is_builtin_dynamic_code = name in {"eval", "exec"}
            is_process_or_shell = leaf in {"system", "popen", "Popen", "run", "check_call", "check_output"}
            if is_builtin_dynamic_code or is_process_or_shell:
                issues.append(f"{path.relative_to(ROOT)} calls potentially unsafe function {name}")
    return issues

def main() -> int:
    issues = [issue for path in TARGETS for issue in audit(path)]
    generator = (ROOT / "training/llm/generate.py").read_text(encoding="utf-8")
    if "weights_only=True" not in generator:
        issues.append("generate.py must load checkpoints with weights_only=True")
    if issues:
        print("SANDBOX STATIC AUDIT: FAIL")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print("SANDBOX STATIC AUDIT: PASS")
    print("Scope: source-level checks only; no agent tools, shell, or network interface is exposed by this prototype.")
    print("Limitation: this is not a runtime sandbox, penetration test, or proof that a future app is secure.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

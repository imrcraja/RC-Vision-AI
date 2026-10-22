# Learning state for local experiments

Optional JSON files exported here may be packaged by `training/package_daily_learning.py`. Do not store API keys, passwords, private chat logs, or other secrets here. The daily GitHub Actions workflow does not have access to the phone's private storage; the Android app must implement a separate user-approved export/import feature before phone memory or local checkpoints can be included.

Supported file names if you choose to maintain state in this directory:
- `memory.json`
- `knowledge.json`
- `skills.json`
- `evaluation.json`

Keep data minimal and user-approved. The ZIP exporter currently creates empty templates for these schemas and copies files present in this directory; it does not automatically infer facts or memories.

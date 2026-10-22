# OpenRouter setup for RC Vision AI

## First: rotate any key pasted into a chat or public place

Treat a pasted API key as compromised. Revoke it in OpenRouter and create a new key. Do not commit either key to Git, put it in source code, screenshots, ZIP files, or issue comments.

## Daily training corpus

1. Open the repository's [Actions secrets settings](https://github.com/imrcraja/RC-Vision-AI/settings/secrets/actions).
2. Add a repository secret named `OPENROUTER_API_KEY` and paste the newly rotated key into GitHub's secret form.
3. Optional: add a repository variable named `OPENROUTER_MODEL` with a model ID available to your account. If omitted, the workflow uses `openrouter/auto`.
4. Run **Daily learning package and model research** from the Actions tab, or wait for its scheduled run.
5. The workflow prefers OpenRouter when the secret exists, falls back to Gemini only if its secret exists, and otherwise uses the checked-in seed corpus.

The remote model generates a small amount of synthetic educational text. The repository's original random-initialized LLM is then trained on that corpus. This is not fine-tuning the OpenRouter model, and the tiny research model will not become a capable general assistant from a few hundred training steps. Review generated data and training metrics before relying on a checkpoint.

## OpenRouter chat in the Android app

The Chat screen asks for an API key and model ID. You can choose Save encrypted key: the app encrypts it with an Android Keystore AES-GCM key and stores the ciphertext in app-private preferences, so it persists across app restarts. Use Forget key to clear it. Uninstalling the app or clearing its app data can remove the saved key. This is safer than plaintext storage but does not make a key embedded in a distributed APK safe; do not ship your own shared API key in an APK. Use a private, rotated key with limited credits/usage and monitor usage in OpenRouter.

## Tool execution and sandbox status

The current Android integration sends text messages to the selected OpenRouter model and displays its text response. It also supports a simple sequential batch of newline-separated prompts with per-task progress and results. The Settings screen exposes available RAM, app heap estimate, battery temperature, Android thermal status, and a short UI frame-rate estimate. Standard Android APIs do not reliably expose CPU temperature, GPU load, storage throughput, or the FPS of other apps/games. It does **not** yet execute generated code, run an isolated sandbox, control the phone, call external tools, generate images/audio/video/3D assets, or train model weights on the phone. Those require separate, permissioned modules and tests. A model API key does not automatically grant those capabilities.

Provider/model availability, usage limits, billing, and provider policies still apply. Do not assume that any API is unlimited or unrestricted.

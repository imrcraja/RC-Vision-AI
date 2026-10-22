# RC Vision AI engineering roadmap

This roadmap intentionally separates a working runtime from the much harder task of training a capable image model.

## Rules

1. No third-party AI inference APIs.
2. Do not import an existing open-source image-generation model or engine.
3. Prefer standard-library runtime code until a specific, reviewed dependency is justified. Any future dependency must be disclosed and must not silently bring in a pretrained model.
4. Do not describe the project as an image generator until a model actually produces images and tests demonstrate it.
5. Never claim that a model learns from a prompt alone. Training requires data, an objective, an optimizer, and compute.
6. No automatic self-modifying source code. Updates must be reviewable, versioned, and user-approved.

## Milestone 1 — Runtime foundation

- [x] Repository identity and principles
- [x] Standard-library CLI
- [x] Sequential task queue with explicit task states
- [x] Best-effort RAM and thermal-zone reporting
- [x] Unit tests for queue behavior
- [ ] Run CI on supported Python versions

## Milestone 2 — Local workspace

- [x] Device-local prompt history with save, reuse, and clear controls (starter)
- [ ] Versioned local settings and prompt export
- [ ] Explicit workspace export/import controls
- [ ] Reference-image metadata (files remain local)
- [ ] Real task event log and cancellation

## Milestone 3 — Original training-data tools

- [ ] Dataset manifest schema with source/permission fields
- [ ] Image validation and duplicate detection
- [ ] Dataset split reproducibility and audit report
- [ ] Never bundle third-party/private images without permission

## Milestone 4 — Model research and training

- [ ] Choose an original architecture appropriate to target hardware
- [ ] Document tensor shapes, loss, optimizer, and checkpoint format
- [ ] Build a small experimental model and deterministic tests
- [ ] Measure memory, speed, and image quality honestly
- [ ] Scale only when compute and lawful training data are available

## Milestone 5 — User experience and packaging

- [x] Native Android app shell with Create, Chat, Train, and Settings screens
- [x] Liquid-glass-inspired panels and entrance transitions (initial pass; true background blur and reduced-motion settings remain)
- [x] Android debug APK CI workflow added
- [ ] Verify APK CI build and install on a real device
- [ ] Accessibility, screen-reader, and reduced-motion support
- [ ] Real inference-step progress, not guessed percentages
- [ ] Thermal/resource-aware pauses with user-visible reasons
- [ ] ZIP export with manifest, checksums, version compatibility, and safe import

## Practical constraint

A genuinely capable image model trained entirely from scratch is a major compute/data project. The early milestones are useful software, but they do not magically provide image-generation ability. Target-device benchmarks will determine what can run locally.

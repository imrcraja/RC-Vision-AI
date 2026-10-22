# Build the Android APK

The Android app module is `app`. It uses Kotlin and Android platform APIs directly; no third-party AI libraries or pretrained model assets are bundled.

## Requirements

- JDK 17
- Android SDK Platform 35
- Android Gradle Plugin 8.10.1 and a compatible Gradle 8.x distribution
- Internet may be needed by the build machine to download standard Android build tooling. The installed app itself has no Internet permission.

## Build

From the repository root, after installing the required Android build tools:

```bash
gradle assembleDebug
```

The debug APK is expected at:

```
app/build/outputs/apk/debug/app-debug.apk
```

This repository currently does not include the Gradle Wrapper or a prebuilt APK. A successful build has not yet been verified in CI.

## Device install

Transfer the generated APK to your Android device and install it. For USB debugging from a computer:

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

The first app build is a UI/runtime prototype only; it does not include a trained LLM or image-generation model.

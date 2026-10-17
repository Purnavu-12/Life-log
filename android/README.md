# LifeLog Android

Native Android client for LifeLog, built with Kotlin and Jetpack Compose.

## What it does

- Loads the memories created by the existing LifeLog server.
- Records audio or selects an audio file from the device.
- Sends audio to the existing `POST /api/upload` endpoint.
- Uses the server-returned transcription and extracted summary, tags, people, and tasks.
- Searches memories through the existing semantic search endpoint.
- Deletes memories through the existing API.

The Android app intentionally does not duplicate transcription or extraction. The server remains the source of truth for those operations, so the website and app display the same memory data.

## Configure the server

The Android app is a client of the deployed LifeLog server. It does not use the
repository's `backend/` directory as its production backend.

Before running the app, replace the `API_BASE_URL` placeholder in
`app/build.gradle.kts` with the server URL used by the website, for example:

```kotlin
buildConfigField("String", "API_BASE_URL", "\"https://lifelog.example.com/\"")
```

The URL must end with `/` because it is used as Retrofit's base URL. The server
must expose the same endpoints used by the website, including `/api/upload`,
`/api/memories`, `/api/search`, and `/api/memories/{id}`.

The development manifest permits cleartext HTTP for local development. Use HTTPS and remove `android:usesCleartextTraffic="true"` for production.

## Build without Android Studio

The repository includes a GitHub Actions workflow at
`.github/workflows/android-debug-apk.yml`.

After pushing the repository:

1. Open the repository on GitHub.
2. Open the **Actions** tab.
3. Select **Build Android debug APK**.
4. Select **Run workflow** if the workflow has not run from a push yet.
5. Open the completed workflow run.
6. Download the `lifelog-debug-apk` artifact.
7. Extract it and install `app-debug.apk` on the phone.

The workflow uses Java 17, Gradle 8.9, Android API 35, and builds
`android/app/build/outputs/apk/debug/app-debug.apk`.

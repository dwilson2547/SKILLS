---
name: android-device
description: 'Reach, install on, and drive a physical Android phone from this WSL machine: wireless-debugging pair/connect, APK install, launch, logcat, screenshots, taps. Use whenever an app has to go onto the phone or be checked on it, whenever the user reads out a wireless-debugging IP:port or pairing code, or when adb shows no device / unauthorized / offline / "protocol fault".'
---

# Android device (WSL → phone over wireless debugging)

Everything goes through **Windows adb.exe** via `adb-phone` (next to this file). WSL's own
adb stays `unauthorized` over usbipd and its wireless pairing fails TLS: don't retry it.

```bash
P=~/.claude/skills/android-device/adb-phone
```

Verified 2026-11-03 on a Galaxy S21 Ultra (SM-G998U1), platform-tools 37.0.1.

## Ports: the rule that keeps getting broken

Wireless debugging shows **two different ports**, and using the wrong one is not harmless:

| What the user gives | Which port it is | The only command to run |
|---|---|---|
| IP:port **and a 6-digit code** | the **pairing** port (from the "Pair device with pairing code" dialog) | `$P pair <ip:port> <code>` |
| IP:port, **no code** | the **connect** port (main Wireless debugging screen) | `$P connect <ip:port>` |

- **A code means pairing. Never `connect` to a port that came with a code**, not even "just to
  try first". `connect` on the pairing port fails with `protocol fault (couldn't read status
  message)`, leaves an `offline` device entry, and **burns that pairing session**: the following
  `pair` on the same port fails too, and the user has to open a new dialog for a new code.
- `pair` on the connect port fails with the same `protocol fault`. Same cure: don't guess.
- If unsure which port it is, ask. A wasted pairing code costs the user a trip into Settings.
- Never chain `connect … || pair …`: `connect` exits 0 even when it fails.

## Session flow

1. `$P status`: lists devices and mDNS services. If a device shows `device`, skip to step 4.
2. Pairing is remembered across sessions, so usually only the **connect** port is needed (it
   changes every time wireless debugging is toggled or the phone changes network). Ask the
   user for "the IP:port on the main Wireless debugging screen (not the pairing dialog)".
   `$P connect <ip:port>`.
3. Only if connect is refused/unauthorized: ask for **Pair device with pairing code**, then
   `$P pair <ip:port> <code>` and nothing else on that port. After pairing, adb may connect by
   itself via mDNS; if `$P status` still shows nothing (mDNS often lists nothing here), ask for
   the main-screen connect port and `$P connect` it.
4. The phone has to be on the same WiFi as the PC. When the user turns WiFi off (e.g. a
   cellular test), adb is gone; the old port is refused afterwards, so get the new one.

## Installing and driving

```bash
$P install app/build/outputs/apk/debug/app-debug.apk   # copies under C: (adb.exe needs a Windows path), install -r
$P start com.example.app/.MainActivity
$P log com.example.app        # logcat for the app's pid only, UI noise stripped
$P shot /path/to/screen.png   # then Read the PNG to see the screen
$P tap <x> <y>                # device pixels
```

- Screenshots read back scaled (the S21 is 1080x2400, shown at 900x2000): **multiply what you
  see by the stated factor (1.20) before `tap`**.
- Tapping the user's UI is fine for verifying your own feature (start a capture, press a
  button you built). Ask before anything that signs out, deletes, or forgets state.
- `libpenguin.so not found` in logcat is Samsung system noise.

## Building

Run `./gradlew assembleDebug` (plus `testDebugUnitTest lintDebug`) in the app's `android_app/`.
SDK at `~/Android/Sdk`, found through the app's uncommitted `local.properties`
(`sdk.dir=/home/daniel/Android/Sdk`). Accepting SDK licences is the user's call: hand them
`sdkmanager --licenses`.

## USB instead (rarely needed)

Only for serial devices or a phone with no WiFi. `usbipd bind --busid <id>` needs an admin
Windows prompt (the user runs it); `usbipd.exe attach --wsl --busid <id>` does not. While
attached, Windows can't use the device. An ESP32 that resets drops the attach.

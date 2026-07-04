# Drive Token Generator — Termux Edition

![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Android-3DDC84)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Generates a `token.pickle` from a Google OAuth `credentials.json`, entirely
inside Termux on Android — no desktop browser, no localhost redirect needed.

This version has every known Termux gotcha pre-solved. Following the steps
below in order should produce zero errors.

## Project structure

```
.
├── generate_token.py    # main script — reads credentials.json, writes token.pickle
├── unlock_token.py       # optional — prints client_id/secret/refresh_token from token.pickle
├── setup_termux.sh       # one-time Termux environment setup
├── requirements.txt      # Python dependencies
├── LICENSE
└── README.md
```

## Why this works differently than desktop scripts

Most Google OAuth quickstart scripts use `InstalledAppFlow.run_local_server()`,
which spins up a local web server and waits for your browser to redirect back
to `http://localhost:PORT`. That's unreliable on Termux. Instead, this project
uses Google's **out-of-band (OOB) flow**: you open the auth URL, approve
access, Google shows you a code on-screen, and you paste that code back into
Termux manually.

## Step 1 — Get a real `credentials.json`

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials.
2. Create an OAuth Client ID → choose **Desktop app**.
3. Download the JSON and rename it `credentials.json`.

A fake/test `credentials.json` will let the script run but Google will
reject the actual sign-in with `Error 401: invalid_client` — you need a real
one from Cloud Console for a working `token.pickle`.

## Step 2 — Get the project onto your phone

```bash
cd /storage/emulated/0/Download
git clone <this-repo-or-copy-files-here> Token-Pickle-Generator-Android
cd Token-Pickle-Generator-Android
```

## Step 3 — Run the setup script

```bash
bash setup_termux.sh
```

This single script handles every issue we ran into previously:

| Problem                                              | Fix baked into `setup_termux.sh`                          |
|-------------------------------------------------------|-------------------------------------------------------------|
| `ERROR: Installing pip is forbidden` (pip self-upgrade blocked by Termux) | Installs `python-pip` via `pkg` instead, never runs `pip install --upgrade pip` |
| `cryptography` build hangs at "Installing build dependencies" (tries compiling Rust on-device) | Installs `python-cryptography` via `pkg` first — a prebuilt binary — so pip sees it already satisfied |
| No storage access to read/write files in `/storage/emulated/0/...` | Runs `termux-setup-storage` automatically |
| Transient pip failures | Falls back to the official `get-pip.py` bootstrap and retries |
| Silent import failures later | Verifies `google_auth_oauthlib` and `google.auth` import cleanly before declaring success |

If it prints `Setup complete, no errors.` at the end, you're good.

## Step 4 — Add your credentials

Copy your real `credentials.json` into this folder (overwrite any test file):

```bash
cp /sdcard/Download/credentials.json .
```

Keep the project inside phone storage (not an SD card) — some Android setups
restrict SD card write access.

## Step 5 — Generate the token

```bash
python generate_token.py
```

You'll see:

```
1) Open this URL in any browser (Chrome on your phone is fine):

https://accounts.google.com/o/oauth2/auth?...

2) Sign in, approve access, then copy the code Google shows you.

Paste the authorization code here: _
```

Open the link, sign in with the Google account you want to grant access to,
approve, copy the code shown, paste it in. You'll get:

```
[OK] Saved credentials to /path/to/token.pickle
```

## Step 6 (optional) — Extract raw client_id / client_secret / refresh_token

Useful for `rclone` configs or Cloudflare-based Drive index deployments:

```bash
python unlock_token.py
```

Add `--json` for machine-readable output.

## Command reference

```bash
python generate_token.py --credentials path/to/creds.json --token path/to/token.pickle
python generate_token.py --scopes drive youtube      # scope presets
python generate_token.py --force                     # ignore existing token, re-auth
python unlock_token.py --json
```

Scope presets:

| Preset          | Scope                                              |
|-----------------|-----------------------------------------------------|
| `drive.file`    | `https://www.googleapis.com/auth/drive.file` (default) |
| `drive`         | `https://www.googleapis.com/auth/drive` (full access)|
| `drive.readonly`| `https://www.googleapis.com/auth/drive.readonly`    |
| `youtube`       | `https://www.googleapis.com/auth/youtube.upload`    |

## Using token.pickle in your own scripts

```python
import pickle
from googleapiclient.discovery import build

with open("token.pickle", "rb") as f:
    creds = pickle.load(f)

service = build("drive", "v3", credentials=creds)
```

Re-running `generate_token.py` later will silently refresh an expired token
(if a refresh token was granted) — no need to redo the browser flow unless
you revoke access or pass `--force`.

## Security notes

- Never commit `credentials.json` or `token.pickle` to a public repo.
- Both are already in `.gitignore`.
- `token.pickle` grants whatever scopes you requested — treat it like a password.

## Troubleshooting

**"Installing build dependencies" hangs on `cryptography`**
You skipped `setup_termux.sh` or it didn't finish. Run:
```bash
pkg install -y python-cryptography
pip install -r requirements.txt
```

**`ERROR: Installing pip is forbidden`**
Don't run `pip install --upgrade pip` on Termux. If you hit this manually:
```bash
pkg install -y python-pip
```

**`Error 401: invalid_client` in the browser**
Your `credentials.json` is a test/fake file, or the OAuth client was deleted
in Cloud Console. Get a real one (Step 1).

**Permission denied reading/writing files**
Run `termux-setup-storage` and accept the Android permission prompt, or
enable it manually: Settings → Apps → Termux → Permissions → Storage.

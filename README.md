# Drive Token Generator — Termux Edition

![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Android-3DDC84)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
[![License](https://img.shields.io/github/license/AaryaKrishna19/Token-Pickle-Generator-Termux)](https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/AaryaKrishna19/Token-Pickle-Generator-Termux?style=social)](https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux)
[![Issues](https://img.shields.io/github/issues/AaryaKrishna19/Token-Pickle-Generator-Termux)](https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux/issues)

Generate a Google OAuth `token.pickle` from `credentials.json`, entirely on
your Android phone using Termux — no PC, no desktop browser, no localhost
redirect capture needed.

**Repo:** https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux

Quick start (already have Termux installed):
```bash
pkg install -y git && git clone https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux.git && cd Token-Pickle-Generator-Termux && bash setup_termux.sh
```

## Project structure

```
.
├── generate_token.py    # main script — reads credentials.json, writes token.pickle
├── unlock_token.py       # optional — prints client_id/secret/refresh_token from token.pickle
├── ui.py                 # shared terminal UI kit (auto-adjusts to screen width)
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

---

## Full setup from a completely fresh Termux install

Follow these in order. Every step exists because of a real error hit while
building this project — following them in order avoids all of them.

### 1. Install Termux

Install Termux from **F-Droid** (not the outdated Play Store version):
https://f-droid.org/en/packages/com.termux/

### 2. Update Termux's package lists

Open Termux and run:

```bash
pkg update -y && pkg upgrade -y
```

If you see a prompt about mirrors, type `y` and continue. If package upgrades
prompt to keep or overwrite a config file, the default (keep) is fine.

### 3. Grant storage permission

This lets Termux read/write files in your phone's shared storage (Downloads,
`/sdcard`, etc.) instead of being sandboxed to its own app-private folder.

```bash
termux-setup-storage
```

Android will show a permission popup — tap **Allow**. This creates a
`storage` folder inside Termux's home directory (`~/storage/`) that links to
your phone's shared storage.

If the command does nothing or you don't see a popup, grant it manually:
**Android Settings → Apps → Termux → Permissions → Storage → Allow**.

### 4. Install Python and native dependencies

```bash
pkg install -y python python-pip python-cryptography git
```

Why each package matters:

| Package              | Why you need it                                                                 |
|-----------------------|----------------------------------------------------------------------------------|
| `python`              | Runs the scripts                                                                |
| `python-pip`          | A working `pip` that Termux manages itself                                      |
| `python-cryptography` | Prebuilt binary for the `cryptography` library — avoids a source build that hangs |
| `git`                 | To clone this repository                                                        |

**Do not run `pip install --upgrade pip`.** Termux blocks this on purpose
(`ERROR: Installing pip is forbidden, this will break the python-pip package`)
because pip is managed as a Termux package, not a pip-managed one.

### 5. Get the project

```bash
cd storage/downloads
git clone https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux.git
cd Token-Pickle-Generator-Termux
```

(Replace the URL with wherever you host this repo. `storage/downloads` is the
symlinked folder from Step 3, pointing at your phone's real Downloads folder.)

### 6. Run the setup script

```bash
bash setup_termux.sh
```

This automates steps 2–4 above plus installs the remaining Python packages,
so if you're setting this up again later (new phone, fresh Termux), this one
command is all you need after installing Termux itself:

```bash
pkg install -y git && git clone https://github.com/AaryaKrishna19/Token-Pickle-Generator-Termux.git && cd Token-Pickle-Generator-Termux && bash setup_termux.sh
```

`setup_termux.sh` does the following, in order:

1. `pkg update -y`
2. `pkg install -y python python-pip python-cryptography`
3. `termux-setup-storage`
4. `pip install -r requirements.txt` (with an automatic `get-pip.py` bootstrap
   retry if the first attempt fails for any reason)
5. Verifies `google_auth_oauthlib` and `google.auth` import correctly

If it prints `Setup complete, no errors.` at the end, you're ready.

---

## Get a real credentials.json

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials.
2. Create an OAuth Client ID → choose **Desktop app**.
3. Download the JSON and rename it `credentials.json`.
4. Enable the Drive API (and YouTube Data API v3 if you plan to use the
   `youtube` scope) for your project under **APIs & Services → Library**.

A fake/placeholder `credentials.json` will let the script run and print an
auth URL, but Google will reject the actual sign-in with
`Error 401: invalid_client` — you need a real client from Cloud Console for a
working `token.pickle`.

## Add your credentials

Copy your real `credentials.json` into the project folder:

```bash
cp storage/downloads/credentials.json .
```

Keep the project inside phone storage (not an external SD card) — some
Android setups restrict SD card write access for apps like Termux.

## Generate the token

```bash
python generate_token.py
```

You'll see a small UI walk you through it:

```
╔════════════════════════════════════════════════════════════╗
║                   Drive Token Generator                    ║
╚════════════════════════════════════════════════════════════╝

ℹ Using credentials file: .../credentials.json
ℹ Output token path:      .../token.pickle
------------------------------------------------------------
ℹ Requested scopes: https://www.googleapis.com/auth/drive.file

[Step 1] Open this URL in any browser (Chrome on your phone is fine):

https://accounts.google.com/o/oauth2/auth?...

[Step 2] Sign in, approve access, then copy the code Google shows you.

Paste the authorization code here:
```

Open the link, sign in with the Google account you want to grant access to,
approve, copy the code shown, paste it in. You'll get:

```
✔ Saved to /path/to/token.pickle
------------------------------------------------------------
✔ All done. token.pickle is ready to use.
```

## Extracting client_id / client_secret / refresh_token

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

| Preset          | Scope                                                |
|-----------------|-------------------------------------------------------|
| `drive.file`    | `https://www.googleapis.com/auth/drive.file` (default) |
| `drive`         | `https://www.googleapis.com/auth/drive` (full access)  |
| `drive.readonly`| `https://www.googleapis.com/auth/drive.readonly`       |
| `youtube`       | `https://www.googleapis.com/auth/youtube.upload`       |

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

- Never commit `credentials.json` or `token.pickle` to a public repo —
  they're already in `.gitignore`.
- `token.pickle` grants whatever scopes you requested — treat it like a
  password.
- If you ever suspect a token leaked, revoke it at
  https://myaccount.google.com/permissions and generate a new one with
  `--force`.

## Troubleshooting

**"Installing build dependencies" hangs on `cryptography`**
You skipped `setup_termux.sh`, or `python-cryptography` wasn't installed via
`pkg` first. Run:
```bash
pkg install -y python-cryptography
pip install -r requirements.txt
```

**`ERROR: Installing pip is forbidden`**
Don't run `pip install --upgrade pip` on Termux. Fix with:
```bash
pkg install -y python-pip
```

**`Error 401: invalid_client` in the browser**
Your `credentials.json` is a placeholder/fake file, or the OAuth client was
deleted in Cloud Console. Get a real one (see "Get a real credentials.json").

**Permission denied reading/writing files in shared storage**
Run `termux-setup-storage` and accept the Android permission prompt, or
enable it manually: Settings → Apps → Termux → Permissions → Storage.

**`No mirror or mirror group selected` warning during `pkg update`**
Harmless — Termux is just suggesting you pick a mirror. Ignore it, or run
`termux-change-repo` if `pkg update` is consistently slow.

## Credits

Built and maintained by **[AaryaKrishna19](https://github.com/AaryaKrishna19)**.

## License

MIT — see [LICENSE](LICENSE).

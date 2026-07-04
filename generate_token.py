#!/usr/bin/env python3
"""
generate_token.py
------------------
Generates token.pickle from a Google OAuth credentials.json file.
Designed to run on Android Termux (no local browser redirect capture needed).

Usage:
    python generate_token.py
    python generate_token.py --credentials my_creds.json --token my_token.pickle
    python generate_token.py --scopes drive youtube
    python generate_token.py --force

Flow:
    1. Reads credentials.json (OAuth client secret, "Desktop app" type recommended).
    2. Builds an authorization URL.
    3. You open that URL in any browser, sign in, grant access, and copy the
       authorization code Google shows you.
    4. Paste the code back into the terminal.
    5. Script exchanges the code for tokens and pickles the Credentials object
       to token.pickle for reuse by other scripts.
"""

import argparse
import pickle
import sys
from pathlib import Path

from ui import Ui

try:
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
except ImportError:
    print(
        "Missing dependencies. Install them first:\n"
        "  pip install google-auth-oauthlib google-auth\n",
        file=sys.stderr,
    )
    sys.exit(1)


DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Convenience presets so users don't have to type full scope URLs.
SCOPE_PRESETS = {
    "drive.file": "https://www.googleapis.com/auth/drive.file",
    "drive": "https://www.googleapis.com/auth/drive",
    "drive.readonly": "https://www.googleapis.com/auth/drive.readonly",
    "youtube": "https://www.googleapis.com/auth/youtube.upload",
}

# Out-of-band redirect: shows the code on Google's page instead of
# trying to hit a localhost server (which is unreliable on Termux).
OOB_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def resolve_scopes(raw_scopes: list[str]) -> list[str]:
    """Expand preset names (e.g. 'youtube', 'drive') into full scope URLs.
    Anything already a full URL is passed through unchanged."""
    return [SCOPE_PRESETS.get(s, s) for s in raw_scopes]


def load_existing_credentials(token_path: Path):
    if not token_path.exists():
        return None
    try:
        with open(token_path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def save_credentials(creds, token_path: Path):
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)
    Ui.ok(f"Saved to {token_path.name}")


def run_manual_flow(credentials_path: Path, scopes: list[str]):
    flow = Flow.from_client_secrets_file(
        str(credentials_path),
        scopes=scopes,
        redirect_uri=OOB_REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    Ui.step(1, "Open this URL in any browser:")
    print()
    Ui.url_block(auth_url)

    Ui.step(2, "Sign in, approve access, then copy the code shown.")

    # Best-effort: try to open it automatically if termux-open-url exists.
    try:
        import subprocess
        subprocess.run(["termux-open-url", auth_url], check=False)
    except FileNotFoundError:
        pass

    print()
    code = Ui.prompt("Paste authorization code: ")
    Ui.info("Exchanging code for tokens...")
    flow.fetch_token(code=code)
    return flow.credentials


def main():
    parser = argparse.ArgumentParser(description="Generate token.pickle from credentials.json")
    parser.add_argument(
        "--credentials",
        default="credentials.json",
        help="Path to OAuth client credentials JSON (default: credentials.json)",
    )
    parser.add_argument(
        "--token",
        default="token.pickle",
        help="Output path for the pickled token (default: token.pickle)",
    )
    parser.add_argument(
        "--scopes",
        nargs="+",
        default=DEFAULT_SCOPES,
        help=(
            f"OAuth scopes to request (default: {DEFAULT_SCOPES[0]}). "
            f"Accepts full scope URLs or presets: {', '.join(SCOPE_PRESETS)}. "
            f"Example: --scopes drive youtube"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore any existing token.pickle and force a fresh auth flow",
    )
    args = parser.parse_args()

    credentials_path = Path(args.credentials)
    token_path = Path(args.token)

    Ui.banner("Google OAuth token wizard")
    print()

    if not credentials_path.exists():
        Ui.error(f"Could not find {credentials_path}")
        Ui.info("Put your credentials.json next to this script,")
        Ui.info("or pass --credentials PATH")
        sys.exit(1)

    Ui.kv("Credentials:", credentials_path.name)
    Ui.kv("Token output:", token_path.name)

    creds = None if args.force else load_existing_credentials(token_path)

    if creds and creds.valid:
        Ui.rule()
        Ui.ok(f"Existing valid token found at {token_path.name}. Nothing to do.")
        Ui.footer()
        return

    if creds and creds.expired and creds.refresh_token:
        Ui.info("Existing token expired, attempting silent refresh...")
        try:
            creds.refresh(Request())
            save_credentials(creds, token_path)
            Ui.rule()
            Ui.ok("Done.")
            Ui.footer()
            return
        except Exception as e:
            Ui.warn(f"Refresh failed ({e}). Running full auth flow instead.")

    Ui.rule()
    scopes = resolve_scopes(args.scopes)
    Ui.kv("Scopes:", ", ".join(scopes))
    creds = run_manual_flow(credentials_path, scopes)
    save_credentials(creds, token_path)
    Ui.rule()
    Ui.ok("All done. token.pickle is ready to use.")
    Ui.footer()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        Ui.warn("Cancelled by user.")
        sys.exit(130)

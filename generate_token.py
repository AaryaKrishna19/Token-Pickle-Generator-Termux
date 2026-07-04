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


# ---------------------------------------------------------------------------
# Tiny terminal UI helpers (no external deps, safe on Termux)
# ---------------------------------------------------------------------------

class Ui:
    """Minimal ANSI-based UI kit. Falls back to plain text if the terminal
    doesn't support colors (e.g. output piped to a file)."""

    _use_color = sys.stdout.isatty()

    RESET = "\033[0m" if _use_color else ""
    BOLD = "\033[1m" if _use_color else ""
    DIM = "\033[2m" if _use_color else ""
    CYAN = "\033[36m" if _use_color else ""
    GREEN = "\033[32m" if _use_color else ""
    YELLOW = "\033[33m" if _use_color else ""
    RED = "\033[31m" if _use_color else ""
    MAGENTA = "\033[35m" if _use_color else ""

    WIDTH = 60

    @classmethod
    def banner(cls, title: str):
        line = "═" * cls.WIDTH
        pad = (cls.WIDTH - len(title)) // 2
        print(f"{cls.CYAN}╔{line}╗{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}{' ' * pad}{cls.BOLD}{title}{cls.RESET}{' ' * (cls.WIDTH - pad - len(title))}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}╚{line}╝{cls.RESET}")

    @classmethod
    def step(cls, number: int, text: str):
        print(f"\n{cls.MAGENTA}{cls.BOLD}[Step {number}]{cls.RESET} {text}")

    @classmethod
    def ok(cls, text: str):
        print(f"{cls.GREEN}✔ {text}{cls.RESET}")

    @classmethod
    def info(cls, text: str):
        print(f"{cls.CYAN}ℹ {text}{cls.RESET}")

    @classmethod
    def warn(cls, text: str):
        print(f"{cls.YELLOW}⚠ {text}{cls.RESET}")

    @classmethod
    def error(cls, text: str):
        print(f"{cls.RED}✘ {text}{cls.RESET}", file=sys.stderr)

    @classmethod
    def rule(cls):
        print(f"{cls.DIM}{'-' * cls.WIDTH}{cls.RESET}")

    @classmethod
    def url_box(cls, url: str):
        print(f"{cls.YELLOW}{url}{cls.RESET}")

    @classmethod
    def prompt(cls, text: str) -> str:
        return input(f"{cls.BOLD}{text}{cls.RESET}").strip()


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
    Ui.ok(f"Saved to {token_path.resolve()}")


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

    Ui.step(1, "Open this URL in any browser (Chrome on your phone is fine):")
    print()
    Ui.url_box(auth_url)
    print()
    Ui.step(2, "Sign in, approve access, then copy the code Google shows you.")

    # Best-effort: try to open it automatically if termux-open-url exists.
    try:
        import subprocess
        subprocess.run(["termux-open-url", auth_url], check=False)
    except FileNotFoundError:
        pass

    print()
    code = Ui.prompt("Paste the authorization code here: ")
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

    Ui.banner("Drive Token Generator")
    print()

    if not credentials_path.exists():
        Ui.error(
            f"Could not find {credentials_path}. Put your Google OAuth "
            f"credentials.json next to this script (or pass --credentials PATH)."
        )
        sys.exit(1)

    Ui.info(f"Using credentials file: {credentials_path.resolve()}")
    Ui.info(f"Output token path:      {token_path.resolve()}")

    creds = None if args.force else load_existing_credentials(token_path)

    if creds and creds.valid:
        Ui.rule()
        Ui.ok(f"Existing valid token found at {token_path.resolve()}. Nothing to do.")
        return

    if creds and creds.expired and creds.refresh_token:
        Ui.info("Existing token expired, attempting silent refresh...")
        try:
            creds.refresh(Request())
            save_credentials(creds, token_path)
            Ui.rule()
            Ui.ok("Done.")
            return
        except Exception as e:
            Ui.warn(f"Refresh failed ({e}). Running full auth flow instead.")

    Ui.rule()
    scopes = resolve_scopes(args.scopes)
    Ui.info(f"Requested scopes: {', '.join(scopes)}")
    creds = run_manual_flow(credentials_path, scopes)
    save_credentials(creds, token_path)
    Ui.rule()
    Ui.ok("All done. token.pickle is ready to use.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        Ui.warn("Cancelled by user.")
        sys.exit(130)

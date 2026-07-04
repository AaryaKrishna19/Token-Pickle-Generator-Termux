#!/usr/bin/env python3
"""
unlock_token.py
----------------
Reads a token.pickle produced by generate_token.py and prints the
client_id, client_secret, and refresh_token it contains.

Useful for tools that want raw OAuth credentials directly (e.g. rclone
configs, Cloudflare-based Drive index deployments) instead of the
pickled Credentials object itself.

Usage:
    python unlock_token.py
    python unlock_token.py --token path/to/token.pickle
    python unlock_token.py --json     # machine-readable output
"""

import argparse
import json
import pickle
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Extract client_id/secret/refresh_token from token.pickle")
    parser.add_argument("--token", default="token.pickle", help="Path to token.pickle (default: token.pickle)")
    parser.add_argument("--json", action="store_true", help="Print as JSON instead of plain text")
    args = parser.parse_args()

    token_path = Path(args.token)
    if not token_path.exists():
        print(f"[ERROR] {token_path} not found. Run generate_token.py first.", file=sys.stderr)
        sys.exit(1)

    with open(token_path, "rb") as f:
        creds = pickle.load(f)

    if not getattr(creds, "refresh_token", None):
        print(
            "[WARN] No refresh_token stored on this credential. "
            "Re-run generate_token.py with --force to get a fresh one "
            "(Google only issues a refresh_token on first consent, or "
            "when you pass prompt=consent, which generate_token.py already does).",
            file=sys.stderr,
        )

    data = {
        "client_id": getattr(creds, "client_id", None),
        "client_secret": getattr(creds, "client_secret", None),
        "refresh_token": getattr(creds, "refresh_token", None),
        "token_uri": getattr(creds, "token_uri", None),
        "scopes": list(getattr(creds, "scopes", []) or []),
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Client ID:      {data['client_id']}")
        print(f"Client Secret:  {data['client_secret']}")
        print(f"Refresh Token:  {data['refresh_token']}")
        print(f"Token URI:      {data['token_uri']}")
        print(f"Scopes:         {', '.join(data['scopes']) if data['scopes'] else '(none recorded)'}")


if __name__ == "__main__":
    main()

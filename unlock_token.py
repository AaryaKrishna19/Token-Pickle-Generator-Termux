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

from ui import Ui


def main():
    parser = argparse.ArgumentParser(description="Extract client_id/secret/refresh_token from token.pickle")
    parser.add_argument("--token", default="token.pickle", help="Path to token.pickle (default: token.pickle)")
    parser.add_argument("--json", action="store_true", help="Print as JSON instead of the styled view")
    args = parser.parse_args()

    token_path = Path(args.token)

    if not args.json:
        Ui.banner("Token unlocker")
        print()

    if not token_path.exists():
        if args.json:
            print(json.dumps({"error": f"{token_path} not found"}))
        else:
            Ui.error(f"{token_path} not found.")
            Ui.info("Run generate_token.py first.")
        sys.exit(1)

    with open(token_path, "rb") as f:
        creds = pickle.load(f)

    data = {
        "client_id": getattr(creds, "client_id", None),
        "client_secret": getattr(creds, "client_secret", None),
        "refresh_token": getattr(creds, "refresh_token", None),
        "token_uri": getattr(creds, "token_uri", None),
        "scopes": list(getattr(creds, "scopes", []) or []),
    }

    if args.json:
        print(json.dumps(data, indent=2))
        return

    if not data["refresh_token"]:
        Ui.warn("No refresh_token stored on this credential.")
        Ui.info("Re-run generate_token.py --force to get a fresh one.")

    Ui.rule()
    Ui.kv("Client ID:", data["client_id"] or "(none)")
    Ui.kv("Client Secret:", data["client_secret"] or "(none)")
    Ui.kv("Refresh Token:", data["refresh_token"] or "(none)")
    Ui.kv("Token URI:", data["token_uri"] or "(none)")
    Ui.kv("Scopes:", ", ".join(data["scopes"]) if data["scopes"] else "(none recorded)")
    Ui.rule()
    Ui.footer()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        Ui.warn("Cancelled by user.")
        sys.exit(130)

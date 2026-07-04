#!/data/data/com.termux/files/usr/bin/bash
# One-time environment setup for Termux.
# Every step here exists because of a real failure encountered before:
#   - pip install --upgrade pip        -> blocked by Termux ("forbidden")
#   - cryptography built from source   -> hangs compiling Rust on-device
# Both are avoided by installing via `pkg` instead of letting pip build them.
set -e

echo "=== 1/5: Updating package lists ==="
pkg update -y

echo "=== 2/5: Installing Python + prebuilt native deps ==="
# python-pip: gives us a working pip without pip trying to upgrade itself.
# python-cryptography: prebuilt binary wheel via apt, so pip never needs to
#   compile the cryptography package from source (that's the step that hangs).
pkg install -y python python-pip python-cryptography

echo "=== 3/5: Requesting storage permission ==="
termux-setup-storage 2>/dev/null || echo "  (already granted or unavailable, skipping)"

echo "=== 4/5: Installing Python dependencies ==="
if ! pip install -r requirements.txt; then
    echo "  pip install failed once, retrying with pip bootstrap fix..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python
    pip install -r requirements.txt
fi

echo "=== 5/5: Verifying imports ==="
python -c "from google_auth_oauthlib.flow import Flow; from google.auth.transport.requests import Request; print('  All imports OK.')"

echo ""
echo "Setup complete, no errors."
echo "Next steps:"
echo "  1. Put your real credentials.json in this folder (overwrite any test/fake one)."
echo "  2. Run: python generate_token.py"
echo "  3. (optional) Run: python unlock_token.py"

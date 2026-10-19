#!/usr/bin/env bash
# exit on error
set -o errexit

echo "[render-build] Upgrading pip..."
python -m pip install --upgrade pip

echo "[render-build] Installing dependencies..."
pip install -r requirements.txt

# Builds must not import or mutate application data. Run reviewed migrations
# separately, with backups and explicit environment selection.

echo "[render-build] Setup complete."

#!/bin/bash
# Moneyfest Aid: set up the three real RGB wallets on Mutinynet (no Docker).
# Double-click in Finder. Safe to run again: it skips steps already done.
cd "$(dirname "$0")/.." || exit 1
mkdir -p data
[ -x .rgb-venv/bin/python ] || { echo "Run scripts/rgb_probe.command first (installs rgb-lib)."; read -r; exit 1; }
.rgb-venv/bin/python -u backend/rgb_setup.py auto 2>&1 | tee data/rgb-setup.txt
echo; read -r -p "Press Enter to close."

#!/bin/bash
# Moneyfest Aid with REAL RGB wallets on Mutinynet. Double-click in Finder.
# Stop any other running Moneyfest server first (control + C in its window).
cd "$(dirname "$0")/.." || exit 1
MONEYFEST_WALLETS=rgb .rgb-venv/bin/python -u backend/app.py 2>&1 | tee data/run-real.txt

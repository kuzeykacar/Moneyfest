#!/bin/bash
# Moneyfest Aid with REAL RGB wallets (Mutinynet) and the REAL local AI (QVAC).
# Start scripts/setup_ai.command first and keep its window open. Stop any other Moneyfest server first.
cd "$(dirname "$0")/.." || exit 1
MONEYFEST_WALLETS=rgb MONEYFEST_AI=qvac .rgb-venv/bin/python -u backend/app.py 2>&1 | tee data/run-real.txt

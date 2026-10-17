#!/bin/bash
# Moneyfest Aid with pretend wallets but the REAL local AI (QVAC). Handy while RGB is being funded.
# Start scripts/setup_ai.command first and keep its window open. Opens on http://127.0.0.1:8001 so it can run next to the pretend version on 8000.
cd "$(dirname "$0")/.." || exit 1
PORT=8001 MONEYFEST_AI=qvac python3 -u backend/app.py 2>&1 | tee data/run-ai-only.txt

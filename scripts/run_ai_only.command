#!/bin/bash
# Moneyfest Aid with pretend wallets but the REAL local AI (QVAC). Handy while RGB is being funded.
# Start scripts/setup_ai.command first and keep its window open. Stop any other Moneyfest server first.
cd "$(dirname "$0")/.." || exit 1
MONEYFEST_AI=qvac python3 -u backend/app.py 2>&1 | tee data/run-ai-only.txt

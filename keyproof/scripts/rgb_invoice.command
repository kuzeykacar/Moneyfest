#!/bin/bash
# Make the tenant's RGB invoice for the KaleidoSwap test-USDT faucet, and show the bitcoin address to fund.
cd "$(dirname "$0")/.." || exit 1
[ -x .venv/bin/python ] || bash scripts/setup_mac.command
.venv/bin/python keyproof/rgb_setup.py invoice 2>&1 | tee data/rgb-invoice.txt
echo; echo "Finished. You can close this window."

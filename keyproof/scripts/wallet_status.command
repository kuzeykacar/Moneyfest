#!/bin/bash
# Show the 3 KeyProof test wallets: addresses and balances.
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python keyproof/rgb_setup.py status 2>&1 | tee data/wallet-status.txt
echo; echo "Finished. You can close this window."

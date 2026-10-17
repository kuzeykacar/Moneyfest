#!/bin/bash
# KeyProof: fund the RGB wallets, create UTXOs, issue the demo stablecoin. Safe to run again.
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python keyproof/rgb_setup.py auto 2>&1 | tee data/rgb-setup.txt
echo; echo "Finished. You can close this window."

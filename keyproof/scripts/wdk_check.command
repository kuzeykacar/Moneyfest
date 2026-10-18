#!/bin/bash
# Installs Tether WDK's RGB wallet module and checks it works on our test network. Writes data/wdk-check.txt
cd "$(dirname "$0")/.." || exit 1
export PATH="$PWD/../.node/bin:$PATH"
mkdir -p data
( cd wdk && npm install --no-audit --no-fund 2>&1 | tail -5 && node check.mjs ) 2>&1 | tee data/wdk-check.txt
echo; echo "Finished. You can close this window."

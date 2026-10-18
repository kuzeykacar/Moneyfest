#!/bin/bash
# Compare the local AI models (speed + correctness). Writes data/bench-ai.txt
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python tools/bench_ai.py 2>&1 | tee data/bench-ai.txt
echo; echo "Finished. You can close this window."

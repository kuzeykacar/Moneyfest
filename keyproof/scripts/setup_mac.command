#!/bin/bash
# KeyProof: one-time install on the Mac (double-click in Finder).
# Makes .venv with cryptography + rgb-lib. Writes data/setup.txt.
cd "$(dirname "$0")/.." || exit 1
mkdir -p data
LOG=data/setup.txt; : > "$LOG"
PY=""; for p in python3.13 python3.12 python3.11 python3.10 python3; do command -v "$p" >/dev/null && { PY="$p"; break; }; done
echo "python: $($PY --version)" | tee -a "$LOG"
[ -x .venv/bin/python ] || $PY -m venv .venv >>"$LOG" 2>&1
.venv/bin/pip install --quiet --upgrade pip >>"$LOG" 2>&1
.venv/bin/pip install "cryptography>=43" "rgb-lib==0.3.0b7" >>"$LOG" 2>&1
.venv/bin/python -c "import cryptography, rgb_lib; print('ok: cryptography', cryptography.__version__)" 2>&1 | tee -a "$LOG"
echo; echo "Finished. You can close this window."

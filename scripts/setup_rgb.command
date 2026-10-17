#!/bin/bash
# Moneyfest Aid: one-time RGB setup on this Mac.
# Double-click this file in Finder (or run: bash scripts/setup_rgb.command).
# It installs kaleido-cli in a private folder, checks Docker and starts the first RGB node.
# Secrets (your password and 12 recovery words) are typed by YOU and never saved to a file.

cd "$(dirname "$0")/.." || exit 1
mkdir -p data
LOG="data/setup-log.txt"          # data/ is git-ignored; no secrets are written here
: > "$LOG"
say() { echo; echo "== $1"; echo "== $1" >> "$LOG"; }
run() { "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }

say "1/5 Checking Python (need 3.11 or newer)"
PY=""
for p in python3.13 python3.12 python3.11 python3; do
  if command -v "$p" >/dev/null && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  echo "Python 3.11+ not found. Install it from https://www.python.org/downloads/ then double-click this file again." | tee -a "$LOG"
  read -r -p "Press Enter to close."; exit 1
fi
run "$PY" --version

say "2/5 Checking Docker"
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Open Docker Desktop, wait for the whale icon to stop moving, then double-click this file again." | tee -a "$LOG"
  read -r -p "Press Enter to close."; exit 1
fi
run docker --version

say "3/5 Installing kaleido-cli (into .kaleido-venv, only for this project)"
if [ ! -x .kaleido-venv/bin/kaleido ]; then
  run "$PY" -m venv .kaleido-venv || exit 1
  run .kaleido-venv/bin/pip install --quiet --upgrade pip
  run .kaleido-venv/bin/pip install kaleido-cli || { read -r -p "Install failed. Press Enter to close."; exit 1; }
fi
K=.kaleido-venv/bin/kaleido
{ for c in "" node wallet asset; do echo "### kaleido $c --help"; $K $c --help; done; } > data/kaleido-help.txt 2>&1
echo "kaleido-cli ready (help saved to data/kaleido-help.txt)" | tee -a "$LOG"

say "4/5 Creating and starting the RGB node (first run downloads Docker images, can take a few minutes)"
run $K setup

say "5/5 Wallet setup: YOUR TURN"
echo "Next you choose a password and get 12 recovery words."
echo "WRITE THE 12 WORDS ON PAPER. Never type them into a chat or a file."
echo "These steps are not saved to the log."
read -r -p "Press Enter when ready..."
$K node init
echo
echo "Now unlocking the node. If it asks for a network, choose signet / Mutinynet."
$K node unlock

say "Checking the node"
run $K node list
run $K wallet balance
echo
echo "Your test bitcoin address (send test BTC here from https://faucet.mutinynet.com):" | tee -a "$LOG"
run $K wallet address
echo
echo "Done. Tell Claude: 'setup finished'. The log is in data/setup-log.txt (no secrets in it)."
read -r -p "Press Enter to close."

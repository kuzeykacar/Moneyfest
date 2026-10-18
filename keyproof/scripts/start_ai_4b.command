#!/bin/bash
# Start KeyProof's local AI: Qwen3.5 4B (Q4_K_M) via QVAC on http://127.0.0.1:11436. Keep this window open.
# First run downloads the model (~2.7 GB) from Hugging Face and checks its SHA-256 (same file QVAC's registry uses).
cd "$(dirname "$0")/.." || exit 1
KP="$PWD"
M="$KP/data/models/Qwen3.5-4B-Q4_K_M.gguf"
SUM=00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4
mkdir -p "$KP/data/models"
if [ ! -f "$M" ]; then
  echo "Downloading Qwen3.5 4B (~2.7 GB)..."
  curl -fL --retry 3 -C - -o "$M.part" \
    "https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf" || { echo "download failed"; read -r; exit 1; }
  echo "$SUM  $M.part" | shasum -a 256 -c - || { echo "checksum mismatch"; read -r; exit 1; }
  mv "$M.part" "$M"
fi
export PATH="$HOME/Moneyfest/.node/bin:$PATH"
cd "$HOME/Moneyfest/.qvac" || { echo "QVAC not installed: run Moneyfest/scripts/setup_ai.command once"; read -r; exit 1; }
cat > qvac.keyproof.json <<JSON
{"serve": {"models": {"keyproof": {"src": "$M", "type": "llm", "default": true, "preload": true, "config": {"ctx_size": 8192}}}}}
JSON
npx qvac serve --openai -c qvac.keyproof.json --model keyproof --port 11436 --host 127.0.0.1 2>&1 | tee "$KP/data/ai4b-serve.txt"

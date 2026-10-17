#!/bin/bash
# Start the local AI (QVAC, Qwen3 1.7B) on http://127.0.0.1:11434. Reuses the Moneyfest install.
# Keep this window open while using the app.
QV="$HOME/Moneyfest/.qvac"
if [ ! -d "$QV/node_modules/@qvac/cli" ]; then
  echo "QVAC is not installed yet: double-click Moneyfest/scripts/setup_ai.command once."; read -r; exit 1
fi
export PATH="$HOME/Moneyfest/.node/bin:$PATH"
cd "$QV" && npx qvac serve --openai -c qvac.config.json --model moneyfest --port 11434 --host 127.0.0.1

#!/bin/bash
# Moneyfest Aid: install Node.js + QVAC into this project (no admin needed) and start the local AI.
# Double-click in Finder. First run downloads Node (~50 MB) and a model (~0.5-1.5 GB).
# Leave this window open while using the app: it is the local AI server (http://127.0.0.1:11434).
cd "$(dirname "$0")/.." || exit 1
mkdir -p data .qvac
LOG=data/ai-setup.txt
: > "$LOG"
say() { echo; echo "== $1" | tee -a "$LOG"; }

say "1/4 Node.js (into .node, version 22 LTS)"
if [ ! -x .node/bin/node ]; then
  BASE=https://nodejs.org/dist/latest-v22.x
  FILE=$(curl -fsSL "$BASE/SHASUMS256.txt" | awk '/darwin-arm64.tar.gz/ {print $2}')
  SUM=$(curl -fsSL "$BASE/SHASUMS256.txt" | awk '/darwin-arm64.tar.gz/ {print $1}')
  echo "downloading $FILE" | tee -a "$LOG"
  curl -fL "$BASE/$FILE" -o "data/$FILE" || { echo "download failed" | tee -a "$LOG"; read -r; exit 1; }
  echo "$SUM  data/$FILE" | shasum -a 256 -c - | tee -a "$LOG" || { echo "checksum mismatch" | tee -a "$LOG"; read -r; exit 1; }
  mkdir -p .node && tar -xzf "data/$FILE" -C .node --strip-components 1 && rm "data/$FILE"
fi
export PATH="$PWD/.node/bin:$PATH"
node --version | tee -a "$LOG"

say "2/4 QVAC (into .qvac)"
cd .qvac || exit 1
[ -f package.json ] || npm init -y >/dev/null
[ -d node_modules/@qvac/cli ] || npm install @qvac/cli @qvac/sdk 2>&1 | tail -5 | tee -a "../$LOG"

say "3/4 Choosing a model"
node --input-type=module -e "
const m = await import('@qvac/sdk');
const qwen = Object.keys(m).filter(k => /^QWEN/.test(k)).sort();
console.log('available:', qwen.join(' '));
const prefer = [/^QWEN3_5_2B/, /^QWEN3_1_7B/, /^QWEN3_5_0_8B/, /^QWEN3_600M_INST_Q4\$/];
let pick = null;
for (const p of prefer) { pick = qwen.find(k => p.test(k) && !/MULTIMODAL|VL/.test(k)); if (pick) break; }
pick = pick || 'QWEN3_600M_INST_Q4';
console.log('picked:', pick);
const fs = await import('fs');
fs.writeFileSync('qvac.config.json', JSON.stringify({serve: {models: {moneyfest: {model: pick, default: true, preload: true, config: {ctx_size: 4096}}}}}, null, 2));
" 2>&1 | tee -a "../$LOG"
cat qvac.config.json | tee -a "../$LOG"

say "4/4 Starting the local AI server on http://127.0.0.1:11434 (first start downloads the model)"
echo "Keep this window open. Start the app with MONEYFEST_AI=qvac (scripts/run_real.command does this)."
npx qvac serve --openai -c qvac.config.json --model moneyfest --port 11434 --host 127.0.0.1 2>&1 | tee -a "../data/ai-serve.txt"

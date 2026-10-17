#!/bin/bash
# Moneyfest Aid: install rgb-lib (no Docker needed) and record what it offers.
# Double-click in Finder. Writes data/rgb-probe.txt (no secrets).
cd "$(dirname "$0")/.." || exit 1
mkdir -p data
OUT="data/rgb-probe.txt"
: > "$OUT"
log() { echo "$@" | tee -a "$OUT"; }

log "== Python"
PY=""
for p in python3.13 python3.12 python3.11 python3.10 python3; do
  command -v "$p" >/dev/null && { PY="$p"; break; }
done
log "using: $(command -v $PY) $($PY --version 2>&1)"
log "machine: $(uname -m) $(sw_vers -productVersion 2>/dev/null)"

log "== Installing rgb-lib into .rgb-venv"
[ -x .rgb-venv/bin/python ] || $PY -m venv .rgb-venv >>"$OUT" 2>&1
.rgb-venv/bin/pip install --quiet --upgrade pip >>"$OUT" 2>&1
.rgb-venv/bin/pip uninstall -y rgb-lib >>"$OUT" 2>&1; .rgb-venv/bin/pip install "rgb-lib==0.3.0b7" >>"$OUT" 2>&1
.rgb-venv/bin/pip show rgb-lib >>"$OUT" 2>&1

log "== rgb-lib API"
.rgb-venv/bin/python - >>"$OUT" 2>&1 <<'EOF'
import inspect, rgb_lib
print("module file:", rgb_lib.__file__)
print("BitcoinNetwork:", [n for n in dir(rgb_lib.BitcoinNetwork) if not n.startswith("_")])
for name in ["Wallet", "WalletData", "Online", "Recipient", "Assignment", "Keys", "AssetSchema", "DatabaseType"]:
    obj = getattr(rgb_lib, name, None)
    print(f"\n### {name}: {obj}")
    if obj is None:
        continue
    try:
        print("  init:", inspect.signature(obj.__init__))
    except Exception as e:
        print("  init: ?", e)
    for m in sorted(dir(obj)):
        if m.startswith("_"):
            continue
        try:
            print(f"  {m}{inspect.signature(getattr(obj, m))}")
        except Exception:
            print(f"  {m}")
print("\n### top-level functions")
for m in sorted(dir(rgb_lib)):
    f = getattr(rgb_lib, m)
    if callable(f) and not inspect.isclass(f) and not m.startswith("_"):
        try:
            print(f"  {m}{inspect.signature(f)}")
        except Exception:
            print(f"  {m}")
EOF

log "== Network check (Mutinynet indexer)"
curl -s -m 10 https://mutinynet.com/api/blocks/tip/height >>"$OUT" 2>&1 && log " <- mutinynet block height"
log "== done"
echo
echo "Finished. You can close this window."

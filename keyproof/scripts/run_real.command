#!/bin/bash
# KeyProof with REAL RGB on Bitcoin Mutinynet and the local AI (http://127.0.0.1:8010).
cd "$(dirname "$0")/.." || exit 1
AI=fake; (curl -s -m 2 http://127.0.0.1:11436/v1/models >/dev/null || curl -s -m 2 http://127.0.0.1:11434/v1/models >/dev/null) && AI=qvac
# Tenant wallet on Tether WDK (local service on 127.0.0.1:8011), if installed (scripts/wdk_check.command installs it)
if [ -d wdk/node_modules/@utexo ] && [ -f data/wdk/seed.txt ]; then
  lsof -ti tcp:8011 | xargs kill 2>/dev/null
  (PATH="$PWD/../.node/bin:$PATH" node wdk/server.mjs >> data/wdk-server.txt 2>&1 &)
fi
KEYPROOF_AI=$AI KEYPROOF_RGB=rgb .venv/bin/python keyproof/app.py 2>&1 | tee -a data/app-real.txt

#!/bin/bash
# KeyProof with REAL RGB on Bitcoin Mutinynet and the local AI (http://127.0.0.1:8010).
cd "$(dirname "$0")/.." || exit 1
AI=fake; curl -s -m 2 http://127.0.0.1:11434/v1/models >/dev/null && AI=qvac
KEYPROOF_AI=$AI KEYPROOF_RGB=rgb .venv/bin/python keyproof/app.py 2>&1 | tee -a data/app-real.txt

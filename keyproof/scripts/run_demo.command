#!/bin/bash
# KeyProof with simulated RGB and the local AI if it is running (http://127.0.0.1:8010).
cd "$(dirname "$0")/.." || exit 1
AI=fake; curl -s -m 2 http://127.0.0.1:11434/v1/models >/dev/null && AI=qvac
KEYPROOF_AI=$AI KEYPROOF_RGB=fake .venv/bin/python keyproof/app.py

#!/bin/bash
# Test the local AI reading the tenant's documents (needs the local AI running). Writes data/ai-docs.txt
cd "$(dirname "$0")/.." || exit 1
.venv/bin/python tools/test_ai_docs.py "$@" 2>&1 | tee data/ai-docs.txt
echo; echo "Finished. You can close this window."

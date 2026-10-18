#!/bin/bash
# Stop whatever is using port 8010 (a stuck KeyProof) and start KeyProof again with real RGB + local AI.
cd "$(dirname "$0")/.." || exit 1
PIDS=$(lsof -ti tcp:8010)
if [ -n "$PIDS" ]; then echo "Stopping old KeyProof: $PIDS"; kill $PIDS; sleep 2; kill -9 $(lsof -ti tcp:8010) 2>/dev/null; fi
exec ./scripts/run_real.command

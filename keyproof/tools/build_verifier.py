"""Build the standalone verifier page from the official verification key and trusted-issuer list.
    python3 tools/build_verifier.py            -> web/verify.html (served by the app, uses local snarkjs)
    python3 tools/build_verifier.py --cdn OUT  -> a single file that loads snarkjs from a CDN (to host anywhere)
"""
import json, os, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
t = open(os.path.join(R, "tools", "verify_template.html")).read()
vk = open(os.path.join(R, "web", "zk", "verification_key.json")).read()
tr = open(os.path.join(R, "web", "zk", "trusted_issuers.json")).read()
t = t.replace("__VK__", vk).replace("__TRUST__", tr)
if "--cdn" in sys.argv:
    out = sys.argv[sys.argv.index("--cdn") + 1]
    t = t.replace("__SNARKJS__", '<script src="https://cdn.jsdelivr.net/npm/snarkjs@0.7.4/build/snarkjs.min.js"></script>')
else:
    out = os.path.join(R, "web", "verify.html")
    t = t.replace("__SNARKJS__", '<script src="zk/snarkjs.min.js"></script>')
open(out, "w").write(t)
print("written", out)

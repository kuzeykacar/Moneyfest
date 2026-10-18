# Third-party code and data in KeyProof

KeyProof is our own code, written during the hackathon. It builds on these open-source projects.
Files copied into this repository keep their original license next to them.

## Included in this repository
| What | Where | Source | License |
|---|---|---|---|
| snarkjs (browser build) | `web/zk/snarkjs.min.js` | https://github.com/iden3/snarkjs | GPL-3.0 – `web/zk/snarkjs-LICENSE` |
| asn1crypto | `vendor/asn1crypto/` | https://github.com/wbond/asn1crypto | MIT – `vendor/asn1crypto/LICENSE` |
| QR Code Generator for JavaScript (Kazuhiko Arase) | `web/vendor/qrcode.js` | https://github.com/kazuhikoarase/qrcode-generator | MIT – `web/vendor/qrcode-LICENSE` |
| Poseidon hash constants | `keyproof/poseidon_constants.json` | taken from circomlibjs (https://github.com/iden3/circomlibjs) so our Python Poseidon matches circomlib | GPL-3.0 (circomlibjs) |
| circom compiler binary (Linux) | `tools/circom-linux` | https://github.com/iden3/circom release 2.2.2 | GPL-3.0 |
| Compiled circuit + keys | `web/zk/keyproof.wasm`, `keyproof_final.zkey`, `verification_key.json` | built from our `circuits/keyproof.circom`, which includes circomlib templates (Poseidon, EdDSAPoseidonVerifier, comparators) | circomlib: GPL-3.0 |

## Used, not included (installed or downloaded by our scripts)
| What | Used for | License |
|---|---|---|
| circomlib (https://github.com/iden3/circomlib) – `npm install circomlib` before recompiling the circuit | circuit templates | GPL-3.0 |
| rgb-lib Python bindings (https://github.com/RGB-Tools/rgb-lib-python) | RGB wallets | MIT / Apache-2.0 |
| pyca/cryptography (https://github.com/pyca/cryptography) | signatures, certificates | Apache-2.0 / BSD |
| QVAC (`@qvac/cli`, `@qvac/sdk`) | local AI server | see npm package |
| Qwen3.5 4B / Qwen3 1.7B GGUF (https://huggingface.co/unsloth/Qwen3.5-4B-GGUF) | local language models | Apache-2.0 (Qwen) |
| Tether WDK RGB module `@utexo/wdk-wallet-rgb` | tenant wallet | see npm package |
| Playwright (https://playwright.dev) | browser tests | Apache-2.0 |
| KaleidoSwap Mutinynet indexer and RGB proxy, Mutinynet faucet | test network services | online services |

## Note
Because the circuit uses circomlib and the app ships snarkjs (both GPL-3.0), anyone redistributing KeyProof should
keep those licenses and make the source available, as this public repository does.

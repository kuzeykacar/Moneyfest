// Step 1 check: can the WDK RGB wallet open a wallet on our Bitcoin test network (Mutinynet / signet)?
// Uses a NEW throwaway seed (data/wdk/seed.txt, git-ignored). Spends nothing.
import fs from "fs";
import path from "path";
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const pkgDir = path.join(root, "wdk", "node_modules", "@utexo", "wdk-wallet-rgb");
console.log("package.json:", fs.readFileSync(path.join(pkgDir, "package.json"), "utf8").slice(0, 1500));
// look for network names the module accepts
const walk = (d, out = []) => { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); const s = fs.statSync(p);
  if (s.isDirectory() && f !== "node_modules") walk(p, out); else if (/\.(m?js|cjs|d\.ts)$/.test(f)) out.push(p); } return out; };
const hits = new Set();
for (const f of walk(pkgDir)) { const t = fs.readFileSync(f, "utf8"); for (const m of t.matchAll(/['"](mainnet|testnet|testnet4|signet|signetCustom|signet_custom|regtest|mutinynet)['"]/gi)) hits.add(m[1]); }
console.log("network names found in the module:", [...hits]);
const { default: WalletManagerRgb } = await import("@utexo/wdk-wallet-rgb");
const seedFile = path.join(root, "data", "wdk", "seed.txt");
fs.mkdirSync(path.dirname(seedFile), { recursive: true });
let seed = fs.existsSync(seedFile) ? fs.readFileSync(seedFile, "utf8").trim() : null;
if (!seed) {
  try { const bip39 = require("bip39"); seed = bip39.generateMnemonic(); } catch (e) {
    try { const m = await import("@tetherto/wdk-wallet"); seed = (m.default?.getRandomSeedPhrase || m.WalletManager?.getRandomSeedPhrase)?.(); } catch (e2) {}
  }
  if (!seed && WalletManagerRgb.getRandomSeedPhrase) seed = WalletManagerRgb.getRandomSeedPhrase();
  if (!seed) throw new Error("could not make a seed phrase");
  fs.writeFileSync(seedFile, seed, { mode: 0o600 });
}
for (const network of ["signet", "signetCustom", "signet_custom", "testnet"]) {
  try {
    const m = new WalletManagerRgb(seed, { network, dataDir: path.join(root, "data", "wdk", network),
      indexerUrl: "https://esplora.signet.kaleidoswap.com", transportEndpoint: "rpcs://proxy.kaleidoswap.com/json-rpc" });
    const a = await m.getAccount(0);
    console.log("network", network, "-> OK, address", await a.getAddress());
    try { console.log("  balance", JSON.stringify(await a.getBalance?.())); } catch (e) { console.log("  balance error:", e.message); }
    m.dispose?.();
  } catch (e) { console.log("network", network, "-> FAILED:", String(e.message || e).slice(0, 200)); }
}
console.log("done");

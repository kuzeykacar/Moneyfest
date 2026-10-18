// Tenant wallet on Tether WDK (self-custodial, seed stays in data/wdk, git-ignored).
// Tiny local service for the KeyProof app: GET /wallet -> {address, balance, network}. Listens on 127.0.0.1 only.
import fs from "fs";
import http from "http";
import path from "path";
import WalletManagerRgb from "@utexo/wdk-wallet-rgb";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const seed = fs.readFileSync(path.join(root, "data", "wdk", "seed.txt"), "utf8").trim();
const cfg = { network: "signet", dataDir: path.join(root, "data", "wdk", "tenant"),
  indexerUrl: process.env.RGB_INDEXER || "https://esplora.signet.kaleidoswap.com",
  transportEndpoint: process.env.RGB_PROXY || "rpcs://proxy.kaleidoswap.com/json-rpc" };
const big = (_, v) => (typeof v === "bigint" ? Number(v) : v);
let manager = null, account = null, cache = null, cacheAt = 0;

async function info() {
  if (!account) { manager = new WalletManagerRgb(seed, cfg); account = await manager.getAccount(0); }
  if (cache && Date.now() - cacheAt < 20000) return cache;
  const address = await account.getAddress();
  let balance = null, error = null;
  try { balance = JSON.parse(JSON.stringify(await account.getBalance(), big)); } catch (e) { error = String(e.message || e); }
  cache = { ok: true, sdk: "Tether WDK (@utexo/wdk-wallet-rgb)", network: "Bitcoin signet (Mutinynet)", address, balance, error };
  cacheAt = Date.now();
  return cache;
}

http.createServer(async (req, res) => {
  let out;
  try { out = req.url.startsWith("/wallet") ? await info() : { ok: false, error: "not found" }; }
  catch (e) { out = { ok: false, error: String(e.message || e) }; account = null; }
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify(out, big));
}).listen(8011, "127.0.0.1", () => console.log("KeyProof WDK wallet service on 127.0.0.1:8011"));

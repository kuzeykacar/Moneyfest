// One-time trusted setup for the KeyProof circuit (demo ceremony: our own random contributions).
// Produces web/zk/keyproof_final.zkey and web/zk/verification_key.json.
// The browser build of snarkjs has no file system, so files are passed as in-memory objects.
const s = require("./snark.cjs");
const fs = require("fs");
const crypto = require("crypto");
const POWER = 16;
const ent = () => crypto.randomBytes(32).toString("hex");
const mem = () => ({ type: "mem" });
const load = (p) => ({ type: "mem", data: new Uint8Array(fs.readFileSync(p)) });
const save = (o, p) => fs.writeFileSync(p, Buffer.from(o.data));
(async () => {
  const curve = await s.curves.getCurveFromName("bn128", true);
  const t0 = Date.now(), log = (m) => console.log(((Date.now() - t0) / 1000).toFixed(0) + "s", m);
  if (!fs.existsSync("build/pot_final.ptau")) {
    const p0 = mem(); await s.powersOfTau.newAccumulator(curve, POWER, p0); log("ptau new");
    const p1 = mem(); await s.powersOfTau.contribute(p0, p1, "keyproof-1", ent()); log("ptau contribute");
    const p2 = mem(); await s.powersOfTau.beacon(p1, p2, "beacon", ent(), 10); log("ptau beacon");
    const pf = mem(); await s.powersOfTau.preparePhase2(p2, pf); log("ptau prepared");
    save(pf, "build/pot_final.ptau");
  }
  const z0 = mem(); await s.zKey.newZKey(load("build/keyproof.r1cs"), load("build/pot_final.ptau"), z0); log("zkey new");
  const z1 = mem(); await s.zKey.contribute(z0, z1, "keyproof-team", ent()); log("zkey contribute");
  const zf = mem(); await s.zKey.beacon(z1, zf, "final", ent(), 10); log("zkey beacon");
  save(zf, "web/zk/keyproof_final.zkey");
  const vk = await s.zKey.exportVerificationKey(load("web/zk/keyproof_final.zkey"));
  fs.writeFileSync("web/zk/verification_key.json", JSON.stringify(vk));
  log("done");
  process.exit(0);
})().catch((e) => { console.error(e); process.exit(1); });

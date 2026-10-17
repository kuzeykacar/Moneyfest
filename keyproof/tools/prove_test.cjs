// Full Groth16 proof + verify with the demo documents (same code path as the browser).
const fs = require("fs");
const s = require("./snark.cjs");
require("../web/zk/keyproof.js");
const Z = globalThis.KeyProofZK;
const cards = JSON.parse(fs.readFileSync("build/cards.json", "utf8"));
const dummy = JSON.parse(fs.readFileSync("web/zk/dummy_card.json", "utf8"));
const vk = JSON.parse(fs.readFileSync("web/zk/verification_key.json", "utf8"));
const mem = (p) => ({ type: "mem", data: new Uint8Array(fs.readFileSync(p)) });
(async () => {
  const rules = { checks: { identity: true, income: true, occupation: true, savings: false, guarantor: false },
    minIncome: 1500, allowStudent: true, allowEmployed: false, leaseEnd: "2027-07-31", today: "2026-10-18", maxAgeDays: 90, requestId: "987654321" };
  const req = Z.publicRequest(rules);
  const t0 = Date.now();
  const { proof, publicSignals } = await s.groth16.fullProve(Z.circuitInput(req, cards, dummy), mem("web/zk/keyproof.wasm"), mem("web/zk/keyproof_final.zkey"));
  console.log("prove ms", Date.now() - t0, "proof bytes", JSON.stringify(proof).length, "signals", publicSignals.length);
  console.log("verify:", await s.groth16.verify(vk, publicSignals, proof));
  const bad = [...publicSignals]; bad[17] = "1000"; // landlord's minIncome changed
  let r; try { r = await s.groth16.verify(vk, bad, proof); } catch (e) { r = "error (" + String(e.message).slice(0, 80) + ")"; }
  console.log("verify with easier minIncome:", r);
  process.exit(0);
})();

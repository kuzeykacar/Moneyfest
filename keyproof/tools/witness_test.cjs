// Check the circuit accepts the demo documents and rejects bad ones (witness only, no proof).
const fs = require("fs");
require("../web/zk/keyproof.js");
const Z = globalThis.KeyProofZK;
const wc = require("../build/keyproof_js/witness_calculator.js");
const cards = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const dummy = JSON.parse(fs.readFileSync("web/zk/dummy_card.json", "utf8"));
const base = { checks: { identity: true, income: true, occupation: true, savings: false, guarantor: false },
  minIncome: 1500, allowStudent: true, allowEmployed: true, leaseEnd: "2027-07-31",
  today: "2026-10-18", maxAgeDays: 90, requestId: 12345 };
const cases = [
  ["3 checks, should pass", base],
  ["all 5, should pass", { ...base, checks: { identity: 1, income: 1, occupation: 1, savings: 1, guarantor: 1 }, minSavings: 3000, minGuarantor: 3000 }],
  ["income 2000, should FAIL", { ...base, minIncome: 2000 }],
  ["lease to 2028, should FAIL", { ...base, leaseEnd: "2028-06-30" }],
  ["employed only, should FAIL", { ...base, allowStudent: false }],
];
(async () => {
  const calc = await wc(fs.readFileSync("build/keyproof_js/keyproof.wasm"));
  for (const [name, rules] of cases) {
    const req = Z.publicRequest(rules);
    const pre = Z.precheck(req, cards).map((p) => `${p.slot}:${p.ok ? "ok" : "NO(" + p.why + ")"}`).join(" ");
    let res;
    try { await calc.calculateWitness(Z.circuitInput(req, cards, dummy), true); res = "witness OK"; }
    catch (e) { res = "witness REJECTED"; }
    console.log(name.padEnd(28), res.padEnd(17), pre);
  }
  // tampered card value with original signature
  const bad = JSON.parse(JSON.stringify(cards)); bad.income.v1 = 2650;
  try { await calc.calculateWitness(Z.circuitInput(Z.publicRequest(base), bad, dummy), true); console.log("edited card value: witness OK (BAD)"); }
  catch (e) { console.log("edited card value: witness REJECTED (good)"); }
})();

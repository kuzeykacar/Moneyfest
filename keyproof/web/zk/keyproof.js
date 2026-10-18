// KeyProof ZK helpers, shared by the tenant page (makes proofs) and the landlord page (checks them).
// Plain script: works in the browser (window.KeyProofZK) and in Node (globalThis.KeyProofZK).
(function (root) {
  const SLOTS = ["identity", "income", "occupation", "savings", "guarantor"];
  const EPOCH = Date.UTC(1970, 0, 1);
  const DAY = 86400000;

  function dayNumber(isoDate) {
    return Math.round((Date.parse(isoDate + "T00:00:00Z") - EPOCH) / DAY);
  }

  // Landlord rules (from checkboxes) -> public numbers for the circuit.
  // rules: {checks: {identity:true,...}, minIncome, allowStudent, allowEmployed, leaseEnd (YYYY-MM-DD or ""),
  //         minSavings, minGuarantor, today (YYYY-MM-DD), maxAgeDays, requestId}
  function publicRequest(rules) {
    const today = rules.today;
    const t = new Date(today + "T00:00:00Z");
    const cutoff = new Date(Date.UTC(t.getUTCFullYear() - 18, t.getUTCMonth(), t.getUTCDate()));
    return {
      enabled: SLOTS.map((s) => (rules.checks[s] ? 1 : 0)),
      adultCutoff: Math.round((cutoff - EPOCH) / DAY),
      minIncome: rules.minIncome || 0,
      allowStudent: rules.allowStudent ? 1 : 0,
      allowEmployed: rules.allowEmployed ? 1 : 0,
      leaseEnd: rules.leaseEnd ? dayNumber(rules.leaseEnd) : 0,
      minSavings: rules.minSavings || 0,
      minGuarantor: rules.minGuarantor || 0,
      today: dayNumber(today),
      maxAgeDays: rules.maxAgeDays || 90,
      requestId: String(rules.requestId),
      requiredSex: rules.sex === "M" ? 1 : rules.sex === "F" ? 2 : 0,
    };
  }

  // Check the rules in plain code first, so the tenant sees which check fails and why
  // (the circuit enforces the same rules; it just cannot say which one failed).
  function precheck(req, cards) {
    const out = [];
    const c = (i) => cards[SLOTS[i]];
    const need = (i) => req.enabled[i] === 1;
    const fresh = (card) => card.issuedAt + req.maxAgeDays >= req.today;
    const holder = (cards.identity || Object.values(cards).find(Boolean) || {}).holder;
    SLOTS.forEach((s, i) => {
      if (!need(i)) return;
      const card = c(i);
      if (!card) return out.push({ slot: s, ok: false, why: "document missing" });
      if (card.type !== i + 1) return out.push({ slot: s, ok: false, why: "wrong kind of document" });
      if (card.holder !== holder) return out.push({ slot: s, ok: false, why: "belongs to a different person" });
      let ok = true, why = "";
      if (s === "identity") {
        ok = card.v1 <= req.adultCutoff; why = ok ? "18 or older" : "under 18";
        if (ok && req.requiredSex) { ok = card.v2 === req.requiredSex; why = ok ? "18 or older, sex as requested" : "sex does not match the request"; }
      }
      if (s === "income") { ok = card.v1 >= req.minIncome && fresh(card); why = !fresh(card) ? "document too old" : ok ? "income meets the minimum" : "income below the minimum"; }
      if (s === "occupation") {
        const st = (card.v1 === 1 && req.allowStudent) || (card.v1 === 2 && req.allowEmployed);
        const lasts = card.v2 >= req.leaseEnd;
        ok = st && lasts;
        why = !st ? "status not accepted" : !lasts ? "ends before the lease ends" : (card.v1 === 1 ? "student" : "employed") + ", lasts the whole lease";
      }
      if (s === "savings") { ok = card.v1 >= req.minSavings && fresh(card); why = !fresh(card) ? "document too old" : ok ? "savings meet the minimum" : "savings below the minimum"; }
      if (s === "guarantor") { ok = card.v1 >= req.minGuarantor && fresh(card); why = !fresh(card) ? "document too old" : ok ? "guarantor's income meets the minimum" : "guarantor's income below the minimum"; }
      out.push({ slot: s, ok, why });
    });
    return out;
  }

  // Full circuit input: public request + the tenant's private cards.
  function circuitInput(req, cards, dummy) {
    const input = Object.assign({}, req, {
      enabled: req.enabled.map(String),
      issuerAx: [], issuerAy: [], card: [], R8x: [], R8y: [], S: [], holder: "0",
    });
    for (const k of ["adultCutoff", "minIncome", "allowStudent", "allowEmployed", "leaseEnd",
                     "minSavings", "minGuarantor", "today", "maxAgeDays", "requiredSex"]) input[k] = String(req[k] || 0);
    SLOTS.forEach((s, i) => {
      const card = req.enabled[i] ? cards[s] : null;
      if (card) {
        input.holder = card.holder;
        input.card.push([card.type, card.holder, card.v1, card.v2, card.issuedAt].map(String));
        input.issuerAx.push(card.issuerKey[0]); input.issuerAy.push(card.issuerKey[1]);
        input.R8x.push(card.sig[0]); input.R8y.push(card.sig[1]); input.S.push(card.sig[2]);
      } else {
        input.card.push(dummy.fields.map(String));
        input.issuerAx.push(dummy.issuerKey[0]); input.issuerAy.push(dummy.issuerKey[1]);
        input.R8x.push(dummy.sig[0]); input.R8y.push(dummy.sig[1]); input.S.push(dummy.sig[2]);
      }
    });
    return input;
  }

  // Public signals order (from circom): outputs first, then public inputs in declaration order.
  function publicSignals(req, issuerKeys, holderTag) {
    return [holderTag, ...req.enabled.map(String),
      ...issuerKeys.map((k) => k[0]), ...issuerKeys.map((k) => k[1]),
      ...["adultCutoff", "minIncome", "allowStudent", "allowEmployed", "leaseEnd", "minSavings",
          "minGuarantor", "today", "maxAgeDays", "requestId", "requiredSex"].map((k) => String(req[k] || 0))];
  }

  root.KeyProofZK = { SLOTS, dayNumber, publicRequest, precheck, circuitInput, publicSignals };
})(typeof window !== "undefined" ? window : globalThis);

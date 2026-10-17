pragma circom 2.1.6;

// KeyProof: prove that signed documents pass a landlord's rules, without showing the documents.
//
// Each document carries a small "data card" with 5 numbers, signed by its issuer (EdDSA-Poseidon):
//   [docType, holder, value1, value2, issuedAt]
// Slots (docType):
//   1 identity     value1 = birth date (days since 1970)
//   2 income       value1 = monthly income (EUR)
//   3 occupation   value1 = status (1 student, 2 employed), value2 = end date (days)
//   4 savings      value1 = balance (EUR)
//   5 guarantor    value1 = guarantor's monthly income (EUR), holder = the tenant they guarantee
//
// Public: which checks the landlord ticked, the limits, and the issuer keys used.
// Private: the cards and their signatures. If any ticked check fails, no proof can be made.

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/eddsaposeidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

template SignedCard() {
    signal input enabled;
    signal input f[5];
    signal input Ax;
    signal input Ay;
    signal input R8x;
    signal input R8y;
    signal input S;

    component h = Poseidon(5);
    for (var i = 0; i < 5; i++) { h.inputs[i] <== f[i]; }

    component v = EdDSAPoseidonVerifier();
    v.enabled <== enabled;
    v.Ax <== Ax;
    v.Ay <== Ay;
    v.R8x <== R8x;
    v.R8y <== R8y;
    v.S <== S;
    v.M <== h.out;
}

// enabled => (a >= b)
template RequireGE(bits) {
    signal input enabled;
    signal input a;
    signal input b;
    component ge = GreaterEqThan(bits);
    ge.in[0] <== a;
    ge.in[1] <== b;
    enabled * (1 - ge.out) === 0;
}

template KeyProof() {
    var N = 5;
    var BITS = 40;

    // ---- public inputs (the landlord's request)
    signal input enabled[N];        // 1 = the landlord ticked this check
    signal input issuerAx[N];       // issuer key for each slot (landlord checks it is a trusted issuer)
    signal input issuerAy[N];
    signal input adultCutoff;       // birth date must be on or before this day
    signal input minIncome;
    signal input allowStudent;
    signal input allowEmployed;
    signal input leaseEnd;          // contract or enrolment must last until this day (0 = no check)
    signal input minSavings;
    signal input minGuarantor;
    signal input today;
    signal input maxAgeDays;        // money documents must be newer than this
    signal input requestId;         // ties the proof to one landlord request

    // ---- private inputs (the tenant's documents)
    signal input holder;
    signal input card[N][5];
    signal input R8x[N];
    signal input R8y[N];
    signal input S[N];

    // ---- public output
    signal output holderTag;        // same tenant + same request => same tag; unlinkable across landlords

    component sig[N];
    for (var i = 0; i < N; i++) {
        enabled[i] * (1 - enabled[i]) === 0;                 // 0 or 1
        sig[i] = SignedCard();
        sig[i].enabled <== enabled[i];
        for (var j = 0; j < 5; j++) { sig[i].f[j] <== card[i][j]; }
        sig[i].Ax <== issuerAx[i];
        sig[i].Ay <== issuerAy[i];
        sig[i].R8x <== R8x[i];
        sig[i].R8y <== R8y[i];
        sig[i].S <== S[i];
        enabled[i] * (card[i][0] - (i + 1)) === 0;           // right kind of document in this slot
        enabled[i] * (card[i][1] - holder) === 0;            // every document belongs to the same person
    }

    // 1 identity: adult
    component adult = RequireGE(BITS);
    adult.enabled <== enabled[0];
    adult.a <== adultCutoff;
    adult.b <== card[0][2];

    // 2 income
    component inc = RequireGE(BITS);
    inc.enabled <== enabled[1];
    inc.a <== card[1][2];
    inc.b <== minIncome;

    // 3 occupation: allowed status, and lasts until the lease end
    component isStudent = IsEqual();
    isStudent.in[0] <== card[2][2];
    isStudent.in[1] <== 1;
    component isEmployed = IsEqual();
    isEmployed.in[0] <== card[2][2];
    isEmployed.in[1] <== 2;
    signal okStudent <== isStudent.out * allowStudent;
    signal okEmployed <== isEmployed.out * allowEmployed;
    enabled[2] * (1 - okStudent - okEmployed) === 0;
    component lasts = RequireGE(BITS);
    lasts.enabled <== enabled[2];
    lasts.a <== card[2][3];
    lasts.b <== leaseEnd;

    // 4 savings
    component sav = RequireGE(BITS);
    sav.enabled <== enabled[3];
    sav.a <== card[3][2];
    sav.b <== minSavings;

    // 5 guarantor
    component gua = RequireGE(BITS);
    gua.enabled <== enabled[4];
    gua.a <== card[4][2];
    gua.b <== minGuarantor;

    // money documents must be recent: issuedAt + maxAgeDays >= today
    component fresh[3];
    var moneySlots[3] = [1, 3, 4];
    for (var k = 0; k < 3; k++) {
        fresh[k] = RequireGE(BITS);
        fresh[k].enabled <== enabled[moneySlots[k]];
        fresh[k].a <== card[moneySlots[k]][4] + maxAgeDays;
        fresh[k].b <== today;
    }

    component tag = Poseidon(2);
    tag.inputs[0] <== holder;
    tag.inputs[1] <== requestId;
    holderTag <== tag.out;
}

component main {public [enabled, issuerAx, issuerAy, adultCutoff, minIncome, allowStudent, allowEmployed,
                        leaseEnd, minSavings, minGuarantor, today, maxAgeDays, requestId]} = KeyProof();

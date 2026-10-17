"""ZK-friendly cryptography in plain Python: Poseidon hash, Baby Jubjub curve, EdDSA-Poseidon.

These match circomlib exactly, so a card signed here can be checked inside the circom circuit.
Issuers use this to sign the small "data card" inside each document.
"""

import hashlib
import json
import os
import secrets

# BN254 scalar field: every number inside the circuit lives in this field.
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# ---------------------------------------------------------------- Poseidon
with open(os.path.join(os.path.dirname(__file__), "poseidon_constants.json")) as _f:
    _K = json.load(_f)
_C = [[int(x, 16) if isinstance(x, str) and x.startswith("0x") else int(x) for x in row] for row in _K["C"]]
_M = [[[int(x, 16) if isinstance(x, str) and x.startswith("0x") else int(x) for x in r] for r in m] for m in _K["M"]]
_ROUNDS_F = 8
_ROUNDS_P = [56, 57, 56, 60, 60]


def poseidon(inputs):
    """Poseidon hash of 1 to 5 field elements (same as circomlib Poseidon(n))."""
    n = len(inputs)
    assert 1 <= n <= 5
    t = n + 1
    C, M, rp = _C[t - 2], _M[t - 2], _ROUNDS_P[t - 2]
    state = [0] + [int(x) % P for x in inputs]
    for r in range(_ROUNDS_F + rp):
        state = [(a + C[r * t + i]) % P for i, a in enumerate(state)]
        if r < _ROUNDS_F // 2 or r >= _ROUNDS_F // 2 + rp:
            state = [pow(a, 5, P) for a in state]
        else:
            state[0] = pow(state[0], 5, P)
        state = [sum(M[i][j] * state[j] for j in range(t)) % P for i in range(t)]
    return state[0]


# ---------------------------------------------------------------- Baby Jubjub
A_COEF, D_COEF = 168700, 168696
BASE8 = (5299619240641551281634865583518297030282874472190772894086521144482721001553,
         16950150798460657717958625567821834550301663161624707787222815936182638968203)
SUB_ORDER = 2736030358979909402780800718157159386076813972158567259200215660948447373041


def point_add(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    t = D_COEF * x1 * x2 * y1 * y2 % P
    x3 = (x1 * y2 + y1 * x2) * pow(1 + t, -1, P) % P
    y3 = (y1 * y2 - A_COEF * x1 * x2) * pow(1 - t, -1, P) % P
    return (x3, y3)


def point_mul(pt, k):
    result, addend = (0, 1), pt
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


# ---------------------------------------------------------------- EdDSA-Poseidon
def new_private_key():
    """A random secret. Public key = k*Base8; signing uses s = 8k (same as circomlib's pruned scalar)."""
    return secrets.randbelow(SUB_ORDER - 1) + 1


def public_key(k):
    return point_mul(BASE8, k)


def sign(k, msg):
    """Sign one field element. Returns (R8x, R8y, S)."""
    A = public_key(k)
    s = 8 * k
    r = int.from_bytes(hashlib.sha512(k.to_bytes(32, "big") + int(msg).to_bytes(32, "big")).digest(), "big") % SUB_ORDER
    R8 = point_mul(BASE8, r)
    hm = poseidon([R8[0], R8[1], A[0], A[1], msg])
    S = (r + hm * s) % SUB_ORDER
    return R8[0], R8[1], S


def verify(A, msg, sig):
    """Check S*B8 == R8 + 8*hm*A, exactly like circomlib's EdDSAPoseidonVerifier."""
    R8x, R8y, S = sig
    if S >= SUB_ORDER:
        return False
    hm = poseidon([R8x, R8y, A[0], A[1], msg])
    left = point_mul(BASE8, S)
    right = point_add((R8x, R8y), point_mul(A, 8 * hm))
    return left == right


def to_field(text):
    """Turn a string (e.g. a fiscal code) into a field element."""
    return int.from_bytes(hashlib.sha256(text.encode()).digest(), "big") % P


if __name__ == "__main__":
    assert poseidon([1, 2]) == 7853200120776062878684798364095072458815029376092732009249414926327459813530
    k = new_private_key()
    m = poseidon([1, 2, 3, 4, 5])
    sig = sign(k, m)
    assert verify(public_key(k), m, sig)
    assert not verify(public_key(k), m + 1, sig)
    print("zkcrypto self-test ok")

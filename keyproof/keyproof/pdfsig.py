"""Digitally signed PDFs: create (for the demo issuers) and verify (for the tenant's app).

A signed PDF stores a CMS signature (PKCS#7, "adbe.pkcs7.detached") over every byte of the file
except the signature itself. Changing one character anywhere breaks it.

verify_pdf() runs 4 checks:
  1. not changed:   the bytes hash to what the issuer signed, and the signature covers the whole file
  2. trusted issuer: the signing certificate was issued by our trusted root
  3. still valid:   the certificate was valid when signing and has not been revoked
  4. right issuer:  the issuer is allowed to vouch for this kind of document
"""

import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vendor"))

from asn1crypto import cms  # noqa: E402
from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.serialization import pkcs7  # noqa: E402

# Our own (demo) certificate extension: issuer role, allowed document types, and its ZK card key.
KEYPROOF_OID = x509.ObjectIdentifier("1.3.6.1.4.1.57264.7.1")
SIG_SPACE = 16384  # bytes reserved for the signature
DOC_TYPES = {1: "identity", 2: "income", 3: "occupation", 4: "savings", 5: "guarantor"}


def issuer_info(cert):
    """Role, allowed document types and ZK key stored in an issuer certificate."""
    ext = cert.extensions.get_extension_for_oid(KEYPROOF_OID)
    return json.loads(ext.value.value.decode())


def _esc(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_signed_pdf(lines, card, signer_name, key, cert, signed_at=None):
    """Build a one-page PDF with `lines` of text and the data `card`, signed by `cert`/`key`.

    lines: list of (font, size, text); font "F1" regular or "F2" bold.
    """
    signed_at = signed_at or dt.datetime.now(dt.timezone.utc)
    y = 780
    content = ["BT"]
    for font, size, text in lines:
        content.append(f"/{font} {size} Tf 1 0 0 1 56 {y} Tm ({_esc(text)}) Tj")
        y -= size + 12
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")

    card_hex = json.dumps(card, separators=(",", ":")).encode().hex()
    m = signed_at.strftime("D:%Y%m%d%H%M%SZ")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [5 0 R] /SigFlags 3 >> /KeyProofCard 7 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 8 0 R /F2 9 0 R >> >> /Annots [5 0 R] >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Annot /Subtype /Widget /FT /Sig /T (Signature1) /Rect [0 0 0 0] /F 132 /P 3 0 R /V 6 0 R >>",
        ("<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /adbe.pkcs7.detached "
         f"/Name ({_esc(signer_name)}) /M ({m}) /Reason (Issued document) "
         "/ByteRange [0 ########## ########## ##########] "
         "/Contents <" + "0" * (2 * SIG_SPACE) + "> >>").encode(),
        b"<< /Type /KeyProofCard /Data <" + card_hex.encode() + b"> >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)

    start = out.index(b"/Contents <" + b"0" * 16) + len(b"/Contents ")
    end = start + 2 * SIG_SPACE + 2
    byte_range = b"[0 %010d %010d %010d]" % (start, end, len(out) - end)
    placeholder = b"[0 ########## ########## ##########]"
    assert len(byte_range) == len(placeholder)
    pos = out.index(placeholder)
    out[pos:pos + len(placeholder)] = byte_range

    signed_bytes = bytes(out[:start]) + bytes(out[end:])
    sig = (pkcs7.PKCS7SignatureBuilder().set_data(signed_bytes)
           .add_signer(cert, key, hashes.SHA256())
           .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature,
                                               pkcs7.PKCS7Options.NoCapabilities,
                                               pkcs7.PKCS7Options.Binary]))
    assert len(sig) <= SIG_SPACE
    hexsig = sig.hex().encode()
    out[start + 1:start + 1 + len(hexsig)] = hexsig
    return bytes(out)


def read_card(pdf):
    """The data card embedded in the PDF (covered by the PDF signature)."""
    m = re.search(rb"/Type /KeyProofCard /Data <([0-9a-fA-F]+)>", pdf)
    if not m:
        return None
    return json.loads(bytes.fromhex(m.group(1).decode()))


class Check:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail):
        self.items.append({"check": name, "ok": bool(ok), "detail": detail})
        return ok

    @property
    def ok(self):
        return bool(self.items) and all(i["ok"] for i in self.items)


def verify_pdf(pdf, root_cert, revoked_serials=(), expected_type=None, now=None):
    """Run the 4 checks. Returns {"ok", "checks", "issuer", "card"}."""
    now = now or dt.datetime.now(dt.timezone.utc)
    c = Check()
    result = {"ok": False, "checks": c.items, "issuer": None, "card": None}

    ranges = re.findall(rb"/ByteRange \[(\d+) (\d+) (\d+) (\d+)\]", pdf)
    if len(ranges) != 1:
        c.add("not changed", False, "no digital signature found" if not ranges else "more than one signature")
        return result
    a, b, cc, d = map(int, ranges[0])
    if a != 0 or cc + d != len(pdf):
        c.add("not changed", False, "content was added after signing")
        return result
    try:
        cms_der = bytes.fromhex(pdf[b + 1:cc - 1].decode())
    except ValueError:
        c.add("not changed", False, "signature is unreadable")
        return result
    try:
        info = cms.ContentInfo.load(_trim_der(cms_der))
        sd = info["content"]
        si = sd["signer_infos"][0]
        attrs = {at["type"].native: at["values"][0] for at in si["signed_attrs"]}
        signed_digest = attrs["message_digest"].native
        signer = next(cert for cert in sd["certificates"]
                      if cert.chosen.serial_number == si["sid"].chosen["serial_number"].native)
        cert = x509.load_der_x509_certificate(signer.chosen.dump())
    except Exception as e:  # malformed signature
        c.add("not changed", False, f"signature is unreadable ({type(e).__name__})")
        return result

    digest = hashlib.sha256(pdf[a:a + b] + pdf[cc:cc + d]).digest()
    attrs_der = b"\x31" + si["signed_attrs"].dump()[1:]
    try:
        cert.public_key().verify(si["signature"].native, attrs_der, ec.ECDSA(hashes.SHA256()))
        sig_ok = True
    except Exception:
        sig_ok = False
    if not c.add("not changed", digest == signed_digest and sig_ok,
                 "every byte matches what the issuer signed" if digest == signed_digest and sig_ok
                 else "the document was modified after it was signed"):
        return result

    try:
        cert.verify_directly_issued_by(root_cert)
        trusted = True
    except Exception:
        trusted = False
    name = cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value
    result["issuer"] = name
    if not c.add("trusted issuer", trusted,
                 f"{name}, certified by {root_cert.subject.rfc4514_string()}" if trusted
                 else f"{name} is not certified by a trusted authority"):
        return result

    signing_time = attrs.get("signing_time")
    when = signing_time.native if signing_time is not None else now
    valid = cert.not_valid_before_utc <= when <= cert.not_valid_after_utc
    revoked = cert.serial_number in set(revoked_serials)
    if not c.add("still valid", valid and not revoked,
                 "certificate revoked" if revoked else
                 ("certificate valid on signing date" if valid else "certificate expired or not yet valid")):
        return result

    card = read_card(pdf)
    meta = issuer_info(cert)
    doc_type = card and card.get("type")
    right = card is not None and doc_type in meta["docTypes"] and (expected_type is None or doc_type == expected_type)
    c.add("right issuer", right,
          f"{name} ({meta['role']}) may issue {DOC_TYPES.get(doc_type, '?')} documents" if right
          else f"{name} ({meta['role']}) cannot vouch for this kind of document")
    if right:
        card["issuerKey"] = meta["zk"]
    result.update(ok=c.ok, card=card if c.ok else None)
    return result


def _trim_der(data):
    """The signature is zero-padded inside the PDF; keep only the DER object."""
    if data[1] & 0x80:
        n = data[1] & 0x7F
        length = int.from_bytes(data[2:2 + n], "big")
        return data[:2 + n + length]
    return data[:2 + data[1]]


def verify_credential(card, issuer_cert_pem, root_cert, revoked_serials=(), now=None):
    """Same 4 checks for a credential that arrived as an RGB token (no PDF):
    the issuer's seal on the data card, issuer certified by the root, certificate valid, right issuer."""
    import zkcrypto as zk
    now = now or dt.datetime.now(dt.timezone.utc)
    c = Check()
    result = {"ok": False, "checks": c.items, "issuer": None, "card": None}
    cert = x509.load_pem_x509_certificate(issuer_cert_pem.encode())
    meta = issuer_info(cert)
    A = (int(meta["zk"][0]), int(meta["zk"][1]))
    fields = [card["type"], int(card["holder"]), card["v1"], card["v2"], card["issuedAt"]]
    sig = tuple(int(x) for x in card["sig"])
    if not c.add("not changed", zk.verify(A, zk.poseidon(fields), sig),
                 "the issuer's seal on this credential is valid" if zk.verify(A, zk.poseidon(fields), sig)
                 else "the credential was modified after the issuer sealed it"):
        return result
    try:
        cert.verify_directly_issued_by(root_cert)
        trusted = True
    except Exception:
        trusted = False
    name = cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value
    result["issuer"] = name
    if not c.add("trusted issuer", trusted, f"{name}, certified by {root_cert.subject.rfc4514_string()}" if trusted
                 else f"{name} is not certified by a trusted authority"):
        return result
    valid = cert.not_valid_before_utc <= now <= cert.not_valid_after_utc and cert.serial_number not in set(revoked_serials)
    if not c.add("still valid", valid, "certificate valid" if valid else "certificate expired or revoked"):
        return result
    right = card["type"] in meta["docTypes"]
    c.add("right issuer", right, f"{name} ({meta['role']}) may issue {DOC_TYPES.get(card['type'], '?')} credentials" if right
          else f"{name} ({meta['role']}) cannot vouch for this kind of credential")
    if right:
        card = dict(card)
        card["issuerKey"] = meta["zk"]
        result.update(ok=c.ok, card=card)
    return result

"""A real document whose true origin is Team Moneyfest, signed with the team's own RSA key.

    python3 keyproof/make_team_doc.py   ->  real_docs/Team_Moneyfest_membership.pdf (+ an edited copy)

The team key is created once in data/team_key.pem (git-ignored). The certificate is self-issued by the team,
so PDF readers show "signed by Team Moneyfest" with an unknown-issuer warning, which is the truth.
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from cryptography import x509  # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from cryptography.x509.oid import NameOID  # noqa: E402

from make_demo import layout  # noqa: E402
from pdfsig import make_signed_pdf  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
kp = os.path.join(ROOT, "data", "team_key.pem")
if os.path.exists(kp):
    key = serialization.load_pem_private_key(open(kp, "rb").read(), None)
else:
    os.makedirs(os.path.dirname(kp), exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    open(kp, "wb").write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    os.chmod(kp, 0o600)
name = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Team Moneyfest"),
                  x509.NameAttribute(NameOID.COMMON_NAME, "Team Moneyfest document signing")])
now = dt.datetime.now(dt.timezone.utc)
cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now - dt.timedelta(days=1))
        .not_valid_after(now + dt.timedelta(days=365)).sign(key, hashes.SHA256()))
when = now.astimezone(dt.timezone(dt.timedelta(hours=2)))
raw = layout("Team Moneyfest", "Agentic Dollars on Bitcoin hackathon - Turin", "Certificate of team membership",
             f"Ref. MF-2026-001   -   Issued {when.strftime('%d/%m/%Y')}",
             [("Team", "Moneyfest"), ("Event", "Agentic Dollars on Bitcoin (Turin, 17-18 Oct 2026)"),
              ("Project", "KeyProof"), ("Member", "Kuzey Can Kacar"), ("Member", "Irem Sengor"),
              ("Member", "Ege Arca Akcay"), ("Member", "Kerem Alp Yildiz")],
             ["Team Moneyfest certifies that the people above are the members of the team that built KeyProof."],
             "Team Moneyfest", when.strftime("%d/%m/%Y %H:%M CEST"), accent=(0.09, 0.16, 0.30),
             footer="Issued and digitally signed by Team Moneyfest itself (self-issued RSA certificate). Verify: Adobe Acrobat > Signature panel.",
             algo="RSA 2048, SHA-256")
pdf = make_signed_pdf([], {"type": 0, "note": "no KeyProof data card"}, "Team Moneyfest", key, cert, raw=raw)
out = os.path.join(ROOT, "real_docs")
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "Team_Moneyfest_membership.pdf"), "wb").write(pdf)
fake = pdf.replace(b"(Kerem Alp Yildiz)", b"(Mallory Hackers!)")
assert fake != pdf and len(fake) == len(pdf)
open(os.path.join(out, "Team_Moneyfest_membership_EDITED.pdf"), "wb").write(fake)
print("written real_docs/Team_Moneyfest_membership.pdf and the edited copy")

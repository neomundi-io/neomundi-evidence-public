<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="ATTESTATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Signed attestation — `cryptographically_attested`

The fourth assurance level is now **reachable**. This document states by what
mechanism, what it demonstrates, and what it will never demonstrate.

Validated design: [`DESIGN_SIGNATURE_ANCHORING_V1.md`](DESIGN_SIGNATURE_ANCHORING_V1.md).

---

## What an attestation establishes

> That an **identified party committed** to the precise digest of an evidence
> package, and that the package you hold is that one.

And what it does not establish, said in the same breath:

> Neither that the measured execution took place, nor **when** it took place,
> nor that the signing date is true, nor that the signed content is true.

**Signing proves commitment and custody, not a fact.** A perfectly signed
attestation over a fabricated archive is cryptographically valid. What the
signature adds is that we know **who** committed, and they can no longer deny
it.

---

## The mechanism

**Ed25519/EdDSA, detached compact JWS.** Same algorithm, same format and same
public-key shape (JWK `OKP`/`Ed25519`) as `govern-v3/app/rgc/signing.py` in
production — one verification path for both products, with two separate
custodies.

**The attestation is detached, and that is not cosmetic.** It covers the
digest of the archive **file**; slipping it inside the archive would change
that digest and invalidate the signature just computed. Circular.

```
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip          ← untouched, byte for byte
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws      ← the attestation
```

Three intended consequences: **V0.1 archives are not touched**, the **frozen
corpora** stay frozen, and a historical archive can be attested
**retrospectively** without being reopened.

---

## Use

```sh
# 1. a key, OUTSIDE the repository -- the tool refuses to write one inside
python sign.py genkey --kid nm-ev-2026-11-a \
    --out ~/keys/private.json --trust-store-out ~/keys/store.json \
    --valid-from 2026-11-05T00:00:00Z

# 2. attest, without touching the archive
python sign.py attest --archive <archive.zip> --key ~/keys/private.json \
    --attested-at 2026-11-05T14:00:00Z --kind retrospective \
    --out <archive.zip>.jws

# 3. verify, offline, with the public key alone
python verify_attestation.py <archive.zip>.jws \
    --archive <archive.zip> --trust-store ~/keys/store.json

# 4. and raise a binding to the fourth level
python bind.py verify manifest.json --archive <archive.zip> \
    --attestation <archive.zip>.jws --trust-store ~/keys/store.json
```

`--attested-at` is **required**: the tool never reads the clock, so two runs
on the same inputs produce the same token, byte for byte.

---

## The fourteen control lines

Five of them are the **pillars**: the level is reached only if all five marked
★ are `PASS`.

| Control | Possible states |
|---|---|
| attestation readable | `PASS` / `FAIL` |
| attestation shape | `PASS` / `FAIL` |
| ★ canonicalisation profile | `PASS` / `FAIL` |
| ★ header: imposed algorithm | `PASS` / `FAIL` |
| trust store readable | `PASS` / `FAIL` |
| ★ **cryptographic signature** | `PASS` / `FAIL` / `NOT TESTED` |
| ★ **trusted identity** | `PASS` / `FAIL` / `NOT TESTED` |
| signer's legal capacity | **always `NOT TESTED`** |
| separation of the five identities | `PASS` / `NOT TESTED` |
| ★ **agreement with the archive** | `PASS` / `FAIL` / `NOT TESTED` |
| nature of the attestation | `PASS` |
| independent timestamp | **always `NOT TESTED`** |
| third-party anchoring | **always `NOT TESTED`** |
| anchor-proof agreement | `PASS` / `FAIL` / `NOT TESTED` |
| truth of the content | **always `NOT TESTED`** |

The three in bold are the three things the brief requires never to be merged:

```
[PASS      ] signature cryptographique - EdDSA/Ed25519, cle nm-ev-2026-11-a
[PASS      ] identite de confiance - cle active, signataire nm-recherche
[PASS      ] concordance avec l archive - bundle_sha256 recalcule
```

**A valid signature by an untrusted key never reads as an attestation.** That
is case 12 of the test suite: signature `PASS`, trust `FAIL`, no level.

---

## The canonicalisation profile, precisely specified

`neomundi-jcs-strings/1`, in [`canonical.py`](../canonical.py):

1. UTF-8, no BOM;
2. `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`;
3. permitted types: string, `null`, object, array — **numbers and booleans
   forbidden**;
4. every key matches `^[a-z0-9_]+$`.

**Why it is equivalent to RFC 8785 over its domain.** JCS is hard on three
points; the profile neutralises two and inherits the third:

- **numbers.** JCS imposes ECMAScript formatting (`1.0` → `1`, `1e-07` →
  `1e-7`), which `station/ledger/canonical.py` handles in ~250 lines.
  **Forbidding them removes the question instead of managing it.** A count
  therefore travels as a string: `"30"`, not `30`.
- **key ordering.** JCS sorts on UTF-16 code units, Python on code points.
  **Restricting keys to ASCII makes the two orders coincide.**
- **string escaping.** `json.dumps` is already conformant.

Outside this domain the equivalence **does not hold** — which is why the
domain is restricted rather than the implementation extended.

**The profile never takes part in verifying a signature.** The verifier checks
the bytes carried *verbatim* by the JWS. It re-canonicalises only to **check
conformance to the profile**, which is a separate control — and case 22 proves
it: a non-canonical but correctly signed payload yields profile `FAIL` and
signature `PASS`.

---

## The five identities, kept apart

Conflating them is the commonest way to overclaim. The schema holds them
separate:

| Role | What it is | Capacity to commit |
|---|---|---|
| `signer` | the party that **commits** | declared, **never verified** |
| `technical_operator` | who ran the operation, on which machine | n/a |
| `measurement_author` | who produced the attested corpus's measurements | n/a |
| `key_custodian` | who holds and controls the private key | n/a |
| `trust_authority` | a third party vouching for key or time | `null` today |

**Succession, not revocation.** An identity is not revocable: revocation
applies to **keys**. An entity may be given a successor — a commercial
company after an association — and **adding that successor invalidates no
earlier attestation**. The verifier reports the succession without re-judging
anything.

**Legal capacity is always `NOT TESTED`.** No code establishes that an entity
may lawfully commit. The store carries the declared value (`unverified` at
this stage for NeoMundi Recherche), and the verifier reports it as is.

---

## The trust store

**Outside the Evidence repository.** The repository ships only a **test**
store, under `examples/attestation/`, whose keys grant nothing without
`--allow-test-keys`.

Public material only: a store containing a private-key field is **refused**
(case 17), as is a duplicate `kid` (case 18) or an unknown verification policy
(case 19) — refused, not interpreted.

### Rotation and compromise do not behave alike

| Situation | Verdict | Why |
|---|---|---|
| `rotated`, signature **before** | `PASS` | the key stopped being used; nothing happened to it |
| `rotated`, signature **after** | `FAIL` | it should not have been used |
| `compromised`, **whatever the date** | `FAIL` | whoever holds the private key can forge any `attested_at_declared`; letting earlier signatures survive would mean trusting a timestamp the attacker controls |
| key **unknown** to the store | `NOT TESTED` | the signature may be valid, we cannot know. Calling it invalid would be a groundless accusation |
| key **expired** | `FAIL` | outside its declared window |

---

## Retrospective attestation

An already-frozen corpus can be attested **without being touched**. But the
attestation then says exactly what it does:

```
[PASS      ] nature de l attestation - RETROSPECTIVE : elle constate une
             verification faite le 2026-11-05T14:00:00Z (declare), sur un
             corpus gele le 2026-11-05T10:26:04Z (conserve depuis son propre
             manifeste). Elle ne pretend PAS que le corpus ait ete signe a la
             date de son execution.
```

The **freeze date is preserved** from the subject's own manifest, never
invented; a retrospective attestation that omitted it is refused, at the
signer and at the verifier (case 21).

---

## Verifying with none of our tools

This is the independence argument, and it is **demonstrated**. The public JWK
rebuilds the PEM identically, so `openssl` verifies our signature on its own:

```sh
# 1. split the JWS, write the signed bytes
JWS=$(cat archive.zip.jws)
printf '%s' "${JWS%.*}" > signed.bin

# 2. extract the signature (3rd segment, base64url → binary)
python - <<'PY'
import base64, pathlib
s = pathlib.Path("archive.zip.jws").read_text().strip().split(".")[2]
pathlib.Path("sig.bin").write_bytes(
    base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))
PY

# 3. build the PEM from the 32 bytes of `x` in the store
#    (DER SubjectPublicKeyInfo prefix for Ed25519)
python - <<'PY'
import base64, json, pathlib
x = json.loads(pathlib.Path("store.json").read_text())["keys"][0]["x"]
der = bytes.fromhex("302a300506032b6570032100") + \
      base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
pathlib.Path("pub.pem").write_bytes(
    b"-----BEGIN PUBLIC KEY-----\n" + base64.encodebytes(der) +
    b"-----END PUBLIC KEY-----\n")
PY

# 4. verify — with openssl, not with us
openssl pkeyutl -verify -pubin -inkey pub.pem -rawin -in signed.bin -sigfile sig.bin
```

Observed result on the real attestation:

```
intact attestation     Signature Verified Successfully
altered attestation    Signature Verification Failure
```

---

## The dependency, stated plainly

**Ed25519 is not verifiable with Python's standard library.** Three paths, and
all three exist:

1. **`cryptography` present** → full verification. A maintained, audited
   component, already in the project's stack.
2. **`cryptography` absent** → `NOT TESTED`, with the reason and the install
   line. **Never `PASS`, never `FAIL`** (case 15). And `verify.py`'s 21
   integrity controls remain entirely dependency-free.
3. **`openssl` path** → above.

**No pure-Python Ed25519 implementation was vendored.** Writing our own
cryptography to preserve a "zero dependency" slogan would trade a real
guarantee for a cosmetic one.

---

## Test matrix

`python tests/test_attestation.py <archive> [corpus]` → **23/23 conforming.**
All keys are ephemeral, generated at run time and erased at the end.

| # | Case | Observed result |
|---|---|---|
| 1 | valid archive, valid signature, known key | **`cryptographically_attested`** |
| 2 | archive modified after signing | signature `PASS`, **agreement `FAIL`** — the signature is not at fault |
| 3 | forged signature | signature `FAIL` |
| 4 | unknown public key | `NOT TESTED` and **not** `FAIL`; no level |
| 5 | valid signature, anchor absent | level reached, anchoring `NOT TESTED` |
| 6 | anchor present but not matching | **`FAIL`** on anchor-proof agreement; the anchor's *validity* stays `NOT TESTED` |
| 7 | **archive recomputed after deleting one observation** | `verify.py` alone: **0 internal FAIL**. The attestation: **agreement `FAIL`** |
| 8 | malformed signature metadata (5 shapes) | **5/5** return a motivated `FAIL`, no traceback |
| 9 | **unsigned** historical archive | binding accepted at `reference_verifiable`, attestation `NOT TESTED` |
| 10 | `verify.py` non-regression on GROUNDED-S1 | `19 PASS, 0 FAIL, 2 NOT TESTED` — unchanged |
| 11 | forged `alg` (`none`, `HS256`, `RS256`) | **3/3 refused** — the algorithm is imposed, never read to choose |
| 12 | `test` key without `--allow-test-keys` | signature `PASS`, **trust `FAIL`** |
| 13 | **compromised** key, earlier signature | **retroactive `FAIL`** |
| 14 | **rotated** key, earlier signature | `PASS` — the difference from compromise |
| 14b | rotated key, **later** signature | `FAIL` |
| 15 | `cryptography` absent | signature `NOT TESTED`, no level |
| 16 | the verifier reaches no private key | does not import `sign`; no private primitive |
| 17 | store containing a private-key field | store **refused** |
| 18 | duplicate `kid` in the store | **refused** |
| 19 | unknown verification policy | **refused**, not interpreted |
| 20 | header `kid` ≠ payload `kid` | **refused** |
| 21 | retrospective attestation with no freeze date | **refused** |
| 22 | **non-canonical** but correctly signed payload | profile `FAIL`, signature `PASS` — the two controls are genuinely distinct |

### Case 7 closes a declared limit

Since 5 November the falsification suite has carried an accepted limit: "one
observation erased everywhere, counts and checksums redone" is **undetectable
inside** the archive. The test confirms it: `verify.py` returns **0 FAIL** on
the amputated archive, which is internally perfect.

The attestation detects it — because the original digest was signed elsewhere.
**It is the first time a declared product limit closes.**

---

## Residual limits

| | Severity |
|---|---|
| **`attested_at_declared` is declared.** No trusted clock. Expiry checking therefore rests on the signer's word | **high** — the decisive argument for third-party anchoring |
| **No third-party anchoring is implemented.** OpenTimestamps is planned; the field exists and raises no level | **high** |
| **A signature is not the truth of the content** | **high**, and permanent |
| **The signer's legal capacity is not verifiable** by code, and stays `unverified` | high — a legal question |
| Key compromise is **retroactive**: it invalidates everything | medium, handled |
| The trust store is not yet **published on a second channel** | medium |
| **Unsigned** V0.1 archives gain nothing automatically: they must be attested | low, accepted |

---

## Files

| | |
|---|---|
| [`canonical.py`](../canonical.py) | the `neomundi-jcs-strings/1` profile, shared signer/verifier |
| [`sign.py`](../sign.py) | the signer — private key, refuses to write inside the repository |
| [`verify_attestation.py`](../verify_attestation.py) | the verifier — public material only, never imports the signer |
| `schemas/evidence-attestation-v1.json` | the signed object |
| `schemas/evidence-trust-store-v1.json` | the store, its states and its policy |
| `examples/attestation/` | a real attestation and a **test** store — private key destroyed |
| `tests/test_attestation.py` | 23 security cases, ephemeral keys |

<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="LISEZ-MOI.fr.md">Français</a> · <a href="../../README.md">← README</a></sub>

# V1 evidence package — auditor's guide

**Everything in this directory is synthetic.** The archive was built for the
review, the signing key was an **ephemeral demonstration key** and has been
**destroyed**, and the external receipt is invented. **No pilot data, no real
dataset.**

One thing only is not synthetic: the **timestamp proof**, genuinely obtained
from the four public OpenTimestamps calendars. Its state is `PENDING`, and
**that attests no date**.

---

## What the package contains

| File | Bytes | What it is |
|---|---|---|
| `NEOMUNDI_EVIDENCE_V1_DEMO.zip` | 20,237 | the evidence package, 4 observations, 8 members |
| `corpus/` | 5 files | the replayed inputs, so their digests recompute |
| `…zip.jws` | 2,211 | the **Ed25519** attestation, detached |
| `…zip.jws.ots` | 856 | the **OpenTimestamps** proof, real, `PENDING` |
| `…zip.jws.timestamp.json` | 1,173 | the timestamp descriptor |
| `trust-store.json` | 2,793 | **public keys only**, status `test` |
| `binding/` | 3 files | an observation ↔ artifacts binding |
| `receipt-synthetic.html` | 2,837 | an **invented** external receipt |
| `map-comparable.json` · `map-no-context.json` | | two correspondence tables |
| `reconciliation.md` | 3,021 | the reconciliation report produced |

### Digests, to be kept elsewhere than with the package

```
archive      e31e12bb7e32c7a33db1ecacc8c38cd18225fa10618c7e1aa5d6f9540f2ad7d6
attestation  d533518f4413d75e7ea58923d21bfe6c168eba2f1cc6703dc12353abceda3493
```

**A digest kept with the package attests nothing.** It is the only defence
against a wholly rebuilt package, and it has value only if you keep it
separately — or if you verify the attestation, which covers it.

---

## The five commands

None needs the network. None writes into the package.

### 1 — Integrity

```sh
python ../../verify.py NEOMUNDI_EVIDENCE_V1_DEMO.zip --corpus corpus
```

**Expected: `BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED`**, over 21 lines.

No dependency: `verify.py` imports only the standard library. To satisfy
yourself, block everything and run it again — the summary is identical.

The 2 `NOT TESTED` are the ledger chaining and the archive's origin: two
things no local verification can do, and which carry their reason explicitly.

### 2 — Ed25519 attestation

```sh
python ../../verify_attestation.py NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --trust-store trust-store.json --allow-test-keys
```

**Expected: `10 PASS, 0 FAIL, 5 NOT TESTED`, level
`cryptographically_attested`.**

Without `--allow-test-keys`, the demonstration key is **refused** — by
design: it must grant no attestation by default.

Three lines stay `NOT TESTED` forever: the signer's **legal capacity**, the
**independent timestamp**, and the **truth of the content**.

A fourth is `NOT TESTED` **because you have not lifted it yet**: the trust
store's digest has not been compared against anything. You downloaded the
store and the package from the same place, so whoever controls that place
controls both. Compare it against a digest you obtained **by another
channel**:

```sh
python ../../verify_attestation.py NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --trust-store trust-store.json --allow-test-keys \
    --store-digest <the sha256 you obtained elsewhere>
```

That line then becomes `PASS` — or `FAIL`, which would be the interesting
case. **No second channel is published yet** (condition C-5), so today the
only digest you can obtain is the one you compute from the same file. Which
proves nothing, and is exactly why the line defaults to `NOT TESTED` rather
than `PASS`.

### 3 — Timestamping, and its real status

```sh
python ../../timestamp.py verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots \
    --subject NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --descriptor NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.timestamp.json
```

**Expected: `4 PASS, 0 FAIL, 3 NOT TESTED`.** The *binding* is established;
the `attestation confirmee par la chaine` line is `NOT TESTED` because all
four attestations are `PENDING`.

Under `--strict`, **code 2**: an automated consumer must know the date is not
established.

To verify the **time** — which we do not — the official client:

```sh
ots verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots
```

### 4 — Observation ↔ artifacts binding

```sh
cd binding
python ../../../bind.py verify manifest.json \
    --archive ../NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --attestation ../NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --trust-store ../trust-store.json --allow-test-keys
```

**Expected: `10 PASS, 0 FAIL, 3 NOT TESTED`, level
`cryptographically_attested`.** Both artifacts are raised from
`reference_verifiable` to `cryptographically_attested` by the attestation of
the archive that declares their digests.

### 5 — Reconciliation

```sh
python ../../adapters/reconcile.py receipt-imported.json \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip --map map-comparable.json
```

**Expected: `4 MATCHED, 2 MISMATCHED, 1 MISSING, 1 NOT COMPARABLE,
1 NOT VERIFIABLE`**, and **3 contradictions preserved**.

Then the same receipt with `--map map-no-context.json`: when the receipt
declares neither measurement version, nor coverage, nor definition, **nothing
measured compares any more** — but a **digest still matches**.

---

## Four things to try, to catch us out

This is the best use of your time.

**Change one byte inside a member.** Reopen the ZIP, alter
`observations.jsonl`, close it without redoing `checksums.sha256`.
→ `verify.py` must return **3 FAIL**.

**Append one byte to the end of the file.** → `verify.py` passes (**0 FAIL**),
and that is **correct**: it verifies *internal* integrity. The
**attestation** refuses — the *file's* identity is what it covers. Two tools,
two distinct guarantees.

**Remove one observation and recompute everything** — manifest counts and
checksums. The archive becomes internally **perfect**, and `verify.py` alone
sees nothing. The attestation refuses it. This is the limit we declared
undetectable until 6 November.

**Forge the attestation.** Change a byte of the `.jws`, or its `alg` field to
`none`. → refused, with the cause.

---

## Reproduce the whole package

```sh
python ../../tests/make_fixture.py <directory>
```

The archive is **deterministic byte for byte**: two runs yield the same
digest. The attestation cannot be reproduced — its private key was destroyed.
It stays **verifiable**, and no new attestation can be issued with that key.

---

## What this package does not establish

- **That the measured execution took place.** There was none: everything is
  synthetic.
- **No date.** The timestamp proof is `PENDING`.
- **No eIDAS qualification.** OpenTimestamps is not a qualified trust service
  provider.
- **The truth of any content.** A perfect attestation over a fabricated
  archive is cryptographically valid — and that is precisely the case here.
- **That these functions work on a real pilot package.** None has been
  exercised on one yet.

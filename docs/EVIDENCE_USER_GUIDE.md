# NeoMundi Evidence — user guide

**7 November 2026.** Every command below was **executed** before being written
here. Exit codes were measured, not assumed.

Five levels are used throughout, and they are not interchangeable:

| Level | Meaning |
|---|---|
| **IMPLEMENTED** | the code exists and runs |
| **TESTED** | covered by an automated suite |
| **DEMONSTRATED** | executed and **observed** at least once |
| **QUALIFIED** | exercised end to end on a **real** case, verdict recorded |
| **NOT CONFIRMED** | claimed, never observed |

> A feature exercised only on fixtures is **never** described as validated in
> real conditions.

---

## 1. What this is

A set of command-line tools that take a **campaign archive** produced by
Station and establish what its bytes allow you to assert — and what they do
not.

| | Role | What it does not do |
|---|---|---|
| **Measurement** | the instrument that measures | it does not know which code produced it |
| **Station** | the observation and campaign frame | it calibrates nothing |
| **Evidence** | integrity and verification | it measures nothing, and judges no content |

🔴 Evidence is **not** a certification, **not** a scientific validation,
**not** a legal guarantee, and **not** a production traffic monitor.

---

## 2. Prerequisites

### To verify an archive you received — the common case

**Python 3, and nothing else.** `verify.py` imports only the standard
library.

**DEMONSTRATED**: with `cryptography` **and** `opentimestamps` both blocked,
`verify.py` returns the **same** summary — the CI enforces this in a dedicated
job.

### To verify an attestation

`cryptography` is required, plus the trust store (public material) and,
ideally, its digest obtained through a **second channel**.

### To sign

The private key. **No verification requires a private key** — that is a design
property, not a convenience.

---

## 3. Exit codes — measured, not assumed

| Code | Meaning |
|---|---|
| `0` | no `FAIL` |
| `1` | at least one `FAIL` |
| `2` | `--strict`, and a **required** guarantee is not demonstrated |

### 🔴 A `0` under `--strict` does not mean "better verified"

Measured on 7 November, on the CI fixture:

| Invocation | Code |
|---|---|
| `verify.py <archive> --corpus <corpus>` | `0` — 20 PASS, 0 FAIL, 2 NOT TESTED |
| `verify.py <archive>` | `0` — 18 PASS, 0 FAIL, 3 NOT TESTED |
| `verify.py <archive> --corpus <corpus> --strict` | `0` |
| `verify.py <archive> --strict` *(no corpus)* | **`2`** |

The fixture declares replay records; without a corpus their inputs cannot be
confronted, so a **required** guarantee is missing. The exact reading is:
*nothing required is missing **among what is declared**.* An archive that
declares less is held to less.

---

## 4. The twelve operations

### 4.1 Produce a measurement — **QUALIFIED**

Station's job, documented there. The preflight emits **no** call; `--execute`
is what authorises them.

```sh
station run-slot <pack> <campaign> --slot 12:00:00 --var-dir <dir> \
  --ledger <dir>/ledger.jsonl --index <dir>/index.sqlite \
  --max-units 1 --max-attempts 1            # preflight only
#   ... same command plus --execute          # emits the calls
```

**Limit** — one observation says nothing about a distribution, and
`model_served` is the **provider's claim**.

### 4.2 Verify the ledger chain — **QUALIFIED**

```sh
station ledger verify --path <ledger.jsonl>
```

**Output**: record count, **head digest**, and `chaîne vérifiée`.

**Limit** — chaining catches an **inconsistent** alteration. A complete
rewrite of the ledger would produce a valid chain.

### 4.3 Export — **QUALIFIED**

```sh
station campaign export <campaign> --sortie <out.zip> --registre <ledger.jsonl>
```

**Limit** — an export is a **projection**. The ledger keeps `response_text`;
the export carries only its **digest**. See §6.

### 4.4 Verify integrity — **QUALIFIED**

```sh
python verify.py <archive.zip> [--corpus <dir>] [--json <report.json>] [--strict]
```

**Observed on Q-2** (real): **17 PASS, 0 FAIL, 4 NOT TESTED**, code `0`.

🔴 **`--corpus` on an archive with no replay records changes nothing.** Q-2
carries none: the line stays `NOT TESTED` — *« aucun enregistrement de
provenance »* — whatever path you pass. **The tool is not at fault**: on the
demo archive, which declares 4 replay records, a missing corpus yields
**`FAIL` — "absents 4"**. A missing corpus never passes silently; there simply
has to be something to confront.

**Limit** — `verify.py` checks **internal** integrity. File **identity** is
what the attestation covers. See §5·C.

### 4.5 Verify provenance — **QUALIFIED**

```sh
python adapters/provenance.py <archive.zip> [--out <json>] [--md <md>] [--strict]
```

**Output**: the walk `Execution → Measurement → Evaluator → Configuration →
Export → Evidence`, each line carrying its nature — `CONTROLE`, `DECLARE`,
`NON DEMONTRABLE` — then a **provenance level**.

**Observed on Q-2**: **11 PASS, 0 FAIL, 7 NOT TESTED**, level
`instrument_declare_et_configure`.

**Three levels exist, and there is no fourth.** `instrument_verifie` cannot
exist: establishing it would require **observing the measurement**, which an
archive does not do.

### 4.6 Attest — **QUALIFIED**

```sh
python sign.py attest --archive <zip> --key <key.json> --out <out.jws> \
  --attested-at <UTC> --kind contemporaneous --signer <id> \
  --measurement-author <id> --custodian <id> --register <register.txt>
```

The tool **does not read the clock**: `--attested-at` is explicit, so two runs
produce the same token. `--register` is not optional in practice — **without
it a key compromise cannot be scoped**.

### 4.7 Verify a signature — **QUALIFIED**

```sh
python verify_attestation.py <attestation.jws> --archive <zip> \
  --trust-store <store.json> --store-digest <sha256> --strict
```

**Observed on Q-2**: **11 PASS, 0 FAIL, 4 NOT TESTED**, level
`cryptographically_attested`, `--strict` code `0`.

**Measured refusals:**

| Situation | Code |
|---|---|
| `test` key **without** `--allow-test-keys` | **`1`** — *"elle n'accorde aucune attestation"* |
| store not confronted, under `--strict` | **`2`** |
| archive does not match the attestation | **`1`** |

Without `--store-digest`, the store line stays `NOT TESTED`: *a store that has
not been confronted is not false — it is not confronted.*

### 4.8 Independent timestamping — **IMPLEMENTED, TESTED**

```sh
python timestamp.py stamp   <subject> --stamped-at <UTC>      # NETWORK
python timestamp.py inspect <proof.ots>                       # offline
python timestamp.py verify  <proof.ots> --subject <subject> [--strict]
python timestamp.py upgrade <proof.ots>                       # NETWORK
```

**Measured on the shipped proof** (`…zip.jws.ots`, 786 bytes):

| Invocation | Code | Result |
|---|---|---|
| `inspect` | `0` | magic, version 1, SHA-256 |
| `verify --subject <the signed file>` | `0` | **3 PASS, 0 FAIL, 4 NOT TESTED** — the binding holds |
| `verify --strict` | **`2`** | the proof is `PENDING` |
| `verify --subject <wrong file>` | **`1`** | *"la preuve s'engage sur d533518f…, le sujet se hache sur …"* |

🔴 **A `PENDING` proof attests NO date.** It says a calendar committed to
include the digest in a future transaction. The shipped proof carries **4
PENDING attestations and 0 Bitcoin**.

🔴 **No eIDAS qualification.** OpenTimestamps is not a qualified trust service
provider, and nothing here may be presented as a qualified timestamp.

**This tool verifies the binding, not the time.** Validating a Bitcoin
attestation needs a block header — a trust source we do not have. It
**delegates**: `ots verify <proof.ots>`.

**NOT CONFIRMED** — no attestation produced by this project carries an anchor:
Q-2's attestation has `external_anchor: null`.

### 4.9 Reconcile an external receipt — **TESTED, DEMONSTRATED on fixtures**

```sh
python adapters/reconcile.py <receipt.json> --archive <zip> --map <map.json> \
  [--observation <id>] [--supplied <material>] [--tolerance 1e-09] [--strict]
```

🔴 **Five verdicts, not two:**

| Verdict | Meaning |
|---|---|
| `MATCHED` | the two values agree, within tolerance |
| `MISMATCHED` | they differ — **both are kept**, nothing is decided |
| `MISSING` | the receipt does not carry that field |
| `NOT COMPARABLE` | both values exist but are not of the same nature |
| `NOT VERIFIABLE` | the receipt's value cannot be confronted with what we hold |

**Observed** on the shipped fixture: `4 MATCHED, 2 MISMATCHED, 1 MISSING,
1 NOT COMPARABLE, 1 NOT VERIFIABLE`. On a mismatch: *"both values are kept as
they are — nothing is decided here."*

**NOT CONFIRMED** — no receipt actually produced by a third party has been
reconciled.

### 4.10 Ingest a third-party package — **TESTED**

```sh
python adapters/ingest.py <package> [--trust-store <store>] [--out <json>] [--strict]
```

**Three verdicts**: `ACCEPTE` (0) · `INCOMPLET` (0, or **2** under
`--strict`) · `REJETE` (1). **`INCOMPLET` is not a refusal.**

Nothing from the package is executed, and no private key is needed.

**NOT CONFIRMED** — 16 fixture cases pass; **no package actually produced by a
third party has ever been ingested.**

### 4.11 Bind external artefacts — **TESTED, DEMONSTRATED**

```sh
python bind.py build  --archive <zip> --observation <id> \
                      --artifact role=path --created-at <UTC> --out manifest.json
python bind.py verify manifest.json --root <dir> [--archive <zip>] \
                      [--attestation <jws>] [--trust-store <store>] [--strict]
```

**Observed**: `4 PASS, 0 FAIL, 5 NOT TESTED`, and a **derived** assurance
level: `reference_verifiable` — *"the artefacts offered are indeed those the
record refers to."* **Nothing more.**

**Measured refusal**: an unknown observation id yields code **`1`** —
*"aucune observation 'obs-inexistante' dans l'archive (4 observations
presentes)"*.

🔴 Two caveats the tool states itself: *a textual description of an execution
is not proof that the execution happened*, and *binding an artefact to a
record does not say when, or at whose premises*.

### 4.12 Audit the trust store — **TESTED**

```sh
python publish_store.py audit   <store.json>     # can it be published as is?
python publish_store.py payload <store.json>     # the second-channel payload
```

It **publishes nothing**. `sign.py genkey` **refuses** to write a private key
under the repository root — measured, code **`1`**.

---

## 5. Four layers that catch different things

Measured on 7 November against the shipped demo dossier
(`e31e12bb…`), each alteration rebuilt preserving the original `ZipInfo` so the
**only** difference is the targeted one.

| Scenario | `verify.py` alone | With the attestation |
|---|---|---|
| **A** intact archive | `0` — 19 PASS, 0 FAIL | `0` — 10 PASS, 0 FAIL |
| **B** one byte **inside** a member | **`1`** — digest diverges | `1` |
| **C** one byte appended **at the end** of the ZIP | **`0` — 17 PASS, 0 FAIL** | **`1`** |
| **D** an observation removed, **all checks recomputed** | **`0` — 17 PASS, 0 FAIL** | **`1`** |

🔴 **C and D are the point.** `verify.py` verifies the archive's **internal
integrity**; the attestation verifies the **file's identity**. Confusing them
would be promising one while delivering the other.

### 🔴 Never quote a detection rate without naming its battery

Three figures coexist, and all three are exact:

| Battery | Result |
|---|---|
| `tests/test_falsification.py` | **10/10** alterations detected, **+1 declared limit** |
| `tests/test_adversarial.py` | **13 detected, 2 declared misses**, out of 15 |
| Q-1 adversarial case G | provenance rewritten **then repaired** → **not detected**, even with the attestation |

**Detection depends entirely on how thorough the forger is.** "10 out of 10"
describes that battery of ten named alterations — it is **not** a general
detection rate.

---

## 6. What is kept, exported, published, verifiable

Four distinct things. Confusing any two of them produces a false statement.

| | Response text | Digests |
|---|---|---|
| **Station ledger** | **kept** (`response_text`) | yes |
| **Export** (transmissible) | **absent** | yes |
| **Published** | nothing of Q-2 — private and frozen | — |
| **Available to a verifier** | only what the export carries | yes |

🔴 Both symmetric errors are wrong: *"NeoMundi does not keep responses"* —
false, the ledger does — and *"the export carries the exchanges"* — also
false. **What leaves is a deliberate choice**, and it is an argument: the
dossier attests what was said without the export disclosing it.

---

## 7. Independent verification

What a third party can do **without us**, with no account and no private key.

```sh
# 1. the hash of the file you received, BEFORE opening it
sha256sum campaign.zip

# 2. compare it with the one transmitted THROUGH ANOTHER CHANNEL
#    (a mismatch = do not open, and tell us)

# 3. fetch the trust store
curl -O https://raw.githubusercontent.com/neomundi-io/neomundi-evidence-public/main/trust/trust-store.json

# 4. fetch its digest from an independent channel
curl -s https://mcp.neomundi.org/trust/trust-store-digest.json

# 5. compare
sha256sum trust-store.json

# 6. verify the archive, then the attestation
python verify.py campaign.zip
python verify_attestation.py campaign.jws --archive campaign.zip \
  --trust-store trust-store.json --store-digest <the digest from step 4> --strict
```

⚠️ The `/trust/` path segment is **required** — without it, `401`.

**Established**: a forger would have to compromise **two** distinct
infrastructures — a Git host and a VPS.

🔴 **Not established**: both channels are under the **same governance**.
NeoMundi controls the repository **and** the VPS. **This is not a third-party
trust anchor.** What you get is resistance to the compromise of a **single**
channel.

---

## 8. Reading results

| State | Meaning | What it is **not** |
|---|---|---|
| `PASS` | the check ran and agrees | proof of truth |
| `FAIL` | the check ran and disagrees | necessarily fraud |
| `NOT TESTED` | **the check could not be run** | half a `PASS`, nor a failure |

🔴 **No binary verdict is ever returned.** There is no "✓ archive authentic":
an archive can be **internally perfect and false**.

Three orders of conclusion, never to be merged:

| | Example | Scope |
|---|---|---|
| **Technical success** | 17 PASS, 0 FAIL | the bytes agree |
| **Experimental result** | `coherence 0.675` on one observation | a dated fact, not generalisable |
| **Scientific conclusion** | *none* | no calibration, no threshold, no validation |

---

## 9. Where to go next

| Need | Document |
|---|---|
| Reproduce the scenarios | [EVIDENCE_TECHNICAL_DEMO.md](EVIDENCE_TECHNICAL_DEMO.md) |
| Follow an artefact through the chain | [EVIDENCE_TRACEABILITY.md](EVIDENCE_TRACEABILITY.md) |
| What is **not** established | [EVIDENCE_LIMITATIONS.md](EVIDENCE_LIMITATIONS.md) |
| Tests run, with results | [EVIDENCE_VALIDATION_REPORT.md](EVIDENCE_VALIDATION_REPORT.md) |
| Release decision | [EVIDENCE_RELEASE_READINESS.md](EVIDENCE_RELEASE_READINESS.md) |
| Attestation in depth | [ATTESTATION.md](ATTESTATION.md) · [SIGNING_POLICY.md](SIGNING_POLICY.md) |
| Timestamping in depth | [TIMESTAMPING.md](TIMESTAMPING.md) |
| Third-party submission | [SUBMISSION.md](SUBMISSION.md) |
| Verifying from an outside digest | [EXTERNAL_REFERENCE.md](EXTERNAL_REFERENCE.md) |

**French counterpart**: this guide has no `.fr.md` pair yet. The repository is
bilingual by convention (30 `.fr.md` files), and the pairing is a **declared
follow-up**, recorded in the validation report.

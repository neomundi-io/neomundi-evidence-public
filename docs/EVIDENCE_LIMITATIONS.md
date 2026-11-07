# NeoMundi Evidence — limitations

**7 November 2026.** Functional, methodological and experimental limits.
Nothing here is softened, and nothing is a to-do list in disguise: most of
these are **bounds**, not omissions.

---

## 1. The three that will not move

### 1.1 A coherent rewrite of declared provenance is undetectable

A forger who rewrites a configuration fingerprint and a model name, **then
repairs** digests, checksums and the manifest, passes **every local check** —
including the attestation.

**Why this is not a defect**: no recomputation can distinguish a true
declaration from a coherent false one. Establishing it would require having
observed the measurement.

**Recorded as a ceiling, never as a `PASS`.** The absence of an alarm is not
an attestation.

### 1.2 That the declared evaluator actually ran is never verifiable

Permanently `NOT TESTED` from an archive. There are **three** provenance
levels and **no fourth**; a test fails if `instrument_verifie` ever appears.

### 1.3 A signature establishes commitment and custody, not fact

The verifier prints it on every run: *an attestation perfectly signed over a
fabricated archive is cryptographically valid.*

---

## 2. Temporal anchoring — implemented, and it attests no date

`timestamp.py` implements OpenTimestamps, is covered by 25 tests, and a real
786-byte `.ots` proof ships with the demonstration. **Measured**: the binding
to the subject's digest verifies (3 PASS, 0 FAIL), a wrong subject is refused
(code 1), and `--strict` returns **code 2**.

🔴 **The shipped proof carries 4 `PENDING` attestations and 0 Bitcoin.** A
pending says a calendar committed to include the digest in a future
transaction — **it attests no date**.

🔴 **No eIDAS qualification.** OpenTimestamps is not a qualified trust service
provider.

**The tool verifies the binding, not the time**, and delegates:
`ots verify <proof>`. Validating a Bitcoin attestation needs a block header —
a trust source we do not have.

**And no attestation produced by this project carries an anchor**: Q-2's
attestation has `external_anchor: null`.

---

## 3. Two capabilities not confirmed in real conditions

| Capability | Status | What is missing |
|---|---|---|
| **Third-party ingestion** (`adapters/ingest.py`) | TESTED — 16 fixture cases | **no package actually produced by a third party has ever been ingested** |
| **Reconciliation** (`adapters/reconcile.py`) | TESTED — 27/27 — and DEMONSTRATED on fixtures | **no receipt actually produced by a third party has been reconciled** |

Neither may be described as validated in operational conditions.

---

## 4. Detection: never a rate

| Battery | Scope | Result |
|---|---|---|
| `tests/test_falsification.py` | ten named alterations | **10/10**, +1 declared limit |
| `tests/test_adversarial.py` | fifteen cases | **13 detected, 2 declared misses** |
| byte appended at end of ZIP | — | `verify.py` **no**, attestation **yes** |
| amputation + full recomputation | — | `verify.py` **no**, attestation **yes** |
| Q-1 case G | provenance rewritten then repaired | **no**, not even the attestation |

🔴 **All five are exact, and they do not describe the same thing.** "10 out of
10" belongs to **that battery of ten**. It is **not** a general detection rate,
and must never be published as one.

⚠️ **An unresolved divergence.** `test_falsification.py` reports a comparable
amputation as **detected** ("mieux qu'annoncé"), while the demonstration's
scenario D shows it **undetected** by `verify.py` alone. The two forgers are
not equally thorough and the documentation does not yet say how they differ.

---

## 5. What `verify.py` does not see, by design

It verifies the archive's **internal** integrity. It does **not** verify the
file's **identity** — that is what the attestation covers.

**Measured**: a byte appended at the end of the ZIP leaves **17 PASS,
0 FAIL**, and the attestation refuses the file.

**Three `NOT TESTED` lines are structural**, and each says why:

1. **export completeness** — the archive declares neither the number of
   records exported nor the types excluded. *A valid chain says nothing about
   what was not exported.* It is the **producer's** job to declare that
   contract;
2. **JCS chaining of the source ledger** — out of scope: recomputing it here
   would be a second implementation of the ledger. To be confronted with
   `station ledger verify`;
3. **origin and time of the archive** — out of reach of any local check.

---

## 6. The trust store: two channels, one governance

**Established**: a forger would have to compromise **two** distinct
infrastructures — a Git host and a VPS.

🔴 **Not established**: both are under the **same governance**. NeoMundi
controls the repository **and** the VPS. **This is not a third-party trust
anchor.** What you get is resistance to the compromise of a **single**
channel.

Without `--store-digest`, the store line stays `NOT TESTED`: *a store that has
not been confronted is not false — it is not confronted.*

---

## 7. Identity and legal capacity

The declared capacity is **`experimental`**: the entity is **named**, it has
**decided** to attest in a scientific, non-commercial setting, and **no
verification of its powers has been made**.

🔴 `experimental` is **not a weaker `verified` — it is the opposite.** No code
can establish that an entity may legally commit itself. This is never a legal
certification.

---

## 8. Experimental limits carried over from Q-2

The global verdict of Q-2 is **`PARTIAL`**, and no successful demonstration
changes that.

1. the **code provenance status** is established at preflight and does **not**
   enter the ledger envelope — a third party reads `code_commit` without
   knowing the concordance was checked;
2. **source artefacts are not in the export** — only their digests. You can
   **confront** what you already hold; you cannot recompute what you do not
   have;
3. the **API ledger's idempotence is not qualified**; Q-1 and Q-2 produced
   different measurements, which is an **indication** against a cache, not a
   qualification;
4. **timestamps are declared** — three neighbouring instants, three different
   meanings;
5. **`provider_attested` is the provider's claim**, unverified;
6. **one observation, one provider** — Q-2 qualifies a **chain**, not a model,
   and claims no statistical reproducibility;
7. the **API response contract is not closed**: 32 top-level keys were found
   where the audit declared 25, and `contract_version` is not checked.

---

## 9. Documentation gaps, declared

| Gap | Status |
|---|---|
| `.fr.md` counterparts of the six new documents | **missing** — the repository is bilingual by convention (30 `.fr.md`) |
| `interpretation_contract 1.0` | cited by name; its file was not located on the inspected branches |
| supplier terms, and rights over a response digest | **not analysed** |
| contrast ratios of the visual states | values recorded, **ratios not measured** |

---

## 10. What this document is for

A product that enumerates its blind spots is the only kind an auditor can
rely on. **These limits are the argument, not its qualification.**

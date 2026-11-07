# NeoMundi Evidence — validation report

**7 November 2026.** Tests run, results, exit codes and reservations.

| | |
|---|---|
| Branch | `docs/consolidation-v1-20261107` |
| Starting commit | `28503cee4c93a91c3fc6df0e774fe31ab9523657` |
| Base | `main`, local and remote aligned |
| Nature of the work | **documentation only** — no product code was modified |

---

## 1. Test suites — the CI sequence, replayed locally

Fixture: `python tests/make_fixture.py <dir> --profile v2` →
`NEOMUNDI_EVIDENCE_CI_FIXTURE.zip`, plus `corpus/`, `binding/`,
`fixture.json`.

| Suite | Code | Summary |
|---|---|---|
| `test_timestamp` | **0** | 25/25 conforming |
| `test_reconciliation` | **0** | 27/27 |
| `test_bom` | **0** | 11/11 |
| `test_completude` | **0** | 15/15 |
| `test_capacite` | **0** | 10/10 |
| `test_cles` | **0** | 13/13 |
| `test_publication` | **0** | 15/15 |
| `test_ingestion` | **0** | 16/16 |
| `test_provenance` | **0** | 19/19 |
| `test_no_crlf` | **0** | 0 problems |
| `test_falsification` | **0** | **10/10 alterations detected, 1 declared limit** |
| `test_adversarial` | **0** | **13 detected, 2 declared misses, out of 15** |
| `test_attestation` | **0** | 24/24, 3 inapplicable |
| `test_i18n` | **0** | 26/26 |
| `test_binding` | **0** | 0 problems *(see §2)* |

**No regression.** Fifteen suites, all green.

### `verify.py` exit codes, measured without a pipe

| Invocation | Code | Summary |
|---|---|---|
| `--corpus <corpus>` | **0** | 20 PASS, 0 FAIL, 2 NOT TESTED |
| *(no corpus)* | **0** | 18 PASS, 0 FAIL, 3 NOT TESTED |
| `--corpus <corpus> --strict` | **0** | — |
| `--strict` *(no corpus)* | **2** | a **required** guarantee is missing |

---

## 2. One failure, and its diagnosis

`test_binding.py` first returned **code 1** with
`FileNotFoundError: …/binding/manifest.json`.

| Hypothesis | Verdict |
|---|---|
| test error | **no** |
| **procedure error** | **yes** |
| software defect | **no** |
| documentation error | **no** |

**Cause**: `make_fixture.py` does not produce `manifest.json`. The CI builds
it first with `bind.py build`, using `first_observation_id` from
`fixture.json` — and the workflow says so in a comment: *"le manifeste de
liaison est construit ICI : l'exemple commité porte sur l'archive de
démonstration, pas sur la fixture."*

**Correction**: run the missing step. After it, `test_binding` returns
**code 0, 0 problems**.

**Recorded in** `EVIDENCE_TECHNICAL_DEMO.md` §10 so the next person does not
lose time on it.

> No success criterion was modified to obtain a `PASS`.

---

## 3. Scenarios — thirteen expected exit codes, all conforming

Against the shipped demo dossier, `e31e12bb7e32c7a3…`. Each altered copy was
rebuilt preserving the original `ZipInfo`; the original was never opened for
writing, and its digest was **unchanged** afterwards.

| # | Scenario | Expected | Obtained |
|---|---|---|---|
| A1 | `verify.py --corpus` | 0 | **0** — 19 PASS, 0 FAIL |
| A2 | `verify.py` | 0 | **0** — 17 PASS, 0 FAIL |
| A3 | attestation + store | 0 | **0** — 10 PASS, 0 FAIL |
| B1 | one byte **inside** a member | 1 | **1** — digest diverges |
| C1 | one byte **at the end** of the ZIP, `verify.py` | 0 | **0** — 17 PASS, 0 FAIL |
| C2 | same file, attestation | 1 | **1** — archive mismatch |
| D1 | observation removed + recomputed, `verify.py` | — | **0** — 17 PASS, 0 FAIL |
| D2 | same file, attestation | 1 | **1** |
| E1 | `test` key without `--allow-test-keys` | 1 | **1** |
| E3 | binding to an unknown observation | 1 | **1** |
| E4 | private key under the repository root | 1 | **1** — *file not created* |
| F1 | `timestamp.py inspect` | 0 | **0** |
| F2 | `timestamp.py verify --subject` | 0 | **0** — binding holds |
| F3 | `timestamp.py verify --strict` | 2 | **2** — `PENDING` |
| F4 | `timestamp.py verify`, wrong subject | 1 | **1** |

**E2** — store not confronted under `--strict` — returned **2**, as the design
requires.

**D1 is the result that matters**: an amputation with all checks recomputed is
**not** detected by `verify.py` alone. Reproduced here independently of the
demo script.

---

## 4. Corrections applied

Seven findings from the review `REVUE_20261107/` fell within this repository.
All are documentation corrections; **no product code was changed.**

| # | Finding | Where it is now addressed |
|---|---|---|
| 1 | `--corpus` presented as a check performed on Q-2 | `EVIDENCE_USER_GUIDE.md` §4.4, with the counter-test |
| 2 | `--strict` exit codes and their reading | §3 of the guide, with four measurements |
| 3 | "10/10" used as a general detection rate | guide §5, demo §9, limitations §4 |
| 4 | timestamping: implemented, `PENDING`, no date | guide §4.8, limitations §2 |
| 5 | third-party ingestion not confirmed | guide §4.10, limitations §3 |
| 6 | the five reconciliation verdicts | guide §4.9, traceability §3 |
| 7 | kept / exported / published / verifiable | guide §6, traceability §4 |

**Findings belonging to the WordPress site were not executed** — they are
outside this mission and recorded as future dependencies in the review folder.

---

## 5. Frozen references — unchanged

| | Manifest | Files | State |
|---|---|---|---|
| Q-1 | `e6dec1062266f933…` | 20/20 | **unchanged** |
| Q-2 | `83794b85c8a54ead…` | 13/13 | **unchanged** |

Verified on both the working copy and the private versioned copy. The register
of 59 claims is intact, and identifier traceability is preserved.

---

## 6. Repository state

| | |
|---|---|
| Product code modified | **none** |
| Documents added | **12** under `docs/` — six English, six French |
| Stray files left behind | **none** — the refused key was never written |
| Pre-existing untracked directory | `reports/oda3-mukesh-2026-11-06/` — **not touched** |

---

## 7. Reservations

1. **Two capabilities remain NOT CONFIRMED** in real conditions: third-party
   ingestion and reconciliation.
2. **The timestamp proof is `PENDING`** — no date is attested, and no
   attestation of this project carries an anchor.
3. **Q-2 remains `PARTIAL`.** Nothing in this work changes that, and nothing
   was attempted in that direction.
4. **Case G stays undetectable**, and is published as a ceiling.
5. **One divergence is unresolved**: `test_falsification.py` reports an
   amputation as detected where scenario D shows it undetected. The two forgers
   differ in thoroughness and the documentation does not yet say how.

### A procedural lesson, recorded

The first push of this batch shipped **English only**, declaring the French
counterpart a "follow-up". **The CI refused it**: the `discipline du depot`
job enforces the EN/FR pair on every `docs/*.md`, with two named exceptions
that did not apply.

**It was a gate, not a tolerant convention.** The six counterparts were
written rather than adding these files to the exception list — which would
have weakened the gate for a reason that was not one.

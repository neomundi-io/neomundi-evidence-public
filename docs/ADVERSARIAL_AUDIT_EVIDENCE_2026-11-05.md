<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="AUDIT_CONTRADICTOIRE_EVIDENCE_2026-11-05.md">Français</a> · <a href="../README.md">← README</a></sub>

# Adversarial audit — NeoMundi Evidence

**5 November 2026.** Audited before any development, by actively looking for
cases where the instrument would conclude wrongly.

---

## Scope

| | |
|---|---|
| Repository | `neomundi-io/neomundi-evidence-public` |
| Commit audited | `a658af2bbacc9f3d34daee5829498be342b87a54` |
| Working branch | `feat/evidence-observation-binding-v1` |
| Environment | Python 3.12.10, Windows 11, offline |
| Archives exercised | `NEOMUNDI_EVIDENCE_DEMO_V0.1.zip` (GROUNDED-S1) and `NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip` (MED) |

**Out of scope:** the NeoMundi API, the measurement engines, Control Tower,
production. None was touched, none was called.

---

## Protocol

1. inventory of tracked files and their dependencies;
2. run the existing tests, record results **before** any change;
3. build an adversarial probe — `tests/test_adversarial.py` — that fabricates
   hostile archives and watches what the verifier does with them;
4. probe malformed inputs separately.

No capability is claimed on the strength of a README.

---

## Baseline, before any change

| Command | Result | Time |
|---|---|---|
| `verify.py` on GROUNDED-S1 (with `--corpus`) | **19 PASS, 0 FAIL, 2 NOT TESTED** — 21 control lines | 287 ms |
| `verify.py` on MED | **10 PASS, 0 FAIL, 8 NOT TESTED** — 18 lines | — |
| `tests/test_falsification.py` on GROUNDED-S1 | **10/10 detected**, 1 declared limit, 0 problems | — |
| `tools/med_demo_build.py`, rebuild | identical archive: `a0d8a701…`, source ledgers untouched | — |

**No dependency declared, and none needed:** the three Python modules import
only `argparse`, `collections`, `hashlib`, `io`, `json`, `shutil`,
`subprocess`, `sys`, `tempfile`, `zipfile`, `pathlib`.

---

## Capability matrix

| # | Capability | Status | Where | Observed |
|---|---|---|---|---|
| 1 | Artifact ingestion | **PARTIAL** | `verify.py` | reads ZIP members; no ingestion of artifacts outside the archive |
| 2 | SHA-256 computation | **DEMONSTRATED** | `sha256`, `sha256_fichier` | digests recomputed over the delivered bytes |
| 3 | Digest verification | **DEMONSTRATED** | `controle_checksums` | one byte changed → FAIL |
| 4 | Signature verification | **ABSENT** | — | no signature code in the repository |
| 5 | Key identification | **ABSENT** | — | — |
| 6 | Unknown or revoked keys | **ABSENT** | — | — |
| 7 | Manifest validation | **PARTIAL** | `controle_schema` | checks the schema **name** and the member list; no field typing; **crashed** on a malformed manifest |
| 8 | Tamper detection | **DEMONSTRATED** | falsification suite | 10/10, plus 13/15 on the adversarial probe |
| 9 | Package integrity | **DEMONSTRATED** | `controle_checksums` | coverage checked **both ways**: uncovered member, and digest without a member |
| 10 | Reference traceability | **PARTIAL** | `controle_cardinalites` | `observation_id` joins checked **inside** the archive; no external reference |
| 11 | Result provenance | **PARTIAL** | `controle_entrees` | `recording_sha256` and `bundle_sha256` recomputed **if** `--corpus` is supplied; merely declared otherwise |
| 12 | Offline verification | **DEMONSTRATED** | `verify.py` | standard library only, no network primitive, no write |
| 13 | Documentary reconstruction | **ABSENT** | — | — |
| 14 | Actual replay | **ABSENT** | — | — |
| 15 | Replay verification | **ABSENT** | — | — |
| 16 | Report usable by a third party | **PARTIAL** | `Bilan.dire` | readable text output; **no machine-readable output** |
| 17 | Compatibility with NeoMundi measurements | **PARTIAL** | `controle_nulls` | reads measurement records from a Station archive; no binding to external evidence |
| 18 | Compatibility with external evidence | **ABSENT** | — | **this is precisely what phase 1 addresses** |

---

## Adversarial probe — 15 cases about form

`python tests/test_adversarial.py <archive> [corpus]` → **13 detected, 2 missed.**

| Case | Verdict |
|---|---|
| an extra, undeclared member | detected |
| a checksum declared for an absent member | detected |
| a member with an absolute path (`/etc/passwd`) | detected |
| a backslash directory traversal | detected |
| **two ZIP entries with the same name** | detected |
| **a member declared as a symlink** | detected |
| an unknown export schema | detected |
| a manifest with no schema | detected |
| a duplicated `observation_id` | detected |
| a measurement with no `observation_id` | detected |
| an empty JSONL and lying counts | detected |
| an empty checksum manifest | detected |
| an unreadable manifest | detected, **but by crashing** — see A-01 |
| an archive nested inside the archive | **missed** — accepted limit |
| an export timestamp in the future | **missed** — accepted limit |

Both misses are **limits**, not defects: the tool never extracts a nested
archive, and no trusted clock exists to contradict a declared date.

---

## Findings

### A-01 — The verifier crashes on malformed input · **P0**

**7 of 9 malformed inputs produced a Python traceback instead of a verdict.**

| Input | Exception |
|---|---|
| unreadable manifest | `JSONDecodeError` |
| manifest = JSON array | `AttributeError: 'list' object has no attribute 'get'` |
| corrupt `observations.jsonl` | `JSONDecodeError` |
| corrupt `measurements.jsonl` | `JSONDecodeError` |
| non-object line in `observations.jsonl` | `AttributeError: 'str' object has no attribute 'get'` |
| binary `checksums.sha256` | `UnicodeDecodeError` |
| binary `rapport.md` | `UnicodeDecodeError` |

**Why it matters.** The tool's contract is to return `PASS`, `FAIL` or
`NOT TESTED`. A tool that crashes returns none of them. Worse, it then exits
with code 1 — indistinguishable from a legitimate `FAIL` for anyone
automating verification, while the actual meaning is "the tool broke", not
"the archive is bad".

And this is exactly a verifier's job: it is handed archives nobody knows are
sound.

**Same class as a defect already fixed** on 5 November in `controle_csv`,
which read `observations.csv` with no guard. The fix had not been
generalised.

**Correction:** an entry guard on every structured read, returning `FAIL`
with the cause. P0 because phase 1 adds inputs whose shape comes from a third
party.

### A-02 — No machine-readable output · **P1**

`verify.py` wrote text only. A third party wanting to automate verification
had to parse French strings. §3.6 of the brief requires both forms.

### A-03 — No signature verification anywhere · **P1 (finding)**

Capabilities 4, 5 and 6 are **absent**. The repository claims none of them,
and the README says so. So this is not a gap between documentation and code —
it is a real limit to keep visible, and a precondition for any
"cryptographically attested" association.

### A-04 — `controle_schema` does not validate manifest shape · **P1**

It checks the schema **name** and the member **list**. It checks no field
type. A manifest whose `decomptes.observations` is `"a lot"` passes this
control and fails a later one by accident rather than by design.

### A-05 — Indicator divergence reported by a pilot · **not reproduced**

A pilot reports `g_score = 0.3863` in a signed audit against `0.594` on the
dashboard, and a swap between the stability and energy labels.

**Nothing was reproduced here, and nothing could be:** those values belong
neither to this repository nor to the archives it has. The pilot's package was
not supplied. No G-score computation exists in Evidence, and none was
touched.

This belongs to the repository that owns the dashboard. It is recorded here
for the record, **with no conclusion**.

---

## Assurance audit — what is demonstrated, and what is not

The distinction the brief asks for, applied to the actual tool:

| Level | State | Basis |
|---|---|---|
| **Cryptographic integrity** | **demonstrated** | member digests are recomputed over the delivered bytes, and coverage is checked both ways |
| **Authenticity** | **absent** | no signature, no key, no authority |
| **Provenance** | **partial** | for a replayed corpus with `--corpus`, input digests recompute. Otherwise provenance is **declared** |
| **Execution truth** | **out of reach** | no execution artifact is ingested, and nothing ties the archive to a real execution beyond what it declares |
| **Reproducibility** | **partial, and asymmetric** | the MED archive rebuilds byte for byte; a real campaign does not replay, and neither does a ledger |

**The central hole, confirmed by the audit:** an internally perfect archive
remains indistinguishable from a rebuilt one. The falsification suite already
established that; the adversarial probe did not contradict it. Only a digest
kept outside the archive detects it, and no signature attests it today.

That hole is what phase 1 starts to close — **by qualifying the binding, not
by manufacturing it.**

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| A crash read as a `FAIL` by a third-party script | high | A-01, fixed in phase 1 |
| A documentary "association" taken as proof of execution | high | explicit assurance levels, and enforced vocabulary |
| A third party parsing text output with a regex | medium | JSON output (A-02) |
| A measurement `FLAG` read as evidence of fraud | high | Evidence never recomputes nor reinterprets a measurement |
| Regression of existing capabilities | medium | baseline recorded above, re-compared at every step |

---

## Recommendations

**P0 — before any new function**

1. **A-01**: make `verify.py` robust to malformed input. Every structured read
   returns `FAIL` with its cause, never an exception.

**P1 — within this mission**

2. **A-02**: machine-readable output, alongside the text.
3. **A-04**: validate manifest shape, not just the schema name.
4. Bind an observation to external evidence, with explicit **assurance
   levels** — the object of phase 1.
5. Resolve and verify local artifacts within a defined safety boundary —
   phase 2.

**P2 — after this mission**

6. Signing and signature verification (capabilities 4 to 6), which gate any
   "cryptographically attested" association.
7. External anchoring of digests.
8. Replay — feasibility study first, see `REPLAY_FEASIBILITY.md`.
9. Investigate A-05 **in the dashboard's repository**, not here.

---

## What this audit does not establish

It covers one repository and two archives. It says nothing about the evidence
package announced by the pilot — **not supplied, therefore not verified**. It
says nothing either about the API, the measurement engines or the dashboard,
which were neither inspected nor called.

---

## What was done about it, by the end of the 5 November mission

| Finding | State | Where |
|---|---|---|
| **A-01** crash on malformed input | **fixed** | `texte` / `objet_json` / `lignes_jsonl` guards, per-control isolation via `execute`, and a `BILAN` rendered on every path. All 9 malformed inputs now return a motivated verdict |
| **A-02** no machine-readable output | **fixed** | `verify.py --json`, `bind.py verify --json`; the text output is unchanged |
| **A-03** no signature verification | **unchanged, and accepted** | still a real limit. `cryptographically_attested` is declarable but never derivable |
| **A-04** manifest shape not validated | **fixed** | type checking inside `controle_schema`, with no `PASS` line added |
| **A-05** a pilot's indicator divergence | **not investigated here** | belongs to the dashboard's repository; no package was supplied |

Capabilities 13 to 15 — reconstruction, replay, replay verification —
**remain absent**. The feasibility study concludes `NO-GO` on replaying a
measurement to an identical result: see [REPLAY_FEASIBILITY](REPLAY_FEASIBILITY.md).

Capability 18 — compatibility with external evidence — moves from **ABSENT**
to **PARTIAL**: see [BINDING](BINDING.md).

Baselines re-verified after every correction, and identical: GROUNDED-S1
**19 PASS / 0 FAIL / 2 NOT TESTED** over 21 lines, MED **10 / 0 / 8** over 18
lines, falsification **10/10** plus one declared limit.

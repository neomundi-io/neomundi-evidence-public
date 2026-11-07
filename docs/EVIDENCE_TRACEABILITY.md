# NeoMundi Evidence — traceability map

**7 November 2026.** How an artefact travels, what is attached to it, and what
each layer does and does not establish.

Chain: **Measurement → Observation → Ledger → Export → Attestation →
Verification.**

The worked example is **Q-2**, the frozen experimental reference. Its dossier
is private; the identifiers and digests below are quoted from it.

---

## 1. Step by step

### Measurement

| | |
|---|---|
| **Identifier** | `meas-02c6a7f1bf3b0f99…` |
| **Produced** | five signals, `measurement_version 3.3.1`, `checks_emitted 3` |
| **Provenance links** | contains the `observation_id`; the coverage record carries the evaluator of each signal |
| **Controls available** | the signals are confronted with `measured_signals` |
| **Observed** | `status measured`, no refusal |
| **Limit** | no API response carries the **code revision** that produced it — an external trace is required, and that is Station's role |

### Observation

| | |
|---|---|
| **Identifier** | `obs-02c6a7f1bf3b0f99…` — **derived** from campaign, slot and repetition index |
| **Produced** | `prompt_sha256 8b6d6fe6…`, `response_sha256 6ec418cb…`, `model_served`, latency, tokens |
| **Links** | `run_id`, `campaign_sha256 4a6deb10…`, `plan_sha256 c3f7aaf8…` |
| **Limit** | the identifier does **not** distinguish two executions of the same slot. Only `run_id` and timestamps do |

### Ledger

| | |
|---|---|
| **Produced** | 6 records, appended only, chained |
| **Digest** | head `a3fdf598…` |
| **Control** | `station ledger verify --path <ledger>` — recomputed by the instrument that wrote it |
| **Observed** | no anomaly |
| **Limit** | chaining catches an **inconsistent** alteration; a complete rewrite would produce a valid chain |

🔴 The ledger keeps `response_text`. The export does not. See §4.

### Export

| | |
|---|---|
| **Produced** | `station.export.campagne/3`, 9 members |
| **Digest** | `8f1d7259a1b260e1…` |
| **Control** | `python verify.py` — 8 declared member digests recomputed |
| **Observed** | 17 PASS, 0 FAIL, 4 NOT TESTED |
| **Limit** | the archive declares **neither** how many records were exported **nor** which types were excluded. *A valid chain says nothing about what was not exported.* |

### Attestation

| | |
|---|---|
| **Produced** | `campagne-q2.jws`, `1fec125c…` |
| **Key** | `nm-ev-recherche-202611-1`, EdDSA/Ed25519 |
| **Signed input** | **2003 bytes** = `base64url(header)` (82) + `.` + `base64url(payload)` (1920) |
| **Canonical payload** | **1440 bytes**, profile `neomundi-jcs-strings/1` |
| **Control** | `python verify_attestation.py … --store-digest … --strict` |
| **Observed** | 11 PASS, 0 FAIL, 4 NOT TESTED, `--strict` code 0 |

🔴 **The signature does not cover the archive's bytes.** It covers an
eleven-field document that **contains three digests** of it:

| `subject` field | Value |
|---|---|
| `bundle_sha256` | `8f1d7259a1b260e1…` |
| `manifest_sha256` | `f641130c71b49211…` |
| `checksums_sha256` | `d98d275f09d0f262…` |
| `export_schema` | `station.export.campagne/3` |
| `observation_count` | `"1"` |
| `subject_frozen_at_declared` | `2026-11-06T22:38:48Z` |
| `subject_provenance_declared` | *free text supplied by the signer* |

⚠️ **`subject_provenance_declared` is signed, and remains a declaration.**
Signing a sentence does not make it true: it establishes that **we** wrote it
and commit to it.

The **caveats are inside the signed document**, so a verifier cannot ignore
them without ignoring the signature.

### Verification

| | |
|---|---|
| **Control** | signature, member digests, **and the store digest confronted with a second channel** |
| **Observed** | the store's bytes hash to `dac94e8a…`; `mcp.neomundi.org/trust/trust-store-digest.json` declares the same, HTTP 200 |
| **Limit** | both channels are under the **same governance** — this is **not** a third-party trust anchor |

---

## 2. Six layers that must never be conflated

| Layer | Establishes | Does **not** establish | Tool |
|---|---|---|---|
| **Internal integrity** | the members have not moved relative to one another | that the archive is the one we produced | `verify.py` |
| **Whole-archive integrity** | the received file is the one whose digest was recorded | origin, time, truth | `sha256sum` + a digest kept elsewhere |
| **Attestation** | an identified party committed to that digest | the truth of the content | `sign.py attest` |
| **Signature verification** | the signature is valid under a public key in the store | who that party legally is | `verify_attestation.py` |
| **Reconciliation** | field-by-field agreement with an external receipt | which value is right — **nothing is decided** | `adapters/reconcile.py` |
| **Temporal anchoring** | the proof commits to the subject's digest | **the date**, while the proof is `PENDING` | `timestamp.py` |

**Measured demonstration of the first/third distinction**: a byte appended at
the end of the ZIP leaves internal integrity at **17 PASS, 0 FAIL** and is
refused by the attestation.

---

## 3. The five reconciliation verdicts

Not two. Reducing them to two would remove exactly what distinguishes this
tool from a naive comparator.

| Verdict | Condition |
|---|---|
| `MATCHED` | both values present, equal within `--tolerance` |
| `MISMATCHED` | both present, differing beyond tolerance — **both are kept** |
| `MISSING` | the receipt does not carry the field |
| `NOT COMPARABLE` | both present, but not of the same nature |
| `NOT VERIFIABLE` | the receipt's value cannot be confronted with what we hold |

**Observed** on the shipped fixture: `4 MATCHED, 2 MISMATCHED, 1 MISSING,
1 NOT COMPARABLE, 1 NOT VERIFIABLE`. On a mismatch the tool states: *"both
values are kept as they are — nothing is decided here."*

**Status**: TESTED (27/27) and DEMONSTRATED on fixtures. **NOT CONFIRMED** on
a receipt actually produced by a third party.

---

## 4. Kept, exported, published, verifiable

| | Response text | Digests | Who can see it |
|---|---|---|---|
| **Station ledger** | **kept** | yes | us |
| **Export** | **absent** | yes | the recipient |
| **Published** | — | the trust store only | anyone |
| **Verifier's view** | what the export carries | yes | the recipient |

🔴 Four distinct things. *"NeoMundi does not keep responses"* is **false** —
the ledger does. *"The export carries the exchanges"* is **false** too. What
leaves is a deliberate choice.

---

## 5. Assurance levels — derived, never read

| Level | Meaning |
|---|---|
| `declared` | the archive asserts it; nothing confronts it |
| `reference_verifiable` | a digest kept elsewhere allows confrontation |
| `cryptographically_attested` | an identified key has committed |
| `not_demonstrable` | no check could establish it |

These are **computed by the verifier**, never read from the document: an
archive does not decide its own level.

**Observed**: `bind.py verify` derives `reference_verifiable`;
`verify_attestation.py` derives `cryptographically_attested`.

Provenance has its own three-level scale — `instrument_non_documente`,
`instrument_declare`, `instrument_declare_et_configure` — and **there is no
fourth**. A test fails if `instrument_verifie` ever appears.

---

## 6. Links to the qualification references

Q-1 and Q-2 are **frozen** and live outside this repository, in the operator's
private versioned space. Their integrity manifests are
`e6dec106…` (20 files) and `83794b85…` (13 files), verified unchanged on
7 November 2026.

| Claim traced here | Registry id |
|---|---|
| chain, execution, measurement | `CH-001` … `CH-006`, `ME-001` … `ME-003` |
| signals and their nature | `SI-001` … `SI-009` |
| ledger, export, code provenance | `ST-001` … `ST-008` |
| Evidence controls | `EV-001` … `EV-007` |
| attestation | `AT-001` … `AT-006` |
| trust store, two channels | `C5-001` … `C5-003` |
| replay and timestamping | `RE-001` … `RE-004`, `FU-001` |
| explicit prohibitions | `IN-001` … `IN-004` |

The register of 59 claims is kept with the qualification dossiers, not in this
repository: it carries references to private artefacts.

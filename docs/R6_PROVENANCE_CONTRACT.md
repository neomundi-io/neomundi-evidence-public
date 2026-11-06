<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="R6_PROVENANCE_CONTRACT.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# R-6 — evaluator provenance: contract proposal

**6 November 2026.** Answers recommendation **R-6** of the ODA3 evaluation:
*record the evaluator's provenance in `measurements.jsonl`.*

> **Proposal only. Nothing implemented, and nothing proposed for Station.**
> The contract below is to be agreed before anyone writes code.
>
> The **measured inventory** behind this proposal — which evaluator, which
> model, which engine, with which configuration fingerprints — is held
> internally and not published here. Publishing the measuring instrument's
> internals is a disclosure decision, not an engineering one. This document
> states what was measured in numbers, and names no model, host or
> fingerprint.

---

## Correction of 6 November 2026 — the audit revises this proposal

**This document proposed a structure Station already has.** The repository
audit established it, and the proposal is simplified rather than complicated.

| Link | Actual state | Evidence |
|---|---|---|
| The API **emits** provenance | OK | `GovernResponse.evaluators` — per signal: evaluator, model used, status, reason, configuration fingerprints |
| Station **models its retention** | OK | `src/station/runtime/coverage.py`: `MeasurementCoverage`, record type `measurement_coverage`, with its **anti-secret barrier applied at construction** and its tests |
| Station **wires** the write | NO | `to_coverage()` has **no caller** in `src/` — only its definition, its re-export and a unit test |
| The ledger carries it | NO | **0 records** of `measurement_coverage` across three ledgers (actual types: `run`, `runner_attempt`, `observation`, `measurement`, `reference_evaluation`, `replay_provenance`) |
| The **export** carries it | NO | `station.export.campagne/2` = 8 members, **0 occurrences** of `coverage` in `src/station/runner/export.py` |
| Evidence consumes it | OK **now** | `adapters/provenance.py`, and `verify.py` accepts `/3` |

**Two rectifications to this document.** Its §3 announced "0 provenance
fields across 238 measurements": true, and measured on **frozen ledgers**
written before `coverage.py` existed. The conclusion changes: the gap is not
conceptual, it is **wiring**.

And its "Part A / Part B" invented a split. `MeasurementCoverage` proposes a
better one, for a reason I had missed: `Measurement` is a **sealed schema**,
and the digest of every record already written depends on the shape of the
contract. A **new contract** migrates none of them. So the existing model is
adopted, not mine.

---

## The three decisions, argued

### D1 — wire `to_coverage` into the write path

**Recommendation: YES, and it is the cheapest of the three.** The model
exists, is tested, carries its own anti-secret barrier, and is a **separate**
record type: no sealed schema migrates, no already-written digest moves. It
is a connection, not a design.

Without D1, D3 has nothing to carry.

*Station, separate branch and PR. Not done here: it touches the write path of
a live measurement.*

### D2 — instrument the under-populated evaluators

**Recommendation: NOT NOW, and above all not as a prerequisite.**

Three situations hide behind "under-populated", and conflating them would be
wrong in two directions: a **local computation** has no model and no prompt —
its nulls are **correct**, and `adapters/provenance.py` does not read them as
a gap; two evaluators **do call** a model without reporting their engine —
that is a genuine under-population, API-side; one populates everything,
because it crosses an HTTP boundary and had to.

The contract must therefore **accept `null` with a reason**, rather than wait
on instrumentation that would fabricate a plausible value. A fabricated
provenance is indistinguishable from a real one, and that is the one risk in
this work that cannot be undone.

### D3 — the export carries the member

**Recommendation: YES.** One more member, additive, the other eight
unchanged. `verify.py` already accepts `/3`, and a `/2` archive stays
readable: provenance controls return `NOT TESTED` there, never `FAIL` — the
gap is the producer's, exactly as for the completeness contract.

---

## The consolidated contract — `station.export.campagne/3`

**One member added: `measurement_coverage.jsonl`.** It carries the
`MeasurementCoverage` records as Station writes them, in the ledger's
original bytes, uninterpreted:

```
coverage_id | measurement_id | observation_id | measurement_version
coverage_version | api_measurement_status | checks_attempted
checks_succeeded | failed_checks | degraded_g_inputs
unmeasured_signals | evaluators | reported_at
```

`evaluators` is **opaque and verbatim**: one dictionary per signal, whose
present fields Evidence observes and whose absent ones it names, never
completing one. The six diagnostic fields are **all optional**, and their
`None` carries meaning: an earlier API does not serve them, and such a
silence cannot claim that all went well.

**What Evidence does with it**, and the three levels it derives:

| Level | When |
|---|---|
| `instrument_non_documente` | no coverage member, or no `evaluators` at all |
| `instrument_declare` | evaluators are named, with no configuration fingerprint |
| `instrument_declare_et_configure` | named **and** configured, for every signal that has a model |

**There is no fourth level.** `instrument_verifie` would be a claim no
archive can support: that the declared evaluator is the one that ran would
require observing the measurement. It is a permanent `NOT TESTED`, and case
11 of `tests/test_provenance.py` fails if a fourth level appears.

---

## The short answer

**The provenance cannot be documented from existing data, so R-6 requires a
contract evolution.** Measured, not inferred:

- the measurement API **already emits** a 12-field provenance block per
  signal, and the evaluator's identity is populated for **5 of 5 signals on
  7 of 7** observations;
- the ledger keeps **none of it** — 0 provenance fields across **238
  measurements in 8 frozen ledgers**, all `measurement_version 3.3.1`;
- so no Evidence archive can export what its ledger never held.

**The loss happens at the ledger write, in Station. Not in Evidence, and not
in the API.** That single fact decides where the change belongs — and it is
not here.

---

## 1. What was measured

| Question | Answer |
|---|---|
| Is the evaluator's identity recorded at the API? | **yes, completely** — 5 signals × 7 observations, no gap |
| How many provenance fields reach the ledger? | **zero**, on 238 measurements across 8 ledgers |
| How many evaluators fully populate the deep fields? | **1 of 5** — the only one that calls an external HTTP API |
| How many signals share a single evaluator call? | **2** — one call, one model, two scores |
| Can the gap be retrofitted on historical archives? | **no** |

**R-6's premise needs one refinement.** The evaluator's identity is not
missing — it is recorded, and then dropped. R-6 is not about inventing
fields; it is about carrying existing ones across a boundary.

### Three distinct situations behind "under-populated"

- One evaluator is a **local computation**: no model, no prompt. Its nulls
  are **structurally correct**, not a gap. A contract demanding a prompt hash
  here would demand a value that does not exist.
- Two evaluators **do call a model** and report neither attempts, nor engine,
  nor configuration fingerprint. **That is a genuine under-population**, and
  it is the only part of R-6 that is an instrumentation defect rather than a
  contract gap.
- One evaluator populates everything, because it crosses an HTTP boundary and
  had to.

Lumping these three together as "missing provenance" would be wrong in two
directions at once.

## 2. Stable identifiers versus per-call values

This is the finding that changes R-6's cost, and it must be read with its
sample size: **n = 7**.

| | Count | Nature |
|---|---|---|
| **Stable by nature** | 5 fields | configuration identifiers: they change when the instrument changes, not per measurement |
| **Per-call, constant in this sample** | 3 fields | **n = 7 proves nothing about their stability.** One of them exists precisely because a fallback is possible, another because a retry is |
| **Per-call** | 1 field | latency: 7 distinct values |

**Consequence for the contract.** Five fields belong **once per campaign**,
not on every measurement. Recording them per measurement would multiply 238
identical copies and invite a reader to think they were measured each time.

But the fallback indicator and the attempt count must stay **per
measurement**: a measurement served by a fallback is not the same evidence as
one served by the primary, and seven successes cannot establish otherwise.

## 3. Consequences for historical archives

**Uniform, and not retrofittable.**

- **238 of 238** measurements carry no provenance. There is no subset to
  salvage and no version that behaved differently.
- **No retrofit is possible.** Reconstructing which model served a
  measurement from October would mean asserting it from configuration
  *believed* to have been in force. That is an invention, and it would be
  worse than the gap: **a fabricated provenance is indistinguishable from a
  real one.**
- **The frozen corpora stay as they are.** Their digests are chained and, for
  some, attested.
- Any claim about the evaluators of an existing archive is therefore
  **`not_demonstrable`** — not `declared`, because nothing declares it.

### The asymmetry that is hard to defend

The same ledger records, richly, the **observed model** (provider, requested,
served, attestation, parameters sent and effective, prompt version and
digest) and the **reference evaluator** (versioned and fingerprinted).

And **nothing** about the five instruments that produced the signals.

So the archive traces the *subject* of the measurement and the *reference*
used to judge it, and not the *measuring instrument*. Stated plainly, that
ordering is the wrong way round.

---

## Contract proposal — `station.export.campagne/3`

> **SUPERSEDED** by "The consolidated contract" above. This version invented
> a Part A / Part B split; `MeasurementCoverage` proposes a better one, and it
> exists. Kept as a record of the reasoning, and **not to be implemented**.

A **new version**, not a modification of `/2`. Three parts.

### Part A — a campaign-level `evaluateurs` block

The five configuration identifiers, once, in the manifest:

```json
"evaluateurs": {
  "contrat": "neomundi.evaluator-provenance/1",
  "par_signal": {
    "<signal_a>": {
      "evaluator": "<function identifier>",
      "kind": "computation",
      "model_configured": null,
      "evaluator_runtime": null,
      "prompt_template_hash": null,
      "inference_config_hash": null,
      "config_fingerprint": null
    },
    "<signal_b>": {
      "evaluator": "<function identifier>",
      "kind": "external_model",
      "model_configured": "<model identifier>",
      "evaluator_runtime": "<engine host>",
      "prompt_template_hash": "<16 hex>",
      "inference_config_hash": "<16 hex>",
      "config_fingerprint": "<16 hex>",
      "shares_call_with": ["<signal_c>"]
    }
  }
}
```

`kind` is what makes the nulls readable: `computation` declares that no model
and no prompt exist, so their absence is **correct** and a verifier must not
treat it as a gap. Without it, every verifier would have to hard-code which
signals have models.

`shares_call_with` prevents the duplication trap of §1: two signals, one
call, and a reader who should know it. Without it, a reader would reasonably
count two independent instruments where there is one.

### Part B — per measurement, only what varies

```json
"evaluateurs_execution": {
  "<signal_b>": {
    "status": "measured", "reason": null,
    "model_used": "<model identifier>", "served_by": "primary",
    "attempts": 1, "latency_ms": 0.0
  }
}
```

Six fields, not twelve. The fallback indicator and the attempt count are
here and **not** in Part A, for the reason in §2.

### Part C — what Evidence verifies, and what it refuses to

| Control | Verdict |
|---|---|
| the manifest declares an `evaluateurs` block | `PASS` / `NOT TESTED` if absent |
| every measured signal has an entry | `PASS` / `FAIL` on a gap |
| a `computation` evaluator declares no model | `PASS` / `FAIL` if it declares one |
| an `external_model` evaluator declares its engine and fingerprints | `PASS` / `FAIL` if partial |
| `model_used` agrees with `model_configured`, or the fallback indicator explains why not | `PASS` / `FAIL` / `NOT TESTED` |
| **that the declared evaluator is the one that ran** | **never verifiable.** A permanent `NOT TESTED` |

The last line is the important one. Evidence can check that a declaration is
**complete and internally coherent**. It cannot check that it is **true** —
that would require observing the measurement, which is Station's role and not
an archive's. Any control claiming otherwise would be the false `PASS` this
product exists to refuse.

---

## Compatibility

| | |
|---|---|
| `/2` archives | **unchanged, and still valid.** The controls above are `NOT TESTED` on them, never `FAIL` — the gap is the producer's, exactly as for the completeness contract |
| `/3` archives | the new controls apply |
| `verify.py` | must accept both schemas. It already keeps a list of known schemas |
| Frozen corpora | untouched. No re-export, no re-signing |
| Comparability | **a `/3` archive is not comparable to a `/2` on provenance** — not because the values differ, but because one side has none. That boundary must be declared like the others |

## Risks

| Risk | Why it matters |
|---|---|
| **Inventing provenance for the under-populated evaluators** | the real danger. If an evaluator cannot report its engine, the contract must accept `null` **with a reason**, not a plausible-looking value |
| **Reading a `/3` archive as validating the past** | publishing a `/3` with full provenance may make the 238 historical measurements look deficient. They are not: they were produced under a contract that did not ask |
| **Mistaking two signals for two instruments** | mitigated by `shares_call_with`, and only by it |
| **Inflating every measurement by 60 fields** | mitigated by the A/B split. Done naively, R-6 would add five 12-field blocks to each of 238 records |
| **Treating a complete declaration as a true one** | the structural risk of all provenance. Mitigated only by the permanent `NOT TESTED` of Part C |
| **Disclosing the instrument's internals** | naming models, hosts and configuration fingerprints in a public archive is a **disclosure decision**. It is not taken here, and a `/3` producer must take it deliberately |

## What this proposal does NOT ask of Station

Nothing, yet. It describes what a `/3` export would carry **if** Station
chose to write it. Three distinct decisions follow, and none is taken here:

1. whether Station's ledger write keeps the API's provenance block;
2. whether the two under-populated evaluators are instrumented;
3. whether the export carries it.

Only the third concerns Evidence, and it is the last of the three.

---

## Recommendation

**R-6 is a real gap, correctly identified, and it cannot be closed by
documentation.** But its cost is lower than "structural" suggests: the
provenance already exists at the API, the contract is already uniform, and
five of its eight populated fields belong once per campaign rather than on
every record.

What Evidence can do **today, without touching anything**: declare the
absence. A control line stating that a `/2` archive carries no evaluator
provenance, and that any claim about the measuring instrument is therefore
`not_demonstrable`. That is not R-6 — it is the honest statement of R-6 being
open, and it belongs in a later change rather than in a proposal.

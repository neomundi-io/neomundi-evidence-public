<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="REPLAY_FEASIBILITY.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Replaying a measurement — feasibility study

**5 November 2026.** A study only. Nothing was replayed, nothing was built,
no execution was triggered.

---

## The question

Given an evidence package, can the measurement be **replayed** to obtain the
same result?

The answer depends entirely on what "replay" and "the same" mean. Three
distinct things are routinely conflated:

| | What would be redone | Verdict |
|---|---|---|
| **Input replay** | re-submit the same recorded inputs to the same code | **GO** |
| **Measurement replay** | obtain the same five signals | **NO-GO** as things stand |
| **Byte-exact ledger reproduction** | rewrite an identical ledger | **NO-GO**, and never to be claimed |

---

## What the archives already provide

Measured on `NEOMUNDI_EVIDENCE_DEMO_V0.1.zip`, schema
`station.export.campagne/2`, 30 observations:

| Element | State | Consequence for a replay |
|---|---|---|
| `code_commit` | **single** — `a52715d3…` across all 30 | the code revision is identified |
| `config_snapshot_sha256` | **single** — `7882f080…` across all 30 | the configuration is identified by digest |
| `measurement_version` | **single** — `3.3.1` | the measurement contract is identified |
| `replay_provenance.jsonl` | 30 records, `recording_path` + `recording_sha256` + `bundle_sha256` | **inputs are identifiable and verifiable** |
| Ledger | 151 records, head `fc1f2787…`, `chaine_verifiee: true` | declared by the exporter, **not recomputed** by `verify.py` |

Input digests recompute: that is `verify.py`'s `empreintes des entrées
rejouées` control, which returns 30/30 conforming when the frozen corpus is
supplied.

**So the first stage of replay is settled.** The inputs are there, and they
can be proven to be the right ones.

---

## Why the second stage is not

### 1. Incomplete measurements are the rule, not the exception

Of the 30 measurements in this batch:

| Status | Count |
|---|---|
| `measured` | 15 |
| `degraded` | 8 |
| `not_measured` | 7 |

And per signal, the number of **absent** values:

| Signal | `null` out of 30 |
|---|---|
| `semantic_instability_score` | 22 |
| `factual_hallucination_score` | 14 |
| `stability_score` | 14 |
| `coherence_score` | 7 |
| `semantic_risk` | 7 |

A faithful replay would have to reproduce **those absences**. But a missing
signal is not a property of the input: it is the trace of what was reachable
at measurement time. Reproducing it would mean reproducing the evaluators'
state, not the corpus's.

That is the blocker, and no amount of code works around it.

### 2. The evaluators are remote and non-deterministic

Measurement calls external evaluators. Their availability varies, and an
outage yields a `degraded` or `not_measured` rather than an error. Two
consequences:

- two runs on the same input may return different coverage, with neither
  being wrong;
- the model **served** is not guaranteed to match the model **requested**: the
  published identifier is the requested one, and an alias can move.

### 3. This batch is in the `synthetic` regime

`regimes_d_execution: ["synthetic"]`, and the reading guard written into the
archive says so:

> these responses were fabricated for the bench and observe no real operator.

So replaying GROUNDED-S1 successfully would say **nothing** about whether a
real campaign can be replayed. A replay demonstrated on synthetic data would
be a demonstration on the wrong object.

### 4. Data freeze is not computational reproducibility

The two have been kept separate since GATE 0, for an observed reason: seven
divergences had been attributed to a later code change. A frozen corpus
guarantees the **inputs**. It does not guarantee the computation redoes
itself identically.

---

## Verdicts

### Input replay — **GO**

Feasible today, and already done: the `replay` regime exists, input digests
verify, and `bind.py` now allows attaching the input recording to the
observation with a derived assurance level.

**What this establishes:** that the replayed inputs are the record's own.
Nothing more.

### Measurement replay, **identical** result — **NO-GO**

Blocked by points 1 and 2, neither of which is a defect to be fixed. Claiming
them solved would be false.

**Condition to lift:** that measurement become deterministic at constant
inputs, which would require local, frozen evaluators attested by the digest
of the served model. That is not an evolution of this repository.

### Measurement replay, **comparable** result — **conditional GO**

Feasible, on five conditions, all of them checkable:

1. **a divergence budget declared in advance** — a per-signal tolerance,
   written before the run, not after;
2. **coverage compared before values** — two measurements with different
   coverage are not comparable signal by signal;
3. **identical `measurement_version` on both sides**, otherwise comparability
   boundaries are crossed;
4. **evaluator provenance recorded** on both sides, including the model
   actually served where it is attested;
5. **no paid call without explicit authorisation** — which in practice points
   to a local test environment rather than production.

**What this would establish:** that the computation redoes itself within an
announced tolerance. Not that the original result was right.

### Byte-exact ledger reproduction — **permanent NO-GO**

Never to be claimed. A ledger carries timestamps and a chain; rewriting it
identically would mean reproducing the instant it was written. The freeze is
the only authoritative record, and that is how it was constituted.

---

## What would have to be built, and in what order

None of this is built here, and none of it should be without a decision.

| Step | Object | Prerequisite |
|---|---|---|
| 1 | a replay harness **outside production**, on the workstation's Ollama | none — both models are already there |
| 2 | record evaluator provenance on every replay | that the contract carries it on both sides |
| 3 | compare coverage first, values second, tolerance declared | step 1 |
| 4 | a divergence report distinguishing *absent*, *different* and *out of tolerance* | steps 2 and 3 |
| 5 | replay on a **non-synthetic** batch | an authorisation, and a frozen real corpus |

Step 5 is the one that counts, and the only one needing an operating decision
rather than development.

---

## What this study does not establish

It rests on the two demonstration archives and what they declare. The Station
code was not re-read for this study, no campaign was launched, and no
evaluator was called. The durations, costs and success rates of a real replay
remain **unknown**: no figure is advanced here because none was measured.

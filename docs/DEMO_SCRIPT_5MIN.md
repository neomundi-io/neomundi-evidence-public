<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="DEMO_SCRIPT_5MIN.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Demonstration script — five minutes

**Executed and timed on 5 November 2026.** Five runs: **7 s, 6 s, 7 s, 8 s, 7 s**
of machine time, identical outcomes.

The five-minute budget is therefore not constrained by the machine. It is
entirely available for narration: **7 seconds of execution, about 4 min 50 of
speech.**

A single command runs the whole thing:

```sh
GEL=<freeze> bash demo_5min.sh /tmp/demo
```

The script writes only into its output directory. It touches neither the
freeze, nor the instrument's repository, nor production.

---

## What the demonstration must let people observe

Four things, in this order, and the fourth is the most important:

1. an evidence file is produced from a frozen corpus;
2. it verifies **without NeoMundi**;
3. verification **refuses** a tampered archive;
4. there is a falsification it **does not see**, and we show it.

A demonstration that stops at step 3 sells a guarantee. This one stops at
step 4.

---

## Run-through, with the speaking budget

### Step 1 — the starting point verifies · t+0 s · *45 s of speech*

| Observed result | |
|---|---|
| freeze | `12 PASS, 0 FAIL, 3 NOT TESTED` |
| chain | 151 records, head `fc1f2787e6e0e24f…`, no anomaly |

**To say:** we do not start from a working directory but from a **frozen**
corpus, whose hashes were recorded on 5 November and whose chain re-verifies.
And the freeze verifier returns three `NOT TESTED` — it states what it does not
do.

### Step 2 — the file is produced · t+3 s · *45 s of speech*

30 observations, 1 run, and the archive's hash.

**To say:** the export **refuses** to produce anything if the chain does not
verify, if the campaign is empty, or if the output file already exists. It then
re-reads the archive it has just written. And that hash must be kept
**elsewhere** than with the archive — which is the thread of step 4.

### Step 3 — it verifies without NeoMundi · t+4 s · *60 s of speech*

→ **`19 PASS, 0 FAIL, 2 NOT TESTED`**

**To say:** `verify.py` has no dependency, emits no network call, writes
nothing. It is meant to be **read** before being run. The two `NOT TESTED` are
named with their reason: the JCS chaining, which we refuse to reimplement here,
and the archive's origin, which no local verification can establish.

### Step 4 — verification refuses, then fails · t+4 s · *90 s of speech*

→ **`10/10 alterations detected, 1 declared limitation, 0 problem`**

Ten attacks refused: one byte changed, a measurement removed with checksums
recomputed, a `null` signal declared measured, an orphan measurement, an
invented absence, the regime guard erased, a secret injected, a CSV formula, a
member escaping the directory, the manifest removed.

**Then the eleventh, which passes.** One observation erased *everywhere* — its
measurement, its evaluation, its provenance — with counts fixed and checksums
rebuilt: nothing contradicts anything any more, and no internal check can see
it.

**To say, word for word:** "This is what our verification cannot do. A careful
forger produces a coherent file. The only defence is the archive's hash, kept
somewhere other than with the archive. That is why we will send it to you
through a separate channel, and why external anchoring is on our roadmap — it
does not exist today."

### Step 5 — the report states what it does not know · t+7 s · *60 s of speech*

Four places in the report, in order:

| | What to show |
|---|---|
| Null values | "cost not established: 30 of 30" — **no sum is displayed**, because there is nothing to sum |
| Measurements, per signal | `semantic_instability_score`: 8 measured, **22 `null`**. None became a `0` |
| Execution regime | the guard: here `provider_attested` attests a replayed recording, **not a provider** |
| Limits | seven statements, inside the archive — not in a brochure |

**To say:** the measurement states are 15 `measured`, 8 `degraded`, 7
`not_measured`. A file that promises "an absence stays an absence" needs
absences to demonstrate it. This one has them.

---

## What the demonstration does not establish

To be said in closing, without being prompted:

- **the correctness of the signals** — the existence of a score does not
  establish it;
- **the authenticity of the archive** — no signature, no opposable timestamp;
- **that this corpus says anything about a real model** — its regime is
  `synthetic`: it establishes that the chain works, and nothing about the
  outside world;
- **that a buyer wants to pay for this** — that is the question we are coming to
  ask.

---

## What remains with the person presenting

The script measures machine time. It does not measure speech.

**Before the review:** run the script once out loud, watch in hand, to check
that the five speaking budgets hold. That is the only part no execution can
establish.

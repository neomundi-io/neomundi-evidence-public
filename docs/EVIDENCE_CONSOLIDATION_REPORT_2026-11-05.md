<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Consolidation report — NeoMundi Evidence

**5 November 2026.** Branch `feat/evidence-observation-binding-v1`, off
`a658af2`. Pull request prepared, **not merged, not deployed**.

---

## Scope held

None of this was touched or called: the NeoMundi API, the measurement
engines, Control Tower, production, the existing contracts, historical data,
the G-score computation. No paid external call was made. `evidence-journey`
is preserved untouched — HEAD `18cf5719`, zero modifications, `index.html`
still `cfb9104c…`.

---

## Synthesis

| Domain | Initial state | Action taken | Final state | Evidence |
|---|---|---|---|---|
| **Integrity** | DEMONSTRATED, but the tool crashed on malformed input | entry guards, per-control isolation, `BILAN` on every path | **DEMONSTRATED and robust** — 9 of 9 malformed inputs return a motivated verdict | `tests/test_adversarial.py`, 13 detected / 2 limits / 0 crashes |
| **Provenance** | PARTIAL — recomputed only with `--corpus` | unchanged in principle; the level is now named and derived | **PARTIAL, and said to be** | `verify.py`, `empreintes des entrées rejouées` control, 30/30 |
| **Observation / evidence binding** | **ABSENT** | level 1 built: schema, builder, verifier, four derived assurance levels | **PARTIAL** — `reference_verifiable` reachable, `cryptographically_attested` never | `tests/test_binding.py`: 1 positive, 17 negative, 1 scientific, 0 problems |
| **Artifact resolution** | ABSENT | level 2: explicit root, refuses absolute paths, traversals and outward symlinks, read ceiling | **PARTIAL, local only** — no URL is ever resolved | 4 dedicated negative cases |
| **Reconstruction / replay** | ABSENT | **no development** — feasibility study only | **ABSENT**, with a reasoned GO/NO-GO | `docs/REPLAY_FEASIBILITY.md` |
| **Documentation** | 7 EN/FR pairs | +4 pairs: audit, binding, feasibility, this report; terminology in 10 terms | **consolidated, 11 pairs** | reviewed, links checked |
| **Demonstration** | `demo_5min.sh` | `demo_binding.sh` **added**, the existing one untouched | **extended** | execution observed, 3 distinct verdicts |

---

## Baselines, before and after

Recorded before any change, and re-verified after each one. None moved.

| | Before | After |
|---|---|---|
| `verify.py` on GROUNDED-S1 | 19 PASS / 0 FAIL / 2 NOT TESTED, 21 lines | **identical** |
| `verify.py` on MED | 10 / 0 / 8, 18 lines | **identical** |
| `tests/test_falsification.py` | 10/10, 1 declared limit | **identical** |
| `tools/med_demo_build.py` | reproduces `a0d8a701…` | **identical** |

No `PASS` line was added, deliberately: the counts of 21 and 18 lines are
cited by frozen documents, including the suspended Evidence Journey page. New
controls speak only on failure.

---

## The nine answers

### 1. What can NeoMundi Evidence demonstrate today?

Three things, and not a fourth.

**That the bytes of an evidence package have not moved.** Member digests are
recomputed over the delivered bytes, and coverage is checked both ways: an
uncovered member is seen, and so is a digest with no member.

**That a tampered package is refused.** Ten content alterations out of ten are
detected, and fifteen hostile archives out of fifteen receive a verdict —
thirteen of them a refusal.

**That an offered file is the one a record refers to.** This is what the
mission added: its bytes hash to a digest the record declares, and that
record is hash-chained.

### 2. What can it verify automatically?

With no intervention, offline, with no dependency: **21 controls** on a
GROUNDED-S1 archive, **18** on MED, **11 to 13** on a binding.

Every control returns `PASS`, `FAIL` or `NOT TESTED`, and the three stay
distinct. A `NOT TESTED` always carries its reason. Since this mission, a
malformed input returns a motivated `FAIL` instead of a traceback — which
matters because an exit code of 1 with no verdict was indistinguishable from
a legitimate refusal.

Both verifiers also write a JSON report, so a third party need not parse
French strings.

### 3. Can it tell an execution narrative from verifiable evidence? Within what limits?

**Yes, and a dedicated test demonstrates it.** Two manifests carrying
word-for-word identical prose:

```
  Scenario A: 1 statement, 0 artifacts → declared
  Scenario B: 1 statement, 2 artifacts → reference_verifiable
```

Scenario A is neither refused nor accepted: it is reported for what it is, a
declarative document. Statements attached to a manifest are **always**
`NOT TESTED`, with the explicit note that a textual description of an
execution is not proof that the execution took place.

**The limits.** The distinction rests on the presence of a recomputable
anchor, not on the truth of the narrative. An **accurate** narrative with no
artifact stays `declared`; a **false** narrative accompanied by anchored
artifacts earns `reference_verifiable` for those artifacts — the tool does not
read prose and does not contradict it. It only refuses to let it count as
evidence.

### 4. Can it bind a NeoMundi observation to external artifacts without modifying the API?

**Yes, and the API did not have to change by a single byte.**

The anchor already existed: an observation record declares `response_sha256`,
`prompt_sha256`, `request_sha256` — digests of objects that are not in the
archive. The provenance record adds `recording_sha256` and `bundle_sha256`.
Six anchor points, all already published by Station.

The binding hooks onto them without asking anyone for anything. Verified on a
real observation: both offered artifacts hash to two of those six digests.

One design detail matters more than it looks: the manifest copies the declared
digests, and the verifier **confronts them with the record** instead of
believing them. It is the only control that catches a forger who remade the
artifact *and* the manifest in concert.

### 5. Can it fetch and verify the artifacts?

**Locally, yes. Remotely, no — and that is a choice, not a gap.**

Artifacts are files under an explicit root. Four refusals: absolute path,
directory traversal, outward symlink, and a size beyond the read ceiling
(64 MiB by default, adjustable).

**No URL is ever resolved, and no network is touched.** A verifier that went
and fetched whatever a document pointed at would become an exfiltration
instrument; both tools import only the standard library and contain no network
primitive.

A missing artifact returns `NOT TESTED`, not `FAIL`: its claim was not
contradicted, it was not exercised. The binding then falls back to `declared`,
and the report says the **verification** is incomplete — not that the manifest
is false.

### 6. Can it reconstruct or replay an execution?

**No. And the study says which of the three senses are reachable.**

| | Verdict |
|---|---|
| Replay of the **inputs** | **GO** — already done, and input digests verify |
| Replay of the **measurement**, identical result | **NO-GO** |
| Replay of the measurement, **comparable** result | **conditional GO**, on five conditions |
| **Byte-exact** ledger reproduction | **permanent NO-GO**, never to be claimed |

The blocker is not a defect to fix. In this batch,
`semantic_instability_score` is **null in 22 of 30 measurements**, and only 15
measurements are `measured` against 8 `degraded` and 7 `not_measured`. A
faithful replay would have to reproduce **those absences**, which are not a
property of the input but the trace of what was reachable at the moment of
measurement.

Add that this batch is in the `synthetic` regime: replaying it successfully
would say nothing about a real campaign.

### 7. What guarantees can reasonably be presented to a company?

Four sentences, each backed by an observed execution.

> **The integrity of an evidence package is verifiable by you, offline, with
> nothing to install.** One standard-library Python file, 21 controls, and
> three states that are never merged.

> **Tampering is detected.** Ten alterations out of ten, and fifteen hostile
> archives out of fifteen receive a verdict.

> **A file we hand you can be tied back to the record that mentions it**, by
> recomputing a digest, without trusting us and without touching our API.

> **What we cannot do is written down**, in the tool and in its output, on
> every run.

### 8. What guarantees must absolutely not be claimed?

Seven, and the first three are the most tempting.

1. **"Proof that the execution took place."** Never. Binding an artifact to a
   record says neither that the execution happened, nor when, nor at whose
   hands.
2. **"Authenticity"** or **"signed"**. No signature is verified.
   `cryptographically_attested` is declarable and **never** derivable — a
   manifest claiming it is refused.
3. **"Reproducible"** in the computational sense. The freeze guarantees the
   inputs, not that the measurement redoes itself identically.
4. **"Certified timestamp."** No trusted clock. `created_at`, `exporte_le` and
   `recorded_at` are declared and contradicted by nothing — a date in the
   future passes, and that is an accepted limit.
5. **"Chaining verified by the tool."** `verify.py` leaves it `NOT TESTED` by
   design: recomputing it here would be a second implementation of the ledger.
6. **"Medical, legal or factual validation."** A measurement is a measurement.
   Demonstration B covers a medical corpus and validates no medical answer.
7. **"Tamper-proof archive."** A forger who rebuilds the whole archive produces
   a consistent package. Only a digest kept **elsewhere than with it** detects
   that.

### 9. What are the genuinely priority improvements next?

Ordered by evidential value gained, not by ease.

**P0 — sign, and anchor outside.** It is the only piece of work that unlocks a
whole assurance level. Today `cryptographically_attested` exists in the scale
and is never reachable; signing the manifest with an identified key, and
anchoring the digest outside the archive, would close finding A-03 and the
audit's central hole at once. Everything else is secondary to it.

**P1 — the replay harness outside production.** On the workstation's Ollama, at
zero cost, with a divergence budget declared in advance and coverage compared
before values. It is step 1 of the feasibility study, and the only one needing
no authorisation.

**P1 — translate the verifiers' output.** It is in French; the documentation is
bilingual. A foreign auditor today reads strings they cannot understand. The
JSON report mitigates; it does not replace.

**P2 — investigate A-05 in the dashboard's repository.** The indicator
divergence reported by a pilot (`g_score` 0.3863 against 0.594, and a swap of
the stability/energy labels) does not belong to this repository and could not
be reproduced here. The announced evidence package was not supplied.

**P2 — the adversarial probe's two accepted limits:** the nested archive, never
extracted, and the future timestamp, which nothing contradicts. Lifting them
needs an extraction policy and a trusted clock respectively — hence the P0
work.

---

## What this mission fixed, and how it surfaced

Four defects, and **none was found by re-reading the code.**

**The verifier crashed on seven of nine malformed inputs.** Found by
fabricating hostile archives. The existing falsification tests could not see
it: they only alter well-formed content. A verifier is by definition handed
archives nobody knows are sound, and a crash is the worst failure there —
exit code 1 with no verdict, indistinguishable from a legitimate refusal.

**`main`'s seven early returns skipped the `BILAN`.** Found because my own
probe counted "crashes" by the absence of a `BILAN` line and flagged two that
were not crashes at all.

**A missing artifact returned `FAIL`.** Found by my own negative test, which
expected a degradation and got a refusal. A file not supplied does not
contradict its claim: it prevents the claim from being exercised. Conflating
the two merged states this product keeps separate.

**A `PASS` on "no claim exceeds what was demonstrated" when zero claims had
been exercised.** Found by reading real output, not the code. It was an
invented success over an empty sample.

And one mistake of mine, caught by the archives themselves: I had assumed
`fichiers` was a table in the manifest, when it is a **list**. The new control
failed both valid archives, and the baselines showed it immediately.

---

## Delivery state

| | |
|---|---|
| Branch | `feat/evidence-observation-binding-v1` |
| Off | `a658af2bbacc9f3d34daee5829498be342b87a54` |
| Commits | 2 — `c22dfb3` (audit and robustness), `1a07287` (binding) |
| `main` | **untouched** |
| Merge | **not done**, and not to be done without review |
| Deployment | **none** |
| Leak check | passed: no key, no machine path, no third-party name, no private correspondence |

### What remains open, and is outside this mission

- The five-minute demonstration was not **re-timed** in this mission:
  `demo_binding.sh` is added without replacing it.
- The evidence package announced by a pilot was **not supplied**, so nothing in
  it was verified. None of its results was reconstituted.
- SEILX log preservation remains **not executed**: the scripts exist, access
  was blocked, and the 10 November deadline stands.

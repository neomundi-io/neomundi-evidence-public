<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="MED_DEMO.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Demonstration B — MED, an independent medical experiment

**A measurement is not a medical validation of the answer.** Nothing in this
demonstration establishes that an answer is clinically correct. It establishes
what was asked, what answered, what was answered, and what was measured.

---

## The chain this demonstration shows

```
dataset item  →  AI answer  →  measurement  →  recorded trace  →  evidence file  →  verification
```

Each arrow is a record in an append-only, hash-chained ledger. The evidence file
copies those records **in their original bytes**.

| | |
|---|---|
| Archive | `NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip` |
| Schema | `neomundi.evidence.med-demo/1` — a **derived** artefact |
| Built by | [`tools/med_demo_build.py`](../tools/med_demo_build.py) |
| Source | the 7 frozen MED ledgers, read-only |
| Observations | 209 |
| Measurements | 208, all `measured`, version `3.3.1` |
| Verification | **10 PASS, 0 FAIL, 8 NOT TESTED** |

---

## The dataset, and why its content is not published

| | |
|---|---|
| Name | MedMCQA |
| Source | [`openlifescienceai/medmcqa`](https://huggingface.co/datasets/openlifescienceai/medmcqa) |
| Revision | `91c6572c454088bf71b679ad90aa8dffcd0d5868` |
| Licence tag | `apache-2.0` |
| Licensing section of the card | `[Needs More Information]` |
| Declared collection | *Historical Exam questions from official websites — AIIMS & NEET PG (1991-present)*, and *open websites and books* |
| Citation requested | Pal, Umapathi & Sankarasubbu, 2022 — *MedMCQA: A Large-scale Multi-Subject Multi-Choice Dataset for Medical domain Question Answering* |
| Selection | 300 rows read at the source; **202 kept** by a single-answer filter; 98 set aside as multiple-choice |

**The dataset content is not redistributed here.** The YAML tag announces
`apache-2.0` while the card's Licensing Information section was left as the empty
template, and the material comes from third-party examinations. That
contradiction is unresolved, and we do not resolve it by assuming the permissive
reading.

So: **no question text, no choices, no reference label.** What is published is
the **`item_id`** — the dataset's own identifier — so that an auditor resolves a
question **at the source**, from the publisher, and not from us.

The ledger never held the question text anyway: it keeps `prompt_sha256`, a hash.

---

## Providers and models actually used

Named, deliberately. An experiment whose subjects are hidden cannot be examined.

| Provider | Model requested | Model served | Attestation | Obs. | Measured |
|---|---|---|---|---|---|
| `anthropic` | `claude-sonnet-5-5` | `claude-sonnet-5-5` | `provider_attested` | 30 | 30 |
| `cohere` | `command-a-plus-05-2026` | **`null`** | `requested_only` | 30 | 30 |
| `deepseek` | `deepseek-flash` | **`null`** | `requested_only` | 30 | 30 |
| `google` | `gemini-2.5-flash` | `gemini-2.5-flash` | `provider_attested` | 30 | 30 |
| `infomaniak` | `swiss-ai/Apertus-v1.5-70B` | `swiss-ai/Apertus-v1.5-70B` | `provider_attested` | 30 | 30 |
| `moonshot` | `kimi-k3` | `kimi-k3` / **`null`** | 29 attested, 1 `requested_only` | 30 | **29** |
| `openai` | `gpt-6-astra` | `gpt-6-astra` | `provider_attested` | **29** | 29 |

**Three facts in that table are more interesting than the models.**

**Two providers did not attest which model served.** `cohere` and `deepseek`
return `model_served: null`. For those 60 observations, the requested model is
the only thing established — we do not know what actually answered. This is
recorded rather than smoothed over.

**One observation has no measurement.** On `moonshot`, one call exceeded 120
seconds before any response. Its observation exists with
`execution_status: error`, `response_text: null`, and `latency_ms: 0` — which is
a duration **not established**, not a duration of zero milliseconds.

**One attempt produced no observation at all.** `openai` has 29 observations for
30 attempts.

**No ranking is published, and none should be derived from this.** Different
providers served different models under different conditions; the campaigns are
separate series and do not aggregate.

---

## Signals measured

All five signals were valued on all 208 measurements, at `measurement_version`
`3.3.1`, and all 208 carry a production measurement identifier.

| Signal | Measured | `null` |
|---|---|---|
| `coherence_score` | 208 | 0 |
| `factual_hallucination_score` | 208 | 0 |
| `semantic_instability_score` | 208 | 0 |
| `semantic_risk` | 208 | 0 |
| `stability_score` | 208 | 0 |

**What these signals are not.** They describe properties of the text that was
produced. None of them is a clinical judgement, and none of them was validated
against medical ground truth. A high `coherence_score` on a wrong answer remains
a high `coherence_score` on a wrong answer.

---

## What was excluded from the archive, and why

**`reference_evaluations.jsonl` is excluded.** It carries the pair `status` +
`extracted_answer`: whenever an answer is `correct`, the extracted letter **is**
the dataset's reference label. Publishing that across 208 measurements would
reconstruct part of the MedMCQA labels, whose redistribution conditions are
unresolved.

**Consequence, stated plainly:** this archive does **not** let anyone say whether
an answer was correct in the dataset's sense. The correctness judgement exists —
it is in the ledger, and in the complete campaign archive, which stays private.

That is why this is a **derived** artefact under its own schema, rather than a
campaign export with a member quietly removed. Removing a member from an
attested archive would mean rewriting its manifest and checksums by hand, which
turns an attested archive into a retouched file.

---

## Verifying it yourself

```sh
python verify.py NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip
```

Result on 5 November 2026: **10 PASS, 0 FAIL, 8 NOT TESTED.**

The eight `NOT TESTED` are named with their reason. Five of them are the members
this archive does not carry — reference evaluations, replay provenance, a CSV, a
declared-absences section, an execution-regime section. The other three are the
chaining of the seven ledgers, the replayed-input hashes, and the archive's
origin.

> **The tamper-detection suite does not apply to this archive.** Its ten
> alterations assume a `rapport.md` member, an `observations.csv`, at least one
> `null` signal and a regime guard — none of which a derived MED archive has.
> Run it on [Demonstration A](DEMO.md) instead; it refuses to run here and says
> why.

### What this archive does not let you verify

- **the chaining of the seven ledgers.** The archive declares their head hashes;
  recomputing the chain is the instrument's job, not this verifier's.
- **the archive's origin or time.** No signature, no external anchoring.
- **whether an answer was medically correct.** Out of scope, by design.

---

## What is demonstrated, what is not, and what cannot be established

| | |
|---|---|
| **Demonstrated** | a real question item, a real model, a real recorded answer, five real measured signals, a chained trace, a derived evidence file, and an independent file-level verification |
| **Demonstrated** | that two providers did not attest their served model, and that this is visible rather than hidden |
| **Not measured** | the medical correctness of any answer |
| **Not published** | the question text, the choices, the reference labels, and the correctness verdicts |
| **Cannot be established** | the origin and the time of the archive; the chain's resistance to a complete rewrite |
| **Not reproducible** | the experiment itself. Real calls to seven external operators on 29–30 October 2026. An operator does not replay an answer: re-running would produce different answers, latencies and signals. **The freeze is the only record of what was observed.** |

---

## Where the figures come from

Every figure on this page is read from the frozen ledgers, which are the ones the
reference freeze records — see [Corpus reference](CORPUS_REFERENCE.md) for their
head hashes and the three-source concordance of their campaign identities.

The build tool reads them **read-only** and verifies, after writing, that the
source ledgers' hashes have not moved.

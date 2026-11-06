<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="CORPUS_REFERENCE.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Reference corpora — hashes and verification

This document declares the corpora NeoMundi Evidence V0.1 relies on, their
hashes, and how a third party verifies them.

**It contains no corpus data.** The archives live outside Git, on private
media, and are released only by explicit decision — see
[Obtaining the archives](#obtaining-the-archives).

> **The operators and models are named.** This is deliberate: MED is an
> independent experiment, and an experiment whose subjects are hidden cannot be
> examined. What is **not** published is the dataset content — see
> [MED demonstration](MED_DEMO.md).
>
> No result is presented as a ranking. A measurement describes properties of a
> produced text; it does not establish that an answer is medically correct.

Reference freeze: `20261105T1200_GEL_CORPUS_GATE0`, 5 November 2026.

---

## The two corpora

| | MED | GROUNDED-S1 |
|---|---|---|
| Execution regime | `live` — seven real operators | `synthetic` — no operator |
| Ledgers | 7 | 1 |
| Records | 844 | 151 |
| Observations | 209 | 30 |
| Measurements | 208, all `measured` | 30: 15 `measured`, 8 `degraded`, 7 `not_measured` |
| Reference evaluations | 208 | 30 |
| `measurement_version` | 3.3.1 | 3.3.1 |
| Production correlation | real `neomundi_measurement_id` | sentinels `33100000-…` |
| Publication | **derived archive published**; dataset content not redistributed | published |
| V0.1 use | **Demonstration B** — sector traceability | **Demonstration A** — controlled verifier behaviour |

---

## Hashes

### Freeze archives

```
98043a138a58ef764902718a2f07d2a3058108ce448cd19a042c7e9fda294559  GEL_MED_20261105.zip
754da1d21c67590b12a26ee524a58dec3c288b0c3a698c7186b60c99451aee49  GEL_GROUNDED-S1_20261105.zip
```

### Ledger head hashes

Recorded on 4 November 2026, re-verified on 5 November on the frozen copies —
identical to the character.

| Provider | Records | Head hash | Model requested | Attestation of served model |
|---|---|---|---|---|
| `anthropic` | 121 | `e2170cebf2fd16a94509f556152624e8ff0339644aae1f430c69133ac65588a2` | `claude-sonnet-5-5` | provider_attested |
| `cohere` | 121 | `4e26bf8e1cef4af398eb3b6ba5da9a49e88fee05234fd5a3986809c62d91514d` | `command-a-plus-05-2026` | requested_only |
| `deepseek` | 121 | `8c10d4fdd1ae3162ce08410d4d328d385d81dcc6c8067deead2c558347a1467d` | `deepseek-flash` | requested_only |
| `google` | 121 | `221e7b212640d820d8b220d94016a7a6a6240ca15284b8cb08feed3b97f66234` | `gemini-2.5-flash` | provider_attested |
| `infomaniak` | 121 | `1ca7027a40c538bbb5285303901c8f219319e57059ac9f6d4a75db507a3047bf` | `swiss-ai/Apertus-v1.5-70B` | provider_attested |
| `moonshot` | 121 | `d8f5138594eb5a19aa629eb70dc3f0045b2b30675add049cc8b389c988553ff8` | `kimi-k3` | provider_attested (29) / requested_only (1) |
| `openai` | 118 | `d6df67cccb2a8b54cce2d7bf2a3aba752d3ab1f44ba20f71b323178754a44d58` | `gpt-6-astra` | provider_attested |
| `GROUNDED-S1` | 151 | `fc1f2787e6e0e24fd70c9b6d252efe99dc9e2fe297233f289254c47a4c7d43b2` | `grounded-s1-2026-10-22` | synthetic — attests a replayed recording |

A `requested_only` attestation means the provider did **not** state which model
actually served the request. For those two campaigns, the requested model is the
only thing established.

### Campaign identities

Each `campaign_sha256` is consistent across **three** sources: declared by the
ledger, carried by the frozen definition, and **recomputed by us** from that
definition with the standard library alone. 8 of 8 — re-verified 6 November
2026, 10 of 10 counting two campaigns not published here.

> **"Recomputed by us" is not "independently reproducible", and an earlier
> edition of this page blurred the two.** It said *recomputed independently*,
> which reads as a guarantee a reviewer can exercise. Two things stand in the
> way, and both are ours: the recipe was **written down nowhere**, and the
> campaign definitions are **not reachable from the instrument's main branch**
> — see [Obtaining the archives](#obtaining-the-archives).
>
> This is not a theoretical gap. An external evaluation on 6 November held the
> frozen data, tried three plausible recipes on
> `grounded-med-synthetique-v1`, and concluded **"not established"** — it had
> removed one excluded field instead of two. A true claim that no one else can
> exercise is indistinguishable, from the outside, from a false one.
>
> The recipe is a formula over an object whose shape is already described here;
> it carries no key, no secret and no dataset content. **Publishing it is a
> pending decision** (ODA3 recommendation R-5). Until it is taken, treat every
> `campaign_sha256` below as **class C** in the table under
> [Verifying](#verifying): verifiable with the instrument, not without it.

| Campaign | `campaign_sha256` |
|---|---|
| `grounded-med-complet-defauts-anthropic-v1` | `b11ba303045aa464…` |
| `grounded-med-complet-defauts-cohere-v1` | `0665a3d42cd22609…` |
| `grounded-med-complet-defauts-deepseek-v1` | `2914c55c2f9af943…` |
| `grounded-med-complet-defauts-google-v1` | `012075b1248bb485…` |
| `grounded-med-complet-defauts-infomaniak-v1` | `73d4dbda0a9c20aa…` |
| `grounded-med-complet-defauts-moonshot-v1` | `e6e8decf5f543ff8…` |
| `grounded-med-complet-defauts-openai-v1` | `81e8b981b8a7de14…` |
| `grounded-med-synthetique-v1` | `7882f080d33bec30…` |

### Link from ledger to its inputs — GROUNDED-S1 only

```
bundle_sha256  d84722b4f4db3af939c456f3a535e484cabffbaabcbc69f684dc997fce05f7e1
```

The 30 `replay_provenance` records attest the hash of each of the 30 inputs.
**30 of 30 match** the frozen files, and `bundle_sha256` recomputes exactly —
with the standard library alone.

This link is what makes a synthetic corpus verifiable rather than merely copied:
no input can be substituted without the ledger contradicting it.

---

## Verifying

### Who can verify what — four classes of access

Every hash on this page belongs to exactly one class. The class, not the hash,
is what tells a reviewer whether they can exercise the claim themselves.

| | Class | Who can verify | Hashes in it |
|---|---|---|---|
| **A** | **The public repository alone** | anyone, stdlib only | the V1 demonstration dossier's digests; the CI fixture, which is byte-deterministic |
| **B** | **The freeze archive, stdlib only** | a reviewer granted access | the two freeze-archive hashes; the 30 `recording_sha256`; `bundle_sha256` |
| **C** | **The instrument** | us, today | JCS chaining; `record_sha256`; **and `campaign_sha256`, until its recipe is published** |
| **D** | **Nobody, by nature** | — | ledger head hashes — `recorded_at` is read from a clock, so a re-execution never reproduces them; MED, whose calls were live |

**Class C is the one to watch.** A hash in class C is not weaker
cryptographically — it is weaker *evidentially*, because its verification
rests on the party that produced it. Moving a hash from C to B is always an
act of documentation, never of cryptography.

**Class D is not a defect.** A head hash that depended on nothing would not be
a chain. Confusing D with a failure is the symmetric error to confusing C
with B.

### With nothing installed

```sh
sha256sum -c GEL_GROUNDED-S1_20261105.zip.sha256    # before opening the archive
unzip GEL_GROUNDED-S1_20261105.zip -d freeze/
python freeze/verifier_gel.py freeze/
```

The freeze verifier has no dependency and emits no network call. It returns
`PASS`, `FAIL` or `NOT TESTED` per check. On 5 November 2026, on the complete
freeze: **12 PASS, 0 FAIL, 3 NOT TESTED.**

The three `NOT TESTED` are deliberate:

| Check | Why not tested here |
|---|---|
| JCS chaining of MED (7 ledgers) | recomputing it would be a second implementation of the ledger |
| JCS chaining of GROUNDED-S1 | same |
| input-recording hashes — MED | `live` corpus: no `replay_provenance` to verify |

### Chaining, with the instrument

Chaining is verified with the instrument that wrote it, on the original ledger.
On 5 November 2026, on the frozen copies: **8 chains of 8 valid, 0 anomaly.**

---

## What these hashes do not prove

- **Neither origin nor time.** The chaining has no external anchoring, and
  `recorded_at` is supplied by the caller. The ledger attests what it was told.
- **Not integrity against a complete rewrite.** An entirely rewritten chain
  verifies perfectly. Only a hash kept elsewhere — such as those in this
  document — allows it to be detected.
- **Not the correctness of the signals.** The existence of a score does not
  establish its validity.

---

## Computational reproducibility — not to be confused with the freeze

The freeze says *these bytes have not changed*. Reproducibility says *they can
be remade*. Both are established separately, and they do not give the same
result.

| Corpus | Verdict |
|---|---|
| MED | **NOT REPRODUCIBLE.** Real calls to seven external operators on 29–30 October 2026. An operator does not replay an answer. |
| GROUNDED-S1 | **PARTIAL.** 55 of 62 inputs reproduce byte for byte. |

### The 7 divergences of GROUNDED-S1

The divergent files are ranks 3, 7, 11, 15, 19, 23, 27 — that is,
`rank % 4 == 3`, the `not_measured` archetype. That archetype was corrected on
**24 October 2026**, two days after the corpus was produced, by a dated change
in the private instrument repository.

The divergence is therefore **explained and attributable**. It is not a sign of
alteration. Both versions of the archetype are preserved in the freeze.

Two points that matter for any reproducibility claim:

1. **The generator script did not exist at the attested revision** — it was
   committed a few minutes after the corpus was produced. The freeze is
   therefore the only authoritative record of those 62 inputs.
2. **Reproducing a ledger byte for byte is impossible**, even for a synthetic
   corpus: `recorded_at` is read from the clock, and the chaining hashes depend
   on it. "Reproducible" means *same inputs, same observation and measurement
   content, valid chain*. Never *same head hash*.

---

## Obtaining the archives

There is no self-service access.

- **GROUNDED-S1** — release to an external reviewer is possible after an
  explicit decision by the corpus owner. The hash is transmitted through a
  **separate channel** from the archive: whoever can replace the archive can
  replace the checksum that travels with it.
- **MED** — the **derived demonstration archive is published**: it carries the
  observations and the measurements, and names the operators and models. The
  **complete campaign archive stays private**, because it carries the reference
  evaluations, whose publication would reconstruct dataset labels. The dataset's
  own content is never redistributed — see [MED demonstration](MED_DEMO.md).

---

## Computation context

| | MED | GROUNDED-S1 |
|---|---|---|
| Attested `code_commit` | `e4ffda6b5bfcc105efbf0c764ca7d61e5e263220` | `a52715d39383c71d2fbded47cf65ebeadc381317` |
| Produced on | 2026-10-29, 11:38–12:02 UTC | 2026-10-22T02:09:54Z |
| Dataset | a public multiple-choice medical dataset, 202 items | same, through the frozen panel |
| Schemas | 15 sealed JSON schemas, in the freeze | same |

The two `code_commit` values are published because they are **inside the frozen
records themselves**: they are part of the evidence an auditor reads, not an
internal reference. They designate revisions of a private repository and cannot
be resolved without access to it.

> The MED campaign definitions are **not on the instrument's main branch**. They
> are pinned by a dated tag in the private repository and are included in the
> freeze for that reason: an auditor starting from the main branch could not
> recompute the `campaign_sha256` values.

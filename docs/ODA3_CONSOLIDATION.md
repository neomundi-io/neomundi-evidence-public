<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="ODA3_CONSOLIDATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# ODA3 consolidation — what changed, and what did not

**6 November 2026.** Answers the external evaluation conducted for
**Mukesh Kumar Singh (ODA3 Institute)**, whose question was the right one:

> What is the difference between keeping a verifiable record of an AI
> execution and establishing that this record is probative enough to support
> a specific assurance claim?

The evaluation produced nine recommendations. **Eight are treated here. One
is deliberately left out**, and the reason matters more than the work.

---

## The finding that reorganised the work

The evaluation removed one observation from all five of its members in a real
archive, then redid the counts and the checksums.

`verify.py` returned **19 PASS, 0 FAIL**.

An internally perfect archive had exported only part of its ledger, and
nothing said so. Measured on the real export: **151 records of 6 types in
the ledger, 120 of 4 types in the archive** — with a manifest announcing
151. The 31 withheld records (30 `runner_attempt`, one `run`) were named
nowhere.

That is the whole difference between integrity and probative sufficiency,
and it is now a control line.

---

## What was done, recommendation by recommendation

| | What was asked | What was done |
|---|---|---|
| **R-1** | name the record types excluded from the export | the completeness contract: `types_exclus` with its counts, in the manifest, checked |
| **R-2** | a control confronting the ledger total to the sum of counts | the same control, three states: `PASS` / `FAIL` / `NOT TESTED` |
| **R-3** | reconcile the public dossier with a real archive, or write its divergences | a **versioned profile**: `v2` corrects five of six divergences, the sixth is declared |
| **R-4** | signal a `stamped_at_declared` later than its anchoring block | the two values are now named side by side, with the relation that must hold |
| **R-5** | document the recipe for `campaign_sha256` | the claim was corrected, and a **four-class access table** added. Recipe publication is a pending decision |
| **R-6** | record the evaluator's provenance in `measurements.jsonl` | **not done** — structural, and the subject of a separate analysis |
| **R-7** | rename `config_snapshot_sha256` or document it | documented, at the mapping and in [`BINDING.md`](BINDING.md). **Not renamed** |
| **R-8** | fix the `['True']` rendering | fixed, in both languages |

---

## R-5 — the most instructive of the eight

The published corpus reference said each `campaign_sha256` was
*"recomputed independently. 8 of 8."*

The evaluation held the frozen data, tried three plausible recipes on
`grounded-med-synthetique-v1`, and concluded **"not established"**.

Both statements were true, and that is the point. **Verified on 6 November:
the recipe recomputes 10 of 10 campaigns**, including the exact digest the
evaluation could not reproduce. It had excluded one field where the recipe
excludes two.

So nothing was wrong with the hash. What was wrong was the **claim**:
*"recomputed independently"* reads as a guarantee a reviewer can exercise,
and the recipe was written down nowhere. **A true claim that no one else can
exercise is indistinguishable, from the outside, from a false one.**

The fix is a four-class table in
[`CORPUS_REFERENCE.md`](CORPUS_REFERENCE.md#verifying): who can verify what,
with what access. Class C — *verifiable with the instrument, not without it*
— is where `campaign_sha256` sits until the recipe is published. **Moving a
hash from C to B is always an act of documentation, never of cryptography.**

---

## R-3 — why a profile, and not a correction

The V1 review dossier is **byte-identical** to the CI fixture, and that
digest is carried by three signed pieces: the Ed25519 attestation, the
OpenTimestamps proof anchored in Bitcoin blocks 974714/974715, and the
binding manifest.

Correcting the generator in place would have **silently invalidated a signed
and timestamped evidence chain**. So the generator is versioned instead:

```sh
python tests/make_fixture.py <dir>              # v2, the faithful profile
python tests/make_fixture.py <dir> --profile v1 # the historical archive, byte for byte
```

Case 1 of [`tests/test_completude.py`](../tests/test_completude.py) is the
guard: it fails if `v1` ever stops reproducing `e31e12bb…`. Nothing else in
the repository would notice.

| Divergence | Treatment |
|---|---|
| measurements not chained | **corrected** — all four members chained in one ledger |
| no cause on an incomplete measurement | **corrected** — `reason` carries the cause **per signal** |
| `sequence` restarting per member | **corrected** — monotonic across the ledger |
| `registre.enregistrements` = 4 for 16 delivered | **corrected** — the source total, with the export counted separately |
| `record_sha256` recipe without `sequence` | **narrowed and declared** — same field set as the instrument, canonicalisation is `json.dumps(sort_keys)` and says so |
| `code_commit` / `config_snapshot_sha256` as filler | **kept, and declared** — a synthetic object must carry visible filler, not a plausible-looking value |

The sixth is the one that stays. Implementing RFC 8785 here would be the
**second ledger implementation this product refuses to build** — two
implementations that diverge prove nothing, and the one that wrote the
ledger is not this one. `v2` therefore matches the field set and declares
that the canonicalisation coincides only on this fixture's value domain.

### And v2 withholds records on purpose

The source ledger now carries **six** record types and the export delivers
**four** — a `run` and four `runner_attempt` are written into the chain and
withheld. Without that, R-1 and R-2 would not be **exercisable**: one cannot
test a completeness control on a complete object.

The withheld records participate in the chain. That is the heart of it:
**a valid chain says nothing about the completeness of an export.**

---

## The new guarantee, and its exact limits

One control line, `completeness of the export`. What it establishes:

- the archive **names** what its ledger held, what it exported, and what it
  withheld, with counts;
- those three numbers **add up**;
- the exported count matches the sum of the members' counts.

What it does **not** establish, and must never be read as:

- **that the withholding was legitimate.** The control reads a declaration.
  An archive can declare withholding 30 records and be lying about why.
- **that nothing else is missing.** It checks the arithmetic of a
  declaration, not the ledger, which it does not have.
- **completeness, for any archive that does not declare the contract.** That
  case is `NOT TESTED` — not `PASS`.

The `NOT TESTED` is **not** marked required. In this codebase `required`
means *"this NOT TESTED would be avoidable if the caller supplied what is
missing"*. Here the caller can do nothing: the **producer** must declare the
contract. Marking it required would make every historical archive exit 2 in
strict mode, for a gap its holder did not create.

---

## Consequences for historical archives

**No historical evidence was modified.** Three distinct treatments:

| | |
|---|---|
| The V1 dossier, its attestation, its proof | **untouched.** `v1` reproduces it byte for byte |
| Figures we re-measured | rewritten: the auditor's guide, CI, the generator's descriptor, the attestation suite's expectation |
| Figures we **cannot** re-measure | annotated, not rewritten. GROUNDED-S1 and MED are not in this repository; their new count is *derivable* — one more line — but **derivable is not measured**, and this product exists to hold that distinction |
| Dated observations | **left alone.** The two 5 November audit reports, the consolidation report and the attestation matrix record measurements taken at a date. Rewriting them would falsify a record |

An archive that predates the contract now shows **one more `NOT TESTED`**.
That is the honest consequence of adding a guarantee: the count did not get
worse, the reporting got more complete.

---

## What remains open

| | |
|---|---|
| **R-6** | structural. Recording the evaluator's provenance in `measurements.jsonl` affects the instrument, the consumers, **and the frozen archives** — it would move comparability boundaries. Analysis first, no code |
| **R-5, second half** | publishing the recipe. A formula over an object whose shape is already described, carrying no key and no dataset content — but the decision is not ours to take alone |
| **R-9 / B-1** | the signer's legal identity. Nothing technical replaces it |
| The sixth divergence | `record_sha256` canonicalisation. Declared, not closed |
| Per-signal cause, as a **control** | `v2` carries the causes; nothing yet verifies that an unmeasured signal names one |
| The prompt text, and the five evaluators' identity | the evaluation found them absent from the data examined. R-6 covers the second; the first is a measurement decision, not an Evidence one |

---

## The architectural distinction this work protects

**From AI Behavior to Auditable Evidence** — Measurement → Station →
Evidence.

Evidence produces verifiable evidence whose guarantees **and limits** are
explicit. It does not certify, on its own, that an AI execution was correct
or compliant. Five things stay distinct, and the ODA3 evaluation is what
forced the fifth onto the page:

| | |
|---|---|
| **Integrity** | the bytes are the ones the record refers to |
| **Provenance** | who produced them, with what, and whether that is attested |
| **Completeness** | whether what is offered is all there was — **new as a control** |
| **Reconstruction** | whether the inputs can be reproduced, and whether the measurement can |
| **Probative sufficiency** | whether all of the above supports a *specific* claim — and this one is never established by a tool |

The evaluation's own verdict counts say it better than a summary could:
**27 claims supported, 8 unsupported, 3 undetermined, 6 split, 10 not
observable**. A product whose evaluation returns only green has not been
evaluated.

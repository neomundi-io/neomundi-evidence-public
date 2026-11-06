<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="V1_STATUS.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Evidence V1 tracking — status at 6 November 2026

Supersedes [`V1_CLOSURE_PLAN.md`](V1_CLOSURE_PLAN.md), which stays a **dated
record** of the morning of 6 November and is not rewritten: rewriting a dated
observation would falsify a record.

---

## The eight conditions

| | Condition | Status | What remains |
|---|---|---|---|
| **B-1** | Legal identity of the signer | 🟢 **RESOLVED** | — direction decision of 6 Nov: NeoMundi Recherche, RNA W563015824, capacity `experimental`. Implemented and tested |
| **B-2** | A production key, and its custody | 🟢 **decisions and tooling** · ⏳ **the step** | the three decisions are taken, the tooling is built and exercised. **The key is not generated**: an offline step, on the operator workstation |
| **B-3** | Exercise the chain on a real package | 🟢 **RESOLVED**, limit named | the limit is the operational link below, not a verification defect |
| **C-4** | A confirmed timestamp proof | 🟢 **RESOLVED** | — Bitcoin blocks 974714/974715, proof committed, verifiable offline |
| **C-5** | Publish the store on a second channel | 🟠 **PARTIAL** | the barrier is built and tested. What is missing is **a production store to audit** — therefore B-2 |
| **C-6** | Translate the verifiers' output | 🟢 **RESOLVED** | — and PR #12 closed a hole the suite could not see: 44 strings in `sign.py` |
| **D-7** | Receive the complete CP8 package | 🟠 **PARTIAL** | two artefacts, awaited from Dennis. Not in our hands |
| **D-8** | Third-party anchoring and its cost | 🟢 **RESOLVED** | — ADR-001 accepted |

**Six resolved, two partial, none blocked.** On the morning of 6 November:
three resolved, four partial, one blocked.

## The nine ODA3 recommendations

| | | |
|---|---|---|
| **R-1** · **R-2** | excluded types, and the control confronting them | 🟢 — with its measured ceiling: catches an *inconsistent* amputation, not a thorough forger |
| **R-3** | reconcile the public dossier | 🟢 — `v2` profile, 5 of 6 divergences corrected, the 6th declared |
| **R-4** | `stamped_at_declared` against the block | 🟢 |
| **R-5** | document the `campaign_sha256` recipe | 🟠 — the claim is corrected; **publishing the recipe** remains a decision |
| **R-6** | evaluator provenance | 🟠 — contract `station.export.campagne/3` **proposed**, nothing implemented. Change point: Station |
| **R-7** · **R-8** | `config_snapshot_sha256`, `['True']` rendering | 🟢 |
| **R-9** | identity of the signer | 🟢 — it is B-1 |

---

## The experimental chain Measurement → Station → Evidence

| Stage | What exists | What is missing |
|---|---|---|
| **Measurement** | the API emits 12 provenance fields per signal, `evaluator` populated 5/5 on 7/7 | nothing, at this link |
| **Station** | the ledger chains the records; the export produces an archive | **provenance is lost at the ledger write** — 0 fields across 238 measurements. That is R-6 |
| **Evidence** | 22 control lines, Ed25519 attestation, Bitcoin anchoring, completeness, declared capacity | the production key, and publication of the store |

**Two links of three hold.** The Station gap is R-6: analysed, not started.

### And the operational link B-3 revealed

This is the most important point of this tracking note, and it is **not** a
verification defect.

Evidence consumes **exported** packages. On the real 22-file package received
on 30 October, all 21 declared digests were recomputed and agree — but
`verify.py` refused, for want of an Evidence manifest, and that refusal is
**correct**.

**Nothing converts a raw collection into an Evidence package.** The pilot
onboarding path does not exist. Until it does, "end to end" stops the moment
a third party hands us their files.

That is the link to build for operations, and it belongs to the existing
tooling — not to a new architectural track.

---

## Next steps

In order, opening nothing new.

| | | Who |
|---|---|---|
| 1 | **generate the production key** — offline, operator workstation, network disconnected, per B-2 §Activation | an operator, not an agent |
| 2 | store to `store_kind: production`, then `publish_store.py audit` on the **real** store | engineering |
| 3 | **C-5**: publish the digest and `store_version` on the second channel, after a human reads the audit's `NOT TESTED` lines | decision, then engineering |
| 4 | **the onboarding link**: convert a raw collection into an Evidence package, so B-3 closes operationally and not only in verification | engineering |
| 5 | **R-6**: decide whether Station's ledger write keeps the API's provenance. Three distinct decisions, none taken | Station coordination |
| 6 | **D-7**: two artefacts awaited from Dennis | not in our hands |
| 7 | **R-5, second half**: publish the `campaign_sha256` recipe or not | an isolated decision, no prerequisite |

Steps 1 and 3 are **irreversible**. Neither is taken.

---

## What is not declared

**Evidence V1 is not probatively closed.** Two of the three pillars of a
probative claim moved today: *who attests* went from a test key to a named
entity with `experimental` capacity — a real advance, and a single link.
*Which instrument measured* remains `not_demonstrable`.

And the sentence that must never slip: **an experimental attestation is not a
legal certification.** The verifier prints it, in both languages, on every
run, and [`tests/test_capacite.py`](../tests/test_capacite.py) fails if it
ever stops.

What is demonstrated, and what is not, is set out in
[`EXPERIMENTAL_CHAIN.md`](EXPERIMENTAL_CHAIN.md).

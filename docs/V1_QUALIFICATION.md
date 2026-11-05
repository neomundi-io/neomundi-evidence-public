<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="V1_QUALIFICATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# V1 qualification — the eight conditions, and two verdicts

**6 November 2026.** Closing the qualification sprint opened against the
eight conditions of [`V1_CANDIDATE.md`](V1_CANDIDATE.md), before the
external review of **Monday 9 November**.

> **Governing principle: no RESOLVED of convenience.** A condition is lifted
> only by a result actually observed. Three of the eight are resolved, four
> are partial, one is blocked — and the blockage is not technical.

---

## The matrix

| | Condition | Initial state | Exact criterion for resolution | What was done | Owner | Evidence | Final state |
|---|---|---|---|---|---|---|---|
| **B-1** | Settle the signer's legal identity | `legal_capacity_to_attest: "unverified"`, reported on every run | the entity is **named** with its registration, the **authorised representative** is recorded and their power **checked against the statutes**, and a **dated human decision** exists | [`SIGNING_POLICY.md`](SIGNING_POLICY.md) Part A: the five roles separated, the three candidate entities with what each would mean, the GitHub organisation **excluded** as not a legal person, and the three-part gate | **Sébastien** — legal, not technical | the policy; the field still reads `unverified` | 🔴 **BLOCKED** — awaiting a decision no code can take |
| **B-2** | A production key, and its custody | no production key; everything signed with destroyed ephemeral test keys | a written procedure covering generation, custody, backup, rotation, revocation and traceability — **and** B-1 settled, since a key is held in the name of an entity | [`SIGNING_POLICY.md`](SIGNING_POLICY.md) Part B: `kid` convention never reused, `rotated`/`compromised` asymmetry and its retroactivity, "never revoke dry", and three gaps named | Sébastien, then an operator | the procedure; **no key generated** | 🟠 **PARTIAL** — procedure written, waits on B-1 |
| **B-3** | Exercise the chain on one real package | no function ever exercised on a real package | at least one function exercised on a package **produced by a third party**, with the result stated as observed | a real package of 22 files, received 30 October, examined 6 November: **21 declared digests recomputed, 21 concordant**. `verify.py` refuses (no Evidence manifest) with a motivated verdict. `sign.py` refuses — **and the refusal is correct**. One real defect found and fixed; one robustness defect found and fixed | principal engineer | the sweep; `tests/test_bom.py` 11/11; `tests/test_reconciliation.py` 27/27 | 🟢 **RESOLVED** — with a named limit, below |
| **C-4** | Obtain a confirmed timestamp proof | 4 `PENDING` attestations, 0 Bitcoin; no date attested | at least one **Bitcoin** attestation present in a proof's own bytes, bound to its subject, with the original intact | `upgrade` run on the proof submitted 5 November 21:52Z: **blocks 974714 and 974715**. `verify` returns `5 PASS, 0 FAIL, 2 NOT TESTED`; `--strict` exits **0**, where the still-pending V1 proof exits **2** | principal engineer | `examples/timestamp/…jws.confirmed.ots`, committed; `tests/test_timestamp.py` 25/25, cases 26–29 | 🟢 **RESOLVED** |
| **C-5** | Publish the trust store on a second channel | store and package come from the **same source** | the store's digest published on an independent channel, **after** a content audit signed off by the representative of B-1 | [`TRUST_STORE_PUBLICATION.md`](TRUST_STORE_PUBLICATION.md): the two-channel design, the authenticity path, what it still does not establish, and a seven-point content audit. One prerequisite found: `store_version` is genuinely missing — `changes` exists but is a record, not a comparable version, **and no code reads it** | Sébastien (sign-off), then engineering | the design; **nothing published** | 🟠 **PARTIAL** — not closeable before B-1 |
| **C-6** | Translate the verifiers' output | French only | an auditor reaches a verdict in English, with **identical** states, order, exit codes, field names and digests | `--lang en` on `verify.py` and `verify_attestation.py`. Coverage **measured**: `tests/test_i18n.py` fails on any untranslated French prose, across a valid archive **and seven failure regimes** | principal engineer | `tests/test_i18n.py` 21/21, in CI; [`I18N.md`](I18N.md) | 🟠 **PARTIAL** — 2 tools of 6, the two an auditor runs |
| **D-7** | Receive the complete CP8 package | recorded as "not transmitted" | the package inventoried by class, and an **exact** list of what to request | the package **had arrived** on 5 November — the previous sheet was wrong, and that is the only statement of this sprint found false. Inventory held privately: 5 objects received, **1 independent recomputation succeeded** (`receipt_hash` MATCHED), **11 digests cited with no referent**, **0 signatures verified on either side** | principal engineer; then Dennis | the private inventory; six requests ranked | 🟠 **PARTIAL** — closes on the first two requests |
| **D-8** | Decide on third-party anchoring and its cost | undecided | an ADR separating the four time claims, with a minimal V1 policy and the operational cost stated | [`ADR-001-ANCHORING.md`](ADR-001-ANCHORING.md), **ACCEPTED**: the four claims, why a declared date is worth nothing, why a block height is not a date, the V1 policy, and four rejected alternatives | principal engineer | the ADR; the two proofs in the repository demonstrate both ends | 🟢 **RESOLVED** |

**Three resolved, four partial, one blocked.**

---

## The dependency that decides the rest

B-1 is not one condition among eight. It gates three.

```
B-1  legal identity  ──┬──>  B-2  a key is held in the name of an entity
     (not technical)   └──>  C-5  the content audit needs a representative
                              to sign it off
```

B-2's procedure is written and C-5's design is drawn; neither can close
without a decision that belongs to Sébastien and to the entity, not to this
repository. **Writing more code moves neither.**

---

## What was found that nobody was looking for

Four things, all from real material rather than from fixtures. They are the
substance of this sprint.

### 1. A real defect in the reconciliation adapter — the first found by a real package

The CP8 receipt carries **six duplicated labels**: "Verifier A" names both
the vulnerable and the patched fixture. `compare_un_champ` took the first
match, **silently** — producing a possibly wrong reconciliation report with
no sign of it. A mapping may now target a `receipt_source_path`, which is a
real key; without one, an ambiguous label is **refused**.

**`receipt_label` is not a key on a real receipt.** No fixture would ever
have shown that: we wrote the fixtures.

### 2. Fifteen of twenty-two real files carry a UTF-8 BOM

Because the collector is a PowerShell script. Three of our entry points broke
on it — and the worst was `receipt_import`, which **refused a perfectly
valid JSON receipt as "unreadable"**. A partner exporting on Windows would
have had their receipt rejected, with a message blaming their file.

And the trap in the fix: the BOM is stripped **for parsing only**. Stripping
the bytes upstream would have looked cleaner and falsified the digest of
every file received.

### 3. A digest with no recoverable referent

The CP8 package's own reasoning rests on a signed audit trail it treats as
canonical. Its digest is confirmed to be in our integrity registry, with
issuer and issuance time — and our own verify page states that **document
content is never retained**.

So the digest attests **existence and issuance, not content**. The value
`g_score = 0.3863` therefore sits at `declared`, not
`reference_verifiable`, despite a digest and a URL that both answer. That is
exactly the distinction this product exists to draw, applied to our own
registry.

### 4. `sign.py` refusing a real archive is correct behaviour

The signed subject reads `observation_count` from an Evidence manifest. Over
a foreign archive it would sign `"0"` across seven observations — **a false
signed statement**. Better to refuse.

But that refusal reveals the real gap, below.

---

## The gap B-3 revealed, and did not close

Evidence consumes packages **exported** by NeoMundi. A real collection of
raw API responses is not one, and **no component in this repository converts
one into the other.**

That is the missing link between "a real package exists" and "Evidence
qualifies it" — which is to say, between a demonstration and a pilot. It is
named, not filled: filling it would be a feature, and this sprint was not
for features.

**Consequence for an offer: the pilot onboarding path does not exist yet.**

---

## Verdict 1 — external demonstration of Monday 9 November

# 🟢 GO

The demonstration rests on what is in the repository and verifiable by a
reviewer alone.

| What is demonstrable on Monday | Evidence |
|---|---|
| Package integrity, 21 controls, three never-merged states | `19 PASS, 0 FAIL, 2 NOT TESTED` |
| Autonomous verification, offline, **no dependency**, and a single file is enough | case 10 of the i18n suite |
| Ed25519 attestation, level `cryptographically_attested` reached | 10 PASS, 4 NOT TESTED |
| **A genuinely Bitcoin-confirmed timestamp proof**, blocks 974714 / 974715 | `5 PASS, 0 FAIL, 2 NOT TESTED` |
| The `PENDING` → confirmed lifecycle, **visible at both ends** | two proofs side by side; `--strict` gives 2 and 0 |
| An English-speaking auditor reaches a verdict | `--lang en`, coverage measured |
| Reconciliation refuses an ambiguous label rather than guessing | cases 19b–19d |
| **A real third-party package, with 21 digests recomputed** | and two refusals that are correct |

Ten suites green: verify 19/0/2 · falsification 10/10 · adversarial 13
detected, 2 limits · attestation 22/22 · binding 0 problems · timestamping
25/25 · reconciliation 27/27 · BOM 11/11 · FR/EN 21/21 · no-CRLF 0 problems.

**What must be said out loud at the start of the demonstration**, in these
terms:

- the demonstration package is **synthetic**; the signing key was an
  **ephemeral demonstration key, destroyed**;
- the confirmed proof is **real**, and what it establishes is an **upper
  bound** on time, not a date we verify;
- the signer's **legal capacity is not verified**, and the verifier says so
  on every run;
- `timestamp.py`, `bind.py` and `reconcile.py` **still print French**.

---

## Verdict 2 — qualification on a real client package

# 🔴 NO-GO

Not because the chain failed on a real package, but because of what the real
package showed.

| Blocker | Why it blocks |
|---|---|
| **No onboarding path** | Evidence consumes an *exported* package. A client arrives with raw responses, and nothing converts them. Without it, no client package can enter the chain at all. |
| **B-1 not settled** | a production attestation would be issued in the name of an entity that has not decided to commit. Every package signed would carry the defect forward. |
| **No production key, no custody** | B-2 waits on B-1. Everything signed stays a demonstration. |
| **Eleven digests cited with no referent, on the one real partner package** | reconciliation cannot be exercised on it: there is no digest in common with any Evidence archive, and the refusal is correct |

### What would turn this into a GO

In order, and only the first is ours alone to do:

1. **An import path** — from a real collection to an Evidence package. The
   only purely technical item on this list, and the one that unblocks
   everything downstream.
2. **B-1** — the legal identity decision. Not technical, and it gates B-2
   and C-5.
3. **The first two CP8 requests** — the signed audit trail, and the packet
   with its `manifest.sha256`. Then reconciliation can be exercised on the
   object it was designed for.

**Nothing on that list is code we were asked to write this sprint.** Which
is the honest conclusion of a qualification sprint: what remains is not
engineering effort, it is three decisions and one feature.

---

## Merge order

| | Commit | Content |
|---|---|---|
| 1 | `939fb4d` | C-4 — the confirmed proof; the ambiguous-label defect |
| 2 | `8e559c9` | B-3 — the real package; the BOM defect |
| 3 | `2671636` | B-1, B-2, C-5, D-8 — the four policy documents |
| 4 | `38fd68e` | C-6 — bilingual output |
| 5 | this document, and the product sheet's correction |

One branch, `feat/evidence-v1-qualification`, off `main` = `e8d8f64`. CI runs
the ten suites on Python 3.11, 3.12 and 3.13. **No deployment, and no merge
without validation.**

### What is NOT in this repository

The CP8 completeness inventory (**D-7**) is held privately: it names private
artifacts, and the package was supplied for private analysis. Nothing from
it — no file, no digest — is in the public repository.

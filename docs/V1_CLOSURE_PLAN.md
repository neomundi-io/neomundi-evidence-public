<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="V1_CLOSURE_PLAN.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Closure plan — the five remaining conditions

> **Dated record of the morning of 6 November 2026.** Current status is in
> [`V1_STATUS.md`](V1_STATUS.md): B-1 is since **resolved**, B-2 has its three
> decisions. This document is not rewritten — rewriting a dated observation
> would falsify a record.

**6 November 2026.** Follows
[`V1_QUALIFICATION.md`](V1_QUALIFICATION.md), which reported three
conditions resolved, four partial, one blocked. Perimeter:
**experimental, scientific, non-commercial.**

---

## Where the five stand now

| | Condition | Was | Is now | What closes it |
|---|---|---|---|---|
| **C-6** | Translate the verifiers' output | 🟠 2 tools of 6 | 🟢 **RESOLVED** | — done: 7 tools, coverage measured on 13 scenarios |
| **C-5** | Publish the trust store on a second channel | 🟠 design only | 🟠 **PARTIAL** — both prerequisites **built** | a content audit, signed off by B-1's representative |
| **B-1** | Settle the signer's legal identity | 🔴 blocked | 🔴 **BLOCKED** — but now **approvable** | three signatures on a decision sheet |
| **B-2** | A production key, and its custody | 🟠 procedure written | 🟠 **PARTIAL** — custody proposed, procedure ordered | acceptance of the custody, then B-1 |
| **D-7** | Receive the complete CP8 package | 🟠 inventoried | 🟠 **PARTIAL** — two pieces identified, request drafted | Dennis sending two artifacts |

**One resolved this session. Three now wait on a human act, not on code.**

---

## What changed, and why it matters

### C-6 is closed

All seven tools take `--lang {fr,en}`. 147 call sites were converted
mechanically — `print(` → `dis(` — after verifying that the text count
equals the AST call count in every file, so no occurrence lived in a
comment.

Coverage is **measured**, not declared: the suite exercises the tools across
13 scenarios and fails on any untranslated French prose, or any divergence
in exit code between the two languages.

One rule had to be written down to get there: **a string appearing verbatim
in an input file is data, not prose.** `reconcile.py` prints the partner's
labels and the correspondence table's free text; translating those would
stop the report from naming what the partner wrote. Case 23 checks it in the
other direction — it requires that such a string exist and come out
unchanged, so "it's data" cannot excuse anything.

### C-5's two prerequisites are built

Both were named as blocking in its own design, and both are done:

- **`store_version`** — a monotonic integer, now required. The schema had a
  `changes` array, but that is a record, not a comparable version, and **no
  code read it**. Without an orderable version, two auditors with different
  stores cannot tell which is newer.
- **`--store-digest`** — compares the store's bytes against a digest
  obtained through another channel. Three states, and the default is the
  honest one: concordant → `PASS`, divergent → `FAIL`, absent →
  `NOT TESTED`. An uncompared store is not false; it is uncompared.

**Nothing is published.** What remains is the content audit — seven points,
including a re-reading of every `notes` field, which is where internal
context leaks — and it needs someone with authority to sign it off. That
someone is B-1's D-2.

### B-1 is still blocked, but for a different reason than yesterday

Yesterday it was blocked because the decision had not been taken. Today it
is blocked because **the decision sheet has not been signed** — which is a
much shorter distance.

[`B1_EXPERIMENTAL_SIGNING_DECISION.md`](B1_EXPERIMENTAL_SIGNING_DECISION.md)
puts one proposal on the table rather than three options: **NeoMundi
Recherche**, the French association, RNA W563015824 — the only one of the
three entities whose object covers the act, now that the perimeter is
explicitly non-commercial. Three blanks to fill: the entity, the authorised
representative's **role**, the operator's **role**.

It also proposes a fourth value for `legal_capacity_to_attest`:
**`experimental`**. `unverified` would understate a decision actually
taken; `verified` would overstate a check nobody performed against the
statutes. The schema change waits for the approval — **a value nobody
authorised would be an invitation to use it.**

### B-2 has answers where it had blanks

[`B2_KEY_CUSTODY_AND_ACTIVATION.md`](B2_KEY_CUSTODY_AND_ACTIVATION.md) fills
the five custody questions that were marked *to decide*, and orders the
activation into four steps where no step may be taken early.

The distinction from RGC is now argued rather than asserted, and the
decisive reason is verifiable in the code: RGC's `verify_jws` derives the
public key **from the private key**, so only the secret holder can verify an
RGC signature, and offline nothing works. An Evidence attestation must be
verifiable by an auditor who does not trust us and has no network. Reusing
RGC's key would make the attestation verifiable by us alone — the opposite
of its purpose.

**No key is generated**, and the document refuses to allow one before B-1 is
approved and the custody accepted.

### D-7's two pieces are named exactly

Not "the complete package" — two artifacts, with their digests, and the
reason each one matters:

1. **The signed audit trail file.** Its digest is in the private
   inventory, not here. Dennis's own reasoning treats this file as
   canonical, and **we cannot reproduce it**: our verify endpoint confirms
   the digest is in our registry, and states that document content is never
   retained. So the digest attests existence and issuance, **not content** —
   and `g_score = 0.3863` therefore sits at `declared`, not
   `reference_verifiable`, despite a digest and a URL that both answer.
2. **The execution packet with its `manifest.sha256`**, plus the findings
   files, the four run logs, and the CVE template. Eleven digests are cited
   today and **no referent is supplied**.

The drafted message also says which two things are **ours** to fix and not
his: the `0.3863` / `0.594` labelling collision, and the request-count
arithmetic. That is what makes it a request rather than a deflection.

---

## Order of execution

The dependency graph has not changed, but it is now shorter.

```
B-1 signed  ──>  schema: `experimental`  ──>  B-2 key generated
     │                                             │
     └──>  C-5 content audit signed off  <─────────┘
                      │
                      └──>  trust store published, store_kind: production

D-7  independent of all of the above; waits on Dennis
```

| # | Step | Owner | Blocks |
|---|---|---|---|
| 1 | Sign B-1's three blanks | **Sébastien** | everything below |
| 2 | Accept B-2's custody | **Sébastien** | step 4 |
| 3 | Send the CP8 request to Dennis | **Sébastien** | D-7 only — do this in parallel, it has latency |
| 4 | Add `experimental` to the schema, with its verifier line | engineering | step 5 |
| 5 | Generate the key, offline, under custody | operator | step 7 |
| 6 | The content audit's seven points | engineering, then Sébastien signs | step 8 |
| 7 | Open the register of signed packages | operator | first real attestation |
| 8 | Publish the store's digest on the `.org` | engineering | C-5 closed |

**Step 3 should go first in wall-clock terms**, because it is the only one
whose latency is outside our control.

Steps 4 to 8 are between a few hours and a day of work. **Nothing on this
list is hard.** What stood in the way was never engineering effort — it was
that no decision had been put in a form anyone could approve.

---

## What is still NOT closed by any of this

Stated so the plan is not read as more than it is.

- **The pilot onboarding path.** Evidence consumes packages *exported* by
  NeoMundi. A real collection of raw API responses is not one, and no
  component converts one into the other. This is the gap B-3 revealed and
  did not close, and it is unchanged. It remains the blocker for a client
  package — and in the non-commercial perimeter, it is no longer urgent.
- **A verified legal capacity.** `experimental` is honest, not complete. A
  commercial offer would need the Sàrl decision and a real check of powers.
- **A date verified by us.** The confirmed OpenTimestamps proof gives an
  **upper bound** on time, read as a block height. Converting it to an hour
  needs a block header, and we delegate that, by name, to `ots verify`.
- **The Markdown report of `reconcile.py`**, still French. A file artifact,
  not verifier output — named in [`I18N.md`](I18N.md).

---

## Verdict

### Merging PR #8 — 🟢 GO

Verified on a **clean checkout**, not on a working copy: `main` = `e8d8f64`,
head `3b28c06`, `MERGEABLE` / `CLEAN`, five CI checks green on Python 3.11,
3.12 and 3.13.

- The ten suites reproduce identically from a fresh clone.
- The auditor's five commands give the published figures.
- The Bitcoin-confirmed proof verifies offline from the clone: `5 PASS,
  0 FAIL, 2 NOT TESTED`, blocks 974714 / 974715, and `--strict` separates it
  from the still-pending proof with codes 0 and 2.
- Confidentiality: **116 tracked files swept byte by byte, ZIP archives
  opened and inspected — zero findings.** No CP8 artifact, no artifact of
  the real third-party package, no key material, no machine path, no
  personal data. `__pycache__` is gitignored and no `.pyc` is tracked.
- Scope: 30 files, docs, tests, tools and one committed proof pair. **No
  frozen corpus, no Station, no API.**

### Continuing on the experimental perimeter — 🟢 GO

Three conditions now wait on three signatures. The engineering that was in
the way is done, and what remains is bounded and ordered above.

### Qualification on a real client package — 🔴 NO-GO, unchanged

The onboarding path does not exist. Nothing in this session changed that,
and nothing in this session was meant to: a non-commercial perimeter does
not need it yet. **It must not be read as resolved because the other
conditions moved.**

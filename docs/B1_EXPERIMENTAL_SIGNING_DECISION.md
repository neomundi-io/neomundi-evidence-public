<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="B1_EXPERIMENTAL_SIGNING_DECISION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# B-1 — Experimental signing policy, for approval

**6 November 2026.** Condition **B-1**. Companion to
[`SIGNING_POLICY.md`](SIGNING_POLICY.md), which analyses; this one
**decides**.

> **Nothing here is in force.** This is a decision sheet: it states exactly
> what is being authorised, by whom, for what scope, and what it explicitly
> does not cover. It takes effect when the approval block at the end is
> filled in and dated.

---

## Why this document exists, when `SIGNING_POLICY.md` already did the analysis

Because B-1 was blocked for a reason that was not legal at all: **nothing
was in a form that could be approved.** The analysis laid out three
candidate entities and five roles, and then asked for a decision — without
putting one on the table.

A decision sheet is the missing object. And one thing makes it tractable
now: the perimeter is **experimental, scientific and non-commercial**. That
is a far lighter commitment than a commercial attestation, and it is the
reason this can be settled rather than deferred again.

---

## What is proposed

### The committing entity

**NeoMundi Recherche** — the French association, RNA **W563015824**.

Why this one, and not the other two:

| Entity | Why not |
|---|---|
| The Swiss Sàrl | signing in a commercial entity's name imports commercial liability into an experiment that has no commercial purpose. Right for a paid pilot; wrong, and heavier than needed, for this. |
| The GitHub organisation | **not a legal person.** It cannot commit, and must never be named as the committing entity. |

The association is the entity whose purpose — non-profit research — matches
what is actually being attested. The choice is not a default by elimination:
it is the only one of the three whose object covers the act.

### The scope of what a signature commits to

This is the operative part, and it is deliberately narrow.

> An attestation signed under this policy asserts exactly this: **NeoMundi
> Recherche, in the context of a scientific experiment, committed to the
> digest of this measurement package on the declared date.**

And it asserts nothing else. In particular, **none** of the following:

- that the measurement is correct, or that its values mean what a reader
  assumes;
- that the execution took place, or when, or at whose hands;
- that the declared date is true — no trusted clock takes part;
- any warranty, service level, or commercial undertaking whatsoever;
- any medical, legal, or factual validation.

The verifier already says all of this on every run. This policy adds a
statement the verifier cannot make: **who** is committing, and in what
capacity.

### The five roles, as proposed

| Role | Proposed | Commits to |
|---|---|---|
| **Committing entity** | NeoMundi Recherche (RNA W563015824) | the content of the statement, within the scope above |
| **Authorised representative** | **to name below** | that the association is bound |
| **Key holder** | the operator workstation's DPAPI store | nothing; holds the secret |
| **Technical operator** | **to name below**, by role | nothing; runs the command |
| **Measurement author** | `nm-station` | the measurement, not the commitment |

The holder and the operator may be the same person. The **representative**
and the **holder** must be distinguishable in the record even when they are
the same person, because they commit to different things — and a trust store
that merged them would make a workstation's secret read as an
organisation's signature.

### What goes in the trust store, and what does not

| Field | Value | Note |
|---|---|---|
| `store_kind` | `production` | only once this sheet is approved |
| `legal_name` | `NeoMundi Recherche` | an entity's name is public |
| `kind` | `association` | |
| `jurisdiction` | `FR` | |
| `registration_reference` | `RNA W563015824` | public register entry |
| `legal_capacity_to_attest` | `experimental` | **see below** |
| the representative's **name** | **absent** | a natural person's name is not ours to publish; the role is recorded, the person is not |

#### A fourth value for `legal_capacity_to_attest`

The field currently accepts `unverified`, and the policy says it leaves that
state only on a verified check of powers. For a commercial attestation, that
remains right.

For this scope it would be **wrong in both directions**: `unverified`
understates a decision that has actually been taken, and `verified` would
overstate a check nobody performed against the statutes.

The honest value is a third one: **`experimental`** — the entity is named
and has decided, the scope is non-commercial, and **no verification of
powers has been performed.** The verifier must report it as its own line,
neither as a failure nor as a full capacity.

> This requires adding `experimental` to the schema's enumeration and a
> verifier line that says precisely what it means. **Not yet done** — it is
> the first technical step after approval, and it must not be done before,
> because a value in the schema that nobody has authorised would be an
> invitation to use it.

---

## What this does NOT authorise

Listed because an approval tends to be read more broadly than it was given.

1. **No commercial attestation.** A paid pilot needs the Sàrl decision, or
   an explicit extension of this one. This sheet does not provide it.
2. **No key generation.** That is B-2, and it has its own approval.
3. **No publication of the trust store.** That is C-5, which additionally
   requires a content audit.
4. **No retroactive re-signing** of anything already attested with a test
   key. Those packages stay demonstrations; re-attesting them would produce
   **retrospective** attestations, which is a separate act.
5. **No claim of eIDAS qualification**, ever, under any configuration.

---

## The decision — APPROVED on 6 November 2026

Taken as a direction decision. Recorded here as it was given.

```
D-1  The committing entity is NeoMundi Recherche, RNA W563015824 --
     the scientific association currently carrying the project.

     APPROVED -- 6 November 2026, direction decision.
     Scope: experimental, scientific, NON-COMMERCIAL.

D-2  The authorised representative of the association for signing acts
     under this policy is:

     role: the legal representative of NeoMundi Recherche
     (the ROLE is what the trust store records. The natural person is
     named in the internal register only, and is never published --
     see "the person is not ours to publish" above.)

D-3  The technical operator authorised to run a signature, and the holder
     of the private key:

     role:   the technical operator of the signing workstation
     holder: that workstation's DPAPI store

     Same person as D-2?   NOT RECORDED -- and it changes no verdict.
     The verifier already reports when roles coincide, on every run
     ("the separation is nominal"). Answering it would document a fact
     the output already states; leaving it blank withholds nothing.

     ---

     `legal_capacity_to_attest` is set to `experimental`, with the meaning
     stated above: entity named and decided, non-commercial scope, NO
     verification of powers performed.

     Deliberately NOT done, and not required: constitution of the future
     commercial company, and any exhaustive legal qualification. Neither
     blocks this scope.
```

### What this does not settle

The **person** holding the D-2 role. That belongs in the internal register,
not here, and not in the trust store — the field for a representative's name
is deliberately absent from the schema. Development does not wait on it: no
code path reads it, and no verdict depends on it.

### What has been done since approval

1. ✅ `experimental` added to the trust-store schema, with a verifier line
   that states what it does and does not mean, in both languages — and
   [`tests/test_capacite.py`](../tests/test_capacite.py) locks the three ways
   it could be misread;
2. ✅ `sign.py --signer-capacity experimental --signer-registration` emits it;
3. ⏳ **B-2**: the custody and rotation tooling is built and tested; the
   production key itself is **not generated** — see
   [`B2_KEY_CUSTODY_AND_ACTIVATION.md`](B2_KEY_CUSTODY_AND_ACTIVATION.md);
4. ⏳ **C-5**: prepared, not published;
5. ⏳ the trust store moves to `store_kind: production` only at step 3.

Until the production key exists, every attestation this product produces
remains a **demonstration**, and must be described as one. The verifier says
so itself: a `test` key grants nothing without `--allow-test-keys`.

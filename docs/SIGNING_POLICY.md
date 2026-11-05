<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="SIGNING_POLICY.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Signing policy — identity, mandate, and key custody

**6 November 2026.** Conditions **B-1** and **B-2** of
[`V1_CANDIDATE.md`](V1_CANDIDATE.md).

These two are one document because a key policy without an identity policy
says nothing: a key proves that *something* held it, never that anyone was
entitled to commit.

> **Nothing in this document is in force.** It states what must be decided,
> by whom, and what evidence closes each point. No production key exists, and
> none may be generated before Part A is settled.

---

## Part A — B-1: who commits, and to what

### What an attestation actually asserts

A verified Ed25519 attestation establishes exactly one thing:

> The holder of key `kid` committed to the digest of this package, and
> declared a signature date.

Everything else people will read into it is not there. In particular it does
**not** assert that the measurement is correct, that the execution took place,
that the declared date is true, or that the holder was entitled to commit on
anyone's behalf. That last gap is what Part A exists to close — and **no line
of code can close it.**

### The five roles, which must never be merged

The trust store already separates these. The policy explains why.

| Role | Who, today | What it commits to |
|---|---|---|
| **Committing entity** | `nm-recherche` — **undecided** | the content of the statement |
| **Authorised representative** | **not recorded** | that the entity is bound |
| **Key holder** | `nm-operator-poste` | nothing; holds the secret |
| **Technical operator** | `nm-operator-poste` | nothing; runs the command |
| **Measurement author** | `nm-station` | the measurement, not the commitment |

**Measuring is not committing, and holding a key is not being entitled to
use it.** Merging the key holder with the committing entity is the single
most tempting error here: it would make a workstation's secret look like an
organisation's signature.

### The decision to make

Three legal entities exist, and they are not interchangeable.

| Candidate | What signing would mean | What it would require |
|---|---|---|
| **The French association** (RNA W563015824) | a non-profit research body attests | a board decision, and a check that the signatory holds the power |
| **The Swiss Sàrl** | a commercial company attests, with commercial liability | a manager's decision; brings liability a pilot contract would rest on |
| **The GitHub organisation** | **not a legal person** | nothing — it cannot commit, and must never be named as the committing entity |

The third is listed only to be excluded: an organisation account is not a
legal person, and an attestation naming it would assert a commitment nobody
made.

**This is a legal decision before it is a technical one.** The honest default
until it is taken is the one in force today: `legal_capacity_to_attest:
"unverified"`, reported by the verifier on every run.

### How this condition closes

`legal_capacity_to_attest` moves off `unverified` when, and only when, all
three hold:

1. the committing entity is **named**, with its registration reference;
2. the **authorised representative** is recorded, and their power to bind the
   entity has been **checked against the entity's own statutes or mandate** —
   not asserted;
3. a **human decision** is recorded, dated, by that representative.

**No automated check may set this field.** The verifier reads it from the
trust store and reports it; it never derives it. A field that code could set
would be worth nothing.

### What the verifier does meanwhile

It reaches `cryptographically_attested` — the signature does verify — and
reports the unverified legal capacity as a separate, permanent `NOT TESTED`
line. The two statements are independent, and merging them would be the
dishonest shortcut: a valid signature from a party with no established
capacity is exactly what it looks like.

---

## Part B — B-2: the key, and its custody

### Why no production key exists yet

Because Part A is not settled. A production key generated now would be held
in the name of an entity that has not decided to commit, and every package
signed with it would carry that defect forward. **Generation waits.**

Everything signed to date used **ephemeral test keys**, destroyed after use,
and their trust stores carry `store_kind: "test"`.

### Generation

| | |
|---|---|
| Algorithm | **Ed25519**, imposed — never read from a token header |
| Tool | `sign.py genkey`, which refuses to write a private key under the repository root |
| Where | offline, on the operator workstation, never on a server |
| `kid` | **never reused**, including after revocation |
| Store kind | `production` only once Part A is settled |

The `kid` convention: `nm-ev-<entity>-<yyyymm>-<n>`. It must be unique for
all time — a reused `kid` would make two different keys indistinguishable in
a trust store, and would silently transfer trust from one to the other.

### Custody

| Question | Answer required before any production key |
|---|---|
| Where does the secret live? | the operator workstation's DPAPI store |
| Who can read it? | **to decide** — and recorded, by name of role |
| Is there an off-machine backup? | **required**; a lost key cannot re-sign anything |
| Where is the backup? | **to decide** — and it must not be reachable with the workstation |
| Who can authorise a signature? | **to decide** — the representative of Part A |

A workstation holding a key that can commit an organisation is a control
point. The backup question is not clerical: without it a disk failure makes
every future attestation impossible, and tempts a re-generation under the
same `kid`, which the convention above forbids.

### Rotation versus compromise — the distinction that carries everything

These are not two degrees of the same event. They have opposite effects on
the past.

| | `rotated` | `compromised` |
|---|---|---|
| Meaning | the key was replaced in an orderly way | the secret may be in someone else's hands |
| Signatures **before** the event | **stay trusted** | **all become untrusted, retroactively** |
| Why | nothing suggests the holder was ever not the holder | the holder can forge any `attested_at_declared` they like |
| Policy field | `on_rotated_key_within_window: trusted` | `on_compromised_key: untrusted_retroactively` |

**The asymmetry is the point.** A compromise cannot be contained by a date,
because the one thing a thief controls is the date they write. Any policy
that trusted pre-compromise signatures would be trusting a field the attacker
chooses.

Consequence, to face before the first paid pilot: marking a key
`compromised` invalidates **every** package it ever signed. The decision to
mark it must therefore be taken knowing whether those packages need
re-attestation under a new key — and re-attestation produces a
**retrospective** attestation, which states a verification at the effective
signature date and must never be presented as contemporaneous.

### Revocation

**Never revoke a key dry.** Replace first, then revoke. A revocation whose
replacement is not already in the trust store leaves every consumer with a
key they must distrust and no key they can trust — the verifier returns
`NOT TESTED` for an unknown key, so the whole chain silently drops a level
rather than failing loudly.

Order: generate successor → publish it in the trust store → set
`superseded_by` on the predecessor → only then mark the predecessor.

### Traceability

Each signature must be attributable after the fact:

- the `kid` is in the token header, so every attestation names its key;
- the trust store records `valid_from_declared` and `superseded_by`;
- **what is not recorded anywhere today** is a register of which packages
  were signed with which `kid`. Needed before a pilot: without it, a
  compromise cannot be scoped, and scoping is the only thing that limits the
  damage.

### Offline verification, from the public key alone

This is already true and must stay true. `verify_attestation.py` needs the
token, the archive, and a trust store — no network, no service, and
`cryptography` is optional: absent, the signature line returns `NOT TESTED`,
never `PASS`. An independent tool reaches the same conclusion:
`openssl pkeyutl -verify` validates the same signature.

**A verification that needed us would not be a verification.**

---

## What this document does not settle

- Which entity commits. That is Part A's open decision, and it is the gate on
  everything else.
- Who holds the key, and who authorises a signature. Both marked **to
  decide** above.
- Whether the committing entity carries the liability a pilot contract would
  rest on. A question for the entity, not for this repository.
- The register of signed packages. Named as missing; not built.

Until the first of these is settled, every attestation this product produces
is a **demonstration**, and must be described as one.

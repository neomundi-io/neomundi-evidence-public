<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="TRUST_STORE_PUBLICATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Publishing the trust store

**6 November 2026.** Condition **C-5** of
[`V1_CANDIDATE.md`](V1_CANDIDATE.md). **Design only — nothing is published.**

> No actual publication takes place before the content audit in the last
> section is done and signed off. This document is the design and the gate,
> not the act.

---

## The weakness this addresses

An auditor today downloads two things from the same place:

- the package, with its attestation;
- the trust store that says which key to trust.

Whoever controls that place controls both. A forger who can write to the
repository can add their own key to the store and sign a rebuilt archive with
it — and every control passes. This is limit 7 of
[`V1_CANDIDATE.md`](V1_CANDIDATE.md), stated there as "a forger who rebuilds
the archive **and** the attestation produces a consistent set, if their key is
trusted."

**The attack is not against the cryptography. It is against the single
source.** Ed25519 is not the weak point; the fact that the answer to "whose
key is this?" arrives by the same road as the question is.

---

## What would actually fix it, and what only looks like it

| Proposal | Does it help? |
|---|---|
| Publish the store on a second host we control | **barely** — same operator, same compromise |
| Publish the store's **digest** on a second channel | **yes** — the auditor compares, and one host alone can no longer lie |
| Sign the store with the same key it vouches for | **no** — circular; the store is what tells you to trust that key |
| Sign the store with a separate offline key | **yes**, and it moves the problem to that key's custody, which is a smaller and better-understood problem |
| Have a third party host the store | **yes**, and it costs an agreement we do not have |

The second line is the cheap, real fix. The fourth is the stronger one and is
deferred, because it needs a second key and Part A of
[`SIGNING_POLICY.md`](SIGNING_POLICY.md) has not even settled the first.

**Note what is not on this list: provenance by assertion.** A store that says
"published by NeoMundi" establishes nothing; the forger writes the same line.
An authenticity path must not rest on the store's own claims about itself.

---

## Design

### A versioned registry, separate from any archive

The store is **not** a file inside a package. It is a registry with its own
lifecycle, because keys outlive packages and a package must not carry its own
answer to whether its signer is trustworthy.

| | |
|---|---|
| Identifier | `store_id`, stable |
| Version | monotonic `store_version`, **new integer on every change** |
| Date | `updated_at_declared` — declared by us, never a timestamp |
| Nature | `store_kind: production` or `test`; `test` is `untrusted_unless_allowed` |
| Content | public key material and identities **only** |

A version number matters more than it looks: without it, two auditors holding
different stores cannot tell which is newer, and "the store said so" becomes
unfalsifiable.

The schema today has a `changes` array — an append-only history of what
changed and when, by declared date. That is **a record, not a comparable
version**: two stores can carry different histories with no single number
that orders them, and **no code reads the field at all** — `sign.py genkey`
writes it and nothing consumes it. So `store_version` is genuinely missing,
and adding it is a **prerequisite** of this condition rather than an optional
refinement.

### Two channels, and what each is for

| Channel | Carries | Role |
|---|---|---|
| **Primary** — the Evidence repository | the full store | what the tool reads |
| **Secondary** — the `.org` site, and the MCP card | the store's **digest** and its `store_version` | what the auditor compares against |

The secondary channel carries **no key material**. It carries a digest and a
version, which is all that is needed to detect a substituted store and
nothing that could be substituted *for* one.

### The authenticity path

An auditor who wants more than our word does this:

1. download the store from the repository;
2. compute its SHA-256;
3. read the digest and version published on the `.org`;
4. compare.

A forger must now compromise **two** independently operated channels and keep
them consistent. That is the whole gain, and it is worth stating plainly: it
raises the cost of the attack, it does not make it impossible.

### What this still does not establish

- **That the entity behind the key has capacity to commit.** That is B-1, and
  no publication channel touches it.
- **That we are who we say we are.** Both channels are ours. A third-party
  attestation of our identity is out of V1 scope and is named as such.
- **That a key was not misused by its own holder.** Custody, not publication:
  Part B of [`SIGNING_POLICY.md`](SIGNING_POLICY.md).

A reader who takes two channels for proof of identity has over-read this
design. The two channels defeat a *substitution*; they say nothing about
*who*.

---

## Content audit — the gate before any publication

The store is public material only, by construction. But "by construction" is
exactly the kind of claim that should be checked rather than trusted, because
a store is assembled by a tool and tools acquire fields.

Nothing is published until every line below is answered on observation.

| To check | Why it matters | State |
|---|---|---|
| No private key material, in any field | the catastrophic failure | **to verify at publication time** |
| No personal data — no name of a natural person, no e-mail, no address | publishing a representative's identity is a GDPR act, not a technical one | **to verify** |
| `legal_name` values are entities, not people | an association's name is public; a person's is not ours to publish | **to verify** |
| No internal hostname, path or machine identifier | `nm-operator-poste` names a role; it must not name a host | **to verify** |
| `store_kind` is correct | a `test` store published as production would make demonstration keys trusted | **to verify** |
| No `registration_reference` before B-1 | publishing a registration implies the entity decided to commit | **to verify** |
| `notes` fields re-read one by one | free text is where internal context leaks | **to verify** |

The last line is the one that will actually catch something. Structured
fields get reviewed; free-text notes get written in a hurry.

### Who signs off

The content audit is a **human decision**, recorded and dated, by the
representative identified in Part A of
[`SIGNING_POLICY.md`](SIGNING_POLICY.md). Until that representative is
identified, this condition **cannot** close — which makes C-5 dependent on
B-1, not merely adjacent to it.

---

## What remains to be built

| Item | Status |
|---|---|
| `store_version` in `schemas/evidence-trust-store-v1.json` | **missing** — prerequisite |
| A verifier line comparing the store's digest to a declared one | **not built** |
| The `.org` publication page | **not built** |
| The content audit, performed | **not done** |
| Sign-off | **blocked on B-1** |

**C-5 is therefore not closeable before B-1.** Stating the design is the part
that can be done now, and it is what this document is.

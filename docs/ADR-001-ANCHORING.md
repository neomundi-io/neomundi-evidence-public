<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="ADR-001-ANCHORING.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# ADR-001 — Third-party anchoring, and the four time claims

**Status: ACCEPTED, 6 November 2026.** Condition **D-8** of
[`V1_CANDIDATE.md`](V1_CANDIDATE.md).

---

## The problem

Four different things get called "timestamped", and they are not degrees of
one another. Three of them are routinely presented as the fourth, which is
how a package comes to claim a date nobody established.

This ADR fixes the vocabulary, states which claims V1 may make, and settles
whether third-party anchoring is worth its operational cost.

---

## The four claims, strongest last

| # | Claim | What establishes it | What it is worth alone |
|---|---|---|---|
| 1 | **Declared date** | someone wrote it in a field | **nothing** — the writer chose it |
| 2 | **Cryptographic signature** | a key verified over the content | the *commitment*, **not the date** |
| 3 | **Confirmed OpenTimestamps anchor** | the digest is committed in a mined Bitcoin block | an **upper bound**: it existed no later than that block |
| 4 | **eIDAS qualified timestamp** | a qualified trust service provider issues it | a legal presumption, in the EU |

### Why (1) is worth nothing

`attested_at_declared` is written by the signer. A signature over it proves
the signer committed to that value — not that the value is true. A holder of
the key can write any date they like, past or future, and the signature will
verify. **We never qualify a declared date as an independent timestamp.**

### Why (2) does not carry a date

This is the confusion that matters most, because a verified signature *feels*
like a dated act. It is not. The signature binds a key to a content; the date
inside the content is claim (1). Nothing in the cryptography observes a clock.

### What (3) actually establishes, and what it does not

An OpenTimestamps proof whose attestation is a **Bitcoin block header** says:
this digest existed **no later than** that block. That is a real, independent
upper bound, obtained from a party with no interest in our packages.

It does **not** say when the digest was created — only that it is not newer
than the block. And converting a block height into a wall-clock date requires
the **block header**, which this repository does not have and will not fetch.
That conversion is delegated to the official client: `ots verify`.

So our tool's line is, and stays:

```
[PASS      ] attestation confirmee par la chaine - 2 attestation(s) Bitcoin, bloc(s) 974714, 974715
[NOT TESTED] temps verifie par un tiers - hors de portee de cet outil
```

**A block height is not a date.** We report the height we read, and refuse to
name the hour.

### Why (4) is not claimed, and will not be

OpenTimestamps is not a qualified trust service provider under eIDAS. No
configuration of it becomes one. The `NOT TESTED` line on eIDAS qualification
is **permanent** — not a gap awaiting work — and exists so that nobody reads
claim (3) as claim (4).

---

## The `PENDING` state, which is the easiest to misread

A freshly submitted proof carries `PENDING` attestations. A calendar has
undertaken to include the digest in a future Bitcoin transaction.

> **A `PENDING` proof attests no date whatsoever.**

It is weaker than claim (3) and tells you nothing claim (1) did not. It is
evidence that a submission happened, and that is all.

This is observable in the repository right now, which is the point:

| Proof | State | `verify --strict` |
|---|---|---|
| `examples/timestamp/…jws.confirmed.ots` | 2 Bitcoin attestations, blocks 974714 / 974715 | **0** |
| `examples/dossier-v1/…jws.ots` | 4 `PENDING`, 0 Bitcoin | **2** |

The two live side by side deliberately, so the lifecycle is visible at both
ends — and so an automated consumer cannot be fooled by a filename. The
second proof is named nothing special, and `--strict` refuses it on its
contents.

---

## Decision

**V1 adopts OpenTimestamps as an optional third-party anchor, and claims only
what a proof's own bytes establish.**

Concretely:

1. **Claim (1) is never called a timestamp.** `attested_at_declared` is
   always rendered as declared, by us.
2. **Claim (2) is never called a date.** The attestation line says a party
   committed; a separate line says what is known about time.
3. **Claim (3) is reported as the block height read from the proof**, never
   converted to an hour. Time verification is delegated, by name, to
   `ots verify`.
4. **Claim (4) is never made.** The eIDAS line is a permanent `NOT TESTED`.
5. **Anchoring stays optional.** No level of assurance depends on it: a
   package with no proof reaches `cryptographically_attested` exactly as one
   with a confirmed proof does. Anchoring adds an independent upper bound on
   time; it does not add commitment.
6. **Only digests leave the machine.** Submission sends a 32-byte digest to
   four public calendars — never an archive, never a pilot's data. This is
   what makes the anchor acceptable at all.

### The operational cost, which is the real content of D-8

| Cost | Reality | Consequence for an offer |
|---|---|---|
| Money | **none** — no account, no fee | nothing to price |
| Network | one submission to four public calendars | an air-gapped operator **cannot anchor**; say so rather than promise it |
| Latency | hours between submission and a Bitcoin attestation | **"timestamped" is not available at the moment of sealing** |
| A second step | `upgrade`, later, which writes a **new** proof | an operational step someone must actually run |
| Growth | the proof grew 786 → 2 717 bytes on confirmation | negligible |

The latency is the one that bites a contract. A package sealed and handed
over immediately carries a `PENDING` proof, which attests nothing. **An offer
may therefore promise an anchor, but never an anchor "on delivery".** The
honest wording is that an independent upper bound becomes available within
hours of sealing, by a step the operator runs.

### Minimal V1 policy

| | |
|---|---|
| Anchor at sealing | **yes**, submit — it costs nothing and starts the clock |
| Ship with a `PENDING` proof | **yes**, labelled as attesting no date |
| Promise a confirmed anchor on delivery | **no** |
| Re-run `upgrade` | the operator's step; it never overwrites the earlier proof |
| Keep the earlier proof | **always** — it is a piece of evidence in its own right, and `upgraded_from` chains the two |
| Required for an assurance level | **never** |

---

## Consequences

- `verify.py`, `verify_attestation.py` and `timestamp.py` keep their
  permanent `NOT TESTED` lines for third-party time and eIDAS. Those lines
  are the decision, written in the output.
- `upgrade` writes a new proof and a new descriptor, and leaves the
  predecessor byte-identical. Verified by case 27 of the timestamp suite: the
  upgrade must not change the committed object.
- An offer document that says "timestamped" without naming which of the four
  claims is meant is a defect, and should be treated as one.

## Rejected alternatives

| Alternative | Why not |
|---|---|
| Read the Bitcoin block header ourselves | needs a node or a trusted explorer. A "trusted explorer" is a trust dependency we would have to disclose, and it would replace a clean delegation with a hidden one. |
| Require a confirmed anchor for `cryptographically_attested` | the level is about commitment, not time. Coupling them would make the level unreachable for hours after sealing, for no gain in what it asserts. |
| Buy an eIDAS qualified timestamp | defensible later, and a real option for an EU contract. Out of V1: it introduces a paid provider, a per-package cost, and a jurisdiction question none of which is settled. |
| Drop anchoring entirely | it is free, sends only a digest, and is the only independent bound on time we can obtain. Dropping it would leave claim (1) as our only time claim — which is worth nothing. |

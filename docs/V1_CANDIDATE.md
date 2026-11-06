<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="V1_CANDIDATE.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# NeoMundi Evidence V1 — candidate product sheet

**6 November 2026.** Candidate submitted to the external review of **Monday
9 November**. Review protocol:
[`V1_REVIEW_PROTOCOL.md`](V1_REVIEW_PROTOCOL.md).

---

## In one sentence

> Evidence turns a NeoMundi measurement package into a package **your auditor
> verifies themselves, offline, without trusting us** — and which states
> plainly what it does not prove.

---

## The four assurance levels

This is the scale the whole product serves, and the verifier **derives** the
level — it never reads it from a document.

| Level | Means | Reachable |
|---|---|---|
| `declared` | written in a document; nothing recomputed | yes |
| `reference_verifiable` | a file is present, and its bytes hash to a digest the record declares | **yes** |
| `cryptographically_attested` | a signature by an identified key verifies | **yes, since 5 November** |
| `not_demonstrable` | out of reach of any local check | a statement, not an achievement |

**A package claiming more than it is gets refused.** That is the central
control: without it, writing a word in a text file would make a document look
like proof.

---

## The five tools

| Tool | What it does | Dependency |
|---|---|---|
| `verify.py` | 21 integrity controls on a package | **none** |
| `bind.py` | binds an observation to its external artifacts | none |
| `sign.py` · `verify_attestation.py` | detached **Ed25519** attestation | `cryptography`, **optional** on verification |
| `timestamp.py` | detached **OpenTimestamps** timestamping | none for the binding |
| `adapters/` | reconciliation with an external package | none |

**One single third-party package in the whole product** — `cryptography` —
and it is **optional**: absent, the signature line returns `NOT TESTED`, never
`PASS`. The 21 integrity controls import only the standard library.

---

## DEMONSTRATED guarantees

Each was executed, and the figure quoted is the one obtained — not an
estimate.

| Guarantee | Evidence |
|---|---|
| **Package integrity**, 21 controls, three never-merged states | `19 PASS, 0 FAIL, 2 NOT TESTED` on the demonstration package † |
| **A tampered package is refused** | 10 alterations out of 10 detected; 15 hostile archives out of 15 get a verdict |
| **Autonomous verification**, offline, no dependency | identical summary with `cryptography` and `opentimestamps` blocked |
| **No malformed input crashes** the tool | 9 malformed inputs out of 9 return a motivated verdict |
| **An offered artifact is the one the record refers to** | binding by digest recomputation, 17 faulty manifests refused |
| **An identified party committed** to a package's digest | detached Ed25519/JWS, level `cryptographically_attested` reached |
| **An archive recomputed after a deletion is detected** | `verify.py` alone: 0 FAIL; the attestation: FAIL |
| **A timestamp proof is bound to the package**, dependency-free | committed digest read at a fixed offset, 21 test cases |
| **An external receipt is confronted without being believed** | 5 statuses distinguished, contradictions preserved |
| **Verification by a tool that is not ours** | `openssl pkeyutl -verify` validates the same signature |
| **An automated consumer cannot be misled** | `--strict`: codes 0 / 1 / 2, changing no verdict |

† Measured before the completeness control existed; see
[ODA3 consolidation](ODA3_CONSOLIDATION.md).


### And one declared limit that closed

Since 5 November the falsification suite carried an accepted limit: "one
observation erased everywhere, counts and checksums redone" was **undetectable
inside** the archive. The attestation detects it. **It is the first time a
declared product limit has closed.**

---

## PENDING guarantees

Neither abandoned nor acquired. What is missing is named.

| Guarantee | What is missing | Realistic lead time |
|---|---|---|
| **An attested date** | Bitcoin confirmation of the `PENDING` proof | **hours** after `upgrade` |
| **Time verified by us** | a block header, hence a source of trust | out of scope — delegated to `ots verify` |
| **A production key** | the legal identity decision, and a custody | **before any paid pilot** |
| **A published trust store** | a second publication channel, and its audit | weeks |
| **The adapter exercised on a real package** | an external pilot's complete package | depends on the pilot |
| **Replaying a measurement** | deterministic evaluators — `NO-GO` as it stands | see `REPLAY_FEASIBILITY` |

---

## Functions NOT VALIDATED on real packages

This is the most important section of this sheet, and it must be read before
any offer.

> **None of the five functions has been exercised on a real pilot package.**
> Everything demonstrated above was demonstrated on **synthetic fixtures** and
> a **destroyed demonstration key**.

| Function | Exercised on | Never exercised on |
|---|---|---|
| Integrity | GROUNDED-S1 and MED demonstration archives, synthetic fixture | a package produced by a pilot |
| Attestation | a **test** key, demonstration archives | a production key, a real custody |
| Timestamping | a real proof, but **`PENDING`** | a **confirmed** proof |
| Binding | synthetic artifacts | a pilot's artifacts |
| Reconciliation | an **invented** receipt, **and the real CP8 receipt** | an archive bearing a digest in common with it — see below |

And three facts to state as they are:

- **Dennis Christie's package arrived on 5 November** — `RECONCILIATION.md`
  and both receipts. An earlier edition of this sheet said it had not been
  received; that was true when written and is no longer. The complete
  inventory is condition **D-7**, and it is kept privately: eleven digests
  are **cited with no referent supplied**, and the signed audit trail the
  package treats as canonical is **unrecoverable from us** — our own verify
  page states that document content is never retained.
- **A real third-party package was exercised on 6 November** — 21 declared
  digests recomputed, 21 concordant. `reference_verifiable` is therefore
  reached on real artifacts. But `verify.py` and `sign.py` both **refuse**
  it, and the second refusal is correct: the signed subject reads
  `observation_count` from an Evidence manifest, and over a foreign archive
  it would sign `"0"` across seven observations.
- **the signer's legal capacity is not verified**, and no code will establish
  it.

---

## What must never be claimed

Seven sentences, and the first three are the most tempting.

1. **"Proof that the execution took place."** Never. Binding an artifact to a
   record says neither that the execution happened, nor when, nor at whose
   hands.
2. **"Timestamped"** in the sense of an established date. The proof is
   `PENDING`: **no date is attested.**
3. **"Signed"**, for a document whose signature has not been verified.
4. **"eIDAS qualified timestamp."** OpenTimestamps is not a qualified trust
   service provider.
5. **"Reproducible"** in the computational sense. The freeze guarantees the
   inputs, not that the measurement redoes itself identically.
6. **"Medical, legal or factual validation."** A measurement is a measurement.
7. **"Tamper-proof package."** A forger who rebuilds the archive **and** the
   attestation produces a consistent set, if their key is trusted. Only a
   digest kept elsewhere, or a key whose custody is controlled, detects that.

---

## The last conditions before a commercial pilot offer

In decreasing order of blockage. The first three are **blocking**.

### 🔴 B-1 — Settle the signer's legal identity

`trust-store.json` currently carries `legal_capacity_to_attest: "unverified"`
for NeoMundi Recherche, and the verifier reports it on every run.

**Signing is a commitment.** Which of the three entities commits — the French
association, the Swiss Sàrl, or the GitHub organisation? The question is
**legal before it is technical**, and no line of code will settle it.

*Without this decision, a production attestation cannot be issued.*

### 🔴 B-2 — A production key, and its custody

No production key exists. Needed: generate it offline, place it in the
workstation's DPAPI store, an off-machine backup, and a **written rotation
procedure** — including the `rotated` / `compromised` distinction, since the
second invalidates **every** earlier signature.

*Without that, everything signed remains a demonstration.*

### 🔴 B-3 — Exercise the chain on **one** real pilot package

One would suffice, and there is none. Until a function has been exercised on a
package produced by a pilot, "it works" is an **extrapolation**, not an
observation.

*This is the condition that separates a demonstration from a product.*

### 🟠 C-4 — Obtain at least one **confirmed** timestamp proof

An `upgrade` a few hours after sealing. Until then, "timestamped" cannot be
written in an offer.

### 🟠 C-5 — Publish the trust store on a second channel

Today an auditor downloading the store and the package gets both from the
**same source**. Publishing the store's digest elsewhere — the `.org`, the MCP
card — lifts that weakness. **After auditing what it exposes.**

### 🟠 C-6 — Translate the verifiers' output

It is in French; the documentation is bilingual. An English-speaking auditor
today reads strings they cannot understand. The JSON report mitigates; it does
not replace.

### 🟡 D-7 — Receive the complete CP8 package

`RECONCILIATION.md` and the receipt itself. The adapter is ready; it has not
been exercised on the object it was designed for.

### 🟡 D-8 — Decide on third-party anchoring, and its operational cost

OpenTimestamps is free and needs no account, but it introduces a **network
submission** and a wait for confirmation. To be settled before promising it in
a contract.

---

## Candidate state

| | |
|---|---|
| Branch | `feat/evidence-v1-candidate` |
| Off | `main` = `15ac159` |
| CI | **5 green checks**, Python 3.11 / 3.12 / 3.13 |
| Suites | **8 suites**, see the review protocol |
| Demonstration package | `examples/dossier-v1/` — entirely synthetic |
| Demonstration | `demo_v1_5min.sh` — 12 screens, offline |
| Deployment | **none** |

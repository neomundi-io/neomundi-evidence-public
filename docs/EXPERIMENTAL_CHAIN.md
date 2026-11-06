<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="EXPERIMENTAL_CHAIN.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# The experimental proof chain — what it demonstrates, and what it does not

**6 November 2026.** B-1 approved, B-2 tooled, C-5 prepared. This document
records what is **actually demonstrated**, how it was measured, and where the
chain stops.

> **An experimental attestation is never a legal certification.** That
> sentence is not a disclaimer appended here: the verifier prints it, in both
> languages, on every run, and
> [`tests/test_capacite.py`](../tests/test_capacite.py) fails if it ever
> stops.

---

## The issuing entity

**NeoMundi Recherche**, RNA **W563015824** — the scientific association
currently carrying the project. Scope: **experimental, scientific,
non-commercial**.

`legal_capacity_to_attest` is **`experimental`**, and that value means
something precise:

| | |
|---|---|
| The entity is **named** | and has taken a documented decision to attest |
| The scope is **non-commercial** | |
| **No verification of its powers has been performed** | |

`experimental` is **not a weaker `verified`**. It is the opposite: `verified`
says a check happened elsewhere; `experimental` says none did. The
distinction between an identity **declared** and an identity legally
**verified** is the one thing this whole condition exists to keep visible.

**Deliberately not done, and not required:** the constitution of the future
commercial company, and any exhaustive legal qualification. Neither blocks
this scope.

---

## The chain, link by link

| | Link | Status | What establishes it |
|---|---|---|---|
| **a** | archive bytes → digest | ✅ | `sha256`, standard library. Portable since `create_system` was pinned — before, Linux returned a different digest than the signed one |
| **b** | digest → detached JWS | ✅ | Ed25519, algorithm **imposed**, never read from the header. Forging `alg` to `none` is caught |
| **c** | public key → trust store | ⚠️ **test store** | the tool says so itself: a `test` key grants nothing without `--allow-test-keys` |
| **d** | public key → **legal entity** | ⚠️ **declared** | B-1: entity named, capacity `experimental`, powers unverified |
| **e** | date | ✅ | OpenTimestamps, Bitcoin blocks 974714/974715. Attests *no later than*, never *when*. `PENDING` attests **no** date |
| **f** | completeness of the export | ⚠️ **partial** | catches an *inconsistent* amputation; a forger who also rewrites the declaration defeats it |
| **g** | measuring instrument | ❌ **absent** | R-6: 0 provenance fields across 238 measurements. `not_demonstrable` |

Three links hold on their own. Two are declared. One is partial. **One is
absent.**

### The dependency this week revealed

Link **f** falls back on **b**. The completeness control is the defence that
works on an **unsigned** archive; beyond that, only the signature stops a
thorough forger. So B-1 and B-2 are not a track parallel to the completeness
work — **they condition its value.** While the key is a test key, completeness
is guaranteed against negligence only.

---

## What a third party can reproduce

Offline, with no access to us, no account, and no network:

```sh
# 1. the archive is the one the attestation commits to
python verify.py <archive.zip> --corpus <corpus>

# 2. the signature, and the identity declared for it
python verify_attestation.py <archive.zip.jws> --archive <archive.zip> \
       --trust-store <trust-store.json> --store-digest <digest from channel 2>

# 3. the anchoring date, without trusting our clock
python timestamp.py verify <proof.ots> --subject <archive.zip.jws>

# 4. and the package can be rebuilt byte for byte
python tests/make_fixture.py <dir> --profile v1   # reproduces e31e12bb…
```

Step 2's `--store-digest` is what closes the single-source weakness: the
auditor obtains that digest from a **second channel** and the primary host
can no longer lie alone. The payload for that channel is produced by
`publish_store.py payload`, and carries **a digest and a version, nothing
else**.

---

## Demonstrated guarantees, and how

Every row below is a test that fails if the property stops holding.

| Guarantee | Measured by |
|---|---|
| A declared capacity **never changes a verdict**. Writing `verified` in a store gains nothing | `test_capacite` 6–7: identical counts, `NOT TESTED` either way |
| The declared/verified distinction survives translation | `test_capacite` 4–5: the negation is asserted in **both** languages |
| A capacity value unknown to the verifier is **reported, not interpreted** | `test_capacite` 9 |
| Every schema value has an explanation, and every explanation a schema value | `test_capacite` 8 — the drift that bit `CAUSES_PAR_SIGNAL` once |
| An **inconsistent** amputation of an export is refused, with no signature involved | `test_completude`; replayed as OD-C in the ODA3 re-evaluation |
| A **rotation** leaves earlier signatures trusted; a **compromise** invalidates them all, retroactively | `test_cles` 5–6, on the **same** attestation, unchanged to the byte: `PASS` then `FAIL` |
| A dry revocation is refused — twice | `test_cles` 4: no successor, then a successor not yet published |
| A compromise is neither requalifiable as a rotation nor replaceable | `test_cles` 8 |
| A `kid` is never reused | `test_cles` 9 |
| The register of signed packages is **append-only** | `test_cles` 1–2 |
| Signing with no register **says so** | `test_cles` 3 |
| A private key, and the register, are refused anywhere under the repository | `test_cles` 11–12 — a hard guard, not a warning |
| The secondary channel's payload carries **no key material** | `test_publication` 4 |
| A private scalar in a store is caught **twice** — by pattern and by field | `test_publication` 5 |
| A failed audit produces **no payload at all** | `test_publication` 6 |
| The published digest is that of the **transmitted bytes** | `test_publication` 7 |
| The publication preparer has **no network access** | `test_publication` 8, verified statically over its imports |
| The payload's digest is accepted verbatim by `--store-digest`, and a false one is refused | `test_publication` 9–10 |

**Suites:** `completude` 15/15 · `bom` 11/11 · `capacite` 10/10 · `cles`
12/12 · `publication` 10/10 · `i18n` 26/26 · `attestation` 24/24 ·
`timestamp` 25/25 · `reconciliation` 27/27 · `falsification` 10/10 ·
`adversarial` 13 of 15 with two declared limits.

**No historical evidence changed.** The V1 dossier still returns
`19 PASS, 0 FAIL, 3 NOT TESTED`, its digest is unmoved, and `--profile v1`
still reproduces it byte for byte.

---

## What is NOT demonstrated

| | |
|---|---|
| **That the entity may lawfully commit** | no powers were verified. A permanent `NOT TESTED` — no code can decide it |
| **Who holds the key**, as a natural person | the role is recorded; the person is in the internal register and is never published |
| **That the declared evaluator is the one that ran** | R-6. `not_demonstrable`, and no contract change makes it verifiable from an archive |
| **That a withholding was legitimate** | the control reads a declaration, not the ledger |
| **That the content is true** | out of a signature's reach. A perfectly signed attestation over a fabricated archive is cryptographically valid |
| **Any date, as an independent fact**, absent an anchor | `attested_at_declared` is declared by the signer |
| **eIDAS qualification** | never claimed, under any configuration |

---

## The one irreversible step not taken

**The production key is not generated.** The tooling is built and tested —
generation, custody, backup, rotation, compromise scoping, the register — and
the key itself does not exist.

That is deliberate. A long-lived signing secret for a named legal entity is
exactly the irreversible mechanism that must not be created without an
explicit decision, and the documented procedure places its generation
**offline, on the operator workstation**, not inside a working session.

What remains, in order, is in
[`B2_KEY_CUSTODY_AND_ACTIVATION.md`](B2_KEY_CUSTODY_AND_ACTIVATION.md):
accept the custody block, name the backup medium and the register's location,
then run one command. Until then, **every attestation this product produces
is a demonstration, and is described as one.**

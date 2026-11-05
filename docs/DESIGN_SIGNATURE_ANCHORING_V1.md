<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="DESIGN_SIGNATURE_ANCHORING_V1.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Signature and external anchoring — proposed architecture

**5 November 2026. A proposal awaiting validation. No code has been written.**
This document is the phase 4 deliverable; implementation is explicitly on
hold.

Goal: make `cryptographically_attested` reachable with a real, demonstrable
guarantee that a third party can verify without trusting us.

---

## A note on the order of phases

The brief asks, in phase 3, to "define **then execute**" ten tests, and in
phase 4 not to write code before the architecture is validated. Both cannot
hold at once: you do not execute the tests of a mechanism that does not exist.

**I resolved it in favour of phase 4:** the ten tests are **defined** below
with their expected verdicts, and **none was executed**. They become the
acceptance grid for the implementation, on the day it is authorised.

One thing only was executed, and outside the repository: a feasibility probe
of the cryptographic component, because proposing an architecture without
checking that its central brick works would be exactly the "announced
capability" this product refuses. Its keys were ephemeral and have been
erased.

---

# Phase 1 — Audit of existing capabilities

Read-only. No repository was modified, no service called.

## 1.1 What already exists, and is reusable

**`govern-v3/app/rgc/signing.py` — a complete Ed25519/JWS mechanism, in
production.**

| Element | Observed value |
|---|---|
| Algorithm | Ed25519, `alg: "EdDSA"` |
| Format | compact JWS, via `PyJWT` |
| Library | `cryptography` + `PyJWT` |
| Key identifier | `kid` in the JWS header **and** `integrity.key_id` in the contract |
| Public key | `public_jwk()` → JWK `OKP` / `Ed25519`, served by `GET /v1/rgc/jwks` |
| Signed object | `{payload_hash, hash_algorithm, schema_version, request_id, timestamp}` — **a short attestation referencing a digest, not the whole object** |
| Declared canonicalisation | `sorted-json-utf8` (`RgcIntegrity.canonicalization`) |
| No fallback | deliberate: `503` if the key is missing, never a hash-only contract |
| Private key | `RGC_SIGNING_PRIVATE_KEY`, 32-byte seed in base64url, via environment |

**This is the pattern to reuse.** The format is right, the algorithm choice is
right, and the decision to sign a *short attestation referencing a digest*
rather than the whole object is precisely what Evidence needs.

### Three limits of RGC, which explain what must be added

**`verify_jws` requires the private key.** It derives the public key from the
private one (`_public_key_pem()` calls `_load_private_key()`). So there is
**no third-party verification path**: only the secret holder can verify.
Sufficient for an internal check, unusable for an auditor.

**JWKS is an HTTP endpoint.** Resolving `key_id` → verification key means
calling the API. Offline verification is therefore impossible as it stands.

**No expiry, no revocation.** `RgcIntegrity` carries no `not_after`, no key
status, no revocation list. Key lifecycle has to be designed, and the brief
asks for it explicitly.

## 1.2 Station — no signature at all

Exhaustive search over `src/station/`: **no signature primitive.** The only
occurrence is the constant `RGC_JWKS_PATH = "/v1/rgc/jwks"` in
`connectors/neomundi/contract.py`, never called to verify anything.

Station does, however, carry a component of real value:
**`src/station/ledger/canonical.py` is a complete RFC 8785 (JCS)
implementation, with no external dependency.** It handles the three points
where `json.dumps` is not enough — ECMAScript number formatting, key ordering
over UTF-16 code units, and refusing anything that cannot be canonicalised
unambiguously (NaN, infinity, integers beyond 2⁵³−1).

**Direct consequence:** the ledger is canonicalised and **chained**, but
**unsigned**. Whoever can rebuild the ledger can rebuild its chain. That is
exactly the central hole the adversarial audit identified.

## 1.3 The four-level Evidence contract — verified

Read in `schemas/evidence-manifest-v1.json` and `bind.py`:

```
declared · reference_verifiable · cryptographically_attested · not_demonstrable
```

| Contract point | Observed state |
|---|---|
| The level is **derived**, never read from the manifest | ✅ `controle_revendications` refuses any claim exceeding the derived level |
| `cryptographically_attested` unreachable today | ✅ `controle_signatures` always returns `NOT TESTED` |
| The signature slot **already exists** in the schema | ✅ `signatures[]` with `{algorithm, key_id, value, covers}` |
| An unsigned archive keeps its level | ✅ no signature → `NOT TESTED`, not `FAIL` |
| Never a `PASS` over an empty set | ✅ fixed on 5 November: zero claims exercised → `NOT TESTED` |

**So the schema need not change to accommodate signatures.** What is needed is
to pin down the semantics of `signatures[]` and to add the trust store, which
it lacks.

## 1.4 Malformed cases — regression in place, structured verdicts

| Check | Result |
|---|---|
| All 9 malformed inputs return a verdict | ✅ 9 `[VERDICT]` cases, 0 crashes |
| Machine-readable verdicts | ✅ `neomundi.evidence.verification-report/1` and `…binding-report/1` |
| The three states stay distinct in JSON | ✅ a `state` field per control, and separate `counts` |
| What the report does not establish is written down | ✅ `does_not_establish`, 4 entries |

## 1.5 Fully offline verification — minimal solution identified

**Ed25519 is not verifiable with Python's standard library.** `hashlib` and
`hmac` alone give symmetric primitives, which cannot serve public
verification. There is no elegant way around this.

Available on this workstation:

| Component | State |
|---|---|
| `cryptography` | **50.0.0** — Ed25519 present |
| `PyJWT` | 2.13.0 |
| `openssl` | 3.5.7 |
| `gpg`, `ssh-keygen` | present |
| `nacl`, `ecdsa`, `PyCryptodome` | absent |

**Feasibility probe executed, observed results:**

```
[OK] verification stdlib + cryptography, without PyJWT
[OK] an altered payload is refused
openssl pkeyutl -verify      : Signature Verified Successfully
openssl on altered input     : Signature Verification Failure | code 1
PEM rebuilt from the JWK identical : True
```

Four lessons, all decisive for the architecture:

1. **`PyJWT` is not necessary.** A compact JWS splits into three base64url
   parts with the standard library; only the `Ed25519PublicKey.verify()`
   primitive needs `cryptography`. One dependency instead of two.
2. **`openssl` verifies the same signature**, with none of our tools. That is
   the independence argument of the whole package, and it is demonstrated,
   not assumed.
3. **The public JWK is enough**: it rebuilds the PEM identically. The trust
   store can therefore be a plain JSON file, and the `openssl` path derives
   from it.
4. An Ed25519 public key is **32 bytes**. The store fits one line per key.

## 1.6 What signature proves, and what anchoring proves

This is the point the brief asks not to conflate, and it deserves to be
written before any design.

| Mechanism | Proves | Does not prove |
|---|---|---|
| **Signature** | that the holder of key `kid` signed **those exact bytes**, and that they have not moved since | that the signed content is true; nor **when** it was signed |
| **External anchoring** | that this digest **existed before** an instant attested by a third party | that the content is true; nor who produced it |
| **Both together** | that an identified party committed to a precise content, before a date it does not control | **still not** that the measured execution took place |

**A signature proves custody and commitment, not a fact.** A perfectly signed
attestation over a fabricated archive is cryptographically valid. What the
signature adds is that we know **who** committed, and they can no longer deny
it.

That is a great deal, and it is not the truth of the content. The two must
remain two separate control lines.

---

# Phase 2 — Minimal design

## 2.1 The structuring choice: a **detached** signature

The signature does **not** go inside the archive.

The reasoning is forcing: the attestation covers `bundle_sha256`, the digest
of the archive file. Slipping the signature inside the archive would change
its bytes, hence its digest, hence invalidate the signature just computed.
Circular, and unsolvable.

A detached file beside the archive:

```
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip          ← untouched, byte for byte
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws      ← the signed attestation
```

**Three of the brief's constraints are satisfied at once:**

- *compatibility with V0.1 archives* — they are not touched;
- *no change to the frozen corpora* — they can be attested
  **retroactively**, without being reopened;
- *no rewriting of historical evidence* — nothing is rewritten, something is
  added beside it.

That is the biggest gain of this design, and it falls straight out of the
decision to detach.

## 2.2 The signed object — `neomundi.evidence.attestation/1`

A short claim set, **flat, and textual only**:

```json
{
  "schema": "neomundi.evidence.attestation/1",
  "subject_kind": "evidence_bundle",
  "bundle_sha256": "84ff0dec…",
  "manifest_sha256": "…",
  "checksums_sha256": "…",
  "export_schema": "station.export.campagne/2",
  "observation_count": "30",
  "issued_at": "2026-11-05T12:00:00Z",
  "signer_identity": "neomundi-evidence-signer",
  "key_id": "nm-ev-2026-11-a"
}
```

**Why strings only, `observation_count` included.** A float or an integer in
the signed object brings back the whole question of canonical number
formatting — the one `ledger/canonical.py` handles in 250 lines and which
Evidence's simplified `jcs()` **does not** handle, as its own docstring says.
Forbidding numbers in the attestation removes the problem instead of managing
it. The cost is `"30"` instead of `30`; the benefit is that no serialisation
disagreement between a signer and a verifier is possible.

**Why three digests and not one.** `bundle_sha256` binds the whole file;
`manifest_sha256` and `checksums_sha256` let an auditor who received only part
of the package anchor what they have. Defence in depth, and support for
partial deliveries.

**Transport.** A compact JWS, whose payload is carried **verbatim**:

```
base64url(header) . base64url(attestation) . base64url(signature)
```

Intended consequence: the verifier verifies **the bytes it reads**, never
rebuilding the object. Canonicalisation therefore plays no part in the
verification path — which eliminates the most insidious class of bug in this
kind of mechanism.

Header: `{"alg":"EdDSA","typ":"JOSE","kid":"nm-ev-2026-11-a"}`. The verifier
**refuses any `alg` other than `EdDSA`**, and never reads `alg` to choose an
algorithm — it imposes its own. That is the defence against the "algorithm
confusion" family of attacks that devastated JWT implementations.

## 2.3 The trust store — `trust/neomundi-evidence-keys.json`

Versioned in the public repository. **Public keys only.**

```json
{
  "schema": "neomundi.evidence.trust-store/1",
  "updated_at": "2026-11-05T12:00:00Z",
  "keys": [
    {
      "kid": "nm-ev-2026-11-a",
      "kty": "OKP", "crv": "Ed25519", "alg": "EdDSA",
      "x": "<32 bytes in base64url>",
      "signer_identity": "neomundi-evidence-signer",
      "status": "active",
      "valid_from": "2026-11-05T00:00:00Z",
      "valid_until": null,
      "superseded_by": null,
      "revocation": null
    },
    {
      "kid": "test-only-do-not-trust",
      "status": "test",
      "…": "the public examples' key"
    }
  ]
}
```

### Lifecycle, and the distinction that matters

```json
"revocation": { "kind": "rotated" | "compromised", "at": "…", "reason": "…" }
```

**`rotated`** — the key stopped being used. Signatures whose `issued_at` ≤
`revocation.at` **stay trusted**. Nothing happened to the key; we changed it.

**`compromised`** — **all** signatures by that `kid` become untrusted,
whatever their `issued_at`. Reason: whoever holds the private key can forge
any `issued_at`. Letting pre-compromise signatures survive would mean
trusting a timestamp the attacker controls.

That is the distinction most designs get wrong, and it only holds because the
two cases are named separately in the store.

### The verifier's decision table

| Situation | `signature` | `trust` | Derived level capped at |
|---|---|---|---|
| `kid` unknown to the store | `NOT TESTED` | `NOT TESTED` | `reference_verifiable` |
| `kid` known, signature invalid | **`FAIL`** | — | — |
| `kid` `active`, signature valid | `PASS` | `PASS` | `cryptographically_attested` |
| `kid` `rotated`, `issued_at` within window | `PASS` | `PASS` | `cryptographically_attested` |
| `kid` `rotated`, `issued_at` after | `PASS` | **`FAIL`** | — |
| `kid` `compromised` | `PASS` | **`FAIL`** | — |
| `kid` expired (`issued_at` > `valid_until`) | `PASS` | **`FAIL`** | — |
| `kid` `status: test`, without `--allow-test-keys` | `PASS` | **`FAIL`** | — |
| `cryptography` absent | `NOT TESTED` | `NOT TESTED` | `reference_verifiable` |

An unknown key returns **`NOT TESTED`, not `FAIL`**: the signature may be
perfectly valid, we simply cannot know. Calling it invalid would be a
groundless accusation — the same reasoning as for a missing artifact, settled
on 5 November.

A test key must be **refusable**: the public examples ship one, and an
ordinary verification must never grant it `cryptographically_attested`.

## 2.4 Three control lines, never merged

The brief asks for the distinction between valid signature, trusted identity,
and content integrity. Three separate lines:

```
[PASS      ] cryptographic signature - EdDSA/Ed25519, key nm-ev-2026-11-a
[PASS      ] trusted identity - key active, signer neomundi-evidence-signer
[PASS      ] agreement with the archive - bundle_sha256 recomputed, conforming
[NOT TESTED] external anchoring - tier A only: `issued_at` remains declared
[NOT TESTED] truth of the content - a signature attests no fact
```

`cryptographically_attested` is derived only if the **first three** are
`PASS`. A valid signature by an untrusted key must never read as an
attestation.

## 2.5 Anchoring — two tiers, and only the second is independent of us

### Tier A — internal anchor register, available immediately

`anchors/anchor-log.jsonl`, in the public repository, append-only and
**itself chained**:

```json
{"seq":"1","attestation_sha256":"…","bundle_sha256":"…",
 "kid":"nm-ev-2026-11-a","recorded_at":"2026-11-05T12:00:00Z",
 "prev_entry_sha256":null}
```

The ordering witness is the Git commit; the date witness is GitHub's push
record, which we do not write.

**What tier A proves:** this digest was published in a public append-only log
at or before commit *X*, and the log has not been reordered without rewriting
Git history.

**What tier A does not prove: independence from NeoMundi.** We own the
repository. An administrator can force a rewrite. The organisation rulesets
(`non_fast_forward`, `deletion`) raise the cost; they do not make it
impossible. And the GitHub organisation is **not verified**
(`is_verified: false`), so an auditor cannot even lean on that.

> The brief asks for an anchor register independent of **the archive**. Tier A
> satisfies that: the log does not live in the archive and does not depend on
> it. It does **not** satisfy independence from **the issuer**, which is a
> different property. Conflating them would be the overclaim this product
> forbids itself.

### Tier B — third-party anchoring, to be decided separately

| Candidate | Cost | Independence | Offline verification | Caveat |
|---|---|---|---|---|
| **OpenTimestamps** | free, no account | **strong** — Bitcoin-anchored | **yes**, after one network submission | confirmation in hours |
| Sigstore / Rekor | free | strong | partial — inclusion proof must be stored | identity tied to an OIDC provider |
| RFC 3161 timestamping | low to none | medium — depends on the authority | yes | authority choice to investigate |
| Deposit with a notary | moderate | strong, non-technical | n/a | fits the three legal entities |

**Recommendation: OpenTimestamps**, the only candidate that is free, needs no
account, and whose proof verifies offline. To be decided separately, as it
introduces a network submission — at sealing time only, never at
verification.

**Until tier B exists, `issued_at` remains declared.** Expiry checking
therefore rests on our word. That is the most significant residual risk in the
whole design, and the decisive argument for tier B.

## 2.6 Separation of signer and verifier

| | Signer | Verifier |
|---|---|---|
| File | `sign.py` | `verify_attestation.py` |
| Key | private, read from the workstation's DPAPI store | public, read from the trust store |
| Dependency | `cryptography` **required** | `cryptography` **optional** → `NOT TESTED` otherwise |
| Writes | `*.jws` + one line in the anchor log | **nothing** |
| Runs | the operator's workstation, never in CI | anywhere, offline |

**Hard rule: the verifier never imports the signer.** No code path in the
verifier can reach a private key. That is statically checkable, and it will be
a test.

### Private key custody

The 32-byte seed goes into the workstation's existing secret store
(`XML/secrets.cartography.xml`, CLIXML/DPAPI), with an off-machine backup.
**Never** in Git, in an archive, in an example, in an environment variable
written to disk, nor in a CI secret — signing is not a continuous-integration
step.

A key **distinct from RGC's**, deliberately: same mechanism, same format, same
verification path, but two custodies. Reusing RGC's key would mean touching
production to sign an Evidence package, and would make one compromise an
incident shared by both products.

## 2.7 The dependency question, answered plainly

Evidence promises dependency-free verification. Ed25519 is unverifiable in the
standard library. Three paths, and I take all three:

1. **`cryptography` present** → full verification. A maintained, audited
   component, and **already in the project's stack**: no new vendor.
2. **`cryptography` absent** → `NOT TESTED`, with the reason and the install
   line. The 21 existing integrity controls remain intact and dependency-free.
   Never a `PASS`, never a `FAIL`.
3. **Documented `openssl` path** → the auditor verifies our signature with a
   tool that is not ours. **Demonstrated working.**

**I will not vendor a pure-Python Ed25519 implementation.** Writing our own
cryptography to preserve a "zero dependency" slogan would trade a real
guarantee for a cosmetic one.

---

# Phase 3 — Acceptance tests, defined and not executed

## The brief's ten

| # | Case | `signature` | `trust` | `agreement` | Derived level |
|---|---|---|---|---|---|
| 1 | valid archive, valid signature, known anchor | `PASS` | `PASS` | `PASS` | **`cryptographically_attested`** |
| 2 | archive modified after signing | `PASS` | `PASS` | **`FAIL`** | none — refused |
| 3 | forged signature | **`FAIL`** | — | — | none — refused |
| 4 | unknown public key | `NOT TESTED` | `NOT TESTED` | `PASS` | `reference_verifiable` |
| 5 | valid signature, external anchor absent | `PASS` | `PASS` | `PASS` | `cryptographically_attested`, **anchoring `NOT TESTED`** |
| 6 | anchor present but not matching | `PASS` | `PASS` | `PASS` | **`FAIL`** on anchoring |
| 7 | archive fully recomputed after deleting one observation | `PASS` | `PASS` | **`FAIL`** | none — the case the signature **closes** |
| 8 | malformed signature metadata | **`FAIL`** with a reason, never a traceback | — | — | none |
| 9 | unsigned historical archive | `NOT TESTED` | `NOT TESTED` | n/a | **`reference_verifiable` preserved** |
| 10 | regression on GROUNDED-S1 and existing suites | 19/0/2 and 10/0/8 **unchanged** | | | |

**Case 7 is what justifies this whole piece of work.** It is the falsification
suite's declared limit since 5 November: "one observation erased everywhere,
counts and checksums redone" is undetectable **inside** the archive. A signed
attestation over the original digest detects it. It is the first time a
declared product limit closes.

**Case 9 is the non-regression guarantee for the existing estate.** An
unsigned archive is not rejected: it keeps `reference_verifiable`. The absence
of an attestation is not a defect of the archive.

## Six tests the brief does not list, which follow from the design

| # | Case | Expected |
|---|---|---|
| 11 | `alg` forged in the header (`none`, `HS256`) | `FAIL` — the verifier imposes `EdDSA` and never reads `alg` to choose |
| 12 | the examples' test key, without `--allow-test-keys` | `FAIL` on trust |
| 13 | `compromised`: signature predating the revocation | `FAIL` — unlike `rotated` |
| 14 | `rotated`: signature predating the revocation | `PASS` |
| 15 | `cryptography` absent from the environment | `NOT TESTED`, and the 21 controls unchanged |
| 16 | the verifier reaches no private key | statically checked on the import graph |

## Two cross-cutting rules, explicitly tested

- **Never a `PASS` over an empty set of controls.** Already applied since
  5 November, to be extended to the new lines.
- **The three states stay distinct**, in text and in JSON alike.

---

# Phase 4 — Residual risks, cost, and what remains to decide

## Residual risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R-1 | **No trusted clock before tier B.** `issued_at` is declared, so expiry rests on our word | **high** | tier B; and say so on every run |
| R-2 | **A signature is not the truth of the content.** A perfect attestation over a fabricated archive is valid | **high** | three separate lines; `truth of the content` always `NOT TESTED` |
| R-3 | At tier A we are both issuer and keeper of the log | high | tier B; publish the store's digest on a second channel |
| R-4 | A key compromise is **retroactive** | high | `kind: compromised` invalidates everything; written rotation procedure |
| R-5 | Trust store and anchor log served from the **same** source | medium | publish the store's digest on the .org site and the MCP card |
| R-6 | GitHub organisation **not verified** (`is_verified: false`) | medium | never invoke GitHub as corroboration of identity |
| R-7 | `cryptography` version drift on the verifier's side | low | the `openssl` path, independent of our stack |
| R-8 | Loss of the private key | medium | off-machine backup; a loss does not invalidate past signatures |

## Cost and maintenance complexity

| Item | Estimated size |
|---|---|
| `sign.py` | ~150 lines |
| verifier extension | ~200 lines |
| trust store + anchor log | ~80 lines |
| schemas | 2 — attestation, trust store |
| tests | ~400 lines, 16 cases |
| documentation | 2 EN/FR pairs |

**Dependencies added: one**, `cryptography`, already present in the project's
stack, and **optional** on the verifier's side.

**The recurring cost is not code, it is custody discipline.** A key rotation
requires: generate, record in the store, mark the old one `rotated`, commit,
and never reuse a `kid`. Tier B adds a network submission at sealing, never at
verification.

## What remains to decide, and I do not decide

1. **Tier B, and which one.** OpenTimestamps is my recommendation; it
   introduces a network submission and an external dependency at sealing.
2. **The signer's identity.** `neomundi-evidence-signer` is a technical name.
   Which of the **three legal entities** commits — the French association,
   Louis M Sàrl, or the GitHub organisation? A signature is a commitment; that
   question is legal before it is technical.
3. **Retroactively attest the frozen archives?** It is possible without
   touching them, and would close case 7 across the existing estate. But an
   attestation issued on 5 December over a 5 November archive attests
   **custody on 5 December**, not origin — and must say so.
4. **Publish the trust store somewhere other than this repository**, to lift
   R-5.

---

## What this proposal does not establish

No code has been written. The sixteen tests are **defined, not executed**. The
line counts are **estimates**. The only thing measured is the feasibility
probe of the cryptographic component, whose keys were ephemeral and have been
erased.

Neither the API, nor Station, nor the frozen corpora, nor Sergei's campaigns
were touched: this phase was read-only, and stayed that way.

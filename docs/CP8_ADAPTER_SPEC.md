<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="CP8_ADAPTER_SPEC.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# External receipt adapter — specification

**Specification only. No code is written, and nothing is integrated into
Evidence's cryptographic engine.**

Originating case: a "CP8" validation receipt sent by an external pilot
concerning CVE-2026-112244. We hold an **HTML document**; the full
`RECONCILIATION.md` report is expected and **has not been received**.

---

## Why an adapter, and not an integration

An external receipt is a **third party's declaration**. Integrating it into
the attestation engine would grant it the standing of objects we sign
ourselves, which is exactly the conflation this product refuses.

The adapter therefore stays **at the periphery**: it imports, qualifies and
reconciles — and it modifies neither `verify.py`, nor
`verify_attestation.py`, nor the trust store, nor the four assurance levels.

---

## Three statuses, never to be merged

This is the core of the specification. Every imported field gets exactly one
of these, and the report keeps them apart.

| Status | Means | Example in this case |
|---|---|---|
| **Primary evidence** | an object whose digest or signature we recompute ourselves | an attested Evidence archive, a recomputed `record_sha256` |
| **External declaration** | a fact asserted by the third party that we could not recompute | "two independent executions on local fixtures" |
| **Verified conclusion** | a statement we established by confronting a declaration with primary evidence | "the receipt's `g_score` differs from NeoMundi measurement `X`" |

**An HTML receipt is not primary evidence.** It does not become so by
carrying a "receipt hash": a digest computed by the issuer and published by
the issuer attests nothing beyond its own internal consistency.

> **Explicit prohibition:** never describe this HTML receipt as
> "cryptographically signed". No signature was produced, no key was supplied,
> and no verification was performed. Until a signature and a public key are
> received and verified, the receipt remains an **external declaration**.

---

## The adapter's six steps

### 1. Import

Input: the third party's document, as received, **unretouched**.

- SHA-256 of the received file, computed by us and retained;
- date and channel of receipt, **declared by us** and marked as such;
- no normalisation of the content: a reformatted receipt is no longer the
  receipt received.

An extractor reads the HTML and produces a **field object**, where every
field carries its source path in the document. A field whose path does not
resolve is `absent`, never `null` — the same distinction as an unmeasured
signal.

### 2. Verify what is verifiable

| Element the receipt announces | What the adapter does with it |
|---|---|
| a receipt hash | recomputed over the received bytes → **PASS / FAIL** |
| log digests | recomputable **only if the logs are supplied**; otherwise `NOT TESTED` |
| a signature | `NOT TESTED` until a public key is received; then verifiable through the same Ed25519/JWS path as our attestations |
| "two independent executions" | **never verifiable** from a document: `NOT TESTED`, permanently |
| a concordant result | `NOT TESTED`: a third party's internal concordance is not our measurement |

Rule: **no `PASS` over an empty set.** A receipt from which nothing is
recomputable yields an entirely `NOT TESTED` report, and that report is a
valid result — not a failure.

### 3. State its limits

For each receipt, the adapter produces an explicit list of what it could not
establish. For the present case, as it stands today:

- the `RECONCILIATION.md` report **was not supplied**;
- no public key accompanies the receipt;
- the logs whose digests are announced **are not attached**;
- the local fixtures of the two executions are not attached;
- nothing yet ties the receipt to a `request_id` or an observation on our
  side.

### 4. Tie it to a NeoMundi measurement — and only on real concordance

**The link is never made by plausible resemblance.** Three routes, in
decreasing order of strength:

| Route | Requires | Strength |
|---|---|---|
| **by digest** | a receipt digest equals a digest our record declares (`response_sha256`, `prompt_sha256`, `request_sha256`) | **strong** — this is `bind.py`'s mechanism, reused as is |
| **by identifier** | a `request_id`, `observation_id` or `measurement_id` present on both sides and found in our corpus | medium — an identifier is declarative |
| **none** | neither a common digest nor a common identifier | **the link is refused** |

Closeness of date, model or value **does not constitute a link**. An adapter
that linked on that basis would manufacture the evidence it claims to verify.

> Context to be checked rather than assumed: a `401` from `/v1/govern` leaves
> **no trace** server-side, and `observation_id` has never existed in our API
> responses. If the receipt carries only an identifier of that kind, the
> "by identifier" route may be structurally impossible, and that should be
> said rather than searched for longer.

### 5. Produce a field-by-field reconciliation table

One row per field, five columns, and no "overall verdict" column.

| Field | Receipt value | NeoMundi value | Status | Basis |
|---|---|---|---|---|
| `g_score` | `0.3863` | `0.594` | **DIVERGENT, preserved** | both values kept as they are |
| `cve` | `CVE-2026-112244` | *(to be resolved)* | external declaration | — |
| receipt hash | *(declared)* | recomputed by us | PASS / FAIL | received bytes |
| log digests | *(declared)* | — | NOT TESTED | logs not supplied |
| "two executions" | *(declared)* | — | NOT TESTED | not verifiable from a document |

### 6. Preserve divergences, without picking one

**`0.3863` against `0.594` remains a two-valued divergence.**

The adapter does not decide, average, arbitrate, or mark one "correct". It
records both, their sources, and what would be missing to settle it.

What is missing is itself known:

- the `request_id` of the NeoMundi measurement concerned;
- the `measurement_version` on each side — two different versions cross a
  comparability boundary, and the values then no longer compare;
- the **measurement coverage** on each side: two measurements with different
  coverage do not compare signal by signal.

> An internal note separately establishes that `stability_score` is **not a
> signal** but an aggregate (`G / 0.60`), and that an `energy_score`
> republishes the retained aggregate. A `g_score` divergence may therefore
> come from a **difference of definition** rather than of computation. The
> adapter must record the definition used on each side before qualifying the
> gap.
>
> **No G-score computation is modified, nor recomputed, by this adapter.**

---

## What the adapter will never do

- artificially reconstitute the third party's results;
- fill an absent field with a plausible value;
- describe as "signed" anything whose signature has not been verified;
- raise an assurance level on the strength of an external declaration;
- settle a divergence the data does not settle;
- modify the cryptographic engine, the trust store, or the four levels.

---

## Proposed interface, and its isolation

```sh
# None of these programs exists: this is the specification.
python adapters/receipt_import.py <receipt.html> --out receipt.json --received-at <date>
python adapters/receipt_verify.py receipt.json [--logs <directory>] [--public-key <jwk>]
python adapters/reconcile.py receipt.json --archive <evidence_archive.zip> \
       --observation <observation_id> --out reconciliation.md
```

Three programs, a separate `adapters/` directory, and **no import from
`verify_attestation.py` or `sign.py`**. The adapter may read `bind.py` to
reuse digest-based linking; the reverse is forbidden.

Schemas to version on the day of implementation:
`neomundi.evidence.external-receipt/1` and
`neomundi.evidence.reconciliation/1`.

---

## Prerequisites to implementation

1. **Receive `RECONCILIATION.md`.** Without it, the adapter would be designed
   from a single document and a conjecture.
2. **Obtain the public key** if a signature is claimed. With no key, the
   signature stays `NOT TESTED` forever.
3. **Obtain the logs** whose digests are announced, otherwise those digests
   remain declarative.
4. **Identify the NeoMundi measurement concerned**, by a `request_id` or a
   digest. Without that, step 4 refuses the link and the reconciliation table
   has no "NeoMundi" column.

**None of this is in our hands alone.** That is why the specification is
delivered before the code: building the adapter now would produce a tool
whose main branch could not be exercised.

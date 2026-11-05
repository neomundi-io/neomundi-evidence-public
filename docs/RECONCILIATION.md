<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="RECONCILIATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Reconciliation — confronting an external receipt with a NeoMundi measurement

Originating specification: [`CP8_ADAPTER_SPEC.md`](CP8_ADAPTER_SPEC.md). This
document describes the **implementation**.

---

## What reconciliation establishes

**Nothing, by itself.** It *confronts*, and it **keeps both sides**.

| | |
|---|---|
| An external receipt | a **declaration** |
| Our archive | **primary evidence**, insofar as we recompute its digests |
| A demonstrated agreement | a **verified conclusion** |

Mixing them would produce exactly the conflation this product refuses. The
report carries the three classes explicitly.

---

## The five statuses

| Status | Means |
|---|---|
| **`MATCHED`** | both sides present, comparable, and equal |
| **`MISMATCHED`** | both sides present, comparable, and **different** |
| **`MISSING`** | one side absent |
| **`NOT VERIFIABLE`** | present, but its **verification** needs material we do not have |
| **`NOT COMPARABLE`** | both sides exist, and a **comparability boundary** is crossed |

### `NOT VERIFIABLE` and `NOT COMPARABLE` do not say the same thing

This is the easiest distinction to lose, and the first version of this tool
lost it — it routed both to `NOT COMPARABLE`.

- **`NOT VERIFIABLE`**: the receipt announces a log digest, and the log is not
  attached. **Our inability to check.**
- **`NOT COMPARABLE`**: the receipt says `concordant`, we say `measured`. Two
  distinct statements whose comparison would be meaningless.

---

## Comparability comes **before** value

> Two different values are a **computation** divergence only if they measure
> the **same thing**: same definition, same measurement version, same
> coverage.

Otherwise they do not compare, and concluding an anomaly would be **a
reasoning error, not a discovery**. The boundary is therefore evaluated first,
and a non-comparable field is **never** declared `MISMATCHED`.

```
FRONTIERES DE COMPARABILITE -- evaluees AVANT les valeurs :
  - version de mesure du recu NON DECLAREE -- impossible d etablir la comparabilite
  - couverture de mesure du recu NON DECLAREE -- impossible d etablir la comparabilite
  - definition du score du recu NON DECLAREE -- impossible d etablir la comparabilite
```

### But a digest still matches

The boundary bites only on **measured values**. Each correspondence declares
its **kind**:

| Kind | Sensitive to measurement context? |
|---|---|
| `digest` | **no** — a digest matches or it does not |
| `identifier` | **no** |
| `measured_value` | **yes** |
| `statement` | no, though often non-comparable for other reasons |

**This was a defect in my first version**: an undeclared measurement version
made *every* field `NOT COMPARABLE`, including a digest that matched —
destroying the strongest evidence available. A regression test locks it
(case 10).

---

## Linking: three routes, and no fourth

| Route | Requires | Strength |
|---|---|---|
| **by digest** | a receipt digest equals a digest our record declares | **strong** |
| **by identifier** | an identifier present on both sides and found in our corpus | medium — an identifier is declarative |
| **refused** | neither | — |

**Closeness of date, model or value does not constitute a link.** An adapter
linking on that basis would manufacture the evidence it claims to verify.

And **a requested observation is not a demonstrated correspondence**:
`--observation` forces nothing, and the report says the link was refused.

---

## No correspondence is guessed

The importer collects **candidate fields** with their source paths and
**interprets nothing**. Deciding that a third party's `g_score` corresponds to
ours is a claim about two definitions; no extractor can make it.

The correspondence must therefore be **declared** in an explicit table, and
every entry must say **why** (`basis` is mandatory). Without an entry, a
receipt field is simply **left aside**, and a targeted field is
`NOT COMPARABLE`.

A table targeting a field that does **not exist** on our side is refused
**loudly** — never reported as a silent `MISSING`.

---

## Use

```sh
# 1. import, without interpreting
python adapters/receipt_import.py receipt.html \
    --received-at 2026-11-05T12:00:00Z --out receipt.json

# 2. reconcile, with an EXPLICIT table
python adapters/reconcile.py receipt.json \
    --archive <evidence_archive.zip> \
    --map examples/reconciliation/map-comparable.json \
    --supplied "le journal d execution 1" \
    --out reconciliation.md --json reconciliation.json --strict
```

`--received-at` is **required**: the tool does not read the clock, and that
date is not an attested date — it is when *we* received.

`--supplied` declares the material actually provided. A field requiring
something absent returns `NOT VERIFIABLE`.

`--strict` returns **code 2** if a field remains unestablished, **without
changing any status**.

---

## `bind.py` is reused, not rewritten

Digest-based linking — the only strong one — is `bind.py`'s: `lire_sujet()`
returns the digests the record declares. **No second engine is written**, and
a test checks it on the call graph (case 23):

```
appels a bind : charge, lignes_jsonl, lire_sujet
```

---

## The CP8 case — what is ready, and what is missing

### What the adapter can already do

Import an HTML receipt, collect its fields and digests, link it by digest or
identifier, produce a field-by-field table, and **preserve contradictions**.

The synthetic fixture deliberately carries **`0,3863`** and **`0,594`**: both
values appear as they are in the report, without conversion, and neither is
designated correct.

### What is not verifiable today

| Element | State |
|---|---|
| **`RECONCILIATION.md`** | **not supplied.** The adapter is therefore designed on the described shape, not on the package |
| The CP8 HTML receipt itself | **not transmitted in this piece of work.** The fixture is entirely **synthetic** |
| The logs whose digests are announced | not attached → `NOT VERIFIABLE` |
| A signature | **no public key**, no signature recognised → the receipt is **never** described as signed |
| The two executions' fixtures | not attached |
| The receipt's measurement version | **not declared** → every measured value is `NOT COMPARABLE` |

### Why `0.3863` against `0.594` is **not** concluded

Because the conditions for the comparison are not met. What is missing:

1. the `request_id` or digest tying the receipt to a precise measurement;
2. the `measurement_version` on each side — two versions cross a comparability
   boundary;
3. the **measurement coverage** on each side — two measurements with different
   coverage do not compare signal by signal;
4. the **definition** used on each side.

> An internal note separately establishes that `stability_score` is **not a
> signal** but an aggregate (`G / 0.60`). A gap may therefore come from a
> **difference of definition** rather than of computation. The adapter records
> the declared definition on each side before qualifying anything.
>
> **No G-score computation is modified or recomputed.**

---

## Test matrix — 24/24

`python tests/test_reconciliation.py` — self-contained, the fixture is built.

| # | Case | Result |
|---|---|---|
| 1-3 | import: fields, digests, **verbatim** values with source paths | 13 fields, all traced |
| 2 | **no signature recognised or declared** | `signatures: []`, limit written |
| 4 | **the five statuses are distinguished** | 4 `MATCHED`, 2 `MISMATCHED`, 1 `MISSING`, 1 `NOT COMPARABLE`, 1 `NOT VERIFIABLE` |
| 5 | link by **digest** | a receipt digest lands on a declared digest |
| 6-7 | contradictions preserved, **`0,3863` and `0,594` as they are** | both sides present, no conversion |
| 8 | **decimal comma** read | gap computed |
| 9 | no context: measured values do not compare | `NOT COMPARABLE` |
| 10 | **but a digest still matches** | `MATCHED` — regression locked |
| 11 | **no correspondence guessed** | 5 receipt fields left aside |
| 12 | table targeting a nonexistent field | **loud refusal**, not a `MISSING` |
| 13 | duplicate label | refused |
| 14-15 | unknown receipt / table schema | refused, not interpreted |
| 16 | **6 hostile inputs** (empty, truncated, 200 nested rows, injected script, non-UTF-8 bytes, non-object JSON) | **6/6**, no traceback |
| 17 | injected script | content stays **data**, never an instruction |
| 18 | nothing in common | **link refused** |
| 19 | **requested** observation | refused — a request is not a correspondence |
| 20 | `--strict` | code 2, **9 identical lines** |
| 21-22 | Markdown report | three evidence classes; **no machine path** |
| 23 | **`bind.py` reused** | `lire_sujet`, `lignes_jsonl`, `charge` |
| 24 | the receipt is **never** described as signed or verified | no abusive qualification |

---

## What reconciliation will never do

- **Settle** a divergence the data does not settle.
- **Average**, arbitrate, or designate a correct value.
- **Describe as "signed"** anything whose signature has not been verified.
- **Raise an assurance level** on the strength of an external declaration.
- **Guess** a correspondence.
- **Artificially reconstitute** a third party's results.
- **Fill** an absent field with a plausible value.

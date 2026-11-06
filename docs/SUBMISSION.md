<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="SUBMISSION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Submitting an execution package, and verifying it independently

For a pilot who wants their execution records handled by NeoMundi Evidence.
Everything here runs locally, on the standard library, with **no private key
and no network**.

> **What ingestion establishes, and what it cannot.** It recomputes the
> digests and sizes of the files you declare, checks the structure of your
> manifest, and verifies any signature you already hold against the published
> trust store. It establishes **nothing else** — and it never promotes a
> declaration into an attested fact.

---

## 1. The package

A directory, or a ZIP of it, with a manifest at the root:

```
mon-paquet/
    submission.json          <- the manifest, schema neomundi.evidence.submission/1
    artefacts/
        prompt.txt
        response.txt
        measurement.json
```

Generate a working example to copy from:

```sh
python tests/make_submission.py mon-paquet --profil valide
```

`submission.json` declares who you are, what you executed, and one entry per
file with its `sha256`, its size in bytes and its `role`. The full contract is
in [`schemas/evidence-submission-v1.json`](../schemas/evidence-submission-v1.json),
and every field name there ends in `_declared` when it is your word rather
than something we recompute. That suffix is not decoration: it is the line
between the two registers.

**Paths are relative, with forward slashes, no `..`.** Absolute paths, drive
letters, backslashes and symbolic links are refused — a package must not be
able to name a file outside itself.

## 2. Ingestion

```sh
python adapters/ingest.py mon-paquet \
       --out rapport.json --md rapport.md \
       --trust-store trust/trust-store.json
```

`--trust-store` is needed only if your package declares attestations. Supply
**the operator's store**, never one carried inside the package: a package must
not carry its own answer to whether its signer is trustworthy.

### Three verdicts, and they are not interchangeable

| Verdict | Exit | Meaning |
|---|---|---|
| **`ACCEPTE`** | `0` | structure sound, every declared digest recomputed and matching |
| **`INCOMPLET`** | `0`, or `2` with `--strict` | **not a refusal.** Something is missing that *you can supply* — a declared artefact absent, or an attestation declared with no store given |
| **`REJETE`** | `1` | a control failed. A digest that does not match, a required field missing, a path reaching outside the package, a signature that does not verify |

The distinction between `INCOMPLET` and `REJETE` is deliberate. Treating a
missing file as fraud would turn away a pilot acting in good faith; treating a
wrong digest as a gap would let a false package through.

## 3. The three registers of the report

Every line carries its nature, and that is the whole design. **These three
labels, and the three verdicts, are contract terms: they are printed verbatim
in both languages and never translated** — exactly like `PASS`, `FAIL` and
`NOT TESTED`. A JSON report whose field values changed with `--lang` would not
be comparable across readers.

| Nature | What it means |
|---|---|
| **`CONTROLE`** | we recomputed it. Digests, sizes, structure, signatures. The only register where we commit to anything |
| **`DECLARE`** | your word, kept **verbatim**. Identity, model, execution conditions. We carry it; we do not endorse it |
| **`NON DEMONTRABLE`** | no control could establish it from this package. Not a lack of diligence — a property of the material |

**No `DECLARE` line can ever read `PASS`.** Case 13 of
[`tests/test_ingestion.py`](../tests/test_ingestion.py) fails if one ever
does. Without that lock, writing "model X" in a manifest would be enough for
the report to present it as checked.

### What stays NOT DEMONSTRABLE, whatever you send

- **that the execution took place.** We recompute digests of *files*. That
  they came from the run you describe is a declaration, and will remain one.
- **who produced the package.** Nothing inside a file establishes who wrote
  it.
- **that the artefacts are the ones from that run.** Matching digests
  establish that the files have not moved since the manifest was written.
  That is a real guarantee, and a narrower one than it looks.
- **the date.** `submitted_at_declared` is yours; no trusted clock takes
  part.
- **the meaning of your fields.** Deciding that one of your scores
  corresponds to one of ours is a claim about two definitions. It needs a
  **declared** mapping table — see
  [`adapters/reconcile.py`](../adapters/reconcile.py), which refuses to guess.

## 4. Verifying independently, without us

If your package carries an attestation signed by NeoMundi Recherche, you can
check it yourself — offline, from public material only:

```sh
# 1. the trust store, from the repository
curl -O https://raw.githubusercontent.com/neomundi-io/neomundi-evidence-public/main/trust/trust-store.json

# 2. its digest, from a DIFFERENT channel -- this is the step that matters
curl https://mcp.neomundi.org/trust/trust-store-digest.json

# 3. confront, then verify
sha256sum trust-store.json          # must equal the `sha256` field above
python verify_attestation.py <attestation.jws> --archive <subject> \
       --trust-store trust-store.json --store-digest <digest from step 2>
```

Taking both the store and its digest from the same place proves only that one
source agrees with itself. See [`trust/README.md`](../trust/README.md).

## 5. Security, as implemented

| | |
|---|---|
| **No code from your package is ever run.** | ingestion reads bytes and hashes them. Nothing is imported, executed or interpreted |
| **No private key is needed**, ever | checked statically: `adapters/ingest.py` imports neither `sign.py` nor `cryptography` |
| **Your package is never modified** | a ZIP is unpacked into a temporary directory and that copy is read |
| **Path traversal is refused before extraction** | a ZIP member named `../../x` is rejected *before* anything is written — learning it during extraction would be too late |
| **Bounded** | 512 artefacts, 64 MiB per file, 256 MiB total, 4096 ZIP members. A package declaring more uncompressed bytes than the cap is refused on its own declaration |
| **Symbolic links are refused** | a link passes a path pattern and still leaves the package |

## 6. The limits worth stating plainly

An `ACCEPTE` package is **exploitable**, not **proven**. It means its
structure holds and its declared digests are ours to recompute. Anything
about the execution itself remains your declaration.

And an attestation verified under this chain is signed under
`legal_capacity_to_attest: experimental` — the entity is named and has
decided, and **no verification of its powers has been performed**. It is
never a legal certification. The verifier says so on every run.

## 7. If your package comes from a Station export

A `station.export.campagne` export is read by a second tool, which walks the
chain **Execution → Measurement → Evaluator → Configuration → Export →
Evidence**:

```sh
python adapters/provenance.py <export.zip> --out provenance.json --md provenance.md
```

It returns an **instrumental provenance level**:

| Level | What it says |
|---|---|
| `instrument_non_documente` | the export does not document its evaluators. The signals stay usable; what falls away is what can be **claimed** about how they were obtained |
| `instrument_declare` | evaluators are named, with no configuration fingerprint |
| `instrument_declare_et_configure` | named **and** configured |

**There is no fourth level.** That the declared evaluator is the one that ran
would require observing the measurement: a permanent `NOT TESTED`.

The report speaks the **same nature vocabulary** as ingestion — `CONTROLE`,
`DECLARE`, `NON DEMONTRABLE` — so it plugs into this chain without
translation. An absent evaluator is there **neither a measurement failure nor
a favourable score**: it produces no `FAIL`.

Contract detail: [`R6_PROVENANCE_CONTRACT.md`](R6_PROVENANCE_CONTRACT.md).

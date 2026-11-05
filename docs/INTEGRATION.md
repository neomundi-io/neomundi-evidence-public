<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="INTEGRATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Integrating Evidence — exit codes, strict mode, reports

For anyone automating verification. If you read a report with your eyes, the
text output is enough and this document is not for you.

---

## The rule, in one sentence

> **Do not read the default exit code. Read the JSON report, or turn on
> `--strict`.**

All three tools exit **0** by default as soon as no control has failed —
including when controls **could not be performed**. That is deliberate:
`NOT TESTED` is not a failure, and treating absence of proof as proof of
absence would be wrong. But for a script, four very different situations then
return the same `0`.

---

## Exit codes

| Code | Means |
|---|---|
| **0** | no control failed. And, if `--strict` is on, every **required** guarantee is demonstrated |
| **1** | **at least one control failed.** The package, binding or attestation must not be presented as verified |
| **2** | no failure, but `--strict` is on and a **required** guarantee is not demonstrated |

**`1` wins over `2`.** A failure is the stronger statement; a consumer that
does not distinguish non-zero codes is not misled either way.

---

## The trap, without `--strict`

```sh
python verify_attestation.py a.jws --archive a.zip   # no trust store supplied
echo $?                                              # 0
```

Four situations return `0` and are not equivalent:

| Actual situation | Code | What a script would conclude |
|---|---|---|
| level `cryptographically_attested` reached | `0` | "attested" — **correct** |
| key unknown to the trust store | `0` | "attested" — **false** |
| `cryptography` absent from the environment | `0` | "attested" — **false** |
| no trust store supplied | `0` | "attested" — **false** |

The last three are **non-verifications**.

---

## `--strict`: what it does, and what it does not

```sh
python verify_attestation.py a.jws --archive a.zip --strict
echo $?                                              # 2
```

```
[NOT TESTED] signature cryptographique - aucun magasin de confiance fourni…
[NOT TESTED] identite de confiance - sans magasin, aucune confiance n est etablie

MODE STRICT : 2 garantie(s) requise(s) non demontree(s) :
  - signature cryptographique
  - identite de confiance
Aucun verdict n a change : ces lignes restent telles qu affichees.
Seul le code de sortie en tient compte (2).
```

**It changes no verdict.** Lines stay `PASS`, `FAIL` or `NOT TESTED`
identically — CI checks this by comparing the control lines, byte for byte,
with and without the flag. Turning a `NOT TESTED` into a `FAIL` would
reintroduce the merging of the three states this product forbids.

**The default stays non-strict**, so a human run keeps returning a diagnosis
rather than a refusal.

### Required guarantees, and guarantees out of reach

A guarantee is **required** when its `NOT TESTED` is **contingent**: it would
become `PASS` if you supplied what is missing.

| Tool | Required guarantees | How to satisfy them |
|---|---|---|
| `verify.py` | replayed-input digests | `--corpus <directory>` |
| `bind.py` | subject in its archive · claims exercised · each artifact · subject attestation | `--archive`, `--root`, `--attestation` + `--trust-store`, `--max-artifact-bytes` |
| `verify_attestation.py` | the **five pillars**: canonicalisation profile, imposed algorithm, signature, trust, agreement | `--archive`, `--trust-store`, and `cryptography` installed |

**Never** required are the **permanent** limits — they will never be `PASS`,
and demanding them would make strict mode always red, hence useless:

- the signer's **legal capacity** — no code establishes it;
- the **independent timestamp** — `attested_at_declared` is declared;
- **third-party anchoring** — not implemented;
- the **truth of the content** — a signature attests no fact;
- the **ledger chaining** — recomputing it here would be a second
  implementation;
- the **archive's origin** — no third-party signature, no anchor.

---

## Machine-readable reports

`--json <file>` on all three tools. **The text output stays identical: the
file is added, it replaces nothing.**

| Tool | Report schema |
|---|---|
| `verify.py` | `neomundi.evidence.verification-report/1` |
| `bind.py verify` | `neomundi.evidence.binding-report/1` |
| `verify_attestation.py` | `neomundi.evidence.attestation-report/1` |

Common fields, and the ones that matter:

```json
{
  "schema": "neomundi.evidence.attestation-report/1",
  "controls": [{"state": "PASS", "control": "…", "detail": "…"}],
  "counts": {"pass": 10, "fail": 0, "not_tested": 4},
  "strict": false,
  "required_not_demonstrated": [],
  "exit_code": 0,
  "attained_level": "cryptographically_attested",
  "does_not_establish": ["that the execution took place", "…"]
}
```

**What to read, in this order:**

1. **`counts.fail`** — if non-zero, stop there;
2. **`required_not_demonstrated`** — if non-empty, your verification is
   incomplete, whatever the exit code;
3. **`attained_level`** — `null` means **no level reached**, not "a low
   level";
4. **`does_not_establish`** — what the report, by construction, does not say.

**Never infer success from `counts.fail == 0` alone.** The three states are
three distinct fields precisely so they are not conflated.

### `strict` is carried in the report, on purpose

Without that field, two runs with the same verdict and different exit codes
would be indistinguishable after the fact.

---

## An example of a correct consumer

```sh
#!/bin/sh
set -e

python verify_attestation.py "$1" \
    --archive "$2" --trust-store "$3" \
    --json report.json --strict || code=$?

python - <<'PY'
import json, sys
r = json.load(open("report.json", encoding="utf-8"))
if r["counts"]["fail"]:
    sys.exit("REFUSED: %d control(s) failed" % r["counts"]["fail"])
if r["required_not_demonstrated"]:
    sys.exit("INCOMPLETE: %s" % ", ".join(r["required_not_demonstrated"]))
if r["attained_level"] != "cryptographically_attested":
    sys.exit("LEVEL INSUFFICIENT: %r" % r["attained_level"])
print("ATTESTED -- and this still does not establish:")
for limit in r["does_not_establish"]:
    print("  -", limit)
PY
```

That last block is not politeness: an integrator that displays "attested"
without saying what it does not establish reproduces exactly the overclaim
this product forbids itself.

---

## Continuous integration

`.github/workflows/tests.yml`, three jobs, on every pull request and every
push to `main`.

| Job | What it establishes |
|---|---|
| **`suites`** — Python 3.11, 3.12, 3.13 | the four suites pass; the verifier's baselines are **exact**; strict mode changes no verdict; codes 0/2 are as expected |
| **`sans-cryptography`** | `verify.py` is **indifferent** to the missing dependency; the signature returns `NOT TESTED`, never `PASS` or `FAIL`; the default returns 0 and strict returns 2 |
| **`discipline`** | `verify.py` and `canonical.py` import the standard library only; the verifier reaches **no** private key; no private material is tracked; the signer **refuses** to write a key under the repository root; all internal links resolve; every document has its EN/FR pair |

### CI does not use the demonstration archives, and why

`tests/make_fixture.py` builds an archive with **no link to any real
dataset**, deterministic byte for byte.

The finding that forces this is worth writing down. The GROUNDED-S1 archive
carries `dataset_id: medmcqa-single`, thirty real `item_id`s, and a
`reference_evaluations.jsonl` that crosses `extracted_answer` with `status`.
For its thirteen observations with status `correct`, **the reference label of
thirteen MedMCQA items is exactly recoverable**. Committing it would have
disclosed those labels — and that is already the reason this member was
excluded from the MED demonstration archive.

### What CI does not establish

**The published baselines are not checked in CI** — 19/0/2 on GROUNDED-S1,
10/0/8 on MED — because those archives are not on the runner. They remain a
**local** check:

```sh
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip --corpus <corpus>
#   expected: BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED   (21 lines)
python verify.py NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip
#   expected: BILAN : 10 PASS, 0 FAIL, 8 NOT TESTED   (18 lines)
```

The fixture returns the same counts (19/0/2 with corpus, 17/0/3 without),
which makes it an equivalent canary — but **it is not the same archive**, and
one must not be read for the other.

Three cases of the attestation suite — 9, 9b and 9c — are reported
**`INAPPLICABLE`** on the fixture: they rely on `examples/binding`, whose
manifest names the demonstration archive and carries its digest. An
inapplicable case is **neither a success nor a failure**, and the summary
counts them separately.

---

## What integration cannot give you

- **Proof that the execution took place.** No exit code carries it.
- **A reliable date.** `attested_at_declared` is declared by the signer.
- **The truth of the content.** A perfectly signed attestation over a
  fabricated archive is cryptographically valid.

Those three lines are `NOT TESTED` on every run, and they will stay that way.

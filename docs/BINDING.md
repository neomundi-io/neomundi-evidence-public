<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="BINDING.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Binding an observation to evidence

**A textual description of an execution is not proof that the execution took
place.** Everything on this page follows from that one sentence.

A NeoMundi measurement produces a record. The record declares digests of
objects that are **not inside the archive**: the response, the prompt, the
request. Binding means offering a file whose bytes hash to one of those
digests.

What that establishes: **this file is the one the record refers to.**
What it does not establish: that the execution happened, when, or at whose
hands.

---

## The four assurance levels

| Level | Means | Available today |
|---|---|---|
| `declared` | written in the document; nothing recomputed | yes |
| `reference_verifiable` | the artifact is present, and its bytes hash to a digest the record declares | **yes** |
| `cryptographically_attested` | a signature by an identified key verifies | **no** — nothing in this repository verifies a signature |
| `not_demonstrable` | out of reach of any local check | n/a — a statement, not an achievement |

**A manifest is a set of claims. The level is derived by the verifier, never
read from the document.** A manifest claiming more than it can show is
refused, and that is the single most important control in the tool:

```
[FAIL      ] aucune revendication ne depasse ce qui est demontre
             art-01 revendique `cryptographically_attested`, derive `reference_verifiable`
```

Why the derivation matters: without it, writing
`"claimed_assurance": "cryptographically_attested"` in a text file would make
a document look like proof.

---

## Use

### Build a manifest

```sh
python bind.py build \
    --archive NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
    --observation obs-4ccb376a… \
    --artifact response=response.txt \
    --artifact recording=responses/grounded-009.json \
    --statement "Replayed from the frozen recording of 2026-10-22." \
    --created-at 2026-11-05T12:00:00Z \
    --out manifest.json
```

`--created-at` is **required**, deliberately: the tool never reads the clock,
so two runs on the same inputs produce the same manifest, byte for byte.

`build` never claims more than it has just observed. A hand-written manifest
can still lie — which is the verifier's job to say.

### Verify a binding

```sh
python bind.py verify manifest.json \
    --archive NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
    --json report.json
```

Without `--archive`, the declared digests are not confronted with the record,
and the control reports `NOT TESTED` — never `PASS`.

| Option | Effect |
|---|---|
| `--root DIR` | where artifact paths resolve; defaults to the manifest's directory |
| `--archive FILE` | the Evidence archive of the subject, to confront declared digests with the record |
| `--json FILE` | an additional machine-readable report; the text output is unchanged |
| `--max-artifact-bytes N` | read ceiling per artifact, default 64 MiB. Beyond it, the artifact is `NOT TESTED` and not read |

Standard library only. No network. No write outside the requested output.

---

## What the verifier checks

| Control | On failure |
|---|---|
| manifest readable, and a known schema | `FAIL` |
| manifest shape: required fields, types, digest format, unique ids | `FAIL` |
| the archive supplied is the one the manifest names | `FAIL` |
| the subject observation exists in that archive, exactly once | `FAIL` |
| the subject agrees with the record (`record_sha256`, commit, comparability key) | `FAIL` |
| **the declared digests are the record's own** | `FAIL` |
| artifact path stays inside the root: no absolute path, no traversal, no outward symlink | `FAIL` |
| artifact present, and its bytes hash to what the manifest announces | `FAIL` |
| artifact bound to a digest the record actually declares | `FAIL` |
| artifact bytes hash to that declared digest | `FAIL` |
| **no claim exceeds what was demonstrated** | `FAIL` |
| signature verification | always `NOT TESTED` |
| attached statements | always `NOT TESTED` |
| execution truth | always `NOT TESTED` |

A missing artifact is `NOT TESTED`, not `FAIL`: its claim was not contradicted,
it was not exercised. The binding then falls back to `declared`, and the
report says so. Confusing the two would merge states this product keeps
separate.

The aggregate level of a binding is the **weakest** of its artifacts. Taking
the strongest would let an unanchored artifact be covered by its neighbour.

---

## The central test

`tests/test_binding.py` ends with the test that justifies the whole
mechanism: two manifests carrying **word-for-word identical** prose, one with
anchored artifacts beneath it and one without.

```
  Scenario A : 1 statement, 0 artifacts -> declared
  Scenario B : 1 statement, 2 artifacts -> reference_verifiable
```

Scenario A is neither refused nor accepted as proof: it is reported for what
it is, a declarative document. If the tool returned the same verdict for
both, it would be measuring prose instead of evidence.

The suite also runs 17 faulty manifests, each refused for its own distinct
reason. The one that matters most:

> **the artifact and the manifest rewritten in concert** — a forger who
> recomputes the digest of a forged artifact and writes it everywhere in the
> manifest gets an internally consistent document. Only confronting it with
> the **record** catches it. That is why `declared_digests` must be
> confronted, not merely copied.

---

## Terminology

Words carry the product's rigour. These are used in one sense only, here and
in the code.

| Term | Means | Does not mean |
|---|---|---|
| **Measurement** | the five signals computed by the NeoMundi engine for one observation | a judgement on the answer's substance; never a medical, legal or factual validation |
| **Observation** | one recorded exchange: request sent, response received, as sealed in the ledger | the execution itself |
| **Artifact** | a file offered as an external object the record refers to | proof of anything on its own |
| **Manifest** | a document that *claims* a binding between an observation and artifacts | a verified result |
| **Integrity verification** | recomputing a digest over delivered bytes and comparing | authenticity |
| **Signature verification** | checking a signature against an identified key — **not implemented here** | integrity verification |
| **Provenance** | the chain of what produced an object, insofar as it is recomputable | a declaration of origin in a text field |
| **Execution reconstruction** | rebuilding a *documentary* account of an execution from records | the execution having happened |
| **Execution replay** | running the same inputs again through the same code to obtain a comparable result | obtaining identical bytes |
| **Execution truth** | that the execution really took place, at that time, at that operator | anything this repository can establish |

Two pairs are routinely conflated, and must not be:

- **integrity ≠ authenticity.** A digest that recomputes says the bytes did not
  move. It says nothing about who produced them.
- **reconstruction ≠ replay ≠ truth.** The first is documentary, the second is
  computational, the third is historical. This repository does the first,
  not the second, and cannot do the third.

---

## Limits

- **No signature is verified.** `cryptographically_attested` is therefore
  unreachable today, and the verifier states this on every run.
- **`created_at` and `declared_origin` are declared** by the manifest's author
  and contradicted by nothing. No trusted clock is involved.
- **A forger who rebuilds both the archive and the artifacts** produces a
  consistent set. Only a digest kept elsewhere than with it detects that.
- **No URL is ever resolved.** Artifacts are local files under an explicit
  root; nothing is fetched.
- **A binding says nothing about the quality of an answer.** It ties files to a
  record. The measurement remains a measurement.

---

## Files

| | |
|---|---|
| `bind.py` | build and verify a binding |
| `schemas/evidence-manifest-v1.json` | the manifest schema, with the levels defined in it |
| `examples/binding/` | a real binding: two artifacts, both anchored |
| `tests/test_binding.py` | 1 positive case, 17 negative, 1 scientific |
| `demo_binding.sh` | the three verdicts, side by side |

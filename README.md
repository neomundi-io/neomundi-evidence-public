<div align="center">

<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="README.fr.md">Français</a></sub>

[Station — Observe & Experiment](https://github.com/neomundi-io/neomundi-station-public) ·
[Runtime Measurement — Measure & Integrate](https://github.com/neomundi-io/neomundi-runtime-measurement) ·
**[Evidence — Verify & Reconstruct](README.md)** ·
[Use Cases — Applications, Pilots & Evidence](https://github.com/neomundi-io/neomundi-use-cases) ·
[ControlTower — Create an Account](https://controltower.neomundi.io/welcome)

<sub>[NeoMundi GitHub organization](https://github.com/neomundi-io)</sub>

# NeoMundi Evidence

### Capture what happened. Verify what can be proven.

**An evidence file for an instrumented AI qualification campaign — exportable,
readable, and checkable by its recipient without us.**

[![Evidence: V0.1](https://img.shields.io/badge/Evidence-V0.1-475569?style=flat-square)](#what-an-evidence-file-contains)
[![tests](https://github.com/neomundi-io/neomundi-evidence-public/actions/workflows/tests.yml/badge.svg)](https://github.com/neomundi-io/neomundi-evidence-public/actions/workflows/tests.yml)
[![Independent Verification](https://img.shields.io/badge/Independent_Verification-no_dependencies-0f766e?style=flat-square)](#verify-an-evidence-file)
[![Integrity: SHA-256](https://img.shields.io/badge/Integrity-SHA--256-0f766e?style=flat-square)](docs/EXTERNAL_REFERENCE.md)
[![Tamper Detection: 10/10 tested](https://img.shields.io/badge/Tamper_Detection-10%2F10_tested-0f766e?style=flat-square)](#tamper-detection-tests)
[![Verification: standard library](https://img.shields.io/badge/Verification-standard_library_only-0f766e?style=flat-square)](verify.py)
[![Demonstrations: 2](https://img.shields.io/badge/Demonstrations-synthetic_%2B_medical-2563eb?style=flat-square)](#the-two-demonstrations)
[![Status: external review candidate](https://img.shields.io/badge/Status-external_review_candidate-a16207?style=flat-square)](#the-four-categories)
[![License: all rights reserved](https://img.shields.io/badge/License-all_rights_reserved-6b7280?style=flat-square)](#licence)

**[Verify an evidence file](#verify-an-evidence-file)** ·
[Demonstration A — synthetic](docs/DEMO.md) ·
[Demonstration B — medical](docs/MED_DEMO.md) ·
[Five-minute demo](docs/DEMO_SCRIPT_5MIN.md) ·
[Reproduce the demo](docs/DEMO.md) ·
[Corpus reference](docs/CORPUS_REFERENCE.md) ·
[External reference](docs/EXTERNAL_REFERENCE.md) ·
[Limitations](#limitations) ·
[Future site](docs/FUTURE_SITE.md)

<sub>Start with <b>verify.py</b>: one file, standard library only, no network
call, nothing to install. It is meant to be <b>read</b> before it is run —
that is the condition of an independent check.</sub>

</div>

---

## Limitations first

They come first because an evidence product that lists its functions before its
limits is a brochure, not an instrument.

| This file does **not** prove | Why |
|---|---|
| the origin of an archive | no third-party signature, no external anchoring |
| the time of an event | `recorded_at` is **declared by the caller**; the ledger attests what it was told |
| that a chain was not rewritten in full | an entirely rebuilt chain verifies perfectly; only a hash kept elsewhere detects it |
| the correctness of the measured signals | the existence of a score does not establish its validity |
| what an AI did in production | V0.1 covers **campaigns**, never live client API traffic |
| regulatory compliance | no certification, no claim of legal admissibility |

**A SHA-256 hash is not a proof of truth.** It establishes that a received file
is the one whose hash was received. Nothing more.

---

## The four categories

Every claim in this repository sits in exactly one of these, and is never
presented as belonging to another.

| Category | Meaning | What is in it |
|---|---|---|
| **DEMONSTRATED** | executed, measured, with an output to show | producing an evidence file · independent verification · ten tamper detections · the frozen corpora · the timed demo |
| **EXPERIMENTAL** | it works, but on few cases, or without enough hindsight to rely on | the enriched archive (export schema `/2`, days old, one campaign exported) · the execution-regime guard · re-deriving input-recording hashes (one corpus only) |
| **LIMITATIONS** | known, stated, not fixable at this stage | origin and timestamp · chaining not re-validated by our verifier · an entirely rewritten archive · a ledger is not byte-reproducible |
| **PLANNED** | considered, not committed, conditional on a request | external anchoring · signature · contractual retention · an in-browser verification space · instrumenting live traffic |

**In none of the four:** a certification, a completeness guarantee, or legally
recognised probative value. Those are not features to schedule — they are
promises we would not keep.

---

## The two demonstrations

Two corpora, two purposes. Neither replaces the other.

| | **A — GROUNDED-S1** | **B — MED** |
|---|---|---|
| Nature | synthetic, fabricated for the bench | an independent medical experiment |
| What it shows | the verifier's controlled behaviour: absences of measurement, and **10 of 10 tamper detections** | sector traceability: a real question item, a real model, a real answer, real signals |
| Execution regime | `synthetic` — observes no real operator | `live` — seven named providers |
| Measurements | 15 `measured`, 8 `degraded`, **7 `not_measured`** | 208, all `measured` |
| Models named | no — it observes nothing real | **yes** — see the table in [Demonstration B](docs/MED_DEMO.md) |
| Verification | **19 PASS, 0 FAIL, 2 NOT TESTED** | **10 PASS, 0 FAIL, 8 NOT TESTED** |
| Tamper suite | **applies** — 10/10 detected | does not apply, and says why |
| Documentation | [Demonstration A](docs/DEMO.md) | [Demonstration B](docs/MED_DEMO.md) |

**Why both.** A synthetic corpus can carry measurements that were *not made* —
that is how "an absence stays an absence" is demonstrated rather than promised.
A real corpus cannot be fabricated to order, and it is the only one that shows
what the instrument does on an actual medical question answered by an actual
model.

**What neither demonstrates.** That a measured signal is correct. That an answer
is medically right. A measurement describes properties of a produced text.

---

## What an evidence file contains

Export schema `station.export.campagne/2`. Eight members.

| Member | Content |
|---|---|
| `observations.jsonl` | what was observed, in the ledger's **original bytes** |
| `observations.csv` | derived view; `;` separated, UTF-8 with BOM, formula-prone cells neutralised |
| `measurements.jsonl` | the measurements: signals, coverage, state, version |
| `reference_evaluations.jsonl` | the reference evaluations, and the hash of the reference — never the reference |
| `replay_provenance.jsonl` | the execution regime, and the hash of each replayed input |
| `manifest.json` | schema, campaign, counts, regimes, **named absences**, reading guards, limits |
| `rapport.md` | the document a business reader reads |
| `checksums.sha256` | the hash of every member |

### How the records join

**`observation_id` is the only join key.** It is required on all four JSONL
files. `measurement_id` and `evaluation_id` must **not** be used as join keys:
no schema constrains their shape, and it differs from one corpus to another.

### What is absent stays absent

An unmeasured signal is `null`, never `0`. An observation without a measurement
is **named** in `manifest.json` and in the report. An unestablished cost is not
summed. And a `latency_ms` of `0` on a failed observation is reported as a
duration **not established** — an aborted call leaves no duration behind.

---

## Verify an evidence file

```sh
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip
python verify.py <archive> --corpus <input corpus directory>
python verify.py <archive> --json report.json     # machine-readable, in addition
```

Standard library only. No dependency, no network call, no write.

Every check returns `PASS`, `FAIL` or `NOT TESTED`. A check that is out of
scope returns `NOT TESTED` **with its reason**: no failure is ever replaced by a
favourable value.

> The verifier's own output is in French. Only the documentation is bilingual —
> translating the tool would mean modifying a validated verifier, which this
> release does not do. It is a PLANNED item.

### What `verify.py` deliberately does not do

It does **not** recompute the ledger's hash chaining. Doing so here would be a
second implementation of the chaining rules: two implementations that diverge
prove nothing, and the one that produced the archive would remain the
reference. Chaining is verified with the instrument that wrote it.

### Results observed on 5 November 2026

On the demonstration archive, produced from the frozen `GROUNDED-S1` corpus:

```
BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED
```

The two `NOT TESTED` are the JCS chaining and the archive's origin — the two
checks no local verification can perform.

---

## Bind an observation to its evidence

A record declares digests of objects that are **not inside the archive**: the
response, the prompt, the request. Binding means offering a file whose bytes
hash to one of those digests.

```sh
python bind.py build --archive <archive> --observation obs-... \
                     --artifact response=response.txt \
                     --created-at 2026-11-05T12:00:00Z --out manifest.json
python bind.py verify manifest.json --archive <archive>
```

Four assurance levels, and **the level is derived by the verifier, never read
from the manifest**:

| Level | Available today |
|---|---|
| `declared` | yes |
| `reference_verifiable` | **yes** |
| `cryptographically_attested` | **no** — nothing here verifies a signature |
| `not_demonstrable` | a statement, not an achievement |

A manifest claiming more than it can show is refused. Two manifests carrying
word-for-word identical prose, one anchored and one not, get different
verdicts — because **a textual description of an execution is not proof that
the execution took place**.

See [Binding](docs/BINDING.md) · `sh demo_binding.sh <archive>`

---

## Tamper detection tests

```sh
python tests/test_falsification.py <archive> <corpus>
```

**10 of 10 alterations detected**, and **one declared limitation**:

| Alteration | Detected |
|---|---|
| one byte changed inside a measurement | yes |
| a measurement removed, checksums recomputed | yes |
| a `null` signal declared as measured | yes |
| a measurement attached to a non-existent observation | yes |
| a declared absence that does not exist | yes |
| the execution-regime guard removed from the manifest | yes |
| a secret injected into the report | yes |
| a formula injected into the CSV | yes |
| a member escaping the target directory | yes |
| the manifest removed | yes |
| **one observation erased everywhere, counts and checksums rebuilt** | **no — see below** |

The last one is the limitation that matters. Someone who removes an observation
**and** its measurement **and** its evaluation **and** its provenance, then
fixes every count and recomputes every hash, produces an archive in which
nothing contradicts anything. No internal check can see it.

**The only defence is the archive's hash, kept somewhere other than with the
archive.** Sending the archive and its checksum through the same channel proves
nothing: whoever can replace one can replace the other. See
[External reference](docs/EXTERNAL_REFERENCE.md).

---

## The reference corpus

The demonstration uses **GROUNDED-S1**, a **synthetic** corpus, frozen and
verified — see [Corpus reference](docs/CORPUS_REFERENCE.md).

Its execution regime is `synthetic`: these answers were **fabricated for the
bench** and observe no real operator. They establish that the chain works, and
nothing about the outside world. The archive carries that guard in plain text,
in its manifest and in its report.

It is also the only corpus that carries **measurements that were not made** —
15 `measured`, 8 `degraded`, 7 `not_measured`. A product that promises "an
absence stays an absence" needs absences to demonstrate it.

The second corpus, **MED**, is a real experiment on seven named providers, and
it is published as [Demonstration B](docs/MED_DEMO.md). What is **not** published
is the dataset's own content: its licence status is contradictory at the source,
so no question text, no choices and no reference label are redistributed. The
`item_id` values are published instead, so a question resolves at the dataset
publisher.

---

## Documentation

| | |
|---|---|
| [`docs/DEMO_SCRIPT_5MIN.md`](docs/DEMO_SCRIPT_5MIN.md) | the five-minute demo, with measured durations |
| [`docs/DEMO.md`](docs/DEMO.md) | reproduce the demonstration |
| [`docs/CORPUS_REFERENCE.md`](docs/CORPUS_REFERENCE.md) | the corpora, their hashes, and how an auditor checks them |
| [`docs/EXTERNAL_REFERENCE.md`](docs/EXTERNAL_REFERENCE.md) | verifying from an independently kept hash — and why an internal hash attests nothing |
| [`docs/MED_DEMO.md`](docs/MED_DEMO.md) | Demonstration B — the medical experiment, its dataset, its models and its limits |
| [`docs/TIMESTAMPING.md`](docs/TIMESTAMPING.md) | independent timestamping with OpenTimestamps: what it proves, and why `PENDING` proves no date |
| [`docs/INTEGRATION.md`](docs/INTEGRATION.md) | integrating Evidence: exit codes, `--strict`, JSON reports, and CI |
| [`docs/ATTESTATION.md`](docs/ATTESTATION.md) | the signed attestation: how `cryptographically_attested` is reached, and the 23-case matrix |
| [`docs/CP8_ADAPTER_SPEC.md`](docs/CP8_ADAPTER_SPEC.md) | external receipt adapter — specification only, no code |
| [`docs/BINDING.md`](docs/BINDING.md) | binding an observation to its evidence, the four assurance levels, and the terminology |
| [`docs/REPLAY_FEASIBILITY.md`](docs/REPLAY_FEASIBILITY.md) | can a measurement be replayed? GO / NO-GO, with the blockers |
| [`docs/ADVERSARIAL_AUDIT_EVIDENCE_2026-11-05.md`](docs/ADVERSARIAL_AUDIT_EVIDENCE_2026-11-05.md) | the adversarial audit of 5 November: 18 capabilities, what each one really does |
| [`docs/EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.md`](docs/EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.md) | the 5 November consolidation: what changed, and the nine answers |
| [`docs/FUTURE_SITE.md`](docs/FUTURE_SITE.md) | the planned architecture of the product site — not built, not deployed |

Each document exists in English and in French (`*.fr.md`).

---

## Limitations

Beyond the table at the top of this file:

- **Reproducibility.** "Reproducible" here means *same inputs, same observation
  and measurement content, valid chain*. Never *same hash*. A ledger is not
  byte-reproducible even when synthetic: `recorded_at` is read from the clock,
  and the chaining hashes depend on it. An archive's own hash changes at every
  export, because the manifest carries the export timestamp — six of the eight
  members are byte-identical across two exports.
- **No external anchoring.** No signature, no third-party timestamp.
- **The verifier's output is French-only.** Documentation is bilingual; the tool
  is not.
- **One campaign exported.** The enriched archive is EXPERIMENTAL for that
  reason, not because a check failed.

---

## Security

Please do not open a public issue for a vulnerability. Write to
**[contact@neomundi.io](mailto:contact@neomundi.io)** with what you observed and
how to reproduce it. Never attach a real key, not even your own.

What we consider a vulnerability here: a path that lets a tampered archive pass
verification; a leak of a secret or a personal path into an exported archive; a
check that returns `PASS` where it cannot actually conclude.

---

## Licence

**No licence is declared on this repository, and that is a decision rather than
an oversight.**

A public repository without a licence file is **all rights reserved** by
default: you may read it and discuss it, and no right to copy, modify or
redistribute is granted. Concretely, today: reading and discussing — yes; reuse
in another project, redistribution, or derived work — no.

Choosing a licence is a decision still to be taken, and it does not belong to
this file.

**Datasets keep their own licences**, declared when they are imported and
carried by their manifests — and **no third-party dataset content is published
here.** No corpus, no ledger, no archive is in this repository: only the
verifier, the tests and the documentation.

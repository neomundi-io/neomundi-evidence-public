# NeoMundi Evidence — reproducible technical demonstration

**7 November 2026.** Every result below was **observed** on that date. The
starting point is the shipped script; nothing was reinvented.

```sh
sh demo_v1_5min.sh
```

🔴 **Everything in the demo dossier is synthetic.** The archive was
manufactured, the signing key was an **ephemeral demonstration key that has
been destroyed**, and the external receipt is invented. No pilot data, no real
dataset. The script says so in its own header, and so must anyone presenting
it.

---

## 1. Artefacts, with digests

| File | Bytes | SHA-256 (first 32) |
|---|---|---|
| `NEOMUNDI_EVIDENCE_V1_DEMO.zip` | 20 237 | `e31e12bb7e32c7a33db1ecacc8c38cd1` |
| `…zip.jws` | 2 211 | `d533518f4413d75e7ea58923d21bfe6c` |
| `…zip.jws.ots` | 786 | `3c1f7db3248c008c91f40ba1c5ab4d73` |
| `trust-store.json` *(test store)* | 2 815 | `6e6534544d85cf8e6ef83b6a176869e9` |

All four live in `examples/dossier-v1/`. The archive's digest was recomputed
**after** every scenario below and found unchanged: the original is never
opened for writing.

---

## 2. Method

Each altered copy is rebuilt preserving the original `ZipInfo` — date,
compression method, `create_system` — so the **only** difference is the
targeted alteration. Without that, the control would be measuring the noise of
the rewrite.

Exit codes were measured **without a pipe**: `cmd > /dev/null 2>&1; echo $?`.
A piped `$?` reports the last stage of the pipeline, not the tool. That
mistake was made once during this work and corrected before anything was
asserted.

---

## 3. Scenario A — normal verification

| # | Command | Code | Result |
|---|---|---|---|
| A1 | `python verify.py <archive> --corpus <corpus>` | **0** | 19 PASS, 0 FAIL, 3 NOT TESTED |
| A2 | `python verify.py <archive>` | **0** | 17 PASS, 0 FAIL, 4 NOT TESTED |
| A3 | `python verify_attestation.py <jws> --archive <archive> --trust-store <store> --allow-test-keys` | **0** | 10 PASS, 0 FAIL, 5 NOT TESTED — level `cryptographically_attested` |

⚠️ **A1 and A2 differ by the corpus**, not by quality. With the corpus, the
replay-input digests can be confronted (4/4) and two `NOT TESTED` become
`PASS`.

---

## 4. Scenario B — internal alteration

One byte changed **inside** `observations.jsonl`.

```
python verify.py b-interne.zip        ->  code 1
[FAIL] empreintes des 7 membres declares - divergents : ['observations.jsonl']
BILAN : 16 PASS, 1 FAIL, 4 NOT TESTED
```

**Interpretation**: the member digest diverges. This is the easy case, and the
one most people assume is the only one.

---

## 5. Scenario C — external alteration

One byte **appended at the end of the ZIP file**. No member changes.

| # | Command | Code | Result |
|---|---|---|---|
| C1 | `verify.py c-queue.zip` | **0** | **17 PASS, 0 FAIL** |
| C2 | `verify_attestation.py <jws> --archive c-queue.zip …` | **1** | `[FAIL] concordance avec l archive` |

Archive digest: `5319ac9f…` against the original `e31e12bb…`.

🔴 **This is by design, not a defect.** `verify.py` verifies the archive's
**internal integrity**; the attestation verifies the **file's identity**. Two
tools, two distinct guarantees — and confusing them would be promising one
while delivering the other.

---

## 6. Scenario D — an observation removed, all checks recomputed

The hardest case, and reproduced here **independently of the demo script**: one
observation removed from `observations.jsonl`, its rows purged from
`measurements.jsonl`, `reference_evaluations.jsonl`,
`replay_provenance.jsonl` and the CSV, the manifest counts rebuilt, and
`checksums.sha256` recomputed.

| # | Command | Code | Result |
|---|---|---|---|
| D1 | `verify.py d-amputee.zip` | **0** | **17 PASS, 0 FAIL, 4 NOT TESTED** |
| D2 | `verify_attestation.py <jws> --archive d-amputee.zip …` | **1** | `[FAIL] concordance avec l archive` |

🔴 **A thorough forger produces an archive that is internally perfect.**
`verify.py` alone sees nothing. The reference attestation refuses it.

⚠️ **A divergence to be aware of.** `tests/test_falsification.py` contains a
comparable amputation and reports it as **detected**, flagged *"mieux
qu'annoncé"*. The two forgers are **not equally thorough**, and the
documentation does not yet say how they differ. Until it does: quote **cases**,
never a rate.

---

## 7. Scenario E — what the tools refuse

A verification that cannot refuse is not a verification.

| # | Situation | Command | Code | Message |
|---|---|---|---|---|
| E1 | a `test` key, without explicit consent | `verify_attestation.py … <no --allow-test-keys>` | **1** | *"cle de statut `test` : elle n'accorde aucune attestation"* |
| E2 | store not confronted, under `--strict` | `verify_attestation.py … --strict` | **2** | the store line stays `NOT TESTED` |
| E3 | binding to an unknown observation | `bind.py build --observation obs-inexistante` | **1** | *"aucune observation 'obs-inexistante' dans l'archive (4 observations presentes)"* |
| E4 | writing a private key under the repository root | `sign.py genkey --out <repo>/interdite.json` | **1** | *"refus d'écrire une clé privée sous la racine du dépôt"* |

**E4 was checked twice**: the file was **not created**. The refusal happens
*before* generation, not after.

### The Station-side equivalent, recorded in Q-2

The preflight comparison is in the frozen Q-2 dossier and was **not re-run
here** — Station is out of this mission's scope.

```
A  [warning] STATION_CODE_COMMIT declares 8d79743… and the repository is on
            91db315… : the variable CONTRADICTS the code about to run
B  [ready  ] the evidence will name 91db315… — declaration confronted with
            the repository, working tree clean
```

Case A is **authentic**: it is the defect Q-1 let through, caught before the
first call.

---

## 8. Scenario F — timestamping

| # | Command | Code | Result |
|---|---|---|---|
| F1 | `timestamp.py inspect <proof.ots>` | **0** | magic, version 1, SHA-256, 786 bytes |
| F2 | `timestamp.py verify <proof.ots> --subject <jws>` | **0** | **3 PASS, 0 FAIL, 4 NOT TESTED** — the binding holds |
| F3 | `timestamp.py verify … --strict` | **2** | the proof is `PENDING` |
| F4 | `timestamp.py verify <proof.ots> --subject <wrong file>` | **1** | *"la preuve s'engage sur d533518f…, le sujet se hache sur …"* |

🔴 **`PENDING` attests no date.** The shipped proof carries **4 PENDING
attestations and 0 Bitcoin**. A pending says a calendar committed to include
the digest in a future transaction — nothing about time.

🔴 **No eIDAS qualification**, and the tool **delegates** time verification:
`ots verify <proof.ots>`. Validating a Bitcoin attestation needs a block
header, which is a trust source we do not have.

**F2 and F4 together are the useful pair**: the binding is verified
positively, and a wrong subject is refused with both digests named.

---

## 9. Detection: cases, not rates

| Battery | Scope | Result |
|---|---|---|
| `tests/test_falsification.py` | ten named alterations | **10/10 detected**, +1 declared limit |
| `tests/test_adversarial.py` | fifteen cases | **13 detected, 2 declared misses** |
| Scenario C above | byte appended at end | `verify.py` **no**, attestation **yes** |
| Scenario D above | amputation + recomputation | `verify.py` **no**, attestation **yes** |
| Q-1 adversarial case G | provenance rewritten **then repaired** | **no** — not even the attestation |

🔴 **All five rows are exact, and they do not describe the same thing.**
Detection depends entirely on how thorough the forger is. The only honest
formulation:

> *Ten typical alterations, all detected by the verifier alone. Two forms of
> careful forgery that only the attestation stops — and one that no local
> check stops, which we publish.*

---

## 10. Reproducing all of it

```sh
# the five shipped demonstrations
sh demo_v1_5min.sh          # integrity, autonomy, attestation, timestamp, reconciliation
sh demo_5min.sh
sh demo_binding.sh
sh demo_reconciliation.sh
sh demo_timestamp.sh

# the CI fixture, then the full suites
python tests/make_fixture.py <dir> --profile v2
```

The CI workflow `.github/workflows/tests.yml` is the authoritative sequence —
including a dedicated job that blocks `cryptography` and checks that
`verify.py` returns the **same** summary.

⚠️ **One procedural trap, met during this work.** `tests/test_binding.py`
needs a `manifest.json` that `make_fixture.py` does **not** produce: the CI
builds it first with `bind.py build`, using `first_observation_id` from
`fixture.json`. Running the suite without that step fails with
`FileNotFoundError` — a **procedure** error, not a software defect.

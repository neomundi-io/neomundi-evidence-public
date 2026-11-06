<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="COMPARATIVE_REPORT.fr.md">Français</a></sub>

# ODA3 re-evaluation — the experiments replayed on the merged commit

**6 November 2026.** Replay of the ODA3 experiments on the commit that merged
PR #10, compared to the initial audit.

| | |
|---|---|
| Commit under test | **`ee78214`** — `Merge pull request #10 from neomundi-io/feat/evidence-oda3-consolidation`, identical to `origin/main` |
| Initial audit | `reports/oda3-mukesh-2026-11-06/`, **55 files, unmodified** |
| This replay | `reports/oda3-reevaluation-2026-11-06/`, a separate folder |
| Archive under test | `examples/dossier-v1`, `e31e12bb7e32c7a33db1ecacc8c38cd18225fa10618c7e1aa5d6f9540f2ad7d6` — byte-identical to the audited one |

> No ODA3 file was modified. No `NOT TESTED` was turned into a `PASS`.

---

## The short answer

**The consolidation improves the guarantee, and less than the recommendation
suggests.** Three findings, all measured:

1. The completeness control **catches** an amputated export — but only from a
   forger who does **not** also rewrite the declaration.
2. **OD-C still returns `19 PASS, 0 FAIL` on the V1 dossier**, and always
   will. That archive declares no completeness contract, so there is nothing
   to contradict. The ODA3 finding is **narrowed, not closed**.
3. The auditor's probe **changed between the initial audit and now**, so its
   column cannot be compared. Reading it as a regression would be a method
   error.

---

## 1. The experiments, before and after

Commands:

```sh
python reports/oda3-mukesh-2026-11-06/oda3_experiments.py \
  --dossier examples/dossier-v1 --repo . \
  --probe reports/oda3-mukesh-2026-11-06/oda3_probe.py \
  --json  reports/oda3-reevaluation-2026-11-06/raw/04_experiences_dossier_v1.json
```

Only **our** tools are comparable. The probe's column is treated in §4.

| Case | Alteration | `verify.py` initial | `verify.py` after PR #10 | Attestation initial | after |
|---|---|---|---|---|---|
| **OD-A** | a null byte appended after the central directory | `0` — 19/0/**2** | `0` — 19/0/**3** | `1` — 9/1/4 | `1` — 9/1/**5** |
| **OD-B** | one hex character changed, checksums **not** redone | `1` — 18/**1**/2 | `1` — 18/**1**/3 | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-C** | the **last** record removed everywhere, counts and checksums rebuilt | **`0` — 19/0/2** | **`0` — 19/0/3** | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-E** | an **interior** record removed, likewise | `0` — 19/0/2 | `0` — 19/0/3 | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-D** | the JWS `alg` forged to `none` | `0` — 19/0/2 | `0` — 19/0/3 | `1` — 8/**2**/4 | `1` — 8/**2**/5 |

Read exit codes, not prose: `0` = concluded favourably, non-zero = refused.

**Every verdict is unchanged. Every count gains exactly one `NOT TESTED`** —
`verify.py` went from 21 to 22 control lines, and the V1 dossier declares no
completeness contract, so the new line is `NOT TESTED`. The attestation
gained one likewise, from the `--store-digest` control.

**That is the honest result on this archive: one more thing reported, nothing
more caught.**

## 2. The guarantee actually demonstrated — and its exact limit

OD-C's scenario is what the new control was built for, so it had to be
exercised on an archive that **declares** the contract. Replayed on a
`--profile v2` fixture, against two forgers
(`raw/05_odc_sur_v2.txt`):

| Forger | What they rebuild | `verify.py` |
|---|---|---|
| **Negligent** | counts and checksums, **not** the contract | **`exit 1` — 19 PASS, 1 FAIL** |
| **Thorough** | counts, checksums **and** the contract | `exit 0` — 20 PASS, 0 FAIL |

The refusal, verbatim:

```
[FAIL      ] completude de l export - le contrat annonce 16 enregistrement(s)
             exporte(s), les decomptes des membres en totalisent 12
```

So the control is real, and so is its ceiling:

- **It catches an inconsistent amputation.** The declaration and the members
  no longer add up, and the archive is refused — with no signature involved.
- **A consistent forger defeats it.** Rewrite the three contract fields
  coherently and the arithmetic closes again.

**What stops the thorough forger is the signature, and only the signature.**
`verify_attestation.py` refused **all five** altered archives, in both runs,
in every case. The contract fields live in `manifest.json`, covered by
`checksums.sha256`, covered by the archive digest, which is signed: a
thorough forger must break Ed25519.

The completeness control's value is therefore precisely stated: **it is the
defence that works on an unsigned archive.** That is exactly the case ODA3
exercised — they could not re-sign. It raises the cost of forgery from
"rebuild the checksums" to "rebuild the checksums and the declaration, or
hold the key". It does not make an amputated export detectable in general,
and must never be read that way.

## 3. R-6 is not exercised by any of this

The provenance gap analysed in [`R6_PROVENANCE_CONTRACT.md`](../../docs/R6_PROVENANCE_CONTRACT.md)
is untouched by these experiments, and remains as measured: **0 provenance
fields across 238 measurements in 8 frozen ledgers.** No experiment above
could have found it, and none closes it.

## 4. Two limits of the auditor's instrument

Both established by observation, not by reading code. Neither changes any
conclusion of the initial audit, and neither is a defect in our product — but
both bound what this replay can claim.

### The probe is not a frozen instrument

On the **same** dossier, byte-identical, the probe's own standalone run in the
initial audit and my replay agree exactly:

```
run 06, initial audit  : 1 PASS, 0 FAIL, 2 NOT TESTED, 6 FACT   (9 controls)
run 01, this replay    : 1 PASS, 0 FAIL, 2 NOT TESTED, 6 FACT   (9 controls)
```

But the probe **invoked by the experiments** in the initial audit reported
`3 PASS, 0 FAIL, 0 NOT TESTED, 4 FACT` — **7** controls. The file timestamps
settle it:

| | |
|---|---|
| `07_experiments.json` written | **08:49:43** |
| `oda3_probe.py` written | **08:58:24** |

The probe was rewritten **nine minutes after** the experiments were recorded,
gaining two controls. It is **untracked by Git**, so no revision identifies
either version.

**Consequence.** The `oda3_probe.py` column of the initial experiments table
is not comparable with mine. In particular OD-E moves from `1 FAIL` to
`0 FAIL` on the probe — **neither a regression nor an improvement, but a
change of instrument.** `verify.py` and `verify_attestation.py` remain fully
comparable: they are ours, at `ee78214`.

### Three of five altered-archive digests are not reproducible

Two passes, same machine, same commit, same input archive
(`raw/09_limites_de_l_instrument.txt`):

| Case | Pass 1 | Pass 2 | |
|---|---|---|---|
| OD-A | `5319ac9f…` | `5319ac9f…` | identical |
| OD-B | `8d037b6c…` | `beadcf64…` | **differs** |
| OD-C | `4cdb6288…` | `e6d41a2e…` | **differs** |
| OD-E | `6e766ef3…` | `4571b43e…` | **differs** |
| OD-D | `e31e12bb…` | `e31e12bb…` | identical |

`zipfile.writestr` with a `str` name stamps `ZipInfo.date_time` with the
**current clock**, so every case that rebuilds the archive yields a new
digest. The two stable cases are the two that rebuild nothing: OD-A appends a
byte, OD-D touches only the `.jws`.

The altered digests in the ODA3 report are therefore **not** re-derivable by
a third party — which is the same class of defect R-5 found in our own
corpus reference, and worth naming for exactly that reason. The **verdicts**
reproduce; the digests do not.

### And the probe cannot confirm R-1

```
grep types_exclus            oda3_probe.py  → 0
grep enregistrements_exportes oda3_probe.py → 0
grep completude              oda3_probe.py  → 0
```

The probe does not read the declaration PR #10 added. **It can neither
confirm nor refute R-1.** Only [`tests/test_completude.py`](../../tests/test_completude.py)
exercises it — our own test, which is weaker evidence than an independent
instrument and is stated as such.

## 5. C-2 — an apparent regression that is the opposite

The probe reports the `record_sha256` recipe as `PASS` on the V1 dossier and
`NOT TESTED` on `v2`. Read alone, that inverts the conclusion. The
confrontation (`raw/03_c2_recette_declaree.txt`):

```
--- profil v1 ---   declared recipe : NO
    agree WITH `sequence` : 0 ; agree WITHOUT `sequence` : 4
--- profil v2 ---   declared recipe : yes
    agree WITH `sequence` : 16 ; agree WITHOUT `sequence` : 0
```

`v1` hashed **without** `sequence` — the probe's simplification, which it
reproduces, hence `PASS`. `v2` hashes **with** `sequence` — the instrument's
real field set, which the probe omits, hence `NOT TESTED`.

**The move from `PASS` to `NOT TESTED` is an improvement.** `v2` moved
*towards* the instrument and *away* from the probe. A reader taking the
probe's verdict at face value would conclude the opposite.

The chain confrontation script (`oda3_chain_confrontation.py`) requires a
Station `src` checkout that is not reachable from this session, so C-2 was
settled by the purpose-written confrontation above rather than by that
instrument. **Stated as a substitution, not as an equivalent.**

---

## 6. Summary

### New guarantees actually demonstrated

| | |
|---|---|
| An **inconsistent** amputation of an export is refused, with no signature involved | measured: `exit 1`, 19 PASS **1 FAIL** on `v2` |
| An archive **names** what its ledger held, exported and withheld, and the three numbers add up | the control's `PASS` line |
| `v2` hashes with the instrument's field set | 16/16 agree with `sequence`, 0/16 without |
| The V1 dossier reproduces byte for byte on Linux | `create_system` pinned; CI green |

### Limits corrected

| | |
|---|---|
| An export could withhold records silently | now declared and checked — **when the producer declares the contract** |
| `['True']` rendering | fixed, both languages |
| `stamped_at_declared` versus the anchoring block | now side by side |
| The `campaign_sha256` claim | corrected; four-class access table |
| The archive was not reproducible outside Windows | fixed — a defect the audit could not see, it ran on Windows |

### Limits persisting

| | |
|---|---|
| **OD-C on an archive without the contract** | `19 PASS, 0 FAIL`, permanently. Narrowed, not closed |
| **A thorough forger defeats the completeness control** | only the signature stops them |
| **R-6** | 0 provenance fields in 238 measurements; contract evolution required |
| **R-5, second half** | the recipe is still unpublished — class C |
| **R-9 / B-1** | the signer's legal identity. Nothing technical replaces it |
| The sixth `v2` divergence | `record_sha256` canonicalisation: declared, not closed |
| **That a declaration is *true*** | never verifiable from an archive. A permanent `NOT TESTED` |

### New regressions

**None in our tools.** Every `verify.py` and `verify_attestation.py` verdict
is unchanged across all five cases; the only movement is `+1 NOT TESTED`,
which is the new control reporting honestly on an archive that predates it.

The one apparent regression — OD-E on the probe, `1 FAIL` → `0 FAIL` — is a
**change of the auditor's instrument**, established by its file timestamps,
and is not attributable to this commit.

---

## Raw outputs

| File | What it holds |
|---|---|
| `raw/01_probe_dossier_v1.{txt,json}` | the probe on the V1 dossier |
| `raw/02_probe_fixture_v2.{txt,json}` | the probe on a `v2` fixture |
| `raw/03_c2_recette_declaree.txt` | the C-2 confrontation |
| `raw/04_experiences_dossier_v1.{txt,json}` | the five experiments replayed |
| `raw/05_odc_sur_v2.txt` | OD-C against a negligent and a thorough forger |
| `raw/07_instrument_non_fige.txt` | the probe changed between runs |
| `raw/08_experiences_second_passage.json` | second pass, for digest reproducibility |
| `raw/09_limites_de_l_instrument.txt` | the two instrument limits |

# NeoMundi Evidence — release readiness

**7 November 2026.**

---

# READY WITH LIMITATIONS

The documented capabilities match the code, every published command was
executed, the scenarios are reproducible, the exit codes conform, and the
frozen qualifications are intact.

**The limitations are real, declared, and none of them is a defect to be
fixed before release.**

---

## 1. Why not READY

Four things are **not** confirmed, and a release that implied otherwise would
be false:

| | Status |
|---|---|
| **Third-party ingestion** | TESTED on 16 fixtures; **no real third-party package ever ingested** |
| **Reconciliation** | TESTED 27/27, DEMONSTRATED on fixtures; **no real receipt reconciled** |
| **Temporal anchoring** | IMPLEMENTED and TESTED; the shipped proof is **`PENDING`** — no date attested, no eIDAS qualification |
| **Q-2** | global verdict **`PARTIAL`**, and it stays so |

And one documentation gap: the six new documents have **no `.fr.md`
counterpart** in a repository that is bilingual by convention.

## 2. Why not NOT READY

| Criterion | State |
|---|---|
| Documented capabilities match the code | **yes** — every command executed |
| Commands verified | **yes** — 12 operations, exit codes measured |
| Demonstration reproducible | **yes** — 15 suites green, 13 expected codes conforming |
| Results traceable | **yes** — identifiers, digests and controls mapped |
| Reservations explicit | **yes** — a dedicated document, nothing softened |
| Relevant tests run | **yes** — the CI sequence replayed locally |
| Documents coherent | **yes** — six entry points, no duplication |
| Historical qualifications intact | **yes** — Q-1 20/20, Q-2 13/13, manifests unchanged |
| Decision justified | **this document** |

**One failure occurred and was diagnosed**: `test_binding` was a **procedure**
error on my side — the CI builds the binding manifest first. No success
criterion was altered to obtain a `PASS`.

---

## 3. What a release may claim

- a **verifier that runs with nothing installed**, returning **three** states
  and never a binary verdict;
- an **Ed25519 attestation** verifiable offline, **without any private key**,
  with the caveats **inside** the signed document;
- a **trust store** confrontable through two technically independent channels
  — *under the same governance*;
- **four verification layers** that catch different things, demonstrated —
  including two alterations that `verify.py` alone does **not** catch;
- **five reconciliation verdicts**, which confront without deciding;
- **refusals that work**: a test key grants nothing, an unknown observation is
  refused, a private key cannot be written under the repository root.

## 4. What a release must not claim

🔴 No **detection rate** without naming its battery — "10/10" belongs to ten
named alterations · no **date** from a `PENDING` proof · no **eIDAS**
qualification · no **legal certification** — `experimental` is the opposite of
`verified` · no **third-party trust anchor** — both channels are ours · no
**operational validation** of ingestion or reconciliation · and **never**
`PARTIAL` presented as `PASS`.

---

## 5. Recommended follow-ups, in order

1. **produce the `.fr.md` counterparts** — convention, and the cheapest item;
2. **resolve the divergence** between `test_falsification.py` and scenario D:
   say how the two forgers differ, or align them;
3. **ingest one real third-party package**, and one real receipt — that is what
   moves two capabilities from TESTED to QUALIFIED;
4. **upgrade the timestamp proof** once the chain has confirmed, then re-run
   `timestamp.py upgrade` and `verify --strict`: a `PENDING` that becomes a
   Bitcoin attestation is the single largest gain available;
5. **declare the export completeness contract** —
   `registre.enregistrements_exportes` and `registre.types_exclus` — which
   closes one of the three structural `NOT TESTED`.

None of the five blocks a release. The fourth is the only one that would
change what the product **establishes**, rather than what it documents.

---

## 6. Decision

**READY WITH LIMITATIONS**, for a documentation release of the public
repository on the branch `docs/consolidation-v1-20261107`.

Nothing is merged, nothing is deployed, nothing is published. The frozen
references Q-1 and Q-2 are unchanged, and the `PARTIAL` verdict stands.

> Finishing the documentation does not mean the experimental limits have
> disappeared. It means they are now written down where a third party can read
> them.

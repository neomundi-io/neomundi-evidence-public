<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="EXTERNAL_REFERENCE.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Verifying from an independently kept hash

**The rule, before anything else:** a hash contained *inside* the archive
attests nothing about the archive. `checksums.sha256` establishes that the
members are consistent with one another — not that they are the ones we
produced. Whoever can replace the archive can replace the checksum that travels
with it.

A verification is independent only if the hash comes from **elsewhere**.

---

## The three levels, never to be confused

| Level | What it establishes | What it does not |
|---|---|---|
| `checksums.sha256`, **inside** the archive | the members have not moved relative to one another | that the archive is the one we produced |
| the archive's hash, **kept elsewhere** | the received file is the one whose hash was recorded | origin, time, or the truth of the content |
| a third-party signature or anchor | who produced it, and when | **does not exist today** — see the roadmap |

---

## The two control sources

The reference freeze exists in **two independent copies**, and that is what
makes it usable as a reference.

| Source | Location | State on 5 November 2026 |
|---|---|---|
| workstation | the operator's local backup tree | online, verified: `12 PASS, 0 FAIL, 3 NOT TESTED` |
| removable media | an offline external drive | copied and verified at copy time — **207 of 207 files conforming**, verifier re-run in place: same 12 PASS. **The drive has since been disconnected** |

> The external copy being offline is a **quality** for this role: a control
> source that cannot be continuously rewritten is worth more than one mounted
> permanently. It must be reconnected to be used, and read again then — never
> reuse a figure from this document without having observed it anew.

### Freeze archive hashes

```
98043a138a58ef764902718a2f07d2a3058108ce448cd19a042c7e9fda294559  GEL_MED_20261105.zip
754da1d21c67590b12a26ee524a58dec3c288b0c3a698c7186b60c99451aee49  GEL_GROUNDED-S1_20261105.zip
```

Observed identical on **both** copies on 5 November 2026.

---

## Verifying a received evidence file

### What to compare: the members, not the archive

The **archive's** hash changes at every export: its manifest carries the export
timestamp. Two exports of the same corpus, two minutes apart, give two
different archive hashes.

Measured on 5 November on two consecutive exports: **six members of eight are
byte-identical**. Only `manifest.json` and `checksums.sha256` vary, and the only
field that differs is the export timestamp.

**The member hashes are therefore the reusable reference.** For the
demonstration archive:

```
f8726fb87b844d15e579c06df1261ca220e5666e6dc932be03d52c4ef092eda8  observations.csv
0ef38ba4c19dbfdacca0f5f0c7df512ce2d20f70506d1689d89a9973ee985350  observations.jsonl
f83b73a278507d6b01726723e636fbd3c6a66a39406667f9ffc6f3452db75092  measurements.jsonl
5da470239cc1f87143da7ab23250023fb767b9e6e3f5572e6fe44818633b5ec4  reference_evaluations.jsonl
a165bb220b55ad0658c84936e0d3bc6ab2ddc059e5ed2807c7e55bd409afba34  replay_provenance.jsonl
2a3e661ab85f1e7b9f3c3264f5be586c2997af3f00ea48918f1f397be19bbf8b  rapport.md
```

`manifest.json` and `checksums.sha256` are deliberately absent from this list:
they vary from one export to the next.

### The procedure

```sh
# 1. the hash of the archive you received, before opening it
sha256sum NEOMUNDI_EVIDENCE_DEMO_V0.1.zip

# 2. compare it with the one transmitted THROUGH ANOTHER CHANNEL
#    (a mismatch = do not open, and tell us)

# 3. the members, against the list in this document
unzip -o NEOMUNDI_EVIDENCE_DEMO_V0.1.zip -d received/
cd received && sha256sum observations.jsonl measurements.jsonl \
    reference_evaluations.jsonl replay_provenance.jsonl observations.csv rapport.md

# 4. internal consistency, and everything else
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip --corpus <corpus>
```

Step 2 is the one that counts. The other three are consistency checks: only
step 2 is an **independent** verification.

---

## External anchoring — planned, not built

Today the ledger has **no external anchoring**. An entirely rewritten chain
verifies perfectly. This is the limitation the tamper-detection test
demonstrates: one observation erased everywhere, counts and checksums rebuilt,
passes every internal check.

Three possible mechanisms, by increasing cost. **None is committed**, and none
should be announced as available.

| Mechanism | What it would bring | What it would cost |
|---|---|---|
| **Periodic publication of the head hash** to a medium outside our control | a rewritten chain would diverge from the hash published on that date | choosing the medium, and standing behind its durability |
| **Signing the archive** with a key whose public half is distributed separately | origin, and integrity at emission | key management — a lost key invalidates the whole past, a compromised key invalidates it too |
| **Third-party timestamping** (RFC 3161 or equivalent) | an opposable time bound | an external dependency, and a contract |

Two conditions before committing to any of them, and neither is technical:

1. **a pilot must ask for it.** None has, to date.
2. **the ledger's discipline must allow it.** The design has anticipated it from
   the start. Adding it later does not anchor the past: it would anchor from the
   date it enters service, and the frozen corpus would remain unanchored.

> That second point is worth stating to a reviewer: even if we anchored
> tomorrow, the 844 and 151 records already frozen would not be. Their only
> protection would remain the dual copy and the hashes in this document.

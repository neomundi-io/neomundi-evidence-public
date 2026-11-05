<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="TIMESTAMPING.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Independent timestamping — OpenTimestamps

The signed attestation establishes **who** committed. It does not establish
**when**: `attested_at_declared` is a date the signer writes itself.
Independent timestamping attacks exactly that limit — and only partly closes
it.

---

## What this tool establishes, and what it delegates

> **It establishes, with no dependency at all, that the `.ots` proof commits
> to the subject's digest.** That is the *binding*, and it is the only part we
> can demonstrate ourselves.

> **It does not verify the time.** Validating a Bitcoin attestation needs a
> block header, hence a source of trust we do not have. That verification is
> **delegated** to the official client (`ots verify`), and the corresponding
> line stays `NOT TESTED` here.

A tool claiming to verify time without a block header would be lying.

---

## `PENDING` is not proof of time

This is the easiest thing to misread, and it is repeated on every run.

| State | Means |
|---|---|
| **`PENDING`** | a public calendar committed to including the digest in a **future** Bitcoin transaction. **No date is attested.** |
| **`BITCOIN`** | the digest is committed in a block. A time claim exists — and verifying it needs the official client |

Moving from one to the other takes **hours**: the time for the chain to
confirm the calendar's transaction. You get it by running `upgrade` again.

> **No eIDAS qualified timestamp is claimed.** OpenTimestamps is not a
> qualified trust service provider under the regulation. The verifier writes
> this on a dedicated line, on every run.

---

## What leaves the machine

**A 32-byte digest, and nothing else.**

Never the archive, never the manifest, never any pilot data. And only two
subcommands touch the network:

| Subcommand | Network |
|---|---|
| `stamp` | **yes** — submits the digest to the calendars |
| `upgrade` | **yes** — asks for the completed attestation |
| `inspect` | no |
| `verify` | **no, never** — a test checks this on the call graph |

---

## Use

```sh
# 1. timestamp the signed attestation -- the recommended subject
python timestamp.py stamp examples/attestation/A.zip.jws \
    --descriptor A.zip.jws.timestamp.json \
    --stamped-at 2026-11-05T22:00:00Z

# 2. read the proof, offline
python timestamp.py inspect A.zip.jws.ots

# 3. verify the binding, offline
python timestamp.py verify A.zip.jws.ots \
    --subject examples/attestation/A.zip.jws \
    --descriptor A.zip.jws.timestamp.json --json report.json

# 4. later, once the chain has passed
python timestamp.py upgrade A.zip.jws.ots --out A.zip.jws.v2.ots

# 5. and verify the TIME with the official client, not with us
ots verify A.zip.jws.v2.ots
```

**Why timestamp the attestation rather than the archive.** The attestation
carries the archive's digest *and* the signature. Timestamping the attestation
therefore ties the time to the signed commitment, not merely to bytes.

`--stamped-at` is **required**: the tool never reads the clock, and that date
is **not** the timestamp — it is when *we* submitted.

---

## The seven control lines

| Control | Possible states |
|---|---|
| ★ `preuve .ots lisible` | `PASS` / `FAIL` |
| ★ **`liaison a l empreinte du sujet`** | `PASS` / `FAIL` / `NOT TESTED` |
| `descripteur de liaison` | `PASS` / `FAIL` / `NOT TESTED` |
| `arbre des attestations` | `PASS` / `FAIL` / `NOT TESTED` |
| ★ `attestation confirmee par la chaine` | `PASS` / `NOT TESTED` |
| `temps verifie par un tiers` | **always `NOT TESTED`** |
| `qualification eIDAS` | **always `NOT TESTED`** |

The three ★ are **required** under `--strict`. A `PENDING` proof therefore
returns **code 2**: honest, and exactly what an automated consumer needs to
know.

The last two will **never** be `PASS`, and so are never required — a strict
mode counting them would always be red.

---

## Why the binding depends on nothing

The detached `.ots` format places the committed digest at a **fixed offset**:

```
31 bytes of magic · 1 version byte · 1 op byte · 32 bytes of digest
   ^ \x00OpenTimestamps\x00\x00Proof\x00…      ^ 0x08 = SHA-256
```

Reading the binding is therefore reading three fields of known length. No
dependency, no tree parsing, no risk of divergence.

**The rest of the tree is left to the official library** (`opentimestamps`).
Writing a second implementation of a cryptographic format would be a debt, not
independence.

| If `opentimestamps` is… | then |
|---|---|
| present | the tree is read, attestations are listed |
| absent | `arbre des attestations` → `NOT TESTED`, **and the binding stays `PASS`** |

A test exercises this by blocking the import: the binding holds without the
library. That is the property this architecture rests on.

> **A note on the official client.** `opentimestamps-client` — which provides
> the `ots` command — depends on `python-bitcoinlib`, and **that dependency
> crashes on import on the development workstation** (`TypeError` in a path
> check). The format library itself works. One more reason for the binding not
> to depend on it.

---

## `upgrade` never overwrites

```sh
python timestamp.py upgrade old.ots --out new.ots
```

A proof is a **piece of evidence**. Overwriting it would destroy the earlier
one, which stays verifiable and attests the submission. `upgrade` therefore
refuses an existing output without `--force`, and always leaves the input
intact.

While no Bitcoin attestation appears, it says so:

```
attestations Bitcoin : 0 avant, 0 apres
l ancienne preuve est INTACTE : old.ots

Rien n a progresse : la transaction n est probablement pas encore
confirmee par la chaine. Reessayer plus tard. Tant qu aucune
attestation Bitcoin n apparait, **aucune date n est attestee.**
```

---

## Test matrix

**Offline, deterministic**: `python tests/test_timestamp.py` → **21/21**.

| # | Case | Result |
|---|---|---|
| 1 | authentic proof, right subject | **binding `PASS`** |
| 2 | `PENDING` | both time lines `NOT TESTED` |
| 3 | eIDAS claim | none, explicit line |
| 4 | different subject | **binding `FAIL`**, code 1 |
| 5 | subject not supplied | `NOT TESTED`, **not `FAIL`** |
| 6 | strict on `PENDING` | **code 2**, verdicts unchanged |
| 7 | strict on a `FAIL` | code 1 — the `FAIL` wins; **7 identical lines** |
| 8 | 5 malformed proofs (no magic, truncated, empty, unknown version, unknown hash op) | **5/5** motivated `FAIL`, no traceback |
| 13 | proof not found | motivated `FAIL` |
| 14 | matching descriptor | `PASS` |
| 15 | **descriptor lying about the subject** | `FAIL` — it is confronted with the proof, not believed |
| 16 | descriptor with unknown schema | refused, not interpreted |
| 17 | unreadable descriptor | motivated `FAIL` |
| 18 | machine report | three distinct states, 3 limits stated |
| 19 | `inspect` | committed digest shown, `PENDING` stated |
| 20 | **`opentimestamps` blocked** | **binding `PASS`**, tree `NOT TESTED` |
| 21 | strict without the library | code 2, never `PASS` |
| 22 | confirmed proof (synthetic) | `attestation confirmee` → `PASS`, **time still `NOT TESTED`** |
| 23 | confirmed + strict | code 0 |
| 24 | even confirmed | the official client's command is given |
| 25 | `verify`'s call graph | **no network primitive** |

**Network, separate**: `python tests/test_timestamp_network.py [--stamp]` →
**3/3**, and **never** runs in CI. A suite depending on four third-party
servers would fail for reasons that are not product defects, and a CI that is
red without an internal cause teaches people to ignore red.

### What the tests cannot exercise

The real `PENDING → CONFIRMED` transition takes **hours** of Bitcoin
confirmation. The path is therefore covered by a **synthetic fixture** (cases
22 and 23): a Bitcoin attestation built offline, which exercises the logic and
**attests no date whatsoever**. No test claims otherwise.

---

## The shipped example

`examples/timestamp/` carries a **real proof**, obtained on 5 November 2026
from the four public calendars:

| | |
|---|---|
| Subject | `examples/attestation/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws` |
| Committed digest | `9b65f9bb02b06944fefd0cc1dd52db157797c274bf27f3e29ee2585126108c18` |
| Proof | 786 bytes, `86da875b…` |
| State | **`PENDING` on 4 calendars** |

The subject is the attestation **already public** in this repository: its
digest is therefore not a disclosure.

**That proof attests no date**, and its descriptor says so. It will have to be
upgraded to carry one.

---

## Dependencies and network — declared

| | |
|---|---|
| **Binding** | no dependency |
| **Reading attestations** | `opentimestamps`; absent → `NOT TESTED` |
| **`stamp` / `upgrade`** | `opentimestamps` **required**, and **network required** |
| **Network reached** | four public calendars over HTTPS |
| **Account, payment** | **none** |
| **Bitcoin** | no node is run, no transaction is emitted, no fee is paid. The calendars aggregate thousands of digests into a transaction they fund |
| **Data transmitted** | **a 32-byte digest** |

---

## What timestamping does not establish

- **The time, on our part.** We verify no Bitcoin attestation.
- **Any date at all, while the state is `PENDING`.**
- **The truth of the content.** Timestamping a fabricated archive yields a
  perfectly valid proof for that fabricated archive.
- **An eIDAS qualification.** None, and none is claimed.
- **That the subject is the one you think** — unless you pass `--subject`, in
  which case the binding *is* demonstrated.

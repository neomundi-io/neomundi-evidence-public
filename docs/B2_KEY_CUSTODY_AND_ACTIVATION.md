<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="B2_KEY_CUSTODY_AND_ACTIVATION.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# B-2 — Custody and activation of the real Ed25519 key

**6 November 2026.** Condition **B-2**. Operational companion to
[`B1_EXPERIMENTAL_SIGNING_DECISION.md`](B1_EXPERIMENTAL_SIGNING_DECISION.md).

> **No key may be generated under this procedure until B-1 is approved and
> the custody below is accepted.** A key generated earlier would be held in
> the name of an entity that has not decided to commit, and every package
> signed with it would carry that defect forward.

---

## Why this key must be distinct from the RGC key

Not a matter of tidiness. Four reasons, and the fourth is decisive.

| | RGC key | Evidence key |
|---|---|---|
| Purpose | signs measurement receipts **in flight** | attests a **frozen package**, after the fact |
| Where the secret lives | on the **production API host** | offline, on an operator workstation, **never on a server** |
| `kid` namespace | `neomundi-rgc-…` | `nm-ev-…` |
| Who can verify | **only the secret holder** | anyone, from the public key alone |

### The fourth reason, which settles it

`app/rgc/signing.py`'s `verify_jws` calls `_public_key_pem()`, which calls
`_load_private_key()`: **it derives the public key from the private key.**
Only the holder of the secret can verify an RGC signature, and offline
nothing works at all — `GET /v1/rgc/jwks` is an HTTP endpoint.

An Evidence attestation must be verifiable **by an auditor who does not
trust us and has no network**. That is the entire product. Reusing RGC's key
would not merely be untidy — it would make the attestation verifiable only
by us, which is the opposite of what it exists for.

So: **RGC must never be offered as the verifier of an Evidence attestation,
and the two keys never share material, holder, host, or `kid` namespace.**

A second consequence worth stating: RGC's public key is already published in
a public repository, and that publication **does not establish official
control** — the GitHub organisation is `is_verified: false`, the file sits
under `fixtures/`, and the commit is signed by GitHub's own web-flow key.
Whatever provenance path Evidence's trust store ends up using (C-5), it
cannot borrow RGC's.

---

## Generation

| | |
|---|---|
| Algorithm | **Ed25519**, imposed — never read from a token header |
| Tool | `sign.py genkey` |
| Where | **offline**, on the operator workstation named in B-1 D-3 |
| Private key path | **outside the repository**, enforced |
| `kid` | `nm-ev-recherche-202611-1` |
| `--store-kind` | `production` |
| `--signer-kind` | `association` |
| `--signer-jurisdiction` | `FR` |

The tool already refuses to write a private key under the repository root —
`refuse_dans_le_depot()`. That guard is not advisory: a committed private
key stays in Git history forever.

The `kid` is **never reused**, including after revocation. A reused `kid`
would make two different keys indistinguishable in a trust store, and would
silently transfer trust from one to the other.

---

## Custody — the five answers that were blank

`SIGNING_POLICY.md` listed these as **to decide**. Here they are, as a
proposal to accept or amend.

| Question | Proposed |
|---|---|
| Where does the secret live? | the operator workstation's **DPAPI store**, which binds it to that Windows user on that machine |
| Who can read it? | the **technical operator** role of B-1 D-3, and nobody else |
| Is there an off-machine backup? | **yes, required** |
| Where is the backup? | **approved on 6 November**: a **dedicated encrypted USB medium**, off-machine, physically separate from the workstation, holding the private key and its `kid` **and nothing else** |
| Who authorises a signature? | the **authorised representative** of B-1 D-2 |

### Why the backup is not optional, and why it is dangerous

Without it, a disk failure makes every future attestation impossible — and
tempts a regeneration under the same `kid`, which the convention forbids.

With it, the secret exists in two places, so custody is now two problems.
The medium therefore holds **only** the key: no manifest, no note naming
what it is for, nothing that makes it worth stealing on its own. And it
must not be reachable with the workstation — a backup in the same drawer as
the machine protects against disk failure and against nothing else.

### What is NOT proposed, and why

- **No HSM, no cloud KMS.** Both would move the secret to a service and
  introduce a dependency this product exists to avoid. For a non-commercial
  experiment, the cost is not justified. For a commercial pilot, revisit.
- **No shared secret, no split key.** One holder, named. Splitting a key
  across holders is a real technique and the wrong one here: it protects
  against a dishonest holder, which is not the risk at this scale, and it
  multiplies the ways a signature becomes impossible.
- **No passphrase on the key file.** DPAPI already binds it to the user and
  machine; a passphrase on top would be stored somewhere, which is a second
  secret with no second custody.

---

## Activation — the ordered procedure

No step may be taken before the previous one is recorded as done.

### Step 0 — prerequisites (nothing technical yet)

1. B-1 is **approved**, with D-1, D-2 and D-3 filled in and dated.
2. The custody above is **accepted**, or amended and accepted.
3. `experimental` is added to the trust-store schema, with the verifier line
   that states its meaning.

**If any of the three is missing, stop.** Generating a key to "be ready"
is precisely the act this procedure exists to prevent.

### Step 1 — generation, offline

> **Corrected on 6 November 2026.** The command previously written here was
> run as an exercise and produced **a schema-invalid store, silently**: it
> passed `--signer "NeoMundi Recherche"`, a legal name where the schema
> expects an identifier (`^[a-z0-9][a-z0-9-]{2,63}$`). It also predated
> `--signer-capacity`, so it declared `unverified` — **contradicting the B-1
> decision** — with the word "experimental" only in a free-text note.
>
> `genkey` now **refuses** a non-conforming identifier before generating
> anything, and the audit confronts the patterns. The command below is the
> one that was exercised end to end.

```sh
# on the operator workstation, network disconnected
python sign.py genkey \
    --kid nm-ev-recherche-202611-1 \
    --out "<path OUTSIDE the repository>" \
    --trust-store-out "<path>" \
    --store-kind production \
    --store-id neomundi-evidence \
    --signer nm-recherche \
    --signer-legal-name "NeoMundi Recherche" \
    --signer-kind association \
    --signer-jurisdiction FR \
    --signer-registration "RNA W563015824" \
    --signer-capacity experimental \
    --valid-from 2026-11-06T00:00:00Z \
    --key-notes "Experimental scope, non-commercial."
```

| Option | Why it is there, and what breaks without it |
|---|---|
| `--signer nm-recherche` | an **identifier**, not a legal name. `genkey` refuses anything else |
| `--signer-legal-name` | the legal name. This is where "NeoMundi Recherche" belongs |
| `--signer-registration` | RNA W563015824. **Declared**, never checked against a registry by this code |
| `--signer-capacity experimental` | without it the store says `unverified`, which contradicts B-1 |
| `--store-kind production` | sets the key's status to `active`. A `test` store would grant nothing |
| `--valid-from` | the date of the B-1 approval. The tool never reads the clock |

Expected output: three lines naming the private key file, the store, the
public key `x`, and `store_version : 1`.

**Then, immediately:**

```sh
python publish_store.py audit "<path to the store>"
```

Expected: **`7 PASS, 0 FAIL, 2 NOT TESTED`**, exit code `0`. The two
`NOT TESTED` are the names of natural persons and the published legal
capacity — neither is decidable by a program, and both are for a human to
read.

**If there is a single `FAIL`, stop.** Do not place the key in custody, and
do not sign anything: the store would be published wrong, and a publication
does not come back.

Record: the `kid`, the public key `x`, the date, and the operator's role.
**Never the private key, and never its path in a shared document.**

### Step 2 — custody

1. Place the private key in the DPAPI store.
2. Write the off-machine backup.
3. **Delete the plaintext file** produced by `genkey`, by overwriting then
   unlinking — not by moving it to a recycle bin.
4. Verify the key still signs, from the DPAPI copy, on a throwaway archive.

Step 4 matters: a custody that has never been exercised is a custody nobody
knows works.

### Step 3 — publication of the public material

The trust store, with `store_kind: production` and `store_version: 1`. This
is **C-5**, and it has its own content audit — seven points, including a
re-reading of every `notes` field, which is where internal context leaks.

### Step 4 — the first real attestation

One package, chosen deliberately, with the representative's authorisation
recorded. **And `--register` from the very first signature**, decision C-3:

```sh
python sign.py attest \
    --archive "<package.zip>" \
    --key "<the private key>" \
    --out "<package.zip.jws>" \
    --attested-at "<ISO 8601 instant in Z>" \
    --register "<...>/evidence-private/registre/signatures.txt"
```

Without `--register`, the tool signs **and says so**: nothing would record
that this key signed this package, and a compromise would then invalidate
everything it ever signed with no way to scope it. One signature with no
trace is enough to lose that ability.

Then verify it the way an auditor would: offline, from the public key alone,
and with `openssl pkeyutl -verify` as an independent second tool.

**If that verification does not pass, stop and do not sign a second
package.**

---

## The register — built on 6 November 2026

`SIGNING_POLICY.md` named this missing. **It no longer is:** `sign.py attest
--register` writes it, `sign.py scope` reads it to scope a compromise, and
decision C-3 gives it a versioned home outside the public repository.

What the policy said about the need stays true word for word:

Without it, a compromise cannot be scoped — and scoping is the only thing
that limits the damage, because marking a key `compromised` invalidates
**every** package it ever signed, retroactively, whatever date they declare.

Minimum viable form, one line per attestation, outside the public
repository:

```
<attested_at_declared>  <kid>  <bundle_sha256>  <attestation_sha256>  <operator role>
```

**This register is a prerequisite of the first real attestation**, not a
follow-up. A single signature with no record of it is already an unscopable
compromise.

---

## Rotation, compromise, revocation

Unchanged from [`SIGNING_POLICY.md`](SIGNING_POLICY.md), and restated
because it is the part that carries consequences:

- `rotated` leaves earlier signatures **trusted**; `compromised` makes them
  **all untrusted, retroactively**. The asymmetry is the point: a thief
  controls the date they write, so no date can contain a compromise.
- **Never revoke dry.** Generate the successor, publish it in the store, set
  `superseded_by` on the predecessor, and only then mark it. A revocation
  whose replacement is not yet published leaves every consumer with a key
  they must distrust and none they can trust — and the verifier returns
  `NOT TESTED` for an unknown key, so the chain silently drops a level
  instead of failing loudly.

---

## Acceptance — APPROVED on 6 November 2026

```
C-1  The custody above is ACCEPTED, with one rotation guard explicitly
     approved:

     NO key withdrawal without a successor PREVIOUSLY PUBLISHED in the
     same store.

     Tooled and exercised: `sign.py retire --kind rotated` refuses
     without `--successor`, then refuses a successor absent from the
     store. Cases 4, 5 and 6 of `tests/test_cles.py` lock it.

C-2  The off-machine backup medium is:

     a DEDICATED ENCRYPTED USB medium, off-machine, holding the private
     key and its `kid` AND NOTHING ELSE.

     "Dedicated" is a constraint, not an adjective: a medium shared
     with anything else carries a manifest, a filename, a date --
     enough to tell a thief what they are holding.

C-3  The register of signed packages will be kept at:

     the VERSIONED private Evidence space, under `registre/`, with a
     backup INDEPENDENT of the key's.

     Outside the public repository, and the guard is hard: `sign.py`
     refuses to write a register under the repository root (case 12).

     Date: 6 November 2026   Direction decision.
```

### Why the two backups stay separate

The key and the register are backed up **independently**, and that is not
belt-and-braces: putting them on one medium would hand a thief **both the
secret and the list of what it opens**. The register names every signed
package; the key signs more. One medium carrying both turns a theft into an
undetectable substitution.

### What remains, and that is all

**The production key is not generated**, and this block being filled in does
not generate it. It authorises the step; the step happens **offline, on the
operator workstation**, network disconnected, per the Activation procedure —
not in a working session, and not by an agent.

Until then, everything this product signs remains a **demonstration**, and
the verifier says so itself: a `test` key grants nothing without
`--allow-test-keys`.

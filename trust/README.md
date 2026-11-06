<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="README.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Trust store — how to verify a NeoMundi Evidence attestation

`trust-store.json` carries the **public** material needed to verify an
attestation: the signing identity and the Ed25519 **public** key. No private
key material is here, and none ever will be.

| | |
|---|---|
| Signing entity | **NeoMundi Recherche**, association loi 1901, RNA **W563015824**, France |
| Key | `nm-ev-recherche-202611-1` — Ed25519, status `active` |
| Store | `store_id: neomundi-evidence`, `store_kind: production`, `store_version: 1` |
| Declared capacity | **`experimental`** — see the limits below |

---

## Verifying, in three steps

**1. Obtain the store's digest from a channel that is not this repository.**

This matters more than it looks. If you take both the store and its digest
from here, you have checked that this repository agrees with itself — which
proves nothing. **A digest is only useful when it travels by a different
road than the thing it describes.**

That is why **no digest file is published in this repository**: putting one
here would invite exactly the circular check this condition exists to
prevent. The second channel carries a `neomundi.evidence.trust-store-digest/2`
payload with the digest, the `store_version`, and the signer's public
metadata — and **no key material at all**.

**2. Confront the bytes you hold with that digest.**

```sh
sha256sum trust/trust-store.json          # Linux, macOS
Get-FileHash trust/trust-store.json -Algorithm SHA256   # Windows
```

If it differs from the second channel's value, **stop**: one of the two
sources is not telling you the truth. Do not proceed, and tell us.

**3. Verify the attestation, offline.**

```sh
python verify_attestation.py <attestation.jws> \
       --archive <package.zip> \
       --trust-store trust/trust-store.json \
       --store-digest <digest obtained at step 1>
```

A sound result ends with `0 FAIL` and the line
`store digest confronted — PASS`. Without `--store-digest` that line stays
`NOT TESTED`, and the chain is one notch weaker: you would be trusting a
single source.

Nothing in this requires network access, an account, or our cooperation.

---

## What a successful verification establishes

**That NeoMundi Recherche committed to the digest of that exact package.**
The bytes you hold are the bytes the attestation refers to, and the signature
is mathematically sound.

## And what it does not

| | |
|---|---|
| **It is not a legal certification.** | `legal_capacity_to_attest: experimental` means the entity is **named** and has taken a documented decision to attest within a scientific, non-commercial scope, and that **no verification of its powers to commit has been performed**. It is an identity **declared**, never an identity legally **verified** |
| **Cryptographic verification is not identity verification.** | the signature proves the holder of the private key signed. That the holder is lawfully NeoMundi Recherche is a **declaration** carried by this store, not a cryptographic fact. No code can establish it, and the verifier returns a permanent `NOT TESTED` on legal capacity |
| **It says nothing about the content being true.** | a perfectly signed attestation over a fabricated package is cryptographically valid. Signing establishes a commitment and custody, not a fact |
| **It is not a date.** | `attested_at_declared` is declared by the signer. Only a third-party anchor makes a date independent, and not every package carries one |
| **No eIDAS qualification is claimed**, under any configuration. | |

---

## If the key is withdrawn

Two cases, and they are **not** symmetrical:

- **`rotated`** — earlier signatures stay **trusted**. An attestation
  declared before the rotation remains valid.
- **`compromised`** — **every** signature by that key becomes untrusted,
  **retroactively**, whatever date it declares. A thief controls the date
  they write, so no date can contain a compromise.

Either is published as a new `store_version`, with the digest updated on the
second channel. **A `store_version` that never moves while the store changes
is the exact symptom of a substitution.**

## Reporting a problem

A digest that does not match, metadata that disagrees between the two
channels, or a verification that fails where it should pass — tell us. The
limits above are deliberate; a disagreement between channels is not.

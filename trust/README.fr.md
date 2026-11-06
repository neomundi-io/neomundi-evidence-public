<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="README.md">English</a> · <a href="../README.fr.md">← README</a></sub>

# Magasin de confiance — comment vérifier une attestation NeoMundi Evidence

`trust-store.json` porte le matériel **public** nécessaire à la vérification
d'une attestation : l'identité signataire et la clé Ed25519 **publique**.
Aucun matériel privé n'y figure, et il n'y en aura jamais.

| | |
|---|---|
| Entité signataire | **NeoMundi Recherche**, association loi 1901, RNA **W563015824**, France |
| Clé | `nm-ev-recherche-202611-1` — Ed25519, statut `active` |
| Magasin | `store_id: neomundi-evidence`, `store_kind: production`, `store_version: 1` |
| Capacité déclarée | **`experimental`** — voir les limites plus bas |

---

## Vérifier, en trois gestes

**1. Obtenir l'empreinte du magasin par un canal qui n'est pas ce dépôt.**

C'est le geste qui compte le plus. Si vous prenez le magasin *et* son
empreinte ici, vous avez vérifié que ce dépôt est d'accord avec lui-même — ce
qui n'établit rien. **Une empreinte ne sert que si elle voyage par une autre
route que ce qu'elle décrit.**

C'est pourquoi **aucun fichier d'empreinte n'est publié dans ce dépôt** : en
mettre un ici inviterait précisément au contrôle circulaire que cette
condition existe pour empêcher. Le second canal porte une charge
`neomundi.evidence.trust-store-digest/2` avec l'empreinte, la
`store_version` et les métadonnées publiques du signataire — et **aucun
matériel de clé**.

**2. Confronter les octets que vous tenez à cette empreinte.**

```sh
sha256sum trust/trust-store.json          # Linux, macOS
Get-FileHash trust/trust-store.json -Algorithm SHA256   # Windows
```

Si elle diffère de la valeur du second canal, **arrêtez-vous** : l'une des
deux sources ne vous dit pas la vérité. Ne continuez pas, et dites-le-nous.

**3. Vérifier l'attestation, hors ligne.**

```sh
python verify_attestation.py <attestation.jws> \
       --archive <paquet.zip> \
       --trust-store trust/trust-store.json \
       --store-digest <empreinte obtenue au geste 1>
```

Un résultat sain finit par `0 FAIL` et par la ligne
`empreinte du magasin confrontee — PASS`. Sans `--store-digest`, cette ligne
reste `NOT TESTED` et la chaîne perd un cran : vous feriez confiance à une
source unique.

Rien de tout cela n'exige de réseau, de compte, ni notre concours.

---

## Ce qu'une vérification réussie établit

**Que NeoMundi Recherche s'est engagée sur l'empreinte de ce paquet précis.**
Les octets que vous tenez sont bien ceux auxquels l'attestation se réfère, et
la signature est mathématiquement juste.

## Et ce qu'elle n'établit pas

| | |
|---|---|
| **Ce n'est pas une certification juridique.** | `legal_capacity_to_attest: experimental` signifie que l'entité est **nommée** et a pris une décision documentée d'attester dans un cadre scientifique et non commercial, et qu'**aucune vérification de ses pouvoirs n'a été faite**. Identité **déclarée**, jamais identité juridiquement **vérifiée** |
| **Une vérification cryptographique n'est pas une vérification d'identité.** | la signature prouve que le détenteur de la clé privée a signé. Que ce détenteur soit licitement NeoMundi Recherche est une **déclaration** portée par ce magasin, non un fait cryptographique. Aucun code ne peut l'établir, et le vérificateur rend un `NOT TESTED` permanent sur la capacité juridique |
| **Elle ne dit rien de la vérité du contenu.** | une attestation parfaitement signée sur un paquet fabriqué est cryptographiquement valide. Signer établit un engagement et une custody, pas un fait |
| **Ce n'est pas une date.** | `attested_at_declared` est déclaré par le signataire. Seul un ancrage tiers rend une date indépendante, et tous les paquets n'en portent pas |
| **Aucune qualification eIDAS n'est revendiquée**, sous aucune configuration. | |

---

## Si la clé est retirée

Deux cas, et ils ne sont **pas** symétriques :

- **`rotated`** — les signatures antérieures restent **de confiance**. Une
  attestation déclarée avant la rotation reste valide.
- **`compromised`** — **toutes** les signatures de cette clé deviennent non
  fiables, **rétroactivement**, quelle que soit leur date déclarée. Un voleur
  choisit la date qu'il écrit : aucune date ne peut contenir une
  compromission.

L'un comme l'autre se publie sous une nouvelle `store_version`, avec
l'empreinte mise à jour sur le second canal. **Une `store_version` qui ne
bouge pas alors que le magasin change est le symptôme exact d'une
substitution.**

## Signaler un problème

Une empreinte qui ne concorde pas, des métadonnées qui divergent entre les
deux canaux, une vérification qui échoue là où elle devrait passer :
dites-le-nous. Les limites ci-dessus sont délibérées ; un désaccord entre
canaux ne l'est pas.

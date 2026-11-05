<sub>🇬🇧 <a href="DESIGN_SIGNATURE_ANCHORING_V1.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Signature et ancrage externe — architecture proposée

**5 novembre 2026. Proposition soumise à validation. Aucun code n'a été
écrit.** Ce document est le livrable de la phase 4 ; l'implémentation est
explicitement en attente.

Objectif : rendre `cryptographically_attested` atteignable avec une garantie
réelle, démontrable, et vérifiable par un tiers sans nous faire confiance.

---

## Avertissement sur l'ordre des phases

Le brief demande en phase 3 de « définir **puis exécuter** » dix tests, et en
phase 4 de ne pas coder avant validation de l'architecture. Les deux ne
peuvent pas être tenus ensemble : on n'exécute pas les tests d'un mécanisme
qui n'existe pas.

**J'ai tranché pour la phase 4 :** les dix tests sont **définis** ci-dessous
avec leur verdict attendu, et **aucun n'a été exécuté**. Ils deviennent la
grille d'acceptation de l'implémentation, le jour où elle est autorisée.

Une seule chose a été exécutée, et hors du dépôt : une sonde de faisabilité
du composant cryptographique, parce que proposer une architecture sans
vérifier que sa brique centrale fonctionne serait exactement la « capacité
annoncée » que ce produit refuse. Ses clés étaient éphémères et ont été
effacées.

---

# Phase 1 — Audit des capacités existantes

En lecture seule. Aucun dépôt n'a été modifié, aucun service appelé.

## 1.1 Ce qui existe déjà, et qui est réutilisable

**`govern-v3/app/rgc/signing.py` — un mécanisme Ed25519/JWS complet et en
production.**

| Élément | Valeur constatée |
|---|---|
| Algorithme | Ed25519, `alg: "EdDSA"` |
| Format | JWS compact, via `PyJWT` |
| Bibliothèque | `cryptography` + `PyJWT` |
| Identifiant de clé | `kid` dans l'en-tête JWS **et** `integrity.key_id` dans le contrat |
| Clé publique | `public_jwk()` → JWK `OKP` / `Ed25519`, exposée par `GET /v1/rgc/jwks` |
| Objet signé | `{payload_hash, hash_algorithm, schema_version, request_id, timestamp}` — **une attestation courte référençant une empreinte, pas l'objet entier** |
| Canonicalisation déclarée | `sorted-json-utf8` (`RgcIntegrity.canonicalization`) |
| Absence de repli | assumée : `503` si la clé manque, jamais de contrat « empreinte seule » |
| Clé privée | `RGC_SIGNING_PRIVATE_KEY`, graine 32 octets en base64url, par variable d'environnement |

**C'est le patron à réutiliser.** Le format est bon, le choix d'algorithme
est bon, et la décision de signer une *attestation courte référençant une
empreinte* plutôt que l'objet entier est précisément ce dont Evidence a
besoin.

### Trois limites de RGC, qui expliquent ce qui doit être ajouté

**`verify_jws` exige la clé privée.** Elle dérive la clé publique de la clé
privée (`_public_key_pem()` appelle `_load_private_key()`). Il n'existe donc
**aucun chemin de vérification par un tiers** : seul le détenteur du secret
peut vérifier. C'est suffisant pour un contrôle interne, inutilisable pour un
auditeur.

**Le JWKS est un point d'accès HTTP.** Résoudre `key_id` → clé de
vérification suppose d'appeler l'API. Une vérification hors ligne est donc
impossible en l'état.

**Aucune expiration, aucune révocation.** `RgcIntegrity` ne porte ni
`not_after`, ni statut de clé, ni liste de révocation. Le cycle de vie des
clés est à concevoir, et le brief le demande explicitement.

## 1.2 Station — aucune signature

Recherche exhaustive sur `src/station/` : **aucune primitive de signature.**
La seule occurrence est la constante `RGC_JWKS_PATH = "/v1/rgc/jwks"` dans
`connectors/neomundi/contract.py`, jamais appelée pour vérifier quoi que ce
soit.

En revanche, Station porte un composant de grande valeur :
**`src/station/ledger/canonical.py` est une implémentation complète de
RFC 8785 (JCS), sans aucune dépendance externe.** Elle traite les trois
points où `json.dumps` ne suffit pas — écriture ECMAScript des nombres, tri
des clés sur les unités UTF-16, et refus de tout ce qui n'est pas canonisable
sans ambiguïté (NaN, infini, entier au-delà de 2⁵³−1).

**Conséquence directe :** le registre est canonicalisé et **chaîné**, mais
**non signé**. Quiconque peut reconstruire le registre peut reconstruire sa
chaîne. C'est exactement le trou central relevé par l'audit hostile.

## 1.3 Le contrat des quatre niveaux Evidence — vérifié

Lu dans `schemas/evidence-manifest-v1.json` et dans `bind.py` :

```
declared · reference_verifiable · cryptographically_attested · not_demonstrable
```

| Point du contrat | État constaté |
|---|---|
| Le niveau est **dérivé**, jamais lu dans le manifeste | ✅ `controle_revendications` refuse toute revendication excédant le dérivé |
| `cryptographically_attested` inatteignable aujourd'hui | ✅ `controle_signatures` rend toujours `NOT TESTED` |
| L'emplacement de signature **existe déjà** au schéma | ✅ `signatures[]` avec `{algorithm, key_id, value, covers}` |
| Une archive non signée garde son niveau | ✅ aucune signature → `NOT TESTED`, pas `FAIL` |
| Jamais de `PASS` sur un ensemble vide | ✅ corrigé le 5 novembre : zéro revendication éprouvée → `NOT TESTED` |

**Le schéma n'a donc pas à changer pour accueillir la signature.** Il faut
préciser la sémantique de `signatures[]` et ajouter le magasin de confiance,
qui en est absent.

## 1.4 Les cas malformés — régression en place, verdicts structurés

| Vérification | Résultat |
|---|---|
| Les 9 entrées malformées rendent un verdict | ✅ 9 cas `[VERDICT]`, 0 plantage |
| Verdicts lisibles par machine | ✅ `neomundi.evidence.verification-report/1` et `…binding-report/1` |
| Les trois états restent distincts dans le JSON | ✅ champ `state` par contrôle, et `counts` séparés |
| Ce que le rapport n'établit pas est inscrit | ✅ `does_not_establish`, 4 mentions |

## 1.5 Vérification entièrement hors ligne — solution minimale identifiée

**Ed25519 n'est pas vérifiable avec la bibliothèque standard de Python.**
`hashlib` et `hmac` seuls donnent du symétrique, qui ne peut pas servir à une
vérification publique. Il n'y a pas d'échappatoire élégante à ce constat.

Disponible sur ce poste :

| Composant | État |
|---|---|
| `cryptography` | **50.0.0** — Ed25519 présent |
| `PyJWT` | 2.13.0 |
| `openssl` | 3.5.7 |
| `gpg`, `ssh-keygen` | présents |
| `nacl`, `ecdsa`, `PyCryptodome` | absents |

**Sonde de faisabilité exécutée, résultats constatés :**

```
[OK] verification stdlib + cryptography, sans PyJWT
[OK] une charge alteree est refusee
openssl pkeyutl -verify     : Signature Verified Successfully
openssl sur entree alteree  : Signature Verification Failure | code 1
PEM reconstruit depuis le JWK identique : True
```

Quatre enseignements, tous décisifs pour l'architecture :

1. **`PyJWT` n'est pas nécessaire.** Un JWS compact se découpe en trois
   parties base64url avec la bibliothèque standard ; seule la primitive
   `Ed25519PublicKey.verify()` demande `cryptography`. Une dépendance au lieu
   de deux.
2. **`openssl` vérifie la même signature**, sans aucun de nos outils. C'est
   l'argument d'indépendance du dossier, et il est démontré, pas supposé.
3. **Le JWK public suffit** : il reconstruit le PEM à l'identique. Le magasin
   de confiance peut donc être un simple fichier JSON, et la voie `openssl`
   s'en dérive.
4. Une clé publique Ed25519 fait **32 octets**. Le magasin tient sur une
   ligne par clé.

## 1.6 Ce que la signature démontre, et ce que l'ancrage démontre

C'est le point que le brief demande de ne pas confondre, et il mérite d'être
écrit avant toute conception.

| Mécanisme | Démontre | Ne démontre pas |
|---|---|---|
| **Signature** | que le détenteur de la clé `kid` a signé **ces octets-là**, et qu'ils n'ont pas bougé depuis | que le contenu signé soit vrai ; ni **quand** il a été signé |
| **Ancrage externe** | que cette empreinte **existait avant** un instant attesté par un tiers | que le contenu soit vrai ; ni qui l'a produit |
| **Les deux ensemble** | qu'une partie identifiée s'est engagée sur un contenu précis, avant une date qu'elle ne contrôle pas | **toujours pas** que l'exécution mesurée a eu lieu |

**La signature prouve une custody et un engagement, pas un fait.** Une
attestation parfaitement signée portant sur une archive fabriquée est
cryptographiquement valide. Ce que la signature ajoute, c'est qu'on sait
**qui** s'est engagé, et qu'il ne peut plus le nier.

C'est beaucoup, et ce n'est pas la vérité du contenu. Les deux doivent rester
deux lignes de contrôle séparées.

---

# Phase 2 — Conception minimale

## 2.1 Le choix structurant : une signature **détachée**

La signature ne va **pas** dans l'archive.

Le raisonnement est contraignant : l'attestation couvre
`bundle_sha256`, l'empreinte du fichier d'archive. Glisser la signature dans
l'archive changerait ses octets, donc son empreinte, donc invaliderait la
signature qui vient d'être calculée. Circulaire, et insoluble.

Un fichier détaché à côté de l'archive :

```
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip          ← inchangé, à l'octet
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws      ← l'attestation signée
```

**Trois contraintes du brief se trouvent satisfaites d'un coup :**

- *compatibilité avec les archives V0.1* — elles ne sont pas touchées ;
- *aucun changement des corpus gelés* — ils peuvent être attestés
  **rétroactivement**, sans être réouverts ;
- *aucune réécriture des preuves historiques* — rien n'est réécrit, on ajoute
  à côté.

C'est le gain le plus important de cette conception, et il tombe du choix du
détachement.

## 2.2 L'objet signé — `neomundi.evidence.attestation/1`

Une revendication courte, **plate, et uniquement textuelle** :

```json
{
  "schema": "neomundi.evidence.attestation/1",
  "subject_kind": "evidence_bundle",
  "bundle_sha256": "84ff0dec…",
  "manifest_sha256": "…",
  "checksums_sha256": "…",
  "export_schema": "station.export.campagne/2",
  "observation_count": "30",
  "issued_at": "2026-11-05T12:00:00Z",
  "signer_identity": "neomundi-evidence-signer",
  "key_id": "nm-ev-2026-11-a"
}
```

**Pourquoi uniquement des chaînes, `observation_count` compris.** Un flottant
ou un entier dans l'objet signé ramène toute la question de l'écriture
canonique des nombres — celle que `ledger/canonical.py` traite en 250 lignes
et que le `jcs()` d'Evidence, simplifié, **ne traite pas** et le dit dans sa
propre docstring. Interdire les nombres dans l'attestation supprime le
problème au lieu de le gérer. Le coût est un `"30"` au lieu d'un `30` ; le
bénéfice est qu'aucun désaccord de sérialisation n'est possible entre un
signataire et un vérificateur.

**Pourquoi trois empreintes et pas une.** `bundle_sha256` lie le fichier
entier. `manifest_sha256` et `checksums_sha256` permettent à un auditeur
n'ayant reçu qu'une partie du dossier d'ancrer ce qu'il a. C'est de la
défense en profondeur, et un support des livraisons partielles.

**Le transport.** Un JWS compact, dont la charge est portée **verbatim** :

```
base64url(en-tête) . base64url(attestation) . base64url(signature)
```

Conséquence voulue : le vérificateur signe-vérifie **les octets qu'il lit**,
sans jamais reconstruire l'objet. La canonicalisation n'intervient donc nulle
part dans le chemin de vérification — ce qui élimine la classe de bugs la
plus pernicieuse de ce genre de dispositif.

En-tête : `{"alg":"EdDSA","typ":"JOSE","kid":"nm-ev-2026-11-a"}`. Le
vérificateur **refuse tout `alg` autre que `EdDSA`**, et ne lit jamais `alg`
pour choisir un algorithme — il impose le sien. C'est la parade à la famille
d'attaques « algorithm confusion » qui a ravagé les implémentations JWT.

## 2.3 Le magasin de confiance — `trust/neomundi-evidence-keys.json`

Versionné dans le dépôt public. **Clés publiques uniquement.**

```json
{
  "schema": "neomundi.evidence.trust-store/1",
  "updated_at": "2026-11-05T12:00:00Z",
  "keys": [
    {
      "kid": "nm-ev-2026-11-a",
      "kty": "OKP", "crv": "Ed25519", "alg": "EdDSA",
      "x": "<32 octets en base64url>",
      "signer_identity": "neomundi-evidence-signer",
      "status": "active",
      "valid_from": "2026-11-05T00:00:00Z",
      "valid_until": null,
      "superseded_by": null,
      "revocation": null
    },
    {
      "kid": "test-only-do-not-trust",
      "status": "test",
      "…": "clé des exemples publics"
    }
  ]
}
```

### Le cycle de vie, et la distinction qui compte

```json
"revocation": { "kind": "rotated" | "compromised", "at": "…", "reason": "…" }
```

**`rotated`** — la clé a cessé d'être utilisée. Les signatures dont
`issued_at` ≤ `revocation.at` **restent de confiance**. Rien n'est arrivé à
la clé ; on en a changé.

**`compromised`** — **toutes** les signatures de cette `kid` deviennent non
fiables, quel que soit leur `issued_at`. Raison : qui détient la clé privée
peut forger n'importe quel `issued_at`. Faire survivre les signatures
antérieures à une compromission serait faire confiance à un horodatage que
l'attaquant contrôle.

C'est la distinction que la plupart des conceptions ratent, et elle n'est
tenable que parce que les deux cas sont nommés séparément dans le magasin.

### La table de décision du vérificateur

| Situation | `signature` | `confiance` | Niveau dérivé plafonné à |
|---|---|---|---|
| `kid` inconnue du magasin | `NOT TESTED` | `NOT TESTED` | `reference_verifiable` |
| `kid` connue, signature fausse | **`FAIL`** | — | — |
| `kid` `active`, signature bonne | `PASS` | `PASS` | `cryptographically_attested` |
| `kid` `rotated`, `issued_at` dans la fenêtre | `PASS` | `PASS` | `cryptographically_attested` |
| `kid` `rotated`, `issued_at` postérieur | `PASS` | **`FAIL`** | — |
| `kid` `compromised` | `PASS` | **`FAIL`** | — |
| `kid` expirée (`issued_at` > `valid_until`) | `PASS` | **`FAIL`** | — |
| `kid` `status: test`, sans `--allow-test-keys` | `PASS` | **`FAIL`** | — |
| `cryptography` absent | `NOT TESTED` | `NOT TESTED` | `reference_verifiable` |

Une clé inconnue rend **`NOT TESTED` et non `FAIL`** : la signature est
peut-être parfaitement valide, nous ne pouvons simplement pas le savoir. La
dire fausse serait une accusation sans fondement — même raisonnement que pour
un artefact absent, tranché le 5 novembre.

Une clé de test doit être **refusable** : les exemples publics en embarquent
une, et une vérification ordinaire ne doit jamais lui accorder
`cryptographically_attested`.

## 2.4 Les trois lignes de contrôle, jamais fusionnées

Le brief demande la distinction entre signature valide, identité de
confiance, et intégrité du contenu. Trois lignes séparées :

```
[PASS      ] signature cryptographique - EdDSA/Ed25519, cle nm-ev-2026-11-a
[PASS      ] identite de confiance - cle active, signataire neomundi-evidence-signer
[PASS      ] concordance avec l archive - bundle_sha256 recalcule, conforme
[NOT TESTED] ancrage externe - niveau A seulement : `issued_at` reste declare
[NOT TESTED] verite du contenu - une signature n atteste pas un fait
```

`cryptographically_attested` n'est dérivé que si les **trois premières** sont
`PASS`. Une signature valide d'une clé non fiable ne doit jamais se lire
comme une attestation.

## 2.5 L'ancrage — deux niveaux, et seul le second est indépendant de nous

### Niveau A — registre d'ancrage interne, disponible immédiatement

`anchors/anchor-log.jsonl`, dans le dépôt public, append-only et **lui-même
chaîné** :

```json
{"seq":"1","attestation_sha256":"…","bundle_sha256":"…",
 "kid":"nm-ev-2026-11-a","recorded_at":"2026-11-05T12:00:00Z",
 "prev_entry_sha256":null}
```

Le témoin d'ordre est le commit Git ; le témoin de date est l'enregistrement
de poussée de GitHub, que nous n'écrivons pas.

**Ce que le niveau A démontre :** cette empreinte a été publiée dans un
journal public append-only au plus tard au commit *X*, et le journal n'a pas
été réordonné sans réécrire l'historique Git.

**Ce que le niveau A ne démontre pas : l'indépendance vis-à-vis de NeoMundi.**
Nous détenons le dépôt. Un administrateur peut forcer une réécriture. Les
règles d'organisation (`non_fast_forward`, `deletion`) en augmentent le coût ;
elles ne la rendent pas impossible. Et l'organisation GitHub n'est **pas
vérifiée** (`is_verified: false`), donc un auditeur ne peut même pas
s'appuyer là-dessus.

> Le brief demande un « registre d'ancrage indépendant de **l'archive** ». Le
> niveau A y répond : le journal ne vit pas dans l'archive et n'en dépend pas.
> Il ne répond **pas** à l'indépendance vis-à-vis de **l'émetteur**, qui est
> une autre propriété. Les confondre serait la surenchère que ce produit
> s'interdit.

### Niveau B — ancrage par un tiers, à décider séparément

| Candidat | Coût | Indépendance | Vérification hors ligne | Réserve |
|---|---|---|---|---|
| **OpenTimestamps** | gratuit, sans compte | **forte** — ancré sur Bitcoin | **oui**, après une soumission réseau unique | confirmation en quelques heures |
| Sigstore / Rekor | gratuit | forte | partielle — preuve d'inclusion à stocker | identité liée à un fournisseur OIDC |
| Horodatage RFC 3161 | faible à nul | moyenne — dépend de l'autorité | oui | choix de l'autorité à instruire |
| Dépôt chez un notaire | modéré | forte, non technique | sans objet | convient aux trois entités juridiques |

**Recommandation : OpenTimestamps**, seul candidat à la fois gratuit, sans
compte, et dont la preuve se vérifie hors ligne. Décision à prendre à part,
car il introduit une soumission réseau — au moment du scellement seulement,
jamais à la vérification.

**Tant que le niveau B n'existe pas, `issued_at` reste déclaré.** Le contrôle
d'expiration repose donc sur notre parole. C'est le risque résiduel le plus
important de toute la conception, et c'est l'argument décisif en faveur du
niveau B.

## 2.6 Séparation du signataire et du vérificateur

| | Signataire | Vérificateur |
|---|---|---|
| Fichier | `sign.py` | `verify_attestation.py` |
| Clé | privée, lue dans le magasin DPAPI du poste | publique, lue dans le magasin de confiance |
| Dépendance | `cryptography` **requis** | `cryptography` **optionnel** → `NOT TESTED` sinon |
| Écrit | `*.jws` + une ligne au journal d'ancrage | **rien** |
| Exécution | poste de l'opérateur, jamais en CI | n'importe où, hors ligne |

**Règle dure : le vérificateur n'importe jamais le signataire.** Aucun chemin
de code du vérificateur ne peut atteindre une clé privée. C'est vérifiable
statiquement, et ce sera un test.

### Custody de la clé privée

La graine de 32 octets va dans le magasin de secrets existant du poste
(`XML/secrets.cartography.xml`, CLIXML/DPAPI), avec une sauvegarde hors
machine. **Jamais** dans Git, dans une archive, dans un exemple, dans une
variable d'environnement écrite sur disque, ni dans un secret de CI — la
signature n'est pas une étape d'intégration continue.

Une **clé distincte de celle de RGC**, et c'est volontaire : même mécanisme,
même format, même chemin de vérification, mais deux custodies. Réutiliser la
clé de RGC obligerait à toucher la production pour signer un dossier
Evidence, et ferait d'une compromission un incident commun aux deux produits.

## 2.7 La question de la dépendance, traitée franchement

Evidence promet une vérification sans dépendance. Ed25519 est invérifiable en
bibliothèque standard. Trois voies, et je prends les trois :

1. **`cryptography` présent** → vérification complète. Composant maintenu,
   audité, et **déjà dans la pile** du projet : aucun nouveau fournisseur.
2. **`cryptography` absent** → `NOT TESTED`, avec la raison et la ligne
   d'installation. Les 21 contrôles d'intégrité existants restent intacts et
   sans dépendance. Jamais de `PASS`, jamais de `FAIL`.
3. **Voie `openssl` documentée** → l'auditeur vérifie notre signature avec un
   outil qui n'est pas le nôtre. **Démontré fonctionnel.**

**Je ne vendoriserai pas une implémentation Ed25519 en Python pur.** Écrire
notre propre cryptographie pour préserver un slogan « zéro dépendance »
échangerait une garantie réelle contre une garantie cosmétique.

---

# Phase 3 — Tests d'acceptation, définis et non exécutés

## Les dix du brief

| # | Cas | `signature` | `confiance` | `concordance` | Niveau dérivé |
|---|---|---|---|---|---|
| 1 | archive valide, signature valide, ancrage connu | `PASS` | `PASS` | `PASS` | **`cryptographically_attested`** |
| 2 | archive modifiée après signature | `PASS` | `PASS` | **`FAIL`** | aucun — refusée |
| 3 | signature falsifiée | **`FAIL`** | — | — | aucun — refusée |
| 4 | clé publique inconnue | `NOT TESTED` | `NOT TESTED` | `PASS` | `reference_verifiable` |
| 5 | signature valide, ancrage externe absent | `PASS` | `PASS` | `PASS` | `cryptographically_attested`, **ancrage `NOT TESTED`** |
| 6 | ancrage présent mais non concordant | `PASS` | `PASS` | `PASS` | **`FAIL`** sur l'ancrage |
| 7 | archive recalculée après suppression d'une observation | `PASS` | `PASS` | **`FAIL`** | aucun — c'est le cas que la signature **ferme** |
| 8 | métadonnées de signature malformées | **`FAIL`** motivé, jamais une trace d'appels | — | — | aucun |
| 9 | archive historique non signée | `NOT TESTED` | `NOT TESTED` | sans objet | **`reference_verifiable` conservé** |
| 10 | régression GROUNDED-S1 et suites existantes | 19/0/2 et 10/0/8 **inchangés** | | | |

**Le cas 7 est celui qui justifie tout ce chantier.** C'est la limite déclarée
de la suite de falsification depuis le 5 novembre : « une observation effacée
partout, décomptes et sommes refaits » est indétectable **à l'intérieur** de
l'archive. Une attestation signée sur l'empreinte d'origine la détecte. C'est
la première fois qu'une limite déclarée du produit se referme.

**Le cas 9 est la garantie de non-régression du parc existant.** Une archive
non signée n'est pas rejetée : elle garde `reference_verifiable`. L'absence
d'attestation n'est pas un défaut de l'archive.

## Six tests que le brief ne liste pas, et qui découlent de la conception

| # | Cas | Attendu |
|---|---|---|
| 11 | `alg` falsifié dans l'en-tête (`none`, `HS256`) | `FAIL` — le vérificateur impose `EdDSA` et ne lit jamais `alg` pour choisir |
| 12 | clé de test des exemples, sans `--allow-test-keys` | `FAIL` sur la confiance |
| 13 | `compromised` : signature antérieure à la révocation | `FAIL` — contrairement à `rotated` |
| 14 | `rotated` : signature antérieure à la révocation | `PASS` |
| 15 | `cryptography` absent de l'environnement | `NOT TESTED`, et les 21 contrôles inchangés |
| 16 | le vérificateur n'atteint aucune clé privée | vérifié statiquement sur le graphe d'imports |

## Deux règles transversales, testées explicitement

- **Jamais de `PASS` sur un ensemble vide de contrôles.** Déjà appliqué depuis
  le 5 novembre, à étendre aux nouvelles lignes.
- **Les trois états restent distincts**, dans le texte comme dans le JSON.

---

# Phase 4 — Risques résiduels, coût, et ce qui reste à décider

## Risques résiduels

| # | Risque | Portée | Atténuation |
|---|---|---|---|
| R-1 | **Aucune horloge de confiance avant le niveau B.** `issued_at` est déclaré, donc l'expiration repose sur notre parole | **élevée** | niveau B ; et le dire à chaque exécution |
| R-2 | **Une signature n'est pas la vérité du contenu.** Une attestation parfaite sur une archive fabriquée est valide | **élevée** | trois lignes séparées ; `verite du contenu` toujours `NOT TESTED` |
| R-3 | Au niveau A, nous sommes à la fois émetteur et gardien du journal | élevée | niveau B ; publier l'empreinte du magasin sur un second canal |
| R-4 | Une compromission de clé est **rétroactive** | élevée | `kind: compromised` invalide tout ; procédure de rotation écrite |
| R-5 | Magasin de confiance et journal d'ancrage servis par la **même** source | moyenne | publier l'empreinte du magasin sur le .org et la carte MCP |
| R-6 | Organisation GitHub **non vérifiée** (`is_verified: false`) | moyenne | ne jamais invoquer GitHub comme corroboration d'identité |
| R-7 | Dérive de version de `cryptography` chez le vérificateur | faible | la voie `openssl`, indépendante de notre pile |
| R-8 | Perte de la clé privée | moyenne | sauvegarde hors machine ; une perte n'invalide pas les signatures passées |

## Coût et complexité de maintenance

| Élément | Volume estimé |
|---|---|
| `sign.py` | ~150 lignes |
| extension du vérificateur | ~200 lignes |
| magasin de confiance + journal d'ancrage | ~80 lignes |
| schémas | 2 — attestation, magasin de confiance |
| tests | ~400 lignes, 16 cas |
| documentation | 2 paires EN/FR |

**Dépendances ajoutées : une**, `cryptography`, déjà présente dans la pile du
projet, et **optionnelle** côté vérificateur.

**Le coût récurrent n'est pas du code, c'est de la discipline de custody.**
Une rotation de clé demande : générer, inscrire au magasin, marquer
l'ancienne `rotated`, commiter, et ne jamais réutiliser une `kid`. Le niveau B
ajoute une soumission réseau au scellement, jamais à la vérification.

## Ce qui reste à décider, et que je ne décide pas

1. **Le niveau B, et lequel.** OpenTimestamps est ma recommandation ; il
   introduit une soumission réseau et une dépendance externe au scellement.
2. **L'identité du signataire.** `neomundi-evidence-signer` est un nom
   technique. Laquelle des **trois entités juridiques** s'engage — association
   FR, Louis M Sàrl, ou l'organisation GitHub ? Une signature est un
   engagement ; cette question est juridique avant d'être technique.
3. **Attester rétroactivement les archives gelées ?** C'est possible sans les
   toucher, et cela refermerait le cas 7 sur le parc existant. Mais une
   attestation émise le 5 décembre sur une archive du 5 novembre atteste la
   **custody au 5 décembre**, pas l'origine — et doit le dire.
4. **Publier le magasin de confiance ailleurs que dans ce dépôt**, pour lever
   R-5.

---

## Ce que cette proposition n'établit pas

Aucun code n'a été écrit. Les dix-six tests sont **définis, non exécutés**.
Les volumes de lignes sont des **estimations**. La seule chose mesurée est la
sonde de faisabilité du composant cryptographique, dont les clés étaient
éphémères et ont été effacées.

Ni l'API, ni Station, ni les corpus gelés, ni les campagnes de Sergei n'ont
été touchés : cette phase était en lecture seule, et l'est restée.

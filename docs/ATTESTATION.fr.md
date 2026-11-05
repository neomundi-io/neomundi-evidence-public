<sub>🇬🇧 <a href="ATTESTATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Attestation signée — `cryptographically_attested`

Le quatrième niveau de garantie est désormais **atteignable**. Ce document dit
par quel mécanisme, ce qu'il démontre, et ce qu'il ne démontrera jamais.

Conception validée : [`DESIGN_SIGNATURE_ANCHORING_V1.fr.md`](DESIGN_SIGNATURE_ANCHORING_V1.fr.md).

---

## Ce qu'une attestation établit

> Qu'une **partie identifiée s'est engagée** sur l'empreinte précise d'un
> dossier de preuve, et que le dossier que vous tenez est bien celui-là.

Et ce qu'elle n'établit pas, à dire dans la même phrase :

> Ni que l'exécution mesurée a eu lieu, ni **quand** elle a eu lieu, ni que la
> date de signature soit vraie, ni que le contenu signé soit vrai.

**Signer prouve un engagement et une custody, pas un fait.** Une attestation
parfaitement signée sur une archive fabriquée est cryptographiquement valide.
Ce que la signature ajoute, c'est qu'on sait **qui** s'est engagé, et qu'il ne
peut plus le nier.

---

## Le mécanisme

**Ed25519/EdDSA, JWS compact détaché.** Même algorithme, même format et même
forme de clé publique (JWK `OKP`/`Ed25519`) que `govern-v3/app/rgc/signing.py`
en production — un seul chemin de vérification pour les deux produits, avec
deux custodies distinctes.

**L'attestation est détachée, et ce n'est pas esthétique.** Elle porte
l'empreinte du **fichier** d'archive ; la glisser dans l'archive changerait
cette empreinte et invaliderait la signature qu'on vient de calculer.
Circulaire.

```
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip          ← inchangé, à l'octet
NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws      ← l'attestation
```

Trois conséquences, toutes voulues : les archives **V0.1 ne sont pas
touchées**, les **corpus gelés** restent gelés, et une archive historique peut
être attestée **rétrospectivement** sans être réouverte.

---

## Emploi

```sh
# 1. une clé, HORS du dépôt -- l outil refuse d en écrire une dedans
python sign.py genkey --kid nm-ev-2026-11-a \
    --out ~/cles/privee.json --trust-store-out ~/cles/magasin.json \
    --valid-from 2026-11-05T00:00:00Z

# 2. attester, sans toucher l archive
python sign.py attest --archive <archive.zip> --key ~/cles/privee.json \
    --attested-at 2026-11-05T14:00:00Z --kind retrospective \
    --out <archive.zip>.jws

# 3. vérifier, hors ligne, avec la seule clé publique
python verify_attestation.py <archive.zip>.jws \
    --archive <archive.zip> --trust-store ~/cles/magasin.json

# 4. et faire monter une liaison au quatrième niveau
python bind.py verify manifest.json --archive <archive.zip> \
    --attestation <archive.zip>.jws --trust-store ~/cles/magasin.json
```

`--attested-at` est **exigé** : l'outil ne lit jamais l'horloge, de sorte que
deux exécutions sur les mêmes entrées rendent le même jeton, à l'octet.

---

## Les quatorze lignes de contrôle

Trois d'entre elles sont les **piliers** : le niveau n'est atteint que si les
cinq marqués ★ sont `PASS`.

| Contrôle | État possible |
|---|---|
| attestation lisible | `PASS` / `FAIL` |
| forme de l'attestation | `PASS` / `FAIL` |
| ★ profil de canonicalisation | `PASS` / `FAIL` |
| ★ en-tête : algorithme imposé | `PASS` / `FAIL` |
| magasin de confiance lisible | `PASS` / `FAIL` |
| ★ **signature cryptographique** | `PASS` / `FAIL` / `NOT TESTED` |
| ★ **identité de confiance** | `PASS` / `FAIL` / `NOT TESTED` |
| capacité juridique du signataire | **toujours `NOT TESTED`** |
| séparation des cinq identités | `PASS` / `NOT TESTED` |
| ★ **concordance avec l'archive** | `PASS` / `FAIL` / `NOT TESTED` |
| nature de l'attestation | `PASS` |
| horodatage indépendant | **toujours `NOT TESTED`** |
| ancrage tiers | **toujours `NOT TESTED`** |
| concordance de la preuve d'ancrage | `PASS` / `FAIL` / `NOT TESTED` |
| vérité du contenu | **toujours `NOT TESTED`** |

Les trois piliers en gras sont les trois choses que le cahier des charges
demande de ne jamais fusionner :

```
[PASS      ] signature cryptographique - EdDSA/Ed25519, cle nm-ev-2026-11-a
[PASS      ] identite de confiance - cle active, signataire nm-recherche
[PASS      ] concordance avec l archive - bundle_sha256 recalcule
```

**Une signature valide d'une clé non fiable ne se lit jamais comme une
attestation.** C'est le cas 12 de la suite de tests : signature `PASS`,
confiance `FAIL`, aucun niveau.

---

## Le profil de canonicalisation, précisément spécifié

`neomundi-jcs-strings/1`, dans [`canonical.py`](../canonical.py) :

1. UTF-8, sans BOM ;
2. `json.dumps(objet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` ;
3. types permis : chaîne, `null`, objet, tableau — **nombres et booléens
   interdits** ;
4. toute clé respecte `^[a-z0-9_]+$`.

**Pourquoi il est équivalent à RFC 8785 sur son domaine.** JCS est difficile
sur trois points ; le profil en neutralise deux et hérite du troisième :

- **les nombres.** JCS impose l'écriture ECMAScript (`1.0` → `1`, `1e-07` →
  `1e-7`), ce que `station/ledger/canonical.py` traite en ~250 lignes. **Les
  interdire supprime la question au lieu de la gérer.** Un décompte voyage
  donc en chaîne : `"30"`, pas `30`.
- **l'ordre des clés.** JCS trie sur les unités UTF-16, Python sur les points
  de code. **En restreignant les clés à l'ASCII, les deux ordres coïncident.**
- **l'échappement des chaînes.** `json.dumps` y est déjà conforme.

Hors de ce domaine, l'équivalence **ne tient pas** — c'est pourquoi le domaine
est restreint plutôt que l'implémentation étendue.

**Le profil n'intervient jamais dans la vérification d'une signature.** Le
vérificateur vérifie les octets portés *verbatim* par le JWS. Il recanonicalise
seulement pour **contrôler la conformité au profil**, qui est un contrôle
distinct — et le cas 22 le prouve : une charge non canonique mais correctement
signée donne profil `FAIL` et signature `PASS`.

---

## Les cinq identités, séparées

Les confondre est la façon la plus courante de surenchérir. Le schéma les
tient à part :

| Rôle | Ce qu'il est | Capacité à s'engager |
|---|---|---|
| `signer` | la partie qui **s'engage** | déclarée, **jamais vérifiée** |
| `technical_operator` | qui a exécuté l'opération, sur quelle machine | sans objet |
| `measurement_author` | qui a produit les mesures du corpus attesté | sans objet |
| `key_custodian` | qui détient et contrôle la clé privée | sans objet |
| `trust_authority` | un tiers garant de la clé ou du temps | `null` aujourd'hui |

**Succession, et non révocation.** Une identité n'est pas révocable : la
révocation porte sur les **clés**. Une entité peut recevoir un successeur —
une société commerciale après une association — et **ajouter ce successeur
n'invalide aucune attestation antérieure**. Le vérificateur signale la
succession sans rien rejuger.

**La capacité juridique est toujours `NOT TESTED`.** Aucun code n'établit
qu'une entité peut légalement s'engager. Le magasin porte la valeur déclarée
(`unverified` à ce stade pour NeoMundi Recherche), et le vérificateur la
rapporte telle quelle.

---

## Le magasin de confiance

**Hors du dépôt Evidence.** Le dépôt n'embarque qu'un magasin de **test**,
sous `examples/attestation/`, dont les clés n'accordent rien sans
`--allow-test-keys`.

Matériel public uniquement : un magasin contenant un champ de clé privée est
**refusé** (cas 17), de même qu'un `kid` en double (cas 18) ou une politique
de vérification inconnue (cas 19) — refusée, et non interprétée.

### Rotation et compromission ne se comportent pas pareil

| Situation | Verdict | Pourquoi |
|---|---|---|
| `rotated`, signature **antérieure** | `PASS` | la clé a cessé d'être utilisée ; rien ne lui est arrivé |
| `rotated`, signature **postérieure** | `FAIL` | elle n'aurait pas dû servir |
| `compromised`, **quelle que soit la date** | `FAIL` | qui détient la clé privée peut forger n'importe quel `attested_at_declared` ; faire survivre les signatures antérieures reviendrait à faire confiance à un horodatage que l'attaquant contrôle |
| clé **inconnue** du magasin | `NOT TESTED` | la signature est peut-être valide, nous ne pouvons pas le savoir. La dire fausse serait une accusation sans fondement |
| clé **expirée** | `FAIL` | hors de sa fenêtre déclarée |

---

## Attestation rétrospective

Un corpus déjà gelé peut être attesté **sans être touché**. Mais l'attestation
dit alors exactement ce qu'elle fait :

```
[PASS      ] nature de l attestation - RETROSPECTIVE : elle constate une
             verification faite le 2026-11-05T14:00:00Z (declare), sur un
             corpus gele le 2026-11-05T10:26:04Z (conserve depuis son propre
             manifeste). Elle ne pretend PAS que le corpus ait ete signe a la
             date de son execution.
```

La **date de gel est conservée** depuis le manifeste du sujet, jamais
inventée ; une attestation rétrospective qui l'omettrait est refusée, au
signataire comme au vérificateur (cas 21).

---

## Vérifier sans aucun de nos outils

C'est l'argument d'indépendance, et il est **démontré**. Le JWK public
reconstruit le PEM à l'identique, donc `openssl` vérifie notre signature
tout seul :

```sh
# 1. découper le JWS, et écrire les octets signés
JWS=$(cat archive.zip.jws)
printf '%s' "${JWS%.*}" > signe.bin

# 2. extraire la signature (3e segment, base64url → binaire)
python - <<'PY'
import base64, pathlib
s = pathlib.Path("archive.zip.jws").read_text().strip().split(".")[2]
pathlib.Path("sig.bin").write_bytes(
    base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))
PY

# 3. bâtir le PEM depuis les 32 octets de `x` du magasin
#    (préfixe DER SubjectPublicKeyInfo pour Ed25519)
python - <<'PY'
import base64, json, pathlib
x = json.loads(pathlib.Path("magasin.json").read_text())["keys"][0]["x"]
der = bytes.fromhex("302a300506032b6570032100") + \
      base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
pathlib.Path("pub.pem").write_bytes(
    b"-----BEGIN PUBLIC KEY-----\n" + base64.encodebytes(der) +
    b"-----END PUBLIC KEY-----\n")
PY

# 4. vérifier — avec openssl, pas avec nous
openssl pkeyutl -verify -pubin -inkey pub.pem -rawin -in signe.bin -sigfile sig.bin
```

Résultat constaté sur l'attestation réelle :

```
attestation intacte    Signature Verified Successfully
attestation alteree    Signature Verification Failure
```

---

## Dépendance, dite franchement

**Ed25519 n'est pas vérifiable avec la bibliothèque standard de Python.** Trois
voies, et les trois existent :

1. **`cryptography` présent** → vérification complète. Composant maintenu,
   audité, et déjà dans la pile du projet.
2. **`cryptography` absent** → `NOT TESTED`, avec la raison et la ligne
   d'installation. **Jamais `PASS`, jamais `FAIL`** (cas 15). Et les 21
   contrôles d'intégrité de `verify.py` restent entièrement sans dépendance.
3. **Voie `openssl`** → ci-dessus.

**Aucune implémentation Ed25519 en Python pur n'a été vendorisée.** Écrire
notre propre cryptographie pour préserver un slogan « zéro dépendance »
échangerait une garantie réelle contre une garantie cosmétique.

---

## Matrice de tests

`python tests/test_attestation.py <archive> [corpus]` → **25/25 conformes.**
Toutes les clés sont éphémères, générées à l'exécution et effacées à la fin.

| # | Cas | Résultat observé |
|---|---|---|
| 1 | archive valide, signature valide, clé connue | **`cryptographically_attested`** |
| 2 | archive modifiée après signature | signature `PASS`, **concordance `FAIL`** — la signature n'est pas en cause |
| 3 | signature falsifiée | signature `FAIL` |
| 4 | clé publique inconnue | `NOT TESTED` et **non** `FAIL` ; aucun niveau |
| 5 | signature valide, ancrage absent | niveau atteint, ancrage `NOT TESTED` |
| 6 | ancrage présent mais non concordant | **`FAIL`** sur la concordance de la preuve ; la *validité* de l'ancrage reste `NOT TESTED` |
| 7 | **archive recalculée après suppression d'une observation** | `verify.py` seul : **0 FAIL interne**. L'attestation : **concordance `FAIL`** |
| 8 | métadonnées de signature malformées (5 formes) | **5/5** rendent un `FAIL` motivé, sans trace d'appels |
| 9 | archive historique **non signée** | liaison acceptée à `reference_verifiable`, attestation `NOT TESTED` |
| 9b | **`bind.py --attestation`** : élévation transitive | liaison élevée à `cryptographically_attested` |
| 9c | `bind.py --attestation` non fiable | **aucune élévation** — la liaison retombe |
| 10 | non-régression `verify.py` GROUNDED-S1 | `19 PASS, 0 FAIL, 2 NOT TESTED` — inchangé |
| 11 | `alg` falsifié (`none`, `HS256`, `RS256`) | **3/3 refusés** — l'algorithme est imposé, jamais lu pour choisir |
| 12 | clé `test` sans `--allow-test-keys` | signature `PASS`, **confiance `FAIL`** |
| 13 | clé **compromise**, signature antérieure | **`FAIL` rétroactif** |
| 14 | clé **rotation**, signature antérieure | `PASS` — la différence avec une compromission |
| 14b | clé rotation, signature **postérieure** | `FAIL` |
| 15 | `cryptography` absent | signature `NOT TESTED`, aucun niveau |
| 16 | le vérificateur n'atteint aucune clé privée | n'importe pas `sign` ; aucune primitive privée |
| 17 | magasin contenant un champ de clé privée | magasin **refusé** |
| 18 | `kid` en double dans le magasin | **refusé** |
| 19 | politique de vérification inconnue | **refusée**, pas interprétée |
| 20 | `kid` d'en-tête ≠ `kid` de la charge | **refusé** |
| 21 | attestation rétrospective sans date de gel | **refusée** |
| 22 | charge **non canonique** mais correctement signée | profil `FAIL`, signature `PASS` — les deux contrôles sont bien distincts |

### Un défaut trouvé en revue, et sa cause de fond

Le chemin `bind.py --attestation` était **cassé** dans le commit candidat
initial : l'élévation transitive échouait toujours par
`AttributeError: 'Namespace' object has no attribute 'anchor_proof'`.

La cause n'était pas l'oubli d'un champ, mais sa **possibilité** :
`bind.py` reconstruisait à la main le jeu d'arguments du vérificateur, si
bien qu'ajouter une option d'un côté cassait l'autre en silence. La
correction est une **fabrique unique**, `arguments_de_verification()` : un
nouveau champ y reçoit son défaut, et tous les appelants en héritent.

Aucun test ne couvrait ce chemin — c'est pour cela qu'il est passé. Les cas
**9b** et **9c** l'éprouvent désormais. Un chemin non testé est un chemin
cassé.

### Le cas 7 referme une limite déclarée

Depuis le 5 novembre, la suite de falsification porte une limite assumée :
« une observation effacée partout, décomptes et sommes refaits » est
**indétectable à l'intérieur** de l'archive. Le test le confirme : `verify.py`
rend **0 FAIL** sur l'archive amputée, qui est intérieurement parfaite.

L'attestation, elle, la détecte — parce que l'empreinte d'origine a été signée
ailleurs. **C'est la première fois qu'une limite déclarée du produit se
referme.**

---

---

## Le besoin futur d'un mode strict, pour les usages automatisés

`NOT TESTED` est **le bon verdict pour un lecteur humain**, et il est conservé
tel quel : une clé inconnue du magasin peut parfaitement avoir produit une
signature valide, et la déclarer fausse serait une accusation sans fondement.
Le vérificateur sort donc en **code 0**.

**Mais ce choix est un piège pour un consommateur automatisé.** Une chaîne
d'intégration qui lit le code de sortie ne distingue pas aujourd'hui :

| Situation réelle | Code de sortie | Ce qu'un script en conclut |
|---|---|---|
| niveau `cryptographically_attested` atteint | `0` | « attesté » |
| clé **inconnue** du magasin | `0` | « attesté » — **faux** |
| `cryptography` **absent** de l'environnement | `0` | « attesté » — **faux** |
| aucun magasin fourni | `0` | « attesté » — **faux** |

Les trois dernières lignes sont des **non-vérifications**, pas des succès. Le
texte et le rapport JSON les disent clairement — `attained_level` vaut `null`
et chaque contrôle porte son `state` — mais un script qui se contente du code
de sortie les lit comme un feu vert.

### Ce que le mode strict devrait faire

**Non implémenté. À décider, et à ne pas improviser.**

Un drapeau `--strict` ferait sortir en **code non nul** dès qu'un **pilier**
est `NOT TESTED`, sans changer aucun verdict : les lignes resteraient
`NOT TESTED`, seul le code de sortie changerait. Les cinq piliers sont le
profil de canonicalisation, l'algorithme imposé, la signature, la confiance et
la concordance.

Les lignes **définitivement** `NOT TESTED` — capacité juridique, horodatage
indépendant, ancrage tiers, vérité du contenu — ne devraient **jamais** entrer
dans ce calcul : elles ne seront jamais `PASS`, et un mode strict qui les
compterait serait toujours rouge, donc inutile.

Trois propriétés à tenir :

1. **le mode strict ne modifie aucun verdict**, il ne change que le code de
   sortie. Transformer un `NOT TESTED` en `FAIL` réintroduirait la fusion des
   états que ce produit interdit ;
2. **le défaut reste non strict**, pour qu'une exécution humaine continue de
   rendre un diagnostic plutôt qu'un refus ;
3. **le rapport JSON doit porter le mode appliqué**, sinon deux exécutions au
   même verdict et au code de sortie différent seraient indistinguables après
   coup.

**Recommandation d'usage, dès maintenant et sans attendre ce mode :** un
consommateur automatisé ne doit pas lire le code de sortie, mais le rapport
JSON — `attained_level` et le `state` de chaque pilier. C'est déjà suffisant,
et c'est déjà juste.

## Limites résiduelles

| | Portée |
|---|---|
| **`attested_at_declared` est déclaré.** Aucune horloge de confiance. Le contrôle d'expiration repose donc sur la parole du signataire | **élevée** — c'est l'argument décisif pour un ancrage tiers |
| **Aucun ancrage tiers n'est implémenté.** OpenTimestamps est prévu ; le champ existe et n'élève aucun niveau | **élevée** |
| **Une signature n'est pas la vérité du contenu** | **élevée**, et définitive |
| **La capacité juridique du signataire n'est pas vérifiable** par du code, et reste `unverified` | élevée — question juridique |
| Une compromission de clé est **rétroactive** : elle invalide tout | moyenne, traitée |
| Le magasin de confiance n'est pas encore **publié sur un second canal** | moyenne |
| Les archives V0.1 **non signées** ne gagnent rien automatiquement : il faut les attester | faible, assumé |

---

## Fichiers

| | |
|---|---|
| [`canonical.py`](../canonical.py) | le profil `neomundi-jcs-strings/1`, partagé signataire/vérificateur |
| [`sign.py`](../sign.py) | le signataire — clé privée, refuse d'écrire dans le dépôt |
| [`verify_attestation.py`](../verify_attestation.py) | le vérificateur — public seulement, n'importe jamais le signataire |
| `schemas/evidence-attestation-v1.json` | l'objet signé |
| `schemas/evidence-trust-store-v1.json` | le magasin, ses états et sa politique |
| `examples/attestation/` | une attestation réelle et un magasin de **test** — clé privée détruite |
| `tests/test_attestation.py` | 23 cas de sécurité, clés éphémères |

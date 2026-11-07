# NeoMundi Evidence — mode d'emploi

**7 novembre 2026.** Chaque commande ci-dessous a été **exécutée** avant
d'être écrite ici. Les codes de sortie ont été mesurés, non supposés.

Cinq niveaux sont employés partout, et ils ne sont pas interchangeables :

| Niveau | Sens |
|---|---|
| **IMPLÉMENTÉ** | le code existe et s'exécute |
| **TESTÉ** | couvert par une suite automatisée |
| **DÉMONTRÉ** | exécuté et **observé** au moins une fois |
| **QUALIFIÉ** | exercé de bout en bout sur un cas **réel**, verdict consigné |
| **NON CONFIRMÉ** | affirmé, jamais observé |

> Une fonctionnalité éprouvée uniquement sur fixtures n'est **jamais** décrite
> comme validée en conditions réelles.

---

## 1. Ce que c'est

Un ensemble d'outils en ligne de commande qui prennent une **archive de
campagne** produite par Station et établissent ce que ses octets permettent
d'affirmer — et ce qu'ils ne permettent pas.

| | Rôle | Ce qu'il ne fait pas |
|---|---|---|
| **Measurement** | l'instrument qui mesure | il ne sait pas quel code l'a produit |
| **Station** | le cadre d'observation et de campagne | il n'étalonne rien |
| **Evidence** | l'intégrité et la vérification | il ne mesure rien, et ne juge aucun contenu |

🔴 Evidence n'est **ni** une certification, **ni** une validation
scientifique, **ni** une garantie juridique, **ni** un moniteur de trafic de
production.

---

## 2. Prérequis

### Pour vérifier une archive reçue — le cas courant

**Python 3, et rien d'autre.** `verify.py` n'importe que la bibliothèque
standard.

**DÉMONTRÉ** : avec `cryptography` **et** `opentimestamps` bloqués,
`verify.py` rend **le même** bilan — la CI l'impose dans un emploi dédié.

### Pour vérifier une attestation

`cryptography` est nécessaire, plus le magasin de confiance (matériel public)
et, idéalement, son empreinte obtenue par un **second canal**.

### Pour signer

La clé privée. **Aucune vérification n'exige de clé privée** — c'est une
propriété de conception, pas une commodité.

---

## 3. Codes de sortie — mesurés, non supposés

| Code | Sens |
|---|---|
| `0` | aucun `FAIL` |
| `1` | au moins un `FAIL` |
| `2` | `--strict`, et une garantie **requise** n'est pas démontrée |

### 🔴 Un `0` sous `--strict` ne signifie pas « mieux vérifié »

Mesuré le 7 novembre sur la fixture de CI :

| Invocation | Code |
|---|---|
| `verify.py <archive> --corpus <corpus>` | `0` — 20 PASS, 0 FAIL, 2 NOT TESTED |
| `verify.py <archive>` | `0` — 18 PASS, 0 FAIL, 3 NOT TESTED |
| `verify.py <archive> --corpus <corpus> --strict` | `0` |
| `verify.py <archive> --strict` *(sans corpus)* | **`2`** |

La fixture **déclare** des enregistrements de rejeu ; sans corpus, leurs
entrées ne peuvent pas être confrontées, donc une garantie **requise**
manque. La lecture exacte est : *rien de requis ne manque **parmi ce qui est
déclaré**.* Une archive qui déclare moins est exigible de moins.

---

## 4. Les douze opérations

### 4.1 Produire une mesure — **QUALIFIÉ**

Le rôle de Station, documenté chez elle. Le préflight n'émet **aucun** appel ;
`--execute` est ce qui les autorise.

```sh
station run-slot <pack> <campagne> --slot 12:00:00 --var-dir <rép> \
  --ledger <rép>/ledger.jsonl --index <rép>/index.sqlite \
  --max-units 1 --max-attempts 1            # préflight seul
#   ... la même commande plus --execute      # émet les appels
```

**Limite** — une observation ne dit rien d'une distribution, et
`model_served` est l'**affirmation du fournisseur**.

### 4.2 Vérifier le chaînage du registre — **QUALIFIÉ**

```sh
station ledger verify --path <ledger.jsonl>
```

**Sortie** : le nombre d'enregistrements, l'**empreinte de tête**, et
`chaîne vérifiée`.

**Limite** — le chaînage attrape une altération **incohérente**. Une
réécriture complète du registre produirait une chaîne valide.

### 4.3 Exporter — **QUALIFIÉ**

```sh
station campaign export <campagne> --sortie <out.zip> --registre <ledger.jsonl>
```

**Limite** — un export est une **projection**. Le registre conserve
`response_text` ; l'export n'en porte que l'**empreinte**. Voir §6.

### 4.4 Vérifier l'intégrité — **QUALIFIÉ**

```sh
python verify.py <archive.zip> [--corpus <rép>] [--json <rapport.json>] [--strict]
```

**Observé sur Q-2** (réel) : **17 PASS, 0 FAIL, 4 NOT TESTED**, code `0`.

🔴 **`--corpus` ne change rien sur une archive sans enregistrement de rejeu.**
Q-2 n'en porte aucun : la ligne reste `NOT TESTED` — *« aucun enregistrement
de provenance »* — quel que soit le chemin fourni. **L'outil n'est pas en
cause** : sur l'archive de démonstration, qui déclare 4 enregistrements de
rejeu, un corpus manquant rend **`FAIL` — « absents 4 »**. Un corpus manquant
ne passe jamais en silence ; il faut simplement qu'il y ait quelque chose à
confronter.

**Limite** — `verify.py` contrôle l'intégrité **interne**. L'**identité** du
fichier est ce que l'attestation couvre. Voir §5·C.

### 4.5 Vérifier la provenance — **QUALIFIÉ**

```sh
python adapters/provenance.py <archive.zip> [--out <json>] [--md <md>] [--strict]
```

**Sortie** : le parcours `Exécution → Mesure → Évaluateur → Configuration →
Export → Preuve`, chaque ligne portant sa nature — `CONTROLE`, `DECLARE`,
`NON DEMONTRABLE` — puis un **niveau de provenance**.

**Observé sur Q-2** : **11 PASS, 0 FAIL, 7 NOT TESTED**, niveau
`instrument_declare_et_configure`.

**Trois niveaux existent, et il n'y en a pas de quatrième.**
`instrument_verifie` ne peut pas exister : l'établir exigerait d'**observer la
mesure**, ce qu'une archive ne fait pas.

### 4.6 Attester — **QUALIFIÉ**

```sh
python sign.py attest --archive <zip> --key <cle.json> --out <out.jws> \
  --attested-at <UTC> --kind contemporaneous --signer <id> \
  --measurement-author <id> --custodian <id> --register <registre.txt>
```

L'outil **ne lit pas l'horloge** : `--attested-at` est explicite, pour que
deux exécutions rendent le même jeton. `--register` n'est pas optionnel en
pratique : **sans lui, une compromission de clé ne peut pas être
circonscrite**.

### 4.7 Vérifier une signature — **QUALIFIÉ**

```sh
python verify_attestation.py <attestation.jws> --archive <zip> \
  --trust-store <magasin.json> --store-digest <sha256> --strict
```

**Observé sur Q-2** : **11 PASS, 0 FAIL, 4 NOT TESTED**, niveau
`cryptographically_attested`, `--strict` code `0`.

**Refus mesurés :**

| Situation | Code |
|---|---|
| clé `test` **sans** `--allow-test-keys` | **`1`** — *« elle n'accorde aucune attestation »* |
| magasin non confronté, sous `--strict` | **`2`** |
| l'archive ne correspond pas à l'attestation | **`1`** |

Sans `--store-digest`, la ligne du magasin reste `NOT TESTED` : *un magasin
non confronté n'est pas faux — il est non confronté.*

### 4.8 Horodatage indépendant — **IMPLÉMENTÉ, TESTÉ**

```sh
python timestamp.py stamp   <sujet> --stamped-at <UTC>       # RÉSEAU
python timestamp.py inspect <preuve.ots>                     # hors ligne
python timestamp.py verify  <preuve.ots> --subject <sujet> [--strict]
python timestamp.py upgrade <preuve.ots>                     # RÉSEAU
```

**Mesuré sur la preuve livrée** (`…zip.jws.ots`, 786 octets) :

| Invocation | Code | Résultat |
|---|---|---|
| `inspect` | `0` | magie, version 1, SHA-256 |
| `verify --subject <le fichier signé>` | `0` | **3 PASS, 0 FAIL, 4 NOT TESTED** — la liaison tient |
| `verify --strict` | **`2`** | la preuve est `PENDING` |
| `verify --subject <mauvais fichier>` | **`1`** | *« la preuve s'engage sur d533518f…, le sujet se hache sur … »* |

🔴 **Une preuve `PENDING` n'atteste AUCUNE date.** Elle dit qu'un calendrier
s'est engagé à inclure l'empreinte dans une transaction future. La preuve
livrée porte **4 attestations `PENDING` et 0 Bitcoin**.

🔴 **Aucune qualification eIDAS.** OpenTimestamps n'est pas un prestataire de
services de confiance qualifié, et rien ici ne doit être présenté comme un
horodatage qualifié.

**Cet outil vérifie la liaison, pas le temps.** Valider une attestation
Bitcoin demande un en-tête de bloc — une source de confiance que nous n'avons
pas. Il **délègue** : `ots verify <preuve.ots>`.

**NON CONFIRMÉ** — aucune attestation produite par ce projet ne porte
d'ancrage : celle de Q-2 a `external_anchor: null`.

### 4.9 Réconcilier un reçu externe — **TESTÉ, DÉMONTRÉ sur fixtures**

```sh
python adapters/reconcile.py <recu.json> --archive <zip> --map <carte.json> \
  [--observation <id>] [--supplied <matériau>] [--tolerance 1e-09] [--strict]
```

🔴 **Cinq verdicts, pas deux :**

| Verdict | Sens |
|---|---|
| `MATCHED` | les deux valeurs concordent, dans la tolérance |
| `MISMATCHED` | elles diffèrent — **les deux sont conservées**, rien n'est tranché |
| `MISSING` | le reçu ne porte pas ce champ |
| `NOT COMPARABLE` | les deux valeurs existent mais ne sont pas de même nature |
| `NOT VERIFIABLE` | la valeur du reçu n'est pas confrontable à ce que nous détenons |

**Observé** sur la fixture livrée : `4 MATCHED, 2 MISMATCHED, 1 MISSING,
1 NOT COMPARABLE, 1 NOT VERIFIABLE`. Sur un écart : *« les deux valeurs sont
conservées telles quelles : rien n'est tranché ici »*.

**NON CONFIRMÉ** — aucun reçu réellement produit par un tiers n'a été
réconcilié.

### 4.10 Ingérer un paquet tiers — **TESTÉ**

```sh
python adapters/ingest.py <paquet> [--trust-store <magasin>] [--out <json>] [--strict]
```

**Trois verdicts** : `ACCEPTE` (0) · `INCOMPLET` (0, ou **2** sous
`--strict`) · `REJETE` (1). **`INCOMPLET` n'est pas un refus.**

Rien du paquet n'est exécuté, et aucune clé privée n'est nécessaire.

**NON CONFIRMÉ** — 16 cas de fixtures passent ; **aucun paquet réellement
produit par un tiers n'a jamais été ingéré.**

### 4.11 Lier des artefacts externes — **TESTÉ, DÉMONTRÉ**

```sh
python bind.py build  --archive <zip> --observation <id> \
                      --artifact rôle=chemin --created-at <UTC> --out manifeste.json
python bind.py verify manifeste.json --root <rép> [--archive <zip>] \
                      [--attestation <jws>] [--trust-store <magasin>] [--strict]
```

**Observé** : `4 PASS, 0 FAIL, 5 NOT TESTED`, et un niveau de garantie
**dérivé** : `reference_verifiable` — *« les artefacts offerts sont bien ceux
auxquels l'enregistrement se réfère »*. **Rien de plus.**

**Refus mesuré** : un identifiant d'observation inconnu rend le code **`1`** —
*« aucune observation 'obs-inexistante' dans l'archive (4 observations
présentes) »*.

🔴 Deux réserves que l'outil énonce lui-même : *une description textuelle
d'une exécution ne constitue pas une preuve que cette exécution a eu lieu*, et
*lier un artefact à un enregistrement ne dit pas quand, ni chez qui*.

### 4.12 Auditer le magasin de confiance — **TESTÉ**

```sh
python publish_store.py audit   <magasin.json>    # publiable tel quel ?
python publish_store.py payload <magasin.json>    # la charge du second canal
```

Il **ne publie rien**. `sign.py genkey` **refuse** d'écrire une clé privée
sous la racine du dépôt — mesuré, code **`1`**.

---

## 5. Quatre couches qui attrapent des choses différentes

Mesuré le 7 novembre sur le dossier de démonstration livré (`e31e12bb…`),
chaque altération reconstruite en préservant les `ZipInfo` d'origine pour que
la **seule** différence soit celle visée.

| Scénario | `verify.py` seul | Avec l'attestation |
|---|---|---|
| **A** archive intacte | `0` — 19 PASS, 0 FAIL | `0` — 10 PASS, 0 FAIL |
| **B** un octet **dans** un membre | **`1`** — l'empreinte diverge | `1` |
| **C** un octet ajouté **à la fin** du ZIP | **`0` — 17 PASS, 0 FAIL** | **`1`** |
| **D** une observation retirée, **tout recalculé** | **`0` — 17 PASS, 0 FAIL** | **`1`** |

🔴 **C et D sont le point.** `verify.py` vérifie l'**intégrité interne** de
l'archive ; l'attestation vérifie l'**identité du fichier**. Les confondre
serait promettre l'une en ne tenant que l'autre.

### 🔴 Ne jamais citer un taux de détection sans nommer sa batterie

Trois chiffres coexistent, et les trois sont exacts :

| Batterie | Résultat |
|---|---|
| `tests/test_falsification.py` | **10/10** altérations détectées, **+1 limite déclarée** |
| `tests/test_adversarial.py` | **13 détectées, 2 manques déclarés**, sur 15 |
| Q-1, cas adversarial G | provenance réécrite **puis réparée** → **non détectée**, même avec l'attestation |

**La détection dépend entièrement du soin du faussaire.** « 10 sur 10 »
décrit cette batterie de dix altérations nommées — ce n'est **pas** un taux
général de détection.

---

## 6. Conservé, exporté, publié, vérifiable

Quatre choses distinctes. Confondre deux d'entre elles produit une
affirmation fausse.

| | Texte de la réponse | Empreintes |
|---|---|---|
| **Registre Station** | **conservé** (`response_text`) | oui |
| **Export** (transmissible) | **absent** | oui |
| **Publié** | rien de Q-2 — privé et figé | — |
| **Disponible pour un vérificateur** | seulement ce que l'export porte | oui |

🔴 Les deux erreurs symétriques sont fausses : *« NeoMundi ne conserve pas les
réponses »* — faux, le registre les conserve — et *« l'export porte les
échanges »* — faux aussi. **Ce qui sort est un choix délibéré**, et c'est un
argument : le dossier atteste ce qui a été dit sans que l'export le divulgue.

---

## 7. Vérification indépendante

Ce qu'un tiers peut faire **sans nous**, sans compte et sans clé privée.

```sh
# 1. l'empreinte du fichier reçu, AVANT de l'ouvrir
sha256sum campagne.zip

# 2. la confronter à celle transmise PAR UN AUTRE CANAL
#    (un écart = ne pas ouvrir, et nous le dire)

# 3. récupérer le magasin de confiance
curl -O https://raw.githubusercontent.com/neomundi-io/neomundi-evidence-public/main/trust/trust-store.json

# 4. récupérer son empreinte sur un canal indépendant
curl -s https://mcp.neomundi.org/trust/trust-store-digest.json

# 5. comparer
sha256sum trust-store.json

# 6. vérifier l'archive, puis l'attestation
python verify.py campagne.zip
python verify_attestation.py campagne.jws --archive campagne.zip \
  --trust-store trust-store.json --store-digest <l'empreinte de l'étape 4> --strict
```

⚠️ Le segment `/trust/` est **obligatoire** — sans lui, `401`.

**Établi** : un faussaire devrait compromettre **deux** infrastructures
distinctes — un hébergeur Git et un VPS.

🔴 **Non établi** : les deux canaux sont sous la **même gouvernance**.
NeoMundi contrôle le dépôt **et** le VPS. **Ce n'est pas un tiers de
confiance.** Ce qu'on obtient est une résistance à la compromission d'un
**seul** canal.

---

## 8. Lire les résultats

| État | Sens | Ce qu'il **n'est pas** |
|---|---|---|
| `PASS` | le contrôle a été fait et il concorde | une preuve de vérité |
| `FAIL` | le contrôle a été fait et il ne concorde pas | nécessairement une fraude |
| `NOT TESTED` | **le contrôle n'a pas pu être fait** | un demi-`PASS`, ni un échec |

🔴 **Aucun verdict binaire n'est jamais rendu.** Il n'existe pas de
« ✓ archive authentique » : une archive peut être **intérieurement parfaite et
fausse**.

Trois ordres de conclusion, jamais à fondre :

| | Exemple | Portée |
|---|---|---|
| **Réussite technique** | 17 PASS, 0 FAIL | les octets concordent |
| **Résultat expérimental** | `coherence 0,675` sur une observation | un fait daté, non généralisable |
| **Conclusion scientifique** | *aucune* | aucune calibration, aucun seuil, aucune validation |

---

## 9. Où aller ensuite

| Besoin | Document |
|---|---|
| Reproduire les scénarios | [EVIDENCE_TECHNICAL_DEMO.fr.md](EVIDENCE_TECHNICAL_DEMO.fr.md) |
| Suivre un artefact dans la chaîne | [EVIDENCE_TRACEABILITY.fr.md](EVIDENCE_TRACEABILITY.fr.md) |
| Ce qui n'est **pas** établi | [EVIDENCE_LIMITATIONS.fr.md](EVIDENCE_LIMITATIONS.fr.md) |
| Tests exécutés, avec résultats | [EVIDENCE_VALIDATION_REPORT.fr.md](EVIDENCE_VALIDATION_REPORT.fr.md) |
| Décision de version | [EVIDENCE_RELEASE_READINESS.fr.md](EVIDENCE_RELEASE_READINESS.fr.md) |
| L'attestation en détail | [ATTESTATION.fr.md](ATTESTATION.fr.md) · [SIGNING_POLICY.fr.md](SIGNING_POLICY.fr.md) |
| L'horodatage en détail | [TIMESTAMPING.fr.md](TIMESTAMPING.fr.md) |
| La soumission par un tiers | [SUBMISSION.fr.md](SUBMISSION.fr.md) |
| Vérifier depuis une empreinte extérieure | [EXTERNAL_REFERENCE.fr.md](EXTERNAL_REFERENCE.fr.md) |

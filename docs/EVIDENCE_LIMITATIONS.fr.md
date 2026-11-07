# NeoMundi Evidence — limites

**7 novembre 2026.** Limites fonctionnelles, méthodologiques et
expérimentales. Rien n'est adouci, et rien n'est une liste de tâches
déguisée : la plupart sont des **bornes**, non des oublis.

---

## 1. Les trois qui ne bougeront pas

### 1.1 Une réécriture cohérente de la provenance déclarée est indétectable

Un faussaire qui réécrit une empreinte de configuration et un nom de modèle,
**puis répare** empreintes, sommes et manifeste, passe **tous les contrôles
locaux** — y compris l'attestation.

**Pourquoi ce n'est pas un défaut** : aucune recomputation ne distingue une
déclaration vraie d'une déclaration cohérente et fausse. L'établir exigerait
d'avoir observé la mesure.

**Consigné comme un plafond, jamais comme un `PASS`.** L'absence d'alarme
n'est pas une attestation.

### 1.2 Que l'évaluateur déclaré ait réellement tourné n'est jamais vérifiable

Durablement `NOT TESTED` depuis une archive. Il existe **trois** niveaux de
provenance et **pas de quatrième** ; un test échoue si `instrument_verifie`
apparaît.

### 1.3 Une signature établit un engagement et une custody, pas un fait

Le vérificateur l'imprime à chaque exécution : *une attestation parfaitement
signée sur une archive fabriquée est cryptographiquement valide.*

---

## 2. Ancrage temporel — implémenté, et il n'atteste aucune date

`timestamp.py` implémente OpenTimestamps, est couvert par 25 tests, et une
vraie preuve `.ots` de 786 octets est livrée avec la démonstration.
**Mesuré** : la liaison à l'empreinte du sujet se vérifie (3 PASS, 0 FAIL), un
mauvais sujet est refusé (code 1), et `--strict` rend **code 2**.

🔴 **La preuve livrée porte 4 attestations `PENDING` et 0 Bitcoin.** Un
pending dit qu'un calendrier s'est engagé à inclure l'empreinte dans une
transaction future — **il n'atteste aucune date**.

🔴 **Aucune qualification eIDAS.** OpenTimestamps n'est pas un prestataire de
services de confiance qualifié.

**L'outil vérifie la liaison, pas le temps**, et délègue :
`ots verify <preuve>`. Valider une attestation Bitcoin demande un en-tête de
bloc — une source de confiance que nous n'avons pas.

**Et aucune attestation produite par ce projet ne porte d'ancrage** : celle de
Q-2 a `external_anchor: null`.

---

## 3. Deux capacités non confirmées en conditions réelles

| Capacité | Statut | Ce qui manque |
|---|---|---|
| **Ingestion tierce** (`adapters/ingest.py`) | TESTÉ — 16 cas de fixtures | **aucun paquet réellement produit par un tiers n'a jamais été ingéré** |
| **Réconciliation** (`adapters/reconcile.py`) | TESTÉ — 27/27 — et DÉMONTRÉ sur fixtures | **aucun reçu réellement produit par un tiers n'a été réconcilié** |

Ni l'une ni l'autre ne peut être décrite comme validée en conditions
opérationnelles.

---

## 4. Détection : jamais un taux

| Batterie | Périmètre | Résultat |
|---|---|---|
| `tests/test_falsification.py` | dix altérations nommées | **10/10**, +1 limite déclarée |
| `tests/test_adversarial.py` | quinze cas | **13 détectés, 2 manques déclarés** |
| octet ajouté en fin de ZIP | — | `verify.py` **non**, attestation **oui** |
| amputation + recalcul complet | — | `verify.py` **non**, attestation **oui** |
| Q-1, cas G | provenance réécrite puis réparée | **non**, pas même l'attestation |

🔴 **Les cinq sont exacts, et ne décrivent pas la même chose.** « 10 sur 10 »
appartient à **cette batterie de dix**. Ce n'est **pas** un taux général de
détection, et cela ne doit jamais être publié comme tel.

⚠️ **Une divergence non résolue.** `test_falsification.py` rapporte une
amputation comparable comme **détectée** (« mieux qu'annoncé »), tandis que le
scénario D de la démonstration la montre **non détectée** par `verify.py`
seul. Les deux faussaires ne sont pas d'égal soin et la documentation ne dit
pas encore en quoi ils diffèrent.

---

## 5. Ce que `verify.py` ne voit pas, par conception

Il vérifie l'intégrité **interne** de l'archive. Il **ne** vérifie **pas**
l'**identité** du fichier — c'est ce que l'attestation couvre.

**Mesuré** : un octet ajouté à la fin du ZIP laisse **17 PASS, 0 FAIL**, et
l'attestation refuse le fichier.

**Trois lignes `NOT TESTED` sont structurelles**, et chacune dit pourquoi :

1. **complétude de l'export** — l'archive ne déclare ni le nombre
   d'enregistrements exportés ni les types exclus. *Une chaîne valide ne dit
   rien de ce qui n'a pas été exporté.* C'est au **producteur** de déclarer ce
   contrat ;
2. **chaînage JCS du registre d'origine** — hors de portée : le recalculer ici
   serait une seconde implémentation du registre. À confronter avec
   `station ledger verify` ;
3. **origine et horodatage de l'archive** — hors d'atteinte de tout contrôle
   local.

---

## 6. Le magasin de confiance : deux canaux, une gouvernance

**Établi** : un faussaire devrait compromettre **deux** infrastructures
distinctes — un hébergeur Git et un VPS.

🔴 **Non établi** : les deux sont sous la **même gouvernance**. NeoMundi
contrôle le dépôt **et** le VPS. **Ce n'est pas un tiers de confiance.** Ce
qu'on obtient est une résistance à la compromission d'un **seul** canal.

Sans `--store-digest`, la ligne du magasin reste `NOT TESTED` : *un magasin
non confronté n'est pas faux — il est non confronté.*

---

## 7. Identité et capacité juridique

La capacité déclarée est **`experimental`** : l'entité est **nommée**, elle a
**décidé** d'attester dans un cadre scientifique et non commercial, et
**aucune vérification de ses pouvoirs n'a été faite**.

🔴 `experimental` n'est **pas un `verified` plus faible — c'est l'opposé.**
Aucun code ne peut établir qu'une entité peut légalement s'engager. Ce n'est
jamais une certification juridique.

---

## 8. Limites expérimentales reprises de Q-2

Le verdict global de Q-2 est **`PARTIAL`**, et aucune démonstration réussie ne
le change.

1. le **statut de provenance du code** est établi au préflight et n'entre
   **pas** dans l'enveloppe du registre — un tiers lit `code_commit` sans
   savoir que la concordance a été contrôlée ;
2. les **artefacts sources ne sont pas dans l'export** — seules leurs
   empreintes. On peut **confronter** ce qu'on détient déjà ; on ne peut pas
   recalculer ce qu'on n'a pas ;
3. l'**idempotence du registre de l'API n'est pas qualifiée** ; Q-1 et Q-2 ont
   produit des mesures différentes, ce qui est un **indice** contre un cache,
   pas une qualification ;
4. les **horodatages sont déclarés** — trois instants voisins, trois sens
   différents ;
5. **`provider_attested` est l'affirmation du fournisseur**, non vérifiée ;
6. **une observation, un fournisseur** — Q-2 qualifie une **chaîne**, pas un
   modèle, et ne prétend à aucune reproductibilité statistique ;
7. le **contrat de réponse de l'API n'est pas clos** : 32 clés de premier
   niveau relevées là où l'audit en déclarait 25, et `contract_version` n'est
   pas contrôlé.

---

## 9. Lacunes documentaires, déclarées

| Lacune | Statut |
|---|---|
| `interpretation_contract 1.0` | cité par son nom ; son fichier n'a pas été localisé sur les branches inspectées |
| conditions des fournisseurs, droits sur l'empreinte d'une réponse | **non analysés** |
| ratios de contraste des états visuels | valeurs relevées, **ratios non mesurés** |

---

## 10. À quoi sert ce document

Un produit qui énumère ses angles morts est le seul auquel un auditeur peut se
fier. **Ces limites sont l'argument, non sa restriction.**

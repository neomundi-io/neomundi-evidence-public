# NeoMundi Evidence — rapport de validation

**7 novembre 2026.** Tests exécutés, résultats, codes de sortie et réserves.

| | |
|---|---|
| Branche | `docs/consolidation-v1-20261107` |
| Commit de départ | `28503cee4c93a91c3fc6df0e774fe31ab9523657` |
| Base | `main`, local et distant alignés |
| Nature du lot | **documentaire** — aucun code produit n'a été modifié |

---

## 1. Suites de tests — la séquence de CI, rejouée localement

Fixture : `python tests/make_fixture.py <rép> --profile v2` →
`NEOMUNDI_EVIDENCE_CI_FIXTURE.zip`, plus `corpus/`, `binding/`,
`fixture.json`.

| Suite | Code | Bilan |
|---|---|---|
| `test_timestamp` | **0** | 25/25 conformes |
| `test_reconciliation` | **0** | 27/27 |
| `test_bom` | **0** | 11/11 |
| `test_completude` | **0** | 15/15 |
| `test_capacite` | **0** | 10/10 |
| `test_cles` | **0** | 13/13 |
| `test_publication` | **0** | 15/15 |
| `test_ingestion` | **0** | 16/16 |
| `test_provenance` | **0** | 19/19 |
| `test_no_crlf` | **0** | 0 problème |
| `test_falsification` | **0** | **10/10 altérations détectées, 1 limite déclarée** |
| `test_adversarial` | **0** | **13 détectés, 2 manques déclarés, sur 15** |
| `test_attestation` | **0** | 24/24, 3 inapplicables |
| `test_i18n` | **0** | 26/26 |
| `test_binding` | **0** | 0 problème *(voir §2)* |

**Aucune régression.** Quinze suites, toutes vertes.

### Codes de sortie de `verify.py`, mesurés sans tube

| Invocation | Code | Bilan |
|---|---|---|
| `--corpus <corpus>` | **0** | 20 PASS, 0 FAIL, 2 NOT TESTED |
| *(sans corpus)* | **0** | 18 PASS, 0 FAIL, 3 NOT TESTED |
| `--corpus <corpus> --strict` | **0** | — |
| `--strict` *(sans corpus)* | **2** | une garantie **requise** manque |

---

## 2. Un échec, et son diagnostic

`test_binding.py` a d'abord rendu le **code 1** avec
`FileNotFoundError: …/binding/manifest.json`.

| Hypothèse | Verdict |
|---|---|
| erreur de test | **non** |
| **erreur de procédure** | **oui** |
| défaut logiciel | **non** |
| erreur documentaire | **non** |

**Cause** : `make_fixture.py` ne produit pas `manifest.json`. La CI le
construit d'abord par `bind.py build`, en employant `first_observation_id` de
`fixture.json` — et le workflow le dit en commentaire : *« le manifeste de
liaison est construit ICI : l'exemple commité porte sur l'archive de
démonstration, pas sur la fixture. »*

**Correction** : exécuter l'étape manquante. Après elle, `test_binding` rend
**code 0, 0 problème**.

**Consigné dans** `EVIDENCE_TECHNICAL_DEMO.fr.md` §10 pour que le suivant n'y
perde pas de temps.

> Aucun critère de réussite n'a été modifié pour obtenir un `PASS`.

---

## 3. Scénarios — treize codes de sortie attendus, tous conformes

Sur le dossier de démonstration livré, `e31e12bb7e32c7a3…`. Chaque copie
altérée a été reconstruite en préservant les `ZipInfo` d'origine ; l'original
n'a jamais été ouvert en écriture, et son empreinte était **inchangée** après
coup.

| # | Scénario | Attendu | Obtenu |
|---|---|---|---|
| A1 | `verify.py --corpus` | 0 | **0** — 19 PASS, 0 FAIL |
| A2 | `verify.py` | 0 | **0** — 17 PASS, 0 FAIL |
| A3 | attestation + magasin | 0 | **0** — 10 PASS, 0 FAIL |
| B1 | un octet **dans** un membre | 1 | **1** — l'empreinte diverge |
| C1 | un octet **à la fin** du ZIP, `verify.py` | 0 | **0** — 17 PASS, 0 FAIL |
| C2 | le même fichier, attestation | 1 | **1** — l'archive ne correspond pas |
| D1 | observation retirée + recalcul, `verify.py` | — | **0** — 17 PASS, 0 FAIL |
| D2 | le même fichier, attestation | 1 | **1** |
| E1 | clé `test` sans `--allow-test-keys` | 1 | **1** |
| E3 | liaison à une observation inconnue | 1 | **1** |
| E4 | clé privée sous la racine du dépôt | 1 | **1** — *fichier non créé* |
| F1 | `timestamp.py inspect` | 0 | **0** |
| F2 | `timestamp.py verify --subject` | 0 | **0** — la liaison tient |
| F3 | `timestamp.py verify --strict` | 2 | **2** — `PENDING` |
| F4 | `timestamp.py verify`, mauvais sujet | 1 | **1** |

**E2** — magasin non confronté sous `--strict` — a rendu **2**, comme la
conception l'exige.

**D1 est le résultat qui compte** : une amputation avec tous les contrôles
recalculés n'est **pas** détectée par `verify.py` seul. Reproduit ici
indépendamment du script de démonstration.

---

## 4. Corrections appliquées

Sept constats de la revue `REVUE_20261107/` relevaient de ce dépôt. Tous sont
des corrections documentaires ; **aucun code produit n'a été changé.**

| # | Constat | Où il est traité désormais |
|---|---|---|
| 1 | `--corpus` présenté comme un contrôle effectué sur Q-2 | `EVIDENCE_USER_GUIDE.fr.md` §4.4, avec la contre-épreuve |
| 2 | les codes de `--strict` et leur lecture | §3 du guide, avec quatre mesures |
| 3 | « 10/10 » employé comme taux général de détection | guide §5, démo §9, limites §4 |
| 4 | horodatage : implémenté, `PENDING`, aucune date | guide §4.8, limites §2 |
| 5 | ingestion tierce non confirmée | guide §4.10, limites §3 |
| 6 | les cinq verdicts de réconciliation | guide §4.9, traçabilité §3 |
| 7 | conservé / exporté / publié / vérifiable | guide §6, traçabilité §4 |

**Les constats relevant du site WordPress n'ont pas été exécutés** — ils sont
hors de cette mission et consignés comme dépendances futures dans le dossier
de revue.

---

## 5. Références figées — inchangées

| | Manifeste | Fichiers | État |
|---|---|---|---|
| Q-1 | `e6dec1062266f933…` | 20/20 | **inchangé** |
| Q-2 | `83794b85c8a54ead…` | 13/13 | **inchangé** |

Vérifié sur la copie de travail **et** sur la copie privée versionnée. Le
registre des 59 affirmations est intact, et la traçabilité des identifiants
est préservée.

---

## 6. État du dépôt

| | |
|---|---|
| Code produit modifié | **aucun** |
| Documents ajoutés | 12 sous `docs/` — six en anglais, six en français |
| Fichiers parasites laissés | **aucun** — la clé refusée n'a jamais été écrite |
| Répertoire non suivi préexistant | `reports/oda3-mukesh-2026-11-06/` — **non touché** |

---

## 7. Réserves

1. **Deux capacités restent NON CONFIRMÉES** en conditions réelles :
   l'ingestion tierce et la réconciliation.
2. **La preuve d'horodatage est `PENDING`** — aucune date n'est attestée, et
   aucune attestation de ce projet ne porte d'ancrage.
3. **Q-2 reste `PARTIAL`.** Rien dans ce travail ne le change, et rien n'a été
   tenté dans cette direction.
4. **Le cas G reste indétectable**, et il est publié comme un plafond.
5. **Une divergence n'est pas résolue** : `test_falsification.py` rapporte une
   amputation comme détectée là où le scénario D la montre non détectée. Les
   deux faussaires diffèrent par leur soin et la documentation ne dit pas
   encore en quoi.

### Une leçon de procédure, consignée

Le premier dépôt de ce lot a été livré **en anglais seulement**, en déclarant
la contrepartie française comme une « suite ». La CI l'a refusé : l'emploi
`discipline du dépôt` impose la paire EN/FR sur tout `docs/*.md`, avec deux
exceptions nommées qui ne s'appliquaient pas.

**Ce n'était donc pas une convention tolérante, mais une barrière.** Les six
contreparties ont été écrites plutôt que d'ajouter ces fichiers à la liste
d'exceptions — ce qui aurait affaibli la barrière pour une raison qui n'en
était pas une.

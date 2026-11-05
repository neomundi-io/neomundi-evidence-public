<sub>🇬🇧 <a href="ADVERSARIAL_AUDIT_EVIDENCE_2026-11-05.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Audit contradictoire — NeoMundi Evidence

**5 novembre 2026.** Audit mené avant tout développement, en cherchant
activement les cas où l'instrument conclurait à tort.

---

## Périmètre

| | |
|---|---|
| Dépôt | `neomundi-io/neomundi-evidence-public` |
| Commit audité | `a658af2bbacc9f3d34daee5829498be342b87a54` |
| Branche de travail | `feat/evidence-observation-binding-v1` |
| Environnement | Python 3.12.10, Windows 11, hors ligne |
| Archives éprouvées | `NEOMUNDI_EVIDENCE_DEMO_V0.1.zip` (GROUNDED-S1) et `NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip` (MED) |

**Ce qui est hors périmètre :** l'API NeoMundi, les moteurs de mesure, Control
Tower, la production. Aucun n'a été touché, aucun n'a été appelé.

---

## Protocole

1. inventaire des fichiers suivis et de leurs dépendances ;
2. exécution des tests existants, résultats enregistrés **avant** toute
   modification ;
3. construction d'une sonde contradictoire — `tests/test_adversarial.py` — qui
   fabrique des archives hostiles et observe ce que le vérificateur en fait ;
4. sondage séparé des entrées malformées.

Aucune capacité n'est déclarée sur la foi d'un README.

---

## Ligne de base, avant modification

| Commande | Résultat | Durée |
|---|---|---|
| `verify.py` sur GROUNDED-S1 (avec `--corpus`) | **19 PASS, 0 FAIL, 2 NOT TESTED** — 21 lignes de contrôle | 287 ms |
| `verify.py` sur MED | **10 PASS, 0 FAIL, 8 NOT TESTED** — 18 lignes | — |
| `tests/test_falsification.py` sur GROUNDED-S1 | **10/10 détectées**, 1 limite déclarée, 0 problème | — |
| `tools/med_demo_build.py`, reconstruction | archive identique : `a0d8a701…`, registres inchangés | — |

**Aucune dépendance déclarée, et aucune nécessaire** : les trois modules
Python n'importent que `argparse`, `collections`, `hashlib`, `io`, `json`,
`shutil`, `subprocess`, `sys`, `tempfile`, `zipfile`, `pathlib`.

---

## Matrice des capacités

| # | Capacité | Statut | Où | Observé |
|---|---|---|---|---|
| 1 | Ingestion d'artefacts | **PARTIEL** | `verify.py` | lit les membres d'un ZIP ; aucune ingestion d'artefact hors archive |
| 2 | Calcul d'empreintes SHA-256 | **DÉMONTRÉ** | `sha256`, `sha256_fichier` | empreintes recalculées sur les octets livrés |
| 3 | Vérification d'empreintes | **DÉMONTRÉ** | `controle_checksums` | un octet changé → FAIL |
| 4 | Vérification de signatures | **ABSENT** | — | aucun code de signature dans le dépôt |
| 5 | Identification des clés | **ABSENT** | — | — |
| 6 | Clés inconnues ou révoquées | **ABSENT** | — | — |
| 7 | Vérification de manifestes | **PARTIEL** | `controle_schema` | vérifie le **nom** du schéma et la liste des membres ; aucun contrôle de type des champs ; **plante** sur manifeste malformé |
| 8 | Détection d'altération | **DÉMONTRÉ** | suite de falsification | 10/10, plus 13/15 à la sonde contradictoire |
| 9 | Intégrité d'un paquet | **DÉMONTRÉ** | `controle_checksums` | couverture contrôlée **dans les deux sens** : membre non couvert et somme sans membre |
| 10 | Traçabilité des références | **PARTIEL** | `controle_cardinalites` | jointure `observation_id` vérifiée **à l'intérieur** de l'archive ; aucune référence externe |
| 11 | Provenance des résultats | **PARTIEL** | `controle_entrees` | `recording_sha256` et `bundle_sha256` recalculés **si** `--corpus` est fourni ; sinon simplement déclarés |
| 12 | Vérification hors ligne | **DÉMONTRÉ** | `verify.py` | bibliothèque standard seule, aucune primitive réseau, aucune écriture |
| 13 | Reconstruction documentaire | **ABSENT** | — | — |
| 14 | Rejeu effectif | **ABSENT** | — | — |
| 15 | Vérification d'un rejeu | **ABSENT** | — | — |
| 16 | Rapport exploitable par un tiers | **PARTIEL** | `Bilan.dire` | sortie texte lisible ; **aucune sortie lisible par machine** |
| 17 | Compatibilité mesures NeoMundi | **PARTIEL** | `controle_nulls` | lit les enregistrements de mesure d'une archive Station ; aucune liaison à une preuve externe |
| 18 | Compatibilité preuves externes | **ABSENT** | — | **c'est précisément l'objet de la phase 1** |

---

## Sonde contradictoire — 15 cas de forme

`python tests/test_adversarial.py <archive> [corpus]` → **13 détectés, 2 manqués.**

| Cas | Verdict |
|---|---|
| un membre surnuméraire, non déclaré | détecté |
| une somme annoncée pour un membre absent | détecté |
| un membre à chemin absolu (`/etc/passwd`) | détecté |
| une traversée de répertoire à l'antislash | détecté |
| **deux entrées ZIP du même nom** | détecté |
| **un membre déclaré lien symbolique** | détecté |
| un schéma d'export inconnu | détecté |
| un manifeste sans schéma | détecté |
| un `observation_id` en double | détecté |
| une mesure sans `observation_id` | détecté |
| un JSONL vide et des décomptes qui mentent | détecté |
| un manifeste de sommes vide | détecté |
| un manifeste illisible | détecté, **mais par un plantage** — voir A-01 |
| une archive imbriquée dans l'archive | **manqué** — limite assumée |
| un horodatage d'export dans le futur | **manqué** — limite assumée |

Les deux manques sont des **limites**, pas des défauts : l'outil n'extrait
jamais une archive imbriquée, et aucune horloge de confiance ne permet de
contredire une date déclarée.

---

## Anomalies

### A-01 — Le vérificateur plante sur une entrée malformée · **P0**

**7 entrées malformées sur 9 produisent une trace Python au lieu d'un verdict.**

| Entrée | Exception |
|---|---|
| manifeste illisible | `JSONDecodeError` |
| manifeste = tableau JSON | `AttributeError: 'list' object has no attribute 'get'` |
| `observations.jsonl` corrompu | `JSONDecodeError` |
| `measurements.jsonl` corrompu | `JSONDecodeError` |
| `observations.jsonl` non-objet | `AttributeError: 'str' object has no attribute 'get'` |
| `checksums.sha256` binaire | `UnicodeDecodeError` |
| `rapport.md` binaire | `UnicodeDecodeError` |

**Pourquoi c'est grave.** Le contrat de l'outil est de rendre `PASS`, `FAIL` ou
`NOT TESTED`. Un outil qui plante n'en rend aucun. Pire, il sort en code 1 —
indistinguable d'un `FAIL` pour qui automatiserait la vérification, alors que
le sens est « l'outil s'est cassé », pas « l'archive est mauvaise ».

Et c'est exactement le cas d'usage d'un vérificateur : on lui donne des
archives dont on ne sait pas si elles sont saines.

**Même classe qu'un défaut déjà corrigé** le 5 novembre sur `controle_csv`,
qui lisait `observations.csv` sans garde. La correction n'avait pas été
généralisée.

**Correction :** garde d'entrée sur chaque lecture structurée, rendant `FAIL`
avec la cause. P0 parce que la phase 1 ajoute des entrées dont la forme vient
d'un tiers.

### A-02 — Aucune sortie lisible par machine · **P1**

`verify.py` n'écrit que du texte. Un tiers qui veut automatiser la vérification
doit analyser des chaînes françaises. Le §3.6 de la mission exige les deux
formes.

### A-03 — Aucune vérification de signature, nulle part · **P1 (constat)**

Les capacités 4, 5 et 6 sont **absentes**. Le dépôt n'en revendique aucune, et
le README le dit. Ce n'est donc pas une divergence entre la documentation et le
code — c'est une limite réelle à garder visible, et une précondition à toute
« association cryptographiquement attestée ».

### A-04 — `controle_schema` ne valide pas la forme du manifeste · **P1**

Il vérifie le **nom** du schéma et la **liste** des membres. Il ne vérifie
aucun type de champ. Un manifeste dont `decomptes.observations` vaut
`"beaucoup"` traverse ce contrôle, et fait échouer un contrôle ultérieur par
accident plutôt que par conception.

### A-05 — Divergence d'indicateurs rapportée par un pilote · **non reproduite**

Un pilote rapporte `g_score = 0.3863` dans l'audit signé contre `0.594` au
tableau de bord, et une inversion des libellés entre stabilité et énergie.

**Rien n'a été reproduit ici, et rien ne pouvait l'être :** ces valeurs
n'appartiennent ni à ce dépôt ni aux archives dont il dispose. Le paquet du
pilote n'a pas été fourni. Aucun calcul de G-score n'existe dans Evidence, et
aucun n'a été touché.

Ce point relève du dépôt responsable du tableau de bord. Il est consigné ici
pour mémoire, **sans conclusion**.

---

## Audit des garanties — ce qui est démontré, et ce qui ne l'est pas

La distinction demandée par la mission, appliquée à l'outil réel :

| Niveau | État | Fondement |
|---|---|---|
| **Intégrité cryptographique** | **démontrée** | les empreintes des membres sont recalculées sur les octets livrés, et la couverture est contrôlée dans les deux sens |
| **Authenticité** | **absente** | aucune signature, aucune clé, aucune autorité |
| **Provenance** | **partielle** | pour un corpus rejoué et avec `--corpus`, les empreintes d'entrée se recalculent. Sinon, la provenance est **déclarée** |
| **Vérité de l'exécution** | **hors de portée** | aucun artefact d'exécution n'est ingéré, et rien ne relie l'archive à une exécution réelle au-delà de ce qu'elle déclare |
| **Reproductibilité** | **partielle, et asymétrique** | l'archive MED se reconstruit à l'octet ; une campagne réelle ne se rejoue pas, un registre non plus |

**Le trou central, confirmé par l'audit :** une archive intérieurement
parfaite reste indiscernable d'une archive refabriquée. La suite de
falsification le démontrait déjà ; la sonde contradictoire ne l'a pas démenti.
Seule une empreinte conservée hors de l'archive le détecte, et aucune
signature ne vient aujourd'hui l'attester.

C'est ce trou que la phase 1 commence à combler — **en qualifiant la liaison,
pas en la fabriquant.**

---

## Risques

| Risque | Portée | Atténuation |
|---|---|---|
| Un plantage lu comme un `FAIL` par un script tiers | élevé | A-01, corrigé en phase 1 |
| Une « association » documentaire prise pour une preuve d'exécution | élevé | niveaux de garantie explicites, et vocabulaire imposé |
| Une sortie texte analysée par expression régulière par un tiers | moyen | sortie JSON (A-02) |
| Un `FLAG` de mesure lu comme une preuve de fraude | élevé | la mesure n'est jamais recalculée ni réinterprétée par Evidence |
| Une régression des capacités existantes | moyen | ligne de base enregistrée ci-dessus, recomparée à chaque étape |

---

## Recommandations

**P0 — à faire avant toute nouvelle fonction**

1. **A-01** : rendre `verify.py` robuste aux entrées malformées. Toute lecture
   structurée rend `FAIL` avec sa cause, jamais une exception.

**P1 — dans cette mission**

2. **A-02** : sortie lisible par machine, en plus du texte.
3. **A-04** : valider la forme du manifeste, pas seulement son nom de schéma.
4. Associer une observation à des preuves externes, avec des **niveaux de
   garantie** explicites — l'objet de la phase 1.
5. Résolution et vérification d'artefacts locaux, dans un périmètre de
   sécurité défini — phase 2.

**P2 — après cette mission**

6. Signature et vérification de signature (capacités 4 à 6), qui conditionnent
   toute « association cryptographiquement attestée ».
7. Ancrage extérieur des empreintes.
8. Rejeu — étude de faisabilité d'abord, voir `REPLAY_FEASIBILITY.md`.
9. Instruire A-05 **dans le dépôt du tableau de bord**, pas ici.

---

## Ce que cet audit n'établit pas

Il porte sur un dépôt et deux archives. Il ne dit rien du paquet de preuves
annoncé par le pilote — **non fourni, donc non vérifié**. Il ne dit rien non
plus de l'API, des moteurs de mesure ni du tableau de bord, qui n'ont été ni
inspectés ni appelés.

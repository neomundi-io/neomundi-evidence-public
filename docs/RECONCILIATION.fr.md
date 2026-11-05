<sub>🇬🇧 <a href="RECONCILIATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Réconciliation — confronter un reçu externe à une mesure NeoMundi

Spécification d'origine : [`CP8_ADAPTER_SPEC.fr.md`](CP8_ADAPTER_SPEC.fr.md).
Ce document décrit l'**implémentation**.

---

## Ce que la réconciliation établit

**Rien, d'elle-même.** Elle *confronte*, et elle **conserve les deux côtés**.

| | |
|---|---|
| Un reçu externe | une **déclaration** |
| Notre archive | une **preuve primaire**, dans la mesure où nous en recalculons les empreintes |
| Une concordance démontrée | une **conclusion vérifiée** |

Les mélanger produirait exactement la confusion que ce produit refuse. Le
rapport porte les trois classes en clair.

---

## Les cinq statuts

| Statut | Signifie |
|---|---|
| **`MATCHED`** | les deux côtés sont présents, comparables, et égaux |
| **`MISMATCHED`** | les deux côtés sont présents, comparables, et **différents** |
| **`MISSING`** | un côté est absent |
| **`NOT VERIFIABLE`** | présent, mais sa **vérification** demande un matériau que nous n'avons pas |
| **`NOT COMPARABLE`** | les deux côtés existent, et une **frontière de comparabilité** est franchie |

### `NOT VERIFIABLE` et `NOT COMPARABLE` ne disent pas la même chose

C'est la distinction la plus facile à perdre, et la première version de cet
outil la perdait — elle routait les deux vers `NOT COMPARABLE`.

- **`NOT VERIFIABLE`** : le reçu annonce l'empreinte d'un journal, et le
  journal n'est pas joint. **Notre incapacité à contrôler.**
- **`NOT COMPARABLE`** : le reçu dit `concordant`, nous disons `measured`.
  Deux énoncés distincts, dont la comparaison serait vide de sens.

---

## La comparabilité passe **avant** la valeur

> Deux valeurs différentes ne sont une divergence de **calcul** que si elles
> mesurent la **même chose** : même définition, même version de mesure, même
> couverture.

Sinon elles ne se comparent pas, et conclure à une anomalie serait **une faute
de raisonnement, pas une découverte**. La frontière est donc évaluée d'abord,
et un champ non comparable n'est **jamais** déclaré `MISMATCHED`.

```
FRONTIERES DE COMPARABILITE -- evaluees AVANT les valeurs :
  - version de mesure du recu NON DECLAREE -- impossible d etablir la comparabilite
  - couverture de mesure du recu NON DECLAREE -- impossible d etablir la comparabilite
  - definition du score du recu NON DECLAREE -- impossible d etablir la comparabilite
```

### Mais une empreinte concorde quand même

La frontière ne mord que sur les **valeurs mesurées**. Chaque correspondance
déclare sa **nature** :

| Nature | Sensible au contexte de mesure ? |
|---|---|
| `digest` | **non** — une empreinte concorde ou non |
| `identifier` | **non** |
| `measured_value` | **oui** |
| `statement` | non, mais souvent non comparable pour d'autres raisons |

**C'était un défaut de ma première version** : une version de mesure non
déclarée rendait *tous* les champs `NOT COMPARABLE`, y compris une empreinte
qui concorde — détruisant la preuve la plus forte du dispositif. Un test de
régression le verrouille (cas 10).

---

## La liaison : trois voies, et aucune quatrième

| Voie | Exige | Force |
|---|---|---|
| **par empreinte** | une empreinte du reçu égale une empreinte que notre enregistrement déclare | **forte** |
| **par identifiant** | un identifiant présent des deux côtés et retrouvé dans notre corpus | moyenne — un identifiant est déclaratif |
| **refusée** | ni l'un ni l'autre | — |

**Une proximité de date, de modèle ou de valeur ne constitue pas une
liaison.** Un adaptateur qui relierait sur cette base fabriquerait la preuve
qu'il prétend vérifier.

Et **une observation demandée n'est pas une correspondance démontrée** :
`--observation` ne force rien, et le rapport dit que la liaison a été refusée.

---

## Aucune correspondance n'est devinée

L'importateur relève des **champs candidats** avec leur chemin d'origine, et
**n'interprète rien**. Décider que le `g_score` d'un tiers correspond au nôtre
est une affirmation sur deux définitions ; aucun extracteur ne peut la porter.

La correspondance doit donc être **déclarée** dans une table explicite, et
chaque entrée doit dire **pourquoi** (`basis` est obligatoire). Sans entrée, un
champ du reçu est simplement **laissé de côté**, et un champ visé est
`NOT COMPARABLE`.

Une table qui vise un champ **inexistant** chez nous est refusée **bruyamment**
— jamais rapportée comme un `MISSING` silencieux.

---

## Emploi

```sh
# 1. importer, sans interpreter
python adapters/receipt_import.py recu.html \
    --received-at 2026-11-05T12:00:00Z --out recu.json

# 2. reconcilier, avec une table EXPLICITE
python adapters/reconcile.py recu.json \
    --archive <archive_evidence.zip> \
    --map examples/reconciliation/map-comparable.json \
    --supplied "le journal d execution 1" \
    --out reconciliation.md --json reconciliation.json --strict
```

`--received-at` est **exigé** : l'outil ne lit pas l'horloge, et cette date
n'est pas une date attestée — c'est la date où **nous** avons reçu.

`--supplied` déclare les matériaux réellement fournis. Un champ qui en exige un
absent ressort `NOT VERIFIABLE`.

`--strict` rend **code 2** si un champ reste non établi, **sans changer aucun
statut**.

---

## `bind.py` est réutilisé, pas réécrit

La liaison par empreinte — la seule forte — est celle de `bind.py` :
`lire_sujet()` rend les empreintes que l'enregistrement déclare. **Aucun second
moteur n'est écrit**, et un test le vérifie sur le graphe d'appels (cas 23) :

```
appels a bind : charge, lignes_jsonl, lire_sujet
```

---

## Le cas CP8 — ce qui est prêt, et ce qui manque

### Ce que l'adaptateur sait déjà faire

Importer un reçu HTML, relever ses champs et ses empreintes, le lier par
empreinte ou par identifiant, produire un tableau champ par champ, et
**conserver les contradictions**.

La fixture synthétique porte délibérément **`0,3863`** et **`0,594`** : les
deux valeurs figurent telles quelles dans le rapport, sans conversion, et
aucune n'est désignée correcte.

### Ce qui n'est pas vérifiable aujourd'hui

| Élément | État |
|---|---|
| **`RECONCILIATION.md`** | **non fourni.** L'adaptateur est donc conçu sur la forme décrite, pas sur le dossier |
| Le reçu HTML CP8 lui-même | **non transmis dans ce chantier.** La fixture est entièrement **synthétique** |
| Les journaux dont les empreintes sont annoncées | non joints → `NOT VERIFIABLE` |
| Une signature | **aucune clé publique**, aucune signature reconnue → le reçu **n'est jamais** qualifié de signé |
| Les fixtures des deux exécutions | non jointes |
| La version de mesure du reçu | **non déclarée** → toute valeur mesurée est `NOT COMPARABLE` |

### Pourquoi `0,3863` contre `0,594` n'est **pas** conclu

Parce que les conditions de la comparaison ne sont pas réunies. Il manque :

1. le `request_id` ou l'empreinte qui lie le reçu à une mesure précise ;
2. la `measurement_version` de chaque côté — deux versions franchissent une
   frontière de comparabilité ;
3. la **couverture de mesure** de chaque côté — deux mesures de couvertures
   différentes ne se comparent pas signal par signal ;
4. la **définition** employée de chaque côté.

> Une note interne établit par ailleurs que `stability_score` **n'est pas un
> signal** mais un agrégat (`G / 0,60`). Un écart peut donc venir d'une
> **différence de définition** et non de calcul. L'adaptateur enregistre la
> définition déclarée de chaque côté avant de qualifier quoi que ce soit.
>
> **Aucun calcul de G-score n'est modifié ni recalculé.**

---

## Matrice de tests — 24/24

`python tests/test_reconciliation.py` — autonome, la fixture est fabriquée.

| # | Cas | Résultat |
|---|---|---|
| 1-3 | import : champs, empreintes, valeurs **verbatim** avec chemin | 13 champs, tous tracés |
| 2 | **aucune signature reconnue ni déclarée** | `signatures: []`, limite écrite |
| 4 | **les cinq statuts sont distingués** | 4 `MATCHED`, 2 `MISMATCHED`, 1 `MISSING`, 1 `NOT COMPARABLE`, 1 `NOT VERIFIABLE` |
| 5 | liaison par **empreinte** | une empreinte du reçu tombe sur une empreinte déclarée |
| 6-7 | contradictions conservées, **`0,3863` et `0,594` tels quels** | les deux côtés présents, aucune conversion |
| 8 | **virgule décimale** lue | écart calculé |
| 9 | sans contexte : les valeurs mesurées ne se comparent pas | `NOT COMPARABLE` |
| 10 | **mais une empreinte concorde quand même** | `MATCHED` — régression verrouillée |
| 11 | **aucune correspondance devinée** | 5 champs du reçu laissés de côté |
| 12 | table visant un champ inexistant | **refus bruyant**, pas un `MISSING` |
| 13 | étiquette en double | refus |
| 14-15 | schéma de reçu / de table inconnu | refusés, pas interprétés |
| 16 | **6 entrées hostiles** (vide, tronquée, 200 lignes imbriquées, script injecté, octets non-UTF-8, JSON non-objet) | **6/6**, aucune trace d'appels |
| 17 | script injecté | le contenu reste une **donnée**, jamais une instruction |
| 18 | rien de commun | **liaison refusée** |
| 19 | observation **demandée** | refusée — une demande n'est pas une correspondance |
| 20 | `--strict` | code 2, **9 lignes identiques** |
| 21-22 | rapport Markdown | trois classes de preuve ; **aucun chemin de machine** |
| 23 | **`bind.py` réutilisé** | `lire_sujet`, `lignes_jsonl`, `charge` |
| 24 | le reçu n'est **jamais** qualifié de signé ni de vérifié | aucune qualification abusive |

---

## Ce que la réconciliation ne fera jamais

- **Trancher** une divergence que les données ne tranchent pas.
- **Moyenner**, arbitrer, ou désigner une valeur correcte.
- **Qualifier de « signé »** ce dont la signature n'a pas été vérifiée.
- **Élever un niveau de garantie** sur la foi d'une déclaration externe.
- **Deviner** une correspondance.
- **Reconstituer** artificiellement les résultats d'un tiers.
- **Compléter** un champ absent par une valeur plausible.

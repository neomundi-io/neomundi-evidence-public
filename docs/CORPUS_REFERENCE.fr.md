<sub>🇬🇧 <a href="CORPUS_REFERENCE.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Corpus de référence — empreintes et vérification

Ce document appartient au dépôt `neomundi-evidence`. Il déclare les corpus sur
lesquels NeoMundi Evidence V0.1 s'appuie, leurs empreintes, et comment un tiers
les vérifie.

**Il ne contient aucune donnée de corpus.** Les archives vivent hors de Git, sur
un support privé, et ne sont remises que sur décision explicite — voir
« Obtenir les archives ».

> **Les opérateurs et les modèles sont nommés.** C'est délibéré : MED est une
> expérimentation indépendante, et une expérimentation dont on cache les sujets
> ne peut pas être examinée. Ce qui n'est **pas** publié, c'est le contenu du
> jeu de données — voir la [démonstration MED](MED_DEMO.fr.md).
>
> Aucun résultat n'est présenté comme un classement. Une mesure décrit des
> propriétés d'un texte produit ; elle n'établit pas qu'une réponse est
> médicalement juste.

Gel de référence : `20261105T1200_GEL_CORPUS_GATE0`, 5 novembre 2026.

---

## Les deux corpus

| | MED | GROUNDED-S1 |
|---|---|---|
| Régime d'exécution | `live` — sept opérateurs réels | `synthetic` — aucun opérateur |
| Registres | 7 | 1 |
| Enregistrements | 844 | 151 |
| Observations | 209 | 30 |
| Mesures | 208, toutes `measured` | 30 : 15 `measured`, 8 `degraded`, 7 `not_measured` |
| Évaluations de référence | 208 | 30 |
| `measurement_version` | 3.3.1 | 3.3.1 |
| Corrélation production | `neomundi_measurement_id` réels | sentinelles `33100000-…` |
| Publication | **archive dérivée publiée** ; contenu du jeu de données non redistribué | publiée |
| Usage V0.1 | **Démonstration B** — traçabilité sectorielle | **Démonstration A** — comportement contrôlé du vérificateur |

---

## Empreintes

### Archives

```
98043a138a58ef764902718a2f07d2a3058108ce448cd19a042c7e9fda294559  GEL_MED_20261105.zip
754da1d21c67590b12a26ee524a58dec3c288b0c3a698c7186b60c99451aee49  GEL_GROUNDED-S1_20261105.zip
```

### Empreintes de tête des registres

Relevées le 4 novembre 2026, revérifiées le 5 novembre sur les copies du gel —
identiques au caractère près.

| Fournisseur | Enregistrements | Empreinte de tête | Modèle demandé | Attestation du modèle servi |
|---|---|---|---|---|
| `anthropic` | 121 | `e2170cebf2fd16a94509f556152624e8ff0339644aae1f430c69133ac65588a2` | `claude-sonnet-5-5` | provider_attested |
| `cohere` | 121 | `4e26bf8e1cef4af398eb3b6ba5da9a49e88fee05234fd5a3986809c62d91514d` | `command-a-plus-05-2026` | requested_only |
| `deepseek` | 121 | `8c10d4fdd1ae3162ce08410d4d328d385d81dcc6c8067deead2c558347a1467d` | `deepseek-flash` | requested_only |
| `google` | 121 | `221e7b212640d820d8b220d94016a7a6a6240ca15284b8cb08feed3b97f66234` | `gemini-2.5-flash` | provider_attested |
| `infomaniak` | 121 | `1ca7027a40c538bbb5285303901c8f219319e57059ac9f6d4a75db507a3047bf` | `swiss-ai/Apertus-v1.5-70B` | provider_attested |
| `moonshot` | 121 | `d8f5138594eb5a19aa629eb70dc3f0045b2b30675add049cc8b389c988553ff8` | `kimi-k3` | provider_attested (29) / requested_only (1) |
| `openai` | 118 | `d6df67cccb2a8b54cce2d7bf2a3aba752d3ab1f44ba20f71b323178754a44d58` | `gpt-6-astra` | provider_attested |
| `GROUNDED-S1` | 151 | `fc1f2787e6e0e24fd70c9b6d252efe99dc9e2fe297233f289254c47a4c7d43b2` | `grounded-s1-2026-10-22` | synthétique — atteste un enregistrement rejoué |

Une attestation `requested_only` signifie que le fournisseur **n'a pas** déclaré
quel modèle a réellement servi la requête. Pour ces deux campagnes, le modèle
demandé est la seule chose établie.

### Identités de campagne

Chaque `campaign_sha256` est concordant sur **trois** sources : déclaré par le
registre, porté par la définition gelée, et **recalculé par nous** depuis cette
définition, avec la bibliothèque standard seule. 8 sur 8 — revérifié le
6 novembre 2026, 10 sur 10 en comptant deux campagnes non publiées ici.

> **« Recalculé par nous » n'est pas « reproductible indépendamment », et une
> édition antérieure de cette page confondait les deux.** Elle écrivait
> *recalculé indépendamment*, ce qui se lit comme une garantie qu'un relecteur
> peut exercer. Deux choses l'en empêchent, et les deux sont de notre fait : la
> recette n'était **écrite nulle part**, et les définitions de campagne sont
> **hors de portée de la branche principale de l'instrument** — voir
> [Obtenir les archives](#obtenir-les-archives).
>
> Ce n'est pas un manque théorique. Une évaluation externe du 6 novembre
> détenait les données gelées, a essayé trois recettes plausibles sur
> `grounded-med-synthetique-v1`, et a conclu **« non établi »** — elle avait
> retiré un champ exclu au lieu de deux. Une revendication vraie que personne
> d'autre ne peut exercer est, vue de l'extérieur, indiscernable d'une
> revendication fausse.
>
> La recette est une formule sur un objet dont la forme est déjà décrite ici ;
> elle ne porte aucune clé, aucun secret, aucun contenu de jeu de données.
> **Sa publication est une décision en attente** (recommandation ODA3 R-5).
> Jusqu'à ce qu'elle soit prise, tenir chaque `campaign_sha256` ci-dessous pour
> une empreinte de **classe C** au sens du tableau de
> [Vérifier](#vérifier) : vérifiable avec l'instrument, pas sans lui.

| Campagne | `campaign_sha256` |
|---|---|
| `grounded-med-complet-defauts-anthropic-v1` | `b11ba303045aa464…` |
| `grounded-med-complet-defauts-cohere-v1` | `0665a3d42cd22609…` |
| `grounded-med-complet-defauts-deepseek-v1` | `2914c55c2f9af943…` |
| `grounded-med-complet-defauts-google-v1` | `012075b1248bb485…` |
| `grounded-med-complet-defauts-infomaniak-v1` | `73d4dbda0a9c20aa…` |
| `grounded-med-complet-defauts-moonshot-v1` | `e6e8decf5f543ff8…` |
| `grounded-med-complet-defauts-openai-v1` | `81e8b981b8a7de14…` |
| `grounded-med-synthetique-v1` | `7882f080d33bec30…` |

### Lien du registre vers ses entrées — GROUNDED-S1 seulement

```
bundle_sha256  d84722b4f4db3af939c456f3a535e484cabffbaabcbc69f684dc997fce05f7e1
```

Les 30 enregistrements `replay_provenance` attestent l'empreinte de chacune des
30 entrées. **30 sur 30 correspondent** aux fichiers du gel, et le
`bundle_sha256` se recalcule exactement — avec la bibliothèque standard seule.

C'est ce lien qui fait qu'un corpus synthétique est vérifiable plutôt que
simplement recopié : on ne peut pas y substituer une entrée sans que le registre
le contredise.

---

## Vérifier

### Qui peut vérifier quoi — quatre classes d'accès

Chaque empreinte de cette page appartient à exactement une classe. C'est la
classe, et non l'empreinte, qui dit à un relecteur s'il peut exercer la
revendication lui-même.

| | Classe | Qui peut vérifier | Empreintes concernées |
|---|---|---|---|
| **A** | **Le dépôt public seul** | n'importe qui, bibliothèque standard | les empreintes du dossier de démonstration V1 ; la fixture de CI, déterministe à l'octet |
| **B** | **L'archive de gel, bibliothèque standard** | un relecteur à qui l'accès est accordé | les deux empreintes d'archive de gel ; les 30 `recording_sha256` ; `bundle_sha256` |
| **C** | **L'instrument** | nous, aujourd'hui | le chaînage JCS ; `record_sha256` ; **et `campaign_sha256`, jusqu'à publication de sa recette** |
| **D** | **Personne, par nature** | — | les empreintes de tête des registres — `recorded_at` est lu à l'horloge, donc un rejeu ne les reproduit jamais ; MED, dont les appels étaient réels |

**C'est la classe C qu'il faut surveiller.** Une empreinte de classe C n'est
pas plus faible cryptographiquement — elle est plus faible **sur le plan
probatoire**, parce que sa vérification repose sur la partie qui l'a produite.
Faire passer une empreinte de C à B est toujours un acte de documentation,
jamais de cryptographie.

**La classe D n'est pas un défaut.** Une empreinte de tête qui ne dépendrait de
rien ne serait pas une chaîne. Confondre D avec un échec est l'erreur
symétrique de confondre C avec B.

### Sans rien installer

```sh
sha256sum -c GEL_GROUNDED-S1_20261105.zip.sha256    # avant d'ouvrir l'archive
unzip GEL_GROUNDED-S1_20261105.zip -d gel/
python gel/verifier_gel.py gel/
```

`verifier_gel.py` n'a aucune dépendance et n'émet aucun appel réseau. Il rend
PASS, FAIL ou NOT TESTED par contrôle. Au 5 novembre 2026, sur le gel complet :
**12 PASS, 0 FAIL, 3 NOT TESTED.**

Les trois NOT TESTED sont assumés :

| Contrôle | Pourquoi non testé ici |
|---|---|
| chaînage JCS de MED (7 registres) | le recalculer serait une seconde implémentation du registre |
| chaînage JCS de GROUNDED-S1 | idem |
| empreintes des entrées rejouées — MED | corpus `live` : aucun `replay_provenance` à vérifier |

### Le chaînage, avec la Station

```sh
station ledger verify --path <registre>
```

Au 5 novembre 2026, sur les copies du gel : **8 chaînes sur 8 valides, 0
anomalie.**

---

## Ce que ces empreintes ne prouvent pas

- **Ni l'origine, ni l'heure.** Le chaînage n'a aucun ancrage extérieur, et
  `recorded_at` est fourni par l'appelant. Le registre atteste ce qu'on lui a
  déclaré.
- **Ni l'intégrité contre une réécriture complète.** Une chaîne entière
  réécrite se vérifie parfaitement. Seule une empreinte conservée ailleurs —
  comme celles de ce document — permet de le détecter.
- **Ni la justesse des signaux.** L'existence d'un score ne démontre pas sa
  validité.

---

## Reproductibilité du calcul — à ne pas confondre avec le gel

Le gel dit *ces octets n'ont pas changé*. La reproductibilité dit *on peut les
refabriquer*. Les deux sont établies séparément, et elles ne donnent pas le même
résultat.

| Corpus | Verdict |
|---|---|
| MED | **NON REPRODUCTIBLE.** Appels réels à sept opérateurs externes les 29–30 octobre 2026. Un fournisseur ne rejoue pas une réponse. |
| GROUNDED-S1 | **PARTIELLE.** 55 des 62 entrées se reproduisent à l'octet. |

### Les 7 divergences de GROUNDED-S1

Les fichiers divergents sont les rangs 3, 7, 11, 15, 19, 23, 27 — soit
`rang % 4 == 3`, l'archétype `non-mesuree`. Cet archétype a été corrigé le
**24 octobre 2026** par une modification datée du dépôt privé de l'instrument, postérieure à la production du
corpus du 22 octobre.

La divergence est donc **expliquée et attribuée à un commit nommé**. Elle n'est
pas un signe d'altération. Les deux versions de l'archétype sont dans le gel.

Deux précisions qui comptent pour une déclaration de reproductibilité :

1. **Le script générateur n'existait pas à la révision attestée** — il a été
   commité quatre minutes après la production du corpus. Le gel est donc le seul
   enregistrement autoritatif de ces 62 entrées.
2. **Reproduire un registre à l'octet est impossible**, même pour un corpus
   synthétique : `recorded_at` est lu à l'horloge, et les empreintes de chaînage
   en dépendent. « Reproductible » signifie *mêmes entrées, même contenu
   d'observations et de mesures, chaîne valide*. Jamais *même empreinte de tête*.

---

## Obtenir les archives

Aucun accès en libre-service.

- **GROUNDED-S1** — remise possible à un relecteur externe après décision
  explicite du propriétaire du corpus. L'empreinte est transmise par un canal
  **distinct** de l'archive : qui peut remplacer l'archive peut remplacer la
  somme qui l'accompagne.
- **MED** — l'**archive de démonstration dérivée est publiée** : elle porte les
  observations et les mesures, et nomme les opérateurs et les modèles.
  L'**archive de campagne complète reste privée**, parce qu'elle porte les
  évaluations de référence, dont la publication reconstituerait des étiquettes
  du jeu de données. Le contenu du jeu de données n'est jamais redistribué —
  voir la [démonstration MED](MED_DEMO.fr.md).

---

## Contexte de calcul

| | MED | GROUNDED-S1 |
|---|---|---|
| Commit attesté | `e4ffda6b5bfcc105efbf0c764ca7d61e5e263220` | `a52715d39383c71d2fbded47cf65ebeadc381317` |
| Produit le | 2026-10-29, 11:38–12:02 UTC | 2026-10-22T02:09:54Z |
| Définitions de campagne | épinglées par un tag daté du dépôt privé | idem |
| Jeu de données | le jeu de données source v1, 202 items | idem, via le panel gelé |
| Schémas | 15 schémas scellés, dans le gel | idem |

> Les définitions de campagne MED **ne sont pas sur la branche principale de l'instrument**. Elles sont
> épinglées par un tag daté du dépôt privé. Un clone de la branche principale
> ne les contient pas : un auditeur qui partirait de `main` ne pourrait pas recalculer
> les `campaign_sha256`. C'est pourquoi elles sont dans le gel.

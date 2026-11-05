<sub>🇬🇧 <a href="MED_DEMO.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Démonstration B — MED, une expérimentation médicale indépendante

**Une mesure n'est pas une validation médicale de la réponse.** Rien dans cette
démonstration n'établit qu'une réponse est cliniquement juste. Elle établit ce
qui a été demandé, ce qui a répondu, ce qui a été répondu, et ce qui a été
mesuré.

---

## La chaîne que cette démonstration montre

```
item du jeu de données  →  réponse d'IA  →  mesure  →  trace enregistrée  →  dossier de preuve  →  vérification
```

Chaque flèche est un enregistrement dans un registre en ajout seul, chaîné par
empreintes. Le dossier de preuve recopie ces enregistrements **en octets
d'origine**.

| | |
|---|---|
| Archive | `NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip` |
| Schéma | `neomundi.evidence.med-demo/1` — artefact **dérivé** |
| Produite par | [`tools/med_demo_build.py`](../tools/med_demo_build.py) |
| Source | les 7 registres MED gelés, en lecture seule |
| Observations | 209 |
| Mesures | 208, toutes `measured`, version `3.3.1` |
| Vérification | **10 PASS, 0 FAIL, 8 NOT TESTED** |

---

## Le jeu de données, et pourquoi son contenu n'est pas publié

| | |
|---|---|
| Nom | MedMCQA |
| Source | [`openlifescienceai/medmcqa`](https://huggingface.co/datasets/openlifescienceai/medmcqa) |
| Révision | `91c6572c454088bf71b679ad90aa8dffcd0d5868` |
| Étiquette de licence | `apache-2.0` |
| Section de licence de la fiche | `[Needs More Information]` |
| Collecte déclarée | *Historical Exam questions from official websites — AIIMS & NEET PG (1991-present)*, et *open websites and books* |
| Citation demandée | Pal, Umapathi & Sankarasubbu, 2022 — *MedMCQA: A Large-scale Multi-Subject Multi-Choice Dataset for Medical domain Question Answering* |
| Sélection | 300 lignes lues à la source ; **202 conservées** par un filtre « réponse unique » ; 98 écartées comme à choix multiples |

**Le contenu du jeu de données n'est pas redistribué ici.** L'étiquette YAML
annonce `apache-2.0` tandis que la section « Licensing Information » de la fiche
est restée au gabarit vide, et le matériau provient d'examens de tiers. Cette
contradiction n'est pas levée, et nous ne la levons pas en retenant d'office la
lecture permissive.

Donc : **ni énoncé, ni choix, ni étiquette de référence.** Ce qui est publié,
c'est l'**`item_id`** — l'identifiant propre au jeu de données — pour qu'un
auditeur résolve une question **à la source**, chez l'éditeur, et non chez nous.

Le registre n'a de toute façon jamais détenu l'énoncé : il conserve
`prompt_sha256`, une empreinte.

---

## Fournisseurs et modèles réellement utilisés

Nommés, délibérément. Une expérimentation dont on cache les sujets ne peut pas
être examinée.

| Fournisseur | Modèle demandé | Modèle servi | Attestation | Obs. | Mesurées |
|---|---|---|---|---|---|
| `anthropic` | `claude-sonnet-5-5` | `claude-sonnet-5-5` | `provider_attested` | 30 | 30 |
| `cohere` | `command-a-plus-05-2026` | **`null`** | `requested_only` | 30 | 30 |
| `deepseek` | `deepseek-flash` | **`null`** | `requested_only` | 30 | 30 |
| `google` | `gemini-2.5-flash` | `gemini-2.5-flash` | `provider_attested` | 30 | 30 |
| `infomaniak` | `swiss-ai/Apertus-v1.5-70B` | `swiss-ai/Apertus-v1.5-70B` | `provider_attested` | 30 | 30 |
| `moonshot` | `kimi-k3` | `kimi-k3` / **`null`** | 29 attestées, 1 `requested_only` | 30 | **29** |
| `openai` | `gpt-6-astra` | `gpt-6-astra` | `provider_attested` | **29** | 29 |

**Trois faits de ce tableau sont plus intéressants que les modèles.**

**Deux fournisseurs n'ont pas attesté quel modèle a servi.** `cohere` et
`deepseek` rendent `model_served: null`. Pour ces 60 observations, le modèle
demandé est la seule chose établie — on ne sait pas ce qui a réellement répondu.
C'est enregistré, pas lissé.

**Une observation n'a aucune mesure.** Chez `moonshot`, un appel a dépassé
120 secondes avant toute réponse. Son observation existe, avec
`execution_status: error`, `response_text: null`, et `latency_ms: 0` — qui est
une durée **non établie**, pas une durée de zéro milliseconde.

**Une tentative n'a produit aucune observation.** `openai` compte 29
observations pour 30 tentatives.

**Aucun classement n'est publié, et il ne faut en dériver aucun.** Des
fournisseurs différents ont servi des modèles différents dans des conditions
différentes ; les campagnes sont des séries distinctes et ne s'agrègent pas.

---

## Signaux mesurés

Les cinq signaux sont valués sur les 208 mesures, en `measurement_version`
`3.3.1`, et les 208 portent un identifiant de mesure de production.

| Signal | Mesuré | `null` |
|---|---|---|
| `coherence_score` | 208 | 0 |
| `factual_hallucination_score` | 208 | 0 |
| `semantic_instability_score` | 208 | 0 |
| `semantic_risk` | 208 | 0 |
| `stability_score` | 208 | 0 |

**Ce que ces signaux ne sont pas.** Ils décrivent des propriétés du texte
produit. Aucun n'est un jugement clinique, et aucun n'a été validé contre une
vérité médicale. Un `coherence_score` élevé sur une réponse fausse reste un
`coherence_score` élevé sur une réponse fausse.

---

## Ce qui a été écarté de l'archive, et pourquoi

**`reference_evaluations.jsonl` est écarté.** Il porte le couple `status` +
`extracted_answer` : chaque fois qu'une réponse est `correct`, la lettre
extraite **est** l'étiquette de référence du jeu de données. Publier cela sur
208 mesures reconstituerait une partie des étiquettes de MedMCQA, dont les
conditions de redistribution ne sont pas levées.

**Conséquence, dite franchement :** cette archive **ne permet pas** de dire si
une réponse était juste au sens du jeu de données. Le jugement de justesse
existe — il est dans le registre, et dans l'archive de campagne complète, qui
reste privée.

C'est pourquoi il s'agit d'un artefact **dérivé** sous son propre schéma, et non
d'un export de campagne dont on aurait discrètement retiré un membre. Retirer un
membre d'une archive attestée obligerait à réécrire son manifeste et ses sommes
à la main, ce qui fait d'une archive attestée un fichier retouché.

---

## Le vérifier soi-même

```sh
python verify.py NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip
```

Résultat au 5 novembre 2026 : **10 PASS, 0 FAIL, 8 NOT TESTED.**

Les huit `NOT TESTED` sont nommés avec leur raison. Cinq portent sur les membres
que cette archive ne contient pas — évaluations de référence, provenance de
rejeu, CSV, rubrique d'absences déclarées, rubrique de régime d'exécution. Les
trois autres sont le chaînage des sept registres, les empreintes d'entrées
rejouées, et l'origine de l'archive.

> **La suite de falsification ne s'applique pas à cette archive.** Ses dix
> altérations supposent un membre `rapport.md`, un `observations.csv`, au moins
> un signal `null` et une garde de régime — qu'une archive MED dérivée n'a pas.
> La lancer sur la [démonstration A](DEMO.fr.md) ; ici elle refuse de tourner et
> dit pourquoi.

### Ce que cette archive ne permet pas de vérifier

- **le chaînage des sept registres.** L'archive déclare leurs empreintes de
  tête ; recalculer la chaîne est le travail de l'instrument, pas de ce
  vérificateur.
- **l'origine ou l'heure de l'archive.** Aucune signature, aucun ancrage
  extérieur.
- **si une réponse était médicalement juste.** Hors périmètre, par conception.

---

## Ce qui est démontré, ce qui ne l'est pas, et ce qui ne peut pas l'être

| | |
|---|---|
| **Démontré** | un item de question réel, un modèle réel, une réponse réellement enregistrée, cinq signaux réellement mesurés, une trace chaînée, un dossier de preuve dérivé, et une vérification indépendante au niveau des fichiers |
| **Démontré** | que deux fournisseurs n'ont pas attesté leur modèle servi, et que cela se voit au lieu d'être caché |
| **Non mesuré** | la justesse médicale d'une réponse, quelle qu'elle soit |
| **Non publié** | l'énoncé des questions, les choix, les étiquettes de référence, et les verdicts de justesse |
| **Ne peut pas être établi** | l'origine et l'heure de l'archive ; la résistance de la chaîne à une réécriture complète |
| **Non reproductible** | l'expérimentation elle-même. Des appels réels à sept opérateurs externes les 29 et 30 octobre 2026. Un opérateur ne rejoue pas une réponse : relancer produirait d'autres réponses, d'autres latences, d'autres signaux. **Le gel est le seul enregistrement de ce qui a été observé.** |

---

## D'où viennent les chiffres

Chaque chiffre de cette page est lu dans les registres gelés, ceux que le gel de
référence consigne — voir la [référence des corpus](CORPUS_REFERENCE.fr.md) pour
leurs empreintes de tête et la concordance à trois sources de leurs identités de
campagne.

L'outil de construction les lit **en lecture seule** et vérifie, après écriture,
que les empreintes des registres sources n'ont pas bougé.

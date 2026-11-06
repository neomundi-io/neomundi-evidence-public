<sub>🇬🇧 <a href="ODA3_CONSOLIDATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Consolidation ODA3 — ce qui a changé, et ce qui n'a pas changé

**6 novembre 2026.** Réponse à l'évaluation externe conduite pour
**Mukesh Kumar Singh (ODA3 Institute)**, dont la question était la bonne :

> Quelle différence existe-t-il entre conserver un enregistrement vérifiable
> d'une exécution IA et établir que cet enregistrement est suffisamment
> probant pour soutenir une affirmation d'assurance précise ?

L'évaluation a produit neuf recommandations. **Huit sont traitées ici. Une
est délibérément laissée de côté**, et sa raison compte plus que le travail.

---

## Le constat qui a réorganisé le travail

L'évaluation a retiré une observation de ses cinq membres dans une archive
réelle, puis refait les décomptes et les sommes de contrôle.

`verify.py` a rendu **19 PASS, 0 FAIL**.

Une archive intérieurement parfaite n'avait exporté qu'une partie de son
registre, et rien ne le disait. Mesuré sur l'export réel : **151
enregistrements de 6 types au registre, 120 de 4 types dans l'archive** —
avec un manifeste annonçant 151. Les 31 retenus (30 `runner_attempt`, un
`run`) n'étaient nommés nulle part.

C'est toute la différence entre intégrité et suffisance probatoire, et c'est
désormais une ligne de contrôle.

---

## Ce qui a été fait, recommandation par recommandation

| | Ce qui était demandé | Ce qui a été fait |
|---|---|---|
| **R-1** | nommer les types d'enregistrement exclus de l'export | le contrat de complétude : `types_exclus` et leurs décomptes, au manifeste, contrôlés |
| **R-2** | un contrôle confrontant le total du registre à la somme des décomptes | le même contrôle, trois états : `PASS` / `FAIL` / `NOT TESTED` |
| **R-3** | rapprocher le dossier public d'une archive réelle, ou écrire ses divergences | un **profil versionné** : `v2` corrige cinq écarts sur six, le sixième est déclaré |
| **R-4** | signaler un `stamped_at_declared` postérieur au bloc qui l'ancre | les deux valeurs sont désormais dites côte à côte, avec la relation qui doit tenir |
| **R-5** | documenter la recette de `campaign_sha256` | la revendication est corrigée, et un **tableau de quatre classes d'accès** ajouté. La publication de la recette est une décision en attente |
| **R-6** | enregistrer la provenance de l'évaluateur dans `measurements.jsonl` | **non fait** — structurel, et objet d'une analyse distincte |
| **R-7** | renommer `config_snapshot_sha256` ou le documenter | documenté, à la table de correspondance et dans [`BINDING.fr.md`](BINDING.fr.md). **Non renommé** |
| **R-8** | corriger le rendu `['True']` | corrigé, dans les deux langues |

---

## R-5 — la plus instructive des huit

La référence de corpus publiée écrivait que chaque `campaign_sha256` était
*« recalculé indépendamment. 8 sur 8. »*

L'évaluation détenait les données gelées, a essayé trois recettes plausibles
sur `grounded-med-synthetique-v1`, et a conclu **« non établi »**.

Les deux énoncés étaient vrais, et c'est tout le sujet. **Vérifié le
6 novembre : la recette recalcule 10 campagnes sur 10**, dont l'empreinte
exacte que l'évaluation n'a pas su reproduire. Elle avait exclu un champ là
où la recette en exclut deux.

Rien n'était donc faux dans l'empreinte. Ce qui était faux, c'était la
**revendication** : *« recalculé indépendamment »* se lit comme une garantie
qu'un relecteur peut exercer, et la recette n'était écrite nulle part. **Une
revendication vraie que personne d'autre ne peut exercer est, vue de
l'extérieur, indiscernable d'une revendication fausse.**

La correction est un tableau de quatre classes dans
[`CORPUS_REFERENCE.fr.md`](CORPUS_REFERENCE.fr.md#vérifier) : qui peut
vérifier quoi, avec quel accès. La classe C — *vérifiable avec l'instrument,
pas sans lui* — est celle où `campaign_sha256` se trouve jusqu'à publication
de la recette. **Faire passer une empreinte de C à B est toujours un acte de
documentation, jamais de cryptographie.**

---

## R-3 — pourquoi un profil, et non une correction

Le dossier de revue V1 est **octet pour octet** la fixture de CI, et cette
empreinte est portée par trois pièces signées : l'attestation Ed25519, la
preuve OpenTimestamps ancrée dans les blocs Bitcoin 974714/974715, et le
manifeste de liaison.

Corriger le générateur en place aurait **invalidé en silence une chaîne de
preuve signée et horodatée**. Le générateur est donc versionné :

```sh
python tests/make_fixture.py <rep>              # v2, le profil fidèle
python tests/make_fixture.py <rep> --profile v1 # l'archive historique, à l'octet
```

Le cas 1 de [`tests/test_completude.py`](../tests/test_completude.py) est la
garde : il échoue si `v1` cesse un jour de reproduire `e31e12bb…`. Rien
d'autre dans le dépôt ne le remarquerait.

| Divergence | Traitement |
|---|---|
| mesures non chaînées | **corrigé** — les quatre membres chaînés dans un seul registre |
| aucune cause sur une mesure incomplète | **corrigé** — `reason` porte la cause **par signal** |
| `sequence` repartant par membre | **corrigé** — monotone sur tout le registre |
| `registre.enregistrements` = 4 pour 16 livrés | **corrigé** — le total source, l'export compté à part |
| recette de `record_sha256` sans `sequence` | **réduit et déclaré** — même jeu de champs que l'instrument, la canonicalisation est `json.dumps(sort_keys)` et le dit |
| `code_commit` / `config_snapshot_sha256` en remplissage | **conservé, et déclaré** — un objet synthétique doit porter un remplissage visible, pas une valeur d'allure plausible |

Le sixième est celui qui reste. Implémenter RFC 8785 ici serait la **seconde
implémentation du registre que ce produit refuse de construire** — deux
implémentations qui divergent ne prouvent rien, et celle qui a écrit le
registre n'est pas celle-ci. `v2` aligne donc le jeu de champs et déclare que
la canonicalisation ne coïncide que sur le domaine de valeurs de cette
fixture.

### Et v2 retient des enregistrements, exprès

Le registre source porte désormais **six** types et l'export en livre
**quatre** — un `run` et quatre `runner_attempt` sont écrits dans la chaîne
et retenus. Sans cela, R-1 et R-2 ne seraient pas **éprouvables** : on ne
teste pas un contrôle de complétude sur un objet complet.

Les enregistrements retenus participent à la chaîne. C'est le fond du sujet :
**une chaîne valide ne dit rien de la complétude d'un export.**

---

## La garantie neuve, et ses limites exactes

Une ligne de contrôle, `complétude de l'export`. Ce qu'elle établit :

- l'archive **nomme** ce que son registre portait, ce qu'elle a exporté et ce
  qu'elle a retenu, avec les décomptes ;
- ces trois nombres **s'additionnent** ;
- le décompte exporté concorde avec la somme des décomptes de membres.

Ce qu'elle n'établit **pas**, et qu'il ne faut jamais y lire :

- **que la retenue était légitime.** Le contrôle lit une déclaration. Une
  archive peut déclarer retenir 30 enregistrements et mentir sur le pourquoi.
- **que rien d'autre ne manque.** Il vérifie l'arithmétique d'une
  déclaration, pas le registre, qu'il n'a pas.
- **la complétude d'une archive qui ne déclare pas le contrat.** Ce cas vaut
  `NOT TESTED` — pas `PASS`.

Le `NOT TESTED` n'est **pas** marqué requis. Dans ce dépôt, `requis` signifie
*« ce NOT TESTED serait évitable si l'appelant fournissait ce qui manque »*.
Ici l'appelant ne peut rien : c'est le **producteur** qui doit déclarer. Le
marquer requis ferait sortir en 2 toute archive historique, pour un manque
que son porteur n'a pas créé.

---

## Conséquences pour les archives historiques

**Aucune preuve historique n'a été modifiée.** Trois traitements distincts :

| | |
|---|---|
| Le dossier V1, son attestation, sa preuve | **intacts.** `v1` le reproduit octet pour octet |
| Les chiffres que nous avons remesurés | réécrits : le guide de l'auditeur, la CI, le descripteur du générateur, l'attente de la suite d'attestation |
| Les chiffres que nous **ne pouvons pas** remesurer | annotés, non réécrits. GROUNDED-S1 et MED ne sont pas dans ce dépôt ; leur nouveau décompte est *dérivable* — une ligne de plus — mais **dérivable n'est pas mesuré**, et ce produit existe pour tenir cette distinction |
| Les observations datées | **laissées telles quelles.** Les deux rapports d'audit du 5 novembre, le rapport de consolidation et la matrice d'attestation consignent des mesures prises à une date. Les réécrire falsifierait un relevé |

Une archive antérieure au contrat porte désormais **un `NOT TESTED` de
plus**. C'est la conséquence honnête de l'ajout d'une garantie : le décompte
ne s'est pas dégradé, le rapport s'est complété.

---

## Ce qui reste ouvert

| | |
|---|---|
| **R-6** | structurel. Enregistrer la provenance de l'évaluateur dans `measurements.jsonl` affecte l'instrument, les consommateurs **et les archives gelées** — cela déplacerait des frontières de comparabilité. L'analyse d'abord, aucun code |
| **R-5, seconde moitié** | publier la recette. Une formule sur un objet dont la forme est déjà décrite, sans clé ni contenu de jeu de données — mais la décision ne nous appartient pas seuls |
| **R-9 / B-1** | l'identité juridique du signataire. Rien de technique ne la remplace |
| La sixième divergence | la canonicalisation de `record_sha256`. Déclarée, pas fermée |
| La cause par signal, comme **contrôle** | `v2` porte les causes ; rien ne vérifie encore qu'un signal non mesuré en nomme une |
| Le texte du prompt, et l'identité des cinq évaluateurs | l'évaluation les a trouvés absents des données examinées. R-6 couvre le second ; le premier est une décision de mesure, pas d'Evidence |

---

## La distinction d'architecture que ce travail protège

**From AI Behavior to Auditable Evidence** — Measurement → Station →
Evidence.

Evidence produit des preuves vérifiables dont les garanties **et les
limites** sont explicites. Il ne certifie pas, à lui seul, qu'une exécution
IA était juste ou conforme. Cinq choses restent distinctes, et l'évaluation
ODA3 est ce qui a forcé la cinquième sur la page :

| | |
|---|---|
| **Intégrité** | les octets sont ceux auxquels l'enregistrement se réfère |
| **Provenance** | qui les a produits, avec quoi, et si cela est attesté |
| **Complétude** | si ce qui est offert est tout ce qu'il y avait — **nouveau comme contrôle** |
| **Reconstruction** | si les entrées peuvent être reproduites, et si la mesure peut l'être |
| **Suffisance probatoire** | si tout ce qui précède soutient une affirmation *précise* — et celle-là n'est jamais établie par un outil |

Les décomptes de verdicts de l'évaluation le disent mieux qu'un résumé :
**27 revendications soutenues, 8 non soutenues, 3 indéterminées, 6
partagées, 10 non observables**. Un produit dont l'évaluation ne rend que du
vert n'a pas été évalué.

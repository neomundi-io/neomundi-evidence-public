<sub>🇬🇧 <a href="REPLAY_FEASIBILITY.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Rejeu d'une mesure — étude de faisabilité

**5 novembre 2026.** Étude seule. Rien n'a été rejoué, rien n'a été
développé, aucune exécution n'a été déclenchée.

---

## La question posée

Peut-on, à partir d'un dossier de preuve, **rejouer** la mesure et obtenir le
même résultat ?

La réponse dépend entièrement de ce que « rejouer » et « le même » veulent
dire. Trois choses distinctes sont régulièrement confondues :

| | Ce qu'on referait | Verdict |
|---|---|---|
| **Rejeu des entrées** | re-soumettre les mêmes entrées enregistrées au même code | **GO** |
| **Rejeu de la mesure** | obtenir les mêmes cinq signaux | **NO-GO** en l'état |
| **Reproduction à l'octet du registre** | réécrire le registre identique | **NO-GO**, et à ne jamais annoncer |

---

## Ce que les archives fournissent déjà

Mesuré sur `NEOMUNDI_EVIDENCE_DEMO_V0.1.zip`, schéma
`station.export.campagne/2`, 30 observations :

| Élément | État | Conséquence pour un rejeu |
|---|---|---|
| `code_commit` | **unique** — `a52715d3…` sur les 30 | la révision du code est identifiée |
| `config_snapshot_sha256` | **unique** — `7882f080…` sur les 30 | la configuration est identifiée par empreinte |
| `measurement_version` | **unique** — `3.3.1` | le contrat de mesure est identifié |
| `replay_provenance.jsonl` | 30 enregistrements, `recording_path` + `recording_sha256` + `bundle_sha256` | **les entrées sont identifiables et vérifiables** |
| Registre | 151 enregistrements, tête `fc1f2787…`, `chaine_verifiee: true` | déclaré par l'exportateur, **non recalculé** par `verify.py` |

Les empreintes d'entrée se recalculent : c'est le contrôle `empreintes des
entrées rejouées` de `verify.py`, qui rend 30/30 conformes quand le corpus
gelé lui est fourni.

**Donc le premier étage du rejeu est acquis.** Les entrées sont là, et on
sait prouver que ce sont bien elles.

---

## Pourquoi le deuxième étage ne l'est pas

### 1. Les mesures incomplètes sont la règle, pas l'exception

Sur les 30 mesures de ce lot :

| Statut | Nombre |
|---|---|
| `measured` | 15 |
| `degraded` | 8 |
| `not_measured` | 7 |

Et par signal, le nombre de valeurs **absentes** :

| Signal | `null` sur 30 |
|---|---|
| `semantic_instability_score` | 22 |
| `factual_hallucination_score` | 14 |
| `stability_score` | 14 |
| `coherence_score` | 7 |
| `semantic_risk` | 7 |

Un rejeu fidèle devrait reproduire **ces absences-là**. Or une absence de
signal n'est pas une propriété de l'entrée : c'est la trace de ce qui était
joignable au moment de la mesure. La reproduire exigerait de reproduire
l'état des évaluateurs, pas celui du corpus.

C'est le point de blocage, et il n'est pas contournable par du code.

### 2. Les évaluateurs sont distants et non déterministes

La mesure appelle des évaluateurs externes. Leur disponibilité est variable,
et une indisponibilité produit un `degraded` ou un `not_measured` plutôt
qu'une erreur. Deux conséquences :

- deux exécutions sur la même entrée peuvent rendre des couvertures
  différentes, sans qu'aucune soit fausse ;
- le modèle **servi** n'est pas garanti identique au modèle **demandé** :
  l'identifiant publié est celui demandé, et un alias peut se déplacer.

### 3. Ce lot est en régime `synthetic`

`regimes_d_execution: ["synthetic"]`, et la garde de lecture inscrite dans
l'archive le dit :

> ces réponses ont été fabriquées pour le banc et n'observent aucun opérateur
> réel.

Rejouer GROUNDED-S1 avec succès ne dirait donc **rien** de la possibilité de
rejouer une campagne réelle. Un rejeu démontré sur du synthétique serait une
démonstration sur le mauvais objet.

### 4. Le gel des données n'est pas la reproductibilité du calcul

Les deux ont été tenus séparés depuis le GATE 0, et pour une raison
constatée : sept divergences avaient été attribuées à un changement de code
postérieur. Un corpus gelé garantit les **entrées**. Il ne garantit pas que
le calcul se refasse à l'identique.

---

## Verdicts

### Rejeu des entrées — **GO**

Faisable aujourd'hui, et déjà fait : le régime `replay` existe, les
empreintes d'entrée se vérifient, et `bind.py` permet désormais d'attacher
l'enregistrement d'entrée à l'observation avec un niveau de garantie dérivé.

**Ce que cela établit :** que les entrées rejouées sont bien celles de
l'enregistrement. Rien de plus.

### Rejeu de la mesure, résultat **identique** — **NO-GO**

Bloqué par les points 1 et 2, et aucun des deux ne relève d'un défaut à
corriger. Les annoncer résolus serait faux.

**Condition de lever :** que la mesure devienne déterministe à entrées
constantes, ce qui supposerait des évaluateurs locaux, figés et attestés par
empreinte du modèle servi. Ce n'est pas une évolution de ce dépôt.

### Rejeu de la mesure, résultat **comparable** — **GO conditionnel**

Faisable, à cinq conditions, toutes vérifiables :

1. **un budget de divergence déclaré d'avance** — une tolérance par signal,
   écrite avant l'exécution, pas après ;
2. **la couverture comparée avant les valeurs** — deux mesures de couvertures
   différentes ne se comparent pas signal par signal ;
3. **`measurement_version` identique de part et d'autre**, sinon les frontières
   de comparabilité sont franchies ;
4. **la provenance des évaluateurs enregistrée** des deux côtés, y compris le
   modèle réellement servi quand il est attesté ;
5. **aucun appel payant sans autorisation explicite** — ce qui en pratique
   pointe vers un environnement d'essai local plutôt que vers la production.

**Ce que cela établirait :** que le calcul se refait dans une tolérance
annoncée. Pas que le résultat d'origine était juste.

### Reproduction à l'octet du registre — **NO-GO permanent**

À ne jamais annoncer. Un registre porte des horodatages et un chaînage ;
le réécrire identique supposerait de reproduire l'instant de son écriture.
Le gel est le seul enregistrement autoritatif, et c'est ainsi qu'il a été
constitué.

---

## Ce qu'il faudrait construire, et dans quel ordre

Rien de tout cela n'est développé ici, et rien ne doit l'être sans décision.

| Étape | Objet | Préalable |
|---|---|---|
| 1 | un harnais de rejeu **hors production**, sur l'Ollama du poste | aucun — les deux modèles y sont déjà |
| 2 | enregistrer la provenance des évaluateurs à chaque rejeu | que le contrat la porte des deux côtés |
| 3 | comparer couverture d'abord, valeurs ensuite, tolérance déclarée | l'étape 1 |
| 4 | un rapport de divergence qui distingue *absent*, *différent* et *hors tolérance* | les étapes 2 et 3 |
| 5 | rejeu sur un lot **non synthétique** | une autorisation, et un corpus réel gelé |

L'étape 5 est celle qui compte, et c'est la seule qui exige une décision
d'exploitation plutôt qu'un développement.

---

## Ce que cette étude n'établit pas

Elle s'appuie sur les deux archives de démonstration et sur ce qu'elles
déclarent. Le code de la Station n'a pas été relu pour cette étude, aucune
campagne n'a été lancée, et aucun évaluateur n'a été appelé. Les durées, les
coûts et les taux de réussite d'un rejeu réel restent **inconnus** : aucun
chiffre n'est avancé ici parce qu'aucun n'a été mesuré.

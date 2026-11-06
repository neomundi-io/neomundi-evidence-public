<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="R6_PROVENANCE_CONTRACT.md">English</a> · <a href="../README.md">← README</a></sub>

# R-6 — provenance des évaluateurs : proposition de contrat

**6 novembre 2026.** Répond à la recommandation **R-6** de l'évaluation
ODA3 : *consigner la provenance de l'évaluateur dans `measurements.jsonl`.*

> **Proposition seulement. Rien d'implémenté, et rien de proposé à Station.**
> Le contrat ci-dessous est à valider avant que quiconque écrive du code.
>
> L'**inventaire mesuré** qui fonde cette proposition — quel évaluateur, quel
> modèle, quel moteur, avec quelles empreintes de configuration — est
> conservé en interne et n'est pas publié ici. Publier les internes de
> l'instrument de mesure est une décision de divulgation, pas une décision
> d'ingénierie. Ce document énonce ce qui a été mesuré en nombres, et ne
> nomme aucun modèle, aucun hôte, aucune empreinte.

---

## Correction du 6 novembre 2026 — l'audit révise cette proposition

**Ce document proposait une structure que Station possède déjà.** L'audit des
dépôts l'a établi, et la proposition en est simplifiée plutôt que compliquée.

| Maillon | État réel | Preuve |
|---|---|---|
| L'API **émet** la provenance | ✅ | `GovernResponse.evaluators` — par signal : l'évaluateur, le modèle utilisé, le statut, le motif, des empreintes de configuration |
| Station **modélise sa conservation** | ✅ | `src/station/runtime/coverage.py` : `MeasurementCoverage`, type d'enregistrement `measurement_coverage`, avec sa **barrière anti-secret appliquée à la construction** et ses tests |
| Station **câble** l'écriture | ❌ | `to_coverage()` n'a **aucun appelant** dans `src/` — seulement sa définition, sa réexportation et un test unitaire |
| Le registre en porte | ❌ | **0 enregistrement** `measurement_coverage` sur trois registres (types réels : `run`, `runner_attempt`, `observation`, `measurement`, `reference_evaluation`, `replay_provenance`) |
| L'**export** le transporte | ❌ | `station.export.campagne/2` = 8 membres, **0 occurrence** de `coverage` dans `src/station/runner/export.py` |
| Evidence le consomme | ✅ **désormais** | `adapters/provenance.py`, et `verify.py` accepte `/3` |

**Deux rectifications de ce document.** Son §3 annonçait « 0 champ de
provenance sur 238 mesures » : c'est vrai, et c'était mesuré sur des
**registres gelés** écrits avant que `coverage.py` n'existe. La conclusion
change : le trou n'est pas conceptuel, il est de **câblage**.

Et sa « Partie A / Partie B » inventait un découpage. `MeasurementCoverage`
en propose un meilleur, pour une raison que je n'avais pas vue :
`Measurement` est un **schéma scellé**, et l'empreinte de chaque
enregistrement déjà écrit dépend de la forme du contrat. Un **contrat neuf**
n'en migre aucun. C'est donc le modèle existant qui est adopté, et non le
mien.

---

## Les trois décisions, argumentées

### D1 — câbler `to_coverage` dans le chemin d'écriture

**Recommandation : OUI, et c'est la moins chère des trois.** Le modèle
existe, il est testé, il porte sa propre barrière anti-secret, et c'est un
type d'enregistrement **distinct** : aucun schéma scellé ne migre, aucune
empreinte déjà écrite ne bouge. C'est un branchement, pas une conception.

Sans D1, D3 n'a rien à transporter.

*Station, branche et PR séparées. Non fait ici : cela touche le chemin
d'écriture d'une mesure vivante.*

### D2 — instrumenter les évaluateurs sous-renseignés

**Recommandation : PAS MAINTENANT, et surtout pas en prérequis.**

Trois situations se cachent derrière « sous-renseigné », et les confondre
serait faux dans deux directions : un **calcul local** n'a ni modèle ni
prompt — ses nuls sont **corrects**, et `adapters/provenance.py` ne les lit
pas comme un trou ; deux évaluateurs **appellent** un modèle sans rapporter
leur moteur — c'est une vraie sous-population, côté API ; un seul renseigne
tout, parce qu'il franchit une frontière HTTP et qu'il a bien fallu.

Le contrat doit donc **accepter `null` avec un motif**, plutôt que d'attendre
une instrumentation qui fabriquerait une valeur plausible. Une provenance
inventée est indiscernable d'une provenance réelle, et c'est le seul risque
de ce chantier qu'on ne peut pas rattraper.

### D3 — l'export porte le membre

**Recommandation : OUI.** Un membre de plus, additif, et les huit autres
inchangés. `verify.py` accepte déjà `/3`, et une archive `/2` reste lisible :
les contrôles de provenance y rendent `NOT TESTED`, jamais `FAIL` — le trou
est celui du producteur, exactement comme pour le contrat de complétude.

---

## Le contrat consolidé — `station.export.campagne/3`

**Un membre ajouté : `measurement_coverage.jsonl`.** Il porte les
enregistrements `MeasurementCoverage` tels que Station les écrit, dans les
octets d'origine du registre, sans interprétation :

```
coverage_id | measurement_id | observation_id | measurement_version
coverage_version | api_measurement_status | checks_attempted
checks_succeeded | failed_checks | degraded_g_inputs
unmeasured_signals | evaluators | reported_at
```

`evaluators` est **opaque et verbatim** : un dictionnaire par signal, dont
Evidence constate les champs présents et nomme les absents, sans jamais en
compléter un. Les six champs de diagnostic sont **tous optionnels**, et leur
`None` est porteur : une API antérieure ne les sert pas, et un tel silence ne
peut pas affirmer que tout s'est bien passé.

**Ce qu'Evidence en fait**, et les trois niveaux qu'il en dérive :

| Niveau | Quand |
|---|---|
| `instrument_non_documente` | pas de membre de couverture, ou aucun `evaluators` |
| `instrument_declare` | les évaluateurs sont nommés, sans empreinte de configuration |
| `instrument_declare_et_configure` | nommés **et** configurés, pour tous les signaux qui ont un modèle |

**Il n'existe pas de quatrième niveau.** `instrument_verifie` serait une
prétention qu'aucune archive ne peut soutenir : que l'évaluateur déclaré soit
celui qui a tourné exigerait d'observer la mesure. C'est un `NOT TESTED`
permanent, et le cas 11 de `tests/test_provenance.py` échoue si un quatrième
niveau apparaît.

---

## La réponse courte

**La provenance ne peut pas être documentée depuis les données existantes :
R-6 exige donc une évolution de contrat.** Mesuré, non déduit :

- l'API de mesure **émet déjà** un bloc de provenance de 12 champs par
  signal, et l'identité de l'évaluateur est renseignée pour **5 signaux sur 5
  sur 7 observations sur 7** ;
- le registre n'en conserve **rien** — 0 champ de provenance sur **238 mesures
  dans 8 registres gelés**, tous en `measurement_version 3.3.1` ;
- aucune archive Evidence ne peut donc exporter ce que son registre n'a jamais
  tenu.

**La perte se produit à l'écriture du registre, dans Station. Pas dans
Evidence, et pas dans l'API.** Ce seul fait décide où le changement
appartient — et ce n'est pas ici.

---

## 1. Ce qui a été mesuré

| Question | Réponse |
|---|---|
| L'identité de l'évaluateur est-elle consignée à l'API ? | **oui, complètement** — 5 signaux × 7 observations, sans trou |
| Combien de champs de provenance atteignent le registre ? | **zéro**, sur 238 mesures dans 8 registres |
| Combien d'évaluateurs renseignent pleinement les champs profonds ? | **1 sur 5** — le seul qui appelle une API HTTP externe |
| Combien de signaux partagent un même appel d'évaluateur ? | **2** — un appel, un modèle, deux notes |
| L'écart peut-il être rétro-rempli sur les archives historiques ? | **non** |

**La prémisse de R-6 demande une précision.** L'identité de l'évaluateur n'est
pas absente — elle est consignée, puis abandonnée. R-6 ne porte pas sur
l'invention de champs, mais sur le transport de champs existants à travers une
frontière.

### Trois situations distinctes derrière « sous-renseigné »

- Un évaluateur est un **calcul local** : aucun modèle, aucun prompt. Ses
  nuls sont **structurellement corrects**, pas un trou. Un contrat qui
  exigerait ici une empreinte de prompt exigerait une valeur qui n'existe pas.
- Deux évaluateurs **appellent bien un modèle** et ne rapportent ni
  tentatives, ni moteur, ni empreinte de configuration. **C'est une véritable
  sous-population**, et c'est la seule part de R-6 qui soit un défaut
  d'instrumentation plutôt qu'un trou de contrat.
- Un évaluateur renseigne tout, parce qu'il franchit une frontière HTTP et
  qu'il a bien fallu.

Confondre ces trois cas en « provenance absente » serait faux dans deux
directions à la fois.

## 2. Identifiants stables contre valeurs par appel

C'est le constat qui change le coût de R-6, et il doit être lu avec sa taille
d'échantillon : **n = 7**.

| | Nombre | Nature |
|---|---|---|
| **Stables par nature** | 5 champs | identifiants de configuration : ils changent quand l'instrument change, pas à chaque mesure |
| **Par appel, constants dans cet échantillon** | 3 champs | **n = 7 ne prouve rien sur leur stabilité.** L'un existe précisément parce qu'un repli est possible, un autre parce qu'une reprise l'est |
| **Par appel** | 1 champ | la latence : 7 valeurs distinctes |

**Conséquence pour le contrat.** Cinq champs appartiennent **une fois par
campagne**, pas à chaque mesure. Les consigner par mesure multiplierait 238
copies identiques et inviterait un lecteur à croire qu'elles ont été mesurées
à chaque fois.

Mais l'indicateur de repli et le nombre de tentatives doivent rester **par
mesure** : une mesure servie par un repli n'est pas la même preuve qu'une
mesure servie par le primaire, et sept succès ne peuvent pas établir le
contraire.

## 3. Conséquences pour les archives historiques

**Uniformes, et non rétro-remplissables.**

- **238 sur 238** mesures ne portent aucune provenance. Il n'y a aucun
  sous-ensemble à sauver et aucune version qui se soit comportée autrement.
- **Aucun rétro-remplissage n'est possible.** Reconstituer quel modèle a servi
  une mesure d'octobre reviendrait à l'affirmer depuis une configuration
  *supposée* en vigueur. C'est une invention, et elle serait pire que le
  trou : **une provenance fabriquée est indiscernable d'une provenance
  réelle.**
- **Les corpus gelés restent tels quels.** Leurs empreintes sont chaînées et,
  pour certaines, attestées.
- Toute affirmation sur les évaluateurs d'une archive existante est donc
  **`not_demonstrable`** — et non `declared`, puisque rien ne la déclare.

### L'asymétrie difficile à défendre

Le même registre consigne, richement, le **modèle observé** (fournisseur,
demandé, servi, attestation, paramètres envoyés et effectifs, version et
empreinte du prompt) et l'**évaluateur de référence** (versionné et empreinté).

Et **rien** sur les cinq instruments qui ont produit les signaux.

L'archive trace donc le *sujet* de la mesure et la *référence* qui a servi à
le juger, et pas l'*instrument de mesure*. Dit simplement, cet ordre est
inversé.

---

## Proposition de contrat — `station.export.campagne/3`

> **REMPLACEE** par « Le contrat consolidé » ci-dessus. Cette version
> inventait un découpage Partie A / Partie B ; `MeasurementCoverage` en
> propose un meilleur, et il existe. Conservée comme relevé du raisonnement,
> et **ne pas l'implémenter**.

Une **nouvelle version**, pas une modification de `/2`. Trois parties.

### Partie A — un bloc `evaluateurs` au niveau de la campagne

Les cinq identifiants de configuration, une fois, dans le manifeste :

```json
"evaluateurs": {
  "contrat": "neomundi.evaluator-provenance/1",
  "par_signal": {
    "<signal_a>": {
      "evaluator": "<identifiant de fonction>",
      "kind": "computation",
      "model_configured": null,
      "evaluator_runtime": null,
      "prompt_template_hash": null,
      "inference_config_hash": null,
      "config_fingerprint": null
    },
    "<signal_b>": {
      "evaluator": "<identifiant de fonction>",
      "kind": "external_model",
      "model_configured": "<identifiant de modele>",
      "evaluator_runtime": "<hote du moteur>",
      "prompt_template_hash": "<16 hex>",
      "inference_config_hash": "<16 hex>",
      "config_fingerprint": "<16 hex>",
      "shares_call_with": ["<signal_c>"]
    }
  }
}
```

`kind` est ce qui rend les nuls lisibles : `computation` déclare qu'aucun
modèle et aucun prompt n'existent, donc que leur absence est **correcte** et
qu'un vérificateur ne doit pas la traiter comme un trou. Sans lui, tout
vérificateur devrait coder en dur quels signaux ont un modèle.

`shares_call_with` évite le piège de duplication du §1 : deux signaux, un
appel, et un lecteur qui devrait le savoir. Sans lui, un lecteur compterait
raisonnablement deux instruments indépendants là où il n'y en a qu'un.

### Partie B — par mesure, seulement ce qui varie

```json
"evaluateurs_execution": {
  "<signal_b>": {
    "status": "measured", "reason": null,
    "model_used": "<identifiant de modele>", "served_by": "primary",
    "attempts": 1, "latency_ms": 0.0
  }
}
```

Six champs, pas douze. L'indicateur de repli et le nombre de tentatives sont
ici et **pas** en partie A, pour la raison du §2.

### Partie C — ce qu'Evidence vérifie, et ce qu'il refuse de vérifier

| Contrôle | Verdict |
|---|---|
| le manifeste déclare un bloc `evaluateurs` | `PASS` / `NOT TESTED` s'il est absent |
| chaque signal mesuré a une entrée | `PASS` / `FAIL` sur un trou |
| un évaluateur `computation` ne déclare aucun modèle | `PASS` / `FAIL` s'il en déclare un |
| un évaluateur `external_model` déclare son moteur et ses empreintes | `PASS` / `FAIL` si partiel |
| `model_used` concorde avec `model_configured`, ou l'indicateur de repli explique pourquoi non | `PASS` / `FAIL` / `NOT TESTED` |
| **que l'évaluateur déclaré soit celui qui a tourné** | **jamais vérifiable.** Un `NOT TESTED` permanent |

La dernière ligne est l'importante. Evidence peut contrôler qu'une
déclaration est **complète et cohérente avec elle-même**. Il ne peut pas
contrôler qu'elle est **vraie** — cela exigerait d'observer la mesure, ce qui
est le rôle de Station et non celui d'une archive. Tout contrôle qui
prétendrait l'inverse serait le faux `PASS` que ce produit existe pour
refuser.

---

## Compatibilité

| | |
|---|---|
| Archives `/2` | **inchangées, et toujours valides.** Les contrôles ci-dessus y sont `NOT TESTED`, jamais `FAIL` — le trou est celui du producteur, exactement comme pour le contrat de complétude |
| Archives `/3` | les nouveaux contrôles s'appliquent |
| `verify.py` | doit accepter les deux schémas. Il tient déjà une liste de schémas connus |
| Corpus gelés | intouchés. Aucun ré-export, aucune re-signature |
| Comparabilité | **une archive `/3` n'est pas comparable à une `/2` sur la provenance** — non parce que les valeurs diffèrent, mais parce qu'un côté n'en a aucune. Cette frontière doit être déclarée comme les autres |

## Risques

| Risque | Pourquoi il compte |
|---|---|
| **Inventer une provenance pour les évaluateurs sous-renseignés** | le vrai danger. Si un évaluateur ne peut pas rapporter son moteur, le contrat doit accepter `null` **avec une raison**, pas une valeur d'apparence plausible |
| **Lire une archive `/3` comme validant le passé** | publier une `/3` à provenance complète peut faire paraître déficientes les 238 mesures historiques. Elles ne le sont pas : elles ont été produites sous un contrat qui ne demandait pas |
| **Confondre deux signaux avec deux instruments** | atténué par `shares_call_with`, et par lui seul |
| **Gonfler chaque mesure de 60 champs** | atténué par la coupe A/B. Fait naïvement, R-6 ajouterait cinq blocs de 12 champs à chacun des 238 enregistrements |
| **Traiter une déclaration complète comme une déclaration vraie** | le risque structurel de toute provenance. Atténué seulement par le `NOT TESTED` permanent de la partie C |
| **Divulguer les internes de l'instrument** | nommer modèles, hôtes et empreintes de configuration dans une archive publique est une **décision de divulgation**. Elle n'est pas prise ici, et un producteur `/3` doit la prendre délibérément |

## Ce que cette proposition ne demande PAS à Station

Rien, pour l'instant. Elle décrit ce qu'un export `/3` porterait **si**
Station choisissait de l'écrire. Trois décisions distinctes en découlent, et
aucune n'est prise ici :

1. si l'écriture du registre de Station conserve le bloc de provenance de
   l'API ;
2. si les deux évaluateurs sous-renseignés sont instrumentés ;
3. si l'export le porte.

Seule la troisième concerne Evidence, et c'est la dernière des trois.

---

## Recommandation

**R-6 est un écart réel, correctement identifié, et il ne peut pas être fermé
par de la documentation.** Mais son coût est plus faible que « structurel » ne
le suggère : la provenance existe déjà à l'API, le contrat y est déjà
uniforme, et cinq de ses huit champs renseignés appartiennent une fois par
campagne plutôt qu'à chaque enregistrement.

Ce qu'Evidence peut faire **aujourd'hui, sans toucher à rien** : déclarer
l'absence. Une ligne de contrôle énonçant qu'une archive `/2` ne porte aucune
provenance d'évaluateur, et que toute affirmation sur l'instrument de mesure
est donc `not_demonstrable`. Ce n'est pas R-6 — c'est l'énoncé honnête de R-6
restant ouvert, et sa place est dans un changement ultérieur, pas dans une
proposition.

<sub>🇬🇧 <a href="V1_CLOSURE_PLAN.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Plan de clôture — les cinq conditions restantes

> **Relevé daté du matin du 6 novembre 2026.** L'état courant est dans
> [`V1_STATUS.fr.md`](V1_STATUS.fr.md) : B-1 est depuis **résolue**, B-2 a ses
> trois décisions. Ce document n'est pas réécrit — réécrire une observation
> datée falsifierait un enregistrement.

**6 novembre 2026.** Suite de
[`V1_QUALIFICATION.fr.md`](V1_QUALIFICATION.fr.md), qui rapportait trois
conditions résolues, quatre partielles, une bloquée. Périmètre :
**expérimental, scientifique, non commercial.**

---

## Où en sont les cinq

| | Condition | Était | Est | Ce qui la ferme |
|---|---|---|---|---|
| **C-6** | Traduire la sortie des vérificateurs | 🟠 2 outils sur 6 | 🟢 **RÉSOLUE** | — faite : 7 outils, couverture mesurée sur 13 scénarios |
| **C-5** | Publier le magasin sur un second canal | 🟠 conception seule | 🟠 **PARTIELLE** — les deux préalables **construits** | un audit de contenu, validé par le représentant de B-1 |
| **B-1** | Trancher l'identité juridique | 🔴 bloquée | 🔴 **BLOQUÉE** — mais désormais **approuvable** | trois signatures sur une fiche de décision |
| **B-2** | Une clé de production, et sa garde | 🟠 procédure écrite | 🟠 **PARTIELLE** — garde proposée, procédure ordonnée | l'acceptation de la garde, puis B-1 |
| **D-7** | Recevoir le dossier CP8 complet | 🟠 inventorié | 🟠 **PARTIELLE** — deux pièces identifiées, demande rédigée | Dennis envoyant deux artefacts |

**Une résolue cette session. Trois attendent désormais un acte humain, pas
du code.**

---

## Ce qui a changé, et pourquoi cela compte

### C-6 est fermée

Les sept outils acceptent `--lang {fr,en}`. 147 sites d'appel ont été
convertis mécaniquement — `print(` → `dis(` — après avoir vérifié que le
décompte du texte égale celui des appels dans l'AST de chaque fichier, donc
qu'aucune occurrence ne vivait dans un commentaire.

La couverture est **mesurée**, pas déclarée : la suite exerce les outils sur
13 scénarios et échoue sur toute prose française non traduite, comme sur
tout écart de code de sortie entre les deux langues.

Une règle a dû être écrite pour y parvenir : **une chaîne qui figure
verbatim dans un fichier d'entrée est une donnée, pas de la prose.**
`reconcile.py` imprime les étiquettes du partenaire et le texte libre de la
table de correspondance ; les traduire ferait cesser le rapport de nommer ce
que le partenaire a écrit. Le cas 23 le vérifie dans l'autre sens — il exige
qu'une telle chaîne existe et ressorte inchangée, pour que « c'est une
donnée » n'excuse rien.

### Les deux préalables de C-5 sont construits

Les deux étaient nommés bloquants dans sa propre conception, et les deux
sont faits :

- **`store_version`** — un entier monotone, désormais exigé. Le schéma
  portait un tableau `changes`, mais c'est un relevé, pas une version
  comparable, et **aucun code ne le lisait**. Sans version ordonnable, deux
  auditeurs détenant des magasins différents ne peuvent pas dire lequel est
  le plus récent.
- **`--store-digest`** — confronte les octets du magasin à une empreinte
  obtenue par un autre canal. Trois états, et le défaut est l'honnête :
  concordante → `PASS`, divergente → `FAIL`, absente → `NOT TESTED`. Un
  magasin non confronté n'est pas faux ; il est non confronté.

**Rien n'est publié.** Ce qui reste est l'audit de contenu — sept points,
dont la relecture de chaque champ `notes`, là où le contexte interne fuit —
et il demande quelqu'un ayant autorité pour le valider. Ce quelqu'un est le
D-2 de B-1.

### B-1 est encore bloquée, mais pas pour la raison d'hier

Hier elle l'était parce que la décision n'avait pas été prise. Aujourd'hui
elle l'est parce que **la fiche de décision n'est pas signée** — ce qui est
une distance bien plus courte.

[`B1_EXPERIMENTAL_SIGNING_DECISION.fr.md`](B1_EXPERIMENTAL_SIGNING_DECISION.fr.md)
met **une** proposition sur la table au lieu de trois options : **NeoMundi
Recherche**, l'association française, RNA W563015824 — la seule des trois
entités dont l'objet couvre l'acte, maintenant que le périmètre est
explicitement non commercial. Trois blancs à remplir : l'entité, le **rôle**
du représentant habilité, le **rôle** de l'opérateur.

Elle propose aussi une quatrième valeur pour `legal_capacity_to_attest` :
**`experimental`**. `unverified` sous-dirait une décision réellement prise ;
`verified` sur-dirait un contrôle que personne n'a effectué sur les
statuts. Le changement de schéma attend l'approbation — **une valeur que
personne n'a autorisée serait une invitation à s'en servir.**

### B-2 a des réponses là où elle avait des blancs

[`B2_KEY_CUSTODY_AND_ACTIVATION.fr.md`](B2_KEY_CUSTODY_AND_ACTIVATION.fr.md)
remplit les cinq questions de garde marquées *à décider*, et ordonne
l'activation en quatre gestes dont aucun ne peut être pris en avance.

La distinction avec RGC est désormais argumentée et non affirmée, et la
raison décisive est vérifiable dans le code : le `verify_jws` de RGC dérive
la clé publique **de la clé privée**, donc seul le détenteur du secret peut
vérifier une signature RGC, et hors ligne rien ne marche. Une attestation
Evidence doit être vérifiable par un auditeur qui ne nous fait pas confiance
et n'a pas de réseau. Réutiliser la clé RGC rendrait l'attestation
vérifiable par nous seuls — l'inverse de sa raison d'être.

**Aucune clé n'est générée**, et le document refuse d'en autoriser une avant
que B-1 soit approuvée et la garde acceptée.

### Les deux pièces de D-7 sont nommées exactement

Pas « le dossier complet » — deux artefacts, avec leurs empreintes, et la
raison de chacun :

1. **Le fichier du journal d'audit signé.** Son empreinte est dans
   l'inventaire privé, pas ici. Le raisonnement de Dennis tient ce fichier
   pour canonique, et **nous ne pouvons pas le reproduire** : notre page de
   vérification confirme que l'empreinte figure au registre, et énonce que le
   contenu d'un document n'est jamais conservé. L'empreinte atteste donc
   l'existence et l'émission, **pas le contenu** — et `g_score = 0,3863`
   reste par conséquent au niveau `declared`, pas `reference_verifiable`,
   malgré une empreinte et une URL qui répondent toutes deux.
2. **Le paquet d'exécution avec son `manifest.sha256`**, plus les fichiers
   de constatations, les quatre journaux et le gabarit CVE. Onze empreintes
   sont citées aujourd'hui et **aucun référent n'est fourni**.

Le message rédigé dit aussi quelles deux choses sont **à nous** et non à
lui : la collision d'étiquettes `0,3863` / `0,594`, et l'arithmétique du
décompte de requêtes. C'est ce qui en fait une demande et non un renvoi.

---

## Ordre de réalisation

Le graphe de dépendances n'a pas changé, mais il est plus court.

```
B-1 signee  ──>  schema : `experimental`  ──>  B-2 cle generee
     │                                              │
     └──>  C-5 audit de contenu valide  <────────────┘
                      │
                      └──>  magasin publie, store_kind: production

D-7  independant de tout ce qui precede ; attend Dennis
```

| nº | Geste | Responsable | Bloque |
|---|---|---|---|
| 1 | Signer les trois blancs de B-1 | **Sébastien** | tout ce qui suit |
| 2 | Accepter la garde de B-2 | **Sébastien** | geste 4 |
| 3 | Envoyer la demande CP8 à Dennis | **Sébastien** | D-7 seule — à faire en parallèle, elle a de la latence |
| 4 | Ajouter `experimental` au schéma, avec sa ligne de vérificateur | ingénierie | geste 5 |
| 5 | Générer la clé, hors ligne, sous garde | opérateur | geste 7 |
| 6 | Les sept points de l'audit de contenu | ingénierie, puis Sébastien valide | geste 8 |
| 7 | Ouvrir le registre des dossiers signés | opérateur | première attestation réelle |
| 8 | Publier l'empreinte du magasin sur le `.org` | ingénierie | C-5 fermée |

**Le geste 3 devrait partir en premier en temps réel**, parce que c'est le
seul dont la latence échappe à notre contrôle.

Les gestes 4 à 8 représentent de quelques heures à une journée de travail.
**Rien dans cette liste n'est difficile.** Ce qui bloquait n'a jamais été un
effort d'ingénierie — c'était qu'aucune décision n'avait été mise sous une
forme approuvable.

---

## Ce que tout cela ne ferme TOUJOURS pas

Dit pour que le plan ne se lise pas plus largement qu'il n'est.

- **Le chemin d'entrée d'un pilote.** Evidence consomme des dossiers
  *exportés* par NeoMundi. Une collecte de réponses brutes n'en est pas un,
  et aucun composant ne convertit l'une en l'autre. C'est le verrou que B-3
  a révélé et n'a pas levé, inchangé. Il reste le blocage pour un dossier
  client — et dans le périmètre non commercial, il n'est plus urgent.
- **Une capacité juridique vérifiée.** `experimental` est honnête, pas
  complet. Une offre commerciale demanderait la décision sur la Sàrl et un
  vrai contrôle des pouvoirs.
- **Une date vérifiée par nous.** La preuve OpenTimestamps confirmée donne
  une **borne supérieure** sur le temps, lue comme une hauteur de bloc. La
  convertir en heure demande un en-tête de bloc, et nous déléguons cela,
  nommément, à `ots verify`.
- **Le rapport Markdown de `reconcile.py`**, toujours en français. Un
  artefact fichier, pas une sortie de vérificateur — nommé dans
  [`I18N.fr.md`](I18N.fr.md).

---

## Verdict

### Fusionner la PR #8 — 🟢 GO

Vérifié sur un **checkout propre**, pas sur une copie de travail : `main` =
`e8d8f64`, tête `3b28c06`, `MERGEABLE` / `CLEAN`, cinq contrôles CI verts
sur Python 3.11, 3.12 et 3.13.

- Les dix suites se reproduisent à l'identique depuis un clone neuf.
- Les cinq commandes de l'auditeur rendent les chiffres publiés.
- La preuve confirmée par Bitcoin se vérifie hors ligne depuis le clone :
  `5 PASS, 0 FAIL, 2 NOT TESTED`, blocs 974714 / 974715, et `--strict` la
  sépare de la preuve encore pendante par les codes 0 et 2.
- Confidentialité : **116 fichiers suivis balayés octet par octet, ZIP
  ouverts et inspectés — zéro trouvaille.** Aucun artefact CP8, aucun
  artefact du dossier réel tiers, aucun matériel de clé, aucun chemin de
  machine, aucune donnée personnelle. `__pycache__` est ignoré et aucun
  `.pyc` n'est suivi.
- Périmètre : 30 fichiers, documents, tests, outils et une paire de preuve
  commitée. **Aucun corpus gelé, ni Station, ni API.**

### Poursuivre sur le périmètre expérimental — 🟢 GO

Trois conditions attendent désormais trois signatures. L'ingénierie qui
bloquait est faite, et ce qui reste est borné et ordonné ci-dessus.

### Qualification sur un dossier client réel — 🔴 NO-GO, inchangé

Le chemin d'entrée n'existe pas. Rien dans cette session ne l'a changé, et
rien dans cette session n'était censé le faire : un périmètre non commercial
n'en a pas encore besoin. **Cela ne doit pas se lire comme résolu parce que
les autres conditions ont bougé.**

<sub>🇬🇧 <a href="BINDING.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Lier une observation à ses preuves

**Une description textuelle d'une exécution ne constitue pas une preuve que
cette exécution a réellement eu lieu.** Tout ce qui suit découle de cette
seule phrase.

Une mesure NeoMundi produit un enregistrement. Cet enregistrement déclare les
empreintes d'objets qui ne sont **pas dans l'archive** : la réponse, le
prompt, la requête. Lier, c'est produire un fichier dont les octets se
hachent sur l'une de ces empreintes.

Ce que cela établit : **ce fichier est bien celui auquel l'enregistrement se
réfère.** Ce que cela n'établit pas : que l'exécution a eu lieu, ni quand, ni
chez qui.

---

## Les quatre niveaux de garantie

| Niveau | Signifie | Disponible aujourd'hui |
|---|---|---|
| `declared` | écrit dans le document ; rien de recalculé | oui |
| `reference_verifiable` | l'artefact est là, et ses octets se hachent sur une empreinte que l'enregistrement déclare | **oui** |
| `cryptographically_attested` | une signature d'une clé identifiée vérifie | **non** — rien dans ce dépôt ne vérifie une signature |
| `not_demonstrable` | hors de portée de tout contrôle local | sans objet — c'est un constat, pas un acquis |

**Un manifeste est un ensemble de revendications. Le niveau est dérivé par le
vérificateur, jamais lu dans le document.** Un manifeste qui se revendique
mieux qu'il ne l'est est refusé, et c'est le contrôle le plus important de
l'outil :

```
[FAIL      ] aucune revendication ne depasse ce qui est demontre
             art-01 revendique `cryptographically_attested`, derive `reference_verifiable`
```

Pourquoi la dérivation compte : sans elle, il suffirait d'écrire
`"claimed_assurance": "cryptographically_attested"` dans un fichier texte
pour qu'un document ait l'air d'une preuve.

---

## Emploi

### Construire un manifeste

```sh
python bind.py build \
    --archive NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
    --observation obs-4ccb376a… \
    --artifact response=response.txt \
    --artifact recording=responses/grounded-009.json \
    --statement "Rejoué depuis l'enregistrement gelé du 2026-10-22." \
    --created-at 2026-11-05T12:00:00Z \
    --out manifest.json
```

`--created-at` est **exigé**, volontairement : l'outil ne lit jamais
l'horloge, donc deux exécutions sur les mêmes entrées rendent le même
manifeste, à l'octet.

`build` ne revendique jamais mieux que ce qu'il vient de constater. Un
manifeste écrit à la main peut quand même mentir — c'est au vérificateur de
le dire.

### Vérifier une liaison

```sh
python bind.py verify manifest.json \
    --archive NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
    --json rapport.json
```

Sans `--archive`, les empreintes déclarées ne sont pas confrontées à
l'enregistrement, et le contrôle rend `NOT TESTED` — jamais `PASS`.

| Option | Effet |
|---|---|
| `--root RÉPERTOIRE` | où résoudre les chemins d'artefacts ; défaut : le répertoire du manifeste |
| `--archive FICHIER` | l'archive Evidence du sujet, pour confronter les empreintes déclarées à l'enregistrement |
| `--json FICHIER` | un rapport lisible par machine, en plus ; la sortie texte reste identique |
| `--max-artifact-bytes N` | plafond de lecture par artefact, défaut 64 Mio. Au-delà, l'artefact est `NOT TESTED` et non lu |

Bibliothèque standard seule. Aucun réseau. Aucune écriture hors de la sortie
demandée.

### Un rôle dont le nom trompe — `config_snapshot`

Dans un registre **réel**, `config_snapshot_sha256` porte l'empreinte de la
**campagne**, et non celle d'un fichier de configuration. Le nom dit le
contraire, et c'est un piège qu'il faut nommer : offrir un fichier de
configuration pour ce rôle fait rendre `MISMATCHED`, d'où un relecteur
conclurait que l'artefact a été altéré — alors que seul le champ est mal
nommé.

Le champ n'est **pas** renommé. Le renommer invaliderait toutes les archives
qui le portent déjà, et les archives sont la preuve. Il est documenté à la
place — ici, et par un commentaire à la table de correspondance dans
`bind.py`, là où quelqu'un rencontrerait le piège.

Soulevé comme recommandation **R-7** par l'évaluation externe du 6 novembre,
qui a mesuré que `campaign_sha256` et `config_snapshot_sha256` portent la
**même** valeur dans un registre réel.

---

## Ce que le vérificateur contrôle

| Contrôle | En cas d'échec |
|---|---|
| manifeste lisible, et schéma connu | `FAIL` |
| forme du manifeste : champs requis, types, format d'empreinte, identifiants uniques | `FAIL` |
| l'archive fournie est celle que le manifeste nomme | `FAIL` |
| l'observation sujet existe dans cette archive, une seule fois | `FAIL` |
| le sujet concorde avec l'enregistrement (`record_sha256`, commit, clé de comparabilité) | `FAIL` |
| **les empreintes déclarées sont bien celles de l'enregistrement** | `FAIL` |
| le chemin d'artefact reste sous la racine : ni absolu, ni traversant, ni lien sortant | `FAIL` |
| artefact présent, et ses octets conformes à ce que le manifeste annonce | `FAIL` |
| artefact lié à une empreinte que l'enregistrement déclare réellement | `FAIL` |
| les octets de l'artefact se hachent sur cette empreinte déclarée | `FAIL` |
| **aucune revendication ne dépasse ce qui est démontré** | `FAIL` |
| vérification de signature | toujours `NOT TESTED` |
| énoncés attachés | toujours `NOT TESTED` |
| vérité de l'exécution | toujours `NOT TESTED` |

Un artefact absent est `NOT TESTED`, pas `FAIL` : sa revendication n'a pas été
contredite, elle n'a pas été éprouvée. La liaison retombe alors au niveau
`declared`, et le rapport le dit. Confondre les deux fusionnerait des états
que ce produit garde distincts.

Le niveau agrégé d'une liaison est le **plus faible** de ses artefacts.
Prendre le plus fort laisserait un artefact non ancré se faire couvrir par
son voisin.

---

## Le test central

`tests/test_binding.py` se termine par le test qui justifie tout le
dispositif : deux manifestes portant une prose **identique mot pour mot**,
l'un avec des artefacts ancrés dessous, l'autre sans.

```
  Scenario A : 1 enonce, 0 artefact  -> declared
  Scenario B : 1 enonce, 2 artefacts -> reference_verifiable
```

Le scénario A n'est ni refusé ni accepté comme preuve : il est rendu pour ce
qu'il est, un document déclaratif. Si l'outil rendait le même verdict pour
les deux, il mesurerait la prose au lieu de la preuve.

La suite éprouve aussi dix-sept manifestes fautifs, chacun refusé pour sa
raison propre. Le plus important :

> **l'artefact et le manifeste refaits de concert** — un faussaire qui
> recalcule l'empreinte de son faux artefact et l'inscrit partout dans le
> manifeste obtient un document intérieurement cohérent. Seule la
> confrontation à l'**enregistrement** le prend. C'est pour cela que
> `declared_digests` doit être confronté, et pas seulement recopié.

---

## Terminologie

Les mots portent la rigueur du produit. Ceux-ci n'ont qu'un sens, ici comme
dans le code.

| Terme | Signifie | Ne signifie pas |
|---|---|---|
| **Mesure** | les cinq signaux calculés par le moteur NeoMundi pour une observation | un jugement sur le fond de la réponse ; jamais une validation médicale, juridique ou factuelle |
| **Observation** | un échange enregistré : requête émise, réponse reçue, tels que scellés au registre | l'exécution elle-même |
| **Artefact** | un fichier offert comme l'objet externe auquel l'enregistrement se réfère | une preuve à lui seul |
| **Manifeste** | un document qui *revendique* une liaison entre une observation et des artefacts | un résultat vérifié |
| **Vérification d'intégrité** | recalculer une empreinte sur les octets livrés et la comparer | l'authenticité |
| **Vérification de signature** | contrôler une signature contre une clé identifiée — **non implémentée ici** | une vérification d'intégrité |
| **Provenance** | la chaîne de ce qui a produit un objet, pour autant qu'elle soit recalculable | une déclaration d'origine dans un champ texte |
| **Reconstruction d'exécution** | rebâtir un récit *documentaire* d'une exécution à partir d'enregistrements | que l'exécution ait eu lieu |
| **Rejeu d'exécution** | repasser les mêmes entrées dans le même code pour obtenir un résultat comparable | obtenir les mêmes octets |
| **Vérité de l'exécution** | que l'exécution a réellement eu lieu, à cette heure, chez cet opérateur | quoi que ce dépôt puisse établir |

Deux couples sont régulièrement confondus, et ne doivent pas l'être :

- **intégrité ≠ authenticité.** Une empreinte qui se recalcule dit que les
  octets n'ont pas bougé. Elle ne dit rien de qui les a produits.
- **reconstruction ≠ rejeu ≠ vérité.** La première est documentaire, le second
  est calculatoire, la troisième est historique. Ce dépôt fait la première,
  pas le second, et ne peut pas la troisième.

---

## Limites

- **Aucune signature n'est vérifiée.** `cryptographically_attested` est donc
  hors d'atteinte aujourd'hui, et le vérificateur le dit à chaque exécution.
- **`created_at` et `declared_origin` sont déclarés** par l'auteur du manifeste
  et contredits par rien. Aucune horloge de confiance n'intervient.
- **Un faussaire qui reconstruit à la fois l'archive et les artefacts** produit
  un ensemble cohérent. Seule une empreinte conservée ailleurs qu'avec elle le
  détecte.
- **Aucune URL n'est jamais résolue.** Les artefacts sont des fichiers locaux
  sous une racine explicite ; rien n'est téléchargé.
- **Une liaison ne dit rien de la qualité d'une réponse.** Elle rattache des
  fichiers à un enregistrement. La mesure reste une mesure.

---

## Fichiers

| | |
|---|---|
| `bind.py` | construire et vérifier une liaison |
| `schemas/evidence-manifest-v1.json` | le schéma du manifeste, les niveaux y sont définis |
| `examples/binding/` | une liaison réelle : deux artefacts, tous deux ancrés |
| `tests/test_binding.py` | 1 cas positif, 17 négatifs, 1 scientifique |
| `demo_binding.sh` | les trois verdicts, côte à côte |

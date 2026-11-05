<sub>🇬🇧 <a href="EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Rapport de consolidation — NeoMundi Evidence

**5 novembre 2026.** Branche `feat/evidence-observation-binding-v1`, partie de
`a658af2`. Pull request préparée, **non fusionnée, non déployée**.

---

## Périmètre tenu

Rien de ceci n'a été touché ni appelé : l'API NeoMundi, les moteurs de mesure,
Control Tower, la production, les contrats existants, les données
historiques, le calcul du G-score. Aucun appel externe payant n'a été émis.
`evidence-journey` est conservé intact — HEAD `18cf5719`, zéro modification,
`index.html` toujours `cfb9104c…`.

---

## Synthèse

| Domaine | État initial | Action réalisée | État final | Preuve |
|---|---|---|---|---|
| **Intégrité** | DÉMONTRÉE, mais l'outil plantait sur une entrée malformée | gardes d'entrée, isolation par contrôle, `BILAN` sur tous les chemins | **DÉMONTRÉE et robuste** — 9 entrées malformées sur 9 rendent un verdict motivé | `tests/test_adversarial.py`, 13 détectés / 2 limites / 0 plantage |
| **Provenance** | PARTIELLE — recalculée seulement avec `--corpus` | inchangée dans son principe ; le niveau est désormais nommé et dérivé | **PARTIELLE, et dite comme telle** | `verify.py`, contrôle `empreintes des entrées rejouées`, 30/30 |
| **Association observation / preuve** | **ABSENTE** | niveau 1 construit : schéma, constructeur, vérificateur, quatre niveaux de garantie dérivés | **PARTIELLE** — `reference_verifiable` atteignable, `cryptographically_attested` jamais | `tests/test_binding.py` : 1 positif, 17 négatifs, 1 scientifique, 0 problème |
| **Résolution d'artefacts** | ABSENTE | niveau 2 : racine explicite, refus des chemins absolus, des traversées et des liens sortants, plafond de lecture | **PARTIELLE, locale seulement** — aucune URL n'est jamais résolue | 4 cas négatifs dédiés |
| **Reconstruction / rejeu** | ABSENTE | **aucun développement** — étude de faisabilité seule | **ABSENTE**, avec un GO/NO-GO motivé | `docs/REPLAY_FEASIBILITY.fr.md` |
| **Documentation** | 7 paires EN/FR | +4 paires : audit, liaison, faisabilité, ce rapport ; terminologie en 10 termes | **consolidée, 11 paires** | revue, et les liens vérifiés |
| **Démonstration** | `demo_5min.sh` | `demo_binding.sh` **ajouté**, l'existant non touché | **étendue** | exécution constatée, 3 verdicts distincts |

---

## Lignes de base, avant et après

Enregistrées avant toute modification, et revérifiées après chacune. Aucune
n'a bougé.

| | Avant | Après |
|---|---|---|
| `verify.py` sur GROUNDED-S1 | 19 PASS / 0 FAIL / 2 NOT TESTED, 21 lignes | **identique** |
| `verify.py` sur MED | 10 / 0 / 8, 18 lignes | **identique** |
| `tests/test_falsification.py` | 10/10, 1 limite déclarée | **identique** |
| `tools/med_demo_build.py` | reproduit `a0d8a701…` | **identique** |

Aucune ligne `PASS` n'a été ajoutée, volontairement : les décomptes de 21 et
18 lignes sont cités par des documents figés, dont la page Evidence Journey
suspendue. Les contrôles nouveaux ne s'expriment qu'en cas d'échec.

---

## Les neuf réponses

### 1. Qu'est-ce que NeoMundi Evidence peut démontrer aujourd'hui ?

Trois choses, et pas une quatrième.

**Que les octets d'un dossier de preuve n'ont pas bougé.** Les empreintes des
membres sont recalculées sur les octets livrés, et la couverture est contrôlée
dans les deux sens : un membre non couvert est vu, une somme sans membre
aussi.

**Qu'un dossier altéré est refusé.** Dix altérations de contenu sur dix sont
détectées, et quinze archives hostiles sur quinze reçoivent un verdict — dont
treize un refus.

**Qu'un fichier offert est bien celui auquel un enregistrement se réfère.**
C'est l'apport de cette mission : ses octets se hachent sur une empreinte que
l'enregistrement déclare, et cet enregistrement est chaîné.

### 2. Que peut-il vérifier automatiquement ?

Sans intervention, hors ligne, sans dépendance : **21 contrôles** sur une
archive GROUNDED-S1, **18** sur MED, **11 à 13** sur une liaison.

Chaque contrôle rend `PASS`, `FAIL` ou `NOT TESTED`, et les trois restent
distincts. Un `NOT TESTED` porte toujours sa raison. Depuis cette mission,
une entrée malformée rend un `FAIL` motivé au lieu d'une trace d'appels — ce
qui compte parce qu'un code de sortie 1 sans verdict était indistinguable
d'un refus légitime.

Les deux vérificateurs écrivent aussi un rapport JSON, pour qu'un tiers
n'ait pas à analyser des chaînes françaises.

### 3. Peut-il distinguer un récit d'exécution d'une preuve vérifiable ? Dans quelles limites ?

**Oui, et c'est démontré par un test dédié.** Deux manifestes portant une
prose identique mot pour mot :

```
  Scénario A : 1 énoncé, 0 artefact  → declared
  Scénario B : 1 énoncé, 2 artefacts → reference_verifiable
```

Le scénario A n'est ni refusé ni accepté : il est rendu pour ce qu'il est, un
document déclaratif. Les énoncés attachés à un manifeste sont **toujours**
`NOT TESTED`, avec la mention explicite qu'une description textuelle d'une
exécution ne constitue pas une preuve que cette exécution a eu lieu.

**Les limites.** La distinction porte sur la présence d'un ancrage
recalculable, pas sur la véracité du récit. Un récit **exact** sans artefact
reste `declared` ; un récit **faux** accompagné d'artefacts ancrés obtient
`reference_verifiable` pour ses artefacts — l'outil ne lit pas la prose et ne
la contredit pas. Il refuse seulement qu'elle compte comme preuve.

### 4. Peut-il associer une observation NeoMundi à des artefacts externes sans modifier l'API ?

**Oui, et sans que l'API ait eu à changer d'un octet.**

L'ancrage existait déjà : un enregistrement d'observation déclare
`response_sha256`, `prompt_sha256`, `request_sha256` — les empreintes d'objets
qui ne sont pas dans l'archive. L'enregistrement de provenance ajoute
`recording_sha256` et `bundle_sha256`. Six points d'ancrage, tous déjà
publiés par la Station.

La liaison s'y accroche sans rien demander à personne. Vérifié sur une
observation réelle : les deux artefacts offerts se hachent sur deux de ces six
empreintes.

Un détail de conception compte plus qu'il n'y paraît : le manifeste recopie
les empreintes déclarées, et le vérificateur **les confronte à
l'enregistrement** au lieu de les croire. C'est le seul contrôle qui attrape
un faussaire ayant refait l'artefact *et* le manifeste de concert.

### 5. Peut-il récupérer et vérifier les artefacts ?

**Localement, oui. À distance, non — et ce n'est pas un manque, c'est un
choix.**

Les artefacts sont des fichiers sous une racine explicite. Quatre refus :
chemin absolu, traversée de répertoire, lien symbolique sortant, et taille
au-delà du plafond de lecture (64 Mio par défaut, modifiable).

**Aucune URL n'est jamais résolue, et aucun réseau n'est touché.** Un
vérificateur qui irait chercher ce qu'un document lui indique deviendrait un
instrument d'exfiltration ; les deux outils n'importent que la bibliothèque
standard, et ne contiennent aucune primitive réseau.

Un artefact absent rend `NOT TESTED`, pas `FAIL` : sa revendication n'a pas
été contredite, elle n'a pas été éprouvée. La liaison retombe alors au niveau
`declared`, et le rapport dit que la **vérification** est incomplète — pas que
le manifeste est faux.

### 6. Peut-il reconstruire ou rejouer une exécution ?

**Non. Et l'étude dit lesquels des trois sens sont atteignables.**

| | Verdict |
|---|---|
| Rejeu des **entrées** | **GO** — déjà fait, et les empreintes d'entrée se vérifient |
| Rejeu de la **mesure**, résultat identique | **NO-GO** |
| Rejeu de la mesure, résultat **comparable** | **GO conditionnel**, à cinq conditions |
| Reproduction **à l'octet** du registre | **NO-GO permanent**, à ne jamais annoncer |

Le blocage n'est pas un défaut à corriger. Sur ce lot, `semantic_instability_score`
est **null dans 22 mesures sur 30**, et 15 mesures seulement sont `measured`
contre 8 `degraded` et 7 `not_measured`. Un rejeu fidèle devrait reproduire
**ces absences**, qui ne sont pas une propriété de l'entrée mais la trace de
ce qui était joignable à l'instant de la mesure.

S'ajoute que ce lot est en régime `synthetic` : réussir à le rejouer ne dirait
rien d'une campagne réelle.

### 7. Quelles garanties peut-on raisonnablement présenter à une entreprise ?

Quatre phrases, chacune adossée à une exécution constatée.

> **L'intégrité d'un dossier de preuve est vérifiable par vous-même, hors
> ligne, sans rien installer.** Un fichier Python de la bibliothèque standard,
> 21 contrôles, et trois états qui ne se confondent pas.

> **Une altération est détectée.** Dix altérations sur dix, et quinze archives
> hostiles sur quinze reçoivent un verdict.

> **Un fichier que nous vous remettons peut être rattaché à l'enregistrement
> qui le mentionne**, par recalcul d'empreinte, sans nous faire confiance et
> sans toucher à notre API.

> **Ce que nous ne savons pas faire est écrit**, dans l'outil et dans sa
> sortie, à chaque exécution.

### 8. Quelles garanties ne doit-on surtout pas revendiquer ?

Sept, et les trois premières sont celles qui tenteraient le plus.

1. **« Preuve que l'exécution a eu lieu. »** Jamais. Lier un artefact à un
   enregistrement ne dit ni que l'exécution a eu lieu, ni quand, ni chez qui.
2. **« Authenticité »** ou **« signé »**. Aucune signature n'est vérifiée.
   `cryptographically_attested` est déclarable et **jamais** dérivable — un
   manifeste qui le revendique est refusé.
3. **« Reproductible »** au sens du calcul. Le gel garantit les entrées, pas
   que la mesure se refasse à l'identique.
4. **« Horodatage certifié. »** Aucune horloge de confiance. `created_at`,
   `exporte_le` et `recorded_at` sont déclarés et contredits par rien — une
   date dans le futur passe, et c'est une limite assumée.
5. **« Chaînage vérifié par l'outil. »** `verify.py` le laisse `NOT TESTED`
   par conception : le recalculer ici serait une seconde implémentation du
   registre.
6. **« Validation médicale, juridique ou factuelle. »** Une mesure est une
   mesure. La démonstration B porte sur un corpus médical et ne valide aucune
   réponse médicale.
7. **« Archive infalsifiable. »** Un faussaire qui reconstruit l'archive
   entière produit un dossier cohérent. Seule une empreinte conservée
   **ailleurs qu'avec elle** le détecte.

### 9. Quelles sont les prochaines améliorations réellement prioritaires ?

Par ordre de valeur de preuve gagnée, pas de facilité.

**P0 — signer, et ancrer dehors.** C'est le seul chantier qui débloque un
niveau de garantie entier. Aujourd'hui `cryptographically_attested` existe
dans l'échelle et n'est jamais atteignable ; signer le manifeste avec une clé
identifiée, et ancrer l'empreinte hors de l'archive, fermerait d'un coup les
constats A-03 et le trou central de l'audit. Tout le reste est secondaire
devant ça.

**P1 — le harnais de rejeu hors production.** Sur l'Ollama du poste, à coût
nul, avec un budget de divergence déclaré d'avance et la couverture comparée
avant les valeurs. C'est l'étape 1 de l'étude de faisabilité, et la seule qui
ne demande aucune autorisation.

**P1 — traduire la sortie des vérificateurs.** Elle est en français ; la
documentation est bilingue. Un auditeur étranger lit aujourd'hui des
chaînes qu'il ne comprend pas. Le rapport JSON atténue, il ne remplace pas.

**P2 — instruire A-05 dans le dépôt du tableau de bord.** La divergence
d'indicateurs rapportée par un pilote (`g_score` 0,3863 contre 0,594, et
l'inversion des libellés stabilité/énergie) n'appartient pas à ce dépôt et
n'a pu être reproduite ici. Le paquet de preuves annoncé n'a pas été fourni.

**P2 — les deux limites assumées de la sonde contradictoire :** l'archive
imbriquée, jamais extraite, et l'horodatage futur, que rien ne contredit. Les
lever demande respectivement une politique d'extraction et une horloge de
confiance — donc le chantier P0.

---

## Ce que cette mission a corrigé, et comment c'est apparu

Quatre défauts, et **aucun n'a été trouvé en relisant le code.**

**Le vérificateur plantait sur sept entrées malformées sur neuf.** Trouvé en
fabriquant des archives hostiles. Les tests de falsification existants ne
pouvaient pas le voir : ils n'altèrent que du contenu bien formé. Un
vérificateur reçoit par définition des archives dont on ne sait pas si elles
sont saines, et le plantage y est le pire des échecs — code de sortie 1 sans
verdict, indistinguable d'un refus légitime.

**Les sept retours anticipés de `main` sautaient le `BILAN`.** Trouvé parce que
ma propre sonde comptait les « plantages » par l'absence de ligne `BILAN` et
en signalait deux qui n'en étaient pas.

**Un artefact absent rendait `FAIL`.** Trouvé par mon propre test négatif, qui
attendait une dégradation et obtenait un refus. Un fichier non fourni ne
contredit pas sa revendication : il empêche de l'éprouver. Confondre les deux
fusionnait des états que ce produit garde séparés.

**Un `PASS` sur « aucune revendication ne dépasse » alors que zéro
revendication avait été éprouvée.** Trouvé en lisant une sortie réelle, pas le
code. C'était un succès inventé sur un échantillon vide.

Et une erreur de ma part, prise par les archives elles-mêmes : j'avais supposé
`fichiers` de type table dans le manifeste, alors que c'est une **liste**. Le
contrôle neuf faisait échouer les deux archives valides, et les lignes de base
l'ont montré immédiatement.

---

## État de la livraison

| | |
|---|---|
| Branche | `feat/evidence-observation-binding-v1` |
| Partie de | `a658af2bbacc9f3d34daee5829498be342b87a54` |
| Commits | 2 — `c22dfb3` (audit et robustesse), `1a07287` (liaison) |
| `main` | **non touché** |
| Fusion | **non faite**, et à ne pas faire sans revue |
| Déploiement | **aucun** |
| Contrôle anti-fuite | passé : aucune clé, aucun chemin de machine, aucun nom de tiers, aucune correspondance privée |

### Ce qui reste ouvert, et ne relève pas de cette mission

- La démonstration de cinq minutes n'a pas été **rechronométrée** dans cette
  mission : `demo_binding.sh` s'ajoute sans la remplacer.
- Le paquet de preuves annoncé par un pilote n'a **pas été fourni**, donc rien
  n'en a été vérifié. Aucun de ses résultats n'a été reconstitué.
- La préservation des journaux SEILX reste **non exécutée** : les scripts
  existent, l'accès a été bloqué, et l'échéance du 10 novembre tient.

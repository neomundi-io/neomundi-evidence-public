<div align="center">

<sub>🇬🇧 <a href="README.md">English</a> · 🇫🇷 <b>Français</b></sub>

[Station — Observer & Expérimenter](https://github.com/neomundi-io/neomundi-station-public) ·
[Runtime Measurement — Mesurer & Intégrer](https://github.com/neomundi-io/neomundi-runtime-measurement) ·
**[Evidence — Vérifier & Reconstruire](README.fr.md)** ·
[Cas d'usage — Applications, pilotes & preuves](https://github.com/neomundi-io/neomundi-use-cases) ·
[ControlTower — Créer un compte](https://controltower.neomundi.io/welcome)

<sub>[Organisation GitHub NeoMundi](https://github.com/neomundi-io)</sub>

# NeoMundi Evidence

### Enregistrer ce qui s'est passé. Vérifier ce qui peut être prouvé.

**Un dossier de preuve pour une campagne de qualification d'IA instrumentée —
exportable, lisible, et contrôlable par son destinataire sans nous.**

[![Evidence : V0.1](https://img.shields.io/badge/Evidence-V0.1-475569?style=flat-square)](#ce-que-contient-un-dossier-de-preuve)
[![tests](https://github.com/neomundi-io/neomundi-evidence-public/actions/workflows/tests.yml/badge.svg)](https://github.com/neomundi-io/neomundi-evidence-public/actions/workflows/tests.yml)
[![Vérification indépendante](https://img.shields.io/badge/V%C3%A9rification_ind%C3%A9pendante-sans_d%C3%A9pendance-0f766e?style=flat-square)](#vérifier-un-dossier-de-preuve)
[![Intégrité : SHA-256](https://img.shields.io/badge/Int%C3%A9grit%C3%A9-SHA--256-0f766e?style=flat-square)](docs/EXTERNAL_REFERENCE.fr.md)
[![Falsification : 10/10 testées](https://img.shields.io/badge/Falsification-10%2F10_test%C3%A9es-0f766e?style=flat-square)](#tests-de-falsification)
[![Vérification : bibliothèque standard](https://img.shields.io/badge/V%C3%A9rification-biblioth%C3%A8que_standard-0f766e?style=flat-square)](verify.py)
[![Démonstrations : 2](https://img.shields.io/badge/D%C3%A9monstrations-synth%C3%A9tique_%2B_m%C3%A9dicale-2563eb?style=flat-square)](#les-deux-démonstrations)
[![Statut : candidate pour revue externe](https://img.shields.io/badge/Statut-candidate_revue_externe-a16207?style=flat-square)](#les-quatre-catégories)
[![Licence : tous droits réservés](https://img.shields.io/badge/Licence-tous_droits_r%C3%A9serv%C3%A9s-6b7280?style=flat-square)](#licence)

**[Vérifier un dossier de preuve](#vérifier-un-dossier-de-preuve)** ·
[Démonstration A — synthétique](docs/DEMO.fr.md) ·
[Démonstration B — médicale](docs/MED_DEMO.fr.md) ·
[Démo de cinq minutes](docs/DEMO_SCRIPT_5MIN.fr.md) ·
[Reproduire la démo](docs/DEMO.fr.md) ·
[Référence des corpus](docs/CORPUS_REFERENCE.fr.md) ·
[Référence externe](docs/EXTERNAL_REFERENCE.fr.md) ·
[Limites](#limites) ·
[Site futur](docs/FUTURE_SITE.fr.md)

<sub>Commencer par <b>verify.py</b> : un fichier, bibliothèque standard seule,
aucun appel réseau, rien à installer. Il est fait pour être <b>lu</b> avant
d'être exécuté — c'est la condition d'une vérification indépendante.</sub>

</div>

---

## Les limites d'abord

Elles viennent en premier parce qu'un produit de preuve qui annonce ses
fonctions avant ses limites est une plaquette, pas un instrument.

| Ce dossier **ne** prouve **pas** | Pourquoi |
|---|---|
| l'origine d'une archive | aucune signature tierce, aucun ancrage extérieur |
| l'heure d'un événement | `recorded_at` est **fourni par l'appelant** ; le registre atteste ce qu'on lui a déclaré |
| qu'une chaîne n'a pas été réécrite en entier | une chaîne intégralement refaite se vérifie parfaitement ; seule une empreinte conservée ailleurs le détecte |
| la justesse des signaux mesurés | l'existence d'un score ne fonde pas sa validité |
| ce qu'a fait une IA en production | la V0.1 porte sur des **campagnes**, jamais sur le trafic client d'une API |
| une conformité réglementaire | aucune certification, aucune admissibilité juridique revendiquée |

**Une empreinte SHA-256 n'est pas une preuve de vérité.** Elle établit qu'un
fichier reçu est celui dont on a reçu l'empreinte. Rien de plus.

---

## Les quatre catégories

Chaque élément de ce dépôt se range dans l'une d'elles, et n'est jamais présenté
comme appartenant à une autre.

| Catégorie | Ce que cela signifie | Ce qui s'y trouve |
|---|---|---|
| **DÉMONTRÉ** | exécuté, mesuré, avec une sortie à montrer | la production d'un dossier · la vérification autonome · les dix détections de falsification · les corpus gelés · la démo chronométrée |
| **EXPÉRIMENTAL** | cela fonctionne, mais sur peu de cas, ou sans recul suffisant pour s'y fier | l'archive enrichie (schéma d'export `/2`, quelques jours d'existence, une campagne exportée) · la garde de régime d'exécution · la redérivation des empreintes d'entrée (un seul corpus) |
| **LIMITES** | connu, énoncé, non corrigeable à ce stade | l'origine et l'horodatage · le chaînage non revalidé par notre vérificateur · l'archive entièrement réécrite · un registre non reproductible à l'octet |
| **PRÉVU** | envisagé, non engagé, conditionné à une demande | l'ancrage extérieur · la signature · la conservation contractuelle · un espace de vérification dans le navigateur · l'instrumentation du trafic réel |

**Dans aucune des quatre :** une certification, une garantie d'exhaustivité, une
valeur probante juridiquement reconnue. Ce ne sont pas des fonctions à
planifier — ce sont des promesses que nous ne tiendrions pas.

---

## Les deux démonstrations

Deux corpus, deux objets. Aucun ne remplace l'autre.

| | **A — GROUNDED-S1** | **B — MED** |
|---|---|---|
| Nature | synthétique, fabriqué pour le banc | une expérimentation médicale indépendante |
| Ce qu'elle montre | le comportement contrôlé du vérificateur : absences de mesure, et **10 falsifications sur 10 détectées** | la traçabilité sectorielle : un item de question réel, un modèle réel, une réponse réelle, des signaux réels |
| Régime d'exécution | `synthetic` — n'observe aucun opérateur réel | `live` — sept fournisseurs nommés |
| Mesures | 15 `measured`, 8 `degraded`, **7 `not_measured`** | 208, toutes `measured` |
| Modèles nommés | non — elle n'observe rien de réel | **oui** — voir le tableau de la [démonstration B](docs/MED_DEMO.fr.md) |
| Vérification | **19 PASS, 0 FAIL, 2 NOT TESTED** | **10 PASS, 0 FAIL, 8 NOT TESTED** |
| Suite de falsification | **s'applique** — 10/10 détectées | ne s'applique pas, et dit pourquoi |
| Documentation | [Démonstration A](docs/DEMO.fr.md) | [Démonstration B](docs/MED_DEMO.fr.md) |

**Pourquoi les deux.** Un corpus synthétique peut porter des mesures qui n'ont
*pas* été faites — c'est ainsi que « une absence reste une absence » se
démontre au lieu de se promettre. Un corpus réel ne se fabrique pas sur
commande, et c'est le seul qui montre ce que l'instrument fait sur une vraie
question médicale répondue par un vrai modèle.

**Ce qu'aucune des deux ne démontre.** Qu'un signal mesuré soit juste. Qu'une
réponse soit médicalement correcte. Une mesure décrit des propriétés d'un
texte produit.

---

## Ce que contient un dossier de preuve

Schéma d'export `station.export.campagne/2`. Huit membres.

| Membre | Contenu |
|---|---|
| `observations.jsonl` | ce qui a été observé, en **octets d'origine** du registre |
| `observations.csv` | vue dérivée ; séparateur `;`, UTF-8 avec BOM, cellules à risque de formule neutralisées |
| `measurements.jsonl` | les mesures : signaux, couverture, état, version |
| `reference_evaluations.jsonl` | les évaluations de référence, et l'empreinte de la référence — jamais la référence |
| `replay_provenance.jsonl` | le régime d'exécution, et l'empreinte de chaque entrée rejouée |
| `manifest.json` | schéma, campagne, décomptes, régimes, **absences nommées**, gardes de lecture, limites |
| `rapport.md` | le document qu'un lecteur métier lit |
| `checksums.sha256` | l'empreinte de chaque membre |

### Comment les enregistrements se joignent

**`observation_id` est la seule clé de jointure.** Elle est requise sur les
quatre fichiers JSONL. `measurement_id` et `evaluation_id` ne doivent **pas**
servir de jointure : aucun schéma n'impose leur forme, et elle diffère d'un
corpus à l'autre.

### Ce qui est absent reste absent

Un signal non mesuré vaut `null`, jamais `0`. Une observation sans mesure est
**nommée** dans `manifest.json` et dans le rapport. Un coût non établi n'est pas
sommé. Et un `latency_ms` à `0` sur une observation en échec est rapporté comme
une durée **non établie** — un appel abandonné ne laisse aucune durée.

---

## Vérifier un dossier de preuve

```sh
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip
python verify.py <archive> --corpus <répertoire du corpus d'entrée>
python verify.py <archive> --json rapport.json     # lisible par machine, en plus
```

Bibliothèque standard seule. Aucune dépendance, aucun appel réseau, aucune
écriture.

Chaque contrôle rend `PASS`, `FAIL` ou `NOT TESTED`. Un contrôle hors de portée
rend `NOT TESTED` **avec sa raison** : aucun échec n'est jamais remplacé par une
valeur favorable.

> La sortie du vérificateur est en français. Seule la documentation est bilingue
> — traduire l'outil reviendrait à modifier un vérificateur validé, ce que cette
> version ne fait pas. C'est un élément **PRÉVU**.

### Ce que `verify.py` ne fait pas, volontairement

Il ne recalcule **pas** le chaînage du registre. Le refaire ici serait une
seconde implémentation des règles de chaînage : deux implémentations qui
divergent ne prouvent rien, et celle qui a produit l'archive resterait la
référence. Le chaînage se vérifie avec l'instrument qui l'a écrit.

### Résultats constatés le 5 novembre 2026

Sur l'archive de démonstration, produite depuis le corpus gelé `GROUNDED-S1` :

```
BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED
```

Les deux `NOT TESTED` sont le chaînage JCS et l'origine de l'archive — les deux
contrôles qu'aucune vérification locale ne peut faire.

---

## Lier une observation à ses preuves

Un enregistrement déclare les empreintes d'objets qui ne sont **pas dans
l'archive** : la réponse, le prompt, la requête. Lier, c'est produire un
fichier dont les octets se hachent sur l'une de ces empreintes.

```sh
python bind.py build --archive <archive> --observation obs-... \
                     --artifact response=reponse.txt \
                     --created-at 2026-11-05T12:00:00Z --out manifest.json
python bind.py verify manifest.json --archive <archive>
```

Quatre niveaux de garantie, et **le niveau est dérivé par le vérificateur,
jamais lu dans le manifeste** :

| Niveau | Disponible aujourd'hui |
|---|---|
| `declared` | oui |
| `reference_verifiable` | **oui** |
| `cryptographically_attested` | **non** — rien ici ne vérifie une signature |
| `not_demonstrable` | un constat, pas un acquis |

Un manifeste qui se revendique mieux qu'il ne l'est est refusé. Deux
manifestes portant une prose identique mot pour mot, l'un ancré et l'autre
non, reçoivent des verdicts différents — parce qu'**une description textuelle
d'une exécution ne constitue pas une preuve que cette exécution a eu lieu**.

Voir [Liaison](docs/BINDING.fr.md) · `sh demo_binding.sh <archive>`

---

## Tests de falsification

```sh
python tests/test_falsification.py <archive> <corpus>
```

**10 altérations sur 10 détectées**, et **une limite déclarée** :

| Altération | Détectée |
|---|---|
| un octet changé dans une mesure | oui |
| une mesure retirée, sommes recalculées | oui |
| un signal `null` déclaré mesuré | oui |
| une mesure rattachée à une observation inexistante | oui |
| une absence déclarée qui n'existe pas | oui |
| la garde de régime retirée du manifeste | oui |
| un secret injecté dans le rapport | oui |
| une formule injectée dans le CSV | oui |
| un membre qui sort du répertoire cible | oui |
| le manifeste retiré | oui |
| **une observation effacée partout, décomptes et sommes refaits** | **non — voir ci-dessous** |

La dernière est la limite qui compte. Qui retire une observation **et** sa
mesure **et** son évaluation **et** sa provenance, puis corrige chaque décompte
et recalcule chaque empreinte, produit une archive où plus rien ne se
contredit. Aucun contrôle interne ne peut le voir.

**La seule défense est l'empreinte de l'archive, conservée ailleurs qu'avec
l'archive.** Transmettre l'archive et sa somme par le même canal ne prouve
rien : qui peut remplacer l'une peut remplacer l'autre. Voir la
[référence externe](docs/EXTERNAL_REFERENCE.fr.md).

---

## Le corpus de référence

La démonstration porte sur **GROUNDED-S1**, corpus **synthétique**, gelé et
vérifié — voir la [référence des corpus](docs/CORPUS_REFERENCE.fr.md).

Son régime d'exécution est `synthetic` : ces réponses ont été **fabriquées pour
le banc** et n'observent aucun opérateur réel. Elles établissent que la chaîne
fonctionne, et rien du monde extérieur. L'archive porte cette garde en clair,
dans son manifeste et dans son rapport.

C'est aussi le seul corpus qui porte des **mesures non faites** — 15 `measured`,
8 `degraded`, 7 `not_measured`. Un produit qui promet « une absence reste une
absence » a besoin d'absences pour le démontrer.

Le second corpus, **MED**, est une expérimentation réelle sur sept fournisseurs
nommés, et il est publié comme [démonstration B](docs/MED_DEMO.fr.md). Ce qui
n'est **pas** publié, c'est le contenu propre du jeu de données : son statut de
licence est contradictoire à la source, donc ni énoncé, ni choix, ni étiquette
de référence ne sont redistribués. Les `item_id` le sont à la place, pour qu'une
question se résolve chez l'éditeur du jeu de données.

---

## Documentation

| | |
|---|---|
| [`docs/DEMO_SCRIPT_5MIN.fr.md`](docs/DEMO_SCRIPT_5MIN.fr.md) | la démo de cinq minutes, avec les durées mesurées |
| [`docs/DEMO.fr.md`](docs/DEMO.fr.md) | reproduire la démonstration |
| [`docs/CORPUS_REFERENCE.fr.md`](docs/CORPUS_REFERENCE.fr.md) | les corpus, leurs empreintes, et comment un auditeur les vérifie |
| [`docs/EXTERNAL_REFERENCE.fr.md`](docs/EXTERNAL_REFERENCE.fr.md) | vérifier depuis une empreinte conservée indépendamment — et pourquoi une empreinte interne n'atteste rien |
| [`docs/MED_DEMO.fr.md`](docs/MED_DEMO.fr.md) | Démonstration B — l'expérimentation médicale, son jeu de données, ses modèles et ses limites |
| [`docs/TIMESTAMPING.fr.md`](docs/TIMESTAMPING.fr.md) | horodatage indépendant par OpenTimestamps : ce qu'il prouve, et pourquoi `PENDING` ne prouve aucune date |
| [`docs/INTEGRATION.fr.md`](docs/INTEGRATION.fr.md) | intégrer Evidence : codes de sortie, `--strict`, rapports JSON, et CI |
| [`docs/V1_QUALIFICATION.fr.md`](docs/V1_QUALIFICATION.fr.md) | le sprint de qualification : les huit conditions, et deux verdicts GO/NO-GO distincts |
| [`docs/SIGNING_POLICY.fr.md`](docs/SIGNING_POLICY.fr.md) | qui s'engage, et la garde de la clé : les cinq rôles, et pourquoi `compromised` invalide le passé |
| [`docs/ADR-001-ANCHORING.fr.md`](docs/ADR-001-ANCHORING.fr.md) | ADR-001 : les quatre prétentions temporelles, et pourquoi une hauteur de bloc n'est pas une date |
| [`docs/TRUST_STORE_PUBLICATION.fr.md`](docs/TRUST_STORE_PUBLICATION.fr.md) | publier le magasin de confiance sur un second canal — conception, et l'audit de contenu qui la verrouille |
| [`docs/I18N.fr.md`](docs/I18N.fr.md) | sortie bilingue : ce que `--lang` traduit, ce qu'il ne touche jamais, et comment la couverture est mesurée |
| [`docs/V1_CANDIDATE.fr.md`](docs/V1_CANDIDATE.fr.md) | la fiche produit de la candidate V1 : garanties démontrées, en attente, et non validées |
| [`docs/V1_REVIEW_PROTOCOL.fr.md`](docs/V1_REVIEW_PROTOCOL.fr.md) | le protocole de revue externe, un périmètre par relecteur |
| [`docs/ATTESTATION.fr.md`](docs/ATTESTATION.fr.md) | l'attestation signée : comment `cryptographically_attested` est atteint, et la matrice de 23 cas |
| [`docs/RECONCILIATION.fr.md`](docs/RECONCILIATION.fr.md) | réconcilier un reçu externe avec une mesure NeoMundi : cinq statuts, et pourquoi la comparabilité passe d'abord |
| [`docs/CP8_ADAPTER_SPEC.fr.md`](docs/CP8_ADAPTER_SPEC.fr.md) | adaptateur de reçu externe — spécification seule, aucun code |
| [`docs/BINDING.fr.md`](docs/BINDING.fr.md) | lier une observation à ses preuves, les quatre niveaux de garantie, et la terminologie |
| [`docs/REPLAY_FEASIBILITY.fr.md`](docs/REPLAY_FEASIBILITY.fr.md) | peut-on rejouer une mesure ? GO / NO-GO, et les blocages |
| [`docs/AUDIT_CONTRADICTOIRE_EVIDENCE_2026-11-05.md`](docs/AUDIT_CONTRADICTOIRE_EVIDENCE_2026-11-05.md) | l'audit contradictoire du 5 novembre : 18 capacités, ce que chacune fait réellement |
| [`docs/EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.fr.md`](docs/EVIDENCE_CONSOLIDATION_REPORT_2026-11-05.fr.md) | la consolidation du 5 novembre : ce qui a changé, et les neuf réponses |
| [`docs/FUTURE_SITE.fr.md`](docs/FUTURE_SITE.fr.md) | l'architecture prévue du site produit — non construit, non déployé |

Chaque document existe en anglais et en français (`*.fr.md`).

---

## Limites

Au-delà du tableau en tête de ce fichier :

- **Reproductibilité.** « Reproductible » signifie ici *mêmes entrées, même
  contenu d'observations et de mesures, chaîne valide*. Jamais *même empreinte*.
  Un registre n'est pas reproductible à l'octet, même synthétique :
  `recorded_at` est lu à l'horloge et les empreintes de chaînage en dépendent.
  L'empreinte d'une archive change à chaque export, parce que le manifeste porte
  l'horodatage — six des huit membres sont identiques à l'octet entre deux
  exports.
- **Aucun ancrage extérieur.** Aucune signature, aucun horodatage tiers.
- **La sortie du vérificateur est en français seulement.** La documentation est
  bilingue ; l'outil non.
- **Une seule campagne exportée.** L'archive enrichie est EXPÉRIMENTALE pour
  cette raison, pas parce qu'un contrôle a échoué.

---

## Sécurité

N'ouvrez pas d'issue publique pour une vulnérabilité. Écrivez à
**[contact@neomundi.io](mailto:contact@neomundi.io)** avec ce que vous avez
observé et comment le reproduire. Ne joignez **aucune clé réelle**, même la
vôtre.

Ce que nous considérons comme une vulnérabilité ici : un chemin qui ferait
passer une archive altérée à la vérification ; une fuite de secret ou de chemin
personnel dans une archive exportée ; un contrôle qui rendrait `PASS` là où il
ne peut pas conclure.

---

## Licence

**Aucune licence n'est déclarée sur ce dépôt, et c'est une décision, pas un
oubli.**

Un dépôt public sans fichier de licence est en **tous droits réservés** par
défaut : vous pouvez le lire et en discuter, et aucun droit de copie, de
modification ou de redistribution n'est accordé. Concrètement, aujourd'hui :
lire et discuter — oui ; réutiliser dans un autre projet, redistribuer, ou
produire une œuvre dérivée — non.

Choisir une licence est une décision encore à prendre, et elle n'appartient pas
à ce fichier.

**Les jeux de données gardent leurs propres licences**, déclarées à leur import
et portées par leurs manifestes — et **aucun contenu de jeu de données tiers
n'est publié ici.** Aucun corpus, aucun registre, aucune archive ne se trouve
dans ce dépôt : seulement le vérificateur, les tests et la documentation.

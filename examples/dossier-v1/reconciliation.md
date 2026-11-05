# Rapport de reconciliation

> Un recu externe est une **declaration**. Notre archive est une **preuve
> primaire** dans la mesure ou nous en recalculons les empreintes. Ce
> rapport les confronte et **conserve les deux cotes** : il ne tranche rien.

| | |
|---|---|
| Recu | `receipt-synthetic.html` |
| Empreinte du recu | `36e634bc758ea9dc1910ea2c9290713d859e2450729c77aa8895d371e3a3f80b` |
| Recu le (declare par nous) | 2026-11-06T09:10:00Z |
| Archive | `NEOMUNDI_EVIDENCE_V1_DEMO.zip` |
| Voie de liaison | **EMPREINTE** |
| Observation liee | `obs-06ada57c26aa5cf429e9f2c0a99e3e4a42daecd45fc4c955d7c1399ab4227ae8` |

**Liaison :** une empreinte du recu egale une empreinte que l enregistrement declare : 5ebf9582f2aed6ea...

## Champ par champ

| Statut | Nature | Etiquette du recu | Champ NeoMundi | Valeur du recu | Notre valeur |
|---|---|---|---|---|---|
| **MATCHED** | measured_value | `latence observee (ms)` | `latency_ms` | `100` | `100` |
| **MISMATCHED** | measured_value | `score de coherence` | `coherence_score` | `0,3863` | `0.5` |
| **MATCHED** | identifier | `modele declare` | `model_requested` | `ci-fixture-v1` | `ci-fixture-v1` |
| **MATCHED** | identifier | `item` | `item_id` | `fixture-item-a` | `fixture-item-a` |
| **MATCHED** | digest | `empreinte de la reponse` | `response_sha256` | `5ebf9582f2aed6ea16c5cef8c67f01b4b6746cd12554f3e36f43b603ab36ee4c` | `5ebf9582f2aed6ea16c5cef8c67f01b4b6746cd12554f3e36f43b603ab36ee4c` |
| **NOT VERIFIABLE** | digest | `empreinte du journal d execution 1` | `record_sha256` | `1111111111111111111111111111111111111111111111111111111111111111` | `983a7ac49e622ed74185384f116d971cc74a9e3f03a48db3dcb966dbca16f554` |
| **NOT COMPARABLE** | statement | `resultat declare` | `status` | `concordant` | `measured` |
| **MISMATCHED** | measured_value | `score de stabilite declare` | `stability_score` | `0,594` | `0.5` |
| **MISSING** | ? | `empreinte du prompt` | `prompt_sha256` | `None` | `c5624e7688061c87b5cc059290e1678d919379eb489d836119ce942e4110ca24` |

## Contradictions conservees

**Aucune n est tranchee.** Les deux valeurs figurent telles quelles.

- `score de coherence` : recu **0,3863**, nous **0.5** — *MISMATCHED*
- `resultat declare` : recu **concordant**, nous **measured** — *NOT COMPARABLE*
- `score de stabilite declare` : recu **0,594**, nous **0.5** — *MISMATCHED*

## Classes de preuve

**Preuve primaire** — 
- les empreintes de notre archive, que nous recalculons

**Declaration externe** — 
- tout champ du recu : valeur, statut, identifiant
- toute signature annoncee et non verifiee

**Conclusion verifiee** — aucune

## Limites

- Un recu externe est une DECLARATION. Rien ici ne le transforme en preuve verifiee.
- Aucune divergence n est tranchee : les deux valeurs sont conservees.
- Aucune signature n a ete verifiee ; le recu n est pas qualifie de signe.
- Aucune correspondance n est devinee : sans entree dans la table, un champ est NOT COMPARABLE.

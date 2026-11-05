<sub>🇬🇧 <a href="CP8_ADAPTER_SPEC.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Adaptateur de reçu externe — spécification

**Spécification seule. Aucun code n'est écrit, et rien n'est intégré au
moteur cryptographique d'Evidence.**

Cas d'origine : un reçu de validation « CP8 » transmis par un pilote externe
au sujet de CVE-2026-112244. Nous disposons d'un **document HTML** ; le
rapport complet `RECONCILIATION.md` est attendu et **n'a pas été reçu**.

---

## Pourquoi un adaptateur, et pas une intégration

Un reçu externe est une **déclaration d'un tiers**. L'intégrer au moteur
d'attestation reviendrait à lui accorder le statut des objets que nous
signons nous-mêmes, ce qui est précisément la confusion que ce produit
refuse.

L'adaptateur reste donc **en périphérie** : il importe, il qualifie, il
réconcilie — et il ne modifie ni `verify.py`, ni `verify_attestation.py`, ni
le magasin de confiance, ni les quatre niveaux de garantie.

---

## Les trois statuts, à ne jamais fusionner

C'est le cœur de la spécification. Tout champ importé reçoit exactement un
de ces statuts, et le rapport les tient séparés.

| Statut | Signifie | Exemple sur ce cas |
|---|---|---|
| **Preuve primaire** | un objet dont nous recalculons nous-mêmes l'empreinte ou la signature | une archive Evidence attestée, un `record_sha256` recalculé |
| **Déclaration externe** | un fait affirmé par le tiers, que nous n'avons pas pu recalculer | « deux exécutions indépendantes sur des fixtures locales » |
| **Conclusion vérifiée** | un énoncé que nous avons établi en confrontant une déclaration à une preuve primaire | « le `g_score` du reçu diffère de celui de la mesure NeoMundi `X` » |

**Un reçu HTML n'est pas une preuve primaire.** Il ne le devient pas en
portant un « hash de reçu » : un condensé calculé par l'émetteur et publié
par l'émetteur n'atteste rien de plus que sa propre cohérence interne.

> **Interdiction explicite :** ne jamais qualifier ce reçu HTML de
> « cryptographiquement signé ». Aucune signature n'a été produite, aucune
> clé n'a été fournie, et aucune vérification n'a été faite. Tant qu'une
> signature et une clé publique ne sont pas reçues et vérifiées, le reçu
> reste une **déclaration externe**.

---

## Les six étapes de l'adaptateur

### 1. Importer

Entrée : le document du tiers, tel que reçu, **sans retouche**.

- empreinte SHA-256 du fichier reçu, calculée par nous et conservée ;
- date et canal de réception, **déclarés par nous** et marqués comme tels ;
- aucune normalisation du contenu : un reçu reformaté n'est plus le reçu
  reçu.

Un extracteur lit le HTML et produit un **objet de champs**, où chaque champ
porte son chemin d'origine dans le document. Un champ dont le chemin ne
résout pas est `absent`, jamais `null` — la distinction est la même que pour
un signal non mesuré.

### 2. Vérifier ce qui est vérifiable

| Élément annoncé par le reçu | Ce que l'adaptateur en fait |
|---|---|
| un hash de reçu | recalculé sur les octets reçus → **PASS / FAIL** |
| des empreintes de journaux | recalculables **seulement si les journaux sont fournis** ; sinon `NOT TESTED` |
| une signature | `NOT TESTED` tant qu'aucune clé publique n'est reçue ; vérifiable ensuite par le même chemin Ed25519/JWS que nos attestations |
| « deux exécutions indépendantes » | **jamais vérifiable** depuis un document : `NOT TESTED`, définitivement |
| un résultat concordant | `NOT TESTED` : la concordance interne d'un tiers n'est pas notre mesure |

Règle : **aucun `PASS` sur un ensemble vide.** Un reçu dont rien n'est
recalculable rend un rapport entièrement `NOT TESTED`, et ce rapport est un
résultat valide — pas un échec.

### 3. Dire ses limites

L'adaptateur produit, pour chaque reçu, une liste explicite de ce qu'il n'a
pas pu établir. Sur le cas présent, telle qu'elle se présente aujourd'hui :

- le rapport `RECONCILIATION.md` **n'a pas été fourni** ;
- aucune clé publique n'accompagne le reçu ;
- les journaux dont les empreintes sont annoncées **ne sont pas joints** ;
- les fixtures locales des deux exécutions ne sont pas jointes ;
- rien ne relie encore le reçu à un `request_id` ou à une observation de
  notre côté.

### 4. Relier à une mesure NeoMundi — et seulement par une concordance réelle

**La liaison ne se fait jamais par rapprochement de vraisemblance.** Trois
voies, par ordre de force décroissante :

| Voie | Ce qu'elle exige | Force |
|---|---|---|
| **par empreinte** | une empreinte du reçu égale une empreinte que notre enregistrement déclare (`response_sha256`, `prompt_sha256`, `request_sha256`) | **forte** — c'est le mécanisme de `bind.py`, réutilisé tel quel |
| **par identifiant** | un `request_id`, `observation_id` ou `measurement_id` présent des deux côtés et retrouvé dans notre corpus | moyenne — un identifiant est déclaratif |
| **aucune** | ni empreinte ni identifiant commun | **la liaison est refusée** |

Une proximité de date, de modèle ou de valeur **ne constitue pas une
liaison**. Un adaptateur qui relierait sur cette base fabriquerait la preuve
qu'il prétend vérifier.

> Rappel de contexte, à vérifier et non à supposer : un `401` de `/v1/govern`
> ne laisse **aucune trace** côté serveur, et `observation_id` n'a jamais
> existé dans nos réponses d'API. Si le reçu ne porte qu'un identifiant de ce
> genre, la voie « par identifiant » peut être structurellement impossible,
> et il faut le dire plutôt que de chercher plus longtemps.

### 5. Produire un tableau de réconciliation, champ par champ

Une ligne par champ, cinq colonnes, et aucune colonne « verdict global ».

| Champ | Valeur du reçu | Valeur NeoMundi | Statut | Fondement |
|---|---|---|---|---|
| `g_score` | `0.3863` | `0.594` | **DIVERGENT, préservé** | les deux valeurs sont conservées telles quelles |
| `cve` | `CVE-2026-112244` | *(à résoudre)* | déclaration externe | — |
| hash de reçu | *(déclaré)* | recalculé par nous | PASS / FAIL | octets reçus |
| empreintes de journaux | *(déclarées)* | — | NOT TESTED | journaux non fournis |
| « deux exécutions » | *(déclaré)* | — | NOT TESTED | non vérifiable depuis un document |

### 6. Préserver les divergences, sans en choisir une

**`0,3863` contre `0,594` reste une divergence à deux valeurs.**

L'adaptateur ne tranche pas, ne moyenne pas, n'arbitre pas, et ne marque pas
l'une « correcte ». Il enregistre les deux, leurs sources, et ce qui
manquerait pour trancher.

Ce qui manquerait, justement, est connu :

- le `request_id` de la mesure NeoMundi concernée ;
- la `measurement_version` de chaque côté — deux versions différentes
  franchissent une frontière de comparabilité, et les valeurs ne se comparent
  alors plus ;
- la **couverture de mesure** de chaque côté : deux mesures de couvertures
  différentes ne se comparent pas signal par signal.

> Une note interne établit par ailleurs que `stability_score` **n'est pas un
> signal** mais un agrégat (`G / 0,60`), et qu'un `energy_score` republie
> l'agrégat retenu. Une divergence de `g_score` peut donc venir d'un **écart
> de définition** et non d'un écart de calcul. L'adaptateur doit enregistrer
> la définition employée de chaque côté avant de qualifier l'écart.
>
> **Aucun calcul de G-score n'est modifié, ni recalculé, par cet
> adaptateur.**

---

## Ce que l'adaptateur ne fera jamais

- reconstituer artificiellement les résultats du tiers ;
- compléter un champ absent par une valeur plausible ;
- qualifier de « signé » ce dont la signature n'a pas été vérifiée ;
- élever un niveau de garantie sur la foi d'une déclaration externe ;
- trancher une divergence que les données ne tranchent pas ;
- modifier le moteur cryptographique, le magasin de confiance, ou les quatre
  niveaux.

---

## Interface proposée, et son isolement

```sh
# Aucun de ces programmes n existe : ceci est la specification.
python adapters/receipt_import.py <recu.html> --out recu.json --received-at <date>
python adapters/receipt_verify.py recu.json [--logs <repertoire>] [--public-key <jwk>]
python adapters/reconcile.py recu.json --archive <archive_evidence.zip> \
       --observation <observation_id> --out reconciliation.md
```

Trois programmes, un répertoire `adapters/` séparé, et **aucun import depuis
`verify_attestation.py` ni `sign.py`**. L'adaptateur peut lire `bind.py` pour
réutiliser la liaison par empreinte ; l'inverse est interdit.

Schémas à versionner le jour de l'implémentation :
`neomundi.evidence.external-receipt/1` et
`neomundi.evidence.reconciliation/1`.

---

## Préalables à l'implémentation

1. **Recevoir `RECONCILIATION.md`.** Sans lui, l'adaptateur serait conçu sur
   un seul document et une conjecture.
2. **Obtenir la clé publique** si une signature est revendiquée. Sans clé, la
   signature reste `NOT TESTED` pour toujours.
3. **Obtenir les journaux** dont les empreintes sont annoncées, sinon ces
   empreintes resteront déclaratives.
4. **Identifier la mesure NeoMundi concernée** par un `request_id` ou une
   empreinte. Sans cela, l'étape 4 refuse la liaison et le tableau de
   réconciliation n'a pas de colonne « NeoMundi ».

**Rien de tout cela n'est en notre pouvoir seul.** C'est pourquoi la
spécification est livrée avant le code : construire l'adaptateur maintenant
produirait un outil dont on ne pourrait pas éprouver la branche principale.

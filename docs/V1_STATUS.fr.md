<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="V1_STATUS.md">English</a> · <a href="../README.md">← README</a></sub>

# Suivi Evidence V1 — état au 6 novembre 2026

Remplace [`V1_CLOSURE_PLAN.fr.md`](V1_CLOSURE_PLAN.fr.md), qui reste un
**relevé daté** du matin du 6 novembre et n'est pas réécrit : réécrire une
observation datée falsifierait un enregistrement.

---

## Les huit conditions

| | Condition | État | Ce qui reste |
|---|---|---|---|
| **B-1** | Identité juridique du signataire | 🟢 **RÉSOLUE** | — décision de direction du 6 nov : NeoMundi Recherche, RNA W563015824, capacité `experimental`. Implémentée et testée |
| **B-2** | Une clé de production, et sa garde | 🟢 **décisions et outillage** · ⏳ **le geste** | les trois décisions sont prises, l'outillage est construit et éprouvé. **La clé n'est pas générée** : un geste hors ligne, sur le poste de l'opérateur |
| **B-3** | Éprouver la chaîne sur un dossier réel | 🟢 **RÉSOLUE**, limite nommée | la limite est le chaînon d'exploitation ci-dessous, pas un défaut de vérification |
| **C-4** | Une preuve d'horodatage confirmée | 🟢 **RÉSOLUE** | — blocs Bitcoin 974714/974715, preuve commitée, vérifiable hors ligne |
| **C-5** | Publier le magasin sur un second canal | 🟠 **PARTIELLE** | la barrière est construite et testée. Il manque **un magasin de production à auditer** — donc B-2 |
| **C-6** | Traduire la sortie des vérificateurs | 🟢 **RÉSOLUE** | — et la PR #12 a comblé un trou que la suite ne voyait pas : 44 chaînes de `sign.py` |
| **D-7** | Recevoir le dossier CP8 complet | 🟠 **PARTIELLE** | deux artefacts, attendus de Dennis. Hors de notre main |
| **D-8** | Ancrage tiers et son coût | 🟢 **RÉSOLUE** | — ADR-001 acceptée |

**Six résolues, deux partielles, aucune bloquée.** Au matin du 6 novembre :
trois résolues, quatre partielles, une bloquée.

## Les neuf recommandations ODA3

| | | |
|---|---|---|
| **R-1** · **R-2** | types exclus, et le contrôle qui les confronte | 🟢 — avec son plafond mesuré : attrape une amputation *incohérente*, pas un faussaire méticuleux |
| **R-3** | réconcilier le dossier public | 🟢 — profil `v2`, 5 écarts sur 6 corrigés, le 6ᵉ déclaré |
| **R-4** | `stamped_at_declared` face au bloc | 🟢 |
| **R-5** | documenter la recette `campaign_sha256` | 🟠 — l'affirmation est corrigée, la **publication de la recette** reste une décision |
| **R-6** | provenance des évaluateurs | 🟠 — contrat `station.export.campagne/3` **proposé**, rien d'implémenté. Point de changement : Station |
| **R-7** · **R-8** | `config_snapshot_sha256`, rendu `['True']` | 🟢 |
| **R-9** | identité du signataire | 🟢 — c'est B-1 |

---

## La chaîne expérimentale Mesure → Station → Preuve

| Étape | Ce qui existe | Ce qui manque |
|---|---|---|
| **Mesure** | l'API émet 12 champs de provenance par signal, `evaluator` renseigné 5/5 sur 7/7 | rien, à ce maillon |
| **Station** | le registre chaîne les enregistrements ; l'export produit une archive | **la provenance est perdue à l'écriture du registre** — 0 champ sur 238 mesures. C'est R-6 |
| **Preuve** | 22 lignes de contrôle, attestation Ed25519, ancrage Bitcoin, complétude, capacité déclarée | la clé de production, et la publication du magasin |

**Deux maillons sur trois tiennent.** Le trou côté Station est R-6, analysé et
non engagé.

### Et le chaînon d'exploitation que B-3 a révélé

C'est le point le plus important de ce suivi, et il n'est **pas** un défaut de
vérification.

Evidence consomme des paquets **exportés**. Sur le dossier réel de 22 fichiers
reçu le 30 octobre, les 21 empreintes déclarées ont été recalculées et
concordent — mais `verify.py` a refusé, faute de manifeste Evidence, et ce
refus est **juste**.

**Rien ne convertit une collecte brute en paquet Evidence.** Le chemin
d'accueil d'un pilote n'existe pas. Tant qu'il n'existe pas, « de bout en
bout » s'arrête au moment où un tiers nous tend ses fichiers.

C'est le chaînon à construire pour l'exploitation, et il relève de
l'outillage existant — pas d'un nouveau chantier d'architecture.

---

## Prochaines étapes

Dans l'ordre, et sans rien ouvrir de nouveau.

| | | Qui |
|---|---|---|
| 1 | **générer la clé de production** — hors ligne, poste de l'opérateur, réseau débranché, selon la procédure B-2 §Activation | un opérateur, pas un agent |
| 2 | magasin en `store_kind: production`, puis `publish_store.py audit` sur le magasin **réel** | ingénierie |
| 3 | **C-5** : publier l'empreinte et la `store_version` sur le second canal, après relecture humaine des `NOT TESTED` de l'audit | décision, puis ingénierie |
| 4 | **le chaînon d'accueil** : convertir une collecte brute en paquet Evidence, pour que B-3 se referme en exploitation et pas seulement en vérification | ingénierie |
| 5 | **R-6** : décider si l'écriture du registre de Station conserve la provenance de l'API. Trois décisions distinctes, aucune prise | coordination Station |
| 6 | **D-7** : deux artefacts attendus de Dennis | hors de notre main |
| 7 | **R-5, seconde moitié** : publier ou non la recette `campaign_sha256` | décision isolée, sans prérequis |

Les gestes 1 et 3 sont **irréversibles**. Aucun des deux n'est pris.

---

## Ce qui n'est pas déclaré

**Evidence V1 n'est pas probatoirement close.** Deux des trois piliers d'une
affirmation probante ont bougé ce jour : *qui atteste* est passé d'une clé de
test à une entité nommée en capacité `experimental` — un progrès réel, et un
seul maillon. *Quel instrument a mesuré* reste `not_demonstrable`.

Et la phrase qui ne doit jamais glisser : **une attestation expérimentale
n'est pas une certification juridique.** Le vérificateur l'imprime, dans les
deux langues, à chaque passage, et
[`tests/test_capacite.py`](../tests/test_capacite.py) échoue si elle cesse de
l'être.

Le détail de ce qui est démontré, et de ce qui ne l'est pas, est dans
[`EXPERIMENTAL_CHAIN.fr.md`](EXPERIMENTAL_CHAIN.fr.md).

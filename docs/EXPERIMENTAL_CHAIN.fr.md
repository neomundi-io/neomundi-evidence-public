<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="EXPERIMENTAL_CHAIN.md">English</a> · <a href="../README.md">← README</a></sub>

# La chaîne de preuve expérimentale — ce qu'elle démontre, et ce qu'elle ne démontre pas

**6 novembre 2026.** B-1 approuvée, B-2 outillée, C-5 préparée. Ce document
consigne ce qui est **réellement démontré**, comment cela a été mesuré, et où
la chaîne s'arrête.

> **Une attestation expérimentale n'est jamais une certification juridique.**
> Cette phrase n'est pas une clause ajoutée ici : le vérificateur l'imprime,
> dans les deux langues, à chaque passage, et
> [`tests/test_capacite.py`](../tests/test_capacite.py) échoue si elle cesse
> de l'être.

---

## L'entité émettrice

**NeoMundi Recherche**, RNA **W563015824** — l'association scientifique
portant actuellement le projet. Périmètre : **expérimental, scientifique,
non commercial**.

`legal_capacity_to_attest` vaut **`experimental`**, et cette valeur dit
quelque chose de précis :

| | |
|---|---|
| L'entité est **nommée** | et a pris une décision documentée d'attester |
| Le périmètre est **non commercial** | |
| **Aucune vérification de ses pouvoirs n'a été faite** | |

`experimental` n'est **pas un `verified` plus faible**. C'est l'inverse :
`verified` dit qu'un contrôle a eu lieu ailleurs ; `experimental` dit
qu'aucun n'a eu lieu. La distinction entre une identité **déclarée** et une
identité juridiquement **vérifiée** est la seule chose que cette condition
existe pour garder visible.

**Volontairement non fait, et non requis :** la constitution de la future
société commerciale, et toute qualification juridique exhaustive. Ni l'une ni
l'autre ne bloque ce périmètre.

---

## La chaîne, maillon par maillon

| | Maillon | État | Ce qui l'établit |
|---|---|---|---|
| **a** | octets de l'archive → empreinte | ✅ | `sha256`, bibliothèque standard. Portable depuis l'épinglage de `create_system` — avant, Linux rendait une autre empreinte que celle signée |
| **b** | empreinte → JWS détaché | ✅ | Ed25519, algorithme **imposé**, jamais lu dans l'en-tête. Falsifier `alg` en `none` est attrapé |
| **c** | clé publique → magasin de confiance | ⚠️ **magasin de test** | l'outil le dit de lui-même : une clé `test` n'accorde rien sans `--allow-test-keys` |
| **d** | clé publique → **personne morale** | ⚠️ **déclaré** | B-1 : entité nommée, capacité `experimental`, pouvoirs non vérifiés |
| **e** | date | ✅ | OpenTimestamps, blocs Bitcoin 974714/974715. Atteste *pas plus tard que*, jamais *quand*. Un `PENDING` n'atteste **aucune** date |
| **f** | complétude de l'export | ⚠️ **partiel** | attrape une amputation *incohérente* ; un faussaire qui réécrit aussi la déclaration le défait |
| **g** | instrument de mesure | ❌ **absent** | R-6 : 0 champ de provenance sur 238 mesures. `not_demonstrable` |

Trois maillons tiennent seuls. Deux sont déclarés. Un est partiel. **Un est
absent.**

### La dépendance que cette semaine a révélée

Le maillon **f** retombe sur **b**. Le contrôle de complétude est la défense
qui fonctionne sur une archive **non signée** ; au-delà, seule la signature
arrête un faussaire méticuleux. B-1 et B-2 ne sont donc pas un chantier
parallèle à celui de la complétude — **ils en conditionnent la valeur.** Tant
que la clé est une clé de test, la complétude n'est garantie que contre la
négligence.

---

## Ce qu'un tiers peut reproduire

Hors ligne, sans accès à nous, sans compte, sans réseau :

```sh
# 1. l'archive est bien celle sur laquelle l'attestation s'engage
python verify.py <archive.zip> --corpus <corpus>

# 2. la signature, et l'identite declaree pour elle
python verify_attestation.py <archive.zip.jws> --archive <archive.zip> \
       --trust-store <trust-store.json> --store-digest <empreinte du canal 2>

# 3. la date d'ancrage, sans faire confiance a notre horloge
python timestamp.py verify <preuve.ots> --subject <archive.zip.jws>

# 4. et le paquet se reconstruit octet pour octet
python tests/make_fixture.py <dossier> --profile v1   # reproduit e31e12bb…
```

Le `--store-digest` du geste 2 est ce qui ferme la faiblesse de source
unique : l'auditeur obtient cette empreinte par un **second canal**, et
l'hôte principal ne peut plus mentir seul. La charge de ce canal est produite
par `publish_store.py payload`, et porte **une empreinte et une version, rien
d'autre**.

---

## Garanties démontrées, et par quoi

Chaque ligne ci-dessous est un test qui échoue si la propriété cesse de
tenir.

| Garantie | Mesurée par |
|---|---|
| Une capacité déclarée **ne change jamais un verdict**. Écrire `verified` dans un magasin ne rapporte rien | `test_capacite` 6–7 : décomptes identiques, `NOT TESTED` dans les deux cas |
| La distinction déclarée/vérifiée survit à la traduction | `test_capacite` 4–5 : la négation est exigée dans les **deux** langues |
| Une valeur de capacité inconnue du vérificateur est **rapportée, non interprétée** | `test_capacite` 9 |
| Toute valeur du schéma a une explication, et toute explication une valeur du schéma | `test_capacite` 8 — la dérive qui avait mordu `CAUSES_PAR_SIGNAL` |
| Une amputation **incohérente** d'un export est refusée, sans aucune signature | `test_completude` ; rejouée en OD-C dans la réévaluation ODA3 |
| Une **rotation** laisse les signatures antérieures de confiance ; une **compromission** les invalide toutes, rétroactivement | `test_cles` 5–6, sur la **même** attestation, inchangée à l'octet : `PASS` puis `FAIL` |
| Une révocation à sec est refusée — deux fois | `test_cles` 4 : sans successeur, puis successeur non publié |
| Une compromission n'est ni requalifiable en rotation, ni remplaçable | `test_cles` 8 |
| Un `kid` ne se réutilise jamais | `test_cles` 9 |
| Le registre des paquets signés est **append-only** | `test_cles` 1–2 |
| Signer sans registre **le dit** | `test_cles` 3 |
| Une clé privée, et le registre, sont refusés partout sous le dépôt | `test_cles` 11–12 — garde dure, pas un avertissement |
| La charge du second canal ne porte **aucun matériel de clé** | `test_publication` 4 |
| Un scalaire privé dans un magasin est attrapé **deux fois** — par motif et par champ | `test_publication` 5 |
| Un audit en échec ne produit **aucune charge** | `test_publication` 6 |
| L'empreinte publiée est celle des **octets transmis** | `test_publication` 7 |
| Le préparateur de publication n'a **aucun accès réseau** | `test_publication` 8, vérifié statiquement sur ses imports |
| L'empreinte de la charge est acceptée telle quelle par `--store-digest`, et une fausse est refusée | `test_publication` 9–10 |

**Suites :** `completude` 15/15 · `bom` 11/11 · `capacite` 10/10 · `cles`
12/12 · `publication` 10/10 · `i18n` 26/26 · `attestation` 24/24 ·
`timestamp` 25/25 · `reconciliation` 27/27 · `falsification` 10/10 ·
`adversarial` 13 sur 15, avec deux limites déclarées.

**Aucune preuve historique n'a changé.** Le dossier V1 rend toujours
`19 PASS, 0 FAIL, 3 NOT TESTED`, son empreinte n'a pas bougé, et
`--profile v1` le reproduit toujours octet pour octet.

---

## Ce qui n'est PAS démontré

| | |
|---|---|
| **Que l'entité puisse légalement s'engager** | aucun pouvoir n'a été vérifié. Un `NOT TESTED` permanent — aucun code ne peut en décider |
| **Qui détient la clé**, en personne physique | le rôle est consigné ; la personne est au registre interne et n'est jamais publiée |
| **Que l'évaluateur déclaré soit celui qui a tourné** | R-6. `not_demonstrable`, et aucun changement de contrat ne le rend vérifiable depuis une archive |
| **Qu'une rétention ait été légitime** | le contrôle lit une déclaration, pas le registre |
| **Que le contenu soit vrai** | hors de portée d'une signature. Une attestation parfaitement signée sur une archive fabriquée est cryptographiquement valide |
| **Une date comme fait indépendant**, sans ancrage | `attested_at_declared` est déclaré par le signataire |
| **Une qualification eIDAS** | jamais revendiquée, sous aucune configuration |

---

## Le seul geste irréversible non pris

**La clé de production n'est pas générée.** L'outillage est construit et
testé — génération, garde, sauvegarde, rotation, circonscription d'une
compromission, le registre — et la clé elle-même n'existe pas.

C'est délibéré. Un secret de signature à longue vie au nom d'une personne
morale nommée est exactement le mécanisme irréversible qu'il ne faut pas
créer sans décision explicite, et la procédure documentée place sa génération
**hors ligne, sur le poste de l'opérateur**, pas dans une session de travail.

Ce qui reste, dans l'ordre, est dans
[`B2_KEY_CUSTODY_AND_ACTIVATION.fr.md`](B2_KEY_CUSTODY_AND_ACTIVATION.fr.md) :
accepter le bloc de garde, nommer le support de sauvegarde et l'emplacement
du registre, puis lancer une commande. Jusque-là, **toute attestation que ce
produit émet est une démonstration, et elle est décrite comme telle.**

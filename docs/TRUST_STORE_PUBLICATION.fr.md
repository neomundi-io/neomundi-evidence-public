<sub>🇬🇧 <a href="TRUST_STORE_PUBLICATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Publier le magasin de confiance

**6 novembre 2026.** Condition **C-5** de
[`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md). **Conception seulement — rien
n'est publié.**

> Aucune publication effective n'a lieu avant que l'audit de contenu de la
> dernière section soit fait et validé. Ce document est la conception et le
> verrou, pas l'acte.

---

## La faiblesse visée

Un auditeur télécharge aujourd'hui deux choses au même endroit :

- le dossier, avec son attestation ;
- le magasin de confiance qui dit quelle clé croire.

Qui contrôle cet endroit contrôle les deux. Un faussaire capable d'écrire
dans le dépôt peut y ajouter sa propre clé et signer avec elle une archive
reconstruite — et tous les contrôles passent. C'est la limite 7 de
[`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md), énoncée là comme « un faussaire
qui reconstruit l'archive **et** l'attestation produit un ensemble cohérent,
si sa clé est de confiance ».

**L'attaque ne porte pas sur la cryptographie. Elle porte sur la source
unique.** Ed25519 n'est pas le point faible ; le fait que la réponse à
« à qui est cette clé ? » arrive par la même route que la question, si.

---

## Ce qui corrigerait vraiment, et ce qui en a seulement l'air

| Proposition | Est-ce que ça aide ? |
|---|---|
| Publier le magasin sur un second hôte que nous tenons | **à peine** — même opérateur, même compromission |
| Publier l'**empreinte** du magasin sur un second canal | **oui** — l'auditeur compare, et un hôte seul ne peut plus mentir |
| Signer le magasin avec la clé même dont il se porte garant | **non** — circulaire ; le magasin est ce qui dit de croire cette clé |
| Signer le magasin avec une clé hors ligne distincte | **oui**, et cela déplace le problème vers la garde de cette clé, problème plus petit et mieux compris |
| Faire héberger le magasin par un tiers | **oui**, et cela coûte un accord que nous n'avons pas |

La deuxième ligne est la correction réelle et bon marché. La quatrième est la
plus forte, et elle est différée : elle demande une seconde clé, alors que la
partie A de [`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md) n'a même pas
tranché la première.

**Noter ce qui n'est pas dans cette liste : la provenance par affirmation.**
Un magasin qui dit « publié par NeoMundi » n'établit rien ; le faussaire écrit
la même ligne. Un chemin d'authenticité ne doit pas reposer sur ce que le
magasin prétend de lui-même.

---

## Conception

### Un registre versionné, séparé de toute archive

Le magasin **n'est pas** un fichier à l'intérieur d'un dossier. C'est un
registre à cycle de vie propre, parce que les clés survivent aux dossiers et
qu'un dossier ne doit pas porter sa propre réponse à la question de savoir si
son signataire est digne de foi.

| | |
|---|---|
| Identifiant | `store_id`, stable |
| Version | `store_version` monotone, **entier neuf à chaque changement** |
| Date | `updated_at_declared` — déclarée par nous, jamais un horodatage |
| Nature | `store_kind: production` ou `test` ; `test` vaut `untrusted_unless_allowed` |
| Contenu | matériel de clé **public** et identités, **uniquement** |

Un numéro de version compte plus qu'il n'y paraît : sans lui, deux auditeurs
détenant des magasins différents ne peuvent pas dire lequel est le plus
récent, et « le magasin le disait » devient infalsifiable.

Le schéma porte aujourd'hui un tableau `changes` — une histoire en ajout seul
de ce qui a changé et quand, par date déclarée. C'est **un relevé, pas une
version comparable** : deux magasins peuvent porter des histoires différentes
sans aucun nombre qui les ordonne, et **aucun code ne lit ce champ** —
`sign.py genkey` l'écrit, rien ne le consomme. `store_version` manque donc
réellement, et l'ajouter est un **préalable** de cette condition, non un
raffinement optionnel.

### Deux canaux, et à quoi sert chacun

| Canal | Porte | Rôle |
|---|---|---|
| **Primaire** — le dépôt Evidence | le magasin complet | ce que l'outil lit |
| **Secondaire** — le site `.org`, et la carte MCP | l'**empreinte** du magasin et son `store_version` | ce à quoi l'auditeur compare |

Le canal secondaire ne porte **aucun matériel de clé**. Il porte une empreinte
et une version, ce qui suffit à détecter un magasin substitué et ne contient
rien qui puisse être substitué *à* un magasin.

### Le chemin d'authenticité

Un auditeur qui veut plus que notre parole fait ceci :

1. télécharger le magasin depuis le dépôt ;
2. calculer son SHA-256 ;
3. lire l'empreinte et la version publiées sur le `.org` ;
4. comparer.

Un faussaire doit désormais compromettre **deux** canaux exploités
indépendamment, et les maintenir cohérents. C'est tout le gain, et il faut le
dire franchement : cela élève le coût de l'attaque, cela ne la rend pas
impossible.

### Ce que cela n'établit toujours pas

- **Que l'entité derrière la clé a qualité pour s'engager.** C'est B-1, et
  aucun canal de publication n'y touche.
- **Que nous sommes qui nous disons être.** Les deux canaux sont les nôtres.
  Une attestation d'identité par un tiers est hors du périmètre V1, et c'est
  dit comme tel.
- **Qu'une clé n'a pas été mal employée par son propre détenteur.** C'est la
  garde, pas la publication : partie B de
  [`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md).

Un lecteur qui prendrait deux canaux pour une preuve d'identité aurait
sur-lu cette conception. Les deux canaux défont une *substitution* ; ils ne
disent rien de *qui*.

---

## Audit de contenu — le verrou avant toute publication

Le magasin est, par construction, du matériel public uniquement. Mais « par
construction » est précisément le genre d'affirmation qu'il faut contrôler
plutôt que croire, parce qu'un magasin est assemblé par un outil et que les
outils acquièrent des champs.

Rien n'est publié tant que chaque ligne ci-dessous n'est pas répondue sur
constat.

| À contrôler | Pourquoi cela compte | État |
|---|---|---|
| Aucun matériel de clé privée, dans aucun champ | la défaillance catastrophique | **à vérifier à la publication** |
| Aucune donnée personnelle — pas de nom de personne physique, pas de courriel, pas d'adresse | publier l'identité d'un représentant est un acte RGPD, pas un acte technique | **à vérifier** |
| Les `legal_name` sont des entités, pas des personnes | le nom d'une association est public ; celui d'une personne n'est pas à nous de le publier | **à vérifier** |
| Aucun nom d'hôte, chemin ou identifiant de machine interne | `nm-operator-poste` nomme un rôle ; il ne doit pas nommer un hôte | **à vérifier** |
| `store_kind` est juste | un magasin `test` publié comme production rendrait les clés de démonstration dignes de foi | **à vérifier** |
| Aucun `registration_reference` avant B-1 | publier un enregistrement laisse entendre que l'entité a décidé de s'engager | **à vérifier** |
| Les champs `notes` relus un par un | le texte libre est là où le contexte interne fuit | **à vérifier** |

La dernière ligne est celle qui attrapera réellement quelque chose. Les
champs structurés sont relus ; les notes en texte libre s'écrivent à la hâte.

### Qui valide

L'audit de contenu est une **décision humaine**, consignée et datée, par le
représentant identifié à la partie A de
[`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md). Tant que ce représentant
n'est pas identifié, cette condition **ne peut pas** se fermer — ce qui rend
C-5 dépendante de B-1, et pas seulement voisine.

---

## Ce qui reste à construire

| Élément | État |
|---|---|
| `store_version` dans `schemas/evidence-trust-store-v1.json` | **manquant** — préalable |
| Une ligne de vérificateur comparant l'empreinte du magasin à une empreinte déclarée | **non construite** |
| La page de publication sur le `.org` | **non construite** |
| L'audit de contenu, effectué | **non fait** |
| La validation | **bloquée sur B-1** |

**C-5 n'est donc pas fermable avant B-1.** Énoncer la conception est la part
qui peut se faire maintenant, et c'est ce que ce document est.

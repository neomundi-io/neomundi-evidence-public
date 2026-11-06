<sub>🇬🇧 <a href="B2_KEY_CUSTODY_AND_ACTIVATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# B-2 — Garde et activation de la clé Ed25519 réelle

**6 novembre 2026.** Condition **B-2**. Pendant opérationnel de
[`B1_EXPERIMENTAL_SIGNING_DECISION.fr.md`](B1_EXPERIMENTAL_SIGNING_DECISION.fr.md).

> **Aucune clé ne peut être générée sous cette procédure avant que B-1 soit
> approuvée et que la garde ci-dessous soit acceptée.** Une clé générée plus
> tôt serait détenue au nom d'une entité qui n'a pas décidé de s'engager, et
> chaque dossier signé avec elle emporterait ce défaut.

---

## Pourquoi cette clé doit être distincte de la clé RGC

Ce n'est pas une question de propreté. Quatre raisons, et la quatrième
tranche.

| | Clé RGC | Clé Evidence |
|---|---|---|
| Objet | signe des reçus de mesure **à la volée** | atteste un **dossier gelé**, après coup |
| Où vit le secret | sur l'**hôte de l'API de production** | hors ligne, sur un poste d'opérateur, **jamais sur un serveur** |
| Espace de `kid` | `neomundi-rgc-…` | `nm-ev-…` |
| Qui peut vérifier | **le seul détenteur du secret** | n'importe qui, à partir de la seule clé publique |

### La quatrième raison, celle qui tranche

Le `verify_jws` de `app/rgc/signing.py` appelle `_public_key_pem()`, qui
appelle `_load_private_key()` : **il dérive la clé publique de la clé
privée.** Seul le détenteur du secret peut donc vérifier une signature RGC,
et hors ligne rien ne marche du tout — `GET /v1/rgc/jwks` est un point
d'accès HTTP.

Une attestation Evidence doit être vérifiable **par un auditeur qui ne nous
fait pas confiance et n'a pas de réseau**. C'est tout le produit. Réutiliser
la clé RGC ne serait pas seulement malpropre : cela rendrait l'attestation
vérifiable par nous seuls, soit l'inverse de sa raison d'être.

Donc : **RGC ne doit jamais être proposé comme vérificateur d'une
attestation Evidence, et les deux clés ne partagent ni matériel, ni
détenteur, ni hôte, ni espace de `kid`.**

Une seconde conséquence à dire : la clé publique RGC est déjà publiée dans
un dépôt public, et cette publication **n'établit pas le contrôle officiel**
— l'organisation GitHub rend `is_verified: false`, le fichier est rangé sous
`fixtures/`, et le commit est signé par la clé web-flow de GitHub. Quel que
soit le chemin de provenance que le magasin Evidence retiendra (C-5), il ne
peut pas emprunter celui de RGC.

---

## Génération

| | |
|---|---|
| Algorithme | **Ed25519**, imposé — jamais lu dans un en-tête de jeton |
| Outil | `sign.py genkey` |
| Où | **hors ligne**, sur le poste de l'opérateur nommé en B-1 D-3 |
| Chemin de la clé privée | **hors du dépôt**, imposé |
| `kid` | `nm-ev-recherche-202611-1` |
| `--store-kind` | `production` |
| `--signer-kind` | `association` |
| `--signer-jurisdiction` | `FR` |

L'outil refuse déjà d'écrire une clé privée sous la racine du dépôt —
`refuse_dans_le_depot()`. Cette garde n'est pas un conseil : une clé privée
commitée reste dans l'historique Git pour toujours.

Le `kid` n'est **jamais réutilisé**, y compris après révocation. Un `kid`
réutilisé rendrait deux clés différentes indiscernables dans un magasin, et
transférerait silencieusement la confiance de l'une à l'autre.

---

## Garde — les cinq réponses qui étaient blanches

`SIGNING_POLICY.fr.md` les marquait **à décider**. Les voici, comme
proposition à accepter ou amender.

| Question | Proposé |
|---|---|
| Où vit le secret ? | le **magasin DPAPI** du poste de l'opérateur, qui le lie à cet utilisateur Windows sur cette machine |
| Qui peut le lire ? | le rôle d'**opérateur technique** de B-1 D-3, et personne d'autre |
| Y a-t-il une sauvegarde hors machine ? | **oui, exigée** |
| Où est la sauvegarde ? | **approuvé le 6 novembre** : une **clé USB chiffrée dédiée**, hors machine, physiquement séparée du poste, portant la clé privée et son `kid` **et rien d'autre** |
| Qui autorise une signature ? | le **représentant habilité** de B-1 D-2 |

### Pourquoi la sauvegarde n'est pas optionnelle, et pourquoi elle est dangereuse

Sans elle, une panne de disque rend toute attestation future impossible — et
incite à régénérer sous le même `kid`, ce que la convention interdit.

Avec elle, le secret existe en deux endroits, donc la garde devient deux
problèmes. Le support ne porte donc **que** la clé : aucun manifeste, aucune
note disant à quoi elle sert, rien qui le rende volable pour lui-même. Et il
ne doit pas être atteignable avec le poste — une sauvegarde dans le tiroir de
la machine protège de la panne de disque et de rien d'autre.

### Ce qui n'est PAS proposé, et pourquoi

- **Ni HSM, ni KMS en nuage.** Les deux déplaceraient le secret vers un
  service et introduiraient une dépendance que ce produit existe pour
  éviter. Pour une expérience non commerciale, le coût ne se justifie pas.
  Pour un pilote commercial, à réexaminer.
- **Ni secret partagé, ni clé scindée.** Un détenteur, nommé. Scinder une
  clé entre détenteurs est une vraie technique, et la mauvaise ici : elle
  protège d'un détenteur malhonnête, qui n'est pas le risque à cette
  échelle, et elle multiplie les façons dont une signature devient
  impossible.
- **Aucune phrase secrète sur le fichier de clé.** DPAPI le lie déjà à
  l'utilisateur et à la machine ; une phrase par-dessus serait stockée
  quelque part, soit un second secret sans seconde garde.

---

## Activation — la procédure ordonnée

Aucun geste ne peut être pris avant que le précédent soit consigné comme
fait.

### Geste 0 — les préalables (rien de technique encore)

1. B-1 est **approuvée**, avec D-1, D-2 et D-3 remplis et datés.
2. La garde ci-dessus est **acceptée**, ou amendée puis acceptée.
3. `experimental` est ajouté au schéma du magasin, avec la ligne de
   vérificateur qui en dit le sens.

**Si l'un des trois manque, s'arrêter.** Générer une clé « pour être prêt »
est précisément l'acte que cette procédure existe pour empêcher.

### Geste 1 — génération, hors ligne

```sh
# sur le poste de l operateur, reseau deconnecte
python sign.py genkey \
    --kid nm-ev-recherche-202611-1 \
    --out <chemin HORS du depot> \
    --trust-store-out <chemin> \
    --store-kind production \
    --signer "NeoMundi Recherche" \
    --signer-legal-name "NeoMundi Recherche" \
    --signer-kind association \
    --signer-jurisdiction FR \
    --valid-from <date de l approbation B-1> \
    --key-notes "Perimetre experimental, non commercial. legal_capacity_to_attest: experimental."
```

Consigner : le `kid`, la clé publique `x`, la date, et le rôle de
l'opérateur. **Jamais la clé privée, et jamais son chemin dans un document
partagé.**

### Geste 2 — garde

1. Placer la clé privée dans le magasin DPAPI.
2. Écrire la sauvegarde hors machine.
3. **Supprimer le fichier en clair** produit par `genkey`, en l'écrasant
   puis en le détruisant — pas en le mettant à la corbeille.
4. Vérifier que la clé signe toujours, depuis la copie DPAPI, sur une
   archive jetable.

Le geste 4 compte : une garde qui n'a jamais été exercée est une garde dont
personne ne sait qu'elle fonctionne.

### Geste 3 — publication du matériel public

Le magasin, en `store_kind: production` et `store_version: 1`. C'est
**C-5**, qui a son propre audit de contenu — sept points, dont la relecture
de chaque champ `notes`, là où le contexte interne fuit.

### Geste 4 — la première attestation réelle

Un dossier, choisi délibérément, avec l'autorisation du représentant
consignée. Puis le vérifier comme le ferait un auditeur : hors ligne, à
partir de la seule clé publique, et avec `openssl pkeyutl -verify` comme
second outil indépendant.

**Si cette vérification ne passe pas, s'arrêter et ne pas signer un second
dossier.**

---

## Le registre qui n'existe pas encore

`SIGNING_POLICY.fr.md` le nommait manquant, et il l'est toujours : **aucune
trace de quels dossiers ont été signés avec quel `kid`.**

Sans lui, une compromission ne peut pas être circonscrite — et la
circonscrire est la seule chose qui en limite les dégâts, puisque marquer
une clé `compromised` invalide **tous** les dossiers qu'elle a signés,
rétroactivement, quelle que soit la date qu'ils déclarent.

Forme minimale viable, une ligne par attestation, hors du dépôt public :

```
<attested_at_declared>  <kid>  <bundle_sha256>  <attestation_sha256>  <role operateur>
```

**Ce registre est un préalable de la première attestation réelle**, pas un
suivi. Une seule signature sans trace est déjà une compromission non
circonscriptible.

---

## Rotation, compromission, révocation

Inchangées depuis [`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md), et
redites parce que c'est la partie qui porte des conséquences :

- `rotated` laisse les signatures antérieures **de confiance** ;
  `compromised` les rend **toutes non fiables, rétroactivement**.
  L'asymétrie est le fond : un voleur maîtrise la date qu'il écrit, donc
  aucune date ne peut borner une compromission.
- **Ne jamais révoquer à sec.** Générer le successeur, le publier au
  magasin, poser `superseded_by` sur le prédécesseur, et seulement alors le
  marquer. Une révocation dont le remplacement n'est pas publié laisse
  chaque consommateur avec une clé qu'il doit refuser et aucune qu'il puisse
  accepter — et le vérificateur rend `NOT TESTED` pour une clé inconnue,
  donc la chaîne perd silencieusement un niveau au lieu d'échouer
  franchement.

---

## Acceptation — APPROUVÉE le 6 novembre 2026

```
C-1  La garde ci-dessus est ACCEPTEE, avec une garde de rotation
     explicitement approuvee :

     AUCUN retrait de cle sans successeur PREALABLEMENT PUBLIE
     dans le meme magasin.

     Outille et eprouve : `sign.py retire --kind rotated` refuse sans
     `--successor`, puis refuse un successeur absent du magasin. Les
     cas 4, 5 et 6 de `tests/test_cles.py` le verrouillent.

C-2  Le support de sauvegarde hors machine est :

     une CLE USB CHIFFREE DEDIEE, hors machine, portant la cle privee
     et son `kid` ET RIEN D AUTRE.

     << Dediee >> est une contrainte, pas un adjectif : un support
     partage avec autre chose porte un manifeste, un nom de fichier,
     une date -- de quoi dire a qui le vole ce qu il tient.

C-3  Le registre des dossiers signes sera tenu a :

     l espace prive Evidence VERSIONNE, sous `registre/`, avec une
     sauvegarde INDEPENDANTE de celle de la cle.

     Hors du depot public, et la garde est dure : `sign.py` refuse
     d ecrire un registre sous la racine du depot (cas 12).

     Date : 6 novembre 2026   Decision de direction.
```

### Pourquoi les deux sauvegardes restent séparées

La clé et le registre se sauvegardent **indépendamment**, et ce n'est pas une
précaution de confort : les réunir sur le même support offrirait à qui le vole
**à la fois le secret et la liste de ce qu'il ouvre**. Le registre nomme
chaque paquet signé ; la clé permet d'en signer d'autres. Un seul support
porteur des deux transforme un vol en substitution indétectable.

### Ce qui reste, et c'est tout

**La clé de production n'est pas générée**, et ce bloc rempli ne la génère
pas. Il autorise le geste ; le geste se fait **hors ligne, sur le poste de
l'opérateur**, réseau débranché, selon la procédure du §Activation — pas dans
une session de travail, et pas par un agent.

Jusque-là, tout ce que ce produit signe reste une **démonstration**, et le
vérificateur le dit de lui-même : une clé `test` n'accorde rien sans
`--allow-test-keys`.

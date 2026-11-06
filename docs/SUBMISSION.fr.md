<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="SUBMISSION.md">English</a> · <a href="../README.fr.md">← README</a></sub>

# Soumettre un paquet d'exécution, et le vérifier indépendamment

Pour un pilote qui veut faire traiter ses relevés d'exécution par NeoMundi
Evidence. Tout se passe en local, bibliothèque standard seule, **sans aucune
clé privée et sans réseau**.

> **Ce que l'ingestion établit, et ce qu'elle ne peut pas.** Elle recalcule
> les empreintes et les tailles des fichiers que vous déclarez, contrôle la
> structure de votre manifeste, et vérifie toute signature que vous détenez
> déjà contre le magasin de confiance publié. Elle n'établit **rien d'autre**
> — et elle ne transforme jamais une déclaration en fait attesté.

---

## 1. Le paquet

Un dossier, ou un ZIP de ce dossier, avec un manifeste à la racine :

```
mon-paquet/
    submission.json          <- le manifeste, schema neomundi.evidence.submission/1
    artefacts/
        prompt.txt
        response.txt
        measurement.json
```

Pour en obtenir un exemple fonctionnel à recopier :

```sh
python tests/make_submission.py mon-paquet --profil valide
```

`submission.json` déclare qui vous êtes, ce que vous avez exécuté, et une
entrée par fichier avec son `sha256`, sa taille en octets et son `role`. Le
contrat complet est dans
[`schemas/evidence-submission-v1.json`](../schemas/evidence-submission-v1.json),
et chaque nom de champ y finit par `_declared` quand c'est votre parole plutôt
qu'une valeur que nous recalculons. Ce suffixe n'est pas un ornement : c'est
la frontière entre les deux registres.

**Les chemins sont relatifs, en barres obliques, sans `..`.** Les chemins
absolus, les lettres de lecteur, les barres inversées et les liens
symboliques sont refusés — un paquet ne doit pas pouvoir nommer un fichier
hors de lui-même.

## 2. L'ingestion

```sh
python adapters/ingest.py mon-paquet \
       --out rapport.json --md rapport.md \
       --trust-store trust/trust-store.json
```

`--trust-store` n'est nécessaire que si votre paquet déclare des
attestations. Fournissez **le magasin de l'opérateur**, jamais celui porté
par le paquet : un paquet ne doit pas porter sa propre réponse à la question
de savoir si son signataire est digne de confiance.

### Trois verdicts, et ils ne sont pas interchangeables

| Verdict | Sortie | Sens |
|---|---|---|
| **ACCEPTÉ** | `0` | structure saine, chaque empreinte déclarée recalculée et concordante |
| **INCOMPLET** | `0`, ou `2` avec `--strict` | **ce n'est pas un refus.** Il manque quelque chose *que vous pouvez fournir* — un artefact déclaré absent, ou une attestation déclarée sans magasin fourni |
| **REJETÉ** | `1` | un contrôle a échoué. Une empreinte qui ne concorde pas, un champ obligatoire absent, un chemin qui sort du paquet, une signature qui ne vérifie pas |

La distinction entre INCOMPLET et REJETÉ est délibérée. Traiter un fichier
manquant comme une fraude ferait fuir un pilote de bonne foi ; traiter une
empreinte fausse comme un manque laisserait passer un paquet faux.

## 3. Les trois registres du rapport

Chaque ligne porte sa nature, et c'est toute la conception :

| Nature | Ce que cela veut dire |
|---|---|
| **CONTROLE** | nous l'avons recalculé. Empreintes, tailles, structure, signatures. Le seul registre où nous engageons quelque chose |
| **DECLARE** | votre parole, conservée **verbatim**. Identité, modèle, conditions d'exécution. Nous la transportons ; nous ne la cautionnons pas |
| **NON DEMONTRABLE** | aucun contrôle ne pourrait l'établir depuis ce paquet. Ce n'est pas un manque de zèle — c'est une propriété du matériau |

**Aucune ligne `DECLARE` ne peut jamais porter `PASS`.** Le cas 13 de
[`tests/test_ingestion.py`](../tests/test_ingestion.py) échoue si cela
arrive. Sans ce verrou, il suffirait d'écrire « modèle X » dans un manifeste
pour que le rapport le présente comme contrôlé.

### Ce qui reste NON DEMONTRABLE, quoi que vous envoyiez

- **que l'exécution ait eu lieu.** Nous recalculons des empreintes de
  *fichiers*. Qu'ils proviennent de l'exécution que vous décrivez est une
  déclaration, et le restera.
- **qui a produit le paquet.** Rien dans un fichier n'établit qui l'a écrit.
- **que les artefacts soient ceux de cette exécution.** Des empreintes
  concordantes établissent que les fichiers n'ont pas bougé depuis l'écriture
  du manifeste. C'est une garantie réelle, et plus étroite qu'elle n'en a
  l'air.
- **la date.** `submitted_at_declared` est la vôtre ; aucune horloge de
  confiance n'intervient.
- **le sens de vos champs.** Décider qu'un de vos scores correspond à l'un
  des nôtres est une affirmation sur deux définitions. Cela demande une table
  de correspondance **déclarée** — voir
  [`adapters/reconcile.py`](../adapters/reconcile.py), qui refuse de deviner.

## 4. Vérifier indépendamment, sans nous

Si votre paquet porte une attestation signée par NeoMundi Recherche, vous
pouvez la contrôler vous-même — hors ligne, à partir de matériel public
seulement :

```sh
# 1. le magasin de confiance, depuis le depot
curl -O https://raw.githubusercontent.com/neomundi-io/neomundi-evidence-public/main/trust/trust-store.json

# 2. son empreinte, depuis un AUTRE canal -- c'est le geste qui compte
curl https://mcp.neomundi.org/trust/trust-store-digest.json

# 3. confronter, puis verifier
sha256sum trust-store.json          # doit egaler le champ `sha256` ci-dessus
python verify_attestation.py <attestation.jws> --archive <sujet> \
       --trust-store trust-store.json --store-digest <empreinte du geste 2>
```

Prendre le magasin *et* son empreinte au même endroit n'établit qu'une chose :
qu'une source est d'accord avec elle-même. Voir
[`trust/README.fr.md`](../trust/README.fr.md).

## 5. La sécurité, telle qu'elle est implémentée

| | |
|---|---|
| **Aucun code de votre paquet n'est jamais exécuté** | l'ingestion lit des octets et les hache. Rien n'est importé, exécuté ni interprété |
| **Aucune clé privée n'est nécessaire** | vérifié statiquement : `adapters/ingest.py` n'importe ni `sign.py` ni `cryptography` |
| **Votre paquet n'est jamais modifié** | un ZIP est déplié dans un dossier temporaire, et c'est cette copie qui est lue |
| **La traversée de chemin est refusée avant extraction** | un membre nommé `../../x` est rejeté *avant* que rien ne soit écrit — l'apprendre pendant l'extraction serait trop tard |
| **Borné** | 512 artefacts, 64 Mio par fichier, 256 Mio au total, 4096 membres de ZIP. Un paquet annonçant plus d'octets décompressés que la borne est refusé sur sa propre déclaration |
| **Les liens symboliques sont refusés** | un lien passe un motif de chemin et sort quand même du paquet |

## 6. Les limites, dites simplement

Un paquet ACCEPTÉ est **exploitable**, pas **prouvé**. Cela signifie que sa
structure tient et que ses empreintes déclarées sont à notre portée de
recalcul. Tout ce qui porte sur l'exécution elle-même reste votre
déclaration.

Et une attestation vérifiée sous cette chaîne est signée en
`legal_capacity_to_attest: experimental` — l'entité est nommée et a décidé, et
**aucune vérification de ses pouvoirs n'a été faite**. Ce n'est jamais une
certification juridique. Le vérificateur le dit à chaque passage.

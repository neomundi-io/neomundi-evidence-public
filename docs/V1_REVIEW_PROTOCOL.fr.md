<sub>🇬🇧 <a href="V1_REVIEW_PROTOCOL.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Protocole de revue — NeoMundi Evidence V1

**Lundi 9 novembre 2026.** Fiche produit :
[`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md).

---

## Ce qu'on vous demande, et ce qu'on ne vous demande pas

**On vous demande d'essayer de nous mettre en défaut.** Un « ça a l'air
bien » ne nous apprend rien ; un contre-exemple vaut une semaine de
développement.

**On ne vous demande pas de valider.** Aucun de vous n'a à signer quoi que ce
soit, et la candidate n'est pas en attente de votre approbation — elle est en
attente de vos **objections**.

---

## Avant de commencer : ce qui est synthétique

> Tout le dossier de démonstration est **fabriqué**. La clé de signature était
> une clé de **démonstration éphémère**, **détruite**. Le reçu externe est
> **inventé**.
>
> Une seule chose est réelle : la **preuve d'horodatage**, obtenue des quatre
> calendriers publics. Elle est **`PENDING`**, et **cela n'atteste aucune
> date**.

**Aucune des cinq fonctions n'a été exercée sur un dossier de pilote réel.**
C'est la limite dominante de cette revue, et c'est à elle que vos objections
seront les plus utiles.

---

## Préparation — cinq minutes

```sh
git clone https://github.com/neomundi-io/neomundi-evidence-public
cd neomundi-evidence-public/examples/dossier-v1
```

Python 3.11 ou plus. **Aucune dépendance n'est nécessaire** pour les
21 contrôles d'intégrité. Pour les deux lignes de signature :
`pip install cryptography` — et si vous ne l'installez pas, l'outil rend
`NOT TESTED`, jamais `PASS`.

La démonstration guidée : `sh demo_v1_5min.sh` depuis la racine.

Le guide de l'auditeur, avec les cinq commandes et les résultats attendus :
[`examples/dossier-v1/LISEZ-MOI.fr.md`](../examples/dossier-v1/LISEZ-MOI.fr.md).

---

## Les périmètres proposés

Un périmètre par relecteur, choisi pour que personne ne relise ce qu'un autre
relit — et que personne ne relise son propre travail.

### Dennis — la réconciliation, et l'adaptateur conçu pour votre dossier

Vous êtes le seul à pouvoir dire si l'adaptateur lira **réellement** votre
dossier.

| À éprouver | Où |
|---|---|
| L'importateur relève-t-il les champs d'un reçu de **votre** forme ? | `adapters/receipt_import.py` |
| La table de correspondance est-elle **remplissable** par quelqu'un qui connaît les deux côtés ? | `examples/dossier-v1/map-*.json` |
| Les cinq statuts couvrent-ils vos cas, ou en manque-t-il un ? | `docs/RECONCILIATION.fr.md` |
| **La distinction `NOT COMPARABLE` tient-elle ?** | le cœur du sujet |

**La question qui compte.** Nous refusons de conclure que `0,3863` contre
`0,594` est une divergence de calcul, parce qu'il manque la version de mesure,
la couverture et la définition de chaque côté. **Est-ce que ce refus vous
paraît juste, ou excessif ?** Si vous pouvez fournir ces quatre éléments, la
comparaison devient possible — et c'est le seul chemin.

> `RECONCILIATION.md` et le reçu lui-même **ne nous sont pas parvenus**.
> L'adaptateur est donc conçu sur la forme décrite, pas sur votre dossier.

### Sergei — l'exploitation, et la règle d'arrêt

Vous avez conduit des campagnes réelles. Vous savez ce qui casse.

| À éprouver | Où |
|---|---|
| Un dossier produit par une campagne réelle passe-t-il les 21 contrôles ? | `verify.py` |
| Les 2 `NOT TESTED` structurels sont-ils acceptables pour un pilote ? | chaînage, origine |
| Le mode `--strict` convient-il à une chaîne automatisée ? | `docs/INTEGRATION.fr.md` |
| **Le coût opérationnel d'une attestation par dossier** est-il tenable ? | `sign.py` |

**La question qui compte.** Signer un dossier demande une clé privée sur le
poste d'un opérateur, et une discipline de custody. **Est-ce compatible avec
la façon dont vos campagnes tournent réellement ?** Si non, c'est une
objection structurelle et nous préférons l'entendre maintenant.

### Pradeep — le raisonnement, et les prémisses

Votre apport précédent portait sur une prémisse, pas sur un bug. C'est
exactement la lecture dont nous avons besoin ici.

| À éprouver | Où |
|---|---|
| **La dérivation du niveau** est-elle honnête, ou y a-t-il un chemin vers un faux `cryptographically_attested` ? | `verify_attestation.py` |
| L'équivalence du profil de canonicalisation à RFC 8785 **tient-elle sur son domaine** ? | `canonical.py` |
| `rotated` contre `compromised` : la rétroactivité est-elle correctement raisonnée ? | `docs/ATTESTATION.fr.md` |
| Une ligne `NOT TESTED` est-elle jamais utilisée pour **masquer** un échec ? | partout |

**La question qui compte.** Nous affirmons qu'une frontière de comparabilité
ne doit pas mordre sur une empreinte. **Est-ce un raisonnement solide, ou une
commodité que nous nous sommes accordée ?**

### Patrick — la position d'un auditeur qui arrive sans contexte

*Nous n'avons pas de trace d'un travail antérieur de votre part sur ce
produit. C'est précisément la raison de ce périmètre : vous êtes le seul à
pouvoir juger ce que vaut le dossier pour quelqu'un qui n'a aucun contexte.*

| À éprouver | Où |
|---|---|
| Le guide de l'auditeur suffit-il **seul**, sans nous poser de question ? | `examples/dossier-v1/LISEZ-MOI.fr.md` |
| Les résultats attendus correspondent-ils à ce que vous obtenez ? | les cinq commandes |
| Quelque chose se **lit** comme une garantie plus forte qu'elle ne l'est ? | toute la sortie |
| **Les quatre tentatives pour nous mettre en défaut** aboutissent-elles ? | section dédiée du guide |

**La question qui compte.** Un dossier de preuve qui a besoin de son auteur
pour être compris n'est pas un dossier de preuve. **Y arrivez-vous seul ?**

### Daniel — la cohérence avec la mesure, et les signaux

| À éprouver | Où |
|---|---|
| Un dossier exporté reflète-t-il fidèlement ce que la mesure a produit ? | `verify.py`, contrôles de cardinalité et de nullité |
| Un signal `null` reste-t-il bien **non mesuré**, jamais zéro ? | contrôle `coherence des signaux nuls` |
| Les frontières de comparabilité sont-elles les bonnes ? | `measurement_version`, couverture |
| Le vocabulaire dit-il ce que les signaux **mesurent réellement** ? | `docs/BINDING.fr.md`, section terminologie |

**La question qui compte.** Nous écrivons que `stability_score` est un
**agrégat** et non un signal, et nous refusons de le comparer à un score
tiers sans connaître les définitions. **Est-ce exact, et suffisant ?**

---

## Les huit suites, à relancer si vous le souhaitez

```sh
python verify.py <archive> --corpus <corpus>        # 19 PASS, 0 FAIL, 2 NOT TESTED
python tests/test_falsification.py <archive> <corpus>   # 10/10
python tests/test_adversarial.py <archive> <corpus>     # 13 detectes, 2 limites
python tests/test_binding.py <archive> examples/binding # 0 probleme
python tests/test_attestation.py <archive> <corpus>     # 25/25
python tests/test_timestamp.py                          # 21/21, hors reseau
python tests/test_reconciliation.py                     # 24/24, autonome
python tests/test_timestamp_network.py                  # 3/3, RESEAU, jamais en CI
```

La CI exécute les sept premières sur **Python 3.11, 3.12 et 3.13** à chaque
*pull request*. La huitième ne tourne jamais en CI : elle dépend de quatre
serveurs tiers, et une CI rouge sans cause interne apprend à ignorer le rouge.

---

## Comment nous transmettre une objection

**Un contre-exemple reproductible vaut mieux qu'une opinion.** Si vous
trouvez un chemin vers un verdict faux, la forme la plus utile est :

1. le fichier ou la commande qui le produit ;
2. ce que l'outil a répondu ;
3. ce qu'il aurait dû répondre, selon vous.

Si votre objection porte sur une **prémisse** plutôt que sur un
comportement — comme « vous ne devriez pas appeler cela une garantie » —
dites-le sous cette forme. Ce sont les objections les plus utiles, et les
plus difficiles à trouver seuls.

---

## Ce que la revue ne peut pas établir

Elle porte sur un dossier **synthétique** et une clé **de démonstration**.
Elle ne dira pas si le produit tient sur un dossier de pilote réel — personne
n'en a encore soumis un. C'est la condition **B-3** de la fiche produit, et
elle reste **bloquante** pour une offre commerciale.

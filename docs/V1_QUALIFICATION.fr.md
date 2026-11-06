<sub>🇬🇧 <a href="V1_QUALIFICATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Qualification V1 — les huit conditions, et deux verdicts

**6 novembre 2026.** Clôture du sprint de qualification ouvert contre les
huit conditions de [`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md), avant la
revue externe du **lundi 9 novembre**.

> **Principe directeur : aucun RESOLVED de convenance.** Une condition n'est
> levée que par un résultat effectivement constaté. Trois des huit sont
> résolues, quatre partielles, une bloquée — et le blocage n'est pas
> technique.

---

## La matrice

| | Condition | État initial | Critère exact de résolution | Ce qui a été fait | Responsable | Preuve | État final |
|---|---|---|---|---|---|---|---|
| **B-1** | Trancher l'identité juridique du signataire | `legal_capacity_to_attest: "unverified"`, rapporté à chaque exécution | l'entité est **nommée** avec son enregistrement, le **représentant habilité** est consigné et son pouvoir **contrôlé sur les statuts**, et une **décision humaine datée** existe | [`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md) partie A : les cinq rôles séparés, les trois entités candidates avec ce que chacune signifierait, l'organisation GitHub **écartée** comme n'étant pas une personne juridique, et le verrou en trois temps | **Sébastien** — juridique, pas technique | la politique ; le champ dit toujours `unverified` | 🔴 **BLOQUÉE** — attend une décision qu'aucun code ne prend |
| **B-2** | Une clé de production, et sa garde | aucune clé de production ; tout signé avec des clés de test éphémères détruites | une procédure écrite couvrant génération, garde, sauvegarde, rotation, révocation et traçabilité — **et** B-1 tranchée, puisqu'une clé est détenue au nom d'une entité | [`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md) partie B : convention de `kid` jamais réutilisé, asymétrie `rotated`/`compromised` et sa rétroactivité, « ne jamais révoquer à sec », et trois manques nommés | Sébastien, puis un opérateur | la procédure ; **aucune clé générée** | 🟠 **PARTIELLE** — procédure écrite, attend B-1 |
| **B-3** | Éprouver la chaîne sur un dossier réel | aucune fonction jamais exercée sur un dossier réel | au moins une fonction exercée sur un dossier **produit par un tiers**, avec le résultat énoncé comme constaté | un dossier réel de 22 fichiers, reçu le 30 octobre, examiné le 6 novembre : **21 empreintes déclarées recalculées, 21 concordantes**. `verify.py` refuse (pas de manifeste Evidence) par un verdict motivé. `sign.py` refuse — **et le refus est juste**. Un défaut réel trouvé et corrigé ; un défaut de robustesse trouvé et corrigé | ingénieur principal | le balayage ; `tests/test_bom.py` 11/11 ; `tests/test_reconciliation.py` 27/27 | 🟢 **RÉSOLUE** — avec une limite nommée, plus bas |
| **C-4** | Obtenir une preuve d'horodatage confirmée | 4 attestations `PENDING`, 0 Bitcoin ; aucune date attestée | au moins une attestation **Bitcoin** présente dans les octets d'une preuve, liée à son sujet, l'original intact | `upgrade` lancé sur la preuve soumise le 5 novembre à 21:52Z : **blocs 974714 et 974715**. `verify` rend `5 PASS, 0 FAIL, 2 NOT TESTED` ; `--strict` sort en **0**, là où la preuve V1 encore pendante sort en **2** | ingénieur principal | `examples/timestamp/…jws.confirmed.ots`, commitée ; `tests/test_timestamp.py` 25/25, cas 26–29 | 🟢 **RÉSOLUE** |
| **C-5** | Publier le magasin sur un second canal | magasin et dossier viennent de la **même source** | l'empreinte du magasin publiée sur un canal indépendant, **après** un audit de contenu validé par le représentant de B-1 | [`TRUST_STORE_PUBLICATION.fr.md`](TRUST_STORE_PUBLICATION.fr.md) : la conception à deux canaux, le chemin d'authenticité, ce qu'elle n'établit toujours pas, et un audit de contenu en sept points. Un préalable constaté : `store_version` manque réellement — `changes` existe mais c'est un relevé, pas une version comparable, **et aucun code ne le lit** | Sébastien (validation), puis l'ingénierie | la conception ; les deux préalables **construits** le 6 nov (`store_version`, `--store-digest`) ; **rien de publié** | 🟠 **PARTIELLE** — non fermable avant B-1 |
| **C-6** | Traduire la sortie des vérificateurs | français seulement | un auditeur parvient à un verdict en anglais, avec états, ordre, codes de sortie, noms de champs et empreintes **identiques** | `--lang en` sur `verify.py` et `verify_attestation.py`. Couverture **mesurée** : `tests/test_i18n.py` échoue sur toute prose française non traduite, sur une archive valide **et sept régimes d'échec** | ingénieur principal | `tests/test_i18n.py` 25/25, en CI ; [`I18N.fr.md`](I18N.fr.md) | 🟢 **RÉSOLUE** le 6 nov — les **7** outils, voir [`V1_CLOSURE_PLAN.fr.md`](V1_CLOSURE_PLAN.fr.md) |
| **D-7** | Recevoir le dossier CP8 complet | consigné comme « non transmis » | le dossier inventorié par classe, et une liste **exacte** de ce qu'il faut demander | le dossier **était arrivé** le 5 novembre — la fiche antérieure se trompait, et c'est le seul énoncé de ce sprint trouvé faux. Inventaire tenu en privé : 5 objets reçus, **1 recalcul indépendant réussi** (`receipt_hash` CONCORDANT), **11 empreintes citées sans référent**, **0 signature vérifiée de part et d'autre** | ingénieur principal ; puis Dennis | l'inventaire privé ; six demandes hiérarchisées | 🟠 **PARTIELLE** — se ferme sur les deux premières demandes |
| **D-8** | Décider de l'ancrage tiers et de son coût | non tranché | une ADR séparant les quatre prétentions temporelles, avec une politique V1 minimale et le coût d'exploitation énoncé | [`ADR-001-ANCHORING.fr.md`](ADR-001-ANCHORING.fr.md), **ACCEPTÉE** : les quatre prétentions, pourquoi une date déclarée ne vaut rien, pourquoi une hauteur de bloc n'est pas une date, la politique V1, et quatre solutions écartées | ingénieur principal | l'ADR ; les deux preuves du dépôt montrent les deux bouts | 🟢 **RÉSOLUE** |

**Trois résolues, quatre partielles, une bloquée** — au matin du
6 novembre. C-6 s'est fermée le même jour ; l'état courant est dans
[`V1_CLOSURE_PLAN.fr.md`](V1_CLOSURE_PLAN.fr.md).

---

## La dépendance qui décide du reste

B-1 n'est pas une condition parmi huit. Elle en conditionne trois.

```
B-1  identité juridique  ──┬──>  B-2  une clé est détenue au nom d'une entité
     (pas technique)       └──>  C-5  l'audit de contenu demande un
                                  représentant pour le valider
```

La procédure de B-2 est écrite et la conception de C-5 est dessinée ;
aucune ne peut se fermer sans une décision qui appartient à Sébastien et à
l'entité, pas à ce dépôt. **Écrire plus de code n'en déplace aucune.**

---

## Ce qui a été trouvé sans qu'on le cherche

Quatre choses, toutes venues de matériel réel et non de fixtures. C'est la
substance de ce sprint.

### 1. Un défaut réel de l'adaptateur de réconciliation — le premier trouvé par un dossier réel

Le reçu CP8 porte **six étiquettes dupliquées** : « Verifier A » désigne à
la fois la fixture vulnérable et la patchée. `compare_un_champ` prenait la
première correspondance, **sans le dire** — produisant un rapport de
réconciliation possiblement faux, sans aucun signe. Une correspondance peut
désormais viser un `receipt_source_path`, qui est une vraie clé ; faute de
chemin, une étiquette ambiguë est **refusée**.

**`receipt_label` n'est pas une clé sur un reçu réel.** Aucune fixture ne
l'aurait jamais montré : les fixtures, c'est nous qui les écrivons.

### 2. Quinze des vingt-deux fichiers réels portent un BOM UTF-8

Parce que le collecteur est un script PowerShell. Trois de nos entrées
cassaient dessus — et la pire était `receipt_import`, qui **refusait un reçu
JSON parfaitement valide comme « illisible »**. Un partenaire exportant sous
Windows aurait vu son reçu rejeté, avec un message accusant son fichier.

Et le piège du correctif : le BOM est retiré **pour l'analyse seulement**.
Dépouiller les octets en amont aurait paru plus propre et aurait faussé
l'empreinte de chaque fichier reçu.

### 3. Une empreinte sans référent récupérable

Le raisonnement du dossier CP8 repose sur un journal d'audit signé qu'il
tient pour canonique. Son empreinte est bien confirmée dans notre registre
d'intégrité, avec émetteur et heure d'émission — et notre propre page de
vérification énonce que **le contenu d'un document n'est jamais conservé**.

L'empreinte atteste donc l'**existence et l'émission, pas le contenu**. La
valeur `g_score = 0,3863` est par conséquent au niveau `declared`, et non
`reference_verifiable`, malgré une empreinte et une URL qui répondent toutes
deux. C'est exactement la distinction que ce produit existe pour tracer,
appliquée à notre propre registre.

### 4. Que `sign.py` refuse une archive réelle est le bon comportement

L'objet signé tire `observation_count` d'un manifeste Evidence. Sur une
archive étrangère il signerait « 0 » au-dessus de sept observations — **un
énoncé signé FAUX**. Mieux vaut refuser.

Mais ce refus révèle le vrai manque, ci-dessous.

---

## Le verrou que B-3 a révélé, et n'a pas levé

Evidence consomme des dossiers **exportés** par NeoMundi. Une collecte de
réponses brutes n'en est pas un, et **aucun composant de ce dépôt ne
convertit l'un en l'autre.**

C'est le chaînon manquant entre « un dossier réel existe » et « Evidence le
qualifie » — c'est-à-dire entre une démonstration et un pilote. Il est
nommé, pas comblé : le combler serait une fonctionnalité, et ce sprint
n'était pas pour les fonctionnalités.

**Conséquence pour une offre : le chemin d'entrée d'un pilote n'existe pas
encore.**

---

## Verdict 1 — démonstration externe du lundi 9 novembre

# 🟢 GO

La démonstration repose sur ce qui est dans le dépôt et vérifiable par un
relecteur seul.

| Ce qui est démontrable lundi | Preuve |
|---|---|
| Intégrité d'un dossier, 21 contrôles, trois états jamais fusionnés | `19 PASS, 0 FAIL, 2 NOT TESTED` |
| Vérification autonome, hors ligne, **sans dépendance**, et un seul fichier suffit | cas 10 de la suite FR/EN |
| Attestation Ed25519, niveau `cryptographically_attested` atteint | 10 PASS, 5 NOT TESTED |
| **Une preuve d'horodatage réellement confirmée par Bitcoin**, blocs 974714 / 974715 | `5 PASS, 0 FAIL, 2 NOT TESTED` |
| Le cycle `PENDING` → confirmé, **visible aux deux bouts** | deux preuves côte à côte ; `--strict` rend 2 et 0 |
| Un auditeur anglophone parvient à un verdict | `--lang en`, couverture mesurée |
| La réconciliation refuse une étiquette ambiguë plutôt que de deviner | cas 19b–19d |
| **Un dossier réel et tiers, 21 empreintes recalculées** | et deux refus qui sont justes |

Dix suites vertes : verify 19/0/2 · falsification 10/10 · hostile 13
détectés, 2 limites · attestation 22/22 · liaison 0 problème · horodatage
25/25 · réconciliation 27/27 · BOM 11/11 · FR/EN 21/21 · no-CRLF 0 problème.

**Ce qu'il faut dire à voix haute en ouvrant la démonstration**, dans ces
termes :

- le dossier de démonstration est **synthétique** ; la clé de signature
  était une **clé de démonstration éphémère, détruite** ;
- la preuve confirmée est **réelle**, et ce qu'elle établit est une **borne
  supérieure** sur le temps, pas une date que nous vérifions ;
- la **capacité juridique du signataire n'est pas vérifiée**, et le
  vérificateur le dit à chaque exécution ;
- `timestamp.py`, `bind.py` et `reconcile.py` **impriment encore du
  français**.

---

## Verdict 2 — qualification sur un dossier client réel

# 🔴 NO-GO

Non parce que la chaîne a échoué sur un dossier réel, mais à cause de ce que
le dossier réel a montré.

| Verrou | Pourquoi il bloque |
|---|---|
| **Aucun chemin d'entrée** | Evidence consomme un dossier *exporté*. Un client arrive avec des réponses brutes, et rien ne les convertit. Sans cela, aucun dossier client ne peut entrer dans la chaîne. |
| **B-1 non tranchée** | une attestation de production serait émise au nom d'une entité qui n'a pas décidé de s'engager. Chaque dossier signé emporterait le défaut. |
| **Aucune clé de production, aucune garde** | B-2 attend B-1. Tout ce qui est signé reste une démonstration. |
| **Onze empreintes citées sans référent, sur le seul dossier partenaire réel** | la réconciliation n'y est pas exerçable : aucune empreinte commune avec une archive Evidence, et le refus est juste |

### Ce qui en ferait un GO

Dans cet ordre, et seul le premier ne dépend que de nous :

1. **Un chemin d'import** — d'une collecte réelle vers un dossier Evidence.
   Le seul point purement technique de cette liste, et celui qui débloque
   tout l'aval.
2. **B-1** — la décision d'identité juridique. Pas technique, et elle
   conditionne B-2 et C-5.
3. **Les deux premières demandes CP8** — le journal d'audit signé, et le
   paquet avec son `manifest.sha256`. Alors la réconciliation pourra être
   exercée sur l'objet pour lequel elle a été conçue.

**Rien dans cette liste n'est du code qu'on nous a demandé d'écrire durant
ce sprint.** C'est la conclusion honnête d'un sprint de qualification : ce
qui reste n'est pas un effort d'ingénierie, c'est trois décisions et une
fonctionnalité.

---

## Ordre de fusion

| | Commit | Contenu |
|---|---|---|
| 1 | `939fb4d` | C-4 — la preuve confirmée ; le défaut d'étiquette ambiguë |
| 2 | `8e559c9` | B-3 — le dossier réel ; le défaut du BOM |
| 3 | `2671636` | B-1, B-2, C-5, D-8 — les quatre documents de politique |
| 4 | `38fd68e` | C-6 — sortie bilingue |
| 5 | ce document, et la correction de la fiche produit |

Une seule branche, `feat/evidence-v1-qualification`, partie de `main` =
`e8d8f64`. La CI exécute les dix suites sur Python 3.11, 3.12 et 3.13.
**Aucun déploiement, et aucune fusion sans validation.**

### Ce qui n'est PAS dans ce dépôt

L'inventaire de complétude CP8 (**D-7**) est tenu en privé : il nomme des
artefacts privés, et le dossier a été fourni pour une analyse privée. Rien
de lui — aucun fichier, aucune empreinte — n'est dans le dépôt public.

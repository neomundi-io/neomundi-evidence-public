<sub>🇬🇧 <a href="V1_CANDIDATE.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# NeoMundi Evidence V1 — fiche produit candidate

**6 novembre 2026.** Candidate soumise à la revue externe du **lundi
9 novembre**. Protocole de revue :
[`V1_REVIEW_PROTOCOL.fr.md`](V1_REVIEW_PROTOCOL.fr.md).

---

## En une phrase

> Evidence transforme un dossier de mesure NeoMundi en un dossier que
> **votre auditeur vérifie lui-même, hors ligne, sans nous faire confiance** —
> et qui dit en clair ce qu'il ne prouve pas.

---

## Les quatre niveaux de garantie

C'est l'échelle que tout le produit sert, et le vérificateur **dérive** le
niveau — il ne le lit jamais dans un document.

| Niveau | Signifie | Atteignable |
|---|---|---|
| `declared` | écrit dans un document ; rien de recalculé | oui |
| `reference_verifiable` | un fichier est là, et ses octets se hachent sur une empreinte que l'enregistrement déclare | **oui** |
| `cryptographically_attested` | une signature d'une clé identifiée vérifie | **oui, depuis le 5 novembre** |
| `not_demonstrable` | hors de portée de tout contrôle local | un constat, pas un acquis |

**Un dossier qui se revendique mieux qu'il ne l'est est refusé.** C'est le
contrôle central : sans lui, il suffirait d'écrire un mot dans un fichier
texte pour qu'un document ait l'air d'une preuve.

---

## Les cinq outils

| Outil | Ce qu'il fait | Dépendance |
|---|---|---|
| `verify.py` | 21 contrôles d'intégrité d'un dossier | **aucune** |
| `bind.py` | lie une observation à ses artefacts externes | aucune |
| `sign.py` · `verify_attestation.py` | attestation **Ed25519** détachée | `cryptography`, **optionnelle** côté vérification |
| `timestamp.py` | horodatage **OpenTimestamps** détaché | aucune pour la liaison |
| `adapters/` | réconciliation avec un dossier externe | aucune |

**Un seul paquet tiers dans tout le produit** — `cryptography` — et il est
**optionnel** : absent, la ligne de signature rend `NOT TESTED`, jamais
`PASS`. Les 21 contrôles d'intégrité, eux, n'importent que la bibliothèque
standard.

---

## Garanties DÉMONTRÉES

Chacune a été exécutée, et le chiffre cité est celui obtenu — pas une
estimation.

| Garantie | Preuve |
|---|---|
| **Intégrité d'un dossier**, 21 contrôles, trois états jamais fusionnés | `19 PASS, 0 FAIL, 2 NOT TESTED` sur le dossier de démonstration |
| **Un dossier altéré est refusé** | 10 altérations sur 10 détectées ; 15 archives hostiles sur 15 reçoivent un verdict |
| **Vérification autonome**, hors ligne, sans dépendance | bilan identique avec `cryptography` et `opentimestamps` bloqués |
| **Aucune entrée malformée ne fait planter** l'outil | 9 entrées malformées sur 9 rendent un verdict motivé |
| **Un artefact offert est celui auquel l'enregistrement se réfère** | liaison par recalcul d'empreinte, 17 manifestes fautifs refusés |
| **Une partie identifiée s'est engagée** sur l'empreinte d'un dossier | Ed25519/JWS détaché, niveau `cryptographically_attested` atteint |
| **Une archive recalculée après suppression est détectée** | `verify.py` seul : 0 FAIL ; l'attestation : FAIL |
| **Une preuve d'horodatage est liée au dossier**, sans dépendance | liaison lue à offset fixe, 21 cas de test |
| **Un reçu externe est confronté sans être cru** | 5 statuts distingués, contradictions conservées |
| **Vérification par un outil qui n'est pas le nôtre** | `openssl pkeyutl -verify` valide la même signature |
| **Un consommateur automatisé ne peut pas se tromper** | `--strict` : codes 0 / 1 / 2, sans changer aucun verdict |

### Et une limite déclarée qui s'est refermée

Depuis le 5 novembre, la suite de falsification portait une limite assumée :
« une observation effacée partout, décomptes et sommes refaits » était
**indétectable à l'intérieur** de l'archive. L'attestation la détecte.
**C'est la première fois qu'une limite déclarée du produit se referme.**

---

## Garanties EN ATTENTE

Elles ne sont ni abandonnées ni acquises. Ce qui manque est nommé.

| Garantie | Ce qui manque | Délai réaliste |
|---|---|---|
| **Une date attestée** | la confirmation Bitcoin de la preuve `PENDING` | **quelques heures** après `upgrade` |
| **Le temps vérifié par nous** | un en-tête de bloc, donc une source de confiance | hors périmètre — délégué à `ots verify` |
| **Une clé de production** | la décision d'identité juridique, et une custody | **avant tout pilote payant** |
| **Un magasin de confiance publié** | un second canal de publication, et son audit | semaines |
| **L'adaptateur éprouvé sur un dossier réel** | le dossier complet d'un pilote externe | dépend du pilote |
| **Le rejeu d'une mesure** | des évaluateurs déterministes — `NO-GO` en l'état | voir `REPLAY_FEASIBILITY` |

---

## Fonctions NON VALIDÉES sur des dossiers réels

C'est la section la plus importante de cette fiche, et elle doit être lue
avant toute offre.

> **Aucune des cinq fonctions n'a été exercée sur un dossier de pilote
> réel.** Tout ce qui est démontré ci-dessus l'a été sur des **fixtures
> synthétiques** et une **clé de démonstration détruite**.

| Fonction | Éprouvée sur | Jamais éprouvée sur |
|---|---|---|
| Intégrité | archives de démonstration GROUNDED-S1 et MED, fixture synthétique | un dossier produit par un pilote |
| Attestation | clé de **test**, archives de démonstration | une clé de production, une custody réelle |
| Horodatage | une preuve réelle, mais **`PENDING`** | une preuve **confirmée** |
| Liaison | artefacts synthétiques | les artefacts d'un pilote |
| Réconciliation | un reçu **inventé**, **et le vrai reçu CP8** | une archive portant une empreinte commune avec lui — voir plus bas |

Et trois faits qu'il faut dire tels quels :

- **le dossier de Dennis Christie est arrivé le 5 novembre** —
  `RECONCILIATION.md` et les deux reçus. Une édition antérieure de cette
  fiche disait qu'il n'avait pas été reçu ; c'était vrai à l'écriture et ne
  l'est plus. L'inventaire complet est la condition **D-7**, tenu en privé :
  onze empreintes y sont **citées sans qu'aucun référent soit fourni**, et le
  journal d'audit signé que le dossier tient pour canonique est
  **irrécupérable chez nous** — notre propre page de vérification énonce que
  le contenu d'un document n'est jamais conservé.
- **un dossier réel et tiers a été éprouvé le 6 novembre** — 21 empreintes
  déclarées recalculées, 21 concordantes. Le niveau `reference_verifiable`
  est donc atteint sur des artefacts réels. Mais `verify.py` et `sign.py` le
  **refusent** tous deux, et le second refus est juste : l'objet signé tire
  `observation_count` d'un manifeste Evidence, et sur une archive étrangère
  il signerait « 0 » au-dessus de sept observations.
- **la capacité juridique du signataire n'est pas vérifiée**, et aucun code ne
  l'établira.

---

## Ce qu'il ne faut jamais revendiquer

Sept phrases, et les trois premières sont celles qui tenteraient le plus.

1. **« Preuve que l'exécution a eu lieu. »** Jamais. Lier un artefact à un
   enregistrement ne dit ni que l'exécution a eu lieu, ni quand, ni chez qui.
2. **« Horodaté »** au sens d'une date établie. La preuve est `PENDING` :
   **aucune date n'est attestée.**
3. **« Signé »**, pour un document dont la signature n'a pas été vérifiée.
4. **« Horodatage qualifié eIDAS. »** OpenTimestamps n'est pas un prestataire
   de services de confiance qualifié.
5. **« Reproductible »** au sens du calcul. Le gel garantit les entrées, pas
   que la mesure se refasse à l'identique.
6. **« Validation médicale, juridique ou factuelle. »** Une mesure est une
   mesure.
7. **« Dossier infalsifiable. »** Un faussaire qui reconstruit l'archive
   **et** l'attestation produit un ensemble cohérent, si sa clé est de
   confiance. Seule une empreinte conservée ailleurs, ou une clé dont la
   custody est maîtrisée, le détecte.

---

## Les dernières conditions avant une offre commerciale pilote

Par ordre de blocage décroissant. Les trois premières sont **bloquantes**.

### 🔴 B-1 — Trancher l'identité juridique du signataire

`trust-store.json` porte aujourd'hui `legal_capacity_to_attest:
"unverified"` pour NeoMundi Recherche, et le vérificateur le rapporte à
chaque exécution.

**Signer est un engagement.** Laquelle des trois entités s'engage —
association FR, Sàrl suisse, ou organisation GitHub ? La question est
**juridique avant d'être technique**, et aucune ligne de code ne la tranchera.

*Sans cette décision, une attestation de production ne peut pas être émise.*

### 🔴 B-2 — Une clé de production, et sa custody

Aucune clé de production n'existe. Il faut : la générer hors ligne, la placer
dans le magasin DPAPI du poste, une sauvegarde hors machine, et une
**procédure de rotation écrite** — y compris la distinction `rotated` /
`compromised`, puisque la seconde invalide **toutes** les signatures
antérieures.

*Sans cela, tout ce qui est signé reste une démonstration.*

### 🔴 B-3 — Éprouver la chaîne sur **un** dossier de pilote réel

Un seul suffirait, et il n'y en a aucun. Tant qu'aucune fonction n'a été
exercée sur un dossier produit par un pilote, « cela fonctionne » est une
**extrapolation**, pas un constat.

*C'est la condition qui sépare une démonstration d'un produit.*

### 🟠 C-4 — Obtenir au moins une preuve d'horodatage **confirmée**

Un `upgrade` quelques heures après le scellement. Jusque-là, « horodaté » ne
peut pas être écrit dans une offre.

### 🟠 C-5 — Publier le magasin de confiance sur un second canal

Aujourd'hui, un auditeur qui télécharge le magasin et le dossier les obtient
de la **même source**. Publier l'empreinte du magasin ailleurs — le `.org`, la
carte MCP — lève cette faiblesse. **Après audit de ce qui y est exposé.**

### 🟠 C-6 — Traduire la sortie des vérificateurs

Elle est en français ; la documentation est bilingue. Un auditeur anglophone
lit aujourd'hui des chaînes qu'il ne comprend pas. Le rapport JSON atténue, il
ne remplace pas.

### 🟡 D-7 — Recevoir le dossier CP8 complet

`RECONCILIATION.md` et le reçu lui-même. L'adaptateur est prêt ; il n'a pas
été éprouvé sur l'objet pour lequel il a été conçu.

### 🟡 D-8 — Décider de l'ancrage tiers, et de son coût opérationnel

OpenTimestamps est gratuit et sans compte, mais il introduit une **soumission
réseau** et une attente de confirmation. À arbitrer avant de le promettre
dans un contrat.

---

## État de la candidate

| | |
|---|---|
| Branche | `feat/evidence-v1-candidate` |
| Partie de | `main` = `15ac159` |
| CI | **5 contrôles verts**, Python 3.11 / 3.12 / 3.13 |
| Suites | **8 suites**, voir le protocole de revue |
| Dossier de démonstration | `examples/dossier-v1/` — entièrement synthétique |
| Démonstration | `demo_v1_5min.sh` — 12 écrans, hors ligne |
| Déploiement | **aucun** |

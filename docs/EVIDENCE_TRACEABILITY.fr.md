# NeoMundi Evidence — carte de traçabilité

**7 novembre 2026.** Comment un artefact circule, ce qui lui est attaché, et
ce que chaque couche établit ou non.

Chaîne : **Mesure → Observation → Registre → Export → Attestation →
Vérification.**

L'exemple travaillé est **Q-2**, la référence expérimentale figée. Son dossier
est privé ; les identifiants et empreintes ci-dessous en sont cités.

---

## 1. Étape par étape

### Mesure

| | |
|---|---|
| **Identifiant** | `meas-02c6a7f1bf3b0f99…` |
| **Produit** | cinq signaux, `measurement_version 3.3.1`, `checks_emitted 3` |
| **Liens de provenance** | contient l'`observation_id` ; l'enregistrement de couverture porte l'évaluateur de chaque signal |
| **Contrôles disponibles** | les signaux sont confrontés à `measured_signals` |
| **Observé** | `status measured`, aucun refus |
| **Limite** | aucune réponse de l'API ne porte la **révision de code** qui l'a produite — une trace externe est requise, et c'est le rôle de Station |

### Observation

| | |
|---|---|
| **Identifiant** | `obs-02c6a7f1bf3b0f99…` — **dérivé** de la campagne, du créneau et de l'index de répétition |
| **Produit** | `prompt_sha256 8b6d6fe6…`, `response_sha256 6ec418cb…`, `model_served`, latence, jetons |
| **Liens** | `run_id`, `campaign_sha256 4a6deb10…`, `plan_sha256 c3f7aaf8…` |
| **Limite** | l'identifiant **ne distingue pas** deux exécutions du même créneau. Seuls `run_id` et les horodatages le font |

### Registre

| | |
|---|---|
| **Produit** | 6 enregistrements, en ajout seul, chaînés |
| **Empreinte** | tête `a3fdf598…` |
| **Contrôle** | `station ledger verify --path <registre>` — recalculé par l'instrument qui l'a écrit |
| **Observé** | aucune anomalie |
| **Limite** | le chaînage attrape une altération **incohérente** ; une réécriture complète produirait une chaîne valide |

🔴 Le registre conserve `response_text`. L'export non. Voir §4.

### Export

| | |
|---|---|
| **Produit** | `station.export.campagne/3`, 9 membres |
| **Empreinte** | `8f1d7259a1b260e1…` |
| **Contrôle** | `python verify.py` — 8 empreintes de membres déclarées, recalculées |
| **Observé** | 17 PASS, 0 FAIL, 4 NOT TESTED |
| **Limite** | l'archive ne déclare **ni** le nombre d'enregistrements exportés **ni** les types exclus. *Une chaîne valide ne dit rien de ce qui n'a pas été exporté.* |

### Attestation

| | |
|---|---|
| **Produit** | `campagne-q2.jws`, `1fec125c…` |
| **Clé** | `nm-ev-recherche-202611-1`, EdDSA/Ed25519 |
| **Entrée signée** | **2003 octets** = `base64url(en-tête)` (82) + `.` + `base64url(charge)` (1920) |
| **Charge canonique** | **1440 octets**, profil `neomundi-jcs-strings/1` |
| **Contrôle** | `python verify_attestation.py … --store-digest … --strict` |
| **Observé** | 11 PASS, 0 FAIL, 4 NOT TESTED, `--strict` code 0 |

🔴 **La signature ne couvre pas les octets de l'archive.** Elle couvre un
document de onze champs qui **contient trois empreintes** de celle-ci :

| Champ de `subject` | Valeur |
|---|---|
| `bundle_sha256` | `8f1d7259a1b260e1…` |
| `manifest_sha256` | `f641130c71b49211…` |
| `checksums_sha256` | `d98d275f09d0f262…` |
| `export_schema` | `station.export.campagne/3` |
| `observation_count` | `"1"` |
| `subject_frozen_at_declared` | `2026-11-06T22:38:48Z` |
| `subject_provenance_declared` | *texte libre fourni par le signataire* |

⚠️ **`subject_provenance_declared` est signé, et reste une déclaration.**
Signer une phrase ne la rend pas vraie : cela établit que **nous** l'avons
écrite et que nous nous y engageons.

Les **réserves sont dans le document signé**, de sorte qu'un vérificateur ne
peut pas les ignorer sans ignorer la signature.

### Vérification

| | |
|---|---|
| **Contrôle** | signature, empreintes de membres, **et l'empreinte du magasin confrontée à un second canal** |
| **Observé** | les octets du magasin se hachent sur `dac94e8a…` ; `mcp.neomundi.org/trust/trust-store-digest.json` déclare la même, HTTP 200 |
| **Limite** | les deux canaux sont sous la **même gouvernance** — ce n'est **pas** un tiers de confiance |

---

## 2. Six couches à ne jamais confondre

| Couche | Établit | N'établit **pas** | Outil |
|---|---|---|---|
| **Intégrité interne** | les membres n'ont pas bougé les uns par rapport aux autres | que l'archive est celle que nous avons produite | `verify.py` |
| **Intégrité de l'archive entière** | le fichier reçu est celui dont l'empreinte a été notée | l'origine, le temps, la vérité | `sha256sum` + une empreinte conservée ailleurs |
| **Attestation** | une partie identifiée s'est engagée sur cette empreinte | la vérité du contenu | `sign.py attest` |
| **Vérification de signature** | la signature est valide sous une clé publique du magasin | qui cette partie est juridiquement | `verify_attestation.py` |
| **Réconciliation** | la concordance champ par champ avec un reçu externe | quelle valeur est juste — **rien n'est tranché** | `adapters/reconcile.py` |
| **Ancrage temporel** | la preuve s'engage sur l'empreinte du sujet | **la date**, tant que la preuve est `PENDING` | `timestamp.py` |

**Démonstration mesurée de la distinction première/troisième** : un octet
ajouté à la fin du ZIP laisse l'intégrité interne à **17 PASS, 0 FAIL** et est
refusé par l'attestation.

---

## 3. Les cinq verdicts de réconciliation

Pas deux. Les réduire à deux retirerait exactement ce qui distingue cet outil
d'un comparateur naïf.

| Verdict | Condition |
|---|---|
| `MATCHED` | les deux valeurs présentes, égales dans `--tolerance` |
| `MISMATCHED` | les deux présentes, différant au-delà de la tolérance — **les deux sont conservées** |
| `MISSING` | le reçu ne porte pas le champ |
| `NOT COMPARABLE` | les deux présentes, mais pas de même nature |
| `NOT VERIFIABLE` | la valeur du reçu n'est pas confrontable à ce que nous détenons |

**Observé** sur la fixture livrée : `4 MATCHED, 2 MISMATCHED, 1 MISSING,
1 NOT COMPARABLE, 1 NOT VERIFIABLE`. Sur un écart, l'outil énonce : *« les
deux valeurs sont conservées telles quelles : rien n'est tranché ici »*.

**Statut** : TESTÉ (27/27) et DÉMONTRÉ sur fixtures. **NON CONFIRMÉ** sur un
reçu réellement produit par un tiers.

---

## 4. Conservé, exporté, publié, vérifiable

| | Texte de la réponse | Empreintes | Qui peut le voir |
|---|---|---|---|
| **Registre Station** | **conservé** | oui | nous |
| **Export** | **absent** | oui | le destinataire |
| **Publié** | — | le magasin de confiance seul | quiconque |
| **Vue du vérificateur** | ce que l'export porte | oui | le destinataire |

🔴 Quatre choses distinctes. *« NeoMundi ne conserve pas les réponses »* est
**faux** — le registre les conserve. *« L'export porte les échanges »* est
**faux** aussi. Ce qui sort est un choix délibéré.

---

## 5. Niveaux de garantie — dérivés, jamais lus

| Niveau | Sens |
|---|---|
| `declared` | l'archive l'affirme ; rien ne le confronte |
| `reference_verifiable` | une empreinte conservée ailleurs permet la confrontation |
| `cryptographically_attested` | une clé identifiée s'est engagée |
| `not_demonstrable` | aucun contrôle ne pourrait l'établir |

Ils sont **calculés par le vérificateur**, jamais lus dans le document : une
archive ne décide pas de son propre niveau.

**Observé** : `bind.py verify` dérive `reference_verifiable` ;
`verify_attestation.py` dérive `cryptographically_attested`.

La provenance a sa propre échelle à trois niveaux —
`instrument_non_documente`, `instrument_declare`,
`instrument_declare_et_configure` — et **il n'y en a pas de quatrième**. Un
test échoue si `instrument_verifie` apparaît.

---

## 6. Liens vers les références de qualification

Q-1 et Q-2 sont **figées** et vivent hors de ce dépôt, dans l'espace privé
versionné de l'opérateur. Leurs manifestes d'intégrité sont `e6dec106…`
(20 fichiers) et `83794b85…` (13 fichiers), vérifiés inchangés le 7 novembre
2026.

| Affirmation tracée ici | Identifiant du registre |
|---|---|
| chaîne, exécution, mesure | `CH-001` … `CH-006`, `ME-001` … `ME-003` |
| les signaux et leur nature | `SI-001` … `SI-009` |
| registre, export, provenance de code | `ST-001` … `ST-008` |
| contrôles Evidence | `EV-001` … `EV-007` |
| attestation | `AT-001` … `AT-006` |
| magasin de confiance, deux canaux | `C5-001` … `C5-003` |
| rejeu et horodatage | `RE-001` … `RE-004`, `FU-001` |
| interdictions explicites | `IN-001` … `IN-004` |

Le registre des 59 affirmations est conservé avec les dossiers de
qualification, non dans ce dépôt : il porte des références à des artefacts
privés.

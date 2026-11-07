# NeoMundi Evidence — préparation de version

**7 novembre 2026.**

---

# READY WITH LIMITATIONS

Les capacités documentées correspondent au code, toute commande publiée a été
exécutée, les scénarios sont reproductibles, les codes de sortie sont
conformes, et les qualifications figées sont intactes.

**Les limites sont réelles, déclarées, et aucune n'est un défaut à corriger
avant la version.**

---

## 1. Pourquoi pas READY

Quatre choses ne sont **pas** confirmées, et une version qui laisserait croire
l'inverse serait fausse :

| | Statut |
|---|---|
| **Ingestion tierce** | TESTÉ sur 16 fixtures ; **aucun paquet tiers réel jamais ingéré** |
| **Réconciliation** | TESTÉ 27/27, DÉMONTRÉ sur fixtures ; **aucun reçu réel réconcilié** |
| **Ancrage temporel** | IMPLÉMENTÉ et TESTÉ ; la preuve livrée est **`PENDING`** — aucune date attestée, aucune qualification eIDAS |
| **Q-2** | verdict global **`PARTIAL`**, et il le reste |

## 2. Pourquoi pas NOT READY

| Critère | État |
|---|---|
| Les capacités documentées correspondent au code | **oui** — chaque commande exécutée |
| Commandes vérifiées | **oui** — 12 opérations, codes mesurés |
| Démonstration reproductible | **oui** — 15 suites vertes, 13 codes attendus conformes |
| Résultats traçables | **oui** — identifiants, empreintes et contrôles cartographiés |
| Réserves explicites | **oui** — un document dédié, rien d'adouci |
| Tests pertinents exécutés | **oui** — la séquence de CI rejouée localement |
| Documents cohérents | **oui** — six points d'entrée, dans les deux langues |
| Qualifications historiques intactes | **oui** — Q-1 20/20, Q-2 13/13, manifestes inchangés |
| Décision justifiée | **ce document** |

**Deux échecs sont survenus et ont été diagnostiqués** : `test_binding` était
une erreur de **procédure** de mon côté — la CI construit d'abord le manifeste
de liaison — et le premier dépôt, livré en anglais seulement, a été **refusé
par la CI** qui impose la paire EN/FR. Les six contreparties ont été écrites.
**Aucun critère de réussite n'a été modifié**, et la liste d'exceptions de la
CI n'a pas été élargie.

---

## 3. Ce qu'une version peut affirmer

- un **vérificateur qui tourne sans rien installer**, rendant **trois** états
  et jamais un verdict binaire ;
- une **attestation Ed25519** vérifiable hors ligne, **sans aucune clé
  privée**, dont les réserves sont **dans** le document signé ;
- un **magasin de confiance** confrontable par deux canaux techniquement
  indépendants — *sous la même gouvernance* ;
- **quatre couches de vérification** qui attrapent des choses différentes,
  démontrées — dont deux altérations que `verify.py` seul **ne** voit **pas** ;
- **cinq verdicts de réconciliation**, qui confrontent sans trancher ;
- **des refus qui fonctionnent** : une clé de test n'accorde rien, une
  observation inconnue est refusée, une clé privée ne peut pas être écrite sous
  la racine du dépôt.

## 4. Ce qu'une version ne doit pas affirmer

🔴 Aucun **taux de détection** sans nommer sa batterie — « 10/10 » appartient
à dix altérations nommées · aucune **date** depuis une preuve `PENDING` ·
aucune qualification **eIDAS** · aucune **certification juridique** —
`experimental` est l'opposé de `verified` · aucun **tiers de confiance** — les
deux canaux sont les nôtres · aucune **validation opérationnelle** de
l'ingestion ou de la réconciliation · et **jamais** `PARTIAL` présenté comme
`PASS`.

---

## 5. Suites recommandées, dans l'ordre

1. **résoudre la divergence** entre `test_falsification.py` et le scénario D :
   dire en quoi les deux faussaires diffèrent, ou les aligner ;
2. **ingérer un paquet tiers réel**, et un reçu réel — c'est ce qui fait
   passer deux capacités de TESTÉ à QUALIFIÉ ;
3. **mettre à niveau la preuve d'horodatage** une fois la chaîne confirmée,
   puis rejouer `timestamp.py upgrade` et `verify --strict` : un `PENDING` qui
   devient une attestation Bitcoin est le plus grand gain disponible ;
4. **déclarer le contrat de complétude de l'export** —
   `registre.enregistrements_exportes` et `registre.types_exclus` — ce qui
   referme l'un des trois `NOT TESTED` structurels.

Aucune des quatre ne bloque une version. La troisième est la seule qui
changerait ce que le produit **établit**, plutôt que ce qu'il documente.

---

## 6. Décision

**READY WITH LIMITATIONS**, pour une version documentaire du dépôt public sur
la branche `docs/consolidation-v1-20261107`.

Rien n'est fusionné, rien n'est déployé, rien n'est publié. Les références
figées Q-1 et Q-2 sont inchangées, et le verdict `PARTIAL` tient.

> Achever la documentation ne signifie pas que les limites expérimentales ont
> disparu. Cela signifie qu'elles sont désormais écrites là où un tiers peut
> les lire.

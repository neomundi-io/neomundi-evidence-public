# NeoMundi Evidence — démonstration technique reproductible

**7 novembre 2026.** Chaque résultat ci-dessous a été **observé** à cette
date. Le point de départ est le script livré ; rien n'a été réinventé.

```sh
sh demo_v1_5min.sh
```

🔴 **Tout, dans le dossier de démonstration, est synthétique.** L'archive a
été fabriquée, la clé de signature était une **clé de démonstration éphémère,
détruite depuis**, et le reçu externe est inventé. Aucune donnée de pilote,
aucun jeu de données réel. Le script le dit dans son propre en-tête, et
quiconque le présente doit le répéter.

---

## 1. Artefacts, avec empreintes

| Fichier | Octets | SHA-256 (32 premiers) |
|---|---|---|
| `NEOMUNDI_EVIDENCE_V1_DEMO.zip` | 20 237 | `e31e12bb7e32c7a33db1ecacc8c38cd1` |
| `…zip.jws` | 2 211 | `d533518f4413d75e7ea58923d21bfe6c` |
| `…zip.jws.ots` | 786 | `3c1f7db3248c008c91f40ba1c5ab4d73` |
| `trust-store.json` *(magasin de test)* | 2 815 | `6e6534544d85cf8e6ef83b6a176869e9` |

Les quatre vivent dans `examples/dossier-v1/`. L'empreinte de l'archive a été
recalculée **après** chaque scénario et trouvée inchangée : l'original n'est
jamais ouvert en écriture.

---

## 2. Méthode

Chaque copie altérée est reconstruite en préservant les `ZipInfo` d'origine —
date, méthode de compression, `create_system` — pour que la **seule**
différence soit l'altération visée. Sans cela, le contrôle mesurerait le bruit
de la réécriture.

Les codes de sortie ont été mesurés **sans tube** :
`cmd > /dev/null 2>&1; echo $?`. Un `$?` après un tube rapporte la dernière
étape du tube, pas l'outil. Cette erreur a été commise une fois pendant ce
travail, et corrigée avant toute affirmation.

---

## 3. Scénario A — vérification normale

| # | Commande | Code | Résultat |
|---|---|---|---|
| A1 | `python verify.py <archive> --corpus <corpus>` | **0** | 19 PASS, 0 FAIL, 3 NOT TESTED |
| A2 | `python verify.py <archive>` | **0** | 17 PASS, 0 FAIL, 4 NOT TESTED |
| A3 | `python verify_attestation.py <jws> --archive <archive> --trust-store <magasin> --allow-test-keys` | **0** | 10 PASS, 0 FAIL, 5 NOT TESTED — niveau `cryptographically_attested` |

⚠️ **A1 et A2 diffèrent par le corpus**, non par la qualité. Avec le corpus,
les empreintes des entrées rejouées sont confrontables (4/4) et deux
`NOT TESTED` deviennent `PASS`.

---

## 4. Scénario B — altération interne

Un octet changé **dans** `observations.jsonl`.

```
python verify.py b-interne.zip        ->  code 1
[FAIL] empreintes des 7 membres declares - divergents : ['observations.jsonl']
BILAN : 16 PASS, 1 FAIL, 4 NOT TESTED
```

**Interprétation** : l'empreinte du membre diverge. C'est le cas facile, et
celui que la plupart croient être le seul.

---

## 5. Scénario C — altération externe

Un octet **ajouté à la fin du fichier ZIP**. Aucun membre ne change.

| # | Commande | Code | Résultat |
|---|---|---|---|
| C1 | `verify.py c-queue.zip` | **0** | **17 PASS, 0 FAIL** |
| C2 | `verify_attestation.py <jws> --archive c-queue.zip …` | **1** | `[FAIL] concordance avec l archive` |

Empreinte de l'archive : `5319ac9f…` contre l'original `e31e12bb…`.

🔴 **C'est par conception, non un défaut.** `verify.py` vérifie l'**intégrité
interne** de l'archive ; l'attestation vérifie l'**identité du fichier**. Deux
outils, deux garanties distinctes — et les confondre serait promettre l'une en
ne tenant que l'autre.

---

## 6. Scénario D — une observation retirée, tous les contrôles recalculés

Le cas le plus dur, et reproduit ici **indépendamment du script de
démonstration** : une observation retirée d'`observations.jsonl`, ses lignes
purgées de `measurements.jsonl`, `reference_evaluations.jsonl`,
`replay_provenance.jsonl` et du CSV, les décomptes du manifeste refaits, et
`checksums.sha256` recalculé.

| # | Commande | Code | Résultat |
|---|---|---|---|
| D1 | `verify.py d-amputee.zip` | **0** | **17 PASS, 0 FAIL, 4 NOT TESTED** |
| D2 | `verify_attestation.py <jws> --archive d-amputee.zip …` | **1** | `[FAIL] concordance avec l archive` |

🔴 **Un faussaire soigneux produit une archive intérieurement parfaite.**
`verify.py` seul n'y voit rien. L'attestation de référence la refuse.

⚠️ **Une divergence à connaître.** `tests/test_falsification.py` contient une
amputation comparable et la rapporte comme **détectée**, en la qualifiant de
*« mieux qu'annoncé »*. Les deux faussaires ne sont **pas d'égal soin**, et la
documentation ne dit pas encore en quoi ils diffèrent. En attendant : citer des
**cas**, jamais un taux.

---

## 7. Scénario E — ce que les outils refusent

Une vérification qui ne sait pas refuser n'en est pas une.

| # | Situation | Commande | Code | Message |
|---|---|---|---|---|
| E1 | clé `test`, sans consentement explicite | `verify_attestation.py … <sans --allow-test-keys>` | **1** | *« clé de statut `test` : elle n'accorde aucune attestation »* |
| E2 | magasin non confronté, sous `--strict` | `verify_attestation.py … --strict` | **2** | la ligne du magasin reste `NOT TESTED` |
| E3 | liaison à une observation inconnue | `bind.py build --observation obs-inexistante` | **1** | *« aucune observation 'obs-inexistante' dans l'archive (4 observations présentes) »* |
| E4 | écrire une clé privée sous la racine du dépôt | `sign.py genkey --out <dépôt>/interdite.json` | **1** | *« refus d'écrire une clé privée sous la racine du dépôt »* |

**E4 a été contrôlé deux fois** : le fichier **n'a pas été créé**. Le refus a
lieu *avant* la génération, non après.

### L'équivalent côté Station, consigné dans Q-2

La comparaison des préflights est dans le dossier Q-2 figé et **n'a pas été
rejouée ici** — Station est hors du périmètre de cette mission.

```
A  [warning] STATION_CODE_COMMIT déclare 8d79743… et le dépôt est sur
            91db315… : la variable CONTREDIT le code qui va tourner
B  [ready  ] les preuves nommeront 91db315… — déclaration confrontée au
            dépôt, arbre propre
```

Le cas A est **authentique** : c'est le défaut que Q-1 a laissé passer,
attrapé avant le premier appel.

---

## 8. Scénario F — horodatage

| # | Commande | Code | Résultat |
|---|---|---|---|
| F1 | `timestamp.py inspect <preuve.ots>` | **0** | magie, version 1, SHA-256, 786 octets |
| F2 | `timestamp.py verify <preuve.ots> --subject <jws>` | **0** | **3 PASS, 0 FAIL, 4 NOT TESTED** — la liaison tient |
| F3 | `timestamp.py verify … --strict` | **2** | la preuve est `PENDING` |
| F4 | `timestamp.py verify <preuve.ots> --subject <mauvais fichier>` | **1** | *« la preuve s'engage sur d533518f…, le sujet se hache sur … »* |

🔴 **`PENDING` n'atteste aucune date.** La preuve livrée porte **4
attestations `PENDING` et 0 Bitcoin**. Un `pending` dit qu'un calendrier s'est
engagé à inclure l'empreinte dans une transaction future — rien sur le temps.

🔴 **Aucune qualification eIDAS**, et l'outil **délègue** la vérification du
temps : `ots verify <preuve.ots>`. Valider une attestation Bitcoin demande un
en-tête de bloc, ce qui est une source de confiance que nous n'avons pas.

**F2 et F4 forment la paire utile** : la liaison est vérifiée positivement, et
un mauvais sujet est refusé avec les deux empreintes nommées.

---

## 9. Détection : des cas, pas des taux

| Batterie | Périmètre | Résultat |
|---|---|---|
| `tests/test_falsification.py` | dix altérations nommées | **10/10 détectées**, +1 limite déclarée |
| `tests/test_adversarial.py` | quinze cas | **13 détectés, 2 manques déclarés** |
| Scénario C ci-dessus | octet ajouté en fin | `verify.py` **non**, attestation **oui** |
| Scénario D ci-dessus | amputation + recalcul | `verify.py` **non**, attestation **oui** |
| Q-1, cas adversarial G | provenance réécrite **puis réparée** | **non** — pas même l'attestation |

🔴 **Les cinq lignes sont exactes, et elles ne décrivent pas la même chose.**
La détection dépend entièrement du soin du faussaire. La seule formulation
honnête :

> *Dix altérations types, toutes détectées par le vérificateur seul. Deux
> formes de falsification soignée que seule l'attestation arrête — et une
> qu'aucun contrôle local n'arrête, que nous publions.*

---

## 10. Tout reproduire

```sh
# les cinq démonstrations livrées
sh demo_v1_5min.sh          # intégrité, autonomie, attestation, horodatage, réconciliation
sh demo_5min.sh
sh demo_binding.sh
sh demo_reconciliation.sh
sh demo_timestamp.sh

# la fixture de CI, puis les suites complètes
python tests/make_fixture.py <rép> --profile v2
```

Le workflow `.github/workflows/tests.yml` est la séquence de référence — y
compris un emploi dédié qui bloque `cryptography` et contrôle que `verify.py`
rend le **même** bilan.

⚠️ **Un piège de procédure, rencontré pendant ce travail.**
`tests/test_binding.py` a besoin d'un `manifest.json` que `make_fixture.py` ne
produit **pas** : la CI le construit d'abord par `bind.py build`, en employant
`first_observation_id` de `fixture.json`. Lancer la suite sans cette étape
échoue sur `FileNotFoundError` — une erreur de **procédure**, non un défaut
logiciel.

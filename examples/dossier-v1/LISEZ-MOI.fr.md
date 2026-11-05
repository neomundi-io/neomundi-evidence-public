<sub>🇬🇧 <a href="README.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../../README.fr.md">← README</a></sub>

# Dossier de preuve V1 — guide de l'auditeur

**Tout ce que contient ce répertoire est synthétique.** L'archive a été
fabriquée pour la revue, la clé de signature était une clé de
**démonstration éphémère** et a été **détruite**, et le reçu externe est
inventé. **Aucune donnée de pilote, aucun jeu de données réel.**

Une seule chose n'est pas synthétique : la **preuve d'horodatage**, obtenue
réellement des quatre calendriers publics OpenTimestamps. Son état est
`PENDING`, et **cela n'atteste aucune date**.

---

## Ce que le dossier contient

| Fichier | Octets | Ce que c'est |
|---|---|---|
| `NEOMUNDI_EVIDENCE_V1_DEMO.zip` | 20 237 | le dossier de preuve, 4 observations, 8 membres |
| `corpus/` | 5 fichiers | les entrées rejouées, pour que leurs empreintes se recalculent |
| `…zip.jws` | 2 212 | l'attestation **Ed25519**, détachée |
| `…zip.jws.ots` | 856 | la preuve **OpenTimestamps**, réelle, `PENDING` |
| `…zip.jws.timestamp.json` | 1 173 | le descripteur de l'horodatage |
| `trust-store.json` | 2 878 | **clés publiques seulement**, statut `test` |
| `binding/` | 3 fichiers | une liaison observation ↔ artefacts |
| `receipt-synthetic.html` | 2 837 | un reçu externe **inventé** |
| `map-comparable.json` · `map-no-context.json` | | deux tables de correspondance |
| `reconciliation.md` | 3 021 | le rapport de réconciliation produit |

### Empreintes, à conserver ailleurs qu'avec le dossier

```
archive      e31e12bb7e32c7a33db1ecacc8c38cd18225fa10618c7e1aa5d6f9540f2ad7d6
attestation  265144e307869f000fcd007d2791bb454bbe4f89662b43869ca10babe5f8c8f4
```

**Une empreinte conservée avec le dossier n'atteste rien.** C'est la seule
défense contre un dossier entièrement refabriqué, et elle n'a de valeur que
si vous la gardez séparément — ou si vous vérifiez l'attestation, qui la
couvre.

---

## Les cinq commandes

Aucune n'a besoin du réseau. Aucune n'écrit dans le dossier.

### 1 — Intégrité

```sh
python ../../verify.py NEOMUNDI_EVIDENCE_V1_DEMO.zip --corpus corpus
```

**Attendu : `BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED`**, sur 21 lignes.

Aucune dépendance : `verify.py` n'importe que la bibliothèque standard. Pour
vous en convaincre, bloquez tout et relancez — le bilan est identique.

Les 2 `NOT TESTED` sont le chaînage du registre et l'origine de l'archive :
deux choses qu'aucune vérification locale ne peut faire, et qui portent leur
raison en clair.

### 2 — Attestation Ed25519

```sh
python ../../verify_attestation.py NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --trust-store trust-store.json --allow-test-keys
```

**Attendu : `10 PASS, 0 FAIL, 4 NOT TESTED`, niveau
`cryptographically_attested`.**

Sans `--allow-test-keys`, la clé de démonstration est **refusée** — c'est
voulu : elle ne doit accorder aucune attestation par défaut.

Trois lignes restent `NOT TESTED` pour toujours : la **capacité juridique**
du signataire, l'**horodatage indépendant**, et la **vérité du contenu**.

### 3 — Horodatage, et son statut réel

```sh
python ../../timestamp.py verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots \
    --subject NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --descriptor NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.timestamp.json
```

**Attendu : `4 PASS, 0 FAIL, 3 NOT TESTED`.** La *liaison* est établie ; la
ligne `attestation confirmee par la chaine` est `NOT TESTED` parce que les
quatre attestations sont `PENDING`.

En mode `--strict`, **code 2** : un consommateur automatisé doit savoir que
la date n'est pas établie.

Pour vérifier le **temps** — ce que nous ne faisons pas — le client officiel :

```sh
ots verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots
```

### 4 — Liaison observation ↔ artefacts

```sh
cd binding
python ../../../bind.py verify manifest.json \
    --archive ../NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --attestation ../NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --trust-store ../trust-store.json --allow-test-keys
```

**Attendu : `10 PASS, 0 FAIL, 3 NOT TESTED`, niveau
`cryptographically_attested`.** Les deux artefacts sont élevés de
`reference_verifiable` à `cryptographically_attested` par l'attestation de
l'archive qui déclare leurs empreintes.

### 5 — Réconciliation

```sh
python ../../adapters/reconcile.py receipt-imported.json \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip --map map-comparable.json
```

**Attendu : `4 MATCHED, 2 MISMATCHED, 1 MISSING, 1 NOT COMPARABLE,
1 NOT VERIFIABLE`**, et **3 contradictions conservées**.

Puis le même reçu avec `--map map-no-context.json` : quand le reçu ne déclare
ni version de mesure, ni couverture, ni définition, **plus rien de ce qui est
mesuré ne se compare** — mais une **empreinte concorde quand même**.

---

## Quatre choses à essayer pour nous mettre en défaut

C'est le meilleur usage de votre temps.

**Changez un octet dans un membre.** Rouvrez le ZIP, modifiez
`observations.jsonl`, refermez sans refaire `checksums.sha256`.
→ `verify.py` doit rendre **3 FAIL**.

**Ajoutez un octet à la fin du fichier.** → `verify.py` passe (**0 FAIL**),
et c'est **exact** : il vérifie l'intégrité *interne*. L'**attestation**, elle,
refuse — l'identité du *fichier* est ce qu'elle couvre. Deux outils, deux
garanties distinctes.

**Retirez une observation et recalculez tout** — décomptes du manifeste et
sommes de contrôle. L'archive devient intérieurement **parfaite**, et
`verify.py` seul n'y voit rien. L'attestation la refuse. C'est la limite que
nous déclarions indétectable jusqu'au 6 novembre.

**Falsifiez l'attestation.** Changez un octet du `.jws`, ou son champ
`alg` en `none`. → refus, avec la cause.

---

## Reproduire le dossier entier

```sh
python ../../tests/make_fixture.py <repertoire>
```

L'archive est **déterministe à l'octet** : deux exécutions rendent la même
empreinte. L'attestation, elle, ne peut pas être reproduite — sa clé privée a
été détruite. Elle reste **vérifiable**, et aucune nouvelle attestation ne
peut être émise avec cette clé.

---

## Ce que ce dossier n'établit pas

- **Que l'exécution mesurée a eu lieu.** Il n'y en a pas eu : tout est
  synthétique.
- **Aucune date.** La preuve d'horodatage est `PENDING`.
- **Aucune qualification eIDAS.** OpenTimestamps n'est pas un prestataire de
  services de confiance qualifié.
- **La vérité d'aucun contenu.** Une attestation parfaite sur une archive
  fabriquée est cryptographiquement valide — et c'est précisément le cas ici.
- **Que ces fonctions marchent sur un dossier de pilote réel.** Aucune ne l'a
  encore été.

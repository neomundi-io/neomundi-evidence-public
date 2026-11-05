<sub>🇬🇧 <a href="TIMESTAMPING.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Horodatage indépendant — OpenTimestamps

L'attestation signée établit **qui** s'est engagé. Elle n'établit pas
**quand** : `attested_at_declared` est une date que le signataire écrit
lui-même. L'horodatage indépendant attaque précisément cette limite — et il
ne la referme qu'en partie.

---

## Ce que cet outil établit, et ce qu'il délègue

> **Il établit, sans aucune dépendance, que la preuve `.ots` s'engage sur
> l'empreinte du sujet.** C'est la *liaison*, et c'est la seule part que nous
> pouvons démontrer nous-mêmes.

> **Il ne vérifie pas le temps.** Valider une attestation Bitcoin demande un
> en-tête de bloc, donc une source de confiance que nous n'avons pas. Cette
> vérification est **déléguée** au client officiel (`ots verify`), et la ligne
> correspondante reste `NOT TESTED` ici.

Un outil qui prétendrait vérifier le temps sans en-tête de bloc mentirait.

---

## `PENDING` n'est pas une preuve de temps

C'est le point le plus facile à mal lire, et il est répété à chaque exécution.

| État | Signifie |
|---|---|
| **`PENDING`** | un calendrier public s'est engagé à inclure l'empreinte dans une **future** transaction Bitcoin. **Aucune date n'est attestée.** |
| **`BITCOIN`** | l'empreinte est engagée dans un bloc. Une revendication temporelle existe — et sa vérification demande le client officiel |

Le passage de l'un à l'autre prend **quelques heures** : le temps que la
chaîne confirme la transaction du calendrier. On l'obtient en relançant
`upgrade`.

> **Aucun horodatage qualifié eIDAS n'est revendiqué.** OpenTimestamps n'est
> pas un prestataire de services de confiance qualifié au sens du règlement.
> Le vérificateur l'écrit sur une ligne dédiée, à chaque exécution.

---

## Ce qui quitte le poste

**Une empreinte de 32 octets, et rien d'autre.**

Jamais l'archive, jamais le manifeste, jamais une donnée de pilote. Et seules
deux sous-commandes touchent le réseau :

| Sous-commande | Réseau |
|---|---|
| `stamp` | **oui** — soumet l'empreinte aux calendriers |
| `upgrade` | **oui** — demande l'attestation achevée |
| `inspect` | non |
| `verify` | **non, jamais** — un test le vérifie sur le graphe d'appels |

---

## Emploi

```sh
# 1. horodater l attestation signee -- le sujet recommande
python timestamp.py stamp examples/attestation/A.zip.jws \
    --descriptor A.zip.jws.timestamp.json \
    --stamped-at 2026-11-05T22:00:00Z

# 2. lire la preuve, hors ligne
python timestamp.py inspect A.zip.jws.ots

# 3. verifier la liaison, hors ligne
python timestamp.py verify A.zip.jws.ots \
    --subject examples/attestation/A.zip.jws \
    --descriptor A.zip.jws.timestamp.json --json rapport.json

# 4. plus tard, une fois la chaine passee
python timestamp.py upgrade A.zip.jws.ots --out A.zip.jws.v2.ots

# 5. et verifier le TEMPS avec le client officiel, pas avec nous
ots verify A.zip.jws.v2.ots
```

**Pourquoi horodater l'attestation plutôt que l'archive.** L'attestation
porte l'empreinte de l'archive *et* la signature. Horodater l'attestation lie
donc le temps à l'engagement signé, pas seulement à des octets.

`--stamped-at` est **exigé** : l'outil ne lit jamais l'horloge, et cette date
n'est **pas** l'horodatage — c'est la date à laquelle *nous* avons soumis.

---

## Les sept lignes de contrôle

| Contrôle | États possibles |
|---|---|
| ★ `preuve .ots lisible` | `PASS` / `FAIL` |
| ★ **`liaison a l empreinte du sujet`** | `PASS` / `FAIL` / `NOT TESTED` |
| `descripteur de liaison` | `PASS` / `FAIL` / `NOT TESTED` |
| `arbre des attestations` | `PASS` / `FAIL` / `NOT TESTED` |
| ★ `attestation confirmee par la chaine` | `PASS` / `NOT TESTED` |
| `temps verifie par un tiers` | **toujours `NOT TESTED`** |
| `qualification eIDAS` | **toujours `NOT TESTED`** |

Les trois ★ sont **requises** en mode `--strict`. Une preuve `PENDING` rend
donc **code 2** : honnête, et exactement ce qu'un consommateur automatisé doit
savoir.

Les deux dernières ne seront **jamais** `PASS`, et ne sont donc jamais
requises — un mode strict qui les compterait serait toujours rouge.

---

## Pourquoi la liaison ne dépend de rien

Le format `.ots` détaché place l'empreinte engagée à un **offset fixe** :

```
31 octets de magie · 1 octet de version · 1 octet d operation · 32 octets d empreinte
   ^ \x00OpenTimestamps\x00\x00Proof\x00…         ^ 0x08 = SHA-256
```

Lire la liaison, c'est donc lire trois champs de longueur connue. Aucune
dépendance, aucune analyse d'arbre, aucun risque de divergence.

**Le reste de l'arbre est laissé à la bibliothèque officielle**
(`opentimestamps`). Écrire une seconde implémentation d'un format
cryptographique serait une dette, pas une indépendance.

| Si `opentimestamps` est… | alors |
|---|---|
| présent | l'arbre est lu, les attestations sont listées |
| absent | `arbre des attestations` → `NOT TESTED`, **et la liaison reste `PASS`** |

Un test l'éprouve en bloquant l'import : la liaison tient sans la
bibliothèque. C'est la propriété qui fonde cette architecture.

> **Note sur le client officiel.** `opentimestamps-client` — qui fournit la
> commande `ots` — dépend de `python-bitcoinlib`, et **cette dépendance plante
> à l'import sur le poste de développement** (`TypeError` dans une
> vérification de chemin). La bibliothèque de format, elle, fonctionne. C'est
> une raison de plus pour que la liaison n'en dépende pas.

---

## `upgrade` n'écrase jamais

```sh
python timestamp.py upgrade ancienne.ots --out nouvelle.ots
```

Une preuve est une **pièce**. L'écraser détruirait l'antérieure, qui reste
vérifiable et qui atteste la soumission. `upgrade` refuse donc une sortie
existante sans `--force`, et laisse toujours l'entrée intacte.

Tant qu'aucune attestation Bitcoin n'apparaît, il le dit :

```
attestations Bitcoin : 0 avant, 0 apres
l ancienne preuve est INTACTE : ancienne.ots

Rien n a progresse : la transaction n est probablement pas encore
confirmee par la chaine. Reessayer plus tard. Tant qu aucune
attestation Bitcoin n apparait, **aucune date n est attestee.**
```

---

## Matrice de tests

**Hors réseau, déterministe** : `python tests/test_timestamp.py` → **21/21**.

| # | Cas | Résultat |
|---|---|---|
| 1 | preuve authentique, sujet juste | **liaison `PASS`** |
| 2 | `PENDING` | les deux lignes temporelles `NOT TESTED` |
| 3 | revendication eIDAS | aucune, ligne explicite |
| 4 | sujet différent | **liaison `FAIL`**, code 1 |
| 5 | sujet non fourni | `NOT TESTED`, **pas `FAIL`** |
| 6 | strict sur `PENDING` | **code 2**, verdicts inchangés |
| 7 | strict sur un `FAIL` | code 1 — le `FAIL` l'emporte ; **7 lignes identiques** |
| 8 | 5 preuves malformées (magie absente, tronquée, vide, version inconnue, hachage inconnu) | **5/5** `FAIL` motivé, aucune trace d'appels |
| 13 | preuve introuvable | `FAIL` motivé |
| 14 | descripteur concordant | `PASS` |
| 15 | **descripteur qui ment sur le sujet** | `FAIL` — il est confronté à la preuve, pas cru |
| 16 | descripteur de schéma inconnu | refusé, pas interprété |
| 17 | descripteur illisible | `FAIL` motivé |
| 18 | rapport machine | trois états distincts, 3 limites dites |
| 19 | `inspect` | empreinte engagée, `PENDING` dit |
| 20 | **`opentimestamps` bloqué** | **liaison `PASS`**, arbre `NOT TESTED` |
| 21 | strict sans la bibliothèque | code 2, jamais `PASS` |
| 22 | preuve confirmée (synthétique) | `attestation confirmee` → `PASS`, **temps toujours `NOT TESTED`** |
| 23 | confirmée + strict | code 0 |
| 24 | même confirmée | la commande du client officiel est donnée |
| 25 | graphe d'appels de `verify` | **aucune primitive réseau** |

**Réseau, séparé** : `python tests/test_timestamp_network.py [--stamp]` →
**3/3**, et ne tourne **jamais** en CI. Une suite qui dépend de quatre
serveurs tiers échouerait pour des raisons qui ne sont pas des défauts du
produit, et une CI rouge sans cause interne apprend à ignorer le rouge.

### Ce que les tests ne peuvent pas éprouver

Le passage réel `PENDING → CONFIRMED` demande des **heures** de confirmation
Bitcoin. Le chemin est donc couvert par une **fixture synthétique** (cas 22 et
23) : une attestation Bitcoin construite hors réseau, qui éprouve la logique
et **n'atteste évidemment aucune date**. Aucun test ne prétend le contraire.

---

## L'exemple livré

`examples/timestamp/` porte une **preuve réelle**, obtenue le 5 novembre 2026
des quatre calendriers publics :

| | |
|---|---|
| Sujet | `examples/attestation/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws` |
| Empreinte engagée | `9b65f9bb02b06944fefd0cc1dd52db157797c274bf27f3e29ee2585126108c18` |
| Preuve | 786 octets, `86da875b…` |
| État | **`PENDING` sur 4 calendriers** |

Le sujet est l'attestation **déjà publique** dans ce dépôt : son empreinte
n'est donc pas une divulgation.

**Cette preuve n'atteste aucune date**, et c'est écrit dans son descripteur.
Elle devra être mise à niveau pour en porter une.

---

## Dépendances et réseau — déclarées

| | |
|---|---|
| **Liaison** | aucune dépendance |
| **Lecture des attestations** | `opentimestamps` ; absente → `NOT TESTED` |
| **`stamp` / `upgrade`** | `opentimestamps` **requis**, et **réseau requis** |
| **Réseau atteint** | quatre calendriers publics en HTTPS |
| **Compte, paiement** | **aucun** |
| **Bitcoin** | aucun nœud n'est exécuté, aucune transaction n'est émise, aucun frais n'est payé. Les calendriers agrègent des milliers d'empreintes dans une transaction qu'ils financent |
| **Données transmises** | **une empreinte de 32 octets** |

---

## Ce que l'horodatage n'établit pas

- **Le temps, de notre part.** Nous ne vérifions aucune attestation Bitcoin.
- **Aucune date, tant que l'état est `PENDING`.**
- **La vérité du contenu.** Horodater une archive fabriquée produit une preuve
  parfaitement valide pour cette archive fabriquée.
- **Une qualification eIDAS.** Aucune, et aucune n'est revendiquée.
- **Que le sujet soit celui qu'on croit** — sauf si vous passez `--subject`,
  auquel cas la liaison, elle, est démontrée.

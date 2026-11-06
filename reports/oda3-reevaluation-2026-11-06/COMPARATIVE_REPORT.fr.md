<sub>🇫🇷 <b>Français</b> · 🇬🇧 <a href="COMPARATIVE_REPORT.md">English</a></sub>

# Réévaluation ODA3 — les expériences rejouées sur le commit fusionné

**6 novembre 2026.** Rejeu des expériences ODA3 sur le commit qui a fusionné
la PR #10, comparé à l'audit initial.

| | |
|---|---|
| Commit testé | **`ee78214`** — `Merge pull request #10 from neomundi-io/feat/evidence-oda3-consolidation`, identique à `origin/main` |
| Audit initial | `reports/oda3-mukesh-2026-11-06/`, **55 fichiers, non modifiés** |
| Ce rejeu | `reports/oda3-reevaluation-2026-11-06/`, dossier distinct |
| Archive testée | `examples/dossier-v1`, `e31e12bb7e32c7a33db1ecacc8c38cd18225fa10618c7e1aa5d6f9540f2ad7d6` — identique octet pour octet à celle auditée |

> Aucun fichier ODA3 n'a été modifié. Aucun `NOT TESTED` n'a été transformé en
> `PASS`.

---

## La réponse courte

**La consolidation améliore la garantie, et moins que la recommandation ne le
suggère.** Trois constats, tous mesurés :

1. Le contrôle de complétude **attrape** un export amputé — mais seulement
   face à un faussaire qui ne réécrit **pas** aussi la déclaration.
2. **OD-C rend toujours `19 PASS, 0 FAIL` sur le dossier V1**, et le rendra
   toujours. Cette archive ne déclare aucun contrat de complétude : il n'y a
   rien à contredire. Le constat ODA3 est **restreint, pas levé**.
3. La sonde de l'auditeur **a changé entre l'audit initial et maintenant** :
   sa colonne n'est pas comparable. La lire comme une régression serait une
   erreur de méthode.

---

## 1. Les expériences, avant et après

Commande :

```sh
python reports/oda3-mukesh-2026-11-06/oda3_experiments.py \
  --dossier examples/dossier-v1 --repo . \
  --probe reports/oda3-mukesh-2026-11-06/oda3_probe.py \
  --json  reports/oda3-reevaluation-2026-11-06/raw/04_experiences_dossier_v1.json
```

Seuls **nos** outils sont comparables. La colonne de la sonde est traitée au
§4.

| Cas | Altération | `verify.py` initial | `verify.py` après PR #10 | Attestation initiale | après |
|---|---|---|---|---|---|
| **OD-A** | un octet nul ajouté après l'annuaire central | `0` — 19/0/**2** | `0` — 19/0/**3** | `1` — 9/1/4 | `1` — 9/1/**5** |
| **OD-B** | un caractère hexadécimal changé, sommes **non** refaites | `1` — 18/**1**/2 | `1` — 18/**1**/3 | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-C** | le **dernier** enregistrement retiré partout, décomptes et sommes refaits | **`0` — 19/0/2** | **`0` — 19/0/3** | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-E** | un enregistrement **intérieur** retiré, de même | `0` — 19/0/2 | `0` — 19/0/3 | `1` — 9/1/4 | `1` — 9/1/5 |
| **OD-D** | l'`alg` du JWS falsifié en `none` | `0` — 19/0/2 | `0` — 19/0/3 | `1` — 8/**2**/4 | `1` — 8/**2**/5 |

Lire les codes de sortie, pas la prose : `0` = a conclu favorablement, non nul
= a refusé.

**Tous les verdicts sont inchangés. Chaque décompte gagne exactement un
`NOT TESTED`** — `verify.py` est passé de 21 à 22 lignes de contrôle, et le
dossier V1 ne déclare aucun contrat de complétude : la nouvelle ligne est
`NOT TESTED`. L'attestation en gagne un de même, par le contrôle
`--store-digest`.

**C'est le résultat honnête sur cette archive : une chose de plus rapportée,
rien de plus attrapé.**

## 2. La garantie réellement démontrée — et sa limite exacte

Le scénario d'OD-C est celui pour lequel le contrôle a été construit : il
fallait donc l'exercer sur une archive qui **déclare** le contrat. Rejoué sur
une fixture `--profile v2`, face à deux faussaires
(`raw/05_odc_sur_v2.txt`) :

| Faussaire | Ce qu'il refait | `verify.py` |
|---|---|---|
| **Négligent** | les décomptes et les sommes, **pas** le contrat | **`exit 1` — 19 PASS, 1 FAIL** |
| **Méticuleux** | les décomptes, les sommes **et** le contrat | `exit 0` — 20 PASS, 0 FAIL |

Le refus, mot pour mot :

```
[FAIL      ] completude de l export - le contrat annonce 16 enregistrement(s)
             exporte(s), les decomptes des membres en totalisent 12
```

Le contrôle est donc réel, et son plafond l'est aussi :

- **Il attrape une amputation incohérente.** La déclaration et les membres ne
  s'additionnent plus, et l'archive est refusée — sans aucune signature.
- **Un faussaire cohérent le défait.** Qu'il réécrive les trois champs du
  contrat de manière cohérente, et l'arithmétique se referme.

**Ce qui arrête le faussaire méticuleux, c'est la signature, et elle seule.**
`verify_attestation.py` a refusé les **cinq** archives altérées, dans les deux
passages, dans tous les cas. Les champs du contrat vivent dans
`manifest.json`, couvert par `checksums.sha256`, couvert par l'empreinte de
l'archive, qui est signée : un faussaire méticuleux doit casser Ed25519.

La valeur du contrôle de complétude s'énonce donc précisément : **c'est la
défense qui fonctionne sur une archive non signée.** C'est exactement le cas
qu'ODA3 a exercé — ils ne pouvaient pas re-signer. Il porte le coût de la
falsification de « refaire les sommes » à « refaire les sommes et la
déclaration, ou détenir la clé ». Il ne rend pas un export amputé détectable
en général, et ne doit jamais être lu ainsi.

## 3. R-6 n'est exercé par rien de tout cela

L'écart de provenance analysé dans [`R6_PROVENANCE_CONTRACT.fr.md`](../../docs/R6_PROVENANCE_CONTRACT.fr.md)
n'est pas touché par ces expériences, et reste tel que mesuré : **0 champ de
provenance sur 238 mesures dans 8 registres gelés.** Aucune expérience
ci-dessus ne pouvait le trouver, et aucune ne le ferme.

## 4. Deux limites de l'instrument de l'auditeur

Les deux établies par observation, non par lecture de code. Ni l'une ni
l'autre ne change une conclusion de l'audit initial, et ni l'une ni l'autre
n'est un défaut de notre produit — mais les deux bornent ce que ce rejeu peut
affirmer.

### La sonde n'est pas un instrument figé

Sur le **même** dossier, identique octet pour octet, le passage autonome de la
sonde dans l'audit initial et mon rejeu concordent exactement :

```
run 06, audit initial  : 1 PASS, 0 FAIL, 2 NOT TESTED, 6 FACT   (9 controles)
run 01, ce rejeu       : 1 PASS, 0 FAIL, 2 NOT TESTED, 6 FACT   (9 controles)
```

Mais la sonde **appelée par les expériences** dans l'audit initial rapportait
`3 PASS, 0 FAIL, 0 NOT TESTED, 4 FACT` — **7** contrôles. Les horodatages des
fichiers tranchent :

| | |
|---|---|
| `07_experiments.json` écrit | **08:49:43** |
| `oda3_probe.py` écrit | **08:58:24** |

La sonde a été réécrite **neuf minutes après** l'enregistrement des
expériences, gagnant deux contrôles. Elle n'est **pas suivie par Git** :
aucune révision n'identifie ni l'une ni l'autre version.

**Conséquence.** La colonne `oda3_probe.py` du tableau d'expériences initial
n'est pas comparable à la mienne. En particulier OD-E passe de `1 FAIL` à
`0 FAIL` côté sonde — **ni une régression ni une amélioration, mais un
changement d'instrument.** `verify.py` et `verify_attestation.py` restent
pleinement comparables : ils sont à nous, à `ee78214`.

### Trois des cinq empreintes d'archives altérées ne sont pas reproductibles

Deux passages, même machine, même commit, même archive d'entrée
(`raw/09_limites_de_l_instrument.txt`) :

| Cas | Passage 1 | Passage 2 | |
|---|---|---|---|
| OD-A | `5319ac9f…` | `5319ac9f…` | identique |
| OD-B | `8d037b6c…` | `beadcf64…` | **diffère** |
| OD-C | `4cdb6288…` | `e6d41a2e…` | **diffère** |
| OD-E | `6e766ef3…` | `4571b43e…` | **diffère** |
| OD-D | `e31e12bb…` | `e31e12bb…` | identique |

`zipfile.writestr` avec un nom en `str` horodate `ZipInfo.date_time` à
l'**heure courante** : tout cas qui reconstruit l'archive rend une nouvelle
empreinte. Les deux cas stables sont les deux qui ne reconstruisent rien :
OD-A ajoute un octet, OD-D ne touche que le `.jws`.

Les empreintes altérées du rapport ODA3 ne sont donc **pas** re-dérivables par
un tiers — c'est la même classe de défaut que R-5 a trouvée dans notre propre
référence de corpus, et elle mérite d'être nommée pour exactement cette
raison. Les **verdicts** se reproduisent ; les empreintes, non.

### Et la sonde ne peut pas confirmer R-1

```
grep types_exclus             oda3_probe.py  → 0
grep enregistrements_exportes oda3_probe.py  → 0
grep completude               oda3_probe.py  → 0
```

La sonde ne lit pas la déclaration ajoutée par la PR #10. **Elle ne peut ni
confirmer ni infirmer R-1.** Seul [`tests/test_completude.py`](../../tests/test_completude.py)
l'exerce — notre propre test, preuve plus faible qu'un instrument
indépendant, et énoncée comme telle.

## 5. C-2 — une régression apparente qui est l'inverse

La sonde rapporte la recette `record_sha256` en `PASS` sur le dossier V1 et en
`NOT TESTED` sur `v2`. Lu seul, cela inverse la conclusion. La confrontation
(`raw/03_c2_recette_declaree.txt`) :

```
--- profil v1 ---   recette declaree : NON
    concordent avec `sequence` : 0 ; concordent SANS `sequence` : 4
--- profil v2 ---   recette declaree : oui
    concordent avec `sequence` : 16 ; concordent SANS `sequence` : 0
```

`v1` hachait **sans** `sequence` — la simplification de la sonde, qu'elle
reproduit, d'où le `PASS`. `v2` hache **avec** `sequence` — le jeu de champs
réel de l'instrument, que la sonde omet, d'où le `NOT TESTED`.

**Le passage de `PASS` à `NOT TESTED` est un progrès.** `v2` s'est déplacé
*vers* l'instrument et *loin* de la sonde. Un lecteur prenant le verdict de la
sonde au pied de la lettre conclurait l'inverse.

Le script de confrontation de chaîne (`oda3_chain_confrontation.py`) exige un
checkout `src` de Station inatteignable depuis cette session : C-2 a donc été
tranché par la confrontation écrite ci-dessus plutôt que par cet instrument.
**Énoncé comme une substitution, pas comme un équivalent.**

---

## 6. Synthèse

### Garanties nouvelles réellement démontrées

| | |
|---|---|
| Une amputation **incohérente** d'un export est refusée, sans aucune signature | mesuré : `exit 1`, 19 PASS **1 FAIL** sur `v2` |
| Une archive **nomme** ce que son registre tenait, a exporté et a retenu, et les trois nombres s'additionnent | la ligne `PASS` du contrôle |
| `v2` hache avec le jeu de champs de l'instrument | 16/16 concordent avec `sequence`, 0/16 sans |
| Le dossier V1 se reproduit octet pour octet sous Linux | `create_system` épinglé ; CI verte |

### Limites corrigées

| | |
|---|---|
| Un export pouvait retenir des enregistrements en silence | désormais déclaré et contrôlé — **quand le producteur déclare le contrat** |
| Le rendu `['True']` | corrigé, dans les deux langues |
| `stamped_at_declared` face au bloc d'ancrage | désormais côte à côte |
| L'affirmation sur `campaign_sha256` | corrigée ; table d'accès à quatre classes |
| L'archive n'était pas reproductible hors Windows | corrigé — défaut que l'audit ne pouvait pas voir, il tournait sous Windows |

### Limites persistantes

| | |
|---|---|
| **OD-C sur une archive sans le contrat** | `19 PASS, 0 FAIL`, définitivement. Restreint, pas levé |
| **Un faussaire méticuleux défait le contrôle de complétude** | seule la signature l'arrête |
| **R-6** | 0 champ de provenance sur 238 mesures ; évolution de contrat requise |
| **R-5, seconde moitié** | la recette reste non publiée — classe C |
| **R-9 / B-1** | l'identité juridique du signataire. Rien de technique ne la remplace |
| La sixième divergence `v2` | canonicalisation de `record_sha256` : déclarée, pas close |
| **Qu'une déclaration soit *vraie*** | jamais vérifiable depuis une archive. Un `NOT TESTED` permanent |

### Nouvelles régressions

**Aucune dans nos outils.** Tous les verdicts de `verify.py` et de
`verify_attestation.py` sont inchangés sur les cinq cas ; le seul mouvement
est `+1 NOT TESTED`, qui est le nouveau contrôle rapportant honnêtement sur
une archive qui le précède.

La seule régression apparente — OD-E côté sonde, `1 FAIL` → `0 FAIL` — est un
**changement de l'instrument de l'auditeur**, établi par les horodatages de
ses fichiers, et n'est pas imputable à ce commit.

---

## Sorties brutes

| Fichier | Ce qu'il contient |
|---|---|
| `raw/01_probe_dossier_v1.{txt,json}` | la sonde sur le dossier V1 |
| `raw/02_probe_fixture_v2.{txt,json}` | la sonde sur une fixture `v2` |
| `raw/03_c2_recette_declaree.txt` | la confrontation C-2 |
| `raw/04_experiences_dossier_v1.{txt,json}` | les cinq expériences rejouées |
| `raw/05_odc_sur_v2.txt` | OD-C face à un faussaire négligent et à un méticuleux |
| `raw/07_instrument_non_fige.txt` | la sonde a changé entre les passages |
| `raw/08_experiences_second_passage.json` | second passage, pour la reproductibilité des empreintes |
| `raw/09_limites_de_l_instrument.txt` | les deux limites de l'instrument |

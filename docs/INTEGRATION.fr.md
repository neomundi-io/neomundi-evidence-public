<sub>🇬🇧 <a href="INTEGRATION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Intégrer Evidence — codes de sortie, mode strict, rapports

Pour qui automatise la vérification. Si vous lisez un rapport à l'œil, la
sortie texte suffit et ce document ne vous concerne pas.

---

## La règle en une phrase

> **Ne lisez pas le code de sortie par défaut. Lisez le rapport JSON, ou
> activez `--strict`.**

Les trois outils sortent en **0** par défaut dès lors qu'aucun contrôle n'a
échoué — y compris quand des contrôles n'ont **pas pu être faits**. C'est
volontaire : `NOT TESTED` n'est pas un échec, et traiter l'absence de preuve
comme une preuve d'absence serait faux. Mais pour un script, quatre
situations très différentes rendent alors le même `0`.

---

## Les codes de sortie

| Code | Signifie |
|---|---|
| **0** | aucun contrôle n'a échoué. Et, si `--strict` est actif, toute garantie **requise** est démontrée |
| **1** | **au moins un contrôle a échoué.** Le dossier, la liaison ou l'attestation ne doit pas être présenté comme vérifié |
| **2** | aucun échec, mais `--strict` est actif et une garantie **requise** n'est pas démontrée |

**`1` l'emporte sur `2`.** Un échec est l'énoncé le plus fort ; un consommateur
qui ne distingue pas les codes non nuls n'est pas induit en erreur pour
autant.

---

## Le piège, sans `--strict`

```sh
python verify_attestation.py a.jws --archive a.zip   # pas de magasin fourni
echo $?                                              # 0
```

Quatre situations rendent `0` et ne se valent pas :

| Situation réelle | Code | Ce qu'un script en conclurait |
|---|---|---|
| niveau `cryptographically_attested` atteint | `0` | « attesté » — **juste** |
| clé inconnue du magasin de confiance | `0` | « attesté » — **faux** |
| `cryptography` absent de l'environnement | `0` | « attesté » — **faux** |
| aucun magasin fourni | `0` | « attesté » — **faux** |

Les trois dernières sont des **non-vérifications**.

---

## `--strict` : ce qu'il fait, et ce qu'il ne fait pas

```sh
python verify_attestation.py a.jws --archive a.zip --strict
echo $?                                              # 2
```

```
[NOT TESTED] signature cryptographique - aucun magasin de confiance fourni…
[NOT TESTED] identite de confiance - sans magasin, aucune confiance n est etablie

MODE STRICT : 2 garantie(s) requise(s) non demontree(s) :
  - signature cryptographique
  - identite de confiance
Aucun verdict n a change : ces lignes restent telles qu affichees.
Seul le code de sortie en tient compte (2).
```

**Il ne change aucun verdict.** Les lignes restent `PASS`, `FAIL` ou
`NOT TESTED` à l'identique — la CI le vérifie en comparant, octet pour octet,
les lignes de contrôle avec et sans le drapeau. Transformer un `NOT TESTED`
en `FAIL` réintroduirait la fusion des trois états que ce produit interdit.

**Le défaut reste non strict**, pour qu'une exécution humaine continue de
rendre un diagnostic plutôt qu'un refus.

### Garanties requises, et garanties hors d'atteinte

Une garantie est **requise** quand son `NOT TESTED` est **contingent** :
elle deviendrait `PASS` si vous fournissiez ce qui manque.

| Outil | Garanties requises | Comment les satisfaire |
|---|---|---|
| `verify.py` | empreintes des entrées rejouées | `--corpus <répertoire>` |
| `bind.py` | le sujet dans son archive · revendications éprouvées · chaque artefact · attestation du sujet | `--archive`, `--root`, `--attestation` + `--trust-store`, `--max-artifact-bytes` |
| `verify_attestation.py` | les **cinq piliers** : profil de canonicalisation, algorithme imposé, signature, confiance, concordance | `--archive`, `--trust-store`, et `cryptography` installé |

Ne sont **jamais** requises les limites **permanentes** — elles ne seront
jamais `PASS`, et les exiger rendrait le mode strict toujours rouge, donc
inutile :

- la **capacité juridique** du signataire — aucun code ne l'établit ;
- l'**horodatage indépendant** — `attested_at_declared` est déclaré ;
- l'**ancrage tiers** — non implémenté ;
- la **vérité du contenu** — une signature n'atteste pas un fait ;
- le **chaînage du registre** — le recalculer ici serait une seconde
  implémentation ;
- l'**origine de l'archive** — aucune signature tierce, aucun ancrage.

---

## Les rapports lisibles par machine

`--json <fichier>` sur les trois outils. **La sortie texte reste identique :
le fichier s'ajoute, il ne remplace rien.**

| Outil | Schéma du rapport |
|---|---|
| `verify.py` | `neomundi.evidence.verification-report/1` |
| `bind.py verify` | `neomundi.evidence.binding-report/1` |
| `verify_attestation.py` | `neomundi.evidence.attestation-report/1` |

Champs communs, et ceux qui comptent :

```json
{
  "schema": "neomundi.evidence.attestation-report/1",
  "controls": [{"state": "PASS", "control": "…", "detail": "…"}],
  "counts": {"pass": 10, "fail": 0, "not_tested": 4},
  "strict": false,
  "required_not_demonstrated": [],
  "exit_code": 0,
  "attained_level": "cryptographically_attested",
  "does_not_establish": ["that the execution took place", "…"]
}
```

**Ce qu'il faut lire, et dans cet ordre :**

1. **`counts.fail`** — s'il est non nul, arrêtez là ;
2. **`required_not_demonstrated`** — s'il n'est pas vide, votre vérification
   est incomplète, quel que soit le code de sortie ;
3. **`attained_level`** — `null` signifie **aucun niveau atteint**, pas
   « niveau faible » ;
4. **`does_not_establish`** — ce que le rapport, par construction, ne dit pas.

**Ne déduisez jamais un succès de `counts.fail == 0` seul.** Les trois états
sont trois champs distincts précisément pour qu'on ne les confonde pas.

### `strict` est porté au rapport, exprès

Sans ce champ, deux exécutions au même verdict et au code de sortie différent
seraient indistinguables après coup.

---

## Un exemple de consommateur correct

```sh
#!/bin/sh
set -e

python verify_attestation.py "$1" \
    --archive "$2" --trust-store "$3" \
    --json rapport.json --strict || code=$?

python - <<'PY'
import json, sys
r = json.load(open("rapport.json", encoding="utf-8"))
if r["counts"]["fail"]:
    sys.exit("REFUSE : %d controle(s) en echec" % r["counts"]["fail"])
if r["required_not_demonstrated"]:
    sys.exit("INCOMPLET : %s" % ", ".join(r["required_not_demonstrated"]))
if r["attained_level"] != "cryptographically_attested":
    sys.exit("NIVEAU INSUFFISANT : %r" % r["attained_level"])
print("ATTESTE -- et cela n etablit toujours pas :")
for limite in r["does_not_establish"]:
    print("  -", limite)
PY
```

Le dernier bloc n'est pas de la politesse : un intégrateur qui affiche
« attesté » sans dire ce que cela n'établit pas reproduit exactement la
surenchère que ce produit s'interdit.

---

## Intégration continue

`.github/workflows/tests.yml`, trois tâches, à chaque *pull request* et à
chaque poussée sur `main`.

| Tâche | Ce qu'elle établit |
|---|---|
| **`suites`** — Python 3.11, 3.12, 3.13 | les quatre suites passent ; les lignes de base du vérificateur sont **exactes** ; le mode strict ne change aucun verdict ; les codes 0/2 sont ceux attendus |
| **`sans-cryptography`** | `verify.py` est **indifférent** à l'absence de dépendance ; la signature rend `NOT TESTED` et jamais `PASS` ni `FAIL` ; le défaut rend 0 et le strict rend 2 |
| **`discipline`** | `verify.py` et `canonical.py` n'importent que la bibliothèque standard ; le vérificateur n'atteint **aucune** clé privée ; aucun matériau privé dans le suivi ; le signataire **refuse** d'écrire une clé sous la racine ; tous les liens internes résolvent ; chaque document a sa paire EN/FR |

### La CI n'utilise pas les archives de démonstration, et pourquoi

`tests/make_fixture.py` fabrique une archive **sans aucun lien avec un jeu de
données réel**, déterministe à l'octet.

Le constat qui l'impose mérite d'être écrit. L'archive GROUNDED-S1 porte
`dataset_id: medmcqa-single`, trente `item_id` réels, et un
`reference_evaluations.jsonl` qui croise `extracted_answer` et `status`. Pour
ses treize observations au statut `correct`, **l'étiquette de référence de
treize items MedMCQA est exactement reconstituable**. La commiter aurait
divulgué ces étiquettes — et c'est déjà la raison pour laquelle ce membre
avait été exclu de l'archive de démonstration MED.

### Ce que la CI n'établit pas

**Les lignes de base publiées ne sont pas vérifiées en CI** — 19/0/2 sur
GROUNDED-S1, 10/0/8 sur MED — faute de ces archives sur le coureur. Elles
restent un contrôle **local** :

```sh
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip --corpus <corpus>
#   attendu : BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED   (21 lignes)
python verify.py NEOMUNDI_EVIDENCE_MED_DEMO_V0.1.zip
#   attendu : BILAN : 10 PASS, 0 FAIL, 8 NOT TESTED   (18 lignes)
```

La fixture rend les mêmes décomptes (19/0/2 avec corpus, 17/0/3 sans), ce qui
en fait un canari équivalent — mais **ce n'est pas la même archive**, et il ne
faut pas lire l'un pour l'autre.

Trois cas de la suite d'attestation — 9, 9b et 9c — sont rendus
**`INAPPLICABLE`** sur la fixture : ils s'appuient sur `examples/binding`,
dont le manifeste nomme l'archive de démonstration et porte son empreinte. Un
cas inapplicable n'est **ni un succès ni un échec**, et le bilan les compte à
part.

---

## Ce que l'intégration ne peut pas vous donner

- **Une preuve que l'exécution a eu lieu.** Aucun code de sortie ne la porte.
- **Une date fiable.** `attested_at_declared` est déclaré par le signataire.
- **La vérité du contenu.** Une attestation parfaitement signée sur une
  archive fabriquée est cryptographiquement valide.

Ces trois lignes sont `NOT TESTED` à chaque exécution, et elles le resteront.

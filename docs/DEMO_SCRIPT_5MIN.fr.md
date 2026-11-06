<sub>🇬🇧 <a href="DEMO_SCRIPT_5MIN.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Scénario de démonstration — cinq minutes

**Exécuté et chronométré le 5 novembre 2026.** Trois passages : **7 s, 6 s, 7 s**
de temps machine, bilans identiques. Transcriptions conservées dans
`GATE7_20261105/`.

Le budget de cinq minutes n'est donc pas contraint par la machine. Il est
entièrement disponible pour la narration : **7 secondes d'exécution, ~4 min 50
de parole.**

Une seule commande déroule tout :

```sh
bash demo_5min.sh /tmp/demo
```

---

## Ce que la démonstration doit faire constater

Quatre choses, dans cet ordre, et la quatrième est la plus importante :

1. un dossier de preuve se produit depuis un corpus gelé ;
2. il se vérifie **sans NeoMundi** ;
3. la vérification **refuse** une archive touchée ;
4. il existe une falsification qu'elle **ne voit pas**, et on la montre.

Une démonstration qui s'arrête à l'étape 3 vend une garantie. Celle-ci
s'arrête à l'étape 4.

---

## Déroulé, avec le budget de parole

### Étape 1 — le point de départ se vérifie · t+0 s · *45 s de parole*

```sh
python verifier_gel.py <gel>
station ledger verify --path <gel>/GROUNDED-S1/donnees/ledger.jsonl
```

| Résultat constaté | |
|---|---|
| gel | `12 PASS, 0 FAIL, 3 NOT TESTED` |
| chaîne | 151 enregistrements, tête `fc1f2787e6e0e24f…`, aucune anomalie |

**À dire :** on ne part pas d'un répertoire de travail mais d'un corpus **gelé**,
dont les empreintes ont été relevées le 5 novembre et dont la chaîne se
revérifie. Et le vérificateur du gel rend trois `NOT TESTED` — il dit ce qu'il
ne fait pas.

### Étape 2 — le dossier se produit · t+3 s · *45 s de parole*

```sh
station campaign export grounded-med-synthetique-v1 --sortie <archive> --registre <registre>
sha256sum <archive>
```

30 observations, 1 run, et l'empreinte de l'archive.

**À dire :** l'export **refuse** de produire quoi que ce soit si la chaîne ne se
vérifie pas, si la campagne est vide, ou si le fichier de sortie existe déjà. Il
relit ensuite l'archive qu'il vient d'écrire. Et cette empreinte-là doit être
conservée **ailleurs** qu'avec l'archive — c'est le fil de l'étape 4.

### Étape 3 — il se vérifie sans NeoMundi · t+4 s · *60 s de parole*

```sh
python verify.py <archive> --corpus <corpus>
```

→ **`19 PASS, 0 FAIL, 2 NOT TESTED`** *(mesuré avant l'existence du contrôle de complétude ; toute archive antérieure à ce contrat porte désormais un `NOT TESTED` de plus — voir [consolidation ODA3](ODA3_CONSOLIDATION.fr.md))*

**À dire :** `verify.py` n'a aucune dépendance, n'émet aucun appel réseau,
n'écrit rien. Il est fait pour être **lu** avant d'être exécuté. Les deux
`NOT TESTED` sont nommés avec leur raison : le chaînage JCS, qu'on refuse de
réimplémenter ici, et l'origine de l'archive, qu'aucune vérification locale ne
peut établir.

### Étape 4 — la vérification refuse, puis échoue · t+4 s · *90 s de parole*

```sh
python tests/test_falsification.py <archive> <corpus>
```

→ **`10/10 altérations détectées, 1 limite déclarée, 0 problème`**

Dix attaques refusées : un octet changé, une mesure retirée avec sommes
recalculées, un signal `null` déclaré mesuré, une mesure orpheline, une absence
inventée, la garde de régime retirée, un secret injecté, une formule CSV, un
membre qui sort du répertoire, le manifeste retiré.

**Puis la onzième, qui passe.** Une observation effacée *partout* — sa mesure,
son évaluation, sa provenance — avec les décomptes corrigés et les sommes
refaites : plus rien ne se contredit, et aucun contrôle interne ne peut la voir.

**À dire, mot pour mot :** « Voilà ce que notre vérification ne sait pas faire.
Un falsificateur soigneux produit un dossier cohérent. La seule défense est
l'empreinte de l'archive, conservée ailleurs qu'avec elle. C'est pour cela que
nous vous la transmettrons par un canal séparé, et c'est pour cela qu'un ancrage
extérieur figure à notre feuille de route — il n'existe pas aujourd'hui. »

### Étape 5 — le rapport dit ce qu'il ne sait pas · t+7 s · *60 s de parole*

Quatre endroits du rapport, dans l'ordre :

| | Ce qu'on montre |
|---|---|
| Valeurs `null` | « coût non établi : 30 sur 30 » — **aucune somme n'est affichée**, parce qu'il n'y a rien à sommer |
| Mesures, par signal | `semantic_instability_score` : 8 mesurés, **22 `null`**. Aucun n'est devenu un `0` |
| Régime d'exécution | la garde : ici `provider_attested` atteste un enregistrement rejoué, **pas un fournisseur** |
| Limites | sept énoncés, dans l'archive — pas dans une plaquette |

**À dire :** les états de mesure sont 15 `measured`, 8 `degraded`,
7 `not_measured`. Un dossier qui promet « une absence reste une absence » a
besoin d'absences pour le démontrer. Celui-ci en a.

---

## Ce que la démonstration n'établit pas

À dire en clôture, sans y être poussé :

- **la justesse des signaux** — l'existence d'un score ne la fonde pas ;
- **l'authenticité de l'archive** — aucune signature, aucun horodatage opposable ;
- **que ce corpus dise quoi que ce soit d'un modèle réel** — son régime est
  `synthetic` : il dit que la chaîne fonctionne, et rien du monde extérieur ;
- **qu'un acheteur veuille payer pour cela** — c'est la question qu'on vient
  poser.

---

## Ce qui reste à la charge de la personne qui présente

Le script mesure le temps machine. Il ne mesure pas la parole.

**Avant le 9 novembre :** dérouler le scénario une fois à voix haute, montre en
main, pour vérifier que les cinq budgets de parole tiennent. C'est le seul
élément du GATE 7 qu'aucune exécution ne peut établir.

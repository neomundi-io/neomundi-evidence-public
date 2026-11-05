<sub>🇬🇧 <a href="EXTERNAL_REFERENCE.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Vérifier depuis une empreinte conservée indépendamment

**La règle, avant tout le reste :** une empreinte contenue dans l'archive
n'atteste rien de l'archive. `checksums.sha256` établit que les membres sont
cohérents entre eux — pas qu'ils sont ceux qu'on a produits. Qui peut remplacer
l'archive peut remplacer la somme qui l'accompagne.

Une vérification n'est indépendante que si l'empreinte vient **d'ailleurs**.

---

## Les trois niveaux, à ne jamais confondre

| Niveau | Ce qu'il établit | Ce qu'il n'établit pas |
|---|---|---|
| `checksums.sha256`, **dans** l'archive | les membres n'ont pas bougé les uns par rapport aux autres | que l'archive soit celle qu'on a produite |
| empreinte de l'archive, **conservée ailleurs** | le fichier reçu est celui dont on a relevé l'empreinte | l'origine, l'heure, ni la véracité du contenu |
| signature ou ancrage **tiers** | qui a produit, et quand | **n'existe pas aujourd'hui** — voir la feuille de route |

---

## Les deux sources de contrôle

Le gel `20261105T1200_GEL_CORPUS_GATE0` existe en **deux exemplaires
indépendants**, et c'est ce qui le rend utilisable comme référence.

| Source | Emplacement | État au 5 novembre 2026 |
|---|---|---|
| poste | l'arborescence de sauvegarde locale de l'opérateur | en ligne, vérifié : `12 PASS, 0 FAIL, 3 NOT TESTED` |
| support externe | un disque externe hors ligne | copié et vérifié à la copie — **207/207 fichiers conformes**, vérificateur relancé sur place : mêmes 12 PASS. **Le support est depuis déconnecté** |

> Le support externe est hors ligne, et c'est une **qualité** pour ce rôle : une
> source de contrôle qu'on ne peut pas réécrire en continu vaut mieux qu'une
> copie montée en permanence. Il faut le rebrancher pour s'en servir, et le
> relever alors — ne jamais reprendre un chiffre de ce document sans l'avoir
> reconstaté.

### Empreintes des archives de gel

```
98043a138a58ef764902718a2f07d2a3058108ce448cd19a042c7e9fda294559  GEL_MED_20261105.zip
754da1d21c67590b12a26ee524a58dec3c288b0c3a698c7186b60c99451aee49  GEL_GROUNDED-S1_20261105.zip
```

Constatées identiques sur les **deux** exemplaires le 5 novembre 2026.

---

## Vérifier un dossier de preuve reçu

### Ce qu'il faut comparer : les membres, pas l'archive

L'empreinte de l'**archive** change à chaque export : son manifeste porte
`exporte_le`. Deux exports du même corpus, à deux minutes d'intervalle, donnent
deux empreintes d'archive différentes.

Mesuré le 5 novembre sur deux exports consécutifs : **six membres sur huit sont
identiques à l'octet**. Seuls `manifest.json` et `checksums.sha256` varient, et
le seul champ qui diffère est `exporte_le`.

**Ce sont donc les empreintes des membres qui constituent la référence
réutilisable.** Celles de l'archive de démonstration :

```
f8726fb87b844d15e579c06df1261ca220e5666e6dc932be03d52c4ef092eda8  observations.csv
0ef38ba4c19dbfdacca0f5f0c7df512ce2d20f70506d1689d89a9973ee985350  observations.jsonl
f83b73a278507d6b01726723e636fbd3c6a66a39406667f9ffc6f3452db75092  measurements.jsonl
5da470239cc1f87143da7ab23250023fb767b9e6e3f5572e6fe44818633b5ec4  reference_evaluations.jsonl
a165bb220b55ad0658c84936e0d3bc6ab2ddc059e5ed2807c7e55bd409afba34  replay_provenance.jsonl
2a3e661ab85f1e7b9f3c3264f5be586c2997af3f00ea48918f1f397be19bbf8b  rapport.md
```

`manifest.json` et `checksums.sha256` sont volontairement absents de cette
liste : ils varient d'un export à l'autre.

### La marche à suivre

```sh
# 1. l'empreinte de l'archive reçue, avant de l'ouvrir
sha256sum NEOMUNDI_EVIDENCE_DEMO_V0.1.zip

# 2. la confronter à celle transmise PAR UN AUTRE CANAL
#    (un écart = ne pas ouvrir, et nous le dire)

# 3. les membres, contre la liste de ce document
unzip -o NEOMUNDI_EVIDENCE_DEMO_V0.1.zip -d recu/
cd recu && sha256sum observations.jsonl measurements.jsonl \
    reference_evaluations.jsonl replay_provenance.jsonl observations.csv rapport.md

# 4. la cohérence interne, et tout le reste
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip --corpus <corpus>
```

L'étape 2 est celle qui compte. Les trois autres sont des contrôles de
cohérence : seule l'étape 2 est une vérification **indépendante**.

---

## L'ancrage extérieur — à prévoir, pas à développer

Aujourd'hui, le registre n'a **aucun ancrage extérieur**. Une chaîne
intégralement réécrite se vérifie parfaitement. C'est la limite que le test de
falsification démontre : une observation effacée partout, décomptes et sommes
refaits, passe tous les contrôles internes.

Trois mécanismes possibles, par coût croissant. **Aucun n'est engagé**, et aucun
ne doit être annoncé comme disponible.

| Mécanisme | Ce qu'il apporterait | Ce qu'il coûterait |
|---|---|---|
| **Publication périodique de l'empreinte de tête** dans un support hors de notre contrôle | une chaîne réécrite divergerait de l'empreinte publiée à cette date | le choix du support, et sa pérennité |
| **Signature de l'archive** par une clé dont la publique est diffusée séparément | l'origine, et l'intégrité à l'émission | la gestion de la clé — une clé perdue invalide tout le passé, une clé compromise invalide tout |
| **Horodatage par un tiers** (RFC 3161 ou équivalent) | une borne temporelle opposable | une dépendance externe, et un contrat |

Deux conditions avant d'en engager un, et elles ne sont pas techniques :

1. **un pilote doit le demander.** Aucun ne l'a fait à ce jour ;
2. **la discipline du registre doit le permettre.** La conception l'anticipe depuis
   l'origine. L'ajouter après coup n'ancre pas le passé : il ancrerait à partir
   de la date de mise en service, et le corpus gelé resterait sans ancrage.

> Ce second point mérite d'être dit à un relecteur : même si nous ancrions
> demain, les 844 et 151 enregistrements déjà gelés ne le seraient pas. Leur
> seule protection restera le double exemplaire et les empreintes de ce
> document.

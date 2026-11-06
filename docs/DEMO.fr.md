<sub>🇬🇧 <a href="DEMO.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Reproduire la démonstration

Cinq minutes, aucun appel réseau, aucun coût, aucune donnée de pilote.

Tout part du corpus **gelé** `GROUNDED-S1`, pas d'un répertoire de travail :
une démonstration qui part d'un état mouvant ne se rejoue pas.

---

## Ce qu'il faut

- L'instrument, dans une version qui produit le schéma d'export `/2` — pour
  l'export et pour la vérification de chaînage.
- Le gel `20261105T1200_GEL_CORPUS_GATE0`.
- Python 3.12 pour `verify.py` — **et rien d'autre** : ni dépendance, ni réseau.

---

## 1. Vérifier le point de départ

Le gel, avant de s'en servir :

```sh
cd <gel>
python verifier_gel.py .
```

Attendu : `12 PASS, 0 FAIL, 3 NOT TESTED`.

Puis le chaînage du registre, avec l'instrument qui l'a écrit :

```sh
station ledger verify --path <gel>/GROUNDED-S1/donnees/ledger.jsonl
```

Attendu : 151 enregistrements, empreinte de tête
`fc1f2787e6e0e24fd70c9b6d252efe99dc9e2fe297233f289254c47a4c7d43b2`,
aucune anomalie.

---

## 2. Produire le dossier

```sh
station campaign export grounded-med-synthetique-v1 \
  --sortie NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
  --registre <gel>/GROUNDED-S1/donnees/ledger.jsonl
```

L'export **refuse** de produire quoi que ce soit si la chaîne ne se vérifie
pas, si la campagne n'a aucun enregistrement, ou si le fichier de sortie existe
déjà. Il relit ensuite l'archive qu'il vient d'écrire et la confronte à ce
qu'il voulait écrire.

Attendu : 1 run, 30 observations, et `archive_sha256`.

> L'empreinte de l'archive **change à chaque export**, parce que le manifeste
> porte l'horodatage de l'export. Les empreintes des membres, elles, sont
> stables : ce sont elles qu'on compare. Celle du 5 novembre 2026 était
> `84ff0decfbc12a71034412a2a8f55f7f89f21dc850b49a4b144ebc2075ea516c`.

---

## 3. Vérifier le dossier, sans NeoMundi

```sh
python verify.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
  --corpus <gel>/GROUNDED-S1/entrees/corpus
```

Attendu : `19 PASS, 0 FAIL, 2 NOT TESTED`. *(mesuré avant l'existence du contrôle de complétude ; toute archive antérieure à ce contrat porte désormais un `NOT TESTED` de plus — voir [consolidation ODA3](ODA3_CONSOLIDATION.fr.md))*

Les deux contrôles non faits sont nommés avec leur raison : le chaînage JCS
(hors de portée d'un vérificateur indépendant, par choix) et l'origine de
l'archive (hors de portée de toute vérification locale).

---

## 4. Montrer que la vérification sert à quelque chose

Un vérificateur qui accepte une archive intacte ne prouve rien tant qu'on n'a
pas montré qu'il refuse une archive touchée.

```sh
python tests/test_falsification.py NEOMUNDI_EVIDENCE_DEMO_V0.1.zip \
  <gel>/GROUNDED-S1/entrees/corpus
```

Attendu : `10/10 altérations détectées, 1 limite déclarée, 0 problème`.

**C'est le moment le plus utile de la démonstration.** La dernière ligne — la
falsification *non* détectée — est celle qu'il faut montrer, pas celle qu'il
faut cacher : une observation effacée partout, décomptes et sommes refaits,
produit une archive cohérente. Seule l'empreinte conservée ailleurs le détecte.

---

## 5. Lire le rapport

Ouvrir `rapport.md` dans l'archive, et s'arrêter sur quatre endroits :

1. **« Valeurs `null` »** — « coût non établi : 30 sur 30 ». Aucune somme n'est
   affichée, parce qu'il n'y a rien à sommer.
2. **« Mesures »** — le tableau par signal. `semantic_instability_score` :
   8 mesurés, 22 `null`. Aucun de ces 22 n'est devenu un `0`.
3. **« Régime d'exécution »** — la garde. Elle dit que `provider_attested`, dans
   ce dossier, atteste un enregistrement rejoué et non un fournisseur, et qu'un
   `neomundi_measurement_id` peut y être une sentinelle.
4. **« Limites »** — sept énoncés, dans l'archive et non dans une plaquette.

---

## Ce que la démonstration établit, et ce qu'elle n'établit pas

**Établi :** un dossier de campagne se produit, se lit, et se vérifie sans
NeoMundi ; la vérification détecte une altération ; les absences sont nommées
et jamais comblées.

**Non établi :** que les signaux mesurés soient justes. Que l'archive soit
authentique — aucune signature, aucun horodatage opposable. Qu'un acheteur
veuille payer pour cela.

Ce dernier point n'est pas une limite technique. C'est la question ouverte.

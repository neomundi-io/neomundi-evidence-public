# -*- coding: utf-8 -*-
"""Les octets commités sont ceux du travail, et aucun artefact texte n'a de CRLF.

    python tests/test_no_crlf.py

POURQUOI CE TEST EXISTE
-----------------------

Constaté le 6 novembre, et il a cassé la CI. Un `.jws` écrit sous Windows
portait des CRLF ; Git, normalisant en LF, changeait ses octets — et donc
son empreinte, de `265144e3…` à `9247482d…`. La preuve d'horodatage, qui
s'engage sur cette empreinte, ne concordait plus.

La signature elle-même survivait, parce que le jeton est découpé sur les
points et que la fin de ligne est retirée. C'est l'**empreinte du fichier**
qui changeait — et c'est elle que l'horodatage atteste.

DEUX CONTRÔLES, ET POURQUOI DEUX
--------------------------------

**Les octets commités sont-ils ceux du travail ?** C'est le contrôle fort :
il détecte directement le mode de panne, quelle qu'en soit la cause —
normalisation de fins de ligne, filtre, ou autre. Un relecteur externe
obtient les octets *commités* ; si l'empreinte citée dans la documentation
est celle du *travail*, elle est fausse pour lui.

**Un artefact texte porte-t-il des CRLF ?** C'est le contrôle de la cause la
plus fréquente, et il la nomme. Restreint aux artefacts **textuels** : une
archive ZIP contient légitimement des `\\r\\n` — son `observations.csv` en
porte par conception.

Les documents (`.md`, `.html`) sont hors périmètre : leur empreinte n'est
attestée nulle part, et les normaliser est souhaitable.

LA FRONTIÈRE, ET POURQUOI ELLE EST LÀ
-------------------------------------

Les producteurs d'artefacts — `sign.py`, `timestamp.py`, `bind.py`,
`make_fixture.py`, `receipt_import.py` — écrivent désormais en **LF
explicite**, parce que leurs sorties sont attestées ou citées par empreinte.

Les **rapports** de vérification (`--json`, `reconciliation.md`) restent
écrits en texte : ils décrivent une vérification, ne sont attestés par rien,
et leur empreinte n'est citée nulle part. Les convertir serait de la propreté,
pas une correction — et ce test ne les couvre donc pas.

Bibliothèque standard seule.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

#: Les répertoires qui portent une chaîne de preuve complète.
DOSSIERS = ("examples/dossier-v1", "examples/attestation", "examples/timestamp",
            "examples/binding", "examples/reconciliation")

#: Extensions des artefacts TEXTUELS, où un CRLF est une faute.
TEXTE = (".jws", ".json", ".txt")

#: Documents : hors périmètre, leur empreinte n'est attestée nulle part.
DOCUMENTS = (".md", ".html")


def main() -> int:
    crlf: list[str] = []
    divergents: list[str] = []
    examines = 0

    # --- contrôle 1 : aucun CRLF dans un artefact TEXTUEL --------------
    for dossier in DOSSIERS:
        base = RACINE / dossier
        if not base.is_dir():
            continue
        for chemin in sorted(base.rglob("*")):
            if not chemin.is_file() or chemin.suffix not in TEXTE:
                continue
            examines += 1
            if b"\r\n" in chemin.read_bytes():
                crlf.append(str(chemin.relative_to(RACINE)).replace("\\", "/"))

    # --- contrôle 2 : les octets COMMITÉS sont ceux du travail ---------
    # C'est le contrôle fort : un relecteur externe obtient les octets
    # commités, et c'est sur eux que portent les empreintes citées.
    suivis = subprocess.run(
        ["git", "ls-files"] + list(DOSSIERS),
        capture_output=True, text=True, cwd=RACINE).stdout.split()
    for nom in suivis:
        chemin = RACINE / nom
        if not chemin.is_file() or chemin.suffix in DOCUMENTS:
            continue
        examines += 1
        dans_git = subprocess.run(["git", "show", ":" + nom],
                                  capture_output=True, cwd=RACINE).stdout
        if dans_git and dans_git != chemin.read_bytes():
            divergents.append(nom)

    print("Octets commités == octets du travail, et aucun CRLF en artefact texte")
    print("%d contrôle(s) de fichier\n" % examines)

    for nom in crlf:
        print("[PROBLEME ] %-54s CRLF dans un artefact texte" % nom)
    for nom in divergents:
        print("[PROBLEME ] %-54s octets commités != octets du travail" % nom)

    if not crlf and not divergents:
        print("[OK       ] aucun CRLF en artefact texte")
        print("[OK       ] les octets commités sont ceux du travail")

    total = len(crlf) + len(divergents)
    print("\nBILAN : %d probleme(s)" % total)
    if total:
        print("\nUn fichier dont les octets changent entre le travail et Git a une")
        print("EMPREINTE différente — et c'est elle que l'horodatage atteste.")
        print("Un relecteur externe obtient les octets COMMITÉS.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

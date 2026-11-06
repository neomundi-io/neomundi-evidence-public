# -*- coding: utf-8 -*-
"""Fabrique un paquet de soumission pilote, valide ou ADVERSE.

    python tests/make_submission.py <dossier> [--profil <nom>] [--zip]

POURQUOI UNE FIXTURE, ET JAMAIS UN PAQUET REEL
----------------------------------------------

Le dossier recu le 30 octobre porte des donnees de pilote. Le commiter
divulguerait ce qui ne nous appartient pas, et c est deja la raison pour
laquelle les corpus reels ne sont pas dans ce depot.

Ces paquets n ont donc AUCUN lien avec un jeu de donnees reel. Ils sont
deterministes a l octet : aucune horloge, aucun alea. Deux generations
rendent le meme paquet, donc un test peut s engager sur une empreinte.

LES PROFILS ADVERSES SONT LE COEUR
----------------------------------

Un ingesteur qui n accepte que des paquets corrects n a pas ete eprouve. Six
profils cassent une propriete chacun, et un seul a la fois -- sinon on ne
sait pas lequel des defauts a ete attrape :

  valide                   tout concorde
  empreinte-fausse         une empreinte declaree ne correspond pas
  paquet-modifie           le FICHIER a bouge apres l ecriture du manifeste
  champ-absent             `execution` manque au manifeste
  artefact-absent          un artefact declare n est pas fourni
  chemin-malveillant       un chemin remonte hors du paquet (`..`)
  provenance-insuffisante  aucun champ de provenance declare

`empreinte-fausse` et `paquet-modifie` se ressemblent et ne disent pas la
meme chose : le premier est un manifeste faux sur un fichier intact, le
second un fichier altere sous un manifeste intact. L ingesteur doit refuser
les deux, et ne peut pas les distinguer -- ce qui est exactement correct.

Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PROFILS = ("valide", "empreinte-fausse", "paquet-modifie", "champ-absent",
           "artefact-absent", "chemin-malveillant", "provenance-insuffisante")

#: Contenus FIXES. Pas d horloge, pas d alea : deux generations rendent les
#: memes octets, donc une empreinte est citable dans un test.
PROMPT = b"Explique en une phrase ce qu une attestation detachee etablit.\n"
REPONSE = (b"Elle etablit qu une partie identifiee s est engagee sur une "
           b"empreinte precise, et rien de plus.\n")
MESURE = json.dumps({
    "schema": "exemple.pilote.mesure/1",
    "item_id": "demo-001",
    "score_declared": "0.8140",
    "verdict_declared": "concordant",
    "note": "Objet synthetique. Aucun lien a un jeu de donnees reel.",
}, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def empreinte(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def construire(sortie: Path, profil: str = "valide") -> Path:
    if profil not in PROFILS:
        raise SystemExit("profil inconnu : %s (connus : %s)"
                         % (profil, ", ".join(PROFILS)))
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "artefacts").mkdir(parents=True, exist_ok=True)

    fichiers = {
        "artefacts/prompt.txt": PROMPT,
        "artefacts/response.txt": REPONSE,
        "artefacts/measurement.json": MESURE,
    }
    for nom, octets in fichiers.items():
        (sortie / nom).write_bytes(octets)

    artefacts = [
        {"path": "artefacts/prompt.txt", "sha256": empreinte(PROMPT),
         "bytes": len(PROMPT), "role": "prompt", "media_type": "text/plain"},
        {"path": "artefacts/response.txt", "sha256": empreinte(REPONSE),
         "bytes": len(REPONSE), "role": "response", "media_type": "text/plain"},
        {"path": "artefacts/measurement.json", "sha256": empreinte(MESURE),
         "bytes": len(MESURE), "role": "measurement",
         "media_type": "application/json"},
    ]

    manifeste = {
        "schema": "neomundi.evidence.submission/1",
        "submission_id": "pilote-demo-001",
        "submitted_at_declared": "2026-11-06T12:00:00Z",
        "pilot": {
            "name_declared": "Pilote de demonstration",
            "reference_declared": "DEMO-B3",
            "contact_declared": None,
        },
        "execution": {
            "kind_declared": "single_call",
            "model_declared": "modele-de-demonstration-v1",
            "provider_declared": "fournisseur-de-demonstration",
            "executed_at_declared": "2026-11-06T11:58:00Z",
            "parameters_declared": {"temperature": "0", "max_tokens": "256"},
            "notes_declared": None,
        },
        "artifacts": artefacts,
        "provenance_declared": {
            "code_reference_declared": "exemple-pilote@0.1.0",
            "environment_declared": "conteneur de demonstration",
            "evaluator_declared": None,
            "notes_declared": "Provenance DECLAREE. Rien dans ce paquet ne "
                              "permet de la confronter.",
        },
        "limits_declared": [
            "Ce paquet n etablit pas que l execution a eu lieu.",
            "Les empreintes declarees portent sur les fichiers fournis, pas "
            "sur une execution.",
        ],
    }

    # ---- les profils adverses, un defaut chacun ------------------------
    if profil == "empreinte-fausse":
        # Manifeste FAUX sur un fichier intact : un caractere de l empreinte
        # declaree change, et rien d autre.
        bon = manifeste["artifacts"][1]["sha256"]
        manifeste["artifacts"][1]["sha256"] = \
            ("0" if bon[0] != "0" else "1") + bon[1:]
    elif profil == "paquet-modifie":
        # Fichier ALTERE sous un manifeste intact. L inverse du precedent, et
        # l ingesteur ne peut pas les distinguer -- ce qui est correct :
        # dans les deux cas, ce qu il tient n est pas ce qui est annonce.
        (sortie / "artefacts/response.txt").write_bytes(
            REPONSE.replace(b"et rien de plus", b"et bien davantage"))
    elif profil == "champ-absent":
        del manifeste["execution"]
    elif profil == "artefact-absent":
        # Declare, et pas fourni. Ce n est pas une fraude : c est un paquet
        # incomplet, donc le verdict attendu est INCOMPLET et non REJETE.
        (sortie / "artefacts/measurement.json").unlink()
    elif profil == "chemin-malveillant":
        manifeste["artifacts"].append({
            "path": "../../etc/passwd",
            "sha256": "0" * 64, "bytes": 0, "role": "other",
            "media_type": None,
        })
    elif profil == "provenance-insuffisante":
        manifeste["provenance_declared"] = {
            "code_reference_declared": None,
            "environment_declared": None,
            "evaluator_declared": None,
            "notes_declared": None,
        }

    (sortie / "submission.json").write_bytes(
        (json.dumps(manifeste, ensure_ascii=False, indent=2, sort_keys=True)
         + "\n").encode("utf-8"))
    return sortie


def empaqueter(dossier: Path, cible: Path) -> Path:
    """Un ZIP DETERMINISTE : dates et `create_system` epingles.

    `zipfile.ZipInfo` met `create_system` a 0 sous Windows et 3 ailleurs, et
    ce champ entre dans l annuaire central. Sans l epingler, la MEME commande
    rendrait deux archives differentes selon le systeme -- defaut constate le
    6 novembre sur la fixture V1.
    """
    noms = sorted(p.relative_to(dossier).as_posix()
                  for p in dossier.rglob("*") if p.is_file())
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
        for nom in noms:
            entree = zipfile.ZipInfo(nom, date_time=(2026, 1, 1, 0, 0, 0))
            entree.create_system = 0
            entree.external_attr = 0o644 << 16
            z.writestr(entree, (dossier / nom).read_bytes())
    return cible


def main() -> int:
    a = argparse.ArgumentParser(
        description="Fabrique un paquet de soumission pilote, valide ou adverse.")
    a.add_argument("sortie", type=Path)
    a.add_argument("--profil", default="valide", choices=PROFILS)
    a.add_argument("--zip", action="store_true",
                   help="empaqueter en ZIP deterministe a cote du dossier")
    arguments = a.parse_args()

    dossier = construire(arguments.sortie, arguments.profil)
    print("paquet ecrit : %s" % dossier)
    print("  profil   : %s" % arguments.profil)
    fichiers = sorted(p.relative_to(dossier).as_posix()
                      for p in dossier.rglob("*") if p.is_file())
    print("  fichiers : %d -- %s" % (len(fichiers), ", ".join(fichiers)))
    if arguments.zip:
        cible = dossier.parent / (dossier.name + ".zip")
        empaqueter(dossier, cible)
        print("  zip      : %s (%s)"
              % (cible, hashlib.sha256(cible.read_bytes()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

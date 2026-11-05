# -*- coding: utf-8 -*-
"""Tests de la liaison observation <-> artefacts.

    python tests/test_binding.py <archive_evidence.zip> <repertoire_exemple>

Trois familles, et la troisieme est la plus importante :

  POSITIF        un manifeste honnete et complet est accepte, au bon niveau
  NEGATIF        dix-sept manifestes fautifs sont tous refus, chacun pour sa
                 raison propre
  SCIENTIFIQUE   deux manifestes au texte IDENTIQUE, l un ancre et l autre
                 non, doivent etre distingues

Le test scientifique est la raison d etre de tout ce dispositif. Si un outil
rendait le meme verdict pour les deux, il mesurerait la prose et non la
preuve -- et une description textuelle d une execution ne constitue pas une
preuve que cette execution a eu lieu.

Bibliotheque standard seule.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BIND = RACINE / "bind.py"

# Le meme texte, mot pour mot, dans les deux scenarios du test scientifique.
ENONCE = (
    "Le 22 octobre 2026 a 09:00:00 UTC, l item 00ff4465 a ete soumis au "
    "modele grounded-s1-2026-10-22. La reponse a ete recue en 512 ms, puis "
    "mesuree en version 3.3.0. L enregistrement a ete scelle dans un registre "
    "chaine, et l archive a ete gelee le 5 novembre 2026."
)


def lancer(manifeste: Path, racine: Path, archive: Path | None) -> tuple[int, str]:
    commande = [sys.executable, str(BIND), "verify", str(manifeste), "--root", str(racine)]
    if archive is not None:
        commande += ["--archive", str(archive)]
    fini = subprocess.run(
        commande, capture_output=True, text=True, check=False, encoding="utf-8", errors="replace"
    )
    return fini.returncode, fini.stdout + fini.stderr


def motif(sortie: str) -> str:
    return next((l.strip() for l in sortie.splitlines() if l.startswith("[FAIL")), "")


def niveau(sortie: str) -> str:
    for ligne in sortie.splitlines():
        if ligne.startswith("Niveau de garantie DERIVE"):
            return ligne.split(":", 1)[1].strip()
    return "aucun"


# --------------------------------------------------------------------------
# Les alterations. Chacune recoit le manifeste honnete et rend sa version
# fautive ; certaines touchent aussi les fichiers sous la racine.
# --------------------------------------------------------------------------


class SauteLeCas(Exception):
    """Le cas ne peut pas etre construit dans cet environnement."""


def alt_artefact_absent(m, racine):
    (racine / m["artifacts"][0]["path"]).unlink()
    return m


def alt_artefact_modifie(m, racine):
    """Un octet de plus dans l artefact, le manifeste inchange."""
    chemin = racine / m["artifacts"][0]["path"]
    chemin.write_bytes(chemin.read_bytes() + b" ")
    return m


def alt_artefact_et_manifeste_accordes(m, racine):
    """Le cas serieux : l artefact est modifie ET le manifeste refait.

    Un faussaire qui recalcule l empreinte de son faux artefact et l inscrit
    partout dans le manifeste obtient un document interieurement coherent.
    Seule la confrontation a l ENREGISTREMENT le prend -- et c est pour cela
    que `declared_digests` doit etre confronte, et pas seulement recopie.
    """
    import hashlib

    chemin = racine / m["artifacts"][0]["path"]
    faux = b"Une reponse entierement reecrite par un tiers."
    chemin.write_bytes(faux)
    empreinte = hashlib.sha256(faux).hexdigest()
    m["artifacts"][0]["sha256"] = empreinte
    m["artifacts"][0]["size_bytes"] = len(faux)
    m["declared_digests"][m["artifacts"][0]["binds_to"]] = empreinte
    return m


def alt_revendique_signature(m, racine):
    """`cryptographically_attested` sans aucune signature verifiable."""
    m["artifacts"][0]["claimed_assurance"] = "cryptographically_attested"
    return m


def alt_revendique_signature_avec_signature(m, racine):
    """Meme revendication, mais avec une signature au manifeste.

    Elle ne doit rien changer : ce depot ne verifie aucune signature, donc
    une signature presente ne peut pas faire monter le niveau derive.
    """
    m["artifacts"][0]["claimed_assurance"] = "cryptographically_attested"
    m["signatures"] = [
        {
            "algorithm": "ed25519",
            "key_id": "exemple-sans-cle-publiee",
            "value": "AAAA" * 16,
            "covers": "manifest",
        }
    ]
    return m


def alt_revendique_sans_ancrage(m, racine):
    """`reference_verifiable` revendique alors que `binds_to` est null."""
    m["artifacts"][0]["binds_to"] = None
    m["artifacts"][0]["claimed_assurance"] = "reference_verifiable"
    return m


def alt_ancrage_non_declare(m, racine):
    """L artefact pretend se lier a une empreinte que l enregistrement n a pas."""
    m["declared_digests"].pop(m["artifacts"][0]["binds_to"], None)
    return m


def alt_observation_inexistante(m, racine):
    m["subject"]["observation_id"] = "obs-" + "0" * 64
    return m


def alt_empreinte_archive_fausse(m, racine):
    m["subject"]["source_archive"]["sha256"] = "f" * 64
    return m


def alt_record_sha_reecrit(m, racine):
    m["subject"]["record_sha256"] = "a" * 64
    return m


def alt_chemin_absolu(m, racine):
    m["artifacts"][0]["path"] = "/etc/passwd"
    return m


def alt_traversee(m, racine):
    m["artifacts"][0]["path"] = "../../../secret.txt"
    return m


def alt_lien_symbolique(m, racine):
    """Un lien symbolique qui sort de la racine. Souvent refuse par Windows."""
    cible = racine.parent / "hors-racine.txt"
    cible.write_text("contenu hors racine", encoding="utf-8")
    lien = racine / "lien.txt"
    try:
        lien.symlink_to(cible)
    except (OSError, NotImplementedError) as erreur:
        raise SauteLeCas("creation de lien symbolique refusee : %s" % erreur) from erreur
    m["artifacts"][0]["path"] = "lien.txt"
    return m


def alt_schema_inconnu(m, racine):
    m["schema"] = "neomundi.evidence.manifest/99"
    return m


def alt_manifeste_tableau(m, racine):
    return ["un tableau, pas un objet"]


def alt_identifiants_en_double(m, racine):
    m["artifacts"][1]["artifact_id"] = m["artifacts"][0]["artifact_id"]
    return m


def alt_taille_fausse(m, racine):
    m["artifacts"][0]["size_bytes"] = 999999
    return m


NEGATIFS = [
    ("artefact absent", alt_artefact_absent, "NOT TESTED"),
    ("artefact modifie d un octet", alt_artefact_modifie, "FAIL"),
    ("artefact ET manifeste refaits de concert", alt_artefact_et_manifeste_accordes, "FAIL"),
    ("revendique une attestation sans signature", alt_revendique_signature, "FAIL"),
    ("revendique une attestation avec signature non verifiee",
     alt_revendique_signature_avec_signature, "FAIL"),
    ("revendique une reference sans ancrage", alt_revendique_sans_ancrage, "FAIL"),
    ("ancrage absent des empreintes declarees", alt_ancrage_non_declare, "FAIL"),
    ("observation inexistante dans l archive", alt_observation_inexistante, "FAIL"),
    ("empreinte d archive fausse", alt_empreinte_archive_fausse, "FAIL"),
    ("record_sha256 reecrit au manifeste", alt_record_sha_reecrit, "FAIL"),
    ("chemin d artefact absolu", alt_chemin_absolu, "FAIL"),
    ("traversee de repertoire", alt_traversee, "FAIL"),
    ("lien symbolique sortant", alt_lien_symbolique, "FAIL"),
    ("schema de manifeste inconnu", alt_schema_inconnu, "FAIL"),
    ("manifeste = tableau JSON", alt_manifeste_tableau, "FAIL"),
    ("artifact_id en double", alt_identifiants_en_double, "FAIL"),
    ("taille annoncee fausse", alt_taille_fausse, "FAIL"),
]


# --------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 3:
        print("emploi : python tests/test_binding.py <archive.zip> <repertoire_exemple>")
        return 2
    archive = Path(sys.argv[1]).resolve()
    exemple = Path(sys.argv[2]).resolve()
    honnete = json.loads((exemple / "manifest.json").read_text(encoding="utf-8"))

    problemes = []

    # ------------------------------------------------------------------ positif
    print("POSITIF -- un manifeste honnete\n")
    code, sortie = lancer(exemple / "manifest.json", exemple, archive)
    attendu = code == 0 and niveau(sortie) == "reference_verifiable"
    print("[%-9s] accepte, niveau derive %s" % ("OK" if attendu else "PROBLEME", niveau(sortie)))
    if not attendu:
        problemes.append("le manifeste honnete n est pas accepte au niveau attendu")

    # Sans l archive, le niveau tient mais la confrontation ne se fait pas.
    code_sans, sortie_sans = lancer(exemple / "manifest.json", exemple, None)
    sans_confrontation = "[NOT TESTED] le sujet existe dans son archive" in sortie_sans
    print("[%-9s] sans --archive : la confrontation est NOT TESTED, pas PASS"
          % ("OK" if sans_confrontation and code_sans == 0 else "PROBLEME"))
    if not (sans_confrontation and code_sans == 0):
        problemes.append("sans archive, la confrontation n est pas marquee NOT TESTED")

    # ------------------------------------------------------------------ negatifs
    print("\nNEGATIF -- dix-sept manifestes fautifs\n")
    for nom, alteration, attendu_etat in NEGATIFS:
        travail = Path(tempfile.mkdtemp(prefix="binding-")) / "racine"
        try:
            shutil.copytree(exemple, travail)
            try:
                altere = alteration(copy.deepcopy(honnete), travail)
            except SauteLeCas as raison:
                print("[INAPPLIC.] %-44s %s" % (nom, raison))
                continue
            cible = travail / "manifest.json"
            cible.write_text(
                json.dumps(altere, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            code, sortie = lancer(cible, travail, archive)

            if attendu_etat == "FAIL":
                reussi = code != 0
                detail = motif(sortie)
            else:
                # Un artefact absent n est pas une faute du manifeste : la
                # liaison tombe a `declared`, et c est cela qu on verifie.
                reussi = code == 0 and niveau(sortie) == "declared"
                detail = "niveau derive %s" % niveau(sortie)
            print("[%-9s] %-44s %s" % ("REFUSE" if attendu_etat == "FAIL" else "DEGRADE",
                                       nom, detail[:62]) if reussi
                  else "[PROBLEME ] %-44s %s" % (nom, detail[:62]))
            if not reussi:
                problemes.append(nom)
        finally:
            shutil.rmtree(travail.parent, ignore_errors=True)

    # -------------------------------------------------------------- scientifique
    print("\nSCIENTIFIQUE -- deux manifestes au texte IDENTIQUE\n")
    travail = Path(tempfile.mkdtemp(prefix="binding-ab-"))
    try:
        # Scenario A : la prose, et rien dessous.
        a = copy.deepcopy(honnete)
        a["statements"] = [ENONCE]
        a["artifacts"] = []
        racine_a = travail / "A"
        racine_a.mkdir(parents=True)
        (racine_a / "manifest.json").write_text(
            json.dumps(a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # Scenario B : la MEME prose, et les artefacts ancres dessous.
        b = copy.deepcopy(honnete)
        b["statements"] = [ENONCE]
        racine_b = travail / "B"
        shutil.copytree(exemple, racine_b)
        (racine_b / "manifest.json").write_text(
            json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        meme_texte = a["statements"] == b["statements"]
        code_a, sortie_a = lancer(racine_a / "manifest.json", racine_a, archive)
        code_b, sortie_b = lancer(racine_b / "manifest.json", racine_b, archive)
        niveau_a, niveau_b = niveau(sortie_a), niveau(sortie_b)

        print("  Scenario A : %d enonce(s), %d artefact(s) -> niveau %s"
              % (len(a["statements"]), len(a["artifacts"]), niveau_a))
        print("  Scenario B : %d enonce(s), %d artefact(s) -> niveau %s"
              % (len(b["statements"]), len(b["artifacts"]), niveau_b))
        print()

        distingue = (
            meme_texte
            and code_a == 0
            and code_b == 0
            and niveau_a == "declared"
            and niveau_b == "reference_verifiable"
        )
        print("[%-9s] texte identique, verdicts distincts" % ("OK" if distingue else "PROBLEME"))
        if not distingue:
            problemes.append("les deux scenarios ne sont pas distingues")
        else:
            print("            A n est refuse NI accepte comme preuve : il est")
            print("            rendu pour ce qu il est, un document declaratif.")
            print("            B etablit que les artefacts sont ceux de")
            print("            l enregistrement. Rien de plus.")
    finally:
        shutil.rmtree(travail, ignore_errors=True)

    # ------------------------------------------------------------------- bilan
    print("\nBILAN : %d probleme(s)" % len(problemes))
    for p in problemes:
        print("  - %s" % p)
    if not problemes:
        print("\nCe que ces tests etablissent : l outil refuse une liaison fautive,")
        print("et ne confond pas un recit avec une preuve.")
        print("Ce qu ils n etablissent pas : qu une liaison acceptee corresponde")
        print("a une execution reelle. Aucune signature, aucun ancrage exterieur.")
    return 1 if problemes else 0


if __name__ == "__main__":
    sys.exit(main())

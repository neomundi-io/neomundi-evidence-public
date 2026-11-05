# -*- coding: utf-8 -*-
"""Sonde contradictoire : chercher ou le verificateur conclurait a tort.

Emploi :  python tests/test_adversarial.py <archive_intacte.zip> [corpus]

Les tests de falsification existants eprouvent dix alterations du CONTENU.
Cette sonde-ci eprouve autre chose : la FORME de l'archive, et les cas ou un
controle pourrait passer alors qu'il ne devrait pas. Elle est volontairement
hostile a notre propre outil.

Chaque cas rend l'un de trois verdicts, et aucun n'est un echec de la sonde :

    DETECTE    le verificateur refuse. C'est ce qu'on veut.
    MANQUE     le verificateur accepte. A instruire : defaut, ou limite a dire.
    INAPPLIC.  le cas ne peut pas etre construit dans cet environnement.

Un `MANQUE` n'est pas forcement un bug : certains cas sont hors de portee d'un
verificateur de fichiers, et la bonne reponse est alors de les documenter comme
limites plutot que de pretendre les couvrir.

Bibliotheque standard seule.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
VERIFY = RACINE / "verify.py"

DETECTE, MANQUE, INAPPLICABLE = "DETECTE", "MANQUE", "INAPPLIC."

# Ecrites par code de caractere : un saut de ligne et une sequence
# volontairement indecodable en UTF-8.
SAUT = bytes([10])
OCTETS_NON_UTF8 = bytes([255, 254, 0, 1])


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def lire(source: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(source) as archive:
        return {nom: archive.read(nom) for nom in archive.namelist()}


def resommer(membres: dict[str, bytes], membre_sommes: str = "checksums.sha256") -> dict[str, bytes]:
    couverts = [n for n in membres if n != membre_sommes]
    membres[membre_sommes] = "".join(
        "%s  %s\n" % (sha256(membres[n]), n) for n in couverts
    ).encode("utf-8")
    return membres


def ecrire(membres: dict[str, bytes], cible: Path, entrees_brutes: list | None = None) -> Path:
    with zipfile.ZipFile(cible, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for nom, octets in membres.items():
            info = zipfile.ZipInfo(nom, date_time=(2026, 11, 5, 0, 0, 0))
            archive.writestr(info, octets)
        for info, octets in entrees_brutes or []:
            archive.writestr(info, octets)
    return cible


def verifier(archive: Path, corpus: Path | None) -> tuple[int, str]:
    commande = [sys.executable, str(VERIFY), str(archive)]
    if corpus is not None:
        commande += ["--corpus", str(corpus)]
    fini = subprocess.run(commande, capture_output=True, text=True, check=False,
                          encoding="utf-8", errors="replace")
    return fini.returncode, fini.stdout + fini.stderr


# --------------------------------------------------------------------------
# Les cas. Chacun rend (membres, entrees_brutes) ou leve SauteLeCas.
# --------------------------------------------------------------------------


class SauteLeCas(Exception):
    """Le cas ne peut pas etre construit ici."""


def cas_membre_surnumeraire(m):
    """Un fichier de plus, non declare au manifeste de sommes."""
    m["artifacts/extra.json"] = b'{"injecte": true}\n'
    return m, None


def cas_somme_pour_membre_absent(m):
    """Le manifeste de sommes annonce un membre qui n'est pas la."""
    m["checksums.sha256"] = m["checksums.sha256"] + (
        "%s  fantome.jsonl\n" % ("0" * 64)
    ).encode("utf-8")
    return m, None


def cas_chemin_absolu(m):
    """Un membre dont le chemin est absolu."""
    info = zipfile.ZipInfo("/etc/passwd", date_time=(2026, 11, 5, 0, 0, 0))
    return m, [(info, b"root:x:0:0\n")]


def cas_traversee_antislash(m):
    """Traversee de repertoire ecrite a la mode Windows."""
    info = zipfile.ZipInfo("..\\..\\evade.txt", date_time=(2026, 11, 5, 0, 0, 0))
    return m, [(info, b"sortie du repertoire cible\n")]


def cas_doublon_de_nom(m):
    """Deux entrees ZIP portent le MEME nom, avec des contenus differents.

    `ZipFile.read` rend la DERNIERE ; `namelist` les liste toutes les deux.
    Un verificateur qui somme ce que `read` rend peut valider l'une pendant
    qu'un extracteur ecrit l'autre.
    """
    nom = "observations.jsonl"
    info = zipfile.ZipInfo(nom, date_time=(2026, 11, 5, 0, 0, 0))
    return m, [(info, b'{"payload":{"observation_id":"obs-INJECTE"},"integrity":{}}\n')]


def cas_lien_symbolique(m):
    """Un membre declare comme lien symbolique vers un fichier du systeme."""
    info = zipfile.ZipInfo("artifacts/lien", date_time=(2026, 11, 5, 0, 0, 0))
    info.create_system = 3                      # UNIX
    info.external_attr = (0o120777 << 16)       # S_IFLNK | 0777
    return m, [(info, b"/etc/passwd")]


def cas_schema_inconnu(m):
    man = json.loads(m["manifest.json"])
    man["schema"] = "station.export.campagne/99"
    m["manifest.json"] = json.dumps(man, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(m), None


def cas_schema_absent(m):
    man = json.loads(m["manifest.json"])
    man.pop("schema", None)
    m["manifest.json"] = json.dumps(man, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(m), None


def cas_observation_dupliquee(m):
    """Le meme observation_id, deux fois. Les decomptes restent justes."""
    lignes = m["observations.jsonl"].splitlines()
    if len(lignes) < 2:
        raise SauteLeCas("pas assez d'observations")
    lignes[1] = lignes[0]
    m["observations.jsonl"] = b"\n".join(lignes) + b"\n"
    return resommer(m), None


def cas_mesure_sans_observation_id(m):
    """Une mesure dont l'observation_id est null : la jointure devient creuse."""
    if "measurements.jsonl" not in m:
        raise SauteLeCas("archive sans mesures")
    lignes = m["measurements.jsonl"].splitlines()
    e = json.loads(lignes[0])
    e["payload"]["observation_id"] = None
    lignes[0] = json.dumps(e, separators=(",", ":")).encode("utf-8")
    m["measurements.jsonl"] = b"\n".join(lignes) + b"\n"
    return resommer(m), None


def cas_jsonl_vide_decomptes_mentent(m):
    """Les fichiers sont vides, le manifeste annonce toujours ses decomptes."""
    m["observations.jsonl"] = b""
    return resommer(m), None


def cas_sommes_vides(m):
    """Le manifeste de sommes est vide : plus rien n'est couvert."""
    m["checksums.sha256"] = b""
    return m, None


def cas_zip_imbrique(m):
    """Un membre qui est lui-meme une archive : l'outil la suit-il ?"""
    interne = Path(tempfile.mkdtemp()) / "interne.zip"
    with zipfile.ZipFile(interne, "w") as z:
        z.writestr("charge.txt", b"x" * 1024)
    m["artifacts/imbrique.zip"] = interne.read_bytes()
    return resommer(m), None


def cas_manifeste_non_json(m):
    m["manifest.json"] = b"ceci n'est pas du JSON"
    return resommer(m), None


def cas_horodatage_futur(m):
    """Une date d'export dans le futur. Rien ne la contredit."""
    man = json.loads(m["manifest.json"])
    cle = "exporte_le" if "exporte_le" in man else "construit_le"
    man[cle] = "2099-01-01T00:00:00Z"
    m["manifest.json"] = json.dumps(man, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(m), None


# --------------------------------------------------------------------------
# Entrees malformees. Attendu : un VERDICT, jamais une trace d appels.
#
# Un verificateur recoit par definition des archives dont on ne sait pas si
# elles sont saines. S il plante, il ne rend aucun verdict -- et son code de
# sortie 1 devient indistinguable d un FAIL legitime pour qui l automatise.
#
# Les neuf cas ci-dessous ont tous ete observes avant correction : sept
# faisaient planter l outil. Ils restent ici comme cas de non-regression.
# --------------------------------------------------------------------------


def mal_manifeste_illisible(m):
    m["manifest.json"] = b"{ ceci n est pas du JSON"
    return resommer(m), None


def mal_manifeste_tableau(m):
    """JSON valide, forme fausse : un tableau la ou un objet est attendu."""
    m["manifest.json"] = b'["un tableau, pas un objet"]'
    return resommer(m), None


def mal_observations_corrompu(m):
    lignes = m["observations.jsonl"].splitlines()
    lignes[0] = b'{"payload": {"observation_id": tronque'
    m["observations.jsonl"] = SAUT.join(lignes) + SAUT
    return resommer(m), None


def mal_mesures_corrompu(m):
    if "measurements.jsonl" not in m:
        raise SauteLeCas("archive sans mesures")
    lignes = m["measurements.jsonl"].splitlines()
    lignes[0] = b"{{{"
    m["measurements.jsonl"] = SAUT.join(lignes) + SAUT
    return resommer(m), None


def mal_observations_non_objet(m):
    """Une ligne qui est une chaine JSON : valide, mais pas un enregistrement."""
    lignes = m["observations.jsonl"].splitlines()
    lignes[0] = b'"une chaine au lieu d un objet"'
    m["observations.jsonl"] = SAUT.join(lignes) + SAUT
    return resommer(m), None


def mal_sommes_binaire(m):
    m["checksums.sha256"] = OCTETS_NON_UTF8 + b" pas de l UTF-8"
    return m, None


def mal_sommes_sans_separateur(m):
    """Les sommes sans le double espace : le decoupage ne trouve plus rien."""
    m["checksums.sha256"] = b"0" * 64 + b" observations.jsonl" + SAUT
    return m, None


def mal_decomptes_non_entiers(m):
    """Les decomptes du manifeste sont des chaines : A-04 de l audit."""
    man = json.loads(m["manifest.json"])
    decomptes = man.get("decomptes") or man.get("counts")
    if not isinstance(decomptes, dict) or not decomptes:
        raise SauteLeCas("manifeste sans decomptes")
    for cle in decomptes:
        decomptes[cle] = "beaucoup"
    m["manifest.json"] = json.dumps(man, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(m), None


def mal_rapport_binaire(m):
    if "rapport.md" not in m:
        raise SauteLeCas("archive sans rapport")
    m["rapport.md"] = OCTETS_NON_UTF8 + b" pas de l UTF-8"
    return resommer(m), None


MALFORMES = [
    ("manifeste illisible", mal_manifeste_illisible),
    ("manifeste = tableau JSON", mal_manifeste_tableau),
    ("observations.jsonl corrompu", mal_observations_corrompu),
    ("measurements.jsonl corrompu", mal_mesures_corrompu),
    ("observations.jsonl ligne non-objet", mal_observations_non_objet),
    ("checksums.sha256 binaire", mal_sommes_binaire),
    ("checksums.sha256 sans separateur", mal_sommes_sans_separateur),
    ("manifeste a decomptes non entiers", mal_decomptes_non_entiers),
    ("rapport.md binaire", mal_rapport_binaire),
]


CAS = [
    ("un membre surnumeraire, non declare", cas_membre_surnumeraire, True),
    ("une somme annoncee pour un membre absent", cas_somme_pour_membre_absent, True),
    ("un membre a chemin absolu", cas_chemin_absolu, True),
    ("une traversee de repertoire a l'antislash", cas_traversee_antislash, True),
    ("deux entrees ZIP du meme nom", cas_doublon_de_nom, True),
    ("un membre declare lien symbolique", cas_lien_symbolique, True),
    ("un schema d'export inconnu", cas_schema_inconnu, True),
    ("un manifeste sans schema", cas_schema_absent, True),
    ("un observation_id en double", cas_observation_dupliquee, True),
    ("une mesure sans observation_id", cas_mesure_sans_observation_id, True),
    ("un JSONL vide et des decomptes qui mentent", cas_jsonl_vide_decomptes_mentent, True),
    ("un manifeste de sommes vide", cas_sommes_vides, True),
    ("une archive imbriquee dans l'archive", cas_zip_imbrique, False),
    ("un manifeste illisible", cas_manifeste_non_json, True),
    ("un horodatage d'export dans le futur", cas_horodatage_futur, False),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("emploi : python tests/test_adversarial.py <archive_intacte.zip> [corpus]")
        return 2
    source = Path(sys.argv[1]).resolve()
    corpus = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    print("Sonde contradictoire — %s" % source.name)
    print("empreinte            : %s\n" % sha256(source.read_bytes()))

    code, _ = verifier(source, corpus)
    print("[%-9s] l'archive intacte est acceptee" % ("OK" if code == 0 else "PROBLEME"))
    print()

    temporaire = Path(tempfile.mkdtemp(prefix="adversarial-"))
    resultats = []
    try:
        for index, (nom, fabrique, devrait_detecter) in enumerate(CAS):
            cible = temporaire / ("cas%02d.zip" % index)
            try:
                membres, brutes = fabrique(lire(source))
            except SauteLeCas as raison:
                resultats.append((INAPPLICABLE, nom, str(raison), devrait_detecter))
                print("[%-9s] %-48s %s" % (INAPPLICABLE, nom, raison))
                continue
            ecrire(membres, cible, brutes)
            code, sortie = verifier(cible, corpus)
            motif = next((l.strip() for l in sortie.splitlines() if l.startswith("[FAIL")), "")
            verdict = DETECTE if code != 0 else MANQUE
            resultats.append((verdict, nom, motif, devrait_detecter))
            print("[%-9s] %-48s %s" % (verdict, nom, motif[:70]))
    finally:
        shutil.rmtree(temporaire, ignore_errors=True)

    detectes = sum(1 for v, _, _, _ in resultats if v == DETECTE)
    manques = [(n, d) for v, n, _, d in resultats if v == MANQUE]
    inapplicables = sum(1 for v, _, _, _ in resultats if v == INAPPLICABLE)

    print("\nBILAN : %d detectes, %d manques, %d inapplicables, sur %d cas"
          % (detectes, len(manques), inapplicables, len(CAS)))

    attendus = [n for n, devrait in manques if devrait]
    toleres = [n for n, devrait in manques if not devrait]
    if attendus:
        print("\nManques sur des cas qui DEVRAIENT etre detectes :")
        for n in attendus:
            print("  - %s" % n)
    if toleres:
        print("\nManques attendus, a documenter comme limites :")
        for n in toleres:
            print("  - %s" % n)

    # ----------------------------------------------------------------------
    # Robustesse : l outil rend-il un verdict sur une entree malformee ?
    # ----------------------------------------------------------------------
    print("\nEntrees malformees -- attendu : un verdict, jamais un plantage\n")
    temporaire = Path(tempfile.mkdtemp(prefix="malformes-"))
    plantages = []
    try:
        for index, (nom, fabrique) in enumerate(MALFORMES):
            cible = temporaire / ("mal%02d.zip" % index)
            try:
                membres, brutes = fabrique(lire(source))
            except SauteLeCas as raison:
                print("[%-9s] %-40s %s" % (INAPPLICABLE, nom, raison))
                continue
            ecrire(membres, cible, brutes)
            _, sortie = verifier(cible, corpus)
            ligne_bilan = next(
                (l for l in sortie.splitlines() if l.startswith("BILAN")), ""
            )
            if not ligne_bilan:
                # Aucun BILAN : l outil n a rendu aucun verdict.
                trace = next(
                    (l.strip() for l in reversed(sortie.splitlines()) if l.strip()), "?"
                )
                plantages.append((nom, trace))
                print("[PLANTAGE ] %-40s %s" % (nom, trace[:60]))
            else:
                motif = next(
                    (l.strip() for l in sortie.splitlines() if l.startswith("[FAIL")), ""
                )
                print("[VERDICT  ] %-40s %s" % (nom, (motif or ligne_bilan)[:60]))
    finally:
        shutil.rmtree(temporaire, ignore_errors=True)

    if plantages:
        print("\n%d entree(s) malformee(s) font PLANTER l outil :" % len(plantages))
        for nom, trace in plantages:
            print("  - %-40s %s" % (nom, trace))
    else:
        print("\nAucun plantage : toute entree malformee rend un verdict motive.")

    print("\nCette sonde eprouve la FORME de l'archive. Elle ne dit rien de")
    print("l'authenticite, de la provenance, ni de la verite de l'execution.")
    # Le code de sortie signale les manques NON prevus et les plantages : ce
    # sont eux qui demandent une decision, pas les limites deja connues.
    return 1 if attendus or plantages else 0


if __name__ == "__main__":
    sys.exit(main())

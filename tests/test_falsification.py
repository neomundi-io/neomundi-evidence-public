# -*- coding: utf-8 -*-
"""Tests de falsification : le verificateur detecte-t-il reellement une alteration ?

Un verificateur qui rend PASS sur une archive intacte ne prouve rien tant qu'on
n'a pas montre qu'il rend FAIL sur une archive touchee. Ce fichier fabrique des
archives alterees, une par classe d'attaque, et exige l'echec.

Il porte aussi le cas qui ECHOUE a etre detecte, et c'est volontaire : une
limite constatee vaut mieux qu'une limite supposee.

Emploi :  python tests/test_falsification.py <archive_intacte.zip>

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


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def lire(source: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(source) as archive:
        return {nom: archive.read(nom) for nom in archive.namelist()}


def ecrire(membres: dict[str, bytes], cible: Path) -> Path:
    with zipfile.ZipFile(cible, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for nom, octets in membres.items():
            info = zipfile.ZipInfo(nom, date_time=(2026, 11, 5, 0, 0, 0))
            archive.writestr(info, octets)
    return cible


def resommer(membres: dict[str, bytes]) -> dict[str, bytes]:
    """Recalcule `checksums.sha256` : ce qu'un falsificateur soigneux ferait."""
    couverts = [n for n in membres if n != "checksums.sha256"]
    membres["checksums.sha256"] = "".join(
        "%s  %s\n" % (sha256(membres[n]), n) for n in couverts
    ).encode("utf-8")
    return membres


def verifier(archive: Path, corpus: Path | None) -> tuple[int, str]:
    commande = [sys.executable, str(VERIFY), str(archive)]
    if corpus is not None:
        commande += ["--corpus", str(corpus)]
    acheve = subprocess.run(commande, capture_output=True, text=True, check=False)
    return acheve.returncode, acheve.stdout + acheve.stderr


# --------------------------------------------------------------------------
# Les alterations
# --------------------------------------------------------------------------


def un_octet_change(membres: dict[str, bytes]) -> dict[str, bytes]:
    """Un seul octet d'une mesure, sans toucher aux sommes."""
    octets = bytearray(membres["measurements.jsonl"])
    for index, valeur in enumerate(octets):
        if chr(valeur).isdigit() and chr(valeur) != "0":
            octets[index] = ord("0")
            break
    membres["measurements.jsonl"] = bytes(octets)
    return membres


def une_mesure_retiree(membres: dict[str, bytes]) -> dict[str, bytes]:
    lignes = membres["measurements.jsonl"].splitlines()
    membres["measurements.jsonl"] = b"\n".join(lignes[:-1]) + b"\n"
    return resommer(membres)


def un_signal_null_declare_mesure(membres: dict[str, bytes]) -> dict[str, bytes]:
    lignes = membres["measurements.jsonl"].splitlines()
    sortie = []
    fait = False
    for ligne in lignes:
        enregistrement = json.loads(ligne)
        signaux = enregistrement["payload"].get("signals") or {}
        nuls = [nom for nom, valeur in signaux.items() if valeur is None]
        if nuls and not fait:
            enregistrement["payload"]["measured_signals"] = sorted(
                set(enregistrement["payload"].get("measured_signals") or []) | {nuls[0]}
            )
            fait = True
            ligne = json.dumps(enregistrement, separators=(",", ":")).encode("utf-8")
        sortie.append(ligne)
    membres["measurements.jsonl"] = b"\n".join(sortie) + b"\n"
    return resommer(membres)


def une_mesure_orpheline(membres: dict[str, bytes]) -> dict[str, bytes]:
    lignes = membres["measurements.jsonl"].splitlines()
    enregistrement = json.loads(lignes[0])
    enregistrement["payload"]["observation_id"] = "obs-inexistante-0000"
    lignes[0] = json.dumps(enregistrement, separators=(",", ":")).encode("utf-8")
    membres["measurements.jsonl"] = b"\n".join(lignes) + b"\n"
    manifeste = json.loads(membres["manifest.json"])
    membres["manifest.json"] = json.dumps(manifeste, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(membres)


def une_absence_inventee(membres: dict[str, bytes]) -> dict[str, bytes]:
    manifeste = json.loads(membres["manifest.json"])
    manifeste.setdefault("absences", {})["observations_sans_mesure"] = ["obs-qui-na-pas-ete-mesuree"]
    membres["manifest.json"] = json.dumps(manifeste, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(membres)


def une_garde_de_regime_retiree(membres: dict[str, bytes]) -> dict[str, bytes]:
    """L'archive reste exacte et devient trompeuse. Le verificateur le refuse."""
    manifeste = json.loads(membres["manifest.json"])
    manifeste["gardes_de_lecture"] = []
    membres["manifest.json"] = json.dumps(manifeste, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(membres)


def une_observation_effacee_partout(membres: dict[str, bytes]) -> dict[str, bytes]:
    """Le dossier entierement refabrique : coherent, et faux.

    On retire une observation ET sa mesure ET son evaluation ET sa provenance,
    on corrige chaque decompte du manifeste, on recalcule les sommes. Plus rien
    ne se contredit. C'est l'attaque que ce verificateur ne peut pas voir, et la
    raison pour laquelle l'empreinte de l'archive doit etre conservee ailleurs.
    """
    observations = [
        json.loads(l) for l in membres["observations.jsonl"].splitlines() if l.strip()
    ]
    victime = observations[-1]["payload"]["observation_id"]

    def sans_victime(membre: str) -> int:
        if membre not in membres:
            return 0
        gardees = [
            l
            for l in membres[membre].splitlines()
            if l.strip() and json.loads(l)["payload"].get("observation_id") != victime
        ]
        membres[membre] = b"\n".join(gardees) + b"\n" if gardees else b""
        return len(gardees)

    restantes = sans_victime("observations.jsonl")
    mesures = sans_victime("measurements.jsonl")
    evaluations = sans_victime("reference_evaluations.jsonl")
    provenances = sans_victime("replay_provenance.jsonl")

    # Le CSV est une vue derivee : on en retire la ligne correspondante.
    lignes_csv = membres["observations.csv"].split(b"\r\n")
    membres["observations.csv"] = b"\r\n".join(
        l for l in lignes_csv if victime.encode("utf-8") not in l
    )

    manifeste = json.loads(membres["manifest.json"])
    manifeste["decomptes"]["observations"] = restantes
    manifeste["decomptes"]["mesures"] = mesures
    manifeste["decomptes"]["evaluations"] = evaluations
    manifeste["decomptes"]["provenances_de_rejeu"] = provenances
    membres["manifest.json"] = json.dumps(manifeste, ensure_ascii=False, indent=2).encode("utf-8")
    return resommer(membres)


#: Le faux secret est ASSEMBLE a l'execution, jamais ecrit en un morceau.
#:
#: Un litteral en forme de cle dans un fichier versionne declenche les
#: detecteurs de secret (celui de GitHub, les crochets de pre-commit), et
#: obligerait a les faire taire — c'est-a-dire a desarmer exactement le controle
#: qu'on veut garder. Les fragments ci-dessous ne ressemblent a rien une fois
#: separes, et leur concatenation suffit a eprouver le verificateur.
FRAGMENTS_DU_FAUX_SECRET = ("Author", "ization: ", "Bea", "rer ", "s", "k-", "EXEMPLE-FAUX-0000")


def un_secret_injecte(membres: dict[str, bytes]) -> dict[str, bytes]:
    faux = "".join(FRAGMENTS_DU_FAUX_SECRET).encode("utf-8")
    membres["rapport.md"] = membres["rapport.md"] + b"\n\n" + faux + b"\n"
    return resommer(membres)


def une_formule_csv(membres: dict[str, bytes]) -> dict[str, bytes]:
    """Injecte en DEBUT de cellule, a une frontiere de champ.

    Injecter au milieu d'une cellule ne serait pas une formule : un tableur
    n'interprete que ce qui commence la cellule. La premiere version de ce test
    remplacait la premiere occurrence de `ok`, qui tombait dans
    `max_completion_tokens` — au milieu d'une valeur entre guillemets. Le
    verificateur avait raison de ne rien signaler.
    """
    lignes = membres["observations.csv"].split(b"\r\n")
    for index, ligne in enumerate(lignes):
        if index > 0 and ligne.strip() and b";ok;" in ligne:
            lignes[index] = ligne.replace(b";ok;", b';=cmd|"/c calc"!A1;', 1)
            break
    else:
        message = "aucune cellule `ok` entiere a alterer : le test ne prouverait rien"
        raise AssertionError(message)
    membres["observations.csv"] = b"\r\n".join(lignes)
    return resommer(membres)


def un_chemin_abusif(membres: dict[str, bytes]) -> dict[str, bytes]:
    membres["../evade.txt"] = b"ce membre sort du repertoire cible\n"
    return membres


def un_manifeste_retire(membres: dict[str, bytes]) -> dict[str, bytes]:
    del membres["manifest.json"]
    return membres


#: Les alterations qui DOIVENT etre detectees.
DETECTABLES = (
    ("un octet change dans une mesure", un_octet_change),
    ("une mesure retiree, sommes recalculees", une_mesure_retiree),
    ("un signal null declare mesure", un_signal_null_declare_mesure),
    ("une mesure rattachee a une observation inexistante", une_mesure_orpheline),
    ("une absence declaree qui n'existe pas", une_absence_inventee),
    ("la garde de regime retiree du manifeste", une_garde_de_regime_retiree),
    ("un secret injecte dans le rapport", un_secret_injecte),
    ("une formule injectee dans le CSV", une_formule_csv),
    ("un membre qui sort du repertoire cible", un_chemin_abusif),
    ("le manifeste retire", un_manifeste_retire),
)

#: Les alterations qui NE SONT PAS detectees par ce verificateur, et pourquoi.
#: Les enoncer est le propre d'un controle honnete : une limite constatee vaut
#: mieux qu'une limite supposee.
NON_DETECTABLES = (
    (
        "une observation effacee partout, decomptes et sommes refaits",
        une_observation_effacee_partout,
        "plus rien ne se contredit dans l'archive : les quatre fichiers concordent, les "
        "decomptes du manifeste sont justes, les sommes sont exactes. Aucun controle interne "
        "ne peut voir ce qui a ete retire. Seule l'empreinte de l'archive d'origine, "
        "conservee ailleurs qu'avec elle, le detecte.",
    ),
)


#: Les schemas que cette suite sait alterer.
#:
#: Elle vise les archives de CAMPAGNE. Ses dix alterations supposent un membre
#: `rapport.md`, un `observations.csv`, au moins un signal `null` et une garde
#: de regime — toutes choses qu'un artefact derive n'a pas forcement. Lancee sur
#: autre chose, elle s'interrompait en cours de route sur un `KeyError`, en
#: laissant croire a des falsifications non detectees. Un refus net vaut mieux
#: qu'un demi-resultat trompeur.
SCHEMAS_ALTERABLES = ("station.export.campagne/1", "station.export.campagne/2")


def schema_de(source: Path) -> str:
    with zipfile.ZipFile(source) as archive:
        if "manifest.json" not in archive.namelist():
            return "<sans manifeste>"
        return str(json.loads(archive.read("manifest.json")).get("schema"))


def main() -> int:
    if len(sys.argv) < 2:
        print("emploi : python tests/test_falsification.py <archive_intacte.zip> [corpus]")
        return 2
    source = Path(sys.argv[1]).resolve()

    schema = schema_de(source)
    if schema not in SCHEMAS_ALTERABLES:
        print("Cette suite ne s'applique pas a l'archive fournie.\n")
        print("  schema de l'archive : %s" % schema)
        print("  schemas alterables  : %s\n" % ", ".join(SCHEMAS_ALTERABLES))
        print(
            "Ses dix alterations supposent un membre `rapport.md`, un `observations.csv`,\n"
            "au moins un signal `null` et une garde de regime. Un artefact derive n'a pas\n"
            "forcement ces proprietes : les alterations seraient inapplicables, et un\n"
            "resultat << non detecte >> ne voudrait rien dire.\n"
        )
        print("Lancer cette suite sur l'archive de demonstration GROUNDED-S1.")
        return 2

    corpus = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    empreinte_origine = sha256(source.read_bytes())

    print("Archive de reference : %s" % source.name)
    print("empreinte            : %s\n" % empreinte_origine)

    temporaire = Path(tempfile.mkdtemp(prefix="falsification-"))
    echecs = 0
    try:
        code, _ = verifier(source, corpus)
        if code == 0:
            print("[OK       ] l'archive intacte est acceptee")
        else:
            echecs += 1
            print("[PROBLEME ] l'archive intacte est REFUSEE : rien d'autre n'a de sens")

        print("\n--- alterations qui doivent etre detectees ---")
        for nom, alteration in DETECTABLES:
            cible = temporaire / ("%s.zip" % abs(hash(nom)))
            ecrire(alteration(lire(source)), cible)
            code, sortie = verifier(cible, corpus)
            detectee = code != 0
            if detectee:
                motif = next(
                    (l.strip() for l in sortie.splitlines() if l.startswith("[FAIL")),
                    "",
                )
                print("[DETECTEE ] %-52s %s" % (nom, motif[:72]))
            else:
                echecs += 1
                print("[MANQUEE  ] %-52s le verificateur a rendu PASS" % nom)

        print("\n--- alterations NON detectees, et leur raison ---")
        for nom, alteration, raison in NON_DETECTABLES:
            cible = temporaire / ("nd-%s.zip" % abs(hash(nom)))
            ecrire(alteration(lire(source)), cible)
            code, _ = verifier(cible, corpus)
            empreinte_alteree = sha256(cible.read_bytes())
            if code == 0:
                print("[ATTENDU  ] %s" % nom)
                print("            raison : %s" % raison)
                print("            l'empreinte, elle, change : %s" % empreinte_alteree[:32])
                if empreinte_alteree == empreinte_origine:
                    echecs += 1
                    print("            [PROBLEME] l'empreinte n'a pas change")
            else:
                print("[DETECTEE ] %s (mieux qu'annonce)" % nom)

        print(
            "\nBILAN : %d/%d alterations detectees, %d limite(s) declaree(s), %d probleme(s)"
            % (len(DETECTABLES) - echecs, len(DETECTABLES), len(NON_DETECTABLES), echecs)
        )
        print(
            "\nCe que ces tests etablissent : le verificateur refuse une archive touchee.\n"
            "Ce qu'ils n'etablissent pas : qu'une archive acceptee soit authentique. "
            "Un falsificateur qui reconstruit l'archive entiere produit un dossier coherent.\n"
            "La seule defense est l'empreinte de l'archive, conservee ailleurs qu'avec elle."
        )
        return 1 if echecs else 0
    finally:
        shutil.rmtree(temporaire, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

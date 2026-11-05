# -*- coding: utf-8 -*-
"""Verificateur autonome d'un dossier de preuve NeoMundi Evidence.

Emploi :  python verify.py <archive.zip>
          python verify.py <archive.zip> --corpus <repertoire du corpus d entree>

BIBLIOTHEQUE STANDARD SEULE. Aucune dependance, aucun code NeoMundi, aucun
appel reseau, aucune ecriture. Il est fait pour etre lu de bout en bout avant
d'etre execute : c'est la condition d'une verification independante.

Chaque controle rend PASS, FAIL ou NOT TESTED. Un controle qui ne peut pas
etre fait ici rend NOT TESTED avec sa raison. Aucun echec n'est jamais
remplace par une valeur favorable.

## Ce que ce verificateur ne fait PAS, et pourquoi

Il ne recalcule PAS le chainage du registre. Le refaire ici serait une seconde
implementation des regles de chainage : deux implementations qui divergent ne
prouvent rien, et celle qui a produit l'archive serait toujours la reference.
Le chainage se verifie avec `station ledger verify`, sur le registre d'origine.

Ce qu'il verifie, en revanche, est entierement a sa portee : que les fichiers
livres sont ceux que le manifeste annonce, que les enregistrements se joignent,
que les absences declarees sont reelles, et que les empreintes que les
enregistrements portent sur leurs propres entrees se recalculent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

#: Les versions de schema d'export que ce verificateur sait lire. Une archive
#: `/1` reste lisible : ses cinq membres sont un sous-ensemble des huit.
#:
#: `neomundi.evidence.med-demo/1` est un artefact DERIVE, produit par
#: `tools/med_demo_build.py` : il porte moins de membres parce que les
#: evaluations de reference en ont ete ecartees, et son manifeste dit lui-meme
#: lesquelles et pourquoi. Les controles qui portent sur un membre absent
#: rendent NOT TESTED, comme pour toute archive incomplete.
SCHEMAS_CONNUS = (
    "station.export.campagne/1",
    "station.export.campagne/2",
    "neomundi.evidence.med-demo/1",
)

#: Les membres attendus par version de schema.
MEMBRES_PAR_SCHEMA = {
    "station.export.campagne/1": (
        "observations.csv",
        "observations.jsonl",
        "manifest.json",
        "rapport.md",
        "checksums.sha256",
    ),
    "station.export.campagne/2": (
        "observations.csv",
        "observations.jsonl",
        "measurements.jsonl",
        "reference_evaluations.jsonl",
        "replay_provenance.jsonl",
        "manifest.json",
        "rapport.md",
        "checksums.sha256",
    ),
    "neomundi.evidence.med-demo/1": (
        "observations.jsonl",
        "measurements.jsonl",
        "manifest.json",
        "report.md",
        "checksums.sha256",
    ),
}

#: Motifs qui ne doivent jamais apparaitre dans une archive remise a un tiers.
MOTIFS_INTERDITS = (
    ("cle ou jeton", ("Authorization", "Bearer ", "api_key", "api-key", "X-API-Key", "sk-")),
    ("chemin d utilisateur", ("/home/", "C:\\Users", "/Users/", "/mnt/c/Users")),
    ("chemin de serveur", ("/opt/", "/var/log/", "/etc/")),
)

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"


class Bilan:
    """Les resultats, et rien d'autre : aucun etat n'est deduit, chacun est dit."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []

    def dire(self, etat: str, controle: str, detail: str = "") -> None:
        self.lignes.append((etat, controle, detail))
        print("[%-10s] %s%s" % (etat, controle, " - " + detail if detail else ""))

    def compte(self, etat: str) -> int:
        return sum(1 for ligne in self.lignes if ligne[0] == etat)

    def code_de_sortie(self) -> int:
        return 1 if self.compte(FAIL) else 0


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def jcs(obj: object) -> bytes:
    """Forme canonique JCS pour les objets de ces archives.

    Les objets haches par la Station ne portent ici que des chaines et des
    structures : cles triees, aucun espace, UTF-8 suffisent. Un objet portant
    des flottants demanderait une implementation JCS complete, et ce
    verificateur le dirait plutot que de rendre un resultat douteux.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def lignes_jsonl(octets: bytes) -> list[dict[str, object]]:
    return [json.loads(ligne) for ligne in octets.splitlines() if ligne.strip()]


def charge(enregistrement: dict[str, object]) -> dict[str, object]:
    """Le bloc metier d'une ligne de registre."""
    valeur = enregistrement.get("payload")
    return valeur if isinstance(valeur, dict) else {}


# --------------------------------------------------------------------------
# Les controles
# --------------------------------------------------------------------------


def controle_schema(bilan: Bilan, manifeste: dict[str, object], noms: list[str]) -> str | None:
    schema = manifeste.get("schema")
    if not isinstance(schema, str) or schema not in SCHEMAS_CONNUS:
        bilan.dire(
            FAIL,
            "schema d'export reconnu",
            "schema %r inconnu de ce verificateur ; connus : %s"
            % (schema, ", ".join(SCHEMAS_CONNUS)),
        )
        return None
    attendus = MEMBRES_PAR_SCHEMA[schema]
    manquants = [m for m in attendus if m not in noms]
    surplus = [n for n in noms if n not in attendus]
    if manquants:
        bilan.dire(FAIL, "membres attendus par le schema %s" % schema, "manquants : %s" % manquants)
    else:
        detail = "membres en surplus : %s" % surplus if surplus else ""
        bilan.dire(PASS, "membres attendus par le schema %s" % schema, detail)
    return schema


def controle_checksums(bilan: Bilan, archive: zipfile.ZipFile, noms: list[str]) -> None:
    if "checksums.sha256" not in noms:
        bilan.dire(FAIL, "checksums.sha256 present", "membre absent")
        return
    lignes = archive.read("checksums.sha256").decode("utf-8").splitlines()
    declares = {}
    for ligne in lignes:
        if not ligne.strip():
            continue
        attendu, _, nom = ligne.partition("  ")
        declares[nom] = attendu
    divergents, absents = [], []
    for nom, attendu in declares.items():
        if nom not in noms:
            absents.append(nom)
        elif sha256(archive.read(nom)) != attendu:
            divergents.append(nom)
    non_couverts = [n for n in noms if n not in declares and n != "checksums.sha256"]
    if divergents or absents:
        bilan.dire(
            FAIL,
            "empreintes des %d membres declares" % len(declares),
            "divergents : %s ; annonces et absents : %s" % (divergents or "aucun", absents or "aucun"),
        )
    else:
        bilan.dire(PASS, "empreintes des %d membres declares" % len(declares))
    if non_couverts:
        bilan.dire(
            FAIL,
            "chaque membre est couvert par une empreinte",
            "hors manifeste de sommes : %s" % non_couverts,
        )
    else:
        bilan.dire(PASS, "chaque membre est couvert par une empreinte")


def controle_cardinalites(
    bilan: Bilan, archive: zipfile.ZipFile, noms: list[str], manifeste: dict[str, object]
) -> None:
    observations = lignes_jsonl(archive.read("observations.jsonl"))
    ids = {charge(e).get("observation_id") for e in observations}
    decomptes = manifeste.get("decomptes")
    decomptes = decomptes if isinstance(decomptes, dict) else {}

    if decomptes.get("observations") != len(observations):
        bilan.dire(
            FAIL,
            "le manifeste compte les observations livrees",
            "manifeste %s, lignes %d" % (decomptes.get("observations"), len(observations)),
        )
    else:
        bilan.dire(PASS, "le manifeste compte les observations livrees (%d)" % len(observations))

    for membre, cle in (
        ("measurements.jsonl", "mesures"),
        ("reference_evaluations.jsonl", "evaluations"),
        ("replay_provenance.jsonl", "provenances_de_rejeu"),
    ):
        if membre not in noms:
            bilan.dire(
                NOT_TESTED,
                "jointure de %s" % membre,
                "ce membre n est pas dans l archive. Le manifeste doit dire pourquoi.",
            )
            continue
        enregistrements = lignes_jsonl(archive.read(membre))
        if decomptes.get(cle) != len(enregistrements):
            bilan.dire(
                FAIL,
                "le manifeste compte les enregistrements de %s" % membre,
                "manifeste %s, lignes %d" % (decomptes.get(cle), len(enregistrements)),
            )
        else:
            bilan.dire(
                PASS,
                "le manifeste compte les enregistrements de %s (%d)" % (membre, len(enregistrements)),
            )
        orphelins = sorted(
            str(charge(e).get("observation_id"))
            for e in enregistrements
            if charge(e).get("observation_id") not in ids
        )
        if orphelins:
            bilan.dire(
                FAIL,
                "aucun orphelin dans %s" % membre,
                "%d sans observation livree : %s" % (len(orphelins), orphelins[:3]),
            )
        else:
            bilan.dire(PASS, "aucun orphelin dans %s" % membre)


def controle_absences(
    bilan: Bilan, archive: zipfile.ZipFile, noms: list[str], manifeste: dict[str, object]
) -> None:
    """Les absences que le manifeste declare sont-elles reellement absentes ?

    C'est le controle qui separe un dossier honnete d'un dossier plausible : une
    absence annoncee doit se constater sur les fichiers livres, et une absence
    non annoncee doit ne pas exister.
    """
    absences = manifeste.get("absences")
    if not isinstance(absences, dict):
        bilan.dire(
            NOT_TESTED,
            "les absences declarees sont reelles",
            "le manifeste ne declare aucune rubrique d absences",
        )
        return
    observations = {
        charge(e).get("observation_id") for e in lignes_jsonl(archive.read("observations.jsonl"))
    }
    ecarts = []
    for membre, cle in (
        ("measurements.jsonl", "observations_sans_mesure"),
        ("reference_evaluations.jsonl", "observations_sans_evaluation"),
    ):
        if membre not in noms:
            continue
        couverts = {
            charge(e).get("observation_id") for e in lignes_jsonl(archive.read(membre))
        }
        constate = sorted(str(o) for o in observations - couverts)
        declare = sorted(str(o) for o in absences.get(cle, []))
        if constate != declare:
            ecarts.append("%s : declare %s, constate %s" % (cle, declare[:3], constate[:3]))
    if ecarts:
        bilan.dire(FAIL, "les absences declarees sont reelles", " ; ".join(ecarts))
    else:
        bilan.dire(PASS, "les absences declarees sont reelles")


def controle_nulls(bilan: Bilan, archive: zipfile.ZipFile, noms: list[str]) -> None:
    """Aucun signal `null` du registre n'est devenu un zero quelque part."""
    if "measurements.jsonl" not in noms:
        bilan.dire(
            NOT_TESTED, "aucun signal null rendu comme zero", "aucun membre de mesures dans cette archive"
        )
        return
    mesures = lignes_jsonl(archive.read("measurements.jsonl"))
    nuls = values = 0
    incoherences = []
    for enregistrement in mesures:
        payload = charge(enregistrement)
        signaux = payload.get("signals")
        signaux = signaux if isinstance(signaux, dict) else {}
        mesures_declarees = payload.get("measured_signals")
        mesures_declarees = mesures_declarees if isinstance(mesures_declarees, list) else []
        for nom, valeur in signaux.items():
            if valeur is None:
                nuls += 1
                # Un signal null declare mesure serait la contradiction que le
                # dossier doit refuser de livrer en silence.
                if nom in mesures_declarees:
                    incoherences.append(
                        "%s : signal %s null mais declare mesure"
                        % (payload.get("measurement_id"), nom)
                    )
            else:
                values += 1
    if incoherences:
        bilan.dire(
            FAIL,
            "aucun signal null declare mesure (%d null, %d values)" % (nuls, values),
            " ; ".join(incoherences[:3]),
        )
    else:
        bilan.dire(
            PASS, "aucun signal null declare mesure (%d null, %d values)" % (nuls, values)
        )


def controle_regime(bilan: Bilan, archive: zipfile.ZipFile, manifeste: dict[str, object]) -> None:
    """Un regime hors ligne porte-t-il sa garde de lecture ?"""
    regimes = manifeste.get("regimes_d_execution")
    if not isinstance(regimes, list):
        bilan.dire(
            NOT_TESTED,
            "un regime hors ligne porte sa garde",
            "le manifeste ne declare aucun regime d execution",
        )
        return
    hors_ligne = [r for r in regimes if r != "live"]
    gardes = manifeste.get("gardes_de_lecture")
    gardes = gardes if isinstance(gardes, list) else []
    rapport = archive.read("rapport.md").decode("utf-8")
    if hors_ligne and not gardes:
        bilan.dire(
            FAIL,
            "un regime hors ligne porte sa garde",
            "regimes %s sans aucune garde de lecture" % hors_ligne,
        )
        return
    if hors_ligne and "Regime d'execution" not in rapport.replace("é", "e"):
        bilan.dire(
            FAIL,
            "un regime hors ligne porte sa garde",
            "le rapport ne porte aucune section de regime",
        )
        return
    detail = "regimes : %s" % (", ".join(regimes) or "aucun")
    bilan.dire(PASS, "un regime hors ligne porte sa garde", detail)


def controle_confidentialite(bilan: Bilan, archive: zipfile.ZipFile, noms: list[str]) -> None:
    trouves = []
    for nom in noms:
        texte = archive.read(nom).decode("utf-8", "replace")
        for etiquette, motifs in MOTIFS_INTERDITS:
            for motif in motifs:
                if motif in texte:
                    trouves.append("%s : %s (%s)" % (nom, etiquette, motif))
    if trouves:
        bilan.dire(FAIL, "aucun secret ni chemin de machine dans l archive", " ; ".join(trouves[:4]))
    else:
        bilan.dire(PASS, "aucun secret ni chemin de machine dans l archive")


def controle_csv(bilan: Bilan, archive: zipfile.ZipFile, noms: list[str]) -> None:
    """Les cellules a risque de formule sont-elles neutralisees ?

    Le membre peut etre absent : une archive derivee n'en porte pas forcement,
    et une archive abimee non plus. Lire sans garde ferait PLANTER le
    verificateur au lieu de rendre un resultat — et un verificateur qui plante
    ne rend ni PASS, ni FAIL, ni NOT TESTED.
    """
    if "observations.csv" not in noms:
        bilan.dire(
            NOT_TESTED,
            "aucune cellule CSV interpretable comme formule",
            "aucun membre CSV dans cette archive",
        )
        return
    texte = archive.read("observations.csv").decode("utf-8-sig")
    suspectes = []
    for numero, ligne in enumerate(texte.splitlines()):
        for cellule in ligne.split(";"):
            nu = cellule.strip('"')
            if nu[:1] in ("=", "+", "@") or nu[:1] == "\t":
                suspectes.append("ligne %d : %r" % (numero + 1, nu[:24]))
    if suspectes:
        bilan.dire(
            FAIL,
            "aucune cellule CSV interpretable comme formule",
            " ; ".join(suspectes[:3]),
        )
    else:
        bilan.dire(PASS, "aucune cellule CSV interpretable comme formule")


def controle_entrees(
    bilan: Bilan, archive: zipfile.ZipFile, noms: list[str], corpus: Path | None
) -> None:
    """Les empreintes que les provenances portent sur leurs entrees se recalculent-elles ?"""
    if "replay_provenance.jsonl" not in noms:
        bilan.dire(
            NOT_TESTED,
            "empreintes des entrees rejouees",
            "aucun enregistrement de provenance : corpus de regime live, ou membre absent",
        )
        return
    provenances = [charge(e) for e in lignes_jsonl(archive.read("replay_provenance.jsonl"))]
    if not provenances:
        bilan.dire(
            NOT_TESTED, "empreintes des entrees rejouees", "aucun enregistrement de provenance"
        )
        return
    if corpus is None:
        bilan.dire(
            NOT_TESTED,
            "empreintes des entrees rejouees (%d a verifier)" % len(provenances),
            "le corpus d entree n est pas dans l archive. Le fournir avec --corpus "
            "<repertoire> pour que ce controle soit fait.",
        )
        return
    bons = divergents = absents = 0
    for p in provenances:
        chemin = corpus / str(p.get("recording_path"))
        if not chemin.is_file():
            absents += 1
        elif sha256_fichier(chemin) == p.get("recording_sha256"):
            bons += 1
        else:
            divergents += 1
    if divergents or absents:
        bilan.dire(
            FAIL,
            "empreintes des entrees rejouees (%d conformes)" % bons,
            "divergents %d, absents %d" % (divergents, absents),
        )
    else:
        bilan.dire(PASS, "empreintes des entrees rejouees (%d/%d conformes)" % (bons, bons))

    manifeste_corpus = corpus / "manifest.json"
    if not manifeste_corpus.is_file():
        bilan.dire(
            NOT_TESTED, "bundle_sha256 re-derive", "le corpus fourni n a pas de manifest.json"
        )
        return
    m = json.loads(manifeste_corpus.read_text(encoding="utf-8"))
    entrees = m.get("entries", [])
    recs = sorted(
        (
            {
                "path": "responses/" + e["recording"],
                "sha256": sha256_fichier(corpus / "responses" / e["recording"]),
            }
            for e in entrees
        ),
        key=lambda r: r["path"],
    )
    recalcule = hashlib.sha256(
        jcs(
            {
                "bundle_id": m.get("bundle_id"),
                "regime": m.get("regime"),
                "origin": m.get("origin"),
                "recordings": recs,
            }
        )
    ).hexdigest()
    attestes = {str(p.get("bundle_sha256")) for p in provenances}
    if recalcule in attestes:
        bilan.dire(PASS, "bundle_sha256 re-derive depuis les entrees", recalcule[:32] + "...")
    else:
        bilan.dire(
            FAIL,
            "bundle_sha256 re-derive depuis les entrees",
            "recalcule %s ; atteste %s" % (recalcule[:16], ", ".join(a[:16] for a in sorted(attestes))),
        )


def controle_chaine(bilan: Bilan, manifeste: dict[str, object]) -> None:
    """Le chainage reste hors de portee, mais on rapporte ce que l'archive declare.

    Deux formes de declaration existent : `registre` (un seul registre, archive
    de campagne) et `registres` (plusieurs, artefact derive). Ne lire que la
    premiere ferait dire « inconnue » a une archive qui declare pourtant ses
    empreintes de tete — un verificateur ne doit pas rapporter une absence qui
    n'existe pas.
    """
    un = manifeste.get("registre")
    plusieurs = manifeste.get("registres")
    if isinstance(un, dict):
        declares = [un]
    elif isinstance(plusieurs, list):
        declares = [r for r in plusieurs if isinstance(r, dict)]
    else:
        declares = []

    if not declares:
        bilan.dire(
            NOT_TESTED,
            "chainage JCS du registre d origine",
            "hors de portee, et l archive ne declare aucune empreinte de tete a confronter.",
        )
        return
    tetes = ", ".join(str(r.get("empreinte_de_tete"))[:16] + "..." for r in declares)
    verifiees = {r.get("chaine_verifiee", r.get("chaine_verifiee_par_cet_outil")) for r in declares}
    bilan.dire(
        NOT_TESTED,
        "chainage JCS de %d registre(s) d origine" % len(declares),
        "hors de portee : le recalculer ici serait une seconde implementation du "
        "registre. L archive declare %s et les empreintes de tete %s. A confronter avec : "
        "station ledger verify --path <registre>" % (sorted(map(str, verifiees)), tetes),
    )


def controle_origine(bilan: Bilan) -> None:
    bilan.dire(
        NOT_TESTED,
        "origine et horodatage de l archive",
        "hors de portee de toute verification locale : aucune signature tierce, aucun "
        "ancrage exterieur. `recorded_at` est declare par l appelant.",
    )


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Verifie un dossier de preuve NeoMundi Evidence, sans aucune dependance."
    )
    analyseur.add_argument("archive", type=Path, help="l archive ZIP a verifier")
    analyseur.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="repertoire du corpus d entree, pour verifier les empreintes des entrees rejouees",
    )
    arguments = analyseur.parse_args()

    bilan = Bilan()
    if not arguments.archive.is_file():
        bilan.dire(FAIL, "archive lisible", "%s introuvable" % arguments.archive)
        return bilan.code_de_sortie()

    print("Dossier de preuve : %s" % arguments.archive)
    print("empreinte de l archive : %s\n" % sha256_fichier(arguments.archive))

    try:
        archive = zipfile.ZipFile(arguments.archive)
    except zipfile.BadZipFile as erreur:
        bilan.dire(FAIL, "archive lisible", str(erreur))
        return bilan.code_de_sortie()

    with archive:
        abusifs = [
            n for n in archive.namelist() if n.startswith("/") or ".." in Path(n).parts
        ]
        if abusifs:
            bilan.dire(
                FAIL,
                "aucun membre ne sort du repertoire cible",
                "chemins abusifs : %s" % abusifs[:3],
            )
            return bilan.code_de_sortie()
        bilan.dire(PASS, "aucun membre ne sort du repertoire cible")

        if archive.testzip() is not None:
            bilan.dire(FAIL, "integrite interne du ZIP", "un membre est corrompu")
            return bilan.code_de_sortie()
        bilan.dire(PASS, "integrite interne du ZIP")

        noms = archive.namelist()
        if "manifest.json" not in noms:
            bilan.dire(FAIL, "manifest.json present", "sans manifeste, rien n est verifiable")
            return bilan.code_de_sortie()
        manifeste = json.loads(archive.read("manifest.json"))

        if controle_schema(bilan, manifeste, noms) is None:
            return bilan.code_de_sortie()
        controle_checksums(bilan, archive, noms)
        controle_cardinalites(bilan, archive, noms, manifeste)
        controle_absences(bilan, archive, noms, manifeste)
        controle_nulls(bilan, archive, noms)
        controle_regime(bilan, archive, manifeste)
        controle_csv(bilan, archive, noms)
        controle_confidentialite(bilan, archive, noms)
        controle_entrees(bilan, archive, noms, arguments.corpus)
        controle_chaine(bilan, manifeste)
        controle_origine(bilan)

    print(
        "\nBILAN : %d PASS, %d FAIL, %d NOT TESTED"
        % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED))
    )
    if bilan.compte(FAIL):
        print("Ce dossier ne doit pas etre presente comme verifie.")
    return bilan.code_de_sortie()


if __name__ == "__main__":
    sys.exit(main())

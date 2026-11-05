# -*- coding: utf-8 -*-
"""Lie une observation NeoMundi a des artefacts externes, et verifie la liaison.

    python bind.py build  --archive A.zip --observation obs-... \\
                          --artifact response=chemin/vers/reponse.json \\
                          --out manifeste.json
    python bind.py verify manifeste.json [--root REPERTOIRE] [--archive A.zip] [--json]

CE QUE CET OUTIL ETABLIT, ET CE QU IL N ETABLIT PAS
---------------------------------------------------

Une observation declare des empreintes d objets qui ne sont PAS dans
l archive : `response_sha256`, `prompt_sha256`, `request_sha256`. Ces
empreintes sont portees par un enregistrement chaine, donc deplacer l une
d elles apres coup casse la chaine.

Lier, ici, c est produire un fichier dont les octets se hachent sur l une de
ces empreintes. Cela etablit **que ce fichier est bien celui auquel
l enregistrement se refere**. Cela n etablit PAS que l execution a eu lieu,
ni quand, ni chez qui.

Un manifeste est un ensemble de REVENDICATIONS. Le niveau de garantie
reellement atteint est DERIVE par le verificateur a partir de ce qu il
recalcule -- jamais lu dans le manifeste. Un manifeste qui se revendique
mieux qu il ne l est est refuse, et c est le controle le plus important de
cet outil.

Quatre niveaux, dans cet ordre :

    declared                      ecrit dans le document, rien de recalcule
    reference_verifiable          l artefact est la, et ses octets se hachent
                                  sur une empreinte que l enregistrement declare
    cryptographically_attested    une signature d une cle identifiee verifie
                                  -- AUCUNE implementation ici, donc jamais
                                  derivable aujourd hui
    not_demonstrable              hors de portee de tout controle local

Bibliotheque standard seule. Aucun reseau. Aucune ecriture hors du `--out`
demande.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

SCHEMA = "neomundi.evidence.manifest/1"

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"

DECLARE, REFERENCE, ATTESTE, INDEMONTRABLE = (
    "declared",
    "reference_verifiable",
    "cryptographically_attested",
    "not_demonstrable",
)

# L ordre est celui de la force croissante. `not_demonstrable` est hors
# echelle : il dit qu aucun niveau ne sera jamais atteint pour cet objet.
FORCE = {DECLARE: 1, REFERENCE: 2, ATTESTE: 3}

# Le role d un artefact, et l empreinte que l enregistrement declare pour lui.
ANCRAGE_PAR_ROLE = {
    "response": "response_sha256",
    "prompt": "prompt_sha256",
    "request": "request_sha256",
    "config_snapshot": "config_snapshot_sha256",
    "recording": "recording_sha256",
    "bundle": "bundle_sha256",
    "other": None,
}

# Les empreintes qu un enregistrement d observation declare, et ou les lire.
DIGESTS_OBSERVATION = ("response_sha256", "prompt_sha256", "request_sha256")
DIGESTS_INTEGRITE = ("config_snapshot_sha256",)
DIGESTS_PROVENANCE = ("recording_sha256", "bundle_sha256")

# Plafond de taille d un artefact, en octets. Un verificateur ne doit pas
# hacher aveuglement ce qu on lui presente : un fichier enorme transforme une
# verification en attente indefinie. Au-dela, l artefact est NOT TESTED, pas
# FAIL : sa taille n est pas une faute, c est un refus de le lire ici.
PLAFOND_ARTEFACT = 64 * 1024 * 1024

LIMITES = [
    "Une correspondance d empreinte etablit qu un fichier est celui auquel "
    "l enregistrement se refere. Elle n etablit pas que l execution a eu lieu.",
    "Aucune signature n est verifiee : ce depot n en implemente aucune.",
    "`created_at` et `declared_origin` sont declares par l auteur du manifeste "
    "et ne sont contredits par rien.",
    "Un faussaire qui reconstruit a la fois l archive et les artefacts produit "
    "un ensemble coherent. Seule une empreinte conservee ailleurs le detecte.",
]


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------


class Illisible(Exception):
    """Une entree n a pas la forme attendue. Rendue en FAIL, jamais en trace."""


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def objet_json(octets: bytes, quoi: str) -> dict:
    try:
        valeur = json.loads(octets)
    except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
        raise Illisible("%s n est pas du JSON lisible : %s" % (quoi, erreur)) from erreur
    if not isinstance(valeur, dict):
        raise Illisible(
            "%s devrait etre un objet JSON ; recu %s" % (quoi, type(valeur).__name__)
        )
    return valeur


def lignes_jsonl(octets: bytes, quoi: str) -> list[dict]:
    sortie = []
    for numero, ligne in enumerate(octets.splitlines(), start=1):
        if not ligne.strip():
            continue
        try:
            valeur = json.loads(ligne)
        except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
            raise Illisible("%s, ligne %d : JSON illisible (%s)" % (quoi, numero, erreur)) from erreur
        if not isinstance(valeur, dict):
            raise Illisible(
                "%s, ligne %d : attendu un objet, recu %s" % (quoi, numero, type(valeur).__name__)
            )
        sortie.append(valeur)
    return sortie


def est_sha256(valeur: object) -> bool:
    return (
        isinstance(valeur, str)
        and len(valeur) == 64
        and all(c in "0123456789abcdef" for c in valeur)
    )


def chemin_sur(racine: Path, relatif: str) -> Path:
    """Resout un chemin d artefact en refusant toute sortie de la racine.

    Trois refus distincts, parce qu ils ont trois causes distinctes : un
    chemin absolu, une traversee, et un lien symbolique qui pointe dehors.
    `resolve()` suit les liens, donc la comparaison finale les attrape tous
    -- y compris un lien plante au milieu du chemin.
    """
    if not relatif or relatif.startswith(("/", "\\")) or ":" in relatif[:3]:
        raise Illisible("chemin absolu refuse : %r" % relatif)
    if ".." in Path(relatif).parts:
        raise Illisible("traversee de repertoire refusee : %r" % relatif)
    cible = (racine / relatif).resolve()
    racine_resolue = racine.resolve()
    if racine_resolue != cible and racine_resolue not in cible.parents:
        raise Illisible(
            "le chemin sort du repertoire racine : %r resout hors de %s" % (relatif, racine_resolue)
        )
    return cible


# --------------------------------------------------------------------------
# Lecture d une archive Evidence
# --------------------------------------------------------------------------


def charge(enregistrement: dict) -> dict:
    valeur = enregistrement.get("payload")
    return valeur if isinstance(valeur, dict) else {}


def integrite(enregistrement: dict) -> dict:
    valeur = enregistrement.get("integrity")
    return valeur if isinstance(valeur, dict) else {}


def lire_sujet(archive_chemin: Path, observation_id: str) -> tuple[dict, dict]:
    """Rend (sujet, empreintes_declarees) pour une observation d une archive.

    Les empreintes sont lues la ou l archive les porte : trois dans le
    `payload` de l observation, une dans son bloc `integrity`, et deux dans
    l enregistrement de provenance quand il existe.
    """
    try:
        archive = zipfile.ZipFile(archive_chemin)
    except (zipfile.BadZipFile, OSError) as erreur:
        raise Illisible("archive illisible : %s" % erreur) from erreur

    with archive:
        noms = archive.namelist()
        if "observations.jsonl" not in noms:
            raise Illisible("l archive n a pas de membre observations.jsonl")
        observations = lignes_jsonl(archive.read("observations.jsonl"), "observations.jsonl")
        trouvees = [e for e in observations if charge(e).get("observation_id") == observation_id]
        if not trouvees:
            raise Illisible(
                "aucune observation %r dans l archive (%d observations presentes)"
                % (observation_id, len(observations))
            )
        if len(trouvees) > 1:
            raise Illisible(
                "%d observations portent l identifiant %r : l archive est ambigue"
                % (len(trouvees), observation_id)
            )
        enregistrement = trouvees[0]
        p, i = charge(enregistrement), integrite(enregistrement)

        empreintes = {}
        for cle in DIGESTS_OBSERVATION:
            if est_sha256(p.get(cle)):
                empreintes[cle] = p[cle]
        for cle in DIGESTS_INTEGRITE:
            if est_sha256(i.get(cle)):
                empreintes[cle] = i[cle]

        if "replay_provenance.jsonl" in noms:
            provenances = lignes_jsonl(
                archive.read("replay_provenance.jsonl"), "replay_provenance.jsonl"
            )
            for e in provenances:
                q = charge(e)
                if q.get("observation_id") != observation_id:
                    continue
                for cle in DIGESTS_PROVENANCE:
                    if est_sha256(q.get(cle)):
                        empreintes[cle] = q[cle]

        mesure_version = None
        if "measurements.jsonl" in noms:
            for e in lignes_jsonl(archive.read("measurements.jsonl"), "measurements.jsonl"):
                q = charge(e)
                if q.get("observation_id") == observation_id:
                    mesure_version = q.get("measurement_version")
                    break

        sujet = {"observation_id": observation_id}
        for depuis, vers in (
            ("record_sha256", "record_sha256"),
            ("prev_record_sha256", "prev_record_sha256"),
            ("code_commit", "code_commit"),
            ("comparability_key", "comparability_key"),
        ):
            if isinstance(i.get(depuis), str):
                sujet[vers] = i[depuis]
        if isinstance(mesure_version, str):
            sujet["measurement_version"] = mesure_version
        sujet["source_archive"] = {
            "name": archive_chemin.name,
            "sha256": sha256_fichier(archive_chemin),
        }
        return sujet, empreintes


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def construire(arguments: argparse.Namespace) -> int:
    sujet, empreintes = lire_sujet(arguments.archive, arguments.observation)

    artefacts = []
    for index, brut in enumerate(arguments.artifact or [], start=1):
        role, _, relatif = brut.partition("=")
        if not relatif:
            raise Illisible("artefact mal forme : %r ; attendu role=chemin" % brut)
        if role not in ANCRAGE_PAR_ROLE:
            raise Illisible(
                "role %r inconnu ; connus : %s" % (role, ", ".join(sorted(ANCRAGE_PAR_ROLE)))
            )
        chemin = Path(relatif)
        if not chemin.is_file():
            raise Illisible("artefact introuvable : %s" % chemin)

        ancrage = ANCRAGE_PAR_ROLE[role]
        empreinte = sha256_fichier(chemin)
        # La revendication est DERIVEE ici aussi : `build` ne revendique
        # jamais mieux que ce qu il vient de constater. Un manifeste ecrit a
        # la main peut mentir, et c est au verificateur de le dire.
        if ancrage and empreintes.get(ancrage) == empreinte:
            revendique = REFERENCE
        else:
            revendique = DECLARE
        artefacts.append(
            {
                "artifact_id": "art-%02d" % index,
                "role": role,
                "path": chemin.name if arguments.basenames else relatif.replace("\\", "/"),
                "size_bytes": chemin.stat().st_size,
                "sha256": empreinte,
                "binds_to": ancrage,
                "claimed_assurance": revendique,
            }
        )

    manifeste = {
        "schema": SCHEMA,
        "created_at": arguments.created_at,
        "subject": sujet,
        "declared_digests": dict(sorted(empreintes.items())),
        "artifacts": artefacts,
        "signatures": [],
        "statements": list(arguments.statement or []),
        "limits": LIMITES,
    }

    sortie = json.dumps(manifeste, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if arguments.out:
        # LF explicite : un manifeste de liaison peut etre atteste a son
        # tour, et son empreinte ne doit pas dependre du systeme.
        arguments.out.write_bytes(sortie.encode("utf-8"))
        print("manifeste ecrit : %s" % arguments.out)
        print("empreinte        : %s" % sha256(sortie.encode("utf-8")))
    else:
        sys.stdout.write(sortie)

    print()
    print("%d artefact(s), %d empreinte(s) declaree(s) par l enregistrement."
          % (len(artefacts), len(empreintes)))
    lies = sum(1 for a in artefacts if a["claimed_assurance"] == REFERENCE)
    print("%d artefact(s) se hachent sur une empreinte de l enregistrement." % lies)
    if lies != len(artefacts):
        print("Les autres restent au niveau `declared` : aucun ancrage ne les tient.")
    print()
    print("Rappel : une correspondance d empreinte dit que le fichier est celui")
    print("auquel l enregistrement se refere. Elle ne dit pas que l execution a")
    print("eu lieu. Verifier avec : python bind.py verify <manifeste>")
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------


class Bilan:
    """Les lignes de controle, et rien d autre. PASS, FAIL et NOT TESTED
    restent distincts : aucun n absorbe les autres."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []
        #: Index des lignes dont le NOT TESTED est CONTINGENT -- celles qui
        #: deviendraient PASS si l appelant fournissait ce qui manque. On
        #: retient l index et non l intitule : plusieurs intitules sont
        #: construits, donc un ensemble de noms serait fragile.
        self.requis: list[int] = []

    def dire(self, etat: str, intitule: str, detail: str = "",
             requis: bool = False) -> None:
        """Inscrit une ligne. `requis` ne change NI l etat NI l affichage.

        Il ne sert qu au code de sortie en mode strict.
        """
        if requis:
            self.requis.append(len(self.lignes))
        self.lignes.append((etat, intitule, detail))
        print("[%-10s] %s%s" % (etat, intitule, " - " + detail if detail else ""))

    def requises_non_demontrees(self) -> list[str]:
        """Les garanties requises qui ne sont pas `PASS`."""
        return [self.lignes[i][1] for i in self.requis if self.lignes[i][0] != PASS]

    def compte(self, etat: str) -> int:
        return sum(1 for l in self.lignes if l[0] == etat)

    def code_de_sortie(self, strict: bool = False) -> int:
        """0 sain, 1 au moins un FAIL, 2 garantie requise non demontree.

        Un `FAIL` l emporte : c est l enonce le plus fort, et un
        consommateur qui ne distingue pas les codes non nuls n est pas
        induit en erreur pour autant.
        """
        if self.compte(FAIL):
            return 1
        if strict and self.requises_non_demontrees():
            return 2
        return 0


def controle_forme(bilan: Bilan, manifeste: dict) -> bool:
    """La forme du manifeste, avant tout calcul.

    Sans ce controle, un champ absent ou d un mauvais type ferait echouer un
    controle ulterieur par accident -- et le lecteur du rapport croirait a un
    defaut de la preuve plutot qu a un defaut du document.
    """
    if manifeste.get("schema") != SCHEMA:
        bilan.dire(
            FAIL,
            "schema de manifeste reconnu",
            "schema %r inconnu ; attendu %r" % (manifeste.get("schema"), SCHEMA),
        )
        return False

    problemes = []
    for cle, type_attendu in (
        ("created_at", str),
        ("subject", dict),
        ("declared_digests", dict),
        ("artifacts", list),
    ):
        valeur = manifeste.get(cle)
        if valeur is None:
            problemes.append("%s absent" % cle)
        elif not isinstance(valeur, type_attendu):
            problemes.append("%s : attendu %s, recu %s" % (cle, type_attendu.__name__, type(valeur).__name__))
    for cle, type_attendu in (("signatures", list), ("statements", list), ("limits", list)):
        if cle in manifeste and not isinstance(manifeste[cle], type_attendu):
            problemes.append("%s : attendu %s" % (cle, type_attendu.__name__))

    sujet = manifeste.get("subject")
    if isinstance(sujet, dict) and not isinstance(sujet.get("observation_id"), str):
        problemes.append("subject.observation_id absent ou non textuel")

    empreintes = manifeste.get("declared_digests")
    if isinstance(empreintes, dict):
        for cle, valeur in empreintes.items():
            if not est_sha256(valeur):
                problemes.append("declared_digests.%s n est pas un SHA-256" % cle)

    artefacts = manifeste.get("artifacts")
    if isinstance(artefacts, list):
        vus = set()
        for index, a in enumerate(artefacts):
            if not isinstance(a, dict):
                problemes.append("artifacts[%d] n est pas un objet" % index)
                continue
            for cle in ("artifact_id", "role", "path", "sha256", "claimed_assurance"):
                if not isinstance(a.get(cle), str):
                    problemes.append("artifacts[%d].%s absent ou non textuel" % (index, cle))
            if not est_sha256(a.get("sha256")):
                problemes.append("artifacts[%d].sha256 n est pas un SHA-256" % index)
            if a.get("claimed_assurance") not in (DECLARE, REFERENCE, ATTESTE, INDEMONTRABLE):
                problemes.append(
                    "artifacts[%d].claimed_assurance %r hors de l echelle"
                    % (index, a.get("claimed_assurance"))
                )
            if a.get("role") not in ANCRAGE_PAR_ROLE:
                problemes.append("artifacts[%d].role %r inconnu" % (index, a.get("role")))
            if "binds_to" not in a:
                problemes.append("artifacts[%d].binds_to absent" % index)
            identifiant = a.get("artifact_id")
            if identifiant in vus:
                problemes.append("artifact_id %r en double" % identifiant)
            vus.add(identifiant)

    if problemes:
        bilan.dire(FAIL, "forme du manifeste", "; ".join(problemes[:6]))
        return False
    bilan.dire(PASS, "forme du manifeste", "%d artefact(s)" % len(manifeste["artifacts"]))
    return True


def controle_sujet(bilan: Bilan, manifeste: dict, archive: Path | None) -> None:
    """Le manifeste parle-t-il de l observation qu il dit, dans l archive qu il dit ?"""
    sujet = manifeste["subject"]
    identifiant = sujet["observation_id"]
    source = sujet.get("source_archive")

    if archive is None:
        bilan.dire(
            NOT_TESTED,
            "le sujet existe dans son archive",
            "archive non fournie. La fournir avec --archive <fichier> pour que "
            "les empreintes declarees soient confrontees a l enregistrement.",
            requis=True,
        )
        return

    empreinte_archive = sha256_fichier(archive)
    if isinstance(source, dict) and est_sha256(source.get("sha256")):
        if source["sha256"] != empreinte_archive:
            bilan.dire(
                FAIL,
                "l archive fournie est celle du manifeste",
                "le manifeste nomme %s ; l archive fournie se hache sur %s"
                % (source["sha256"][:16] + "...", empreinte_archive[:16] + "..."),
            )
            return
        bilan.dire(PASS, "l archive fournie est celle du manifeste")
    else:
        bilan.dire(
            NOT_TESTED,
            "l archive fournie est celle du manifeste",
            "le manifeste ne porte pas d empreinte d archive",
        )

    sujet_reel, empreintes_reelles = lire_sujet(archive, identifiant)
    bilan.dire(PASS, "le sujet existe dans son archive", "observation %s" % identifiant[:20] + "...")

    ecarts = []
    for cle in ("record_sha256", "prev_record_sha256", "code_commit", "comparability_key",
                "measurement_version"):
        if cle in sujet and sujet[cle] != sujet_reel.get(cle):
            ecarts.append("%s : manifeste %r, archive %r" % (cle, sujet[cle], sujet_reel.get(cle)))
    if ecarts:
        bilan.dire(FAIL, "le sujet concorde avec l enregistrement", "; ".join(ecarts[:3]))
    else:
        bilan.dire(PASS, "le sujet concorde avec l enregistrement")

    # Les empreintes declarees sont-elles bien celles de l enregistrement ?
    # C est ici qu un manifeste qui a REECRIT une empreinte pour la faire
    # correspondre a son artefact se fait prendre.
    declarees = manifeste["declared_digests"]
    faux = [
        "%s : manifeste %s..., enregistrement %s"
        % (cle, valeur[:12], (empreintes_reelles.get(cle) or "absente")[:12] + "...")
        for cle, valeur in sorted(declarees.items())
        if empreintes_reelles.get(cle) != valeur
    ]
    if faux:
        bilan.dire(
            FAIL,
            "les empreintes declarees sont celles de l enregistrement",
            "; ".join(faux[:3]),
        )
    else:
        bilan.dire(
            PASS,
            "les empreintes declarees sont celles de l enregistrement",
            "%d empreinte(s)" % len(declarees),
        )

    manquantes = sorted(set(empreintes_reelles) - set(declarees))
    if manquantes:
        bilan.dire(
            NOT_TESTED,
            "empreintes de l enregistrement non reprises au manifeste",
            "%s : rien n est offert pour elles" % ", ".join(manquantes),
        )


def controle_artefacts(
    bilan: Bilan, manifeste: dict, racine: Path, plafond: int = PLAFOND_ARTEFACT
) -> list[dict]:
    """Chaque artefact : present, de la bonne taille, et ancre ou non.

    Rend la liste des verdicts par artefact, avec le niveau DERIVE -- jamais
    celui revendique.
    """
    declarees = manifeste["declared_digests"]
    verdicts = []

    for a in manifeste["artifacts"]:
        identifiant, role, relatif = a["artifact_id"], a["role"], a["path"]
        revendique, ancrage = a["claimed_assurance"], a.get("binds_to")
        intitule = "artefact %s (%s)" % (identifiant, role)

        verdict = {
            "artifact_id": identifiant,
            "role": role,
            "path": relatif,
            "claimed_assurance": revendique,
            "derived_assurance": DECLARE,
            "binds_to": ancrage,
            # Un artefact non fourni n a pas pu etre eprouve. Ce n est pas la
            # meme chose qu un artefact qui contredit sa revendication, et les
            # deux ne doivent pas rendre le meme etat.
            "verifiable_here": True,
            "problems": [],
        }

        try:
            chemin = chemin_sur(racine, relatif)
        except Illisible as erreur:
            bilan.dire(FAIL, intitule, str(erreur))
            verdict["problems"].append(str(erreur))
            verdicts.append(verdict)
            continue

        if not chemin.is_file():
            # Absent n est pas faux : le manifeste reste exploitable, mais
            # aucun niveau au-dessus de `declared` ne peut etre derive.
            bilan.dire(
                NOT_TESTED,
                intitule,
                "fichier absent sous la racine : %s. Sa revendication `%s` n a pas "
                "pu etre eprouvee ; elle n est pas contredite pour autant."
                % (relatif, revendique),
                requis=True,
            )
            verdict["verifiable_here"] = False
            verdict["problems"].append("fichier absent sous la racine")
            verdicts.append(verdict)
            continue

        taille = chemin.stat().st_size
        if taille > plafond:
            bilan.dire(
                NOT_TESTED,
                intitule,
                "%d octets, au-dela du plafond de %d. Non lu : relever le "
                "plafond avec --max-artifact-bytes pour l eprouver."
                % (taille, plafond),
                requis=True,
            )
            verdict["verifiable_here"] = False
            verdict["observed_size_bytes"] = taille
            verdict["problems"].append("artefact au-dela du plafond de lecture")
            verdicts.append(verdict)
            continue

        empreinte = sha256_fichier(chemin)
        verdict["observed_sha256"] = empreinte
        verdict["observed_size_bytes"] = taille

        if empreinte != a["sha256"]:
            bilan.dire(
                FAIL,
                intitule,
                "le manifeste annonce %s..., le fichier se hache sur %s..."
                % (a["sha256"][:16], empreinte[:16]),
            )
            verdict["problems"].append("empreinte du manifeste non conforme au fichier")
            verdicts.append(verdict)
            continue

        if isinstance(a.get("size_bytes"), int) and a["size_bytes"] != taille:
            # Une taille fausse avec une empreinte juste est impossible ;
            # c est donc un defaut du manifeste, pas de l artefact.
            bilan.dire(
                FAIL,
                intitule + ", taille",
                "annoncee %d octets, observee %d" % (a["size_bytes"], taille),
            )
            verdict["problems"].append("taille annoncee fausse")

        if ancrage is None:
            bilan.dire(
                PASS,
                intitule,
                "present et conforme au manifeste, mais SANS ancrage dans "
                "l enregistrement. Niveau derive : %s." % DECLARE,
            )
            verdicts.append(verdict)
            continue

        attendue = declarees.get(ancrage)
        if attendue is None:
            bilan.dire(
                FAIL,
                intitule,
                "pretend se lier a %s, que l enregistrement ne declare pas. "
                "Un fichier quelconque ne devient pas une preuve en se "
                "nommant." % ancrage,
            )
            verdict["problems"].append("ancrage %s absent des empreintes declarees" % ancrage)
            verdicts.append(verdict)
            continue

        if empreinte != attendue:
            bilan.dire(
                FAIL,
                intitule,
                "l enregistrement declare %s = %s..., le fichier se hache sur %s..."
                % (ancrage, attendue[:16], empreinte[:16]),
            )
            verdict["problems"].append("l artefact ne correspond pas a l empreinte declaree")
            verdicts.append(verdict)
            continue

        verdict["derived_assurance"] = REFERENCE
        bilan.dire(
            PASS,
            intitule,
            "ses octets se hachent sur %s de l enregistrement. Niveau derive : %s."
            % (ancrage, REFERENCE),
        )
        verdicts.append(verdict)

    return verdicts


def controle_attestation(bilan: Bilan, verdicts: list[dict],
                         arguments: argparse.Namespace) -> bool:
    """L archive du sujet est-elle attestee par une cle de confiance ?

    Si oui, les artefacts deja `reference_verifiable` montent a
    `cryptographically_attested`. Le raisonnement : l ancrage d un artefact
    est une empreinte DECLAREE PAR L ENREGISTREMENT, et cet enregistrement
    vit dans l archive. Attester l archive atteste donc les empreintes
    qu elle declare, et l artefact qui s y hache en herite -- transitivement.

    L elevation exige les trois a la fois : l attestation, l archive, et le
    magasin. Sans l un des trois, rien ne monte, et la ligne le dit.
    """
    if arguments.attestation is None:
        bilan.dire(
            NOT_TESTED,
            "attestation de l archive du sujet",
            "aucune attestation fournie. La fournir avec --attestation <fichier.jws> "
            "--trust-store <magasin> pour que le niveau `%s` soit atteignable." % ATTESTE,
            requis=True,
        )
        return False

    if arguments.archive is None or arguments.trust_store is None:
        bilan.dire(
            FAIL,
            "attestation de l archive du sujet",
            "une attestation est fournie sans --archive ou sans --trust-store : elle ne "
            "peut etre confrontee a rien. Aucun niveau n est eleve.",
        )
        return False

    try:
        import verify_attestation
    except ImportError as erreur:  # pragma: no cover - module absent
        bilan.dire(FAIL, "attestation de l archive du sujet",
                   "verify_attestation introuvable : %s" % erreur)
        return False

    # Le verificateur d attestation ecrit sur la sortie standard : on le
    # laisse parler, c est son rapport, et le lecteur a besoin de le voir.
    print("\n--- verification de l attestation du sujet ---")
    # La fabrique du verificateur, et non un Namespace rebati ici : c est ce
    # qui a casse une fois, en silence, quand une option a ete ajoutee.
    sous_arguments = verify_attestation.arguments_de_verification(
        attestation=arguments.attestation,
        archive=arguments.archive,
        trust_store=arguments.trust_store,
        allow_test_keys=arguments.allow_test_keys,
    )
    sous_bilan, niveau, _ = verify_attestation.verifier(sous_arguments)
    print("--- fin de la verification de l attestation ---\n")

    if niveau != verify_attestation.ATTESTE:
        bilan.dire(
            FAIL,
            "attestation de l archive du sujet",
            "l attestation fournie n atteint pas `%s` (%d FAIL, %d NOT TESTED dans sa "
            "propre verification). Aucun niveau n est eleve."
            % (ATTESTE, sous_bilan.compte(FAIL), sous_bilan.compte(NOT_TESTED)),
        )
        return False

    bilan.dire(
        PASS,
        "attestation de l archive du sujet",
        "l archive est attestee par une cle de confiance : les empreintes qu elle "
        "declare le sont aussi, et les artefacts qui s y hachent en heritent.",
    )
    eleves = 0
    for v in verdicts:
        if v["derived_assurance"] == REFERENCE:
            v["derived_assurance"] = ATTESTE
            v["elevated_by_attestation"] = True
            eleves += 1
    bilan.dire(
        PASS if eleves else NOT_TESTED,
        "elevation des artefacts par l attestation",
        "%d artefact(s) eleve(s) de `%s` a `%s`" % (eleves, REFERENCE, ATTESTE)
        if eleves else "aucun artefact n etait au niveau `%s` : rien a elever" % REFERENCE,
    )
    return True


def controle_revendications(bilan: Bilan, verdicts: list[dict]) -> None:
    """Le controle central : un manifeste ne doit pas se revendiquer mieux
    qu il n est.

    C est le seul endroit ou l outil contredit son entree. Sans lui, il
    suffirait d ecrire `cryptographically_attested` dans un fichier texte
    pour qu une preuve en paraisse une.
    """
    exces, non_eprouvees = [], []
    for v in verdicts:
        revendique, derive = v["claimed_assurance"], v["derived_assurance"]
        if revendique == INDEMONTRABLE:
            continue  # se declarer indemontrable n est jamais un exces
        if not v.get("verifiable_here", True):
            # L artefact n est pas la : sa revendication reste en suspens.
            # La dire contredite serait une accusation sans fondement.
            non_eprouvees.append("%s (`%s`)" % (v["artifact_id"], revendique))
            continue
        if FORCE.get(revendique, 99) > FORCE.get(derive, 0):
            exces.append(
                "%s revendique `%s`, derive `%s`" % (v["artifact_id"], revendique, derive)
            )
    if exces:
        bilan.dire(
            FAIL,
            "aucune revendication ne depasse ce qui est demontre",
            "; ".join(exces[:4]),
        )
    else:
        eprouvees = sum(1 for v in verdicts if v.get("verifiable_here", True))
        if verdicts and not eprouvees:
            # Un PASS ici serait un succes invente : aucune revendication n a
            # ete regardee. Dire PASS sur un echantillon vide est precisement
            # la facon dont un outil de preuve devient trompeur.
            bilan.dire(
                NOT_TESTED,
                "aucune revendication ne depasse ce qui est demontre",
                "aucune revendication n a pu etre eprouvee : rien n est affirme ici.",
                requis=True,
            )
        else:
            bilan.dire(
                PASS,
                "aucune revendication ne depasse ce qui est demontre",
                "%d revendication(s) eprouvee(s)" % eprouvees,
            )
    if non_eprouvees:
        bilan.dire(
            NOT_TESTED,
            "revendications non eprouvees faute d artefact",
            "%s. Fournir les fichiers sous --root pour les eprouver."
            % ", ".join(non_eprouvees[:4]),
            requis=True,
        )


def controle_signatures(bilan: Bilan, manifeste: dict) -> None:
    signatures = manifeste.get("signatures") or []
    if not signatures:
        # Formulation rectifiee le 6 novembre : depuis que l attestation
        # DETACHEE existe, dire ici que `cryptographically_attested` est
        # inatteignable serait faux -- il vient peut-etre d etre atteint
        # quelques lignes plus haut. Ce controle ne porte que sur les
        # signatures INSCRITES AU MANIFESTE, qui sont une autre chose.
        bilan.dire(
            NOT_TESTED,
            "signatures inscrites au manifeste",
            "aucune, et ce depot n en verifie aucune : le tableau `signatures[]` du "
            "manifeste reste non exploite. Le niveau `%s` s obtient par une "
            "attestation DETACHEE de l archive (--attestation), pas par ce champ."
            % ATTESTE,
        )
        return
    cles = [s.get("key_id") for s in signatures if isinstance(s, dict)]
    bilan.dire(
        NOT_TESTED,
        "signatures inscrites au manifeste",
        "%d signature(s) presente(s) (cles %s) et AUCUNE n est verifiee ici. "
        "Une signature non verifiee ne vaut pas mieux qu un champ texte."
        % (len(signatures), ", ".join(str(c) for c in cles[:3])),
    )


def controle_enonces(bilan: Bilan, manifeste: dict) -> None:
    """La these du produit, rendue a chaque execution."""
    enonces = manifeste.get("statements") or []
    bilan.dire(
        NOT_TESTED,
        "enonces attaches au manifeste",
        "%d enonce(s). Une description textuelle d une execution ne constitue "
        "pas une preuve que cette execution a eu lieu : aucun de ces textes "
        "n est verifie, ni ne peut l etre." % len(enonces),
    )


def controle_verite(bilan: Bilan) -> None:
    bilan.dire(
        NOT_TESTED,
        "verite de l execution",
        "hors de portee de cet outil et de ce depot. Lier un artefact a un "
        "enregistrement ne dit pas qu une execution a eu lieu, ni quand, ni "
        "chez qui. Aucune horloge de confiance, aucun ancrage exterieur.",
    )


def agregat(verdicts: list[dict]) -> str:
    """Le niveau de la liaison entiere : le plus faible de ses artefacts.

    Une chaine vaut son maillon le plus faible. Prendre le plus fort
    laisserait un artefact non ancre se faire couvrir par son voisin.
    """
    if not verdicts:
        return DECLARE
    return min((v["derived_assurance"] for v in verdicts), key=lambda n: FORCE.get(n, 0))


def verifier(arguments: argparse.Namespace) -> int:
    bilan = Bilan()
    manifeste_chemin = arguments.manifest
    racine = arguments.root or manifeste_chemin.parent

    print("Manifeste de preuve : %s" % manifeste_chemin)
    if not manifeste_chemin.is_file():
        bilan.dire(FAIL, "manifeste lisible", "%s introuvable" % manifeste_chemin)
        return rendre(bilan, [], DECLARE, arguments)
    print("empreinte           : %s" % sha256_fichier(manifeste_chemin))
    print("racine des artefacts: %s\n" % racine)

    try:
        manifeste = objet_json(manifeste_chemin.read_bytes(), "le manifeste")
    except Illisible as erreur:
        bilan.dire(FAIL, "manifeste lisible", str(erreur))
        return rendre(bilan, [], DECLARE, arguments)

    if not controle_forme(bilan, manifeste):
        return rendre(bilan, [], DECLARE, arguments)

    verdicts = []
    for intitule, controle in (
        ("sujet", lambda: controle_sujet(bilan, manifeste, arguments.archive)),
        (
            "artefacts",
            lambda: verdicts.extend(
                controle_artefacts(bilan, manifeste, racine, arguments.max_artifact_bytes)
            ),
        ),
    ):
        try:
            controle()
        except Illisible as erreur:
            bilan.dire(FAIL, intitule, str(erreur))
        except Exception as erreur:  # noqa: BLE001 - un defaut de l outil sort en FAIL nomme
            bilan.dire(
                FAIL, intitule, "controle interrompu : %s: %s" % (type(erreur).__name__, erreur)
            )

    # AVANT le controle des revendications : l elevation change le niveau
    # derive, donc elle doit etre faite avant qu on juge si une revendication
    # le depasse. Dans l autre ordre, un manifeste revendiquant a juste titre
    # `cryptographically_attested` serait refuse.
    try:
        controle_attestation(bilan, verdicts, arguments)
    except Illisible as erreur:
        bilan.dire(FAIL, "attestation de l archive du sujet", str(erreur))
    except Exception as erreur:  # noqa: BLE001 - un defaut de l outil sort en FAIL nomme
        bilan.dire(FAIL, "attestation de l archive du sujet",
                   "controle interrompu : %s: %s" % (type(erreur).__name__, erreur))

    controle_revendications(bilan, verdicts)
    controle_signatures(bilan, manifeste)
    controle_enonces(bilan, manifeste)
    controle_verite(bilan)

    return rendre(bilan, verdicts, agregat(verdicts), arguments)


def rendre(bilan: Bilan, verdicts: list[dict], niveau: str, arguments: argparse.Namespace) -> int:
    print(
        "\nBILAN : %d PASS, %d FAIL, %d NOT TESTED"
        % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED))
    )
    if bilan.compte(FAIL):
        print("Cette liaison ne doit pas etre presentee comme verifiee.")
        niveau_effectif = None
    else:
        niveau_effectif = niveau
        print("Niveau de garantie DERIVE pour la liaison : %s" % niveau)
        if niveau == ATTESTE:
            print(
                "Soit : les artefacts offerts sont ceux auxquels l enregistrement\n"
                "se refere, ET une partie identifiee s est engagee sur l empreinte\n"
                "de l archive qui les declare. Ce n est toujours pas une preuve que\n"
                "l execution a eu lieu, ni une preuve de la DATE : celle-ci reste\n"
                "declaree faute d ancrage tiers."
            )
        elif niveau == REFERENCE:
            print(
                "Soit : les artefacts offerts sont bien ceux auxquels\n"
                "l enregistrement se refere. Ce n est pas une preuve que\n"
                "l execution a eu lieu."
            )
        elif niveau == DECLARE:
            absents = [v for v in verdicts if not v.get("verifiable_here", True)]
            if absents:
                print(
                    "Soit : %d artefact(s) sur %d n ont pas pu etre eprouves ici,\n"
                    "donc la liaison entiere retombe au niveau declaratif. Ce n est\n"
                    "pas un refus du manifeste : c est une verification incomplete."
                    % (len(absents), len(verdicts))
                )
            else:
                print(
                    "Soit : rien n a pu etre ancre dans l enregistrement. Le\n"
                    "manifeste est un document, pas une preuve."
                )

    manquantes = bilan.requises_non_demontrees()
    if arguments.strict:
        if manquantes:
            print(
                "\nMODE STRICT : %d garantie(s) requise(s) non demontree(s) :"
                % len(manquantes)
            )
            for m in manquantes:
                print("  - %s" % m)
            print("Aucun verdict n a change : seul le code de sortie en tient compte (2).")
        else:
            print("\nMODE STRICT : toutes les garanties requises sont demontrees.")

    if arguments.json:
        rapport = {
            "schema": "neomundi.evidence.binding-report/1",
            "strict": bool(arguments.strict),
            "required_not_demonstrated": manquantes,
            "exit_code": bilan.code_de_sortie(arguments.strict),
            "manifest": str(arguments.manifest),
            "controls": [
                {"state": e, "control": i, "detail": d} for e, i, d in bilan.lignes
            ],
            "counts": {
                "pass": bilan.compte(PASS),
                "fail": bilan.compte(FAIL),
                "not_tested": bilan.compte(NOT_TESTED),
            },
            "artifacts": verdicts,
            "derived_assurance": niveau_effectif,
            "establishes": (
                "that the offered artifacts are the ones the hash-chained record "
                "refers to"
                if niveau_effectif == REFERENCE
                else None
            ),
            "does_not_establish": [
                "that the execution took place",
                "when it took place",
                "which operator served it",
                "authenticity: no signature is verified by this repository",
            ],
        }
        chemin = arguments.json
        chemin.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("\nrapport lisible par machine : %s" % chemin)

    return bilan.code_de_sortie(arguments.strict)


# --------------------------------------------------------------------------


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Lie une observation NeoMundi a des artefacts externes, et verifie la liaison."
    )
    sous = analyseur.add_subparsers(dest="commande", required=True)

    b = sous.add_parser("build", help="construire un manifeste de preuve")
    b.add_argument("--archive", type=Path, required=True, help="archive Evidence du sujet")
    b.add_argument("--observation", required=True, help="observation_id du sujet")
    b.add_argument(
        "--artifact",
        action="append",
        metavar="ROLE=CHEMIN",
        help="un artefact a lier ; roles : %s" % ", ".join(sorted(ANCRAGE_PAR_ROLE)),
    )
    b.add_argument("--statement", action="append", help="un enonce a attacher (jamais verifie)")
    b.add_argument(
        "--created-at",
        dest="created_at",
        required=True,
        help="horodatage de creation, format 2026-11-05T12:00:00Z. Exige explicitement : "
        "l outil ne lit pas l horloge, pour que deux executions rendent le meme manifeste.",
    )
    b.add_argument(
        "--basenames",
        action="store_true",
        help="n inscrire que le nom de fichier des artefacts, sans leur repertoire",
    )
    b.add_argument("--out", type=Path, default=None, help="fichier de sortie ; defaut : la sortie standard")

    v = sous.add_parser("verify", help="verifier un manifeste de preuve")
    v.add_argument("manifest", type=Path, help="le manifeste a verifier")
    v.add_argument(
        "--root", type=Path, default=None,
        help="repertoire ou resoudre les chemins d artefacts ; defaut : celui du manifeste",
    )
    v.add_argument(
        "--archive", type=Path, default=None,
        help="archive Evidence du sujet, pour confronter les empreintes declarees a "
        "l enregistrement. Sans elle, ce controle est NOT TESTED.",
    )
    v.add_argument("--json", type=Path, default=None, metavar="FICHIER",
                   help="ecrire aussi un rapport lisible par machine")
    v.add_argument(
        "--attestation", type=Path, default=None, metavar="FICHIER.jws",
        help="attestation detachee de l archive du sujet. Avec --archive et "
             "--trust-store, elle rend le niveau `%s` atteignable." % ATTESTE,
    )
    v.add_argument(
        "--trust-store", type=Path, default=None, metavar="FICHIER",
        help="magasin de confiance, pour resoudre la cle de l attestation",
    )
    v.add_argument(
        "--allow-test-keys", action="store_true",
        help="accepter explicitement une cle de statut `test`",
    )
    v.add_argument(
        "--strict", action="store_true",
        help="sortir en code 2 si une garantie REQUISE n est pas demontree. Ne "
             "change AUCUN verdict : les lignes restent PASS, FAIL ou NOT TESTED "
             "a l identique. Pour les consommateurs automatises.",
    )
    v.add_argument(
        "--max-artifact-bytes",
        dest="max_artifact_bytes",
        type=int,
        default=PLAFOND_ARTEFACT,
        metavar="OCTETS",
        help="plafond de lecture d un artefact ; defaut %d. Au-dela, l artefact "
        "est NOT TESTED et non lu." % PLAFOND_ARTEFACT,
    )

    arguments = analyseur.parse_args()
    try:
        if arguments.commande == "build":
            return construire(arguments)
        return verifier(arguments)
    except Illisible as erreur:
        print("[%-10s] %s" % (FAIL, erreur))
        return 1


if __name__ == "__main__":
    sys.exit(main())

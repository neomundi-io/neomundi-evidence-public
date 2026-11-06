# -*- coding: utf-8 -*-
"""Ingere un paquet d execution fourni par un tiers. N EXECUTE RIEN.

    python adapters/ingest.py <dossier|paquet.zip> \\
        --out rapport.json [--md rapport.md] \\
        [--trust-store <magasin.json>] [--strict] [--lang fr|en]

CE QUE CE PROGRAMME COMBLE
--------------------------

`verify.py` ne sait lire qu une archive DEJA au format Evidence : il exige un
`manifest.json` et des membres connus. Confronte au dossier reel recu le
30 octobre -- 22 fichiers, 21 empreintes declarees, 21 concordantes -- il a
refuse, et ce refus etait JUSTE : ce paquet n est pas une archive Evidence.

Rien ne convertissait donc une collecte brute en objet exploitable. Un pilote
pouvait nous tendre ses fichiers et s arreter la. C est ce chainon, et rien
de plus.

LA SEULE REGLE QUI COMPTE
-------------------------

**Une declaration non verifiee ne devient jamais un fait atteste.** Chaque
ligne du rapport porte donc sa nature :

  CONTROLE        nous l avons recalcule. Empreintes, tailles, structure,
                  signatures. C est le seul registre ou nous engageons
                  quelque chose.
  DECLARE         la parole du soumetteur, conservee VERBATIM. Identite,
                  modele, conditions d execution. Nous la transportons,
                  nous ne la cautionnons pas.
  NON DEMONTRABLE aucun controle ne pourrait l etablir depuis ce paquet.
                  Ce n est pas un manque de zele : c est une propriete du
                  materiau.

Un champ dont le chemin ne resout pas est **absent**, jamais `null` -- meme
discipline que pour un signal non mesure.

CE QU IL NE FAIT PAS, PAR CONSTRUCTION
--------------------------------------

Il n execute aucun code venu du paquet, ne suit aucun lien symbolique,
n ecrit jamais dans le paquet soumis, et n a besoin d AUCUNE cle privee.
Il ne verifie pas les signatures lui-meme : il appelle
`verify_attestation.py`, le MEME verificateur qu un auditeur, et rapporte
son verdict tel quel. Aucun second moteur de signature n existe ici.

Le magasin de confiance vient de l OPERATEUR, jamais du paquet : un paquet
ne doit pas porter sa propre reponse a la question de savoir si son
signataire est digne de confiance.

Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

try:
    import i18n
except ImportError:  # pragma: no cover - chemin de degradation
    class i18n:  # type: ignore[no-redef]
        FR = "fr"
        EN = "en"

        @staticmethod
        def traduire(texte: str, langue: str) -> str:
            return texte

        @staticmethod
        def traduire_format(format_fr: str, langue: str) -> str:
            return format_fr


SCHEMA_SOUMISSION = "neomundi.evidence.submission/1"
SCHEMA_RAPPORT = "neomundi.evidence.ingestion-report/1"
MANIFESTE = "submission.json"

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"
CONTROLE, DECLARE, INDEMONTRABLE = "CONTROLE", "DECLARE", "NON DEMONTRABLE"

ACCEPTE, REJETE, INCOMPLET = "ACCEPTE", "REJETE", "INCOMPLET"

#: Bornes de securite. Un paquet soumis est une entree HOSTILE jusqu a
#: preuve du contraire : il peut etre malforme par accident comme par
#: dessein, et les deux cas se traitent pareil.
MAX_ARTEFACTS = 512
MAX_OCTETS_PAR_FICHIER = 64 * 1024 * 1024
MAX_OCTETS_TOTAL = 256 * 1024 * 1024
MAX_MEMBRES_ZIP = 4096

#: Un chemin de soumission est RELATIF, en barres obliques, sans remontee.
#: Les trois refus ci-dessous ne sont pas du zele : un paquet capable de
#: nommer un fichier hors de lui-meme peut faire ecrire ou lire n importe ou.
MOTIF_CHEMIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,511}$")

_LANGUE = [i18n.FR]


def dis(*morceaux: object) -> None:
    if not morceaux:
        print()
        return
    premier = morceaux[0]
    if isinstance(premier, str):
        pose = i18n.traduire_format(premier, _LANGUE[0])
        if pose == premier:
            pose = i18n.traduire(premier, _LANGUE[0])
        premier = pose
    print(premier, *morceaux[1:])


class Bilan:
    """Trois etats, et pour chacun sa NATURE. `NOT TESTED` n est pas un `PASS`."""

    def __init__(self) -> None:
        self.lignes: list[dict] = []

    def dire(self, etat: str, nature: str, intitule: str, detail: str = "",
             requis: bool = False) -> None:
        self.lignes.append({"etat": etat, "nature": nature,
                            "intitule": intitule, "detail": detail,
                            "requis": requis})
        vu = i18n.traduire(intitule, _LANGUE[0])
        vu_detail = i18n.traduire(detail, _LANGUE[0])
        print("[%-10s] [%-15s] %s%s"
              % (etat, nature, vu, " - " + vu_detail if vu_detail else ""))

    def compte(self, etat: str) -> int:
        return sum(1 for l in self.lignes if l["etat"] == etat)

    def requis_non_demontres(self) -> list[str]:
        return [l["intitule"] for l in self.lignes
                if l["requis"] and l["etat"] != PASS]

    def verdict(self) -> str:
        """ACCEPTE, REJETE ou INCOMPLET -- et jamais autre chose.

        Un FAIL rejette. Sans FAIL, un controle REQUIS non demontre rend le
        paquet INCOMPLET : ce n est pas un refus, c est un paquet auquel il
        manque quelque chose que le soumetteur peut fournir.
        """
        if self.compte(FAIL):
            return REJETE
        if self.requis_non_demontres():
            return INCOMPLET
        return ACCEPTE


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def chemin_sur(brut: object) -> tuple[bool, str]:
    """Le chemin declare est-il relatif, sans remontee, sans lettre de lecteur ?"""
    if not isinstance(brut, str) or not brut:
        return False, "chemin absent ou non textuel"
    if "\\" in brut:
        return False, "barre oblique inversee : un chemin de soumission s ecrit en `/`"
    if brut.startswith("/"):
        return False, "chemin ABSOLU"
    if re.match(r"^[A-Za-z]:", brut):
        return False, "lettre de lecteur"
    if ".." in brut.split("/"):
        return False, "segment `..` : remontee hors du paquet"
    if not MOTIF_CHEMIN.match(brut):
        return False, "caracteres hors du jeu admis"
    return True, ""


def deplier(source: Path, travail: Path, bilan: Bilan) -> Path | None:
    """Rend la racine a lire. Un `.zip` est deplie SOUS CONTROLE."""
    if source.is_dir():
        bilan.dire(PASS, CONTROLE, "forme du paquet",
                   "dossier lu sur place, aucune extraction")
        return source
    if not zipfile.is_zipfile(source):
        bilan.dire(FAIL, CONTROLE, "forme du paquet",
                   "ni dossier ni archive ZIP lisible : %s" % source.name)
        return None

    cible = travail / "deplie"
    cible.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as z:
        infos = z.infolist()
        if len(infos) > MAX_MEMBRES_ZIP:
            bilan.dire(FAIL, CONTROLE, "forme du paquet",
                       "%d membres, borne %d" % (len(infos), MAX_MEMBRES_ZIP))
            return None
        # La taille DECOMPRESSEE est verifiee AVANT d ecrire quoi que ce
        # soit : un paquet de quelques kilo-octets peut se deplier en
        # gigaoctets, et l apprendre pendant l extraction est trop tard.
        total = sum(i.file_size for i in infos)
        if total > MAX_OCTETS_TOTAL:
            bilan.dire(FAIL, CONTROLE, "forme du paquet",
                       "%d octets decompresses annonces, borne %d"
                       % (total, MAX_OCTETS_TOTAL))
            return None
        for i in infos:
            ok, pourquoi = chemin_sur(i.filename.rstrip("/"))
            if not ok:
                bilan.dire(FAIL, CONTROLE, "chemins du paquet",
                           "membre refuse %r : %s" % (i.filename, pourquoi))
                return None
        z.extractall(cible)
    bilan.dire(PASS, CONTROLE, "forme du paquet",
               "archive ZIP de %d membre(s), %d octets decompresses, depliee"
               % (len(infos), total))
    return cible


def controle_manifeste(racine: Path, bilan: Bilan) -> dict | None:
    chemin = racine / MANIFESTE
    if not chemin.is_file():
        bilan.dire(FAIL, CONTROLE, "manifeste de soumission",
                   "`%s` absent a la racine du paquet" % MANIFESTE)
        return None
    try:
        # Sur des OCTETS : un BOM UTF-8 est detecte tout seul. Quinze des
        # vingt-deux fichiers du dossier reel du 30 octobre en portaient un.
        doc = json.loads(chemin.read_bytes())
    except (ValueError, OSError) as erreur:
        bilan.dire(FAIL, CONTROLE, "manifeste de soumission",
                   "`%s` illisible : %s" % (MANIFESTE, type(erreur).__name__))
        return None
    if not isinstance(doc, dict):
        bilan.dire(FAIL, CONTROLE, "manifeste de soumission",
                   "le manifeste n est pas un objet JSON")
        return None
    if doc.get("schema") != SCHEMA_SOUMISSION:
        bilan.dire(FAIL, CONTROLE, "schema du manifeste",
                   "attendu %s, declare %r"
                   % (SCHEMA_SOUMISSION, doc.get("schema")))
        return None
    bilan.dire(PASS, CONTROLE, "manifeste de soumission",
               "%s, %d octets" % (SCHEMA_SOUMISSION, chemin.stat().st_size))
    return doc


def controle_champs(doc: dict, bilan: Bilan) -> None:
    requis = ["submission_id", "submitted_at_declared", "pilot",
              "execution", "artifacts"]
    manquants = [c for c in requis if c not in doc]
    if manquants:
        bilan.dire(FAIL, CONTROLE, "champs obligatoires",
                   "absents : %s" % ", ".join(manquants))
    else:
        bilan.dire(PASS, CONTROLE, "champs obligatoires",
                   "les %d champs du contrat sont presents" % len(requis))

    ident = doc.get("submission_id")
    if not isinstance(ident, str) or not re.match(r"^[a-z0-9][a-z0-9-]{2,63}$", ident):
        bilan.dire(FAIL, CONTROLE, "identifiant de soumission",
                   "non conforme a `^[a-z0-9][a-z0-9-]{2,63}$` : %r" % ident)
    else:
        bilan.dire(PASS, CONTROLE, "identifiant de soumission", ident)

    pilote = doc.get("pilot") or {}
    nom = pilote.get("name_declared")
    if not isinstance(nom, str) or not nom.strip():
        bilan.dire(FAIL, CONTROLE, "identite du soumetteur",
                   "`pilot.name_declared` absent ou vide")
    else:
        # DECLARE, et c est tout ce que cela peut etre : rien dans un
        # fichier n etablit qui l a ecrit.
        bilan.dire(NOT_TESTED, DECLARE, "identite du soumetteur",
                   "%r -- declaree, et non verifiee. Aucun controle sur un "
                   "paquet ne peut etablir qui l a produit." % nom)

    exe = doc.get("execution") or {}
    for champ in ("kind_declared", "model_declared"):
        if not exe.get(champ):
            bilan.dire(FAIL, CONTROLE, "conditions d execution",
                       "`execution.%s` absent" % champ)
            break
    else:
        bilan.dire(NOT_TESTED, DECLARE, "conditions d execution",
                   "modele %r, nature %r, fournisseur %r -- declares. Ce "
                   "paquet ne porte rien qui permette de les confronter."
                   % (exe.get("model_declared"), exe.get("kind_declared"),
                      exe.get("provider_declared")))


def controle_artefacts(racine: Path, doc: dict, bilan: Bilan) -> list[dict]:
    """Le SEUL registre ou ce programme etablit quelque chose."""
    artefacts = doc.get("artifacts")
    if not isinstance(artefacts, list) or not artefacts:
        bilan.dire(FAIL, CONTROLE, "artefacts declares",
                   "aucun artefact declare")
        return []
    if len(artefacts) > MAX_ARTEFACTS:
        bilan.dire(FAIL, CONTROLE, "artefacts declares",
                   "%d artefacts, borne %d" % (len(artefacts), MAX_ARTEFACTS))
        return []

    resultats: list[dict] = []
    total = 0
    concordants = absents = discordants = refuses = 0

    for a in artefacts:
        brut = a.get("path") if isinstance(a, dict) else None
        ok, pourquoi = chemin_sur(brut)
        if not ok:
            refuses += 1
            resultats.append({"path": brut, "etat": "chemin_refuse",
                              "pourquoi": pourquoi})
            continue
        cible = racine / brut
        # Resolution puis confinement : le motif de chemin ne suffit pas,
        # un lien symbolique passe le motif et sort du paquet.
        try:
            resolu = cible.resolve()
            dedans = resolu == racine.resolve() or racine.resolve() in resolu.parents
        except OSError:
            dedans = False
        if cible.is_symlink() or not dedans:
            refuses += 1
            resultats.append({"path": brut, "etat": "chemin_refuse",
                              "pourquoi": "lien symbolique ou cible hors du paquet"})
            continue
        if not cible.is_file():
            absents += 1
            resultats.append({"path": brut, "etat": "absent"})
            continue
        taille = cible.stat().st_size
        if taille > MAX_OCTETS_PAR_FICHIER:
            refuses += 1
            resultats.append({"path": brut, "etat": "trop_volumineux",
                              "bytes": taille})
            continue
        total += taille
        if total > MAX_OCTETS_TOTAL:
            bilan.dire(FAIL, CONTROLE, "volume du paquet",
                       "au-dela de %d octets au total" % MAX_OCTETS_TOTAL)
            return resultats
        reel = sha256_fichier(cible)
        annonce = a.get("sha256")
        octets_annonces = a.get("bytes")
        if reel == annonce and taille == octets_annonces:
            concordants += 1
            resultats.append({"path": brut, "etat": "concordant",
                              "sha256": reel, "bytes": taille,
                              "role_declared": a.get("role")})
        else:
            discordants += 1
            resultats.append({"path": brut, "etat": "discordant",
                              "sha256_recalcule": reel,
                              "sha256_declare": annonce,
                              "bytes_reels": taille,
                              "bytes_declares": octets_annonces})

    detail = ("%d concordant(s), %d discordant(s), %d absent(s), %d refuse(s), "
              "%d octets recalcules" % (concordants, discordants, absents,
                                        refuses, total))
    if discordants or refuses:
        bilan.dire(FAIL, CONTROLE, "empreintes des artefacts declares", detail)
    elif absents:
        # Un artefact annonce et non fourni n est pas une fraude : c est un
        # paquet incomplet, et le soumetteur peut le completer.
        bilan.dire(NOT_TESTED, CONTROLE, "empreintes des artefacts declares",
                   detail, requis=True)
    else:
        bilan.dire(PASS, CONTROLE, "empreintes des artefacts declares", detail)
    return resultats


def controle_fichiers_non_declares(racine: Path, doc: dict,
                                   bilan: Bilan) -> list[str]:
    declares = {a.get("path") for a in (doc.get("artifacts") or [])
                if isinstance(a, dict)}
    declares.add(MANIFESTE)
    for att in (doc.get("attestations") or []):
        if isinstance(att, dict):
            declares.add(att.get("jws_path"))
            declares.add(att.get("subject_path"))
    presents = []
    for p in sorted(racine.rglob("*")):
        if p.is_file():
            presents.append(p.relative_to(racine).as_posix())
    surplus = [n for n in presents if n not in declares]
    if surplus:
        # Pas un FAIL : un fichier en surplus n invalide rien. Mais le taire
        # laisserait croire que le paquet a ete couvert en entier.
        bilan.dire(NOT_TESTED, CONTROLE, "fichiers non declares",
                   "%d fichier(s) present(s) et non declare(s), donc NON "
                   "controle(s) : %s" % (len(surplus), ", ".join(surplus[:6])))
    else:
        bilan.dire(PASS, CONTROLE, "fichiers non declares",
                   "aucun : les %d fichier(s) du paquet sont tous declares"
                   % len(presents))
    return surplus


def controle_attestations(racine: Path, doc: dict, magasin: Path | None,
                          bilan: Bilan) -> list[dict]:
    atts = doc.get("attestations") or []
    if not atts:
        bilan.dire(NOT_TESTED, CONTROLE, "signatures existantes",
                   "le paquet ne declare aucune attestation. Son niveau ne "
                   "depassera donc pas `reference_verifiable`.")
        return []
    if magasin is None:
        bilan.dire(NOT_TESTED, CONTROLE, "signatures existantes",
                   "%d attestation(s) declaree(s), et aucun magasin de "
                   "confiance fourni. Le fournir avec --trust-store : jamais "
                   "celui du paquet." % len(atts), requis=True)
        return []

    resultats = []
    echecs = 0
    for att in atts:
        jws = att.get("jws_path")
        sujet = att.get("subject_path")
        bons = all(chemin_sur(c)[0] for c in (jws, sujet))
        if not bons or not (racine / jws).is_file() or not (racine / sujet).is_file():
            echecs += 1
            resultats.append({"jws_path": jws, "etat": "fichier_absent_ou_refuse"})
            continue
        # UN SEUL verificateur de signature existe dans ce depot. On
        # l appelle, on ne le refait pas : deux moteurs qui divergent ne
        # prouvent rien, et celui-ci est celui qu un auditeur emploie.
        fini = subprocess.run(
            [sys.executable, str(RACINE / "verify_attestation.py"),
             str(racine / jws), "--archive", str(racine / sujet),
             "--trust-store", str(magasin)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        sortie = (fini.stdout or "") + (fini.stderr or "")
        bilan_ligne = next((l for l in sortie.splitlines()
                            if l.startswith("BILAN")), "")
        niveau = next((l for l in sortie.splitlines()
                       if l.startswith("Niveau")), "")
        resultats.append({"jws_path": jws, "subject_path": sujet,
                          "exit": fini.returncode, "bilan": bilan_ligne,
                          "niveau": niveau})
        if fini.returncode != 0:
            echecs += 1

    detail = "; ".join("%s -> exit %s %s" % (r.get("jws_path"), r.get("exit"),
                                             r.get("bilan", ""))
                       for r in resultats)[:400]
    if echecs:
        bilan.dire(FAIL, CONTROLE, "signatures existantes", detail)
    else:
        bilan.dire(PASS, CONTROLE, "signatures existantes", detail)
    return resultats


def controle_provenance(doc: dict, bilan: Bilan) -> None:
    prov = doc.get("provenance_declared") or {}
    champs = ("code_reference_declared", "environment_declared",
              "evaluator_declared")
    renseignes = [c for c in champs if prov.get(c)]
    absents = [c for c in champs if not prov.get(c)]
    if renseignes:
        bilan.dire(NOT_TESTED, DECLARE, "provenance de l execution",
                   "renseignee : %s ; absente : %s. Declaree et non "
                   "verifiable depuis ce paquet."
                   % (", ".join(renseignes), ", ".join(absents) or "aucune"))
    else:
        bilan.dire(NOT_TESTED, INDEMONTRABLE, "provenance de l execution",
                   "aucun champ de provenance declare. Toute affirmation sur "
                   "l environnement ou l instrument de cette execution est "
                   "donc `not_demonstrable`.")

    bilan.dire(NOT_TESTED, INDEMONTRABLE, "que l execution ait eu lieu",
               "hors de portee d une ingestion. Nous recalculons des "
               "empreintes de FICHIERS ; qu ils proviennent de l execution "
               "annoncee est une declaration, et le restera.")

    limites = doc.get("limits_declared") or []
    if limites:
        bilan.dire(NOT_TESTED, DECLARE, "limites annoncees par le soumetteur",
                   "%d limite(s), conservee(s) verbatim : %s"
                   % (len(limites), " | ".join(str(l) for l in limites)[:240]))


def rendre_markdown(rapport: dict) -> str:
    l = ["# Rapport d ingestion NeoMundi Evidence", "",
         "- Paquet : `%s`" % rapport["package"],
         "- Soumission : `%s`" % rapport.get("submission_id"),
         "- Verdict : **%s**" % rapport["verdict"],
         "- Decomptes : %d PASS, %d FAIL, %d NOT TESTED"
         % (rapport["counts"]["pass"], rapport["counts"]["fail"],
            rapport["counts"]["not_tested"]),
         "", "## Lignes de controle", "",
         "| Etat | Nature | Controle | Detail |", "|---|---|---|---|"]
    for ligne in rapport["lines"]:
        l.append("| %s | %s | %s | %s |"
                 % (ligne["etat"], ligne["nature"], ligne["intitule"],
                    ligne["detail"].replace("|", "/")[:200]))
    l += ["", "## Ce que ce rapport n etablit pas", ""]
    for x in rapport["does_not_establish"]:
        l.append("- %s" % x)
    return "\n".join(l) + "\n"


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Ingere un paquet d execution tiers. N execute rien, et "
                    "n a besoin d aucune cle privee.")
    analyseur.add_argument("paquet", type=Path,
                           help="dossier ou archive ZIP de soumission")
    analyseur.add_argument("--out", type=Path, default=None,
                           help="rapport JSON, lisible par machine")
    analyseur.add_argument("--md", type=Path, default=None,
                           help="rapport Markdown, lisible par un humain")
    analyseur.add_argument("--trust-store", type=Path, default=None,
                           help="magasin de confiance de l OPERATEUR, pour "
                                "verifier les attestations declarees. Jamais "
                                "celui porte par le paquet")
    analyseur.add_argument("--strict", action="store_true",
                           help="sortir 2 sur un paquet INCOMPLET")
    analyseur.add_argument("--lang", choices=("fr", "en"), default="fr",
                           help="langue de la PROSE. Ne change aucun verdict")
    arguments = analyseur.parse_args()
    _LANGUE[0] = arguments.lang

    bilan = Bilan()
    dis("paquet : %s" % arguments.paquet)
    dis()

    travail = Path(tempfile.mkdtemp(prefix="evidence-ingest-"))
    try:
        racine = deplier(arguments.paquet, travail, bilan)
        doc: dict = {}
        artefacts: list[dict] = []
        surplus: list[str] = []
        atts: list[dict] = []
        if racine is not None:
            lu = controle_manifeste(racine, bilan)
            if lu is not None:
                doc = lu
                controle_champs(doc, bilan)
                artefacts = controle_artefacts(racine, doc, bilan)
                surplus = controle_fichiers_non_declares(racine, doc, bilan)
                atts = controle_attestations(racine, doc,
                                             arguments.trust_store, bilan)
                controle_provenance(doc, bilan)

        verdict = bilan.verdict()
        rapport = {
            "schema": SCHEMA_RAPPORT,
            "package": str(arguments.paquet),
            "submission_id": doc.get("submission_id"),
            "submission_schema": doc.get("schema"),
            "verdict": verdict,
            "counts": {"pass": bilan.compte(PASS), "fail": bilan.compte(FAIL),
                       "not_tested": bilan.compte(NOT_TESTED)},
            "required_not_demonstrated": bilan.requis_non_demontres(),
            "lines": bilan.lignes,
            "artifacts": artefacts,
            "undeclared_files": surplus,
            "attestations": atts,
            "declared_verbatim": {
                "pilot": doc.get("pilot"),
                "execution": doc.get("execution"),
                "provenance_declared": doc.get("provenance_declared"),
                "limits_declared": doc.get("limits_declared"),
                "submitted_at_declared": doc.get("submitted_at_declared"),
            },
            "does_not_establish": [
                "Que l execution declaree ait eu lieu. Nous recalculons des "
                "empreintes de fichiers, pas des faits.",
                "Qui a produit ce paquet. L identite du soumetteur est "
                "declaree, et aucun controle sur des fichiers ne l etablit.",
                "Que les artefacts fournis soient ceux de l execution "
                "annoncee. Leur concordance d empreinte etablit qu ils n ont "
                "pas bouge depuis que le manifeste a ete ecrit, rien de plus.",
                "La date. `submitted_at_declared` est declaree ; aucune "
                "horloge de confiance n intervient.",
                "Le sens des champs du soumetteur. Decider qu un de ses "
                "champs correspond a l un des notres est une affirmation sur "
                "deux definitions : voir `adapters/reconcile.py`, qui exige "
                "une table de correspondance DECLAREE.",
            ],
        }

        dis()
        dis("BILAN : %d PASS, %d FAIL, %d NOT TESTED"
            % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))
        dis("VERDICT : %s" % verdict)
        if verdict == REJETE:
            dis()
            dis("Le paquet est REJETE : au moins un controle a echoue. Les "
                "lignes FAIL ci-dessus disent lesquelles.")
        elif verdict == INCOMPLET:
            dis()
            dis("Le paquet est INCOMPLET, et ce n est pas un refus : il "
                "manque quelque chose que le soumetteur peut fournir.")
            for x in bilan.requis_non_demontres():
                dis("  - %s" % x)
        else:
            dis()
            dis("Le paquet est ACCEPTE : sa structure et les empreintes qu il "
                "declare sont controlees. Les lignes DECLARE restent la "
                "parole du soumetteur, et les NON DEMONTRABLE le resteront.")

        if arguments.out:
            arguments.out.parent.mkdir(parents=True, exist_ok=True)
            arguments.out.write_bytes(
                (json.dumps(rapport, ensure_ascii=False, indent=2) + "\n")
                .encode("utf-8"))
            dis("rapport JSON : %s" % arguments.out)
        if arguments.md:
            arguments.md.parent.mkdir(parents=True, exist_ok=True)
            arguments.md.write_bytes(rendre_markdown(rapport).encode("utf-8"))
            dis("rapport Markdown : %s" % arguments.md)

        if verdict == REJETE:
            return 1
        if verdict == INCOMPLET and arguments.strict:
            return 2
        return 0
    finally:
        shutil.rmtree(travail, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

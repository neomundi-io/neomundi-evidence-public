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

# La traduction est OPTIONNELLE, et c est voulu : les 21 controles ne
# doivent jamais dependre d elle. Sans `i18n.py` a cote, l outil tourne,
# rend exactement les memes verdicts et le meme code de sortie -- en
# francais. Un auditeur peut donc copier ce seul fichier.
try:
    import i18n
except ImportError:  # pragma: no cover - chemin de degradation
    class i18n:  # type: ignore[no-redef]
        """Repli sans traduction. Rend tout tel quel."""

        FR = "fr"
        EN = "en"
        LANGUES = ("fr",)

        @staticmethod
        def traduire(texte: str, langue: str) -> str:
            return texte

        @staticmethod
        def traduire_format(format_fr: str, langue: str) -> str:
            return format_fr

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
    "station.export.campagne/3",
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
    # `/3` ajoute UN membre a `/2` : la provenance instrumentale, telle que
    # l API la sert et sans interpretation. Un membre de plus, et aucun
    # changement aux sept autres -- une archive `/2` reste donc lisible, et
    # les controles de provenance y rendent NOT TESTED plutot que FAIL.
    "station.export.campagne/3": (
        "observations.csv",
        "observations.jsonl",
        "measurements.jsonl",
        "measurement_coverage.jsonl",
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


def _dis(langue: str, format_fr: str, *arguments: object) -> None:
    """Imprime une ligne de prose, dans `langue`.

    Les etats, les empreintes et les decomptes passent par les arguments :
    ils ne sont jamais traduits, seul le modele l est.
    """
    modele = i18n.traduire_format(format_fr, langue)
    print(modele % arguments if arguments else modele)


class Bilan:
    """Les resultats, et rien d'autre : aucun etat n'est deduit, chacun est dit."""

    def __init__(self, langue: str = i18n.FR) -> None:
        #: La langue d AFFICHAGE, et rien de plus. `self.lignes` stocke
        #: toujours le francais : c est ce qui garantit que le mode strict,
        #: le code de sortie et le rapport JSON ne dependent pas de la
        #: langue, puisque tous trois lisent `self.lignes`.
        self.langue = langue
        self.lignes: list[tuple[str, str, str]] = []
        #: Index des lignes dont le NOT TESTED est CONTINGENT -- celles qui
        #: deviendraient PASS si l appelant fournissait ce qui manque. On
        #: retient l index et non l intitule : plusieurs intitules sont
        #: construits, donc un ensemble de noms serait fragile.
        self.requis: list[int] = []

    def dire(self, etat: str, controle: str, detail: str = "",
             requis: bool = False) -> None:
        """Inscrit une ligne. `requis` ne change NI l etat NI l affichage.

        Il ne sert qu au code de sortie en mode strict : marquer une ligne
        requise dit que son `NOT TESTED` serait evitable si l appelant
        fournissait ce qui manque.
        """
        if requis:
            self.requis.append(len(self.lignes))
        self.lignes.append((etat, controle, detail))
        # L etat n est JAMAIS traduit : `PASS`, `FAIL` et `NOT TESTED` sont
        # des termes du contrat. Seules la prose de l intitule et celle du
        # detail changent de langue.
        vu = i18n.traduire(controle, self.langue)
        vu_detail = i18n.traduire(detail, self.langue)
        print("[%-10s] %s%s" % (etat, vu, " - " + vu_detail if vu_detail else ""))

    def requises_non_demontrees(self) -> list[str]:
        """Les garanties requises qui ne sont pas `PASS`."""
        return [self.lignes[i][1] for i in self.requis if self.lignes[i][0] != PASS]

    def compte(self, etat: str) -> int:
        return sum(1 for ligne in self.lignes if ligne[0] == etat)

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


class EntreeIllisible(Exception):
    """Une entree de l archive n a pas la forme attendue.

    Un verificateur ne plante pas : il rend un verdict. Toute lecture
    structuree leve cette exception plutot qu une exception de la
    bibliotheque standard, et l appelant la convertit en FAIL motive.
    """


def texte(archive: zipfile.ZipFile, nom: str, encodage: str = "utf-8") -> str:
    """Decode un membre, ou dit pourquoi il n est pas decodable."""
    octets = archive.read(nom)
    try:
        return octets.decode(encodage)
    except UnicodeDecodeError as erreur:
        raise EntreeIllisible(
            "%s n est pas decodable en %s : %s" % (nom, encodage, erreur)
        ) from erreur


def objet_json(octets: bytes, quoi: str) -> dict[str, object]:
    """Un objet JSON, ou la raison pour laquelle ce n en est pas un."""
    try:
        valeur = json.loads(octets)
    except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
        raise EntreeIllisible("%s n est pas du JSON lisible : %s" % (quoi, erreur)) from erreur
    if not isinstance(valeur, dict):
        raise EntreeIllisible(
            "%s devrait etre un objet JSON ; recu %s" % (quoi, type(valeur).__name__)
        )
    return valeur


def lignes_jsonl(octets: bytes, quoi: str = "un membre JSONL") -> list[dict[str, object]]:
    """Les objets d un JSONL, ou la premiere ligne qui n en est pas un.

    Le numero de ligne est celui du fichier, lignes vides comprises : c est
    celui qu un lecteur verra dans son editeur.
    """
    enregistrements = []
    for numero, ligne in enumerate(octets.splitlines(), start=1):
        if not ligne.strip():
            continue
        try:
            valeur = json.loads(ligne)
        except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
            raise EntreeIllisible(
                "%s, ligne %d : JSON illisible (%s)" % (quoi, numero, erreur)
            ) from erreur
        if not isinstance(valeur, dict):
            raise EntreeIllisible(
                "%s, ligne %d : attendu un objet, recu %s"
                % (quoi, numero, type(valeur).__name__)
            )
        enregistrements.append(valeur)
    return enregistrements


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
    # A-04 de l audit du 5 novembre : la forme du manifeste etait non verifiee.
    # Un `decomptes` au mauvais type faisait echouer un controle ULTERIEUR par
    # accident, et le lecteur du rapport l imputait a la preuve plutot qu au
    # document. Aucune ligne PASS n est ajoutee ici : les decomptes publies de
    # 21 et 18 lignes sont cites par des documents figes.
    malformes = []
    # `fichiers` est une LISTE de noms dans les deux schemas, pas une table :
    # l avoir suppose dict faisait echouer les deux archives valides.
    for cle, type_attendu in (("decomptes", dict), ("fichiers", list), ("absences", dict)):
        valeur = manifeste.get(cle)
        if valeur is not None and not isinstance(valeur, type_attendu):
            malformes.append(
                "%s : attendu %s, recu %s" % (cle, type_attendu.__name__, type(valeur).__name__)
            )
    decomptes = manifeste.get("decomptes")
    if isinstance(decomptes, dict):
        malformes += [
            "decomptes.%s : attendu un entier, recu %s" % (c, type(v).__name__)
            for c, v in sorted(decomptes.items())
            if not isinstance(v, int) or isinstance(v, bool)
        ]
    if malformes:
        bilan.dire(FAIL, "forme du manifeste", "; ".join(malformes[:5]))

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
    lignes = texte(archive, "checksums.sha256").splitlines()
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
    observations = lignes_jsonl(archive.read("observations.jsonl"), "observations.jsonl")
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
        enregistrements = lignes_jsonl(archive.read(membre), membre)
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
        charge(e).get("observation_id")
        for e in lignes_jsonl(archive.read("observations.jsonl"), "observations.jsonl")
    }
    ecarts = []
    for membre, cle in (
        ("measurements.jsonl", "observations_sans_mesure"),
        ("reference_evaluations.jsonl", "observations_sans_evaluation"),
    ):
        if membre not in noms:
            continue
        couverts = {
            charge(e).get("observation_id") for e in lignes_jsonl(archive.read(membre), membre)
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
    mesures = lignes_jsonl(archive.read("measurements.jsonl"), "measurements.jsonl")
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
    rapport = texte(archive, "rapport.md")
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
        contenu = archive.read(nom).decode("utf-8", "replace")
        for etiquette, motifs in MOTIFS_INTERDITS:
            for motif in motifs:
                if motif in contenu:
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
    contenu = texte(archive, "observations.csv", "utf-8-sig")
    suspectes = []
    for numero, ligne in enumerate(contenu.splitlines()):
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
    provenances = [
        charge(e)
        for e in lignes_jsonl(archive.read("replay_provenance.jsonl"), "replay_provenance.jsonl")
    ]
    if not provenances:
        bilan.dire(
            NOT_TESTED, "empreintes des entrees rejouees", "aucun enregistrement de provenance"
        )
        return
    if corpus is None:
        # La SEULE ligne contingente de cet outil : l appelant peut la faire
        # passer en fournissant `--corpus`. Les autres NOT TESTED d ici sont
        # des limites PERMANENTES -- chainage du registre, origine de
        # l archive, membre absent -- et les exiger rendrait le mode strict
        # toujours rouge, donc inutile.
        bilan.dire(
            NOT_TESTED,
            "empreintes des entrees rejouees (%d a verifier)" % len(provenances),
            "le corpus d entree n est pas dans l archive. Le fournir avec --corpus "
            "<repertoire> pour que ce controle soit fait.",
            requis=True,
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
    m = objet_json(manifeste_corpus.read_bytes(), "le manifeste du corpus")
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
    # R-8 : `sorted(map(str, ...))` imprimait un conteneur Python -- << L
    # archive declare ['True'] >>. Un auditeur ne peut rien en faire, et la
    # ligne se lit comme un defaut de l outil. On dit la valeur.
    etats = [r.get("chaine_verifiee", r.get("chaine_verifiee_par_cet_outil"))
             for r in declares]
    if all(e is True for e in etats):
        dit = "chaine verifiee par son instrument"
    elif all(e is False for e in etats):
        dit = "chaine NON verifiee par son instrument"
    elif all(e is None for e in etats):
        dit = "rien sur la verification de sa chaine"
    else:
        dit = "des etats differents selon le registre (%s)" % ", ".join(
            "verifiee" if e is True else ("non verifiee" if e is False else "non dit")
            for e in etats)
    bilan.dire(
        NOT_TESTED,
        "chainage JCS de %d registre(s) d origine" % len(declares),
        "hors de portee : le recalculer ici serait une seconde implementation du "
        "registre. L archive declare %s, et les empreintes de tete %s. A confronter "
        "avec : station ledger verify --path <registre>" % (dit, tetes),
    )


def controle_completude(
    bilan: Bilan, archive: zipfile.ZipFile, noms: list[str], manifeste: dict[str, object]
) -> None:
    """L archive dit-elle ce que son registre portait, et ce qu elle n exporte pas ?

    C est la question que l integrite ne pose pas. Une archive peut etre
    parfaitement coherente avec elle-meme et ne livrer qu une PARTIE de son
    registre -- l evaluation ODA3 du 6 novembre a mesure 151 enregistrements
    de 6 types au registre pour 120 de 4 types a l export, et un manifeste
    annoncant 151. Les 31 retenus n etaient nommes nulle part.

    Le contrat verifie ici :

        enregistrements = enregistrements_exportes + somme(types_exclus)
        enregistrements_exportes = somme(decomptes des membres exportes)

    Une archive qui ne declare pas ce contrat rend `NOT TESTED`. Elle n est
    pas fautive -- le contrat est neuf -- mais sa completude n est pas
    etablie, et le dire est tout l objet de cette ligne.
    """
    registre = manifeste.get("registre")
    registre = registre if isinstance(registre, dict) else {}
    total = registre.get("enregistrements")
    exportes = registre.get("enregistrements_exportes")
    exclus = registre.get("types_exclus")
    exclus = exclus if isinstance(exclus, dict) else None

    if not isinstance(exportes, int) or exclus is None:
        bilan.dire(
            NOT_TESTED,
            "completude de l export",
            "l archive ne declare pas de contrat de completude : il lui manque "
            "`registre.enregistrements_exportes` et `registre.types_exclus`. Son "
            "integrite interne peut etre entiere et son export partiel -- une chaine "
            "valide ne dit rien de ce qui n a pas ete exporte. Non marque requis : "
            "c est au PRODUCTEUR de l archive de declarer ce contrat, pas a "
            "l appelant de le fournir.",
        )
        return

    # Les decomptes des membres effectivement livres.
    decomptes = manifeste.get("decomptes")
    decomptes = decomptes if isinstance(decomptes, dict) else {}
    livres = {
        "observations.jsonl": decomptes.get("observations"),
        "measurements.jsonl": decomptes.get("mesures"),
        "reference_evaluations.jsonl": decomptes.get("evaluations"),
        "replay_provenance.jsonl": decomptes.get("provenances_de_rejeu"),
    }
    somme_livres = sum(v for nom, v in livres.items()
                       if nom in noms and isinstance(v, int))
    somme_exclus = sum(v for v in exclus.values() if isinstance(v, int))

    ecarts = []
    if isinstance(total, int) and total != exportes + somme_exclus:
        ecarts.append(
            "le registre annonce %d enregistrement(s), or %d exporte(s) + %d retenu(s) "
            "font %d" % (total, exportes, somme_exclus, exportes + somme_exclus))
    if exportes != somme_livres:
        ecarts.append(
            "le contrat annonce %d enregistrement(s) exporte(s), les decomptes des "
            "membres en totalisent %d" % (exportes, somme_livres))

    if ecarts:
        bilan.dire(FAIL, "completude de l export", " ; ".join(ecarts))
        return

    nommes = ", ".join("%s (%d)" % (t, n) for t, n in sorted(exclus.items())) or "aucun"
    bilan.dire(
        PASS,
        "completude de l export",
        "%d enregistrement(s) au registre, %d exporte(s), %d retenu(s) : %s. Les "
        "decomptes s additionnent. Ce qui est retenu est NOMME, donc l absence est "
        "une exclusion declaree et non un manque silencieux."
        % (total if isinstance(total, int) else exportes + somme_exclus,
           exportes, somme_exclus, nommes),
    )


def controle_origine(bilan: Bilan) -> None:
    bilan.dire(
        NOT_TESTED,
        "origine et horodatage de l archive",
        "hors de portee de toute verification locale : aucune signature tierce, aucun "
        "ancrage exterieur. `recorded_at` est declare par l appelant.",
    )


def execute(bilan: Bilan, intitule: str, controle, *arguments: object) -> object:
    """Lance un controle en l isolant de ses voisins.

    Un controle qui ne peut pas lire son entree rend un FAIL motive, et les
    autres controles continuent. Sans cela, un seul membre malforme empeche
    l outil de rendre le moindre verdict -- et son code de sortie 1 devient
    indistinguable d un FAIL legitime.

    `Exception` est rattrapee largement et volontairement : tout defaut
    imprevu de l outil doit sortir comme un FAIL nomme, jamais comme une
    trace d appels. Le type de l exception est dit, pour que le defaut reste
    diagnosticable.
    """
    try:
        return controle(bilan, *arguments)
    except EntreeIllisible as erreur:
        bilan.dire(FAIL, intitule, str(erreur))
    except Exception as erreur:  # noqa: BLE001 - voir la docstring
        bilan.dire(
            FAIL,
            intitule,
            "controle interrompu par un defaut de l outil : %s: %s"
            % (type(erreur).__name__, erreur),
        )
    return None


def deroule(bilan: Bilan, arguments: argparse.Namespace) -> None:
    """La sequence de controles. Peut rendre la main a tout moment.

    Elle n imprime jamais le bilan : c est `main` qui le fait, sur tous les
    chemins. Un `return` ici veut dire << impossible d aller plus loin >>,
    pas << pas de verdict >>.
    """
    if not arguments.archive.is_file():
        bilan.dire(FAIL, "archive lisible", "%s introuvable" % arguments.archive)
        return

    _dis(bilan.langue, "Dossier de preuve : %s", arguments.archive)
    _dis(bilan.langue, "empreinte de l archive : %s",
         sha256_fichier(arguments.archive))
    print()

    try:
        archive = zipfile.ZipFile(arguments.archive)
    except zipfile.BadZipFile as erreur:
        bilan.dire(FAIL, "archive lisible", str(erreur))
        return

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
            return
        bilan.dire(PASS, "aucun membre ne sort du repertoire cible")

        if archive.testzip() is not None:
            bilan.dire(FAIL, "integrite interne du ZIP", "un membre est corrompu")
            return
        bilan.dire(PASS, "integrite interne du ZIP")

        noms = archive.namelist()
        if "manifest.json" not in noms:
            bilan.dire(FAIL, "manifest.json present", "sans manifeste, rien n est verifiable")
            return
        try:
            manifeste = objet_json(archive.read("manifest.json"), "manifest.json")
        except EntreeIllisible as erreur:
            # Le manifeste conditionne tous les autres controles : lui seul
            # interrompt la sequence, et il le dit.
            bilan.dire(FAIL, "manifest.json lisible", str(erreur))
            return
        # Aucune ligne PASS ici, volontairement : un manifeste lisible est la
        # premisse des controles qui suivent, pas un controle de plus. En
        # ajouter une decalerait les decomptes publies (21 lignes sur
        # GROUNDED-S1, 18 sur MED) que des documents figes citent.

        if execute(bilan, "schema d'export reconnu", controle_schema, manifeste, noms) is None:
            return
        execute(bilan, "empreintes des membres", controle_checksums, archive, noms)
        execute(bilan, "cardinalites", controle_cardinalites, archive, noms, manifeste)
        execute(bilan, "absences declarees", controle_absences, archive, noms, manifeste)
        execute(bilan, "coherence des signaux nuls", controle_nulls, archive, noms)
        execute(bilan, "garde de regime", controle_regime, archive, manifeste)
        execute(bilan, "neutralisation des formules CSV", controle_csv, archive, noms)
        execute(bilan, "absence de secrets et de chemins", controle_confidentialite, archive, noms)
        execute(bilan, "empreintes des entrees", controle_entrees, archive, noms, arguments.corpus)
        execute(bilan, "completude de l export", controle_completude,
                archive, noms, manifeste)
        execute(bilan, "chainage du registre", controle_chaine, manifeste)
        execute(bilan, "origine de l archive", controle_origine)


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Verifie un dossier de preuve NeoMundi Evidence, sans aucune dependance."
    )
    analyseur.add_argument("archive", type=Path, help="l archive ZIP a verifier")
    analyseur.add_argument(
        "--lang",
        choices=("fr", "en"),
        default="fr",
        help="langue de la PROSE. Ne change aucun verdict, aucun code de "
             "sortie, aucun nom de champ et aucune empreinte.",
    )
    analyseur.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="repertoire du corpus d entree, pour verifier les empreintes des entrees rejouees",
    )
    analyseur.add_argument(
        "--json",
        type=Path,
        default=None,
        metavar="FICHIER",
        help="ecrire aussi un rapport lisible par machine. La sortie texte reste "
        "identique : ce fichier s ajoute, il ne remplace rien.",
    )
    analyseur.add_argument(
        "--strict",
        action="store_true",
        help="sortir en code 2 si une garantie REQUISE n est pas demontree. Ici une "
        "seule l est : les empreintes des entrees rejouees, qui exigent --corpus. "
        "Ne change AUCUN verdict.",
    )
    arguments = analyseur.parse_args()

    bilan = Bilan(arguments.lang)

    deroule(bilan, arguments)

    # Un seul point de sortie : le bilan est rendu meme quand la sequence
    # s est arretee tot. Sans cela, un code de sortie 1 sans ligne BILAN est
    # indistinguable d un plantage de l outil.
    print()
    _dis(bilan.langue, "BILAN : %d PASS, %d FAIL, %d NOT TESTED",
         bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED))
    if bilan.compte(FAIL):
        _dis(bilan.langue, "Ce dossier ne doit pas etre presente comme verifie.")

    manquantes = bilan.requises_non_demontrees()
    if arguments.strict:
        if manquantes:
            print()
            _dis(bilan.langue,
                 "MODE STRICT : %d garantie(s) requise(s) non demontree(s) :",
                 len(manquantes))
            for m in manquantes:
                # `manquantes` porte les intitules FRANCAIS, parce que
                # `self.lignes` les stocke ainsi. Ils se traduisent ici,
                # comme a l impression d une ligne de controle.
                print("  - %s" % i18n.traduire(m, bilan.langue))
            _dis(bilan.langue,
                 "Aucun verdict n a change : seul le code de sortie en tient compte (2).")
        else:
            print()
            _dis(bilan.langue,
                 "MODE STRICT : toutes les garanties requises sont demontrees.")

    if arguments.json:
        # Les trois etats restent trois champs distincts : un consommateur qui
        # ne lirait que `pass` et `fail` croirait a une couverture complete.
        rapport = {
            "schema": "neomundi.evidence.verification-report/1",
            "archive": str(arguments.archive),
            "archive_sha256": (
                sha256_fichier(arguments.archive) if arguments.archive.is_file() else None
            ),
            "corpus": str(arguments.corpus) if arguments.corpus else None,
            "controls": [
                {"state": etat, "control": intitule, "detail": detail}
                for etat, intitule, detail in bilan.lignes
            ],
            "counts": {
                "pass": bilan.compte(PASS),
                "fail": bilan.compte(FAIL),
                "not_tested": bilan.compte(NOT_TESTED),
            },
            "verdict": "fail" if bilan.compte(FAIL) else "no_failure",
            "strict": bool(arguments.strict),
            "required_not_demonstrated": manquantes,
            "exit_code": bilan.code_de_sortie(arguments.strict),
            "does_not_establish": [
                "authenticity: no signature is verified by this tool",
                "origin: no trusted clock, no external anchor",
                "that the execution took place",
            ],
        }
        arguments.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _dis(bilan.langue, "rapport lisible par machine : %s", arguments.json)

    return bilan.code_de_sortie(arguments.strict)


if __name__ == "__main__":
    sys.exit(main())

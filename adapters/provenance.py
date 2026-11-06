# -*- coding: utf-8 -*-
"""Lit la provenance instrumentale d un export Station. N INTERPRETE RIEN.

    python adapters/provenance.py <export.zip> \\
        [--out rapport.json] [--md rapport.md] [--strict] [--lang fr|en]

LA CHAINE QUE CE PROGRAMME PARCOURT

    Execution -> Mesure -> Evaluateur -> Configuration -> Export -> Preuve

et il dit, a CHAQUE maillon, ce qui est controle et ce qui ne l est pas.

POURQUOI IL EXISTE

R-6. L API de mesure sert, par signal, l evaluateur, le modele utilise, le
statut, le motif et des empreintes de configuration. Station modelise leur
conservation -- `MeasurementCoverage`, avec sa barriere anti-secret -- et le
transport s arrete la : un export `station.export.campagne/2` porte huit
membres et aucun ne contient cette provenance.

Donc, sur une archive `/2`, **toute affirmation sur l instrument de mesure est
`not_demonstrable`**, et ce programme le dit plutot que de le taire. Sur une
archive `/3`, il lit le membre de couverture et rapporte ce qu il y trouve --
sans jamais le prendre pour une verification.

LES TROIS REGISTRES, COMME EN B-3

  CONTROLE         recalcule ou confronte par nous : empreintes, structure,
                   resolution des identifiants, arithmetique des decomptes ;
  DECLARE          la parole de l export, conservee VERBATIM : identifiants
                   de modele, versions, horodatages ;
  NON DEMONTRABLE  aucun controle sur une archive ne pourrait l etablir.

Le vocabulaire est celui d `adapters/ingest.py` a dessein : le rapport se
branche dans la chaine B-3 sans traduction.

CE QU IL NE FAIT PAS

Il ne recalcule pas les signaux, ne corrige aucune valeur, ne complete aucun
champ absent, et n a besoin d AUCUNE cle privee. La structure et les
empreintes des membres ne sont pas re-verifiees ici : `verify.py` est appele,
et son verdict rapporte tel quel. Un seul verificateur d archive existe.

Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
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


SCHEMA_RAPPORT = "neomundi.evidence.provenance-report/1"
MEMBRE_COUVERTURE = "measurement_coverage.jsonl"

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"
CONTROLE, DECLARE, INDEMONTRABLE = "CONTROLE", "DECLARE", "NON DEMONTRABLE"

#: Les niveaux de provenance instrumentale. Il n en existe pas de quatrieme :
#: `instrument_verifie` serait une pretention qu aucune archive ne peut
#: soutenir, et l absence de ce niveau est le coeur de ce module.
NIVEAUX = ("instrument_non_documente", "instrument_declare",
           "instrument_declare_et_configure")

#: Les champs de provenance que l API sert par signal. On ne les INVENTE pas :
#: on constate lesquels sont la, et on nomme les absents.
CHAMPS_EVALUATEUR = ("evaluator", "model_used", "status", "reason",
                     "model_configured", "served_by", "attempts",
                     "latency_ms", "evaluator_runtime",
                     "prompt_template_hash", "inference_config_hash",
                     "config_fingerprint")
#: Ceux qui, seuls, permettent de dire qu une configuration est documentee.
CHAMPS_CONFIGURATION = ("evaluator_runtime", "prompt_template_hash",
                        "inference_config_hash", "config_fingerprint")

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
    def __init__(self) -> None:
        self.lignes: list[dict] = []

    def dire(self, etat: str, nature: str, intitule: str, detail: str = "",
             requis: bool = False) -> None:
        self.lignes.append({"etat": etat, "nature": nature,
                            "intitule": intitule, "detail": detail,
                            "requis": requis})
        print("[%-10s] [%-15s] %s%s"
              % (etat, nature, i18n.traduire(intitule, _LANGUE[0]),
                 " - " + i18n.traduire(detail, _LANGUE[0]) if detail else ""))

    def compte(self, etat: str) -> int:
        return sum(1 for l in self.lignes if l["etat"] == etat)

    def requis_non_demontres(self) -> list[str]:
        return [l["intitule"] for l in self.lignes
                if l["requis"] and l["etat"] != PASS]


def lignes_jsonl(z: zipfile.ZipFile, nom: str) -> list[dict]:
    if nom not in z.namelist():
        return []
    out = []
    for brute in z.read(nom).splitlines():
        if brute.strip():
            try:
                out.append(json.loads(brute))
            except ValueError:
                continue
    return out


def charge(enr: dict) -> dict:
    """La charge utile d un enregistrement de registre, ou l objet lui-meme."""
    p = enr.get("payload")
    return p if isinstance(p, dict) else enr


# --------------------------------------------------------------------------
# Les maillons, dans l ordre de la chaine.
# --------------------------------------------------------------------------

def maillon_export(z: zipfile.ZipFile, bilan: Bilan) -> dict:
    """Export : le contrat, sa version, son empreinte."""
    if "manifest.json" not in z.namelist():
        bilan.dire(FAIL, CONTROLE, "contrat d export",
                   "`manifest.json` absent : ce n est pas un export Station")
        return {}
    octets = z.read("manifest.json")
    m = json.loads(octets)
    schema = m.get("schema")
    porte = MEMBRE_COUVERTURE in z.namelist()
    bilan.dire(PASS if schema else FAIL, CONTROLE, "contrat d export",
               "%s ; membre de couverture %s"
               % (schema, "PRESENT" if porte else "absent"))
    bilan.dire(PASS, CONTROLE, "empreinte du contrat d export",
               "manifest.json se hache sur %s ; campaign_sha256 declare %s"
               % (hashlib.sha256(octets).hexdigest()[:16],
                  str(m.get("campaign_sha256"))[:16] or "absent"))
    return m


def maillon_structure(archive: Path, bilan: Bilan) -> dict:
    """Structure et empreintes : DELEGUEES a `verify.py`, pas refaites."""
    fini = subprocess.run(
        [sys.executable, str(RACINE / "verify.py"), str(archive)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    sortie = (fini.stdout or "") + (fini.stderr or "")
    resume = next((l for l in sortie.splitlines() if l.startswith("BILAN")), "")
    bilan.dire(PASS if fini.returncode == 0 else FAIL, CONTROLE,
               "structure et empreintes des membres",
               "verify.py -> exit %d  %s" % (fini.returncode, resume))
    return {"exit": fini.returncode, "bilan": resume}


def maillon_execution(z: zipfile.ZipFile, bilan: Bilan) -> dict:
    """Execution : les observations, et ce qu elles disent du modele."""
    obs = [charge(o) for o in lignes_jsonl(z, "observations.jsonl")]
    if not obs:
        bilan.dire(NOT_TESTED, CONTROLE, "chaine vers l execution",
                   "aucune observation dans l export", requis=True)
        return {"observations": 0}

    demandes = {o.get("model_requested") for o in obs if o.get("model_requested")}
    servis = {o.get("model_served") for o in obs if o.get("model_served")}
    atteste = sum(1 for o in obs if o.get("model_served_attestation"))
    bilan.dire(NOT_TESTED, DECLARE, "identite du modele observe",
               "demande %s ; servi %s ; %d/%d portent une attestation de "
               "modele servi. Declares par l export."
               % (sorted(demandes) or "absent", sorted(servis) or "absent",
                  atteste, len(obs)))
    if demandes and servis and demandes != servis:
        bilan.dire(NOT_TESTED, DECLARE, "modele demande et modele servi",
                   "ILS DIFFERENT. Un `model_requested` peut etre un alias : "
                   "ne pas lire l un pour l autre.")

    # Entrees et sorties : des empreintes, et non les octets. C est une
    # propriete de l export, pas un defaut -- mais elle borne ce qu un tiers
    # peut refaire.
    champs = ("prompt_sha256", "request_sha256", "response_sha256")
    presents = {c: sum(1 for o in obs if o.get(c)) for c in champs}
    bilan.dire(PASS if all(presents[c] == len(obs) for c in champs)
               else NOT_TESTED, CONTROLE,
               "provenance des entrees et sorties",
               "sur %d observation(s) : %s" % (len(obs), presents))
    bilan.dire(NOT_TESTED, INDEMONTRABLE, "empreintes des artefacts sources",
               "l export porte des EMPREINTES d entrees et de sorties, pas "
               "leurs octets. Un tiers ne peut donc pas les recalculer : il "
               "peut seulement confronter une empreinte a un artefact qu il "
               "detient deja.")
    return {"observations": len(obs),
            "model_requested": sorted(demandes), "model_served": sorted(servis),
            "attestations_de_modele": atteste}


def maillon_mesure(z: zipfile.ZipFile, obs_ids: set[str], bilan: Bilan) -> dict:
    """Mesure : la resolution des identifiants, et la couverture declaree."""
    mes = [charge(m) for m in lignes_jsonl(z, "measurements.jsonl")]
    if not mes:
        bilan.dire(NOT_TESTED, CONTROLE, "chaine vers la mesure",
                   "aucune mesure dans l export", requis=True)
        return {"mesures": 0}

    resolus = sum(1 for m in mes if m.get("observation_id") in obs_ids)
    orphelins = [m.get("measurement_id") for m in mes
                 if m.get("observation_id") not in obs_ids]
    bilan.dire(PASS if not orphelins else FAIL, CONTROLE,
               "chaine execution -> mesure",
               "%d/%d mesure(s) resolvent leur `observation_id` vers une "
               "observation de cet export%s"
               % (resolus, len(mes),
                  "" if not orphelins else " ; orphelines : %s" % orphelins[:4]))

    versions = sorted({m.get("measurement_version") for m in mes if m.get("measurement_version")})
    bilan.dire(PASS if len(versions) == 1 else NOT_TESTED, CONTROLE,
               "version de mesure",
               "%s. %s" % (versions or "absente",
                           "uniforme sur tout l export" if len(versions) == 1
                           else "NON uniforme : les lignes ne sont pas "
                                "comparables entre elles sans le dire"))

    # Couverture : on confronte ce que l export dit de lui-meme. On ne deduit
    # RIEN de `checks_emitted` : l audit T1.1 a etabli que ce nombre et les
    # `checks_succeeded` de l API comptent des choses differentes.
    incoherentes = []
    for m in mes:
        sig = m.get("signals") or {}
        mesures = [k for k, v in sig.items() if v is not None]
        declares = m.get("measured_signals") or []
        if sorted(mesures) != sorted(declares):
            incoherentes.append(m.get("measurement_id"))
    bilan.dire(PASS if not incoherentes else FAIL, CONTROLE,
               "couverture des controles",
               "`measured_signals` concorde avec les signaux non nuls sur "
               "%d/%d mesure(s)%s"
               % (len(mes) - len(incoherentes), len(mes),
                  "" if not incoherentes else " ; ecarts : %s" % incoherentes[:4]))

    # Un signal non mesure doit dire POURQUOI. Un `null` sans motif est
    # exactement l ambiguite que la couverture existe pour lever.
    sans_motif = []
    for m in mes:
        sig = m.get("signals") or {}
        nuls = [k for k, v in sig.items() if v is None]
        if nuls and not m.get("reason"):
            sans_motif.append(m.get("measurement_id"))
    total_nuls = sum(1 for m in mes for v in (m.get("signals") or {}).values()
                     if v is None)
    bilan.dire(PASS if not sans_motif else NOT_TESTED, CONTROLE,
               "signaux non mesures et leur motif",
               "%d signal(aux) nul(s) ; %d mesure(s) en portent sans motif%s"
               % (total_nuls, len(sans_motif),
                  "" if not sans_motif else " : %s" % sans_motif[:4]))

    horo = sum(1 for m in mes if m.get("measured_at"))
    bilan.dire(NOT_TESTED, DECLARE, "horodatage et son origine",
               "%d/%d mesure(s) portent `measured_at`, declare par Station. "
               "Aucune horloge de confiance n intervient, et l export porte "
               "trois instants voisins -- envoi, reception, mesure -- qui "
               "disent trois choses differentes." % (horo, len(mes)))
    return {"mesures": len(mes), "versions": versions,
            "orphelines": orphelins, "signaux_nuls": total_nuls}


def maillon_evaluateur(z: zipfile.ZipFile, mes_ids: set[str],
                       bilan: Bilan) -> dict:
    """Evaluateur et configuration : le coeur de R-6."""
    if MEMBRE_COUVERTURE not in z.namelist():
        bilan.dire(NOT_TESTED, INDEMONTRABLE, "identite des evaluateurs",
                   "cet export ne porte pas `%s`. L API sert cette "
                   "provenance, Station en modelise la conservation, et le "
                   "transport s arrete avant l export. Toute affirmation sur "
                   "l instrument de mesure est donc `not_demonstrable` -- et "
                   "non `declared`, puisque rien ne la declare."
                   % MEMBRE_COUVERTURE, requis=True)
        bilan.dire(NOT_TESTED, INDEMONTRABLE, "configuration des evaluateurs",
                   "sans membre de couverture, il n y a aucune configuration "
                   "a lire.")
        return {"niveau": "instrument_non_documente", "couvertures": 0}

    cov = [charge(c) for c in lignes_jsonl(z, MEMBRE_COUVERTURE)]
    if not cov:
        bilan.dire(FAIL, CONTROLE, "identite des evaluateurs",
                   "`%s` present et VIDE. Un membre vide n est pas une "
                   "absence de provenance : c est un export qui se contredit."
                   % MEMBRE_COUVERTURE)
        return {"niveau": "instrument_non_documente", "couvertures": 0}

    rattachees = sum(1 for c in cov if c.get("measurement_id") in mes_ids)
    orphelines = [c.get("coverage_id") for c in cov
                  if c.get("measurement_id") not in mes_ids]
    bilan.dire(PASS if not orphelines else FAIL, CONTROLE,
               "chaine mesure -> couverture",
               "%d/%d couverture(s) resolvent leur `measurement_id`%s"
               % (rattachees, len(cov),
                  "" if not orphelines else " ; orphelines : %s" % orphelines[:4]))

    # Quels signaux portent un evaluateur, et quels champs ?
    par_signal: dict[str, set[str]] = {}
    sans_evaluateurs = 0
    for c in cov:
        ev = c.get("evaluators")
        if not isinstance(ev, dict) or not ev:
            sans_evaluateurs += 1
            continue
        for signal, detail in ev.items():
            if isinstance(detail, dict):
                # Seules les clefs dont la valeur n est PAS nulle comptent.
                #
                # `set.update(detail)` versait les clefs d un dictionnaire
                # sans regarder leurs valeurs : quatre champs de
                # configuration a `null` suffisaient a faire declarer un
                # instrument << configure >>. Defaut constate le 6 novembre
                # par le controle adversarial E de Q-1.
                #
                # C est le SYMETRIQUE du defaut corrige plus bas : meme
                # distinction, sens inverse. Un nul n est pas une valeur ; et
                # une clef absente n est pas un trou quand le signal n a rien
                # a documenter. Le signal reste NOMME dans les deux cas --
                # `setdefault` cree l entree meme si l ensemble reste vide.
                par_signal.setdefault(signal, set()).update(
                    nom for nom, valeur in detail.items() if valeur is not None
                )

    if not par_signal:
        bilan.dire(NOT_TESTED, INDEMONTRABLE, "identite des evaluateurs",
                   "%d couverture(s), et aucune ne porte `evaluators`. L API "
                   "d une version anterieure ne le sert pas, et un tel "
                   "silence ne peut pas affirmer que tout s est bien passe."
                   % len(cov), requis=True)
        return {"niveau": "instrument_non_documente", "couvertures": len(cov)}

    nommes = sorted(par_signal)
    bilan.dire(NOT_TESTED, DECLARE, "identite des evaluateurs",
               "%d signal(aux) nomment leur evaluateur : %s. DECLARE par "
               "l API, conserve verbatim." % (len(nommes), ", ".join(nommes)))

    # Un signal qui porte une VALEUR et qu `evaluators` ne nomme pas.
    #
    # Le membre de couverture existe et documente d autres signaux : ce n est
    # donc pas le silence d une API anterieure -- traite plus haut, en
    # NOT TESTED -- mais un export qui publie un resultat sans dire avec quoi
    # il a ete obtenu. Les deux situations se ressemblent et ne se valent
    # pas, et c est pourquoi ce controle est place APRES le retour du cas
    # << aucun evaluateur >>.
    #
    # Defaut constate le 6 novembre par le controle adversarial D de Q-1 :
    # retirer une entree ne faisait tomber aucun controle et le niveau
    # restait le plus haut. Supprimer une entree genante ELEVAIT donc la
    # completude apparente.
    sans_instrument = sorted({
        signal
        for m in (charge(x) for x in lignes_jsonl(z, "measurements.jsonl"))
        for signal, valeur in (m.get("signals") or {}).items()
        if valeur is not None and signal not in par_signal
    })
    bilan.dire(PASS if not sans_instrument else FAIL, CONTROLE,
               "chaque signal mesure nomme son instrument",
               "tous les signaux portant une valeur sont nommes par "
               "`evaluators`" if not sans_instrument else
               "%d signal(aux) publient une valeur sans entree d evaluateur : "
               "%s. Le membre de couverture en documente pourtant d autres : "
               "l export se contredit."
               % (len(sans_instrument), ", ".join(sans_instrument)))

    # Deux signaux peuvent partager un meme appel. Le dire, sinon un lecteur
    # compte deux instruments independants la ou il n y en a qu un.
    identites: dict[str, list[str]] = {}
    for c in cov:
        ev = c.get("evaluators") or {}
        for signal, detail in ev.items():
            if isinstance(detail, dict) and detail.get("evaluator"):
                identites.setdefault(detail["evaluator"], [])
                if signal not in identites[detail["evaluator"]]:
                    identites[detail["evaluator"]].append(signal)
    partages = evaluateurs_partages(identites)
    if partages:
        bilan.dire(NOT_TESTED, DECLARE, "evaluateurs partages entre signaux",
                   "un meme evaluateur sert plusieurs signaux : %s. Ce ne "
                   "sont pas des instruments independants."
                   % "; ".join("%s -> %s" % (k, ", ".join(v))
                               for k, v in partages.items()))

    # Configuration : documentee ou non, par signal, sans moyenne.
    #
    # Un signal dont AUCUNE couverture ne declare de modele est un calcul
    # LOCAL : il n a ni moteur ni prompt, et ses champs de configuration
    # absents sont CORRECTS. Le compter comme non configure plafonnait le
    # niveau d un export pourtant complet -- defaut constate le 6 novembre
    # sur un export Station reel, ou `stability_score` suffisait a faire
    # retomber un `/3` documente en `instrument_declare`.
    avec_modele: set[str] = set()
    for c in cov:
        for signal, detail in (c.get("evaluators") or {}).items():
            if isinstance(detail, dict) and (detail.get("model_used")
                                             or detail.get("model_configured")):
                avec_modele.add(signal)
    configures, nus, locaux = [], [], []
    for signal, champs in par_signal.items():
        if signal not in avec_modele:
            locaux.append(signal)
        elif set(CHAMPS_CONFIGURATION) & champs:
            configures.append(signal)
        else:
            nus.append(signal)
    bilan.dire(NOT_TESTED, DECLARE, "configuration des evaluateurs",
               "documentee pour %s ; declarant un modele SANS configuration : "
               "%s ; calcul(s) local(aux), sans modele ni prompt, dont les "
               "nuls sont CORRECTS : %s."
               % (", ".join(sorted(configures)) or "aucun",
                  ", ".join(sorted(nus)) or "aucun",
                  ", ".join(sorted(locaux)) or "aucun"))

    # Statut d execution par evaluateur : present ou absent, jamais devine.
    statuts: dict[str, int] = {}
    sans_statut = 0
    for c in cov:
        for detail in (c.get("evaluators") or {}).values():
            if isinstance(detail, dict):
                s = detail.get("status")
                if s:
                    statuts[s] = statuts.get(s, 0) + 1
                else:
                    sans_statut += 1
    bilan.dire(PASS if statuts and not sans_statut else NOT_TESTED, CONTROLE,
               "statut d execution par evaluateur",
               "statuts rencontres : %s ; %d entree(s) sans statut"
               % (statuts or "aucun", sans_statut))

    if sans_evaluateurs:
        bilan.dire(NOT_TESTED, CONTROLE, "couvertures sans evaluateurs",
                   "%d/%d couverture(s) ne portent aucun `evaluators`. Leur "
                   "silence n est pas un succes." % (sans_evaluateurs, len(cov)))

    # Le niveau le plus haut exige une configuration pour chaque signal QUI
    # A UN MODELE -- et rien pour ceux qui n en ont pas.
    # `sans_instrument` plafonne aussi : on ne peut pas dire d un export
    # qu il documente ET configure ses instruments quand l un des signaux
    # mesures n en nomme aucun.
    niveau = ("instrument_declare_et_configure"
              if configures and not nus and not sans_instrument
              else "instrument_declare")
    return {"niveau": niveau, "couvertures": len(cov),
            "signaux_nommes": nommes, "configures": sorted(configures),
            "sans_configuration": sorted(nus),
            "mesures_sans_instrument": sans_instrument,
            "calculs_locaux": sorted(locaux), "statuts": statuts,
            "evaluateurs_partages": partages}


def evaluateurs_partages(identites: dict[str, list[str]]) -> dict[str, list[str]]:
    """Les evaluateurs servant PLUSIEURS signaux. Deux signaux, un appel."""
    return {k: v for k, v in identites.items() if len(v) > 1}


def maillon_preuve(bilan: Bilan) -> None:
    """La limite permanente, et elle ne bougera pas."""
    bilan.dire(NOT_TESTED, INDEMONTRABLE,
               "que l evaluateur declare soit celui qui a tourne",
               "jamais verifiable depuis une archive. Il faudrait observer la "
               "mesure, ce qui est le role de Station et non celui d un "
               "export. Un controle qui pretendrait l etablir serait le faux "
               "PASS que ce produit existe pour refuser.")


def main() -> int:
    a = argparse.ArgumentParser(
        description="Lit la provenance instrumentale d un export Station. "
                    "N a besoin d aucune cle privee.")
    a.add_argument("export", type=Path, help="archive d export Station")
    a.add_argument("--out", type=Path, default=None)
    a.add_argument("--md", type=Path, default=None)
    a.add_argument("--strict", action="store_true",
                   help="sortir 2 si une provenance requise n est pas demontree")
    a.add_argument("--lang", choices=("fr", "en"), default="fr")
    arguments = a.parse_args()
    _LANGUE[0] = arguments.lang

    bilan = Bilan()
    dis("export : %s" % arguments.export)
    dis()
    if not zipfile.is_zipfile(arguments.export):
        bilan.dire(FAIL, CONTROLE, "contrat d export",
                   "ni une archive ZIP lisible : %s" % arguments.export.name)
        dis()
        dis("BILAN : %d PASS, %d FAIL, %d NOT TESTED"
            % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))
        return 1

    with zipfile.ZipFile(arguments.export) as z:
        manifeste = maillon_export(z, bilan)
        structure = maillon_structure(arguments.export, bilan)
        execution = maillon_execution(z, bilan)
        obs_ids = {charge(o).get("observation_id")
                   for o in lignes_jsonl(z, "observations.jsonl")}
        mesure = maillon_mesure(z, obs_ids, bilan)
        mes_ids = {charge(m).get("measurement_id")
                   for m in lignes_jsonl(z, "measurements.jsonl")}
        evaluateur = maillon_evaluateur(z, mes_ids, bilan)
    maillon_preuve(bilan)

    rapport = {
        "schema": SCHEMA_RAPPORT,
        "export": str(arguments.export),
        "export_schema_declared": manifeste.get("schema"),
        "campaign_id_declared": manifeste.get("campaign_id"),
        "campaign_sha256_declared": manifeste.get("campaign_sha256"),
        "provenance_level": evaluateur.get("niveau"),
        "counts": {"pass": bilan.compte(PASS), "fail": bilan.compte(FAIL),
                   "not_tested": bilan.compte(NOT_TESTED)},
        "required_not_demonstrated": bilan.requis_non_demontres(),
        "lines": bilan.lignes,
        "chain": {"export": {"schema": manifeste.get("schema")},
                  "structure": structure, "execution": execution,
                  "measurement": mesure, "evaluator": evaluateur},
        "does_not_establish": [
            "Que l evaluateur declare soit celui qui a tourne. Il faudrait "
            "observer la mesure ; une archive ne le permet pas.",
            "Que les valeurs des signaux soient justes. Ce programme ne "
            "recalcule aucun signal et n en corrige aucun.",
            "La date. Les horodatages de l export sont declares par Station.",
            "Que les artefacts sources existent. L export porte leurs "
            "empreintes, pas leurs octets.",
            "Qu une provenance absente soit l aveu d un defaut. Un calcul "
            "local n a ni modele ni prompt, et ses champs nuls sont corrects.",
        ],
    }

    dis()
    dis("BILAN : %d PASS, %d FAIL, %d NOT TESTED"
        % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))
    dis("NIVEAU DE PROVENANCE : %s" % rapport["provenance_level"])
    if rapport["provenance_level"] == "instrument_non_documente":
        dis()
        dis("Cet export ne documente pas son instrument de mesure. Les "
            "signaux restent exploitables ; ce qui tombe est ce qu on peut "
            "AFFIRMER de la facon dont ils ont ete obtenus.")

    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_bytes(
            (json.dumps(rapport, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        dis("rapport JSON : %s" % arguments.out)
    if arguments.md:
        lignes = ["# Rapport de provenance -- NeoMundi Evidence", "",
                  "- Export : `%s`" % rapport["export"],
                  "- Contrat : `%s`" % rapport["export_schema_declared"],
                  "- Niveau : **%s**" % rapport["provenance_level"],
                  "- Decomptes : %d PASS, %d FAIL, %d NOT TESTED"
                  % (rapport["counts"]["pass"], rapport["counts"]["fail"],
                     rapport["counts"]["not_tested"]), "",
                  "| Etat | Nature | Maillon | Detail |", "|---|---|---|---|"]
        for l in bilan.lignes:
            lignes.append("| %s | %s | %s | %s |"
                          % (l["etat"], l["nature"], l["intitule"],
                             l["detail"].replace("|", "/")[:200]))
        lignes += ["", "## Ce que ce rapport n etablit pas", ""]
        lignes += ["- %s" % x for x in rapport["does_not_establish"]]
        arguments.md.parent.mkdir(parents=True, exist_ok=True)
        arguments.md.write_bytes(("\n".join(lignes) + "\n").encode("utf-8"))
        dis("rapport Markdown : %s" % arguments.md)

    if bilan.compte(FAIL):
        return 1
    if arguments.strict and bilan.requis_non_demontres():
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

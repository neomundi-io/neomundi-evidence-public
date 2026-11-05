# -*- coding: utf-8 -*-
"""Reconcilie un recu externe avec une mesure NeoMundi, champ par champ.

    python adapters/reconcile.py <recu-normalise.json> \\
        --archive <archive_evidence.zip> --map <correspondances.json> \\
        [--observation obs-...] [--out rapport.md] [--json rapport.json] [--strict]

CE QUE CE PROGRAMME ETABLIT
---------------------------

Rien, de lui-meme. Il CONFRONTE, et il conserve les deux cotes. Un recu
externe est une **declaration** ; notre archive est une **preuve primaire**
dans la mesure ou nous en recalculons les empreintes. Les melanger
produirait exactement la confusion que ce produit refuse.

IL REUTILISE `bind.py`, ET N EN REFAIT PAS UN SECOND
----------------------------------------------------

La liaison par empreinte -- la seule forte -- est celle de `bind.py` :
`lire_sujet()` rend les empreintes que l enregistrement declare, et une
empreinte du recu qui tombe sur l une d elles etablit une correspondance
DEMONTREE. Aucun second moteur n est ecrit ici.

LES CINQ STATUTS, ET POURQUOI LA COMPARABILITE PASSE AVANT LA VALEUR
--------------------------------------------------------------------

    MATCHED         les deux cotes sont presents, comparables, et egaux
    MISMATCHED      les deux cotes sont presents, comparables, et DIFFERENTS
    MISSING         un cote est absent
    NOT VERIFIABLE  present, mais nous ne pouvons pas le recalculer
    NOT COMPARABLE  les deux cotes sont presents, et une frontiere de
                    comparabilite est franchie

Le dernier statut est le plus important, et c est celui qu on oublie. Deux
valeurs differentes ne sont une divergence de CALCUL que si elles mesurent
la MEME chose : meme definition, meme version de mesure, meme couverture.
Sinon elles ne se comparent pas, et conclure a une anomalie serait une
faute de raisonnement -- pas une decouverte.

La comparabilite est donc evaluee D ABORD. Un champ non comparable n est
jamais declare `MISMATCHED`.

CE QU IL NE FERA JAMAIS
-----------------------

Trancher une divergence que les donnees ne tranchent pas. Moyenner.
Qualifier de << signe >> ce dont la signature n a pas ete verifiee. Elever
un niveau de garantie sur la foi d une declaration. Deviner une
correspondance : sans entree dans la table, un champ est `NOT COMPARABLE`.

Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

# Reutilisation explicite : la liaison par empreinte vient de `bind.py`.
import bind  # noqa: E402

SCHEMA_RECU = "neomundi.evidence.external-receipt/1"
SCHEMA_RAPPORT = "neomundi.evidence.reconciliation/1"
SCHEMA_TABLE = "neomundi.evidence.reconciliation-map/1"

#: La NATURE d un champ decide si une frontiere de comparabilite le
#: concerne. Une empreinte concorde ou ne concorde pas : la version de
#: mesure n y change rien, et la rendre NOT COMPARABLE detruirait la preuve
#: la plus forte du dispositif. Seules les VALEURS MESUREES dependent du
#: contexte de mesure.
NATURES = ("digest", "identifier", "measured_value", "statement")
NATURE_PAR_DEFAUT = "measured_value"
#: Les natures sur lesquelles une frontiere de comparabilite mord.
NATURES_SENSIBLES_AU_CONTEXTE = ("measured_value",)

MATCHED = "MATCHED"
MISMATCHED = "MISMATCHED"
MISSING = "MISSING"
NOT_VERIFIABLE = "NOT VERIFIABLE"
NOT_COMPARABLE = "NOT COMPARABLE"

#: Les champs de NOS enregistrements qu une table peut viser. Ferme
#: volontairement : viser un champ qui n existe pas doit etre une erreur
#: bruyante, pas un `MISSING` silencieux.
CHAMPS_NEOMUNDI = (
    "observation_id", "item_id", "provider", "model_requested", "model_served",
    "model_served_attestation", "prompt_sha256", "request_sha256",
    "response_sha256", "response_length", "latency_ms", "tokens_input",
    "tokens_output", "execution_status", "finish_reason",
    "dataset_id", "dataset_version",
    "measurement_version", "measurement_coverage", "status",
    "coherence_score", "semantic_risk", "stability_score",
    "factual_hallucination_score", "semantic_instability_score",
    "record_sha256", "code_commit", "comparability_key",
)


class Illisible(Exception):
    """Une entree n a pas la forme attendue."""


def objet(chemin: Path, quoi: str, schema_attendu: str | None = None) -> dict:
    try:
        valeur = json.loads(chemin.read_bytes())
    except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
        raise Illisible("%s n est pas du JSON lisible : %s" % (quoi, erreur)) from erreur
    except OSError as erreur:
        raise Illisible("%s : %s" % (quoi, erreur)) from erreur
    if not isinstance(valeur, dict):
        raise Illisible("%s devrait etre un objet JSON ; recu %s"
                        % (quoi, type(valeur).__name__))
    if schema_attendu and valeur.get("schema") != schema_attendu:
        raise Illisible("%s : schema %r inconnu ; attendu %r"
                        % (quoi, valeur.get("schema"), schema_attendu))
    return valeur


# --------------------------------------------------------------------------
# La table de correspondance -- explicite, jamais devinee
# --------------------------------------------------------------------------


def charge_table(chemin: Path) -> dict:
    table = objet(chemin, "la table de correspondance", SCHEMA_TABLE)
    entrees = table.get("mappings")
    if not isinstance(entrees, list) or not entrees:
        raise Illisible("la table ne declare aucune correspondance")
    problemes, vues = [], set()
    for index, e in enumerate(entrees):
        if not isinstance(e, dict):
            problemes.append("mappings[%d] n est pas un objet" % index)
            continue
        for cle in ("receipt_label", "neomundi_field", "basis"):
            if not isinstance(e.get(cle), str):
                problemes.append("mappings[%d].%s absent ou non textuel" % (index, cle))
        champ = e.get("neomundi_field")
        if isinstance(champ, str) and champ not in CHAMPS_NEOMUNDI:
            # Bruyant, et non silencieux : viser un champ inexistant est une
            # faute de la table, pas une absence de donnee.
            problemes.append(
                "mappings[%d].neomundi_field %r n existe pas dans nos "
                "enregistrements" % (index, champ)
            )
        nature = e.get("kind", NATURE_PAR_DEFAUT)
        if nature not in NATURES:
            problemes.append(
                "mappings[%d].kind %r inconnu ; attendu l un de %s"
                % (index, nature, ", ".join(NATURES))
            )
        chemin = e.get("receipt_source_path")
        if chemin is not None and not isinstance(chemin, str):
            problemes.append("mappings[%d].receipt_source_path doit etre textuel"
                             % index)
        # La cle d unicite est le COUPLE : deux correspondances peuvent
        # porter la meme etiquette si elles visent deux chemins distincts.
        cle = (e.get("receipt_label"), chemin)
        if cle in vues:
            problemes.append(
                "correspondance en double : etiquette %r, chemin %r"
                % (e.get("receipt_label"), chemin)
            )
        vues.add(cle)
    if problemes:
        raise Illisible("; ".join(problemes[:5]))
    return table


# --------------------------------------------------------------------------
# Lecture de NOTRE cote
# --------------------------------------------------------------------------


def lire_notre_cote(archive: Path, observation_id: str) -> dict[str, object]:
    """Les valeurs de NOTRE enregistrement, pour une observation.

    Passe par `bind.lire_sujet` pour les empreintes declarees -- c est la
    reutilisation annoncee -- puis relit l observation et sa mesure pour les
    champs de valeur.
    """
    import zipfile

    sujet, empreintes = bind.lire_sujet(archive, observation_id)
    valeurs: dict[str, object] = dict(empreintes)
    valeurs.update({k: v for k, v in sujet.items() if isinstance(v, str)})

    with zipfile.ZipFile(archive) as z:
        noms = z.namelist()
        for ligne in bind.lignes_jsonl(z.read("observations.jsonl"),
                                       "observations.jsonl"):
            p = bind.charge(ligne)
            if p.get("observation_id") != observation_id:
                continue
            for cle in CHAMPS_NEOMUNDI:
                if cle in p:
                    valeurs[cle] = p[cle]
            break
        if "measurements.jsonl" in noms:
            for ligne in bind.lignes_jsonl(z.read("measurements.jsonl"),
                                           "measurements.jsonl"):
                m = bind.charge(ligne)
                if m.get("observation_id") != observation_id:
                    continue
                for cle in ("measurement_version", "measurement_coverage", "status"):
                    if cle in m:
                        valeurs[cle] = m[cle]
                signaux = m.get("signals")
                if isinstance(signaux, dict):
                    for cle, valeur in signaux.items():
                        if cle in CHAMPS_NEOMUNDI:
                            valeurs[cle] = valeur
                break
    return valeurs


# --------------------------------------------------------------------------
# La comparaison -- comparabilite D ABORD
# --------------------------------------------------------------------------


def normalise_nombre(valeur: object) -> float | None:
    """Rend un flottant si la valeur en a la forme, sinon None.

    La virgule decimale est acceptee : un recu francophone ecrit `0,3863`,
    et refuser de le lire serait une faute d outil, pas une rigueur.
    """
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        return float(valeur)
    if not isinstance(valeur, str):
        return None
    texte = valeur.strip().replace(",", ".")
    try:
        return float(texte)
    except ValueError:
        return None


def compare_un_champ(entree: dict, recu: dict, nous: dict,
                     tolerance: float, comparabilite: list[str],
                     arguments_fournis: tuple[str, ...] = ()) -> dict:
    """Le statut d un champ, et tout ce qui a servi a le decider."""
    etiquette = entree["receipt_label"]
    champ = entree["neomundi_field"]
    chemin_vise = entree.get("receipt_source_path")

    # Un `receipt_source_path` est une VRAIE cle : l importateur le releve
    # par champ. Une etiquette ne l est pas -- constate sur le dossier CP8
    # reel, ou << Verifier A >> designe deux lignes de tableau.
    if chemin_vise:
        trouves = [c for c in recu["fields"] if c["source_path"] == chemin_vise]
    else:
        trouves = [c for c in recu["fields"] if c["label"] == etiquette]
    cote_recu = trouves[0] if trouves else None
    presente_chez_nous = champ in nous

    resultat = {
        "receipt_label": etiquette,
        "neomundi_field": champ,
        "basis": entree["basis"],
        "receipt_value": cote_recu["value"] if cote_recu else None,
        "receipt_source_path": cote_recu["source_path"] if cote_recu else chemin_vise,
        "neomundi_value": nous.get(champ),
        "status": None,
        "note": "",
    }

    # AMBIGUITE : plusieurs champs portent cette etiquette, et aucun chemin
    # n a ete vise. Choisir le premier serait deviner -- et produire un
    # rapport faux sans le dire.
    if len(trouves) > 1:
        resultat["status"] = NOT_COMPARABLE
        resultat["receipt_value"] = None
        resultat["receipt_source_path"] = None
        resultat["note"] = (
            "ETIQUETTE AMBIGUE : %d champs du recu portent %r (%s). Viser un "
            "`receipt_source_path` dans la table pour lever l ambiguite. Choisir "
            "le premier serait deviner."
            % (len(trouves), etiquette,
               ", ".join(c["source_path"] for c in trouves[:4]))
        )
        return resultat

    if cote_recu is None and not presente_chez_nous:
        resultat["status"] = MISSING
        resultat["note"] = "absent des deux cotes"
        return resultat
    if cote_recu is None:
        resultat["status"] = MISSING
        resultat["note"] = ("l etiquette %r n est pas dans le recu ; notre cote "
                            "porte une valeur" % etiquette)
        return resultat
    if not presente_chez_nous:
        resultat["status"] = MISSING
        resultat["note"] = ("le recu porte une valeur ; notre enregistrement n a "
                            "pas de champ %r pour cette observation" % champ)
        return resultat

    # --- LA COMPARABILITE PASSE AVANT LA VALEUR -----------------------
    # ... mais seulement pour les champs dont la nature en depend. Une
    # empreinte ou un identifiant se comparent quel que soit le contexte de
    # mesure, et les declarer NOT COMPARABLE serait perdre la preuve la plus
    # forte dont on dispose.
    nature = entree.get("kind", NATURE_PAR_DEFAUT)
    resultat["kind"] = nature
    if comparabilite and nature in NATURES_SENSIBLES_AU_CONTEXTE:
        resultat["status"] = NOT_COMPARABLE
        resultat["note"] = (
            "VALEUR MESUREE, et une frontiere de comparabilite est franchie : "
            "%s. Les deux valeurs ne mesurent donc pas forcement la meme chose, "
            "et les declarer divergentes serait une faute de raisonnement, pas "
            "une decouverte." % " ; ".join(comparabilite)
        )
        return resultat

    # NOT VERIFIABLE passe AVANT NOT COMPARABLE : si nous ne pouvons pas
    # controler la valeur faute de materiau, la question de sa comparabilite
    # ne se pose meme pas.
    requis = entree.get("requires")
    if requis and requis not in (arguments_fournis or ()):
        resultat["status"] = NOT_VERIFIABLE
        resultat["note"] = (
            "le recu declare cette valeur, et sa verification demande %s -- "
            "qui n est pas fourni. Ce n est ni une concordance ni une "
            "divergence : c est une impossibilite de controler." % requis
        )
        return resultat

    if entree.get("comparable") is False:
        resultat["status"] = NOT_COMPARABLE
        resultat["note"] = entree.get("not_comparable_reason") or (
            "la table declare ce champ non comparable")
        return resultat

    # --- egalite, numerique ou textuelle ------------------------------
    a = normalise_nombre(cote_recu["value"])
    b = normalise_nombre(nous[champ])
    if a is not None and b is not None:
        ecart = abs(a - b)
        if ecart <= tolerance:
            resultat["status"] = MATCHED
            resultat["note"] = "ecart %.6g, dans la tolerance %.6g" % (ecart, tolerance)
        else:
            resultat["status"] = MISMATCHED
            resultat["note"] = (
                "ecart %.6g, au-dela de la tolerance %.6g. **LES DEUX VALEURS "
                "SONT CONSERVEES TELLES QUELLES** : rien n est tranche ici."
                % (ecart, tolerance)
            )
        resultat["delta"] = ecart
        return resultat

    if str(cote_recu["value"]).strip() == str(nous[champ]).strip():
        resultat["status"] = MATCHED
        resultat["note"] = "chaines identiques"
    else:
        resultat["status"] = MISMATCHED
        resultat["note"] = ("chaines differentes. Les deux sont conservees ; "
                            "rien n est tranche.")
    return resultat


def frontieres_de_comparabilite(table: dict, nous: dict) -> list[str]:
    """Ce qui empeche de comparer les valeurs, avant meme de les regarder.

    La table DECLARE le contexte du recu -- version de mesure, couverture,
    definition. S il diverge du notre, aucune valeur ne se compare.
    """
    declare = table.get("receipt_context") or {}
    frontieres = []
    for cle, intitule in (("measurement_version", "version de mesure"),
                          ("measurement_coverage", "couverture de mesure"),
                          ("score_definition", "definition du score")):
        cote_recu = declare.get(cle)
        cote_nous = nous.get(cle) if cle != "score_definition" else \
            declare.get("our_score_definition")
        if cote_recu is None:
            frontieres.append(
                "%s du recu NON DECLAREE -- impossible d etablir la comparabilite"
                % intitule
            )
        elif cote_nous is None:
            frontieres.append("%s de notre cote inconnue" % intitule)
        elif str(cote_recu).strip() != str(cote_nous).strip():
            frontieres.append("%s : recu %r, nous %r"
                              % (intitule, cote_recu, cote_nous))
    return frontieres


# --------------------------------------------------------------------------
# La liaison -- par empreinte, par identifiant, ou refusee
# --------------------------------------------------------------------------


def etablir_la_liaison(recu: dict, archive: Path,
                       observation_demandee: str | None) -> tuple[str | None, str, str]:
    """Rend (observation_id, voie, explication).

    Trois voies, par force decroissante, et aucune quatrieme. Une proximite
    de date, de modele ou de valeur NE CONSTITUE PAS une liaison : un
    adaptateur qui relierait sur cette base fabriquerait la preuve qu il
    pretend verifier.
    """
    import zipfile

    with zipfile.ZipFile(archive) as z:
        observations = bind.lignes_jsonl(z.read("observations.jsonl"),
                                         "observations.jsonl")
    charges = [bind.charge(o) for o in observations]

    # --- voie 1 : par EMPREINTE. La seule forte. ----------------------
    empreintes_recu = {d["sha256"] for d in recu.get("digests", [])}
    if empreintes_recu:
        for p in charges:
            declarees = {p.get(c) for c in ("response_sha256", "prompt_sha256",
                                            "request_sha256")}
            communes = empreintes_recu & {d for d in declarees if isinstance(d, str)}
            if communes:
                return (p["observation_id"], "empreinte",
                        "une empreinte du recu egale une empreinte que "
                        "l enregistrement declare : %s" % sorted(communes)[0][:16] + "...")

    # --- voie 2 : par IDENTIFIANT. Declarative, donc moyenne. ---------
    identifiants = {c["value"].strip() for c in recu.get("fields", [])
                    if c.get("value")}
    for p in charges:
        for cle in ("observation_id", "item_id"):
            valeur = p.get(cle)
            if isinstance(valeur, str) and valeur in identifiants:
                return (p["observation_id"], "identifiant",
                        "le recu porte %s = %r, retrouve dans notre corpus"
                        % (cle, valeur))

    # --- voie 3 : aucune. La liaison est REFUSEE. ---------------------
    if observation_demandee:
        return (None, "refusee",
                "aucune empreinte ni identifiant commun. L observation %r a ete "
                "DEMANDEE, mais une demande n est pas une correspondance "
                "demontree : la liaison est refusee." % observation_demandee)
    return (None, "refusee",
            "aucune empreinte ni identifiant commun entre le recu et le corpus. "
            "Une proximite de date, de modele ou de valeur ne constitue pas une "
            "liaison.")


# --------------------------------------------------------------------------


def reconcilier(arguments: argparse.Namespace) -> tuple[dict, int]:
    recu = objet(arguments.receipt, "le recu normalise", SCHEMA_RECU)
    table = charge_table(arguments.map)

    print("Recu     : %s" % arguments.receipt)
    print("  source : %s (%s)" % (recu["source"]["name"], recu["source"]["sha256"][:16] + "..."))
    print("Archive  : %s" % arguments.archive)
    print("Table    : %s (%d correspondance(s) declaree(s))\n"
          % (arguments.map, len(table["mappings"])))

    identifiant, voie, explication = etablir_la_liaison(
        recu, arguments.archive, arguments.observation)
    print("LIAISON  : %s" % voie.upper())
    print("  %s" % explication)

    rapport: dict[str, object] = {
        "schema": SCHEMA_RAPPORT,
        "receipt": {
            "name": recu["source"]["name"],
            "sha256": recu["source"]["sha256"],
            "received_at_declared": recu["source"]["received_at_declared"],
            "form": recu["source"]["form"],
        },
        "archive": str(arguments.archive),
        "map": str(arguments.map),
        "link": {"route": voie, "observation_id": identifiant,
                 "explanation": explication},
        "evidence_classes": {
            "primary_evidence": [
                "les empreintes de notre archive, que nous recalculons",
            ],
            "external_declaration": [
                "tout champ du recu : valeur, statut, identifiant",
                "toute signature annoncee et non verifiee",
            ],
            "verified_conclusion": [],
        },
        "fields": [],
        "comparability_boundaries": [],
        "contradictions_preserved": [],
        "limits": [
            "Un recu externe est une DECLARATION. Rien ici ne le transforme en "
            "preuve verifiee.",
            "Aucune divergence n est tranchee : les deux valeurs sont conservees.",
            "Aucune signature n a ete verifiee ; le recu n est pas qualifie de signe.",
            "Aucune correspondance n est devinee : sans entree dans la table, un "
            "champ est NOT COMPARABLE.",
        ],
    }

    if identifiant is None:
        rapport["fields"] = [
            {"receipt_label": e["receipt_label"], "neomundi_field": e["neomundi_field"],
             "basis": e["basis"], "receipt_value": None, "neomundi_value": None,
             "status": NOT_COMPARABLE,
             "note": "aucune liaison etablie : il n y a pas de cote NeoMundi a "
                     "confronter."}
            for e in table["mappings"]
        ]
        print("\nAucune liaison : %d champ(s) ressortent NOT COMPARABLE."
              % len(rapport["fields"]))
        return rapport, 0

    nous = lire_notre_cote(arguments.archive, identifiant)
    frontieres = frontieres_de_comparabilite(table, nous)
    rapport["comparability_boundaries"] = frontieres
    if frontieres:
        print("\nFRONTIERES DE COMPARABILITE -- evaluees AVANT les valeurs :")
        for f in frontieres:
            print("  - %s" % f)

    # Ce que l appelant a reellement fourni. Un champ dont la verification
    # exige un materiau absent de cette liste ressort NOT VERIFIABLE.
    fournis = tuple(arguments.supplied or ())
    tolerance = arguments.tolerance
    if fournis:
        print("\nmateriaux fournis : %s" % ", ".join(fournis))
    print("\nCHAMP PAR CHAMP (tolerance numerique %.6g) :\n" % tolerance)
    for entree in table["mappings"]:
        resultat = compare_un_champ(entree, recu, nous, tolerance, frontieres,
                                    fournis)
        rapport["fields"].append(resultat)
        print("[%-14s] %-26s  recu=%-14s  nous=%s"
              % (resultat["status"], entree["receipt_label"][:26],
                 str(resultat["receipt_value"])[:14],
                 str(resultat["neomundi_value"])[:20]))
        if resultat["status"] in (MISMATCHED, NOT_COMPARABLE):
            print("                 %s" % resultat["note"][:140])

    rapport["contradictions_preserved"] = [
        {"receipt_label": f["receipt_label"], "neomundi_field": f["neomundi_field"],
         "receipt_value": f["receipt_value"], "neomundi_value": f["neomundi_value"],
         "status": f["status"]}
        for f in rapport["fields"] if f["status"] in (MISMATCHED, NOT_COMPARABLE)
    ]

    decompte = {}
    for f in rapport["fields"]:
        decompte[f["status"]] = decompte.get(f["status"], 0) + 1
    rapport["counts"] = decompte

    print("\nBILAN : " + ", ".join("%d %s" % (n, s) for s, n in sorted(decompte.items())))
    if rapport["contradictions_preserved"]:
        print("\n%d contradiction(s) CONSERVEE(S), aucune tranchee :"
              % len(rapport["contradictions_preserved"]))
        for c in rapport["contradictions_preserved"]:
            print("  %s : recu %r / nous %r  [%s]"
                  % (c["receipt_label"], c["receipt_value"], c["neomundi_value"],
                     c["status"]))

    # Le mode strict : une liaison refusee ou un champ non verifiable sont
    # CONTINGENTS -- fournir le dossier complet les leverait.
    manquants = [f["receipt_label"] for f in rapport["fields"]
                 if f["status"] in (MISSING, NOT_VERIFIABLE, NOT_COMPARABLE)]
    code = 0
    if arguments.strict and (manquants or voie == "refusee"):
        code = 2
        print("\nMODE STRICT : %d champ(s) non etabli(s), liaison %s."
              % (len(manquants), voie))
        print("Aucun statut n a change : seul le code de sortie en tient compte (2).")
    elif arguments.strict:
        print("\nMODE STRICT : tous les champs sont etablis.")
    rapport["strict"] = bool(arguments.strict)
    rapport["required_not_established"] = manquants
    rapport["exit_code"] = code
    return rapport, code


def ecrire_markdown(rapport: dict, chemin: Path) -> None:
    """Un rapport intelligible, qui conserve les deux cotes."""
    lignes = [
        "# Rapport de reconciliation",
        "",
        "> Un recu externe est une **declaration**. Notre archive est une **preuve",
        "> primaire** dans la mesure ou nous en recalculons les empreintes. Ce",
        "> rapport les confronte et **conserve les deux cotes** : il ne tranche rien.",
        "",
        "| | |",
        "|---|---|",
        "| Recu | `%s` |" % rapport["receipt"]["name"],
        "| Empreinte du recu | `%s` |" % rapport["receipt"]["sha256"],
        "| Recu le (declare par nous) | %s |" % rapport["receipt"]["received_at_declared"],
        "| Archive | `%s` |" % Path(rapport["archive"]).name,
        "| Voie de liaison | **%s** |" % rapport["link"]["route"].upper(),
        "| Observation liee | `%s` |" % (rapport["link"]["observation_id"] or "aucune"),
        "",
        "**Liaison :** %s" % rapport["link"]["explanation"],
        "",
    ]
    if rapport.get("comparability_boundaries"):
        lignes += [
            "## Frontieres de comparabilite",
            "",
            "Evaluees **avant** toute comparaison de valeur. Deux valeurs ne sont",
            "une divergence de calcul que si elles mesurent la meme chose.",
            "",
        ]
        lignes += ["- %s" % f for f in rapport["comparability_boundaries"]]
        lignes.append("")

    lignes += ["## Champ par champ", "",
               "| Statut | Nature | Etiquette du recu | Champ NeoMundi | Valeur du recu | Notre valeur |",
               "|---|---|---|---|---|---|"]
    for f in rapport["fields"]:
        lignes.append("| **%s** | %s | `%s` | `%s` | `%s` | `%s` |" % (
            f["status"], f.get("kind", "?"), f["receipt_label"],
            f["neomundi_field"], f["receipt_value"], f["neomundi_value"]))
    lignes.append("")

    if rapport.get("contradictions_preserved"):
        lignes += ["## Contradictions conservees", "",
                   "**Aucune n est tranchee.** Les deux valeurs figurent telles quelles.",
                   ""]
        for c in rapport["contradictions_preserved"]:
            lignes.append("- `%s` : recu **%s**, nous **%s** — *%s*"
                          % (c["receipt_label"], c["receipt_value"],
                             c["neomundi_value"], c["status"]))
        lignes.append("")

    lignes += ["## Classes de preuve", ""]
    for classe, intitule in (("primary_evidence", "Preuve primaire"),
                             ("external_declaration", "Declaration externe"),
                             ("verified_conclusion", "Conclusion verifiee")):
        elements = rapport["evidence_classes"][classe]
        lignes.append("**%s** — %s" % (intitule, "aucune" if not elements else ""))
        lignes += ["- %s" % e for e in elements]
        lignes.append("")

    lignes += ["## Limites", ""] + ["- %s" % l for l in rapport["limits"]] + [""]
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n".join(lignes), encoding="utf-8")


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Reconcilie un recu externe avec une mesure NeoMundi."
    )
    analyseur.add_argument("receipt", type=Path, help="le recu NORMALISE (JSON)")
    analyseur.add_argument("--archive", type=Path, required=True)
    analyseur.add_argument("--map", type=Path, required=True,
                           help="table de correspondance EXPLICITE. Exigee : "
                                "aucune correspondance n est devinee.")
    analyseur.add_argument("--observation", default=None,
                           help="observation souhaitee ; une demande n est PAS une "
                                "correspondance demontree")
    analyseur.add_argument(
        "--supplied", action="append", default=None, metavar="MATERIAU",
        help="declare un materiau effectivement fourni (ex. `le journal d "
             "execution`). Un champ qui en exige un absent ressort "
             "NOT VERIFIABLE.",
    )
    analyseur.add_argument("--tolerance", type=float, default=1e-9)
    analyseur.add_argument("--out", type=Path, default=None, help="rapport Markdown")
    analyseur.add_argument("--json", type=Path, default=None)
    analyseur.add_argument("--strict", action="store_true",
                           help="code 2 si un champ reste non etabli. Ne change "
                                "AUCUN statut.")
    arguments = analyseur.parse_args()

    try:
        rapport, code = reconcilier(arguments)
    except (Illisible, bind.Illisible) as erreur:
        print("[FAIL      ] %s" % erreur)
        return 1
    except OSError as erreur:
        print("[FAIL      ] %s" % erreur)
        return 1

    if arguments.out:
        ecrire_markdown(rapport, arguments.out)
        print("\nrapport Markdown : %s" % arguments.out)
    if arguments.json:
        arguments.json.parent.mkdir(parents=True, exist_ok=True)
        arguments.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("rapport JSON     : %s" % arguments.json)
    return code


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Tests de la reconciliation entre un recu externe et une mesure NeoMundi.

    python tests/test_reconciliation.py [<archive_evidence.zip>]

Sans argument, la fixture d integration continue est fabriquee et utilisee :
la suite est donc autonome et deterministe.

CE QUE CES TESTS EPROUVENT
--------------------------

Que les CINQ statuts sont reellement distingues. Qu une correspondance n est
jamais devinee. Que la comparabilite est evaluee avant la valeur -- mais
seulement pour les valeurs MESUREES, jamais pour une empreinte. Et que les
contradictions sont conservees, jamais tranchees.

Ils n eprouvent PAS que le recu soit vrai : c est une declaration externe,
et rien ici ne la transforme en preuve.

Bibliotheque standard seule. Toutes les fixtures sont SYNTHETIQUES.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
IMPORTEUR = RACINE / "adapters" / "receipt_import.py"
RECONCILIATEUR = RACINE / "adapters" / "reconcile.py"
FABRIQUE = RACINE / "tests" / "make_fixture.py"
EXEMPLES = RACINE / "examples" / "reconciliation"
RECU_HTML = EXEMPLES / "receipt-synthetic.html"

QUAND = "2026-11-05T12:00:00Z"


def lancer(programme: Path, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run([sys.executable, str(programme)] + args,
                          capture_output=True, text=True, check=False,
                          encoding="utf-8", errors="replace")
    return fini.returncode, fini.stdout + fini.stderr


def statuts(sortie: str) -> dict[str, int]:
    """Les decomptes par statut, lus sur la ligne de bilan."""
    for ligne in sortie.splitlines():
        if ligne.startswith("BILAN : ") and "MATCH" in ligne or \
           ligne.startswith("BILAN : ") and "COMPARABLE" in ligne:
            sortie_dict = {}
            for part in ligne[len("BILAN : "):].split(", "):
                morceaux = part.strip().split(" ", 1)
                if len(morceaux) == 2 and morceaux[0].isdigit():
                    sortie_dict[morceaux[1]] = int(morceaux[0])
            return sortie_dict
    return {}


def statut_de(sortie: str, etiquette: str) -> str:
    for ligne in sortie.splitlines():
        if ligne.startswith("[") and "] " in ligne:
            etat, _, reste = ligne[1:].partition("] ")
            if reste.strip().startswith(etiquette[:26]):
                return etat.strip()
    return "absent"


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="reconciliation-"))
    resultats: list[tuple[str, str, object, str]] = []

    def pose(numero, intitule, reussi, constat):
        resultats.append((numero, intitule, reussi, constat))

    try:
        # ---- le decor : une archive, et le recu importe ----------------
        if len(sys.argv) > 1:
            archive = Path(sys.argv[1]).resolve()
        else:
            code, _ = lancer(FABRIQUE, [str(travail / "fixture")])
            if code != 0:
                print("la fabrique de fixture a echoue")
                return 2
            archive = travail / "fixture" / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"

        print("Tests de reconciliation")
        print("archive : %s" % archive.name)
        print("recu    : %s (SYNTHETIQUE)\n" % RECU_HTML.name)

        recu = travail / "recu.json"
        code, s = lancer(IMPORTEUR, [str(RECU_HTML), "--received-at", QUAND,
                                     "--out", str(recu)])
        pose("1", "import du recu : champs et empreintes releves",
             code == 0 and recu.is_file(),
             "code %d" % code)

        normalise = json.loads(recu.read_text(encoding="utf-8"))
        pose("2", "aucune signature n est reconnue ni declaree",
             normalise["signatures"] == []
             and any("cryptographiquement signe" in l for l in normalise["limits"]),
             "signatures=[] et la limite est ecrite")

        pose("3", "les valeurs sont VERBATIM, avec leur chemin d origine",
             all("source_path" in c and c["value"] is not None
                 for c in normalise["fields"]),
             "%d champs, tous avec un chemin" % len(normalise["fields"]))

        # ---- les cinq statuts, table AVEC contexte ---------------------
        code, s5 = lancer(RECONCILIATEUR, [
            str(recu), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-comparable.json")])
        vus = statuts(s5)
        attendus = {"MATCHED", "MISMATCHED", "MISSING", "NOT COMPARABLE",
                    "NOT VERIFIABLE"}
        pose("4", "les CINQ statuts sont reellement distingues",
             code == 0 and attendus <= set(vus),
             "vus : %s" % ", ".join("%s=%d" % (k, v) for k, v in sorted(vus.items())))

        # ---- la liaison par EMPREINTE ---------------------------------
        pose("5", "liaison par EMPREINTE, la seule forte",
             "LIAISON  : EMPREINTE" in s5,
             "une empreinte du recu tombe sur une empreinte declaree")

        # ---- les contradictions sont CONSERVEES ------------------------
        rapport = travail / "r.json"
        lancer(RECONCILIATEUR, [str(recu), "--archive", str(archive),
                                "--map", str(EXEMPLES / "map-comparable.json"),
                                "--json", str(rapport)])
        r = json.loads(rapport.read_text(encoding="utf-8"))
        contradictions = r["contradictions_preserved"]
        deux_cotes = all(c["receipt_value"] is not None or c["neomundi_value"] is not None
                         for c in contradictions)
        pose("6", "les contradictions sont conservees, les DEUX valeurs",
             len(contradictions) >= 2 and deux_cotes,
             "%d contradiction(s), les deux cotes presents" % len(contradictions))

        pose("7", "0,3863 et 0,594 figurent tels quels dans le rapport",
             any("0,3863" in str(c["receipt_value"]) for c in contradictions)
             and any("0,594" in str(c["receipt_value"]) for c in r["fields"]),
             "les deux valeurs du recu sont preservees sans conversion")

        # ---- la virgule decimale est lue ------------------------------
        coherence = next(f for f in r["fields"] if f["neomundi_field"] == "coherence_score")
        pose("8", "une virgule decimale est lue, pas rejetee",
             coherence["status"] == "MISMATCHED" and "delta" in coherence,
             "ecart calcule : %s" % coherence.get("delta"))

        # ---- SANS contexte : rien ne se compare, SAUF les empreintes ---
        code, s9 = lancer(RECONCILIATEUR, [
            str(recu), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-no-context.json")])
        pose("9", "sans contexte declare : les valeurs mesurees ne se comparent pas",
             statut_de(s9, "score de coherence") == "NOT COMPARABLE"
             and statut_de(s9, "latence observee") == "NOT COMPARABLE",
             "la frontiere mord sur les valeurs mesurees")

        pose("10", "mais une EMPREINTE concorde quand meme",
             statut_de(s9, "empreinte de la reponse") == "MATCHED"
             and statut_de(s9, "item") == "MATCHED",
             "une empreinte concorde ou non ; la version de mesure n y change rien")

        # ---- aucune correspondance devinee -----------------------------
        champs_rapportes = {f["receipt_label"] for f in r["fields"]}
        champs_du_recu = {c["label"] for c in normalise["fields"]}
        hors_table = champs_du_recu - champs_rapportes
        pose("11", "aucune correspondance n est devinee",
             len(hors_table) >= 3,
             "%d champ(s) du recu laisses de cote faute d entree dans la table"
             % len(hors_table))

        # ---- une table qui vise un champ INEXISTANT -------------------
        mauvaise = json.loads((EXEMPLES / "map-comparable.json").read_text(encoding="utf-8"))
        mauvaise["mappings"][0]["neomundi_field"] = "champ_qui_n_existe_pas"
        chemin = travail / "map-mauvaise.json"
        chemin.write_text(json.dumps(mauvaise), encoding="utf-8")
        code, s12 = lancer(RECONCILIATEUR, [str(recu), "--archive", str(archive),
                                            "--map", str(chemin)])
        pose("12", "table visant un champ inexistant : refus BRUYANT",
             code == 1 and "n existe pas" in s12,
             "refus motive, pas un MISSING silencieux")

        # ---- etiquette en double --------------------------------------
        doublon = json.loads((EXEMPLES / "map-comparable.json").read_text(encoding="utf-8"))
        doublon["mappings"].append(dict(doublon["mappings"][0]))
        chemin = travail / "map-doublon.json"
        chemin.write_text(json.dumps(doublon), encoding="utf-8")
        code, s13 = lancer(RECONCILIATEUR, [str(recu), "--archive", str(archive),
                                            "--map", str(chemin)])
        pose("13", "etiquette de recu en double : refus",
             code == 1 and "en double" in s13, "refus motive")

        # ---- schemas inconnus ------------------------------------------
        for numero, cible, cle in (("14", "recu", "schema"), ("15", "table", "schema")):
            if cible == "recu":
                mauvais = {**normalise, cle: "autre/99"}
                chemin = travail / "recu-schema.json"
                chemin.write_text(json.dumps(mauvais), encoding="utf-8")
                code, sx = lancer(RECONCILIATEUR, [
                    str(chemin), "--archive", str(archive),
                    "--map", str(EXEMPLES / "map-comparable.json")])
            else:
                mauvais = {**json.loads((EXEMPLES / "map-comparable.json")
                                        .read_text(encoding="utf-8")), cle: "autre/99"}
                chemin = travail / "map-schema.json"
                chemin.write_text(json.dumps(mauvais), encoding="utf-8")
                code, sx = lancer(RECONCILIATEUR, [
                    str(recu), "--archive", str(archive), "--map", str(chemin)])
            pose(numero, "schema de %s inconnu : refuse, pas interprete" % cible,
                 code == 1 and "inconnu" in sx, "refus motive")

        # ---- entrees HOSTILES a l importeur ---------------------------
        hostiles = [
            ("html vide", b""),
            ("html tronque", b"<table><tr><td>a"),
            ("balises imbriquees a l excess", b"<table>" + b"<tr><td>x</td>" * 200 + b"</table>"),
            ("script injecte", b"<table><tr><td>cle</td><td><script>alert(1)</script>v</td></tr></table>"),
            ("octets non utf-8", bytes([0xff, 0xfe, 0x00]) + b"<table><tr><td>a</td><td>b</td></tr></table>"),
            ("json non objet", b"[1,2,3]"),
        ]
        plantages = []
        for nom, contenu in hostiles:
            suffixe = ".json" if "json" in nom else ".html"
            cible = travail / ("hostile-%s%s" % (nom.replace(" ", "-"), suffixe))
            cible.write_bytes(contenu)
            code, sh = lancer(IMPORTEUR, [str(cible), "--received-at", QUAND,
                                          "--out", str(travail / "h.json")])
            if "Traceback" in sh:
                plantages.append(nom)
        pose("16", "six entrees hostiles : aucune trace d appels",
             not plantages,
             "%d/6 traitees proprement" % (len(hostiles) - len(plantages))
             + ("" if not plantages else " ; plantages : %s" % plantages))

        # ---- un script injecte ne devient pas une valeur de confiance --
        cible = travail / "injecte.html"
        cible.write_bytes(
            b"<table><tr><td>cle</td><td><script>alert(1)</script>valeur</td></tr></table>")
        lancer(IMPORTEUR, [str(cible), "--received-at", QUAND,
                           "--out", str(travail / "i.json")])
        injecte = json.loads((travail / "i.json").read_text(encoding="utf-8"))
        valeurs = " ".join(c["value"] for c in injecte["fields"])
        pose("17", "le contenu d un recu reste une DONNEE, jamais une instruction",
             "<script>" not in valeurs,
             "le balisage est consomme, le texte conserve")

        # ---- liaison REFUSEE quand rien ne concorde -------------------
        sans_lien = travail / "sans-lien.html"
        sans_lien.write_bytes(
            b"<table><tr><td>item</td><td>rien-de-commun</td></tr>"
            b"<tr><td>score de coherence</td><td>0,1</td></tr></table>")
        code, _ = lancer(IMPORTEUR, [str(sans_lien), "--received-at", QUAND,
                                     "--out", str(travail / "sl.json")])
        code, s18 = lancer(RECONCILIATEUR, [
            str(travail / "sl.json"), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-comparable.json")])
        pose("18", "aucune correspondance : la liaison est REFUSEE",
             "LIAISON  : REFUSEE" in s18 and "ne constitue pas une liaison" in s18,
             "ni empreinte ni identifiant commun")

        # ---- une observation DEMANDEE n est pas une liaison -----------
        code, s19 = lancer(RECONCILIATEUR, [
            str(travail / "sl.json"), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-comparable.json"),
            "--observation", "obs-" + "0" * 64])
        pose("19", "une observation DEMANDEE n est pas une correspondance demontree",
             "REFUSEE" in s19 and "une demande n est pas" in s19,
             "la demande est refusee explicitement")

        # ---- strict : code 2, et AUCUN statut change ------------------
        code_a, sa = lancer(RECONCILIATEUR, [
            str(recu), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-comparable.json")])
        code_b, sb = lancer(RECONCILIATEUR, [
            str(recu), "--archive", str(archive),
            "--map", str(EXEMPLES / "map-comparable.json"), "--strict"])
        lignes_a = [l for l in sa.splitlines() if l.startswith("[")]
        lignes_b = [l for l in sb.splitlines() if l.startswith("[")]
        pose("20", "strict : code 2, et AUCUN statut change",
             code_a == 0 and code_b == 2 and lignes_a == lignes_b,
             "%d lignes identiques ; code %d puis %d"
             % (len(lignes_a), code_a, code_b))

        # ---- le rapport Markdown est intelligible ---------------------
        md = travail / "rapport.md"
        lancer(RECONCILIATEUR, [str(recu), "--archive", str(archive),
                                "--map", str(EXEMPLES / "map-comparable.json"),
                                "--out", str(md)])
        texte = md.read_text(encoding="utf-8")
        pose("21", "rapport Markdown : les trois classes de preuve y figurent",
             all(m in texte for m in ("Preuve primaire", "Declaration externe",
                                      "Conclusion verifiee", "Contradictions conservees")),
             "classes et contradictions presentes")

        pose("22", "le rapport ne porte AUCUN chemin de machine",
             "C:\\Users" not in texte and "/home/" not in texte,
             "seul le nom de l archive figure")

        # ---- `bind.py` est reellement reutilise ----------------------
        import ast

        arbre = ast.parse(RECONCILIATEUR.read_text(encoding="utf-8"))
        importe_bind = any(
            (isinstance(n, ast.Import) and any(a.name == "bind" for a in n.names))
            for n in ast.walk(arbre))
        appels = [n.func.attr for n in ast.walk(arbre)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and isinstance(n.func.value, ast.Name) and n.func.value.id == "bind"]
        pose("23", "`bind.py` est reutilise, aucun second moteur",
             importe_bind and "lire_sujet" in appels,
             "appels a bind : %s" % ", ".join(sorted(set(appels))))

        # ---- le recu n est JAMAIS qualifie de signe -------------------
        tout = s5 + texte + json.dumps(r, ensure_ascii=False)
        faux = [m for m in ("recu signe", "signature verifiee", "cryptographiquement signe et")
                if m in tout.lower()]
        pose("24", "le recu n est jamais qualifie de signe ni de verifie",
             not faux and "DECLARATION" in tout.upper(),
             "aucune qualification abusive" if not faux else "trouve : %s" % faux)

    finally:
        shutil.rmtree(travail, ignore_errors=True)

    print()
    echecs = []
    for numero, intitule, reussi, constat in resultats:
        etiquette = "OK" if reussi else "PROBLEME"
        if not reussi:
            echecs.append("%s %s" % (numero, intitule))
        print("[%-9s] %-3s %-54s %s" % (etiquette, numero, intitule[:54], constat[:70]))

    print("\nBILAN : %d/%d cas conformes" % (len(resultats) - len(echecs), len(resultats)))
    for e in echecs:
        print("  PROBLEME : %s" % e)

    if not echecs:
        print("\nCe que ces tests etablissent : les cinq statuts sont distingues, aucune")
        print("correspondance n est devinee, et les contradictions sont conservees.")
        print("Ce qu ils n etablissent pas : que le recu soit vrai. C est une")
        print("declaration externe, et rien ici ne la transforme en preuve.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

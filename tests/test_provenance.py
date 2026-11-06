# -*- coding: utf-8 -*-
"""Provenance instrumentale : lire ce qui est la, nommer ce qui manque.

D OU VIENT CETTE SUITE
----------------------

De R-6. L API de mesure sert, par signal, l evaluateur, le modele utilise, le
statut, le motif et des empreintes de configuration. Station en modelise la
conservation -- `MeasurementCoverage`, avec sa barriere anti-secret -- et le
transport s arrete avant l export : `station.export.campagne/2` porte huit
membres, aucun ne contient cette provenance.

LES TROIS PROPRIETES QUE CETTE SUITE VERROUILLE
-----------------------------------------------

  * **une absence de provenance ne devient jamais une provenance attestee.**
    Un export sans couverture rend `instrument_non_documente` et le DIT,
    au registre `NON DEMONTRABLE` -- jamais `declared`, puisque rien ne la
    declare (cas 2 et 3) ;
  * **un evaluateur absent n est ni un echec de mesure ni un score
    favorable.** Il ne produit AUCUN `FAIL` : les signaux restent
    exploitables, et ce qui tombe est ce qu on peut AFFIRMER de la facon
    dont ils ont ete obtenus (cas 3 et 10) ;
  * **`instrument_verifie` n existe pas.** Il n y a que trois niveaux, et
    aucun ne pretend qu une declaration a ete confrontee (cas 11).

ET LE PIEGE QUE LES PROFILS RENDENT EXPLICITE
---------------------------------------------

`empreinte-incoherente` et `export-altere` sont indiscernables -- une somme
fausse sur un membre intact, un membre altere sous des sommes justes. Les
deux doivent rendre `FAIL`, et l outil ne doit pas pretendre savoir lequel.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-52s %s" % (etat, numero, intitule, detail))


def lancer(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def exporter(travail: Path, profil: str) -> Path:
    cible = travail / ("%s.zip" % profil)
    code, s = lancer("tests/make_station_export.py",
                     [str(cible), "--profil", profil])
    assert code == 0, s
    return cible


def lire(z: Path, *extra: str) -> tuple[int, str, dict]:
    sortie_json = z.with_suffix(".rapport.json")
    code, s = lancer("adapters/provenance.py",
                     [str(z), "--out", str(sortie_json)] + list(extra))
    doc = json.loads(sortie_json.read_bytes()) if sortie_json.exists() else {}
    return code, s, doc


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-prov-"))
    try:
        # ---- 1. un export /3 complet est lu, et son niveau est le plus haut
        c1, s1, d1 = lire(exporter(travail, "valide"))
        pose("1", "un export /3 complet rend le niveau le plus haut",
             c1 == 0 and d1.get("provenance_level") == "instrument_declare_et_configure"
             and d1["counts"]["fail"] == 0,
             d1.get("provenance_level", "?"))

        # ---- 2. un /2 : NON DEMONTRABLE, et pas `declared` --------------
        c2, s2, d2 = lire(exporter(travail, "sans-couverture"))
        ligne = next((l for l in d2["lines"]
                      if l["intitule"] == "identite des evaluateurs"), {})
        pose("2", "un export /2 rend `instrument_non_documente`",
             c2 == 0 and d2.get("provenance_level") == "instrument_non_documente"
             and ligne.get("nature") == "NON DEMONTRABLE"
             and "not_demonstrable" in ligne.get("detail", "")
             and "non `declared`" in ligne.get("detail", ""),
             "et la ligne dit pourquoi")

        # ---- 3. un evaluateur absent n est NI un echec NI un score ------
        # La propriete la plus importante de cette suite.
        c3, s3, d3 = lire(exporter(travail, "evaluateur-absent"))
        ligne3 = next((l for l in d3["lines"]
                       if l["intitule"] == "identite des evaluateurs"), {})
        pose("3", "un evaluateur absent ne produit aucun FAIL",
             c3 == 0 and d3["counts"]["fail"] == 0
             and d3.get("provenance_level") == "instrument_non_documente"
             # Et le silence est nomme comme tel, plutot que tu.
             and ligne3.get("nature") == "NON DEMONTRABLE"
             and "ne peut pas affirmer que tout s est bien passe"
                 in ligne3.get("detail", ""),
             "0 FAIL, niveau %s, et le silence est dit"
             % d3.get("provenance_level"))

        # ---- 4. nomme mais non configure : un niveau intermediaire ------
        c4, _, d4 = lire(exporter(travail, "version-evaluateur-inconnue"))
        c5, _, d5 = lire(exporter(travail, "configuration-non-documentee"))
        pose("4", "nomme sans configuration rend `instrument_declare`",
             d4.get("provenance_level") == "instrument_declare"
             and d5.get("provenance_level") == "instrument_declare"
             and c4 == 0 and c5 == 0,
             "deux chemins, meme niveau")

        # ---- 4b. un calcul local n abaisse PAS le niveau ---------------
        # Defaut constate le 6 novembre sur un vrai export Station : un
        # signal sans modele -- un calcul local -- n a ni moteur ni prompt,
        # et ses clefs de configuration ABSENTES sont correctes. Le compter
        # comme non configure faisait retomber un `/3` complet en
        # `instrument_declare`. Le generateur le masquait, parce qu il
        # portait ces clefs a `null` au lieu de les omettre.
        c4b, _, d4b = lire(exporter(travail, "calcul-local-sans-config"))
        lc = next((l for l in d4b["lines"]
                   if l["intitule"] == "configuration des evaluateurs"), {})
        pose("4b", "un calcul local n abaisse pas le niveau",
             c4b == 0
             and d4b.get("provenance_level") == "instrument_declare_et_configure"
             and "nuls sont CORRECTS" in lc.get("detail", "")
             and d4b["chain"]["evaluator"]["calculs_locaux"] == ["stability_score"],
             "niveau %s, local nomme" % d4b.get("provenance_level"))

        # ---- 5 et 6. les deux faces du meme defaut d empreinte ---------
        c6, s6, d6 = lire(exporter(travail, "empreinte-incoherente"))
        pose("5", "une empreinte incoherente est un FAIL",
             c6 == 1 and d6["counts"]["fail"] >= 1
             and "structure et empreintes" in s6,
             "code %d" % c6)
        c7, s7, d7 = lire(exporter(travail, "export-altere"))
        pose("6", "un export altere apres les sommes est un FAIL",
             c7 == 1 and d7["counts"]["fail"] >= 1,
             "indiscernable du cas 5, et c est correct")

        # ---- 7. une execution partielle est RAPPORTEE, pas echouee -----
        c8, s8, d8 = lire(exporter(travail, "execution-partielle"))
        pose("7", "une execution partielle est rapportee sans echouer",
             c8 == 0 and d8["counts"]["fail"] == 0
             and d8.get("provenance_level") == "instrument_declare_et_configure",
             "l API declare partial ; le rapport le porte")

        # ---- 8. un signal non mesure doit dire pourquoi ----------------
        c9, s9, d9 = lire(exporter(travail, "signal-not-measured"))
        lm = next((l for l in d9["lines"]
                   if "signaux non mesures" in l["intitule"]), {})
        pose("8", "un signal nul avec son motif passe",
             c9 == 0 and lm.get("etat") == "PASS"
             and "0 mesure(s) en portent sans motif" in lm.get("detail", ""),
             lm.get("etat", "?"))

        # ---- 9. des metadonnees declarees restent DECLARE --------------
        # Le cas NORMAL, pas un defaut : rien dans l export ne permet de
        # confronter un identifiant de modele.
        c10, _, d10 = lire(exporter(travail, "metadonnees-non-verifiables"))
        declarees = [l for l in d10["lines"] if l["nature"] == "DECLARE"]
        promues = [l for l in declarees if l["etat"] == "PASS"]
        pose("9", "aucune metadonnee declaree n est rapportee comme controlee",
             c10 == 0 and declarees and not promues,
             "%d ligne(s) DECLARE, %d promue(s)" % (len(declarees), len(promues)))

        # ---- 10. aucune ligne NON DEMONTRABLE ne porte PASS ------------
        fautives = []
        for d in (d1, d2, d3, d4, d8, d9, d10):
            fautives += [l for l in d.get("lines", [])
                         if l["nature"] == "NON DEMONTRABLE" and l["etat"] == "PASS"]
        pose("10", "aucun indemontrable n est rapporte comme demontre",
             not fautives, "%d ligne(s) fautive(s)" % len(fautives))

        # ---- 11. `instrument_verifie` n existe pas ---------------------
        sys.path.insert(0, str(RACINE / "adapters"))
        import provenance
        pose("11", "il n existe aucun niveau `instrument_verifie`",
             len(provenance.NIVEAUX) == 3
             and not any("verifie" in n for n in provenance.NIVEAUX),
             " | ".join(provenance.NIVEAUX))

        # ---- 12. la limite permanente est toujours presente ------------
        toutes = all(
            any(l["intitule"].startswith("que l evaluateur declare")
                and l["etat"] == "NOT TESTED" for l in d.get("lines", []))
            for d in (d1, d2, d3, d8))
        pose("12", "la limite permanente figure sur CHAQUE rapport",
             toutes, "y compris sur un export complet")

        # ---- 13. un evaluateur partage entre signaux est DIT -----------
        # Sans cela un lecteur compte deux instruments independants la ou il
        # n y en a qu un, et croit a une confirmation croisee.
        partage = next((l for l in d1["lines"]
                        if "partages" in l["intitule"]), {})
        pose("13", "un evaluateur servant deux signaux est signale",
             partage.get("etat") == "NOT TESTED"
             and "pas des instruments independants" in partage.get("detail", ""),
             partage.get("detail", "")[:46] or "ligne absente")

        # ---- 14. le mode strict distingue l exigible du permanent ------
        c14, _, _ = lire(exporter(travail, "sans-couverture"), "--strict")
        c15, _, _ = lire(exporter(travail, "valide"), "--strict")
        pose("14", "le mode strict sort 2 sur une provenance absente",
             c14 == 2 and c15 == 0,
             "sans couverture %d, complet %d" % (c14, c15))

        # ---- 15. le rapport est exploitable dans la chaine B-3 ---------
        # Meme vocabulaire de natures : il se branche sans traduction.
        natures = {l["nature"] for l in d1["lines"]}
        pose("15", "le rapport parle le vocabulaire de B-3",
             natures <= {"CONTROLE", "DECLARE", "NON DEMONTRABLE"}
             and d1.get("schema") == "neomundi.evidence.provenance-report/1"
             and len(d1.get("does_not_establish") or []) >= 4,
             " | ".join(sorted(natures)))

        # ---- 16. aucune cle privee n est requise -----------------------
        import ast
        arbre = ast.parse((RACINE / "adapters" / "provenance.py").read_text(encoding="utf-8"))
        importes: set[str] = set()
        for n in ast.walk(arbre):
            if isinstance(n, ast.Import):
                importes.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                importes.add(n.module.split(".")[0])
        pose("16", "le lecteur de provenance n importe ni sign ni crypto",
             not (importes & {"sign", "cryptography"}),
             "importe %s" % ", ".join(sorted(importes)))

    finally:
        shutil.rmtree(travail, ignore_errors=True)

    print()
    problemes = sum(1 for e, _, _ in _bilan if e == "PROBLEME")
    inapplicables = sum(1 for e, _, _ in _bilan if e == "INAPPLICABLE")
    conformes = sum(1 for e, _, _ in _bilan if e == "OK")
    print("BILAN : %d/%d cas conformes, %d inapplicable(s), %d probleme(s)"
          % (conformes, len(_bilan) - inapplicables, inapplicables, problemes))
    if problemes:
        print()
        print("R-6 existe pour qu une provenance absente se VOIE. Si cette")
        print("suite echoue, soit une absence passe pour une provenance, soit")
        print("un evaluateur manquant se lit comme un echec de mesure -- et")
        print("dans les deux cas on affirme plus qu on ne demontre.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

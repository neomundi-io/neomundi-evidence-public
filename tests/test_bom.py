# -*- coding: utf-8 -*-
"""Un BOM UTF-8 ne doit rendre aucun fichier illisible.

D OU VIENT CETTE SUITE
----------------------

Du dossier reel recu le 30 octobre 2026 : 15 de ses 22 fichiers portent un
BOM UTF-8, parce que son collecteur est un script PowerShell et que
PowerShell en met un. Aucune de nos fixtures n en portait, donc aucun test
ne le couvrait, et trois de nos entrees cassaient dessus :

  * `receipt_import` refusait un recu JSON PARFAITEMENT VALIDE comme
    << illisible >>. Un partenaire exportant sous Windows aurait vu son
    recu rejete, et le message n aurait accuse que son fichier.
  * `sign attest` rendait une trace d execution sur une cle a BOM.
  * `timestamp upgrade --descriptor` aussi.

`json.loads` sur des OCTETS detecte un BOM tout seul ; c est sur du texte
deja decode qu il echoue. D ou la regle que cette suite verrouille :

    TOUTE entree JSON se lit en octets, jamais en texte decode.

ET UNE EXIGENCE QUI VA EN SENS INVERSE
--------------------------------------

Le BOM est retire POUR L ANALYSE SEULEMENT. L empreinte enregistree doit
rester celle du fichier TEL QU IL A ETE TRANSMIS -- sinon elle ne
correspond plus a ce que le partenaire a envoye, et la liaison se rompt
en silence. Le cas 4 verifie exactement cela, et c est le piege de ce
correctif : depouiller les octets en amont aurait paru plus propre et
aurait fausse chaque empreinte.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-58s %s" % (etat, numero, intitule, detail))


def lancer(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-bom-"))
    try:
        # ---- 1. un recu JSON a BOM est LU, pas refuse -------------------
        corps = json.dumps(
            {"coherence_score": "0.3863", "verdict": "concordant"}
        ).encode("utf-8")
        recu = travail / "recu-powershell.json"
        recu.write_bytes(BOM + corps)
        empreinte_transmise = hashlib.sha256(recu.read_bytes()).hexdigest()

        code, s1 = lancer("adapters/receipt_import.py", [
            str(recu), "--received-at", "2026-11-06T00:00:00Z",
            "--out", str(travail / "recu-importe.json")])
        pose("1", "un recu JSON a BOM est lu, non refuse",
             code == 0 and "illisible" not in s1,
             "code %d" % code)

        # ---- 2. les champs sont bien releves ----------------------------
        lu = None
        if (travail / "recu-importe.json").exists():
            lu = json.loads((travail / "recu-importe.json").read_bytes())
        pose("2", "les champs du recu a BOM sont releves",
             lu is not None and len(lu.get("fields", [])) == 2,
             "%s champ(s)" % (len(lu["fields"]) if lu else "aucun"))

        # ---- 3. aucune trace d execution, jamais ------------------------
        pose("3", "aucune trace d execution sur une entree a BOM",
             "Traceback" not in s1,
             "un verdict motive, pas une trace")

        # ---- 4. LE PIEGE : l empreinte reste celle du FICHIER TRANSMIS --
        # Depouiller le BOM avant de hacher aurait paru plus propre, et
        # aurait fausse l empreinte de chaque fichier recu d un partenaire.
        pose("4", "l empreinte reste celle du fichier TEL QUE TRANSMIS",
             lu is not None
             and lu["source"]["sha256"] == empreinte_transmise,
             "BOM compris dans l empreinte")

        # ---- 5. la meme entree SANS BOM donne une autre empreinte -------
        # Sans quoi le cas 4 passerait pour une mauvaise raison.
        sans = travail / "recu-sans-bom.json"
        sans.write_bytes(corps)
        lancer("adapters/receipt_import.py", [
            str(sans), "--received-at", "2026-11-06T00:00:00Z",
            "--out", str(travail / "recu-sans-importe.json")])
        lu2 = json.loads((travail / "recu-sans-importe.json").read_bytes())
        pose("5", "sans BOM, l empreinte DIFFERE -- le cas 4 ne passe pas a vide",
             lu2["source"]["sha256"] != empreinte_transmise
             and [c["label"] for c in lu2["fields"]]
                 == [c["label"] for c in lu["fields"]],
             "memes champs releves, empreintes distinctes")

        # ---- 6. une table de correspondance a BOM ----------------------
        archive = RACINE / "examples" / "dossier-v1" / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"
        table_src = RACINE / "examples" / "dossier-v1" / "map-comparable.json"
        recu_src = RACINE / "examples" / "dossier-v1" / "receipt-imported.json"
        if archive.is_file() and table_src.is_file():
            table = travail / "map-bom.json"
            table.write_bytes(BOM + table_src.read_bytes())
            code, s6 = lancer("adapters/reconcile.py", [
                str(recu_src), "--archive", str(archive), "--map", str(table)])
            pose("6", "une table de correspondance a BOM est lue",
                 "Traceback" not in s6 and "illisible" not in s6,
                 "code %d" % code)
        else:
            pose("6", "une table de correspondance a BOM est lue", None,
                 "dossier de demonstration absent")

        # ---- 7. un descripteur d horodatage a BOM ----------------------
        preuve = (RACINE / "examples" / "timestamp"
                  / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.ots")
        desc = (RACINE / "examples" / "timestamp"
                / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.timestamp.json")
        if preuve.is_file() and desc.is_file():
            d_bom = travail / "desc-bom.json"
            d_bom.write_bytes(BOM + desc.read_bytes())
            code, s7 = lancer("timestamp.py", [
                "verify", str(preuve), "--descriptor", str(d_bom)])
            pose("7", "un descripteur d horodatage a BOM est lu",
                 "Traceback" not in s7
                 and "descripteur de liaison" in s7
                 and "[FAIL      ] descripteur de liaison" not in s7,
                 "la liaison au descripteur tient")
        else:
            pose("7", "un descripteur d horodatage a BOM est lu", None,
                 "preuve de demonstration absente")

        # ---- 8. la regle de code : aucune lecture JSON en TEXTE --------
        # C est elle qui empeche la regression, bien plus que les cas
        # ci-dessus : un site neuf qui lirait du texte serait signale ici.
        import ast

        # `canonical.py` est exempte, et le cas 9 prouve pourquoi : c est
        # l oracle de conformite au profil, et le profil INTERDIT un BOM.
        # Y tolerer un BOM rendrait l oracle complaisant, donc inutile.
        EXEMPTES = {"canonical.py"}
        fautifs: list[str] = []
        for chemin in sorted(RACINE.glob("*.py")) + sorted(
                (RACINE / "adapters").glob("*.py")):
            if chemin.name in EXEMPTES:
                continue
            arbre = ast.parse(chemin.read_text(encoding="utf-8"))
            for n in ast.walk(arbre):
                if not (isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Attribute)
                        and n.func.attr in ("loads", "load")
                        and isinstance(n.func.value, ast.Name)
                        and n.func.value.id == "json"):
                    continue
                if not n.args:
                    continue
                rendu = ast.unparse(n.args[0])
                if "read_text" in rendu or ".decode(" in rendu:
                    fautifs.append("%s:%d  json.loads(%s)"
                                   % (chemin.name, n.lineno, rendu))
        pose("8", "aucune lecture JSON ne passe par du texte decode",
             not fautifs,
             "aucun site fautif" if not fautifs
             else "; ".join(fautifs))

        # ---- 9 et 10. l exemption de `canonical.py` est une AFFIRMATION
        # eprouvee, pas une derogation : l oracle doit refuser un BOM, et
        # le refuser par un verdict motive.
        sys.path.insert(0, str(RACINE))
        import canonical

        conforme, cause = canonical.est_conforme(BOM + b'{"a":"b"}')
        pose("9", "l oracle de canonicalisation REFUSE un BOM",
             conforme is False,
             "le profil interdit un BOM : %s" % cause[:44])

        pose("10", "et il le refuse par un verdict motive, non par une trace",
             isinstance(cause, str) and cause.strip() != "",
             "cause nommee")

        # Et la meme charge SANS BOM doit, elle, etre conforme -- sans quoi
        # le cas 9 passerait pour une raison qui n est pas le BOM.
        conforme2, cause2 = canonical.est_conforme(b'{"a":"b"}')
        pose("11", "sans BOM la meme charge est conforme -- le cas 9 est bien du BOM",
             conforme2 is True,
             cause2[:52])

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
        print("Un BOM UTF-8 est banal : PowerShell en met un, et 15 des 22")
        print("fichiers du dossier reel du 30 octobre en portent. Refuser")
        print("un fichier valide pour cette raison accuse le partenaire a")
        print("notre place.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

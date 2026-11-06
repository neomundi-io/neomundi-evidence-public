# -*- coding: utf-8 -*-
"""Ingestion d un paquet tiers : accepte, rejete, ou incomplet.

D OU VIENT CETTE SUITE
----------------------

De la condition B-3. Le dossier reel recu le 30 octobre portait 22 fichiers
et 21 empreintes declarees, toutes concordantes -- et `verify.py` l a refuse,
a juste titre : ce n est pas une archive Evidence. Rien ne convertissait une
collecte brute en objet exploitable, donc un pilote pouvait nous tendre ses
fichiers et s arreter la.

LES TROIS PROPRIETES QUE CETTE SUITE VERROUILLE
-----------------------------------------------

  * **une declaration ne devient jamais un fait.** Aucune ligne de nature
    `DECLARE` ne peut porter `PASS` -- cas 13. Sans ce verrou, il suffirait
    d ecrire << modele X >> dans un manifeste pour que le rapport le
    rapporte comme controle ;
  * **REJETE et INCOMPLET ne se confondent pas.** Une empreinte fausse est un
    refus ; un artefact annonce et non fourni est un manque que le soumetteur
    peut combler. Les traiter pareil ferait fuir un pilote de bonne foi, ou
    laisserait passer un paquet faux ;
  * **aucune cle privee, jamais.** Ingerer et verifier se font avec du
    materiel PUBLIC seulement -- cas 15, verifie statiquement sur les imports.

ET UN PIEGE QUE LES FIXTURES RENDENT EXPLICITE
----------------------------------------------

`empreinte-fausse` et `paquet-modifie` sont indiscernables pour
l ingesteur : l un est un manifeste faux sur un fichier intact, l autre un
fichier altere sous un manifeste intact. Les deux doivent etre REJETES, et
l outil ne doit PAS pretendre savoir lequel -- cas 2 et 3.
"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-54s %s" % (etat, numero, intitule, detail))


def lancer(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def fabriquer(travail: Path, profil: str) -> Path:
    cible = travail / profil
    code, s = lancer("tests/make_submission.py", [str(cible), "--profil", profil])
    assert code == 0, s
    return cible


def ingerer(paquet: Path, *extra: str) -> tuple[int, str, str]:
    code, s = lancer("adapters/ingest.py", [str(paquet)] + list(extra))
    verdict = next((l.split(":", 1)[1].strip() for l in s.splitlines()
                    if l.startswith("VERDICT")), "")
    return code, verdict, s


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-ingest-test-"))
    try:
        # ---- 1. un paquet conforme est ACCEPTE -------------------------
        v = fabriquer(travail, "valide")
        c1, verdict1, s1 = ingerer(v)
        pose("1", "un paquet conforme est ACCEPTE",
             c1 == 0 and verdict1 == "ACCEPTE" and "0 FAIL" in s1,
             "code %d, %s" % (c1, verdict1))

        # ---- 2 et 3. les deux faces du meme defaut ---------------------
        c2, verdict2, s2 = ingerer(fabriquer(travail, "empreinte-fausse"))
        pose("2", "une empreinte declaree fausse est REJETEE",
             c2 == 1 and verdict2 == "REJETE" and "discordant" in s2,
             "code %d, %s" % (c2, verdict2))

        c3, verdict3, s3 = ingerer(fabriquer(travail, "paquet-modifie"))
        pose("3", "un fichier altere apres le manifeste est REJETE",
             c3 == 1 and verdict3 == "REJETE" and "discordant" in s3,
             "indiscernable du cas 2, et c est correct")

        # ---- 4. un champ obligatoire absent ---------------------------
        c4, verdict4, s4 = ingerer(fabriquer(travail, "champ-absent"))
        pose("4", "un champ obligatoire absent est REJETE",
             c4 == 1 and verdict4 == "REJETE" and "execution" in s4,
             "code %d, %s" % (c4, verdict4))

        # ---- 5. INCOMPLET n est pas un refus --------------------------
        # Un artefact annonce et non fourni est un manque, pas une fraude :
        # le soumetteur peut le completer. Confondre les deux ferait fuir
        # un pilote de bonne foi.
        manque = fabriquer(travail, "artefact-absent")
        c5, verdict5, s5 = ingerer(manque)
        c5s, _, _ = ingerer(manque, "--strict")
        pose("5", "un artefact annonce et non fourni rend INCOMPLET",
             c5 == 0 and verdict5 == "INCOMPLET" and c5s == 2
             and "absent" in s5,
             "code %d, strict %d" % (c5, c5s))

        # ---- 6. un chemin qui remonte hors du paquet ------------------
        c6, verdict6, s6 = ingerer(fabriquer(travail, "chemin-malveillant"))
        pose("6", "un chemin remontant hors du paquet est REJETE",
             c6 == 1 and verdict6 == "REJETE"
             and ("remontee" in s6 or "refuse" in s6),
             "code %d, %s" % (c6, verdict6))

        # ---- 7. une provenance absente PLAFONNE, elle ne rejette pas --
        # La structure et les empreintes restent bonnes : le paquet est
        # exploitable. Ce qui tombe, c est ce qu on peut en AFFIRMER.
        c7, verdict7, s7 = ingerer(fabriquer(travail, "provenance-insuffisante"))
        ligne = next((l for l in s7.splitlines()
                      if "provenance de l execution" in l), "")
        pose("7", "une provenance absente plafonne sans rejeter",
             c7 == 0 and verdict7 == "ACCEPTE"
             and "NON DEMONTRABLE" in ligne
             and "not_demonstrable" in ligne,
             "ACCEPTE, provenance NON DEMONTRABLE")

        # ---- 8. un ZIP rend le MEME verdict qu un dossier -------------
        zip_src = travail / "valide"
        cible = travail / "valide.zip"
        sys.path.insert(0, str(RACINE / "tests"))
        import make_submission
        make_submission.empaqueter(zip_src, cible)
        c8, verdict8, s8 = ingerer(cible)
        pose("8", "un ZIP rend le meme verdict qu un dossier",
             c8 == 0 and verdict8 == verdict1 and "ZIP" in s8,
             "%s, deplie sous controle" % verdict8)

        # ---- 9. un ZIP piege est refuse AVANT extraction --------------
        # La borne compte : apprendre la traversee pendant l extraction
        # serait trop tard, des fichiers auraient deja ete ecrits.
        piege = travail / "piege.zip"
        with zipfile.ZipFile(piege, "w") as z:
            z.writestr("submission.json", "{}")
            e = zipfile.ZipInfo("../../evade.txt", date_time=(2026, 1, 1, 0, 0, 0))
            z.writestr(e, "evade")
        c9, verdict9, s9 = ingerer(piege)
        hors = (travail.parent / "evade.txt").exists() or (RACINE / "evade.txt").exists()
        pose("9", "un ZIP a traversee est refuse avant extraction",
             c9 == 1 and verdict9 == "REJETE" and not hors
             and "refuse" in s9,
             "aucun fichier ecrit hors du paquet")

        # ---- 10 a 12. les attestations, avec une cle de TEST ----------
        cle = travail / "k.json"
        magasin = travail / "store.json"
        code, s = lancer("sign.py", [
            "genkey", "--kid", "nm-ing-1", "--out", str(cle),
            "--trust-store-out", str(magasin), "--store-kind", "test",
            "--signer-capacity", "experimental",
            "--valid-from", "2026-11-06T00:00:00Z"])
        assert code == 0, s
        fx = travail / "fx"
        lancer("tests/make_fixture.py", [str(fx), "--profile", "v2"])
        archive = fx / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"
        jws = travail / "a.jws"
        code, s = lancer("sign.py", [
            "attest", "--archive", str(archive), "--key", str(cle),
            "--out", str(jws), "--attested-at", "2026-11-06T12:00:00Z"])
        assert code == 0, s

        def paquet_atteste(nom: str, octets_jws: bytes) -> Path:
            # Dans SON dossier : deplacer `travail/valide` le detruirait, et
            # les cas 13 et 14 le relisent. Defaut rencontre a l ecriture.
            cible = travail / nom
            code, s = lancer("tests/make_submission.py",
                             [str(cible), "--profil", "valide"])
            assert code == 0, s
            (cible / "artefacts" / "att.jws").write_bytes(octets_jws)
            (cible / "artefacts" / "sujet.zip").write_bytes(archive.read_bytes())
            m = json.loads((cible / "submission.json").read_bytes())
            for p, role in (("artefacts/att.jws", "attestation"),
                            ("artefacts/sujet.zip", "recording")):
                o = (cible / p).read_bytes()
                m["artifacts"].append({
                    "path": p, "sha256": hashlib.sha256(o).hexdigest(),
                    "bytes": len(o), "role": role, "media_type": None})
            m["attestations"] = [{"jws_path": "artefacts/att.jws",
                                  "subject_path": "artefacts/sujet.zip",
                                  "trust_store_declared": None}]
            (cible / "submission.json").write_bytes(
                (json.dumps(m, ensure_ascii=False, indent=2,
                            sort_keys=True) + "\n").encode("utf-8"))
            return cible

        bon = paquet_atteste("atteste", jws.read_bytes())
        c10, verdict10, s10 = ingerer(bon, "--trust-store", str(magasin),
                                      "--allow-test-keys")
        # `--allow-test-keys` n est pas une option d `ingest.py` : on verifie
        # qu une option inconnue est refusee plutot que silencieusement ignoree.
        pose("10", "une option inconnue est refusee, non ignoree",
             c10 == 2 and "unrecognized arguments" in s10,
             "argparse sort 2")

        c11, verdict11, s11 = ingerer(bon, "--trust-store", str(magasin))
        ligne_sig = next((l for l in s11.splitlines()
                          if "signatures existantes" in l), "")
        # La cle est de statut `test` : le verificateur la refuse sans
        # --allow-test-keys, et `ingest.py` ne le lui passe PAS. Un paquet
        # signe par une cle de test ne doit pas etre accepte.
        pose("11", "une signature par cle de TEST ne fait pas accepter",
             c11 == 1 and verdict11 == "REJETE" and "exit 1" in ligne_sig,
             "la cle de test n accorde rien")

        casse = paquet_atteste("atteste-casse", jws.read_bytes())
        j = casse / "artefacts" / "att.jws"
        t = j.read_bytes()
        i = t.rfind(b".") + 5
        t = t[:i] + (b"B" if t[i:i + 1] != b"B" else b"C") + t[i + 1:]
        j.write_bytes(t)
        m = json.loads((casse / "submission.json").read_bytes())
        for a in m["artifacts"]:
            if a["path"] == "artefacts/att.jws":
                a["sha256"] = hashlib.sha256(t).hexdigest()
                a["bytes"] = len(t)
        (casse / "submission.json").write_bytes(
            (json.dumps(m, ensure_ascii=False, indent=2,
                        sort_keys=True) + "\n").encode("utf-8"))
        c12, verdict12, _ = ingerer(casse, "--trust-store", str(magasin))
        pose("12", "une signature alteree est REJETEE",
             c12 == 1 and verdict12 == "REJETE",
             "code %d" % c12)

        # Une attestation declaree SANS magasin fourni : incomplet, pas
        # accepte. L operateur peut fournir le magasin.
        c12b, verdict12b, s12b = ingerer(bon)
        pose("12b", "une attestation sans magasin rend INCOMPLET",
             c12b == 0 and verdict12b == "INCOMPLET"
             and "aucun magasin" in s12b,
             "le magasin vient de l operateur")

        # ---- 13. aucune ligne DECLARE ne porte PASS -------------------
        rapport = travail / "r.json"
        ingerer(v, "--out", str(rapport))
        doc = json.loads(rapport.read_bytes())
        fautives = [l for l in doc["lines"]
                    if l["nature"] in ("DECLARE", "NON DEMONTRABLE")
                    and l["etat"] == "PASS"]
        pose("13", "aucune declaration n est rapportee comme controlee",
             not fautives and doc["verdict"] == "ACCEPTE",
             "%d ligne(s) fautive(s)" % len(fautives))

        # ---- 14. le rapport est exploitable, et dit ses limites -------
        pose("14", "le rapport porte son schema et ses limites",
             doc.get("schema") == "neomundi.evidence.ingestion-report/1"
             and len(doc.get("does_not_establish") or []) >= 4
             and "declared_verbatim" in doc
             and doc["declared_verbatim"]["execution"]["model_declared"],
             "%d limite(s) enoncee(s)" % len(doc["does_not_establish"]))

        # ---- 15. aucune cle privee n est requise ---------------------
        # Verifie STATIQUEMENT : `ingest.py` n importe ni `sign.py` ni
        # `cryptography`. Un ingesteur qui aurait besoin d un secret ne
        # pourrait pas tourner chez un tiers.
        arbre = ast.parse((RACINE / "adapters" / "ingest.py").read_text(encoding="utf-8"))
        importes: set[str] = set()
        for n in ast.walk(arbre):
            if isinstance(n, ast.Import):
                importes.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                importes.add(n.module.split(".")[0])
        interdits = importes & {"sign", "cryptography"}
        pose("15", "l ingesteur n importe ni sign.py ni cryptography",
             not interdits, "importe %s" % ", ".join(sorted(importes)))

    finally:
        shutil.rmtree(travail, ignore_errors=True)
        for parasite in ("evade.txt",):
            (RACINE / parasite).unlink(missing_ok=True)

    print()
    problemes = sum(1 for e, _, _ in _bilan if e == "PROBLEME")
    inapplicables = sum(1 for e, _, _ in _bilan if e == "INAPPLICABLE")
    conformes = sum(1 for e, _, _ in _bilan if e == "OK")
    print("BILAN : %d/%d cas conformes, %d inapplicable(s), %d probleme(s)"
          % (conformes, len(_bilan) - inapplicables, inapplicables, problemes))
    if problemes:
        print()
        print("Un pilote exterieur depend de ces verdicts pour savoir si son")
        print("paquet est exploitable. Si cette suite echoue, soit un paquet")
        print("faux passe, soit un paquet de bonne foi est refuse -- et dans")
        print("les deux cas la declaration et le fait se sont melanges.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

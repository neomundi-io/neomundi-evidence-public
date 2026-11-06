# -*- coding: utf-8 -*-
"""Tests de l horodatage independant. DETERMINISTES ET HORS RESEAU.

    python tests/test_timestamp.py

Aucun appel reseau. La preuve de reference est celle commitee dans
`examples/timestamp/`, obtenue une fois des quatre calendriers publics et
figee depuis : une suite de tests qui depend du reseau n est pas une suite
de tests, c est une sonde.

Les tests d INTEGRATION -- ceux qui touchent reellement les calendriers --
sont separes, dans `tests/test_timestamp_network.py`, et ne tournent jamais
en integration continue.

CE QUE CES TESTS EPROUVENT
--------------------------

La LIAISON, qui est la seule chose que notre outil demontre : la preuve
s engage-t-elle sur l empreinte du sujet ? Et le refus, dans toutes les
formes de malformation qu on a su fabriquer.

Ils n eprouvent PAS le temps : nous ne le verifions pas, et un test qui
pretendrait le faire serait faux.

Bibliotheque standard seule. `opentimestamps`, s il est present, permet
trois cas de plus -- notamment une preuve CONFIRMEE synthetique, qu on ne
peut pas obtenir autrement sans attendre des heures.
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
OUTIL = RACINE / "timestamp.py"
PREUVE = RACINE / "examples" / "timestamp" / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.ots"
SUJET = RACINE / "examples" / "attestation" / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws"
DESCRIPTEUR = (RACINE / "examples" / "timestamp"
               / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.timestamp.json")

# La preuve REELLEMENT confirmee par la chaine, obtenue le 6 novembre :
# blocs Bitcoin 974714 et 974715. Elle s eprouve hors ligne, sans aucune
# dependance -- et c est la seule piece qui demontre C-4.
CONFIRMEE = (RACINE / "examples" / "timestamp"
             / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.confirmed.ots")
CONFIRMEE_D = (RACINE / "examples" / "timestamp"
               / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.confirmed.timestamp.json")

MAGIE = bytes.fromhex("004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294")


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def lancer(args: list[str]) -> tuple[int, str]:
    fini = subprocess.run([sys.executable, str(OUTIL)] + args, capture_output=True,
                          text=True, check=False, encoding="utf-8", errors="replace")
    return fini.returncode, fini.stdout + fini.stderr


def verifier(preuve: Path, sujet: Path | None = None, extra: list[str] | None = None):
    args = ["verify", str(preuve)]
    if sujet is not None:
        args += ["--subject", str(sujet)]
    return lancer(args + (extra or []))


def etat(sortie: str, intitule: str) -> str:
    for ligne in sortie.splitlines():
        if ligne.startswith("[") and "] " in ligne:
            e, _, reste = ligne[1:].partition("] ")
            if reste.split(" - ")[0].strip() == intitule:
                return e.strip()
    return "absent"


def officielle_presente() -> bool:
    try:
        import opentimestamps.core.timestamp  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def preuve_confirmee_synthetique(cible: Path, empreinte: bytes) -> Path | None:
    """Fabrique une preuve portant une attestation Bitcoin, hors reseau.

    On ne peut pas obtenir une vraie preuve confirmee en quelques minutes :
    la chaine met des heures. Celle-ci est SYNTHETIQUE et sert uniquement a
    eprouver la logique PENDING -> CONFIRMED. Elle n atteste evidemment
    aucune date -- et c est pour cela qu aucun test ne pretend le contraire.
    """
    if not officielle_presente():
        return None
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
    from opentimestamps.core.op import OpSHA256
    from opentimestamps.core.serialize import BytesSerializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

    timestamp = Timestamp(empreinte)
    timestamp.attestations.add(BitcoinBlockHeaderAttestation(800000))
    contexte = BytesSerializationContext()
    DetachedTimestampFile(OpSHA256(), timestamp).serialize(contexte)
    cible.write_bytes(contexte.getbytes())
    return cible


# --------------------------------------------------------------------------


def main() -> int:
    resultats: list[tuple[str, str, object, str]] = []

    def pose(numero, intitule, reussi, constat):
        resultats.append((numero, intitule, reussi, constat))

    if not PREUVE.is_file():
        print("preuve de reference absente : %s" % PREUVE)
        return 2

    octets = PREUVE.read_bytes()
    empreinte_sujet = hashlib.sha256(SUJET.read_bytes()).digest()
    travail = Path(tempfile.mkdtemp(prefix="timestamp-"))

    print("Tests de l horodatage -- HORS RESEAU")
    print("preuve de reference : %s (%d octets)" % (PREUVE.name, len(octets)))
    print("empreinte           : %s\n" % sha256(octets))

    try:
        # ---- 1. la liaison, cas positif -------------------------------
        code, s = verifier(PREUVE, SUJET)
        pose("1", "preuve authentique, sujet juste : liaison etablie",
             code == 0 and etat(s, "liaison a l empreinte du sujet") == "PASS",
             "liaison PASS, code %d" % code)

        # ---- 2. PENDING n est pas une preuve de temps -----------------
        pose("2", "PENDING : le temps reste NON atteste",
             etat(s, "attestation confirmee par la chaine") == "NOT TESTED"
             and etat(s, "temps verifie par un tiers") == "NOT TESTED",
             "les deux lignes temporelles sont NOT TESTED")

        # ---- 3. aucune revendication eIDAS ----------------------------
        pose("3", "aucun horodatage qualifie eIDAS revendique",
             etat(s, "qualification eIDAS") == "NOT TESTED" and "AUCUNE" in s,
             "ligne presente et explicite")

        # ---- 4. mauvais sujet : la liaison ECHOUE ---------------------
        autre = travail / "autre.txt"
        autre.write_text("un autre contenu", encoding="utf-8")
        code, s4 = verifier(PREUVE, autre)
        pose("4", "sujet different : la liaison echoue",
             code == 1 and etat(s4, "liaison a l empreinte du sujet") == "FAIL",
             "FAIL sur la liaison, code %d" % code)

        # ---- 5. sujet non fourni : NOT TESTED, pas FAIL ---------------
        code, s5 = verifier(PREUVE)
        pose("5", "sujet non fourni : NOT TESTED et non FAIL",
             code == 0 and etat(s5, "liaison a l empreinte du sujet") == "NOT TESTED",
             "la liaison n est pas niee, elle n est pas eprouvee")

        # ---- 6. strict : PENDING -> code 2 ----------------------------
        code, s6 = verifier(PREUVE, SUJET, ["--strict"])
        memes = [l for l in s6.splitlines() if l.startswith("[")] == \
                [l for l in s.splitlines() if l.startswith("[")]
        pose("6", "strict : code 2 sur PENDING, et AUCUN verdict change",
             code == 2 and "attestation confirmee" in s6,
             "code 2 ; verdicts identiques : %s" % ("oui" if memes else "NON"))

        # ---- 7. strict ne change aucun verdict (compare ligne a ligne)
        code_a, sa = verifier(PREUVE, autre)
        code_b, sb = verifier(PREUVE, autre, ["--strict"])
        lignes_a = [l for l in sa.splitlines() if l.startswith("[")]
        lignes_b = [l for l in sb.splitlines() if l.startswith("[")]
        pose("7", "strict n altere aucune ligne de controle",
             lignes_a == lignes_b and code_a == 1 and code_b == 1,
             "%d lignes identiques ; un FAIL l emporte sur le strict"
             % len(lignes_a))

        # ---- 8 a 12. preuves malformees -------------------------------
        malformees = [
            ("magie absente", b"PAS UNE PREUVE" + octets[31:]),
            ("preuve tronquee", octets[:40]),
            ("preuve vide", b""),
            ("version majeure inconnue", MAGIE + bytes([9]) + octets[32:]),
            ("operation de hachage inconnue", MAGIE + bytes([1, 0x02]) + octets[33:]),
        ]
        refuses = []
        for nom, contenu in malformees:
            cible = travail / ("malforme-%s.ots" % nom.replace(" ", "-"))
            cible.write_bytes(contenu)
            code, sm = verifier(cible, SUJET)
            # Un FAIL motive, et surtout AUCUNE trace d appels.
            motive = code == 1 and "Traceback" not in sm
            refuses.append((nom, motive))
        pose("8", "cinq preuves malformees : FAIL motive, aucune trace",
             all(m for _, m in refuses),
             "%d/5 refusees proprement" % sum(1 for _, m in refuses if m))

        # ---- 13. preuve inexistante -----------------------------------
        code, s13 = verifier(travail / "jamais-ecrite.ots", SUJET)
        pose("13", "preuve introuvable : FAIL motive",
             code == 1 and "introuvable" in s13 and "Traceback" not in s13,
             "FAIL motive")

        # ---- 14. descripteur concordant --------------------------------
        code, s14 = verifier(PREUVE, SUJET, ["--descriptor", str(DESCRIPTEUR)])
        pose("14", "descripteur concordant : PASS",
             code == 0 and etat(s14, "descripteur de liaison") == "PASS",
             "descripteur PASS")

        # ---- 15. descripteur qui MENT sur le sujet ---------------------
        menteur = json.loads(DESCRIPTEUR.read_text(encoding="utf-8"))
        menteur["subject_sha256"] = "0" * 64
        chemin_menteur = travail / "menteur.json"
        chemin_menteur.write_text(json.dumps(menteur), encoding="utf-8")
        code, s15 = verifier(PREUVE, SUJET, ["--descriptor", str(chemin_menteur)])
        pose("15", "descripteur qui ment sur le sujet : FAIL",
             code == 1 and etat(s15, "descripteur de liaison") == "FAIL",
             "le descripteur est confronte a la preuve, pas cru")

        # ---- 16. descripteur de schema inconnu -------------------------
        inconnu = {**json.loads(DESCRIPTEUR.read_text(encoding="utf-8")),
                   "schema": "autre/99"}
        chemin_inconnu = travail / "inconnu.json"
        chemin_inconnu.write_text(json.dumps(inconnu), encoding="utf-8")
        code, s16 = verifier(PREUVE, SUJET, ["--descriptor", str(chemin_inconnu)])
        pose("16", "descripteur de schema inconnu : refuse",
             code == 1 and etat(s16, "descripteur de liaison") == "FAIL",
             "refuse, pas interprete")

        # ---- 17. descripteur illisible ---------------------------------
        chemin_casse = travail / "casse.json"
        chemin_casse.write_bytes(b"{ pas du json")
        code, s17 = verifier(PREUVE, SUJET, ["--descriptor", str(chemin_casse)])
        pose("17", "descripteur illisible : FAIL motive, aucune trace",
             code == 1 and "Traceback" not in s17,
             "FAIL motive")

        # ---- 18. rapport lisible par machine ---------------------------
        rapport = travail / "r.json"
        verifier(PREUVE, SUJET, ["--json", str(rapport)])
        r = json.loads(rapport.read_text(encoding="utf-8"))
        pose("18", "rapport machine : etats distincts et limites dites",
             r["schema"] == "neomundi.evidence.timestamp-report/1"
             and r["state"] == "pending"
             and r["committed_sha256"] == r["subject_sha256"]
             and set(r["counts"]) == {"pass", "fail", "not_tested"}
             and len(r["does_not_establish"]) >= 3,
             "state=%s, %d limite(s) dites" % (r["state"], len(r["does_not_establish"])))

        # ---- 19. inspect hors ligne ------------------------------------
        code, s19 = lancer(["inspect", str(PREUVE)])
        pose("19", "inspect : lit la liaison et dit PENDING",
             code == 0 and sha256(SUJET.read_bytes()) in s19
             and "pas une preuve de temps" in s19,
             "empreinte engagee affichee, PENDING dit")

        # ---- 20. l empreinte est lue SANS la bibliotheque officielle ---
        # On bloque `opentimestamps` par le chemin d import, et la LIAISON
        # doit rester etablie : c est la propriete qui fonde l architecture.
        import os

        faux = travail / "sans-ots"
        (faux / "opentimestamps").mkdir(parents=True, exist_ok=True)
        (faux / "opentimestamps" / "__init__.py").write_text(
            "raise ImportError('bloque pour le test')\n", encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(faux)
        fini = subprocess.run(
            [sys.executable, str(OUTIL), "verify", str(PREUVE), "--subject", str(SUJET)],
            capture_output=True, text=True, check=False, encoding="utf-8",
            errors="replace", env=env)
        s20 = fini.stdout + fini.stderr
        pose("20", "liaison etablie SANS `opentimestamps`",
             fini.returncode == 0
             and etat(s20, "liaison a l empreinte du sujet") == "PASS"
             and etat(s20, "arbre des attestations") == "NOT TESTED",
             "liaison PASS sans dependance, arbre NOT TESTED")

        # ---- 21. strict sans la bibliotheque : code 2 ------------------
        fini2 = subprocess.run(
            [sys.executable, str(OUTIL), "verify", str(PREUVE), "--subject", str(SUJET),
             "--strict"],
            capture_output=True, text=True, check=False, encoding="utf-8",
            errors="replace", env=env)
        pose("21", "strict sans la bibliotheque : code 2, jamais PASS",
             fini2.returncode == 2,
             "code %d" % fini2.returncode)

        # ---- 22. preuve CONFIRMEE synthetique --------------------------
        confirmee = preuve_confirmee_synthetique(travail / "confirmee.ots",
                                                 empreinte_sujet)
        if confirmee is None:
            pose("22", "preuve confirmee : la ligne passe a PASS", None,
                 "`opentimestamps` absent : fixture non constructible")
            pose("23", "preuve confirmee + strict : code 0", None,
                 "`opentimestamps` absent")
        else:
            code, s22 = verifier(confirmee, SUJET)
            pose("22", "preuve confirmee : la ligne passe a PASS",
                 code == 0
                 and etat(s22, "attestation confirmee par la chaine") == "PASS"
                 and etat(s22, "temps verifie par un tiers") == "NOT TESTED",
                 "confirmee PASS, mais le TEMPS reste NOT TESTED")
            code, s23 = verifier(confirmee, SUJET, ["--strict"])
            pose("23", "preuve confirmee + strict : code 0",
                 code == 0, "code %d" % code)

        # ---- 24. une preuve confirmee ne dispense PAS du tiers ---------
        if confirmee is not None:
            pose("24", "meme confirmee, le temps n est jamais verifie ici",
                 "ots verify" in s22,
                 "la commande du client officiel est donnee")
        else:
            pose("24", "meme confirmee, le temps n est jamais verifie ici", None,
                 "`opentimestamps` absent")

        # ---- 26 a 29. la preuve REELLEMENT confirmee du depot --------
        # Hors ligne, sans dependance. C est la piece de C-4 : tant qu elle
        # n existait pas, << horodate >> n etait pas ecrivable.
        import json as _json

        code, s26 = verifier(CONFIRMEE, SUJET,
                             ["--descriptor", str(CONFIRMEE_D)])
        pose("26", "preuve REELLE confirmee : 5 PASS, 0 FAIL, 2 NOT TESTED",
             code == 0
             and "BILAN : 5 PASS, 0 FAIL, 2 NOT TESTED" in s26
             and etat(s26, "attestation confirmee par la chaine") == "PASS",
             "blocs Bitcoin lus dans les octets du depot")

        # Un `upgrade` qui changerait l objet engage substituerait ce qui est
        # atteste. Les deux preuves doivent engager le MEME.
        _, i_pend = lancer(["inspect", str(PREUVE)])
        _, i_conf = lancer(["inspect", str(CONFIRMEE)])

        def _engagee(sortie: str) -> str:
            for ligne in sortie.splitlines():
                if "empreinte engagee" in ligne:
                    return ligne.split(":")[-1].strip()
            return ""

        pose("27", "l upgrade n a PAS change l objet engage",
             _engagee(i_pend) == _engagee(i_conf) != "",
             "meme empreinte engagee de part et d autre")

        d_conf = _json.loads(CONFIRMEE_D.read_text(encoding="utf-8"))
        pose("28", "`upgraded_from` designe les octets de l anterieure",
             d_conf.get("upgraded_from") == sha256(PREUVE.read_bytes()),
             "l anterieure n est pas detruite : elle reste une piece")

        pose("29", "confirmee, le TEMPS reste NON verifie et eIDAS NON revendique",
             etat(s26, "temps verifie par un tiers") == "NOT TESTED"
             and etat(s26, "qualification eIDAS") == "NOT TESTED"
             and "ots verify" in s26,
             "une attestation Bitcoin n est pas une date que NOUS verifions")

        # ---- 25. aucune primitive reseau dans le chemin de verification
        import ast

        arbre = ast.parse(OUTIL.read_text(encoding="utf-8"))
        fonctions = {n.name: n for n in ast.walk(arbre)
                     if isinstance(n, ast.FunctionDef)}
        reseau = []
        for nom in ("verifier", "rendre", "empreinte_engagee", "lire_attestations",
                    "charge_officielle", "inspect"):
            if nom not in fonctions:
                continue
            source = ast.unparse(fonctions[nom])
            reseau += [m for m in ("RemoteCalendar", "urlopen", "requests",
                                   "socket", "submit(") if m in source]
        pose("25", "le chemin de verification ne touche AUCUN reseau",
             not reseau,
             "aucune primitive reseau" if not reseau else "trouve : %s" % reseau)

    finally:
        shutil.rmtree(travail, ignore_errors=True)

    # ------------------------------------------------------------------
    print()
    echecs, inapplicables = [], []
    for numero, intitule, reussi, constat in resultats:
        if reussi is None:
            etiquette = "INAPPLIC."
            inapplicables.append("%s %s" % (numero, intitule))
        else:
            etiquette = "OK" if reussi else "PROBLEME"
            if not reussi:
                echecs.append("%s %s" % (numero, intitule))
        print("[%-9s] %-3s %-56s %s"
              % (etiquette, numero, intitule[:56], constat[:68]))

    eprouves = len(resultats) - len(inapplicables)
    print("\nBILAN : %d/%d cas conformes, %d inapplicable(s)"
          % (eprouves - len(echecs), eprouves, len(inapplicables)))
    for i in inapplicables:
        print("  inapplicable : %s" % i)
    for e in echecs:
        print("  PROBLEME : %s" % e)

    if not echecs:
        print("\nCe que ces tests etablissent : la LIAISON entre une preuve et son")
        print("sujet, et le refus de toute preuve malformee -- sans aucune dependance.")
        print("Ce qu ils n etablissent pas : le TEMPS. Nous ne le verifions pas, et")
        print("une preuve PENDING n atteste aucune date.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""Tests de securite de l attestation detachee.

    python tests/test_attestation.py <archive_evidence.zip>

Vingt-deux cas. Les dix premiers sont ceux du cahier des charges ; les douze
suivants decoulent de la conception et n y figuraient pas.

Toutes les cles sont EPHEMERES : generees dans un repertoire temporaire a
l execution, et effacees a la fin. Aucune cle privee n existe dans le depot,
et un test le verifie.

Deux cas meritent d etre lus avant les autres :

  * **cas 7** -- une archive entierement recalculee apres suppression d une
    observation. C est la limite DECLAREE de la suite de falsification depuis
    le 5 novembre : rien a l interieur de l archive ne la contredit. Une
    attestation signee sur l empreinte d origine la detecte. C est la
    premiere fois qu une limite declaree du produit se referme.

  * **cas 22** -- une charge non conforme au profil de canonicalisation, mais
    correctement signee. Le profil doit echouer et la signature passer : s ils
    echouaient ensemble, les deux controles n en seraient qu un.

Bibliotheque standard, plus `cryptography` pour signer.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
SIGN = RACINE / "sign.py"
VERIFY_ATT = RACINE / "verify_attestation.py"
BIND = RACINE / "bind.py"
VERIFY = RACINE / "verify.py"

QUAND = "2026-11-05T14:00:00Z"
DEPUIS = "2026-11-05T00:00:00Z"


def b64u(octets: bytes) -> str:
    return base64.urlsafe_b64encode(octets).rstrip(b"=").decode("ascii")


def deb64u(valeur: str) -> bytes:
    return base64.urlsafe_b64decode(valeur + "=" * (-len(valeur) % 4))


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def lancer(commande: list[str], env: dict | None = None) -> tuple[int, str]:
    fini = subprocess.run(commande, capture_output=True, text=True, check=False,
                          encoding="utf-8", errors="replace", env=env)
    return fini.returncode, fini.stdout + fini.stderr


def verifier(jws: Path, archive: Path | None, magasin: Path | None,
             extra: list[str] | None = None, env: dict | None = None) -> tuple[int, str]:
    commande = [sys.executable, str(VERIFY_ATT), str(jws)]
    if archive is not None:
        commande += ["--archive", str(archive)]
    if magasin is not None:
        commande += ["--trust-store", str(magasin)]
    return lancer(commande + (extra or []), env)


def etat(sortie: str, intitule: str) -> str:
    """L etat de la ligne de controle nommee, ou 'absent'."""
    for ligne in sortie.splitlines():
        if ligne.startswith("[") and "] " in ligne:
            e, _, reste = ligne[1:].partition("] ")
            if reste.split(" - ")[0].strip() == intitule:
                return e.strip()
    return "absent"


def motif_bind(sortie: str) -> str:
    """Le premier FAIL d une sortie de `bind.py`, pour expliquer un echec."""
    return next((l.strip() for l in sortie.splitlines() if l.startswith("[FAIL")), "")


def niveau(sortie: str) -> str:
    """Le niveau REELLEMENT atteint, ou "aucun".

    Le verificateur ecrit deux formulations : le nom du niveau quand il est
    atteint, et une phrase commencant par AUCUN quand il ne l est pas. Les
    confondre faisait echouer deux cas dont le comportement etait pourtant
    correct -- c etait ce lecteur-ci qui etait faux, pas l outil.
    """
    for ligne in sortie.splitlines():
        if ligne.startswith("Niveau atteint :"):
            valeur = ligne.split(":", 1)[1].strip()
            return "aucun" if valeur.upper().startswith("AUCUN") else valeur
    return "aucun"


def ecris_jws(cible: Path, entete: dict, charge_octets: bytes, signature: bytes) -> Path:
    """Reassemble un JWS a partir de ses trois morceaux, tels quels.

    Volontairement sans recanonicaliser : certains cas ont besoin d ecrire une
    charge qui n est PAS canonique, ou un en-tete falsifie.
    """
    e = b64u(json.dumps(entete, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    cible.write_text(e + "." + b64u(charge_octets) + "." + b64u(signature) + "\n",
                     encoding="ascii")
    return cible


def morceaux(jws: Path) -> tuple[dict, bytes, bytes, str, str]:
    e, c, s = jws.read_text(encoding="ascii").strip().split(".")
    return json.loads(deb64u(e)), deb64u(c), deb64u(s), e, c


# --------------------------------------------------------------------------


class Banc:
    """Le decor : une cle ephemere, un magasin, une attestation valide."""

    def __init__(self, archive: Path, travail: Path) -> None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        self.ed25519 = ed25519
        self.serialization = serialization
        self.archive = archive
        self.travail = travail
        self.privee_fichier = travail / "privee.json"
        self.magasin = travail / "magasin.json"
        self.jws = travail / "valide.jws"

        code, sortie = lancer([
            sys.executable, str(SIGN), "genkey", "--kid", "nm-ev-test-a",
            "--out", str(self.privee_fichier), "--trust-store-out", str(self.magasin),
            "--valid-from", DEPUIS, "--key-notes", "cle ephemere de test",
        ])
        if code != 0:
            raise SystemExit("genkey a echoue :\n" + sortie)

        code, sortie = lancer([
            sys.executable, str(SIGN), "attest", "--archive", str(archive),
            "--key", str(self.privee_fichier), "--attested-at", QUAND,
            "--kind", "retrospective", "--out", str(self.jws),
        ])
        if code != 0:
            raise SystemExit("attest a echoue :\n" + sortie)

        self.privee = self.ed25519.Ed25519PrivateKey.from_private_bytes(
            deb64u(json.loads(self.privee_fichier.read_text(encoding="utf-8"))["d"])
        )

    def signe(self, entete: dict, charge_octets: bytes) -> bytes:
        e = b64u(json.dumps(entete, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        return self.privee.sign((e + "." + b64u(charge_octets)).encode("ascii"))

    def resigne(self, cible: Path, charge: dict, entete: dict | None = None,
                canonique: bool = True) -> Path:
        """Reecrit une attestation, resignee pour de vrai."""
        octets = (
            json.dumps(charge, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")
            if canonique
            else json.dumps(charge, indent=2, ensure_ascii=False).encode("utf-8")
        )
        tete = entete or {"alg": "EdDSA", "kid": charge["key_id"], "typ": "JOSE"}
        return ecris_jws(cible, tete, octets, self.signe(tete, octets))

    def charge(self) -> dict:
        return json.loads(morceaux(self.jws)[1])

    def magasin_modifie(self, nom: str, transforme) -> Path:
        m = json.loads(self.magasin.read_text(encoding="utf-8"))
        transforme(m)
        cible = self.travail / nom
        cible.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        return cible

    def archive_sans_une_observation(self) -> Path:
        """Le cas 7 : une observation retiree, tout recalcule a l interieur.

        Decomptes du manifeste et sommes de controle refaits, de sorte que
        l archive est interieurement parfaite. C est exactement ce que la
        suite de falsification declare indetectable.
        """
        cible = self.travail / "amputee.zip"
        with zipfile.ZipFile(self.archive) as z:
            membres = {n: z.read(n) for n in z.namelist()}

        obs = [l for l in membres["observations.jsonl"].splitlines() if l.strip()]
        retiree = json.loads(obs[0])["payload"]["observation_id"]
        membres["observations.jsonl"] = b"\n".join(obs[1:]) + b"\n"
        for membre in ("measurements.jsonl", "reference_evaluations.jsonl",
                       "replay_provenance.jsonl"):
            if membre not in membres:
                continue
            gardees = [
                l for l in membres[membre].splitlines()
                if l.strip() and json.loads(l)["payload"].get("observation_id") != retiree
            ]
            membres[membre] = b"\n".join(gardees) + b"\n"

        manifeste = json.loads(membres["manifest.json"])
        decomptes = manifeste.get("decomptes", {})
        for cle, membre in (("observations", "observations.jsonl"),
                            ("mesures", "measurements.jsonl"),
                            ("evaluations", "reference_evaluations.jsonl"),
                            ("provenances_de_rejeu", "replay_provenance.jsonl")):
            if cle in decomptes and membre in membres:
                decomptes[cle] = len(
                    [l for l in membres[membre].splitlines() if l.strip()]
                )
        membres["manifest.json"] = json.dumps(
            manifeste, ensure_ascii=False, indent=2
        ).encode("utf-8")

        couverts = [n for n in membres if n != "checksums.sha256"]
        membres["checksums.sha256"] = "".join(
            "%s  %s\n" % (sha256(membres[n]), n) for n in couverts
        ).encode("utf-8")

        with zipfile.ZipFile(cible, "w", compression=zipfile.ZIP_STORED) as z:
            for nom in sorted(membres):
                info = zipfile.ZipInfo(nom, date_time=(2026, 11, 5, 0, 0, 0))
                z.writestr(info, membres[nom])
        return cible


# --------------------------------------------------------------------------
# Les cas
# --------------------------------------------------------------------------


def cas(banc: Banc) -> list[tuple[str, str, bool, str]]:
    """Rend (numero, intitule, reussi, constat) pour chaque cas."""
    r = []
    T = banc.travail

    def pose(numero, intitule, reussi, constat):
        """`reussi` a trois valeurs : True, False, et None = INAPPLICABLE.

        Un cas inapplicable n est NI un succes NI un echec : il n a pas pu
        etre eprouve dans cet environnement, et le dire est la seule reponse
        honnete.
        """
        r.append((numero, intitule, reussi if reussi is None else bool(reussi), constat))

    # ---- 1. archive valide, signature valide, cle connue -------------------
    code, s = verifier(banc.jws, banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("1", "archive valide, signature valide, cle connue",
         code == 0 and niveau(s) == "cryptographically_attested",
         "niveau %s" % niveau(s))

    # ---- 2. archive modifiee apres signature ------------------------------
    modifiee = T / "modifiee.zip"
    modifiee.write_bytes(banc.archive.read_bytes() + b"\x00")
    code, s = verifier(banc.jws, modifiee, banc.magasin, ["--allow-test-keys"])
    pose("2", "archive modifiee apres signature",
         code != 0 and etat(s, "concordance avec l archive") == "FAIL"
         and etat(s, "signature cryptographique") == "PASS",
         "signature PASS, concordance FAIL -- la signature n est pas en cause")

    # ---- 3. signature falsifiee -------------------------------------------
    entete, charge_octets, signature, _, _ = morceaux(banc.jws)
    fausse = bytearray(signature)
    fausse[0] ^= 0xFF
    code, s = verifier(ecris_jws(T / "faux-sig.jws", entete, charge_octets, bytes(fausse)),
                       banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("3", "signature falsifiee",
         code != 0 and etat(s, "signature cryptographique") == "FAIL",
         etat(s, "signature cryptographique"))

    # ---- 4. cle publique inconnue -----------------------------------------
    inconnu = banc.magasin_modifie(
        "magasin-autre-kid.json",
        lambda m: m["keys"][0].update({"kid": "nm-ev-test-inconnue"}),
    )
    code, s = verifier(banc.jws, banc.archive, inconnu, ["--allow-test-keys"])
    pose("4", "cle publique inconnue",
         code == 0 and etat(s, "signature cryptographique") == "NOT TESTED"
         and etat(s, "identite de confiance") == "NOT TESTED"
         and niveau(s) == "aucun",
         "NOT TESTED et non FAIL : la signature est peut-etre valide")

    # ---- 5. signature valide, ancrage externe absent -----------------------
    code, s = verifier(banc.jws, banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("5", "signature valide, ancrage externe absent",
         niveau(s) == "cryptographically_attested" and etat(s, "ancrage tiers") == "NOT TESTED",
         "niveau atteint, ancrage NOT TESTED")

    # ---- 6. ancrage present mais non concordant ---------------------------
    avec_ancrage = copy.deepcopy(banc.charge())
    faux_proof = T / "preuve.ots"
    faux_proof.write_bytes(b"une preuve d ancrage qui n est pas la bonne")
    avec_ancrage["external_anchor"] = {
        "kind": "opentimestamps", "status": "submitted",
        "proof_sha256": "0" * 64, "note": "empreinte declaree volontairement fausse",
    }
    jws6 = banc.resigne(T / "ancrage.jws", avec_ancrage)
    code, s = verifier(jws6, banc.archive, banc.magasin,
                       ["--allow-test-keys", "--anchor-proof", str(faux_proof)])
    pose("6", "ancrage present mais non concordant",
         code != 0 and etat(s, "concordance de la preuve d ancrage") == "FAIL"
         and etat(s, "ancrage tiers") == "NOT TESTED",
         "la preuve nommee n est pas celle fournie ; la VALIDITE de l ancrage "
         "reste non verifiee")

    # ---- 7. archive recalculee apres suppression d une observation --------
    amputee = banc.archive_sans_une_observation()
    code_interne, s_interne = lancer([sys.executable, str(VERIFY), str(amputee)])
    code, s = verifier(banc.jws, amputee, banc.magasin, ["--allow-test-keys"])
    pose("7", "archive recalculee apres suppression d une observation",
         code != 0 and etat(s, "concordance avec l archive") == "FAIL",
         "verify.py seul : %d FAIL interne(s) ; l attestation : concordance %s"
         % (sum(1 for l in s_interne.splitlines() if l.startswith("[FAIL")),
            etat(s, "concordance avec l archive")))

    # ---- 8. metadonnees de signature malformees ---------------------------
    malformes = [
        ("deux segments", "a.b"),
        ("segment vide", "a..c"),
        ("base64url invalide", "@@@.###.$$$"),
        ("charge non JSON", b64u(b'{"alg":"EdDSA"}') + "." + b64u(b"pas du json") + ".AA"),
        ("charge = tableau", b64u(b'{"alg":"EdDSA"}') + "." + b64u(b"[1,2]") + ".AA"),
    ]
    plantages = []
    for nom, contenu in malformes:
        cible = T / ("malforme-%s.jws" % nom.replace(" ", "-"))
        cible.write_text(contenu + "\n", encoding="ascii")
        code, s = verifier(cible, banc.archive, banc.magasin, ["--allow-test-keys"])
        if "BILAN" not in s or code == 0:
            plantages.append("%s (%s)" % (nom, "pas de BILAN" if "BILAN" not in s else "accepte"))
    pose("8", "metadonnees de signature malformees",
         not plantages,
         "%d/%d rendent un FAIL motive sans trace d appels"
         % (len(malformes) - len(plantages), len(malformes))
         + ("" if not plantages else " ; manques : " + ", ".join(plantages)))

    # ---- 9. archive historique NON SIGNEE : niveau conserve ---------------
    exemple = RACINE / "examples" / "binding"
    # L exemple de liaison nomme son archive et porte son empreinte. Sur une
    # autre archive, les trois cas qui s en servent ne peuvent pas etre
    # eprouves -- et le dire vaut mieux que de les faire echouer, ou pire,
    # de les faire passer pour la mauvaise raison.
    manifeste_exemple = json.loads((exemple / "manifest.json").read_text(encoding="utf-8"))
    empreinte_attendue = (
        manifeste_exemple.get("subject", {}).get("source_archive", {}).get("sha256")
    )
    liaison_applicable = empreinte_attendue == sha256(banc.archive.read_bytes())
    raison_inapplicable = (
        "l exemple de liaison porte sur une autre archive (%s...)"
        % (empreinte_attendue or "?")[:16]
    )
    if not liaison_applicable:
        pose("9", "archive historique non signee : niveau conserve",
             None, raison_inapplicable)
        code, s = 0, ""
    else:
        code, s = lancer([sys.executable, str(BIND), "verify",
                          str(exemple / "manifest.json"),
                          "--root", str(exemple), "--archive", str(banc.archive)])
        pose("9", "archive historique non signee : niveau conserve",
             code == 0 and "reference_verifiable" in s
             and etat(s, "attestation de l archive du sujet") == "NOT TESTED",
             "liaison acceptee au niveau reference_verifiable, attestation NOT TESTED")

    # ---- 9b. bind.py --attestation : l ELEVATION TRANSITIVE ---------------
    # Cas ajoute le 6 novembre, en revue : ce chemin n etait couvert par
    # AUCUN test, et il etait CASSE -- `bind.py` rebatissait a la main le jeu
    # d arguments du verificateur, et une option ajoutee ensuite le faisait
    # echouer par AttributeError. Un chemin non teste est un chemin casse.
    if not liaison_applicable:
        pose("9b", "bind.py --attestation : elevation transitive des artefacts",
             None, raison_inapplicable)
    else:
        code, s = lancer([
            sys.executable, str(BIND), "verify", str(exemple / "manifest.json"),
            "--root", str(exemple), "--archive", str(banc.archive),
            "--attestation", str(banc.jws), "--trust-store", str(banc.magasin),
            "--allow-test-keys",
        ])
        eleves = "cryptographically_attested" in s and "eleve(s) de" in s
        pose("9b", "bind.py --attestation : elevation transitive des artefacts",
             code == 0 and eleves
             and etat(s, "attestation de l archive du sujet") == "PASS"
             and "Niveau de garantie DERIVE pour la liaison : cryptographically_attested" in s,
             "liaison elevee a cryptographically_attested"
             if eleves else "ELEVATION ABSENTE -- %s" % (motif_bind(s) or "sans motif"))

    # ---- 9c. bind.py --attestation avec une attestation NON valide --------
    # L elevation ne doit pas se produire, et la liaison doit retomber.
    if not liaison_applicable:
        # Celui-ci PASSAIT pour la mauvaise raison : il attend un FAIL et en
        # obtenait un, mais celui de << l archive n est pas celle du
        # manifeste >>, pas celui de la confiance refusee.
        pose("9c", "bind.py --attestation non fiable : aucune elevation",
             None, raison_inapplicable)
    else:
        code, s = lancer([
            sys.executable, str(BIND), "verify", str(exemple / "manifest.json"),
            "--root", str(exemple), "--archive", str(banc.archive),
            "--attestation", str(banc.jws), "--trust-store", str(banc.magasin),
        ])  # sans --allow-test-keys : l attestation n atteint pas le niveau
        pose("9c", "bind.py --attestation non fiable : aucune elevation",
             code != 0
             and etat(s, "attestation de l archive du sujet") == "FAIL"
             # et pour la BONNE raison : la cle de test est refusee
             and "statut `test`" in s
             and "cryptographically_attested" not in s.split("BILAN")[-1],
             "elevation refusee pour la bonne raison : cle de test non autorisee")

    # ---- 10. non-regression ------------------------------------------------
    code_g, s_g = lancer([sys.executable, str(VERIFY), str(banc.archive),
                          "--corpus", str(banc.corpus)] if banc.corpus
                         else [sys.executable, str(VERIFY), str(banc.archive)])
    bilan_g = next((l for l in s_g.splitlines() if l.startswith("BILAN")), "")
    attendu_g = "BILAN : 20 PASS, 0 FAIL, 2 NOT TESTED" if banc.corpus else None
    pose("10", "non-regression de verify.py sur GROUNDED-S1",
         bilan_g == attendu_g if attendu_g else "0 FAIL" in bilan_g,
         bilan_g or "aucun bilan")

    # ---- 11. `alg` falsifie dans l en-tete --------------------------------
    resultats_alg = []
    for faux_alg in ("none", "HS256", "RS256"):
        entete_faux = {"alg": faux_alg, "kid": "nm-ev-test-a", "typ": "JOSE"}
        cible = T / ("alg-%s.jws" % faux_alg)
        ecris_jws(cible, entete_faux, charge_octets, banc.signe(entete_faux, charge_octets))
        code, s = verifier(cible, banc.archive, banc.magasin, ["--allow-test-keys"])
        resultats_alg.append(code != 0 and etat(s, "en-tete : algorithme impose") == "FAIL")
    pose("11", "alg falsifie dans l en-tete (none, HS256, RS256)",
         all(resultats_alg),
         "%d/3 refuses -- l algorithme est impose, jamais lu pour choisir"
         % sum(resultats_alg))

    # ---- 12. cle de test sans --allow-test-keys ---------------------------
    code, s = verifier(banc.jws, banc.archive, banc.magasin)
    pose("12", "cle de statut `test` sans --allow-test-keys",
         code != 0 and etat(s, "identite de confiance") == "FAIL"
         and etat(s, "signature cryptographique") == "PASS",
         "signature PASS, confiance FAIL")

    # ---- 13. cle COMPROMISE, signature anterieure -------------------------
    def compromets(m):
        m["keys"][0]["status"] = "compromised"
        m["keys"][0]["revocation"] = {
            "kind": "compromised", "at_declared": "2026-11-30T00:00:00Z",
            "reason": "exercice de test",
        }
    compromis = banc.magasin_modifie("magasin-compromis.json", compromets)
    code, s = verifier(banc.jws, banc.archive, compromis, ["--allow-test-keys"])
    pose("13", "cle compromise, signature ANTERIEURE a la revocation",
         code != 0 and etat(s, "identite de confiance") == "FAIL",
         "refusee RETROACTIVEMENT : un detenteur de la cle privee peut forger "
         "n importe quelle date")

    # ---- 14. cle ROTATION, signature anterieure ---------------------------
    def tourne(m):
        m["keys"][0]["status"] = "rotated"
        m["keys"][0]["revocation"] = {
            "kind": "rotated", "at_declared": "2026-11-30T00:00:00Z",
            "reason": "rotation planifiee",
        }
    tournee = banc.magasin_modifie("magasin-rotation.json", tourne)
    code, s = verifier(banc.jws, banc.archive, tournee, ["--allow-test-keys"])
    pose("14", "cle retiree par rotation, signature ANTERIEURE",
         code == 0 and etat(s, "identite de confiance") == "PASS"
         and niveau(s) == "cryptographically_attested",
         "acceptee -- c est la difference avec une compromission")

    # ---- 14b. rotation, signature POSTERIEURE -----------------------------
    def tourne_avant(m):
        m["keys"][0]["status"] = "rotated"
        m["keys"][0]["revocation"] = {
            "kind": "rotated", "at_declared": "2026-11-01T00:00:00Z",
            "reason": "rotation anterieure a l attestation",
        }
    code, s = verifier(banc.jws, banc.archive,
                       banc.magasin_modifie("magasin-rotation-avant.json", tourne_avant),
                       ["--allow-test-keys"])
    pose("14b", "rotation, signature POSTERIEURE a la rotation",
         code != 0 and etat(s, "identite de confiance") == "FAIL",
         "refusee")

    # ---- 15. `cryptography` absent de l environnement ---------------------
    import os

    faux_paquet = T / "sans-crypto"
    (faux_paquet / "cryptography").mkdir(parents=True, exist_ok=True)
    (faux_paquet / "cryptography" / "__init__.py").write_text(
        "raise ImportError('indisponible dans cet environnement de test')\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(faux_paquet)
    code, s = verifier(banc.jws, banc.archive, banc.magasin, ["--allow-test-keys"], env=env)
    pose("15", "`cryptography` absent : NOT TESTED, jamais PASS ni FAIL",
         code == 0 and etat(s, "signature cryptographique") == "NOT TESTED"
         and niveau(s) == "aucun",
         "signature NOT TESTED, aucun niveau atteint")

    # ---- 16. le verificateur n atteint aucune cle privee ------------------
    import ast

    arbre = ast.parse(VERIFY_ATT.read_text(encoding="utf-8"))
    importes = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            importes.update(a.name.split(".")[0] for a in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            importes.add(noeud.module.split(".")[0])
    texte = VERIFY_ATT.read_text(encoding="utf-8")
    interdits = [m for m in ("Ed25519PrivateKey", "private_bytes", "PrivateFormat",
                             ".sign(") if m in texte]
    pose("16", "le verificateur n atteint aucune cle privee",
         "sign" not in importes and not interdits,
         "n importe pas `sign` ; aucune primitive privee" if not interdits
         else "primitives trouvees : %s" % interdits)

    # ---- 17. magasin contenant un champ de cle PRIVEE ---------------------
    pollue = banc.magasin_modifie(
        "magasin-pollue.json",
        lambda m: m["keys"][0].update({"d": "AAAA" * 10}),
    )
    code, s = verifier(banc.jws, banc.archive, pollue, ["--allow-test-keys"])
    pose("17", "magasin contenant un champ de cle privee",
         code != 0 and etat(s, "magasin de confiance lisible") == "FAIL",
         "magasin refuse -- un magasin ne porte que du public")

    # ---- 18. kid en double dans le magasin -------------------------------
    def duplique(m):
        m["keys"].append(copy.deepcopy(m["keys"][0]))
    code, s = verifier(banc.jws, banc.archive,
                       banc.magasin_modifie("magasin-doublon.json", duplique),
                       ["--allow-test-keys"])
    pose("18", "kid en double dans le magasin",
         code != 0 and etat(s, "magasin de confiance lisible") == "FAIL",
         "refuse -- un kid ne se reutilise pas")

    # ---- 19. politique de verification inconnue ---------------------------
    def politique_inconnue(m):
        m["verification_policy"]["policy_id"] = "autre-politique/9"
    code, s = verifier(banc.jws, banc.archive,
                       banc.magasin_modifie("magasin-politique.json", politique_inconnue),
                       ["--allow-test-keys"])
    pose("19", "politique de verification inconnue",
         code != 0 and etat(s, "magasin de confiance lisible") == "FAIL",
         "refusee, pas interpretee")

    # ---- 20. kid de l en-tete different de celui de la charge ------------
    entete_decale = {"alg": "EdDSA", "kid": "nm-ev-autre", "typ": "JOSE"}
    cible = T / "kid-decale.jws"
    ecris_jws(cible, entete_decale, charge_octets, banc.signe(entete_decale, charge_octets))
    code, s = verifier(cible, banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("20", "kid de l en-tete different de celui de la charge",
         code != 0 and etat(s, "en-tete : algorithme impose") == "FAIL",
         "refuse")

    # ---- 21. attestation retrospective sans date de gel du sujet ---------
    sans_gel = copy.deepcopy(banc.charge())
    sans_gel["subject"]["subject_frozen_at_declared"] = None
    code, s = verifier(banc.resigne(T / "sans-gel.jws", sans_gel),
                       banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("21", "attestation retrospective sans date de gel du sujet",
         code != 0 and etat(s, "forme de l attestation") == "FAIL",
         "refusee -- une attestation retrospective doit conserver la date de gel")

    # ---- 22. charge NON CANONIQUE mais correctement signee ---------------
    # Le test qui prouve que les deux controles sont independants.
    code, s = verifier(banc.resigne(T / "non-canonique.jws", banc.charge(), canonique=False),
                       banc.archive, banc.magasin, ["--allow-test-keys"])
    pose("22", "charge non canonique, mais correctement signee",
         code != 0
         and etat(s, "profil de canonicalisation") == "FAIL"
         and etat(s, "signature cryptographique") == "PASS",
         "profil FAIL et signature PASS -- les deux controles sont bien distincts")

    # ---- 26 et 27. LA FABRIQUE D ARGUMENTS, structurellement ----------
    #
    # UNE GARDE QUI SAUTE EN CI NE GARDE RIEN.
    #
    # Les cas 9b et 9c etaient censes garder ce point. Ils ne le font pas :
    # ils exigent l archive de DEMONSTRATION, et la CI les lance sur la
    # FIXTURE -- donc ils ressortent INAPPLICABLE. Le defaut est passe
    # ainsi le 6 novembre : `--store-digest` et `--lang` ont ete ajoutes a
    # l analyseur de `verify_attestation.py` et oublies dans la fabrique,
    # et `bind.py --attestation` est retombe sur le meme AttributeError que
    # `anchor_proof` avait deja produit. Verifie en reintroduisant le
    # defaut : la suite restait a 22/22.
    #
    # Ce controle ne depend d AUCUNE archive, donc il ne peut pas sauter.
    # Et il est plus fort qu un scenario : un champ ajoute demain et oublie
    # ici sera signale meme si aucun scenario ne l exerce.
    import ast as _ast

    source_va = (RACINE / "verify_attestation.py").read_text(encoding="utf-8")
    arbre_va = _ast.parse(source_va)
    fonctions = {n.name: n for n in _ast.walk(arbre_va)
                 if isinstance(n, _ast.FunctionDef)}

    lus: set[str] = set()
    for nom_fn in ("verifier", "rendre"):
        if nom_fn not in fonctions:
            continue
        for n in _ast.walk(fonctions[nom_fn]):
            if (isinstance(n, _ast.Attribute)
                    and isinstance(n.value, _ast.Name)
                    and n.value.id == "arguments"):
                lus.add(n.attr)

    import verify_attestation as _va

    fournis = set(vars(_va.arguments_de_verification(
        attestation=RACINE / "inexistant.jws")))
    manquants = sorted(lus - fournis)

    pose("26", "la fabrique fournit TOUT ce que `verifier` lit",
         not manquants,
         "%d champ(s) lus par verifier/rendre, tous fournis" % len(lus)
         if not manquants else "MANQUANTS : %s" % manquants)

    # Dans l autre sens : un champ fourni que personne ne lit est du bruit,
    # pas un defaut. On ne l exige donc pas -- on le NOMME, pour qu il ne
    # s accumule pas sans qu on le sache.
    inutiles = sorted(fournis - lus)
    pose("27", "les champs de la fabrique que `verifier` ne lit pas sont nommes",
         True,
         "aucun" if not inutiles else "non lus : %s" % inutiles)

    return r


# --------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print("emploi : python tests/test_attestation.py <archive.zip> [corpus]")
        return 2
    archive = Path(sys.argv[1]).resolve()
    corpus = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    if not archive.is_file():
        print("archive introuvable : %s" % archive)
        return 2

    print("Tests de securite de l attestation -- %s" % archive.name)
    print("empreinte : %s" % sha256(archive.read_bytes()))
    print("Les cles sont EPHEMERES et effacees a la fin.\n")

    travail = Path(tempfile.mkdtemp(prefix="attestation-"))
    try:
        banc = Banc(archive, travail)
        banc.corpus = corpus
        resultats = cas(banc)
    finally:
        shutil.rmtree(travail, ignore_errors=True)
        print("\n[cles ephemeres effacees]")

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
        print("[%-9s] %-3s %-58s %s"
              % (etiquette, numero, intitule[:58], constat[:70]))

    eprouves = len(resultats) - len(inapplicables)
    print("\nBILAN : %d/%d cas conformes, %d inapplicable(s)"
          % (eprouves - len(echecs), eprouves, len(inapplicables)))
    for i in inapplicables:
        print("  inapplicable : %s" % i)
    for e in echecs:
        print("  - %s" % e)

    if not echecs:
        print("\nCe que ces tests etablissent : une attestation fautive est refusee, et")
        print("les trois piliers -- signature, confiance, concordance -- restent trois")
        print("controles distincts.")
        print("Ce qu ils n etablissent pas : que la DATE declaree soit vraie, ni que le")
        print("contenu atteste soit vrai. Aucun ancrage tiers n est implemente.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

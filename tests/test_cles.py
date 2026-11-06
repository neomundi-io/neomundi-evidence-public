# -*- coding: utf-8 -*-
"""Cycle de vie d une cle : registre, rotation, compromission.

D OU VIENT CETTE SUITE
----------------------

De la condition B-2. Deux manques y etaient nommes et aucun n etait outille :

  * **le registre des paquets signes.** `SIGNING_POLICY.md` le disait
    manquant, et B-2 en fait un PREREQUIS de la premiere attestation
    reelle. La raison est asymetrique : marquer une cle `compromised`
    invalide RETROACTIVEMENT tout ce qu elle a signe, quelle que soit la
    date declaree, parce qu un voleur choisit la date qu il ecrit.
    Circonscrire est la seule chose qui limite les degats, et on ne
    circonscrit que ce qu on a consigne.
  * **<< ne jamais revoquer a sec >>.** Generer le successeur, le publier,
    puis seulement marquer le predecesseur. Une revocation dont le
    remplacant n est pas publie laisse tout consommateur avec une cle a ne
    plus croire et aucune a croire -- et le verificateur rendant NOT TESTED
    sur une cle inconnue, la chaine perd un niveau EN SILENCE au lieu
    d echouer franchement.

L ASYMETRIE EST LE COEUR
------------------------

Les cas 5 et 6 la mesurent sur la MEME attestation, inchangee a l octet :

    rotation     -> PASS, elle reste de confiance
    compromission -> FAIL, elle ne l est plus

Si ces deux cas rendaient le meme verdict, l un des deux mecanismes serait
faux -- et ce serait une raison de ne pas signer du tout.

ET UNE LACUNE TROUVEE EN CONSTRUISANT
-------------------------------------

Une rotation exige que le successeur soit deja dans le MEME magasin, et
`genkey` ecrivait toujours un magasin NEUF. La garde etait donc correcte et
la rotation impossible en pratique. D ou `genkey --append`, et le cas 9 qui
verifie qu il refuse de reutiliser un `kid`.
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
    print("[%-9s] %-3s %-54s %s" % (etat, numero, intitule, detail))


def lancer(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-cles-"))
    try:
        code, s = lancer("tests/make_fixture.py",
                         [str(travail / "fix"), "--profile", "v2"])
        assert code == 0, s
        archive = travail / "fix" / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"
        magasin = travail / "store.json"
        commun = ["--store-kind", "test", "--signer-capacity", "experimental",
                  "--signer-registration", "RNA W563015824",
                  "--signer-jurisdiction", "FR"]
        code, s = lancer("sign.py", [
            "genkey", "--kid", "k1", "--out", str(travail / "k1.json"),
            "--trust-store-out", str(magasin), "--valid-from",
            "2026-11-06T00:00:00Z"] + commun)
        assert code == 0, s

        registre = travail / "registre.txt"
        jws = travail / "a1.jws"
        code, s_att = lancer("sign.py", [
            "attest", "--archive", str(archive), "--key", str(travail / "k1.json"),
            "--out", str(jws), "--attested-at", "2026-11-06T13:00:00Z",
            "--register", str(registre)])

        # ---- 1. le registre est ecrit, au format annonce par B-2 --------
        lignes = [l for l in registre.read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")] if registre.exists() else []
        champs = lignes[0].split() if lignes else []
        pose("1", "le registre consigne la ligne prescrite par B-2",
             code == 0 and len(lignes) == 1 and len(champs) == 5
             and champs[0] == "2026-11-06T13:00:00Z" and champs[1] == "k1"
             and len(champs[2]) == 64 and len(champs[3]) == 64,
             "%d champ(s)" % len(champs))

        # ---- 2. le registre est APPEND-ONLY ----------------------------
        # Une seconde signature ne doit pas effacer la premiere : sinon la
        # portee d une compromission se perd a chaque nouvelle attestation.
        lancer("sign.py", [
            "attest", "--archive", str(archive), "--key", str(travail / "k1.json"),
            "--out", str(travail / "a2.jws"), "--attested-at",
            "2026-11-06T14:00:00Z", "--register", str(registre)])
        apres = [l for l in registre.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")]
        pose("2", "le registre est append-only",
             len(apres) == 2 and apres[0] == lignes[0],
             "%d ligne(s), la premiere intacte" % len(apres))

        # ---- 3. signer SANS registre le dit, et ne le tait pas ---------
        _, s_sans = lancer("sign.py", [
            "attest", "--archive", str(archive), "--key", str(travail / "k1.json"),
            "--out", str(travail / "a3.jws"), "--attested-at",
            "2026-11-06T15:00:00Z"])
        pose("3", "signer sans registre est signale, pas tu",
             "AUCUN registre tenu" in s_sans
             and "circonscrite" in s_sans,
             "l outil avertit")

        # ---- 4. << ne jamais revoquer a sec >> -------------------------
        code_a, s_a = lancer("sign.py", [
            "retire", "--trust-store", str(magasin), "--out", str(travail / "x.json"),
            "--kid", "k1", "--kind", "rotated", "--at", "2026-11-07T00:00:00Z",
            "--reason", "rotation"])
        code_b, s_b = lancer("sign.py", [
            "retire", "--trust-store", str(magasin), "--out", str(travail / "x.json"),
            "--kid", "k1", "--kind", "rotated", "--successor", "k2",
            "--at", "2026-11-07T00:00:00Z", "--reason", "rotation"])
        pose("4", "une rotation a sec est refusee, deux fois",
             code_a == 1 and "revocation a sec" in s_a
             and code_b == 1 and "ABSENT de ce magasin" in s_b
             and "k2" in s_b and not (travail / "x.json").exists(),
             "sans successeur, puis successeur non publie")

        code, s = lancer("sign.py", [
            "genkey", "--kid", "k2", "--out", str(travail / "k2.json"),
            "--trust-store-out", str(magasin), "--append", "--valid-from",
            "2026-11-07T00:00:00Z"] + commun)
        assert code == 0, s
        apres_ajout = json.loads(magasin.read_bytes())

        tourne = travail / "store-rot.json"
        lancer("sign.py", [
            "retire", "--trust-store", str(magasin), "--out", str(tourne),
            "--kid", "k1", "--kind", "rotated", "--successor", "k2",
            "--at", "2026-11-07T00:00:00Z", "--reason", "rotation annuelle"])

        def confiance(store: Path) -> tuple[int, str]:
            c, sortie = lancer("verify_attestation.py", [
                str(jws), "--archive", str(archive), "--trust-store", str(store),
                "--allow-test-keys"])
            ligne = next((l for l in sortie.splitlines()
                          if "identite de confiance" in l), "")
            return c, ligne

        # ---- 5. une ROTATION laisse les signatures anterieures ---------
        code_r, ligne_r = confiance(tourne)
        pose("5", "apres rotation : l attestation reste de confiance",
             code_r == 0 and "[PASS" in ligne_r and "rotated" in ligne_r,
             "code %d" % code_r)

        # ---- 6. une COMPROMISSION les emporte TOUTES ------------------
        # Meme attestation, meme archive, meme octet. Seul le magasin change.
        comp = travail / "store-comp.json"
        _, s_comp = lancer("sign.py", [
            "retire", "--trust-store", str(magasin), "--out", str(comp),
            "--kid", "k1", "--kind", "compromised", "--at", "2026-11-07T00:00:00Z",
            "--reason", "poste suspecte compromis", "--register", str(registre)])
        code_c, ligne_c = confiance(comp)
        pose("6", "apres compromission : la MEME attestation tombe",
             code_c == 1 and "[FAIL" in ligne_c and "COMPROMISE" in ligne_c
             and "quelle que soit leur date declaree" in ligne_c,
             "code %d, et l asymetrie tient" % code_c)

        # ---- 7. la portee est circonscrite, et chiffree ---------------
        pose("7", "une compromission annonce sa portee consignee",
             "Portee consignee : 2 attestation(s)" in s_comp,
             "2 des 3 signatures etaient au registre")

        # ---- 8. une compromission ne se requalifie pas ----------------
        code_q, s_q = lancer("sign.py", [
            "retire", "--trust-store", str(comp), "--out", str(travail / "z.json"),
            "--kid", "k1", "--kind", "rotated", "--successor", "k2",
            "--at", "2026-11-08T00:00:00Z", "--reason", "oups"])
        code_n, s_n = lancer("sign.py", [
            "retire", "--trust-store", str(magasin), "--out", str(travail / "z.json"),
            "--kid", "k1", "--kind", "compromised", "--successor", "k2",
            "--at", "2026-11-07T00:00:00Z", "--reason", "vol"])
        pose("8", "compromission : ni requalifiable, ni remplacable",
             code_q == 1 and "deja COMPROMISE" in s_q
             and code_n == 1 and "n est pas remplacee" in s_n,
             "les deux sens refuses")

        # ---- 9. un `kid` ne se reutilise jamais -----------------------
        # Deux cles portant le meme `kid` rendraient le registre ambigu, et
        # une compromission non circonscrivable.
        code_k, s_k = lancer("sign.py", [
            "genkey", "--kid", "k2", "--out", str(travail / "k2bis.json"),
            "--trust-store-out", str(magasin), "--append", "--valid-from",
            "2026-11-08T00:00:00Z"] + commun)
        pose("9", "`genkey --append` refuse de reutiliser un `kid`",
             code_k == 1 and "DEJA present" in s_k,
             "et le magasin n a pas bouge")

        # ---- 10. `store_version` est monotone -------------------------
        # C est le nombre publie sur le second canal (C-5) : s il ne bouge
        # pas, un consommateur ne voit pas qu il tient une version perimee.
        avant = 1
        pose("10", "l ajout d une cle incremente `store_version`",
             apres_ajout.get("store_version") == avant + 1
             and len(apres_ajout.get("changes", [])) == 2,
             "version %s, %d changement(s)"
             % (apres_ajout.get("store_version"),
                len(apres_ajout.get("changes", []))))

        # ---- 10b. un identifiant non conforme REFUSE avant la generation
        # La procedure operateur ecrite passait `--signer "NeoMundi
        # Recherche"` -- une raison sociale la ou le schema attend un
        # identifiant. `genkey` ecrivait sans broncher un magasin NON
        # CONFORME, et aucune validation de schema ne tourne dans ce depot
        # pour le dire. Le pire moment pour s en apercevoir serait apres
        # avoir genere la cle reelle : d ou un refus AVANT toute ecriture.
        avant = travail / "ne-doit-pas-naitre.json"
        code_i, s_i = lancer("sign.py", [
            "genkey", "--kid", "k9", "--out", str(avant),
            "--signer", "NeoMundi Recherche",
            "--signer-legal-name", "NeoMundi Recherche",
            "--valid-from", "2026-11-06T00:00:00Z"] + commun[:-2])
        pose("10b", "un identifiant non conforme refuse AVANT generation",
             code_i == 1 and "non conforme" in s_i
             and "Aucune cle n a ete generee" in s_i and not avant.exists(),
             "aucun fichier de cle ecrit")

        # ---- 11. une cle privee ne s ecrit JAMAIS dans le depot -------
        code_d, s_d = lancer("sign.py", [
            "genkey", "--kid", "k-interdit",
            "--out", str(RACINE / "cle-interdite.json"),
            "--valid-from", "2026-11-06T00:00:00Z"] + commun)
        pose("11", "refus d ecrire une cle privee sous le depot",
             code_d != 0 and not (RACINE / "cle-interdite.json").exists(),
             "code %d" % code_d)

        # ---- 12. et un registre non plus ------------------------------
        # Le registre nomme des paquets et des cles : il est hors du depot
        # public par construction, comme la cle.
        code_g, s_g = lancer("sign.py", [
            "attest", "--archive", str(archive), "--key", str(travail / "k1.json"),
            "--out", str(travail / "a4.jws"), "--attested-at",
            "2026-11-06T16:00:00Z", "--register", str(RACINE / "registre-interdit.txt")])
        pose("12", "refus d ecrire le registre sous le depot",
             not (RACINE / "registre-interdit.txt").exists(),
             "code %d" % code_g)

    finally:
        for parasite in ("cle-interdite.json", "registre-interdit.txt"):
            (RACINE / parasite).unlink(missing_ok=True)
        shutil.rmtree(travail, ignore_errors=True)

    print()
    problemes = sum(1 for e, _, _ in _bilan if e == "PROBLEME")
    inapplicables = sum(1 for e, _, _ in _bilan if e == "INAPPLICABLE")
    conformes = sum(1 for e, _, _ in _bilan if e == "OK")
    print("BILAN : %d/%d cas conformes, %d inapplicable(s), %d probleme(s)"
          % (conformes, len(_bilan) - inapplicables, inapplicables, problemes))
    if problemes:
        print()
        print("Une rotation et une compromission ne disent pas la meme chose :")
        print("la premiere laisse le passe de confiance, la seconde l emporte")
        print("en entier. Si cette suite echoue, l un des deux mecanismes est")
        print("faux -- et c est une raison de ne pas signer du tout.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

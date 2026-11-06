# -*- coding: utf-8 -*-
"""Une identite DECLAREE ne doit jamais se lire comme une identite VERIFIEE.

D OU VIENT CETTE SUITE
----------------------

De la condition B-1. L entite emettrice est NeoMundi Recherche, le cadre est
experimental et non commercial, et la valeur `experimental` a ete ajoutee a
`legal_capacity_to_attest` pour le dire. Cette valeur est le point ou une
confusion coute le plus cher : elle nomme une entite reelle, elle repose sur
une decision reelle, et **aucun pouvoir n a ete verifie**.

Trois glissements sont possibles, et cette suite les verrouille :

  * lire `experimental` comme un `verified` plus faible. C est le contraire :
    `verified` dit qu un controle a eu lieu ailleurs, `experimental` dit
    qu aucun n a eu lieu ;
  * laisser une valeur declaree **changer un verdict**. Aucune valeur de ce
    champ ne doit produire un PASS -- sinon un producteur ameliore son
    resultat en ecrivant un mot dans un fichier (cas 6 et 7) ;
  * presenter une attestation experimentale comme une certification
    juridique. La negation doit etre ECRITE, dans les deux langues
    (cas 4 et 5).

ET UN PIEGE DEJA RENCONTRE
--------------------------

`CAUSES_PAR_SIGNAL` avait quatre causes pour cinq signaux, et la table a
diverge de l enumeration sans que rien ne le dise. Le cas 8 interdit la
meme derive ici : toute valeur du schema doit avoir une explication, et
toute explication doit correspondre a une valeur du schema.
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
sys.path.insert(0, str(RACINE))

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-56s %s" % (etat, numero, intitule, detail))


def lancer(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def ligne_de_capacite(sortie: str, anglais: bool = False) -> str:
    """La ligne de controle de la capacite, telle qu elle est rendue."""
    intitule = "legal capacity of the signer" if anglais \
        else "capacite juridique du signataire"
    morceaux: list[str] = []
    for brute in sortie.splitlines():
        if intitule in brute:
            morceaux.append(brute)
        elif morceaux and brute.startswith(" " * 8):
            morceaux.append(brute)          # continuation d une ligne repliee
        elif morceaux:
            break
    return " ".join(m.strip() for m in morceaux)


def fabriquer(travail: Path, capacite: str) -> tuple[Path, Path, Path]:
    """Une fixture, une cle de TEST, un magasin declarant `capacite`."""
    coin = travail / capacite
    code, s = lancer("tests/make_fixture.py", [str(coin / "fix"), "--profile", "v2"])
    assert code == 0, s
    cle, magasin = coin / "cle.json", coin / "trust-store.json"
    code, s = lancer("sign.py", [
        "genkey", "--kid", "nm-ev-%s" % capacite.replace("_", "-"),
        "--out", str(cle), "--trust-store-out", str(magasin),
        "--store-kind", "test", "--store-id", "neomundi-evidence-essai",
        "--signer-capacity", capacite, "--signer-registration", "RNA W563015824",
        "--signer-jurisdiction", "FR", "--valid-from", "2026-11-06T00:00:00Z"])
    assert code == 0, s
    archive = coin / "fix" / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"
    jws = coin / "att.jws"
    code, s = lancer("sign.py", [
        "attest", "--archive", str(archive), "--key", str(cle), "--out", str(jws),
        "--attested-at", "2026-11-06T13:00:00Z"])
    assert code == 0, s
    return archive, jws, magasin


def verifier(archive: Path, jws: Path, magasin: Path,
             langue: str | None = None) -> tuple[int, str]:
    args = [str(jws), "--archive", str(archive), "--trust-store", str(magasin),
            "--allow-test-keys"]
    if langue:
        args += ["--lang", langue]
    return lancer("verify_attestation.py", args)


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-capacite-"))
    try:
        schema = json.loads(
            (RACINE / "schemas" / "evidence-trust-store-v1.json").read_bytes())
        enum = (schema["properties"]["identities"]["items"]["properties"]
                ["legal_capacity_to_attest"]["enum"])

        # ---- 1. le schema enumere `experimental` ------------------------
        pose("1", "le schema enumere `experimental`",
             "experimental" in enum, " | ".join(enum))

        # ---- 2. le schema dit ce que la valeur veut dire ----------------
        # Un magasin se lit sans son schema a cote, mais un relecteur du
        # schema doit pouvoir y trouver le sens sans le deviner.
        desc = (schema["properties"]["identities"]["items"]["properties"]
                ["legal_capacity_to_attest"]["description"])
        pose("2", "le schema distingue DECLAREE de VERIFIEE",
             "DECLARED" in desc and "VERIFIED" in desc
             and "never a legal certification" in desc,
             "%d caracteres" % len(desc))

        archive, jws, magasin = fabriquer(travail, "experimental")

        # ---- 3. le magasin consigne la valeur et la reference -----------
        signataire = json.loads(magasin.read_bytes())["identities"][0]
        pose("3", "le magasin declare l entite emettrice",
             signataire["legal_capacity_to_attest"] == "experimental"
             and signataire["legal_name"] == "NeoMundi Recherche"
             and signataire["registration_reference"] == "RNA W563015824"
             and signataire["kind"] == "association",
             "%s / %s" % (signataire["legal_name"],
                          signataire["registration_reference"]))

        # ---- 4. la ligne FR nie explicitement la certification ----------
        code_fr, s_fr = verifier(archive, jws, magasin, "fr")
        l_fr = ligne_de_capacite(s_fr)
        pose("4", "en francais : DECLAREE, et pas une certification",
             "NOT TESTED" in l_fr and "DECLAREE" in l_fr
             and "non juridiquement VERIFIEE" in l_fr
             and "n est pas une certification juridique" in l_fr,
             l_fr[:48] or "ligne absente")

        # ---- 5. et la ligne EN aussi ------------------------------------
        # Une negation qui ne survit pas a la traduction ne protege que les
        # lecteurs francophones.
        code_en, s_en = verifier(archive, jws, magasin, "en")
        l_en = ligne_de_capacite(s_en, anglais=True)
        pose("5", "en anglais : DECLARED, et pas une certification",
             "NOT TESTED" in l_en and "DECLARED" in l_en
             and "not legally VERIFIED" in l_en
             and "not a legal certification" in l_en,
             l_en[:48] or "ligne absente")

        # ---- 6. `experimental` ne produit JAMAIS un PASS ----------------
        pose("6", "`experimental` reste NOT TESTED, jamais PASS",
             "[NOT TESTED]" in l_fr and "[PASS" not in l_fr,
             "code %d" % code_fr)

        # ---- 7. declarer `verified` n ameliore AUCUN verdict ------------
        # Le cas adverse : un producteur qui ecrit `verified` dans son
        # magasin ne doit rien y gagner.
        a2, j2, m2 = fabriquer(travail, "verified")
        _, s_v = verifier(a2, j2, m2, "fr")
        l_v = ligne_de_capacite(s_v)
        meme_decompte = (
            [x for x in s_fr.splitlines() if x.startswith("BILAN")] ==
            [x for x in s_v.splitlines() if x.startswith("BILAN")])
        pose("7", "declarer `verified` ne change aucun verdict",
             "[NOT TESTED]" in l_v and "[PASS" not in l_v and meme_decompte,
             "decomptes identiques" if meme_decompte else "DECOMPTES DIFFERENTS")

        # ---- 8. aucune derive entre l enumeration et les explications ---
        from verify_attestation import SENS_DE_LA_CAPACITE
        manquantes = [v for v in enum if v not in SENS_DE_LA_CAPACITE]
        orphelines = [v for v in SENS_DE_LA_CAPACITE if v not in enum]
        pose("8", "chaque valeur du schema a son explication, et inversement",
             not manquantes and not orphelines,
             "sans explication %s | hors schema %s"
             % (manquantes or "aucune", orphelines or "aucune"))

        # ---- 9. une valeur inconnue n est pas INTERPRETEE ---------------
        # Un magasin peut venir d un producteur plus recent que ce
        # verificateur. Deviner le sens d un mot-cle inconnu serait pire
        # que de dire qu on ne le connait pas.
        coin = travail / "inconnue"
        shutil.copytree(travail / "experimental", coin)
        m3 = coin / "trust-store.json"
        doc = json.loads(m3.read_bytes())
        doc["identities"][0]["legal_capacity_to_attest"] = "notarised"
        m3.write_bytes(json.dumps(doc, ensure_ascii=False, indent=2).encode("utf-8"))
        _, s_i = verifier(coin / "fix" / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip",
                          coin / "att.jws", m3, "fr")
        l_i = ligne_de_capacite(s_i)
        pose("9", "une capacite inconnue est rapportee, non interpretee",
             "[NOT TESTED]" in l_i and "notarised" in l_i
             and "n est pas interpretee" in l_i,
             l_i[:48] or "ligne absente")

        # ---- 10. la capacite n est jamais `requis` en mode strict -------
        # `requis` veut dire << evitable si l APPELANT fournissait ce qui
        # manque >>. Ici l appelant ne peut rien faire : c est une question
        # juridique. Le marquer requis ferait sortir 2 toute attestation
        # experimentale, pour un ecart que son porteur n a pas cree.
        #
        # ATTENTION A LA CAUSE. En mode strict, `--store-digest` manquant
        # suffit a faire sortir 2 -- et celui-la est legitimement requis,
        # puisque l appelant PEUT le fournir. Sans le fournir, ce cas
        # mesurerait l autre ligne et passerait pour une preuve qu il n est
        # pas. On le fournit donc, et il ne reste que des NOT TESTED que
        # personne ne peut lever.
        empreinte = hashlib.sha256(magasin.read_bytes()).hexdigest()
        code_strict, s_strict = lancer("verify_attestation.py", [
            str(jws), "--archive", str(archive), "--trust-store", str(magasin),
            "--allow-test-keys", "--store-digest", empreinte, "--strict"])
        requises = [l.strip(" -") for l in s_strict.splitlines()
                    if l.startswith("    - ")]
        pose("10", "la capacite declaree n est pas une garantie `requise`",
             code_strict != 2 and not any("capacite" in r for r in requises),
             "code strict %d, requises non demontrees : %s"
             % (code_strict, requises or "aucune"))

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
        print("`experimental` nomme une entite reelle sur une decision reelle,")
        print("sans qu aucun pouvoir ait ete verifie. Si cette suite echoue,")
        print("c est qu une attestation experimentale peut se lire comme une")
        print("certification juridique -- exactement ce que B-1 interdit.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

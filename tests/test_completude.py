# -*- coding: utf-8 -*-
"""La completude de l export : ce que l integrite ne dit pas.

D OU VIENT CETTE SUITE
----------------------

De l evaluation externe du 6 novembre 2026. Elle a mesure, sur une archive
reelle, un registre source de **151 enregistrements de 6 types** et un
export de **120 de 4 types** -- avec un manifeste annoncant 151. Les 31
retenus, 30 `runner_attempt` et un `run`, n etaient nommes nulle part.

Et son experience la plus importante : une observation retiree de ses cinq
membres, puis les decomptes et les sommes refaits. Resultat : `verify.py`
rendait **19 PASS, 0 FAIL**. Une archive incomplete franchissait les
controles d integrite.

CE QUE LA SUITE ETABLIT
-----------------------

Que le controle de completude distingue trois etats, et qu il ne glisse
jamais vers le PASS :

  PASS        contrat present ET arithmetique juste
  FAIL        contrat present ET contradictoire
  NOT TESTED  aucun contrat -- la completude n est pas etablie

Et que le profil `v1` du generateur reproduit a l octet l archive sur
laquelle reposent une attestation Ed25519 et une ancre Bitcoin.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

#: L empreinte de l archive historique. Une attestation Ed25519, une preuve
#: OpenTimestamps ancree dans les blocs Bitcoin 974714/974715 et un manifeste
#: de liaison portent TOUS sur cette valeur.
EMPREINTE_V1 = "e31e12bb7e32c7a33db1ecacc8c38cd18225fa10618c7e1aa5d6f9540f2ad7d6"

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-56s %s" % (etat, numero, intitule, detail))


def verifier(archive: Path, corpus: Path | None = None,
             extra: list[str] | None = None) -> tuple[int, str]:
    args = [sys.executable, str(RACINE / "verify.py"), str(archive)]
    if corpus:
        args += ["--corpus", str(corpus)]
    args += extra or []
    fini = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def etat_de(sortie: str, intitule: str) -> str:
    for ligne in sortie.splitlines():
        if ligne.startswith("[") and intitule in ligne:
            return ligne[1:ligne.index("]")].strip()
    return "ABSENTE"


def fabriquer(src: Path, cible: Path, transforme) -> Path:
    """Copie `src` en changeant son manifeste, ET en refaisant sa somme.

    LE PIEGE, trouve en ecrivant cette suite : reecrire `manifest.json` sans
    refaire son entree dans `checksums.sha256` produit une archive
    DOUBLEMENT fautive -- le contrat se contredit, et l empreinte du membre
    ne concorde plus. Les cas negatifs passaient alors en partie pour la
    mauvaise raison : `verify.py` sortait en 1 a cause de la somme, pas de
    la contradiction.

    On refait donc la somme. La seule faute de l archive produite est celle
    qu on y a mise, et c est la condition pour que le cas 11 -- << aucun
    autre controle n echoue >> -- veuille dire quelque chose.
    """
    with zipfile.ZipFile(src) as z:
        membres = {i.filename: z.read(i.filename) for i in z.infolist()}
        ordre = [i.filename for i in z.infolist()]

    m = json.loads(membres["manifest.json"])
    transforme(m)
    membres["manifest.json"] = json.dumps(
        m, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"

    # La somme est refaite a l identique de sa forme : `<sha256>  <nom>`,
    # et seules les lignes deja presentes sont mises a jour.
    lignes = []
    for ligne in membres["checksums.sha256"].decode("utf-8").splitlines():
        if not ligne.strip():
            continue
        _, _, nom = ligne.partition("  ")
        nom = nom.strip()
        if nom in membres:
            lignes.append("%s  %s" % (hashlib.sha256(membres[nom]).hexdigest(), nom))
        else:
            lignes.append(ligne)
    membres["checksums.sha256"] = ("\n".join(lignes) + "\n").encode("utf-8")

    with zipfile.ZipFile(cible, "w") as o:
        for nom in ordre:
            o.writestr(nom, membres[nom])
    return cible


def generer(ou: Path, profil: str) -> tuple[Path, Path]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / "tests" / "make_fixture.py"), str(ou),
         "--profile", profil],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if fini.returncode != 0:
        raise SystemExit("[FAIL] generation %s : %s" % (profil, fini.stderr))
    return ou / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip", ou / "corpus"


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-completude-"))
    try:
        v2, corpus2 = generer(travail / "v2", "v2")
        v1, corpus1 = generer(travail / "v1", "v1")

        # ---- 1. le profil HISTORIQUE est reproduit a l octet -----------
        # Le cas le plus important de cette suite : une attestation Ed25519
        # et une ancre Bitcoin portent sur cette empreinte. Si le generateur
        # cessait de la reproduire, rien d autre ne le remarquerait.
        obtenue = hashlib.sha256(v1.read_bytes()).hexdigest()
        pose("1", "profil v1 : l archive signee est reproduite a l octet",
             obtenue == EMPREINTE_V1,
             obtenue[:16] + "..." if obtenue == EMPREINTE_V1
             else "OBTENU %s... ATTENDU %s..." % (obtenue[:16], EMPREINTE_V1[:16]))

        demo = RACINE / "examples" / "dossier-v1" / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"
        pose("2", "et il est identique au dossier de revue publie",
             demo.is_file() and demo.read_bytes() == v1.read_bytes(),
             "octet pour octet" if demo.is_file() else "dossier absent")

        # ---- 3. POSITIF : contrat present et coherent -> PASS ----------
        code, s3 = verifier(v2, corpus2)
        pose("3", "contrat present et coherent : PASS",
             etat_de(s3, "completude de l export") == "PASS" and code == 0,
             "code %d" % code)

        # ---- 4. le PASS nomme ce qui est retenu ------------------------
        # Un PASS muet sur les types retenus vaudrait le silence qu il
        # remplace : l exclusion doit etre LUE, pas deduite.
        pose("4", "le PASS NOMME les types retenus et leur nombre",
             "runner_attempt" in s3 and "run" in s3,
             "une exclusion declaree, non un manque silencieux")

        # ---- 5. ABSENT : aucun contrat -> NOT TESTED, jamais PASS ------
        code5, s5 = verifier(v1, corpus1)
        pose("5", "aucun contrat : NOT TESTED, et jamais PASS",
             etat_de(s5, "completude de l export") == "NOT TESTED" and code5 == 0,
             "une archive muette n est pas une archive complete")

        # ---- 6. et le mode strict ne la punit PAS ----------------------
        # `requis` veut dire << l appelant pourrait le fournir >>. Ici c est
        # le PRODUCTEUR qui doit declarer : punir le porteur serait injuste.
        code6, _ = verifier(v1, corpus1, ["--strict"])
        pose("6", "strict ne punit pas une archive antérieure au contrat",
             code6 == 0, "code %d" % code6)

        # ---- 7 a 9. NEGATIF : trois contradictions distinctes ----------
        def total_faux(m):
            m["registre"]["enregistrements"] = 151

        def exportes_faux(m):
            m["registre"]["enregistrements_exportes"] = 120

        def exclus_caches(m):
            m["registre"]["types_exclus"] = {}

        for numero, nom, transforme, quoi in (
                ("7", "total.zip", total_faux,
                 "un total qui ne concorde pas : FAIL"),
                ("8", "exportes.zip", exportes_faux,
                 "un decompte d export faux : FAIL"),
                ("9", "caches.zip", exclus_caches,
                 "des types retenus MASQUES : FAIL")):
            fautive = fabriquer(v2, travail / nom, transforme)
            code_f, s_f = verifier(fautive)
            pose(numero, quoi,
                 etat_de(s_f, "completude de l export") == "FAIL" and code_f == 1,
                 "code %d" % code_f)

        # ---- 10. LE CAS CONTRADICTOIRE d ODA3 --------------------------
        # Le scenario exact mesure sur une archive reelle : le manifeste
        # annonce le total du registre SOURCE comme s il etait le total
        # exporte. C est la forme que prend la sur-declaration.
        def oda3(m):
            m["registre"]["enregistrements_exportes"] = m["registre"]["enregistrements"]
            m["registre"]["types_exclus"] = {}

        fautive = fabriquer(v2, travail / "oda3.zip", oda3)
        code10, s10 = verifier(fautive)
        pose("10", "le scenario ODA3 -- sur-declarer l export : FAIL",
             etat_de(s10, "completude de l export") == "FAIL" and code10 == 1,
             "annoncer le registre source comme l export est detecte")

        # ---- 11. et l INTEGRITE, elle, passe toujours ------------------
        # C est tout le propos : les deux garanties sont distinctes. Une
        # archive sur-declarant son export reste intérieurement coherente.
        autres = [l for l in s10.splitlines()
                  if l.startswith("[FAIL") and "completude" not in l]
        pose("11", "la sur-declaration ne fait echouer AUCUN autre controle",
             not autres,
             "integrite et completude sont deux garanties distinctes"
             if not autres else "%d autre(s) FAIL : %s" % (len(autres), autres[:1]))

        # ---- 12. les deux profils ne sont PAS la meme archive ----------
        pose("12", "v1 et v2 sont deux archives distinctes",
             v1.read_bytes() != v2.read_bytes(),
             "versionner, et non reecrire : les preuves historiques tiennent")

        # ---- 13 et 14. LE DESCRIPTEUR DIT-IL LA VERITE ? ---------------
        #
        # La CI lit ses lignes de base dans `fixture.json` -- une seule
        # source de verite, aucun nombre recopie a la main. Mais RIEN ne
        # verifiait localement que ce descripteur dise vrai.
        #
        # Le 6 novembre, l ajout du controle de completude a deplace les
        # quatre valeurs et une seule a ete mise a jour. La CI l a attrape ;
        # une suite locale aurait du le faire avant elle. Ces deux cas sont
        # ce controle manquant.
        for numero, archive, corpus, profil in (("13", v2, corpus2, "v2"),
                                                ("14", v1, corpus1, "v1")):
            descripteur = json.loads(
                (archive.parent / "fixture.json").read_bytes())["attendu"]
            _, avec = verifier(archive, corpus)
            _, sans = verifier(archive)
            obtenu_avec = next((l for l in avec.splitlines()
                                if l.startswith("BILAN")), "")
            obtenu_sans = next((l for l in sans.splitlines()
                                if l.startswith("BILAN")), "")
            ecarts = []
            if obtenu_avec != descripteur["verify_avec_corpus"]:
                ecarts.append("avec corpus : descripteur %r, obtenu %r"
                              % (descripteur["verify_avec_corpus"], obtenu_avec))
            if obtenu_sans != descripteur["verify_sans_corpus"]:
                ecarts.append("sans corpus : descripteur %r, obtenu %r"
                              % (descripteur["verify_sans_corpus"], obtenu_sans))
            pose(numero,
                 "profil %s : le descripteur dit les lignes de base REELLES" % profil,
                 not ecarts,
                 "les 2 valeurs concordent" if not ecarts else " ; ".join(ecarts))

        # ---- 15. LE DOSSIER DE REVUE dit-il la verite ? ----------------
        #
        # Meme lecon que les cas 13 et 14, sur l autre objet. Les chiffres du
        # dossier de revue etaient ecrits DANS le workflow de CI, et rien ne
        # les confrontait localement : un remplacement global y a mis la
        # ligne de base de la fixture `v2` a la place de la sienne, et seule
        # la CI l a vu.
        #
        # Ils vivent desormais dans `examples/dossier-v1/attendu.json`, la
        # CI les lit la, et ce cas verifie qu ils disent la realite.
        dossier = RACINE / "examples" / "dossier-v1"
        descr = dossier / "attendu.json"
        if not descr.is_file():
            pose("15", "le descripteur du dossier de revue dit la verite",
                 None, "attendu.json absent")
        else:
            a = json.loads(descr.read_bytes())["attendu"]
            archive_v1 = dossier / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"

            def bilan_de(args: list[str]) -> str:
                fini = subprocess.run([sys.executable] + args, cwd=str(dossier),
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
                sortie = (fini.stdout or "") + (fini.stderr or "")
                return next((l for l in sortie.splitlines()
                             if l.startswith("BILAN")), "aucun BILAN")

            mesures = {
                "verify_avec_corpus": bilan_de(
                    ["../../verify.py", archive_v1.name, "--corpus", "corpus"]),
                "verify_sans_corpus": bilan_de(
                    ["../../verify.py", archive_v1.name]),
                "attestation": bilan_de(
                    ["../../verify_attestation.py", archive_v1.name + ".jws",
                     "--archive", archive_v1.name,
                     "--trust-store", "trust-store.json", "--allow-test-keys"]),
                "horodatage": bilan_de(
                    ["../../timestamp.py", "verify", archive_v1.name + ".jws.ots",
                     "--subject", archive_v1.name + ".jws",
                     "--descriptor", archive_v1.name + ".jws.timestamp.json"]),
            }
            ecarts = ["%s : descripteur %r, obtenu %r" % (k, a[k], v)
                      for k, v in mesures.items() if a.get(k) != v]
            pose("15", "le descripteur du dossier de revue dit la verite",
                 not ecarts,
                 "les 4 valeurs du guide concordent" if not ecarts
                 else " ; ".join(ecarts[:2]))

    finally:
        shutil.rmtree(travail, ignore_errors=True)

    print()
    problemes = sum(1 for e, _, _ in _bilan if e == "PROBLEME")
    conformes = sum(1 for e, _, _ in _bilan if e == "OK")
    print("BILAN : %d/%d cas conformes, %d probleme(s)"
          % (conformes, len(_bilan), problemes))
    if problemes:
        print()
        print("Une archive peut etre intérieurement parfaite et n exporter qu une")
        print("partie de son registre. Si ce controle glisse vers le PASS, le")
        print("produit affirme une completude que personne n a etablie.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

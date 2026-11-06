# -*- coding: utf-8 -*-
"""La barriere avant publication : ce qui sort ne revient pas.

D OU VIENT CETTE SUITE
----------------------

De la condition C-5. Un auditeur telecharge aujourd hui le paquet ET le
magasin qui dit a quelle cle se fier, depuis le MEME endroit. Qui controle
cet endroit controle les deux : un faussaire capable d ecrire dans le depot
ajoute sa cle au magasin, signe une archive reconstruite, et tous les
controles passent.

**L attaque ne vise pas la cryptographie, elle vise la source unique.** Le
correctif est de publier l EMPREINTE du magasin sur un second canal.

CE QUE CETTE SUITE VERROUILLE
-----------------------------

  * la charge du second canal ne porte **aucun materiel de cle** -- cas 4 et
    5. Une charge qui emporterait un scalaire prive transformerait le
    correctif en divulgation ;
  * un magasin de TEST ne se publie pas comme officiel (cas 2) ;
  * l audit en echec ne produit AUCUNE charge (cas 6). Un audit qui avertit
    puis publie quand meme n est pas une barriere ;
  * l empreinte publiee est celle des OCTETS TRANSMIS (cas 7). La recalculer
    sur une re-serialisation rendrait un nombre que l auditeur ne retrouve
    pas sur le fichier telecharge -- le meme piege que le BOM des recus ;
  * le programme n a aucun acces reseau (cas 8). Il prepare une publication,
    il ne la fait pas.
"""
from __future__ import annotations

import ast
import hashlib
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
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def main() -> int:
    travail = Path(tempfile.mkdtemp(prefix="evidence-publication-"))
    try:
        commun = ["--signer-capacity", "experimental",
                  "--signer-registration", "RNA W563015824",
                  "--signer-jurisdiction", "FR",
                  "--valid-from", "2026-11-06T00:00:00Z"]
        prod = travail / "prod.json"
        code, s = lancer("sign.py", [
            "genkey", "--kid", "nm-p1", "--out", str(travail / "cle.json"),
            "--trust-store-out", str(prod), "--store-kind", "production",
            "--store-id", "neomundi-evidence"] + commun)
        assert code == 0, s
        essai = travail / "essai.json"
        code, s = lancer("sign.py", [
            "genkey", "--kid", "nm-t1", "--out", str(travail / "clet.json"),
            "--trust-store-out", str(essai), "--store-kind", "test",
            "--store-id", "neomundi-evidence-essai"] + commun)
        assert code == 0, s

        # ---- 1. un magasin de production passe l audit -----------------
        code_p, s_p = lancer("publish_store.py", ["audit", str(prod)])
        pose("1", "un magasin de production passe l audit",
             code_p == 0 and "0 FAIL" in s_p, "code %d" % code_p)

        # ---- 2. un magasin de TEST est refuse --------------------------
        code_t, s_t = lancer("publish_store.py", ["audit", str(essai)])
        pose("2", "un magasin de test est refuse a la publication",
             code_t == 1 and "store_kind: test" in s_t
             and "PUBLICATION REFUSEE" in s_t, "code %d" % code_t)

        # ---- 3. les NOT TESTED restent des NOT TESTED ------------------
        # Un audit sans FAIL n est pas un feu vert complet : les noms de
        # personnes ne sont pas decidables par un programme, et il le dit.
        pose("3", "un audit sans FAIL ne se donne pas pour complet",
             "NOT TESTED" in s_p and "relire par un humain" in s_p
             and "ne sait pas reconnaitre un nom" in s_p,
             "les limites sont ecrites")

        # ---- 4. la charge ne porte AUCUN materiel de cle ---------------
        sortie = travail / "charge.json"
        code_c, _ = lancer("publish_store.py",
                           ["payload", str(prod), "--out", str(sortie)])
        charge = json.loads(sortie.read_bytes()) if sortie.exists() else {}
        brut = sortie.read_text(encoding="utf-8") if sortie.exists() else ""
        magasin = json.loads(prod.read_bytes())
        public = magasin["keys"][0]["x"]
        # `x` est VOLONTAIREMENT absent, et c est la propriete qui compte :
        # une charge qui porterait la cle publique deviendrait elle-meme une
        # racine de confiance, et le second canal cesserait d etre un
        # TEMOIN pour devenir une seconde source a surveiller.
        pose("4", "la charge ne porte aucun materiel de cle",
             code_c == 0 and public not in brut and '"d"' not in brut
             and set(charge) == {"schema", "store_id", "store_version",
                                 "store_kind", "sha256",
                                 "updated_at_declared", "signers", "keys",
                                 "limits"},
             "%d champ(s), ni cle publique ni privee" % len(charge))

        # ---- 4b. et elle porte bien l identite, le `kid` et le statut ---
        # Un tiers doit pouvoir savoir CE QU IL regarde avant de telecharger
        # le magasin : qui s engage, sous quel `kid`, et en quelle capacite.
        sg = (charge.get("signers") or [{}])[0]
        kx = (charge.get("keys") or [{}])[0]
        pose("4b", "la charge nomme le signataire, le kid et la capacite",
             sg.get("legal_name") == "NeoMundi Recherche"
             and sg.get("registration_reference") == "RNA W563015824"
             and sg.get("legal_capacity_to_attest") == "experimental"
             and kx.get("kid") and kx.get("status")
             and charge["schema"].endswith("/2"),
             "%s / %s / %s" % (sg.get("identity_id"), kx.get("kid"),
                               sg.get("legal_capacity_to_attest")))

        # ---- 4c. la charge dit que l EMPREINTE fait foi ------------------
        # Dupliquer des metadonnees sur deux canaux cree un risque de
        # DIVERGENCE. La charge doit donc dire laquelle tranche, sinon un
        # tiers pourrait croire la prose plutot que le hachage.
        limites = " ".join(charge.get("limits") or [])
        pose("4c", "la charge declare que l empreinte fait foi",
             "EMPREINTE fait foi" in limites
             and "informatives" in limites
             and "certification juridique" in limites,
             "divergence et capacite enoncees")

        # ---- 5. un scalaire prive glisse dans le magasin est vu --------
        fuite = travail / "fuite.json"
        avec = json.loads(prod.read_bytes())
        avec["keys"][0]["d"] = "Zm9vYmFyYmF6cXV1eA"
        fuite.write_bytes(
            (json.dumps(avec, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        code_f, s_f = lancer("publish_store.py", ["audit", str(fuite)])
        pose("5", "un scalaire prive dans le magasin est refuse",
             code_f == 1 and "scalaire PRIVE" in s_f
             and "hors schema" in s_f,
             "repere deux fois : par motif et par champ")

        # ---- 6. un audit en echec ne produit AUCUNE charge -------------
        tentee = travail / "ne-doit-pas-exister.json"
        code_n, s_n = lancer("publish_store.py",
                             ["payload", str(fuite), "--out", str(tentee)])
        pose("6", "un audit en echec ne produit aucune charge",
             code_n == 1 and not tentee.exists()
             and "aucune charge n est produite" in s_n,
             "le fichier n a pas ete ecrit")

        # ---- 7. l empreinte est celle des OCTETS TRANSMIS --------------
        # Meme piege que le BOM des recus : re-serialiser pour normaliser
        # rendrait un nombre introuvable sur le fichier telecharge.
        attendue = hashlib.sha256(prod.read_bytes()).hexdigest()
        pose("7", "l empreinte publiee est celle des octets transmis",
             charge.get("sha256") == attendue,
             "%s..." % (charge.get("sha256") or "absente")[:16])

        # ---- 8. aucun acces reseau, et c est verifiable statiquement ---
        arbre = ast.parse((RACINE / "publish_store.py").read_text(encoding="utf-8"))
        importes: set[str] = set()
        for n in ast.walk(arbre):
            if isinstance(n, ast.Import):
                importes.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                importes.add(n.module.split(".")[0])
        reseau = importes & {"socket", "http", "urllib", "requests",
                             "httpx", "ftplib", "smtplib", "ssl"}
        pose("8", "le preparateur n a aucun acces reseau",
             not reseau, "importe %s" % ", ".join(sorted(importes)))

        # ---- 9. l empreinte produite est celle que le verificateur veut
        # Le circuit se referme : la charge du second canal se passe telle
        # quelle a `--store-digest`.
        fix = travail / "fix"
        lancer("tests/make_fixture.py", [str(fix), "--profile", "v2"])
        archive = fix / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"
        jws = travail / "a.jws"
        lancer("sign.py", ["attest", "--archive", str(archive),
                           "--key", str(travail / "cle.json"), "--out", str(jws),
                           "--attested-at", "2026-11-06T13:00:00Z"])
        code_v, s_v = lancer("verify_attestation.py", [
            str(jws), "--archive", str(archive), "--trust-store", str(prod),
            "--store-digest", charge.get("sha256", "")])
        ligne = next((l for l in s_v.splitlines()
                      if "empreinte du magasin" in l), "")
        pose("9", "la charge se passe telle quelle a --store-digest",
             "[PASS" in ligne, ligne[:62] or "ligne absente")

        # ---- 10b. un magasin `production` ne porte aucune cle `test` ---
        # Constate le 6 novembre : basculer `store_kind` a `production` en
        # laissant les cles au statut `test` passait cet audit. Le
        # verificateur, lui, refuse ces cles -- on aurait donc publie une
        # racine de confiance qui n accorde RIEN, et le defaut n aurait
        # apparu qu au premier auditeur qui l essaie.
        menteur = travail / "menteur.json"
        d = json.loads(essai.read_bytes())
        d["store_kind"] = "production"
        menteur.write_bytes(
            (json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        code_m, s_m = lancer("publish_store.py", ["audit", str(menteur)])
        pose("10b", "un magasin de production sans aucune cle de test",
             code_m == 1 and "cle(s) de statut `test`" in s_m
             and "n accorde rien" in s_m,
             "code %d" % code_m)

        # ---- 10c. les identifiants sont confrontes au motif du schema ---
        # Aucune validation de schema ne tourne dans ce depot : sans ce
        # controle, un `identity_id` non conforme rend le magasin invalide
        # EN SILENCE. La procedure operateur en produisait un.
        tordu = travail / "tordu.json"
        d2 = json.loads(prod.read_bytes())
        d2["identities"][0]["identity_id"] = "NeoMundi Recherche"
        d2["keys"][0]["signer_identity"] = "NeoMundi Recherche"
        tordu.write_bytes(
            (json.dumps(d2, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        code_t, s_t = lancer("publish_store.py", ["audit", str(tordu)])
        pose("10c", "un identifiant non conforme au schema est refuse",
             code_t == 1 and "identifiants conformes au schema" in s_t
             and "NeoMundi Recherche" in s_t,
             "code %d" % code_t)

        # ---- 10d. `unverified` sur un magasin de production est signale --
        # Pas un FAIL : `unverified` reste une valeur legitime. Mais apres
        # la decision B-1, c est le symptome d un `--signer-capacity`
        # oublie -- exactement ce que produisait la procedure operateur.
        oubli = travail / "oubli.json"
        code_o, _ = lancer("sign.py", [
            "genkey", "--kid", "nm-o1", "--out", str(travail / "ko.json"),
            "--trust-store-out", str(oubli), "--store-kind", "production",
            "--store-id", "neomundi-evidence",
            "--valid-from", "2026-11-06T00:00:00Z"])
        _, s_o = lancer("publish_store.py", ["audit", str(oubli)])
        pose("10d", "`unverified` sur un magasin de production est signale",
             code_o == 0 and "se publie en `unverified`" in s_o
             and "oubli de" in s_o and "0 FAIL" in s_o,
             "signale sans refuser")

        # ---- 10. une empreinte FAUSSE est refusee ----------------------
        _, s_m = lancer("verify_attestation.py", [
            str(jws), "--archive", str(archive), "--trust-store", str(prod),
            "--store-digest", "0" * 64])
        ligne_m = next((l for l in s_m.splitlines()
                        if "empreinte du magasin" in l), "")
        pose("10", "une empreinte de magasin fausse est refusee",
             "[FAIL" in ligne_m, ligne_m[:62] or "ligne absente")

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
        print("Une publication est irreversible. Si cette suite echoue, la")
        print("barriere qui empeche un materiel prive de sortir ne tient plus")
        print("-- et ce qui sort ne revient pas.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

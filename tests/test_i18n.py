# -*- coding: utf-8 -*-
"""La langue ne change que la PROSE. Rien d autre, jamais.

CE QUE CETTE SUITE VERROUILLE
-----------------------------

Quatre choses doivent etre IDENTIQUES en francais et en anglais, et c est
tout l enjeu de la condition C-6 :

  * le nombre de lignes de controle, et leur ORDRE ;
  * les etats -- `PASS`, `FAIL`, `NOT TESTED` -- qui sont des termes du
    contrat et non de la prose ;
  * les codes de sortie, en mode normal comme en mode strict ;
  * les empreintes, et les noms de champs du rapport JSON.

Traduire ne doit rien pouvoir casser. Une suite qui se contenterait de
verifier que la sortie anglaise << a l air anglaise >> laisserait passer un
decalage de verdict, qui est le seul risque reel de ce chantier.

ET LA COUVERTURE EST MESUREE, PAS AFFIRMEE
------------------------------------------

Le cas 7 exerce l outil sur de vraies archives et echoue si la moindre
ligne ressort avec de la prose francaise non traduite. C est ce cas, et lui
seul, qui autorise a ecrire que la sortie de `verify.py` est bilingue : le
catalogue ne se declare pas complet, il se constate complet sur ce qui est
reellement emis.

`i18n.residu` ne considere PAS comme un residu une chaine faite uniquement
de donnees -- une empreinte, une liste de noms de fichiers, un decompte. Il
n y a rien a y traduire, et exiger qu elles changent serait exiger qu on
abime les donnees.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
import re as _re

import i18n  # noqa: E402

#: `[PASS      ] `, `[NOT TESTED] `, `[NOT COMPARABLE] ` en tete de ligne.
#: Retire par MOTIF : rogner caractere par caractere mangeait la premiere
#: lettre de la prose -- << AUCUNE >> devenait << UCUNE >> -- et produisait
#: des faux positifs.
_PREFIXE_ETAT = _re.compile(r"^\[[A-Z ]+\]\s*")

_bilan: list[tuple[str, str, str]] = []


def pose(numero: str, intitule: str, conforme: bool | None, detail: str = "") -> None:
    etat = "OK" if conforme else ("INAPPLICABLE" if conforme is None else "PROBLEME")
    _bilan.append((etat, numero, intitule))
    print("[%-9s] %-3s %-56s %s" % (etat, numero, intitule, detail))


def lancer_outil(outil: str, args: list[str]) -> tuple[int, str]:
    fini = subprocess.run(
        [sys.executable, str(RACINE / outil)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return fini.returncode, (fini.stdout or "") + (fini.stderr or "")


def lancer(args: list[str]) -> tuple[int, str]:
    return lancer_outil("verify.py", args)


def lignes_de_controle(sortie: str) -> list[tuple[str, str]]:
    """Les lignes `[ETAT     ] intitule - detail`, en (etat, reste)."""
    trouvees = []
    for ligne in sortie.splitlines():
        if ligne.startswith("[") and "]" in ligne:
            etat = ligne[1:ligne.index("]")].strip()
            trouvees.append((etat, ligne[ligne.index("]") + 1:].strip()))
    return trouvees


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: test_i18n.py <archive> [corpus]")
        return 2
    archive = sys.argv[1]
    corpus = sys.argv[2] if len(sys.argv) > 2 else None
    base = [archive] + (["--corpus", corpus] if corpus else [])
    travail = Path(tempfile.mkdtemp(prefix="evidence-i18n-"))

    try:
        code_fr, s_fr = lancer(base + ["--lang", "fr"])
        code_en, s_en = lancer(base + ["--lang", "en"])
        l_fr = lignes_de_controle(s_fr)
        l_en = lignes_de_controle(s_en)

        # ---- 1. meme nombre de lignes ----------------------------------
        pose("1", "meme nombre de lignes de controle",
             len(l_fr) == len(l_en) and len(l_fr) > 0,
             "%d lignes de part et d autre" % len(l_fr))

        # ---- 2. memes etats, dans le MEME ORDRE ------------------------
        # C est le controle qui compte : un decalage de verdict est le seul
        # risque reel de ce chantier.
        etats_fr = [e for e, _ in l_fr]
        etats_en = [e for e, _ in l_en]
        pose("2", "memes etats, dans le meme ordre",
             etats_fr == etats_en,
             "%s" % ("identiques" if etats_fr == etats_en
                     else "DECALAGE : %r vs %r" % (etats_fr, etats_en)))

        # ---- 3. meme code de sortie ------------------------------------
        pose("3", "meme code de sortie", code_fr == code_en,
             "fr=%d en=%d" % (code_fr, code_en))

        # ---- 4. meme code de sortie en mode STRICT ---------------------
        c_fr, t_fr = lancer(base + ["--lang", "fr", "--strict"])
        c_en, t_en = lancer(base + ["--lang", "en", "--strict"])
        pose("4", "meme code de sortie en mode strict", c_fr == c_en,
             "fr=%d en=%d" % (c_fr, c_en))

        # ---- 5. les empreintes sont IDENTIQUES -------------------------
        # Une empreinte traduite serait une empreinte fausse.
        import re
        emp_fr = sorted(set(re.findall(r"\b[0-9a-f]{16,64}\b", s_fr)))
        emp_en = sorted(set(re.findall(r"\b[0-9a-f]{16,64}\b", s_en)))
        pose("5", "les empreintes sont identiques, au caractere",
             emp_fr == emp_en and len(emp_fr) > 0,
             "%d empreinte(s) communes" % len(emp_fr))

        # ---- 6. le rapport JSON : memes NOMS de champs, memes valeurs
        # contractuelles. Seule la prose des intitules change.
        j_fr, j_en = travail / "fr.json", travail / "en.json"
        lancer(base + ["--lang", "fr", "--json", str(j_fr)])
        lancer(base + ["--lang", "en", "--json", str(j_en)])
        d_fr = json.loads(j_fr.read_bytes())
        d_en = json.loads(j_en.read_bytes())

        def noms(o, prefixe=""):
            if isinstance(o, dict):
                for k, v in sorted(o.items()):
                    yield prefixe + k
                    yield from noms(v, prefixe + k + ".")
            elif isinstance(o, list) and o:
                yield from noms(o[0], prefixe + "[].")

        pose("6", "rapport JSON : memes noms de champs",
             list(noms(d_fr)) == list(noms(d_en)),
             "%d champs" % len(list(noms(d_fr))))

        # ---- 6b. et les decomptes du rapport ne bougent pas ------------
        def decomptes(d):
            return {k: v for k, v in d.items() if isinstance(v, (int, float))}
        pose("6b", "rapport JSON : memes decomptes",
             decomptes(d_fr) == decomptes(d_en),
             "%s" % decomptes(d_fr))

        # ---- 7. AUCUN RESIDU : la couverture est MESUREE ---------------
        # C est ce cas, et lui seul, qui autorise a dire que la sortie est
        # bilingue. Le catalogue ne se declare pas complet : il se constate
        # complet sur ce qui est reellement emis.
        def morceaux(reste: str) -> tuple[str, str]:
            if " - " in reste:
                a, b = reste.split(" - ", 1)
                return a, b
            return reste, ""

        residus: list[str] = []
        # On interroge le FRANCAIS, apparie a son anglais. `residu` demande
        # << cette chaine francaise serait-elle rendue non traduite ? >> ;
        # la nourrir avec l anglais signalerait de l anglais deja traduit.
        for (_, reste_fr), (_, reste_en) in zip(l_fr, l_en):
            for m_fr, m_en in zip(morceaux(reste_fr), morceaux(reste_en)):
                if m_fr != m_en:
                    continue          # traduit : rien a dire
                if i18n.residu(m_fr, i18n.EN):
                    residus.append(m_fr[:72])
        # La prose d encadrement compte aussi, appariee de la meme facon.
        prose_fr = [l.strip() for l in s_fr.splitlines()
                    if l.strip() and not l.startswith("[")]
        prose_en = [l.strip() for l in s_en.splitlines()
                    if l.strip() and not l.startswith("[")]
        for a, b in zip(prose_fr, prose_en):
            if a == b and i18n.residu(a, i18n.EN):
                residus.append(a[:72])
        pose("7", "AUCUN residu francais dans la sortie anglaise",
             not residus,
             "couverture complete, constatee"
             if not residus else "%d residu(s) : %s" % (len(residus), residus[:3]))

        # ---- 8. le francais n a PAS change ----------------------------
        # Le defaut doit rester le francais, a l octet pres.
        code_defaut, s_defaut = lancer(base)
        pose("8", "sans --lang, la sortie francaise est inchangee",
             s_defaut == s_fr and code_defaut == code_fr,
             "le defaut reste le francais")

        # ---- 9. une langue inconnue est REFUSEE, pas devinee -----------
        code_x, s_x = lancer(base + ["--lang", "de"])
        pose("9", "une langue inconnue est refusee",
             code_x != 0 and "invalid choice" in s_x.lower(),
             "code %d" % code_x)

        # ---- 10. l outil tourne SANS i18n.py, et en francais -----------
        # Les 21 controles ne doivent jamais dependre de la traduction.
        seul = travail / "seul"
        seul.mkdir()
        shutil.copy2(RACINE / "verify.py", seul / "verify.py")
        fini = subprocess.run(
            [sys.executable, str(seul / "verify.py")] + base,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(seul),
        )
        pose("10", "sans `i18n.py` a cote, memes verdicts, en francais",
             fini.returncode == code_fr
             and lignes_de_controle(fini.stdout or "") == l_fr,
             "la traduction est OPTIONNELLE")

        # ---- 13. LES CHEMINS D ECHEC, ou vit la prose ------------------
        # Le cas 7 mesure sur l archive fournie, qui passe tout. La prose
        # francaise vit surtout dans les chemins d echec : c est la qu un
        # controle explique ce qui manque. Un balayage manuel y a trouve un
        # residu que le cas 7 ne voyait pas, d ou ce cas-ci.
        import zipfile

        def fabrique(nom: str, transforme=None, retirer=None) -> str:
            cible = travail / nom
            with zipfile.ZipFile(archive) as z, zipfile.ZipFile(cible, "w") as o:
                for info in z.infolist():
                    if retirer and info.filename == retirer:
                        continue
                    octets = z.read(info.filename)
                    if transforme:
                        octets = transforme(info.filename, octets)
                    o.writestr(info, octets)
            return str(cible)

        def _schema_faux(nom, octets):
            if nom == "manifest.json":
                m = json.loads(octets)
                m["schema"] = "pas.un.schema/9"
                return json.dumps(m).encode("utf-8")
            return octets

        def _membre_altere(nom, octets):
            return (octets + b'\n{"bidon":1}\n'
                    if nom.endswith("measurements.jsonl") else octets)

        def _manifeste_casse(nom, octets):
            return b"{ pas du json" if nom == "manifest.json" else octets

        pas_un_zip = travail / "pasunzip.zip"
        pas_un_zip.write_bytes(b"ceci n est pas un zip")

        regimes = {
            "membre altere": [fabrique("alt.zip", _membre_altere)],
            "sans manifeste": [fabrique("sm.zip", retirer="manifest.json")],
            "manifeste casse": [fabrique("mc.zip", _manifeste_casse)],
            "schema inconnu": [fabrique("si.zip", _schema_faux)],
            "sans sommes": [fabrique("ss.zip", retirer="checksums.sha256")],
            "pas un zip": [str(pas_un_zip)],
            "introuvable": [str(travail / "nexistepas.zip")],
        }

        residus_echec: list[str] = []
        codes_divergents: list[str] = []
        for nom_regime, args in regimes.items():
            cf, sf = lancer(args + ["--lang", "fr"])
            ce, se = lancer(args + ["--lang", "en"])
            if cf != ce:
                codes_divergents.append("%s : fr=%d en=%d" % (nom_regime, cf, ce))
            lf, le = lignes_de_controle(sf), lignes_de_controle(se)
            if [e for e, _ in lf] != [e for e, _ in le]:
                codes_divergents.append("%s : etats decales" % nom_regime)
            for (_, rf), (_, re_) in zip(lf, le):
                for a, b in zip(morceaux(rf), morceaux(re_)):
                    if a == b and i18n.residu(a, i18n.EN):
                        residus_echec.append("%s : %s" % (nom_regime, a[:56]))

        pose("13", "aucun residu sur 7 regimes d ECHEC",
             not residus_echec,
             "7 regimes fautifs balayes" if not residus_echec
             else "%d residu(s) : %s" % (len(residus_echec), residus_echec[:2]))

        pose("14", "memes etats et memes codes sur les 7 regimes d echec",
             not codes_divergents,
             "aucun decalage" if not codes_divergents
             else "; ".join(codes_divergents[:2]))

        # ---- 11. le catalogue ne porte aucun doublon de sens -----------
        # Une meme chaine francaise dans EXACT et dans FORMATS rendrait la
        # traduction dependante de l ordre des etages.
        communs = set(i18n.EXACT) & set(i18n.FORMATS)
        pose("11", "aucune chaine n est a la fois EXACT et FORMAT",
             not communs,
             "catalogue : %d exacts, %d formats"
             % (len(i18n.EXACT), len(i18n.FORMATS))
             if not communs else "en double : %s" % sorted(communs))

        # ---- 12. chaque format anglais porte les MEMES marques --------
        # Un format anglais qui perdrait un `%s` mangerait une donnee ; un
        # qui en gagnerait un planterait a l emission.
        desaccords: list[str] = []
        for fr, en in i18n.FORMATS.items():
            def marques(t: str) -> list[str]:
                out, i = [], 0
                while i < len(t):
                    if t[i] == "%" and i + 1 < len(t):
                        if t[i + 1] == "%":
                            i += 2
                            continue
                        if t[i + 1] in "dsr":
                            out.append("d" if t[i + 1] == "d" else "s")
                            i += 2
                            continue
                    i += 1
                return out
            if marques(fr) != marques(en):
                desaccords.append("%r -> %r" % (fr[:38], en[:38]))
        pose("12", "chaque format anglais porte les memes marques que le francais",
             not desaccords,
             "%d format(s) verifies" % len(i18n.FORMATS)
             if not desaccords else "; ".join(desaccords[:2]))

        # ---- 15 a 20. les memes garanties sur verify_attestation.py ----
        # C est l outil qui porte le niveau `cryptographically_attested`.
        D = RACINE / "examples" / "dossier-v1"
        jws = D / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws"
        zipp = D / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"
        magasin = D / "trust-store.json"
        if jws.is_file() and zipp.is_file() and magasin.is_file():
            socle = [str(jws), "--archive", str(zipp),
                     "--trust-store", str(magasin), "--allow-test-keys"]
            af, saf = lancer_outil("verify_attestation.py", socle + ["--lang", "fr"])
            ae, sae = lancer_outil("verify_attestation.py", socle + ["--lang", "en"])
            laf, lae = lignes_de_controle(saf), lignes_de_controle(sae)

            pose("15", "attestation : meme nombre de lignes",
                 len(laf) == len(lae) and len(laf) > 0,
                 "%d lignes" % len(laf))
            pose("16", "attestation : memes etats, meme ordre",
                 [e for e, _ in laf] == [e for e, _ in lae],
                 "identiques")
            pose("17", "attestation : meme code de sortie", af == ae,
                 "fr=%d en=%d" % (af, ae))

            sf2 = lancer_outil("verify_attestation.py", socle + ["--lang", "fr", "--strict"])[0]
            se2 = lancer_outil("verify_attestation.py", socle + ["--lang", "en", "--strict"])[0]
            pose("18", "attestation : meme code en mode strict", sf2 == se2,
                 "fr=%d en=%d" % (sf2, se2))

            residus_a: list[str] = []
            for (_, rf), (_, re_) in zip(laf, lae):
                for a, b in zip(morceaux(rf), morceaux(re_)):
                    if a == b and i18n.residu(a, i18n.EN):
                        residus_a.append(a[:64])
            pa = [l.strip() for l in saf.splitlines()
                  if l.strip() and not l.startswith("[")]
            pe = [l.strip() for l in sae.splitlines()
                  if l.strip() and not l.startswith("[")]
            for a, b in zip(pa, pe):
                if a == b and i18n.residu(a, i18n.EN):
                    residus_a.append(a[:64])
            pose("19", "attestation : AUCUN residu francais en anglais",
                 not residus_a,
                 "couverture constatee" if not residus_a
                 else "%d residu(s) : %s" % (len(residus_a), residus_a[:2]))

            # ---- 20. LE NIVEAU est un terme du CONTRAT -----------------
            # S il se traduisait, un consommateur qui compare la chaine ne
            # reconnaitrait plus le niveau atteint.
            pose("20", "le NIVEAU n est jamais traduit",
                 "cryptographically_attested" in saf
                 and "cryptographically_attested" in sae,
                 "le terme contractuel est intact dans les deux langues")
        else:
            for n in ("15", "16", "17", "18", "19", "20"):
                pose(n, "attestation : garanties FR/EN", None,
                     "dossier de demonstration absent")

        # ---- 21 a 24. LES SIX OUTILS, sur 17 scenarios ----------------
        import zipfile

        V = RACINE / "examples" / "dossier-v1"
        W = RACINE / "examples" / "timestamp"
        ATT = RACINE / "examples" / "attestation"

        # Une archive fautive, pour exercer les chemins d echec.
        mauvaise = travail / "mauvaise.zip"
        with zipfile.ZipFile(archive) as z, zipfile.ZipFile(mauvaise, "w") as o:
            for info in z.infolist():
                d = z.read(info.filename)
                if info.filename.endswith("measurements.jsonl"):
                    d += b'\n{"bidon":1}\n'
                o.writestr(info, d)

        # Un manifeste de liaison, construit pour l occasion.
        liaison = travail / "liaison"
        liaison.mkdir()
        shutil.copytree(str(RACINE / "examples" / "binding"), str(liaison / "b"),
                        dirs_exist_ok=True) if (RACINE / "examples" / "binding").is_dir() else None

        scenarios = [
            ("verify valide", "verify.py", [archive] + (["--corpus", corpus] if corpus else [])),
            ("verify fautif", "verify.py", [str(mauvaise)]),
            ("attestation complete", "verify_attestation.py",
             [str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws"),
              "--archive", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"),
              "--trust-store", str(V / "trust-store.json"), "--allow-test-keys"]),
            ("attestation nue", "verify_attestation.py",
             [str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws")]),
            ("timestamp inspect conf", "timestamp.py",
             ["inspect", str(W / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.confirmed.ots")]),
            ("timestamp inspect pend", "timestamp.py",
             ["inspect", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots")]),
            ("timestamp verify conf", "timestamp.py",
             ["verify", str(W / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.confirmed.ots"),
              "--subject", str(ATT / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws"),
              "--descriptor",
              str(W / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.confirmed.timestamp.json")]),
            ("timestamp verify pend", "timestamp.py",
             ["verify", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots"),
              "--subject", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws"),
              "--descriptor", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.timestamp.json")]),
            ("timestamp verify nu", "timestamp.py",
             ["verify", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots")]),
            ("timestamp introuvable", "timestamp.py",
             ["inspect", str(travail / "nexistepas.ots")]),
            ("reconcile", "adapters/reconcile.py",
             [str(V / "receipt-imported.json"),
              "--archive", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"),
              "--map", str(V / "map-comparable.json")]),
            ("reconcile sans contexte", "adapters/reconcile.py",
             [str(V / "receipt-imported.json"),
              "--archive", str(V / "NEOMUNDI_EVIDENCE_V1_DEMO.zip"),
              "--map", str(V / "map-no-context.json")]),
            ("receipt_import", "adapters/receipt_import.py",
             [str(V / "receipt-synthetic.html"), "--received-at",
              "2026-11-06T00:00:00Z", "--out", str(travail / "r.json")]),
        ]

        # LA REGLE DES DONNEES : ce qui figure verbatim dans une entree est
        # une donnee. On rassemble le texte des entrees lisibles.
        entrees = b""
        for f in (V / "receipt-imported.json", V / "map-comparable.json",
                  V / "map-no-context.json", V / "receipt-synthetic.html"):
            if f.is_file():
                entrees += f.read_bytes()
        texte_entrees = entrees.decode("utf-8", "replace")

        residus_outils: list[str] = []
        codes_divergents: list[str] = []
        donnees_intactes = 0
        for titre, outil, args in scenarios:
            cf, sf = lancer_outil(outil, [str(a) for a in args] + ["--lang", "fr"])
            ce, se = lancer_outil(outil, [str(a) for a in args] + ["--lang", "en"])
            if cf != ce:
                codes_divergents.append("%s : fr=%d en=%d" % (titre, cf, ce))
            for a, b in zip(sf.splitlines(), se.splitlines()):
                if a.rstrip() != b.rstrip():
                    continue
                nettoye = _PREFIXE_ETAT.sub("", a.strip(), count=1)
                for bout in nettoye.split(" - "):
                    nu = bout.strip()
                    if not i18n.residu(nu, i18n.EN):
                        continue
                    # La regle des donnees.
                    if nu and nu[:40] in texte_entrees:
                        donnees_intactes += 1
                        continue
                    residus_outils.append("%s : %s" % (titre, nu[:52]))

        # ---- 21b. LE CONTROLE QUI MANQUAIT -----------------------------
        #
        # `residu` demande << traduisible ? >>, pas << traduite ? >>. Le
        # 6 novembre `receipt_import.py` ne traduisait RIEN -- son
        # `import i18n` echouait, parce que lance depuis `adapters/` la
        # racine n est pas sur `sys.path` -- et le cas 21 le declarait
        # conforme, puisque ses chaines etaient bien au catalogue.
        #
        # Celui-ci est une CONTRADICTION, pas une heuristique : le
        # catalogue promet que la chaine change, et elle n a pas change.
        non_traduits: list[str] = []
        for titre, outil, args in scenarios:
            _, sf = lancer_outil(outil, [str(a) for a in args] + ["--lang", "fr"])
            _, se = lancer_outil(outil, [str(a) for a in args] + ["--lang", "en"])
            for a, b in zip(sf.splitlines(), se.splitlines()):
                a, b = a.rstrip(), b.rstrip()
                if a != b:
                    continue
                nettoye = _PREFIXE_ETAT.sub("", a.strip(), count=1)
                for bout in nettoye.split(" - "):
                    nu = bout.strip()
                    if i18n.devrait_changer(nu, i18n.EN):
                        non_traduits.append("%s : %s" % (titre, nu[:50]))

        pose("21b", "aucune chaine que le catalogue promet de traduire ne sort en francais",
             not non_traduits,
             "le catalogue et la sortie concordent"
             if not non_traduits
             else "%d chaine(s) NON TRADUITE(S) : %s"
                  % (len(non_traduits), non_traduits[:2]))

        pose("21", "les SIX outils : aucun residu francais en anglais",
             not residus_outils,
             "%d scenarios balayes" % len(scenarios) if not residus_outils
             else "%d residu(s) : %s" % (len(residus_outils), residus_outils[:2]))

        pose("22", "memes codes de sortie sur les %d scenarios" % len(scenarios),
             not codes_divergents,
             "aucun ecart" if not codes_divergents
             else "; ".join(codes_divergents[:2]))

        # ---- 23. la regle des donnees n est pas une echappatoire -------
        # Il doit EXISTER du texte venu d une entree qui ressort inchange.
        # Sans ce cas, << c est une donnee >> excuserait n importe quoi.
        pose("23", "du texte venu d une ENTREE ressort inchange, et c est voulu",
             donnees_intactes > 0,
             "%d occurrence(s) conservee(s) verbatim" % donnees_intactes)

        # ---- 24. les six outils exposent bien --lang -------------------
        sans_option = []
        for outil, sonde in (("verify.py", ["--help"]),
                             ("verify_attestation.py", ["--help"]),
                             ("timestamp.py", ["verify", "--help"]),
                             ("bind.py", ["verify", "--help"]),
                             ("sign.py", ["attest", "--help"]),
                             ("adapters/reconcile.py", ["--help"]),
                             ("adapters/receipt_import.py", ["--help"])):
            _, aide = lancer_outil(outil, sonde)
            if "--lang" not in aide:
                sans_option.append(outil)
        pose("24", "chaque outil expose --lang {fr,en}",
             not sans_option,
             "7 outils" if not sans_option else "sans option : %s" % sans_option)

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
        print("La langue ne doit changer que la prose. Un etat, un code de")
        print("sortie, un nom de champ ou une empreinte qui bouge avec la")
        print("langue est un defaut, pas une traduction.")
    return 1 if problemes else 0


if __name__ == "__main__":
    raise SystemExit(main())

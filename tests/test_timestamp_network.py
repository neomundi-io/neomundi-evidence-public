# -*- coding: utf-8 -*-
"""Tests d INTEGRATION de l horodatage. TOUCHENT LE RESEAU.

    python tests/test_timestamp_network.py [--stamp]

**Ne tournent JAMAIS en integration continue.** Une suite qui depend de
quatre serveurs tiers echouerait pour des raisons qui ne sont pas des
defauts du produit, et une CI rouge sans cause interne apprend a ignorer le
rouge.

CE QUI QUITTE LE POSTE
----------------------

Sans `--stamp` : rien n est soumis. On interroge seulement les calendriers
sur une empreinte DEJA soumise, celle de la preuve d exemple. C est une
lecture.

Avec `--stamp` : une empreinte de 32 octets est soumise, et **une seule** --
celle d un fichier temporaire fabrique pour ce test. Jamais une archive,
jamais un manifeste, jamais une donnee de pilote.

POURQUOI `upgrade` NE PEUT PAS ETRE EPROUVE JUSQU AU BOUT
---------------------------------------------------------

Passer de PENDING a CONFIRMED demande que Bitcoin confirme la transaction du
calendrier : quelques heures. Ce test verifie donc que `upgrade` se comporte
correctement **quand rien n a encore progresse** -- qu il le dit, qu il
n ecrase pas l ancienne preuve, et qu il n invente aucune attestation.

Le chemin << une attestation Bitcoin apparait >> est couvert hors reseau par
une fixture synthetique, dans `tests/test_timestamp.py` (cas 22 et 23).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
OUTIL = RACINE / "timestamp.py"
PREUVE = RACINE / "examples" / "timestamp" / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.ots"
SUJET = RACINE / "examples" / "attestation" / "NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws"


def lancer(args: list[str]) -> tuple[int, str]:
    fini = subprocess.run([sys.executable, str(OUTIL)] + args, capture_output=True,
                          text=True, check=False, encoding="utf-8", errors="replace")
    return fini.returncode, fini.stdout + fini.stderr


def main() -> int:
    stamper = "--stamp" in sys.argv
    travail = Path(tempfile.mkdtemp(prefix="ots-reseau-"))
    resultats = []

    print("Tests d INTEGRATION de l horodatage -- RESEAU")
    print("soumission d une nouvelle empreinte : %s\n"
          % ("OUI (--stamp)" if stamper else "non"))

    try:
        # ---- 1. upgrade sur une preuve encore PENDING -----------------
        avant = PREUVE.read_bytes()
        nouvelle = travail / "upgradee.ots"
        code, s = lancer(["upgrade", str(PREUVE), "--out", str(nouvelle)])
        intacte = PREUVE.read_bytes() == avant
        dit = "Rien n a progresse" in s or "attestation Bitcoin" in s
        resultats.append((
            "1", "upgrade sur une preuve PENDING",
            code == 0 and intacte and dit,
            "ancienne intacte : %s ; etat dit : %s" % (intacte, dit),
        ))

        # ---- 2. upgrade refuse d ecraser sa sortie --------------------
        code2, s2 = lancer(["upgrade", str(PREUVE), "--out", str(nouvelle)])
        resultats.append((
            "2", "upgrade refuse d ecraser une preuve existante",
            code2 != 0 and "existe deja" in s2,
            "refus sans --force : une preuve est une piece",
        ))

        # ---- 3. la preuve issue d upgrade reste liee au meme sujet ----
        if nouvelle.is_file():
            code3, s3 = lancer(["verify", str(nouvelle), "--subject", str(SUJET)])
            resultats.append((
                "3", "la preuve mise a niveau reste liee au meme sujet",
                code3 == 0 and "liaison a l empreinte du sujet" in s3,
                "liaison preservee",
            ))

        # ---- 4. horodatage d une empreinte neuve, si demande ---------
        if stamper:
            sujet = travail / "sujet-de-test.txt"
            sujet.write_text(
                "Fichier fabrique pour le test d integration. Seule son "
                "empreinte quitte ce poste.\n", encoding="utf-8")
            print("  empreinte soumise : %s"
                  % hashlib.sha256(sujet.read_bytes()).hexdigest())
            code4, s4 = lancer([
                "stamp", str(sujet), "--out", str(travail / "neuve.ots"),
                "--descriptor", str(travail / "neuve.json"),
                "--stamped-at", "2026-11-05T22:00:00Z", "--timeout", "20",
            ])
            soumis = s4.count("[SOUMIS")
            resultats.append((
                "4", "stamp : au moins un calendrier repond",
                code4 == 0 and soumis >= 1,
                "%d calendrier(s) sur 4 ont repondu" % soumis,
            ))
            if code4 == 0:
                code5, s5 = lancer([
                    "verify", str(travail / "neuve.ots"), "--subject", str(sujet),
                    "--descriptor", str(travail / "neuve.json"),
                ])
                resultats.append((
                    "5", "la preuve neuve se verifie, et est PENDING",
                    code5 == 0 and "PENDING" in s5,
                    "liaison et descripteur concordants, etat PENDING",
                ))
        else:
            resultats.append((
                "4", "stamp : au moins un calendrier repond", None,
                "non execute : relancer avec --stamp pour soumettre",
            ))
    finally:
        shutil.rmtree(travail, ignore_errors=True)

    print()
    echecs, inapplicables = [], []
    for numero, intitule, reussi, constat in resultats:
        if reussi is None:
            etiquette, _ = "INAPPLIC.", inapplicables.append(numero)
        else:
            etiquette = "OK" if reussi else "PROBLEME"
            if not reussi:
                echecs.append("%s %s" % (numero, intitule))
        print("[%-9s] %-3s %-52s %s" % (etiquette, numero, intitule[:52], constat[:66]))

    eprouves = len(resultats) - len(inapplicables)
    print("\nBILAN : %d/%d cas conformes, %d non execute(s)"
          % (eprouves - len(echecs), eprouves, len(inapplicables)))
    for e in echecs:
        print("  PROBLEME : %s" % e)

    print("\nCes tests touchent des serveurs tiers. Un echec peut venir d eux, et")
    print("c est pourquoi ils ne tournent jamais en integration continue.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())

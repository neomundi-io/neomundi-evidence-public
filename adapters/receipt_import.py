# -*- coding: utf-8 -*-
"""Importe un recu de preuve externe, SANS en interpreter le sens.

    python adapters/receipt_import.py <recu.html|recu.json> \\
        --received-at 2026-11-05T12:00:00Z --out recu.json

CE QUE CE PROGRAMME FAIT, ET CE QU IL REFUSE DE FAIRE
-----------------------------------------------------

Il extrait des CHAMPS CANDIDATS d un document tiers, chacun avec son chemin
d origine dans le document, et les empreintes qu il y trouve. Il conserve
les valeurs **verbatim**.

Il ne devine **aucune** correspondance avec nos champs. Decider que le
`g_score` d un tiers correspond a notre `g_score` est une affirmation sur
deux definitions, et aucun extracteur ne peut la porter. Cette
correspondance doit etre DECLAREE, dans une table de correspondance
explicite que `reconcile.py` exige -- sinon le champ ressort
`NOT COMPARABLE`.

Un champ dont le chemin ne resout pas est **absent**, jamais `null` : la
distinction est la meme que pour un signal non mesure.

**Un recu HTML n est pas une preuve primaire.** Il ne le devient pas en
portant un << hash de recu >> : un condense calcule par l emetteur et publie
par l emetteur n atteste rien de plus que sa propre coherence interne. Ce
programme ne qualifie donc JAMAIS un recu de << signe >>.

Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import sys
from pathlib import Path

SCHEMA = "neomundi.evidence.external-receipt/1"

#: Une empreinte SHA-256 en hexadecimal, pour la reperer dans un texte.
MOTIF_SHA256 = re.compile(r"\b[0-9a-f]{64}\b")

#: Un nombre decimal, pour reperer une valeur mesurable. On ne l INTERPRETE
#: pas : on note seulement que la chaine en a la forme.
MOTIF_NOMBRE = re.compile(r"^-?\d+(?:[.,]\d+)?$")

#: Plafond de lecture. Un recu de plusieurs mega-octets n est pas un recu,
#: et le hacher aveuglement transformerait l import en attente indefinie.
PLAFOND = 8 * 1024 * 1024


class Illisible(Exception):
    """Une entree n a pas la forme attendue. Rendue en erreur motivee."""


class Extracteur(html.parser.HTMLParser):
    """Releve les paires etiquette/valeur d un HTML, avec leur chemin.

    Trois formes sont relevees, parce que ce sont celles qu on rencontre :
    les lignes de tableau, les couples `<dt>`/`<dd>`, et les elements
    portant un attribut `data-field`. Le reste du texte est conserve a
    part, pour que rien ne soit perdu en silence.

    Volontairement tolerant : un document tiers peut etre mal forme, et
    refuser de le lire n apprendrait rien. En revanche il n est jamais
    << repare >> : ce qui n est pas compris est signale, pas devine.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.champs: list[dict[str, str]] = []
        self.texte_libre: list[str] = []
        self._pile: list[str] = []
        self._cellules: list[str] = []
        self._courant: list[str] = []
        self._etiquette_dt: str | None = None
        self._champ_data: str | None = None
        self._ligne = 0

    # -- suivi de position -------------------------------------------------
    def _chemin(self, suffixe: str) -> str:
        return "/".join(self._pile[-3:]) + "#" + suffixe

    def handle_starttag(self, tag, attrs):
        self._pile.append(tag)
        attributs = dict(attrs)
        if tag == "tr":
            self._cellules = []
            self._ligne += 1
        if tag in ("td", "th", "dt", "dd") or "data-field" in attributs:
            self._courant = []
        if "data-field" in attributs:
            self._champ_data = attributs["data-field"] or ""

    def handle_endtag(self, tag):
        texte = " ".join(" ".join(self._courant).split()).strip()
        if tag in ("td", "th"):
            self._cellules.append(texte)
            self._courant = []
        elif tag == "dt":
            self._etiquette_dt = texte
            self._courant = []
        elif tag == "dd":
            if self._etiquette_dt:
                self.champs.append({
                    "label": self._etiquette_dt,
                    "value": texte,
                    "source_path": "dl/dt+dd[%s]" % self._etiquette_dt,
                })
            self._etiquette_dt = None
            self._courant = []
        elif tag == "tr":
            # Une ligne de deux cellules est une paire etiquette/valeur.
            # Au-dela de deux, on conserve TOUTES les cellules : tronquer
                # serait perdre de l information d un document tiers.
            if len(self._cellules) >= 2:
                self.champs.append({
                    "label": self._cellules[0],
                    "value": self._cellules[1],
                    "source_path": "table/tr[%d]/td[1]" % self._ligne,
                })
                for index, extra in enumerate(self._cellules[2:], start=3):
                    self.champs.append({
                        "label": "%s (colonne %d)" % (self._cellules[0], index),
                        "value": extra,
                        "source_path": "table/tr[%d]/td[%d]" % (self._ligne, index),
                    })
            self._cellules = []
        if self._champ_data is not None and tag not in ("td", "th", "dt", "dd"):
            self.champs.append({
                "label": self._champ_data,
                "value": texte,
                "source_path": "[data-field=%s]" % self._champ_data,
            })
            self._champ_data = None
            self._courant = []
        if self._pile and self._pile[-1] == tag:
            self._pile.pop()

    def handle_data(self, data):
        propre = data.strip()
        if not propre:
            return
        self._courant.append(propre)
        self.texte_libre.append(propre)


def importer(octets: bytes, nom: str, recu_le: str) -> dict[str, object]:
    if len(octets) > PLAFOND:
        raise Illisible(
            "recu de %d octets, au-dela du plafond de %d : non lu"
            % (len(octets), PLAFOND)
        )
    # Un BOM UTF-8 est retire POUR L ANALYSE SEULEMENT. `octets` reste
    # intact : l empreinte doit rester celle du fichier tel qu il a ete
    # transmis. 15 des 22 fichiers du dossier reel du 30 octobre en
    # portent un, parce que PowerShell en met un.
    utiles = octets[3:] if octets[:3] == b"\xef\xbb\xbf" else octets
    texte = utiles.decode("utf-8", "replace")

    if nom.lower().endswith(".json"):
        try:
            charge = json.loads(texte)
        except json.JSONDecodeError as erreur:
            raise Illisible("recu JSON illisible : %s" % erreur) from erreur
        champs = [
            {"label": str(cle), "value": json.dumps(valeur, ensure_ascii=False)
             if not isinstance(valeur, str) else valeur,
             "source_path": "$.%s" % cle}
            for cle, valeur in sorted(charge.items())
        ] if isinstance(charge, dict) else []
        texte_libre = [texte]
        forme = "json"
    else:
        extracteur = Extracteur()
        extracteur.feed(texte)
        extracteur.close()
        champs = extracteur.champs
        texte_libre = extracteur.texte_libre
        forme = "html"

    # Les empreintes : relevees PARTOUT, avec le contexte ou elles
    # apparaissent. On ne decide pas de ce qu elles engagent.
    empreintes = []
    vues = set()
    for champ in champs:
        for trouvee in MOTIF_SHA256.findall(champ["value"]):
            if trouvee not in vues:
                vues.add(trouvee)
                empreintes.append({
                    "sha256": trouvee,
                    "label": champ["label"],
                    "source_path": champ["source_path"],
                })
    for trouvee in MOTIF_SHA256.findall(" ".join(texte_libre)):
        if trouvee not in vues:
            vues.add(trouvee)
            empreintes.append({
                "sha256": trouvee,
                "label": None,
                "source_path": "texte libre",
            })

    recu = {
        "schema": SCHEMA,
        "source": {
            "name": nom,
            "form": forme,
            "sha256": hashlib.sha256(octets).hexdigest(),
            "size_bytes": len(octets),
            "received_at_declared": recu_le,
        },
        "fields": champs,
        "digests": empreintes,
        # Vide par construction : ce programme ne sait pas reconnaitre une
        # signature verifiable, et en declarer une serait pretendre.
        "signatures": [],
        "limits": [
            "Ce recu est une DECLARATION EXTERNE, pas une preuve primaire.",
            "Aucun champ n a ete interprete : les valeurs sont verbatim, et "
            "aucune correspondance avec un champ NeoMundi n est supposee.",
            "`received_at_declared` est declare par NOUS : c est la date de "
            "reception, pas une date attestee.",
            "Aucune signature n a ete reconnue ni verifiee. Ce recu ne doit "
            "jamais etre qualifie de << cryptographiquement signe >>.",
        ],
    }
    return recu


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Importe un recu de preuve externe, sans en interpreter le sens."
    )
    analyseur.add_argument("receipt", type=Path)
    analyseur.add_argument("--received-at", required=True,
                           metavar="2026-11-05T12:00:00Z",
                           help="date de RECEPTION, declaree par nous. Exigee "
                                "explicitement : l outil ne lit pas l horloge.")
    analyseur.add_argument("--out", type=Path, default=None)
    arguments = analyseur.parse_args()

    try:
        octets = arguments.receipt.read_bytes()
        recu = importer(octets, arguments.receipt.name, arguments.received_at)
    except (Illisible, OSError) as erreur:
        print("[FAIL      ] %s" % erreur)
        return 1

    sortie = json.dumps(recu, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        # LF explicite : un recu normalise entre dans une chaine de
        # reconciliation, et son empreinte ne doit pas dependre du systeme.
        arguments.out.write_bytes(sortie.encode("utf-8"))
        print("recu normalise : %s" % arguments.out)
    else:
        sys.stdout.write(sortie)

    print()
    print("source      : %s (%s, %d octets)"
          % (recu["source"]["name"], recu["source"]["form"],
             recu["source"]["size_bytes"]))
    print("empreinte   : %s" % recu["source"]["sha256"])
    print("champs      : %d candidats releves" % len(recu["fields"]))
    print("empreintes  : %d trouvees dans le document" % len(recu["digests"]))
    print("signatures  : 0 -- aucune n est reconnue par cet outil")
    print()
    print("AUCUNE correspondance n a ete supposee. Pour reconcilier, fournir une")
    print("table de correspondance EXPLICITE a `adapters/reconcile.py`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

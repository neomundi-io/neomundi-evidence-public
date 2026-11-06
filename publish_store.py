# -*- coding: utf-8 -*-
"""Audite un magasin de confiance, puis prepare sa publication. N EMET RIEN.

    python publish_store.py audit   magasin.json
    python publish_store.py payload magasin.json [--out charge.json]

CE QUE CE PROGRAMME EST, ET N EST PAS
-------------------------------------

C est la BARRIERE de C-5, pas un publicateur. Il ne contacte aucun reseau,
n ecrit sur aucun site et ne pousse rien. Il repond a une seule question :
**ce fichier peut-il etre publie tel quel ?** -- et il fabrique la charge
minimale que le second canal doit porter.

POURQUOI UN SECOND CANAL
------------------------

Un auditeur telecharge aujourd hui le paquet ET le magasin qui dit a quelle
cle se fier, depuis le MEME endroit. Qui controle cet endroit controle les
deux : un faussaire capable d ecrire dans le depot ajoute sa cle au magasin,
signe une archive reconstruite, et tous les controles passent.

**L attaque ne vise pas la cryptographie, elle vise la source unique.** Le
correctif bon marche et reel est de publier l EMPREINTE du magasin ailleurs :
l auditeur compare, et un hote seul ne peut plus mentir.

Le second canal ne porte donc **aucun materiel de cle** : une empreinte et un
numero de version, ce qui suffit a detecter un magasin substitue et n offre
rien qui puisse en tenir lieu.

CE QUE L AUDIT NE PEUT PAS FAIRE
--------------------------------

Il ne sait pas reconnaitre le nom d une personne physique. Il repere les
STRUCTURES ou un nom se glisse -- une identite `natural_person`, un champ hors
schema -- et rend NOT TESTED en nommant ce qu un humain doit relire. Un audit
qui pretendrait trancher cela rendrait un PASS que personne n a merite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import i18n
except ImportError:  # pragma: no cover - chemin de degradation
    class i18n:  # type: ignore[no-redef]
        FR = "fr"
        EN = "en"

        @staticmethod
        def traduire(texte: str, langue: str) -> str:
            return texte

        @staticmethod
        def traduire_format(format_fr: str, langue: str) -> str:
            return format_fr


SCHEMA_MAGASIN = "neomundi.evidence.trust-store/1"
PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"

#: Champs admis au registre des identites et a celui des cles. Tout champ
#: hors de ces listes est un vecteur de divulgation : le schema les refuse
#: (`additionalProperties: false`), mais un magasin edite a la main peut en
#: porter, et c est precisement le cas qu on audite.
CHAMPS_IDENTITE = {
    "identity_id", "legal_name", "kind", "jurisdiction",
    "registration_reference", "legal_capacity_to_attest",
    "valid_from_declared", "superseded_by", "notes",
}
CHAMPS_CLE = {
    "kid", "kty", "crv", "alg", "x", "status", "signer_identity",
    "key_custodian_identity", "valid_from_declared", "valid_until_declared",
    "superseded_by", "revocation", "notes",
}

#: Ce qui ne doit JAMAIS sortir. `d` est le scalaire prive d une cle JWK :
#: sa seule presence dans un fichier destine a la publication est une
#: divulgation irreversible.
MOTIFS_INTERDITS = [
    (r'"d"\s*:', "le scalaire PRIVE d une cle JWK (`d`)"),
    (r"BEGIN [A-Z ]*PRIVATE KEY", "un bloc de cle privee PEM"),
    (r"(?i)\b(?:api[_-]?key|secret|passphrase|password|token)\b\s*[\"':=]",
     "un secret nomme"),
    (r"(?i)[a-z]:\\\\?[Uu]sers\\\\?", "un chemin de machine Windows"),
    (r"/(?:home|Users)/[A-Za-z0-9._-]+", "un chemin de machine POSIX"),
    (r"(?i)\bsk-[A-Za-z0-9]{12,}", "une cle d API en clair"),
]

_LANGUE = [i18n.FR]


def dis(*morceaux: object) -> None:
    if not morceaux:
        print()
        return
    premier = morceaux[0]
    if isinstance(premier, str):
        pose = i18n.traduire_format(premier, _LANGUE[0])
        if pose == premier:
            pose = i18n.traduire(premier, _LANGUE[0])
        premier = pose
    print(premier, *morceaux[1:])


class Bilan:
    """Trois etats, jamais confondus. `NOT TESTED` n est pas un `PASS`."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []

    def dire(self, etat: str, intitule: str, detail: str) -> None:
        self.lignes.append((etat, intitule, detail))
        dis("[%-10s] %s - %s" % (etat, intitule, detail))

    def compte(self, etat: str) -> int:
        return sum(1 for e, _, _ in self.lignes if e == etat)

    def code(self) -> int:
        return 1 if self.compte(FAIL) else 0


def empreinte(chemin: Path) -> str:
    """L empreinte des OCTETS TRANSMIS, et jamais d une re-serialisation.

    Re-serialiser pour << normaliser >> rendrait une empreinte que l auditeur
    ne retrouverait pas sur le fichier qu il a telecharge.
    """
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def auditer(magasin: dict, octets: bytes, bilan: Bilan) -> None:
    texte = octets.decode("utf-8", errors="replace")

    # ---- 1. aucun materiel prive, aucun secret, aucun chemin de machine --
    trouves = [quoi for motif, quoi in MOTIFS_INTERDITS
               if re.search(motif, texte)]
    if trouves:
        bilan.dire(FAIL, "aucun materiel prive ni secret",
                   "PUBLICATION REFUSEE : ce fichier porte %s. Une "
                   "divulgation est irreversible." % ", puis ".join(trouves))
    else:
        bilan.dire(PASS, "aucun materiel prive ni secret",
                   "%d motif(s) interdit(s) recherche(s), aucun trouve"
                   % len(MOTIFS_INTERDITS))

    # ---- 2. le schema, et la version publiable ---------------------------
    if magasin.get("schema") != SCHEMA_MAGASIN:
        bilan.dire(FAIL, "schema du magasin",
                   "attendu %s, declare %r"
                   % (SCHEMA_MAGASIN, magasin.get("schema")))
    else:
        bilan.dire(PASS, "schema du magasin", SCHEMA_MAGASIN)

    version = magasin.get("store_version")
    if not isinstance(version, int) or version < 1:
        bilan.dire(FAIL, "store_version publiable",
                   "absente ou invalide (%r). C est le nombre que le second "
                   "canal porte : sans lui, un consommateur ne voit pas "
                   "qu il tient une version perimee." % version)
    else:
        bilan.dire(PASS, "store_version publiable", "version %d" % version)

    # ---- 3. un magasin de TEST ne se publie pas comme officiel -----------
    genre = magasin.get("store_kind", "production")
    if genre == "test":
        bilan.dire(FAIL, "nature du magasin",
                   "`store_kind: test`. Le publier sur le canal officiel "
                   "ferait passer pour une racine de confiance un magasin "
                   "dont les cles n accordent rien.")
    else:
        bilan.dire(PASS, "nature du magasin", "`store_kind: %s`" % genre)

    # ---- 4. aucun champ hors des listes admises --------------------------
    intrus: list[str] = []
    for identite in magasin.get("identities", []):
        intrus += ["identities[%s].%s" % (identite.get("identity_id"), c)
                   for c in identite if c not in CHAMPS_IDENTITE]
    for cle in magasin.get("keys", []):
        intrus += ["keys[%s].%s" % (cle.get("kid"), c)
                   for c in cle if c not in CHAMPS_CLE]
    if intrus:
        bilan.dire(FAIL, "aucun champ hors schema",
                   "champ(s) inattendu(s), vecteur de divulgation : %s"
                   % ", ".join(intrus))
    else:
        bilan.dire(PASS, "aucun champ hors schema",
                   "%d identite(s) et %d cle(s) conformes"
                   % (len(magasin.get("identities", [])),
                      len(magasin.get("keys", []))))

    # ---- 5. les personnes physiques : a RELIRE, jamais a trancher --------
    personnes = [i.get("identity_id") for i in magasin.get("identities", [])
                 if i.get("kind") == "natural_person"]
    if personnes:
        bilan.dire(NOT_TESTED, "noms de personnes physiques",
                   "identite(s) de genre `natural_person` : %s. Un nom de "
                   "personne n est pas a nous de le publier. A RELIRE par un "
                   "humain -- ce programme ne sait pas reconnaitre un nom."
                   % ", ".join(str(p) for p in personnes))
    else:
        bilan.dire(NOT_TESTED, "noms de personnes physiques",
                   "aucune identite `natural_person`. Ce n est pas la preuve "
                   "qu aucun nom ne figure ailleurs : ce programme ne sait "
                   "pas reconnaitre un nom, seulement les structures ou il "
                   "se glisse.")

    # ---- 6. la capacite juridique, telle que declaree -------------------
    for identite in magasin.get("identities", []):
        if identite.get("legal_capacity_to_attest") == "experimental":
            bilan.dire(NOT_TESTED, "capacite juridique publiee",
                       "%s se publie en `experimental` : entite nommee, "
                       "aucun pouvoir verifie. La page du second canal doit "
                       "le dire, et ne jamais presenter ces attestations "
                       "comme des certifications juridiques."
                       % identite.get("identity_id"))
            break


def audit(arguments: argparse.Namespace) -> int:
    octets = arguments.magasin.read_bytes()
    magasin = json.loads(octets)          # json.loads sur des OCTETS : un BOM
                                          # est detecte tout seul.
    bilan = Bilan()
    dis("magasin   : %s" % arguments.magasin)
    dis("empreinte : %s" % hashlib.sha256(octets).hexdigest())
    dis()
    auditer(magasin, octets, bilan)
    dis()
    dis("BILAN : %d PASS, %d FAIL, %d NOT TESTED"
        % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))
    if bilan.compte(FAIL):
        dis()
        dis("PUBLICATION REFUSEE. Aucun FAIL n est un avertissement ici : une")
        dis("publication est irreversible, et ce qui sort ne revient pas.")
    else:
        dis()
        dis("Aucun obstacle AUTOMATIQUE a la publication. Les NOT TESTED")
        dis("ci-dessus restent a relire par un humain : ce programme n a pas")
        dis("de verdict a rendre sur eux, et n en rend pas.")
    return bilan.code()


def payload(arguments: argparse.Namespace) -> int:
    """La charge du second canal. Une empreinte, une version, et rien d autre."""
    octets = arguments.magasin.read_bytes()
    magasin = json.loads(octets)
    bilan = Bilan()
    auditer(magasin, octets, bilan)
    if bilan.compte(FAIL):
        dis("[FAIL] audit en echec : aucune charge n est produite. Lancer")
        dis("       `audit` pour le detail.")
        return 1

    charge = {
        "schema": "neomundi.evidence.trust-store-digest/1",
        "store_id": magasin.get("store_id"),
        "store_version": magasin.get("store_version"),
        "store_kind": magasin.get("store_kind", "production"),
        "sha256": hashlib.sha256(octets).hexdigest(),
        "updated_at_declared": magasin.get("updated_at_declared"),
        "limits": [
            "Cette charge ne porte AUCUN materiel de cle : une empreinte et "
            "une version, rien de plus.",
            "Elle permet de detecter un magasin substitue. Elle n atteste ni "
            "le contenu du magasin, ni la capacite juridique des identites "
            "qui y figurent.",
            "La date est DECLAREE : aucune horloge de confiance n intervient.",
        ],
    }
    rendu = json.dumps(charge, ensure_ascii=False, indent=2) + "\n"
    if arguments.out:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_bytes(rendu.encode("utf-8"))
        dis("charge ecrite : %s" % arguments.out)
    else:
        sys.stdout.write(rendu)
    dis()
    dis("A publier sur le SECOND canal, et nulle part ailleurs. Ce programme")
    dis("ne publie rien : il n a aucun acces reseau.")
    dis("L auditeur confronte ensuite avec :")
    dis("  python verify_attestation.py <att.jws> --trust-store <magasin> \\")
    dis("         --store-digest %s" % charge["sha256"])
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Audite un magasin de confiance et prepare sa publication. "
                    "Ne publie rien.")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--lang", choices=("fr", "en"), default="fr",
                        help="langue de la PROSE. Ne change aucun verdict et "
                             "aucun code de sortie.")
    sous = analyseur.add_subparsers(dest="commande", required=True)

    a = sous.add_parser("audit", parents=[parent],
                        help="ce magasin peut-il etre publie tel quel ?")
    a.add_argument("magasin", type=Path)

    p = sous.add_parser("payload", parents=[parent],
                        help="la charge du second canal : empreinte et version")
    p.add_argument("magasin", type=Path)
    p.add_argument("--out", type=Path, default=None)

    arguments = analyseur.parse_args()
    _LANGUE[0] = getattr(arguments, "lang", i18n.FR) or i18n.FR
    return audit(arguments) if arguments.commande == "audit" else payload(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

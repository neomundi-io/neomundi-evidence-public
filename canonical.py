# -*- coding: utf-8 -*-
"""Profil de canonicalisation `neomundi-jcs-strings/1`.

UN SEUL module, partage par le signataire et le verificateur. Deux
implementations du meme profil seraient la classe de bug la plus pernicieuse
de ce dispositif : elles divergeraient sur un cas rare, et la signature
deviendrait invalide sans que rien n ait ete altere.

LE PROFIL
---------

1. UTF-8, sans BOM.
2. `json.dumps(objet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
3. Types de valeur permis : chaine, `null`, objet, tableau de valeurs
   permises. **LES NOMBRES ET LES BOOLEENS SONT INTERDITS.**
4. Toute cle d objet respecte `^[a-z0-9_]+$`.

POURQUOI CE PROFIL EST EQUIVALENT A RFC 8785 SUR SON DOMAINE
------------------------------------------------------------

RFC 8785 (JCS) est difficile sur trois points. Le profil en neutralise deux
et herite du troisieme :

**Les nombres.** JCS impose l ecriture ECMAScript : `1.0` s ecrit `1`,
`1e-7` s ecrit `1e-7` la ou Python ecrit `1e-07`. C est la partie la plus
delicate de la norme, et `src/station/ledger/canonical.py` lui consacre
environ 250 lignes. **En interdisant les nombres, la question disparait au
lieu d etre geree.** Un decompte voyage donc en chaine : `"30"`, pas `30`.

**L ordre des cles.** JCS trie sur les unites de code UTF-16 ; Python trie
sur les points de code. Les deux ordres diffferent des qu une cle contient un
caractere hors du plan multilingue de base. **En restreignant les cles a
`[a-z0-9_]`, les deux ordres coincident**, et `sort_keys=True` suffit.

**L echappement des chaines.** `json.dumps` est deja conforme a JCS sur ce
point ; rien a faire.

HORS de ce domaine restreint, l equivalence NE TIENT PAS. C est precisement
pour cela que le domaine est restreint plutot que l implementation etendue :
un objet signe n a aucun besoin de nombres, et s en priver coute un
guillemet.

CE QUE LE PROFIL NE FAIT PAS
----------------------------

Il n intervient **jamais** dans la verification d une signature. Le
verificateur signe-verifie les octets portes verbatim par le JWS. Le profil
sert a deux choses seulement : produire ces octets cote signataire, et
**controler apres coup** qu ils ont bien ete produits selon le profil -- ce
qui est un controle distinct, et dont l echec n est pas un echec de
signature.

Bibliotheque standard seule.
"""

from __future__ import annotations

import json
import re

PROFIL = "neomundi-jcs-strings/1"

#: Une cle d objet admissible. Volontairement etroite : voir la docstring.
CLE_ADMISSIBLE = re.compile(r"^[a-z0-9_]+$")


class HorsDuProfil(ValueError):
    """La valeur ne peut pas etre canonisee selon `neomundi-jcs-strings/1`."""


def controle_domaine(valeur: object, chemin: str = "$") -> None:
    """Refuse tout ce que le profil n admet pas, en disant ou.

    Le refus est explicite plutot qu approximatif : une valeur qu on ne sait
    pas canoniser sans ambiguite ne doit jamais etre signee << au mieux >>.
    """
    if valeur is None or isinstance(valeur, str):
        return
    if isinstance(valeur, bool):
        # Avant `int` : en Python, `bool` est une sous-classe de `int`, et un
        # `isinstance(valeur, int)` attraperait `True` en le nommant entier.
        raise HorsDuProfil(
            "%s : booleen interdit par le profil (utiliser \"true\"/\"false\" si besoin)" % chemin
        )
    if isinstance(valeur, (int, float)):
        raise HorsDuProfil(
            "%s : nombre interdit par le profil -- le porter en chaine (%r)" % (chemin, valeur)
        )
    if isinstance(valeur, dict):
        for cle, sous in valeur.items():
            if not isinstance(cle, str):
                raise HorsDuProfil("%s : cle non textuelle %r" % (chemin, cle))
            if not CLE_ADMISSIBLE.match(cle):
                raise HorsDuProfil(
                    "%s.%s : cle hors de ^[a-z0-9_]+$ -- l ordre de tri JCS ne serait "
                    "plus garanti" % (chemin, cle)
                )
            controle_domaine(sous, "%s.%s" % (chemin, cle))
        return
    if isinstance(valeur, (list, tuple)):
        for index, sous in enumerate(valeur):
            controle_domaine(sous, "%s[%d]" % (chemin, index))
        return
    raise HorsDuProfil("%s : type %s non canonisable" % (chemin, type(valeur).__name__))


def canonise(valeur: object) -> bytes:
    """Les octets canoniques d une valeur, ou la raison du refus."""
    controle_domaine(valeur)
    return json.dumps(
        valeur, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def est_conforme(octets: bytes) -> tuple[bool, str]:
    """Ces octets ont-ils ete produits selon le profil ?

    Relit, recanonise, et compare. Rend (conforme, explication). Un ecart
    n est pas un echec de signature : c est un manquement au profil de
    production, et les deux doivent se lire separement.
    """
    try:
        valeur = json.loads(octets.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erreur:
        return False, "charge illisible : %s" % erreur
    try:
        rejoue = canonise(valeur)
    except HorsDuProfil as erreur:
        return False, str(erreur)
    if rejoue != octets:
        return False, (
            "les octets ne sont pas la forme canonique de leur propre contenu "
            "(%d octets portes, %d octets recanonises)" % (len(octets), len(rejoue))
        )
    return True, "forme canonique de %d octets" % len(octets)

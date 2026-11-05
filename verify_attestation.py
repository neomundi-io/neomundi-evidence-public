# -*- coding: utf-8 -*-
"""Verifie une attestation detachee, hors ligne, a partir d une cle publique.

    python verify_attestation.py A.zip.jws --archive A.zip --trust-store magasin.json
    python verify_attestation.py A.zip.jws --archive A.zip --trust-store m.json --json r.json

CE QUE CE PROGRAMME EST
-----------------------

Le VERIFICATEUR. Il ne connait que du materiel public, il n ecrit rien hors
du `--json` demande, et **il n importe jamais `sign.py`** : aucun chemin de
code ici ne peut atteindre une cle privee. C est verifiable statiquement, et
c est teste.

TROIS CHOSES SEPAREES, JAMAIS FUSIONNEES
----------------------------------------

    signature cryptographique   la cle `kid` a-t-elle signe CES octets ?
    identite de confiance       cette `kid` est-elle connue, active, et
                                rattachee a un signataire que nous acceptons ?
    concordance avec l archive  l empreinte attestee est-elle celle de
                                l archive que nous tenons ?

Une signature parfaitement valide d une cle non fiable ne doit JAMAIS se lire
comme une attestation. Le niveau `cryptographically_attested` n est derive
que si les trois sont `PASS`.

Deux lignes de plus rendent toujours `NOT TESTED`, et c est definitif :
la **capacite juridique** du signataire, qu aucun code ne peut etablir, et la
**verite du contenu**, qu une signature n atteste pas.

DEPENDANCE
----------

Ed25519 n est pas verifiable avec la bibliotheque standard. Si
`cryptography` est absent, ce programme rend `NOT TESTED` avec la raison --
jamais `PASS`, jamais `FAIL`. Les 21 controles d integrite de `verify.py`
restent, eux, entierement sans dependance.

Une voie entierement independante de nos outils est documentee : `openssl`
verifie la meme signature. Voir `docs/ATTESTATION.fr.md`.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import canonical

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"

SCHEMA_ATTESTATION = "neomundi.evidence.attestation/1"
SCHEMA_MAGASIN = "neomundi.evidence.trust-store/1"
POLITIQUE = "neomundi-evidence-policy/1"
ALG_IMPOSE = "EdDSA"

DECLARE, REFERENCE, ATTESTE = "declared", "reference_verifiable", "cryptographically_attested"

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519

    CRYPTO = True
except ImportError:  # pragma: no cover - teste par un environnement sans crypto
    CRYPTO = False


class Illisible(Exception):
    """Une entree n a pas la forme attendue. Rendue en FAIL, jamais en trace."""


def b64u(octets: bytes) -> str:
    return base64.urlsafe_b64encode(octets).rstrip(b"=").decode("ascii")


def deb64u(valeur: str) -> bytes:
    reste = len(valeur) % 4
    if reste == 1:
        raise Illisible("segment base64url de longueur impossible")
    try:
        return base64.urlsafe_b64decode(valeur + "=" * (-len(valeur) % 4))
    except Exception as erreur:  # noqa: BLE001 - toute erreur de decodage est la meme faute
        raise Illisible("base64url invalide : %s" % erreur) from erreur


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def objet_json(octets: bytes, quoi: str) -> dict:
    try:
        valeur = json.loads(octets)
    except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
        raise Illisible("%s n est pas du JSON lisible : %s" % (quoi, erreur)) from erreur
    if not isinstance(valeur, dict):
        raise Illisible("%s devrait etre un objet JSON ; recu %s"
                        % (quoi, type(valeur).__name__))
    return valeur


class Bilan:
    """Les lignes de controle. PASS, FAIL et NOT TESTED restent trois etats."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []

    def dire(self, etat: str, intitule: str, detail: str = "") -> None:
        self.lignes.append((etat, intitule, detail))
        print("[%-10s] %s%s" % (etat, intitule, " - " + detail if detail else ""))

    def compte(self, etat: str) -> int:
        return sum(1 for l in self.lignes if l[0] == etat)

    def a_echoue(self, intitule: str) -> bool:
        return any(e == FAIL and i == intitule for e, i, _ in self.lignes)

    def est_passe(self, intitule: str) -> bool:
        return any(e == PASS and i == intitule for e, i, _ in self.lignes)

    def code_de_sortie(self) -> int:
        return 1 if self.compte(FAIL) else 0


# --------------------------------------------------------------------------
# Le JWS
# --------------------------------------------------------------------------


def decoupe(jeton: str) -> tuple[str, str, str]:
    parties = jeton.strip().split(".")
    if len(parties) != 3 or not all(parties):
        raise Illisible(
            "un JWS compact a exactement trois segments non vides ; recu %d" % len(parties)
        )
    return parties[0], parties[1], parties[2]


# --------------------------------------------------------------------------
# Les controles
# --------------------------------------------------------------------------


INTITULE_SIGNATURE = "signature cryptographique"
INTITULE_CONFIANCE = "identite de confiance"
INTITULE_CONCORDANCE = "concordance avec l archive"
INTITULE_PROFIL = "profil de canonicalisation"
INTITULE_ENTETE = "en-tete : algorithme impose"


def controle_forme(bilan: Bilan, attestation: dict) -> bool:
    """La forme de l attestation, avant tout calcul cryptographique."""
    if attestation.get("schema") != SCHEMA_ATTESTATION:
        bilan.dire(FAIL, "schema d attestation reconnu",
                   "schema %r inconnu ; attendu %r"
                   % (attestation.get("schema"), SCHEMA_ATTESTATION))
        return False

    problemes = []
    for cle, type_attendu in (("canonicalization", str), ("attestation_id", str),
                              ("attestation_kind", str), ("subject_kind", str),
                              ("subject", dict), ("identities", dict),
                              ("attested_at_declared", str), ("key_id", str)):
        valeur = attestation.get(cle)
        if valeur is None:
            problemes.append("%s absent" % cle)
        elif not isinstance(valeur, type_attendu):
            problemes.append("%s : attendu %s, recu %s"
                             % (cle, type_attendu.__name__, type(valeur).__name__))

    if attestation.get("attestation_kind") not in ("contemporaneous", "retrospective"):
        problemes.append("attestation_kind %r hors du contrat"
                         % attestation.get("attestation_kind"))

    sujet = attestation.get("subject")
    if isinstance(sujet, dict):
        for cle in ("bundle_sha256", "bundle_name", "export_schema", "observation_count"):
            if not isinstance(sujet.get(cle), str):
                problemes.append("subject.%s absent ou non textuel" % cle)
        empreinte = sujet.get("bundle_sha256")
        if isinstance(empreinte, str) and (
            len(empreinte) != 64 or any(c not in "0123456789abcdef" for c in empreinte)
        ):
            problemes.append("subject.bundle_sha256 n est pas un SHA-256")
        compte = sujet.get("observation_count")
        if isinstance(compte, str) and not compte.isdigit():
            problemes.append("subject.observation_count doit etre un entier en chaine")

    identites = attestation.get("identities")
    if isinstance(identites, dict):
        for role in ("signer", "technical_operator", "measurement_author",
                     "key_custodian", "trust_authority"):
            if role not in identites:
                problemes.append("identities.%s absent" % role)
        for role in ("signer", "technical_operator", "measurement_author", "key_custodian"):
            if role in identites and not isinstance(identites[role], str):
                problemes.append("identities.%s doit etre un identity_id textuel" % role)

    if (
        attestation.get("attestation_kind") == "retrospective"
        and isinstance(sujet, dict)
        and not sujet.get("subject_frozen_at_declared")
    ):
        # Sans la date de gel conservee, une attestation retrospective ne peut
        # pas dire ce qu elle atteste.
        problemes.append(
            "attestation retrospective sans subject_frozen_at_declared : "
            "la date de gel du corpus doit etre conservee"
        )

    if problemes:
        bilan.dire(FAIL, "forme de l attestation", "; ".join(problemes[:5]))
        return False
    bilan.dire(PASS, "forme de l attestation",
               "%s, cle %s" % (attestation["attestation_kind"], attestation["key_id"]))
    return True


def controle_profil(bilan: Bilan, octets_charge: bytes) -> None:
    """La charge a-t-elle ete produite selon `neomundi-jcs-strings/1` ?

    Controle SEPARE de la signature : un ecart ici n invalide pas la
    signature, il dit que le producteur n a pas suivi son propre profil.
    """
    conforme, explication = canonical.est_conforme(octets_charge)
    bilan.dire(PASS if conforme else FAIL, INTITULE_PROFIL,
               "%s -- %s" % (canonical.PROFIL, explication))


def controle_entete(bilan: Bilan, entete: dict, key_id: str) -> None:
    """L algorithme est IMPOSE, jamais lu dans l en-tete pour choisir.

    C est la parade a la famille d attaques << algorithm confusion >> : un
    en-tete annoncant `none` ou `HS256` est refuse, et jamais honore.
    """
    problemes = []
    if entete.get("alg") != ALG_IMPOSE:
        problemes.append("alg %r refuse ; seul %r est accepte"
                         % (entete.get("alg"), ALG_IMPOSE))
    if entete.get("kid") != key_id:
        problemes.append("kid de l en-tete (%r) different de key_id de la charge (%r)"
                         % (entete.get("kid"), key_id))
    if problemes:
        bilan.dire(FAIL, INTITULE_ENTETE, "; ".join(problemes))
    else:
        bilan.dire(PASS, INTITULE_ENTETE, "%s, kid %s" % (ALG_IMPOSE, key_id))


def charge_magasin(chemin: Path) -> dict:
    magasin = objet_json(chemin.read_bytes(), "le magasin de confiance")
    if magasin.get("schema") != SCHEMA_MAGASIN:
        raise Illisible("magasin de schema %r inconnu ; attendu %r"
                        % (magasin.get("schema"), SCHEMA_MAGASIN))
    politique = magasin.get("verification_policy")
    if not isinstance(politique, dict) or politique.get("policy_id") != POLITIQUE:
        raise Illisible(
            "politique de verification %r inconnue ; attendu %r. Un magasin dont la "
            "politique n est pas comprise est refuse, pas interprete."
            % ((politique or {}).get("policy_id"), POLITIQUE)
        )
    cles = magasin.get("keys")
    if not isinstance(cles, list) or not cles:
        raise Illisible("magasin sans aucune cle")
    vus = set()
    for entree in cles:
        if not isinstance(entree, dict) or not isinstance(entree.get("kid"), str):
            raise Illisible("entree de cle malformee")
        if entree["kid"] in vus:
            raise Illisible("kid %r en double dans le magasin : un kid ne se reutilise pas"
                            % entree["kid"])
        vus.add(entree["kid"])
        if any(c in entree for c in ("d", "private", "private_key")):
            # Un magasin de confiance ne doit contenir que du public. Trouver
            # un champ de cle privee est une divulgation, pas une variante.
            raise Illisible(
                "le magasin contient un champ de cle PRIVEE pour %r : refus. "
                "Un magasin de confiance ne porte que du materiel public." % entree["kid"]
            )
    return magasin


def controle_signature(bilan: Bilan, entree_cle: dict, signe: bytes, signature: bytes) -> None:
    if not CRYPTO:
        bilan.dire(NOT_TESTED, INTITULE_SIGNATURE,
                   "`cryptography` est absent de cet environnement : Ed25519 n est pas "
                   "verifiable avec la bibliotheque standard. `pip install cryptography` "
                   "pour l eprouver. Aucun PASS n est accorde sans verification.")
        return
    if entree_cle.get("crv") != "Ed25519" or entree_cle.get("alg") != ALG_IMPOSE:
        bilan.dire(FAIL, INTITULE_SIGNATURE,
                   "la cle declare crv=%r alg=%r ; attendu Ed25519/EdDSA"
                   % (entree_cle.get("crv"), entree_cle.get("alg")))
        return
    try:
        brut = deb64u(str(entree_cle.get("x", "")))
    except Illisible as erreur:
        bilan.dire(FAIL, INTITULE_SIGNATURE, "cle publique illisible : %s" % erreur)
        return
    if len(brut) != 32:
        bilan.dire(FAIL, INTITULE_SIGNATURE,
                   "une cle publique Ed25519 fait 32 octets ; recu %d" % len(brut))
        return
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(brut).verify(signature, signe)
    except Exception as erreur:  # noqa: BLE001 - toute cause rend le meme verdict
        bilan.dire(FAIL, INTITULE_SIGNATURE,
                   "la cle %s n a pas signe ces octets (%s)"
                   % (entree_cle.get("kid"), type(erreur).__name__))
        return
    bilan.dire(PASS, INTITULE_SIGNATURE,
               "EdDSA/Ed25519, cle %s, %d octets signes"
               % (entree_cle.get("kid"), len(signe)))


def controle_confiance(bilan: Bilan, magasin: dict, entree_cle: dict,
                       attestation: dict, autoriser_test: bool) -> None:
    """La cle est-elle de confiance pour CETTE attestation ?

    Distincte de la validite mathematique : une signature juste d une cle
    compromise reste une signature juste, et n est pas une attestation.
    """
    statut = entree_cle.get("status")
    revocation = entree_cle.get("revocation") or {}
    emis = attestation.get("attested_at_declared", "")
    kid = entree_cle.get("kid")

    if statut == "test" and not autoriser_test:
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "cle %s de statut `test` : elle n accorde aucune attestation. "
                   "Relancer avec --allow-test-keys pour l accepter explicitement." % kid)
        return

    if statut == "compromised" or revocation.get("kind") == "compromised":
        # RETROACTIF, et c est la difference avec une rotation : qui detient
        # la cle privee peut forger n importe quel `attested_at_declared`,
        # donc faire survivre les signatures anterieures reviendrait a faire
        # confiance a un horodatage que l attaquant controle.
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "cle %s COMPROMISE le %s (%s) : toutes ses signatures sont non "
                   "fiables, quelle que soit leur date declaree."
                   % (kid, revocation.get("at_declared", "?"),
                      revocation.get("reason", "sans motif")))
        return

    if revocation.get("kind") == "rotated":
        limite = revocation.get("at_declared", "")
        if emis and limite and emis > limite:
            bilan.dire(FAIL, INTITULE_CONFIANCE,
                       "cle %s retiree par rotation le %s, attestation declaree le %s : "
                       "posterieure a la rotation." % (kid, limite, emis))
            return

    fin = entree_cle.get("valid_until_declared")
    if isinstance(fin, str) and emis and emis > fin:
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "cle %s expiree le %s, attestation declaree le %s" % (kid, fin, emis))
        return

    debut = entree_cle.get("valid_from_declared")
    if isinstance(debut, str) and emis and emis < debut:
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "attestation declaree le %s, anterieure a la validite de la cle %s (%s)"
                   % (emis, kid, debut))
        return

    identites = {i.get("identity_id"): i for i in magasin.get("identities", [])
                 if isinstance(i, dict)}
    signataire_cle = entree_cle.get("signer_identity")
    signataire_att = (attestation.get("identities") or {}).get("signer")
    if signataire_cle != signataire_att:
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "l attestation se dit signee par %r, le magasin rattache la cle %s a %r"
                   % (signataire_att, kid, signataire_cle))
        return
    if signataire_att not in identites:
        bilan.dire(FAIL, INTITULE_CONFIANCE,
                   "signataire %r inconnu du registre d identites du magasin" % signataire_att)
        return

    identite = identites[signataire_att]
    detail = "cle %s %s, signataire %s (%s)" % (
        kid, statut, signataire_att, identite.get("legal_name", "?"))
    if identite.get("superseded_by"):
        # Une succession est ADDITIVE : elle n invalide rien. L arrivee d une
        # societe commerciale apres une association doit laisser les
        # attestations anterieures intactes.
        detail += " ; identite remplacee depuis par %s, sans effet sur cette attestation" \
            % identite["superseded_by"]
    bilan.dire(PASS, INTITULE_CONFIANCE, detail)


def controle_capacite_juridique(bilan: Bilan, magasin: dict, attestation: dict) -> None:
    """TOUJOURS NOT TESTED. Aucun code n etablit une capacite juridique."""
    signataire = (attestation.get("identities") or {}).get("signer")
    identites = {i.get("identity_id"): i for i in magasin.get("identities", [])
                 if isinstance(i, dict)}
    identite = identites.get(signataire) or {}
    bilan.dire(
        NOT_TESTED, "capacite juridique du signataire",
        "declaree `%s` pour %s (%s). Aucun code ne peut etablir qu une entite peut "
        "legalement s engager : c est une question juridique, et elle reste ouverte."
        % (identite.get("legal_capacity_to_attest", "inconnue"), signataire,
           identite.get("legal_name", "?")),
    )


def controle_identites(bilan: Bilan, magasin: dict, attestation: dict) -> None:
    """Les cinq roles sont-ils distincts et resolus ?

    On ne REFUSE pas qu ils coincident -- en phase experimentale c est
    normal -- mais on le DIT, parce qu une attestation ou le signataire est
    aussi le detenteur de la cle et l auteur des mesures offre une separation
    des roles nominale et non reelle.
    """
    identites = attestation.get("identities") or {}
    connues = {i.get("identity_id") for i in magasin.get("identities", [])
               if isinstance(i, dict)}
    roles = ("signer", "technical_operator", "measurement_author", "key_custodian")
    inconnues = sorted({identites.get(r) for r in roles} - connues - {None})
    if inconnues:
        bilan.dire(NOT_TESTED, "separation des cinq identites",
                   "role(s) non resolu(s) dans le magasin : %s" % ", ".join(inconnues))
        return
    distinctes = {identites.get(r) for r in roles}
    autorite = identites.get("trust_authority")
    bilan.dire(
        PASS, "separation des cinq identites",
        "%d identite(s) distincte(s) sur 4 roles%s ; autorite de confiance tierce : %s"
        % (len(distinctes),
           " -- des roles coincident, la separation est nominale" if len(distinctes) < 4 else "",
           autorite or "aucune"),
    )


def controle_concordance(bilan: Bilan, attestation: dict, archive: Path | None) -> None:
    sujet = attestation["subject"]
    if archive is None:
        bilan.dire(NOT_TESTED, INTITULE_CONCORDANCE,
                   "archive non fournie. La fournir avec --archive pour confronter "
                   "l empreinte attestee a l archive reelle.")
        return
    if not archive.is_file():
        bilan.dire(FAIL, INTITULE_CONCORDANCE, "archive introuvable : %s" % archive)
        return

    observee = sha256_fichier(archive)
    if observee != sujet["bundle_sha256"]:
        bilan.dire(FAIL, INTITULE_CONCORDANCE,
                   "l attestation porte sur %s..., l archive fournie se hache sur %s..."
                   % (sujet["bundle_sha256"][:16], observee[:16]))
        return

    ecarts = []
    try:
        with zipfile.ZipFile(archive) as z:
            noms = z.namelist()
            if isinstance(sujet.get("manifest_sha256"), str):
                if "manifest.json" not in noms:
                    ecarts.append("manifest.json absent de l archive")
                else:
                    reel = hashlib.sha256(z.read("manifest.json")).hexdigest()
                    if reel != sujet["manifest_sha256"]:
                        ecarts.append("manifest_sha256 divergent")
            if isinstance(sujet.get("checksums_sha256"), str):
                if "checksums.sha256" not in noms:
                    ecarts.append("checksums.sha256 absent de l archive")
                else:
                    reel = hashlib.sha256(z.read("checksums.sha256")).hexdigest()
                    if reel != sujet["checksums_sha256"]:
                        ecarts.append("checksums_sha256 divergent")
    except (zipfile.BadZipFile, OSError) as erreur:
        bilan.dire(FAIL, INTITULE_CONCORDANCE, "archive illisible : %s" % erreur)
        return

    if ecarts:
        # Impossible en pratique si `bundle_sha256` concorde ; si cela arrive,
        # c est l attestation qui est incoherente, pas l archive.
        bilan.dire(FAIL, INTITULE_CONCORDANCE,
                   "empreinte du fichier conforme mais %s : attestation incoherente"
                   % "; ".join(ecarts))
        return

    bilan.dire(PASS, INTITULE_CONCORDANCE,
               "bundle_sha256 recalcule sur %d octets, et les empreintes de membres "
               "concordent" % archive.stat().st_size)


def controle_nature(bilan: Bilan, attestation: dict) -> None:
    """Ce que l attestation atteste, selon sa nature. Jamais l origine."""
    sujet = attestation["subject"]
    if attestation["attestation_kind"] == "retrospective":
        bilan.dire(
            PASS, "nature de l attestation",
            "RETROSPECTIVE : elle constate une verification faite le %s (declare), sur un "
            "corpus gele le %s (conserve depuis son propre manifeste). Elle ne pretend PAS "
            "que le corpus ait ete signe a la date de son execution."
            % (attestation["attested_at_declared"], sujet.get("subject_frozen_at_declared")),
        )
    else:
        bilan.dire(PASS, "nature de l attestation",
                   "CONTEMPORAINE : signee le %s (declare), lors de la production du dossier."
                   % attestation["attested_at_declared"])


def controle_horodatage(bilan: Bilan, attestation: dict) -> None:
    """TOUJOURS NOT TESTED. Une date declaree n est pas un horodatage."""
    bilan.dire(
        NOT_TESTED, "horodatage independant",
        "`attested_at_declared` vaut %s et reste une date DECLAREE par le signataire. "
        "Aucune horloge de confiance n intervient dans ce mecanisme, donc cette valeur "
        "ne doit jamais etre presentee comme un horodatage independant."
        % attestation["attested_at_declared"],
    )


def controle_ancrage(bilan: Bilan, attestation: dict, preuve: Path | None) -> None:
    """L ancrage tiers, et la seule chose qu on puisse en dire aujourd hui.

    Aucune verification OpenTimestamps n est implementee : le SENS d un
    ancrage reste donc hors de portee, et la ligne est `NOT TESTED`.

    Une chose etroite est toutefois verifiable : si un fichier de preuve est
    fourni, son empreinte doit etre celle que l attestation declare. Cela ne
    dit pas que la preuve est valide -- seulement qu elle est bien CELLE que
    le signataire a nommee. Un ancrage << present mais non concordant >> se
    fait ainsi prendre, sans qu on pretende pour autant valider l ancrage.
    """
    ancrage = attestation.get("external_anchor")
    if not ancrage:
        if preuve is not None:
            bilan.dire(FAIL, "concordance de la preuve d ancrage",
                       "une preuve d ancrage est fournie alors que l attestation n en "
                       "declare aucun : elle ne se rattache a rien.")
            return
        bilan.dire(NOT_TESTED, "ancrage tiers",
                   "aucun ancrage tiers declare, et aucun n est implemente ici. Tant qu il "
                   "n existe pas, la date de signature reste declaree.")
        return

    bilan.dire(
        NOT_TESTED, "ancrage tiers",
        "ancrage `%s` declare au statut `%s`, et AUCUNE verification d ancrage n est "
        "implementee dans ce depot. Un ancrage non verifie ne vaut pas mieux qu un champ "
        "texte, et n eleve aucun niveau." % (ancrage.get("kind"), ancrage.get("status")),
    )

    declaree = ancrage.get("proof_sha256")
    if preuve is None:
        if isinstance(declaree, str):
            bilan.dire(NOT_TESTED, "concordance de la preuve d ancrage",
                       "l attestation declare une preuve d empreinte %s... ; la fournir "
                       "avec --anchor-proof <fichier> pour confronter ses octets."
                       % declaree[:16])
        return
    if not isinstance(declaree, str):
        bilan.dire(FAIL, "concordance de la preuve d ancrage",
                   "une preuve est fournie, mais l attestation ne declare aucune "
                   "`proof_sha256` a laquelle la comparer.")
        return
    if not preuve.is_file():
        bilan.dire(FAIL, "concordance de la preuve d ancrage",
                   "preuve d ancrage introuvable : %s" % preuve)
        return
    observee = sha256_fichier(preuve)
    if observee != declaree:
        bilan.dire(FAIL, "concordance de la preuve d ancrage",
                   "l attestation declare %s..., le fichier fourni se hache sur %s... : "
                   "ce n est pas la preuve nommee." % (declaree[:16], observee[:16]))
        return
    bilan.dire(PASS, "concordance de la preuve d ancrage",
               "le fichier fourni est bien celui que l attestation nomme. Sa VALIDITE "
               "en tant qu ancrage reste non verifiee.")


def controle_verite(bilan: Bilan) -> None:
    bilan.dire(
        NOT_TESTED, "verite du contenu",
        "hors de portee d une signature. Une attestation parfaitement signee sur une "
        "archive fabriquee est cryptographiquement valide : signer etablit un engagement "
        "et une custody, pas un fait.",
    )


# --------------------------------------------------------------------------


def arguments_de_verification(
    attestation: Path,
    archive: Path | None = None,
    trust_store: Path | None = None,
    allow_test_keys: bool = False,
    anchor_proof: Path | None = None,
    json: Path | None = None,
) -> argparse.Namespace:
    """Le jeu d arguments complet de `verifier`, pour un appelant interne.

    Existe parce que `bind.py` reconstruisait ce jeu a la main : ajouter
    `--anchor-proof` ici cassait l autre en silence, par un AttributeError
    que seule la revue a vu. Une fabrique unique rend impossible qu un
    appelant oublie un champ -- un nouveau champ recoit son defaut ici, et
    tous les appelants en heritent.
    """
    return argparse.Namespace(
        attestation=attestation,
        archive=archive,
        trust_store=trust_store,
        allow_test_keys=allow_test_keys,
        anchor_proof=anchor_proof,
        json=json,
    )


def verifier(arguments: argparse.Namespace) -> tuple[Bilan, str | None, dict]:
    bilan = Bilan()
    contexte: dict[str, object] = {}

    print("Attestation : %s" % arguments.attestation)
    if not arguments.attestation.is_file():
        bilan.dire(FAIL, "attestation lisible", "%s introuvable" % arguments.attestation)
        return bilan, None, contexte
    print("empreinte   : %s" % sha256_fichier(arguments.attestation))
    print("magasin     : %s\n" % (arguments.trust_store or "aucun"))

    try:
        e, c, s = decoupe(arguments.attestation.read_text(encoding="ascii", errors="strict"))
        octets_entete, octets_charge, signature = deb64u(e), deb64u(c), deb64u(s)
        entete = objet_json(octets_entete, "l en-tete JWS")
        attestation = objet_json(octets_charge, "la charge de l attestation")
    except (Illisible, UnicodeDecodeError) as erreur:
        bilan.dire(FAIL, "attestation lisible", str(erreur))
        return bilan, None, contexte
    bilan.dire(PASS, "attestation lisible", "JWS compact, 3 segments")

    if not controle_forme(bilan, attestation):
        return bilan, None, contexte
    contexte["attestation"] = attestation

    controle_profil(bilan, octets_charge)
    controle_entete(bilan, entete, attestation["key_id"])

    if arguments.trust_store is None:
        bilan.dire(NOT_TESTED, INTITULE_SIGNATURE,
                   "aucun magasin de confiance fourni : la cle %s n est pas resoluble. "
                   "La fournir avec --trust-store <fichier>." % attestation["key_id"])
        bilan.dire(NOT_TESTED, INTITULE_CONFIANCE, "sans magasin, aucune confiance n est etablie")
    else:
        try:
            magasin = charge_magasin(arguments.trust_store)
        except (Illisible, OSError) as erreur:
            bilan.dire(FAIL, "magasin de confiance lisible", str(erreur))
            magasin = None
        if magasin is not None:
            contexte["magasin"] = magasin
            bilan.dire(PASS, "magasin de confiance lisible",
                       "%s, politique %s, %d cle(s), %d identite(s)"
                       % (magasin.get("store_id"), POLITIQUE,
                          len(magasin["keys"]), len(magasin.get("identities", []))))
            entrees = {k["kid"]: k for k in magasin["keys"]}
            entree = entrees.get(attestation["key_id"])
            if entree is None:
                # INCONNUE n est pas FAUSSE : la signature peut etre
                # parfaitement valide, nous ne pouvons pas le savoir.
                bilan.dire(NOT_TESTED, INTITULE_SIGNATURE,
                           "cle %s inconnue de ce magasin (%d cle(s) connue(s)). La "
                           "signature est peut-etre valide ; rien ici ne permet de le dire."
                           % (attestation["key_id"], len(entrees)))
                bilan.dire(NOT_TESTED, INTITULE_CONFIANCE,
                           "cle inconnue : aucune confiance n est etablie, et aucune n est niee")
            else:
                signe = (e + "." + c).encode("ascii")
                controle_signature(bilan, entree, signe, signature)
                controle_confiance(bilan, magasin, entree, attestation,
                                   arguments.allow_test_keys)
                controle_capacite_juridique(bilan, magasin, attestation)
                controle_identites(bilan, magasin, attestation)

    controle_concordance(bilan, attestation, arguments.archive)
    controle_nature(bilan, attestation)
    controle_horodatage(bilan, attestation)
    controle_ancrage(bilan, attestation, arguments.anchor_proof)
    controle_verite(bilan)

    niveau = niveau_derive(bilan)
    return bilan, niveau, contexte


def niveau_derive(bilan: Bilan) -> str | None:
    """`cryptographically_attested` seulement si les trois piliers sont PASS.

    Rend `None` quand un controle a echoue : il n y a alors aucun niveau a
    annoncer, et surtout pas un niveau degrade qui se lirait comme un succes
    partiel.
    """
    if bilan.compte(FAIL):
        return None
    piliers = (INTITULE_PROFIL, INTITULE_ENTETE, INTITULE_SIGNATURE,
               INTITULE_CONFIANCE, INTITULE_CONCORDANCE)
    return ATTESTE if all(bilan.est_passe(p) for p in piliers) else None


def rendre(bilan: Bilan, niveau: str | None, contexte: dict,
           arguments: argparse.Namespace) -> int:
    print("\nBILAN : %d PASS, %d FAIL, %d NOT TESTED"
          % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))

    if bilan.compte(FAIL):
        print("Cette attestation ne doit pas etre presentee comme verifiee.")
    elif niveau == ATTESTE:
        print("Niveau atteint : %s" % ATTESTE)
        print("Soit : une partie identifiee s est engagee sur l empreinte de cette")
        print("archive, et l archive que vous tenez est bien celle-la. Ce n est ni une")
        print("preuve que l execution a eu lieu, ni une preuve de la DATE : celle-ci")
        print("reste declaree faute d ancrage tiers.")
    else:
        print("Niveau atteint : AUCUN au-dela de l integrite.")
        print("Des piliers n ont pas pu etre eprouves -- voir les lignes NOT TESTED.")

    if arguments.json:
        attestation = contexte.get("attestation") or {}
        rapport = {
            "schema": "neomundi.evidence.attestation-report/1",
            "attestation": str(arguments.attestation),
            "archive": str(arguments.archive) if arguments.archive else None,
            "trust_store": str(arguments.trust_store) if arguments.trust_store else None,
            "controls": [{"state": e, "control": i, "detail": d} for e, i, d in bilan.lignes],
            "counts": {"pass": bilan.compte(PASS), "fail": bilan.compte(FAIL),
                       "not_tested": bilan.compte(NOT_TESTED)},
            "attained_level": niveau,
            "subject": attestation.get("subject"),
            "identities": attestation.get("identities"),
            "attestation_kind": attestation.get("attestation_kind"),
            "attested_at_declared": attestation.get("attested_at_declared"),
            "establishes": (
                "that an identified party committed to this archive digest, and that the "
                "archive supplied is that one"
                if niveau == ATTESTE else None
            ),
            "does_not_establish": [
                "that the execution took place",
                "when it took place: attested_at_declared is DECLARED, not an independent timestamp",
                "the legal capacity of the signer to attest",
                "the truth of the attested content",
            ],
        }
        arguments.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("\nrapport lisible par machine : %s" % arguments.json)

    return bilan.code_de_sortie()


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Verifie une attestation Evidence detachee, hors ligne."
    )
    analyseur.add_argument("attestation", type=Path, help="le fichier .jws a verifier")
    analyseur.add_argument("--archive", type=Path, default=None,
                           help="l archive attestee, pour confronter l empreinte")
    analyseur.add_argument("--trust-store", type=Path, default=None,
                           help="magasin de confiance (cles publiques et etats)")
    analyseur.add_argument("--anchor-proof", type=Path, default=None, metavar="FICHIER",
                           help="fichier de preuve d ancrage tiers, pour confronter son "
                                "empreinte a celle que l attestation declare. Sa validite "
                                "en tant qu ancrage n est PAS verifiee.")
    analyseur.add_argument("--allow-test-keys", action="store_true",
                           help="accepter explicitement une cle de statut `test`")
    analyseur.add_argument("--json", type=Path, default=None, metavar="FICHIER",
                           help="ecrire aussi un rapport lisible par machine")
    arguments = analyseur.parse_args()

    bilan, niveau, contexte = verifier(arguments)
    return rendre(bilan, niveau, contexte, arguments)


if __name__ == "__main__":
    sys.exit(main())

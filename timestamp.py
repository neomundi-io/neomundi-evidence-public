# -*- coding: utf-8 -*-
"""Horodatage independant par OpenTimestamps -- preuve `.ots` detachee.

    python timestamp.py stamp   <sujet> [--out P.ots] [--descriptor D.json]
    python timestamp.py inspect <P.ots>
    python timestamp.py verify  <P.ots> --subject <sujet> [--strict] [--json R.json]
    python timestamp.py upgrade <P.ots> --out <NOUVEAU.ots>

CE QUE CET OUTIL ETABLIT, ET CE QU IL DELEGUE
---------------------------------------------

Il etablit, **sans aucune dependance**, que la preuve `.ots` s engage sur
l empreinte du sujet qu on lui donne. C est la LIAISON, et c est la part que
nous pouvons demontrer nous-memes.

Il ne verifie PAS le temps. Valider une attestation Bitcoin demande un
en-tete de bloc, donc une source de confiance exterieure -- et nous n en
avons pas. Cette verification est DELEGUEE au client officiel
(`ots verify`), et la ligne correspondante reste `NOT TESTED` ici. Un outil
qui pretendrait verifier le temps sans en-tete de bloc mentirait.

PENDING N EST PAS UNE PREUVE DE TEMPS
-------------------------------------

Une attestation `PENDING` dit qu un calendrier public s est engage a inclure
l empreinte dans une prochaine transaction Bitcoin. **Elle n atteste aucune
date.** Seule une attestation `BITCOIN` -- obtenue plus tard, par `upgrade`,
apres confirmation de la chaine -- porte une revendication temporelle. Et
meme alors, la verifier demande le client officiel.

**Aucun horodatage qualifie eIDAS n est revendique, ni ici, ni ailleurs.**
OpenTimestamps n est pas un prestataire de services de confiance au sens du
reglement.

CE QUI QUITTE LE POSTE
----------------------

**Une empreinte de 32 octets, et rien d autre.** Jamais l archive, jamais le
manifeste, jamais une donnee de pilote. `stamp` et `upgrade` sont les seules
sous-commandes qui touchent le reseau ; `inspect` et `verify` n y touchent
jamais.

DEPENDANCES
-----------

La LIAISON se lit a offset fixe : magie de 31 octets, un octet de version,
un octet d operation de hachage, puis 32 octets d empreinte. Aucune
dependance.

La lecture des ATTESTATIONS demande `opentimestamps`. Absente, les lignes
correspondantes rendent `NOT TESTED` -- jamais `PASS`, jamais `FAIL`.
`stamp` et `upgrade`, eux, l exigent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PASS, FAIL, NOT_TESTED = "PASS", "FAIL", "NOT TESTED"

SCHEMA_DESCRIPTEUR = "neomundi.evidence.timestamp/1"

#: L en-tete d un fichier `.ots` detache, tel que le format le fixe.
MAGIE = bytes.fromhex("004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294")
VERSION_MAJEURE = 1
#: Tag de l operation de hachage du fichier. Seul SHA-256 est accepte ici :
#: c est celui que la Station emploie partout, et accepter les autres sans
#: les eprouver serait une capacite annoncee.
TAG_SHA256 = 0x08
LONGUEUR_SHA256 = 32

#: Les calendriers publics d OpenTimestamps. Aucun compte, aucun paiement.
CALENDRIERS = (
    "https://alice.btc.calendar.opentimestamps.org",
    "https://bob.btc.calendar.opentimestamps.org",
    "https://finney.calendar.eternitywall.com",
    "https://btc.calendar.catallaxy.com",
)

INTITULE_LISIBLE = "preuve .ots lisible"
INTITULE_LIAISON = "liaison a l empreinte du sujet"
INTITULE_CONFIRMEE = "attestation confirmee par la chaine"


class Illisible(Exception):
    """Une entree n a pas la forme attendue. Rendue en FAIL, jamais en trace."""


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def empreinte_engagee(octets: bytes) -> str:
    """L empreinte sur laquelle la preuve s engage, lue a offset fixe.

    C est le seul endroit du dispositif ou nous analysons le format `.ots`
    nous-memes, et il est deliberement minuscule : trois champs de longueur
    connue. Tout le reste de l arbre est laisse a la bibliotheque officielle,
    parce qu une seconde implementation d un format cryptographique est une
    dette, pas une independance.
    """
    if len(octets) < len(MAGIE) + 2 + LONGUEUR_SHA256:
        raise Illisible(
            "preuve trop courte : %d octets, il en faut au moins %d"
            % (len(octets), len(MAGIE) + 2 + LONGUEUR_SHA256)
        )
    if not octets.startswith(MAGIE):
        raise Illisible(
            "ce n est pas un fichier .ots detache : la magie attendue est absente"
        )
    position = len(MAGIE)
    version = octets[position]
    if version != VERSION_MAJEURE:
        raise Illisible(
            "version majeure %d non prise en charge ; attendu %d"
            % (version, VERSION_MAJEURE)
        )
    tag = octets[position + 1]
    if tag != TAG_SHA256:
        raise Illisible(
            "operation de hachage 0x%02x non prise en charge ; seul SHA-256 "
            "(0x%02x) est accepte" % (tag, TAG_SHA256)
        )
    return octets[position + 2: position + 2 + LONGUEUR_SHA256].hex()


# --------------------------------------------------------------------------
# La bibliotheque officielle, quand elle est la
# --------------------------------------------------------------------------


def charge_officielle():
    """Rend le module officiel, ou None. Jamais d exception."""
    try:
        from opentimestamps.core.serialize import BytesDeserializationContext
        from opentimestamps.core.timestamp import DetachedTimestampFile
        from opentimestamps.core.notary import (
            PendingAttestation,
            BitcoinBlockHeaderAttestation,
        )

        return {
            "deserialise": BytesDeserializationContext,
            "detache": DetachedTimestampFile,
            "pending": PendingAttestation,
            "bitcoin": BitcoinBlockHeaderAttestation,
        }
    except Exception:  # noqa: BLE001 - une dependance absente ou cassee se vaut
        return None


def lire_attestations(octets: bytes) -> list[dict[str, object]] | None:
    """Les attestations de la preuve, ou None si la bibliotheque manque."""
    officielle = charge_officielle()
    if officielle is None:
        return None
    relu = officielle["detache"].deserialize(officielle["deserialise"](octets))
    sortie: list[dict[str, object]] = []
    for _, attestation in relu.timestamp.all_attestations():
        if isinstance(attestation, officielle["pending"]):
            sortie.append({"kind": "pending", "uri": attestation.uri})
        elif isinstance(attestation, officielle["bitcoin"]):
            sortie.append({"kind": "bitcoin", "height": int(attestation.height)})
        else:
            sortie.append({"kind": "unknown",
                           "tag": getattr(attestation, "TAG", b"").hex()})
    return sortie


# --------------------------------------------------------------------------
# Le bilan
# --------------------------------------------------------------------------


class Bilan:
    """Les lignes de controle. PASS, FAIL et NOT TESTED restent trois etats."""

    def __init__(self) -> None:
        self.lignes: list[tuple[str, str, str]] = []
        #: Index des lignes dont le NOT TESTED est CONTINGENT.
        self.requis: list[int] = []

    def dire(self, etat: str, controle: str, detail: str = "",
             requis: bool = False) -> None:
        if requis:
            self.requis.append(len(self.lignes))
        self.lignes.append((etat, controle, detail))
        print("[%-10s] %s%s" % (etat, controle, " - " + detail if detail else ""))

    def compte(self, etat: str) -> int:
        return sum(1 for l in self.lignes if l[0] == etat)

    def requises_non_demontrees(self) -> list[str]:
        return [self.lignes[i][1] for i in self.requis if self.lignes[i][0] != PASS]

    def code_de_sortie(self, strict: bool = False) -> int:
        """0 sain, 1 au moins un FAIL, 2 garantie requise non demontree."""
        if self.compte(FAIL):
            return 1
        if strict and self.requises_non_demontrees():
            return 2
        return 0


# --------------------------------------------------------------------------
# stamp
# --------------------------------------------------------------------------


def stamp(arguments: argparse.Namespace) -> int:
    if not arguments.subject.is_file():
        raise SystemExit("[FAIL] sujet introuvable : %s" % arguments.subject)
    try:
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.op import OpSHA256
        from opentimestamps.core.serialize import BytesSerializationContext
        from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp
    except Exception as erreur:  # noqa: BLE001
        raise SystemExit(
            "[FAIL] `opentimestamps` est requis pour HORODATER : "
            "pip install opentimestamps\n"
            "       (le verificateur, lui, lit la liaison sans aucune dependance)\n"
            "       cause : %s: %s" % (type(erreur).__name__, erreur)
        ) from erreur

    with arguments.subject.open("rb") as f:
        brut = hashlib.sha256()
        for bloc in iter(lambda: f.read(1 << 20), b""):
            brut.update(bloc)
    empreinte = brut.digest()

    print("Sujet      : %s" % arguments.subject)
    print("Empreinte  : %s" % empreinte.hex())
    print()
    print("SEULE cette valeur de 32 octets est transmise. Ni l archive, ni le")
    print("manifeste, ni aucune donnee de pilote ne quitte ce poste.")
    print()

    timestamp = Timestamp(empreinte)
    repondus, muets = [], []
    for url in arguments.calendar or CALENDRIERS:
        try:
            timestamp.merge(RemoteCalendar(url).submit(empreinte, timeout=arguments.timeout))
            repondus.append(url)
            print("[%-10s] %s" % ("SOUMIS", url))
        except Exception as erreur:  # noqa: BLE001 - un calendrier muet n est pas fatal
            muets.append(url)
            print("[%-10s] %s -- %s" % ("MUET", url, type(erreur).__name__))

    if not repondus:
        raise SystemExit(
            "\n[FAIL] aucun calendrier n a repondu : aucune preuve n a ete ecrite."
        )

    contexte = BytesSerializationContext()
    DetachedTimestampFile(OpSHA256(), timestamp).serialize(contexte)
    preuve = contexte.getbytes()

    sortie = arguments.out or Path(str(arguments.subject) + ".ots")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_bytes(preuve)
    print("\npreuve ecrite : %s (%d octets)" % (sortie, len(preuve)))

    if arguments.descriptor:
        descripteur = {
            "schema": SCHEMA_DESCRIPTEUR,
            "subject_name": arguments.subject.name,
            "subject_sha256": empreinte.hex(),
            "subject_kind": arguments.subject_kind,
            "proof_name": sortie.name,
            "proof_sha256": hashlib.sha256(preuve).hexdigest(),
            "stamped_at_declared": arguments.stamped_at,
            "calendars_submitted": sorted(repondus),
            "calendars_silent": sorted(muets),
            "state_at_stamping": "pending",
            "limits": [
                "Une attestation `pending` n atteste AUCUNE date : elle dit qu un "
                "calendrier s est engage a inclure l empreinte dans une prochaine "
                "transaction Bitcoin.",
                "`stamped_at_declared` est declare par nous : ce n est pas "
                "l horodatage, c est la date a laquelle nous avons soumis.",
                "Aucun horodatage qualifie eIDAS n est revendique.",
                "La verification du temps demande le client officiel : "
                "`ots verify <preuve>`.",
            ],
        }
        # LF explicite : l empreinte du descripteur est citee dans la
        # documentation, et un auditeur la recalcule.
        arguments.descriptor.write_bytes(
            (json.dumps(descripteur, ensure_ascii=False, indent=2, sort_keys=True)
             + "\n").encode("utf-8")
        )
        print("descripteur   : %s" % arguments.descriptor)

    print()
    print("ETAT : PENDING sur %d calendrier(s). **Ce n est pas encore une preuve"
          % len(repondus))
    print("de temps.** Relancer `upgrade` dans quelques heures, une fois la")
    print("transaction confirmee par la chaine.")
    return 0


# --------------------------------------------------------------------------
# inspect
# --------------------------------------------------------------------------


def inspect(arguments: argparse.Namespace) -> int:
    octets = arguments.proof.read_bytes()
    print("Preuve    : %s (%d octets)" % (arguments.proof, len(octets)))
    print("empreinte : %s" % hashlib.sha256(octets).hexdigest())
    try:
        engagee = empreinte_engagee(octets)
    except Illisible as erreur:
        print("\n[FAIL] %s" % erreur)
        return 1
    print("\nempreinte engagee : %s" % engagee)
    print("  (lue a offset fixe, sans aucune dependance)")

    attestations = lire_attestations(octets)
    if attestations is None:
        print("\nattestations : NON LUES -- `opentimestamps` est absent.")
        print("  pip install opentimestamps pour les lire.")
        return 0
    pending = [a for a in attestations if a["kind"] == "pending"]
    bitcoin = [a for a in attestations if a["kind"] == "bitcoin"]
    print("\n%d attestation(s) :" % len(attestations))
    for a in attestations:
        if a["kind"] == "pending":
            print("  PENDING   %s" % a["uri"])
        elif a["kind"] == "bitcoin":
            print("  BITCOIN   bloc %d" % a["height"])
        else:
            print("  INCONNUE  tag %s" % a.get("tag"))
    print()
    if bitcoin:
        print("Au moins une attestation Bitcoin est presente. Le TEMPS qu elle")
        print("porte reste a verifier avec le client officiel :")
        print("  ots verify %s" % arguments.proof.name)
    else:
        print("Aucune attestation Bitcoin : %d PENDING seulement." % len(pending))
        print("**Ce n est pas une preuve de temps.** Relancer `upgrade` plus tard.")
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------


def verifier(arguments: argparse.Namespace) -> tuple[Bilan, dict]:
    bilan = Bilan()
    contexte: dict[str, object] = {}

    print("Preuve  : %s" % arguments.proof)
    if not arguments.proof.is_file():
        bilan.dire(FAIL, INTITULE_LISIBLE, "%s introuvable" % arguments.proof,
                   requis=True)
        return bilan, contexte
    octets = arguments.proof.read_bytes()
    print("empreinte de la preuve : %s" % hashlib.sha256(octets).hexdigest())
    print("sujet   : %s\n" % (arguments.subject or "non fourni"))

    try:
        engagee = empreinte_engagee(octets)
    except Illisible as erreur:
        bilan.dire(FAIL, INTITULE_LISIBLE, str(erreur), requis=True)
        return bilan, contexte
    bilan.dire(PASS, INTITULE_LISIBLE,
               "magie, version %d, SHA-256 ; %d octets" % (VERSION_MAJEURE, len(octets)),
               requis=True)
    contexte["committed_sha256"] = engagee

    # --- la liaison, c est ce que NOUS demontrons -------------------------
    if arguments.subject is None:
        bilan.dire(NOT_TESTED, INTITULE_LIAISON,
                   "sujet non fourni. Le fournir avec --subject <fichier> pour que "
                   "la liaison soit eprouvee.", requis=True)
    elif not arguments.subject.is_file():
        bilan.dire(FAIL, INTITULE_LIAISON, "sujet introuvable : %s" % arguments.subject,
                   requis=True)
    else:
        reelle = sha256_fichier(arguments.subject)
        contexte["subject_sha256"] = reelle
        if reelle != engagee:
            bilan.dire(FAIL, INTITULE_LIAISON,
                       "la preuve s engage sur %s..., le sujet se hache sur %s..."
                       % (engagee[:16], reelle[:16]), requis=True)
        else:
            bilan.dire(PASS, INTITULE_LIAISON,
                       "la preuve s engage exactement sur l empreinte du sujet",
                       requis=True)

    # --- le descripteur, s il y en a un -----------------------------------
    if arguments.descriptor is None:
        bilan.dire(NOT_TESTED, "descripteur de liaison",
                   "aucun descripteur fourni ; la liaison ci-dessus suffit a "
                   "etablir sur quoi la preuve porte.")
    else:
        try:
            d = json.loads(arguments.descriptor.read_bytes())
            if not isinstance(d, dict):
                raise Illisible("le descripteur devrait etre un objet JSON")
            if d.get("schema") != SCHEMA_DESCRIPTEUR:
                raise Illisible("schema %r inconnu ; attendu %r"
                                % (d.get("schema"), SCHEMA_DESCRIPTEUR))
            ecarts = []
            if d.get("subject_sha256") != engagee:
                ecarts.append("subject_sha256 du descripteur != empreinte engagee")
            observee = hashlib.sha256(octets).hexdigest()
            if d.get("proof_sha256") not in (None, observee):
                ecarts.append("proof_sha256 du descripteur != empreinte de la preuve")
            if ecarts:
                bilan.dire(FAIL, "descripteur de liaison", "; ".join(ecarts))
            else:
                bilan.dire(PASS, "descripteur de liaison",
                           "concordant ; soumis le %s (declare)"
                           % d.get("stamped_at_declared"))
            contexte["descriptor"] = d
        except (Illisible, json.JSONDecodeError, OSError) as erreur:
            bilan.dire(FAIL, "descripteur de liaison", str(erreur))

    # --- les attestations -------------------------------------------------
    attestations = None
    try:
        attestations = lire_attestations(octets)
    except Exception as erreur:  # noqa: BLE001 - une preuve malformee sort en FAIL
        bilan.dire(FAIL, "arbre des attestations",
                   "preuve illisible par la bibliotheque officielle : %s: %s"
                   % (type(erreur).__name__, erreur))

    if attestations is None and not bilan.compte(FAIL):
        bilan.dire(NOT_TESTED, "arbre des attestations",
                   "`opentimestamps` est absent de cet environnement : l arbre n est "
                   "pas lu. `pip install opentimestamps` pour l eprouver. La LIAISON "
                   "ci-dessus, elle, ne depend de rien.")
        bilan.dire(NOT_TESTED, INTITULE_CONFIRMEE,
                   "etat inconnu sans la bibliotheque", requis=True)
    elif attestations is not None:
        contexte["attestations"] = attestations
        pending = [a for a in attestations if a["kind"] == "pending"]
        bitcoin = [a for a in attestations if a["kind"] == "bitcoin"]
        inconnues = [a for a in attestations if a["kind"] == "unknown"]
        bilan.dire(PASS, "arbre des attestations",
                   "%d pending, %d bitcoin, %d inconnue(s)"
                   % (len(pending), len(bitcoin), len(inconnues)))
        if bitcoin:
            bilan.dire(PASS, INTITULE_CONFIRMEE,
                       "%d attestation(s) Bitcoin, bloc(s) %s"
                       % (len(bitcoin), ", ".join(str(a["height"]) for a in bitcoin)),
                       requis=True)
        else:
            # PENDING n est PAS une preuve de temps, et c est tout l objet de
            # cette ligne : un consommateur qui lirait l arbre en PASS et
            # s arreterait la croirait la date etablie.
            bilan.dire(NOT_TESTED, INTITULE_CONFIRMEE,
                       "%d attestation(s) PENDING et AUCUNE Bitcoin. Un `pending` dit "
                       "qu un calendrier s est engage a inclure l empreinte dans une "
                       "transaction future : il n atteste aucune date. Relancer "
                       "`upgrade` apres confirmation." % len(pending),
                       requis=True)

    # --- ce que nous ne verifions pas, et ne verifierons pas --------------
    bilan.dire(NOT_TESTED, "temps verifie par un tiers",
               "hors de portee de cet outil : valider une attestation Bitcoin "
               "demande un en-tete de bloc, donc une source de confiance que nous "
               "n avons pas. A confronter avec le client officiel : "
               "`ots verify %s`" % arguments.proof.name)
    bilan.dire(NOT_TESTED, "qualification eIDAS",
               "AUCUNE. OpenTimestamps n est pas un prestataire de services de "
               "confiance qualifie au sens du reglement eIDAS, et rien ici ne doit "
               "etre presente comme un horodatage qualifie.")
    return bilan, contexte


def rendre(bilan: Bilan, contexte: dict, arguments: argparse.Namespace) -> int:
    print("\nBILAN : %d PASS, %d FAIL, %d NOT TESTED"
          % (bilan.compte(PASS), bilan.compte(FAIL), bilan.compte(NOT_TESTED)))

    attestations = contexte.get("attestations") or []
    confirmee = any(a["kind"] == "bitcoin" for a in attestations)
    if bilan.compte(FAIL):
        print("Cette preuve ne doit pas etre presentee comme verifiee.")
    elif confirmee:
        print("La preuve s engage sur le sujet, et porte une attestation Bitcoin.")
        print("Le TEMPS qu elle revendique reste a verifier avec `ots verify`.")
    else:
        print("La liaison est etablie. Le TEMPS ne l est PAS : la preuve est")
        print("PENDING, ce qui n atteste aucune date.")

    manquantes = bilan.requises_non_demontrees()
    if arguments.strict:
        if manquantes:
            print("\nMODE STRICT : %d garantie(s) requise(s) non demontree(s) :"
                  % len(manquantes))
            for m in manquantes:
                print("  - %s" % m)
            print("Aucun verdict n a change : seul le code de sortie en tient compte (2).")
        else:
            print("\nMODE STRICT : toutes les garanties requises sont demontrees.")

    if arguments.json:
        rapport = {
            "schema": "neomundi.evidence.timestamp-report/1",
            "proof": str(arguments.proof),
            "subject": str(arguments.subject) if arguments.subject else None,
            "controls": [{"state": e, "control": c, "detail": d}
                         for e, c, d in bilan.lignes],
            "counts": {"pass": bilan.compte(PASS), "fail": bilan.compte(FAIL),
                       "not_tested": bilan.compte(NOT_TESTED)},
            "strict": bool(arguments.strict),
            "required_not_demonstrated": manquantes,
            "exit_code": bilan.code_de_sortie(arguments.strict),
            "committed_sha256": contexte.get("committed_sha256"),
            "subject_sha256": contexte.get("subject_sha256"),
            "attestations": attestations,
            "state": "confirmed" if confirmee else ("pending" if attestations else "unknown"),
            "establishes": (
                "that the proof commits to this subject's digest"
                if not bilan.compte(FAIL) else None
            ),
            "does_not_establish": [
                "the time itself: verifying a Bitcoin attestation needs a block header",
                "any date at all while the state is pending",
                "an eIDAS qualified timestamp -- none is claimed",
            ],
        }
        arguments.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("\nrapport lisible par machine : %s" % arguments.json)

    return bilan.code_de_sortie(arguments.strict)


# --------------------------------------------------------------------------
# upgrade
# --------------------------------------------------------------------------


def sous_arbres(timestamp):
    """Parcourt un arbre de timestamp et rend chaque sous-arbre.

    Necessaire parce que `all_attestations()` ne rend que le MESSAGE et
    l attestation, alors que la mise a niveau doit fusionner la reponse du
    calendrier dans le sous-arbre QUI PORTE cette attestation.
    """
    yield timestamp
    for sous in timestamp.ops.values():
        yield from sous_arbres(sous)


def upgrade(arguments: argparse.Namespace) -> int:
    """Demande aux calendriers l attestation achevee, et ecrit une NOUVELLE preuve.

    Jamais en place : une preuve est une piece, et l ecraser detruirait
    l anterieure. L ancienne reste intacte, et les deux se verifient.
    """
    if arguments.out.exists() and not arguments.force:
        raise SystemExit(
            "[FAIL] %s existe deja. Choisir un autre nom, ou --force.\n"
            "       Une preuve ne s ecrase pas : l anterieure est une piece."
            % arguments.out
        )
    octets = arguments.proof.read_bytes()
    engagee = empreinte_engagee(octets)
    try:
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.serialize import (BytesDeserializationContext,
                                                   BytesSerializationContext)
        from opentimestamps.core.timestamp import DetachedTimestampFile
        from opentimestamps.core.notary import (PendingAttestation,
                                                BitcoinBlockHeaderAttestation)
    except Exception as erreur:  # noqa: BLE001
        raise SystemExit(
            "[FAIL] `opentimestamps` est requis pour mettre a niveau : "
            "pip install opentimestamps\n       cause : %s: %s"
            % (type(erreur).__name__, erreur)
        ) from erreur

    relu = DetachedTimestampFile.deserialize(BytesDeserializationContext(octets))
    print("Preuve      : %s" % arguments.proof)
    print("engagee sur : %s\n" % engagee)

    def confirmees(arbre) -> int:
        return sum(1 for _, a in arbre.all_attestations()
                   if isinstance(a, BitcoinBlockHeaderAttestation))

    avant = confirmees(relu.timestamp)
    progresse = 0
    for sous in list(sous_arbres(relu.timestamp)):
        en_attente = [a for a in sous.attestations
                      if isinstance(a, PendingAttestation)]
        for attestation in en_attente:
            url = attestation.uri
            try:
                achevee = RemoteCalendar(url).get_timestamp(
                    sous.msg, timeout=arguments.timeout
                )
            except Exception as erreur:  # noqa: BLE001 - pas encore confirmee
                print("[%-10s] %s -- %s" % ("EN ATTENTE", url, type(erreur).__name__))
                continue
            # La reponse porte le MEME message que ce sous-arbre : elle se
            # fusionne la, et nulle part ailleurs.
            sous.merge(achevee)
            progresse += 1
            print("[%-10s] %s" % ("ACHEVEE", url))

    apres = confirmees(relu.timestamp)
    contexte = BytesSerializationContext()
    relu.serialize(contexte)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_bytes(contexte.getbytes())

    print("\nnouvelle preuve : %s" % arguments.out)
    print("attestations Bitcoin : %d avant, %d apres" % (avant, apres))
    print("l ancienne preuve est INTACTE : %s" % arguments.proof)

    # Le descripteur de la NOUVELLE preuve. Sans lui elle n est pas
    # verifiable : `verify` compare `proof_sha256` a l empreinte du
    # fichier, et une preuve upgradee en a forcement une autre.
    if arguments.descriptor is not None:
        ancien = json.loads(arguments.descriptor.read_text(encoding="utf-8"))
        if ancien.get("subject_sha256") != engagee:
            raise SystemExit(
                "[FAIL] ce descripteur ne decrit pas cette preuve :\n"
                "       il annonce le sujet %s\n"
                "       la preuve engage     %s"
                % (ancien.get("subject_sha256"), engagee)
            )
        descripteur = dict(ancien)
        descripteur["proof_name"] = arguments.out.name
        descripteur["proof_sha256"] = sha256_fichier(arguments.out)
        # L anterieure n est jamais detruite : c est une piece a part.
        descripteur["upgraded_from"] = sha256_fichier(arguments.proof)
        # `state_at_stamping` dit l etat AU SCELLEMENT, et ne se reecrit
        # pas : l etat courant se lit dans les octets de la preuve, jamais
        # dans un descripteur. C est la regle de tout le produit.
        chemin_d = (arguments.descriptor_out if arguments.descriptor_out
                    else arguments.out.parent / (arguments.out.name + ".json"))
        chemin_d.write_bytes(
            (json.dumps(descripteur, ensure_ascii=False, indent=2,
                        sort_keys=True) + "\n").encode("utf-8")
        )
        print("descripteur     : %s" % chemin_d)
        print("  upgraded_from : %s" % descripteur["upgraded_from"])
    if apres == avant:
        print()
        print("Rien n a progresse : la transaction n est probablement pas encore")
        print("confirmee par la chaine. Reessayer plus tard. Tant qu aucune")
        print("attestation Bitcoin n apparait, **aucune date n est attestee.**")
    else:
        print()
        print("La preuve porte desormais une attestation Bitcoin. Le TEMPS qu elle")
        print("revendique reste a verifier avec le client officiel :")
        print("  ots verify %s" % arguments.out.name)
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Horodatage independant par OpenTimestamps, preuve detachee."
    )
    sous = analyseur.add_subparsers(dest="commande", required=True)

    s = sous.add_parser("stamp", help="horodater l empreinte d un sujet (RESEAU)")
    s.add_argument("subject", type=Path)
    s.add_argument("--out", type=Path, default=None)
    s.add_argument("--descriptor", type=Path, default=None)
    s.add_argument("--subject-kind", default="evidence_attestation",
                   choices=("evidence_attestation", "evidence_bundle", "other"))
    s.add_argument("--stamped-at", required=True, metavar="2026-11-05T22:00:00Z",
                   help="date de soumission DECLAREE. Exigee explicitement : l outil "
                        "ne lit pas l horloge, et cette date n est PAS l horodatage.")
    s.add_argument("--calendar", action="append", default=None,
                   help="calendrier a interroger ; defaut : les quatre publics")
    s.add_argument("--timeout", type=int, default=15)

    i = sous.add_parser("inspect", help="lire une preuve, hors ligne")
    i.add_argument("proof", type=Path)

    v = sous.add_parser("verify", help="verifier la liaison, hors ligne")
    v.add_argument("proof", type=Path)
    v.add_argument("--subject", type=Path, default=None,
                   help="le fichier horodate, pour eprouver la liaison")
    v.add_argument("--descriptor", type=Path, default=None)
    v.add_argument("--json", type=Path, default=None, metavar="FICHIER")
    v.add_argument("--strict", action="store_true",
                   help="sortir en code 2 si une garantie REQUISE n est pas demontree. "
                        "Ne change AUCUN verdict.")

    u = sous.add_parser("upgrade", help="demander l attestation achevee (RESEAU)")
    u.add_argument("proof", type=Path)
    u.add_argument("--out", type=Path, required=True)
    u.add_argument("--force", action="store_true",
                   help="ecraser la sortie si elle existe ; par defaut refuse")
    u.add_argument("--descriptor", type=Path, default=None,
                   help="le descripteur de la preuve d origine. Fourni, un descripteur de la NOUVELLE preuve est ecrit, portant `upgraded_from`.")
    u.add_argument("--descriptor-out", type=Path, default=None,
                   help="ou ecrire ce descripteur ; par defaut a cote de la nouvelle preuve")
    u.add_argument("--timeout", type=int, default=15)

    arguments = analyseur.parse_args()
    try:
        if arguments.commande == "stamp":
            return stamp(arguments)
        if arguments.commande == "inspect":
            return inspect(arguments)
        if arguments.commande == "upgrade":
            return upgrade(arguments)
        bilan, contexte = verifier(arguments)
        return rendre(bilan, contexte, arguments)
    except Illisible as erreur:
        print("[%-10s] %s" % (FAIL, erreur))
        return 1
    except OSError as erreur:
        print("[%-10s] %s" % (FAIL, erreur))
        return 1


if __name__ == "__main__":
    sys.exit(main())

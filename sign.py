# -*- coding: utf-8 -*-
"""Signe une attestation detachee sur un dossier de preuve Evidence.

    python sign.py genkey --kid <kid> --out <PRIVEE.json hors du depot> \\
                          --trust-store-out <magasin.json>
    python sign.py attest --archive A.zip --key <PRIVEE.json> \\
                          --attested-at 2026-11-05T12:00:00Z \\
                          --kind retrospective --out A.zip.jws

CE QUE CE PROGRAMME EST, ET N EST PAS
-------------------------------------

C est le SIGNATAIRE. Il detient une cle privee, il ecrit des fichiers, et il
ne tourne que sur le poste d un operateur -- jamais en integration continue :
signer n est pas une etape de construction.

Le VERIFICATEUR est un autre programme, `verify_attestation.py`, qui ne
connait que du materiel public et n ecrit rien. **Il n importe jamais ce
module**, et c est verifiable statiquement.

L attestation est DETACHEE, et ce n est pas un choix esthetique : elle porte
l empreinte du FICHIER d archive, donc la glisser dans l archive changerait
cette empreinte et invaliderait la signature qu on vient de calculer.
Circulaire. Un fichier a cote laisse l archive intacte a l octet -- ce qui
rend possible une attestation RETROSPECTIVE d un corpus gele, sans le
reouvrir.

CE QU UNE ATTESTATION ETABLIT
-----------------------------

Qu une partie identifiee s est engagee sur une empreinte precise. Elle
n etablit ni que le contenu est vrai, ni **quand** il a ete signe : aucune
horloge de confiance n intervient ici, et `attested_at_declared` reste une
DATE DECLAREE. Seul un ancrage tiers -- OpenTimestamps est le candidat, non
implemente -- rendrait une revendication de date independante.

Exige `cryptography`. Cles de TEST ephemeres uniquement a ce stade.
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

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError as erreur:  # pragma: no cover - environnement sans crypto
    print("[FAIL] `cryptography` est requis pour SIGNER : pip install cryptography")
    print("       (le verificateur, lui, s en passe et rend NOT TESTED)")
    raise SystemExit(2) from erreur

SCHEMA_ATTESTATION = "neomundi.evidence.attestation/1"
SCHEMA_MAGASIN = "neomundi.evidence.trust-store/1"
ALG = "EdDSA"

#: Racine du depot, pour la garde anti-divulgation ci-dessous.
DEPOT = Path(__file__).resolve().parent

LIMITES = [
    "Une signature etablit un engagement et une custody, pas la verite du contenu signe.",
    "`attested_at_declared` est declare par le signataire : ce n est pas un horodatage independant.",
    "Aucun ancrage tiers n est implemente ; le champ `external_anchor` ne peut pas elever le niveau.",
    "La capacite juridique du signataire n est pas verifiable par du code.",
]


def b64u(octets: bytes) -> str:
    return base64.urlsafe_b64encode(octets).rstrip(b"=").decode("ascii")


def deb64u(valeur: str) -> bytes:
    return base64.urlsafe_b64decode(valeur + "=" * (-len(valeur) % 4))


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def refuse_dans_le_depot(cible: Path, quoi: str) -> None:
    """Interdit d ecrire une cle privee sous la racine du depot.

    Garde dure, et non un avertissement : une cle privee commitee par
    inadvertance est une divulgation irreversible -- l historique Git la
    conserve meme apres suppression du fichier.
    """
    resolu = cible.resolve()
    if resolu == DEPOT or DEPOT in resolu.parents:
        raise SystemExit(
            "[FAIL] refus d ecrire %s sous la racine du depot (%s).\n"
            "       Une cle privee commitee reste dans l historique Git pour toujours.\n"
            "       Choisir un chemin hors du depot." % (quoi, DEPOT)
        )


# --------------------------------------------------------------------------
# genkey
# --------------------------------------------------------------------------


def genkey(arguments: argparse.Namespace) -> int:
    refuse_dans_le_depot(arguments.out, "une cle privee")

    privee = ed25519.Ed25519PrivateKey.generate()
    graine = privee.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    brut_public = privee.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(
        json.dumps({"kid": arguments.kid, "alg": ALG, "crv": "Ed25519", "d": b64u(graine)},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        arguments.out.chmod(0o600)
    except OSError:
        # Windows n honore pas toujours le mode POSIX ; ce n est pas une
        # raison d echouer, mais c est une raison de le dire.
        print("[note] mode 0600 non applique par ce systeme de fichiers")

    print("cle privee ecrite : %s" % arguments.out)
    print("  kid             : %s" % arguments.kid)
    print("  NE JAMAIS la commiter, ni la placer dans une archive ou un exemple.")

    if arguments.trust_store_out:
        magasin = {
            "schema": SCHEMA_MAGASIN,
            "store_id": arguments.store_id,
            "updated_at_declared": arguments.valid_from,
            "store_kind": arguments.store_kind,
            "verification_policy": {
                "policy_id": "neomundi-evidence-policy/1",
                "accepted_algorithms": [ALG],
                "accepted_curves": ["Ed25519"],
                "on_unknown_key": "not_tested",
                "on_rotated_key_within_window": "trusted",
                "on_rotated_key_after_window": "untrusted",
                "on_compromised_key": "untrusted_retroactively",
                "on_expired_key": "untrusted",
                "on_test_key": "untrusted_unless_allowed",
            },
            "identities": [
                {
                    "identity_id": arguments.signer,
                    "legal_name": arguments.signer_legal_name,
                    "kind": arguments.signer_kind,
                    "jurisdiction": arguments.signer_jurisdiction,
                    "registration_reference": None,
                    # Declare, jamais derive : aucun code ne peut etablir
                    # qu une entite peut legalement s engager.
                    "legal_capacity_to_attest": "unverified",
                    "valid_from_declared": arguments.valid_from,
                    "superseded_by": None,
                    "notes": "Capacite juridique a attester NON VERIFIEE a ce stade.",
                },
                {
                    "identity_id": arguments.custodian,
                    "legal_name": arguments.custodian,
                    "kind": "machine",
                    "jurisdiction": None,
                    "registration_reference": None,
                    "legal_capacity_to_attest": "not_applicable",
                    "valid_from_declared": arguments.valid_from,
                    "superseded_by": None,
                    "notes": "Detenteur technique de la cle, et operateur. "
                             "Ne s engage sur rien.",
                },
                {
                    # L auteur des mesures est un role A PART ENTIERE : sans
                    # lui au registre, la separation des cinq identites reste
                    # non resolue, et le verificateur le dit.
                    "identity_id": arguments.measurement_author,
                    "legal_name": arguments.measurement_author,
                    "kind": "machine",
                    "jurisdiction": None,
                    "registration_reference": None,
                    "legal_capacity_to_attest": "not_applicable",
                    "valid_from_declared": arguments.valid_from,
                    "superseded_by": None,
                    "notes": "Auteur des mesures du corpus atteste. "
                             "Distinct du signataire : mesurer n est pas s engager.",
                },
            ],
            "keys": [
                {
                    "kid": arguments.kid,
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "alg": ALG,
                    "x": b64u(brut_public),
                    "status": "test" if arguments.store_kind == "test" else "active",
                    "signer_identity": arguments.signer,
                    "key_custodian_identity": arguments.custodian,
                    "valid_from_declared": arguments.valid_from,
                    "valid_until_declared": None,
                    "superseded_by": None,
                    "revocation": None,
                    "notes": arguments.key_notes,
                }
            ],
            "changes": [
                {
                    "at_declared": arguments.valid_from,
                    "what": "creation du magasin et inscription de la cle %s" % arguments.kid,
                    "by_identity": arguments.custodian,
                }
            ],
            "limits": [
                "Ce magasin ne contient que du materiel public.",
                "Les dates y sont DECLAREES : aucune n est horodatee independamment.",
                "La capacite juridique des identites est declaree, jamais verifiee par du code.",
            ],
        }
        arguments.trust_store_out.parent.mkdir(parents=True, exist_ok=True)
        # LF explicite : voir la note sur `write_text` ci-dessus.
        arguments.trust_store_out.write_bytes(
            (json.dumps(magasin, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        print("magasin de confiance ecrit : %s" % arguments.trust_store_out)
        print("  cle publique (x)         : %s" % b64u(brut_public))
    return 0


# --------------------------------------------------------------------------
# attest
# --------------------------------------------------------------------------


def lire_sujet(archive: Path) -> dict[str, object]:
    """Les faits de l archive, lus dans l archive -- jamais saisis a la main."""
    with zipfile.ZipFile(archive) as z:
        noms = z.namelist()
        if "manifest.json" not in noms:
            raise SystemExit("[FAIL] l archive n a pas de manifest.json")
        octets_manifeste = z.read("manifest.json")
        manifeste = json.loads(octets_manifeste)
        observations = [
            l for l in z.read("observations.jsonl").splitlines() if l.strip()
        ] if "observations.jsonl" in noms else []
        sommes = z.read("checksums.sha256") if "checksums.sha256" in noms else None

    sujet: dict[str, object] = {
        "bundle_sha256": sha256_fichier(archive),
        "bundle_name": archive.name,
        "export_schema": str(manifeste.get("schema") or ""),
        # Le decompte voyage en CHAINE : voir le profil de canonicalisation.
        "observation_count": str(len(observations)),
    }
    sujet["manifest_sha256"] = hashlib.sha256(octets_manifeste).hexdigest()
    if sommes is not None:
        sujet["checksums_sha256"] = hashlib.sha256(sommes).hexdigest()
    # La date de gel est CONSERVEE depuis le manifeste du sujet, jamais
    # inventee. Les deux schemas d export la nomment differemment.
    gel = manifeste.get("exporte_le") or manifeste.get("construit_le")
    sujet["subject_frozen_at_declared"] = _instant(gel) if isinstance(gel, str) else None
    return sujet


def _instant(valeur: str) -> str | None:
    """Ramene un horodatage du manifeste a la seconde, en UTC, suffixe Z.

    Les manifestes portent des formes variees (`...722251+00:00`). La
    precision sous la seconde n apporte rien a une preuve et ferait diverger
    deux producteurs ; on la retire plutot que de la transporter.
    """
    texte = valeur.strip()
    if texte.endswith("Z"):
        texte = texte[:-1]
    elif "+" in texte[10:]:
        texte = texte[: texte.rindex("+")]
    if "." in texte:
        texte = texte[: texte.index(".")]
    return texte + "Z" if len(texte) == 19 and texte[10] == "T" else None


def attest(arguments: argparse.Namespace) -> int:
    if not arguments.archive.is_file():
        raise SystemExit("[FAIL] archive introuvable : %s" % arguments.archive)
    # Les OCTETS, pas le texte : `json.loads` detecte un BOM lui-meme,
    # et une cle ecrite par PowerShell en porte un.
    cle = json.loads(arguments.key.read_bytes())
    privee = ed25519.Ed25519PrivateKey.from_private_bytes(deb64u(cle["d"]))
    kid = cle["kid"]

    sujet = lire_sujet(arguments.archive)

    if arguments.kind == "retrospective" and not sujet.get("subject_frozen_at_declared"):
        # Une attestation retrospective SANS date de gel du sujet ne pourrait
        # pas dire ce qu elle atteste : on la refuse plutot que de laisser le
        # lecteur supposer.
        raise SystemExit(
            "[FAIL] attestation retrospective refusee : le manifeste du sujet ne porte "
            "aucune date de gel exploitable. Une attestation retrospective doit "
            "conserver la date de gel du corpus."
        )

    attestation = {
        "schema": SCHEMA_ATTESTATION,
        "canonicalization": canonical.PROFIL,
        "attestation_id": "att-" + sujet["bundle_sha256"][:32],
        "attestation_kind": arguments.kind,
        "subject_kind": "evidence_bundle",
        "subject": {**sujet, "subject_provenance_declared": arguments.provenance},
        "identities": {
            "signer": arguments.signer,
            "technical_operator": arguments.operator,
            "measurement_author": arguments.measurement_author,
            "key_custodian": arguments.custodian,
            "trust_authority": arguments.trust_authority,
        },
        "attested_at_declared": arguments.attested_at,
        "key_id": kid,
        "external_anchor": (
            {"kind": "opentimestamps", "status": "planned", "proof_sha256": None,
             "note": "Ancrage tiers prevu, NON implemente : ce champ n eleve aucun niveau."}
            if arguments.plan_anchor else None
        ),
        "limits": LIMITES,
    }

    # Le profil refuse tout ce qu il ne sait pas canoniser : mieux vaut un
    # echec ici qu une attestation signee qu un verificateur jugera non
    # conforme.
    charge = canonical.canonise(attestation)
    entete = canonical.canonise({"alg": ALG, "kid": kid, "typ": "JOSE"})

    signe = (b64u(entete) + "." + b64u(charge)).encode("ascii")
    jeton = b64u(entete) + "." + b64u(charge) + "." + b64u(privee.sign(signe))

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    # LF EXPLICITE, et jamais `write_text` : sous Windows il traduit `\n` en
    # `\r\n`, et le MEME dossier signe sur deux systemes n aurait pas la
    # meme empreinte. Or une preuve d horodatage s engage sur cette
    # empreinte -- le defaut a ete constate, pas suppose.
    arguments.out.write_bytes((jeton + "\n").encode("ascii"))

    print("attestation ecrite : %s" % arguments.out)
    print("  sujet            : %s" % sujet["bundle_name"])
    print("  bundle_sha256    : %s" % sujet["bundle_sha256"])
    print("  nature           : %s" % arguments.kind)
    print("  cle              : %s" % kid)
    print("  gel du sujet     : %s (conserve)" % sujet.get("subject_frozen_at_declared"))
    print()
    print("L archive n a pas ete touchee : l attestation est DETACHEE.")
    print("`attested_at_declared` est une date DECLAREE, pas un horodatage")
    print("independant. Verifier avec :")
    print("  python verify_attestation.py %s --archive %s --trust-store <magasin>"
          % (arguments.out, arguments.archive))
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Signe une attestation detachee sur un dossier de preuve Evidence."
    )
    sous = analyseur.add_subparsers(dest="commande", required=True)

    g = sous.add_parser("genkey", help="generer une cle de test et son magasin de confiance")
    g.add_argument("--kid", required=True, help="identifiant de cle, jamais reutilise")
    g.add_argument("--out", type=Path, required=True,
                   help="fichier de cle PRIVEE -- refuse sous la racine du depot")
    g.add_argument("--trust-store-out", type=Path, default=None,
                   help="magasin de confiance a ecrire (materiel public seulement)")
    g.add_argument("--store-id", default="neomundi-evidence-test")
    g.add_argument("--store-kind", choices=("production", "test"), default="test")
    g.add_argument("--signer", default="nm-recherche")
    g.add_argument("--signer-legal-name", default="NeoMundi Recherche")
    g.add_argument("--signer-kind", default="association",
                   choices=("association", "company", "organisation", "natural_person",
                            "machine", "unassigned"))
    g.add_argument("--signer-jurisdiction", default=None)
    g.add_argument("--custodian", default="nm-operator-poste")
    g.add_argument("--measurement-author", default="nm-station")
    g.add_argument("--valid-from", required=True, metavar="2026-11-05T00:00:00Z")
    g.add_argument("--key-notes", default="")

    a = sous.add_parser("attest", help="signer une attestation sur une archive")
    a.add_argument("--archive", type=Path, required=True)
    a.add_argument("--key", type=Path, required=True, help="la cle privee, hors du depot")
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--attested-at", required=True, metavar="2026-11-05T12:00:00Z",
                   help="date de signature DECLAREE. Exigee explicitement : l outil ne "
                        "lit pas l horloge, pour que deux executions rendent le meme jeton.")
    a.add_argument("--kind", choices=("contemporaneous", "retrospective"),
                   default="retrospective")
    a.add_argument("--signer", default="nm-recherche")
    a.add_argument("--operator", default="nm-operator-poste")
    a.add_argument("--measurement-author", default="nm-station")
    a.add_argument("--custodian", default="nm-operator-poste")
    a.add_argument("--trust-authority", default=None,
                   help="autorite de confiance tierce ; aucune aujourd hui")
    a.add_argument("--provenance", default=None)
    a.add_argument("--plan-anchor", action="store_true",
                   help="inscrire un ancrage tiers PREVU (n eleve aucun niveau)")

    arguments = analyseur.parse_args()
    if arguments.commande == "genkey":
        return genkey(arguments)
    return attest(arguments)


if __name__ == "__main__":
    sys.exit(main())

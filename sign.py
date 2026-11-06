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


# ---------------------------------------------------------------------------
# La langue de la PROSE. Optionnelle, et volontairement : sans `i18n.py` a
# cote, cet outil tourne et rend exactement les memes verdicts, en francais.
# Les controles ne doivent jamais dependre de la couche de traduction.
# ---------------------------------------------------------------------------
try:
    import i18n
except ImportError:  # pragma: no cover - chemin de degradation
    class i18n:  # type: ignore[no-redef]
        """Repli sans traduction. Rend tout tel quel."""

        FR = "fr"
        EN = "en"

        @staticmethod
        def traduire(texte: str, langue: str) -> str:
            return texte

        @staticmethod
        def traduire_format(format_fr: str, langue: str) -> str:
            return format_fr


#: La langue d affichage, posee une fois par `main`. Une cellule plutot
#: qu un parametre : il y a 19 appels a `dis` dans ce fichier, et les
#: renommer se relit, leur ajouter un argument non.
_LANGUE = [i18n.FR]


def dis(*morceaux: object) -> None:
    """Imprime de la prose, dans la langue courante.

    Seul le FORMAT est traduit. Les arguments -- empreintes, decomptes,
    noms de fichiers, etiquettes venues d un recu tiers -- traversent
    VERBATIM : les traduire les abimerait.
    """
    if not morceaux:
        print()
        return
    premier = morceaux[0]
    if isinstance(premier, str):
        # DEUX formes d appel coexistent dans ce depot :
        #   dis("x : %s", valeur)      -> `premier` est un FORMAT
        #   dis("x : %s" % valeur)     -> `premier` est DEJA rendu
        # La premiere se traduit par recherche exacte du format ; la
        # seconde par le moteur a motifs, qui en extrait les arguments.
        # Sans ce repli, toute la prose construite par `%` sortait en
        # francais -- et c est la forme majoritaire ici.
        pose = i18n.traduire_format(premier, _LANGUE[0])
        if pose == premier:
            pose = i18n.traduire(premier, _LANGUE[0])
        premier = pose
    print(premier, *morceaux[1:])


def _pose_langue(arguments: "argparse.Namespace") -> None:
    """Pose la langue depuis les arguments, si l outil en expose une."""
    _LANGUE[0] = getattr(arguments, "lang", i18n.FR) or i18n.FR

#: `--lang` est declare sur un analyseur PARENT, pour qu il s ecrive apres
#: la sous-commande -- `verify <fichier> --lang en` -- qui est la facon dont
#: on l ecrit naturellement.
def _parent_langue() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--lang",
        choices=("fr", "en"),
        default="fr",
        help="langue de la PROSE. Ne change aucun verdict, aucun code de "
             "sortie, aucun nom de champ et aucune empreinte.",
    )
    return parent

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError as erreur:  # pragma: no cover - environnement sans crypto
    dis("[FAIL] `cryptography` est requis pour SIGNER : pip install cryptography")
    dis("       (le verificateur, lui, s en passe et rend NOT TESTED)")
    raise SystemExit(2) from erreur

SCHEMA_ATTESTATION = "neomundi.evidence.attestation/1"
SCHEMA_MAGASIN = "neomundi.evidence.trust-store/1"
ALG = "EdDSA"

# La note consignee au registre doit dire ce que la valeur veut dire, et pas
# la repeter : un magasin se lit sans son schema a cote.
NOTE_PAR_CAPACITE = {
    "unverified": "Capacite juridique a attester NON VERIFIEE a ce stade.",
    "experimental":
        "Entite NOMMEE, ayant decide d attester dans un cadre scientifique et non "
        "commercial. AUCUNE verification de ses pouvoirs n a ete faite. Identite "
        "declaree, non juridiquement verifiee : les attestations emises sous ce "
        "statut ne sont pas des certifications juridiques.",
    "verified": "Pouvoirs verifies HORS de ce code ; ce champ n en est que la "
                "declaration.",
    "disputed": "Capacite CONTESTEE. Ne pas lire les attestations comme engageantes.",
}

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
        dis("[note] mode 0600 non applique par ce systeme de fichiers")

    dis("cle privee ecrite : %s" % arguments.out)
    dis("  kid             : %s" % arguments.kid)
    dis("  NE JAMAIS la commiter, ni la placer dans une archive ou un exemple.")

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
                    "registration_reference": arguments.signer_registration,
                    # Declare, jamais derive : aucun code ne peut etablir
                    # qu une entite peut legalement s engager.
                    "legal_capacity_to_attest": arguments.signer_capacity,
                    "valid_from_declared": arguments.valid_from,
                    "superseded_by": None,
                    "notes": NOTE_PAR_CAPACITE[arguments.signer_capacity],
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
            # Monotone, et EXIGE : c est le nombre publie sur le
            # second canal, a cote de l empreinte du magasin.
            "store_version": 1,
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
        if arguments.append:
            # Une rotation EXIGE que le successeur soit deja publie dans le
            # MEME magasin -- sinon `retire --kind rotated` refuse, et il a
            # raison. Sans ce chemin, la rotation serait impossible en
            # pratique : `genkey` ecrirait toujours un magasin neuf.
            if not arguments.trust_store_out.exists():
                dis("[FAIL] `--append` demande, mais %s n existe pas."
                    % arguments.trust_store_out)
                return 1
            existant = json.loads(arguments.trust_store_out.read_bytes())
            if existant.get("schema") != SCHEMA_MAGASIN:
                dis("[FAIL] %s n est pas un magasin %s"
                    % (arguments.trust_store_out, SCHEMA_MAGASIN))
                return 1
            if any(c.get("kid") == arguments.kid for c in existant.get("keys", [])):
                # La convention interdit de reutiliser un `kid`. Le relacher
                # ici rendrait deux cles distinctes indiscernables dans le
                # registre, et une compromission non circonscrivable.
                dis("[FAIL] `kid` %s DEJA present dans ce magasin. Un `kid` ne "
                    "se reutilise jamais." % arguments.kid)
                return 1
            existant["keys"].append(magasin["keys"][0])
            connues = {i.get("identity_id") for i in existant.get("identities", [])}
            for identite in magasin["identities"]:
                if identite["identity_id"] not in connues:
                    existant["identities"].append(identite)
            # Monotone, et c est le nombre publie sur le second canal : il
            # doit bouger a chaque changement, sinon un consommateur ne voit
            # pas qu il tient une version perimee.
            existant["store_version"] = int(existant.get("store_version", 1)) + 1
            existant["updated_at_declared"] = arguments.valid_from
            existant.setdefault("changes", []).append({
                "at_declared": arguments.valid_from,
                "what": "inscription de la cle %s" % arguments.kid,
                "by_identity": arguments.custodian,
            })
            magasin = existant

        arguments.trust_store_out.parent.mkdir(parents=True, exist_ok=True)
        # LF explicite : voir la note sur `write_text` ci-dessus.
        arguments.trust_store_out.write_bytes(
            (json.dumps(magasin, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        dis("magasin de confiance ecrit : %s" % arguments.trust_store_out)
        dis("  cle publique (x)         : %s" % b64u(brut_public))
        dis("  store_version            : %s" % magasin.get("store_version"))
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

    dis("attestation ecrite : %s" % arguments.out)
    dis("  sujet            : %s" % sujet["bundle_name"])
    dis("  bundle_sha256    : %s" % sujet["bundle_sha256"])
    dis("  nature           : %s" % arguments.kind)
    dis("  cle              : %s" % kid)
    dis("  gel du sujet     : %s (conserve)" % sujet.get("subject_frozen_at_declared"))
    dis()
    dis("L archive n a pas ete touchee : l attestation est DETACHEE.")
    dis("`attested_at_declared` est une date DECLAREE, pas un horodatage")
    dis("independant. Verifier avec :")
    dis("  python verify_attestation.py %s --archive %s --trust-store <magasin>"
          % (arguments.out, arguments.archive))

    if arguments.register:
        inscrire_au_registre(arguments.register, arguments.attested_at, kid,
                             str(sujet["bundle_sha256"]),
                             sha256_fichier(arguments.out), arguments.operator)
    else:
        dis()
        dis("[note] AUCUN registre tenu. Sans `--register <fichier>`, rien ne")
        dis("       consigne que cette cle a signe ce paquet -- et une")
        dis("       compromission ne pourra pas etre circonscrite : elle")
        dis("       invalidera TOUT ce que la cle a jamais signe.")
    return 0


# --------------------------------------------------------------------------
# Le registre des paquets signes, et le cycle de vie des cles.
#
# `SIGNING_POLICY.md` nommait ce registre manquant, et B-2 en fait un
# PREREQUIS de la premiere attestation reelle, pas un suivi. La raison est
# asymetrique : marquer une cle `compromised` invalide RETROACTIVEMENT tout
# ce qu elle a signe, quelle que soit la date declaree -- parce qu un voleur
# choisit la date qu il ecrit. Circonscrire est donc la seule chose qui
# limite les degats, et on ne circonscrit que ce qu on a consigne.
# --------------------------------------------------------------------------

ENTETE_REGISTRE = (
    "# Registre des paquets signes. HORS du depot public.\n"
    "# attested_at_declared  kid  bundle_sha256  attestation_sha256  role_operateur\n"
)


def inscrire_au_registre(chemin: Path, instant: str, kid: str, bundle: str,
                         attestation: str, operateur: str) -> None:
    """Ajoute une ligne. APPEND-ONLY : on ne reecrit jamais ce fichier."""
    refuse_dans_le_depot(chemin, "un registre de paquets signes")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    neuf = not chemin.exists()
    with chemin.open("a", encoding="utf-8", newline="\n") as f:
        if neuf:
            f.write(ENTETE_REGISTRE)
        f.write("%s  %s  %s  %s  %s\n"
                % (instant, kid, bundle, attestation, operateur))
    dis()
    dis("registre complete : %s" % chemin)


def lire_registre(chemin: Path) -> list[dict[str, str]]:
    lignes = []
    for brute in chemin.read_text(encoding="utf-8").splitlines():
        if not brute.strip() or brute.lstrip().startswith("#"):
            continue
        morceaux = brute.split()
        if len(morceaux) < 4:
            continue
        lignes.append({
            "attested_at_declared": morceaux[0], "kid": morceaux[1],
            "bundle_sha256": morceaux[2], "attestation_sha256": morceaux[3],
            "operateur": morceaux[4] if len(morceaux) > 4 else "?",
        })
    return lignes


def scope(arguments: argparse.Namespace) -> int:
    """Que faudrait-il reconsiderer si CETTE cle etait compromise ?"""
    lignes = lire_registre(arguments.register)
    vises = [l for l in lignes if l["kid"] == arguments.kid]
    dis("registre : %s -- %d attestation(s) consignee(s)"
        % (arguments.register, len(lignes)))
    dis("cle       : %s -- %d concernee(s)" % (arguments.kid, len(vises)))
    if not lignes:
        dis()
        dis("[FAIL] registre VIDE. Ce n est pas la preuve que la cle n a rien")
        dis("       signe : c est l absence de toute information. Une")
        dis("       compromission resterait non circonscrivable.")
        return 1
    if not vises:
        dis()
        dis("Aucune attestation consignee pour cette cle -- dans la limite de")
        dis("ce registre, et de rien d autre.")
        return 0
    dis()
    for l in vises:
        dis("  %s  bundle %s...  att %s..."
            % (l["attested_at_declared"], l["bundle_sha256"][:16],
               l["attestation_sha256"][:16]))
    dis()
    dis("Si cette cle etait marquee `compromised`, ces %d attestation(s)"
        % len(vises))
    dis("deviendraient NON FIABLES retroactivement, quelle que soit leur date")
    dis("declaree. Une rotation, elle, les laisserait de confiance.")
    return 0


def _charger_magasin(chemin: Path) -> dict:
    magasin = json.loads(chemin.read_bytes())
    if magasin.get("schema") != SCHEMA_MAGASIN:
        dis("[FAIL] %s n est pas un magasin %s" % (chemin, SCHEMA_MAGASIN))
        raise SystemExit(1)
    return magasin


def _ecrire_magasin(magasin: dict, sortie: Path) -> None:
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_bytes(
        (json.dumps(magasin, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def retirer_cle(arguments: argparse.Namespace) -> int:
    """Rotation ou compromission. L ORDRE est contraint, et c est le coeur.

    << Ne jamais revoquer a sec >> : generer le successeur, le publier dans
    le magasin, puis seulement marquer le predecesseur. Une revocation dont
    le remplacant n est pas publie laisse tout consommateur avec une cle a
    ne plus croire et aucune a croire -- et le verificateur rendant
    NOT TESTED sur une cle inconnue, la chaine perd un niveau en silence au
    lieu d echouer franchement.
    """
    magasin = _charger_magasin(arguments.trust_store)
    cles = {c.get("kid"): c for c in magasin.get("keys", []) if isinstance(c, dict)}

    if arguments.kid not in cles:
        dis("[FAIL] cle %s absente du magasin %s"
            % (arguments.kid, arguments.trust_store))
        return 1
    sortante = cles[arguments.kid]

    if sortante.get("status") == "compromised":
        dis("[FAIL] cle %s deja COMPROMISE. Une compromission ne se "
            "requalifie pas en rotation : elle est retroactive et definitive."
            % arguments.kid)
        return 1

    if arguments.kind == "rotated":
        successeur = arguments.successor
        if not successeur:
            dis("[FAIL] une rotation exige `--successor <kid>`. Retirer une cle")
            dis("       sans nommer celle qui la remplace est une revocation a sec.")
            return 1
        if successeur not in cles:
            dis("[FAIL] successeur %s ABSENT de ce magasin. Le generer et le "
                "publier d abord (genkey --append) : sinon tout consommateur "
                "se retrouve avec une cle a ne plus croire et aucune a croire."
                % successeur)
            return 1
        remplacante = cles[successeur]
        if remplacante.get("status") not in ("active", "test"):
            dis("[FAIL] successeur %s de statut `%s` : il ne peut pas prendre"
                % (successeur, remplacante.get("status")))
            dis("       la suite. Un remplacant doit etre utilisable.")
            return 1
        sortante["superseded_by"] = successeur
    elif arguments.successor:
        dis("[FAIL] `--successor` ne s applique pas a une compromission : une")
        dis("       cle compromise n est pas remplacee, elle est retiree, et")
        dis("       ses signatures anterieures tombent toutes.")
        return 1

    sortante["status"] = arguments.kind
    sortante["revocation"] = {
        "kind": arguments.kind,
        "at_declared": arguments.at,
        "reason": arguments.reason,
    }
    magasin["updated_at_declared"] = arguments.at
    _ecrire_magasin(magasin, arguments.out)

    dis("magasin ecrit : %s" % arguments.out)
    dis("  cle retiree : %s -> `%s` le %s"
        % (arguments.kid, arguments.kind, arguments.at))
    dis("  motif       : %s" % arguments.reason)
    if arguments.kind == "rotated":
        dis("  remplacee par : %s" % arguments.successor)
        dis()
        dis("Une ROTATION laisse les signatures anterieures DE CONFIANCE :")
        dis("une attestation declaree avant la rotation reste valide.")
    else:
        dis()
        dis("Une COMPROMISSION est RETROACTIVE : toutes les signatures de")
        dis("cette cle deviennent non fiables, quelle que soit leur date")
        dis("declaree -- parce qu un voleur choisit la date qu il ecrit.")
        if arguments.register and arguments.register.exists():
            vises = [l for l in lire_registre(arguments.register)
                     if l["kid"] == arguments.kid]
            dis("Portee consignee : %d attestation(s) concernee(s)." % len(vises))
        else:
            dis("[note] aucun registre fourni : la portee reste INCONNUE.")
    return 0


# --------------------------------------------------------------------------


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Signe une attestation detachee sur un dossier de preuve Evidence."
    )
    _PARENT = _parent_langue()
    sous = analyseur.add_subparsers(dest="commande", required=True)

    g = sous.add_parser("genkey", parents=[_PARENT], help="generer une cle de test et son magasin de confiance")
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
    g.add_argument("--signer-registration", default=None,
                   metavar="RNA W563015824",
                   help="reference publique d immatriculation, DECLAREE et jamais "
                        "confrontee a un registre par ce code")
    g.add_argument("--signer-capacity", default="unverified",
                   choices=("unverified", "experimental", "verified", "disputed"),
                   help="capacite juridique a attester, DECLAREE. `experimental` : "
                        "entite nommee, decision prise, cadre non commercial, "
                        "AUCUNE verification des pouvoirs. Jamais une certification "
                        "juridique")
    g.add_argument("--custodian", default="nm-operator-poste")
    g.add_argument("--measurement-author", default="nm-station")
    g.add_argument("--valid-from", required=True, metavar="2026-11-05T00:00:00Z")
    g.add_argument("--key-notes", default="")
    g.add_argument("--append", action="store_true",
                   help="ajouter la cle a un magasin EXISTANT au lieu d en "
                        "ecrire un neuf. Indispensable a une rotation : le "
                        "successeur doit etre publie dans le meme magasin")

    a = sous.add_parser("attest", parents=[_PARENT], help="signer une attestation sur une archive")
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
    a.add_argument("--register", type=Path, default=None,
                   help="registre des paquets signes, HORS du depot. Sans lui, "
                        "une compromission ne pourra pas etre circonscrite")

    r = sous.add_parser("retire", parents=[_PARENT],
                        help="retirer une cle : rotation ou compromission")
    r.add_argument("--trust-store", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True,
                   help="magasin resultant ; l original n est jamais reecrit")
    r.add_argument("--kid", required=True, help="la cle a retirer")
    r.add_argument("--kind", required=True, choices=("rotated", "compromised"),
                   help="`rotated` laisse les signatures anterieures de "
                        "confiance ; `compromised` les invalide TOUTES, "
                        "retroactivement")
    r.add_argument("--successor", default=None,
                   help="le `kid` qui prend la suite. EXIGE pour une rotation, "
                        "et deja publie dans ce magasin")
    r.add_argument("--at", required=True, metavar="2026-11-06T00:00:00Z",
                   help="date DECLAREE du retrait")
    r.add_argument("--reason", required=True, help="motif, en clair")
    r.add_argument("--register", type=Path, default=None,
                   help="pour circonscrire la portee d une compromission")

    s = sous.add_parser("scope", parents=[_PARENT],
                        help="ce qu une compromission de cette cle remettrait en cause")
    s.add_argument("--register", type=Path, required=True)
    s.add_argument("--kid", required=True)

    arguments = analyseur.parse_args()
    _pose_langue(arguments)
    if arguments.commande == "genkey":
        return genkey(arguments)
    if arguments.commande == "retire":
        return retirer_cle(arguments)
    if arguments.commande == "scope":
        return scope(arguments)
    return attest(arguments)


if __name__ == "__main__":
    sys.exit(main())

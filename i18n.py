# -*- coding: utf-8 -*-
"""Sortie bilingue FR/EN des verificateurs, sans toucher un seul verdict.

CE QUE CE MODULE NE TOUCHE JAMAIS
---------------------------------

Quatre choses sortent de son perimetre, par contrat :

  * les etats -- `PASS`, `FAIL`, `NOT TESTED` -- qui sont des termes du
    contrat, pas de la prose. Les traduire casserait tout consommateur ;
  * les codes de sortie -- 0, 1, 2 -- qui ne dependent d aucune langue ;
  * les noms de champs des rapports JSON, qui sont deja contractuels ;
  * les empreintes, identifiants, noms de fichiers et valeurs mesurees,
    qui traversent la traduction VERBATIM.

La langue ne change que la prose. C est la seule garantie qui compte ici,
et `tests/test_i18n.py` la verifie en comparant les deux sorties ligne par
ligne.

POURQUOI LA TRADUCTION SE FAIT A L EMISSION
-------------------------------------------

Les sites d appel ne sont PAS modifies. Ils construisent leur intitule et
leur detail en francais comme avant, et `Bilan.dire` traduit juste avant
d imprimer. Ce choix a une raison precise : convertir 52 sites d appel en
identifiants de catalogue aurait touche la logique de verification trois
jours avant une revue externe, pour un gain nul -- la prose serait la meme.
Ici, aucune ligne de logique ne bouge.

Le prix de ce choix : a l emission on ne voit que la chaine DEJA formatee,
plus son format. D ou les deux etages ci-dessous.

LES DEUX ETAGES
---------------

  1. EXACT -- la chaine entiere est dans le catalogue. Couvre les
     intitules fixes et les details litteraux.
  2. MOTIF -- la chaine a ete produite par un format connu. On derive du
     format francais une expression reguliere, on en extrait les
     arguments, et on les reinjecte dans le format anglais. Les arguments
     ainsi transportes sont les donnees -- empreintes, decomptes, noms --
     et ils ressortent inchanges.

Si aucun etage ne repond, la chaine francaise sort telle quelle. Ce n est
pas un echec silencieux : le cas 7 de `tests/test_i18n.py` exerce l outil
sur des archives reelles et ECHOUE si le moindre residu apparait. La
couverture est donc MESUREE, jamais affirmee.
"""
from __future__ import annotations

import re

FR = "fr"
EN = "en"
LANGUES = (FR, EN)

# --------------------------------------------------------------------------
# Les chaines ENTIERES. Clef : le francais tel qu un site d appel le produit.
# --------------------------------------------------------------------------

EXACT: dict[str, str] = {
    # ---- intitules de controle, verify.py -------------------------------
    "archive lisible": "archive readable",
    "aucun membre ne sort du repertoire cible":
        "no member escapes the target directory",
    "aucun secret ni chemin de machine dans l archive":
        "no secret and no machine path in the archive",
    "aucun signal null rendu comme zero": "no null signal rendered as zero",
    "aucune cellule CSV interpretable comme formule":
        "no CSV cell readable as a formula",
    "bundle_sha256 re-derive": "bundle_sha256 re-derived",
    "bundle_sha256 re-derive depuis les entrees":
        "bundle_sha256 re-derived from the inputs",
    "chainage JCS du registre d origine": "JCS chaining of the source ledger",
    "chaque membre est couvert par une empreinte":
        "every member is covered by a digest",
    "checksums.sha256 present": "checksums.sha256 present",
    "empreintes des entrees rejouees": "digests of the replayed inputs",
    "forme du manifeste": "manifest shape",
    "integrite interne du ZIP": "internal ZIP integrity",
    "le manifeste compte les observations livrees":
        "the manifest counts the delivered observations",
    "les absences declarees sont reelles": "the declared absences are real",
    "manifest.json lisible": "manifest.json readable",
    "manifest.json present": "manifest.json present",
    "origine et horodatage de l archive": "origin and timestamp of the archive",
    "schema d'export reconnu": "export schema recognised",
    "un regime hors ligne porte sa garde":
        "an offline regime carries its guard",

    # ---- intitules de REPLI, verify.py ----------------------------------
    # Ils ne sortent que si un controle leve une exception imprevue. Rares,
    # donc d autant plus importants : un auditeur anglophone qui tombe sur
    # un defaut de l outil ne doit pas lire la seule ligne francaise de sa
    # sortie.
    "absence de secrets et de chemins": "absence of secrets and paths",
    "absences declarees": "declared absences",
    "cardinalites": "cardinalities",
    "chainage du registre": "ledger chaining",
    "coherence des signaux nuls": "coherence of null signals",
    "empreintes des entrees": "digests of the inputs",
    "empreintes des membres": "digests of the members",
    "garde de regime": "regime guard",
    "neutralisation des formules CSV": "neutralisation of CSV formulas",
    "origine de l archive": "origin of the archive",

    # ---- details litteraux, verify.py -----------------------------------
    "aucun enregistrement de provenance": "no provenance record",
    "aucun enregistrement de provenance : corpus de regime live, ou membre absent":
        "no provenance record: a live-regime corpus, or an absent member",
    "aucun membre CSV dans cette archive": "no CSV member in this archive",
    "aucun membre de mesures dans cette archive":
        "no measurement member in this archive",
    "ce membre n est pas dans l archive. Le manifeste doit dire pourquoi.":
        "this member is not in the archive. The manifest must say why.",
    "hors de portee de toute verification locale : aucune signature tierce, "
    "aucun ancrage exterieur. `recorded_at` est declare par l appelant.":
        "out of reach of any local check: no third-party signature, no "
        "external anchor. `recorded_at` is declared by the caller.",
    "hors de portee, et l archive ne declare aucune empreinte de tete a confronter.":
        "out of reach, and the archive declares no head digest to compare against.",
    "le corpus d entree n est pas dans l archive. Le fournir avec "
    "--corpus <repertoire> pour que ce controle soit fait.":
        "the input corpus is not in the archive. Supply it with "
        "--corpus <directory> so that this check is performed.",
    "le corpus fourni n a pas de manifest.json":
        "the supplied corpus has no manifest.json",
    "le manifeste ne declare aucun regime d execution":
        "the manifest declares no execution regime",
    "le manifeste ne declare aucune rubrique d absences":
        "the manifest declares no absences section",
    "le rapport ne porte aucune section de regime":
        "the report carries no regime section",
    "aucun": "none",
    "membre absent": "member absent",
    "sans manifeste, rien n est verifiable":
        "without a manifest, nothing is verifiable",
    "un membre est corrompu": "a member is corrupt",

    # ====================================================================
    # verify_attestation.py
    # ====================================================================

    # ---- intitules de controle ------------------------------------------
    "ancrage tiers": "third-party anchor",
    "attestation lisible": "attestation readable",
    "capacite juridique du signataire": "legal capacity of the signer",
    "concordance de la preuve d ancrage": "agreement of the anchor proof",
    "forme de l attestation": "attestation shape",
    "horodatage independant": "independent timestamp",
    "magasin de confiance lisible": "trust store readable",
    "nature de l attestation": "nature of the attestation",
    "schema d attestation reconnu": "attestation schema recognised",
    "separation des cinq identites": "separation of the five identities",
    "verite du contenu": "truth of the content",

    # ---- details litteraux ----------------------------------------------
    "JWS compact, 3 segments": "compact JWS, 3 segments",
    "aucun ancrage tiers declare, et aucun n est implemente ici. Tant qu il "
    "n existe pas, la date de signature reste declaree.":
        "no third-party anchor declared, and none is implemented here. Until "
        "one exists, the signature date remains declared.",
    "hors de portee d une signature. Une attestation parfaitement signee sur "
    "une archive fabriquee est cryptographiquement valide : signer etablit un "
    "engagement et une custody, pas un fait.":
        "out of reach of a signature. A perfectly signed attestation over a "
        "fabricated archive is cryptographically valid: signing establishes a "
        "commitment and a custody, not a fact.",
    "le fichier fourni est bien celui que l attestation nomme. Sa VALIDITE en "
    "tant qu ancrage reste non verifiee.":
        "the supplied file is indeed the one the attestation names. Its "
        "VALIDITY as an anchor remains unverified.",
    "une preuve d ancrage est fournie alors que l attestation n en declare "
    "aucun : elle ne se rattache a rien.":
        "an anchor proof is supplied while the attestation declares none: it "
        "attaches to nothing.",
    "une preuve est fournie, mais l attestation ne declare aucune "
    "`proof_sha256` a laquelle la comparer.":
        "a proof is supplied, but the attestation declares no `proof_sha256` "
        "to compare it against.",

    # ---- prose d encadrement --------------------------------------------
    # ---- les cinq piliers, et leurs details litteraux -------------------
    "signature cryptographique": "cryptographic signature",
    "identite de confiance": "trusted identity",
    "concordance avec l archive": "agreement with the archive",
    "profil de canonicalisation": "canonicalisation profile",
    "en-tete : algorithme impose": "header: imposed algorithm",
    "`cryptography` est absent de cet environnement : Ed25519 n est pas "
    "verifiable avec la bibliotheque standard. `pip install cryptography` "
    "pour l eprouver. Aucun PASS n est accorde sans verification.":
        "`cryptography` is absent from this environment: Ed25519 is not "
        "verifiable with the standard library. `pip install cryptography` to "
        "exercise it. No PASS is granted without verification.",
    "archive non fournie. La fournir avec --archive pour confronter l "
    "empreinte attestee a l archive reelle.":
        "archive not supplied. Supply it with --archive to compare the "
        "attested digest against the real archive.",
    "cle inconnue : aucune confiance n est etablie, et aucune n est niee":
        "unknown key: no trust is established, and none is denied",
    "sans magasin, aucune confiance n est etablie":
        "without a store, no trust is established",
    "des roles coincident, la separation est nominale":
        "roles coincide; the separation is nominal",
    "aucune": "none",

    "Cette attestation ne doit pas etre presentee comme verifiee.":
        "This attestation must not be presented as verified.",
    "Des piliers n ont pas pu etre eprouves -- voir les lignes NOT TESTED.":
        "Some pillars could not be exercised -- see the NOT TESTED lines.",
    "Niveau atteint : AUCUN au-dela de l integrite.":
        "Level reached: NONE beyond integrity.",
    "Aucun verdict n a change : ces lignes restent telles qu affichees.":
        "No verdict changed: these lines stand exactly as shown.",
    "Seul le code de sortie en tient compte (2).":
        "Only the exit code accounts for it (2).",
    # Un paragraphe decoupe en quatre `print`. Les fragments anglais sont
    # decoupes pour se recoller dans le meme ordre.
    "Soit : une partie identifiee s est engagee sur l empreinte de cette":
        "That is: an identified party committed to the digest of this",
    "archive, et l archive que vous tenez est bien celle-la. Ce n est ni une":
        "archive, and the archive you hold is that one. It is neither a",
    "preuve que l execution a eu lieu, ni une preuve de la DATE : celle-ci":
        "proof that the execution took place, nor a proof of the DATE: that",
    "reste declaree faute d ancrage tiers.":
        "remains declared, for want of a third-party anchor.",

    # ---- prose d encadrement, verify.py ---------------------------------
    "Ce dossier ne doit pas etre presente comme verifie.":
        "This package must not be presented as verified.",
    "Aucun verdict n a change : seul le code de sortie en tient compte (2).":
        "No verdict changed: only the exit code accounts for it (2).",
    "MODE STRICT : toutes les garanties requises sont demontrees.":
        "STRICT MODE: every required guarantee is demonstrated.",
}

# --------------------------------------------------------------------------
# Les FORMATS. Clef : le format francais, tel qu il est ecrit dans le code.
# Les arguments traversent VERBATIM : empreintes, decomptes, noms de fichier.
# --------------------------------------------------------------------------

FORMATS: dict[str, str] = {
    # ---- intitules construits, verify.py --------------------------------
    "chainage JCS de %d registre(s) d origine":
        "JCS chaining of %d source ledger(s)",
    "membres attendus par le schema %s": "members expected by schema %s",
    "empreintes des %d membres declares": "digests of the %d declared members",
    "le manifeste compte les observations livrees (%d)":
        "the manifest counts the delivered observations (%d)",
    "aucun signal null declare mesure (%d null, %d values)":
        "no null signal declared measured (%d null, %d values)",
    "empreintes des entrees rejouees (%d a verifier)":
        "digests of the replayed inputs (%d to check)",
    "empreintes des entrees rejouees (%d conformes)":
        "digests of the replayed inputs (%d conformant)",
    "empreintes des entrees rejouees (%d/%d conformes)":
        "digests of the replayed inputs (%d/%d conformant)",
    "jointure de %s": "join of %s",
    "le manifeste compte les enregistrements de %s":
        "the manifest counts the records of %s",
    "le manifeste compte les enregistrements de %s (%d)":
        "the manifest counts the records of %s (%d)",
    "aucun orphelin dans %s": "no orphan in %s",

    # ---- details formates, verify.py ------------------------------------
    "%d sans observation livree : %s": "%d with no delivered observation: %s",
    "%s introuvable": "%s not found",
    "chemins abusifs : %s": "abusive paths: %s",
    "controle interrompu par un defaut de l outil : %s: %s":
        "check interrupted by a defect of the tool: %s: %s",
    "divergents %d, absents %d": "divergent %d, absent %d",
    "divergents : %s ; annonces et absents : %s":
        "divergent: %s; announced and absent: %s",
    "hors de portee : le recalculer ici serait une seconde implementation du "
    "registre. L archive declare %s et les empreintes de tete %s. A "
    "confronter avec : station ledger verify --path <registre>":
        "out of reach: recomputing it here would be a second implementation "
        "of the ledger. The archive declares %s and the head digests %s. To "
        "be compared with: station ledger verify --path <ledger>",
    "hors manifeste de sommes : %s": "outside the checksum manifest: %s",
    "manifeste %s, lignes %d": "manifest %s, lines %d",
    "manquants : %s": "missing: %s",
    "recalcule %s ; atteste %s": "recomputed %s; attested %s",
    "regimes : %s": "regimes: %s",
    "regimes %s sans aucune garde de lecture":
        "regimes %s with no reading guard at all",
    "schema %r inconnu de ce verificateur ; connus : %s":
        "schema %r unknown to this verifier; known: %s",

    # ---- messages d entree illisible, verify.py --------------------------
    # Ils portent le texte d une exception Python en dernier argument : ce
    # texte traverse VERBATIM, il est deja anglais et ce n est pas a nous
    # de le reecrire.
    "%s n est pas du JSON lisible : %s":
        "%s is not readable JSON: %s",
    "%s n est pas decodable en %s : %s":
        "%s is not decodable as %s: %s",
    "%s devrait etre un objet JSON ; recu %s":
        "%s should be a JSON object; got %s",
    "%s, ligne %d : JSON illisible (%s)":
        "%s, line %d: unreadable JSON (%s)",
    "%s, ligne %d : attendu un objet, recu %s":
        "%s, line %d: expected an object, got %s",

    # ====================================================================
    # verify_attestation.py
    # ====================================================================
    "%d identite(s) distincte(s) sur 4 roles%s ; autorite de confiance tierce : %s":
        "%d distinct identity(ies) across 4 roles%s; third-party trust "
        "authority: %s",
    "%s -- %s": "%s -- %s",
    "%s, cle %s": "%s, key %s",
    "%s, kid %s": "%s, kid %s",
    "%s, politique %s, %d cle(s), %d identite(s)":
        "%s, policy %s, %d key(s), %d identity(ies)",
    "CONTEMPORAINE : signee le %s (declare), lors de la production du dossier.":
        "CONTEMPORANEOUS: signed on %s (declared), at the time the package "
        "was produced.",
    "RETROSPECTIVE : elle constate une verification faite le %s (declare), "
    "sur un corpus gele le %s (conserve depuis son propre manifeste). Elle ne "
    "pretend PAS que le corpus ait ete signe a la date de son execution.":
        "RETROSPECTIVE: it records a verification performed on %s (declared), "
        "over a corpus frozen on %s (preserved from its own manifest). It "
        "does NOT claim the corpus was signed on the date of its execution.",
    "`attested_at_declared` vaut %s et reste une date DECLAREE par le "
    "signataire. Aucune horloge de confiance n intervient dans ce mecanisme, "
    "donc cette valeur ne doit jamais etre presentee comme un horodatage "
    "independant.":
        "`attested_at_declared` is %s and remains a date DECLARED by the "
        "signer. No trusted clock takes part in this mechanism, so this value "
        "must never be presented as an independent timestamp.",
    "ancrage `%s` declare au statut `%s`, et AUCUNE verification d ancrage n "
    "est implementee dans ce depot. Un ancrage non verifie ne vaut pas mieux "
    "qu un champ texte, et n eleve aucun niveau.":
        "anchor `%s` declared with status `%s`, and NO anchor verification is "
        "implemented in this repository. An unverified anchor is worth no "
        "more than a text field, and raises no level.",
    "declaree `%s` pour %s (%s). Aucun code ne peut etablir qu une entite "
    "peut legalement s engager : c est une question juridique, et elle reste "
    "ouverte.":
        "declared `%s` for %s (%s). No code can establish that an entity may "
        "legally commit: that is a legal question, and it remains open.",
    "l attestation declare %s..., le fichier fourni se hache sur %s... : ce n "
    "est pas la preuve nommee.":
        "the attestation declares %s..., the supplied file hashes to %s...: "
        "this is not the named proof.",
    "l attestation declare une preuve d empreinte %s... ; la fournir avec "
    "--anchor-proof <fichier> pour confronter ses octets.":
        "the attestation declares a proof with digest %s...; supply it with "
        "--anchor-proof <file> to compare its bytes.",
    "preuve d ancrage introuvable : %s": "anchor proof not found: %s",
    "role(s) non resolu(s) dans le magasin : %s":
        "role(s) unresolved in the store: %s",
    "schema %r inconnu ; attendu %r": "schema %r unknown; expected %r",
    # ---- les cinq piliers, details formates ------------------------------
    "EdDSA/Ed25519, cle %s, %d octets signes":
        "EdDSA/Ed25519, key %s, %d bytes signed",
    "archive illisible : %s": "archive unreadable: %s",
    "archive introuvable : %s": "archive not found: %s",
    "attestation declaree le %s, anterieure a la validite de la cle %s (%s)":
        "attestation declared on %s, earlier than the validity of key %s (%s)",
    "aucun magasin de confiance fourni : la cle %s n est pas resoluble. La "
    "fournir avec --trust-store <fichier>.":
        "no trust store supplied: key %s cannot be resolved. Supply one with "
        "--trust-store <file>.",
    "bundle_sha256 recalcule sur %d octets, et les empreintes de membres concordent":
        "bundle_sha256 recomputed over %d bytes, and the member digests agree",
    "cle %s COMPROMISE le %s (%s) : toutes ses signatures sont non fiables, "
    "quelle que soit leur date declaree.":
        "key %s COMPROMISED on %s (%s): every signature of its is untrusted, "
        "whatever date it declares.",
    "cle %s de statut `test` : elle n accorde aucune attestation. Relancer "
    "avec --allow-test-keys pour l accepter explicitement.":
        "key %s has status `test`: it grants no attestation. Re-run with "
        "--allow-test-keys to accept it explicitly.",
    "cle %s expiree le %s, attestation declaree le %s":
        "key %s expired on %s, attestation declared on %s",
    "cle %s inconnue de ce magasin (%d cle(s) connue(s)). La signature est "
    "peut-etre valide ; rien ici ne permet de le dire.":
        "key %s unknown to this store (%d known key(s)). The signature may be "
        "valid; nothing here allows one to say so.",
    "cle %s retiree par rotation le %s, attestation declaree le %s : "
    "posterieure a la rotation.":
        "key %s withdrawn by rotation on %s, attestation declared on %s: "
        "later than the rotation.",
    "cle publique illisible : %s": "public key unreadable: %s",
    "empreinte du fichier conforme mais %s : attestation incoherente":
        "file digest conformant but %s: inconsistent attestation",
    "l attestation porte sur %s..., l archive fournie se hache sur %s...":
        "the attestation is about %s..., the supplied archive hashes to %s...",
    "l attestation se dit signee par %r, le magasin rattache la cle %s a %r":
        "the attestation says it is signed by %r, the store attaches key %s to %r",
    "la cle %s n a pas signe ces octets (%s)":
        "key %s did not sign these bytes (%s)",
    "la cle declare crv=%r alg=%r ; attendu Ed25519/EdDSA":
        "the key declares crv=%r alg=%r; expected Ed25519/EdDSA",
    "signataire %r inconnu du registre d identites du magasin":
        "signer %r unknown to the store's identity registry",
    "une cle publique Ed25519 fait 32 octets ; recu %d":
        "an Ed25519 public key is 32 bytes; got %d",
    "un JWS compact a exactement trois segments non vides ; recu %d":
        "a compact JWS has exactly three non-empty segments; got %d",
    "%s -- forme canonique de %d octets":
        "%s -- canonical form of %d bytes",
    "%s, cle %s test, signataire %s (%s)":
        "%s, key %s test, signer %s (%s)",
    "cle %s %s, signataire %s (%s)":
        "key %s %s, signer %s (%s)",
    "contemporaine, cle %s": "contemporaneous, key %s",
    "retrospective, cle %s": "retrospective, key %s",

    "Attestation : %s": "Attestation: %s",
    "Niveau atteint : %s": "Level reached: %s",
    "empreinte   : %s": "digest      : %s",
    "magasin     : %s": "trust store : %s",

    # ---- prose d encadrement, verify.py ---------------------------------
    "Dossier de preuve : %s": "Evidence package: %s",
    "empreinte de l archive : %s": "archive digest: %s",
    "BILAN : %d PASS, %d FAIL, %d NOT TESTED":
        "SUMMARY: %d PASS, %d FAIL, %d NOT TESTED",
    "rapport lisible par machine : %s": "machine-readable report: %s",
    "MODE STRICT : %d garantie(s) requise(s) non demontree(s) :":
        "STRICT MODE: %d required guarantee(s) not demonstrated:",
}


# --------------------------------------------------------------------------


def _vers_motif(format_fr: str) -> tuple[re.Pattern[str], list[str]]:
    """Derive de `format_fr` une expression reguliere et l ordre de ses types.

    `%d` ne capture que des chiffres, pour qu un format a deux `%d` ne
    morde pas sur une chaine qui en contiendrait un. `%s` et `%r` sont
    gourmands au minimum, et le motif est ancre des deux cotes : sans
    ancrage, un format court matcherait l interieur d un format long et la
    traduction partirait sur le mauvais.
    """
    morceaux: list[str] = []
    types: list[str] = []
    index = 0
    while index < len(format_fr):
        caractere = format_fr[index]
        if caractere == "%" and index + 1 < len(format_fr):
            marque = format_fr[index + 1]
            if marque == "d":
                morceaux.append(r"(-?\d+)")
                types.append("d")
                index += 2
                continue
            if marque in ("s", "r"):
                morceaux.append(r"(.*?)")
                types.append(marque)
                index += 2
                continue
            if marque == "%":
                morceaux.append(re.escape("%"))
                index += 2
                continue
        morceaux.append(re.escape(caractere))
        index += 1
    return re.compile(r"\A" + "".join(morceaux) + r"\Z", re.S), types


def _construire_motifs() -> list[tuple[re.Pattern[str], list[str], str]]:
    """Construit les motifs une fois, du format le plus specifique au moins.

    L ordre est celui de la longueur du format FRANCAIS, decroissante : un
    format court est plus permissif, et s il passait d abord il mordrait sur
    une chaine produite par un format long. Trier sur la chaine anglaise --
    ce que faisait la premiere version -- n ordonne rien d utile.
    """
    construits = []
    for fr, en in FORMATS.items():
        motif, types = _vers_motif(fr)
        construits.append((len(fr), motif, types, en))
    construits.sort(key=lambda t: -t[0])
    return [(motif, types, en) for _, motif, types, en in construits]


_MOTIFS: list[tuple[re.Pattern[str], list[str], str]] = _construire_motifs()


def _argument_traduit(valeur: str, langue: str) -> str:
    """Traduit un argument TEXTUEL s il est de la prose connue.

    Le detail porte parfois sa prose dans un argument. On tente le
    catalogue sur la valeur, en tolerant un prefixe de ponctuation --
    << -- des roles coincident... >> arrive ainsi.

    Recursion bornee : on n appelle `traduire` que sur une valeur presente
    au catalogue EXACT, jamais sur un format, donc pas de boucle.
    """
    if not valeur:
        return valeur
    pose = EXACT.get(valeur)
    if pose is not None:
        return pose
    # Un prefixe de ponctuation et d espaces se conserve tel quel.
    depouille = valeur.lstrip(" -–—:;,")
    prefixe = valeur[: len(valeur) - len(depouille)]
    pose = EXACT.get(depouille)
    if pose is not None:
        return prefixe + pose
    return valeur


def _sans_repr(format_en: str) -> str:
    """Remplace chaque `%r` par `%s`, sans toucher a `%%`.

    Une valeur capturee depuis un `%r` francais porte deja ses guillemets.
    La repr-ifier une seconde fois rendrait `"\'inconnu\'"`.
    """
    sortie: list[str] = []
    index = 0
    while index < len(format_en):
        if format_en[index] == "%" and index + 1 < len(format_en):
            marque = format_en[index + 1]
            if marque == "r":
                sortie.append("%s")
                index += 2
                continue
            sortie.append(format_en[index:index + 2])
            index += 2
            continue
        sortie.append(format_en[index])
        index += 1
    return "".join(sortie)


def traduire(texte: str, langue: str) -> str:
    """Rend `texte` dans `langue`. Inconnu : rendu tel quel, jamais devine.

    Un texte non traduit sort en francais plutot que mutile. Le cas 7 de
    `tests/test_i18n.py` echoue si cela arrive sur une archive reelle, donc
    le repli n est pas une tolerance : c est un filet dont le test mesure
    qu il ne sert pas.
    """
    if langue == FR or not texte:
        return texte
    exact = EXACT.get(texte)
    if exact is not None:
        return exact
    for motif, types, en in _MOTIFS:
        trouve = motif.match(texte)
        if trouve is None:
            continue
        arguments = list(trouve.groups())
        # `%d` cote anglais attend un entier ; `%s` et `%r` recoivent la
        # capture TELLE QUELLE. Une valeur capturee n est jamais reformatee :
        # c est la regle qui protege les empreintes, les decomptes et les
        # noms de fichiers, et c est aussi elle qui evite de redoubler les
        # guillemets d une capture issue d un `%r`.
        prets: list[object] = []
        for valeur, marque in zip(arguments, types):
            if marque == "d":
                prets.append(int(valeur))
                continue
            # Un argument TEXTUEL peut lui-meme etre de la prose -- la ligne
            # des cinq identites en recoit deux. On le soumet au catalogue :
            # prose, il se traduit ; donnee, il n y est pas et ressort
            # inchange. Aucune liste d exceptions n est necessaire, puisque
            # le catalogue ne contient que de la prose.
            prets.append(_argument_traduit(valeur, langue))
        # Un `%r` cote anglais repr-ifierait une capture qui porte deja ses
        # guillemets. Il devient donc `%s`.
        en_pose = _sans_repr(en)
        try:
            return en_pose % tuple(prets)
        except (TypeError, ValueError):
            # Un format qui ne se reinjecte pas est un defaut de catalogue,
            # pas une raison de mutiler la sortie.
            return texte
    return texte


def traduire_format(format_fr: str, langue: str) -> str:
    """Rend un FORMAT dans `langue`, pret a recevoir ses arguments.

    A distinguer de `traduire`, qui recoit une chaine DEJA rendue et doit
    en extraire les arguments. Ici l appelant tient encore ses valeurs, donc
    un `%r` reste un `%r` : c est lui qui doit repr-ifier, pas nous.
    """
    if langue == FR:
        return format_fr
    pose = FORMATS.get(format_fr)
    if pose is not None:
        return pose
    # Une prose SANS argument vit dans `EXACT`, pas dans `FORMATS`. Sans ce
    # repli, le paragraphe final de `verify_attestation.py` sortait en
    # francais au milieu d une sortie anglaise.
    return EXACT.get(format_fr, format_fr)


def couvert(texte: str) -> bool:
    """`texte` est-il connu du catalogue, exactement ou par motif ?

    Une chaine couverte l est, que sa traduction DIFFERE ou non : certaines
    s ecrivent pareil dans les deux langues -- << manifest.json present >>,
    << checksums.sha256 present >>. Les compter comme non traduites etait le
    faux positif de la premiere version.
    """
    if texte in EXACT:
        return True
    return any(motif.match(texte) for motif, _, _ in _MOTIFS)


#: Marqueurs de prose FRANCAISE. Heuristique assumee : elle ne sert qu aux
#: tests, et son role est d attraper une regression du catalogue, pas de
#: juger une langue. Un message d exception Python -- << File is not a zip
#: file >> -- n en porte aucun, et c etait l autre faux positif.
_MARQUEURS_FR = (
    " aucun", " aucune", " est ", " sont ", " les ", " des ", " une ", " un ",
    " dans ", " pas ", " sans ", " que ", " qui ", " doit ", " avec ", " pour ",
    " sur ", " par ", " cette ", " ce ", " ne ", " de ", " du ", " au ", " aux ",
    "declare", "empreinte", "manifeste", "archive", "membre", "controle",
    "verifie", "aucune", "portee", "fournir", "corpus d entree",
)


def residu(texte: str, langue: str) -> bool:
    """`texte`, en francais, ressortirait-il NON traduit dans `langue` ?

    A nourrir avec le FRANCAIS. Le nourrir avec la sortie anglaise signale
    de l anglais deja traduit -- c etait le defaut du cas 7 a sa premiere
    ecriture.

    Rend `True` seulement si les deux tiennent : la chaine n est pas au
    catalogue, et elle porte des marqueurs de prose francaise. Une chaine
    faite de donnees -- empreinte, liste de fichiers, decompte -- n est
    jamais un residu : il n y a rien a y traduire.
    """
    if langue == FR or not texte.strip():
        return False
    if couvert(texte):
        return False
    sonde = " " + texte.lower() + " "
    return any(marque in sonde for marque in _MARQUEURS_FR)

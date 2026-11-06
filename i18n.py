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

DEUX QUESTIONS DIFFERENTES, ET C EST LE PIEGE
---------------------------------------------

`residu` demande << cette chaine est-elle TRADUISIBLE ? >>.
`devrait_changer` demande << le catalogue promet-il qu elle CHANGE ? >>.

La seconde est la bonne pour un controle par paire. Le 6 novembre,
`receipt_import.py` ne traduisait rien -- son `import i18n` echouait parce
que `sys.path[0]` vaut `adapters/` et non la racine -- et `residu` le
declarait conforme, puisque ses chaines etaient bien au catalogue. Un outil
entierement francais est ainsi passe pour traduit.
"""
from __future__ import annotations

import re as _re_module

FR = "fr"
EN = "en"
LANGUES = (FR, EN)

# --------------------------------------------------------------------------
# Les chaines ENTIERES. Clef : le francais tel qu un site d appel le produit.
# --------------------------------------------------------------------------

EXACT: dict[str, str] = {
    # ---- intitules de controle, verify.py -------------------------------
    # ---- R-1 + R-2 : le controle de completude ---------------------------
    "completude de l export": "completeness of the export",
    "l archive ne declare pas de contrat de completude : il lui manque "
    "`registre.enregistrements_exportes` et `registre.types_exclus`. Son "
    "integrite interne peut etre entiere et son export partiel -- une chaine "
    "valide ne dit rien de ce qui n a pas ete exporte. Non marque requis : "
    "c est au PRODUCTEUR de l archive de declarer ce contrat, pas a "
    "l appelant de le fournir.":
        "the archive declares no completeness contract: it lacks "
        "`registre.enregistrements_exportes` and `registre.types_exclus`. Its "
        "internal integrity may be whole and its export partial -- a valid "
        "chain says nothing about what was not exported. Not marked required: "
        "it is for the archive's PRODUCER to declare this contract, not for "
        "the caller to supply it.",
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

    # ---- reconcile.py : notes de statut et frontieres
    'absent des deux cotes':
        'absent on both sides',
    'chaines identiques':
        'identical strings',
    'chaines differentes. Les deux sont conservees ; rien n est tranche.':
        'different strings. Both are preserved; nothing is settled.',
    'aucune empreinte ni identifiant commun entre le recu et le corpus. Une proximite de date, de modele ou de valeur ne constitue pas une liaison.':
        'no digest and no identifier in common between the receipt and the corpus. A closeness of date, model or value does not constitute a binding.',
    'la table declare ce champ non comparable':
        'the table declares this field not comparable',
    'refusee':
        'refused',
    'empreinte':
        'digest',
    'identifiant':
        'identifier',
    'version de mesure':
        'measurement version',
    'couverture de mesure':
        'measurement coverage',
    'definition du score':
        'score definition',
    'Preuve primaire':
        'Primary evidence',
    'Declaration externe':
        'External declaration',
    'Conclusion verifiee':
        'Verified conclusion',
    'les empreintes de notre archive, que nous recalculons':
        'the digests of our archive, which we recompute',
    'tout champ du recu : valeur, statut, identifiant':
        'every field of the receipt: value, status, identifier',
    'toute signature annoncee et non verifiee':
        'every signature announced and not verified',
    'Un recu externe est une DECLARATION. Rien ici ne le transforme en preuve verifiee.':
        'An external receipt is a DECLARATION. Nothing here turns it into verified evidence.',
    'Aucune divergence n est tranchee : les deux valeurs sont conservees.':
        'No divergence is settled: both values are preserved.',
    'Aucune signature n a ete verifiee ; le recu n est pas qualifie de signe.':
        'No signature was verified; the receipt is not called signed.',
    'Aucune correspondance n est devinee : sans entree dans la table, un champ est NOT COMPARABLE.':
        'No mapping is guessed: without an entry in the table, a field is NOT COMPARABLE.',
    'aucune liaison etablie : il n y a pas de cote NeoMundi a confronter.':
        'no binding established: there is no NeoMundi side to compare against.',

    # ====================================================================
    # reconcile.py, sign.py, receipt_import.py
    # ====================================================================
    # ---- prose sans argument
    'FRONTIERES DE COMPARABILITE -- evaluees AVANT les valeurs :':
        'COMPARABILITY BOUNDARIES -- evaluated BEFORE the values:',
    'la table ne declare aucune correspondance':
        'the table declares no mapping',
    'Aucun statut n a change : seul le code de sortie en tient compte (2).':
        'No status changed: only the exit code accounts for it (2).',
    'MODE STRICT : tous les champs sont etablis.':
        'STRICT MODE: every field is established.',
    'NE JAMAIS la commiter, ni la placer dans une archive ou un exemple.':
        'NEVER commit it, and never place it in an archive or an example.',
    'L archive n a pas ete touchee : l attestation est DETACHEE.':
        'The archive was not touched: the attestation is DETACHED.',
    '`attested_at_declared` est une date DECLAREE, pas un horodatage':
        '`attested_at_declared` is a DECLARED date, not an independent',
    'independant. Verifier avec :':
        'timestamp. Verify with:',
    '[FAIL] `cryptography` est requis pour SIGNER : pip install cryptography':
        '[FAIL] `cryptography` is required to SIGN: pip install cryptography',
    '(le verificateur, lui, s en passe et rend NOT TESTED)':
        '(the verifier, however, does without it and returns NOT TESTED)',
    '[FAIL] attestation retrospective refusee : le manifeste du sujet ne porte aucune date de gel exploitable. Une attestation retrospective doit conserver la date de gel du corpus.':
        "[FAIL] retrospective attestation refused: the subject's manifest carries no usable freeze date. A retrospective attestation must preserve the corpus freeze date.",
    '[note] mode 0600 non applique par ce systeme de fichiers':
        '[note] mode 0600 not applied by this filesystem',
    '[FAIL] l archive n a pas de manifest.json':
        '[FAIL] the archive has no manifest.json',
    'signatures  : 0 -- aucune n est reconnue par cet outil':
        'signatures  : 0 -- none is recognised by this tool',
    'AUCUNE correspondance n a ete supposee. Pour reconcilier, fournir une':
        'NO mapping has been assumed. To reconcile, supply an',
    'table de correspondance EXPLICITE a `adapters/reconcile.py`.':
        'EXPLICIT mapping table to `adapters/reconcile.py`.',

    # ====================================================================
    # bind.py
    # ====================================================================
    # ---- prose, intitules et details sans argument
    'Rappel : une correspondance d empreinte dit que le fichier est celui':
        'Reminder: a digest match says the file is the one',
    'auquel l enregistrement se refere. Elle ne dit pas que l execution a':
        'the record refers to. It does not say the execution',
    'eu lieu. Verifier avec : python bind.py verify <manifeste>':
        'took place. Verify with: python bind.py verify <manifest>',
    'le sujet existe dans son archive':
        'the subject exists in its archive',
    '--- verification de l attestation du sujet ---':
        "--- verification of the subject's attestation ---",
    '--- fin de la verification de l attestation ---':
        '--- end of the attestation verification ---',
    'attestation de l archive du sujet':
        "attestation of the subject's archive",
    'l archive est attestee par une cle de confiance : les empreintes qu elle declare le sont aussi, et les artefacts qui s y hachent en heritent.':
        'the archive is attested by a trusted key: so are the digests it declares, and the artifacts that hash to them inherit it.',
    'elevation des artefacts par l attestation':
        'elevation of the artifacts by the attestation',
    'signatures inscrites au manifeste':
        'signatures recorded in the manifest',
    'enonces attaches au manifeste':
        'statements attached to the manifest',
    'verite de l execution':
        'truth of the execution',
    'hors de portee de cet outil et de ce depot. Lier un artefact a un enregistrement ne dit pas qu une execution a eu lieu, ni quand, ni chez qui. Aucune horloge de confiance, aucun ancrage exterieur.':
        'out of reach of this tool and of this repository. Binding an artifact to a record does not say an execution took place, nor when, nor at whose hands. No trusted clock, no external anchor.',
    'Les autres restent au niveau `declared` : aucun ancrage ne les tient.':
        'The others stay at level `declared`: no anchor holds them.',
    'schema de manifeste reconnu':
        'manifest schema recognised',
    'archive non fournie. La fournir avec --archive <fichier> pour que les empreintes declarees soient confrontees a l enregistrement.':
        'archive not supplied. Supply it with --archive <file> so that the declared digests are compared against the record.',
    'l archive fournie est celle du manifeste':
        "the supplied archive is the manifest's",
    'le manifeste ne porte pas d empreinte d archive':
        'the manifest carries no archive digest',
    'le sujet concorde avec l enregistrement':
        'the subject agrees with the record',
    'les empreintes declarees sont celles de l enregistrement':
        "the declared digests are the record's",
    'empreintes de l enregistrement non reprises au manifeste':
        'digests of the record not carried over to the manifest',
    'aucune revendication ne depasse ce qui est demontre':
        'no claim exceeds what is demonstrated',
    'revendications non eprouvees faute d artefact':
        'claims not exercised for want of an artifact',
    'manifeste lisible':
        'manifest readable',
    'Cette liaison ne doit pas etre presentee comme verifiee.':
        'This binding must not be presented as verified.',
    'l archive n a pas de membre observations.jsonl':
        'the archive has no observations.jsonl member',
    'verify_attestation introuvable : %s':
        'verify_attestation not found: %s',
    'aucune revendication n a pu etre eprouvee : rien n est affirme ici.':
        'no claim could be exercised: nothing is asserted here.',
    'Soit : les artefacts offerts sont ceux auxquels l enregistrement\nse refere, ET une partie identifiee s est engagee sur l empreinte\nde l archive qui les declare. Ce n est toujours pas une preuve que\nl execution a eu lieu, ni une preuve de la DATE : celle-ci reste\ndeclaree faute d ancrage tiers.':
        'That is: the artifacts offered are the ones the record refers\nto, AND an identified party committed to the digest of the\narchive that declares them. It is still not a proof that the\nexecution took place, nor a proof of the DATE: that remains\ndeclared, for want of a third-party anchor.',
    'Soit : les artefacts offerts sont bien ceux auxquels\nl enregistrement se refere. Ce n est pas une preuve que\nl execution a eu lieu.':
        'That is: the artifacts offered are indeed the ones the\nrecord refers to. It is not a proof that the execution\ntook place.',
    'Soit : rien n a pu etre ancre dans l enregistrement. Le\nmanifeste est un document, pas une preuve.':
        'That is: nothing could be anchored in the record. The\nmanifest is a document, not a proof.',

    # ====================================================================
    # timestamp.py
    # ====================================================================
    # ---- prose et intitules, sans argument
    'SEULE cette valeur de 32 octets est transmise. Ni l archive, ni le':
        'ONLY this 32-byte value is transmitted. Neither the archive, nor the',
    'manifeste, ni aucune donnee de pilote ne quitte ce poste.':
        'manifest, nor any pilot data leaves this machine.',
    'de temps.** Relancer `upgrade` dans quelques heures, une fois la':
        'of time.** Re-run `upgrade` in a few hours, once the',
    'transaction confirmee par la chaine.':
        'transaction is confirmed by the chain.',
    '(lue a offset fixe, sans aucune dependance)':
        '(read at a fixed offset, with no dependency at all)',
    'temps verifie par un tiers':
        'time verified by a third party',
    'qualification eIDAS':
        'eIDAS qualification',
    'AUCUNE. OpenTimestamps n est pas un prestataire de services de confiance qualifie au sens du reglement eIDAS, et rien ici ne doit etre presente comme un horodatage qualifie.':
        'NONE. OpenTimestamps is not a qualified trust service provider under the eIDAS regulation, and nothing here may be presented as a qualified timestamp.',
    'ce n est pas un fichier .ots detache : la magie attendue est absente':
        'this is not a detached .ots file: the expected magic is absent',
    '[FAIL] aucun calendrier n a repondu : aucune preuve n a ete ecrite.':
        '[FAIL] no calendar answered: no proof was written.',
    'attestations : NON LUES -- `opentimestamps` est absent.':
        'attestations: NOT READ -- `opentimestamps` is absent.',
    'pip install opentimestamps pour les lire.':
        'pip install opentimestamps to read them.',
    'Au moins une attestation Bitcoin est presente. Le TEMPS qu elle':
        'At least one Bitcoin attestation is present. The TIME it',
    'porte reste a verifier avec le client officiel :':
        'carries remains to be verified with the official client:',
    'revendique reste a verifier avec le client officiel :':
        'claims remains to be verified with the official client:',
    '**Ce n est pas une preuve de temps.** Relancer `upgrade` plus tard.':
        '**This is not a proof of time.** Re-run `upgrade` later.',
    'sujet non fourni. Le fournir avec --subject <fichier> pour que la liaison soit eprouvee.':
        'subject not supplied. Supply it with --subject <file> so that the binding is exercised.',
    'descripteur de liaison':
        'binding descriptor',
    'aucun descripteur fourni ; la liaison ci-dessus suffit a etablir sur quoi la preuve porte.':
        'no descriptor supplied; the binding above is enough to establish what the proof is about.',
    'arbre des attestations':
        'attestation tree',
    '`opentimestamps` est absent de cet environnement : l arbre n est pas lu. `pip install opentimestamps` pour l eprouver. La LIAISON ci-dessus, elle, ne depend de rien.':
        '`opentimestamps` is absent from this environment: the tree is not read. `pip install opentimestamps` to exercise it. The BINDING above, however, depends on nothing.',
    'etat inconnu sans la bibliotheque':
        'state unknown without the library',
    'Cette preuve ne doit pas etre presentee comme verifiee.':
        'This proof must not be presented as verified.',
    'Rien n a progresse : la transaction n est probablement pas encore':
        'Nothing progressed: the transaction is probably not yet',
    'confirmee par la chaine. Reessayer plus tard. Tant qu aucune':
        'confirmed by the chain. Try again later. As long as no',
    'attestation Bitcoin n apparait, **aucune date n est attestee.**':
        'Bitcoin attestation appears, **no date is attested.**',
    'La preuve porte desormais une attestation Bitcoin. Le TEMPS qu elle':
        'The proof now carries a Bitcoin attestation. The TIME it',
    'La preuve s engage sur le sujet, et porte une attestation Bitcoin.':
        'The proof commits to the subject, and carries a Bitcoin attestation.',
    'Le TEMPS qu elle revendique reste a verifier avec `ots verify`.':
        'The TIME it claims remains to be verified with `ots verify`.',
    'La liaison est etablie. Le TEMPS ne l est PAS : la preuve est':
        'The binding is established. The TIME is NOT: the proof is',
    'PENDING, ce qui n atteste aucune date.':
        'PENDING, which attests no date.',
    'la preuve s engage exactement sur l empreinte du sujet':
        "the proof commits exactly to the subject's digest",
    'le descripteur devrait etre un objet JSON':
        'the descriptor should be a JSON object',

    # ====================================================================
    # verify_attestation.py
    # ====================================================================

    # ---- intitules de controle ------------------------------------------
    # ---- C-5 : la confrontation de l empreinte du magasin ---------------
    "empreinte du magasin confrontee": "trust store digest compared",
    "aucune empreinte fournie. La fournir avec --store-digest <sha256>, "
    "obtenue par un AUTRE canal que celui qui a fourni le magasin. Un "
    "magasin non confronte n est pas faux : il est non confronte.":
        "no digest supplied. Supply it with --store-digest <sha256>, "
        "obtained through a channel OTHER than the one that supplied the "
        "store. An uncompared store is not false: it is uncompared.",
    "ancrage tiers": "third-party anchor",
    "attestation lisible": "attestation readable",
    "capacite juridique du signataire": "legal capacity of the signer",
    # Le sens de chaque valeur de `legal_capacity_to_attest`. Ces chaines sont
    # passees en argument a la ligne de controle : elles doivent etre au
    # catalogue EXACT pour que `_argument_traduit` les rende en anglais.
    "l entite est NOMMEE et a decide d attester dans un cadre scientifique "
    "et non commercial ; AUCUNE verification de ses pouvoirs n a ete faite. "
    "Identite DECLAREE, non juridiquement VERIFIEE : ceci n est pas une "
    "certification juridique.":
        "the entity is NAMED and has decided to attest within a scientific, "
        "non-commercial scope; NO verification of its powers has been "
        "performed. An identity DECLARED, not legally VERIFIED: this is not a "
        "legal certification.",
    "aucune verification des pouvoirs, et aucune decision documentee non "
    "plus. Identite DECLAREE seulement.":
        "no verification of powers, and no documented decision either. An "
        "identity DECLARED only.",
    "des pouvoirs ont ete verifies HORS de ce code, et ce champ n en est que "
    "la declaration. Le verificateur ne refait pas ce controle.":
        "powers were verified OUTSIDE this code, and this field is only the "
        "declaration of it. The verifier does not redo that check.",
    "la capacite est CONTESTEE. Lire l attestation comme engageante serait "
    "abusif.":
        "the capacity is DISPUTED. Reading the attestation as binding would "
        "be improper.",
    "ce role ne s engage sur rien ; la question ne se pose pas.":
        "this role commits to nothing; the question does not arise.",
    "valeur non connue de ce verificateur ; elle n est pas interpretee.":
        "a value unknown to this verifier; it is not interpreted.",
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
    # B-2 : registre des paquets signes et cycle de vie des cles.
    'deviendraient NON FIABLES retroactivement, quelle que soit leur date':
        'would become UNTRUSTED retroactively, whatever date they declare.',
    'declaree. Une rotation, elle, les laisserait de confiance.':
        'A rotation, by contrast, would leave them trusted.',
    '[note] AUCUN registre tenu. Sans `--register <fichier>`, rien ne':
        '[note] NO register kept. Without `--register <file>`, nothing',
    'consigne que cette cle a signe ce paquet -- et une':
        'records that this key signed this package -- and a',
    'compromission ne pourra pas etre circonscrite : elle':
        'compromise could not be scoped: it would invalidate',
    'invalidera TOUT ce que la cle a jamais signe.':
        'EVERYTHING the key ever signed.',
    '[FAIL] registre VIDE. Ce n est pas la preuve que la cle n a rien':
        '[FAIL] register EMPTY. That is not proof the key signed nothing:',
    'signe : c est l absence de toute information. Une':
        'it is the absence of any information at all. A',
    'compromission resterait non circonscrivable.':
        'compromise would remain unscopable.',
    'Aucune attestation consignee pour cette cle -- dans la limite de':
        'No attestation recorded for this key -- within the limits of',
    'ce registre, et de rien d autre.':
        'this register, and nothing else.',
    'Une ROTATION laisse les signatures anterieures DE CONFIANCE :':
        'A ROTATION leaves earlier signatures TRUSTED:',
    'une attestation declaree avant la rotation reste valide.':
        'an attestation declared before the rotation stays valid.',
    'Une COMPROMISSION est RETROACTIVE : toutes les signatures de':
        'A COMPROMISE is RETROACTIVE: every signature made with this',
    'cette cle deviennent non fiables, quelle que soit leur date':
        'key becomes untrusted, whatever date it declares -- because',
    'declaree -- parce qu un voleur choisit la date qu il ecrit.':
        'a thief chooses the date they write.',
    '[FAIL] une rotation exige `--successor <kid>`. Retirer une cle':
        '[FAIL] a rotation requires `--successor <kid>`. Withdrawing a key',
    'sans nommer celle qui la remplace est une revocation a sec.':
        'without naming its replacement is a dry revocation.',
    '[FAIL] `--successor` ne s applique pas a une compromission : une':
        '[FAIL] `--successor` does not apply to a compromise: a compromised',
    'cle compromise n est pas remplacee, elle est retiree, et':
        'key is not replaced, it is withdrawn, and all of its',
    'ses signatures anterieures tombent toutes.':
        'earlier signatures fall with it.',
    '[note] aucun registre fourni : la portee reste INCONNUE.':
        '[note] no register supplied: the scope remains UNKNOWN.',
    'la suite. Un remplacant doit etre utilisable.':
        'over. A replacement must be usable.',
    '[FAIL] cle %s deja COMPROMISE. Une compromission ne se requalifie pas en rotation : elle est retroactive et definitive.':
        '[FAIL] key %s already COMPROMISED. A compromise is not requalified as a rotation: it is retroactive and final.',
    '[FAIL] successeur %s ABSENT de ce magasin. Le generer et le publier d abord (genkey --append) : sinon tout consommateur se retrouve avec une cle a ne plus croire et aucune a croire.':
        '[FAIL] successor %s ABSENT from this store. Generate and publish it first (genkey --append): otherwise every consumer is left with a key to distrust and none to trust.',
    '[FAIL] `kid` %s DEJA present dans ce magasin. Un `kid` ne se reutilise jamais.':
        '[FAIL] `kid` %s ALREADY present in this store. A `kid` is never reused.',
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
    "%d enregistrement(s) au registre, %d exporte(s), %d retenu(s) : %s. Les "
    "decomptes s additionnent. Ce qui est retenu est NOMME, donc l absence est "
    "une exclusion declaree et non un manque silencieux.":
        "%d record(s) in the ledger, %d exported, %d withheld: %s. The counts "
        "add up. What is withheld is NAMED, so the absence is a declared "
        "exclusion and not a silent gap.",
    "le registre annonce %d enregistrement(s), or %d exporte(s) + %d retenu(s) "
    "font %d":
        "the ledger announces %d record(s), yet %d exported + %d withheld "
        "make %d",
    "le contrat annonce %d enregistrement(s) exporte(s), les decomptes des "
    "membres en totalisent %d":
        "the contract announces %d exported record(s), the members' counts "
        "total %d",
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

    # ---- reconcile.py : ossature et notes formatees
    '[%-14s] %-26s  recu=%-14s  nous=%s':
        '[%-14s] %-26s  receipt=%-14s  us=%s',
    'une empreinte du recu egale une empreinte que l enregistrement declare : %s':
        'a digest of the receipt equals a digest the record declares: %s',
    'le recu porte %s = %r, retrouve dans notre corpus':
        'the receipt carries %s = %r, found again in our corpus',
    'ecart %.6g, dans la tolerance %.6g':
        'gap %.6g, within the tolerance %.6g',
    'ecart %.6g, au-dela de la tolerance %.6g. **LES DEUX VALEURS SONT CONSERVEES TELLES QUELLES** : rien n est tranche ici.':
        'gap %.6g, beyond the tolerance %.6g. **BOTH VALUES ARE PRESERVED AS THEY ARE**: nothing is settled here.',
    'l etiquette %r n est pas dans le recu ; notre cote porte une valeur':
        'label %r is not in the receipt; our side carries a value',
    'le recu porte une valeur ; notre enregistrement n a pas de champ %r pour cette observation':
        'the receipt carries a value; our record has no field %r for this observation',
    'VALEUR MESUREE, et une frontiere de comparabilite est franchie : %s. Les deux valeurs ne mesurent donc pas forcement la meme chose, et les declarer divergentes serait une faute de raisonnement, pas une decouverte.':
        'MEASURED VALUE, and a comparability boundary is crossed: %s. The two values therefore do not necessarily measure the same thing, and declaring them divergent would be a reasoning error, not a discovery.',
    'le recu declare cette valeur, et sa verification demande %s -- qui n est pas fourni. Ce n est ni une concordance ni une divergence : c est une impossibilite de controler.':
        'the receipt declares this value, and verifying it requires %s -- which is not supplied. This is neither an agreement nor a divergence: it is an impossibility to check.',
    'aucune empreinte ni identifiant commun. L observation %r a ete DEMANDEE, mais une demande n est pas une correspondance demontree : la liaison est refusee.':
        'no digest and no identifier in common. Observation %r was REQUESTED, but a request is not a demonstrated match: the binding is refused.',
    'ETIQUETTE AMBIGUE : %d champs du recu portent %r (%s). Viser un `receipt_source_path` dans la table pour lever l ambiguite. Choisir le premier serait deviner.':
        'AMBIGUOUS LABEL: %d fields of the receipt carry %r (%s). Target a `receipt_source_path` in the table to lift the ambiguity. Choosing the first would be guessing.',
    '%s du recu NON DECLAREE -- impossible d etablir la comparabilite':
        '%s of the receipt NOT DECLARED -- comparability cannot be established',
    '%s de notre cote inconnue':
        '%s on our side unknown',
    '%s : recu %r, nous %r':
        '%s: receipt %r, us %r',

    # ====================================================================
    # reconcile.py, sign.py, receipt_import.py
    # ====================================================================
    # ---- prose et details formates
    'Recu     : %s':
        'Receipt  : %s',
    'source : %s (%s)':
        'source : %s (%s)',
    'Archive  : %s':
        'Archive  : %s',
    'Table    : %s (%d correspondance(s) declaree(s))':
        'Table    : %s (%d declared mapping(s))',
    'LIAISON  : %s':
        'BINDING  : %s',
    'CHAMP PAR CHAMP (tolerance numerique %.6g) :':
        'FIELD BY FIELD (numeric tolerance %.6g):',
    '%s : schema %r inconnu ; attendu %r':
        '%s: schema %r unknown; expected %r',
    'Aucune liaison : %d champ(s) ressortent NOT COMPARABLE.':
        'No binding: %d field(s) come out NOT COMPARABLE.',
    'materiaux fournis : %s':
        'materials supplied: %s',
    '%d contradiction(s) CONSERVEE(S), aucune tranchee :':
        '%d contradiction(s) PRESERVED, none settled:',
    'MODE STRICT : %d champ(s) non etabli(s), liaison %s.':
        'STRICT MODE: %d field(s) not established, binding %s.',
    'rapport Markdown : %s':
        'Markdown report : %s',
    'rapport JSON     : %s':
        'JSON report     : %s',
    '%s : recu %r / nous %r  [%s]':
        '%s: receipt %r / us %r  [%s]',
    '[FAIL      ] %s':
        '[FAIL      ] %s',
    'cle privee ecrite : %s':
        'private key written: %s',
    'kid             : %s':
        'kid             : %s',
    'attestation ecrite : %s':
        'attestation written: %s',
    'sujet            : %s':
        'subject          : %s',
    'bundle_sha256    : %s':
        'bundle_sha256    : %s',
    'nature           : %s':
        'nature           : %s',
    'cle              : %s':
        'key              : %s',
    'gel du sujet     : %s (conserve)':
        'subject freeze   : %s (preserved)',
    'python verify_attestation.py %s --archive %s --trust-store <magasin>':
        'python verify_attestation.py %s --archive %s --trust-store <store>',
    '[FAIL] refus d ecrire %s sous la racine du depot (%s).\n       Une cle privee commitee reste dans l historique Git pour toujours.\n       Choisir un chemin hors du depot.':
        '[FAIL] refusing to write %s under the repository root (%s).\n       A committed private key stays in Git history forever.\n       Choose a path outside the repository.',
    'magasin de confiance ecrit : %s':
        'trust store written      : %s',
    'cle publique (x)         : %s':
        'public key (x)           : %s',
    '[FAIL] archive introuvable : %s':
        '[FAIL] archive not found: %s',
    'source      : %s (%s, %d octets)':
        'source      : %s (%s, %d bytes)',
    'champs      : %d candidats releves':
        'fields      : %d candidates collected',
    'empreintes  : %d trouvees dans le document':
        'digests     : %d found in the document',
    'recu de %d octets, au-dela du plafond de %d : non lu':
        'receipt of %d bytes, beyond the ceiling of %d: not read',
    'recu normalise : %s':
        'normalised receipt: %s',
    'recu JSON illisible : %s':
        'unreadable JSON receipt: %s',

    # ====================================================================
    # bind.py
    # ====================================================================
    # ---- prose et details formates
    '%d artefact(s), %d empreinte(s) declaree(s) par l enregistrement.':
        '%d artifact(s), %d digest(s) declared by the record.',
    '%d artefact(s) se hachent sur une empreinte de l enregistrement.':
        '%d artifact(s) hash to a digest of the record.',
    '%d artefact(s)':
        '%d artifact(s)',
    '%d signature(s) presente(s) (cles %s) et AUCUNE n est verifiee ici. Une signature non verifiee ne vaut pas mieux qu un champ texte.':
        '%d signature(s) present (keys %s) and NONE is verified here. An unverified signature is worth no more than a text field.',
    '%d enonce(s). Une description textuelle d une execution ne constitue pas une preuve que cette execution a eu lieu : aucun de ces textes n est verifie, ni ne peut l etre.':
        '%d statement(s). A textual description of an execution does not constitute a proof that this execution took place: none of these texts is verified, nor can be.',
    'Manifeste de preuve : %s':
        'Evidence manifest   : %s',
    'empreinte           : %s':
        'digest              : %s',
    'racine des artefacts: %s':
        'artifact root       : %s',
    'chemin absolu refuse : %r':
        'absolute path refused: %r',
    'traversee de repertoire refusee : %r':
        'directory traversal refused: %r',
    'le chemin sort du repertoire racine : %r resout hors de %s':
        'the path escapes the root directory: %r resolves outside %s',
    'manifeste ecrit : %s':
        'manifest written: %s',
    'empreinte        : %s':
        'digest           : %s',
    '%d empreinte(s)':
        '%d digest(s)',
    '%s : rien n est offert pour elles':
        '%s: nothing is offered for them',
    'ses octets se hachent sur %s de l enregistrement. Niveau derive : %s.':
        'its bytes hash to %s of the record. Derived level: %s.',
    'aucune attestation fournie. La fournir avec --attestation <fichier.jws> --trust-store <magasin> pour que le niveau `%s` soit atteignable.':
        'no attestation supplied. Supply it with --attestation <file.jws> --trust-store <store> so that level `%s` becomes reachable.',
    'une attestation est fournie sans --archive ou sans --trust-store : elle ne peut etre confrontee a rien. Aucun niveau n est eleve.':
        'an attestation is supplied without --archive or without --trust-store: it can be compared to nothing. No level is raised.',
    'l attestation fournie n atteint pas `%s` (%d FAIL, %d NOT TESTED dans sa propre verification). Aucun niveau n est eleve.':
        'the supplied attestation does not reach `%s` (%d FAIL, %d NOT TESTED in its own verification). No level is raised.',
    '%s. Fournir les fichiers sous --root pour les eprouver.':
        '%s. Supply the files under --root to exercise them.',
    'aucune, et ce depot n en verifie aucune : le tableau `signatures[]` du manifeste reste non exploite. Le niveau `%s` s obtient par une attestation DETACHEE de l archive (--attestation), pas par ce champ.':
        "none, and this repository verifies none: the manifest's `signatures[]` array stays unused. Level `%s` is obtained by an attestation DETACHED from the archive (--attestation), not by this field.",
    'Niveau de garantie DERIVE pour la liaison : %s':
        'Assurance level DERIVED for the binding: %s',
    'aucune observation %r dans l archive (%d observations presentes)':
        'no observation %r in the archive (%d observations present)',
    '%d observations portent l identifiant %r : l archive est ambigue':
        '%d observations carry the identifier %r: the archive is ambiguous',
    'artefact mal forme : %r ; attendu role=chemin':
        'malformed artifact: %r; expected role=path',
    'role %r inconnu ; connus : %s':
        'role %r unknown; known: %s',
    'artefact introuvable : %s':
        'artifact not found: %s',
    'le manifeste nomme %s ; l archive fournie se hache sur %s':
        'the manifest names %s; the supplied archive hashes to %s',
    'fichier absent sous la racine : %s. Sa revendication `%s` n a pas pu etre eprouvee ; elle n est pas contredite pour autant.':
        'file absent under the root: %s. Its claim `%s` could not be exercised; it is not contradicted for that.',
    '%d octets, au-dela du plafond de %d. Non lu : relever le plafond avec --max-artifact-bytes pour l eprouver.':
        '%d bytes, beyond the ceiling of %d. Not read: raise the ceiling with --max-artifact-bytes to exercise it.',
    'le manifeste annonce %s..., le fichier se hache sur %s...':
        'the manifest announces %s..., the file hashes to %s...',
    'annoncee %d octets, observee %d':
        'announced %d bytes, observed %d',
    'present et conforme au manifeste, mais SANS ancrage dans l enregistrement. Niveau derive : %s.':
        'present and conformant to the manifest, but with NO anchor in the record. Derived level: %s.',
    'pretend se lier a %s, que l enregistrement ne declare pas. Un fichier quelconque ne devient pas une preuve en se nommant.':
        'claims to bind to %s, which the record does not declare. Any old file does not become evidence by naming itself.',
    'l enregistrement declare %s = %s..., le fichier se hache sur %s...':
        'the record declares %s = %s..., the file hashes to %s...',
    '%d revendication(s) eprouvee(s)':
        '%d claim(s) exercised',
    'controle interrompu : %s: %s':
        'check interrupted: %s: %s',
    'Soit : %d artefact(s) sur %d n ont pas pu etre eprouves ici,\ndonc la liaison entiere retombe au niveau declaratif. Ce n est\npas un refus du manifeste : c est une verification incomplete.':
        'That is: %d artifact(s) out of %d could not be exercised here,\nso the whole binding falls back to the declarative level. This\nis not a refusal of the manifest: it is an incomplete check.',

    # ====================================================================
    # timestamp.py
    # ====================================================================
    # ---- prose et details formates
    'Sujet      : %s':
        'Subject    : %s',
    'Empreinte  : %s':
        'Digest     : %s',
    'preuve ecrite : %s (%d octets)':
        'proof written: %s (%d bytes)',
    'ETAT : PENDING sur %d calendrier(s). **Ce n est pas encore une preuve':
        'STATE: PENDING on %d calendar(s). **This is not yet a proof',
    'Preuve    : %s (%d octets)':
        'Proof     : %s (%d bytes)',
    'empreinte : %s':
        'digest    : %s',
    'empreinte engagee : %s':
        'committed digest  : %s',
    '%d attestation(s) :':
        '%d attestation(s):',
    'Preuve  : %s':
        'Proof   : %s',
    'empreinte de la preuve : %s':
        'digest of the proof    : %s',
    'sujet   : %s':
        'subject : %s',
    'magie, version %d, SHA-256 ; %d octets':
        'magic, version %d, SHA-256; %d bytes',
    'hors de portee de cet outil : valider une attestation Bitcoin demande un en-tete de bloc, donc une source de confiance que nous n avons pas. A confronter avec le client officiel : `ots verify %s`':
        'out of reach of this tool: validating a Bitcoin attestation needs a block header, hence a source of trust we do not have. To be compared with the official client: `ots verify %s`',
    'Preuve      : %s':
        'Proof       : %s',
    'engagee sur : %s':
        'committed to: %s',
    'nouvelle preuve : %s':
        'new proof       : %s',
    'attestations Bitcoin : %d avant, %d apres':
        'Bitcoin attestations : %d before, %d after',
    'l ancienne preuve est INTACTE : %s':
        'the earlier proof is INTACT    : %s',
    'preuve trop courte : %d octets, il en faut au moins %d':
        'proof too short: %d bytes, at least %d are needed',
    'version majeure %d non prise en charge ; attendu %d':
        'major version %d not supported; expected %d',
    'operation de hachage 0x%02x non prise en charge ; seul SHA-256 (0x%02x) est accepte':
        'hash operation 0x%02x not supported; only SHA-256 (0x%02x) is accepted',
    '[FAIL] sujet introuvable : %s':
        '[FAIL] subject not found: %s',
    'descripteur   : %s':
        'descriptor    : %s',
    'ots verify %s':
        'ots verify %s',
    'Aucune attestation Bitcoin : %d PENDING seulement.':
        'No Bitcoin attestation: %d PENDING only.',
    'descripteur     : %s':
        'descriptor      : %s',
    'upgraded_from : %s':
        'upgraded_from : %s',
    '[FAIL] %s':
        '[FAIL] %s',
    'PENDING   %s':
        'PENDING   %s',
    'sujet introuvable : %s':
        'subject not found: %s',
    'preuve illisible par la bibliotheque officielle : %s: %s':
        'proof unreadable by the official library: %s: %s',
    '%d pending, %d bitcoin, %d inconnue(s)':
        '%d pending, %d bitcoin, %d unknown',
    'BITCOIN   bloc %d':
        'BITCOIN   block %d',
    'INCONNUE  tag %s':
        'UNKNOWN   tag %s',
    'la preuve s engage sur %s..., le sujet se hache sur %s...':
        'the proof commits to %s..., the subject hashes to %s...',
    'concordant ; soumis le %s (declare)':
        'concordant; submitted on %s (declared)',
    '%d attestation(s) Bitcoin, bloc(s) %s':
        '%d Bitcoin attestation(s), block(s) %s',
    '%d attestation(s) PENDING et AUCUNE Bitcoin. Un `pending` dit qu un calendrier s est engage a inclure l empreinte dans une transaction future : il n atteste aucune date. Relancer `upgrade` apres confirmation.':
        '%d PENDING attestation(s) and NO Bitcoin one. A `pending` says a calendar undertook to include the digest in a future transaction: it attests no date. Re-run `upgrade` after confirmation.',
    '[FAIL] %s existe deja. Choisir un autre nom, ou --force.\n       Une preuve ne s ecrase pas : l anterieure est une piece.':
        '[FAIL] %s already exists. Choose another name, or --force.\n       A proof is not overwritten: the earlier one is evidence.',
    '[FAIL] `opentimestamps` est requis pour HORODATER : pip install opentimestamps\n       (le verificateur, lui, lit la liaison sans aucune dependance)\n       cause : %s: %s':
        '[FAIL] `opentimestamps` is required to STAMP: pip install opentimestamps\n       (the verifier, however, reads the binding with no dependency)\n       cause: %s: %s',
    '[FAIL] `opentimestamps` est requis pour mettre a niveau : pip install opentimestamps\n       cause : %s: %s':
        '[FAIL] `opentimestamps` is required to upgrade: pip install opentimestamps\n       cause: %s: %s',
    '[FAIL] ce descripteur ne decrit pas cette preuve :\n       il annonce le sujet %s\n       la preuve engage     %s':
        '[FAIL] this descriptor does not describe this proof:\n       it announces subject %s\n       the proof commits to %s',

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
    "declaree `%s` pour %s (%s) -- %s Aucun code ne peut etablir qu une entite "
    "peut legalement s engager : c est une question juridique, et elle reste "
    "ouverte.":
        "declared `%s` for %s (%s) -- %s No code can establish that an entity "
        "may legally commit: that is a legal question, and it remains open.",
    "l attestation declare %s..., le fichier fourni se hache sur %s... : ce n "
    "est pas la preuve nommee.":
        "the attestation declares %s..., the supplied file hashes to %s...: "
        "this is not the named proof.",
    "l attestation declare une preuve d empreinte %s... ; la fournir avec "
    "--anchor-proof <fichier> pour confronter ses octets.":
        "the attestation declares a proof with digest %s...; supply it with "
        "--anchor-proof <file> to compare its bytes.",
    "preuve d ancrage introuvable : %s": "anchor proof not found: %s",
    "les octets du magasin se hachent sur l empreinte annoncee par un "
    "second canal (%s...). Un faussaire devrait compromettre les DEUX.":
        "the store's bytes hash to the digest announced by a second channel "
        "(%s...). A forger would have to compromise BOTH.",
    "le magasin fourni se hache sur %s..., le second canal annonce %s... : "
    "ce n est pas le meme magasin. Ne pas s en servir.":
        "the supplied store hashes to %s..., the second channel announces "
        "%s...: this is not the same store. Do not use it.",
    "%s v%s, politique %s, %d cle(s), %d identite(s)":
        "%s v%s, policy %s, %d key(s), %d identity(ies)",
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
    # B-2 : registre des paquets signes et cycle de vie des cles.
    'registre complete : %s':
        'register appended : %s',
    'registre : %s -- %d attestation(s) consignee(s)':
        'register : %s -- %d attestation(s) recorded',
    'cle       : %s -- %d concernee(s)':
        'key      : %s -- %d affected',
    'Si cette cle etait marquee `compromised`, ces %d attestation(s)':
        'If this key were marked `compromised`, those %d attestation(s)',
    'magasin ecrit : %s':
        'store written : %s',
    'cle retiree : %s -> `%s` le %s':
        'key withdrawn : %s -> `%s` on %s',
    'motif       : %s':
        'reason        : %s',
    'store_version            : %s':
        'store_version            : %s',
    '%s  bundle %s...  att %s...':
        '%s  bundle %s...  att %s...',
    '[FAIL] %s n est pas un magasin %s':
        '[FAIL] %s is not a %s store',
    '[FAIL] cle %s absente du magasin %s':
        '[FAIL] key %s absent from store %s',
    'remplacee par : %s':
        'replaced by   : %s',
    'Portee consignee : %d attestation(s) concernee(s).':
        'Recorded scope : %d attestation(s) affected.',
    '[FAIL] `--append` demande, mais %s n existe pas.':
        '[FAIL] `--append` requested, but %s does not exist.',
    '[FAIL] successeur %s de statut `%s` : il ne peut pas prendre':
        '[FAIL] successor %s has status `%s`: it cannot take',
}


# --------------------------------------------------------------------------


#: Un specificateur printf complet : drapeaux, largeur, precision, type.
#: `%-14s`, `%.6g`, `%02d` sont tous des specificateurs, et un seul non
#: reconnu suffisait a faire rater tout le motif -- donc a laisser sortir
#: du francais, en silence.
_SPEC = _re_module.compile(r"%([-+ 0#]*)(\d*)(?:\.(\d+))?([dsrgfeiu])")


def _vers_motif(format_fr: str) -> tuple[_re_module.Pattern[str], list[str]]:
    """Derive de `format_fr` une expression reguliere et l ordre de ses types.

    `%d` ne capture que des chiffres, pour qu un format a deux `%d` ne
    morde pas sur une chaine qui en contiendrait un. Les autres capturent
    souplement, et le motif est ancre des deux cotes : sans ancrage, un
    format court matcherait l interieur d un format long et la traduction
    partirait sur le mauvais.

    La LARGEUR n est jamais imposee au motif. `%-14s` rend une valeur
    padd�e a droite, et exiger exactement 14 caracteres ferait rater une
    valeur plus longue : printf deborde, il ne tronque pas. On capture donc
    souplement, espaces de remplissage compris, et c est le format anglais
    qui refait la mise en page.
    """
    morceaux: list[str] = []
    types: list[str] = []
    index = 0
    while index < len(format_fr):
        if format_fr[index] == "%":
            if format_fr[index:index + 2] == "%%":
                morceaux.append(_re_module.escape("%"))
                index += 2
                continue
            trouve = _SPEC.match(format_fr, index)
            if trouve is not None:
                marque = trouve.group(4)
                if marque in ("d", "i", "u"):
                    # Une largeur peut avoir ajoute des espaces autour.
                    morceaux.append(r"\s*(-?\d+)\s*")
                    types.append("d")
                elif marque in ("g", "f", "e"):
                    morceaux.append(r"\s*(-?[\d.eE+-]+)\s*")
                    types.append("g")
                else:
                    morceaux.append(r"(.*?)")
                    types.append(marque)
                index = trouve.end()
                continue
        morceaux.append(_re_module.escape(format_fr[index]))
        index += 1
    return (_re_module.compile(r"\A" + "".join(morceaux) + r"\Z", _re_module.S),
            types)


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
    """Remplace chaque `%r` par `%s`, specificateurs complets compris.

    Une valeur capturee depuis un `%r` francais porte deja ses guillemets ;
    la repr-ifier une seconde fois rendrait `"\'inconnu\'"`.
    """
    def _remplace(trouve: "_re_module.Match[str]") -> str:
        if trouve.group(4) == "r":
            return "%" + trouve.group(1) + trouve.group(2) + (
                "." + trouve.group(3) if trouve.group(3) else "") + "s"
        return trouve.group(0)

    sortie: list[str] = []
    index = 0
    while index < len(format_en):
        if format_en[index] == "%":
            if format_en[index:index + 2] == "%%":
                sortie.append("%%")
                index += 2
                continue
            trouve = _SPEC.match(format_en, index)
            if trouve is not None:
                sortie.append(_remplace(trouve))
                index = trouve.end()
                continue
        sortie.append(format_en[index])
        index += 1
    return "".join(sortie)


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

    # Les BLANCS d encadrement sont mis de cote, puis remis. Sans cela,
    # `"\nempreinte engagee : %s"` ne se trouvait ni par recherche exacte
    # -- la clef n a pas le `\n` -- ni par motif, puisque les motifs sont
    # ancres `\A...\Z`. Et on ne peut pas renoncer a cet ancrage : c est
    # lui qui empeche un format court de mordre dans un format long.
    noyau = texte.strip()
    if noyau != texte:
        coupe = len(texte) - len(texte.lstrip())
        tete = texte[:coupe]
        queue = texte[len(texte.rstrip()):]
        return tete + traduire(noyau, langue) + queue

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
                prets.append(int(valeur.strip()))
                continue
            if marque == "g":
                prets.append(float(valeur.strip()))
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

    # Meme raison que dans `traduire` : un format ecrit
    # `"\nBILAN : %d PASS..."` ne se trouve pas sous la clef sans `\n`.
    noyau = format_fr.strip()
    if noyau != format_fr:
        coupe = len(format_fr) - len(format_fr.lstrip())
        tete = format_fr[:coupe]
        queue = format_fr[len(format_fr.rstrip()):]
        return tete + traduire_format(noyau, langue) + queue

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


def devrait_changer(texte: str, langue: str) -> bool:
    """Le catalogue promet-il une traduction DIFFERENTE pour `texte` ?

    A distinguer soigneusement de `couvert`, qui dit seulement que la
    chaine est connue. Certaines entrees s ecrivent pareil dans les deux
    langues -- << manifest.json present >> -- et pour celles-la la reponse
    est non, legitimement.

    Sert au controle par paire : si le francais et l anglais sortent
    IDENTIQUES alors que cette fonction rend `True`, la traduction n a pas
    eu lieu. C est ce controle, et non `residu`, qui attrape un outil dont
    l `import i18n` a echoue et dont le repli silencieux a pris le relais.
    """
    if langue == FR or not texte.strip():
        return False
    return traduire(texte, langue) != texte


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

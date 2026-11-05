# -*- coding: utf-8 -*-
"""Fabrique une archive Evidence de test, et son corpus d entree.

    python tests/make_fixture.py <repertoire_de_sortie>

POURQUOI CE GENERATEUR EXISTE
-----------------------------

L integration continue a besoin d une archive sur laquelle lancer les
suites. Les archives de demonstration ne peuvent pas servir, et le constat
qui l etablit vaut d etre ecrit :

l archive GROUNDED-S1 porte `dataset_id: medmcqa-single`, trente `item_id`
reels, et un membre `reference_evaluations.jsonl` qui croise
`extracted_answer` et `status`. Pour les treize observations au statut
`correct`, l etiquette de reference de treize items MedMCQA est donc
EXACTEMENT reconstituable. C est precisement la raison pour laquelle ce
membre avait ete exclu de l archive de demonstration MED. La publier dans
le depot aurait divulgue ces etiquettes.

Cette archive-ci n a donc **aucun lien avec un jeu de donnees reel** :
`dataset_id` vaut `ci-fixture`, les identifiants d items sont inventes, et
les reponses disent elles-memes ce qu elles sont. Croiser son
`extracted_answer` et son `status` ne revele rien, parce qu il n y a rien
derriere.

DETERMINISME
------------

Horodatages figes, `ZIP_STORED`, membres tries, `date_time` constant : deux
executions rendent la MEME archive a l octet. Une empreinte instable
ferait echouer la CI pour une raison qui n est pas un defaut du produit.

CE QUE LA FIXTURE COUVRE
------------------------

Les suites exigent, chacune, des proprietes precises : un `rapport.md`
portant une garde de regime, un `observations.csv` a fins de ligne CRLF, au
moins un signal `null`, des enregistrements de provenance de rejeu avec un
corpus d entree resoluble. Tout cela est produit ici -- y compris le
corpus, pour que `--corpus` et le mode strict soient eprouvables.

Bibliotheque standard seule.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

SCHEMA = "station.export.campagne/2"

#: Tout est fige : voir la section DETERMINISME.
INSTANT = "2026-01-01T00:00:00Z"
DATE_ZIP = (2026, 1, 1, 0, 0, 0)
COMMIT = "0" * 40
CONFIG_SHA = "1" * 64

#: Quatre observations, choisies pour couvrir les quatre etats de mesure.
#: `semantic_instability_score` est nul partout : la suite de falsification
#: exige au moins un signal `null` pour pouvoir l alterer.
OBSERVATIONS = [
    {"suffixe": "a", "statut": "measured",     "signaux": 4, "evaluation": "correct"},
    {"suffixe": "b", "statut": "measured",     "signaux": 4, "evaluation": "incorrect"},
    {"suffixe": "c", "statut": "degraded",     "signaux": 2, "evaluation": "unparseable"},
    {"suffixe": "d", "statut": "not_measured", "signaux": 0, "evaluation": "abstention"},
]

SIGNAUX = ("coherence_score", "semantic_risk", "stability_score",
           "factual_hallucination_score", "semantic_instability_score")

REPONSE = (
    "Reponse fabriquee pour la fixture d integration continue. Elle "
    "n observe aucun operateur, ne porte aucun raisonnement, et n atteste "
    "rien. Son seul role est de donner a la chaine un texte de longueur "
    "plausible. Choix : {lettre}."
)

GARDE_SYNTHETIC = (
    "Regime d'execution `synthetic` : ces reponses ont ete fabriquees pour "
    "le banc et n'observent aucun operateur reel. `model_served_attestation` "
    "y vaut l'attestation de l'enregistrement rejoue, pas celle d'un "
    "fournisseur."
)


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def jcs(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def construire(sortie: Path) -> tuple[Path, Path]:
    sortie.mkdir(parents=True, exist_ok=True)
    corpus = sortie / "corpus"
    (corpus / "responses").mkdir(parents=True, exist_ok=True)

    observations, mesures, evaluations, provenances = [], [], [], []
    lignes_csv = ["observation_id;provider;model_requested;execution_status;latency_ms"]
    entrees_corpus = []
    precedent = None

    for index, modele in enumerate(OBSERVATIONS):
        lettre = "ABCD"[index]
        texte = REPONSE.format(lettre=lettre)
        identifiant = "obs-" + sha256(("fixture-%s" % modele["suffixe"]).encode())

        # --- l enregistrement d entree, dans le corpus ---------------------
        nom_enregistrement = "responses/fixture-%s.json" % modele["suffixe"]
        enregistrement = {
            "provider": "synthetic:ci-fixture",
            "model_requested": "ci-fixture-v1",
            "model_served": "ci-fixture-v1",
            "model_served_attestation": "provider_attested",
            "sent_at": INSTANT,
            "received_at": INSTANT,
            "latency_ms": 100 + index,
            "response_text": texte,
        }
        octets_enregistrement = json.dumps(
            enregistrement, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8") + b"\n"
        (corpus / nom_enregistrement).write_bytes(octets_enregistrement)
        entrees_corpus.append({"recording": "fixture-%s.json" % modele["suffixe"]})

        # --- l observation -------------------------------------------------
        charge = {
            "campaign_id": "camp-ci-fixture",
            "cost": None,
            # AUCUN jeu de donnees reel : voir la docstring du module.
            "dataset_id": "ci-fixture",
            "dataset_version": "v1",
            "error": None,
            "execution_status": "ok",
            "finish_reason": "stop",
            "flow_type": "single",
            "item_id": "fixture-item-%s" % modele["suffixe"],
            "latency_ms": 100 + index,
            "model_requested": "ci-fixture-v1",
            "model_served": "ci-fixture-v1",
            "model_served_attestation": "provider_attested",
            "observation_id": identifiant,
            "pack": "ci",
            "params_effective": {"temperature": "0"},
            "params_sent": {"temperature": "0"},
            "prompt_sha256": sha256(("prompt-%s" % modele["suffixe"]).encode()),
            "prompt_version": "fixture-v1",
            "provider": "synthetic:ci-fixture",
            "received_at": INSTANT,
            "repetition_index": 0,
            "request_sha256": sha256(("request-%s" % modele["suffixe"]).encode()),
            "response_length": len(texte),
            "response_sha256": sha256(texte.encode("utf-8")),
            "response_text": texte,
            "run_id": "run-ci-fixture",
            "sent_at": INSTANT,
            "slot": index,
            "system_fingerprint": None,
            "tokens_input": 10,
            "tokens_output": 20,
        }
        integrite = {
            "code_commit": COMMIT,
            "comparability_key": "gen:v1:" + sha256(b"fixture"),
            "config_snapshot_sha256": CONFIG_SHA,
            "prev_record_sha256": precedent,
            "record_id": identifiant,
            "recorded_at": INSTANT,
        }
        enregistre = {"payload": charge, "integrity": integrite, "sequence": index + 1}
        integrite["record_sha256"] = sha256(jcs({"payload": charge, "integrity": {
            k: v for k, v in integrite.items() if k != "record_sha256"}}))
        precedent = integrite["record_sha256"]
        observations.append(enregistre)

        # Le CSV est a fins de ligne CRLF : la suite de falsification le
        # decoupe sur `\r\n` pour y injecter une formule.
        lignes_csv.append("%s;synthetic:ci-fixture;ci-fixture-v1;ok;%d"
                          % (identifiant, 100 + index))

        # --- la mesure -----------------------------------------------------
        mesures_signaux = {s: None for s in SIGNAUX}
        for nom in SIGNAUX[: modele["signaux"]]:
            mesures_signaux[nom] = 0.5
        mesures.append({"payload": {
            "checks_emitted": 3,
            "measured_at": INSTANT,
            "measured_signals": list(SIGNAUX[: modele["signaux"]]),
            "measurement_coverage": modele["signaux"] / 4,
            "measurement_id": "mes-" + identifiant,
            "measurement_reason": "initiale",
            "measurement_version": "3.3.1",
            "neomundi_measurement_id": None,
            "observation_id": identifiant,
            "reason": None,
            "signals": mesures_signaux,
            "status": modele["statut"],
        }, "integrity": {"record_id": "mes-" + identifiant, "recorded_at": INSTANT},
            "sequence": index + 1})

        # --- l evaluation de reference -------------------------------------
        # Inoffensive ici : `dataset_id` est `ci-fixture`, donc croiser
        # `extracted_answer` et `status` ne revele aucune etiquette reelle.
        evaluations.append({"payload": {
            "evaluated_at": INSTANT,
            "evaluation_id": "eval-" + identifiant,
            "evaluator_version": "ci-fixture-eval-v1",
            "extracted_answer": lettre if modele["evaluation"] != "abstention" else None,
            "observation_id": identifiant,
            "reference_sha256": sha256(("ref-%s" % modele["suffixe"]).encode()),
            "status": modele["evaluation"],
        }, "integrity": {"record_id": "eval-" + identifiant, "recorded_at": INSTANT},
            "sequence": index + 1})

        # --- la provenance de rejeu ----------------------------------------
        provenances.append({"payload": {
            "bundle_sha256": None,  # rempli plus bas, une fois le corpus fige
            "observation_id": identifiant,
            "origin": "ci-fixture",
            "provenance_id": "prov-" + identifiant,
            "provenance_version": "1",
            "provider": "synthetic:ci-fixture",
            "recorded_attestation": "provider_attested",
            "recording_path": nom_enregistrement,
            "recording_sha256": sha256(octets_enregistrement),
        }, "integrity": {"record_id": "prov-" + identifiant, "recorded_at": INSTANT},
            "sequence": index + 1})

    # --- le manifeste du corpus, et son empreinte de paquet ----------------
    # Les quatre champs que `verify.py` reinjecte dans l empreinte de paquet
    # -- bundle_id, regime, origin, recordings -- doivent etre portes ici,
    # sinon le controle `bundle_sha256 re-derive` echoue sur une fixture
    # pourtant saine. C est ce qui est arrive au premier essai.
    manifeste_corpus = {"bundle_id": "ci-fixture", "regime": "synthetic",
                        "origin": "ci-fixture", "entries": entrees_corpus,
                        "frozen_at": INSTANT}
    # LF EXPLICITE, et jamais `write_text` : sous Windows il traduit `\n`
    # en `\r\n`, et la MEME archive fabriquee sur deux systemes n aurait
    # pas la meme empreinte. Les octets d un corpus font partie de la
    # chaine : leurs empreintes sont dans `replay_provenance`.
    (corpus / "manifest.json").write_bytes(
        (json.dumps(manifeste_corpus, ensure_ascii=False, indent=2, sort_keys=True)
         + "\n").encode("utf-8"))
    recs = sorted(
        ({"path": "responses/" + e["recording"],
          "sha256": sha256((corpus / "responses" / e["recording"]).read_bytes())}
         for e in entrees_corpus),
        key=lambda r: r["path"],
    )
    bundle = sha256(jcs({
        "bundle_id": manifeste_corpus["bundle_id"],
        "regime": manifeste_corpus["regime"],
        "origin": manifeste_corpus["origin"],
        "recordings": recs,
    }))
    for p in provenances:
        p["payload"]["bundle_sha256"] = bundle

    # --- les membres de l archive ------------------------------------------
    membres: dict[str, bytes] = {
        "observations.jsonl": b"".join(jcs(o) + b"\n" for o in observations),
        "measurements.jsonl": b"".join(jcs(m) + b"\n" for m in mesures),
        "reference_evaluations.jsonl": b"".join(jcs(e) + b"\n" for e in evaluations),
        "replay_provenance.jsonl": b"".join(jcs(p) + b"\n" for p in provenances),
        "observations.csv": ("\r\n".join(lignes_csv) + "\r\n").encode("utf-8"),
    }

    nuls = {s: sum(1 for m in mesures if m["payload"]["signals"][s] is None)
            for s in SIGNAUX}
    manifeste = {
        "absences": {"observations_sans_evaluation": [], "observations_sans_mesure": []},
        "campaign_id": "camp-ci-fixture",
        "campaign_sha256": sha256(b"camp-ci-fixture"),
        "confidentialite": "aucune donnee reelle : fixture d integration continue",
        "csv": {"separateur": ";", "fins_de_ligne": "CRLF"},
        "decomptes": {
            "evaluations": len(evaluations),
            "mesures": len(mesures),
            "observations": len(observations),
            "provenances_de_rejeu": len(provenances),
            "runs": 1,
        },
        "diffusion": "test",
        "evaluations_de_reference": {"evaluateur": "ci-fixture-eval-v1"},
        "exporte_le": INSTANT,
        "fichiers": [
            "observations.csv", "observations.jsonl", "measurements.jsonl",
            "reference_evaluations.jsonl", "replay_provenance.jsonl",
            "manifest.json", "rapport.md", "checksums.sha256",
        ],
        "gardes_de_lecture": [GARDE_SYNTHETIC],
        "jsonl": {"encodage": "utf-8"},
        "limites": [
            "Un cout `null` signifie non etabli, jamais zero.",
            "Un signal `null` signifie non mesure. Aucun signal absent n est "
            "remplace par zero.",
            "Archive de FIXTURE : aucune donnee reelle, aucun operateur observe.",
        ],
        "mesures": {
            "identifiant_de_mesure_api_absent": len(mesures),
            "raisons_de_mesure": {"initiale": len(mesures)},
            "signaux_nuls": nuls,
            "signaux_values": {s: len(mesures) - nuls[s] for s in SIGNAUX},
            "statuts": {m["payload"]["status"]: sum(
                1 for x in mesures if x["payload"]["status"] == m["payload"]["status"])
                for m in mesures},
            "total": len(mesures),
            "versions_de_mesure": ["3.3.1"],
        },
        "regimes_d_execution": ["synthetic"],
        "registre": {"chaine_verifiee": True, "empreinte_de_tete": precedent,
                     "enregistrements": len(observations), "nom": "ledger.jsonl"},
        "runs": [{"run_id": "run-ci-fixture"}],
        "schema": SCHEMA,
    }
    membres["manifest.json"] = json.dumps(
        manifeste, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"

    membres["rapport.md"] = ("\n".join([
        "# Campagne camp-ci-fixture -- FIXTURE",
        "",
        "Archive fabriquee pour l integration continue. **Aucune donnee reelle.**",
        "",
        "## Gardes de lecture",
        "",
        GARDE_SYNTHETIC,
        "",
        "## Limites",
        "",
        "- Un signal `null` signifie non mesure, jamais zero.",
        "- Aucun operateur reel n a ete observe.",
        "",
    ])).encode("utf-8")

    couverts = sorted(n for n in membres if n != "checksums.sha256")
    membres["checksums.sha256"] = "".join(
        "%s  %s\n" % (sha256(membres[n]), n) for n in couverts).encode("utf-8")

    archive = sortie / "NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as z:
        for nom in sorted(membres):
            z.writestr(zipfile.ZipInfo(nom, date_time=DATE_ZIP), membres[nom])

    # --- de quoi eprouver la LIAISON ---------------------------------------
    # La suite de liaison a besoin d un repertoire d artefacts a part : le
    # corpus porte deja son propre `manifest.json`, et `test_binding.py`
    # cherche le manifeste de LIAISON sous ce nom. Les deux ne peuvent pas
    # cohabiter dans le meme repertoire.
    liaison = sortie / "binding"
    (liaison / "responses").mkdir(parents=True, exist_ok=True)
    premiere = observations[0]["payload"]
    (liaison / "response.txt").write_bytes(premiere["response_text"].encode("utf-8"))
    nom_premier = provenances[0]["payload"]["recording_path"]
    (liaison / nom_premier).write_bytes((corpus / nom_premier).read_bytes())

    # --- un descripteur, pour que la CI n ait rien a deviner ---------------
    (sortie / "fixture.json").write_bytes(
        json.dumps(
            {
                "archive": archive.name,
                "archive_sha256": sha256(archive.read_bytes()),
                "corpus": "corpus",
                "binding": "binding",
                "first_observation_id": premiere["observation_id"],
                "first_recording_path": nom_premier,
                "attendu": {
                    "verify_avec_corpus": "BILAN : 19 PASS, 0 FAIL, 2 NOT TESTED",
                    "verify_sans_corpus": "BILAN : 17 PASS, 0 FAIL, 3 NOT TESTED",
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        .encode("utf-8") + b"\n"
    )
    return archive, corpus


def main() -> int:
    if len(sys.argv) < 2:
        print("emploi : python tests/make_fixture.py <repertoire_de_sortie>")
        return 2
    archive, corpus = construire(Path(sys.argv[1]).resolve())
    print("archive : %s" % archive)
    print("  empreinte : %s" % sha256(archive.read_bytes()))
    print("  taille    : %d octets" % archive.stat().st_size)
    print("corpus  : %s (%d fichiers)" % (corpus, sum(1 for _ in corpus.rglob("*") if _.is_file())))
    print("liaison : %s" % (archive.parent / "binding"))
    print("descripteur : %s" % (archive.parent / "fixture.json"))
    print()
    print("Aucune donnee reelle : `dataset_id` vaut `ci-fixture`, les items sont")
    print("inventes, et croiser `extracted_answer` et `status` ne revele rien.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

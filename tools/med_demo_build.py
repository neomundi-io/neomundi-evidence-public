# -*- coding: utf-8 -*-
"""Construit l'archive de demonstration MED depuis les registres GELES.

Emploi :  python tools/med_demo_build.py <sortie.zip> <registre.jsonl> [...]

BIBLIOTHEQUE STANDARD SEULE. Les registres sont LUS, jamais ecrits. Aucune
empreinte existante n'est recalculee ni modifiee : les enregistrements sont
recopies en OCTETS D'ORIGINE, ligne du journal par ligne du journal.

## Pourquoi un outil separe, et non l'exporteur de l'instrument

L'exporteur de campagne de l'instrument produit huit membres, dont
`reference_evaluations.jsonl`. Pour le corpus MED, ce membre ne peut pas etre
publie : voir EXCLUSIONS ci-dessous. Retirer un membre d'une archive deja
produite obligerait a reecrire son manifeste et ses sommes a la main, ce qui
ferait d'une archive attestee un fichier retouche.

Cet outil produit donc un artefact DERIVE, sous son propre schema, qui dit
lui-meme ce qu'il contient et ce qu'il a ecarte. L'archive de campagne
complete, elle, reste disponible en prive et n'est pas modifiee.

## EXCLUSIONS, et leur raison

**Les evaluations de reference sont ecartees.** Elles portent le couple
`status` + `extracted_answer` : lorsqu'une reponse est `correct`, la lettre
extraite EST l'etiquette de reference du jeu de donnees. Les publier sur 208
mesures reconstituerait une partie des etiquettes de MedMCQA, dont les
conditions de redistribution ne sont pas levees.

**Le texte des questions, les choix et les etiquettes de reference ne sont
nulle part dans cette archive.** Le registre n'en contient de toute facon que
l'empreinte (`prompt_sha256`). L'`item_id` publie est l'identifiant du jeu de
donnees amont : un auditeur resout la question a la source, chez l'editeur du
jeu de donnees, et non chez nous.

## Ce que l'archive NE demontre PAS

Une mesure n'est pas une validation medicale de la reponse. Aucun signal publie
ici ne dit qu'une reponse est cliniquement juste.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

SCHEMA = "neomundi.evidence.med-demo/1"
OBSERVATIONS = "observations.jsonl"
MESURES = "measurements.jsonl"
MANIFESTE = "manifest.json"
RAPPORT = "report.md"
CHECKSUMS = "checksums.sha256"
MEMBRES = (OBSERVATIONS, MESURES, MANIFESTE, RAPPORT)

#: Horodatage fige des membres du ZIP : l'archive est reproductible a l'octet.
DATE_ZIP = (2026, 11, 5, 0, 0, 0)

JEU_DE_DONNEES = {
    "name": "MedMCQA",
    "upstream_repository": "openlifescienceai/medmcqa",
    "url": "https://huggingface.co/datasets/openlifescienceai/medmcqa",
    "revision": "91c6572c454088bf71b679ad90aa8dffcd0d5868",
    "licence_tag": "apache-2.0",
    "licensing_section_of_the_card": "[Needs More Information]",
    "collection_declared": (
        "Historical Exam questions from official websites - AIIMS & NEET PG (1991-present), "
        "and open websites and books"
    ),
    "citation_requested": (
        "Pal, Umapathi & Sankarasubbu, 2022 — MedMCQA: A Large-scale Multi-Subject "
        "Multi-Choice Dataset for Medical domain Question Answering"
    ),
    "redistribution": (
        "NOT REDISTRIBUTED HERE. The dataset's YAML tag announces apache-2.0 while the "
        "Licensing Information section of its card was left as the empty template, and its "
        "content comes from third-party examinations. The uncertainty is unresolved: no "
        "question text, no choices and no reference label are published. Only the `item_id` "
        "values are, so that a question resolves at the source."
    ),
    "selection": (
        "300 rows read at the source, 202 kept by a single-answer filter; 98 set aside "
        "because declared as multiple-choice."
    ),
}

EXCLUSIONS = [
    {
        "excluded": "reference_evaluations.jsonl",
        "reason": (
            "the pair `status` + `extracted_answer` would reveal the dataset's reference "
            "label every time an answer is `correct`. Publishing that across the whole corpus "
            "would reconstruct part of the MedMCQA labels, whose redistribution conditions "
            "are unresolved."
        ),
        "consequence": (
            "this archive does not let anyone say whether an answer was correct in the "
            "dataset's sense. It lets anyone say what was asked, what answered, what was "
            "answered, and what was measured."
        ),
    },
    {
        "excluded": "question text, choices, reference labels",
        "reason": "same cause; and the ledger only ever kept their hash.",
        "consequence": "the published `item_id` resolves the question at the dataset publisher.",
    },
]

LIMITES = (
    "A measurement is NOT a medical validation of the answer. No signal published here "
    "establishes that an answer is clinically correct.",
    "A `model_served` of `null` means the provider did not attest which model actually "
    "served the request. The requested model is then the only thing established.",
    "A `cost` of `null` means not established, never zero.",
    "`latency_ms` is 0 on a failed observation: an aborted call leaves no duration behind. "
    "It is not a duration of zero milliseconds.",
    "The hashes in this archive attest its files. They attest neither origin nor time: "
    "`recorded_at` is supplied by the caller, and the ledger chain has no external anchoring.",
    "This tool does not recompute the ledgers' chaining: that is verified with the instrument "
    "that wrote it. The head hashes declared here are those of the freeze.",
    "This archive is a DERIVED artefact. The complete campaign archive, which carries the "
    "reference evaluations, stays private and is not modified.",
)


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def lire_registre(chemin: Path) -> tuple[list[bytes], list[bytes], str | None]:
    """Rend les lignes brutes des observations, des mesures, et l'empreinte de tete."""
    observations: list[bytes] = []
    mesures: list[bytes] = []
    tete: str | None = None
    with chemin.open("rb") as f:
        for ligne in f:
            brut = ligne.rstrip(b"\n")
            if not brut.strip():
                continue
            enregistrement = json.loads(brut)
            integrite = enregistrement.get("integrity", {})
            tete = integrite.get("record_sha256", tete)
            type_ = integrite.get("record_type")
            if type_ == "observation":
                observations.append(brut)
            elif type_ == "measurement":
                mesures.append(brut)
    return observations, mesures, tete


def charge(brut: bytes) -> dict[str, object]:
    valeur = json.loads(brut).get("payload")
    return valeur if isinstance(valeur, dict) else {}


def resume_par_campagne(observations: list[bytes], mesures: list[bytes]) -> list[dict[str, object]]:
    """Un bloc par campagne : modele demande, modele servi, attestation, decomptes."""
    par_campagne: dict[str, dict[str, object]] = {}
    mesures_par_observation = {charge(b).get("observation_id") for b in mesures}
    for brut in observations:
        p = charge(brut)
        c = str(p.get("campaign_id"))
        bloc = par_campagne.setdefault(
            c,
            {
                "campaign_id": c,
                "provider": p.get("provider"),
                "models_requested": set(),
                "models_served": set(),
                "attestations": collections.Counter(),
                "observations": 0,
                "mesurees": 0,
                "issues": collections.Counter(),
                "latences_ms": [],
            },
        )
        bloc["observations"] = int(bloc["observations"]) + 1
        bloc["models_requested"].add(p.get("model_requested"))  # type: ignore[union-attr]
        bloc["models_served"].add(p.get("model_served"))  # type: ignore[union-attr]
        bloc["attestations"][p.get("model_served_attestation")] += 1  # type: ignore[index]
        bloc["issues"][p.get("execution_status")] += 1  # type: ignore[index]
        if p.get("observation_id") in mesures_par_observation:
            bloc["mesurees"] = int(bloc["mesurees"]) + 1
        if p.get("execution_status") == "ok" and isinstance(p.get("latency_ms"), int):
            bloc["latences_ms"].append(p["latency_ms"])  # type: ignore[union-attr,index]

    sorties = []
    for bloc in sorted(par_campagne.values(), key=lambda b: str(b["campaign_id"])):
        latences = sorted(bloc.pop("latences_ms"))  # type: ignore[arg-type]
        sorties.append(
            {
                "campaign_id": bloc["campaign_id"],
                "provider": bloc["provider"],
                "model_requested": sorted(str(m) for m in bloc["models_requested"]),  # type: ignore[union-attr]
                "model_served": sorted(
                    ("null" if m is None else str(m)) for m in bloc["models_served"]  # type: ignore[union-attr]
                ),
                "attestations": dict(sorted(bloc["attestations"].items(), key=lambda kv: str(kv[0]))),  # type: ignore[union-attr]
                "observations": bloc["observations"],
                "observations_mesurees": bloc["mesurees"],
                "observations_sans_mesure": int(bloc["observations"]) - int(bloc["mesurees"]),
                "issues": dict(sorted(bloc["issues"].items(), key=lambda kv: str(kv[0]))),  # type: ignore[union-attr]
                "latence_ms_mediane": latences[len(latences) // 2] if latences else None,
            }
        )
    return sorties


def resume_mesures(mesures: list[bytes]) -> dict[str, object]:
    statuts: collections.Counter[str] = collections.Counter()
    versions: set[str] = set()
    values: collections.Counter[str] = collections.Counter()
    nuls: collections.Counter[str] = collections.Counter()
    correles = 0
    for brut in mesures:
        p = charge(brut)
        statuts[str(p.get("status"))] += 1
        versions.add(str(p.get("measurement_version")))
        correles += p.get("neomundi_measurement_id") is not None
        for nom, valeur in (p.get("signals") or {}).items():  # type: ignore[union-attr]
            if valeur is None:
                nuls[nom] += 1
            else:
                values[nom] += 1
    return {
        "total": len(mesures),
        "statuts": dict(sorted(statuts.items())),
        "versions_de_mesure": sorted(versions),
        "signaux_values": dict(sorted(values.items())),
        "signaux_nuls": dict(sorted(nuls.items())),
        "correlees_a_une_mesure_de_production": correles,
    }


def exemple_travaille(observations: list[bytes], mesures: list[bytes]) -> dict[str, object] | None:
    """Une observation complete, avec sa mesure : la chaine de bout en bout."""
    par_observation = {charge(b).get("observation_id"): charge(b) for b in mesures}
    for brut in observations:
        p = charge(brut)
        identifiant = p.get("observation_id")
        if identifiant not in par_observation:
            continue
        m = par_observation[identifiant]
        return {
            "observation_id": identifiant,
            "item_id": p.get("item_id"),
            "dataset": "%s / %s" % (p.get("dataset_id"), p.get("dataset_version")),
            "provider": p.get("provider"),
            "model_requested": p.get("model_requested"),
            "model_served": p.get("model_served"),
            "model_served_attestation": p.get("model_served_attestation"),
            "prompt_version": p.get("prompt_version"),
            "prompt_sha256": p.get("prompt_sha256"),
            "sent_at": p.get("sent_at"),
            "latency_ms": p.get("latency_ms"),
            "tokens_input": p.get("tokens_input"),
            "tokens_output": p.get("tokens_output"),
            "response_length": p.get("response_length"),
            "response_sha256": p.get("response_sha256"),
            "response_text": p.get("response_text"),
            "measurement_id": m.get("measurement_id"),
            "measurement_version": m.get("measurement_version"),
            "measurement_status": m.get("status"),
            "neomundi_measurement_id": m.get("neomundi_measurement_id"),
            "signals": m.get("signals"),
            "measured_signals": m.get("measured_signals"),
            "measurement_coverage": m.get("measurement_coverage"),
        }
    return None


def rendre_rapport(manifeste: dict[str, object], exemple: dict[str, object] | None) -> str:
    lignes = [
        "# NeoMundi Evidence — MED demonstration",
        "",
        "Derived artefact. **A measurement is not a medical validation of the answer.**",
        "",
        "## Scope",
        "",
        "- schema : `%s`" % manifeste["schema"],
        "- built on : %s" % manifeste["construit_le"],
        "- ledgers read : %d" % len(manifeste["registres"]),  # type: ignore[arg-type]
        "- observations : %d" % manifeste["decomptes"]["observations"],  # type: ignore[index]
        "- measurements : %d" % manifeste["decomptes"]["mesures"],  # type: ignore[index]
        "",
        "## Dataset",
        "",
        "- name : %s (`%s`)" % (JEU_DE_DONNEES["name"], JEU_DE_DONNEES["upstream_repository"]),
        "- revision : `%s`" % JEU_DE_DONNEES["revision"],
        "- licence tag : `%s` — licensing section of the card : `%s`"
        % (JEU_DE_DONNEES["licence_tag"], JEU_DE_DONNEES["licensing_section_of_the_card"]),
        "- selection : %s" % JEU_DE_DONNEES["selection"],
        "- citation requested : %s" % JEU_DE_DONNEES["citation_requested"],
        "",
        "**%s**" % JEU_DE_DONNEES["redistribution"],
        "",
        "## Campaigns, models and providers",
        "",
        "| Campaign | Provider | Model requested | Model served | Attestation | Obs. | Measured |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in manifeste["campagnes"]:  # type: ignore[union-attr]
        lignes.append(
            "| `%s` | `%s` | `%s` | `%s` | %s | %d | %d |"
            % (
                c["campaign_id"],
                c["provider"],
                ", ".join(c["model_requested"]),
                ", ".join(c["model_served"]),
                ", ".join("%s=%d" % (k, v) for k, v in c["attestations"].items()),
                c["observations"],
                c["observations_mesurees"],
            )
        )
    mes = manifeste["mesures"]
    lignes += [
        "",
        "> A `model_served` of `null` means the provider did **not** attest which model actually",
        "> served the request. The requested model is then the only thing established.",
        "",
        "## Measurements",
        "",
        "- version(s) : %s" % ", ".join(mes["measurement_version"] if False else mes["versions_de_mesure"]),  # type: ignore[index]
        "- states : %s" % ", ".join("%s=%d" % (k, v) for k, v in mes["statuts"].items()),  # type: ignore[index]
        "- correlated to a production measurement identifier : %d of %d"
        % (mes["correlees_a_une_mesure_de_production"], mes["total"]),  # type: ignore[index]
        "",
        "| Signal | Measured | `null` (not measured) |",
        "|---|---|---|",
    ]
    noms = sorted(set(mes["signaux_values"]) | set(mes["signaux_nuls"]))  # type: ignore[index]
    for nom in noms:
        lignes.append(
            "| %s | %d | %d |"
            % (nom, mes["signaux_values"].get(nom, 0), mes["signaux_nuls"].get(nom, 0))  # type: ignore[index,union-attr]
        )

    lignes += ["", "## What was excluded, and why", ""]
    for e in EXCLUSIONS:  # type: ignore[union-attr]
        lignes += [
            "**%s**" % e["excluded"],
            "",
            "- reason : %s" % e["reason"],
            "- consequence : %s" % e["consequence"],
            "",
        ]

    if exemple is not None:
        lignes += [
            "## One worked example — the whole chain",
            "",
            "| | |",
            "|---|---|",
            "| dataset item | `%s` — resolve it at the dataset source, not here |" % exemple["item_id"],
            "| dataset | `%s` |" % exemple["dataset"],
            "| provider | `%s` |" % exemple["provider"],
            "| model requested | `%s` |" % exemple["model_requested"],
            "| model served | `%s` (%s) |"
            % (exemple["model_served"], exemple["model_served_attestation"]),
            "| prompt template | `%s` |" % exemple["prompt_version"],
            "| prompt hash | `%s` |" % exemple["prompt_sha256"],
            "| sent at | %s |" % exemple["sent_at"],
            "| latency | %s ms |" % exemple["latency_ms"],
            "| tokens in / out | %s / %s |" % (exemple["tokens_input"], exemple["tokens_output"]),
            "| answer length | %s characters |" % exemple["response_length"],
            "| answer hash | `%s` |" % exemple["response_sha256"],
            "| observation | `%s` |" % exemple["observation_id"],
            "| measurement | `%s`, version `%s`, state `%s` |"
            % (
                exemple["measurement_id"],
                exemple["measurement_version"],
                exemple["measurement_status"],
            ),
            "| production measurement id | `%s` |" % exemple["neomundi_measurement_id"],
            "| coverage | %s |" % exemple["measurement_coverage"],
            "",
            "### Signals actually measured on this answer",
            "",
            "| Signal | Value |",
            "|---|---|",
        ]
        for nom, valeur in sorted((exemple["signals"] or {}).items()):  # type: ignore[union-attr]
            lignes.append("| %s | %s |" % (nom, "null" if valeur is None else valeur))
        lignes += [
            "",
            "**None of these values says the answer is clinically correct.** They describe",
            "properties of the text that was produced, measured by the instrument at the stated",
            "version.",
            "",
            "### The answer that was recorded",
            "",
            "```",
            str(exemple["response_text"] or "").strip(),
            "```",
            "",
        ]

    lignes += ["## Verification", "", "    sha256sum -c checksums.sha256", "", "## Limits", ""]
    lignes += ["- %s" % limite for limite in LIMITES]
    return "\n".join(lignes) + "\n"


def construire(sortie: Path, registres: list[Path], construit_le: str) -> dict[str, object]:
    if sortie.exists():
        message = "%s existe deja : une archive n'est jamais ecrasee" % sortie
        raise SystemExit(message)

    observations: list[bytes] = []
    mesures: list[bytes] = []
    blocs_registres = []
    for chemin in registres:
        obs, mes, tete = lire_registre(chemin)
        observations += obs
        mesures += mes
        blocs_registres.append(
            {
                "nom": chemin.name,
                "repertoire": chemin.parent.name,
                "observations": len(obs),
                "mesures": len(mes),
                "empreinte_de_tete": tete,
                "chaine_verifiee_par_cet_outil": False,
            }
        )

    manifeste: dict[str, object] = {
        "schema": SCHEMA,
        "construit_le": construit_le,
        "nature": (
            "DERIVED artefact, built read-only from the frozen ledgers. Records are copied "
            "in their original bytes."
        ),
        "jeu_de_donnees": JEU_DE_DONNEES,
        "registres": blocs_registres,
        "decomptes": {"observations": len(observations), "mesures": len(mesures)},
        "campagnes": resume_par_campagne(observations, mesures),
        "mesures": resume_mesures(mesures),
        "exclusions": EXCLUSIONS,
        "fichiers": [*MEMBRES, CHECKSUMS],
        "join_key": "`observation_id`, present on both JSONL files.",
        "limites": list(LIMITES),
    }

    exemple = exemple_travaille(observations, mesures)
    contenu = {
        OBSERVATIONS: b"".join(b + b"\n" for b in observations),
        MESURES: b"".join(b + b"\n" for b in mesures),
        MANIFESTE: (json.dumps(manifeste, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
        RAPPORT: rendre_rapport(manifeste, exemple).encode("utf-8"),
    }
    contenu[CHECKSUMS] = "".join(
        "%s  %s\n" % (sha256(contenu[nom]), nom) for nom in MEMBRES
    ).encode("utf-8")

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for nom in (*MEMBRES, CHECKSUMS):
            info = zipfile.ZipInfo(nom, date_time=DATE_ZIP)
            info.external_attr = 0o644 << 16
            archive.writestr(info, contenu[nom])
    octets = tampon.getvalue()

    # Relecture : l'archive ecrite est confrontee a ce qu'on voulait ecrire.
    with zipfile.ZipFile(io.BytesIO(octets)) as archive:
        for nom, attendu in contenu.items():
            if archive.read(nom) != attendu:
                raise SystemExit("archive incoherente apres ecriture : %s" % nom)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    with sortie.open("xb") as fichier:
        fichier.write(octets)
    return {"archive_sha256": sha256(octets), "octets": len(octets), "manifeste": manifeste}


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Construit l'archive de demonstration MED depuis des registres geles."
    )
    analyseur.add_argument("sortie", type=Path)
    analyseur.add_argument("registres", type=Path, nargs="+")
    analyseur.add_argument(
        "--construit-le",
        default="2026-11-05T00:00:00Z",
        help="horodatage inscrit au manifeste ; fixe par defaut pour que l'archive soit reproductible",
    )
    arguments = analyseur.parse_args()

    empreintes_avant = {p: sha256(p.read_bytes()) for p in arguments.registres}
    resultat = construire(arguments.sortie, arguments.registres, arguments.construit_le)
    bouges = [str(p) for p, h in empreintes_avant.items() if sha256(p.read_bytes()) != h]

    print("archive        : %s" % arguments.sortie)
    print("archive_sha256 : %s" % resultat["archive_sha256"])
    print("octets         : %d" % resultat["octets"])
    m = resultat["manifeste"]
    print("observations   : %d" % m["decomptes"]["observations"])  # type: ignore[index]
    print("mesures        : %d" % m["decomptes"]["mesures"])  # type: ignore[index]
    print("campagnes      : %d" % len(m["campagnes"]))  # type: ignore[arg-type]
    print("registres lus  : %d, inchanges : %s" % (len(arguments.registres), "oui" if not bouges else bouges))
    return 1 if bouges else 0


if __name__ == "__main__":
    sys.exit(main())

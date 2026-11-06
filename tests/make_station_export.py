# -*- coding: utf-8 -*-
"""Fabrique un export Station `/3`, valide ou ADVERSE, pour eprouver R-6.

    python tests/make_station_export.py <sortie.zip> [--profil <nom>]

POURQUOI UN GENERATEUR DISTINCT DE `make_fixture.py`

`make_fixture.py` produit l archive dont l empreinte est SIGNEE, horodatee et
liee : son profil `v1` reproduit `e31e12bb...` octet pour octet, et le cas 1
de `tests/test_completude.py` echoue si cela cesse. Y ajouter un profil
toucherait la passe de chainage, les decomptes du manifeste et quatre lignes
de base. Un generateur a part ne touche rien de signe.

Celui-ci est petit a dessein : il produit juste ce qu il faut pour que
`adapters/provenance.py` ait quelque chose a lire, et il casse une propriete
a la fois.

LES PROFILS

  valide                        couverture complete, configuration documentee
  sans-couverture               un `/2` : aucun membre de couverture
  evaluateur-absent             couverture presente, `evaluators` a null
  version-evaluateur-inconnue   evaluateur nomme, sans version ni empreinte
  configuration-non-documentee  evaluateurs sans aucun champ de configuration
  empreinte-incoherente         une empreinte de `checksums.sha256` est fausse
  export-altere                 un membre a bouge APRES l ecriture des sommes
  execution-partielle           l API declare n avoir pas fini de mesurer
  signal-not-measured           un signal nul, avec son motif
  metadonnees-non-verifiables   des champs declares que rien ne permet de
                                confronter -- et c est le cas NORMAL, pas un
                                defaut : il doit ressortir DECLARE
  calcul-local-sans-config      un calcul local qui OMET les clefs de
                                configuration, au lieu de les porter a null.
                                C est la forme d un vrai export, et elle a
                                revele un defaut que ce generateur masquait
  configuration-nulle           les quatre clefs de configuration PRESENTES
                                et NULLES, sur des signaux qui ont pourtant
                                un modele. Symetrique du profil precedent :
                                la presence d une clef ne vaut pas sa valeur
  signal-sans-instrument        la mesure publie cinq valeurs, `evaluators`
                                n en nomme que quatre. Le membre EXISTE : ce
                                n est pas le silence d une API anterieure,
                                c est un export qui se contredit

Deterministe : aucune horloge, aucun alea. Bibliotheque standard seule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PROFILS = ("valide", "sans-couverture", "evaluateur-absent",
           "version-evaluateur-inconnue", "configuration-non-documentee",
           "empreinte-incoherente", "export-altere", "execution-partielle",
           "signal-not-measured", "metadonnees-non-verifiables",
           "calcul-local-sans-config", "configuration-nulle",
           "signal-sans-instrument")

SIGNAUX = ("stability_score", "coherence_score", "semantic_risk",
           "factual_hallucination_score", "semantic_instability_score")


def jcs(objet: object) -> bytes:
    return json.dumps(objet, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


def _evaluateurs(profil: str) -> dict | None:
    """Le bloc que l API sert par signal, et que la couverture conserve."""
    if profil == "evaluateur-absent":
        return None
    base: dict[str, dict] = {}
    for s in SIGNAUX:
        calcul_local = s == "stability_score"
        detail: dict[str, object] = {
            "evaluator": "evaluateur_de_demonstration.%s" % s,
            "model_used": None if calcul_local else "modele-de-demonstration",
            "status": "measured",
            "reason": None,
        }
        if profil == "calcul-local-sans-config" and calcul_local:
            # Les clefs sont OMISES, pas mises a null : c est la forme qu un
            # vrai export Station produit pour un calcul local, et elle doit
            # etre lue comme << correct >> et non comme << non configure >>.
            base[s] = {"evaluator": detail["evaluator"], "status": "measured",
                       "reason": None}
            continue
        if profil == "version-evaluateur-inconnue":
            # Nomme, et rien de plus : ni modele configure, ni empreinte.
            detail = {"evaluator": detail["evaluator"], "status": "measured",
                      "reason": None}
        elif profil != "configuration-non-documentee":
            detail.update({
                "model_configured": None if calcul_local else "modele-de-demonstration",
                "served_by": "primary",
                "attempts": 1,
                "latency_ms": 12.5,
                # Un calcul local n a ni moteur ni prompt : ses nuls sont
                # CORRECTS, et le rapport ne doit pas les lire comme un trou.
                "evaluator_runtime": None if calcul_local else "moteur-de-demonstration",
                "prompt_template_hash": None if calcul_local else "0" * 16,
                "inference_config_hash": None if calcul_local else "1" * 16,
                "config_fingerprint": None if calcul_local else "2" * 16,
            })
            if profil == "configuration-nulle":
                # PRESENTES et NULLES. Une configuration vide n est pas une
                # configuration, et le modele reste declare : c est ce qui
                # rend ce profil different de `configuration-non-documentee`,
                # ou les clefs sont absentes.
                for champ in ("evaluator_runtime", "prompt_template_hash",
                              "inference_config_hash", "config_fingerprint"):
                    detail[champ] = None
        base[s] = detail
    # Deux signaux partagent un meme appel : le dire, sinon un lecteur
    # compte deux instruments la ou il n y en a qu un.
    partage = "evaluateur_de_demonstration.juge_partage"
    base["factual_hallucination_score"]["evaluator"] = partage
    base["semantic_instability_score"]["evaluator"] = partage
    if profil == "signal-sans-instrument":
        # La mesure publie bien les cinq valeurs ; `evaluators` n en nomme
        # que quatre. Le membre existe et documente les autres, donc le
        # rapport ne peut pas mettre ce trou sur le compte d une API
        # anterieure.
        base.pop("semantic_risk", None)
    return base


def construire(cible: Path, profil: str = "valide") -> Path:
    if profil not in PROFILS:
        raise SystemExit("profil inconnu : %s (connus : %s)"
                         % (profil, ", ".join(PROFILS)))

    obs = {"observation_id": "obs-demo-1", "run_id": "run-demo",
           "campaign_id": "camp-demo", "pack": "demo", "flow_type": "single",
           "slot": "a", "repetition_index": 0,
           "sent_at": "2026-01-01T00:00:00Z", "received_at": "2026-01-01T00:00:01Z",
           "latency_ms": 1000, "provider": "fournisseur-de-demonstration",
           "model_requested": "modele-demo-v1", "model_served": "modele-demo-v1",
           "model_served_attestation": "declared", "params_sent": {"temperature": "0"},
           "params_effective": {"temperature": "0"}, "prompt_version": "p1",
           "prompt_sha256": "a" * 64, "request_sha256": "b" * 64,
           "response_sha256": "c" * 64, "execution_status": "ok"}

    nul = profil == "signal-not-measured"
    signaux = {s: (None if (nul and s == "coherence_score") else 0.5)
               for s in SIGNAUX}
    mesure = {"measurement_id": "mes-demo-1", "observation_id": "obs-demo-1",
              "measurement_version": "3.3.1", "measurement_reason": "initiale",
              "checks_emitted": 3, "status": "measured" if not nul else "degraded",
              "measured_at": "2026-01-01T00:00:02Z",
              "measured_signals": sorted(k for k, v in signaux.items() if v is not None),
              "signals": signaux,
              "measurement_coverage": 0.8 if nul else 1.0,
              "neomundi_measurement_id": None,
              "reason": ("coherence_score non mesure : evaluateur indisponible"
                         if nul else None)}

    partielle = profil == "execution-partielle"
    couverture = {"coverage_id": "cov-demo-1", "measurement_id": "mes-demo-1",
                  "observation_id": "obs-demo-1", "measurement_version": "3.3.1",
                  "coverage_version": "1",
                  "api_measurement_status": "partial" if partielle else "complete",
                  "checks_attempted": 5, "checks_succeeded": 2 if partielle else 5,
                  "failed_checks": ({"semantic_risk": "delai depasse"}
                                    if partielle else {}),
                  "degraded_g_inputs": ["semantic_risk"] if partielle else [],
                  "unmeasured_signals": ({"coherence_score": "evaluateur indisponible"}
                                         if nul else {}),
                  "evaluators": _evaluateurs(profil),
                  "reported_at": "2026-01-01T00:00:03Z"}

    def enveloppe(sequence: int, charge: dict) -> dict:
        return {"sequence": sequence, "payload": charge,
                "integrity": {"record_type": "x", "record_sha256": "0" * 64}}

    membres: dict[str, bytes] = {
        "observations.jsonl": jcs(enveloppe(1, obs)) + b"\n",
        "observations.csv": b"observation_id\nobs-demo-1\n",
        "measurements.jsonl": jcs(enveloppe(2, mesure)) + b"\n",
        "reference_evaluations.jsonl": b"",
        "replay_provenance.jsonl": b"",
        "rapport.md": b"# Export de demonstration\n\nObjet synthetique.\n",
    }
    avec_couverture = profil != "sans-couverture"
    if avec_couverture:
        membres["measurement_coverage.jsonl"] = jcs(enveloppe(3, couverture)) + b"\n"

    manifeste = {
        "schema": ("station.export.campagne/3" if avec_couverture
                   else "station.export.campagne/2"),
        "campaign_id": "camp-demo",
        "campaign_sha256": "d" * 64,
        "exporte_le": "2026-01-01T00:00:04Z",
        # Les clefs que `verify.py` confronte, membre par membre. Les
        # omettre faisait echouer DEUX controles sur tous les profils, et
        # masquait les defauts que les profils adverses ciblent.
        "decomptes": {"observations": 1, "mesures": 1,
                      "evaluations": 0, "provenances_de_rejeu": 0,
                      "couvertures": 1 if avec_couverture else 0},
        "limites": [
            "Objet synthetique, sans lien a un jeu de donnees reel.",
            "Les empreintes d entrees et de sorties sont declarees : leurs "
            "octets ne sont pas dans cet export.",
        ],
    }
    membres["manifest.json"] = (
        json.dumps(manifeste, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n").encode("utf-8")

    couverts = sorted(n for n in membres if n != "checksums.sha256")
    sommes = {n: sha256(membres[n]) for n in couverts}
    if profil == "empreinte-incoherente":
        # Le manifeste est intact, et UNE somme est fausse.
        bon = sommes["measurements.jsonl"]
        sommes["measurements.jsonl"] = ("0" if bon[0] != "0" else "1") + bon[1:]
    membres["checksums.sha256"] = "".join(
        "%s  %s\n" % (sommes[n], n) for n in couverts).encode("utf-8")
    if profil == "export-altere":
        # Les sommes sont justes, et un membre a bouge APRES. L inverse du
        # profil precedent, et indiscernable pour un verificateur.
        membres["measurements.jsonl"] = membres["measurements.jsonl"].replace(
            b'"checks_emitted":3', b'"checks_emitted":9')

    cible.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
        for nom in sorted(membres):
            # `create_system` epingle a 0 : sans cela la MEME commande rend
            # deux archives differentes selon le systeme -- defaut constate.
            e = zipfile.ZipInfo(nom, date_time=(2026, 1, 1, 0, 0, 0))
            e.create_system = 0
            e.external_attr = 0o644 << 16
            z.writestr(e, membres[nom])
    return cible


def main() -> int:
    a = argparse.ArgumentParser(
        description="Fabrique un export Station /3, valide ou adverse.")
    a.add_argument("sortie", type=Path)
    a.add_argument("--profil", default="valide", choices=PROFILS)
    arguments = a.parse_args()
    cible = construire(arguments.sortie, arguments.profil)
    print("export ecrit : %s" % cible)
    print("  profil   : %s" % arguments.profil)
    print("  sha256   : %s" % sha256(cible.read_bytes()))
    with zipfile.ZipFile(cible) as z:
        print("  membres  : %s" % ", ".join(sorted(z.namelist())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

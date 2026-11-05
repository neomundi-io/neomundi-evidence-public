#!/bin/sh
# NeoMundi Evidence V1 -- demonstration de cinq minutes.
#
#   sh demo_v1_5min.sh
#
# Cinq etapes : integrite, verification autonome, attestation Ed25519,
# horodatage au STATUT REEL, et reconciliation.
#
# TOUT est synthetique. L archive est fabriquee pour la demonstration, la
# cle de signature etait une cle de DEMONSTRATION ephemere et a ete
# detruite, et le recu externe est invente. Aucune donnee de pilote, aucun
# jeu de donnees reel.
#
# HORS LIGNE de bout en bout : la seule preuve d horodatage a ete obtenue
# une fois, et elle est livree avec le dossier.

set -eu
ICI="$(cd "$(dirname "$0")" && pwd)"
D="$ICI/examples/dossier-v1"
cd "$D"

titre() {
    printf '\n========================================================\n'
    printf '  %s\n' "$1"
    printf '========================================================\n\n'
}

pause() {
    printf '\n'
    if [ -t 0 ]; then printf '  -- Entree pour continuer --'; read -r _; printf '\n'; fi
}

# --------------------------------------------------------------------------
titre "Le dossier soumis a la revue"

printf 'Un dossier complet, entierement synthetique :\n\n'
printf '  %-46s %6s o\n' "NEOMUNDI_EVIDENCE_V1_DEMO.zip" "$(wc -c < NEOMUNDI_EVIDENCE_V1_DEMO.zip | tr -d ' ')"
printf '  %-46s %6s o   attestation Ed25519\n' "…zip.jws" "$(wc -c < NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws | tr -d ' ')"
printf '  %-46s %6s o   preuve OpenTimestamps\n' "…zip.jws.ots" "$(wc -c < NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots | tr -d ' ')"
printf '  %-46s %6s o   cles PUBLIQUES seulement\n' "trust-store.json" "$(wc -c < trust-store.json | tr -d ' ')"
printf '\nempreinte de l archive :\n  %s\n' "$(python - <<'PY'
import hashlib, pathlib
print(hashlib.sha256(pathlib.Path("NEOMUNDI_EVIDENCE_V1_DEMO.zip").read_bytes()).hexdigest())
PY
)"
pause

# --------------------------------------------------------------------------
titre "1 / 5  INTEGRITE -- 21 controles, trois etats qui ne se confondent pas"

python "$ICI/verify.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip --corpus corpus | tail -26
pause

titre "1b / 5  Un octet change DANS un membre, et le dossier est refuse"

python - <<'PY'
import pathlib, tempfile, zipfile
src = pathlib.Path("NEOMUNDI_EVIDENCE_V1_DEMO.zip")
with zipfile.ZipFile(src) as z:
    membres = {n: z.read(n) for n in z.namelist()}
# UN octet, dans la premiere observation. Les sommes de controle de
# l archive ne sont PAS refaites : c est ce que `verify.py` attrape.
avant = membres["observations.jsonl"]
membres["observations.jsonl"] = avant[:-2] + b" \n"
cible = pathlib.Path(tempfile.gettempdir()) / "altere.zip"
with zipfile.ZipFile(cible, "w", compression=zipfile.ZIP_STORED) as z:
    for nom in sorted(membres):
        z.writestr(zipfile.ZipInfo(nom, date_time=(2026, 1, 1, 0, 0, 0)), membres[nom])
print("  un octet change dans observations.jsonl -> %s" % cible)
PY
printf '\n'
python "$ICI/verify.py" "${TMPDIR:-/tmp}/altere.zip" 2>&1 | grep -E '^\[FAIL|^BILAN|^Ce dossier' | sed 's/^/  /' || true
rm -f "${TMPDIR:-/tmp}/altere.zip"
pause

titre '1c / 5  Et ce que verify.py NE voit PAS -- par conception'

printf 'On ajoute un octet a la FIN du fichier ZIP. Aucun membre ne change,\n'
printf 'donc l integrite INTERNE est intacte -- et `verify.py` le dit.\n\n'
cp NEOMUNDI_EVIDENCE_V1_DEMO.zip "${TMPDIR:-/tmp}/queue.zip"
printf '\0' >> "${TMPDIR:-/tmp}/queue.zip"
python "$ICI/verify.py" "${TMPDIR:-/tmp}/queue.zip" 2>&1 | grep '^BILAN' | sed 's/^/  /'
printf '\nC est exact, et ce n est pas un defaut : `verify.py` verifie\n'
printf 'l INTEGRITE INTERNE du dossier. L IDENTITE DU FICHIER, elle, est ce\n'
printf 'que l attestation couvre -- et elle le refuse :\n\n'
python "$ICI/verify_attestation.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive "${TMPDIR:-/tmp}/queue.zip" --trust-store trust-store.json \
    --allow-test-keys 2>&1 | grep -E '^\[FAIL|^BILAN' | sed 's/^/  /' || true
printf '\nDeux outils, deux garanties distinctes. Les confondre serait\n'
printf 'promettre l une en ne tenant que l autre.\n'
rm -f "${TMPDIR:-/tmp}/queue.zip"
pause

# --------------------------------------------------------------------------
titre "2 / 5  VERIFICATION AUTONOME -- aucune dependance obligatoire"

printf 'On bloque `cryptography` ET `opentimestamps`, puis on verifie.\n'
printf 'Le verificateur d archive ne doit pas meme s en apercevoir.\n\n'
BLOQUE="${TMPDIR:-/tmp}/sans-deps"
rm -rf "$BLOQUE"
mkdir -p "$BLOQUE/cryptography" "$BLOQUE/opentimestamps"
printf "raise ImportError('bloque pour la demonstration')\n" > "$BLOQUE/cryptography/__init__.py"
printf "raise ImportError('bloque pour la demonstration')\n" > "$BLOQUE/opentimestamps/__init__.py"
PYTHONPATH="$BLOQUE" python "$ICI/verify.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip --corpus corpus | grep '^BILAN'
printf '\nMEME BILAN. `verify.py` n importe que la bibliotheque standard.\n'
printf '\nEt l horodatage ? La LIAISON se lit a offset fixe, donc elle tient\n'
printf 'aussi sans la bibliotheque -- seul l arbre des attestations non :\n\n'
PYTHONPATH="$BLOQUE" python "$ICI/timestamp.py" verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots \
    --subject NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws | grep -E '^\[(PASS|NOT TESTED) *\] (liaison|arbre)'
rm -rf "$BLOQUE"
pause

# --------------------------------------------------------------------------
titre "3 / 5  ATTESTATION Ed25519 -- qui s est engage, et sur quoi"

python "$ICI/verify_attestation.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --trust-store trust-store.json --allow-test-keys | tail -22
pause

titre "3b / 5  Une cle de DEMONSTRATION n accorde rien par defaut"

python "$ICI/verify_attestation.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip \
    --trust-store trust-store.json 2>&1 | grep -E '^\[FAIL|^BILAN|^Cette' || true
pause

titre "3c / 5  Ce que l attestation referme : la limite n 7"

printf 'Une archive dont on retire une observation, PUIS dont on recalcule\n'
printf 'decomptes et sommes, est interieurement PARFAITE. `verify.py` seul\n'
printf 'n y voit rien. L attestation, elle, la refuse.\n\n'
python - <<'PY'
import hashlib, json, zipfile, pathlib, tempfile, os
src = pathlib.Path("NEOMUNDI_EVIDENCE_V1_DEMO.zip")
with zipfile.ZipFile(src) as z:
    m = {n: z.read(n) for n in z.namelist()}
obs = [l for l in m["observations.jsonl"].splitlines() if l.strip()]
retiree = json.loads(obs[0])["payload"]["observation_id"]
m["observations.jsonl"] = b"\n".join(obs[1:]) + b"\n"
for membre in ("measurements.jsonl", "reference_evaluations.jsonl",
               "replay_provenance.jsonl"):
    gardees = [l for l in m[membre].splitlines()
               if l.strip() and json.loads(l)["payload"].get("observation_id") != retiree]
    m[membre] = b"\n".join(gardees) + b"\n"
man = json.loads(m["manifest.json"])
for cle, membre in (("observations", "observations.jsonl"), ("mesures", "measurements.jsonl"),
                    ("evaluations", "reference_evaluations.jsonl"),
                    ("provenances_de_rejeu", "replay_provenance.jsonl")):
    man["decomptes"][cle] = len([l for l in m[membre].splitlines() if l.strip()])
m["manifest.json"] = json.dumps(man, ensure_ascii=False, indent=2).encode()
couverts = sorted(n for n in m if n != "checksums.sha256")
m["checksums.sha256"] = "".join(
    "%s  %s\n" % (hashlib.sha256(m[n]).hexdigest(), n) for n in couverts).encode()
cible = pathlib.Path(tempfile.gettempdir()) / "amputee.zip"
with zipfile.ZipFile(cible, "w", compression=zipfile.ZIP_STORED) as z:
    for n in sorted(m):
        z.writestr(zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0)), m[n])
print("  une observation retiree, tout recalcule -> %s" % cible)
PY
printf '\n  `verify.py` seul :\n'
python "$ICI/verify.py" "${TMPDIR:-/tmp}/amputee.zip" 2>&1 | grep '^BILAN' | sed 's/^/    /'
printf '\n  avec l attestation :\n'
python "$ICI/verify_attestation.py" NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --archive "${TMPDIR:-/tmp}/amputee.zip" --trust-store trust-store.json \
    --allow-test-keys 2>&1 | grep -E '^\[FAIL|^BILAN' | sed 's/^/    /' || true
rm -f "${TMPDIR:-/tmp}/amputee.zip"
pause

# --------------------------------------------------------------------------
titre "4 / 5  HORODATAGE -- le statut REEL, et ce qu il ne prouve pas"

python "$ICI/timestamp.py" verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots \
    --subject NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws \
    --descriptor NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.timestamp.json | tail -20
printf '\nEn mode strict, un PENDING rend CODE 2 -- pas 0 :\n'
set +e
python "$ICI/timestamp.py" verify NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws.ots \
    --subject NEOMUNDI_EVIDENCE_V1_DEMO.zip.jws --strict > /dev/null 2>&1
printf '  code de sortie : %d\n' "$?"
set -e
pause

# --------------------------------------------------------------------------
titre "5 / 5  RECONCILIATION -- confronter sans trancher"

python "$ICI/adapters/reconcile.py" receipt-imported.json \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip --map map-comparable.json | tail -24
pause

titre "5b / 5  Le MEME recu, sans contexte de mesure declare"

printf 'Plus rien de ce qui est MESURE ne se compare. Mais une empreinte,\n'
printf 'elle, concorde toujours.\n\n'
python "$ICI/adapters/reconcile.py" receipt-imported.json \
    --archive NEOMUNDI_EVIDENCE_V1_DEMO.zip --map map-no-context.json \
    | grep -E '^\[|^BILAN'
pause

# --------------------------------------------------------------------------
titre "Ce que la demonstration a etabli, et ce qu elle n a pas etabli"

cat <<'FIN'
  DEMONTRE, sous vos yeux

    L integrite d un dossier, par 21 controles, et son refus des qu un
    octet change.

    La verification AUTONOME : le verificateur d archive n importe que la
    bibliotheque standard, et la liaison d horodatage non plus.

    Une partie IDENTIFIEE engagee sur l empreinte du dossier, par
    Ed25519 -- et le refus d une cle de demonstration par defaut.

    La detection d une archive recalculee apres suppression : la premiere
    limite declaree du produit qui se referme.

    Une preuve d horodatage REELLE, liee a l attestation.

    Une reconciliation qui conserve les deux cotes et ne tranche rien.

  PAS DEMONTRE, et ecrit a chaque execution

    LE TEMPS. La preuve est PENDING : un calendrier s est engage a
    inclure l empreinte dans une transaction future. AUCUNE DATE n est
    attestee, et nous ne verifions de toute facon aucune attestation
    Bitcoin -- cela demande un en-tete de bloc.

    AUCUN horodatage qualifie eIDAS. OpenTimestamps n est pas un
    prestataire de services de confiance qualifie.

    LA VERITE DU CONTENU. Une attestation parfaitement signee sur une
    archive fabriquee est cryptographiquement valide. Signer etablit un
    engagement, pas un fait.

    LA CAPACITE JURIDIQUE du signataire : aucun code ne l etablit.

    QUE L EXECUTION MESUREE A EU LIEU. Rien ici ne le dit.

  Et tout ce que vous venez de voir portait sur des fixtures
  SYNTHETIQUES et une cle de DEMONSTRATION detruite. Aucune de ces
  fonctions n a encore ete eprouvee sur un dossier de pilote reel.
FIN

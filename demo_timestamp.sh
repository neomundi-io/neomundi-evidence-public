#!/bin/sh
# Demonstration de l horodatage independant. HORS LIGNE, et reproductible.
#
#   sh demo_timestamp.sh
#
# Elle montre ce que nous demontrons -- la LIAISON -- et ce que nous ne
# demontrons pas : le TEMPS.

set -eu
ICI="$(cd "$(dirname "$0")" && pwd)"
PREUVE="$ICI/examples/timestamp/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.ots"
SUJET="$ICI/examples/attestation/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws"
DESC="$ICI/examples/timestamp/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip.jws.timestamp.json"

titre() { printf '\n========================================================\n  %s\n========================================================\n\n' "$1"; }
pause() { printf '\n'; if [ -t 0 ]; then printf '  -- Entree pour continuer --'; read -r _; printf '\n'; fi; }

titre "1. Ce que la preuve porte"
printf 'Une preuve .ots de %s octets, obtenue de quatre calendriers publics.\n' "$(wc -c < "$PREUVE" | tr -d ' ')"
printf 'Seule une empreinte de 32 octets avait quitte le poste.\n\n'
python "$ICI/timestamp.py" inspect "$PREUVE"
pause

titre "2. La liaison -- ce que NOUS demontrons"
python "$ICI/timestamp.py" verify "$PREUVE" --subject "$SUJET" --descriptor "$DESC"
pause

titre "3. Un autre sujet : la liaison doit echouer"
printf 'un contenu different\n' > "${TMPDIR:-/tmp}/autre-sujet.txt"
python "$ICI/timestamp.py" verify "$PREUVE" --subject "${TMPDIR:-/tmp}/autre-sujet.txt" || true
rm -f "${TMPDIR:-/tmp}/autre-sujet.txt"
pause

titre "4. Mode strict : PENDING n est pas une preuve de temps"
printf 'Les verdicts ne changent pas. Seul le code de sortie en tient compte.\n\n'
python "$ICI/timestamp.py" verify "$PREUVE" --subject "$SUJET" --strict || CODE=$?
printf '\ncode de sortie : %s (2 = garantie requise non demontree)\n' "${CODE:-0}"
pause

titre "Ce que la demonstration montre"
cat <<'TEXTE'
  Nous demontrons que la preuve s engage sur l empreinte du sujet, et
  nous le faisons SANS AUCUNE DEPENDANCE : l empreinte engagee se lit a
  offset fixe dans le format .ots.

  Nous ne demontrons PAS le temps. Valider une attestation Bitcoin
  demande un en-tete de bloc, donc une source de confiance que nous
  n avons pas. C est delegue au client officiel : `ots verify`.

  Et tant que l etat est PENDING, AUCUNE date n est attestee -- un
  calendrier s est seulement engage a inclure l empreinte dans une
  transaction future.

  Aucun horodatage qualifie eIDAS n est revendique.
TEXTE

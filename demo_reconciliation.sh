#!/bin/sh
# Demonstration de la reconciliation. Autonome : la fixture est fabriquee.
#
#   sh demo_reconciliation.sh
#
# Elle montre les cinq statuts, et surtout pourquoi deux valeurs differentes
# ne sont pas forcement une divergence de calcul.

set -eu
ICI="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

titre() { printf '\n========================================================\n  %s\n========================================================\n\n' "$1"; }
pause() { printf '\n'; if [ -t 0 ]; then printf '  -- Entree pour continuer --'; read -r _; printf '\n'; fi; }

python "$ICI/tests/make_fixture.py" "$T/fixture" > /dev/null
ARCHIVE="$T/fixture/NEOMUNDI_EVIDENCE_CI_FIXTURE.zip"

titre "1. Importer un recu externe, SANS l interpreter"
printf 'Le recu est entierement SYNTHETIQUE. Rien de ce qu il dit n est cru.\n\n'
python "$ICI/adapters/receipt_import.py" \
    "$ICI/examples/reconciliation/receipt-synthetic.html" \
    --received-at 2026-11-05T12:00:00Z --out "$T/recu.json"
pause

titre "2. Reconcilier -- le recu DECLARE son contexte de mesure"
printf 'Les valeurs mesurees peuvent alors etre comparees.\n\n'
python "$ICI/adapters/reconcile.py" "$T/recu.json" --archive "$ARCHIVE" \
    --map "$ICI/examples/reconciliation/map-comparable.json"
pause

titre "3. Le meme recu, sans contexte declare -- le cas REEL"
printf 'Rien de ce qui est MESURE ne se compare plus. Mais une empreinte,\n'
printf 'elle, concorde toujours : elle ne depend pas du contexte de mesure.\n\n'
python "$ICI/adapters/reconcile.py" "$T/recu.json" --archive "$ARCHIVE" \
    --map "$ICI/examples/reconciliation/map-no-context.json"
pause

titre "4. Un recu qui ne correspond a rien"
printf '<table><tr><td>item</td><td>rien-de-commun</td></tr></table>\n' > "$T/sans-lien.html"
python "$ICI/adapters/receipt_import.py" "$T/sans-lien.html" \
    --received-at 2026-11-05T12:00:00Z --out "$T/sl.json" > /dev/null
python "$ICI/adapters/reconcile.py" "$T/sl.json" --archive "$ARCHIVE" \
    --map "$ICI/examples/reconciliation/map-comparable.json" | head -12
pause

titre "Ce que la demonstration montre"
cat <<'TEXTE'
  Les cinq statuts sont distingues, et le plus important est celui qu on
  oublie : NOT COMPARABLE. Deux valeurs differentes ne sont une divergence
  de CALCUL que si elles mesurent la meme chose -- meme definition, meme
  version, meme couverture. Sinon, conclure a une anomalie serait une faute
  de raisonnement, pas une decouverte.

  La frontiere de comparabilite ne mord que sur les valeurs MESUREES. Une
  empreinte concorde ou ne concorde pas, et la version de mesure n y change
  rien : c est la preuve la plus forte dont on dispose, et elle survit.

  Aucune correspondance n est devinee : sans entree dans la table, un champ
  est laisse de cote. Et une proximite de date ou de modele ne constitue
  JAMAIS une liaison.

  Les contradictions sont CONSERVEES. Rien n est tranche, rien n est moyenne.
  Un recu externe reste une DECLARATION ; notre archive reste une preuve
  primaire. Les melanger serait la confusion que ce produit refuse.
TEXTE

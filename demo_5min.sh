#!/usr/bin/env bash
# Demonstration de cinq minutes — NeoMundi Evidence V0.1.
#
# Cinq etapes, chronometrees. Aucun appel reseau, aucun cout, aucune donnee de
# pilote. Tout part du corpus GELE, jamais d'un repertoire de travail.
#
# Emploi (depuis WSL) :
#     bash demo_5min.sh [repertoire_de_sortie]
#
# Le script ECRIT uniquement dans son repertoire de sortie. Il ne touche ni au
# gel, ni au depot de la Station, ni a la production.

set -uo pipefail

# Aucun chemin personnel n'est code en dur : ce script est dans un depot, et un
# depot n'a pas a porter l'arborescence de la machine de qui l'a ecrit.
#
#     STATION  le depot de la Station (defaut : ~/code/neomundi-station)
#     GEL      le gel des corpus de reference — OBLIGATOIRE
#     EVIDENCE ce depot (defaut : le repertoire de ce script)
STATION="${STATION:-$HOME/code/neomundi-station}"
EVIDENCE="${EVIDENCE:-$(cd "$(dirname "$0")" && pwd)}"
SORTIE="${1:-/tmp/demo-evidence-$$}"

if [ -z "${GEL:-}" ]; then
  cat >&2 <<'AIDE'
GEL n'est pas defini : ce script ne devine pas ou vit le gel des corpus.

    GEL=<chemin du gel> bash demo_5min.sh [repertoire_de_sortie]

Le gel attendu est `20261105T1200_GEL_CORPUS_GATE0` ; il doit contenir
`GROUNDED-S1/donnees/ledger.jsonl` et `GROUNDED-S1/entrees/corpus/`.
AIDE
  exit 2
fi

PY="$STATION/.venv/bin/python"
STATION_CLI="$STATION/.venv/bin/station"
ARCHIVE="$SORTIE/NEOMUNDI_EVIDENCE_DEMO_V0.1.zip"
CORPUS="$GEL/GROUNDED-S1/entrees/corpus"
REGISTRE="$GEL/GROUNDED-S1/donnees/ledger.jsonl"

mkdir -p "$SORTIE"
DEBUT=$(date -u +%s)

chrono() { printf '%s' "$(( $(date -u +%s) - DEBUT ))"; }

etape() {
  printf '\n'
  printf '================================================================\n'
  printf '  ETAPE %s  —  %s        [t+%ss]\n' "$1" "$2" "$(chrono)"
  printf '================================================================\n'
}

echo "DEMONSTRATION NEOMUNDI EVIDENCE V0.1"
echo "lancee le $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "sortie : $SORTIE"
echo "gel    : $GEL"

# ---------------------------------------------------------------- 1
etape 1 "le point de depart se verifie"
echo "> python verifier_gel.py <gel>"
"$PY" "$GEL/verifier_gel.py" "$GEL" 2>&1 | tail -3
echo
echo "> station ledger verify --path <gel>/GROUNDED-S1/donnees/ledger.jsonl"
"$STATION_CLI" ledger verify --path "$REGISTRE" 2>&1 | tail -3

# ---------------------------------------------------------------- 2
etape 2 "le dossier se produit"
echo "> station campaign export grounded-med-synthetique-v1"
rm -f "$ARCHIVE"
( cd "$STATION" && "$STATION_CLI" campaign export grounded-med-synthetique-v1 \
    --sortie "$ARCHIVE" --registre "$REGISTRE" 2>&1 ) | sed 's/^/  /'
echo
echo "  empreinte de l'archive, a conserver AILLEURS qu'avec elle :"
sha256sum "$ARCHIVE" | sed 's/^/    /'

# ---------------------------------------------------------------- 3
etape 3 "il se verifie sans NeoMundi"
echo "> python verify.py <archive> --corpus <corpus>"
"$PY" "$EVIDENCE/verify.py" "$ARCHIVE" --corpus "$CORPUS" 2>&1 | tail -6

# ---------------------------------------------------------------- 4
etape 4 "une falsification est detectee, et une limite est montree"
echo "> python tests/test_falsification.py <archive> <corpus>"
"$PY" "$EVIDENCE/tests/test_falsification.py" "$ARCHIVE" "$CORPUS" 2>&1 \
  | grep -E "^\[|^ *raison|^ *l'empreinte|^BILAN" | sed 's/^/  /'

# ---------------------------------------------------------------- 5
etape 5 "le rapport dit ce qu'il ne sait pas"
"$PY" - "$ARCHIVE" <<'PYEOF'
import json, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
with zipfile.ZipFile(sys.argv[1]) as z:
    rapport = z.read("rapport.md").decode("utf-8")
    manifeste = json.loads(z.read("manifest.json"))

def extrait(titre, lignes=6):
    index = rapport.find(titre)
    if index < 0:
        return "  (%s absent)" % titre
    return "\n".join("  " + l for l in rapport[index:].splitlines()[:lignes])

print("  --- aucun cout etabli, donc aucune somme affichee ---")
for ligne in rapport.splitlines():
    if "cout non etabli" in ligne.replace("û", "u").replace("é", "e"):
        print("  " + ligne.strip())
print()
print("  --- par signal : ce qui est mesure, ce qui reste null ---")
mes = manifeste["mesures"]
for nom in sorted(set(mes["signaux_values"]) | set(mes["signaux_nuls"])):
    print("  %-32s mesure %2d   null %2d"
          % (nom, mes["signaux_values"].get(nom, 0), mes["signaux_nuls"].get(nom, 0)))
print("  etats de mesure :", mes["statuts"])
print()
print("  --- la garde de regime ---")
for garde in manifeste["gardes_de_lecture"]:
    print("  " + garde)
print()
print("  --- les limites, inscrites dans l'archive ---")
for limite in manifeste["limites"]:
    print("  - " + limite)
PYEOF

FIN=$(date -u +%s)
printf '\n================================================================\n'
printf '  DUREE TOTALE : %s s  (%s min %s s)\n' "$((FIN-DEBUT))" "$(( (FIN-DEBUT)/60 ))" "$(( (FIN-DEBUT)%60 ))"
printf '  archive      : %s\n' "$ARCHIVE"
printf '================================================================\n'
printf '\nCe qui vient d etre etabli :\n'
printf '  - un dossier de campagne se produit, se lit et se verifie sans NeoMundi ;\n'
printf '  - la verification refuse une archive touchee, dix fois sur dix ;\n'
printf '  - une falsification coherente passe, et seule l empreinte conservee\n'
printf '    ailleurs la detecte. Cette limite est montree, pas cachee.\n'
printf '\nCe qui NE l est pas : la justesse des signaux, l authenticite de l archive,\n'
printf 'et la disposition d un acheteur a payer pour cela.\n'

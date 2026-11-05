#!/bin/sh
# Demonstration de la liaison observation <-> artefacts.
#
# Complementaire de demo_5min.sh, qui montre la verification d une archive.
# Celle-ci montre autre chose : la difference entre un RECIT et une PREUVE.
#
#   sh demo_binding.sh <archive_evidence.zip>
#
# Rien n est ecrit hors du repertoire temporaire, et rien n est publie.

set -eu

ARCHIVE="${1:?emploi : sh demo_binding.sh <archive_evidence.zip>}"
ICI="$(cd "$(dirname "$0")" && pwd)"
EXEMPLE="$ICI/examples/binding"
TRAVAIL="$(mktemp -d)"
trap 'rm -rf "$TRAVAIL"' EXIT

pause() {
    printf '\n'
    if [ -t 0 ]; then printf '  -- Entree pour continuer --'; read -r _; printf '\n'; fi
}

titre() {
    printf '\n========================================================\n'
    printf '  %s\n' "$1"
    printf '========================================================\n\n'
}

titre "1. Ce que l archive porte deja"

printf 'Une observation declare des empreintes d objets qui ne sont PAS dans\n'
printf 'l archive : la reponse, le prompt, la requete. Ces empreintes sont\n'
printf 'portees par un enregistrement chaine.\n\n'
printf 'Les voici, telles que l enregistrement les declare :\n\n'
python "$ICI/bind.py" verify "$EXEMPLE/manifest.json" \
    --root "$EXEMPLE" --archive "$ARCHIVE" 2>&1 \
    | grep -E "empreintes declarees|le sujet" || true

pause

titre "2. Une liaison verifiable"

printf 'Deux fichiers sont offerts. Leurs octets se hachent sur deux des\n'
printf 'empreintes que l enregistrement declare.\n\n'
python "$ICI/bind.py" verify "$EXEMPLE/manifest.json" \
    --root "$EXEMPLE" --archive "$ARCHIVE"

pause

titre "3. Le meme recit, sans rien dessous"

printf 'On retire les artefacts et on garde le texte, mot pour mot.\n\n'
mkdir -p "$TRAVAIL/recit"
python - "$EXEMPLE/manifest.json" "$TRAVAIL/recit/manifest.json" <<'PY'
import json, sys
m = json.loads(open(sys.argv[1], encoding="utf-8").read())
m["statements"] = [
    "Le 22 octobre 2026 a 09:00:00 UTC, l item 00ff4465 a ete soumis au "
    "modele grounded-s1-2026-10-22. La reponse a ete recue en 512 ms, puis "
    "mesuree en version 3.3.0."
]
m["artifacts"] = []
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(m, ensure_ascii=False, indent=2))
PY
python "$ICI/bind.py" verify "$TRAVAIL/recit/manifest.json" \
    --root "$TRAVAIL/recit" --archive "$ARCHIVE"

pause

titre "4. Une liaison qui se revendique mieux qu elle n est"

printf 'Le manifeste se revendique `cryptographically_attested`. Aucune\n'
printf 'signature n est verifiee dans ce depot, donc ce niveau est hors\n'
printf 'd atteinte -- et le dire serait faux.\n\n'
mkdir -p "$TRAVAIL/menteur"
cp -R "$EXEMPLE/." "$TRAVAIL/menteur/"
python - "$TRAVAIL/menteur/manifest.json" <<'PY'
import json, sys
chemin = sys.argv[1]
m = json.loads(open(chemin, encoding="utf-8").read())
for a in m["artifacts"]:
    a["claimed_assurance"] = "cryptographically_attested"
open(chemin, "w", encoding="utf-8").write(json.dumps(m, ensure_ascii=False, indent=2))
PY
python "$ICI/bind.py" verify "$TRAVAIL/menteur/manifest.json" \
    --root "$TRAVAIL/menteur" --archive "$ARCHIVE" || true

pause

titre "Ce que la demonstration montre"

cat <<'FIN'
  Trois manifestes. Le premier et le troisieme portent le MEME texte.

    liaison verifiable   -> reference_verifiable
    le meme recit seul   -> declared
    liaison qui se ment  -> refusee

  L outil ne mesure pas la prose. Une description textuelle d une
  execution ne constitue pas une preuve que cette execution a eu lieu.

  Et ce qu une liaison verifiable etablit reste limite : que les
  fichiers offerts sont bien ceux auxquels l enregistrement se refere.
  Pas que l execution a eu lieu, ni quand, ni chez qui.
FIN

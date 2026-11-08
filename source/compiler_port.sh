#!/bin/bash
# Compile une carte GMod à partir d'un fichier Blender (par défaut : le port seul).
# Lancer :  bash jjk_carte_ecole/source/compiler_port.sh
#    port + Shibuya :  NOM_CARTE=jjk_shibuya BLEND=shibuya.blend bash jjk_carte_ecole/source/compiler_port.sh
#    visibilité rapide (tests) : ajouter VVIS_RAPIDE=1
# 0. creer_port_compact.py (puis creer_shibuya.py) doivent avoir créé le fichier .blend
# 1. textures_gmod.py : matériaux maison (materials/jjk_port)   2. exporter_gmod.py (Blender) : source/<carte>.vmf
# 3. modèles NEOTOKYO copiés dans l'addon (pour les joueurs) ; modèles CS:S copiés TEMPORAIREMENT dans garrysmod/models
# 4. vbsp / vvis / vrad dans un dossier temporaire ; seule la .bsp est copiée dans ../maps/
set -e
ICI="$(cd "$(dirname "$0")" && pwd)"
DOSSIER="$(cd "$ICI/.." && pwd)"                   # jjk_carte_ecole
GMOD="$(cd "$DOSSIER/../../.." && pwd)"             # .../GarrysMod
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
NOM_CARTE="${NOM_CARTE:-jjk_port}"
BLEND="${BLEND:-port.blend}"
TMP="${TMPDIR:-/tmp}/$NOM_CARTE"
mkdir -p "$TMP"
cd "$DOSSIER/blender"
python textures_gmod.py
CARTE="$NOM_CARTE" "$BLENDER" -b "$BLEND" --python exporter_gmod.py 2>&1 | grep -a "EXPORT GMOD"
PYTHONIOENCODING=utf-8 python copier_neotokyo.py "$ICI/$NOM_CARTE.vmf"
# modèles CS:S -> garrysmod/models (seulement ceux qui n'y sont pas), journal pour les effacer ensuite
JOURNAL="$TMP/copies.txt"
: > "$JOURNAL"
nettoyer() { while read -r f; do rm -f "$f"; done < "$JOURNAL"; find "$GMOD/garrysmod/models/props" -type d -empty -delete 2>/dev/null || true; }
trap nettoyer EXIT
grep -o '"model" "models/props/[^"]*"' "$ICI/$NOM_CARTE.vmf" | sort -u | sed 's/"model" "//; s/\.mdl"//' | while read -r m; do
  for f in "$DOSSIER/blender/modeles_jeu/$m".*; do
    [ -e "$f" ] || continue
    dest="$GMOD/garrysmod/${f#$DOSSIER/blender/modeles_jeu/}"
    if [ ! -e "$dest" ]; then mkdir -p "$(dirname "$dest")"; cp "$f" "$dest"; echo "$dest" >> "$JOURNAL"; fi
  done
done
cp "$ICI/$NOM_CARTE.vmf" "$TMP/"
cd "$TMP"
"$GMOD/bin/vbsp.exe" -game "$GMOD/garrysmod" "$NOM_CARTE.vmf"
"$GMOD/bin/vvis.exe" ${VVIS_RAPIDE:+-fast} -game "$GMOD/garrysmod" "$NOM_CARTE"
"$GMOD/bin/vrad.exe" -game "$GMOD/garrysmod" -StaticPropLighting "$NOM_CARTE"
mkdir -p "$DOSSIER/maps"
cp "$NOM_CARTE.bsp" "$DOSSIER/maps/"
echo "Carte prête : jjk_carte_ecole/maps/$NOM_CARTE.bsp"

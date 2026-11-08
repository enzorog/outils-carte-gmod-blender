"""
Extrait les VRAIES textures du jeu (CS:S, HL2) choisies pour le port -> blender/textures_jeu/<nom>.png
Ce sont aussi les textures que GMod affichera : ce qu'on voit dans Blender = ce qu'on aura en jeu.
Lancer : python textures_jeu.py
"""
import os, sys
import vpk
from vtf_png import vtf_vers_image

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "textures_jeu")
GMOD = os.path.normpath(os.path.join(ICI, "..", "..", "..", ".."))
os.makedirs(SORTIE, exist_ok=True)
CSS = vpk.open(os.path.join(GMOD, "sourceengine", "content_cstrike_dir.vpk"))
HL2 = vpk.open(os.path.join(GMOD, "sourceengine", "hl2_textures_dir.vpk"))

CHOIX = {
    "beton_sol": (HL2, "concrete/concretefloor036a"),
    "beton_sol2": (HL2, "concrete/concretefloor039a"),
    "route": (HL2, "concrete/concretefloor033a"),
    "terre": (CSS, "de_train/train_gravel_floor_01"),
    "tole_grise": (CSS, "de_nuke/nukmetwallk"),
    "tole_beige": (CSS, "de_nuke/nukmetwallj"),
    "tole_brune": (CSS, "de_nuke/nukmetwallg"),
    "carton": (CSS, "props/cardboardbox001a"),
    "tole_bleue": (CSS, "de_nuke/nukmetwalli"),
    "tole_toit": (HL2, "metal/metalroof004a"),
    "rideau": (HL2, "metal/metaldoor061a"),
    "acier_rouge": (CSS, "models/props/de_nuke/i_beams_red"),
    "acier_gris": (HL2, "metal/metalhull003a"),
    "grille": (HL2, "metal/metalgrate013a"),
    "beton_mur": (HL2, "concrete/concretewall074a"),
    "coque": (HL2, "metal/metalhull005a"),
    "bois": (CSS, "models/props/de_train/wood_pallet_01"),
    "facade": (HL2, "building_template/building_template007h"),
    "facade2": (HL2, "building_template/building_template010a"),
    "facade3": (HL2, "building_template/building_template007m"),
    "facade4": (HL2, "building_template/building_template009e"),
    "rayures": (CSS, "de_train/train_cautionstripe"),
    "bois_mur": (HL2, "wood/woodwall009a"),
    "herbe": (HL2, "nature/grassfloor002a"),
    "dallage": (HL2, "stone/stonefloor006a"),
    "gravier": (HL2, "nature/gravelfloor004a"),
    "brique": (HL2, "brick/brickwall031d"),
    "enduit": (HL2, "plaster/plasterwall044b"),
    "beton_mur2": (HL2, "concrete/concretewall071a"),
    "carrelage": (HL2, "tile/tilefloor013a"),
    "beton_sol3": (HL2, "concrete/concretefloor026a"),
    "acier_rouille": (HL2, "metal/metalwall021a"),
    "conteneur_1": (CSS, "models/props/de_port/cargo_container01"),
    "conteneur_2": (CSS, "models/props/de_port/cargo_container02"),
    "conteneur_3": (CSS, "models/props/de_port/cargo_container03"),
    "conteneur_4": (HL2, "models/props_wasteland/cargo_container01"),
    "conteneur_5": (HL2, "models/props_wasteland/cargo_container02"),
}

for nom, (paquet, chemin) in CHOIX.items():
    img = vtf_vers_image(paquet.get_file("materials/" + chemin + ".vtf").read())
    img.save(os.path.join(SORTIE, nom + ".png"))
    print("texture du jeu", nom, img.size, "<-", chemin)

"""
Ouvre port.blend et rend une série de vues « comme si on se promenait » -> apercus/visite_XX_nom.png
Lancer : blender.exe -b port.blend --python rendre_vues.py
"""
import bpy, math, os

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "apercus")
sc = bpy.context.scene
cam = sc.camera
QY = 150.0

VUES = [
    ("01_tunnel_d_entree", (184, -66, 1.7), (187, 0, 4), 18),
    ("01a_bouche_du_tunnel", (186.5, 10, 4), (186.5, -40, 6), 20),
    ("01b_sortie_du_tunnel", (186.5, -6, 1.7), (150, 60, 4), 22),
    ("02a_camion_de_pres", (34, 46, 3.2), (24, 52, 1.5), 22),
    ("02_route_principale", (5, 64.5, 1.7), (100, 66, 3), 28),
    ("03_allee_entre_conteneurs", (47.6, 72, 1.7), (47.6, 125, 2), 20),
    ("04_parc_conteneurs_hauteur", (40, 70, 9), (90, 110, 0), 20),
    ("05_hangar_porte_ouverte", (70, 47, 1.7), (70, 38, 4), 20),
    ("06_hangar_garage", (88, 30, 3.5), (78, 25, 1.5), 18),
    ("06c_hangar_colis", (131, 34, 3.5), (125, 24, 1), 18),
    ("06d_hangar_planque", (165, 34, 3), (172, 28, 1), 18),
    ("06b_escalier_mezzanine", (72, 18, 1.7), (62.5, 26, 3.5), 18),
    ("07_toit_du_hangar", (52, 22, 14.2), (110, 110, 5), 20),
    ("08_bord_du_quai", (150, QY - 2.5, 1.7), (80, QY + 15, 3), 22),
    ("09_interieur_hangar_rayonnages", (118, 38, 1.7), (100, 18, 2.5), 18),
    ("10_sous_la_grue", (69, QY - 11, 1.7), (69, QY - 11.1, 40), 16),
    ("11_en_haut_de_la_grue", (68, QY - 12, 38), (110, 70, 0), 20),
    ("12_pied_de_la_tour", (178, 4, 1.7), (200, 25, 25), 20),
    ("14_enceinte_de_batiments", (100, 120, 25), (60, -20, 10), 22),
    ("13_vue_d_ensemble_soir", (-70, -90, 150), (100, 75, 0), 24),
]

for nom, pos, cible, lens in VUES:
    cam.location = pos
    dv = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(dv[0], dv[1]), -dv[2]), 0, math.atan2(dv[1], dv[0]) - math.pi / 2)
    cam.data.lens = lens
    sc.render.filepath = os.path.join(SORTIE, "visite_" + nom + ".png")
    bpy.ops.render.render(write_still=True)
    print("vue", nom)

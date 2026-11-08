"""
Ouvre port.blend (version compacte) et rend des vues de contrôle -> apercus/compact_XX_nom.png
Lancer : blender.exe -b port.blend --python rendre_vues_compact.py
"""
import bpy, math, os

ICI = os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene
cam = sc.camera
VUES = [
    ("01_vue_d_ensemble", (-45, -55, 75), (60, 45, 0), 22),
    ("02_tunnel_interieur", (104.5, -38, 1.7), (104.5, 20, 3), 18),
    ("03_bouche_du_tunnel", (104.5, 14, 3), (104.5, -20, 4), 20),
    ("04_entrepot_mezzanine", (20, 19.5, 1.7), (7, 10, 2.2), 18),
    ("05_garage", (70, 19.5, 2), (62, 12, 1.5), 18),
    ("06_colis", (34, 19.5, 2), (34, 10, 1), 18),
    ("07_planque", (82, 19.5, 2), (80, 12, 1), 18),
    ("07b_planque_salon", (74, 9, 2.2), (84, 15, 0.8), 18),
    ("07c_planque_boss", (80, 17, 1.8), (87, 18.5, 1.2), 18),
    ("04b_bureau_sous_mezzanine", (6.5, 9.5, 1.6), (3, 7.5, 0.9), 14),
    ("05b_garage_pneus", (60, 12, 1.7), (60, 6.5, 0.8), 18),
    ("08_escalier_du_toit", (8, 0.5, 1.7), (14, 4, 4), 18),
    ("09_camions", (30, 32.5, 2), (18, 27, 1.5), 20),
    ("10_allee_conteneurs", (33.4, 41, 1.7), (33.4, 68, 2), 20),
    ("11_zone_de_stock", (16, 39, 5), (6, 55, 0), 18),
    ("12_grue_echelle", (13, 73, 3), (20, 78, 11), 18),
    ("13_cabine_de_grue", (24.5, 81, 19.4), (27, 84.5, 18.8), 16),
    ("14_bureau_du_quai", (86.5, 80.5, 1.8), (81, 78.5, 1.0), 16),
    ("15_semi_remorques", (38, 74.5, 2.2), (30, 79.5, 1.5), 20),
    ("16_depuis_un_toit", (13, 8.5, 10.2), (60, 80, 14), 20),
    ("17_facade_des_hangars", (45, 33, 4), (20, 18, 4), 18),
]
for nom, pos, cible, lens in VUES:
    cam.location = pos
    dv = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(dv[0], dv[1]), -dv[2]), 0, math.atan2(dv[1], dv[0]) - math.pi / 2)
    cam.data.lens = lens
    sc.render.filepath = os.path.join(ICI, "apercus", "compact_" + nom + ".png")
    bpy.ops.render.render(write_still=True)
    print("vue", nom)

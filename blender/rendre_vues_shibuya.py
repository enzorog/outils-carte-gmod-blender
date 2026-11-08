"""
Ouvre shibuya.blend et rend des vues de contrôle de Shibuya -> apercus/shibuya_det_XX.png
Lancer : blender.exe -b shibuya.blend --python rendre_vues_shibuya.py
"""
import bpy, math, os

ICI = os.path.dirname(os.path.abspath(bpy.data.filepath))
sc = bpy.context.scene
cam = sc.camera
VUES = [
    ("01_sortie_du_tunnel", (104, -30, 1.7), (104, -140, 0), 20),
    ("02_place_depuis_les_gradins", (72, -122, 1.5), (104, -145, -2), 18),
    ("03_place_vue_haute", (40, -80, 35), (104, -145, -3), 22),
    ("04_rue_marchande", (43, -92, 1.7), (40, -150, 2), 18),
    ("05_boutique_tenues", (39.5, -118.4, 1.6), (31.5, -119.2, 1.2), 14),
    ("06_boutique_armes", (27.1, -182.3, 1.6), (19.1, -181.1, 1.2), 14),
    ("07_espace_rp", (-45, -150, 4), (-45, -95, 1), 18),
    ("08_rassemblement", (215, -215, 3), (235, -235, 0), 18),
    ("09_zone_de_conflit", (240, -100, 5), (270, -70, 0), 18),
    ("10_egout_entree", (180.5, -196, 3), (180.5, -187, -3), 16),
    ("11_egout_couloir", (180.5, -186.5, -3.4), (180.5, -175, -3.4), 16),
    ("12_passerelle", (22, -202, 6), (22, -185, 10), 18),
    ("13_rue", (230, -150, 1.7), (150, -150, 3), 20),
    ("14_vue_aerienne", (-170, -400, 190), (100, -130, 0), 24),
]
for nom, pos, cible, lens in VUES:
    cam.location = pos
    dv = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(dv[0], dv[1]), -dv[2]), 0, math.atan2(dv[1], dv[0]) - math.pi / 2)
    cam.data.lens = lens
    sc.render.filepath = os.path.join(ICI, "apercus", "shibuya_det_" + nom + ".png")
    bpy.ops.render.render(write_still=True)
    print("vue", nom)

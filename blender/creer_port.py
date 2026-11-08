"""
PORT INDUSTRIEL — BLOCKOUT (test « tout Blender »), univers JJK RP.
Formes simples pour valider l'organisation : terrain, routes, quai + eau, 4 hangars (on peut y entrer, toits accessibles),
grue portique, parc à conteneurs (modèle de conteneur réutilisé), tour de bureaux, bateaux, clôtures.
Architecture INTACTE (pas les destructions vues sur FOC JJK). Couleurs = matériaux probables, pas l'éclairage de la capture.

Lancer (sans ouvrir Blender) :
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python creer_port.py
Résultat : port_blockout.blend (à ouvrir dans Blender) + apercus/port_*.png
Relançable : la scène est recréée à chaque fois (aucun doublon).

Unités : mètres (1 m ≈ 52,5 unités GMod). Axes : X = est, Y = nord, Z = haut. L'eau est au nord.
Les dimensions importantes sont en haut du fichier.
"""
import bpy, math, os, random

ICI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- dimensions (modifiables)
PORT_L, PORT_P = 200.0, 150.0          # taille du port (est-ouest, sud-nord)
QUAI_Y = 150.0                          # bord du quai (au-delà : l'eau)
QUAI_HAUT = 2.5                         # hauteur du quai au-dessus de l'eau
HANGAR = dict(l=40.0, p=25.0, h=12.0, mur=0.4, porte_l=9.0, porte_h=7.0)
HANGARS_X = [5.0, 50.0, 95.0, 140.0]    # 4 hangars au sud
HANGAR_Y = 15.0
CONTENEUR = (12.19, 2.44, 2.59)         # conteneur 40 pieds (longueur, largeur, hauteur)
ROUTE_L = 9.0

# ---------------------------------------------------------------- couleurs (matériaux probables, plutôt sombres)
COULEURS = {
    "beton": (0.42, 0.41, 0.39), "beton_sombre": (0.28, 0.28, 0.27), "asphalte": (0.12, 0.12, 0.13),
    "ligne": (0.75, 0.68, 0.40), "terre": (0.33, 0.27, 0.20), "eau": (0.06, 0.13, 0.16),
    "toit_rouille": (0.42, 0.20, 0.10), "tole_mur": (0.32, 0.34, 0.33), "acier_rouge": (0.45, 0.10, 0.07),
    "acier": (0.30, 0.31, 0.33), "verre_sombre": (0.07, 0.09, 0.12), "grillage": (0.45, 0.46, 0.45),
    "coque": (0.12, 0.16, 0.22), "coque_rouge": (0.36, 0.08, 0.06), "pont_navire": (0.40, 0.38, 0.35),
    "c_rouge": (0.40, 0.09, 0.07), "c_bleu": (0.09, 0.17, 0.30), "c_vert": (0.11, 0.24, 0.15),
    "c_rouille": (0.45, 0.24, 0.10), "c_gris": (0.34, 0.35, 0.36), "c_blanc": (0.62, 0.62, 0.58),
    "bois": (0.30, 0.20, 0.12), "jaune": (0.70, 0.55, 0.10),
}


# ---------------------------------------------------------------- outils
def materiau(nom):
    m = bpy.data.materials.get("PORT_" + nom)
    if not m:
        m = bpy.data.materials.new("PORT_" + nom)
        r, g, b = COULEURS[nom]
        m.diffuse_color = (r, g, b, 1.0)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.85
    return m


COLL = {}


def collection(chemin):
    """collection par chemin « PORT/HANGARS » (créée si besoin, sous JJK_RP)"""
    if chemin in COLL:
        return COLL[chemin]
    parent = bpy.context.scene.collection
    nom_complet = ""
    for part in ["JJK_RP"] + chemin.split("/"):
        nom_complet = part if not nom_complet else nom_complet + "/" + part
        c = COLL.get(nom_complet)
        if not c:
            c = bpy.data.collections.new(part if part in ("JJK_RP", "PORT") else "PORT_" + part)
            parent.children.link(c)
            COLL[nom_complet] = c
        parent = c
    COLL[chemin] = parent
    return parent


def maillage_boite(nom):
    me = bpy.data.meshes.get(nom)
    if me:
        return me
    v = [(-0.5, -0.5, 0), (0.5, -0.5, 0), (0.5, 0.5, 0), (-0.5, 0.5, 0), (-0.5, -0.5, 1), (0.5, -0.5, 1), (0.5, 0.5, 1), (-0.5, 0.5, 1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(nom)
    me.from_pydata(v, [], f)
    me.update()
    return me


def boite(nom, coll, x0, y0, z0, x1, y1, z1, couleur, rot_z=0.0, maillage=None):
    """boîte de x0..x1, y0..y1, z0..z1 (avant rotation autour de son centre au sol)"""
    me = maillage or bpy.data.meshes.new(nom)
    if not maillage:
        src = maillage_boite("_unite")
        me = src.copy()
        me.name = nom
    o = bpy.data.objects.new(nom, me)
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, z0)
    o.scale = (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    o.rotation_euler = (0, 0, rot_z)
    if not maillage:
        me.materials.append(materiau(couleur))
    collection(coll).objects.link(o)
    return o


def prisme_toit(nom, coll, x0, y0, x1, y1, z, h, couleur):
    """toit à deux pentes (faîte le long de X), en tôle"""
    ym = (y0 + y1) / 2
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), (x0, ym, z + h), (x1, ym, z + h)]
    f = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    me = bpy.data.meshes.new(nom)
    me.from_pydata(v, [], f)
    me.update()
    me.materials.append(materiau(couleur))
    o = bpy.data.objects.new(nom, me)
    collection(coll).objects.link(o)
    return o


def cylindre(nom, coll, x, y, z0, z1, r, couleur, seg=12):
    v, f = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v += [(x + r * math.cos(a), y + r * math.sin(a), z0), (x + r * math.cos(a), y + r * math.sin(a), z1)]
    for k in range(seg):
        a, b = 2 * k, 2 * ((k + 1) % seg)
        f.append((a, b, b + 1, a + 1))
    f.append(tuple(2 * k for k in reversed(range(seg))))
    f.append(tuple(2 * k + 1 for k in range(seg)))
    me = bpy.data.meshes.new(nom)
    me.from_pydata(v, [], f)
    me.update()
    me.materials.append(materiau(couleur))
    o = bpy.data.objects.new(nom, me)
    collection(coll).objects.link(o)
    return o


# ---------------------------------------------------------------- scène vide
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"

# ---------------------------------------------------------------- TERRAIN, QUAI, EAU
boite("PORT_Terrain", "PORT/TERRAIN", -10, -10, -1.0, PORT_L + 10, QUAI_Y, 0.0, "beton")
boite("PORT_Quai_Principal", "PORT/QUAIS", -10, QUAI_Y - 22, 0.0, PORT_L + 10, QUAI_Y, 0.05, "beton_sombre")
boite("PORT_Quai_Mur", "PORT/QUAIS", -10, QUAI_Y - 0.6, -QUAI_HAUT - 3, PORT_L + 10, QUAI_Y, 0.0, "beton_sombre")
boite("PORT_Eau", "PORT/QUAIS", -200, QUAI_Y, -QUAI_HAUT - 0.2, PORT_L + 200, QUAI_Y + 250, -QUAI_HAUT, "eau")
for i, x in enumerate(range(5, int(PORT_L), 12)):              # bollards d'amarrage
    cylindre("PORT_Bollard_%02d" % (i + 1), "PORT/QUAIS", x, QUAI_Y - 1.2, 0, 0.8, 0.35, "acier")
boite("PORT_Terre_Ouest", "PORT/TERRAIN", 0, 70, 0.0, 18, 126, 0.03, "terre")
boite("PORT_Terre_Est", "PORT/TERRAIN", 182, 70, 0.0, 200, 126, 0.03, "terre")

# ---------------------------------------------------------------- ROUTES
boite("PORT_Route_EstOuest", "PORT/ROUTES", -10, 60, 0.02, PORT_L + 10, 60 + ROUTE_L, 0.06, "asphalte")
boite("PORT_Route_VersQuai", "PORT/ROUTES", 96, 60 + ROUTE_L, 0.02, 96 + ROUTE_L, QUAI_Y - 22, 0.06, "asphalte")
boite("PORT_Route_Entree", "PORT/ROUTES", 186, -10, 0.02, 186 + ROUTE_L, 60, 0.06, "asphalte")
for i, x in enumerate(range(0, int(PORT_L), 8)):                # marquage au sol
    boite("PORT_Marquage_%02d" % (i + 1), "PORT/ROUTES", x, 64.35, 0.06, x + 4, 64.65, 0.07, "ligne")

# ---------------------------------------------------------------- HANGARS (on entre par une grande porte, toit accessible)
H = HANGAR
for n, hx in enumerate(HANGARS_X, 1):
    nom = "PORT_Hangar_%02d" % n
    c = "PORT/HANGARS/" + nom
    x0, y0, x1, y1 = hx, HANGAR_Y, hx + H["l"], HANGAR_Y + H["p"]
    e = H["mur"]
    boite(nom + "_Dalle", c, x0, y0, 0.0, x1, y1, 0.15, "beton_sombre")
    pm = (x0 + x1) / 2
    # façade nord (vers la route) : grande porte au milieu
    boite(nom + "_Facade_G", c, x0, y1 - e, 0, pm - H["porte_l"] / 2, y1, H["h"], "tole_mur")
    boite(nom + "_Facade_D", c, pm + H["porte_l"] / 2, y1 - e, 0, x1, y1, H["h"], "tole_mur")
    boite(nom + "_Facade_Haut", c, pm - H["porte_l"] / 2, y1 - e, H["porte_h"], pm + H["porte_l"] / 2, y1, H["h"], "tole_mur")
    boite(nom + "_Mur_Sud", c, x0, y0, 0, x1, y0 + e, H["h"], "tole_mur")
    boite(nom + "_Mur_Ouest", c, x0, y0, 0, x0 + e, y1, H["h"], "tole_mur")
    boite(nom + "_Mur_Est", c, x1 - e, y0, 0, x1, y1, H["h"], "tole_mur")
    boite(nom + "_Porte_Pietons", c, x1 - e - 0.05, y0 + 4, 0, x1 + 0.05, y0 + 5.2, 2.2, "acier")      # petite porte côté est
    prisme_toit(nom + "_Toit", c, x0 - 0.6, y0 - 0.6, x1 + 0.6, y1 + 0.6, H["h"], 3.5, "toit_rouille")
    # mezzanine intérieure + escalier (pour monter vers une trappe du toit)
    boite(nom + "_Mezzanine", c, x0 + e, y0 + e, 5.0, x0 + 12, y1 - e, 5.3, "acier")
    for k in range(10):
        boite(nom + "_Escalier_%02d" % (k + 1), c, x0 + 12 + k * 0.6, y0 + 2, 0, x0 + 12.6 + k * 0.6, y0 + 4, 5.0 - k * 0.5, "acier")
    # échelle extérieure vers le toit (côté ouest)
    boite(nom + "_Echelle_Toit", c, x0 - 0.5, y0 + 10, 0, x0 - 0.1, y0 + 11, H["h"] + 1, "jaune")
    # quelques caisses et palettes à l'intérieur
    for k in range(4):
        boite(nom + "_Caisses_%02d" % (k + 1), c, x0 + 16 + k * 5, y0 + 3, 0.15, x0 + 19 + k * 5, y0 + 6, 1.6 + (k % 2), "bois")

# ---------------------------------------------------------------- CONTENEURS (un seul maillage, réutilisé partout = léger)
me_c = maillage_boite("PORT_Conteneur_Modele")
CC = ["c_rouge", "c_bleu", "c_vert", "c_rouille", "c_gris", "c_blanc"]
for nom in CC:
    materiau(nom)
rnd = random.Random(7)
L, l, h = CONTENEUR
compte = 0
for bloc, (bx, by, ncol, nrang) in enumerate([(22, 76, 4, 6), (82, 76, 4, 6), (112, 76, 4, 6), (152, 76, 2, 6), (22, 100, 4, 8), (112, 100, 4, 8)]):
    for i in range(ncol):
        for j in range(nrang):
            empile = rnd.choice((1, 2, 2, 3))
            for k in range(empile):
                compte += 1
                x, y = bx + i * (L + 0.6), by + j * (l + 0.3)
                o = bpy.data.objects.new("PORT_Container_%03d" % compte, me_c)
                o.location = (x + L / 2, y + l / 2, k * h)
                o.scale = (L, l, h)
                coul = rnd.choice(CC)
                o.data = me_c
                o.material_slots  # un maillage partagé : la couleur va sur l'objet
                if not o.data.materials:
                    o.data.materials.append(materiau("c_gris"))
                o.material_slots[0].link = "OBJECT"
                o.material_slots[0].material = materiau(coul)
                collection("PORT/CONTENEURS").objects.link(o)

# ---------------------------------------------------------------- GRUE PORTIQUE (sur le quai)
g = "PORT/GRUES"
gx, gy = 60.0, QUAI_Y - 18
for dx in (0, 18):
    for dy in (0, 14):
        boite("PORT_Grue_Pied_%d_%d" % (dx, dy), g, gx + dx, gy + dy, 0, gx + dx + 1.5, gy + dy + 1.5, 30, "acier_rouge")
boite("PORT_Grue_Traverse_S", g, gx, gy, 28, gx + 19.5, gy + 1.5, 30, "acier_rouge")
boite("PORT_Grue_Traverse_N", g, gx, gy + 14, 28, gx + 19.5, gy + 15.5, 30, "acier_rouge")
boite("PORT_Grue_Fleche", g, gx + 7, gy - 20, 30, gx + 12.5, QUAI_Y + 45, 33, "acier_rouge")
boite("PORT_Grue_Cabine", g, gx + 7.5, QUAI_Y + 2, 26, gx + 12, QUAI_Y + 6, 30, "jaune")
boite("PORT_Grue_Machinerie", g, gx + 6, gy + 2, 33, gx + 13.5, gy + 12, 37, "acier_rouge")
for k in range(2):
    boite("PORT_Grue_Rail_%d" % (k + 1), g, -10, gy + 0.5 + k * 14, 0.05, PORT_L + 10, gy + 1 + k * 14, 0.15, "acier")

# ---------------------------------------------------------------- TOUR DE BUREAUX (toit accessible, parapet)
t = "PORT/BATIMENTS"
boite("PORT_Tour_Bureaux", t, 184, 15, 0, 200, 35, 48, "verre_sombre")
boite("PORT_Tour_Parapet_N", t, 184, 34.4, 48, 200, 35, 49.2, "beton_sombre")
boite("PORT_Tour_Parapet_S", t, 184, 15, 48, 200, 15.6, 49.2, "beton_sombre")
boite("PORT_Tour_Parapet_O", t, 184, 15, 48, 184.6, 35, 49.2, "beton_sombre")
boite("PORT_Tour_Parapet_E", t, 199.4, 15, 48, 200, 35, 49.2, "beton_sombre")
boite("PORT_Tour_Edicule", t, 188, 18, 48, 194, 24, 52, "beton_sombre")
boite("PORT_Poste_Garde", t, 196, 2, 0, 200, 8, 3, "beton")
boite("PORT_Bureau_Quai", t, 120, QUAI_Y - 20, 0, 132, QUAI_Y - 12, 6, "tole_mur")
prisme_toit("PORT_Bureau_Quai_Toit", t, 119.5, QUAI_Y - 20.5, 132.5, QUAI_Y - 11.5, 6, 1.5, "toit_rouille")

# ---------------------------------------------------------------- BATEAUX AMARRÉS
b = "PORT/BATEAUX"
boite("PORT_Cargo_Coque", b, 30, QUAI_Y + 4, -QUAI_HAUT - 4, 110, QUAI_Y + 20, 3, "coque")
boite("PORT_Cargo_Pont", b, 30, QUAI_Y + 4, 3, 110, QUAI_Y + 20, 3.3, "pont_navire")
boite("PORT_Cargo_Chateau", b, 96, QUAI_Y + 6, 3.3, 108, QUAI_Y + 18, 15, "c_blanc")
for i in range(5):
    for j in range(2):
        o = bpy.data.objects.new("PORT_Cargo_Conteneur_%02d" % (i * 2 + j + 1), me_c)
        o.location = (40 + i * 11 + L / 2 - 6, QUAI_Y + 8 + j * 4 + l / 2, 3.3)
        o.scale = (10, l, h)
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = materiau(CC[(i + j) % len(CC)])
        collection(b).objects.link(o)
boite("PORT_Remorqueur", b, 140, QUAI_Y + 5, -QUAI_HAUT - 1.5, 156, QUAI_Y + 11, 1.5, "coque_rouge")
boite("PORT_Remorqueur_Cabine", b, 148, QUAI_Y + 6.5, 1.5, 153, QUAI_Y + 9.5, 4.5, "c_blanc")

# ---------------------------------------------------------------- CLÔTURES (grillage) + portail
f = "PORT/DECORATIONS"
for nom, a in (("Sud", (-10, -10.2, 186, -10)), ("Sud_Est", (195, -10.2, PORT_L + 10, -10)),
               ("Ouest", (-10.2, -10, -10, QUAI_Y - 22)), ("Est", (PORT_L + 10, -10, PORT_L + 10.2, QUAI_Y - 22))):
    boite("PORT_Grillage_" + nom, f, a[0], a[1], 0, a[2], a[3], 2.5, "grillage")
boite("PORT_Barriere_Entree", f, 186, -9, 1.0, 195, -8.8, 1.15, "jaune")
for i, (x, y) in enumerate(((30, 58), (75, 58), (120, 58), (165, 58), (30, 70), (165, 70))):     # lampadaires
    cylindre("PORT_Lampadaire_%02d" % (i + 1), f, x, y, 0, 9, 0.15, "acier")

# ---------------------------------------------------------------- COLLISIONS PRÉVISIONNELLES (vide pour l'instant)
collection("PORT/COLLISIONS_PREVISIONNELLES")
for nom in ("VEGETATION",):
    collection("PORT/" + nom)

# ---------------------------------------------------------------- affichage léger (Solid) + aperçus
for area_screen in bpy.data.screens:
    for area in area_screen.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "SOLID"
                    sp.shading.color_type = "MATERIAL"
                    sp.clip_end = 3000
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_shadows = True
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.world = sc.world or bpy.data.worlds.new("Monde")
sc.world.color = (0.32, 0.24, 0.26)

APERCUS = os.path.join(ICI, "apercus")
os.makedirs(APERCUS, exist_ok=True)
cam_data = bpy.data.cameras.new("PORT_Camera")
cam_data.clip_end = 3000
cam = bpy.data.objects.new("PORT_Camera", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def vue(nom, pos, cible, ortho=None):
    cam.location = pos
    d = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    cam_data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam_data.ortho_scale = ortho
    else:
        cam_data.lens = 24
    sc.render.filepath = os.path.join(APERCUS, nom + ".png")
    bpy.ops.render.render(write_still=True)


vue("port_vue_aerienne", (260, -90, 150), (100, 85, 0))
vue("port_plan_dessus", (100, 90, 400), (100, 90.01, 0), ortho=300)
vue("port_depuis_le_toit_de_la_tour", (186.5, 33, 51.5), (95, 105, 8))
vue("port_au_sol_route", (20, 64, 1.7), (120, 64, 4))
vue("port_interieur_hangar", (75, 38, 1.7), (60, 20, 3))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ICI, "port_blockout.blend"))
print("PORT : %d objets, %d conteneurs -> port_blockout.blend" % (len(bpy.data.objects), compte))

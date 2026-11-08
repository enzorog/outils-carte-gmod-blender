"""
PORT INDUSTRIEL — VERSION DÉTAILLÉE (test « tout Blender »), univers JJK RP.
Même disposition que le blockout validé (4 hangars au sud, route est-ouest, parc à conteneurs, grue + quai + cargo au
nord, tour de bureaux à l'est). Textures maison (textures_port.py), modèles détaillés, lumière du soir.
Architecture INTACTE.

Lancer : "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --factory-startup --python creer_port_detail.py
Résultat : port.blend + apercus/detail_*.png   (relançable, aucun doublon)
Unités : mètres. X = est, Y = nord, Z = haut. Eau au nord.
"""
import bpy, math, os, random

ICI = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ICI, "textures")
TEX_JEU = os.path.join(ICI, "textures_jeu")   # vraies textures de CS:S / HL2 (textures_jeu.py)

# ---------------------------------------------------------------- dimensions (validées au blockout)
PORT_L = 200.0
QUAI_Y = 150.0
QUAI_HAUT = 2.5
HANGAR = dict(l=40.0, p=25.0, h=12.0, mur=0.3, porte_l=9.0, porte_h=7.0)
HANGARS_X = [5.0, 50.0, 95.0, 140.0]
HANGAR_Y = 15.0
CONT = (12.19, 2.44, 2.59)
ROUTE_Y, ROUTE_L = 60.0, 9.0

# ================================================================== MATÉRIAUX
MATS = {}


def mat_image(nom, fichier, tuile=2.0, rugosite=0.8, metal=0.0, emission=0.0, teinte_objet=False, alpha=False, couleur=None):
    """matériau à texture projetée en boîte (coordonnées de l'objet en mètres / tuile)"""
    if nom in MATS:
        return MATS[nom]
    m = bpy.data.materials.new("PORT_" + nom)
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    bsdf = n.get("Principled BSDF")
    coord = n.new("ShaderNodeTexCoord")
    mapping = n.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / tuile, 1 / tuile, 1 / tuile)
    img = n.new("ShaderNodeTexImage")
    chemin = os.path.join(TEX_JEU, fichier + ".png")
    if not os.path.exists(chemin):
        chemin = os.path.join(TEX, fichier + ".png")
    img.image = bpy.data.images.load(chemin, check_existing=True)
    img.projection = "BOX"
    img.projection_blend = 0.15
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], img.inputs["Vector"])
    sortie = img.outputs["Color"]
    if teinte_objet:                                           # couleur de l'objet x texture grise (conteneurs)
        info = n.new("ShaderNodeObjectInfo")
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(sortie, mix.inputs[6])
        nt.links.new(info.outputs["Color"], mix.inputs[7])
        sortie = mix.outputs[2]
    nt.links.new(sortie, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rugosite
    bsdf.inputs["Metallic"].default_value = metal
    if emission:
        nt.links.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha:
        nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
    m.diffuse_color = couleur or (0.4, 0.4, 0.4, 1)
    MATS[nom] = m
    return m


def mat_uni(nom, rgb, rugosite=0.7, metal=0.0, emission=0.0, alpha=1.0):
    if nom in MATS:
        return MATS[nom]
    m = bpy.data.materials.new("PORT_" + nom)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rugosite
    b.inputs["Metallic"].default_value = metal
    if emission:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*rgb, 1)
    MATS[nom] = m
    return m


def mat_uv(nom, fichier, rugosite=0.6, metal=0.3, alpha=False):
    """matériau qui suit les UV du modèle (conteneurs : atlas de la texture du jeu ; décalques avec transparence)"""
    if nom in MATS:
        return MATS[nom]
    m = bpy.data.materials.new("PORT_" + nom)
    m.use_nodes = True
    n = m.node_tree.nodes
    bsdf = n.get("Principled BSDF")
    img = n.new("ShaderNodeTexImage")
    chemin = os.path.join(TEX_JEU, fichier + ".png")
    if not os.path.exists(chemin):
        chemin = os.path.join(TEX, fichier + ".png")
    img.image = bpy.data.images.load(chemin, check_existing=True)
    m.node_tree.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        m.node_tree.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = rugosite
    bsdf.inputs["Metallic"].default_value = metal
    MATS[nom] = m
    return m


def preparer_materiaux():
    # sols, murs, toits, métal : vraies textures du jeu (CS:S, HL2)
    mat_image("beton_sol", "beton_sol", 4, 0.9)
    mat_image("beton_sol2", "beton_sol2", 4, 0.9)
    mat_image("asphalte", "route", 4, 0.95)
    mat_image("terre", "terre", 3, 1.0)
    mat_image("tole_grise", "tole_grise", 4, 0.65, 0.4)
    mat_image("tole_bleue", "tole_bleue", 4, 0.6, 0.4)
    mat_image("tole_beige", "tole_beige", 4, 0.65, 0.4)
    mat_image("tole_brune", "tole_brune", 4, 0.65, 0.4)
    mat_image("carton", "carton", 1.0, 0.9)
    mat_image("tole_toit", "tole_toit", 3, 0.75, 0.3)
    mat_image("rideau", "rideau", 4, 0.6, 0.4)
    mat_image("acier_rouge", "acier_rouge", 1.0, 0.6, 0.3)
    mat_image("acier_gris", "acier_gris", 2, 0.55, 0.5)
    mat_image("acier_jaune", "acier_jaune", 2, 0.6, 0.3)
    mat_image("beton_mur", "beton_mur", 4, 0.9)
    mat_image("coque", "coque", 6, 0.6, 0.3)
    mat_image("bois", "bois", 1.2, 0.85)
    mat_image("grillage", "grillage", 2, 0.5, 0.7, alpha=True)
    mat_image("facade", "facade", 3.5, 0.4, 0.1)
    mat_image("facade2", "facade2", 3.5, 0.5, 0.1)
    mat_image("facade3", "facade3", 3.5, 0.5, 0.1)
    mat_image("facade4", "facade4", 3.5, 0.5, 0.1)
    mat_image("ville", "ville_nuit", 40, 0.9, 0, emission=0.9)
    mat_image("marquage", "marquage", 1, 0.8)
    mat_image("rayures", "rayures", 1, 0.8)
    for k in range(1, 6):
        mat_uv("conteneur_%d" % k, "conteneur_%d" % k)
    for nom in ("dec_tache_huile", "dec_flaque", "dec_traces_pneus", "dec_numero_1", "dec_numero_2", "dec_numero_3", "dec_numero_4"):
        mat_uv(nom, nom, 0.2 if nom == "dec_flaque" else 0.8, 0.0, alpha=True)
    mat_uv("panneau_port", "panneau_port", 0.6, 0.2)
    mat_uv("panneau_danger", "panneau_danger", 0.6, 0.2)
    mat_image("cabine", "cabine", 2.5, 0.7, 0.2)
    mat_image("carrosserie_bleue", "carrosserie_bleue", 2, 0.4, 0.5)
    mat_image("carrosserie_blanche", "carrosserie_blanche", 2, 0.4, 0.5)
    mat_image("carrosserie_orange", "carrosserie_orange", 2, 0.4, 0.5)
    mat_uni("blanc_sol", (0.75, 0.74, 0.70), 0.8)
    mat_uni("caoutchouc", (0.03, 0.03, 0.03), 0.9)
    mat_uni("vitre", (0.05, 0.07, 0.09), 0.05, 0.6)
    mat_uni("lampe", (1.0, 0.72, 0.42), 0.5, 0, emission=12.0)
    mat_uni("eau", (0.02, 0.05, 0.06), 0.06, 0.0)
    mat_uni("peinture_blanche", (0.70, 0.70, 0.66), 0.6)
    mat_uni("cone", (0.85, 0.30, 0.05), 0.6)
    mat_uni("caisse_grise", (0.30, 0.30, 0.31), 0.55, 0.3)
    mat_uni("carrosserie_rouge", (0.42, 0.05, 0.05), 0.35, 0.4)
    mat_uni("acier_bleu", (0.05, 0.16, 0.42), 0.45, 0.6)
    mat_uni("acier_orange", (0.85, 0.33, 0.04), 0.45, 0.5)
    mat_uni("peinture_jaune", (0.85, 0.62, 0.05), 0.7)
    mat_uni("jante", (0.45, 0.45, 0.47), 0.35, 0.8)
    mat_uni("sodium", (1.0, 0.55, 0.18), 0.5, 0, emission=5.0)
    mat_uni("secours", (0.1, 0.9, 0.3), 0.5, 0, emission=8.0)
    mat_uni("film", (0.8, 0.82, 0.85), 0.15, 0.0, alpha=0.55)


# ================================================================== GÉOMÉTRIE
COLL = {}


def collection(chemin):
    if chemin in COLL:
        return COLL[chemin]
    parent = bpy.context.scene.collection
    acc = ""
    for part in ["JJK_RP"] + chemin.split("/"):
        acc = part if not acc else acc + "/" + part
        c = COLL.get(acc)
        if not c:
            c = bpy.data.collections.new(part if part in ("JJK_RP", "PORT") else "PORT_" + part)
            parent.children.link(c)
            COLL[acc] = c
        parent = c
    COLL[chemin] = parent
    return parent


def objet(nom, coll, v, f, mat, origine=(0, 0, 0)):
    me = bpy.data.meshes.new(nom)
    me.from_pydata(v, [], f)
    me.update()
    if isinstance(mat, str):
        mat = MATS[mat]
    me.materials.append(mat)
    o = bpy.data.objects.new(nom, me)
    o.location = origine
    collection(coll).objects.link(o)
    return o


def boite(nom, coll, x0, y0, z0, x1, y1, z1, mat):
    """boîte aux vraies dimensions (origine au coin bas : la texture garde son échelle)"""
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    v = [(0, 0, 0), (dx, 0, 0), (dx, dy, 0), (0, dy, 0), (0, 0, dz), (dx, 0, dz), (dx, dy, dz), (0, dy, dz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return objet(nom, coll, v, f, mat, (x0, y0, z0))


def poutre(nom, coll, a, b, s, mat):
    """poutre carrée (section s) entre deux points 3D (treillis de la grue, diagonales)"""
    ax, ay, az = a
    dx, dy, dz = b[0] - ax, b[1] - ay, b[2] - az
    l = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
    u = (dx / l, dy / l, dz / l)
    ref = (0, 0, 1) if abs(u[2]) < 0.9 else (1, 0, 0)
    v1 = (u[1] * ref[2] - u[2] * ref[1], u[2] * ref[0] - u[0] * ref[2], u[0] * ref[1] - u[1] * ref[0])
    n1 = math.sqrt(sum(c * c for c in v1))
    v1 = tuple(c / n1 * s / 2 for c in v1)
    v2 = (u[1] * v1[2] - u[2] * v1[1], u[2] * v1[0] - u[0] * v1[2], u[0] * v1[1] - u[1] * v1[0])
    coins = [tuple(v1[i] * p + v2[i] * q for i in range(3)) for p, q in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    v = [c for c in coins] + [(c[0] + dx, c[1] + dy, c[2] + dz) for c in coins]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return objet(nom, coll, v, f, mat, a)


def toit(nom, coll, x0, y0, x1, y1, z, h, mat):
    ym = (y0 + y1) / 2
    v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), (x0, ym, z + h), (x1, ym, z + h),
         (x0, y0, z - 0.15), (x1, y0, z - 0.15), (x1, y1, z - 0.15), (x0, y1, z - 0.15)]
    f = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (6, 9, 8, 7), (0, 6, 7, 1), (2, 8, 9, 3), (0, 3, 9, 6), (1, 7, 8, 2)]
    return objet(nom, coll, v, f, mat)


def cylindre(nom, coll, x, y, z0, z1, r, mat, seg=14):
    v, f = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v += [(r * math.cos(a), r * math.sin(a), 0), (r * math.cos(a), r * math.sin(a), z1 - z0)]
    for k in range(seg):
        a, b = 2 * k, 2 * ((k + 1) % seg)
        f.append((a, b, b + 1, a + 1))
    f.append(tuple(2 * k for k in reversed(range(seg))))
    f.append(tuple(2 * k + 1 for k in range(seg)))
    return objet(nom, coll, v, f, mat, (x, y, z0))


def escalier(nom, coll, x0, x1, y0, z0, z1, sens=1, pas=0.28, haut=0.18, mat="acier_gris"):
    """escalier droit (marches pleines) qui monte vers +Y (sens=1) ou -Y"""
    n = max(1, int((z1 - z0) / haut))
    for k in range(n):
        ya = y0 + sens * k * pas
        boite("%s_%02d" % (nom, k + 1), coll, x0, ya, z0 + k * haut, x1, ya + sens * pas, z0 + (k + 1) * haut, mat)
    return y0 + sens * n * pas


def garde_corps(nom, coll, a, b, z, h=1.0, mat="acier_jaune"):
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(l // 1.5))
    for k in range(n + 1):
        f = k / n
        x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        boite("%s_Poteau_%02d" % (nom, k), coll, x - 0.03, y - 0.03, z, x + 0.03, y + 0.03, z + h, mat)
    poutre(nom + "_Lisse", coll, (a[0], a[1], z + h), (b[0], b[1], z + h), 0.06, mat)
    poutre(nom + "_Sous_Lisse", coll, (a[0], a[1], z + h / 2), (b[0], b[1], z + h / 2), 0.04, mat)


# ================================================================== SCÈNE
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"
preparer_materiaux()
rnd = random.Random(2026)

import addon_utils
from mathutils import Matrix, Vector
try:
    addon_utils.enable("SourceIO-master", default_set=False)
    SOURCEIO = hasattr(bpy.ops, "sourceio") and hasattr(bpy.ops.sourceio, "mdl")
except Exception:
    SOURCEIO = False
MODELES_JEU = os.path.join(ICI, "modeles_jeu")                     # rempli par extraire_modeles.py
SOURCES = {}
COLL_SOURCES = "PORT_Modeles_Jeu_Sources"


def source_modele(chemin):
    """importe un .mdl du jeu une seule fois (gardé caché) ; renvoie (objets, point bas-centre) ou None"""
    if chemin in SOURCES:
        return SOURCES[chemin]
    f = os.path.join(MODELES_JEU, chemin + ".mdl")
    SOURCES[chemin] = None
    if not (SOURCEIO and os.path.exists(f)):
        print("modèle absent (objet maison à la place) :", chemin)
        return None
    avant = set(bpy.data.objects)
    bpy.ops.sourceio.mdl(filepath=f, directory=os.path.dirname(f) + os.sep, files=[{"name": os.path.basename(f)}],
                         discover_resources=True, import_textures=True, import_physics=False, scale=0.0254)
    nouv = [o for o in bpy.data.objects if o not in avant]
    if COLL_SOURCES not in bpy.data.collections:
        bpy.context.scene.collection.children.link(bpy.data.collections.new(COLL_SOURCES))
    cs = bpy.data.collections[COLL_SOURCES]
    for o in nouv:
        for c_ in list(o.users_collection):
            c_.objects.unlink(o)
        cs.objects.link(o)
    bpy.context.view_layer.update()
    maillages = [o for o in nouv if o.type == "MESH"]
    if not maillages:
        return None
    pts = [o.matrix_world @ Vector(c_) for o in maillages for c_ in o.bound_box]
    bas = Vector(((min(q.x for q in pts) + max(q.x for q in pts)) / 2, (min(q.y for q in pts) + max(q.y for q in pts)) / 2, min(q.z for q in pts)))
    SOURCES[chemin] = (maillages, bas)
    return SOURCES[chemin]


def modele(nom, coll, chemin, x, y, z=0.0, rot=0.0, ry=0.0):
    """pose une copie du modèle du jeu, son bas-centre en (x, y, z), tourné de rot autour de Z ; False si absent"""
    src = source_modele(chemin)
    if not src:
        return False
    maillages, bas = src
    m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
    if ry:                                                          # couché : on remet le bas au sol
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Translation((0, 0, 0.0)) @ Matrix.Rotation(ry, 4, "Y")
    for o in maillages:
        n = o.copy()
        n.name = nom
        n.parent = None
        for md in list(n.modifiers):
            n.modifiers.remove(md)
        n.matrix_world = m @ Matrix.Translation(-bas) @ o.matrix_world
        n["mdl"] = chemin + ".mdl"                                  # pour l'export GMod : ce sera un prop_static
        collection(coll).objects.link(n)
    return True


def fut(nom, c, x, y, z):
    if not modele(nom, c, rnd.choice(("models/props_c17/oildrum001", "models/props_c17/oildrum001", "models/props_borealis/bluebarrel001", "models/props/cs_assault/barrelwarning")), x, y, z, rnd.uniform(0, 6.28)):
        cylindre(nom, c, x, y, z, z + 0.95, 0.3, rnd.choice(("acier_rouge", "acier_jaune")))


def caisse(nom, c, x, y, z, rot=0.0):
    """caisse en bois du jeu (1 m) posée bas-centre en (x, y, z)"""
    if not modele(nom, c, "models/props_junk/wood_crate001a", x, y, z, rot):
        boite(nom, c, x - 0.5, y - 0.5, z, x + 0.5, y + 0.5, z + 1.0, "bois")


def prisme(nom, coll, pts, y0, y1, mat):
    """polygone convexe (x, z) extrudé de y0 à y1 (voûtes, ventilateurs du tunnel)"""
    n = len(pts)
    v = []
    for x, z in pts:
        v += [(x, y0, z), (x, y1, z)]
    f = [tuple(2 * i for i in range(n)), tuple(2 * i + 1 for i in reversed(range(n)))]
    for i in range(n):
        j = (i + 1) % n
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    return objet(nom, coll, v, f, mat)


def lumiere(nom, coll, pos, puissance, couleur, rayon=0.3):
    li = bpy.data.lights.new(nom, "POINT")
    li.energy, li.color = puissance, couleur
    li.shadow_soft_size = rayon
    o = bpy.data.objects.new(nom, li)
    o.location = pos
    collection(coll).objects.link(o)
    return o


def rayonnage(nom, c, xa, ya, xb, yb, niveaux, ecart=1.85):
    """rayonnage de stockage (montants bleus, lisses orange, planchers en bois) chargé au hasard"""
    le_long_x = (xb - xa) > (yb - ya)
    longueur = (xb - xa) if le_long_x else (yb - ya)
    travees = max(1, int(longueur // 2.7))
    pas = longueur / travees
    for k in range(travees + 1):
        for cote in (0, 1):
            if le_long_x:
                xx, yy = xa + k * pas, (ya, yb - 0.1)[cote]
                boite("%s_Montant_%d_%d" % (nom, k, cote), c, xx - 0.05, yy, 0.12, xx + 0.05, yy + 0.1, niveaux * ecart + 0.3, "acier_bleu")
            else:
                xx, yy = (xa, xb - 0.1)[cote], ya + k * pas
                boite("%s_Montant_%d_%d" % (nom, k, cote), c, xx, yy - 0.05, 0.12, xx + 0.1, yy + 0.05, niveaux * ecart + 0.3, "acier_bleu")
    for n_ in range(niveaux):
        z = 0.25 + n_ * ecart
        boite("%s_Niveau_%d" % (nom, n_), c, xa, ya, z - 0.12, xb, yb, z, "acier_orange")
        for k in range(travees):
            r = rnd.random()
            if r < 0.15:
                continue
            a = (xa + k * pas + 0.15) if le_long_x else xa + 0.1
            b = (ya + 0.1) if le_long_x else (ya + k * pas + 0.15)
            la = (pas - 0.3) if le_long_x else (xb - xa - 0.2)
            lb = (yb - ya - 0.2) if le_long_x else (pas - 0.3)
            hmax = ecart - 0.35
            if r < 0.55:                                            # cartons empilés
                for j in range(rnd.randint(1, 3)):
                    hh = hmax / 3
                    boite("%s_Carton_%d_%d_%d" % (nom, n_, k, j), c, a + 0.05 * j, b, z + j * hh, a + la - 0.05 * j, b + lb, z + (j + 1) * hh - 0.03, "carton")
            elif r < 0.8:                                           # caisse en bois
                for j in range(2):
                    if la > lb:
                        caisse("%s_Caisse_%d_%d_%d" % (nom, n_, k, j), c, a + la * (0.27 + 0.46 * j), b + lb / 2, z)
                    else:
                        caisse("%s_Caisse_%d_%d_%d" % (nom, n_, k, j), c, a + la / 2, b + lb * (0.27 + 0.46 * j), z)
            else:                                                   # fûts
                for j in range(2):
                    if le_long_x:
                        fut("%s_Fut_%d_%d_%d" % (nom, n_, k, j), c, a + 0.4 + j * (la - 0.8), b + lb / 2, z)
                    else:
                        fut("%s_Fut_%d_%d_%d" % (nom, n_, k, j), c, a + la / 2, b + 0.4 + j * (lb - 0.8), z)


def palette_chargee(nom, c, x, y, z=0.12):
    """palette en bois + pile de cartons filmée"""
    if modele(nom, c, rnd.choice(("models/props/cs_assault/moneypallet", "models/props/cs_assault/moneypallet03")), x + 0.8, y + 0.8, z, rnd.choice((0, 1.5708, 3.1416))):
        return
    boite(nom + "_Palette", c, x, y, z, x + 1.2, y + 1.0, z + 0.15, "bois")
    hh = rnd.choice((0.6, 0.9, 1.2, 1.5))
    boite(nom + "_Cartons", c, x + 0.05, y + 0.05, z + 0.15, x + 1.15, y + 0.95, z + 0.15 + hh, "carton")
    if rnd.random() < 0.6:
        boite(nom + "_Film", c, x + 0.03, y + 0.03, z + 0.15, x + 1.17, y + 0.97, z + 0.17 + hh, "film")


# ---------------------------------------------------------------- TERRAIN, ROUTES, MARQUAGES
boite("PORT_Terrain", "PORT/TERRAIN", -10, -10, -1, PORT_L + 10, QUAI_Y, 0, "beton_sol")
boite("PORT_Terre_Ouest", "PORT/TERRAIN", 0, 70, 0, 18, 126, 0.03, "terre")
boite("PORT_Terre_Est", "PORT/TERRAIN", 182, 70, 0, 200, 126, 0.03, "terre")
boite("PORT_Route_EstOuest", "PORT/ROUTES", -10, ROUTE_Y, 0.0, PORT_L + 10, ROUTE_Y + ROUTE_L, 0.06, "asphalte")
boite("PORT_Route_VersQuai", "PORT/ROUTES", 96, ROUTE_Y + ROUTE_L, 0.0, 96 + ROUTE_L, QUAI_Y - 22, 0.06, "asphalte")
TUNNEL_X0, TUNNEL_X1 = 182.0, 191.0                                # la seule entrée / sortie du port
boite("PORT_Route_Entree", "PORT/ROUTES", TUNNEL_X0, -10, 0.0, TUNNEL_X1, ROUTE_Y, 0.06, "asphalte")
for i, x in enumerate(range(0, int(PORT_L), 8)):
    boite("PORT_Marquage_Axe_%02d" % i, "PORT/ROUTES", x, ROUTE_Y + 4.35, 0.06, x + 4, ROUTE_Y + 4.65, 0.07, "marquage")
for i, x in enumerate(range(10, 180, 3)):                         # places de stationnement des camions (côté hangars)
    boite("PORT_Marquage_Place_%02d" % i, "PORT/ROUTES", x, 50, 0.0, x + 0.12, 58, 0.02, "blanc_sol")
for k, y in enumerate((ROUTE_Y + ROUTE_L + 0.4, QUAI_Y - 22.4)):  # bandes jaunes de sécurité
    boite("PORT_Bande_Securite_%d" % k, "PORT/ROUTES", -10, y, 0.0, PORT_L + 10, y + 0.35, 0.03, "rayures")

# ---------------------------------------------------------------- QUAI + EAU
q = "PORT/QUAIS"
boite("PORT_Quai_Principal", q, -10, QUAI_Y - 22, 0.0, PORT_L + 10, QUAI_Y, 0.08, "beton_sol")
boite("PORT_Quai_Mur", q, -10, QUAI_Y - 1.2, -QUAI_HAUT - 4, PORT_L + 10, QUAI_Y, 0.0, "beton_mur")
boite("PORT_Quai_Bordure", q, -10, QUAI_Y - 0.5, 0.08, PORT_L + 10, QUAI_Y, 0.3, "rayures")
boite("PORT_Sol_Parc_Conteneurs", "PORT/TERRAIN", 18, 72, 0.0, 182, 126, 0.02, "beton_sol2")
boite("PORT_Eau", q, -300, QUAI_Y, -QUAI_HAUT - 4, PORT_L + 300, QUAI_Y + 400, -QUAI_HAUT, "eau")
for i, x in enumerate(range(4, int(PORT_L), 10)):
    cylindre("PORT_Bollard_%02d" % i, q, x, QUAI_Y - 1.0, 0.08, 0.7, 0.28, "acier_jaune")
    cylindre("PORT_Bollard_Tete_%02d" % i, q, x, QUAI_Y - 1.0, 0.7, 0.85, 0.38, "acier_jaune")
for i, x in enumerate(range(8, int(PORT_L), 9)):                  # défenses en caoutchouc sur le mur du quai
    boite("PORT_Defense_%02d" % i, q, x - 0.9, QUAI_Y, -QUAI_HAUT - 1, x + 0.9, QUAI_Y + 0.6, -0.3, "caoutchouc")
for i, x in enumerate((25, 85, 135, 175)):                         # échelles vers l'eau
    for k in range(10):
        boite("PORT_Echelle_%d_Barreau_%02d" % (i, k), q, x - 0.3, QUAI_Y, -QUAI_HAUT - 1 + k * 0.35, x + 0.3, QUAI_Y + 0.1, -QUAI_HAUT - 0.96 + k * 0.35, "acier_gris")
    for s in (-0.3, 0.3):
        boite("PORT_Echelle_%d_Montant_%s" % (i, "G" if s < 0 else "D"), q, x + s - 0.04, QUAI_Y, -QUAI_HAUT - 1, x + s + 0.04, QUAI_Y + 0.12, 0.9, "acier_gris")

# ---------------------------------------------------------------- HANGARS (détaillés)
H = HANGAR
for n, hx in enumerate(HANGARS_X, 1):
    nom = "PORT_Hangar_%02d" % n
    c = "PORT/HANGARS/" + nom
    x0, y0, x1, y1 = hx, HANGAR_Y, hx + H["l"], HANGAR_Y + H["p"]
    e = H["mur"]
    murs = ("tole_grise", "tole_bleue", "tole_beige", "tole_brune")[(n - 1) % 4]
    THEME = ("entrepot", "garage", "colis", "planque")[(n - 1) % 4]
    pm = (x0 + x1) / 2
    boite(nom + "_Dalle", c, x0, y0, 0.0, x1, y1, 0.12, "beton_sol")
    # socle de béton (1 m) + bardage en tôle
    for s, a in (("N", (x0, y1 - e, x1, y1)), ("S", (x0, y0, x1, y0 + e)), ("O", (x0, y0, x0 + e, y1)), ("E", (x1 - e, y0, x1, y1))):
        if s == "N":
            boite(nom + "_Socle_N_G", c, x0, y1 - e - 0.05, 0, pm - H["porte_l"] / 2, y1 + 0.05, 1.0, "beton_mur")
            boite(nom + "_Socle_N_D", c, pm + H["porte_l"] / 2, y1 - e - 0.05, 0, x1, y1 + 0.05, 1.0, "beton_mur")
        else:
            boite(nom + "_Socle_" + s, c, a[0] - 0.05, a[1] - 0.05, 0, a[2] + 0.05, a[3] + 0.05, 1.0, "beton_mur")
    boite(nom + "_Facade_G", c, x0, y1 - e, 1.0, pm - H["porte_l"] / 2, y1, H["h"], murs)
    boite(nom + "_Facade_D", c, pm + H["porte_l"] / 2, y1 - e, 1.0, x1, y1, H["h"], murs)
    boite(nom + "_Facade_Haut", c, pm - H["porte_l"] / 2, y1 - e, H["porte_h"], pm + H["porte_l"] / 2, y1, H["h"], murs)
    boite(nom + "_Mur_Sud", c, x0, y0, 1.0, x1, y0 + e, H["h"], murs)
    boite(nom + "_Mur_Ouest", c, x0, y0, 1.0, x0 + e, y1, H["h"], murs)
    boite(nom + "_Mur_Est", c, x1 - e, y0, 1.0, x1, y1, H["h"], murs)
    # pignons (triangles sous le toit)
    for s, xx in (("O", x0), ("E", x1 - e)):
        ym = (y0 + y1) / 2
        v = [(0, y0, H["h"]), (0, y1, H["h"]), (0, ym, H["h"] + 3.5), (e, y0, H["h"]), (e, y1, H["h"]), (e, ym, H["h"] + 3.5)]
        objet(nom + "_Pignon_" + s, c, v, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], murs, (xx, 0, 0))
    # porte roulante à moitié levée + encadrement
    boite(nom + "_Rideau_Metallique", c, pm - H["porte_l"] / 2, y1 - 0.15, H["porte_h"] - 1.4, pm + H["porte_l"] / 2, y1 + 0.05, H["porte_h"], "rideau")
    boite(nom + "_Coffre_Rideau", c, pm - H["porte_l"] / 2 - 0.2, y1, H["porte_h"], pm + H["porte_l"] / 2 + 0.2, y1 + 0.6, H["porte_h"] + 0.6, "acier_gris")
    for s in (-1, 1):
        boite(nom + "_Montant_Porte_%d" % s, c, pm + s * H["porte_l"] / 2 - 0.15, y1 - 0.1, 0, pm + s * H["porte_l"] / 2 + 0.15, y1 + 0.25, H["porte_h"], "acier_jaune")
    boite(nom + "_Porte_Pietons", c, x1 - 0.05, y0 + 4, 0.12, x1 + 0.08, y0 + 5.2, 2.3, "acier_gris")
    boite(nom + "_Auvent_Porte", c, x1, y0 + 3.6, 2.6, x1 + 1.1, y0 + 5.6, 2.75, "tole_grise")
    # poteaux métalliques extérieurs tous les 5 m, gouttières, descentes d'eau
    for k in range(9):
        xx = x0 + k * 5
        for yy in (y0 - 0.3, y1):
            if abs(xx - pm) > H["porte_l"] / 2 + 0.3 or yy < y1 - 1:
                boite("%s_Poteau_%d_%s" % (nom, k, "S" if yy < y0 else "N"), c, xx - 0.15, yy, 0, xx + 0.15, yy + 0.3, H["h"], "acier_gris")
    toit(nom + "_Toit", c, x0 - 0.8, y0 - 0.8, x1 + 0.8, y1 + 0.8, H["h"], 3.5, "tole_toit")
    for s, yy in (("S", y0 - 1.1), ("N", y1 + 0.8)):
        boite(nom + "_Gouttiere_" + s, c, x0 - 0.8, yy, H["h"] - 0.35, x1 + 0.8, yy + 0.3, H["h"] - 0.05, "acier_gris")
        for xx in (x0 - 0.6, x1 + 0.4):
            boite("%s_Descente_%s_%d" % (nom, s, int(xx)), c, xx, yy + 0.05, 0, xx + 0.2, yy + 0.25, H["h"] - 0.3, "acier_gris")
    # lanterneaux (bandes vitrées) sur le toit
    for k in range(3):
        xx = x0 + 6 + k * 12
        poutre("%s_Lanterneau_%d" % (nom, k), c, (xx, y0 + 4, H["h"] + 1.2), (xx + 6, y0 + 4, H["h"] + 1.2), 0.9, "vitre")
    # escalier extérieur vers le toit (côté ouest) + palier + garde-corps sur le toit
    ys0, ys1 = y0 - 3.1, y0 - 1.9                                  # bande de l'escalier, au-delà de l'avancée du toit
    for k in range(34):                                             # volée 1 : vers l'est, de 0 à 6 m
        xa = x0 + 3 + k * 0.28
        boite("%s_Esc_A_%02d" % (nom, k), c, xa, ys0, 0, xa + 0.28, ys1, (k + 1) * 0.176, "acier_gris")
    xp = x0 + 3 + 34 * 0.28
    boite(nom + "_Palier_Ext", c, xp, ys0, 5.85, xp + 1.4, ys1, 6.0, "acier_gris")
    for k in range(34):                                             # volée 2 : de 6 à 12 m
        xa = xp + 1.4 + k * 0.28
        boite("%s_Esc_B_%02d" % (nom, k), c, xa, ys0, 6.0 + k * 0.176, xa + 0.28, ys1, 6.0 + (k + 1) * 0.176, "acier_gris")
    xh = xp + 1.4 + 34 * 0.28
    boite(nom + "_Palier_Toit", c, xh, ys0, H["h"] - 0.15, xh + 2.0, y0 - 0.7, H["h"], "acier_gris")   # on passe sur le toit
    for k in range(30):                                             # poteaux sous l'escalier
        if k % 5 == 0:
            xa = x0 + 3 + k * 0.56
            boite("%s_Esc_Poteau_%02d" % (nom, k), c, xa, ys0 + 0.4, 0, xa + 0.15, ys0 + 0.55, min(H["h"], k * 0.352 + 0.2), "acier_gris")
    garde_corps(nom + "_GC_Esc", c, (x0 + 3, ys0 - 0.05), (xh + 2.0, ys0 - 0.05), 1.0)
    garde_corps(nom + "_GC_Toit", c, (x0 + 1, y0 + 1), (x1 - 1, y0 + 1), H["h"] + 0.4)
    # intérieur : fermes de charpente, mezzanine, palettes, fûts, lampes
    for k in range(1, 8):
        xx = x0 + k * 5
        poutre("%s_Ferme_Entrait_%d" % (nom, k), c, (xx, y0, H["h"] - 0.4), (xx, y1, H["h"] - 0.4), 0.25, "acier_gris")
        poutre("%s_Ferme_Arbaletrier_S_%d" % (nom, k), c, (xx, y0, H["h"] - 0.2), (xx, (y0 + y1) / 2, H["h"] + 3.2), 0.22, "acier_gris")
        poutre("%s_Ferme_Arbaletrier_N_%d" % (nom, k), c, (xx, y1, H["h"] - 0.2), (xx, (y0 + y1) / 2, H["h"] + 3.2), 0.22, "acier_gris")
        poutre("%s_Ferme_Poincon_%d" % (nom, k), c, (xx, (y0 + y1) / 2, H["h"] - 0.4), (xx, (y0 + y1) / 2, H["h"] + 3.2), 0.18, "acier_gris")
        if not modele("%s_Lampe_%d" % (nom, k), c, "models/props_c17/light_industrialbell01_on", xx, (y0 + y1) / 2, H["h"] - 1.6):
            boite("%s_Lampe_%d" % (nom, k), c, xx - 0.6, (y0 + y1) / 2 - 0.2, H["h"] - 1.2, xx + 0.6, (y0 + y1) / 2 + 0.2, H["h"] - 1.0, "lampe")
    boite(nom + "_Mezzanine", c, x0 + e, y0 + e, 5.0, x0 + 12, y1 - e, 5.25, "acier_gris")
    yfin_i = escalier(nom + "_Escalier_Int", c, x0 + 12.25, x0 + 13.65, y0 + 7.0, 0.12, 5.25, 1)
    boite(nom + "_Palier_Mezz", c, x0 + 12.0, yfin_i, 5.0, x0 + 13.65, yfin_i + 1.8, 5.25, "acier_gris")
    garde_corps(nom + "_GC_Mezz_A", c, (x0 + 12, y0 + 1), (x0 + 12, yfin_i - 0.1), 5.25)
    garde_corps(nom + "_GC_Mezz_B", c, (x0 + 12, yfin_i + 1.9), (x0 + 12, y1 - 1), 5.25)
    garde_corps(nom + "_GC_Esc_Int", c, (x0 + 13.7, y0 + 7.0), (x0 + 13.7, yfin_i + 1.8), 0.9)
    # --- intérieur rempli : rayonnages, îlots de palettes, bureau sous la mezzanine, établi, stock sur la mezzanine
    if THEME in ("entrepot", "colis"):
        rayonnage(nom + "_Rayon_Sud", c, x0 + 15, y0 + 0.5, x1 - 0.6, y0 + 1.7, 4)
    if THEME == "entrepot":
        rayonnage(nom + "_Rayon_Est", c, x1 - 1.7, y0 + 6.5, x1 - 0.5, y1 - 4.5, 4)
    rayonnage(nom + "_Rayon_Ouest", c, x0 + 0.4, y0 + 7.5, x0 + 1.6, y1 - 0.8, 2, 2.2)
    for i in range(3 if THEME in ("entrepot", "colis") else 0):    # îlots de palettes (côté est, hors de l'allée de la porte)
        for j in range(3):
            if rnd.random() < 0.85:
                palette_chargee("%s_Palette_%d_%d" % (nom, i, j), c, x0 + 26.5 + i * 1.8, y0 + 3.5 + j * 1.8)
    for i in range(2 if THEME != "garage" else 0):
        for j in range(4):
            if rnd.random() < 0.8:
                palette_chargee("%s_PaletteB_%d_%d" % (nom, i, j), c, x0 + 15.3 + i * 1.8, y0 + 3.5 + j * 1.8)
    # bureau vitré sous la mezzanine (coin sud-ouest)
    bx0, by0, bx1, by1 = x0 + 0.3, y0 + 0.3, x0 + 7.5, y0 + 6.2
    boite(nom + "_Bureau_Mur_N", c, bx0, by1 - 0.12, 0.12, bx1, by1, 1.0, "cabine")
    boite(nom + "_Bureau_Vitre_N", c, bx0, by1 - 0.08, 1.0, bx1 - 1.2, by1 - 0.04, 2.6, "vitre")
    boite(nom + "_Bureau_Mur_E", c, bx1 - 0.12, by0, 0.12, bx1, by1, 2.9, "cabine")
    boite(nom + "_Bureau_Porte", c, bx1 - 1.1, by1 - 0.14, 0.12, bx1 - 0.2, by1 - 0.1, 2.2, "acier_gris")
    boite(nom + "_Bureau_Plafond", c, bx0, by0, 2.9, bx1, by1, 3.0, "cabine")
    boite(nom + "_Bureau_Table", c, bx0 + 1, by0 + 1, 0.75, bx0 + 3, by0 + 2, 0.8, "bois")
    boite(nom + "_Bureau_Armoire", c, bx0 + 4.5, by0 + 0.1, 0.12, bx0 + 6.5, by0 + 0.6, 2.0, "acier_gris")
    lumiere(nom + "_Bureau_Lumiere", c, ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.7), 60, (1.0, 0.95, 0.85))
    # établi + panneau à outils (mur ouest, sous la mezzanine)
    boite(nom + "_Etabli", c, x0 + 3, y1 - 2.2, 0.9, x0 + 8, y1 - 1.3, 0.98, "bois")
    for xx in (x0 + 3.1, x0 + 7.8):
        boite("%s_Etabli_Pied_%d" % (nom, int(xx)), c, xx, y1 - 2.1, 0.12, xx + 0.1, y1 - 1.4, 0.9, "acier_gris")
    boite(nom + "_Panneau_Outils", c, x0 + 3, y1 - 0.42, 1.2, x0 + 8, y1 - 0.35, 2.4, "acier_gris")
    cylindre(nom + "_Bonbonne_1", c, x0 + 9, y1 - 1.5, 0.12, 1.6, 0.2, "acier_rouge")
    cylindre(nom + "_Bonbonne_2", c, x0 + 9.5, y1 - 1.4, 0.12, 1.6, 0.2, "acier_vert" if "acier_vert" in MATS else "acier_gris")
    # stock sur la mezzanine
    for k in range(10):
        px_, py_ = x0 + 1 + (k % 5) * 2.1, y0 + 2 + (k // 5) * 3.5
        if rnd.random() < 0.8:
            palette_chargee("%s_Mezz_Pal_%d" % (nom, k), c, px_, py_, 5.25)
    for k in range(6):
        fut("%s_Mezz_Fut_%d" % (nom, k), c, x0 + 1 + (k % 3) * 0.7, y1 - 2 - (k // 3) * 0.7, 5.25)
    # fûts près de la porte (côté ouest de l'allée), marquage jaune de l'allée
    for k in range(8):
        fut("%s_Fut_%d" % (nom, k), c, pm - 7.5 - (k % 4) * 0.7, y1 - 2 - (k // 4) * 0.7, 0.12)
    for xx in (pm - 5.6, pm + 5.4):
        boite("%s_Allee_%d" % (nom, int(xx)), c, xx, y0 + 2.2, 0.12, xx + 0.2, y1 - 0.4, 0.13, "peinture_jaune")
    for k in range(2):                                              # éclairage de travail
        lumiere("%s_Lumiere_%d" % (nom, k), c, (x0 + 12 + k * 16, (y0 + y1) / 2, H["h"] - 1.5), 700 if THEME == "planque" else 2500,
                (1.0, 0.6, 0.3) if THEME == "planque" else (1.0, 0.85, 0.65), 1.0)

# ---------------------------------------------------------------- CONTENEURS (5 modèles réutilisés, vraies textures de CS:S / HL2)
L, l, h = CONT
v = [(0, 0, 0), (L, 0, 0), (L, l, 0), (0, l, 0), (0, 0, h), (L, 0, h), (L, l, h), (0, l, h)]
faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
# zones de l'atlas (u0, v0, u1, v1) : flanc en haut, portes en bas à gauche, panneau nervuré à droite
FLANC, PORTES, PANNEAU = (0.0, 0.678, 1.0, 1.0), (0.0, 0.0, 0.522, 0.497), (0.532, 0.0, 0.762, 0.678)
ZONE_FACE = [PANNEAU, PANNEAU, FLANC, PORTES, FLANC, PANNEAU]
MODELES_C = []
for k in range(1, 6):
    me = bpy.data.meshes.new("PORT_Conteneur_Modele_%d" % k)
    me.from_pydata([(x - L / 2, y - l / 2, z) for x, y, z in v], [], faces)
    me.update()
    me.materials.append(MATS["conteneur_%d" % k])
    uv = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        u0, v0, u1, v1 = ZONE_FACE[poly.index]
        coins = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for j, li in enumerate(poly.loop_indices):
            uv.data[li].uv = coins[j]
    MODELES_C.append(me)
me_c = MODELES_C[0]
compte = 0
BLOCS_C = []
for by, nrang in ((76, 6), (100, 8)):
    for bx, ncol in ((20, 2), (49.6, 2), (79.2, 1), (109, 2), (138.6, 2), (168.2, 1)):
        BLOCS_C.append((bx, by, ncol, nrang))
for bx, by, ncol, nrang in BLOCS_C:
    for i in range(ncol):
        for j in range(nrang):
            for k in range(rnd.choice((1, 2, 2, 3))):
                compte += 1
                o = bpy.data.objects.new("PORT_Container_%03d" % compte, rnd.choice(MODELES_C))
                o.location = (bx + i * (L + 0.6) + L / 2, by + j * (l + 0.3) + l / 2, k * h)
                if rnd.random() < 0.5:
                    o.rotation_euler = (0, 0, math.pi)                  # portes d'un côté ou de l'autre
                collection("PORT/CONTENEURS").objects.link(o)

# ---------------------------------------------------------------- GRUE PORTIQUE en treillis
g = "PORT/GRUES"
gx, gy = 60.0, QUAI_Y - 18
pieds = [(gx, gy), (gx + 18, gy), (gx, gy + 14), (gx + 18, gy + 14)]
for i, (px_, py_) in enumerate(pieds):
    boite("PORT_Grue_Pied_%d" % i, g, px_, py_, 0.8, px_ + 1.4, py_ + 1.4, 30, "acier_rouge")
    boite("PORT_Grue_Bogie_%d" % i, g, px_ - 1.5, py_ - 0.3, 0, px_ + 2.9, py_ + 1.7, 0.8, "acier_gris")
for k, (a, b) in enumerate(((pieds[0], pieds[1]), (pieds[2], pieds[3]), (pieds[0], pieds[2]), (pieds[1], pieds[3]))):
    for z0, z1 in ((2, 15), (15, 28)):                              # croix de contreventement
        poutre("PORT_Grue_Croix_%d_%d_a" % (k, z0), g, (a[0] + 0.7, a[1] + 0.7, z0), (b[0] + 0.7, b[1] + 0.7, z1), 0.35, "acier_rouge")
        poutre("PORT_Grue_Croix_%d_%d_b" % (k, z0), g, (b[0] + 0.7, b[1] + 0.7, z0), (a[0] + 0.7, a[1] + 0.7, z1), 0.35, "acier_rouge")
    poutre("PORT_Grue_Ceinture_%d" % k, g, (a[0] + 0.7, a[1] + 0.7, 15), (b[0] + 0.7, b[1] + 0.7, 15), 0.5, "acier_rouge")
for s in (0, 14):
    boite("PORT_Grue_Traverse_%d" % s, g, gx, gy + s, 28, gx + 19.4, gy + s + 1.4, 30.5, "acier_rouge")
# flèche en treillis (4 membrures + diagonales), avance au-dessus de l'eau
fy0, fy1, fz = gy - 22, QUAI_Y + 48, 31.5
for dx in (7.0, 12.4):
    for dz in (0.0, 3.0):
        poutre("PORT_Grue_Membrure_%d_%d" % (dx, dz), g, (gx + dx, fy0, fz + dz), (gx + dx, fy1, fz + dz), 0.45, "acier_rouge")
k = 0
y = fy0
while y < fy1 - 3:
    for dx in (7.0, 12.4):
        poutre("PORT_Grue_Diag_V_%d_%d" % (k, dx), g, (gx + dx, y, fz), (gx + dx, y + 3, fz + 3), 0.22, "acier_rouge")
    poutre("PORT_Grue_Diag_H_%d" % k, g, (gx + 7, y, fz + 3), (gx + 12.4, y + 3, fz + 3), 0.2, "acier_rouge")
    poutre("PORT_Grue_Entretoise_%d" % k, g, (gx + 7, y, fz), (gx + 12.4, y, fz), 0.2, "acier_rouge")
    y += 3
    k += 1
boite("PORT_Grue_Machinerie", g, gx + 5.5, gy + 2, fz + 3, gx + 14, gy + 12, fz + 7.5, "tole_grise")
toit("PORT_Grue_Machinerie_Toit", g, gx + 5.5, gy + 2, gx + 14, gy + 12, fz + 7.5, 0.8, "acier_gris")
boite("PORT_Grue_Chariot", g, gx + 6.8, QUAI_Y + 4, fz - 1.2, gx + 12.6, QUAI_Y + 9, fz, "acier_jaune")
boite("PORT_Grue_Cabine", g, gx + 8, QUAI_Y + 5, fz - 4.2, gx + 11.4, QUAI_Y + 8.5, fz - 1.2, "acier_jaune")
boite("PORT_Grue_Cabine_Vitre", g, gx + 7.95, QUAI_Y + 8.45, fz - 3.8, gx + 11.45, QUAI_Y + 8.6, fz - 1.8, "vitre")
for k in range(10):                                                 # escalier en zigzag le long d'un pied
    z0 = k * 3
    yy = gy - 2.2 if k % 2 else gy - 1.0
    boite("PORT_Grue_Palier_%d" % k, g, gx - 1.6, gy - 2.6, z0 + 2.9, gx + 3, gy - 0.1, z0 + 3.05, "acier_gris")
    poutre("PORT_Grue_Volee_%d" % k, g, (gx - 1.2 if k % 2 else gx + 2.6, gy - 1.4, z0), (gx + 2.6 if k % 2 else gx - 1.2, gy - 1.4, z0 + 3), 0.9, "acier_gris")
for k in range(2):
    boite("PORT_Grue_Rail_%d" % k, g, -10, gy + 0.4 + k * 14, 0.08, PORT_L + 10, gy + 1.0 + k * 14, 0.2, "acier_gris")

# ---------------------------------------------------------------- TOUR DE BUREAUX (au bord est, à côté de la route d'entrée)
t = "PORT/BATIMENTS"
TX = 193.0
boite("PORT_Tour_Socle", t, TX - 0.5, 14.5, 0, TX + 16.5, 35.5, 4.5, "beton_mur")
boite("PORT_Tour_Facades", t, TX, 15, 4.5, TX + 16, 35, 48, "facade")
boite("PORT_Tour_Auvent", t, TX + 2, 12, 3.5, TX + 14, 15, 3.8, "acier_gris")
boite("PORT_Tour_Entree_Vitree", t, TX + 5, 14.9, 0.1, TX + 11, 15.0, 3.4, "vitre")
for s_, a in (("N", (TX, 34.4, TX + 16, 35)), ("S", (TX, 15, TX + 16, 15.6)), ("O", (TX, 15, TX + 0.6, 35)), ("E", (TX + 15.4, 15, TX + 16, 35))):
    boite("PORT_Tour_Parapet_" + s_, t, a[0], a[1], 48, a[2], a[3], 49.2, "beton_mur")
boite("PORT_Tour_Edicule", t, TX + 4, 18, 48, TX + 10, 24, 51.5, "beton_mur")
for k in range(3):
    boite("PORT_Tour_Clim_%d" % k, t, TX + 11, 20 + k * 4, 48, TX + 14, 22.5 + k * 4, 49.6, "acier_gris")
cylindre("PORT_Tour_Reservoir", t, TX + 6, 30, 48, 51, 1.8, "acier_gris")
boite("PORT_Poste_Garde", t, 193, -8, 0, 197, -2, 3, "beton_mur")
boite("PORT_Poste_Garde_Vitre", t, 192.95, -7, 1.2, 193.0, -3, 2.5, "vitre")
boite("PORT_Poste_Garde_Toit", t, 192.7, -8.3, 3, 197.3, -1.7, 3.2, "acier_gris")
boite("PORT_Bureau_Quai", t, 120, QUAI_Y - 20, 0, 132, QUAI_Y - 12, 6, "tole_bleue")
toit("PORT_Bureau_Quai_Toit", t, 119.5, QUAI_Y - 20.5, 132.5, QUAI_Y - 11.5, 6, 1.5, "tole_toit")
boite("PORT_Bureau_Quai_Fenetres", t, 121, QUAI_Y - 12.02, 2.6, 131, QUAI_Y - 11.98, 4.2, "vitre")

# ---------------------------------------------------------------- CLÔTURES, PORTAIL, LAMPADAIRES, DÉCOR
d = "PORT/DECORATIONS"
e_ = "PORT/ENCEINTE"
FACADES = ["facade", "facade2", "facade3", "facade", "facade2", "facade3", "tole_beige"]
r3 = random.Random(31)


def bloc_enceinte(nom, x0, y0, x1, y1, haut, mat):
    """immeuble / entrepôt de l'enceinte : façade, acrotère, quelques équipements sur le toit"""
    boite(nom, e_, x0, y0, 0, x1, y1, haut, mat)
    boite(nom + "_Socle", e_, x0 - 0.1, y0 - 0.1, 0, x1 + 0.1, y1 + 0.1, 1.2, "beton_mur")
    boite(nom + "_Acrotere", e_, x0 - 0.15, y0 - 0.15, haut, x1 + 0.15, y1 + 0.15, haut + 0.9, "beton_mur")
    for k in range(r3.randint(0, 3)):
        cx, cy = r3.uniform(x0 + 2, x1 - 4), r3.uniform(y0 + 2, y1 - 4)
        boite("%s_Toit_Equip_%d" % (nom, k), e_, cx, cy, haut, cx + r3.uniform(1.5, 3.5), cy + r3.uniform(1.5, 3), haut + r3.uniform(1, 2.5), "acier_gris")


def rangee(prefixe, debut, fin, fixe0, fixe1, axe, trou=None):
    """rangée continue de bâtiments de largeurs / hauteurs variées (axe « x » : le long de X)"""
    pos, k = debut, 0
    while pos < fin - 1:
        larg = min(r3.uniform(14, 32), fin - pos)
        a0, a1 = pos, pos + larg
        if trou and a0 < trou[1] and a1 > trou[0]:                 # on s'arrête au tunnel, on reprend après
            if a0 < trou[0] - 1:
                a1 = trou[0]
            else:
                pos = trou[1]
                continue
        mat = r3.choice(FACADES)
        haut = r3.choice((14, 16)) if mat.startswith("tole") else r3.choice((24, 28, 32, 38, 44, 52))
        if axe == "x":
            bloc_enceinte("%s_%02d" % (prefixe, k), a0, fixe0, a1, fixe1, haut, mat)
        else:
            bloc_enceinte("%s_%02d" % (prefixe, k), fixe0, a0, fixe1, a1, haut, mat)
        pos, k = a1, k + 1


A0, A1, PIED, EP = 179.6, 193.4, 4.5, 0.8                       # voûte : 13,8 m de large, 11,4 m sous la clé
AXC, AR = (A0 + A1) / 2, (A1 - A0) / 2
rangee("PORT_Enceinte_Sud", -32, 232, -30, -10, "x", trou=(A0 - 4.6, A1 + 4.6))
rangee("PORT_Enceinte_Ouest", -10, 154, -32, -10, "y")
rangee("PORT_Enceinte_Est", -10, 154, 210, 232, "y")
TY0, TY1 = -70.0, -10.0
SEG = 20


def profil(r, ecart):
    pts = [(AXC - r, 0.0), (AXC - r, PIED)]
    for k in range(1, SEG):
        a = math.pi - math.pi * k / SEG
        pts.append((AXC + r * math.cos(a), PIED + r * math.sin(a)))
    pts += [(AXC + r, PIED), (AXC + r, 0.0)]
    return pts


INT, EXT = profil(AR, 0), profil(AR + EP, 0)
for k in range(len(INT) - 1):                                       # coque de la voûte, tranche par tranche
    prisme("PORT_Tunnel_Voute_%02d" % k, e_, [INT[k], INT[k + 1], EXT[k + 1], EXT[k]][::-1], TY0, TY1, "beton_mur")
# bâtiment-pont au-dessus de la bouche : piliers, tympan (plein entre la voûte et les étages), étages
ZT = PIED + AR + EP + 1.5
boite("PORT_Pont_Tunnel_Pilier_O", e_, A0 - 4.6, -30, 0, A0 - EP, -10, 34, "facade3")
boite("PORT_Pont_Tunnel_Pilier_E", e_, A1 + EP, -30, 0, A1 + 4.6, -10, 34, "facade3")
for k in range(len(EXT) - 1):
    (xa, za), (xb, zb) = EXT[k], EXT[k + 1]
    if min(za, zb) >= PIED - 0.01:
        prisme("PORT_Pont_Tympan_%02d" % k, e_, [(xa, za), (xb, zb), (xb, ZT), (xa, ZT)], -30, -10, "beton_mur")
boite("PORT_Pont_Tunnel_Etages", e_, A0 - EP, -30, ZT, A1 + EP, -10, 34, "facade3")
boite("PORT_Pont_Tunnel_Acrotere", e_, A0 - 4.75, -30.15, 34, A1 + 4.75, -9.85, 35, "beton_mur")
for yy in (-10.0, -30.6):                                           # encadrement de la bouche (arc en relief)
    for k in range(len(EXT) - 1):
        prisme("PORT_Tunnel_Arc_%d_%02d" % (int(-yy), k), e_, [INT[k], INT[k + 1], EXT[k + 1], EXT[k]][::-1], yy, yy + 0.6, "beton_sol")
# chaussée, trottoirs, garde-corps
boite("PORT_Tunnel_Route", e_, A0, TY0, -0.3, A1, TY1, 0.06, "asphalte")
boite("PORT_Tunnel_Trottoir_O", e_, A0, TY0, 0.06, TUNNEL_X0, TY1, 0.3, "beton_sol")
boite("PORT_Tunnel_Trottoir_E", e_, TUNNEL_X1, TY0, 0.06, A1, TY1, 0.3, "beton_sol")
garde_corps("PORT_Tunnel_GC_O", e_, (TUNNEL_X0 - 0.1, TY0), (TUNNEL_X0 - 0.1, TY1 - 1), 0.3)
garde_corps("PORT_Tunnel_GC_E", e_, (TUNNEL_X1 + 0.05, TY0), (TUNNEL_X1 + 0.05, TY1 - 1), 0.3)
boite("PORT_Tunnel_Marquage", e_, (TUNNEL_X0 + TUNNEL_X1) / 2 - 0.12, TY0, 0.06, (TUNNEL_X0 + TUNNEL_X1) / 2 + 0.12, TY1, 0.07, "marquage")
for xx in (A0 + 0.01, A1 - 0.03):                                   # bandes de sécurité + chemins de câbles
    boite("PORT_Tunnel_Bande_%d" % int(xx), e_, xx, TY0, 0.3, xx + 0.02, TY1, 1.2, "rayures")
    boite("PORT_Tunnel_Cables_%d" % int(xx), e_, xx, TY0, 3.4, xx + (0.35 if xx < AXC else -0.35), TY1, 3.55, "acier_gris")
# lampes au sodium en deux rangées (orange, comme un vrai tunnel), vraies lumières, panneaux de secours verts
for k in range(int((TY1 - TY0) // 4)):
    y = TY1 - 2 - k * 4
    for cote in (-1, 1):
        a = math.radians(55)
        lx, lz = AXC + cote * AR * math.cos(a), PIED + AR * math.sin(a)
        boite("PORT_Tunnel_Sodium_%02d_%d" % (k, cote), e_, lx - 0.35, y - 0.6, lz - 0.12, lx + 0.35, y + 0.6, lz + 0.05, "sodium")
    if k % 3 == 0:
        lumiere("PORT_Tunnel_Lumiere_%02d" % k, e_, (AXC, y, PIED + AR - 1.5), 180, (1.0, 0.55, 0.2), 0.5)
    if k % 4 == 1:
        boite("PORT_Tunnel_Secours_%02d" % k, e_, A0 + 0.02, y - 0.4, 2.2, A0 + 0.08, y + 0.4, 2.6, "secours")
        boite("PORT_Tunnel_Niche_%02d" % k, e_, A1 - 0.4, y - 0.8, 0.3, A1 - 0.02, y + 0.8, 2.2, "acier_rouge")
# ventilateurs suspendus (paires) sous la clé de voûte
for yv in (-22.0, -46.0):
    for cote in (-1, 1):
        cx_, cz_ = AXC + cote * 1.7, PIED + AR - 1.4
        cercle = [(cx_ + 0.65 * math.cos(2 * math.pi * k / 16), cz_ + 0.65 * math.sin(2 * math.pi * k / 16)) for k in range(16)]
        prisme("PORT_Tunnel_Ventilo_%d_%d" % (int(-yv), cote), e_, cercle[::-1], yv - 2.2, yv + 2.2, "acier_gris")
        boite("PORT_Tunnel_Ventilo_Attache_%d_%d" % (int(-yv), cote), e_, cx_ - 0.08, yv - 1, cz_ + 0.6, cx_ + 0.08, yv + 1, PIED + AR - 0.1, "acier_gris")
# flaques au sol et légère brume (les faisceaux des lampes se voient)
brume = bpy.data.materials.new("PORT_Brume_Tunnel")
brume.use_nodes = True
nt = brume.node_tree
nt.nodes.remove(nt.nodes.get("Principled BSDF"))
vol = nt.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.006
vol.inputs["Color"].default_value = (0.9, 0.8, 0.7, 1)
nt.links.new(vol.outputs[0], nt.nodes.get("Material Output").inputs["Volume"])
MATS["brume"] = brume
boite("PORT_Tunnel_Brume", e_, A0, TY0, 0.3, A1, TY1, PIED + AR, "brume")
TUNNEL_FLAQUES = [(rnd.uniform(TUNNEL_X0 + 0.5, TUNNEL_X1 - 2.5), rnd.uniform(TY0 + 2, TY1 - 4)) for _ in range(10)]
for i, (x, y) in enumerate(((20, 58.5), (55, 58.5), (90, 58.5), (125, 58.5), (160, 58.5), (35, 70.5), (75, 70.5), (115, 70.5), (155, 70.5), (40, QUAI_Y - 21.5), (110, QUAI_Y - 21.5), (170, QUAI_Y - 21.5))):
    cylindre("PORT_Lampadaire_%02d" % i, d, x, y, 0, 10, 0.12, "acier_gris")
    sens = 1 if y < ROUTE_Y else -1
    poutre("PORT_Lampadaire_%02d_Bras" % i, d, (x, y, 9.8), (x, y + sens * 1.6, 10.2), 0.1, "acier_gris")
    boite("PORT_Lampadaire_%02d_Tete" % i, d, x - 0.35, y + sens * 1.6 - 0.2, 9.95, x + 0.35, y + sens * 1.6 + 0.2, 10.15, "lampe")
for i in range(14):                                                 # palettes, fûts, cônes sur le quai et près des hangars
    x, y = rnd.uniform(5, 190), rnd.choice((rnd.uniform(41, 49), rnd.uniform(QUAI_Y - 20, QUAI_Y - 6)))
    if 55 < x < 85 and y > 120:
        continue
    for j in range(rnd.randint(1, 4)):
        boite("PORT_Palette_%02d_%d" % (i, j), d, x, y, j * 0.16, x + 1.2, y + 1.0, j * 0.16 + 0.14, "bois")
for i in range(10):
    x, y = rnd.uniform(10, 180), rnd.uniform(QUAI_Y - 20, QUAI_Y - 4)
    cylindre("PORT_Fut_Quai_%02d" % i, d, x, y, 0.08, 0.95, 0.3, rnd.choice(("acier_rouge", "acier_jaune", "acier_gris")))
for i, x in enumerate(range(97, 106, 2)):
    if not modele("PORT_Cone_%02d" % i, d, "models/props_junk/trafficcone001a", x, ROUTE_Y + ROUTE_L + 1.2, 0.06, rnd.uniform(0, 6.28)):
        cylindre("PORT_Cone_%02d" % i, d, x, ROUTE_Y + ROUTE_L + 1.2, 0.06, 0.75, 0.18, "cone", 8)

# ---------------------------------------------------------------- VILLE AU LOIN (de l'autre côté de l'eau, comme sur la capture)
v_ = "PORT/DECOR_LOINTAIN"
r2 = random.Random(9)
x = -260
while x < 460:
    w, p, hh = r2.uniform(25, 60), r2.uniform(20, 40), r2.uniform(40, 190)
    y = QUAI_Y + 330 + r2.uniform(0, 80)
    boite("PORT_Ville_Immeuble_%d" % int(x), v_, x, y, -3, x + w, y + p, hh, "ville")
    x += w + r2.uniform(5, 25)


# ================================================================== REMPLISSAGE (plus d'endroit vide)
def plan(nom, coll, x0, y0, x1, y1, z, mat, rot=0.0):
    """plan horizontal (décalque au sol : tache, flaque, traces)"""
    cx, cy, lx, ly = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    o = objet(nom, coll, [(-lx, -ly, 0), (lx, -ly, 0), (lx, ly, 0), (-lx, ly, 0)], [(0, 1, 2, 3)], mat, (cx, cy, z))
    uv = o.data.uv_layers.new(name="UV")
    for j, li in enumerate(o.data.polygons[0].loop_indices):
        uv.data[li].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][j]
    o.rotation_euler = (0, 0, rot)
    return o


def panneau_vertical(nom, coll, x, y, z, larg, haut, mat, orient=0.0):
    """plan vertical face à -Y quand orient = 0 (enseignes, numéros peints)"""
    o = objet(nom, coll, [(-larg / 2, 0, 0), (larg / 2, 0, 0), (larg / 2, 0, haut), (-larg / 2, 0, haut)], [(0, 1, 2, 3)], mat, (x, y, z))
    uv = o.data.uv_layers.new(name="UV")
    for j, li in enumerate(o.data.polygons[0].loop_indices):
        uv.data[li].uv = [(0, 0), (1, 0), (1, 1), (0, 1)][j]
    o.rotation_euler = (0, 0, orient)
    return o


def roue(nom, coll, x, y, z, r=0.5, ep=0.35, axe="y"):
    """pneu à 28 côtés lissé + jante grise de chaque côté"""
    seg = 28

    def disque(rr, e0, e1):
        v, f = [], []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            c, s_ = rr * math.cos(a), rr * math.sin(a)
            if axe == "y":
                v += [(c, e0, s_), (c, e1, s_)]
            else:
                v += [(e0, c, s_), (e1, c, s_)]
        for k in range(seg):
            a, b = 2 * k, 2 * ((k + 1) % seg)
            f.append((a, b, b + 1, a + 1))
        f.append(tuple(2 * k for k in reversed(range(seg))))
        f.append(tuple(2 * k + 1 for k in range(seg)))
        return v, f

    v, f = disque(r, -ep / 2, ep / 2)
    o = objet(nom, coll, v, f, "caoutchouc", (x, y, z + r))
    for poly in o.data.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    for cote in (-1, 1):
        e0 = cote * ep / 2
        vj, fj = disque(r * 0.55, e0, e0 + cote * 0.02)
        objet(nom + "_Jante_%d" % cote, coll, vj, fj, "jante", (x, y, z + r))
    return o


def camion(nom, x, y, sens=1, couleur="carrosserie_bleue", conteneur=True):
    """camion porteur (comme le modèle de référence) : cabine inclinée + déflecteur, caisse grise, 3 essieux.
    Seule la couleur de la cabine change. sens = 1 : cabine vers +X"""
    c = "PORT/VEHICULES/" + nom
    X = lambda d: x + sens * d                                       # position le long du camion

    def bx(n, d0, d1, ya, yb, z0, z1, m):
        return boite(nom + "_" + n, c, X(d0), y + ya, z0, X(d1), y + yb, z1, m)

    def pr(n, pts, ya, yb, m):
        return prisme(nom + "_" + n, c, [(X(d), z) for d, z in pts], y + ya, y + yb, m)

    bx("Chassis", -5.0, 5.0, -0.5, 0.5, 0.6, 0.95, "acier_gris")
    bx("Caisse", -5.0, 2.6, -1.25, 1.25, 1.25, 4.0, "caisse_grise")
    for ya, yb in ((-1.28, -1.25), (1.25, 1.28)):                   # cadre de la caisse
        for d0, d1, z0, z1 in ((-5.0, 2.6, 3.9, 4.0), (-5.0, 2.6, 1.25, 1.35), (-5.0, -4.9, 1.25, 4.0), (2.5, 2.6, 1.25, 4.0)):
            bx("Cadre_%d_%d_%d" % (int(ya * 100), int(d0 * 10), int(z0 * 10)), d0, d1, ya, yb, z0, z1, "acier_gris")
    # cabine : profil de côté extrudé sur la largeur
    pr("Cabine", [(2.8, 0.95), (5.0, 0.95), (5.0, 1.7), (4.95, 2.3), (4.7, 3.3), (4.2, 3.45), (2.8, 3.45)], -1.2, 1.2, couleur)
    pr("Deflecteur", [(2.8, 3.45), (4.2, 3.45), (3.5, 4.0), (2.8, 4.0)], -1.1, 1.1, couleur)
    pr("Pare_Brise", [(4.99, 2.35), (4.74, 3.27), (4.77, 3.28), (5.02, 2.36)], -1.05, 1.05, "vitre")
    for ya, yb in ((-1.22, -1.2), (1.2, 1.22)):
        bx("Vitre_%d" % int(ya * 10), 3.3, 4.45, ya, yb, 2.2, 3.15, "vitre")
        bx("Porte_Joint_%d" % int(ya * 10), 3.15, 3.2, ya, yb, 1.0, 3.3, "caoutchouc")
        bx("Marchepied_%d" % int(ya * 10), 3.4, 4.3, ya * 0.98, yb * 0.98, 0.55, 0.65, "acier_gris")
    bx("Pare_Chocs", 4.95, 5.25, -1.25, 1.25, 0.4, 0.95, "acier_gris")
    for ya in (-0.95, 0.75):
        bx("Phare_%d" % int(ya * 10), 5.0, 5.04, ya, ya + 0.2, 1.05, 1.2, "lampe")
        bx("Clignotant_%d" % int(ya * 10), 5.0, 5.04, ya, ya + 0.2, 0.98, 1.03, "sodium")
    for d0 in (0.2, -1.6):                                          # coffres à outils sous la caisse
        for ya, yb in ((-1.15, -0.7), (0.7, 1.15)):
            bx("Coffre_%d_%d" % (int(d0 * 10), int(ya * 10)), d0, d0 + 1.0, ya, yb, 0.55, 1.2, "acier_gris")
    for d in (-3.15,):                                              # garde-boue des roues arrière
        for ya, yb in ((-1.3, -0.9), (0.9, 1.3)):
            bx("Garde_Boue_%d" % int(ya * 10), d - 1.2, d + 1.2, ya, yb, 1.15, 1.25, "acier_gris")
    for d in (3.9, -2.6, -3.7):                                     # 3 essieux
        for yy in (-1.05, 1.05):
            roue("%s_Roue_%d_%d" % (nom, int(d * 10), int(yy * 10)), c, X(d), y + yy, 0)


def chariot(nom, x, y, rot=0.0, couleur="carrosserie_orange"):
    """chariot élévateur : caisse, mât, fourches, cage, contrepoids"""
    c = "PORT/VEHICULES/" + nom
    if modele(nom, c, "models/props/cs_assault/forklift", x, y, 0, rot + math.pi / 2):
        return
    parties = []
    parties.append(boite(nom + "_Corps", c, x - 1.0, y - 0.6, 0.3, x + 1.0, y + 0.6, 1.3, couleur))
    parties.append(boite(nom + "_Contrepoids", c, x - 1.3, y - 0.6, 0.3, x - 0.9, y + 0.6, 1.4, "acier_gris"))
    for yy in (y - 0.45, y + 0.45):
        parties.append(boite(nom + "_Mat_%d" % int(yy * 10), c, x + 1.0, yy - 0.06, 0.2, x + 1.15, yy + 0.06, 3.2, "acier_gris"))
        parties.append(boite(nom + "_Fourche_%d" % int(yy * 10), c, x + 1.15, yy - 0.08, 0.15, x + 2.3, yy + 0.08, 0.25, "acier_gris"))
        parties.append(boite(nom + "_Cage_%d" % int(yy * 10), c, x - 0.4, yy - 0.04, 1.3, x - 0.32, yy + 0.04, 2.4, "acier_gris"))
        parties.append(boite(nom + "_CageAv_%d" % int(yy * 10), c, x + 0.6, yy - 0.04, 1.3, x + 0.68, yy + 0.04, 2.4, "acier_gris"))
    parties.append(boite(nom + "_Toit_Cage", c, x - 0.45, y - 0.55, 2.4, x + 0.75, y + 0.55, 2.48, "acier_gris"))
    for xx in (x - 0.7, x + 0.7):
        for yy in (y - 0.62, y + 0.62):
            parties.append(roue("%s_Roue_%d_%d" % (nom, int(xx * 10), int(yy * 10)), c, xx, yy, 0, 0.3, 0.25))
    if rot:                                                         # tourne tout le chariot autour de son centre
        ca, sa = math.cos(rot), math.sin(rot)
        for o in parties:
            dx, dy = o.location.x - x, o.location.y - y
            o.location.x, o.location.y = x + dx * ca - dy * sa, y + dx * sa + dy * ca
            o.rotation_euler = (0, 0, rot)


def cabine_chantier(nom, x, y, longueur=6.0, etage=False):
    c = "PORT/BATIMENTS"
    for k in range(2 if etage else 1):
        z = k * 2.8
        boite("%s_%d" % (nom, k), c, x, y, z, x + longueur, y + 2.5, z + 2.7, "cabine")
        boite("%s_%d_Fenetre" % (nom, k), c, x + 1, y - 0.03, z + 1.2, x + longueur - 1, y + 0.02, z + 2.1, "vitre")
    boite(nom + "_Clim", c, x + longueur - 1.2, y + 2.5, 1.6, x + longueur - 0.2, y + 3.0, 2.3, "acier_gris")
    if etage:
        escalier(nom + "_Escalier", c, x - 1.2, x - 0.1, y + 0.2, 0, 2.8, 1)


C = "PORT/DECORATIONS"
# camions garés le long des hangars et sur la route du quai, chariots élévateurs dans le parc et le quai
for i, (x, y, sens, coul) in enumerate(((20, 52, 1, "carrosserie_bleue"), (40, 52, 1, "carrosserie_blanche"), (66, 52, -1, "carrosserie_rouge"),
                                         (128, 52, 1, "carrosserie_blanche"), (160, 52, -1, "carrosserie_bleue"), (60, 64.5, 1, "carrosserie_blanche"),
                                         (140, 66.5, -1, "carrosserie_orange"), (70, QUAI_Y - 16, 1, "carrosserie_rouge"))):
    camion("PORT_Camion_%02d" % (i + 1), x, y, sens, coul, conteneur=(i % 3 != 2))
for i, (x, y, rot) in enumerate(((80, 73, 0.0), (110, 98, 1.57), (150, 73, 3.14), (35, 128, 0.6), (130, QUAI_Y - 8, 2.2), (100, QUAI_Y - 14, 0.3), (12, 44, 1.0))):
    chariot("PORT_Chariot_%02d" % (i + 1), x, y, rot)
# cabines de chantier (bureaux du parc), bennes, blocs de béton, armoires électriques, bornes incendie
cabine_chantier("PORT_Cabine_Parc_01", 3, 100, 7, etage=True)
cabine_chantier("PORT_Cabine_Parc_02", 3, 80, 6)
# ---- intérieurs différents : garage (camion en réparation), colis (conteneur qu'on décharge), planque (table de réunion)
for n, hx in enumerate(HANGARS_X, 1):
    THEME = ("entrepot", "garage", "colis", "planque")[(n - 1) % 4]
    x0, y0, x1, y1 = hx, HANGAR_Y, hx + HANGAR["l"], HANGAR_Y + HANGAR["p"]
    c = "PORT/HANGARS/PORT_Hangar_%02d" % n
    nh = "PORT_Hangar_%02d" % n
    if THEME == "garage":
        camion(nh + "_Camion_Reparation", x0 + 31, y0 + 11, -1, "carrosserie_blanche")
        for k in range(6):                                          # piles de pneus
            for j in range(rnd.randint(2, 5)):
                if not modele("%s_Pneu_%d_%d" % (nh, k, j), c, "models/props_vehicles/tire001b_truck", x0 + 16 + k * 1.3, y0 + 1.2, 0.12 + j * 0.34 + 0.61, rnd.uniform(0, 6.28), math.pi / 2):
                    cylindre("%s_Pneu_%d_%d" % (nh, k, j), c, x0 + 16 + k * 1.3, y0 + 1.2, 0.12 + j * 0.32, 0.42 + j * 0.32, 0.5, "caoutchouc")
        for k in range(3):                                          # servantes d'atelier rouges + établis le long du mur sud
            boite("%s_Servante_%d" % (nh, k), c, x0 + 25 + k * 4, y0 + 0.5, 0.12, x0 + 26, y0 + 1.1, 1.1, "acier_rouge")
            boite("%s_Etabli_Sud_%d" % (nh, k), c, x0 + 26.3 + k * 4, y0 + 0.4, 0.9, x0 + 28.6 + k * 4, y0 + 1.2, 0.98, "bois")
        for xx in (x1 - 3, x1 - 9):                                 # portique de levage au-dessus du camion
            boite("%s_Portique_%d" % (nh, int(xx)), c, xx, y0 + 7, 0.12, xx + 0.25, y0 + 7.25, 6, "acier_jaune")
            boite("%s_PortiqueB_%d" % (nh, int(xx)), c, xx, y0 + 14.8, 0.12, xx + 0.25, y0 + 15.05, 6, "acier_jaune")
            boite("%s_Portique_Poutre_%d" % (nh, int(xx)), c, xx, y0 + 7, 6, xx + 0.25, y0 + 15.05, 6.4, "acier_jaune")
        for k in range(4):
            plan("%s_Huile_%d" % (nh, k), c, x0 + 24 + k * 3, y0 + 9 + rnd.uniform(0, 3), x0 + 26 + k * 3, y0 + 11 + rnd.uniform(0, 3), 0.125, "dec_tache_huile")
        chariot(nh + "_Chariot", x0 + 18, y0 + 18, 1.57)
    elif THEME == "colis":
        o = bpy.data.objects.new(nh + "_Conteneur_Decharge", rnd.choice(MODELES_C))
        o.location, o.rotation_euler = (x0 + 33, y0 + 13, 0.12), (0, 0, math.pi / 2)
        collection(c).objects.link(o)
        boite(nh + "_Tapis_Roulant", c, x0 + 15.5, y0 + 9, 0.8, x0 + 31.5, y0 + 10, 0.95, "caoutchouc")
        for k in range(9):
            boite("%s_Tapis_Pied_%d" % (nh, k), c, x0 + 15.7 + k * 1.9, y0 + 9.1, 0.12, x0 + 15.85 + k * 1.9, y0 + 9.9, 0.8, "acier_gris")
            if rnd.random() < 0.6:
                boite("%s_Colis_Tapis_%d" % (nh, k), c, x0 + 16 + k * 1.7, y0 + 9.2, 0.95, x0 + 16.6 + k * 1.7, y0 + 9.8, 1.35, "carton")
        for k in range(30):                                         # colis en vrac au bout du tapis
            cx_, cy_ = x0 + 27 + rnd.uniform(0, 3.5), y0 + 11 + rnd.uniform(0, 3)
            t_ = rnd.uniform(0.4, 0.8)
            boite("%s_Colis_%d" % (nh, k), c, cx_, cy_, 0.12, cx_ + t_, cy_ + t_, 0.12 + t_ * rnd.uniform(0.6, 1.0), "carton")
        chariot(nh + "_Chariot", x0 + 29, y0 + 20, 3.14)
    elif THEME == "planque":
        cx_, cy_ = x0 + 30, y0 + 13                                # table de réunion, chaises, canapés, brasero
        boite(nh + "_Table", c, cx_ - 2, cy_ - 0.8, 0.75, cx_ + 2, cy_ + 0.8, 0.82, "bois")
        for xx, yy in ((cx_ - 1.8, cy_ - 0.75), (cx_ + 1.7, cy_ - 0.75), (cx_ - 1.8, cy_ + 0.65), (cx_ + 1.7, cy_ + 0.65)):
            boite("%s_Table_Pied_%d_%d" % (nh, int(xx * 10), int(yy * 10)), c, xx, yy, 0.12, xx + 0.1, yy + 0.1, 0.75, "acier_gris")
        for k in range(6):
            xx = cx_ - 1.5 + (k % 3) * 1.5
            yy = cy_ - 1.5 if k < 3 else cy_ + 1.1
            if not modele("%s_Chaise_%d" % (nh, k), c, "models/props_c17/chair_office01a", xx, yy + 0.2, 0.12, (0 if k < 3 else math.pi) + rnd.uniform(-0.4, 0.4)):
                boite("%s_Chaise_%d" % (nh, k), c, xx - 0.22, yy, 0.45, xx + 0.22, yy + 0.4, 0.5, "acier_gris")
        for k, (xa, ya) in enumerate(((cx_ - 5, cy_ - 1.2), (cx_ + 4, cy_ - 1.2))):
            if not modele("%s_Canape_%d" % (nh, k), c, "models/props_c17/furniturecouch001a", xa + 0.5, ya + 1.3, 0.12, 0 if k == 0 else math.pi):
                boite("%s_Canape_%d" % (nh, k), c, xa, ya, 0.12, xa + 1, ya + 2.6, 0.55, "carrosserie_rouge")
        cylindre(nh + "_Brasero", c, cx_, cy_ + 5, 0.12, 1.0, 0.3, "acier_rouge")
        boite(nh + "_Brasero_Feu", c, cx_ - 0.2, cy_ + 4.8, 1.0, cx_ + 0.2, cy_ + 5.2, 1.15, "sodium")
        lumiere(nh + "_Brasero_Lumiere", c, (cx_, cy_ + 5, 1.6), 150, (1.0, 0.45, 0.15), 0.4)
        boite(nh + "_Ampoule", c, cx_ - 0.1, cy_ - 0.1, 3.0, cx_ + 0.1, cy_ + 0.1, 3.2, "lampe")
        boite(nh + "_Ampoule_Fil", c, cx_ - 0.01, cy_ - 0.01, 3.2, cx_ + 0.01, cy_ + 0.01, HANGAR["h"] - 0.4, "caoutchouc")
        lumiere(nh + "_Ampoule_Lumiere", c, (cx_, cy_, 2.9), 120, (1.0, 0.8, 0.55), 0.2)
        for k in range(10):                                         # caisses empilées haut, en désordre
            xx, yy = x0 + 16 + rnd.uniform(0, 20), y0 + 1 + rnd.uniform(0, 4)
            for j in range(rnd.randint(1, 4)):
                d_ = rnd.uniform(-0.15, 0.15)
                caisse("%s_Caisse_Haute_%d_%d" % (nh, k, j), c, xx + 0.6 + d_, yy + 0.6 + d_, 0.12 + j * 1.02, d_)
        for k in range(5):
            plan("%s_Tache_%d" % (nh, k), c, x0 + 20 + k * 3, y0 + 16, x0 + 22 + k * 3, y0 + 18, 0.125, "dec_tache_huile")
cabine_chantier("PORT_Cabine_Quai", 150, QUAI_Y - 20, 6)
for i, (x, y) in enumerate(((47, 44), (92, 44), (137, 44), (182, 44), (168, 110))):
    if modele("PORT_Benne_%d" % i, C, "models/props_junk/trashdumpster01a", x, y, 0, math.pi / 2):
        continue
    boite("PORT_Benne_%d" % i, C, x - 1.6, y - 1.0, 0, x + 1.6, y + 1.0, 1.4, "acier_gris")
    boite("PORT_Benne_%d_Bord" % i, C, x - 1.7, y - 1.1, 1.4, x + 1.7, y + 1.1, 1.5, "acier_jaune")
for k in range(24):                                                    # blocs de béton (séparateurs) le long de la route du quai
    y = ROUTE_Y + ROUTE_L + 2 + k * 2.1
    if y > QUAI_Y - 24:
        break
    for xx in (94.6, 106.2):
        boite("PORT_Bloc_Beton_%d_%d" % (k, xx), C, xx - 0.3, y, 0, xx + 0.3, y + 1.9, 0.8, "beton_mur")
for i, x in enumerate((15, 60, 105, 150)):
    boite("PORT_Armoire_Elec_%d" % i, C, x, HANGAR_Y - 1.4, 0, x + 1.2, HANGAR_Y - 0.8, 1.8, "acier_gris")
    cylindre("PORT_Borne_Incendie_%d" % i, C, x + 3, 57.6, 0, 0.9, 0.16, "acier_rouge", 8)
# tuyaux le long des murs sud des hangars
for n, hx in enumerate(HANGARS_X):
    for k, z in enumerate((3.0, 3.6)):
        poutre("PORT_Tuyau_H%d_%d" % (n, k), C, (hx, HANGAR_Y - 0.55, z), (hx + HANGAR["l"], HANGAR_Y - 0.55, z), 0.25, "acier_gris")
    # lampes murales au-dessus de la porte + numéro peint sur la façade
    pm = hx + HANGAR["l"] / 2
    for s_ in (-1, 1):
        boite("PORT_Lampe_Murale_H%d_%d" % (n, s_), C, pm + s_ * 6 - 0.3, HANGAR_Y + HANGAR["p"] + 0.05, 8.5, pm + s_ * 6 + 0.3, HANGAR_Y + HANGAR["p"] + 0.4, 8.8, "lampe")
    panneau_vertical("PORT_Numero_Hangar_%d" % (n + 1), C, pm, HANGAR_Y + HANGAR["p"] + 0.04, 7.6, 3.6, 3.6, "dec_numero_%d" % (n + 1), math.pi)
# palettes et caisses devant les hangars, sacs, fûts : des petits groupes partout
for i in range(40):
    x = rnd.uniform(4, 182)
    y = rnd.choice((rnd.uniform(41.5, 49), rnd.uniform(QUAI_Y - 21, QUAI_Y - 3), rnd.uniform(126, 128)))
    if 58 < x < 82 and y > QUAI_Y - 20:
        continue
    if rnd.random() < 0.5:
        for j in range(rnd.randint(1, 5)):
            boite("PORT_Palette_Extra_%02d_%d" % (i, j), C, x, y, j * 0.16, x + 1.2, y + 1.0, j * 0.16 + 0.14, "bois")
    else:
        for j in range(rnd.randint(1, 3)):
            caisse("PORT_Caisse_Extra_%02d_%d" % (i, j), C, x + j * 1.3 + 0.6, y + 0.6, 0)
# décalques au sol : taches d'huile, flaques, traces de pneus (cassent la répétition du béton)
for i in range(60):
    x, y = rnd.uniform(0, 200), rnd.uniform(-5, QUAI_Y - 2)
    t = rnd.uniform(1.5, 5)
    nom = rnd.choice(("dec_tache_huile", "dec_tache_huile", "dec_flaque", "dec_traces_pneus"))
    if nom == "dec_traces_pneus":
        plan("PORT_Decal_%02d" % i, "PORT/DECALQUES", x - 1.5, y - 6, x + 1.5, y + 6, 0.075, nom, rnd.choice((0, math.pi / 2)))
    else:
        plan("PORT_Decal_%02d" % i, "PORT/DECALQUES", x - t, y - t, x + t, y + t, 0.075, nom, rnd.uniform(0, 6.28))
# panneaux : nom du port au-dessus de la bouche du tunnel (côté port), « danger » sur le quai
panneau_vertical("PORT_Panneau_Entree", C, AXC, -9.35, ZT + 0.2, 12, 3, "panneau_port", math.pi)
for i, (x, y) in enumerate(TUNNEL_FLAQUES):
    plan("PORT_Tunnel_Flaque_%d" % i, C, x, y, x + rnd.uniform(1.2, 2.5), y + rnd.uniform(1.5, 4), 0.075, "dec_flaque")
for i, x in enumerate((20, 90, 170)):
    boite("PORT_Panneau_Danger_Poteau_%d" % i, C, x - 0.05, QUAI_Y - 2.2, 0, x + 0.05, QUAI_Y - 2.1, 2.2, "acier_gris")
    panneau_vertical("PORT_Panneau_Danger_%d" % i, C, x, QUAI_Y - 2.25, 1.3, 0.9, 0.9, "panneau_danger")

# ================================================================== LUMIÈRE DU SOIR, RENDU
monde = bpy.data.worlds.new("PORT_Monde")
sc.world = monde
monde.use_nodes = True
fond = monde.node_tree.nodes.get("Background")
try:
    ciel = monde.node_tree.nodes.new("ShaderNodeTexSky")
    ciel.sun_elevation = math.radians(3)
    ciel.sun_rotation = math.radians(250)
    monde.node_tree.links.new(ciel.outputs["Color"], fond.inputs["Color"])
    fond.inputs["Strength"].default_value = 0.35
except Exception:
    fond.inputs["Color"].default_value = (0.28, 0.20, 0.22, 1)
soleil = bpy.data.objects.new("PORT_Soleil", bpy.data.lights.new("PORT_Soleil", "SUN"))
soleil.data.energy = 2.2
soleil.data.color = (1.0, 0.62, 0.38)
soleil.data.angle = math.radians(3)
soleil.rotation_euler = (math.radians(80), 0, math.radians(-65))
sc.collection.objects.link(soleil)
appoint = bpy.data.objects.new("PORT_Ciel_Appoint", bpy.data.lights.new("PORT_Ciel_Appoint", "SUN"))
appoint.data.energy = 0.35
appoint.data.color = (0.55, 0.62, 0.85)
appoint.rotation_euler = (math.radians(30), 0, math.radians(120))
sc.collection.objects.link(appoint)

for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        continue
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = "AgX" if "AgX" in [v.identifier for v in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = "MATERIAL"              # le fichier s'ouvre directement AVEC les textures
                    sp.shading.color_type = "TEXTURE"
                    sp.clip_end = 3000
                    sp.clip_start = 0.1

APERCUS = os.path.join(ICI, "apercus")
os.makedirs(APERCUS, exist_ok=True)
cam_d = bpy.data.cameras.new("PORT_Camera")
cam_d.clip_end = 4000
cam = bpy.data.objects.new("PORT_Camera", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def vue(nom, pos, cible, lens=24):
    cam.location = pos
    dv = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(dv[0], dv[1]), -dv[2]), 0, math.atan2(dv[1], dv[0]) - math.pi / 2)
    cam_d.lens = lens
    sc.render.filepath = os.path.join(APERCUS, nom + ".png")
    bpy.ops.render.render(write_still=True)


if COLL_SOURCES in bpy.context.view_layer.layer_collection.children:
    bpy.context.view_layer.layer_collection.children[COLL_SOURCES].exclude = True
# UV (projection en cube, 1 tuile = 2 m) sur tous les objets : les textures s'affichent aussi en mode « Solide »
for o in bpy.data.objects:
    if o.type != "MESH" or o.data.uv_layers:
        continue
    me = o.data
    uv = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        nx, ny, nz = (abs(c) for c in poly.normal)
        for li in poly.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            if nz >= nx and nz >= ny:
                uv.data[li].uv = (x / 2, y / 2)
            elif nx >= ny:
                uv.data[li].uv = (y / 2, z / 2)
            else:
                uv.data[li].uv = (x / 2, z / 2)
# les images sont rangées DANS le fichier .blend (plus jamais de textures introuvables)
bpy.ops.file.pack_all()
# la vue de départ : au-dessus du port, en regardant tout le port
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    r3d = sp.region_3d
                    r3d.view_location = (100, 90, 0)
                    r3d.view_distance = 330
                    import mathutils
                    r3d.view_rotation = mathutils.Euler((math.radians(55), 0, math.radians(25))).to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ICI, "port.blend"))
vue("detail_vue_aerienne", (260, -90, 150), (100, 85, 0))
vue("detail_depuis_le_toit_de_la_tour", (186.5, 33, 51.5), (95, 105, 8))
vue("detail_au_sol_route", (20, 64, 1.7), (120, 70, 4))
vue("detail_interieur_hangar", (75, 38, 1.7), (60, 22, 5))
vue("detail_quai_grue", (95, QUAI_Y - 8, 2.0), (60, QUAI_Y + 10, 15))
vue("detail_hangars_facade", (70, 52, 3.0), (30, 35, 8))
print("PORT DÉTAILLÉ : %d objets, %d conteneurs -> port.blend" % (len(bpy.data.objects), compte))

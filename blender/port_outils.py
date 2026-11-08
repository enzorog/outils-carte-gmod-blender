"""
Outils communs des scripts de cartes Blender (matériaux, boîtes, poutres, escaliers, modèles du jeu, lumières...).
Importé par creer_port_compact.py ; ne construit rien tout seul.
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
    mat_image("acier_rouge", "acier_rouille", 2.0, 0.6, 0.3)
    mat_image("acier_gris", "acier_gris", 2, 0.55, 0.5)
    mat_image("acier_jaune", "acier_jaune", 2, 0.6, 0.3)
    mat_image("beton_mur", "beton_mur", 4, 0.9)
    mat_image("coque", "coque", 6, 0.6, 0.3)
    mat_image("bois", "bois_mur", 1.6, 0.85)
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
    mat_uni("tapis", (0.12, 0.012, 0.012), 0.95)


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


sc = bpy.context.scene
rnd = random.Random(2026)

import addon_utils
from mathutils import Matrix, Vector
try:
    addon_utils.enable("SourceIO-master", default_set=False)
    SOURCEIO = hasattr(bpy.ops, "sourceio") and hasattr(bpy.ops.sourceio, "mdl")
except Exception:
    SOURCEIO = False
NEOTOKYO = os.path.normpath(os.path.join(ICI, "..", "..", "..", "..", "..", "NEOTOKYO", "NeotokyoSource"))  # jeu gratuit NEOTOKYO°
MODELES_JEU = os.path.join(ICI, "modeles_jeu")                     # rempli par extraire_modeles.py
SOURCES = {}
COLL_SOURCES = "PORT_Modeles_Jeu_Sources"


def source_modele(chemin):
    """importe un .mdl du jeu une seule fois (gardé caché) ; renvoie (objets, point bas-centre) ou None"""
    if chemin in SOURCES:
        return SOURCES[chemin]
    f = os.path.join(NEOTOKYO if chemin.startswith("models/nt/") else MODELES_JEU, chemin + ".mdl")
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
    r = Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
    pts = [r @ o.matrix_world @ Vector(c_) for o in maillages for c_ in o.bound_box]
    cx = (min(q.x for q in pts) + max(q.x for q in pts)) / 2
    cy = (min(q.y for q in pts) + max(q.y for q in pts)) / 2
    m = Matrix.Translation((x - cx, y - cy, z - min(q.z for q in pts))) @ r
    for o in maillages:
        n = o.copy()
        n.name = nom
        n.parent = None
        for md in list(n.modifiers):
            n.modifiers.remove(md)
        n.matrix_world = m @ o.matrix_world
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



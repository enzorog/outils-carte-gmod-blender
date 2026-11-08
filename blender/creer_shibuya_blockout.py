"""
SHIBUYA — BLOCKOUT v2 (formes simples, couleurs unies) : plan ARRONDI et en RELIEF.
  - place centrale neutre en contrebas (carrefour « scramble », statue), boulevards en anneaux autour, avenues en étoile
    légèrement courbes ; bâtiments posés le long des rues (orientés selon la courbe), 2e rangée derrière, cours / ruelles ;
  - relief : place en cuvette (-3 m), colline au sud-ouest (+7 m), butte au sud-est (+4 m), rues en pente ;
  - rue marchande (3 vendeurs), espaces RP, zone de rassemblement, zones de conflit (rondes), 6 accès égouts, passerelles ;
  - le port (déjà fait) au nord, au milieu ; son tunnel débouche sur l'avenue nord qui descend à la place.
Version COMPACTE (~430 x 275 m au sud du port) : il faut garder de la place pour la forêt, Hokkaido et Tokyo.
Lancer : blender.exe -b --factory-startup --python creer_shibuya_blockout.py   -> shibuya_blockout.blend + apercus/shibuya_*.png
"""
import bpy, math, os, random
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
R = random.Random(7)
LIM, YN, HMAX = 405.0, -26.0, 44.0
PX0, PX1 = -26.0, 148.0                                   # bande du port + baie
PC = (104.0, -145.0)                                      # centre de la place
R_PLACE = 34.0
BX0, BY0, BX1, BY1 = -112.0, -300.0, 320.0, YN              # Shibuya COMPACT (le reste de la carte : forêt, Hokkaido, Tokyo)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
COUL = {"route": (0.16, 0.16, 0.17), "trottoir": (0.42, 0.42, 0.42), "batiment": (0.62, 0.58, 0.52), "haut": (0.48, 0.47, 0.50),
        "place": (0.78, 0.66, 0.58), "parc": (0.22, 0.45, 0.20), "conflit": (0.62, 0.12, 0.10), "egout": (0.95, 0.80, 0.10),
        "boutique": (0.95, 0.55, 0.10), "passerelle": (0.15, 0.35, 0.85), "mur": (0.33, 0.31, 0.30), "port": (0.20, 0.30, 0.45),
        "eau": (0.05, 0.15, 0.28), "ruine": (0.35, 0.25, 0.22), "rp": (0.35, 0.65, 0.30), "colline": (0.50, 0.47, 0.40)}
MATS = {}
for k, c in COUL.items():
    m = bpy.data.materials.new("SHI_" + k)
    m.diffuse_color = (*c, 1)
    MATS[k] = m
COLL = {}


def coll(nom):
    if nom not in COLL:
        c = bpy.data.collections.new("SHIBUYA_" + nom)
        bpy.context.scene.collection.children.link(c)
        COLL[nom] = c
    return COLL[nom]


def objet(nom, c, v, f, mat):
    me = bpy.data.meshes.new(nom)
    me.from_pydata(v, [], f)
    me.materials.append(MATS[mat])
    o = bpy.data.objects.new(nom, me)
    coll(c).objects.link(o)
    return o


def prisme(nom, c, pts, z0, z1, mat):
    """polygone convexe (x, y) extrudé ; z1 peut être une liste (dessus en pente, un z par sommet)"""
    n = len(pts)
    hauts = z1 if isinstance(z1, (list, tuple)) else [z1] * n
    v = [(x, y, z0) for x, y in pts] + [(x, y, hauts[i]) for i, (x, y) in enumerate(pts)]
    f = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    return objet(nom, c, v, f, mat)


def boite(nom, c, x0, y0, z0, x1, y1, z1, mat):
    return prisme(nom, c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, mat)


def disque(nom, c, cx, cy, r, z0, z1, mat, seg=32):
    return prisme(nom, c, [(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)], z0, z1, mat)


def lisse(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- relief
COLLINES = [((-50.0, -245.0), 55.0, 7.0), ((275.0, -255.0), 42.0, 4.0)]          # (centre, rayon, hauteur)


def H(x, y):
    """hauteur du sol : place en cuvette, collines en terrasses (pentes douces de 30 m sur les bords)"""
    h = 0.0
    d = math.hypot(x - PC[0], y - PC[1])
    h -= 3.0 * (1 - lisse((d - R_PLACE) / 22.0))
    for (cx, cy), r, hh in COLLINES:
        dc = math.hypot(x - cx, y - cy)
        h += hh * (1 - lisse((dc - r) / 22.0))
    return h


# ---------------------------------------------------------------- zones spéciales (cercles) : on n'y construit pas d'immeubles
ZONES = {
    "place": (PC, R_PLACE + 4),
    "espaces_rp": ((-45.0, -110.0), 38.0),
    "rassemblement": ((235.0, -235.0), 32.0),
    "conflit_ne": ((270.0, -70.0), 36.0),
    "conflit_s": ((105.0, -275.0), 26.0),
    "conflit_o": ((-85.0, -40.0), 0.0),
}
RUE_MARCHANDE = [(PC[0] - 62 + 7 * math.sin(t / 2), PC[1] + 55 - t * 11) for t in range(11)]     # rue piétonne courbe à l'ouest

# ---------------------------------------------------------------- grille d'occupation (2 m) : routes, zones, port, immeubles
PAS = 2.0
N = int(2 * LIM / PAS) + 1
OCC = np.zeros((N, N), dtype=np.uint8)


def ij(x, y):
    return int((x + LIM) / PAS), int((y + LIM) / PAS)


def marquer_disque(cx, cy, r, val=1):
    i0, j0 = ij(cx - r, cy - r)
    i1, j1 = ij(cx + r, cy + r)
    for i in range(max(0, i0), min(N, i1 + 1)):
        for j in range(max(0, j0), min(N, j1 + 1)):
            x, y = -LIM + i * PAS, -LIM + j * PAS
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                OCC[i, j] = max(OCC[i, j], val)


def marquer_poly(pts, val=1):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    i0, j0 = ij(min(xs), min(ys))
    i1, j1 = ij(max(xs), max(ys))
    for i in range(max(0, i0), min(N, i1 + 1)):
        for j in range(max(0, j0), min(N, j1 + 1)):
            x, y = -LIM + i * PAS, -LIM + j * PAS
            if dedans(pts, x, y):
                OCC[i, j] = max(OCC[i, j], val)


def dedans(pts, x, y):
    s = 0
    n = len(pts)
    for k in range(n):
        (ax, ay), (bx, by) = pts[k], pts[(k + 1) % n]
        c = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if c != 0:
            if s == 0:
                s = 1 if c > 0 else -1
            elif (c > 0) != (s > 0):
                return False
    return True


def libre(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    if min(xs) < BX0 + 1 or max(xs) > BX1 - 1 or min(ys) < BY0 + 1 or max(ys) > BY1 - 1:
        return False
    i0, j0 = ij(min(xs), min(ys))
    i1, j1 = ij(max(xs), max(ys))
    for i in range(max(0, i0), min(N, i1 + 1)):
        for j in range(max(0, j0), min(N, j1 + 1)):
            if OCC[i, j] and dedans(pts, -LIM + i * PAS, -LIM + j * PAS):
                return False
    return True


marquer_poly([(PX0, YN), (PX1, YN), (PX1, LIM + 5), (PX0, LIM + 5)], 9)              # le port et sa baie
for (c_, r_) in ZONES.values():
    marquer_disque(c_[0], c_[1], r_, 5)

# ---------------------------------------------------------------- réseau de rues : anneaux + avenues en étoile (légèrement courbes)
RUES = []                                                   # (nom, liste de points, largeur)


def ok_point(x, y):
    return BX0 + 3 < x < BX1 - 3 and BY0 + 3 < y < BY1 - 3


def ajouter_rue(nom, pts, larg):
    morceau = []
    for p in pts:
        if ok_point(*p):
            morceau.append(p)
        else:
            if len(morceau) > 1:
                RUES.append((nom + "_%d" % len(RUES), morceau, larg))
            morceau = []
    if len(morceau) > 1:
        RUES.append((nom + "_%d" % len(RUES), morceau, larg))


for k, r in enumerate((68, 130, 195, 260)):
    ondule = R.uniform(4, 10)
    pts = [(PC[0] + (r + ondule * math.sin(3 * a)) * math.cos(a), PC[1] + (r + ondule * math.sin(3 * a)) * math.sin(a))
           for a in [2 * math.pi * t / int(r / 2.5) for t in range(int(r / 2.5) + 1)]]
    ajouter_rue("Anneau_%d" % k, pts, 11 if k == 0 else 8)
ANGLES = [90 + 45 * k + R.uniform(-6, 6) for k in range(8)]
ANGLES[0] = 90.0                                            # l'avenue nord va tout droit au tunnel du port
for k, a0 in enumerate(ANGLES):
    debut = R_PLACE + 2 if k < 8 else 100
    courbe = 0 if k == 0 else R.uniform(-0.25, 0.25)
    pts = []
    for t in range(0, 300, 6):
        r = debut + t
        a = math.radians(a0) + courbe * math.sin(t / 160.0)
        pts.append((PC[0] + r * math.cos(a), PC[1] + r * math.sin(a)))
    ajouter_rue("Avenue_%d" % k, pts, 14 if k == 0 else 9)
# l'avenue nord rejoint le tunnel (dans la bande du port)
RUES.append(("Avenue_Tunnel", [(104.0, PC[1] + R_PLACE), (104.0, YN)], 16))


def route_segment(nom, a, b, larg, mat="route"):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1
    nx, ny = -dy / l * larg / 2, dx / l * larg / 2
    ext = 0.6 / l                                            # léger chevauchement entre segments
    a2 = (a[0] - dx * ext, a[1] - dy * ext)
    b2 = (b[0] + dx * ext, b[1] + dy * ext)
    pts = [(a2[0] + nx, a2[1] + ny), (a2[0] - nx, a2[1] - ny), (b2[0] - nx, b2[1] - ny), (b2[0] + nx, b2[1] + ny)]
    za, zb = H(*a) + 0.05, H(*b) + 0.05
    prisme(nom, "RUES", pts, min(za, zb) - 3, [za, za, zb, zb], mat)
    marquer_poly([(p[0] + (nx / (larg / 2)) * 1.5 * s, p[1] + (ny / (larg / 2)) * 1.5 * s) for p, s in zip(pts, (1, -1, -1, 1))], 3)


n_seg = 0
for nom, pts, larg in RUES:
    for k in range(len(pts) - 1):
        route_segment("SHI_%s_%03d" % (nom, k), pts[k], pts[k + 1], larg)
        n_seg += 1
for k in range(len(RUE_MARCHANDE) - 1):
    route_segment("SHI_Rue_Marchande_%02d" % k, RUE_MARCHANDE[k], RUE_MARCHANDE[k + 1], 12, "place")

# ---------------------------------------------------------------- sol : grandes dalles plates + tuiles en pente seulement dans le relief
TUILE = 15.0
nt = 0
nx_, ny_ = int((BX1 - BX0) / TUILE) + 1, int((BY1 - BY0) / TUILE) + 1
plat = [[False] * ny_ for _ in range(nx_)]
for i in range(nx_):
    for j in range(ny_):
        x0, y0 = BX0 + i * TUILE, BY0 + j * TUILE
        x1, y1 = min(x0 + TUILE, BX1), min(y0 + TUILE, BY1)
        hs = [H(x0, y0), H(x1, y0), H(x1, y1), H(x0, y1)]
        if max(abs(h) for h in hs) < 0.02:
            plat[i][j] = True
            continue
        prisme("SHI_Sol_%02d_%02d_a" % (i, j), "SOL", [(x0, y0), (x1, y0), (x1, y1)], min(hs) - 2, [hs[0], hs[1], hs[2]], "colline" if max(hs) > 1 else "trottoir")
        prisme("SHI_Sol_%02d_%02d_b" % (i, j), "SOL", [(x0, y0), (x1, y1), (x0, y1)], min(hs) - 2, [hs[0], hs[2], hs[3]], "colline" if max(hs) > 1 else "trottoir")
        nt += 2
for j in range(ny_):                                         # dalles plates : une par suite de tuiles plates sur la ligne
    i = 0
    while i < nx_:
        if plat[i][j]:
            k = i
            while k < nx_ and plat[k][j]:
                k += 1
            boite("SHI_Sol_Plat_%02d_%02d" % (j, i), "SOL", BX0 + i * TUILE, BY0 + j * TUILE, -1, min(BX0 + k * TUILE, BX1), min(BY0 + (j + 1) * TUILE, BY1), 0, "trottoir")
            nt += 1
            i = k
        else:
            i += 1

# ---------------------------------------------------------------- immeubles le long des rues (1re rangée + 2e rangée derrière)
nb_bat = 0


def poser_batiment(nom, centre, tangente, largeur, profondeur, haut, mat):
    tx, ty = tangente
    nx, ny = -ty, tx
    cx, cy = centre
    pts = [(cx + tx * s1 * largeur / 2 + nx * s2 * profondeur / 2, cy + ty * s1 * largeur / 2 + ny * s2 * profondeur / 2)
           for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    if not libre(pts):
        return False
    z0 = min(H(*p) for p in pts)
    haut = min(haut, HMAX - 2 - max(0, z0))
    prisme(nom, "BATIMENTS", pts, z0 - 1, z0 + haut, mat)
    marquer_poly(pts, 2)
    return True


for nom, pts, larg in RUES:
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy)
        if l < 1:
            continue
        tx, ty = dx / l, dy / l
        for cote in (-1, 1):
            for rang, ecart in ((0, 0.0), (1, 1.0)):
                if rang == 1 and R.random() < 0.35:
                    continue
                prof = R.uniform(10, 18)
                largeur = R.uniform(9, 17)
                off = larg / 2 + 2.5 + prof / 2 + ecart * (prof + 4)
                c = ((a[0] + b[0]) / 2 - ty * off * cote, (a[1] + b[1]) / 2 + tx * off * cote)
                h = R.choice((9, 12, 15, 18, 22, 26, 30, 35))
                if poser_batiment("SHI_Bat_%04d" % nb_bat, c, (tx, ty), min(largeur, l + 2), prof, h, "haut" if h >= 26 else "batiment"):
                    nb_bat += 1

# ---------------------------------------------------------------- remplissage : petits immeubles dans les espaces libres (ruelles de 3 m entre eux)
for essai in range(9000):
    x, y = R.uniform(BX0 + 4, BX1 - 4), R.uniform(BY0 + 4, BY1 - 4)
    a = math.atan2(y - PC[1], x - PC[0]) + math.pi / 2 + R.uniform(-0.15, 0.15)     # orienté selon les anneaux
    larg, prof = R.uniform(7, 14), R.uniform(7, 13)
    h = R.choice((7, 9, 12, 15, 18, 22, 26, 30))
    tx, ty = math.cos(a), math.sin(a)
    # on vérifie avec une marge de 1,5 m (la ruelle) puis on pose la vraie taille
    marge = [(x + tx * s1 * (larg / 2 + 1.5) - ty * s2 * (prof / 2 + 1.5), y + ty * s1 * (larg / 2 + 1.5) + tx * s2 * (prof / 2 + 1.5))
             for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    if not libre(marge):
        continue
    if poser_batiment("SHI_Bat_%04d" % nb_bat, (x, y), (tx, ty), larg, prof, h, "haut" if h >= 26 else "batiment"):
        marquer_poly(marge, 2)
        nb_bat += 1

# ---------------------------------------------------------------- place centrale en cuvette : sol, escaliers, statue, massifs
disque("SHI_Place", "PLACE", PC[0], PC[1], R_PLACE, H(*PC) - 2, H(*PC) + 0.12, "place", 48)
disque("SHI_Place_Statue", "PLACE", PC[0], PC[1], 1.5, H(*PC), H(*PC) + 3.5, "batiment", 12)
for a in range(8):
    x, y = PC[0] + 19 * math.cos(a * math.pi / 4 + 0.39), PC[1] + 19 * math.sin(a * math.pi / 4 + 0.39)
    disque("SHI_Place_Massif_%d" % a, "PLACE", x, y, 3.5, H(x, y) - 0.5, H(x, y) + 0.6, "parc", 16)
for k in range(32):                                          # gradins / escaliers tout autour de la cuvette
    a0, a1 = 2 * math.pi * k / 32, 2 * math.pi * (k + 1) / 32
    for s in range(3):
        r0, r1 = R_PLACE + s * 2.0, R_PLACE + (s + 1) * 2.0
        z = H(*PC) + 1.0 * (s + 1)
        pts = [(PC[0] + r0 * math.cos(a0), PC[1] + r0 * math.sin(a0)), (PC[0] + r1 * math.cos(a0), PC[1] + r1 * math.sin(a0)),
               (PC[0] + r1 * math.cos(a1), PC[1] + r1 * math.sin(a1)), (PC[0] + r0 * math.cos(a1), PC[1] + r0 * math.sin(a1))]
        prisme("SHI_Place_Gradin_%02d_%d" % (k, s), "PLACE", pts, z - 1.5, z, "trottoir")

# ---------------------------------------------------------------- rue marchande : 3 vendeurs + échoppes côté ouest
for k, nom in enumerate(("Vendeur_Tenues", "Vendeur_Accessoires", "Vendeur_Armes")):
    a, b = RUE_MARCHANDE[2 + k * 3], RUE_MARCHANDE[3 + k * 3]
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy)
    tx, ty = dx / l, dy / l
    c = ((a[0] + b[0]) / 2 + ty * 13, (a[1] + b[1]) / 2 - tx * 13)
    pts = [(c[0] + tx * s1 * 8 - ty * s2 * 7, c[1] + ty * s1 * 8 + tx * s2 * 7) for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    z0 = min(H(*p) for p in pts)
    prisme("SHI_" + nom, "RUE_MARCHANDE", pts, z0 - 1, z0 + 9, "boutique")
for k in range(10):
    p = RUE_MARCHANDE[k]
    disque("SHI_Etal_%d" % k, "RUE_MARCHANDE", p[0] + 4.5, p[1], 1.2, H(*p), H(*p) + 2.2, "boutique", 8)

# ---------------------------------------------------------------- parcs (RP, rassemblement) et zones de conflit (rondes)
for z, mat in (("espaces_rp", "rp"), ("rassemblement", "parc"), ("conflit_ne", "conflit"), ("conflit_s", "conflit")):
    (cx, cy), r = ZONES[z]
    disque("SHI_" + z, "ZONES", cx, cy, r, H(cx, cy) - 1, H(cx, cy) + 0.1, mat, 32)
    for k in range(8 if mat != "conflit" else 9):
        a, d = R.uniform(0, 2 * math.pi), R.uniform(5, r - 8)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        if mat == "conflit":
            w = R.uniform(5, 14)
            boite("SHI_%s_Ruine_%d" % (z, k), "ZONES", x, y, H(x, y), x + w, y + R.uniform(5, 14), H(x, y) + R.uniform(2, 14), "ruine")
        else:
            disque("SHI_%s_Arbre_%d" % (z, k), "ZONES", x, y, 2.5, H(x, y), H(x, y) + 7, "parc", 10)
disque("SHI_Scene_Evenements", "ZONES", -45, -95, 7, H(-45, -95), H(-45, -95) + 1.2, "batiment", 16)

# ---------------------------------------------------------------- accès égouts (6), passerelles entre les toits
for k, (x, y) in enumerate(((-80, -170), (10, -45), (50, -265), (PC[0] + 40, PC[1] - 40), (250, -130), (190, -45))):
    disque("SHI_Egout_%d" % k, "EGOUTS", x, y, 3, H(x, y), H(x, y) + 1.0, "egout", 12)
for k, (a, b) in enumerate((((0, -185), (35, -185)), ((185, -185), (220, -175)), ((170, -70), (205, -80)), ((-20, -60), (10, -75)))):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy)
    nx, ny = -dy / l * 2, dx / l * 2
    z = max(H(*a), H(*b)) + 14
    prisme("SHI_Passerelle_%d" % k, "PASSERELLES", [(a[0] + nx, a[1] + ny), (a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), (b[0] + nx, b[1] + ny)], z - 0.5, z, "passerelle")

# ---------------------------------------------------------------- enceinte autour de Shibuya (bâtiments hauts), le port au nord
for k, (x0, y0, x1, y1) in enumerate(((BX0 - 12, BY0 - 12, BX1 + 12, BY0), (BX0 - 12, BY0, BX0, BY1 + 12), (BX1, BY0, BX1 + 12, BY1 + 12),
                                      (BX0, BY1, -14, BY1 + 12), (136, BY1, BX1, BY1 + 12))):
    boite("SHI_Enceinte_%d" % k, "ENCEINTE", x0, y0, 0, x1, y1, HMAX, "haut")
boite("SHI_Port_Emprise", "PORT", -14, -26, 0, 136, 92, 3, "port")
boite("SHI_Port_Eau", "PORT", -14, 92, -2, 136, 220, -1.9, "eau")

# ---------------------------------------------------------------- rendu
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_shadows = True
sc.display.shading.show_cavity = True
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
os.makedirs(os.path.join(ICI, "apercus"), exist_ok=True)


def vue(nom, pos, cible, lens=24, ortho=None, res=(1800, 1800)):
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.location = pos
    dv = [cible[i] - pos[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(dv[0], dv[1]), -dv[2]), 0, math.atan2(dv[1], dv[0]) - math.pi / 2)
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    cam.data.lens = lens
    cam.data.clip_end = 5000
    sc.render.filepath = os.path.join(ICI, "apercus", "shibuya_" + nom + ".png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ICI, "shibuya_blockout.blend"))
vue("plan_dessus", (104, -40, 600), (104, -39.99, 0), ortho=530)
vue("vue_tunnel_vers_place", (104, -30, 3), (104, -145, -2), 20, res=(1600, 900))
vue("vue_place", (55, -95, 25), (104, -145, -3), 22, res=(1600, 900))
vue("vue_colline", (20, -190, 15), (-50, -245, 5), 22, res=(1600, 900))
vue("vue_aerienne", (-170, -400, 190), (100, -130, 0), 24, res=(1600, 900))
print("SHIBUYA BLOCKOUT : %d objets, %d bâtiments, %d segments de rue, %d tuiles de sol" % (len(bpy.data.objects), nb_bat, n_seg, nt))

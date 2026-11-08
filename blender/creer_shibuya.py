"""
SHIBUYA — VERSION DÉTAILLÉE, branchée sur le port (même fichier, même carte GMod).
Reprend le blockout validé (creer_shibuya_blockout.py : plan arrondi, relief, zones) avec :
  - vraies textures (façades, asphalte, dallage, herbe, gravier), immeubles avec auvents, néons, équipements de toit ;
  - mobilier de rue NEOTOKYO (lampadaires + lumières, distributeurs, poubelles, poteaux, panneaux, arrêts de bus) ;
  - place centrale : carrefour piéton, statue, arbres, bancs, écrans géants ; rue marchande : 3 boutiques AVEC intérieur
    (tenues, accessoires, armes blanches) + étals ; parcs (espace RP avec scène, zone de rassemblement avec fontaine) ;
  - zones de conflit (ruines, barricades, épaves), 6 accès égouts (escalier + couloir, vide au bout), passerelles sur les toits.
Lancer APRÈS creer_port_compact.py : blender.exe -b --factory-startup --python creer_shibuya.py   -> shibuya.blend (port + Shibuya)
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

import sys
sys.path.insert(0, ICI)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ICI, "port.blend"))       # le port déjà construit
import port_outils as O
for m in bpy.data.materials:                                               # matériaux du port déjà dans le fichier
    if m.name.startswith("PORT_"):
        O.MATS[m.name[5:]] = m
O.preparer_materiaux()
O.mat_image("herbe", "herbe", 3, 0.9)
O.mat_image("dallage", "dallage", 2.5, 0.8)
O.mat_image("gravier", "gravier", 3, 0.9)
O.mat_image("brique", "brique", 3, 0.85)
O.mat_image("enduit", "enduit", 3, 0.85)
O.mat_image("beton_mur2", "beton_mur2", 4, 0.9)
O.mat_image("carrelage", "carrelage", 1.5, 0.5)
O.mat_image("beton_sol3", "beton_sol3", 4, 0.9)
O.mat_image("grille", "grille", 2, 0.6, 0.5)
O.mat_uni("neon_rose", (1.0, 0.15, 0.55), 0.5, 0, emission=6.0)
O.mat_uni("neon_bleu", (0.15, 0.55, 1.0), 0.5, 0, emission=6.0)
O.mat_uni("neon_jaune", (1.0, 0.8, 0.15), 0.5, 0, emission=6.0)
O.mat_uni("neon_vert", (0.2, 1.0, 0.45), 0.5, 0, emission=6.0)
O.mat_uni("ecran", (0.55, 0.75, 1.0), 0.5, 0, emission=4.0)
O.mat_uni("bronze", (0.32, 0.22, 0.12), 0.5, 0.6)
O.mat_uni("auvent_rouge", (0.45, 0.06, 0.05), 0.6)
O.mat_uni("auvent_bleu", (0.06, 0.15, 0.40), 0.6)
O.mat_uni("auvent_vert", (0.08, 0.28, 0.12), 0.6)
if "CLIP_Bout_Du_Tunnel" in bpy.data.objects:                              # le tunnel du port débouche maintenant sur Shibuya
    bpy.data.objects.remove(bpy.data.objects["CLIP_Bout_Du_Tunnel"], do_unlink=True)
MAP = {"route": "asphalte", "trottoir": "beton_sol", "colline": "beton_sol3", "place": "dallage", "parc": "herbe", "rp": "herbe",
       "conflit": "gravier", "ruine": "beton_mur", "egout": "acier_gris", "boutique": "enduit", "passerelle": "acier_gris",
       "mur": "beton_mur", "eau": "eau"}
FACADES_VILLE = ["facade", "facade2", "facade3", "facade", "facade2", "facade3", "brique", "enduit", "beton_mur2"]
COLL = {}
BATS = []                                                    # immeubles posés : (nom, coins, centre, tangente, z0, hauteur, face)


def coll(nom):
    return O.collection("SHIBUYA/" + nom)


def objet(nom, c, v, f, mat):
    if mat in ("batiment", "haut"):
        mat = R.choice(FACADES_VILLE)
    return O.objet(nom, "SHIBUYA/" + c, v, f, MAP.get(mat, mat))


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


def modele(nom, c, chemin, x, y, rot=0.0, z=None):
    return O.modele(nom, "SHIBUYA/" + c, chemin, x, y, (H(x, y) if z is None else z) - 0.02, rot)


def local(c, u, v, tx, ty):
    """point dans le repère d'un bâtiment (u : le long de la rue, v : vers l'intérieur)"""
    return (c[0] + tx * u - ty * v, c[1] + ty * u + tx * v)


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

EGOUTS = [(-80.0, -170.0), (10.0, -48.0), (50.0, -262.0), (PC[0] + 45.0, PC[1] - 45.0), (250.0, -130.0), (190.0, -48.0)]
TROU = (1.3, 3.4)                                          # demi-largeur, demi-longueur du trou de l'escalier d'égout

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
    prisme(nom, "RUES", pts, min(za, zb) - 0.6, [za, za, zb, zb], mat)
    marquer_poly([(p[0] + (nx / (larg / 2)) * 1.5 * s, p[1] + (ny / (larg / 2)) * 1.5 * s) for p, s in zip(pts, (1, -1, -1, 1))], 3)


n_seg = 0
for nom, pts, larg in RUES:
    for k in range(len(pts) - 1):
        route_segment("SHI_%s_%03d" % (nom, k), pts[k], pts[k + 1], larg)
        n_seg += 1
for k in range(len(RUE_MARCHANDE) - 1):
    route_segment("SHI_Rue_Marchande_%02d" % k, RUE_MARCHANDE[k], RUE_MARCHANDE[k + 1], 12, "place")

# ---------------------------------------------------------------- égouts : chaque entrée va au centre d'une tuile plate et libre (pas sur une rue)
def tuile_libre(x0, y0):
    if max(abs(H(x0 + a, y0 + b)) for a in (0, 7.5, 15) for b in (0, 7.5, 15)) > 0.02:
        return False
    i0, j0 = ij(x0 + 7.5 - TROU[0] - 1.5, y0 + 7.5 - TROU[1] - 1.5)
    i1, j1 = ij(x0 + 7.5 + TROU[0] + 1.5, y0 + 7.5 + TROU[1] + 14)
    return not OCC[max(0, i0):i1 + 1, max(0, j0):j1 + 1].any()


for k, (ex, ey) in enumerate(list(EGOUTS)):
    meilleur = None
    for di in range(-6, 7):
        for dj in range(-6, 7):
            x0 = BX0 + (int((ex - BX0) / 15.0) + di) * 15.0
            y0 = BY0 + (int((ey - BY0) / 15.0) + dj) * 15.0
            if BX0 <= x0 and x0 + 15 <= BX1 and BY0 <= y0 and y0 + 15 <= BY1 - 15 and tuile_libre(x0, y0):
                d_ = abs(di) + abs(dj)
                if meilleur is None or d_ < meilleur[0]:
                    meilleur = (d_, x0 + 7.5, y0 + 7.5)
    if meilleur:
        EGOUTS[k] = (meilleur[1], meilleur[2])
        marquer_poly([(meilleur[1] - 5, meilleur[2] - 6), (meilleur[1] + 5, meilleur[2] - 6), (meilleur[1] + 5, meilleur[2] + 16), (meilleur[1] - 5, meilleur[2] + 16)], 5)
print("EGOUTS", EGOUTS)

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
        trous = [e for e in EGOUTS if x0 + 2 < e[0] < x1 - 2 and y0 + 4 < e[1] < y1 - 4]
        if trous:                                            # tuile avec un trou d'escalier d'égout (plate)
            ex, ey = trous[0]
            z_ = H(ex, ey)
            for k_, (a0, b0, a1, b1) in enumerate(((x0, y0, x1, ey - TROU[1]), (x0, ey + TROU[1], x1, y1), (x0, ey - TROU[1], ex - TROU[0], ey + TROU[1]),
                                                  (ex + TROU[0], ey - TROU[1], x1, ey + TROU[1]))):
                boite("SHI_Sol_Egout_%02d_%02d_%d" % (i, j, k_), "SOL", a0, b0, z_ - 1, a1, b1, z_, "trottoir")
            nt += 4
            continue
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

# ---------------------------------------------------------------- réservations : boutiques de la rue marchande, tours des passerelles
for k in range(3):
    a, b = RUE_MARCHANDE[2 + k * 3], RUE_MARCHANDE[3 + k * 3]
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
    c = ((a[0] + b[0]) / 2 + ty * 13, (a[1] + b[1]) / 2 - tx * 13)
    marquer_poly([(c[0] + tx * su * 10 + ty * sv * 9, c[1] + ty * su * 10 - tx * sv * 9) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))], 5)
for a, b in (((5.0, -185.0), (40.0, -185.0)), ((182.0, -188.0), (222.0, -176.0)), ((168.0, -72.0), (205.0, -84.0)), ((-25.0, -62.0), (8.0, -78.0))):
    marquer_disque(a[0], a[1], 5.5, 5)
    marquer_disque(b[0], b[1], 5.5, 5)

# ---------------------------------------------------------------- immeubles le long des rues (1re rangée + 2e rangée derrière)
nb_bat = 0


def poser_batiment(nom, centre, tangente, largeur, profondeur, haut, mat, face=None):
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
    BATS.append((nom, pts, centre, tangente, largeur, profondeur, z0, haut, face))
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
                if poser_batiment("SHI_Bat_%04d" % nb_bat, c, (tx, ty), min(largeur, l + 2), prof, h, "haut" if h >= 26 else "batiment",
                                  face=(cote * ty, -cote * tx) if rang == 0 else None):
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

# ================================================================== DÉTAILS (version finale)
NT_ = "models/nt/"
G = O.garde_corps


def lampadaire(nom, x, y, h=6.5):
    z = H(x, y)
    if not modele(nom, "MOBILIER", NT_ + "props_street/streetlamp_square", x, y, 0):
        O.cylindre(nom, "SHIBUYA/MOBILIER", x, y, z, z + h, 0.09, "acier_gris")
    O.lumiere(nom + "_Lumiere", "SHIBUYA/MOBILIER", (x, y, z + h - 0.6), 260, (1.0, 0.82, 0.6), 0.3)


# ---------------------------------------------------------------- immeubles : auvents, néons, équipements de toit, distributeurs
NEONS = ["neon_rose", "neon_bleu", "neon_jaune", "neon_vert"]
AUVENTS = ["auvent_rouge", "auvent_bleu", "auvent_vert", "tole_toit"]
for (nom, pts, c, (tx, ty), larg, prof, z0, haut, face) in BATS:
    # équipement de toit (climatiseur ou réservoir), un sur deux
    if R.random() < 0.5:
        u, v = R.uniform(-larg / 4, larg / 4), R.uniform(-prof / 4, prof / 4)
        p = local(c, u, v, tx, ty)
        if R.random() < 0.6:
            prisme(nom + "_Clim", "TOITS", [local(p, a_, b_, tx, ty) for a_, b_ in ((-1.2, -0.8), (1.2, -0.8), (1.2, 0.8), (-1.2, 0.8))],
                   z0 + haut, z0 + haut + 1.4, "acier_gris")
        else:
            O.cylindre(nom + "_Reservoir", "SHIBUYA/TOITS", p[0], p[1], z0 + haut, z0 + haut + 2.4, 1.1, "acier_gris", 10)
    if not face:
        continue
    fx, fy = face                                              # vers la rue
    # repère de la façade côté rue : u le long, devant = c + face * prof/2
    devant = (c[0] + fx * prof / 2, c[1] + fy * prof / 2)
    # auvent de rez-de-chaussée (une brosse)
    a_ = local(devant, -larg / 2 + 0.6, 0, tx, ty)
    b_ = local(devant, larg / 2 - 0.6, 0, tx, ty)
    zz = H(*devant)
    prisme(nom + "_Auvent", "FACADES", [a_, b_, (b_[0] + fx * 1.4, b_[1] + fy * 1.4), (a_[0] + fx * 1.4, a_[1] + fy * 1.4)], zz + 3.0, zz + 3.15, R.choice(AUVENTS))
    # enseigne néon verticale sur le coin (une brosse), sur les immeubles de 12 m et plus
    if haut >= 12 and R.random() < 0.75:
        p = local(devant, larg / 2 - 0.8, 0, tx, ty)
        hz = min(haut - 1, R.uniform(6, 12))
        prisme(nom + "_Neon", "FACADES", [p, (p[0] + fx * 1.0, p[1] + fy * 1.0), (p[0] + fx * 1.0 + tx * 0.25, p[1] + fy * 1.0 + ty * 0.25), (p[0] + tx * 0.25, p[1] + ty * 0.25)],
               zz + 4.0, zz + 4.0 + hz, R.choice(NEONS))
    # devant : distributeur ou panneau sur pied (vrais modèles NEOTOKYO), tournés vers la rue
    rot = math.atan2(fy, fx)
    r_ = R.random()
    p = (devant[0] + fx * 0.6, devant[1] + fy * 0.6)
    if r_ < 0.35:
        modele(nom + "_Distributeur", "MOBILIER", NT_ + "props_street/vend%d" % R.randint(1, 5), p[0], p[1], rot)
    elif r_ < 0.6:
        p = (devant[0] + fx * 1.6, devant[1] + fy * 1.6)
        modele(nom + "_Panneau_Pied", "MOBILIER", NT_ + "props_street/signage_stand%02d" % R.randint(1, 10), p[0], p[1], rot)

# ---------------------------------------------------------------- mobilier le long des rues : lampadaires + lumières, poubelles, poteaux
n_lamp = 0
for nom, pts, larg in RUES:
    dist = 0.0
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l < 0.5:
            continue
        tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
        dist += l
        if dist < 24:
            continue
        dist = 0.0
        cote = 1 if n_lamp % 2 else -1
        off = larg / 2 + 1.1
        x, y = a[0] - ty * off * cote, a[1] + tx * off * cote
        i_, j_ = ij(x, y)
        if not (0 <= i_ < N and 0 <= j_ < N) or OCC[i_, j_] in (2, 5, 9):
            continue
        lampadaire("SHI_Lampadaire_%03d" % n_lamp, x, y)
        r_ = R.random()
        x2, y2 = x + tx * 2.2, y + ty * 2.2
        if r_ < 0.25:
            modele("SHI_Poubelle_%03d" % n_lamp, "MOBILIER", NT_ + "props_street/recyclebin1", x2, y2, math.atan2(ty, tx))
        elif r_ < 0.4:
            modele("SHI_Poteau_%03d" % n_lamp, "MOBILIER", NT_ + "props_street/telephone_pole%d" % R.randint(1, 4), x2, y2, 0)
        elif r_ < 0.5:
            modele("SHI_Boite_Lettres_%03d" % n_lamp, "MOBILIER", NT_ + "props_street/mailbox%d" % R.randint(1, 2), x2, y2, math.atan2(-tx * cote, ty * cote))
        elif r_ < 0.6 and larg >= 9:
            modele("SHI_Arret_Bus_%03d" % n_lamp, "MOBILIER", NT_ + "props_street/busstop", x2 + tx * 2, y2 + ty * 2, math.atan2(ty, tx))
        n_lamp += 1

# ---------------------------------------------------------------- place centrale en cuvette : dallage, gradins, statue, arbres, bancs, écrans
zp = H(*PC)
disque("SHI_Place", "PLACE", PC[0], PC[1], R_PLACE, zp - 2, zp + 0.12, "dallage", 48)
for k in range(32):                                          # gradins tout autour (on s'y assoit, on y descend)
    a0, a1 = 2 * math.pi * k / 32, 2 * math.pi * (k + 1) / 32
    for s_ in range(3):
        r0, r1 = R_PLACE + s_ * 2.0, R_PLACE + (s_ + 1) * 2.0
        z = zp + 1.0 * (s_ + 1)
        q = [(PC[0] + r0 * math.cos(a0), PC[1] + r0 * math.sin(a0)), (PC[0] + r1 * math.cos(a0), PC[1] + r1 * math.sin(a0)),
             (PC[0] + r1 * math.cos(a1), PC[1] + r1 * math.sin(a1)), (PC[0] + r0 * math.cos(a1), PC[1] + r0 * math.sin(a1))]
        prisme("SHI_Place_Gradin_%02d_%d" % (k, s_), "PLACE", q, z - 1.5, z, "beton_sol")
# carrefour piéton : bandes blanches en étoile (comme le « scramble » de Shibuya)
for k in range(8):
    a = math.radians(22.5 + k * 45)
    for b_ in range(9):
        r = 6 + b_ * 3.0
        cx, cy = PC[0] + r * math.cos(a), PC[1] + r * math.sin(a)
        q = [local((cx, cy), su * 2.6, sv * 0.6, -math.sin(a), math.cos(a)) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        prisme("SHI_Place_Zebra_%d_%d" % (k, b_), "PLACE", q, zp + 0.12, zp + 0.13, "blanc_sol")
# statue du chien (Hachikō) en bronze sur son socle
disque("SHI_Statue_Socle", "PLACE", PC[0], PC[1], 1.6, zp + 0.12, zp + 1.3, "dallage", 8)
for nom_, (a0, b0, c0, a1, b1, c1) in (("Corps", (-0.7, -0.25, 1.75, 0.7, 0.25, 2.25)), ("Tete", (0.55, -0.2, 2.25, 1.0, 0.2, 2.7)),
                                       ("Museau", (1.0, -0.1, 2.3, 1.25, 0.1, 2.48)), ("Oreille_G", (0.65, -0.2, 2.7, 0.8, -0.05, 2.88)),
                                       ("Oreille_D", (0.65, 0.05, 2.7, 0.8, 0.2, 2.88)), ("Patte_AV", (0.45, -0.2, 1.3, 0.65, 0.2, 1.8)),
                                       ("Patte_AR", (-0.65, -0.22, 1.3, -0.3, 0.22, 1.85)), ("Queue", (-0.95, -0.05, 2.05, -0.7, 0.05, 2.35))):
    boite("SHI_Statue_" + nom_, "PLACE", PC[0] + a0, PC[1] + b0, zp + c0 - 0.0, PC[0] + a1, PC[1] + b1, zp + c1, "bronze")
for a in range(8):                                           # massifs d'arbres + bancs + lampadaires
    ang = a * math.pi / 4 + 0.39
    x, y = PC[0] + 19 * math.cos(ang), PC[1] + 19 * math.sin(ang)
    disque("SHI_Place_Massif_%d" % a, "PLACE", x, y, 3.2, zp, zp + 0.5, "herbe", 12)
    modele("SHI_Place_Arbre_%d" % a, "PLACE", NT_ + "props_nature/" + R.choice(("tree1", "tree2", "tree3", "sakurasv", "sakura2sv")), x, y, R.uniform(0, 6.28), zp + 0.5)
    bx, by = PC[0] + 24.5 * math.cos(ang), PC[1] + 24.5 * math.sin(ang)
    modele("SHI_Place_Banc_%d" % a, "PLACE", NT_ + "props_street/parkbench", bx, by, ang + math.pi, zp + 0.12)
    lx, ly = PC[0] + 12 * math.cos(ang + 0.39), PC[1] + 12 * math.sin(ang + 0.39)
    lampadaire("SHI_Place_Lampadaire_%d" % a, lx, ly)
# écrans géants sur les 3 plus hauts immeubles autour de la place (brosses lumineuses face à la place)
autour = sorted([b for b in BATS if math.hypot(b[2][0] - PC[0], b[2][1] - PC[1]) < 110], key=lambda b: -b[7])[:3]
for k, (nom, pts, c, (tx, ty), larg, prof, z0, haut, face) in enumerate(autour):
    d = (PC[0] - c[0], PC[1] - c[1])
    l = math.hypot(*d) or 1
    fx, fy = d[0] / l, d[1] / l
    # coin le plus proche de la place : écran posé sur la façade la plus tournée vers la place
    best = max(range(4), key=lambda i: (pts[i][0] - c[0]) * fx + (pts[i][1] - c[1]) * fy + (pts[(i + 1) % 4][0] - c[0]) * fx + (pts[(i + 1) % 4][1] - c[1]) * fy)
    p0, p1 = pts[best], pts[(best + 1) % 4]
    ex, ey = (p1[0] - p0[0]), (p1[1] - p0[1])
    el = math.hypot(ex, ey) or 1
    nx_, ny_ = ey / el, -ex / el
    if nx_ * fx + ny_ * fy < 0:
        nx_, ny_ = -nx_, -ny_
    m0 = (p0[0] + ex * 0.15, p0[1] + ey * 0.15)
    m1 = (p0[0] + ex * 0.85, p0[1] + ey * 0.85)
    zb = z0 + haut * 0.45
    prisme("SHI_Ecran_Geant_%d" % k, "PLACE", [m0, m1, (m1[0] + nx_ * 0.4, m1[1] + ny_ * 0.4), (m0[0] + nx_ * 0.4, m0[1] + ny_ * 0.4)],
           zb, min(z0 + haut - 1, zb + el * 0.45), "ecran")
    O.lumiere("SHI_Ecran_Geant_%d_Lumiere" % k, "SHIBUYA/PLACE", ((m0[0] + m1[0]) / 2 + nx_ * 4, (m0[1] + m1[1]) / 2 + ny_ * 4, zb + 3), 400, (0.6, 0.75, 1.0), 2.0)

# ---------------------------------------------------------------- rue marchande : étals, lanternes, 3 boutiques avec intérieur
for k in range(len(RUE_MARCHANDE) - 1):
    a, b = RUE_MARCHANDE[k], RUE_MARCHANDE[k + 1]
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    # étal côté est de la rue, sous une bâche
    p = (m[0] + ty * 4.2, m[1] - tx * 4.2)
    if k % 3 != 1:
        modele("SHI_Etal_%d" % k, "RUE_MARCHANDE", NT_ + "props_street/" + R.choice(("market_stand", "market_stand_long")), p[0], p[1], math.atan2(-tx, ty) + math.pi / 2)
        modele("SHI_Etal_%d_Bache" % k, "RUE_MARCHANDE", NT_ + "props_street/tarp_frame", p[0], p[1], math.atan2(ty, tx))
        modele("SHI_Etal_%d_Tabouret" % k, "RUE_MARCHANDE", NT_ + "props_street/stool_short", p[0] - ty * 1.6, p[1] + tx * 1.6, R.uniform(0, 6))
    # lanternes au-dessus de la rue (rouges, lumineuses)
    for s_ in (-1, 1):
        q = (m[0] - ty * 5.5 * s_, m[1] + tx * 5.5 * s_)
        O.cylindre("SHI_Lanterne_%d_%d" % (k, s_), "SHIBUYA/RUE_MARCHANDE", q[0], q[1], H(*q) + 3.4, H(*q) + 4.1, 0.25, "neon_rose", 8)
    O.lumiere("SHI_Rue_Marchande_Lumiere_%d" % k, "SHIBUYA/RUE_MARCHANDE", (m[0], m[1], H(*m) + 4.5), 180, (1.0, 0.5, 0.35), 0.4)

BOUTIQUES = [("Tenues", "neon_rose"), ("Accessoires", "neon_bleu"), ("Armes", "neon_jaune")]
for k, (nom_b, neon) in enumerate(BOUTIQUES):
    a, b = RUE_MARCHANDE[2 + k * 3], RUE_MARCHANDE[3 + k * 3]
    l = math.hypot(b[0] - a[0], b[1] - a[1])
    tx, ty = (b[0] - a[0]) / l, (b[1] - a[1]) / l
    # la boutique est côté ouest : v vers l'intérieur de la boutique, porte face à la rue
    c = ((a[0] + b[0]) / 2 + ty * 13, (a[1] + b[1]) / 2 - tx * 13)
    vx, vy = ty, -tx                                        # de la rue vers le fond de la boutique
    ux, uy = tx, ty
    L_, P_, HB = 8.0, 6.5, 4.2                              # demi-largeur, demi-profondeur, hauteur
    z0 = min(H(*local(c, su * L_, sv * P_, ux, uy)) for su in (-1, 1) for sv in (-1, 1))
    nb = "SHI_Boutique_" + nom_b
    cb = "RUE_MARCHANDE/" + nb


    def mur(n_, u0, v0, u1, v1, zz0, zz1, mat="enduit"):
        q = [local(c, u0, v0 * 1, ux, uy), local(c, u1, v0, ux, uy), local(c, u1, v1, ux, uy), local(c, u0, v1, ux, uy)]
        # local() : v le long de la normale (-ty, tx) ; ici on veut v vers (vx, vy) = (ty, -tx) -> on inverse le signe de v
        q = [(c[0] + ux * uu + vx * vv, c[1] + uy * uu + vy * vv) for uu, vv in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        prisme(nb + "_" + n_, cb, q, zz0, zz1, mat)


    mur("Sol", -L_, -P_, L_, P_, z0 - 1, z0 + 0.1, "carrelage")
    mur("Plafond", -L_, -P_, L_, P_, z0 + HB, z0 + HB + 0.3, "enduit")
    mur("Toit", -L_ - 0.4, -P_ - 0.6, L_ + 0.4, P_ + 0.4, z0 + HB + 0.3, z0 + HB + 0.5, "tole_toit")
    mur("Fond", -L_, P_ - 0.25, L_, P_, z0 + 0.1, z0 + HB, "enduit")
    mur("Cote_G", -L_, -P_, -L_ + 0.25, P_, z0 + 0.1, z0 + HB, "enduit")
    mur("Cote_D", L_ - 0.25, -P_, L_, P_, z0 + 0.1, z0 + HB, "enduit")
    mur("Devant_G", -L_, -P_, -1.5, -P_ + 0.25, z0 + 0.1, z0 + HB, "enduit")
    mur("Devant_D", 1.5, -P_, L_, -P_ + 0.25, z0 + 0.1, z0 + HB, "enduit")
    mur("Linteau", -1.5, -P_, 1.5, -P_ + 0.25, z0 + 2.6, z0 + HB, "enduit")
    mur("Vitrine_G", -L_ + 0.8, -P_ - 0.02, -2.2, -P_ + 0.02, z0 + 0.9, z0 + 2.8, "vitre")
    mur("Vitrine_D", 2.2, -P_ - 0.02, L_ - 0.8, -P_ + 0.02, z0 + 0.9, z0 + 2.8, "vitre")
    mur("Enseigne", -4.5, -P_ - 0.35, 4.5, -P_ - 0.05, z0 + 3.0, z0 + 3.9, neon)
    mur("Comptoir", -2.5, P_ - 2.6, 2.5, P_ - 1.8, z0 + 0.1, z0 + 1.05, "bois")
    O.lumiere(nb + "_Lumiere", "SHIBUYA/" + cb, (c[0] + vx * 0.5, c[1] + vy * 0.5, z0 + HB - 0.4), 110, (1.0, 0.92, 0.8), 0.4)
    # contenu selon la boutique (vrais modèles NEOTOKYO)
    rot_fond = math.atan2(-vy, -vx)                         # face à la porte
    def pp(u, v):
        return (c[0] + ux * u + vx * v, c[1] + uy * u + vy * v)
    if nom_b == "Tenues":
        for i_, u in enumerate((-5.5, -3.0, 3.0, 5.5)):
            q = pp(u, 1.0)
            modele(nb + "_Portant_%d" % i_, cb, NT_ + "props_office/clothing_rack", q[0], q[1], rot_fond + math.pi / 2, z0 + 0.1)
        for i_, u in enumerate((-6.5, 6.5)):
            q = pp(u, -4.5)
            modele(nb + "_Mannequin_%d" % i_, cb, NT_ + "props_street/mannequin_flat", q[0], q[1], rot_fond + math.pi, z0 + 0.1)
        q = pp(-6.8, 4.5)
        modele(nb + "_Combinaisons", cb, NT_ + "props_office/jumpsuit_rack", q[0], q[1], rot_fond + math.pi / 2, z0 + 0.1)
    elif nom_b == "Accessoires":
        for i_, u in enumerate((-6.5, 6.5)):
            q = pp(u, 2.0)
            modele(nb + "_Presentoir_%d" % i_, cb, NT_ + "props_office/magazine_rack", q[0], q[1], rot_fond + (math.pi / 2 if u < 0 else -math.pi / 2), z0 + 0.1)
        for i_, u in enumerate((-3.5, 3.5)):
            q = pp(u, 0.0)
            modele(nb + "_Etagere_%d" % i_, cb, NT_ + "props_warehouse/shelf1", q[0], q[1], rot_fond, z0 + 0.1)
        q = pp(0, 0.8)
        modele(nb + "_Bagages", cb, NT_ + "props_office/rack_luggage", q[0], q[1], rot_fond, z0 + 0.1)
    else:                                                    # armes blanches : armures et casques de samouraï
        for i_, u in enumerate((-5.5, -2.5, 2.5, 5.5)):
            q = pp(u, 4.6)
            modele(nb + "_Socle_%d" % i_, cb, NT_ + "props_office/samurai_displaybase", q[0], q[1], rot_fond, z0 + 0.1)
            modele(nb + "_Armure_%d" % i_, cb, NT_ + "props_office/samurai_armor", q[0], q[1], rot_fond, z0 + 0.3)
        for i_, u in enumerate((-1.6, 0.0, 1.6)):
            q = pp(u, P_ - 2.2)
            modele(nb + "_Casque_%d" % i_, cb, NT_ + "props_office/samurai_helmet%d" % (i_ + 1), q[0], q[1], rot_fond, z0 + 1.05)
    q = pp(4.0, P_ - 1.2)
    modele(nb + "_Chaise", cb, NT_ + "props_office/officechair02", q[0], q[1], rot_fond, z0 + 0.1)

# ---------------------------------------------------------------- parcs : espace RP (scène, bancs) et zone de rassemblement (fontaine)
ARBRES = ["tree1", "tree2", "tree3", "sakurasv", "sakura2sv", "sakura3sv", "tree05_sg", "tree06_sg"]
for z, (cx, cy), r in (("espaces_rp",) + ZONES["espaces_rp"], ("rassemblement",) + ZONES["rassemblement"]):
    zz = H(cx, cy)
    disque("SHI_Parc_" + z, "PARCS", cx, cy, r, zz - 1, zz + 0.1, "herbe", 32)
    disque("SHI_Parc_%s_Bordure" % z, "PARCS", cx, cy, r + 0.6, zz - 1, zz + 0.05, "beton_sol", 32)
    for k in range(16):
        a, d = R.uniform(0, 2 * math.pi), R.uniform(r * 0.45, r - 3)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        modele("SHI_Parc_%s_Arbre_%d" % (z, k), "PARCS", NT_ + "props_nature/" + R.choice(ARBRES), x, y, R.uniform(0, 6.28), zz + 0.1)
    for k in range(6):
        a, d = R.uniform(0, 2 * math.pi), R.uniform(r * 0.3, r - 4)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        modele("SHI_Parc_%s_Buisson_%d" % (z, k), "PARCS", NT_ + "props_nature/" + R.choice(("bushhedge", "gardenrock01", "gardenrock02", "potted_plants05")), x, y, R.uniform(0, 6.28), zz + 0.1)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        lampadaire("SHI_Parc_%s_Lampadaire_%d" % (z, k), cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a))
if True:                                                     # espace RP : scène couverte + rangées de bancs
    (cx, cy), r = ZONES["espaces_rp"]
    zz = H(cx, cy)
    sx, sy = cx, cy + r * 0.35
    boite("SHI_Scene", "PARCS", sx - 7, sy - 3, zz, sx + 7, sy + 3, zz + 1.0, "bois")
    boite("SHI_Scene_Fond", "PARCS", sx - 7, sy + 2.7, zz + 1.0, sx + 7, sy + 3, zz + 5.5, "bois")
    boite("SHI_Scene_Toit", "PARCS", sx - 7.5, sy - 3.5, zz + 5.5, sx + 7.5, sy + 3.2, zz + 5.8, "tole_toit")
    for xx in (sx - 7, sx + 6.75):
        boite("SHI_Scene_Pilier_%d" % int(xx), "PARCS", xx, sy - 3.2, zz + 1.0, xx + 0.25, sy - 2.95, zz + 5.5, "bois")
    modele("SHI_Scene_Torii", "PARCS", NT_ + "props_nature/small_torii", sx, sy - 6, 0, zz + 0.1)
    for rang in range(3):
        for k in range(4):
            modele("SHI_Scene_Banc_%d_%d" % (rang, k), "PARCS", NT_ + "props_street/parkbench", sx - 6 + k * 4, sy - 9 - rang * 3, -math.pi / 2, zz + 0.1)
    O.lumiere("SHI_Scene_Lumiere", "SHIBUYA/PARCS", (sx, sy - 1, zz + 5), 300, (1.0, 0.85, 0.65), 0.5)
if True:                                                     # zone de rassemblement : fontaine ronde + bancs autour
    (cx, cy), r = ZONES["rassemblement"]
    zz = H(cx, cy)
    disque("SHI_Fontaine_Bord", "PARCS", cx, cy, 5.0, zz, zz + 0.7, "dallage", 20)
    disque("SHI_Fontaine_Eau", "PARCS", cx, cy, 4.4, zz + 0.3, zz + 0.6, "eau", 20)
    disque("SHI_Fontaine_Centre", "PARCS", cx, cy, 0.8, zz + 0.6, zz + 2.2, "dallage", 10)
    for k in range(8):
        a = k * math.pi / 4
        modele("SHI_Rassemblement_Banc_%d" % k, "PARCS", NT_ + "props_street/parkbench", cx + 8 * math.cos(a), cy + 8 * math.sin(a), a + math.pi, zz + 0.1)

# ---------------------------------------------------------------- zones de conflit : ruines, barricades, épaves, feux
for z in ("conflit_ne", "conflit_s", "conflit_o"):
    if z not in ZONES or ZONES[z][1] <= 0:
        continue
    (cx, cy), r = ZONES[z]
    zz = H(cx, cy)
    disque("SHI_Conflit_" + z, "CONFLIT", cx, cy, r, zz - 1, zz + 0.08, "gravier", 32)
    for k in range(7):                                       # murs en ruine (hauteurs irrégulières)
        a, d = R.uniform(0, 2 * math.pi), R.uniform(4, r - 8)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        ang = R.uniform(0, math.pi)
        tx, ty = math.cos(ang), math.sin(ang)
        lw = R.uniform(5, 12)
        for s_ in range(3):
            u0, u1 = -lw / 2 + s_ * lw / 3, -lw / 2 + (s_ + 1) * lw / 3 - 0.3
            q = [local((x, y), u0, -0.3, tx, ty), local((x, y), u1, -0.3, tx, ty), local((x, y), u1, 0.3, tx, ty), local((x, y), u0, 0.3, tx, ty)]
            prisme("SHI_%s_Ruine_%d_%d" % (z, k, s_), "CONFLIT", q, zz, zz + R.uniform(1.2, 6.5), R.choice(("brique", "beton_mur", "beton_mur2")))
    for k in range(10):                                      # barricades tout autour
        a = 2 * math.pi * k / 10 + R.uniform(-0.1, 0.1)
        x, y = cx + (r - 2) * math.cos(a), cy + (r - 2) * math.sin(a)
        modele("SHI_%s_Barricade_%d" % (z, k), "CONFLIT", NT_ + "props_street/blockade%d" % R.randint(1, 4), x, y, a + math.pi / 2)
    for k in range(3):                                       # épaves de voitures
        a, d = R.uniform(0, 2 * math.pi), R.uniform(3, r * 0.6)
        modele("SHI_%s_Epave_%d" % (z, k), "CONFLIT", "models/props_vehicles/" + R.choice(("car002a", "car004a")), cx + d * math.cos(a), cy + d * math.sin(a), R.uniform(0, 6.28))
    for k in range(3):
        a, d = R.uniform(0, 2 * math.pi), R.uniform(3, r * 0.7)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        O.fut("SHI_%s_Fut_%d" % (z, k), "SHIBUYA/CONFLIT", x, y, H(x, y))
        boite("SHI_%s_Feu_%d" % (z, k), "CONFLIT", x - 0.15, y - 0.15, H(x, y) + 0.95, x + 0.15, y + 0.15, H(x, y) + 1.1, "sodium")
        O.lumiere("SHI_%s_Feu_%d_Lumiere" % (z, k), "SHIBUYA/CONFLIT", (x, y, H(x, y) + 1.6), 90, (1.0, 0.45, 0.15), 0.4)

# ---------------------------------------------------------------- accès égouts : bordure + garde-corps, escalier qui descend, couloir (vide au bout)
for k, (ex, ey) in enumerate(EGOUTS):
    z = H(ex, ey)
    ce = "EGOUTS/SHI_Egout_%d" % k
    dx, dy = TROU
    boite("SHI_Egout_%d_Muret_O" % k, ce, ex - dx - 0.25, ey - dy, z, ex - dx, ey + dy, z + 0.6, "beton_mur")
    boite("SHI_Egout_%d_Muret_E" % k, ce, ex + dx, ey - dy, z, ex + dx + 0.25, ey + dy, z + 0.6, "beton_mur")
    boite("SHI_Egout_%d_Muret_N" % k, ce, ex - dx - 0.25, ey + dy, z, ex + dx + 0.25, ey + dy + 0.25, z + 0.6, "beton_mur")
    G("SHI_Egout_%d_GC_O" % k, "SHIBUYA/" + ce, (ex - dx - 0.12, ey - dy), (ex - dx - 0.12, ey + dy), z + 0.6, 0.5)
    G("SHI_Egout_%d_GC_E" % k, "SHIBUYA/" + ce, (ex + dx + 0.12, ey - dy), (ex + dx + 0.12, ey + dy), z + 0.6, 0.5)
    # puits (murs sous le sol) + escalier qui descend vers le sud... vers le nord (entrée au sud du trou)
    zf = z - 5.2
    boite("SHI_Egout_%d_Puits_O" % k, ce, ex - dx - 0.3, ey - dy, zf, ex - dx, ey + dy + 12.3, z - 1, "beton_mur")
    boite("SHI_Egout_%d_Puits_E" % k, ce, ex + dx, ey - dy, zf, ex + dx + 0.3, ey + dy + 12.3, z - 1, "beton_mur")
    boite("SHI_Egout_%d_Puits_S" % k, ce, ex - dx - 0.3, ey - dy - 0.3, zf, ex + dx + 0.3, ey - dy, z, "beton_mur")
    # rampe en escalier (une seule brosse inclinée, praticable) + marches visuelles fines
    prisme("SHI_Egout_%d_Escalier" % k, ce, [(ex - dx, ey - dy), (ex + dx, ey - dy), (ex + dx, ey + dy), (ex - dx, ey + dy)], zf - 0.3, [z - 0.02, z - 0.02, zf, zf], "beton_sol")
    # couloir sous la rue : sol, plafond (sous la dalle), lumière, mur invisible au bout (sera mappé plus tard)
    boite("SHI_Egout_%d_Couloir_Sol" % k, ce, ex - dx, ey + dy, zf - 0.3, ex + dx, ey + dy + 12, zf, "beton_sol")
    boite("SHI_Egout_%d_Couloir_Plafond" % k, ce, ex - dx - 0.3, ey + dy, z - 1.4, ex + dx + 0.3, ey + dy + 12.3, z - 1.0, "beton_mur")
    boite("SHI_Egout_%d_Couloir_Fond" % k, ce, ex - dx - 0.3, ey + dy + 12, zf - 0.3, ex + dx + 0.3, ey + dy + 12.3, z - 1.0, "beton_mur")
    boite("SHI_Egout_%d_Rigole" % k, ce, ex - 0.4, ey + dy, zf - 0.02, ex + 0.4, ey + dy + 12, zf + 0.01, "eau")
    O.lumiere("SHI_Egout_%d_Lumiere" % k, "SHIBUYA/" + ce, (ex, ey + dy + 5, z - 1.8), 60, (0.7, 1.0, 0.7), 0.3)
    boite("SHI_Egout_%d_Lampe" % k, ce, ex - 0.2, ey + dy + 4.8, z - 1.45, ex + 0.2, ey + dy + 5.2, z - 1.4, "secours")

# ---------------------------------------------------------------- passerelles entre les toits : 2 tours d'escalier + pont avec garde-corps
def tour_escalier(nom, x, y, z0, z1, ang):
    """petite tour métallique : rampes en escalier (brosses inclinées) en zigzag, paliers ; renvoie le point du haut"""
    tx, ty = math.cos(ang), math.sin(ang)
    c = "PASSERELLES/" + nom
    n = max(1, round((z1 - z0) / 3.5))
    hm = (z1 - z0) / n
    for k in range(n):
        sens = 1 if k % 2 == 0 else -1
        va = 0.0 if k % 2 == 0 else 1.3
        ua, ub = (-2.6, 2.6) if sens > 0 else (2.6, -2.6)
        za, zb = z0 + k * hm, z0 + (k + 1) * hm
        q = [local((x, y), ua, va, tx, ty), local((x, y), ub, va, tx, ty), local((x, y), ub, va + 1.2, tx, ty), local((x, y), ua, va + 1.2, tx, ty)]
        prisme("%s_Volee_%d" % (nom, k), c, q, min(za, zb) - 0.15, [za, zb, zb, za], "grille")
        uP = ub
        q = [local((x, y), uP - 0.7, 0, tx, ty), local((x, y), uP + 0.7, 0, tx, ty), local((x, y), uP + 0.7, 2.5, tx, ty), local((x, y), uP - 0.7, 2.5, tx, ty)]
        prisme("%s_Palier_%d" % (nom, k), c, q, zb - 0.15, zb, "grille")
        for pu in (-2.6, 2.6):
            for pv in (0.0, 2.5):
                p = local((x, y), pu, pv, tx, ty)
                O.boite("%s_Poteau_%d_%d_%d" % (nom, k, int(pu), int(pv)), "SHIBUYA/" + c, p[0] - 0.06, p[1] - 0.06, z0, p[0] + 0.06, p[1] + 0.06, zb, "acier_gris") if k == n - 1 else None
    return local((x, y), (2.6 if n % 2 == 1 else -2.6), 1.25, tx, ty)


PASSERELLES = [((5.0, -185.0), (40.0, -185.0)), ((182.0, -188.0), (222.0, -176.0)), ((168.0, -72.0), (205.0, -84.0)), ((-25.0, -62.0), (8.0, -78.0))]
for k, (a, b) in enumerate(PASSERELLES):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    zb = max(H(*a), H(*b)) + 12.0
    ha = tour_escalier("SHI_Passerelle_%d_Tour_A" % k, a[0], a[1], H(*a), zb, ang)
    hb = tour_escalier("SHI_Passerelle_%d_Tour_B" % k, b[0], b[1], H(*b), zb, ang + math.pi)
    l = math.hypot(hb[0] - ha[0], hb[1] - ha[1])
    tx, ty = (hb[0] - ha[0]) / l, (hb[1] - ha[1]) / l
    nx_, ny_ = -ty * 1.2, tx * 1.2
    prisme("SHI_Passerelle_%d_Pont" % k, "PASSERELLES", [(ha[0] + nx_, ha[1] + ny_), (ha[0] - nx_, ha[1] - ny_), (hb[0] - nx_, hb[1] - ny_), (hb[0] + nx_, hb[1] + ny_)],
           zb - 0.35, zb, "grille")
    for s_ in (-1, 1):
        G("SHI_Passerelle_%d_GC_%d" % (k, s_), "SHIBUYA/PASSERELLES", (ha[0] + nx_ * s_, ha[1] + ny_ * s_), (hb[0] + nx_ * s_, hb[1] + ny_ * s_), zb, 1.05)

# ---------------------------------------------------------------- enceinte autour de Shibuya (bâtiments hauts), le port au nord
for k, (x0, y0, x1, y1) in enumerate(((BX0 - 12, BY0 - 12, BX1 + 12, BY0), (BX0 - 12, BY0, BX0, BY1 + 12), (BX1, BY0, BX1 + 12, BY1 + 12),
                                      (BX0, BY1, -14, BY1 + 12), (136, BY1, BX1, BY1 + 12))):
    boite("SHI_Enceinte_%d" % k, "ENCEINTE", x0, y0, 0, x1, y1, HMAX, "haut")

# ================================================================== fichier
if O.COLL_SOURCES in bpy.context.view_layer.layer_collection.children:
    bpy.context.view_layer.layer_collection.children[O.COLL_SOURCES].exclude = True
for o in bpy.data.objects:                                          # UV pour l'affichage « Solide »
    if o.type != "MESH" or o.data.uv_layers:
        continue
    me = o.data
    uv = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        nx, ny, nz = (abs(c) for c in poly.normal)
        for li in poly.loop_indices:
            x, y, z = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (x / 2, y / 2) if nz >= nx and nz >= ny else ((y / 2, z / 2) if nx >= ny else (x / 2, z / 2))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ICI, "shibuya.blend"))
print("SHIBUYA DÉTAILLÉ : %d objets, %d immeubles, %d lampadaires -> shibuya.blend" % (len(bpy.data.objects), nb_bat, n_lamp))

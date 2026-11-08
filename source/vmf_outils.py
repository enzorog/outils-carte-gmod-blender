"""
Outils pour écrire une carte Source (.vmf) par script : boîtes, murs avec ouvertures, dalles trouées, toits,
escaliers, maisons, entités, props, collines (déplacements). Utilisé par generer_tokyo.py.
"""
import os, math, random

ICI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- textures (toutes fournies avec GMod / HL2)
T = {
    "sol": "nature/grassfloor002a",           # herbe (le terrain)
    "falaise": "stone/stonewall050a",         # flancs du plateau, murets, murs de pierre
    "chemin": "stone/stonefloor006a",         # chemins pavés
    "torii": "wood/woodwall029a",             # bois sombre (poteaux, poutres)
    "mur_ext": "plaster/plasterwall044b",     # murs extérieurs (enduit clair)
    "mur_int": "plaster/plasterwall044c",     # cloisons intérieures
    "plancher": "wood/woodfloor007a",         # planchers
    "plafond": "wood/woodfloor008a",          # plafonds en planches
    "toit": "building_template/roof_template001a",
    "marche": "wood/woodstair002a",
    "bureau": "wood/woodwall009a",            # meubles en bois (brosses)
    "tableau": "wood/woodwall029a",
    "metal": "metal/metalwall070a",           # réserve des reliques
    "socle": "stone/stonewall050c",           # socles de pierre
    "sable": "nature/sandfloor010a",          # terrain d'entraînement
    "enceinte": "stone/stonewall050a",        # mur du bord de la carte (caché par la forêt)
    "ciel": "tools/toolsskybox",
    "nodraw": "tools/toolsnodraw",
    # sol de chaque domaine de clan (pour les reconnaître)
    "gojo": "stone/stonefloor006a",
    "zenin": "nature/gravelfloor004a",
    "kamo": "stone/stonefloor011a",
    "inumaki": "nature/dirtfloor006a",
}

# ---------------------------------------------------------------- écriture VMF
solides, entites, zones = [], [], []
_cible = []          # si non vide : les solides vont dans cette liste (pour une entité de brosse : porte…)
DETAIL_AUTO = [False]  # True : les solides du monde vont dans un func_detail (ne coupent pas la visibilité)
DETAIL_SOLIDES = []
_id = [10]


def nid():
    _id[0] += 1
    return _id[0]


def _vec(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _croix(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _axes(n):
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if az >= ax and az >= ay:
        return "[1 0 0 0] 0.25", "[0 -1 0 0] 0.25"
    if ax >= ay:
        return "[0 1 0 0] 0.25", "[0 0 -1 0] 0.25"
    return "[1 0 0 0] 0.25", "[0 0 -1 0] 0.25"


def solide(faces, centre, disp=None):
    """faces : liste de (p1, p2, p3, matériau) ; les 3 points sont sur la face, l'ordre est corrigé ici.
    disp : (indice de la face, texte dispinfo) pour transformer une face en déplacement (colline)."""
    cotes = []
    for i, (p1, p2, p3, mat) in enumerate(faces):
        n = _croix(_vec(p1, p2), _vec(p3, p2))
        d = _vec(centre, p2)
        if n[0] * d[0] + n[1] * d[1] + n[2] * d[2] > 0:      # la normale doit sortir du solide
            p1, p3 = p3, p1
            n = (-n[0], -n[1], -n[2])
        u, v = _axes(n)
        pl = "(%g %g %g) (%g %g %g) (%g %g %g)" % (p1 + p2 + p3)
        extra = disp[1] if disp and disp[0] == i else ""
        lm = "32" if extra else "16"          # les grandes collines ont besoin d'une échelle de lumière plus large
        cotes.append('\t\tside\n\t\t{\n\t\t\t"id" "%d"\n\t\t\t"plane" "%s"\n\t\t\t"material" "%s"\n'
                     '\t\t\t"uaxis" "%s"\n\t\t\t"vaxis" "%s"\n\t\t\t"rotation" "0"\n\t\t\t"lightmapscale" "%s"\n'
                     '\t\t\t"smoothing_groups" "0"\n%s\t\t}\n' % (nid(), pl, mat.upper(), u, v, lm, extra))
    (_cible[-1] if _cible else (DETAIL_SOLIDES if DETAIL_AUTO[0] and not disp else solides)).append('\tsolid\n\t{\n\t\t"id" "%d"\n%s\t\teditor\n\t\t{\n\t\t\t"color" "0 180 0"\n'
                   '\t\t\t"visgroupshown" "1"\n\t\t\t"visgroupautoshown" "1"\n\t\t}\n\t}\n' % (nid(), "".join(cotes)))


def boite(x0, y0, z0, x1, y1, z1, mat, dessus=None, dessous=None):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    if x1 - x0 < 1 or y1 - y0 < 1 or z1 - z0 < 1:
        return
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    solide([
        ((x0, y1, z1), (x1, y1, z1), (x1, y0, z1), dessus or mat),
        ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), dessous or mat),
        ((x0, y1, z1), (x0, y0, z1), (x0, y0, z0), mat),
        ((x1, y1, z0), (x1, y0, z0), (x1, y0, z1), mat),
        ((x1, y1, z1), (x0, y1, z1), (x0, y1, z0), mat),
        ((x1, y0, z0), (x0, y0, z0), (x0, y0, z1), mat),
    ], c)


def toit(x0, y0, x1, y1, z, h, mat=None, debord=64):
    """toit à deux pentes, faîte le long du côté le plus long"""
    mat = mat or T["toit"]
    x0, y0, x1, y1 = x0 - debord, y0 - debord, x1 + debord, y1 + debord
    if x1 - x0 >= y1 - y0:
        ym = (y0 + y1) / 2
        a, b = (x0, ym, z + h), (x1, ym, z + h)
        faces = [
            ((x0, y0, z), (x1, y0, z), (x1, y1, z), mat),           # dessous
            ((x0, y0, z), (x1, y0, z), b, mat),                       # pente sud
            ((x1, y1, z), (x0, y1, z), a, mat),                       # pente nord
            ((x0, y0, z), (x0, y1, z), a, mat),                       # pignon ouest
            ((x1, y1, z), (x1, y0, z), b, mat),                       # pignon est
        ]
    else:
        xm = (x0 + x1) / 2
        a, b = (xm, y0, z + h), (xm, y1, z + h)
        faces = [
            ((x0, y0, z), (x1, y0, z), (x1, y1, z), mat),
            ((x0, y1, z), (x0, y0, z), a, mat),                       # pente ouest
            ((x1, y0, z), (x1, y1, z), b, mat),                       # pente est
            ((x0, y0, z), (x1, y0, z), a, mat),                       # pignon sud
            ((x1, y1, z), (x0, y1, z), b, mat),                       # pignon nord
        ]
    solide(faces, ((x0 + x1) / 2, (y0 + y1) / 2, z + h / 3))


def entite(classe, origine, **cles):
    lignes = ['\t"id" "%d"\n\t"classname" "%s"\n' % (nid(), classe)]
    for k, v in cles.items():
        lignes.append('\t"%s" "%s"\n' % (k, v))
    lignes.append('\t"origin" "%g %g %g"\n' % origine)
    entites.append("entity\n{\n%s\teditor\n\t{\n\t\t\"color\" \"220 30 220\"\n\t\t\"visgroupshown\" \"1\"\n"
                   "\t\t\"visgroupautoshown\" \"1\"\n\t}\n}\n" % "".join(lignes))


def lampe(x, y, z, force=300, couleur="255 196 132"):
    entite("light", (x, y, z), _light="%s %d" % (couleur, force), _quadratic_attn="1", _linear_attn="0", _constant_attn="0")


def zone(x0, y0, x1, y1, nom, couleur, niveau=0):
    zones.append((x0, y0, x1, y1, nom, couleur, niveau))


# ---------------------------------------------------------------- outils de construction
def _mur(a0, a1, z0, z1, ouvertures, poser):
    """découpe un mur (de a0 à a1, de z0 à z1) autour d'ouvertures (a, b, za, zb), même superposées (2 étages)"""
    coupes = sorted({a0, a1} | {o[0] for o in ouvertures} | {o[1] for o in ouvertures})
    coupes = [c for c in coupes if a0 <= c <= a1]
    for i in range(len(coupes) - 1):
        a, b = coupes[i], coupes[i + 1]
        m = (a + b) / 2
        trous = sorted((o[2], o[3]) for o in ouvertures if o[0] < m < o[1])
        z = z0
        for za, zb in trous:
            poser(a, b, z, za)
            z = max(z, zb)
        poser(a, b, z, z1)


FENETRE = []          # [matériau] : si rempli, les fenêtres reçoivent un panneau de shoji (papier éclairé)


def _est_fenetre(z0, za, zb):
    return FENETRE and za > z0 + 20 and zb - za <= 100


def mur_x(x0, x1, y0, y1, z0, z1, mat, ouvertures=()):
    """mur le long de X (de x0 à x1, épaisseur y0..y1) ; ouvertures = (xa, xb, za, zb)"""
    _mur(x0, x1, z0, z1, ouvertures, lambda a, b, za, zb: boite(a, y0, za, b, y1, zb, mat))
    for a, b, za, zb in ouvertures:
        if _est_fenetre(z0, za, zb):
            ym = (y0 + y1) / 2
            boite(a, ym - 2, za, b, ym + 2, zb, FENETRE[0])


def mur_y(y0, y1, x0, x1, z0, z1, mat, ouvertures=()):
    """mur le long de Y (de y0 à y1, épaisseur x0..x1) ; ouvertures = (ya, yb, za, zb)"""
    _mur(y0, y1, z0, z1, ouvertures, lambda a, b, za, zb: boite(x0, a, za, x1, b, zb, mat))
    for a, b, za, zb in ouvertures:
        if _est_fenetre(z0, za, zb):
            xm = (x0 + x1) / 2
            boite(xm - 2, a, za, xm + 2, b, zb, FENETRE[0])


def dalle_trouee(x0, y0, x1, y1, z0, z1, mat, trous=(), dessus=None, dessous=None):
    """dalle rectangulaire percée de trous rectangulaires (découpée en morceaux)"""
    xs = sorted({x0, x1} | {t[0] for t in trous} | {t[2] for t in trous})
    ys = sorted({y0, y1} | {t[1] for t in trous} | {t[3] for t in trous})
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if any(t[0] < cx < t[2] and t[1] < cy < t[3] for t in trous):
                continue
            boite(xs[i], ys[j], z0, xs[i + 1], ys[j + 1], z1, mat, dessus, dessous)


def fenetres(debut, fin, za, zb, eviter=(), pas=320, largeur=96):
    """ouvertures régulières le long d'un mur, en évitant les portes"""
    res = []
    n = int((fin - debut) // pas)
    for k in range(n):
        c = debut + (k + 0.5) * (fin - debut) / n
        a, b = c - largeur / 2, c + largeur / 2
        if any(not (b <= e0 - 16 or a >= e1 + 16) for e0, e1 in eviter):
            continue
        res.append((a, b, za, zb))
    return res


def chemin(x0, y0, x1, y1, z=0):
    boite(x0, y0, z, x1, y1, z + 2, T["chemin"])
    zone(x0, y0, x1, y1, "", (190, 170, 140), -1)


def torii(cx, cy, z, largeur=448, hauteur=448, axe="x"):
    m = T["torii"]
    l = largeur / 2
    if axe == "x":
        for sx in (-1, 1):
            boite(cx + sx * l - 20, cy - 20, z, cx + sx * l + 20, cy + 20, z + hauteur, m)
        boite(cx - l - 96, cy - 28, z + hauteur, cx + l + 96, cy + 28, z + hauteur + 32, m)      # kasagi
        boite(cx - l - 32, cy - 16, z + hauteur - 96, cx + l + 32, cy + 16, z + hauteur - 72, m)  # nuki
    else:
        for sy in (-1, 1):
            boite(cx - 20, cy + sy * l - 20, z, cx + 20, cy + sy * l + 20, z + hauteur, m)
        boite(cx - 28, cy - l - 96, z + hauteur, cx + 28, cy + l + 96, z + hauteur + 32, m)
        boite(cx - 16, cy - l - 32, z + hauteur - 96, cx + 16, cy + l + 32, z + hauteur - 72, m)
    zone(cx - l - 40, cy - 40, cx + l + 40, cy + 40, "", (240, 120, 40), 3) if axe == "x" else \
        zone(cx - 40, cy - l - 40, cx + 40, cy + l + 40, "", (240, 120, 40), 3)


def escalier_y(x0, x1, y0, z0, n, haut=16, prof=32, sens=1, mat=None):
    """escalier qui monte vers +Y (sens=1) ou -Y (sens=-1) ; marches pleines"""
    mat = mat or T["marche"]
    for k in range(1, n + 1):
        ya = y0 + sens * (k - 1) * prof
        boite(x0, ya, z0, x1, ya + sens * prof, z0 + k * haut, mat, dessus=mat)


def escalier_x(y0, y1, x0, z0, n, haut=16, prof=24, sens=1, descend=False, mat=None):
    """escalier le long de X ; descend=True : chaque marche descend de « haut » (pour la réserve)"""
    mat = mat or T["marche"]
    for k in range(1, n + 1):
        xa = x0 + sens * (k - 1) * prof
        if descend:
            boite(xa, y0, z0 - 384, xa + sens * prof, y1, z0 - k * haut, mat)
        else:
            boite(xa, y0, z0, xa + sens * prof, y1, z0 + k * haut, mat)


def pupitres(x0, y0, x1, y1, z, face="S"):
    """rangées de pupitres + bureau du professeur + tableau, face au mur « face »"""
    w, d = x1 - x0, y1 - y0
    for i in range(3):
        for j in range(3):
            cx = x0 + w * (i + 1) / 4
            cy = y0 + d * (0.25 + 0.17 * j) if face == "N" else y1 - d * (0.25 + 0.17 * j)
            boite(cx - 22, cy - 14, z, cx + 22, cy + 14, z + 30, T["bureau"])
    if face == "S":
        boite((x0 + x1) / 2 - 48, y0 + 56, z, (x0 + x1) / 2 + 48, y0 + 88, z + 34, T["bureau"])
        boite(x0 + w * 0.2, y0, z + 40, x1 - w * 0.2, y0 + 4, z + 104, T["tableau"])
    else:
        boite((x0 + x1) / 2 - 48, y1 - 88, z, (x0 + x1) / 2 + 48, y1 - 56, z + 34, T["bureau"])
        boite(x0 + w * 0.2, y1 - 4, z + 40, x1 - w * 0.2, y1, z + 104, T["tableau"])


def maison(x0, y0, x1, y1, z0, nom, couleur, porte="S", h=176, mat=None, cloison=True):
    """maison simple : plancher, 4 murs (porte + fenêtres), une cloison avec porte, plafond, toit, lumières"""
    mat = mat or T["mur_ext"]
    e = 16
    boite(x0, y0, z0, x1, y1, z0 + 4, T["plancher"])
    zb = z0 + 4
    zp, zf0, zf1 = zb + 120, zb + 56, zb + 120
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    p = {}
    for cote in "NSEW":
        p[cote] = []
    if porte in "NS":
        p[porte] = [(cx - 56, cx + 56, zb, zp)]
    else:
        p[porte] = [(cy - 56, cy + 56, zb, zp)]
    ev = lambda c: [(a, b) for a, b, _, _ in p[c]]
    mur_x(x0, x1, y0, y0 + e, zb, z0 + h, mat, p["S"] + fenetres(x0 + e, x1 - e, zf0, zf1, ev("S")))
    mur_x(x0, x1, y1 - e, y1, zb, z0 + h, mat, p["N"] + fenetres(x0 + e, x1 - e, zf0, zf1, ev("N")))
    mur_y(y0 + e, y1 - e, x0, x0 + e, zb, z0 + h, mat, p["W"] + fenetres(y0 + e, y1 - e, zf0, zf1, ev("W")))
    mur_y(y0 + e, y1 - e, x1 - e, x1, zb, z0 + h, mat, p["E"] + fenetres(y0 + e, y1 - e, zf0, zf1, ev("E")))
    if cloison:
        if x1 - x0 >= y1 - y0:
            mur_y(y0 + e, y1 - e, cx - 8, cx + 8, zb, z0 + h, T["mur_int"], [(cy - 48, cy + 48, zb, zb + 112)])
            lampe((x0 + cx) / 2, cy, z0 + h - 24)
            lampe((cx + x1) / 2, cy, z0 + h - 24)
        else:
            mur_x(x0 + e, x1 - e, cy - 8, cy + 8, zb, z0 + h, T["mur_int"], [(cx - 48, cx + 48, zb, zb + 112)])
            lampe(cx, (y0 + cy) / 2, z0 + h - 24)
            lampe(cx, (cy + y1) / 2, z0 + h - 24)
    else:
        lampe(cx, cy, z0 + h - 24)
    boite(x0, y0, z0 + h, x1, y1, z0 + h + 16, T["plafond"], dessus=T["toit"])
    toit(x0, y0, x1, y1, z0 + h + 16, int(min(x1 - x0, y1 - y0) * 0.32), debord=48)
    zone(x0, y0, x1, y1, nom, couleur, 2)


def batiment_couloir(x0, y0, x1, y1, z0, nb, nom, couleur, h=176):
    """bâtiment long : un couloir au milieu (le long de X), des chambres de chaque côté"""
    e = 16
    boite(x0, y0, z0, x1, y1, z0 + 4, T["plancher"])
    zb = z0 + 4
    yc = (y0 + y1) / 2
    w = (x1 - x0) / nb
    # murs extérieurs : portes aux deux bouts du couloir, une fenêtre par chambre
    fen = [(x0 + w * (k + 0.5) - 48, x0 + w * (k + 0.5) + 48, zb + 56, zb + 120) for k in range(nb)]
    mur_x(x0, x1, y0, y0 + e, zb, z0 + h, T["mur_ext"], fen)
    mur_x(x0, x1, y1 - e, y1, zb, z0 + h, T["mur_ext"], fen)
    for xx in (x0, x1 - e):
        mur_y(y0 + e, y1 - e, xx, xx + e, zb, z0 + h, T["mur_ext"], [(yc - 56, yc + 56, zb, zb + 120)])
    # murs du couloir avec une porte par chambre
    portes = [(x0 + w * (k + 0.5) - 40, x0 + w * (k + 0.5) + 40, zb, zb + 112) for k in range(nb)]
    mur_x(x0 + e, x1 - e, yc - 88, yc - 72, zb, z0 + h, T["mur_int"], portes)
    mur_x(x0 + e, x1 - e, yc + 72, yc + 88, zb, z0 + h, T["mur_int"], portes)
    # cloisons entre les chambres
    for k in range(1, nb):
        xx = x0 + w * k
        boite(xx - 8, y0 + e, zb, xx + 8, yc - 88, z0 + h, T["mur_int"])
        boite(xx - 8, yc + 88, zb, xx + 8, y1 - e, z0 + h, T["mur_int"])
    for k in range(nb):
        cxx = x0 + w * (k + 0.5)
        lampe(cxx, (y0 + yc - 88) / 2, z0 + h - 24, 120)
        lampe(cxx, (yc + 88 + y1) / 2, z0 + h - 24, 120)
        boite(cxx - 28, y0 + e + 8, zb, cxx + 28, y0 + e + 88, zb + 20, T["bureau"])     # lit
        boite(cxx - 28, y1 - e - 88, zb, cxx + 28, y1 - e - 8, zb + 20, T["bureau"])
    for k in range(0, nb, 2):
        lampe(x0 + w * (k + 0.5), yc, z0 + h - 24, 120)
    boite(x0, y0, z0 + h, x1, y1, z0 + h + 16, T["plafond"])
    toit(x0, y0, x1, y1, z0 + h + 16, int((y1 - y0) * 0.3), debord=48)
    zone(x0, y0, x1, y1, nom, couleur, 2)


def domaine(x0, y0, x1, y1, nom, cle, couleur, porte, maison_taille=(960, 640)):
    """domaine de clan : sol à sa couleur, mur d'enceinte avec un portail, maison principale + annexe, chemin"""
    e, hm = 32, 192
    boite(x0 + e, y0 + e, 0, x1 - e, y1 - e, 2, T[cle])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    g = 120
    if porte == "S":
        mur_x(x0, x1, y0, y0 + e, 0, hm, T["falaise"], [(cx - g, cx + g, 0, hm - 1)])
        mur_x(x0, x1, y1 - e, y1, 0, hm, T["falaise"])
    else:
        mur_x(x0, x1, y0, y0 + e, 0, hm, T["falaise"])
        mur_x(x0, x1, y1 - e, y1, 0, hm, T["falaise"], [(cx - g, cx + g, 0, hm - 1)])
    mur_y(y0 + e, y1 - e, x0, x0 + e, 0, hm, T["falaise"])
    mur_y(y0 + e, y1 - e, x1 - e, x1, 0, hm, T["falaise"])
    torii(cx, y0 + e / 2 if porte == "S" else y1 - e / 2, 0, largeur=g * 2 + 64, hauteur=288)
    mw, md = maison_taille
    # la maison au fond du domaine, la porte vers le portail
    if porte == "S":
        my1 = y1 - e - 160
        my0 = my1 - md
        boite(cx - 64, y0 + e, 2, cx + 64, my0, 4, T["chemin"])
        maison(cx - mw / 2, my0, cx + mw / 2, my1, 2, "Maison " + nom, couleur, porte="S")
    else:
        my0 = y0 + e + 160
        my1 = my0 + md
        boite(cx - 64, my1, 2, cx + 64, y1 - e, 4, T["chemin"])
        maison(cx - mw / 2, my0, cx + mw / 2, my1, 2, "Maison " + nom, couleur, porte="N")
    # annexe (dojo du clan) sur le côté
    ax0 = x0 + e + 128
    ay0 = (y0 + e + 128) if porte == "N" else (y1 - e - 128 - 400)
    if ax0 + 480 < cx - mw / 2 - 64:
        maison(ax0, ay0, ax0 + 480, ay0 + 400, 2, "Dojo " + nom, couleur, porte="E", cloison=False)
    zone(x0, y0, x1, y1, "Domaine " + nom, couleur, 1)




# ================================================================== AJOUTS (carte v3)
def prisme(points, z0, z1, mat, dessus=None, dessous=None):
    """solide vertical à base polygonale CONVEXE (points dans l'ordre, sens quelconque)"""
    n = len(points)
    cx = sum(p[0] for p in points) / n
    cy = sum(p[1] for p in points) / n
    faces = [((points[0][0], points[0][1], z1), (points[1][0], points[1][1], z1), (points[2][0], points[2][1], z1), dessus or mat),
             ((points[0][0], points[0][1], z0), (points[1][0], points[1][1], z0), (points[2][0], points[2][1], z0), dessous or mat)]
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        faces.append(((a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), mat))
    solide(faces, (cx, cy, (z0 + z1) / 2))


def bande(a, b, largeur, z0, z1, mat, dessus=None):
    """segment épais de a à b (chemin en diagonale, mur en biais)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1
    nx, ny = -dy / l * largeur / 2, dx / l * largeur / 2
    pts = [(round(a[0] + nx), round(a[1] + ny)), (round(b[0] + nx), round(b[1] + ny)),
           (round(b[0] - nx), round(b[1] - ny)), (round(a[0] - nx), round(a[1] - ny))]
    prisme(pts, z0, z1, mat, dessus)


def chemin_ligne(points, largeur=240, z=0, mat=None):
    """chemin pavé qui suit une ligne brisée (2 unités d'épaisseur), avec un rond à chaque coude"""
    mat = mat or T["chemin"]
    for a, b in zip(points, points[1:]):
        bande(a, b, largeur, z, z + 2, mat)
    for p in points[1:-1]:
        r = largeur / 2
        prisme([(round(p[0] + r * math.cos(k * math.pi / 4)), round(p[1] + r * math.sin(k * math.pi / 4))) for k in range(8)],
               z, z + 2, mat)


def prop(modele, x, y, z, lacet=0, echelle=None, solide_=6, couleur=None, ombres=True, fondu=None):
    """prop_static (décor figé, éclairé par vrad) ; lacet = rotation autour de la verticale (degrés)
    fondu = (début, fin) : le petit décor disparaît en douceur au loin (meilleures performances)"""
    cles = dict(model=modele, angles="0 %g 0" % lacet, solid=str(solide_), skin="0",
                disableshadows="0" if ombres else "1", fademindist=str(fondu[0]) if fondu else "-1",
                fademaxdist=str(fondu[1]) if fondu else "0", fadescale="1")
    if echelle:
        cles["modelscale"] = "%g" % echelle
    if couleur:
        cles["rendercolor"] = couleur
    entite("prop_static", (x, y, z), **cles)


def porte_pivotante(x0, y0, z0, x1, y1, z1, mat, charniere, nom="porte_secrete", angle=90, vitesse=60):
    """porte qui pivote (ex. la bibliothèque du bureau du directeur) : s'ouvre avec E, se referme seule"""
    _cible.append([])
    boite(x0, y0, z0, x1, y1, z1, mat)
    brosse = _cible.pop()
    lignes = ['\t"id" "%d"\n\t"classname" "func_door_rotating"\n' % nid()]
    cles = {"targetname": nom, "origin": "%g %g %g" % charniere, "distance": str(angle), "speed": str(vitesse),
            "spawnflags": "256", "wait": "6", "noise1": "doors/wood_move1.wav", "noise2": "doors/wood_stop1.wav",
            "lip": "0", "dmg": "0", "rendercolor": "255 255 255"}
    for k, v in cles.items():
        lignes.append('\t"%s" "%s"\n' % (k, v))
    entites.append("entity\n{\n%s%s\teditor\n\t{\n\t\t\"color\" \"220 30 220\"\n\t\t\"visgroupshown\" \"1\"\n"
                   "\t\t\"visgroupautoshown\" \"1\"\n\t}\n}\n" % ("".join(lignes), "".join(brosse)))


def colline(cx, cy, rx, ry, hauteur, mat, puissance=4, graine=1, zsol=0):
    """colline douce (un seul déplacement) centrée en (cx, cy) ; les bords restent au niveau du sol.
    Le sol plat doit être troué à cet endroit (voir dalle_trouee) ; la carte reste fermée par le socle dessous."""
    x0, y0, x1, y1 = round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)
    n = 2 ** puissance + 1
    rnd = random.Random(graine)
    bosses = [(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0.15, 0.35)) for _ in range(4)]
    lignes_d, lignes_n, lignes_o, lignes_a = [], [], [], []
    for r in range(n):
        v = r / (n - 1) * 2 - 1
        ds = []
        for c in range(n):
            u = c / (n - 1) * 2 - 1
            d = math.sqrt(u * u + v * v)
            h = (0.5 + 0.5 * math.cos(math.pi * min(1.0, d))) * hauteur        # colline arrondie (en cloche)
            for bu, bv, ba in bosses:
                e = math.hypot(u - bu, v - bv)
                h += (0.5 + 0.5 * math.cos(math.pi * min(1.0, e / 0.5))) * ba * 0.5 * hauteur * max(0.0, 1 - d)
            if r in (0, n - 1) or c in (0, n - 1):
                h = 0
            ds.append("%.1f" % h)
        lignes_d.append('\t\t\t\t"row%d" "%s"\n' % (r, " ".join(ds)))
        lignes_n.append('\t\t\t\t"row%d" "%s"\n' % (r, " ".join(["0 0 1"] * n)))
        lignes_o.append('\t\t\t\t"row%d" "%s"\n' % (r, " ".join(["0 0 0"] * n)))
        lignes_a.append('\t\t\t\t"row%d" "%s"\n' % (r, " ".join(["0"] * n)))
    tags = "".join('\t\t\t\t"row%d" "%s"\n' % (r, " ".join(["9"] * (2 * (n - 1)))) for r in range(n - 1))
    info = ('\t\t\tdispinfo\n\t\t\t{\n\t\t\t\t"power" "%d"\n\t\t\t\t"startposition" "[%g %g %g]"\n\t\t\t\t"flags" "0"\n'
            '\t\t\t\t"elevation" "0"\n\t\t\t\t"subdiv" "0"\n'
            '\t\t\t\tnormals\n\t\t\t\t{\n%s\t\t\t\t}\n\t\t\t\tdistances\n\t\t\t\t{\n%s\t\t\t\t}\n'
            '\t\t\t\toffsets\n\t\t\t\t{\n%s\t\t\t\t}\n\t\t\t\toffset_normals\n\t\t\t\t{\n%s\t\t\t\t}\n'
            '\t\t\t\talphas\n\t\t\t\t{\n%s\t\t\t\t}\n\t\t\t\ttriangle_tags\n\t\t\t\t{\n%s\t\t\t\t}\n'
            '\t\t\t\tallowed_verts\n\t\t\t\t{\n\t\t\t\t\t"10" "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1"\n\t\t\t\t}\n\t\t\t}\n'
            % (puissance, x0, y0, zsol, "".join(lignes_n), "".join(lignes_d), "".join(lignes_o), "".join(lignes_n), "".join(lignes_a), tags))
    c = ((x0 + x1) / 2, (y0 + y1) / 2, zsol - 8)
    solide([
        ((x0, y1, zsol), (x1, y1, zsol), (x1, y0, zsol), mat),
        ((x0, y0, zsol - 16), (x1, y0, zsol - 16), (x1, y1, zsol - 16), T["nodraw"]),
        ((x0, y1, zsol), (x0, y0, zsol), (x0, y0, zsol - 16), T["nodraw"]),
        ((x1, y1, zsol - 16), (x1, y0, zsol - 16), (x1, y0, zsol), T["nodraw"]),
        ((x1, y1, zsol), (x0, y1, zsol), (x0, y1, zsol - 16), T["nodraw"]),
        ((x1, y0, zsol - 16), (x0, y0, zsol - 16), (x0, y0, zsol), T["nodraw"]),
    ], c, disp=(0, info))
    return (x0, y0, x1, y1)


def ecrire(chemin, ciel="sky_day01_01"):
    monde = ('world\n{\n\t"id" "1"\n\t"mapversion" "1"\n\t"classname" "worldspawn"\n\t"skyname" "%s"\n'
             '\t"maxpropscreenwidth" "-1"\n\t"detailvbsp" "detail.vbsp"\n\t"detailmaterial" "detail/detailsprites"\n' % ciel
             + "".join(solides) + "}\n")
    vmf = ('versioninfo\n{\n\t"editorversion" "400"\n\t"editorbuild" "8000"\n\t"mapversion" "1"\n\t"formatversion" "100"\n'
           '\t"prefab" "0"\n}\nvisgroups\n{\n}\nviewsettings\n{\n\t"bSnapToGrid" "1"\n\t"bShowGrid" "1"\n\t"nGridSpacing" "64"\n}\n'
           + monde + "".join(entites) + 'cameras\n{\n\t"activecamera" "-1"\n}\ncordon\n{\n\t"mins" "(-1024 -1024 -1024)"\n'
           '\t"maxs" "(1024 1024 1024)"\n\t"active" "0"\n}\n')
    if DETAIL_SOLIDES:
        detail = 'entity\n{\n\t"id" "%d"\n\t"classname" "func_detail"\n%s}\n' % (nid(), "".join(DETAIL_SOLIDES))
        vmf = vmf.replace("cameras\n{", detail + "cameras\n{", 1)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(vmf)
    print("[carte] %d solides, %d entités -> %s" % (len(solides), len(entites), os.path.basename(chemin)))


def toit_croupe(x0, y0, x1, y1, z, h, mat=None, debord=64):
    """toit japonais à 4 pentes (croupes) : faîte le long du côté le plus long, pans triangulaires aux bouts"""
    mat = mat or T["toit"]
    x0, y0, x1, y1 = x0 - debord, y0 - debord, x1 + debord, y1 + debord
    if x1 - x0 >= y1 - y0:
        ym = (y0 + y1) / 2
        i = min((y1 - y0) / 2, (x1 - x0) / 2 - 24)
        r1, r2 = (x0 + i, ym, z + h), (x1 - i, ym, z + h)
        faces = [((x0, y0, z), (x1, y0, z), (x1, y1, z), mat),
                 ((x0, y0, z), (x1, y0, z), r2, mat),
                 ((x1, y1, z), (x0, y1, z), r1, mat),
                 ((x0, y1, z), (x0, y0, z), r1, mat),
                 ((x1, y0, z), (x1, y1, z), r2, mat)]
    else:
        xm = (x0 + x1) / 2
        i = min((x1 - x0) / 2, (y1 - y0) / 2 - 24)
        r1, r2 = (xm, y0 + i, z + h), (xm, y1 - i, z + h)
        faces = [((x0, y0, z), (x1, y0, z), (x1, y1, z), mat),
                 ((x0, y1, z), (x0, y0, z), r1, mat),
                 ((x1, y0, z), (x1, y1, z), r2, mat),
                 ((x0, y0, z), (x1, y0, z), r1, mat),
                 ((x1, y1, z), (x0, y1, z), r2, mat)]
    solide(faces, ((x0 + x1) / 2, (y0 + y1) / 2, z + h / 3))
    # bordure de l'avant-toit (planche sombre) : donne l'épaisseur des toits japonais
    for a in ((x0, y0, x1, y0 + 10), (x0, y1 - 10, x1, y1), (x0, y0, x0 + 10, y1), (x1 - 10, y0, x1, y1)):
        boite(a[0], a[1], z - 14, a[2], a[3], z, T.get("bois_sombre", mat))
    return r1, r2


# ================================================================== AJOUTS (qualité)
def brosse_entite(classe, x0, y0, z0, x1, y1, z1, mat, dessus=None, **cles):
    """entité de brosse (func_illusionary pour l'eau, trigger_teleport…) en forme de boîte"""
    _cible.append([])
    boite(x0, y0, z0, x1, y1, z1, mat, dessus)
    brosse = _cible.pop()
    lignes = ['\t"id" "%d"\n\t"classname" "%s"\n' % (nid(), classe)]
    for k, v in cles.items():
        lignes.append('\t"%s" "%s"\n' % (k, v))
    entites.append("entity\n{\n%s%s\teditor\n\t{\n\t\t\"color\" \"220 30 220\"\n\t\t\"visgroupshown\" \"1\"\n"
                   "\t\t\"visgroupautoshown\" \"1\"\n\t}\n}\n" % ("".join(lignes), "".join(brosse)))


def teleporteur(x0, y0, z0, x1, y1, z1, cible):
    """zone invisible qui téléporte les joueurs vers l'entité info_teleport_destination « cible »"""
    brosse_entite("trigger_teleport", x0, y0, z0, x1, y1, z1, "tools/toolstrigger", target=cible, spawnflags="1",
                  StartDisabled="0")


def arrivee(nom, x, y, z, lacet=0):
    entite("info_teleport_destination", (x, y, z), targetname=nom, angles="0 %g 0" % lacet)


# charpente automatique : sur les murs d'enduit, poteaux de bois sombre, plinthe et poutre haute des deux côtés,
# en évitant toutes les ouvertures (portes et fenêtres) — style des bâtiments japonais
HABILLAGE = {}       # {"enduits": set(matériaux), "bois": matériau}


def _segments_libres(a0, a1, z0, z1, ouvertures):
    """parties de [a0, a1] qui ne croisent aucune ouverture entre z0 et z1"""
    coupes = [(a0, a1)]
    for a, b, za, zb in ouvertures:
        if zb <= z0 or za >= z1:
            continue
        nouv = []
        for c0, c1 in coupes:
            if b <= c0 or a >= c1:
                nouv.append((c0, c1))
            else:
                if a > c0:
                    nouv.append((c0, a))
                if b < c1:
                    nouv.append((b, c1))
        coupes = nouv
    return [(c0, c1) for c0, c1 in coupes if c1 - c0 > 8]


def _habiller(a0, a1, e0, e1, z0, z1, mat, ouvertures, poser):
    if not HABILLAGE or mat not in HABILLAGE["enduits"] or e1 - e0 > 48 or z1 - z0 < 140:
        return
    bois = HABILLAGE["bois"]
    for s in (-1, 1):                               # les deux faces du mur
        f0, f1 = (e0 - 5, e0) if s < 0 else (e1, e1 + 5)
        for c0, c1 in _segments_libres(a0, a1, z0, z0 + 22, ouvertures):
            poser(c0, c1, f0, f1, z0, z0 + 22, bois)                              # plinthe
        for c0, c1 in _segments_libres(a0, a1, z1 - 26, z1 - 8, ouvertures):
            poser(c0, c1, f0, f1, z1 - 26, z1 - 8, bois)                          # poutre haute
        n = max(1, int((a1 - a0) // 340))
        for k in range(n + 1):
            c = a0 + (a1 - a0) * k / n
            c = min(max(c, a0 + 6), a1 - 6)
            if _segments_libres(c - 7, c + 7, z0, z1, ouvertures) == [(c - 7, c + 7)]:
                poser(c - 7, c + 7, f0 - (2 if s < 0 else 0), f1 + (2 if s > 0 else 0), z0, z1, bois)   # poteau


_mur_x_base, _mur_y_base = mur_x, mur_y


def mur_x(x0, x1, y0, y1, z0, z1, mat, ouvertures=()):
    _mur_x_base(x0, x1, y0, y1, z0, z1, mat, ouvertures)
    _habiller(x0, x1, y0, y1, z0, z1, mat, list(ouvertures), lambda a, b, e0, e1, za, zb, m: boite(a, e0, za, b, e1, zb, m))


def mur_y(y0, y1, x0, x1, z0, z1, mat, ouvertures=()):
    _mur_y_base(y0, y1, x0, x1, z0, z1, mat, ouvertures)
    _habiller(y0, y1, x0, x1, z0, z1, mat, list(ouvertures), lambda a, b, e0, e1, za, zb, m: boite(e0, a, za, e1, b, zb, m))

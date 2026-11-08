"""
PORT (partie de Shibuya) — version COMPACTE (environ 40 % plus petite que creer_port_detail.py), pensée pour GMod.
  - 4 hangars au sud (entrepôt, garage, colis, planque), route est-ouest, parc à conteneurs, zone de stock à l'ouest,
    quai + grue (échelle, cabine ouverte) + bureau du quai ouvert au nord, tour au sud-est ;
  - une seule entrée / sortie : le tunnel voûté au sud (vide au bout : la suite sera mappée) ;
  - enceinte de bâtiments plus hauts que le plafond de la carte : même en volant on ne voit jamais le vide ;
  - murs invisibles : bord de l'eau, plafond, bout du tunnel (objets CLIP_*) ; échelle de la grue (objet LADDER_*).
  - vrais modèles : NEOTOKYO° (camions japonais, conteneurs, palettes, échelle, rampes), HL2, CS:S.
Lancer : blender.exe -b --factory-startup --python creer_port_compact.py      -> port.blend
Unités : mètres. X = est, Y = nord, Z = haut. Eau au nord.
"""
import bpy, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from port_outils import *                                              # noqa: F401,F403
import port_outils as O

# ---------------------------------------------------------------- dimensions
ZPLAF = 32.0                                     # plafond invisible de la carte (les bâtiments de l'enceinte sont plus hauts)
H = dict(l=38.0, p=15.0, h=8.0, mur=0.25, porte_l=6.0, porte_h=4.8)
HANGARS_X = [2.0, 50.0]
HY0 = 6.0                                        # mur sud des hangars
ROUTE_Y, ROUTE_L = 34.0, 6.0                     # route est-ouest
TX0, TX1 = 101.0, 108.0                          # route du tunnel (seule entrée / sortie)
A0, A1 = 99.5, 109.5                             # voûte du tunnel
QR0, QR1 = 52.0, 58.0                            # route qui descend vers le quai
QUAI_Y, QUAI_HAUT = 90.0, 2.0
XMIN, XMAX = -2.0, 122.0                         # intérieur de l'enceinte

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"
preparer_materiaux()
mat_uni("clip", (0.9, 0.1, 0.9), 0.5, alpha=0.15)
mat_uni("echelle_invisible", (0.1, 0.9, 0.9), 0.5, alpha=0.15)
rnd = O.rnd


def sol(x, y):
    """hauteur du sol à cet endroit (pour poser les objets sans qu'ils flottent ni s'enfoncent)"""
    for n, hx in enumerate(HANGARS_X):
        if hx <= x <= hx + H["l"] and HY0 <= y <= HY0 + H["p"]:
            return 0.12
    if y >= QUAI_Y - 14:
        return 0.08
    if ROUTE_Y <= y <= ROUTE_Y + ROUTE_L or (TX0 <= x <= TX1 and y <= ROUTE_Y) or (QR0 <= x <= QR1 and y >= ROUTE_Y):
        return 0.06
    return 0.0


def pose(nom, coll, chemin, x, y, rot=0.0, z=None, ry=0.0):
    """pose un modèle du jeu SUR le sol (léger enfoncement de 1 cm)"""
    return modele(nom, coll, chemin, x, y, (sol(x, y) if z is None else z) - 0.01, rot, ry)


def clip(nom, x0, y0, z0, x1, y1, z1):
    o = boite("CLIP_" + nom, "PORT/MURS_INVISIBLES", x0, y0, z0, x1, y1, z1, "clip")
    o.hide_render = True
    o.display_type = "WIRE"
    return o


def escalier_ouvert(nom, c, x0, x1, y0, z0, z1, axe="y", sens=1, rampe=True):
    """escalier métallique propre : marches fines + 2 limons inclinés + rampe NEOTOKYO ; monte le long de Y (ou X)"""
    n = max(1, round((z1 - z0) / 0.18))
    haut = (z1 - z0) / n
    pas = 0.28
    for k in range(n):
        a = y0 + sens * k * pas
        z = z0 + (k + 1) * haut
        if axe == "y":
            boite("%s_Marche_%02d" % (nom, k), c, x0, a, z - 0.05, x1, a + sens * pas, z, "acier_gris")
        else:
            boite("%s_Marche_%02d" % (nom, k), c, a, x0, z - 0.05, a + sens * pas, x1, z, "acier_gris")
    fin = y0 + sens * n * pas
    for cote, xx in (("G", x0), ("D", x1)):
        if axe == "y":
            poutre("%s_Limon_%s" % (nom, cote), c, (xx, y0, z0), (xx, fin, z1), 0.16, "acier_gris")
        else:
            poutre("%s_Limon_%s" % (nom, cote), c, (y0, xx, z0), (fin, xx, z1), 0.16, "acier_gris")
    if rampe:
        # rampe du jeu (NEOTOKYO straight_stair02 : 5,5 m de long, 3,9 m de haut) ; sinon garde-corps maison
        m = (y0 + fin) / 2
        ok = False
        if abs(z1 - z0 - 3.86) < 0.8:
            if axe == "y":
                ok = modele(nom + "_Rampe", c, "models/nt/props_warehouse/straight_stair02", x1, m, z0 + 0.05, 0 if sens > 0 else math.pi)
            else:
                ok = modele(nom + "_Rampe", c, "models/nt/props_warehouse/straight_stair02", m, x1, z0 + 0.05, -math.pi / 2 if sens > 0 else math.pi / 2)
        if not ok:
            for xx in (x0, x1):
                if axe == "y":
                    poutre("%s_Main_Courante_%d" % (nom, int(xx * 10)), c, (xx, y0, z0 + 1.0), (xx, fin, z1 + 1.0), 0.05, "acier_jaune")
                else:
                    poutre("%s_Main_Courante_%d" % (nom, int(xx * 10)), c, (y0, xx, z0 + 1.0), (fin, xx, z1 + 1.0), 0.05, "acier_jaune")
    return fin


# ================================================================== SOL, ROUTES, QUAI, EAU
t, r_ = "PORT/TERRAIN", "PORT/ROUTES"
boite("PORT_Terrain", t, XMIN, -2, -1, XMAX, QUAI_Y, 0, "beton_sol")
boite("PORT_Sol_Derriere_Enceinte", t, -14, -27, -1, 136, -14, 0, "terre")
boite("PORT_Sol_Stock", t, 0, 41, 0, 14, 68, 0.02, "terre")
boite("PORT_Sol_Parc", t, 15, 41, 0, 120, 68, 0.02, "beton_sol2")
boite("PORT_Route_EstOuest", r_, XMIN, ROUTE_Y, 0, XMAX, ROUTE_Y + ROUTE_L, 0.06, "asphalte")
boite("PORT_Route_Tunnel", r_, TX0, -2, 0, TX1, ROUTE_Y, 0.06, "asphalte")
boite("PORT_Route_Quai", r_, QR0, ROUTE_Y + ROUTE_L, 0, QR1, QUAI_Y - 14, 0.06, "asphalte")
for i, x in enumerate(range(0, 122, 6)):
    boite("PORT_Marquage_Axe_%02d" % i, r_, x, ROUTE_Y + 2.9, 0.06, x + 3, ROUTE_Y + 3.1, 0.07, "marquage")
for i, x in enumerate(range(4, 98, 3)):                              # places des camions devant les hangars
    if not any(abs(x - p_) < 4 for p_ in (16, 32, 64, 80)):
        boite("PORT_Marquage_Place_%02d" % i, r_, x, 24, 0, x + 0.1, 31, 0.02, "blanc_sol")
q = "PORT/QUAIS"
boite("PORT_Quai_Principal", q, XMIN, QUAI_Y - 14, 0, XMAX, QUAI_Y, 0.08, "beton_sol")
boite("PORT_Quai_Mur", q, XMIN, QUAI_Y - 1.0, -QUAI_HAUT - 4, XMAX, QUAI_Y, 0, "beton_mur")
boite("PORT_Quai_Bordure", q, XMIN, QUAI_Y - 0.4, 0.08, XMAX, QUAI_Y, 0.25, "rayures")
boite("PORT_Bande_Securite", q, XMIN, QUAI_Y - 14.4, 0, XMAX, QUAI_Y - 14, 0.03, "rayures")
boite("PORT_Eau", q, -14, QUAI_Y, -QUAI_HAUT - 4, 136, QUAI_Y + 130, -QUAI_HAUT, "eau")
for i, x in enumerate(range(3, 121, 8)):
    cylindre("PORT_Bollard_%02d" % i, q, x, QUAI_Y - 0.8, 0.08, 0.6, 0.22, "acier_jaune")
    cylindre("PORT_Bollard_Tete_%02d" % i, q, x, QUAI_Y - 0.8, 0.6, 0.72, 0.3, "acier_jaune")
for i, x in enumerate(range(6, 121, 7)):
    boite("PORT_Defense_%02d" % i, q, x - 0.7, QUAI_Y, -QUAI_HAUT - 0.8, x + 0.7, QUAI_Y + 0.5, -0.25, "caoutchouc")
clip("Bord_De_L_Eau", XMIN - 12, QUAI_Y - 0.2, 0, XMAX + 14, QUAI_Y + 0.4, ZPLAF + 1)

# ================================================================== 2 GRANDS HANGARS (38 x 15 x 8 m), deux espaces chacun
# hangar 1 : entrepôt | colis      hangar 2 : garage | planque      (cloison avec porte entre les deux espaces)
HANGARS = [(2.0, ("entrepot", "colis"), "tole_grise"), (50.0, ("garage", "planque"), "tole_bleue")]
for n, (hx, THEMES, murs) in enumerate(HANGARS, 1):
    nom = "PORT_Hangar_%02d" % n
    c = "PORT/HANGARS/" + nom
    x0, y0, x1, y1 = hx, HY0, hx + H["l"], HY0 + H["p"]
    e, hh = H["mur"], H["h"]
    PORTES = [hx + 14.0, hx + 30.0]                                  # un rideau métallique par espace
    boite(nom + "_Dalle", c, x0, y0, 0, x1, y1, 0.12, "beton_sol")
    bords = [x0] + [v for pm_ in PORTES for v in (pm_ - H["porte_l"] / 2, pm_ + H["porte_l"] / 2)] + [x1]
    for k in range(0, len(bords), 2):
        boite("%s_Socle_N_%d" % (nom, k), c, bords[k], y1 - e - 0.05, 0, bords[k + 1], y1 + 0.05, 0.8, "beton_mur")
        boite("%s_Facade_%d" % (nom, k), c, bords[k], y1 - e, 0.8, bords[k + 1], y1, hh, murs)
    boite(nom + "_Socle_S", c, x0 - 0.05, y0 - 0.05, 0, x1 + 0.05, y0 + e + 0.05, 0.8, "beton_mur")
    boite(nom + "_Socle_O", c, x0 - 0.05, y0, 0, x0 + e + 0.05, y1, 0.8, "beton_mur")
    boite(nom + "_Socle_E", c, x1 - e - 0.05, y0, 0, x1 + 0.05, y1, 0.8, "beton_mur")
    boite(nom + "_Mur_Sud", c, x0, y0, 0.8, x1, y0 + e, hh, murs)
    boite(nom + "_Mur_Ouest", c, x0, y0, 0.8, x0 + e, y1, hh, murs)
    boite(nom + "_Mur_Est", c, x1 - e, y0, 0.8, x1, y1, hh, murs)
    for s_, xx in (("O", x0), ("E", x1 - e)):
        ym = (y0 + y1) / 2
        v = [(0, y0, hh), (0, y1, hh), (0, ym, hh + 2.2), (e, y0, hh), (e, y1, hh), (e, ym, hh + 2.2)]
        objet(nom + "_Pignon_" + s_, c, v, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], murs, (xx, 0, 0))
    for k, pm_ in enumerate(PORTES):
        boite("%s_Facade_Haut_%d" % (nom, k), c, pm_ - H["porte_l"] / 2, y1 - e, H["porte_h"], pm_ + H["porte_l"] / 2, y1, hh, murs)
        boite("%s_Rideau_Metallique_%d" % (nom, k), c, pm_ - H["porte_l"] / 2, y1 - 0.12, H["porte_h"] - 1.0, pm_ + H["porte_l"] / 2, y1 + 0.04, H["porte_h"], "rideau")
        boite("%s_Coffre_Rideau_%d" % (nom, k), c, pm_ - H["porte_l"] / 2 - 0.15, y1, H["porte_h"], pm_ + H["porte_l"] / 2 + 0.15, y1 + 0.45, H["porte_h"] + 0.45, "acier_gris")
        for s_ in (-1, 1):
            boite("%s_Montant_Porte_%d_%d" % (nom, k, s_), c, pm_ + s_ * H["porte_l"] / 2 - 0.12, y1 - 0.08, 0, pm_ + s_ * H["porte_l"] / 2 + 0.12, y1 + 0.2, H["porte_h"], "acier_jaune")
    for k in range(9):
        xx = x0 + k * H["l"] / 8
        boite("%s_Poteau_S_%d" % (nom, k), c, xx - 0.12, y0 - 0.25, 0, xx + 0.12, y0, hh, "acier_gris")
    toit(nom + "_Toit", c, x0 - 0.6, y0 - 0.6, x1 + 0.6, y1 + 0.6, hh, 2.2, "tole_toit")
    for s_, yy in (("S", y0 - 0.85), ("N", y1 + 0.6)):
        boite(nom + "_Gouttiere_" + s_, c, x0 - 0.6, yy, hh - 0.3, x1 + 0.6, yy + 0.25, hh - 0.05, "acier_gris")
    for k in range(3):
        xx = x0 + 5 + k * 11
        poutre("%s_Lanterneau_%d" % (nom, k), c, (xx, y0 + 2.6, hh + 0.8), (xx + 5, y0 + 2.6, hh + 0.8), 0.7, "vitre")
    ys0, ys1 = y0 - 2.15, y0 - 1.0
    xa = escalier_ouvert(nom + "_Esc_Toit_A", c, ys0, ys1, x0 + 1.0, 0, 3.9, axe="x")
    boite(nom + "_Palier_Toit_1", c, xa, ys0, 3.75, xa + 1.2, ys1, 3.9, "acier_gris")
    xb = escalier_ouvert(nom + "_Esc_Toit_B", c, ys0, ys1, xa + 1.2, 3.9, hh, axe="x")
    boite(nom + "_Palier_Toit_2", c, xb, ys0, hh - 0.15, xb + 1.6, y0 - 0.5, hh, "acier_gris")
    for k, xx in enumerate((xa, xa + 1.2, xb + 1.6)):
        boite("%s_Esc_Poteau_%d" % (nom, k), c, xx - 0.07, ys0 + 0.05, 0, xx + 0.07, ys0 + 0.19, 3.9 if k < 2 else hh, "acier_gris")
    for k in range(1, 8):
        xx = x0 + k * H["l"] / 8
        poutre("%s_Ferme_Entrait_%d" % (nom, k), c, (xx, y0, hh - 0.3), (xx, y1, hh - 0.3), 0.2, "acier_gris")
        poutre("%s_Ferme_S_%d" % (nom, k), c, (xx, y0, hh - 0.15), (xx, (y0 + y1) / 2, hh + 2.0), 0.18, "acier_gris")
        poutre("%s_Ferme_N_%d" % (nom, k), c, (xx, y1, hh - 0.15), (xx, (y0 + y1) / 2, hh + 2.0), 0.18, "acier_gris")
        if not modele("%s_Lampe_%d" % (nom, k), c, "models/props_c17/light_industrialbell01_on", xx, (y0 + y1) / 2, hh - 1.3):
            boite("%s_Lampe_%d" % (nom, k), c, xx - 0.4, (y0 + y1) / 2 - 0.15, hh - 1.0, xx + 0.4, (y0 + y1) / 2 + 0.15, hh - 0.85, "lampe")

    # mezzanine (côté ouest) posée sur des poteaux, escalier propre, palier, garde-corps ouvert au palier
    MZ, MX = 3.6, x0 + 6.0
    boite(nom + "_Mezzanine", c, x0 + e, y0 + e, MZ - 0.2, MX, y1 - e, MZ, "acier_gris")
    boite(nom + "_Mezz_Poutre", c, MX - 0.3, y0 + e, MZ - 0.5, MX, y1 - e, MZ - 0.2, "acier_gris")
    for k in range(5):
        yy = y0 + 0.6 + k * (H["p"] - 1.2) / 4
        boite("%s_Mezz_Poteau_%d" % (nom, k), c, MX - 0.28, yy - 0.12, 0.12, MX - 0.04, yy + 0.12, MZ - 0.5, "acier_bleu")
    yfin = escalier_ouvert(nom + "_Esc_Mezz", c, MX + 0.05, MX + 1.25, y0 + 2.0, 0.12, MZ)
    boite(nom + "_Palier_Mezz", c, MX - 0.05, yfin, MZ - 0.15, MX + 1.25, yfin + 1.3, MZ, "acier_gris")
    garde_corps(nom + "_GC_Mezz_A", c, (MX, y0 + 0.5), (MX, y0 + 1.9), MZ)
    garde_corps(nom + "_GC_Mezz_B", c, (MX, yfin + 1.35), (MX, y1 - 0.5), MZ)
    garde_corps(nom + "_GC_Palier", c, (MX + 1.25, yfin), (MX + 1.25, yfin + 1.3), MZ)
    # bureau vitré sous la mezzanine + établi
    bx0, by0, bx1, by1 = x0 + e, y0 + e, x0 + 5.2, y0 + 4.5
    boite(nom + "_Bureau_Mur_N", c, bx0, by1 - 0.1, 0.12, bx1, by1, 0.9, "cabine")
    boite(nom + "_Bureau_Vitre_N", c, bx0, by1 - 0.07, 0.9, bx1 - 1.0, by1 - 0.03, 2.4, "vitre")
    boite(nom + "_Bureau_Mur_E", c, bx1 - 0.1, by0, 0.12, bx1, by1, 2.6, "cabine")
    boite(nom + "_Bureau_Plafond", c, bx0, by0, 2.6, bx1, by1, 2.7, "cabine")
    pose(nom + "_Bureau_Table", c, "models/nt/props_office/desk_military", bx0 + 0.9, by0 + 1.9, 0)
    pose(nom + "_Bureau_Chaise", c, "models/nt/props_office/officechair02", bx0 + 1.9, by0 + 1.9, math.pi / 2 + rnd.uniform(-0.3, 0.3))
    pose(nom + "_Bureau_Classeur", c, "models/nt/props_office/filecabinet_three", bx1 - 0.45, by0 + 1.3, 0)
    pose(nom + "_Bureau_Archives", c, "models/nt/props_office/fileboxstack", bx0 + 3.2, by1 - 0.85, 0)
    pose(nom + "_Bureau_Fontaine", c, "models/nt/props_office/water_cooler", bx1 - 0.5, by1 - 0.55, math.pi)
    pose(nom + "_Bureau_Poubelle", c, "models/nt/props_office/trashbin1", bx0 + 0.4, by1 - 0.5, 0)
    modele(nom + "_Bureau_Tableau", c, "models/nt/props_office/painting_one", bx0 + 0.04, by0 + 3.4, 1.0, 0)
    lumiere(nom + "_Bureau_Lumiere", c, ((bx0 + bx1) / 2, (by0 + by1) / 2, 2.4), 40, (1.0, 0.95, 0.85))
    nom_hangar = nom
    for zi, THEME in enumerate(THEMES):
        x0, x1 = hx + 16.0 * zi, hx + 16.0 * zi + 22.0              # chaque espace : 22 m de large (le 2e commence après la cloison)
        pm = PORTES[zi]
        nom = nom_hangar + "_" + THEME.capitalize()
        for k in range(2):
            lumiere("%s_Lumiere_%d" % (nom, k), c, (x0 + 9 + k * 8, (y0 + y1) / 2, hh - 1.5), 300 if THEME == "planque" else 700,
                    (1.0, 0.62, 0.32) if THEME == "planque" else (1.0, 0.86, 0.68), 1.0)
        if THEME == "entrepot":
            rayonnage(nom + "_Rayon_Sud", c, x0 + 8, y0 + 0.4, x1 - 0.5, y0 + 1.5, 3, 1.7)
            rayonnage(nom + "_Rayon_Est", c, x1 - 1.5, y0 + 3.5, x1 - 0.4, y1 - 3.5, 3, 1.7)
            for i in range(3):
                for j in range(3):
                    pose("%s_Pal_%d_%d" % (nom, i, j), c, rnd.choice(("models/nt/props_warehouse/boxpallet", "models/nt/props_warehouse/wrapped_product",
                                                                       "models/props/cs_assault/moneypallet")), x0 + 14.5 + i * 1.7, y0 + 4 + j * 1.7, rnd.choice((0, 1.57)))
            pose(nom + "_Chariot_Menage", c, "models/nt/props_office/janitor_cart", x1 - 2.2, y1 - 1.3, math.pi / 2)
            pose(nom + "_Seau", c, "models/nt/props_office/mop_bucket", x1 - 3.4, y1 - 1.0, 0)
            pose(nom + "_Panneau_Sol", c, "models/nt/props_office/folding_sign", pm + 3.6, y1 - 1.4, 0.4)
            pose(nom + "_Archives", c, "models/nt/props_office/fileboxstack", x0 + 9.5, y0 + 10.5, 0.1)
        elif THEME == "garage":
            pose(nom + "_Camion_Reparation", c, "models/nt/props_vehicles/isuzutruck2", x0 + 15, y0 + 7.5, math.pi)
            modele(nom + "_Pont_Roulant", c, "models/nt/props_warehouse/crane_hoist", x0 + 15, (y0 + y1) / 2, hh - 5.2)
            for k in range(4):
                for j in range(rnd.randint(2, 4)):
                    if not pose("%s_Pneu_%d_%d" % (nom, k, j), c, "models/props_vehicles/tire001b_truck", x0 + 8.5 + k * 1.3, y0 + 1.1, 0, 0.12 + j * 0.34, math.pi / 2):
                        cylindre("%s_Pneu_%d_%d" % (nom, k, j), c, x0 + 8.5 + k * 1.3, y0 + 1.1, 0.12 + j * 0.3, 0.42 + j * 0.3, 0.5, "caoutchouc")
            for k in range(2):
                pose("%s_Etagere_%d" % (nom, k), c, "models/nt/props_warehouse/shelf1", x1 - 0.9, y0 + 3 + k * 3.5, 0)
            boite(nom + "_Etabli", c, x0 + 14, y0 + 0.4, 0.9, x0 + 19, y0 + 1.2, 0.98, "bois")
            for xx in (x0 + 14.1, x0 + 18.8):
                boite("%s_Etabli_Pied_%d" % (nom, int(xx * 10)), c, xx, y0 + 0.45, 0.12, xx + 0.1, y0 + 1.15, 0.9, "acier_gris")
            pose(nom + "_Casiers", c, "models/nt/props_office/lockers", x1 - 0.45, y0 + 11.3, math.pi / 2)
            pose(nom + "_Combinaisons", c, "models/nt/props_office/jumpsuit_rack", x0 + 15.5, y1 - 1.0, 0)
            pose(nom + "_Extincteur", c, "models/nt/props_office/fireext", pm + 3.4, y1 - 0.6, 0)
            boite(nom + "_Servante", c, x0 + 19.5, y0 + 0.5, 0.12, x0 + 20.3, y0 + 1.1, 1.1, "acier_rouge")
        elif THEME == "colis":
            rayonnage(nom + "_Rayon_Sud", c, x0 + 8, y0 + 0.4, x1 - 0.5, y0 + 1.5, 3, 1.7)
            pose(nom + "_Conteneur_Decharge", c, "models/nt/props_warehouse/container_scaled", x1 - 2.2, y0 + 8.0, math.pi / 2)
            boite(nom + "_Tapis_Roulant", c, x0 + 8.5, y0 + 6.5, 0.8, x0 + 18, y0 + 7.3, 0.92, "caoutchouc")
            for k in range(6):
                boite("%s_Tapis_Pied_%d" % (nom, k), c, x0 + 8.7 + k * 1.8, y0 + 6.6, 0.12, x0 + 8.85 + k * 1.8, y0 + 7.2, 0.8, "acier_gris")
                if rnd.random() < 0.6:
                    boite("%s_Colis_Tapis_%d" % (nom, k), c, x0 + 9 + k * 1.5, y0 + 6.6, 0.92, x0 + 9.5 + k * 1.5, y0 + 7.2, 1.3, "carton")
            for k in range(24):
                cx_, cy_ = x0 + 15 + rnd.uniform(0, 2.5), y0 + 8 + rnd.uniform(0, 2.5)
                t_ = rnd.uniform(0.35, 0.7)
                boite("%s_Colis_%d" % (nom, k), c, cx_, cy_, 0.12, cx_ + t_, cy_ + t_, 0.12 + t_ * rnd.uniform(0.6, 1.0), "carton")
            pose(nom + "_Chariot", c, "models/nt/props_vehicles/forkliftdown", x0 + 12, y0 + 11.5, 0)
            pose(nom + "_Bagagerie", c, "models/nt/props_office/rack_luggage", x0 + 8.5, y0 + 12.5, 0)
            pose(nom + "_Archives", c, "models/nt/props_office/fileboxstack", x0 + 10.5, y0 + 9.5, 0.2)
            pose(nom + "_Panneau_Sol", c, "models/nt/props_office/folding_sign", pm + 3.6, y1 - 1.4, -0.4)
            for k in range(3):
                modele("%s_Valise_%d" % (nom, k), c, "models/nt/props_office/luggage_suitcase", x0 + 10 + k * 2.5, y0 + 6.9, 0.92, math.pi / 2)
        else:                                                           # planque : le repaire
            cx_, cy_ = x0 + 14, y0 + 7.5
            boite(nom + "_Tapis", c, cx_ - 4, cy_ - 3.2, 0.12, cx_ + 4, cy_ + 3.2, 0.14, "tapis")
            pose(nom + "_Canape_O", c, "models/nt/props_office/couch01", cx_ - 3.0, cy_, 0, 0.14)
            pose(nom + "_Canape_E", c, "models/nt/props_office/couch01", cx_ + 3.0, cy_, math.pi, 0.14)
            pose(nom + "_Canape_S", c, "models/nt/props_office/couch01", cx_, cy_ - 2.4, math.pi / 2, 0.14)
            boite(nom + "_Table_Basse", c, cx_ - 0.9, cy_ - 0.5, 0.42, cx_ + 0.9, cy_ + 0.5, 0.48, "bois")
            for xx, yy in ((cx_ - 0.85, cy_ - 0.45), (cx_ + 0.75, cy_ - 0.45), (cx_ - 0.85, cy_ + 0.35), (cx_ + 0.75, cy_ + 0.35)):
                boite("%s_Table_Basse_Pied_%d_%d" % (nom, int(xx * 10), int(yy * 10)), c, xx, yy, 0.14, xx + 0.1, yy + 0.1, 0.42, "acier_gris")
            modele(nom + "_Cendrier", c, "models/nt/props_office/ashtray3", cx_ + 0.3, cy_, 0.48, 0)
            modele(nom + "_Ventilateur", c, "models/nt/props_office/ceiling_rotate_fan_01", cx_, cy_, hh - 1.6, 0)
            # bureau du boss au fond, armure de samouraï, grande bannière
            pose(nom + "_Bureau_Boss", c, "models/nt/props_office/desk_military", x1 - 3.2, y1 - 3.0, math.pi / 2)
            pose(nom + "_Fauteuil_Boss", c, "models/nt/props_office/officechair", x1 - 3.2, y1 - 1.8, math.pi + rnd.uniform(-0.2, 0.2))
            pose(nom + "_Chaise_Invite_1", c, "models/nt/props_office/officechair02", x1 - 3.8, y1 - 4.3, 0.2)
            pose(nom + "_Chaise_Invite_2", c, "models/nt/props_office/officechair02", x1 - 2.6, y1 - 4.3, -0.2)
            pose(nom + "_Armure_Socle", c, "models/nt/props_office/samurai_displaybase", x1 - 0.7, y1 - 6.0, 0)
            modele(nom + "_Armure", c, "models/nt/props_office/samurai_armor", x1 - 0.7, y1 - 6.0, 0.31, math.pi)
            modele(nom + "_Tableau_2", c, "models/nt/props_office/painting_two", x1 - e - 0.04, y0 + 7.5, 1.6, math.pi)
            modele(nom + "_Tableau_1", c, "models/nt/props_office/painting_three", x1 - e - 0.04, y1 - 8.5, 1.4, math.pi)
            # coin cuisine contre le mur sud, casiers, distributeur, paravents
            pose(nom + "_Casiers", c, "models/nt/props_office/lockers", x0 + 12.5, y0 + e + 0.3, 0)
            pose(nom + "_Comptoir", c, "models/nt/props_office/cabinet_integrated_counter", x0 + 17.2, y0 + 2.0, math.pi / 2)
            modele(nom + "_Micro_Ondes", c, "models/nt/props_office/microwave", x0 + 16.6, y0 + 2.0, 1.13, 0)
            pose(nom + "_Fontaine", c, "models/nt/props_office/water_cooler", x0 + 19.4, y0 + 0.7, 0)
            pose(nom + "_Distributeur", c, "models/nt/props_office/vend_train", x0 + 20.6, y0 + 0.6, math.pi / 2)
            pose(nom + "_Paravent_1", c, "models/nt/props_office/shoji1", cx_ + 5.6, cy_ + 2.5, math.pi / 2)
            pose(nom + "_Paravent_2", c, "models/nt/props_office/shoji1", cx_ + 5.6, cy_ - 1.5, math.pi / 2)
            pose(nom + "_Poubelle", c, "models/nt/props_office/trashbin1", cx_ - 4.6, cy_ + 3.3, 0)
            pose(nom + "_Presentoir", c, "models/nt/props_office/magazine_rack", x0 + 6.8, y1 - 2.5, 0)
            cylindre(nom + "_Brasero", c, x0 + 9, y1 - 2.0, 0.12, 1.0, 0.3, "acier_rouge")
            boite(nom + "_Brasero_Feu", c, x0 + 8.8, y1 - 2.2, 1.0, x0 + 9.2, y1 - 1.8, 1.12, "sodium")
            lumiere(nom + "_Brasero_Lumiere", c, (x0 + 9, y1 - 2.0, 1.6), 120, (1.0, 0.45, 0.15), 0.4)
            lumiere(nom + "_Salon_Lumiere", c, (cx_, cy_, 2.6), 110, (1.0, 0.78, 0.55), 0.3)
            lumiere(nom + "_Boss_Lumiere", c, (x1 - 3.2, y1 - 3.0, 2.4), 70, (1.0, 0.85, 0.6), 0.3)
            for k in range(5):
                xx, yy = x0 + 19 + rnd.uniform(0, 1.5), y0 + 9 + k * 1.1
                for j in range(rnd.randint(1, 2)):
                    caisse("%s_Caisse_%d_%d" % (nom, k, j), c, xx, yy, 0.12 + j * 1.02, rnd.uniform(-0.2, 0.2))
    x0, x1, pm, nom = hx, hx + H["l"], PORTES[0], nom_hangar
    # stock sur la mezzanine
    for k in range(6):
        if rnd.random() < 0.8:
            pose("%s_Mezz_Pal_%d" % (nom, k), c, rnd.choice(("models/nt/props_warehouse/boxpallet", "models/nt/props_warehouse/sackstack",
                                                             "models/nt/props_warehouse/wrapped_product")), x0 + 1.3 + (k % 2) * 2.4, y0 + 5.5 + (k // 2) * 2.6, 0, MZ)
    for k in range(4):
        fut("%s_Fut_%d" % (nom, k), c, pm - 4.5 - (k % 2) * 0.7, y1 - 1.2 - (k // 2) * 0.7, 0.11)

# ================================================================== TOUR DE BUREAUX (sud-est, à côté du tunnel)
b = "PORT/BATIMENTS"
TX = 111.0
boite("PORT_Tour_Socle", b, TX - 0.4, 5.6, 0, TX + 10.4, 18.4, 3.5, "beton_mur")
boite("PORT_Tour_Facades", b, TX, 6, 3.5, TX + 10, 18, 30, "facade")
boite("PORT_Tour_Auvent", b, TX + 1.5, 18, 2.8, TX + 8.5, 20, 3.0, "acier_gris")
boite("PORT_Tour_Entree_Vitree", b, TX + 3, 18.0, 0.06, TX + 7, 18.1, 2.7, "vitre")
boite("PORT_Tour_Parapet", b, TX - 0.1, 5.9, 30, TX + 10.1, 18.1, 30.9, "beton_mur")
boite("PORT_Poste_Garde", b, TX0 - 3.6, 1, 0, TX0 - 0.6, 5, 2.8, "beton_mur")
boite("PORT_Poste_Garde_Vitre", b, TX0 - 0.62, 1.6, 1.1, TX0 - 0.57, 4.4, 2.3, "vitre")
boite("PORT_Poste_Garde_Toit", b, TX0 - 3.8, 0.8, 2.8, TX0 - 0.4, 5.2, 3.0, "acier_gris")

# ================================================================== PARC À CONTENEURS (vrai conteneur NEOTOKYO, 7,5 m)
cc = "PORT/CONTENEURS"
compte = 0
for by in (42.5, 56.0):
    for bx in (16.0, 35.0, 60.0, 79.0, 98.0):
        for i in range(2):
            for j in range(4):
                x, y = bx + i * 7.9 + 3.75, by + j * 2.45 + 1.05
                for k in range(rnd.choice((1, 2, 2, 3))):
                    compte += 1
                    ok = modele("PORT_Conteneur_%03d" % compte, cc, "models/nt/props_warehouse/container_scaled", x, y, 0.02 + k * 2.6,
                                rnd.choice((0, math.pi)))
                    if ok:
                        bpy.data.objects["PORT_Conteneur_%03d" % compte]["skin"] = rnd.randint(0, 9)
                    else:
                        boite("PORT_Conteneur_%03d" % compte, cc, x - 3.75, y - 1.05, k * 2.6, x + 3.75, y + 1.05, k * 2.6 + 2.59, "tole_bleue")
pose("PORT_Portique_Conteneurs", cc, "models/nt/props_warehouse/container_loader", 104.0, QUAI_Y - 7.0, 0)
if modele("PORT_Portique_Conteneur_Charge", cc, "models/nt/props_warehouse/container_scaled", 104.0, QUAI_Y - 7.0, 0.07, 0):
    bpy.data.objects["PORT_Portique_Conteneur_Charge"]["skin"] = 3
for i, x in enumerate((24, 66, 106)):
    pose("PORT_Chariot_Parc_%d" % i, cc, "models/nt/props_vehicles/forkliftdown", x, 54.2, rnd.uniform(0, 6.28))

# ================================================================== ZONE DE STOCK (ouest) : marchandises pas encore rangées
st = "PORT/STOCK"
MODELES_STOCK = ["models/nt/props_warehouse/boxpallet", "models/nt/props_warehouse/wrapped_product", "models/nt/props_warehouse/sackstack",
                 "models/nt/props_warehouse/ncrate_large", "models/nt/props_warehouse/ncrate_small", "models/nt/props_warehouse/longcrates",
                 "models/nt/props_warehouse/longcrates_covered", "models/nt/props_warehouse/crate_a", "models/nt/props_warehouse/crate_b",
                 "models/props/cs_assault/moneypallet", "models/props/cs_assault/moneypallet03", "models/props_junk/wood_crate002a"]
k = 0
for gx in range(5):
    for gy in range(11):
        if gx == 2 or rnd.random() < 0.12:                         # une allée au milieu + quelques trous
            continue
        x, y = 1.4 + gx * 2.6, 42.0 + gy * 2.4
        m = rnd.choice(MODELES_STOCK)
        pose("PORT_Stock_%03d" % k, st, m, x, y, rnd.choice((0, math.pi / 2)) + rnd.uniform(-0.15, 0.15))
        if "ncrate_small" in m or "crate_" in m or "wood_crate" in m:
            pose("PORT_Stock_%03d_Haut" % k, st, m, x + rnd.uniform(-0.1, 0.1), y, rnd.uniform(0, 6.28), 1.0)
        k += 1
pose("PORT_Stock_Chariot", st, "models/props/cs_assault/forklift", 7.0, 62.0, 1.2)
pose("PORT_Stock_Diable", st, "models/props/cs_assault/handtruck", 7.2, 45.0, 0.4)

# ================================================================== GRUE (plus petite) : échelle, passerelle, cabine ouverte
g = "PORT/GRUES"
gx0, gx1, gy0, gy1, GZ = 20.0, 32.0, QUAI_Y - 12.0, QUAI_Y - 2.5, 17.5
for i, (px, py) in enumerate(((gx0, gy0), (gx1, gy0), (gx0, gy1), (gx1, gy1))):
    boite("PORT_Grue_Pied_%d" % i, g, px - 0.45, py - 0.45, 0.08, px + 0.45, py + 0.45, GZ, "acier_rouge")
    boite("PORT_Grue_Socle_%d" % i, g, px - 0.8, py - 0.8, 0.08, px + 0.8, py + 0.8, 0.6, "beton_mur")
for s_, yy in (("S", gy0), ("N", gy1)):
    boite("PORT_Grue_Traverse_" + s_, g, gx0 - 0.45, yy - 0.5, GZ - 0.9, gx1 + 0.45, yy + 0.5, GZ, "acier_rouge")
    poutre("PORT_Grue_Diag_%s_1" % s_, g, (gx0, yy, 1.0), (gx1, yy, GZ - 1.0), 0.3, "acier_rouge")
    poutre("PORT_Grue_Diag_%s_2" % s_, g, (gx1, yy, 1.0), (gx0, yy, GZ - 1.0), 0.3, "acier_rouge")
for s_, xx in (("O", gx0), ("E", gx1)):
    boite("PORT_Grue_Longeron_" + s_, g, xx - 0.5, gy0 - 0.5, GZ - 0.9, xx + 0.5, gy1 + 14, GZ, "acier_rouge")
boite("PORT_Grue_Passerelle", g, gx0 - 0.5, gy0 - 0.5, GZ, gx1 + 0.5, gy1 + 0.5, GZ + 0.12, "grille" if "grille" in O.MATS else "acier_gris")
garde_corps("PORT_Grue_GC_S", g, (gx0 + 1.2, gy0 - 0.4), (gx1 + 0.4, gy0 - 0.4), GZ + 0.12)
garde_corps("PORT_Grue_GC_N", g, (gx0 - 0.4, gy1 + 0.4), (gx1 + 0.4, gy1 + 0.4), GZ + 0.12)
garde_corps("PORT_Grue_GC_E", g, (gx1 + 0.4, gy0 - 0.4), (gx1 + 0.4, gy1 + 0.4), GZ + 0.12)
for k in range(5):                                                  # flèche au-dessus de l'eau
    yy = gy1 + 2 + k * 2.6
    poutre("PORT_Grue_Fleche_%d" % k, g, (gx0, yy, GZ - 0.5), (gx1, yy + 1.3, GZ - 0.5), 0.2, "acier_rouge")
# cabine de la grue : creuse, porte côté échelle, fenêtres, pupitre
cx0, cy0, cx1, cy1, cz = gx0 + 3, gy0 + 2.5, gx0 + 8, gy0 + 6.5, GZ + 0.12
boite("PORT_Grue_Cabine_Sol", g, cx0, cy0, cz, cx1, cy1, cz + 0.1, "acier_gris")
boite("PORT_Grue_Cabine_Toit", g, cx0 - 0.2, cy0 - 0.2, cz + 2.7, cx1 + 0.2, cy1 + 0.2, cz + 2.85, "acier_gris")
boite("PORT_Grue_Cabine_Mur_N", g, cx0, cy1 - 0.1, cz, cx1, cy1, cz + 1.0, "tole_grise")
boite("PORT_Grue_Cabine_Vitre_N", g, cx0, cy1 - 0.07, cz + 1.0, cx1, cy1 - 0.03, cz + 2.7, "vitre")
boite("PORT_Grue_Cabine_Mur_E", g, cx1 - 0.1, cy0, cz, cx1, cy1, cz + 2.7, "tole_grise")
boite("PORT_Grue_Cabine_Mur_S_G", g, cx0, cy0, cz, cx0 + 1.0, cy0 + 0.1, cz + 2.7, "tole_grise")
boite("PORT_Grue_Cabine_Mur_S_D", g, cx0 + 2.1, cy0, cz, cx1, cy0 + 0.1, cz + 2.7, "tole_grise")
boite("PORT_Grue_Cabine_Mur_S_Haut", g, cx0 + 1.0, cy0, cz + 2.2, cx0 + 2.1, cy0 + 0.1, cz + 2.7, "tole_grise")
boite("PORT_Grue_Cabine_Mur_O", g, cx0, cy0, cz, cx0 + 0.1, cy1, cz + 2.7, "tole_grise")
boite("PORT_Grue_Cabine_Pupitre", g, cx0 + 1.2, cy1 - 1.0, cz, cx1 - 1.2, cy1 - 0.4, cz + 1.0, "acier_gris")
pose("PORT_Grue_Cabine_Siege", g, "models/nt/props_office/officechair", (cx0 + cx1) / 2, cy1 - 1.6, -math.pi / 2, cz + 0.1)
lumiere("PORT_Grue_Cabine_Lumiere", g, ((cx0 + cx1) / 2, (cy0 + cy1) / 2, cz + 2.4), 35, (1.0, 0.9, 0.75))
# échelle (vraie échelle NEOTOKYO, 5,85 m, empilée) sur la face ouest du pied sud-ouest + zone d'échelle invisible
for k in range(3):
    modele("PORT_Grue_Echelle_%d" % k, g, "models/nt/props_warehouse/ladder_256", gx0 - 0.75, gy0, 0.08 + k * 5.85, 0)
o = boite("LADDER_Grue", "PORT/MURS_INVISIBLES", gx0 - 1.05, gy0 - 0.4, 0.08, gx0 - 0.5, gy0 + 0.4, GZ + 1.4, "echelle_invisible")
o.hide_render, o.display_type = True, "WIRE"


# ================================================================== BUREAU DU QUAI (bleu) : on peut entrer
bq = "PORT/BATIMENTS/PORT_Bureau_Quai"
qx0, qy0, qx1, qy1, qh = 80.0, QUAI_Y - 12.5, 88.0, QUAI_Y - 8.0, 3.2
boite("PORT_Bureau_Quai_Sol", bq, qx0, qy0, 0.08, qx1, qy1, 0.2, "beton_sol")
boite("PORT_Bureau_Quai_Mur_N", bq, qx0, qy1 - 0.15, 0.2, qx1, qy1, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Mur_O", bq, qx0, qy0, 0.2, qx0 + 0.15, qy1, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Mur_E", bq, qx1 - 0.15, qy0, 0.2, qx1, qy1, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Mur_S_G", bq, qx0, qy0, 0.2, qx0 + 3.2, qy0 + 0.15, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Mur_S_D", bq, qx0 + 4.4, qy0, 0.2, qx1, qy0 + 0.15, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Linteau", bq, qx0 + 3.2, qy0, 2.4, qx0 + 4.4, qy0 + 0.15, qh, "tole_bleue")
boite("PORT_Bureau_Quai_Fenetre_S", bq, qx0 + 5, qy0 - 0.01, 1.2, qx1 - 0.6, qy0 + 0.02, 2.2, "vitre")
boite("PORT_Bureau_Quai_Fenetre_N", bq, qx0 + 1, qy1 - 0.02, 1.2, qx1 - 1, qy1 + 0.01, 2.2, "vitre")
for i in range(2):
    boite("PORT_Bureau_Quai_Toit_%d" % i, bq, qx0 - 0.3, qy0 - 0.3 + i * (qy1 - qy0 + 0.6) / 2, qh, qx1 + 0.3,
          qy0 - 0.3 + (i + 1) * (qy1 - qy0 + 0.6) / 2, qh + 0.25, "tole_toit")
pose("PORT_Bureau_Quai_Bureau", bq, "models/nt/props_office/desk_military", qx0 + 1.2, qy1 - 1.4, 0, 0.2)
pose("PORT_Bureau_Quai_Chaise", bq, "models/nt/props_office/officechair", qx0 + 2.2, qy1 - 1.4, math.pi / 2, 0.2)
pose("PORT_Bureau_Quai_Classeur", bq, "models/nt/props_office/filecabinet_three", qx1 - 0.45, qy1 - 1.4, math.pi, 0.2)
pose("PORT_Bureau_Quai_Copieur", bq, "models/nt/props_office/copier", qx1 - 1.5, qy0 + 0.7, 0, 0.2)
pose("PORT_Bureau_Quai_Fontaine", bq, "models/nt/props_office/water_cooler", qx0 + 0.5, qy0 + 0.6, 0, 0.2)
modele("PORT_Bureau_Quai_Tableau", bq, "models/nt/props_office/painting_one", qx0 + 0.19, qy0 + 2.6, 1.2, 0)
lumiere("PORT_Bureau_Quai_Lumiere", bq, ((qx0 + qx1) / 2, (qy0 + qy1) / 2, qh - 0.3), 45, (1.0, 0.93, 0.8))

# ================================================================== ENCEINTE : bâtiments plus hauts que le plafond, tunnel
e_ = "PORT/ENCEINTE"
FACADES = ["facade", "facade2", "facade3"]
r3 = random.Random(31)


def bloc_enceinte(nom, x0, y0, x1, y1, haut, mat):
    boite(nom, e_, x0, y0, 0, x1, y1, haut, mat)
    boite(nom + "_Socle", e_, x0 - 0.1, y0 - 0.1, 0, x1 + 0.1, y1 + 0.1, 1.2, "beton_mur")
    boite(nom + "_Acrotere", e_, x0 - 0.15, y0 - 0.15, haut, x1 + 0.15, y1 + 0.15, haut + 0.9, "beton_mur")


def rangee(prefixe, debut, fin, f0, f1, axe, trou=None):
    pos, k = debut, 0
    while pos < fin - 1:
        larg = min(r3.uniform(10, 20), fin - pos)
        a0, a1 = pos, pos + larg
        if trou and a0 < trou[1] and a1 > trou[0]:
            if a0 < trou[0] - 1:
                a1 = trou[0]
            else:
                pos = trou[1]
                continue
        haut = r3.choice((ZPLAF + 2, ZPLAF + 5, ZPLAF + 8, ZPLAF + 12))
        mat = r3.choice(FACADES)
        if axe == "x":
            bloc_enceinte("%s_%02d" % (prefixe, k), a0, f0, a1, f1, haut, mat)
        else:
            bloc_enceinte("%s_%02d" % (prefixe, k), f0, a0, f1, a1, haut, mat)
        pos, k = a1, k + 1


rangee("PORT_Enceinte_Sud", -14, 136, -14, -2, "x", trou=(A0 - 3, A1 + 3))
rangee("PORT_Enceinte_Ouest", -2, QUAI_Y + 2, -14, -2, "y")
rangee("PORT_Enceinte_Est", -2, QUAI_Y + 2, 122, 136, "y")
PIED, EP = 3.5, 0.7
AXC, AR = (A0 + A1) / 2, (A1 - A0) / 2
TY0, TY1 = -26.0, -2.0
SEG = 18


def profil(r):
    pts = [(AXC - r, 0.0), (AXC - r, PIED)]
    for k in range(1, SEG):
        a = math.pi - math.pi * k / SEG
        pts.append((AXC + r * math.cos(a), PIED + r * math.sin(a)))
    return pts + [(AXC + r, PIED), (AXC + r, 0.0)]


INT, EXT = profil(AR), profil(AR + EP)
for k in range(len(INT) - 1):
    prisme("PORT_Tunnel_Voute_%02d" % k, e_, [INT[k], INT[k + 1], EXT[k + 1], EXT[k]][::-1], TY0, TY1, "beton_mur")
ZT = PIED + AR + EP + 1.0
boite("PORT_Pont_Tunnel_Pilier_O", e_, A0 - 3, -14, 0, A0 - EP, -2, ZPLAF + 4, "facade3")
boite("PORT_Pont_Tunnel_Pilier_E", e_, A1 + EP, -14, 0, A1 + 3, -2, ZPLAF + 4, "facade3")
for k in range(len(EXT) - 1):
    (xa, za), (xb, zb) = EXT[k], EXT[k + 1]
    if min(za, zb) >= PIED - 0.01:
        prisme("PORT_Pont_Tympan_%02d" % k, e_, [(xa, za), (xb, zb), (xb, ZT), (xa, ZT)], -14, -2, "beton_mur")
boite("PORT_Pont_Tunnel_Etages", e_, A0 - EP, -14, ZT, A1 + EP, -2, ZPLAF + 4, "facade3")
for yy in (-2.0, -14.5):
    for k in range(len(EXT) - 1):
        prisme("PORT_Tunnel_Arc_%d_%02d" % (int(-yy), k), e_, [INT[k], INT[k + 1], EXT[k + 1], EXT[k]][::-1], yy, yy + 0.5, "beton_sol")
boite("PORT_Tunnel_Route", e_, A0, TY0, -0.3, A1, TY1, 0.06, "asphalte")
boite("PORT_Tunnel_Trottoir_O", e_, A0, TY0, 0.06, TX0, TY1, 0.25, "beton_sol")
boite("PORT_Tunnel_Trottoir_E", e_, TX1, TY0, 0.06, A1, TY1, 0.25, "beton_sol")
boite("PORT_Tunnel_Marquage", e_, (TX0 + TX1) / 2 - 0.1, TY0, 0.06, (TX0 + TX1) / 2 + 0.1, TY1, 0.07, "marquage")
for xx in (A0 + 0.01, A1 - 0.03):
    boite("PORT_Tunnel_Bande_%d" % int(xx), e_, xx, TY0, 0.25, xx + 0.02, TY1, 1.0, "rayures")
for k in range(int((TY1 - TY0) // 4)):
    y = TY1 - 2 - k * 4
    for cote in (-1, 1):
        a = math.radians(55)
        lx, lz = AXC + cote * AR * math.cos(a), PIED + AR * math.sin(a)
        boite("PORT_Tunnel_Sodium_%02d_%d" % (k, cote), e_, lx - 0.3, y - 0.5, lz - 0.1, lx + 0.3, y + 0.5, lz + 0.04, "sodium")
    if k % 3 == 0:
        lumiere("PORT_Tunnel_Lumiere_%02d" % k, e_, (AXC, y, PIED + AR - 1.2), 160, (1.0, 0.55, 0.2), 0.5)
    if k % 4 == 1:
        boite("PORT_Tunnel_Secours_%02d" % k, e_, A0 + 0.02, y - 0.35, 1.9, A0 + 0.08, y + 0.35, 2.25, "secours")
clip("Bout_Du_Tunnel", A0 - 1, TY0 - 0.6, 0, A1 + 1, TY0 + 0.2, PIED + AR + 1)
panneau_vertical("PORT_Panneau_Entree", "PORT/DECORATIONS", AXC, -1.45, ZT + 0.3, 9, 2.25, "panneau_port", math.pi)
# plafond invisible au-dessus de toute la zone (on ne peut pas monter au-dessus des bâtiments)


# ================================================================== VÉHICULES (vrais modèles NEOTOKYO)
v_ = "PORT/VEHICULES"
GARES = [(8, 27.5, "isuzutruck1"), (24, 27.5, "isuzutruck2"), (40, 27.5, "isuzutruck1"), (45, 27.5, "worktruck"),
         (56, 27.5, "isuzutruck1"), (72, 27.5, "garbagetruck"), (92, 27.5, "isuzutruck2")]
for i, (x, y, m) in enumerate(GARES):
    pose("PORT_Camion_%02d" % i, v_, "models/nt/props_vehicles/" + m, x, y, math.pi / 2 + rnd.uniform(-0.05, 0.05))
for i, (x, y, m, rot) in enumerate(((112, 25, "kcar", 0), (115.5, 25, "panelvan", 0), (119, 25, "jcar", math.pi / 2), (112, 30.5, "mcar", math.pi / 2),
                                    (116, 30.5, "vcar", math.pi / 2))):
    pose("PORT_Voiture_%02d" % i, v_, "models/nt/props_vehicles/" + m, x, y, rot)
    if "PORT_Voiture_%02d" % i in bpy.data.objects:
        bpy.data.objects["PORT_Voiture_%02d" % i]["skin"] = rnd.randint(0, 4)
# semi-remorques avec conteneur sur la route du quai
for i, (x, y) in enumerate(((25.0, QUAI_Y - 7.25), (64.0, QUAI_Y - 10.5))):
    pose("PORT_Semi_%d_Tracteur" % i, v_, "models/nt/props_vehicles/renaultrig", x + 7.2, y, 0)
    pose("PORT_Semi_%d_Remorque" % i, v_, "models/nt/props_vehicles/flatbeadtrailer", x, y, 0)
    modele("PORT_Semi_%d_Conteneur" % i, v_, "models/nt/props_warehouse/container_scaled", x, y, sol(x, y) + 1.33, 0)
for i, (x, y, rot) in enumerate(((44, QUAI_Y - 5, 0.4), (95, QUAI_Y - 6, 2.2), (65, 31, 1.0))):
    pose("PORT_Chariot_%02d" % i, v_, "models/props/cs_assault/forklift", x, y, rot)

# ================================================================== DÉCOR : lampadaires, bennes, cônes, caisses
d = "PORT/DECORATIONS"
for i, (x, y) in enumerate([(x, ROUTE_Y - 0.8) for x in range(6, 120, 18)] + [(x, ROUTE_Y + ROUTE_L + 0.8) for x in range(15, 120, 18)]
                           + [(x, QUAI_Y - 14.8) for x in range(10, 120, 22)]):
    sens = 1 if y < ROUTE_Y else -1
    cylindre("PORT_Lampadaire_%02d" % i, d, x, y, 0, 8, 0.1, "acier_gris")
    poutre("PORT_Lampadaire_%02d_Bras" % i, d, (x, y, 7.9), (x, y + sens * 1.3, 7.9), 0.08, "acier_gris")
    boite("PORT_Lampadaire_%02d_Tete" % i, d, x - 0.3, y + sens * 1.3 - 0.18, 7.75, x + 0.3, y + sens * 1.3 + 0.18, 7.92, "lampe")
    lumiere("PORT_Lampadaire_%02d_Lumiere" % i, d, (x, y + sens * 1.3, 7.4), 400, (1.0, 0.78, 0.5), 0.3)
for i, (x, y) in enumerate(((43, 22.5), (47, 22.5), (91, 22.5), (95, 22.5))):
    pose("PORT_Benne_%d" % i, d, "models/props_junk/trashdumpster01a", x, y, math.pi / 2)
for i, x in enumerate(range(int(QR0) - 1, int(QR1) + 2, 2)):
    pose("PORT_Cone_%02d" % i, d, "models/props_junk/trafficcone001a", x, ROUTE_Y + ROUTE_L + 0.9, rnd.uniform(0, 6.28))
for i in range(14):                                                 # marchandises sur le quai
    x, y = rnd.uniform(36, 118), rnd.uniform(QUAI_Y - 7, QUAI_Y - 2)
    if 79 < x < 89:
        continue
    pose("PORT_Quai_Marchandise_%02d" % i, d, rnd.choice(MODELES_STOCK), x, y, rnd.uniform(0, 6.28))
for i in range(6):
    fut("PORT_Fut_Quai_%d" % i, d, rnd.uniform(36, 76), QUAI_Y - 1.8, 0.07)
panneau_vertical("PORT_Panneau_Danger_0", d, 40, QUAI_Y - 14.2, 0.9, 2.5, 1.1, "panneau_danger")
panneau_vertical("PORT_Panneau_Danger_1", d, 100, QUAI_Y - 14.2, 0.9, 2.5, 1.1, "panneau_danger")
for i, x in enumerate((40, 100)):
    for s_ in (-1, 1):
        boite("PORT_Panneau_Danger_%d_Poteau_%d" % (i, s_), d, x + s_ * 1.1 - 0.04, QUAI_Y - 14.15, 0, x + s_ * 1.1 + 0.04, QUAI_Y - 14.07, 2.0, "acier_gris")

# ================================================================== RUELLES : entre les deux hangars et derrière
ru = "PORT/RUELLES"
for i, (x, y, m, rot) in enumerate(((42.0, 7.5, "models/props_junk/trashdumpster01a", 0), (42.0, 10.2, "models/props_junk/trashdumpster01a", 0),
                                    (48.3, 8.0, "models/nt/props_warehouse/sackstack", 0), (48.2, 11.0, "models/nt/props_warehouse/boxpallet", 0.1),
                                    (48.2, 13.0, "models/nt/props_warehouse/wrapped_product", 0), (41.8, 15.5, "models/nt/props_warehouse/woodpallet", 0.2),
                                    (45.0, 19.0, "models/nt/props_vehicles/panelvan", math.pi / 2), (41.6, 13.4, "models/props/cs_assault/moneypallet", 0),
                                    (48.5, 16.2, "models/nt/props_warehouse/ncrate_large", 0), (41.8, 18.5, "models/props_junk/propane_tank001a", 0))):
    pose("PORT_Ruelle_%02d" % i, ru, m, x, y, rot)
for i in range(3):
    pose("PORT_Ruelle_Palettes_%d" % i, ru, "models/nt/props_warehouse/woodpallet", 41.8, 15.5, 0.2 + i * 0.1, 0.17 * (i + 1))
for i in range(5):
    fut("PORT_Ruelle_Fut_%d" % i, ru, 46.5 + (i % 2) * 0.7, 6.8 + (i // 2) * 0.7, 0)
for k, xx in enumerate((40.0, 50.0)):                               # climatiseurs et tuyaux sur les murs du passage
    sens = 1 if xx == 40.0 else -1
    for j in range(3):
        yy = HY0 + 2.5 + j * 4.5
        boite("PORT_Ruelle_Clim_%d_%d" % (k, j), ru, xx, yy, 2.2 + j % 2, xx + sens * 0.7, yy + 1.0, 2.9 + j % 2, "acier_gris")
    boite("PORT_Ruelle_Tuyau_%d" % k, ru, xx, HY0 + 0.5, 5.6, xx + sens * 0.2, HY0 + H["p"] - 0.5, 5.8, "acier_gris")
    boite("PORT_Ruelle_Tableau_Elec_%d" % k, ru, xx, HY0 + 12.5, 0.9, xx + sens * 0.3, HY0 + 13.6, 2.3, "acier_gris")
lumiere("PORT_Ruelle_Lumiere", ru, (45, 12, 6.5), 250, (1.0, 0.75, 0.45), 0.3)
boite("PORT_Ruelle_Lampe", ru, 49.7, 11.8, 6.6, 50.0, 12.2, 6.9, "lampe")
for i, x in enumerate((24, 30, 62, 70, 78, 86)):                     # derrière les hangars (côté enceinte)
    pose("PORT_Arriere_%d" % i, ru, rnd.choice(MODELES_STOCK), x, HY0 - 4.0, rnd.uniform(0, 6.28))
for i, x in enumerate((36, 84)):
    pose("PORT_Arriere_Benne_%d" % i, ru, "models/props_junk/trashdumpster01a", x, HY0 - 4.2, 0)

# ================================================================== VILLE AU LOIN (de l'autre côté de l'eau)
vl = "PORT/DECOR_LOINTAIN"
r2 = random.Random(9)
x = -13
while x < 128:
    w, p, hh = r2.uniform(12, 24), r2.uniform(12, 18), r2.uniform(18, ZPLAF + 8)
    y = QUAI_Y + 120 + r2.uniform(0, 25)
    boite("PORT_Ville_Immeuble_%d" % int(x), vl, x, y, -3, min(x + w, 135), y + p, hh, "ville")
    x += w + r2.uniform(4, 15)

# ================================================================== LUMIÈRE, FICHIER
monde = bpy.data.worlds.new("PORT_Monde")
sc.world = monde
monde.use_nodes = True
fond = monde.node_tree.nodes.get("Background")
try:
    ciel = monde.node_tree.nodes.new("ShaderNodeTexSky")
    ciel.sun_elevation = math.radians(25)
    ciel.sun_rotation = math.radians(230)
    monde.node_tree.links.new(ciel.outputs["Color"], fond.inputs["Color"])
    fond.inputs["Strength"].default_value = 0.45
except Exception:
    fond.inputs["Color"].default_value = (0.4, 0.45, 0.55, 1)
soleil = bpy.data.objects.new("PORT_Soleil", bpy.data.lights.new("PORT_Soleil", "SUN"))
soleil.data.energy, soleil.data.color, soleil.data.angle = 3.0, (1.0, 0.82, 0.62), math.radians(3)
soleil.rotation_euler = (math.radians(55), 0, math.radians(-40))
sc.collection.objects.link(soleil)
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
cam_d = bpy.data.cameras.new("PORT_Camera")
cam_d.clip_end = 4000
cam = bpy.data.objects.new("PORT_Camera", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
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
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type, sp.shading.color_type, sp.clip_end, sp.clip_start = "MATERIAL", "TEXTURE", 3000, 0.1
                    import mathutils
                    sp.region_3d.view_location, sp.region_3d.view_distance = (60, 45, 0), 200
                    sp.region_3d.view_rotation = mathutils.Euler((math.radians(55), 0, math.radians(25))).to_quaternion()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O.ICI, "port.blend"))
print("PORT COMPACT : %d objets, %d conteneurs -> port.blend" % (len(bpy.data.objects), compte))

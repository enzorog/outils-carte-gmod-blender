"""
Textures du PORT (réalistes, sombres, usées — pas cartoon), générées en Python (Pillow) -> blender/textures/*.png
Tuilables. Réutilisables plus tard dans GMod (conversion en VTF).
Lancer : python textures_port.py
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "textures")
os.makedirs(SORTIE, exist_ok=True)


def bruit(n, graine, octaves=5, persistance=0.55):
    """bruit fractal tuilable (0..255), en niveaux de gris (numpy)"""
    import numpy as np
    r = np.random.default_rng(graine)
    total = np.zeros((n, n), dtype=np.float32)
    amp, somme, taille = 1.0, 0.0, 4
    for _ in range(octaves):
        grille = r.random((taille, taille)).astype(np.float32)
        petit = Image.fromarray((grille * 255).astype(np.uint8))
        grand = Image.new("L", (taille * 3, taille * 3))
        for i in range(3):
            for j in range(3):
                grand.paste(petit, (i * taille, j * taille))
        grand = grand.resize((n * 3, n * 3), Image.BICUBIC).crop((n, n, 2 * n, 2 * n))
        total += np.asarray(grand, dtype=np.float32) * amp
        somme += amp
        amp *= persistance
        taille *= 2
        if taille > n:
            break
    total /= somme
    total = (total - total.min()) / (total.max() - total.min() + 1e-6) * 255
    return Image.fromarray(total.astype(np.uint8), "L")


def teinte(gris, sombre, clair):
    """niveaux de gris -> dégradé entre deux couleurs"""
    return Image.merge("RGB", [gris.point(lambda v, a=sombre[i], b=clair[i]: int(a + (b - a) * v / 255)) for i in range(3)])


def melanger(a, b, masque):
    return Image.composite(b, a, masque)


def taches(n, graine, nb, rmin, rmax, flou):
    m = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(m)
    r = random.Random(graine)
    for _ in range(nb):
        x, y, s = r.randrange(n), r.randrange(n), r.randint(rmin, rmax)
        v = r.randint(60, 200)
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                d.ellipse([x + dx - s, y + dy - s * 0.7, x + dx + s, y + dy + s * 0.7], fill=v)
    return m.filter(ImageFilter.GaussianBlur(flou))


def coulures(n, graine, nb, couleur_alpha=140):
    """traînées de rouille / saleté qui coulent vers le bas"""
    m = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(m)
    r = random.Random(graine)
    for _ in range(nb):
        x, y0 = r.randrange(n), r.randrange(n // 3)
        l, w = r.randint(n // 6, n // 2), r.randint(2, 7)
        d.line([(x, y0), (x + r.randint(-4, 4), y0 + l)], fill=r.randint(couleur_alpha // 2, couleur_alpha), width=w)
    return m.filter(ImageFilter.GaussianBlur(3))


def fissures(img, graine, nb, couleur, n):
    d = ImageDraw.Draw(img)
    r = random.Random(graine)
    for _ in range(nb):
        x, y = r.randrange(n), r.randrange(n)
        a = r.uniform(0, 2 * math.pi)
        pts = [(x, y)]
        for _ in range(r.randint(6, 16)):
            a += r.uniform(-0.6, 0.6)
            x, y = x + math.cos(a) * r.randint(6, 18), y + math.sin(a) * r.randint(6, 18)
            pts.append((x, y))
        d.line(pts, fill=couleur, width=r.randint(1, 2))


def sauver(img, nom):
    img.save(os.path.join(SORTIE, nom + ".png"))
    print("texture", nom)


# ---------------------------------------------------------------- sols
def beton_sol(n=1024):            # 4 m, joints de dilatation, taches d'huile, usure
    img = teinte(bruit(n, 1), (88, 87, 83), (150, 148, 140))
    img = melanger(img, Image.new("RGB", (n, n), (58, 56, 52)), taches(n, 2, 26, 20, 90, 18))
    img = melanger(img, Image.new("RGB", (n, n), (40, 38, 36)), taches(n, 3, 10, 8, 30, 6).point(lambda v: v * 0.7))
    d = ImageDraw.Draw(img)
    for k in (0, n // 2):
        d.line([(k, 0), (k, n)], fill=(52, 51, 48), width=3)
        d.line([(0, k), (n, k)], fill=(52, 51, 48), width=3)
    fissures(img, 4, 18, (62, 60, 56), n)
    return img


def asphalte(n=1024):             # 4 m
    g = bruit(n, 5, 6, 0.7)
    img = teinte(g, (26, 26, 28), (64, 63, 62))
    r = random.Random(6)
    px = img.load()
    for _ in range(n * n // 6):
        x, y = r.randrange(n), r.randrange(n)
        v = r.randint(-18, 26)
        c = px[x, y]
        px[x, y] = (max(0, min(255, c[0] + v)),) * 3
    img = melanger(img, Image.new("RGB", (n, n), (20, 20, 22)), taches(n, 7, 8, 40, 120, 30).point(lambda v: v * 0.6))
    fissures(img, 8, 30, (14, 14, 15), n)
    return img


def terre(n=512):                 # 3 m, terre battue et gravillons
    img = teinte(bruit(n, 9), (62, 50, 38), (118, 98, 74))
    d = ImageDraw.Draw(img)
    r = random.Random(10)
    for _ in range(1400):
        x, y, s = r.randrange(n), r.randrange(n), r.randint(1, 3)
        v = r.randint(70, 150)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(v, int(v * 0.9), int(v * 0.8)))
    return img


# ---------------------------------------------------------------- tôles ondulées (2 m)
def tole(base, rouille, n=1024, graine=11, force_rouille=0.5):
    img = Image.new("RGB", (n, n))
    px = img.load()
    periode = 40
    for x in range(n):
        o = 0.5 + 0.5 * math.sin(2 * math.pi * x / periode)
        k = 0.72 + 0.4 * o
        for y in range(n):
            px[x, y] = tuple(int(c * k) for c in base)
    img = ImageChops.multiply(img, teinte(bruit(n, graine), (190, 190, 190), (255, 255, 255)))
    masque = ImageChops.lighter(coulures(n, graine + 1, 60), taches(n, graine + 2, 14, 10, 60, 12).point(lambda v: v * force_rouille))
    img = melanger(img, Image.new("RGB", (n, n), rouille), masque)
    return img


def tole_toit(n=1024):            # toit très rouillé (comme sur la capture), couleur probable sous la lumière
    img = tole((112, 74, 52), (96, 44, 20), n, 21, 1.6)
    img = melanger(img, teinte(bruit(n, 23), (70, 34, 16), (140, 80, 40)), taches(n, 24, 30, 30, 120, 25))
    return img


# ---------------------------------------------------------------- acier peint (grue), écaillé
def acier_peint(couleur, n=512, graine=31):
    img = teinte(bruit(n, graine), tuple(int(c * 0.75) for c in couleur), couleur)
    eclats = taches(n, graine + 1, 50, 2, 10, 1).point(lambda v: 255 if v > 120 else 0)
    img = melanger(img, teinte(bruit(n, graine + 2), (70, 40, 22), (120, 70, 36)), eclats)
    img = melanger(img, Image.new("RGB", (n, n), (78, 38, 18)), coulures(n, graine + 3, 30, 110))
    return img


# ---------------------------------------------------------------- conteneurs (niveaux de gris, teintés par objet)
def conteneur_cote(w=1024, h=256):
    img = Image.new("RGB", (w, h))
    px = img.load()
    nerv = w / 44
    for x in range(w):
        t = (x % nerv) / nerv
        k = 0.78 if t < 0.15 or 0.5 < t < 0.65 else (1.0 if t < 0.5 else 0.88)
        for y in range(h):
            px[x, y] = (int(205 * k),) * 3
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 10], fill=(150, 150, 150))
    d.rectangle([0, h - 12, w, h], fill=(130, 130, 130))
    for x in (0, w - 14):
        d.rectangle([x, 0, x + 14, h], fill=(120, 120, 120))
    usure = bruit(w, 41).resize((w, h))
    img = ImageChops.multiply(img, teinte(usure, (170, 170, 170), (255, 255, 255)))
    rouille = coulures(w, 42, 40).resize((w, h))
    img = melanger(img, Image.new("RGB", (w, h), (90, 60, 40)), rouille)
    d = ImageDraw.Draw(img)
    d.rectangle([w * 0.06, h * 0.18, w * 0.2, h * 0.32], fill=(235, 235, 235))      # étiquette / code
    return img


def conteneur_porte(n=256):
    img = Image.new("RGB", (n, n), (190, 190, 190))
    d = ImageDraw.Draw(img)
    d.line([(n // 2, 0), (n // 2, n)], fill=(90, 90, 90), width=4)
    for x in (n * 0.18, n * 0.36, n * 0.64, n * 0.82):
        d.rectangle([x - 3, 8, x + 3, n - 8], fill=(110, 110, 110))                    # barres de fermeture
        d.rectangle([x - 7, n * 0.45, x + 7, n * 0.55], fill=(90, 90, 90))
    for y in (n * 0.12, n * 0.5, n * 0.88):
        d.rectangle([2, y - 6, 12, y + 6], fill=(80, 80, 80))
        d.rectangle([n - 12, y - 6, n - 2, y + 6], fill=(80, 80, 80))
    d.rectangle([0, 0, n - 1, n - 1], outline=(120, 120, 120), width=8)
    img = ImageChops.multiply(img, teinte(bruit(n, 43), (175, 175, 175), (255, 255, 255)))
    return img


# ---------------------------------------------------------------- bâtiments
def facade_bureaux(n=512, graine=51):     # 1 tuile = 4 fenêtres x 4 étages (12 m x 14 m)
    img = Image.new("RGB", (n, n), (34, 38, 44))
    d = ImageDraw.Draw(img)
    r = random.Random(graine)
    cw, ch = n // 8, n // 6
    for i in range(8):
        for j in range(6):
            x0, y0 = i * cw + 4, j * ch + 8
            allume = r.random() < 0.14
            c = (230, 190, 120) if allume else (18 + r.randint(0, 12), 24 + r.randint(0, 12), 32 + r.randint(0, 14))
            d.rectangle([x0, y0, x0 + cw - 8, y0 + ch - 16], fill=c)
    for j in range(6):
        d.rectangle([0, j * ch, n, j * ch + 6], fill=(58, 60, 64))
    return img


def beton_mur(n=512, graine=61):          # béton de quai / parapet, lignes de coffrage
    img = teinte(bruit(n, graine), (80, 80, 78), (132, 130, 124))
    img = melanger(img, Image.new("RGB", (n, n), (56, 58, 54)), coulures(n, graine + 1, 50, 90))
    d = ImageDraw.Draw(img)
    for k in range(0, n, n // 4):
        d.line([(0, k), (n, k)], fill=(72, 72, 70), width=2)
    for k in range(0, n, n // 2):
        d.line([(k, 0), (k, n)], fill=(72, 72, 70), width=2)
    return img


def coque(n=512):                         # coque : bleu nuit, rouille, bande rouge sous la flottaison
    img = acier_peint((40, 52, 70), n, 71)
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(n * 0.78), n, n], fill=(96, 30, 24))
    return img


def bois(n=512):
    img = Image.new("RGB", (n, n))
    d = ImageDraw.Draw(img)
    r = random.Random(81)
    for k in range(0, n, 64):
        v = r.randint(-14, 14)
        d.rectangle([0, k, n, k + 62], fill=(118 + v, 88 + v, 58 + v))
        for _ in range(6):
            y = k + r.randint(6, 56)
            d.line([(0, y), (n, y + r.randint(-3, 3))], fill=(96 + v, 70 + v, 46 + v), width=1)
    return ImageChops.multiply(img, teinte(bruit(n, 82), (200, 200, 200), (255, 255, 255)))


def grillage(n=256):                      # RGBA : losanges de fil de fer (le reste transparent)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pas = 32
    for k in range(-n, 2 * n, pas):
        d.line([(k, 0), (k + n, n)], fill=(150, 152, 150, 255), width=2)
        d.line([(k, n), (k + n, 0)], fill=(150, 152, 150, 255), width=2)
    return img


def ville_nuit(n=512, graine=91):         # façades lointaines de la ville, fenêtres allumées
    img = Image.new("RGB", (n, n), (20, 22, 28))
    d = ImageDraw.Draw(img)
    r = random.Random(graine)
    for x in range(4, n, 16):
        for y in range(4, n, 20):
            if r.random() < 0.22:
                v = r.randint(150, 255)
                d.rectangle([x, y, x + 9, y + 11], fill=(v, int(v * 0.78), int(v * 0.5)))
    return img


def marquage(n=256):                      # peinture de sol (bande jaune usée)
    img = teinte(bruit(n, 95), (150, 120, 30), (210, 170, 50))
    return melanger(img, Image.new("RGB", (n, n), (90, 88, 80)), taches(n, 96, 30, 4, 20, 3))


TOUT = {
    "beton_sol": beton_sol, "asphalte": asphalte, "terre": terre,
    "tole_grise": lambda: tole((128, 134, 132), (88, 52, 30), graine=13, force_rouille=0.5),
    "tole_bleue": lambda: tole((60, 82, 100), (92, 54, 30), graine=15, force_rouille=0.6),
    "tole_toit": tole_toit,
    "acier_rouge": lambda: acier_peint((150, 36, 26), graine=31),
    "acier_gris": lambda: acier_peint((96, 100, 104), graine=33),
    "acier_jaune": lambda: acier_peint((190, 150, 30), graine=35),
    "conteneur_cote": conteneur_cote, "conteneur_porte": conteneur_porte,
    "facade_bureaux": facade_bureaux, "beton_mur": beton_mur, "coque": coque, "bois": bois,
    "grillage": grillage, "ville_nuit": ville_nuit, "marquage": marquage,
}

if __name__ == "__main__":
    for nom, f in TOUT.items():
        sauver(f(), nom)

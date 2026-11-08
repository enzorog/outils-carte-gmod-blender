"""
Textures supplémentaires du PORT : décalques (avec transparence) qui cassent la répétition, numéros peints,
panneaux, béton plus sombre, panneaux de cabine de chantier, carrosseries.
Lancer : python textures_port_2.py   (après textures_port.py) -> blender/textures/*.png
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from textures_port import bruit, teinte, melanger, taches, coulures, acier_peint, sauver

N = 512


def police(taille):
    for f in ("C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            return ImageFont.truetype(f, taille)
        except OSError:
            continue
    return ImageFont.load_default()


def decal(couleur, masque):
    """image RGBA : couleur + transparence donnée par un masque (L)"""
    img = Image.new("RGBA", masque.size, couleur + (0,))
    img.putalpha(masque)
    return img


def tache_huile():
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    r = random.Random(1)
    for _ in range(18):
        x, y, s = N / 2 + r.gauss(0, 60), N / 2 + r.gauss(0, 50), r.randint(30, 110)
        d.ellipse([x - s, y - s * 0.7, x + s, y + s * 0.7], fill=r.randint(120, 230))
    m = m.filter(ImageFilter.GaussianBlur(14))
    return decal((14, 13, 12), m)


def flaque():
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    r = random.Random(2)
    for _ in range(10):
        x, y, s = N / 2 + r.gauss(0, 70), N / 2 + r.gauss(0, 40), r.randint(50, 130)
        d.ellipse([x - s, y - s * 0.5, x + s, y + s * 0.5], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: 255 if v > 110 else int(v * 2.2))
    return decal((26, 32, 36), m)


def traces_pneus():
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    for x0 in (150, 330):
        for k in range(0, N, 18):
            d.rectangle([x0, k, x0 + 46, k + 10], fill=150)
    m = m.filter(ImageFilter.GaussianBlur(4))
    return decal((18, 17, 16), m)


def numero(n):
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    d.text((N / 2, N / 2), str(n), fill=255, font=police(420), anchor="mm")
    usure = bruit(N, 30 + n).point(lambda v: 255 if v > 70 else 0)
    from PIL import ImageChops
    m = ImageChops.multiply(m, usure)
    return decal((222, 220, 210), m)


def panneau_port():
    img = Image.new("RGB", (1024, 256), (24, 44, 78))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 1015, 247], outline=(220, 220, 220), width=6)
    d.text((40, 70), "東京港  第3埠頭", fill=(235, 235, 235), font=police(90), anchor="lm")
    d.text((40, 185), "TOKYO PORT  —  PIER 3  —  CONTAINER TERMINAL", fill=(200, 205, 210), font=police(44), anchor="lm")
    return melanger(img, Image.new("RGB", img.size, (60, 50, 40)), coulures(1024, 5, 20, 90).resize(img.size))


def panneau_danger():
    img = Image.new("RGB", (N, N), (214, 170, 30))
    d = ImageDraw.Draw(img)
    for k in range(-N, 2 * N, 64):
        d.polygon([(k, 0), (k + 32, 0), (k + 32 - N * 0.18, N * 0.18), (k - N * 0.18, N * 0.18)], fill=(20, 20, 20))
    d.rectangle([0, N * 0.82, N, N], fill=(20, 20, 20))
    d.text((N / 2, N * 0.42), "危険", fill=(20, 20, 20), font=police(150), anchor="mm")
    d.text((N / 2, N * 0.66), "DANGER", fill=(20, 20, 20), font=police(80), anchor="mm")
    return img


def cabine():                                       # cabine de chantier : panneaux nervurés blanc cassé
    img = Image.new("RGB", (N, N), (186, 186, 178))
    d = ImageDraw.Draw(img)
    for x in range(0, N, 32):
        d.line([(x, 0), (x, N)], fill=(150, 150, 144), width=3)
    d.rectangle([0, 0, N, 14], fill=(110, 112, 110))
    d.rectangle([0, N - 14, N, N], fill=(110, 112, 110))
    return melanger(img, Image.new("RGB", (N, N), (100, 90, 70)), coulures(N, 7, 30, 80))


def beton_sol2():                                   # béton plus sombre et plus sale (parc à conteneurs)
    img = teinte(bruit(1024, 41), (66, 64, 60), (120, 116, 108))
    img = melanger(img, Image.new("RGB", (1024, 1024), (42, 40, 36)), taches(1024, 42, 30, 30, 120, 22))
    d = ImageDraw.Draw(img)
    for k in (0, 512):
        d.line([(k, 0), (k, 1024)], fill=(40, 39, 36), width=4)
        d.line([(0, k), (1024, k)], fill=(40, 39, 36), width=4)
    return img


TOUT = {
    "dec_tache_huile": tache_huile, "dec_flaque": flaque, "dec_traces_pneus": traces_pneus,
    "dec_numero_1": lambda: numero(1), "dec_numero_2": lambda: numero(2), "dec_numero_3": lambda: numero(3), "dec_numero_4": lambda: numero(4),
    "panneau_port": panneau_port, "panneau_danger": panneau_danger, "cabine": cabine, "beton_sol2": beton_sol2,
    "carrosserie_bleue": lambda: acier_peint((40, 70, 120), graine=51), "carrosserie_blanche": lambda: acier_peint((190, 190, 184), graine=53),
    "carrosserie_orange": lambda: acier_peint((200, 110, 30), graine=55),
}

if __name__ == "__main__":
    for nom, f in TOUT.items():
        sauver(f(), nom)

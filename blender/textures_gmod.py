"""
Fabrique les matériaux GMod du port qui n'existent pas déjà dans le jeu -> jjk_carte_ecole/materials/jjk_port/*.vtf + *.vmt
(couleurs unies, textures maison, textures de modèles réutilisées sur des murs : conteneurs, bois, poutres rouges...)
Lancer : python textures_gmod.py      (écrit aussi textures_gmod.json : nom -> chemin GMod + taille en pixels)
"""
import os, re, json, struct
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.normpath(os.path.join(ICI, "..", "materials", "jjk_port"))
TEX, TEX_JEU = os.path.join(ICI, "textures"), os.path.join(ICI, "textures_jeu")
os.makedirs(SORTIE, exist_ok=True)


def ecrire_vtf(chemin, img):
    """VTF 7.2 non compressé (BGR888 ou BGRA8888) avec toutes ses mipmaps"""
    alpha = img.mode == "RGBA" and img.getextrema()[3][0] < 255
    img = img.convert("RGBA" if alpha else "RGB")
    w, h = img.size
    mips, a = [], img
    while True:
        mips.append(a)
        if a.size == (1, 1):
            break
        a = a.resize((max(1, a.size[0] // 2), max(1, a.size[1] // 2)), Image.LANCZOS)
    fmt = 12 if alpha else 3                                       # BGRA8888 / BGR888
    flags = 0x2000 if alpha else 0                                 # EIGHTBITALPHA
    tete = struct.pack("<4s2II2HI2H4x3f4xfIBIBBH", b"VTF\0", 7, 2, 80, w, h, flags, 1, 0, 0.5, 0.5, 0.5, 1.0,
                       fmt, len(mips), 0xFFFFFFFF, 0, 0, 1)
    tete += b"\0" * (80 - len(tete))
    corps = b""
    for m in reversed(mips):                                       # de la plus petite à la plus grande
        r = m.tobytes("raw", "BGRA" if alpha else "BGR")
        corps += r
    with open(chemin, "wb") as f:
        f.write(tete + corps)


def puissance2(img, maxi=512):
    w, h = img.size
    nw = min(maxi, 1 << max(2, (w - 1).bit_length()))
    nh = min(maxi, 1 << max(2, (h - 1).bit_length()))
    return img.resize((nw, nh), Image.LANCZOS)


def materiau(nom, img, emissif=False, alpha=False):
    img = puissance2(img)
    ecrire_vtf(os.path.join(SORTIE, nom + ".vtf"), img)
    shader = "UnlitGeneric" if emissif else "LightmappedGeneric"
    extra = '\t"$translucent" "1"\n' if alpha else ""
    with open(os.path.join(SORTIE, nom + ".vmt"), "w", encoding="utf-8") as f:
        f.write('"%s"\n{\n\t"$basetexture" "jjk_port/%s"\n%s\t"$surfaceprop" "metal"\n}\n' % (shader, nom, extra))
    return {"chemin": "jjk_port/" + nom, "px": list(img.size)}


if __name__ == "__main__":
    src = "".join(open(os.path.join(ICI, f), encoding="utf-8").read() for f in ("port_outils.py", "creer_shibuya.py") if os.path.exists(os.path.join(ICI, f)))
    jeu = open(os.path.join(ICI, "textures_jeu.py"), encoding="utf-8").read()
    choix = dict(re.findall(r'"(\w+)": \((?:HL2|CSS), "([^"]+)"\)', jeu))
    table = {}
    # mat_image : texture du jeu si c'est une texture de mur (pas de modèle), sinon matériau maison
    for nom, fichier, tuile in re.findall(r'mat_image\("(\w+)", "(\w+)", ([\d.]+)', src):
        emissif = bool(re.search(r'mat_image\("%s"[^\n]*emission=' % nom, src))
        chemin_png = os.path.join(TEX_JEU, fichier + ".png")
        if not os.path.exists(chemin_png):
            chemin_png = os.path.join(TEX, fichier + ".png")
        if not os.path.exists(chemin_png):
            print("pas d'image pour", nom)
            continue
        px = list(Image.open(chemin_png).size)
        if fichier in choix and not choix[fichier].startswith("models/"):
            table[nom] = {"chemin": choix[fichier], "px": px, "tuile": float(tuile)}
        else:
            d = materiau(nom, Image.open(chemin_png), emissif)
            d["tuile"] = float(tuile)
            table[nom] = d
    # mat_uv : textures plaquées par UV (conteneurs, panneaux)
    for nom, fichier in re.findall(r'mat_uv\("(\w+)", "(\w+)"', src):
        if nom.startswith("dec_"):
            continue
        p = os.path.join(TEX_JEU, fichier + ".png")
        p = p if os.path.exists(p) else os.path.join(TEX, fichier + ".png")
        d = materiau(nom, Image.open(p))
        d["uv"] = True
        table[nom] = d
    for nom in ("conteneur_%d" % k for k in range(1, 6)):
        if nom not in table:
            d = materiau(nom, Image.open(os.path.join(TEX_JEU, nom + ".png")))
            d["uv"] = True
            table[nom] = d
    # mat_uni : couleurs unies (légère variation pour éviter l'aspect plastique)
    for nom, rgb, reste in re.findall(r'mat_uni\("(\w+)", \(([\d., ]+)\)([^\n]*)', src):
        if nom in ("film", "eau"):
            continue
        c = tuple(int(min(1.0, float(v)) ** (1 / 2.2) * 255) for v in rgb.split(","))
        img = Image.new("RGB", (64, 64), c)
        d = materiau(nom, img, "emission=" in reste)
        d["tuile"] = 2.0
        table[nom] = d
    table["eau"] = {"chemin": "nature/water_canals_water2", "px": [512, 512], "tuile": 8.0, "eau": True}
    table["vitre"] = {"chemin": "glass/glasswindow007a", "px": [256, 256], "tuile": 2.0}
    json.dump(table, open(os.path.join(ICI, "textures_gmod.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(table), "matériaux ;", len(os.listdir(SORTIE)) // 2, "faits maison dans materials/jjk_port")

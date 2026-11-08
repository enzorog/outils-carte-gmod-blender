"""
Copie dans l'addon jjk_carte_ecole les modèles NEOTOKYO° utilisés par la carte (models/nt/...) avec leurs matériaux,
pour que GMod (et les joueurs) les aient sans installer NEOTOKYO.
Lancer : python copier_neotokyo.py ../source/jjk_port.vmf
"""
import os, re, sys, shutil
from extraire_modeles import textures_du_mdl

ICI = os.path.dirname(os.path.abspath(__file__))
NT = os.path.normpath(os.path.join(ICI, "..", "..", "..", "..", "..", "NEOTOKYO", "NeotokyoSource"))
ADDON = os.path.normpath(os.path.join(ICI, ".."))


def trouver(rel):
    """chemin réel dans NEOTOKYO (insensible à la casse, comme le moteur)"""
    p = NT
    for part in rel.replace("\\", "/").split("/"):
        if not os.path.isdir(p):
            return None
        noms = {n.lower(): n for n in os.listdir(p)}
        if part.lower() not in noms:
            return None
        p = os.path.join(p, noms[part.lower()])
    return p


def copier(rel):
    src = trouver(rel)
    if not src:
        return False
    dst = os.path.join(ADDON, rel.replace("\\", "/").lower())
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    return True


def materiau(vmt_rel, deja):
    if vmt_rel in deja:
        return True
    if not copier(vmt_rel):
        return False
    deja.add(vmt_rel)
    texte = open(trouver(vmt_rel), encoding="latin-1").read()
    # certains matériaux NEOTOKYO écrivent « xxx.vmt » au lieu de « xxx » pour la texture : on corrige la copie
    corrige = re.sub(r'(\$\w+"?\s+"[^"]+?)\.vmt"', lambda m_: m_.group(1) + '"', texte, flags=re.I)
    if corrige != texte:
        open(os.path.join(ADDON, vmt_rel.replace("\\", "/").lower()), "w", encoding="latin-1").write(corrige)
        texte = corrige
    for m in re.finditer(r'"?\$(basetexture2?|bumpmap|normalmap|detail|envmapmask|phongexponenttexture|selfillummask|lightwarptexture)"?\s+"?([^"\s]+)"?', texte, re.I):
        copier("materials/" + m.group(2).replace("\\", "/").lower().lstrip("/").removesuffix(".vtf").removesuffix(".vmt") + ".vtf")
    for m in re.finditer(r'"?include"?\s+"([^"]+)"', texte, re.I):
        materiau(m.group(1).replace("\\", "/").lower().lstrip("/"), deja)
    return True


if __name__ == "__main__":
    vmf = open(sys.argv[1], encoding="utf-8").read()
    modeles = sorted(set(re.findall(r'"model" "(models/nt/[^"]+)\.mdl"', vmf)))
    deja, manque = set(), []
    for m in modeles:
        if not copier(m + ".mdl"):
            manque.append(m)
            continue
        for ext in (".vvd", ".dx90.vtx", ".dx80.vtx", ".sw.vtx", ".phy"):
            copier(m + ext)
        b = open(trouver(m + ".mdl"), "rb").read()
        noms, dossiers = textures_du_mdl(b)
        for n in noms:
            if not any(materiau("materials/" + (d + n).replace("\\", "/").lower() + ".vmt", deja) for d in dossiers):
                manque.append(m + " : " + n)
    print("NEOTOKYO : %d modèles, %d matériaux copiés dans l'addon" % (len(modeles), len(deja)), ("MANQUE " + "; ".join(manque)) if manque else "")

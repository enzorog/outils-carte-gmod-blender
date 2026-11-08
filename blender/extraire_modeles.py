"""
Extrait des modèles du jeu (HL2, CS:S) avec leurs matériaux et textures -> blender/modeles_jeu/{models,materials}
SourceIO (extension Blender) les importe ensuite avec leurs vraies textures.
Lancer : python extraire_modeles.py models/props_vehicles/truck001a.mdl [autres .mdl ...]
"""
import os, re, struct, sys
import vpk

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "modeles_jeu")
GMOD = os.path.normpath(os.path.join(ICI, "..", "..", "..", ".."))
PAQUETS = [vpk.open(os.path.join(GMOD, "sourceengine", f)) for f in
           ("hl2_misc_dir.vpk", "hl2_textures_dir.vpk", "content_cstrike_dir.vpk", "content_hl2_dir.vpk")]
PAQUETS.append(vpk.open(os.path.join(GMOD, "garrysmod", "garrysmod_dir.vpk")))


def lire(chemin):
    chemin = chemin.replace("\\", "/").lower()
    for p in PAQUETS:
        try:
            return p.get_file(chemin).read()
        except KeyError:
            continue
    return None


def ecrire(chemin, data):
    dest = os.path.join(SORTIE, chemin.replace("\\", "/").lower())
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)


def chaine(b, o):
    return b[o:b.index(b"\0", o)].decode("latin-1")


def textures_du_mdl(b):
    tc, to, dc, do = struct.unpack_from("<4i", b, 204)
    noms = [chaine(b, to + i * 64 + struct.unpack_from("<i", b, to + i * 64)[0]) for i in range(tc)]
    dossiers = [chaine(b, struct.unpack_from("<i", b, do + i * 4)[0]) for i in range(dc)]
    return noms, dossiers


def extraire_materiau(vmt_chemin, deja):
    if vmt_chemin in deja:
        return True
    data = lire(vmt_chemin)
    if data is None:
        return False
    deja.add(vmt_chemin)
    ecrire(vmt_chemin, data)
    texte = data.decode("latin-1")
    for m in re.finditer(r'"?\$(basetexture2?|bumpmap|normalmap|detail|envmapmask|phongexponenttexture|selfillummask)"?\s+"?([^"\s]+)"?', texte, re.I):
        vtf = "materials/" + m.group(2).replace("\\", "/").lower().removesuffix(".vtf") + ".vtf"
        d = lire(vtf)
        if d is not None:
            ecrire(vtf, d)
    for m in re.finditer(r'"?include"?\s+"([^"]+)"', texte, re.I):            # matériaux « patch »
        extraire_materiau(m.group(1).replace("\\", "/").lower(), deja)
    return True


def extraire_modele(mdl):
    mdl = mdl.lower().removesuffix(".mdl")
    b = lire(mdl + ".mdl")
    if b is None:
        print("INTROUVABLE", mdl)
        return False
    ecrire(mdl + ".mdl", b)
    for ext in (".vvd", ".dx90.vtx", ".dx80.vtx", ".sw.vtx", ".phy", ".ani"):
        d = lire(mdl + ext)
        if d is not None:
            ecrire(mdl + ext, d)
    noms, dossiers = textures_du_mdl(b)
    deja, manque = set(), []
    for n in noms:
        if not any(extraire_materiau("materials/" + (d + n).replace("\\", "/").lower() + ".vmt", deja) for d in dossiers):
            manque.append(n)
    print("modèle", mdl, "-", len(deja), "matériaux", ("MANQUE " + ", ".join(manque)) if manque else "")
    return True


if __name__ == "__main__":
    for m in sys.argv[1:]:
        extraire_modele(m)

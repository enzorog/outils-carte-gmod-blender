"""
Lecteur de textures Valve (.vtf) -> PNG, sans rien installer (numpy + Pillow).
Gère les formats courants : DXT1, DXT3, DXT5, RGBA8888, BGRA8888, RGB888, BGR888, BGRX8888.
Lit la plus grande image (le dernier mipmap du fichier).
  from vtf_png import vtf_vers_image ; img = vtf_vers_image(octets)
  python vtf_png.py fichier.vtf sortie.png
"""
import struct, sys
import numpy as np
from PIL import Image

FORMATS = {0: ("RGBA", 4), 1: ("ABGR", 4), 2: ("RGB", 3), 3: ("BGR", 3), 12: ("BGRA", 4), 16: ("BGRX", 4),
           13: ("DXT1", 0.5), 14: ("DXT3", 1), 15: ("DXT5", 1)}


def _couleurs_565(c):
    r = ((c >> 11) & 31) * 255 // 31
    g = ((c >> 5) & 63) * 255 // 63
    b = (c & 31) * 255 // 31
    return np.stack([r, g, b], -1).astype(np.int32)


def _dxt_couleur(blocs, dxt1):
    c0 = blocs[:, 0].astype(np.uint32) | (blocs[:, 1].astype(np.uint32) << 8)
    c1 = blocs[:, 2].astype(np.uint32) | (blocs[:, 3].astype(np.uint32) << 8)
    idx = blocs[:, 4].astype(np.uint32) | (blocs[:, 5].astype(np.uint32) << 8) | (blocs[:, 6].astype(np.uint32) << 16) | (blocs[:, 7].astype(np.uint32) << 24)
    p0, p1 = _couleurs_565(c0), _couleurs_565(c1)
    quatre = (c0 > c1) | (not dxt1)
    p2 = np.where(quatre[:, None], (2 * p0 + p1) // 3, (p0 + p1) // 2)
    p3 = np.where(quatre[:, None], (p0 + 2 * p1) // 3, 0)
    pal = np.stack([p0, p1, p2, p3], 1)                         # (n, 4, 3)
    sel = np.stack([(idx >> (2 * k)) & 3 for k in range(16)], 1)  # (n, 16)
    return np.take_along_axis(pal, sel[:, :, None].astype(np.int64), 1)      # (n, 16, 3)


def _dxt5_alpha(blocs):
    a0, a1 = blocs[:, 0].astype(np.int32), blocs[:, 1].astype(np.int32)
    bits = np.zeros(len(blocs), dtype=np.uint64)
    for k in range(6):
        bits |= blocs[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    pal = np.zeros((len(blocs), 8), dtype=np.int32)
    pal[:, 0], pal[:, 1] = a0, a1
    huit = a0 > a1
    for k in range(1, 7):
        pal[:, k + 1] = np.where(huit, ((7 - k) * a0 + k * a1) // 7, 0)
    for k in range(1, 5):
        pal[:, k + 1] = np.where(huit, pal[:, k + 1], ((5 - k) * a0 + k * a1) // 5)
    pal[:, 6] = np.where(huit, pal[:, 6], 0)
    pal[:, 7] = np.where(huit, pal[:, 7], 255)
    sel = np.stack([((bits >> np.uint64(3 * k)) & np.uint64(7)).astype(np.int64) for k in range(16)], 1)
    return np.take_along_axis(pal, sel, 1)


def _assembler(px, w, h):
    bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
    img = px.reshape(bh, bw, 4, 4, -1).transpose(0, 2, 1, 3, 4).reshape(bh * 4, bw * 4, -1)
    return img[:h, :w]


def vtf_vers_image(d):
    assert d[:4] == b"VTF\0", "pas un VTF"
    w, h = struct.unpack_from("<HH", d, 16)
    fmt = struct.unpack_from("<i", d, 52)[0]
    nom, octets = FORMATS.get(fmt, (None, None))
    if nom is None:
        raise ValueError("format VTF %d non géré" % fmt)
    if nom.startswith("DXT"):
        taille = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * (8 if nom == "DXT1" else 16)
    else:
        taille = w * h * octets
    brut = np.frombuffer(d[len(d) - taille:], dtype=np.uint8)
    if nom == "DXT1":
        rgb = _dxt_couleur(brut.reshape(-1, 8), True)
        img = _assembler(np.concatenate([rgb, np.full(rgb.shape[:2] + (1,), 255)], -1), w, h)
    elif nom == "DXT5":
        b = brut.reshape(-1, 16)
        a = _dxt5_alpha(b[:, :8])
        rgb = _dxt_couleur(b[:, 8:], False)
        img = _assembler(np.concatenate([rgb, a[:, :, None]], -1), w, h)
    elif nom == "DXT3":
        b = brut.reshape(-1, 16)
        a = np.stack([((b[:, k // 2] >> (4 * (k % 2))) & 15) * 17 for k in range(16)], 1).astype(np.int32)
        rgb = _dxt_couleur(b[:, 8:], False)
        img = _assembler(np.concatenate([rgb, a[:, :, None]], -1), w, h)
    else:
        px = brut.reshape(h, w, octets).astype(np.int32)
        ordre = {"RGBA": [0, 1, 2, 3], "ABGR": [3, 2, 1, 0], "RGB": [0, 1, 2], "BGR": [2, 1, 0], "BGRA": [2, 1, 0, 3], "BGRX": [2, 1, 0]}[nom]
        img = px[:, :, ordre]
        if img.shape[2] == 3:
            img = np.concatenate([img, np.full((h, w, 1), 255)], -1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")


if __name__ == "__main__":
    vtf_vers_image(open(sys.argv[1], "rb").read()).save(sys.argv[2])

"""
Importe tous les modèles extraits (modeles_jeu/) avec SourceIO, les aligne sur une grille et rend une planche
-> apercus/galerie_modeles.png + affiche les dimensions (mètres) de chacun.
Lancer : blender.exe -b --factory-startup --python galerie_modeles.py
"""
import bpy, addon_utils, os, math, glob
from mathutils import Vector

addon_utils.enable("SourceIO-master", default_set=False)
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.join(ICI, "modeles_jeu")


def importer(mdl):
    avant = set(bpy.data.objects)
    bpy.ops.sourceio.mdl(filepath=mdl, directory=os.path.dirname(mdl) + os.sep, files=[{"name": os.path.basename(mdl)}],
                         discover_resources=True, import_textures=True, import_physics=False, scale=0.0254)
    return [o for o in bpy.data.objects if o not in avant]


def boite_englobante(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


if __name__ == "__main__":
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    sc = bpy.context.scene
    fichiers = sorted(glob.glob(os.path.join(RACINE, "models", "**", "*.mdl"), recursive=True))
    x = 0.0
    for f in fichiers:
        objs = importer(f)
        if not objs:
            print("ECHEC", f)
            continue
        bpy.context.view_layer.update()
        mn, mx = boite_englobante(objs)
        racines = [o for o in objs if o.parent is None]
        for o in racines:
            o.location += Vector((x - mn.x, -mn.y - (mx.y - mn.y) / 2 * 0, -mn.z))
        d = mx - mn
        print("DIM %-55s L %.2f  l %.2f  h %.2f" % (os.path.relpath(f, RACINE).replace("\\", "/"), d.x, d.y, d.z))
        x += d.x + 2.0
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.color = (0.55, 0.6, 0.65)
    s = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN"))
    s.data.energy = 4
    s.rotation_euler = (0.9, 0.2, 0.6)
    sc.collection.objects.link(s)
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = x * 0.52
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (x / 2, -80, 20)
    cam.rotation_euler = (math.radians(80), 0, 0)
    sc.render.resolution_x, sc.render.resolution_y = 3200, 700
    sc.render.filepath = os.path.join(ICI, "apercus", "galerie_modeles.png")
    bpy.ops.render.render(write_still=True)

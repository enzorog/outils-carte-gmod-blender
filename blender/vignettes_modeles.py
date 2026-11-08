"""
Rend une vignette par modèle (.mdl) d'un dossier de jeu Source, avec SourceIO, puis une planche par dossier.
Lancer : blender.exe -b --factory-startup --python vignettes_modeles.py -- <dossier models> <dossier sortie> [filtre...]
Sortie : <sortie>/<sous-dossier>.png (planche) + <sortie>/liste.txt (modèle, dimensions en m, triangles)
"""
import bpy, addon_utils, os, sys, math, glob
from mathutils import Vector

addon_utils.enable("SourceIO-master", default_set=False)
args = sys.argv[sys.argv.index("--") + 1:]
RACINE, SORTIE = args[0], args[1]
FILTRES = args[2:]
os.makedirs(os.path.join(SORTIE, "v"), exist_ok=True)

sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x = sc.render.resolution_y = 256
sc.render.film_transparent = False
w = bpy.data.worlds.new("w")
sc.world = w
w.color = (0.32, 0.33, 0.35)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
sc.collection.objects.link(cam)
sc.camera = cam

fichiers = sorted(glob.glob(os.path.join(RACINE, "**", "*.mdl"), recursive=True))
if FILTRES:
    fichiers = [f for f in fichiers if any(k in f.replace("\\", "/") for k in FILTRES)]
liste = open(os.path.join(SORTIE, "liste.txt"), "a", encoding="utf-8")
for i, f in enumerate(fichiers):
    rel = os.path.relpath(f, RACINE).replace("\\", "/")
    avant = set(bpy.data.objects)
    try:
        bpy.ops.sourceio.mdl(filepath=f, directory=os.path.dirname(f) + os.sep, files=[{"name": os.path.basename(f)}],
                             discover_resources=True, import_textures=True, import_physics=False, scale=0.0254)
    except Exception as e:
        print("ECHEC", rel, e)
        continue
    nouv = [o for o in bpy.data.objects if o not in avant]
    mesh = [o for o in nouv if o.type == "MESH"]
    if mesh:
        bpy.context.view_layer.update()
        pts = [o.matrix_world @ Vector(c) for o in mesh for c in o.bound_box]
        mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        d, centre = mx - mn, (mn + mx) / 2
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in mesh)
        dirn = Vector((1.0, -1.3, 0.8)).normalized()
        cam.location = centre + dirn * (d.length * 2 + 1)
        cam.rotation_euler = (-dirn).to_track_quat("-Z", "Y").to_euler()
        cam.data.ortho_scale = max(d.length * 1.05, 0.1)
        cam.data.clip_end = d.length * 6 + 10
        sc.render.filepath = os.path.join(SORTIE, "v", rel.replace("/", "__").replace(".mdl", ".png"))
        bpy.ops.render.render(write_still=True)
        liste.write("%s\t%.2f\t%.2f\t%.2f\t%d\n" % (rel, d.x, d.y, d.z, tris))
        liste.flush()
    for o in nouv:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)
    print("VIGNETTE %d/%d %s" % (i + 1, len(fichiers), rel))
liste.close()

"""
Transforme le port Blender (port.blend) en carte GMod (.vmf) :
  - chaque objet maison (boîtes, voûtes, cylindres...) devient une brosse, avec la même texture et la même échelle ;
  - les objets du jeu (fûts, caisses, chariot...) deviennent des prop_static ;
  - les lumières Blender deviennent des lumières de la carte, + soleil, eau, ciel, points d'apparition.
Opti : seuls les gros volumes (sol, murs, bâtiments, hangars, tunnel) coupent la visibilité ; tout le petit décor est en
func_detail, les petits props disparaissent au loin, échelle de lumière large sur les grandes surfaces.
Lancer : blender.exe -b port.blend --python exporter_gmod.py      -> ../source/jjk_port.vmf
"""
import bpy, bmesh, os, re, json, math
from mathutils import Vector

ICI = os.path.dirname(os.path.abspath(bpy.data.filepath))
SORTIE = os.path.normpath(os.path.join(ICI, "..", "source", os.environ.get("CARTE", "jjk_port") + ".vmf"))
TABLE = json.load(open(os.path.join(ICI, "textures_gmod.json"), encoding="utf-8"))
U = 39.37                                                      # 1 m = 39,37 unités (1 unité = 1 pouce)
_tout = [o for o in bpy.data.objects if o.type == "MESH" and not (bpy.data.collections.get("PORT_Modeles_Jeu_Sources") and o.name in bpy.data.collections["PORT_Modeles_Jeu_Sources"].all_objects)]
_pts = [o.matrix_world @ Vector(c) for o in _tout for c in o.bound_box]
BMIN = Vector((min(p.x for p in _pts), min(p.y for p in _pts), min(p.z for p in _pts)))
BMAX = Vector((max(p.x for p in _pts), max(p.y for p in _pts), max(p.z for p in _pts)))
OX, OY = (BMIN.x + BMAX.x) / 2, (BMIN.y + BMAX.y) / 2               # centre de la carte (m)
DECALAGE_VILLE = 0.0
NODRAW, CIEL = "TOOLS/TOOLSNODRAW", "TOOLS/TOOLSSKYBOX"
STRUCTURE = re.compile(r"^PORT_(Terrain|Enceinte_|Pont_Tunnel|Tunnel_Voute|Tour_(Facades|Socle)|Quai_(Principal|Mur)|Eau|"
                       r"Hangar_\d+_(Dalle|Mur_|Facade_|Socle_|Toit|Pignon))|^SHI_(Bat_\d{4}$|Enceinte_\d+$|Sol_)")
IGNORE = re.compile(r"(_Film|_Brume|Flaque|Huile|Tache|Traces|_Numero|PORT_Dec_|PORT_Decal_|Marquage_Place)")

ids = [1]
solides_monde, solides_detail, entites = [], [], []


def nid():
    ids[0] += 1
    return ids[0]


def P(v, ville=False):
    return ((v.x - OX) * U, (v.y + (DECALAGE_VILLE if ville else 0) - OY) * U, v.z * U)


def axes_monde(n, tuile_u):
    """projection « boîte » comme dans Blender : axes dans le plan de la face"""
    n = Vector(n).normalized()
    if abs(n.z) > 0.7:
        u, v = Vector((1, 0, 0)), Vector((0, -1, 0))
    else:
        u = Vector((-n.y, n.x, 0)).normalized()
        v = Vector((0, 0, -1))
    return u, v


def cote(p1, p2, p3, mat, uax, vax, lm):
    return ('\t\tside\n\t\t{\n\t\t\t"id" "%d"\n\t\t\t"plane" "(%.2f %.2f %.2f) (%.2f %.2f %.2f) (%.2f %.2f %.2f)"\n'
            '\t\t\t"material" "%s"\n\t\t\t"uaxis" "%s"\n\t\t\t"vaxis" "%s"\n\t\t\t"rotation" "0"\n\t\t\t"lightmapscale" "%d"\n'
            '\t\t\t"smoothing_groups" "0"\n\t\t}\n' % ((nid(),) + tuple(p1) + tuple(p2) + tuple(p3) + (mat.upper(), uax, vax, lm)))


def axe_txt(direction, decalage, echelle):
    return "[%.5f %.5f %.5f %.3f] %.5f" % (direction.x, direction.y, direction.z, decalage, echelle)


def brosse(o, detail):
    """objet Blender convexe -> brosse VMF ; renvoie False si l'objet n'est pas convexe ou trop fin"""
    ville = o.name.startswith("PORT_Ville_")
    me = o.data
    mw = o.matrix_world
    pts = [Vector(P(mw @ v.co, ville)) for v in me.vertices]
    if len(pts) < 4:
        return False
    if any(abs(c) > 15200 for q in pts for c in q):            # hors des limites de la carte (ville trop loin)
        return True
    centre = sum(pts, Vector()) / len(pts)
    taille = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    if min(taille) < 0.5:
        return False
    uvl = me.uv_layers.active
    cotes = []
    plans = []
    for poly in me.polygons:
        vs = [pts[i] for i in poly.vertices]
        n = (vs[1] - vs[0]).cross(vs[2] - vs[0])
        if n.length < 1e-4:
            # cherche 3 points non alignés
            for k in range(2, len(vs)):
                n = (vs[1] - vs[0]).cross(vs[k] - vs[0])
                if n.length > 1e-4:
                    break
        if n.length < 1e-4:
            continue
        n.normalize()
        if n.dot(vs[0] - centre) < 0:
            n = -n
        if any(abs(n.dot(q.normalized() if False else q) - n.dot(vs[0])) < 0 for q in ()):  # (réservé)
            pass
        d = n.dot(vs[0])
        if any(n.dot(q) - d > 1.0 for q in pts):                   # un sommet dépasse : pas convexe
            return False
        if any(abs(n.dot(pl[0]) - 1) < 1e-4 and abs(pl[1] - d) < 0.05 for pl in plans):
            continue                                               # face coplanaire déjà vue
        plans.append((n, d))
        nom_mat = (o.material_slots[poly.material_index].material.name if o.material_slots else "PORT_beton_mur")
        cle = nom_mat.replace("PORT_", "")
        t = TABLE.get(cle)
        mat = t["chemin"] if t else "concrete/concretewall074a"
        if t and t.get("eau"):
            mat = mat if n.z > 0.7 else NODRAW
        # axes de texture
        if t and t.get("uv") and uvl:
            li = list(poly.loop_indices)
            a, b, c = (pts[me.loops[i].vertex_index] for i in li[:3])
            ua, ub, uc = (uvl.data[i].uv for i in li[:3])
            W, H = t["px"]
            e1, e2 = b - a, c - a
            m11, m12, m22 = e1.dot(e1), e1.dot(e2), e2.dot(e2)
            det = m11 * m22 - m12 * m12
            if abs(det) < 1e-6:
                ux, vx = axes_monde(n, 1)
                uax, vax = axe_txt(ux, 0, 0.25), axe_txt(vx, 0, 0.25)
            else:
                def gradient(fa, fb, fc):
                    d1, d2 = fb - fa, fc - fa
                    x = (d1 * m22 - d2 * m12) / det
                    y = (d2 * m11 - d1 * m12) / det
                    return e1 * x + e2 * y
                gu = gradient(ua.x * W, ub.x * W, uc.x * W)
                gv = gradient((1 - ua.y) * H, (1 - ub.y) * H, (1 - uc.y) * H)
                su, sv = max(gu.length, 1e-6), max(gv.length, 1e-6)
                uax = axe_txt(gu / su, ua.x * W - a.dot(gu), 1 / su)
                vax = axe_txt(gv / sv, (1 - ua.y) * H - a.dot(gv), 1 / sv)
        else:
            tuile = (t or {}).get("tuile", 2.0)
            px = (t or {}).get("px", [512, 512])
            ux, vx = axes_monde(n, tuile)
            uax, vax = axe_txt(ux, 0, tuile * U / px[0]), axe_txt(vx, 0, tuile * U / px[1])
        aire = poly.area * (U * U) if False else (vs[1] - vs[0]).cross(vs[2] - vs[0]).length
        lm = 64 if (ville or poly.area > 400) else (32 if poly.area > 60 or detail else 16)
        # 3 points du plan, dans le sens attendu par vbsp (normale sortante)
        p1, p2, p3 = vs[0], vs[1], vs[2]
        nn = (p1 - p2).cross(p3 - p2)
        if nn.dot(centre - p2) > 0:
            p1, p3 = p3, p1
        cotes.append(cote(p1, p2, p3, mat, uax, vax, lm))
    if len(plans) < 4:
        return False
    txt = '\tsolid\n\t{\n\t\t"id" "%d"\n%s\t}\n' % (nid(), "".join(cotes))
    (solides_detail if detail else solides_monde).append(txt)
    return True


def boite_brute(x0, y0, z0, x1, y1, z1, mat, liste):
    """boîte en unités (ciel, sous-sol)"""
    faces = [((x0, y1, z1), (x1, y1, z1), (x1, y0, z1)), ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0)),
             ((x0, y1, z1), (x0, y0, z1), (x0, y0, z0)), ((x1, y1, z0), (x1, y0, z0), (x1, y0, z1)),
             ((x1, y1, z1), (x0, y1, z1), (x0, y1, z0)), ((x1, y0, z0), (x0, y0, z0), (x0, y0, z1))]
    cs = []
    for f in faces:
        n = Vector(f[0]).__sub__(Vector(f[1])).cross(Vector(f[2]) - Vector(f[1]))
        ux, vx = axes_monde(n, 1)
        cs.append(cote(Vector(f[0]), Vector(f[1]), Vector(f[2]), mat, axe_txt(ux, 0, 0.25), axe_txt(vx, 0, 0.25), 64))
    liste.append('\tsolid\n\t{\n\t\t"id" "%d"\n%s\t}\n' % (nid(), "".join(cs)))


def entite(classe, origine, **cles):
    lignes = ['\t"id" "%d"\n\t"classname" "%s"\n\t"origin" "%.1f %.1f %.1f"\n' % ((nid(), classe) + tuple(origine))]
    for k, v in cles.items():
        lignes.append('\t"%s" "%s"\n' % (k, v))
    entites.append("entity\n{\n%s}\n" % "".join(lignes))


# ------------------------------------------------------------------ parcours de la scène
stats = {"brosses": 0, "detail": 0, "props": 0, "ignores": 0, "non_convexes": [], "lumieres": 0}
sources = bpy.data.collections.get("PORT_Modeles_Jeu_Sources")
objets_sources = set(sources.all_objects) if sources else set()
for o in bpy.data.objects:
    if o in objets_sources or o.type not in ("MESH", "LIGHT"):
        continue
    if o.type == "LIGHT":
        if o.data.type == "POINT":
            c = o.data.color
            br = max(30, min(400, o.data.energy * 0.3))
            entite("light", P(o.matrix_world.translation), _light="%d %d %d %d" % (c[0] * 255, c[1] * 255, c[2] * 255, br),
                   _fifty_percent_distance="%d" % (max(200, min(900, o.data.energy ** 0.5 * 18))),
                   _zero_percent_distance="%d" % (max(500, min(2200, o.data.energy ** 0.5 * 45))))
            stats["lumieres"] += 1
        continue
    if "mdl" in o:
        mw = o.matrix_world
        rot = mw.to_3x3().normalized().to_euler("XYZ")
        diag = max(o.dimensions) if o.dimensions else 1
        petit = diag < 2.0
        dynamique = any(k in o["mdl"] for k in ("tire0", "wood_crate", "trashdumpster", "trafficcone", "oildrum", "couch", "chair_office", "bluebarrel", "barrelwarning", "handtruck", "props_warehouse/crate_", "mop_bucket", "microwave", "luggage_", "janitor_cart", "folding_sign", "officechair", "fireext", "ceiling_rotate_fan", "banner01", "propane_tank", "signage_stand", "samurai_helmet", "stool_short", "recyclebin"))
        if dynamique:                                               # objets « physiques » du jeu : fixes, solides, sans physique
            entite("prop_dynamic", P(mw.translation), model=o["mdl"], skin=str(o.get("skin", 0)), angles="%.2f %.2f %.2f" % (math.degrees(rot.y), math.degrees(rot.z), math.degrees(rot.x)),
                   solid="6", DisableBoneFollowers="1", disableshadows="1", fademindist="1800" if petit else "-1",
                   fademaxdist="2600" if petit else "0", fadescale="1", spawnflags="0")
            stats["props"] += 1
            continue
        entite("prop_static", P(mw.translation), model=o["mdl"], angles="%.2f %.2f %.2f" % (math.degrees(rot.y), math.degrees(rot.z), math.degrees(rot.x)),
               solid="6", skin=str(o.get("skin", 0)), disableshadows="1" if petit else "0", fademindist="1800" if petit else "-1",
               fademaxdist="2600" if petit else "0", fadescale="1")
        stats["props"] += 1
        continue
    if IGNORE.search(o.name) or not o.data.polygons:
        stats["ignores"] += 1
        continue
    if o.name.startswith("PORT_Eau"):
        # eau : une seule brosse, limitée en Y, surface en matériau d'eau
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        x0, y0, z0 = P(Vector((min(q.x for q in bb), min(q.y for q in bb), min(q.z for q in bb))))
        x1, y1, z1 = P(Vector((max(q.x for q in bb), max(q.y for q in bb), max(q.z for q in bb))))
        faces_eau = []
        boite_brute(x0, y0, z0, x1, y1, z1, NODRAW, faces_eau)
        faces_eau[0] = faces_eau[0].replace('"TOOLS/TOOLSNODRAW"', '"NATURE/WATER_CANALS_WATER2"', 1)
        solides_monde.append(faces_eau[0])
        continue
    if o.dimensions.length < 0.05:
        continue
    if o.name.startswith("CLIP_") or o.name.startswith("LADDER_"):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        a_ = P(Vector((min(q.x for q in bb), min(q.y for q in bb), min(q.z for q in bb))))
        b_ = P(Vector((max(q.x for q in bb), max(q.y for q in bb), max(q.z for q in bb))))
        if o.name.startswith("CLIP_"):
            boite_brute(*a_, *b_, "TOOLS/TOOLSPLAYERCLIP", solides_monde)
        else:
            tmp = []
            boite_brute(*a_, *b_, "TOOLS/TOOLSINVISIBLELADDER", tmp)
            entites.append('entity\n{\n\t"id" "%d"\n\t"classname" "func_ladder"\n%s}\n' % (nid(), tmp[0]))
        continue
    detail = not STRUCTURE.search(o.name)
    ancien = None
    if len(o.data.polygons) == 1 or min(o.dimensions) * U < 0.9:
        # plan (panneau) ou boîte trop fine (marquage) : on lui donne 1 unité d'épaisseur, vers l'arrière / vers le haut
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        if len(bm.faces) == 1:
            f = bm.faces[0]
            ep = -f.normal * (1.2 / U) / max(o.scale)
            r = bmesh.ops.extrude_face_region(bm, geom=[f])
            bmesh.ops.translate(bm, vec=ep, verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        else:
            dims = [max(v.co[i] for v in bm.verts) - min(v.co[i] for v in bm.verts) for i in range(3)]
            i = dims.index(min(dims))
            haut = max(v.co[i] for v in bm.verts)
            for v in bm.verts:
                if v.co[i] > haut - 1e-6:
                    v.co[i] += (1.0 / U) / max(o.scale)
        neuf = bpy.data.meshes.new(o.name + "_epais")
        bm.to_mesh(neuf)
        bm.free()
        for m_ in o.data.materials:                                 # garder le matériau (panneaux, marquages)
            neuf.materials.append(m_)
        if len(o.data.polygons) == 1 and o.data.uv_layers:
            pass
        ancien, o.data = o.data, neuf
    ok = brosse(o, detail)
    if ancien is not None:
        o.data = ancien
    if ok:
        stats["detail" if detail else "brosses"] += 1
    else:
        stats["non_convexes"].append(o.name)

# ------------------------------------------------------------------ ciel (boîte fermée autour de tout), sous-sol
# limite de la carte : collée à l'enceinte, plafond = le haut du plus haut bâtiment
_enc = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(("PORT_Enceinte_", "PORT_Pont_Tunnel", "SHI_Enceinte_"))]
_pe = [o.matrix_world @ Vector(c) for o in _enc for c in o.bound_box] or _pts
X0, Y0, Z0 = P(Vector((min(q.x for q in _pe), BMIN.y, BMIN.z - 4)))
X1, Y1, Z1 = P(Vector((max(q.x for q in _pe), BMAX.y, max(q.z for q in _pe))))
E = 16
for b in ((X0 - E, Y0 - E, Z0 - E, X1 + E, Y1 + E, Z0), (X0 - E, Y0 - E, Z1, X1 + E, Y1 + E, Z1 + E),
          (X0 - E, Y0 - E, Z0, X0, Y1 + E, Z1), (X1, Y0 - E, Z0, X1 + E, Y1 + E, Z1),
          (X0, Y0 - E, Z0, X1, Y0, Z1), (X0, Y1, Z0, X1, Y1 + E, Z1)):
    boite_brute(*b, CIEL, solides_monde)
# sous l'eau : fond (pour que l'eau ait un fond)
_eau = bpy.data.objects["PORT_Eau"]
_bb = [_eau.matrix_world @ Vector(c) for c in _eau.bound_box]
fx0, fy0, fz0 = P(Vector((min(q.x for q in _bb), min(q.y for q in _bb), min(q.z for q in _bb) - 3)))
fx1, fy1, fz1 = P(Vector((max(q.x for q in _bb), max(q.y for q in _bb), min(q.z for q in _bb))))
boite_brute(fx0, fy0, fz0, fx1, fy1, fz1, "NATURE/DIRTFLOOR006A", solides_monde)

# ------------------------------------------------------------------ soleil, ambiance, apparitions, cubemaps
soleil = bpy.data.objects.get("PORT_Soleil")
d = (soleil.matrix_world.to_3x3() @ Vector((0, 0, -1))) if soleil else Vector((0.5, 0.5, -0.5))
lacet = math.degrees(math.atan2(d.y, d.x))
entite("light_environment", P(Vector((60, 45, 20))), angles="-38 %.1f 0" % lacet, pitch="-38",
       _light="255 222 190 450", _ambient="135 145 165 150", _lightHDR="-1 -1 -1 1", _ambientHDR="-1 -1 -1 1", SunSpreadAngle="5")
entite("shadow_control", P(Vector((60, 45, 21))), angles="80 %.1f 0" % lacet, color="40 40 50", distance="120")
entite("env_fog_controller", P(Vector((60, 45, 22))), fogenable="1", fogcolor="150 140 135", fogcolor2="150 140 135",
       fogstart="3500", fogend="16000", fogmaxdensity="0.55", farz="-1", fogblend="0")
for k, (x, y) in enumerate(((104.5, 2), (102, 4), (107, 4), (104.5, 8), (60, 37), (30, 37), (90, 37), (56, 80))):
    entite("info_player_start", P(Vector((x, y, 0.2))), angles="0 90 0")
for x, y, z in ((104.5, -20, 2), (13, 13, 2), (37, 13, 2), (61, 13, 2), (85, 13, 2), (60, 37, 2), (33, 54, 2), (90, 54, 2),
                (7, 55, 2), (56, 82, 2), (84, 80, 1.6), (25, 81, 19), (116, 27, 2)):
    entite("env_cubemap", P(Vector((x, y, z))))
if "SHI_Place" in bpy.data.objects:                                 # Shibuya : apparitions sur la place, reflets dans la ville
    for k in range(8):
        a_ = k * math.pi / 4
        entite("info_player_start", P(Vector((104 + 26 * math.cos(a_), -145 + 26 * math.sin(a_), -2.6))), angles="0 %d 0" % ((k * 45 + 180) % 360))
    for x, y, z in ((104, -145, -1), (104, -60, 2), (45, -140, 2), (30, -118, 1.5), (25, -182, 1.5), (-45, -110, 2), (235, -235, 5),
                    (270, -70, 2), (180.5, -180, -3.5), (200, -150, 2), (0, -230, 9), (150, -250, 2), (-80, -60, 2), (280, -150, 2)):
        entite("env_cubemap", P(Vector((x, y, z))))

# ------------------------------------------------------------------ écriture
monde = ('world\n{\n\t"id" "1"\n\t"mapversion" "1"\n\t"classname" "worldspawn"\n\t"skyname" "sky_day01_01"\n'
         '\t"maxpropscreenwidth" "-1"\n\t"detailvbsp" "detail.vbsp"\n\t"detailmaterial" "detail/detailsprites"\n'
         + "".join(solides_monde) + "}\n")
detail = 'entity\n{\n\t"id" "%d"\n\t"classname" "func_detail"\n%s}\n' % (nid(), "".join(solides_detail))
vmf = ('versioninfo\n{\n\t"editorversion" "400"\n\t"editorbuild" "8000"\n\t"mapversion" "1"\n\t"formatversion" "100"\n\t"prefab" "0"\n}\n'
       'visgroups\n{\n}\nviewsettings\n{\n\t"bSnapToGrid" "1"\n\t"bShowGrid" "1"\n\t"nGridSpacing" "64"\n}\n'
       + monde + detail + "".join(entites) + 'cameras\n{\n\t"activecamera" "-1"\n}\ncordon\n{\n\t"mins" "(-1024 -1024 -1024)"\n'
       '\t"maxs" "(1024 1024 1024)"\n\t"active" "0"\n}\n')
open(SORTIE, "w", encoding="utf-8").write(vmf)
print("EXPORT GMOD : %d brosses de structure, %d brosses de détail, %d props, %d lumières, %d ignorés, %d non convexes -> %s"
      % (stats["brosses"], stats["detail"], stats["props"], stats["lumieres"], stats["ignores"], len(stats["non_convexes"]), SORTIE))
print("NON CONVEXES :", ", ".join(n for n in stats["non_convexes"] if "Decal" not in n))

#!/usr/bin/env python3
"""
Minolta XL-401 x iPhone 16 Pro - parametric printable camera body.

A proportional homage to the Minolta XL-401 Super 8 camera, with the film
cartridge chamber replaced by a cradle for an iPhone 16 Pro. The phone stands
portrait with its screen facing the operator (it becomes the monitor) and its
rear cameras facing forward through the lens board.

Run headless with Blender-as-a-module:   python3 build_xl401.py
Or inside Blender:                       blender -b -P build_xl401.py

Everything dimensional lives in PARAMS below. Change a number, re-run, get a
new set of STLs.

Coordinate system, all units in millimetres:
    +X  operator's right, standing behind the camera
    +Y  forward, the direction the lens points
    +Z  up.  Z = 0 is the bottom of the grip.
"""

import math
import os
import sys
import zipfile
from datetime import datetime, timezone

import bpy
import bmesh
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------
# Measured references:
#   Minolta XL-400 (the XL-401's near-identical predecessor): 48 x 103 x 184 mm,
#   650 g, Rokkor 8.5-34mm f/1.2. The iPhone 16 Pro is 71.5 mm wide - wider than
#   that entire camera body - so the mid-section here is deliberately stretched.
#   This is an homage in the XL-401's design language, not a scale replica.

P = {
    # ---- iPhone 16 Pro -----------------------------------------------------
    "phone_w":            71.5,
    "phone_h":           149.6,
    "phone_t":             8.25,
    "phone_corner_r":     11.0,
    # The plateau is 11 mm off the phone's centreline, so the lens is off the
    # body's by the same amount however the phone is placed. Keeping the phone
    # centred leaves 5 mm of clearance around the barrel and - more usefully -
    # keeps the cavity, tunnel, window, collar and eyecup all symmetric, so the
    # offset lens reads as the one deliberate asymmetry rather than a lean.
    "phone_dx":            0.0,
    # Rear camera plateau. Nominal figures - the aperture is deliberately
    # oversized so a few mm of error here changes nothing. Measure yours and
    # adjust if the fit gauge says otherwise.
    "plateau_w":          38.0,
    "plateau_h":          38.0,
    "plateau_z":           4.2,   # how far it protrudes from the back
    "plateau_inset_x":     6.8,   # from the phone's left edge, viewed from behind
    "plateau_inset_top":   6.8,   # from the phone's top edge
    "plateau_fillet":      9.0,

    # ---- fit ---------------------------------------------------------------
    # Flip the phone end-for-end. The plateau is 25.8 mm from one end of the
    # phone, so this is what decides whether the lens sits high in the body
    # (False, screen upright - the default) or low like a classic Super 8
    # cartridge camera (True, but the screen is then upside down and you need
    # an orientation-locking app such as Blackmagic Camera).
    "phone_inverted":  False,

    "case_t":              2.5,   # thickness a slim case adds
    "case_wh":             2.0,   # width/height a slim case adds
    "fit_clear":           0.35,  # clearance per side around the phone

    # ---- body --------------------------------------------------------------
    "wall":                2.6,
    "wall_boss":           3.2,
    "body_len":          145.0,   # front face to back face
    "body_w":             94.0,
    "body_bottom":        62.0,   # Z of the body's underside
    "body_top":          230.0,   # Z of the body's top
    "body_bevel":          3.0,
    "wedge_z":           150.0,   # lower front chamfer starts here...
    # Clamped in derive(): the wedge must never cut deeper than the front wall,
    # or it opens straight into the phone cavity.
    "wedge_cut":          26.0,   # ...and pulls the front face back this far

    # ---- lens --------------------------------------------------------------
    "lens_board_t":        6.0,   # bolt-on front plate thickness
    "aperture":           48.0,   # square opening in front of the plateau
    "aperture_r":          8.0,
    "aperture_chamfer":   30.0,   # degrees, flares outward
    "aperture_wall":       2.5,   # thin wall at the aperture = no vignetting
    "barrel_od":          67.0,
    "barrel_len":         52.0,
    "barrel_bore":        60.0,
    "spigot_od":          62.0,
    "spigot_id":          59.0,
    # The barrel mount is a groove cut INTO the board, not a ring standing proud
    # of it. A protruding ring is the closest solid to the phone's lenses and so
    # it, not the aperture, sets the clear cone: at 8 mm it held the usable cone
    # to 41 deg, at 4 mm to 55 deg, still short of the ultra-wide's 60. Recessed,
    # nothing stands forward of the board face and the aperture governs again.
    "spigot_len":          4.0,
    "spigot_clear":        0.25,

    # ---- grip --------------------------------------------------------------
    "grip_top":           62.0,
    "grip_len":           66.0,
    "grip_w":             46.0,
    # Forward of the body's midpoint: the phone's 199 g sits right at the front,
    # so a grip hung off the back would make the camera nose-heavy.
    "grip_y":            -64.0,   # centre of the grip in Y
    "grip_rake":           8.0,   # degrees, leaning back
    "grip_bevel":          8.0,
    "tripod_nut_af":      11.15,  # 1/4"-20 hex nut across flats
    "tripod_nut_t":        5.6,

    # ---- viewfinder --------------------------------------------------------
    # The phone sits hard against the front of the body, so its screen faces
    # back down the empty rear of the shell. That volume becomes a finder
    # tunnel: a big rear window frames the screen and shades it from sunlight.
    "tun_lip":             5.0,   # lip that traps the phone at the tunnel mouth
    "tun_crop_bottom":    22.0,   # extra crop low down, to leave floor for the tenon
    "tun_flare":           1.0,   # degrees; widens toward the eye
    "win_r":              10.0,
    "win_lip":             1.5,
    "hood_t":              6.0,   # raised collar around the window
    "hood_border":         8.0,
    # footage-counter dial recessed into the top deck
    "finder_od":          30.0,
    "finder_y":         -112.0,

    # ---- grip tenon (captured between the two body halves) -----------------
    "tenon_w":            30.0,
    "tenon_lip":          42.0,
    "tenon_len":          44.0,
    "tenon_h":            16.0,

    # ---- assembly ----------------------------------------------------------
    # The shell seam. Not on the centreline: a centre split puts 47 mm of solid
    # deck between the outer face and the joint, which would need 55 mm screws.
    # Offset, the smaller piece is a 17 mm service panel and M3x25 does it.
    "split_x":            30.0,

    "dowel_d":             3.0,
    "dowel_clear":         0.2,
    "screw_d":             3.4,   # M3 clearance
    "pilot_d":             2.5,   # self-tapping pilot; open out to insert_d for inserts
    "insert_d":            4.2,   # M3 heat-set insert
    "insert_len":          6.0,
    "boss_od":             8.0,

    # ---- print -------------------------------------------------------------
    "bed":              (256.0, 256.0, 256.0),
    "efoot_chamfer":       0.6,
    "shims":            (0.8, 1.6, 3.2),
}

# ---- derived ---------------------------------------------------------------
D = {}


def derive():
    """Everything computed from PARAMS. Kept separate so PARAMS stays readable."""
    D["cav_w"] = P["phone_w"] + P["case_wh"] + 2 * P["fit_clear"]
    D["cav_h"] = P["phone_h"] + P["case_wh"] + 2 * P["fit_clear"]
    D["cav_d"] = P["phone_t"] + P["case_t"] + 2 * P["fit_clear"]

    # The cavity sits hard against the front of the body. Y = 0 is the body's
    # front face; the lens board bolts on in front of that.
    D["cav_y1"] = -P["lens_board_t"] - P["plateau_z"] - 1.0    # front of cavity
    D["cav_y0"] = D["cav_y1"] - D["cav_d"]                     # back of cavity

    # Referenced to the body floor, not centred: the plateau sits near the top
    # of the phone, so every mm the cavity rises pushes the lens axis higher.
    # A 5 mm floor keeps the lens as low as the geometry allows.
    D["cav_z0"] = P["body_bottom"] + 5.0
    D["cav_z1"] = D["cav_z0"] + D["cav_h"]

    # Where the phone actually sits inside that cavity (centred, phone upright,
    # screen facing -Y). Viewed from the front we see the phone's back, and the
    # observer's left is +X, so the plateau ends up on the +X side.
    D["cav_cx"] = P["phone_dx"]
    px1 = D["cav_cx"] + D["cav_w"] / 2.0 - P["fit_clear"]   # phone's +X edge
    plat_x1 = px1 - P["plateau_inset_x"]
    D["plateau_cx"] = plat_x1 - P["plateau_w"] / 2.0

    if P["phone_inverted"]:
        pz0 = D["cav_z0"] + P["fit_clear"]           # phone's bottom edge
        D["plateau_cz"] = pz0 + P["plateau_inset_top"] + P["plateau_h"] / 2.0
    else:
        pz1 = D["cav_z1"] - P["fit_clear"]           # phone's top edge
        plat_z1 = pz1 - P["plateau_inset_top"]
        D["plateau_cz"] = plat_z1 - P["plateau_h"] / 2.0

    # Lens axis is concentric with the plateau.
    D["lens_cx"] = D["plateau_cx"]
    D["lens_cz"] = D["plateau_cz"]

    # Keep the wedge in front of the phone cavity, leaving `wall` of material.
    max_cut = (-D["cav_y1"]) - P["wall"]
    span = P["wedge_z"] - P["body_bottom"]
    D["wedge_cut"] = min(P["wedge_cut"], max_cut)
    D["wedge_slope"] = D["wedge_cut"] / span

    D["total_h"] = P["body_top"]
    # Finder tunnel: a lip all round traps the phone, cropped harder at the
    # bottom so the floor stays thick enough to capture the grip tenon.
    D["tun_w"] = D["cav_w"] - 2 * P["tun_lip"]
    tz0 = D["cav_z0"] + P["tun_crop_bottom"]
    tz1 = D["cav_z1"] - P["tun_lip"]
    D["tun_h"] = tz1 - tz0
    D["tun_cz"] = (tz0 + tz1) / 2.0
    grow = 2 * (P["body_len"] - P["wall"] + D["cav_y0"]) * math.tan(math.radians(P["tun_flare"]))
    # Inset from the tunnel's rear opening rather than matching it exactly:
    # coincident faces between the two cutters are a degenerate boolean, and it
    # leaves a clean lip framing the window.
    D["win_w"] = D["tun_w"] + grow - 2 * P["win_lip"]
    D["win_h"] = D["tun_h"] + grow - 2 * P["win_lip"]
    D["floor_top"] = D["tun_cz"] - D["win_h"] / 2.0   # lowest point of the tunnel
    D["deck_bot"] = D["tun_cz"] + D["win_h"] / 2.0    # highest point of the tunnel
    D["screen_cz"] = (D["cav_z0"] + D["cav_z1"]) / 2.0
    D["total_len"] = P["body_len"] + P["barrel_len"] + P["hood_t"]


derive()


# ---------------------------------------------------------------------------
# BLENDER HELPERS
# ---------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001      # 1 Blender unit == 1 mm
    sc.unit_settings.length_unit = "MILLIMETERS"


def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def activate(obj):
    try:
        bpy.ops.object.select_all(action="DESELECT")
    except RuntimeError:
        pass
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def mesh_from_bm(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def box(name, size, center=(0, 0, 0)):
    """Axis-aligned box given by (sx, sy, sz) and its centre."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return mesh_from_bm(name, bm)


def box_span(name, x0, x1, y0, y1, z0, z1):
    """Box given by its min/max on each axis - usually clearer than centre+size.

    Bounds are sorted, so a reversed pair gives a box rather than an inside-out
    one (which segfaults the exact boolean solver rather than failing politely).
    """
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return box(name, (x1 - x0, y1 - y0, z1 - z0),
               ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(name, r, h, center=(0, 0, 0), axis="Z", verts=64, r2=None):
    """Cylinder or truncated cone (r at -axis end, r2 at +axis end)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r, radius2=(r if r2 is None else r2), depth=h)
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Matrix.Rotation(math.radians(-90), 3, "X"))
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts,
                         matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return mesh_from_bm(name, bm)


def rounded_rect_prism(name, w, h, depth, r, center=(0, 0, 0), axis="Y", seg=8):
    """A rectangular prism with rounded corners in its cross-section.

    Used for the phone cavity, the aperture and the door - anything that wants a
    phone-like or camera-like rounded rectangle rather than a sharp box.
    """
    bm = bmesh.new()
    hw, hh = w / 2 - r, h / 2 - r
    pts = []
    for cx, cy, a0 in ((hw, hh, 0), (-hw, hh, 90), (-hw, -hh, 180), (hw, -hh, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # Drop duplicated corner-joins, including the wrap from the last arc back to
    # the first - a repeated vertex there makes a degenerate face that the
    # manifold solver rejects.
    uniq = []
    for q in pts:
        if not uniq or (abs(q[0] - uniq[-1][0]) > 1e-6 or abs(q[1] - uniq[-1][1]) > 1e-6):
            uniq.append(q)
    while len(uniq) > 3 and (abs(uniq[0][0] - uniq[-1][0]) < 1e-6
                             and abs(uniq[0][1] - uniq[-1][1]) < 1e-6):
        uniq.pop()
    vs = [bm.verts.new((x, -depth / 2, y)) for x, y in uniq]
    bm.faces.new(vs)
    bmesh.ops.translate(bm, vec=(0, 0, 0), verts=bm.verts)
    ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    nv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, depth, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_from_bm(name, bm)
    if axis == "Z":
        obj.rotation_euler = (math.radians(90), 0, 0)
    elif axis == "X":
        obj.rotation_euler = (0, 0, math.radians(90))
    obj.location = center
    bake(obj)
    return obj


def bake(obj):
    """Freeze an object's transform into its mesh data.

    Done directly on the mesh rather than via transform_apply: the operator
    walks the view layer's object list, and doing that right after a boolean
    has removed a tool object from it reads freed memory - which is where the
    intermittent segfaults were coming from.
    """
    # matrix_basis, not matrix_world: setting .location only refreshes
    # matrix_world on the next depsgraph evaluation, so reading it here would
    # silently bake an identity and leave the part sitting at the origin.
    obj.data.transform(obj.matrix_basis)
    obj.matrix_basis = Matrix.Identity(4)
    return obj


def modifier_apply(obj, mod):
    activate(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def bevel(obj, width, segments=3, angle=30.0):
    m = obj.modifiers.new("bev", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    m.miter_outer = "MITER_ARC"
    return modifier_apply(obj, m)


SOLVER = os.environ.get("XL401_SOLVER", "MANIFOLD3D")
BOOL_TRACE = bool(os.environ.get("XL401_TRACE"))
_bool_n = [0]


def mesh_arrays(obj, dtype_v="float64", dtype_f="int64"):
    """World-space vertices and triangles of an object.

    Triangulated through a throwaway bmesh. Reading mesh.loop_triangles instead
    is a trap: the cache survives a clear_geometry()/from_pydata() rebuild and
    then indexes a vertex array that no longer exists, which silently yields
    garbage geometry rather than an error.
    """
    import numpy as np
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    mw = obj.matrix_basis
    V = np.array([(mw @ v.co)[:] for v in bm.verts], dtype=dtype_v)
    F = np.array([[v.index for v in f.verts] for f in bm.faces], dtype=dtype_f)
    bm.free()
    return V, F


def _to_manifold(obj):
    """Blender object -> manifold3d solid, in world space.

    Triangulates through a throwaway bmesh rather than calc_loop_triangles().
    The latter populates a derived cache on the mesh datablock that the
    clear_geometry() in _from_manifold then pulls out from under it, which
    surfaces as a segfault somewhere later in the build.
    """
    from manifold3d import Manifold, Mesh
    V, F = mesh_arrays(obj, dtype_v="float32", dtype_f="uint32")
    man = Manifold(Mesh(vert_properties=V, tri_verts=F))
    if str(man.status()) not in ("Error.NoError", "NoError"):
        raise RuntimeError("%s is not a valid solid: %s" % (obj.name, man.status()))
    return man


def _from_manifold(obj, man):
    """Write a manifold3d solid back into an existing Blender object.

    Rewrites the existing mesh datablock in place. Swapping in a new one and
    freeing the old is a use-after-free here (Blender keeps derived caches
    pointing at it) and shows up as a nondeterministic segfault later on.
    """
    m = man.to_mesh()
    V = [tuple(float(c) for c in v[:3]) for v in m.vert_properties]
    F = [tuple(int(i) for i in f) for f in m.tri_verts]
    me = obj.data
    me.clear_geometry()
    me.from_pydata(V, [], F)
    me.update()
    obj.matrix_basis = Matrix.Identity(4)
    return obj


def boolean(target, tool, op="DIFFERENCE", keep_tool=False):
    """CSG via manifold3d.

    Blender's own EXACT and MANIFOLD solvers both segfault nondeterministically
    on this model in a headless bpy build, so the geometry kernel is manifold3d
    and Blender is left to do what it is good at here: authoring and rendering.
    Set XL401_SOLVER=EXACT or MANIFOLD to use Blender's instead.
    """
    if BOOL_TRACE:
        _bool_n[0] += 1
        print("  bool#%d %-9s %-14s <- %s" % (_bool_n[0], op, target.name, tool.name),
              flush=True)
    if SOLVER == "MANIFOLD3D":
        a, b = _to_manifold(target), _to_manifold(tool)
        r = {"DIFFERENCE": a - b, "UNION": a + b, "INTERSECT": a ^ b}[op]
        _from_manifold(target, r)
    else:
        m = target.modifiers.new("bool", "BOOLEAN")
        m.operation = op
        m.object = tool
        m.solver = SOLVER
        if SOLVER == "EXACT":
            m.use_self = True
        modifier_apply(target, m)
    if not keep_tool:
        tool_mesh = tool.data
        bpy.data.objects.remove(tool, do_unlink=True)
        if tool_mesh.users == 0:
            bpy.data.meshes.remove(tool_mesh)
    return target


def cut(target, *tools):
    for t in tools:
        boolean(target, t, "DIFFERENCE")
    return target


def fuse(target, *tools):
    for t in tools:
        boolean(target, t, "UNION")
    return target




def prism_x(name, pts_yz, x0, x1):
    """Extrude a 2-D polygon given in the (Y, Z) plane along X."""
    bm = bmesh.new()
    vs = [bm.verts.new((x0, y, z)) for y, z in pts_yz]
    bm.faces.new(vs)
    ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    nv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(x1 - x0, 0, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_from_bm(name, bm)


def ring_sector(name, r_in, r_out, y0, y1, a0, a1, verts=48):
    """Annular sector about the Y axis, from angle a0 to a1 (degrees)."""
    outer = cyl(name, r_out, y1 - y0, (0, (y0 + y1) / 2, 0), axis="Y", verts=verts)
    if r_in > 0:
        cut(outer, cyl("_i", r_in, (y1 - y0) * 3, (0, (y0 + y1) / 2, 0),
                       axis="Y", verts=verts))
    span = a1 - a0
    if span < 359:
        # wedge cutter: a fan of triangles covering the *kept* angular range
        bm = bmesh.new()
        R = r_out * 3
        base = [bm.verts.new((0, y0 - 1, 0)), ]
        pts = []
        n = max(2, int(span / 6) + 1)
        for i in range(n + 1):
            a = math.radians(a0 + span * i / n)
            pts.append(bm.verts.new((R * math.cos(a), y0 - 1, R * math.sin(a))))
        for i in range(n):
            bm.faces.new([base[0], pts[i], pts[i + 1]])
        ret = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        nv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, (y1 - y0) + 2, 0), verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        wedge = mesh_from_bm(name + "_w", bm)
        boolean(outer, wedge, "INTERSECT")
    return outer


def chamfered_window(name, w, h, r, y0, y1, angle, center_xz):
    """A rounded-rectangle opening that flares outward from y0 to y1.

    This is what stops the phone's lenses being vignetted: the narrow end sits
    just in front of the camera plateau and the walls fall away at `angle`.
    """
    # Sign of `angle` decides flare vs taper; the direction of travel from y0 to
    # y1 must not. Without the abs() a rear-to-front span silently inverts, and
    # the mismatch against the derived opening size crashes the exact solver.
    depth = abs(y1 - y0)
    grow = 2.0 * depth * math.tan(math.radians(angle))
    cx, cz = center_xz
    bm = bmesh.new()

    def loop(ww, hh, rr, y):
        hw, hh2 = ww / 2 - rr, hh / 2 - rr
        out = []
        for ccx, ccy, a0 in ((hw, hh2, 0), (-hw, hh2, 90), (-hw, -hh2, 180), (hw, -hh2, 270)):
            for i in range(9):
                a = math.radians(a0 + 90 * i / 8)
                out.append(bm.verts.new((cx + ccx + rr * math.cos(a), y,
                                         cz + ccy + rr * math.sin(a))))
        return out

    a = loop(w, h, r, y0)
    b = loop(w + grow, h + grow, r + grow / 2, y1)
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new([a[i], a[j], b[j], b[i]])
        except ValueError:
            pass
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_from_bm(name, bm)


def union_all(name, objs):
    """Boolean-union a list into one solid. Use when the pieces overlap;
    merge() only concatenates, which leaves a self-intersecting mesh that the
    manifold solver refuses."""
    first = objs[0]
    for o in objs[1:]:
        boolean(first, o, "UNION")
    first.name = name
    return first


def merge(name, objs):
    """Concatenate several *disjoint* objects into one - a single boolean beats
    a dozen. Overlapping pieces need union_all instead."""
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    return mesh_from_bm(name, bm)


# ---------------------------------------------------------------------------
# PARTS
# ---------------------------------------------------------------------------

def build_body():
    """The camera shell, before it is split into left and right halves."""
    bw, bl = P["body_w"], P["body_len"]
    z0, z1 = P["body_bottom"], P["body_top"]
    hx = bw / 2

    b = box_span("body", -hx, hx, -bl, 0, z0, z1)
    bevel(b, P["body_bevel"], 3)

    # ---- lower-front wedge: pulls mass out from under the high-set lens -----
    wz = P["wedge_z"]
    slope = D["wedge_slope"]
    y_at_low = -(wz - (z0 - 20)) * slope
    cut(b, prism_x("wedge", [(2, wz), (80, wz), (80, z0 - 20), (y_at_low, z0 - 20)],
                   -hx - 5, hx + 5))

    # ---- phone cavity ------------------------------------------------------
    cav = rounded_rect_prism("cav", D["cav_w"], D["cav_h"], D["cav_d"],
                             P["phone_corner_r"],
                             center=(D["cav_cx"], (D["cav_y0"] + D["cav_y1"]) / 2, (D["cav_z0"] + D["cav_z1"]) / 2),
                             axis="Y")
    # ---- pocket for the protruding camera plateau --------------------------
    pw = P["plateau_w"] + 12.0
    pocket = rounded_rect_prism("pock", pw, pw, P["plateau_z"] + 1.2 + 0.6,
                                P["plateau_fillet"],
                                center=(D["plateau_cx"],
                                        D["cav_y1"] + (P["plateau_z"] + 1.2) / 2 - 0.3,
                                        D["plateau_cz"]),
                                axis="Y")
    cut(b, cav, pocket)

    # ---- finder tunnel -----------------------------------------------------
    # The phone sits at the very front, so the whole rear of the shell is empty.
    # Rather than waste it, it becomes a finder: a tapered tunnel that frames
    # the screen and shades it. The narrow end is a lip that traps the phone;
    # it is cropped harder at the bottom so there is solid floor left for the
    # grip tenon, and because a landscape-locked camera app puts its image in
    # the middle of the screen anyway.
    tunnel = chamfered_window("tun", D["tun_w"], D["tun_h"], 12.0,
                              D["cav_y0"], -bl + P["wall"], P["tun_flare"],
                              (D["cav_cx"], D["tun_cz"]))
    window = rounded_rect_prism("win", D["win_w"], D["win_h"], P["wall"] * 4,
                                P["win_r"],
                                center=(D["cav_cx"], -bl + P["wall"], D["tun_cz"]),
                                axis="Y")
    cut(b, tunnel, window)

    # ---- raised hood collar around the rear window -------------------------
    hb, ht = P["hood_border"], P["hood_t"]
    collar = rounded_rect_prism("col", D["win_w"] + 2 * hb, D["win_h"] + 2 * hb, ht,
                                P["win_r"] + hb,
                                center=(D["cav_cx"], -bl - ht / 2, D["tun_cz"]), axis="Y")
    cut(collar, rounded_rect_prism("colb", D["win_w"], D["win_h"], ht * 3, P["win_r"],
                                   center=(D["cav_cx"], -bl - ht / 2, D["tun_cz"]), axis="Y"))
    fuse(b, collar)

    # ---- lens board rebate -------------------------------------------------
    lb = P["lens_board_t"]
    cut(b, box_span("reb", -42, 42, -lb, 1.0, 150, 226))

    # ---- raised bezel framing the lens board -------------------------------
    bez = box_span("bez", -45, 45, 0, 3.0, 146, 230)
    bevel(bez, 1.2, 2)
    fuse(b, bez)
    cut(b, box_span("bez_win", -42, 42, -1, 4.0, 150, 226))

    # ---- pilot holes for the film door -------------------------------------
    cut(b, merge("door_pilots", [
        cyl("dp%d" % i, P["pilot_d"] / 2, 9.0, (-hx + 2 + 4.5, y, z), axis="X", verts=16)
        for i, (y, z) in enumerate(DOOR_SCREWS)]))

    # ---- pilot holes for the lens board's retaining screws ------------------
    # Blind, into the 5.2 mm wall between the rebate and the phone cavity, and
    # deliberately short: 4 mm of thread leaves 1.2 mm of wall so a self-tapper
    # cannot break through onto the phone.
    cut(b, merge("lb_pilots", [
        cyl("lbp%d" % i, P["pilot_d"] / 2, 4.0,
            (x, -P["lens_board_t"] - 2.0, z), axis="Y", verts=16)
        for i, (x, z) in enumerate(BOARD_SCREWS)]))

    # ---- footage-counter dial on the top deck ------------------------------
    # An XL-401 signature detail, and unlike a protruding eyepiece it costs no
    # height: the rear window and its hood are already the finder.
    fo, fy = P["finder_od"], P["finder_y"]
    fuse(b, cyl("dial_bez", fo / 2 + 2.0, 1.6, (0, fy, z1 + 0.79), axis="Z", verts=48))
    cut(b, cyl("dial_rec", fo / 2, 2.4, (0, fy, z1 + 0.4), axis="Z", verts=48))

    # ---- grip tenon pocket, captured between the halves --------------------
    tw, tlip, tl, th = P["tenon_w"], P["tenon_lip"], P["tenon_len"], P["tenon_h"]
    gy = P["grip_y"]
    c = P["dowel_clear"]
    # Union the two boxes into one cutter first: cut separately they leave
    # coplanar faces on the shell, which segfaults the exact solver.
    tenon_void = box_span("tp1", -tw / 2 - c, tw / 2 + c, gy - tl / 2 - c, gy + tl / 2 + c,
                          z0 - 1, z0 + th + c)
    fuse(tenon_void, box_span("tp2", -tlip / 2 - c, tlip / 2 + c,
                              gy - tl / 2 - c, gy + tl / 2 + c,
                              z0 + th - 6 + c, z0 + th + c))
    cut(b, tenon_void)

    # ---- lightening pockets ------------------------------------------------
    # Cut from the split plane, so they face up on the bed and need no support.
    # Straight off ~25% of the filament, and they read as camera internals.
    # Cut one at a time and keep clear of the tilted eyepiece bore - overlapping
    # a merged multi-box tool with that cone is what the exact solver chokes on.
    px = 26.0
    ft, db = D["floor_top"] - 3, D["deck_bot"] + 3
    cut(b, box_span("lp1", -px, px, -26, -38, z0 + 3, ft))
    cut(b, box_span("lp2", -px, px, -90, -bl + 8, z0 + 3, ft))
    cut(b, box_span("lp3", -px, px, -26, -100, db, z1 - 3))
    cut(b, box_span("lp4", -px, px, -124, -bl + 8, db, z1 - 3))
    # Side walls either side of the finder tunnel, hollowed from the seam face.
    cut(b, box_span("sp_r", 38, 44, -40, -138, 72, 222))
    cut(b, box_span("sp_l", -44, -38, -40, -138, 72, 222))

    # ---- left-side film door opening ---------------------------------------
    dy0, dy1 = D["cav_y0"] - 1.5, D["cav_y1"] + 1.5
    dz0, dz1 = D["cav_z0"] - 2.0, D["cav_z1"] + 2.0
    door_void = box_span("door_op", -hx - 2, D["cav_cx"] - D["cav_w"] / 2, dy0, dy1, dz0, dz1)
    # shallow rebate the door panel sits into, so it finishes flush
    fuse(door_void, box_span("door_reb", -hx - 2, -hx + 2.0,
                             dy0 - 9, dy1 + 9, dz0 - 7, dz1 + 7))
    cut(b, door_void)
    return b


# The two screws retaining the lens board, driven straight in through its face.
# They sit in the solid margin *below* the aperture: the aperture flares to
# x = +38 at the board face, so anything level with it on the +X side would break
# straight into the lens opening. (X, Z) pairs, bored along Y. Shared by the body
# and the board so the holes line up.
BOARD_SCREWS = [(-20.0, 158.0), (28.0, 158.0)]

# The four screws holding the film door on. (Y, Z) pairs, bored along X. Placed
# clear of the door opening, of the front wedge, of the lens rebate and of the
# side lightening pockets - all of which would otherwise leave a screw threading
# into empty space.
DOOR_SCREWS = [(-31.0, 90.0), (-31.0, 196.0), (-7.0, 90.0), (-7.0, 196.0)]

# Clamshell fasteners live where the shell is genuinely solid: the top deck and
# the floor. (Y, Z) pairs, bored along X.
SCREWS = [(-20, 224), (-80, 223), (-135, 223), (-60, 70), (-100, 70), (-138, 70)]
DOWELS = [(-45, 224), (-118, 224), (-45, 70), (-118, 70)]


def add_clamshell_features(b):
    """Screw and dowel bores, then split into left and right halves."""
    hx = P["body_w"] / 2
    sx = P["split_x"]
    # Fuse a solid boss at each fastener first. Without it a lightening pocket
    # can leave a screw threading into thin air, and the two are positioned
    # independently.
    bosses = [cyl("bs%d" % i, 5.0, hx - 21.5, ((21.5 + hx) / 2, y, z), axis="X", verts=24)
              for i, (y, z) in enumerate(SCREWS + DOWELS)]
    for bo in bosses:
        fuse(b, bo)
    tools = []
    for y, z in SCREWS:
        # clearance through the panel, pilot into the body, spotface outside
        tools.append(union_all("scr", [
            cyl("s1", P["screw_d"] / 2, 22, (38.0, y, z), axis="X", verts=20),
            cyl("s2", P["pilot_d"] / 2, 10, (25.5, y, z), axis="X", verts=20),
            cyl("s3", 6.5 / 2, 3.2, (hx - 1.4, y, z), axis="X", verts=20)]))
    for y, z in DOWELS:
        tools.append(cyl("d1", (P["dowel_d"] + P["dowel_clear"]) / 2, 18,
                         (sx, y, z), axis="X", verts=20))
    cut(b, merge("fastener_tools", tools))
    return b


def split_body(b):
    hx, sx = P["body_w"] / 2, P["split_x"]
    body = b
    panel = body.copy()
    panel.data = body.data.copy()
    link(panel)
    body.name, panel.name = "01_body_main", "02_body_panel"
    cut(body, box_span("cutP", sx, hx + 20, -400, 400, -100, 400))
    cut(panel, box_span("cutB", -hx - 20, sx, -400, 400, -100, 400))
    return body, panel


def build_grip():
    z0, z1 = 0.0, P["grip_top"]
    gy, gl, gw = P["grip_y"], P["grip_len"], P["grip_w"]
    rake = math.tan(math.radians(P["grip_rake"])) * z1
    g = prism_x("03_grip", [(gy + gl / 2, z1), (gy + gl / 2 - rake, z0),
                            (gy - gl / 2 - rake, z0), (gy - gl / 2, z1)],
                -gw / 2, gw / 2)
    bevel(g, P["grip_bevel"], 4)

    # T-tenon, trapped when the two shells close around it
    tw, tlip, tl, th = P["tenon_w"], P["tenon_lip"], P["tenon_len"], P["tenon_h"]
    fuse(g,
         box_span("t1", -tw / 2, tw / 2, gy - tl / 2, gy + tl / 2, z1 - 2, z1 + th - 6),
         box_span("t2", -tlip / 2, tlip / 2, gy - tl / 2, gy + tl / 2, z1 + th - 6, z1 + th))

    # finger grooves on the front face
    grooves = [cyl("gr%d" % i, 8.0, gw + 6, (0, gy + gl / 2 - rake * (1 - zz / z1) + 5.0, zz),
                   axis="X", verts=32)
               for i, zz in enumerate((14.0, 31.0, 48.0))]
    cut(g, merge("grooves", grooves))

    # 1/4"-20 tripod nut trap, opening downward so it prints without support
    af = P["tripod_nut_af"]
    hexr = af / (2 * math.cos(math.radians(30)))
    trap = cyl("trap", hexr, P["tripod_nut_t"], (0, gy - rake / 2, P["tripod_nut_t"] / 2 - 0.01),
               axis="Z", verts=6)
    shaft = cyl("shaft", 7.0 / 2, 30, (0, gy - rake / 2, 15), axis="Z", verts=24)
    cut(g, trap, shaft)
    return g


def build_lens_board():
    t = P["lens_board_t"]
    # 0.3 mm smaller than its rebate all round. Cut to the rebate exactly it
    # would neither drop in on a real print nor render without z-fighting.
    c = P["fit_clear"]
    bd = box_span("04_lens_board", -42 + c, 42 - c, -t, 0, 150 + c, 226 - c)
    bevel(bd, 1.5, 2)
    # Aperture: narrow end toward the phone, falling away at `aperture_chamfer`
    # so nothing clips the ultra-wide's cone.
    cut(bd, chamfered_window("ap", P["aperture"], P["aperture"], P["aperture_r"],
                             -t - 0.5, 0.01, P["aperture_chamfer"],
                             (D["lens_cx"], D["lens_cz"])))
    # Annular groove the barrel's spigot drops into - recessed, so the board's
    # front face stays flat and nothing intrudes on the lenses' cone.
    gr = ring_sector("groove", P["spigot_id"] / 2, P["spigot_od"] / 2,
                     -P["spigot_len"], 0.01, 0, 360)
    gr.location = (D["lens_cx"], 0, D["lens_cz"])
    bake(gr)
    cut(bd, gr)
    # retaining screws, straight through the face into the body behind
    holes = []
    for i, (x, z) in enumerate(BOARD_SCREWS):
        holes.append(union_all("lh%d" % i, [
            cyl("lha", P["screw_d"] / 2, t + 2, (x, -t / 2, z), axis="Y", verts=16),
            cyl("lhb", 6.2 / 2, 2.2, (x, -1.0, z), axis="Y", verts=16)]))
    cut(bd, merge("lholes", holes))
    # photocell window + badge recess, on the quiet side of the lens
    cut(bd, cyl("cds", 6.0, 3.0, (-31, -1.4, 172), axis="Y", verts=32),
        box_span("badge", -38, -20, -1.2, 0.5, 156, 164))
    return bd


def build_barrel():
    od, bore, L = P["barrel_od"], P["barrel_bore"], P["barrel_len"]
    cx, cz = D["lens_cx"], D["lens_cz"]
    b = cyl("05_lens_barrel", od / 2, L, (cx, L / 2, cz), axis="Y", verts=96)
    # Male spigot on the rear, dropping back into the board's groove.
    c = P["spigot_clear"]
    sl = P["spigot_len"] - 0.3
    sp = ring_sector("spig", (P["spigot_id"] + c) / 2, (P["spigot_od"] - c) / 2,
                     -sl, 0.01, 0, 360)
    sp.location = (cx, 0, cz)
    bake(sp)
    fuse(b, sp)
    cut(b, cyl("bore", bore / 2, L + 12, (cx, (L - 6) / 2 + 3, cz), axis="Y", verts=96))
    # turned grooves and a fluted zoom band - the XL-401's lens is all rings
    rings = [ring_sector("rg%d" % i, od / 2 - 1.6, od / 2 + 1, y, y + 2.4, 0, 360)
             for i, y in enumerate((16.0, 19.5, 40.0))]
    for r in rings:
        r.location = (cx, 0, cz)
        bake(r)
    cut(b, merge("rings", rings))
    flutes = []
    for i in range(44):
        a = math.radians(360 * i / 44)
        r = od / 2 + 0.25
        flutes.append(cyl("fl%d" % i, 1.1, 14.0,
                          (cx + r * math.cos(a), 30.0, cz + r * math.sin(a)),
                          axis="Y", verts=8))
    cut(b, merge("flutes", flutes))
    return b


def build_lens_ring():
    """Contrast-colour bezel that presses into the front of the barrel."""
    od, bore = P["barrel_od"], P["barrel_bore"]
    cx, cz, L = D["lens_cx"], D["lens_cz"], P["barrel_len"]
    r = ring_sector("06_lens_ring", bore / 2 - 4.0, od / 2 - 0.4, 0, 4.0, 0, 360)
    r.location = (cx, L - 4.0, cz)
    bake(r)
    lip = ring_sector("lip", bore / 2 - 4.0, bore / 2 - 0.25, 0, 3.0, 0, 360)
    lip.location = (cx, L - 7.0, cz)
    bake(lip)
    fuse(r, lip)
    return r


def build_door():
    """Left-hand 'film door'. The phone loads through it, edge on."""
    hx = P["body_w"] / 2
    c = 0.25
    dy0, dy1 = D["cav_y0"] - 1.5 + c, D["cav_y1"] + 1.5 - c
    dz0, dz1 = D["cav_z0"] - 2.0 + c, D["cav_z1"] + 2.0 - c
    x_in = D["cav_cx"] - D["cav_w"] / 2
    plug = box_span("07_phone_door", x_in, -hx + 2.0, dy0, dy1, dz0, dz1)
    flange = box_span("fl", -hx + 2.0, -hx + 0.05,
                      dy0 - 9 + c, dy1 + 9 - c, dz0 - 7 + c, dz1 + 7 - c)
    bevel(flange, 2.0, 3)
    fuse(plug, flange)
    holes = []
    for i, (y, z) in enumerate(DOOR_SCREWS):
        holes.append(union_all("dhole%d" % i, [
            cyl("dh", P["screw_d"] / 2, 14, (-hx + 5, y, z), axis="X", verts=16),
            cyl("dc", 6.2 / 2, 2.4, (-hx + 1.15, y, z), axis="X", verts=16)]))
    cut(plug, merge("dholes", holes))
    return plug


def build_eyecup():
    """Soft hood that pushes over the collar around the rear window. Print TPU."""
    hb, ht = P["hood_border"], P["hood_t"]
    w, h = D["win_w"] + 2 * hb, D["win_h"] + 2 * hb
    bl = P["body_len"]
    wall, L = 3.0, 24.0
    outer = chamfered_window("eo", w + 2 * wall + 0.6, h + 2 * wall + 0.6, P["win_r"] + hb,
                             -bl - ht, -bl - ht - L, 7.0, (D["cav_cx"], D["tun_cz"]))
    inner = chamfered_window("ei", w + 0.6, h + 0.6, P["win_r"] + hb,
                             -bl - ht + 1, -bl - ht - L - 1, 7.0, (D["cav_cx"], D["tun_cz"]))
    cut(outer, inner)
    outer.name = "08_eyecup"
    return outer


def build_trigger():
    t = box_span("09_trigger", -5, 5, -2, 12, -7, 7)
    bevel(t, 2.0, 3)
    fuse(t, cyl("pin", 2.4 / 2, 22, (0, 0, 0), axis="X", verts=16))
    t.rotation_euler = (0, math.radians(P["grip_rake"]), 0)
    t.location = (0, P["grip_y"] + P["grip_len"] / 2 - 2.0, 42.0)
    return bake(t)


def shim_name(i, t):
    """Part name for a shim. Used by both the builder and the notes table, which
    otherwise drift apart and silently lose the notes."""
    return "1%d_shim_%s" % (i, str(t).replace(".", "p"))


def shim_home(t, back_off):
    """Where a shim sits in the assembly: stacked behind the phone."""
    return (D["cav_cx"], D["cav_y0"] + t / 2 + back_off, (D["cav_z0"] + D["cav_z1"]) / 2)


def build_shims():
    """Frames, not plates - they take up slack behind the phone without
    covering the screen. Stack to suit a bare phone or any case."""
    out = []
    b = 9.0
    for i, t in enumerate(P["shims"]):
        w, h = D["cav_w"] - 0.5, D["cav_h"] - 0.5
        name = shim_name(i, t)
        c = shim_home(t, 0.0)
        f = rounded_rect_prism(name, w, h, t, P["phone_corner_r"], center=c, axis="Y")
        cut(f, rounded_rect_prism("in", w - 2 * b, h - 2 * b, t * 3,
                                  max(1.0, P["phone_corner_r"] - b), center=c, axis="Y"))
        out.append(f)
    return out


def build_phone(name="phone", gauge=False):
    """iPhone 16 Pro stand-in. Printed as a fit gauge; also used for renders."""
    w = P["phone_w"] + (P["case_wh"] if gauge else 0.0)
    h = P["phone_h"] + (P["case_wh"] if gauge else 0.0)
    t = P["phone_t"] + (P["case_t"] if gauge else 0.0)
    body = rounded_rect_prism(name, w, h, t, P["phone_corner_r"],
                              center=(0, 0, 0), axis="Y")
    bevel(body, 1.0, 2, angle=50)
    px1 = w / 2 - (P["case_wh"] / 2 if gauge else 0.0)
    pz1 = h / 2 - (P["case_wh"] / 2 if gauge else 0.0)
    cx = px1 - P["plateau_inset_x"] - P["plateau_w"] / 2
    cz = pz1 - P["plateau_inset_top"] - P["plateau_h"] / 2
    plat = rounded_rect_prism("plat", P["plateau_w"], P["plateau_h"], P["plateau_z"] * 2,
                              P["plateau_fillet"], center=(cx, 0, cz), axis="Y")
    plat.location = (0, t / 2, 0)
    bake(plat)
    fuse(body, plat)
    return body


# ---------------------------------------------------------------------------
# ASSEMBLY
# ---------------------------------------------------------------------------

# How each part is rotated to sit on the bed. (rx, ry, rz) in degrees.
PRINT_ORIENT = {
    "01_body_main": (0, -90, 0),      # rests on its outer face, voids opening up
    "02_body_panel": (0, 90, 0),
    "03_grip": (0, 0, 0),
    "04_lens_board": (-90, 0, 0),
    "05_lens_barrel": (90, 0, 0),
    "06_lens_ring": (90, 0, 0),
    "07_phone_door": (0, 90, 0),
    "08_eyecup": (-90, 0, 0),
    "09_trigger": (0, 90, 0),
    "13_phone_gauge": (-90, 0, 0),
}

NOTES = {
    "01_body_main": "Outer face down, seam up. Longest print.",
    "02_body_panel": "Outer face down. Flat, quick.",
    "03_grip": "Stands on its base; tenon up. No supports.",
    "04_lens_board": "Aperture face up. No supports.",
    "05_lens_barrel": "Mouth down, concentric. No supports.",
    "06_lens_ring": "Contrast colour. No supports.",
    "07_phone_door": "Flange face down. No supports.",
    "08_eyecup": "TPU 95A if you have it, else PLA. No supports.",
    "09_trigger": "Contrast colour. Tiny - print alongside something else.",
    "13_phone_gauge": "Check the cavity fits before committing to the body print.",
}
for _i, _t in enumerate(P["shims"]):
    NOTES[shim_name(_i, _t)] = "Frame, not a plate - it presses on the bezel and "\
                               "leaves the screen clear. Flat, no supports."


def build_all():
    reset_scene()
    parts = {}

    body = build_body()
    add_clamshell_features(body)
    main_shell, panel = split_body(body)
    parts["01_body_main"] = main_shell
    parts["02_body_panel"] = panel
    parts["03_grip"] = build_grip()
    parts["04_lens_board"] = build_lens_board()
    parts["05_lens_barrel"] = build_barrel()
    parts["06_lens_ring"] = build_lens_ring()
    parts["07_phone_door"] = build_door()
    parts["08_eyecup"] = build_eyecup()
    parts["09_trigger"] = build_trigger()
    for i, sh in enumerate(build_shims()):
        parts[sh.name] = sh

    gauge = build_phone("13_phone_gauge", gauge=True)
    gauge.location = (0, 0, 0)
    bake(gauge)
    parts["13_phone_gauge"] = gauge
    return parts


def place_phone():
    """The phone where it actually sits, for renders and the fit check."""
    ph = build_phone("phone_fitted", gauge=False)
    ph.location = (D["cav_cx"],
                   D["cav_y1"] - P["fit_clear"] - P["phone_t"] / 2 - P["case_t"] / 2,
                   (D["cav_z0"] + D["cav_z1"]) / 2)
    return bake(ph)


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def to_trimesh(obj):
    import trimesh
    V, F = mesh_arrays(obj)
    return trimesh.Trimesh(V, F, process=False)


def oriented_for_print(obj):
    """Copy, rotate to its print orientation, and drop onto Z = 0."""
    import numpy as np
    m = to_trimesh(obj)
    rx, ry, rz = PRINT_ORIENT.get(obj.name, (0, 0, 0))
    for axis, ang in ((( 1, 0, 0), rx), ((0, 1, 0), ry), ((0, 0, 1), rz)):
        if ang:
            import trimesh
            m.apply_transform(trimesh.transformations.rotation_matrix(
                math.radians(ang), axis))
    lo = m.bounds[0]
    m.apply_translation([-lo[0], -lo[1], -lo[2]])
    return m


def write_3mf(path, meshes):
    """Minimal but valid 3MF: a zip of XML, with millimetres declared."""
    model = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
             '<metadata name="Application">build_xl401.py</metadata>',
             '<resources>']
    build = ['<build>']
    for i, (name, m) in enumerate(meshes, start=1):
        model.append('<object id="%d" type="model" name="%s"><mesh><vertices>' % (i, name))
        model += ['<vertex x="%.4f" y="%.4f" z="%.4f"/>' % tuple(v) for v in m.vertices]
        model.append('</vertices><triangles>')
        model += ['<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in m.faces]
        model.append('</triangles></mesh></object>')
        build.append('<item objectid="%d"/>' % i)
    build.append('</build>')
    model.append('</resources>')
    model += build
    model.append('</model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
          'relationships+xml"/><Default Extension="model" ContentType="application/vnd.'
          'ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.'
            'microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", "\n".join(model))


# ---------------------------------------------------------------------------
# RENDERING
# ---------------------------------------------------------------------------

def mat(name, base, rough=0.5, metal=0.0, emit=None, emit_strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def setup_world(strength=1.0):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.055, 0.065, 1.0)
    bg.inputs[1].default_value = strength
    return w


def add_light(name, loc, energy, size=200.0, target=(0, -70, 140)):
    d = bpy.data.lights.new(name, type="AREA")
    d.energy = energy
    d.size = size
    o = bpy.data.objects.new(name, d)
    link(o)
    o.location = loc
    direction = Vector(target) - Vector(loc)
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return o


def add_camera(loc, target, lens=85.0):
    c = bpy.data.cameras.new("Cam")
    c.lens = lens
    # Explicit: modelling in millimetres puts the camera ~2 m out for a wide
    # exploded layout, well past the default clip end, which renders empty.
    c.clip_start = 1.0
    c.clip_end = 50000.0
    o = bpy.data.objects.new("Cam", c)
    link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def render(path, res=(1600, 1200), samples=96):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def scene_bounds(objs):
    import numpy as np
    pts = []
    for o in objs:
        if o.type != "MESH" or o.hide_render:
            continue
        # matrix_basis, not matrix_world - the latter is stale until the
        # depsgraph runs, so an exploded layout would frame as if un-exploded.
        mw = o.matrix_basis
        pts += [(mw @ v.co)[:] for v in o.data.vertices]
    a = np.array(pts)
    return a.min(axis=0), a.max(axis=0)


def frame(objs, direction, lens=80.0, margin=1.14, up_shift=0.0):
    """Point the camera along `direction` and fit the subject to the frame.

    Works in camera space: the subject's bounding box is projected onto the
    camera's right/up/forward axes, the camera aims at the centre of that
    projection, and the distance comes from its width and height. Fitting the
    world-space bbox instead leaves an exploded layout small and pushed into one
    corner, because neither its diagonal nor its centre says anything about how
    it actually lands in frame.
    """
    import numpy as np
    sc = bpy.context.scene
    aspect = sc.render.resolution_x / sc.render.resolution_y
    lo, hi = scene_bounds(objs)
    ctr = Vector(((lo + hi) / 2).tolist())
    corners = [Vector((x, y, z))
               for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]

    d = Vector(direction).normalized()
    fwd = -d                                   # the camera looks back along -d
    right = fwd.cross(Vector((0, 0, 1)))
    right = right.normalized() if right.length > 1e-6 else Vector((1, 0, 0))
    up = right.cross(fwd).normalized()

    rs = [(c - ctr).dot(right) for c in corners]
    us = [(c - ctr).dot(up) for c in corners]
    fs = [(c - ctr).dot(fwd) for c in corners]
    target = ctr + right * ((min(rs) + max(rs)) / 2) + up * ((min(us) + max(us)) / 2)
    target.z += up_shift

    tan_v = 36.0 / (2 * lens)                  # vertical half-angle at the sensor
    tan_h = tan_v * aspect
    half_w = (max(rs) - min(rs)) / 2
    half_h = (max(us) - min(us)) / 2
    dist = max(half_w / tan_h, half_h / tan_v) * margin - min(fs)
    return add_camera(target + d * dist, target, lens=lens)


def build_scene(mode="display", with_phone=True):
    """Full assembly, materials and lighting. Returns the parts dict."""
    parts = build_all()
    parts["13_phone_gauge"].hide_render = True
    body_m = mat("body", (0.043, 0.043, 0.048), rough=0.44)
    trim_m = mat("trim", (0.63, 0.64, 0.67), rough=0.28, metal=1.0)
    soft_m = mat("soft", (0.028, 0.028, 0.030), rough=0.85)
    for n, o in parts.items():
        if n in ("06_lens_ring", "09_trigger"):
            assign(o, trim_m)
        elif n == "08_eyecup":
            assign(o, soft_m)
        else:
            assign(o, body_m)
    # Shims are alternatives, not a stack: show the one a bare phone needs.
    for n, o in parts.items():
        if n.endswith("shim_0p8") or n.endswith("shim_1p6"):
            o.hide_render = True
    if mode == "shooting":
        for n in ("05_lens_barrel", "06_lens_ring"):
            parts[n].hide_render = True
    # The panel and the shell share the plane X = split_x exactly, which
    # z-fights. Sink the panel slightly *into* the shell rather than pulling it
    # out: overlapping breaks the tie without opening a gap for light to leak
    # through, which a positive offset does very visibly.
    if "02_body_panel" in parts:
        parts["02_body_panel"].location.x -= 0.30
    if with_phone:
        ph = place_phone()
        assign(ph, mat("screen", (0.04, 0.05, 0.07), rough=0.22,
                       emit=(0.30, 0.50, 0.82), emit_strength=2.2))
        parts["phone"] = ph
    setup_world(0.85)
    add_light("key", (420, 330, 560), 380000, 340)
    add_light("fill", (-560, 240, 300), 170000, 420)
    add_light("rim", (-140, -560, 430), 240000, 320)
    g = box_span("ground", -1400, 1400, -1400, 1400, -8, 0)
    assign(g, mat("gnd", (0.085, 0.088, 0.095), rough=0.9))
    return parts


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

# Nominal positions of the three rear lenses within the plateau, and the half
# angle each needs kept clear. Diagonal FOVs: ultra-wide ~120 deg, main ~73 deg,
# 5x tele ~23 deg.
LENSES = [
    ("ultra-wide 0.5x", (-9.5, -9.5), 60.0),
    ("main 1x",         (-9.5,  9.5), 36.5),
    ("tele 5x",         ( 9.5, -9.5), 11.5),
]

PLA_DENSITY = 1.24        # g/cm3
INFILL_EFFECTIVE = 0.34   # 20% infill + walls + top/bottom, as printed


def overhang_fraction(m, limit=45.0):
    """Share of surface area steeper than `limit` and facing downward."""
    import numpy as np
    n = m.face_normals
    a = m.area_faces
    down = n[:, 2] < -math.cos(math.radians(90 - limit))
    return float(a[down].sum() / a.sum()) if a.sum() else 0.0


def clear_half_angle(scene_mesh, origin, max_deg=75.0, rays=72):
    """Largest cone half-angle from `origin` that reaches open air.

    Cast against the real assembled geometry, so this measures what was
    modelled rather than what was intended.
    """
    import numpy as np
    lo, hi = 0.0, max_deg
    for _ in range(14):
        mid = (lo + hi) / 2
        t = math.radians(mid)
        ang = np.linspace(0, 2 * math.pi, rays, endpoint=False)
        d = np.stack([np.sin(t) * np.cos(ang),
                      np.full(rays, math.cos(t)),
                      np.sin(t) * np.sin(ang)], axis=1)
        o = np.repeat(np.array([origin]), rays, axis=0)
        if scene_mesh.ray.intersects_any(ray_origins=o, ray_directions=d).any():
            hi = mid
        else:
            lo = mid
    return lo


def validate(parts, verbose=True):
    """Every printability and fit claim in the README is generated here."""
    import numpy as np
    import trimesh
    rows, problems = [], []
    bed = P["bed"]
    total_vol = 0.0
    for name in sorted(parts):
        obj = parts[name]
        m = to_trimesh(obj)
        pm = oriented_for_print(obj)
        sz = pm.extents
        fits = all(sz[i] <= bed[i] for i in range(3))
        vol = m.volume / 1000.0                       # cm3
        mass = vol * INFILL_EFFECTIVE * PLA_DENSITY   # g
        ok = m.is_watertight and m.is_winding_consistent and m.volume > 0
        rows.append(dict(name=name, w=sz[0], d=sz[1], h=sz[2], vol=vol, mass=mass,
                         watertight=m.is_watertight, winding=m.is_winding_consistent,
                         euler=m.euler_number, fits=fits,
                         overhang=overhang_fraction(pm), note=NOTES.get(name, "")))
        total_vol += vol
        if not ok:
            problems.append("%s: mesh is not a closed solid" % name)
        if not fits:
            problems.append("%s: %.0f x %.0f x %.0f exceeds the %.0f mm bed"
                            % (name, sz[0], sz[1], sz[2], bed[0]))
    return rows, problems, total_vol


def check_fit(parts):
    """Does the phone actually go in, and how much room is left?"""
    import trimesh
    ph = place_phone()
    pm = to_trimesh(ph)
    shells = [to_trimesh(parts[n]) for n in ("01_body_main", "02_body_panel",
                                             "04_lens_board", "07_phone_door")]
    clash = 0.0
    for s in shells:
        try:
            inter = pm.intersection(s)
            clash += max(0.0, inter.volume) / 1000.0
        except Exception:
            pass
    bpy.data.objects.remove(ph, do_unlink=True)
    return dict(clash_cm3=clash,
                gap_x=D["cav_w"] - P["phone_w"],
                gap_y=D["cav_d"] - P["phone_t"],
                gap_z=D["cav_h"] - P["phone_h"])


def check_optics(parts):
    """Ray-cast the real geometry to see which lenses are unobstructed."""
    import numpy as np
    import trimesh
    glass_y = D["cav_y1"] - P["fit_clear"] + P["plateau_z"]
    out = {}
    for mode, names in (("shooting", ("01_body_main", "02_body_panel", "04_lens_board")),
                        ("display", ("01_body_main", "02_body_panel", "04_lens_board",
                                     "05_lens_barrel", "06_lens_ring"))):
        scene = trimesh.util.concatenate([to_trimesh(parts[n]) for n in names])
        res = []
        for label, (lx, lz), need in LENSES:
            origin = (D["lens_cx"] + lx, glass_y + 0.2, D["lens_cz"] + lz)
            got = clear_half_angle(scene, origin)
            res.append((label, need, got, got >= need))
        out[mode] = res
    return out


# ---------------------------------------------------------------------------
# DRIVER
# ---------------------------------------------------------------------------

VIEWS = {
    "hero_front":  dict(dir=(1.05, 0.95, 0.45), lens=80, mode="display"),
    "hero_rear":   dict(dir=(-0.75, -1.05, 0.42), lens=80, mode="display"),
    "shooting":    dict(dir=(0.55, 1.15, 0.22), lens=95, mode="shooting"),
    "profile":     dict(dir=(-1.0, 0.05, 0.14), lens=110, mode="display"),
}


def do_export(outdir):
    import trimesh
    parts = build_all()
    stl_dir = os.path.join(outdir, "stl")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(os.path.join(outdir, "3mf"), exist_ok=True)
    # Clear first: renaming or dropping a part would otherwise leave its old STL
    # sitting in the directory, indistinguishable from a current one.
    for f in os.listdir(stl_dir):
        if f.endswith(".stl"):
            os.remove(os.path.join(stl_dir, f))

    rows, problems, total = validate(parts)
    fit = check_fit(parts)
    optics = check_optics(parts)
    assembled = [parts[n] for n in parts if not n.startswith(("10_", "11_", "13_"))]
    lo, hi = scene_bounds(assembled)
    D["assembled"] = (hi[1] - lo[1], hi[2] - lo[2], hi[0] - lo[0])

    printable = []
    for name in sorted(parts):
        pm = oriented_for_print(parts[name])
        pm.export(os.path.join(outdir, "stl", name + ".stl"))
        printable.append((name, pm))
    write_3mf(os.path.join(outdir, "3mf", "xl401_all_parts.3mf"), printable)

    # assembled glTF for the web viewer, decimated so the page stays light
    ph = place_phone()
    assign(ph, mat("screen", (0.05, 0.06, 0.09), rough=0.2))
    for n in ("10_shim_0p8", "11_shim_1p6", "13_phone_gauge"):
        parts[n].hide_set(True)
        parts[n].hide_viewport = True
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and not o.hide_viewport:
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, "preview"),
                              export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, "xl401.blend"))
    return rows, problems, total, fit, optics


def do_render(outdir, view):
    cfg = VIEWS[view]
    parts = build_scene(mode=cfg["mode"])
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name != "ground" and not o.hide_render]
    frame(objs, cfg["dir"], lens=cfg["lens"], up_shift=6)
    os.makedirs(os.path.join(outdir, "renders"), exist_ok=True)
    render(os.path.join(outdir, "renders", view + ".png"),
           res=(int(os.environ.get("XL401_W", 1600)), int(os.environ.get("XL401_H", 1200))),
           samples=int(os.environ.get("XL401_SAMPLES", 96)))


def do_exploded(outdir):
    parts = build_scene(mode="display")
    # The phone and door come out to the left, the way they actually load; the
    # optical parts run forward along the axis; the grip drops out below.
    spread = {"06_lens_ring": (0, 185, 0), "05_lens_barrel": (0, 128, 0),
              "04_lens_board": (0, 62, 0), "02_body_panel": (125, 0, 0),
              "phone": (-150, 0, 0), "12_shim_3p2": (-150, 0, -105),
              "07_phone_door": (-235, 0, 0), "08_eyecup": (0, -110, 0),
              "03_grip": (0, 10, -135), "09_trigger": (0, 62, -135)}
    for n, off in spread.items():
        if n in parts:
            parts[n].location = Vector(parts[n].location) + Vector(off)
    # An exploded layout is ~3x the width of the assembly, so the lighting rig
    # built for the assembly falls off badly. Push the lights out and brighten
    # them to match, and drop the floor - a parts diagram does not need one.
    g = bpy.data.objects.get("ground")
    if g:
        bpy.data.objects.remove(g, do_unlink=True)
    for o in bpy.context.scene.objects:
        if o.type == "LIGHT":
            o.location = Vector(o.location) * 1.7
            o.data.energy *= 5.0
            o.data.size *= 2.0
    setup_world(1.5)
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name != "ground" and not o.hide_render]
    frame(objs, (0.78, 0.86, 0.30), lens=85, margin=1.10, up_shift=0)
    os.makedirs(os.path.join(outdir, "renders"), exist_ok=True)
    render(os.path.join(outdir, "renders", "exploded.png"),
           res=(int(os.environ.get("XL401_W", 1600)), int(os.environ.get("XL401_H", 1200))),
           samples=int(os.environ.get("XL401_SAMPLES", 96)))


# Short per-part blurbs for the web page's parts table.
PAGE_NOTES = {
    "01_body_main": "Outer face down, seam up. Longest print.",
    "02_body_panel": "Service panel. Flat and quick.",
    "03_grip": "Stands on its base, tenon up.",
    "04_lens_board": "Aperture face up.",
    "05_lens_barrel": "Mouth down, concentric.",
    "06_lens_ring": "Contrast colour.",
    "07_phone_door": "Flange face down.",
    "08_eyecup": "TPU 95A if you have it.",
    "09_trigger": "Tiny - print alongside something.",
    "10_shim_0p8": "Slim case (~2.5 mm).",
    "11_shim_1p6": "Thin case (~1.5 mm).",
    "12_shim_3p2": "Bare phone.",
    "13_phone_gauge": "Fit gauge. Print this first.",
}


def inject_page_data(outdir, rows, total, optics):
    """Write the measured numbers into index.html.

    The page used to carry hand-copied figures, which drift the moment a
    parameter changes. Everything between the markers is generated here, so the
    page can only ever show what was actually measured.
    """
    path = os.path.join(outdir, "index.html")
    if not os.path.exists(path):
        return
    html = open(path).read()

    spec = ('\n      <b>%.0f</b> \u00d7 <b>%.0f</b> \u00d7 <b>%.0f</b> mm &nbsp;\u00b7&nbsp;\n'
            '      <b>%d</b> printed parts &nbsp;\u00b7&nbsp;\n'
            '      <b>~%.0f g</b> PLA &nbsp;\u00b7&nbsp;\n'
            '      fits a <b>%.0f\u00b3</b> bed\n    ' %
            (D["assembled"][0], D["assembled"][1], D["assembled"][2],
             len(rows), sum(r["mass"] for r in rows), P["bed"][0]))

    def cell(mode, i):
        _lbl, _need, got, ok = optics[mode][i]
        return '<td class="num %s">%.1f\u00b0 %s</td>' % (
            "yes" if ok else "no", got, "clear" if ok else "vignettes")

    opt_rows = ["\n"]
    for i, (label, need, _g, _o) in enumerate(optics["shooting"]):
        pretty = label.replace("0.5x", "0.5\u00d7").replace("1x", "1\u00d7").replace("5x", "5\u00d7")
        opt_rows.append('      <tr><td>%s</td><td class="num">%.1f\u00b0</td>\n'
                        '          %s%s</tr>\n'
                        % (pretty[0].upper() + pretty[1:], need,
                           cell("display", i), cell("shooting", i)))
    opt_rows.append("    ")

    parts = ["\n"]
    for r in rows:
        parts.append("  ['%s', '%.0f \u00d7 %.0f \u00d7 %.0f', '%.0f g', '%.0f %%', '%s'],\n"
                     % (r["name"], r["w"], r["d"], r["h"], r["mass"],
                        100 * r["overhang"], PAGE_NOTES.get(r["name"], "")))

    for a, b, body in (("<!--specline-->", "<!--/specline-->", spec),
                       ("<!--optics-->", "<!--/optics-->", "".join(opt_rows)),
                       ("// parts-data-start", "// parts-data-end", "".join(parts))):
        i0 = html.index(a) + len(a)
        i1 = html.index(b)
        html = html[:i0] + body + html[i1:]
    with open(path, "w") as f:
        f.write(html)
    print("index.html: injected %d parts, optics and spec line" % len(rows))


def report(outdir, rows, problems, total, fit, optics):
    """Write VALIDATION.md and echo the same numbers to the terminal."""
    L = []
    L.append("# Validation report")
    L.append("")
    L.append("Generated by `build_xl401.py` on %s."
             % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    L.append("Every number here is measured off the exported meshes, not asserted.")
    L.append("")
    L.append("## Overall")
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append("| Assembled size | %.0f L x %.0f H x %.0f W mm |" % D["assembled"])
    L.append("| Parts | %d |" % len(rows))
    L.append("| Solid volume | %.0f cm3 |" % total)
    L.append("| Estimated PLA | %.0f g at 20%% infill |"
             % sum(r["mass"] for r in rows))
    L.append("| Bed | %.0f x %.0f x %.0f mm |" % P["bed"])
    L.append("")
    L.append("## Parts")
    L.append("")
    L.append("| Part | Print size (mm) | Solid | PLA | Closed | Fits bed | Overhang | Orientation |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append("| `%s` | %.0f x %.0f x %.0f | %.1f cm3 | %.0f g | %s | %s | %.0f%% | %s |"
                 % (r["name"], r["w"], r["d"], r["h"], r["vol"], r["mass"],
                    "yes" if r["watertight"] and r["winding"] else "**NO**",
                    "yes" if r["fits"] else "**NO**", 100 * r["overhang"], r["note"]))
    L.append("")
    L.append("\"Closed\" means watertight with consistent winding - the test a slicer applies.")
    L.append("Overhang is the share of surface area steeper than 45 degrees and facing down,")
    L.append("in the orientation given.")
    L.append("")
    L.append("## Phone fit")
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append("| Cavity | %.1f x %.1f x %.1f mm |" % (D["cav_w"], D["cav_d"], D["cav_h"]))
    L.append("| iPhone 16 Pro | %.1f x %.1f x %.1f mm |"
             % (P["phone_w"], P["phone_t"], P["phone_h"]))
    L.append("| Slack, bare phone | %.1f mm wide, %.1f deep, %.1f tall |"
             % (fit["gap_x"], fit["gap_y"], fit["gap_z"]))
    L.append("| Interference with the shell | %.2f cm3 |" % fit["clash_cm3"])
    L.append("")
    if fit["clash_cm3"] < 0.01:
        L.append("The phone solid does not intersect any shell part: it goes in.")
    else:
        L.append("**The phone overlaps the shell by %.2f cm3 - it will not fit.**"
                 % fit["clash_cm3"])
    L.append("")
    L.append("## Optics")
    L.append("")
    L.append("Largest cone half-angle that reaches open air from each lens, measured by")
    L.append("ray-casting the assembled geometry.")
    L.append("")
    for mode in ("shooting", "display"):
        L.append("**%s mode** (%s)"
                 % (mode.capitalize(),
                    "barrel removed" if mode == "shooting" else "barrel fitted"))
        L.append("")
        L.append("| Lens | Needs | Clear | |")
        L.append("|---|---|---|---|")
        for label, need, got, ok in optics[mode]:
            L.append("| %s | %.1f deg | %.1f deg | %s |"
                     % (label, need, got, "clear" if ok else "vignettes"))
        L.append("")
    L.append("## Problems")
    L.append("")
    if problems:
        for pr in problems:
            L.append("- **%s**" % pr)
    else:
        L.append("None. Every part is a closed solid and fits the bed.")
    L.append("")
    txt = "\n".join(L)
    with open(os.path.join(outdir, "VALIDATION.md"), "w") as f:
        f.write(txt)
    print(txt)
    return txt


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "export"
    out = HERE
    if cmd == "export":
        rows, problems, total, fit, optics = do_export(out)
        report(out, rows, problems, total, fit, optics)
        inject_page_data(out, rows, total, optics)
    elif cmd == "render":
        do_render(out, argv[2])
    elif cmd == "exploded":
        do_exploded(out)
    else:
        raise SystemExit("usage: build_xl401.py [export|render <view>|exploded]")


if __name__ == "__main__":
    main(sys.argv)

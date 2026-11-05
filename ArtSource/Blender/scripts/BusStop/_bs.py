"""버스정류장 그룹 공용 도우미: 기본 도형, 베벨, 절차 머티리얼(굽기용), 이미지/유리/데칼 머티리얼, 소켓."""
import os, sys, json, math, subprocess
import bpy, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import k3d  # noqa: E402

TAU = math.tau


# ---------------------------------------------------------------- 2D 텍스처

def textures(asset):
    """_tex.py(Pillow) 로 이 에셋 PNG 를 다시 만든다. 반환: (텍스처 폴더, 데칼 배치표)."""
    py = k3d.PY
    subprocess.run([py, "-I", os.path.join(HERE, "_tex.py"), asset, k3d.ART, k3d.CACHE], check=True)
    lay = os.path.join(k3d.CACHE, "busstop", asset + ".json")
    return os.path.join(k3d.ART, "Textures", asset), (json.load(open(lay)) if os.path.exists(lay) else {})


# ---------------------------------------------------------------- 도형

def _obj(name, bm, mat=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    o.location, o.rotation_euler = loc, rot
    return o


def bev(o, w=0.003, segs=2, angle=35):
    """베벨 + 가중 노멀 (스무스 셰이딩)."""
    for p in o.data.polygons:
        p.use_smooth = True
    if w > 0:
        b = o.modifiers.new("Bevel", 'BEVEL')
        b.width, b.segments, b.limit_method = w, segs, 'ANGLE'
        b.angle_limit = math.radians(angle)
        b.miter_outer = 'MITER_ARC'
    wn = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    wn.weight = 100
    return o


def box(name, size, loc, mat=None, bevel=0.003, segs=2, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    return bev(_obj(name, bm, mat, loc, rot), bevel, segs)


def cyl(name, r, h, loc, mat=None, n=24, bevel=0.002, segs=2, rot=(0, 0, 0), r2=None):
    """Z 축 원기둥 (loc = 아래면 중심)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    return bev(_obj(name, bm, mat, loc, rot), bevel, segs, 30)


def prism(name, pts, depth, mat=None, axis='Z', loc=(0, 0, 0), bevel=0.003, segs=2, rot=(0, 0, 0)):
    """2D 윤곽(반시계) 을 axis 방향으로 depth 만큼 압출 (가운데 정렬).
    axis='Z': (x,y) 윤곽 · 'X': (y,z) 윤곽 · 'Y': (x,z) 윤곽."""
    bm = bmesh.new()
    def P(u, v, w):
        return {'Z': (u, v, w), 'X': (w, u, v), 'Y': (u, w, v)}[axis]
    vs = [bm.verts.new(P(u, v, -depth / 2)) for u, v in pts]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=P(0, 0, depth), verts=top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bev(_obj(name, bm, mat, loc, rot), bevel, segs)


def rrect(w, h, r, n=4, cx=0.0, cy=0.0):
    """둥근 사각형 윤곽 점 (반시계)."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (w / 2 - r), cy + qy * (h / 2 - r)
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
    return pts


def pipe(name, pts, r, mat=None, res=10, caps=True):
    """점 목록을 지나는 둥근 관 (커브 -> 메시)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = r, max(1, res // 4), caps
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(cu)
    m = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(m)
    if mat:
        m.data.materials.clear()
        m.data.materials.append(mat)
    return bev(m, 0, 0)


def bend(pts, rad=0.05, n=4):
    """꺾인 점 목록의 모서리를 둥글게 (관 꺾임)."""
    out = [Vector(pts[0])]
    for i in range(1, len(pts) - 1):
        a, b, c = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[i + 1])
        d1, d2 = (a - b).normalized(), (c - b).normalized()
        r = min(rad, (a - b).length / 2, (c - b).length / 2)
        p0, p2 = b + d1 * r, b + d2 * r
        for k in range(n + 1):
            t = k / n
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2)
    out.append(Vector(pts[-1]))
    return [tuple(v) for v in out]


def quad(name, w, h, mat, loc, rot=(0, 0, 0), uv=(0, 0, 1, 1)):
    """정면 -Y 를 보는 사각형 (U -> +X, V -> +Z), uv = 아틀라스 사각형."""
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    lay = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = uv
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[lay].uv = c
    return _obj(name, bm, mat, loc, rot)


def wrap(name, r, w, h, mat, center_z, ang=0.0, uv=(0, 0, 1, 1), axis_xy=(0.0, 0.0), segs=8):
    """반지름 r 원기둥(Z 축, 중심 axis_xy) 표면을 감싸는 데칼. ang=0 이면 -Y 쪽 정면."""
    bm = bmesh.new()
    lay = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = uv
    rows = []
    for i in range(segs + 1):
        t = i / segs
        a = ang + (t - 0.5) * (w / r)
        x, y = axis_xy[0] + math.sin(a) * r, axis_xy[1] - math.cos(a) * r
        rows.append((bm.verts.new((x, y, center_z - h / 2)), bm.verts.new((x, y, center_z + h / 2)), t))
    for (a0, a1, t0), (b0, b1, t1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, b0, b1, a1))
        for l, (tt, vv) in zip(f.loops, ((t0, v0), (t1, v0), (t1, v1), (t0, v1))):
            l[lay].uv = (u0 + (u1 - u0) * tt, vv)
    return _obj(name, bm, mat)


def decal(name, lay, key, mat, loc, rot=(0, 0, 0), w=None):
    """데칼 배치표(key) 크기 그대로 사각형. w 를 주면 비율 유지 축소."""
    d = lay["decals"][key]
    s = (w / d["w"]) if w else 1.0
    return quad(name, d["w"] * s, d["h"] * s, mat, loc, rot, d["uv"])


def uv_along(o, axis=0, tile=0.6):
    """나뭇결이 axis 방향(V)으로 가도록 하는 월드 박스 UV."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    mw = o.matrix_world
    for f in bm.faces:
        n = (mw.to_3x3() @ f.normal)
        dom = max(range(3), key=lambda i: abs(n[i]))
        others = [i for i in range(3) if i != dom]
        if dom == axis:                                               # 마구리
            ua, va = others
        else:
            va, ua = axis, next(i for i in others if i != axis)
        for l in f.loops:
            w = mw @ l.vert.co
            l[uvl].uv = (w[ua] / tile, w[va] / tile)
    bm.to_mesh(me)
    bm.free()


def join(objs, name):
    o = k3d.join(objs, name)
    return o


def parent(children, root):
    for c in children:
        mw = c.matrix_world.copy()
        c.parent = root
        c.matrix_world = mw


def socket(name, loc, root, rot=(0, 0, 0), size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', size
    bpy.context.scene.collection.objects.link(e)
    e.location, e.rotation_euler = loc, rot
    e.parent = root
    return e


def bake_hidden(obj, size, hide=(), **kw):
    """다른 오브젝트(유리 등)를 렌더에서 숨기고 굽는다 (AO 오염 방지)."""
    old = [(o, o.hide_render) for o in hide]
    for o, _ in old:
        o.hide_render = True
    try:
        return k3d.bake(obj, size, **kw)
    finally:
        for o, h in old:
            o.hide_render = h


# ---------------------------------------------------------------- 노드 도우미

def _set(nt, sock, v):
    if isinstance(v, bpy.types.NodeSocket):
        nt.links.new(v, sock)
    elif v is not None:
        if hasattr(sock.default_value, "__len__") and not isinstance(v, (tuple, list)):
            v = (v,) * len(sock.default_value)
        elif hasattr(sock.default_value, "__len__") and len(v) < len(sock.default_value):
            v = (*v, 1.0)
        sock.default_value = v


def M(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation, n.use_clamp = op, clamp
    _set(nt, n.inputs[0], a)
    if b is not None:
        _set(nt, n.inputs[1], b)
    return n.outputs[0]


def MR(nt, x, lo, hi, a=0.0, b=1.0):
    n = nt.nodes.new('ShaderNodeMapRange')
    n.clamp = True
    _set(nt, n.inputs['Value'], x)
    n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = lo, hi
    n.inputs['To Min'].default_value, n.inputs['To Max'].default_value = a, b
    return n.outputs['Result']


def MIX(nt, fac, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type, n.blend_type, n.clamp_result = 'RGBA', blend, True
    _set(nt, n.inputs['Factor'], fac)
    _set(nt, [s for s in n.inputs if s.name == 'A' and s.type == 'RGBA'][0], a)
    _set(nt, [s for s in n.inputs if s.name == 'B' and s.type == 'RGBA'][0], b)
    return [s for s in n.outputs if s.type == 'RGBA'][0]


def NOISE(nt, vec, scale, detail=6.0, rough=0.55, distort=0.0):
    n = nt.nodes.new('ShaderNodeTexNoise')
    _set(nt, n.inputs['Vector'], vec)
    n.inputs['Scale'].default_value, n.inputs['Detail'].default_value = scale, detail
    n.inputs['Roughness'].default_value, n.inputs['Distortion'].default_value = rough, distort
    return n.outputs['Fac']


def VMUL(nt, v, s):
    n = nt.nodes.new('ShaderNodeVectorMath')
    n.operation = 'MULTIPLY'
    _set(nt, n.inputs[0], v)
    n.inputs[1].default_value = s if isinstance(s, (tuple, list)) else (s, s, s)
    return n.outputs[0]


def IMG(nt, path, vec, non_color=False, box=True):
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = k3d.load_image(path)
    if non_color:
        n.image.colorspace_settings.name = 'Non-Color'
    if box:
        n.projection, n.projection_blend = 'BOX', 0.3
    if vec is not None:
        _set(nt, n.inputs['Vector'], vec)
    return n


def BW(nt, c):
    n = nt.nodes.new('ShaderNodeRGBToBW')
    _set(nt, n.inputs[0], c)
    return n.outputs[0]


def SEP(nt, v):
    n = nt.nodes.new('ShaderNodeSeparateXYZ')
    _set(nt, n.inputs[0], v)
    return n.outputs


def _common(m, scale):
    nt = m.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    co = tc.outputs['Object']
    return nt, k3d.principled(m), co, VMUL(nt, co, scale), geo


def _edge(nt, geo, radius=0.006):
    bv = nt.nodes.new('ShaderNodeBevel')
    bv.samples = 8
    bv.inputs['Radius'].default_value = radius
    d = nt.nodes.new('ShaderNodeVectorMath')
    d.operation = 'DOT_PRODUCT'
    nt.links.new(bv.outputs['Normal'], d.inputs[0])
    nt.links.new(geo.outputs['Normal'], d.inputs[1])
    return MR(nt, M(nt, 'SUBTRACT', 1.0, d.outputs['Value']), 0.004, 0.06)


def _cavity(nt, dist=0.06):
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao.samples, ao.only_local = 12, True
    ao.inputs['Distance'].default_value = dist
    return M(nt, 'SUBTRACT', 1.0, ao.outputs['AO'])


def _lin(c):
    return tuple(x / 255.0 if max(c) > 1.0 else x for x in c)


# ---------------------------------------------------------------- 절차 머티리얼 (bake 용)

def m_paint(name, color, rough=0.42, wear=0.5, grime=0.5, rust=0.25, fade=0.35, scale=1.0,
            bare=(0.42, 0.42, 0.43), ground=0.35):
    """도장 강재: 색 얼룩 + 모서리 칠 벗겨짐(금속) + 녹 + 오목한 곳 때 + 바닥 흙탕 + 빗물 줄 + 윗면 탈색."""
    m = k3d.mat(name, color, rough)
    nt, p, co, c, geo = _common(m, scale)
    gm, ru = k3d.polyhaven("green_metal_rust", "1k"), k3d.polyhaven("rust_coarse_01", "1k")
    pv = BW(nt, IMG(nt, gm["diff"], VMUL(nt, co, 0.7 * scale)).outputs['Color'])
    n1 = NOISE(nt, c, 2.5, 5)
    n2 = NOISE(nt, c, 45, 8, 0.6)
    z = SEP(nt, co)[2]
    nrm_z = SEP(nt, geo.outputs['Normal'])[2]
    edge = _edge(nt, geo)
    wear_m = MR(nt, M(nt, 'ADD', edge, M(nt, 'MULTIPLY', M(nt, 'SUBTRACT', n2, 0.5), 1.3)),
                0.85 - 0.45 * wear, 1.0 - 0.45 * wear)
    low = MR(nt, z, ground, 0.0)                                       # 바닥 근처
    rust_m = M(nt, 'MULTIPLY', M(nt, 'ADD', M(nt, 'MULTIPLY', wear_m, 0.8),
                                 MR(nt, M(nt, 'MULTIPLY', low, NOISE(nt, c, 9, 6)), 0.25, 0.45)), rust, True)
    cav = _cavity(nt)
    streak = MR(nt, NOISE(nt, VMUL(nt, co, (9 * scale, 9 * scale, 0.5 * scale)), 1.0, 4), 0.52, 0.72)
    vert = MR(nt, M(nt, 'ABSOLUTE', nrm_z), 0.6, 0.2)
    grime_m = M(nt, 'MULTIPLY', M(nt, 'ADD', M(nt, 'ADD', M(nt, 'MULTIPLY', cav, 1.4),
                                                   M(nt, 'MULTIPLY', low, 0.8)),
                                  M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', streak, vert), 0.35)),
                grime * 0.9, True)
    fade_m = M(nt, 'MULTIPLY', MR(nt, nrm_z, 0.4, 0.95), fade)
    col = MIX(nt, 0.55, color, M(nt, 'ADD', M(nt, 'MULTIPLY', pv, 0.9), 0.1), 'SOFT_LIGHT')
    col = MIX(nt, M(nt, 'MULTIPLY', n1, 0.35), col, tuple(x * 0.82 for x in color))
    faded = tuple(x * 0.55 + 0.11 for x in color)
    col = MIX(nt, fade_m, col, faded)
    col = MIX(nt, wear_m, col, bare)
    col = MIX(nt, rust_m, col, IMG(nt, ru["diff"], c).outputs['Color'])
    col = MIX(nt, grime_m, col, (0.035, 0.03, 0.024))
    # 어두운 도장엔 검은 때가 안 보임 -> 밝은 흙탕 튐(바닥 25 cm) + 세로면 녹물 줄. 색·거칠기만 (범프에 넣지 않음)
    run = M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', streak, vert), rust * 0.7, True)
    col = MIX(nt, run, col, IMG(nt, ru["diff"], VMUL(nt, co, (2 * scale, 2 * scale, 0.4 * scale))).outputs['Color'])
    mud = M(nt, 'MULTIPLY', MR(nt, z, 0.25, 0.02), MR(nt, NOISE(nt, c, 14, 6), 0.38, 0.62), True)
    mud = M(nt, 'MULTIPLY', mud, min(1.0, ground / 0.35) * 0.85)
    col = MIX(nt, mud, col, (0.30, 0.26, 0.2))
    nt.links.new(col, p.inputs['Base Color'])
    rgh = M(nt, 'ADD', rough, M(nt, 'MULTIPLY', M(nt, 'SUBTRACT', n1, 0.5), 0.2))
    rgh = MIX(nt, wear_m, rgh, 0.32)
    rgh = MIX(nt, M(nt, 'ADD', rust_m, M(nt, 'MULTIPLY', grime_m, 0.6), True), rgh, 0.9)
    rgh = MIX(nt, M(nt, 'ADD', mud, run, True), rgh, 0.85)
    nt.links.new(BW(nt, rgh), p.inputs['Roughness'])
    nt.links.new(M(nt, 'MULTIPLY', wear_m, M(nt, 'SUBTRACT', 1.0, rust_m, True)), p.inputs['Metallic'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value, bump.inputs['Distance'].default_value = 0.25, 0.0006
    nt.links.new(M(nt, 'MULTIPLY', n2, 0.3), bump.inputs['Height'])   # Bevel/AO 노드가 섞이면 굽기 노멀이 깨짐
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def m_metal(name, color, rough=0.3, grime=0.5, brushed=True, scale=1.0, metal=1.0, spots=0.3):
    """알루미늄/스테인리스: 결(브러시) + 물자국 얼룩 + 오목한 곳 때 + 손자국."""
    m = k3d.mat(name, color, rough, metal)
    nt, p, co, c, geo = _common(m, scale)
    br = NOISE(nt, VMUL(nt, co, (160 * scale, 160 * scale, 2 * scale)), 1.0, 6) if brushed \
        else NOISE(nt, c, 30, 6)                                       # 세로 헤어라인
    n1 = NOISE(nt, c, 3, 5)
    sp = MR(nt, NOISE(nt, c, 14, 4), 0.62 - 0.1 * spots, 0.75)
    z = SEP(nt, co)[2]
    cav = _cavity(nt)
    low = MR(nt, z, 0.3, 0.0)
    grime_m = M(nt, 'MULTIPLY', M(nt, 'ADD', M(nt, 'MULTIPLY', cav, 1.3), M(nt, 'MULTIPLY', low, 0.6)), grime, True)
    col = MIX(nt, M(nt, 'MULTIPLY', br, 0.25), color, tuple(x * 0.8 for x in color))
    col = MIX(nt, M(nt, 'MULTIPLY', sp, spots), col, (0.75, 0.74, 0.7))
    col = MIX(nt, M(nt, 'MULTIPLY', n1, 0.3), col, tuple(x * 0.85 for x in color))
    col = MIX(nt, grime_m, col, (0.04, 0.035, 0.03))
    nt.links.new(col, p.inputs['Base Color'])
    rgh = M(nt, 'ADD', rough, M(nt, 'MULTIPLY', M(nt, 'SUBTRACT', br, 0.5), 0.25))
    rgh = M(nt, 'ADD', rgh, M(nt, 'ADD', M(nt, 'MULTIPLY', sp, 0.25 * spots), M(nt, 'MULTIPLY', grime_m, 0.5)), True)
    nt.links.new(rgh, p.inputs['Roughness'])
    nt.links.new(M(nt, 'MULTIPLY', metal, M(nt, 'SUBTRACT', 1.0, grime_m, True)), p.inputs['Metallic'])
    return m


def m_plastic(name, color, rough=0.5, grime=0.5, fade=0.3, scale=1.0):
    m = k3d.mat(name, color, rough)
    nt, p, co, c, geo = _common(m, scale)
    n1 = NOISE(nt, c, 4, 5)
    n2 = NOISE(nt, c, 60, 6)
    cav = _cavity(nt, 0.04)
    nz = SEP(nt, geo.outputs['Normal'])[2]
    col = MIX(nt, M(nt, 'MULTIPLY', n1, 0.3), color, tuple(x * 0.85 for x in color))
    col = MIX(nt, M(nt, 'MULTIPLY', MR(nt, nz, 0.4, 0.95), fade), col, tuple(x * 0.6 + 0.12 for x in color))
    g = M(nt, 'MULTIPLY', M(nt, 'ADD', M(nt, 'MULTIPLY', cav, 1.3), M(nt, 'MULTIPLY', n2, 0.15)), grime, True)
    col = MIX(nt, g, col, (0.04, 0.035, 0.03))
    nt.links.new(col, p.inputs['Base Color'])
    nt.links.new(M(nt, 'ADD', rough, M(nt, 'MULTIPLY', g, 0.3)), p.inputs['Roughness'])
    return m


def m_rubber(name, color=(0.022, 0.022, 0.024), rough=0.85, dust=0.6):
    m = k3d.mat(name, color, rough)
    nt, p, co, c, geo = _common(m, 1.0)
    nz = SEP(nt, geo.outputs['Normal'])[2]
    d = M(nt, 'MULTIPLY', M(nt, 'MULTIPLY', MR(nt, nz, 0.2, 0.9), NOISE(nt, c, 25, 5)), dust)
    nt.links.new(MIX(nt, d, color, (0.16, 0.15, 0.13)), p.inputs['Base Color'])
    return m


def m_wood(name, tint=(0.55, 0.36, 0.2), rough=0.62, grime=0.5, grey=0.35):
    """오크 스캔(UVMap, 결 = V) + 비바람 회색 탈색 + 앉는 자리 반들반들 + 물얼룩."""
    m = k3d.mat(name, tint, rough)
    nt, p, co, c, geo = _common(m, 1.0)
    ow = k3d.polyhaven("oak_veneer_01", "1k")
    di = IMG(nt, ow["diff"], None, box=False).outputs['Color']
    rg = IMG(nt, ow["rough"], None, non_color=True, box=False).outputs['Color']
    nz = SEP(nt, geo.outputs['Normal'])[2]
    n1 = NOISE(nt, c, 3, 5)
    water = MR(nt, NOISE(nt, VMUL(nt, co, 1.0), 7, 4), 0.58, 0.7)
    col = MIX(nt, 1.0, di, tint, 'MULTIPLY')
    col = MIX(nt, 1.0, col, (1.6, 1.6, 1.6), 'MULTIPLY')
    col = MIX(nt, M(nt, 'MULTIPLY', MR(nt, nz, 0.3, 0.95), M(nt, 'ADD', grey, M(nt, 'MULTIPLY', n1, 0.3))), col,
              (0.3, 0.28, 0.25))
    col = MIX(nt, M(nt, 'MULTIPLY', water, 0.5), col, (0.08, 0.05, 0.03))
    cav = _cavity(nt, 0.03)
    col = MIX(nt, M(nt, 'MULTIPLY', cav, grime * 1.5, True), col, (0.03, 0.022, 0.015))
    edge = _edge(nt, geo, 0.004)
    col = MIX(nt, M(nt, 'MULTIPLY', edge, 0.45), col, (0.42, 0.33, 0.24))
    nt.links.new(col, p.inputs['Base Color'])
    nt.links.new(M(nt, 'ADD', M(nt, 'MULTIPLY', BW(nt, rg), 0.5), rough * 0.6), p.inputs['Roughness'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value, bump.inputs['Distance'].default_value = 0.3, 0.0008
    nt.links.new(BW(nt, di), bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


# ---------------------------------------------------------------- 굽지 않는 머티리얼

def m_image(name, path, rough=0.45, emit=0.0, clip=None, double=False, metal=0.0):
    """이미지 머티리얼 (간판/포스터/데칼/M_Dyn). emit>0 이면 같은 이미지로 발광."""
    m = k3d.mat(name, (1, 1, 1), rough, metal)
    p = k3d.principled(m)
    n = k3d.image_node(m, k3d.load_image(path), p.inputs['Base Color'])
    if emit:
        m.node_tree.links.new(n.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emit
    if clip is not None:
        m.node_tree.links.new(n.outputs['Alpha'], p.inputs['Alpha'])
        k3d.flag(m, alpha_clip=clip)
    if double:
        k3d.flag(m, double_sided=True)
    return m


def m_glass(name, path, rough=0.04):
    """M_Glass: 색조 = 텍스처 RGB, 불투명도(먼지·손자국) = 텍스처 알파. Alpha 기본값은 1 로 둔다."""
    m = k3d.mat(name, (1, 1, 1), rough)
    p = k3d.principled(m)
    n = k3d.image_node(m, k3d.load_image(path), p.inputs['Base Color'])
    m.node_tree.links.new(n.outputs['Alpha'], p.inputs['Alpha'])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return k3d.flag(m, double_sided=True)


# ---------------------------------------------------------------- 1인칭 확인 렌더

def shot(asset, cam, target, lens=35, tag="fp", res=(1280, 720), sun_dir=(-0.45, 0.55, -0.7), extra=()):
    """눈높이 카메라 렌더 -> ArtSource/Previews/<asset>_<tag>.png (지면·해·하늘 포함)."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
    w = bpy.data.worlds.new("bs_shot")
    if w.node_tree is None:
        w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value, bg.inputs['Strength'].default_value = (0.6, 0.66, 0.74, 1), 0.7
    old, sc.world = sc.world, w
    tmp = []
    ld = bpy.data.lights.new("bs_sun", 'SUN')
    ld.energy = 2.2
    sun = bpy.data.objects.new("bs_sun", ld)
    sc.collection.objects.link(sun)
    sun.rotation_euler = Vector(sun_dir).to_track_quat('-Z', 'Y').to_euler()
    tmp.append(sun)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.002))
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("bs_ground", (0.3, 0.3, 0.3), 0.85))
    tmp.append(g)
    cd = bpy.data.cameras.new("bs_cam")
    cd.lens, cd.clip_start = lens, 0.05
    c = bpy.data.objects.new("bs_cam", cd)
    sc.collection.objects.link(c)
    c.location = cam
    c.rotation_euler = (Vector(target) - Vector(cam)).to_track_quat('-Z', 'Y').to_euler()
    tmp.append(c)
    sc.camera = c
    p = os.path.join(k3d.SRC, "Previews", f"{asset}_{tag}.png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.world = old
    print("bs: shot", p)
    return p

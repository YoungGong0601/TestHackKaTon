"""차량 그룹 공용 도구: 스플라인, 매개 곡면(단차 인셋), 회전체, 튜브, 절차 머티리얼.
CarSedan/CarHatch/Bicycle/DeliveryScooter 스크립트가 import 한다."""
import sys, os, math, subprocess
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import k3d  # noqa: E402

TEX = os.path.join(k3d.CACHE, "vehicles")


def make_textures():
    """Pillow 텍스처(번호판·스티커·배달통 등)를 캐시에 만든다. VEH_TEX_DONE=1 이면 건너뜀 (병렬 실행 시 먼저 한 번 만든다)."""
    if os.environ.get("VEH_TEX_DONE"):
        return
    py = os.path.abspath(os.path.join(HERE, "..", "..", "..", "_cache", "venv", "bin", "python"))
    subprocess.run([py, os.path.join(HERE, "_tex.py"), TEX], check=True)


def tex(name):
    return os.path.join(TEX, name)


# ------------------------------------------------------------------ 1D 스플라인 (단조 3차, PCHIP)
def pchip(pts):
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros_like(ys)
    for k in range(1, len(xs) - 1):
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
    m[0], m[-1] = d[0], d[-1]

    def f(x):
        x = min(max(float(x), xs[0]), xs[-1])
        k = int(min(max(np.searchsorted(xs, x) - 1, 0), len(xs) - 2))
        t = (x - xs[k]) / h[k]
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[k] + (t ** 3 - 2 * t ** 2 + t) * h[k] * m[k]
                + (-2 * t ** 3 + 3 * t ** 2) * ys[k + 1] + (t ** 3 - t ** 2) * h[k] * m[k + 1])
    return f


def smooth01(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ 매개 곡면
def params(base, regions, key):
    """기본 매개값 + 영역 경계(깊이 있는 경계는 중복 = 단차선). [(값, side)] 정렬."""
    out = {(round(v, 7), 0) for v in base}
    for r in regions:
        dup = abs(r.get("depth", 0)) > 0
        for b in (key + "0", key + "1"):
            v = round(r[b], 7)
            out |= {(v, -1), (v, 1)} if dup else {(v, 0)}
        bd, bs = r.get("band"), r.get("band_sides", "u0u1v0v1")
        if bd:
            k = 0 if key == "u" else 1
            for side, sgn in ((key + "0", 1), (key + "1", -1)):
                if side in bs:
                    out.add((round(r[side] + sgn * bd[k], 7), 0))
    vals = sorted(out, key=lambda p: (p[0], p[1]))
    lo, hi = min(base), max(base)
    return [p for p in vals if lo - 1e-9 <= p[0] <= hi + 1e-9]


def pgrid(name, S, us, vs, regions, base_mat, flip=False, eps=1e-4, attrs=True):
    """S(u,v)->(x,y,z). us/vs = params() 결과. regions: dict(u0,u1,v0,v1, depth(안쪽 +), mat, seal, band_mat, band(du,dv)).
    base_mat(u,v) -> Material. 반환: 오브젝트 (중복점 병합, 퇴화면 제거)."""
    def eff(p):
        return p[0] + p[1] * 1e-7

    def inside(r, ue, ve):
        return r["u0"] < ue < r["u1"] and r["v0"] < ve < r["v1"]

    def N(u, v):
        a = Vector(S(u + eps, v)) - Vector(S(u - eps, v))
        b = Vector(S(u, v + eps)) - Vector(S(u, v - eps))
        n = a.cross(b)
        if n.length < 1e-12:
            return Vector((0, 0, 0))
        n.normalize()
        return -n if flip else n

    bm = bmesh.new()
    lay_u = bm.verts.layers.float.new("pu")
    lay_v = bm.verts.layers.float.new("pv")
    V, D = [], []
    for vi in vs:
        row, drow = [], []
        for ui in us:
            ue, ve = eff(ui), eff(vi)
            d = 0.0
            for r in regions:
                if r.get("depth", 0) and inside(r, ue, ve):
                    d = r["depth"]
            p = Vector(S(ui[0], vi[0]))
            if d:
                p = p - N(ui[0], vi[0]) * d
            bv = bm.verts.new(p)
            bv[lay_u], bv[lay_v] = ui[0], vi[0]
            row.append(bv)
            drow.append(d)
        V.append(row)
        D.append(drow)
    mats = []

    def mi(m):
        if m not in mats:
            mats.append(m)
        return mats.index(m)

    for i in range(len(vs) - 1):
        for j in range(len(us) - 1):
            q = [V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]]
            if flip:
                q.reverse()
            ds = (D[i][j], D[i][j + 1], D[i + 1][j + 1], D[i + 1][j])
            um = (eff(us[j]) + eff(us[j + 1])) / 2
            vm = (eff(vs[i]) + eff(vs[i + 1])) / 2
            m = None
            if max(ds) != min(ds):  # 단차면
                for r in regions:
                    if r.get("depth", 0) and r["u0"] - 1e-6 <= um <= r["u1"] + 1e-6 and r["v0"] - 1e-6 <= vm <= r["v1"] + 1e-6:
                        m = r.get("seal") or r["mat"]
            if m is None:
                for r in regions:
                    if inside(r, um, vm):
                        m = r["mat"]
                        bd, bs = r.get("band"), r.get("band_sides", "u0u1v0v1")
                        if bd and r.get("band_mat") and (
                                ("u0" in bs and um < r["u0"] + bd[0]) or ("u1" in bs and um > r["u1"] - bd[0]) or
                                ("v0" in bs and vm < r["v0"] + bd[1]) or ("v1" in bs and vm > r["v1"] - bd[1])):
                            m = r["band_mat"]
            if m is None:
                m = base_mat(um, vm)
            try:
                f = bm.faces.new(q)
                f.material_index = mi(m)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def mirror_x(o, merge=0.0008):
    m = o.modifiers.new("mir", 'MIRROR')
    m.use_axis[0] = True
    m.use_clip = True
    m.use_mirror_merge = True
    m.merge_threshold = merge
    k3d.apply_all(o)
    return o


# ------------------------------------------------------------------ 기본 메시 도구
def mesh_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def lathe(name, prof, segs, mat_ids=None, mats=(), axis='X', a0=0.0, a1=2 * math.pi, cap=False):
    """prof=[(축 위치, 반지름)] 를 축 둘레로 회전. mat_ids[k] = 구간 k 의 재질 인덱스."""
    bm = bmesh.new()
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = segs if full else segs + 1
    rings = []
    for k in range(n):
        a = a0 + (a1 - a0) * k / segs
        ring = []
        for (x, r) in prof:
            c, s = math.cos(a) * r, math.sin(a) * r
            co = (x, c, s) if axis == 'X' else ((c, s, x) if axis == 'Z' else (c, x, s))
            ring.append(bm.verts.new(co))
        rings.append(ring)
    for k in range(segs):
        r0, r1 = rings[k], rings[(k + 1) % n]
        for i in range(len(prof) - 1):
            try:
                f = bm.faces.new((r0[i], r0[i + 1], r1[i + 1], r1[i]))
                f.material_index = mat_ids[i] if mat_ids else 0
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, list(mats))


def tube(name, pts, radius, segs=10, mat=None, cap=True, closed=False):
    """경로 pts([(x,y,z)]) 를 따라가는 원형 튜브 (radius: 숫자 또는 점별 리스트)."""
    pts = [Vector(p) for p in pts]
    rad = radius if isinstance(radius, (list, tuple)) else [radius] * len(pts)
    bm = bmesh.new()
    rings = []
    n_prev = None
    for i, p in enumerate(pts):
        if closed:
            t = (pts[(i + 1) % len(pts)] - pts[i - 1])
        else:
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        t.normalize()
        if n_prev is None:
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            n1 = t.cross(ref).normalized()
        else:
            n1 = (n_prev - t * n_prev.dot(t)).normalized()  # 평행 이동 프레임 (꼬임 방지)
        n_prev = n1
        b1 = t.cross(n1).normalized()
        ring = [bm.verts.new(p + (n1 * math.cos(2 * math.pi * k / segs) + b1 * math.sin(2 * math.pi * k / segs)) * rad[i])
                for k in range(segs)]
        rings.append(ring)
    last = len(rings) if closed else len(rings) - 1
    for i in range(last):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    if cap and not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, [mat] if mat else [])


def box(name, size, loc=(0, 0, 0), mat=None, bevel=0.0, segs=2, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = mesh_obj(name, bm, [mat] if mat else [])
    o.location = loc
    o.rotation_euler = rot
    if bevel > 0:
        bevel_mod(o, bevel, segs, angle=None)
    return o


def cyl(name, r, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, segs=24, r2=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r if r2 is None else r2,
                          depth=depth)
    o = mesh_obj(name, bm, [mat] if mat else [])
    o.location, o.rotation_euler = loc, rot
    if bevel > 0:
        bevel_mod(o, bevel, 2, angle=40)
    return o


def bevel_mod(o, width, segs=2, angle=40, weighted=True):
    b = o.modifiers.new("bev", 'BEVEL')
    b.width = width
    b.segments = segs
    b.use_clamp_overlap = True
    b.harden_normals = False
    if angle is None:
        b.limit_method = 'NONE'
    else:
        b.limit_method = 'ANGLE'
        b.angle_limit = math.radians(angle)
    if weighted:
        w = o.modifiers.new("wn", 'WEIGHTED_NORMAL')
        w.keep_sharp = True
    return b


def shade(o, angle=32):
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(angle))


def apply_tf(o):
    k3d.select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join(objs, name):
    for o in objs:
        apply_tf(o)
    return k3d.join(objs, name)


def empty(name, loc, parent=None, size=0.08):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    if parent:
        e.parent = parent
    return e


def planar_uv(o, axis='X', center=(0, 0, 0), size=1.0, faces=None):
    """축 방향 평면 투영 UV (0..1 = center±size/2)."""
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    cx, cy, cz = center
    for p in me.polygons:
        if faces is not None and p.index not in faces:
            continue
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if axis == 'X':
                a, b = (co.y - cy), (co.z - cz)
            elif axis == 'Y':
                a, b = (co.x - cx), (co.z - cz)
            else:
                a, b = (co.x - cx), (co.y - cy)
            uv[li].uv = (0.5 + a / size, 0.5 + b / size)


def quad(name, w, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), flip_u=False):
    """UV 0..1 사각형 (앞면 = -Y 방향, U 오른쪽, V 위)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((-w / 2, 0, -h / 2)), bm.verts.new((w / 2, 0, -h / 2)),
          bm.verts.new((w / 2, 0, h / 2)), bm.verts.new((-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    for l, uv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        l[uvl].uv = (1 - uv[0], uv[1]) if flip_u else uv
    o = mesh_obj(name, bm, [mat])
    o.location, o.rotation_euler = loc, rot
    return o


# ------------------------------------------------------------------ 노드 도우미
class NB:
    """절차 머티리얼 노드 빌더 (Principled 1개 + 입력 체인)."""

    def __init__(s, name):
        s.m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        s.nt = k3d._nodes(s.m)
        s.p = k3d.principled(s.m)
        if s.p is None:
            k3d.mat(name)
            s.p = k3d.principled(s.m)
        s._tc = None
        s._geo = None

    def n(s, typ, **props):
        node = s.nt.nodes.new(typ)
        for k, v in props.items():
            setattr(node, k, v)
        return node

    @staticmethod
    def sock(node, name, out=False, typ=None):
        socks = node.outputs if out else node.inputs
        for so in socks:
            if so.name == name and (typ is None or so.type == typ):
                return so
        raise KeyError(f"{node.bl_idname}.{name}")

    def link(s, src, dst):
        if isinstance(src, (int, float)):
            dst.default_value = src
        elif isinstance(src, (tuple, list)):
            dst.default_value = tuple(src) + ((1.0,) if len(src) == 3 and len(dst.default_value) == 4 else ())
        else:
            s.nt.links.new(src, dst)

    # 좌표
    def obj(s):
        if s._tc is None:
            s._tc = s.n('ShaderNodeTexCoord')
        return s._tc.outputs['Object']

    def geo(s, out='Normal'):
        if s._geo is None:
            s._geo = s.n('ShaderNodeNewGeometry')
        return s._geo.outputs[out]

    def xyz(s, vec=None):
        n = s.n('ShaderNodeSeparateXYZ')
        s.link(vec if vec is not None else s.obj(), n.inputs[0])
        return n.outputs['X'], n.outputs['Y'], n.outputs['Z']

    def attr(s, name):
        n = s.n('ShaderNodeAttribute', attribute_name=name)
        return n.outputs['Fac']

    def uv(s, name="UVMap"):
        n = s.n('ShaderNodeUVMap', uv_map=name)
        return n.outputs['UV']

    # 수학
    def math(s, op, a, b=0.0, clamp=False):
        n = s.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        s.link(a, n.inputs[0])
        s.link(b, n.inputs[1])
        return n.outputs[0]

    def add(s, a, b):
        return s.math('ADD', a, b)

    def mul(s, a, b, clamp=False):
        return s.math('MULTIPLY', a, b, clamp)

    def sub(s, a, b):
        return s.math('SUBTRACT', a, b)

    def absf(s, a):
        return s.math('ABSOLUTE', a)

    def maxf(s, a, b):
        return s.math('MAXIMUM', a, b)

    def minf(s, a, b):
        return s.math('MINIMUM', a, b)

    def maprange(s, x, a, b, c=0.0, d=1.0, smooth=False):
        n = s.n('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP' if smooth else 'LINEAR', clamp=True)
        s.link(a, n.inputs[1])
        s.link(b, n.inputs[2])
        s.link(c, n.inputs[3])
        s.link(d, n.inputs[4])
        s.link(x, n.inputs[0])
        return n.outputs[0]

    def band(s, x, lo, hi, soft=0.002):
        """lo<x<hi 에서 1 (가장자리 부드럽게)."""
        a = s.maprange(x, lo - soft, lo + soft, 0, 1, True)
        b = s.maprange(x, hi - soft, hi + soft, 1, 0, True)
        return s.mul(a, b)

    def line(s, x, c, w):
        """|x-c|<w 에서 1 인 선 (홈)."""
        return s.maprange(s.absf(s.sub(x, c)), w * 0.35, w, 1, 0, True)

    def noise(s, scale, detail=4.0, rough=0.55, vec=None, dist=0.0, out='Fac', dim='3D'):
        n = s.n('ShaderNodeTexNoise', noise_dimensions=dim)
        if vec is not None:
            s.link(vec, n.inputs['Vector'])
        else:
            s.link(s.obj(), n.inputs['Vector'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist
        return n.outputs[out]

    def voronoi(s, scale, vec=None, feature='F1', out='Distance'):
        n = s.n('ShaderNodeTexVoronoi', feature=feature)
        s.link(vec if vec is not None else s.obj(), n.inputs['Vector'])
        n.inputs['Scale'].default_value = scale
        return n.outputs[out]

    def ao(s, dist=0.1, inside=False, samples=16):
        n = s.n('ShaderNodeAmbientOcclusion', inside=inside, samples=samples)
        n.inputs['Distance'].default_value = dist
        return n.outputs['AO']

    def mix(s, fac, a, b):
        n = s.n('ShaderNodeMix', data_type='RGBA', clamp_factor=True)
        s.link(fac, s.sock(n, 'Factor', typ='VALUE'))
        s.link(a, s.sock(n, 'A', typ='RGBA'))
        s.link(b, s.sock(n, 'B', typ='RGBA'))
        return s.sock(n, 'Result', out=True, typ='RGBA')

    def mixf(s, fac, a, b):
        n = s.n('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        s.link(fac, s.sock(n, 'Factor', typ='VALUE'))
        s.link(a, s.sock(n, 'A', typ='VALUE'))
        s.link(b, s.sock(n, 'B', typ='VALUE'))
        return s.sock(n, 'Result', out=True, typ='VALUE')

    def image(s, path, uv=None, non_color=False, ext='CLIP', out='Color'):
        im = k3d.load_image(path, non_color=non_color)
        n = s.n('ShaderNodeTexImage', extension=ext)
        n.image = im
        if uv is not None:
            s.link(uv, n.inputs['Vector'])
        return n.outputs[out]

    def bump(s, h, strength=0.5, dist=0.003):
        n = s.n('ShaderNodeBump')
        s.link(h, n.inputs['Height'])
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = dist
        return n.outputs['Normal']

    # 출력
    def out(s, color=None, rough=None, metal=None, normal=None, emis=None, emis_strength=0.0):
        p = s.p
        if color is not None:
            s.link(color, p.inputs['Base Color'])
        if rough is not None:
            s.link(rough, p.inputs['Roughness'])
        if metal is not None:
            s.link(metal, p.inputs['Metallic'])
        if normal is not None:
            s.link(normal, p.inputs['Normal'])
        if emis is not None:
            s.link(emis, p.inputs['Emission Color'])
            p.inputs['Emission Strength'].default_value = emis_strength
        return s.m


# ------------------------------------------------------------------ 공용 머티리얼 레시피
def grime_mask(g, low_z=0.55, low_amt=0.6, cav_dist=0.06, cav_amt=0.7, speck=0.25, scale=1.0):
    """아래쪽 흙먼지 + 틈새 때 + 점 얼룩 마스크 (0..1)."""
    x, y, z = g.xyz()
    low = g.mul(g.maprange(z, low_z, 0.05, 0, 1), g.maprange(g.noise(2.5 * scale, 6, 0.6), 0.3, 0.75, 0.35, 1.0))
    low = g.mul(low, low_amt)
    cav = g.mul(g.maprange(g.ao(cav_dist), 1.0, 0.45, 0, 1), cav_amt)
    sp = g.mul(g.maprange(g.noise(140 * scale, 2, 0.5), 0.62, 0.72, 0, 1), speck)
    return g.minf(g.add(g.add(low, cav), sp), 1.0)


def mat_paint(name, color, rough=0.2, metal=0.0, faded=None, gaps=None, dirt=1.0, scale=1.0, flake=0.0):
    """차체 도장: 아래쪽 흙먼지·틈새 때·햇빛 바램·패널 틈(gaps = 노드 출력 0..1)."""
    g = NB(name)
    rgb = g.n('ShaderNodeRGB', name="paint_rgb")  # 색 변형 굽기 때 이 노드 값만 바꾼다
    rgb.outputs[0].default_value = (*color, 1)
    col = rgb.outputs[0]
    if faded:
        fr = g.n('ShaderNodeRGB', name="paint_faded")
        fr.outputs[0].default_value = (*faded, 1)
        up = g.maprange(g.xyz(g.geo('Normal'))[2], 0.45, 0.95, 0, 1)
        f = g.mul(up, g.maprange(g.noise(1.2, 4, 0.6), 0.3, 0.7, 0.55, 1.0))
        col = g.mix(f, col, fr.outputs[0])
    dark = g.n('ShaderNodeVectorMath', operation='SCALE')
    g.link(rgb.outputs[0], dark.inputs[0])
    dark.inputs['Scale'].default_value = 0.93
    col = g.mix(g.mul(g.noise(9, 3, 0.5), 0.12), col, dark.outputs[0])  # 미세 얼룩
    dm = grime_mask(g, scale=scale)
    dm = g.mul(dm, dirt)
    col = g.mix(dm, col, (0.16, 0.135, 0.105))
    r = g.add(rough, g.mul(dm, 0.45))
    h = g.mul(g.noise(60, 2, 0.4), 0.15)
    if gaps is not None:
        gm = gaps(g)
        col = g.mix(gm, col, (0.012, 0.012, 0.012))
        r = g.add(r, g.mul(gm, 0.4))
        h = g.sub(h, gm)
    return g.out(col, r, metal, g.bump(h, 0.35, 0.004))


def mat_plastic(name, color=(0.03, 0.03, 0.032), rough=0.62, faded=(0.075, 0.075, 0.072), dirt=0.8, grain=900):
    """무광 텍스처 플라스틱 (위쪽은 햇빛에 하얗게 바램)."""
    g = NB(name)
    up = g.maprange(g.xyz(g.geo('Normal'))[2], 0.3, 0.9, 0, 1)
    col = g.mix(g.mul(up, 0.8), color, faded)
    dm = g.mul(grime_mask(g, low_z=0.4, cav_amt=0.5, speck=0.15), dirt)
    col = g.mix(dm, col, (0.10, 0.09, 0.075))
    r = g.add(rough, g.mul(dm, 0.2))
    return g.out(col, r, 0.0, g.bump(g.noise(grain, 2, 0.6), 0.25, 0.002))


def mat_metal(name, color=(0.8, 0.8, 0.8), rough=0.15, smudge=0.15, rust=0.0):
    g = NB(name)
    r = g.add(rough, g.mul(g.noise(18, 4, 0.6), smudge))
    col = color
    m = 1.0
    if rust > 0:
        rm = g.mul(g.maprange(g.noise(7, 6, 0.65), 0.55, 0.7, 0, 1), g.maprange(g.ao(0.04), 1.0, 0.6, 0.2, 1.0))
        rm = g.mul(rm, rust)
        col = g.mix(rm, color, (0.18, 0.07, 0.025))
        r = g.mixf(rm, r, 0.85)
        m = g.mixf(rm, 1.0, 0.0)
    return g.out(col, r, m, g.bump(g.noise(300, 2, 0.5), 0.08, 0.001))


def mat_rubber(name, color=(0.022, 0.022, 0.023), rough=0.82, dust=0.5):
    g = NB(name)
    col = g.mix(g.mul(g.maprange(g.noise(4, 5, 0.6), 0.4, 0.8, 0, 1), dust), color, (0.09, 0.085, 0.075))
    return g.out(col, rough, 0.0, g.bump(g.noise(500, 2, 0.5), 0.15, 0.001))


def glass(name, color, alpha, rough=0.04, image=None):
    m = k3d.mat(name, color, rough, 0.0, alpha=alpha)
    k3d.flag(m, transparent=True)
    m.surface_render_method = 'BLENDED'  # 미리보기(EEVEE)에서 디더 노이즈 없이 Unity 투명과 비슷하게
    if image:
        nt = m.node_tree
        p = k3d.principled(m)
        k3d.image_node(m, k3d.load_image(image), p.inputs['Base Color'])
    return m


def flat_image(name, image, rough=0.5, alpha_clip=None, metal=0.0):
    """굽지 않는 이미지 머티리얼 (번호판·스티커)."""
    m = k3d.mat(name, (1, 1, 1), rough, metal)
    p = k3d.principled(m)
    n = k3d.image_node(m, k3d.load_image(image), p.inputs['Base Color'])
    if alpha_clip is not None:
        m.node_tree.links.new(n.outputs['Alpha'], p.inputs['Alpha'])
        k3d.flag(m, alpha_clip=alpha_clip)
    return m

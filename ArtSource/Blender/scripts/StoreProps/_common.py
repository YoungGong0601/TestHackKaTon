# StoreProps 공용 도우미: 메시 생성, 절차 머티리얼(마모/때/지문), 라벨(Pillow) 연결
import sys, os, math, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d, bpy, bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PY = k3d.PY


# ------------------------------------------------------------ 메시

def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def from_bm(bm, name, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        o.data.materials.append(mat)
    return o


def bevel(o, w=0.002, seg=2, angle=35, harden=True):
    """베벨 + 경화 노멀 + 스무스 셰이딩."""
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width, m.segments = w, seg
    m.limit_method, m.angle_limit = 'ANGLE', math.radians(angle)
    m.harden_normals = harden
    for p in o.data.polygons:
        p.use_smooth = True
    return m


def box(name, size, loc=(0, 0, 0), mat=None, bev=0.002, seg=2, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = from_bm(bm, name, mat)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    if bev:
        bevel(o, bev, seg)
    return o


def cyl(name, r, h, loc=(0, 0, 0), segs=32, mat=None, bev=0.0015, seg=2, r2=None, rot=None):
    """바닥이 loc 에 오는 원기둥 (r2 = 윗면 반지름)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    o = from_bm(bm, name, mat)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    if bev:
        bevel(o, bev, seg)
    else:
        k3d.smooth(o, 40)
    return o


def lathe(name, prof, segs=32, mat=None, loc=(0, 0, 0), sharp=40):
    """Z축 회전체. prof = [(r, z), ...] 아래->위, r=0 이면 극점."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs),
                                        r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1 and len(b) == 1:
                break
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(bm, name, mat)
    o.location = loc
    k3d.smooth(o, sharp)
    return o


def fillet(pts, rad, steps=6):
    """폴리라인 모서리를 둥글게 (2차 베지어 근사)."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        d = min(rad, (a - p).length * 0.45, (b - p).length * 0.45)
        p1 = p + (a - p).normalized() * d
        p2 = p + (b - p).normalized() * d
        for i in range(steps + 1):
            t = i / steps
            out.append((1 - t) ** 2 * p1 + 2 * (1 - t) * t * p + t * t * p2)
    out.append(pts[-1])
    return out


def tube(name, pts, r, corner=0.04, mat=None, res=2, closed=False, steps=6):
    """둥근 파이프 (커브 bevel -> 메시)."""
    path = fillet(pts + ([pts[0], pts[1]] if closed else []), corner, steps)
    if closed:
        path = path[1:-1]
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(path) - 1)
    for p, c in zip(sp.points, path):
        p.co = (c.x, c.y, c.z, 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = r, res, True
    o = link(bpy.data.objects.new(name, cu))
    k3d.select([o])
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    if mat:
        o.data.materials.clear()
        o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def quad(name, w, h, mat, uv=(0, 0, 1, 1), loc=(0, 0, 0), rot=None):
    """정면(-Y)을 보는 사각 판. U -> +X, V -> +Z."""
    bm = bmesh.new()
    vs = [bm.verts.new(c) for c in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = uv
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[uvl].uv = c
    o = from_bm(bm, name, mat)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    return o


def finalize(o, name=None):
    """회전/크기 적용, 원점을 월드 (0,0,0)."""
    k3d.select([o])
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    k3d.set_origin(o, Vector((0, 0, 0)))
    if name:
        o.name = o.data.name = name
    return o


def socket(name, loc, parent, rot=(0, 0, 0)):
    e = link(bpy.data.objects.new(name, None))
    e.empty_display_type, e.empty_display_size = 'ARROWS', 0.05
    e.location, e.rotation_euler = loc, rot
    e.parent = parent
    e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def ensure_uv(o):
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")


# ------------------------------------------------------------ 노드 도우미

def new_mat(name):
    m = k3d.mat(name)
    return m, m.node_tree, k3d.principled(m)


def _set(sock, v):
    if isinstance(v, bpy.types.NodeSocket):
        sock.node.id_data.links.new(v, sock)
    elif isinstance(v, (tuple, list)):
        sock.default_value = (*v[:3], 1) if len(sock.default_value) == 4 else tuple(v[:3])
    else:
        sock.default_value = v


def mix(nt, fac, a, b, blend='MIX', kind='RGBA'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = kind
    if kind == 'RGBA':
        n.blend_type = blend
        n.clamp_result = True
    ins = [s for s in n.inputs if s.enabled]
    _set(ins[0], fac)
    _set(ins[1], a)
    _set(ins[2], b)
    return [s for s in n.outputs if s.enabled][0]


def fmix(nt, fac, a, b):
    return mix(nt, fac, a, b, kind='FLOAT')


def op(nt, operation, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation, n.use_clamp = operation, clamp
    _set(n.inputs[0], a)
    if b is not None:
        _set(n.inputs[1], b)
    return n.outputs[0]


def mrange(nt, v, a, b, c=0.0, d=1.0):
    n = nt.nodes.new('ShaderNodeMapRange')
    _set(n.inputs['Value'], v)
    n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = a, b
    n.inputs['To Min'].default_value, n.inputs['To Max'].default_value = c, d
    return n.outputs['Result']


def coord(nt, kind='Object', scale=(1, 1, 1), loc=(0, 0, 0)):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(tc.outputs[kind], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = scale
    mp.inputs['Location'].default_value = loc
    return mp.outputs['Vector']


def noise(nt, scale, detail=4.0, rough=0.55, vec=None, distortion=0.0, color=False):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = distortion
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Color' if color else 'Factor']


def voronoi(nt, scale, vec=None, feature='F1', out='Distance'):
    n = nt.nodes.new('ShaderNodeTexVoronoi')
    n.feature = feature
    n.inputs['Scale'].default_value = scale
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n.outputs[out]


def edge_mask(nt, radius=0.003, lo=0.02, hi=0.2):
    """볼록/오목 모서리 마스크 (Bevel 노드 노멀 차이)."""
    bv = nt.nodes.new('ShaderNodeBevel')
    bv.samples = 8
    bv.inputs['Radius'].default_value = radius
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    vm = nt.nodes.new('ShaderNodeVectorMath')
    vm.operation = 'DOT_PRODUCT'
    nt.links.new(bv.outputs['Normal'], vm.inputs[0])
    nt.links.new(geo.outputs['Normal'], vm.inputs[1])
    return mrange(nt, op(nt, 'SUBTRACT', 1.0, vm.outputs['Value']), lo, hi)


def cavity(nt, dist=0.04, lo=0.55, hi=1.0):
    """0 = 오목한 구석(때), 1 = 트인 곳."""
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao.only_local, ao.samples = True, 16
    ao.inputs['Distance'].default_value = dist
    return mrange(nt, ao.outputs['AO'], lo, hi)


def bump(nt, height, strength=0.2, dist=0.001, normal=None):
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = dist
    _set(b.inputs['Height'], height)
    if normal is not None:
        nt.links.new(normal, b.inputs['Normal'])
    return b.outputs['Normal']


def ph_tex(nt, ph_id, scale_m, which=('diff', 'rough'), res="1k", vec=None, blend=0.2):
    """Poly Haven 텍스처를 오브젝트 좌표 박스 투영으로 (UV 불필요)."""
    maps = k3d.polyhaven(ph_id, res)
    if vec is None:
        vec = coord(nt, 'Object', (1 / scale_m,) * 3)
    out = {}
    for w in which:
        if w not in maps:
            continue
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = k3d.load_image(maps[w], non_color=(w != 'diff'))
        n.projection, n.projection_blend = 'BOX', blend
        nt.links.new(vec, n.inputs['Vector'])
        out[w] = n.outputs['Color']
    return out


# ------------------------------------------------------------ 머티리얼 레시피

def powder_coat(name, color, rough=0.5, wear=0.5, metal_col=(0.42, 0.42, 0.43), grime=0.6, edge_r=0.003,
                scratch=0.4, peel=0.05):
    """분체도장 금속: 색 얼룩, 구석 때, 모서리 칠 벗겨짐(금속 노출), 잔긁힘."""
    m, nt, p = new_mat(name)
    v = coord(nt)
    var = mrange(nt, noise(nt, 6, 3, vec=v), 0.3, 0.7, 0.9, 1.08)
    base = mix(nt, 1.0, color, op(nt, 'MULTIPLY', var, 1.0), 'MULTIPLY')
    cav = cavity(nt, 0.03)
    g = op(nt, 'MULTIPLY', op(nt, 'SUBTRACT', 1.0, cav), grime)
    base = mix(nt, g, base, (0.035, 0.03, 0.025))
    # 긁힘: 늘린 노이즈의 가는 선
    sv = coord(nt, 'Object', (3, 3, 120))
    sc = mrange(nt, noise(nt, 30, 2, vec=sv), 0.62, 0.66)
    sc = op(nt, 'MULTIPLY', sc, mrange(nt, noise(nt, 4, 2, vec=v), 0.5, 0.65))
    sc = op(nt, 'MULTIPLY', sc, scratch)
    # 모서리 마모
    e = edge_mask(nt, edge_r)
    wm = op(nt, 'MULTIPLY', e, mrange(nt, noise(nt, 45, 6, 0.6, vec=v), 0.38, 0.62))
    wm = op(nt, 'MULTIPLY', wm, wear, clamp=True)
    wm = op(nt, 'MAXIMUM', wm, sc)
    wm = op(nt, 'MAXIMUM', wm, op(nt, 'MULTIPLY', mrange(nt, noise(nt, 18, 5, 0.65, vec=v), 0.66, 0.7), peel))
    base = mix(nt, wm, base, metal_col)
    nt.links.new(base, p.inputs['Base Color'])
    nt.links.new(fmix(nt, wm, 0.0, 1.0), p.inputs['Metallic'])
    r = op(nt, 'ADD', rough, op(nt, 'MULTIPLY', mrange(nt, noise(nt, 9, 3, vec=v), 0.3, 0.7), 0.12))
    r = fmix(nt, g, r, 0.8)
    nt.links.new(fmix(nt, wm, r, 0.32), p.inputs['Roughness'])
    h = op(nt, 'ADD', op(nt, 'MULTIPLY', noise(nt, 900, 2, vec=v), 0.3), op(nt, 'MULTIPLY', wm, -0.4))
    nt.links.new(bump(nt, h, 0.12, 0.0006), p.inputs['Normal'])
    return m


def stainless(name, rough=0.3, axis='X', smudge=0.6, grime=0.6, tint=(0.62, 0.62, 0.6)):
    """헤어라인 스테인리스: 결 방향 줄무늬, 지문/물자국, 구석 때."""
    m, nt, p = new_mat(name)
    st = {'X': (2, 400, 400), 'Y': (400, 2, 400), 'Z': (400, 400, 2)}[axis]
    v = coord(nt)
    sv = coord(nt, 'Object', st)
    streak = noise(nt, 1.0, 3, 0.7, vec=sv)
    base = mix(nt, 1.0, tint, op(nt, 'ADD', 0.88, op(nt, 'MULTIPLY', streak, 0.2)), 'MULTIPLY')
    cav = cavity(nt, 0.025)
    g = op(nt, 'MULTIPLY', op(nt, 'SUBTRACT', 1.0, cav), grime)
    base = mix(nt, g, base, (0.08, 0.07, 0.055))
    nt.links.new(base, p.inputs['Base Color'])
    p.inputs['Metallic'].default_value = 1.0
    sm = op(nt, 'MULTIPLY', mrange(nt, noise(nt, 14, 6, 0.7, vec=v, distortion=0.6), 0.52, 0.66), smudge)
    fp = op(nt, 'MULTIPLY', mrange(nt, voronoi(nt, 90, v), 0.0, 0.25, 1.0, 0.0),
            mrange(nt, noise(nt, 7, 2, vec=v), 0.55, 0.62))
    sm = op(nt, 'MAXIMUM', sm, op(nt, 'MULTIPLY', fp, smudge * 0.8))
    r = op(nt, 'ADD', rough, op(nt, 'MULTIPLY', streak, 0.1))
    r = op(nt, 'ADD', r, op(nt, 'MULTIPLY', sm, 0.22))
    nt.links.new(fmix(nt, g, r, 0.75), p.inputs['Roughness'])
    nt.links.new(bump(nt, streak, 0.04, 0.0003), p.inputs['Normal'])
    return m


def wood(name, scale_m=0.7, tint=(1, 1, 1), rough=0.42, ph_id="oak_veneer_01", wipe=0.5, wear=0.4,
         edge_dark=0.3, scratch=0.3):
    """우드 라미네이트(HPL): 실사 결 + 닦인 자국 광택 + 모서리 손때 + 잔긁힘."""
    m, nt, p = new_mat(name)
    t = ph_tex(nt, ph_id, scale_m)
    v = coord(nt)
    base = mix(nt, 1.0, t['diff'], tint, 'MULTIPLY')
    var = mrange(nt, noise(nt, 2.5, 3, vec=v), 0.3, 0.7, 0.92, 1.06)
    base = mix(nt, 1.0, base, op(nt, 'MULTIPLY', var, 1.0), 'MULTIPLY')
    e = edge_mask(nt, 0.004)
    cav = cavity(nt, 0.03)
    g = op(nt, 'SUBTRACT', 1.0, cav)
    dirt = op(nt, 'MAXIMUM', op(nt, 'MULTIPLY', e, edge_dark), op(nt, 'MULTIPLY', g, 0.5))
    base = mix(nt, dirt, base, (0.07, 0.05, 0.035))
    sv = coord(nt, 'Object', (60, 60, 2))
    sc = op(nt, 'MULTIPLY', mrange(nt, noise(nt, 6, 2, vec=sv), 0.63, 0.67),
            mrange(nt, noise(nt, 3, 2, vec=v), 0.5, 0.7))
    sc = op(nt, 'MULTIPLY', sc, scratch)
    base = mix(nt, sc, base, (0.55, 0.45, 0.34))
    nt.links.new(base, p.inputs['Base Color'])
    wp = mrange(nt, noise(nt, 3.5, 4, 0.6, vec=v, distortion=1.2), 0.45, 0.6)
    r = op(nt, 'ADD', op(nt, 'MULTIPLY', t.get('rough', 0.5), 0.35), rough * 0.75)
    r = fmix(nt, op(nt, 'MULTIPLY', wp, wipe), r, rough * 0.55)
    r = fmix(nt, op(nt, 'MULTIPLY', e, wear), r, rough + 0.2)
    nt.links.new(r, p.inputs['Roughness'])
    lum = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(t['diff'], lum.inputs[0])
    h = op(nt, 'SUBTRACT', lum.outputs[0], op(nt, 'MULTIPLY', sc, 0.5))
    nt.links.new(bump(nt, h, 0.08, 0.0008), p.inputs['Normal'])
    return m


def plastic(name, color, rough=0.45, grime=0.6, wear=0.3, scuff=0.3, fade=0.0, edge_col=None):
    """사출 플라스틱: 색 얼룩, 구석 때, 모서리 하얗게 긁힘, 잔흠집, 미세 텍스처."""
    m, nt, p = new_mat(name)
    v = coord(nt)
    var = mrange(nt, noise(nt, 5, 3, vec=v), 0.3, 0.7, 0.93, 1.06)
    base = mix(nt, 1.0, color, op(nt, 'MULTIPLY', var, 1.0), 'MULTIPLY')
    if fade:
        base = mix(nt, op(nt, 'MULTIPLY', mrange(nt, noise(nt, 1.5, 2, vec=v), 0.3, 0.7), fade), base, (0.85, 0.85, 0.8))
    cav = cavity(nt, 0.03)
    g = op(nt, 'MULTIPLY', op(nt, 'SUBTRACT', 1.0, cav), grime)
    base = mix(nt, g, base, (0.04, 0.035, 0.03))
    e = edge_mask(nt, 0.003)
    wm = op(nt, 'MULTIPLY', op(nt, 'MULTIPLY', e, mrange(nt, noise(nt, 40, 5, vec=v), 0.4, 0.62)), wear, clamp=True)
    sv = coord(nt, 'Object', (5, 5, 90))
    sc = op(nt, 'MULTIPLY', mrange(nt, noise(nt, 20, 2, vec=sv), 0.63, 0.67),
            mrange(nt, noise(nt, 4, 2, vec=v), 0.5, 0.68))
    wm = op(nt, 'MAXIMUM', wm, op(nt, 'MULTIPLY', sc, scuff))
    base = mix(nt, wm, base, edge_col or tuple(min(1, c * 1.5 + 0.12) for c in color))
    nt.links.new(base, p.inputs['Base Color'])
    r = op(nt, 'ADD', rough, op(nt, 'MULTIPLY', mrange(nt, noise(nt, 8, 3, vec=v), 0.3, 0.7), 0.1))
    r = fmix(nt, g, r, 0.85)
    nt.links.new(fmix(nt, wm, r, rough + 0.25), p.inputs['Roughness'])
    h = op(nt, 'ADD', op(nt, 'MULTIPLY', noise(nt, 600, 2, vec=v), 0.25), op(nt, 'MULTIPLY', sc, -0.5))
    nt.links.new(bump(nt, h, 0.1, 0.0005), p.inputs['Normal'])
    return m


def rubber(name, color=(0.025, 0.025, 0.025), rough=0.82):
    m, nt, p = new_mat(name)
    v = coord(nt)
    base = mix(nt, mrange(nt, noise(nt, 30, 4, vec=v), 0.4, 0.7), color, tuple(c * 2.2 + 0.02 for c in color))
    nt.links.new(base, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    nt.links.new(bump(nt, noise(nt, 400, 2, vec=v), 0.15, 0.0005), p.inputs['Normal'])
    return m


def label_mat(name, png, rough=0.45, img_name=None, double_sided=False):
    """Pillow 텍스처를 Base Color 에 바로 연결한 라벨 머티리얼 (bake 에서 keep)."""
    m, nt, p = new_mat(name)
    im = k3d.load_image(png, img_name or os.path.splitext(os.path.basename(png))[0])
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = im
    nt.links.new(n.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    if double_sided:
        k3d.flag(m, double_sided=True)
    return m


def draw_labels(asset):
    """labels.py(Pillow)로 T_<asset>_Label.png 를 텍스처 폴더에 그린다."""
    out = os.path.join(k3d.ART, "Textures", asset, f"T_{asset}_Label.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run([PY, "-I", os.path.join(HERE, "labels.py"), asset, out], check=True)
    return out


def scene_tris(objs):
    t = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in k3d.tree_of(objs):
        if o.type == 'MESH':
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            t += len(me.loop_triangles)
    return t

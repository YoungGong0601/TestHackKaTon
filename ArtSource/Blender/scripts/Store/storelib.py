"""매장(store_arch) 그룹 공용 도우미: 베벨 박스/실린더, 절차 머티리얼(얼룩·때·모서리 마모), 이미지 머티리얼, 실내 카메라 렌더.

좌표 규칙
- 프로토타입(three.js, Y-up) -> 블렌더 매장 좌표: P(x, y, z) = (x, -z, y). 매장 정면(유리문 쪽) = 블렌더 -Y.
- 블렌더 -> Unity: (x, y, z) -> (-x, z, -y). 즉 Unity = (-x_proto, y_proto, z_proto).
"""
import bpy, bmesh, math, os, sys, subprocess
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import k3d  # noqa: E402

TEX = os.path.join(k3d.CACHE, "store_tex")          # Pillow 로 그린 원본 이미지 (캐시)
VENV_PY = os.path.join(k3d.CACHE, "venv", "bin", "python")

# 레이아웃 상수 (프로토타입 pe)
X0, X1, Z0, FRONT, H = -6.0, 5.5, -4.2, 3.8, 3.1
DOOR_L, DOOR_R, DOOR_H = 0.9, 1.9, 2.3
COUNTER_X, COUNTER_END = -2.6, 1.7
STAFF = (-3.72, 0, -2.5)
PICK = (-2.92, 1.08, 0.85)
BOARD = (-2.72, 2.62, 0.9)


def P(x, y, z):
    """프로토타입 좌표 -> 블렌더 매장 좌표."""
    return Vector((x, -z, y))


def textures():
    """Pillow 텍스처를 (없으면) 생성하고 폴더 경로를 돌려준다."""
    stamp = os.path.join(TEX, ".done")
    src = os.path.join(HERE, "store_tex.py")
    if not os.path.exists(stamp) or os.path.getmtime(stamp) < os.path.getmtime(src):
        subprocess.run([VENV_PY, src, TEX], check=True)
    return TEX


def tex(name):
    return os.path.join(textures(), name)


# ---------------------------------------------------------------- mesh

def link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


def obj_from_bm(name, bm, loc=(0, 0, 0), rot=None, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.location = loc
    if rot:
        o.rotation_euler = rot
    if mat:
        me.materials.append(mat)
    return o


def bevel(o, w=0.004, seg=2, angle=35):
    """베벨 + 단단한 노멀 + 가중 노멀."""
    for p in o.data.polygons:
        p.use_smooth = True
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width, m.segments = w, seg
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = True
    m.miter_outer = 'MITER_ARC'
    wn = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    return o


def box(name, size, loc=(0, 0, 0), mat=None, bev=0.004, seg=2, rot=None):
    """중심 기준 박스 (size = x,y,z 미터)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = obj_from_bm(name, bm, loc, rot, mat)
    if bev:
        bevel(o, min(bev, min(size) * 0.45), seg)
    return o


def boxz(name, x0, x1, y0, y1, z0, z1, mat=None, bev=0.004, seg=2):
    """범위로 지정하는 박스."""
    return box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), mat, bev, seg)


def cyl(name, r, h, loc=(0, 0, 0), mat=None, n=24, bev=0.002, seg=2, rot=None, r2=None, caps=True):
    """Z 축 실린더 (중심 기준). r2 를 주면 원뿔대."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=n, radius1=r,
                          radius2=r if r2 is None else r2, depth=h, calc_uvs=True)
    o = obj_from_bm(name, bm, loc, rot, mat)
    if bev:
        bevel(o, min(bev, r * 0.3, h * 0.3), seg)
    return o


def atlas_uv(atlas, key):
    """store_tex.py 아틀라스의 UV 사각형 (u0, v0, u1, v1)."""
    for line in open(tex(atlas) + ".uv"):
        k, *r = line.split()
        if k == key:
            return tuple(float(v) for v in r)
    raise KeyError(key)


def quad(name, w, h, loc=(0, 0, 0), mat=None, rot=(math.pi / 2, 0, 0), uv=(0, 0, 1, 1)):
    """정면(-Y)을 보는 사각 판 (UV 0-1 또는 아틀라스 사각형, U 오른쪽 / V 위). 기본 회전 = XZ 평면."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x, y, 0)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    u0, v0, u1, v1 = uv
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[uvl].uv = c
    o = obj_from_bm(name, bm, loc, rot, mat)
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def floor_quad(name, w, h, loc, mat, uv=(0, 0, 1, 1)):
    """바닥에 눕힌 판 (위를 봄, V = +Y)."""
    return quad(name, w, h, loc, mat, rot=(0, 0, 0), uv=uv)


def apply_tf(o):
    k3d.select([o])
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def join(objs, name):
    """k3d.join 래퍼 (빈 목록 무시)."""
    objs = [o for o in objs if o]
    if len(objs) == 1:
        k3d.apply_all(objs[0])
        objs[0].name = objs[0].data.name = name
        return objs[0]
    return k3d.join(objs, name)


def empty(name, loc, parent=None, size=0.05):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = size
    link(e)
    e.location = loc
    if parent:
        reparent(e, parent)
    return e


def reparent(child, parent):
    """월드 위치 유지하며 부모 지정."""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw


def set_origin(o, p):
    k3d.set_origin(o, Vector(p))


# ---------------------------------------------------------------- materials

def _n(nt, kind, loc=(0, 0), **kw):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _mix(nt, a, b, fac, mode='MIX'):
    m = nt.nodes.new('ShaderNodeMix')
    m.data_type, m.blend_type = 'RGBA', mode
    m.clamp_result = True
    _sock(nt, a, m.inputs[6])
    _sock(nt, b, m.inputs[7])
    _sock(nt, fac, m.inputs[0])
    return m.outputs[2]


def _sock(nt, v, inp):
    if hasattr(v, "is_linked") or hasattr(v, "links"):
        nt.links.new(v, inp)
    elif isinstance(v, (int, float)):
        inp.default_value = v
    else:
        inp.default_value = (*v[:3], 1) if len(inp.default_value) == 4 else v


def _math(nt, op, a, b=None, clamp=True):
    m = nt.nodes.new('ShaderNodeMath')
    m.operation = op
    m.use_clamp = clamp
    _sock(nt, a, m.inputs[0])
    if b is not None:
        _sock(nt, b, m.inputs[1])
    return m.outputs[0]


def _noise(nt, coord, scale, detail=6.0, rough=0.55, dist=0.0):
    t = nt.nodes.new('ShaderNodeTexNoise')
    t.inputs['Scale'].default_value = scale
    t.inputs['Detail'].default_value = detail
    t.inputs['Roughness'].default_value = rough
    t.inputs['Distortion'].default_value = dist
    nt.links.new(coord, t.inputs['Vector'])
    return t.outputs['Fac']


def _ramp(nt, v, a, b):
    """v 를 [a,b] -> [0,1] 로."""
    m = nt.nodes.new('ShaderNodeMapRange')
    m.clamp = True
    nt.links.new(v, m.inputs['Value'])
    m.inputs['From Min'].default_value = a
    m.inputs['From Max'].default_value = b
    return m.outputs['Result']


def pbr(name, color, rough=0.5, metal=0.0, *, var=0.10, vscale=6.0, grime=0.35, grime_col=(0.05, 0.04, 0.03),
        gdist=0.06, edge=0.0, edge_col=None, bump=0.12, bscale=90.0, rvar=0.18, scratch=0.0, smudge=0.0,
        streak=0.0, emission=None, estr=0.0, coat=None, img=None, img_m=1.0, brush=0.0):
    """절차 PBR (굽기용). 색은 linear.
    var: 색 얼룩 · grime: 틈새 때(AO) · edge: 볼록 모서리 마모 · scratch: 긁힘 · smudge: 손자국(거칠기) · streak: 세로 흘러내린 때."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = _n(nt, 'ShaderNodeOutputMaterial', (900, 0))
    p = _n(nt, 'ShaderNodeBsdfPrincipled', (600, 0))
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord', (-1200, 0)).outputs['Object']
    col = tuple(color[:3])
    dark = tuple(c * (1 - var) for c in col)
    lite = tuple(min(1, c * (1 + var * 0.7)) for c in col)
    n1 = _noise(nt, tc, vscale, 8, 0.6)
    n2 = _noise(nt, tc, vscale * 0.23, 4, 0.5)
    base = _mix(nt, dark, lite, _math(nt, 'MULTIPLY', _math(nt, 'ADD', n1, n2, False), 0.5))
    if img:  # 실사 스캔 텍스처 (오브젝트 좌표 박스 투영, img_m = 텍스처 1장의 실제 크기 m)
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1 / img_m,) * 3
        nt.links.new(tc, mp.inputs['Vector'])
        ti = nt.nodes.new('ShaderNodeTexImage')
        ti.image = k3d.load_image(img)
        ti.projection, ti.projection_blend = 'BOX', 0.25
        nt.links.new(mp.outputs[0], ti.inputs['Vector'])
        base = _mix(nt, ti.outputs['Color'], col, 1.0, 'MULTIPLY')
    rgh = _math(nt, 'ADD', rough - rvar * 0.5, _math(nt, 'MULTIPLY', n1, rvar))
    if brush > 0:  # 헤어라인(브러시드) 결: X 방향으로 길게
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (2.0, 260.0, 260.0)
        nt.links.new(tc, mp.inputs['Vector'])
        bn = _noise(nt, mp.outputs[0], 1.0, 4, 0.6)
        rgh = _math(nt, 'ADD', rgh, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', bn, 0.5, False), brush), False)
        base = _mix(nt, base, tuple(min(1, c * 1.12) for c in col), _math(nt, 'MULTIPLY', bn, brush * 0.8))
    if grime > 0:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ao.samples = 16
        ao.only_local = True
        ao.inputs['Distance'].default_value = gdist
        cav = _math(nt, 'POWER', _math(nt, 'SUBTRACT', 1.0, ao.outputs['AO']), 0.8)
        gmask = _math(nt, 'MULTIPLY', cav, _ramp(nt, _noise(nt, tc, 14, 6, 0.65), 0.3, 0.7))
        gmask = _math(nt, 'MULTIPLY', _math(nt, 'ADD', gmask, _math(nt, 'MULTIPLY', cav, 0.5)), grime)
        base = _mix(nt, base, grime_col, gmask)
        rgh = _math(nt, 'ADD', rgh, _math(nt, 'MULTIPLY', gmask, 0.3))
    if streak > 0:
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (14, 14, 0.6)
        nt.links.new(tc, mp.inputs['Vector'])
        s = _ramp(nt, _noise(nt, mp.outputs[0], 3, 3, 0.5), 0.55, 0.8)
        base = _mix(nt, base, grime_col, _math(nt, 'MULTIPLY', s, streak))
    if edge > 0:
        ae = nt.nodes.new('ShaderNodeAmbientOcclusion')
        ae.samples = 16
        ae.only_local = True
        ae.inside = True
        ae.inputs['Distance'].default_value = 0.012
        emask = _ramp(nt, _math(nt, 'SUBTRACT', 1.0, ae.outputs['AO']), 0.25, 0.65)
        emask = _math(nt, 'MULTIPLY', emask, _ramp(nt, _noise(nt, tc, 40, 8, 0.7), 0.35, 0.6))
        emask = _math(nt, 'MULTIPLY', emask, edge)
        base = _mix(nt, base, edge_col or tuple(min(1, c * 1.6 + 0.08) for c in col), emask)
        rgh = _math(nt, 'SUBTRACT', rgh, _math(nt, 'MULTIPLY', emask, 0.2))
    if scratch > 0:
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1, 1, 1)
        nt.links.new(tc, mp.inputs['Vector'])
        w = nt.nodes.new('ShaderNodeTexWave')
        w.wave_type = 'BANDS'
        w.inputs['Scale'].default_value = 60
        w.inputs['Distortion'].default_value = 25
        w.inputs['Detail'].default_value = 4
        nt.links.new(mp.outputs[0], w.inputs['Vector'])
        sm = _math(nt, 'MULTIPLY', _ramp(nt, w.outputs['Fac'], 0.93, 1.0),
                   _ramp(nt, _noise(nt, tc, 5, 2, 0.5), 0.45, 0.65))
        sm = _math(nt, 'MULTIPLY', sm, scratch)
        base = _mix(nt, base, tuple(min(1, c * 1.35 + 0.05) for c in col), sm)
        rgh = _math(nt, 'ADD', rgh, _math(nt, 'MULTIPLY', sm, 0.25))
    if smudge > 0:
        v = nt.nodes.new('ShaderNodeTexVoronoi')
        v.inputs['Scale'].default_value = 26
        v.inputs['Randomness'].default_value = 1
        nt.links.new(tc, v.inputs['Vector'])
        sm = _math(nt, 'MULTIPLY', _ramp(nt, v.outputs['Distance'], 0.25, 0.05),
                   _ramp(nt, _noise(nt, tc, 3, 2, 0.5), 0.45, 0.7))
        rgh = _math(nt, 'ADD', rgh, _math(nt, 'MULTIPLY', sm, smudge))
    nt.links.new(base, p.inputs['Base Color'])
    nt.links.new(rgh, p.inputs['Roughness'])
    p.inputs['Metallic'].default_value = metal
    if bump > 0:
        b = nt.nodes.new('ShaderNodeBump')
        b.inputs['Strength'].default_value = bump
        b.inputs['Distance'].default_value = 0.002
        nt.links.new(_noise(nt, tc, bscale, 8, 0.6), b.inputs['Height'])
        nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[:3], 1)
        p.inputs['Emission Strength'].default_value = estr
    else:  # Blender 5 기본 발광색이 흰색이라, 발광 재질과 합쳐 구우면 전체가 하얗게 빛난다 -> 검정으로
        p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    if coat:
        p.inputs['Coat Weight'].default_value = coat
    return m


def img_mat(name, path, rough=0.45, emit=0.0, metal=0.0, alpha_clip=None, uv=None):
    """이미지 머티리얼 (굽지 않고 그대로 내보낼 것: 글자/포스터/화면용). emit>0 이면 같은 이미지로 발광."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = _n(nt, 'ShaderNodeOutputMaterial', (600, 0))
    p = _n(nt, 'ShaderNodeBsdfPrincipled', (300, 0))
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    im = k3d.load_image(path)
    t = k3d.image_node(m, im, p.inputs['Base Color'], uv=uv)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit > 0:
        nt.links.new(t.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emit
    if alpha_clip is not None:
        nt.links.new(t.outputs['Alpha'], p.inputs['Alpha'])
        k3d.flag(m, alpha_clip=alpha_clip)
    return m


def img_in_pbr(m, path, uv="UVMap"):
    """굽는 pbr 머티리얼의 Base Color 를 이미지로 교체 (라벨이 붙은 부품용, 이미지 UV 고정)."""
    nt = m.node_tree
    p = k3d.principled(m)
    k3d.image_node(m, k3d.load_image(path), p.inputs['Base Color'], uv=uv)
    return m


# ---------------------------------------------------------------- render

def shot(name, cam, target, lens=24, res=(1280, 800), lights=(), world=(0.5, 0.5, 0.52), wstr=0.6, exposure=0.0):
    """실내 1인칭 렌더 -> ArtSource/Previews/<name>.png. lights = [(loc, energy, size, color)] 면광원(아래를 봄)."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = exposure
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except Exception:
        pass
    w = bpy.data.worlds.new("shot_world")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (*world, 1)
    bg.inputs['Strength'].default_value = wstr
    sc.world = w
    tmp = []
    for loc, energy, size, colr in lights:
        ld = bpy.data.lights.new("shot_l", 'AREA')
        ld.energy, ld.size, ld.color = energy, size, colr
        lo = link(bpy.data.objects.new("shot_l", ld))
        lo.location = loc
        tmp.append(lo)
    cd = bpy.data.cameras.new("shot_cam")
    cd.lens = lens
    cd.clip_start = 0.05
    co = link(bpy.data.objects.new("shot_cam", cd))
    co.location = cam
    co.rotation_euler = (Vector(target) - Vector(cam)).to_track_quat('-Z', 'Y').to_euler()
    tmp.append(co)
    sc.camera = co
    pdir = os.path.join(k3d.SRC, "Previews")
    os.makedirs(pdir, exist_ok=True)
    path = os.path.join(pdir, name + ".png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    print("store: shot", path)
    return path

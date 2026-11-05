# Storefront 그룹 공용 도우미: 베벨 박스·원기둥·파이프·글자 메시 + 굽기용 절차 머티리얼.
import os, sys, math, subprocess
import bpy, bmesh
from mathutils import Vector, Matrix

sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts')
import k3d

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/_cache/venv/bin/python'
FONT = '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/_cache/fonts/'
TEXDIR = os.path.join(k3d.ART, "Textures")

# 유리문 힌지 축·클로저 슈 (door.py·facade.py 공용). 문짝 제작 좌표: 힌지 쪽 문틀 면 x=0, 문 두께 중심 y=0.
# 축 = 맞경첩 너클 중심: 문틀 면에서 0.5mm, 문 거리 쪽 면(-0.025)보다 1mm 바깥 → 열 때 문짝이 문틀을 파고들지 않는다.
DOOR_AX, DOOR_AY = 0.007, -0.026
DOOR_SHOE = (0.31, -0.064, 2.304)    # 클로저 전완 끝 슈 조인트 (헤더 앞면 브래킷 축, 문짝 위 끝 2.28m 보다 위)


def textures(which):
    """tex.py(Pillow) 로 2D 텍스처를 다시 만든다."""
    env = dict(os.environ, K3D_ROOT=k3d.REPO)
    subprocess.run([VENV, os.path.join(HERE, "tex.py"), which], check=True, env=env)


def tex(asset, name):
    for ext in (".png", ".jpg"):
        p = os.path.join(TEXDIR, asset, f"T_{asset}_{name}{ext}")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


# ---------------------------------------------------------------- 메시
def _obj(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def finish(o, bev=0.0, seg=2, angle=40, wn=True):
    """베벨 + 스무스 + 가중 노멀 (단단한 표면 기본)."""
    for p in o.data.polygons:
        p.use_smooth = True
    if bev:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width, m.segments, m.limit_method = bev, seg, 'ANGLE'
        m.angle_limit = math.radians(angle)
        m.miter_outer = 'MITER_ARC'
    if wn:
        w = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
        w.keep_sharp = True
        w.weight = 100
    return o


def box(name, size, loc, mat=None, bev=0.002, seg=2, rot=(0, 0, 0)):
    """size=(x,y,z) 미터, loc=중심."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    sx, sy, sz = size
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    o = _obj(name, bm, mat)
    o.location, o.rotation_euler = loc, rot
    return finish(o, bev, seg)


def box2(a, b, mat=None, bev=0.002, seg=2, name="Part"):
    """두 모서리 점 a,b 로 박스."""
    c = [(a[i] + b[i]) / 2 for i in range(3)]
    s = [abs(b[i] - a[i]) for i in range(3)]
    return box(name, s, c, mat, bev, seg)


def cyl(name, r, h, loc, mat=None, rot=(0, 0, 0), n=24, bev=0.0015, seg=2, r2=None):
    """Z 축 원기둥 (loc=중심). r2 를 주면 원뿔대."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = _obj(name, bm, mat)
    o.location, o.rotation_euler = loc, rot
    return finish(o, bev, seg)


def sphere(name, r, loc, mat=None, n=16, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=n, v_segments=max(6, n // 2), radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    o = _obj(name, bm, mat)
    o.location = loc
    return finish(o, 0)


def quad(name, w, h, loc, mat=None, face="-Y", uv=(0, 0, 1, 1)):
    """UV 0..1 이 똑바로 보이는 사각형 (face 쪽에서 볼 때 U→오른쪽, V→위)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = uv
    for l, t in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[uvl].uv = t
    o = _obj(name, bm, mat)
    o.location = loc
    o.rotation_euler = {"-Y": (0, 0, 0), "+Y": (0, 0, math.pi), "-X": (0, 0, -math.pi / 2),
                        "+X": (0, 0, math.pi / 2), "+Z": (-math.pi / 2, 0, 0), "-Z": (math.pi / 2, 0, 0)}[face]
    return o


def fillet(pts, r, n=6):
    """꺾인 선의 모서리를 반경 r 로 둥글게 (파이프 굽힘)."""
    pts = [Vector(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1, d2 = (a - b).normalized(), (c - b).normalized()
        ang = d1.angle(d2)
        if ang > math.pi - 1e-3:
            out.append(b)
            continue
        t = min(r / math.tan(ang / 2), (a - b).length * 0.45, (c - b).length * 0.45)
        p1, p2 = b + d1 * t, b + d2 * t
        for k in range(n + 1):
            s = k / n  # 2차 베지어로 근사
            out.append((1 - s) ** 2 * p1 + 2 * (1 - s) * s * b + s * s * p2)
    out.append(pts[-1])
    return out


def pipe(name, pts, r, mat=None, n=12, bend=0.0, caps=True):
    """점 목록을 따라가는 관 (bend>0 이면 굽힘 반경)."""
    if bend:
        pts = fillet(pts, bend)
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution = r, max(1, n // 4 - 1)
    cu.use_fill_caps = caps
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    return to_mesh(o, mat)


def to_mesh(o, mat=None):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    name, mw = o.name, o.matrix_world.copy()
    cu = o.data
    bpy.data.objects.remove(o)
    if isinstance(cu, bpy.types.Curve):
        bpy.data.curves.remove(cu)
    n = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(n)
    n.matrix_world = mw
    me.materials.clear()
    if mat:
        me.materials.append(mat)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        p.use_smooth = True
    return n


def text(name, s, size, depth, font="BlackHanSans-Regular.ttf", bevel=0.0, res=3, align="CENTER", spacing=1.0):
    """글자 메시 (XZ 평면, 정면 -Y, 두께 depth 를 y=-depth..0 으로). 원점=글자 가운데 아래."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = s
    cu.font = bpy.data.fonts.load(FONT + font if not font.startswith("/") else font, check_existing=True)
    cu.size, cu.extrude, cu.resolution_u = size, depth / 2, res
    cu.bevel_depth, cu.bevel_resolution = bevel, 1
    cu.align_x, cu.align_y = align, 'BOTTOM_BASELINE'
    cu.space_character = spacing
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.location = (0, -depth / 2, 0)
    n = to_mesh(o)
    k3d.select([n])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return n


def mat_by_normal(o, front_mat, side_mat, rim_mat=None, axis=(0, -1, 0), thr=0.97):
    """정면(axis 쪽) 면 = front_mat, 테두리(비스듬) = rim_mat, 나머지 = side_mat."""
    me = o.data
    me.materials.clear()
    mats = [front_mat, side_mat] + ([rim_mat] if rim_mat else [])
    for m in mats:
        me.materials.append(m)
    ax = Vector(axis)
    for p in me.polygons:
        d = p.normal.dot(ax)
        p.material_index = 0 if d > thr else (2 if rim_mat and d > 0.25 else 1)


def poly_extrude(name, pts2d, depth, mat=None, loc=(0, 0, 0)):
    """XZ 평면의 2D 다각형을 -Y 쪽으로 depth 만큼 돌출 (정면이 y=-depth)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in pts2d]
    f = bm.faces.new(vs)
    if f.normal.y > 0:
        f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.y -= depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    o = _obj(name, bm, mat)
    o.location = loc
    return finish(o, 0)


def ellipse_pts(cx, cz, rx, rz, a0=0, a1=2 * math.pi, n=24):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cz + rz * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rrect_pts(x0, z0, x1, z1, r, n=4):
    pts = []
    for cx, cz, a in ((x1 - r, z0 + r, -math.pi / 2), (x1 - r, z1 - r, 0), (x0 + r, z1 - r, math.pi / 2), (x0 + r, z0 + r, math.pi)):
        for i in range(n + 1):
            t = a + (math.pi / 2) * i / n
            pts.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    return pts


def join(objs, name):
    objs = [o for o in objs if o]
    for o in objs:
        k3d.select([o])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o = k3d.join(objs, name)
    return o


def empty(name, loc, parent=None, size=0.05):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', size
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


# ---------------------------------------------------------------- 머티리얼 (굽기용 절차)
def _n(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _mix(nt, fac, a, b, blend='MIX'):
    m = _n(nt, 'ShaderNodeMixRGB', blend_type=blend)
    for sock, v in ((m.inputs['Factor'], fac), (m.inputs['Color1'], a), (m.inputs['Color2'], b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, sock)
        elif isinstance(v, (int, float)):
            sock.default_value = v
        else:
            sock.default_value = (*v[:3], 1)
    return m.outputs['Color']


def _math(nt, op, a, b=None, clamp=True):
    m = _n(nt, 'ShaderNodeMath', operation=op, use_clamp=clamp)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, m.inputs[i])
        else:
            m.inputs[i].default_value = v
    return m.outputs[0]


def _vary(nt, col, n, amt):
    """col × (1 + (n-0.5)·2·amt) — 밝기 얼룩."""
    g = _math(nt, 'ADD', 1.0, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', n, 0.5, clamp=False), amt * 2, clamp=False), clamp=False)
    return _mix(nt, 1.0, col, g, 'MULTIPLY')


def _noise(nt, scale, detail=4.0, stretch=(1, 1, 1), coord=None, rough=0.55):
    tc = coord or _n(nt, 'ShaderNodeTexCoord').outputs['Object']
    if stretch != (1, 1, 1):
        mp = _n(nt, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = stretch
        nt.links.new(tc, mp.inputs['Vector'])
        tc = mp.outputs['Vector']
    n = _n(nt, 'ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    nt.links.new(tc, n.inputs['Vector'])
    return n.outputs['Factor']


def _ramp(nt, x, lo, hi):
    m = _n(nt, 'ShaderNodeMapRange')
    nt.links.new(x, m.inputs['Value'])
    m.inputs['From Min'].default_value, m.inputs['From Max'].default_value = lo, hi
    return m.outputs['Result']


def pbr(name, color, rough=0.5, metal=0.0, var=0.12, var_scale=6.0, streak=None, grime=0.35, grime_col=(0.03, 0.025, 0.02),
        grime_dist=0.04, edge=0.0, edge_col=None, bottom=0.0, bottom_h=0.25, scratch=0.0, bump=0.15, bump_scale=120.0,
        fade=0.0, rough_var=0.15, smudge=0.0, emission=None, strength=0.0, image=None):
    """사실적 기본 머티리얼: 색 변화·줄결(streak 축)·틈 때(AO)·모서리 마모(Bevel)·아래 먼지·스크래치·햇빛 바램·손때.
    color 는 linear RGB. 결과는 Principled 하나 → k3d.bake 로 굽는다."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = k3d._nodes(m)
    nt.nodes.clear()
    p = _n(nt, 'ShaderNodeBsdfPrincipled')
    out = _n(nt, 'ShaderNodeOutputMaterial')
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    tc = _n(nt, 'ShaderNodeTexCoord')
    obj_co = tc.outputs['Object']
    # 기본 색 + 저주파 변화
    if image:
        im = _n(nt, 'ShaderNodeTexImage')
        im.image = k3d.load_image(image)
        col = im.outputs['Color']
    else:
        col = color
    if var:
        col = _vary(nt, col, _noise(nt, var_scale, 3.0, coord=obj_co), var)
    rough_s = None
    if streak:  # 브러시/압출 줄결
        st = {'X': (2, 160, 160), 'Y': (160, 2, 160), 'Z': (160, 160, 2)}[streak]
        sn = _noise(nt, 3.0, 6.0, st, coord=obj_co, rough=0.7)
        col = _vary(nt, col, sn, 0.12)
        rough_s = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', sn, 0.5, clamp=False), 0.25, clamp=False)
    if fade:  # 햇빛 바램 (위쪽·얼룩)
        fz = _noise(nt, 1.5, 2.0, coord=obj_co)
        col = _mix(nt, _math(nt, 'MULTIPLY', fz, fade), col, (0.75, 0.72, 0.66))
    if scratch:  # 가는 스크래치 (밝게)
        vor = _n(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE')
        vor.inputs['Scale'].default_value = 35
        mp = _n(nt, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1, 1, 6)
        nt.links.new(obj_co, mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], vor.inputs['Vector'])
        sc = _math(nt, 'MULTIPLY', _ramp(nt, vor.outputs['Distance'], 0.012, 0.0), _ramp(nt, _noise(nt, 4, 2, coord=obj_co), 0.5, 0.65))
        col = _mix(nt, _math(nt, 'MULTIPLY', sc, scratch), col, (0.8, 0.8, 0.8))
    if edge:  # 모서리 마모: Bevel 노멀과 실제 노멀 차이
        bv = _n(nt, 'ShaderNodeBevel')
        bv.inputs['Radius'].default_value = 0.004
        geo = _n(nt, 'ShaderNodeNewGeometry')
        dot = _n(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
        nt.links.new(bv.outputs['Normal'], dot.inputs[0])
        nt.links.new(geo.outputs['Normal'], dot.inputs[1])
        em = _math(nt, 'MULTIPLY', _ramp(nt, dot.outputs['Value'], 0.995, 0.90), _ramp(nt, _noise(nt, 18, 3, coord=obj_co), 0.42, 0.6))
        col = _mix(nt, _math(nt, 'MULTIPLY', em, edge), col, edge_col or (0.6, 0.6, 0.6))
    if grime:  # 틈 때 (AO)
        ao = _n(nt, 'ShaderNodeAmbientOcclusion', only_local=True, samples=8)
        ao.inputs['Distance'].default_value = grime_dist
        g = _math(nt, 'MULTIPLY', _ramp(nt, ao.outputs['AO'], 1.0, 0.3), _ramp(nt, _noise(nt, 9, 3, coord=obj_co), 0.3, 0.7))
        col = _mix(nt, _math(nt, 'MULTIPLY', g, grime), col, grime_col)
    if bottom:  # 아래쪽 먼지·물때
        sep = _n(nt, 'ShaderNodeSeparateXYZ')
        geo2 = _n(nt, 'ShaderNodeNewGeometry')
        nt.links.new(geo2.outputs['Position'], sep.inputs['Vector'])
        bz = _math(nt, 'MULTIPLY', _ramp(nt, sep.outputs['Z'], bottom_h, 0.0), _ramp(nt, _noise(nt, 5, 4, coord=obj_co), 0.25, 0.75))
        col = _mix(nt, _math(nt, 'MULTIPLY', bz, bottom), col, (0.12, 0.1, 0.075))
    if isinstance(col, bpy.types.NodeSocket):
        nt.links.new(col, p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = (*col[:3], 1)
    # 거칠기
    r = _math(nt, 'ADD', rough, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', _noise(nt, 4, 3, coord=obj_co), 0.5, clamp=False), rough_var, clamp=False))
    if rough_s:
        r = _math(nt, 'ADD', r, rough_s)
    if smudge:  # 손때 (거칠기 얼룩)
        sm = _ramp(nt, _noise(nt, 14, 2, coord=obj_co), 0.5, 0.62)
        r = _math(nt, 'ADD', r, _math(nt, 'MULTIPLY', sm, smudge))
    nt.links.new(r, p.inputs['Roughness'])
    p.inputs['Metallic'].default_value = metal
    if bump:
        b = _n(nt, 'ShaderNodeBump')
        b.inputs['Strength'].default_value = bump
        b.inputs['Distance'].default_value = 0.0005
        nt.links.new(_noise(nt, bump_scale, 6, coord=obj_co), b.inputs['Height'])
        nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[:3], 1)
        p.inputs['Emission Strength'].default_value = strength
    return m


def img_mat(name, path, rough=0.5, emission=0.0, alpha_clip=None, alpha=False, double=False, metal=0.0):
    """텍스처 한 장짜리 평면 머티리얼 (굽지 않음: bake keep= 로 넘기거나 별도 오브젝트)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = k3d._nodes(m)
    nt.nodes.clear()
    p = _n(nt, 'ShaderNodeBsdfPrincipled')
    out = _n(nt, 'ShaderNodeOutputMaterial')
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    im = _n(nt, 'ShaderNodeTexImage')
    im.image = k3d.load_image(path)
    im.image.name = os.path.splitext(os.path.basename(path))[0]
    nt.links.new(im.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emission:
        nt.links.new(im.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emission
    if alpha_clip or alpha:
        nt.links.new(im.outputs['Alpha'], p.inputs['Alpha'])
    if alpha_clip:
        k3d.flag(m, alpha_clip=alpha_clip)
    if double:
        k3d.flag(m, double_sided=True)
    return m


def flat(name, color, rough=0.5, metal=0.0, emission=None, strength=0.0, alpha=1.0):
    m = k3d.mat(name, color, rough, metal, emission, strength, alpha)
    return m


def look(cam_loc, target, lens=35, res=(1400, 1000), path=None, sun=True, world=0.6):
    """사람 눈높이 카메라 한 장 (EEVEE)."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("sf_look")
    sc.world = w
    nt = k3d._nodes(w)
    bg = next((n for n in nt.nodes if n.type == 'BACKGROUND'), None) or nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.62, 0.68, 0.76, 1)
    bg.inputs['Strength'].default_value = world
    tmp = []
    if sun:
        ld = bpy.data.lights.new("sf_sun", 'SUN')
        ld.energy, ld.angle = 2.2, math.radians(8)
        lo = bpy.data.objects.new("sf_sun", ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = (math.radians(50), 0, math.radians(-35))
        tmp.append(lo)
    cd = bpy.data.cameras.new("sf_cam")
    cd.lens = lens
    cd.clip_start = 0.02
    cam = bpy.data.objects.new("sf_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    tmp.append(cam)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    print("sf: look", path)
    return path

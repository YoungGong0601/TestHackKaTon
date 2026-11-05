# Items 그룹 공용 도구 (Home/hk.py 스냅샷 — 다른 그룹 수정에 영향받지 않도록 복사)
import bpy, bmesh, math, os, sys, subprocess
from mathutils import Vector, Matrix, Euler

SCRIPTS = '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts'
sys.path.insert(0, SCRIPTS)
import k3d

HERE = os.path.dirname(os.path.abspath(__file__))
PY = '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/_cache/venv/bin/python'
OUT2D = os.path.join(k3d.CACHE, "items2d")
CAT = "Items"


def tex(name, part=None):
    """tex2d.py 로 만든 2D 텍스처 경로 (없으면 생성)."""
    p = os.path.join(OUT2D, part or name)
    if not os.path.exists(p):
        env = dict(os.environ, K3D_CACHE=k3d.CACHE)
        subprocess.run([PY, os.path.join(HERE, "tex2d.py"), name, OUT2D], check=True, env=env)
    return p


def srgb(h):
    """'#rrggbb' -> linear RGB."""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---------------------------------------------------------------- 메시 기본형
def mesh_obj(name, bm, mat=None, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    if mat:
        me.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def finish(o, bev=0.003, seg=2, angle=35, smooth=True, wn=True):
    """베벨 + 가중 노멀 (모든 하드 엣지)."""
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    if bev and bev > 0:
        m = o.modifiers.new("Bevel", 'BEVEL')
        m.width, m.segments, m.limit_method = bev, seg, 'ANGLE'
        m.angle_limit = math.radians(angle)
        m.use_clamp_overlap = True
        m.harden_normals = False
    if wn:
        w = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
        w.keep_sharp = True
        w.weight = 50
    return o


def place(o, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    o.location = loc
    o.rotation_euler = rot
    if scale:
        o.scale = scale
    return o


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bev=0.003, seg=2, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = mesh_obj(name, bm, mat, parent)
    place(o, loc, rot)
    return finish(o, bev, seg)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, n=24, r2=None, bev=0.002, seg=2, parent=None, caps=True):
    """원기둥 (바닥 z=0 ~ 위 z=h, r2=윗반지름)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2,
                          depth=h, calc_uvs=True)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    o = mesh_obj(name, bm, mat, parent)
    place(o, loc, rot)
    return finish(o, bev, seg)


def lathe(name, prof, n=32, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, rmod=None, close_top=False,
          close_bot=False, smooth=True):
    """프로필 [(r, z), ...] 을 Z 축으로 회전. rmod(theta, z, r) -> r 로 주름 등 변형."""
    bm = bmesh.new()
    rings = []
    for i in range(n):
        th = 2 * math.pi * i / n
        ring = []
        for (r, z) in prof:
            rr = rmod(th, z, r) if rmod else r
            ring.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), z)))
        rings.append(ring)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(len(prof) - 1):
            if prof[k][0] < 1e-6 and prof[k + 1][0] < 1e-6:
                continue
            bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]))
    if close_bot:
        bm.faces.new([rings[i][0] for i in range(n)][::-1])
    if close_top:
        bm.faces.new([rings[i][-1] for i in range(n)])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    o = mesh_obj(name, bm, mat, parent)
    place(o, loc, rot)
    for p in o.data.polygons:
        p.use_smooth = smooth
    return o


def tube(name, pts, r, n=10, mat=None, parent=None, cap=True, rfun=None):
    """점 목록을 따라가는 튜브 (rfun(t) 로 반지름 변화)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
        if rfun:
            sp.points[i].radius = rfun(i / (len(pts) - 1))
    cu.bevel_depth = r
    cu.bevel_resolution = max(1, n // 4 - 1)
    cu.use_fill_caps = cap
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    k3d.select([o])
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    o.name = name
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    if mat:
        o.data.materials.clear()
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def poly_extrude(name, pts, depth, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), bev=0.002, seg=2, parent=None):
    """XY 평면 다각형을 Z 로 depth 만큼 돌출."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0)) for x, y in pts]
    f = bm.faces.new(vs)
    if f.normal.z < 0:
        f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=[e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    o = mesh_obj(name, bm, mat, parent)
    place(o, loc, rot)
    return finish(o, bev, seg)


def quad(name, w, h, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), uv=(0, 0, 1, 1), parent=None, nx=1, ny=1, bend=None):
    """XZ 평면 사각형 (정면 -Y), UV 0..1 (U 오른쪽, V 위). uv=(u0,v0,u1,v1) 아틀라스 영역."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x, z = (i / nx - 0.5) * w, (j / ny - 0.5) * h
            y = bend(i / nx, j / ny) if bend else 0.0
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for l in f.loops:
                vx, vz = l.vert.co.x / w + 0.5, l.vert.co.z / h + 0.5
                l[uvl].uv = (uv[0] + (uv[2] - uv[0]) * vx, uv[1] + (uv[3] - uv[1]) * vz)
    bm.normal_update()
    o = mesh_obj(name, bm, mat, parent)
    place(o, loc, rot)
    return o


def torus(name, R, r, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, nu=14, nv=6, sx=1.0, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=nu, minor_segments=nv)
    o = bpy.context.active_object
    o.name = o.data.name = name
    o.scale = (sx, 1, 1)
    k3d.select([o])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.location, o.rotation_euler = loc, rot
    if mat:
        o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def join(objs, name):
    objs = [o for o in objs if o and o.type == 'MESH']
    o = k3d.join(objs, name)
    return o


def vgroup(o, name):
    g = o.vertex_groups.new(name=name)
    g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    return o


def split_vgroup(o, gname, newname, pivot, parent=None):
    """bake 후: 버텍스 그룹 부분을 떼어 새 오브젝트로 (같은 머티리얼), 원점 = pivot."""
    k3d.select([o])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    o.vertex_groups.active_index = o.vertex_groups[gname].index
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    new = [x for x in bpy.context.selected_objects if x != o][0]
    new.name = new.data.name = newname
    k3d.set_origin(new, Vector(pivot))
    if parent:
        mw = new.matrix_world.copy()
        new.parent = parent
        new.matrix_world = mw
    return new


def socket(name, loc, parent=None, rot=(0, 0, 0), size=0.03):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    if parent:
        mw = e.matrix_world.copy()
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def parent_keep(child, parent):
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw


# ---------------------------------------------------------------- 절차 머티리얼
def _sock(node, name, typ, out=False):
    for s in (node.outputs if out else node.inputs):
        if s.name == name and s.type == typ:
            return s
    raise KeyError(name)


class G:
    """작은 노드 빌더."""

    def __init__(self, m):
        self.m, self.nt = m, m.node_tree
        self.N, self.L = self.nt.nodes, self.nt.links

    def n(self, kind, **props):
        x = self.N.new(kind)
        for k, v in props.items():
            if k.startswith("i_"):
                x.inputs[k[2:].replace("_", " ")].default_value = v
            else:
                setattr(x, k, v)
        return x

    def link(self, a, b):
        self.L.new(a, b)

    def val(self, v):
        x = self.N.new('ShaderNodeValue')
        x.outputs[0].default_value = v
        return x.outputs[0]

    def math(self, op, a, b=None, clamp=False):
        x = self.N.new('ShaderNodeMath')
        x.operation, x.use_clamp = op, clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                x.inputs[i].default_value = v
            else:
                self.L.new(v, x.inputs[i])
        return x.outputs[0]

    def mix(self, fac, a, b, blend='MIX'):
        """색 섞기 (a,b 는 소켓 또는 색 튜플)."""
        x = self.N.new('ShaderNodeMix')
        x.data_type, x.blend_type = 'RGBA', blend
        x.clamp_factor = True
        fs = _sock(x, 'Factor', 'VALUE')
        if isinstance(fac, (int, float)):
            fs.default_value = fac
        else:
            self.L.new(fac, fs)
        for nm, v in (('A', a), ('B', b)):
            s = _sock(x, nm, 'RGBA')
            if isinstance(v, (tuple, list)):
                s.default_value = (*v[:3], 1)
            else:
                self.L.new(v, s)
        return _sock(x, 'Result', 'RGBA', True)

    def lerp(self, fac, a, b):
        """스칼라 섞기."""
        x = self.N.new('ShaderNodeMix')
        x.data_type = 'FLOAT'
        x.clamp_factor = True
        fs = _sock(x, 'Factor', 'VALUE')
        if isinstance(fac, (int, float)):
            fs.default_value = fac
        else:
            self.L.new(fac, fs)
        for nm, v in (('A', a), ('B', b)):
            s = [q for q in x.inputs if q.name == nm and q.type == 'VALUE'][0]
            if isinstance(v, (int, float)):
                s.default_value = v
            else:
                self.L.new(v, s)
        return [q for q in x.outputs if q.type == 'VALUE'][0]

    def ramp(self, v, lo, hi):
        x = self.N.new('ShaderNodeMapRange')
        x.clamp = True
        self.L.new(v, x.inputs['Value'])
        x.inputs['From Min'].default_value, x.inputs['From Max'].default_value = lo, hi
        return x.outputs['Result']

    def coord(self, kind='Object', scale=1.0):
        tc = self.N.new('ShaderNodeTexCoord')
        s = tc.outputs[kind]
        if scale != 1.0:
            vm = self.N.new('ShaderNodeVectorMath')
            vm.operation = 'SCALE'
            self.L.new(s, vm.inputs[0])
            vm.inputs['Scale'].default_value = scale
            s = vm.outputs[0]
        return s

    def noise(self, scale, detail=4, rough=0.55, vec=None, dist=0.0, color=False):
        x = self.N.new('ShaderNodeTexNoise')
        x.inputs['Scale'].default_value = scale
        x.inputs['Detail'].default_value = detail
        x.inputs['Roughness'].default_value = rough
        x.inputs['Distortion'].default_value = dist
        self.L.new(vec or self.coord(), x.inputs['Vector'])
        return x.outputs['Color' if color else 'Fac']

    def voronoi(self, scale, vec=None, feature='F1', out='Distance'):
        x = self.N.new('ShaderNodeTexVoronoi')
        x.feature = feature
        x.inputs['Scale'].default_value = scale
        self.L.new(vec or self.coord(), x.inputs['Vector'])
        return x.outputs[out]

    def wave(self, scale, vec=None, axis='X', dist=2.0, detail=2.0, kind='BANDS', profile='SIN'):
        x = self.N.new('ShaderNodeTexWave')
        x.wave_type, x.bands_direction, x.wave_profile = kind, axis, profile
        x.inputs['Scale'].default_value = scale
        x.inputs['Distortion'].default_value = dist
        x.inputs['Detail'].default_value = detail
        self.L.new(vec or self.coord(), x.inputs['Vector'])
        return x.outputs['Fac']

    def ao(self, dist, inside=False, samples=8):
        x = self.N.new('ShaderNodeAmbientOcclusion')
        x.inside, x.samples = inside, samples
        x.only_local = True
        x.inputs['Distance'].default_value = dist
        return x.outputs['AO']

    def img(self, path, non_color=False, vec=None, proj='FLAT', interp='Cubic'):
        x = self.N.new('ShaderNodeTexImage')
        x.image = k3d.load_image(path, non_color=non_color)
        x.projection, x.interpolation = proj, interp
        if proj == 'BOX':
            x.projection_blend = 0.25
        if vec is not None:
            self.L.new(vec, x.inputs['Vector'])
        return x

    def sep(self, vec):
        x = self.N.new('ShaderNodeSeparateXYZ')
        self.L.new(vec, x.inputs[0])
        return x.outputs


def P(name, col, rough=0.5, metal=0.0, var=0.08, vs=6.0, rv=0.08, grime=0.0, gd=0.03, gcol=None,
      edge=0.0, ed=0.004, ecol=None, erough=None, emetal=None, bump=0.0, bs=300.0, bk='noise', bd=0.0004,
      img=None, imode='base', dust=0.0, dz=0.08, dcol=None, smudge=0.0, emis=None, estr=0.0, alpha=1.0,
      extra=None):
    """절차 Principled 머티리얼 (bake 용). 색은 linear 또는 '#hex'.
    var 색 변화, grime 틈 때(AO), edge 모서리 마모(안쪽 AO), bump 표면결, dust 아래쪽 먼지, smudge 지문/광택 얼룩."""
    if isinstance(col, str):
        col = srgb(col)
    if isinstance(gcol, str):
        gcol = srgb(gcol)
    if isinstance(ecol, str):
        ecol = srgb(ecol)
    if isinstance(dcol, str):
        dcol = srgb(dcol)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    g = G(m)
    p = g.n('ShaderNodeBsdfPrincipled')
    o = g.n('ShaderNodeOutputMaterial')
    g.link(p.outputs[0], o.inputs['Surface'])
    obj = g.coord('Object')
    # 기본색 + 저주파/고주파 변화
    n1 = g.noise(vs, 5, 0.6, obj)
    n2 = g.noise(vs * 9, 3, 0.5, obj)
    nv = g.math('ADD', g.math('MULTIPLY', n1, 0.7), g.math('MULTIPLY', n2, 0.3))
    lo = tuple(c * (1 - var) for c in col)
    hi = tuple(min(1, c * (1 + var)) for c in col)
    base = g.mix(nv, lo, hi)
    if img:
        im = g.img(img, vec=g.coord('UV'))
        if imode == 'base':
            base = g.mix(1.0, im.outputs['Color'], g.mix(nv, tuple(1 - var for _ in range(3)), (1, 1, 1)), 'MULTIPLY')
        elif imode == 'mul':
            base = g.mix(1.0, base, im.outputs['Color'], 'MULTIPLY')
        elif imode == 'alpha':
            base = g.mix(im.outputs['Alpha'], base, im.outputs['Color'])
    rough_s = g.math('ADD', g.math('MULTIPLY', g.math('SUBTRACT', g.noise(vs * 3, 4, 0.6, obj), 0.5), rv * 2), rough)
    metal_s = None
    if smudge:
        sm = g.ramp(g.noise(55, 6, 0.7, obj, dist=1.5), 0.45, 0.75)
        sm = g.math('MULTIPLY', sm, g.ramp(g.noise(7, 2, 0.5, obj), 0.4, 0.7))
        rough_s = g.math('ADD', rough_s, g.math('MULTIPLY', sm, smudge))
    if edge:
        e = g.math('SUBTRACT', 1.0, g.ao(ed, inside=True))
        e = g.ramp(g.math('MULTIPLY', e, g.math('ADD', g.noise(40, 4, 0.7, obj), 0.35)), 0.25, 0.55)
        e = g.math('MULTIPLY', e, g.ramp(g.noise(3.5, 3, 0.5, obj), 0.3, 0.62))  # 군데군데만 닳음
        e = g.math('MULTIPLY', e, edge, clamp=True)
        base = g.mix(e, base, ecol or tuple(min(1, c * 1.8 + 0.08) for c in col))
        if erough is not None:
            rough_s = g.lerp(e, rough_s, erough)
        if emetal is not None:
            metal_s = g.lerp(e, metal, emetal)
    if grime:
        a = g.math('SUBTRACT', 1.0, g.ao(gd))
        a = g.math('MULTIPLY', g.ramp(a, 0.05, 0.7), g.math('ADD', 0.5, g.noise(18, 3, 0.6, obj)))
        a = g.math('MULTIPLY', a, grime, clamp=True)
        base = g.mix(a, base, gcol or tuple(c * 0.35 for c in col))
        rough_s = g.lerp(a, rough_s, min(1.0, rough + 0.2))
    if dust:
        z = g.sep(g.coord('Object'))[2]
        d = g.math('SUBTRACT', 1.0, g.ramp(z, 0.0, dz))
        d = g.math('MULTIPLY', g.math('MULTIPLY', d, d), g.math('ADD', 0.4, g.noise(25, 4, 0.6, obj)))
        d = g.math('MULTIPLY', d, dust, clamp=True)
        base = g.mix(d, base, dcol or (0.18, 0.16, 0.13))
        rough_s = g.lerp(d, rough_s, 0.9)
    if extra:
        base, rough_s = extra(g, base, rough_s, obj)
    g.link(base, p.inputs['Base Color'])
    g.link(rough_s, p.inputs['Roughness'])
    if metal_s is not None:
        g.link(metal_s, p.inputs['Metallic'])
    else:
        p.inputs['Metallic'].default_value = metal
    if bump:
        if bk == 'voronoi':
            h = g.voronoi(bs, obj)
        elif bk == 'cloth':
            h = g.math('ADD', g.wave(bs, obj, 'X', 0.5, 1), g.wave(bs, obj, 'Z', 0.5, 1))
        else:
            h = g.noise(bs, 6, 0.6, obj)
        b = g.n('ShaderNodeBump', i_Strength=bump, i_Distance=bd)
        g.link(h, b.inputs['Height'])
        g.link(b.outputs['Normal'], p.inputs['Normal'])
    if emis:
        p.inputs['Emission Color'].default_value = (*(srgb(emis) if isinstance(emis, str) else emis)[:3], 1)
        p.inputs['Emission Strength'].default_value = estr
    p.inputs['Alpha'].default_value = alpha
    return m


def flat_img(name, path, rough=0.6, metal=0.0, emis=0.0, normal=None):
    """굽지 않는 이미지 머티리얼 (인쇄물 등). bake(keep=(name,)) 로 지킬 것."""
    m = k3d.mat(name, (1, 1, 1), rough, metal)
    g = G(m)
    p = k3d.principled(m)
    im = g.img(path)
    g.link(im.outputs['Color'], p.inputs['Base Color'])
    if emis:
        g.link(im.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emis
    return m


def glass(name, col=(0.85, 0.9, 0.9), alpha=0.18, rough=0.05):
    m = k3d.mat(name, col, rough, 0.0, alpha=alpha)
    k3d.flag(m, transparent=True)
    return m


# ---------------------------------------------------------------- 촬영 (내부/임의 카메라)
def shot(path, cam_loc, target, lens=24, res=(1280, 800), lights=(), world=0.25, exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new("hk_w")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.55, 0.58, 1)
    bg.inputs['Strength'].default_value = world
    tmp = []
    for kind, loc, energy, col, size in lights:
        ld = bpy.data.lights.new("hk_l", kind)
        ld.energy, ld.color = energy, col
        if kind in ('POINT', 'SPOT'):
            ld.shadow_soft_size = size
        if kind == 'AREA':
            ld.size = size
        lo = bpy.data.objects.new("hk_l", ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        if kind in ('SPOT', 'AREA', 'SUN'):
            lo.rotation_euler = (0, 0, 0)
        tmp.append(lo)
    cd = bpy.data.cameras.new("hk_cam")
    cd.lens = lens
    cd.clip_start = 0.02
    cam = bpy.data.objects.new("hk_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in tmp + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    print("hk: shot", path)
    return path


PREV = os.path.join(k3d.SRC, "Previews")

"""Street 그룹 공용 도우미: 형상(베벨 파츠·텍스트·튜브), 절차 머티리얼(마모·때·녹), 데칼, 마무리(굽기·내보내기·미리보기·검증)."""
import bpy, bmesh, math, os, sys, json, random, subprocess
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(k3d.CACHE, "street_tex")
FONT_EB = os.path.join(k3d.CACHE, "fonts", "NanumSquareEB.ttf")
FONT_B = os.path.join(k3d.CACHE, "fonts", "NanumSquareB.ttf")
CAT = "Street"


def ensure_tex():
    """Pillow 텍스처가 없으면 _textures.py 를 돌린다."""
    if not os.path.exists(os.path.join(TEX, ".done")):
        subprocess.run([k3d.PY, "-I",
                        os.path.join(HERE, "_textures.py"), TEX], check=True)


def atlas(name):
    ensure_tex()
    return os.path.join(TEX, name + ".png"), json.load(open(os.path.join(TEX, name + ".json")))


# ------------------------------------------------------------------ 형상
def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def from_bm(name, bm, mat=None):
    if not bm.loops.layers.uv:
        bm.loops.layers.uv.new("UVMap")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        me.materials.append(mat)
    return o


def mods(o, bevel=0.0, segs=2, angle=40, wn=True, sharp=35):
    """스무스 + (베벨) + 가중 노멀. 베벨이 없으면 각도 기준 샤프."""
    for p in o.data.polygons:
        p.use_smooth = True
    if bevel > 0:
        b = o.modifiers.new("Bevel", 'BEVEL')
        b.width, b.segments, b.limit_method = bevel, segs, 'ANGLE'
        b.angle_limit = math.radians(angle)
        b.use_clamp_overlap = True
    elif sharp:
        o.data.set_sharp_from_angle(angle=math.radians(sharp))
    if wn:
        w = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
        w.keep_sharp = True
    return o


def _xf(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.004, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=_xf(loc, rot, size), calc_uvs=True)
    return mods(from_bm(name, bm, mat), bevel, segs)


def cyl(name, r, h, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, r2=None, seg=24, bevel=0.003, segs=2, caps=True):
    """원기둥(원뿔대). loc = 아래 중심 (rot 적용 전 기준 +Z 방향으로 h)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=h,
                          matrix=_xf(loc, rot) @ Matrix.Translation((0, 0, h / 2)), calc_uvs=True)
    return mods(from_bm(name, bm, mat), bevel, segs)


def sphere(name, r, loc=(0, 0, 0), mat=None, seg=16, rings=8, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r,
                              matrix=_xf(loc, (0, 0, 0), scale), calc_uvs=True)
    return mods(from_bm(name, bm, mat), 0, wn=False, sharp=0)


def lathe(name, prof, seg=24, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, close=True, smooth_ang=50):
    """(r, z) 프로필을 Z 축으로 돌린 회전체 (애자·타이어·볼라드 머리)."""
    bm = bmesh.new()
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in prof])
    n = len(prof)
    for k in range(seg):
        A, B = rings[k], rings[(k + 1) % seg]
        for i in range(n - 1):
            bm.faces.new((A[i], B[i], B[i + 1], A[i + 1]))
    if close:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.transform(_xf(loc, rot))
    o = from_bm(name, bm, mat)
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(smooth_ang))
    return o


def tube(name, pts, r, sides=8, mat=None, caps=True):
    """점 목록을 따라가는 관 (전선·케이블·파이프)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    cu.bevel_depth = r
    cu.bevel_resolution = max(0, sides // 4 - 1)
    cu.use_fill_caps = caps
    tmp = link(bpy.data.objects.new(name + "_c", cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    o = link(bpy.data.objects.new(name, me))
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def text_mesh(name, s, size, font=FONT_EB, depth=0.0, sx=1.0, sy=1.0, mat=None, spacing=1.0):
    """한글 텍스트 -> 메시 (XY 평면, 가운데 정렬). depth>0 이면 위로 두께."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = s
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.space_character = spacing
    cu.resolution_u = 4
    cu.extrude = depth / 2
    tmp = link(bpy.data.objects.new(name + "_t", cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.transform(Matrix.Translation((0, 0, depth / 2)) if depth else Matrix())
    bm.transform(Matrix.Diagonal((sx, sy, 1, 1)))
    if not bm.loops.layers.uv:
        bm.loops.layers.uv.new("UVMap")
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        me.materials.append(mat)
    return o


def xform(o, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """메시 데이터에 변환을 굽는다 (오브젝트 변환은 0 유지)."""
    o.data.transform(_xf(loc, rot, scale))
    o.data.update()
    return o


def empty(name, loc, rot=(0, 0, 0), parent=None, size=0.05):
    e = link(bpy.data.objects.new(name, None))
    e.empty_display_type, e.empty_display_size = 'ARROWS', size
    e.location, e.rotation_euler = loc, rot
    if parent:
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


def join(objs, name):
    return k3d.join([o for o in objs if o], name)


# ------------------------------------------------------------------ 데칼 (굽지 않는 선명한 라벨)
def decal_mat(name, png, rough=0.55, alpha_clip=False, emission=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = k3d._nodes(m)
    p = k3d.principled(m)
    im = k3d.load_image(png)
    k3d.image_node(m, im, p.inputs['Base Color'], uv="UVMap")
    p.inputs['Roughness'].default_value = rough
    if alpha_clip:
        n = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
        nt.links.new(n.outputs['Alpha'], p.inputs['Alpha'])
        k3d.flag(m, alpha_clip=0.5)
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = 'DITHERED'
        if hasattr(m, "blend_method"):
            try:
                m.blend_method = 'CLIP'
            except Exception:
                pass
    if emission:
        n = [x for x in nt.nodes if x.type == 'TEX_IMAGE'][0]
        nt.links.new(n.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emission
    return m


def quad(name, w, h, rect=(0, 0, 1, 1), mat=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """XZ 평면 사각형, 정면 -Y (U 오른쪽, V 위). rect = 아틀라스 UV 사각형."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(v) for v in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    u0, v0, u1, v1 = rect
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
        l[uv].uv = c
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    bm.transform(_xf(loc, rot))
    o = from_bm(name, bm, mat)
    return o


def wrap_decal(name, radius, z0, h, ang0, ang1, rect, mat, seg=10, center=(0, 0), r_top=None, bulge=0.0):
    """원기둥에 감긴 데칼 (전단지·반사띠). 각도 rad, 0 = -Y(정면) 방향, 반시계."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = rect
    rows = []
    for j in range(2):
        z = z0 + h * j
        rr = radius if r_top is None else radius + (r_top - radius) * j
        row = []
        for i in range(seg + 1):
            t = i / seg
            a = ang0 + (ang1 - ang0) * t
            b = bulge * math.sin(math.pi * t)
            row.append(bm.verts.new((center[0] + math.sin(a) * (rr + b), center[1] - math.cos(a) * (rr + b), z)))
        rows.append(row)
    for i in range(seg):
        f = bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        for l, (ii, jj) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
            l[uv].uv = (u0 + (u1 - u0) * ii / seg, v0 + (v1 - v0) * jj)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(name, bm, mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# ------------------------------------------------------------------ 절차 머티리얼
class NB:
    def __init__(self, m):
        self.m, self.nt = m, m.node_tree
        self.N, self.L = self.nt.nodes, self.nt.links

    def n(self, t, **kw):
        x = self.N.new(t)
        for k, v in kw.items():
            if k.startswith("i_"):
                x.inputs[int(k[2:]) if k[2:].isdigit() else k[2:].replace("_", " ")].default_value = v
            else:
                setattr(x, k, v)
        return x

    def ln(self, a, b):
        self.L.new(a, b)

    def noise(self, vec, scale, detail=6, rough=0.55, dist=0.0, w=None):
        x = self.n('ShaderNodeTexNoise')
        x.inputs['Scale'].default_value = scale
        x.inputs['Detail'].default_value = detail
        x.inputs['Roughness'].default_value = rough
        x.inputs['Distortion'].default_value = dist
        self.ln(vec, x.inputs['Vector'])
        return x.outputs['Fac']

    def mr(self, val, a, b, c=0.0, d=1.0, clamp=True):
        x = self.n('ShaderNodeMapRange', clamp=clamp)
        x.inputs['From Min'].default_value, x.inputs['From Max'].default_value = a, b
        x.inputs['To Min'].default_value, x.inputs['To Max'].default_value = c, d
        self.ln(val, x.inputs['Value'])
        return x.outputs['Result']

    def math(self, op, a, b=None, clamp=False):
        x = self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                x.inputs[i].default_value = v
            else:
                self.ln(v, x.inputs[i])
        return x.outputs[0]

    def mixc(self, fac, a, b, blend='MIX'):
        x = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend)
        for sock, v in ((x.inputs['Factor'], fac), (x.inputs[6], a), (x.inputs[7], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v[:3], 1)
            else:
                self.ln(v, sock)
        return x.outputs[2]

    def mixf(self, fac, a, b):
        x = self.n('ShaderNodeMix', data_type='FLOAT')
        for sock, v in ((x.inputs['Factor'], fac), (x.inputs[2], a), (x.inputs[3], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            else:
                self.ln(v, sock)
        return x.outputs[0]


def wmat(name, base, rough=0.5, metal=0.0, *, var=0.12, vscale=2.5, grime=0.5, grime_col=(0.03, 0.027, 0.022),
         grime_dist=0.06, edge=0.0, edge_col=(0.42, 0.42, 0.40), edge_metal=1.0, edge_rough=0.35, rust=0.0,
         rust_scale=5.0, rust_bias=0.0, rust_z=None, streaks=0.0, streak_col=(0.10, 0.065, 0.04), bottom=0.0, bottom_h=0.25,
         bottom_col=(0.16, 0.13, 0.09), bump=0.12, bump_scale=90.0, img=None, img_rect=None, scratches=0.0,
         dents=0.0, seed=0.0, fade_top=0.0, ph=None, ph_scale=1.0, ph_mix=0.5, metal_bare=None):
    """풍화된 표면 1종. base = linear RGB. 마스크: AO(틈 때), Bevel 노멀(모서리 마모), 노이즈(색 변화/녹/얼룩),
    오브젝트 Z(바닥 흙탕), 세로 늘인 노이즈(빗물 줄), 높은 주파수(잔 긁힘). ph = Poly Haven diff 경로(디테일 곱)."""
    m = bpy.data.materials.new(name)
    nt = k3d._nodes(m)
    nb = NB(m)
    p = k3d.principled(m)
    tc = nb.n('ShaderNodeTexCoord')
    obj = tc.outputs['Object']
    if seed:
        mp = nb.n('ShaderNodeMapping')
        mp.inputs['Location'].default_value = (seed * 3.7, seed * 1.3, seed * 2.1)
        nb.ln(obj, mp.inputs['Vector'])
        obj = mp.outputs['Vector']
    # 기본색 변화
    n1 = nb.noise(obj, vscale, 6, 0.6)
    lo = tuple(c * (1 - var) for c in base)
    hi = tuple(min(1, c * (1 + var * 0.8)) for c in base)
    col = nb.mixc(nb.mr(n1, 0.3, 0.7), lo, hi)
    if ph:
        im = k3d.load_image(ph)
        t = nb.n('ShaderNodeTexImage', projection='BOX', projection_blend=0.3)
        t.image = im
        mp2 = nb.n('ShaderNodeMapping')
        mp2.inputs['Scale'].default_value = (1 / ph_scale,) * 3
        nb.ln(tc.outputs['Object'], mp2.inputs['Vector'])
        nb.ln(mp2.outputs['Vector'], t.inputs['Vector'])
        # 휘도만 디테일로 곱한다 (평균 0.5 기준)
        bw = nb.n('ShaderNodeRGBToBW')
        nb.ln(t.outputs['Color'], bw.inputs['Color'])
        det = nb.math('MULTIPLY', nb.math('ADD', bw.outputs[0], 0.55), 1.0)
        col = nb.mixc(ph_mix, col, nb.mixc(1.0, col, det, 'MULTIPLY'))
    if img is not None:
        uvn = nb.n('ShaderNodeUVMap', uv_map="UVMap")
        ti = nb.n('ShaderNodeTexImage')
        ti.image = k3d.load_image(img)
        nb.ln(uvn.outputs['UV'], ti.inputs['Vector'])
        col = nb.mixc(1.0, col, ti.outputs['Color'], 'MULTIPLY')
    if fade_top:
        sep = nb.n('ShaderNodeSeparateXYZ')
        nb.ln(tc.outputs['Object'], sep.inputs['Vector'])
        col = nb.mixc(nb.math('MULTIPLY', nb.mr(sep.outputs['Z'], 0.0, 2.0), fade_top), col, (0.75, 0.75, 0.72))
    rgh = nb.mixf(nb.mr(n1, 0.2, 0.8), rough * 0.85, min(1, rough * 1.15))
    met = metal
    # 녹 (노이즈 얼룩)
    if rust > 0:
        n2 = nb.noise(obj, rust_scale, 12, 0.7, 0.4)
        n2b = nb.noise(obj, rust_scale * 6, 8, 0.6)
        rm = nb.mr(nb.math('ADD', n2, nb.math('MULTIPLY', n2b, 0.25)), 0.78 - rust * 0.22 - rust_bias, 0.84 - rust * 0.2 - rust_bias)
        if rust_z:
            sepr = nb.n('ShaderNodeSeparateXYZ')
            nb.ln(tc.outputs['Object'], sepr.inputs['Vector'])
            rm = nb.math('MULTIPLY', rm, nb.mr(sepr.outputs['Z'], rust_z, 0.0), clamp=True)
        rcol = nb.mixc(nb.noise(obj, 40, 4), (0.075, 0.032, 0.016), (0.19, 0.075, 0.03))
        col = nb.mixc(rm, col, rcol)
        rgh = nb.mixf(rm, rgh, 0.88)
        if metal > 0:
            met = nb.mixf(rm, metal, 0.0)
    # 모서리 마모 (Bevel 노멀 vs 셰이딩 노멀)
    if edge > 0:
        bev = nb.n('ShaderNodeBevel', samples=8)
        bev.inputs['Radius'].default_value = 0.006
        geo = nb.n('ShaderNodeNewGeometry')
        dot = nb.n('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        nb.ln(bev.outputs['Normal'], dot.inputs[0])
        nb.ln(geo.outputs['Normal'], dot.inputs[1])
        em = nb.mr(dot.outputs['Value'], 0.995, 0.93)
        n3 = nb.noise(obj, 18, 8, 0.7)
        em = nb.math('MULTIPLY', em, nb.mr(n3, 0.35, 0.6), clamp=True)
        em = nb.math('MULTIPLY', em, edge, clamp=True)
        col = nb.mixc(em, col, edge_col)
        rgh = nb.mixf(em, rgh, edge_rough)
        if edge_metal is not None and (metal > 0 or edge_metal > 0):
            met = nb.mixf(em, met if not isinstance(met, (int, float)) else met, edge_metal)
    # 잔 긁힘
    if scratches > 0:
        mps = nb.n('ShaderNodeMapping')
        mps.inputs['Scale'].default_value = (1.0, 1.0, 40.0)
        mps.inputs['Rotation'].default_value = (0.3, 0.8, 0.2)
        nb.ln(obj, mps.inputs['Vector'])
        ns = nb.noise(mps.outputs['Vector'], 30, 2, 0.5)
        sm = nb.math('MULTIPLY', nb.mr(ns, 0.68, 0.72), scratches, clamp=True)
        col = nb.mixc(sm, col, tuple(min(1, c * 1.5 + 0.05) for c in base))
        rgh = nb.mixf(sm, rgh, rough * 0.7)
    # 틈 때 (AO)
    if grime > 0:
        ao = nb.n('ShaderNodeAmbientOcclusion', only_local=True, samples=16)
        ao.inputs['Distance'].default_value = grime_dist
        n4 = nb.noise(obj, 7, 6, 0.6)
        gm = nb.math('MULTIPLY', nb.mr(ao.outputs['AO'], 0.95, 0.35), nb.mr(n4, 0.25, 0.65, 0.5, 1.0), clamp=True)
        gm = nb.math('MULTIPLY', gm, grime, clamp=True)
        col = nb.mixc(gm, col, grime_col)
        rgh = nb.mixf(gm, rgh, 0.9)
    # 빗물 줄 (세로로 늘인 노이즈)
    if streaks > 0:
        mpz = nb.n('ShaderNodeMapping')
        mpz.inputs['Scale'].default_value = (14.0, 14.0, 0.6)
        nb.ln(obj, mpz.inputs['Vector'])
        nz = nb.noise(mpz.outputs['Vector'], 3.0, 5, 0.6)
        sm = nb.math('MULTIPLY', nb.mr(nz, 0.52, 0.72), streaks, clamp=True)
        col = nb.mixc(sm, col, streak_col)
    # 바닥 흙탕/먼지
    if bottom > 0:
        sep = nb.n('ShaderNodeSeparateXYZ')
        nb.ln(tc.outputs['Object'], sep.inputs['Vector'])
        n5 = nb.noise(obj, 12, 6, 0.65)
        bz = nb.math('ADD', sep.outputs['Z'], nb.math('MULTIPLY', nb.math('SUBTRACT', n5, 0.5), bottom_h * 0.8))
        bm_ = nb.math('MULTIPLY', nb.mr(bz, bottom_h, 0.0), bottom, clamp=True)
        col = nb.mixc(bm_, col, bottom_col)
        rgh = nb.mixf(bm_, rgh, 0.92)
    nb.ln(col, p.inputs['Base Color'])
    if isinstance(rgh, (int, float)):
        p.inputs['Roughness'].default_value = rgh
    else:
        nb.ln(rgh, p.inputs['Roughness'])
    if isinstance(met, (int, float)):
        p.inputs['Metallic'].default_value = met
    else:
        nb.ln(met, p.inputs['Metallic'])
    # 범프 (잔 요철 + 찌그러짐)
    if bump > 0 or dents > 0:
        h = nb.noise(obj, bump_scale, 8, 0.6)
        if dents > 0:
            dn = nb.noise(obj, 2.5, 3, 0.5)
            h = nb.math('ADD', nb.math('MULTIPLY', h, bump), nb.math('MULTIPLY', nb.mr(dn, 0.55, 0.75), dents * 8))
        b = nb.n('ShaderNodeBump')
        b.inputs['Strength'].default_value = 1.0 if dents > 0 else bump
        b.inputs['Distance'].default_value = 0.002
        nb.ln(h, b.inputs['Height'])
        nb.ln(b.outputs['Normal'], p.inputs['Normal'])
    return m


def galv(name, rough=0.45, base=(0.55, 0.56, 0.56), **kw):
    """아연도금 강관."""
    kw.setdefault("grime", 0.55)
    kw.setdefault("var", 0.18)
    kw.setdefault("vscale", 6)
    kw.setdefault("streaks", 0.35)
    kw.setdefault("bump", 0.05)
    return wmat(name, base, rough, 1.0, **kw)


def paint(name, color, rough=0.5, **kw):
    """도장 금속 (모서리 마모로 하도/금속 노출)."""
    kw.setdefault("edge", 0.8)
    kw.setdefault("edge_col", (0.30, 0.30, 0.29))
    kw.setdefault("edge_metal", 0.8)
    kw.setdefault("grime", 0.55)
    kw.setdefault("scratches", 0.4)
    kw.setdefault("bump", 0.03)          # 강판은 매끈하다: 잔 요철은 약하게
    return wmat(name, color, rough, 0.0, **kw)


def concrete(name, base=(0.36, 0.35, 0.33), **kw):
    kw.setdefault("grime", 0.6)
    kw.setdefault("var", 0.15)
    kw.setdefault("bump", 0.35)
    kw.setdefault("bump_scale", 140)
    return wmat(name, base, 0.9, 0.0, **kw)


def rubber(name, base=(0.022, 0.022, 0.022), **kw):
    kw.setdefault("grime", 0.4)
    kw.setdefault("grime_col", (0.05, 0.045, 0.04))
    kw.setdefault("bump", 0.2)
    return wmat(name, base, 0.82, 0.0, **kw)


def flat(name, color, rough=0.5, metal=0.0, emission=None, strength=1.0):
    return k3d.mat(name, color, rough, metal, emission, strength)


# ------------------------------------------------------------------ 타일 머티리얼 (도로·보도 공용)
def tile_asphalt():
    """기본 노면: 큰 균열이 없는 clean_asphalt (실측 2.1 m, 반복 무늬가 안 보인다).
    색은 골재 대비를 키운 asphalt_base_diff.jpg (_textures.asphalt_base)."""
    ensure_ground_tex()
    maps = dict(k3d.polyhaven("clean_asphalt", "2k"), diff=os.path.join(TEX, "asphalt_base_diff.jpg"))
    maps.pop("ao", None)    # AO 맵이 골재를 다시 어둡게 눌러 고르게 만든다
    return k3d.tile("Street_Asphalt", maps=maps)


def tile_asphalt_old():
    """보수판: 균열 많은 asphalt_02 (실측 3 m, 판이 작아 반복이 안 보인다), 바랜 회색."""
    return k3d.tile("Street_AsphaltOld", polyhaven_id="asphalt_02", res="2k", tint=(0.80, 0.80, 0.82))


def tile_patch():
    """맨홀 둘레 새 보수 아스팔트 (기본 노면 텍스처를 어둡게)."""
    return _tinted_copy(tile_asphalt(), "M_Tile_Street_AsphaltPatch", (0.78, 0.79, 0.81))


def tile_curb():
    return k3d.tile("Street_Curb", polyhaven_id="concrete_floor_worn_001", res="1k", tint=(0.95, 0.95, 0.93))


def tile_pavers():
    return k3d.tile("Street_Pavers", polyhaven_id="concrete_pavers", res="2k", tint=(0.92, 0.92, 0.92))


def tile_gutter():
    return k3d.tile("Street_GutterConcrete", polyhaven_id="gravel_concrete_03", res="1k")


def _tinted_copy(src, name, tint):
    """같은 텍스처를 쓰는 색만 다른 타일 머티리얼 (텍스처 중복 저장 방지)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = src.copy()
    m.name = name
    # Blender 는 원본 tint x 새 tint 로 칠하므로 Unity 에도 곱한 값을 넘긴다
    m["unity_tint"] = [a * b for a, b in zip(src.get("unity_tint", [1, 1, 1]), tint)]
    nt = m.node_tree
    p = k3d.principled(m)
    if p.inputs['Base Color'].is_linked:
        lk = p.inputs['Base Color'].links[0]
        fs = lk.from_socket
        nt.links.remove(lk)
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(fs, mix.inputs['A'])
        mix.inputs['B'].default_value = (*tint, 1)
        nt.links.new(mix.outputs['Result'], p.inputs['Base Color'])
    return m


def tile_paint_white():
    ensure_tex()
    ensure_ground_tex()
    return k3d.tile("Street_PaintWhite", maps={"diff": os.path.join(TEX, "roadpaint_diff.jpg"),
                                               "nor": os.path.join(TEX, "roadpaint_nor.jpg"),
                                               "rough": os.path.join(TEX, "roadpaint_rough.png")})


def ensure_ground_tex():
    """점자블록·노랑 도료·맨홀 텍스처 (_tex_ground.py)."""
    ensure_tex()
    if not os.path.exists(os.path.join(TEX, ".ground_done")):
        subprocess.run([k3d.PY, "-I",
                        os.path.join(HERE, "_tex_ground.py"), TEX], check=True)


def tile_paint_yellow():
    """흰 도료와 같은 아스팔트 결을 따라 닳은 노랑 도료 (uv_world 크기는 아스팔트와 같게)."""
    ensure_ground_tex()
    return k3d.tile("Street_PaintYellow", maps={"diff": os.path.join(TEX, "roadpaint_yellow_diff.jpg"),
                                                "nor": os.path.join(TEX, "roadpaint_nor.jpg"),
                                                "rough": os.path.join(TEX, "roadpaint_rough.png")})


def tile_tactile(kind="line"):
    """노란 점자블록 (300 mm 블록 2x2 = 0.6 m 타일). kind = 'line'(선형, 돌기 U 방향) / 'dot'(점형)."""
    ensure_ground_tex()
    nm = "Street_TactileLine" if kind == "line" else "Street_TactileDot"
    return k3d.tile(nm, maps={"diff": os.path.join(TEX, f"tactile_{kind}_diff.jpg"),
                              "nor": os.path.join(TEX, f"tactile_{kind}_nor.jpg"),
                              "rough": os.path.join(TEX, f"tactile_{kind}_rough.png")})


# 타일 크기(m): 모듈 길이(6/12/18 m)가 모두 이 값의 정수배라 이어 붙여도 결이 맞는다
TILE_ASPHALT = 2.0   # clean_asphalt 실측 2.1 m, 도료도 같은 값
TILE_ASPHALT_OLD = 3.0  # asphalt_02 실측 3 m (보수판)
TILE_PATCH = 2.0
TILE_PAVER = 2.0     # concrete_pavers 실측 1.92 m
TILE_CURB = 3.0
TILE_GUTTER = 2.0
TILE_TACTILE = 0.6


def all_tiles():
    """병렬 실행 전에 타일 텍스처를 한 번에 만든다 (파일 쓰기 경합 방지)."""
    for f in (tile_asphalt, tile_asphalt_old, tile_curb, tile_pavers, tile_gutter, tile_paint_white, tile_paint_yellow):
        f()
    tile_tactile("line")
    tile_tactile("dot")


# ------------------------------------------------------------------ 마무리
def finish(asset, roots, height, notes="", fp=None, views=((35, 18), (215, 12)), lens=50, validate=True, res=(1200, 900),
           extra=()):
    """내보내기 + 미리보기 (+ fp=dict 1인칭 샷) + 검증 (검증은 장면을 지우므로 맨 마지막)."""
    fbx = k3d.export(asset, CAT, roots, notes=notes)
    paths = k3d.preview(asset, roots, views=views, lens=lens, res=res)
    if fp is not None:
        paths += fp_shot(asset, roots, **fp)
    for i, kw in enumerate(extra):
        paths += fp_shot(asset, roots, tag="x%d" % i, **kw)
    print("STREET_PREVIEWS", json.dumps(paths))
    if validate:
        rep = k3d.validate(fbx, height)
        print("STREET_VALIDATE", asset, json.dumps(rep["problems"], ensure_ascii=False), rep["tris"],
              rep["size_m_unity_xyz"])
    return fbx


def fp_shot(asset, roots, dist=3.0, eye=1.55, look_h=None, az=20, lens=35, tag="fp", cx=None):
    """1인칭(눈높이 1.55 m) 샷."""
    mn, mx = k3d.bounds(roots)
    c = (mn + mx) / 2
    if cx is not None:
        c = Vector(cx)
    a = math.radians(az)
    cam_loc = Vector((c.x + math.sin(a) * dist, c.y - math.cos(a) * dist, eye))
    tgt = Vector((c.x, c.y, look_h if look_h is not None else min(eye, (mn.z + mx.z) / 2)))
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = 1200, 900
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("fp_world")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs['Color'].default_value = (0.62, 0.66, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.6
    old = sc.world
    sc.world = w
    tmp = []
    sd = bpy.data.lights.new("fp_sun", 'SUN')
    sd.energy = 2.2
    so = link(bpy.data.objects.new("fp_sun", sd))
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    tmp.append(so)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(c.x, c.y, mn.z - 0.002))
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("fp_ground", (0.3, 0.3, 0.3), 0.85))
    tmp.append(g)
    cd = bpy.data.cameras.new("fp_cam")
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.05, 200
    cam = link(bpy.data.objects.new("fp_cam", cd))
    cam.location = cam_loc
    cam.rotation_euler = (tgt - cam_loc).to_track_quat('-Z', 'Y').to_euler()
    tmp.append(cam)
    sc.camera = cam
    p = os.path.join(k3d.SRC, "Previews", f"{asset}_{tag}_0.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.world = old
    return [p]

# 할아버지 낡은 가죽 단화 한 켤레 (벨크로 효도화). 오른쪽 한 짝을 만들어 굽고, 거울 복제로 왼쪽.
# 정면(-Y) = 앞코(문 쪽), 원점 = 두 짝 바닥 중앙.
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "HomeShoes"
L = 0.282            # 바깥창 길이
NEX = 3.0            # 단면 지수 (클수록 옆벽이 곧다)
d2r = math.radians


def sstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def width(s, ext=0.0):
    """발볼 반폭 (s: 0 뒤꿈치 -> 1 앞코)."""
    wb = 0.031 + 0.017 * sstep(0.22, 0.7, s) - 0.006 * sstep(0.86, 1.0, s) + ext
    u = (s + ext * 1.6) / (1 + ext * 3.2)          # 끝을 조금 늘린 매개변수
    fh = math.sqrt(max(0.0, 1 - ((0.11 - u) / 0.11) ** 2)) if u < 0.11 else 1.0
    ft = math.sqrt(max(0.0, 1 - ((u - 0.78) / 0.22) ** 2)) if u > 0.78 else 1.0
    return wb * fh * ft


def xc(s):  # 앞코가 안쪽(엄지, +X)으로 살짝
    return 0.007 * sstep(0.55, 1.0, s) - 0.002 * sstep(0.0, 0.3, s)


def ysec(s):
    return (0.5 - s) * L


def sole_bot(s):    # 앞코 들림(토 스프링)
    return 0.011 * sstep(0.68, 1.0, s) ** 1.6


def sole_top(s):
    return sole_bot(s) + 0.016 + 0.012 * (1 - sstep(0.22, 0.48, s))


def height(s):      # 갑피 높이 (창 위에서)
    pts = [(0, 0.07), (0.25, 0.074), (0.5, 0.079), (0.64, 0.064), (0.8, 0.043), (0.92, 0.029), (1.0, 0.019)]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if s <= b:
            t = (s - a) / (b - a)
            t = t * t * (3 - 2 * t)
            return va + (vb - va) * t
    return pts[-1][1]


def opening(s):     # 발 넣는 입구 (위에서 본 반폭)
    sc, As, Ax = 0.235, 0.22, 0.029
    if abs(s - sc) >= As:
        return 0.0
    return Ax * math.sqrt(1 - ((s - sc) / As) ** 2)


def spow(v, p):
    return math.copysign(abs(v) ** p, v)


def upt(s, th, off=0.0):
    w, h = width(s) + off, height(s) + off
    return Vector((xc(s) + w * spow(math.cos(th), 2 / NEX), ysec(s), sole_top(s) - 0.002 + h * abs(math.sin(th)) ** (2 / NEX)))


# ---------------------------------------------------------------- 머티리얼
def leather():
    m = bpy.data.materials.new("M_tmp_leather")
    m.use_nodes = True
    m.node_tree.nodes.clear()
    g = hk.G(m)
    p = g.n('ShaderNodeBsdfPrincipled')
    out = g.n('ShaderNodeOutputMaterial')
    g.link(p.outputs[0], out.inputs['Surface'])
    obj = g.coord('Object')
    xyz = g.sep(obj)
    base = g.mix(g.noise(9, 5, 0.6, obj), hk.srgb("#2c1d14"), hk.srgb("#46301f"))
    # 앞코 까짐 / 뒤꿈치 쓸림: 밝고 거칠게
    toe = g.ramp(g.math('MULTIPLY', xyz[1], -1.0), 0.09, 0.135)
    heel = g.ramp(xyz[1], 0.1, 0.14)
    scuff = g.math('MULTIPLY', g.math('MAXIMUM', toe, heel), g.ramp(g.noise(60, 6, 0.75, obj, dist=2.0), 0.42, 0.7))
    base = g.mix(g.math('MULTIPLY', scuff, 0.8), base, hk.srgb("#6e5440"))
    # 모서리 닳음 (광 빠진 갈색)
    e = g.math('SUBTRACT', 1.0, g.ao(0.004, inside=True))
    e = g.math('MULTIPLY', g.ramp(e, 0.2, 0.5), g.ramp(g.noise(30, 4, 0.6, obj), 0.35, 0.65))
    base = g.mix(g.math('MULTIPLY', e, 0.7), base, hk.srgb("#7a5a40"))
    # 주름 골 때 (AO)
    a = g.math('SUBTRACT', 1.0, g.ao(0.012))
    base = g.mix(g.math('MULTIPLY', g.ramp(a, 0.05, 0.6), 0.75), base, hk.srgb("#120b07"))
    # 앞코 주름 (발등 꺾이는 곳, 위쪽만)
    flex = g.math('MULTIPLY', g.ramp(xyz[1], -0.075, -0.045), g.math('SUBTRACT', 1.0, g.ramp(xyz[1], -0.02, 0.0)))
    flex = g.math('MULTIPLY', flex, g.ramp(xyz[2], 0.04, 0.065))
    # 볼 라인에 불규칙하고 깊은 주름 2~3개 (기계적인 잔물결 대신)
    wav = g.wave(22, obj, 'Y', 9.0, 3.0)
    crease = g.math('MULTIPLY', g.ramp(wav, 0.72, 0.97), flex)
    base = g.mix(g.math('MULTIPLY', crease, 0.55), base, hk.srgb("#1a110b"))
    rough = g.math('ADD', 0.42, g.math('MULTIPLY', g.noise(25, 4, 0.6, obj), 0.18))
    rough = g.lerp(scuff, rough, 0.75)
    rough = g.lerp(crease, rough, 0.6)
    g.link(base, p.inputs['Base Color'])
    g.link(rough, p.inputs['Roughness'])
    # 범프: 가죽 시보 + 주름
    b1 = g.n('ShaderNodeBump', i_Strength=0.25, i_Distance=0.0003)
    g.link(g.voronoi(900, obj), b1.inputs['Height'])
    b2 = g.n('ShaderNodeBump', i_Strength=0.8, i_Distance=0.0015)
    g.link(g.math('MULTIPLY', crease, 1.0), b2.inputs['Height'])
    g.link(b1.outputs['Normal'], b2.inputs['Normal'])
    g.link(b2.outputs['Normal'], p.inputs['Normal'])
    return m


lea = leather()
lining = hk.P("M_tmp_lining", "#8a7356", 0.8, var=0.12, vs=40, grime=0.8, gd=0.02, gcol="#3a2c1e", bump=0.15, bs=600)
insole = hk.P("M_tmp_insole", "#9c7f5c", 0.75, var=0.15, vs=12, grime=0.9, gd=0.03, gcol="#3b2a1a",
              extra=lambda g, b, r, o: (g.mix(g.ramp(g.noise(5, 3, 0.5, o), 0.4, 0.8), b, hk.srgb("#4a3624")), r))
rubber = hk.P("M_tmp_sole", "#2b231d", 0.78, var=0.06, vs=30, grime=0.5, gd=0.006, gcol="#0f0c0a", edge=0.5, ed=0.002,
              ecol="#5a4c40", erough=0.9, dust=0.7, dz=0.012, dcol="#6b6155", bump=0.1, bs=500)
welt = hk.P("M_tmp_welt", "#3a2a1e", 0.55, var=0.08, vs=40, grime=0.6, gd=0.004, gcol="#120c08", bump=0.3, bs=1400,
            bk='voronoi', dust=0.4, dz=0.03, dcol="#5e5448")
strapm = hk.P("M_tmp_strap", "#33241a", 0.5, var=0.08, vs=20, edge=0.8, ed=0.0015, ecol="#6a4d36", grime=0.5, gd=0.004,
              bump=0.2, bs=900, bk='voronoi')
metal = hk.P("M_tmp_ring", "#8c8478", 0.35, 1.0, var=0.1, grime=0.6, gd=0.003, gcol="#2a2620")

# ---------------------------------------------------------------- 갑피 (오른쪽)
NS, M = 30, 8
S = [(1 - math.cos(math.pi * i / NS)) / 2 for i in range(NS + 1)]
bm = bmesh.new()
R, Lf = [], []
for s in S:
    w = max(width(s), 1e-6)
    xo = opening(s)
    thc = math.pi / 2 if xo <= 0 else math.acos(min(1.0, (xo / w) ** (NEX / 2)))
    R.append([bm.verts.new(upt(s, thc * j / M)) for j in range(M + 1)])
    Lf.append([bm.verts.new(upt(s, math.pi - thc * j / M)) for j in range(M + 1)])
for i in range(NS):
    for j in range(M):
        bm.faces.new((R[i][j], R[i][j + 1], R[i + 1][j + 1], R[i + 1][j]))
        bm.faces.new((Lf[i][j], Lf[i + 1][j], Lf[i + 1][j + 1], Lf[i][j + 1]))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
upper = hk.mesh_obj(A + "_Upper", bm, lea)
upper.data.materials.append(lining)
for p in upper.data.polygons:
    p.use_smooth = True
# 바깥 법선이 밖을 보게 (뒤집혔으면 반전)
ctr = Vector((0, 0, 0.03))
if sum((p.center - ctr).dot(p.normal) for p in upper.data.polygons) < 0:
    for p in upper.data.polygons:
        p.flip()
sol = upper.modifiers.new("Sol", 'SOLIDIFY')
sol.thickness, sol.offset, sol.use_rim = 0.0028, -1.0, True
sol.material_offset = 1          # 안쪽 껍질 = 안감
sol.use_even_offset = True
k3d.apply_all(upper)

# 입구 둘레 패드 (발목 쿠션)
ring = []
for i, s in enumerate(S):
    if opening(s) > 0 or i == 0:
        w = max(width(s), 1e-6)
        xo = opening(s)
        thc = math.pi / 2 if xo <= 0 else math.acos(min(1.0, (xo / w) ** (NEX / 2)))
        ring.append((s, thc))
pr = [upt(s, th, -0.0016) for s, th in ring]
pl = [upt(s, math.pi - th, -0.0016) for s, th in ring]
loop = pr + pl[::-1][:-1] + [pr[0]]
collar = hk.tube(A + "_Collar", [tuple(p) for p in loop], 0.0042, 10, lea)
collar.data.materials.append(lining)

# 깔창
ins = []
for k in range(40):
    t = k / 40 * 2 * math.pi
    s = 0.5 - 0.47 * math.cos(t)
    side = math.sin(t)
    ins.append((xc(s) + side * (width(s) - 0.004), ysec(s)))
bm = bmesh.new()
f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in ins])
o_ins = hk.mesh_obj(A + "_Insole", bm, insole)
for v in o_ins.data.vertices:
    s = 0.5 - v.co.y / L
    v.co.z = sole_top(min(1, max(0, s))) + 0.002
if o_ins.data.polygons[0].normal.z < 0:
    o_ins.data.polygons[0].flip()
hk.finish(o_ins, 0, wn=False)

# ---------------------------------------------------------------- 밑창 (뒤축 두툼 + 앞코 들림)
NSS, NR = 30, 16
bm = bmesh.new()
rings = []
for i in range(NSS + 1):
    u = (1 - math.cos(math.pi * i / NSS)) / 2
    s = -0.018 + u * 1.036
    sc_ = min(1.0, max(0.0, s))
    w = width(sc_, 0.0042)
    if s < 0.0:  # 끝 둥글림 (연장 구간)
        w = w * math.sqrt(max(0, 1 - (s / 0.018) ** 2))
    if s > 1.0:
        w = w * math.sqrt(max(0, 1 - ((s - 1) / 0.018) ** 2))
    zb, zt = sole_bot(sc_), sole_top(sc_)
    zm, hz = (zb + zt) / 2, (zt - zb) / 2
    r = []
    for k in range(NR):
        ph = 2 * math.pi * k / NR
        x = xc(sc_) + w * spow(math.cos(ph), 2 / 6)
        z = zm + hz * spow(math.sin(ph), 2 / 6)
        r.append(bm.verts.new((x, ysec(s), z)))
    rings.append(r)
for i in range(NSS):
    for k in range(NR):
        a, b = rings[i], rings[i + 1]
        bm.faces.new((a[k], a[(k + 1) % NR], b[(k + 1) % NR], b[k]))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
sole = hk.mesh_obj(A + "_Sole", bm, rubber)
for p in sole.data.polygons:
    p.use_smooth = True
# 창 테두리 웰트 (갑피와 창 사이 띠)
wl = []
for k in range(48):
    t = k / 48 * 2 * math.pi
    s = 0.5 - 0.5 * math.cos(t)
    side = math.sin(t)
    sw = width(s, 0.0018)
    wl.append((xc(s) + side * sw, ysec(s), sole_top(s) + 0.0005))
wl.append(wl[0])
weltp = hk.tube(A + "_Welt", wl, 0.0022, 8, welt)
weltp.scale = (1, 1, 1)

# ---------------------------------------------------------------- 벨크로 끈 + D링 (바깥쪽 = -X)
def strap_band(s0, s1, th0, th1, off, name, mat=None, nr=1):
    bm = bmesh.new()
    rows = []
    K = 16
    for s in [s0 + (s1 - s0) * q / nr for q in range(nr + 1)]:
        row = []
        for k in range(K + 1):
            th = th0 + (th1 - th0) * k / K
            row.append(bm.verts.new(upt(s, th, off)))
        rows.append(row)
    for q in range(nr):
        for k in range(K):
            bm.faces.new((rows[q][k], rows[q][k + 1], rows[q + 1][k + 1], rows[q + 1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = hk.mesh_obj(name, bm, mat or strapm)
    for p in o.data.polygons:
        p.use_smooth = True
    if o.data.polygons[K // 2].normal.z < 0:
        for p in o.data.polygons:
            p.flip()
    so = o.modifiers.new("Sol", 'SOLIDIFY')
    so.thickness, so.offset = 0.0028, 1.0
    hk.finish(o, 0.0008, 1, angle=40)
    return o


strap = strap_band(0.43, 0.505, 0.12, math.pi - 0.62, 0.0009, A + "_Strap")
# 바깥쪽 고정 탭 + D링
tab = strap_band(0.43, 0.505, math.pi - 0.62, math.pi - 0.25, 0.0009, A + "_Tab")
dr = upt(0.4675, math.pi - 0.6, 0.0045)
ringo = hk.torus(A + "_DRing", 0.0085, 0.0013, tuple(dr), (0, d2r(90) - 0.6, d2r(90)), metal, nu=16, nv=6, sx=1.0)

shoe = hk.join([upper, collar, o_ins, sole, weltp, strap, tab, ringo], A)
k3d.set_origin(shoe, (0, 0, 0))
k3d.bake(shoe, 2048, ao_distance=0.025)

# 왼짝 = 거울 복제 (같은 텍스처)
left = shoe.copy()
left.data = shoe.data.copy()
bpy.context.scene.collection.objects.link(left)
bm = bmesh.new()
bm.from_mesh(left.data)
for v in bm.verts:
    v.co.x = -v.co.x
for f in bm.faces:
    f.normal_flip()
bm.to_mesh(left.data)
bm.free()
left.name = A + "_L"
shoe.location, shoe.rotation_euler = (-0.06, -0.006, 0), (0, 0, d2r(-4))
left.location, left.rotation_euler = (0.062, 0.014, 0), (0, 0, d2r(3.5))
for o in (shoe, left):
    k3d.select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pair = k3d.join([shoe, left], A)
k3d.set_origin(pair, (0, 0, 0))
for p in pair.data.polygons:
    p.use_smooth = True
hk.socket(A + "_Socket_Grab", (0, 0.03, 0.08), pair)
hk.socket(A + "_Socket_StepIn", (0, 0.18, 0.0), pair)
notes = ("할아버지 갈색 가죽 벨크로 단화 한 켤레 (창 길이 0.28m, 높이 ~0.1m). 원점 = 두 짝 바닥 중앙, 앞코 = -Y (Unity +Z). "
         "프로토타입 위치 three(0.18, -0.13, -1.28) rotY 0.16 = 현관 타일 위 (HomeEntry_Socket_Shoes). "
         "Socket_Grab = 집는/바라보는 점, Socket_StepIn = 신을 때 서는 점(뒤꿈치 쪽). 왼짝은 오른짝 거울 복제(같은 텍스처). "
         "높이 0.098m 는 실제 단화 치수: brief 의 0.135(프로토타입 하이탑 GLB) 기준 validate 경고는 의도한 것.")
k3d.export(A, hk.CAT, [pair], notes=notes)
k3d.preview(A, [pair])
k3d.preview(A, [pair], views=((20, 50),), lens=60, tag='top')
k3d.preview(A, [pair], views=((0, 40),), lens=35, tag='fp')

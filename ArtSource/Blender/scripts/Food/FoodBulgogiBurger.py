# 불고기 버거 (히어로): 아래 번 -> 소스 -> 불고기 글레이즈 패티 -> 양상추 -> 양파 -> 마요 -> 참깨 번 (프로토타입 s0.bulgogi)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *
from mathutils.bvhtree import BVHTree

A = "FoodBulgogiBurger"
k3d.reset()
rnd = random.Random(11)

# ---------------------------------------------------------------- 머티리얼 (전부 2048 한 장으로 굽는다)
def m_crust():
    s = Sh(f"M_{A}_Crust", "#c98a45", 0.4)
    h = s.attr("h")
    lo = s.noise(28, 5, .55)
    hi = s.noise(220, 3, .5)
    hh = s.math('ADD', h, s.math('MULTIPLY', s.math('SUBTRACT', lo, .5), .1))
    col = s.ramp(hh, [(0, "#f2dcaa"), (.2, "#e9bd78"), (.36, "#d99a4c"), (.6, "#c47f37"), (.85, "#b0692a"), (1, "#97541f")])
    spots = s.ramp(s.noise(60, 4, .6), [(.55, (1, 1, 1, 1)), (.72, hexc("#b9845a"))])  # 굽기 얼룩
    col = s.mix(col, spots, .2, 'MULTIPLY')
    col = s.mix(col, "#f1d59b", s.math('MULTIPLY', s.attr("band"), .6))  # 윗번 아래 가장자리 위 연한 띠 (오븐에서 부푼 자리)
    col = s.mix(col, s.ramp(hi, [(0, "#ffffff"), (1, "#d9c2a0")]), .18, 'MULTIPLY')
    col = s.mix(col, "#fff4dc", s.math('MULTIPLY', s.mr(s.noise(14, 2, .4), .55, .75), .18))  # 윤기 밝은 얼룩
    rough = s.math('ADD', s.math('MULTIPLY', h, -.18), s.mr(lo, .3, .7, .38, .52))
    nrm = s.bump(s.math('ADD', hi, s.math('MULTIPLY', lo, 2)), .18, .0004)
    return s.out(col, rough, nrm)


def m_cut():
    s = Sh(f"M_{A}_Cut", "#efd9a8", 0.75)
    x, y, z = s.xyz()
    rad = s.vmath('LENGTH', s.comb(x, y, 0))
    toast = s.math('ADD', s.mr(rad, .028, .046, 1, 0), s.math('MULTIPLY', s.math('SUBTRACT', s.noise(90, 4, .6), .5), .7))
    base = s.ramp(toast, [(.2, "#f2dfb4"), (.55, "#dcb06a"), (.9, "#b97a34")])
    pores = s.voronoi(900)
    base = s.mix(base, "#a07040", s.mr(pores, .0, .25, .35, 0))
    nrm = s.bump(s.mr(pores, 0, .35, 0, 1), .45, .0004)
    return s.out(base, s.mr(pores, 0, .3, .9, .7), nrm)


PZ0, PZ1 = 0.0222, 0.0372


def m_meat():
    s = Sh(f"M_{A}_Meat", "#4a2a18", 0.6)
    x, y, z = s.xyz()
    vc = s.voronoi(320, out='Color')
    sep = s.n('ShaderNodeSeparateColor')
    s.put(sep.inputs[0], vc)
    meat = s.ramp(sep.outputs[0], [(0, "#3a1c0e"), (.45, "#5a3220"), (.8, "#6e4228"), (1, "#8a5a38")])
    char = s.mr(s.noise(35, 6, .65), .52, .68)
    meat = s.mix(meat, "#160a05", s.math('MULTIPLY', char, .85))
    # 불고기 글레이즈: 윗면 + 옆으로 흘러내린 자국 (각도 노이즈로 길이)
    ang = s.math('ARCTAN2', y, x)
    ring = s.comb(s.math('COSINE', ang), s.math('SINE', ang), 0)
    L = s.mr(s.noise(2.2, 2, .5, vec=ring), .42, .66, 0, .012)
    edge = s.math('SUBTRACT', z, s.math('SUBTRACT', PZ1 - 0.0028, L))
    glaze = s.mr(edge, -.0004, .0006)
    glaze = s.math('MULTIPLY', glaze, s.mr(s.noise(70, 3, .5), .3, .45, .55, 1))
    gcol = s.mix("#2a0f05", "#5a2410", s.noise(40, 3, .5))
    col = s.mix(meat, gcol, glaze)
    rough = s.math('MULTIPLY_ADD', glaze, .14 - .62, .62)
    vd = s.voronoi(320)
    nrm = s.bump(s.math('MULTIPLY', s.math('ADD', vd, s.math('MULTIPLY', s.noise(120, 4, .6), .6)),
                        s.math('SUBTRACT', 1, s.math('MULTIPLY', glaze, .75))), .55, .0006)
    return s.out(col, rough, nrm)


def m_glaze():
    s = Sh(f"M_{A}_Glaze", "#3a170a", 0.12)
    col = s.mix("#3a1406", "#7e3814", s.noise(160, 3, .5))
    return s.out(col, s.mr(s.noise(80, 2, .5), .3, .7, .1, .2), s.bump(s.noise(150, 2, .5), .12, .0003))


def m_lettuce():
    s = Sh(f"M_{A}_Lettuce", "#8fc24a", 0.45)
    x, y, z = s.xyz()
    rad = s.math('DIVIDE', s.vmath('LENGTH', s.comb(x, y, 0)), 0.058)
    rr = s.math('ADD', rad, s.math('MULTIPLY', s.math('SUBTRACT', s.noise(30, 3, .5), .5), .3))
    col = s.ramp(rr, [(.2, "#f1f2cf"), (.5, "#d5e597"), (.78, "#a3cc58"), (.92, "#78ad38"), (1, "#5e9528")])
    ang = s.math('ARCTAN2', y, x)
    dist = s.noise(60, 3, .5, dist=2.0)
    vein = s.math('SINE', s.math('ADD', s.math('MULTIPLY', ang, 34), s.math('MULTIPLY', dist, 7)))
    vm = s.math('MULTIPLY', s.mr(vein, .86, 1), s.mr(rad, .3, .9, 1, .2))
    fine = s.voronoi(260, feature='DISTANCE_TO_EDGE')
    fm = s.mr(fine, 0, .06, .35, 0)
    col = s.mix(col, "#f6f7dc", s.math('ADD', s.math('MULTIPLY', vm, .6), s.math('MULTIPLY', fm, .25)))
    col = s.mix(col, s.ramp(s.noise(45, 4, .6), [(0, "#ffffff"), (1, "#d6e2b4")]), .35, 'MULTIPLY')
    nrm = s.bump(s.math('ADD', s.math('ADD', vm, fm), s.math('MULTIPLY', s.noise(200, 5, .65), 1.2)), .3, .0004)
    return s.out(col, s.mr(s.noise(50, 2, .5), .3, .7, .3, .5), nrm)


def m_onion():
    s = Sh(f"M_{A}_Onion", "#f1ecdd", 0.3)
    col = s.mix("#ebe6d8", "#d6cdb6", s.noise(90, 3, .5))
    col = s.mix(col, "#dcc6dc", s.mr(s.attr("rim"), .5, 1, 0, .45))
    return s.out(col, .28, s.bump(s.noise(200, 2, .5), .1, .0003))


def m_mayo():
    s = Sh(f"M_{A}_Mayo", "#f3ead0", 0.2)
    col = s.mix("#f6eed8", "#e9dbb6", s.noise(60, 2, .5))
    col = s.mix(col, "#d8c497", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.003)), .3))  # 얇은 곳/틈은 노르스름하게
    return s.out(col, s.mr(s.noise(40, 2, .5), .3, .7, .14, .22), s.bump(s.noise(90, 2, .4), .12, .0004))


def m_seed():
    s = Sh(f"M_{A}_Sesame", "#f1e2bd", 0.45)
    col = s.mix("#ecdcb4", "#cba26a", s.math('MULTIPLY', s.attr("sr"), .9))
    col = s.mix(col, "#c8a070", s.mr(s.noise(3000, 2, .5), .5, .8, 0, .4))
    return s.out(col, .42, s.bump(s.noise(4000, 2, .5), .1, .0001))


MC, MCUT, MMEAT, MGLAZE, MLET, MON, MMAYO, MSEED = (m_crust(), m_cut(), m_meat(), m_glaze(), m_lettuce(),
                                                    m_onion(), m_mayo(), m_seed())


def wrap_a(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def rf(seed, amp1=.012, amp2=.006):
    return lambda a, i, r, z: 1 + amp1 * nz(math.cos(a) * 2, math.sin(a) * 2, seed) + amp2 * nz(math.cos(a) * 6, math.sin(a) * 6, seed + .7)


# ---------------------------------------------------------------- 아래 번 (heel)
HB = 0.0213
prof = [(0, 0.0), (0.02, 0.0), (0.038, 0.0002), (0.045, 0.0013), (0.0492, 0.0036), (0.0515, 0.007), (0.0524, 0.011),
        (0.0519, 0.0152), (0.0503, 0.0186), (0.0478, 0.0204), (0.044, 0.0211), (0.032, 0.0213), (0.016, 0.0213), (0, 0.0213)]
heel = lathe(f"{A}_Heel", prof, 72, rf(1.3),
             lambda a, i, r, z: (0.0005 * nz(r * math.cos(a) * 90, r * math.sin(a) * 90, 2) if z > .02 else 0))
mats(heel, MC, MCUT)
set_mat_by(heel, lambda c, n: 1 if (n.z > .55 and c.z > .019) else 0)
vattr(heel, "h", lambda co: .12 + .5 * co.z / HB)

# ---------------------------------------------------------------- 패티
prof = [(0, PZ0), (0.03, PZ0), (0.047, PZ0 + .0002), (0.0518, PZ0 + .0012), (0.0537, PZ0 + .0038), (0.0543, PZ0 + .0072),
        (0.0539, PZ0 + .0105), (0.0524, PZ0 + .0133), (0.0496, PZ1 - .0002), (0.044, PZ1 + .0003), (0.034, PZ1 + .0005),
        (0.022, PZ1 + .0006), (0.011, PZ1 + .0006), (0, PZ1 + .0006)]
patty = lathe(f"{A}_Patty", prof, 80,
              lambda a, i, r, z: 1 + .02 * nz(math.cos(a) * 2.5, math.sin(a) * 2.5, 4.1) + .012 * nz(math.cos(a) * 9, math.sin(a) * 9, z * 300),
              lambda a, i, r, z: .0007 * nz(r * math.cos(a) * 140, r * math.sin(a) * 140, 7 + (z > .03)))
mats(patty, MMEAT)


# ---------------------------------------------------------------- 흘러내린 불고기 소스 (방울 모양)
def drips(name, specs, mat):
    bm = bmesh.new()
    for (a, r, ztop, length, width, thick) in specs:
        out = Vector((math.cos(a), math.sin(a), 0))
        tan = Vector((-math.sin(a), math.cos(a), 0))
        M = Matrix((tan, out, Vector((0, 0, 1)))).transposed().to_4x4()
        M.translation = Vector((r * math.cos(a), r * math.sin(a), ztop - length / 2))
        res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.0)
        for v in res['verts']:
            x, y, z = v.co
            w = width * (.35 + .65 * ((1 - z) / 2) ** .6)  # 위는 가늘고 아래는 방울
            v.co = M @ Vector((x * w, y * thick * (.5 + .5 * (1 - z) / 2), z * length / 2))
    o = mesh_obj(name, bm)
    return mats(o, mat)


specs = []
for k in range(7):  # 소스 층 가장자리에서 아래 번 옆면으로 흘러내린 자국
    a = rnd.uniform(-1.5, 1.5) - math.pi / 2 + (math.pi if k > 4 else 0)
    specs.append((a, 0.0526, .0196, rnd.uniform(.005, .011), rnd.uniform(.0022, .0032), .0009))
gl = drips(f"{A}_Drips", specs, MGLAZE)

# 패티 아래 소스 층
sauce = lathe(f"{A}_Sauce", [(0, .0211), (.03, .0211), (.046, .0212), (.0505, .0207), (.0526, .0196), (.0531, .0187), (.0522, .0183),
                             (.0512, .0196), (.0494, .0214), (.0475, .0226), (.03, .0228), (0, .0228)],
              64, lambda a, i, r, z: 1 + (.035 * nz(math.cos(a) * 4, math.sin(a) * 4, 9.2) - .02 if i > 3 else 0))
mats(sauce, MGLAZE)


# ---------------------------------------------------------------- 양상추 (주름진 잎 두 장)
def leaf(name, z, Rl, seed, rot):
    segs, rings = 200, 8
    bm = bmesh.new()
    c = bm.verts.new((0, 0, z))
    R = []
    for i in range(1, rings + 1):
        t = i / rings
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs + rot
            ca, sa = math.cos(a), math.sin(a)
            edge = Rl * (1 + .07 * nz(ca * 3, sa * 3, seed) + .03 * nz(ca * 10, sa * 10, seed + 1) + .012 * math.sin(a * 7 + 2 * nz(ca, sa, seed + 5)))
            r = edge * t
            ruff = (.0032 * math.sin(a * 13 + 3 * nz(ca * 2, sa * 2, seed + 2)) + .0018 * nz(ca * 8, sa * 8, seed + 3)) * t ** 2.2 \
                + (.0012 * math.sin(a * 19 + 4 * nz(ca * 5, sa * 5, seed + 4)) + .0006 * math.sin(a * 29 + 3 * nz(ca * 3, sa * 3, seed + 6))) * t ** 5  # 가장자리 잔물결
            droop = -max(0.0, r - .05) * .55
            zz = z + ruff + droop + .0005 * nz(r * ca * 160, r * sa * 160, seed)
            ring.append(bm.verts.new((r * ca, r * sa, zz)))
        R.append(ring)
    for k in range(segs):
        bm.faces.new((c, R[0][k], R[0][(k + 1) % segs]))
    for A_, B_ in zip(R, R[1:]):
        for k in range(segs):
            bm.faces.new((A_[k], A_[(k + 1) % segs], B_[(k + 1) % segs], B_[k]))
    o = mesh_obj(name, bm)
    solidify(o, .0009, 0)
    o.modifiers["Solid"].use_even_offset = False  # 촘촘한 물결에서 even offset 은 가시를 만든다
    return mats(o, MLET)


let1 = leaf(f"{A}_Lettuce1", .0393, .0585, 3.3, 0)
let2 = leaf(f"{A}_Lettuce2", .0408, .0555, 8.1, .6)

# ---------------------------------------------------------------- 양파 링
onions = []
for (ox, oy, R0, rot) in ((.014, -.026, .0235, .1), (-.018, -.006, .017, .5), (.006, .02, .019, .2), (.026, .012, .012, .9)):
    bm = bmesh.new()
    seg, sides, rr = 40, 8, .0017
    rings = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        ring = []
        for j in range(sides):
            b = 2 * math.pi * j / sides
            r = R0 + rr * math.cos(b)
            ring.append(bm.verts.new((ox + r * math.cos(a), oy + r * math.sin(a), .0428 + .55 * rr * math.sin(b) + .0006 * math.sin(a * 3 + rot))))
        rings.append(ring)
    for k in range(seg):
        for j in range(sides):
            bm.faces.new((rings[k][j], rings[(k + 1) % seg][j], rings[(k + 1) % seg][(j + 1) % sides], rings[k][(j + 1) % sides]))
    o = mesh_obj(f"{A}_Onion{len(onions)}", bm)
    vattr(o, "rim", lambda co, ox=ox, oy=oy, R0=R0: 1.0 if math.hypot(co.x - ox, co.y - oy) > R0 + .001 else 0.0)
    onions.append(mats(o, MON))

# ---------------------------------------------------------------- 마요 (윗번 아래, 가장자리로 흘러내림)
mayo = lathe(f"{A}_Mayo", [(0, .0433), (.03, .0433), (.042, .0435), (.0465, .0441), (.044, .0449), (.03, .0451), (0, .0451)],
             96, lambda a, i, r, z: 1 + .1 * nz(math.cos(a) * 4, math.sin(a) * 4, 2.4) + .05 * nz(math.cos(a) * 11, math.sin(a) * 11, 1) + .025 * nz(math.cos(a) * 25, math.sin(a) * 25, 6))
mats(mayo, MMAYO)

# ---------------------------------------------------------------- 윗번 (crown) + 참깨
Z0, HC, RC = .0449, .0425, .0535
prof = [(0, Z0 + .0004), (.03, Z0 + .0002), (.0455, Z0), (.0498, Z0 + .0011), (.0522, Z0 + .0036)]
for k in range(22):
    th = math.pi / 2 * math.sin(math.pi / 2 * k / 21)
    prof.append((RC * math.cos(th) ** .78, Z0 + .0072 + (HC - .0072) * math.sin(th) ** 1.1))
prof[-1] = (0, Z0 + HC)
crown = lathe(f"{A}_Crown", prof, 80, rf(5.5, .014, .006),
              lambda a, i, r, z: .0016 * nz(math.cos(a) * 1.5, math.sin(a) * 1.5, 3) * max(0, (z - Z0) / HC) * min(1, r / RC) ** 2 + .0003 * nz(r * math.cos(a) * 120, r * math.sin(a) * 120, 1))
mats(crown, MC, MCUT)
set_mat_by(crown, lambda c, n: 1 if (n.z < -.55 and c.z < Z0 + .002) else 0)
vattr(crown, "h", lambda co: .3 + .7 * max(0, (co.z - Z0) / HC))
vattr(crown, "band", lambda co: math.exp(-((co.z - Z0 - .0062) / .0017) ** 2))

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(crown, dg)
bm = bmesh.new()
seeds = []
while len(seeds) < 96:
    r = .046 * math.sqrt(rnd.random())
    a = rnd.uniform(0, 2 * math.pi)
    hit = bvh.ray_cast(Vector((r * math.cos(a), r * math.sin(a), .2)), Vector((0, 0, -1)))
    if hit[0] is None or any((hit[0] - p).length < .0042 for p in seeds):
        continue
    p, n = hit[0], hit[1].normalized()
    seeds.append(p)
    t = n.cross(Vector((0, 0, 1)))
    t = (t if t.length > 1e-4 else Vector((1, 0, 0))).normalized()
    t = Matrix.Rotation(rnd.uniform(0, math.pi * 2), 3, n) @ t
    M = Matrix((t, n.cross(t), n)).transposed().to_4x4()
    M.translation = p + n * .00018
    res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    L = rnd.uniform(.0015, .0019)
    for v in res['verts']:
        x, y, z = v.co
        v.co = M @ Vector((x * L, y * L * .55 * (1 - .3 * x), z * .00055))
seed_o = mesh_obj(f"{A}_Seeds", bm)
mats(seed_o, MSEED)
vattr(seed_o, "sr", lambda co: max(0.0, nz(co.x * 900, co.y * 900, co.z * 900)))

# ---------------------------------------------------------------- 마요 드립 (양상추 위로 번지고 가장자리에서 늘어짐)
lbvh = [BVHTree.FromObject(o, dg) for o in (let1, let2)]


def leaf_hit(r, a):
    best = None
    for b in lbvh:
        h = b.ray_cast(Vector((r * math.cos(a), r * math.sin(a), .06)), Vector((0, 0, -1)))
        if h[0] is not None and (best is None or h[0].z > best[0].z):
            best = (h[0], h[1].normalized())
    return best


def leaf_edge(a):
    rr, last = .044, None
    while rr < .068:
        h = leaf_hit(rr, a)
        if h is None:
            break
        last = (rr, h)
        rr += .0004
    return last


bm = bmesh.new()


mayo_specs, tries = [], 0
while len(mayo_specs) < 6 and tries < 200:
    tries += 1
    a = -math.pi / 2 + rnd.uniform(-1.35, 1.35) if len(mayo_specs) < 5 else math.pi / 2 + rnd.uniform(-.8, .8)
    if any(abs(wrap_a(a - b)) < .32 for b, *_ in mayo_specs):
        continue
    e = leaf_edge(a)
    if e is None or e[0] < .0565:  # 패티보다 충분히 바깥에 있는 가장자리만
        continue
    mayo_specs.append((a, e[0], e[1][0].z))
for (a, re_, ze) in mayo_specs:
    out, tan = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    w = rnd.uniform(.0024, .0036)
    # 잎 위로 번진 마요: 구 하나를 잎 표면에 덮어씌움 (정점마다 위에서 쏴서 표면+법선 따라 두께) — 겹치는 방울 없이 매끈한 한 덩어리
    r0, r1 = .046, re_ - .0004
    res = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=14, radius=1.0)
    for v in res['verts']:
        x_, y_, z_ = v.co  # z = 길이 방향(극점 = 양 끝), x = 폭, y = 두께
        f = (z_ + 1) / 2
        rr = r0 + (r1 - r0) * f
        h = None
        for k in range(12):  # 잎 밖이면 안쪽으로 당겨서 다시
            h = leaf_hit(rr - .0005 * k, a + x_ * w * (1.15 - .3 * f) / rr)
            if h:
                break
        p, n = h
        v.co = p + n * (.00012 + .0009 * (y_ if y_ > 0 else .3 * y_))
    L = rnd.uniform(.006, .012)
    zt = ze + .0012
    cnt = Vector((math.cos(a) * (re_ + .0008), math.sin(a) * (re_ + .0008), 0))
    res = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=1.0)
    for v in res['verts']:  # 가장자리에서 늘어진 방울: 위는 가늘고 아래는 둥글게
        x_, y_, z_ = v.co
        k = (1 - z_) / 2
        ww = w * (.5 + .38 * k ** 1.5) * (1 + .12 * math.sin(z_ * 5 + a))
        v.co = cnt + tan * x_ * ww + out * y_ * .0011 * (.6 + .4 * k) + Vector((0, 0, zt - L / 2 + z_ * L / 2))
md = mesh_obj(f"{A}_MayoDrips", bm)
mats(md, MMAYO)
print("FoodBulgogiBurger: mayo drips", [(round(a, 2), round(r_, 4), round(z_, 4)) for a, r_, z_ in mayo_specs])

# ---------------------------------------------------------------- 합치고 굽기
parts = [heel, sauce, patty, gl, let1, let2, *onions, mayo, md, crown, seed_o]
for o in parts:
    smooth(o, 180 if "Lettuce" in o.name or "Drips" in o.name else 60)
    for nm in ("h", "rim", "sr", "band"):
        if nm not in o.data.attributes:
            const_attr(o, nm, 0.0)
body = join(parts, f"{A}_Mesh")
k3d.bake(body, size=2048, samples=64)
socket(body, A, "Grip", (0, 0, .045))
socket(body, A, "LookTarget", (0, -.03, .07))
k3d.export(A, "Food", [body], notes={
    "desc": "불고기 버거(히어로). 단일 정적 메시. 정면 -Y(Unity +Z), 원점 바닥 중앙. 지름 약 0.11m, 높이 약 0.089m.",
    "sockets": {"FoodBulgogiBurger_Socket_Grip": "손으로 쥘 때 중심", "FoodBulgogiBurger_Socket_LookTarget": "시선/카메라 포커스"}})
k3d.preview(A, [body])
k3d.preview(A, [body], views=((0, 8),), lens=35, tag='fp')
k3d.preview(A, [body], views=((20, 55),), tag='top')

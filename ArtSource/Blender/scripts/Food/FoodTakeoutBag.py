# 크라프트 종이 포장백: 옆 주름(거싯) + 안으로 접힌 윗단 + 꼰 종이 손잡이 + 로고 인쇄 + 냅킨 (포장 주문 결과물)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

A = "FoodTakeoutBag"
W, D, H = 0.26, 0.15, 0.30
HEM = 0.03
textures()
k3d.reset()
rnd = random.Random(5)

# ---------------------------------------------------------------- 머티리얼
def kraft_base(s, dark=0.0):
    x, y, z = s.xyz()
    streak = s.vmath('MULTIPLY', s.tc(), (1.0, 1.0, .22))
    fib = s.noise(700, 2, .5, vec=streak)
    col = s.ramp(s.noise(9, 4, .55), [(.3, "#a77b4b"), (.7, "#c09264")])
    col = s.mix(col, "#8c6238", s.mr(fib, .6, .75, 0, .5))
    col = s.mix(col, "#d4b386", s.mr(s.noise(1500, 1, .5), .68, .78, 0, .5))
    if dark:
        col = s.mix(col, "#000000", dark)
    return col


s = Sh(f"M_{A}_Kraft", "#b98e5e", .88)
x, y, z = s.xyz()
nx, ny, nzz = s.xyz(s.tc('Normal'))
col = kraft_base(s)
front, back = s.math('LESS_THAN', ny, -.5), s.math('GREATER_THAN', ny, .5)
side = s.math('GREATER_THAN', s.math('ABSOLUTE', nx), .5)
v = s.math('DIVIDE', z, H)
u_fb = s.math('ADD', s.math('MULTIPLY', s.math('DIVIDE', x, W), s.math('SUBTRACT', 1, s.math('MULTIPLY', back, 2))), .5)
u_sd = s.math('ADD', s.math('MULTIPLY', s.math('DIVIDE', y, D), s.math('SUBTRACT', s.math('MULTIPLY', s.math('GREATER_THAN', nx, 0), 2), 1)), .5)
a_fb = s.image(os.path.join(TEX, "bag_front.png"), s.comb(u_fb, v, 0), ext='CLIP', out='Alpha')
a_sd = s.image(os.path.join(TEX, "bag_side.png"), s.comb(u_sd, v, 0), ext='CLIP', out='Alpha')
ink = s.math('ADD', s.math('MULTIPLY', a_fb, s.math('ADD', front, back)), s.math('MULTIPLY', a_sd, side))
ink = s.math('MULTIPLY', ink, s.mr(s.noise(300, 2, .5), .3, .7, .78, .95))  # 크라프트에 스며든 잉크 얼룩
col = s.mix(col, "#3a2416", ink)
grease = s.math('MULTIPLY', s.mr(s.noise(6, 3, .6, vec=s.vmath('ADD', s.tc(), (.3, .1, 0))), .58, .66), s.mr(z, .03, .14, 1, 0))
col = s.mix(col, "#6e4a26", s.math('MULTIPLY', grease, .75))  # 감자튀김 기름 자국
col = s.mix(col, "#5a3e22", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.02)), .5))  # 주름 사이 때
crease = s.voronoi(14, feature='DISTANCE_TO_EDGE')
nrm = s.bump(s.math('ADD', s.mr(crease, 0, .04, 1, 0), s.math('MULTIPLY', s.noise(500, 3, .5), .5)), .25, .0006)
MK = s.out(col, s.math('ADD', s.math('MULTIPLY', grease, -.3), s.mr(s.noise(80, 2, .5), .3, .7, .82, .92)), nrm)

s = Sh(f"M_{A}_KraftIn", "#a98257", .9)
x, y, z = s.xyz()
col = kraft_base(s, .12)
hem = s.math('GREATER_THAN', z, H - HEM)
col = s.mix(col, "#c49c6c", s.math('MULTIPLY', hem, .5))
col = s.mix(col, "#2a1a0c", s.math('MULTIPLY', s.mr(z, .02, .2, .55, 0), 1))  # 안쪽 아래는 어둡게
MKI = s.out(col, .9, s.bump(s.math('ADD', hem, s.math('MULTIPLY', s.noise(400, 3, .5), .3)), .3, .0005))

s = Sh(f"M_{A}_Rope", "#a4784a", .85)
w1 = s.wave(260, 3, direction='DIAGONAL', detail=1)
col = s.mix("#8f6538", "#c39a68", w1)
MR = s.out(col, .85, s.bump(w1, .6, .0008))

s = Sh(f"M_{A}_Napkin", "#f2eee4", .92)
col = s.mix("#f6f3ec", "#ddd6c6", s.mr(s.noise(40, 3, .5), .3, .7))
col = s.mix(col, "#a08a6a", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.03)), .6))
MN = s.out(col, .92, s.bump(s.noise(800, 2, .5), .1, .0003))

# ---------------------------------------------------------------- 몸통 (둘레를 한 바퀴 도는 띠 + 바닥)
C = 0.007  # 옆 주름 깊이
outline = []
for i in range(16):
    outline.append((-W / 2 + W * i / 16, -D / 2, 'F', 0))
for i in range(8):
    t = i / 8
    outline.append((W / 2 - C * (1 - abs(1 - 2 * t)), -D / 2 + D * t, 'R', 1 - abs(1 - 2 * t)))
for i in range(16):
    outline.append((W / 2 - W * i / 16, D / 2, 'B', 0))
for i in range(8):
    t = i / 8
    outline.append((-W / 2 + C * (1 - abs(1 - 2 * t)), D / 2 - D * t, 'L', 1 - abs(1 - 2 * t)))
zs = [0, .006, .02, .045, .066, .072, .078, .1, .13, .16, .19, .22, .245, .262, H - HEM, H - .02, H - .01, H - .004, H]
NRM = {'F': Vector((0, -1, 0)), 'B': Vector((0, 1, 0)), 'R': Vector((1, 0, 0)), 'L': Vector((-1, 0, 0))}
bm = bmesh.new()
rings = []
for z in zs:
    ring = []
    gus = .009 * min(1.0, max(0.0, (z - (H - .1)) / .1)) ** 1.5  # 옆 거싯이 윗단 쪽에서 더 안으로 접혀 V
    for k, (x, y, side, tri) in enumerate(outline):
        n = NRM[side]
        corner = min(abs(abs(x) - W / 2), abs(abs(y) - D / 2)) if side in 'FB' else min(abs(abs(y) - D / 2), 1)
        pin = min(1.0, corner / .02) * min(1.0, z / .03)
        crumple = .0028 * nz(x * 22, y * 22, z * 22 + 3) + .001 * nz(x * 70, y * 70, z * 70)
        fold = -.0016 * math.exp(-((z - .072) / .005) ** 2) - .0011 * math.exp(-((z - .02) / .004) ** 2)  # 납작하게 접혀 있던 자국 + 바닥 접힘선
        bulge = .0016 * math.sin(math.pi * (x / W + .5)) * math.sin(math.pi * min(1.0, z / (H - HEM))) if side in 'FB' else 0.0
        off = (crumple * pin + fold * pin + bulge) * (1 if z < H - .002 else .6) - gus * tri
        ring.append(bm.verts.new((x + n.x * off, y + n.y * off, z)))
    rings.append(ring)
N = len(outline)
for a, b in zip(rings, rings[1:]):
    for k in range(N):
        bm.faces.new((a[k], a[(k + 1) % N], b[(k + 1) % N], b[k]))
bottom = bm.faces.new(list(reversed(rings[0])))
bmesh.ops.triangulate(bm, faces=[bottom])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
body = mesh_obj(f"{A}_Body", bm)
mats(body, MK, MKI)
solidify(body, .0006, -1, 1, 1)
bevel(body, .0012, 2, 35)
smooth(body, 25)

# ---------------------------------------------------------------- 손잡이 (꼰 종이끈) + 안쪽 접착 패치
def tube(name, pts, r, sides=8):
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(Vector((0, 1, 0))).normalized()
        b = t.cross(a).normalized()
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * j / sides) + b * math.sin(2 * math.pi * j / sides)) * r)
                      for j in range(sides)])
    for A_, B_ in zip(rings, rings[1:]):
        for j in range(sides):
            bm.faces.new((A_[j], A_[(j + 1) % sides], B_[(j + 1) % sides], B_[j]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


handles, patches = [], []
HX, HUP = .052, .082
for sgn in (-1, 1):
    yy = sgn * (D / 2 - .0034)
    pts = [Vector((-HX, yy, H - .045)), Vector((-HX, yy, H - .02)), Vector((-HX, yy, H))]
    for k in range(1, 22):
        t = math.pi * k / 22
        pts.append(Vector((-HX * math.cos(t) * (1 + .12 * math.sin(t)), yy - sgn * .006 * math.sin(t), H + HUP * math.sin(t) ** .8)))
    pts += [Vector((HX, yy, H)), Vector((HX, yy, H - .02)), Vector((HX, yy, H - .045))]
    h = tube(f"{A}_Handle{'F' if sgn < 0 else 'B'}", pts, .0026)
    handles.append(mats(h, MR))
    bm = bmesh.new()
    py = sgn * (D / 2 - .0007)
    vs = [bm.verts.new((x_, py, z_)) for x_, z_ in ((-.075, H - .055), (.075, H - .055), (.075, H - .011), (-.075, H - .011))]
    bm.faces.new(vs if sgn > 0 else vs[::-1])
    p = mesh_obj(f"{A}_Patch{'F' if sgn < 0 else 'B'}", bm)
    solidify(p, .0004, 1)
    patches.append(mats(p, MKI))

# ---------------------------------------------------------------- 안에 채운 구겨진 냅킨 (빈 봉투처럼 보이지 않게)
bm = bmesh.new()
nxn, nyn = 26, 15
g = [[bm.verts.new((-W / 2 + .014 + (W - .028) * i / nxn, -D / 2 + .006 + (D - .012) * j / nyn,
                    .205 + .022 * nz(i * .35, j * .35, 1.7) + .008 * nz(i * 1.1, j * 1.1, 4) - .03 * (max(abs(i / nxn - .5), abs(j / nyn - .5)) * 2) ** 3))
      for i in range(nxn + 1)] for j in range(nyn + 1)]
for j in range(nyn):
    for i in range(nxn):
        bm.faces.new((g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]))
nap = mesh_obj(f"{A}_Napkin", bm)
mats(nap, MN)
smooth(nap, 180)

parts = [body, *handles, *patches, nap]
for o in handles:
    smooth(o, 180)
me = join(parts, f"{A}_Mesh")
k3d.bake(me, size=1024, samples=48)
socket(me, A, "Grip", (0, 0, H + HUP - .004))
socket(me, A, "Contents", (0, 0, .004))
k3d.export(A, "Food", [me], notes={
    "desc": "크라프트 포장백 (불고기 버거 세트 포장 결과물). 0.26 x 0.15 x 0.30m + 손잡이(전체 높이 약 0.385m). 정면 -Y 에 로고, 옆면 분리배출 표시. "
            "윗단 3cm 안쪽 접힘, 손잡이 2개(앞/뒤). 원점 바닥 중앙.",
    "sockets": {f"{A}_Socket_Grip": "손잡이 두 개를 함께 쥐는 점", f"{A}_Socket_Contents": "봉투 안 바닥 (내용물 배치 기준)"}})
k3d.preview(A, [me])
k3d.preview(A, [me], views=((10, 40),), tag='top')
k3d.preview(A, [me], views=((90, 30), (180, 30), (270, 30)), tag='review')

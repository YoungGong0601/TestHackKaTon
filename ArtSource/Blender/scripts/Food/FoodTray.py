# 패스트푸드 플라스틱 쟁반 + 인쇄된 종이 깔지 (깔지는 굽지 않고 2048 원본 그대로 써서 글씨를 선명하게)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

A = "FoodTray"
HX, HY, RC = 0.205, 0.155, 0.03     # 바깥 반폭, 반깊이, 모서리 반지름
FLOOR = 0.006                        # 바닥 윗면 (안쪽 깊이 약 1.6cm, 음식은 소켓 높이에 놓는다)
textures()
k3d.reset()

# ---------------------------------------------------------------- 머티리얼
s = Sh(f"M_{A}_Plastic", "#4b2218", .4)
x, y, z = s.xyz()
col = s.mix("#4b2218", "#45201a", s.noise(5, 2, .5))                                     # 큰 얼룩 없이 거의 균일
col = s.mix(col, "#6b3a2a", s.math('MULTIPLY', s.mr(s.noise(1400, 2, .5), .6, .7), .35))  # 고운 반점 (성형 플라스틱 결)
col = s.mix(col, "#2c120b", s.math('MULTIPLY', s.mr(s.noise(1100, 2, .5, vec=s.vmath('ADD', s.tc(), (.3, .1, 0))), .6, .7), .3))
sc1 = s.mr(s.wave(900, 18, direction='X', detail=3), .94, 1)  # 잔 흠집 (긴 방향)
sc2 = s.mr(s.wave(700, 22, direction='Y', detail=3), .95, 1)
scr = s.math('MULTIPLY', s.math('MAXIMUM', sc1, sc2), s.mr(s.noise(9, 2, .5), .45, .65))
rimtop = s.mr(z, .0185, .0215)  # 테두리 윗면 닳음
col = s.mix(col, "#8a5a46", s.math('ADD', s.math('MULTIPLY', scr, .35), s.math('MULTIPLY', rimtop, .12)))
col = s.mix(col, "#1c0d08", s.math('MULTIPLY', s.mr(s.ao(.012), .85, .4), .6))  # 때는 오목한 안쪽 구석에만
grip = s.math('MULTIPLY', s.mr(s.math('ABSOLUTE', x), HX - .03, HX - .012), s.mr(s.math('SINE', s.math('MULTIPLY', y, 900)), .2, 1))
stip = s.noise(2500, 1, .5)
rough = s.math('ADD', s.mr(s.noise(30, 2, .5), .3, .7, .32, .44), s.math('ADD', s.math('MULTIPLY', scr, .25), s.math('MULTIPLY', rimtop, .1)))
MP = s.out(col, rough, s.bump(s.math('ADD', s.math('MULTIPLY', stip, .25), s.math('ADD', s.math('MULTIPLY', grip, .8), s.math('MULTIPLY', scr, -.4))), .25, .0004))

ML = k3d.mat(f"M_{A}_Liner", (1, 1, 1), .85)  # 굽지 않음: 깔지 이미지를 그대로 사용 (2048)
k3d.image_node(ML, k3d.load_image(os.path.join(TEX, "tray_liner.png")), k3d.principled(ML).inputs['Base Color'], uv="UVMap")

# ---------------------------------------------------------------- 쟁반: 둥근 사각 링을 단면 프로필로 이어 붙임
def ring_pts(d):
    r = max(RC - d, .003)
    cx, cy = HX - d - r, HY - d - r
    pts = []
    for (sx, sy, a0) in ((1, -1, -90), (1, 1, 0), (-1, 1, 90), (-1, -1, 180)):
        for k in range(7):
            a = math.radians(a0 + 90 * k / 6)
            pts.append((sx * cx + r * math.cos(a), sy * cy + r * math.sin(a)))
    out = []
    n = len(pts)
    for i in range(n):  # 직선 구간을 잘게 나눔
        p, q = pts[i], pts[(i + 1) % n]
        out.append(p)
        steps = (7 if (i // 7) % 2 == 0 else 10) if i % 7 == 6 else 0  # 짧은 변 7칸, 긴 변 10칸 (링마다 같은 점 수)
        for k in range(1, steps + 1):
            t = k / (steps + 1)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


prof = [(.115, FLOOR), (.075, FLOOR), (.045, FLOOR), (.03, FLOOR + .0001), (.026, FLOOR + .0008), (.0235, FLOOR + .0025),
        (.0215, FLOOR + .0055), (.0195, FLOOR + .0095), (.0172, FLOOR + .0135), (.0145, .0221), (.010, .0222), (.0065, .0216),
        (.0035, .0198), (.0015, .016), (.0005, .008), (0, .0025), (.0004, .0005), (.0025, 0), (.0045, .0006), (.006, .0021),
        (.0075, .0029), (.012, .0032), (.04, .0032), (.1, .0032)]
counts = {len(ring_pts(d)) for d, _ in prof}
assert len(counts) == 1, counts  # 모든 링의 점 수가 같아야 이어 붙일 수 있다
bm = bmesh.new()
rings = [[bm.verts.new((px, py, z)) for (px, py) in ring_pts(d)] for d, z in prof]
N = len(rings[0])
for a, b in zip(rings, rings[1:]):
    for k in range(N):
        bm.faces.new((a[k], a[(k + 1) % N], b[(k + 1) % N], b[k]))
for R_ in (rings[0], rings[-1]):
    f = bm.faces.new(R_)
    bmesh.ops.triangulate(bm, faces=[f])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
tray = mesh_obj(f"{A}_Body", bm)
mats(tray, MP)
smooth(tray, 50)

# ---------------------------------------------------------------- 깔지 (살짝 우는 종이, 모서리 들뜸)
LW, LD, LZ = 0.354, 0.256, FLOOR + .0003
nx_, ny_ = 24, 18
bm = bmesh.new()
uvs = {}
g = []
for j in range(ny_ + 1):
    row = []
    for i in range(nx_ + 1):
        u, v = i / nx_, j / ny_
        cx, cy = (u - .5) * LW, (v - .5) * LD
        corner = max(0.0, (abs(u - .5) * 2) ** 6 + (abs(v - .5) * 2) ** 6 - .5)
        zz = LZ + .0004 * (nz(u * 3, v * 3, 2) + 1) + .0035 * corner * (1 + nz(u * 2, v * 2, 5))
        vt = bm.verts.new((cx, cy, zz))
        uvs[vt] = (u, v)
        row.append(vt)
    g.append(row)
uvl = bm.loops.layers.uv.new("UVMap")
for j in range(ny_):
    for i in range(nx_):
        f = bm.faces.new((g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]))
        for l in f.loops:
            l[uvl].uv = uvs[l.vert]
liner = mesh_obj(f"{A}_Liner", bm)
mats(liner, ML)
smooth(liner, 180)

me = join([tray, liner], f"{A}_Mesh")
k3d.bake(me, size=1024, samples=48, keep=(f"M_{A}_Liner",))
top = LZ + .0002
for nm, p in (("Burger", (-.08, -.02, top)), ("Fries", (.10, .05, top)), ("Cup", (.125, -.075, top)), ("Pager", (-.07, .085, top)),
              ("GripL", (-HX + .008, 0, .02)), ("GripR", (HX - .008, 0, .02))):
    socket(me, A, nm, p)
k3d.export(A, "Food", [me], notes={
    "desc": "패스트푸드 쟁반 0.41 x 0.31 x 0.022m (바닥 윗면 0.006m, 깔지 윗면 약 0.0065m, 안쪽 깊이 약 1.6cm). 음식은 FoodTray_Socket_* 위치에 놓는다. 정면 -Y, 원점 바닥 중앙.",
    "liner": "M_FoodTray_Liner 는 굽지 않은 2048 원본 텍스처(UV 0-1 이 깔지 전체, U 오른쪽 V 위쪽). 앱 주문 홍보·'주문은 키오스크에서만' 안내 문구 인쇄.",
    "sockets": {f"{A}_Socket_Burger": "버거 자리", f"{A}_Socket_Fries": "감자튀김 자리", f"{A}_Socket_Cup": "음료 자리",
                f"{A}_Socket_Pager": "진동벨 자리", f"{A}_Socket_GripL": "왼손 잡는 곳", f"{A}_Socket_GripR": "오른손 잡는 곳"}})
k3d.preview(A, [me])
k3d.preview(A, [me], views=((0, 50),), lens=35, tag='fp')

# 약 봉투 (새봄 약국) — 부풀어 오른 종이 봉투 + 접힌 윗단 + 스테이플
import sys, math, random
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "HomeMedicineBag"
W, H, D = 0.13, 0.168, 0.026
rnd = random.Random(4)
paper = hk.P("M_tmp_bagpaper", (1, 1, 1), 0.82, img=hk.tex("medbag.png"), imode='base', var=0.05, vs=30,
             grime=0.12, gd=0.008, gcol="#9a9280", bump=0.12, bs=900, bd=0.0002, dust=0.15, dz=0.015)

# 앞뒤가 가장자리에서 만나는 베개형 봉투 (가운데 약 포장으로 불룩)
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
nx, nz = 14, 16
wob = {}
def bul(u, v):
    return (math.sin(math.pi * u) ** 0.55) * (math.sin(math.pi * v) ** 0.45)
def pos(u, v, side):
    k = (u, v)
    if k not in wob:
        wob[k] = (rnd.uniform(-1, 1) * 0.0012, rnd.uniform(-1, 1) * 0.0008)
    b = bul(u, v) * D / 2 + (wob[k][0] if 0 < u < 1 and 0 < v < 1 else 0)
    return Vector(((u - 0.5) * W + wob[k][1] * bul(u, v), side * b, v * H))
grid = {}
for side in (-1, 1):
    for j in range(nz + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / nz
            edge = i in (0, nx) or j in (0, nz)
            key = (i, j, 0 if edge else side)
            if key not in grid:
                grid[key] = bm.verts.new(pos(u, v, side))
for side in (-1, 1):
    for j in range(nz):
        for i in range(nx):
            def g(ii, jj):
                e = ii in (0, nx) or jj in (0, nz)
                return grid[(ii, jj, 0 if e else side)]
            q = [g(i, j), g(i + 1, j), g(i + 1, j + 1), g(i, j + 1)]
            if side > 0:
                q = q[::-1]
            f = bm.faces.new(q)
            for l in f.loops:
                u = l.vert.co.x / W + 0.5
                v = l.vert.co.z / H
                # 앞면 = 아틀라스 왼쪽 절반, 뒷면 = 오른쪽 절반 (뒤에서 볼 때 바로 읽힘)
                l[uvl].uv = (u * 0.5, v) if side < 0 else (0.5 + (1 - u) * 0.5, v)
for v in bm.verts:
    for (a, b, c, amp) in ((0.3, 1.0, -0.06, 0.0009), (-0.8, 1.0, 0.11, 0.0007), (1.0, 0.25, -0.02, 0.0006)):
        d = (a * v.co.x + b * v.co.z * 0.6 + c) / math.hypot(a, b * 0.6)
        v.co.y += amp * math.exp(-(d / 0.004) ** 2) * (1 if v.co.y <= 0 else -1) * min(1, abs(v.co.y) / 0.003)
bm.normal_update()
body = hk.mesh_obj(A + "_Body", bm, paper)
for p in body.data.polygons:
    p.use_smooth = True
# 두께감: 아주 얇은 solidify
s = body.modifiers.new("Sol", 'SOLIDIFY')
s.thickness, s.offset = 0.0006, 1

# 윗단 접힌 날개 (앞으로 한 번 접힘)
fl = hk.quad(A + "_Flap", W * 0.97, 0.02, paper, loc=(0, -0.0032, H - 0.0105), rot=(math.radians(-4), 0, 0),
             uv=(0.5, 0.93, 1.0, 0.985), nx=6, ny=2)
fl.modifiers.new("Sol", 'SOLIDIFY').thickness = 0.0006
# 접힌 선 (둥근 말림)
fold = hk.tube(A + "_Fold", [(-W / 2 + 0.001, -0.0012, H + 0.0005), (W / 2 - 0.001, -0.0012, H + 0.0005)], 0.0016, 8, paper)
# 스테이플
st = hk.P("M_tmp_staple", "#b8b8bc", 0.3, 1.0)
staple = hk.tube(A + "_Staple", [(-0.006, -0.0052, H - 0.006), (-0.006, -0.0058, H - 0.004), (0.006, -0.0058, H - 0.004),
                                 (0.006, -0.0052, H - 0.006)], 0.0005, 6, st)
obj = hk.join([body, fl, fold, staple], A)
k3d.origin_bottom(obj)
obj.location = (0, 0, 0)
k3d.bake(obj, 1024, ao_distance=0.02)
hk.socket(A + "_Socket_Grab", (0, 0, H * 0.6), obj)
notes = ("약 봉투 0.13x0.17x0.026m, 원점 바닥 중앙, 정면(-Y)=약 봉투 앞면(새봄 약국 인쇄). "
         "프로토타입 위치: 신발장 위 (three -0.84, 0.96, -1.45) 기울임 rot z 0.12. Socket_Grab=집는 점.")
k3d.export(A, hk.CAT, [obj], notes=notes)
k3d.preview(A, [obj])
k3d.preview(A, [obj], views=((0, 5),), lens=80, tag='front')

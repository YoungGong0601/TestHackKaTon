# 손주가 써 준 메모 (수첩에서 찢은 한 장, 4등분 접었다 편 자국) — 앞면 M_Dyn_Memo_Paper (손글씨 placeholder)
import sys, math, random
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ik as ik, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "Memo"
W, H, T = 0.165, 0.21, 0.00012        # 프로토타입 PlaneGeometry(.165,.21) 와 같은 크기
NX, NZ = 36, 46
rnd = random.Random(8)

# 찢긴 윗변: 칸마다 들쭉날쭉 + 군데군데 크게 뜯김
tear = [rnd.uniform(0.0, 0.0011) for _ in range(NX + 1)]
for c in (5, 6, 21, 30, 31):
    tear[c] += rnd.uniform(0.0008, 0.0016)


def sm(d, e=0.0012):
    return math.sqrt(d * d + e * e) - e


def disp(x, z):
    """접힌 자국 (세로 골짜기, 가로 산) + 잔주름 + 오른쪽 아래 말림."""
    y = -0.055 * sm(x) + 0.04 * sm(z - H / 2)
    y += math.sin(x * 18) * 0.0012 + math.sin(z * 13) * 0.001
    for (a, b, c, amp) in ((0.4, 1.0, -0.12, 0.0006), (-1.0, 0.3, 0.05, 0.0005), (0.8, -0.6, 0.02, 0.0004)):
        d = (a * x + b * z + c) / math.hypot(a, b)
        y += amp * math.exp(-(d / 0.003) ** 2)
    cu = max(0.0, (x - 0.03) / (W / 2 - 0.03)) * max(0.0, 1 - z / 0.07)
    y -= 0.006 * cu * cu
    return y


bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
F, B = {}, {}
for j in range(NZ + 1):
    for i in range(NX + 1):
        x = (i / NX - 0.5) * W
        z = j / NZ * H - (tear[i] if j == NZ else 0.0)
        y = disp(x, z)
        F[i, j] = bm.verts.new((x, y, z))
        B[i, j] = bm.verts.new((x, y + T, z))
front_f, back_f = [], []
for j in range(NZ):
    for i in range(NX):
        f = bm.faces.new((F[i, j], F[i + 1, j], F[i + 1, j + 1], F[i, j + 1]))   # 정면 -Y
        f.material_index = 0
        front_f.append(f)
        b = bm.faces.new((B[i, j + 1], B[i + 1, j + 1], B[i + 1, j], B[i, j]))
        b.material_index = 1
        back_f.append(b)
# 옆면 (종이 두께)
ring = [(i, 0) for i in range(NX)] + [(NX, j) for j in range(NZ)] + [(i, NZ) for i in range(NX, 0, -1)] + \
       [(0, j) for j in range(NZ, 0, -1)]
for k in range(len(ring)):
    a, b = ring[k], ring[(k + 1) % len(ring)]
    f = bm.faces.new((F[b], F[a], B[a], B[b]))
    f.material_index = 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in front_f:
    for l in f.loops:
        co = l.vert.co
        l[uvl].uv = (co.x / W + 0.5, co.z / H)
for f in back_f:
    for l in f.loops:
        co = l.vert.co
        l[uvl].uv = (0.5 - co.x / W, co.z / H)

# 머티리얼: 앞 = 동적 (굽지 않음), 뒤/옆 = 종이 (bake)
dyn = bpy.data.materials.new("M_Dyn_Memo_Paper")
dyn.use_nodes = True
p = k3d.principled(dyn)
p.inputs['Roughness'].default_value = 0.86
k3d.image_node(dyn, k3d.load_image(ik.tex("memo", "memo.png")), p.inputs['Base Color'])
back = ik.P("M_tmp_memo_back", (1, 1, 1), rough=0.88, var=0.04, vs=20, img=ik.tex("memo", "memo_back.png"),
            imode='base', bump=0.06, bs=1500, bd=0.00003)

sheet = ik.mesh_obj(A + "_Sheet", bm)
sheet.data.materials.append(dyn)
sheet.data.materials.append(back)
for poly in sheet.data.polygons:
    poly.use_smooth = True
k3d.bake(sheet, 1024, ao=False, samples=16)

ik.socket(A + "_Socket_Grip", (-0.068, 0, 0.012), sheet)
ik.socket(A + "_Socket_ReadCenter", (0, disp(0, H / 2) - 0.001, H / 2), sheet)

notes = ("메모 한 장 0.165x0.21m (프로토타입 크기), 두께 0.12mm, 원점 = 아랫변 중앙, 정면(-Y)=글씨 면. 위쪽은 수첩에서 찢긴 들쭉날쭉한 변, "
         "4등분 접었다 편 자국(세로 골짜기·가로 산) + 오른쪽 아래 말림. "
         "동적 면: Memo_Sheet 의 앞면 서브메시, 머티리얼 M_Dyn_Memo_Paper, 실제 크기 0.165x0.21m, placeholder 1608x2048 px "
         "(손자가 부탁한 것 / 시장 입구 버거대왕 / 불고기 버거 세트 / 콜라 말고 사이다로 / 포장 / 112번 버스, Nanum Pen Script 볼펜), "
         "UV 0..1 = 시트 전체 (U 오른쪽 +X, V 위 +Z, 정면에서 봤을 때 똑바로). 프로토타입 줄 간격: 640px 기준 62px, 첫 글줄 74px. "
         "뒷면·옆면은 M_Memo_Sheet (1024 bake, 무지 종이·접힌 자국 — 앞 글씨는 동적이라 비친 잉크를 굽지 않음). Socket_Grip = 왼쪽 아래 집는 점(프로토타입 pinchMemo), "
         "Socket_ReadCenter = 시선 목표(종이 중앙).")
k3d.export(A, ik.CAT, [sheet], notes=notes)
k3d.preview(A, [sheet])
k3d.preview(A, [sheet], views=((0, 4),), lens=50, tag='front')

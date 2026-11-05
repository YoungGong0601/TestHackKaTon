# StreetTrashCan: 가로 휴지통 (0.62 x 0.42 x 0.95 m) — 일반쓰레기/재활용 투입구 2개, 둥근 지붕, 아래 수거문(왼쪽 경첩).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d
from mathutils import Vector

k3d.reset()
A = "StreetTrashCan"
W, D, H = 0.62, 0.42, 0.95
png, rect = S.atlas("T_StreetTrashCan_Decals")
body_m = S.paint("M_STC_Paint", (0.055, 0.06, 0.066), 0.45, edge=0.9, edge_col=(0.35, 0.35, 0.34), edge_metal=1.0,
                 rust=0.4, rust_scale=8, rust_z=0.35, streaks=0.9, streak_col=(0.11, 0.075, 0.035), bottom=1.0,
                 bottom_h=0.22, scratches=0.35, grime=0.7, bump=0.0)
roof_m = S.wmat("M_STC_Steel", (0.48, 0.49, 0.5), 0.32, 1.0, var=0.12, grime=0.6, scratches=1.0, streaks=0.5,
                streak_col=(0.2, 0.18, 0.15), bump=0.03, rust=0.2, rust_scale=20)
dark = S.flat("M_StreetTrashCan_Inside", (0.01, 0.01, 0.01), 0.95)
decal = S.decal_mat("M_StreetTrashCan_Decals", png, 0.45)
fy = -D / 2

P = []
P.append(S.box(A + "_Plinth", (W - 0.06, D - 0.06, 0.06), (0, 0, 0.03), mat=roof_m, bevel=0.006))
shell = S.box(A + "_Shell", (W, D, 0.80), (0, 0, 0.06 + 0.40), mat=body_m, bevel=0.03, segs=3)
# 투입구 2개를 불리언으로 뚫는다 (베벨 전에)
holes = []
for k, x in enumerate((-0.15, 0.15)):
    c = S.box(A + "_Cut%d" % k, (0.2, 0.2, 0.12), (x, fy, 0.72), mat=body_m, bevel=0.0)
    c.hide_render = True
    holes.append(c)
for c in holes:
    b = shell.modifiers.new("Hole", 'BOOLEAN')
    b.object, b.operation, b.solver = c, 'DIFFERENCE', 'EXACT'
    shell.modifiers.move(len(shell.modifiers) - 1, 0)
P.append(shell)
for k, x in enumerate((-0.15, 0.15)):
    # 안쪽 어둠 + 투입구 테두리(스테인리스)
    P.append(S.box(A + "_Cavity%d" % k, (0.2, 0.012, 0.12), (x, fy + 0.11, 0.72), mat=dark, bevel=0.0))
    for s in (-1, 1):
        P.append(S.box(A + "_RimV%d%d" % (k, s), (0.012, 0.03, 0.14), (x + s * 0.106, fy - 0.004, 0.72), mat=roof_m, bevel=0.003))
        P.append(S.box(A + "_RimH%d%d" % (k, s), (0.224, 0.03, 0.012), (x, fy - 0.004, 0.72 + s * 0.066), mat=roof_m, bevel=0.003))
    P.append(S.box(A + "_Flap%d" % k, (0.19, 0.006, 0.05), (x, fy + 0.03, 0.765), (math.radians(25), 0, 0), roof_m, 0.002))
# 둥근 지붕 (처마)
P.append(S.box(A + "_Roof", (W + 0.04, D + 0.04, 0.09), (0, 0, 0.905), mat=roof_m, bevel=0.04, segs=4))
P.append(S.box(A + "_RoofBand", (W + 0.012, D + 0.012, 0.025), (0, 0, 0.87), mat=body_m, bevel=0.006))
# 라벨 (투입구 아래) + 옆면 안내 + 문 스티커
P.append(S.quad(A + "_LblGen", 0.24, 0.095, rect["general"], decal, (-0.15, fy - 0.0025, 0.6)))
P.append(S.quad(A + "_LblRec", 0.24, 0.095, rect["recycle"], decal, (0.15, fy - 0.0025, 0.6)))
P.append(S.quad(A + "_Notice", 0.30, 0.186, rect["notice"], decal, (W / 2 + 0.0025, 0.0, 0.62), (0, 0, math.pi / 2)))
# 문틀 + 경첩
dz0, dz1, dw = 0.1, 0.5, 0.5
for zz in (dz0 + 0.07, dz1 - 0.07):
    P.append(S.cyl(A + "_Hinge%.2f" % zz, 0.009, 0.06, (-dw / 2 - 0.004, fy - 0.012, zz - 0.03), mat=roof_m, seg=10, bevel=0.0015))

body = S.join(P, A + "_Body")
for c in holes:
    bpy_obj = c
    import bpy
    bpy.data.objects.remove(bpy_obj, do_unlink=True)
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, keep=("M_StreetTrashCan_Decals", "M_StreetTrashCan_Inside"), samples=24)

# 수거문 (원점 = 왼쪽 세로 경첩, 로컬 Z 축 회전)
D_ = []
D_.append(S.box(A + "_DoorPanel", (dw, 0.014, dz1 - dz0), (0, fy - 0.007, (dz0 + dz1) / 2), mat=body_m, bevel=0.005))
D_.append(S.cyl(A + "_Keyhole", 0.013, 0.008, (dw / 2 - 0.05, fy - 0.014, dz1 - 0.08), (math.pi / 2, 0, 0), roof_m, seg=16, bevel=0.002))
D_.append(S.box(A + "_Pull", (0.12, 0.02, 0.02), (dw / 2 - 0.1, fy - 0.022, dz0 + 0.05), mat=roof_m, bevel=0.004))
D_.append(S.quad(A + "_DoorSticker", 0.12, 0.066, rect["st_key"], decal, (-0.08, fy - 0.0145, 0.36), (0, 0.06, 0)))
door = S.join(D_, A + "_Door")
k3d.set_origin(door, (-dw / 2 - 0.004, fy - 0.012, dz0))
k3d.bake(door, 512, keep=("M_StreetTrashCan_Decals",), samples=24)
S.parent(door, body)
S.empty(A + "_Socket_General", (-0.15, fy - 0.05, 0.72), parent=body)
S.empty(A + "_Socket_Recycle", (0.15, fy - 0.05, 0.72), parent=body)
notes = ("가로 휴지통 0.66 x 0.46 x 0.95 m. 원점 = 바닥 중앙, 정면 -Y. 투입구 2개(왼쪽 일반쓰레기, 오른쪽 재활용)는 실제로 뚫려 있고 "
         "안쪽은 검은 M_StreetTrashCan_Inside. StreetTrashCan_Door = 수거문(원점 = 왼쪽 경첩, 로컬 Z 회전). "
         "Socket_General / Socket_Recycle: 버리는 위치. 프로토타입 길거리 배치 높이 0.95 m.")
S.finish(A, [body], 0.95, notes, fp=dict(dist=1.5, look_h=0.6, az=25))

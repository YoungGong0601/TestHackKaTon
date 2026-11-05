# StreetClothingBin: 의류 수거함 (1.0 x 0.72 x 1.72 m, 녹색 강판) — 위 투입구(앞으로 젖혀지는 호퍼) + 아래 수거문(왼쪽 경첩, 자물쇠).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d
from mathutils import Vector

k3d.reset()
A = "StreetClothingBin"
W, D = 1.0, 0.72
png, rect = S.atlas("T_StreetClothingBin_Decals")
green = S.paint("M_SCB_Paint", (0.045, 0.105, 0.062), 0.55, edge=1.0, edge_col=(0.12, 0.07, 0.04), edge_metal=0.2,
                rust=0.55, rust_scale=6, rust_z=0.5, streaks=0.8, streak_col=(0.09, 0.05, 0.025), bottom=1.0,
                bottom_h=0.3, fade_top=0.25, scratches=0.3, grime=0.7)
steel = S.galv("M_SCB_Steel", 0.5, base=(0.4, 0.4, 0.39), rust=0.7, rust_scale=14)
dark = S.flat("M_StreetClothingBin_Inside", (0.012, 0.012, 0.012), 0.9)
brass = S.wmat("M_SCB_Brass", (0.45, 0.33, 0.12), 0.35, 1.0, var=0.2, grime=0.8, scratches=0.8, bump=0.02)
decal = S.decal_mat("M_StreetClothingBin_Decals", png, 0.5)
fy = -D / 2

P = []
# 다리 4개 + 바닥 틀
for sx in (-1, 1):
    for sy in (-1, 1):
        P.append(S.box(A + "_Foot%d%d" % (sx, sy), (0.07, 0.07, 0.06), (sx * (W / 2 - 0.05), sy * (D / 2 - 0.05), 0.03),
                       mat=steel, bevel=0.004))
P.append(S.box(A + "_Plinth", (W - 0.02, D - 0.02, 0.05), (0, 0, 0.085), mat=green, bevel=0.006))
# 몸통 + 접힌 모서리 기둥 4개
P.append(S.box(A + "_Shell", (W, D, 1.5), (0, 0, 0.11 + 0.75), mat=green, bevel=0.012, segs=3))
for sx in (-1, 1):
    for sy in (-1, 1):
        P.append(S.box(A + "_Corner%d%d" % (sx, sy), (0.035, 0.035, 1.5), (sx * (W / 2 - 0.004), sy * (D / 2 - 0.004), 0.86),
                       mat=green, bevel=0.006))
# 경사 지붕 (앞이 낮음) + 처마
P.append(S.box(A + "_Roof", (W + 0.08, D + 0.1, 0.045), (0, 0.0, 1.655), (math.radians(4), 0, 0), green, 0.012, 3))
P.append(S.box(A + "_RoofLip", (W + 0.08, 0.02, 0.06), (0, -(D / 2 + 0.05), 1.62), mat=green, bevel=0.006))
# 투입구 틀 (호퍼가 들어가는 어두운 개구부)
oz0, oz1, ow = 1.12, 1.44, 0.66
P.append(S.box(A + "_HopFrameT", (ow + 0.08, 0.03, 0.04), (0, fy - 0.012, oz1 + 0.02), mat=green, bevel=0.005))
P.append(S.box(A + "_HopFrameB", (ow + 0.08, 0.03, 0.03), (0, fy - 0.012, oz0 - 0.02), mat=green, bevel=0.005))
for s in (-1, 1):
    P.append(S.box(A + "_HopFrameS%d" % s, (0.04, 0.03, oz1 - oz0 + 0.06), (s * (ow / 2 + 0.02), fy - 0.012, (oz0 + oz1) / 2),
                   mat=green, bevel=0.005))
P.append(S.box(A + "_HopHole", (ow, 0.004, oz1 - oz0), (0, fy - 0.001, (oz0 + oz1) / 2), mat=dark, bevel=0.0))
# 수거문 틀 + 경첩 받침
dz0, dz1, dw = 0.17, 0.98, 0.84
for s in (-1, 1):
    P.append(S.box(A + "_DoorJamb%d" % s, (0.025, 0.02, dz1 - dz0 + 0.04), (s * (dw / 2 + 0.018), fy - 0.008, (dz0 + dz1) / 2),
                   mat=green, bevel=0.004))
for zz in (dz0 + 0.12, dz1 - 0.12):
    P.append(S.cyl(A + "_Hinge%.2f" % zz, 0.012, 0.09, (-dw / 2 - 0.006, fy - 0.022, zz - 0.045), mat=steel, seg=12, bevel=0.002))
# 걸쇠 받이 (자물쇠 고리)
P.append(S.box(A + "_HaspFix", (0.05, 0.012, 0.08), (dw / 2 + 0.03, fy - 0.012, 0.56), mat=steel, bevel=0.003))
P.append(S.lathe(A + "_Staple", [(0.008, -0.004), (0.016, -0.004), (0.016, 0.004), (0.008, 0.004)], seg=12,
                 loc=(dw / 2 + 0.03, fy - 0.03, 0.56), rot=(0, math.pi / 2, 0), mat=steel, close=False))
# 옆면 스티커 (왼쪽 = 수거 품목, 오른쪽 = 무단투기 금지 + 허가), 정면 위 재활용 마크
P.append(S.quad(A + "_SideItems", 0.40, 0.52, rect["items"], decal, (-W / 2 - 0.0025, 0.0, 1.05), (0, 0, -math.pi / 2)))
P.append(S.quad(A + "_SideWarn", 0.46, 0.30, rect["warning"], decal, (W / 2 + 0.0025, 0.0, 1.2), (0, 0, math.pi / 2)))
P.append(S.quad(A + "_SidePermit", 0.20, 0.08, rect["permit"], decal, (W / 2 + 0.0025, 0.12, 0.92), (0, 0, math.pi / 2)))
P.append(S.quad(A + "_SideLoan", 0.18, 0.084, rect["st_loan"], decal, (W / 2 + 0.0025, -0.15, 0.62), (0, 0, math.pi / 2 + 0.05)))
P.append(S.quad(A + "_Recycle", 0.12, 0.12, rect["recycle"], decal, (0.38, fy - 0.0025, 1.52)))

body = S.join(P, A + "_Body")
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 2048, keep=("M_StreetClothingBin_Decals", "M_StreetClothingBin_Inside"), samples=32)

# 호퍼 (투입구 덮개): 아래 모서리 경첩, 앞으로 젖혀 연다 (로컬 X 축 회전, 열림 = -X 회전 약 -50°)
H_ = []
hz0 = oz0 - 0.005
H_.append(S.box(A + "_HopPanel", (ow - 0.01, 0.03, oz1 - oz0 - 0.01), (0, fy - 0.03, (oz0 + oz1) / 2), mat=green, bevel=0.008))
H_.append(S.box(A + "_HopLip", (ow - 0.01, 0.05, 0.02), (0, fy - 0.045, oz1 - 0.015), mat=green, bevel=0.006))
H_.append(S.cyl(A + "_HopHandle", 0.012, 0.36, (-0.18, fy - 0.075, oz1 - 0.05), (0, math.pi / 2, 0), steel, seg=12, bevel=0.002))
for s in (-1, 1):
    H_.append(S.box(A + "_HopHandleLeg%d" % s, (0.02, 0.05, 0.02), (s * 0.17, fy - 0.055, oz1 - 0.05), mat=steel, bevel=0.003))
H_.append(S.quad(A + "_HopSticker", 0.42, 0.137, rect["hopper"], decal, (0, fy - 0.0465, (oz0 + oz1) / 2 - 0.01)))
hop = S.join(H_, A + "_Hopper")
k3d.set_origin(hop, (0, fy - 0.03, hz0))
k3d.bake(hop, 512, keep=("M_StreetClothingBin_Decals",), samples=24)
S.parent(hop, body)

# 수거문: 왼쪽 세로 경첩 (로컬 Z 축 회전), 큰 라벨 + 자물쇠
D_ = []
D_.append(S.box(A + "_DoorPanel", (dw, 0.02, dz1 - dz0), (0, fy - 0.012, (dz0 + dz1) / 2), mat=green, bevel=0.006))
D_.append(S.box(A + "_DoorRib", (dw - 0.1, 0.012, 0.03), (0, fy - 0.025, dz0 + 0.06), mat=green, bevel=0.004))
D_.append(S.quad(A + "_DoorLabel", 0.74, 0.451, rect["main"], decal, (0, fy - 0.0225, 0.64)))
D_.append(S.box(A + "_Hasp", (0.11, 0.008, 0.035), (dw / 2 - 0.03, fy - 0.026, 0.56), mat=steel, bevel=0.002))
D_.append(S.box(A + "_LockBody", (0.042, 0.02, 0.05), (dw / 2 + 0.03, fy - 0.05, 0.525), mat=brass, bevel=0.005))
D_.append(S.lathe(A + "_Shackle", [(0.011, -0.003), (0.016, -0.003), (0.016, 0.003), (0.011, 0.003)], seg=16,
                  loc=(dw / 2 + 0.03, fy - 0.05, 0.555), rot=(math.pi / 2, 0, 0), mat=steel, close=False))
door = S.join(D_, A + "_Door")
k3d.set_origin(door, (-dw / 2 - 0.006, fy - 0.022, dz0))
k3d.bake(door, 1024, keep=("M_StreetClothingBin_Decals",), samples=24)
S.parent(door, body)

S.empty(A + "_Socket_Drop", (0, fy - 0.15, (oz0 + oz1) / 2), parent=body)
S.empty(A + "_Socket_HopperGrip", (0, fy - 0.08, oz1 - 0.05), parent=body)
notes = ("의류 수거함 1.0 x 0.72 x 1.70 m. 원점 = 바닥 중앙, 정면 -Y. 움직이는 부품: StreetClothingBin_Hopper(원점 = 아래 경첩, "
         "로컬 X 축으로 앞으로 젖힘, 열림 약 -50°), StreetClothingBin_Door(원점 = 왼쪽 세로 경첩, 로컬 Z 축 회전, 열림 약 -100°). "
         "호퍼 뒤 개구부는 검은 M_StreetClothingBin_Inside. Socket_Drop(옷을 넣는 위치), Socket_HopperGrip(손잡이). "
         "라벨: 의류 수거함 / 헌옷·신발·가방 / 수거 품목 / 무단투기 금지 / 허가번호 (M_StreetClothingBin_Decals).")
S.finish(A, [body], 1.7, notes, fp=dict(dist=2.2, look_h=1.0, az=25))

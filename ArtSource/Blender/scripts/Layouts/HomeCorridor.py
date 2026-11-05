# 현관문 밖 복도식 아파트 공용 복도 (홈 씬 배경 조각). 문을 열면 이 복도와 난간 너머 단지가 보인다.
# 좌표 = HomeEntry 좌표계 그대로 (Blender = (-x3, z3, y3)). 레이아웃에서 (0,0,0), 회전 없이 둔다.
# 현관 벽 바깥면 y=-2.47, 복도 바닥 = 현관 타일 높이 z=-0.13, 폭 1.5m, x -7.5..7.5. 지면(z=-13.63, 5층 아래)도 포함.
import sys, math
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Home"))
import hk, k3d, bpy, bmesh

k3d.reset()
A, CAT = "HomeCorridor", "LayoutHome"
Y0, CW, PT = -2.47, 1.5, 0.18            # 현관 벽 바깥면, 복도 폭, 난간벽 두께
YP, YPo = Y0 - CW, Y0 - CW - PT          # 난간벽 안쪽/바깥면
FZ, CZ, PZ = -0.13, 2.32, 0.97           # 복도 바닥, 천장 밑면, 난간벽 윗면
X1, XE = 7.5, 1.10                       # 복도 반길이, 현관 옆벽 바깥 x
GZ = FZ - 13.5                           # 지면 (5층)
LY = -3.2                                # 복도 천장등 y
d2r = math.radians

# ---------------------------------------------------------------- 타일 (바닥/벽/천장/지면)
t_floor = k3d.tile("LayoutHome_CorridorFloor", polyhaven_id="concrete_floor_worn_001", tint=(0.74, 0.82, 0.76))
t_wall = k3d.tile("LayoutHome_CorridorWall", polyhaven_id="painted_plaster_wall", res="1k", tint=(0.93, 0.9, 0.82))
t_ground = k3d.tile("LayoutHome_Asphalt", polyhaven_id="asphalt_02", res="1k")
t_wain = k3d.tile("LayoutHome_CorridorWainscot", polyhaven_id="painted_plaster_wall", res="1k", tint=(0.2, 0.3, 0.25))


def sbox(nm, x0, x1, y0, y1, z0, z1, m):
    o = hk.box(A + "_" + nm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), mat=m, bev=0)
    o.modifiers.clear()
    for p in o.data.polygons:
        p.use_smooth = False
    return o


floor = sbox("Floor", -X1, X1, YPo, Y0 + 0.07, FZ - 0.25, FZ, t_floor)          # 현관 벽 밑으로 7cm 들어감 (틈 없음)
walls = hk.join([
    sbox("Parapet", -X1, X1, YPo, YP, FZ - 0.25, PZ, t_wall),                  # 난간벽 (높이 1.1m)
    sbox("FacadeL", XE, X1, Y0, Y0 + 0.12, FZ - 0.25, CZ, t_wall),             # 이웃집 쪽 외벽 (현관 옆벽 바깥)
    sbox("FacadeR", -X1, -XE, Y0, Y0 + 0.12, FZ - 0.25, CZ, t_wall),
    sbox("Ceiling", -X1, X1, YPo, Y0, CZ, CZ + 0.2, t_wall),                   # 윗층 복도 슬래브
    sbox("Beam", -X1, X1, YPo, YPo + 0.24, CZ - 0.32, CZ, t_wall),             # 슬래브 끝 보 (물끊기 턱)
    sbox("EndL", X1, X1 + 0.2, YPo, Y0 + 0.12, FZ - 0.25, CZ + 0.2, t_wall),   # 계단실 벽
    sbox("EndR", -X1 - 0.2, -X1, YPo, Y0 + 0.12, FZ - 0.25, CZ + 0.2, t_wall),
], A + "_Walls")
wain = sbox("Wainscot", -X1, X1, YP, YP + 0.004, FZ, FZ + 0.78, t_wain)                # 난간벽 아래 녹색 칠 (4mm 덧칠 면)
k3d.uv_world(wain, 1.4)
k3d.uv_world(floor, 2.2)
k3d.uv_world(walls, 1.4)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -80, GZ))
ground = bpy.context.active_object
ground.name = A + "_Ground"
ground.scale = (300, 160, 1)
k3d.select([ground])
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ground.data.materials.append(t_ground)
k3d.uv_world(ground, 5.0)

# ---------------------------------------------------------------- 굽는 부품 (난간, 갓돌, 걸레받이, 천장등, 전선관)
paint = hk.P("HC_RailPaint", "#2f4a3b", rough=0.42, var=0.06, edge=0.9, ed=0.006, ecol="#6a4630", erough=0.8,
             grime=0.5, gd=0.03, bump=0.15, bs=220)                                     # 녹색 유성 페인트 + 모서리 녹
capm = hk.P("HC_Cap", "#a8a49a", rough=0.88, var=0.14, grime=0.7, gd=0.05, edge=0.4, ed=0.01, bump=0.35, bs=90,
            dust=0.3, dz=0.04)                                                          # 프리캐스트 갓돌
skirt = hk.P("HC_Skirt", "#565c55", rough=0.72, var=0.12, edge=0.5, ed=0.005, grime=0.4, dust=0.7, dz=0.06)
lampb = hk.P("HC_LampBase", "#e6e2d8", rough=0.38, var=0.03, grime=0.5, gd=0.02, dust=0.4, dz=0.02)
pvc = hk.P("HC_Conduit", "#d8d5cb", rough=0.5, var=0.05, grime=0.4, gd=0.02)

YC = (YP + YPo) / 2
trim = [hk.box(A + "_Cap", (2 * X1, PT + 0.05, 0.05), (0, YC, PZ + 0.025), mat=capm, bev=0.008, seg=2),
        hk.box(A + "_Rail", (2 * X1, 0.05, 0.05), (0, YC, PZ + 0.31), mat=paint, bev=0.005, seg=2),
        hk.box(A + "_RailMid", (2 * X1, 0.02, 0.02), (0, YC, PZ + 0.17), mat=paint, bev=0.003, seg=2),
        hk.box(A + "_SkirtP", (2 * X1, 0.012, 0.10), (0, YP + 0.006, FZ + 0.05), mat=skirt, bev=0.002),
        hk.box(A + "_SkirtFL", (X1 - XE, 0.012, 0.10), ((X1 + XE) / 2, Y0 - 0.006, FZ + 0.05), mat=skirt, bev=0.002),
        hk.box(A + "_SkirtFR", (X1 - XE, 0.012, 0.10), (-(X1 + XE) / 2, Y0 - 0.006, FZ + 0.05), mat=skirt, bev=0.002)]
x = -X1 + 0.35
while x < X1:                                                                           # 난간 기둥 + 앵커 판 (1.2m 간격)
    trim.append(hk.box(A + "_Post", (0.04, 0.04, 0.26), (x, YC, PZ + 0.05 + 0.13), mat=paint, bev=0.004))
    trim.append(hk.box(A + "_Plate", (0.09, 0.09, 0.006), (x, YC, PZ + 0.053), mat=paint, bev=0.002))
    for dx in (-0.03, 0.03):
        trim.append(hk.cyl(A + "_Bolt", 0.006, 0.008, (x + dx, YC + 0.03, PZ + 0.056), mat=paint, n=8, bev=0.001))
    x += 1.2
trim.append(hk.cyl(A + "_LampBase", 0.15, 0.022, (0, LY, CZ), rot=(math.pi, 0, 0), mat=lampb, n=40, bev=0.004, seg=2))
trim.append(hk.cyl(A + "_Conduit", 0.011, Y0 - LY - 0.1, (0, LY + 0.1, CZ - 0.012), rot=(d2r(-90), 0, 0), mat=pvc, n=12, bev=0))
for yy in (LY + 0.35, Y0 - 0.12):                                                       # 전선관 새들
    trim.append(hk.box(A + "_Saddle", (0.05, 0.018, 0.026), (0, yy, CZ - 0.012), mat=pvc, bev=0.002))
trim_o = hk.join(trim, A + "_Trim")
k3d.bake(trim_o, 1024)

# 천장등 유백 커버 (발광, 굽지 않음)
glow_m = k3d.mat("M_HomeCorridor_LampGlow", (0.95, 0.94, 0.9), 0.3, emission=(1.0, 0.97, 0.9), strength=3.0)
glow = hk.cyl(A + "_LampGlow", 0.125, 0.05, (0, LY, CZ - 0.022), rot=(math.pi, 0, 0), mat=glow_m, n=40, r2=0.1,
              bev=0.012, seg=3)
k3d.apply_all(glow)

# ---------------------------------------------------------------- 계층 + 소켓 + 내보내기
for o in (floor, walls, wain, ground, glow):
    hk.parent_keep(o, trim_o)
hk.socket(A + "_Socket_Lamp", (0, LY, CZ - 0.08), trim_o)
hk.socket(A + "_Socket_Exit", (0, Y0 - 0.23, FZ), trim_o)          # 문 열고 걸어 나가는 지점 (프로토타입 walkTo R-.35)
notes = ("현관문 밖 복도식 아파트 공용 복도 (레이아웃 배경 조각). 좌표 = HomeEntry 좌표계 그대로: 레이아웃에서 (0,0,0) 회전 없음. "
         "원점은 바닥 중앙이 아니라 HomeEntry 원점이고, 지면(HomeCorridor_Ground, z=-13.63 = 5층 아래 단지 주차장)까지 "
         "포함하므로 validate 의 min_z 는 의도한 값. 복도 폭 1.5m, 바닥 z=-0.13 (현관 타일과 같은 높이, 문턱 2cm), 천장 2.32, "
         "난간벽 1.1m + 갓돌 + 녹색 페인트 난간(녹 모서리), x -7.5..7.5 양끝은 계단실 벽. "
         "자식: _Floor (M_Tile_LayoutHome_CorridorFloor), _Walls (난간벽/외벽/천장/보/끝벽, M_Tile_LayoutHome_CorridorWall), "
         "_Wainscot (난간벽 아래 0.78m 녹색 칠, M_Tile_LayoutHome_CorridorWainscot, 벽에서 4mm), _Ground (M_Tile_LayoutHome_Asphalt), _LampGlow (천장등 커버 발광 M_HomeCorridor_LampGlow, 루트는 1024 굽기). "
         "소켓: Lamp (복도 천장등 Point Light 위치), Exit (문 열고 걸어 나가는 지점).")
k3d.export(A, CAT, [trim_o], notes=notes)
ground.hide_render = True                                         # 미리보기는 복도만 (지면 300m 는 화면 밖)
k3d.preview(A, [floor, walls], views=((20, 15), (160, 35)), ground=False)

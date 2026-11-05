"""StoreKitchen: 카운터 뒤 주방 설비 (튀김기 2대·그리들·작업대·벽선반 포장재·제빙기·후드·음료 디스펜서 아일랜드·STAFF ONLY 문).
원점 = 매장 원점 (프로토타입 (0,0,0) 바닥, StoreShell 과 같은 자리). 블렌더 매장좌표 = (x, -z, y).
조리 라인은 왼쪽 벽(x=-6)을 따라 뒤→앞: 튀김기, 그리들, 작업대, 제빙기 (프로토타입의 겹침을 풀어 배치). 설비 정면 = +X (카운터 쪽)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
k3d = S.k3d
bpy = S.bpy
k3d.reset()
S.textures()
B, C = S.boxz, S.cyl
WX, YB, H = -6.0, 4.2, 3.1

# ---- 머티리얼 (굽기용)
m_ss = S.pbr("M_tmp_KSteel", (0.62, 0.62, 0.6), 0.3, 1.0, var=0.05, grime=0.55, gdist=0.04, brush=0.18, smudge=0.35,
             scratch=0.4, bump=0.015)
m_ssd = S.pbr("M_tmp_KSteelGreasy", (0.45, 0.43, 0.4), 0.36, 1.0, var=0.1, grime=0.8, grime_col=(0.07, 0.045, 0.02),
              gdist=0.06, brush=0.15, streak=0.45, smudge=0.4, scratch=0.3, bump=0.015)
m_plate = S.pbr("M_tmp_KGriddle", (0.03, 0.027, 0.024), 0.32, 0.85, var=0.35, vscale=12, grime=0.6,
                grime_col=(0.05, 0.03, 0.01), scratch=0.6, bump=0.04)
m_oil = S.pbr("M_tmp_KOil", (0.33, 0.17, 0.03), 0.04, var=0.15, grime=0.0, bump=0.01, bscale=40)
m_wire = S.pbr("M_tmp_KWire", (0.6, 0.6, 0.58), 0.28, 1.0, grime=0.6, grime_col=(0.1, 0.06, 0.02), bump=0)
m_blk = S.pbr("M_tmp_KBlack", (0.022, 0.022, 0.024), 0.45, var=0.1, grime=0.4, smudge=0.4, edge=0.3,
              edge_col=(0.1, 0.1, 0.1), bump=0.03, bscale=200)
m_hdpe = S.pbr("M_tmp_KBoard", (0.76, 0.75, 0.71), 0.6, var=0.08, grime=0.4, scratch=0.9, bump=0.06, bscale=150)
m_red = S.pbr("M_tmp_KBottleRed", (0.5, 0.03, 0.02), 0.25, grime=0.4, smudge=0.4, bump=0)
m_yel = S.pbr("M_tmp_KBottleYellow", (0.72, 0.46, 0.02), 0.25, grime=0.4, smudge=0.4, bump=0)
m_card = S.pbr("M_tmp_KCardboard", (0.45, 0.32, 0.2), 0.8, var=0.15, grime=0.4, edge=0.3, edge_col=(0.55, 0.42, 0.28), bump=0.1)
m_rub = S.pbr("M_tmp_KRubberMat", (0.018, 0.018, 0.018), 0.75, var=0.1, grime=0.5, grime_col=(0.06, 0.04, 0.02),
              bump=0.6, bscale=60)
m_cup = S.pbr("M_tmp_KCup", (0.82, 0.8, 0.76), 0.5, var=0.05, grime=0.2)
m_lid = S.pbr("M_tmp_KLid", (0.86, 0.86, 0.85), 0.3, grime=0.2, bump=0)
m_filt = S.pbr("M_tmp_KFilter", (0.4, 0.39, 0.37), 0.35, 1.0, var=0.15, grime=0.9, grime_col=(0.09, 0.05, 0.015),
               gdist=0.03, streak=0.5, bump=0.02)
m_door = S.pbr("M_tmp_KDoorPaint", (0.46, 0.47, 0.46), 0.45, var=0.06, grime=0.5, edge=0.6, edge_col=(0.7, 0.7, 0.68),
               scratch=0.5, smudge=0.5, streak=0.15, bump=0.02)
m_food = [S.pbr("M_tmp_KLettuce", (0.12, 0.36, 0.05), 0.5, var=0.3, vscale=60, bump=0.4, bscale=80, grime=0.2),
          S.pbr("M_tmp_KTomato", (0.5, 0.05, 0.03), 0.3, var=0.25, vscale=50, bump=0.3, bscale=60, grime=0.2),
          S.pbr("M_tmp_KOnion", (0.75, 0.72, 0.64), 0.4, var=0.2, vscale=70, bump=0.3, bscale=90, grime=0.2),
          S.pbr("M_tmp_KPickle", (0.2, 0.3, 0.06), 0.35, var=0.25, vscale=60, bump=0.3, bscale=70, grime=0.2)]
m_lamp = S.pbr("M_tmp_KLampLens", (0.9, 0.9, 0.86), 0.3, grime=0.3, bump=0, emission=(1.0, 0.95, 0.85), estr=2.5)

A = "kitchen_signs.png"
m_sign = S.img_mat("M_StoreKitchen_Signs", S.tex(A), rough=0.45)
m_scr = S.img_mat("M_StoreKitchen_Screens", S.tex(A), rough=0.2, emit=1.3)
m_port = k3d.mat("M_Glass_StoreKitchen_Porthole", (0.85, 0.9, 0.92), 0.05, alpha=0.18)
RX = (math.pi / 2, 0, math.pi / 2)    # +X 를 보는 판
labels, screens = [], []


def lab(key, w, h, loc, rot=RX, scr=False):
    q = S.quad("lb", w, h, loc, m_scr if scr else m_sign, rot=rot, uv=S.atlas_uv(A, key))
    (screens if scr else labels).append(q)
    return q


line = []

# ---------------------------------------------------------------- 튀김기 2대 (정면 +X, 앞면 x=-5.37)
FX0, FX1 = -5.99, -5.37


def basket(loc, tilt):
    """튀김 바구니 (철망 막대) + 손잡이. loc = 바구니 중심."""
    p = []
    bx, by, bz = 0.36, 0.19, 0.14
    for y in (-by / 2, by / 2):           # 위 테두리
        p.append(B("r", -bx / 2, bx / 2, y - 0.003, y + 0.003, bz / 2 - 0.006, bz / 2, m_wire, 0))
    for x in (-bx / 2, bx / 2):
        p.append(B("r", x - 0.003, x + 0.003, -by / 2, by / 2, bz / 2 - 0.006, bz / 2, m_wire, 0))
    p.append(B("bt", -bx / 2, bx / 2, -by / 2, by / 2, -bz / 2, -bz / 2 + 0.003, m_wire, 0))
    for i in range(10):                    # 세로 철사
        x = -bx / 2 + (i + 0.5) * bx / 10
        for y in (-by / 2, by / 2):
            p.append(B("v", x - 0.0015, x + 0.0015, y - 0.0015, y + 0.0015, -bz / 2, bz / 2, m_wire, 0))
    for i in range(5):
        y = -by / 2 + (i + 0.5) * by / 5
        for x in (-bx / 2, bx / 2):
            p.append(B("v", x - 0.0015, x + 0.0015, y - 0.0015, y + 0.0015, -bz / 2, bz / 2, m_wire, 0))
    hd = C("hd", 0.006, 0.22, (bx / 2 + 0.1, 0, bz / 2 + 0.03), m_wire, 8, 0, rot=(0, math.radians(90 - 15), 0))
    p.append(hd)
    gr = C("gr", 0.014, 0.12, (bx / 2 + 0.25, 0, bz / 2 + 0.07), m_blk, 12, 0.003, rot=(0, math.radians(90 - 15), 0))
    p.append(gr)
    o = S.join(p, "basket")
    S.set_origin(o, (0, 0, 0))
    o.location = loc
    o.rotation_euler = (0, tilt, 0)
    return o


for i, yc in enumerate((3.2, 2.55)):
    y0, y1 = yc - 0.3, yc + 0.3
    line.append(B("f_cab", FX0, FX1 - 0.01, y0, y1, 0.12, 0.6, m_ssd, 0.004))
    for a in ((FX1 - 0.09, FX1 - 0.01, y0, y1), (FX0, FX0 + 0.13, y0, y1), (FX0 + 0.13, FX1 - 0.09, y0, y0 + 0.07),
              (FX0 + 0.13, FX1 - 0.09, y1 - 0.07, y1)):   # 기름통 벽 (안쪽 면 = 통 내벽)
        line.append(B("f_wall", a[0], a[1], a[2], a[3], 0.6, 0.86, m_ssd, 0.002, 1))
    line.append(B("f_door", FX1 - 0.01, FX1, y0 + 0.03, y1 - 0.03, 0.15, 0.6, m_ss, 0.004, 2))
    line.append(B("f_hdl", FX1, FX1 + 0.022, yc - 0.2, yc + 0.2, 0.545, 0.565, m_ss, 0.006, 2))
    line.append(B("f_ctl", FX1 - 0.01, FX1 + 0.004, y0 + 0.02, y1 - 0.02, 0.63, 0.84, m_ss, 0.004, 2))
    line.append(B("f_disp", FX1 + 0.004, FX1 + 0.012, yc - 0.075, yc + 0.075, 0.705, 0.775, m_blk, 0.003, 1))
    for k in range(4):
        by = yc - 0.16 + k * 0.107
        line.append(B("f_btn", FX1 + 0.004, FX1 + 0.012, by - 0.02, by + 0.02, 0.66, 0.685, m_blk, 0.003, 2))
    for sx in (FX0 + 0.06, FX1 - 0.07):
        for sy in (y0 + 0.06, y1 - 0.06):
            line.append(C("f_leg", 0.022, 0.11, (sx, sy, 0.065), m_ss, 12, 0.003))
            line.append(C("f_foot", 0.03, 0.012, (sx, sy, 0.006), m_blk, 12, 0.003))
    # 상판 (가운데 기름통 구멍) + 기름 + 안쪽 벽
    line.append(B("f_top", FX1 - 0.09, FX1 + 0.01, y0, y1, 0.86, 0.9, m_ss, 0.004, 2))
    line.append(B("f_top", FX0, FX0 + 0.13, y0, y1, 0.86, 0.9, m_ssd, 0.004, 2))
    line.append(B("f_top", FX0 + 0.13, FX1 - 0.09, y0, y0 + 0.07, 0.86, 0.9, m_ss, 0.004, 2))
    line.append(B("f_top", FX0 + 0.13, FX1 - 0.09, y1 - 0.07, y1, 0.86, 0.9, m_ss, 0.004, 2))
    line.append(B("f_vat", FX0 + 0.13, FX1 - 0.09, y0 + 0.07, y1 - 0.07, 0.6, 0.62, m_ssd, 0))
    line.append(B("f_oil", FX0 + 0.13, FX1 - 0.09, y0 + 0.07, y1 - 0.07, 0.62, 0.81, m_oil, 0))
    # 뒤 연도(굴뚝) + 바구니 걸이
    line.append(B("f_flue", FX0, FX0 + 0.13, y0 + 0.02, y1 - 0.02, 0.9, 1.1, m_ssd, 0.006, 2))
    line.append(B("f_flueg", FX0 + 0.04, FX0 + 0.11, y0 + 0.08, y1 - 0.08, 1.1, 1.104, m_blk, 0.001, 1))
    line.append(C("f_hang", 0.006, 0.58, (FX0 + 0.145, yc, 1.06), m_ss, 10, 0, rot=(math.pi / 2, 0, 0)))
    for s in (-0.11, 0.11):
        line.append(basket((FX0 + 0.33, yc + s, 0.98), math.radians(-12)))
    lab("timer%d" % i, 0.1, 0.044, (FX1 + 0.0125, yc, 0.74), scr=True)
    lab("hot", 0.16, 0.089, (FX1 + 0.0005, yc, 0.42))
line.append(B("f_fill", FX0 + 0.02, FX1 - 0.02, 2.85, 2.9, 0.86, 0.905, m_ss, 0.002, 1))   # 튀김기 사이 덮개

# ---------------------------------------------------------------- 그리들 (스탠드 위, y 1.3~2.2)
GY0, GY1 = 1.3, 2.2
line.append(B("g_stand", -5.99, -5.29, GY0, GY1, 0.58, 0.6, m_ss, 0.003, 2))
line.append(B("g_shelf", -5.97, -5.31, GY0 + 0.02, GY1 - 0.02, 0.2, 0.22, m_ss, 0.003, 2))
for sx in (-5.96, -5.32):
    for sy in (GY0 + 0.03, GY1 - 0.03):
        line.append(C("g_leg", 0.018, 0.58, (sx, sy, 0.29), m_ss, 12, 0.003))
line.append(B("g_body", -5.97, -5.33, GY0 + 0.01, GY1 - 0.01, 0.6, 0.84, m_ssd, 0.005, 2))
line.append(B("g_plate", -5.97, -5.36, GY0 + 0.01, GY1 - 0.01, 0.84, 0.865, m_plate, 0.003, 2))
line.append(B("g_back", -5.99, -5.95, GY0, GY1, 0.865, 0.99, m_ssd, 0.003, 2))
for y in (GY0, GY1 - 0.02):
    line.append(B("g_side", -5.99, -5.45, y, y + 0.02, 0.865, 0.95, m_ssd, 0.003, 2))
line.append(B("g_trough", -5.36, -5.31, GY0 + 0.03, GY1 - 0.03, 0.8, 0.865, m_ss, 0.004, 2))
for k in range(3):
    ky = GY0 + 0.2 + k * 0.25
    line.append(C("g_knob", 0.02, 0.025, (-5.32, ky, 0.7), m_blk, 16, 0.004, rot=(0, math.pi / 2, 0)))
line.append(B("g_scraper", -5.7, -5.5, 1.5, 1.6, 0.865, 0.875, m_ss, 0.002, 1))
line.append(B("g_scr_h", -5.5, -5.38, 1.535, 1.565, 0.865, 0.89, m_blk, 0.006, 2))

# ---------------------------------------------------------------- 작업대 (y -0.65~1.28) + 재료 받침 + 소스통 + 도마
TY0, TY1, TX1 = -0.65, 1.28, -5.24
line.append(B("t_top", WX + 0.01, TX1, TY0, TY1, 0.88, 0.92, m_ss, 0.006, 3))
line.append(B("t_splash", WX + 0.01, WX + 0.03, TY0, TY1, 0.92, 1.03, m_ss, 0.003, 2))
line.append(B("t_shelf", WX + 0.05, TX1 - 0.04, TY0 + 0.04, TY1 - 0.04, 0.24, 0.26, m_ss, 0.003, 2))
for sx in (WX + 0.06, TX1 - 0.05):
    for sy in (TY0 + 0.05, TY1 - 0.05):
        line.append(C("t_leg", 0.019, 0.86, (sx, sy, 0.45), m_ss, 12, 0.003))
        line.append(C("t_foot", 0.024, 0.03, (sx, sy, 0.015), m_ss, 12, 0.004, r2=0.016))
# 재료 받침 (1/6 팬 4개)
line.append(B("t_rail", WX + 0.05, WX + 0.25, 0.25, 1.15, 0.92, 1.0, m_ss, 0.003, 2))
for k in range(4):
    py = 0.3 + k * 0.215
    line.append(B("t_pan", WX + 0.07, WX + 0.23, py, py + 0.19, 0.96, 1.004, m_ss, 0.002, 1))
    line.append(B("t_fill", WX + 0.075, WX + 0.225, py + 0.005, py + 0.185, 0.96, 0.998, m_food[k], 0.004, 2))
line.append(B("t_board", -5.7, -5.3, -0.3, 0.2, 0.92, 0.94, m_hdpe, 0.004, 2))
for k in range(5):
    by = -0.55 + k * 0.08
    mt = m_red if k % 2 == 0 else m_yel
    line.append(C("t_btl", 0.03, 0.17, (-5.4, by, 1.005), mt, 16, 0.006, 2))
    line.append(C("t_cap", 0.012, 0.045, (-5.4, by, 1.112), mt, 10, 0.003, r2=0.003))
# 선반 아래 상자
for k, (y0, w, h) in enumerate(((-0.55, 0.45, 0.3), (0.0, 0.5, 0.25), (0.6, 0.55, 0.32))):
    line.append(B("t_box", -5.95, -5.45, y0, y0 + w, 0.26, 0.26 + h, m_card, 0.008, 2))
    lab("box%d" % (k % 4), 0.2, 0.137, (-5.4495, y0 + w / 2, 0.26 + h / 2))

# ---------------------------------------------------------------- 벽 선반 2단 + 포장재 상자
for z, y1, brk in ((1.75, 1.25, (-0.55, 0.85, 1.15)), (2.08, 1.0, (-0.55, 0.2, 0.9))):
    line.append(B("s_board", WX, WX + 0.34, TY0, y1, z - 0.03, z, m_ss, 0.003, 2))
    line.append(B("s_lip", WX + 0.33, WX + 0.345, TY0, y1, z - 0.03, z + 0.02, m_ss, 0.002, 1))
    for by in brk:
        line.append(B("s_brk", WX, WX + 0.3, by - 0.01, by + 0.01, z - 0.2, z - 0.03, m_ss, 0.002, 1))
boxes = [(-0.6, 0.28, 0.22, 0), (-0.28, 0.28, 0.27, 1), (0.04, 0.26, 0.2, 2), (0.34, 0.3, 0.25, 3), (0.68, 0.28, 0.22, 0),
         (1.0, 0.22, 0.18, 2)]
for y0, w, h, k in boxes:
    line.append(B("s_box", WX + 0.03, WX + 0.31, y0, y0 + w, 1.75, 1.75 + h, m_card, 0.008, 2))
    lab("box%d" % k, min(0.2, w - 0.04), min(0.137, h - 0.04) if h < 0.2 else 0.137, (WX + 0.3105, y0 + w / 2, 1.75 + h / 2))
for y0, w, h in ((-0.6, 0.5, 0.18), (0.0, 0.4, 0.16), (0.5, 0.4, 0.2)):   # 위 칸: 컵 뚜껑 묶음·냅킨 상자
    line.append(B("s_box", WX + 0.04, WX + 0.3, y0, y0 + w, 2.08, 2.08 + h, m_card, 0.008, 2))

# ---------------------------------------------------------------- KDS 모니터 (벽걸이 암)
line.append(B("k_plate", WX, WX + 0.01, 0.33, 0.47, 1.36, 1.48, m_blk, 0.002, 1))
line.append(B("k_arm", WX + 0.01, WX + 0.09, 0.38, 0.42, 1.4, 1.44, m_blk, 0.004, 2))
line.append(B("k_mon", WX + 0.09, WX + 0.12, 0.165, 0.635, 1.27, 1.57, m_blk, 0.006, 2))
lab("kds", 0.44, 0.272, (WX + 0.121, 0.4, 1.42), scr=True)

# ---------------------------------------------------------------- 제빙기 (y -1.6~-0.7): 저장통 + 제빙 헤드
IY0, IY1, IX1 = -1.6, -0.7, -5.3
for sx in (WX + 0.06, IX1 - 0.06):
    for sy in (IY0 + 0.06, IY1 - 0.06):
        line.append(C("i_leg", 0.022, 0.15, (sx, sy, 0.075), m_ss, 12, 0.003))
line.append(B("i_bin", WX + 0.01, IX1, IY0, IY1, 0.15, 1.05, m_ss, 0.006, 2))
line.append(B("i_bdoor", IX1, IX1 + 0.012, IY0 + 0.05, IY1 - 0.05, 0.72, 0.98, m_ss, 0.006, 2))
line.append(B("i_bhdl", IX1 + 0.012, IX1 + 0.03, IY0 + 0.3, IY1 - 0.3, 0.955, 0.975, m_blk, 0.006, 2))
line.append(B("i_seam", IX1, IX1 + 0.003, IY0, IY1, 1.045, 1.06, m_blk, 0.001, 1))
line.append(B("i_head", WX + 0.01, IX1, IY0 + 0.04, IY1 - 0.04, 1.06, 1.82, m_ss, 0.006, 2))
line.append(B("i_grill", IX1, IX1 + 0.006, IY0 + 0.1, IY1 - 0.1, 1.12, 1.5, m_blk, 0.002, 1))
for k in range(12):
    z = 1.135 + k * 0.03
    line.append(B("i_louv", IX1 + 0.006, IX1 + 0.012, IY0 + 0.1, IY1 - 0.1, z, z + 0.012, m_ss, 0.002, 1))
line.append(B("i_vhdl", IX1 + 0.006, IX1 + 0.03, IY1 - 0.1, IY1 - 0.08, 1.55, 1.75, m_blk, 0.006, 2))
lab("ice", 0.24, 0.08, (IX1 + 0.0005, (IY0 + IY1) / 2, 1.62))

# ---------------------------------------------------------------- 후드 (y 1.1~3.7, 바닥 2.24) + 배기 덕트
HX1, HY0, HY1, HZ0, HZ1 = -4.935, 1.1, 3.7, 2.24, 2.66
line.append(B("h_top", WX, HX1, HY0, HY1, HZ1 - 0.02, HZ1, m_ss, 0.004, 2))
line.append(B("h_front", HX1 - 0.02, HX1, HY0, HY1, HZ0, HZ1, m_ss, 0.006, 2))
for y in (HY0, HY1 - 0.02):
    line.append(B("h_side", WX, HX1, y, y + 0.02, HZ0, HZ1, m_ss, 0.004, 2))
line.append(B("h_gut", HX1 - 0.12, HX1 - 0.02, HY0 + 0.02, HY1 - 0.02, HZ0, HZ0 + 0.03, m_ssd, 0.003, 1))
for k in range(5):   # 배플 필터 (기울어짐)
    fy = HY0 + 0.06 + k * 0.5
    f = S.box("h_filt", (0.04, 0.48, 0.38), (WX + 0.16, fy + 0.24, HZ0 + 0.21), m_filt, 0.003, 1, rot=(0, math.radians(-30), 0))
    line.append(f)
    for j in range(7):
        r = S.box("h_baf", (0.012, 0.018, 0.36), (WX + 0.136, fy + 0.04 + j * 0.065, HZ0 + 0.21), m_filt, 0.002, 1,
                  rot=(0, math.radians(-30), 0))
        line.append(r)
line.append(B("h_back", WX, WX + 0.01, HY0, HY1, HZ0, HZ1, m_ssd, 0.002, 1))
for y in (1.6, 3.2):   # 방습 조명
    line.append(B("h_lamp", HX1 - 0.32, HX1 - 0.1, y - 0.2, y + 0.2, HZ1 - 0.05, HZ1 - 0.02, m_ss, 0.004, 2))
    line.append(B("h_lens", HX1 - 0.31, HX1 - 0.11, y - 0.19, y + 0.19, HZ1 - 0.065, HZ1 - 0.05, m_lamp, 0.006, 2))
line.append(B("h_duct", WX + 0.05, WX + 0.55, 2.15, 2.65, HZ1, H, m_ss, 0.006, 2))
for y in (HY0 + 0.3, HY1 - 0.3):   # 천장 행거
    line.append(C("h_rod", 0.006, H - HZ1, (HX1 - 0.15, y, (H + HZ1) / 2), m_ss, 8, 0))
lab("hood", 0.45, 0.108, (HX1 + 0.0005, 2.4, HZ0 + 0.24))

# ---------------------------------------------------------------- 바닥: 미끄럼방지 고무매트 + 트렌치 배수구
line.append(B("mat", -5.3, -4.5, 1.35, 3.5, 0.0, 0.012, m_rub, 0.004, 2))
line.append(B("drain_f", -5.0, -4.4, -0.32, -0.16, 0.0, 0.004, m_ss, 0.001, 1))
for k in range(9):
    x = -4.98 + k * 0.0675
    line.append(B("drain_b", x, x + 0.04, -0.3, -0.18, 0.001, 0.0045, m_ssd, 0.0008, 1))

# ---------------------------------------------------------------- STAFF ONLY 문 (뒷벽, x -4.95~-4.05) 문틀
SX0, SX1 = -4.95, -4.05
for a, b in ((SX0 - 0.05, SX0), (SX1, SX1 + 0.05)):
    line.append(B("d_jamb", a, b, YB - 0.08, YB - 0.01, 0, 2.15, m_ss, 0.004, 2))
line.append(B("d_head", SX0 - 0.05, SX1 + 0.05, YB - 0.08, YB - 0.01, 2.1, 2.15, m_ss, 0.004, 2))
lab("log", 0.21, 0.3, (-3.78, YB - 0.0085, 1.45), rot=(math.pi / 2, 0, 0))
line.append(B("d_clip", -3.81, -3.75, YB - 0.014, YB - 0.008, 1.585, 1.615, m_blk, 0.003, 1))
line.append(B("d_board", -3.895, -3.665, YB - 0.008, YB, 1.29, 1.615, m_card, 0.003, 1))

kline = S.join(line, "StoreKitchen_Line")
S.set_origin(kline, (0, 0, 0))

# ---------------------------------------------------------------- 아일랜드 (음료 디스펜서·컵)
# 프로토 범위(z -0.95~0.55)만 쓴다. 그 앞(블렌더 y < -0.55)은 조리 직원이 픽업으로 걸어가는 통로라 비운다
isl = []
AX0, AX1, AY0, AY1 = -4.01, -3.39, -0.55, 0.95
isl.append(B("a_cab", AX0, AX1 - 0.01, AY0 + 0.02, AY1 - 0.02, 0.1, 0.9, m_ssd, 0.004))
isl.append(B("a_kick", AX0 + 0.03, AX1 - 0.04, AY0 + 0.04, AY1 - 0.04, 0.0, 0.1, m_blk, 0.002))
for k in range(2):
    y0 = AY0 + 0.04 + k * 0.7
    isl.append(B("a_door", AX1 - 0.01, AX1, y0, y0 + 0.68, 0.13, 0.86, m_ss, 0.004, 2))
    isl.append(B("a_hdl", AX1, AX1 + 0.02, y0 + (0.6 if k == 0 else 0.04), y0 + (0.64 if k == 0 else 0.08), 0.55, 0.8, m_ss, 0.006, 2))
isl.append(B("a_top", AX0 - 0.02, AX1 + 0.02, AY0, AY1, 0.9, 0.93, m_ss, 0.004, 3))
# 음료 디스펜서 (정면 +X, 카운터 너머로 맛 표시판이 보임)
DY, DW = 0.45, 0.88
d0, d1 = DY - DW / 2, DY + DW / 2
isl.append(B("v_body", -3.97, -3.53, d0, d1, 1.25, 1.76, m_ss, 0.008, 3))
isl.append(B("v_back", -3.97, -3.78, d0, d1, 0.93, 1.25, m_ss, 0.006, 2))
isl.append(B("v_lid", -3.96, -3.54, d0 + 0.01, d1 - 0.01, 1.76, 1.79, m_ss, 0.008, 3))
isl.append(B("v_panelf", -3.53, -3.515, d0 + 0.01, d1 - 0.01, 1.3, 1.66, m_blk, 0.004, 2))
isl.append(B("v_tray", -3.75, -3.5, d0 + 0.02, d1 - 0.02, 0.93, 0.965, m_ss, 0.003, 2))
for k in range(16):
    y = d0 + 0.05 + k * 0.05
    isl.append(B("v_grate", -3.74, -3.51, y, y + 0.025, 0.965, 0.972, m_ssd, 0.001, 1))
isl.append(B("v_manif", -3.78, -3.56, d0 + 0.03, d1 - 0.03, 1.17, 1.25, m_blk, 0.006, 2))
for k in range(4):
    y = d0 + 0.11 + k * 0.22
    isl.append(C("v_noz", 0.017, 0.07, (-3.62, y, 1.135), m_blk, 12, 0.004, r2=0.012))
    isl.append(B("v_lever", -3.57, -3.555, y - 0.03, y + 0.03, 1.07, 1.16, m_blk, 0.004, 2))
lab("drinks", 0.84, 0.3125, (-3.5145, DY, 1.48), scr=True)
# 컵 쌓음 3줄 + 뚜껑
for k, y in enumerate((-0.15, -0.29, -0.43)):
    isl.append(C("c_cup", 0.045, 0.36, (-3.7, y, 0.93 + 0.18), m_cup, 20, 0.004, r2=0.038))
    isl.append(C("c_rim", 0.047, 0.006, (-3.7, y, 0.93 + 0.363), m_cup, 20, 0.002))
isl.append(C("c_lids", 0.05, 0.08, (-3.88, -0.3, 0.97), m_lid, 20, 0.004))
island = S.join(isl, "StoreKitchen_Island")
S.set_origin(island, (0, 0, 0))

# ---------------------------------------------------------------- STAFF ONLY 문짝 (원점 = 경첩 축 바닥, 왼쪽 경첩)
dp = [B("leaf", 0, SX1 - SX0, -0.045, 0, 0, 2.098, m_door, 0.004, 2)]
DW2 = SX1 - SX0
dp.append(B("kick", 0.01, DW2 - 0.01, -0.0465, -0.045, 0.01, 0.3, m_ss, 0.001, 1))
dp.append(B("push", DW2 - 0.16, DW2 - 0.06, -0.0465, -0.045, 0.95, 1.35, m_ss, 0.002, 1))
bpy.ops.mesh.primitive_torus_add(major_radius=0.162, minor_radius=0.012, major_segments=40, minor_segments=10,
                                 location=(DW2 / 2, -0.047, 1.5), rotation=(math.pi / 2, 0, 0))
ring = bpy.context.active_object
ring.data.materials.append(m_ss)
dp.append(ring)
dp.append(C("port_d", 0.152, 0.002, (DW2 / 2, -0.046, 1.5), m_blk, 40, 0, rot=(math.pi / 2, 0, 0)))   # 창 너머 어두운 복도
dp.append(B("closer", 0.05, 0.33, -0.1, -0.045, 1.98, 2.035, m_ss, 0.008, 2))
dp.append(B("arm", 0.28, 0.5, -0.088, -0.072, 2.04, 2.052, m_ss, 0.003, 1))
for z in (0.25, 1.05, 1.85):
    dp.append(C("hinge", 0.008, 0.1, (-0.002, -0.022, z), m_ss, 12, 0.002))
door = S.join(dp, "StoreKitchen_StaffDoor")
S.set_origin(door, (0, 0, 0))

k3d.bake(kline, 2048, samples=32, ao_distance=0.08)
k3d.bake(island, 2048, samples=32, ao_distance=0.06)
k3d.bake(door, 1024, samples=32, ao_distance=0.05)

port = C("StoreKitchen_StaffDoor_Window", 0.15, 0.004, (DW2 / 2, -0.051, 1.5), m_port, 40, 0, rot=(math.pi / 2, 0, 0))
port = S.join([port], "StoreKitchen_StaffDoor_Window")
dsign = S.quad("StoreKitchen_StaffDoor_Sign", 0.4, 0.15, (DW2 / 2, -0.0475, 1.8), m_sign, uv=S.atlas_uv(A, "staff"))
# 손자 오브젝트는 FBX bake_space_transform 에서 이중 회전되므로 창·표지를 문 메시에 합친다
door = S.join([door, port, dsign], "StoreKitchen_StaffDoor")
door.location = (SX0, YB - 0.005, 0)

lb = S.join(labels, "StoreKitchen_Labels")
S.set_origin(lb, (0, 0, 0))
sc = S.join(screens, "StoreKitchen_Screens")
S.set_origin(sc, (0, 0, 0))

root = kline
for o in (island, door, lb, sc):
    S.reparent(o, root)
socks = {"FryerBeep_A": (FX1 + 0.01, 3.2, 0.74), "FryerBeep_B": (FX1 + 0.01, 2.55, 0.74), "CookHandoff": (-3.5, -0.85, 0),
         "DrinkLook": (-3.51, DY, 1.48), "StaffDoor": ((SX0 + SX1) / 2, YB - 0.3, 0)}
for k, p in socks.items():
    S.empty("StoreKitchen_Socket_" + k, p, root)

notes = {
    "pivot": "원점 = 매장 원점(프로토타입 (0,0,0) 바닥). StoreShell 과 같이 Unity (0,0,0) 회전 0. 블렌더 (x,y,z) -> Unity (-x, z, -y).",
    "layout": "왼쪽 벽(Unity x=+6) 조리 라인 뒤→앞: 튀김기 2대(프로토 z -3.2/-2.55, 바구니 걸이에 바구니 4개), 그리들(z -2.2~-1.3), 작업대(z -1.28~0.65, 재료 팬·소스통·도마·아래 상자), 제빙기(z 0.7~1.6). 후드는 튀김기·그리들 위(바닥 2.24, 배플 필터·방습등·천장 덕트). 벽 선반 2단(1.75/2.08)에 포장재 상자, KDS 모니터(1.42).",
    "island": "StoreKitchen_Island: 카운터 바로 뒤 아일랜드(프로토 x -4.01~-3.39, z -0.95~0.55) + 음료 디스펜서(정면 +X = 카운터 쪽, 맛 표시판이 카운터 너머로 보임) + 컵. 그 앞(프로토 z 0.55 이후)은 조리 직원 통로라 비움. 픽업 열등은 StoreCounter_PickupLamp 몫.",
    "door": "StoreKitchen_StaffDoor: 뒷벽 STAFF ONLY 문(프로토 x -4.95~-4.05), 원점 = 왼쪽 경첩 축 바닥, 회전하면 방 안쪽(Unity +Z)으로 열림. 둥근 창(M_Glass_StoreKitchen_Porthole)·표지 '관계자 외 출입금지'(M_StoreKitchen_Signs)는 문 메시에 포함. 뒤는 벽으로 막혀 있음(장식).",
    "screens": "StoreKitchen_Screens(M_StoreKitchen_Screens 발광 1.3, 정적): 튀김기 타이머 2:41/0:58, KDS 주문 현황, 음료 맛 표시판. StoreKitchen_Labels: 고온 주의·ICE MAKER·후드 세척·청소 점검표·상자 인쇄.",
    "sockets": "FryerBeep_A/B(fryer_beep 소리 위치), CookHandoff(조리 직원이 픽업으로 세트를 건네는 바닥 자리, 프로토 (-3.5, 0, 0.85)), DrinkLook(음료 표시판), StaffDoor(문 앞 바닥).",
    "clear": "직원 스툴 자리(프로토 (-3.72, z -2.5)), 조리 직원 시작점(프로토 (-5, z -1.4))과 픽업 경로(프로토 (-4.7, z 0.85) -> (-3.5, z 0.85)), 카운터 뒤 통로는 비워 둠.",
}
k3d.export("StoreKitchen", "Store", [root], notes=notes)
k3d.preview("StoreKitchen", [root], views=((60, 20), (125, 15)))
k3d.preview("StoreKitchen", [root], views=((90, 8),), lens=35, tag="fp")

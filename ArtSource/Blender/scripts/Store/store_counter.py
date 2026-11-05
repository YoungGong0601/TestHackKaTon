"""StoreCounter: 주문/픽업 카운터 (히어로). 정면(손님 쪽) = -Y, 길이 = X, 원점 = 바닥 중앙.
매장 배치: 블렌더 매장좌표 (-2.96, 1.25, 0) + Z회전 +90° / Unity (2.96, 0, -1.25), yaw -90°.
로컬 X = 프로토타입 -Z 방향 (x=+2.95 끝이 뒷벽, x=-2.95 끝이 칸막이벽 쪽 픽업)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
k3d = S.k3d
k3d.reset()
S.textures()

L, D, TOP = 5.9, 0.72, 1.055
X0, X1 = -L / 2, L / 2

# ---- 머티리얼 (굽기용 절차 재질)
wood_img = k3d.polyhaven("kitchen_wood", "1k")["diff"]
m_wood = S.pbr("M_tmp_CounterWood", (0.78, 0.62, 0.48), 0.42, img=wood_img, img_m=0.6, var=0.06, grime=0.5,
               gdist=0.03, edge=0.35, edge_col=(0.55, 0.45, 0.35), bump=0.05, smudge=0.15)
m_gap = S.pbr("M_tmp_CounterGap", (0.035, 0.028, 0.022), 0.7, grime=0.2, bump=0)
m_red = S.pbr("M_tmp_CounterRed", (0.42, 0.035, 0.022), 0.38, var=0.08, grime=0.45, edge=0.7,
              edge_col=(0.62, 0.55, 0.5), scratch=0.5, smudge=0.25, bump=0.08)
m_kick = S.pbr("M_tmp_CounterKick", (0.025, 0.025, 0.025), 0.6, grime=0.6, grime_col=(0.09, 0.08, 0.06),
               scratch=0.8, edge=0.4, edge_col=(0.12, 0.12, 0.12))
m_quartz = S.pbr("M_tmp_CounterQuartz", (0.055, 0.052, 0.05), 0.22, var=0.25, vscale=180, grime=0.4,
                 smudge=0.35, scratch=0.25, bump=0.03, bscale=300)
m_steel = S.pbr("M_tmp_CounterSteel", (0.62, 0.62, 0.6), 0.3, 1.0, var=0.05, grime=0.5, brush=0.18,
                smudge=0.3, scratch=0.4, bump=0.02)
m_mel = S.pbr("M_tmp_CounterMelamine", (0.72, 0.71, 0.68), 0.55, var=0.05, grime=0.6, gdist=0.12,
              edge=0.3, edge_col=(0.5, 0.42, 0.3), streak=0.15, bump=0.02)
m_blk = S.pbr("M_tmp_CounterBlackPlastic", (0.03, 0.03, 0.032), 0.45, var=0.1, grime=0.35, smudge=0.4,
              edge=0.3, edge_col=(0.1, 0.1, 0.1), bump=0.04, bscale=200)
m_grey = S.pbr("M_tmp_CounterGreyPlastic", (0.16, 0.16, 0.17), 0.5, grime=0.4, smudge=0.3, bump=0.04, bscale=200)
m_chrome = S.pbr("M_tmp_CounterChrome", (0.8, 0.8, 0.8), 0.12, 1.0, var=0.04, grime=0.4, scratch=0.3, smudge=0.2, bump=0)
m_vinyl = S.pbr("M_tmp_CounterVinyl", (0.02, 0.018, 0.017), 0.42, var=0.08, grime=0.3, bump=0.3, bscale=400,
                edge=0.5, edge_col=(0.08, 0.075, 0.07))
m_card = S.pbr("M_tmp_CounterCardboard", (0.45, 0.32, 0.2), 0.8, var=0.15, grime=0.4, bump=0.1)
m_paper = S.pbr("M_tmp_CounterPaper", (0.75, 0.6, 0.42), 0.85, var=0.1, grime=0.3, bump=0.05)
m_cup = S.pbr("M_tmp_CounterCup", (0.82, 0.8, 0.76), 0.5, var=0.05, grime=0.2)

# ---- 본체 (정면 + 상판 + 걸레받이)
body = []
body.append(S.boxz("c_plinth", X0 + 0.01, X1 - 0.01, -0.31, 0.33, 0, 0.1, m_kick, 0.004))
body.append(S.boxz("c_panel", X0, X1, -0.345, -0.32, 0.1, 0.86, m_gap, 0.002))
x = X0 + 0.02
while x + 0.03 <= X1 - 0.015:
    body.append(S.boxz("c_slat", x, x + 0.03, -0.366, -0.344, 0.112, 0.852, m_wood, 0.0035, 1))
    x += 0.045
body.append(S.boxz("c_band", X0, X1, -0.372, -0.32, 0.86, 1.015, m_red, 0.004, 3))
body.append(S.boxz("c_bandlip", X0, X1, -0.376, -0.366, 0.852, 0.862, m_steel, 0.002, 1))  # 띠 아래 금속 몰딩
# 상판 (픽업 구간은 스테인리스 받침으로 끊김)
PK0, PK1 = -2.65, -1.55
body.append(S.boxz("c_top_a", X0 - 0.025, PK0, -0.40, 0.40, 1.015, TOP, m_quartz, 0.004, 3))
body.append(S.boxz("c_top_b", PK1, X1 + 0.025, -0.40, 0.40, 1.015, TOP, m_quartz, 0.004, 3))
body.append(S.boxz("c_pick_base", PK0, PK1, -0.40, 0.40, 1.015, 1.045, m_steel, 0.003, 2))
body.append(S.boxz("c_pick_tray", PK0 + 0.01, PK1 - 0.01, -0.34, 0.30, 1.045, 1.058, m_steel, 0.002, 1))
for y in (-0.36, 0.34):  # 받침 앞뒤 턱
    body.append(S.boxz("c_pick_lip", PK0, PK1, y, y + 0.025, 1.045, 1.075, m_steel, 0.003, 2))
# 상판 배선 구멍 (그로밋)
body.append(S.boxz("c_pick_plate", -2.42, -1.78, -0.371, -0.366, 0.61, 0.83, m_blk, 0.002, 1))
body.append(S.cyl("c_grommet", 0.03, 0.006, (0.05, 0.25, TOP + 0.002), m_blk, 20, 0.002))
counter = S.join(body, "StoreCounter_Body")
S.set_origin(counter, (0, 0, 0))

# ---- 직원 쪽 수납장 (멜라민 선반)
back = []
back.append(S.boxz("b_bottom", X0, X1, -0.32, 0.36, 0.1, 0.12, m_mel, 0.003))
back.append(S.boxz("b_top", X0, X1, -0.32, 0.36, 0.985, 1.015, m_mel, 0.003))
for z in (0.46, 0.74):
    back.append(S.boxz("b_shelf", X0 + 0.02, X1 - 0.02, -0.3, 0.34, z, z + 0.02, m_mel, 0.003))
for xd in (-1.95, -0.95, 0.05, 1.05, 2.05):
    back.append(S.boxz("b_div", xd - 0.009, xd + 0.009, -0.32, 0.36, 0.12, 0.985, m_mel, 0.003))
# 돈통 (상판 아래, POS 앞)
back.append(S.boxz("b_drawer", 0.08, 0.52, -0.06, 0.36, 0.86, 0.975, m_blk, 0.004))
back.append(S.boxz("b_drawer_pull", 0.24, 0.36, 0.36, 0.375, 0.9, 0.915, m_chrome, 0.003))
back.append(S.cyl("b_lock", 0.009, 0.01, (0.45, 0.365, 0.94), m_chrome, 12, 0.002, rot=(math.pi / 2, 0, 0)))
# 선반 위 물건: 종이봉투 묶음, 컵 슬리브, 상자
for i, xx in enumerate((-2.6, -2.3, -1.5)):
    back.append(S.boxz("b_bags", xx, xx + 0.26, -0.05, 0.3, 0.48, 0.48 + 0.09 + i * 0.02, m_paper, 0.01, 2))
for i in range(3):
    back.append(S.cyl("b_cups", 0.045, 0.24, (-0.6 + i * 0.1, 0.2, 0.12 + 0.12), m_cup, 16, 0.003))
back.append(S.boxz("b_box", 0.3, 0.75, -0.2, 0.3, 0.12, 0.40, m_card, 0.01, 2))
back.append(S.boxz("b_box2", 1.2, 1.6, -0.1, 0.32, 0.76, 0.96, m_card, 0.01, 2))
back.append(S.boxz("b_box3", 2.3, 2.85, -0.25, 0.3, 0.12, 0.38, m_card, 0.01, 2))
shelves = S.join(back, "StoreCounter_Back")
S.set_origin(shelves, (0, 0, 0))

# ---- POS 계산대 (사용 안 함, 직원 쪽을 봄)
pos = []
PX = 0.3
pos.append(S.boxz("p_base", PX - 0.11, PX + 0.11, 0.05, 0.25, TOP, TOP + 0.022, m_blk, 0.006, 2))
pos.append(S.cyl("p_neck", 0.022, 0.16, (PX, 0.16, TOP + 0.1), m_blk, 16, 0.003))
scr = S.box("p_screen", (0.38, 0.045, 0.29), (0, 0, 0), m_blk, 0.008, 2)
scr.location = (PX, 0.13, TOP + 0.27)
scr.rotation_euler = (math.radians(18), 0, 0)
pos.append(scr)
cd = S.box("p_custdisp", (0.24, 0.03, 0.15), (0, 0, 0), m_blk, 0.006, 2)  # 손님용 보조 화면 (뒷면)
cd.location = (PX, 0.085, TOP + 0.33)
cd.rotation_euler = (math.radians(-8), 0, 0)
pos.append(cd)
pos.append(S.boxz("p_printer", PX + 0.25, PX + 0.4, 0.06, 0.26, TOP, TOP + 0.13, m_grey, 0.01, 2))
pos.append(S.boxz("p_printer_slot", PX + 0.26, PX + 0.39, 0.055, 0.07, TOP + 0.1, TOP + 0.112, m_blk, 0.002, 1))
# 카드 단말기 (손님 쪽, 기울어진 거치대)
ct = S.box("p_cardterm", (0.085, 0.17, 0.05), (0, 0, 0), m_blk, 0.01, 2)
CT = (PX + 0.42, -0.24, TOP + 0.072)
ct.location = CT
ct.rotation_euler = (math.radians(35), 0, 0)
pos.append(ct)
pos.append(S.boxz("p_cardstand", PX + 0.38, PX + 0.46, -0.27, -0.17, TOP, TOP + 0.03, m_grey, 0.006, 2))
SN, CS = math.sin(math.radians(35)), math.cos(math.radians(35))
for i in range(4):  # 키패드
    for j in range(3):
        kb = S.box("p_key", (0.018, 0.014, 0.006), (0, 0, 0), m_grey, 0.002, 1)
        t = -0.04 + i * 0.019
        kb.location = (CT[0] - 0.022 + j * 0.022, CT[1] - 0.026 * SN + t * CS, CT[2] + 0.026 * CS + t * SN)
        kb.rotation_euler = (math.radians(35), 0, 0)
        pos.append(kb)
# 아크릴 안내 스탠드 2개 (키오스크 주문 / 현금 없는 매장)
for nm, sx, sy in (("kiosk", 2.25, -0.22), ("cash", -0.35, -0.26)):
    pos.append(S.boxz("p_stand_" + nm, sx - 0.13, sx + 0.13, sy - 0.05, sy + 0.05, TOP, TOP + 0.012, m_chrome, 0.003, 1))
for sx, sy, w, h, zc in ((2.25, -0.22, 0.25, 0.18, TOP + 0.1), (-0.35, -0.26, 0.23, 0.105, TOP + 0.06)):
    n = (0, -math.sin(math.radians(80)), math.cos(math.radians(80)))
    pl = S.box("p_acryl", (w, 0.005, h), (sx - 0.004 * n[0], sy - 0.004 * n[1], zc - 0.004 * n[2]), m_chrome, 0.001, 1,
               rot=(math.radians(-10), 0, 0))
    pos.append(pl)
pos_obj = S.join(pos, "StoreCounter_POS")
S.set_origin(pos_obj, (0, 0, 0))

# ---- 픽업 열등 갠트리
pk = []
for xx in (-2.5, -1.7):
    pk.append(S.cyl("k_rod", 0.009, 0.6, (xx, -0.12, 1.9), m_steel, 12, 0.002))
    pk.append(S.cyl("k_cap", 0.025, 0.012, (xx, -0.12, 2.194), m_steel, 16, 0.002))
pk.append(S.boxz("k_bar", -2.58, -1.62, -0.145, -0.095, 1.58, 1.63, m_steel, 0.004, 2))
pk.append(S.boxz("k_signplate", -2.42, -1.78, -0.145, -0.136, 1.62, 1.84, m_red, 0.003, 2))
for xx in (-2.4, -1.8):
    pk.append(S.cyl("k_shade", 0.11, 0.1, (xx, -0.12, 1.47), m_red, 28, 0.003, r2=0.045))
    pk.append(S.cyl("k_neck", 0.012, 0.06, (xx, -0.12, 1.55), m_steel, 12, 0.002))
pick = S.join(pk, "StoreCounter_PickupLamp")
S.set_origin(pick, (0, 0, 0))

# ---- 의자 (직원용 회전 스툴, 앉는 높이 0.655)
st = []
st.append(S.cyl("s_base", 0.22, 0.02, (0, 0, 0.01), m_chrome, 32, 0.006))
st.append(S.cyl("s_col", 0.025, 0.5, (0, 0, 0.27), m_chrome, 16, 0.003))
st.append(S.cyl("s_sleeve", 0.035, 0.12, (0, 0, 0.56), m_blk, 16, 0.004))
st.append(S.cyl("s_pan", 0.15, 0.02, (0, 0, 0.615), m_blk, 28, 0.004))
st.append(S.cyl("s_seat", 0.17, 0.045, (0, 0, 0.6375), m_vinyl, 32, 0.02, 3))
bpy = S.bpy
bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.011, major_segments=40, minor_segments=8, location=(0, 0, 0.3))
ring = bpy.context.active_object
ring.data.materials.append(m_chrome)
st.append(ring)
for a in range(3):
    ang = a * math.tau / 3
    sp = S.box("s_spoke", (0.16, 0.012, 0.012), (math.cos(ang) * 0.09, math.sin(ang) * 0.09, 0.3), m_chrome, 0.003, 1,
               rot=(0, 0, ang))
    st.append(sp)
stool = S.join(st, "StoreCounter_Stool")
S.set_origin(stool, (0, 0, 0))

# ---- 굽기
k3d.bake(counter, 2048, samples=48, ao_distance=0.12)
k3d.bake(shelves, 1024, samples=32, ao_distance=0.15)
k3d.bake(pos_obj, 1024, samples=48, ao_distance=0.05)
k3d.bake(pick, 512, samples=32, ao_distance=0.05)
k3d.bake(stool, 512, samples=32, ao_distance=0.06)

# ---- 글자/화면 (굽지 않음: 아틀라스 이미지 머티리얼)
A = "counter_signs.png"
m_sign = S.img_mat("M_StoreCounter_Signs", S.tex(A), rough=0.35)
m_screen = S.img_mat("M_StoreCounter_Screens", S.tex(A), rough=0.15, emit=0.8)
m_lamp = k3d.mat("M_StoreCounter_LampGlow", (1.0, 0.55, 0.25), 0.4, emission=(1.0, 0.45, 0.15), strength=6.0)
labels = []
# 정면: 픽업 안내판 (아크릴 판 위에 인쇄), 로고, 와이파이·알레르기 스티커
labels.append(S.quad("l_pickup_front", 0.62, 0.198, (-2.1, -0.3725, 0.72), m_sign, uv=S.atlas_uv(A, "pickup")))
for xx in (-0.9, 0.9):
    u0, v0, u1, v1 = S.atlas_uv(A, "band")
    sub = (u0 + 40 / 2048, v0 + 10 / 2048, u0 + 600 / 2048, v0 + 150 / 2048)  # 띠 안의 로고 1개
    labels.append(S.quad("l_logo", 0.5, 0.125, (xx, -0.3735, 0.9375), m_sign, uv=sub))
labels.append(S.quad("l_wifi", 0.12, 0.06, (2.45, -0.3735, 0.935), m_sign, uv=S.atlas_uv(A, "wifi")))
labels.append(S.quad("l_allergy", 0.21, 0.151, (2.62, -0.3675, 0.62), m_sign, uv=S.atlas_uv(A, "allergy")))
# 픽업 갠트리 간판 (양면)
labels.append(S.quad("l_pickup_bar", 0.62, 0.198, (-2.1, -0.1475, 1.73), m_sign, uv=S.atlas_uv(A, "pickup")))
# 아크릴 스탠드 인쇄물 (10도 뒤로 기울임)
labels.append(S.quad("l_kiosk_stand", 0.24, 0.17, (2.25, -0.22, TOP + 0.1), m_sign, rot=(math.radians(80), 0, 0),
                     uv=S.atlas_uv(A, "kiosk")))
labels.append(S.quad("l_cash_stand", 0.22, 0.095, (-0.35, -0.26, TOP + 0.06), m_sign, rot=(math.radians(80), 0, 0),
                     uv=S.atlas_uv(A, "cashless")))
# POS 화면 (직원 쪽 +Y 를 봄), 손님용 보조 화면, 카드 단말기 LCD
q = S.quad("l_pos", 0.34, 0.25, (0, 0, 0), m_screen, rot=(math.radians(90 - 18), 0, math.pi), uv=S.atlas_uv(A, "pos"))
q.location = (PX, 0.13 + 0.0235 * math.cos(math.radians(18)), TOP + 0.27 + 0.0235 * math.sin(math.radians(18)))
labels.append(q)
q = S.quad("l_custdisp", 0.21, 0.13, (0, 0, 0), m_screen, rot=(math.radians(90 - 8), 0, 0), uv=S.atlas_uv(A, "kiosk"))
q.location = (PX, 0.085 - 0.0155 * math.cos(math.radians(8)), TOP + 0.33 + 0.0155 * math.sin(math.radians(8)))
labels.append(q)
q = S.quad("l_lcd", 0.06, 0.03, (0, 0, 0), m_screen, rot=(math.radians(35), 0, 0), uv=S.atlas_uv(A, "lcd"))
q.location = (CT[0], CT[1] - 0.0255 * SN + 0.045 * CS, CT[2] + 0.0255 * CS + 0.045 * SN)
labels.append(q)
lab = S.join(labels, "StoreCounter_Labels")
S.set_origin(lab, (0, 0, 0))
# 열등 전구 (발광, 굽지 않음)
glows = [S.cyl("g", 0.04, 0.004, (xx, -0.12, 1.418), m_lamp, 20, 0) for xx in (-2.4, -1.8)]
glow = S.join(glows, "StoreCounter_LampGlow")
S.set_origin(glow, (0, 0, 0))

# ---- 계층/소켓
root = counter
for o in (shelves, pos_obj, pick, lab, glow):
    S.reparent(o, root)
stool.location = (1.25, 0.76, 0)
S.reparent(stool, root)
S.empty("StoreCounter_Socket_StaffSit", (1.25, 0.76, 0.66), root)
S.empty("StoreCounter_Socket_StaffTalk", (1.25, -0.16, 1.3), root)
S.empty("StoreCounter_Socket_Pickup", (-2.1, -0.04, 1.058), root)
S.empty("StoreCounter_Socket_PickupCall", (-2.1, -0.04, 1.4), root)
S.empty("StoreCounter_Socket_TrayStack", (-0.9, -0.05, TOP), root)
S.empty("StoreCounter_Socket_POS", (PX, 0.15, TOP), root)

notes = ("주문/픽업 카운터. 길이 5.9m, 높이 1.055m, 정면(손님)=-Y. 매장 배치: Unity 위치 (2.96, 0, -1.25), Y회전 -90 "
         "(블렌더 매장좌표 (-2.96, 1.25, 0), Z회전 +90). 로컬 +X 끝(x=2.95)이 뒷벽, -X 끝이 칸막이벽/픽업 쪽. "
         "자식: StoreCounter_Stool(직원 스툴, 원점=바닥 중앙, 좌석 높이 0.655), StoreCounter_LampGlow(열등 발광), StoreCounter_Labels(사인·화면 이미지, 굽지 않음). "
         "소켓: StaffSit(스툴 좌석), StaffTalk(말 걸기 지점, 프로토 COUNTER_X-0.2), Pickup(픽업 받침 위, 프로토 PICK), PickupCall(호출음), "
         "TrayStack(쟁반 쌓는 자리, 쟁반은 food 그룹), POS. 열등 갠트리 봉은 천장 소핏 아래(z=2.2)에 닿음.")
k3d.export("StoreCounter", "Store", [root], notes=notes)
k3d.preview("StoreCounter", [root], views=((25, 14), (200, 18)))
k3d.preview("StoreCounter", [root], views=((0, 8),), lens=35, tag="fp")

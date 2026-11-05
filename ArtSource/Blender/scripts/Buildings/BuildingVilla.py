"""BuildingVilla: 붉은 벽돌 다세대 '행복빌라' (1층 필로티 주차장 + 3개 층 + 옥탑 계단실/물탱크).
프로토타입 Km 모듈 Hr(w 12.2, 필로티 2.5m, 층고 2.75m x3, 벽돌, 브론즈 창틀) 기준."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d

A = "BuildingVilla"
k3d.reset()
P = bld.palette()
P["guard"] = bld.pm("GuardYellow", (0.75, 0.55, 0.03), 0.6, edge=(0.2, 0.2, 0.2), edge_amt=0.8, grime=0.5)
P["paintline"] = bld.pm("ParkLine", (0.78, 0.77, 0.72), 0.7, grime=0.5, bump=0.5, scale=20.0, var=0.25)
P["frp"] = bld.pm("FrpBlue", (0.07, 0.2, 0.42), 0.5, edge=(0.3, 0.4, 0.5), grime=0.45, streak=0.4)
BR, PL, CO = bld.T("RedBrick"), bld.T("Plaster"), bld.T("Concrete")

sign = bld.Atlas(A, "Sign", (2048, 1024))
dec = bld.Atlas(A, "Decal", (1024, 512), "RGBA")
inn = bld.Atlas(A, "Interior", (2048, 1024))
gri = bld.Atlas(A, "Grime", (1024, 1024), "RGBA")
Mt = bld.mats(A, sign, dec, inn, gri, inner_emit=0.08)

W, D, PIL = 12.2, 11.0, 2.5          # 폭, 깊이, 필로티 높이
FH, NF, PAR = 2.75, 3, 0.85
HU = FH * NF                          # 위 상자 높이 (필로티 위)
HT = PIL + HU + PAR

addr = sign.add(900, 300, kind="plate_addr", road="은행길", en="Eunhaeng-gil", num="23")
name = sign.add(640, 200, kind="plate", bg="#d9d3c1", lines=["행복빌라"], fg="#3a3226", font="myungjo", border="#8a7a5a")
park = sign.add(600, 420, kind="plate", bg="#f2f0ea", lines=["외부차량 주차금지", "적발 시 견인 조치"], fg="#b4291f",
                border="#b4291f", sizes=[0.4, 0.25])
cctv_s = sign.add(420, 260, kind="plate", bg="#f2c700", lines=["CCTV 녹화중", "24시간 촬영"], fg="#1a1a1a", screws=False)
mail = sign.add(720, 440, kind="mailbox", grid=[3, 2], nums=["201", "202", "301", "302", "401", "402"])
keyp = sign.add(200, 300, kind="keypad")
pull = dec.add(300, 100, kind="plate", bg="#f4f1ea", lines=["당기세요"], fg="#c0221a", screws=False, dirt=0.1)
gas_s = dec.add(320, 120, kind="plate", bg="#f2c700", lines=["가스 배관 · 화기 엄금"], fg="#222222", screws=False)

M = bld.Mesh()

# ---- 위 상자 (필로티 위 z=2.5 부터): 앞 창 4칸 x 3층, 옆 작은 창
BAYS = [-4.575, -1.525, 1.525, 4.575]
KIND = [("L", 2.0, 1.4, 0.9), ("M", 1.2, 1.2, 0.9), ("L", 2.0, 1.4, 0.9), ("S", 0.7, 0.6, 1.6)]
wins = []
for f in range(NF):
    for b, (k, w, h, z) in zip(BAYS, KIND):
        wins.append((f, b, k, w, h, f * FH + z))
holes = [bld.fhole(W, b, z, w, h) for (f, b, k, w, h, z) in wins]
rh = [(3.2 - 0.45, 3.2 + 0.45, f * FH + 1.2, f * FH + 2.1) for f in range(NF)]
lh = [(D - 4.0 - 0.45, D - 4.0 + 0.45, f * FH + 1.2, f * FH + 2.1) for f in range(NF)]
old = M.at((0, 0, PIL))
bld.shell(M, W, D, HU, BR, BR, PL, CO, PL, PL, par=PAR, holes=holes, lholes=lh, rholes=rh)
bld.bands(M, PL, W, [FH - 0.02, 2 * FH - 0.02])
frames = {0: "bronze", 1: "pvc", 2: "bronze"}
for i, (f, b, k, w, h, z) in enumerate(wins):
    it = inn.add(230 * (w + 0.1), 230 * (h + 0.1), kind="interior", v=i * 5 + f)
    bld.fwin(M, P, W, b, z, w, h, frame=frames[f], sashes=2 if k != "S" else 1, grille=(f == 0 and k != "S"),
             interior=it, interior_m=Mt["inner"], glass_m=Mt["glass"], slide=0.25 * ((i * 7) % 3),
             screen_m=Mt["screen"] if k == "L" else None)
    if k == "L" and f > 0:   # 창 난간
        bld.railing(M, P["sus"], (b - w / 2 - 0.05, -0.13), (b + w / 2 + 0.05, -0.13), z - 0.05, h=0.55, post=1.1, bal=0.12,
                    top_r=0.016, bal_r=0.007)
        for sx in (-1, 1):
            M.box(P["sus"], (b + sx * (w / 2 + 0.05), -0.07, z + 0.45), (0.03, 0.12, 0.03), 0.004)
for (u0, u1, v0, v1) in rh:   # 오른쪽 옆 창
    bld.window(M, P, None, (W / 2, 0, 0), (0, 1, 0), (0, 0, 1), u0, u1, v0, v1, frame="pvc", sashes=2,
               interior=inn.add(300, 300, kind="interior", v=40 + int(v0)), interior_m=Mt["inner"], glass_m=Mt["glass"])
for (u0, u1, v0, v1) in lh:
    bld.window(M, P, None, (-W / 2, D, 0), (0, -1, 0), (0, 0, 1), u0, u1, v0, v1, frame="bronze", sashes=2, grille=v0 < 2,
               interior=inn.add(300, 300, kind="interior", v=50 + int(v0)), interior_m=Mt["inner"], glass_m=Mt["glass"])
# 때 덮개 (정면)
drips = [((-4.575 + 0.6 + W / 2) / W - 0.03, (-4.575 + 0.6 + W / 2) / W + 0.03, 1 - (FH + 0.1) / (HU + PAR), 0.25)]
bld.grime_wall(M, Mt["grime"], gri.add(1024, 1024, **bld.grime_spec(W, HU + PAR, holes, drips, 0.85, 3)), W, HU + PAR, holes)
# 실외기
bld.ac_unit(M, P, (-4.575 + 0.55, 0, FH + 0.14), pipe_up=0.5, pipe_side=0.35)
bld.ac_unit(M, P, (1.525 + 0.55, 0, 2 * FH + 0.14), pipe_up=0.5, pipe_side=0.35)
bld.ac_unit(M, P, (W / 2, 6.2, FH * 2 + 0.6), rz=math.pi / 2, pipe_up=0.4, pipe_side=0.3)
# 옥상: 이름 글자, 계단실, 물탱크, 안테나
M.letters("행복빌라", bld.tex2d_font("black"), 0.78, P["brass"], (0, 0.0, HU + 0.1), depth=0.05, spacing=1.05)
M.box(PL, (3.0, 7.7, HU + 1.3), (3.2, 3.0, 2.6), 0.02)
M.box(PL, (3.0, 7.7, HU + 2.64), (3.36, 3.16, 0.08), 0.01)
M.box(P["steel"], (3.4, 7.7 - 1.51, HU + 1.0), (0.9, 0.04, 2.0), 0.008)
M.box(P["sus"], (3.0, 7.7 - 1.535, HU + 1.0), (0.04, 0.03, 0.14), 0.004)
M.box(P["light"], (3.4, 7.7 - 1.53, HU + 2.2), (0.25, 0.06, 0.12), 0.01)
for sx in (-0.6, 0.6):
    for sy in (-0.4, 0.4):
        M.box(P["galv"], (-3.4 + sx, 8.0 + sy, HU + 0.2), (0.06, 0.06, 0.4), 0.004)
M.box(P["galv"], (-3.4, 8.0, HU + 0.42), (1.5, 1.1, 0.05), 0.004)
M.box(P["frp"], (-3.4, 8.0, HU + 1.1), (1.6, 1.1, 1.3), 0.06, 3)
M.cyl(P["frp"], (-3.4, 8.0, HU + 1.74), (-3.4, 8.0, HU + 1.82), 0.25, 16)
M.path(P["pipe"], [(-2.6, 8.0, HU + 0.6), (-2.2, 8.0, HU + 0.6), (-2.2, 8.0, HU + 0.05)], 0.03, 8)
M.cyl(P["galv"], (4.2, 8.6, HU + 2.68), (4.2, 8.6, HU + 4.2), 0.02, 8)
for k in range(5):
    M.cyl(P["galv"], (4.2 - 0.5 + k * 0.05, 8.6, HU + 3.6 + k * 0.08), (4.2 + 0.5 - k * 0.05, 8.6, HU + 3.6 + k * 0.08), 0.006, 4)
M.T = old

# ---- 필로티 층 (z 0..2.5)
COLS = [-5.85, -1.95, 1.95, 5.85]
YE = 5.5                               # 뒤쪽 닫힌 부분 시작 (현관·우편함)
M.box(PL, (0, 0.225, PIL - 0.15), (W, 0.45, 0.3), 0.01)                       # 앞 보
M.quad(PL, (0, (0.45 + YE) / 2, PIL), (1, 0, 0), (0, -1, 0), W, YE - 0.45)            # 필로티 천장
for x in COLS:
    M.box(PL, (x, 0.25, (PIL - 0.3) / 2), (0.45, 0.45, PIL - 0.3), 0.015)
    M.box(P["granite"], (x, 0.25, 0.12), (0.48, 0.48, 0.24), 0.01)
    for cx in (-1, 1):                                                       # 모서리 보호대
        M.box(P["guard"], (x + cx * 0.215, 0.025, 0.7), (0.05, 0.05, 1.0), 0.006)
for x in COLS:
    M.box(PL, (x, YE - 0.05, PIL / 2), (0.45, 0.4, PIL), 0.015)
ent = (2.4, 4.6)
eh = [(ent[0] + W / 2, ent[1] + W / 2, 0, 2.3), (-3.6 + W / 2, -2.4 + W / 2, 1.2, 2.0)]
M.wall(BR, (-W / 2, YE, 0), (1, 0, 0), (0, 0, 1), W, PIL, eh, 0.3, reveal_m=PL)
M.wall(BR, (-W / 2, D, 0), (0, -1, 0), (0, 0, 1), D - YE, PIL, (), 0.3)
M.wall(BR, (W / 2, YE, 0), (0, 1, 0), (0, 0, 1), D - YE, PIL, (), 0.3)
M.wall(PL, (W / 2, D, 0), (-1, 0, 0), (0, 0, 1), W, PIL, (), 0.3)
M.quad(CO, (0, YE / 2, 0.003), (1, 0, 0), (0, 1, 0), W, YE)                   # 주차장 바닥
old = M.at((0, YE, 0))
bld.shopfront(M, P, ent[0], ent[1], glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, frame="bronze", z_open=2.3,
              room_d=2.4, door=0.35, inner=inn.add(800, 820, kind="shop", shop="stairs"), inner_m=Mt["inner"],
              door_item=pull, decal_m=Mt["decal"])
M.T = old
bld.window(M, P, None, (-W / 2, YE, 0), (1, 0, 0), (0, 0, 1), eh[1][0], eh[1][1], 1.2, 2.0, frame="pvc", sashes=2, grille=True,
           interior=inn.add(360, 240, kind="interior", v=3), interior_m=Mt["inner"], glass_m=Mt["glass"])
# 현관 주변: 우편함, 번호키, 이름판, 조명, CCTV
M.box(P["sus"], (0.5, YE - 0.06, 1.25), (0.92, 0.12, 0.58), 0.008)
M.quad(Mt["sign"], (0.5, YE - 0.121, 1.25), (1, 0, 0), (0, 0, 1), 0.88, 0.54, item=mail)
M.box(P["black"], (4.95, YE - 0.02, 1.35), (0.14, 0.04, 0.22), 0.01)
M.quad(Mt["sign"], (4.95, YE - 0.041, 1.35), (1, 0, 0), (0, 0, 1), 0.12, 0.18, item=keyp)
M.box(P["alu"], (5.0, YE - 0.012, 1.95), (0.66, 0.02, 0.22), 0.004)
M.quad(Mt["sign"], (5.0, YE - 0.023, 1.95), (1, 0, 0), (0, 0, 1), 0.64, 0.2, item=name)
for lx in (3.5, -3.0):
    M.cyl(P["pvc"], (lx, 3.6, PIL), (lx, 3.6, PIL - 0.06), 0.16, 20)
    M.cyl(P["light"], (lx, 3.6, PIL - 0.06), (lx, 3.6, PIL - 0.08), 0.13, 20)
bld.cctv(M, P, (-5.0, YE, PIL - 0.35))
M.box(P["alu"], (-1.95, 0.025 - 0.006, 1.55), (0.42, 0.012, 0.3), 0.003, 1)
M.quad(Mt["sign"], (-1.95, 0.025 - 0.0125, 1.55), (1, 0, 0), (0, 0, 1), 0.4, 0.28, item=park)
M.quad(Mt["sign"], (-5.85, 0.025 - 0.003, 1.8), (1, 0, 0), (0, 0, 1), 0.2, 0.124, item=cctv_s)
bld.address_plate(M, P, Mt["sign"], addr, 5.85, 1.9, y=0.025, w=0.42, h=0.14)
# 주차선 + 차 멈춤턱
for x in COLS:
    M.box(P["paintline"], (x, 2.9, 0.006), (0.1, 4.6, 0.006), 0)
for x in (-3.9, 0.0, 3.9):
    for sx in (-0.65, 0.65):
        M.box(P["guard"], (x + sx, 4.85, 0.05), (0.5, 0.14, 0.1), 0.015)
# 가스 배관: 오른쪽 기둥 앞으로 올라가 층마다 계량기
gx = 6.0
bld.gas_line(M, P, [(gx, -0.07, 0.5), (gx, -0.07, PIL + 2 * FH + 1.2)])
M.box(P["galv"], (gx, -0.07, 0.5), (0.06, 0.06, 0.08), 0.004)
for f in range(NF):
    z = PIL + f * FH + 1.0
    bld.gas_line(M, P, [(gx, -0.07, z), (5.35, -0.07, z)], meters=[(5.35, -0.05, z - 0.2)])
M.quad(Mt["decal"], (5.78, 0.022, 1.25), (1, 0, 0), (0, 0, 1), 0.2, 0.075, item=gas_s)
# 선홈통
bld.downpipe(M, P, -6.0, -0.08, HT)

notes = ("붉은 벽돌 다세대 빌라 '행복빌라'. 원점 = 도로 쪽 정면 벽 아래 중앙 (건물은 +Y=Unity -Z 쪽으로 11m 깊다, "
         "정면 = Unity +Z). 폭 12.2m, 필로티 2.5m + 3개 층(2.75m) + 파라펫 0.85m = 11.6m, 옥탑 계단실·물탱크 포함 약 14.4m. "
         "1층 필로티 주차 3칸(기둥 x=±1.95, ±5.85), 공동현관은 y=5.5m 안쪽 벽 x=2.4..4.6 (유리문 '당기세요'). "
         "벽 = M_Tile_Buildings_RedBrick/Plaster/Concrete (월드 UV, 1.4/2.0/3.0m), 창 유리 M_Glass_*, "
         "간판·명판·우편함 M_BuildingVilla_Sign, 창 안쪽 카드 M_BuildingVilla_Interior, 정면 때 덮개 M_BuildingVilla_Grime(투명). "
         "소켓: Entrance(현관문 앞 바닥), ParkingA/B/C(주차칸 중앙 바닥), Mailbox(우편함 앞).")
socks = [("Entrance", (3.5, YE - 0.8, 0), (0, 0, 0)), ("Mailbox", (0.5, YE - 0.7, 0), (0, 0, 0))]
socks += [(f"Parking{c}", (x, 2.6, 0), (0, 0, 0)) for c, x in zip("ABC", (-3.9, 0.0, 3.9))]
notes += (" 때 덮개(M_BuildingVilla_Grime)는 개구부를 잘라낸 띠 메시로 벽에서 12mm 앞에 있다. "
          "배치: 뒷벽과 창 없는 옆벽은 단순 미장면이므로 이웃 건물에 붙이거나 골목 안쪽으로 돌려 가릴 것.")
ob, paths = bld.finish(A, M, atlases=[sign, dec, inn, gri], bake_size=2048, notes=notes, sockets=socks, ao=0.3,
                       samples=32, fp=((-3.5, -9.5, 1.55), (0.5, 3.0, 4.5), 22))
print("PREVIEWS", paths)

"""BuildingSalon: 1층 '그린 미용실'(회전 싸인볼) + 계단실 입구 + 2~3층 주거. 크림색 긴 타일 외벽.
프로토타입 Km 모듈 Hr(w 11.5, base 3.6, floors 2) + Ji(kind hair, 간판 #7d3a52/#efe6d6) 기준."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d

A = "BuildingSalon"
k3d.reset()
P = bld.palette()
LT, PL, CO = bld.T("LongTileCream"), bld.T("Plaster"), bld.T("Concrete")

sign = bld.Atlas(A, "Sign", (2048, 1024))
dec = bld.Atlas(A, "Decal", (2048, 1024), "RGBA")
inn = bld.Atlas(A, "Interior", (2048, 1024))
gri = bld.Atlas(A, "Grime", (1024, 1024), "RGBA")
Mt = bld.mats(A, sign, dec, inn, gri, inner_emit=0.3)
pst = bld.Atlas(A, "PoleStripe", (256, 512))
pole_m = bld.flat_img(f"M_{A}_PoleStripe", pst.path, 0.3, emit=0.6)
P["red"] = bld.pm("PoleRed", (0.55, 0.04, 0.03), 0.3, grime=0.2, bump=0)
pole_g = bld.glass(A, "Pole", (0.8, 0.82, 0.85), 0.18, 0.05)

W, D, G, FH, NF, PAR = 11.5, 12.0, 3.6, 2.75, 2, 0.75
H = G + FH * NF
HT = H + PAR
ZO = 2.4
S0, S1 = -5.45, 1.45          # 미용실
E0, E1 = 2.1, 3.5             # 계단실 입구
BAYS = [-4.3, -1.45, 1.45, 4.3]
uw = []
for f in range(NF):
    for i, b in enumerate(BAYS):
        w, h = (1.9, 1.4) if i in (0, 2) else (1.2, 1.2)
        uw.append((f, b, w, h, G + f * FH + 0.9))
holes = [(S0 + W / 2, S1 + W / 2, 0, ZO), (E0 + W / 2, E1 + W / 2, 0, 2.3)] + [bld.fhole(W, b, z, w, h) for (f, b, w, h, z) in uw]
rh = [(4.0 - 0.4, 4.0 + 0.4, G + f * FH + 1.3, G + f * FH + 2.0) for f in range(NF)]

M = bld.Mesh()
bld.shell(M, W, D, H, LT, PL, PL, CO, PL, PL, par=PAR, holes=holes, rholes=rh)
bld.bands(M, PL, W, [G - 0.02, G + FH - 0.02])
for (a, b) in ((-W / 2, S0), (S1, E0), (E1, W / 2)):
    M.box(P["granite"], ((a + b) / 2, -0.03, 0.15), (b - a + 0.02, 0.06, 0.3), 0.008)

# ---- 미용실
door = dec.add(300, 100, kind="plate", bg="#f4f1ea", lines=["당기세요"], fg="#c0221a", screws=False, dirt=0.1)
posters = [(dec.add(1100, 150, kind="vinyl", lines=["커트 · 파마 · 염색 · 매직 · 클리닉"], fg="#f4e7ef"), -3.2, 2.12, 3.0, 0.32),
           (dec.add(420, 600, kind="poster", head="가격 안내", lines=["남성 커트 12,000", "여성 커트 15,000", "파마 40,000~",
                                                                 "염색 35,000~"], head_bg="#7d3a52"), -4.75, 1.2, 0.42, 0.6),
           (dec.add(420, 600, kind="poster", head="경로 우대", lines=["어르신 커트", "8,000원", "(65세 이상)", "화요일 휴무"],
                    head_bg="#3d6b4f"), -1.55, 1.2, 0.42, 0.6),
           (dec.add(360, 140, kind="plate", bg="#1d1d1d", lines=["OPEN"], fg="#ff5a4a", screws=False, dirt=0.05), 1.05, 1.75, 0.3, 0.12)]
bld.shopfront(M, P, S0, S1, glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, door=0.82, z_open=ZO, room_d=3.6,
              inner=inn.add(1100, 380, kind="shop", shop="hair"), inner_m=Mt["inner"], shut_m=bld.T("Shutter"),
              door_item=door, decal_m=Mt["decal"], posters=posters)
s = sign.add(2000, 205, kind="sign", bg="#7d3a52", fg="#efe6d6", text="그린 미용실", sub="커트 파마 염색", tel="02) 555-0171",
             logo="G", logo_bg="#efe6d6")
bld.signbox(M, P, P["galv"], Mt["sign"], s, ((S0 + S1) / 2, -0.42, 3.17), S1 - S0 + 0.1, 0.72, depth=0.42)
# 회전 싸인볼 (벽 브래킷 + 유리통 + 크롬 캡, 줄무늬 원통은 회전용 자식)
PX, PY, PZ = 1.78, -0.3, 1.62
M.box(P["sus"], (PX, -0.04, PZ + 0.45), (0.16, 0.08, 0.5), 0.01)
for z in (PZ + 0.12, PZ + 0.8):
    M.cyl(P["sus"], (PX, -0.06, z), (PX, PY, z), 0.018, 8)
M.cyl(P["sus"], (PX, PY, PZ - 0.06), (PX, PY, PZ + 0.04), 0.14, 24)
M.sphere(P["sus"], (PX, PY, PZ - 0.07), 0.06, 12)
M.cyl(P["sus"], (PX, PY, PZ + 0.86), (PX, PY, PZ + 0.98), 0.14, 24)
M.sphere(P["red"], (PX, PY, PZ + 1.04), 0.09, 14)
M.cyl(pole_g, (PX, PY, PZ + 0.04), (PX, PY, PZ + 0.86), 0.125, 24, cap=False)
M.path(P["black"], [(PX, -0.02, PZ + 0.2), (PX + 0.25, -0.015, PZ + 0.2), (PX + 0.25, -0.015, 0.4)], 0.006, 6)
pst.add(256, 512, kind="stripes", turns=1.5)
PM = bld.Mesh()
bld.stripe_cyl(PM, pole_m, (0, 0, 0), 0.1, 0.8, 24)

# ---- 계단실 입구 (위층 주거용)
bld.shopfront(M, P, E0, E1, glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, door=0.5, z_open=2.3, room_d=2.6, frame="bronze",
              inner=inn.add(560, 900, kind="shop", shop="stairs"), inner_m=Mt["inner"], lights=False)
M.box(P["sus"], (4.45, -0.05, 1.3), (0.7, 0.1, 0.42), 0.008)
M.quad(Mt["sign"], (4.45, -0.101, 1.3), (1, 0, 0), (0, 0, 1), 0.66, 0.38,
       item=sign.add(660, 380, kind="mailbox", grid=[2, 2], nums=["201", "202", "301", "302"]))
M.box(P["ivory"], (5.05, -0.07, 1.6), (0.36, 0.14, 0.5), 0.012)                       # 분전함
M.quad(Mt["decal"], (5.05, -0.141, 1.7), (1, 0, 0), (0, 0, 1), 0.22, 0.08,
       item=dec.add(260, 90, kind="plate", bg="#f2c700", lines=["위험 · 전기"], fg="#222222", screws=False))
bld.address_plate(M, P, Mt["sign"], sign.add(900, 300, kind="plate_addr", road="은행길", en="Eunhaeng-gil", num="27"),
                  4.45, 2.05, w=0.42, h=0.14)
M.quad(Mt["decal"], (2.8, 0.06, 2.42), (1, 0, 0), (0, 0, 1), 1.2, 0.12,
       item=dec.add(900, 90, kind="vinyl", lines=["그린빌 · 2층 ~ 3층"], fg="#e9e3d6"))

# ---- 위층 창 + 실외기 + 가스관 + 선홈통
for i, (f, b, w, h, z) in enumerate(uw):
    bld.fwin(M, P, W, b, z, w, h, frame="pvc" if (i + f) % 3 else "bronze", sashes=2, grille=False,
             interior=inn.add(220 * (w + 0.1), 220 * (h + 0.1), kind="interior", v=i * 7 + 2), interior_m=Mt["inner"],
             glass_m=Mt["glass"], screen_m=Mt["screen"] if w > 1.5 else None, slide=0.3 * ((i * 5) % 3))
    if w > 1.5 and f == 1:
        bld.railing(M, P["sus"], (b - w / 2 - 0.05, -0.13), (b + w / 2 + 0.05, -0.13), z - 0.05, h=0.55, post=1.1, bal=0.12,
                    top_r=0.016, bal_r=0.007)
        for sx in (-1, 1):
            M.box(P["sus"], (b + sx * (w / 2 + 0.05), -0.07, z + 0.45), (0.03, 0.12, 0.03), 0.004)
for (u0, u1, v0, v1) in rh:
    bld.window(M, P, None, (W / 2, 0, 0), (0, 1, 0), (0, 0, 1), u0, u1, v0, v1, frame="pvc", sashes=2,
               interior=inn.add(200, 180, kind="interior", v=60 + int(v0)), interior_m=Mt["inner"], glass_m=Mt["glass"])
bld.grime_wall(M, Mt["grime"], gri.add(1024, 1024, **bld.grime_spec(W, HT, holes, (), 0.8, 11)), W, HT, holes)
bld.ac_unit(M, P, (-4.3 + 0.5, 0, G + 0.12 + FH), pipe_up=0.5, pipe_side=0.35)
bld.ac_unit(M, P, (W / 2, 7.0, G + 0.6), rz=math.pi / 2, pipe_up=0.4, pipe_side=0.3)
gx = W / 2 - 0.3
bld.gas_line(M, P, [(gx, -0.07, 0.4), (gx, -0.07, G + FH + 1.25)])
for f in range(NF):
    z = G + f * FH + 1.05
    bld.gas_line(M, P, [(gx, -0.07, z), (gx - 0.55, -0.07, z)], meters=[(gx - 0.55, -0.05, z - 0.2)])
bld.downpipe(M, P, -W / 2 + 0.12, -0.08, HT)
bld.cctv(M, P, (-W / 2 + 0.35, 0, G + 0.35), rz=-0.5)

notes = ("1층 '그린 미용실' + 계단실 입구 + 2~3층 주거 (크림색 긴 타일). 원점 = 도로 쪽 정면 벽 아래 중앙, 정면 = Unity +Z, 깊이 12m. "
         "폭 11.5m, 높이 9.85m. 미용실 x -5.45..1.45 (유리문 x≈0.2 '당기세요', 경로우대 포스터), 계단실 x 2.1..3.5. "
         "자식 BuildingSalon_PoleStripe = 회전 싸인볼 줄무늬 원통 (원점 = 회전축 아래 끝, 로컬 Z(Unity Y)축으로 돌리면 됨, "
         "M_BuildingSalon_PoleStripe 발광 0.6, UV u=둘레 v=높이). 유리통 M_Glass_BuildingSalon_Pole.")
socks = [("Door", (0.2, -0.6, 0), (0, 0, 0)), ("PoleLook", (PX, PY, PZ + 0.45), (0, 0, 0))]
notes += (" 때 덮개(M_BuildingSalon_Grime)는 개구부를 잘라낸 띠 메시로 벽에서 12mm 앞에 있다. "
          "배치: 뒷벽과 창 없는 옆벽은 단순 미장면이므로 이웃 건물에 붙이거나 골목 안쪽으로 돌려 가릴 것.")
ob, paths = bld.finish(A, M, atlases=[sign, dec, inn, gri, pst], bake_size=2048, notes=notes,
                       children=[(f"{A}_PoleStripe", PM, (PX, PY, PZ + 0.05))], sockets=socks, ao=0.3, samples=32,
                       fp=((-1.5, -7.0, 1.55), (0.0, 0.0, 2.6), 24))
print("PREVIEWS", paths)

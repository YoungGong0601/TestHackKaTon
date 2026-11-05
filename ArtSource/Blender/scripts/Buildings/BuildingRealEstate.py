"""BuildingRealEstate: 1층 '믿음 공인중개사'(유리창 매물 전단 전세/월세/매매/급매) + '새봄 약국', 2~4층 치과·한의원·영어,
오른쪽 세로 돌출 간판(영어/치과/한의원/노래방/당구장). 갈색 띠 타일 외벽. 프로토타입 Km 모듈 VS 건물 a 기준."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d

A = "BuildingRealEstate"
k3d.reset()
P = bld.palette()
FB, PL, CO, SH = bld.T("FacadeBrown"), bld.T("Plaster"), bld.T("Concrete"), bld.T("Shutter")

sign = bld.Atlas(A, "Sign", (2048, 2048))
dec = bld.Atlas(A, "Decal", (2048, 2048), "RGBA")
inn = bld.Atlas(A, "Interior", (2048, 1024))
gri = bld.Atlas(A, "Grime", (1024, 1024), "RGBA")
Mt = bld.mats(A, sign, dec, inn, gri, inner_emit=0.3)

W, D, G, FH, NF, PAR = 12.0, 11.0, 3.6, 2.75, 3, 0.75
H = G + FH * NF
HT = H + PAR
ZO = 2.4
R0, R1 = -5.75, -0.25         # 부동산
Y0, Y1 = 0.05, 5.4            # 약국
BAYS = [-4.5, -1.5, 1.5, 4.2]
uw = []
for f in range(NF):
    for i, b in enumerate(BAYS):
        w, h = (1.9, 1.4) if i < 3 else (1.2, 1.3)
        uw.append((f, b, w, h, G + f * FH + 0.9))
holes = [(R0 + W / 2, R1 + W / 2, 0, ZO), (Y0 + W / 2, Y1 + W / 2, 0, ZO)] + [bld.fhole(W, b, z, w, h) for (f, b, w, h, z) in uw]
lh = [(D - 4.0 - 0.4, D - 4.0 + 0.4, G + f * FH + 1.3, G + f * FH + 2.0) for f in range(NF)]

M = bld.Mesh()
bld.shell(M, W, D, H, FB, PL, PL, CO, PL, PL, par=PAR, holes=holes, lholes=lh)
bld.bands(M, PL, W, [G - 0.02, G + FH - 0.02, G + 2 * FH - 0.02])
for (a, b) in ((-W / 2, R0), (R1, Y0), (Y1, W / 2)):
    M.box(P["granite"], ((a + b) / 2, -0.03, 0.15), (b - a + 0.02, 0.06, 0.3), 0.008)


def pull():
    return dec.add(300, 100, kind="plate", bg="#f4f1ea", lines=["당기세요"], fg="#c0221a", screws=False, dirt=0.1)


# ---- 부동산: 유리창 안쪽에 매물 전단, 위에 시트 글자
L1 = dec.add(780, 860, kind="listing", grid=[3, 3], seed=11)
L2 = dec.add(780, 860, kind="listing", grid=[3, 3], seed=12)
L3 = dec.add(640, 860, kind="listing", grid=[2, 3], seed=13)
posters = [(L1, -5.06, 1.3, 1.2, 1.32), (L2, -3.69, 1.3, 1.2, 1.32), (L3, -2.41, 1.3, 1.0, 1.32),
           (dec.add(1300, 140, kind="vinyl", lines=["아파트 · 빌라 · 원룸 · 상가 · 토지"], fg="#f4f0e4"), -3.55, 2.15, 3.4, 0.3),
           (dec.add(420, 130, kind="plate", bg="#c0221a", lines=["급매물 환영"], fg="#fff4d0", screws=False), -0.55, 1.75, 0.5, 0.15)]
bld.shopfront(M, P, R0, R1, glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, door=0.8, z_open=ZO, room_d=3.4,
              inner=inn.add(900, 400, kind="shop", shop="realty"), inner_m=Mt["inner"], shut_m=SH,
              door_item=pull(), decal_m=Mt["decal"], posters=posters)
s1 = sign.add(1900, 250, kind="sign", bg="#1f4a7a", fg="#f4f0e4", text="믿음 공인중개사", sub="전세 월세 매매 상가", tel="02) 555-0192")
bld.signbox(M, P, P["galv"], Mt["sign"], s1, ((R0 + R1) / 2, -0.42, 3.17), R1 - R0 + 0.1, 0.72, depth=0.42)
# ---- 약국
posters = [(dec.add(420, 600, kind="poster", head="감기 · 몸살", lines=["종합 감기약", "해열 진통제", "기침 · 가래", "상담 환영"],
                    head_bg="#1f7a4c"), 3.0, 1.25, 0.42, 0.6),
           (dec.add(420, 600, kind="poster", head="건강기능식품", lines=["홍삼 · 비타민", "관절 · 혈행", "어르신 할인"],
                    head_bg="#c47a1e"), 4.6, 1.25, 0.42, 0.6),
           (dec.add(1300, 140, kind="vinyl", lines=["처방 조제 · 일반 의약품 · 건강기능식품"], fg="#e9f4ec"), 3.8, 2.15, 3.0, 0.3)]
bld.shopfront(M, P, Y0, Y1, glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, door=0.3, z_open=ZO, room_d=3.4,
              inner=inn.add(900, 400, kind="shop", shop="pharm"), inner_m=Mt["inner"], shut_m=SH,
              door_item=pull(), decal_m=Mt["decal"], posters=posters)
s2 = sign.add(1800, 250, kind="sign", bg="#f0ece0", fg="#1f7a4c", text="새봄 약국", sub="처방 조제 건강식품", tel="02) 555-0147",
              band="#1f7a4c", logo="약", logo_bg="#1f7a4c")
bld.signbox(M, P, P["galv"], Mt["sign"], s2, ((Y0 + Y1) / 2, -0.42, 3.17), Y1 - Y0 + 0.1, 0.72, depth=0.42)
# ---- 세로 돌출 간판 + 위층 창 시트 글자
vs = sign.add(180, 1500, kind="vsign", blocks=[["#2b5d9a", "영어"], ["#b8352a", "치과"], ["#2c6e49", "한의원"],
                                               ["#6b3f86", "노래방"], ["#c47a1e", "당구장"]])
bld.vsign(M, P, P["galv"], Mt["sign"], vs, 5.62, G + 0.75, proj=0.62, h=5.2, th=0.22)
VIN = {0: ["소망", "치과", "임플란트", "교정"], 1: ["한의원", "침 · 뜸", "추나", "다이어트"], 2: ["영어", "회화", "내신", "토익"]}
COL = {0: "#b8352a", 1: "#2c6e49", 2: "#2b5d9a"}
for i, (f, b, w, h, z) in enumerate(uw):
    bld.fwin(M, P, W, b, z, w, h, frame="alu" if f < 2 else "pvc", sashes=2,
             interior=inn.add(220 * (w + 0.1), 220 * (h + 0.1), kind="interior", v=i * 3 + 4, office=True), interior_m=Mt["inner"],
             glass_m=Mt["glass"], slide=0.2 * (i % 3))
    k = BAYS.index(b)
    M.quad(Mt["decal"], (b, 0.14, z + h / 2 + 0.05), (1, 0, 0), (0, 0, 1), w * 0.72, h * 0.3,
           item=dec.add(600, 260, kind="vinyl", lines=[VIN[f][k]], fg=COL[f]))
for (u0, u1, v0, v1) in lh:
    bld.window(M, P, None, (-W / 2, D, 0), (0, -1, 0), (0, 0, 1), u0, u1, v0, v1, frame="pvc", sashes=2,
               interior=inn.add(200, 180, kind="interior", v=70 + int(v0)), interior_m=Mt["inner"], glass_m=Mt["glass"])
bld.grime_wall(M, Mt["grime"], gri.add(1024, 1024, **bld.grime_spec(W, HT, holes, (), 0.8, 13)), W, HT, holes)
bld.ac_unit(M, P, (-4.5 + 0.5, 0, G + 2 * FH + 0.12), pipe_up=0.5, pipe_side=0.35)
bld.ac_unit(M, P, (1.5 + 0.5, 0, G + FH + 0.12), pipe_up=0.5, pipe_side=0.35)
bld.ac_unit(M, P, (-W / 2, 5.0, G + 0.5), rz=-math.pi / 2, pipe_up=0.4, pipe_side=0.3)
gx = -W / 2 + 0.15
bld.gas_line(M, P, [(gx, -0.07, 0.4), (gx, -0.07, G + 2 * FH + 1.25)])
for f in range(NF):
    z = G + f * FH + 1.05
    bld.gas_line(M, P, [(gx, -0.07, z), (gx + 0.2, -0.07, z)], meters=[(gx + 0.2, -0.05, z - 0.2)])
bld.downpipe(M, P, W / 2 - 0.12, -0.08, HT)
bld.address_plate(M, P, Mt["sign"], sign.add(900, 300, kind="plate_addr", road="은행길", en="Eunhaeng-gil", num="35"),
                  5.7, 2.05, w=0.42, h=0.14)

notes = ("1층 '믿음 공인중개사'(x -5.75..-0.25, 유리창 매물 전단) + '새봄 약국'(x 0.05..5.4), 2층 치과 3층 한의원 4층 영어 (창 시트 글자), "
         "오른쪽 세로 돌출 간판 x=5.62 (양면, 벽에서 0.74m). 원점 = 도로 쪽 정면 벽 아래 중앙, 정면 = Unity +Z, 깊이 11m. "
         "폭 12m, 높이 12.6m. 매물 전단/시트 글자 = M_BuildingRealEstate_Decal (알파 클립, 유리 2cm 안쪽).")
socks = [("RealtyWindow", (-3.7, -0.8, 1.3), (0, 0, 0)), ("PharmacyDoor", (1.65, -0.6, 0), (0, 0, 0))]
notes += (" 때 덮개(M_BuildingRealEstate_Grime)는 개구부를 잘라낸 띠 메시로 벽에서 12mm 앞에 있다. "
          "배치: 뒷벽과 창 없는 옆벽은 단순 미장면이므로 이웃 건물에 붙이거나 골목 안쪽으로 돌려 가릴 것.")
ob, paths = bld.finish(A, M, atlases=[sign, dec, inn, gri], bake_size=2048, notes=notes, sockets=socks, ao=0.3,
                       samples=32, fp=((-3.0, -7.5, 1.55), (0.0, 0.0, 3.2), 24))
print("PREVIEWS", paths)

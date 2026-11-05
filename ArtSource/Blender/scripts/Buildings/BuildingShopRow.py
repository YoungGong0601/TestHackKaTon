"""BuildingShopRow: 1층 상가 3칸(태평 철물 / 꼬꼬 통닭 / 은하 세탁소) + 2층 보습학원 + 3층 주거. 회색 타일 외벽.
프로토타입 Km 모듈 VS (base 3.6m, 층고 2.75m, Ki 간판 색/문구) 기준. 롤 셔터·차양·간판."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d
from mathutils import Vector

A = "BuildingShopRow"
k3d.reset()
P = bld.palette()
FG, PL, CO, SH = bld.T("FacadeGrey"), bld.T("Plaster"), bld.T("Concrete"), bld.T("Shutter")

sign = bld.Atlas(A, "Sign", (2048, 1024))
dec = bld.Atlas(A, "Decal", (2048, 1024), "RGBA")
inn = bld.Atlas(A, "Interior", (2048, 1024))
gri = bld.Atlas(A, "Grime", (1024, 1024), "RGBA")
Mt = bld.mats(A, sign, dec, inn, gri, inner_emit=0.3)

W, D, G, FH, NF, PAR = 15.0, 9.0, 3.6, 2.75, 2, 0.7
H = G + FH * NF
HT = H + PAR
ZO = 2.4                                   # 점포 개구부 높이
SHOPS = [  # x0, x1, 간판, 실내, 셔터 내림 높이(None=올림), 차양
    (-7.2, -2.65, dict(bg="#d9c32f", fg="#1f1f1c", text="태평 철물", sub="열쇠 공구 페인트", tel="02) 555-0133"),
     dict(shop="hard"), 1.85, None),
    (-2.35, 2.55, dict(bg="#b8352a", fg="#f3ead8", text="꼬꼬 통닭", sub="생맥주 포장 환영", tel="02) 555-0129", stroke="#6e1a14"),
     dict(shop="food", pans=False, menu=["후라이드 18,000", "양념 19,000", "반반 19,000", "순살 20,000", "생맥주 4,000", "콜라 2,000"]),
     None, ("#9e2f27", "#d9d0bd")),
    (2.85, 7.2, dict(bg="#2f6ea5", fg="#f0eee4", text="은하 세탁소", sub="드라이 수선 운동화", tel="02) 555-0118", band="#e8e2d2"),
     dict(shop="laundry"), 0.0, None),
]
BAYS = [-5.625, -1.875, 1.875, 5.625]
holes = [(x0 + W / 2, x1 + W / 2, 0, ZO) for (x0, x1, *_) in SHOPS]
uw = []
for f in range(NF):
    for b in BAYS:
        uw.append((f, b, 1.9 if f == 0 else (1.9 if b in (-5.625, 1.875) else 1.2), 1.4 if f == 0 else 1.3, G + f * FH + 0.9))
holes += [bld.fhole(W, b, z, w, h) for (f, b, w, h, z) in uw]
lh = [(D - 3.5 - 0.4, D - 3.5 + 0.4, G + f * FH + 1.3, G + f * FH + 2.0) for f in range(NF)]

M = bld.Mesh()
bld.shell(M, W, D, H, FG, PL, PL, CO, PL, PL, par=PAR, holes=holes, lholes=lh)
bld.bands(M, PL, W, [G - 0.02, G + FH - 0.02])
for (a, b) in ((-W / 2, -7.2), (-2.65, -2.35), (2.55, 2.85), (7.2, W / 2)):   # 점포 사이 기둥 걸레받이
    M.box(P["granite"], ((a + b) / 2, -0.03, 0.15), (b - a + 0.02, 0.06, 0.3), 0.008)
for (x0, x1, sg, sp, sd, aw) in SHOPS:
    xc = (x0 + x1) / 2
    door = dec.add(300, 100, kind="plate", bg="#f4f1ea", lines=["당기세요"], fg="#c0221a", screws=False, dirt=0.1)
    posters = []
    if sg["text"] == "태평 철물":
        posters += [(dec.add(300, 200, kind="sticker", bg="#ffd21f", fg="#1a1a1a", text="24시 열쇠", tel="010-5550-0124"),
                     x0 + 0.45, 1.5, 0.3, 0.2),
                    (dec.add(1000, 140, kind="vinyl", lines=["열쇠 · 도장 · 공구 · 철물"], fg="#f2e9c9"), xc - 0.4, 2.15, 2.4, 0.3)]
    if sg["text"] == "꼬꼬 통닭":
        posters += [(dec.add(1000, 140, kind="vinyl", lines=["치킨 · 생맥주 · 포장 환영"], fg="#ffe9b0"), xc - 0.6, 2.15, 2.6, 0.32),
                    (dec.add(420, 600, kind="poster", head="오늘의 메뉴", lines=["후라이드 18,000", "양념 19,000", "반반 19,000", "배달 가능"],
                             head_bg="#b4291f"), x1 - 0.6, 1.15, 0.42, 0.6)]
    inner = inn.add(int(160 * (x1 - x0)), int(160 * ZO), kind="shop", **sp)
    bld.shopfront(M, P, x0, x1, glass_m=Mt["shopglass"], room_m=PL, floor_m=CO, inner=inner, inner_m=Mt["inner"],
                  door=0.62 if aw else 0.3, z_open=ZO, room_d=3.4, shut_m=SH, shut_down=sd, door_item=door,
                  decal_m=Mt["decal"], posters=posters)
    s = sign.add(int(380 * (x1 - x0 + 0.1)), 300, kind="sign", seed=int(xc * 10) % 97, **sg)
    bld.signbox(M, P, P["galv"], Mt["sign"], s, (xc, -0.42, 3.17), x1 - x0 + 0.1, 0.72, depth=0.42)
    if aw:
        top = dec.add(1000, 260, kind="awning", cols=list(aw), n=16, seed=5)
        val = dec.add(1000, 70, kind="awning", cols=list(aw), n=16, valance=True, seed=6)
        bld.awning(M, P, (top, val), Mt["decal2"], x0 + 0.05, x1 - 0.05, 2.72, -0.16, proj=1.15, drop=0.55, valance=0.2)
    if sd == 0.0:   # 닫힌 셔터 위 전단·스티커
        for (it, px, pz, pw, ph) in ((dec.add(400, 560, kind="poster", head="세탁 · 수선", lines=["와이셔츠 2,000원", "드라이 5,000원~",
                                                                                         "운동화 세탁", "02) 555-0118"], head_bg="#2f6ea5"),
                                       xc - 0.9, 1.35, 0.42, 0.59),
                                      (dec.add(300, 200, kind="sticker", bg="#e8452c", fg="#ffffff", text="24시 열쇠", tel="010-5550-0124"),
                                       xc + 0.6, 1.0, 0.18, 0.12),
                                      (dec.add(300, 200, kind="sticker", bg="#1f4fa0", fg="#ffffff", text="막힌 곳 뚫음", tel="010-5550-0188"),
                                       xc + 0.95, 0.7, 0.18, 0.12)):
            M.quad(Mt["decal"], (px, 0.002, pz), (1, 0, 0), (0, 0, 1), pw, ph, item=it)
# 철물점 바깥 진열: 양동이 더미 2개 + 빗자루 꽂은 플라스틱 상자
P["pred"] = bld.pm("PlasticRed", (0.5, 0.06, 0.04), 0.45, edge=(0.7, 0.3, 0.25), edge_amt=0.4, grime=0.45)
P["pblue"] = bld.pm("PlasticBlue", (0.04, 0.16, 0.42), 0.5, edge=(0.25, 0.35, 0.55), edge_amt=0.4, grime=0.5)
P["bristle"] = bld.pm("Bristle", (0.62, 0.48, 0.18), 0.85, grime=0.4, bump=0.6, scale=40.0)
P["stick"] = bld.pm("WoodStick", (0.42, 0.28, 0.14), 0.6, grime=0.3)
for (bx, by, m) in ((-6.85, -0.42, P["pred"]), (-3.55, -0.4, P["pblue"])):
    for k in range(3):     # 겹쳐 쌓은 양동이 (위로 갈수록 살짝 어긋남)
        M.cyl(m, (bx + k * 0.006, by, 0.005 + k * 0.06), (bx + k * 0.006, by, 0.32 + k * 0.06), 0.13, 16, r2=0.16)
    M.torus(P["galv"], (bx + 0.012, by, 0.44), (0, 0, 1), 0.16, 0.004, 16, 4)
cx, cy = -4.35, -0.42
M.box(P["pblue"], (cx, cy, 0.15), (0.52, 0.36, 0.3), 0.02, 2)
for k in range(5):
    sx, sy = cx - 0.18 + k * 0.09, cy + (0.05 if k % 2 else -0.05)
    top = (sx + 0.06 * (k - 2) / 2, sy, 1.35)
    M.cyl(P["stick"], (sx, sy, 0.1), top, 0.012, 8)
    M.box(P["bristle"], (top[0], sy, top[2] + 0.08), (0.24, 0.05, 0.17), 0.01, 1)
# 2층 보습학원 간판 + 유리 시트 글자
acad = sign.add(1400, 220, kind="sign", bg="#e4dfd1", fg="#2b5d9a", text="수학 영어 보습학원", tel="02) 555-0150", panels=False)
bld.signbox(M, P, P["alu"], Mt["sign"], acad, (-1.875 + 0.3, -0.1, G + 0.42), 4.6, 0.62, depth=0.1)
for i, (f, b, w, h, z) in enumerate(uw):
    frame = "alu" if f == 0 else ("pvc" if i % 2 else "bronze")
    bld.fwin(M, P, W, b, z, w, h, frame=frame, sashes=2, interior=inn.add(220 * (w + 0.1), 220 * (h + 0.1), kind="interior", v=i * 3 + 1, office=(f == 0)),
             interior_m=Mt["inner"], glass_m=Mt["glass"], screen_m=Mt["screen"] if f else None, slide=0.2 * (i % 3))
    if f == 0:
        txt = ["수학", "영어", "내신", "특강"][i % 4]
        M.quad(Mt["decal"], (b, 0.14, z + h / 2 + 0.1), (1, 0, 0), (0, 0, 1), w * 0.7, h * 0.34,
               item=dec.add(600, 300, kind="vinyl", lines=[txt], fg="#2b5d9a"))
for (u0, u1, v0, v1) in lh:
    bld.window(M, P, None, (-W / 2, D, 0), (0, -1, 0), (0, 0, 1), u0, u1, v0, v1, frame="pvc", sashes=2,
               interior=inn.add(200, 180, kind="interior", v=30 + int(v0)), interior_m=Mt["inner"], glass_m=Mt["glass"])
# 때 덮개, 실외기, 선홈통, CCTV, 주소판
bld.grime_wall(M, Mt["grime"], gri.add(1024, 1024, **bld.grime_spec(W, HT, holes, (), 0.8, 7)), W, HT, holes)
bld.ac_unit(M, P, (-5.625 + 0.45, 0, G + FH + 0.12), pipe_up=0.5, pipe_side=0.4)
bld.ac_unit(M, P, (1.875 + 0.5, 0, G + FH + 0.12), pipe_up=0.5, pipe_side=0.4)
bld.ac_unit(M, P, (-W / 2, 4.5, G + 0.35), rz=-math.pi / 2, pipe_up=0.4, pipe_side=0.3)
bld.downpipe(M, P, W / 2 - 0.12, -0.08, HT)
bld.cctv(M, P, (W / 2 - 0.3, 0, G + 0.35), rz=0.5)
addr = sign.add(900, 300, kind="plate_addr", road="은행길", en="Eunhaeng-gil", num="31")
bld.address_plate(M, P, Mt["sign"], addr, -W / 2, 2.1, y=0.6, w=0.42, h=0.14, normal=(-1, 0, 0))
# 전선: 왼쪽 옆벽 인입구 -> 애자 -> 정면을 가로질러 처지며 -> 학원 간판·CCTV 로 내려감 (고정점마다 애자, 벽 따라 클램프)
WZ, WY = G + FH - 0.35, -0.17


def sag(a, b, s=0.1, n=8):
    a, b = Vector(a), Vector(b)
    return [tuple(a.lerp(b, k / n) - Vector((0, 0, s * 4 * (k / n) * (1 - k / n)))) for k in range(n + 1)]


def hook(p, nx, ny):
    """애자 (흰 자기 실패) + 벽 브래킷. nx,ny = 벽 바깥 방향."""
    x, y, z = p
    L = abs(nx * (x + W / 2)) if nx else abs(y)
    M.box(P["galv"], (x - nx * L / 2, y - ny * L / 2, z), (L if nx else 0.02, L if ny else 0.02, 0.02), 0.003)
    M.cyl(P["ivory"], (x, y, z - 0.025), (x, y, z + 0.025), 0.018, 10)


def drop(x0, x1, z1, y1):
    """애자에서 벽 따라 내려가는 전선 + 클램프."""
    pts = [(x0, WY, WZ), (x0, -0.04, WZ - 0.2), (x0, -0.025, z1 + 0.3), (x1, y1, z1)]
    M.path(P["black"], pts, 0.007, 6, joint=False)
    for z in (WZ - 0.6, (WZ + z1) / 2, z1 + 0.45):
        M.box(P["galv"], (x0, -0.017, z), (0.03, 0.034, 0.015), 0.002)


M.cyl(P["black"], (-W / 2 + 0.02, 2.2, WZ + 0.2), (-W / 2 - 0.06, 2.2, WZ + 0.2), 0.016, 8)   # 인입 슬리브
side = [(-W / 2 - 0.06, 2.2, WZ + 0.2), (-W / 2 - 0.1, 1.5, WZ), (-W / 2 - 0.12, 0.03, WZ)]
front = [(-W / 2 + 0.3, WY, WZ), (-3.9, WY, WZ), (0.45, WY, WZ), (3.8, WY, WZ), (7.0, WY, WZ)]
for p in side[1:]:
    hook(p, -1, 0)
for p in front:
    hook(p, 0, -1)
chain = side + front
for a, b in zip(chain, chain[1:]):
    M.path(P["black"], sag(a, b, 0.03 if (Vector(b) - Vector(a)).length < 1.0 else 0.1), 0.007, 6, joint=False)
drop(0.45, 0.5, G + 0.42 + 0.32, -0.05)         # 학원 간판 윗면 안으로
drop(7.0, 7.18, G + 0.35 + 0.05, -0.025)        # CCTV 벽판 안으로

notes = ("1층 상가 3칸 + 2층 보습학원 + 3층 주거 (회색 타일). 원점 = 도로 쪽 정면 벽 아래 중앙, 정면 = Unity +Z, 깊이 9m. "
         "폭 15m, 높이 9.8m (1층 3.6m + 2.75m x2 + 파라펫 0.7m). 점포: 태평 철물(x -7.2..-2.65, 셔터 반쯤), 꼬꼬 통닭(x -2.35..2.55, 차양), "
         "은하 세탁소(x 2.85..7.2, 셔터 내림). 셔터 = M_Tile_Buildings_Shutter (월드 UV 2m). 간판 M_BuildingShopRow_Sign, "
         "유리 시트·스티커·차양 M_BuildingShopRow_Decal(알파 클립, 차양은 DecalDS 양면).")
socks = [("DoorChicken", (0.69, -0.6, 0), (0, 0, 0)), ("DoorHardware", (-5.83, -0.6, 0), (0, 0, 0))]
notes += (" 때 덮개(M_BuildingShopRow_Grime)는 개구부를 잘라낸 띠 메시로 벽에서 12mm 앞에 있다. "
          "배치: 뒷벽과 창 없는 옆벽은 단순 미장면이므로 이웃 건물에 붙이거나 골목 안쪽으로 돌려 가릴 것.")
ob, paths = bld.finish(A, M, atlases=[sign, dec, inn, gri], bake_size=2048, notes=notes, sockets=socks, ao=0.3,
                       samples=32, fp=((-4.0, -8.5, 1.55), (0.5, 0.0, 3.0), 24))
print("PREVIEWS", paths)

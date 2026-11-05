"""BuildingMarketGate: '큰길시장' 전통시장 입구 게이트 (사각 강관 기둥 2개 + 양면 플렉스 간판 상자).
프로토타입 27233~27242 그룹 V (매장 외부 좌표 -17.2, 0, 6): 기둥 0.32x5.4x0.32 (x=±2.6),
간판 상자 6x1.1x0.34 (중심 높이 4.9, 아래 통과 높이 4.35m), 간판 면 5.8x1.0 (#a42a1e 바탕, #f5e7c6 글자, 발광)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d

A = "BuildingMarketGate"
k3d.reset()
P = bld.palette()
# 기둥: 짙은 회청색 도장, 모서리 벗겨짐 + 녹 점 + 빗물 줄
P["post"] = bld.pm("GateSteel", (0.06, 0.068, 0.075), 0.55, 0.3, edge=(0.36, 0.32, 0.27), edge_amt=0.6, grime=0.5,
                   streak=0.8, spots=(0.3, 0.12, 0.04), spot_amt=0.7, bump=0.3, grime_col=(0.22, 0.09, 0.035))
# 간판 상자 몸통: 흰 도장 갈바 판 (때·빗물)
P["boxp"] = bld.pm("GateBox", (0.62, 0.6, 0.56), 0.6, 0.2, edge=(0.4, 0.38, 0.35), edge_amt=0.6, grime=0.6,
                   streak=0.8, bump=0.1)

sign = bld.Atlas(A, "Sign", (2048, 512))
dec = bld.Atlas(A, "Decal", (1024, 512), "RGBA")
Mt = bld.mats(A, sign, dec, sign_emit=0.45)
face = sign.add(2040, 352, kind="sign", bg="#a42a1e", fg="#f5e7c6", text="큰길시장", sub="전통시장",
                tel="큰길시장 상인회", band="#efe1bf", panels=False, fade=0.28, dirt=0.35, seed=21)

M = bld.Mesh()
ZC, BW, BD, BH = 4.9, 6.0, 0.34, 1.1          # 간판 상자 중심 높이 / 폭 / 두께 / 높이
ZB = ZC - BH / 2                              # 상자 아랫면 4.35
for sx in (-1, 1):
    x = sx * 2.6
    M.box(P["conc"], (x, 0, 0.04), (0.62, 0.62, 0.08), 0.02)                     # 콘크리트 받침
    M.box(P["post"], (x, 0, 0.09), (0.46, 0.46, 0.02), 0.004)                   # 베이스 플레이트
    M.box(P["post"], (x, 0, (0.10 + 5.4) / 2), (0.32, 0.32, 5.3), 0.012, 2)     # 사각 강관
    for s in (-1, 1):                                                           # 용접 비드
        M.box(P["post"], (x, s * 0.163, 0.107), (0.34, 0.014, 0.016), 0.006)
        M.box(P["post"], (x + s * 0.163, 0, 0.107), (0.014, 0.31, 0.016), 0.006)
    for bx in (-0.18, 0.18):                                                    # 앵커 볼트 4개
        for by in (-0.18, 0.18):
            M.cyl(P["galv"], (x + bx, by, 0.100), (x + bx, by, 0.104), 0.028, 12)
            M.cyl(P["rust"], (x + bx, by, 0.104), (x + bx, by, 0.124), 0.022, 6)
            M.cyl(P["rust"], (x + bx, by, 0.124), (x + bx, by, 0.15), 0.011, 8)
    M.box(P["post"], (x, 0, ZB - 0.006), (0.42, 0.42, 0.012), 0.003)            # 상자 밑 플랜지
# 간판 상자 + 앞뒤 알루미늄 테 + 리벳 + 양면 간판
M.box(P["boxp"], (0, 0, ZC), (BW, BD, BH), 0.015, 2)
M.box(P["galv"], (0, 0, ZC + BH / 2 + 0.01), (BW + 0.08, BD + 0.08, 0.02), 0.004)   # 빗물막이 덮개
for sy in (-1, 1):
    yr = sy * (BD / 2 + 0.0125)
    for zz in (ZC + 0.525, ZC - 0.525):
        M.box(P["alu"], (0, yr, zz), (BW, 0.025, 0.05), 0.004)
        for k in range(12):
            rx = -2.75 + k * 0.5
            M.cyl(P["sus"], (rx, sy * (BD / 2 + 0.025), zz), (rx, sy * (BD / 2 + 0.029), zz), 0.007, 8)
    for xx in (-2.95, 2.95):
        M.box(P["alu"], (xx, yr, ZC), (0.1, 0.025, 1.0), 0.004)
    # 면은 상자 표면에서 12mm 띄움 (테 25mm 안쪽으로 들어감). 뒤(+Y) 면은 right=-X 로 읽힌다
    M.quad(Mt["sign"], (0, sy * (BD / 2 + 0.012), ZC), (-sy, 0, 0), (0, 0, 1), 5.8, 1.0, item=face)
# 아랫면: 이음 띠 + 물빠짐 고무 구멍 3개
M.box(P["galv"], (0, 0, ZB - 0.004), (BW - 0.1, 0.05, 0.008), 0.002)
for dx in (-1.5, 0.0, 1.5):
    M.cyl(P["black"], (dx, 0.09, ZB), (dx, 0.09, ZB - 0.006), 0.014, 10)
# 전기: 오른쪽 기둥 안쪽 면 분전함 + 전선관 (땅 -> 함 -> 간판)
xi = 2.6 - 0.16
M.box(P["pvc"], (xi - 0.04, -0.03, 1.3), (0.08, 0.16, 0.22), 0.01)
M.box(P["black"], (xi - 0.081, -0.03, 1.33), (0.002, 0.08, 0.05), 0.001)
for z0, z1 in ((0.10, 1.19), (1.41, ZB)):
    M.cyl(P["pipe"], (xi - 0.016, -0.03, z0), (xi - 0.016, -0.03, z1), 0.014, 8)
for zc in (0.6, 2.0, 2.8, 3.6):
    M.box(P["galv"], (xi - 0.017, -0.03, zc), (0.034, 0.042, 0.02), 0.002)
# 기둥 스티커·전단 (눈높이)
st = dec.add(300, 200, kind="sticker", bg="#1f4fa0", fg="#ffffff", text="온누리상품권", tel="사용 가능 시장")
pl = dec.add(420, 140, kind="plate", bg="#f4f1ea", lines=["광고물 부착 금지"], fg="#c0221a", screws=True, dirt=0.25)
fl = dec.add(300, 420, kind="poster", head="점포 임대", lines=["시장 안 1층", "10평 · 즉시 입주", "010-5550-0172"],
             head_bg="#2f6ea5", fade=0.45, dirt=0.3)
M.quad(Mt["decal"], (-2.6, -0.165, 1.5), (1, 0, 0), (0, 0, 1), 0.21, 0.14, item=st)
M.quad(Mt["decal"], (2.6, -0.165, 1.75), (1, 0, 0), (0, 0, 1), 0.27, 0.09, item=pl)
M.quad(Mt["decal"], (2.62, -0.165, 1.3), (1, 0, 0), (0, 0, 1), 0.2, 0.28, item=fl)

notes = ("전통시장 입구 게이트 '큰길시장'. 원점 = 두 기둥 사이 바닥 중앙, 정면 = Unity +Z (간판은 앞뒤 양면). "
         "기둥 사각 강관 0.32m (x=±2.6, 높이 5.4m) + 콘크리트 받침·베이스 플레이트·앵커 볼트 4개, 간판 상자 6x1.1x0.34m "
         "(중심 높이 4.9m, 아래 통과 높이 4.35m), 간판 면 5.8x1.0m = M_BuildingMarketGate_Sign (발광 0.45, 정면·뒷면 같은 그림). "
         "오른쪽 기둥 안쪽에 분전함·전선관, 기둥에 온누리상품권 스티커·광고물 부착 금지판·점포 임대 전단. "
         "프로토타입 위치: 매장 외부 좌표 (-17.2, 0, 6), 간판이 +Z 를 본다. 정류장 '시장입구' 도착 랜드마크. "
         "소켓: BuildingMarketGate_Socket_SignLook (간판 앞면 중심, 시선 타깃).")
socks = [("SignLook", (0, -0.2, ZC), (0, 0, 0))]
ob, paths = bld.finish(A, M, atlases=[sign, dec], bake_size=2048, notes=notes, sockets=socks, ao=0.2, samples=32,
                       fp=((-2.0, -9.0, 1.55), (0.0, 0.0, 3.5), 35))
print("PREVIEWS", paths)

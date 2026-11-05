"""BusShelter: 가로변 버스 승차대 (bench.glb 대체).
프로토타입(WS): 기둥 4개 2.2 m 간격(폭 6.6 m), 높이 2.65 m, 지붕 깊이 2.35 m + 처마, 뒷유리 6.6 x 2.0 m,
한쪽 옆유리, 광고 라이트박스 1.3 x 2.3 x 0.2 m(양면 포스터), 벤치 2.6 m(앉는 높이 0.46), 이름판 2.4 x 0.36 m.
정면(거리 쪽) = -Y, 원점 = 바닥 중앙. 오른쪽(+X) 끝 = 옆유리, 왼쪽(-X) 끝 = 광고 라이트박스."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import _bs as B
from _bs import k3d
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Street"))
import _street as S                        # 점형블록 = 거리 그룹과 같은 M_Tile_Street_TactileDot

A = "BusShelter"
k3d.reset()
tdir, lay = B.textures(A)
random.seed(14208)

# ---------------------------------------------------------------- 머티리얼
paint = B.m_paint("P_SH_Paint", (0.045, 0.05, 0.056), rough=0.42, wear=0.4, grime=0.6, rust=0.35, fade=0.45)
alu = B.m_paint("P_SH_Alu", (0.56, 0.57, 0.58), rough=0.36, wear=0.2, grime=0.65, rust=0.06, fade=0.15,
                bare=(0.72, 0.72, 0.73))
steel = B.m_metal("P_SH_Steel", (0.58, 0.58, 0.59), rough=0.32, grime=0.5, brushed=False)
inox = B.m_metal("P_SH_Inox", (0.62, 0.62, 0.62), rough=0.28, grime=0.45, brushed=True)
rubber = B.m_rubber("P_SH_Rubber")
yel = B.m_plastic("P_SH_BellBox", (0.75, 0.52, 0.02), rough=0.45, grime=0.5, fade=0.4)
red = B.m_plastic("P_SH_BellBtn", (0.6, 0.03, 0.02), rough=0.3, grime=0.3)
wood = B.m_wood("P_SH_Wood", tint=(0.55, 0.36, 0.2), grime=0.55, grey=0.4)
binpaint = B.m_paint("P_SH_BinTop", (0.05, 0.12, 0.09), rough=0.45, wear=0.45, grime=0.6, rust=0.3, fade=0.5)
glass = B.m_glass("M_Glass_BusShelter_Glass", os.path.join(tdir, "T_BusShelter_Glass.png"))
roofm = B.m_glass("M_Glass_BusShelter_Roof", os.path.join(tdir, "T_BusShelter_Roof.png"), rough=0.12)
namem = B.m_image("M_BusShelter_NameSign", os.path.join(tdir, "T_BusShelter_NameSign.png"), rough=0.3, emit=0.35)
adm = B.m_image("M_BusShelter_AdPoster", os.path.join(tdir, "T_BusShelter_AdPoster.png"), rough=0.2, emit=0.9)
decm = B.m_image("M_BusShelter_Decals", os.path.join(tdir, "T_BusShelter_Decals.png"), rough=0.6, clip=0.5,
                 double=True)              # 유리 스티커가 뒤에서도 보이게 (뒷면은 좌우 반전)
leafm = B.m_image("M_BusShelter_Leaves", os.path.join(tdir, "T_BusShelter_Decals.png"), rough=0.7, clip=0.5,
                  double=True)
tact = S.tile_tactile("dot")

# ---------------------------------------------------------------- 치수
PY = 1.0                                   # 기둥 줄 (뒷벽)
XS = (-3.3, -1.1, 1.1, 3.3)                # 기둥 X
YB, YF = 1.23, -1.72                       # 보 뒤끝 / 앞끝
SL = 0.05                                  # 지붕 기울기 (앞이 높고 뒤 물받이로 흐름)


def zt(y):
    """지붕판 아랫면 높이."""
    return 2.62 + (1.2 - y) * SL


def bb(y):
    """보 아랫면 높이 (기둥 쪽이 깊은 테이퍼 보)."""
    if y >= 0.85:
        t = (y - 0.85) / (YB - 0.85)
        return zt(y) - (0.25 + (0.16 - 0.25) * t)
    t = (0.85 - y) / (0.85 - YF)
    return zt(y) - (0.25 + (0.07 - 0.25) * t)


F = []                                     # 프레임 (굽기 2048)
# 기둥 100x100 각관 + 베이스판 + 앵커 너트
for x in XS:
    F.append(B.box("f", (0.1, 0.1, zt(PY) - 0.004), (x, PY, (zt(PY) - 0.004) / 2), paint, bevel=0.008))
    F.append(B.box("f", (0.24, 0.24, 0.014), (x, PY, 0.007), paint, bevel=0.003))
    for sx in (-1, 1):
        for sy in (-1, 1):
            F.append(B.cyl("f", 0.014, 0.012, (x + sx * 0.088, PY + sy * 0.088, 0.014), steel, n=6, bevel=0.0015))
            F.append(B.cyl("f", 0.007, 0.03, (x + sx * 0.088, PY + sy * 0.088, 0.014), steel, n=8, bevel=0.001))
    F.append(B.box("f", (0.104, 0.104, 0.03), (x, PY, 0.95), paint, bevel=0.003))   # 기둥 이음 띠
# 외팔보 (테이퍼) + 무릎 보강판
for x in XS:
    pts = [(YB + 0.03, zt(YB) - 0.002), (YB + 0.03, bb(YB)), (0.85, bb(0.85)), (YF - 0.004, bb(YF)),
           (YF - 0.004, zt(YF) - 0.002)]                            # 끝은 처마·물받이에 살짝 묻힘
    F.append(B.prism("f", pts, 0.06, paint, axis='X', loc=(x, 0, 0), bevel=0.004))
    if x != XS[0]:                                                  # 왼쪽 끝은 라이트박스가 받침
        g = [(0.95, bb(0.95) + 0.01), (0.95, bb(0.95) - 0.4), (0.55, bb(0.55) + 0.01)]
        F.append(B.prism("f", g, 0.016, paint, axis='X', loc=(x, 0, 0), bevel=0.003))
    for y in (0.3, -0.6, -1.4):                                     # 보 옆 볼트
        for s in (-1, 1):
            F.append(B.cyl("f", 0.008, 0.006, (x + s * 0.03, y, (zt(y) + bb(y)) / 2), steel, n=6, bevel=0.001,
                           rot=(0, s * math.pi / 2, 0)))
# 중도리 (원형관)
for y in (0.62, -0.25, -1.1):
    F.append(B.cyl("f", 0.024, 6.96, (-3.48, y, zt(y) - 0.026), paint, n=16, bevel=0.002, rot=(0, math.pi / 2, 0)))
# 지붕 옆 마감 채널 (기울기 따라)
ym = (YB + YF) / 2
for s in (-1, 1):
    F.append(B.box("f", (0.035, YB - YF + 0.02, 0.05), (s * 3.535, ym, zt(ym) + 0.006), alu, bevel=0.004,
                   rot=(-SL, 0, 0)))
# 앞 처마 박스 + 물끊기 + 윗 캡
F.append(B.box("f", (7.1, 0.1, 0.2), (0, -1.77, zt(YF) - 0.06), alu, bevel=0.006))
F.append(B.box("f", (7.1, 0.022, 0.02), (0, -1.825, zt(YF) - 0.15), alu, bevel=0.003))
F.append(B.box("f", (7.12, 0.12, 0.012), (0, -1.77, zt(YF) + 0.046), alu, bevel=0.003))
# 이름판 함체 (처마 아래, 앞뒤 그림) + 베젤
NZ, NY = 2.395, -1.77
F.append(B.box("f", (2.52, 0.1, 0.43), (0, NY, NZ + 0.005), alu, bevel=0.006))
for s in (-1, 1):
    y = NY + s * 0.052
    F.append(B.box("f", (2.52, 0.012, 0.03), (0, y, NZ + 0.195), alu, bevel=0.003))
    F.append(B.box("f", (2.52, 0.012, 0.03), (0, y, NZ - 0.195), alu, bevel=0.003))
    for x in (-1.245, 1.245):
        F.append(B.box("f", (0.03, 0.011, 0.42), (x, y, NZ), alu, bevel=0.003))
# 뒤 물받이 + 말린 테 + 선홈통 (오른쪽 끝 기둥 뒤)
F.append(B.box("f", (7.1, 0.12, 0.1), (0, 1.29, 2.575), alu, bevel=0.006))
F.append(B.cyl("f", 0.012, 7.1, (-3.55, 1.352, 2.622), alu, n=10, bevel=0.0, rot=(0, math.pi / 2, 0)))
F.append(B.pipe("f", B.bend([(3.15, 1.29, 2.53), (3.15, 1.29, 2.32), (3.3, 1.11, 2.12), (3.3, 1.11, 0.16),
                             (3.3, 1.26, 0.05)], 0.06), 0.035, alu, res=16))
for z in (0.55, 1.35, 1.95):
    F.append(B.box("f", (0.1, 0.07, 0.025), (3.3, 1.08, z), steel, bevel=0.002))
# 뒷유리 틀 (위·아래 레일 + 가스켓 + 나사)
for xa, xb in zip(XS, XS[1:]):
    xm, L = (xa + xb) / 2, xb - xa - 0.1
    F.append(B.box("f", (L + 0.004, 0.05, 0.06), (xm, PY, 2.31), paint, bevel=0.005))     # 기둥에 2 mm 묻힘 (면 겹침 방지)
    F.append(B.box("f", (L + 0.004, 0.06, 0.07), (xm, PY, 0.185), paint, bevel=0.005))
    for s in (-1, 1):
        F.append(B.box("f", (L + 0.004, 0.006, 0.01), (xm, PY + s * 0.006, 2.276), rubber, bevel=0.001))
        F.append(B.box("f", (L + 0.004, 0.006, 0.01), (xm, PY + s * 0.006, 0.224), rubber, bevel=0.001))
        for x in (xa + 0.054, xb - 0.054):
            F.append(B.box("f", (0.012, 0.006, 2.04), (x, PY + s * 0.006, 1.25), rubber, bevel=0.001))
    for x in (xa + 0.3, xm, xb - 0.3):
        F.append(B.cyl("f", 0.006, 0.004, (x, PY - 0.03, 0.185), steel, n=8, bevel=0.0008, rot=(math.pi / 2, 0, 0)))
# 옆유리 틀 (오른쪽 끝): 앞 기둥(멀리언) + 레일
SX, SY0, SY1 = XS[-1], PY - 0.05, -0.85
F.append(B.box("f", (0.06, 0.06, bb(SY1 - 0.03) + 0.01), (SX, SY1 - 0.03, (bb(SY1 - 0.03) + 0.01) / 2), paint,
               bevel=0.005))
F.append(B.box("f", (0.16, 0.16, 0.012), (SX, SY1 - 0.03, 0.006), paint, bevel=0.003))
for z, h in ((2.31, 0.06), (0.185, 0.07)):
    F.append(B.box("f", (0.05, SY0 - SY1 + 0.004, h), (SX, (SY0 + SY1) / 2, z), paint, bevel=0.005))
# 광고 라이트박스 (왼쪽 끝, 승차대 안쪽 +X 면 = 버거대왕 / 바깥 -X 면 = 버스앱 공익광고)
LX, LY, LZ, LL, LH = XS[0], 0.27, 1.22, 1.3, 2.3
F.append(B.box("f", (0.17, LL, LH), (LX, LY, LZ), alu, bevel=0.02, segs=3))
for s in (-1, 1):
    x = LX + s * 0.0915
    F.append(B.box("f", (0.015, LL, 0.13), (x, LY, LZ + LH / 2 - 0.065), alu, bevel=0.004))
    F.append(B.box("f", (0.015, LL, 0.17), (x, LY, LZ - LH / 2 + 0.085), alu, bevel=0.004))
    for y in (-1, 1):
        F.append(B.box("f", (0.014, 0.08, LH), (x - s * 0.0005, LY + y * (LL / 2 - 0.04), LZ), alu, bevel=0.004))
    for y in (-0.5, 0.5):                                           # 여닫이 자물쇠
        F.append(B.cyl("f", 0.009, 0.006, (x + s * 0.0075, LY + y, LZ - LH / 2 + 0.085), steel, n=12, bevel=0.001,
                       rot=(0, s * math.pi / 2, 0)))
for y in (-0.5, 0.5):                                               # 받침 다리 + 위 브래킷
    F.append(B.box("f", (0.12, 0.1, 0.075), (LX, LY + y, 0.0375), paint, bevel=0.004))
    F.append(B.box("f", (0.2, 0.16, 0.012), (LX, LY + y, 0.006), paint, bevel=0.003))
    yy = LY + y * 0.8
    F.append(B.box("f", (0.04, 0.06, bb(yy) - (LZ + LH / 2) + 0.02), (LX, yy, (bb(yy) + LZ + LH / 2) / 2), paint,
                   bevel=0.003))
# 비상벨 함 (가운데 오른쪽 기둥 앞면)
F.append(B.box("f", (0.09, 0.05, 0.16), (XS[2], PY - 0.075, 1.28), yel, bevel=0.006))
F.append(B.cyl("f", 0.022, 0.014, (XS[2], PY - 0.1, 1.25), red, n=20, bevel=0.003, rot=(math.pi / 2, 0, 0)))
F.append(B.box("f", (0.05, 0.004, 0.02), (XS[2], PY - 0.101, 1.325), rubber, bevel=0.001))   # 스피커 구멍
frame = B.join(F, A + "_Frame")
k3d.set_origin(frame, (0, 0, 0))
k3d.uv_world(frame, 1.0)  # 합친 메시의 빈(0) UV 면 -> 굽기 탄젠트가 깨져 노멀맵 얼룩. 전부 유효 UV 로

# ---------------------------------------------------------------- 벤치 (나무 살 + 주물 받침 + 팔걸이)
BY = 0.52
Bn = []
for x in (-1.2, -0.4, 0.4, 1.2):
    Bn.append(B.box("b", (0.05, 0.06, 0.4), (x, BY + 0.02, 0.2), paint, bevel=0.006))
    Bn.append(B.box("b", (0.1, 0.34, 0.012), (x, BY + 0.02, 0.006), paint, bevel=0.003))
    for y in (-0.12, 0.16):
        Bn.append(B.cyl("b", 0.011, 0.01, (x, BY + y, 0.012), steel, n=6, bevel=0.001))
    sb = [(BY - 0.2, 0.424), (BY + 0.22, 0.424), (BY + 0.22, 0.395), (BY + 0.05, 0.33), (BY - 0.01, 0.33),
          (BY - 0.2, 0.395)]
    Bn.append(B.prism("b", sb, 0.04, paint, axis='X', loc=(x, 0, 0), bevel=0.004))
    Bn.append(B.box("b", (0.04, 0.035, 0.46), (x, BY + 0.246, 0.64), paint, bevel=0.005, rot=(-0.2, 0, 0)))
for i in range(5):                                                  # 앉는 살 5
    s = B.box("b", (2.62, 0.072, 0.03), (0, BY - 0.168 + i * 0.084, 0.435), wood, bevel=0.005, segs=3)
    B.uv_along(s, 0, 0.6)
    Bn.append(s)
d, n = (0.0, 0.199, 0.98), (0.0, -0.98, 0.199)                      # 등받이 방향 / 앞쪽
for t in (0.23, 0.33, 0.43):                                         # 등받이 살 3
    c = (0, BY + 0.2 + d[1] * t + n[1] * 0.027, 0.415 + d[2] * t + n[2] * 0.027)
    s = B.box("b", (2.62, 0.022, 0.085), c, wood, bevel=0.005, segs=3, rot=(-0.2, 0, 0))
    B.uv_along(s, 0, 0.6)
    Bn.append(s)
for x in (-0.4, 0.4):                                                # 눕기 방지 팔걸이 (스테인리스)
    Bn.append(B.pipe("b", B.bend([(x, BY - 0.15, 0.44), (x, BY - 0.15, 0.64), (x, BY + 0.19, 0.66)], 0.06), 0.016,
                     inox, res=16))
    Bn.append(B.cyl("b", 0.026, 0.008, (x, BY - 0.15, 0.448), inox, n=16, bevel=0.002))
for x in (-1.31, 1.31):                                              # 살 끝 마구리 캡
    for i in range(5):
        Bn.append(B.box("b", (0.006, 0.074, 0.032), (x, BY - 0.168 + i * 0.084, 0.435), rubber, bevel=0.001))
bench = B.join(Bn, A + "_Bench")
k3d.set_origin(bench, (0, BY, 0))
B.uv_along(bench, 0, 0.6)                                          # 나뭇결 = X, 철물도 유효 UV

# ---------------------------------------------------------------- 쓰레기통 (2칸, 승차대 오른쪽 밖)
BX, BYn = 3.88, 0.78
Tn = [B.box("t", (0.64, 0.36, 0.78), (BX, BYn, 0.45), inox, bevel=0.012, segs=3),
      B.box("t", (0.66, 0.38, 0.07), (BX, BYn, 0.87), binpaint, bevel=0.02, segs=3),
      B.box("t", (0.6, 0.32, 0.065), (BX, BYn, 0.0325), rubber, bevel=0.006),
      B.box("t", (0.008, 0.004, 0.62), (BX, BYn - 0.181, 0.42), rubber, bevel=0.001)]
for s in (-1, 1):
    Tn.append(B.box("t", (0.24, 0.02, 0.09), (BX + s * 0.16, BYn - 0.18, 0.73), rubber, bevel=0.006))   # 투입구
    Tn.append(B.box("t", (0.2, 0.004, 0.012), (BX + s * 0.16, BYn - 0.191, 0.71), inox, bevel=0.001))
    Tn.append(B.box("t", (0.3, 0.004, 0.004), (BX + s * 0.16, BYn - 0.181, 0.66), rubber, bevel=0.0))  # 문 틈
    Tn.append(B.box("t", (0.004, 0.004, 0.6), (BX + s * 0.31, BYn - 0.181, 0.37), rubber, bevel=0.0))
    Tn.append(B.cyl("t", 0.01, 0.008, (BX + s * 0.27, BYn - 0.18, 0.6), steel, n=12, bevel=0.001,
                    rot=(math.pi / 2, 0, 0)))
binobj = B.join(Tn, A + "_Bin")
k3d.set_origin(binobj, (BX, BYn, 0))
k3d.uv_world(binobj, 1.0)

# ---------------------------------------------------------------- 유리·지붕·그림 면 (굽지 않음)
G = []
for xa, xb in zip(XS, XS[1:]):
    G.append(B.quad("g", xb - xa - 0.1, 2.06, glass, ((xa + xb) / 2, PY, 1.25)))
G.append(B.quad("g", SY0 - SY1, 2.06, glass, (SX, (SY0 + SY1) / 2, 1.25), (0, 0, math.pi / 2)))
for s in (-1, 1):                                                   # 라이트박스 아크릴
    G.append(B.quad("g", 1.16, 2.02, glass, (LX + s * 0.094, LY, 1.25), (0, 0, s * math.pi / 2)))
glassobj = B.join(G, A + "_Glass")
k3d.uv_world(glassobj, 2.5)

bm = bmesh.new()                                                    # 폴리카보네이트 지붕판
vs = [bm.verts.new(v) for v in ((-3.52, YB - 0.01, zt(YB - 0.01)), (3.52, YB - 0.01, zt(YB - 0.01)),
                                (3.52, YF - 0.02, zt(YF - 0.02)), (-3.52, YF - 0.02, zt(YF - 0.02)))]
bm.faces.new(vs)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
roof = B._obj(A + "_Roof", bm, roofm)
if roof.data.polygons[0].normal.z < 0:
    roof.data.flip_normals()
k3d.uv_world(roof, 2.5)

ny = NY - 0.0515
Q = [B.quad("n", 2.4, 0.36, namem, (0, ny, NZ)), B.quad("n", 2.4, 0.36, namem, (0, NY + 0.0515, NZ), (0, 0, math.pi))]
for s, uv in ((1, (0, 0, 0.5, 1)), (-1, (0.5, 0, 1, 1))):          # +X 안쪽 = 버거 / -X 바깥 = 앱 광고
    Q.append(B.quad("n", 1.14, 2.0, adm, (LX + s * 0.0862, LY, 1.25), (0, 0, s * math.pi / 2), uv))
faces = B.join(Q, A + "_Signs")

tl = B.box("tt", (7.2, 0.3, 0.003), (0, -1.95, 0.0015), tact, bevel=0.001, segs=1)  # 점형블록 (보도 연석 쪽, 3 mm)
k3d.apply_all(tl)
tl.name = A + "_Tactile"
k3d.uv_world(tl, S.TILE_TACTILE)          # 0.6 m 타일 = 300 mm 블록 2x2, y -2.1~-1.8 이 블록 경계

# ---------------------------------------------------------------- 데칼

def dq(key, loc, rot=(0, 0, 0), w=None):
    return B.decal("l", lay, key, decm, loc, rot, w)


L = [dq("frit", ((xa + xb) / 2, PY - 0.003, 1.45)) for xa, xb in zip(XS, XS[1:])]
L.append(dq("frit", (SX - 0.003, (SY0 + SY1) / 2, 1.45), (0, 0, -math.pi / 2), w=1.7))
L += [dq("nosmoke", (SX + 0.003, 0.15, 1.5), (0, 0, math.pi / 2)),
      dq("bell", (XS[2] + 0.15, PY - 0.004, 1.48)),
      dq("manage", (XS[1], PY - 0.0515, 1.75), w=0.09),
      dq("adinfo", (LX + 0.1015, LY, 0.155), (0, 0, math.pi / 2)),
      dq("flyer", (-2.55, PY - 0.004, 1.42)),
      dq("tape", (-2.18, PY - 0.0045, 1.62), w=0.12),
      dq("graffiti", (0.75, PY - 0.004, 1.02)),
      dq("tape", (XS[1], PY - 0.0515, 0.75), w=0.08)]
t = 0.33                                                            # 기증 명판 (가운데 등받이 살)
c = (0.0, BY + 0.2 + d[1] * t + n[1] * 0.0393, 0.415 + d[2] * t + n[2] * 0.0393)
L.append(B.decal("l", lay, "donor", decm, c, (-0.2, 0, 0)))
decals = B.join(L, A + "_Decals")
Lb = [B.decal("l", lay, "bin_general", decm, (BX - 0.16, BYn - 0.1815, 0.57), w=0.2),
      B.decal("l", lay, "bin_recycle", decm, (BX + 0.16, BYn - 0.1815, 0.57), w=0.2),
      B.decal("l", lay, "dumping", decm, (BX + 0.3215, BYn, 0.5), (0, 0, math.pi / 2), w=0.2)]
bindec = B.join(Lb, A + "_Bin_Decals")
Lv = []
for i in range(9):                                                  # 은행잎 (지붕판 위, 뒤쪽 낮은 곳에 고임)
    y = random.uniform(0.75, 1.15) if i < 6 else random.uniform(-1.2, 0.5)
    x = random.uniform(-3.3, 3.3)
    Lv.append(B.decal("l", lay, f"leaf{i % 4}", leafm, (x, y, zt(y) + 0.004),
                      (-math.pi / 2 - SL, 0, random.uniform(0, math.tau))))
leaves = B.join(Lv, A + "_Leaves")
k3d.select([leaves])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # 첫 잎의 회전이 남으면 bounds 가 부풀어짐

# ---------------------------------------------------------------- 굽기 / 계층 / 소켓
others = [bench, binobj, glassobj, roof, faces, tl, decals, bindec, leaves]
B.bake_hidden(frame, 2048, hide=others, samples=48, ao_distance=0.3)
B.bake_hidden(bench, 1024, hide=[frame, binobj, glassobj, roof, faces, tl, decals, bindec, leaves], samples=48,
              ao_distance=0.12)
B.bake_hidden(binobj, 1024, hide=[frame, bench, glassobj, roof, faces, tl, decals, bindec, leaves], samples=48,
              ao_distance=0.12)
B.parent([bench, binobj, glassobj, roof, faces, tl, decals, leaves], frame)
B.parent([bindec], binobj)
for i, x in enumerate((-0.8, 0.0, 0.8)):
    B.socket(f"{A}_Socket_Sit_{i}", (x, BY - 0.02, 0.45), frame)
B.socket(A + "_Socket_RouteMap", (2.2, PY - 0.001, 0.0), frame)
B.socket(A + "_Socket_LookTarget_Name", (0, ny, NZ), frame)
B.socket(A + "_Socket_LookTarget_Ad", (LX + 0.09, LY, 1.25), frame, (0, 0, math.pi / 2))
B.socket(A + "_Socket_Wait", (1.6, -1.2, 0.0), frame)
B.socket(A + "_Socket_BIS", (4.7, -0.3, 0.0), frame, (0, 0, math.pi / 2))
B.socket(A + "_Socket_Sign", (-4.3, -1.55, 0.0), frame)
B.socket(A + "_Socket_BusDoor", (1.6, -2.4, 0.0), frame)

notes = {
    "pivot": "바닥 중앙. 정면(-Y→Unity +Z)이 차도. 오른쪽(+X) 끝 옆유리, 왼쪽(-X) 끝 양면 광고 라이트박스, 앞 연석 쪽 점형블록 띠.",
    "parts": {A + "_Frame": "강재 기둥·외팔보·중도리·처마·물받이·선홈통·유리틀·라이트박스 함체·비상벨 (2048 굽기)",
              A + "_Bench": "나무 살 벤치 2.62 m, 앉는 높이 0.45 m, 눕기 방지 팔걸이 2개 (1024 굽기)",
              A + "_Bin": "2칸 쓰레기통 (일반/재활용) (1024 굽기)",
              A + "_Glass": "M_Glass_BusShelter_Glass 강화유리 (먼지·손자국·흙탕 = 텍스처 알파, 월드 UV 2.5 m)",
              A + "_Roof": "M_Glass_BusShelter_Roof 폴리카보네이트 (골 + 먼지, 월드 UV 2.5 m, 양면)",
              A + "_Signs": "이름판(앞뒤, 약발광 0.35) + 광고 포스터(양면, 발광 0.9)",
              A + "_Tactile": "M_Tile_Street_TactileDot 점형블록 (StreetSidewalk 와 같은 머티리얼, 월드 UV 0.6 m, 3 mm). "
                              "보도 모듈에 이미 같은 자리 점형 띠가 있으면 이 오브젝트를 끈다",
              A + "_Leaves": "지붕 위 은행잎 (양면 알파클립, 지붕 아래에서 비쳐 보임)"},
    "sockets": {A + "_Socket_Sit_0/1/2": "벤치 앉는 자리 (높이 0.45 m, 정면 -Y)",
                A + "_Socket_RouteMap": "BusStopRouteMap 원점을 여기에 (뒷유리 앞면, 오른쪽 칸 가운데)",
                A + "_Socket_LookTarget_Name": "이름판 중심 (높이 2.4 m)",
                A + "_Socket_LookTarget_Ad": "안쪽 버거대왕 광고 중심",
                A + "_Socket_Wait": "버스 기다리는 자리 (지붕 아래 앞쪽)",
                A + "_Socket_BIS": "BusStopBIS 추천 위치 (옆유리 쪽 보도, 표시부가 ±X 보행 방향을 봄)",
                A + "_Socket_Sign": "BusStopSign 추천 위치 (라이트박스 쪽 연석)",
                A + "_Socket_BusDoor": "버스 앞문이 서는 연석 지점"},
    "shadows": {A + "_Glass": "Cast Shadows Off (투명 유리가 꽉 찬 그림자를 만들지 않게)",
                A + "_Roof": "Cast Shadows On (폴리카보네이트 지붕 그늘 표현)",
                A + "_Decals": "Cast Shadows Off (유리 스티커)", A + "_Leaves": "Cast Shadows On"},
    "sidewalk": "승차대 아래 보도는 선형 유도 띠(경계석에서 2.6 m)를 빼거나 뒷유리 뒤(y > 1.4)로 돌린 변형이 필요. "
                "BusDoor 소켓을 연석에 맞추면 기본 보도 모듈의 유도 띠가 벤치 앞(y ≈ 0.2)을 가로지른다",
    "collider": "기둥 4개 박스 0.1x0.1x2.63, 뒷유리 박스 6.6x0.06x2.1, 옆유리 0.06x1.9x2.1, 라이트박스 0.2x1.3x2.3, "
                "벤치 박스 2.62x0.45x0.46, 쓰레기통 0.66x0.38x0.9, 지붕은 충돌 불필요",
}
fbx = k3d.export(A, "BusStop", [frame], notes=notes)
for o in k3d.tree_of([frame]):                                      # 크기 확인용
    if o.type == 'MESH':
        mn, mx = k3d.bounds([o]) if not o.children else k3d.bounds([o])
        print("BOUNDS", o.name, [round(v, 2) for v in mn], [round(v, 2) for v in mx])
k3d.preview(A, [frame])
B.shot(A, (6.5, -6.0, 1.55), (0.5, 0.3, 1.2), 35, "fp")
B.shot(A, (3.0, -1.6, 1.55), (-1.5, 0.8, 1.0), 30, "inside")
B.shot(A, (-1.2, -4.6, 1.55), (-0.4, 0.4, 1.5), 35, "front")

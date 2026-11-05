# 버거대왕 가게 외관 StorefrontFacade: 1층 알루미늄 커튼월 + 유리 + 포스터/시트 + 채널 간판 + 돌출 간판 + 캐노피
# + 위층(2~4층) 타일 외벽·창·학원/치과/당구장 간판 + 양옆 떡집/약국. 프로토타입 좌표 그대로 (x = 프로토타입 x,
# y = -(z - FRONT), 원점 = 매장 x=0 유리선 바닥). 정면(거리) = -Y.
import sys, math, os
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Storefront')
import sf
from sf import k3d, box2, box, cyl, quad
import bpy
from mathutils import Vector, Matrix

A = "StorefrontFacade"
sf.textures("facade")
k3d.reset()

MULL = [-6, -4.5, -3, -1.5, 0, 0.9, 1.9, 3.1, 4.3, 5.5]
DL, DR, DH, H = 0.9, 1.9, 2.3, 3.1
MW, MD = 0.07, 0.10            # 멀리언 폭·깊이
BX0, BX1, TOP = -9.5, 9.5, 13.7  # 건물 폭·높이
FL = [4.2, 7.3, 10.4]          # 2~4층 바닥선
WIN_X = [-7.4, -3.7, 0, 3.7, 7.4]
WIN_Z = [5.9, 9.0, 12.1]
WW, WH = 2.4, 1.6

# ---------------------------------------------------------------- 머티리얼
alu = sf.pbr("SF_Alu", (0.42, 0.44, 0.45), rough=0.38, metal=1.0, var=0.06, streak='Z', grime=0.6, grime_dist=0.05,
             edge=0.4, edge_col=(0.6, 0.6, 0.6), bottom=0.8, bottom_h=0.5, scratch=0.3)
aluh = sf.pbr("SF_AluH", (0.42, 0.44, 0.45), rough=0.38, metal=1.0, var=0.06, streak='X', grime=0.6, grime_dist=0.05,
              edge=0.4, edge_col=(0.6, 0.6, 0.6), bottom=0.9, bottom_h=0.5, scratch=0.3)
alud = sf.pbr("SF_AluDark", (0.05, 0.052, 0.055), rough=0.42, metal=1.0, var=0.08, streak='X', grime=0.5, edge=0.6,
              edge_col=(0.3, 0.3, 0.3), bottom=1.0, bottom_h=0.35, scratch=0.5)
rubber = sf.pbr("SF_Rubber", (0.015, 0.015, 0.015), rough=0.8, var=0.1, grime=0.2, bump=0.3)
steel = sf.pbr("SF_Steel", (0.5, 0.5, 0.52), rough=0.3, metal=1.0, var=0.08, grime=0.7, grime_dist=0.01, scratch=0.5)
red_acp = sf.pbr("SF_RedACP", (0.42, 0.035, 0.022), rough=0.42, var=0.1, var_scale=2, fade=0.22, grime=0.5, grime_dist=0.08,
                 grime_col=(0.06, 0.03, 0.02), edge=0.3, edge_col=(0.7, 0.6, 0.5), bump=0.1)
cream_p = sf.pbr("SF_CreamPaint", (0.85, 0.76, 0.56), rough=0.45, var=0.08, fade=0.15, grime=0.5, grime_dist=0.05)
ret = sf.pbr("SF_LetterReturn", (0.16, 0.035, 0.02), rough=0.4, metal=0.3, var=0.08, grime=0.6, grime_dist=0.03, edge=0.3,
             edge_col=(0.5, 0.4, 0.3))
trim = sf.pbr("SF_TrimCap", (0.55, 0.36, 0.1), rough=0.35, metal=0.6, var=0.08, grime=0.4, grime_dist=0.01)
soffit = sf.pbr("SF_Soffit", (0.62, 0.62, 0.6), rough=0.5, var=0.08, var_scale=1.5, grime=0.6, grime_dist=0.1,
                grime_col=(0.1, 0.09, 0.08), bump=0.1)
sill_m = sf.pbr("SF_Sill", (0.45, 0.43, 0.4), rough=0.6, var=0.15, var_scale=10, grime=0.7, grime_dist=0.03, bump=0.4, bump_scale=60)
interior = sf.flat("M_StorefrontFacade_Interior", (0.02, 0.02, 0.02), 0.9)
paper_back = sf.flat("M_StorefrontFacade_PaperBack", (0.72, 0.7, 0.66), 0.8)
letter_face = sf.flat("M_StorefrontFacade_LetterFace", (1.0, 0.88, 0.64), 0.3, emission=(1.0, 0.88, 0.64), strength=1.6)
logo_c = {k: sf.flat("M_StorefrontFacade_Logo" + k, c, 0.35, emission=c, strength=1.6) for k, c in
          (("Crown", (0.87, 0.56, 0.04)), ("Bun", (0.69, 0.25, 0.025)), ("Patty", (0.15, 0.045, 0.014)), ("Seed", (0.9, 0.75, 0.45)))}
downlight = sf.flat("M_StorefrontFacade_Downlight", (1.0, 0.85, 0.62), 0.3, emission=(1.0, 0.85, 0.62), strength=3.0)
g_store = sf.img_mat("M_Glass_Storefront", sf.tex(A, "GlassSmudge"), rough=0.04, alpha=True, double=True)
k3d.principled(g_store).inputs['Alpha'].default_value = 1.0
tile_wall = k3d.tile("Storefront_FacadeTile", polyhaven_id="rectangular_facade_tiles_02", res="1k")
tile_granite = k3d.tile("Storefront_Granite", polyhaven_id="granite_tile_03", res="1k")


def img(name, **kw):
    return sf.img_mat("M_StorefrontFacade_" + name, sf.tex(A, name), **kw)


# 위층 창유리 = 방 너머 그림(천장 원근 + 하늘 반사)을 그린 불투명 유리. 창마다 종류·좌우 뒤집기를 섞는다
room = {k: img("Room" + k, rough=0.08, emission=e) for k, e in (("Class", 0.35), ("Blinds", 0.2), ("Curtain", 0), ("Empty", 0))}
ROOMS = {5.9: ["Class", "Class~", "Curtain", "Blinds", "Blinds~"],      # 2층 학원·치과
         9.0: ["Blinds", "Curtain~", "Class", "Empty", "Curtain"],      # 3층 당구장
         12.1: ["Empty", "Empty~", "Curtain", "Empty", "Empty~"]}       # 4층 임대


def poster(name, w, h, x, z, y=0.004, rot=0.0, **kw):
    """유리 안쪽에 붙인 인쇄물 (거리 쪽을 봄) + 뒷면 종이."""
    m = img(name, **kw)
    a = quad(A + "_" + name, w, h, (x, y, z), m)
    b = quad(A + "_" + name + "Back", w, h, (x, y + 0.001, z), paper_back, face="+Y")
    for o in (a, b):
        o.rotation_euler.y = rot
    return [a, b]


# ================================================================ 1층 매장 프레임 (Frame)
F = []
for x in MULL:  # 멀리언 + 앞 스냅캡
    F.append(box2((x - MW / 2, -MD / 2, 0), (x + MW / 2, MD / 2, H), alu, 0.003, 2))
    F.append(box2((x - 0.024, -MD / 2 - 0.012, 0.0), (x + 0.024, -MD / 2 + 0.001, H - 0.12), alu, 0.003, 2))
glass_quads = []
for a, b in zip(MULL[:-1], MULL[1:]):
    x0, x1 = a + MW / 2, b - MW / 2
    if a == DL:  # 문 칸: 위 유리만
        pass
    else:
        F.append(box2((x0, -0.025, 0), (x1, 0.025, 0.25), alud, 0.002, 2))                  # 킥 패널
        F.append(box2((x0, -0.026, 0.115), (x1, -0.024, 0.125), rubber, 0.0005, 1))          # 패널 이음선
        F.append(box2((x0, -MD / 2, 0.25), (x1, MD / 2, 0.31), aluh, 0.003, 2))             # 아래 가로대
        glass_quads.append((x0, x1, 0.31, DH - 0.01))
    F.append(box2((x0, -MD / 2, DH - 0.01), (x1, MD / 2, DH + 0.05), aluh, 0.003, 2))      # 문 높이 가로대
    glass_quads.append((x0, x1, DH + 0.05, H - 0.1))
    for y in (-0.008, 0.008):  # 유리 고정 가스켓 (멀리언 옆, 위아래)
        for (gx0, gx1, gz0, gz1) in glass_quads[-2:] if a != DL else glass_quads[-1:]:
            F.append(box2((gx0, y - 0.003, gz0), (gx0 + 0.006, y + 0.003, gz1), rubber, 0.001, 1))
            F.append(box2((gx1 - 0.006, y - 0.003, gz0), (gx1, y + 0.003, gz1), rubber, 0.001, 1))
F.append(box2((MULL[0] - 0.06, -0.065, H - 0.1), (MULL[-1] + 0.06, 0.065, H + 0.02), aluh, 0.004, 3))   # 헤더
for (x0, x1, z0, z1) in glass_quads:   # 유리 (UV = 매장 폭 11.6m × 3.1m 한 장)
    u0, u1, v0, v1 = (x0 + 6.05) / 11.6, (x1 + 6.05) / 11.6, z0 / 3.1, z1 / 3.1
    F.append(quad(A + "_Pane", x1 - x0, z1 - z0, ((x0 + x1) / 2, 0, (z0 + z1) / 2), g_store, uv=(u0, v0, u1, v1)))
# 문틀: 안쪽 멈춤대(밀면 덜컹), 문턱, 바닥 잠금 구멍, 클로저 슈 브래킷, 바닥 도어스토퍼
F += [box2((DR - MW / 2 - 0.022, 0.026, 0), (DR - MW / 2 + 0.004, 0.042, DH), aluh, 0.002, 2),
      box2((DL + MW / 2, 0.026, DH - 0.035), (DR - MW / 2, 0.042, DH + 0.001), aluh, 0.002, 2),
      box2((DR - MW / 2 - 0.022, 0.024, 0.01), (DR - MW / 2 - 0.016, 0.027, DH - 0.01), rubber, 0.0005, 1),
      box2((DL + MW / 2, -0.07, 0), (DR - MW / 2, 0.07, 0.007), steel, 0.002, 2)]
for i in range(6):
    F.append(box2((DL + MW / 2 + 0.01, -0.06 + i * 0.024, 0.0068), (DR - MW / 2 - 0.01, -0.052 + i * 0.024, 0.0075), rubber, 0, 1))
F.append(cyl(A + "_Strike", 0.012, 0.002, (DL + 0.035 + 0.872, 0, 0.0078), rubber, n=16, bev=0.0005, seg=1))
SHX = DL + 0.035 + sf.DOOR_SHOE[0]
F += [box2((SHX - 0.03, -MD / 2 - 0.006, DH + 0.0), (SHX + 0.03, -MD / 2, DH + 0.045), steel, 0.0015, 2),
      box2((SHX - 0.016, -0.077, sf.DOOR_SHOE[2] + 0.008), (SHX + 0.016, -MD / 2 - 0.006, sf.DOOR_SHOE[2] + 0.017), steel, 0.0015, 2)]   # 슈 받침 (조인트 위)
F += [cyl(A + "_StopBase", 0.03, 0.006, (DL - 0.02, -0.80, 0.003), steel, n=24, bev=0.0015),
      cyl(A + "_StopDome", 0.022, 0.035, (DL - 0.02, -0.80, 0.0235), rubber, n=24, bev=0.008, seg=3)]
# 캐노피 (빨강 ACP 앞띠 + 회색 하부 + 다운라이트)
CX0, CX1, CY = MULL[0] - 0.15, MULL[-1] + 0.15, -1.0
F += [box2((CX0, CY, H + 0.02), (CX1, -0.07, H + 0.09), soffit, 0.004, 2),
      box2((CX0, CY - 0.03, H - 0.1), (CX1, CY, H + 0.1), red_acp, 0.004, 2),
      box2((CX0 - 0.03, CY - 0.03, H - 0.1), (CX0, -0.07, H + 0.1), red_acp, 0.004, 2),
      box2((CX1, CY - 0.03, H - 0.1), (CX1 + 0.03, -0.07, H + 0.1), red_acp, 0.004, 2),
      box2((CX0, CY - 0.034, H - 0.06), (CX1, CY - 0.029, H - 0.045), cream_p, 0.001, 1)]
for x in [-5.2, -3.0, -0.8, 1.4, 3.6]:
    F.append(cyl(A + "_DLRing", 0.07, 0.008, (x, -0.55, H + 0.016), steel, n=28, bev=0.002))
    F.append(cyl(A + "_DL", 0.055, 0.004, (x, -0.55, H + 0.0105), downlight, n=28, bev=0))
# 포스터·시트 (유리 안쪽)
F += poster("PosterBulgogi", 0.9, 1.3, -5.25, 1.26)
F += poster("PosterNew", 0.9, 1.3, -2.25, 1.26)
F += poster("PosterFries", 0.9, 1.3, 3.7, 1.26)
F += poster("PosterKiosk", 0.55, 0.78, 2.55, 1.05)
F += poster("StickerCoupon", 0.4, 0.5, -0.75, 1.0)
F += poster("StickerCardOnly", 0.3, 0.195, 0.45, 1.18)
F += poster("StickerCCTV", 0.2, 0.113, 2.22, 1.78)
F += poster("NoteHelpWanted", 0.21, 0.297, 4.85, 1.32, rot=0.05)
F.append(quad(A + "_Hours", 0.5, 0.293, (0.45, 0.004, 1.55), img("VinylHours", alpha_clip=0.5)))
band = img("VinylBand", alpha_clip=0.5)
for a, b in zip(MULL[:-1], MULL[1:]):
    if a != DL:
        x0, x1 = a + MW / 2, b - MW / 2
        F.append(quad(A + "_Band", x1 - x0, 0.06, ((x0 + x1) / 2, 0.003, 2.05), band, uv=(0, 0, (x1 - x0) / 2.0, 1)))
# 발매트 (문 바깥, 6mm)
mat_m = img("DoorMatPrint", rough=0.95)  # 굽지 않음: 프레임 아틀라스에 넣으면 글자가 뭉개진다
dm = box2((DL + 0.05, -0.72, 0.0), (DR - 0.05, -0.12, 0.006), mat_m, 0.003, 2, name=A + "_DoorMat")
k3d.select([dm])
bpy.ops.object.transform_apply(location=True)
me = dm.data
uvl = me.uv_layers[0]
for poly in me.polygons:  # 윗면 = 인쇄 텍스처 0..1
    for li in poly.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        uvl.data[li].uv = ((co.x - (DL + 0.05)) / (DR - DL - 0.1), (co.y + 0.72) / 0.6)
F.append(dm)

# ---- 양옆 가게 (떡집 / 약국) 1층 전면
def neighbor(x0, x1, sign, backdrop):
    out = []
    for x in (x0, (x0 + x1) / 2, x1):
        out.append(box2((x - 0.03, -0.04, 0), (x + 0.03, 0.04, 3.1), alu, 0.003, 2))
    out.append(box2((x0, -0.04, 0), (x1, 0.04, 0.3), alud, 0.003, 2))
    out.append(box2((x0, -0.04, 2.45), (x1, 0.04, 2.51), aluh, 0.003, 2))
    out.append(box2((x0 - 0.05, -0.05, 3.05), (x1 + 0.05, 0.05, 3.13), aluh, 0.003, 2))
    for z0, z1 in ((0.3, 2.45), (2.51, 3.05)):
        for a, b in ((x0 + 0.03, (x0 + x1) / 2 - 0.03), ((x0 + x1) / 2 + 0.03, x1 - 0.03)):
            out.append(quad(A + "_NPane", b - a, z1 - z0, ((a + b) / 2, 0, (z0 + z1) / 2), g_store,
                            uv=((a + 6.05) / 11.6, z0 / 3.1, (b + 6.05) / 11.6, z1 / 3.1)))
    # 안쪽 방 (어두운 상자 + 진열 사진)
    out.append(quad(A + "_NBack", x1 - x0, 2.8, ((x0 + x1) / 2, 0.75, 1.4), img(backdrop, emission=0.35)))
    out.append(quad(A + "_NCeil", x1 - x0, 0.75, ((x0 + x1) / 2, 0.375, 3.1), interior, face="-Z"))
    for x, f in ((x0, "+X"), (x1, "-X")):
        q = quad(A + "_NSide", 0.75, 3.1, (x, 0.375, 1.55), interior, face=f)
        out.append(q)
    # 간판 (상자 + 면)
    out.append(box2((x0 - 0.05, -0.2, 3.25), (x1 + 0.05, -0.02, 4.1), alud, 0.006, 2))
    out.append(quad(A + "_NSign", x1 - x0 - 0.04, 0.81, ((x0 + x1) / 2, -0.2015, 3.675), img(sign, emission=0.6, rough=0.4)))
    return out
F += neighbor(-9.05, -6.5, "SignRiceCake", "BackdropRiceCake")
F += neighbor(5.98, 9.05, "SignPharmacy", "BackdropPharmacy")

frame = sf.join(F, A + "_Frame")
k3d.set_origin(frame, (0, 0, 0))
keep = tuple(m.name for m in frame.data.materials if m.name.startswith("M_"))
k3d.bake(frame, 2048, keep=keep, ao_distance=0.12, samples=32)

# ================================================================ 간판 (Sign): 채널 문자 + 로고 + 지점명 + 돌출 간판 + 위층 간판
S = []
SX0, SX1, SZ0, SZ1, SYF = MULL[0] - 0.15, MULL[-1] + 0.15, 3.195, 4.445, -0.16
S += [box2((SX0, SYF, SZ0), (SX1, -0.01, SZ1), red_acp, 0.006, 3),
      box2((SX0 - 0.012, SYF - 0.012, SZ1 - 0.035), (SX1 + 0.012, -0.01, SZ1 + 0.012), alud, 0.004, 2),
      box2((SX0 - 0.012, SYF - 0.012, SZ0 - 0.012), (SX1 + 0.012, -0.01, SZ0 + 0.035), alud, 0.004, 2),
      box2((SX0, SYF - 0.002, SZ1 - 0.11), (SX1, SYF + 0.01, SZ1 - 0.085), cream_p, 0.001, 1),
      box2((SX0, SYF - 0.002, SZ0 + 0.085), (SX1, SYF + 0.01, SZ0 + 0.11), cream_p, 0.001, 1)]
for x in [SX0 + 0.3 + i * (SX1 - SX0 - 0.6) / 7 for i in range(8)]:   # 패널 이음 리벳
    for z in (SZ0 + 0.06, SZ1 - 0.06):
        S.append(cyl(A + "_Rivet", 0.005, 0.003, (x, SYF - 0.0015, z), steel, rot=(math.pi / 2, 0, 0), n=10, bev=0.001, seg=1))


def letters(s, size, depth, x, z, bevel=0.006):
    t = sf.text(A + "_Text", s, size, depth, bevel=bevel, res=4)
    sf.mat_by_normal(t, letter_face, ret, trim)
    t.location = (x, SYF, z)
    return t


S.append(letters("버거대왕", 0.86, 0.08, 0.55, 3.43))
S.append(letters("시장입구점", 0.17, 0.03, 4.75, 3.33, bevel=0.002))
# 로고: 프로토타입 Rn() 좌표 (1단위 = 1.25/150 m), 왕관+버거만 (워드마크 없음)
LX, LZ, U = -3.32, 3.67, 1.25 / 150
def lp(pts):
    return [(LX + x * U, LZ - y * U) for x, y in pts]
parts = [("Crown", [(-30, -48), (-34, -82), (-14, -62), (0, -90), (14, -62), (34, -82), (30, -48)]),
         ("Bun", [(62 * math.cos(a), -8 - 44 * math.sin(a)) for a in [math.pi * i / 24 for i in range(25)]]),
         ("Patty", [(-60, -6), (60, -6), (60, 10), (-60, 10)]),
         ("Bun", [(x, y) for x, y in sf.rrect_pts(-58, 12, 58, 34, 8)])]
for k, pts in parts:
    o = sf.poly_extrude(A + "_Logo" + k, lp(pts), 0.05)
    sf.mat_by_normal(o, logo_c[k], ret)
    o.location.y = SYF
    S.append(o)
for i in range(7):  # 참깨
    x, y = -40 + i * 13, -30 + (i % 2) * 9
    o = sf.poly_extrude(A + "_Seed", lp(sf.ellipse_pts(x, y, 3.2, 1.8, n=8)[:-1]), 0.056)
    sf.mat_by_normal(o, logo_c["Seed"], ret)
    o.location.y = SYF
    S.append(o)
# 돌출 간판 (기둥 위, 양면)
PX, PZ0, PZ1, PY0, PY1 = -5.95, 4.45, 6.85, -0.12, -0.80
S += [box2((PX - 0.09, PY1, PZ0), (PX + 0.09, PY0, PZ1), alud, 0.008, 3)]
psign = img("ProjSign", emission=1.2, rough=0.4)
for sx, f in ((-0.0905, "-X"), (0.0905, "+X")):
    S.append(quad(A + "_ProjFace", PY0 - PY1 - 0.06, PZ1 - PZ0 - 0.06, (PX + sx, (PY0 + PY1) / 2, (PZ0 + PZ1) / 2), psign, face=f))
for z in (PZ0 + 0.2, PZ1 - 0.2):
    S.append(box2((PX - 0.03, PY0, z - 0.03), (PX + 0.03, -0.03, z + 0.03), steel, 0.004, 2))
    S.append(box2((PX - 0.08, -0.036, z - 0.08), (PX + 0.08, -0.03, z + 0.08), steel, 0.003, 2))
# 위층 간판 (외벽에 붙은 판 간판)
for name, x, z in (("SignAcademy", -3.7, 7.45), ("SignDental", 3.7, 7.45), ("SignBilliards", 0, 10.55)):
    S.append(box2((x - 1.75, -0.12, z - 0.4), (x + 1.75, -0.03, z + 0.4), alud, 0.006, 2))
    S.append(quad(A + "_" + name, 3.46, 0.76, (x, -0.1215, z), img(name, emission=0.5, rough=0.4)))
sign = sf.join(S, A + "_Sign")
k3d.set_origin(sign, (0, 0, 0))
keep = tuple(m.name for m in sign.data.materials if m.name.startswith("M_"))
k3d.bake(sign, 2048, keep=keep, ao_distance=0.08, samples=32)

# ================================================================ 위층 창 (Windows)
Wn = []
vinyl = {(-7.4, 5.9): "VinylAcademy", (-3.7, 5.9): "VinylAcademy", (3.7, 5.9): "VinylDental", (7.4, 5.9): "VinylDental",
         (0, 9.0): "VinylBilliards", (3.7, 12.1): "BannerRent"}
streak = img("Streaks", alpha=True)
k3d.flag(streak, transparent=True)
for wz in WIN_Z:
    for wx, rk in zip(WIN_X, ROOMS[wz]):
        x0, x1, z0, z1 = wx - WW / 2, wx + WW / 2, wz - WH / 2, wz + WH / 2
        Y = 0.10  # 창틀 깊이 (외벽면 -0.03 에서 13cm 안쪽)
        Wn += [box2((x0, Y - 0.05, z0), (x0 + 0.06, Y + 0.05, z1), alu, 0.003, 1),
               box2((x1 - 0.06, Y - 0.05, z0), (x1, Y + 0.05, z1), alu, 0.003, 1),
               box2((x0, Y - 0.05, z0), (x1, Y + 0.05, z0 + 0.06), aluh, 0.003, 1),
               box2((x0, Y - 0.05, z1 - 0.06), (x1, Y + 0.05, z1), aluh, 0.003, 1),
               box2((wx - 0.03, Y - 0.04, z0 + 0.06), (wx + 0.03, Y + 0.0, z1 - 0.06), alu, 0.003, 1),
               box2((wx - 0.03, Y + 0.0, z0 + 0.06), (wx + 0.03, Y + 0.04, z1 - 0.06), alu, 0.003, 1)]
        for a, b, yy in ((x0 + 0.06, wx - 0.03, Y + 0.02), (wx + 0.03, x1 - 0.06, Y - 0.02)):  # 미닫이 두 짝
            Wn += [box2((a, yy - 0.02, z0 + 0.06), (a + 0.05, yy + 0.02, z1 - 0.06), alu, 0.002, 1),
                   box2((b - 0.05, yy - 0.02, z0 + 0.06), (b, yy + 0.02, z1 - 0.06), alu, 0.002, 1),
                   box2((a + 0.05, yy - 0.02, z0 + 0.06), (b - 0.05, yy + 0.02, z0 + 0.11), aluh, 0.002, 1),
                   box2((a + 0.05, yy - 0.02, z1 - 0.11), (b - 0.05, yy + 0.02, z1 - 0.06), aluh, 0.002, 1)]
            u0, u1, v0 = (a + 0.05 - x0) / WW, (b - 0.05 - x0) / WW, 0.085 / WH
            if rk.endswith("~"):
                u0, u1 = 1 - u0, 1 - u1
            Wn.append(quad(A + "_WGlass", b - a - 0.1, z1 - z0 - 0.17, ((a + b) / 2, yy, (z0 + z1) / 2), room[rk.rstrip("~")],
                           uv=(u0, v0, u1, 1 - v0)))
            v = vinyl.get((wx, wz))
            if v:
                Wn.append(quad(A + "_WVinyl", b - a - 0.14, (b - a - 0.14) * 0.664, ((a + b) / 2, yy - 0.003, (z0 + z1) / 2),
                               img(v, alpha_clip=0.5) if v != "BannerRent" else img(v, rough=0.7)))
        Wn.append(box2((x0 - 0.06, -0.075, z0 - 0.05), (x1 + 0.06, 0.12, z0), sill_m, 0.006, 2))     # 창턱
        Wn.append(quad(A + "_Streak", WW, 1.1, (wx, -0.0315, z0 - 0.05 - 0.55), streak))
# 옥상 난간 위 갓돌
Wn.append(box2((BX0 - 0.05, -0.09, TOP), (BX1 + 0.05, 0.25, TOP + 0.08), sill_m, 0.008, 2))
wins = sf.join(Wn, A + "_Windows")
k3d.set_origin(wins, (0, 0, 0))
keep = tuple(m.name for m in wins.data.materials if m.name.startswith("M_"))
k3d.bake(wins, 2048, keep=keep, ao_distance=0.1, samples=32)

# ================================================================ 외벽 (타일링): 위층 외장 타일 / 1층 화강석 기둥·띠
T = []
xs = [BX0] + sum([[wx - WW / 2, wx + WW / 2] for wx in WIN_X], []) + [BX1]
for i in range(0, len(xs), 2):   # 창 사이 벽기둥 (2~4층)
    T.append(box2((xs[i], -0.03, FL[0]), (xs[i + 1], 0.25, TOP), None, 0, 1))
for zs in [(FL[0], WIN_Z[0] - WH / 2)] + [(WIN_Z[k] + WH / 2, WIN_Z[k + 1] - WH / 2) for k in range(2)] + [(WIN_Z[2] + WH / 2, TOP)]:
    for wx in WIN_X:
        T.append(box2((wx - WW / 2, -0.03, zs[0]), (wx + WW / 2, 0.25, zs[1]), None, 0, 1))
wall = sf.join(T, A + "_WallTile")
wall.data.materials.clear()
wall.data.materials.append(tile_wall)
k3d.uv_world(wall, 2.105)
G = [box2((BX0, -0.08, 0), (BX0 + 0.45, 0.25, FL[0]), None, 0, 1),
     box2((-6.5, -0.08, 0), (MULL[0] - MW / 2, 0.25, FL[0]), None, 0, 1),
     box2((MULL[-1] + MW / 2, -0.08, 0), (5.98, 0.25, FL[0]), None, 0, 1),
     box2((BX1 - 0.45, -0.08, 0), (BX1, 0.25, FL[0]), None, 0, 1),
     box2((BX0, -0.02, 3.13), (BX1, 0.25, FL[0]), None, 0, 1),
     box2((BX0 - 0.02, -0.06, FL[0] - 0.12), (BX1 + 0.02, 0.25, FL[0]), None, 0, 1)]   # 층 띠
gran = sf.join(G, A + "_WallGranite")
gran.data.materials.clear()
gran.data.materials.append(tile_granite)
k3d.uv_world(gran, 1.8)
for o in (wall, gran):
    k3d.set_origin(o, (0, 0, 0))
    sf.finish(o, 0, wn=False)
    k3d.smooth(o, 30)

# ================================================================ 소켓
socks = [sf.empty(A + "_Socket_DoorHinge", (DL + 0.035 + sf.DOOR_AX, sf.DOOR_AY, 0)),
         sf.empty(A + "_Socket_SignLook", (0.55, SYF, 3.77)),
         sf.empty(A + "_Socket_DoorLook", (DL + 0.035 + 0.67, 0, 1.32)),
         sf.empty(A + "_Socket_AC_1", (-1.85, -0.03, 5.15)),   # 돌출 간판(x -5.95)과 겹치지 않는 기둥
         sf.empty(A + "_Socket_AC_2", (5.55, -0.03, 8.25)),
         sf.empty(A + "_Socket_AC_3", (5.55, -0.03, 11.35)),
         sf.empty(A + "_Socket_CanopyLight", (1.0, -1.2, 2.6)),
         sf.empty(A + "_Socket_CloserShoe", (SHX, sf.DOOR_SHOE[1], sf.DOOR_SHOE[2]))]
roots = [frame, sign, wins, wall, gran] + socks
notes = {
    "pivot": "원점 = 프로토타입 매장 좌표 x=0, 유리선(FRONT=3.8) 바닥. Blender x = 프로토타입 x, y = -(z-3.8). 문 개구 x 0.935~1.865, 높이 2.29.",
    "size": "건물 폭 19m(x -9.5~9.5), 높이 13.78m. 1층 매장 x -6.035~5.535, 캐노피 1m 돌출, 채널 간판 3.195~4.445m.",
    "door": "StoreGlassDoor 를 StorefrontFacade_Socket_DoorHinge 에 그대로(회전 0) 붙인다. 밀면 안쪽 멈춤대(+Y 쪽 문틀, 문짝과 1mm 틈)에 "
            "걸린다. 밀기 덜컹: 매장 쪽 회전은 최대 0.0011rad(약 0.06도)로 막고, 거리 쪽으로 최대 0.012rad 되튀게 + 소리 + 카메라 흔들림으로 표현. "
            "프로토타입 값(매장 쪽 0.05rad)을 그대로 쓰면 문짝 끝이 멈춤대를 최대 4.5cm 뚫고 들어간다.",
    "sockets": {"StorefrontFacade_Socket_DoorHinge": "유리문 힌지 축(맞경첩 너클 중심) 바닥 = StoreGlassDoor 원점",
                "StorefrontFacade_Socket_CloserShoe": "도어클로저 전완 끝 슈 조인트(헤더 브래킷 세로축). StoreGlassDoor_CloserFore 끝이 늘 이 점에 붙도록 2링크를 푼다", "StorefrontFacade_Socket_SignLook": "인트로 시선(간판 글자 중심)",
                "StorefrontFacade_Socket_DoorLook": "문 스티커 시선", "StorefrontFacade_Socket_AC_1..3": "StorefrontAC 원점(벽면·거치대 바닥) 자리",
                "StorefrontFacade_Socket_CanopyLight": "캐노피 아래 따뜻한 포인트 라이트 자리(프로토타입 2.2, 5m)"},
    "emission": "채널 글자 면·로고 면은 M_StorefrontFacade_LetterFace / Logo* (평면 emissive 1.6), 캐노피 다운라이트 3.0, 간판 텍스처 0.5~1.2.",
    "transparent": "M_Glass_Storefront: BaseColor 텍스처 알파 = 유리 불투명도(UV = 매장 폭 11.6m×3.1m 한 장). M_StorefrontFacade_Streaks = 창턱 아래 빗물 때(반투명).",
    "upper_windows": "위층 창유리는 불투명 M_StorefrontFacade_Room{Class,Blinds,Curtain,Empty}: 거리에서 올려다본 방 천장(원근)·블라인드·커튼 + 하늘 반사를 그린 텍스처, "
                     "smoothness 0.92. Class 0.35·Blinds 0.2 는 불 켜진 방이라 약한 emission. 창마다 종류와 좌우 뒤집기를 섞었다.",
    "floor_stopper": "바닥 도어스토퍼는 문이 아니라 파사드(정적)에 있다: x 0.88, y -0.80.",
}
k3d.export(A, "Storefront", roots, notes=notes)
k3d.preview(A, roots)

# ---- 1인칭 확인 렌더 (내보낸 뒤에만: 문·실외기 FBX 를 불러와 배치, 임시 바닥)
def bring(asset, loc):
    """저장된 .blend 에서 붙여 넣기 (FBX 는 텍스처 경로가 Unity 기준이라 분홍색으로 나온다)."""
    p = os.path.join(k3d.SRC, "Blender", "Storefront", asset + ".blend")
    if not os.path.exists(p):
        return
    with bpy.data.libraries.load(p) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(asset)]
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    for o in dst.objects:
        if o.parent is None:
            o.location = Vector(loc) + o.location
bring("StoreGlassDoor", socks[0].location)
for s in socks[3:6]:
    bring("StorefrontAC", s.location)
try:
    bpy.ops.file.find_missing_files(directory=os.path.join(k3d.ART, "Textures"))
except Exception as e:
    print("find_missing_files", e)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, -10, -0.001))
gp = bpy.context.active_object
gp.data.materials.append(k3d.mat("tmp_ground", (0.3, 0.29, 0.27), 0.85))
P = os.path.join(k3d.SRC, "Previews")
sf.look((-2.4, -4.9, 1.55), (-0.1, 0, 3.72), lens=24, path=os.path.join(P, A + "_fp_intro.png"))
sf.look((-0.2, -3.0, 1.55), (1.3, 0, 1.25), lens=30, path=os.path.join(P, A + "_fp_door.png"))
sf.look((1.0, -16, 1.6), (0.3, 0, 6.0), lens=28, path=os.path.join(P, A + "_street.png"))


REST = {}


def pose_door(a):
    """문을 a rad 당겨 열고 클로저 2링크를 푼다 (Unity 에서 할 계산과 같음: 두 원의 교점 중 거리 쪽 = 팔꿈치)."""
    ob = bpy.data.objects
    leaf, c1, c2, H3 = ob["StoreGlassDoor_Leaf"], ob["StoreGlassDoor_Closer"], ob["StoreGlassDoor_CloserFore"], socks[-1].location
    ang = lambda v: math.atan2(v.y, v.x)
    for o in (leaf, c1, c2):   # 닫힌 상태로 되돌림 (첫 호출 때 저장)
        o.matrix_basis = REST.setdefault(o.name, o.matrix_basis.copy())
    bpy.context.view_layer.update()
    tip = c2.matrix_world.inverted() @ H3                    # 닫힌 상태에서 전완 끝 = 슈
    S0, E0, H = c1.matrix_world.translation.xy, c2.matrix_world.translation.xy, H3.xy
    L1, L2, f1, f2 = (E0 - S0).length, (H - E0).length, ang(E0 - S0), ang(H - E0)
    leaf.rotation_euler.z = -a
    bpy.context.view_layer.update()
    S = c1.matrix_world.translation.xy
    v = H - S
    dd = v.length
    m = (L1 * L1 - L2 * L2 + dd * dd) / (2 * dd)
    h = math.sqrt(max(0.0, L1 * L1 - m * m))
    n = Vector((-v.y, v.x)) / dd
    E = min((S + v / dd * m + n * h, S + v / dd * m - n * h), key=lambda p: p.y)   # 거리 쪽(-Y) 해
    z = c1.matrix_world.translation.z
    c1.matrix_world = Matrix.Translation((S.x, S.y, z)) @ Matrix.Rotation(ang(E - S) - f1, 4, 'Z')   # 본암 → 팔꿈치
    c2.matrix_world = Matrix.Translation((E.x, E.y, H3.z)) @ Matrix.Rotation(ang(H - E) - f2, 4, 'Z')  # 전완: 팔꿈치로 옮겨 → 슈
    bpy.context.view_layer.update()
    err = (c2.matrix_world @ tip - H3).length
    print(f"sf: door {a:.2f}rad |S-H|={dd:.3f} (L1+L2={L1 + L2:.3f}) shoe err={err * 1000:.2f}mm")


pose_door(0.9)
sf.look((0.1, -2.6, 1.55), (1.2, -0.35, 1.45), lens=30, path=os.path.join(P, A + "_fp_door_open.png"))
pose_door(1.45)
sf.look((0.45, -1.35, 2.2), (1.05, -0.15, 2.22), lens=32, path=os.path.join(P, A + "_door_open_hinge.png"))

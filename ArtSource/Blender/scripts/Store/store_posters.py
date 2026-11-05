"""StorePosters: 매장 벽 포스터·액자·로고 라이트박스 (프로토타입 he 그룹 + 오른쪽 벽 액자 3개).
원점 = 매장 원점 (프로토타입 (0,0,0) 바닥, StoreShell 과 같은 자리). 각 포스터는 자식 오브젝트, 원점 = 벽에 닿는 뒷면 중앙.
블렌더 매장좌표 = (x, -z, y) (프로토타입 기준). 뒷벽 y=+4.2 (정면 -Y 를 봄), 오른쪽 벽 x=+5.5 (-X 를 봄)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
import bmesh
k3d = S.k3d
bpy = S.bpy
k3d.reset()
S.textures()

# ---- 머티리얼 (굽기용)
m_alu = S.pbr("M_tmp_PSAlu", (0.62, 0.63, 0.64), 0.32, 1.0, var=0.05, grime=0.55, gdist=0.02, edge=0.6,
              edge_col=(0.85, 0.85, 0.86), scratch=0.5, brush=0.15, bump=0.01)
m_back = S.pbr("M_tmp_PSBacking", (0.55, 0.53, 0.5), 0.8, grime=0.4, bump=0.05)
m_blk = S.pbr("M_tmp_PSBlackFrame", (0.025, 0.024, 0.023), 0.5, var=0.12, grime=0.4, gdist=0.02, edge=0.8,
              edge_col=(0.16, 0.14, 0.12), scratch=0.4, bump=0.05, bscale=220)
m_box = S.pbr("M_tmp_PSLightbox", (0.07, 0.07, 0.075), 0.4, 0.8, var=0.06, grime=0.6, gdist=0.03, edge=0.7,
              edge_col=(0.45, 0.45, 0.46), scratch=0.5, streak=0.2)
m_raceway = S.pbr("M_tmp_PSRaceway", (0.78, 0.77, 0.73), 0.45, var=0.06, grime=0.6, gdist=0.02, streak=0.3,
                  edge=0.2, edge_col=(0.9, 0.9, 0.88), smudge=0.2)
glass = k3d.mat("M_Glass_StorePosters_Cover", (0.92, 0.94, 0.96), 0.06, alpha=0.1)
tape = k3d.mat("M_Glass_StorePosters_Tape", (0.95, 0.92, 0.8), 0.25, alpha=0.38)


def prism(name, pts, y0, y1, mat, bev=0.002, seg=2):
    """XZ 평면 다각형(pts)을 Y 로 y0..y1 만큼 두께를 준 기둥 (마이터 프레임 막대용)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = S.obj_from_bm(name, bm, mat=mat)
    if bev:
        S.bevel(o, bev, seg)
    return o


def mitre_frame(W, H, b, y0, y1, mat, gap=0.0006, bev=0.002, seg=2):
    """45도 마이터 이음 프레임 4개 막대 (외곽 W x H, 폭 b). 이음 틈이 베벨로 보인다."""
    w, h, g = W / 2, H / 2, gap
    bars = [
        [(-w + g, h), (w - g, h), (w - b - g, h - b), (-w + b + g, h - b)],          # 위
        [(-w + b + g, -h + b), (w - b - g, -h + b), (w - g, -h), (-w + g, -h)],      # 아래
        [(-w, -h + g), (-w + b, -h + b + g), (-w + b, h - b - g), (-w, h - g)],      # 왼쪽
        [(w - b, -h + b + g), (w, -h + g), (w, h - g), (w - b, h - b - g)],          # 오른쪽
    ]
    return [prism("bar", p, y0, y1, mat, bev, seg) for p in bars]


posters = []


def finish(name, parts, loc, rz, print_mat, pw, ph, py, cover_y=None, extra=()):
    """프레임 굽기 + 인쇄면(굽지 않음) + 커버를 자식으로, 매장 좌표에 배치."""
    frame = S.join(parts, name)
    S.set_origin(frame, (0, 0, 0))
    k3d.bake(frame, 512, samples=32, ao_distance=0.03)
    kids = [S.quad(name + "_Print", pw, ph, (0, py, 0), print_mat)]
    if cover_y is not None:
        kids.append(S.quad(name + "_Cover", pw + 0.004, ph + 0.004, (0, cover_y, 0), glass))
    kids += list(extra)
    for o in kids:
        S.reparent(o, frame)
    frame.location = loc
    frame.rotation_euler = (0, 0, rz)
    posters.append(frame)
    return frame


BACK, RIGHT = 4.2, 5.5
FACE_BACK, FACE_RIGHT = 0.0, -math.pi / 2

# ---- 1,2. A1 알루미늄 스냅 프레임 (594x841 인쇄, 프로파일 25mm) — 키오스크 안내 / 신메뉴
for nm, tx, x in (("StorePosters_Kiosk", "poster_kiosk.png", 0.75), ("StorePosters_New", "poster_new.png", -0.05)):
    PW, PH, B = 0.594, 0.841, 0.025
    p = mitre_frame(PW + 2 * B - 0.01, PH + 2 * B - 0.01, B, -0.014, -0.002, m_alu, bev=0.004, seg=3)
    p.append(S.boxz("bk", -PW / 2, PW / 2, -0.004, 0.0, -PH / 2, PH / 2, m_back, 0.001, 1))
    m = S.img_mat("M_" + nm + "_Print", S.tex(tx), rough=0.55)
    finish(nm, p, (x, BACK, 2.28), FACE_BACK, m, PW - 0.01, PH - 0.01, -0.0045, cover_y=-0.0075)

# ---- 3. 앱 쿠폰 포스터 (B2 종이, 테이프로 붙임, 모서리가 살짝 들뜸)
PW, PH = 0.5, 0.72
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
NX, NZ = 10, 14
vs = {}
for i in range(NX + 1):
    for j in range(NZ + 1):
        u, v = i / NX, j / NZ
        # 모서리·가장자리 들뜸 (아래쪽 모서리가 더 들뜸)
        cu, cv = abs(u - 0.5) * 2, abs(v - 0.5) * 2
        lift = 0.004 * (cu ** 4) * (cv ** 3) + 0.0012 * math.sin(v * 9.0 + u * 2) * cu ** 2
        lift += 0.003 * (1 - v) ** 6 * cu ** 2
        vs[i, j] = bm.verts.new(((u - 0.5) * PW, -0.0012 - lift, (v - 0.5) * PH))
for i in range(NX):
    for j in range(NZ):
        f = bm.faces.new((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]))
        for l, (a, c) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
            l[uvl].uv = (a / NX, c / NZ)
cp = S.obj_from_bm("StorePosters_Coupon_Print", bm, mat=S.img_mat("M_StorePosters_Coupon_Print", S.tex("poster_coupon.png"), rough=0.7))
for p in cp.data.polygons:
    p.use_smooth = True
tapes = []
for sx, sz, a in ((-1, 1, 40), (1, 1, -40), (-1, -1, -40), (1, -1, 40)):
    t = S.quad("t", 0.075, 0.022, (sx * (PW / 2 - 0.012), -0.0025 - (0.004 if sz < 0 else 0.0018), sz * (PH / 2 - 0.012)), tape,
               rot=(math.pi / 2, math.radians(a), 0))
    tapes.append(t)
tp = S.join(tapes, "StorePosters_Coupon_Tape")
S.apply_tf(tp)          # 합친 테이프의 회전을 메시에 적용 (경계 상자 정리)
# 종이는 굽지 않는 인쇄면만 있으므로 뒤판 대신 얇은 받침(벽에 남은 예전 테이프 자국)을 굽는 부모로 쓴다
old = [S.boxz("old", -0.03 + dx, 0.03 + dx, -0.0006, 0.0, PH / 2 + 0.012 + dz, PH / 2 + 0.03 + dz, m_back, 0, 0)
       for dx, dz in ((-0.18, 0.0), (0.14, 0.01))]
cpn = S.join(old, "StorePosters_Coupon")
S.set_origin(cpn, (0, 0, 0))
k3d.bake(cpn, 256, samples=16, ao=False)
for o in (cp, tp):
    S.reparent(o, cpn)
cpn.location = (4.65, BACK, 1.95)
posters.append(cpn)

# ---- 4. 로고 라이트박스 (1.5 x 0.9, 알루미늄 프로파일 45mm 깊이) + 전선 몰딩
LW, LH, LB, LD = 1.5, 0.9, 0.035, 0.045
p = mitre_frame(LW, LH, LB, -LD, -0.004, m_box, bev=0.005, seg=3)
p.append(S.boxz("bk", -LW / 2 + 0.01, LW / 2 - 0.01, -0.006, 0.0, -LH / 2 + 0.01, LH / 2 - 0.01, m_box, 0.002, 1))
for sx in (-1, 1):   # 프레임 아래 고정 나사
    p.append(S.cyl("sc", 0.0045, 0.004, (sx * (LW / 2 - 0.15), -LD / 2, -LH / 2 - 0.001), m_alu, 10, 0.001))
# 전선 몰딩: 오른쪽 위 모서리 -> 천장(3.1)
RZ = 3.1 - (2.1 + LH / 2)
p.append(S.boxz("rw", LW / 2 - 0.12, LW / 2 - 0.1, -0.012, 0.0, LH / 2 - 0.02, LH / 2 + RZ, m_raceway, 0.003, 2))
m_logo = S.img_mat("M_StorePosters_LogoPanel_Print", S.tex("logo_panel.png"), rough=0.3, emit=0.55)
finish("StorePosters_LogoPanel", p, (3.05, BACK, 2.1), FACE_BACK, m_logo, LW - 2 * LB + 0.004, LH - 2 * LB + 0.004,
       -LD + 0.012, cover_y=None)

# ---- 5-7. 오른쪽 벽 검정 액자 (외곽 0.54 x 0.74, 인쇄 0.48 x 0.68, 유리)
for nm, tx, y in (("StorePosters_RightFries", "poster_fries.png", 1.95), ("StorePosters_RightBulgogi", "poster_bulgogi.png", -0.45),
                  ("StorePosters_RightDessert", "poster_dessert.png", -2.65)):
    FW, FH, FB = 0.54, 0.74, 0.03
    p = mitre_frame(FW, FH, FB, -0.03, 0.0, m_blk, bev=0.004, seg=3)
    p += mitre_frame(FW - 2 * FB + 0.002, FH - 2 * FB + 0.002, 0.006, -0.012, 0.0, m_blk, bev=0.0015, seg=1)  # 안쪽 턱
    p.append(S.boxz("bk", -FW / 2 + 0.02, FW / 2 - 0.02, -0.006, -0.001, -FH / 2 + 0.02, FH / 2 - 0.02, m_back, 0.001, 1))
    p.append(S.boxz("hang", -0.02, 0.02, -0.001, 0.0, FH / 2 - 0.06, FH / 2 - 0.04, m_alu, 0, 0))
    m = S.img_mat("M_" + nm + "_Print", S.tex(tx), rough=0.5)
    finish(nm, p, (RIGHT, y, 2.05), FACE_RIGHT, m, 0.48, 0.68, -0.0065, cover_y=-0.0135)

# 루트 빈 오브젝트는 FBX bake_space_transform 에서 자식이 이중 회전되므로 쓰지 않는다: 포스터마다 최상위 오브젝트
socks = [S.empty("StorePosters_Socket_LookKiosk", (0.75, BACK - 0.02, 2.28)),
         S.empty("StorePosters_Socket_LookNew", (-0.05, BACK - 0.02, 2.28))]

notes = ("매장 벽 포스터 묶음. 원점 = 매장 원점(프로토타입 (0,0,0) 바닥) — StoreShell 과 같은 위치/회전(Unity (0,0,0), 회전 0)에 두면 프로토타입 자리. "
         "각 포스터는 FBX 최상위 오브젝트(StorePosters_*), 원점 = 벽에 닿는 뒷면 중앙(개별 이동 가능). "
         "뒷벽(Unity z=-4.2, 정면 +Z): StorePosters_Kiosk '주문은 키오스크에서 / 빠르고 간편합니다' A1 알루미늄 스냅 프레임(0.64x0.89) 중심 (−0.75, 2.28), "
         "StorePosters_New 신메뉴 A1 (0.05, 2.28), StorePosters_LogoPanel 로고 라이트박스 1.5x0.9 (−3.05, 2.1, 발광 0.55) + 천장까지 전선 몰딩, "
         "StorePosters_Coupon 앱 쿠폰 종이 포스터 0.5x0.72 테이프 부착(모서리 들뜸) (−4.65, 1.95). "
         "오른쪽 벽(Unity x=−5.5, 정면 +X): 검정 액자 0.54x0.74 + 유리, 높이 2.05, RightFries z=−1.95 / RightBulgogi z=0.45 / RightDessert z=2.65. "
         "인쇄면 M_StorePosters_*_Print = 1200x1700 정적 이미지(굽지 않음), 커버 M_Glass_StorePosters_Cover(투명 0.1), 테이프 M_Glass_StorePosters_Tape. "
         "min_z 경고는 매장 원점 기준이라 정상(포스터는 벽 높이에 걸림).")
k3d.export("StorePosters", "Store", posters + socks, notes=notes)
k3d.preview("StorePosters", posters, views=((20, 10), (300, 10)))

"""StoreShell: 버거대왕 매장 실내 건축 (바닥·벽·칸막이·소핏·천장·조명·덕트·소방/전기 설비·화장실 문·시계·비상구 유도등).
원점 = 매장 원점 (프로토타입 (0,0,0) 바닥). 블렌더 매장좌표 = (x, -z, y) (프로토타입 기준) -> Unity = (-x_p, y_p, z_p).
앞(유리) y=-3.8 은 비워 둔다: StorefrontFacade(커튼월·유리문)가 막는다 (파사드 원점 = 매장좌표 (0,-3.8,0))."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
import bmesh, subprocess
k3d = S.k3d
bpy = S.bpy
k3d.reset()
S.textures()

X0, X1, YF, YB, H = -6.0, 5.5, -3.8, 4.2, 3.1
CX = -2.6                 # 카운터 정면선 = 주방 경계
PY0, PY1 = -1.82, -1.70   # 칸막이벽
T = 0.15                  # 벽 두께 (바깥쪽으로)

# ---------------------------------------------------------------- 타일 머티리얼 (굽지 않음, 월드 UV)
m_floor = k3d.tile("Store_Floor", polyhaven_id="interior_tiles", res="2k", tint=(0.95, 0.93, 0.9))
m_kfloor = k3d.tile("Store_KitchenFloor", polyhaven_id="anti_skid_tiles", res="1k", tint=(0.85, 0.72, 0.62))
m_wt = k3d.tile("Store_WallTile", polyhaven_id="long_white_tiles", res="1k", tint=(0.92, 0.88, 0.8))


def tint_copy(m, name, tint):
    """같은 텍스처 세트(T_Tile_Store_WallTile_*)를 쓰는 M_Tile 복제. 색은 틴트로만 구분 (텍스처 중복 저장 방지)."""
    c = m.copy()
    c.name = name
    next(n for n in c.node_tree.nodes if n.type == 'MIX').inputs['B'].default_value = (*tint, 1)
    c["unity_tint"] = list(tint)
    return c


m_wr = tint_copy(m_wt, "M_Tile_Store_WallTileRed", (0.55, 0.07, 0.045))
m_kt = tint_copy(m_wt, "M_Tile_Store_KitchenTile", (1.0, 1.0, 1.0))
# 페인트벽: 스캔의 갈색 얼룩이 1인칭에서 물자국처럼 보여, 평균색 쪽으로 60% 당겨 대비를 줄인 사본을 쓴다
PAINT = k3d.polyhaven("painted_plaster_wall", "1k")
PAINT_DIFF = os.path.join(S.TEX, "paint_diff_soft.jpg")
if not os.path.exists(PAINT_DIFF):
    subprocess.run([S.VENV_PY, "-I", "-c", "import sys, numpy as np; from PIL import Image; "
                    "a = np.asarray(Image.open(sys.argv[1]).convert('RGB'), np.float32); m = a.mean((0, 1)); "
                    "Image.fromarray(np.clip(m + (a - m) * 0.4, 0, 255).astype(np.uint8)).save(sys.argv[2], quality=93)",
                    PAINT["diff"], PAINT_DIFF], check=True)
m_paint = k3d.tile("Store_Paint", maps=dict(PAINT, diff=PAINT_DIFF), tint=(0.9, 0.83, 0.72))
# k3d._copy_as_jpg 가 PNG 입력에서 실패하므로 노멀맵은 Pillow 로 미리 JPG 변환
NOR_JPG = S.tex("ceiling_nor.png")[:-4] + ".jpg"
if not os.path.exists(NOR_JPG):
    subprocess.run([S.VENV_PY, "-I", "-c", "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)",
                    S.tex("ceiling_nor.png"), NOR_JPG], check=True)
m_ceil = k3d.tile("Store_Ceiling", maps={"diff": S.tex("ceiling_diff.jpg"), "nor": NOR_JPG,
                                         "rough": S.tex("ceiling_rough.png")})
TILE_M = {m_floor.name: 1.9, m_kfloor.name: 1.8, m_wt.name: 1.27, m_wr.name: 1.27, m_kt.name: 1.27, m_paint.name: 2.0}


def W(x0, x1, y0, y1, z0, z1, m, bev=0.0):
    o = S.boxz("w", x0, x1, y0, y1, z0, z1, m, bev, 2)
    k3d.uv_world(o, TILE_M[m.name])
    return o


# ---------------------------------------------------------------- 벽 (안쪽 면 = 방 경계, 두께는 바깥으로)
walls = []
BAND = (1.25, 1.37)
# 뒷벽 y=4.2: 주방 구간 흰 타일 전체 높이 / 객석 구간 페인트 + 징두리 타일 + 빨간 띠
walls.append(W(X0 - T, CX, YB, YB + T, 0, H, m_kt))
walls.append(W(CX, X1 + T, YB, YB + T, 0, H, m_paint))
walls.append(W(CX, X1, YB - 0.01, YB, 0, BAND[0], m_wt))
for a, b in ((CX, -2.225), (-1.215, X1)):      # 화장실 문틀에서 끊김
    walls.append(W(a, b, YB - 0.025, YB, BAND[0], BAND[1], m_wr, 0.004))
# 오른쪽 벽 x=5.5
walls.append(W(X1, X1 + T, YF, YB + T, 0, H, m_paint))
walls.append(W(X1 - 0.01, X1, YF, YB, 0, BAND[0], m_wt))
walls.append(W(X1 - 0.025, X1, YF, YB, BAND[0], BAND[1], m_wr, 0.004))
# 왼쪽 벽 x=-6: 주방(칸막이 뒤) 흰 타일 / 앞쪽 객석 구간 페인트 + 징두리
walls.append(W(X0 - T, X0, PY0, YB + T, 0, H, m_kt))
walls.append(W(X0 - T, X0, YF, PY0, 0, H, m_paint))
walls.append(W(X0, X0 + 0.01, YF, PY0, 0, BAND[0], m_wt))
walls.append(W(X0, X0 + 0.025, YF, PY0, BAND[0], BAND[1], m_wr, 0.004))
# 칸막이벽 (주방 | 객석), 전체 높이
walls.append(W(X0, CX, PY0, PY1, 0, H, m_paint))
walls.append(W(X0, -3.33, PY1, PY1 + 0.01, 0, H, m_kt))
walls.append(W(X0, CX, PY0 - 0.01, PY0, 0, BAND[0], m_wt))
walls.append(W(X0, CX, PY0 - 0.025, PY0, BAND[0], BAND[1], m_wr, 0.004))
# 카운터 위 소핏 (앞면 x=-2.62, 바닥 z=2.2): 메뉴판·주문번호판이 앞면에 붙는다
walls.append(W(-2.86, -2.62, PY1, YB, 2.2, H, m_paint))
wall_obj = S.join(walls, "StoreShell_Walls")
S.set_origin(wall_obj, (0, 0, 0))

# ---------------------------------------------------------------- 바닥
f1 = S.floor_quad("f", X1 - CX, YB - YF, ((X1 + CX) / 2, (YB + YF) / 2, 0), m_floor)
f2 = S.floor_quad("f", CX - X0, -1.76 - YF, ((CX + X0) / 2, (-1.76 + YF) / 2, 0), m_floor)
for o in (f1, f2):
    k3d.uv_world(o, 1.9)
    for l in o.data.uv_layers[0].data:   # 스캔이 45도 마름모 배치라 UV 를 45도 돌려 정사각 줄눈(약 0.45m)으로
        u, v = l.uv
        l.uv = ((u + v) / math.sqrt(2), (v - u) / math.sqrt(2))
floor = S.join([f1, f2], "StoreShell_Floor")
S.set_origin(floor, (0, 0, 0))
kf = S.floor_quad("StoreShell_KitchenFloor", CX - X0, YB + 1.76, ((CX + X0) / 2, (YB - 1.76) / 2, 0), m_kfloor)
k3d.uv_world(kf, 1.8)

# ---------------------------------------------------------------- 천장 (600 T-bar, 조명 칸은 뚫음)
PANELS = [(x, y, 1.2, 0.6) for x in (-1.8, 1.2, 3.6) for y in (3.0, 0.6, -1.8)]       # 1200x600 평판등
PANELS += [(-4.5, y, 0.6, 1.2) for y in (3.3, 1.5, -0.9)]                           # 주방 (세로)
FLICKER = (1.2, 0.6)                                                               # 프로토타입 깜빡이는 등 (1, -0.8)
xs = [X0 + 0.6 * i for i in range(20) if X0 + 0.6 * i < X1] + [X1]
ys = [YF] + [0.3 + 0.6 * k for k in range(-6, 7)] + [YB]
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
for i in range(len(xs) - 1):
    for j in range(len(ys) - 1):
        cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
        if any(abs(cx - px) < pw / 2 and abs(cy - py) < ph / 2 for px, py, pw, ph in PANELS):
            continue
        v = [bm.verts.new((x, y, H)) for x, y in ((xs[i], ys[j]), (xs[i], ys[j + 1]), (xs[i + 1], ys[j + 1]), (xs[i + 1], ys[j]))]
        bm.faces.new(v)   # 시계 방향 = 아래(-Z)를 봄
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
ceil = S.obj_from_bm("StoreShell_Ceiling", bm, mat=m_ceil)
k3d.uv_world(ceil, 2.4)
for l in ceil.data.uv_layers[0].data:   # T-bar 선을 y = 0.3 + 0.6k 에 맞춤
    l.uv = (l.uv[0], l.uv[1] + 0.125)

# ---------------------------------------------------------------- 설비 (굽기 1장)
m_white = S.pbr("M_tmp_SHWhite", (0.8, 0.8, 0.78), 0.45, var=0.05, grime=0.5, gdist=0.03, streak=0.15,
                edge=0.2, edge_col=(0.9, 0.9, 0.88), bump=0.02)
m_base = S.pbr("M_tmp_SHBaseboard", (0.032, 0.031, 0.03), 0.55, var=0.1, grime=0.6, grime_col=(0.1, 0.09, 0.07),
               scratch=0.8, edge=0.4, edge_col=(0.12, 0.12, 0.11), bump=0.05, bscale=200)
m_alu = S.pbr("M_tmp_SHAlu", (0.6, 0.61, 0.62), 0.35, 1.0, var=0.05, grime=0.55, gdist=0.03, edge=0.5,
              edge_col=(0.85, 0.85, 0.86), scratch=0.5, brush=0.12, smudge=0.3, bump=0.01)
m_red = S.pbr("M_tmp_SHRed", (0.42, 0.035, 0.022), 0.4, var=0.08, grime=0.45, edge=0.6, edge_col=(0.6, 0.5, 0.45),
              scratch=0.3, bump=0.04)
m_dark = S.pbr("M_tmp_SHDark", (0.012, 0.012, 0.014), 0.6, grime=0.2, bump=0)
m_dome = S.pbr("M_tmp_SHDome", (0.01, 0.01, 0.012), 0.08, grime=0.0, smudge=0.3, bump=0)
m_chrome = S.pbr("M_tmp_SHChrome", (0.8, 0.8, 0.8), 0.15, 1.0, grime=0.4, bump=0)
m_bulb = S.pbr("M_tmp_SHBulbRed", (0.6, 0.02, 0.01), 0.1, grime=0.0, bump=0)
m_lamp = S.pbr("M_tmp_SHLamp", (0.6, 0.03, 0.02), 0.3, grime=0.1, bump=0, emission=(1.0, 0.08, 0.03), estr=2.0)
m_grille = S.pbr("M_tmp_SHGrille", (0.62, 0.62, 0.6), 0.5, var=0.06, grime=0.6, gdist=0.02, bump=0.5, bscale=900)
m_galv = S.pbr("M_tmp_SHGalv", (0.55, 0.56, 0.57), 0.38, 1.0, var=0.2, vscale=40, grime=0.5, gdist=0.08,
               streak=0.3, edge=0.3, edge_col=(0.75, 0.75, 0.76), bump=0.03, bscale=120)
m_paintdoor = S.pbr("M_tmp_SHDoorPaint", (0.21, 0.22, 0.225), 0.42, var=0.06, grime=0.5, gdist=0.03, edge=0.6,
                    edge_col=(0.45, 0.45, 0.44), scratch=0.5, smudge=0.5, bump=0.02)
m_mat = S.pbr("M_tmp_SHDoorMat", (0.03, 0.029, 0.028), 0.92, var=0.2, vscale=30, grime=0.3, bump=0.5, bscale=350,
              edge=0.4, edge_col=(0.06, 0.06, 0.06))
m_switch = S.pbr("M_tmp_SHSwitch", (0.82, 0.81, 0.77), 0.35, grime=0.6, gdist=0.01, smudge=0.6, bump=0)

fx = []
B = S.boxz
# 걸레받이 (비닐, 100mm)
for a in ((-2.584, -2.235, YB - 0.022, YB - 0.01), (-1.205, X1 - 0.01, YB - 0.022, YB - 0.01),
          (X1 - 0.022, X1 - 0.01, YF, YB - 0.022), (X0 + 0.01, X0 + 0.022, YF, PY0 - 0.01),
          (X0 + 0.022, CX + 0.012, PY0 - 0.022, PY0 - 0.01), (CX, CX + 0.012, PY0 - 0.01, PY1)):
    fx.append(B("bb", a[0], a[1], a[2], a[3], 0, 0.1, m_base, 0.004, 3))
# 칸막이 모서리 스테인리스 코너가드
fx.append(B("cg", CX, CX + 0.002, PY0 - 0.012, PY0 + 0.02, 0.1, 1.25, m_alu, 0.0008, 1))
fx.append(B("cg", CX - 0.03, CX + 0.002, PY0 - 0.014, PY0 - 0.012, 0.1, 1.25, m_alu, 0.0008, 1))
# 소핏 아래 빨간 몰딩
fx.append(B("st", -2.875, -2.605, PY1, YB, 2.175, 2.225, m_red, 0.004, 3))
# 화장실 문틀 (알루미늄)
for a, b in ((-2.23, -2.18), (-1.26, -1.21)):
    fx.append(B("jamb", a, b, YB - 0.08, YB - 0.01, 0, 2.15, m_alu, 0.004, 2))
fx.append(B("head", -2.23, -1.21, YB - 0.08, YB - 0.01, 2.1, 2.15, m_alu, 0.004, 2))
fx.append(B("stop", -2.18, -1.26, YB - 0.03, YB - 0.01, 2.08, 2.1, m_alu, 0.002, 1))
# 스위치 (2구, 문 왼쪽)
fx.append(B("sw", -2.42, -2.34, YB - 0.02, YB - 0.01, 1.15, 1.27, m_switch, 0.004, 2))
for sx in (-2.398, -2.362):
    fx.append(B("swk", sx - 0.014, sx + 0.014, YB - 0.026, YB - 0.02, 1.17, 1.25, m_switch, 0.003, 2))
# 화재 발신기·경종·표시등 (오른쪽 벽)
fy = -1.55
fx.append(B("fa_box", X1 - 0.05, X1, fy - 0.07, fy + 0.07, 0.98, 1.16, m_red, 0.006, 2))
fx.append(B("fa_btn", X1 - 0.056, X1 - 0.05, fy - 0.025, fy + 0.025, 1.04, 1.09, m_white, 0.003, 2))
fx.append(S.cyl("fa_bell", 0.075, 0.05, (X1 - 0.025, fy, 1.33), m_red, 32, 0.01, 3, rot=(0, math.pi / 2, 0)))
fx.append(S.cyl("fa_bellc", 0.012, 0.012, (X1 - 0.056, fy, 1.33), m_chrome, 12, 0.002, rot=(0, math.pi / 2, 0)))
fx.append(S.cyl("fa_lampb", 0.04, 0.02, (X1 - 0.01, fy, 1.52), m_red, 24, 0.003, rot=(0, math.pi / 2, 0)))
fx.append(S.cyl("fa_lamp", 0.028, 0.03, (X1 - 0.03, fy, 1.52), m_lamp, 24, 0.008, 3, rot=(0, math.pi / 2, 0)))


def grille(cx, cy, cz, w, h, face):
    """벽 환기 그릴 (face='x' 면 -X 를 봄, 'y' 면 -Y 를 봄). 프레임 + 기울어진 루버 + 어두운 안쪽."""
    out = []
    def bx(u0, u1, d0, d1, z0, z1, m, bev, seg=2, rot=0.0):
        if face == 'x':
            o = B("g", cx - d1, cx - d0, cy + u0, cy + u1, cz + z0, cz + z1, m, bev, seg)
        else:
            o = B("g", cx + u0, cx + u1, cy - d1, cy - d0, cz + z0, cz + z1, m, bev, seg)
        return o
    out.append(bx(-w / 2, w / 2, 0, 0.004, -h / 2, h / 2, m_dark, 0))
    for z0, z1 in ((-h / 2, -h / 2 + 0.025), (h / 2 - 0.025, h / 2)):
        out.append(bx(-w / 2, w / 2, 0, 0.016, z0, z1, m_white, 0.003))
    for u0, u1 in ((-w / 2, -w / 2 + 0.025), (w / 2 - 0.025, w / 2)):
        out.append(bx(u0, u1, 0, 0.016, -h / 2 + 0.025, h / 2 - 0.025, m_white, 0.003))
    n = int((h - 0.05) / 0.03)
    for k in range(n):
        z = -h / 2 + 0.025 + (k + 0.5) * (h - 0.05) / n
        lv = bx(-w / 2 + 0.025, w / 2 - 0.025, 0.004, 0.014, z - 0.012, z + 0.012, m_white, 0.0015, 1)
        # 루버 기울이기 (긴 축 기준 35도)
        lv.rotation_euler = (0, math.radians(35), 0) if face == 'x' else (math.radians(-35), 0, 0)
        out.append(lv)
    return out


fx += grille(X1, 0.75, 2.77, 0.6, 0.3, 'x')
fx += grille(4.6, YB, 2.8, 0.6, 0.3, 'y')


def sqframe(cx, cy, s, b, z0, z1, m):
    return [B("d", cx - s / 2, cx + s / 2, cy - s / 2, cy - s / 2 + b, z0, z1, m, 0.003),
            B("d", cx - s / 2, cx + s / 2, cy + s / 2 - b, cy + s / 2, z0, z1, m, 0.003),
            B("d", cx - s / 2, cx - s / 2 + b, cy - s / 2 + b, cy + s / 2 - b, z0, z1, m, 0.003),
            B("d", cx + s / 2 - b, cx + s / 2, cy - s / 2 + b, cy + s / 2 - b, z0, z1, m, 0.003)]


def diffuser(cx, cy, ztop):
    """4방향 사각 디퓨저 (계단식 콘). ztop = 덕트 바닥."""
    out = [B("dn", cx - 0.17, cx + 0.17, cy - 0.17, cy + 0.17, ztop - 0.1, ztop + 0.01, m_galv, 0.004)]
    out.append(B("db", cx - 0.23, cx + 0.23, cy - 0.23, cy + 0.23, ztop - 0.105, ztop - 0.1, m_dark, 0))
    z = ztop - 0.1
    for s, b in ((0.5, 0.045), (0.39, 0.04), (0.29, 0.035)):
        out += sqframe(cx, cy, s, b, z - 0.022, z, m_white)
        z -= 0.012
    out.append(B("dc", cx - 0.055, cx + 0.055, cy - 0.055, cy + 0.055, z - 0.024, z, m_white, 0.004))
    return out


# 평판등 테두리 (천장 구멍 안쪽 띠 + 플랜지)
for px, py, pw, ph in PANELS:
    x0, x1, y0, y1 = px - pw / 2, px + pw / 2, py - ph / 2, py + ph / 2
    for a in ((x0, x1, y0, y0 + 0.025), (x0, x1, y1 - 0.025, y1), (x0, x0 + 0.025, y0 + 0.025, y1 - 0.025),
              (x1 - 0.025, x1, y0 + 0.025, y1 - 0.025)):
        fx.append(B("tf", a[0], a[1], a[2], a[3], H - 0.006, H + 0.035, m_white, 0.002, 1))
# 매입 다운라이트 테 (객석 앞쪽·입구)
DOWN = [(-4.5, -3.0), (-3.3, -3.0), (-0.3, -3.0), (1.5, -3.0), (4.5, -3.0)]
for x, y in DOWN:
    fx.append(S.cyl("dl", 0.095, 0.012, (x, y, H - 0.006), m_white, 32, 0.003))
# 스프링클러 헤드
for x, y in ((-0.3, 2.4), (-0.3, -2.4), (4.5, 1.2), (4.5, -2.4), (-3.9, 0.6), (-3.9, 3.0)):
    fx.append(S.cyl("sp_e", 0.03, 0.006, (x, y, H - 0.003), m_chrome, 20, 0.002))
    fx.append(S.cyl("sp_b", 0.008, 0.03, (x, y, H - 0.021), m_chrome, 10, 0.001))
    for s in (-1, 1):
        fx.append(B("sp_a", x + s * 0.009 - 0.0015, x + s * 0.009 + 0.0015, y - 0.0015, y + 0.0015, H - 0.045, H - 0.02, m_chrome, 0))
    fx.append(S.cyl("sp_d", 0.016, 0.002, (x, y, H - 0.046), m_chrome, 16, 0))
    fx.append(S.cyl("sp_g", 0.0028, 0.016, (x, y, H - 0.034), m_bulb, 8, 0))
# 천장 스피커
for x, y in ((-0.3, 1.2), (4.5, 1.8)):
    fx.append(S.cyl("spk_f", 0.105, 0.008, (x, y, H - 0.004), m_white, 40, 0.002))
    fx.append(S.cyl("spk_g", 0.088, 0.004, (x, y, H - 0.010), m_grille, 40, 0.001))
# CCTV 돔 (키오스크 쪽을 봄)
CC = (-0.9, 0.6)
fx.append(S.cyl("cc_base", 0.07, 0.025, (CC[0], CC[1], H - 0.0125), m_white, 32, 0.004, 2))
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=0.058, calc_uvs=True)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1e-4], context='VERTS')
dome = S.obj_from_bm("cc_dome", bm, (CC[0], CC[1], H - 0.024), mat=m_dome)
for p in dome.data.polygons:
    p.use_smooth = True
fx.append(dome)
# 천장 PIR 센서 (문 차임)
fx.append(S.cyl("pir", 0.04, 0.02, (1.4, -3.45, H - 0.01), m_white, 24, 0.004))
fx.append(S.cyl("pir_l", 0.022, 0.012, (1.4, -3.45, H - 0.024), m_switch, 16, 0.005, 2))
# 비상구 유도등 (천장에 매단 박스, 안쪽 +Y 를 봄)
fx.append(B("ex", 1.17, 1.63, -3.74, -3.68, 2.735, 2.905, m_white, 0.006, 2))
for x in (1.25, 1.55):
    fx.append(S.cyl("ex_r", 0.005, H - 2.905, (x, -3.71, (H + 2.905) / 2), m_alu, 8, 0))
    fx.append(S.cyl("ex_c", 0.02, 0.01, (x, -3.71, H - 0.005), m_alu, 16, 0.002))
# 에어커튼 (문 위, 천장에서 매닮)
fx.append(B("ac", 0.9, 1.9, -3.75, -3.55, 2.42, 2.62, m_white, 0.012, 3))
fx.append(B("ac_s", 0.96, 1.84, -3.72, -3.6, 2.414, 2.42, m_dark, 0.002, 1))
fx.append(B("ac_p", 1.72, 1.82, -3.551, -3.548, 2.56, 2.6, m_dark, 0.001, 1))
for x in (1.0, 1.8):
    fx.append(S.cyl("ac_r", 0.006, H - 2.62, (x, -3.65, (H + 2.62) / 2), m_alu, 8, 0))
# 시계 테두리
CL = (1.55, YB, 2.62)
fx.append(S.cyl("cl_b", 0.17, 0.035, (CL[0], YB - 0.0175, CL[2]), m_dark, 48, 0.006, 3, rot=(math.pi / 2, 0, 0)))
bpy.ops.mesh.primitive_torus_add(major_radius=0.158, minor_radius=0.008, major_segments=48, minor_segments=8,
                                 location=(CL[0], YB - 0.036, CL[2]), rotation=(math.pi / 2, 0, 0))
rim = bpy.context.active_object
rim.data.materials.append(m_dark)
fx.append(rim)
fixtures = S.join(fx, "StoreShell_Fixtures")
S.set_origin(fixtures, (0, 0, 0))

# ---- 노출 덕트 (아연도 스파이럴 덕트 + 플랜지 + 행거 + 디퓨저)
du = []
E = H - 0.34
du.append(S.cyl("d_main", 0.2, YB + 0.05 + 3.2, (2.3, (YB + 0.05 - 3.2) / 2, E), m_galv, 32, 0.002, rot=(math.pi / 2, 0, 0)))
du.append(S.cyl("d_riser", 0.2, H - (E - 0.2), (2.3, -3.2, (H + E - 0.2) / 2), m_galv, 32, 0.004, 2))
y = YB - 0.6
while y > -3.0:
    du.append(S.cyl("d_fl", 0.212, 0.04, (2.3, y, E), m_galv, 32, 0.004, 2, rot=(math.pi / 2, 0, 0)))
    du.append(S.cyl("d_hg", 0.006, H - E - 0.2, (2.3, y, (H + E + 0.2) / 2), m_alu, 8, 0))
    y -= 1.1
du.append(S.cyl("d_fl", 0.212, 0.04, (2.3, -3.2, E + 0.25), m_galv, 32, 0.004, 2))
du.append(S.cyl("d_cross", 0.13, 3.1, (0.75, 1.9, E + 0.06), m_galv, 24, 0.002, rot=(0, math.pi / 2, 0)))
du.append(S.cyl("d_cap", 0.138, 0.03, (-0.8, 1.9, E + 0.06), m_galv, 24, 0.004, 2, rot=(0, math.pi / 2, 0)))
du.append(S.cyl("d_fl2", 0.14, 0.035, (2.05, 1.9, E + 0.06), m_galv, 24, 0.004, 2, rot=(0, math.pi / 2, 0)))
for x in (-0.3, 1.0):
    du.append(S.cyl("d_hg2", 0.006, H - E - 0.19, (x, 1.9, (H + E + 0.19) / 2), m_alu, 8, 0))
for y in (2.3, -0.2, -2.5):
    du += diffuser(2.3, y, E - 0.19)
du += diffuser(-0.6, 1.9, E + 0.06 - 0.12)
duct = S.join(du, "StoreShell_Duct")
S.set_origin(duct, (0, 0, 0))

# ---- 화장실 문 (원점 = 경첩 축 바닥, 고정이지만 열 수 있게 분리)
DX, DW = -2.18, 0.92
dp = [B("leaf", 0, DW, -0.04, 0, 0, 2.098, m_paintdoor, 0.004, 2)]
dp.append(B("kick", 0.01, DW - 0.01, -0.0415, -0.04, 0.01, 0.26, m_alu, 0.001, 1))
dp.append(S.cyl("rose", 0.028, 0.012, (DW - 0.12, -0.046, 1.02), m_alu, 24, 0.003, rot=(math.pi / 2, 0, 0)))
dp.append(S.cyl("neck", 0.009, 0.035, (DW - 0.12, -0.065, 1.02), m_alu, 12, 0.002, rot=(math.pi / 2, 0, 0)))
dp.append(B("lever", DW - 0.245, DW - 0.11, -0.092, -0.074, 1.011, 1.029, m_alu, 0.006, 3))
dp.append(S.cyl("turn", 0.022, 0.01, (DW - 0.12, -0.045, 1.22), m_alu, 20, 0.003, rot=(math.pi / 2, 0, 0)))
dp.append(B("turn_k", DW - 0.128, DW - 0.112, -0.058, -0.05, 1.205, 1.235, m_alu, 0.002, 1))
dp.append(B("closer", 0.05, 0.33, -0.1, -0.042, 1.98, 2.035, m_alu, 0.008, 2))
dp.append(B("arm", 0.28, 0.5, -0.088, -0.072, 2.04, 2.052, m_alu, 0.003, 1))
for z in (0.25, 1.05, 1.85):
    dp.append(S.cyl("hinge", 0.008, 0.1, (-0.002, -0.02, z), m_alu, 12, 0.002))
door = S.join(dp, "StoreShell_RestroomDoor")
S.set_origin(door, (0, 0, 0))
door.location = (DX, YB - 0.005, 0)

# ---- 출입구 매트
mat = B("StoreShell_DoorMat", 0.65, 2.15, -3.72, -2.67, 0.0, 0.004, m_mat, 0.002, 2)
mat = S.join([mat], "StoreShell_DoorMat")
S.set_origin(mat, (1.4, -3.195, 0))

k3d.bake(fixtures, 2048, samples=32, ao_distance=0.06)
k3d.bake(duct, 1024, samples=32, ao_distance=0.15)
k3d.bake(door, 1024, samples=32, ao_distance=0.05)
k3d.bake(mat, 512, samples=16, ao=False)

# ---------------------------------------------------------------- 발광/사인 (굽지 않음)
m_led = k3d.mat("M_StoreShell_LightPanel", (0.95, 0.96, 0.98), 0.35, emission=(0.92, 0.96, 1.0), strength=3.2)
m_flk = k3d.mat("M_StoreShell_LightFlicker", (0.95, 0.96, 0.98), 0.35, emission=(0.92, 0.96, 1.0), strength=3.2)
leds, flk = [], None
for px, py, pw, ph in PANELS:
    q = S.floor_quad("led", pw - 0.05, ph - 0.05, (px, py, H + 0.03), m_flk if (px, py) == FLICKER else m_led)
    q.rotation_euler = (math.pi, 0, 0)  # 아래를 봄
    if (px, py) == FLICKER:
        flk = q
    else:
        leds.append(q)
for x, y in DOWN:
    d = S.cyl("dlg", 0.07, 0.002, (x, y, H - 0.0135), m_led, 32, 0)
    leds.append(d)
lights = S.join(leds, "StoreShell_LightPanels")
S.set_origin(lights, (0, 0, 0))
flk = S.join([flk], "StoreShell_LightFlicker")
S.set_origin(flk, (FLICKER[0], FLICKER[1], H))

A = "shell_signs.png"
m_sign = S.img_mat("M_StoreShell_Signs", S.tex(A), rough=0.45)
m_exit = S.img_mat("M_StoreShell_ExitGlow", S.tex(A), rough=0.3, emit=1.6)
sg = []
sg.append(S.quad("s_cctv", 0.21, 0.15, (X1 - 0.002, -3.35, 1.6), m_sign, rot=(math.pi / 2, 0, -math.pi / 2), uv=S.atlas_uv(A, "cctv")))
sg.append(S.quad("s_exit", 0.44, 0.15, (1.4, -3.68 + 0.0015, 2.82), m_exit, rot=(math.pi / 2, 0, math.pi), uv=S.atlas_uv(A, "exit")))


def disc_uv(name, r, loc, rot, mat, uvr, n=48):
    """원판 + 아틀라스 사각형 안 원형 UV."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    c = bm.verts.new((0, 0, 0))
    ring = [bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)) for a in (i / n * math.tau for i in range(n))]
    u0, v0, u1, v1 = uvr
    for i in range(n):
        f = bm.faces.new((c, ring[i], ring[(i + 1) % n]))
        for l in f.loops:
            x, y = l.vert.co.x / (2 * r) + 0.5, l.vert.co.y / (2 * r) + 0.5
            l[uvl].uv = (u0 + x * (u1 - u0), v0 + y * (v1 - v0))
    o = S.obj_from_bm(name, bm, loc, rot, mat)
    return o


sg.append(disc_uv("s_clock", 0.158, (CL[0], YB - 0.0365, CL[2]), (math.pi / 2, 0, 0), m_sign, S.atlas_uv(A, "clock")))


def rrect_decal(name, w, h, r, loc, mat, uvr, seg=8):
    """둥근 사각 스티커 (아틀라스의 검은 모서리가 보이지 않게 모양을 자름). 위(+Z)를 봄, V = +Y."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])
    u0, v0, u1, v1 = uvr
    for l in f.loops:
        l[uvl].uv = (u0 + (l.vert.co.x / w + 0.5) * (u1 - u0), v0 + (l.vert.co.y / h + 0.5) * (v1 - v0))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return S.obj_from_bm(name, bm, loc, None, mat)


sg.append(rrect_decal("s_wait", 0.7, 0.3, 0.04, (-0.6, 1.77, 0.0015), m_sign, S.atlas_uv(A, "wait")))
signs = S.join(sg, "StoreShell_Signs")
S.set_origin(signs, (0, 0, 0))
glass = k3d.mat("M_Glass_StoreShell_ClockGlass", (0.92, 0.94, 0.96), 0.04, alpha=0.12)
cg = S.cyl("StoreShell_ClockGlass", 0.152, 0.002, (CL[0], YB - 0.04, CL[2]), glass, 48, 0, rot=(math.pi / 2, 0, 0))
cg = S.join([cg], "StoreShell_ClockGlass")
dsg = S.quad("StoreShell_RestroomDoor_Sign", 0.3, 0.1, (DX + DW / 2, YB - 0.005 - 0.0415, 1.55), m_sign, uv=S.atlas_uv(A, "restroom"))

# ---------------------------------------------------------------- 계층 / 소켓
root = floor
for o in (kf, wall_obj, ceil, fixtures, duct, door, mat, lights, flk, signs, cg):
    S.reparent(o, root)
# 손자 오브젝트는 FBX bake_space_transform 에서 이중 회전되므로 표지를 문 메시에 합친다 (문과 같이 움직임)
door = S.join([door, dsg], "StoreShell_RestroomDoor")
sock = {
    "FacadeOrigin": (0, YF, 0), "DoorChime": (1.4, -3.75, 2.2), "Queue0": (-0.6, 1.77, 0), "CCTVLook": (CC[0], CC[1], H - 0.05),
    "Light_A": (1.0, 2.2, 2.7), "Light_B": (3.6, -1.0, 2.7), "Light_C": (-0.6, -1.6, 2.7), "Light_Kitchen": (-4.4, 1.0, 2.5),
}
for k, p in sock.items():
    S.empty("StoreShell_Socket_" + k, p, root)

notes = {
    "pivot": "원점 = 매장 원점(프로토타입 (0,0,0) 바닥). Unity 에 (0,0,0) 회전 0 으로 두면 프로토타입과 같은 자리. 블렌더 (x,y,z) -> Unity (-x, z, -y) = 프로토 (x_p,y_p,z_p) -> Unity (-x_p, y_p, z_p).",
    "size": "방 x -6~5.5, z -4.2~3.8(유리선), 높이 3.1. 벽 두께 0.15 는 방 바깥쪽. 앞(유리선)은 비어 있음: StorefrontFacade 를 StoreShell_Socket_FacadeOrigin(Unity (0,0,3.8)) 에 회전 0 으로 둔다.",
    "layout": "주방 = 프로토 x -6~-2.6, z -4.2~1.7 (논슬립 타일 바닥·흰 타일 벽). 칸막이벽 z 1.70~1.82. 카운터 위 소핏 앞면 프로토 x=-2.62, 바닥 2.2 (StoreMenuBoard/StoreOrderBoard 를 앞면에 붙임). 화장실 문 뒷벽 x=-1.72 (장식, 뒤는 막힘).",
    "materials": "벽/바닥/천장 = M_Tile_Store_* (월드 UV, Floor 1.9m·KitchenFloor 1.8m·WallTile/Red/KitchenTile 1.27m·Paint 2m·Ceiling 2.4m=600 T-bar 4x4). WallTileRed·KitchenTile 은 T_Tile_Store_WallTile_* 텍스처를 같이 쓰고 JSON baseColor 틴트로만 색을 구분한다. 설비 StoreShell_Fixtures(2048 굽기), 덕트 StoreShell_Duct(1024), 문 StoreShell_RestroomDoor(1024, 원점=경첩축), 매트 512.",
    "lights": "평판등 12개(1200x600, 객석 9 + 주방 3) + 다운라이트 5 = StoreShell_LightPanels (M_StoreShell_LightPanel 발광 3.2). 프로토타입에서 깜빡이는 등(프로토 (1,-0.8)) = StoreShell_LightFlicker 따로, 머티리얼 M_StoreShell_LightFlicker 의 발광 세기를 게임에서 깜빡이면 된다. 실제 포인트 라이트 자리 = StoreShell_Socket_Light_*.",
    "signs": "StoreShell_Signs: CCTV 안내(오른쪽 벽), 비상구 유도등 면(M_StoreShell_ExitGlow 발광 1.6, 문 위 천장에 매단 박스), 시계(11:42), 바닥 스티커 '이곳에서 기다려 주세요'(키오스크 대기 첫 자리, 프로토 (-0.6, -1.77)). 화장실 문 표지는 문 메시에 포함(머티리얼 슬롯 M_StoreShell_Signs).",
    "sockets": "FacadeOrigin(파사드 원점), DoorChime(문 차임 소리), Queue0(대기 첫 자리), CCTVLook(돔 카메라), Light_A/B/C/Kitchen(프로토 포인트 라이트 위치).",
}
k3d.export("StoreShell", "Store", [root], notes=notes)
k3d.preview("StoreShell", [root], views=((30, 35),))

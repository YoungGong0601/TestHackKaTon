"""PH_CafeRoom__Shell: 카페 방 껍데기(벽, 바닥, 천장, 징두리, 바 끝 칸막이, 천장 등 5개).
Env_Cafe 에 씬 원점, 회전 0 으로 둔다. 아래 수치는 전부 Unity 씬 좌표이고 W() 가 소스 (x, z, y) 로 바꾼다."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Store")]
import ph, storelib as S, bpy
k3d = ph.k3d

k3d.reset()
A = "PH_CafeRoom__Shell"
TDIR = os.path.join(k3d.ART, "Textures", "Tile")
TILE_M, parts = {}, []


def tile(src, name, tint, tile_m):
    """공유 텍스처를 그대로 쓰는 틴트 사본(store_shell.py tint_copy). 텍스처 파일은 늘지 않는다."""
    m = k3d.tile(src, maps={"diff": os.path.join(TDIR, f"T_Tile_{src}_BaseColor.jpg")}, tint=(1, 1, 1))
    c = m.copy()
    c.name = "M_Tile_Cafe_" + name
    next(n for n in c.node_tree.nodes if n.type == 'MIX').inputs['B'].default_value = (*tint, 1)
    c["unity_tint"] = list(tint)
    TILE_M[c.name] = tile_m
    return c


def W(x0, x1, y0, y1, z0, z1, m):
    o = S.boxz("w", x0, x1, z0, z1, y0, y1, m, 0)
    bpy.context.view_layer.update()  # uv_world 가 matrix_world 를 읽는다
    if m.name in TILE_M:
        k3d.uv_world(o, TILE_M[m.name])
    parts.append(o)


def strip(run, a, b, y0, y1, d, m):
    """벽면에서 d 만큼 튀어나온 띠. 뒤쪽 1cm 는 벽 속에 묻어 벽면과 같은 면이 생기지 않는다."""
    ax, w, s = run
    lo, hi = sorted((w - s * 0.01, w + s * d))
    W(*((lo, hi, y0, y1, a, b) if ax == "x" else (a, b, y0, y1, lo, hi)), m)


m_floor = tile("Home_WoodFloor", "RoomFloor", (0.82, 0.74, 0.66), 1.7)
m_wall = tile("Store_Paint", "RoomWall", (1.0, 0.95, 0.84), 2.0)
m_brick = tile("Buildings_RedBrick", "RoomBrick", (0.9, 0.84, 0.8), 1.4)
m_ceil = tile("Home_Ceiling", "RoomCeiling", (1.0, 1.0, 1.0), 1.06)
m_wood = tile("Home_WoodFloor", "RoomWood", (0.9, 0.8, 0.68), 1.7)
m_dark = tile("Home_WoodFloor", "RoomDarkWood", (0.3, 0.24, 0.2), 1.7)
# 발광 없는 재질도 검정을 지정한다. 기본 Emission Color 가 흰색이라 그대로 두면 발광 맵이 하얗게 구워진다
m_green = k3d.mat("M_PH_CafeRoom__Shell_Green", (0.0137, 0.1046, 0.0595), 0.55, emission=(0, 0, 0))  # #1F5B45
m_lamp = k3d.mat("M_PH_CafeRoom__Shell_LampBody", (0.02, 0.02, 0.018), 0.4, 0.8, emission=(0, 0, 0))
m_glow = k3d.mat("M_PH_CafeRoom__Shell_LampGlow", (1.0, 0.9, 0.75), 0.4, emission=(1.0, 0.86, 0.66), strength=3.0)

# 구조체. 벽끼리, 벽과 바닥, 천장은 서로 파고들어 틈이 없다. 바깥 면이 겹치지 않게 바닥, 천장, 뒷벽은 1cm 안쪽에서 끝난다
W(-4.64, 3.24, -0.1, 0, -3.025, 3.99, m_floor)
W(-4.64, 3.24, 3.2, 3.4, -3.015, 3.99, m_ceil)   # 앞면이 벽 끝면과 같은 면이면 지글거려서 1cm 뒤로
W(-4.65, -4.55, -0.1, 3.3, -3.025, 3.975, m_wall)
W(3.15, 3.25, -0.1, 3.3, -3.025, 3.975, m_wall)
W(-4.64, 0.76, -0.1, 3.3, 3.9, 4.0, m_brick)
W(0.76, 3.24, -0.1, 3.3, 3.9, 4.0, m_wall)
W(0.72, 0.8, 0, 1.06, 2.205, 3.955, m_dark)     # Wall_BarEnd
W(0.73, 0.79, 1.05, 3.21, 3.88, 3.91, m_dark)   # 벽돌과 페인트 경계를 덮는 띠

# 징두리. 바 뒤 벽돌에는 선반이 서서 두지 않는다. 뒷벽은 키오스크 본체(x 1.57~2.23, 뒷면 z 3.877~3.888) 자리를 비운다
WEST, EAST, BACK = ("x", -4.55, 1), ("x", 3.15, -1), ("z", 3.9, -1)
for run, a, b in ((WEST, -3.02, 3.91), (EAST, -3.02, 3.91), (BACK, 0.78, 1.555), (BACK, 2.245, 3.16)):
    strip(run, a, b, 0, 1.0, 0.006, m_green)
    strip(run, a, b, 0, 0.12, 0.022, m_dark)
    strip(run, a, b, 0.96, 1.03, 0.032, m_wood)
    n = round((b - a) / 0.55)
    for i in range(1, n):
        c = a + (b - a) * i / n
        strip(run, c - 0.025, c + 0.025, 0.12, 0.96, 0.018, m_green)

LAMPS = ((-2.6, -1.6), (1.9, -0.8), (-1.2, 0.6), (1.9, 2.6), (-2.6, 2.6))
for x, z in LAMPS:
    parts.append(S.cyl("lamp", 0.175, 0.09, (x, z, 3.16), m_lamp, 32, 0))   # 윗면 5mm 는 천장 속
    parts.append(S.cyl("glow", 0.155, 0.02, (x, z, 3.11), m_glow, 32, 0))

o = ph.part(A, parts, ph.turn(180))
for p in parts:  # ph.part 는 복사본을 합친다. 원본이 남으면 AO 와 미리보기에 뒤집힌 방이 하나 더 들어간다
    bpy.data.objects.remove(p)
vs = [v.co for v in o.data.vertices]
lo, hi = [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
got = [round(v, 3) for v in (-hi[0], -lo[0], lo[2], hi[2], -hi[1], -lo[1])]  # Unity = (-bx, bz, -by)
assert got == [-4.65, 3.25, -0.1, 3.4, -3.025, 4.0], got

k3d.bake(o, size=1024, ao_distance=0.2)
ph.finish(A, o, notes="Env_Cafe 에 씬 원점, 회전 0 으로 둔다. 원점 = 씬 원점이라 바닥 중앙이 아니다. min_z -0.1 은 바닥판 두께로 의도한 값. "
                      "앞 z -3 은 비어 있고 PH_CafeFront 가 막는다. 범위 x -4.65~3.25, y -0.1~3.4, z -3.025~4.0, 안쪽 x -4.55~3.15, z -3~3.9, 높이 3.2. "
                      "Wall_BarEnd(x 0.72~0.8) 포함. 징두리는 양옆 벽과 칸막이 오른쪽 뒷벽에만 있고 키오스크 자리 x 1.555~2.245 는 비운다. 천장 앞면은 벽 끝면과 지글거리지 않게 z -3.015 다. "
                      "천장 등 5개는 발광 3.0 재질만이고 Light 는 없다. 타일은 공유 텍스처의 틴트 사본 M_Tile_Cafe_Room*.")

lamps = [(ph.at_unity(x, 3.0, z), 40, 0.4, (1, 0.9, 0.75)) for x, z in LAMPS]
for i, (cam, tgt) in enumerate((((2.6, 1.55, -2.6), (-1.5, 1.1, 3.9)), ((-3.8, 1.55, -2.5), (2.4, 1.0, 3.9)),
                                ((-0.7, 1.0, -2.7), (-0.7, 3.2, 2.0)))):
    S.shot(f"{A}_in{i}", ph.at_unity(*cam), ph.at_unity(*tgt), lights=lamps)
k3d.preview(A, [o], views=((180, 8), (0, 25)))

"""PH_OfficeBlock__Body: 2회차 카페 거리의 사무 빌딩. 회색 자리와 같은 16 x 30 x 12.85, 원점 = 몸통 바닥 중앙, 앞 Unity -Z.
씬이 비균등 스케일(0.52~1.2)로 늘려 쓰고 한 채는 카페 위 2층에 얹으므로 글자, 곡선, 텍스처, 문 없이 격자 입면만 둔다.
네 면 모두 벽에 구멍을 내고 유리를 안쪽에 넣어 범위를 넘지 않는다. 밑면은 닫는다(2층 인스턴스가 아래에서 보인다). 굽기 없음."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Buildings")]
import ph, bld, bpy
k3d = ph.k3d

A = "PH_OfficeBlock__Body"
k3d.reset()
WALL = k3d.mat(f"M_{A}_Wall", (0.54, 0.515, 0.456), 0.7)
FRAME = k3d.mat(f"M_{A}_Frame", (0.045, 0.054, 0.065), 0.45)
GLASS = [k3d.mat(f"M_{A}_GlassDark", (0.02, 0.033, 0.05), 0.35),     # M_Glass 가 아니라 불투명으로 남는다
         k3d.mat(f"M_{A}_GlassLight", (0.032, 0.062, 0.1), 0.35)]

W, DP, HT = 16.0, 12.0, 30.0
D, WIN = 0.15, 1.4                                              # 유리가 벽면에서 들어간 깊이, 옆과 뒤 창 폭
UP, RT = (0, 0, 1), (1, 0, 0)
BANDS = [(4.6 + 3.2 * i, 6.2 + 3.2 * i) for i in range(8)]      # 회색 Band 8개와 같은 층
FINS = (-6, -2, 2, 6)
M = bld.Mesh()


def bar(x, y, z0, z1):
    """유리에 박힌 세로살. y = 벽면. 층 사이는 벽이 가려서 한 줄로 세운다."""
    M.box(FRAME, (x, y + D - 0.04, (z0 + z1) / 2), (0.1, 0.14, z1 - z0), 0, 1)


# 앞면: 로비와 유리 띠
y0 = -DP / 2
M.wall(WALL, (-W / 2, y0, 0), RT, UP, W, HT, [(0.2, 15.8, 0.2, 3.4)] + [(0.3, 15.7, a, b) for a, b in BANDS],
       thick=D, reveal_m=FRAME)
M.quad(GLASS[0], (0, y0 + D, 1.8), RT, UP, 15.6, 3.2)
for a, b in BANDS:
    for x in range(-8, 8):                                      # 1 m 판. 양 끝은 벽 뒤로 숨는다
        M.quad(bld.rnd.choice(GLASS), (x + 0.5, y0 + D, (a + b) / 2), RT, UP, 1, b - a)
for x in range(-7, 8):
    if x not in FINS:
        bar(x, y0, 0.1, 28.7)
M.box(FRAME, (0, y0 + D - 0.04, 2.6), (15.6, 0.14, 0.1), 0, 1)  # 로비 가로살
for x in FINS:                                                  # 회색은 y 2.5 에서 끝나 공중에 뜬다. 바닥까지 내린다
    M.box(FRAME, (x, y0, 14.75), (0.3, 0.4, 29.5), 0, 1)
M.box(FRAME, (0, -6.425, 3.5), (16, 0.85, 0.2), 0, 1)           # 차양. 뒷면을 벽면에 맞춰 옆벽과 겹치지 않는다

# 옆과 뒤: 2 m 간격 창 격자. 앞면과 같은 층에 1층 줄을 더한다
for rz, w, d in ((math.pi / 2, DP, W), (math.pi, W, DP), (-math.pi / 2, DP, W)):
    old = M.at(rz=rz)
    us = [2.0 * i + 1 for i in range(int(w / 2))]
    rows = [(1.4, 3.0)] + BANDS
    M.wall(WALL, (-w / 2, -d / 2, 0), RT, UP, w, HT, [(u - WIN / 2, u + WIN / 2, a, b) for u in us for a, b in rows],
           thick=D, reveal_m=FRAME)
    for u in us:
        bar(u - w / 2, -d / 2, 1.3, 28.7)
        for a, b in rows:
            M.quad(bld.rnd.choice(GLASS), (u - w / 2, D - d / 2, (a + b) / 2), RT, UP, WIN, b - a)
    M.T = old

M.quad(WALL, (0, 0, HT), RT, (0, 1, 0), W, DP)                  # 옥상
M.quad(WALL, (0, 0, 0), RT, (0, -1, 0), W, DP)                  # 밑면

src = M.to_object("OfficeSrc")
o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src)
ext = [(round(min(c), 3), round(max(c), 3)) for c in zip(*((-v.x, v.z, -v.y) for v in ph.world_verts(o)))]
print("Unity 범위", ext)
assert ext == [(-8, 8), (0, 30), (-6.85, 6)], ext

ph.finish(A, o, notes="원점 = 프리팹 원점(몸통 바닥 중앙), 앞 -Z. 회색 Body, Canopy, Fin, Band, Lobby 자리와 같다. 유리는 벽면 0.15 안쪽, 차양 뒷면은 벽면. "
                      "Fin 아래 끝은 회색 2.5 에서 바닥까지 내렸다. 굽기 없음, 유리는 불투명.")
for m in (WALL, FRAME, *GLASS):                                 # Unity 처럼 뒷면을 지워 뒤집힌 면을 미리보기에서 잡는다
    m.use_backface_culling = True
print("PREVIEWS", k3d.preview(A, [o]) + k3d.preview(A, [o], views=((215, -30),), ground=False, tag="under")
      + bld.shot(A, [o], (-16, 24, 1.6), (0, 6, 13), 24))

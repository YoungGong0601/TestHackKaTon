# 보도 모듈: StreetSidewalk(12 m) / StreetSidewalkRamp(12 m, 횡단보도·차량 진입로 경사) + 경계석 StreetCurb / StreetCurbRamp.
# I형 보도블록(M_Tile_Street_Pavers 2 m) + 노란 점자블록(선형/점형 0.6 m 타일, 3 mm 돌출) + 시멘트 땜질.
# 경계석은 1 m 돌을 하나씩 만들어(베벨 = 줄눈, 높이·각도 오차, UV 무작위 이동) 합친다.
# 실행: blender -b --factory-startup --python sidewalk.py [-- StreetCurb ...]  (인자 없으면 전부)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d, bpy, bmesh
from mathutils import Vector

L = 12.0
D = 4.0                  # 보도 폭 (경계석 뒤부터)
LOW = (-3.0, 3.0)        # 낮춘 구간 (횡단보도 폭 5 m + 여유)
WING = 1.0               # 전이 구간 길이
DROP = 0.11              # 낮춘 구간 보도 앞끝 하강량 (노면 위 3 cm 가 됨)
BAND = 1.2               # 경사 띠 깊이 (경계석에서)
CURB_W, CURB_H, CURB_LOW, CURB_BOT = 0.18, 0.15, 0.03, -0.05


def fx(x, ramp):
    if not ramp:
        return 0.0
    ax = abs(x)
    hi = LOW[1]
    if ax <= hi:
        return 1.0
    if ax >= hi + WING:
        return 0.0
    t = (hi + WING - ax) / WING
    return t * t * (3 - 2 * t)


def zfun(x, y, ramp):
    """보도 윗면 높이 (원점 = 보도 윗면). 앞(-Y) 띠가 낮춘 구간에서 경사."""
    fy = min(1.0, max(0.0, (-D / 2 + BAND - y) / BAND))
    return -DROP * fy * fx(x, ramp)


def surf(name, xs, ys, mat, tile, ramp, dz=0.0, uv_swap=False):
    """xs, ys 격자 위에 zfun 을 따르는 판."""
    bm = bmesh.new()
    vs = [[bm.verts.new((x, y, zfun(x, y, ramp) + dz)) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if not _planar(f)])
    o = S.from_bm(name, bm, mat)
    k3d.uv_world(o, tile)
    if uv_swap:   # 점자 돌기를 Y 방향으로
        uvl = o.data.uv_layers[0].data
        for lp in o.data.loops:
            co = o.data.vertices[lp.vertex_index].co
            uvl[lp.index].uv = (co.y / tile, co.x / tile)
    return o


def _planar(f):
    zs = [v.co.z for v in f.verts]
    return max(zs) - min(zs) < 1e-6


def lin(a, b, step):
    n = max(1, int(round((b - a) / step)))
    return [a + (b - a) * i / n for i in range(n + 1)]


def cuts(a, b, extra, step):
    pts = sorted(set([round(v, 4) for v in lin(a, b, step) + [e for e in extra if a < e < b]]))
    return pts


def strip(name, x0, x1, y0, y1, mat, ramp, uv_swap=False, dz=0.003):
    """점자블록 띠: 보도면 위 dz(3 mm), 옆면 포함."""
    xs = cuts(x0, x1, [LOW[0] - WING, LOW[0], LOW[1], LOW[1] + WING], 0.3)
    ys = cuts(y0, y1, [], 0.3)
    top = surf(name, xs, ys, mat, S.TILE_TACTILE, ramp, dz, uv_swap)
    # 옆면 (테두리 따라 아래로 4 mm)
    bm = bmesh.new()
    bm.from_mesh(top.data)
    edges = [e for e in bm.edges if e.is_boundary]
    ext = bmesh.ops.extrude_edge_only(bm, edges=edges)
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z -= 0.004
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(top.data)
    bm.free()
    return top


def build_sidewalk(A, ramp):
    k3d.reset()
    pav = S.tile_pavers()
    line, dot = S.tile_tactile("line"), S.tile_tactile("dot")
    cem = S._tinted_copy(S.tile_curb(), "M_Tile_Street_CementPatch", (0.78, 0.78, 0.76))
    x0, x1, y0, y1 = -L / 2, L / 2, -D / 2, D / 2
    xs = cuts(x0, x1, [LOW[0] - WING, LOW[0] - WING / 2, LOW[0], LOW[1], LOW[1] + WING / 2, LOW[1] + WING], 1.0)
    ys = cuts(y0, y1, [y0 + BAND], 0.6) if ramp else [y0, y0 + BAND, y1]
    top = surf(A + "_Top", xs, ys, pav, S.TILE_PAVER, ramp)
    # 가장자리 치마 (모듈만 놓아도 틈이 안 보이게 15 cm 아래로)
    bm = bmesh.new()
    bm.from_mesh(top.data)
    ext = bmesh.ops.extrude_edge_only(bm, edges=[e for e in bm.edges if e.is_boundary])
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z = -0.15
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:   # 윗면은 위로
        if abs(f.normal.z) > 0.5 and f.normal.z < 0:
            f.normal_flip()
    bm.to_mesh(top.data)
    bm.free()
    k3d.uv_world(top, S.TILE_PAVER)
    parts = [top]
    gy = (0.6, 0.9)      # 선형 유도 띠 (경계석에서 2.6 m, 건물 쪽)
    parts.append(strip(A + "_Guide", x0, x1, *gy, line, ramp))
    tact = []            # 횡단보도용 점자블록 = 끌 수 있는 자식 (차량 진입로에서는 끈다, 아래는 보도블록)
    if ramp:
        tact.append(strip(A + "_GuideJ", 0.0, 0.3, *gy, dot, ramp, dz=0.004))  # 분기점 = 점형 (유도 띠 위 1 mm)
        tact.append(strip(A + "_Branch", 0.0, 0.3, -0.9, 0.6, line, ramp, uv_swap=True))
        tact.append(strip(A + "_Warn", -2.4, 2.4, -1.5, -0.9, dot, ramp))      # 횡단 대기 점형 경고
    # 시멘트 땜질 (블록 빠진 자리)
    rng = random.Random(len(A))
    for i, (cx, cy, w, d) in enumerate(((-4.3, 1.55, 0.7, 0.45), (3.7, -0.35, 0.5, 0.35))):
        xs2 = [cx - w / 2, cx + w / 2]
        p = surf(f"{A}_Cement{i}", xs2, [cy - d / 2, cy + d / 2], cem, S.TILE_CURB, ramp, 0.0015)
        parts.append(p)
    body = S.join(parts, A + "_Body")
    if tact:
        S.parent(S.join(tact, A + "_Tactile"), body)
    notes = (f"보도 모듈 {L:g} m(X) x {D:g} m(Y). 원점 = 보도 윗면 중앙(z=0 = Unity y=0, 프로토타입 보도 높이). "
             f"앞(-Y) 끝 = 경계석 뒷면: StreetCurb 원점 + 경계석 로컬 (0, {CURB_W + D / 2:g}, 0.14) 에 같은 회전으로 놓는다(노면보다 14 cm 위). "
             "I형 보도블록 M_Tile_Street_Pavers(월드 UV 2 m), 노란 점자블록 M_Tile_Street_TactileLine(선형, 돌기 방향 = 진행 방향)/"
             "TactileDot(점형) 0.6 m 타일 = 300 mm 블록, 3 mm 돌출. 선형 유도 띠 y 0.6~0.9. "
             "가장자리 15 cm 치마(아래로). 시멘트 땜질 2곳. 모듈 길이 12 m = 타일 정수배.")
    if ramp:
        notes += (f" 경사 구간: x {LOW[0]:g}~{LOW[1]:g} 에서 앞 {BAND:g} m 띠가 {DROP * 100:g} cm 내려가 노면 위 3 cm 가 된다"
                  f"(양옆 {WING:g} m 전이). 자식 StreetSidewalkRamp_Tactile = 횡단 대기 점형 경고 4.8 x 0.6 m + 분기점 점형 + "
                  "분기 선형 띠(x 0~0.3): 횡단보도에서는 켜고, 차량 진입로로 쓸 때는 끈다(아래는 보도블록, 유도 띠는 본체에 끊김 없이 있음). "
                  "StreetCurbRamp 과 StreetRoadCrosswalk 를 같은 X 에 맞춘다.")
        S.empty(A + "_Socket_Wait", (0.0, -1.2, zfun(0, -1.2, True)), parent=body)
        notes += " Socket_Wait = 횡단 대기 위치."
    return [body], notes


# ------------------------------------------------------------------ 경계석
def stone(name, x0, x1, h0, h1, mat, rng):
    """경계석 1개: 앞면 살짝 경사 + 앞 윗모서리 둥글게. 원점 기준 앞면 y=0(도로 쪽 -Y), 윗면 높이 h0->h1 (X 따라)."""

    def ring(x, h):
        r = 0.022
        pts = [(0.0, CURB_BOT), (min(0.012, 0.012 * h / CURB_H) if h > 0.04 else 0.004, h - r)]
        for k in range(1, 4):
            a = math.pi / 2 * k / 3
            pts.append((pts[1][0] + r * (1 - math.cos(a)) + 0.0, h - r + r * math.sin(a)))
        pts.append((CURB_W, h))
        pts.append((CURB_W, CURB_BOT))
        return [Vector((x, y, z)) for y, z in pts]

    bm = bmesh.new()
    r0 = [bm.verts.new(v) for v in ring(x0, h0)]
    r1 = [bm.verts.new(v) for v in ring(x1, h1)]
    n = len(r0)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(r0)))
    bm.faces.new(r1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = S.from_bm(name, bm, mat)
    S.mods(o, bevel=0.004, segs=2, angle=30)
    k3d.apply_all(o)
    # 놓인 오차: 높이 ±3 mm, 앞뒤 ±2 mm, 비틀림 ±0.25°
    o.data.transform(S._xf((0, rng.uniform(-0.002, 0.002), rng.uniform(-0.003, 0.002)),
                           (rng.uniform(-0.002, 0.002), 0, rng.uniform(-0.0045, 0.0045))))
    k3d.uv_world(o, S.TILE_CURB)
    du, dv = rng.random(), rng.random()
    for d in o.data.uv_layers[0].data:
        d.uv = (d.uv[0] + du, d.uv[1] + dv)
    return o


def build_curb(A, ramp):
    k3d.reset()
    ma = S.tile_curb()
    mb = S._tinted_copy(ma, "M_Tile_Street_CurbB", (0.86, 0.86, 0.84))
    mc = S._tinted_copy(ma, "M_Tile_Street_CurbC", (1.0, 0.97, 0.92))
    rng = random.Random(42 if ramp else 7)
    stones = []
    gap = 0.004
    for i in range(int(L)):
        x0, x1 = -L / 2 + i + gap / 2, -L / 2 + i + 1 - gap / 2
        xc = (x0 + x1) / 2

        def h_at(x):
            return CURB_H - (CURB_H - CURB_LOW) * fx(x, ramp)
        m = rng.choice((ma, ma, mb, mc))
        stones.append(stone(f"{A}_S{i}", x0, x1, h_at(x0), h_at(x1), m, rng))
    body = S.join(stones, A + "_Body")
    notes = (f"경계석 {L:g} m(1 m 돌 x {int(L)}개, 줄눈 4 mm). 원점 = 경계석 앞면 아래선 = 노면 높이(z=0 = 도로 윗면). "
             f"앞(-Y) = 도로 쪽. 단면 폭 {CURB_W:g} m, 노면 위 {CURB_H:g} m(보도면보다 1 cm 높음), 노면 아래 {-CURB_BOT:g} m 묻힘 "
             "(min_z 가 0 이 아닌 것은 의도: 노면 아래 묻히는 부분). StreetRoad 원점 + (0, ±4.0, 0) 에 앞면이 닿게: "
             "도로 +Y 쪽은 회전 0, 도로 -Y(앞, 버스정류장) 쪽은 Z 180°. 돌마다 높이·각도 오차와 텍스처 위치가 달라 반복이 안 보인다. "
             "M_Tile_Street_Curb/CurbB/CurbC (같은 텍스처, 색만 다름, 월드 UV 3 m).")
    if ramp:
        notes += (f" 낮춘 구간 x {LOW[0]:g}~{LOW[1]:g}: 노면 위 {CURB_LOW * 100:g} cm (양옆 {WING:g} m 전이 돌). "
                  "StreetSidewalkRamp 과 짝.")
    return [body], notes


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    todo = argv or ["StreetCurb", "StreetCurbRamp", "StreetSidewalk", "StreetSidewalkRamp"]
    for A in todo:
        ramp = A.endswith("Ramp")
        if A.startswith("StreetCurb"):
            roots, notes = build_curb(A, ramp)
            S.finish(A, roots, None, notes, views=((25, 30), (205, 20)),
                     extra=[dict(dist=3.2, eye=1.55, look_h=0.0, az=-35, lens=35, cx=(0.0 if ramp else 1.0, 0.1, 0.0))])
        else:
            roots, notes = build_sidewalk(A, ramp)
            S.finish(A, roots, None, notes, views=((25, 38), (205, 24)),
                     extra=[dict(dist=4.5, eye=1.55, look_h=-0.05, az=-30, lens=35, cx=(0.0, -0.6, 0.0))])

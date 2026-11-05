"""PH_BusInterior: Bus 씬 실내. 프리팹 회색 구조 그대로 새로 짓고 색과 표지는 CityBus 를 따른다.

CityBus 실내를 옮기지 않는 이유: 의자·봉 자리가 Col_ 콜라이더와 다르고 바닥·천장 높이도 다르다.
좌표는 전부 프리팹 로컬 Unity (x 앞, y 위, z 먼 창 쪽). 원점 = 프리팹 원점이라 실내 바닥은 y 0.32, 메시 아래 끝은 y 0.22.
몸체(바닥·벽·천장·문)와 Props(의자·봉·운전석) 두 아틀라스. 의자는 네 벌만 굽고 나머지 자리에는 UV 째로 찍는다.
단색 부품(봉·틀·조명)과 바깥 면·가려진 면은 아틀라스를 먹지 않게 굽지 않는다.
판은 전부 두께 있는 상자라 실내 쪽 면의 노멀이 안을 본다. 유리만 양면 한 장이다.

실행: blender -b --factory-startup --python-exit-code 1 --python bus_interior.py   (1분 안팎, 검사 실패 시 종료 코드 1)
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Vehicles")]
import bpy, bmesh
from mathutils import Vector
import ph, k3d
import _vlib as V

A = "PH_BusInterior"
PY = k3d.PY
TEX = os.path.join(k3d.ART, "Textures")
B = ph.at_unity

IN, OUT = 1.19, 1.25                                  # 벽 안쪽, 바깥쪽 |z|
FL, SILL, HEAD, CEIL, ROOF = 0.32, 1.30, 2.30, 2.65, 2.75
DOORS = (4.45, -0.90)                                 # 앞문, 뒷문 중심 x (반폭 0.58)
FAR = (-5.45, -3.27, -1.09, 1.09, 3.27, 5.45)         # 먼 쪽 창틀 x
NEAR = ((-5.45, -3.465, -1.48), (-0.32, 1.775, 3.87), (5.03, 5.45))   # 문 쪽 창틀 x (문 사이는 끊김)
DOUBLE = (3.10, 2.15, 1.20, 0.25, -0.70, -1.65, -2.60, -3.55, -4.50)  # 좌석 방석 중심 x
SINGLE = (3.10, 2.25, 1.40, 0.55, -2.05, -2.90, -3.75, -4.50)
POLES = ((3.50, -0.68), (1.80, 0.36), (0.05, -0.68), (-1.75, -0.68), (-1.85, 0.36), (-3.60, -0.68))
RAILS = (-0.60, 0.30)
BLINDS = ((-1.12, -0.02), (0.02, 1.12))               # 앞유리 차양 z 범위. 끝단이 눈높이라 앞쪽 지평선도 가린다
COVE = 0.90                                           # 천장 쪽 벽 경사판이 천장과 만나는 |z|
EYE = 1.88                                            # 바닥 + EyeHeight 1.56. 창 가로대를 여기 둬서 밖 평면의 지평선을 가린다


# ---------------------------------------------------------------- 메시 도구 (Unity 좌표)
def bx(lo, hi, m, bev=0.0):
    lo, hi = Vector(lo), Vector(hi)
    s = hi - lo
    return V.box("p", (s.x, s.z, s.y), B(*(lo + hi) / 2), m, bevel=bev, segs=1)


def rod(a, b, r, m, segs=10):
    a, b = B(*a), B(*b)
    d = b - a
    return V.cyl("r", r, d.length, (a + b) / 2, d.to_track_quat('Z', 'Y').to_euler(), m, segs)


def tube(pts, r, m, segs=6, closed=False):
    return V.tube("t", [B(*p) for p in pts], r, segs, m, closed=closed)


def prism(prof, x0, x1, m):
    """(z, y) 단면을 x0..x1 로 민 기둥."""
    bm = bmesh.new()
    a = [bm.verts.new(B(x0, y, z)) for z, y in prof]
    b = [bm.verts.new(B(x1, y, z)) for z, y in prof]
    bm.faces.new(a)
    bm.faces.new(b)
    n = len(prof)
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return V.mesh_obj("c", bm, [m])


def finish(o, angle=38):
    k3d.smooth(o, angle)
    w = o.modifiers.new("wn", 'WEIGHTED_NORMAL')
    w.keep_sharp, w.weight, w.mode = True, 50, 'FACE_AREA'
    return o


# ---------------------------------------------------------------- 머티리얼 (CityBus 실내 색)
def flat(name, color, rough=0.5, metal=0.0, dirt=0.5):
    g = V.NB(name)
    col = g.mix(g.mul(g.noise(7, 3), 0.5), color, tuple(c * 0.86 for c in color))
    dm = g.mul(V.grime_mask(g, low_z=0.8, cav_dist=0.05, speck=0.08), dirt)
    col = g.mix(dm, col, (0.13, 0.115, 0.095))
    g.p.inputs['Emission Color'].default_value = (0, 0, 0, 1)   # 기본값이 흰색이라 비워야 몸이 안 빛난다
    return g.out(col, g.add(rough, g.mul(dm, 0.25)), metal)


def floor():
    """미끄럼방지 비닐: 점 무늬, 통로 닳음."""
    g = V.NB("M_BI_Floor")
    y = g.xyz()[1]
    spk = g.maprange(g.noise(95, 2), 0.58, 0.68, 0, 1)
    col = g.mix(g.mul(spk, 0.55), (0.085, 0.095, 0.105), (0.26, 0.27, 0.27))
    walk = g.mul(g.maprange(g.absf(g.add(y, -0.15)), 0.75, 0.2, 0, 1), g.maprange(g.noise(1.6, 4), 0.35, 0.7, 0.25, 0.8))
    col = g.mix(walk, col, (0.15, 0.14, 0.125))
    dm = g.mul(V.grime_mask(g, low_z=0.8, cav_dist=0.08, speck=0.1), 0.5)
    col = g.mix(dm, col, (0.06, 0.055, 0.05))
    g.p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    return g.out(col, g.add(0.62, g.mul(walk, -0.2)), 0.0, g.bump(spk, 0.3, 0.0015))


def panel(name, color, seams):
    """벽·천장 FRP 판: seams 는 판 이음 홈이 있는 Blender x 위치."""
    g = V.NB(name)
    x = g.xyz()[0]
    gap = None
    for c in seams:
        l = g.line(x, c, 0.006)
        gap = l if gap is None else g.maxf(gap, l)
    col = g.mix(g.mul(g.noise(3, 2), 0.4), color, tuple(c * 0.93 for c in color))
    dm = g.mul(V.grime_mask(g, low_z=0.6, cav_dist=0.07, speck=0), 0.3)
    col = g.mix(g.maxf(dm, gap), col, (0.14, 0.13, 0.115))
    g.p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    return g.out(col, g.add(0.5, g.mul(dm, 0.25)), 0.0, g.bump(g.mul(gap, -1.0), 0.5, 0.004))


def fabric(name, color):
    """의자 천: 작은 점 무늬 모켓."""
    g = V.NB(name)
    dots = g.maprange(g.noise(130, 2), 0.55, 0.62, 0, 1)
    col = g.mix(g.mul(dots, 0.4), color, tuple(min(1, c * 1.9 + 0.015) for c in color))
    dm = g.mul(V.grime_mask(g, low_z=0.3, cav_dist=0.03, speck=0.05), 0.5)
    col = g.mix(dm, col, tuple(c * 0.55 for c in color))
    g.p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    return g.out(col, 0.82, 0.0, g.bump(g.noise(400, 2), 0.35, 0.0015))


def plain(name, color, rough, metal=0.0, glow=None):
    """굽지 않는 단색. 가늘고 긴 조각이 수백 개라 구우면 섬 여백이 아틀라스를 다 먹는다."""
    m = k3d.mat(f"M_{A}_{name}", color, rough, metal, emission=glow, strength=3.0)
    if not glow:
        k3d.principled(m).inputs['Emission Color'].default_value = (0, 0, 0, 1)
    return m


def glass(name, alpha):
    m = k3d.flag(V.glass(name, (0.1, 0.12, 0.12), alpha, 0.03), double_sided=True)
    p = k3d.principled(m)
    p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    n = k3d.image_node(m, k3d.load_image(os.path.join(TEX, "CityBus", "T_CityBus_GlassDirt.png"), "T_CityBus_GlassDirt"),
                       p.inputs['Base Color'])
    mul = m.node_tree.nodes.new('ShaderNodeMath')    # 먼지·물자국: 텍스처 알파 x 머티리얼 알파
    mul.operation, mul.inputs[1].default_value = 'MULTIPLY', alpha
    m.node_tree.links.new(n.outputs['Alpha'], mul.inputs[0])
    m.node_tree.links.new(mul.outputs[0], p.inputs['Alpha'])
    return m


def materials():
    return {
        "floor": floor(),
        "wall": panel("M_BI_Wall", (0.56, 0.56, 0.54), [-x for x in FAR] + [-x for s in NEAR for x in s]),
        "lower": panel("M_BI_Lower", (0.36, 0.37, 0.38), [-x for x in FAR] + [-x for s in NEAR for x in s]),
        "ceil": panel("M_BI_Ceil", (0.62, 0.62, 0.6), [-5.2 + 1.3 * i for i in range(9)]),
        "cove": panel("M_BI_Cove", (0.56, 0.56, 0.54), [-x for x in FAR]),
        "door": flat("M_BI_Door", (0.11, 0.12, 0.13), 0.45, dirt=0.4),
        "shell": flat("M_BI_Shell", (0.018, 0.04, 0.09), 0.4, dirt=0.3),
        "blue": fabric("M_BI_Blue", (0.02, 0.075, 0.21)),
        "orange": fabric("M_BI_Orange", (0.62, 0.20, 0.02)),
        "drv": fabric("M_BI_Drv", (0.03, 0.03, 0.035)),
        "dash": flat("M_BI_Dash", (0.02, 0.02, 0.022), 0.5, dirt=0.3),
        "dark": plain("Dark", (0.022, 0.022, 0.024), 0.55),
        "frame": plain("Frame", (0.05, 0.052, 0.056), 0.42, 0.6),
        "pole": plain("Pole", (0.72, 0.47, 0.02), 0.32),
        "steel": plain("Steel", (0.55, 0.56, 0.58), 0.35, 1.0),
        "ring": plain("Ring", (0.68, 0.68, 0.66), 0.4),
        "red": plain("Red", (0.6, 0.03, 0.02), 0.35),
        "light": plain("Light", (0.9, 0.9, 0.9), 0.3, glow=(1.0, 1.0, 0.95)),
        "screen": plain("Screen", (0.02, 0.2, 0.08), 0.2, glow=(0.015, 0.14, 0.05)),   # x3 해서 Unity 에서 민트로 날아가지 않는 값
        "outer": plain("Outer", (0.02, 0.1, 0.33), 0.35),
        "glass": glass("M_Glass_PH_BusInterior", 0.3),
        "decal": V.flat_image("M_PH_Bus_Decals", os.path.join(TEX, "PH_Bus", "T_PH_Bus_Decals.png"), 0.45, 0.5),
    }


# ---------------------------------------------------------------- 의자
PROFILE = [(-0.262, 1.30), (-0.25, 1.18), (-0.232, 1.04), (-0.212, 0.92), (-0.195, 0.84), (-0.16, 0.785), (-0.09, 0.755),
           (0.03, 0.755), (0.14, 0.77), (0.20, 0.765), (0.218, 0.735), (0.205, 0.705)]   # 앉는 면 옆모습 (방석 중심 기준 x, y)


def spline(P):
    d = [0.0]
    for a, b in zip(P, P[1:]):
        d.append(d[-1] + math.dist(a, b))
    fu = V.pchip([(t / d[-1], p[0]) for t, p in zip(d, P)])
    fv = V.pchip([(t / d[-1], p[1]) for t, p in zip(d, P)])
    return lambda t: Vector((fu(t), fv(t)))


def patch(f, cu, cw, hw, t0, t1, s1, lift, m, rows, cols):
    """옆모습 f(t) 를 폭으로 편 곡면. 앞면이 앉는 쪽이고 lift(T, S) 만큼 그쪽으로 띄운다 (T, S 는 조각 안 -1..1)."""
    bm = bmesh.new()
    grid = []
    for i in range(rows + 1):
        t = t0 + (t1 - t0) * i / rows
        row = []
        for j in range(cols + 1):
            s = s1 * (2 * j / cols - 1)
            a = abs(s) ** 5
            tt = min(1, max(0, t + 0.06 * a * (1 - t) ** 10 - 0.035 * a * t ** 10))   # 위·앞 모서리를 둥글게
            d = f(min(1, tt + 0.01)) - f(max(0, tt - 0.01))
            q = f(tt) + Vector((-d.y, d.x)).normalized() * (0.016 * abs(s) ** 3 + lift(2 * i / rows - 1, s / s1))
            row.append(bm.verts.new(B(cu + q.x, q.y, cw + s * hw)))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    return V.mesh_obj("s", bm, [m])


def chair(M, cu, cw, W, pad, dv=0.0, top=1.30):
    P = [(u, v + dv if v < 0.8 else 0.8 + dv + (v - 0.8) * (top - 0.8 - dv) / 0.5) for u, v in PROFILE]
    f = spline(P)
    sh = patch(f, cu, cw, W / 2, 0, 1, 1, lambda T, S: 0, M['shell'], 18, 8)
    sd = sh.modifiers.new("t", 'SOLIDIFY')
    sd.thickness, sd.offset = 0.018, -1
    puff = lambda T, S: -0.004 + 0.03 * (1 - T ** 4) * (1 - S ** 4)
    return [sh, patch(f, cu, cw, W / 2, 0.045, 0.475, 0.88, puff, pad, 10, 8), patch(f, cu, cw, W / 2, 0.59, 0.925, 0.88, puff, pad, 8, 8)]


def legs(M, cx, cz, half):
    s = M['steel']
    return [bx((cx - 0.03, FL, cz - 0.03), (cx + 0.03, 0.70, cz + 0.03), s, 0.008),
            bx((cx - 0.09, FL, cz - 0.08), (cx + 0.09, FL + 0.012, cz + 0.08), s, 0.004),
            bx((cx - 0.035, 0.69, cz - half), (cx + 0.045, 0.74, cz + half), s, 0.008)]


def grab(M, cx, cz):
    """등받이 위 손잡이."""
    return tube([(cx - 0.262, 1.20, cz - 0.13), (cx - 0.285, 1.28, cz - 0.125), (cx - 0.29, 1.325, cz - 0.08),
                 (cx - 0.29, 1.325, cz + 0.08), (cx - 0.285, 1.28, cz + 0.125), (cx - 0.262, 1.20, cz + 0.13)], 0.011, M['pole'], 8)


def seat_double(M, cx, pad):
    o = legs(M, cx, 0.795, 0.3)
    for z in (0.6075, 0.9825):
        o += chair(M, cx, z, 0.365, pad) + [grab(M, cx, z)]
    return o


def seat_single(M, cx, pad):
    return legs(M, cx, -0.945, 0.17) + chair(M, cx, -0.945, 0.44, pad) + [grab(M, cx, -0.945)]


def stamp(o, lo, hi, moves):
    """구운 메시에서 lo..hi 상자 안의 면을 moves(x 이동량) 자리에 UV 째로 복사한다."""
    a, b = B(*lo), B(*hi)
    mn = [min(a[i], b[i]) for i in range(3)]
    mx = [max(a[i], b[i]) for i in range(3)]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    faces = [f for f in bm.faces if all(mn[i] <= v.co[i] <= mx[i] for v in f.verts for i in range(3))]
    assert faces, (lo, hi)
    geom = faces + list({e for f in faces for e in f.edges}) + list({v for f in faces for v in f.verts})
    for dx in moves:
        new = bmesh.ops.duplicate(bm, geom=geom)['geom']
        bmesh.ops.translate(bm, vec=B(dx, 0, 0), verts=[g for g in new if isinstance(g, bmesh.types.BMVert)])
    bm.to_mesh(o.data)
    bm.free()


# ---------------------------------------------------------------- Props: 의자, 봉, 손잡이, 운전석
def driver(M):
    o = chair(M, 4.425, 0.70, 0.54, M['drv'], dv=0.05, top=1.45)
    o += [V.cyl("c", 0.09, 0.40, B(4.42, 0.52, 0.70), (0, 0, 0), M['dash'], 14),
          bx((4.20, 0.70, 0.46), (4.65, 0.74, 0.94), M['dash'], 0.01),
          bx((3.78, FL, 0.10), (3.84, 1.45, IN), M['lower'], 0.012),          # 칸막이
          rod((3.81, 1.47, 0.12), (3.81, 1.47, 1.17), 0.016, M['pole']),
          rod((3.81, 1.45, 0.12), (3.81, FL, 0.12), 0.018, M['pole']),
          bx((4.95, FL, -IN), (5.39, 1.08, IN), M['lower'], 0.02),            # 대시보드
          bx((4.93, 1.06, -IN), (5.39, 1.15, IN), M['dash'], 0.025),
          bx((4.94, FL, -IN), (4.965, 0.44, IN), M['dark'], 0.004),
          bx((4.94, 0.84, -0.95), (4.955, 0.94, -0.35), M['dark'], 0.004),
          bx((4.90, 1.15, -0.62), (5.12, 1.27, -0.30), M['dash'], 0.02),      # 표 찍는 기계
          bx((4.895, 1.19, -0.56), (4.90, 1.25, -0.36), M['screen']),
          V.cyl("c", 0.055, 0.34, B(4.87, 0.52, -0.70), (0, 0, 0), M['red'], 14, bevel=0.012),   # 소화기
          rod((4.87, 0.69, -0.70), (4.87, 0.74, -0.70), 0.016, M['dark'], 8),
          bx((4.96, 1.13, 0.42), (5.14, 1.27, 0.98), M['dash'], 0.03),        # 계기판 덮개
          bx((4.95, 1.16, 0.53), (4.962, 1.24, 0.87), M['screen']),
          bx((4.67, FL, 0.12), (4.95, 1.14, 0.40), M['steel'], 0.02),         # 요금함
          bx((4.70, 1.14, 0.15), (4.92, 1.18, 0.37), M['dash'], 0.008),
          bx((4.74, 1.0, 0.116), (4.88, 1.08, 0.122), M['screen'])]
    c, r = Vector((4.88, 1.16, 0.70)), 0.22                                    # 운전대 (거의 눕힘)
    e1, e2 = Vector((0, 0, 1)), Vector((0.89, 0.45, 0))
    ring = [c + (e1 * math.cos(a) + e2 * math.sin(a)) * r for a in (i * math.pi / 10 for i in range(20))]
    o += [tube(ring, 0.017, M['dash'], 8, closed=True), rod(c, (5.0, 0.98, 0.70), 0.03, M['dash']),
          rod(c - e2 * r, c, 0.012, M['dash'], 6), rod(c - e1 * r, c + e1 * r, 0.012, M['dash'], 6)]
    return o


def props(M):
    o = []
    for x, z in POLES:
        o += [rod((x, FL, z), (x, CEIL, z), 0.02, M['pole'], 12),
              rod((x, FL, z), (x, FL + 0.02, z), 0.036, M['steel'], 12), rod((x, CEIL - 0.02, z), (x, CEIL, z), 0.036, M['steel'], 12),
              bx((x - 0.025, 1.34, z - 0.035), (x + 0.025, 1.42, z + 0.035), M['red'], 0.008)]   # 하차벨
    for z in RAILS:
        for x in (-4.8, -2.7, -0.6, 1.5, 3.6):
            o.append(rod((x, 2.375, z), (x, CEIL, z), 0.012, M['steel'], 8))
            if x < 3:                                                           # 긴 봉 하나는 아틀라스에 안 들어가 걸이마다 끊는다
                o.append(rod((x, 2.375, z), (x + 2.1, 2.375, z), 0.015, M['pole'], 10))
        for i in range(15):
            x = -4.5 + 0.56 * i
            ring = [(x, 2.095 + 0.045 * math.sin(a), z + 0.043 * math.cos(a)) for a in (k * math.pi / 9 for k in range(18))]
            o += [bx((x - 0.003, 2.135, z - 0.012), (x + 0.003, 2.39, z + 0.012), M['dark']), tube(ring, 0.0065, M['ring'], 6, closed=True)]
    for x, face in ((3.5, -1), (-1.75, 1), (0.05, 1)):                          # 교통카드 단말기, 화면은 문 또는 통로 쪽
        z = -0.68 + 0.05 * face
        o += [bx((x - 0.08, 1.2, z - 0.045), (x + 0.08, 1.42, z + 0.045), M['dash'], 0.015),
              bx((x - 0.055, 1.31, z + 0.045 * face - 0.002), (x + 0.055, 1.38, z + 0.045 * face + 0.002), M['screen'])]
    for x in (3.80, 5.10, -1.55, -0.25):                                        # 문 옆 세로 손잡이
        o += [rod((x, 0.95, -1.15), (x, 1.95, -1.15), 0.016, M['pole']),
              rod((x, 1.0, -1.15), (x, 1.0, -IN), 0.012, M['steel'], 8), rod((x, 1.9, -1.15), (x, 1.9, -IN), 0.012, M['steel'], 8)]
    o += [rod((-5.38, 1.36, -1.05), (-5.38, 1.36, 1.05), 0.016, M['pole']),     # 뒤 창 앞 가로 손잡이
          bx((-5.41, EYE - 0.025, -1.15), (-5.39, EYE + 0.025, 1.15), M['dark']),
          bx((3.70, 2.27, -0.62), (3.76, 2.53, 0.32), M['dash'], 0.012),        # 앞쪽 LED 안내판
          rod((3.73, 2.53, -0.5), (3.73, CEIL, -0.5), 0.012, M['steel'], 8), rod((3.73, 2.53, 0.2), (3.73, CEIL, 0.2), 0.012, M['steel'], 8)]
    o += [bx((5.33, EYE - 0.02, z0), (5.37, EYE + 0.02, z1), M['dark'], 0.006) for z0, z1 in BLINDS]   # 앞유리 차양 끝단
    o += [rod((5.445, 1.14, z), (5.445, 1.95, z + 0.45), 0.008, M['dark'], 6) for z in (-0.9, 0.2)]   # 와이퍼
    for x, pad in ((3.10, M['orange']), (1.20, M['blue'])):
        o += seat_double(M, x, pad)
    for x, pad in ((3.10, M['orange']), (1.40, M['blue'])):
        o += seat_single(M, x, pad)
    o += driver(M)
    return finish(V.join(o, A + "_Props"), 45)


def place_seats(p):
    box = lambda x, z0, z1: ((x - 0.32, 0.30, z0), (x + 0.25, 1.36, z1))
    stamp(p, *box(3.10, 0.40, IN), [2.15 - 3.10])
    stamp(p, *box(1.20, 0.40, IN), [x - 1.20 for x in DOUBLE if x not in (3.10, 2.15, 1.20)])
    stamp(p, *box(3.10, -IN, -0.70), [2.25 - 3.10])
    stamp(p, *box(1.40, -IN, -0.70), [x - 1.40 for x in SINGLE if x not in (3.10, 2.25, 1.40)])


# ---------------------------------------------------------------- 몸체
def door(M, c):
    o = [bx((c - 0.58, 2.36, -OUT), (c + 0.58, CEIL, -IN), M['wall']),
         bx((c - 0.58, FL, -IN), (c + 0.58, FL + 0.02, -0.95), M['pole'], 0.004)]
    for lc in (c - 0.285, c + 0.285):
        o += [bx((lc - 0.275, FL, -1.24), (lc + 0.275, 1.05, -1.20), M['door'], 0.006),
              bx((lc - 0.275, 1.05, -1.24), (lc - 0.215, 2.36, -1.20), M['frame'], 0.004),
              bx((lc + 0.215, 1.05, -1.24), (lc + 0.275, 2.36, -1.20), M['frame'], 0.004),
              bx((lc - 0.275, 2.28, -1.24), (lc + 0.275, 2.36, -1.20), M['frame'], 0.004),
              bx((lc - 0.215, 1.03, -1.235), (lc + 0.215, 1.07, -1.205), M['frame'], 0.004),
              bx((lc - 0.215, EYE - 0.025, -1.235), (lc + 0.215, EYE + 0.025, -1.205), M['frame'], 0.004)]
    o.append(bx((c - 0.012, FL, -1.235), (c + 0.012, 2.36, -1.205), M['dark']))   # 가운데 고무
    for x in (c - 0.58, c + 0.58):     # 문설주: 문짝과 벽판 사이 2cm 틈을 막는다. 벽면보다 4mm 내밀어 같은 평면을 피한다
        o.append(bx((x - 0.04, FL, -OUT), (x + 0.04, SILL, -IN + 0.004), M['frame']))
    return o


def window(M, x0, x1, sign):
    """창 안쪽 턱과 미닫이 틀."""
    a, b = sorted((sign * IN, sign * (IN - 0.04)))
    o = [bx((x0, SILL, a), (x1, SILL + 0.035, b), M['dark'], 0.006),
         bx((x0, HEAD - 0.03, a), (x1, HEAD, b), M['dark'], 0.006)]
    c, d = sorted((sign * 1.208, sign * 1.232))
    o.append(bx((x0, EYE - 0.025, c), (x1, EYE + 0.025, d), M['frame'], 0.003))
    if x1 - x0 > 1:
        o.append(bx(((x0 + x1) / 2 - 0.012, EYE, c), ((x0 + x1) / 2 + 0.012, HEAD, d), M['frame'], 0.003))
    return o


def side(M, xs, sign):
    z0, z1 = sorted((sign * IN, sign * OUT))
    o = []
    for a, b in zip(xs, xs[1:]):
        o += [bx((a, FL, z0), (b, SILL, z1), M['lower']), bx((a, HEAD, z0), (b, CEIL, z1), M['wall'])]
        o += window(M, a + 0.04, b - 0.04, sign)
    for x in xs:
        o.append(bx((x - 0.04, SILL, z0), (x + 0.04, HEAD, z1), M['frame']))
        if abs(x) < 5:     # 하차벨
            a, b = sorted((sign * IN, sign * (IN - 0.018)))
            o.append(bx((x - 0.025, 1.52, a), (x + 0.025, 1.6, b), M['red'], 0.004))
    return o


def shell(M):
    o = []
    for a, b in zip((-5.45, -2.725, 0, 2.725), (-2.725, 0, 2.725, 5.45)):        # 짧게 끊어야 아틀라스에 잘 들어간다
        o.append(bx((a, 0.22, -OUT), (b, FL, OUT), M['floor']))
        o.append(bx((a, CEIL, -COVE), (b, ROOF, COVE), M['ceil']))
        for z0, z1 in ((-OUT, -COVE), (COVE, OUT)):
            o.append(bx((a, CEIL, z0), (b, ROOF, z1), M['outer']))
    o += side(M, FAR, 1)
    for xs in NEAR:
        o += side(M, xs, -1)
    for c in DOORS:
        o += door(M, c)
    for s in (-1, 1):                                                            # 경사판 (광고 자리)
        for a, b in zip((-5.39, -2.725, 0, 2.725), (-2.725, 0, 2.725, 5.39)):
            o.append(prism(((s * IN, HEAD), (s * COVE, CEIL), (s * IN, CEIL)), a, b, M['cove']))
    o += [bx((5.39, FL, -OUT), (5.45, 1.10, OUT), M['wall']), bx((5.39, 2.40, -OUT), (5.45, CEIL, OUT), M['wall']),
          bx((-5.45, FL, -OUT), (-5.39, SILL, OUT), M['lower']), bx((-5.45, HEAD, -OUT), (-5.39, CEIL, OUT), M['wall'])]
    for s in (-1, 1):
        a, b = sorted((s * 1.15, s * OUT))
        o.append(bx((-5.45, SILL, a), (-5.39, HEAD, b), M['wall']))
    o += [bx((5.30, 2.33, 0.2), (5.385, 2.38, 1.1), M['dark'], 0.01)]            # 햇빛 가리개
    for x0, x1 in ((-5.1, -2.3), (-2.1, 0.7), (0.9, 3.6)):                       # 천장 조명
        for z in (-0.78, 0.78):
            o.append(bx((x0, CEIL - 0.016, z - 0.05), (x1, CEIL, z + 0.05), M['light'], 0.004))
    o.append(bx((3.9, CEIL - 0.016, -0.65), (5.2, CEIL, -0.55), M['light'], 0.004))
    for x in (-3.4, 0.45):                                                       # 비상 탈출구
        o.append(bx((x - 0.36, CEIL - 0.02, -0.5), (x + 0.36, CEIL, 0.2), M['cove'], 0.008))
    for x in (-1.7, 2.2):                                                        # 스피커
        o.append(V.cyl("c", 0.085, 0.012, B(x, CEIL - 0.006, -0.15), (0, 0, 0), M['dark'], 16))
    return finish(V.join(o, A))


def hide_faces(o, m):
    """눈이 갈 수 있는 상자 어디서 봐도 뒷면인 면과 경사판 뒤의 면은 굽지 않는다 (틀마다 생기는 작은 섬이 아틀라스를 먹는다)."""
    if m.name not in o.data.materials:
        o.data.materials.append(m)
    i = o.data.materials.find(m.name)
    eyes = [B(x, y, z) for x in (-5.3, 4.7) for y in (1.8, 1.96) for z in (-1.15, 1.15)]
    for p in o.data.polygons:
        y, z = p.center.z, -p.center.y
        if all(p.normal.dot(e - p.center) <= 0 for e in eyes) or (abs(z) > IN - 0.005 and y > 2.4) or (abs(z) > COVE and y > CEIL - 0.005):
            p.material_index = i


# ---------------------------------------------------------------- 유리, 표지
def glazing(M):
    bm = bmesh.new()

    def pane(x0, y0, z0, x1, y1, z1):
        a, b = B(x0, y0, z0), B(x1, y1, z1)
        if z0 == z1:
            bm.faces.new([bm.verts.new(v) for v in (a, (b.x, a.y, a.z), b, (a.x, a.y, b.z))])
        else:
            bm.faces.new([bm.verts.new(v) for v in (a, (a.x, b.y, a.z), b, (a.x, a.y, b.z))])

    for xs, z in ((FAR, 1.22), (NEAR[0], -1.22), (NEAR[1], -1.22), (NEAR[2], -1.22)):
        for a, b in zip(xs, xs[1:]):
            pane(a + 0.04, SILL, z, b - 0.04, HEAD, z)
    for c in DOORS:
        for lc in (c - 0.285, c + 0.285):
            pane(lc - 0.215, 1.05, -1.22, lc + 0.215, 2.28, -1.22)
    pane(5.42, 1.10, -OUT, 5.42, 2.40, OUT)
    pane(-5.42, SILL, -1.15, -5.42, HEAD, 1.15)
    for z0, z1 in BLINDS:
        pane(5.35, EYE, z0, 5.35, 2.40, z1)
    o = V.mesh_obj(A + "_Glass", bm, [M['glass']])
    o.data.uv_layers.new(name="UVMap")
    k3d.uv_world(o, 1.5)
    return o


REG = {"ad_burger": (0, 0, 2048, 512), "ad_civic": (0, 512, 2048, 1024), "board": (512, 1280, 1024, 1536),
       "alight": (1024, 1280, 1536, 1536), "lean": (1536, 1280, 1792, 1536), "hand": (1792, 1280, 2048, 1536)}   # CityBus_tex.REGIONS 와 같음


def led_mat():
    """CityBus 노선 LED 와 같은 그림으로 만든 안내 글자. 번호 칸은 비워 UV 로 잘라 쓴다."""
    path = os.path.join(TEX, A, f"T_{A}_StopLed.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    code = f"import sys; sys.path.insert(0, {os.path.join(HERE, '..', 'Vehicles')!r}); import CityBus_tex as T; T.route_sign({path!r}, '', '이번 정류장', '시장입구')"
    subprocess.run([PY, "-I", "-c", code], check=True)
    m = k3d.mat("M_PH_BusInterior_Led", (1, 1, 1), 0.35, emission=(1, 1, 1), strength=2.5)
    im = k3d.load_image(path, f"T_{A}_StopLed")
    k3d.image_node(m, im, k3d.principled(m).inputs['Base Color'])
    k3d.image_node(m, im, k3d.principled(m).inputs['Emission Color'])
    return m


def decals(M):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    def q(c, right, up, w, h, key, slot=0):
        c, right, up = B(*c), B(*right).normalized(), B(*up).normalized()
        f = bm.faces.new([bm.verts.new(c + right * (sx * w / 2) + up * (sy * h / 2)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        f.material_index = slot
        x0, y0, x1, y1 = REG[key] if key else (0.37 * 2048, 0, 2048, 2048)
        u0, v0, u1, v1 = x0 / 2048 + 0.0005, 1 - y1 / 2048 + 0.0005, x1 / 2048 - 0.0005, 1 - y0 / 2048 - 0.0005
        for l, t in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            l[uv].uv = t

    s = Vector((IN - COVE, CEIL - HEAD, 0)).normalized()                         # 경사판 위 방향 (z, y)
    mid = ((IN + COVE) / 2 - 0.003 * s.y, (HEAD + CEIL) / 2 - 0.003 * s.x)
    for x, key in ((2.2, "ad_burger"), (-1.8, "ad_civic")):                     # 먼 쪽: 통로에서 보면 오른쪽 = +x
        q((x, mid[1], mid[0]), (1, 0, 0), (0, s.y, -s.x), 1.2, 0.30, key)
    for x, key in ((1.0, "ad_civic"), (-3.4, "ad_burger")):                     # 문 쪽: 오른쪽 = -x
        q((x, mid[1], -mid[0]), (-1, 0, 0), (0, s.y, s.x), 1.2, 0.30, key)
    for c, key in ((DOORS[0], "board"), (DOORS[1], "alight")):
        for lc in (c - 0.285, c + 0.285):
            q((lc, 1.62, -1.214), (-1, 0, 0), (0, 1, 0), 0.36, 0.18, key)
            q((lc, 0.80, -1.197), (-1, 0, 0), (0, 1, 0), 0.15, 0.15, "lean" if lc < c else "hand")
    q((3.697, 2.40, -0.15), (0, 0, -1), (0, 1, 0), 0.78, 0.232, None, 1)        # 앞쪽 LED: 뒤에서 보면 오른쪽 = -z
    return V.mesh_obj(A + "_Decals", bm, [M['decal'], led_mat()])


# ---------------------------------------------------------------- 미리보기
def fp(tag, eye, look):
    """Bus 씬과 비슷한 조건의 1인칭 렌더: FOV 66, 하늘 밝은 회색, 바닥 Gray_Dark, 해·천장등 값은 씬에서 환산."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
    for m in bpy.data.materials:
        m.use_backface_culling = "unity_double_sided" not in m
    w = bpy.data.worlds.new("fp")
    sc.world = w
    if w.node_tree is None:
        w.use_nodes = True
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    path, mix = nt.nodes.new('ShaderNodeLightPath'), nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    a, b, r = (next(i for i in mix.inputs if i.identifier == k) for k in ('A_Color', 'B_Color', 'Factor_Float'))
    a.default_value, b.default_value = (0.5, 0.5, 0.5, 1), (0.87, 0.87, 0.87, 1)    # 환경광 / 카메라에 보이는 하늘
    nt.links.new(path.outputs['Is Camera Ray'], r)
    nt.links.new(next(o for o in mix.outputs if o.identifier == 'Result_Color'), bg.inputs['Color'])
    tmp = []
    sun = bpy.data.lights.new("s", 'SUN')
    sun.energy, sun.angle = 3.8, 0.03
    lo = bpy.data.objects.new("s", sun)
    lo.rotation_euler = (-B(0.303, -0.808, 0.505)).to_track_quat('Z', 'Y').to_euler()
    sc.collection.objects.link(lo)
    tmp.append(lo)
    for x in (-3.4, 0.0, 3.0):
        ld = bpy.data.lights.new("p", 'POINT')
        ld.energy, ld.shadow_soft_size, ld.use_shadow = 20, 0.02, False
        lo = bpy.data.objects.new("p", ld)
        lo.location = B(x, 2.2, -0.15)
        sc.collection.objects.link(lo)
        tmp.append(lo)
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("k3d_ground_fp", (0.28, 0.28, 0.28), 0.8))
    tmp.append(g)
    cd = bpy.data.cameras.new("c")
    cd.sensor_fit, cd.lens_unit, cd.angle, cd.clip_start, cd.clip_end = 'VERTICAL', 'FOV', math.radians(66), 0.03, 500
    co = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(co)
    co.location = B(*eye)
    co.rotation_euler = (B(*look) - B(*eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    tmp.append(co)
    sc.render.filepath = os.path.join(k3d.SRC, "Previews", f"{A}_fp_{tag}.png")
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    print("bus_interior: 렌더", sc.render.filepath)


def views():
    e = EYE
    fp("spawn", (3.45, e, -0.2), (-5.0, e, -0.2))        # 스폰 Y -90: 뒤쪽을 보고 시작한다
    fp("window", (2.3, e, 0.1), (2.3, 1.75, 2.0))
    fp("seat", (1.0, e, 0.1), (1.35, 0.85, 0.85))
    fp("front", (2.4, e, -0.15), (5.4, 1.5, 0.1))
    fp("door", (-0.9, e, 0.1), (-0.9, 1.45, -1.3))
    fp("rear", (-4.9, e, -0.1), (4.0, 1.5, -0.15))


def show_ao(m):
    """미리보기 전용: Unity 가 환경광에 곱하는 AO(MS 의 G)를 색에 곱한다. 내보낸 뒤에 부른다."""
    nt, p = m.node_tree, k3d.principled(m)
    ms = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image.name.endswith("_MS"))
    sep, mix = nt.nodes.new('ShaderNodeSeparateColor'), nt.nodes.new('ShaderNodeMix')
    mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    nt.links.new(ms.outputs['Color'], sep.inputs['Color'])
    nt.links.new(p.inputs['Base Color'].links[0].from_socket, next(i for i in mix.inputs if i.identifier == 'A_Color'))
    nt.links.new(sep.outputs['Green'], next(i for i in mix.inputs if i.identifier == 'B_Color'))
    nt.links.new(next(o for o in mix.outputs if o.identifier == 'Result_Color'), p.inputs['Base Color'])


def check_faces(glass_obj):
    """플레이어 눈이 갈 수 있는 자리에서 사방으로 광선을 쏜다. 뒷면에 맞거나 빠져나가면 Unity 에서 구멍으로 보인다."""
    dg, sc = bpy.context.evaluated_depsgraph_get(), bpy.context.scene
    n = 300
    dirs = []
    for i in range(n):
        y, a = 1 - 2 * (i + 0.5) / n, i * math.pi * (3 - 5 ** 0.5)
        r = (1 - y * y) ** 0.5
        dirs.append(Vector((r * math.cos(a), r * math.sin(a), y)))
    back, miss, hits = [], [], 0
    spots = [(x / 10, z) for x in range(-52, 34, 3) for z in (-0.4, -0.15, 0.1)]            # 통로
    spots += [(x / 10, z) for x in range(34, 47, 3) for z in (-0.85, -0.4, -0.15)]          # 앞문 앞
    spots += [(x / 10, -0.85) for x in range(-14, 0, 3)]                                    # 뒷문 앞
    for x, z in spots:
        for d in dirs:
            ok, loc, nor, _, o, _ = sc.ray_cast(dg, B(x, EYE, z), d)
            if not ok:
                miss.append((x, z, tuple(round(c, 2) for c in (-d.x, d.z, -d.y))))
            elif o != glass_obj:
                hits += 1
                if nor.dot(d) > 1e-4:
                    back.append((o.name, tuple(round(c, 2) for c in (-loc.x, loc.z, -loc.y))))
    print(f"bus_interior: 광선 {hits}, 뒷면 {len(back)} {back[:6]}, 샘 {len(miss)} {miss[:6]}")
    assert not back and not miss


# ---------------------------------------------------------------- 만들기
k3d.reset()
M = materials()
P = props(M)
S = shell(M)
hide_faces(P, M['outer'])
hide_faces(S, M['outer'])
keep = tuple(m.name for m in M.values() if m.name.startswith(f"M_{A}_"))
k3d.bake(P, size=2048, keep=keep, ao_distance=0.2, samples=64, margin=6)
place_seats(P)
k3d.bake(S, size=2048, keep=keep, ao_distance=0.5, samples=64, margin=6)
G, D = glazing(M), decals(M)
mark = bpy.data.objects.new(A + "_FrontMark", None)
bpy.context.scene.collection.objects.link(mark)
mark.location, mark.parent = B(5.45, 1.5, 0), S
ph.finish(A, S, extra=[P, G, D], notes={
    "origin": "프리팹 원점. 실내 바닥 윗면 y 0.32, 메시 아래 끝 y 0.22, 천장 밑 y 2.65.",
    "inside": "의자·봉·운전석은 회색 메시와 Col_ 콜라이더 자리 그대로. 판은 두께 있는 상자라 단면으로 충분하고 유리만 양면.",
    "outside": "창 가로대와 앞유리 차양 끝단이 눈높이 y 1.88 이라 Bus 씬 바닥 평면의 지평선을 가린다."})
check_faces(G)
show_ao(bpy.data.materials["M_" + A])
show_ao(bpy.data.materials["M_" + A + "_Props"])
k3d.preview(A, [S, P, G, D], views=((215, 14), (40, 28)), tag="ph")
views()

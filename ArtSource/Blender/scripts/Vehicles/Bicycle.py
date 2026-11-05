"""Bicycle: 한국 생활자전거 26인치 (스텝스루 프레임, 앞 바구니, 짐받이, 흙받이, 체인 케이스, 양발 스탠드).
높이 ~1.04 m (핸들바·바구니), 길이 ~1.78 m. 정면 -Y. 바퀴 2개는 차축 원점 자식 (로컬 X 축 회전).
앞바퀴·포크·핸들은 조향하지 않는 정적 메시 (주차용)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, bmesh
import numpy as np
from mathutils import Vector
import _vlib as V
k3d = V.k3d
FAST = bool(os.environ.get("CAR_FAST"))

A = "Bicycle"
RW = 0.323                     # 바퀴 반지름 (26 x 1.75)
FA, RA = (0, -0.53, RW), (0, 0.53, RW)
BB = (0, 0.09, 0.27)


def bez(p0, p1, p2, p3, n=12):
    P = [Vector(p) for p in (p0, p1, p2, p3)]
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]
        out.append(tuple(a))
    return out


def T(name, pts, r, mat, segs=8, cap=True):
    o = V.tube(A + name, pts, r, segs, mat, cap=cap)
    return o


def mats():
    M = {}
    M["paint"] = V.mat_paint(f"{A}_paint", (0.20, 0.03, 0.035), 0.32, 0.0, faded=(0.34, 0.13, 0.12), dirt=0.9, scale=2.0)
    M["chrome"] = V.mat_metal(f"{A}_chrome", (0.80, 0.80, 0.82), 0.12, 0.2, rust=0.45)
    M["black"] = V.mat_metal(f"{A}_black", (0.03, 0.03, 0.03), 0.45, 0.2, rust=0.5)
    M["rubber"] = V.mat_rubber(f"{A}_rubber")
    M["plastic"] = V.mat_plastic(f"{A}_plastic", (0.02, 0.02, 0.022), 0.6)
    M["saddle"] = V.mat_plastic(f"{A}_saddle", (0.03, 0.025, 0.022), 0.45, (0.07, 0.06, 0.05), dirt=0.6, grain=500)
    M["red"] = V.mat_plastic(f"{A}_red", (0.45, 0.01, 0.01), 0.25, (0.5, 0.08, 0.06), dirt=0.3)
    M["amber"] = V.mat_plastic(f"{A}_amber", (0.75, 0.30, 0.02), 0.25, (0.8, 0.45, 0.15), dirt=0.3)
    M["lens"] = V.mat_metal(f"{A}_lens", (0.9, 0.9, 0.85), 0.05, 0.05)
    # 체인 케이스: 프레임색 (데칼은 굽지 않는 별도 쿼드 Bicycle_Decal)
    g = V.NB(f"{A}_case")
    base = g.mix(g.mul(g.maprange(g.noise(3, 4, 0.6), 0.4, 0.8, 0, 1), 0.5), (0.20, 0.03, 0.035), (0.30, 0.11, 0.10))
    dm = V.grime_mask(g, low_z=0.35, scale=2.0)
    col = g.mix(dm, base, (0.13, 0.11, 0.09))
    M["case"] = g.out(col, g.add(0.35, g.mul(dm, 0.4)), 0.0, g.bump(g.noise(80, 2, 0.5), 0.1, 0.002))
    # 타이어 / 림
    g = V.NB(f"{A}_tire")
    dust = g.mul(g.maprange(g.noise(5, 5, 0.6), 0.35, 0.75, 0, 1), 0.7)
    col = g.mix(dust, (0.02, 0.02, 0.021), (0.09, 0.08, 0.07))
    knob = g.maprange(g.voronoi(160), 0.0, 0.35, 1, 0)
    M["tire"] = g.out(col, 0.85, 0.0, g.bump(knob, 0.5, 0.002))
    return M


def frame(M):
    P = []
    ST = (0, 0.25, 0.74)
    HTt, HTb = (0, -0.375, 0.845), (0, -0.425, 0.665)
    P.append(T("_head", [HTb, HTt], 0.019, M["paint"], 10))
    P.append(T("_main", bez((0, -0.395, 0.775), (0, -0.30, 0.47), (0, -0.07, 0.29), (0, 0.06, 0.29), 10), 0.022, M["paint"], 10))
    P.append(T("_main2", bez((0, -0.41, 0.71), (0, -0.33, 0.43), (0, -0.12, 0.33), (0, 0.075, 0.33), 8), 0.013, M["paint"], 8))
    P.append(T("_seat", [BB, ST], 0.017, M["paint"], 10))
    P.append(V.cyl(A + "_bb", 0.024, 0.08, BB, (0, math.pi / 2, 0), M["paint"], segs=16))
    for sx in (1, -1):
        P.append(T("_chain", [(sx * 0.03, 0.10, 0.27), (sx * 0.05, 0.32, 0.30), (sx * 0.062, 0.52, RW)], 0.010, M["paint"], 8))
        P.append(T("_sstay", [(sx * 0.022, 0.24, 0.715), (sx * 0.045, 0.40, 0.52), (sx * 0.062, 0.52, RW + 0.01)], 0.008, M["paint"], 8))
        # 포크
        P.append(T("_fork", [(sx * 0.03, -0.425, 0.655), (sx * 0.048, -0.465, 0.55), (sx * 0.05, -0.51, 0.40),
                             (sx * 0.05, -0.535, RW)], 0.011, M["chrome"], 8))
        P.append(V.box(A + "_dropout", (0.008, 0.03, 0.03), (sx * 0.062, 0.53, RW), M["paint"]))
        P.append(V.box(A + "_dropoutF", (0.008, 0.03, 0.03), (sx * 0.05, -0.53, RW), M["chrome"]))
        P.append(V.cyl(A + "_nut", 0.008, 0.012, (sx * 0.072, 0.53, RW), (0, math.pi / 2, 0), M["chrome"], segs=6))
        P.append(V.cyl(A + "_nutF", 0.008, 0.012, (sx * 0.060, -0.53, RW), (0, math.pi / 2, 0), M["chrome"], segs=6))
    P.append(V.box(A + "_crown", (0.09, 0.035, 0.03), (0, -0.425, 0.655), M["chrome"], bevel=0.008))
    # 안장·싯포스트 (스프링 안장)
    P.append(T("_post", [(0, 0.25, 0.70), (0, 0.272, 0.86)], 0.0127, M["chrome"], 10))
    sad = V.box(A + "_saddle", (0.21, 0.26, 0.055), (0, 0.29, 0.905), M["saddle"], bevel=0.025, segs=2)
    for v in sad.data.vertices:  # 앞은 좁게
        f = (v.co.y + 0.13) / 0.26
        v.co.x *= 0.45 + 0.55 * f
        v.co.z += 0.012 * (1 - f) - 0.01 * f * f
    P.append(sad)
    P.append(V.box(A + "_sadRail", (0.10, 0.16, 0.015), (0, 0.29, 0.872), M["black"], bevel=0.004))
    for sx in (1, -1):
        P.append(T("_spring", [(sx * 0.06 + 0.012 * math.cos(a), 0.355 + 0.012 * math.sin(a), 0.845 + a * 0.004)
                               for a in np.linspace(0, 6 * math.pi, 16)], 0.0028, M["chrome"], 3))
    # 핸들 (스윕백) + 그립 + 레버 + 벨
    P.append(T("_stem", [HTt, (0, -0.37, 0.93), (0, -0.39, 0.955)], 0.012, M["chrome"], 10))
    bar = [(-0.30, -0.17, 0.98), (-0.275, -0.25, 0.975), (-0.19, -0.355, 0.962), (0, -0.39, 0.955),
           (0.19, -0.355, 0.962), (0.275, -0.25, 0.975), (0.30, -0.17, 0.98)]
    P.append(T("_bar", bar, 0.011, M["chrome"], 10))
    for sx in (1, -1):
        P.append(T("_grip", [(sx * 0.28, -0.235, 0.976), (sx * 0.302, -0.15, 0.981)], 0.017, M["rubber"], 10))
        P.append(T("_lever", [(sx * 0.255, -0.27, 0.985), (sx * 0.30, -0.24, 0.965), (sx * 0.325, -0.19, 0.958)], 0.005, M["black"], 6))
        P.append(V.box(A + "_leverBody", (0.03, 0.035, 0.03), (sx * 0.25, -0.275, 0.985), M["black"], bevel=0.008))
    P.append(V.cyl(A + "_bell", 0.027, 0.02, (-0.17, -0.37, 0.985), (0, 0, 0), M["chrome"], segs=12, r2=0.012, bevel=0.004))
    # 브레이크 케이블
    P.append(T("_cableF", [(-0.25, -0.29, 0.99), (-0.16, -0.46, 0.93), (-0.03, -0.47, 0.78), (0, -0.445, 0.69)], 0.0028, M["plastic"], 5))
    P.append(T("_cableR", [(0.25, -0.29, 0.99), (0.15, -0.47, 0.92), (0.03, -0.44, 0.76), (0.025, -0.32, 0.52),
                           (0.025, -0.10, 0.33), (0.03, 0.10, 0.30), (0.06, 0.30, 0.31), (0.07, 0.48, 0.33)], 0.0028, M["plastic"], 4))
    P.append(V.box(A + "_caliper", (0.10, 0.025, 0.04), (0, -0.445, 0.68), M["chrome"], bevel=0.006))
    P.append(V.cyl(A + "_bandBrake", 0.045, 0.02, (0.075, 0.53, RW), (0, math.pi / 2, 0), M["black"], segs=16, bevel=0.003))
    # 흙받이 (크롬, 얇은 C 단면) + 지지대
    fp = [(-0.030, RW + 0.026), (-0.034, RW + 0.034), (0.0, RW + 0.041), (0.034, RW + 0.034), (0.030, RW + 0.026)]
    for nm, c, a0, a1 in (("_fenderF", FA, 40, 172), ("_fenderR", RA, -32, 138)):
        f = V.lathe(A + nm, fp, 18, mats=[M["chrome"]], axis='X', a0=math.radians(a0), a1=math.radians(a1))
        f.location = c
        s = f.modifiers.new("sol", 'SOLIDIFY')
        s.thickness = 0.0015
        P.append(f)
        for a in (a0 + 8, a1 - 14):
            ar = math.radians(a)
            for sx in (1, -1):
                P.append(T("_stay", [(sx * 0.045, c[1], c[2]), (sx * 0.03, c[1] + math.cos(ar) * (RW + 0.03), c[2] + math.sin(ar) * (RW + 0.03))],
                           0.0022, M["chrome"], 5))
    # 짐받이
    for sx in (1, -1):
        P.append(T("_rackRail", [(sx * 0.065, 0.27, 0.735), (sx * 0.07, 0.72, 0.745)], 0.0045, M["black"], 6))
        P.append(T("_rackStrut", [(sx * 0.07, 0.70, 0.745), (sx * 0.068, 0.53, RW + 0.02)], 0.0042, M["black"], 6))
        P.append(T("_rackStrut2", [(sx * 0.068, 0.50, 0.742), (sx * 0.066, 0.53, RW + 0.02)], 0.0042, M["black"], 6))
    for y in (0.34, 0.44, 0.54, 0.64, 0.72):
        P.append(T("_rackBar", [(-0.07, y, 0.745), (0.07, y, 0.745)], 0.0035, M["black"], 6))
    P.append(V.box(A + "_reflR", (0.08, 0.012, 0.035), (0, 0.735, 0.72), M["red"], bevel=0.004))
    # 체인 케이스 (전체 덮개, 오른쪽 = -X) + 크랭크 축 + 크랭크 + 페달
    pts = []
    for cx, cy, r in ((BB[1], BB[2], 0.115), (RA[1], RA[2], 0.055)):
        for a in np.linspace(0, 2 * math.pi, 40, endpoint=False):
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    hull = convex_hull(pts)
    bm = bmesh.new()
    vs = [bm.verts.new((-0.072, y, z)) for (y, z) in hull]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.x -= 0.03
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    case = V.mesh_obj(A + "_case", bm, [M["case"]])
    V.bevel_mod(case, 0.006, 1, angle=40)
    P.append(case)
    P.append(V.cyl(A + "_spindle", 0.009, 0.22, BB, (0, math.pi / 2, 0), M["chrome"], segs=12))
    for sx, ang in ((1, -0.6), (-1, math.pi - 0.6)):
        e = (0, BB[1] + 0.17 * math.cos(ang), BB[2] + 0.17 * math.sin(ang))
        P.append(beam(A + "_crank", (sx * 0.11, BB[1], BB[2]), (sx * 0.115, e[1], e[2]), 0.02, 0.012, M["chrome"]))
        P.append(V.box(A + "_pedal", (0.10, 0.065, 0.022), (sx * 0.175, e[1], e[2]), M["plastic"], bevel=0.006))
        P.append(V.box(A + "_pedRefl", (0.06, 0.008, 0.016), (sx * 0.175, e[1] - 0.034, e[2]), M["amber"], bevel=0.002))
    # 양발 스탠드
    for sx in (1, -1):
        P.append(T("_stand", [(sx * 0.035, 0.22, 0.30), (sx * 0.08, 0.27, 0.15), (sx * 0.13, 0.30, 0.012)], 0.008, M["black"], 6))
        P.append(V.box(A + "_foot", (0.04, 0.03, 0.012), (sx * 0.13, 0.30, 0.006), M["rubber"], bevel=0.003))
    P.append(V.box(A + "_standPivot", (0.09, 0.03, 0.03), (0, 0.22, 0.30), M["black"], bevel=0.006))
    # 앞 바구니 (철망) + 지지대 + 전조등
    bx, by, bz = 0.36, 0.28, 0.24
    cy, z0 = -0.65, 0.71
    for z in (z0, z0 + 0.08, z0 + 0.16, z0 + bz):
        r = 0.005 if z in (z0, z0 + bz) else 0.0028
        k = 1.0 + 0.08 * (z - z0) / bz  # 위로 갈수록 살짝 넓게
        rect = [(-bx / 2 * k, cy - by / 2 * k, z), (bx / 2 * k, cy - by / 2 * k, z), (bx / 2 * k, cy + by / 2 * k, z),
                (-bx / 2 * k, cy + by / 2 * k, z)]
        P.append(V.tube(A + "_bRing", rect, r, 5, M["black"], cap=False, closed=True))
    n_x, n_y = 8, 6
    for i in range(n_x + 1):
        x = -bx / 2 + bx * i / n_x
        for yy in (cy - by / 2, cy + by / 2):
            sgn = -1 if yy < cy else 1
            P.append(T("_bV", [(x, yy, z0), (x * 1.08, cy + sgn * by / 2 * 1.08, z0 + bz)], 0.0024, M["black"], 4, cap=False))
        P.append(T("_bB", [(x, cy - by / 2, z0), (x, cy + by / 2, z0)], 0.0024, M["black"], 4, cap=False))
    for j in range(1, n_y):
        y = cy - by / 2 + by * j / n_y
        for sx in (1, -1):
            P.append(T("_bS", [(sx * bx / 2, y, z0), (sx * bx / 2 * 1.08, cy + (y - cy) * 1.08, z0 + bz)], 0.0024, M["black"], 4, cap=False))
    for sx in (1, -1):
        P.append(T("_bStrut", [(sx * 0.10, cy - 0.06, z0), (sx * 0.06, -0.55, 0.45), (sx * 0.058, -0.53, RW)], 0.0045, M["black"], 6))
    P.append(T("_bBracket", [(0, cy + by / 2, z0 + 0.15), (0, -0.40, 0.93)], 0.006, M["black"], 6))
    P.append(V.cyl(A + "_lamp", 0.028, 0.06, (0, cy - by / 2 - 0.035, z0 + 0.05), (math.pi / 2, 0, 0), M["black"], segs=16, bevel=0.004))
    P.append(V.cyl(A + "_lampLens", 0.022, 0.006, (0, cy - by / 2 - 0.066, z0 + 0.05), (math.pi / 2, 0, 0), M["lens"], segs=16))
    P.append(V.box(A + "_reflF", (0.05, 0.008, 0.03), (0, cy - by / 2 - 0.009, z0 - 0.018), M["lens"], bevel=0.003))  # 바구니 아래 테에 매달림
    o = V.join(P, A + "_Frame")
    V.shade(o, 40)
    return o


def beam(name, p0, p1, w, h, mat):
    import _car
    return _car.beam(name, p0, p1, w, h, mat, up=(1, 0, 0))


def convex_hull(pts):
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def wheel(M):
    tp = [(0.023 * math.cos(a), 0.300 + 0.023 * math.sin(a)) for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 7)]
    tire = V.lathe(A + "_tire", tp, 48, mats=[M["tire"]])
    rp = [(-0.012, 0.279), (-0.013, 0.290), (-0.010, 0.297), (0.010, 0.297), (0.013, 0.290), (0.012, 0.279), (-0.012, 0.279)]
    rim = V.lathe(A + "_rim", rp, 48, mats=[M["chrome"]])
    hub = V.lathe(A + "_hub", [(-0.05, 0.006), (-0.045, 0.018), (-0.035, 0.032), (-0.028, 0.02), (0.028, 0.02),
                               (0.035, 0.032), (0.045, 0.018), (0.05, 0.006)], 16, mats=[M["chrome"]])
    P = [tire, rim, hub]
    for k in range(36):
        sd = 1 if k % 2 else -1
        th = 2 * math.pi * k / 36
        tr = th + sd * 0.42 * (1 if (k // 2) % 2 else -1)
        P.append(V.tube(A + "_spoke", [(sd * 0.032, 0.028 * math.cos(th), 0.028 * math.sin(th)),
                                      (sd * 0.004, 0.282 * math.cos(tr), 0.282 * math.sin(tr))], 0.0012, 4, M["chrome"], cap=False))
    P.append(T("_valve", [(0, 0.0, 0.282), (0, 0.0, 0.262)], 0.003, M["chrome"], 6))
    P.append(V.box(A + "_spokeRefl", (0.006, 0.05, 0.025), (0, 0.17, 0.0), M["amber"], bevel=0.003))
    w = V.join(P, A + "_WheelFront")
    V.shade(w, 40)
    return w


def main():
    k3d.reset()
    V.make_textures()
    M = mats()
    fr = frame(M)
    w = wheel(M)
    import _car
    _car.fix_emission()
    if not FAST:
        k3d.bake(fr, 1024, samples=16, ao_distance=0.08)
        k3d.bake(w, 512, samples=16, ao_distance=0.05)
    w.location = FA
    w2 = w.copy()
    w2.data = w.data.copy()
    bpy.context.scene.collection.objects.link(w2)
    w2.name = A + "_WheelRear"
    w2.location = RA
    # 체인 케이스 데칼 (굽지 않는 쿼드, -X 바깥면에서 1 mm, -X 쪽에서 볼 때 바로 읽힘)
    dm = V.flat_image(f"M_{A}_Decal", V.tex("bike_decal.png"), 0.6, alpha_clip=0.5)
    dec = V.quad(A + "_Decal", 0.34, 0.0425, dm, (-0.103, 0.28, 0.29), (0, 0, -math.pi / 2))
    for o in (w, w2, dec):
        o.parent = fr
    for nm, loc in (("Grip_L", (0.29, -0.20, 0.98)), ("Grip_R", (-0.29, -0.20, 0.98)), ("Saddle", (0, 0.29, 0.935)),
                    ("Basket", (0, -0.65, 0.73))):
        V.empty(f"{A}_Socket_{nm}", loc, fr)
    if FAST:
        k3d.preview(A, [fr], views=((60, 15), (240, 12), (90, 0)), tag="wip")
        return
    notes = ("생활자전거. 정면 -Y. 원점 바닥 중앙. Bicycle_WheelFront/WheelRear: 원점=차축, 로컬 X 축 회전. "
             "양발 스탠드가 내려진 주차 상태 (똑바로 섬). 체인 케이스·체인은 오른쪽(-X). "
             "Bicycle_Decal: 체인 케이스 데칼 '새싹 CITY 26' 쿼드 0.34x0.0425 m, M_Bicycle_Decal(bike_decal 1024x128, 알파 클립 0.5, 굽지 않음). "
             "소켓: Grip_L/Grip_R(손잡이), Saddle(안장 위), Basket(바구니 바닥). 약 9.4k tris (36살 바퀴 2개 포함, 8k 예산 약간 초과).")
    k3d.export(A, "Vehicles", [fr], notes=notes)
    k3d.preview(A, [fr])
    k3d.preview(A, [fr], views=((290, 12),), lens=35, tag="fp")


main()

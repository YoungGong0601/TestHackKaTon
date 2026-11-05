# 도로 모듈: StreetRoad(직선 12 m) / StreetRoadBusStop(버스 정차 18 m) / StreetRoadCrosswalk(횡단보도 12 m) / StreetRoadAlley(골목 6 m).
# 아스팔트·도료는 M_Tile(월드 UV) 이라 굽지 않는다. 모듈 길이가 타일 크기(2 m)의 정수배라 이어 붙여도 결이 맞는다.
# 실행: blender -b --factory-startup --python road.py [-- StreetRoad StreetRoadAlley ...]  (인자 없으면 전부)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d, bpy, bmesh
from mathutils import Vector

FONT_HAN = os.path.join(k3d.CACHE, "fonts", "BlackHanSans-Regular.ttf")
Z_PATCH, Z_OIL, Z_TAR, Z_PAINT = 0.0015, 0.002, 0.0025, 0.003     # 겹침 없이 층 높이 (m)
W = 8.0                                             # 왕복 2차로 폭 (경계석 앞면 사이)


def grid(name, x0, x1, y0, y1, z, mat, tile, nx=1, ny=1):
    """평평한 사각 판 (위를 향함)."""
    bm = bmesh.new()
    vs = [[bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, z)) for i in range(nx + 1)]
          for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    o = S.from_bm(name, bm, mat)
    k3d.uv_world(o, tile)
    return o


def slab(name, x0, x1, y0, y1, mat, tile, z0=0.0, h=Z_PAINT):
    """도료처럼 얇게 올라온 판 (바닥면 없음)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 - 0.001 if v.co.z < 0 else z0 + h))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.5], context='FACES')
    o = S.from_bm(name, bm, mat)
    k3d.uv_world(o, tile)
    return o


def road_text(name, s, width, stretch, loc, rot_z, mat):
    """노면 글자: 차로를 가로질러 쓰고 진행 방향(글자 위쪽)으로 길게 늘인다. rot_z=0 이면 글 위쪽 = +X."""
    o = S.text_mesh(name, s, 1.0, font=FONT_HAN, depth=Z_PAINT, mat=mat)
    w = o.dimensions.x
    k = width / w
    S.xform(o, scale=(k, k * stretch, 1))
    S.xform(o, rot=(0, 0, -math.pi / 2 + rot_z))
    S.xform(o, loc=(loc[0], loc[1], 0.0))
    k3d.uv_world(o, S.TILE_ASPHALT)
    return o


def _ribbon(bm, pts, w0, rng, taper=0.25):
    """점 목록을 따라가는 타르 리본. 폭은 구간마다 출렁이고 양끝은 가늘어진다."""
    n = len(pts)
    if n < 2:
        return
    ph, fq = rng.uniform(0, 6.28), rng.uniform(0.6, 1.4)
    prev = None
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        t = i / (n - 1)
        end = min(1.0, min(t, 1 - t) / taper)
        wdt = w0 * (0.72 + 0.28 * math.sin(ph + i * fq)) * rng.uniform(0.85, 1.15) * (0.35 + 0.65 * end)
        nx, ny = -ty / ln * wdt / 2, tx / ln * wdt / 2
        pair = (bm.verts.new((x - nx, y - ny, Z_TAR)), bm.verts.new((x + nx, y + ny, Z_TAR)))
        if prev:
            bm.faces.new((prev[0], pair[0], pair[1], prev[1]))
        prev = pair


def _walk(rng, x, y, ang, length, step, wob, box, anchor=None, pull=0.0):
    """조금씩 꺾이며 나아가는 균열 경로. anchor = (축 'x'|'y', 값): 그 선에서 멀어지지 않게 당긴다."""
    x0, x1, y0, y1 = box
    pts = [(x, y)]
    a = ang
    for _ in range(int(length / step)):
        a += rng.uniform(-wob, wob)
        if anchor:   # 긴 균열은 기준선(차로 경계·바퀴 자리)에서 멀어지면 되돌아온다
            k, v = anchor
            off = (y if k == "y" else x) - v
            side = (math.cos(a) if k == "y" else -math.sin(a)) * off   # 왼쪽 법선이 기준선에서 먼 쪽이면 +
            a = ang + max(-0.3, min(0.3, a - pull * side - ang))
        x, y = x + math.cos(a) * step, y + math.sin(a) * step
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            break
        j = rng.uniform(-0.012, 0.012)            # 자잘한 톱니 (진행 방향은 그대로)
        pts.append((x - math.sin(a) * j, y + math.cos(a) * j))
    return pts


def tar_cracks(name, rng, box, mat, long_y=(), trans_x=(), branches=4):
    """크랙 실링(타르): 차로 경계·바퀴 자리를 따라가는 긴 종균열(long_y) + 차로를 가로지르는 횡균열(trans_x)
    + 가지. 폭 4~8 cm, 구간마다 폭이 다르다."""
    x0, x1, y0, y1 = box
    bm = bmesh.new()
    mains = []
    for yy in long_y:
        L = rng.uniform(0.55, 0.9) * (x1 - x0)
        xs = rng.uniform(x0, x1 - L)
        mains.append(_walk(rng, xs, yy, 0.0, L, 0.14, 0.09, box, ("y", yy), 2.5))
    for xx in trans_x:
        up = rng.random() < 0.5
        ys = y0 + 0.1 if up else y1 - 0.1
        L = rng.uniform(0.45, 0.8) * (y1 - y0)
        mains.append(_walk(rng, xx, ys, math.pi / 2 if up else -math.pi / 2, L, 0.12, 0.14, box, ("x", xx), 2.0))
    for pts in mains:
        _ribbon(bm, pts, rng.uniform(0.05, 0.075), rng, 0.12)
    for _ in range(branches):   # 가지: 큰 균열에서 비스듬히 뻗는 짧은 금
        pts = rng.choice(mains)
        if len(pts) < 6:
            continue
        i = rng.randint(2, len(pts) - 3)
        (ax, ay), (bx, by) = pts[i - 1], pts[i + 1]
        base = math.atan2(by - ay, bx - ax) + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1)
        br = _walk(rng, *pts[i], base, rng.uniform(0.5, 1.6), 0.1, 0.35, box)
        _ribbon(bm, br, rng.uniform(0.035, 0.05), rng, 0.5)
    for f in bm.faces:          # 모두 위를 보게
        if f.normal.z < 0:
            f.normal_flip()
    o = S.from_bm(name, bm, mat)
    k3d.uv_world(o, 1.0)
    return o


def oil_band(name, x0, x1, yc, mat, w=0.9, period=6.0):
    """차로 가운데 기름 얼룩 띠 (투명 데칼, 보수판 위·타르 아래). U = 월드 X / 6 m 라 모듈끼리 이어진다."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x, y, Z_OIL)) for x, y in ((x0, yc - w / 2), (x1, yc - w / 2), (x1, yc + w / 2), (x0, yc + w / 2))]
    f = bm.faces.new(vs)
    for lp, (x, v) in zip(f.loops, ((x0, 0), (x1, 0), (x1, 1), (x0, 1))):
        lp[uv].uv = (x / period, v)
    return S.from_bm(name, bm, mat)


def oil_mat(A):
    m = S.decal_mat(f"M_{A}_Oil", os.path.join(S.TEX, "road_oil.png"), rough=0.45)
    nt = m.node_tree
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(tex.outputs['Alpha'], k3d.principled(m).inputs['Alpha'])
    k3d.flag(m, transparent=True)
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = 'BLENDED'
    return m


def patch(prefix, x0, x1, y0, y1, mats, rng):
    """절단 보수 자국: 새 아스팔트 판 + 둘레 타르 실링."""
    p = slab(prefix + "Patch", x0, x1, y0, y1, mats["patch"], S.TILE_ASPHALT_OLD, 0.0, Z_PATCH)
    du, dv = rng.random(), rng.random()
    for d in p.data.uv_layers[0].data:      # 결을 돌리고 옮겨 주변과 다른 균열 무늬
        d.uv = (d.uv[1] + du, d.uv[0] + dv)
    seal = []
    t = 0.02
    for a, b, c, d in ((x0 - t, x1 + t, y0 - t, y0 + t), (x0 - t, x1 + t, y1 - t, y1 + t),
                       (x0 - t, x0 + t, y0 + t, y1 - t), (x1 - t, x1 + t, y0 + t, y1 - t)):
        seal.append(slab(prefix + "Seal%d" % len(seal), a, b, c, d, mats["tar"], 1.0, 0.0, Z_TAR))
    return [p] + seal


def materials(A):
    return {"asphalt": S.tile_asphalt(), "white": S.tile_paint_white(),
            "patch": S.tile_asphalt_old(),
            "yellow": S.tile_paint_yellow(), "gutter": S.tile_gutter(),
            "tar": k3d.mat(f"M_{A}_Tar", (0.04, 0.04, 0.042), 0.5), "oil": oil_mat(A)}


def lane_lines(A, L, mats, x_ranges_center, x_ranges_edge_near, x_ranges_edge_far):
    """가운데 황색 실선 2줄(폭 0.12, 중심 간격 0.24) + 흰 가장자리선(폭 0.1, 경계석에서 0.4 m 안쪽)."""
    out = []
    for i, (a, b) in enumerate(x_ranges_center):
        for k, yc in enumerate((-0.12, 0.12)):
            out.append(slab(f"{A}_LC{i}{k}", a, b, yc - 0.06, yc + 0.06, mats["yellow"], S.TILE_ASPHALT))
    for i, (a, b) in enumerate(x_ranges_edge_near):
        out.append(slab(f"{A}_LN{i}", a, b, -W / 2 + 0.40, -W / 2 + 0.50, mats["white"], S.TILE_ASPHALT))
    for i, (a, b) in enumerate(x_ranges_edge_far):
        out.append(slab(f"{A}_LF{i}", a, b, W / 2 - 0.50, W / 2 - 0.40, mats["white"], S.TILE_ASPHALT))
    return out


def common_notes(L):
    return (f"도로 모듈 {L:g} m(X) x {W:g} m(Y). 원점 = 노면 중앙(z=0 = 아스팔트 윗면). 앞(-Y, Unity +Z 반대쪽 아님: 정면) = "
            "버스정류장/보도 쪽 차로. 높이 쌓기: 노면 z=0 -> Unity y=-0.14(보도면 y=0 보다 14 cm 낮음, 프로토타입 zn). "
            "경계석(StreetCurb) 앞면을 y=±4.0 에 붙인다. 우측통행: 앞 차로(-Y)는 +X 로 진행. "
            "층: 보수판(M_Tile_Street_AsphaltOld = 균열 많은 옛 아스팔트 asphalt_02, 3 m) +1.5 mm, 타르 실링(폭 4~8 cm) +2.5 mm, 도료 +3 mm(두께 3 mm, 실제 융착식 도료 두께). "
            "M_Tile 은 월드 UV(기본 노면 M_Tile_Street_Asphalt = clean_asphalt 와 도료 2 m, 보수판 3 m) 라 모듈 끝끼리 결이 이어진다. "
            "차로 가운데(y ±1.85)에 기름 얼룩 띠 M_<에셋>_Oil(투명 데칼 0.9 m, +2 mm, U = 월드 X / 6 m). "
            "맨홀은 StreetManhole, 빗물받이는 StreetDrain 을 따로 놓는다.")


def build_road(A, L, kind):
    k3d.reset()
    mats = materials(A)
    rng = random.Random(sum(map(ord, A)))  # 고정 시드
    x0, x1 = -L / 2, L / 2
    surf = grid(A + "_Surface", x0, x1, -W / 2, W / 2, 0.0, mats["asphalt"], S.TILE_ASPHALT, int(L / 3), 2)
    parts = []
    notes = common_notes(L)
    if kind == "straight":
        parts += lane_lines(A, L, mats, [(x0, x1)], [(x0, x1)], [(x0, x1)])
        parts += patch(A + "_P1", -4.2, -1.6, -3.3, -1.4, mats, rng)        # 앞 차로 바퀴자국 자리 보수
        parts += patch(A + "_P2", 2.4, 3.5, 1.1, 2.0, mats, rng)
        parts.append(tar_cracks(A + "_Tar", rng, (x0 + 0.2, x1 - 0.2, -W / 2 + 0.3, W / 2 - 0.3), mats["tar"],
                                long_y=(0.38, 2.75), trans_x=(-0.8, 4.6), branches=5))
        notes += " 직선 구간. 가운데 황색 복선 + 양쪽 흰 가장자리선 + 보수판 2곳 + 크랙 실링."
    elif kind == "bus":
        z0 = 8.0
        parts += lane_lines(A, L, mats, [(x0, x1)], [(x0, -z0), (z0, x1)], [(x0, x1)])
        # 정차대: 경계석 0.55 m 안 황색 실선 + 3.1 m 안 황색 점선(0.7 m, 1.2 m 간격) + '버스 정차'
        parts.append(slab(A + "_BusSolid", -z0, z0, -W / 2 + 0.48, -W / 2 + 0.62, mats["yellow"], S.TILE_ASPHALT))
        x = -z0
        i = 0
        while x + 0.7 <= z0 + 1e-6:
            parts.append(slab(f"{A}_BusDash{i}", x, x + 0.7, -W / 2 + 3.03, -W / 2 + 3.17, mats["yellow"],
                              S.TILE_ASPHALT))
            x += 1.2
            i += 1
        parts.append(road_text(A + "_TextBus", "버스 정차", 2.7, 2.8, (-5.0, -W / 2 + 1.75), 0.0, mats["yellow"]))
        parts += patch(A + "_P1", 1.0, 4.6, -3.7, -2.2, mats, rng)          # 버스 정차 자리 패임 보수
        parts.append(tar_cracks(A + "_Tar", rng, (x0 + 0.2, x1 - 0.2, -W / 2 + 0.3, W / 2 - 0.3), mats["tar"],
                                long_y=(-0.36, -2.0, 2.2), trans_x=(-7.0, 6.2), branches=6))
        notes += (" 버스 정차대 16 m(x -8~8): 황색 실선(경계석 0.55 m 안), 황색 점선 0.7 m/1.2 m(경계석 3.1 m 안), "
                  "노면 글자 '버스 정차'(황색, 앞 차로 x=-5, 차로를 가로질러 2.7 m, 진행 방향 길이 약 1.6 m, "
                  "+X 로 달리는 운전자가 읽는 방향). Socket_BusStop = 버스 정차 위치(앞문 기준).")
    elif kind == "crosswalk":
        cw = 2.5
        stop = 4.75
        parts += lane_lines(A, L, mats, [(x0, -stop - 0.225), (stop + 0.225, x1)],
                            [(x0, -cw - 0.25), (cw + 0.25, x1)], [(x0, -cw - 0.25), (cw + 0.25, x1)])
        for i in range(8):                           # 줄무늬 폭 0.5, 간격 0.5 (한국식: 양옆 테두리 없음)
            yc = -3.5 + i
            parts.append(slab(f"{A}_Zebra{i}", -cw, cw, yc - 0.25, yc + 0.25, mats["white"], S.TILE_ASPHALT))
        parts.append(slab(A + "_StopNear", -stop - 0.225, -stop + 0.225, -W / 2 + 0.1, -0.2, mats["white"],
                          S.TILE_ASPHALT))
        parts.append(slab(A + "_StopFar", stop - 0.225, stop + 0.225, 0.2, W / 2 - 0.1, mats["white"],
                          S.TILE_ASPHALT))
        parts.append(tar_cracks(A + "_Tar", rng, (x0 + 0.2, x1 - 0.2, -W / 2 + 0.3, W / 2 - 0.3), mats["tar"],
                                long_y=(0.36,), trans_x=(-4.0,), branches=3))
        notes += (" 횡단보도 폭 5 m(x -2.5~2.5), 줄무늬 0.5 m/간격 0.5 m x 8줄, 정지선 폭 0.45 m(횡단보도에서 2 m 앞). "
                  "가장자리선·중앙선은 정지선/횡단보도에서 끊긴다. 양쪽 보도는 StreetSidewalkRamp + StreetCurbRamp "
                  "(낮춘 구간 x -3~3)를 같은 X 에 맞춘다. 신호등 StreetCrosswalkSignal 은 보도 쪽 x=±3 부근.")
    parts += [oil_band(f"{A}_Oil{k}", x0, x1, yc, mats["oil"]) for k, yc in enumerate((-1.85, 1.85))]
    body = S.join([surf] + parts, A + "_Road")
    if kind == "bus":
        S.empty(A + "_Socket_BusStop", (2.0, -W / 2 + 1.5, 0.0), parent=body)
    return [body], notes


def build_alley():
    A = "StreetRoadAlley"
    k3d.reset()
    mats = materials(A)
    rng = random.Random(77)
    L, WA = 6.0, 5.2
    gy0, gy1 = WA / 2 - 0.34, WA / 2                 # 뒤(+Y) 가장자리 U형 측구 덮개 0.34 m
    surf = grid(A + "_Surface", -L / 2, L / 2, -WA / 2, gy0, 0.0, mats["asphalt"], S.TILE_ASPHALT, 2, 2)
    # 측구 덮개: 0.5 m 콘크리트 판 (줄눈 4 mm, 판마다 1~2 mm 높낮이), 가운데 0.64 m 는 빗물받이 자리
    covers = []
    x = -L / 2
    i = 0
    while x < L / 2 - 1e-6:
        xe = min(L / 2, x + 0.5)
        if xe > -0.32 and x < 0.32:
            x = 0.32
            continue
        if x < -0.32 < xe:
            xe = -0.32
        dz = rng.uniform(-0.002, 0.002)
        c = S.box(f"{A}_Cover{i}", (xe - x - 0.004, gy1 - gy0 - 0.004, 0.06),
                  ((x + xe) / 2, (gy0 + gy1) / 2, -0.03 + 0.004 + dz), mat=mats["gutter"], bevel=0.006, segs=2)
        k3d.apply_all(c)
        k3d.uv_world(c, S.TILE_GUTTER)
        covers.append(c)
        x = xe
        i += 1
    # 빗물받이 자리 밑 어두운 구덩이 (StreetDrain 을 안 놓아도 구멍이 비치지 않게)
    pit = grid(A + "_Pit", -0.32, 0.32, gy0, gy1, -0.004, k3d.mat("M_StreetRoadAlley_Pit", (0.01, 0.01, 0.01), 0.9),
               1.0)
    ptc = patch(A + "_P1", -2.2, -0.6, -1.9, -0.7, mats, rng)
    tar = tar_cracks(A + "_Tar", rng, (-L / 2 + 0.1, L / 2 - 0.1, -WA / 2 + 0.15, gy0 - 0.06), mats["tar"],
                     long_y=(gy0 - 0.12, -0.1), trans_x=(1.6,), branches=4)
    oil = oil_band(A + "_Oil", -L / 2, L / 2, -0.3, mats["oil"])
    body = S.join([surf, pit] + covers + ptc + [tar, oil], A + "_Road")
    # 켜고 끄는 자식: 거주자 우선 주차 선(흰색, 6 m 칸) / '천천히'
    pk = [slab(A + "_PkLong", -L / 2, L / 2, -0.71, -0.61, mats["white"], S.TILE_ASPHALT),
          slab(A + "_PkCross", -L / 2, -L / 2 + 0.1, -WA / 2 + 0.05, -0.71, mats["white"], S.TILE_ASPHALT)]
    parking = S.join(pk, A + "_Parking")
    S.parent(parking, body)
    slow = S.join([road_text(A + "_TextSlowT", "천천히", 1.9, 2.4, (1.2, 0.85), math.pi, mats["white"])],
                  A + "_TextSlow")
    S.parent(slow, body)
    S.empty(A + "_Socket_Drain", (0.0, (gy0 + gy1) / 2, 0.0), parent=body)
    notes = (f"골목 모듈 {L:g} m(X) x {WA:g} m(Y), 보도 없음. 원점 = 노면 중앙(z=0 = 골목 바닥 = Unity y=0, 프로토타입 골목과 같은 높이). "
             "뒤(+Y) 가장자리에 폭 0.34 m U형 측구 콘크리트 덮개(0.5 m 판, M_Tile_Street_GutterConcrete), "
             "가운데 0.64 m 는 빗물받이 자리: StreetDrain 을 Socket_Drain 에 회전 없이(긴 변 X) 놓는다(6 m 마다 1개 = 프로토타입). "
             "자식 StreetRoadAlley_Parking = 거주자 우선 주차 흰 선(앞쪽 1.9 m 폭, 6 m 칸, 모듈마다 칸 경계 1줄), "
             "차로 가운데 y=-0.3 에 기름 얼룩 띠(M_StreetRoadAlley_Oil, 투명 데칼). StreetRoadAlley_TextSlow = 노면 글자 '천천히'(흰색, 1.9 m x 약 1.5 m, -X 로 진행하는 차에서 바로 읽힘 = +X 로 걷는 사람에겐 거꾸로, 프로토타입은 골목에 1번만) — "
             "필요 없는 모듈에서는 끈다. 보수판 1곳 + 크랙 실링. 모듈 길이 6 m = 타일(3/2/0.6 m) 정수배. min_z -0.058 = 측구 덮개 판이 노면 아래로 묻힌 두께(의도).")
    return [body], notes


def shoot(A, roots, notes, L):
    S.finish(A, roots, None, notes, views=((25, 38), (205, 24)),
             extra=[dict(dist=min(9.0, L * 0.7), eye=1.69, look_h=0.0, az=-62, lens=35, cx=(L * 0.18, -1.0, 0.0))])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    todo = argv or ["StreetRoad", "StreetRoadBusStop", "StreetRoadCrosswalk", "StreetRoadAlley"]
    for A in todo:
        if A == "StreetRoadAlley":
            roots, notes = build_alley()
            S.finish(A, roots, None, notes, views=((25, 38), (205, 24)),
                     extra=[dict(dist=5.5, eye=1.55, look_h=0.0, az=-70, lens=35, cx=(1.0, 0.0, 0.0))])
            continue
        L, kind = {"StreetRoad": (12.0, "straight"), "StreetRoadBusStop": (18.0, "bus"),
                   "StreetRoadCrosswalk": (12.0, "crosswalk")}[A]
        roots, notes = build_road(A, L, kind)
        shoot(A, roots, notes, L)

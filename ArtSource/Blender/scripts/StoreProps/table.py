# StoreTable (2인 0.72x0.72) / StoreTable4 (4인 1.05x0.74, 부스용): HPL 상판 + ABS 엣지밴드 + 분체도장 스틸 받침
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

TOP_Z, TOP_T = 0.75, 0.028


def rrect_slab(name, w, d, t, r, z0, mats, segs=6):
    """평면 모서리가 둥근 판. 슬롯: 0 윗면, 1 옆면(엣지밴드), 2 아랫면."""
    bm = bmesh.new()
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90),
                       (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for i in range(segs + 1):
            a = math.radians(a0 + 90 * i / segs)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z0 + t)) for x, y in pts]
    bm.faces.new(top).material_index = 0
    bm.faces.new(list(reversed(bot))).material_index = 2
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((bot[i], bot[j], top[j], top[i])).material_index = 1
    o = from_bm(bm, name)
    for m in mats:
        o.data.materials.append(m)
    bevel(o, 0.0025, 3)
    return o


def arm(name, L, w0, w1, h0, h1, zb, ang, mat, x0=0.0):
    """끝으로 갈수록 가늘고 낮아지는 받침 다리 (+X 방향으로 만든 뒤 ang 회전)."""
    bm = bmesh.new()
    v = [bm.verts.new(c) for c in ((x0, -w0 / 2, zb), (x0, w0 / 2, zb), (L, w1 / 2, zb), (L, -w1 / 2, zb),
                                   (x0, -w0 / 2, zb + h0), (x0, w0 / 2, zb + h0), (L, w1 / 2, zb + h1), (L, -w1 / 2, zb + h1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(bm, name, mat)
    o.rotation_euler = (0, 0, ang)
    bevel(o, 0.004, 3)
    return o


def mats(A):
    return dict(
        top=wood(f"M_{A}_TopSrc", 0.8, tint=(0.95, 0.84, 0.7), rough=0.38, wipe=0.22, edge_dark=0.25),
        edge=plastic(f"M_{A}_EdgeSrc", (0.028, 0.024, 0.02), rough=0.38, grime=0.4, wear=0.7, scuff=0.5),
        back=plastic(f"M_{A}_BackerSrc", (0.5, 0.47, 0.42), rough=0.75, grime=0.3, wear=0.0, scuff=0.0),
        steel=powder_coat(f"M_{A}_SteelSrc", (0.02, 0.02, 0.022), rough=0.48, wear=0.3),
        base=powder_coat(f"M_{A}_BaseSrc", (0.02, 0.02, 0.022), rough=0.5, wear=0.35, scratch=0.12, peel=0.0,
                         metal_col=(0.25, 0.25, 0.26)),  # 드러난 강철은 어두운 회색 (흰 얼룩 방지)
        glide=plastic(f"M_{A}_GlideSrc", (0.02, 0.02, 0.02), rough=0.55, grime=0.9, wear=0.2, scuff=0.2),
        screw=stainless(f"M_{A}_ScrewSrc", 0.35, 'Z', smudge=0.2),
    )


def screws(A, pts, z, M):
    return [cyl(f"{A}_Screw{i}", 0.0048, 0.0025, (x, y, z - 0.0025), 12, M['screw'], bev=0.001, seg=1)
            for i, (x, y) in enumerate(pts)]


def build(A, W, D, twin):
    k3d.reset()
    M = mats(A)
    parts = [rrect_slab(A + "_Top", W, D, TOP_T, 0.03, TOP_Z - TOP_T, [M['top'], M['edge'], M['back']])]
    zb = TOP_Z - TOP_T  # 상판 밑면
    cols = [(-0.31, 0), (0.31, 0)] if twin else [(0, 0)]
    rc = 0.03 if twin else 0.038
    for k, (cx, cy) in enumerate(cols):
        # 기둥 + 위/아래 칼라
        parts.append(cyl(f"{A}_Col{k}", rc, zb - 0.07, (cx, cy, 0.06), 32, M['steel']))
        parts.append(cyl(f"{A}_ColTop{k}", rc + 0.012, 0.014, (cx, cy, zb - 0.02), 32, M['steel']))
        parts.append(cyl(f"{A}_Hub{k}", rc + 0.03, 0.05, (cx, cy, 0.014), 32, M['base'], bev=0.006, seg=3))
        # 다리: 2인은 X자 4갈래, 4인은 각 기둥마다 앞뒤(Y) 2갈래
        angs = [math.radians(45 + 90 * i) for i in range(4)] if not twin else [math.radians(90), math.radians(270)]
        L = 0.3 if not twin else 0.31
        for i, a in enumerate(angs):
            ar = arm(f"{A}_Arm{k}{i}", L, 0.07, 0.046, 0.048, 0.026, 0.014, a, M['base'])
            ar.location = (cx, cy, 0)
            parts.append(ar)
            gx, gy = cx + math.cos(a) * (L - 0.028), cy + math.sin(a) * (L - 0.028)
            parts.append(cyl(f"{A}_Glide{k}{i}", 0.019, 0.012, (gx, gy, 0.002), 24, M['glide'], bev=0.003, seg=2))
            parts.append(cyl(f"{A}_GlideStem{k}{i}", 0.006, 0.006, (gx, gy, 0.0), 12, M['screw'], bev=0.001, seg=1))
    # 상판 밑 스파이더 브라켓 + 나사
    plate_z = zb - 0.005
    if twin:
        parts.append(box(A + "_Rail", (0.78, 0.05, 0.03), (0, 0, zb - 0.015), M['steel'], bev=0.003))
        for k, (cx, cy) in enumerate(cols):
            parts.append(box(f"{A}_Flange{k}", (0.16, 0.16, 0.006), (cx, cy, zb - 0.003), M['steel'], bev=0.002))
        sp = [(cx + sx * 0.06, sy * 0.06) for cx, _ in cols for sx in (-1, 1) for sy in (-1, 1)]
        sp += [(sx * 0.37, 0) for sx in (-1, 1)]
    else:
        for i in range(2):
            parts.append(box(f"{A}_Spider{i}", (0.5, 0.04, 0.006), (0, 0, zb - 0.003), M['steel'], bev=0.002,
                             rot=(0, 0, math.radians(45 + 90 * i))))
        parts.append(cyl(A + "_SpiderHub", 0.07, 0.008, (0, 0, zb - 0.008), 32, M['steel']))
        sp = [(math.cos(math.radians(45 + 90 * i)) * r, math.sin(math.radians(45 + 90 * i)) * r)
              for i in range(4) for r in (0.1, 0.22)]
    parts += screws(A, sp, plate_z - 0.001 if not twin else zb - 0.006, M)
    for p in parts:
        ensure_uv(p)
    o = k3d.join(parts, A)
    k3d.set_origin(o, Vector((0, 0, 0)))
    k3d.bake(o, 1024)
    return o


def finish(A, o, sockets, notes):
    for nm, loc in sockets:
        socket(f"{A}_Socket_{nm}", loc, o)
    print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
    k3d.export(A, "Store", [o], notes=notes)
    k3d.preview(A, [o])
    k3d.preview(A, [o], views=((0, 40),), lens=35, tag="fp")


A = "StoreTable"
o = build(A, 0.72, 0.72, False)
finish(A, o, [("ItemPlace", (0, 0, TOP_Z)), ("Napkin", (-0.26, 0.26, TOP_Z))],
       "2인 테이블 0.72x0.72, 상판 윗면 0.75m. HPL 우드 상판 + 검정 ABS 엣지밴드 + X자 분체도장 주철 받침(수평 조절발). "
       "의자는 앞뒤(Y) ±0.62m 에 마주 배치. 소켓: _Socket_ItemPlace(상판 중앙, 쟁반 놓는 곳), _Socket_Napkin(냅킨통 자리, 뒤 왼쪽 모서리).")

A = "StoreTable4"
o = build(A, 1.05, 0.74, True)
finish(A, o, [("ItemPlaceL", (-0.26, 0, TOP_Z)), ("ItemPlaceR", (0.26, 0, TOP_Z)), ("Napkin", (-0.43, 0.26, TOP_Z))],
       "4인(부스) 테이블 1.05(X) x 0.74(Y), 상판 윗면 0.75m, 쌍기둥 받침. 프로토타입 부스(x=4.72)는 긴 변이 벽에 수직이므로 Y축 90도 회전해 배치. "
       "소켓: _Socket_ItemPlaceL/R(쟁반 2개 자리), _Socket_Napkin.")

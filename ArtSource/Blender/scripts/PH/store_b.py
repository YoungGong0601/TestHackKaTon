"""PH_Seat, PH_Booth, PH_Hood, PH_Fryer, PH_KitchenBench.
실행: blender -b --factory-startup --python store_b.py [-- PH_Fryer ...]  (이름을 주면 그 행만)

주방 세 행은 매장 좌표(store_kitchen.py 와 같은 수치, 정면 +X)로 짜고 to_asset 으로 에셋 좌표(정면 -Y)로 돌린다.
매장 좌표 x, y 가 그대로 친구 프리팹의 x, z 다. 튀김기는 프로토타입처럼 작업대 부피 안에 놓이므로
작업대 앞선을 뒤로, 튀김기 앞면을 앞으로 물려 튀김기가 작업대를 뚫고 나와 보이게 맞췄다."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Store")]
import ph, bpy, bmesh
import storelib as S
from mathutils import Matrix, Vector

k3d = S.k3d
B, C = S.boxz, S.cyl
RX = (math.pi / 2, 0, math.pi / 2)   # +X 를 보는 판


def islands(bm):
    """연결된 정점 묶음들."""
    seen = set()
    for v in bm.verts:
        if v in seen:
            continue
        seen.add(v)
        isl = [v]
        for a in isl:
            for e in a.link_edges:
                w = e.other_vert(a)
                if w not in seen:
                    seen.add(w)
                    isl.append(w)
        yield isl


def crop(src, lo, hi):
    """src 복사본에서 월드 범위 안에 통째로 들어가는 조각만 남긴다 (변환은 정점에 굽는다)."""
    o = src.copy()
    o.data = src.data.copy()
    o.data.transform(src.matrix_world)
    o.parent = None
    o.matrix_world = Matrix.Identity(4)
    bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = [v for isl in islands(bm)
            if not all(lo[i] <= v.co[i] <= hi[i] for v in isl for i in range(3)) for v in isl]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    return o


def to_asset(objs, c=(0, 0, 0)):
    """매장 좌표(정면 +X, 원점 c) -> 에셋 좌표(정면 -Y). 이후 ph.turn(-90) 이면 앞 +X."""
    A = ph.turn(-90) @ Matrix.Translation(-Vector(c))
    bpy.context.view_layer.update()
    for o in objs:
        o.data.transform(A @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)


def done(name, o, az):
    ph.finish(name, o)
    for x in bpy.data.objects:
        x.hide_render = x is not o
    k3d.preview(name, [o], views=((az + 35, 18), (az - 145, 12)), tag="ph")


def lab(objs, key, w, h, loc, screen=False):
    """아틀라스 글자 판 (정면 +X). screen=True 면 발광 화면."""
    u0, v0, u1, v1 = S.atlas_uv("kitchen_signs.png", key)    # box1, box3 칸은 아틀라스 오른쪽 끝을 넘어 반대쪽이 비친다
    m = bpy.data.materials["M_StoreKitchen_Screens" if screen else "M_StoreKitchen_Signs"]
    objs.append(S.quad("lb", w, h, loc, m, rot=RX, uv=(u0, v0, min(u1, 0.999), v1)))


def bake_with(parts, labels, name, size, c=(0, 0, 0)):
    """parts 를 굽고 글자 판을 붙인 PH 메시를 돌려준다."""
    o = S.join(parts, name + "_Src")
    lb = S.join(labels, name + "_Labels")
    to_asset([o, lb], c)
    k3d.bake(o, size, samples=32, ao_distance=0.08, name=name)
    return ph.part(name, [o, lb], ph.turn(-90))


# ---------------------------------------------------------------- 의자, 부스

def seat():
    """의자 정면은 프로토타입에서 +z3 (회전 0), 친구 프레임에서 -Z."""
    ph.load("Store", "StoreChair")
    o = ph.part("PH_Seat", [o for o in bpy.data.objects if o.type == 'MESH'], ph.turn(180))
    done("PH_Seat", o, 180)


def low_back(o):
    """좌면 0.54 -> 0.46, 등받이 윗끝 1.26 -> 0.80. 조각별 높이만 옮겨 구운 텍스처를 그대로 쓴다."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for isl in islands(bm):
        z = [v.co.z for v in isl]
        lo, hi = min(z), max(z)
        if lo > 1.2:                  # 상단 캡
            a, b = lo - 0.46, hi - 0.46
        elif hi > 1.2:                # 등 쿠션(0.43 부터), 등판(바닥부터)
            a, b = max(lo - 0.08, 0), 0.775
        elif lo > 0.39:               # 좌석 쿠션, 파이핑
            a, b = lo - 0.08, hi - 0.08
        elif hi > 0.39:               # 받침
            a, b = lo, hi - 0.08
        else:                         # 킥플레이트
            continue
        for v in isl:
            v.co.z = a + (v.co.z - lo) * (b - a) / (hi - lo)
    bm.to_mesh(o.data)
    bm.free()


def booth():
    """프로토타입의 이 블록은 벤치 2개 + 부스 테이블을 덮는 충돌 상자다 (s.wall(4.32, P-1.15, 5.5, P+1.15)).
    벤치 두 모듈을 Z 로 이어 벽(+X)에 붙이고 그 앞에 StoreTable4 를 둬 폭 1.18 을 채운다."""
    ph.load("Store", "StoreBoothBench")
    frame, cush = bpy.data.objects["StoreBoothBench"], bpy.data.objects["StoreBoothBench_Cushion"]
    cush.parent = None
    with bpy.data.libraries.load(os.path.join(k3d.SRC, "Blender", "Store", "StoreTable4.blend")) as (src, dst):
        dst.objects = ["StoreTable4"]
    table = dst.objects[0]
    bpy.context.scene.collection.objects.link(table)
    table.location = (0, -0.25, 0)    # 앞 끝이 좌석 앞선을 6cm 덮는다
    low_back(frame)
    low_back(cush)
    parts = [table]
    for x in (-0.55, 0.55):           # 캡 끝끼리 맞닿는 간격 (길이 2.2)
        for s in (frame, cush):
            c = s.copy()
            bpy.context.scene.collection.objects.link(c)
            c.matrix_world = Matrix.Translation((x, 0.31, 0)) @ Matrix.Diagonal((1.111, 1, 1, 1))
            parts.append(c)
    done("PH_Booth", ph.part("PH_Booth", parts, ph.turn(90)), 90)


# ---------------------------------------------------------------- 주방

def hood():
    """규격이 StoreKitchen_Line 후드와 같아 조각만 뽑는다. 덕트, 천장 행거는 높이 0.42 를 넘어 뺀다."""
    ph.load("Store", "StoreKitchen")
    lo, hi = (-6.01, 1.09, 2.23), (-4.93, 3.71, 2.67)
    parts = [crop(bpy.data.objects[n], lo, hi) for n in ("StoreKitchen_Line", "StoreKitchen_Labels")]
    to_asset(parts, (-5.4675, 2.4, 2.24))
    done("PH_Hood", ph.part("PH_Hood", parts, ph.turn(-90)), -90)


def basket(wire, grip, loc):
    """튀김 바구니 + 손잡이 (store_kitchen.py 와 같고 손잡이만 짧게: 높이 1.05, 앞 0.38 안에 든다)."""
    p = []
    bx, by, bz = 0.36, 0.19, 0.14
    for y in (-by / 2, by / 2):
        p.append(B("r", -bx / 2, bx / 2, y - 0.003, y + 0.003, bz / 2 - 0.006, bz / 2, wire, 0))
    for x in (-bx / 2, bx / 2):
        p.append(B("r", x - 0.003, x + 0.003, -by / 2, by / 2, bz / 2 - 0.006, bz / 2, wire, 0))
    p.append(B("bt", -bx / 2, bx / 2, -by / 2, by / 2, -bz / 2, -bz / 2 + 0.003, wire, 0))
    for i in range(10):
        x = -bx / 2 + (i + 0.5) * bx / 10
        for y in (-by / 2, by / 2):
            p.append(B("v", x - 0.0015, x + 0.0015, y - 0.0015, y + 0.0015, -bz / 2, bz / 2, wire, 0))
    for i in range(5):
        y = -by / 2 + (i + 0.5) * by / 5
        for x in (-bx / 2, bx / 2):
            p.append(B("v", x - 0.0015, x + 0.0015, y - 0.0015, y + 0.0015, -bz / 2, bz / 2, wire, 0))
    a = math.radians(15)
    along = lambda d: (bx / 2 + d * math.cos(a), 0, bz / 2 + d * math.sin(a))
    rot = (0, math.pi / 2 - a, 0)
    p.append(C("hd", 0.006, 0.1, along(0.05), wire, 8, 0, rot=rot))
    p.append(C("gr", 0.012, 0.09, along(0.145), grip, 12, 0.003, rot=rot))
    o = S.join(p, "basket")
    S.set_origin(o, (0, 0, 0))
    o.location = loc
    return o


def fryer():
    """튀김기 2대. 원점 = 두 대 가운데 바닥. 바구니는 기름에 담긴 상태(타이머가 돌고 있다).
    기름 면 0.93 이 작업대 윗면 0.92 보다 위라 작업대 상판이 통 안으로 비치지 않는다."""
    ph.load("Store", "StoreKitchen")
    M = bpy.data.materials
    ss, ssd, blk, oil, wire = (M["M_tmp_K" + n] for n in ("Steel", "SteelGreasy", "Black", "Oil", "Wire"))
    FX0, FX1 = -0.32, 0.345
    line, labels = [], []
    for i, yc in enumerate((0.34, -0.34)):
        y0, y1 = yc - 0.31, yc + 0.31
        line.append(B("f_cab", FX0, FX1 - 0.01, y0, y1, 0.12, 0.66, ssd, 0.004))
        for a in ((FX1 - 0.09, FX1 - 0.01, y0, y1), (FX0, FX0 + 0.13, y0, y1), (FX0 + 0.13, FX1 - 0.09, y0, y0 + 0.07),
                  (FX0 + 0.13, FX1 - 0.09, y1 - 0.07, y1)):     # 기름통 벽
            line.append(B("f_wall", *a, 0.66, 0.92, ssd, 0.002, 1))
        line.append(B("f_door", FX1 - 0.01, FX1, y0 + 0.03, y1 - 0.03, 0.15, 0.66, ss, 0.004, 2))
        line.append(B("f_hdl", FX1, FX1 + 0.022, yc - 0.2, yc + 0.2, 0.605, 0.625, ss, 0.006, 2))
        line.append(B("f_ctl", FX1 - 0.01, FX1 + 0.004, y0 + 0.02, y1 - 0.02, 0.69, 0.9, ss, 0.004, 2))
        line.append(B("f_disp", FX1 + 0.004, FX1 + 0.012, yc - 0.075, yc + 0.075, 0.765, 0.835, blk, 0.003, 1))
        for k in range(4):
            by = yc - 0.16 + k * 0.107
            line.append(B("f_btn", FX1 + 0.004, FX1 + 0.012, by - 0.02, by + 0.02, 0.72, 0.745, blk, 0.003, 2))
        for sx in (FX0 + 0.06, FX1 - 0.07):
            for sy in (y0 + 0.06, y1 - 0.06):
                line.append(C("f_leg", 0.022, 0.11, (sx, sy, 0.065), ss, 12, 0.003))
                line.append(C("f_foot", 0.03, 0.012, (sx, sy, 0.006), blk, 12, 0.003))
        line.append(B("f_top", FX1 - 0.09, FX1 + 0.01, y0, y1, 0.92, 0.96, ss, 0.004, 2))
        line.append(B("f_top", FX0, FX0 + 0.13, y0, y1, 0.92, 0.96, ssd, 0.004, 2))
        line.append(B("f_top", FX0 + 0.13, FX1 - 0.09, y0, y0 + 0.07, 0.92, 0.96, ss, 0.004, 2))
        line.append(B("f_top", FX0 + 0.13, FX1 - 0.09, y1 - 0.07, y1, 0.92, 0.96, ss, 0.004, 2))
        line.append(B("f_oil", FX0 + 0.13, FX1 - 0.09, y0 + 0.07, y1 - 0.07, 0.68, 0.93, oil, 0))
        line.append(B("f_flue", FX0, FX0 + 0.13, y0 + 0.02, y1 - 0.02, 0.96, 1.05, ssd, 0.006, 2))
        line.append(B("f_flueg", FX0 + 0.04, FX0 + 0.11, y0 + 0.08, y1 - 0.08, 1.05, 1.053, blk, 0.001, 1))
        line.append(C("f_hang", 0.006, 0.58, (FX0 + 0.145, yc, 1.02), ss, 10, 0, rot=(math.pi / 2, 0, 0)))
        for s in (-0.11, 0.11):
            line.append(basket(wire, blk, (0.0135, yc + s, 0.915)))
        lab(labels, "timer%d" % i, 0.1, 0.044, (FX1 + 0.0125, yc, 0.8), True)
        lab(labels, "hot", 0.16, 0.089, (FX1 + 0.0005, yc, 0.42))
    line.append(B("f_fill", FX0 + 0.02, FX1 - 0.02, -0.03, 0.03, 0.92, 0.965, ss, 0.002, 1))     # 두 대 사이 덮개
    line.append(B("f_gap", FX1 - 0.03, FX1 - 0.012, -0.03, 0.03, 0.12, 0.92, ssd, 0.002, 1))     # 앞쪽 틈 막이
    done("PH_Fryer", bake_with(line, labels, "PH_Fryer", 1024), -90)


def bench():
    """조리 라인 작업대 5.3m. 프로토타입 자리(x -5.995..-5.245, y -1.45..3.85) 그대로, 앞선만 4.5cm 뒤로.
    y 2.2..3.5 는 튀김기 자리라 아래 상자를 두지 않는다. 그리들은 프로토타입처럼 상판 위 y 1.4."""
    ph.load("Store", "StoreKitchen")
    M = bpy.data.materials
    ss, ssd, plate, blk, board, card = (M["M_tmp_K" + n] for n in ("Steel", "SteelGreasy", "Griddle", "Black", "Board", "Cardboard"))
    food = [M["M_tmp_K" + n] for n in ("Lettuce", "Tomato", "Onion", "Pickle")]
    X0, X1, Y0, Y1 = -5.995, -5.29, -1.45, 3.85
    line, labels = [], []
    line.append(B("t_top", X0, X1, Y0, Y1, 0.88, 0.92, ss, 0.006, 3))
    line.append(B("t_apron", X0 + 0.03, X1 - 0.02, Y0 + 0.02, Y1 - 0.02, 0.83, 0.88, ss, 0.003, 2))
    line.append(B("t_splash", X0, X0 + 0.02, Y0, Y1, 0.92, 1.0, ss, 0.003, 2))
    line.append(B("t_shelf", X0 + 0.04, X1 - 0.04, Y0 + 0.04, Y1 - 0.04, 0.24, 0.26, ss, 0.003, 2))
    for k in range(5):
        sy = Y0 + 0.05 + k * (Y1 - Y0 - 0.1) / 4
        for sx in (X0 + 0.06, X1 - 0.05):
            line.append(C("t_leg", 0.019, 0.8, (sx, sy, 0.43), ss, 12, 0.003))
            line.append(C("t_foot", 0.024, 0.03, (sx, sy, 0.015), ss, 12, 0.004, r2=0.016))
    # 재료 받침 (1/6 팬 4개, 재료가 팬 위로 살짝 올라온다) + 도마
    RY = -0.4
    line.append(B("t_rail", X0 + 0.05, X0 + 0.25, RY, RY + 0.9, 0.92, 1.0, ss, 0.003, 2))
    for k in range(4):
        py = RY + 0.05 + k * 0.215
        line.append(B("t_pan", X0 + 0.07, X0 + 0.23, py, py + 0.19, 0.96, 1.004, ss, 0.002, 1))
        line.append(B("t_fill", X0 + 0.075, X0 + 0.225, py + 0.005, py + 0.185, 0.96, 1.01, food[k], 0.004, 2))
    line.append(B("t_board", -5.72, -5.34, -0.35, 0.15, 0.92, 0.94, board, 0.004, 2))
    # 그리들 (높이 1.012 까지)
    GY0, GY1 = 0.95, 1.85
    line.append(B("g_body", -5.93, -5.31, GY0, GY1, 0.92, 0.965, ssd, 0.004, 2))
    line.append(B("g_plate", -5.93, -5.37, GY0, GY1, 0.965, 0.985, plate, 0.003, 2))
    line.append(B("g_trough", -5.37, -5.32, GY0 + 0.02, GY1 - 0.02, 0.95, 0.98, ss, 0.004, 2))
    line.append(B("g_back", -5.95, -5.92, GY0, GY1, 0.965, 1.012, ssd, 0.003, 2))
    for y in (GY0, GY1 - 0.02):
        line.append(B("g_side", -5.92, -5.5, y, y + 0.02, 0.985, 1.005, ssd, 0.003, 2))
    for k in range(3):
        line.append(C("g_knob", 0.016, 0.025, (-5.2975, GY0 + 0.2 + k * 0.25, 0.9425), blk, 16, 0.004, rot=(0, math.pi / 2, 0)))
    line.append(B("g_scraper", -5.7, -5.5, 1.35, 1.45, 0.985, 0.995, ss, 0.002, 1))
    line.append(B("g_scr_h", -5.5, -5.38, 1.385, 1.415, 0.985, 1.01, blk, 0.006, 2))
    # 선반 아래 상자
    for k, (y0, w, h) in enumerate(((-1.33, 0.5, 0.3), (-0.72, 0.5, 0.25), (-0.1, 0.55, 0.32), (0.55, 0.45, 0.3),
                                    (1.1, 0.5, 0.25), (1.7, 0.4, 0.28))):
        line.append(B("t_box", -5.95, -5.45, y0, y0 + w, 0.26, 0.26 + h, card, 0.008, 2))
        lab(labels, "box%d" % (k % 4), 0.2, 0.137, (-5.4495, y0 + w / 2, 0.26 + h / 2))
    done("PH_KitchenBench", bake_with(line, labels, "PH_KitchenBench", 2048, (-5.62, 1.2, 0)), -90)


ROWS = dict(PH_Seat=seat, PH_Booth=booth, PH_Hood=hood, PH_Fryer=fryer, PH_KitchenBench=bench)
for n in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ROWS):
    ROWS[n]()

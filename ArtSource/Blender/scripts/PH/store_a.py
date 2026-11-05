"""store_a: PH_Counter, PH_Bulkhead, PH_PickupBoard, PH_PickupStand, PH_Bag, PH_Bag__Cup, PH_NPC__Bag.
원본 .blend 에서 다시 만든다. 실행: blender -b --factory-startup --python store_a.py [-- counter bag cup npc_bag ...]
친구 프레임에서 카운터 앞은 +X, 길이는 Z 라 turn(-90) 뒤 Unity = (-y, z, x) 이다."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Store")]
import ph, bpy, bmesh
import storelib as S
from mathutils import Matrix, Vector
k3d = ph.k3d
T = Matrix.Translation
FRONT_X = ((270, 8), (235, 20), (90, 15))  # 앞 +X 행: Unity +X 쪽 = Blender -X 쪽에서 본다
FRONT_Z = ((180, 12), (215, 18), (0, 12))  # 앞 -Z 행


def islands(me):
    """떨어진 덩어리별 정점 번호."""
    bm = bmesh.new()
    bm.from_mesh(me)
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        seen.add(v.index)
        todo, isl = [v], []
        while todo:
            c = todo.pop()
            isl.append(c.index)
            for e in c.link_edges:
                w = e.other_vert(c)
                if w.index not in seen:
                    seen.add(w.index)
                    todo.append(w)
        out.append(isl)
    bm.free()
    return out


def bbox(me, ix):
    vs = [me.vertices[i].co for i in ix]
    return (Vector([min(v[k] for v in vs) for k in range(3)]),
            Vector([max(v[k] for v in vs) for k in range(3)]))


def only(o, keep):
    """keep(min, max) 가 참인 덩어리만 남긴다."""
    me = o.data
    drop = [i for ix in islands(me) if not keep(*bbox(me, ix)) for i in ix]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in drop], context='VERTS')
    bm.to_mesh(me)
    bm.free()


def flat(o):
    """오브젝트 행렬을 정점에 넣는다 (StoreCounter_Labels 는 X 축으로 90도 돌아가 있다)."""
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)


def done(name, o, notes, views, **kw):
    keep = set(k3d.tree_of([o]))
    for x in list(bpy.data.objects):
        if x not in keep:
            bpy.data.objects.remove(x, do_unlink=True)
    ph.finish(name, o, notes=notes)
    k3d.preview(name, [o], views=views, tag='ph', **kw)


def counter():
    TOP, SPLIT = 1.055, .5   # 슬랫 중간(z 0.115~0.61)에는 정점이 없어서 위쪽만 내려도 왜곡이 없다
    ph.load("Store", "StoreCounter")
    body, lab = bpy.data.objects["StoreCounter_Body"], bpy.data.objects["StoreCounter_Labels"]
    flat(lab)
    only(lab, lambda mn, mx: mx.y < -.36)   # 정면 사인만. POS·갠트리·스탠드 글자는 몸체와 같이 버린다
    lab.data.materials.pop(index=1)         # M_StoreCounter_Screens
    me = body.data
    for ix in islands(me):
        mn, mx = bbox(me, ix)
        if abs(mn.y + .345) < 1e-3:
            panel = ix
        if mn.z > 1.04:   # 상판 위로 나온 픽업 턱·받침판·그로밋을 내려 PH_PickupStand(y 0.99)가 뜨지 않게 한다
            top = 1.056 if mx.x > 0 else 1.0545 if mx.z < 1.06 else TOP   # 그로밋 +1mm, 받침판 -0.5mm(겹침 방지), 턱 상판과 같게
            for i in ix:
                me.vertices[i].co.z -= mx.z - top
    # 뒤 선반을 버려 비는 뒷면·양 끝을 정면 뒤판과 같은 재질로 막는다
    base = T((0, .3325, -.1))
    tall = Matrix.Diagonal((1, 1, .915 / .76, 1))
    short = Matrix.Diagonal((.625 / 5.9, 1, .915 / .76, 1))
    seal = (T((0, .3175, .1)) @ tall @ base,
            T((2.9375, -.0075, .1)) @ Matrix.Rotation(-math.pi / 2, 4, 'Z') @ short @ base,
            T((-2.9375, -.0075, .1)) @ Matrix.Rotation(math.pi / 2, 4, 'Z') @ short @ base)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    vs = [bm.verts[i] for i in panel]
    geom = vs + list({e for v in vs for e in v.link_edges}) + list({f for v in vs for f in v.link_faces})
    for m in seal:
        new = bmesh.ops.duplicate(bm, geom=geom)["geom"]
        bmesh.ops.transform(bm, matrix=m, verts=[g for g in new if isinstance(g, bmesh.types.BMVert)])
    bm.to_mesh(me)
    bm.free()
    for m in (me, lab.data):   # 높이 1.055 -> 0.99, 깊이 0.80 -> 0.76, 길이 5.95 -> 5.94
        for v in m.vertices:
            c = v.co
            if c.z > SPLIT:
                c.z -= TOP - .99
            c.x *= 5.94 / 5.95
            c.y *= .95
    o = ph.part("PH_Counter", [body, lab], ph.move_unity(-.38, 0, 0) @ ph.turn(-90))
    done("PH_Counter", o, {"desc": "주문 카운터. 원점 = 상판 앞 모서리 평면(x 0)의 바닥 중앙, 앞 +X. 슬랫 면은 x -0.03 에 있다. "
                                   "z -2.1 쪽 스테인리스 구간이 픽업 자리(PH_PickupStand 를 y 0.99 에 올린다)."}, FRONT_X, lens=35)


def bulkhead():
    ph.load("Store", "StoreShell")
    rail = bpy.data.objects["StoreShell_Fixtures"]
    only(rail, lambda mn, mx: abs(mn.x + 2.875) < 1e-3 and abs(mn.z - 2.175) < 1e-3)   # 소핏 아래 빨간 몰딩
    # 매장 좌표 -> 에셋 규칙(길이 X, 손님 쪽 -Y, 아랫면 z 0). 몰딩 폭 0.27 은 허용치를 넘어 프로토타입 값 0.26 으로
    rail.matrix_world = Matrix.Diagonal((1, .26 / .27, 1, 1)) @ ph.turn(-90) @ T((2.74, -1.25, -2.175))
    wall = S.boxz("bh_wall", -2.95, 2.95, -.12, .12, .02, .9, bpy.data.materials["M_Tile_Store_Paint"], .003, 2)
    k3d.apply_all(wall)
    k3d.uv_world(wall, 2.0)   # store_shell.py TILE_M 과 같은 값
    o = ph.part("PH_Bulkhead", [wall, rail], ph.turn(-90))
    done("PH_Bulkhead", o, {"desc": "카운터 위 소핏. 원점 = 아랫면 중앙(씬 y 2.2), 벽은 M_Tile_Store_Paint, 아래 몰딩은 StoreShell_Fixtures 그대로."},
         FRONT_X, lens=35)


def board():
    ph.load("Store", "StoreOrderBoard")
    body = bpy.data.objects["StoreOrderBoard_Body"]
    for v in body.data.vertices:
        x, y, z = v.co
        # 깊이 0.09 -> 0.08. 앞은 5mm 밀어 앞면을 x +0.04 에, 뒤(벽걸이 쪽)는 눌러 x -0.04 에 맞춘다
        y = y + .005 if y < -.008 else -.003 + (y + .008) * .043 / .053
        v.co = (x * 1.31 / 1.29, y, (z - .30) * .62 / .60)   # 원점 = 판 중심, 외곽 1.31x0.62
    m = S.pbr("M_tmp_PBScreen", (.012, .013, .015), .42, var=.12, vscale=3, grime=0, smudge=.25, bump=.01, bscale=300, rvar=.1)
    # 꺼진 LCD. 앞면보다 4.5mm 뒤라 앞면 앞에 놓이는 Blurred/Sharp 와 겹치지 않고, 구멍(1.27x0.58)이 Canvas(1.25x0.56)보다 커서 베젤에 걸리지 않는다
    scr = S.quad("PH_PickupBoard_Screen", 1.27, .58, (0, -.0355, 0), m)
    k3d.bake(scr, 512, samples=32, ao=False)
    o = ph.part("PH_PickupBoard", [body, scr], ph.turn(-90))
    done("PH_PickupBoard", o, {"desc": "주문 번호판. 원점 = 판 중심, 앞 +X, 앞면 x +0.04, 빈 화면 x +0.0355 (1.27x0.58). 글자는 Blurred/Sharp Canvas 몫이다."},
         FRONT_X)


def sweep(name, prof, x0, x1, mat):
    """(y, z) 단면을 X 로 밀어낸 판금."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    a = [bm.verts.new((x0, y, z)) for y, z in prof]
    b = [bm.verts.new((x1, y, z)) for y, z in prof]
    for i in range(len(prof)):
        j = (i + 1) % len(prof)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(a)
    bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return S.bevel(S.obj_from_bm(name, bm, mat=mat), .0012, 2)


def arc(cy, cz, r, a0, a1, n=5):
    return [(cy + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def stand():
    W, D, H, R, TH = .35, .25, .098, .007, .003   # 반길이, 반깊이, 철판 윗면, 접힘 반지름, 판 두께. 매트 2mm 까지 높이 0.1
    ph.load("Store", "StoreCounter")
    sign = bpy.data.materials["M_StoreCounter_Signs"]
    for x in list(bpy.data.objects):   # AO 굽기에 원본 카운터가 끼지 않게
        bpy.data.objects.remove(x, do_unlink=True)
    steel = S.pbr("M_tmp_PSSteel", (.62, .62, .6), .3, 1.0, var=.05, grime=.5, brush=.18, smudge=.3, scratch=.4, bump=.02)  # 카운터 픽업 받침과 같은 값
    frame = S.pbr("M_tmp_PSFrame", (.5, .5, .49), .4, 1.0, var=.06, grime=.6, gdist=.02, scratch=.3, bump=.02)
    rubber = S.pbr("M_tmp_PSRubber", (.02, .02, .021), .75, var=.1, grime=.3, smudge=.25, bump=.25, bscale=320,
                   edge=.4, edge_col=(.07, .07, .07))
    outer = [(-D, .05)] + arc(-D + R, H - R, R, 180, 90) + arc(D - R, H - R, R, 90, 0) + [(D, .008)]
    inner = [(D - TH, .008)] + arc(D - R, H - R, R - TH, 0, 90) + arc(-D + R, H - R, R - TH, 90, 180) + [(-D + TH, .05)]
    p = [sweep("ps_sheet", outer + inner, -W, W, steel)]
    p += [S.boxz("ps_cheek", x, x + .012, -D + .012, D - TH, .008, H - TH, frame, .002, 2) for x in (-W + .002, W - .014)]
    p += [S.cyl("ps_foot", .012, .008, (x, y, .004), rubber, 20, .001) for x in (-.31, .31) for y in (-.21, .21)]
    p += [S.cyl("ps_screw", .0055, .0012, (x, y, H + .0006), frame, 14, .0004) for x in (-.325, .325) for y in (-.225, .225)]
    p.append(S.boxz("ps_mat", -.3, .3, -.19, .21, H - .0002, H + .0012, rubber, .0004, 1))
    p += [S.boxz("ps_rib", -.292, .292, -.182 + i * .026, -.170 + i * .026, H + .001, H + .002, rubber, 0) for i in range(15)]
    o = S.join(p, "PH_PickupStand_Steel")
    S.set_origin(o, (0, 0, 0))
    k3d.bake(o, 1024, samples=48, ao_distance=.05)
    lab = S.quad("ps_sign", .1125, .036, (0, -D - .0006, .074), sign, uv=S.atlas_uv("counter_signs.png", "pickup"))
    o = ph.part("PH_PickupStand", [o, lab], ph.turn(-90))
    done("PH_PickupStand", o, {"desc": "음식 받는 곳 받침. 원점 = 바닥 중앙, 윗면 y 0.1 (봉투가 놓이는 고무 매트), 손님 쪽 +X 에 픽업 표시."},
         ((270, 25), (235, 30), (60, 20)))


def takeout():
    """몸통을 회색 0.25 x 0.14 에 맞춘 봉투. 높이 배율이 폭 배율 0.96 에 가까워 앞면 인쇄가 거의 눌리지 않는다.
    손잡이 끝이 회색 윗면 + 0.03 안에 들도록 몸통 위 손잡이는 줄이지 않고 안쪽으로 눕힌다 (둘이 가운데서 닿는다)."""
    TOP, LEAN, H = .3, math.radians(48), .92   # 원본 몸통 높이, 눕힘 각(더 눕히면 두 손잡이가 파고든다), 높이 배율
    ph.load("Food", "FoodTakeoutBag")
    b = bpy.data.objects["FoodTakeoutBag_Mesh"]
    for v in b.data.vertices:
        x, y, z = v.co
        d = max(z - TOP, 0)
        v.co = (x * .25 / .2602, (y - math.copysign(d * math.sin(LEAN), y)) * .14 / .1532, (z - d + d * math.cos(LEAN)) * H)
    return b


def bag():
    o = ph.part("PH_Bag", [takeout()], ph.turn(180))
    done("PH_Bag", o, {"desc": "주문 봉투만. 컵은 PH_Bag__Cup. 원점 = 바닥 중앙, 몸통 0.25x0.276x0.14, 손잡이는 안쪽으로 눕혀 y 0.33 까지. 양면 같은 인쇄, 앞면 -Z."}, FRONT_Z)


def cup():
    ph.load("Food", "FoodDrinkCup_Cider")
    # 원본 크기 그대로다. 몸통이 이미 0.15 이고, 씬의 Label(TMP, Cup 로컬 (0, 0.085, -0.043))은 그 높이 벽(반지름 0.04) 3mm 앞에 뜬다
    o = ph.part("PH_Bag__Cup", [bpy.data.objects["FoodDrinkCup_Cider_Mesh"]], ph.move_unity(0, -.075, 0) @ ph.turn(180))
    done("PH_Bag__Cup", o, {"desc": "사이다 컵. Cup/Visual 로컬: 원점 = 몸통 가운데, 바닥 y -0.075, 몸통 0.15. 뚜껑과 빨대는 그 위로 나온다. 로고 면 -Z."}, FRONT_Z)


def npc_bag():
    b = takeout()
    o = ph.part("PH_NPC__Bag", [b], ph.move_unity(0, -max(v.co.z for v in b.data.vertices) / 2, 0) @ ph.turn(180))
    done("PH_NPC__Bag", o, {"desc": "PH_Bag 과 같은 봉투, 원점 = 범위 중심 (BagAnchor/Visual)."}, FRONT_Z)


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for f in (counter, bulkhead, board, stand, bag, cup, npc_bag):
    if not args or f.__name__ in args:
        f()

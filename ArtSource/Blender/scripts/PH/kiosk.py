"""PH_Kiosk__Body/Cover/WingL/WingR/Card, PH_Kiosk_Broken. 소스: Kiosk/Kiosk, Kiosk/Kiosk_B, Items/BankCard.
turn(180) 뒤 Unity (x, y, z) = 소스 (x, z, y). 그래서 아래 상수는 소스 좌표이고 y 값이 곧 Unity z 다.
친구가 그리는 면: ScreenQuad z -0.0565, Plate 글자 z -0.0592, Notice 글자 z -0.0605. 우리 면은 모두 그 뒤에 둔다.
영수증 종이는 KioskReceipt.cs 가 런타임에 만든다."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Store")]
import ph, bpy, bmesh, k3d
import numpy as np
import storelib as S
from mathutils import Matrix, Vector

SCR_Z, SCR_W, SCR_H = 1.385, 0.42, 0.747            # 화면 중심 높이, 크기
SCREEN_Y = -0.0565                                 # ScreenQuad, 회색 ScreenOff
BACK_Y = SCREEN_Y + 0.0008                         # 화면 뒤 판
FRONT_Y, SEAT_Y, EDGE_Y = -0.0583, -0.0588, -0.0566  # 조작부 테두리 앞면(Plate 뒤), 부품 뒷면, 테두리 뒷면
MOD_K = (0.067 + FRONT_Y) / (0.067 + SEAT_Y)       # 슬롯 모듈 앞면은 소스 -0.067 그대로. 틈이 Receipt 원점 z -0.0662 보다 앞에 온다
TERM_K = (0.132 + FRONT_Y) / (0.1642 + SEAT_Y)     # 단말기 앞끝 -0.1642 -> -0.132 (표의 깊이 0.202 안)
# 받침판 앞뒤 구간 (소스 y -> 새 y). 앞 모서리와 플랜지 주변은 그대로 옮기고 사이만 줄여 구운 흔적이 제자리에 남는다
PLATE_Y = (-0.23, -0.18, -0.045, 0.075, 0.23), (-0.13, -0.08, -0.057, 0.063, 0.068)
POST_DY, FOOT_FRONT_DY, FOOT_BACK_DY = -0.012, 0.10, -0.157
HINGE_SRC = (0.30, -0.0688, 0.838)                 # 소스 덮개 경첩선
HINGE = (0.326, -0.0695, 0.838)                    # 프리팹 Cover/Hinge
COVER_Y, COVER_K, COVER_TAPE = HINGE[1] - 0.006, 0.6, 0.03  # 회색 Poster z, 말림 비율 (앞끝 로컬 -0.0275), 앞면 테이프 폭
# 경첩 테이프: 레일 옆면에서 나와 프리팹 경첩선에서 끝난다 (소스 x -> 새 x, y)
HINGE_TAPE = {0.284: (0.3262, -0.0697), 0.298: (0.3195, -0.0605), 0.303: (0.3135, -0.0475), 0.313: (0.3126, -0.030)}
# 소스 kiosk.py POSTERS: 행, 쪽, 중심 z, 폭, 높이, 각도. 프리팹 Wing_L = 불고기 페스타, Wing_R = 크라운 트리플
WINGS = (("PH_Kiosk__WingL", -1, 1.3, 0.25, 0.56, 0.42), ("PH_Kiosk__WingR", 1, 1.54, 0.2, 0.3, 0.5))
WING_CURL = 0.6                                    # 종이 말림 비율. 범위 중심이 Wing 원점에 맞도록 줄인다
NOTICE_C, NOTICE_R = Vector((0, -0.0662, 1.32)), Matrix.Rotation(-0.04, 3, 'Y')  # 소스 안내문. 회전은 NoticePaper 와 같다
NOTICE_W, NOTICE_H, NOTICE_Y, NOTICE_FOLD, NOTICE_TAPE_Y = 0.34, 0.24, -0.0577, 0.4, -0.0601  # 뒷면 z, 접힘 깊이 비율 (앞면 -0.0594, 평균 -0.0585)
BLANK_UV = (50 / 2048, 493 / 2048, 105 / 2048, 548 / 2048)  # 아틀라스 안내문 칸의 빈 여백
VIEWS = ((180, 6), (208, 10), (25, 10))            # Unity -Z 쪽 정면, 3/4, 뒤


def world(o):
    """변환을 정점에 굽는다. 이후 정점은 소스 월드 좌표 (Kiosk_Labels 는 회전이 남아 있다)."""
    mw = o.matrix_world.copy()
    o.parent = None
    o.data.transform(mw)
    o.matrix_world = Matrix.Identity(4)


def islands(bm):
    """연결 요소별 (정점, 최소, 최대). 합쳐서 구운 메시에서 부품을 고르는 단위다."""
    seen, out = set(), []
    for s in bm.verts:
        if s in seen:
            continue
        seen.add(s)
        stack, c = [s], []
        while stack:
            v = stack.pop()
            c.append(v)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        p = np.array([v.co[:] for v in c])
        out.append((c, p.min(0), p.max(0)))
    return out


def edit(o, fn, *args):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    fn(bm, *args)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()


def squash(vs, y_from, y_to, k):
    """y_from 을 y_to 로 옮기고 그 면을 기준으로 깊이를 k 배 한다 (정점만 움직여 구운 UV 유지)."""
    for v in vs:
        v.co.y = y_to + (v.co.y - y_from) * k


def find(bm, test):
    return next(vs for vs, mn, mx in islands(bm) if test(mn, mx))


def slice_part(bm, test, planes):
    """test 로 고른 부품을 평면들로 자른다."""
    for co, no in planes:
        vs = find(bm, test)
        fs = {f for v in vs for f in v.link_faces}
        es = {e for f in fs for e in f.edges}
        bmesh.ops.bisect_plane(bm, geom=vs + list(es) + list(fs), dist=1e-6, plane_co=co, plane_no=no)


def edit_body(bm):
    for vs, mn, mx in islands(bm):
        x = max(-mn[0], mx[0])
        if mn[1] > 0.05 and mx[1] > 0.3:  # ponytail: 바닥 케이블은 깊이 0.20 밖이라 뺀다. 뒷면이 보이는 배치면 기둥을 따라 내리는 케이블을 새로 만들 것
            bmesh.ops.delete(bm, geom=vs, context='VERTS')
        elif mn[2] > 1.0 and x > 0.318:  # 날개 받침판, 클램프, 나사. ponytail: 무료 리필은 끝이 x 0.485 라 표의 x 상한 0.35 를 넘어 같이 뺐다. 표를 올리면 덩어리를 남기고 z -0.133 안으로 줄일 것
            bmesh.ops.delete(bm, geom=vs, context='VERTS')
        elif mx[2] < 0.047 and 0.25 < x < 0.32:             # 수평 조절 발
            squash(vs, 0, FOOT_FRONT_DY if mn[1] < 0 else FOOT_BACK_DY, 1)
        elif mx[2] < 0.35 and x < 0.19:                     # 기둥, 플랜지, 볼트
            squash(vs, 0, POST_DY, 1)
        elif abs(x - 0.277) < 2e-4:                         # 조작부 테두리: 앞면을 Plate 뒤로
            squash(vs, EDGE_Y, EDGE_Y, (EDGE_Y - FRONT_Y) / (EDGE_Y + 0.059))
        elif 0.27 < x < 0.28 and mx[1] < -0.058:            # 테두리 나사
            squash(vs, 0, FRONT_Y + 0.059, 1)

    # 받침판
    plate = lambda mn, mx: mx[0] > 0.32 and mx[2] < 0.033
    slice_part(bm, plate, [((0, y, 0), (0, 1, 0)) for y in PLATE_Y[0][1:4]])
    for v in find(bm, plate):
        v.co.y = float(np.interp(v.co.y, *PLATE_Y))

    # 전면판에 화면 구멍 (앞면 -0.057 이 ScreenQuad -0.0565 보다 앞이다). 가장자리는 베젤 밑에 숨는다
    panel = lambda mn, mx: abs(mx[0] - 0.294) < 1e-3 and mx[1] < -0.054
    hw, hh = 0.2275, 0.395
    slice_part(bm, panel, [((hw, 0, 0), (1, 0, 0)), ((-hw, 0, 0), (1, 0, 0)),
                           ((0, 0, SCR_Z + hh), (0, 0, 1)), ((0, 0, SCR_Z - hh), (0, 0, 1))])
    fs = {f for v in find(bm, panel) for f in v.link_faces}
    hole = [f for f in fs if (c := f.calc_center_median()).y < -0.0569 and abs(c.x) < hw and abs(c.z - SCR_Z) < hh]
    bmesh.ops.delete(bm, geom=hole, context='FACES')


def edit_controls(bm):
    for vs, mn, mx in islands(bm):
        term = mn[0] > 0.1 and mx[0] < 0.22 and mn[2] > 0.45 and mx[2] < 0.66
        squash(vs, SEAT_Y, FRONT_Y, TERM_K if term else MOD_K)


def edit_labels(bm):
    """스티커, 간판, 흔들이 줄, 점검 안내문만 남긴다. 경첩 테이프는 프리팹 경첩선까지 잇는다."""
    for vs, mn, mx in islands(bm):
        sticker, header = abs(mn[0] + 0.1) < 1e-3 and mx[2] < 1.01, mn[2] > 1.8
        stalk, notice = mx[0] < 0 and mn[2] > 1.65, max(-mn[0], mx[0]) < 0.25 and mn[2] > 1.1
        if abs(mn[0] - 0.284) < 1e-3:
            for v in vs:
                v.co.x, v.co.y = HINGE_TAPE[round(v.co.x, 3)]
        elif not (sticker or header or stalk or notice):
            bmesh.ops.delete(bm, geom=vs, context='VERTS')


def fit_notice(bm):
    """소스 안내문을 빈 종이로 편다. 글자는 프리팹 Notice 가 그리고, 테이프는 새 귀퉁이로 옮긴다."""
    uv = bm.loops.layers.uv.active
    for vs, mn, mx in islands(bm):
        if max(-mn[0], mx[0]) > 0.25 or mn[2] < 1.1:        # 스티커, 간판
            continue
        if mx[0] - mn[0] > 0.2:
            for v in vs:
                p = NOTICE_R.inverted() @ (v.co - NOTICE_C)
                s, t = p.x / 0.297 + 0.5, p.z / 0.21 + 0.5
                q = NOTICE_R @ Vector(((s - 0.5) * NOTICE_W, 0, (t - 0.5) * NOTICE_H))
                v.co = q.x, NOTICE_Y + (p.y + 0.0003) * NOTICE_FOLD, NOTICE_C.z + q.z
                for l in v.link_loops:
                    l[uv].uv = BLANK_UV[0] + (BLANK_UV[2] - BLANK_UV[0]) * s, BLANK_UV[1] + (BLANK_UV[3] - BLANK_UV[1]) * t
        else:
            side = 1 if mn[0] > 0 else -1
            c = NOTICE_R @ Vector((side * (NOTICE_W / 2 - 0.012), 0, NOTICE_H / 2 - 0.006))
            dx, dz = c.x - (mn[0] + mx[0]) / 2, NOTICE_C.z + c.z - (mn[2] + mx[2]) / 2
            for v in vs:
                v.co = v.co.x + dx, NOTICE_TAPE_Y, v.co.z + dz


def fit_cover(bm):
    """경첩 쪽 마지막 칸만 늘려 0.205 -> 0.231 (글자는 늘어나지 않는다). 말림은 로컬 z -0.03 안으로 줄인다."""
    for v in bm.verts:
        if v.co.x > HINGE_SRC[0] - 1e-4:
            v.co.x = HINGE[0]
        v.co.y = COVER_Y + (v.co.y - HINGE_SRC[1]) * COVER_K


def fit_wing(bm, lim):
    """레일 안으로 파고드는 클램프 끝을 자르고 말림을 줄인다. turn(180) 뒤라 앞이 +y 다."""
    for v in bm.verts:
        v.co.x = max(-lim, min(lim, v.co.x))
        if v.co.y > 0:
            v.co.y *= WING_CURL


def strip(name, pts, h, z, mat):
    """세로 테이프. pts = (x, y) 꺾은선."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    rows = [[bm.verts.new((x, y, z + s * h / 2)) for x, y in pts] for s in (-1, 1)]
    for i in range(len(pts) - 1):
        bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
    return S.obj_from_bm(name, bm, mat=mat)


def cut(o, test):
    """o 의 복사본에서 test 에 맞는 덩어리만 남긴다."""
    c = o.copy()
    c.data = o.data.copy()
    bpy.context.scene.collection.objects.link(c)
    edit(c, lambda bm: bmesh.ops.delete(bm, geom=[v for vs, mn, mx in islands(bm) if not test(mn, mx) for v in vs], context='VERTS'))
    return c


def shots(name, o, views=VIEWS, **kw):
    keep = set(k3d.tree_of([o]))
    for x in bpy.data.objects:
        x.hide_render = x not in keep
    k3d.preview(name, [o], views=views, res=(900, 1000), tag='ph', **kw)


def check_clear(o, limit):
    """정면에서 쏜 광선으로 화면 자리에 limit 보다 앞에 나온 것이 없는지 본다. Blender 는 turn(180) 뒤라 y = -Unity z."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    def depth(x, y):
        hit, p, *_ = o.ray_cast((-x, 1.0, y), (0, -1, 0), depsgraph=dg)
        assert hit, f"구멍 {x:.3f} {y:.3f}"
        return -p.y

    for i in range(41):
        for j in range(61):
            x, y = (i / 40 - .5) * SCR_W, SCR_Z + (j / 60 - .5) * SCR_H
            assert depth(x, y) > limit, f"화면 앞 {x:.3f} {y:.3f}"
    return depth


# ---------------------------------------------------------------- PH_Kiosk
ph.load("Kiosk", "Kiosk")
ob = bpy.data.objects
for o in ob:
    if o.type == 'MESH':
        world(o)
# 날개 포스터: Wing 로컬 프레임 (중심 원점, 앞 -Z). 받침판, 클램프, 나사는 Body 에, 종이와 테이프는 Labels 에 있다
for name, side, z, w, h, ang in WINGS:
    inv = (Matrix.Translation((side * 0.312, -0.03, z)) @ Matrix.Rotation(-side * ang, 4, 'Z') @ Matrix.Translation((side * (w / 2 + 0.008), 0, 0))).inverted()

    def mine(mn, mx):
        c = inv @ Vector((mn + mx) / 2)
        return abs(c.x) < w / 2 + 0.04 and abs(c.y) < 0.07 and mn[2] > z - h / 2 - 0.03 and mx[2] < z + h / 2 + 0.03

    wing = ph.part(name, [cut(ob["Kiosk_Body"], mine), cut(ob["Kiosk_Labels"], mine)], ph.turn(180) @ inv)
    edit(wing, fit_wing, w / 2 + 0.01)
    k3d.select([wing])
    bpy.ops.object.material_slot_remove_unused()     # Labels 의 간판 재질
    ph.finish(name, wing, notes=f"{'Wing_L' if side < 0 else 'Wing_R'}/Visual. 원점 = 포스터 중심, 앞 -Z. 회전은 프리팹 Wing 이 준다. 안쪽 클램프 끝은 Body 레일 안으로 들어간다.")
    shots(name, wing, views=((180, 6), (0, 6)))

edit(ob["Kiosk_Body"], edit_body)
edit(ob["Kiosk_Controls"], edit_controls)
edit(ob["Kiosk_Labels"], edit_labels)
backing = S.quad("PH_Kiosk_Backing", 0.462, 0.797, (0, BACK_Y, SCR_Z), k3d.mat("M_PH_Kiosk_Backing", (0.004, 0.004, 0.005), 0.35))
body = ph.part("PH_Kiosk__Body", [ob["Kiosk_Body"], ob["Kiosk_Controls"], ob["Kiosk_Labels"], ob["Kiosk_PopWobbler"], backing], ph.turn(180))
depth = check_clear(body, SCREEN_Y)
for p in ((-0.145, 0.82), (-0.145, 0.666), (0.142, 0.735), (-0.145, 0.44), (0, 0.5), (-0.26, 0.38), (0.26, 0.94)):
    assert depth(*p) > -0.0586, f"Plate 앞 {p}"   # Plate 글자 자리
ph.finish("PH_Kiosk__Body", body, notes="PH_Kiosk Visual. ScreenQuad, Plate 글자는 프리팹이 그리고 이 모델은 그 뒤에 있다. 슬롯 앞면 z -0.067. 날개 포스터는 Wing_L, Wing_R 이 따로 갖고 NEW 흔들이는 여기 있다.")
shots("PH_Kiosk__Body", body)

# 덮개: Cover 가 Z 로 180도 돌아 있어 Z 로 180도 돌려 넣어야 프리팹에서 바로 선다 (turn(180) 에 Blender Y 180도를 더한 것 = X 180도).
# 앞면 테이프는 종이 앞면에서 모서리를 돌아 경첩선에서 꺾이고 레일 쪽 테이프는 Body 에 있다
paper = ob["Kiosk_PayCover"]
edit(paper, fit_cover)
tape = strip("PH_Kiosk_CoverTape", [HINGE[:2], (HINGE[0], COVER_Y - 0.0006), (HINGE[0] - COVER_TAPE, COVER_Y - 0.0006)], 0.15, HINGE[2], bpy.data.materials["M_Glass_Kiosk_Tape"])
cover = ph.part("PH_Kiosk__Cover", [paper, tape], Matrix.Rotation(math.pi, 4, 'X') @ Matrix.Translation([-c for c in HINGE]))
ph.finish("PH_Kiosk__Cover", cover, notes="Cover/Hinge/Visual. 원점 = 경첩선. 로컬 x 0..0.231, y +-0.085, z -0.006 (말림 앞끝 -0.0275). 부모 Cover 의 Z 180도를 뺀 프레임이라 로컬에서는 인쇄가 뒤집혀 있다. PosterFlap 이 Hinge 를 Y +146.1도 돌려 앞으로 연다.")
shots("PH_Kiosk__Cover", cover, views=((180, 4), (150, 12), (0, 4)))

# ---------------------------------------------------------------- PH_Kiosk_Broken
ph.load("Kiosk", "Kiosk_B")
ob = bpy.data.objects
for o in ob:
    if o.type == 'MESH':
        world(o)
edit(ob["Kiosk_B_Body"], edit_body)
edit(ob["Kiosk_B_Controls"], edit_controls)
edit(ob["Kiosk_B_Labels"], edit_labels)
edit(ob["Kiosk_B_Labels"], fit_notice)
panel, lcd = ob["Kiosk_B_Panel"], ob["Kiosk_B_TerminalLcd"]
panel.data.materials[0].name = "M_PH_Kiosk_B_Panel"  # 같은 텍스처를 쓰는 일반 재질. 이 프리팹에는 Plate 가 없다
edit(panel, lambda bm: squash(bm.verts, 0, FRONT_Y + 0.059, 1))
edit(lcd, lambda bm: squash(bm.verts, SEAT_Y, FRONT_Y, TERM_K))
off = S.quad("PH_Kiosk_B_Screen", 0.462, 0.797, (0, SCREEN_Y, SCR_Z),
             S.pbr("kScreenOff", (0.0035, 0.0038, 0.0045), 0.16, 0.0, var=0.03, grime=0.0, bump=0, rvar=0.05, smudge=0.45, scratch=0.12, coat=1.0))
k3d.bake(off, 1024, samples=32, ao_distance=0.02)
broken = ph.part("PH_Kiosk_Broken", [ob["Kiosk_B_Body"], ob["Kiosk_B_Controls"], ob["Kiosk_B_Labels"], panel, lcd, off], ph.turn(180))
check_clear(broken, -0.0603)
ph.finish("PH_Kiosk_Broken", broken, notes="PH_Kiosk_Broken Visual. 꺼진 화면 z -0.0565. 빈 종이 0.34 x 0.24 는 (0, 1.32, -0.0585) 에 NoticePaper 만큼 돌아 있고 글자는 프리팹 Notice 가 z -0.0605 에 그린다.")
shots("PH_Kiosk_Broken", broken)

# ---------------------------------------------------------------- PH_Kiosk__Card
# Card/Visual 회전 (0.5, 0.5, 0.5, -0.5) 은 로컬 +Z 를 위, +X 를 틈 안쪽으로 보낸다. turn(0) 이면 칩 면이 위고 칩 쪽 끝이 먼저 들어간다
ph.load("Items", "BankCard")
card = ph.part("PH_Kiosk__Card", [bpy.data.objects["BankCard_Body"]], ph.turn(0) @ Matrix.Translation((0, 0, -0.02699)))
ph.finish("PH_Kiosk__Card", card, notes="Card/Visual. 원점 = 카드 중심, 칩 면 +Z, 칩 쪽 끝 +X.")
shots("PH_Kiosk__Card", card, views=((0, 0), (180, 0)), lens=80)
print("PH_KIOSK_DONE")

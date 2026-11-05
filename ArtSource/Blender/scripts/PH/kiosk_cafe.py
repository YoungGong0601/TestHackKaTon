"""PH_KioskCafe__Body/WingL/WingR. PH/kiosk.py 의 Body, WingL, WingR 과 메시, 치수가 같고 카드 전용 띠만 뺐다.
바뀌는 것은 재질 이름과 그림이다. 간판, 날개 포스터, NEW 흔들이는 숲길 커피로, Controls 의 빨강은 초록으로 (PH/kiosk_cafe_tex.py).
재질은 전부 새 이름이라 버거집 키오스크에 영향이 없다. Body 아틀라스는 빨강이 없어 Normal, MS 와 함께 공유 파일을 읽기만 한다.
turn(180) 뒤 Unity (x, y, z) = 소스 (x, z, y). 그래서 아래 상수는 소스 좌표이고 y 값이 곧 Unity z 다.
친구가 그리는 면: ScreenQuad z -0.0565, Plate 글자 z -0.0592. 우리 면은 모두 그 뒤에 둔다."""
import sys, os, subprocess
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
# 경첩 테이프: 레일 옆면에서 나와 프리팹 경첩선에서 끝난다 (소스 x -> 새 x, y)
HINGE_TAPE = {0.284: (0.3262, -0.0697), 0.298: (0.3195, -0.0605), 0.303: (0.3135, -0.0475), 0.313: (0.3126, -0.030)}
# 소스 kiosk.py POSTERS: 행, 쪽, 중심 z, 폭, 높이, 각도. 종이 아틀라스 칸은 Wing_L = festa, Wing_R = triple 그대로다
WINGS = (("PH_KioskCafe__WingL", -1, 1.3, 0.25, 0.56, 0.42), ("PH_KioskCafe__WingR", 1, 1.54, 0.2, 0.3, 0.5))
WING_CURL = 0.6                                    # 종이 말림 비율. 범위 중심이 Wing 원점에 맞도록 줄인다
VIEWS = ((180, 6), (208, 10), (25, 10))            # Unity -Z 쪽 정면, 3/4, 뒤
MATERIALS = {"M_Kiosk_Body": "M_PH_KioskCafe_Body", "M_Kiosk_Controls": "M_PH_KioskCafe_Controls", "M_Kiosk_Paper": "M_PH_KioskCafe_Paper",
             "M_Kiosk_Header": "M_PH_KioskCafe_Header", "M_Glass_Kiosk_Tape": "M_Glass_PH_KioskCafe_Tape"}
IMAGES = {"T_Kiosk_Header.png": "T_PH_KioskCafe_Header.png", "T_Kiosk_Paper_BaseColor.jpg": "T_PH_KioskCafe_Paper_BaseColor.jpg",
          "T_Kiosk_Controls_BaseColor.jpg": "T_PH_KioskCafe_Controls_BaseColor.jpg", "T_Kiosk_Controls_Emission.jpg": "T_PH_KioskCafe_Controls_Emission.jpg"}


def rebrand():
    """Unity 재질 이름은 전역이다. 불러온 재질을 메모리에서만 새 이름으로 바꾸고 그림만 새 파일로 갈아 끼운다.
    k3d.material_json 이 구운 재질의 맵을 이미지 이름 끝으로 고르므로 이름에 확장자를 넣지 않는다."""
    done = set()
    for old, new in MATERIALS.items():
        m = bpy.data.materials[old]
        m.name = new
        for n in m.node_tree.nodes:
            f = n.type == 'TEX_IMAGE' and n.image and bpy.path.basename(n.image.filepath)
            if f in IMAGES:
                im = k3d.load_image(os.path.join(k3d.ART, "Textures", "PH_KioskCafe", IMAGES[f]), os.path.splitext(IMAGES[f])[0])
                im.colorspace_settings.name = n.image.colorspace_settings.name
                n.image = im
                done.add(f)
    assert done == set(IMAGES), set(IMAGES) - done


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
    """간판, 흔들이 줄만 남긴다. R2_Cafe 가 Sticker_CardOnly 를 꺼서 구운 카드 전용 띠도 뺀다. 경첩 테이프는 프리팹 경첩선까지 잇는다."""
    for vs, mn, mx in islands(bm):
        header = mn[2] > 1.8
        stalk, notice = mx[0] < 0 and mn[2] > 1.65, max(-mn[0], mx[0]) < 0.25 and mn[2] > 1.1
        if abs(mn[0] - 0.284) < 1e-3:
            for v in vs:
                v.co.x, v.co.y = HINGE_TAPE[round(v.co.x, 3)]
        elif not (header or stalk or notice):
            bmesh.ops.delete(bm, geom=vs, context='VERTS')


def fit_wing(bm, lim):
    """레일 안으로 파고드는 클램프 끝을 자르고 말림을 줄인다. turn(180) 뒤라 앞이 +y 다."""
    for v in bm.verts:
        v.co.x = max(-lim, min(lim, v.co.x))
        if v.co.y > 0:
            v.co.y *= WING_CURL


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


# ---------------------------------------------------------------- PH_KioskCafe
subprocess.run([k3d.PY, os.path.join(HERE, "kiosk_cafe_tex.py"), k3d.REPO], check=True)
ph.load("Kiosk", "Kiosk")
rebrand()
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
edit(ob["Kiosk_PopWobbler"], lambda bm: bmesh.ops.reverse_faces(bm, faces=bm.faces))   # 원본은 면이 안쪽을 봐서 Unity 에서 크림색 뒤쪽 면이 보인다
backing = S.quad("PH_KioskCafe_Backing", 0.462, 0.797, (0, BACK_Y, SCR_Z), k3d.mat("M_PH_KioskCafe_Backing", (0.004, 0.004, 0.005), 0.35))
body = ph.part("PH_KioskCafe__Body", [ob["Kiosk_Body"], ob["Kiosk_Controls"], ob["Kiosk_Labels"], ob["Kiosk_PopWobbler"], backing], ph.turn(180))
depth = check_clear(body, SCREEN_Y)
for p in ((-0.145, 0.82), (-0.145, 0.666), (0.142, 0.735), (-0.145, 0.44), (0, 0.5), (-0.26, 0.38), (0.26, 0.94)):
    assert depth(*p) > -0.0586, f"Plate 앞 {p}"   # Plate 글자 자리
ph.finish("PH_KioskCafe__Body", body, notes="R2_Cafe 의 PH_Kiosk Visual. 메시는 버거집 키오스크에서 카드 전용 띠만 뺐다. ScreenQuad, Plate 글자는 프리팹이 그리고 이 모델은 그 뒤에 있다. 슬롯 앞면 z -0.067. 날개 포스터는 Wing_L, Wing_R 이 따로 갖고 NEW 흔들이는 여기 있다. 덮개 경첩 테이프가 메시에 남아 있다.")
shots("PH_KioskCafe__Body", body)
print("PH_KIOSK_CAFE_DONE")

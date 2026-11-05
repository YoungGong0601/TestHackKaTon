"""PH_Hand 의 메모, 돋보기, 카드, 가리키는 손과 영수증 종이. 원본 .blend 에서 다시 만든다.
blender -b --factory-startup --python hand.py [-- lens receipt ...]
보이는 면 = Unity -Z (turn 180), 원점 = 범위 중심. 돋보기만 원점이 렌즈 중심이다."""
import sys, os, math, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph, bpy, bmesh
from mathutils import Matrix, Vector

k3d = ph.k3d
LENS_R = 0.06         # HandRig Lens_Radius. 후처리가 lens.position 에 이 반지름 원을 그린다
LENS_END = -0.2       # 손잡이 끝 y (회색 -0.19)
LENS_NECK = 0.15      # 원본에서 이 z 아래가 손잡이다
MEMO_FRONT = -0.0008  # 종이 맨 앞 z. 회색 메시 앞면 -0.001 보다 뒤라 Hand_Memo/Text 를 가리지 않는다
HAND_H, TIP_Y = 0.175, 0.09
HAND_TURN = 20       # 검지 축 회전(도). 새끼 쪽이 +Z 로 물러나 손끝이 범위 중심 쪽으로 온다
Y_CUT = 0.06         # 소매를 자르는 원본 y (고무단 시작 0.036)
CUFF_DEPTH = 0.008   # 소매 끝에서 안쪽 막음까지


def centered(objs):
    """정면 -Z, 범위 중심을 원점으로."""
    vs = [v for o in objs for v in ph.world_verts(o)]
    c = Vector([(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)])
    return ph.turn(180) @ Matrix.Translation(-c)


def anchor(name, parent, p):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = p
    e.parent = parent
    return e


def unity(p):
    return tuple(round(v, 4) + 0.0 for v in (-p[0], p[2], -p[1]))  # + 0.0: -0.0 표기 방지


def done(name, obj, notes):
    keep = set(k3d.tree_of([obj]))
    for x in list(bpy.data.objects):  # 원본이 미리보기에 겹쳐 찍히지 않게
        if x not in keep:
            bpy.data.objects.remove(x, do_unlink=True)
    ph.finish(name, obj, notes=notes)
    k3d.preview(name, [obj], res=(900, 1200), tag='ph')
    k3d.preview(name, [obj], views=((180, 4),), res=(900, 1200), tag='ph_unity')  # Unity -Z 쪽(게임 시점)에서 본 모습


# ---------------------------------------------------------------- 메모: 글씨는 Hand_Memo/Text 가 그린다
BLANK_MEMO = '''
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, sys.argv[1])
import tex2d
W, H = 1608, 2048  # tex2d.memo 의 종이, 찢긴 섬유, 손때만 남기고 줄과 글씨는 뺀다
im = tex2d.paper(W, H, 11)
d = ImageDraw.Draw(im, "RGBA")
rng = np.random.default_rng(3)
for x in range(0, W, 3):
    d.line([(x, 0), (x + rng.integers(-2, 3), rng.integers(4, 22))], fill=(250, 247, 238, 120))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
g = np.exp(-(((xx - 0.1 * W) / (0.12 * W)) ** 2 + ((yy - 0.93 * H) / (0.09 * H)) ** 2)) * tex2d.fbm(W, H, 6, 3, 9)
px = np.asarray(im, np.float32) * (1 - 0.1 * g[..., None])
Image.fromarray(px.clip(0, 255).astype(np.uint8)).save(sys.argv[2])
'''


def memo():
    n = "PH_Hand__Memo"
    ph.load("Items", "Memo")
    src = bpy.data.objects["Memo_Sheet"]
    png = os.path.join(k3d.ART, "Textures", n, f"T_{n}_Paper.png")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    subprocess.run([k3d.PY, "-c", BLANK_MEMO,
                    os.path.join(k3d.SRC, "Blender", "scripts", "Items"), png], check=True)
    m = bpy.data.materials["M_Dyn_Memo_Paper"]
    m.name = f"M_{n}_Paper"
    next(x for x in m.node_tree.nodes if x.type == 'TEX_IMAGE').image = k3d.load_image(png)
    ys = [v.y for v in ph.world_verts(src)]
    o = ph.part(n, [src], ph.move_unity(0, 0, (max(ys) - min(ys)) / 2 + MEMO_FRONT) @ centered([src]))
    done(n, o, f"빈 종이(글씨, 줄 없음), 접힌 자국 유지. 맨 앞 z {MEMO_FRONT}, Hand_Memo/Text 는 그보다 앞(-Z)에 있어야 한다.")


# ---------------------------------------------------------------- 돋보기: 유리는 그림자를 끌 수 있게 자식 메시로 둔다
def lens():
    n = "PH_Hand__Lens"
    ph.load("Items", "Magnifier")
    body, glass = bpy.data.objects["Magnifier_Body"], bpy.data.objects["Magnifier_Lens"]
    c = bpy.data.objects["Magnifier_Socket_LensCenter"].matrix_world.translation
    # 유리 반지름을 LENS_R 로. 원본 테 안쪽은 유리보다 1.75mm 좁아 후처리 원이 테 안쪽 턱을 덮는다 (틈이 안 생긴다)
    s = LENS_R / (glass.dimensions.x / 2)
    squash = (LENS_NECK - c.z - LENS_END / s) / LENS_NECK  # 전체를 줄이지 않고 손잡이만 축으로 줄여 끝을 LENS_END 에 맞춘다
    for v in body.data.vertices:
        if v.co.z < LENS_NECK:
            v.co.z = LENS_NECK - (LENS_NECK - v.co.z) * squash
    M = Matrix.Scale(s, 4) @ ph.turn(180) @ Matrix.Translation(-c)
    o = ph.part(n, [body], M)
    ph.part(n + "_Glass", [glass], M, mark=False).parent = o
    done(n, o, f"원점 = 렌즈 중심 (HandRig lens.position). 균일 스케일 {s:.3f}, 유리 반지름 {LENS_R}, 테 바깥 {0.0562 * s:.3f}. "
               f"손잡이만 축으로 {squash:.3f} 배, 끝 y {LENS_END}. 유리는 자식 메시 {n}_Glass.")


# ---------------------------------------------------------------- 카드
def card():
    n = "PH_Hand__Card"
    ph.load("Items", "BankCard")
    body = bpy.data.objects["BankCard_Body"]
    done(n, ph.part(n, [body], centered([body])), "칩이 있는 앞면이 -Z.")


# ---------------------------------------------------------------- 가리키는 손 (리그 없는 정적 메시)
def crop(o, y):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6,
                           plane_co=(0, y, 0), plane_no=(0, 1, 0), clear_outer=True)
    return bm


def hem(bm):
    """자른 소매 끝: 두 벽을 잇는 테두리 + 안쪽으로 들어간 어두운 막음면."""
    edges = [e for e in bm.edges if e.is_boundary]
    vs = {v for e in edges for v in e.verts}
    c = sum((v.co for v in vs), Vector()) / len(vs)
    rim = bmesh.ops.bridge_loops(bm, edges=edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    inner = {min(e.verts, key=lambda v: (v.co - c).length) for e in rim['edges']}
    ang = lambda v: math.atan2(v.co.z - c.z, v.co.x - c.x)
    uvl = bm.loops.layers.uv.active
    for f in rim['faces']:
        f.smooth = True
        us = [ang(l.vert) / math.tau * 8 for l in f.loops]  # 소매 UV 는 둘레 8회 반복
        for l, u in zip(f.loops, us):
            l[uvl].uv = (u + 8 * (max(us) - u > 4), 1.6 + 0.1 * (l.vert in inner))
    # 각도 내림차순 = 법선 +Y (소매 입구 쪽). 반대로 돌면 뒷면 컬링으로 안 보인다
    bm.faces.new([bm.verts.new((v.co.x, v.co.y - CUFF_DEPTH, v.co.z)) for v in sorted(inner, key=ang, reverse=True)]).material_index = 1


def pointer(age=""):
    n, g = f"PH_Hand__Pointer{age}", f"GrandpaHand{age}_R"
    ph.load("Hands", g)
    arm = bpy.data.objects[g + "_Rig"]
    arm.animation_data.action = bpy.data.actions[g + "_Point"]
    bpy.context.scene.frame_set(1)
    skin = ph.posed(bpy.data.objects[g + "_Skin"], "Point_Skin")
    cuff = ph.posed(bpy.data.objects[g + "_Sleeve"], "Point_Cuff")

    bm = crop(skin, Y_CUT - CUFF_DEPTH - 0.001)
    bm.to_mesh(skin.data)
    bm.free()
    skin.data.polygons.foreach_set("material_index", [0] * len(skin.data.polygons))  # 절단면에 걸친 면도 소매 속이라 안 보인다
    skin.data.materials.pop(index=1)  # 소매 속 팔뚝 단색
    bm = crop(cuff, Y_CUT)
    hem(bm)
    bm.to_mesh(cuff.data)
    bm.free()
    cuff.data.materials[1] = k3d.mat(f"M_{n}_CuffInner", (0.012, 0.01, 0.009), 0.95)  # 뜨개 몸판은 잘려 나갔다
    skin.data.uv_layers[0].name = cuff.data.uv_layers[0].name = "UVMap"  # 이름이 다르면 합칠 때 UV 가 갈라진다

    # 원본: 손가락 -Y, 손등 +Z. 에셋 프레임: 검지 +Z, 손등 -Y (FrontMark 가 손등에 온다)
    pb = arm.pose.bones
    up = (pb["index-finger-phalanx-distal"].tail - pb["index-finger-phalanx-proximal"].head).normalized()
    back = Vector((0, 0, 1))
    back = (back - up * back.dot(up)).normalized()
    R = Matrix.Rotation(math.radians(HAND_TURN), 4, 'Z') @ Matrix((back.cross(up) * -1, -back, up)).to_4x4()
    for o in (skin, cuff):
        o.matrix_world = R @ o.matrix_world
    vs = ph.world_verts(skin) + ph.world_verts(cuff)
    mn = [min(v[i] for v in vs) for i in range(3)]
    mx = [max(v[i] for v in vs) for i in range(3)]
    s = HAND_H / (mx[2] - mn[2])
    tip = max(vs, key=lambda v: v.z)

    def to_anchor(i):
        """손끝을 Tip(0, 0.09, 0) 에 가장 가깝게. 범위 중심은 합격 기준 안에 남긴다."""
        c = (mn[i] + mx[i]) / 2 * s
        tol = 0.0095 + 0.03 * (mx[i] - mn[i]) * s
        return max(-c - tol, min(-c + tol, -tip[i] * s))

    M = ph.move_unity(to_anchor(0), TIP_Y - tip.z * s, to_anchor(1)) @ Matrix.Scale(s, 4) @ ph.turn(180)
    o = ph.part(n, [skin, cuff], M)
    t = anchor(n + "_Tip", o, M @ tip)
    done(n, o, f"Point 자세 정적 메시, 균일 스케일 {s:.3f}, 검지 축으로 {HAND_TURN}도 돌림. 실제 손끝 {n}_Tip = Unity 로컬 {unity(t.location)}.")


def pointer80():
    pointer("80")


# ---------------------------------------------------------------- 영수증 종이: 글씨는 Receipt_View 의 Sharp TMP 와 Blurred 막대가 그린다
def receipt():
    n = "PH_ReceiptSheet"
    ph.load("Kiosk", "KioskReceipt")
    W, H, NX, NZ = 0.105, 0.2, 42, 80
    rnd = random.Random(4)
    tear = [rnd.uniform(0.0002, 0.0014) if i % 2 else 0.0 for i in range(NX + 1)]  # 아래쪽 뜯은 톱니

    def curl(x, z):
        """앞면이 볼록하게 말린 감열지 + 쥐었던 잔물결 + 비스듬히 눌린 자국."""
        t = 2 * z / H
        y = 0.0016 * t * t + 0.0004 * (2 * x / W) ** 2
        y += 0.00016 * math.sin(z * 61 + x * 23) + 0.0001 * math.sin(x * 88 - z * 37)
        return y + 0.00022 * math.exp(-(((0.6 * x + z + 0.03) / 0.0028) ** 2))

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    G = {}
    for j in range(NZ + 1):
        for i in range(NX + 1):
            x, z = (i / NX - 0.5) * W, (j / NZ - 0.5) * H + (tear[i] if j == 0 else 0)
            G[i, j] = bm.verts.new((x, curl(x, z), z))
    for j in range(NZ):
        for i in range(NX):
            f = bm.faces.new((G[i, j], G[i + 1, j], G[i + 1, j + 1], G[i, j + 1]))  # 앞 -Y
            for l in f.loops:
                l[uvl].uv = (l.vert.co.x / W + 0.5, l.vert.co.z / H + 0.5)
    me = bpy.data.meshes.new(n + "_Src")
    bm.to_mesh(me)
    bm.free()
    sheet = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(sheet)

    me.materials.append(k3d.mat(f"M_{n}_Paper", (0.92, 0.905, 0.85), 0.45))  # T_KioskReceipt_Paper 바탕색
    me.materials.append(bpy.data.materials["M_KioskReceipt_Back"])
    sol = sheet.modifiers.new("sol", 'SOLIDIFY')
    sol.thickness, sol.offset, sol.use_rim = 0.00012, -1, True
    sol.material_offset = sol.material_offset_rim = 1  # 뒷면, 옆면
    k3d.apply_all(sheet)
    k3d.smooth(sheet, 60)
    ys = [v.y for v in ph.world_verts(sheet)]
    M = ph.move_unity(0, 0, (max(ys) - min(ys)) / 2) @ centered([sheet])  # 맨 앞 z 0 = 회색 Sheet 앞면. 글씨(z -0.002)를 가리지 않는다
    done(n, ph.part(n, [sheet], M),
         "무지 감열지, 앞면 -Z. 글씨는 Receipt_View 의 Sharp TMP 와 Blurred 막대가 그린다. "
         "Receipt_View/Visual 아래 로컬 0 에 넣고 회색 Sheet 를 지운다 (Sheet 자식으로 넣으면 그 스케일이 곱해진다).")


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for row in (memo, lens, card, pointer, receipt, pointer80):
    if not args or row.__name__ in args:
        row()

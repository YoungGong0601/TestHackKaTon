"""PH_BusShelter, PH_BIS, PH_BusStopSign: BusStop 원본 .blend 를 친구 프리팹 규격으로 맞춘다.

치수는 축별 구간 선형 맵으로 맞춘다. 구운 UV 는 그대로라 원본 텍스처를 다시 쓰고, 정점만 옮겨 뒤집힘이 없다.
Blender 좌표로 적는다 (Unity = -x, z, -y).
"""
import sys, os, math, shutil, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "BusStop"))
import ph, bpy
import numpy as np
import _bs as B
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

k3d = ph.k3d


def remap(objs, fn):
    """fn: 월드 좌표 (N,3) -> (N,3). 오브젝트 변환은 그대로 두고 정점만 옮긴다."""
    bpy.context.view_layer.update()
    for o in objs:
        mw = o.matrix_world
        inv = mw.inverted()
        for v, c in zip(o.data.vertices, fn(np.array([mw @ v.co for v in o.data.vertices]))):
            v.co = inv @ Vector(c)
        o.data.update()


def preview(name, o, views, shots=()):
    keep = k3d.tree_of([o])
    for x in [x for x in bpy.data.objects if x not in keep]:           # 원본이 남아 있으면 겹쳐 찍힌다
        bpy.data.objects.remove(x)
    k3d.preview(name, [o], views=views, tag="ph")
    for tag, cam, target, lens in shots:
        B.shot(name, cam, target, lens, "ph_" + tag)


def shelter():
    """turn(0): 원본 앞(-Y, 도로)이 Unity +Z 다. 프로토타입에서도 도로가 프리팹의 +Z 쪽이고
    옆유리가 Unity -X, 광고판이 Unity +X 라 회전 없이 맞는다.
    프로토타입 뒷벽 z3 -32.15 = 로컬 z -1.175(Col_Back), 벤치 (33.8, -32.6) = 로컬 (0.5, -0.725)(Col_Bench 안)."""
    ph.load("BusStop", "BusShelter")
    g = lambda n: bpy.data.objects["BusShelter_" + n]
    k = 2.765 / 2.818
    move = np.array(ph.at_unity(0.5, 0, -0.725)) - (0, 0.52, 0)        # 벤치 원본 중심 (0, 0.52)

    def fit(c):
        x, y, z = c.T
        # 뒷벽을 +0.175 옮기고, 깊이는 옆유리 앞 보 구간(앞)과 기둥-물받이 사이(뒤)에서만 줄인다.
        # ponytail: z 2.0 위 선홈통 윗단이 2.5 cm 깊이로 눌린다. 뒤에서만 보여 두었다. 거슬리면 선홈통을 따로 모델링한다.
        low = np.interp(y, (-1.9, -1.71, -0.96, 1.15, 1.40), (-1.495, -1.305, -0.785, 1.325, 1.45))
        roof = np.interp(y, (1.05, 1.23, 1.40), (1.225, 1.29, 1.46))
        return np.c_[x, np.where((z > 2.0) & (y > 1.05), roof, low), z * k]

    def decal_fit(c):                                                  # 기증 명판만 벤치를 따라간다
        on_bench = (np.abs(c[:, 0]) < 1.32) & (c[:, 1] < 0.9)
        return np.where(on_bench[:, None], c + move, fit(c))

    rest = [g(n) for n in ("Frame", "Glass", "Roof", "Signs", "Leaves")]
    remap(rest, fit)
    remap([g("Bench")], lambda c: c + move)
    remap([g("Decals")], decal_fit)
    o = ph.part("PH_BusShelter", rest + [g("Bench"), g("Decals")], ph.turn(0))
    ph.finish("PH_BusShelter", o)
    preview("PH_BusShelter", o, ((0, 10), (180, 10), (35, 18), (215, 12)),
            (("road", (-1.0, -6.5, 1.55), (0, 0.4, 1.2), 30),
             ("rear", (6.0, 3.8, 1.8), (3.3, 1.3, 1.5), 40),
             ("eave", (2.2, -2.9, 1.1), (3.2, -0.9, 2.55), 30)))


def led_blank():
    """꺼진 LED 판. 도트·색·모듈 이음매는 _tex.led_board 와 같고 글자만 없다."""
    W, H, GX, GY = 2048, 846, 224, 92
    ys, xs = np.mgrid[0:H, 0:W] + 0.5
    r = np.hypot(xs * GX / W % 1 - 0.5, ys * GY / H % 1 - 0.5)
    dot = np.clip((0.40 - r) / 0.09, 0, 1)[..., None]
    px = np.array((0.03, 0.026, 0.022)) + np.array((0.11, 0.06, 0.028)) * dot
    px[:, (np.arange(0, GX, 32) * W / GX).astype(int)] *= 0.45
    px[(np.arange(0, GY, 16) * H / GY).astype(int)] *= 0.45
    im = bpy.data.images.new("T_PH_BIS_Panel", W, H)
    im.pixels.foreach_set(np.dstack((px, np.ones((H, W))))[::-1].astype(np.float32).ravel())
    p = os.path.join(k3d.ART, "Textures", "PH_BIS", "T_PH_BIS_Panel.png")
    k3d._save(im, p)
    return p


def plane_clear(o):
    """친구 글자 면(x ±0.075) 위 격자에서 바깥 광선은 아무것도 맞지 않고, 안쪽 광선은 바로 뒤 판을 맞아야 한다."""
    t = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    for s in (-1, 1):
        for y in np.linspace(-0.749, 0.749, 31):
            for z in np.linspace(2.411, 3.029, 13):
                p = Vector((s * 0.075, y, z))
                assert t.ray_cast(p, Vector((s, 0, 0)))[0] is None, ("글자 면 앞에 메시", p)
                d = t.ray_cast(p, Vector((-s, 0, 0)))[3]
                assert d is not None and 0.001 < d < 0.0035, ("글자 면 뒤 판 거리", p, d)


def bis():
    """turn(90): 원본 앞(점검구, 스티커)이 Unity -X, 곧 플레이어가 오는 BisFaceA 쪽을 본다.
    글자 면은 프로토타입대로 중심 높이 2.72, 1.5 x 0.62, x ±0.075. 그 앞을 가리는 것이 없어야 한다."""
    ph.load("BusStop", "BusStopBIS")
    body, decals = bpy.data.objects["BusStopBIS_Body"], bpy.data.objects["BusStopBIS_Decals"]

    def fit(c):
        x, y, z = c.T
        box = z > 2.3
        lx = np.interp(np.abs(x), (0, 0.75, 0.79, 0.81, 0.89, 0.935), (0, 0.75, 0.78, 0.79, 0.815, 0.83))  # 길이 1.87 -> 1.66
        ly = np.interp(np.abs(y), (0, 0.08, 0.092, 0.105), (0, 0.07, 0.078, 0.08))                        # 면 ±0.07, 테 ±0.08
        z2 = np.interp(z, (0, 2.3, 2.335, 3.09, 3.12), (0, 2.3, 2.345, 3.10, 3.125))                      # 창을 글자 면에 맞춤
        r = np.hypot(x, y)                                                                                # 바닥 덮개 r 0.13 -> 0.08
        s = np.where(z < 0.08, np.interp(r, (0, 0.0572, 0.13), (0, 0.0572, 0.08)) / np.maximum(r, 1e-6), 1)
        return np.c_[np.where(box, np.sign(x) * lx, x * s), np.where(box, np.sign(y) * ly, y * s), z2]

    remap([body, decals], fit)
    m = B.m_image("M_PH_BIS_Panel", led_blank(), rough=0.3)
    q = [B.quad("q", 1.504, 0.624, m, (0, s * 0.0725, 2.72), (0, 0, 0 if s < 0 else math.pi)) for s in (-1, 1)]
    panel = B.join(q, "PH_BIS_Panel")
    o = ph.part("PH_BIS", [body, decals, panel], ph.turn(90))
    plane_clear(o)
    ph.finish("PH_BIS", o)
    preview("PH_BIS", o, ((90, 8), (-90, 8), (0, 8), (50, 14)),
            (("look", (6.0, 1.2, 1.55), (0, 0, 2.5), 45),
             ("close", (1.6, 0.9, 1.7), (0, 0.3, 2.72), 35),
             ("foot", (0.55, -0.35, 0.45), (0, 0, 0.1), 40)))


def sign_head():
    """프로토타입 매장 앞 표지는 "시장 입구"다. 원본 머리판은 은행골 입구라 글자만 바꿔 그린다."""
    src = open(os.path.join(HERE, "..", "BusStop", "_tex.py"), encoding="utf-8").read()
    for a, b in (('"은행골 입구", "eb", 150', '"시장 입구", "eb", 150'), ("Eunhaenggol Entrance", "Sijang Entrance"),
                 ('"14-208", "eb", 96', '"14-231", "eb", 96'), ("동사무소 · 차고지 · 중학교", "시장 공영주차장 · 삼거리 · 보건소")):
        assert a in src, a
        src = src.replace(a, b)
    p = os.path.join(k3d.ART, "Textures", "PH_BusStopSign", "T_PH_BusStopSign_Head.png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        job = os.path.join(t, "_tex.py")  # -c 로 넘기면 Windows 명령줄 한도를 넘는다
        with open(job, "w", encoding="utf-8") as f:
            f.write(src)
        subprocess.run([k3d.PY, "-I", job, "BusStopSign", t, k3d.CACHE], check=True)
        shutil.copyfile(os.path.join(t, "Textures", "BusStopSign", "T_BusStopSign_Head.png"), p)
    return p


def sign():
    """turn(180): 프로토타입 표지 그림은 +z3, 곧 Unity -Z 를 본다. 원본 2.957 m 를 3.07 m 로 균일 확대하면 폭도 0.62 가 된다."""
    path = sign_head()
    ph.load("BusStop", "BusStopSign")
    mats = bpy.data.materials
    mats["M_Dyn_BusStopSign_Routes"].name = "M_PH_BusStopSign_Routes"
    head = mats["M_BusStopSign_Head"]
    head.name = "M_PH_BusStopSign_Head"
    next(n for n in head.node_tree.nodes if n.type == 'TEX_IMAGE').image = k3d.load_image(path)
    objs = [bpy.data.objects["BusStopSign_" + n] for n in ("Body", "Head", "Routes", "Decals")]
    o = ph.part("PH_BusStopSign", objs, ph.turn(180) @ Matrix.Scale(3.07 / 2.957, 4))
    ph.finish("PH_BusStopSign", o)
    preview("PH_BusStopSign", o, ((180, 8), (0, 8), (215, 12)),
            (("head", (-0.3, 2.6, 2.2), (0, 0, 2.72), 45),))


for build in (shelter, bis, sign):
    build()

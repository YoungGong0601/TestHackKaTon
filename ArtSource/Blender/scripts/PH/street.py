"""PH_Rail, PH_Curb: 거리의 긴 메시. 실행: blender -b --factory-startup --python street.py [-- PH_Rail PH_Curb]

PH_Rail: 85 m 를 한 장에 구우면 텍셀이 모자라서, 5기둥 4칸짜리 울타리를 한 번 굽고 기둥과 칸을 조각으로 잘라
         무작위로 다시 조립한다 (칸은 180도 돌려 쓰기도 한다. 뒤집기는 없다).
PH_Curb: sidewalk.py 의 1 m 경계석을 단면만 규격으로 바꿔 120개 놓는다 (M_Tile 월드 UV, 굽기 없음).
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Street")]
import ph, bpy, bmesh, k3d
import _street as S
import sidewalk as SW
from mathutils import Matrix

# 난간 (프로토타입 d(-60, 25.4): 길이 85.4, 기둥 간격 2.2, z3 -35. 높이만 규격 0.92 에 맞춘다)
L, SPANS, H = 85.4, 39, 0.92
PLATE = 0.10                   # 기초판 폭. 양 끝 기초판 바깥이 정확히 ±L/2
PITCH = (L - PLATE) / SPANS    # 2.187 m, Rail_E(스케일 0.941)에서는 2.06 m
POST, BARS, BAR_R = 0.06, 16, 0.0105
BAR_Z0, BAR_Z1 = 0.13, 0.85    # 끝은 위아래 가로대 속에 묻힌다
KIT_POSTS = 5                  # 구울 울타리 = 기둥 5, 칸 4


def tag(objs, pid):
    """베이크 뒤 조각을 다시 고르려고 면에 번호를 남긴다."""
    for o in objs:
        k3d.apply_all(o)
        o.data.attributes.new("pid", 'INT', 'FACE').data.foreach_set("value", [pid] * len(o.data.polygons))
    return objs


def cut(src, pid, x):
    """번호가 pid 인 면만 새 메시로 (x 를 원점으로)."""
    me = src.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.faces.layers.int["pid"]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != pid], context='FACES')
    bm.to_mesh(me)
    bm.free()
    me.transform(Matrix.Translation((-x, 0, 0)))
    return me


def inst(me, M):
    o = S.link(bpy.data.objects.new(me.name, me))
    o.matrix_world = M
    return o


def post(i, x, paint, steel, refl=None):
    """각관 기둥 + 머리 캡 + 기초판(앵커 4개). refl: 차도(+Y) 쪽 반사지."""
    A = f"P{i}"
    parts = [S.box(A + "Body", (POST, POST, 0.90), (x, 0, 0.455), mat=paint, bevel=0.006, segs=2),
             S.box(A + "Cap", (0.064, 0.064, 0.016), (x, 0, H - 0.008), mat=paint, bevel=0.005, segs=2),
             S.box(A + "Plate", (PLATE, PLATE, 0.008), (x, 0, 0.004), mat=paint, bevel=0.0015, segs=1),
             S.box(A + "Weld", (0.067, 0.067, 0.006), (x, 0, 0.011), mat=paint, bevel=0.0025, segs=1)]
    for k, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        at = (x + sx * 0.037, sy * 0.037, 0.008)
        parts.append(S.cyl(f"{A}Nut{k}", 0.0085, 0.007, at, (0, 0, 0.4 * k), mat=steel, seg=6, bevel=0))
        parts.append(S.cyl(f"{A}Stud{k}", 0.0045, 0.012, at, mat=steel, seg=6, bevel=0))
    if refl:
        parts.append(S.box(A + "Refl", (0.04, 0.002, 0.13), (x, POST / 2 + 0.0005, 0.70), mat=refl, bevel=0.0005, segs=1))
    return parts


def panel(i, x0, x1, paint, bent=False):
    """가로대 둘 + 세로살 + 기둥 쪽 받침쇠. 가로대는 기둥 중심까지 들어가 끝이 안 보인다. bent: 무언가에 받혀 휜 살."""
    A, w, mid = f"S{i}", x1 - x0, (x0 + x1) / 2
    parts = [S.box(A + "Top", (w, 0.05, 0.06), (mid, 0, 0.865), mat=paint, bevel=0.008, segs=2),
             S.box(A + "Bot", (w, 0.04, 0.05), (mid, 0, 0.12), mat=paint, bevel=0.006, segs=2)]
    for k, x in enumerate((x0 + 0.036, x1 - 0.036)):
        parts.append(S.box(f"{A}CT{k}", (0.012, 0.056, 0.07), (x, 0, 0.865), mat=paint, bevel=0))
        parts.append(S.box(f"{A}CB{k}", (0.012, 0.046, 0.06), (x, 0, 0.12), mat=paint, bevel=0))
    for k in range(BARS):
        x = x0 + POST / 2 + (w - POST) * (k + 0.5) / BARS
        pts = [(x, 0, BAR_Z0), (x, 0, BAR_Z1)]
        if bent and 5 <= k <= 8:
            dy, dx = (0.032, 0.022, 0.03, 0.014)[k - 5], (-0.01, 0.012, -0.006, 0.01)[k - 5]
            bow = [math.sin(math.pi * j / 12) ** 2 for j in range(13)]
            pts = [(x + dx * b, dy * b, BAR_Z0 + (BAR_Z1 - BAR_Z0) * j / 12) for j, b in enumerate(bow)]
        parts.append(S.tube(f"{A}Bar{k}", pts, BAR_R, sides=8, mat=paint, caps=False))
    return parts


def rail():
    k3d.reset()
    # 프로토타입 green #3D5A48. 위쪽은 볕에 바래고 아래쪽은 녹과 흙탕이 오른다.
    wear = dict(edge=1.0, edge_col=(0.17, 0.12, 0.08), edge_metal=0.3, scratches=0.7, streaks=0.5, bottom=0.5,
                bottom_h=0.15, bump=0.04)
    paint = S.paint("M_PH_RailPaint", (0.040, 0.105, 0.062), 0.46, rust=0.45, rust_scale=6, rust_z=0.7, fade_top=0.03, **wear)
    old = S.paint("M_PH_RailPaintOld", (0.046, 0.098, 0.066), 0.55, rust=0.6, rust_scale=8, fade_top=0.08, seed=3.0, **wear)
    steel = S.galv("M_PH_RailBolt", 0.5, base=(0.35, 0.33, 0.30), rust=0.6, rust_scale=30)
    refl = S.wmat("M_PH_RailRefl", (0.78, 0.52, 0.02), 0.32, 0.0, var=0.1, grime=0.6, scratches=0.6, bump=0.25,
                  bump_scale=900, streaks=0.3)
    parts = []
    for i in range(KIT_POSTS):
        parts += tag(post(i, i * PITCH, old if i % 2 else paint, steel, refl if i == 2 else None), i)
    for i in range(KIT_POSTS - 1):
        parts += tag(panel(i, i * PITCH, (i + 1) * PITCH, old if i == 1 else paint, bent=i == 2), 100 + i)
    kit = S.join(parts, "PH_RailKit")
    k3d.bake(kit, 2048, samples=24, ao_distance=0.08, margin=6, name="PH_Rail")
    k3d.preview("PH_RailKit", [kit], views=((12, 8), (192, 8)), tag="ph")

    posts = [cut(kit, i, i * PITCH) for i in range(KIT_POSTS)]
    panels = [cut(kit, 100 + i, (i + 0.5) * PITCH) for i in range(KIT_POSTS - 1)]
    bpy.data.objects.remove(kit)
    rng = random.Random(85)
    x0 = -(L - PLATE) / 2
    objs = []
    for i in range(SPANS + 1):   # 반사지 기둥은 돌리지 않아 늘 차도를 본다
        objs.append(inst(posts[2 if i % 5 == 2 else rng.choice((0, 1, 3, 4))], Matrix.Translation((x0 + i * PITCH, 0, 0))))
    for i in range(SPANS):
        me = panels[rng.choices(range(4), (4, 3, 1, 4))[0]]
        objs.append(inst(me, Matrix.Translation((x0 + (i + 0.5) * PITCH, 0, 0)) @ Matrix.Rotation(math.pi * rng.randrange(2), 4, 'Z')))
    # 원본 프레임은 프로토타입과 같아 도로가 +Y. turn(180) 뒤 Unity +Z 가 차도, -Z 가 보도다.
    o = ph.part("PH_Rail", objs, ph.turn(180))
    for c in objs:
        bpy.data.objects.remove(c)
    ph.finish("PH_Rail", o, notes=f"길이 {L} m, {SPANS}칸(기둥 간격 {PITCH:.3f} m). 높이 {H}, 기둥 {POST}, 기초판 {PLATE}(전체 깊이). "
                                  "원점 = 바닥 중앙. 프리팹 로컬 +Z = 차도(반사지), -Z = 보도. 프로토타입 기둥은 1 m 지만 규격 0.92 를 따랐다.")
    return o


def curb():
    ph.load("Street", "StreetCurb")   # M_Tile_Street_Curb/B/C 재사용
    bpy.data.objects.remove(bpy.data.objects["StreetCurb_Body"])
    ma, mb, mc = (bpy.data.materials["M_Tile_Street_Curb" + s] for s in ("", "B", "C"))
    SW.CURB_W, SW.CURB_H, SW.CURB_BOT = 0.26, 0.16, 0.0   # 프로토타입 Q(c, .16, .26): 연석 전체가 땅 위로 나온다
    rng = random.Random(120)
    gap = 0.002
    parts = []
    for i in range(120):   # stone() 의 비틀림은 원점 기준이다. 제자리에서 만들면 끝쪽 돌이 옆으로 27 cm 까지 밀려서 원점에서 만들고 옮긴다
        parts.append(SW.stone(f"Curb{i}", gap - 0.5, 0.5 - gap, 0.16, 0.16, rng.choice((ma, ma, mb, mc)), rng))
        parts[-1].matrix_world = Matrix.Translation((i - 59.5, 0, 0))
    # 돌 사이 4 mm 틈 뒤로 하늘이 보이지 않게 어두운 줄눈 몸통을 넣는다
    core = S.box("CurbCore", (119.99, 0.23, 0.14), (0, 0.135, 0.07), mat=S._tinted_copy(ma, "M_Tile_Street_CurbJoint", (0.42, 0.42, 0.41)), bevel=0)
    k3d.uv_world(core, S.TILE_CURB)
    parts.append(core)
    # 둥근 모서리(원본 앞면 y=0)가 차도. 프로토타입 차도는 연석 +z3 쪽이라 Unity -Z 다.
    o = ph.part("PH_Curb", parts, ph.turn(180) @ Matrix.Translation((0, -0.13, 0)))
    for c in parts:
        bpy.data.objects.remove(c)
    ph.finish("PH_Curb", o, notes="1 m 돌 120개, 줄눈 4 mm. 단면 0.26 x 0.16, 원점 = 바닥 중앙. 프리팹 로컬 -Z = 차도(둥근 모서리), +Z = 보도. "
                                  "M_Tile 월드 UV 3 m, 돌마다 UV 위치와 색이 다르다.")
    return o


def shots(name, o, views):
    k3d.preview(name, [o], tag="ph")
    for i, kw in enumerate(views):
        S.fp_shot(name, [o], tag=f"ph_v{i}", **kw)


if __name__ == "__main__":
    todo = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["PH_Rail", "PH_Curb"]
    if "PH_Rail" in todo:
        # Unity 쪽에서 본 보도면(az 180 = Blender +Y), 차도면, 길이 방향, 기초판
        shots("PH_Rail", rail(), [dict(dist=3.2, eye=1.55, look_h=0.45, az=205, lens=35, cx=(38.0, 0, 0)),
                                  dict(dist=3.2, eye=1.55, look_h=0.45, az=25, lens=35, cx=(0.0, 0, 0)),
                                  dict(dist=9.0, eye=1.2, look_h=0.5, az=-82, lens=35, cx=(30.0, 0, 0)),
                                  dict(dist=0.9, eye=0.5, look_h=0.1, az=160, lens=35, cx=(42.65, 0, 0))])
    if "PH_Curb" in todo:
        # az 180 = Unity -Z 쪽(차도)에서 본 모습
        shots("PH_Curb", curb(), [dict(dist=2.6, eye=1.0, look_h=0.05, az=205, lens=35, cx=(0.0, 0, 0)),
                                  dict(dist=2.6, eye=1.0, look_h=0.05, az=25, lens=35, cx=(0.0, 0, 0)),
                                  dict(dist=1.4, eye=0.5, look_h=0.05, az=250, lens=35, cx=(59.6, 0, 0))])

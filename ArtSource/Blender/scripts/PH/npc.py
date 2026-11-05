"""PH_NPC: 모습 9개를 Idle 포즈의 정적 메시 둘로 나눈다. 몸은 ReactPivot/Visual, 머리는 HeadPivot/Visual 로 간다.

blender -b --factory-startup --python npc.py [-- 모습 ...]

- 31본 모습은 .blend 에 액션이 없다(저장 때 버려짐). 같은 에셋 FBX 의 Idle 테이크를 얹는다 (rest 차이 0.02mm).
- 62본 모습(SuitMan, Youth, Staff)은 Idle_Neutral 을 쓴다. Idle 은 다리가 벌어지고 뒷발이 꺾인 자세다.
- 머리는 HeadPivot 기준이고 Y 축으로만 돈다. 그래서 목 중심을 축(x 0, z 0)에 맞추고, 몸의 목 끝을 막아 틈이 비치지 않게 한다.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph, bpy, bmesh
from mathutils import Matrix
from ph_spec import LOOKS

k3d = ph.k3d
HEIGHT, PIVOT_Y = 1.71, 1.58
BAG = ph.at_unity(0.32, 0.72, 0)
# 포즈 좌표 z (머리 아랫단, 몸 윗단). 어깨 위부터 턱 밑까지 목만 지나는 구간을 잰 값이다. 62본은 머리가 이미 따로라 아랫단만 자른다.
NECK = {
    "OfficeMan": (1.458, 1.475), "Ajumma": (1.347, 1.357), "StudentWoman": (1.392, 1.404),
    "StudentMan": (1.493, 1.511), "YoungWoman": (1.373, 1.385), "OldMan": (1.393, 1.415),
    "SuitMan": (1.44, None), "Youth": (1.40, None), "Staff": (1.40, None),
}


def idle(asset):
    rig = bpy.data.objects.get(asset + "_Rig") or bpy.data.objects[asset + "_Armature"]
    act, frame = bpy.data.actions.get("Idle_Neutral"), 0
    if act is None:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(k3d.ART, "Models", "Characters", asset + ".fbx"))
        for o in set(bpy.data.objects) - before:
            bpy.data.objects.remove(o, do_unlink=True)
        act, frame = next(a for a in bpy.data.actions if a.name.endswith("|Idle")), 1
    ad = rig.animation_data or rig.animation_data_create()
    ad.action = act
    ad.action_slot = act.slots[0]
    bpy.context.scene.frame_set(frame)
    return rig


def islands(bm):
    seen, out = set(), []
    for v0 in bm.verts:
        if v0 in seen:
            continue
        seen.add(v0)
        stack, part = [v0], []
        while stack:
            v = stack.pop()
            part.append(v)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(part)
    return sorted(out, key=len)


def sided(mesh, src=None):
    """면마다 어느 쪽인지 표시한 bmesh. 0 목을 지나는 본체, 1 머리, 2 몸.
    src(31본): 머리카락·눈은 따로 떨어진 조각이고, 포니테일은 본체에 붙은 채 목 아래로 내려온다. Head 웨이트로 가른다."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    side = bm.faces.layers.int.new("side")
    if src:
        g = src.vertex_groups["Head"].index
        hw = [sum(e.weight for e in v.groups if e.group == g) for v in src.data.vertices]
        *pieces, main = islands(bm)
        for part in pieces:
            k = 1 if sum(hw[v.index] for v in part) / len(part) > 0.5 else 2
            for f in {f for v in part for f in v.link_faces}:
                f[side] = k
        for f in {f for v in main for f in v.link_faces}:
            if all(hw[v.index] > 0.9 for v in f.verts):
                f[side] = 1
    return bm


def cut(bm, mesh, z, head):
    """머리(head) 또는 몸만 남긴다. 반대쪽 조각을 버리고 z 평면으로 잘라 본체의 반대쪽을 지운 뒤 잘린 목을 막는다. (오브젝트, 목 중심 x y)."""
    b = bm.copy()
    side = b.faces.layers.int["side"]
    bmesh.ops.delete(b, geom=[f for f in b.faces if f[side] == (2 if head else 1)], context='FACES')
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], dist=1e-6, plane_co=(0, 0, z), plane_no=(0, 0, 1))
    bmesh.ops.delete(b, geom=[f for f in b.faces if f[side] == 0 and (f.calc_center_median().z < z) == head], context='FACES')
    ring = [e for e in b.edges if e.is_boundary and all(abs(v.co.z - z) < 1e-4 for v in e.verts)]
    vs = {v for e in ring for v in e.verts}
    c = [(min(v.co[i] for v in vs) + max(v.co[i] for v in vs)) / 2 for i in (0, 1)]
    uv = b.loops.layers.uv.active
    skin = next(iter(vs)).link_loops[0][uv].uv.copy()
    for f in bmesh.ops.holes_fill(b, edges=ring, sides=0)["faces"]:
        f.smooth = False  # 막은 면이 목의 부드러운 노멀을 끌어당기지 않게
        for l in f.loops:
            l[uv].uv = skin  # 고리의 UV 를 그대로 펴면 아틀라스의 엉뚱한 곳이 비친다
    me = mesh.copy()
    b.to_mesh(me)
    b.free()
    o = bpy.data.objects.new("x_cut", me)
    bpy.context.scene.collection.objects.link(o)
    return o, c


def core(o, c, z0, z1, finger):
    """목 심: 몸의 목에서 머리 속 HeadPivot 높이까지 가는 닫힌 원뿔. 머리에 가려 보이지 않고, 틈이 나도 피부색이 보인다."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.active
    skin = min(bm.verts, key=lambda v: (v.co - finger).length).link_loops[0][uv].uv.copy()
    r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.03, radius2=0.012, depth=z1 - z0,
                              matrix=Matrix.Translation((c[0], c[1], (z0 + z1) / 2)))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.smooth = True
        for l in f.loops:
            l[uv].uv = skin
    bm.to_mesh(o.data)
    bm.free()


def show(name, body, head):
    for o in bpy.context.scene.objects:
        o.hide_render = o not in (body, head)
    up = Matrix.Translation((0, 0, PIVOT_Y))
    head.matrix_world = up
    k3d.preview(name, [body, head], views=((0, 6), (90, 6), (180, 6), (35, 15)), res=(600, 800), lens=70, tag="ph")
    for a in (35, -35):
        head.matrix_world = up @ Matrix.Rotation(math.radians(a), 4, 'Z')
        k3d.preview(name, [head], views=((0, 5), (90, 5), (180, 5)), res=(500, 500), lens=70, ground=False, tag=f"ph_turn{a:+d}")


def build(look):
    asset = "Npc" + look
    ph.load("Characters", asset)
    rig = idle(asset)
    lo, hi = NECK[look]
    src = bpy.data.objects[asset + "_Body"]
    posed = ph.posed(src, "x_posed")
    if hi:
        bm = sided(posed.data, src)
        head, neck = cut(bm, posed.data, lo, True)
        body, _ = cut(bm, posed.data, hi, False)
    else:
        hp = ph.posed(bpy.data.objects[asset + "_Head"], "x_headposed")
        bm = sided(hp.data)
        head, neck = cut(bm, hp.data, lo, True)
        body = posed
    bm.free()
    if look == "StudentMan":  # 백팩이 몸 범위 중심을 뒤로 밀어 목이 축에서 4.5cm 벗어난다. 두께만 30% 줄여 2cm 로.
        for v in body.data.vertices:
            v.co.y = min(v.co.y, 0.125 + (v.co.y - 0.125) * 0.7)

    floor = min(v.co.z for v in body.data.vertices)
    s = HEIGHT / (max(v.co.z for v in head.data.vertices) - floor)

    def slide(i):
        """목을 축(0)에 놓되 몸 범위 중심은 ph_check 허용치(0.03 + 3%) 안에 둔다."""
        a = [v.co[i] * s for v in body.data.vertices]
        c, tol = (min(a) + max(a)) / 2, 0.029 + 0.03 * (max(a) - min(a))
        return min(max(-neck[i] * s, -c - tol), -c + tol)

    t = (slide(0), slide(1))
    M = ph.turn(0) @ Matrix.Translation((*t, -floor * s)) @ Matrix.Scale(s, 4)  # 앞 +Z
    finger = (rig.pose.bones.get("Fingers.R") or rig.pose.bones["Middle2.R"]).head
    core(body, neck, lo, PIVOT_Y / s + floor, finger)

    off = [neck[i] * s + t[i] for i in (0, 1)]
    note = (f"{asset} 정적 메시. 포즈 {'Idle' if hi else 'Idle_Neutral'}, 배율 {s:.4f}, 키 {HEIGHT}."
            f" 목 중심은 HeadPivot 축에서 x {off[0]:+.3f}, Unity z {-off[1]:+.3f}.")
    rows = f"PH_NPC__{look}_Body", f"PH_NPC__{look}_Head"
    b = ph.part(rows[0], [body], M)
    h = ph.part(rows[1], [head], ph.move_unity(0, -PIVOT_Y, 0) @ M)
    for o in (b, h):
        k3d.select([o])
        bpy.ops.object.material_slot_remove_unused()
    bag = min((v.co - BAG).length for v in b.data.vertices)
    assert bag > 0.03, f"{look}: 오른손이 BagAnchor 를 삼킴 ({bag:.3f})"
    ph.finish(rows[0], b, notes=note)
    ph.finish(rows[1], h, notes=note)
    print(f"PH_NPC {look} s {s:.4f} neck {off[0]:+.3f} {off[1]:+.3f} bag {bag:.3f}")
    show("PH_NPC__" + look, b, h)


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else LOOKS
for look in args:
    build(look)

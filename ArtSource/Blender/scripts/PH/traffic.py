"""PH_Car, PH_Scooter: 큰길을 지나는 차와 배달 오토바이. 둘 다 앞 +X 의 정적 메시 하나다 (TrafficMover 가 루트째 민다, 반대 차선은 Y 180).

blender -b --factory-startup --python traffic.py [-- car scooter]

- 회색 PH_Scooter 는 탄 사람까지 한 덩어리(Rider, Head)라 NpcYouth 를 태워 합친다. 소켓 Seat, Foot, Grip 에 맞춰 쉬는 자세에서 직접 앉힌다.
- 이 리그의 뼈는 관절에 붙은 토막이고 Foot 은 다리와 끊겨 Root 밑에 있어서 IK 제약을 걸 수 없다. limb 이 두 마디를 직접 계산한다.
- 폭이 회색(±0.25)보다 넓은 건 핸들(±0.34)·거울(±0.35)·토시(±0.38) 때문이다. 충돌체가 없어 게임에는 영향이 없다.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph, bpy, bmesh
from mathutils import Matrix, Quaternion, Vector

k3d = ph.k3d
CAR_LEN, SCOOTER_LEN = 4.4, 1.75
RIDER = 1.02     # NpcYouth 배율. 헬멧 꼭대기가 회색 Head 윗면 1.72 에 온다
HIP = (0.15, 0.08)  # 엉덩이 관절의 y, 안장 소켓 위 높이
LEAN = (4, 9, 14, 19, 12, 5)  # 골반, 배, 허리, 가슴, 목, 머리가 앞으로 숙인 각도 (도, 쉬는 자세 기준)
ARM = 1.3        # 이 모델은 팔이 짧아(어깨에서 손목 0.39) 좌석에서 그립에 닿지 않는다. 늘이는 배율


def car():
    """몸체·유리·실내·바퀴를 그대로 합친다. 등배율이라 지붕은 회색 1.45 보다 낮고 거울은 폭 허용치 안이다."""
    ph.load("Vehicles", "CarSedan")
    src = [o for o in bpy.data.objects if o.type == 'MESH']
    ys = [p.y for o in src for p in ph.world_verts(o)]
    s = CAR_LEN / (max(ys) - min(ys))
    o = ph.part("PH_Car", src, ph.turn(-90) @ Matrix.Scale(s, 4))
    for x in src:
        bpy.data.objects.remove(x)
    ph.finish("PH_Car", o, notes=f"CarSedan 정적 메시, 등배율 {s:.4f}. 바퀴는 돌지 않는다.")
    k3d.preview("PH_Car", [o], views=((-55, 12), (0, 4), (125, 12)), tag="ph")


def put(rig, bone, rot, at=None, stretch=1):
    """뼈를 쉬는 자세에서 rot 만큼 돌려 아마추어 공간 at 에 놓는다 (없으면 부모가 데려간 자리). stretch: 뼈 길이 방향 배율."""
    pb = rig.pose.bones[bone]
    m = rot.to_matrix().to_4x4() @ pb.bone.matrix_local.to_3x3().to_4x4() @ Matrix.Diagonal((1, stretch, 1, 1))
    m.translation = pb.head if at is None else at
    pb.matrix = m
    bpy.context.view_layer.update()


def limb(rig, a, b, c, target, pole, stretch=1):
    """두 마디 IK: a, b 를 돌려 c 의 머리 자리를 target 에 맞춘다. pole 쪽으로 관절이 굽는다."""
    A, B, C = (rig.data.bones[n] for n in (a, b, c))
    v1, v2 = B.head_local - A.head_local, C.head_local - B.head_local
    h = rig.pose.bones[a].head.copy()
    l1, l2 = v1.length * stretch, v2.length * stretch
    u, d = (target - h).normalized(), (target - h).length
    assert d < l1 + l2, f"{a}: 닿지 않음 ({d:.3f} > {l1 + l2:.3f})"
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    joint = h + u * x + (pole - u * pole.dot(u)).normalized() * math.sqrt(l1 * l1 - x * x)
    put(rig, a, v1.rotation_difference(joint - h), h, stretch)
    put(rig, b, v2.rotation_difference(target - joint), joint, stretch)


def ride(rig, seat, foot, grips):
    """쉬는 자세 -> 탄 자세. 좌표는 아마추어 공간."""
    tilt = lambda a: Quaternion((1, 0, 0), math.radians(a))
    B = rig.data.bones
    hip = seat + Vector((0, HIP[0] - seat.y, HIP[1]))
    rest = (B["UpperLeg.L"].head_local + B["UpperLeg.R"].head_local) / 2
    q = tilt(LEAN[0])
    put(rig, "Body", q, hip - q @ (rest - B["Body"].head_local))
    put(rig, "Hips", q)
    for bone, a in zip(("Abdomen", "Torso", "Chest", "Neck", "Head"), LEAN[1:]):
        put(rig, bone, tilt(a))
    for side, sign in (("L", 1), ("R", -1)):
        put(rig, "Shoulder." + side, tilt(LEAN[3]) @ Quaternion((0, 0, 1), math.radians(-14 * sign)))  # 어깨를 앞으로 민다
        for n in ("LowerArm.", "Wrist."):
            B[n + side].inherit_scale = 'NONE'
        limb(rig, "UpperArm." + side, "LowerArm." + side, "Wrist." + side, grips[side], Vector((sign * 0.8, 0.2, -0.6)), ARM)
        q = (B["Middle2." + side].head_local - B["Wrist." + side].head_local).rotation_difference(Vector((0, -1, -0.1)))
        put(rig, "Wrist." + side, q, grips[side])
        for f in ("Index", "Middle", "Ring", "Pinky"):  # 주먹 쥐기. 토시 안에 들어간다
            for i, a in ((2, 60), (3, 120), (4, 160)):
                put(rig, f"{f}{i}.{side}", q @ Quaternion((0, sign, 0), math.radians(a)))
        at = foot + Vector((sign * 0.12, 0, 0))
        put(rig, "Foot." + side, Quaternion(), at)
        limb(rig, "UpperLeg." + side, "LowerLeg." + side, "Foot." + side, at, Vector((sign * 0.25, -1, 0.3)))


def helmet(D):
    """반모 헬멧. 쉬는 머리 둘레로 만들어 머리뼈 변환 D 로 옮긴다."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1, matrix=Matrix.LocRotScale((0, -0.04, 1.60), None, (0.112, 0.128, 0.135)))
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=(0, -0.05, 1.595), plane_no=(0, 0.35, 1), clear_inner=True)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1, matrix=Matrix.LocRotScale((0, -0.145, 1.635), Quaternion((1, 0, 0), 0.35), (0.085, 0.06, 0.008)))  # 챙
    me = bpy.data.meshes.new("x_helmet")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(k3d.mat("M_PH_Scooter_Helmet", (0.55, 0.04, 0.03), 0.3))
    o = bpy.data.objects.new("x_helmet", me)
    bpy.context.scene.collection.objects.link(o)
    k3d.smooth(o)
    o.matrix_world = D
    return o


def scooter():
    ph.load("Vehicles", "DeliveryScooter")
    O = bpy.data.objects
    src = [o for o in O if o.type == 'MESH']
    ys = [p.y for o in src for p in ph.world_verts(o)]
    s = SCOOTER_LEN / (max(ys) - min(ys))
    O["DeliveryScooter_Body"].matrix_world = Matrix.Scale(s, 4)
    bpy.context.view_layer.update()
    with bpy.data.libraries.load(os.path.join(k3d.SRC, "Blender", "Characters", "NpcYouth.blend")) as (a, b):
        b.objects = ["NpcYouth_Armature", "NpcYouth_Body", "NpcYouth_Head"]
    for o in b.objects:
        bpy.context.scene.collection.objects.link(o)
    rig = O["NpcYouth_Armature"]
    rig.matrix_world = Matrix.Scale(RIDER, 4)
    bpy.context.view_layer.update()
    inv = rig.matrix_world.inverted()
    at = lambda n, d=(0, 0, 0): inv @ (O["DeliveryScooter_Socket_" + n].matrix_world.translation + Vector(d))
    ride(rig, at("Seat"), at("Foot"), {"L": at("Grip_L", (-0.02, 0.085, 0)), "R": at("Grip_R", (0.02, 0.085, 0))})
    pb = rig.pose.bones["Head"]
    hat = helmet(rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted())
    box = ph.posed(O["DeliveryScooter_Box"])  # part 는 모디파이어를 버린다. 베벨을 굽는다
    parts = [o for o in src if o.name != "DeliveryScooter_Box"] + [box, ph.posed(O["NpcYouth_Body"]), ph.posed(O["NpcYouth_Head"]), hat]
    o = ph.part("PH_Scooter", parts, ph.turn(-90))
    for x in list(O):
        if x.name not in (o.name, "PH_Scooter_FrontMark"):
            O.remove(x)
    ph.finish("PH_Scooter", o, notes=f"DeliveryScooter 등배율 {s:.4f} + NpcYouth 라이더(배율 {RIDER}) + 헬멧. 앞 +X, 바퀴는 돌지 않는다.")
    k3d.preview("PH_Scooter", [o], views=((0, 4), (-90, 6), (90, 6), (-50, 18), (130, 18)), tag="ph")


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["car", "scooter"]
if "car" in args:
    car()
if "scooter" in args:
    scooter()

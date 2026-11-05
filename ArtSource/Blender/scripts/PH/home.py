"""PH 집 그룹: 신발, 지팡이, 현관문(문틀 + 문짝), 신발장, 전구.  인자로 함수 이름을 주면 그것만 다시 만든다.

Home 에셋은 프로토타입을 (-x3, z3, y3) 로 옮겨 만들었다 (다른 그룹의 (x3, -z3, y3) 와 180도 차이).
FBX -> Unity (-x, z, -y) 를 거치면 그대로 친구 프레임 (x3, y3, -z3) 이 되므로 전부 turn(0) 이 정답이다.
turn(180) 을 쓰면 복도 면이 플레이어 쪽으로 오고 경첩이 반대로 간다. 소스의 진짜 앞면: 문 = +Y, 신발장 문 = -X.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Home")]
import ph, hk, k3d, bpy, bmesh
from mathutils import Matrix

d2r = math.radians
HOME_NOTE = "좌표는 프리팹 로컬 (x3, y3, -z3) 그대로. "


def real_front(root, deg):
    """진짜 앞면이 소스 -Y 가 아닐 때: root 를 -deg 돌려 두고 ph.part(M=turn(deg)) 로 되돌린다.
    정점은 제자리, FrontMark 만 진짜 앞면에 놓인다."""
    root.matrix_world = ph.turn(-deg) @ root.matrix_world


def only(o):
    """결과물만 남긴다 (미리보기에 원본이 겹쳐 찍히지 않게)."""
    keep = set(k3d.tree_of([o]))
    for x in list(bpy.data.objects):
        if x not in keep:
            bpy.data.objects.remove(x, do_unlink=True)
    return o


def shoes():
    ph.load("Home", "HomeShoes")
    # 짝이 엇갈려 길이가 0.312 라 규격 상한(0.299)을 넘는다. 통째로 줄인다 (앞코 = 소스 -Y = 문 쪽 Unity +Z).
    o = only(ph.part("PH_ShoeRack__Shoes", [bpy.data.objects["HomeShoes"]], Matrix.Scale(0.94, 4)))
    ph.finish("PH_ShoeRack__Shoes", o, notes=HOME_NOTE + "앞코 +Z (문 쪽). 프로토타입 rotY 0.16 은 인스턴스에서 준다.")
    k3d.preview("PH_ShoeRack__Shoes", [o], tag="ph")


def cane():
    ph.load("Home", "HomeCane")
    o = only(ph.part("PH_Cane", [bpy.data.objects["HomeCane"]]))
    ph.finish("PH_Cane", o, notes=HOME_NOTE + "원점 = 고무 끝. 갈고리 +X (기대는 벽 쪽).")
    k3d.preview("PH_Cane", [o], tag="ph", res=(900, 1200))


# ---------------------------------------------------------------- 현관문
# 문짝은 소스 원점(경첩 핀)을 Hinge 축에 그대로 둔다: 로컬 x 0..0.92, 안쪽 면 z -0.05, 복도 면 z 0.
# 규격 깊이 0.12 안에서 그 자리에 맞도록 문틀은 HomeDoorFrame.py 를 치수만 바꿔 다시 짓는다.
OW, OH, FW, CW = 0.46, 2.04, 0.08, 0.03     # 열린 폭 절반, 높이, 문틀 면 폭(회색 1.08x2.12), 케이싱 폭
YC, YI, YS = -0.062, 0.066, 0.05            # 소스 y: 복도 면, 집 안쪽 면, 스톱 면(= 문짝 안쪽 면). Hinge 축은 y 0
SHOE_X, SHOE_Y = 0.25, 0.059                # 도어클로저 슈


def door_leaf():
    ph.load("Home", "HomeDoor")
    ob = bpy.data.objects
    # 문틀이 얕아져 슈가 문 쪽으로 왔다. 전완 끝(팔꿈치 -0.08 지점, y 0.09)을 슈까지 접는다.
    for v in ob["HomeDoor_CloserForearm"].data.vertices:
        v.co.y += min(v.co.x, 0.0) * (0.09 - SHOE_Y) / 0.08
    src = [ob[n] for n in ("HomeDoor", "HomeDoor_LeverIn", "HomeDoor_LeverOut", "HomeDoor_CloserArm", "HomeDoor_CloserForearm")]
    real_front(ob["HomeDoor"], 180)
    o = only(ph.part("PH_Door_Home__Leaf", src, ph.turn(180)))
    ph.finish("PH_Door_Home__Leaf", o, notes=HOME_NOTE + "원점 = 경첩 핀 = Hinge. 앞(레버, 전단지) -Z. 복도 쪽 +Z 로 열린다. 문턱 위로 띄워 min y 0.022 가 정상.")
    k3d.preview("PH_Door_Home__Leaf", [o], tag="ph", views=((180, 8), (20, 12)), res=(900, 1200))


def door_frame():
    k3d.reset()
    A = "PH_Door_Home__Frame"
    paint = hk.P("M_tmp_fpaint", "#685749", 0.45, var=0.05, vs=3, rv=0.05, grime=0.6, gd=0.03, gcol="#2a221c",
                 edge=0.8, ed=0.003, ecol="#a39a8c", erough=0.65, bump=0.04, bs=140, bd=0.0015, dust=0.6, dz=0.3,
                 dcol="#3b332b", smudge=0.15)
    stone = hk.P("M_tmp_granite", "#5c5a58", 0.35, var=0.25, vs=60, rv=0.1, grime=0.5, gd=0.02, gcol="#2a2826",
                 edge=0.5, ed=0.003, ecol="#8a8682", erough=0.5, bump=0.03, bs=400, bd=0.0005, smudge=0.2,
                 extra=lambda g, base, r, obj: (g.mix(g.ramp(g.voronoi(180, obj, out='Distance'), 0.0, 0.12),
                                                      (0.02, 0.02, 0.02), base), r))
    steel = hk.P("M_tmp_fsteel", "#b8b8ba", 0.3, 1.0, var=0.05, vs=30, grime=0.6, gd=0.01, gcol="#3a3a3a")
    rubber = hk.P("M_tmp_frubber", "#121212", 0.8, var=0.06, vs=30, dust=0.3, dz=0.2)
    parts = []
    # 기둥 2개 + 상부 틀: L 단면 (복도 쪽 = 문짝이 들어가는 홈, 안쪽 = 스톱)
    for sx in (1, -1):
        prof = [(OW, YC), (OW + FW, YC), (OW + FW, YI), (OW - 0.015, YI), (OW - 0.015, YS), (OW, YS)]
        prof = [(sx * x, y) for x, y in prof]
        parts.append(hk.poly_extrude(A + "_Jamb", prof if sx > 0 else prof[::-1], OH + FW - 0.001, paint, bev=0.003, seg=2))
    # 상부 틀은 기둥 사이에만 끼운다. 기둥과 겹치면 같은 면이 z-fight 하고 안쪽 AO 가 모서리에 밝은 마모 자국을 굽는다.
    prof = [(OH, YC), (OH + FW, YC), (OH + FW, YI), (OH - 0.015, YI), (OH - 0.015, YS), (OH, YS)]
    head = hk.poly_extrude(A + "_Head", [(y, z) for z, y in prof][::-1], 2 * (OW - 0.015) + 0.0004, paint, bev=0.003)
    head.rotation_euler = (d2r(90), 0, d2r(90))
    head.location = (-(OW - 0.015) - 0.0002, 0, 0)
    parts.append(head)
    # 안쪽 케이싱 날개 (벽 면보다 6mm 나와 벽과 겹쳐도 z-fight 없음)
    for sx in (1, -1):
        parts.append(hk.box(A + "_Casing", (CW, 0.012, OH + FW), (sx * (OW + FW + CW / 2), YI - 0.006, (OH + FW) / 2), mat=paint, bev=0.003))
    parts.append(hk.box(A + "_CasingTop", (2 * (OW + FW + CW), 0.012, CW), (0, YI - 0.006, OH + FW + CW / 2), mat=paint, bev=0.003))
    # 문턱: 기둥 사이에 끼운다
    parts.append(hk.box(A + "_Sill", (2 * OW + 0.02, YI - YC - 0.003, 0.02), (0, (YI + YC) / 2, 0.01), mat=stone, bev=0.004, seg=3))
    # 스톱 복도 쪽 면의 고무 개스킷
    for sx in (1, -1):
        parts.append(hk.box(A + "_Gasket", (0.009, 0.005, OH - 0.03), (sx * (OW - 0.006), YS - 0.0025, OH / 2 + 0.012), mat=rubber, bev=0.0015))
    parts.append(hk.box(A + "_GasketTop", (2 * OW - 0.02, 0.005, 0.009), (0, YS - 0.0025, OH - 0.006), mat=rubber, bev=0.0015))
    # 경첩 틀 쪽 너클: 소스 x +0.46 = Unity x -0.46 (Hinge), y 0 = 축
    for z in (0.25, 1.0, 1.75):
        for dz in (-0.008, 0.09):
            parts.append(hk.cyl(A + "_Hinge", 0.0095, 0.008, (OW, 0, z + dz), mat=steel, n=20, bev=0.0012))
        parts.append(hk.cyl(A + "_HingePin", 0.0098, 0.012, (OW, 0, z + 0.098), mat=steel, n=20, bev=0.002))
        parts.append(hk.box(A + "_HingePlate", (0.004, 0.035, 0.09), (OW + 0.002, 0.02, z + 0.045), mat=steel, bev=0.001))
    # 스트라이크 판 (래치 쪽, 문짝 두께 가운데)
    LY = YS / 2
    parts.append(hk.box(A + "_Strike", (0.003, 0.03, 0.26), (-OW + 0.0005, LY, 1.17), mat=steel, bev=0.001))
    for z in (1.03, 1.3):
        parts.append(hk.box(A + "_StrikeHole", (0.004, 0.014, 0.024), (-OW + 0.0002, LY, z), mat=rubber, bev=0.001))
    for z in (1.06, 1.27):
        parts.append(hk.cyl(A + "_Screw", 0.0028, 0.002, (-OW + 0.001, LY, z), rot=(0, d2r(-90), 0), mat=steel, n=10, bev=0.0004))
    # 도어클로저 슈: 상부 스톱 아래면
    parts.append(hk.box(A + "_CloserShoe", (0.06, 0.018, 0.02), (SHOE_X, SHOE_Y, OH - 0.025), mat=steel, bev=0.003))
    parts.append(hk.cyl(A + "_CloserPin", 0.005, 0.01, (SHOE_X, SHOE_Y, OH - 0.045), mat=steel, n=12, bev=0.001))
    src = hk.join(parts, "FrameSrc")
    k3d.set_origin(src, (0, 0, 0))
    k3d.bake(src, 1024, ao_distance=0.08, name=A)
    real_front(src, 180)
    o = only(ph.part(A, [src], ph.turn(180)))
    ph.finish(A, o, notes=HOME_NOTE + "원점 = 문 아래 중앙. Hinge(-0.46, 0, 0) 에 문짝 경첩 축이 온다. 앞(스톱) -Z, 복도 +Z.")
    k3d.preview(A, [o], tag="ph", views=((180, 8), (30, 15)), res=(900, 1200))


def cabinet():
    ph.load("Home", "HomeEntry")
    ob = bpy.data.objects
    # 잡동사니 중 높이 규격(1.168)을 넘는 라디오와 물컵은 뺀다. 전단지 더미와 열쇠 그릇만 남는다.
    cl = ob["HomeEntry_Clutter"]
    bm = bmesh.new()
    bm.from_mesh(cl.data)
    bmesh.ops.delete(bm, context='FACES', geom=[
        f for f in bm.faces
        if (cl.matrix_world @ f.calc_center_median()).y < -1.6 or cl.material_slots[f.material_index].name.startswith("M_Glass")])
    bm.to_mesh(cl.data)
    bm.free()
    src = [ob[n] for n in ("HomeEntry_ShoeCabinet", "HomeEntry_CabDoor0", "HomeEntry_CabDoor1", "HomeEntry_CabDoor2", "HomeEntry_Clutter")]
    real_front(ob["HomeEntry_Trim"], -90)
    # 원점 = 회색 상자 바닥 중앙 three(-0.8, -0.13, -1.54) = 소스 (0.8, -1.54, -0.13)
    o = only(ph.part("PH_ShoeCabinet", src, Matrix.Translation((-0.8, 1.54, 0.13)) @ ph.turn(-90)))
    for v in o.data.vertices:          # 벽에 묻히는 뒷면을 눌러 폭을 규격 상한(0.398) 안으로
        v.co.x = min(v.co.x, 0.176)
    o.data.update()
    k3d.select([o])
    bpy.ops.object.material_slot_remove_unused()
    ph.finish("PH_ShoeCabinet", o, notes=HOME_NOTE + "문 +X (프로토타입 -x3 벽에 붙어 방 쪽을 봄), 뒷면 -X 가 벽. 거울 문은 -Z 쪽, Reflection Probe 가 있어야 비친다.")
    k3d.preview("PH_ShoeCabinet", [o], tag="ph", views=((-60, 15), (120, 15)))


# ---------------------------------------------------------------- 전구 (새 에셋)
def bulb():
    k3d.reset()
    A = "PH_Bulb"
    RG, RN, ZN = 0.034, 0.0136, 0.096        # 유리 반지름, 목 반지름, 목 높이 (원점 = 유리 아래 끝)
    ZS, ZC, ZR = 0.104, 0.166, 0.38          # 소켓 아래, 소켓 위, 천장
    glass = hk.P("M_tmp_bulbglass", "#ffe9c4", 0.22, var=0.03, vs=30, rv=0.03, smudge=0.3, emis=(1.0, 0.54, 0.19), estr=1.8)
    g, p = hk.G(glass), k3d.principled(glass)
    dist = g.n('ShaderNodeVectorMath', operation='DISTANCE')    # 필라멘트에서 멀수록 주황, 목은 그을려 어둡게
    g.link(g.coord('Object'), dist.inputs[0])
    dist.inputs[1].default_value = (0, 0, 0.04)
    hot = g.mix(g.ramp(dist.outputs['Value'], 0.012, 0.05), (1.0, 0.82, 0.5), (1.0, 0.54, 0.19))
    g.link(g.mix(g.ramp(g.sep(g.coord('Object'))[2], 0.08, 0.096), hot, (0.3, 0.13, 0.04)), p.inputs['Emission Color'])
    brass = hk.P("M_tmp_brass", "#a88a52", 0.3, 1.0, var=0.12, vs=40, grime=0.8, gd=0.003, gcol="#3b2e1a", edge=0.6, ed=0.001,
                 ecol="#e0c690", erough=0.15)
    bakelite = hk.P("M_tmp_bakelite", "#2a1a12", 0.34, var=0.08, vs=14, rv=0.06, grime=0.7, gd=0.006, gcol="#0c0705", edge=0.6,
                    ed=0.0012, ecol="#6b4a34", erough=0.55, smudge=0.4)
    cord = hk.P("M_tmp_cord", "#3b2c20", 0.9, var=0.16, vs=220, rv=0.04, grime=0.6, gd=0.002, gcol="#120c08", bump=0.7, bs=2600,
                bk='cloth', bd=0.00018)
    rose = hk.P("M_tmp_rose", "#ddd5bf", 0.5, var=0.06, vs=40, grime=0.8, gd=0.006, gcol="#7d7258", edge=0.3, ed=0.0012,
                ecol="#f1ecdd", smudge=0.3,
                extra=lambda g, b, r, o: (g.mix(g.ramp(g.noise(60, 3, 0.5, o), 0.35, 0.75), b, hk.srgb("#cbb98d")), r))
    steel = hk.P("M_tmp_steel", "#a9a9a6", 0.35, 1.0, var=0.08, vs=60, grime=0.8, gd=0.002, gcol="#3a3a36")

    prof = [(RG * math.sin(a), RG * (1 - math.cos(a))) for a in [math.pi / 2 * k / 14 for k in range(15)]]
    for k in range(1, 15):                   # 어깨: 적도에서 목까지 코사인 곡선
        t = k / 14
        prof.append((RN + (RG - RN) * 0.5 * (1 + math.cos(math.pi * t)), RG + (ZN - RG) * t))
    parts = [hk.lathe(A + "_Glass", prof, 40, glass)]
    # 나사 꼭지 (E26 피치 3.6mm)
    screw = [(0.0128 + 0.0009 * (k % 2), ZN + 0.0018 * k) for k in range(10)]
    parts.append(hk.lathe(A + "_Screw", screw, 24, brass, close_top=True))
    # 베이클라이트 소켓: 안쪽 벽 -> 바닥 -> 톱니 조임 링 -> 몸통 -> 위 덮개
    sock = [(0.0138, ZS + 0.01), (0.0148, ZS), (0.0196, ZS), (0.0205, ZS + 0.0015), (0.0205, ZS + 0.016), (0.0194, ZS + 0.0175),
            (0.0182, ZS + 0.0185), (0.0186, ZS + 0.046), (0.0172, ZS + 0.052), (0.0115, ZS + 0.059), (0.0065, ZC - 0.0005), (0.0, ZC)]
    parts.append(hk.lathe(A + "_Socket", sock, 72, bakelite,
                          rmod=lambda th, z, r: r * (1 + 0.025 * math.cos(24 * th)) if ZS + 0.001 < z < ZS + 0.017 else r))
    parts.append(hk.lathe(A + "_Collar", [(0.0186, ZS + 0.0195), (0.0197, ZS + 0.0205), (0.0197, ZS + 0.0235), (0.0186, ZS + 0.0245)],
                          48, brass))
    # 천 씌운 두 가닥 꼬임선 (옛날 전등선)
    z0, z1, pitch = ZC - 0.003, 0.356, 0.024
    for s in (0.0, math.pi):
        pts = []
        for i in range(97):
            z = z0 + (z1 - z0) * i / 96
            a = s + 2 * math.pi * (z - z0) / pitch
            pts.append((0.0021 * math.cos(a), 0.0021 * math.sin(a), z))
        parts.append(hk.tube(A + "_Cord", pts, 0.0023, 8, cord))
    # 천장 로제트: 선 고정부 + 돔 + 나사 2개
    parts.append(hk.lathe(A + "_Grip", [(0.0052, 0.348), (0.0066, 0.350), (0.0084, 0.357), (0.0112, 0.362)], 32, rose))
    parts.append(hk.lathe(A + "_Rose", [(0.0, 0.3595), (0.012, 0.3595), (0.017, 0.3605), (0.026, 0.365), (0.0335, 0.3685), (0.0375, 0.37),
                                        (0.0392, 0.3725), (0.04, 0.375), (0.04, ZR)], 64, rose, close_top=True))
    for sx in (1, -1):
        parts.append(hk.cyl(A + "_RoseScrew", 0.0034, 0.0016, (sx * 0.0295, 0, 0.3672), rot=(0, d2r(180 - sx * 25), 0), mat=steel, n=14, bev=0.0005))
    src = hk.join(parts, "BulbSrc")
    k3d.set_origin(src, (0, 0, 0))
    k3d.smooth(src, 40)
    for s in src.material_slots:             # k3d 는 발광이 하나라도 있으면 모두의 Emission Color 를 굽는다 -> 비발광은 검정
        q = k3d.principled(s.material)
        if q.inputs['Emission Strength'].default_value <= 0:
            q.inputs['Emission Color'].default_value = (0, 0, 0, 1)
    k3d.bake(src, 1024, ao_distance=0.02, name=A)
    o = only(ph.part(A, [src], mark=False))
    ph.finish(A, o, notes=HOME_NOTE + "원점 = 유리 아래 끝, y 0.38 = 천장. 빛의 중심은 y 0.04 (프로토타입 필라멘트 자리). 깜빡임은 M_PH_Bulb Emission 조절.")
    k3d.preview(A, [o], tag="ph", views=((30, 5), (0, -35)), res=(900, 1200), ground=False)


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for f in (shoes, cane, door_leaf, door_frame, cabinet, bulb):
    if not args or f.__name__ in args:
        f()

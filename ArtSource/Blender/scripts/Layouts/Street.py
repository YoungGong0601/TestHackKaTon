# 거리(Street) 씬 배치: 스테이지 FBX 를 프로토타입 배치대로 놓고, 흐린 아침 조명 + 1인칭 렌더 + Unity 레이아웃 JSON 을 만든다.
# 좌표 = 과제 공식 Blender (x, y, z) = (x3, -z3, y3), three yaw a -> rotZ a. Unity 도구가 (-x, z, -y) 로 바꾼다.
# 골목은 y -11..31 로 +Y 로 뻗고(플레이어 시작 (0.3,-4.7)), 큰길은 X 방향: 앞 보도 y 31.02..35.2 (경계석 35.2),
# 차도 35.2..43.2 (노면 z=-0.14, 버스 차로 y=37 은 +X 진행), 건너편 보도 43.2..47.38.
# 먼저 StreetGround.py 를 실행해 둘 것 (Models/LayoutStreet/StreetGround.fbx).
import sys, os, math, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, k3d
from mathutils import Vector, Matrix

k3d.reset()
sc = bpy.context.scene
RZ = -0.14                    # 노면 높이 (프로토타입 zn)
ROAD_Y = 39.2                 # 차도 중심 (경계석 35.2 / 43.2)
BN, BF = 31.02, 47.38         # 앞/건너편 건물 정면 y
BUS = (31.75, 37.0)           # 버스 정차 위치 (프로토타입 Us, zr) -> 앞문 x = 36.2
SHELTER = (33.3, 32.8)        # 승차대 원점: BusDoor 소켓(로컬 y -2.4)이 경계석에 오게
items, cache = [], {}


def place(rel, x, y, z=0.0, rz=0.0, name=None, **extra):
    """FBX 를 (x,y,z), Z 회전 rz(deg) 에 놓는다. 같은 모델은 처음만 불러오고 그 뒤는 메시를 공유하는 복제."""
    if rel not in cache:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(k3d.ART, "Models", rel))
        root = next(o for o in bpy.data.objects if o not in before and o.parent is None)
        cache[rel] = (root, root.matrix_world.copy())
    else:
        src, _ = cache[rel]
        assert src.type != 'ARMATURE', rel          # 리그 모델은 한 번씩만 쓴다
        dup = {}
        for o in k3d.tree_of([src]):
            dup[o] = o.copy()
            sc.collection.objects.link(dup[o])
        for o, c in dup.items():
            if o.parent in dup:
                c.parent = dup[o.parent]
        root = dup[src]
    root.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rz), 4, 'Z') @ cache[rel][1]
    it = {"model": "Models/" + rel, "name": name or os.path.splitext(os.path.basename(rel))[0],
          "pos": [round(x, 3), round(y, 3), round(z, 3)], "rotZ": round(rz, 2), "scale": 1}
    it.update(extra)
    items.append(it)
    for o in k3d.tree_of([root]):                                   # hide = 이 배치에서 끌 자식 (렌더에서도 끔)
        o.hide_render = o.name.split(".")[0] in extra.get("hide", ())
    return root


def row(seq, x0, y, rz, gap=0.2):
    """건물을 x0 부터 +X 로 gap 간격 줄지어 놓는다. 폭은 로컬 X 범위(회전 180 이면 좌우가 뒤집힘)."""
    x = x0
    for rel, lo, hi in seq:
        w0, w1 = (-hi, -lo) if rz == 180 else (lo, hi)
        place(rel, x - w0, y, 0, rz)
        x += (w1 - w0) + gap
    return x


# ---------------------------------------------------------------- 도로 · 경계석 · 보도 · 골목
S = "Street/"
for cx in (-45.5, -33.5, -21.5, -9.5, 2.5, 14.5, 44.5, 56.5, 68.5, 80.5, 92.5, 104.5, 116.5, 128.5):
    place(S + "StreetRoad.fbx", cx, ROAD_Y, RZ)
place(S + "StreetRoadBusStop.fbx", 29.5, ROAD_Y, RZ)            # 정차대 x 21.5..37.5, '버스 정차' x=24.5 (버스 뒤)
for k in range(16):                                               # x -57.5 .. 134.5
    cx = -51.5 + 12 * k
    place(S + "StreetCurb.fbx", cx, ROAD_Y - 4, RZ, 180)         # 앞(정류장 쪽) 경계석: 앞면이 +Y(차도)
    place(S + "StreetCurb.fbx", cx, ROAD_Y + 4, RZ, 0)
    # 앞 보도는 회전 0: 유도 띠가 경계석에서 1.3~1.6 m (승차대 벤치 앞)로 온다. 180 이면 벤치 밑을 지난다.
    place(S + "StreetSidewalk.fbx", cx, ROAD_Y - 4 - 2.18, 0, 0)
    place(S + "StreetSidewalk.fbx", cx, ROAD_Y + 4 + 2.18, 0, 0)
for cy in (28, 22, 16, 10, 4, -2, -8):                            # 골목 6 m 모듈, 측구(로컬 +Y)가 -X 쪽
    place(S + "StreetRoadAlley.fbx", 0, cy, 0, 90, hide=[] if cy == 16 else ["StreetRoadAlley_TextSlow"])
    place(S + "StreetDrain.fbx", -2.43, cy, 0, 90)                # = StreetRoadAlley_Socket_Drain
for x in (-38, -18, 6, 18, 48, 62, 76):                           # 큰길 빗물받이: 경계석 앞면에서 0.17 m
    place(S + "StreetDrain.fbx", x, 35.37, RZ, 0)
    place(S + "StreetDrain.fbx", x + 5, 43.03, RZ, 180)
place(S + "StreetManhole.fbx", 0.7, 6.2, 0)
place(S + "StreetManhole.fbx", -1.0, 24.4, 0)
place(S + "StreetManhole.fbx", 8.0, 37.6, RZ)
place("LayoutStreet/StreetGround.fbx", 0, 0, 0)

# ---------------------------------------------------------------- 건물 (원점 = 정면 벽 아래 중앙, 정면 -Y)
B = "Buildings/"
VIL, SHOP, SAL, REA = ((B + "BuildingVilla.fbx", -6.197, 6.62), (B + "BuildingShopRow.fbx", -8.02, 7.535),
                       (B + "BuildingSalon.fbx", -5.785, 6.27), (B + "BuildingRealEstate.fbx", -6.52, 6.035))
# 앞줄(정면 +Y): 골목 왼쪽 모퉁이 빌라, 오른쪽 모퉁이 미용실, 정류장 뒤 약국·공인중개사 (프로토타입 17..29 / 29..44)
row([REA, SAL, VIL], -40.43, BN, 180)                             # x -40.43 .. -2.6
row([SAL, SHOP, REA, VIL, SHOP, SAL, REA, VIL, SAL], 2.6, BN, 180)  # x 2.6 .. 122
row([SAL, VIL, SHOP, REA, SAL, VIL, SHOP, REA, VIL, SAL, SHOP, REA, VIL], -46, BF, 0)  # x -46 .. 128
# 골목 양옆 (왼쪽 정면 +X = rotZ 90, 오른쪽 정면 -X = rotZ -90). 큰길 모퉁이 건물 뒤까지만.
place(VIL[0], -2.6, -6 + 6.197, 0, 90)                            # y -6 .. 6.82 (필로티 주차 3칸)
place(REA[0], -2.6, 7.0 + 6.52, 0, 90)                            # y 7.0 .. 19.56
place(SAL[0], 2.6, 3.05 - 5.785, 0, -90)                          # y -9.0 .. 3.05
place(SHOP[0], 2.6, 18.8 - 8.02, 0, -90)                          # y 3.25 .. 18.8
# 골목 끝(플레이어 등 뒤) 아파트 동 + 원경 아파트 (60 m 이상)
place(B + "BuildingBackdrop.fbx", 0, -10, 0, 180, name="BuildingBackdrop_Home")
for i, (x, y, rz) in enumerate(((-30, 112, 4), (25, 120, -3), (80, 108, 2), (135, 125, -5),
                                (-150, 39, 90), (175, 39, -90), (40, -75, 180), (-40, -80, 176))):
    place(B + "BuildingBackdrop.fbx", x, y, 0, rz, name=f"BuildingBackdrop_{i}")

# ---------------------------------------------------------------- 정류장 (승차대 소켓 기준, 회전 180 = 정면이 차도)
P = "BusStop/"
sx, sy = SHELTER
place(P + "BusShelter.fbx", sx, sy, 0, 180)
place(P + "BusStopBIS.fbx", sx - 4.7, sy + 0.3, 0, -90, socket="BusShelter_Socket_BIS")       # 표시면이 -X(다가오는 쪽)
place(P + "BusStopSign.fbx", sx + 4.3, sy + 1.55, 0, 180, socket="BusShelter_Socket_Sign")
place(P + "BusStopRouteMap.fbx", sx - 2.2, sy - 0.999, 0, 180, socket="BusShelter_Socket_RouteMap")

# ---------------------------------------------------------------- 거리 소품
for x in (-60, -35, -10, 15, 40, 65, 90, 115):                    # 전주 25 m 간격 (전선은 로컬 +X 25 m)
    place(S + "StreetUtilityPole.fbx", x, 34.75, 0, 0)
    if x < 115:
        place(S + "StreetWires.fbx", x, 34.75, 0, 0)
for x in (-22, 3, 53, 78, 103):
    place(S + "StreetLight.fbx", x, 34.85, 0, 180)                # 암이 차도(+Y) 쪽
for x in (-8, 17, 42, 67, 92, 117):
    place(S + "StreetLight.fbx", x, 43.55, 0, 0)
place(S + "StreetTrashCan.fbx", 22.5, 34.45, 0, 0)               # 프로토타입 (22.5, -34.45)
place(S + "StreetClothingBin.fbx", 19.0, 31.65, 0, 180)           # 세탁소 셔터 앞 (프로토타입 16.4)
place(S + "StreetNoParking.fbx", -1.9, 29.9, 0, 90)               # 골목 입구 모퉁이, 골목 쪽을 봄
place(S + "StreetBollard.fbx", 2.9, 34.7, 0, 0)                   # 골목 입구 양옆 (차 진입 표시)
place(S + "StreetBollard.fbx", -2.9, 34.7, 0, 0)

# ---------------------------------------------------------------- 차량 (실제 크기, 스케일 1)
V = "Vehicles/"
place(V + "CityBus.fbx", BUS[0], BUS[1], RZ, 90, name="CityBus_112")   # 정면 +X, 문(로컬 -X)이 보도 쪽
place(V + "CarHatch.fbx", 22.0, 42.1, RZ, -90)                     # 건너편 차로 갓길 주차 (프로토타입)
place(V + "CarSedan.fbx", -5.2, 0.197 - 3.9, 0, -90)               # 빌라 필로티 ParkingA (전면 주차)
place(V + "CarSedan.fbx", 1.6, 15.6, 0, 0)                         # 골목 거주자 주차
place(V + "CarHatch.fbx", 1.55, 6.4, 0, 180)
place(V + "DeliveryScooter.fbx", -1.9, 19.9, 0, 175)
place(V + "Bicycle.fbx", -2.15, 27.5, 0, 180)

# ---------------------------------------------------------------- 사람 (리그, Idle/Walk 첫 자세)
C = "Characters/"
npcs = [(C + "NpcStudentMan.fbx", 33.9, 33.75, 34.4, "Phone"),     # 프로토타입 student (yaw .6), 말 걸기 대상
        (C + "NpcAjumma.fbx", 7.4, 32.6, 180, "Idle"),             # 프로토타입 ajumma
        (C + "NpcYoungWoman.fbx", 20.0, 45.3, -90, "Walk"),         # 건너편 행인
        (C + "NpcOfficeMan.fbx", -6.0, 45.7, 90, "Walk"),
        (C + "NpcOldMan.fbx", 52.0, 45.0, 90, "Walk")]
for rel, x, y, rz, clip in npcs:
    arm = place(rel, x, y, 0, rz, clip=clip)
    # FBX 테이크가 아마추어 오브젝트 변환도 키로 가지고 있어 직접 옮기면 원점으로 돌아간다 -> 빈 부모로 옮김 (렌더 전용)
    holder = bpy.data.objects.new(arm.name + "_Place", None)
    sc.collection.objects.link(holder)
    holder.matrix_world = arm.matrix_world.copy()
    arm.parent, arm.matrix_parent_inverse, arm.matrix_basis = holder, Matrix(), Matrix()
    acts = [a for a in bpy.data.actions if a.name.startswith(arm.name + "|")]
    act = next((a for a in acts if a.name.endswith("|" + clip)), None) or next((a for a in acts if "Idle" in a.name), None)
    if act:
        arm.animation_data_create()
        arm.animation_data.action = act
        if hasattr(arm.animation_data, "action_slot") and act.slots:
            arm.animation_data.action_slot = act.slots[0]
    print("Street: npc", arm.name, act.name if act else None)
sc.frame_set(12)

# ---------------------------------------------------------------- 머티리얼 (FBX 는 텍스처 경로가 없음 -> <에셋>.json 으로 복원)
defs = {}
for rel in cache:
    js = os.path.join(k3d.ART, "Models", os.path.splitext(rel)[0] + ".json")
    defs.update({d["name"]: d for d in json.load(open(js))["materials"]})


def tex_node(nt, rel, non_color):
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(k3d.ART, rel), check_existing=True)
    t.image.alpha_mode = 'CHANNEL_PACKED'
    if non_color:
        t.image.colorspace_settings.name = 'Non-Color'
    return t


for m in bpy.data.materials:
    d = defs.get(m.name.split(".")[0])
    if not d:
        continue
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(p.outputs[0], nt.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    mp, bc = d.get("maps", {}), d.get("baseColor", [0.8, 0.8, 0.8, 1])
    p.inputs['Base Color'].default_value = (*bc[:3], 1)
    p.inputs['Metallic'].default_value = d.get("metallic", 0)
    p.inputs['Roughness'].default_value = 1 - d.get("smoothness", 0.5)
    p.inputs['Alpha'].default_value = bc[3]
    if "BaseColor" in mp:
        t = tex_node(nt, mp["BaseColor"], False)
        col = t.outputs['Color']
        if any(abs(c - 1) > 1e-3 for c in bc[:3]):                       # 타일 틴트 (linear 곱)
            vm = nt.nodes.new('ShaderNodeVectorMath')
            vm.operation, vm.inputs[1].default_value = 'MULTIPLY', bc[:3]
            nt.links.new(col, vm.inputs[0])
            col = vm.outputs[0]
        nt.links.new(col, p.inputs['Base Color'])
        if d.get("transparent") or d.get("alphaClip"):
            if bc[3] < 0.999:                                               # 텍스처 알파 x 머티리얼 알파
                mul = nt.nodes.new('ShaderNodeMath')
                mul.operation, mul.inputs[1].default_value = 'MULTIPLY', bc[3]
                nt.links.new(t.outputs['Alpha'], mul.inputs[0])
                nt.links.new(mul.outputs[0], p.inputs['Alpha'])
            else:
                nt.links.new(t.outputs['Alpha'], p.inputs['Alpha'])
    if "MS" in mp:                                                       # R 금속, A 스무스니스
        t = tex_node(nt, mp["MS"], True)
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(t.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Red'], p.inputs['Metallic'])
        inv = nt.nodes.new('ShaderNodeMath')
        inv.operation, inv.inputs[0].default_value = 'SUBTRACT', 1.0
        nt.links.new(t.outputs['Alpha'], inv.inputs[1])
        nt.links.new(inv.outputs[0], p.inputs['Roughness'])
    if "Normal" in mp:
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tex_node(nt, mp["Normal"], True).outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    if d.get("emissionStrength"):
        p.inputs['Emission Strength'].default_value = d["emissionStrength"]
        p.inputs['Emission Color'].default_value = (*d.get("emission", [1, 1, 1])[:3], 1)
        if "Emission" in mp:
            nt.links.new(tex_node(nt, mp["Emission"], False).outputs['Color'], p.inputs['Emission Color'])
    if (d.get("transparent") or d.get("alphaClip")) and hasattr(m, "use_transparent_shadow"):
        m.use_transparent_shadow = True
missing = sorted({m.name for o in bpy.data.objects if o.type == 'MESH' for m in o.data.materials
                  if m and m.name.split(".")[0] not in defs})
print("Street: 머티리얼 정의 없음", missing)

# ---------------------------------------------------------------- 조명: 흐린 아침 (프로토타입 is(DFE6EE, 1.15) + Hemisphere(C4CED8/5C5A56, .9))
lights = []


def lin(h):
    return [round(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4, 4) for i in (1, 3, 5)]


SUN_DIR = Vector((-2, 14, -42)).normalized()                             # 프로토타입 (18,42,-6) -> (16,0,-20)
sun_d = bpy.data.lights.new("Street_Sun", 'SUN')
sun_d.color, sun_d.energy, sun_d.angle = lin("#DFE6EE"), 3.2, math.radians(25)
sun = bpy.data.objects.new("Street_Sun", sun_d)
sc.collection.objects.link(sun)
sun.rotation_euler = SUN_DIR.to_track_quat('-Z', 'Y').to_euler()
lights.append({"name": "OvercastSun", "type": "Directional", "pos": [20, 30, 40], "dir": [round(v, 4) for v in SUN_DIR],
               "color": lin("#DFE6EE"), "intensity": 1.15, "range": 0, "spotAngle": 0})

w = bpy.data.worlds.new("Street_World")
sc.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (*lin("#C4CED8"), 1)                 # 흐린 하늘 = 앰비언트
bg.inputs['Strength'].default_value = 1.0

# ---------------------------------------------------------------- 1인칭 렌더 (눈높이 1.55 m, EEVEE)
sc.render.engine = k3d._engine_eevee()
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.view_settings.view_transform = 'AgX'
sc.eevee.taa_render_samples = 32
if hasattr(sc.eevee, "use_raytracing"):
    sc.eevee.use_raytracing = True
cd = bpy.data.cameras.new("Street_Cam")
cd.lens, cd.clip_start, cd.clip_end = 28, 0.05, 600
cam = bpy.data.objects.new("Street_Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
PV = os.path.join(k3d.SRC, "Previews")
os.makedirs(PV, exist_ok=True)
SHOTS = {1: ((23.4, 33.25, 1.55), (28.6, 33.1, 2.45), 28),           # 정류장 앞: 전광판(BIS) + 표지판
         2: ((13.0, 32.4, 1.55), (30.0, 35.6, 1.75), 28),            # 큰길 아래로: 정차한 112번 버스 + 승차대 (전주 x=15 뒤)
         3: ((0.3, -4.7, 1.55), (0.3, 30.0, 1.4), 28)}               # 시작점: 골목 끝에서 큰길 쪽
only = [int(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else list(SHOTS)   # "--" 만 = 렌더 없음
for n in only:
    loc, tgt, lens = SHOTS[n]
    cd.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(PV, f"Scene_Street_{n}.png")
    bpy.ops.render.render(write_still=True)
    print("Street: shot", sc.render.filepath)

# ---------------------------------------------------------------- Unity 레이아웃 JSON
bpy.context.view_layer.update()
anchors = {n: [round(v, 3) for v in bpy.data.objects[n].matrix_world.translation] for n in (
    "BusStopBIS_Socket_LookTarget", "BusStopBIS_Socket_LookTarget_Back", "BusStopSign_Socket_LookTarget_Routes",
    "BusStopSign_Socket_LookTarget_Head", "BusStopRouteMap_Socket_LookTarget", "BusShelter_Socket_Wait",
    "BusShelter_Socket_Sit_0", "BusShelter_Socket_Sit_1", "BusShelter_Socket_Sit_2", "BusShelter_Socket_LookTarget_Name",
    "CityBus_Socket_DoorFront", "CityBus_Socket_DoorMid", "BusShelter_Socket_BusDoor", "StreetRoadBusStop_Socket_BusStop")}
anchors.update({"Spawn": [0.3, -4.7, 0.0], "BusStopArrive": [23.0, 33.0, 0.0], "BusStopOrigin": [BUS[0], BUS[1], RZ],
                "BusEnter": [-90.0, BUS[1], RZ], "BusExit": [170.0, BUS[1], RZ]})
lay = {"scene": "Street",
       "notes": ("Blender 좌표 (Z-up, m), 과제 공식 (x3, -z3, y3) = 프로토타입 three 좌표. rotZ = Blender Z 회전(deg). "
                 "골목 y -11..31 (+Y 로 큰길), 앞 보도 y 31.02..35.2, 차도 35.2..43.2 (노면 z=-0.14, 중앙선 y=39.2), "
                 "건너편 보도 43.2..47.38. 버스: 차로 y=37 에서 +X 로 진행 (프로토타입 x -90 -> 31.75 정차 -> 170), "
                 "정차 시 원점 = anchors.BusStopOrigin, rotZ 90 (앞문 = anchors.CityBus_Socket_DoorFront). 건너편 차로 y=41.3 은 -X 진행. "
                 "BusShelter_Socket_BusDoor 와 StreetRoadBusStop_Socket_BusStop 은 이 배치에서 쓰지 않는다 (거기에 앞문을 맞추면 버스가 "
                 "4.5 m 뒤로 가서 '버스 정차' 글자를 덮는다). anchors = 배치 후 소켓·게임 지점의 월드 좌표 (Blender). "
                 "플레이어 정류장 도착 판정 x>23 & y>30 (프로토타입). "
                 "hide = 끌 자식 오브젝트(도구 미지원: StreetRoadAlley_TextSlow 는 y=16 모듈만 켬). socket = 원점을 맞춘 BusShelter 소켓. "
                 "앞 보도 StreetSidewalk 는 의도적으로 rotZ 0 (노트의 180 이면 선형 유도 띠가 승차대 벤치 밑을 지남). "
                 "NPC clip = 처음 재생할 클립. 하늘: 흐린 아침 C4CED8 근처, 안개 Exponential Squared 9AA3AB 밀도 0.0125 (프로토타입). "
                 "조명 color = linear (도구가 sRGB 로 바꿈)."),
       "items": items, "lights": lights, "anchors": anchors,
       "ambient": {"sky": lin("#C4CED8"), "ground": lin("#5C5A56"), "intensity": 0.9},
       "fog": {"color": lin("#9AA3AB"), "density": 0.0125},
       "camera": {"pos": [0.3, -4.7, 1.55], "lookAt": [0.3, 30.0, 1.4]}}
p = os.path.join(k3d.ART, "Layouts", "Street.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(lay, open(p, "w"), ensure_ascii=False, indent=1)
for it in items:                                                         # 모델 경로 확인
    assert os.path.exists(os.path.join(k3d.ART, it["model"])), it["model"]
print("Street: layout", p, len(items), "items")

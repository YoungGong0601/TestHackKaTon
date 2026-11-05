"""매장(Store) 씬 조립: 스테이징 FBX + JSON 머티리얼을 불러와 프로토타입 배치대로 놓고, 조명을 달고, 1인칭 렌더를 찍는다.
결과: Assets/Art3D/Layouts/Store.json (블렌더 좌표), ArtSource/Previews/Scene_Store_<n>.png
좌표: 프로토타입(three, Y-up) (x, y, z) -> 블렌더 (x, -z, y). three yaw a -> 블렌더 rotZ a. 에셋 정면 = -Y."""
import bpy, sys, os, json, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts')
import k3d
from mathutils import Vector, Matrix

ART = k3d.ART
FRAME = 12                      # 모든 클립을 같은 프레임으로 본다
ONLY = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []   # 렌더할 샷 번호만 (비면 전부)


def F(x, z, y=0.0):
    """프로토타입 바닥 좌표 (x, z) -> 블렌더."""
    return Vector((x, -z, y))


# ---------------------------------------------------------------- 머티리얼 (Unity JSON 그대로 재현)
_mats = {}


def jmat(d):
    if d["name"] in _mats:
        return _mats[d["name"]]
    m = bpy.data.materials.new(d["name"] + "_U")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    p = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    maps = d.get("maps", {})

    def tex(key, data=False):
        im = bpy.data.images.load(os.path.join(ART, maps[key]), check_existing=True)
        if data:
            im.colorspace_settings.name = 'Non-Color'
        im.alpha_mode = 'CHANNEL_PACKED'
        t = N.new('ShaderNodeTexImage')
        t.image = im
        return t

    def mul(a, b):
        n = N.new('ShaderNodeMath')
        n.operation = 'MULTIPLY'
        for i, v in enumerate((a, b)):
            L.new(v, n.inputs[i]) if not isinstance(v, float) else setattr(n.inputs[i], "default_value", v)
        return n.outputs[0]

    bc = d.get("baseColor", [0.8, 0.8, 0.8, 1])
    alpha = bc[3]
    if "BaseColor" in maps:
        t = tex("BaseColor")
        vm = N.new('ShaderNodeVectorMath')
        vm.operation = 'MULTIPLY'
        L.new(t.outputs['Color'], vm.inputs[0])
        vm.inputs[1].default_value = bc[:3]
        L.new(vm.outputs[0], p.inputs['Base Color'])
        alpha = mul(t.outputs['Alpha'], float(bc[3]))
    else:
        p.inputs['Base Color'].default_value = (*bc[:3], 1)
    if "MS" in maps:                                  # R 금속, A 스무스니스
        t = tex("MS", True)
        sp = N.new('ShaderNodeSeparateColor')
        L.new(t.outputs['Color'], sp.inputs[0])
        L.new(sp.outputs[0], p.inputs['Metallic'])
        inv = N.new('ShaderNodeMath')
        inv.operation = 'SUBTRACT'
        inv.inputs[0].default_value = 1.0
        L.new(mul(t.outputs['Alpha'], float(d.get("smoothness", 1))), inv.inputs[1])
        L.new(inv.outputs[0], p.inputs['Roughness'])
    else:
        p.inputs['Metallic'].default_value = d.get("metallic", 0)
        p.inputs['Roughness'].default_value = 1 - d.get("smoothness", 0.5)
    if "Normal" in maps:
        t = tex("Normal", True)
        nm = N.new('ShaderNodeNormalMap')
        L.new(t.outputs['Color'], nm.inputs['Color'])
        L.new(nm.outputs[0], p.inputs['Normal'])
    if d.get("emissionStrength", 0) > 0:
        ec = d.get("emission", [1, 1, 1])
        if "Emission" in maps:
            t = tex("Emission")
            vm = N.new('ShaderNodeVectorMath')
            vm.operation = 'MULTIPLY'
            L.new(t.outputs['Color'], vm.inputs[0])
            vm.inputs[1].default_value = ec
            L.new(vm.outputs[0], p.inputs['Emission Color'])
        else:
            p.inputs['Emission Color'].default_value = (*ec, 1)
        p.inputs['Emission Strength'].default_value = d["emissionStrength"]
    clip = d.get("alphaClip")
    if clip is not None:
        g = N.new('ShaderNodeMath')
        g.operation = 'GREATER_THAN'
        L.new(alpha, g.inputs[0]) if not isinstance(alpha, (int, float)) else None
        g.inputs[1].default_value = clip
        L.new(g.outputs[0], p.inputs['Alpha'])
    elif d.get("transparent"):
        L.new(alpha, p.inputs['Alpha']) if not isinstance(alpha, (int, float)) else setattr(
            p.inputs['Alpha'], "default_value", alpha)
        m.surface_render_method = 'BLENDED'
    m.use_backface_culling = not d.get("doubleSided", False)   # Unity URP Lit 기본 = 한 면
    _mats[d["name"]] = m
    return m


# ---------------------------------------------------------------- 배치
ITEMS, OBJS = [], {}


def place(model, name, pos, rz=0.0, clip=None):
    """FBX 를 불러와 (pos, rotZ deg) 에 둔다. clip = 리그 캐릭터의 애니메이션 이름."""
    path = os.path.join(ART, "Models", model)
    o0, a0 = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path, use_image_search=False)
    new = [o for o in bpy.data.objects if o not in o0]
    js = json.load(open(path[:-4] + ".json"))
    defs = {d["name"]: d for d in js["materials"]}
    for o in new:
        for s in getattr(o, "material_slots", []):
            if s.material and s.material.name.split(".")[0] in defs:
                s.material = jmat(defs[s.material.name.split(".")[0]])
    # 빈 부모로 옮긴다: 리그의 액션이 아마추어 오브젝트 변환을 덮어써도 배치가 유지된다 (Unity 프리팹 루트와 같음)
    root = bpy.data.objects.new(name, None)
    sc.collection.objects.link(root)
    root.matrix_world = Matrix.Translation(Vector(pos)) @ Matrix.Rotation(math.radians(rz), 4, 'Z')
    for o in new:
        if o.parent is None:
            o.parent = root
            o.matrix_parent_inverse = Matrix.Identity(4)
    new.append(root)
    it = {"model": "Models/" + model, "name": name, "pos": [round(v, 4) for v in pos], "rotZ": round(rz, 2), "scale": 1}
    if clip:
        arm = next(o for o in new if o.type == 'ARMATURE')
        act = next(a for a in bpy.data.actions if a not in a0 and a.name.split("|")[-1].split(".")[0] == clip)
        ad = arm.animation_data or arm.animation_data_create()
        ad.action = act
        if getattr(act, "slots", None):
            ad.action_slot = act.slots[0]
        it["clip"] = clip
        # npc_b 내장 폰은 폰 클립 때만 보인다 (게임 규칙과 같게)
        for o in new:
            if o.name.split(".")[0].endswith("_Phone") and "Phone" not in clip:
                o.hide_render = True
                it.setdefault("hide", []).append(o.name.split(".")[0])
    ITEMS.append(it)
    OBJS[name] = new
    bpy.context.view_layer.update()
    return new


def sock(name, suffix):
    return next(o for o in OBJS[name] if o.name.split(".")[0].endswith(suffix)).matrix_world.translation.copy()


def shift(name, d):
    root = next(o for o in OBJS[name] if o.parent is None)
    root.matrix_world = Matrix.Translation(d) @ root.matrix_world
    it = next(i for i in ITEMS if i["name"] == name)
    it["pos"] = [round(a + b, 4) for a, b in zip(it["pos"], d)]
    bpy.context.view_layer.update()


def sit(name, seat, rz, back=0.06, sink=0.025):
    """앉은 클립의 엉덩이 바닥을 좌판 윗면(seat)보다 sink m 아래(옷·살 눌림)에, 골반을 좌판 중심보다 back m 뒤에 맞춘다."""
    bpy.context.scene.frame_set(FRAME)
    arm = next(o for o in OBJS[name] if o.type == 'ARMATURE')
    hb = next((b for b in arm.pose.bones if b.name.lower() in ("hips", "pelvis")), arm.pose.bones[0])
    hip = arm.matrix_world @ hb.head
    dg = bpy.context.evaluated_depsgraph_get()
    low, feet = 9.0, 9.0
    for o in OBJS[name]:
        if o.type != 'MESH' or o.hide_render:
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            if (w.xy - hip.xy).length < 0.15:
                low = min(low, w.z)
            feet = min(feet, w.z)
        ev.to_mesh_clear()
    fwd = Vector((math.sin(math.radians(rz)), -math.cos(math.radians(rz)), 0))
    tgt = seat - fwd * back
    d = Vector((tgt.x - hip.x, tgt.y - hip.y, seat.z - sink - low))
    shift(name, d)
    print(f"store_layout: {name} 엉덩이 {low:.3f} -> 좌판 {seat.z:.3f}, 발 바닥 z={feet + d.z:.3f}")


def attach_phone(name, owner):
    """npc_a 손에 NpcSmartphone (렌더용. Unity 는 JSON attach 목록으로 붙인다)."""
    s = next(o for o in OBJS[owner] if o.name.split(".")[0].endswith("_Socket_PhoneGrip"))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ART, "Models/Characters/NpcSmartphone.fbx"), use_image_search=False)
    new = [o for o in bpy.data.objects if o not in before]
    defs = {d["name"]: d for d in json.load(open(os.path.join(ART, "Models/Characters/NpcSmartphone.json")))["materials"]}
    for o in new:
        for sl in getattr(o, "material_slots", []):
            if sl.material and sl.material.name.split(".")[0] in defs:
                sl.material = jmat(defs[sl.material.name.split(".")[0]])
    bpy.context.view_layer.update()
    for o in new:
        if o.parent is None:
            mw = o.matrix_world.copy()
            o.parent = s
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_basis = mw            # 소켓 로컬 = FBX 원래 변환 (localPosition/Rotation 0)
    ATTACH.append({"model": "Models/Characters/NpcSmartphone.fbx", "name": name, "to": owner,
                   "socket": s.name.split(".")[0]})


ATTACH = []
k3d.reset()
sc = bpy.context.scene
sc.frame_set(FRAME)

# ---- 건축 (매장 원점 그대로)
place("Store/StoreShell.fbx", "StoreShell", (0, 0, 0))
place("Store/StoreKitchen.fbx", "StoreKitchen", (0, 0, 0))
place("Store/StorePosters.fbx", "StorePosters", (0, 0, 0))
place("Store/StoreCounter.fbx", "StoreCounter", (-2.96, 1.25, 0), 90)
place("Store/StoreMenuBoard.fbx", "StoreMenuBoard", (-2.575, 1.98, 2.28), 90)
place("Store/StoreOrderBoard.fbx", "StoreOrderBoard", (-2.575, -0.9, 2.31), 90)
place("Storefront/StorefrontFacade.fbx", "StorefrontFacade", (0, -3.8, 0))
hinge = sock("StorefrontFacade", "_Socket_DoorHinge")
place("Storefront/StoreGlassDoor.fbx", "StoreGlassDoor", tuple(hinge))
for i in (1, 2, 3):
    place("Storefront/StorefrontAC.fbx", f"StorefrontAC_{i}", tuple(sock("StorefrontFacade", f"_Socket_AC_{i}")))

# ---- 키오스크 (pe.KX/K2X, KZ) 정면 = 매장 앞(-Y)
place("Kiosk/Kiosk.fbx", "Kiosk", F(-0.6, -3.82))
place("Kiosk/Kiosk_B.fbx", "Kiosk_B", F(0.72, -3.82))

def wall_y(x, z):
    """뒷벽(+Y) 실제 표면 y (타일·걸레받이 두께 포함)."""
    hit, loc, *_ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((x, 3.0, z)), Vector((0, 1, 0)))
    assert hit, (x, z)
    return loc.y


# ---- 홀 가구
TABLES = [(2.75, 1.7), (2.75, -1.1), (-3.4, 2.75)]                    # 2인 테이블 (프로토 x, z)
for i, (x, z) in enumerate(TABLES):
    place("Store/StoreTable.fbx", f"Table{i}", F(x, z), 180 if i == 1 else 0)   # Table1: 냅킨 모서리를 손님 쟁반 반대쪽으로
    place("Store/StoreChair.fbx", f"Table{i}_ChairBack", F(x, z - 0.62), 0)       # 프로토 rot 0
    place("Store/StoreChair.fbx", f"Table{i}_ChairFront", F(x, z + 0.62), 180)    # 프로토 rot PI
BOOTHS = [-1.95, 0.45, 2.65]
hit, loc, *_ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((5.3, 0.0, 0.05)), Vector((1, 0, 0)))
BX = loc.x - 0.4955 - 0.004                        # 프로토 x=5.0 이면 오른벽 걸레받이에 1 cm 박힘
for i, z in enumerate(BOOTHS):
    place("Store/StoreTable4.fbx", f"Booth{i}_Table", F(4.72, z), 90)
    place("Store/StoreBoothBench.fbx", f"Booth{i}_BenchBack", F(BX, z - 0.82), 0)
    place("Store/StoreBoothBench.fbx", f"Booth{i}_BenchFront", F(BX, z + 0.82), 180)
for t in [f"Table{i}" for i in range(3)] + [f"Booth{i}_Table" for i in range(3)]:
    n = sock(t, "_Socket_Napkin")
    rz = next(i for i in ITEMS if i["name"] == t)["rotZ"]
    place("Store/StoreNapkinDispenser.fbx", t + "_Napkin", tuple(n), rz)
    off = Matrix.Rotation(math.radians(rz), 3, 'Z') @ Vector((0.09, 0, 0))
    place("Store/StoreStrawHolder.fbx", t + "_Straw", tuple(n + off), rz)
place("Store/StoreHighChair.fbx", "HighChair0", F(-1.9, 3.1), math.degrees(0.6))
place("Store/StoreHighChair.fbx", "HighChair1", F(-2.5, 3.25), math.degrees(0.9))       # 프로토 -2.25 는 우리 의자(바닥 폭 0.45)끼리 겹침
place("Store/StorePlant.fbx", "Plant", F(-5.5, 3.3))
place("Store/StoreWetFloorSign.fbx", "WetFloorSign", F(0.35, 2.35), math.degrees(0.5))
place("Store/StoreTrashStation.fbx", "TrashStation", (2.75, wall_y(2.75, 0.08) - 0.265, 0))   # 프로토 쓰레기/트레이 카운터 자리, 걸레받이 앞
EXT_X = 1.68                                       # 프로토 x=-1.02 는 키오스크 발판 자리라 옮김
place("Store/StoreExtinguisherSign.fbx", "ExtinguisherSign", (EXT_X, wall_y(EXT_X, 1.05), 0.99))
place("Store/StoreExtinguisher.fbx", "Extinguisher", (EXT_X, wall_y(EXT_X, 0.08) - 0.15, 0))

# ---- 음식 (자리 앞 쟁반)
def tray(name, at, rz, burger="Food/FoodBurgerWrapped.fbx", cup="Food/FoodDrinkCup_Cola.fbx"):
    place("Food/FoodTray.fbx", name, tuple(at), rz)
    place(burger, name + "_Burger", tuple(sock(name, "_Socket_Burger")), rz + 8)
    place("Food/FoodFries.fbx", name + "_Fries", tuple(sock(name, "_Socket_Fries")), rz - 12)
    place(cup, name + "_Cup", tuple(sock(name, "_Socket_Cup")), rz + 30)


tray("Tray0", sock("Table0", "_Socket_ItemPlace") + Vector((0, -0.1, 0)), 183, burger="Food/FoodBulgogiBurger.fbx")
tray("Tray1", sock("Table1", "_Socket_ItemPlace") + Vector((0, 0.1, 0)), -4)
tray("Tray2", sock("Booth1_Table", "_Socket_ItemPlaceR"), 177, cup="Food/FoodDrinkCup_Cider.fbx")
tray("Tray3", sock("Booth0_Table", "_Socket_ItemPlaceL"), 3)

# ---- 사람
# 직원: 카운터 스툴(StaffSit)에 SitPhone, 프로토 rot PI/2+0.5
rz_staff = math.degrees(math.pi / 2 + 0.5)
place("Characters/NpcStaff.fbx", "Staff", (0, 0, 0), rz_staff, "SitPhone")
shift("Staff", sock("StoreCounter", "_Socket_StaffSit") - sock("Staff", "_Socket_Seat"))
place("Characters/NpcStaff.fbx", "Cook", F(-5, -1.4), -90, "Idle")                 # 주방, 튀김기 쪽(-X) 봄
# 줄 (Kr(i) = KX, KZ+2.05+0.82i), 키오스크(+Y) 를 봄
QUEUE = [("NpcYouth", "Impatient"), ("NpcAjumma", "Watch"), ("NpcYoungWoman", "Phone"), ("NpcOfficeMan", "Idle")]
for i, (npc, clip) in enumerate(QUEUE):
    place(f"Characters/{npc}.fbx", f"Queue{i}_{npc}", F(-0.6 + (0.0, 0.14, -0.06, 0.2)[i], -3.82 + 2.05 + 0.82 * i), 180 + (4, -9, 6, -3)[i], clip)
attach_phone("Queue2_Phone", "Queue2_NpcYoungWoman")
# 픽업 대기 (m0), 주문번호판(pe.BOARD) 을 봄
board = F(-2.72, 0.9)
for (x, z), (npc, clip) in zip([(-1.72, -0.25), (-1.82, 0.95)], [("NpcSuitMan", "Phone"), ("NpcStudentMan", "Watch")]):
    p = F(x, z)
    d = board - p
    place(f"Characters/{npc}.fbx", f"Wait_{npc}", p, math.degrees(math.atan2(d.x, -d.y)), clip)
# 앉은 손님
place("Characters/NpcStudentWoman.fbx", "Seat_NpcStudentWoman", F(2.75, 2.32), 180, "SitIdle")
sit("Seat_NpcStudentWoman", sock("Table0_ChairFront", "_Socket_Sit"), 180)
place("Characters/NpcOldMan.fbx", "Seat_NpcOldMan", F(2.75, -1.72), 0, "SitIdle")
sit("Seat_NpcOldMan", sock("Table1_ChairBack", "_Socket_Sit"), 0)

# ---- 바깥 거리 (유리 너머로 보이는 것: 보도·도로·건너편 상가)
for i, x in enumerate((-12, 0, 12)):
    place("Street/StreetSidewalk.fbx", f"Sidewalk{i}", (x, -5.8, 0))
    place("Street/StreetCurb.fbx", f"Curb{i}", (x, -7.98, -0.14))
    place("Street/StreetRoad.fbx", f"Road{i}", (x, -11.98, -0.14))
    place("Street/StreetCurb.fbx", f"CurbFar{i}", (x, -15.98, -0.14), 180)
    place("Street/StreetSidewalk.fbx", f"SidewalkFar{i}", (x, -18.16, 0), 180)
for i, x in enumerate((-15.2, 0.0, 15.2)):
    place("Buildings/BuildingShopRow.fbx", f"ShopRow{i}", (x, -20.25, 0), 180)
place("Buildings/BuildingBackdrop.fbx", "Backdrop0", (-6, -85, 0), 180)
place("Street/StreetLight.fbx", "StreetLight0", (4.6, -7.45, 0))

# ---------------------------------------------------------------- 조명 (Unity URP 값 + 렌더용 블렌더 값)
P_COOL, P_WARM = (0.92, 0.96, 1.0), (1.0, 0.93, 0.84)
POINTS = [  # (이름, 위치, 색, URP 세기, 범위)  StoreShell_Socket_Light_* + 키오스크·입구·카운터 보강
    ("Light_A", sock("StoreShell", "_Socket_Light_A"), P_COOL, 2.4, 7.5),
    ("Light_B", sock("StoreShell", "_Socket_Light_B"), P_COOL, 2.4, 7.5),
    ("Light_C", sock("StoreShell", "_Socket_Light_C"), P_COOL, 2.2, 7.0),
    ("Light_Kitchen", sock("StoreShell", "_Socket_Light_Kitchen"), P_WARM, 2.6, 6.0),
    ("Light_Kiosk", Vector((-0.6, 2.6, 2.8)), P_COOL, 1.6, 5.0),
    ("Light_Counter", Vector((-1.9, 1.2, 2.8)), P_COOL, 1.6, 5.0),
    ("Light_Entrance", Vector((1.3, -2.6, 2.8)), P_COOL, 1.4, 5.0),
]
SPOT = ("Light_PickupHeat", sock("StoreCounter", "_Socket_PickupCall") + Vector((0, 0, 0.38)), (1.0, 0.72, 0.46), 2.5, 3.0, 75)
SUN = {"dir": Vector((0.25, 0.55, -0.8)).normalized(), "color": (0.9, 0.94, 1.0), "intensity": 1.0}

LIGHTS = [{"type": "Directional", "name": "OvercastSun", "pos": [0, -12, 12], "dir": [round(v, 3) for v in SUN["dir"]],
           "color": list(SUN["color"]), "intensity": SUN["intensity"], "shadows": True}]
for n, p, c, inten, rng in POINTS:
    LIGHTS.append({"type": "Point", "name": n, "pos": [round(v, 3) for v in p], "color": list(c), "intensity": inten,
                   "range": rng, "shadows": n in ("Light_A", "Light_B", "Light_C", "Light_Kitchen")})
LIGHTS.append({"type": "Spot", "name": SPOT[0], "pos": [round(v, 3) for v in SPOT[1]], "dir": [0, 0, -1],
               "color": list(SPOT[2]), "intensity": SPOT[3], "range": SPOT[4], "spotAngle": SPOT[5]})


def light(kind, loc, energy, color, size=None, aim=None, name="L"):
    ld = bpy.data.lights.new(name, kind)
    ld.energy, ld.color = energy, color
    if kind == 'AREA':
        ld.shape, ld.size, ld.size_y = 'RECTANGLE', size[0], size[1]
    if kind == 'SPOT':
        ld.spot_size, ld.spot_blend = math.radians(size), 0.4
    if kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = 0.15
    lo = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo)
    lo.location = loc
    if aim is not None:
        lo.rotation_euler = Vector(aim).to_track_quat('-Z', 'Y').to_euler()
    return lo


# 천장 평판등 아래 면광원 (Unity 는 발광 패널 + 위 포인트 라이트가 맡음)
PANELS = [(x, y, 1.15, 0.55) for x in (-1.8, 1.2, 3.6) for y in (3.0, 0.6, -1.8)] + [(-4.5, y, 0.55, 1.15) for y in (3.3, 1.5, -0.9)]
for x, y, w, h in PANELS:
    light('AREA', (x, y, 3.07), 45 if x > -4 else 40, P_COOL if x > -4 else P_WARM, (w, h), (0, 0, -1), "Panel")
for n, p, c, inten, rng in POINTS:
    if n != "Light_Kiosk":                         # 렌더에선 면광원이 이미 키오스크를 비춰 과노출됨
        light('POINT', p, inten * 12, c, name=n)
light('SPOT', SPOT[1], 60, SPOT[2], SPOT[5], (0, 0, -1), SPOT[0])
light('SUN', (0, -12, 12), 2.2, SUN["color"], aim=SUN["dir"], name="Sun")
light('AREA', (0.4, -6.5, 2.4), 900, (0.85, 0.9, 1.0), (11, 2.5), (0, 1, -0.25), "SkyFill")   # 흐린 하늘 반사광

w = bpy.data.worlds.new("overcast")
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.72, 0.77, 0.84, 1)
bg.inputs['Strength'].default_value = 0.6
sc.world = w

# ---------------------------------------------------------------- 겹침 검사 (배치가 만드는 관통)
def overlaps():
    import bmesh
    from mathutils.bvhtree import BVHTree
    skip = ("StoreShell", "StorefrontFacade", "StorefrontAC", "StoreGlassDoor", "Sidewalk", "Curb", "Road", "ShopRow",
            "Backdrop", "StreetLight", "Staff", "Cook", "Queue", "Wait_", "Seat_")
    dg = bpy.context.evaluated_depsgraph_get()
    trees = []
    for name, objs in OBJS.items():
        if name.startswith(skip) and name != "StoreShell":
            continue
        for o in objs:
            if o.type != 'MESH' or (name == "StoreShell" and not o.name.startswith("StoreShell_Fixtures")):
                continue
            bm = bmesh.new()
            bm.from_object(o, dg)
            bm.transform(o.matrix_world)
            mn = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
            mx = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
            trees.append((name, o.name, BVHTree.FromBMesh(bm), mn, mx, [f.calc_center_median().copy() for f in bm.faces]))
            bm.free()
    for i, (na, oa, ta, mna, mxa, _) in enumerate(trees):
        for nb, ob, tb, mnb, mxb, cb in trees[i + 1:]:
            if na == nb or any(mna[k] > mxb[k] or mnb[k] > mxa[k] for k in range(3)):
                continue
            ov = ta.overlap(tb)
            if ov:
                pts = [cb[j] for _, j in ov]
                lo = [round(min(p[k] for p in pts), 3) for k in range(3)]
                hi = [round(max(p[k] for p in pts), 3) for k in range(3)]
                print(f"store_layout: 겹침 {oa} x {ob} = {len(ov)}  범위 {lo}..{hi}")


overlaps()

# ---------------------------------------------------------------- 레이아웃 JSON
CAM = {"pos": [1.4, -3.1, 1.55], "lookAt": [-0.6, 3.82, 1.4]}       # 프로토 al(입구 안쪽)에서 키오스크를 봄
out = os.path.join(ART, "Layouts", "Store.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
for it in ITEMS:
    assert os.path.exists(os.path.join(ART, it["model"])), it["model"]
NOTES = ("Blender 좌표 (Z-up, m), 매장 원점 = 프로토타입 매장 원점. 프로토타입 three (x,y,z) -> Blender (x,-z,y) -> Unity (-x,y,z). "
         "rotZ = Blender Z 회전(deg), 모든 에셋 정면 = -Y. 조명 color = sRGB. "
         "clip = 캐릭터 기본 애니메이션 (Unity 테이크 '<Rig>|<clip>'). 앉은 사람(Staff=SitPhone, Seat_*=SitIdle)의 pos 는 그 클립 자세 기준으로 "
         "좌판에 맞춘 값이라 클립 없이 두면 의자에 박힌다. hide = 처음에 끌 자식 오브젝트(npc_b 내장 폰은 Phone 계열 클립 때만 켬). "
         "attach = 소켓에 붙일 소품 (NpcSmartphone 을 to 오브젝트의 socket 자식으로, localPosition/Rotation 0). "
         "줄(Queue0~3)·픽업 대기(Wait_*) 는 프로토타입 Kr(i)·m0 자리이고 게임이 나중에 들여보내는 손님이면 이 자리를 목표점으로 쓰면 됨. "
         "실내 조명은 천장 발광 패널(StoreShell_LightPanels) + 포인트 7개라 URP Forward+ 또는 오브젝트당 추가 조명 8개가 필요. "
         "Light_PickupHeat 는 StoreCounter_PickupLamp 아래 따뜻한 스폿. 미리보기 렌더는 천장 면광원 12개를 더 썼으므로 Unity 와 밝기 분포가 다를 수 있음.")
json.dump({"scene": "Store", "notes": NOTES, "items": ITEMS, "attach": ATTACH, "lights": LIGHTS, "camera": CAM},
          open(out, "w"), ensure_ascii=False, indent=1)
print("store_layout: json", out, len(ITEMS), "items")

# ---------------------------------------------------------------- 1인칭 렌더 (눈높이 1.55 m)
sc.render.engine = k3d._engine_eevee()
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.eevee.taa_render_samples = 48
sc.eevee.use_raytracing = True
sc.eevee.use_shadows = True
sc.eevee.shadow_pool_size = '1024'
sc.eevee.shadow_resolution_scale = 0.5
cd = bpy.data.cameras.new("cam")
cd.clip_start, cd.clip_end = 0.03, 400
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
k = sock("Kiosk", "_Socket_ScreenCenter")
stand = F(-0.6, -3.82 + 0.74, 1.55)                                    # 프로토 zs (키오스크 앞 0.74 m)
SHOTS = [  # (번호, 카메라, 목표, 렌즈, 해상도)
    (1, stand + Vector((0, -0.06, 0)), k, 24, (1440, 1080)),           # 키오스크 화면 (눈~화면 0.73 m)
    (2, stand + Vector((-0.35, -0.1, 0)), Vector((-0.2, -1.2, 1.3)), 28, (1600, 1000)),  # 뒤돌아 줄을 봄
    (3, F(-1.2, -1.2, 1.55), Vector((-3.6, 2.4, 1.25)), 28, (1600, 1000)),             # 카운터와 직원
    (4, Vector(CAM["pos"]), Vector(CAM["lookAt"]), 24, (1600, 1000)),                 # 입구에서 본 매장
]
pdir = os.path.join(k3d.SRC, "Previews")
os.makedirs(pdir, exist_ok=True)
for n, c, t, lens, res in SHOTS:
    if ONLY and str(n) not in ONLY:
        continue
    cd.lens = lens
    cam.location = c
    cam.rotation_euler = (Vector(t) - Vector(c)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(pdir, f"Scene_Store_{n}.png")
    bpy.ops.render.render(write_still=True)
    print("store_layout: shot", sc.render.filepath)

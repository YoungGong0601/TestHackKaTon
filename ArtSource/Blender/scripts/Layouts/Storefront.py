"""매장 앞(Storefront) 씬 조립: 스테이징 FBX + JSON 머티리얼을 프로토타입 배치대로 놓고, 조명을 달고, 1인칭 렌더를 찍는다.
결과: Assets/Art3D/Layouts/Storefront.json (블렌더 좌표), ArtSource/Previews/Scene_Storefront_<n>.png
좌표: 프로토타입(three, Y-up) (x, y, z) -> 블렌더 (x, -z, y). three yaw a -> 블렌더 rotZ a. 에셋 정면 = -Y.
매장 안과 매장 앞 거리는 Layouts/Store.json 을 그대로 읽어 같은 자리에 둔다 (씬이 넘어갈 때 이어지게). 먼저 Store.py 를 실행해 둘 것.
보도는 4.18 m 다 (프로토타입 5.8 m). 경계석 앞면 y=-7.98, 도로 중심 y=-11.98 (z=-0.14)."""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d
from mathutils import Vector, Matrix

ART = k3d.ART
FRAME = 12                      # 모든 클립을 같은 프레임으로 본다 (Store.py 와 같음)
ONLY = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []   # 렌더할 샷 번호만 (비면 전부)


# ---------------------------------------------------------------- 머티리얼 (Unity JSON 그대로 재현, Store.py 와 같은 코드)
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


def place(model, name, pos, rz=0.0, clip=None, hide=()):
    """FBX 를 불러와 빈 부모(name) 아래 (pos, rotZ deg) 에 둔다. clip = 리그 캐릭터 클립, hide = 끌 자식 오브젝트 이름."""
    path = os.path.join(ART, "Models", model)
    o0, a0 = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path, use_image_search=False)
    new = [o for o in bpy.data.objects if o not in o0]
    defs = {d["name"]: d for d in json.load(open(path[:-4] + ".json"))["materials"]}
    for o in new:
        for s in getattr(o, "material_slots", []):
            if s.material and s.material.name.split(".")[0] in defs:
                s.material = jmat(defs[s.material.name.split(".")[0]])
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
        for o in new:                                 # 내장 폰은 폰 클립 때만 보인다
            if o.name.split(".")[0].endswith("_Phone") and "Phone" not in clip:
                o.hide_render = True
    for o in new:
        if o.name.split(".")[0] in hide:
            o.hide_render = True
    if hide:
        it["hide"] = list(hide)
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


def span_x(name):
    """건물 옆벽(±X 를 보는 큰 면)의 월드 X 범위. 옆벽이 없으면 메시 전체 범위.
    전체 범위를 쓰면 옆으로 나온 선홈통·입상관(약 0.5 m) 때문에 벽 사이가 벌어진다."""
    xs, alls = [], []
    for o in OBJS[name]:
        if o.type != 'MESH':
            continue
        mw, r = o.matrix_world, o.matrix_world.to_3x3()
        alls += [(mw @ Vector(c)).x for c in o.bound_box]
        xs += [(mw @ q.center).x for q in o.data.polygons if q.area > 3.0 and abs((r @ q.normal).normalized().x) > 0.95]
    return (min(xs), max(xs)) if xs else (min(alls), max(alls))


def snap(model, name, x_edge, side, y=-3.8, rz=0.0, hide=()):
    """건물 옆벽을 x_edge 에 붙인다. side=+1 이면 왼쪽 끝(min x)을, -1 이면 오른쪽 끝(max x)을 맞춘다."""
    place(model, name, (0, y, 0), rz, hide=hide)
    lo, hi = span_x(name)
    shift(name, Vector(((x_edge - lo) if side > 0 else (x_edge - hi), 0, 0)))
    return span_x(name)


k3d.reset()
sc = bpy.context.scene
sc.frame_set(FRAME)

# ---- 매장 안 + 매장 앞 거리 = Store.json 그대로. 프로토타입 매장 앞 씬의 사람은 앉은 직원(폰)과 앉은 여자 손님뿐이다.
SKIP = ("Queue", "Wait_", "Cook", "Seat_NpcOldMan", "Tray1", "Tray2", "Tray3")
store = json.load(open(os.path.join(ART, "Layouts", "Store.json")))
for it in store["items"]:
    if not it["name"].startswith(SKIP):
        place(it["model"][len("Models/"):], it["name"], tuple(it["pos"]), it["rotZ"], it.get("clip"), tuple(it.get("hide", ())))

# ---- 거리 연장 (Store.json 은 x -18~18): 플레이어 벽 x ±11, 안개 34 m 라서 ±42 까지 깐다
for tag, x in (("W1", -24), ("W2", -36), ("E1", 24), ("E2", 36)):
    place("Street/StreetSidewalk.fbx", f"Sidewalk{tag}", (x, -5.8, 0))
    place("Street/StreetCurb.fbx", f"Curb{tag}", (x, -7.98, -0.14))
    place("Street/StreetRoad.fbx", f"Road{tag}", (x, -11.98, -0.14))
    place("Street/StreetCurb.fbx", f"CurbFar{tag}", (x, -15.98, -0.14), 180)
    place("Street/StreetSidewalk.fbx", f"SidewalkFar{tag}", (x, -18.16, 0), 180)

# ---- 이웃 건물 (같은 줄, 정면 -Y). 왼쪽: 미용실 | 시장 골목 5.2 m (게이트) | 빌라. 오른쪽: 부동산·약국 | 상가.
FX = 9.52                                                    # 파사드 벽 끝 x (WallTile/WallGranite 범위, 옆면 없음)
lo, _ = snap("Buildings/BuildingSalon.fbx", "NeighborSalon", -FX, -1)
alley_r = lo
alley_l = alley_r - 5.2
snap("Buildings/BuildingVilla.fbx", "NeighborVilla", alley_l, -1)
_, hi = snap("Buildings/BuildingRealEstate.fbx", "NeighborRealEstate", FX, +1)
snap("Buildings/BuildingShopRow.fbx", "NeighborShopRow", hi, +1)
# 시장 골목: 게이트(프로토타입 큰길시장, 간판이 거리 쪽) + 골목 바닥 2칸 + 골목 끝 상가
gx = (alley_l + alley_r) / 2
place("Buildings/BuildingMarketGate.fbx", "MarketGate", (gx, -4.15, 0))
for i, y in enumerate((-0.8, 5.2)):
    place("Street/StreetRoadAlley.fbx", f"MarketAlley{i}", (gx, y, 0), 90,
          hide=("StreetRoadAlley_Parking", "StreetRoadAlley_TextSlow"))
place("Buildings/BuildingShopRow.fbx", "MarketAlleyEnd", (gx, 8.2, 0))

# ---- 건너편 끝 + 먼 아파트 (Store.json 에 ShopRow0~2, Backdrop0 이 있다)
lo, _ = span_x("ShopRow0")
snap("Buildings/BuildingSalon.fbx", "FarSalon", lo, -1, y=-20.25, rz=180)
_, hi = span_x("ShopRow2")
snap("Buildings/BuildingRealEstate.fbx", "FarRealEstate", hi, +1, y=-20.25, rz=180)
for i, (x, y, rz) in enumerate(((-30, 72, 4), (22, 86, -6), (48, -96, 186))):
    place("Buildings/BuildingBackdrop.fbx", f"Backdrop{i + 1}", (x, y, 0), rz)

# ---- 보도 소품 (프로토타입 sh(): 경계석 쪽은 경계석 뒷면 y=-7.8 기준, 가게 쪽은 유리선 y=-3.8 기준으로 옮김)
for i, x in enumerate((13.6, -11.4, -36.4)):                 # 전주 (전단지 면이 보도 쪽), 전선은 로컬 +X = 월드 -X 로 25 m
    place("Street/StreetUtilityPole.fbx", f"UtilityPole{i}", (x, -7.6, 0), 180)   # y -7.6: 가로등(4.6,-7.45) 기둥과 전선 0.4 m 띄움
    if i < 2:
        place("Street/StreetWires.fbx", f"Wires{i}", (x, -7.6, 0), 180)
place("Street/StreetSignPole.fbx", "SignPole", (-4.3, -7.4, 0), 180)    # '시장 입구 →' 가 보도 쪽, 화살표가 시장(-X)
place("Street/StreetTrashCan.fbx", "TrashCan", (-8.4, -7.35, 0), 180)
place("Vehicles/Bicycle.fbx", "Bicycle", (-5.2, -5.0, 0), math.degrees(math.pi / 2.2))
scoot = place("Vehicles/DeliveryScooter.fbx", "DeliveryScooter", (4.35, -5.45, 0), -18)
stand = next(o for o in scoot if o.name.split(".")[0] == "DeliveryScooter_Stand")
stand.rotation_euler.x = math.radians(-70.0)                 # 주차 스탠드 (JSON notes)
ITEMS[-1]["parts"] = {"DeliveryScooter_Stand": {"rotX": -70.0}}
for i, x in enumerate((-2.0, 19.0)):                         # 빗물받이: 경계석 앞면에서 0.17 m
    place("Street/StreetDrain.fbx", f"Drain{i}", (x, -8.15, -0.14))
# 차: 매장 쪽 차로는 우측통행이라 -X 로 간다 (rotZ -90). 버스 문(로컬 -X)이 보도 쪽.
bus = place("Vehicles/CityBus.fbx", "Bus", (-6.0, -9.6, -0.14), -90)
car = place("Vehicles/CarSedan.fbx", "ParkedCar", (11.5, -9.1, -0.14), -90)

# ---------------------------------------------------------------- 조명 (Unity URP 값 + 렌더용 블렌더 값)
SUN_DIR = Vector((6, 10, -16)).normalized()                  # 프로토 g: (-7,16,15) -> (-1,0,5)
LIGHTS = [{"type": "Directional", "name": "OvercastSun", "pos": [-7, -15, 16], "dir": [round(v, 3) for v in SUN_DIR],
           "color": [0.941, 0.925, 0.894], "intensity": 1.2, "shadows": True}]
LIGHTS += [l for l in store["lights"] if l["type"] != "Directional"]          # 매장 안 (Store.json 과 같은 값)
canopy = sock("StorefrontFacade", "_Socket_CanopyLight")
LIGHTS.append({"type": "Point", "name": "CanopyWarm", "pos": [round(v, 3) for v in canopy],
               "color": [1.0, 0.851, 0.659], "intensity": 2.2, "range": 5.0})


def light(kind, loc, energy, color, size=None, aim=None, name="L"):
    ld = bpy.data.lights.new(name, kind)
    ld.energy, ld.color = energy, color
    if kind == 'AREA':
        ld.shape, ld.size, ld.size_y = 'RECTANGLE', size[0], size[1]
    if kind == 'SUN':
        ld.angle = math.radians(12)
    if kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = 0.15
    ld.use_shadow = kind == 'SUN' or name == "CanopyWarm"     # 렌더 전용: 매장 안 조명 그림자는 끔 (EEVEE 그림자 풀 초과 방지)
    lo = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo)
    lo.location = loc
    if aim is not None:
        lo.rotation_euler = Vector(aim).to_track_quat('-Z', 'Y').to_euler()
    return lo


P_COOL, P_WARM = (0.92, 0.96, 1.0), (1.0, 0.93, 0.84)
PANELS = [(x, y, 1.15, 0.55) for x in (-1.8, 1.2, 3.6) for y in (3.0, 0.6, -1.8)] + [(-4.5, y, 0.55, 1.15) for y in (3.3, 1.5, -0.9)]
for x, y, w, h in PANELS:                                    # 천장 평판등 (Store.py 와 같음)
    light('AREA', (x, y, 3.07), 45 if x > -4 else 40, P_COOL if x > -4 else P_WARM, (w, h), (0, 0, -1), "Panel")
for l in store["lights"]:
    if l["type"] == "Point":
        light('POINT', l["pos"], l["intensity"] * 12, l["color"], name=l["name"])
light('POINT', canopy, 60, (1.0, 0.851, 0.659), name="CanopyWarm")
light('SUN', (-7, -15, 16), 2.6, (0.941, 0.925, 0.894), aim=SUN_DIR, name="Sun")

w = bpy.data.worlds.new("overcast_morning")
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.70, 0.75, 0.82, 1)
bg.inputs['Strength'].default_value = 1.0
sc.world = w

# ---------------------------------------------------------------- 레이아웃 JSON
hinge = sock("StoreGlassDoor", "_Socket_Handle")
SPAWN = [-2.4, -7.3, 1.55]                                   # 버스에서 내린 자리 (경계석 뒷면에서 0.5 m)
CAM = {"pos": SPAWN, "lookAt": [round(v, 3) for v in sock("StorefrontFacade", "_Socket_SignLook")],
       "fovVertical": 60,
       "intro": {"lookAt1": "StorefrontFacade_Socket_SignLook (3.2초)", "lookAt2": "StorefrontFacade_Socket_DoorLook (1.8초)"},
       "pullWalkTo": [1.78, -5.15, 0], "enterWalkTo": [1.52, -3.4, 0]}
NOTES = ("블렌더 좌표(Z-up, m)입니다. 프로토타입 three (x,y,z) = 블렌더 (x,-z,y)이고 rotZ는 블렌더 Z 회전(deg)입니다. "
         "매장 안·매장 앞 거리 항목은 Layouts/Store.json과 이름·자리가 같습니다(문을 열고 Store 씬으로 넘어갈 때 그대로 이어집니다). "
         "보도는 4.18 m(유리선 y=-3.8 ~ 경계석 뒷면 y=-7.8)이고 도로·경계석은 z=-0.14입니다. "
         "StoreGlassDoor: 회전 0이 닫힘이고 Leaf를 로컬 Z로 돌립니다. 당기면 거리 쪽으로 최대 1.45rad 열리고, 밀면 매장 쪽 0.0011rad에서 막고 거리 쪽으로 0.012rad 되튑니다(소리·카메라 흔들림). "
         "상호작용 점은 StoreGlassDoor_Socket_Handle 입니다. 클로저 2링크는 StorefrontFacade_Socket_CloserShoe로 풉니다. "
         "Bus: 씬 시작 때 자기 정면(로컬 -Y = Unity transform.forward, 월드 -X)으로 가속해 떠나고 x<-46에서 숨깁니다. 프로토타입은 +x로 떠나지만 우측통행이라 매장 쪽 차로는 -X입니다. "
         "Seat_NpcStudentWoman: 세 번째 밀기 때 문 쪽(Handle 소켓)으로 2.6초 돌아봤다가 원래 방향으로 돌아갑니다(프로토타입 ye()). Staff는 SitPhone입니다. "
         "hide = 이 인스턴스에서 끌 자식 오브젝트, parts = 자식의 로컬 회전(deg)입니다. "
         "조명 color는 sRGB입니다. 매장 안 조명은 Store.json과 같고, 하늘은 흐린 아침(회청색 0.70,0.75,0.82) 스카이박스입니다.")
out = os.path.join(ART, "Layouts", "Storefront.json")
for it in ITEMS:
    assert os.path.exists(os.path.join(ART, it["model"])), it["model"]
json.dump({"scene": "Storefront", "notes": NOTES, "items": ITEMS, "lights": LIGHTS,
           "ambient": {"mode": "Trilight/Gradient", "sky": [0.875, 0.902, 0.918], "ground": [0.435, 0.42, 0.392], "intensity": 0.75},
           "fog": {"mode": "Linear", "color": [0.761, 0.776, 0.784], "start": 34, "end": 110},
           "camera": CAM, "interact": {"door": [round(v, 3) for v in hinge], "radius": 2.1}},
          open(out, "w"), ensure_ascii=False, indent=1)
print("storefront_layout: json", out, len(ITEMS), "items")

# ---------------------------------------------------------------- 1인칭 렌더 (눈높이 1.55 m)
sc.render.engine = k3d._engine_eevee()
sc.view_settings.view_transform = 'AgX'
sc.eevee.taa_render_samples = 48
sc.eevee.use_raytracing = True
sc.eevee.use_shadows = True
sc.eevee.shadow_pool_size = '1024'
cd = bpy.data.cameras.new("cam")
cd.clip_start, cd.clip_end = 0.03, 600
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
door_look = sock("StorefrontFacade", "_Socket_DoorLook")
SHOTS = [  # (번호, 카메라, 목표, 렌즈, 차 숨김)
    (1, Vector((1.78, -5.15, 1.55)), door_look + Vector((0, 0, -0.05)), 28, False),     # 당기기 직전 문 앞
    (2, Vector(SPAWN), Vector((-0.1, -3.8, 2.7)), 22, False),                         # 시작 자리, 간판·유리문 쪽
    (3, Vector((0.5, -19.2, 1.55)), Vector((0.5, -3.8, 5.4)), 18, True),               # 건너편 보도에서 본 파사드
    (4, Vector((-16.5, -7.3, 1.55)), Vector((gx, -1.0, 3.2)), 24, False),              # 왼쪽 시장 게이트와 골목
]
pdir = os.path.join(k3d.SRC, "Previews")
os.makedirs(pdir, exist_ok=True)
for n, c, t, lens, no_cars in SHOTS:
    if ONLY and str(n) not in ONLY:
        continue
    for o in bus + car:
        o.hide_render = no_cars
    cd.lens = lens
    cam.location = c
    cam.rotation_euler = (t - c).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.render.filepath = os.path.join(pdir, f"Scene_Storefront_{n}.png")
    bpy.ops.render.render(write_still=True)
    print("storefront_layout: shot", sc.render.filepath)

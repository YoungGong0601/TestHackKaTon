# 홈(현관) 씬 배치: 스테이지 FBX 를 소켓에 맞춰 놓고, 조명 + 1인칭 렌더 3장 + Unity 레이아웃 JSON 을 만든다.
# 좌표 = HomeEntry 좌표계 (Blender = (-x3, z3, y3) = 과제 공식 (x3, -z3, y3) 을 Z 180° 돌린 것, Unity = (x3, y3, -z3)).
# HomeEntry 가 이 좌표계로 만들어져 회전 없이 (0,0,0) 에 두고, 현관문은 -Y (Unity +Z) 쪽이다.
# 먼저 HomeCorridor.py 를 실행해 둘 것 (Models/LayoutHome/HomeCorridor.fbx).
import sys, os, math, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Home"))
import bpy, k3d, hk
from mathutils import Vector, Matrix

k3d.reset()
FIX = Matrix.Rotation(math.radians(-90), 4, 'X')    # FBX 불러오기가 붙이는 X+90° 보정을 되돌림 (= 작성 좌표)
GZ = -13.63                                         # 지면 (HomeCorridor_Ground)
DOOR_OPEN = 1.5                                     # 프로토타입 K.rotation.y = doorT*1.5 (rad, +Z = 복도 쪽)
items = []


def load(rel, name=None, at=None, socket=None):
    """FBX 하나를 불러와 at(작성 좌표 4x4) 또는 socket 의 자리에 놓고 레이아웃 항목을 남긴다."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(k3d.ART, rel))
    root = next(o for o in bpy.data.objects if o not in before and o.parent is None)
    bpy.context.view_layer.update()
    m = bpy.data.objects[socket].matrix_world @ FIX if socket else (at or Matrix())
    root.matrix_world = m @ root.matrix_world
    bpy.context.view_layer.update()
    e = m.to_euler('XYZ')
    it = {"model": rel, "name": name or os.path.splitext(os.path.basename(rel))[0], "pos": [round(v, 4) for v in m.to_translation()],
          "rotZ": round(math.degrees(e.z), 2), "scale": 1}
    if abs(e.x) > 1e-4 or abs(e.y) > 1e-4:
        it["rotXYZ"] = [round(math.degrees(v), 2) for v in e]      # Blender XYZ 오일러 (deg): 기울어진 소품
    if socket:
        it["socket"] = socket
    items.append(it)
    return root, m


H = "Models/Home/"
load(H + "HomeEntry.fbx")
load(H + "HomeDoorFrame.fbx", socket="HomeEntry_Socket_DoorFrame")
door, door_m = load(H + "HomeDoor.fbx", socket="HomeDoorFrame_Socket_DoorHinge")
items[-1]["openRotZ"] = round(math.degrees(DOOR_OPEN), 1)
load(H + "HomeShoes.fbx", socket="HomeEntry_Socket_Shoes")
load(H + "HomeCane.fbx", socket="HomeEntry_Socket_Cane")
load(H + "HomeUmbrella.fbx", socket="HomeEntry_Socket_UmbrellaBlack")
load(H + "HomeUmbrellaRed.fbx", socket="HomeEntry_Socket_UmbrellaRed")
load(H + "HomeMedicineBag.fbx", socket="HomeEntry_Socket_MedicineBag")
load("Models/LayoutHome/HomeCorridor.fbx")
# 난간 너머 단지 아파트 동 (정면이 복도 쪽 +Y 를 보게 Z 180°). ~100m 떨어뜨려 문틈으로 하늘이 조금 보이게.
for i, (x, y, rz) in enumerate(((-6, -98, 180), (44, -112, 186), (-54, -106, 174), (14, -165, 180))):
    load("Models/Buildings/BuildingBackdrop.fbx", f"BuildingBackdrop_{i}",
         Matrix.Translation((x, y, GZ)) @ Matrix.Rotation(math.radians(rz), 4, 'Z'))
door_rest = door.matrix_world.copy()


# FBX 는 텍스처 경로를 담지 않으므로 (k3d export path_mode STRIP) <에셋>.json 의 Unity 머티리얼 정의로 다시 만든다.
defs = {}
for it in items:
    js = os.path.join(k3d.ART, os.path.splitext(it["model"])[0] + ".json")
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
missing = sorted({m.name for o in bpy.data.objects if o.type == 'MESH' for m in o.data.materials
                  if m and m.name.split(".")[0] not in defs})
print("Home: 머티리얼 정의 없음", missing)
door_open = door_m @ Matrix.Rotation(DOOR_OPEN, 4, 'Z') @ door_m.inverted() @ door_rest

# ---------------------------------------------------------------- 조명 (Unity 값 + 렌더용 Blender 값)
sc = bpy.context.scene
lights, bl = [], {}


def light(name, kind, pos, hexcol, ui, rng, energy, aim=None, angle=None, radius=0.05, extra=None):
    """kind: Point/Spot/Directional. hexcol = sRGB (Unity Light.color), energy = Blender W (렌더 전용 맞춤값)."""
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    d = {"name": name, "type": kind, "pos": [round(v, 3) for v in pos], "color": [round(v, 3) for v in c],
         "intensity": ui, "range": rng, "shadows": True}
    ld = bpy.data.lights.new(name, {"Point": 'POINT', "Spot": 'SPOT', "Directional": 'SUN'}[kind])
    ld.color, ld.energy = hk.srgb(hexcol), energy
    if kind == "Directional":
        ld.angle = math.radians(18)
    else:
        ld.shadow_soft_size = radius
    lo = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo)
    lo.location = pos
    if aim:
        v = Vector(aim).normalized()
        lo.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
        d["dir"] = [round(x, 3) for x in v]
    if angle:
        ld.spot_size, ld.spot_blend = math.radians(angle), 0.8
        d["spotAngle"] = angle
    d.update(extra or {})
    lights.append(d)
    bl[name] = lo
    return lo


# 프로토타입 값: lt(센서등 Spot FFBE78, 깜빡임) / nt, Tt(거실 쪽 따뜻한 Point) / Jn(복도 창 찬빛) / In(문 열면 들어오는 빛 0→26)
light("EntrySensorLight", "Spot", (0, -1.25, 2.2), "#FFC487", 2.4, 5.0, 70, aim=(0, 0.05, -1), angle=150, radius=0.04,
      extra={"flicker": "intensity *= 1 + sin(t*9.1)*.015 + sin(t*23.7)*.012 (가끔 -0.25), HomeEntry_LightGlow 발광도 같이"})
light("LivingFill", "Point", (0, 0.3, 2.05), "#FFB878", 0.9, 5.5, 30, radius=0.3)
light("LivingBack", "Point", (-0.2, 1.9, 1.9), "#FFB072", 0.6, 4.0, 18, radius=0.3)
light("WindowCool", "Point", (-0.68, -1.75, 1.78), "#A9C4E0", 0.9, 3.2, 9, radius=0.2)
light("CorridorLamp", "Point", (0, -3.2, 2.2), "#F2F1EC", 1.2, 4.5, 30, radius=0.1)
light("OvercastSun", "Directional", (0, -6, 12), "#DCE3EE", 0.8, 0, 1.6, aim=(0.3, -0.45, -0.84))   # 우리 동 뒤 높은 곳 → 앞 동 정면을 비춤, 복도는 그늘
light("CorridorSkyFill", "Spot", (0, -4.9, 2.0), "#CFDCEA", 1.0, 6.0, 260, aim=(0, 1, -0.32), angle=120, radius=1.2,
      extra={"note": "난간 쪽 열린 하늘에서 복도로 드는 흐린 날 빛 (그림자 켜야 닫힌 문 안으로 새지 않음)"})
light("DoorDaylight", "Spot", (0, -2.85, 1.4), "#C4D6EA", 0.0, 7.0, 0, aim=(0, 3.85, -1.0), angle=86, radius=0.4,
      extra={"openIntensity": 2.6, "note": "문이 열릴 때 0 → 2.6 (프로토타입 In 0→26)"})

# 월드: 카메라에는 흐린 아침 하늘, 조명에는 어두운 실내 앰비언트 (실내 빛샘 방지)
w = bpy.data.worlds.new("Home_World")
sc.world = w
w.use_nodes = True
nt = w.node_tree
bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
sky = nt.nodes.new('ShaderNodeBackground')
sky.inputs['Color'].default_value, sky.inputs['Strength'].default_value = (0.70, 0.75, 0.82, 1), 1.3
bg.inputs['Color'].default_value, bg.inputs['Strength'].default_value = (0.56, 0.52, 0.46, 1), 0.12
lp = nt.nodes.new('ShaderNodeLightPath')
mix = nt.nodes.new('ShaderNodeMixShader')
out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
nt.links.new(bg.outputs[0], mix.inputs[1])
nt.links.new(sky.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs['Surface'])

# ---------------------------------------------------------------- 1인칭 렌더 (눈높이 1.55m)
sc.render.engine = k3d._engine_eevee()
sc.render.resolution_x, sc.render.resolution_y = 1280, 800
sc.view_settings.view_transform = 'AgX'
sc.eevee.taa_render_samples = 48
if hasattr(sc.eevee, "use_raytracing"):
    sc.eevee.use_raytracing = True
cd = bpy.data.cameras.new("Home_Cam")
cd.lens, cd.clip_start, cd.clip_end = 28, 0.02, 400
cam = bpy.data.objects.new("Home_Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
PV = os.path.join(k3d.SRC, "Previews")
os.makedirs(PV, exist_ok=True)


def shot(n, loc, tgt):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(PV, f"Scene_Home_{n}.png")
    bpy.ops.render.render(write_still=True)
    print("Home: shot", sc.render.filepath)


SPAWN, SPAWN_AT = (0, 1.15, 1.55), (0, -2.35, 1.375)     # 프로토타입 spawn (0,0,1.15) yaw 0 pitch -0.05
NEAR, NEAR_AT = (0, -1.2, 1.42), (-0.1, -2.35, 1.1)      # 신발 신은 뒤 (타일 위, 눈 = -0.13+1.55) → lookAt([.1,1.1,R])
shot(1, SPAWN, SPAWN_AT)
shot(2, NEAR, NEAR_AT)
door.matrix_world = door_open
bl["DoorDaylight"].data.energy = 120
shot(3, NEAR, NEAR_AT)
door.matrix_world = door_rest

# ---------------------------------------------------------------- Unity 레이아웃 JSON
lay = {"scene": "Home",
       "notes": ("Blender 좌표 (Z-up, m). HomeEntry 좌표계: Blender = (-x3, z3, y3), Unity = (x3, y3, -z3) (프로토타입 three 좌표). "
                 "현관문은 -Y (Unity +Z). rotZ = Blender Z 회전(deg). rotXYZ = 기울어진 소품의 전체 Blender XYZ 오일러(deg) — "
                 "rotZ 만 쓰면 지팡이/우산 기울기가 빠지고 약 봉투가 신발장 위에 서 버리므로 rotXYZ 를 쓰거나 socket(HomeEntry/HomeDoorFrame "
                 "소켓 이름)에 원점을 그대로 맞출 것. HomeDoor: 원점 = 경첩 축, 열기 = 로컬 Z 를 0 → openRotZ(+86°, 복도 쪽). "
                 "조명 color = sRGB, 모든 조명 그림자 켬 (OvercastSun 은 그림자가 있어야 닫힌 현관에 새지 않음). "
                 "DoorDaylight 는 문이 열릴 때 openIntensity 까지 올린다. 하늘: 흐린 아침 회청색 (RGB 0.70,0.75,0.82 근처) 스카이박스/배경. "
                 "거울 문(HomeEntry_CabDoor2)용 Box Projection Reflection Probe 를 reflectionProbe 범위로 둘 것."),
       "items": items, "lights": lights,
       "ambient": {"sky": [0.557, 0.518, 0.463], "ground": [0.173, 0.133, 0.094], "intensity": 0.34},
       "fog": {"mode": "Linear", "color": [0.72, 0.76, 0.82], "start": 25, "end": 320, "note": "흐린 아침 먼 동 흐리게"},
       "reflectionProbe": {"pos": [0, -0.4, 1.1], "size": [1.96, 5.25, 2.45], "boxProjection": True},
       "camera": {"pos": list(SPAWN), "lookAt": list(SPAWN_AT), "fovVertical": 66,
                  "afterShoes": {"pos": list(NEAR), "lookAt": list(NEAR_AT)}}}
p = os.path.join(k3d.ART, "Layouts", "Home.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(lay, open(p, "w"), ensure_ascii=False, indent=1)
for it in items:                                          # 모델 경로 확인
    assert os.path.exists(os.path.join(k3d.ART, it["model"])), it["model"]
print("Home: layout", p, len(items), "items")

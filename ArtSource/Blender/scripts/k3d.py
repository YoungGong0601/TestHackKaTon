"""키오스크 게임 3D 파이프라인: Blender 5.2 (headless) -> Unity 6 URP.

에셋 스크립트 기본형 (ArtSource/Blender/scripts/<Group>/<asset>.py):

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import k3d
    k3d.reset()
    body = ...                               # 미터, Z-up, 정면 = -Y, 원점 = 바닥 중앙
    k3d.bake(body, size=1024)                # 절차 머티리얼 -> 텍스처 1세트 (M_Glass*/M_Dyn*/M_Tile* 는 유지)
    k3d.export("Kiosk", "Store", [body])     # FBX + JSON + .blend
    k3d.preview("Kiosk", [body])             # ArtSource/Previews/Kiosk_*.png

실행:  blender -b --factory-startup --python <asset>.py
검증:  blender -b --factory-startup --python k3d.py -- validate <...>/Models/Store/Kiosk.fbx [기대높이m]
새 컴퓨터: 처음 한 번 blender -b --factory-startup --python setup.py (Pillow 가 있는 파이썬을 K3D_CACHE/venv 에 만든다)
환경변수: K3D_ROOT(출력 루트, 기본 저장소) · K3D_CACHE(캐시, 기본 ArtSource/_cache) · K3D_BAKE_SLOTS(동시 베이크 수, 기본 6)

규칙
- 머티리얼 이름: M_<이름>. 접두사 M_Glass(투명) · M_Dyn(게임이 런타임에 텍스처를 넣는 화면, UV 0-1) · M_Tile(타일링 텍스처, 월드 UV)
  는 bake 하지 않고 그대로 내보낸다. 나머지는 bake 가 오브젝트당 텍스처 1세트(M_<오브젝트이름>)로 합친다.
- bake 대상 머티리얼은 Principled BSDF 하나가 출력에 바로 연결돼야 한다 (입력에는 어떤 노드든 연결 가능).
- Unity 머티리얼은 FBX 옆 <에셋>.json 을 Assets/Editor/Art3DTools.cs 가 읽어 URP Lit 으로 만든다.
  색은 linear 로 저장한다 (Blender 값 그대로). MS 텍스처 = R 금속, G AO, A 스무스니스.
"""
import bpy, bmesh, os, sys, json, math, shutil, urllib.request, time
try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt
import numpy as np
from mathutils import Vector

REPO = os.environ.get("K3D_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ART = os.path.join(REPO, "Assets", "Art3D")
SRC = os.path.join(REPO, "ArtSource")
KEEP = ("M_Glass", "M_Dyn", "M_Tile")
UA = {"User-Agent": "kiosk-hackathon-asset-pipeline"}
CACHE = os.environ.get("K3D_CACHE") or os.path.join(SRC, "_cache")
PY = os.path.join(CACHE, "venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(CACHE, "venv", "bin", "python")  # Pillow 가 있는 파이썬
BAKE_SLOTS = int(os.environ.get("K3D_BAKE_SLOTS", "6"))  # 동시에 GPU 베이크하는 Blender 프로세스 수 상한


def _bake_slot():
    d = os.path.join(CACHE, "bake_slots")
    os.makedirs(d, exist_ok=True)
    while True:
        for i in range(BAKE_SLOTS):
            f = open(os.path.join(d, f"slot{i}"), "a")  # "w" 는 Windows 에서 잠긴 파일을 비우다 실패한다
            try:
                if fcntl:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                return f
            except OSError:
                f.close()
        time.sleep(0.5)


# ---------------------------------------------------------------- scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    u = bpy.context.scene.unit_settings
    u.system, u.scale_length = 'METRIC', 1.0


def tree_of(objs):
    """objs 와 모든 자식."""
    out = []
    def walk(o):
        if o not in out:
            out.append(o)
            for c in o.children:
                walk(c)
    for o in objs:
        walk(o)
    return out


def select(objs, active=None):
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode != 'OBJECT' else None
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)


def smooth(obj, angle=30):
    """스무스 셰이딩 + 각도 기준 샤프 엣지."""
    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(angle))


def apply_all(obj, keep_armature=True):
    """모디파이어 적용 (Armature 는 남김)."""
    select([obj])
    for m in list(obj.modifiers):
        if keep_armature and m.type == 'ARMATURE':
            continue
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError as e:
            print("k3d: modifier_apply 실패", obj.name, m.name, e)
            obj.modifiers.remove(m)


def join(objs, name):
    """메시 여러 개를 하나로 (모디파이어 먼저 적용)."""
    objs = [o for o in objs if o.type == 'MESH']
    for o in objs:
        apply_all(o)
    select(objs, objs[0])
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    return o


def origin_bottom(obj):
    """원점을 바닥 중앙으로 (월드 위치 유지)."""
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    c = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2,
                (min(v.y for v in vs) + max(v.y for v in vs)) / 2,
                min(v.z for v in vs)))
    set_origin(obj, c)


def set_origin(obj, world_point):
    sc = bpy.context.scene
    old = sc.cursor.location.copy()
    sc.cursor.location = world_point
    select([obj])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    sc.cursor.location = old


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


# ---------------------------------------------------------------- materials

def _nodes(m):
    if m.node_tree is None:
        m.use_nodes = True
    return m.node_tree


def principled(m):
    nt = _nodes(m)
    out = output(m)
    if out and out.inputs['Surface'].is_linked:
        n = out.inputs['Surface'].links[0].from_node
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def output(m):
    outs = [n for n in _nodes(m).nodes if n.type == 'OUTPUT_MATERIAL']
    return next((n for n in outs if n.is_active_output), outs[0] if outs else None)


def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, emission=None, strength=1.0, alpha=1.0,
        double_sided=False):
    """단색 Principled 머티리얼 (color 는 linear RGB)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = _nodes(m)
    p = principled(m)
    if p is None:
        nt.nodes.clear()
        p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        o = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(p.outputs[0], o.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*color[:3], 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Alpha'].default_value = alpha
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[:3], 1)
        p.inputs['Emission Strength'].default_value = strength
    if double_sided:
        m["unity_double_sided"] = 1
    return m


def flag(m, **kw):
    """Unity 쪽 추가 설정: double_sided=True, alpha_clip=0.5, transparent=True, dynamic=True."""
    for k, v in kw.items():
        m["unity_" + k] = v
    return m


def image_node(m, image, socket=None, non_color=False, uv=None):
    nt = _nodes(m)
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = image
    if non_color:
        image.colorspace_settings.name = 'Non-Color'
    if uv:
        u = nt.nodes.new('ShaderNodeUVMap')
        u.uv_map = uv
        nt.links.new(u.outputs[0], n.inputs[0])
    if socket is not None:
        nt.links.new(n.outputs['Color'], socket)
    return n


def load_image(path, name=None, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if name:
        im.name = name
    if non_color:
        im.colorspace_settings.name = 'Non-Color'
    return im


# ---------------------------------------------------------------- UV

def uv_world(obj, tile_m=1.0, layer=None):
    """월드 좌표 박스 투영 UV (1 UV = tile_m 미터). 타일 머티리얼용."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv[layer] if layer else bm.loops.layers.uv.active
    mw = obj.matrix_world
    rot = mw.to_3x3()
    for f in bm.faces:
        n = (rot @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            w = mw @ l.vert.co
            if ax == 0:
                u, v = (w.y if n.x > 0 else -w.y), w.z
            elif ax == 1:
                u, v = (-w.x if n.y > 0 else w.x), w.z
            else:
                u, v = w.x, (w.y if n.z > 0 else -w.y)
            l[uvl].uv = (u / tile_m, v / tile_m)
    bm.to_mesh(me)
    bm.free()


def uv_smart(obj, faces=None, margin=0.004, layer=None):
    """스마트 UV 투영 (faces=인덱스 목록이면 그 면만)."""
    me = obj.data
    if layer:
        me.uv_layers.active = me.uv_layers[layer]
    elif not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    select([obj])
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    sel = set(faces) if faces is not None else None
    for f in bm.faces:
        f.select = sel is None or f.index in sel
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(margin=margin, rotate=True, shape_method='CONCAVE')
    except Exception as e:
        print("k3d: pack_islands 생략", e)
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- bake

def _cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        if os.environ.get("K3D_DEVICE") == "CPU":
            raise RuntimeError("CPU 지정")
        pr = bpy.context.preferences.addons['cycles'].preferences
        for kind in ('METAL', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
            try:
                pr.compute_device_type = kind
            except TypeError:  # 이 운영체제에 없는 종류
                continue
            pr.get_devices()
            if any(d.type == kind for d in pr.devices):
                break
        else:
            raise RuntimeError("GPU 없음")
        for d in pr.devices:
            d.use = d.type == kind  # CPU 를 같이 켜면 Metal 베이크가 힙 손상으로 죽었다
        sc.cycles.device = 'GPU'
    except Exception:
        sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")


def _new_image(name, size, non_color):
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    im = bpy.data.images.new(name, size, size, alpha=True)
    im.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    im.generated_color = (0, 0, 0, 1)
    return im


def _pixels(im):
    a = np.empty(im.size[0] * im.size[1] * 4, np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(im.size[1], im.size[0], 4)


def _bake_pass(obj, mats, image, kind, uv, margin, socket=None):
    """kind: 'EMIT'(socket 값을 emission 으로) / 'NORMAL' / 'AO'."""
    temp = []
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = image
        nt.nodes.active = n
        temp.append((m, n, None, None))
        if kind == 'EMIT':
            p, o = principled(m), output(m)
            prev = o.inputs['Surface'].links[0].from_socket if o.inputs['Surface'].is_linked else None
            e = nt.nodes.new('ShaderNodeEmission')
            e.inputs['Strength'].default_value = 1.0
            src = p.inputs[socket] if p else None
            if src is not None and src.is_linked:
                nt.links.new(src.links[0].from_socket, e.inputs['Color'])
            elif src is not None:
                v = src.default_value
                e.inputs['Color'].default_value = (v, v, v, 1) if isinstance(v, float) else tuple(v)
            else:
                e.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
            nt.links.new(e.outputs[0], o.inputs['Surface'])
            temp[-1] = (m, n, e, prev)
    # 굽지 않는 머티리얼(M_Glass/M_Dyn/M_Tile 등)도 Cycles 가 활성 이미지 노드에 굽기 때문에 더미로 막는다
    dummy = bpy.data.images.new("k3d_dummy", 8, 8)
    for s in obj.material_slots:
        m = s.material
        if m and m not in mats:
            n = _nodes(m).nodes.new('ShaderNodeTexImage')
            n.image = dummy
            m.node_tree.nodes.active = n
            temp.append((m, n, None, None))
    select([obj])
    sc = bpy.context.scene
    sc.render.bake.margin = margin
    sc.render.bake.margin_type = 'EXTEND'
    if kind == 'NORMAL':
        bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', uv_layer=uv, margin=margin, use_clear=True)
    elif kind == 'AO':
        bpy.ops.object.bake(type='AO', uv_layer=uv, margin=margin, use_clear=True)
    else:
        bpy.ops.object.bake(type='EMIT', uv_layer=uv, margin=margin, use_clear=True)
    for m, n, e, prev in temp:
        nt = m.node_tree
        nt.nodes.remove(n)
        if e:
            nt.nodes.remove(e)
            if prev:
                nt.links.new(prev, output(m).inputs['Surface'])
    bpy.data.images.remove(dummy)


def _socket_max(mats, socket):
    best = 0.0
    for m in mats:
        p = principled(m)
        if p and socket in p.inputs:
            s = p.inputs[socket]
            best = max(best, 1.0 if s.is_linked else float(s.default_value))
    return best


def _has_emission(mats):
    for m in mats:
        p = principled(m)
        if not p or p.inputs['Emission Strength'].default_value <= 0:
            continue
        c = p.inputs['Emission Color']
        if c.is_linked or max(c.default_value[:3]) > 0.001:
            return True
    return False


def bake(obj, size=1024, keep=(), ao=True, ao_distance=None, samples=16, margin=None, name=None):
    """obj 의 절차 머티리얼(KEEP 접두사·keep 제외)을 텍스처 1세트로 굽고 M_<name> 하나로 바꾼다.

    결과: Assets/Art3D/Textures/<name>/T_<name>_BaseColor.jpg, _Normal.png, _MS.png (+_Emission.jpg)
    모디파이어(Armature 제외)를 적용하고 삼각화한 뒤 굽는다. 반환: 새 머티리얼 (굽을 게 없으면 None).
    """
    slot = _bake_slot()
    try:
        return _bake_impl(obj, size, keep, ao, ao_distance, samples, margin, name)
    finally:
        slot.close()


def _bake_impl(obj, size, keep, ao, ao_distance, samples, margin, name):
    name = name or obj.name
    margin = margin if margin is not None else max(4, size // 128)
    apply_all(obj)
    select([obj])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')
    me = obj.data
    slots = [s.material for s in obj.material_slots]
    bake_ids = [i for i, m in enumerate(slots)
                if m and not m.name.startswith(KEEP) and m.name not in keep]
    if not bake_ids:
        return None
    mats = [slots[i] for i in bake_ids]
    for m in mats:
        if principled(m) is None:
            raise RuntimeError(f"k3d.bake: {m.name} 에 Principled BSDF 가 없습니다")

    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    base_uv = me.uv_layers[0].name
    if "UVAtlas" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["UVAtlas"])
    me.uv_layers.new(name="UVAtlas")
    face_ids = [p.index for p in me.polygons if p.material_index in bake_ids]
    uv_smart(obj, face_ids, margin=min(0.02, 2.5 * margin / size), layer="UVAtlas")
    me.uv_layers.active = me.uv_layers[base_uv]

    _cycles(samples)
    tdir = os.path.join(ART, "Textures", name)
    os.makedirs(tdir, exist_ok=True)
    pfx = f"T_{name}_"
    base = _new_image(pfx + "BaseColor", size, False)
    _bake_pass(obj, mats, base, 'EMIT', "UVAtlas", margin, 'Base Color')
    rough = _new_image(pfx + "Rough_tmp", size, True)
    _bake_pass(obj, mats, rough, 'EMIT', "UVAtlas", margin, 'Roughness')
    metal_v = _socket_max(mats, 'Metallic')
    metal = None
    if metal_v > 0:
        metal = _new_image(pfx + "Metal_tmp", size, True)
        _bake_pass(obj, mats, metal, 'EMIT', "UVAtlas", margin, 'Metallic')
    nor = _new_image(pfx + "Normal", size, True)
    bpy.context.scene.cycles.samples = max(4, samples // 2)
    _bake_pass(obj, mats, nor, 'NORMAL', "UVAtlas", margin)
    aoim = None
    if ao:
        dims = obj.dimensions
        dist = ao_distance or min(1.0, max(0.03, 0.15 * max(dims)))
        bpy.context.scene.world.light_settings.distance = dist
        bpy.context.scene.cycles.samples = max(32, samples)
        aoim = _new_image(pfx + "AO_tmp", size, True)
        _bake_pass(obj, mats, aoim, 'AO', "UVAtlas", margin)
    emis = None
    emis_strength = 0.0
    if _has_emission(mats):
        bpy.context.scene.cycles.samples = samples
        emis = _new_image(pfx + "Emission", size, False)
        _bake_pass(obj, mats, emis, 'EMIT', "UVAtlas", margin, 'Emission Color')
        emis_strength = max(principled(m).inputs['Emission Strength'].default_value for m in mats)

    # MS = R 금속, G AO, B 0, A 스무스니스
    r = _pixels(rough)
    ms_px = np.zeros_like(r)
    ms_px[..., 0] = _pixels(metal)[..., 0] if metal else 0.0
    ms_px[..., 1] = _pixels(aoim)[..., 0] if aoim else 1.0
    ms_px[..., 3] = 1.0 - r[..., 0]
    ms = _new_image(pfx + "MS", size, True)
    ms.pixels.foreach_set(ms_px.ravel())
    for t in (rough, metal, aoim):
        if t:
            bpy.data.images.remove(t)

    _save(base, os.path.join(tdir, pfx + "BaseColor.jpg"))
    _save(nor, os.path.join(tdir, pfx + "Normal.png"))
    _save(ms, os.path.join(tdir, pfx + "MS.png"))
    if emis:
        _save(emis, os.path.join(tdir, pfx + "Emission.jpg"))

    # 새 머티리얼 (Blender 미리보기용으로도 맞게 연결)
    mname = "M_" + name
    old = bpy.data.materials.get(mname)
    if old:
        old.name = mname + "_old"
    nm = bpy.data.materials.new(mname)
    nt = _nodes(nm)
    p = principled(nm)
    image_node(nm, base, p.inputs['Base Color'])
    tn = image_node(nm, nor, None, non_color=True)
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tn.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], p.inputs['Normal'])
    mn = image_node(nm, ms, None, non_color=True)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mn.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Red'], p.inputs['Metallic'])
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(mn.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], p.inputs['Roughness'])
    if emis:
        image_node(nm, emis, p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emis_strength
    nm["unity_baked"] = 1
    nm["unity_occlusion"] = 1 if aoim else 0
    nm["unity_emission_strength"] = emis_strength

    # 슬롯 재배치: 구운 슬롯들 -> 0번 하나, 나머지 유지
    keep_ids = [i for i in range(len(slots)) if i not in bake_ids]
    remap = {i: 0 for i in bake_ids}
    for k, i in enumerate(keep_ids):
        remap[i] = k + 1
    idx = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", idx)
    new_idx = np.array([remap.get(int(i), 0) for i in idx], np.int32)
    keep_mats = [slots[i] for i in keep_ids]
    me.materials.clear()
    me.materials.append(nm)
    for m in keep_mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", new_idx)

    # UV 합치기: 구운 면은 UVAtlas 좌표를 UV0 으로
    n_loops = len(me.loops)
    a0 = np.empty(n_loops * 2, np.float32)
    aa = np.empty(n_loops * 2, np.float32)
    me.uv_layers[base_uv].data.foreach_get("uv", a0)
    me.uv_layers["UVAtlas"].data.foreach_get("uv", aa)
    starts = np.empty(len(me.polygons), np.int32)
    totals = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_start", starts)
    me.polygons.foreach_get("loop_total", totals)
    mask = np.zeros(n_loops, bool)
    for s, t, mi in zip(starts, totals, new_idx):
        if mi == 0:
            mask[s:s + t] = True
    a0 = a0.reshape(-1, 2)
    a0[mask] = aa.reshape(-1, 2)[mask]
    me.uv_layers[base_uv].data.foreach_set("uv", a0.ravel())
    me.uv_layers.remove(me.uv_layers["UVAtlas"])
    me.uv_layers.active = me.uv_layers[base_uv]
    for m in mats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    return nm


def _save(im, path, quality=93):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    jpg = path.lower().endswith(".jpg")
    im.filepath_raw = path
    im.file_format = 'JPEG' if jpg else 'PNG'
    try:
        im.save(quality=quality) if jpg else im.save()
    except TypeError:
        im.save()
    im.source = 'FILE'
    im.filepath = path


# ---------------------------------------------------------------- tile textures (Poly Haven, CC0)

def polyhaven(asset_id, res="2k", kind="textures"):
    """Poly Haven(CC0) 에셋을 K3D_CACHE/polyhaven/<id>/ 에 받는다 (저장소 밖 캐시).
    textures -> {'diff','nor','rough','ao','metal','arm' 중 있는 것: 경로}, models -> .gltf 경로."""
    d = os.path.join(CACHE, "polyhaven", asset_id)
    os.makedirs(d, exist_ok=True)
    meta = os.path.join(d, "files.json")
    if not os.path.exists(meta):
        req = urllib.request.Request(f"https://api.polyhaven.com/files/{asset_id}", headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            open(meta, "wb").write(r.read())
    files = json.load(open(meta, encoding="utf-8"))

    def get(url, rel):
        p = os.path.join(d, rel)
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r:
                open(p + ".part", "wb").write(r.read())
            os.replace(p + ".part", p)
        return p

    if kind == "models":
        g = files["gltf"][res]["gltf"]
        for rel, info in g.get("include", {}).items():
            get(info["url"], rel)
        return get(g["url"], os.path.basename(g["url"]))
    keys = {"diff": ["Diffuse", "diff"], "nor": ["nor_gl"], "rough": ["Rough", "rough"],
            "ao": ["AO", "ao"], "metal": ["Metal", "metal"], "arm": ["arm"]}
    out = {}
    for k, names in keys.items():
        for nme in names:
            if nme in files and res in files[nme]:
                f = files[nme][res].get("jpg") or files[nme][res].get("png")
                if f:
                    out[k] = get(f["url"], os.path.basename(f["url"]))
                    break
    return out


def tile(name, maps=None, polyhaven_id=None, res="2k", metal=0.0, rough_mul=1.0, tint=None):
    """타일링 PBR 머티리얼 M_Tile_<name>. maps={'diff','nor','rough','ao','metal'} 경로 또는 polyhaven_id.
    텍스처는 Assets/Art3D/Textures/Tile/ 에 T_Tile_<name>_BaseColor.jpg/_Normal.jpg/_MS.png 로 저장.
    UV 는 uv_world(obj, tile_m) 로 월드 스케일 투영할 것."""
    if not name.startswith("Tile_"):
        name = "Tile_" + name
    mname = "M_" + name
    if mname in bpy.data.materials:
        return bpy.data.materials[mname]
    maps = maps or polyhaven(polyhaven_id, res)
    tdir = os.path.join(ART, "Textures", "Tile")
    os.makedirs(tdir, exist_ok=True)
    pfx = os.path.join(tdir, f"T_{name}_")
    if not os.path.exists(pfx + "BaseColor.jpg"):
        _copy_as_jpg(maps["diff"], pfx + "BaseColor.jpg")
    if "nor" in maps and not os.path.exists(pfx + "Normal.jpg"):
        _copy_as_jpg(maps["nor"], pfx + "Normal.jpg")
    if not os.path.exists(pfx + "MS.png"):
        n = 1024
        def ch(path, default):
            if not path:
                return np.full((n, n), default, np.float32)
            im = load_image(path, non_color=True)
            im.scale(n, n)
            v = _pixels(im)[..., 0].copy()
            bpy.data.images.remove(im)
            return v
        rgh = np.clip(ch(maps.get("rough"), 0.6) * rough_mul, 0, 1)
        px = np.zeros((n, n, 4), np.float32)
        px[..., 0] = ch(maps.get("metal"), metal)
        px[..., 1] = ch(maps.get("ao"), 1.0)
        px[..., 3] = 1 - rgh
        im = _new_image(f"T_{name}_MS", n, True)
        im.pixels.foreach_set(px.ravel())
        _save(im, pfx + "MS.png")
    m = bpy.data.materials.new(mname)
    nt = _nodes(m)
    p = principled(m)
    b = image_node(m, load_image(pfx + "BaseColor.jpg", f"T_{name}_BaseColor"), None)
    if tint:
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(b.outputs['Color'], mix.inputs['A'])
        mix.inputs['B'].default_value = (*tint[:3], 1)
        nt.links.new(mix.outputs['Result'], p.inputs['Base Color'])
        m["unity_tint"] = list(tint[:3])
    else:
        nt.links.new(b.outputs['Color'], p.inputs['Base Color'])
    if os.path.exists(pfx + "Normal.jpg"):
        tn = image_node(m, load_image(pfx + "Normal.jpg", f"T_{name}_Normal", True), None, non_color=True)
        nmap = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tn.outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], p.inputs['Normal'])
    mn = image_node(m, load_image(pfx + "MS.png", f"T_{name}_MS", True), None, non_color=True)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mn.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Red'], p.inputs['Metallic'])
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(mn.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], p.inputs['Roughness'])
    m["unity_occlusion"] = 1
    return m


def _copy_as_jpg(src, dst):
    if src.lower().endswith((".jpg", ".jpeg")):
        shutil.copyfile(src, dst)
        return
    im = load_image(src)
    _save(im, dst)
    bpy.data.images.remove(im)


# ---------------------------------------------------------------- export

def _lin(c):
    return [round(float(x), 4) for x in c]


def _rel(path):
    return os.path.relpath(path, ART).replace(os.sep, "/")


def _img_path(im, asset):
    """머티리얼이 쓰는 이미지를 Assets/Art3D/Textures 아래 파일로 보장하고 Art3D 기준 상대경로를 돌려준다."""
    p = bpy.path.abspath(im.filepath) if im.filepath else ""
    if p and os.path.exists(p) and os.path.abspath(p).startswith(os.path.abspath(ART) + os.sep):
        return _rel(p)
    nm = im.name if im.name.startswith("T_") else f"T_{asset}_{im.name}"
    nm = os.path.splitext(nm)[0]
    ext = ".png" if (im.file_format == 'PNG' or not p or p.lower().endswith(".png")) else ".jpg"
    dst = os.path.join(ART, "Textures", asset, nm + ext)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if p and os.path.exists(p):
        shutil.copyfile(p, dst)
    else:
        _save(im, dst)
    im.filepath = dst
    return _rel(dst)


def _linked_image(sock):
    """소켓 상류의 Image Texture 노드 (Normal Map/Mix 등 한 단계 건너뜀)."""
    if not sock.is_linked:
        return None
    n = sock.links[0].from_node
    for _ in range(4):
        if n.type == 'TEX_IMAGE':
            return n.image
        nxt = [i for i in n.inputs if i.is_linked and i.type in ('RGBA', 'VECTOR', 'VALUE')]
        if not nxt:
            return None
        n = nxt[0].links[0].from_node
    return None


def material_json(m, asset):
    p = principled(m)
    d = {}
    if m.get("unity_baked") or m.name.startswith("M_Tile"):
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                nm = n.image.name
                key = next((k for k in ("BaseColor", "Normal", "MS", "Emission") if nm.endswith("_" + k)), None)
                if key:
                    d.setdefault("maps", {})[key] = _img_path(n.image, asset)
        d["baseColor"] = list(m.get("unity_tint", [1, 1, 1])) + [1]
        d["metallic"], d["smoothness"] = 1.0, 1.0
        d["occlusion"] = bool(m.get("unity_occlusion", 0))
        es = float(m.get("unity_emission_strength", 0))
        if es > 0:
            d["emission"], d["emissionStrength"] = [1, 1, 1], round(es, 3)
    elif p:
        bc = p.inputs['Base Color']
        a = float(p.inputs['Alpha'].default_value)
        d["baseColor"] = _lin(bc.default_value[:3]) + [round(a, 3)]
        d["metallic"] = round(float(p.inputs['Metallic'].default_value), 3)
        d["smoothness"] = round(1 - float(p.inputs['Roughness'].default_value), 3)
        im = _linked_image(bc)
        if im:
            d.setdefault("maps", {})["BaseColor"] = _img_path(im, asset)
            d["baseColor"] = [1, 1, 1, round(a, 3)]
        im = _linked_image(p.inputs['Normal'])
        if im:
            d.setdefault("maps", {})["Normal"] = _img_path(im, asset)
        es = float(p.inputs['Emission Strength'].default_value)
        ec = p.inputs['Emission Color']
        im = _linked_image(ec)
        if es > 0 and (im or max(ec.default_value[:3]) > 0.001):
            d["emission"] = [1, 1, 1] if im else _lin(ec.default_value[:3])
            d["emissionStrength"] = round(es, 3)
            if im:
                d.setdefault("maps", {})["Emission"] = _img_path(im, asset)
        if a < 0.999 or m.name.startswith("M_Glass"):
            d["transparent"] = True
    else:
        d["baseColor"] = [0.8, 0.8, 0.8, 1]
    if m.name.startswith("M_Dyn"):
        d["dynamic"] = True
    for k, key, typ in (("double_sided", "doubleSided", bool), ("alpha_clip", "alphaClip", float),
                        ("transparent", "transparent", bool), ("dynamic", "dynamic", bool)):
        if ("unity_" + k) in m:
            d[key] = typ(m["unity_" + k])
    d["name"] = m.name
    return d


def export(asset, category, objs, rigged=False, anim=False, notes=None):
    """objs(+자식)를 Assets/Art3D/Models/<category>/<asset>.fbx 로 내보낸다.
    + <asset>.json (Unity 머티리얼 정의), ArtSource/Blender/<category>/<asset>.blend.
    rigged=True: 아마추어 포함 (Apply Transform 끔, Unity 가 Bake Axis Conversion).
    anim=True: 모든 액션을 클립으로."""
    objs = tree_of(objs)
    mdir = os.path.join(ART, "Models", category)
    os.makedirs(mdir, exist_ok=True)
    fbx = os.path.join(mdir, asset + ".fbx")
    mats = {}
    for o in objs:
        if o.type != 'MESH':
            continue
        while len(o.data.uv_layers) > 1:  # UV2 는 Unity 가 라이트맵용으로 만든다
            o.data.uv_layers.remove(o.data.uv_layers[-1])
        for s in o.material_slots:
            if s.material and s.material.name not in mats:
                mats[s.material.name] = material_json(s.material, asset)
        if not o.material_slots:
            print("k3d: 경고 머티리얼 없음", o.name)
    types = {'MESH', 'EMPTY'} | ({'ARMATURE'} if rigged else set())
    select(objs)
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types=types,
        global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Z', axis_up='Y', bake_space_transform=not rigged,
        use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=False,
        use_custom_props=False, add_leaf_bones=False, use_armature_deform_only=True,
        primary_bone_axis='Y', secondary_bone_axis='X',
        bake_anim=anim, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=anim, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        path_mode='STRIP', embed_textures=False)
    info = {"asset": asset, "category": category, "rigged": rigged, "materials": list(mats.values())}
    if notes:
        info["notes"] = notes
    json.dump(info, open(os.path.join(mdir, asset + ".json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    bdir = os.path.join(SRC, "Blender", category)
    os.makedirs(bdir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bdir, asset + ".blend"), copy=True, compress=True)
    tris = 0
    for o in objs:
        if o.type == 'MESH':
            ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
            ev.calc_loop_triangles()
            tris += len(ev.loop_triangles)
    print(f"k3d: export {fbx}  tris={tris}  materials={list(mats)}")
    return fbx


# ---------------------------------------------------------------- preview

def _engine_eevee():
    items = bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
    return 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in items else 'BLENDER_EEVEE'


def bounds(objs):
    pts = []
    for o in tree_of(objs):
        if o.type == 'MESH':
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def preview(asset, objs, views=((35, 18), (215, 12)), res=(1200, 900), ground=True, lens=50, tag=""):
    """3/4 앞·뒤 렌더 -> ArtSource/Previews/<asset>[_tag]_<i>.png. 경로 목록을 반환 (Read 로 확인할 것).
    views = (방위각 deg: 0=정면(-Y 쪽에서 봄), 고도 deg)."""
    sc = bpy.context.scene
    sc.render.engine = _engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'  # Unity(톤매핑 없음)와 비슷하게
    sc.view_settings.look = 'None'
    mn, mx = bounds(objs)
    c = (mn + mx) / 2
    r = max((mx - mn).length / 2, 0.05)
    tmp = []
    w = bpy.data.worlds.new("k3d_preview")
    if w.node_tree is None:
        w.use_nodes = True
    wn = w.node_tree.nodes
    bg = next((n for n in wn if n.type == 'BACKGROUND'), None)
    if bg is None:
        bg = wn.new('ShaderNodeBackground')
        wo = next((n for n in wn if n.type == 'OUTPUT_WORLD'), None) or wn.new('ShaderNodeOutputWorld')
        w.node_tree.links.new(bg.outputs[0], wo.inputs['Surface'])
    bg.inputs['Color'].default_value = (0.62, 0.66, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.45
    old_world = sc.world
    sc.world = w
    def light(kind, energy, loc, size=1.0):
        ld = bpy.data.lights.new("k3d_l", kind)
        ld.energy = energy
        if kind == 'AREA':
            ld.size = size
        lo = bpy.data.objects.new("k3d_l", ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = c - Vector(loc)
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        tmp.append(lo)
    light('SUN', 1.6, c + Vector((-r * 2, -r * 3, r * 4)))
    light('AREA', 40 * r * r, c + Vector((r * 3, -r * 2, r * 1.5)), r * 2)
    light('AREA', 60 * r * r, c + Vector((-r * 2, r * 3, r * 2)), r * 2)
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=r * 40, location=(c.x, c.y, mn.z - 0.001))
        g = bpy.context.active_object
        g.data.materials.append(mat("k3d_ground", (0.35, 0.35, 0.36), 0.8))
        tmp.append(g)
    cd = bpy.data.cameras.new("k3d_cam")
    cd.lens = lens
    cam = bpy.data.objects.new("k3d_cam", cd)
    sc.collection.objects.link(cam)
    tmp.append(cam)
    sc.camera = cam
    fov = 2 * math.atan(18 / lens)
    dist = r / math.sin(fov / 2) * 1.05
    cd.clip_start, cd.clip_end = dist / 100, dist * 10
    pdir = os.path.join(SRC, "Previews")
    os.makedirs(pdir, exist_ok=True)
    paths = []
    for i, (az, el) in enumerate(views):
        a, e = math.radians(az), math.radians(el)
        cam.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        p = os.path.join(pdir, f"{asset}{('_' + tag) if tag else ''}_{i}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.world = old_world
    print("k3d: preview", paths)
    return paths


# ---------------------------------------------------------------- validate

def validate(fbx, expect_h=None):
    """FBX 를 빈 씬에 다시 불러와 Unity 기준 정보를 출력한다 (JSON). expect_h: 기대 높이(m), 15% 넘게 다르면 문제."""
    reset()
    bpy.ops.import_scene.fbx(filepath=fbx)
    js_path = os.path.splitext(fbx)[0] + ".json"
    js = json.load(open(js_path, encoding="utf-8")) if os.path.exists(js_path) else None
    rep = {"fbx": fbx, "json": bool(js), "objects": [], "problems": []}
    used = set()
    tris = 0
    for o in bpy.data.objects:
        e = {"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None}
        if o.type == 'MESH':
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
            e["tris"] = len(o.data.loop_triangles)
            e["uv_layers"] = len(o.data.uv_layers)
            e["materials"] = [m.name if m else None for m in o.data.materials]
            used |= {m.name for m in o.data.materials if m}
            if not o.data.uv_layers:
                rep["problems"].append(f"{o.name}: UV 없음")
            if any(m is None for m in o.data.materials) or not o.data.materials:
                rep["problems"].append(f"{o.name}: 빈 머티리얼 슬롯")
        if o.type == 'ARMATURE':
            e["bones"] = len(o.data.bones)
        rep["objects"].append(e)
    mn, mx = bounds([o for o in bpy.data.objects if o.parent is None]) if any(
        o.type == 'MESH' for o in bpy.data.objects) else (Vector(), Vector())
    # 다시 불러온 FBX 는 Blender 좌표(Z-up) 기준: Unity 크기 = (x, z, y)
    rep["size_m_unity_xyz"] = [round(mx.x - mn.x, 3), round(mx.z - mn.z, 3), round(mx.y - mn.y, 3)]
    rep["min_z"] = round(mn.z, 3)
    rep["tris"] = tris
    if expect_h:
        h = rep["size_m_unity_xyz"][1]
        if abs(h - expect_h) > 0.15 * expect_h:
            rep["problems"].append(f"높이 {h}m, 기대값 {expect_h}m")
    if abs(rep["min_z"]) > 0.02:
        rep["problems"].append(f"바닥(min_z={rep['min_z']})이 원점과 다름 — 원점이 바닥 중앙이 아니면 notes 에 이유를 적을 것")
    rep["actions"] = [a.name for a in bpy.data.actions]
    if js:
        names = {d["name"] for d in js["materials"]}
        for m in used:
            if m.split(".")[0] not in names:
                rep["problems"].append(f"JSON 에 머티리얼 없음: {m}")
        for d in js["materials"]:
            mname = d["name"]
            for k, rel in d.get("maps", {}).items():
                if not os.path.exists(os.path.join(ART, rel)):
                    rep["problems"].append(f"텍스처 없음: {mname}.{k} -> {rel}")
            if not mname.startswith("M_"):
                rep["problems"].append(f"머티리얼 이름 규칙 위반: {mname}")
    else:
        rep["problems"].append("JSON 없음")
    print("K3D_VALIDATE " + json.dumps(rep, ensure_ascii=False))
    return rep


if __name__ == "__main__" and "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if args and args[0] == "validate":
        f = args[1]
        validate(os.path.abspath(f), float(args[2]) if len(args) > 2 else None)

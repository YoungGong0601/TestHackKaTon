"""PH_ 프리팹용 내보내기 도구. 원본 .blend 를 열어 앞면·피벗·크기를 규격에 맞춘 정적 메시로 만든다."""
import bpy, os, sys, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d

CAT = "PH"


def load(category, asset):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(k3d.SRC, "Blender", category, asset + ".blend"))


def turn(deg):
    """Blender Z 회전 행렬. 에셋 정면은 -Y 다. 앞 -Z=180, 앞 +Z=0, 앞 +X=-90 (뒤집기 없음)."""
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def at_unity(x, y, z):
    """Unity 좌표 -> Blender 좌표."""
    return Vector((-x, -z, y))


def move_unity(x, y, z):
    return Matrix.Translation(at_unity(x, y, z))


def world_verts(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def posed(obj, name=None):
    """Armature 포함 평가 결과를 새 정적 메시로 (현재 포즈)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    o = bpy.data.objects.new(name or obj.name + "_Posed", me)
    bpy.context.scene.collection.objects.link(o)
    o.matrix_world = obj.matrix_world
    return o


def part(name, objs, M=Matrix.Identity(4), mark=True):
    """objs 를 복사해 메시 하나로 합치고 M 을 정점에 굽는다 (오브젝트 변환은 항등).
    mark=True: 합친 메시의 원래 정면(-Y) 중앙에 <name>_FrontMark 를 남겨 검사기가 방향을 확인한다."""
    bpy.context.view_layer.update()
    dup = []
    for o in objs:
        if o.type != 'MESH':
            continue
        c = o.copy()
        c.data = o.data.copy()
        c.animation_data_clear()
        bpy.context.scene.collection.objects.link(c)
        c.parent = None
        c.matrix_world = o.matrix_world
        for m in list(c.modifiers):
            c.modifiers.remove(m)
        c.data.transform(c.matrix_world)
        c.matrix_world = Matrix.Identity(4)
        dup.append(c)
    o = k3d.join(dup, name) if len(dup) > 1 else dup[0]
    o.name = o.data.name = name
    vs = [v.co for v in o.data.vertices]
    fm = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, min(v.y for v in vs),
                 (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
    o.data.transform(M)
    o.data.update()
    if mark:
        e = bpy.data.objects.new(name + "_FrontMark", None)
        bpy.context.scene.collection.objects.link(e)
        e.location = M @ fm
        e.parent = o
    return o


def finish(name, obj, extra=(), notes=None):
    """Assets/Art3D/Models/PH/<name>.fbx + .json 내보내기. 파생물이라 .blend 는 남기지 않는다."""
    k3d.export(name, CAT, [obj, *extra], notes=notes)
    b = os.path.join(k3d.SRC, "Blender", CAT, name + ".blend")
    if os.path.exists(b):
        os.remove(b)

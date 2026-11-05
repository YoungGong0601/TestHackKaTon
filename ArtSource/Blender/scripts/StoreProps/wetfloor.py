# StoreWetFloorSign: A자형 "미끄럼 주의" 노란 PP 입간판 0.6m (뒷판은 경첩 자식)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreWetFloorSign"
k3d.reset()
L, TW, BW, T = 0.6, 0.25, 0.30, 0.014     # 판 길이(경사), 위/아래 폭, 두께
ALPHA = math.radians(11)
HZ = L * math.cos(ALPHA) + 0.004           # 경첩 높이 (고무발 밑면이 바닥 z=0 에 닿게)
mY = plastic("M_StoreWetFloorSign_YellowSrc", (0.8, 0.5, 0.025), rough=0.42, grime=0.8, wear=0.5, scuff=0.8, fade=0.1)
mR = rubber("M_StoreWetFloorSign_RubberSrc")
mlab = label_mat("M_StoreWetFloorSign_Label", draw_labels(A), rough=0.38)


def panel(name, front):
    """경첩(원점)에서 아래로 늘어진 판. front=True 면 정면(-Y)을 봄."""
    bm = bmesh.new()
    s = -1 if front else 1
    pts = [(-BW / 2, -L), (BW / 2, -L), (TW / 2, -0.012), (TW / 2 - 0.012, 0), (-TW / 2 + 0.012, 0), (-TW / 2, -0.012)]
    fr = [bm.verts.new((x, s * T / 2, z)) for x, z in pts]
    bk = [bm.verts.new((x, -s * T / 2, z)) for x, z in pts]
    bm.faces.new(fr)
    bm.faces.new(list(reversed(bk)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(bm, name, mY)
    # 손잡이 구멍
    c = box("cut", (0.11, 0.1, 0.032), (0, 0, -0.05), mY, bev=0.012, seg=4)
    k3d.apply_all(c)
    bo = o.modifiers.new("Cut", 'BOOLEAN')
    bo.object, bo.operation = c, 'DIFFERENCE'
    k3d.apply_all(o)
    bpy.data.objects.remove(c, do_unlink=True)
    bevel(o, 0.003, 2)
    parts = [o]
    lab = quad(name + "_Lab", 0.23, 0.46, mlab, loc=(0, s * (T / 2 + 0.0007), -0.335))
    if not front:
        lab.rotation_euler = (0, 0, math.pi)
    parts.append(lab)
    for x in (-BW / 2 + 0.03, BW / 2 - 0.03):
        parts.append(box(name + "_Foot", (0.04, T + 0.006, 0.012), (x, 0, -L + 0.004), mR, bev=0.002))
    if front:
        for x in (-0.09, 0.09):
            parts.append(cyl(name + "_Knuckle", 0.008, 0.04, (x - 0.02, 0, 0), 16, mY, rot=(0, math.pi / 2, 0)))
        parts.append(cyl(name + "_Pin", 0.003, TW - 0.02, (-(TW - 0.02) / 2, 0, 0), 8, mR, bev=0.0005, seg=1,
                         rot=(0, math.pi / 2, 0)))
    for p in parts:
        ensure_uv(p)
    o = k3d.join(parts, name)
    o.rotation_euler = (-ALPHA if front else ALPHA, 0, 0)
    o.location = (0, 0, HZ)
    k3d.select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


fp = panel(A, True)
k3d.set_origin(fp, Vector((0, 0, 0)))
k3d.bake(fp, 512, keep=("M_StoreWetFloorSign_Label",))
bp = panel(A + "_PanelBack", False)
k3d.set_origin(bp, Vector((0, 0, HZ)))
k3d.bake(bp, 512, keep=("M_StoreWetFloorSign_Label",))
bp.parent = fp
bp.matrix_parent_inverse = fp.matrix_world.inverted()
socket(A + "_Socket_Grip", (0, 0, HZ - 0.05), fp)
print("STAT", A, "tris", scene_tris([fp]), "dims", tuple(round(x, 3) for x in fp.dimensions), "HZ", HZ)
k3d.export(A, "Store", [fp], notes=(
    "A자형 미끄럼 주의 입간판, 높이 0.6m, 바닥 폭 0.30m. 루트 = 앞판(정면 -Y). 자식 StoreWetFloorSign_PanelBack: 원점 = 윗변 경첩(높이 %.3fm), 로컬 X축 회전으로 접힘(-22도면 앞판과 겹침). "
    "인쇄면 M_StoreWetFloorSign_Label(512x1024) 양쪽 판 공용. 소켓: _Socket_Grip(손잡이 구멍)." % HZ))
k3d.preview(A, [fp])

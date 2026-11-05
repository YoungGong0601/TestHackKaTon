"""BuildingAcUnit: 벽걸이 에어컨 실외기 (거치대·냉매관·배수호스 포함). 프로토타입 ac_outdoor.glb 대체."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bld, k3d

A = "BuildingAcUnit"
k3d.reset()

# 원본 GLB 미리보기 (실제 높이 0.62m)
GLB = os.path.join(bld.HERE, "..", "..", "..", "_ref", "models", "ac_outdoor.glb")
old = [o for o in k3d.import_glb(GLB) if o.type == "MESH"] if os.path.exists(GLB) else []
if old:
    mn, mx = k3d.bounds(old)
    s = 0.62 / (mx.z - mn.z)
    for o in old:
        if o.parent is None:
            o.scale = (s, s, s)
    bpy.context.view_layer.update()
    k3d.preview(A, old, tag="before")
    for o in k3d.tree_of(old):
        bpy.data.objects.remove(o, do_unlink=True)

P = bld.palette()
dec = bld.Atlas(A, "Decal", (512, 256), "RGBA")
dm = bld.flat_img(f"M_{A}_Decal", dec.path, 0.5, alpha_clip=0.5)
lab = dec.add(300, 150, kind="sticker", bg="#eeece4", fg="#1d3f78", text="실외기", tel="고압가스 주의")

M = bld.Mesh()
# 원점 = 벽면(y=0), 가장 낮은 점(배수호스 끝) 바닥. -Y 가 벽 바깥.
bld.ac_unit(M, P, (0, 0, 0.405), pipe_up=0.45, pipe_side=0.25, decal=lab, decal_m=dm)

notes = ("벽에 거는 실외기. 원점 = 벽면(y=0) 위, 거치대 아래 끝 높이(바닥). Unity 에서 원점을 벽면에 붙이고 "
         "+Z(forward)가 벽 바깥을 보게 둔다. 본체 0.84x0.30x0.62m, 벽에서 0.12m 띄움. 냉매관은 벽 안으로 4cm 들어감. "
         "용도 구분: 버거대왕 매장 정면(StorefrontFacade_Socket_AC_1..3)은 StorefrontAC, 그 밖의 건물 벽·골목은 BuildingAcUnit "
         "(건물 5동에 굽혀 들어간 bld.ac_unit 과 같은 모양).")
ob, paths = bld.finish(A, M, atlases=[dec], bake_size=1024, notes=notes, ao=0.08, samples=48,
                       fp=((0.9, -2.2, 1.55), (0, 0, 0.75), 35))
paths += k3d.preview(A, [ob], views=((90, 0),), tag="side")   # 옆면: 사선 버팀대 확인
print("PREVIEWS", paths)

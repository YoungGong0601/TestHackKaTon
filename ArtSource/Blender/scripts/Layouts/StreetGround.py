# 거리 씬 바닥 메우기: 도로·보도 모듈 밖(건물 사이 틈, 길 양끝)에 허공이 보이지 않게 노면 3cm 아래에 큰 판 하나를 깐다.
# 좌표 = Street 레이아웃 좌표 그대로 (Blender = (x3, -z3, y3)): 레이아웃에서 (0,0,0), 회전 없이 둔다.
# 재질은 도로와 같은 M_Tile_Street_Asphalt (기존 T_Tile_Street_Asphalt_* 텍스처를 그대로 씀, 새 텍스처 없음).
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, k3d

k3d.reset()
A, CAT = "StreetGround", "LayoutStreet"
Z = -0.17                                   # 노면(z=-0.14) 3cm 아래: 모듈과 겹쳐 깜빡이지 않음
tdir = os.path.join(k3d.ART, "Textures", "Tile")
asphalt = k3d.tile("Street_Asphalt", maps={"diff": os.path.join(tdir, "T_Tile_Street_Asphalt_BaseColor.jpg")})
assert os.path.exists(os.path.join(tdir, "T_Tile_Street_Asphalt_MS.png")), "Street 텍스처 스크립트를 먼저 실행할 것"

bpy.ops.mesh.primitive_plane_add(size=1, location=(20, 40, Z))
g = bpy.context.active_object
g.name = A + "_Base"
g.scale = (700, 500, 1)                     # x -330..370, y -210..290 (안개 너머까지)
k3d.select([g])
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
g.data.materials.append(asphalt)
k3d.uv_world(g, 4.0)
k3d.set_origin(g, (0, 0, 0))                # 레이아웃 원점 = 씬 원점

notes = ("거리 씬 바닥 메우기 판 (700 x 500 m, z=-0.17 = 노면 3cm 아래). 원점 = 씬 원점이라 레이아웃에서 (0,0,0) 회전 없이 둔다. "
         "도로·보도·골목 모듈 밖(건물 사이 틈, 길 양끝 안개 속)에서 허공 대신 아스팔트가 보이게 한다. 재질은 도로와 같은 "
         "M_Tile_Street_Asphalt(월드 UV 4 m). min_z -0.17 은 의도한 값. Cast Shadows Off 권장.")
k3d.export(A, CAT, [g], notes=notes)

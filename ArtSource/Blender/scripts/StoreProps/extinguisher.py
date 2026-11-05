# StoreExtinguisher: 한국형 3.3kg ABC 소화기 + 빨간 "소화기" 받침대 (Poly Haven CC0 스캔 korean_fire_extinguisher_01)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreExtinguisher"
k3d.reset()
objs = k3d.import_glb(k3d.polyhaven("korean_fire_extinguisher_01", res="2k", kind="models"))
o = [x for x in objs if x.type == 'MESH'][0]
o.name = o.data.name = A

# 실물 0.659 m -> 0.60 m (프로토타입 0.56 기준 허용 범위, 비율 유지)
s = 0.60 / 0.659
o.scale = (s, s, s)
k3d.select([o])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 9.9k -> 약 7.7k 삼각형
d = o.modifiers.new("Dec", 'DECIMATE')
d.ratio = 0.78
k3d.apply_all(o)

# 이미지 노드는 원래 UV(UVMap)를 쓰도록 고정 (bake 가 만드는 UVAtlas 와 섞이지 않게)
for m in o.data.materials:
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'TEX_IMAGE' and not n.inputs['Vector'].is_linked:
            u = nt.nodes.new('ShaderNodeUVMap')
            u.uv_map = "UVMap"
            nt.links.new(u.outputs[0], n.inputs['Vector'])

# 라벨(paper)은 원본 2k 텍스처 그대로 유지 -> 작은 한글 글씨가 선명
lab = next(m for m in o.data.materials if m.name.endswith("_paper"))
lab.name = "M_StoreExtinguisher_Label"
p = k3d.principled(lab)
for sock in ('Roughness', 'Metallic', 'Normal'):
    for l in list(p.inputs[sock].links):
        lab.node_tree.links.remove(l)
p.inputs['Roughness'].default_value, p.inputs['Metallic'].default_value = 0.5, 0.0
src = p.inputs['Base Color'].links[0].from_node
while src.type != 'TEX_IMAGE':
    src = next(i for i in src.inputs if i.is_linked).links[0].from_node
lab.node_tree.links.new(src.outputs['Color'], p.inputs['Base Color'])
src.image.name = "T_StoreExtinguisher_Label"

# 원점: 받침대 바닥 중앙
vs = [v.co for v in o.data.vertices if v.co.z < 0.02]
c = Vector((sum(v.x for v in vs) / len(vs), sum(v.y for v in vs) / len(vs), 0))
k3d.set_origin(o, c)
o.location = (0, 0, 0)
bpy.context.view_layer.update()

# 소켓: 손잡이(위쪽 레버), 안전핀, 노즐(호스 끝)
co = [o.matrix_world @ v.co for v in o.data.vertices]
H = max(v.z for v in co)
top = [v for v in co if v.z > H - 0.03]
grip = sum(top, Vector()) / len(top)
pin = [v for v in co if H - 0.09 < v.z < H - 0.04]
pin = sum(pin, Vector()) / len(pin)
xmin = min(v.x for v in co if v.z > 0.2)
noz = [v for v in co if v.x < xmin + 0.015 and v.z > 0.2]
noz = sum(noz, Vector()) / len(noz)

k3d.bake(o, 1024, keep=("M_StoreExtinguisher_Label",))
socket(A + "_Socket_Grip", grip, o)
socket(A + "_Socket_Pin", pin, o)
socket(A + "_Socket_Nozzle", noz, o)
print("STAT", A, "H", round(H, 3), "tris", scene_tris([o]), "grip", grip, "pin", pin, "noz", noz)
k3d.export(A, "Store", [o], notes=(
    "Poly Haven CC0 스캔(korean_fire_extinguisher_01) 기반. 실물 0.659m 를 0.60m 로 균일 축소(프로토타입 0.56m 허용범위). "
    "빨간 '소화기' 받침대 포함: 프로토타입이 바닥(벽 앞)에 두므로 벽 브래킷 대신 받침대를 씀. 원점 = 받침대 바닥 중앙. "
    "라벨은 M_StoreExtinguisher_Label(원본 2k 텍스처, 굽지 않음). "
    "소켓: _Socket_Grip(손잡이 레버), _Socket_Pin(안전핀), _Socket_Nozzle(호스 노즐)."))
k3d.preview(A, [o])
k3d.preview(A, [o], views=((0, 8),), lens=35, tag="fp")

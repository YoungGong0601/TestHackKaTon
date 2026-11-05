# StoreStrawHolder: 테이블 냅킨통 옆 스테인리스 빨대통 (프로토타입 원기둥 r 0.018~0.022, h 0.1) + 종이 포장 빨대
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreStrawHolder"
k3d.reset()
H, R0, R1, WT = 0.1, 0.022, 0.018, 0.0012   # 높이, 바닥/입구 반지름, 벽 두께
mst = stainless("M_StoreStrawHolder_SteelSrc", 0.28, 'Z', smudge=0.5, grime=0.8)
mpap = plastic("M_StoreStrawHolder_PaperSrc", (0.8, 0.78, 0.72), rough=0.85, grime=0.2, wear=0.0, scuff=0.0)
# 종이 포장지: 빨간 사선 줄무늬 인쇄 (오브젝트 좌표 기울인 밴드)
_nt, _p = mpap.node_tree, k3d.principled(mpap)
w = _nt.nodes.new('ShaderNodeTexWave')
w.wave_type, w.bands_direction = 'BANDS', 'DIAGONAL'
w.inputs['Scale'].default_value = 60
_nt.links.new(coord(_nt), w.inputs['Vector'])
stripe = mrange(_nt, w.outputs['Factor'], 0.82, 0.86)
_nt.links.new(mix(_nt, stripe, _p.inputs['Base Color'].links[0].from_socket, (0.45, 0.04, 0.03)), _p.inputs['Base Color'])
mR = rubber("M_StoreStrawHolder_FootSrc")

# 컵: 말린 입구 + 두께 있는 벽 + 바닥 고무 링
cup = lathe(A + "_Cup", [(0, 0.003), (R0 - 0.002, 0.003), (R0, 0.005), (R1, H - 0.003), (R1 + 0.0015, H - 0.0005),
                         (R1, H), (R1 - WT, H - 0.002), (R0 - WT - 0.002, 0.008), (0, 0.008)], segs=32, mat=mst)
parts = [cup, lathe(A + "_Foot", [(0, 0), (R0 - 0.003, 0), (R0 - 0.0015, 0.0015), (R0 - 0.002, 0.0035), (0, 0.0035)], segs=32, mat=mR)]
# 빨대 8개: 가운데 1개 + 둘레 7개가 입구에 기대 살짝 벌어짐 (컵 벽/서로 안 뚫게 기울기 제한)
rnd = random.Random(3)
for i in range(8):
    a = 2 * math.pi * i / 7 + rnd.uniform(-0.15, 0.15)
    r, tilt = (0.0, 0.01) if i == 7 else (0.0085, rnd.uniform(0.025, 0.045))
    s = cyl(f"{A}_Straw{i}", 0.0032, rnd.uniform(0.2, 0.22), (0, 0, 0), 8, mpap, bev=0.0006, seg=1)
    s.rotation_euler = (-tilt * math.sin(a), tilt * math.cos(a), 0)   # 바깥(a 방향)으로 기울임
    s.location = (r * math.cos(a), r * math.sin(a), 0.009)
    parts.append(s)
for q in parts:
    ensure_uv(q)
o = k3d.join(parts, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 512)
socket(A + "_Socket_Pull", (0, 0, H + 0.09), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "테이블 위 스테인리스 빨대통 Ø44 x 0.1m + 종이 포장 빨대 8개(전체 높이 약 0.22m). 프로토타입 냅킨통 옆 비닐 원기둥 자리: "
    "StoreTable / StoreTable4 의 _Socket_Napkin 에서 +X 로 0.09m. 원점 = 바닥 중앙. 소켓: _Socket_Pull(빨대 윗끝)."))
k3d.preview(A, [o], res=(900, 1200))  # 세로로 긴 물건: 가로 4:3 이면 위가 잘림

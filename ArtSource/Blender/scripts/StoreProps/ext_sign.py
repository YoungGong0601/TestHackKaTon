# StoreExtinguisherSign: 벽 부착 "소화기" 위치 표지 (빨간 아크릴 0.24x0.12, 양면테이프)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreExtinguisherSign"
k3d.reset()
W, H, T = 0.24, 0.12, 0.004
macr = plastic("M_StoreExtinguisherSign_AcrylSrc", (0.5, 0.025, 0.018), rough=0.22, grime=0.5, wear=0.4, scuff=0.3)
mtape = plastic("M_StoreExtinguisherSign_TapeSrc", (0.7, 0.7, 0.68), rough=0.8, grime=0.6, wear=0.0, scuff=0.0)
plate = box(A + "_Plate", (W, T, H), (0, -T / 2 - 0.0012, H / 2), macr, bev=0.0012, seg=2)
tape = box(A + "_Tape", (W - 0.03, 0.0012, H - 0.03), (0, -0.0006, H / 2), mtape, bev=0)
lab = quad(A + "_Face", W - 0.004, H - 0.004, label_mat("M_StoreExtinguisherSign_Label", draw_labels(A), rough=0.3),
           loc=(0, -T - 0.0012 - 0.0006, H / 2))
for p in (plate, tape, lab):
    ensure_uv(p)
o = k3d.join([plate, tape, lab], A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 512, keep=("M_StoreExtinguisherSign_Label",))
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "벽 부착 소화기 표지 0.24x0.12m. 원점 = 판 아래 가운데, 뒷면(벽) = y 0 평면, 정면 -Y. "
    "프로토타입 위치: 소화기 바로 위 벽, 판 중심 높이 1.05m -> 원점 높이 0.99m. 인쇄면 M_StoreExtinguisherSign_Label(1024x512)."))
k3d.preview(A, [o])

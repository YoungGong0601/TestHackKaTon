# StoreNapkinDispenser: 테이블 위 양면 스테인리스 냅킨통 (0.09 x 0.07 x 0.12)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreNapkinDispenser"
k3d.reset()
W, D, H = 0.09, 0.07, 0.12
mst = stainless("M_StoreNapkinDispenser_SteelSrc", 0.26, 'Z', smudge=0.6, grime=0.7)
# 기름 지문/손때를 색에도 넣고(stainless()는 거칠기에만 넣음) 바닥 띠에 때
_nt, _p = mst.node_tree, k3d.principled(mst)
_v = coord(_nt)
_sm = op(_nt, 'MULTIPLY', mrange(_nt, noise(_nt, 40, 5, 0.7, vec=_v, distortion=0.3), 0.56, 0.7), 0.22)  # 대리석 무늬처럼 보이지 않게 약하게
_sep = _nt.nodes.new('ShaderNodeSeparateXYZ')
_nt.links.new(_nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], _sep.inputs[0])
_low = op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], 0.022, 0.005), mrange(_nt, noise(_nt, 70, 4, vec=_v), 0.3, 0.7))
_bc = mix(_nt, _sm, _p.inputs['Base Color'].links[0].from_socket, (0.3, 0.29, 0.27))
_bc = mix(_nt, op(_nt, 'MULTIPLY', _low, 0.85), _bc, (0.085, 0.075, 0.06))
_nt.links.new(_bc, _p.inputs['Base Color'])
_nt.links.new(fmix(_nt, op(_nt, 'MAXIMUM', _sm, _low), _p.inputs['Roughness'].links[0].from_socket, 0.62), _p.inputs['Roughness'])
mpap = plastic("M_StoreNapkinDispenser_PaperSrc", (0.78, 0.77, 0.73), rough=0.9, grime=0.3, wear=0.0, scuff=0.0)
mR = rubber("M_StoreNapkinDispenser_FootSrc")
body = box(A + "_Body", (W, D, H - 0.004), (0, 0, 0.004 + (H - 0.004) / 2), mst, bev=0.006, seg=3)
cut = []
for s in (-1, 1):  # 앞/뒤 창 (냅킨 보임)
    cut.append(box("cut", (0.068, 0.01, 0.062), (0, s * D / 2, 0.052), mpap, bev=0.008, seg=3))
cutter = k3d.join(cut, "cutter")
bo = body.modifiers.new("Cut", 'BOOLEAN')
bo.object, bo.operation = cutter, 'DIFFERENCE'
try:
    bo.material_mode = 'TRANSFER'
except Exception:
    pass
# 베벨(이미 있음) 뒤에 불리언이 오도록 순서 유지
k3d.apply_all(body)
bpy.data.objects.remove(cutter, do_unlink=True)
parts = [body]
# 앞/뒤 창 밖으로 살짝 빠져나온 냅킨 한 장씩
for side in (-1, 1):
    bm = bmesh.new()
    rows = []
    for k in range(5):
        t = k / 4
        rows.append([bm.verts.new((x, side * (D / 2 - 0.003 + 0.02 * t), 0.07 - 0.03 * t - 0.012 * t * t)) for x in (-0.026, 0.026)])
    for r0, r1 in zip(rows, rows[1:]):
        bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
    tongue = from_bm(bm, f"{A}_Tongue{side}", mpap)
    sol = tongue.modifiers.new("S", 'SOLIDIFY')
    sol.thickness = 0.0012
    for p in tongue.data.polygons:
        p.use_smooth = True
    parts.append(tongue)
for x in (-W / 2 + 0.012, W / 2 - 0.012):
    for y in (-D / 2 + 0.012, D / 2 - 0.012):
        parts.append(cyl(A + "_Foot", 0.006, 0.004, (x, y, 0), 12, mR, bev=0.001, seg=1))
lab = quad(A + "_Lab", 0.064, 0.032, label_mat("M_StoreNapkinDispenser_Label", draw_labels(A), rough=0.35),
           loc=(0, -D / 2 - 0.0006, 0.1))
parts.append(lab)
for p in parts:
    ensure_uv(p)
o = k3d.join(parts, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 512, keep=("M_StoreNapkinDispenser_Label",))
socket(A + "_Socket_Pull", (0, -D / 2 - 0.02, 0.05), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "테이블 위 양면 냅킨통 0.09x0.07x0.12m (프로토타입 테이블 모서리 스틸 박스). StoreTable 의 _Socket_Napkin 에 둔다. "
    "라벨 M_StoreNapkinDispenser_Label(512x256). 소켓: _Socket_Pull(냅킨 뽑는 곳, 앞면)."))
k3d.preview(A, [o])

# StoreTrashStation: 퇴식구/분리수거함 0.76m. 우드 라미네이트 함체 + 스테인리스 트레이 상판(턱) + 투입구 3개(일반쓰레기/음식물/컵·빨대, 스윙 덮개)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreTrashStation"
k3d.reset()
W, D, TZ = 1.0, 0.5, 0.73          # 함체 폭/깊이, 상판 밑면 높이
FY = -D / 2                        # 함체 앞면 y
OX = (-0.32, 0.0, 0.32)            # 투입구 x
OZ, OW, OH = 0.52, 0.24, 0.16      # 투입구 중심 높이/크기

# 머티리얼
mwood = wood("M_StoreTrashStation_WoodSrc", 0.8, tint=(0.82, 0.7, 0.56), rough=0.45, wipe=0.2, edge_dark=0.45, scratch=0.5)
# 음식물 투입구 아래로 흘러내린 음료 자국 (끈적하게 번들거림)
nt, p = mwood.node_tree, k3d.principled(mwood)
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Object'], sep.inputs[0])
win = op(nt, 'MULTIPLY', mrange(nt, op(nt, 'ABSOLUTE', sep.outputs['X']), 0.13, 0.05),
         mrange(nt, sep.outputs['Z'], 0.29, 0.1))
drip = op(nt, 'MULTIPLY', win, mrange(nt, noise(nt, 1, 3, vec=coord(nt, 'Object', (60, 60, 3))), 0.45, 0.62))
nt.links.new(mix(nt, op(nt, 'MULTIPLY', drip, 0.7), p.inputs['Base Color'].links[0].from_socket, (0.09, 0.05, 0.02)),
             p.inputs['Base Color'])
nt.links.new(fmix(nt, drip, p.inputs['Roughness'].links[0].from_socket, 0.15), p.inputs['Roughness'])

msteel = stainless("M_StoreTrashStation_TopSrc", 0.28, 'X', smudge=0.9, grime=0.8)
mblack = plastic("M_StoreTrashStation_BlackSrc", (0.018, 0.018, 0.018), rough=0.5, grime=0.6, wear=0.5, scuff=0.4)
mkick = plastic("M_StoreTrashStation_KickSrc", (0.02, 0.02, 0.02), rough=0.6, grime=1.0, wear=0.6, scuff=1.0)
minner = k3d.mat("M_StoreTrashStation_InnerSrc", (0.006, 0.006, 0.006), 0.8)
mlock = stainless("M_StoreTrashStation_LockSrc", 0.25, 'Z', smudge=0.3)

parts = []
# 함체: 투입구와 패널 홈을 불리언으로 파냄
body = box(A + "_Body", (W, D, TZ - 0.08), (0, 0, 0.08 + (TZ - 0.08) / 2), mwood, bev=0.004, seg=2)
cut = []
for x in OX:
    cut.append(box("cut", (OW, 0.36, OH), (x, FY + 0.08, OZ), minner, bev=0))  # 깊이 18cm 투입 통로
cut.append(box("cut", (W - 0.06, 0.008, 0.004), (0, FY, 0.29), minner, bev=0))
for x in (-0.165, 0.165):
    cut.append(box("cut", (0.004, 0.008, 0.2), (x, FY, 0.185), minner, bev=0))
cutter = k3d.join(cut, A + "_Cutter")
bo = body.modifiers.new("Cut", 'BOOLEAN')
bo.object, bo.operation = cutter, 'DIFFERENCE'
try:
    bo.material_mode = 'TRANSFER'
except Exception:
    pass
k3d.apply_all(body)
bpy.data.objects.remove(cutter, do_unlink=True)
parts.append(body)

# 걸레받이(안쪽으로 들어간 킥 플레이트)
parts.append(box(A + "_Kick", (W - 0.04, D - 0.06, 0.08), (0, 0.01, 0.04), mkick, bev=0.003))
# 스테인리스 상판 + 뒤/옆 턱 (트레이 놓는 선반)
parts.append(box(A + "_Top", (W + 0.02, D + 0.02, 0.03), (0, 0, TZ + 0.015), msteel, bev=0.003, seg=3))
parts.append(box(A + "_LipB", (W + 0.02, 0.012, 0.025), (0, D / 2 + 0.004, TZ + 0.0425), msteel, bev=0.003))
for s in (-1, 1):
    parts.append(box(f"{A}_LipS{s}", (0.012, D + 0.02, 0.025), (s * (W / 2 + 0.004), 0, TZ + 0.0425), msteel, bev=0.003))
# 투입구 검정 테두리
for x in OX:
    for (sx, sz, dx, dz) in ((OW + 0.03, 0.015, 0, (OH + 0.015) / 2), (OW + 0.03, 0.015, 0, -(OH + 0.015) / 2),
                             (0.015, OH, (OW + 0.015) / 2, 0), (0.015, OH, -(OW + 0.015) / 2, 0)):
        parts.append(box(f"{A}_Bezel", (sx, 0.01, sz), (x + dx, FY - 0.004, OZ + dz), mblack, bev=0.002))
# 아래 패널 열쇠 구멍
for x in (-0.33, 0.0, 0.33):
    lk = cyl(f"{A}_Lock", 0.009, 0.006, (x, FY + 0.002, 0.265), 20, mlock, bev=0.001, rot=(math.pi / 2, 0, 0))
    parts.append(lk)
    parts.append(box(f"{A}_Key", (0.0015, 0.003, 0.008), (x, FY - 0.0042, 0.265), minner, bev=0))

# 라벨 (Pillow 아틀라스 2048x1024)
mlab = label_mat("M_StoreTrashStation_Label", draw_labels(A), rough=0.4)
for i, x in enumerate(OX):
    u0 = 682 * i / 2048
    parts.append(quad(f"{A}_Lab{i}", 0.24, 0.12, mlab, (u0, 1 - 340 / 1024, u0 + 680 / 2048, 1.0), (x, FY - 0.0008, 0.36)))
parts.append(quad(A + "_LabFascia", 0.98, 0.0957, mlab, (0, 1 - 548 / 1024, 1, 1 - 348 / 1024), (0, FY - 0.0008, 0.672)))
parts.append(quad(A + "_LabTray", 0.2, 0.118, mlab, (0, 1 - 960 / 1024, 680 / 2048, 1 - 560 / 1024),
                  (0.3, 0.12, TZ + 0.0308), (-math.pi / 2, 0, 0)))
parts.append(quad(A + "_LabHand", 0.12, 0.0706, mlab, (700 / 2048, 1 - 960 / 1024, 1368 / 2048, 1 - 560 / 1024),
                  (0.33, FY - 0.0008, 0.2)))
for p_ in parts:
    ensure_uv(p_)
o = k3d.join(parts, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 1024, keep=("M_StoreTrashStation_Label",))

# 스윙 덮개 (윗변 경첩 = 원점, 로컬 X축 회전: +각도면 안쪽으로 밀림)
flaps = []
for nm, x in zip(("General", "Food", "Cup"), OX):
    # 덮개: 진회색 ABS. 아래 1/3(미는 자리)에 손때 (bake 때 원점 = 경첩이라 로컬 z 기준)
    mf = plastic(f"M_{A}_Flap{nm}Src", (0.032, 0.032, 0.034), rough=0.4, grime=0.5, wear=0.25, scuff=0.6)
    _nt, _p = mf.node_tree, k3d.principled(mf)
    _sep = _nt.nodes.new('ShaderNodeSeparateXYZ')
    _nt.links.new(_nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], _sep.inputs[0])
    _low = op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], -0.08, -0.13),
              mrange(_nt, noise(_nt, 28, 5, 0.65, vec=coord(_nt), distortion=0.6), 0.38, 0.66))
    _nt.links.new(mix(_nt, op(_nt, 'MULTIPLY', _low, 0.7), _p.inputs['Base Color'].links[0].from_socket, (0.085, 0.072, 0.055)),
                  _p.inputs['Base Color'])
    _nt.links.new(fmix(_nt, _low, _p.inputs['Roughness'].links[0].from_socket, 0.22), _p.inputs['Roughness'])
    mr = rubber(f"M_{A}_Flap{nm}RubSrc")
    hz = OZ + OH / 2 - 0.006
    fy = FY + 0.012
    pl = box(f"{A}_FP", (OW - 0.008, 0.003, OH - 0.012), (x, fy, hz - (OH - 0.012) / 2), mf, bev=0.001)
    rod = cyl(f"{A}_FR", 0.004, OW - 0.004, (x - (OW - 0.004) / 2, fy, hz), 12, mf, bev=0.0008, seg=1, rot=(0, math.pi / 2, 0))
    rb = box(f"{A}_FB", (OW - 0.008, 0.006, 0.012), (x, fy, hz - (OH - 0.012) + 0.004), mr, bev=0.002)
    push = quad(f"{A}_FD", 0.05, 0.05, mlab, (1400 / 2048, 1 - 880 / 1024, 1700 / 2048, 1 - 580 / 1024),
                (x, fy - 0.0021, hz - 0.098))  # '미세요' 데칼
    for q in (pl, rod, rb, push):
        ensure_uv(q)
    f = k3d.join([pl, rod, rb, push], f"{A}_Flap{nm}")
    k3d.set_origin(f, Vector((x, fy, hz)))
    k3d.bake(f, 256, keep=("M_StoreTrashStation_Label",))
    f.parent = o
    f.matrix_parent_inverse = o.matrix_world.inverted()
    flaps.append(f)

for nm, x in zip(("General", "Food", "Cup"), OX):
    socket(f"{A}_Socket_{nm}", (x, FY - 0.03, OZ), o)
socket(A + "_Socket_TrayReturn", (-0.15, 0.0, TZ + 0.03), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "퇴식구 겸 분리수거함 1.0x0.5m, 높이 0.785m(상판 턱 포함). trashcan.glb 와 프로토타입 x=2.75 절차 '쓰레기/트레이' 카운터를 모두 대체한다 "
    "(카운터 자리에 1개 배치, x=4.25 휴지통 자리는 제거). 프로토타입 트레이 4장 더미는 Food 그룹 FoodTray 를 _Socket_TrayReturn 에 쌓는다. "
    "상판은 트레이 반납 선반(스테인리스, 뒤/옆 턱). 앞면 투입구 3개: 일반쓰레기 / 음식물 / 컵·빨대. "
    "덮개 자식: StoreTrashStation_FlapGeneral/FlapFood/FlapCup(진회색 ABS, '미세요/PUSH' 데칼), 원점 = 윗변 경첩, 로컬 X축 회전(+ 안쪽으로 밀림, 0~70도). "
    "라벨 M_StoreTrashStation_Label(2048x1024, 굽지 않음). "
    "소켓: _Socket_General/_Food/_Cup(각 투입구 앞), _Socket_TrayReturn(상판 트레이 놓는 곳)."))
k3d.preview(A, [o])
k3d.preview(A, [o], views=((0, 20),), lens=35, tag="fp")

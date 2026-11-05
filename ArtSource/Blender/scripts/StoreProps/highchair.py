# StoreHighChair: 원목 유아용 하이체어 (프로토타입 le(): 좌판 0.75m, 등받이 1.03m, 팔걸이, 앞 가드, 발판, 벌어진 다리 4개)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
from mathutils import Matrix

A = "StoreHighChair"
k3d.reset()
SEAT = 0.7525                       # 좌판 윗면
B0, T0, LH = 0.205, 0.135, 0.74     # 다리 바닥/윗끝 중심 반폭, 다리 높이


def leg_xy(z):
    """높이 z 에서 다리 중심 반폭 (바닥에서 바깥으로 벌어짐)."""
    return B0 + (T0 - B0) * z / LH


def rod(name, p0, p1, r0, r1, mat, segs=12, bev=0.0015):
    """p0 -> p1 원뿔대 막대 (r0 = p0 쪽 반지름)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r0, radius2=r1, depth=d.length)
    bmesh.ops.translate(bm, vec=(0, 0, d.length / 2), verts=bm.verts)
    M = Matrix.Translation(p0) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    o = from_bm(bm, name, mat)
    if bev:
        bevel(o, bev, 2)
    else:
        k3d.smooth(o, 40)
    return o


# 너도밤나무 원목 + 투명 래커: 닦인 광택, 모서리 손때, 좌판/가드에 끈적한 음식 얼룩
mwood = wood("M_StoreHighChair_WoodSrc", 0.5, tint=(1.0, 0.86, 0.66), rough=0.4, wipe=0.25, wear=0.5, edge_dark=0.4, scratch=0.45)
nt, p = mwood.node_tree, k3d.principled(mwood)
gn = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Normal'], gn.inputs[0])
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], sep.inputs[0])
zone = op(nt, 'MULTIPLY', mrange(nt, gn.outputs['Z'], 0.6, 0.9), mrange(nt, sep.outputs['Z'], 0.70, 0.74))  # 위를 보는 좌판/팔걸이/가드
spots = op(nt, 'MULTIPLY', mrange(nt, voronoi(nt, 38, coord(nt)), 0.12, 0.05),
           mrange(nt, noise(nt, 6, 3, vec=coord(nt)), 0.5, 0.62))
stain = op(nt, 'MULTIPLY', zone, spots)
nt.links.new(mix(nt, op(nt, 'MULTIPLY', stain, 0.75), p.inputs['Base Color'].links[0].from_socket, (0.16, 0.08, 0.03)),
             p.inputs['Base Color'])
nt.links.new(fmix(nt, stain, p.inputs['Roughness'].links[0].from_socket, 0.12), p.inputs['Roughness'])
mfelt = rubber("M_StoreHighChair_GlideSrc", (0.03, 0.028, 0.026), 0.9)

parts = []
# 다리 4개: 바닥 반폭 0.205 -> 윗끝 0.135 (프로토타입 ±0.1rad 벌어짐), 끝에 플라스틱 발굽
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(rod(f"{A}_Leg", (sx * leg_xy(0.004), sy * leg_xy(0.004), 0.004),
                         (sx * T0, sy * T0, LH), 0.021, 0.016, mwood, 16))
        parts.append(cyl(f"{A}_Glide", 0.019, 0.006, (sx * leg_xy(0), sy * leg_xy(0), 0), 16, mfelt, bev=0.002))
# 다리 가로대: 옆/뒤 둥근 막대 + 앞 발판
zs = 0.22
for s in (-1, 1):
    parts.append(rod(f"{A}_RailS", (s * leg_xy(zs), -leg_xy(zs), zs), (s * leg_xy(zs), leg_xy(zs), zs), 0.009, 0.009, mwood, 10, 0.0))
parts.append(rod(A + "_RailB", (-leg_xy(zs), leg_xy(zs), zs), (leg_xy(zs), leg_xy(zs), zs), 0.009, 0.009, mwood, 10, 0.0))
zf = 0.30
parts.append(box(A + "_Foot", (0.40, 0.05, 0.016), (0, -leg_xy(zf) - 0.019 + 0.003 - 0.025, zf), mwood, bev=0.003))  # 다리 앞면에 고정
# 좌판 밑 에이프런 + 좌판
za = 0.708
for s in (-1, 1):
    parts.append(box(f"{A}_ApronX{s}", (2 * leg_xy(za), 0.016, 0.04), (0, s * leg_xy(za), za), mwood, bev=0.002))
    parts.append(box(f"{A}_ApronY{s}", (0.016, 2 * leg_xy(za), 0.04), (s * leg_xy(za), 0, za), mwood, bev=0.002))
parts.append(box(A + "_Seat", (0.30, 0.30, 0.025), (0, 0, SEAT - 0.0125), mwood, bev=0.006, seg=3))
# 등받이 기둥 2개 + 위 등판 + 가운데 살
for s in (-1, 1):
    parts.append(box(f"{A}_Post{s}", (0.026, 0.026, 1.04 - SEAT + 0.01), (s * 0.135, 0.135, (SEAT - 0.01 + 1.04) / 2), mwood, bev=0.004))
parts.append(box(A + "_BackTop", (0.30, 0.022, 0.1), (0, 0.15, 0.98), mwood, bev=0.006, seg=3))
parts.append(box(A + "_BackSlat", (0.26, 0.016, 0.05), (0, 0.142, 0.825), mwood, bev=0.004))
# 팔걸이 + 앞 팔걸이 기둥 + 앞 가드(가로대) + 가운데 다리 사이 기둥
for s in (-1, 1):
    parts.append(box(f"{A}_Arm{s}", (0.024, 0.30, 0.022), (s * 0.142, -0.01, 0.92), mwood, bev=0.005, seg=3))
    parts.append(rod(f"{A}_ArmPost{s}", (s * 0.139, -0.115, SEAT - 0.004), (s * 0.139, -0.115, 0.91), 0.0095, 0.0095, mwood, 12, 0.0))
parts.append(box(A + "_Guard", (0.33, 0.026, 0.024), (0, -0.15, 0.92), mwood, bev=0.006, seg=3))
parts.append(rod(A + "_Crotch", (0, -0.125, SEAT - 0.004), (0, -0.14, 0.91), 0.011, 0.011, mwood, 12, 0.0))
# 나무 다보 마개(팔걸이 앞끝 위)
for s in (-1, 1):
    parts.append(cyl(f"{A}_Plug{s}", 0.006, 0.0008, (s * 0.139, -0.115, 0.931), 12, mwood, bev=0.0003, seg=1))

for q in parts:
    ensure_uv(q)
o = k3d.join(parts, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 1024)
socket(A + "_Socket_Sit", (0, -0.01, SEAT), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "원목(너도밤나무, 래커) 유아용 하이체어. 좌판 윗면 0.75m, 등받이 윗끝 1.03m, 바닥 폭 0.45m(다리가 바닥으로 벌어짐). "
    "팔걸이 + 앞 가드 + 가운데 기둥, 앞 발판(0.30m), 다리 가로대, 플라스틱 발굽. 좌판/가드 윗면에 음식 얼룩. "
    "원점 = 바닥 중앙, 정면 -Y. 프로토타입 le() 위치: (-1.9, 0, 3.1) Y 회전 0.6rad, (-2.25, 0, 3.25) Y 회전 0.9rad. "
    "소켓: _Socket_Sit(좌판 중앙)."))
k3d.preview(A, [o], res=(900, 1200))  # 세로로 긴 물건: 가로 4:3 이면 위가 잘림

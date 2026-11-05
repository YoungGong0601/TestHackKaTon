# StorePlant: 매장 구석 파키라 화분 1.1m (Poly Haven CC0 pachira_aquatica_01 c) + 화분/받침/마사토 + 빛바랜 개업 리본
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
import random

A = "StorePlant"
VAR = os.environ.get("PLANT_VAR", "c")
k3d.reset()
gl = k3d.polyhaven("pachira_aquatica_01", res="1k", kind="models")
objs = k3d.import_glb(gl)
plant = [x for x in objs if x.type == 'MESH' and x.name.endswith("_" + VAR)]
for x in objs:
    if x not in plant:
        bpy.data.objects.remove(x, do_unlink=True)
tdir = os.path.join(os.path.dirname(gl), "textures")


def ph_mat(name, part, rough):
    """원본 잎/줄기 텍스처를 그대로 쓰는 유지 머티리얼 (Base Color, Normal 직결)."""
    m, nt, p = new_mat(name)
    for k, sock in (("diff", 'Base Color'), ("nor_gl", None)):
        im = k3d.load_image(os.path.join(tdir, f"pachira_aquatica_01_{part}_{k}_1k.jpg"),
                            f"T_{A}_{part.capitalize()}_{'BaseColor' if k == 'diff' else 'Normal'}", k != "diff")
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = im
        if sock:
            nt.links.new(n.outputs['Color'], p.inputs[sock])
        else:
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(n.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = rough
    return m


mleaf = k3d.flag(ph_mat("M_StorePlant_Leaves", "leaves", 0.55), double_sided=True)
mbark = ph_mat("M_StorePlant_Bark", "bark", 0.8)
leaves = next(x for x in plant if "leaves" in x.name)
bark = next(x for x in plant if "bark" in x.name)
for x, m, r in ((leaves, mleaf, 0.26), (bark, mbark, 0.42)):  # 소품 예산 8k 이하
    x.data.materials.clear()
    x.data.materials.append(m)
    x.parent = None
    k3d.select([x])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    d = x.modifiers.new("Dec", 'DECIMATE')
    d.ratio = r
    k3d.apply_all(x)

# 줄기 밑동 중심을 원점으로, 높이 맞추기
vs = [v.co for v in bark.data.vertices]
zmin = min(v.z for v in vs)
base = [v for v in vs if v.z < zmin + 0.04]
cx, cy = sum(v.x for v in base) / len(base), sum(v.y for v in base) / len(base)
ztop = max(max(v.co.z for v in leaves.data.vertices), max(v.z for v in vs))
POT_H, SOIL = 0.32, 0.29
s = (1.1 - (SOIL - 0.02)) / (ztop - zmin)
for x in (leaves, bark):
    x.location = (-cx * s, -cy * s, SOIL - 0.02 - zmin * s)
    x.scale = (s, s, s)
    k3d.select([x])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 화분: 살짝 좁아지는 FRP 원통 화분 (말린 테두리)
mpot = plastic("M_StorePlant_PotSrc", (0.055, 0.052, 0.05), rough=0.55, grime=0.8, wear=0.6, scuff=0.6, fade=0.12)
# 스톤 FRP 반점 + 아래쪽 먼지
_nt = mpot.node_tree
_p = k3d.principled(mpot)
_v = coord(_nt)
_sp = mrange(_nt, voronoi(_nt, 900, _v), 0.0, 0.18, 1.0, 0.0)
_bc = _p.inputs['Base Color'].links[0].from_socket
_bc = mix(_nt, op(_nt, 'MULTIPLY', _sp, 0.5), _bc, (0.32, 0.31, 0.29))
_tc = _nt.nodes.new('ShaderNodeTexCoord')
_sep = _nt.nodes.new('ShaderNodeSeparateXYZ')
_nt.links.new(_tc.outputs['Object'], _sep.inputs[0])
_dust = op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], 0.12, 0.0), mrange(_nt, noise(_nt, 12, 4, vec=_v), 0.35, 0.7))
_bc = mix(_nt, op(_nt, 'MULTIPLY', _dust, 0.6), _bc, (0.2, 0.18, 0.15))
# 물받침에 고였던 물 높이의 석회 물때 띠
_lime = op(_nt, 'MULTIPLY', op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], 0.012, 0.016), mrange(_nt, _sep.outputs['Z'], 0.028, 0.022)),
           mrange(_nt, noise(_nt, 40, 4, vec=_v), 0.3, 0.6))
_bc = mix(_nt, op(_nt, 'MULTIPLY', _lime, 0.75), _bc, (0.42, 0.41, 0.38))
_nt.links.new(_bc, _p.inputs['Base Color'])
R1, R0 = 0.17, 0.135
pot = lathe(A + "_Pot", [(0, 0.012), (R0 - 0.01, 0.012), (R0, 0.02), (R0 + 0.002, 0.03),
                         (R1 - 0.009, POT_H - 0.075), (R1 - 0.011, POT_H - 0.07), (R1 - 0.011, POT_H - 0.062), (R1 - 0.006, POT_H - 0.057),
                         (R1 - 0.004, POT_H - 0.02), (R1 + 0.006, POT_H - 0.012), (R1 + 0.007, POT_H - 0.002),
                         (R1 + 0.002, POT_H + 0.002), (R1 - 0.008, POT_H - 0.002), (R1 - 0.012, POT_H - 0.03),
                         (R1 - 0.02, SOIL - 0.04), (0, SOIL - 0.04)], segs=48, mat=mpot)
# 물받침
msau = plastic("M_StorePlant_SaucerSrc", (0.06, 0.06, 0.058), rough=0.4, grime=0.9, wear=0.3, scuff=0.6)
# 물받침: 안쪽 벽 물 높이 석회 링 + 바닥 물때
_nt, _p = msau.node_tree, k3d.principled(msau)
_v = coord(_nt)
_sep = _nt.nodes.new('ShaderNodeSeparateXYZ')
_nt.links.new(_nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], _sep.inputs[0])
_ring = op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], 0.009, 0.012), mrange(_nt, _sep.outputs['Z'], 0.017, 0.014))
_ring = op(_nt, 'MAXIMUM', _ring, op(_nt, 'MULTIPLY', mrange(_nt, _sep.outputs['Z'], 0.011, 0.0085), 0.45))
_ring = op(_nt, 'MULTIPLY', _ring, mrange(_nt, noise(_nt, 35, 5, vec=_v), 0.3, 0.62))
_nt.links.new(mix(_nt, op(_nt, 'MULTIPLY', _ring, 0.8), _p.inputs['Base Color'].links[0].from_socket, (0.4, 0.39, 0.36)), _p.inputs['Base Color'])
_nt.links.new(fmix(_nt, _ring, _p.inputs['Roughness'].links[0].from_socket, 0.85), _p.inputs['Roughness'])
sau = lathe(A + "_Saucer", [(0, 0), (0.15, 0), (0.158, 0.004), (0.162, 0.018), (0.156, 0.02), (0.15, 0.008),
                            (0.13, 0.008), (0, 0.008)], segs=48, mat=msau)
# 흙: 마사토(화강암 풍화토) 2~5mm 알갱이. 셀마다 다른 광물 색 + 알갱이 사이 어두운 틈 + 줄기 둘레 젖은 링
m, nt, p = new_mat("M_StorePlant_SoilSrc")
v = coord(nt)
cr = nt.nodes.new('ShaderNodeValToRGB')
cr.color_ramp.interpolation = 'CONSTANT'
els = cr.color_ramp.elements
els[0].position, els[0].color = 0.0, (0.05, 0.045, 0.04, 1)          # 흑운모
els[1].position, els[1].color = 0.1, (0.24, 0.19, 0.14, 1)           # 베이지 장석
for pos, c in ((0.45, (0.2, 0.19, 0.175)), (0.68, (0.36, 0.33, 0.29)), (0.86, (0.3, 0.2, 0.15))):  # 회색 석영 / 흰 / 분홍
    e = els.new(pos)
    e.color = (*c, 1)
lum = nt.nodes.new('ShaderNodeRGBToBW')
nt.links.new(voronoi(nt, 280, v, out='Color'), lum.inputs[0])
nt.links.new(lum.outputs[0], cr.inputs['Fac'])
f1 = voronoi(nt, 280, v)
grain = mrange(nt, f1, 0.5, 0.15)                      # 알갱이 돔 (1 = 가운데)
fines = mrange(nt, voronoi(nt, 900, v), 0.45, 0.1)     # 고운 모래
col = mix(nt, op(nt, 'MULTIPLY', mrange(nt, f1, 0.32, 0.52), 0.85), cr.outputs['Color'], (0.03, 0.025, 0.02))
col = mix(nt, 1.0, col, mrange(nt, fines, 0.0, 1.0, 0.85, 1.05), 'MULTIPLY')
rad = nt.nodes.new('ShaderNodeVectorMath')
rad.operation = 'LENGTH'
sxy = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], sxy.inputs[0])
cxy = nt.nodes.new('ShaderNodeCombineXYZ')
nt.links.new(sxy.outputs['X'], cxy.inputs['X'])
nt.links.new(sxy.outputs['Y'], cxy.inputs['Y'])
nt.links.new(cxy.outputs[0], rad.inputs[0])
wet = op(nt, 'MULTIPLY', mrange(nt, rad.outputs['Value'], 0.085, 0.04), mrange(nt, noise(nt, 25, 4, vec=v), 0.3, 0.6, 0.6, 1.0))
col = mix(nt, op(nt, 'MULTIPLY', wet, 0.8), col, (0.33, 0.32, 0.3), 'MULTIPLY')  # 젖은 흙은 어둡게
nt.links.new(col, p.inputs['Base Color'])
nt.links.new(fmix(nt, wet, mrange(nt, f1, 0.1, 0.5, 0.75, 0.95), 0.45), p.inputs['Roughness'])
nt.links.new(bump(nt, op(nt, 'ADD', grain, op(nt, 'MULTIPLY', fines, 0.3)), 0.7, 0.003), p.inputs['Normal'])
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=R1 - 0.011)
for vv in bm.verts:
    vv.co.z = SOIL + 0.004 * random.Random(int(vv.co.x * 1000)).random()
soil = from_bm(bm, A + "_Soil", m)
k3d.smooth(soil, 60)

# 개업 리본 2줄: 흙 위에서 화분 테두리를 넘어 바깥으로 늘어짐
mrib = label_mat("M_StorePlant_Ribbon", draw_labels(A), rough=0.35, img_name="T_StorePlant_Label", double_sided=True)


def ribbon(name, az, u0, u1, twist):
    import math as mth
    W = 0.05
    pts = []
    # (반지름, 높이) 경로: 흙 위 -> 테두리 -> 바깥 벽 아래로
    path = [(R1 - 0.06, SOIL + 0.006), (R1 - 0.01, POT_H + 0.008), (R1 + 0.012, POT_H + 0.004),
            (R1 + 0.014, POT_H - 0.04), (R1 + 0.006, 0.12), (R1 + 0.0, 0.05)]
    L = [0]
    for a, b in zip(path, path[1:]):
        L.append(L[-1] + mth.dist(a, b))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = []
    for k, ((r, z), l) in enumerate(zip(path, L)):
        t = l / L[-1]
        vv = (1.0, 0.995, 0.985)[k] if k < 3 else 0.985 * (1 - (l - L[2]) / (L[-1] - L[2]))
        a = az + twist * t
        c, s_ = mth.cos(a), mth.sin(a)
        tang = Vector((-s_, c, 0))
        ctr = Vector((r * c, r * s_, z))
        rows.append(((ctr - tang * W / 2), (ctr + tang * W / 2), vv))
    vs = [(bm.verts.new(a), bm.verts.new(b), v) for a, b, v in rows]
    for (a0, b0, v0), (a1, b1, v1) in zip(vs, vs[1:]):
        f = bm.faces.new((a0, b0, b1, a1))
        for l, uv in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            l[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(bm, name, mrib)
    for pp in o.data.polygons:
        pp.use_smooth = True
    return o


rib1 = ribbon(A + "_Rib1", math.radians(-90 - 28), 0.0, 0.5, 0.12)
rib2 = ribbon(A + "_Rib2", math.radians(-90 + 22), 0.5, 1.0, -0.1)

for x in (pot, sau, soil, rib1, rib2, leaves, bark):
    ensure_uv(x)
obj = k3d.join([pot, sau, soil, rib1, rib2, leaves, bark], A)
k3d.set_origin(obj, Vector((0, 0, 0)))
k3d.bake(obj, 1024, keep=("M_StorePlant_Leaves", "M_StorePlant_Bark", "M_StorePlant_Ribbon"))
print("STAT", A, "tris", scene_tris([obj]), "dims", tuple(round(x, 3) for x in obj.dimensions))
k3d.export(A, "Store", [obj], notes=(
    "파키라 화분(Poly Haven CC0 pachira_aquatica_01 변형 c, 데시메이트) + FRP 화분/물받침/마사토 흙 + 빛바랜 개업 리본(祝開業 / 큰길시장상인회일동). "
    "잎 M_StorePlant_Leaves(양면), 줄기 M_StorePlant_Bark, 리본 M_StorePlant_Ribbon(양면) 은 굽지 않은 텍스처 머티리얼. 화분/흙만 bake."))
k3d.preview(A, [obj])

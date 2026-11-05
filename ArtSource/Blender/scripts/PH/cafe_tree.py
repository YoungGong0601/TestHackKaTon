"""가로수 PH_StreetTree__Body. 프리팹 Crown0~2 타원체 자리에 덩어리 수관, 줄기, 밑동 철제 보호판을 만든다.
좌표는 소스 Blender 이고 turn(180) 뒤 Unity (x, y, z) = 소스 (x, z, y) 다. 원점은 밑동이라 x 범위는 -1.45 ~ 1.5 로 치우친다.
잎은 색과 메시로만 표현한다. 노멀 입력을 넣지 않는 이유는 k3d.bake 의 탄젠트 어긋남과 10 m 밖 밉맵 평탄화다."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("", "../Items", "../Buildings"):
    sys.path.insert(0, os.path.join(HERE, d))
import ph, bpy, bmesh, _ik
from bld import _n, _mixc, _math, _range
from mathutils import Vector, Matrix, noise
k3d = ph.k3d

k3d.reset()
A = "PH_StreetTree__Body"
random.seed(7)
noise.seed_set(7)
CROWN = (((0, 0, 3.9), (1.3, 1.3, 1.2)),            # 프리팹 실측 중심, 반지름
         ((0.7, 0.2, 3.3), (0.8, 0.8, 0.75)),
         ((-0.6, -0.4, 3.4), (0.85, 0.85, 0.75)))
LO, HI = (-1.45, -1.3, 2.55), (1.5, 1.3, 5.1)       # 세 타원체의 합집합 범위
TRIS = 6500                                         # 수관 삼각형 수, 씬에 14그루
N = 24                                              # 보호판 둘레 분할, 8의 배수여야 모서리가 맞는다


def obj(name, me, m):
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(m)
    return o


def fib(n):
    """단위 구 위에 고르게 뿌린 방향 n개."""
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        yield Vector((r * math.cos(i * 2.4), r * math.sin(i * 2.4), z))


def jit(v, a):
    return (v + Vector([random.uniform(-a, a) for _ in "xyz"])).normalized()


def vor(nt, vec, scale, feature="F1"):
    v = _n(nt, "ShaderNodeTexVoronoi", feature=feature, i_Scale=scale)
    nt.links.new(vec, v.inputs["Vector"])
    return v


def leaf_mat():
    m = k3d.mat(f"M_{A}_Leaf", rough=0.75)
    nt = m.node_tree
    g = _n(nt, "ShaderNodeNewGeometry")
    pos = g.outputs["Position"]

    def fbm(scale, detail):
        n = _n(nt, "ShaderNodeTexNoise", i_Scale=scale, i_Detail=detail)
        nt.links.new(pos, n.inputs["Vector"])
        return n.outputs["Fac"]

    up = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(g.outputs["Normal"], up.inputs[0])
    ao = _n(nt, "ShaderNodeAmbientOcclusion", i_Distance=0.45, samples=8)  # Unity 직사광은 AO 맵을 안 받아 색에 굽는다
    t = None  # 잎 조각 두 겹, 잎 뭉치, 수관 전체 얼룩, 위쪽 면, 틈새 깊이를 더한 값으로 색을 고른다
    for s, k in ((vor(nt, pos, 24.0).outputs["Color"], 0.4), (vor(nt, pos, 41.0).outputs["Color"], 0.25),
                 (fbm(7.0, 3.0), 0.2), (fbm(1.3, 3.0), 0.15), (up.outputs["Z"], 0.1), (ao.outputs["AO"], 0.25)):
        x = _math(nt, "MULTIPLY", s, k)
        t = x if t is None else _math(nt, "ADD", t, x)
    r = _n(nt, "ShaderNodeValToRGB")
    nt.links.new(t, r.inputs["Fac"])
    e = r.color_ramp.elements
    e[0].position, e[0].color = 0.40, (0.015, 0.05, 0.014, 1)
    e[1].position, e[1].color = 0.90, (0.27, 0.40, 0.06, 1)
    e.new(0.58).color = (0.05, 0.135, 0.024, 1)
    e.new(0.74).color = (0.13, 0.27, 0.04, 1)
    c = _mixc(nt, _range(nt, ao.outputs["AO"], 0.3, 1.0), (0.004, 0.012, 0.005), r.outputs["Color"])
    nt.links.new(c, k3d.principled(m).inputs["Base Color"])
    return m


def bark_mat():
    m = k3d.mat(f"M_{A}_Bark", rough=0.9)
    nt = m.node_tree
    mp = _n(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (40, 40, 5)
    nt.links.new(_n(nt, "ShaderNodeNewGeometry").outputs["Position"], mp.inputs["Vector"])
    n = _n(nt, "ShaderNodeTexNoise", i_Scale=3.0, i_Detail=6.0)
    nt.links.new(mp.outputs[0], n.inputs["Vector"])
    c = _mixc(nt, _range(nt, n.outputs["Fac"], 0.3, 0.7), (0.045, 0.034, 0.026), (0.17, 0.135, 0.10))
    crack = vor(nt, mp.outputs[0], 1.0, "DISTANCE_TO_EDGE").outputs["Distance"]
    c = _mixc(nt, _range(nt, crack, 0.0, 0.18), (0.015, 0.011, 0.009), c)
    nt.links.new(c, k3d.principled(m).inputs["Base Color"])
    return m


def iron_mat():
    """둥글게 돌아가는 긴 구멍이 뚫린 철판. 구멍은 색으로만 그린다."""
    m = k3d.mat(f"M_{A}_Iron", rough=0.6)
    nt = m.node_tree
    pos = _n(nt, "ShaderNodeNewGeometry").outputs["Position"]
    s = _n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(pos, s.inputs[0])
    rad = _n(nt, "ShaderNodeVectorMath", operation='LENGTH')
    nt.links.new(pos, rad.inputs[0])
    uv = _n(nt, "ShaderNodeCombineXYZ")
    nt.links.new(_math(nt, "DIVIDE", _math(nt, "ARCTAN2", s.outputs["Y"], s.outputs["X"]), 2 * math.pi), uv.inputs["X"])
    nt.links.new(rad.outputs["Value"], uv.inputs["Y"])
    b = _n(nt, "ShaderNodeTexBrick", **{"i_Scale": 1.0, "i_Mortar Size": 0.008, "i_Brick Width": 1 / 16, "i_Row Height": 0.05})
    b.inputs["Color1"].default_value = b.inputs["Color2"].default_value = (0.01, 0.01, 0.011, 1)
    b.inputs["Mortar"].default_value = (0.07, 0.072, 0.076, 1)
    nt.links.new(uv.outputs[0], b.inputs["Vector"])
    nt.links.new(b.outputs["Color"], k3d.principled(m).inputs["Base Color"])
    return m


# 수관: 타원체 안을 채우는 심, 겉의 큰 덩어리, 그 위의 작은 덩어리를 복셀로 합쳐 겉껍질 하나로 만든다
bm = bmesh.new()


def ball(c, s, sub=2):
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1, matrix=Matrix.LocRotScale(c, None, s))


for c, s in CROWN:
    c, s = Vector(c), Vector(s)
    ball(c, s * 0.72, 3)
    k = s.x / 1.3
    for d in fib(round(8 + 8 * k)):
        d = jit(d, 0.3)
        p = c + d * s * random.uniform(0.66, 0.82)
        r = random.uniform(0.38, 0.55) * k ** 0.5
        ball(p, (r, r, r * 0.85))
        for e in fib(7):
            e = jit(e, 0.4)
            if e.dot(d) > -0.1:
                ball(p + e * r * 0.85, [random.uniform(0.17, 0.27)] * 3)
me = bpy.data.meshes.new("Crown")
bm.to_mesh(me)
bm.free()
crown = obj("Crown", me, leaf_mat())
rm = crown.modifiers.new("Remesh", 'REMESH')
rm.mode, rm.voxel_size = 'VOXEL', 0.045
k3d.apply_all(crown)
bm = bmesh.new()
bm.from_mesh(crown.data)
bm.normal_update()
for v in bm.verts:  # 파장 0.15 m 아래는 삼각형 크기에 뭉개져 넣지 않는다
    v.co += v.normal * (0.12 * noise.noise(v.co * 1.6) + 0.06 * noise.noise(v.co * 3.7) + 0.03 * noise.noise(v.co * 6.5))
bm.to_mesh(crown.data)
bm.free()
dec = crown.modifiers.new("Decimate", 'DECIMATE')
dec.ratio = TRIS / (2 * len(crown.data.polygons))
k3d.apply_all(crown)
vs = crown.data.vertices
for i in range(3):  # 변위로 늘어난 범위를 회색 자리에 맞춘다
    a = [v.co[i] for v in vs]
    lo, sc = min(a), (HI[i] - LO[i]) / (max(a) - min(a))
    for v in vs:
        v.co[i] = LO[i] + (v.co[i] - lo) * sc
k3d.smooth(crown, 180)

# 줄기와 수관 속으로 들어가는 가지
bark = bark_mat()
parts = [crown, _ik.tube("Trunk", [(0, 0, 0), (0, 0, 0.12), (0.012, -0.006, 0.6), (0.02, 0.005, 1.3), (0.005, 0.02, 2.0),
                                   (-0.01, 0.02, 2.5), (0, 0.03, 3.0)], 1.0, n=12, mat=bark, cap=False,
                         rfun=lambda t: 0.125 - 0.065 * t + 0.05 * max(0, 1 - 6 * t))]
for pts in (((0, 0.02, 2.05), (0.3, 0.1, 2.4), (0.62, 0.2, 3.0)), ((-0.01, 0.02, 2.2), (-0.3, -0.15, 2.6), (-0.6, -0.4, 3.05)),
            ((0, 0.02, 2.3), (0.1, -0.25, 2.7), (0.18, -0.45, 3.3)), ((0, 0.02, 2.35), (-0.2, 0.3, 2.75), (-0.25, 0.6, 3.3))):
    parts.append(_ik.tube("Branch", pts, 1.0, n=8, mat=bark, cap=False, rfun=lambda t: 0.05 - 0.032 * t))

# 밑동 보호판: 윗면과 옆면만 만들고 흙판이 구멍을 막는다
ang = [(math.cos(2 * math.pi * i / N), math.sin(2 * math.pi * i / N)) for i in range(N)]
sq = [(x * 0.55 / max(abs(x), abs(y)), y * 0.55 / max(abs(x), abs(y))) for x, y in ang]
ring = [(i, (i + 1) % N) for i in range(N)]
me = bpy.data.meshes.new("Grate")
me.from_pydata([(x, y, 0) for x, y in sq] + [(x, y, 0.04) for x, y in sq] + [(x * 0.2, y * 0.2, 0.04) for x, y in ang], [],
               [(i, j, j + N, i + N) for i, j in ring] + [(i + N, j + N, j + 2 * N, i + 2 * N) for i, j in ring])
grate = obj("Grate", me, iron_mat())
k3d.smooth(grate, 30)
me = bpy.data.meshes.new("Soil")
me.from_pydata([(x * 0.21, y * 0.21, 0.036) for x, y in ang], [], [tuple(range(N))])
parts += [grate, obj("Soil", me, k3d.mat(f"M_{A}_Soil", (0.03, 0.022, 0.016), 0.95))]

o = ph.part(A, parts, ph.turn(180))
for x in parts:  # 남겨 두면 돌아간 복사본과 겹쳐 AO 와 미리보기가 틀어진다
    bpy.data.objects.remove(x, do_unlink=True)
k3d.uv_world(o)  # 빈 UV 를 탄젠트 기준으로 쓰지 않게 한다
k3d.bake(o, size=1024, margin=3)
ph.finish(A, o, notes="원점은 밑동 바닥 중앙이고 프리팹 회색 자리에 맞췄다. x 범위 -1.45 ~ 1.5. 잎은 색과 메시이고 노멀은 평평하다.")
k3d.preview(A, [o], views=((35, 18), (215, 12), (0, -6)))

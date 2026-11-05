"""PH_CafeFront__Body: 숲길 커피 앞면. turn(180) 이라 Unity (x, y, z) = 소스 (x, z, y), 앞은 소스 -Y 다.

x 0.45~1.38 은 PH_Door_Glass 자리라 y 2.6 아래에 메시를 두지 않는다. 차양이 문 위에서만 아치로 올라가는 이유다.
간판 글자는 프리팹 Sign(z -0.145, 글자색 0.15 회색)이 그리므로 판은 크림색으로 비워 둔다.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE] + [os.path.join(HERE, "..", d) for d in ("Storefront", "StoreProps", "Buildings")]
import bpy, bmesh
from mathutils import Matrix
import ph, sf, bld
import _common as C
k3d = ph.k3d

A = "PH_CafeFront__Body"
W, P = 7.8, 7.8 / 25              # 폭, 차양 줄무늬 폭. 25칸이라 양 끝이 초록이고 turn(180) 뒤에도 같은 무늬다
D0, D1 = 0.45, 1.38               # 문 자리
MULL = (-3.87, -2.4, -0.95, 0.42, 1.41, 2.6, 3.87)
GREEN = (0.0137, 0.1046, 0.0595)  # #1F5B45, cafe_room.py 와 같은 값
CREAM = (0.863, 0.791, 0.645)     # #EFE6D2
AW_WALL, AW_FRONT, AW_ARCH = 2.722, 2.46, 2.645   # 차양 윗면 높이: 벽, 앞, 문 위. 벽 쪽은 간판 판 밑(2.73)보다 낮다
HEM, HEM_ARCH = 2.30, 2.602       # 드림 끝 높이: 평소, 문 위

k3d.reset()
parts = []


def box(mat, x, y, z, bev=0.003):
    """x, y, z = (최소, 최대). 베벨을 메시에 바로 넣는다. ph.part 가 모디파이어를 지운다."""
    assert not (x[0] < D1 and x[1] > D0 and z[0] < 2.6), f"문 자리 침범 {x} {z}"
    assert not (x[0] < -0.6 and x[1] > -3 and z[0] < 3.23 and z[1] > 2.73 and y[0] < -0.145), f"간판 앞 침범 {x} {y} {z}"
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = [(a + b) / 2 + c * (b - a) for c, (a, b) in zip(v.co, (x, y, z))]
    if bev:
        bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=bev, segments=1, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    parts.append(sf._obj("Part", bm, mat))


def disc(mat, cx, cz, r, y0, y1, uv_scale=1.0):
    """-Y 를 보는 원판. UV 는 원 중심 기준이라 이미지가 똑바로 보인다."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=48, radius1=r, radius2=r, depth=y1 - y0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, (y0 + y1) / 2, cz))
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (0.5 + (l.vert.co.x - cx) / (2 * r) * uv_scale, 0.5 + (l.vert.co.z - cz) / (2 * r) * uv_scale)
    parts.append(sf._obj("Disc", bm, mat))


def xpos(nt):
    s = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(C.coord(nt), s.inputs[0])
    return s.outputs['X']


def slats(m, pitch=0.095, gap=0.012):
    """원목 판에 세로 홈을 그린다. 판자를 따로 세우면 UV 섬이 수백 개로 늘어 해상도가 떨어진다."""
    nt, p = m.node_tree, k3d.principled(m)
    g = C.op(nt, 'LESS_THAN', C.op(nt, 'FRACT', C.op(nt, 'DIVIDE', xpos(nt), pitch)), gap / pitch)
    nt.links.new(C.mix(nt, g, p.inputs['Base Color'].links[0].from_socket, (0.018, 0.012, 0.009)), p.inputs['Base Color'])
    nt.links.new(C.bump(nt, C.op(nt, 'SUBTRACT', 1.0, g), 0.7, 0.004, normal=p.inputs['Normal'].links[0].from_socket),
                 p.inputs['Normal'])
    return m


def canvas(name):
    """줄무늬 천. 소스 x 와 turn 뒤 x 는 부호만 다르고 칸 수가 홀수라 무늬가 같다."""
    m, nt, p = C.new_mat(name)
    v = C.coord(nt)
    odd = C.op(nt, 'MODULO', C.op(nt, 'FLOOR', C.op(nt, 'DIVIDE', C.op(nt, 'ADD', xpos(nt), W / 2), P)), 2)
    var = C.mrange(nt, C.noise(nt, 7, 4, vec=v), 0.3, 0.7, 0.9, 1.05)
    nt.links.new(C.mix(nt, 1.0, C.mix(nt, odd, GREEN, CREAM), var, 'MULTIPLY'), p.inputs['Base Color'])
    nt.links.new(C.bump(nt, C.noise(nt, 350, 2, vec=v), 0.1, 0.0006), p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.8
    return m


def door_k(x):
    """문 위에서 1, 문에서 60cm 넘게 떨어지면 0."""
    t = min(max(D0 - 0.03 - x, x - D1 - 0.03, 0) / 0.6, 1)
    return 1 - t * t * (3 - 2 * t)


def aw_front(x):
    k = door_k(x)
    return AW_FRONT + (AW_ARCH - AW_FRONT) * k


def awning(mat, th=0.012, n=250, ts=(0, 1 / 3, 2 / 3, 1)):
    """천과 앞 드림을 한 단면으로 x 방향으로 쓸어 만든다. 줄무늬마다 둥근 자락이고 윗면은 살짝 물결친다."""
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        x = -W / 2 + W * i / n
        phase = 2 * math.pi * (x + W / 2) / P
        yf = -1.05 + 0.004 * (1 + math.cos(phase))
        k = door_k(x)
        hem = HEM + 0.03 * (1 - abs(math.sin(phase / 2)))
        hem += (HEM_ARCH - hem) * k
        zf = aw_front(x)

        def top(t):
            return -0.09 + (yf + 0.09) * t, AW_WALL + (zf - AW_WALL) * t + 0.006 * math.sin(math.pi * t) * math.cos(phase)
        sec = [top(t) for t in ts] + [(yf, hem), (yf + th, hem)]
        sec += [(top(t)[0] + th * t, top(t)[1] - th) for t in reversed(ts)]
        rings.append([bm.verts.new((x, y, z)) for y, z in sec])
    m = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for j in range(m):
            bm.faces.new((a[j], b[j], b[(j + 1) % m], a[(j + 1) % m]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(sf._obj("Awning", bm, mat))


m_green = C.powder_coat(f"M_{A}_Green", GREEN, rough=0.45, wear=0.1, grime=0.35, scratch=0.1, peel=0.0)
m_black = C.powder_coat(f"M_{A}_Black", (0.015, 0.015, 0.016), rough=0.4, wear=0.15, grime=0.3, scratch=0.15, peel=0.0)
m_wood = slats(C.wood(f"M_{A}_Wood", scale_m=0.9, tint=(0.82, 0.62, 0.44), wear=0.2, scratch=0.15))
m_cream = k3d.mat(f"M_{A}_Cream", CREAM, 0.5)
m_canvas = canvas(f"M_{A}_Canvas")
m_logo = k3d.mat(f"M_{A}_Logo", CREAM, 0.5)
im = k3d.image_node(m_logo, k3d.load_image(os.path.join(k3d.REPO, "Assets", "UI", "Kiosk", "Art", "logo_cafe.png")), uv="UVMap")
m_logo.node_tree.links.new(C.mix(m_logo.node_tree, im.outputs['Alpha'], CREAM, im.outputs['Color']),
                           k3d.principled(m_logo).inputs['Base Color'])
m_glass = k3d.mat("M_Glass_PH_CafeFront", (0.7, 0.8, 0.76), 0.05, alpha=0.2)

# 아래 벽판: 걸레받이, 원목, 창턱. 문 양옆은 검은 틀이 바닥까지 내려온다
for a, b in ((-W / 2, 0.39), (1.44, W / 2)):
    box(m_black, (a, b), (-0.062, 0.062), (0, 0.06))
    box(m_wood, (a, b), (-0.06, 0.06), (0.06, 0.37), 0.002)
for a, b in ((0.39, 0.449), (1.381, 1.44)):
    box(m_black, (a, b), (-0.062, 0.062), (0, 0.37))
for a, b in ((-W / 2, 0.449), (1.381, W / 2)):
    box(m_green, (a, b), (-0.075, 0.075), (0.37, 0.4), 0.004)

# 창틀과 유리. 유리는 틀에 4mm 물린 닫힌 상자라 안팎 어디서 봐도 한 겹이다
for x in MULL:
    box(m_black, (max(x - 0.03, 1.381 if x == 1.41 else -9), min(x + 0.03, 0.449 if x == 0.42 else 9)), (-0.04, 0.04), (0.4, 2.6))
for a, b in ((-3.84, 0.39), (1.44, 3.84)):
    for z in ((0.4, 0.44), (2.16, 2.2), (2.56, 2.6)):
        box(m_black, (a, b), (-0.03, 0.03), z)
for a, b in zip(MULL, MULL[1:]):
    if a != 0.42:
        box(m_glass, (a + 0.026, b - 0.026), (-0.015, 0.015), (0.42, 2.58), 0)

# 띠, 상단 덮개, 안쪽 원목 판
box(m_green, (-W / 2, W / 2), (-0.1, 0.094), (2.6, 3.262), 0.005)
box(m_black, (-W / 2, W / 2), (-0.125, 0.1), (3.262, 3.3), 0.004)
box(m_wood, (-W / 2, W / 2), (0.094, 0.1), (2.6, 3.262), 0)

# 간판 판. 글자는 프리팹이 그린다. 판 앞면 z -0.14, 틀은 Sign 보다 1.5mm 뒤
box(m_cream, (-2.995, -0.605), (-0.14, -0.1), (2.735, 3.225), 0)
for x, z in (((-3, -0.6), (2.73, 2.75)), ((-3, -0.6), (3.21, 3.23)), ((-3, -2.98), (2.75, 3.21)), ((-0.62, -0.6), (2.75, 3.21))):
    box(m_black, x, (-0.1435, -0.1), z, 0.002)

# 띠 장식: 양옆 원목 판, 간판 옆 원두 로고. 문 위에 두면 올라간 차양이 가까이서 로고를 가린다
for a, b in ((1.6, 3.76), (-3.76, -3.14)):
    box(m_black, (a, b), (-0.108, -0.1), (2.76, 3.21), 0.002)
    box(m_wood, (a + 0.02, b - 0.02), (-0.114, -0.108), (2.78, 3.19), 0.002)
disc(m_black, -0.22, 2.985, 0.215, -0.116, -0.1)
disc(m_logo, -0.22, 2.985, 0.2, -0.13, -0.116, 0.8)

# 차양: 벽 쪽 받침, 천, 앞 봉, 팔
box(m_black, (-W / 2, W / 2), (-0.12, -0.1), (2.665, 2.705))
awning(m_canvas)
parts.append(sf.pipe("Bar", [(x / 20, -1.015, aw_front(x / 20) - 0.028) for x in range(-77, 78)], 0.01, m_black, n=12))
for x in MULL:
    parts.append(sf.pipe("Arm", [(x, -0.1, 2.69), (x, -1.012, aw_front(x) - 0.03)], 0.008, m_black, n=12))

o = ph.part(A, parts, ph.turn(180))
for p in parts:
    bpy.data.objects.remove(p, do_unlink=True)   # 남겨 두면 뒤집힌 자리에서 AO 를 어둡힌다
k3d.smooth(o, 40)

U = [(-v.co.x, v.co.z, -v.co.y) for v in o.data.vertices]
lo, hi = [min(a) for a in zip(*U)], [max(a) for a in zip(*U)]
print("Unity 범위", [round(c, 4) for c in lo], [round(c, 4) for c in hi])
assert max(abs(a - b) for a, b in zip(lo + hi, (-3.9, 0, -1.05, 3.9, 3.3, 0.1))) < 0.002, "경계 상자"
assert not [u for u in U if D0 < u[0] < D1 and u[1] < 2.6], "문 자리"
assert not [u for u in U if -3 < u[0] < -0.6 and 2.73 < u[1] < 3.23 and u[2] < -0.145], "간판 앞"

for m in bpy.data.materials:
    if k3d.principled(m):
        k3d.principled(m).inputs['Emission Strength'].default_value = 0   # 기본 Emission Color 가 흰색이다

k3d.bake(o, size=2048, ao_distance=0.25, samples=32, margin=6)
ph.finish(A, o, notes="숲길 커피 앞면. 원점 바닥 중앙, 앞 -Z. x 0.45~1.38 은 y 2.6 까지 비었고 차양은 간판이 가리지 않게 앞쪽이 y 2.3 까지 내려오되 문 위에서만 아치로 올라간다. "
                      "Sign 판은 크림색이고 글자는 프리팹이 그린다.")
k3d.preview(A, [o], views=((180, 0), (215, 12), (150, 3), (20, 10)))
# 눈높이 시점. turn 뒤라 거리 쪽은 Blender +Y, Unity x 는 Blender -x 다
bld.shot(A, [o], (-0.9, 4.5, 1.6), (0.3, 0, 2.5), tag="street")

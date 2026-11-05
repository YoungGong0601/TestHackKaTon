"""PH_Bus: CityBus.blend -> 친구 프레임(진행 +X, 문 -Z)의 몸체 + 앞문 문짝 두 장.

몸체 = 외판·내장·유리·바퀴·닫힌 중문. 앞문 구멍은 비운다. 문짝 원점 = DoorLeafA/B 의 프리팹 위치.
노선 번호는 전부 지운다: LED 3장 -> 꺼진 판, 대시보드 카드 -> 빈 카드, 번호판·회사명 -> bus_tex.py.
"""
import sys, os, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ph, k3d, bpy, bmesh
from mathutils import Matrix, Vector

# 10.9/11.4 로 줄이면 옆면 z -1.19, 앞문 x 4.25, 지붕 2.85 가 되어 앵커(z -1.29, -1.27)에서 뜬다.
# 1.0 이면 차체 10.84x2.98x2.49 가 프로토타입 차체 10.9x3.05x2.5 와 맞고 문이 x 4.45, -0.90 에 정확히 온다.
S = 1.0
FOLD = 15     # 토끼귀 거울을 지붕 받침 축으로 앞쪽으로 접는 각도 (폭 허용치 2.83 안으로)
LEAF_X = 1.223  # 원본 문짝 면의 |x|
# 프로토타입 eg(): 앞문 U = 4.45 (doorX, 승차 문), 문짝 (U -/+ .29, 1.5, l/2 + .04) 순서. z 만 뒤집는다.
DOORS = {"PH_Bus__DoorA": ("CityBus_DoorFront_L", (4.16, 1.5, -1.29)),
         "PH_Bus__DoorB": ("CityBus_DoorFront_R", (4.74, 1.5, -1.29))}
TDIR = os.path.join(k3d.ART, "Textures", "PH_Bus")


def edit_islands(o, fn):
    """o 의 연결된 조각마다 fn(bm, 정점 목록, 중심) 을 부른다."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, parts = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        seen.add(v)
        stack, isl = [v], []
        while stack:
            a = stack.pop()
            isl.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        parts.append(isl)
    for isl in parts:
        fn(bm, isl, sum((v.co for v in isl), Vector()) / len(isl))
    bm.to_mesh(o.data)
    bm.free()


def fold_mirror(bm, isl, c):
    if abs(c.x) > 1.0 and c.y < -5.01 and c.z > 1.8:   # 팔·거울 몸통·보조 거울 (지붕 받침은 그대로)
        s = math.copysign(1, c.x)
        bmesh.ops.rotate(bm, verts=isl, cent=(s * 1.02, -5.02, 0), matrix=Matrix.Rotation(math.radians(-s * FOLD), 3, 'Z'))


def drop_hinge(bm, isl, c):
    """미닫이로 쓰므로 여닫이 회전 기둥과 받침을 뺀다 (원점 = 경첩축, 안쪽 = +x). 손잡이 봉은 남긴다."""
    if max(v.co.x for v in isl) > 0.03 and abs(c.y) < 0.1:
        bmesh.ops.delete(bm, geom=isl, context='VERTS')


subprocess.run([os.path.join(k3d.CACHE, "venv", "bin", "python"), "-I", os.path.join(HERE, "bus_tex.py"), TDIR], check=True)
ph.load("Vehicles", "CityBus")
O = bpy.data.objects

sign = k3d.mat("M_PH_Bus_SignBlank", (1, 1, 1), 0.35)
k3d.image_node(sign, k3d.load_image(os.path.join(TDIR, "T_PH_Bus_SignBlank.png"), "T_PH_Bus_SignBlank"), k3d.principled(sign).inputs['Base Color'])
O["CityBus_RouteSign"].data.materials[0] = sign

old = bpy.data.materials["M_CityBus_Decals"]
decal = old.copy()
decal.name = "M_PH_Bus_Decals"
next(n for n in decal.node_tree.nodes if n.type == 'TEX_IMAGE').image = k3d.load_image(os.path.join(TDIR, "T_PH_Bus_Decals.png"), "T_PH_Bus_Decals")
for o in O:
    if o.type == 'MESH' and old.name in o.data.materials:
        o.data.materials[o.data.materials.find(old.name)] = decal

edit_islands(O["CityBus_Trim"], fold_mirror)
for src, _ in DOORS.values():
    edit_islands(O[src], drop_hinge)

T = ph.turn(-90) @ Matrix.Scale(S, 4)
front = [src for src, _ in DOORS.values()]
source = list(O)
body = ph.part("PH_Bus__Body", [o for o in source if o.type == 'MESH' and o.name not in front], T)
leaves = {n: ph.part(n, [O[src]], ph.move_unity(-a[0], -a[1], LEAF_X * S) @ T) for n, (src, a) in DOORS.items()}
for o in source:   # 프리뷰에 원본이 같이 찍히지 않게
    O.remove(o)

U = [(-v.co.x, v.co.z, -v.co.y) for v in body.data.vertices]
assert max(abs(p[2]) for p in U) < 2.57 * 1.1 / 2, "거울이 폭 허용치를 넘음"
assert not [p for p in U if abs(p[0]) < 0.7 and 2.55 < p[1] < 2.95 and p[2] < -1.27], "번호판 자리에 메시가 있음"
assert not [p for p in U if 3.9 < p[0] < 5.0 and 0.4 < p[1] < 2.55 and p[2] < -1.23], "앞문 구멍에 메시가 있음"

ph.finish("PH_Bus__Body", body, notes={
    "doors": "앞문(x 4.45) 구멍은 비움, 중문(x -0.90)은 닫힌 채 몸체에 포함. 거울은 앞으로 15도 접음.",
    "route": "LED 앞·옆·뒤는 꺼진 판, 대시보드 카드는 빈 카드, 번호판 3086, 회사명 시민교통(주). 노선 번호는 Plate_Blur, Plate_112 몫."})
for n, (_, a) in DOORS.items():
    ph.finish(n, leaves[n], notes={"origin": f"프리팹 로컬 {a} 의 DoorLeaf 원점. 닫힌 위치 기준."})
    leaves[n].location = ph.at_unity(*a)   # 프리뷰는 앵커 자리에 끼운 조립 상태로 본다 (FBX 는 이미 나감)

k3d.preview("PH_Bus__Body", [body], views=((180, 6), (232, 14), (270, 6), (0, 6)), tag="ph")
for n, o in leaves.items():
    k3d.preview(n, [o], views=((180, 4),), res=(700, 1000), ground=False, tag="ph")

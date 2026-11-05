"""NpcAjumma: 아주머니 (누빔 패딩조끼 + 꽃무늬 블라우스 + 회갈색 슬랙스 + 뽀글 파마). 원본 npc_woman1."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import mathutils.noise as mnoise
from mathutils import Vector
import npc_common as N

A = "NpcAjumma"


def prep(arm, body, s0):
    mat = lambda nm: next(m for m in body.data.materials if m and m.name == nm)
    # 조끼 = 앞판(원본 Shirt) + 몸통 옆·뒤 (원본은 앞만 Shirt 라 앞치마처럼 보였음). 소매는 블라우스
    sx = N.bone_head(arm, "UpperArm.L").x * s0
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Jacket" and abs(c.x) * s0 < sx - 0.01), mat("Shirt"))
    # 뒤통수·옆머리 두피를 머리카락으로 (파마 껍질 아래·목덜미 짧은 머리)
    hz = N.bone_head(arm, "Head").z * s0
    ez = min(p.center.z for p in body.data.polygons if body.data.materials[p.material_index].name == "Eyes") * s0
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Skin" and (
        (c.z * s0 > hz + 0.02 and c.y * s0 > 0.0) or
        (c.z * s0 > ez + 0.005 and c.y * s0 > -0.04 and abs(c.x) * s0 > 0.05))), mat("HairBase"))
    # 조끼(Shirt)를 1.2cm 부풀려 패딩 두께
    N.push(body, N.faces(body, lambda c, n, m: m == "Shirt"), 0.012 / s0)
    # 슬랙스 일자 핏: 무릎 아래로 갈수록 종아리 둘레를 최대 1.5cm 키움 (쫄바지처럼 보이던 것)
    kz = N.bone_head(arm, "LowerLeg.L").z
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.normal_update()
    pi = [m.name for m in body.data.materials].index("Pants")
    vs = {v for f in bm.faces if f.material_index == pi for v in f.verts}
    off = {}
    for v in vs:
        w = min(1.0, max(0.0, (kz - v.co.z) / (kz * 0.45)))
        if w > 0:
            off[v] = Vector((v.normal.x, v.normal.y, 0)).normalized() * (0.015 / s0) * (w * w * (3 - 2 * w))
    for v, o in off.items():
        v.co += o
    bm.to_mesh(body.data)
    bm.free()


def perm_cap(arm, body):
    """뽀글 파마 머리: 원래 바가지 머리(뾰족 앞머리)는 두피 안으로 숨기고, 두피를 따라 둥글게 부푼 껍질을 씌움.
    정수리 +4.4cm, 옆·뒤는 귀 위를 덮는 둥근 부피, 앞은 이마선(정수리에서 58°)까지. 1.5~2cm 컬 덩어리 요철."""
    me = body.data
    mats = [m.name if m else "" for m in me.materials]
    gi = body.vertex_groups["Head"].index
    hv = [v.co for v in me.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    eyes = [p.center for p in me.polygons if mats[p.material_index] == f"M_{A}_Eyes" and p.center.z > 1.0]
    ez = sum(c.z for c in eyes) / len(eyes)
    xs, ys = [p.x for p in hv], [p.y for p in hv]
    C = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2 + 0.01, ez + 0.012))
    hi = mats.index(f"M_{A}_Hair")
    for i in {i for p in me.polygons if p.material_index == hi for i in p.vertices}:
        me.vertices[i].co = C + (me.vertices[i].co - C) * 0.8
    tree = N.bvh(body)
    NA, NT = 40, 12

    def tmax(ph):                                       # 앞 58°, 옆 98°, 뒤 118° + 컬이 들쭉날쭉한 머리선
        c = math.cos(ph)
        return math.radians(98 + (20 * c if c > 0 else 40 * c) + 5 * math.sin(ph * 7) + 3 * math.sin(ph * 13 + 1))

    def dirv(th, ph):
        return Vector((math.sin(th) * math.sin(ph), math.sin(th) * math.cos(ph), math.cos(th)))

    def scalp(th, ph):
        d = dirv(th, ph)
        h = tree.ray_cast(C + d * 0.35, -d, 0.35)
        return (h[0] - C).length if h[0] is not None else 0.09

    rr = [[scalp(tmax(2 * math.pi * i / NA) * j / NT, 2 * math.pi * i / NA) for i in range(NA)] for j in range(NT + 1)]
    raw = [row[:] for row in rr]
    for _ in range(8):                                  # 귀·광대처럼 튀는 곳을 감싸 둥글게 (두피보다 안으로는 안 들어감)
        rr = [[max(raw[j][i], (rr[j][i] * 2 + rr[j][(i - 1) % NA] + rr[j][(i + 1) % NA] + rr[max(0, j - 1)][i] + rr[min(NT, j + 1)][i]) / 6)
               for i in range(NA)] for j in range(NT + 1)]
    bm = bmesh.new()
    rows = []
    for j in range(NT + 2):
        row = []
        for i in range(NA):
            ph = 2 * math.pi * i / NA
            if j <= NT:
                s = j / NT
                th = tmax(ph) * s
                r = rr[j][i] + 0.008 + 0.036 * math.cos(s * math.pi / 2)            # 정수리 4.4cm -> 귀 높이 1.6cm -> 끝 0.8cm
                p = C + dirv(th, ph) * r
                p += dirv(th, ph) * (0.006 * mnoise.noise(p * 42.0))              # 컬 덩어리 요철
            else:                                                                 # 가장자리를 두피 안으로 말아 넣음
                th = tmax(ph) * 1.05
                p = C + dirv(th, ph) * (scalp(th, ph) - 0.002)
            row.append(bm.verts.new(p))
            if j == 0:
                break
        rows.append(row)
    top = rows[0][0]
    for i in range(NA):
        bm.faces.new((top, rows[1][i], rows[1][(i + 1) % NA]))
    for a, b in zip(rows[1:], rows[2:]):
        for i in range(NA):
            bm.faces.new((a[i], b[i], b[(i + 1) % NA], a[(i + 1) % NA]))
    bm.normal_update()
    if sum((f.calc_center_median() - C).dot(f.normal) for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    ztop = top.co.z
    hair = N.hair(f"M_{A}_Perm", (0.055, 0.02, 0.013), style="curly", grey_top=ztop - 0.03)
    return [N.shell_obj(A + "_Perm", bm, hair, body, thick=0, subd=1, group="Head")]


def zipper(g, base):
    # 앞 중심 지퍼 (검은 테이프 + 금속 이빨) — 패딩 조끼 앞여밈
    x, y, z = g.xyz()
    front = g.math('LESS_THAN', y, -0.02)
    tape = g.math('MULTIPLY', g.band(x, -0.006, 0.006, 0.0008), front)
    base = g.mix(tape, base, (0.02, 0.012, 0.015))
    teeth = g.ramp(g.wave(0.0035, 'Z', profile='TRI'), [(0.45, (0,)), (0.55, (1,))])
    tz = g.math('MULTIPLY', g.band(x, -0.0025, 0.0025, 0.0005), front)
    return g.mix(g.math('MULTIPLY', tz, teeth), base, (0.3, 0.27, 0.24))


def skin(arm, zr):
    ez, fy, ex = zr["_face"]

    def face(g, base):
        # 볼 홍조 + 연한 립 컬러 (점 눈 얼굴이 남자처럼 보이던 것)
        x, y, z = g.xyz()
        front = g.math('LESS_THAN', y, fy + 0.03)
        dv = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
        g.set(dv.inputs[0], g.n('ShaderNodeCombineXYZ', X=g.math('SUBTRACT', g.math('ABSOLUTE', x), ex + 0.004),
                               Y=g.math('SUBTRACT', z, ez - 0.028)).outputs[0])
        cheek = g.math('MULTIPLY', g.ramp(dv.outputs['Value'], [(0.0, (1,)), (0.026, (0,))]), front)
        base = g.mix(g.math('MULTIPLY', cheek, 0.4), base, (0.62, 0.25, 0.22))
        dl = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
        g.set(dl.inputs[0], g.n('ShaderNodeCombineXYZ', X=g.math('DIVIDE', x, 3.2), Y=g.math('SUBTRACT', z, ez - 0.05)).outputs[0])
        lip = g.math('MULTIPLY', g.ramp(dl.outputs['Value'], [(0.0045, (1,)), (0.0065, (0,))]), front)
        return g.mix(g.math('MULTIPLY', lip, 0.75), base, (0.5, 0.13, 0.14))
    return N.skin(f"M_{A}_Skin", (0.66, 0.44, 0.31), face=face)


floral = lambda nm: (lambda a, z: N.cloth(f"M_{A}_{nm}", (0.05, 0.03, 0.075), "floral", 0.7, col2=(0.6, 0.2, 0.36)))
perm = lambda nm: (lambda a, z: N.hair(f"M_{A}_{nm}", (0.055, 0.02, 0.013), style="curly"))

CFG = dict(
    asset=A, glb="npc_woman1", height=1.595, prep=prep,          # 몸 기준 키. 파마 볼륨(+3cm)을 더해 전체 1.62m
    mats={
        "Shirt": lambda a, z: N.cloth(f"M_{A}_PaddedVest", (0.12, 0.02, 0.035), "quilt", 0.5, extra=zipper),
        "LightJacket": floral("BlouseCuff"), "Jacket": floral("Blouse"),
        "Pants": lambda a, z: N.cloth(f"M_{A}_Slacks", (0.147, 0.124, 0.098), "wool", 0.85, dust=0.6),   # 회갈색 #6b6258
        "Shoes": lambda a, z: N.leather(f"M_{A}_Shoes", (0.02, 0.018, 0.016), 0.5, sole=(0.06, 0.05, 0.045), sole_h=0.02),
        "HairBase": perm("HairBase"), "Hair": perm("Hair"),
        "Eyebrows": lambda a, z: N.flat(f"M_{A}_Brows", (0.03, 0.016, 0.01), 0.6),
        "Skin": skin,
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=perm_cap,
    watch=dict(style="gold", strap=(0.6, 0.45, 0.2), metal=True, size=0.013),
    notes="아주머니(50대): 와인색 누빔 패딩조끼(1.2cm 두께, 앞 지퍼), 보라 꽃무늬 블라우스, 회갈색 일자 슬랙스, 컴포트화,"
          " 적갈색 염색 뽀글 파마(정수리 흰머리 뿌리, 둥근 볼륨이 귀 위를 덮음), 볼 홍조·립 컬러, 금색 시계."
          " '뒤에 사람 기다려요.'(ajm) 용. 키 1.62m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

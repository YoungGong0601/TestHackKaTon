"""NpcClerkWoman: 30대 여성 회사원 (흰 긴소매 블라우스 + 남색 슬랙스 + 검정 구두, 어두운 단발). 원본 npc_woman3."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Vector
import npc_common as N

A = "NpcClerkWoman"
NAVY = (0.018, 0.03, 0.085)
dark = lambda nm: (lambda a, z: N.hair(f"M_{A}_{nm}", (0.014, 0.011, 0.01), style="fine"))


def prep(arm, body, s0):
    # 단발 가닥(따로 떨어진 원통)이 서브디비전 후 레게머리처럼 보임 -> 옆으로 넓히고 납작하게 겹쳐 한 덩어리 단발로
    bm = bmesh.new()
    bm.from_mesh(body.data)
    hi = [m.name for m in body.data.materials].index("Hair")
    hc = N.bone_head(arm, "Head")
    seen = set()
    for f in bm.faces:
        if f.material_index != hi or f.index in seen:
            continue
        comp, st = {f}, [f]
        seen.add(f.index)
        while st:
            for e in st.pop().edges:
                for g in e.link_faces:
                    if g.index not in seen and g.material_index == hi:
                        seen.add(g.index)
                        comp.add(g)
                        st.append(g)
        vs = {v for g in comp for v in g.verts}
        zs = [v.co.z for v in vs]
        if (max(zs) - min(zs)) * s0 < 0.12:                     # 정수리 덮개·눈썹은 그대로
            continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        r = Vector((c.x - hc.x, c.y - hc.y, 0)).normalized()
        t = Vector((-r.y, r.x, 0))
        for v in vs:
            d = v.co - c
            v.co = c + r * (d.dot(r) * 0.75) + t * (d.dot(t) * 1.45) + Vector((0, 0, d.z))
    bm.to_mesh(body.data)
    bm.free()
    # 반팔 티 -> 긴소매: 팔 피부를 손목 5cm 위까지 Shirt 로 (시계는 소매 밖 손목에 남음)
    wx = N.bone_head(arm, "Palm.L").x * s0
    shirt = next(m for m in body.data.materials if m and m.name == "Shirt")
    sl = N.faces(body, lambda c, n, m: m == "Skin" and 0.115 < abs(c.x) * s0 < wx - 0.05 and c.z * s0 > 1.0)
    N.set_mat(body, sl, shirt)
    N.push(body, sl, 0.004 / s0)
    # 슬랙스 일자 핏: 무릎 아래로 갈수록 종아리 둘레를 최대 1.5cm 키움 (원본 바지는 쫄바지처럼 붙음)
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


def blouse(a, zr):
    def extra(g, base):
        # 앞여밈 플래킷 + 단추 (NpcOfficeMan 셔츠와 같은 방식)
        x, y, z = g.xyz()
        ax = g.math('ABSOLUTE', x)
        front = g.math('LESS_THAN', y, -0.03)
        line = (0.45, 0.46, 0.48)
        sti = g.math('MULTIPLY', g.band(ax, 0.0135, 0.0155, 0.0004), front)
        base = g.mix(g.math('MULTIPLY', sti, 0.5), base, line)
        bz = g.math('SUBTRACT', g.math('MODULO', g.math('ADD', z, 10.0), 0.09), 0.045)
        dd = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
        g.set(dd.inputs[0], g.n('ShaderNodeCombineXYZ', X=x, Y=bz).outputs[0])
        r = dd.outputs['Value']
        return g.mix(g.math('MULTIPLY', g.band(r, 0.0035, 0.0055, 0.0004), front), base, line)
    return N.cloth(f"M_{A}_Blouse", (0.72, 0.72, 0.7), "cotton", 0.75, wrinkle=0.7, extra=extra)


CFG = dict(
    asset=A, glb="npc_woman3", height=1.63, prep=prep,
    mats={
        "Shirt": blouse,
        "Pants": lambda a, z: N.cloth(f"M_{A}_Slacks", NAVY, "wool", 0.8, dust=0.3),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Shoes", (0.012, 0.011, 0.011), 0.28, sole=(0.02, 0.018, 0.016), sole_h=0.012),
        "Socks": lambda a, z: N.cloth(f"M_{A}_Socks", NAVY, "knit", 0.9, wrinkle=0.3),
        "HairBase": dark("HairBase"), "Hair": dark("Hair"),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.7, 0.49, 0.37)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    watch=dict(style="white", strap=(0.02, 0.02, 0.022), size=0.013),
    notes="회사원 여(30대): 흰 긴소매 블라우스(앞여밈 박음질·단추), 남색 일자 슬랙스, 검정 구두, 어두운 단발, 검정 가죽줄 시계."
          " 줄 선 손님/행인. 키 1.62m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

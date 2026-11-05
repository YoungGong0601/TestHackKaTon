"""NpcStudentWoman: 대학생 여 (줄무늬 티 + 연청 바지 + 흰 캔버스화 + 뿔테 안경, 단발). 원본 npc_woman3."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Vector
import npc_common as N

A = "NpcStudentWoman"
brown = lambda nm: (lambda a, z: N.hair(f"M_{A}_{nm}", (0.032, 0.019, 0.012), style="fine"))


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


CFG = dict(
    asset=A, glb="npc_woman3", height=1.65, glasses=True, prep=prep,
    mats={
        "Shirt": lambda a, z: N.cloth(f"M_{A}_StripeTee", (0.78, 0.76, 0.7), "stripe", 0.85, col2=(0.015, 0.025, 0.07),
                                        sleeve_x=N.bone_head(a, "UpperArm.L").x),
        "Pants": lambda a, z: N.cloth(f"M_{A}_Jeans", (0.075, 0.12, 0.23), "denim", 0.82, col2=(0.2, 0.28, 0.42), dust=0.5),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Canvas", (0.8, 0.79, 0.76), 0.85, sole=(0.72, 0.7, 0.64), sole_h=0.028, canvas=True),
        "Socks": lambda a, z: N.cloth(f"M_{A}_Socks", (0.75, 0.75, 0.73), "knit", 0.9, wrinkle=0.3),
        "HairBase": brown("HairBase"), "Hair": brown("Hair"),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.72, 0.5, 0.37)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    watch=dict(style="white", strap=(0.12, 0.06, 0.03), size=0.014),
    notes="대학생 여(20대): 남색 줄무늬 반팔 티, 연청 청바지, 흰 캔버스화, 짙은 갈색 단발, 뿔테 안경, 가죽줄 시계."
          " 줄 선 손님/행인(yF 대사 가능). 키 1.64m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

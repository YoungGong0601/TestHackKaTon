"""NpcYoungWoman: 20~30대 직장인 여 (베이지 트렌치코트 + 검정 스타킹 + 로퍼). 원본 npc_woman2."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils.bvhtree import BVHTree
import npc_common as N

A = "NpcYoungWoman"


def prep(arm, body, s0):
    wx = N.bone_head(arm, "Palm.L").x * s0
    sl = N.faces(body, lambda c, n, m: m == "Skin" and 0.115 < abs(c.x) * s0 < wx - 0.012 and c.z * s0 > 1.0)
    N.set_mat(body, sl, bpy.data.materials.new("Sleeve"))
    N.push(body, sl, 0.006 / s0)                              # 코트 소매 두께
    hem = min(p.center.z for p in body.data.polygons if body.data.materials[p.material_index].name == "Dress") * s0
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Skin" and 0.03 < c.z * s0 < hem + 0.01), bpy.data.materials.new("Tights"))
    # 코트 자락(밑단 경계 ~ 허리 3면 접합) 을 1cm 밖으로: 서브디비전 뒤 안쪽 엉덩이 면이 뚫고 나와 AO 가 조각나는 것 방지
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.normal_update()
    di = [m.name for m in body.data.materials].index("Dress")
    st = [f for f in bm.faces if f.material_index == di and any(e.is_boundary for e in f.edges)]
    seen = {f.index for f in st}
    skirt = list(st)
    while st:
        for e in st.pop().edges:
            if len(e.link_faces) == 2:
                for g in e.link_faces:
                    if g.index not in seen and g.material_index == di:
                        seen.add(g.index)
                        skirt.append(g)
                        st.append(g)
    vs = {v for f in skirt for v in f.verts if all(len(e.link_faces) <= 2 for e in v.link_edges)}
    off = {v: v.normal * (0.01 / s0) for v in vs}
    for v, o in off.items():
        v.co += o
    # 자락 안에 숨은 엉덩이(Dress) 면은 2cm 안쪽으로 (자락과 거의 겹쳐 AO 가 삼각 조각으로 깨지던 원인)
    sk = set(skirt)
    tree = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in skirt])
    bm.normal_update()
    hid = [f for f in bm.faces if f not in sk and f.material_index == di
           and tree.ray_cast(f.calc_center_median() + f.normal * 1e-4, f.normal, 0.08 / s0)[0] is not None]
    skv = {v for f in skirt for v in f.verts}
    hv = {v for f in hid for v in f.verts if v not in skv}
    off = {v: v.normal * (-0.02 / s0) for v in hv}
    for v, o in off.items():
        v.co += o
    sm = N.slot(body, bpy.data.materials.new("Skirt"))
    for f in skirt:
        f.material_index = sm
    print("npc: 코트 자락 면", len(skirt), "숨은 면", len(hid), "정점", len(hv))
    bm.to_mesh(body.data)
    bm.free()


def trench(nm):
    def make(arm, zr):
        wz = N.bone_head(arm, "Abdomen").z

        def extra(g, base):
            x, y, z = g.xyz()
            ax = g.math('ABSOLUTE', x)
            front = g.math('LESS_THAN', y, -0.02)
            belt = g.band(z, wz - 0.018, wz + 0.018, 0.002)
            base = g.mix(belt, base, (0.3, 0.2, 0.1))
            # 벨트 가장자리 스티치 + 앞 버클(어두운 금속 사각 테)
            bedge = g.math('MAXIMUM', g.band(z, wz - 0.014, wz - 0.012, 0.0006), g.band(z, wz + 0.012, wz + 0.014, 0.0006))
            base = g.mix(g.math('MULTIPLY', bedge, 0.6), base, (0.5, 0.38, 0.22))
            bk = g.math('MULTIPLY', g.math('MULTIPLY', g.band(z, wz - 0.022, wz + 0.022, 0.001), g.band(x, -0.052, -0.016, 0.001)), front)
            hole = g.math('MULTIPLY', g.band(z, wz - 0.014, wz + 0.014, 0.001), g.band(x, -0.045, -0.023, 0.001))
            base = g.mix(g.math('MULTIPLY', bk, g.math('SUBTRACT', 1.0, hole)), base, (0.09, 0.075, 0.055))
            # 더블 버튼 2열
            bz = g.math('MULTIPLY', g.band(z, wz + 0.06, wz + 0.3, 0.002), g.math('LESS_THAN', y, -0.03))
            bx = g.band(g.math('ABSOLUTE', g.math('SUBTRACT', ax, 0.045)), -1.0, 0.007, 0.002)
            row = g.ramp(g.wave(0.08, 'Z', profile='SAW'), [(0.0, (0,)), (0.02, (1,)), (0.16, (1,)), (0.18, (0,))])
            btn = g.math('MULTIPLY', g.math('MULTIPLY', bz, bx), row)
            base = g.mix(btn, base, (0.06, 0.035, 0.02))
            # 앞여밈 솔기 (중심에서 2.5cm 옆, 벨트 아래 자락까지)
            plk = g.math('MULTIPLY', g.math('MULTIPLY', g.band(x, 0.023, 0.027, 0.001), front), g.band(z, 0.0, wz + 0.32, 0.002))
            base = g.mix(g.math('MULTIPLY', plk, 0.75), base, (0.13, 0.085, 0.045))
            # 사선 주머니 덮개 (벨트 아래 양옆) + 아래 그림자 선
            pz = g.math('SUBTRACT', z, g.math('MULTIPLY', ax, 0.25))
            pk = g.math('MULTIPLY', g.math('MULTIPLY', g.band(pz, wz - 0.19, wz - 0.155, 0.0015), g.band(ax, 0.075, 0.15, 0.0015)), front)
            base = g.mix(g.math('MULTIPLY', pk, 0.3), base, (0.22, 0.15, 0.08))
            pl = g.math('MULTIPLY', g.math('MULTIPLY', g.band(pz, wz - 0.193, wz - 0.188, 0.001), g.band(ax, 0.075, 0.15, 0.0015)), front)
            base = g.mix(pl, base, (0.1, 0.065, 0.035))
            return base
        return N.cloth(f"M_{A}_{nm}", (0.4, 0.28, 0.15), "twill", 0.78, extra=extra)
    return make


def tights(arm, zr):
    g = N.G(f"M_{A}_Tights")
    sheer = g.ramp(g.n('ShaderNodeLayerWeight', Blend=0.35).outputs['Facing'], [(0.0, (0.09, 0.055, 0.04)), (0.6, (0.012, 0.01, 0.01))])
    return g.out(sheer, 0.45, g.bump(g.noise(600, 2), 0.1, 0.0002))


CFG = dict(
    asset=A, glb="npc_woman2", height=1.64, prep=prep,
    mats={
        "Dress": trench("TrenchCoat"), "Sleeve": trench("Sleeve"), "Skirt": trench("Skirt"),
        "Tights": tights,
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.72, 0.5, 0.37)),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Loafers", (0.035, 0.018, 0.01), 0.3, sole=(0.02, 0.015, 0.01), sole_h=0.012),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.03, 0.017, 0.011)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    watch=dict(style="gold", strap=(0.06, 0.03, 0.015), size=0.013),
    notes="직장인 여(20~30대): 베이지 트렌치코트(허리 벨트+버클·더블 버튼·앞여밈 솔기·사선 주머니 덮개·긴소매), 검정 스타킹, 갈색 로퍼, 짙은 갈색 포니테일, 가죽줄 시계."
          " '뭐 하시는 거야...', '왜 저렇게 오래 걸려.'(yF) 용, 끼어들기 장면은 Tap 클립. 키 1.63m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

"""NpcStudentB: 대학생 남 (초록 맨투맨 + 검정 바지 + 흰 운동화, 짙은 갈색 머리, 가방 없음). 원본 npc_man1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import npc_common as N

A = "NpcStudentB"
GREEN = (0.018, 0.2, 0.085)
RIB = (0.01, 0.1, 0.045)


def prep(arm, body, s0):
    # 원본은 신발이 Eyes 재질 -> 발 부분만 Shoes 로 분리
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Eyes" and c.z * s0 < 0.3), bpy.data.materials.new("Shoes"))


def sweatshirt(a, zr):
    zmin = zr["Shirt"][0]                                  # 밑단 근처 면 높이 (rest)
    wx = N.bone_head(a, "Palm.L").x                        # 손목 (T포즈 팔 = X축)
    k = N.bone_head(a, "Neck")

    def extra(g, base):
        # 밑단·소맷단·목둘레 골지 시보리
        x, y, z = g.xyz()
        ax = g.math('ABSOLUTE', x)
        hem = g.math('MULTIPLY', g.band(z, zmin - 0.1, zmin + 0.045, 0.002), g.math('LESS_THAN', ax, wx - 0.3))
        cuff = g.band(ax, wx - 0.07, wx + 0.05, 0.002)
        # 목둘레 = 원본 메시의 후드 자리 고리: 목 축에서 9.2cm 안쪽, 뒤가 앞보다 높게 기운 평면 위
        dn = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
        g.set(dn.inputs[0], g.n('ShaderNodeCombineXYZ', X=x, Y=g.math('SUBTRACT', y, k.y)).outputs[0])
        plane = g.math('SUBTRACT', z, g.math('MULTIPLY', y, 0.18))
        neck = g.math('MULTIPLY', g.band(dn.outputs['Value'], -1.0, 0.092), g.band(plane, k.z - 0.18 * k.y - 0.023, 9.0))
        rib = g.mix(cuff, g.wave(0.0045, 'X', profile='TRI'), g.wave(0.0045, 'Z', profile='TRI'))
        ribm = g.math('MAXIMUM', g.math('MAXIMUM', hem, cuff), neck)
        return g.mix(g.math('MULTIPLY', ribm, g.math('ADD', 0.45, g.math('MULTIPLY', rib, 0.35))), base, RIB)
    return N.cloth(f"M_{A}_Sweatshirt", GREEN, "fleece", 0.92, extra=extra)


CFG = dict(
    asset=A, glb="npc_man1", height=1.74, prep=prep,
    mats={
        "Shirt": sweatshirt,
        "Pants": lambda a, z: N.cloth(f"M_{A}_Pants", (0.016, 0.016, 0.018), "twill", 0.8, dust=0.3),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Sneakers", (0.72, 0.71, 0.69), 0.5, sole=(0.5, 0.48, 0.44), sole_h=0.026),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.62, 0.41, 0.29)),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.04, 0.022, 0.014)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    watch=dict(style="black", strap=(0.02, 0.02, 0.022), size=0.019),
    notes="대학생 남(20대): 초록 맨투맨(짙은 골지 목둘레·밑단·소맷단), 검정 바지, 흰 운동화, 짙은 갈색 머리, 검정 손목시계, 가방 없음."
          " 줄 선 손님/행인. 키 1.73m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

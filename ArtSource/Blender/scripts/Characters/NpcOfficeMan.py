"""NpcOfficeMan: 직장인 남 (반팔 와이셔츠 + 넥타이 + 슬랙스 + 사원증). 원본 npc_man2."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Vector
import npc_common as N

A = "NpcOfficeMan"


def shirt(tie):
    def make(arm, zr):
        nz = N.bone_head(arm, "Neck").z

        def extra(g, base):
            x, y, z = g.xyz()
            ax = g.math('ABSOLUTE', x)
            front = g.math('LESS_THAN', y, -0.03)
            # 앞여밈 플래킷: 3cm 띠 양옆 박음질 + 띠는 두 겹이라 살짝 진함
            plk = g.math('MULTIPLY', g.math('LESS_THAN', ax, 0.015), front)
            base = g.mix(g.math('MULTIPLY', plk, 0.12), base, (0.45, 0.5, 0.6))
            sti = g.math('MULTIPLY', g.band(ax, 0.0135, 0.0155, 0.0004), front)
            base = g.mix(g.math('MULTIPLY', sti, 0.5), base, (0.4, 0.45, 0.55))
            # 단추 (9cm 간격, 지름 1cm, 반투명 흰 단추 + 테두리)
            bz = g.math('SUBTRACT', g.math('MODULO', g.math('ADD', z, 10.0), 0.09), 0.045)
            dd = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
            g.set(dd.inputs[0], g.n('ShaderNodeCombineXYZ', X=x, Y=bz).outputs[0])
            r = dd.outputs['Value']
            btn = g.math('MULTIPLY', g.ramp(r, [(0.0045, (1,)), (0.0055, (0,))]), front)
            ring = g.math('MULTIPLY', g.band(r, 0.0042, 0.0052, 0.0004), front)
            base = g.mix(btn, base, (0.86, 0.87, 0.86))
            base = g.mix(g.math('MULTIPLY', ring, 0.5), base, (0.45, 0.47, 0.5))
            # 왼쪽 가슴 주머니 (박음질 사각 + 위 접단)
            tz = N.bone_head(arm, "Torso").z
            px = g.band(x, 0.045, 0.105, 0.0006)
            pz = g.band(z, tz + 0.075, tz + 0.18, 0.0006)
            inner = g.math('MULTIPLY', g.math('MULTIPLY', g.band(x, 0.048, 0.102, 0.0006), g.band(z, tz + 0.078, tz + 0.177, 0.0006)), front)
            edge = g.math('MULTIPLY', g.math('SUBTRACT', g.math('MULTIPLY', px, pz), inner), front)
            base = g.mix(g.math('MULTIPLY', edge, 0.55), base, (0.4, 0.45, 0.55))
            hemp = g.math('MULTIPLY', g.math('MULTIPLY', px, g.band(z, tz + 0.158, tz + 0.161, 0.0004)), front)
            base = g.mix(g.math('MULTIPLY', hemp, 0.45), base, (0.4, 0.45, 0.55))
            if not tie:
                return base
            top, bot = nz - 0.035, zr["Shirt2"][0] + 0.05
            w = g.math('ADD', 0.014, g.math('MULTIPLY', g.math('SUBTRACT', top, z), 0.024 / (top - bot)))
            m = g.math('MULTIPLY', g.math('LESS_THAN', g.math('ABSOLUTE', x), w), g.band(z, bot, top, 0.003))
            m = g.math('MULTIPLY', m, g.math('LESS_THAN', y, -0.02))
            st = g.ramp(g.wave(0.011, 'X', vec=g.vmap(rot=(0, math.radians(40), 0)), profile='TRI'), [(0.78, (0,)), (0.84, (1,))])
            return g.mix(m, base, g.mix(st, (0.022, 0.03, 0.09), (0.32, 0.05, 0.05)))
        return N.cloth(f"M_{A}_Shirt{'Tie' if tie else ''}", (0.70, 0.76, 0.86), "cotton", 0.75, extra=extra)
    return make


def slacks(arm, zr):
    top = zr["Pants"][1]

    def extra(g, base):
        x, y, z = g.xyz()
        belt = g.band(z, top - 0.032, top + 0.01, 0.002)
        base = g.mix(belt, base, (0.018, 0.013, 0.011))
        buckle = g.math('MULTIPLY', belt, g.math('MULTIPLY', g.math('LESS_THAN', g.math('ABSOLUTE', x), 0.022), g.math('LESS_THAN', y, -0.03)))
        return g.mix(buckle, base, (0.55, 0.55, 0.57))
    return N.cloth(f"M_{A}_Slacks", (0.028, 0.03, 0.036), "wool", 0.78, extra=extra, dust=0.6)


def collar_tie(arm, body):
    """레귤러 칼라(깃대 3cm + 깃 날개, 앞 끝 벌어짐) + 넥타이 매듭. 웨이트는 몸에서 복사."""
    out = N.lanyard_card(arm, body, A)
    zb, zf, c = N.neckline(body, (f"M_{A}_ShirtTie", f"M_{A}_Shirt"), f"M_{A}_Skin")
    tree = N.bvh(body)
    rows = [
        (lambda f: -0.004, lambda f: 0.003, 1.0),                    # 깃대 아래 (목선)
        (lambda f: 0.03, lambda f: 0.006, 1.0),                      # 깃대 위 3cm
        (lambda f: 0.034, lambda f: 0.011, 1.0),                     # 접힌 선
        (lambda f: -0.035 - 0.04 * (1 - f) ** 2, lambda f: 0.004, 0.84),  # 깃 날개 끝 (뒤 3.5cm, 옆 4.5cm, 앞 7.5cm, 앞 끝 벌어짐)
    ]
    bm = N.neck_loft(tree, rows, -172, 172, zb, zf, c, slope=0.4)
    shirt = N.cloth(f"M_{A}_Collar", (0.70, 0.76, 0.86), "cotton", 0.75, wrinkle=0.3)
    out.append(N.shell_obj(A + "_Collar", bm, shirt, body, thick=0.0025, subd=1))
    # 넥타이 매듭: 위 3.5cm -> 아래 2cm 쐐기, 깃대 앞
    h = tree.ray_cast(Vector((c.x, -0.6, zf + 0.012)), Vector((0, 1, 0)), 1.0)
    fy = h[0].y if h[0] is not None else c.y - 0.06
    bm = bmesh.new()
    for v in N.box(bm, Vector((0, fy - 0.011, zf + 0.006)), (0.034, 0.014, 0.04)):
        if v.co.z < zf + 0.006:
            v.co.x *= 0.6
            v.co.y += 0.003
    knot = N.cloth(f"M_{A}_TieKnot", (0.022, 0.03, 0.09), "twill", 0.55, wrinkle=0.2,
                   extra=lambda g, base: g.mix(g.ramp(g.wave(0.011, 'X', vec=g.vmap(rot=(0, math.radians(40), 0)), profile='TRI'),
                                                      [(0.78, (0,)), (0.84, (1,))]), base, (0.32, 0.05, 0.05)))
    out.append(N.shell_obj(A + "_TieKnot", bm, knot, body, thick=0, subd=2, bevel=0.004))
    return out


CFG = dict(
    asset=A, glb="npc_man2", height=1.74,
    mats={
        "Shirt2": shirt(True), "Shirt": shirt(False),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.60, 0.39, 0.27)),
        "Pants": slacks,
        "Shoes": lambda a, z: N.leather(f"M_{A}_Shoes", (0.012, 0.011, 0.011), 0.25, sole=(0.02, 0.018, 0.016), sole_h=0.015),
        "Socks": lambda a, z: N.cloth(f"M_{A}_Socks", (0.02, 0.022, 0.035), "knit", 0.8, wrinkle=0.3),
        "Hair2": lambda a, z: N.hair(f"M_{A}_Hair2", (0.018, 0.014, 0.012)),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.018, 0.014, 0.012)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=collar_tie,
    keep=(f"M_{A}_IdCard",),                     # 사원증은 굽지 않고 640x1024 데칼을 그대로 (아틀라스에선 글씨가 뭉개짐)
    watch=dict(style="white", strap=(0.6, 0.6, 0.62), metal=True),
    notes="직장인 남(30대): 하늘색 반팔 와이셔츠(레귤러 칼라·앞 플래킷·단추·왼쪽 가슴 주머니)+남색 사선 넥타이(매듭)+차콜 슬랙스+검정 구두,"
          " 사원증(한빛물산 김민수 대리, 증명사진) 목걸이, 은색 손목시계. 점심시간 줄 서는 손님/행인. 키 1.73m(validate)."
          " 머티리얼 2개: M_NpcOfficeMan_Body(구운 2048) + M_NpcOfficeMan_IdCard(사원증 앞면 데칼 640x1024, 굽지 않음).",
)

if __name__ == "__main__":
    N.run(CFG)

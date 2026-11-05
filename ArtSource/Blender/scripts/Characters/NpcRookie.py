"""NpcRookie: 2회차 신입 사원 (20대 후반 남, 흰 긴팔 와이셔츠, 넥타이 없음, 남색 슬랙스, 사원증). 바탕 NpcOfficeMan, 원본 npc_man2.
말 걸기 대상이라 같은 몸의 NpcOfficeMan(하늘색 반팔, 넥타이)과 3m 에서 갈려야 한다."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import npc_common as N
from NpcElder import fit_watch

A = "NpcRookie"
WHITE = (0.84, 0.84, 0.82)
SEAM = (0.62, 0.62, 0.61)        # 박음질, 두 겹 그늘
SKIN = (0.66, 0.45, 0.33)
CARD = """
import sys, os
from PIL import Image, ImageDraw, ImageFont
F = lambda w, s: ImageFont.truetype(os.path.expanduser(f"~/Library/Fonts/NanumSquare{w}.ttf"), s)
im = Image.open(os.path.join(sys.argv[1], "npc_idcard.png"))
d = ImageDraw.Draw(im)
d.rectangle((0, 680, 640, 880), fill=(246, 246, 242))
d.text((320, 745), "이도윤", font=F("EB", 104), fill=(20, 20, 26), anchor="mm")
d.text((320, 838), "영업2팀  사원", font=F("B", 50), fill=(60, 60, 72), anchor="mm")
im.save(os.path.join(sys.argv[1], "npc_idcard_rookie.png"))
"""


def prep(arm, body, s0):
    # 긴팔: 팔 맨살을 손목 위 7cm 고리까지 셔츠로
    cut = N.bone_head(arm, "Palm.L").x - 0.07 / s0
    sleeve = N.faces(body, lambda c, n, m: m == "Skin" and 0.3 / s0 < abs(c.x) < cut)
    N.set_mat(body, sleeve, next(m for m in body.data.materials if m.name == "Shirt"))
    N.push(body, sleeve, 0.005 / s0)


def shirt(name):
    def make(arm, zr):
        nz = N.bone_head(arm, "Neck").z
        tz = N.bone_head(arm, "Torso").z

        def extra(g, base):
            x, y, z = g.xyz()
            ax = g.math('ABSOLUTE', x)
            front = g.math('LESS_THAN', y, -0.03)
            # 앞여밈 플래킷: 3cm 띠 양옆 박음질 + 띠는 두 겹이라 살짝 진함
            plk = g.math('MULTIPLY', g.math('LESS_THAN', ax, 0.015), front)
            base = g.mix(g.math('MULTIPLY', plk, 0.12), base, SEAM)
            sti = g.math('MULTIPLY', g.band(ax, 0.0135, 0.0155, 0.0004), front)
            base = g.mix(g.math('MULTIPLY', sti, 0.5), base, SEAM)
            # 단추 (9cm 간격, 지름 1cm, 반투명 흰 단추 + 테두리)
            bz = g.math('SUBTRACT', g.math('MODULO', g.math('ADD', z, 10.0), 0.09), 0.045)
            dd = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
            g.set(dd.inputs[0], g.n('ShaderNodeCombineXYZ', X=x, Y=bz).outputs[0])
            r = dd.outputs['Value']
            ring = g.math('MULTIPLY', g.band(r, 0.0042, 0.0052, 0.0004), front)
            base = g.mix(g.math('MULTIPLY', ring, 0.6), base, (0.4, 0.4, 0.41))
            # 왼쪽 가슴 주머니 (박음질 사각 + 위 접단)
            px = g.band(x, 0.045, 0.105, 0.0006)
            pz = g.band(z, tz + 0.075, tz + 0.18, 0.0006)
            inner = g.math('MULTIPLY', g.math('MULTIPLY', g.band(x, 0.048, 0.102, 0.0006), g.band(z, tz + 0.078, tz + 0.177, 0.0006)), front)
            edge = g.math('MULTIPLY', g.math('SUBTRACT', g.math('MULTIPLY', px, pz), inner), front)
            base = g.mix(g.math('MULTIPLY', edge, 0.55), base, SEAM)
            hemp = g.math('MULTIPLY', g.math('MULTIPLY', px, g.band(z, tz + 0.158, tz + 0.161, 0.0004)), front)
            base = g.mix(g.math('MULTIPLY', hemp, 0.45), base, SEAM)
            # 넥타이 없이 첫 단추를 풀었다: 목 아래 맨살 V
            zo = nz - 0.08
            v = g.math('LESS_THAN', ax, g.math('MULTIPLY', g.math('SUBTRACT', z, zo), 0.42))
            return g.mix(g.math('MULTIPLY', v, g.math('LESS_THAN', y, 0.03)), base, SKIN)
        return N.cloth(f"M_{A}_{name}", WHITE, "cotton", 0.75, extra=extra)
    return make


def slacks(arm, zr):
    top = zr["Pants"][1]

    def extra(g, base):
        x, y, z = g.xyz()
        belt = g.band(z, top - 0.032, top + 0.01, 0.002)
        base = g.mix(belt, base, (0.018, 0.013, 0.011))
        buckle = g.math('MULTIPLY', belt, g.math('MULTIPLY', g.math('LESS_THAN', g.math('ABSOLUTE', x), 0.022), g.math('LESS_THAN', y, -0.03)))
        return g.mix(buckle, base, (0.55, 0.55, 0.57))
    return N.cloth(f"M_{A}_Slacks", (0.014, 0.022, 0.06), "wool", 0.78, extra=extra, dust=0.6)


def collar(arm, body):
    """사원증 + 넥타이 없이 벌어진 레귤러 칼라. 웨이트는 몸에서 복사."""
    out = N.lanyard_card(arm, body, A)
    subprocess.run([N.VENV_PY, "-c", CARD, N.decals()], check=True)   # 카드는 NpcOfficeMan 의 대리 김민수라 이름과 직급만 바꾼다
    nodes = out[0].data.materials[0].node_tree.nodes
    next(n for n in nodes if n.type == 'TEX_IMAGE').image = bpy.data.images.load(os.path.join(N.decals(), "npc_idcard_rookie.png"))
    zb, zf, c = N.neckline(body, (f"M_{A}_ShirtFront", f"M_{A}_Shirt"), f"M_{A}_Skin")
    lift = 0.02                                  # neck_loft 의 목선 레이를 2cm 올린다. 어깨가 목선보다 높아 옆 레이가 어깨에 맞으면 깃이 망토처럼 벌어진다
    rows = [
        (lambda f: -0.004 - lift, lambda f: 0.003, 1.0),             # 깃대 아래 (목선)
        (lambda f: 0.028 - lift, lambda f: 0.006, 1.0),              # 깃대 위
        (lambda f: 0.032 - lift, lambda f: 0.011, 1.0),              # 접힌 선
        (lambda f: -0.022 - 0.035 * (1 - f) ** 2 - lift, lambda f: 0.006, 0.9),  # 깃 날개 끝
    ]
    bm = N.neck_loft(N.bvh(body), rows, -158, 158, zb + lift, zf + lift, c, slope=0.4)
    out.append(N.shell_obj(A + "_Collar", bm, N.cloth(f"M_{A}_Collar", WHITE, "cotton", 0.75, wrinkle=0.3), body, thick=0.0025, subd=1))
    return out


CFG = dict(
    asset=A, glb="npc_man2", height=1.74, prep=prep,
    mats={
        "Shirt2": shirt("ShirtFront"), "Shirt": shirt("Shirt"),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", SKIN),
        "Pants": slacks,
        "Shoes": lambda a, z: N.leather(f"M_{A}_Shoes", (0.012, 0.011, 0.011), 0.25, sole=(0.02, 0.018, 0.016), sole_h=0.015),
        "Socks": lambda a, z: N.cloth(f"M_{A}_Socks", (0.012, 0.016, 0.04), "knit", 0.8, wrinkle=0.3),
        "Hair2": lambda a, z: N.hair(f"M_{A}_Hair2", (0.01, 0.01, 0.013), style="fine"),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.01, 0.01, 0.013), style="fine"),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=collar,
    keep=(f"M_{A}_IdCard",),                     # 사원증은 굽지 않고 640x1024 데칼을 그대로 (아틀라스에선 글씨가 뭉개짐)
    watch=dict(style="black", strap=(0.012, 0.012, 0.013)),
    notes="신입 사원 남(20대 후반): 흰 긴팔 와이셔츠(넥타이 없음, 첫 단추 풂, 왼쪽 가슴 주머니), 남색 슬랙스, 검정 구두, 검은 머리,"
          " 사원증(한빛물산 이도윤 사원) 목걸이, 검정 시계. 2회차 말 걸기 대상. 키 1.73m(validate)."
          " 머티리얼 2개: M_NpcRookie_Body(구운 2048) + M_NpcRookie_IdCard(사원증 앞면 데칼 640x1024, 굽지 않음).",
)

if __name__ == "__main__":
    N.watch = fit_watch
    N.run(CFG)

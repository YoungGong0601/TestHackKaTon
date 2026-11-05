"""NpcElder: 80대 남 (회갈색 뜨개 카디건 + 미색 셔츠 + 회갈색 바지 + 안경, 흰머리). 바탕 NpcOldMan, 원본 npc_man4.
1회차 매장 어르신이자 4회차의 플레이어 자신이라 1인칭 소매(GrandpaHand: 헤더 뜨개, 고무단, 스틸 시계, 갈색 가죽 줄)와 같게 입힌다."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npc_common as N
import NpcOldMan as O

A = "NpcElder"
KNIT = (0.117, 0.091, 0.072)     # sRGB (96, 85, 76) = GrandpaHand_tex.knit_tile 의 base
SHIRT = (0.62, 0.60, 0.53)
watch0 = N.watch


def fit_watch(arm, body, asset, **kw):
    """N.watch 의 줄은 뼈 축을 도는 원이라 납작한 손목에서 3cm 뜬다. 줄을 손목 표면에 붙이고 케이스를 손등에 내린다."""
    parts, top = watch0(arm, body, asset, **kw)
    a0, a1 = N.bone_head(arm, "LowerArm.L"), N.bone_head(arm, "Palm.L")
    ax = (a1 - a0).normalized()
    c = a1 - ax * 0.035
    r = N.arm_radius(body, c, ax)
    tree = N.bvh(body)
    skin = lambda o, d: tree.ray_cast(o + d * 0.2, -d, 0.3)[0]
    for v in parts[0].data.vertices:
        o = c + ax * (v.co - c).dot(ax)
        d = v.co - o
        v.co = skin(o, d.normalized()) + d.normalized() * (d.length - r + 0.001)
    up = (top - c).normalized()
    down = up * ((skin(c, up) - c).dot(up) - r)
    for o in parts[1:]:
        for v in o.data.vertices:
            v.co += down
    return parts, top + down


def prep(arm, body, s0):
    O.prep(arm, body, s0)                                # 구두 재질 분리, 어깨 풍선 줄임
    mat = lambda nm: next(m for m in body.data.materials if m and m.name == nm)
    # 앞을 여민다: 안쪽 셔츠 자리까지 전부 카디건. 앞섶 V 와 셔츠는 재질에서 그린다
    N.set_mat(body, N.faces(body, lambda c, n, m: m in ("Details", "TieTexture")), mat("Shirt"))
    # 밑단을 앞 중앙 높이로 고른다 (앞판 모서리만 3cm 처져 있었다)
    zh = N.bone_head(arm, "Abdomen").z + 0.055 / s0
    si = [m.name for m in body.data.materials].index("Shirt")
    for i in {i for p in body.data.polygons if p.material_index == si for i in p.vertices}:
        body.data.vertices[i].co.z = max(body.data.vertices[i].co.z, zh)
    # 뒤통수 맨살을 머리로 (뒷모습이 주로 보이는데 머리가 귀 위에서 끊겼다)
    hz = N.bone_head(arm, "Head").z * s0
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Skin" and c.z * s0 > hz + 0.01 and c.y * s0 > 0.02), mat("Hair"))
    # 소매를 6.5cm 올려 손목을 드러낸다 (시계가 맨살 위에 있는 1인칭 손과 같게). 손 시작 고리는 두어 맨살 면이 늘어난다
    for s in "LR":
        a0, a1 = N.bone_head(arm, f"LowerArm.{s}"), N.bone_head(arm, f"Palm.{s}")
        ax = (a1 - a0).normalized()
        for v in body.data.vertices:
            if 0.19 / s0 < (v.co - a0).dot(ax) < 0.295 / s0:
                v.co -= ax * (0.065 / s0)


def rib(g, u, v, n):
    """각도 atan2(u, v) 를 n 등분한 세로 골."""
    return g.ramp(g.math('SINE', g.math('MULTIPLY', g.math('ARCTAN2', u, v), n)), [(0.0, (0,)), (0.5, (1,))])


def cardigan(arm, zr):
    zv = N.bone_head(arm, "Torso").z + 0.07              # 앞섶 V 끝
    k = 0.28                                              # V 기울기 |x| / z
    palm = N.bone_head(arm, "Palm.L")
    zmin = zr["Shirt"][0]
    dark = N._shade(KNIT, 0.72)

    def extra(g, base):
        x, y, z = g.xyz()
        ax = g.math('ABSOLUTE', x)
        front = g.math('LESS_THAN', y, 0.03)
        # 헤더 원사: 밝고 어두운 올이 섞인 잔 얼룩
        fleck = g.ramp(g.noise(240, 3, 0.7), [(0.38, (0,)), (0.62, (1,))])
        base = g.mix(g.math('MULTIPLY', fleck, 0.7), base, N._shade(KNIT, 1.3))
        # 고무단: 밑단 5cm, 소맷단 6cm
        ribc = lambda s: g.mix(s, N._shade(KNIT, 0.7), N._shade(KNIT, 1.0))
        base = g.mix(g.band(z, zmin - 1.0, zmin + 0.05, 0.002), base, ribc(rib(g, x, y, 56)))
        cuff = g.math('GREATER_THAN', ax, palm.x - 0.14)
        base = g.mix(cuff, base, ribc(rib(g, g.math('SUBTRACT', z, palm.z), g.math('SUBTRACT', y, palm.y), 22)))
        # 앞섶: V 안은 셔츠, V 테두리 2.3cm 고무 띠, V 아래 앞단 2.8cm
        e = g.math('SUBTRACT', ax, g.math('MULTIPLY', g.math('SUBTRACT', z, zv), k))
        above = g.math('GREATER_THAN', z, zv)
        placket = g.math('MULTIPLY', g.band(ax, -1.0, 0.014, 0.0008), g.math('LESS_THAN', z, zv + 0.03))
        band = g.math('MAXIMUM', g.math('MULTIPLY', g.band(e, -0.002, 0.023, 0.0008), above), placket)
        base = g.mix(g.math('MULTIPLY', band, front), base, dark)
        base = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', g.math('LESS_THAN', e, -0.002), above), front), base, SHIRT)
        # 앞 단추 4개: 5.2cm 간격, 지름 1.7cm
        bz = g.math('SUBTRACT', g.math('MODULO', g.math('ADD', z, 10.0 - zv + 0.038), 0.052), 0.026)
        dd = g.n('ShaderNodeVectorMath', {"operation": 'LENGTH'})
        g.set(dd.inputs[0], g.n('ShaderNodeCombineXYZ', X=x, Y=bz).outputs[0])
        r = dd.outputs['Value']
        on = g.math('MULTIPLY', front, g.band(z, zmin + 0.055, zv, 0.001))
        base = g.mix(g.math('MULTIPLY', g.ramp(r, [(0.0075, (1,)), (0.0085, (0,))]), on), base, (0.02, 0.012, 0.008))
        return g.mix(g.math('MULTIPLY', g.band(r, 0.0035, 0.0055, 0.0005), on), base, (0.07, 0.045, 0.03))
    return N.cloth(f"M_{A}_Cardigan", KNIT, "knit", 0.92, wrinkle=0.8, extra=extra)


def collar(arm, body):
    """셔츠 칼라 (깃대 2.5cm + 깃 날개), 몸 웨이트 복사."""
    zb, zf, c = N.neckline(body, (f"M_{A}_Cardigan",), f"M_{A}_Skin")
    rows = [
        (lambda f: -0.004, lambda f: 0.003, 1.0),
        (lambda f: 0.025, lambda f: 0.005, 1.0),
        (lambda f: 0.029, lambda f: 0.009, 1.0),
        (lambda f: -0.02 - 0.03 * (1 - f) ** 2, lambda f: 0.007, 0.9),
    ]
    bm = N.neck_loft(N.bvh(body), rows, -168, 168, zb, zf, c, slope=0.4)
    mat = N.cloth(f"M_{A}_Collar", SHIRT, "cotton", 0.8, wrinkle=0.3)
    return [N.shell_obj(A + "_Collar", bm, mat, body, thick=0.0025, subd=1)]


def shoes(arm, zr):
    """짙은 갈색 구두. N.leather 는 바닥 먼지가 색을 회색으로 덮어 cloth 로 칠한다."""
    sole = lambda g, base: g.mix(g.band(g.xyz()[2], -1.0, 0.02, 0.002), base, (0.02, 0.018, 0.016))
    return N.cloth(f"M_{A}_Shoes", (0.04, 0.022, 0.013), "twill", 0.5, wrinkle=0.3, extra=sole)


CFG = dict(
    asset=A, glb="npc_man4", height=1.68, prep=prep, glasses=True,
    mats={
        "Shirt": cardigan,
        "Pants": lambda a, z: N.cloth(f"M_{A}_Pants", (0.147, 0.124, 0.098), "wool", 0.85),
        "Shoes": shoes,
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.50, 0.31, 0.23)),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.72, 0.71, 0.68), style="fine"),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=collar,
    watch=dict(style="white", strap=(0.07, 0.035, 0.018)),
    notes="80대 남: 회갈색 헤더 뜨개 카디건(sRGB 96,85,76, V 앞섶, 앞단 띠, 앞 단추 4개, 밑단과 소맷단 고무단), 미색 셔츠와 칼라, 회갈색 바지, 짙은 갈색 구두,"
          " 흰머리와 흰 수염, 안경, 스틸 케이스에 짙은 갈색 가죽 줄 시계(왼 손목 맨살). 1회차 매장 어르신이자 4회차 플레이어 자신. 소매와 시계는 GrandpaHand 와 맞춤. 키 1.67m(validate).",
)

if __name__ == "__main__":
    N.watch = fit_watch
    N.run(CFG)

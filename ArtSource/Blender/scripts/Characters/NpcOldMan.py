"""NpcOldMan: 60대 남 (등산 바람막이 + 체크 셔츠 + 등산바지 + 안경). 원본 npc_man4."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import npc_common as N

A = "NpcOldMan"


def prep(arm, body, s0):
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Eyes" and c.z * s0 < 0.3), bpy.data.materials.new("Shoes"))
    # 풍선처럼 부푼 어깨: 서브디비전 전에 어깨 위 정점을 1.2cm 안으로
    sz = N.bone_head(arm, "UpperArm.L").z
    sx = N.bone_head(arm, "Shoulder.L").x
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.normal_update()
    si = [m.name for m in body.data.materials].index("Shirt")
    vs = {v for f in bm.faces if f.material_index == si for v in f.verts}
    off = {}
    for v in vs:
        ax = abs(v.co.x)
        if v.co.z > sz - 0.06 / s0 and sx * 0.9 < ax < sx + 0.16 / s0 and v.normal.z > 0.3:
            w = min(1.0, (v.co.z - (sz - 0.06 / s0)) / (0.05 / s0))
            off[v] = -v.normal * (0.012 / s0) * w
    for v, o in off.items():
        v.co += o
    bm.to_mesh(body.data)
    bm.free()


def jacket(arm, zr):
    tz = N.bone_head(arm, "Torso").z
    wx = N.bone_head(arm, "Palm.L").x
    body = bpy.data.objects[A + "_Body"]
    me = body.data
    si = [m.name for m in me.materials].index("Shirt")
    # 앞 열림 가장자리 |x| = a + b*z (바람막이 앞면 중 가장 안쪽, 높이별)
    pts = []
    for z0 in [tz - 0.25 + 0.05 * k for k in range(10)]:
        xs = [abs(p.center.x) for p in me.polygons if p.material_index == si and p.normal.y < -0.3 and abs(p.center.z - z0) < 0.025]
        if xs:
            pts.append((z0, min(xs)))
    n = len(pts)
    mz, mx = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    b = sum((p[0] - mz) * (p[1] - mx) for p in pts) / max(1e-9, sum((p[0] - mz) ** 2 for p in pts))
    a = mx - b * mz
    zmin = zr["Shirt"][0]

    def extra(g, base):
        x, y, z = g.xyz()
        ax = g.math('ABSOLUTE', x)
        front = g.math('LESS_THAN', y, -0.02)
        yoke_z = tz + 0.11
        yoke = g.band(z, yoke_z, tz + 2.0, 0.004)              # 어깨 배색 (등산복 투톤)
        base = g.mix(yoke, base, (0.42, 0.055, 0.03))
        # 햇빛 바램: 위를 보는 면(어깨·등 위·팔 위)
        nz = g.xyz(g.n('ShaderNodeNewGeometry').outputs['Normal'])[2]
        fade = g.math('MULTIPLY', g.ramp(nz, [(0.2, (0,)), (0.8, (1,))]), g.ramp(g.noise(6, 2), [(0.3, (0.6,)), (0.7, (1,))]))
        base = g.mix(g.math('MULTIPLY', fade, 0.3), base, g.mix(yoke, (0.12, 0.14, 0.2), (0.55, 0.2, 0.15)))
        # 배색 경계 파이핑 (회색 반사 띠)
        base = g.mix(g.band(z, yoke_z - 0.0035, yoke_z + 0.0005, 0.0006), base, (0.5, 0.5, 0.52))
        # 앞 열림 지퍼 테이프 (1.2cm) + 이빨
        e = g.math('SUBTRACT', ax, g.math('ADD', a, g.math('MULTIPLY', z, b)))
        tape = g.math('MULTIPLY', g.band(e, -0.002, 0.012, 0.0008), front)
        teeth = g.math('MULTIPLY', g.math('MULTIPLY', g.band(e, -0.002, 0.004, 0.0006), front),
                       g.ramp(g.wave(0.004, 'Z', profile='TRI'), [(0.45, (0,)), (0.55, (1,))]))
        base = g.mix(tape, base, (0.015, 0.016, 0.022))
        base = g.mix(teeth, base, (0.1, 0.1, 0.11))
        # 오른쪽 가슴 사선 지퍼 주머니 + 손잡이
        d = g.math('SUBTRACT', g.math('ADD', x, 0.085), g.math('MULTIPLY', g.math('SUBTRACT', z, tz + 0.07), -0.35))
        zp = g.math('MULTIPLY', g.math('MULTIPLY', g.band(d, -0.003, 0.003, 0.0006), g.band(z, tz + 0.01, tz + 0.15, 0.001)), front)
        base = g.mix(zp, base, (0.02, 0.02, 0.025))
        pull = g.math('MULTIPLY', g.math('MULTIPLY', g.band(d, -0.004, 0.004, 0.0006), g.band(z, tz + 0.125, tz + 0.155, 0.001)), front)
        base = g.mix(pull, base, (0.35, 0.35, 0.37))
        # 왼쪽 가슴 가상 브랜드 패치 (흰 사각 + 남색 산)
        pr = g.math('MULTIPLY', g.math('MULTIPLY', g.band(x, 0.07, 0.11, 0.0006), g.band(z, tz + 0.125, tz + 0.15, 0.0006)), front)
        tri = g.math('LESS_THAN', g.math('SUBTRACT', z, tz + 0.129), g.math('SUBTRACT', 0.016, g.math('MULTIPLY', g.math('ABSOLUTE', g.math('SUBTRACT', x, 0.09)), 1.1)))
        base = g.mix(pr, base, g.mix(tri, (0.85, 0.85, 0.82), (0.03, 0.05, 0.14)))
        # 밑단·소맷단 때
        hem = g.math('MAXIMUM', g.n('ShaderNodeMapRange', From_Min=zmin + 0.06, From_Max=zmin, Value=z).outputs[0],
                     g.n('ShaderNodeMapRange', From_Min=wx - 0.09, From_Max=wx - 0.02, Value=ax).outputs[0])
        return g.mix(g.math('MULTIPLY', g.math('MULTIPLY', hem, g.noise(30, 3)), 0.6), base, (0.08, 0.07, 0.06))
    return N.cloth(f"M_{A}_Windbreaker", (0.022, 0.035, 0.08), "nylon", 0.68, wrinkle=1.5, extra=extra)


def collar(arm, body):
    """스탠드 칼라 4cm (앞 열림 양옆까지), 몸 웨이트 복사."""
    zb, zf, c = N.neckline(body, (f"M_{A}_Windbreaker",), f"M_{A}_Skin")
    rows = [
        (lambda f: -0.006, lambda f: 0.004, 1.0),
        (lambda f: 0.02, lambda f: 0.01, 1.0),
        (lambda f: 0.04, lambda f: 0.014, 1.0),
    ]
    bm = N.neck_loft(N.bvh(body), rows, -128, 128, zb, zb - 0.01, c)
    mat = N.cloth(f"M_{A}_Collar", (0.42, 0.055, 0.03), "nylon", 0.68, wrinkle=0.4)
    return [N.shell_obj(A + "_Collar", bm, mat, body, thick=0.004, subd=1)]


plaid = lambda nm: (lambda a, z: N.cloth(f"M_{A}_{nm}", (0.32, 0.29, 0.22), "plaid", 0.85, col2=(0.05, 0.07, 0.15)))

CFG = dict(
    asset=A, glb="npc_man4", height=1.68, prep=prep, glasses=True,
    mats={
        "Shirt": jacket,
        "Details": plaid("Shirt"), "TieTexture": plaid("ShirtFront"),
        "Pants": lambda a, z: N.cloth(f"M_{A}_HikingPants", (0.17, 0.145, 0.1), "twill", 0.8, dust=0.8),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Trekking", (0.09, 0.075, 0.06), 0.75, sole=(0.025, 0.024, 0.024), sole_h=0.03),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.52, 0.33, 0.22)),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.05, 0.048, 0.047), grey=0.9),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=collar,
    watch=dict(style="gold", strap=(0.55, 0.42, 0.2), metal=True),
    notes="60대 남: 남색+빨강 투톤 등산 바람막이(앞 열림, 스탠드 칼라 4cm, 앞 지퍼 테이프, 오른쪽 가슴 사선 지퍼 주머니, 배색 파이핑,"
          " 왼쪽 가슴 가상 패치, 립스톱 결, 어깨 햇빛 바램, 소맷단·밑단 때), 베이지 체크 셔츠, 카키 등산바지, 등산화, 회색 머리·수염, 안경, 금색 시계."
          " 행인/줄 선 손님. 키 1.67m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

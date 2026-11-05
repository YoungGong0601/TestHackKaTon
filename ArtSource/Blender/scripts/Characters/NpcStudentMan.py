"""NpcStudentMan: 대학생 남 (회색 후드티 + 청바지 + 흰 운동화 + 검정 백팩). 원본 npc_man1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import npc_common as N

A = "NpcStudentMan"


def prep(arm, body, s0):
    # 원본은 신발이 Eyes 재질 -> 발 부분만 Shoes 로 분리
    N.set_mat(body, N.faces(body, lambda c, n, m: m == "Eyes" and c.z * s0 < 0.3), bpy.data.materials.new("Shoes"))


def hoodie(a, zr):
    zmin = zr["Shirt"][0]                                  # 후드티 밑단 근처 면 높이 (rest)
    nz = N.bone_head(a, "Neck").z
    wx = N.bone_head(a, "Palm.L").x                        # 손목 (T포즈 팔 = X축)

    def extra(g, base):
        x, y, z = g.xyz()
        ax = g.math('ABSOLUTE', x)
        front = g.math('LESS_THAN', y, -0.03)
        dark = (0.11, 0.11, 0.115)
        # 밑단·소맷단 골지 시보리
        hem = g.math('MULTIPLY', g.band(z, zmin - 0.1, zmin + 0.045, 0.002), g.math('LESS_THAN', ax, wx - 0.3))
        cuff = g.band(ax, wx - 0.07, wx + 0.05, 0.002)
        rib = g.mix(cuff, g.wave(0.0045, 'X', profile='TRI'), g.wave(0.0045, 'Z', profile='TRI'))
        ribm = g.math('MAXIMUM', hem, cuff)
        base = g.mix(g.math('MULTIPLY', ribm, g.math('ADD', 0.25, g.math('MULTIPLY', rib, 0.35))), base, dark)
        # 캥거루 주머니 (사다리꼴, 박음질 선 + 두 겹 원단이라 살짝 어둡게)
        lo, hi = zmin + 0.065, zmin + 0.235
        wid = g.math('SUBTRACT', 0.14, g.math('MULTIPLY', g.math('SUBTRACT', z, lo), 0.35))
        inside = g.math('MULTIPLY', g.math('MULTIPLY', g.band(z, lo, hi, 0.0015), g.math('LESS_THAN', ax, wid)), front)
        edge = g.math('MULTIPLY', g.math('MULTIPLY', g.band(z, lo, hi, 0.0015),
                                         g.band(g.math('SUBTRACT', ax, wid), -0.004, 0.0, 0.001)), front)
        top = g.math('MULTIPLY', g.math('MULTIPLY', g.band(z, hi - 0.004, hi, 0.001), g.math('LESS_THAN', ax, wid)), front)
        base = g.mix(g.math('MULTIPLY', inside, 0.18), base, dark)
        base = g.mix(g.math('MULTIPLY', g.math('MAXIMUM', edge, top), 0.7), base, dark)
        # 후드 끈 2줄 (흰 면끈 + 끝 플라스틱 마개)
        cord = g.math('MULTIPLY', g.math('MULTIPLY', g.band(ax, 0.03, 0.037, 0.0008), g.band(z, nz - 0.2, nz - 0.03, 0.001)), front)
        base = g.mix(cord, base, (0.72, 0.71, 0.68))
        tip = g.math('MULTIPLY', g.math('MULTIPLY', g.band(ax, 0.029, 0.038, 0.0008), g.band(z, nz - 0.215, nz - 0.2, 0.001)), front)
        return g.mix(tip, base, (0.03, 0.03, 0.032))
    return N.cloth(f"M_{A}_Hoodie", (0.19, 0.19, 0.2), "fleece", 0.92, extra=extra)


def hood_and_pack(arm, body):
    """목 뒤에 접혀 내려앉은 후드(두께 감, 앞쪽은 끈 터널 테두리) + 그 위로 지나가는 백팩 끈."""
    zb, zf, c = N.neckline(body, (f"M_{A}_Hoodie",), f"M_{A}_Skin")
    tree = N.bvh(body)
    rows = [  # (목선 기준 높이, 몸에서 띄움, φ배율), f = 1 뒤 / 0 앞
        (lambda f: -0.004, lambda f: 0.004, 1.0),                         # 몸판에 붙는 솔기
        (lambda f: 0.018 + 0.012 * f, lambda f: 0.012 + 0.012 * f, 1.0),  # 목을 감싸며 선 후드 테두리
        (lambda f: -0.02 - 0.03 * f, lambda f: 0.022 + 0.032 * f, 1.0),   # 부푼 바깥
        (lambda f: -0.05 - 0.09 * f, lambda f: 0.016 + 0.036 * f, 1.0),
        (lambda f: -0.06 - 0.12 * f, lambda f: 0.005 + 0.006 * f, 1.0),   # 등에 내려앉은 끝 (뒤 18cm)
    ]
    bm = N.neck_loft(tree, rows, -165, 165, zb, zf, c, n=44)
    tz = N.bone_head(arm, "Torso").z

    def tunnel(g, base):
        # 앞쪽 끝 2cm 끈 터널 박음질 + 안감(어두운 회색)이 보이는 테두리
        x, y, z = g.xyz()
        front = g.math('LESS_THAN', y, c.y - 0.02)
        st = g.math('MULTIPLY', front, g.ramp(g.wave(0.02, 'Z', profile='TRI'), [(0.9, (0,)), (0.96, (1,))]))
        return g.mix(g.math('MULTIPLY', st, 0.4), base, (0.1, 0.1, 0.105))
    hood = N.shell_obj(A + "_Hood", bm, N.cloth(f"M_{A}_Hood", (0.19, 0.19, 0.2), "fleece", 0.92, wrinkle=1.3, extra=tunnel),
                       body, thick=0.008, subd=1)
    return [hood] + N.backpack(arm, body, A, tree=N.bvh_multi([body, hood]))


CFG = dict(
    asset=A, glb="npc_man1", height=1.78, prep=prep,
    mats={
        "Shirt": hoodie,
        "Pants": lambda a, z: N.cloth(f"M_{A}_Jeans", (0.026, 0.045, 0.1), "denim", 0.8, col2=(0.075, 0.115, 0.2), dust=0.5),
        "Shoes": lambda a, z: N.leather(f"M_{A}_Sneakers", (0.72, 0.71, 0.69), 0.5, sole=(0.5, 0.48, 0.44), sole_h=0.026),
        "Skin": lambda a, z: N.skin(f"M_{A}_Skin", (0.6, 0.39, 0.27)),
        "Hair": lambda a, z: N.hair(f"M_{A}_Hair", (0.016, 0.013, 0.011)),
        "Eyes": lambda a, z: N.eyes(f"M_{A}_Eyes"),
    },
    extra=hood_and_pack,
    watch=dict(style="black", strap=(0.02, 0.02, 0.022), size=0.019),
    notes="대학생 남(20대): 회색 후드티(목 뒤에 접혀 내려앉은 후드·캥거루 주머니·후드 끈·골지 시보리)+청바지+흰 운동화,"
          " 차콜 600D 백팩(둥근 윗면, 메인·앞주머니 지퍼, 옆 물병 메시 주머니, 윗 손잡이 고리, 패치, 패드 어깨끈 -> 사다리 버클 -> 웨빙이 겨드랑이 밑으로 가방 아래 모서리까지, 가슴 스트랩),"
          " 검정 손목시계. 줄 맨 앞 '뒤 손님'(yM: '저기요, 빨리 좀 해요.', '비켜보세요, 제가 먼저 할게요.') 추천, 끼어들기 장면은 Tap 클립. 키 1.77m(validate).",
)

if __name__ == "__main__":
    N.run(CFG)

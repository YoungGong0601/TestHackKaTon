# 할아버지 나무 지팡이 (갈고리 손잡이, 고무 발굽, 손목 끈). 원점 = 고무 끝 바닥, 갈고리는 -X 쪽.
import sys, math
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hk, k3d, bpy

k3d.reset()
A = "HomeCane"
d2r = math.radians


def grip(g, base, r, obj):
    # 손잡이 쪽 손때: 어둡고 반들반들
    z = g.sep(obj)[2]
    m = g.math('MULTIPLY', g.ramp(z, 0.8, 0.86), g.ramp(g.noise(30, 4, 0.6, obj), 0.3, 0.7))
    base = g.mix(g.math('MULTIPLY', m, 0.5), base, hk.srgb("#1a0f08"))
    return base, g.lerp(m, r, 0.18)


wood = hk.P("M_tmp_canewood", "#4a2c1a", 0.32, var=0.14, vs=6, rv=0.08, grime=0.5, gd=0.006, gcol="#140a05",
            edge=0.5, ed=0.003, ecol="#8a6040", erough=0.55, bump=0.06, bs=260, dust=0.6, dz=0.12, dcol="#5c5244",
            smudge=0.3, extra=lambda g, b, r, o: grip(g, g.mix(g.math('MULTIPLY', g.ramp(g.wave(260, o, 'X', 7, 3), 0.5, 0.95),
                                                                       0.5), b, hk.srgb("#24140a")), r, o))
rubber = hk.P("M_tmp_canetip", "#161515", 0.85, var=0.06, vs=30, grime=0.6, gd=0.004, dust=0.9, dz=0.025,
              dcol="#6a6258", bump=0.15, bs=400)
brass = hk.P("M_tmp_canering", "#9a8456", 0.3, 1.0, var=0.12, grime=0.7, gd=0.003, gcol="#2e2414", edge=0.6, ed=0.0015,
             ecol="#d8c08a")
cord = hk.P("M_tmp_canecord", "#2a2a30", 0.8, var=0.1, vs=60, bump=0.4, bs=1800, bk='cloth', grime=0.4, gd=0.003)

parts = []
Z1 = 0.835
# 고무 발굽 (아래 주름 링)
parts.append(hk.lathe(A + "_Tip", [(0, 0), (0.012, 0.0008), (0.0135, 0.004), (0.0128, 0.008), (0.0136, 0.012), (0.0128, 0.016),
                                   (0.0132, 0.03), (0.0118, 0.042), (0.0106, 0.043)], 24, rubber))
# 대 (위로 갈수록 살짝 굵게) + 쇠고리
parts.append(hk.cyl(A + "_Shaft", 0.0104, Z1 - 0.04, (0, 0, 0.04), mat=wood, n=20, r2=0.0116, bev=0))
parts.append(hk.cyl(A + "_Ring", 0.0122, 0.01, (0, 0, Z1 - 0.06), mat=brass, n=24, bev=0.0012))
# 갈고리 손잡이 (반원 + 끝 둥글게)
R = 0.045
pts = [(0, 0, Z1 - 0.06)]
for k in range(1, 5):
    pts.append((0, 0, Z1 - 0.06 + 0.06 * k / 4))
for k in range(1, 21):
    a = math.pi * k / 20
    pts.append((-R + R * math.cos(a), 0, Z1 + R * math.sin(a)))
for k in range(1, 4):
    pts.append((-2 * R - 0.001 * k, 0, Z1 - 0.009 * k))
parts.append(hk.tube(A + "_Crook", pts, 0.0119, 14, wood, rfun=lambda t: 1.0 if t < 0.9 else 1.0 - (t - 0.9) * 1.5))
parts.append(hk.lathe(A + "_CrookEnd", [(0.0104, 0), (0.0098, 0.003), (0.006, 0.0062), (0, 0.0072)], 16, wood,
                      loc=(-2 * R - 0.003, 0, Z1 - 0.027), rot=(0, d2r(180), 0)))
# 손목 끈 (갈고리 목에 묶인 고리)
cz = Z1 - 0.045
loop = [(0.011 * math.cos(a), 0.011 * math.sin(a), cz) for a in [k / 10 * 2 * math.pi for k in range(11)]]
parts.append(hk.tube(A + "_CordKnot", loop, 0.0022, 8, cord))
hang = [(0.012, 0, cz), (0.02, -0.004, cz - 0.03), (0.028, -0.006, cz - 0.075), (0.03, -0.004, cz - 0.11), (0.022, 0.0, cz - 0.125),
        (0.014, 0.004, cz - 0.11), (0.013, 0.005, cz - 0.07), (0.012, 0.003, cz - 0.03), (0.011, 0.001, cz)]
parts.append(hk.tube(A + "_Cord", hang, 0.0018, 8, cord))
obj = hk.join(parts, A)
k3d.set_origin(obj, (0, 0, 0))
k3d.bake(obj, 1024, ao_distance=0.015)
hk.socket(A + "_Socket_Grip", (-R, 0, Z1 + R), obj)
hk.socket(A + "_Socket_Tip", (0, 0, 0), obj)
notes = ("할아버지 나무 지팡이 높이 0.89m (갈고리 손잡이, 고무 발굽, 손목 끈). 원점 = 발굽 바닥, 갈고리는 -X 쪽. "
         "프로토타입: 현관 우산꽂이 옆 three(S-.2, A, R+.62) 벽에 기대 rot z -0.075 (HomeEntry_Socket_Cane), "
         "신발 신기 후 숨기고 손에 든다. Socket_Grip = 손잡이 잡는 점, Socket_Tip = 바닥 끝.")
k3d.export(A, hk.CAT, [obj], notes=notes)
k3d.preview(A, [obj])
L_ = [('AREA', (0.6, -0.8, 1.6), 120, (1, 0.95, 0.9), 1.5), ('POINT', (-0.8, -0.5, 0.6), 20, (0.9, 0.95, 1), 0.3)]
hk.shot(hk.PREV + "/HomeCane_full.png", (1.0, -1.7, 0.55), (-0.02, 0, 0.46), lens=40, res=(900, 1200), lights=L_, world=0.4)
hk.shot(hk.PREV + "/HomeCane_grip.png", (0.18, -0.32, 0.95), (-0.04, 0, 0.84), lens=50, lights=L_, world=0.4)

# StreetBollard: 보도 차량진입 억제용 강관 볼라드 (높이 0.85 m, Ø120, 노란 반사띠, 바닥 플랜지 볼트).
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d

k3d.reset()
A = "StreetBollard"

# 몸통: 플랜지 + 관 + 둥근 머리를 회전체 하나로
post_m = S.paint("M_StreetBollard_Paint", (0.040, 0.043, 0.048), 0.48, edge=1.0, edge_col=(0.16, 0.10, 0.06),
                 edge_metal=0.3, rust=0.5, rust_scale=9, rust_z=0.45, scratches=0.8, bottom=0.8, bottom_h=0.22,
                 bump=0.08)
prof = [(0.0, 0.0), (0.098, 0.0), (0.098, 0.010), (0.092, 0.013), (0.068, 0.015), (0.061, 0.03), (0.060, 0.05),
        (0.060, 0.79), (0.0615, 0.795), (0.0625, 0.805), (0.060, 0.822), (0.050, 0.838), (0.034, 0.848),
        (0.016, 0.852), (0.0, 0.853)]
post = S.lathe(A + "_Post", prof, seg=32, mat=post_m)

# 반사띠 (마이크로프리즘 시트 느낌의 범프)
band_m = S.wmat("M_StreetBollard_Band", (0.78, 0.52, 0.02), 0.32, 0.0, var=0.1, grime=0.6, scratches=0.6,
                bump=0.25, bump_scale=900, streaks=0.3)
bands = [S.lathe(A + "_Band%d" % i, [(0.0612, z0), (0.0614, z0 + 0.002), (0.0614, z1 - 0.002), (0.0612, z1)],
                 seg=32, mat=band_m, close=False) for i, (z0, z1) in enumerate(((0.66, 0.745), (0.615, 0.635)))]

# 플랜지 볼트 4개 (육각 머리 + 와셔)
bolt_m = S.galv("M_StreetBollard_Bolt", 0.5, base=(0.35, 0.33, 0.30), rust=0.6, rust_scale=30)
bolts = []
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    x, y = math.cos(a) * 0.078, math.sin(a) * 0.078
    bolts.append(S.cyl(A + "_W%d" % k, 0.013, 0.003, (x, y, 0.010), mat=bolt_m, seg=12, bevel=0.0008))
    bolts.append(S.cyl(A + "_B%d" % k, 0.0095, 0.008, (x, y, 0.013), (0, 0, a), mat=bolt_m, seg=6, bevel=0.001))
    bolts.append(S.cyl(A + "_T%d" % k, 0.005, 0.006, (x, y, 0.021), mat=bolt_m, seg=8, bevel=0.0008))

body = S.join([post] + bands + bolts, A + "_Body")
k3d.origin_bottom(body)
k3d.bake(body, 1024, samples=24)
notes = ("보도 경계석 뒤 0.3~0.5 m 에 1.5 m 간격으로 배치(프로토타입: x 26~39.3, 1.5 m 간격). 원점 = 바닥 중앙. "
         "높이 0.853 m, 몸통 Ø0.12 m, 플랜지 Ø0.196 m. 반사띠 0.66~0.745 m.")
S.finish(A, [body], 0.85, notes, fp=dict(dist=1.6, look_h=0.5))

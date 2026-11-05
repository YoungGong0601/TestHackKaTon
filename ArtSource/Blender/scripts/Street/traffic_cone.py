# StreetTrafficCone: 공사장 라바콘 (높이 0.7 m, 주황 몸통, 흰 반사띠 2줄, 검은 고무 받침 0.38 m).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d

k3d.reset()
A = "StreetTrafficCone"
H, Z0, R0, R1 = 0.70, 0.045, 0.125, 0.030


def rad(z):
    return R0 + (R1 - R0) * (z - Z0) / (H - Z0)


cone_m = S.wmat("M_StreetTrafficCone_Body", (0.82, 0.17, 0.02), 0.42, 0.0, var=0.1, grime=0.8, scratches=0.7,
                streaks=0.5, bottom=0.9, bottom_h=0.2, bump=0.05)
band_m = S.wmat("M_StreetTrafficCone_Band", (0.80, 0.80, 0.77), 0.34, 0.0, var=0.08, grime=0.7, scratches=0.6,
                bump=0.2, bump_scale=900)
base_m = S.rubber("M_StreetTrafficCone_Base")

body = S.lathe(A + "_Cone", [(0.0, Z0), (R0 + 0.02, Z0), (R0, Z0 + 0.02), (R1, H - 0.004), (R1 - 0.004, H),
                             (0.016, H), (0.012, H - 0.03), (0.0, H - 0.03)], seg=32, mat=cone_m)
bands = [S.lathe(A + "_Band%d" % i, [(rad(z0) + 0.0008, z0), (rad(z0) + 0.0018, z0 + 0.002),
                                     (rad(z1) + 0.0018, z1 - 0.002), (rad(z1) + 0.0008, z1)],
                 seg=32, mat=band_m, close=False) for i, (z0, z1) in enumerate(((0.26, 0.38), (0.47, 0.56)))]
base = S.box(A + "_Base", (0.38, 0.38, Z0), (0, 0, Z0 / 2), mat=base_m, bevel=0.012, segs=3)

o = S.join([body, base] + bands, A + "_Body")
k3d.origin_bottom(o)
k3d.bake(o, 512, samples=24)
S.finish(A, [o], 0.70, "원점 = 바닥 중앙. 높이 0.7 m, 받침 0.38 m 사각. 공사 구역 앞에 1 m 안팎 간격으로 배치.",
         fp=dict(dist=1.6, look_h=0.4))

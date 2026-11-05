# StreetSignPole: 교통표지 기둥 (Ø76 아연도금 강관 3.3 m) + 지시표지 "횡단보도"(0.6 m) + 안내판 "시장 입구 →".
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d
from mathutils import Vector

k3d.reset()
A = "StreetSignPole"
H, R = 3.3, 0.038
png, rect = S.atlas("T_StreetSignPole_Faces")
galv = S.galv("M_SSP_Galv", 0.42, rust=0.35, rust_scale=14, rust_z=0.5, bottom=0.9, bottom_h=0.3)
alu = S.wmat("M_SSP_Alu", (0.50, 0.51, 0.52), 0.42, 1.0, var=0.12, grime=0.6, streaks=0.6, scratches=0.6, bump=0.04)
conc = S.concrete("M_SSP_Footing", (0.30, 0.29, 0.27), bottom=0.0)
face = S.decal_mat("M_StreetSignPole_Faces", png, 0.35)

P = []
P.append(S.cyl(A + "_Footing", 0.16, 0.025, (0, 0, -0.01), mat=conc, seg=20, bevel=0.008))
P.append(S.cyl(A + "_Pipe", R, H, (0, 0, 0.0), mat=galv, seg=20, bevel=0.0))
P.append(S.lathe(A + "_Cap", [(0.0, H), (R + 0.004, H), (R + 0.004, H + 0.03), (R * 0.7, H + 0.045), (0.0, H + 0.048)],
                 seg=20, mat=galv))


def sign(name, w, h, zc, key, rounded=0.03):
    """알루미늄 판(테두리 접힘) + 정면 데칼 + 뒷면 보강레일 + U밴드 2개."""
    y0 = -(R + 0.05)
    P.append(S.box(name + "_Plate", (w, 0.006, h), (0, y0, zc), mat=alu, bevel=0.01, segs=3))
    P.append(S.quad(name + "_Face", w - 0.004, h - 0.004, rect[key], face, (0, y0 - 0.0035, zc)))
    for dz in (-h * 0.28, h * 0.28):
        P.append(S.box(name + "_Rail%+.2f" % dz, (w * 0.86, 0.022, 0.03), (0, y0 + 0.014, zc + dz), mat=alu, bevel=0.003))
        P.append(S.box(name + "_Clip%+.2f" % dz, (0.09, 0.03, 0.05), (0, -(R + 0.012), zc + dz), mat=galv, bevel=0.004))
        P.append(S.lathe(name + "_Band%+.2f" % dz, [(R + 0.001, zc + dz - 0.012), (R + 0.006, zc + dz - 0.012),
                                                     (R + 0.006, zc + dz + 0.012), (R + 0.001, zc + dz + 0.012)],
                         seg=20, mat=galv, close=False))
        for s in (-1, 1):
            P.append(S.cyl(name + "_Nut%+.2f%d" % (dz, s), 0.009, 0.012, (s * 0.03, -(R + 0.027), zc + dz),
                           (math.pi / 2, 0, 0), galv, seg=6, bevel=0.001))


sign(A + "_Cross", 0.6, 0.6, 2.95, "crosswalk")
sign(A + "_Market", 0.6, 0.258, 2.42, "market")
# 뒷면 관리 스티커 + 기둥 스티커
P.append(S.quad(A + "_BackSticker", 0.12, 0.072, rect["back"], face, (0.15, -(R + 0.05) + 0.0035, 2.95), (0, 0, math.pi)))
P.append(S.wrap_decal(A + "_PoleSticker", R + 0.002, 1.35, 0.06, -1.2, 1.2, rect["st_loan"], face, 8))

body = S.join(P, A + "_Body")
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, keep=("M_StreetSignPole_Faces",), samples=24)
S.empty(A + "_Socket_Sign", (0, -(R + 0.06), 2.95), parent=body)
notes = ("교통표지 기둥 3.35 m. 원점 = 바닥 중앙(바닥 기초 1 cm 묻힘). 표지 정면 = -Y(Unity +Z). "
         "위: 지시표지 322 횡단보도 0.6x0.6 m(중심 2.95 m), 아래: 안내판 '시장 입구 →' 0.6x0.26 m(중심 2.42 m). "
         "표지 면은 굽지 않는 M_StreetSignPole_Faces(1024 아틀라스). Socket_Sign: 시선 대상.")
S.finish(A, [body], 3.3, notes, fp=dict(dist=2.6, look_h=2.4, az=15))

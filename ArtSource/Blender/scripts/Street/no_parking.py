# StreetNoParking: 동네 골목의 "주차금지" 입간판 — 폐타이어에 시멘트를 채워 세운 강관 + 0.5 m 표지 + 손글씨 코팅지.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d
from mathutils import Vector

k3d.reset()
A = "StreetNoParking"
png, rect = S.atlas("T_StreetNoParking_Face")
tire_m = S.rubber("M_SNP_Tire", (0.018, 0.018, 0.018), grime=0.7, bottom=0.9, bottom_h=0.12, bottom_col=(0.14, 0.12, 0.09),
                  bump=0.25, bump_scale=160)
cem = S.concrete("M_SNP_Cement", (0.30, 0.29, 0.27), grime=0.8, bump=0.6, bump_scale=60, var=0.2)
pipe = S.galv("M_SNP_Pipe", 0.55, base=(0.42, 0.42, 0.41), rust=0.9, rust_scale=8, streaks=0.6)
alu = S.wmat("M_SNP_Alu", (0.48, 0.49, 0.50), 0.45, 1.0, var=0.15, grime=0.6, scratches=0.8, dents=0.3, streaks=0.5)
tie = S.flat("M_SNP_Tie", (0.012, 0.012, 0.012), 0.45)
face = S.decal_mat("M_StreetNoParking_Face", png, 0.45)

P = []
# 타이어 (눕힌 185/65R14, 홈 3줄)
prof = [(0.183, 0.03), (0.19, 0.012), (0.205, 0.002), (0.26, 0.0), (0.288, 0.012), (0.299, 0.035), (0.30, 0.06),
        (0.292, 0.064), (0.292, 0.072), (0.30, 0.076), (0.30, 0.094), (0.292, 0.098), (0.292, 0.106), (0.30, 0.11),
        (0.30, 0.128), (0.292, 0.132), (0.292, 0.14), (0.30, 0.144), (0.299, 0.158), (0.288, 0.18), (0.26, 0.19),
        (0.205, 0.188), (0.19, 0.18), (0.183, 0.165)]
P.append(S.lathe(A + "_Tire", prof + [prof[0]], seg=40, mat=tire_m, close=True, smooth_ang=40))
# 시멘트 (타이어 안을 채움, 가운데가 살짝 낮다)
P.append(S.lathe(A + "_Cement", [(0.0, 0.0), (0.186, 0.0), (0.186, 0.16), (0.12, 0.155), (0.05, 0.15), (0.0, 0.149)],
                 seg=40, mat=cem, smooth_ang=30))
# 강관 + 캡
P.append(S.cyl(A + "_Pipe", 0.0215, 1.5, (0, 0, 0.12), mat=pipe, seg=16, bevel=0.0))
P.append(S.cyl(A + "_PipeCap", 0.024, 0.02, (0, 0, 1.62), mat=pipe, seg=16, bevel=0.004))
# 표지판 0.5 x 0.5 (중심 1.36 m), 접힘 테두리, 뒷면 밴드 2개
y0 = -(0.0215 + 0.012)
P.append(S.box(A + "_Plate", (0.5, 0.004, 0.5), (0, y0, 1.36), mat=alu, bevel=0.006))
P.append(S.quad(A + "_Face", 0.496, 0.496, rect["face"], face, (0, y0 - 0.0025, 1.36)))
for dz in (-0.15, 0.15):
    P.append(S.lathe(A + "_Band%+.2f" % dz, [(0.0225, 1.36 + dz - 0.012), (0.026, 1.36 + dz - 0.012),
                                               (0.026, 1.36 + dz + 0.012), (0.0225, 1.36 + dz + 0.012)], seg=16,
                     mat=pipe, close=False))
    P.append(S.box(A + "_Clip%+.2f" % dz, (0.07, 0.012, 0.024), (0, -0.026, 1.36 + dz), mat=pipe, bevel=0.002))
# 손글씨 코팅지 (케이블타이 2개로 묶음, 살짝 기울어짐)
hz = 0.98
P.append(S.quad(A + "_Note", 0.30, 0.183, rect["hand"], face, (0, -0.024, hz), (math.radians(-6), 0, math.radians(3))))
P.append(S.box(A + "_NoteBack", (0.30, 0.0015, 0.183), (0, -0.0228, hz), (math.radians(-6), 0, math.radians(3)), alu, 0.0))
for dz in (-0.05, 0.05):
    P.append(S.lathe(A + "_Tie%+.2f" % dz, [(0.0218, hz + dz - 0.003), (0.0245, hz + dz - 0.003), (0.0245, hz + dz + 0.003),
                                             (0.0218, hz + dz + 0.003)], seg=16, mat=tie, close=False))
    P.append(S.box(A + "_TieHead%+.2f" % dz, (0.008, 0.01, 0.008), (0.024, 0.0, hz + dz), mat=tie, bevel=0.001))

body = S.join(P, A + "_Body")
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, keep=("M_StreetNoParking_Face",), samples=24)
S.empty(A + "_Socket_Sign", (0, -0.04, 1.36), parent=body)
notes = ("주차금지 입간판 1.64 m. 원점 = 바닥 중앙(타이어 밑면). 표지 정면 = -Y. 타이어 Ø0.6 m 안에 시멘트를 채운 한국 골목식. "
         "표지(0.5x0.5 m) + 손글씨 '차 대지 마세요!!' 코팅지는 M_StreetNoParking_Face(굽지 않음). Socket_Sign: 시선 대상.")
S.finish(A, [body], 1.64, notes, fp=dict(dist=1.8, look_h=1.0, az=25))

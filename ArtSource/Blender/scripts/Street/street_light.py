# StreetLight: 한국 도로 가로등 (지상 7.5 m): 테이퍼 강관 + 곡선 암 + LED 등기구(발광) + 점검구·플랜지·관리번호판.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d
from mathutils import Vector

k3d.reset()
A = "StreetLight"
H = 6.75                        # 강관 수직부 높이
RB, RT = 0.085, 0.056


def pr(z):
    return RB + (RT - RB) * min(z, H) / H


tex_png, rect = S.atlas("T_StreetLight_Decals")
paint = S.paint("M_SL_Paint", (0.20, 0.21, 0.22), 0.45, edge=0.8, edge_col=(0.32, 0.33, 0.33), edge_metal=1.0,
                rust=0.4, rust_scale=9, rust_z=0.7, streaks=0.5, bottom=0.9, bottom_h=0.35, scratches=0.5)
galv = S.galv("M_SL_Galv", 0.5, rust=0.6, rust_scale=25)
head_m = S.paint("M_SL_Head", (0.16, 0.17, 0.18), 0.5, edge=0.5, grime=0.7, streaks=0.4, fade_top=0.0)
lens_m = S.flat("M_StreetLight_LED", (0.9, 0.88, 0.82), 0.2, 0.0, emission=(1.0, 0.9, 0.76), strength=6.0)
decal = S.decal_mat("M_StreetLight_Decals", tex_png, 0.6, alpha_clip=True)

P = []
# 플랜지 + 앵커볼트
P.append(S.box(A + "_Flange", (0.34, 0.34, 0.022), (0, 0, 0.011), mat=paint, bevel=0.006))
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    x, y = math.cos(a) * 0.17, math.sin(a) * 0.17
    x, y = x * 0.83, y * 0.83
    P.append(S.cyl(A + "_Nut%d" % k, 0.017, 0.016, (x, y, 0.022), (0, 0, a), galv, seg=6, bevel=0.0015))
    P.append(S.cyl(A + "_Bolt%d" % k, 0.009, 0.045, (x, y, 0.022), mat=galv, seg=8, bevel=0.001))
# 보강 리브 4장
for k in range(4):
    a = k * math.pi / 2
    P.append(S.box(A + "_Gusset%d" % k, (0.07, 0.008, 0.12), (math.cos(a) * (RB + 0.035), math.sin(a) * (RB + 0.035), 0.08),
                   (0, 0, a), paint, 0.002))
# 강관 (테이퍼) + 꼭대기 캡
prof = [(0.0, 0.02), (RB, 0.02)] + [(pr(z), z) for z in (0.06, 0.5, 1.2, 2.5, 4.0, 5.5, H)] + [(RT + 0.006, H), (RT + 0.006, H + 0.05), (RT * 0.6, H + 0.09), (0.0, H + 0.1)]
P.append(S.lathe(A + "_Shaft", prof, seg=28, mat=paint, smooth_ang=60))
# 점검구 (문 + 나사 2개) 0.55~0.95 m, 정면
dz = 0.75
P.append(S.wrap_decal(A + "_DoorSkin", pr(dz) + 0.0015, 0.55, 0.40, -0.55, 0.55, (0, 0, 0.001, 0.001), paint, 8))
P[-1].data.materials.clear()
P[-1].data.materials.append(paint)
for zz in (0.6, 0.9):
    P.append(S.cyl(A + "_DoorScrew%.1f" % zz, 0.009, 0.006, (0, -(pr(zz) + 0.004), zz), (math.pi / 2, 0, 0), galv, seg=10,
                   bevel=0.001))
# 곡선 암 (정면 -Y 로 1.6 m)
arm = [Vector((0, 0, H - 0.25))]
for k in range(1, 13):
    t = k / 12
    a = t * math.pi / 2 * 0.85
    arm.append(Vector((0, -math.sin(a) * 0.75 - max(0, t - 0.7) * 2.4, H - 0.25 + (1 - math.cos(a)) * 0.0 + math.sin(a) * 0.55 + t * 0.05)))
arm.append(arm[-1] + Vector((0, -0.18, 0.02)))
P.append(S.tube(A + "_Arm", arm, 0.038, 12, paint))
P.append(S.cyl(A + "_ArmCollar", 0.05, 0.12, (0, 0, H - 0.31), mat=paint, seg=20, bevel=0.004))
# 등기구 (끝을 살짝 들어 올림)
tip = arm[-1]
hc = tip + Vector((0, -0.32, -0.01))
tilt = (0, 0, 0)
P.append(S.box(A + "_HeadBody", (0.30, 0.70, 0.085), hc, tilt, head_m, bevel=0.025, segs=3))
P.append(S.box(A + "_HeadTop", (0.26, 0.60, 0.035), hc + Vector((0, 0.02, 0.055)), tilt, head_m, bevel=0.012, segs=2))
for k in range(9):
    x = -0.11 + k * 0.0275
    P.append(S.box(A + "_Fin%d" % k, (0.006, 0.5, 0.03), hc + Vector((x, 0.04, 0.085)), tilt, head_m, bevel=0.002))
P.append(S.cyl(A + "_Sleeve", 0.048, 0.16, tip + Vector((0, 0.08, 0)), (math.pi / 2, 0, 0), head_m, seg=16, bevel=0.005))
for s in (-1, 1):
    P.append(S.cyl(A + "_SleeveBolt%d" % s, 0.008, 0.012, tip + Vector((s * 0.048, 0.0, 0)), (0, s * math.pi / 2, 0),
                   galv, seg=6, bevel=0.001))
# LED 렌즈 (아래면, 굽지 않는 발광 머티리얼)
lens = S.box(A + "_Lens", (0.22, 0.48, 0.01), hc + Vector((0, -0.04, -0.046)), tilt, lens_m, bevel=0.003)
P.append(lens)
P.append(S.box(A + "_LensFrame", (0.25, 0.51, 0.008), hc + Vector((0, -0.04, -0.041)), tilt, head_m, bevel=0.002))

# 데칼: 관리번호판, 스티커, 찢긴 자국
def W(key, z0, h, a0, a1, off=0.004):
    P.append(S.wrap_decal(A + "_D_" + key, pr(z0 + h / 2) + off, z0, h, a0, a1, rect[key], decal, 8))

W("plate", 2.35, 0.26, -1.0, 1.0)
W("st_loan", 1.45, 0.09, 0.6, 2.4)
W("st_key", 1.22, 0.08, -2.2, -0.9)
W("st_piano", 1.62, 0.08, -0.6, 0.9, 0.0045)
W("residue", 1.3, 0.14, 1.2, 2.5, 0.0035)

body = S.join(P, A + "_Body")
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, keep=("M_StreetLight_LED", "M_StreetLight_Decals"), samples=24)
lamp = S.empty(A + "_Socket_Lamp", hc + Vector((0, -0.04, -0.06)), (0, 0, 0), parent=body)
S.empty(A + "_Socket_Plate", (0, -(pr(2.5) + 0.01), 2.48), parent=body)
notes = ("높이 7.5 m 가로등. 원점 = 바닥 중앙. 암과 등기구는 정면(-Y, Unity +Z) 쪽으로 1.6 m 뻗는다 = 도로 쪽으로 돌려 배치. "
         "M_StreetLight_LED = 발광 렌즈(Emission 6, 4000K) — 밤/낮 전환 시 emission 만 조절. "
         "Socket_Lamp: 렌즈 중심(아래를 향함, Spot/Point Light 부착). Socket_Plate: 관리번호판(2.48 m).")
S.finish(A, [body], 7.5, notes, fp=dict(dist=3.5, look_h=3.2, az=-25))

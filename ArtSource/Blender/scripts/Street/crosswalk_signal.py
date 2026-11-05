# StreetCrosswalkSignal: 보행 신호등 (빨강 서있는 사람 / 초록 걷는 사람 / 잔여시간 표시기) + 음향신호기 버튼함.
import sys, os, math, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "StreetCrosswalkSignal"
H = 3.4
RB, RT = 0.057, 0.05
S.ensure_tex()
T = S.TEX


def pr(z):
    return RB + (RT - RB) * min(z, H) / H


box_png, rect = S.atlas("T_StreetCrosswalkSignal_Box")
pole_m = S.paint("M_SCS_Pole", (0.30, 0.31, 0.31), 0.45, edge=0.7, edge_col=(0.45, 0.46, 0.46), edge_metal=1.0,
                 rust=0.35, rust_scale=10, rust_z=0.6, streaks=0.5, bottom=0.9, bottom_h=0.3, scratches=0.4)
galv = S.galv("M_SCS_Galv", 0.5, rust=0.5, rust_scale=25)
house_m = S.paint("M_SCS_Housing", (0.018, 0.019, 0.02), 0.45, edge=0.4, edge_col=(0.25, 0.25, 0.25), edge_metal=0.6,
                  grime=0.7, streaks=0.6, streak_col=(0.2, 0.19, 0.17), scratches=0.15, bump=0.0)
yel_m = S.wmat("M_SCS_Yellow", (0.72, 0.46, 0.015), 0.45, 0.0, var=0.12, grime=0.8, streaks=0.6, scratches=0.3, bump=0.0,
               bottom=0.0, edge=0.5, edge_col=(0.45, 0.42, 0.35), edge_metal=0.0)
btn_m = S.wmat("M_SCS_Button", (0.55, 0.56, 0.57), 0.25, 1.0, var=0.08, grime=0.8, scratches=1.0, bump=0.02)
decal = S.decal_mat("M_StreetCrosswalkSignal_Box", box_png, 0.5)
dyn = {k: S.decal_mat("M_Dyn_StreetCrosswalkSignal_" + k, os.path.join(T, f"T_StreetCrosswalkSignal_{f}.png"), 0.25,
                      emission=e)
       for k, f, e in (("Red", "RedOn", 3.0), ("Green", "GreenOff", 3.0), ("Count", "CountOff", 3.0))}

P = []
# 기초판 + 너트, 강관, 캡
P.append(S.box(A + "_Base", (0.26, 0.26, 0.02), (0, 0, 0.01), mat=pole_m, bevel=0.005))
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    x, y = math.cos(a) * 0.1, math.sin(a) * 0.1
    P.append(S.cyl(A + "_Nut%d" % k, 0.014, 0.014, (x, y, 0.02), (0, 0, a), galv, seg=6, bevel=0.0012))
    P.append(S.cyl(A + "_Bolt%d" % k, 0.008, 0.035, (x, y, 0.02), mat=galv, seg=8))
prof = [(0.0, 0.02), (RB, 0.02)] + [(pr(z), z) for z in (0.05, 0.6, 1.5, 2.4, H)] + [(RT + 0.005, H), (RT + 0.005, H + 0.04), (0.02, H + 0.07), (0.0, H + 0.075)]
P.append(S.lathe(A + "_Pole", prof, seg=24, mat=pole_m, smooth_ang=60))

# 신호등 몸체 (정면 -Y), 밴드 브래킷 2개
hz = 2.95                 # 몸체 중심 높이
hy = -(pr(hz) + 0.05 + 0.11)
for zz in (hz - 0.25, hz + 0.25):
    P.append(S.lathe(A + "_Band%.2f" % zz, [(pr(zz) + 0.001, zz - 0.03), (pr(zz) + 0.009, zz - 0.03), (pr(zz) + 0.009, zz + 0.03),
                                            (pr(zz) + 0.001, zz + 0.03)], seg=24, mat=galv, close=False))
    P.append(S.box(A + "_Bracket%.2f" % zz, (0.06, 0.08, 0.05), (0, -(pr(zz) + 0.04), zz), mat=galv, bevel=0.004))
P.append(S.box(A + "_Housing", (0.38, 0.22, 0.80), (0, hy, hz), mat=house_m, bevel=0.012, segs=3))
P.append(S.box(A + "_Back", (0.30, 0.03, 0.60), (0, hy + 0.12, hz), mat=house_m, bevel=0.006))
lamps = {"Red": hz + 0.19, "Green": hz - 0.19}
fy = hy - 0.11
for k, z in lamps.items():
    # 테두리 링 + 차양(반원통)
    P.append(S.lathe(A + "_Bezel" + k, [(0.150, 0.0), (0.168, 0.0), (0.168, 0.012), (0.150, 0.016)], seg=32,
                     loc=(0, fy, z), rot=(math.pi / 2, 0, 0), mat=house_m, close=False))
    bm = bmesh.new()
    ring = []
    for i in range(17):
        a = math.pi * i / 16
        ring.append((math.cos(a) * 0.172, math.sin(a) * 0.172))
    vs0 = [bm.verts.new((x, fy - 0.004, z + y)) for x, y in ring]
    vs1 = [bm.verts.new((x * 1.04, fy - 0.20, z + y * 1.04 + 0.01)) for x, y in ring]
    for i in range(16):
        bm.faces.new((vs0[i], vs0[i + 1], vs1[i + 1], vs1[i]))
    vis = S.from_bm(A + "_Visor" + k, bm, house_m)
    sol = vis.modifiers.new("Sol", 'SOLIDIFY')
    sol.thickness, sol.offset = 0.004, 0
    S.mods(vis, 0, sharp=50)
    P.append(vis)

# 잔여시간 표시기 (오른쪽, 초록 램프 옆)
cx, cz = 0.36, lamps["Green"]
P.append(S.box(A + "_CountBox", (0.26, 0.14, 0.38), (cx, hy + 0.02, cz), mat=house_m, bevel=0.01))
P.append(S.box(A + "_CountArm", (0.14, 0.05, 0.05), (cx - 0.19, hy + 0.05, cz + 0.12), mat=galv, bevel=0.004))
P.append(S.box(A + "_CountHood", (0.27, 0.10, 0.012), (cx, hy - 0.08, cz + 0.2), (math.radians(-12), 0, 0), house_m, 0.003))

# 음향신호기 버튼함 (뒤 +Y = 보도·대기 쪽, 1.1~1.37 m): 헤드는 건너편을 보고, 버튼은 기다리는 사람을 본다
bz, bw, bh, bd = 1.24, 0.165, 0.27, 0.075
by = pr(bz) + 0.012 + bd / 2
P.append(S.box(A + "_BtnBox", (bw, bd, bh), (0, by, bz), mat=yel_m, bevel=0.008))
P.append(S.box(A + "_BtnBoxBack", (0.06, 0.03, 0.2), (0, pr(bz) + 0.008, bz), mat=galv, bevel=0.003))
for zz in (bz - 0.11, bz + 0.11):
    P.append(S.lathe(A + "_BtnBand%.2f" % zz, [(pr(zz) + 0.001, zz - 0.012), (pr(zz) + 0.007, zz - 0.012),
                                               (pr(zz) + 0.007, zz + 0.012), (pr(zz) + 0.001, zz + 0.012)], seg=24,
                     mat=galv, close=False))
face_y = by + bd / 2 + 0.0015
P.append(S.quad(A + "_BtnFace", bw - 0.012, bh - 0.012, rect["face"], decal, (0, face_y, bz), (0, 0, math.pi)))
btn_z = bz + (bh - 0.012) / 2 - (270 / 520) * (bh - 0.012)
P.append(S.lathe(A + "_BtnRim", [(0.026, 0.0), (0.036, 0.0), (0.036, 0.006), (0.028, 0.008)], seg=24,
                 loc=(0, face_y, btn_z), rot=(-math.pi / 2, 0, 0), mat=house_m, close=False))
# 관리번호 스티커
P.append(S.wrap_decal(A + "_Plate", pr(2.1) + 0.003, 2.02, 0.1, -0.9, 0.9, rect["plate"], decal, 8))

# 동적 면: 램프 2개 + 숫자판 (정면 -Y, U 오른쪽 V 위)
dyn_objs = [S.quad(A + "_LampRed", 0.30, 0.30, (0, 0, 1, 1), dyn["Red"], (0, fy - 0.006, lamps["Red"])),
            S.quad(A + "_LampGreen", 0.30, 0.30, (0, 0, 1, 1), dyn["Green"], (0, fy - 0.006, lamps["Green"])),
            S.quad(A + "_Count", 0.21, 0.28, (0, 0, 1, 1), dyn["Count"], (cx, hy - 0.051, cz))]

body = S.join(P, A + "_Body")
k3d.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, keep=("M_StreetCrosswalkSignal_Box",), samples=24)
for o in dyn_objs:
    S.mods(o, 0, wn=False, sharp=0)
    S.parent(o, body)
# 버튼 = 눌리는 부품 (원점 = 버튼 뿌리 중심, 로컬 -Y 로 4 mm 눌림)
btn = S.cyl(A + "_Button", 0.025, 0.014, (0, 0, 0), (-math.pi / 2, 0, 0), btn_m, seg=24, bevel=0.003)
btn.location = (0, face_y + 0.001, btn_z)
k3d.bake(btn, 256, samples=16)
S.parent(btn, body)
S.empty(A + "_Socket_Button", (0, face_y + 0.02, btn_z), parent=body)
S.empty(A + "_Socket_Speaker", (0, face_y + 0.01, bz - 0.09), parent=body)
S.empty(A + "_Socket_Head", (0, fy - 0.05, hz), parent=body)
# 꺼짐/켜짐 텍스처를 같은 폴더에 둔다 (게임에서 교체)
tdir = os.path.join(k3d.ART, "Textures", A)
os.makedirs(tdir, exist_ok=True)
for f in ("RedOn", "RedOff", "GreenOn", "GreenOff", "Count", "CountOff"):
    shutil.copyfile(os.path.join(T, f"T_StreetCrosswalkSignal_{f}.png"), os.path.join(tdir, f"T_StreetCrosswalkSignal_{f}.png"))
notes = ("보행 신호등 기둥 3.4 m. 원점 = 바닥 중앙. 신호등 헤드 정면 = -Y(Unity +Z): 차도·건너편을 향하게 놓는다. "
         "음향신호기 버튼함은 반대쪽 +Y(Unity -Z) 면 1.1~1.37 m 에 있어, 보도에서 기다리는 사람(StreetSidewalkRamp_Socket_Wait 쪽)이 본다. "
         "동적 면(M_Dyn, UV 0-1, U 오른쪽 V 위, 512px): StreetCrosswalkSignal_LampRed 0.30x0.30 m(z 3.14), "
         "StreetCrosswalkSignal_LampGreen 0.30x0.30 m(z 2.76), StreetCrosswalkSignal_Count 0.21x0.28 m(384x512, 잔여시간 숫자). "
         "기본값: 빨강 켜짐, 초록·숫자 꺼짐. 교체용 텍스처: Textures/StreetCrosswalkSignal/T_StreetCrosswalkSignal_"
         "RedOn/RedOff/GreenOn/GreenOff/Count(15)/CountOff. Emission 3. "
         "StreetCrosswalkSignal_Button = 눌리는 버튼(+Y 면, 원점 = 버튼 뿌리 중심, 누르면 로컬 -Y 로 4 mm 이동). "
         "Socket_Button(누름 위치), Socket_Speaker(음향 '삑' 소리, crosswalk_beep), Socket_Head(시선 대상).")
S.finish(A, [body], 3.4, notes, fp=dict(dist=2.2, look_h=1.6, az=20), lens=35,
         extra=[dict(dist=1.6, look_h=1.2, az=200, lens=35)])   # 보도(+Y) 쪽에서 본 버튼함

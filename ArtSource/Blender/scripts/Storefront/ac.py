# 에어컨 실외기 StorefrontAC: 벽걸이 앵글 거치대 + 실외기 + 테이프 감은 배관·배수 호스·벽 슬리브.
# 원점 = 거치대 바닥, X 가운데, Y=0 이 벽면(뒤). 정면 = -Y. 팬은 자식 StorefrontAC_Fan (원점 = 팬 축).
import sys, math
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sf
from sf import k3d, box2, box, cyl, quad
import bpy

A = "StorefrontAC"
sf.textures("ac")
k3d.reset()

# 실외기 몸체 치수 (실물 800×290×600)
BW, BD, BH = 0.80, 0.29, 0.60
YF, YB = -0.36, -0.07              # 앞면 / 뒷면 y
ZB = 0.365                         # 몸체 바닥 z (거치대 위)
ZT = ZB + BH
FX, FZ, FR = -0.09, ZB + BH / 2, 0.215   # 팬 중심·반지름

ivory = sf.pbr("SAC_Paint", (0.70, 0.68, 0.60), rough=0.55, var=0.1, fade=0.35, grime=0.7, grime_dist=0.05,
               grime_col=(0.07, 0.05, 0.03), edge=0.55, edge_col=(0.22, 0.1, 0.04), bottom=0.8, bottom_h=ZB + 0.18, scratch=0.3, bump=0.2)
inner = sf.pbr("SAC_Inner", (0.02, 0.02, 0.022), rough=0.7, var=0.1, grime=0.0, bump=0.1)
fanm = sf.pbr("SAC_Fan", (0.05, 0.05, 0.055), rough=0.55, var=0.12, grime=0.5, grime_dist=0.03, grime_col=(0.1, 0.08, 0.06), edge=0.3, edge_col=(0.2, 0.18, 0.15))
grille_m = sf.pbr("SAC_Grille", (0.03, 0.03, 0.03), rough=0.5, var=0.1, grime=0.4, edge=0.4, edge_col=(0.25, 0.2, 0.15), bottom=0.5, bottom_h=ZB + 0.15)
fins = sf.pbr("SAC_Fins", (0.35, 0.36, 0.36), rough=0.45, metal=0.8, var=0.15, grime=0.8, grime_dist=0.02, bottom=0.7, bottom_h=ZB + 0.2)
galv = sf.pbr("SAC_Galv", (0.33, 0.34, 0.33), rough=0.5, metal=0.8, var=0.25, var_scale=12, grime=0.8, grime_dist=0.03,
              grime_col=(0.12, 0.05, 0.02), edge=0.8, edge_col=(0.25, 0.1, 0.03), bottom=0.6, bottom_h=0.15, scratch=0.3)
tape = sf.pbr("SAC_Tape", (0.62, 0.6, 0.55), rough=0.6, var=0.2, var_scale=20, fade=0.4, grime=0.6, grime_dist=0.03, bump=0.5, bump_scale=60)
hose = sf.pbr("SAC_Hose", (0.16, 0.16, 0.15), rough=0.7, var=0.15, grime=0.5, bump=0.4)
brass = sf.pbr("SAC_Brass", (0.5, 0.33, 0.12), rough=0.35, metal=1.0, var=0.15, grime=0.8, grime_dist=0.01)
labels = sf.pbr("SAC_Labels", (1, 1, 1), rough=0.5, var=0.06, grime=0.2, image=sf.tex(A, "Labels"), bump=0.05)
putty = sf.pbr("SAC_Putty", (0.5, 0.48, 0.42), rough=0.85, var=0.2, var_scale=30, grime=0.4, bump=0.8, bump_scale=40)
bolt = sf.pbr("SAC_Bolt", (0.4, 0.4, 0.4), rough=0.4, metal=1.0, var=0.2, grime=0.9, grime_dist=0.01, grime_col=(0.15, 0.06, 0.02))

P = []
# ---- 몸체 (앞판에 팬 구멍: Boolean, 구멍 벽은 안쪽 검정)
body = box2((-BW / 2, YF, ZB), (BW / 2, YB, ZT), ivory, 0.0, 1)
cut = cyl(A + "_Cut", FR + 0.012, 0.16, (FX, YF, FZ), inner, rot=(math.pi / 2, 0, 0), n=36, bev=0)
cut.modifiers.clear()
bo = body.modifiers.new("Hole", 'BOOLEAN')
bo.object, bo.solver, bo.material_mode = cut, 'EXACT', 'TRANSFER'
body.modifiers.move(len(body.modifiers) - 1, 0)
k3d.apply_all(body)
bpy.data.objects.remove(cut)
bev = body.modifiers.new("Bevel", 'BEVEL')
bev.width, bev.segments, bev.limit_method, bev.angle_limit = 0.006, 3, 'ANGLE', math.radians(40)
body.modifiers.new("WN", 'WEIGHTED_NORMAL').keep_sharp = True
P.append(body)
P.append(cyl(A + "_Back", FR + 0.02, 0.004, (FX, YF + 0.075, FZ), inner, rot=(math.pi / 2, 0, 0), n=32, bev=0))
# 앞판 패널 이음선·오른쪽 서비스 패널
P.append(box2((0.215, YF - 0.0015, ZB + 0.02), (0.218, YF + 0.001, ZT - 0.02), inner, 0.0005, 1))
for z in (ZB + 0.05, ZT - 0.05):
    for x in (-0.37, 0.37, 0.235):
        P.append(cyl(A + "_Screw", 0.0045, 0.003, (x, YF - 0.001, z), bolt, rot=(math.pi / 2, 0, 0), n=12, bev=0.0008, seg=1))
# 오른쪽 아래 흡기 루버 (가는 홈)
for i in range(7):
    z = ZB + 0.06 + i * 0.022
    P.append(box2((0.25, YF - 0.0012, z), (0.37, YF + 0.002, z + 0.008), inner, 0.0008, 1))
# 위판 살짝 돌출 + 왼쪽·뒤 열교환기 핀
P.append(box2((-BW / 2 - 0.006, YF - 0.006, ZT - 0.012), (BW / 2 + 0.006, YB + 0.006, ZT + 0.004), ivory, 0.004, 2))
P.append(box2((-BW / 2 - 0.004, YF + 0.03, ZB + 0.03), (-BW / 2 + 0.002, YB - 0.02, ZT - 0.03), fins, 0.001, 1))
for i in range(9):  # 핀 보호 철망 (세로 살)
    y = YF + 0.04 + i * 0.022
    P.append(box2((-BW / 2 - 0.009, y, ZB + 0.03), (-BW / 2 - 0.005, y + 0.003, ZT - 0.03), grille_m, 0.0008, 1))
# ---- 팬 보호 그릴 (동심원 + 살). 벽 5~11m 높이 소품이라 철사 단면은 4각 (소품 예산 8k)
for i, r in enumerate((0.05, 0.085, 0.12, 0.155, 0.19, 0.222)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.0028, major_segments=32 if r > 0.1 else 20, minor_segments=4,
                                     location=(FX, YF - 0.012, FZ), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object
    t.name = A + "_Ring"
    t.data.materials.append(grille_m)
    sf.finish(t, 0, wn=False)
    P.append(t)
for i in range(8):
    a = i * math.pi / 4
    L = FR + 0.012
    P.append(sf.box(A + "_Spoke", (L, 0.006, 0.006), (FX + math.cos(a) * L / 2, YF - 0.012, FZ + math.sin(a) * L / 2), grille_m, 0.001, 1, rot=(0, -a, 0)))
P.append(cyl(A + "_GrilleHub", 0.035, 0.01, (FX, YF - 0.012, FZ), grille_m, rot=(math.pi / 2, 0, 0), n=16, bev=0.002))
# ---- 라벨 (브랜드 앞판, 정격 명판 오른쪽 옆, 경고 앞 위)
P.append(quad(A + "_Brand", 0.13, 0.065, (0.305, YF - 0.0008, ZB + 0.28), labels, uv=(0.5, 0.0, 1.0, 0.5)))
P.append(quad(A + "_Warn", 0.10, 0.05, (0.305, YF - 0.0008, ZT - 0.07), labels, uv=(0.5, 0.5, 1.0, 1.0)))
P.append(quad(A + "_Plate", 0.11, 0.11, (BW / 2 + 0.0008, -0.30, ZB + 0.40), labels, face="+X", uv=(0.0, 0.0, 0.5, 1.0)))
# ---- 다리 (U 채널) + 고무 패드
for x in (-0.28, 0.28):
    P.append(box2((x - 0.03, YF + 0.01, ZB - 0.035), (x + 0.03, YB - 0.01, ZB), ivory, 0.003, 2))
    P.append(box2((x - 0.028, YF + 0.03, ZB - 0.045), (x + 0.028, YF + 0.09, ZB - 0.035), hose, 0.002, 1))
    P.append(box2((x - 0.028, YB - 0.09, ZB - 0.045), (x + 0.028, YB - 0.03, ZB - 0.035), hose, 0.002, 1))
# ---- 서비스 밸브 커버(오른쪽 옆) + 황동 플레어 너트
P.append(box2((BW / 2, -0.22, ZB + 0.05), (BW / 2 + 0.03, -0.10, ZB + 0.22), ivory, 0.006, 3))
for z, r in ((ZB + 0.09, 0.012), (ZB + 0.16, 0.015)):
    P.append(cyl(A + "_Nut", r, 0.025, (BW / 2 + 0.042, -0.16, z), brass, rot=(0, math.pi / 2, 0), n=6, bev=0.0015, seg=1))
# ---- 앵글 거치대 (ㄱ자 앵글 40×40×4, 아연도금 + 녹)
ZA = ZB - 0.045      # 받침 앵글 윗면
for x in (-0.28, 0.28):
    # 벽 세로 앵글
    P.append(box2((x - 0.02, -0.004, 0.0), (x + 0.02, 0.0, ZA), galv, 0.0015, 1))
    P.append(box2((x - 0.02, -0.04, 0.0), (x - 0.016, 0.0, ZA), galv, 0.0015, 1))
    # 받침 가로 앵글
    P.append(box2((x - 0.02, -0.43, ZA - 0.004), (x + 0.02, 0.0, ZA), galv, 0.0015, 1))
    P.append(box2((x - 0.02, -0.43, ZA - 0.04), (x - 0.016, 0.0, ZA), galv, 0.0015, 1))
    # 사선 보강
    L = math.hypot(0.33, ZA - 0.05)
    P.append(sf.box(A + "_Brace", (0.04, L, 0.004), (x, -0.165, (ZA + 0.05) / 2), galv, 0.0015, 1,
                    rot=(-math.atan2(ZA - 0.05, 0.33), 0, 0)))
    # 앵커 볼트·와셔
    for z in (0.06, ZA - 0.07):
        P.append(cyl(A + "_Washer", 0.012, 0.003, (x, -0.0055, z), bolt, rot=(math.pi / 2, 0, 0), n=12, bev=0.0006, seg=1))
        P.append(cyl(A + "_Nut", 0.0085, 0.007, (x, -0.011, z), bolt, rot=(math.pi / 2, 0, 0), n=6, bev=0.001, seg=1))
    # 실외기 고정 볼트
    for y in (YF + 0.06, YB - 0.06):
        P.append(cyl(A + "_Nut", 0.007, 0.008, (x, y, ZB + 0.004), bolt, n=6, bev=0.001, seg=1))
P.append(box2((-0.30, -0.42, ZA - 0.004), (0.30, -0.38, ZA), galv, 0.0015, 1))   # 앞 연결 앵글
# ---- 배관 묶음 (보온재+테이프) → 벽 슬리브, 배수 호스, 전원선
route = [(BW / 2 + 0.05, -0.16, ZB + 0.125), (BW / 2 + 0.11, -0.16, ZB + 0.125), (BW / 2 + 0.11, -0.16, ZT + 0.12),
         (BW / 2 + 0.11, 0.03, ZT + 0.12)]
P.append(sf.pipe(A + "_Bundle", route, 0.03, tape, n=12, bend=0.08))
P.append(sf.pipe(A + "_Cable", [(BW / 2 + 0.03, -0.12, ZB + 0.21), (BW / 2 + 0.075, -0.12, ZB + 0.21), (BW / 2 + 0.075, -0.13, ZT + 0.08),
                                (BW / 2 + 0.075, 0.03, ZT + 0.12)], 0.006, hose, n=8, bend=0.05))
P.append(sf.pipe(A + "_Drain", [(0.2, -0.2, ZB - 0.01), (0.2, -0.2, ZB - 0.06), (0.26, -0.06, ZB - 0.2), (0.26, -0.03, 0.02)],
                 0.009, hose, n=8, bend=0.08))
P.append(cyl(A + "_Sleeve", 0.05, 0.03, (BW / 2 + 0.11, -0.012, ZT + 0.12), putty, rot=(math.pi / 2, 0, 0), n=16, bev=0.006, seg=2))
P.append(sf.sphere(A + "_Putty", 0.055, (BW / 2 + 0.11, -0.004, ZT + 0.12), putty, n=12, scale=(1.0, 0.25, 0.9)))

body = sf.join(P, A + "_Body")
k3d.bake(body, 1024, ao_distance=0.06, samples=32)

# ---- 팬 (자식, 원점 = 축). 3날
F = [cyl(A + "_FanHub", 0.045, 0.05, (FX, YF + 0.045, FZ), fanm, rot=(math.pi / 2, 0, 0), n=20, bev=0.006, seg=2)]
blade = [(0.03, -0.035), (0.10, -0.06), (0.17, -0.055), (0.205, -0.02), (0.20, 0.035), (0.15, 0.06), (0.08, 0.05), (0.03, 0.03)]
for i in range(3):
    b = sf.poly_extrude(A + "_Blade", blade, 0.004, fanm)
    k3d.select([b])
    b.rotation_euler = (0, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    b.rotation_euler = (0.45, 0, 0)          # 날개 비틀림(피치)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    b.location = (FX, YF + 0.04, FZ)
    b.rotation_euler = (0, -i * 2 * math.pi / 3, 0)
    sf.finish(b, 0.0015, 1)
    F.append(b)
fan = sf.join(F, A + "_Fan")
k3d.set_origin(fan, (FX, YF + 0.045, FZ))
k3d.bake(fan, 512, ao_distance=0.03, samples=32)
sf.parent(fan, body)

notes = {
    "pivot": "원점 = 앵글 거치대 바닥, X 가운데, Y=0 이 벽면(뒤). 벽에 붙일 때 원점을 벽면에 두면 된다. 높이 약 1.0m(실외기 0.6m + 거치대).",
    "place": "배치는 StorefrontFacade_Socket_AC_1..3 이 기준이다 (소켓 위치·회전 그대로 붙이면 원점이 벽면에 맞는다).",
    "fan": "StorefrontAC_Fan: 원점 = 팬 축. 축은 앞뒤(Blender Y, Unity Z) 방향, 그 축으로 돌리면 된다.",
}
k3d.export(A, "Storefront", [body], notes=notes)
k3d.preview(A, [body])

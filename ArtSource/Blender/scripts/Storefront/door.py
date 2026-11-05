# 유리문 StoreGlassDoor: 알루미늄 프레임 강화유리 여닫이문 (거리 쪽으로 당겨 여는 문), 맞경첩 3개.
# 원점 = 힌지 축(경첩 너클 중심) 바닥 (거리에서 볼 때 왼쪽), 문짝은 +X 로 0.93m, 정면(거리) = -Y.
# 제작은 '문틀 면 x=0, 문 두께 중심 y=0' 좌표로 하고, 마지막에 축이 원점에 오도록 통째로 옮긴다.
import sys, math
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sf
from sf import k3d, box2, cyl, quad
import bpy

A = "StoreGlassDoor"
sf.textures("door")
k3d.reset()

W0, W1 = 0.003, 0.927          # 문짝 x 범위 (힌지 축 x=0)
Z0, Z1 = 0.012, 2.28           # 바닥 틈 12mm
T = 0.025                      # 문 두께 50mm 의 절반
SH, SL = 0.07, 0.11            # 힌지 쪽 / 손잡이 쪽 세로틀 폭
RT, RB = 0.10, 0.18            # 위 / 아래 가로틀 높이
gx0, gx1, gz0, gz1 = W0 + SH, W1 - SL, Z0 + RB, Z1 - RT   # 유리 개구
HX = W1 - SL / 2               # 손잡이 축 x
HZ = 1.10                      # 손잡이 중심 높이
AX, AY = sf.DOOR_AX, sf.DOOR_AY  # 힌지 축 (제작 좌표)

# ---- 머티리얼 (굽기용)
alu_v = sf.pbr("SGD_AluV", (0.045, 0.047, 0.05), rough=0.4, metal=1.0, var=0.06, streak='Z', grime=0.55, grime_dist=0.03,
               edge=0.7, edge_col=(0.32, 0.33, 0.34), bottom=0.7, bottom_h=0.4, scratch=0.6, smudge=0.12)
alu_h = sf.pbr("SGD_AluH", (0.045, 0.047, 0.05), rough=0.4, metal=1.0, var=0.06, streak='X', grime=0.55, grime_dist=0.03,
               edge=0.7, edge_col=(0.32, 0.33, 0.34), bottom=0.8, bottom_h=0.4, scratch=0.6, smudge=0.12)
bead = sf.pbr("SGD_Bead", (0.04, 0.042, 0.045), rough=0.45, metal=1.0, var=0.05, grime=0.8, grime_dist=0.012, bottom=0.6)
rubber = sf.pbr("SGD_Rubber", (0.012, 0.012, 0.012), rough=0.78, var=0.15, grime=0.2, bump=0.3)
steel = sf.pbr("SGD_Steel", (0.55, 0.55, 0.56), rough=0.22, metal=1.0, var=0.05, streak='Z', grime=0.4, grime_dist=0.01,
               smudge=0.35, scratch=0.4, bump=0.05)
steel_y = sf.pbr("SGD_SteelY", (0.55, 0.55, 0.56), rough=0.25, metal=1.0, var=0.05, streak='Y', grime=0.5, grime_dist=0.01, bump=0.05)
chrome = sf.pbr("SGD_Chrome", (0.62, 0.62, 0.63), rough=0.12, metal=1.0, var=0.04, grime=0.6, grime_dist=0.006, scratch=0.3)
brass = sf.pbr("SGD_Brass", (0.56, 0.38, 0.14), rough=0.3, metal=1.0, var=0.1, grime=0.7, grime_dist=0.005)
closer_m = sf.pbr("SGD_Closer", (0.32, 0.33, 0.34), rough=0.42, metal=0.55, var=0.08, grime=0.6, grime_dist=0.02,
                  edge=0.5, edge_col=(0.6, 0.6, 0.6), bump=0.4, bump_scale=300)
dark = sf.pbr("SGD_Dark", (0.01, 0.01, 0.01), rough=0.6, var=0.0, grime=0.0, bump=0.0)

glass = sf.img_mat("M_Glass_StoreGlassDoor", sf.tex(A, "GlassSmudge"), rough=0.04, alpha=True, double=True)
k3d.principled(glass).inputs['Alpha'].default_value = 1.0   # 텍스처 알파가 불투명도
push = sf.img_mat("M_StoreGlassDoor_PushSticker", sf.tex(A, "PushSticker"), rough=0.45)
caution = sf.img_mat("M_StoreGlassDoor_Caution", sf.tex(A, "Caution"), rough=0.45, alpha_clip=0.5)
pull = sf.img_mat("M_Dyn_StoreGlassDoor_PullSticker", sf.tex(A, "PullSticker"), rough=0.45)

P = []  # 문짝에 합칠 부품
# ---- 프레임: 세로틀 전체 높이, 가로틀은 사이에 (맞댄 이음 홈이 보이게 2mm 안쪽)
P += [box2((W0, -T, Z0), (W0 + SH, T, Z1), alu_v, 0.0025, 3),
      box2((W1 - SL, -T, Z0), (W1, T, Z1), alu_v, 0.0025, 3),
      box2((W0 + SH, -T + 0.002, Z1 - RT), (W1 - SL, T - 0.002, Z1), alu_h, 0.0025, 3),
      box2((W0 + SH, -T + 0.002, Z0), (W1 - SL, T - 0.002, Z0 + RB), alu_h, 0.0025, 3)]
# 아래 가로틀 장식 홈(킥 레일 라인) + 하부 브러시 실
for z in (Z0 + 0.05, Z0 + 0.13):
    for s in (-1, 1):
        P.append(box2((W0 + SH + 0.01, s * (T - 0.0015), z - 0.002), (W1 - SL - 0.01, s * (T - 0.0005), z + 0.002), dark, 0.0005, 1))
P.append(box2((W0 + 0.01, -0.006, 0.004), (W1 - 0.01, 0.006, Z0 + 0.001), rubber, 0.001, 1))
# ---- 유리 누름대(비드) + 고무 가스켓 (양면)
b, g = 0.014, 0.004
for s in (-1, 1):
    y0, y1 = s * 0.009, s * 0.022
    P += [box2((gx0, y0, gz0), (gx0 + b, y1, gz1), bead, 0.0015, 2),
          box2((gx1 - b, y0, gz0), (gx1, y1, gz1), bead, 0.0015, 2),
          box2((gx0 + b, y0, gz0), (gx1 - b, y1, gz0 + b), bead, 0.0015, 2),
          box2((gx0 + b, y0, gz1 - b), (gx1 - b, y1, gz1), bead, 0.0015, 2)]
    ya, yb = s * 0.005, s * 0.0105
    P += [box2((gx0 + b, ya, gz0 + b), (gx0 + b + g, yb, gz1 - b), rubber, 0.001, 1),
          box2((gx1 - b - g, ya, gz0 + b), (gx1 - b, yb, gz1 - b), rubber, 0.001, 1),
          box2((gx0 + b + g, ya, gz0 + b), (gx1 - b - g, yb, gz0 + b + g), rubber, 0.001, 1),
          box2((gx0 + b + g, ya, gz1 - b - g), (gx1 - b - g, yb, gz1 - b), rubber, 0.001, 1)]
# ---- 유리 (한 장, 양면)
gw, gh = gx1 - gx0 - 0.012, gz1 - gz0 - 0.012
P.append(quad(A + "_Glass", gw, gh, ((gx0 + gx1) / 2, 0, (gz0 + gz1) / 2), glass))
# ---- 스티커: 안쪽 '미세요 PUSH' (거리쪽 '당기세요' 와 등을 맞댐), 손끼임 주의
SX, SZ = 0.67, 1.32
P.append(quad(A + "_Push", 0.17, 0.085, (SX, 0.0025, SZ), push, face="+Y"))
P.append(quad(A + "_Caution", 0.08, 0.08, (gx0 + 0.07, -0.0025, 1.22), caution))
# ---- 손잡이 (스테인리스 바 Ø32, 600mm, 양면) + 받침 + 로제트
for s in (-1, 1):
    P.append(cyl(A + "_Bar", 0.016, 0.60, (HX, s * 0.090, HZ), steel, n=28, bev=0.009, seg=4))
    for z in (HZ - 0.22, HZ + 0.22):
        P.append(cyl(A + "_Post", 0.0095, 0.066, (HX, s * 0.058, z), steel_y, rot=(math.pi / 2, 0, 0), n=20, bev=0.002))
        P.append(cyl(A + "_Rose", 0.018, 0.005, (HX, s * 0.0272, z), chrome, rot=(math.pi / 2, 0, 0), n=24, bev=0.0015))
# ---- 하부 열쇠 잠금 (거리 쪽 실린더, 안쪽 돌림쇠)
LZ = Z0 + 0.09
P += [cyl(A + "_LockRose", 0.019, 0.006, (HX, -0.028, LZ), chrome, rot=(math.pi / 2, 0, 0), n=28, bev=0.0015),
      cyl(A + "_LockPlug", 0.0115, 0.006, (HX, -0.031, LZ), brass, rot=(math.pi / 2, 0, 0), n=24, bev=0.001),
      box2((HX - 0.0012, -0.0345, LZ - 0.006), (HX + 0.0012, -0.0335, LZ + 0.004), dark, 0, 1),
      cyl(A + "_TurnRose", 0.019, 0.006, (HX, 0.028, LZ), chrome, rot=(math.pi / 2, 0, 0), n=28, bev=0.0015),
      box2((HX - 0.005, 0.03, LZ - 0.016), (HX + 0.005, 0.046, LZ + 0.016), chrome, 0.003, 2)]
# ---- 맞경첩 3개: 너클(3마디)은 축 위, 문짝 날개는 거리 쪽 면에 나사 2개. 문틀 쪽 날개는 문틀에 묻힘(안 보임)
for hz in (Z0 + 0.25, 1.16, Z1 - 0.20):
    for k in (-1, 0, 1):
        P.append(cyl(A + "_Knuckle", 0.0065, 0.0325, (AX, AY, hz + k * 0.0335), chrome, n=16, bev=0.001, seg=1))
    for dz in (-0.0515, 0.0515):
        P.append(cyl(A + "_HingeTip", 0.0042, 0.004, (AX, AY, hz + dz), chrome, n=12, bev=0.0012, seg=1))
    P.append(box2((AX + 0.003, -0.0265, hz - 0.048), (0.046, -0.0245, hz + 0.048), chrome, 0.0006, 1))
    for dz in (-0.026, 0.026):
        P.append(cyl(A + "_Screw", 0.0032, 0.0012, (0.033, -0.0268, hz + dz), dark, rot=(math.pi / 2, 0, 0), n=10, bev=0.0004, seg=1))
# ---- 도어클로저 본체 (거리 쪽 위 가로틀, 일반 암 방식) + 스핀들. 스핀들은 문짝 위 끝(2.28)보다 올라와
#      암이 문짝 위로 넘어가고, 헤더 앞면(y -0.05)보다 거리 쪽에 있어 헤더와도 안 닿는다
CX, CY = 0.14, -0.064
P += [box2((0.085, -0.0255, 2.172), (0.375, -0.029, 2.258), alu_h, 0.0015, 2),
      box2((0.10, -0.029, 2.18), (0.36, -0.072, 2.25), closer_m, 0.008, 3),
      cyl(A + "_Spindle", 0.0085, 0.042, (CX, CY, 2.269), chrome, n=16, bev=0.001)]
for z in (2.198, 2.232):
    P.append(cyl(A + "_Valve", 0.0032, 0.003, (0.3605, -0.05, z), brass, rot=(0, math.pi / 2, 0), n=10, bev=0.0006, seg=1))
for x in (0.092, 0.368):
    for z in (2.178, 2.252):
        P.append(cyl(A + "_Screw", 0.0028, 0.0015, (x, -0.0295, z), dark, rot=(math.pi / 2, 0, 0), n=10, bev=0.0004, seg=1))

leaf = sf.join(P, A + "_Leaf")
k3d.set_origin(leaf, (AX, AY, 0))   # 원점 = 힌지 축 바닥 (마지막에 원점으로 옮김)
k3d.bake(leaf, 2048, keep=("M_StoreGlassDoor_PushSticker", "M_StoreGlassDoor_Caution"), ao_distance=0.05, samples=32)

# ---- 클로저 암 2링크: 본암 StoreGlassDoor_Closer(원점 = 스핀들) + 전완 StoreGlassDoor_CloserFore(원점 = 팔꿈치).
# 둘 다 Leaf 의 자식(형제): FBX 2단 중첩은 다시 불러오면 손자 변환이 틀어져서 한 단계로 둔다.
# 닫힌 상태: 본암이 거리 쪽으로 나와 팔꿈치에서 꺾여 파사드 헤더 슈(sf.DOOR_SHOE)로 돌아감
arm_m = sf.pbr("SGD_Arm", (0.3, 0.31, 0.32), rough=0.4, metal=0.7, var=0.06, grime=0.6, grime_dist=0.01, edge=0.4)
ex, ey = 0.20, -0.235          # 팔꿈치 (제작 좌표)
sx_, sy_, sz_ = sf.DOOR_SHOE   # 슈 조인트
AZ = 2.292                     # 본암 높이 (문짝 위 끝 2.28 과 헤더 아래 2.29 위)
dx, dy = ex - CX, ey - CY
L1, L2 = math.hypot(dx, dy), math.hypot(sx_ - ex, sy_ - ey)
closer = sf.join([sf.box(A + "_ArmMain", (L1, 0.02, 0.007), ((CX + ex) / 2, (CY + ey) / 2, AZ), arm_m, 0.002, 2, rot=(0, 0, math.atan2(dy, dx))),
                  cyl(A + "_ArmHub", 0.013, 0.012, (CX, CY, AZ), arm_m, n=20, bev=0.002),
                  cyl(A + "_Elbow", 0.0085, 0.02, (ex, ey, AZ + 0.006), chrome, n=16, bev=0.0015)], A + "_Closer")
k3d.set_origin(closer, (CX, CY, AZ))
k3d.bake(closer, 512, ao_distance=0.02, samples=32)
fore = sf.join([sf.pipe(A + "_Fore", [(ex, ey, sz_), (sx_, sy_, sz_)], 0.0055, arm_m, n=12),
                cyl(A + "_ShoeJoint", 0.008, 0.016, (sx_, sy_, sz_), chrome, n=16, bev=0.0015)], A + "_CloserFore")
k3d.set_origin(fore, (ex, ey, sz_))
k3d.bake(fore, 512, ao_distance=0.02, samples=32)

# ---- 거리 쪽 '당기세요 PULL' 스티커 (동적 표면, 자식)
sticker = quad(A + "_PullSticker", 0.17, 0.085, (SX, -0.0025, SZ), pull)

for c in (closer, fore, sticker):
    sf.parent(c, leaf)
sf.empty(A + "_Socket_Handle", (HX, -0.090, HZ), leaf)
sf.empty(A + "_Socket_HandleInside", (HX, 0.090, HZ), leaf)
sf.empty(A + "_Socket_Sticker", (SX, -0.003, SZ), leaf)
leaf.location = (0, 0, 0)       # 힌지 축 = 에셋 원점 (자식·소켓도 같이 이동)
bpy.context.view_layer.update()
r = lambda v: [round(c, 4) for c in v]

notes = {
    "pivot": "원점 = 힌지 축(맞경첩 너클 중심, 거리에서 볼 때 문짝 왼쪽) 바닥. StoreGlassDoor_Leaf 의 원점도 같은 점이다. "
             "문짝 몸체는 Blender 기준 x -0.004~+0.920, y +0.001~+0.051(축이 거리 쪽 면보다 1mm 바깥), 높이 0.012~2.28m(바닥 틈 12mm), 두께 50mm. "
             "축이 거리 쪽 면선 위에 있어서, 당겨 여는 동안 문짝의 어떤 점도 힌지 쪽 문틀(x<-0.007) 안으로 들어가지 않는다.",
    "check": "검증: 파사드 .blend 안에서 문짝을 0~1.45rad(0.05rad 간격)로 돌리며 StorefrontFacade_Frame 과의 관통 깊이를 BVH 로 쟀다. "
             "바닥 브러시 실(문턱에 닿는 솔)을 뺀 문짝 정점 전체가 모든 각도에서 0mm.",
    "budget": "개그의 중심 오브젝트(1m 안에서 보고 손잡이를 잡음)라 소품이 아니라 히어로 예산(8k~40k)으로 잡았다. Leaf 2048 bake.",
    "place": "StorefrontFacade 의 StorefrontFacade_Socket_DoorHinge 위치·회전에 그대로 붙이면 문 개구부(x 0.935~1.865)와 맞는다.",
    "swing": "당기면 거리 쪽(정면 방향)으로 열린다: 위에서 볼 때 손잡이가 거리 쪽으로 나오는 방향, 프로토타입 기준 최대 약 83도(1.45rad). "
             "Leaf 를 세로축(Unity Y)으로만 돌린다. 부호는 FBX 좌표 변환 때문에 임포트 뒤 한 번 확인할 것(손잡이 끝이 Unity +Z 쪽으로 나오면 당김). "
             "미는 방향은 파사드 안쪽 멈춤대(문짝과 1mm 틈, 지렛대 0.92m)에 막힌다: 매장 쪽 회전은 최대 0.0011rad 로 막고, 거리 쪽으로 최대 0.012rad 되튀게 "
             "+ 소리 + 카메라 흔들림으로 덜컹을 표현. 프로토타입 값(매장 쪽 0.05rad)을 그대로 쓰면 문짝 끝이 멈춤대를 최대 4.5cm 뚫는다.",
    "closer": {"links": "StoreGlassDoor_Closer(본암, 원점 = 스핀들 세로축)와 StoreGlassDoor_CloserFore(전완, 원점 = 팔꿈치 세로축)는 둘 다 Leaf 의 자식(형제)이다. "
                        "클로저 본체는 Leaf 에 포함.",
               "L1_m": round(L1, 4), "L2_m": round(L2, 4),
               "rest_dir_blender_xy": {"Closer(스핀들→팔꿈치)": r(((ex - CX) / L1, (ey - CY) / L1)),
                                       "CloserFore(팔꿈치→슈)": r(((sx_ - ex) / L2, (sy_ - ey) / L2))},
               "solve": "매 프레임(문 각도가 바뀔 때): S = Closer 월드 위치, H = StorefrontFacade_Socket_CloserShoe 월드 위치(수평면에 투영). "
                        "팔꿈치 E = 중심 S 반지름 L1 원과 중심 H 반지름 L2 원의 교점 중 거리 쪽(-Y/Unity +Z 쪽, 문에서 먼 쪽) 해. "
                        "Closer 를 세로축으로 돌려 본암 방향(rest_dir)이 E 를 향하게 하고, CloserFore 는 위치를 E 로 옮긴 뒤 세로축으로 돌려 전완 방향이 H 를 향하게 한다. "
                        "0~1.45rad 전체에서 |S-H| 는 0.17~0.34m 로 L1+L2(" + str(round(L1 + L2, 3)) + ") 안이라 항상 풀린다. 오일러 부호 대신 '방향 맞추기'(LookRotation 류)로 구현할 것."},
    "dynamic": {"object": "StoreGlassDoor_PullSticker", "material": "M_Dyn_StoreGlassDoor_PullSticker", "size_m": [0.17, 0.085],
                "texture": "T_StoreGlassDoor_PullSticker.png 1024x512", "uv": "0..1, U→오른쪽, V→위 (거리 쪽에서 볼 때)",
                "role": "프로토타입의 돋보기 readable '당기세요'. 흐림/선명 텍스처 교체용."},
    "sockets": {"StoreGlassDoor_Socket_Handle": "거리 쪽 손잡이 바 중심(잡는 점)", "StoreGlassDoor_Socket_HandleInside": "매장 쪽 손잡이",
                "StoreGlassDoor_Socket_Sticker": "당기세요 스티커 시선 목표"},
    "hinges": "맞경첩 3개(z 0.26 / 1.16 / 2.08), 너클은 축 위라 문이 돌아도 제자리. 문틀 쪽 날개는 문틀에 묻힌 것으로 보고 모델링하지 않았다.",
    "glass": "M_Glass_StoreGlassDoor: BaseColor 텍스처 알파 = 유리 불투명도(기본 0.10 + 손자국·먼지). 양면.",
}
k3d.export(A, "Storefront", [leaf], notes=notes)
k3d.preview(A, [leaf])
k3d.preview(A, [leaf], views=((0, 8),), lens=35, tag="fp")
sf.look((0.35, -0.75, 1.5), (0.72, 0, 1.22), lens=35, path=k3d.os.path.join(k3d.SRC, "Previews", A + "_close.png"))
sf.look((0.55, -0.55, 2.0), (0.22, -0.08, 2.24), lens=40, path=k3d.os.path.join(k3d.SRC, "Previews", A + "_closer.png"))

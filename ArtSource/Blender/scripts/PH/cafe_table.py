# PH_CafeTable__Body: 카페 둥근 탁자. StoreProps/table.py 를 복사해 원판과 원형 받침으로 바꿨다.
# 소스 좌표: x = Unity x, y = Unity z, z = Unity y(높이). 원점은 바닥 중앙이다.
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE] + [os.path.join(HERE, "..", d) for d in ("Store", "StoreProps")]
import ph, bpy
import storelib as S
import _common as C
k3d = ph.k3d

k3d.reset()
A = "PH_CafeTable__Body"
TOP_Z, TOP_T, R = 0.735, 0.03, 0.32  # 상판 윗면은 씬의 냅킨, 빨대 높이다
zb = TOP_Z - TOP_T                   # 상판 밑면
z0 = 0.005                           # 받침 밑면 (조절발 높이만큼 뜬다)

oak = C.wood("M_tmp_Oak", 0.7, tint=(0.95, 0.84, 0.7), rough=0.38, wipe=0.22, edge_dark=0.25)
steel = C.powder_coat("M_tmp_Steel", (0.02, 0.02, 0.022), rough=0.5, wear=0.35, scratch=0.12, peel=0.0,
                      metal_col=(0.25, 0.25, 0.26))  # 드러난 강철은 어두운 회색 (흰 얼룩 방지)
glide = C.plastic("M_tmp_Glide", (0.02, 0.02, 0.02), rough=0.55, grime=0.9, wear=0.2, scuff=0.2)
screw = C.stainless("M_tmp_Screw", 0.35, 'Z', smudge=0.2)

parts = [
    C.cyl(A + "_Top", R, TOP_T, (0, 0, zb), 64, oak, bev=0.005, seg=3),
    C.cyl(A + "_Flange", 0.085, 0.006, (0, 0, zb - 0.005), 48, steel, bev=0.001, seg=1),
    C.cyl(A + "_Col", 0.03, zb - 0.017, (0, 0, 0.015), 32, steel, bev=0),
    # 살짝 볼록한 원판 받침
    C.lathe(A + "_Base", [(0, z0), (0.196, z0), (0.2, z0 + 0.002), (0.2, z0 + 0.0055), (0.197, z0 + 0.0085),
                          (0.185, z0 + 0.0105), (0.14, z0 + 0.0145), (0.09, z0 + 0.0175), (0.05, z0 + 0.019),
                          (0, z0 + 0.019)], 64, steel, sharp=50),
    # 기둥 아래, 위 칼라
    C.lathe(A + "_CollarLow", [(0, 0.02), (0.05, 0.02), (0.05, 0.027), (0.047, 0.03), (0.04, 0.0325), (0.035, 0.04),
                               (0.032, 0.056), (0.032, 0.062), (0.0312, 0.0635), (0, 0.0635)], 32, steel, sharp=50),
    C.lathe(A + "_CollarTop", [(0, 0.668), (0.0312, 0.668), (0.0335, 0.67), (0.0335, 0.676), (0.037, 0.688),
                               (0.045, 0.695), (0.052, 0.697), (0.052, 0.702), (0, 0.702)], 32, steel, sharp=50),
]
for i in range(4):
    a = math.radians(45 + 90 * i)
    parts.append(C.cyl(f"{A}_Screw{i}", 0.0055, 0.0035, (0.068 * math.cos(a), 0.068 * math.sin(a), zb - 0.0075),
                       12, screw, bev=0.001, seg=1))
    # 수평 조절발: 윗부분은 받침 안으로 1mm 들어간다
    parts.append(C.cyl(f"{A}_Glide{i}", 0.017, z0 + 0.001, (0.165 * math.cos(a), 0.165 * math.sin(a), 0),
                       16, glide, bev=0, r2=0.014))
for p in parts:
    C.ensure_uv(p)

src = S.join(parts, A + "_src")
o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src, do_unlink=True)  # 원본이 씬에 남으면 AO 굽기가 오염된다
k3d.bake(o, 1024, ao_distance=0.06)
ph.finish(A, o, notes="카페 둥근 탁자. 원점 바닥 중앙, 상판 윗면 y 0.735, 상판 지름 0.64, 기둥 지름 0.06, 받침 지름 0.4. "
                      "원형이라 앞뒤 구분이 없다.")

for m in bpy.data.materials:
    m.use_backface_culling = True  # Unity 처럼 뒷면을 안 그리고 본다
k3d.preview(A, [o], views=((180, 12), (215, 18), (0, 12)))
k3d.preview(A, [o], views=((200, -25),), ground=False, tag="under")  # 상판 밑 플랜지와 나사 확인용
bpy.ops.mesh.primitive_plane_add(size=8)
bpy.context.active_object.data.materials.append(k3d.mat("k3d_floor", (0.2, 0.13, 0.08), 0.6))
S.shot(A + "_eye", ph.at_unity(0.9, 1.6, -0.9), ph.at_unity(0, 0.7, 0), lens=35,
       lights=[(ph.at_unity(0, 3.0, -1.0), 150, 3.0, (1, 0.97, 0.92))])

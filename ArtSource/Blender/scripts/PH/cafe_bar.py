"""PH_BarCounter__Body: 카페 바 카운터. Store/store_counter.py 11-61행에서 파생 (빨강 -> 짙은 원목, 픽업 구간 삭제).
turn(180) 뒤 Unity (x, y, z) = 소스 (x, z, y). 아래 수치는 소스 좌표이고 y 값이 곧 Unity z 다.
원점 = 바닥의 Body 중심(경계 상자 중심이 아니다), 앞 -Z. 상판 윗면 y 1.06 에 진열장과 픽업 받침이 놓인다."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Store")]
import ph, bpy, bmesh
import storelib as S
k3d = ph.k3d

k3d.reset()
A = "PH_BarCounter__Body"
P = "M_" + A + "_"

L, TOP = 5.3, 1.06
X0, X1 = -L / 2, L / 2
XA, XB = X0 + 0.005, X1 - 0.005  # 앞면 부품은 옆판보다 5 mm 안쪽 (같은 평면이 겹치면 지글거린다)

# ---- 머티리얼 (굽기용 절차 재질)
wood_img = k3d.polyhaven("kitchen_wood", "1k")["diff"]
# 판마다 색과 결 크기가 달라야 원목처럼 보인다
woods = [S.pbr(f"{P}Wood{i}", c, 0.42, img=wood_img, img_m=s, var=0.06, grime=0.5, gdist=0.03, edge=0.35,
               edge_col=(0.55, 0.45, 0.35), bump=0.05, smudge=0.15)
         for i, (c, s) in enumerate((((1.3, 1.18, 1.0), 0.6), ((1.15, 1.02, 0.86), 0.73), ((1.45, 1.3, 1.1), 0.87)))]
dark = dict(img=wood_img, var=0.06, grime=0.4, gdist=0.03, edge=0.35, edge_col=(0.16, 0.1, 0.06), bump=0.05, smudge=0.15)
m_band = S.pbr(P + "Band", (0.45, 0.30, 0.20), 0.4, img_m=1.2, **dark)
m_end = S.pbr(P + "End", (0.45, 0.30, 0.20), 0.4, img_m=0.6, **dark)
# 띠는 가로로 긴 판이라 결도 가로로 돌린다 (첫 Mapping 이 이미지용)
next(n for n in m_band.node_tree.nodes if n.type == 'MAPPING').inputs['Rotation'].default_value = (0, math.pi / 2, 0)
m_kick = S.pbr(P + "Kick", (0.0137, 0.105, 0.0595), 0.5, grime=0.6, grime_col=(0.01, 0.02, 0.015), scratch=0.6,
               edge=0.4, edge_col=(0.08, 0.16, 0.12))  # 숲길 커피 초록 #1F5B45
m_stone = S.pbr(P + "Stone", (0.055, 0.052, 0.05), 0.22, var=0.25, vscale=180, grime=0.4, smudge=0.35, scratch=0.25,
                bump=0.03, bscale=300)
m_brass = S.pbr(P + "Brass", (0.7, 0.5, 0.2), 0.3, 1.0, var=0.06, grime=0.4, brush=0.12, smudge=0.25, scratch=0.25,
                bump=0.02)
# ponytail: 슬랫 틈과 뒷면은 단색으로 두고 아틀라스를 앞면에 몰아 준다. 뒤에서 보는 장면이 생기면 굽는다.
m_core = k3d.mat(P + "Dark", (0.035, 0.028, 0.022), 0.7)

# ---- 본체 (코어 + 옆판 + 굽도리 + 띠 + 상판)
body = [
    S.boxz("c_core", X0 + 0.01, X1 - 0.01, -0.295, 0.305, 0, 1.0, m_core, 0),
    S.boxz("c_kick", XA, XB, -0.35, -0.29, 0, 0.12, m_kick, 0.004),
    S.boxz("c_band", XA, XB, -0.316, -0.29, 0.86, 1.0, m_band, 0.004, 3),
    S.boxz("c_bandlip", XA, XB, -0.32, -0.30, 0.852, 0.862, m_brass, 0.002, 1),  # 띠 아래 금속 몰딩
    S.boxz("c_top", -2.7, 2.7, -0.41, 0.35, 1.0, TOP, m_stone, 0.004, 3),
]
for x in (X0, X1 - 0.02):
    body.append(S.boxz("c_end", x, x + 0.02, -0.31, 0.31, 0, 1.0, m_end, 0.003))
N, W, G = 117, 0.03, 0.015  # 세로 원목 판
rng = random.Random(3)
for i in range(N):
    x = -(N * W + (N - 1) * G) / 2 + i * (W + G)
    body.append(S.boxz("c_slat", x, x + W, -0.31, -0.29, 0.115, 0.865, rng.choice(woods), 0.0035, 1))

# ---- 발 받침 (황동 봉, 받침대는 슬랫 앞면까지)
rail = [S.cyl("c_rail", 0.015, 5.2, (0, -0.42, 0.22), m_brass, 24, 0.002, rot=(0, math.pi / 2, 0))]
for x in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):
    rail.append(S.cyl("c_post", 0.008, 0.11, (x, -0.365, 0.22), m_brass, 12, 0.001, rot=(math.pi / 2, 0, 0)))
    rail.append(S.cyl("c_flange", 0.024, 0.006, (x, -0.313, 0.22), m_brass, 20, 0.001, rot=(math.pi / 2, 0, 0)))

# ph.part 는 모디파이어를 버리고 원본을 씬에 남긴다. 먼저 합쳐서 베벨을 적용하고, 원본은 지워야 AO 에 안 잡힌다.
front = S.join(body, "bar_front")
# 안 보이는 면을 지워 아틀라스를 앞면에 준다: 아래를 보는 평면(눈이 늘 1 m 위), 앞쪽 부품의 등. 봉은 둥글어서 뺐다.
bm = bmesh.new()
bm.from_mesh(front.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.99 or (f.normal.y > 0.6 and f.calc_center_median().y < 0)],
                 context='FACES')
bm.to_mesh(front.data)
bm.free()
src = S.join([front, *rail], "bar_src")
o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src, do_unlink=True)

# 오래 걸리는 굽기 전에 규격을 본다 (Unity 좌표 = -x, z, -y)
pts = [(-v.co.x, v.co.z, -v.co.y) for v in o.data.vertices]
mn, mx = [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
print("bar bbox unity", mn, mx)
for got, want in zip(mn + mx, (-2.7, 0, -0.435, 2.7, TOP, 0.35)):
    assert abs(got - want) < 0.002, (mn, mx)

# 긴 면이 번지지 않게 2048. pack 여백은 섬 수에 비례해 커져서(SCALED) 판 수백 개면 UV 의 80% 가 빈다.
# ponytail: k3d.bake 는 픽셀 여백과 UV 여백을 묶어 받아 여기서만 UV 쪽을 바꾼다. k3d 를 고칠 수 있으면 인자로 뺀다.
uv_smart = k3d.uv_smart
k3d.uv_smart = lambda obj, faces, margin, layer: uv_smart(obj, faces, 0.0016, layer)
k3d.bake(o, 2048, keep=(m_core.name,), samples=48, ao_distance=0.12, margin=6)
ph.finish(A, o, notes="바 카운터. 원점 = 바닥의 Body 중심(경계 상자 중심 아님), 앞 -Z, 상판 윗면 y 1.06. "
                      "M_PH_BarCounter__Body_Dark 는 슬랫 틈과 뒷면의 단색이라 굽지 않았다.")
k3d.preview(A, [o], views=((215, 15), (180, 6), (35, 18)))  # 앞면은 Blender +Y: 215, 180 이 앞, 35 가 뒤

# 플레이어가 서는 쪽에서 가운데 구간만 크게 본다 (텍스처 번짐 확인용, 내보내지 않는다)
aim = S.boxz("aim", -0.45, 0.45, 0.3, 0.44, 0, TOP, None, 0)
aim.hide_render = True
bpy.context.view_layer.update()
k3d.preview(A, [aim], views=((180, 25),), tag="near")

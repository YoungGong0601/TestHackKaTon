# StoreChair: 패스트푸드 매장 의자 0.84m. 성형 합판(오크 무늬목, 겹 보이는 단면) 좌판/등판 + 검정 분체도장 Ø19 강관 프레임
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreChair"
k3d.reset()

R = 0.0095          # 파이프 반지름
X = 0.222           # 프레임 반폭 (기둥이 좌판 0.42 바깥을 지나도록)
SEAT_Z = 0.432      # 좌판 받침 파이프 중심 높이


def ply_edge(name, axis):
    """합판 단면: 1.5mm 겹 줄무늬 (축 = 두께 방향)."""
    m, nt, p = new_mat(name)
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type, w.bands_direction = 'BANDS', axis
    w.inputs['Scale'].default_value = 209
    w.inputs['Distortion'].default_value = 1.5
    w.inputs['Detail'].default_value = 2
    nt.links.new(coord(nt), w.inputs['Vector'])
    v = coord(nt)
    band = mrange(nt, w.outputs['Factor'], 0.15, 0.35)
    col = mix(nt, band, (0.16, 0.1, 0.055), (0.55, 0.42, 0.28))
    col = mix(nt, 1.0, col, op(nt, 'ADD', 0.85, op(nt, 'MULTIPLY', noise(nt, 40, 4, vec=v), 0.3)), 'MULTIPLY')
    col = mix(nt, op(nt, 'SUBTRACT', 1.0, cavity(nt, 0.01)), col, (0.05, 0.035, 0.02))
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.6
    nt.links.new(bump(nt, band, 0.1, 0.0003), p.inputs['Normal'])
    return m


def rr_clamp(a, b, W, D, rc, border):
    """격자점을 모서리 둥근 사각형 안으로 (테두리 점은 호 위로)."""
    if abs(a) > W / 2 - rc and abs(b) > D / 2 - rc:
        ca, cb = math.copysign(W / 2 - rc, a), math.copysign(D / 2 - rc, b)
        da, db = a - ca, b - cb
        L = math.hypot(da, db)
        if border or L > rc:
            s = rc / max(L, 1e-9)
            return ca + da * s, cb + db * s
    return a, b


def shell(name, W, D, rc, n, surf, t, mats):
    """곡면 판: surf(a,b) -> (앞면 점, 두께 방향 단위벡터). 슬롯 0 면, 1 단면."""
    bm = bmesh.new()
    F, B = {}, {}
    for i in range(n + 1):
        for j in range(n + 1):
            a, b = -W / 2 + W * i / n, -D / 2 + D * j / n
            a, b = rr_clamp(a, b, W, D, rc, i in (0, n) or j in (0, n))
            p, nv = surf(a, b)
            F[i, j] = bm.verts.new(p)
            B[i, j] = bm.verts.new(p - nv * t)
    for i in range(n):
        for j in range(n):
            bm.faces.new((F[i, j], F[i + 1, j], F[i + 1, j + 1], F[i, j + 1]))
            bm.faces.new((B[i, j + 1], B[i + 1, j + 1], B[i + 1, j], B[i, j]))
    ring = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + \
           [(i, n) for i in range(n, 0, -1)] + [(0, j) for j in range(n, 0, -1)]
    for k in range(len(ring)):
        c0, c1 = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((F[c0], B[c0], B[c1], F[c1])).material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = from_bm(bm, name)
    for m in mats:
        o.data.materials.append(m)
    bevel(o, 0.0025, 2, angle=50)
    return o


mwood = wood("M_StoreChair_WoodSrc", 0.6, tint=(0.92, 0.8, 0.66), rough=0.4, wipe=0.3, wear=0.6, edge_dark=0.35, scratch=0.5)
msteel = powder_coat("M_StoreChair_SteelSrc", (0.018, 0.018, 0.02), rough=0.45, wear=0.55, scratch=0.6, peel=0.1)
mglide = plastic("M_StoreChair_GlideSrc", (0.02, 0.02, 0.02), rough=0.6, grime=0.9, wear=0.2)
mscrew = powder_coat("M_StoreChair_ScrewSrc", (0.03, 0.03, 0.03), rough=0.35, wear=0.8, edge_r=0.001)
parts = []

# 좌판: 오목한 면 + 앞쪽 폭포형으로 말림
SW, SD = 0.42, 0.42


def seat_surf(a, b):
    z = SEAT_Z + R + 0.012 - 0.007 * (1 - (a / (SW / 2)) ** 2) * (1 - ((b + 0.02) / (SD / 2)) ** 2)
    if b < -0.15:
        z -= ((-0.15 - b) / 0.06) ** 2 * 0.024
    if b > 0.17:
        z += ((b - 0.17) / 0.04) ** 2 * 0.006
    return Vector((a, b, z)), Vector((0, 0, 1))


parts.append(shell(A + "_Seat", SW, SD, 0.045, 20, seat_surf, 0.012, [mwood, ply_edge("M_StoreChair_PlySeatSrc", 'Z')]))

# 등판: 몸쪽으로 감싸는 곡면, 뒤로 9도 기울어 기둥 앞면에 고정
K = 0.065 / 0.398


def up_y(z):
    return 0.17 + K * (z - SEAT_Z)


BW, BH, BZ = 0.47, 0.18, 0.75   # 등판은 기둥 앞면을 덮도록 넓힘
nb = Vector((0, -1, K)).normalized()


def back_surf(a, b):
    z = BZ + b
    y = up_y(z) - R + 0.018 * (1 - (a / (BW / 2)) ** 2)
    return Vector((a, y, z)) + nb * 0.011, nb


parts.append(shell(A + "_Back", BW, BH, 0.03, 16, back_surf, 0.011, [mwood, ply_edge("M_StoreChair_PlyBackSrc", 'Y')]))

# 프레임: 좌우 각각 앞다리-좌판 레일-등받이 기둥을 한 번에 구부린 파이프 + 용접된 뒷다리
for s in (-1, 1):
    x = s * X
    parts.append(tube(f"{A}_Frame{s}", [(x, -0.17, 0.014), (x, -0.17, SEAT_Z), (x, 0.17, SEAT_Z), (x, up_y(0.835), 0.835)],
                      R, 0.035, msteel))
    parts.append(tube(f"{A}_RearLeg{s}", [(x, 0.168, SEAT_Z + 0.004), (x, 0.215, 0.014)], R, 0.01, msteel))
    parts.append(tube(f"{A}_Stretcher{s}", [(x, -0.17, 0.16), (x, 0.1986, 0.16)], R * 0.8, 0.01, msteel))
    for y in (-0.17, 0.215):
        parts.append(cyl(f"{A}_Glide{s}{y}", R + 0.0015, 0.014, (x, y, 0.0), 16, mglide, bev=0.002, seg=2))
parts.append(tube(A + "_RailF", [(-X, -0.15, SEAT_Z), (X, -0.15, SEAT_Z)], R * 0.85, 0.01, msteel))
parts.append(tube(A + "_RailB", [(-X, 0.15, SEAT_Z), (X, 0.15, SEAT_Z)], R * 0.85, 0.01, msteel))
parts.append(tube(A + "_RailH", [(-X, 0.015, 0.16), (X, 0.015, 0.16)], R * 0.7, 0.01, msteel))
# 등판 나사 (접시머리, 판 앞면 법선 방향)
for s in (-1, 1):
    for z in (0.70, 0.80):
        a = s * X
        p, _ = back_surf(a, z - BZ)
        sc = cyl(f"{A}_Screw{s}{z}", 0.0045, 0.0015, (0, 0, 0), 12, mscrew, bev=0.0006, seg=1)
        sc.rotation_euler = (math.atan2(1, K), 0, 0)
        sc.location = p - nb * 0.0008
        parts.append(sc)

for p in parts:
    ensure_uv(p)
o = k3d.join(parts, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 1024)
socket(A + "_Socket_Sit", (0, 0, 0.455), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions))
k3d.export(A, "Store", [o], notes=(
    "패스트푸드 의자, 등판 윗끝 0.84m, 좌면 0.455m, 정면(-Y)으로 앉음. 성형 합판(오크 무늬목, 단면 겹 줄무늬) + Ø19 검정 분체도장 강관 + 나일론 발굽. "
    "소켓: _Socket_Sit(좌면 중앙). 프로토타입처럼 테이블 중심에서 ±0.62m 에 마주보게 배치."))
k3d.preview(A, [o])
k3d.preview(A, [o], views=((215, 50), (180, 80), (90, 30)), tag="review")  # 뒤 위/위/옆: 기둥-좌판 간섭 확인

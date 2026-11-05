# StoreBoothBench: 부스 벤치 (프로토타입 N(): 폭 0.98, 좌면 0.54, 등받이 윗끝 1.26)
# 버건디 비닐 레더 좌석 쿠션(파이핑, 앉는 자리 처짐) + 세로 채널 등 쿠션 4개 + 오크 라미네이트 받침/등판/상단 캡 + 검정 킥플레이트
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *

A = "StoreBoothBench"
k3d.reset()
HW = 0.49                                   # 반폭 (폭 0.98)
SY0, SY1, SZ0, SZ1 = -0.25, 0.175, 0.40, 0.54  # 좌석 쿠션 (원점 = 좌석 중심 바닥)
BY, BT, TOP = 0.25, 0.02, 1.26              # 등판 앞면 y, 두께(뒤끝 0.27), 윗끝
CH = 0.245                                  # 채널 폭 (솔기 x = -0.245, 0, 0.245)
RED = (0.366, 0.0232, 0.0144)               # #A32A20 (linear)
RED_D = (0.195, 0.0137, 0.0091)             # #7A1F18 파이핑


def gbox(name, lo, hi, n, mat, drop=(), deform=None, bev=0.004, seg=2, angle=35):
    """축별 n 칸으로 나뉜 상자. drop = 지울(가려지는) 면 방향, deform(co) -> co."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([lo[i] + (hi[i] - lo[i]) * (v.co[i] + 0.5) for i in range(3)])
    for ax in range(3):
        for k in range(1, n[ax]):
            co, no = [0, 0, 0], [0, 0, 0]
            co[ax], no[ax] = lo[ax] + (hi[ax] - lo[ax]) * k / n[ax], 1
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
    bm.normal_update()
    dirs = {'-X': (0, -1), '+X': (0, 1), '-Y': (1, -1), '+Y': (1, 1), '-Z': (2, -1), '+Z': (2, 1)}
    kill = [f for f in bm.faces if any(f.normal[dirs[d][0]] * dirs[d][1] > 0.99 for d in drop)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    if deform:
        for v in bm.verts:
            v.co = deform(v.co.copy())
    o = from_bm(bm, name, mat)
    if bev:
        bevel(o, bev, seg, angle)
    return o


def vinyl(name, col):
    """비닐 레더(레자): 스캔 가죽 결 + 앉는 자리 광택 마모 + 앞 모서리 갈라짐 + 주름 + 모서리 스커프 + 솔기 때/스티치."""
    m, nt, p = new_mat(name)
    v = coord(nt)
    t = ph_tex(nt, "leather_red_02", 0.3, which=('rough', 'nor', 'ao'))
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(nt.nodes.new('ShaderNodeTexCoord').outputs['Object'], sep.inputs[0])
    X, Y, Z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
    ax = op(nt, 'ABSOLUTE', X)
    gn = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(nt.nodes.new('ShaderNodeNewGeometry').outputs['Normal'], gn.inputs[0])
    front = mrange(nt, gn.outputs['Y'], -0.5, -0.85)          # 앞(-Y)을 보는 면
    up = mrange(nt, gn.outputs['Z'], 0.5, 0.85)               # 위를 보는 면
    # 기본 색: 얼룩 + 스캔 AO 로 결 명암
    base = mix(nt, 1.0, col, mrange(nt, noise(nt, 3, 3, vec=v), 0.3, 0.7, 0.86, 1.1), 'MULTIPLY')
    base = mix(nt, 1.0, base, mrange(nt, t['ao'], 0.7, 1.0, 0.72, 1.0), 'MULTIPLY')
    # 앉는 자리 2곳 (x=±0.245): 닳아 번들거리고 색이 살짝 빠짐
    dx = op(nt, 'DIVIDE', op(nt, 'SUBTRACT', ax, CH), 0.17)
    dy = op(nt, 'DIVIDE', op(nt, 'ADD', Y, 0.04), 0.15)
    d2 = op(nt, 'ADD', op(nt, 'MULTIPLY', dx, dx), op(nt, 'MULTIPLY', dy, dy))
    sit = op(nt, 'MULTIPLY', mrange(nt, d2, 1.0, 0.15), op(nt, 'MULTIPLY', up, mrange(nt, Z, 0.5, 0.53)))
    # 등 기대는 자리 (어깨 높이)
    dz = op(nt, 'DIVIDE', op(nt, 'SUBTRACT', Z, 0.9), 0.16)
    lean = op(nt, 'MULTIPLY', mrange(nt, op(nt, 'ADD', op(nt, 'MULTIPLY', dx, dx), op(nt, 'MULTIPLY', dz, dz)), 1.0, 0.2), front)
    lean = op(nt, 'MULTIPLY', lean, mrange(nt, Y, 0.21, 0.19))
    wear = op(nt, 'MAXIMUM', sit, op(nt, 'MULTIPLY', lean, 0.7))
    # 동그란 얼룩으로 보이지 않게 노이즈로 크게 끊음
    wear = op(nt, 'MULTIPLY', wear, mrange(nt, noise(nt, 9, 6, 0.65, vec=v, distortion=0.6), 0.38, 0.68))
    base = mix(nt, op(nt, 'MULTIPLY', wear, 0.2), base, (0.3, 0.1, 0.08))
    # 앞 모서리 쓸림 + 갈라짐 (다리 닿는 곳, 일부 구간만)
    rub = op(nt, 'MULTIPLY', mrange(nt, Y, -0.2, -0.245), mrange(nt, Z, 0.45, 0.53))
    rub = op(nt, 'MULTIPLY', rub, op(nt, 'SUBTRACT', 1.0, mrange(nt, Z, 0.6, 0.62)))
    ck = nt.nodes.new('ShaderNodeTexVoronoi')
    ck.feature = 'DISTANCE_TO_EDGE'
    ck.inputs['Scale'].default_value = 70
    nt.links.new(coord(nt, 'Object', (1, 2.5, 1)), ck.inputs['Vector'])
    crack = op(nt, 'MULTIPLY', mrange(nt, ck.outputs['Distance'], 0.035, 0.012),
               op(nt, 'MULTIPLY', rub, mrange(nt, noise(nt, 2.2, 2, vec=v), 0.56, 0.64)))
    # 모서리 스커프 (하얗게 닳음)
    e = op(nt, 'MULTIPLY', edge_mask(nt, 0.006, 0.03, 0.25), mrange(nt, noise(nt, 30, 5, vec=v), 0.35, 0.65))
    scuff = op(nt, 'MAXIMUM', op(nt, 'MULTIPLY', e, 0.8), op(nt, 'MULTIPLY', rub, 0.35))
    base = mix(nt, op(nt, 'MULTIPLY', scuff, 0.5), base, (0.5, 0.22, 0.18))
    base = mix(nt, crack, base, (0.62, 0.55, 0.5))           # 갈라진 틈에 흰 바탕천
    # 솔기/구석 때
    cav = op(nt, 'SUBTRACT', 1.0, cavity(nt, 0.035, 0.5, 1.0))
    base = mix(nt, op(nt, 'MULTIPLY', cav, 0.75), base, (0.03, 0.008, 0.006))
    # 스티치: 채널 솔기 양옆 9mm 에 가는 실 줄 (앞을 보는 등 쿠션 면만)
    q = op(nt, 'ADD', op(nt, 'DIVIDE', X, CH), 0.5)
    dseam = op(nt, 'MULTIPLY', op(nt, 'ABSOLUTE', op(nt, 'SUBTRACT', op(nt, 'FRACT', q), 0.5)), CH)
    st = mrange(nt, op(nt, 'ABSOLUTE', op(nt, 'SUBTRACT', dseam, 0.009)), 0.0016, 0.0007)
    st = op(nt, 'MULTIPLY', st, op(nt, 'MULTIPLY', front, mrange(nt, Z, 0.58, 0.62)))
    base = mix(nt, op(nt, 'MULTIPLY', st, 0.6), base, (0.09, 0.02, 0.015))
    nt.links.new(base, p.inputs['Base Color'])
    # 거칠기
    r = op(nt, 'ADD', 0.3, op(nt, 'MULTIPLY', t['rough'], 0.28))
    r = fmix(nt, op(nt, 'MULTIPLY', wear, 0.7), r, 0.22)
    r = fmix(nt, op(nt, 'MAXIMUM', scuff, crack), r, 0.62)
    r = fmix(nt, cav, r, 0.7)
    nt.links.new(r, p.inputs['Roughness'])
    # 노멀: 스캔 결 + 주름(좌석 앞쪽 앞뒤 방향, 등 쿠션 아래 가로) + 갈라짐 + 스티치 홈
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = 0.8
    nt.links.new(t['nor'], nm.inputs['Color'])
    w1 = op(nt, 'MULTIPLY', noise(nt, 1.0, 3, 0.6, vec=coord(nt, 'Object', (70, 5, 70))), mrange(nt, Y, -0.16, -0.25))
    w2 = op(nt, 'MULTIPLY', noise(nt, 1.0, 3, 0.6, vec=coord(nt, 'Object', (6, 6, 90))),
            op(nt, 'MULTIPLY', mrange(nt, Z, 0.68, 0.56), front))
    h = op(nt, 'ADD', op(nt, 'MULTIPLY', op(nt, 'ADD', w1, w2), 0.8), op(nt, 'MULTIPLY', crack, -1.0))
    h = op(nt, 'ADD', h, op(nt, 'MULTIPLY', st, -0.4))
    nt.links.new(bump(nt, h, 0.25, 0.002, normal=nm.outputs['Normal']), p.inputs['Normal'])
    return m


mvin = vinyl("M_StoreBoothBench_VinylSrc", RED)
mpipe = vinyl("M_StoreBoothBench_PipeSrc", RED_D)
mwood = wood("M_StoreBoothBench_WoodSrc", 0.8, tint=(0.88, 0.7, 0.54), rough=0.45, wipe=0.2, wear=0.5, edge_dark=0.45, scratch=0.45)
mkick = plastic("M_StoreBoothBench_KickSrc", (0.02, 0.02, 0.02), rough=0.6, grime=1.0, wear=0.6, scuff=1.0)


# 좌석 쿠션: 가운데 볼록 + 두 자리 살짝 꺼짐 + 앞면 불룩
def seat_def(co):
    u = co.x / HW
    w = (co.y - (SY0 + SY1) / 2) / ((SY1 - SY0) / 2)
    if co.z > SZ1 - 1e-4:
        dip = sum(math.exp(-((co.x - s * CH) / 0.12) ** 2) for s in (-1, 1)) * math.exp(-((co.y + 0.04) / 0.12) ** 2)
        co.z += 0.012 * (1 - u ** 4) * (1 - w ** 4) - 0.009 * dip * (1 - w ** 4)
    if co.y < SY0 + 1e-4:
        tz = (co.z - (SZ0 + SZ1) / 2) / ((SZ1 - SZ0) / 2)
        co.y -= 0.006 * (1 - tz ** 2) * (1 - u ** 4)
    return co


cush = [gbox(A + "_Seat", (-HW, SY0, SZ0), (HW, SY1, SZ1), (14, 6, 2), mvin, deform=seat_def, bev=0.018, seg=3)]
# 좌석 윗모서리 파이핑 (앞 + 양옆)
zt, ins = SZ1 - 0.004, 0.004
cush.append(tube(A + "_Pipe", [(-HW + ins, SY1 - 0.02, zt), (-HW + ins, SY0 + ins, zt), (HW - ins, SY0 + ins, zt),
                               (HW - ins, SY1 - 0.02, zt)], 0.0045, 0.015, mpipe, res=1))


# 등 쿠션 채널 4개: 아래 두껍고 위 얇음(살짝 뒤로 기움) + 앞면 불룩
def pillow_def(xc, z0, z1, y0):
    def f(co):
        t = (co.z - z0) / (z1 - z0)
        k = (BY - co.y) / (BY - y0)                     # 1 = 앞면, 0 = 뒷면
        uu = (co.x - xc) / (CH / 2)
        co.y += k * (0.03 * t - 0.014 * (1 - uu ** 2) * (1 - (2 * t - 1) ** 2))
        return co
    return f


for i in range(4):
    x0 = -HW + i * CH
    cush.append(gbox(f"{A}_Back{i}", (x0, 0.16, 0.43), (x0 + CH, BY, TOP - 0.025), (3, 2, 7), mvin, drop=('+Y', '-Z'),
                     deform=pillow_def(x0 + CH / 2, 0.43, TOP - 0.025, 0.16), bev=0.03, seg=3))

# 프레임: 받침 상자 + 킥플레이트 + 등판 + 상단 캡
frame = [gbox(A + "_Base", (-HW, -0.23, 0.08), (HW, BY, SZ0), (1, 1, 1), mwood, drop=('+Y',), bev=0.004),
         gbox(A + "_Kick", (-HW, -0.2, 0.0), (HW, BY, 0.08), (1, 1, 1), mkick, drop=('+Z', '-Z', '+Y'), bev=0.003),
         gbox(A + "_Board", (-HW, BY, 0.0), (HW, BY + BT, TOP - 0.025), (1, 1, 1), mwood, drop=('-Z', '+Z'), bev=0.003),
         gbox(A + "_Cap", (-HW - 0.005, 0.15, TOP - 0.025), (HW + 0.005, BY + BT + 0.005, TOP), (1, 1, 1), mwood, bev=0.006, seg=3)]

for p_ in cush + frame:
    ensure_uv(p_)
o = k3d.join(frame, A)
k3d.set_origin(o, Vector((0, 0, 0)))
k3d.bake(o, 1024)
c = k3d.join(cush, A + "_Cushion")
k3d.set_origin(c, Vector((0, 0, 0)))
k3d.bake(c, 1024)
c.parent = o
c.matrix_parent_inverse = o.matrix_world.inverted()
socket(A + "_Socket_SitL", (-CH, -0.04, SZ1), o)
socket(A + "_Socket_SitR", (CH, -0.04, SZ1), o)
print("STAT", A, "tris", scene_tris([o]), "dims", tuple(round(x, 3) for x in o.dimensions), tuple(round(x, 3) for x in c.dimensions))
k3d.export(A, "Store", [o], notes=(
    "부스 벤치 폭 0.98(X), 좌면 0.54m, 등받이 윗끝 1.26m, 깊이 0.52m(y -0.25 ~ +0.27). 버건디 비닐 레더(#A32A20) 좌석 쿠션 + 세로 채널 등 쿠션 4칸"
    "(솔기 x = -0.245/0/+0.245) + 오크 라미네이트 받침·등판·상단 캡 + 검정 킥플레이트. "
    "원점 = 좌석 중심 바닥, 정면 -Y(테이블 쪽). 루트 = 우드 프레임, 자식 StoreBoothBench_Cushion = 쿠션(정적, 텍스처 세트만 분리). "
    "배치: 프로토타입 N(P) 부스마다 2개, 벤치 원점 = (5.0, 0, P ± 0.82), 두 벤치가 테이블(StoreTable4, 4.72, P)을 마주 봄 "
    "(P = -1.95, 0.45, 2.65). 등판 뒤끝이 좌석 중심에서 0.27m 라 이웃 부스 등판끼리 약 2cm 띄워짐 (프로토타입 등받이 0.13 두께를 그대로 쓰면 5cm 겹침). "
    "소켓: _Socket_SitL / _Socket_SitR (x = ∓0.245, 좌면 0.54, 정면에서 본 왼쪽/오른쪽)."))
k3d.preview(A, [o])
k3d.preview(A, [o], views=((20, 25),), lens=35, tag="fp")

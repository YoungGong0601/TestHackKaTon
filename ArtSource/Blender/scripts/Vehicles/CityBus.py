"""CityBus: 112번 간선(파랑) 저상 시내버스. 원점 = 차체 바닥 중앙, 정면 = -Y, 문 = 오른쪽(-X, Unity +X).

실행: K3D_ROOT=... K3D_CACHE=... blender -b --factory-startup --python CityBus.py
CB_FAST=1 이면 굽기/내보내기 없이 형태 미리보기만 한다.
"""
import bpy, bmesh, math, os, sys, subprocess
from mathutils import Vector, Matrix
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts')
import k3d

FAST = os.environ.get("CB_FAST") == "1"
A = "CityBus"
HERE = os.path.dirname(os.path.abspath(__file__))
TEXPY = os.path.join(HERE, "CityBus_tex.py")
VENV = os.path.abspath(os.path.join(HERE, "..", "..", "..", "_cache", "venv", "bin", "python"))
TDIR = os.path.join(k3d.ART, "Textures", A)

# ---------------------------------------------------------------- 치수 (m)
L, W = 10.84, 2.49            # 차체 (범퍼 제외) 길이·폭
HW = W / 2
YF, YB = -L / 2, L / 2        # 앞면 / 뒷면
ZB, ZR = 0.30, 2.98           # 차체 바닥 / 지붕
ZFL = 0.335                   # 실내 바닥 (저상)
TH = 0.035                    # 외판 두께
AXF, AXR = -3.0, 2.7          # 앞·뒤 차축
RW = 0.48                     # 바퀴 반지름 (275/70R22.5)
DF, DM, DH = -4.45, 0.90, 0.58  # 앞문·중문 중심, 개구부 반폭
DTOP = 2.62
KF = 0.088                    # 앞유리 기울기 dy/dz
yf = lambda z: YF + max(0.0, z - 1.12) * KF   # 앞면 y(z)
ZS = 2.02                     # 옆창 미닫이 경계 높이
WIN = [(-3.80, -2.47, 1.12), (-2.39, -1.06, 1.12), (-0.98, 0.25, 1.12),
       (1.56, 2.78, 1.34), (2.86, 4.06, 1.34), (4.14, 5.12, 1.34)]   # 양쪽 창 (y0, y1, 아래 z)
WIN_L = [(-5.03, -3.87, 1.12), (0.32, 1.48, 1.12)]                     # 왼쪽만 (운전석 창, 중문 맞은편)
WTOP = 2.45


# ---------------------------------------------------------------- 셰이더 그래프 도우미
class SG:
    """절차 머티리얼을 짧게 짜기 위한 래퍼. 결과는 bake 로 텍스처가 된다."""
    def __init__(s, name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, emission=None, strength=3.0, alpha=1.0):
        s.mt = k3d.mat(name, color, rough, metal, emission, strength, alpha)
        s.nt = s.mt.node_tree
        s.p = k3d.principled(s.mt)
        if not emission:   # Blender 5 기본 방출색이 흰색이라 굽기 때 몸 전체가 빛나지 않게 검정으로
            s.p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
        s._tc = s._geo = None

    def link(s, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            s.nt.links.new(v, sock)
        elif isinstance(v, (tuple, list)):
            sock.default_value = tuple(v) + ((1.0,) if len(v) == 3 and len(sock.default_value) == 4 else ())
        else:
            sock.default_value = v

    def node(s, t, **ins):
        n = s.nt.nodes.new(t)
        for k, v in ins.items():
            s.link(n.inputs[k], v)
        return n

    def P(s):
        s._tc = s._tc or s.nt.nodes.new('ShaderNodeTexCoord')
        return s._tc.outputs['Object']

    def N(s):
        s._geo = s._geo or s.nt.nodes.new('ShaderNodeNewGeometry')
        return s._geo.outputs['Normal']

    def xyz(s, v):
        n = s.node('ShaderNodeSeparateXYZ')
        s.link(n.inputs[0], v)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def m(s, op, a, b=0.0, c=None, clamp=False):
        n = s.nt.nodes.new('ShaderNodeMath')
        n.operation, n.use_clamp = op, clamp
        s.link(n.inputs[0], a)
        s.link(n.inputs[1], b)
        if c is not None:
            s.link(n.inputs[2], c)
        return n.outputs[0]

    def gt(s, a, b): return s.m('GREATER_THAN', a, b)
    def lt(s, a, b): return s.m('LESS_THAN', a, b)
    def mul(s, *a):
        r = a[0]
        for b in a[1:]:
            r = s.m('MULTIPLY', r, b)
        return r
    def add(s, a, b, clamp=False): return s.m('ADD', a, b, clamp=clamp)
    def mx(s, a, b): return s.m('MAXIMUM', a, b)
    def ab(s, a): return s.m('ABSOLUTE', a)

    def rng(s, v, a, b, c=0.0, d=1.0, smooth=True):
        """map range (clamp): v 가 a->b 일 때 c->d."""
        n = s.nt.nodes.new('ShaderNodeMapRange')
        if smooth:
            n.interpolation_type = 'SMOOTHSTEP'
        for k, x in (('Value', v), ('From Min', a), ('From Max', b), ('To Min', c), ('To Max', d)):
            s.link(n.inputs[k], x)
        return n.outputs[0]

    def vscale(s, v, sc):
        n = s.nt.nodes.new('ShaderNodeVectorMath')
        n.operation = 'MULTIPLY'
        s.link(n.inputs[0], v)
        n.inputs[1].default_value = sc
        return n.outputs[0]

    def noise(s, v, scale, detail=3.0, rough=0.55):
        n = s.node('ShaderNodeTexNoise', Scale=scale, Detail=detail, Roughness=rough)
        s.link(n.inputs['Vector'], v)
        return n.outputs['Factor']

    def ao(s, dist, inside=False, samples=8):
        n = s.nt.nodes.new('ShaderNodeAmbientOcclusion')
        n.inside, n.samples = inside, samples
        n.inputs['Distance'].default_value = dist
        return n.outputs['AO']

    def mix(s, f, a, b, blend='MIX'):
        n = s.nt.nodes.new('ShaderNodeMix')
        n.data_type, n.blend_type, n.clamp_factor = 'RGBA', blend, True
        for ident, v in (('Factor_Float', f), ('A_Color', a), ('B_Color', b)):
            s.link(next(i for i in n.inputs if i.identifier == ident), v)
        return next(o for o in n.outputs if o.identifier == 'Result_Color')

    def bright(s, c, f):
        n = s.node('ShaderNodeHueSaturation')
        s.link(n.inputs['Color'], c)
        s.link(n.inputs['Value'], f)
        return n.outputs[0]

    def out(s, color=None, rough=None, metal=None, height=None, bump=0.5, bump_dist=0.003):
        for k, v in (('Base Color', color), ('Roughness', rough), ('Metallic', metal)):
            if v is not None:
                s.link(s.p.inputs[k], v)
        if height is not None:
            b = s.node('ShaderNodeBump', Strength=bump, Distance=bump_dist)
            s.link(b.inputs['Height'], height)
            s.nt.links.new(b.outputs['Normal'], s.p.inputs['Normal'])
        return s.mt


def grime(g, col, rough, z_top=1.1, amount=1.0, ao_d=0.12):
    """공통 오염: 아래쪽 도로 먼지 + 틈새 때(AO) + 얼룩 노이즈."""
    P = g.P()
    _, _, z = g.xyz(P)
    low = g.rng(z, z_top, ZB - 0.05)
    blot = g.noise(g.vscale(P, (1.0, 1.0, 2.5)), 2.2, 4)
    cav = g.rng(g.ao(ao_d), 0.95, 0.35)
    d = g.add(g.mul(low, g.rng(blot, 0.35, 0.7, 0.35, 1.0), amount), g.mul(cav, 0.75), clamp=True)
    col = g.mix(g.mul(d, 0.8), col, (0.105, 0.088, 0.07))
    rough = g.add(rough, g.mul(d, 0.45), clamp=True)
    return col, rough, d


# ---------------------------------------------------------------- 머티리얼
def mat_paint():
    """차체 도장: 파랑 상단 / 흰 하단 / 검정 창띠 / 흰 지붕 + 먼지·빗물 자국·그을음·모서리 까짐."""
    g = SG("M_CityBus_Paint", rough=0.3)
    P = g.P()
    x, y, z = g.xyz(P)
    nx, ny, nz = g.xyz(g.N())
    ax = g.ab(x)
    side = g.gt(g.ab(nx), 0.7)
    zlo = g.m('MULTIPLY_ADD', g.gt(y, 1.52), 0.22, 1.07)
    band = g.mul(side, g.gt(z, zlo), g.lt(z, 2.495))
    fband = g.mul(g.lt(ny, -0.55), g.gt(z, 1.135), g.lt(z, 2.93), g.lt(ax, 1.035))
    rband = g.mul(g.gt(ny, 0.55), g.gt(z, 2.085), g.lt(z, 2.765), g.lt(ax, 0.935))
    black = g.mx(g.mx(band, fband), rband)
    roof = g.mx(g.mul(g.gt(nz, 0.55), g.gt(z, 2.7)), g.gt(z, 3.0))
    skirt = g.lt(z, 0.985)
    accent = g.mul(g.gt(z, 0.985), g.lt(z, 1.02))
    var = g.rng(g.noise(P, 1.3, 2), 0.3, 0.7, 0.93, 1.06)
    blue = g.bright((0.012, 0.10, 0.34), var)
    col = g.mix(skirt, blue, g.bright((0.70, 0.71, 0.72), var))
    col = g.mix(accent, col, (0.05, 0.33, 0.70))
    col = g.mix(roof, col, (0.66, 0.67, 0.67))
    col = g.mix(black, col, (0.009, 0.010, 0.012))
    rough = g.m('MULTIPLY_ADD', black, -0.14, 0.30)
    # 모서리 까짐 (아래쪽 위주)
    edge = g.rng(g.ao(0.025, inside=True, samples=8), 0.8, 0.45)
    chips = g.mul(edge, g.rng(g.noise(P, 18, 6), 0.55, 0.7), g.rng(z, 1.4, 0.5, 0.25, 1.0), g.m('SUBTRACT', 1, black))
    col = g.mix(chips, col, (0.30, 0.30, 0.29))
    # 빗물 자국 (창 아래·지붕 아래로 흐르는 세로 줄)
    st = g.rng(g.noise(g.vscale(P, (24, 24, 0.7)), 1.0, 3), 0.52, 0.75)
    smask = g.mx(g.mul(g.rng(z, zlo, g.m('SUBTRACT', zlo, 0.55)), g.lt(z, zlo)),
                 g.mul(g.rng(z, 2.9, 2.5), g.gt(z, 2.495)))
    streak = g.mul(st, smask, side, 0.55)
    # 바퀴 근처 흙탕 + 지붕 먼지
    wheel = g.mx(g.rng(g.ab(g.m('SUBTRACT', y, AXF)), 1.4, 0.2), g.rng(g.ab(g.m('SUBTRACT', y, AXR)), 1.6, 0.2))
    col, rough, d = grime(g, col, rough, z_top=1.25, amount=g.m('MULTIPLY_ADD', wheel, 0.5, 0.7))
    col = g.mix(streak, col, (0.12, 0.105, 0.09))
    col = g.mix(g.mul(roof, g.rng(g.noise(P, 3, 4), 0.3, 0.8, 0.15, 0.55)), col, (0.30, 0.27, 0.22))
    # CNG 배기 그을음 (지붕 뒤쪽)
    soot = g.mul(g.rng(y, 4.0, 5.45), g.gt(z, 2.55), g.rng(g.noise(P, 4, 4), 0.3, 0.7, 0.4, 1.0))
    col = g.mix(g.mul(soot, 0.75), col, (0.025, 0.024, 0.022))
    rough = g.add(rough, g.mul(g.add(streak, soot), 0.35), clamp=True)
    # 패널 이음매 (치마 세로줄, 지붕 가로줄)
    seam_y = g.rng(g.ab(g.m('SUBTRACT', g.m('FRACT', g.m('DIVIDE', g.add(y, 0.37), 1.18)), 0.5)), 0.4955, 0.4995)
    seam_r = g.rng(g.ab(g.m('SUBTRACT', g.m('FRACT', g.m('DIVIDE', g.add(y, 0.2), 1.45)), 0.5)), 0.4965, 0.4995)
    seam_z = g.rng(g.ab(g.m('SUBTRACT', z, 0.985)), 0.003, 0.0005)
    seam = g.mx(g.mx(g.mul(seam_y, skirt, side), g.mul(seam_r, roof)), g.mul(seam_z, g.m('SUBTRACT', 1, black)))
    col = g.mix(g.mul(seam, 0.6), col, (0.03, 0.03, 0.03))
    return g.out(col, rough, 0.0, height=g.m('SUBTRACT', 0, seam), bump=0.8, bump_dist=0.002)


def mat_flat(name, color, rough, metal=0.0, wear=0.0, dirt=1.0, scratch=0.0, emission=None, strength=3.0):
    """단색 + 얼룩/때/긁힘 공통 처리."""
    g = SG(name, color, rough, metal, emission, strength)
    P = g.P()
    var = g.rng(g.noise(P, 6, 3), 0.3, 0.7, 0.9, 1.08)
    col = g.bright(color, var)
    r = g.m('MULTIPLY', var, rough)
    if scratch:
        sc = g.rng(g.noise(g.vscale(P, (40, 3, 40)), 2.0, 6), 0.62, 0.7, 0, scratch)
        col = g.mix(sc, col, (0.12, 0.12, 0.12) if max(color) < 0.1 else (0.4, 0.4, 0.4))
        r = g.add(r, g.mul(sc, 0.25), clamp=True)
    if wear:
        e = g.rng(g.ao(0.02, inside=True, samples=6), 0.8, 0.45, 0, wear)
        col = g.mix(e, col, (0.35, 0.35, 0.34))
    if dirt:
        col, r, _ = grime(g, col, r, amount=dirt)
    return g.out(col, r, metal)


def materials():
    M = {}
    M['paint'] = mat_paint()
    M['under'] = mat_flat("M_CityBus_Under", (0.022, 0.021, 0.02), 0.85, dirt=1.4)
    M['rubber'] = mat_flat("M_CityBus_Rubber", (0.014, 0.014, 0.014), 0.75, dirt=0.6)
    M['plastic'] = mat_flat("M_CityBus_Plastic", (0.028, 0.028, 0.03), 0.5, wear=0.5, scratch=0.8)
    M['chrome'] = mat_flat("M_CityBus_Chrome", (0.85, 0.85, 0.85), 0.08, metal=1.0, dirt=0.3)
    M['alu'] = mat_flat("M_CityBus_Alu", (0.55, 0.56, 0.58), 0.35, metal=1.0, scratch=0.5, dirt=0.6)
    M['lampw'] = mat_flat("M_CityBus_LampW", (0.9, 0.9, 0.88), 0.1, dirt=0, emission=(1.0, 0.96, 0.88))
    M['lampr'] = mat_flat("M_CityBus_LampR", (0.45, 0.015, 0.01), 0.12, dirt=0.3, emission=(0.32, 0.008, 0.004))
    M['lampa'] = mat_flat("M_CityBus_LampA", (0.85, 0.32, 0.02), 0.12, dirt=0.3)
    M['clear'] = mat_flat("M_CityBus_LensClear", (0.55, 0.57, 0.6), 0.05, metal=0.8, dirt=0.2)
    M['yellow'] = mat_flat("M_CityBus_Yellow", (0.75, 0.48, 0.02), 0.55, wear=0.8, scratch=0.6)
    M['grille'] = mat_flat("M_CityBus_Grille", (0.018, 0.018, 0.02), 0.6, dirt=1.2)
    M['rim'] = M['rubber']
    # 실내
    M['wall'] = mat_flat("M_CityBus_InWall", (0.42, 0.41, 0.39), 0.6, dirt=0.4)
    M['ceil'] = mat_flat("M_CityBus_InCeil", (0.58, 0.58, 0.56), 0.7, dirt=0.2)
    M['floor'] = mat_floor()
    M['seat'] = mat_flat("M_CityBus_Seat", (0.02, 0.075, 0.21), 0.35, scratch=0.4, dirt=0.3)
    M['seatp'] = mat_flat("M_CityBus_SeatPrio", (0.62, 0.20, 0.02), 0.35, scratch=0.4, dirt=0.3)
    M['pole'] = mat_flat("M_CityBus_Pole", (0.72, 0.47, 0.02), 0.32, wear=0.6, dirt=0.2)
    M['handle'] = mat_flat("M_CityBus_Handle", (0.68, 0.68, 0.66), 0.4, dirt=0.2)
    M['dash'] = mat_flat("M_CityBus_Dash", (0.02, 0.02, 0.022), 0.5, scratch=0.5, dirt=0.3)
    M['light'] = mat_flat("M_CityBus_InLight", (0.9, 0.9, 0.9), 0.3, dirt=0, emission=(1.0, 1.0, 0.95))
    M['screen'] = mat_flat("M_CityBus_Screen", (0.02, 0.2, 0.08), 0.2, dirt=0, emission=(0.05, 0.45, 0.16))
    M['red'] = mat_flat("M_CityBus_Red", (0.6, 0.03, 0.02), 0.35, dirt=0.2)
    # 유리·동적 (굽지 않음)
    M['glass'] = k3d.flag(k3d.mat("M_Glass_CityBus", (0.035, 0.045, 0.05), 0.04, 0.0, alpha=0.58), double_sided=True)
    M['glassc'] = k3d.flag(k3d.mat("M_Glass_CityBus_Clear", (0.10, 0.12, 0.12), 0.03, 0.0, alpha=0.2), double_sided=True)
    gd = k3d.load_image(os.path.join(TDIR, "T_CityBus_GlassDirt.png"), "T_CityBus_GlassDirt")
    for k, a in (('glass', 0.62), ('glassc', 0.24)):   # 먼지·물자국·손자국: 텍스처 알파(0.8~1) x 머티리얼 알파
        m, p = M[k], k3d.principled(M[k])
        p.inputs['Emission Color'].default_value = (0, 0, 0, 1)
        n = k3d.image_node(m, gd, p.inputs['Base Color'])
        mul = m.node_tree.nodes.new('ShaderNodeMath')
        mul.operation, mul.inputs[1].default_value = 'MULTIPLY', a
        m.node_tree.links.new(n.outputs['Alpha'], mul.inputs[0])
        m.node_tree.links.new(mul.outputs[0], p.inputs['Alpha'])
        p.inputs['Alpha'].default_value = a
    return M


def mat_floor():
    """실내 바닥: 회색 미끄럼방지 비닐 (점 무늬 + 발자국 때)."""
    g = SG("M_CityBus_Floor", (0.07, 0.075, 0.08), 0.7)
    P = g.P()
    spk = g.rng(g.noise(P, 220, 1), 0.6, 0.7, 0, 1)
    col = g.mix(g.mul(spk, 0.5), (0.07, 0.075, 0.08), (0.2, 0.2, 0.19))
    col, r, _ = grime(g, col, 0.7, z_top=0.0, amount=0.0)
    wear = g.rng(g.noise(P, 1.5, 3), 0.45, 0.75)
    col = g.mix(g.mul(wear, 0.5), col, (0.11, 0.1, 0.085))
    return g.out(col, r, height=spk, bump=0.3, bump_dist=0.001)


def mat_tire():
    """타이어: 트레드 홈·사이프(범프) + 옆면 먼지."""
    g = SG("M_CityBus_Tire", (0.02, 0.02, 0.02), 0.85)
    P = g.P()
    x, y, z = g.xyz(P)
    r = g.m('SQRT', g.add(g.mul(y, y), g.mul(z, z)))
    th = g.m('ARCTAN2', z, y)
    tread = g.gt(r, 0.462)
    lx = g.ab(g.m('SUBTRACT', g.m('FRACT', g.m('DIVIDE', g.add(x, 0.3), 0.07)), 0.5))
    groove = g.mul(tread, g.rng(lx, 0.43, 0.47))
    sipe = g.mul(tread, g.rng(g.ab(g.m('SUBTRACT', g.m('FRACT', g.m('MULTIPLY', th, 72 / (2 * math.pi))), 0.5)), 0.38, 0.45))
    h = g.m('SUBTRACT', 0, g.mx(groove, g.mul(sipe, 0.6)))
    dust = g.mul(g.m('SUBTRACT', 1, tread), g.rng(g.noise(P, 8, 4), 0.35, 0.75, 0.05, 0.25))
    col = g.mix(dust, (0.022, 0.022, 0.022), (0.16, 0.14, 0.12))
    col = g.mix(g.mul(tread, 0.25), col, (0.05, 0.048, 0.045))
    return g.out(col, g.m('MULTIPLY_ADD', dust, 0.1, 0.82), height=h, bump=0.9, bump_dist=0.006)


def mat_rim():
    """강철 휠: 은색 도장 + 손구멍(어두운 타원) + 브레이크 분진."""
    g = SG("M_CityBus_Rim", (0.5, 0.51, 0.52), 0.35, 0.5)
    P = g.P()
    x, y, z = g.xyz(P)
    r = g.m('SQRT', g.add(g.mul(y, y), g.mul(z, z)))
    th = g.m('ARCTAN2', z, y)
    ring = g.mul(g.gt(r, 0.175), g.lt(r, 0.225))
    seg = g.lt(g.ab(g.m('SUBTRACT', g.m('FRACT', g.m('MULTIPLY', th, 10 / (2 * math.pi))), 0.5)), 0.22)
    hole = g.mul(ring, seg)
    dust = g.rng(r, 0.3, 0.08, 0.15, 0.75)
    col = g.mix(g.mul(dust, g.rng(g.noise(P, 14, 4), 0.3, 0.7, 0.4, 1.0)), (0.5, 0.51, 0.52), (0.16, 0.10, 0.06))
    col = g.mix(hole, col, (0.004, 0.004, 0.004))
    col, rough, _ = grime(g, col, 0.35, z_top=0.4, amount=0.6, ao_d=0.05)
    return g.out(col, g.m('MULTIPLY_ADD', hole, 0.5, rough), g.m('MULTIPLY_ADD', hole, -0.5, 0.5),
                 height=g.m('SUBTRACT', 0, hole), bump=1.0, bump_dist=0.02)


# ---------------------------------------------------------------- 메시 빌더
class MB:
    """여러 조각을 bmesh 하나로 모은다 (조각마다 베벨 후 머티리얼 슬롯 지정)."""
    def __init__(s, name, maxseg=3):
        s.name, s.bm, s.mats, s.maxseg = name, bmesh.new(), [], maxseg
        s.tmp = bpy.data.meshes.new("_tmp")

    def slot(s, m):
        if m not in s.mats:
            s.mats.append(m)
        return s.mats.index(m)

    def add(s, bm, m, mtx=None):
        if mtx is not None:
            bmesh.ops.transform(bm, matrix=mtx, verts=bm.verts)
        i = s.slot(m)
        for f in bm.faces:
            f.material_index = i
        bm.to_mesh(s.tmp)
        bm.free()
        s.bm.from_mesh(s.tmp)

    def box(s, size, loc, m, bev=0.008, seg=2, rot=(0, 0, 0), only=None, r=0.0):
        """size=(x,y,z) 박스. r>0 이면 세로 모서리를 반지름 r 로 둥글게(평면도), bev>0 이면 나머지 모서리 베벨.
        only='x'|'y'|'z' 면 그 축에 평행한 모서리만 베벨."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        if r > 0:
            es = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
            bmesh.ops.bevel(bm, geom=es, offset=r, segments=4, profile=0.5, affect='EDGES', clamp_overlap=True)
        if bev > 0:
            es = bm.edges[:]
            if r > 0:
                es = [e for e in es if len(e.link_faces) == 2 and e.calc_face_angle(0) > 1.0]
            if only:
                k = 'xyz'.index(only)
                es = [e for e in es if abs((e.verts[0].co - e.verts[1].co)[k]) > 1e-6]
            # 1cm 이하 베벨은 2단이 화면에서 안 보이므로 1단 (삼각형 예산)
            seg = min(1 if bev <= 0.0105 else seg, s.maxseg)
            bmesh.ops.bevel(bm, geom=es, offset=min(bev, min(size) * 0.45), offset_type='OFFSET',
                            segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
        s.add(bm, m, Matrix.Translation(loc) @ _rot(rot))

    def cyl(s, r, depth, loc, m, axis='Z', seg=16, bev=0.0, r2=None, rot=None):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=depth)
        if bev > 0:
            es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 1.0]
            bmesh.ops.bevel(bm, geom=es, offset=bev, segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
        R = {'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi / 2, 4, 'X'), 'Z': Matrix()}[axis]
        s.add(bm, m, Matrix.Translation(loc) @ (_rot(rot) if rot else Matrix()) @ R)

    def tube(s, pts, r, m, seg=8, closed=False, smooth=False):
        """점 목록을 따라가는 관 (손잡이 봉, 거울 팔). smooth=True 면 NURBS 곡선."""
        cu = bpy.data.curves.new("_tube", 'CURVE')
        cu.dimensions, cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = '3D', r, max(0, seg // 4 - 1), True
        sp = cu.splines.new('NURBS' if smooth else 'POLY')
        if smooth:
            sp.order_u, sp.use_endpoint_u, sp.resolution_u = 3, True, 5
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (*c, 1)
        sp.use_cyclic_u = closed
        ob = bpy.data.objects.new("_tube", cu)
        bpy.context.scene.collection.objects.link(ob)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bpy.data.meshes.remove(me)
        s.add(bm, m)

    def quad(s, c, right, up, w, h, m, uv=(0, 0, 1, 1)):
        """c 중심, right/up 방향 사각형 1장 (앞면 = right x up). uv=(u0,v0,u1,v1)."""
        c, right, up = Vector(c), Vector(right).normalized(), Vector(up).normalized()
        bm = bmesh.new()
        lay = bm.loops.layers.uv.new("UVMap")
        vs = [bm.verts.new(c + right * (sx * w / 2) + up * (sy * h / 2)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        f = bm.faces.new(vs)
        u0, v0, u1, v1 = uv
        for l, t in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            l[lay].uv = t
        s.add(bm, m)

    def obj(s, parent=None, loc=(0, 0, 0)):
        me = bpy.data.meshes.new(s.name)
        s.bm.to_mesh(me)
        s.bm.free()
        bpy.data.meshes.remove(s.tmp)
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        for m in s.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(s.name, me)
        bpy.context.scene.collection.objects.link(ob)
        if loc != (0, 0, 0):   # 원점을 피벗으로: 메시는 월드 좌표로 만들었으니 반대로 옮긴다
            me.transform(Matrix.Translation(-Vector(loc)))
            ob.location = loc
        if parent:
            ob.parent = parent
        return ob


def _rot(r):
    return (Matrix.Rotation(r[2], 4, 'Z') @ Matrix.Rotation(r[1], 4, 'Y') @ Matrix.Rotation(r[0], 4, 'X'))


def finish(ob, angle=50, weighted=True):
    """스무스 + 각도 샤프 + 가중 노멀."""
    k3d.smooth(ob, angle)
    if weighted:
        md = ob.modifiers.new("wn", 'WEIGHTED_NORMAL')
        md.keep_sharp, md.weight, md.mode = True, 50, 'FACE_AREA'
    return ob


# ---------------------------------------------------------------- 차체 외판 (형태 -> 베벨 -> 휠하우스 -> 두께 -> 창·문 구멍)
def bez(p0, c, p1, n):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in [i / n for i in range(n + 1)]]


def cutter(coll, size, loc, rot=(0, 0, 0), r=0.0, axis='x', top_only=False, mat_index=2):
    """불리언 커터 박스. r>0 이면 axis 에 평행한 모서리를 둥글게 (창 모서리)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if r > 0:
        k = 'xyz'.index(axis)
        es = [e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co)[k]) > 1e-6]
        if top_only:
            es = [e for e in es if e.verts[0].co.z > 0]
        bmesh.ops.bevel(bm, geom=es, offset=r, segments=3, profile=0.5, affect='EDGES', clamp_overlap=True)
    for f in bm.faces:
        f.material_index = mat_index
    me = bpy.data.meshes.new("_cut")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("_cut", me)
    coll.objects.link(ob)
    ob.matrix_world = Matrix.Translation(loc) @ _rot(rot)
    ob.hide_render = True
    return ob


WELLS = ((AXF, 0.40), (AXR, 0.66))   # (차축 y, 휠하우스 깊이): 앞 |x|>=0.845, 뒤 |x|>=0.585 가 바퀴 공간


def well_cutters(grow=0.0):
    """휠하우스 커터 (반지름 0.545 원기둥). grow 만큼 키운 것은 실내 조각을 바퀴 공간에서 깎는 데 쓴다."""
    coll = bpy.data.collections.new("_wells")
    bpy.context.scene.collection.children.link(coll)
    for ya, depth in WELLS:
        ln = depth + 0.3 + grow
        for s in (-1, 1):
            c = cutter(coll, (ln, 1, 1), (s * (HW + 0.3 - ln / 2), ya, RW), mat_index=0)
            bm = bmesh.new()   # 원기둥으로 교체
            bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=0.545 + grow, radius2=0.545 + grow, depth=ln)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'), verts=bm.verts)
            bm.to_mesh(c.data)
            bm.free()
    return coll


def drop(coll):
    for o in list(coll.objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(coll)


def shell(M):
    prof = [(YF, ZB), (YF, 1.12)]
    prof += bez((yf(2.66), 2.66), (yf(ZR), ZR), (YF + 0.42, ZR), 8)
    prof += bez((YB - 0.26, ZR), (YB, ZR), (YB, ZR - 0.26), 6)
    prof += [(YB, ZB)]
    bm = bmesh.new()
    Lv = [bm.verts.new((-HW, y, z)) for y, z in prof]
    Rv = [bm.verts.new((HW, y, z)) for y, z in prof]
    bm.faces.new(Lv)
    bm.faces.new(Rv[::-1])
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((Lv[i], Lv[j], Rv[j], Rv[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bw = bm.edges.layers.float.get('bevel_weight_edge') or bm.edges.layers.float.new('bevel_weight_edge')
    for e in bm.edges:
        a, b = e.verts[0].co, e.verts[1].co
        yc, zc = (a.y + b.y) / 2, (a.z + b.z) / 2
        if abs(a.x - b.x) < 1e-6:                      # 옆면 윤곽선
            if abs(a.z - ZB) < 1e-4 and abs(b.z - ZB) < 1e-4:
                w = 0.12
            elif yc < -4.9:
                w = 0.7 + 0.3 * min(1, max(0, (-5.0 - yc) / 0.28)) if zc > 2.6 else 1.0
            elif yc > 5.1:
                w = 0.7 + 0.1 * min(1, max(0, (yc - 5.16) / 0.26)) if zc > 2.6 else 0.8
            else:
                w = 0.7
        else:                                           # 폭 방향 모서리
            w = 0.2 if abs(zc - ZB) < 1e-4 else 0.0
        e[bw] = w
    me = bpy.data.meshes.new(A + "_Body")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M['paint'])   # 0 바깥
    me.materials.append(M['wall'])    # 1 안쪽 (solidify offset)
    me.materials.append(M['rim'])     # 2 구멍 테두리 (커터)
    ob = bpy.data.objects.new(A + "_Body", me)
    bpy.context.scene.collection.objects.link(ob)
    bv = ob.modifiers.new("bevel", 'BEVEL')
    bv.limit_method, bv.width, bv.segments, bv.use_clamp_overlap = 'WEIGHT', 0.22, 5, True

    sc = bpy.context.scene.collection
    wells = well_cutters()
    b1 = ob.modifiers.new("wells", 'BOOLEAN')
    b1.operation, b1.solver, b1.operand_type, b1.collection = 'DIFFERENCE', 'EXACT', 'COLLECTION', wells
    sd = ob.modifiers.new("thick", 'SOLIDIFY')
    sd.thickness, sd.offset, sd.material_offset, sd.use_even_offset = TH, -1, 1, True

    holes = bpy.data.collections.new("_holes")
    sc.children.link(holes)
    for y0, y1, z0 in WIN:                       # 양쪽 창 (관통)
        cutter(holes, (3.2, y1 - y0, WTOP - z0), (0, (y0 + y1) / 2, (z0 + WTOP) / 2), r=0.045)
    for y0, y1, z0 in WIN_L:                     # 왼쪽만
        cutter(holes, (0.8, y1 - y0, WTOP - z0), (HW, (y0 + y1) / 2, (z0 + WTOP) / 2), r=0.045)
    for c in (DF, DM):                           # 문 (오른쪽)
        cutter(holes, (0.8, 2 * DH, DTOP - ZFL), (-HW, c, (ZFL + DTOP) / 2), r=0.06, top_only=True)
    a = math.atan(KF)
    for z0, z1 in ((1.18, 2.52), (2.58, 2.88)):  # 앞유리, 앞 행선지 창
        zc = (z0 + z1) / 2
        cutter(holes, (2.0, 0.5, (z1 - z0) / math.cos(a)), (0, yf(zc), zc), rot=(-a, 0, 0), r=0.06, axis='y')
    cutter(holes, (1.76, 0.6, 0.58), (0, YB, 2.41), r=0.06, axis='y')   # 뒷창
    b2 = ob.modifiers.new("holes", 'BOOLEAN')
    b2.operation, b2.solver, b2.operand_type, b2.collection = 'DIFFERENCE', 'EXACT', 'COLLECTION', holes
    k3d.apply_all(ob)
    drop(wells)
    drop(holes)

    # 안쪽 면(슬롯 1)은 실내 메시로 분리, 바깥 면은 위치로 도장/하부 분류
    inner = ob.copy()
    inner.data = ob.data.copy()
    inner.name = inner.data.name = A + "_InnerShell"
    sc.objects.link(inner)
    for o, keep_inner in ((ob, False), (inner, True)):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        dead = [f for f in bm.faces if (f.material_index == 1) != keep_inner]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(o.data)
        bm.free()
    o = ob.data
    under = len(o.materials)
    o.materials.append(M['under'])
    for f in o.polygons:
        c, n = f.center, f.normal
        if f.material_index == 0 and c.z < 1.06 and abs(c.y) < 5.3 and not (abs(c.x) > HW - 0.01 and abs(n.x) > 0.7):
            f.material_index = under
    o = inner.data
    o.materials.append(M['floor'])
    o.materials.append(M['ceil'])
    for f in o.polygons:
        if f.normal.z > 0.7 and f.center.z < 0.7:
            f.material_index = 3
        elif f.normal.z < -0.7 and f.center.z > 2.5:
            f.material_index = 4
    return ob, inner


# ---------------------------------------------------------------- 외장 디테일
def exterior(M):
    b = MB(A + "_Trim")   # 차체와 따로 굽는다 (작은 조각 섬이 많아 차체 옆면 해상도를 뺏지 않게)
    # 범퍼 (앞/뒤)
    for y in (YF - 0.03, YB + 0.03):
        b.box((2.44, 0.22, 0.30), (0, y, 0.43), M['plastic'], bev=0.03, seg=2, r=0.13)
        b.box((2.30, 0.03, 0.035), (0, y + (-0.1 if y < 0 else 0.1), 0.50), M['rubber'], bev=0.01)   # 범퍼 고무띠
        b.box((0.37, 0.02, 0.20), (0, y + (-0.105 if y < 0 else 0.105), 0.38), M['plastic'], bev=0.01)  # 번호판 받침
    # 전조등 (앞 아래 모서리)
    for s in (-1, 1):
        x0 = s * 0.765
        b.box((0.44, 0.06, 0.19), (x0, YF - 0.01, 0.72), M['plastic'], bev=0.015, seg=2, r=0.05)
        b.cyl(0.058, 0.03, (s * 0.63, YF - 0.035, 0.71), M['lampw'], axis='Y', seg=20, bev=0.006)
        b.cyl(0.058, 0.03, (s * 0.78, YF - 0.035, 0.71), M['clear'], axis='Y', seg=20, bev=0.006)
        b.cyl(0.03, 0.035, (s * 0.78, YF - 0.04, 0.71), M['lampw'], axis='Y', seg=12)
        b.box((0.075, 0.03, 0.13), (s * 0.925, YF - 0.035, 0.72), M['lampa'], bev=0.01)
        b.box((0.38, 0.03, 0.016), (s * 0.73, YF - 0.035, 0.795), M['lampw'], bev=0.004)        # LED 주간등
        b.cyl(0.04, 0.03, (s * 0.80, YF - 0.035, 0.50), M['clear'], axis='Y', seg=14, bev=0.005)  # 안개등 (범퍼)
        # 차폭등 (지붕 앞/뒤 모서리)
        b.box((0.09, 0.03, 0.04), (s * 0.85, yf(2.93) - 0.005, 2.93), M['lampa'], bev=0.01, rot=(-0.09, 0, 0))
        b.box((0.09, 0.03, 0.04), (s * 0.80, YB + 0.005, 2.80), M['lampr'], bev=0.01)
    # 앞 아래 그릴 (전조등 사이: 검정 판 + 기울인 가로 날개 5개)
    b.box((1.0, 0.03, 0.21), (0, YF - 0.006, 0.715), M['grille'], bev=0.01)
    for i in range(5):
        b.box((0.94, 0.028, 0.014), (0, YF - 0.026, 0.635 + i * 0.04), M['plastic'], bev=0.004, rot=(-0.45, 0, 0))
    # 앞 엠블럼 + 견인고리 덮개
    b.cyl(0.075, 0.02, (0, YF - 0.01, 0.95), M['chrome'], axis='Y', seg=24, bev=0.006)
    b.box((0.16, 0.02, 0.08), (0.45, YF - 0.13, 0.38), M['plastic'], bev=0.01)
    # 와이퍼 2개 (아래 대기 위치)
    nf = Vector((0, -1, KF)).normalized()
    up = Vector((0, KF, 1)).normalized()
    for px in (-0.70, 0.15):
        c0 = Vector((px, yf(1.22), 1.22)) + nf * 0.03
        b.cyl(0.025, 0.04, c0 - nf * 0.01, M['plastic'], axis='Y', seg=10)
        b.box((0.82, 0.014, 0.022), c0 + Vector((0.41, 0, 0.015)) + nf * 0.01, M['plastic'], bev=0.004, rot=(-math.atan(KF), 0, 0.04))
        b.box((0.88, 0.01, 0.03), c0 + Vector((0.44, 0, 0.045)) + nf * 0.005, M['rubber'], bev=0.003, rot=(-math.atan(KF), 0, 0.04))
    # 토끼귀 사이드미러 (지붕 앞 모서리에서 앞·아래로)
    for s in (-1, 1):
        pts = [(s * 1.02, -5.02, 2.95), (s * 1.18, -5.32, 2.93), (s * 1.34, -5.58, 2.84), (s * 1.42, -5.74, 2.66),
               (s * 1.44, -5.78, 2.46)]
        b.tube(pts, 0.022, M['plastic'], seg=8, smooth=True)
        b.box((0.12, 0.10, 0.06), (s * 1.02, -5.0, 2.955), M['plastic'], bev=0.02)        # 지붕 받침
        b.box((0.27, 0.08, 0.44), (s * 1.45, -5.79, 2.22), M['plastic'], bev=0.025, seg=2, r=0.035)  # 거울 몸통
        b.box((0.23, 0.01, 0.40), (s * 1.45, -5.745, 2.22), M['chrome'], bev=0.01)          # 거울면 (운전석 쪽 +Y)
        b.box((0.18, 0.07, 0.15), (s * 1.42, -5.78, 1.93), M['plastic'], bev=0.03, seg=3)   # 보조(볼록)거울
        b.box((0.15, 0.01, 0.12), (s * 1.42, -5.744, 1.93), M['chrome'], bev=0.008)
        b.cyl(0.015, 0.06, (s * 1.44, -5.78, 2.03), M['plastic'], seg=8)
    # 지붕: CNG 용기 덮개 + 에어컨 + 비상 해치 + 배기구
    b.box((1.96, 4.0, 0.26), (0, -1.6, ZR + 0.11), M['paint'], bev=0.09, seg=3, r=0.3)
    b.box((1.80, 2.4, 0.22), (0, 2.45, ZR + 0.09), M['paint'], bev=0.08, seg=3, r=0.25)
    for yy in (2.0, 2.9):
        b.cyl(0.30, 0.03, (0, yy, ZR + 0.205), M['grille'], seg=28, bev=0.008)
        b.cyl(0.07, 0.04, (0, yy, ZR + 0.215), M['plastic'], seg=16)
    for i in range(7):                       # CNG 덮개 옆 루버
        for s in (-1, 1):
            b.box((0.02, 0.32, 0.03), (s * 0.985, -3.2 + i * 0.55, ZR + 0.08), M['grille'], bev=0.005)
    for yy in (-4.3, 4.35):
        b.box((0.62, 0.62, 0.05), (0, yy, ZR + 0.015), M['plastic'], bev=0.02)
    b.box((0.16, 0.22, 0.10), (0.75, 4.95, ZR + 0.04), M['alu'], bev=0.02)
    b.cyl(0.04, 0.12, (0.75, 5.0, ZR + 0.13), M['grille'], seg=12)
    # 뒷면: 엔진 점검문 + 루버 + 후미등 + 번호판 자리
    b.box((1.62, 0.02, 1.05), (0, YB + 0.005, 1.16), M['paint'], bev=0.012)
    for i in range(7):
        b.box((1.34, 0.03, 0.022), (0, YB + 0.02, 1.38 + i * 0.045), M['grille'], bev=0.005, rot=(0.35, 0, 0))
    b.box((1.38, 0.012, 0.34), (0, YB + 0.008, 1.515), M['grille'], bev=0.004)
    for s in (-1, 1):
        b.box((0.07, 0.03, 0.05), (s * 0.6, YB + 0.025, 0.66), M['alu'], bev=0.01)   # 손잡이
        b.box((0.17, 0.05, 0.86), (s * 1.02, YB, 1.02), M['plastic'], bev=0.025)
        b.box((0.13, 0.03, 0.30), (s * 1.02, YB + 0.025, 1.24), M['lampr'], bev=0.01)
        b.box((0.13, 0.03, 0.17), (s * 1.02, YB + 0.025, 0.98), M['lampa'], bev=0.01)
        b.box((0.13, 0.03, 0.12), (s * 1.02, YB + 0.025, 0.77), M['clear'], bev=0.01)
        b.box((0.13, 0.03, 0.06), (s * 1.02, YB + 0.025, 0.65), M['lampr'], bev=0.008)
    # 옆: 차폭 표시등, 흙받이, 문 고무테·발판 노란선, 광고틀, 왼쪽 뒤 라디에이터 그릴
    for s in (-1, 1):
        for yy in (-1.95, -0.3, 1.95, 3.7, 5.05):
            if s < 0 and DM - DH < yy < DM + DH:
                continue
            b.box((0.02, 0.075, 0.035), (s * (HW + 0.004), yy, 0.35), M['lampa'], bev=0.006)
        b.box((0.55, 0.014, 0.40), (s * 0.92, AXR + 0.57, 0.30), M['rubber'], bev=0.006)
        b.box((0.30, 0.014, 0.30), (s * 1.06, AXF + 0.55, 0.35), M['rubber'], bev=0.006)
    for c in (DF, DM):
        for dy in (-DH - 0.018, DH + 0.018):
            b.box((0.016, 0.036, DTOP - ZFL), (-HW - 0.002, c + dy, (ZFL + DTOP) / 2), M['rubber'], bev=0.006)
        b.box((0.016, 2 * DH + 0.07, 0.036), (-HW - 0.002, c, DTOP + 0.018), M['rubber'], bev=0.006)
        b.box((0.05, 2 * DH - 0.02, 0.012), (-HW + 0.03, c, ZFL + 0.004), M['yellow'], bev=0.003)
        b.box((0.03, 2 * DH, 0.05), (-HW - 0.012, c, ZB + 0.01), M['alu'], bev=0.008)       # 문턱 보호판
    for s, y0, y1 in ((-1, -2.30, 0.10), (1, -1.60, 0.80)):   # 광고틀 (알루미늄 테)
        yc, w, zc, h = (y0 + y1) / 2, y1 - y0, 0.71, 0.60
        x = s * (HW + 0.006)
        for dz in (-h / 2 - 0.015, h / 2 + 0.015):
            b.box((0.014, w + 0.06, 0.03), (x, yc, zc + dz), M['alu'], bev=0.006)
        for dy in (-w / 2 - 0.015, w / 2 + 0.015):
            b.box((0.014, 0.03, h + 0.06), (x, yc + dy, zc), M['alu'], bev=0.006)
    b.box((0.012, 1.35, 0.55), (HW + 0.003, 4.30, 0.82), M['grille'], bev=0.006)
    for i in range(9):
        b.box((0.03, 1.28, 0.02), (HW + 0.01, 4.30, 0.59 + i * 0.058), M['plastic'], bev=0.004, rot=(0, 0.5, 0))   # 긴 축(Y) 기준으로 기울인 날개
    # 오른쪽 CNG 충전구 덮개
    b.box((0.012, 0.36, 0.30), (-HW - 0.003, 3.45, 0.66), M['paint'], bev=0.01)
    b.box((0.02, 0.05, 0.02), (-HW - 0.01, 3.30, 0.66), M['alu'], bev=0.005)
    # 창틀: 미닫이 가로대 + 위 칸 세로대 (검정 알루미늄)
    for y0, y1, z0 in WIN + WIN_L:
        sides = (1,) if (y0, y1, z0) in WIN_L else (-1, 1)
        zs = ZS + (0.06 if z0 > 1.2 else 0.0)
        for s in sides:
            x = s * (HW - 0.02)
            b.box((0.03, y1 - y0, 0.035), (x, (y0 + y1) / 2, zs), M['rubber'], bev=0.006)
            if not (s < 0 and y0 == WIN[0][0]):
                b.box((0.03, 0.03, WTOP - zs), (x, (y0 + y1) / 2, (zs + WTOP) / 2), M['rubber'], bev=0.006)
    # 앞 행선지 표지 함 (유리 뒤 검정 상자)
    b.box((1.85, 0.12, 0.36), (0, yf(2.73) + 0.12, 2.73), M['plastic'], bev=0.01, rot=(-math.atan(KF), 0, 0))
    b.box((1.7, 0.10, 0.06), (0, yf(2.55) + 0.06, 2.55), M['plastic'], bev=0.01, rot=(-math.atan(KF), 0, 0))
    b.box((0.06, 1.26, 0.30), (-HW + 0.10, -3.135, 2.29), M['plastic'], bev=0.01)       # 옆 표지 함
    b.box((1.04, 0.06, 0.26), (0, YB - 0.10, 2.49), M['plastic'], bev=0.01)               # 뒤 표지 함
    return b.obj()


# ---------------------------------------------------------------- 유리
def glass(M):
    b = MB(A + "_Glass")
    for y0, y1, z0 in WIN + WIN_L:
        sides = (1,) if (y0, y1, z0) in WIN_L else (-1, 1)
        zs = ZS + (0.06 if z0 > 1.2 else 0.0)
        yc, w = (y0 + y1) / 2, y1 - y0 - 0.01
        for s in sides:
            b.quad((s * (HW - 0.014), yc, (z0 + zs) / 2), (0, s, 0), (0, 0, 1), w, zs - z0, M['glass'])
            if s < 0 and y0 == WIN[0][0]:              # 옆 LED 표지 창: 고정 한 장
                b.quad((s * (HW - 0.014), yc, (zs + WTOP) / 2), (0, s, 0), (0, 0, 1), w, WTOP - zs, M['glass'])
                continue
            for k, d in ((-1, 0.010), (1, 0.024)):     # 위 미닫이 두 장 (겹침)
                b.quad((s * (HW - d), yc + k * w / 4 - k * 0.01, (zs + WTOP) / 2), (0, s, 0), (0, 0, 1),
                       w / 2 + 0.02, WTOP - zs, M['glass'])
    nf = Vector((0, -1, KF)).normalized()
    up = Vector((0, KF, 1)).normalized()
    for z0, z1 in ((1.18, 2.52), (2.58, 2.88)):
        zc = (z0 + z1) / 2
        b.quad(Vector((0, yf(zc), zc)) - nf * 0.012, (1, 0, 0), up, 2.0, (z1 - z0) / math.cos(math.atan(KF)), M['glassc'])
    b.quad((0, YB - 0.012, 2.41), (-1, 0, 0), (0, 0, 1), 1.76, 0.58, M['glass'])
    ob = b.obj()
    k3d.uv_world(ob, 1.5)
    return ob


# ---------------------------------------------------------------- 실내
def interior(M):
    b = MB(A + "_Int", maxseg=1)   # 짙은 선팅 뒤라 1단 베벨
    h = MB(A + "_IntH", maxseg=1)  # 바퀴 공간과 겹치는 조각: 나중에 휠하우스 모양으로 깎는다
    xin = HW - TH
    ZH = 1.13                      # 휠하우스 덮개 윗면 (바퀴 공간 꼭대기 1.065 위)
    # 뒤쪽 높은 바닥 + 계단 노란 모서리
    h.box((2 * xin - 0.01, YB - TH - 1.56, 0.29), (0, (1.56 + YB - TH) / 2, ZFL + 0.145), M['floor'], bev=0.01)
    b.box((2 * xin - 0.02, 0.04, 0.02), (0, 1.57, ZFL + 0.28), M['yellow'], bev=0.005)
    # 운전석 단, 대시보드, 계기판, 운전대, 의자, 요금함
    b.box((0.95, 1.35, 0.20), (0.72, -4.68, ZFL + 0.10), M['floor'], bev=0.01)
    b.box((2 * xin, 0.34, 0.80), (0, YF + TH + 0.17, ZFL + 0.40), M['dash'], bev=0.03)
    b.box((0.55, 0.30, 0.14), (0.72, -5.05, 1.18), M['dash'], bev=0.03, rot=(0.4, 0, 0))
    b.box((0.40, 0.012, 0.09), (0.72, -5.19, 1.2), M['screen'], bev=0.004, rot=(0.4, 0, 0))
    rim = [(0.72 + 0.23 * math.cos(t * math.pi / 8), -4.80 + 0.23 * math.sin(t * math.pi / 8) * math.cos(0.35),
            1.12 + 0.23 * math.sin(t * math.pi / 8) * math.sin(0.35)) for t in range(16)]
    b.tube(rim, 0.018, M['dash'], seg=8, closed=True)
    b.cyl(0.03, 0.5, (0.72, -4.92, 0.92), M['dash'], seg=10, rot=(0.6, 0, 0))
    b.box((0.50, 0.48, 0.10), (0.72, -4.25, 0.80), M['dash'], bev=0.03, seg=2)
    b.box((0.50, 0.10, 0.62), (0.72, -4.02, 1.15), M['dash'], bev=0.03, seg=2, rot=(-0.15, 0, 0))
    b.box((0.10, 0.3, 0.35), (0.72, -4.25, 0.55), M['alu'], bev=0.01)
    b.box((0.30, 0.30, 0.85), (0.08, -4.65, ZFL + 0.425), M['alu'], bev=0.02)           # 요금함
    # 교통카드 단말기 (앞문·중문)
    for x, y, rz in ((-0.62, -3.92, 0.6), (-0.98, DM - DH - 0.06, 1.2), (-0.98, DM + DH + 0.06, 1.9)):
        b.cyl(0.02, 1.0, (x, y, ZFL + 0.5), M['pole'], seg=8)
        b.box((0.16, 0.09, 0.22), (x, y - 0.04, 1.32), M['dash'], bev=0.015, rot=(0, 0, rz))
        b.box((0.11, 0.01, 0.07), (x - 0.03, y - 0.09, 1.37), M['screen'], bev=0.003, rot=(0, 0, rz))
    # 세로 봉 (노랑) + 하차벨
    poles = [(-0.95, DF + DH + 0.04),
             (-0.42, -2.6), (0.42, -2.6), (-0.42, -1.0), (0.42, -1.0), (0.42, 0.9), (-0.42, 2.4), (0.42, 2.4),
             (-0.42, 3.9), (0.42, 3.9)]
    for x, y in poles:
        z0 = ZFL + (0.29 if y > 1.56 else 0)
        b.cyl(0.018, ZR - TH - z0, (x, y, (z0 + ZR - TH) / 2), M['pole'], seg=8)
        b.box((0.05, 0.035, 0.07), (x + (0.02 if x > 0 else -0.02), y, 1.38), M['red'], bev=0.01)
    # 천장 손잡이 봉 + 손잡이 고리
    for s in (-1, 1):
        x = s * 0.56
        b.cyl(0.016, 8.6, (x, 0.35, 2.24), M['pole'], axis='Y', seg=8)
        for i in range(15):
            y = -3.7 + i * 0.6
            b.box((0.026, 0.006, 0.17), (x, y, 2.14), M['dash'], bev=0.0)
            b.tube([(x, y - 0.05, 2.03), (x, y + 0.05, 2.03), (x, y, 1.95)], 0.011, M['handle'], seg=4, closed=True)
    # 천장 조명
    for s in (-1, 1):
        b.box((0.12, 8.8, 0.025), (s * 0.70, 0.2, ZR - TH - 0.02), M['light'], bev=0.006)
    # 의자 (앞쪽 1인석·노약자석, 뒤쪽 2인석, 맨 뒤 5인석)
    def seat(x, y, zf, m, leg=True):
        b.box((0.43, 0.42, 0.06), (x, y, zf + 0.44), m, bev=0.02, seg=1)
        b.box((0.43, 0.06, 0.50), (x, y + 0.23, zf + 0.72), m, bev=0.02, seg=1, rot=(-0.14, 0, 0))
        b.box((0.30, 0.04, 0.04), (x, y + 0.27, zf + 1.0), M['pole'], bev=0.01)
        if leg:   # 휠하우스 위 의자는 덮개가 받친다
            b.box((0.06, 0.30, 0.40), (x, y, zf + 0.21), M['alu'], bev=0.01)
    for s in (-1, 1):   # 휠하우스 덮개 (의자 받침). 바깥면은 외판 안쪽에 붙고, 바퀴 공간은 아래에서 깎는다
        h.box((0.565, 1.24, ZH - ZFL), (s * (xin - 0.005 - 0.2825), AXF, (ZFL + ZH) / 2), M['wall'], bev=0.03)
        h.box((0.915, 1.36, ZH - ZFL - 0.28), (s * (xin - 0.005 - 0.4575), AXR - 0.04, (ZFL + 0.28 + ZH) / 2),
              M['wall'], bev=0.03)   # 안쪽 면 |x| 0.64(앞)·0.29(뒤): 위 의자 방석 전체를 받친다
    zh = ZH - 0.41      # 덮개 위 의자 (방석 밑면 = ZH)
    for i, y in enumerate((-3.0, -2.15, -1.35, -0.55)):
        for s in (-1, 1):
            if s < 0 and i == 3:
                continue
            seat(s * 0.86, y, zh if i == 0 else ZFL, M['seatp'] if i < 2 else M['seat'], leg=i > 0)
    for y in (2.10, 2.90, 3.70, 4.50):
        for x in (-0.96, -0.51, 0.51, 0.96):
            seat(x, y, zh if y < 3.3 else ZFL + 0.29, M['seat'], leg=y > 3.3)
    for x in (-0.96, -0.48, 0.0, 0.48, 0.96):
        seat(x, 5.05, ZFL + 0.33, M['seat'])
    # 휠체어 공간 접이식 받침 (중문 맞은편)
    b.box((0.05, 1.1, 0.5), (xin - 0.03, DM, 0.95), M['dash'], bev=0.02)
    # 휠하우스 덮개·높은 바닥에서 바퀴 공간(외판 커터 + 외판 두께)을 깎아 아치 밖에서 안 보이게
    ho = h.obj()
    cut = well_cutters(TH + 0.005)
    md = ho.modifiers.new("wells", 'BOOLEAN')
    md.operation, md.solver, md.operand_type, md.collection = 'DIFFERENCE', 'EXACT', 'COLLECTION', cut
    md.use_self = True   # 덮개와 바닥이 겹친다
    k3d.apply_all(ho)
    drop(cut)
    ob = b.obj()
    k3d.select([ob, ho], ob)
    bpy.ops.object.join()
    return ob


# ---------------------------------------------------------------- 문짝 (경첩축 원점)
def door_leaf(name, c, d, M):
    """c=문 중심 y, d=+1 이면 경첩이 앞쪽(-Y)·짝이 뒤로 뻗음. 원점 = 경첩축 바닥."""
    hy = c - d * DH
    x0 = -HW + 0.022
    b = MB(name)
    wl, hl, z0 = DH - 0.006, DTOP - ZFL - 0.012, ZFL + 0.006
    Y = lambda ly: hy + d * ly
    fr, gl = M['dash'], M['glass']
    b.box((0.04, 0.05, hl), (x0, Y(0.025), z0 + hl / 2), fr, bev=0.008)                   # 경첩쪽 세로틀
    b.box((0.04, 0.045, hl), (x0, Y(wl - 0.0225), z0 + hl / 2), fr, bev=0.008)           # 맞닿는 세로틀
    b.box((0.04, wl, 0.06), (x0, Y(wl / 2), z0 + hl - 0.03), fr, bev=0.008)               # 위
    b.box((0.04, wl, 0.16), (x0, Y(wl / 2), z0 + 0.08), fr, bev=0.008)                    # 아래 (발차기판)
    b.box((0.04, wl, 0.05), (x0, Y(wl / 2), z0 + 1.02), fr, bev=0.008)                    # 가운데
    b.box((0.03, 0.03, hl - 0.04), (x0, Y(wl + 0.012), z0 + hl / 2), M['rubber'], bev=0.01)  # 고무 패킹
    b.cyl(0.022, hl + 0.02, (x0 + 0.03, Y(-0.005), z0 + hl / 2), M['alu'], seg=10)        # 회전 기둥
    for zb in (z0 + 0.4, z0 + 1.7):
        b.box((0.06, 0.05, 0.05), (x0 + 0.03, Y(0.03), zb), M['alu'], bev=0.01)
    b.tube([(x0 + 0.02, Y(wl * 0.55), z0 + 0.75), (x0 + 0.06, Y(wl * 0.55), z0 + 0.80),
            (x0 + 0.06, Y(wl * 0.55), z0 + 1.55), (x0 + 0.02, Y(wl * 0.55), z0 + 1.60)], 0.014, M['alu'], seg=8)
    for za, zb in ((z0 + 0.16, z0 + 0.995), (z0 + 1.045, z0 + hl - 0.06)):              # 유리 (양면 머티리얼)
        b.quad((x0, Y(wl / 2), (za + zb) / 2), (0, -1, 0), (0, 0, 1), wl - 0.08, zb - za, gl)
    return b, (x0, hy, z0)


# ---------------------------------------------------------------- 바퀴 (차축 중심 원점)
def revolve(bm, prof, steps=32):
    """(x, r) 윤곽선을 X 축으로 회전. 닫힌 윤곽은 법선 재계산, 열린 윤곽(휠 판)은 가운데가 -X 를 보게."""
    closed = prof[0] == prof[-1]
    if closed:
        prof = prof[:-1]
    vs = [bm.verts.new((x, 0, r)) for x, r in prof]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs) - (0 if closed else 1))]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(1, 0, 0), angle=2 * math.pi, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    if closed:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    else:
        fs = [f for f in bm.faces if f.calc_center_median().length < 0.12]
        if sum(f.normal.x * f.calc_area() for f in fs) > 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)


TIRE = [(-0.118, 0.290), (-0.132, 0.33), (-0.139, 0.38), (-0.137, 0.425), (-0.128, 0.457), (-0.110, 0.474),
        (-0.085, 0.479), (0.085, 0.479), (0.110, 0.474), (0.128, 0.457), (0.137, 0.425), (0.139, 0.38),
        (0.132, 0.33), (0.118, 0.290), (-0.118, 0.290)]


def wheel(name, rear, M):
    """바깥면 = -X 쪽 (오른쪽 바퀴 기준). 뒤바퀴는 복륜."""
    b = MB(name)
    tm, rm = M['tire'], M['rimm']
    offs = (0.0, 0.31) if rear else (0.0,)
    for ox in offs:
        bm = bmesh.new()
        revolve(bm, [(x + ox, r) for x, r in TIRE], 28)
        b.add(bm, tm)
    dish = -0.07 if not rear else -0.10
    rimp = [(-0.122, 0.302), (-0.112, 0.288), (-0.10, 0.281), (-0.06, 0.279), (dish + 0.02, 0.25),
            (dish, 0.20), (dish - 0.005, 0.15), (dish - 0.012, 0.115), (dish - 0.04, 0.10), (dish - 0.05, 0.07),
            (dish - 0.055, 0.0)]
    bm = bmesh.new()
    revolve(bm, rimp, 28)
    b.add(bm, rm)
    for i in range(10):                      # 휠 너트
        t = i * 2 * math.pi / 10
        b.cyl(0.016, 0.03, (dish - 0.02, 0.142 * math.cos(t), 0.142 * math.sin(t)), M['alu'], axis='X', seg=6)
    b.cyl(0.06, 0.04, (dish - 0.07, 0, 0), M['alu'], axis='X', seg=16, bev=0.008)       # 허브캡
    return b.obj()


# ---------------------------------------------------------------- 데칼·표지 (굽기 뒤에 붙임)
REG = {"ad_burger": (0, 0, 2048, 512), "ad_civic": (0, 512, 2048, 1024), "plate": (0, 1024, 512, 1280),
       "placard": (512, 1024, 1024, 1280), "company": (1024, 1024, 2048, 1280), "lowfloor": (0, 1280, 256, 1536),
       "cng": (256, 1280, 512, 1536), "board": (512, 1280, 1024, 1536), "alight": (1024, 1280, 1536, 1536),
       "lean": (1536, 1280, 1792, 1536), "hand": (1792, 1280, 2048, 1536)}   # CityBus_tex.REGIONS 와 같음


def uvr(k):
    x0, y0, x1, y1 = REG[k]
    return (x0 / 2048 + 0.0005, 1 - y1 / 2048 + 0.0005, x1 / 2048 - 0.0005, 1 - y0 / 2048 - 0.0005)


def decal_mats():
    dm = k3d.mat("M_CityBus_Decals", (1, 1, 1), 0.45)
    k3d.principled(dm).inputs['Emission Color'].default_value = (0, 0, 0, 1)
    n = k3d.image_node(dm, k3d.load_image(os.path.join(TDIR, "T_CityBus_Decals.png"), "T_CityBus_Decals"),
                       k3d.principled(dm).inputs['Base Color'])
    dm.node_tree.links.new(n.outputs['Alpha'], k3d.principled(dm).inputs['Alpha'])
    k3d.flag(dm, alpha_clip=0.5)
    im = k3d.load_image(os.path.join(TDIR, "T_CityBus_RouteSign.png"), "T_CityBus_RouteSign")
    sm = k3d.mat("M_Dyn_CityBus_RouteSign", (1, 1, 1), 0.3, emission=(1, 1, 1), strength=2.5)
    k3d.image_node(sm, im, k3d.principled(sm).inputs['Base Color'])
    k3d.image_node(sm, im, k3d.principled(sm).inputs['Emission Color'])
    return dm, sm


def decals(dm, sm):
    b = MB(A + "_Decal")
    q = b.quad
    R, Lr = (0, -1, 0), (0, 1, 0)        # 오른쪽(-X)에서 볼 때 오른쪽 = -Y, 왼쪽(+X)에서 볼 때 = +Y
    Z = (0, 0, 1)
    nf = Vector((0, -1, KF)).normalized()
    up = Vector((0, KF, 1)).normalized()
    # 광고 (오른쪽 버거대왕, 왼쪽 구청)
    q((-HW - 0.004, -1.10, 0.71), R, Z, 2.40, 0.60, dm, uvr("ad_burger"))
    q((HW + 0.004, -0.40, 0.71), Lr, Z, 2.40, 0.60, dm, uvr("ad_civic"))
    # 번호판 (앞·뒤 범퍼)
    q((0, YF - 0.03 - 0.118, 0.38), (1, 0, 0), Z, 0.335, 0.17, dm, uvr("plate"))
    q((0, YB + 0.03 + 0.118, 0.38), (-1, 0, 0), Z, 0.335, 0.17, dm, uvr("plate"))
    # 대시보드 노선 안내판 (앞유리 안, 문 쪽 아래)
    q(Vector((-0.70, yf(1.33), 1.33)) - nf * 0.06, (1, 0, 0), up, 0.40, 0.20, dm, uvr("placard"))
    # 회사명 (양 옆 창 위 띠, 앞쪽)
    q((-HW - 0.003, -3.10, 2.62), R, Z, 0.72, 0.18, dm, uvr("company"))
    q((HW + 0.003, -3.10, 2.62), Lr, Z, 0.72, 0.18, dm, uvr("company"))
    # 스티커: 저상 (앞면·오른쪽 중문 옆 유리), CNG (뒤·오른쪽)
    q((-0.62, YF - 0.012, 1.02), (1, 0, 0), Z, 0.16, 0.16, dm, uvr("lowfloor"))
    q((-HW + 0.005, 0.12, 1.80), R, Z, 0.20, 0.20, dm, uvr("lowfloor"))
    q((0.55, YB + 0.019, 0.83), (-1, 0, 0), Z, 0.16, 0.16, dm, uvr("cng"))
    q((-HW - 0.012, 3.45, 0.66), R, Z, 0.16, 0.16, dm, uvr("cng"))
    return b


def route_sign(sm):
    """노선 LED (동적, 별도 오브젝트): 앞 1.60x0.30, 옆 1.17x0.22, 뒤 0.96x0.18 (모두 5.33:1)."""
    b = MB(A + "_RouteSign")
    nf = Vector((0, -1, KF)).normalized()
    up = Vector((0, KF, 1)).normalized()
    zc = 2.73
    b.quad(Vector((0, yf(zc), zc)) - nf * 0.05, (1, 0, 0), up, 1.60, 0.30, sm)
    b.quad((-HW + 0.065, -3.135, 2.29), (0, -1, 0), (0, 0, 1), 1.17, 0.22, sm)
    b.quad((0, YB - 0.065, 2.49), (-1, 0, 0), (0, 0, 1), 0.96, 0.18, sm)
    return b.obj()


def leaf_stickers(name, c, d, k1, k2, dm):
    b = MB(name + "_S")
    hy = c - d * DH
    yc = hy + d * DH / 2
    x0 = -HW + 0.022    # 문 유리 면
    for x, r in ((x0 - 0.003, (0, -1, 0)), (x0 + 0.003, (0, 1, 0))):   # 바깥·안쪽 (단면 머티리얼이라 두 장, 안쪽도 바로 읽힘)
        b.quad((x, yc, 1.62), r, (0, 0, 1), 0.36, 0.18, dm, uvr(k1))
        b.quad((x, yc, 0.86 if k2 in ("lean", "hand") else 1.98), r, (0, 0, 1), 0.15, 0.15, dm, uvr(k2))
    return b


def join_into(target, ob):
    """굽힌 메시에 나중 조각(데칼)을 합친다 (UV 이름 UVMap 유지)."""
    if not target.data.uv_layers:   # CB_FAST (굽지 않음)
        target.data.uv_layers.new(name="UVMap")
    if ob.data.uv_layers:
        ob.data.uv_layers[0].name = target.data.uv_layers[0].name
    k3d.select([target, ob], target)
    bpy.ops.object.join()
    target.data.uv_layers[0].active_render = True   # 합친 UV 가 렌더 UV 가 아니면 이미지가 안 보임
    return target


# ---------------------------------------------------------------- 미리보기 (1인칭 눈높이)
def fp_shot(objs, cam, look, path, lens=24):
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = 1400, 900
    sc.view_settings.view_transform, sc.view_settings.look = 'Standard', 'None'
    w = bpy.data.worlds.new("fpw")
    sc.world = w
    if w.node_tree is None:
        w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value, bg.inputs['Strength'].default_value = (0.62, 0.66, 0.72, 1), 0.7
    tmp = []
    ld = bpy.data.lights.new("fps", 'SUN')
    ld.energy, ld.angle = 2.6, 0.05
    lo = bpy.data.objects.new("fps", ld)
    lo.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(lo)
    tmp.append(lo)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("k3d_ground_fp", (0.22, 0.22, 0.23), 0.85))
    tmp.append(g)
    cd = bpy.data.cameras.new("fpc")
    cd.lens, cd.clip_start = lens, 0.05
    co = bpy.data.objects.new("fpc", cd)
    sc.collection.objects.link(co)
    co.location = cam
    co.rotation_euler = (Vector(look) - Vector(cam)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    tmp.append(co)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    print("fp_shot", path)


# ---------------------------------------------------------------- main
def main():
    k3d.reset()
    os.makedirs(TDIR, exist_ok=True)
    subprocess.run([VENV, "-I", TEXPY, TDIR], check=True)
    M = materials()
    M['tire'], M['rimm'] = mat_tire(), mat_rim()
    body, inner = shell(M)
    ext = exterior(M)
    glass_ob = glass(M)
    intr = interior(M)
    k3d.select([intr, inner], intr)
    bpy.ops.object.join()
    intr.name = intr.data.name = A + "_Interior"

    leaves = []
    for nm, c, d in (("DoorFront_R", DF, 1), ("DoorFront_L", DF, -1), ("DoorMid_R", DM, 1), ("DoorMid_L", DM, -1)):
        b, piv = door_leaf(f"{A}_{nm}", c, d, M)
        leaves.append((b.obj(loc=piv), c, d))
    wf = wheel(A + "_Wheel_FR", False, M)
    wr = wheel(A + "_Wheel_RR", True, M)
    wf.location = (-(HW - 0.03 - 0.139), AXF, RW)
    wr.location = (-(HW - 0.03 - 0.139), AXR, RW)

    for o in (body, ext, intr, wf, wr, *[l[0] for l in leaves]):
        finish(o, 50, weighted=o not in (wf, wr))
    finish(glass_ob, 30, weighted=False)

    dm, sm = decal_mats()
    if not FAST:
        k3d.bake(body, 2048, samples=24, ao_distance=0.5, margin=8)
        k3d.bake(ext, 2048, samples=16, ao_distance=0.2, margin=6)
        k3d.bake(intr, 1024, samples=16, ao_distance=0.3, margin=4)
        for lf, c, d in leaves:
            k3d.uv_world(lf, 1.5)   # 문 유리 먼지 텍스처를 옆창과 같은 크기로 (굽는 면 UV 는 bake 가 덮어씀)
            k3d.bake(lf, 512, samples=16, ao_distance=0.15)
        k3d.bake(wf, 1024, samples=16, ao_distance=0.12, name=A + "_WheelFront")
        k3d.bake(wr, 1024, samples=16, ao_distance=0.12, name=A + "_WheelRear")
    # 왼쪽 바퀴 = 오른쪽 바퀴를 Z 180도 돌린 복사 (머티리얼 공유, 회전축 X 동일)
    wheels = [wf, wr]
    for src, nm, y in ((wf, "Wheel_FL", AXF), (wr, "Wheel_RL", AXR)):
        o = src.copy()
        o.data = src.data.copy()
        o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
        o.name = o.data.name = f"{A}_{nm}"
        o.location = (HW - 0.03 - 0.139, y, RW)
        bpy.context.scene.collection.objects.link(o)
        wheels.append(o)
    # 데칼·LED 표지 붙이기
    dec = decals(dm, sm).obj()
    join_into(body, dec)
    sign = route_sign(sm)
    for (lf, c, d), ks in zip(leaves, (("board", "hand"), ("board", "lowfloor"), ("alight", "lean"), ("alight", "lean"))):
        join_into(lf, leaf_stickers(lf.name, c, d, ks[0], ks[1], dm).obj())
    # 계층·소켓
    for o in [ext, intr, glass_ob, sign, *wheels, *[l[0] for l in leaves]]:
        o.parent = body
    for nm, loc in (("DoorFront", (-HW - 0.45, DF, 0.0)), ("DoorMid", (-HW - 0.45, DM, 0.0)),
                    ("SignFront", (0.0, yf(2.73) - 0.02, 2.73)), ("SignSide", (-HW - 0.02, -3.135, 2.29))):
        e = bpy.data.objects.new(f"{A}_Socket_{nm}", None)
        e.empty_display_type, e.empty_display_size = 'ARROWS', 0.3
        e.location = loc
        bpy.context.scene.collection.objects.link(e)
        e.parent = body

    pdir = os.path.join(k3d.SRC, "Previews")
    os.makedirs(pdir, exist_ok=True)
    if not FAST:
        k3d.export(A, "Vehicles", [body], notes=NOTES)
    tag = "fast" if FAST else ""
    k3d.preview(A, [body], tag=tag)
    k3d.preview(A, [body], views=((0, 8),), lens=35, tag=(tag + "front").strip())
    fp_shot([body], (-4.2, -8.6, 1.55), (-1.3, -3.6, 1.45), os.path.join(pdir, f"{A}_{tag}fp_0.png"))
    # 문 연 상태 (피벗 확인용)
    for lf, c, d in leaves:
        lf.rotation_euler.z = d * math.radians(88)
    fp_shot([body], (-3.6, -2.2, 1.55), (-1.2, -4.4, 1.25), os.path.join(pdir, f"{A}_{tag}fp_open.png"), lens=28)
    fp_shot([body], (-HW - 0.45, DM, 1.55), (0.3, 2.6, 0.9), os.path.join(pdir, f"{A}_{tag}fp_mid.png"), lens=28)   # 중문 소켓에서 실내
    for lf, c, d in leaves:
        lf.rotation_euler.z = 0
    # 휠하우스·왼쪽 뒤 그릴 확인 (눈높이 1.55m)
    for i, (cam, look) in enumerate((((-3.2, -1.6, 1.55), (-1.2, -3.0, 0.5)), ((-3.2, 4.1, 1.55), (-1.2, 2.7, 0.5)),
                                     ((3.2, 4.1, 1.55), (1.2, 3.3, 0.7)))):
        fp_shot([body], cam, look, os.path.join(pdir, f"{A}_{tag}wheel_{i}.png"), lens=35)


NOTES = {
    "front": "Blender -Y = Unity +Z(transform.forward). 문은 오른쪽(Unity +X, transform.right) 보도 쪽.",
    "parts": "CityBus_Body(외판 도장+광고·번호판·스티커 데칼, 2048) / CityBus_Trim(범퍼·등화·거울·와이퍼·지붕 CNG·에어컨·창틀, 2048) / "
             "CityBus_Interior(의자·봉·손잡이·운전석, 1024) / CityBus_Glass / CityBus_RouteSign / 문짝 4 / 바퀴 4 — 모두 CityBus_Body 의 자식.",
    "origin": "차체 바닥 중앙 (범퍼 제외 차체 길이 10.84m 의 가운데, 바닥 z=0). 바퀴가 땅에 닿는다.",
    "doors": "CityBus_DoorFront_L/R, CityBus_DoorMid_L/R: 원점 = 경첩(회전 기둥) 축의 바닥. _R = 차 앞쪽 짝, _L = 뒤쪽 짝. "
             "열기: 경첩 세로축 기준 차체 바깥쪽으로 약 88도 회전(Blender _R Z +88° / _L Z -88° = Unity localEulerAngles.y _R -88 / _L +88) 또는 프로토타입처럼 "
             "바깥 0.08m + 문 중심에서 멀어지는 쪽으로 0.5m 미끄러짐.",
    "wheels": "CityBus_Wheel_FR/FL/RR/RL: 원점 = 차축 중심 (반지름 0.48m). 회전축 = 로컬 X(Blender) 로 네 바퀴 모두 같다. "
              "뒤는 복륜. 앞 2개는 M_CityBus_WheelFront, 뒤 2개는 M_CityBus_WheelRear 텍스처를 공유. "
              "Unity 전진(+Z) 시 네 바퀴 모두 로컬 X 축 + 방향 회전 (각도 rad = 이동거리 / 0.48).",
    "sockets": "CityBus_Socket_DoorFront / DoorMid: 각 문 앞 보도 위(문 중심에서 바깥 0.45m, 바닥). "
               "CityBus_Socket_SignFront / SignSide: 노선 LED 표지 중심 (돋보기·시선 대상).",
    "dynamic": [
        {"material": "M_Dyn_CityBus_RouteSign", "object": "CityBus_RouteSign (사각형 3장: 앞·오른쪽 옆·뒤, 같은 머티리얼 공유)",
         "size_m": {"front": [1.60, 0.30], "side_right": [1.17, 0.22], "rear": [0.96, 0.18]},
         "texture_px": [2048, 384], "placeholder": "Textures/CityBus/T_CityBus_RouteSign.png (112 시장입구 ↔ 종합병원, 주황 LED 도트)",
         "uv": "각 사각형 UV 0..1 전체, 밖에서 볼 때 U=오른쪽 V=위. 세 장 모두 5.33:1 이라 한 장의 텍스처를 그대로 쓴다. "
               "2413번 등은 같은 비율 텍스처로 교체 (자리표시 T_CityBus_RouteSign_2413.png, 번호가 번진 T_CityBus_RouteSign_2413_Blur.png). "
               "방출 강도 2.5."}],
    "decals": "M_CityBus_Decals (알파 클립): 광고 2종(오른쪽 버거대왕, 왼쪽 은행골구 디지털 배움터), 번호판 '서울 74 사 3112', "
              "대시보드 112 안내판, 회사명 '시민교통(주) 112-07', 저상버스·CNG·승하차·문 주의 스티커.",
    "glass": "M_Glass_CityBus (옆창·뒷창·문 유리, 짙은 선팅), M_Glass_CityBus_Clear (앞유리·행선지 창) — 양면 투명.",
}


main()

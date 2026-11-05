"""DeliveryScooter: 배달 스쿠터 (125cc 급, 휠베이스 1.30 m) + '버거대왕' 배달통 + 핸들 토시 + 휴대폰 거치대.
정면 -Y. 원점 바닥 중앙. 바퀴 2개는 차축 원점 자식 (로컬 X 축 회전). 배달통은 굽지 않는 이미지 재질 (글자 선명).
라이더는 포함하지 않음 (Socket_Seat / Grip 소켓 제공). 센터 스탠드는 경첩 원점 자식 (기본 = 접힘, 주차 = STAND_DEPLOY 만큼 회전).
좌우: 정면 -Y 기준 +X = 왼쪽 (엔진·쇼크), -X = 오른쪽 (머플러)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import _vlib as V
import _car
k3d = V.k3d
FAST = bool(os.environ.get("CAR_FAST"))

A = "DeliveryScooter"
R = 0.27
FW, RW = (0, -0.65, R), (0, 0.65, R)
HINGE = (0, 0.30, 0.19)        # 센터 스탠드 경첩 (로컬 X 축)
STAND_FOLD = math.radians(70)  # 접힘 각 (발이 뒤로)


def pod(name, size, loc, mat, rot=(0, 0, 0), taper=None, lvl=2):
    """둥근 상자 (플라스틱 커버, 크기 그대로). taper=(위쪽 x배율, 위쪽 y이동). lvl=1 은 덜 둥글게."""
    o = V.box(A + name, size, loc, mat, rot=rot)
    if taper:
        for v in o.data.vertices:
            if v.co.z > 0:
                v.co.x *= taper[0]
                v.co.y += taper[1]
    V.bevel_mod(o, min(size) * (0.42 if lvl > 1 else 0.25), 3, angle=None)
    return o


def panel(name, size, loc, mat, rot, bend, top, bev=0.012):
    """곡면 패널 (레그실드): x 로 잘게 나눈 상자를 x² 만큼 뒤로 휘고(다리 감싸기) 위쪽 폭을 top 배로."""
    o = _car.gbox(A + name, size, loc, mat, cuts=8, bev=0, rot=rot)
    for v in o.data.vertices:
        v.co.x *= 1 + (top - 1) * (v.co.z / size[2] + 0.5)
        v.co.y += bend * v.co.x ** 2
    V.bevel_mod(o, bev, 3, angle=30)
    return o


def T(name, pts, r, mat, segs=8, cap=True):
    return V.tube(A + name, pts, r, segs, mat, cap=cap)


def mats():
    M = {}
    M["body"] = V.mat_plastic(f"{A}_body", (0.70, 0.70, 0.68), 0.32, (0.78, 0.77, 0.72), dirt=1.3, grain=700)
    M["black"] = V.mat_plastic(f"{A}_black", (0.025, 0.025, 0.027), 0.55, (0.07, 0.07, 0.068), dirt=1.0)
    M["seat"] = V.mat_plastic(f"{A}_seat", (0.02, 0.02, 0.022), 0.45, (0.05, 0.05, 0.05), dirt=0.5, grain=300)
    M["chrome"] = V.mat_metal(f"{A}_chrome", (0.80, 0.80, 0.82), 0.12, 0.2, rust=0.3)
    M["steel"] = V.mat_metal(f"{A}_steel", (0.30, 0.30, 0.31), 0.45, 0.2, rust=0.6)
    M["alu"] = V.mat_metal(f"{A}_alu", (0.25, 0.25, 0.26), 0.5, 0.2)
    M["rubber"] = V.mat_rubber(f"{A}_rubber")
    M["muff"] = V.mat_plastic(f"{A}_muff", (0.012, 0.012, 0.014), 0.85, (0.04, 0.04, 0.045), dirt=0.8, grain=1500)
    M["head"] = _car.m_emit(f"{A}_headlamp", (0.9, 0.92, 0.95), (0.8, 0.85, 0.95))
    M["lens"] = V.glass(f"M_Glass_{A}_Lens", (0.9, 0.92, 0.95), 0.22, 0.02)
    M["amber"] = _car.m_emit(f"{A}_amber", (0.7, 0.25, 0.02), (0.06, 0.02, 0.0), 0.15)
    M["tail"] = _car.m_tail(f"{A}_tail")
    M["screen"] = _car.m_gloss_black(f"{A}_screen", 0.05)
    g = V.NB(f"{A}_tire")
    x, y, z = g.xyz()
    ang = g.math('ARCTAN2', z, y)
    sip = g.line(g.math('FRACT', g.mul(ang, 40 / (2 * math.pi))), 0.5, 0.08)
    sip = g.mul(sip, g.maprange(g.absf(x), 0.012, 0.02, 0, 1))
    dust = g.mul(g.maprange(g.noise(5, 5, 0.6), 0.35, 0.75, 0, 1), 0.6)
    col = g.mix(dust, (0.018, 0.018, 0.019), (0.08, 0.072, 0.06))
    M["tire"] = g.out(col, 0.82, 0.0, g.bump(g.sub(0, sip), 0.6, 0.003))
    return M


def body(M):
    P = []
    # 바닥판 + 고무 매트
    P.append(pod("_floor", (0.34, 0.50, 0.07), (0, -0.06, 0.39), M["black"], lvl=1))
    P.append(V.box(A + "_mat", (0.28, 0.42, 0.01), (0, -0.06, 0.428), M["rubber"], bevel=0.004))
    # 앞 레그실드: 다리를 감싸는 휜 패널 (위로 갈수록 좁음) + 안쪽 검은 패널 + 조향축 앞 커버
    P.append(panel("_shield", (0.46, 0.045, 0.62), (0, -0.36, 0.70), M["body"], rot=(-0.28, 0, 0), bend=0.7, top=0.72))
    P.append(panel("_shieldIn", (0.36, 0.03, 0.50), (0, -0.315, 0.66), M["black"], rot=(-0.28, 0, 0), bend=0.7, top=0.8, bev=0.008))
    P.append(pod("_nose", (0.16, 0.16, 0.36), (0, -0.44, 0.80), M["body"], rot=(-0.28, 0, 0), taper=(0.8, 0.0), lvl=1))
    # 뒤 차체 (시트 아래): 뒤로 갈수록 좁고 높아지는 사이드 커버 + 캐릭터 라인
    rear = V.box(A + "_rear", (0.34, 0.80, 0.30), (0, 0.40, 0.60), M["body"])
    for v in rear.data.vertices:
        if v.co.y > 0:
            v.co.x *= 0.80
            v.co.z += 0.05 if v.co.z < 0 else 0.0
    V.bevel_mod(rear, 0.045, 3, angle=None)
    P.append(rear)
    for sx in (1, -1):
        P.append(T("_crease", [(sx * 0.172, 0.06, 0.635), (sx * 0.160, 0.45, 0.66), (sx * 0.142, 0.76, 0.69)], 0.005, M["black"], 6))
    P.append(pod("_rearSkirt", (0.30, 0.62, 0.12), (0, 0.32, 0.45), M["black"], lvl=1))
    # 시트
    seat = pod("_seat", (0.30, 0.66, 0.10), (0, 0.30, 0.80), M["seat"], taper=(0.92, 0))
    for v in seat.data.vertices:  # 운전석 낮게, 뒷좌석 높게
        v.co.z += 0.03 * max(0.0, v.co.y) / 0.33
    P.append(seat)
    # 앞 흙받이 (C 단면 부분 회전체)
    fp = [(-0.06, R + 0.035), (-0.065, R + 0.05), (0, R + 0.058), (0.065, R + 0.05), (0.06, R + 0.035)]
    f = V.lathe(A + "_fender", fp, 20, mats=[M["body"]], axis='X', a0=math.radians(35), a1=math.radians(160))
    f.location = FW
    f.modifiers.new("sol", 'SOLIDIFY').thickness = 0.004
    P.append(f)
    # 포크·조향
    for sx in (1, -1):
        P.append(T("_fork", [(sx * 0.075, FW[1], FW[2]), (sx * 0.07, -0.56, 0.58), (sx * 0.06, -0.47, 0.86)], 0.022, M["steel"], 10))
    P.append(T("_steer", [(0, -0.47, 0.84), (0, -0.44, 1.00)], 0.025, M["steel"], 10))
    # 핸들 커버 (계기판) + 전조등
    P.append(pod("_barCover", (0.40, 0.18, 0.11), (0, -0.44, 1.03), M["body"], taper=(0.85, 0.01)))
    P.append(V.box(A + "_meter", (0.15, 0.01, 0.07), (0, -0.37, 1.07), M["screen"], bevel=0.006, rot=(0.5, 0, 0)))
    P.append(headlamp(M))
    P.append(pod("_headBezel", (0.24, 0.05, 0.12), (0, -0.505, 1.00), M["black"], rot=(-0.25, 0, 0)))
    for sx in (1, -1):
        P.append(pod("_signalF", (0.07, 0.04, 0.035), (sx * 0.17, -0.50, 0.93), M["amber"], lvl=1))
        P.append(pod("_signalR", (0.06, 0.04, 0.03), (sx * 0.12, 0.82, 0.70), M["amber"], lvl=1))
    # 핸들바·그립·레버·토시·거울
    for sx in (1, -1):
        P.append(T("_bar", [(sx * 0.16, -0.43, 1.04), (sx * 0.36, -0.40, 1.05)], 0.011, M["steel"], 8))
        P.append(T("_grip", [(sx * 0.26, -0.40, 1.05), (sx * 0.37, -0.395, 1.05)], 0.017, M["rubber"], 8))
        P.append(T("_lever", [(sx * 0.20, -0.45, 1.06), (sx * 0.28, -0.47, 1.05), (sx * 0.34, -0.465, 1.04)], 0.006, M["chrome"], 6))
        muff = pod("_muff", (0.20, 0.24, 0.16), (sx * 0.31, -0.41, 1.04), M["muff"])
        for v in muff.data.vertices:  # 손 넣는 입구 쪽(안쪽) 넓게, 구김
            v.co.z *= 1.0 + 0.15 * (v.co.x * sx > 0)
        P.append(muff)
        P.append(T("_mirStalk", [(sx * 0.20, -0.43, 1.07), (sx * 0.24, -0.43, 1.15), (sx * 0.27, -0.44, 1.22)], 0.007, M["steel"], 6))
        mh = V.cyl(A + "_mirHead", 0.055, 0.03, (sx * 0.28, -0.44, 1.25), (math.pi / 2, 0, 0), M["black"], segs=20, bevel=0.008)
        P.append(mh)
        P.append(V.cyl(A + "_mirGlass", 0.047, 0.004, (sx * 0.28, -0.4245, 1.25), (math.pi / 2, 0, 0), M["chrome"], segs=20))
    # 휴대폰 거치대 + 폰 (배달앱 내비)
    P.append(T("_phoneArm", [(0.08, -0.44, 1.07), (0.09, -0.47, 1.12)], 0.008, M["black"], 6))
    P.append(V.box(A + "_phoneClamp", (0.09, 0.025, 0.17), (0.09, -0.48, 1.18), M["black"], bevel=0.008, rot=(0.35, 0, 0)))
    P.append(V.box(A + "_phone", (0.075, 0.012, 0.155), (0.09, -0.468, 1.183), M["screen"], bevel=0.006, rot=(0.35, 0, 0)))
    # 엔진·스윙암·뒤 쇼크 (왼쪽 +X), 머플러 (오른쪽 -X)
    P.append(pod("_engine", (0.14, 0.55, 0.18), (0.10, 0.40, 0.30), M["alu"], lvl=1))
    P.append(V.box(A + "_engineFins", (0.02, 0.18, 0.12), (0.175, 0.22, 0.30), M["alu"], bevel=0.004))
    P.append(T("_shock", [(0.12, 0.62, 0.34), (0.12, 0.55, 0.62)], 0.018, M["chrome"], 8))
    P.append(T("_spring", [(0.12 + 0.026 * math.cos(a), 0.62 - 0.07 * a / (12 * math.pi) + 0.026 * math.sin(a),
                            0.36 + 0.24 * a / (12 * math.pi)) for a in np.linspace(0, 12 * math.pi, 60)], 0.005, M["steel"], 5))
    P.append(T("_exPipe", [(-0.04, 0.05, 0.24), (-0.12, 0.25, 0.22), (-0.16, 0.42, 0.30)], 0.022, M["steel"], 8))
    P.append(pod("_muffler", (0.10, 0.42, 0.11), (-0.17, 0.60, 0.36), M["steel"], rot=(-0.12, 0, 0)))
    P.append(pod("_heatShield", (0.04, 0.30, 0.09), (-0.225, 0.58, 0.37), M["chrome"], rot=(-0.12, 0, 0), lvl=1))
    P.append(T("_exTip", [(-0.17, 0.80, 0.385), (-0.17, 0.86, 0.395)], 0.02, M["steel"], 10))
    # 뒤 흙받이 + 번호판 받침 + 미등
    P.append(pod("_rearHug", (0.14, 0.30, 0.05), (0, 0.80, 0.56), M["black"], rot=(0.5, 0, 0), lvl=1))
    P.append(V.box(A + "_plateBase", (0.23, 0.02, 0.13), (0, 0.905, 0.52), M["black"], bevel=0.006, rot=(0.25, 0, 0)))  # 뒤·위를 봄
    P.append(pod("_tail", (0.16, 0.05, 0.05), (0, 0.83, 0.72), M["tail"], lvl=1))
    # 짐대 (배달통 받침)
    for sx in (1, -1):
        P.append(T("_rack", [(sx * 0.13, 0.30, 0.84), (sx * 0.15, 0.55, 0.875), (sx * 0.15, 0.88, 0.875)], 0.011, M["black"], 6))
    for y in (0.52, 0.70, 0.88):
        P.append(T("_rackX", [(-0.15, y, 0.875), (0.15, y, 0.875)], 0.009, M["black"], 6))
    o = V.join(P, A + "_Body")
    V.shade(o, 40)
    return o


def headlamp(M):
    """전조등: 크롬 반사경 그릇 + 작은 전구(발광) + 테 + 유리 렌즈. 축 -Y 로 만들고 가로 2배 타원, 기울여 붙인다."""
    bowl = V.lathe(A + "_reflBowl", [(0.016, 0.004), (0.012, 0.018), (0.004, 0.031), (-0.006, 0.040), (-0.014, 0.045),
                                     (-0.014, 0.050)], 24, mats=[M["chrome"]], axis='Y')
    bowl.modifiers.new("sol", 'SOLIDIFY').thickness = 0.002
    ring = V.tube(A + "_lampRing", [(0.050 * math.cos(a), -0.015, 0.050 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)],
                  0.005, 6, M["black"], cap=False, closed=True)
    lens = V.cyl(A + "_lens", 0.049, 0.003, (0, -0.016, 0), (math.pi / 2, 0, 0), M["lens"], segs=32)
    for o in (bowl, ring, lens):
        for v in o.data.vertices:
            v.co.x *= 2.0
    bulb = V.cyl(A + "_bulb", 0.009, 0.016, (0, 0.004, 0), (math.pi / 2, 0, 0), M["head"], segs=12)
    o = V.join([bowl, ring, lens, bulb], A + "_headlamp")
    o.location, o.rotation_euler = (0, -0.535, 1.00), (-0.25, 0, 0)
    return o


def stand(M):
    """센터 스탠드 (U자 다리 2 + 가로대 + 발판 + 차는 레버). 내린 자세로 만들고 STAND_FOLD 만큼 접어 둔다. 원점 = 경첩."""
    h = HINGE[2]
    P = [V.cyl(A + "_standPivot", 0.014, 0.19, (0, 0, 0), (0, math.pi / 2, 0), M["steel"], segs=12)]
    for sx in (1, -1):
        P.append(T("_standLeg", [(sx * 0.08, 0, 0), (sx * 0.085, 0.005, -0.10), (sx * 0.10, 0.0, -h + 0.012)], 0.011, M["steel"], 8))
        P.append(V.box(A + "_standFoot", (0.045, 0.05, 0.012), (sx * 0.10, 0.0, -h + 0.006), M["rubber"], bevel=0.003))
    P.append(T("_standBar", [(-0.085, 0.005, -0.08), (0.085, 0.005, -0.08)], 0.009, M["steel"], 8))
    P.append(T("_standKick", [(0.085, 0.0, -0.04), (0.15, 0.04, -0.03), (0.17, 0.05, -0.02)], 0.008, M["steel"], 6))
    P.append(V.box(A + "_standKickPad", (0.04, 0.02, 0.015), (0.175, 0.055, -0.02), M["rubber"], bevel=0.003))
    o = V.join(P, A + "_Stand")
    o.data.transform(Matrix.Rotation(STAND_FOLD, 4, 'X'))  # 접힘 = 기본 (주행)
    V.shade(o, 40)
    o.location = HINGE
    return o


def delivery_box():
    """배달통: 옆=로고 인쇄, 뒤=주문 안내, 위·앞 = 같은 이미지의 빈 빨강 영역."""
    side = V.flat_image(f"M_{A}_BoxSide", V.tex("box_side.png"), 0.45)
    back = V.flat_image(f"M_{A}_BoxBack", V.tex("box_back.png"), 0.45)
    w, d, h = 0.44, 0.42, 0.40
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    x0, x1, y0, y1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2, 0, h
    P = lambda x, y, z: bm.verts.new((x, y, z))
    faces = [  # (꼭짓점 4, 재질, UV 4)
        ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], 0, [(0, 0), (1, 0), (1, 1), (0, 1)]),   # 오른쪽(+x)
        ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], 0, [(0, 0), (1, 0), (1, 1), (0, 1)]),   # 왼쪽
        ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], 1, [(0, 0), (1, 0), (1, 1), (0, 1)]),   # 뒤(+y)
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], 0, [(0.02, 0.88), (0.12, 0.88), (0.12, 0.98), (0.02, 0.98)]),  # 앞
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 0, [(0.85, 0.88), (0.98, 0.88), (0.98, 0.98), (0.85, 0.98)]),  # 위
        ([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], 0, [(0.85, 0.88), (0.98, 0.88), (0.98, 0.98), (0.85, 0.98)]),  # 아래
    ]
    vcache = {}
    for pts, mi, uvs in faces:
        vs = []
        for p in pts:
            if p not in vcache:
                vcache[p] = P(*p)
            vs.append(vcache[p])
        f = bm.faces.new(vs)
        f.material_index = mi
        for l, uv in zip(f.loops, uvs):
            l[uvl].uv = uv
    o = V.mesh_obj(A + "_Box", bm, [side, back])
    b = o.modifiers.new("bev", 'BEVEL')
    b.width, b.segments, b.harden_normals = 0.018, 3, False
    V.shade(o, 40)
    o.location = (0, 0.70, 0.89)
    return o


def box_hardware(M):
    """배달통 뚜껑 이음선·걸쇠·경첩 (차체와 함께 굽는다)."""
    P = []
    z = 0.89 + 0.33
    P.append(V.box(A + "_lidSeam", (0.448, 0.428, 0.012), (0, 0.70, z), M["black"]))
    for sx in (1, -1):
        P.append(V.box(A + "_latch", (0.05, 0.02, 0.06), (sx * 0.12, 0.70 + 0.218, z - 0.01), M["chrome"], bevel=0.005))
        P.append(V.box(A + "_hinge", (0.07, 0.02, 0.03), (sx * 0.13, 0.70 - 0.217, z), M["chrome"], bevel=0.004))
    P.append(V.box(A + "_lock", (0.03, 0.02, 0.03), (0, 0.70 + 0.218, z - 0.04), M["chrome"], bevel=0.004))
    for sx in (1, -1):
        P.append(V.box(A + "_boxRefl", (0.04, 0.008, 0.10), (sx * 0.17, 0.70 + 0.214, 0.89 + 0.12), M["tail"], bevel=0.003))
    return P


def wheel(M, nm, disc):
    hw = 0.055
    tp = [(-hw * 0.7, 0.165), (-hw, 0.20), (-hw * 0.95, R - 0.03), (-hw * 0.6, R - 0.004), (0, R), (hw * 0.6, R - 0.004),
          (hw * 0.95, R - 0.03), (hw, 0.20), (hw * 0.7, 0.165), (-hw * 0.7, 0.165)]
    P = [V.lathe(A + "_tire", tp, 40, mats=[M["tire"]])]
    rp = [(-hw * 0.75, 0.155), (-hw * 0.8, 0.172), (-hw * 0.6, 0.16), (hw * 0.6, 0.16), (hw * 0.8, 0.172), (hw * 0.75, 0.155)]
    P.append(V.lathe(A + "_rim", rp, 40, mats=[M["black"]]))
    P.append(V.lathe(A + "_hub", [(-hw * 0.9, 0.012), (-hw * 0.8, 0.05), (hw * 0.8, 0.05), (hw * 0.9, 0.012)], 16, mats=[M["alu"]]))
    for k in range(5):
        a = 2 * math.pi * k / 5
        P.append(_car.beam(A + "_sp", (0, math.cos(a) * 0.045, math.sin(a) * 0.045), (0, math.cos(a + 0.25) * 0.158, math.sin(a + 0.25) * 0.158),
                           0.022, 0.03, M["black"], up=(1, 0, 0)))
    if disc:
        d = V.lathe(A + "_disc", [(-0.003, 0.06), (-0.003, 0.11), (0.003, 0.11), (0.003, 0.06), (-0.003, 0.06)], 24, mats=[M["steel"]])
        d.location.x = 0.05
        P.append(d)
    w = V.join(P, A + nm)
    V.shade(w, 40)
    return w


def main():
    k3d.reset()
    V.make_textures()
    M = mats()
    b = body(M)
    hw = box_hardware(M)
    b = V.join([b] + hw, A + "_Body")
    V.shade(b, 40)
    wf = wheel(M, "_WheelFront", True)
    wr = wheel(M, "_WheelRear", False)
    st = stand(M)
    _car.fix_emission()
    if not FAST:
        k3d.bake(b, 1024, samples=16, ao_distance=0.1)
        k3d.bake(wf, 512, samples=12, ao_distance=0.05)
        k3d.bake(wr, 512, samples=12, ao_distance=0.05)
        k3d.bake(st, 512, samples=12, ao_distance=0.05)
    wf.location, wr.location = FW, RW
    box = delivery_box()
    pm = V.flat_image(f"M_{A}_Plate", V.tex("plate_moto.png"), 0.45)
    plate = V.quad(A + "_Plate", 0.21, 0.115, pm, (0, 0.917, 0.52), (-0.25, 0, math.pi))  # 받침과 평행 (뒤·위를 봄)
    for o in (wf, wr, box, plate, st):
        o.parent = b
    # 주차 각: 내린 자세로 만들어 접었으므로 -STAND_FOLD. 발판 바닥이 z=0 에 닿는지 확인
    deploy = -STAND_FOLD
    gap = min((Matrix.Rotation(deploy, 4, 'X') @ v.co).z for v in st.data.vertices) + HINGE[2]
    assert abs(gap) < 0.002, f"스탠드 발판이 바닥에서 {gap:.4f} m"
    deg = math.degrees(deploy)
    for nm, loc in (("Seat", (0, 0.20, 0.86)), ("Grip_L", (0.33, -0.40, 1.05)), ("Grip_R", (-0.33, -0.40, 1.05)),
                    ("Foot", (0, -0.10, 0.43)), ("Exhaust", (-0.17, 0.88, 0.395))):
        V.empty(f"{A}_Socket_{nm}", loc, b)
    if FAST:
        k3d.preview(A, [b], views=((55, 15), (230, 12), (90, 0)), tag="wip")
        return
    notes = ("배달 스쿠터. 정면 -Y. 원점 바닥 중앙. DeliveryScooter_WheelFront/WheelRear: 원점=차축, 로컬 X 축 회전. "
             "DeliveryScooter_Box: 배달통 (M_DeliveryScooter_BoxSide '버거대왕' 로고 / BoxBack '배달앱 주문 전용', 굽지 않은 이미지). "
             "번호판 '서울 중구 바 5821'(가상). 엔진·쇼크는 왼쪽(+X), 머플러·Socket_Exhaust 는 오른쪽(-X). "
             "전조등 = 크롬 반사경 + 전구(구운 발광) + M_Glass_DeliveryScooter_Lens. "
             f"DeliveryScooter_Stand: 센터 스탠드, 원점 = 경첩 (로컬 X 축). 기본(identity) = 접힘(주행). "
             f"주차 시 로컬 X 회전 {deg:.1f}° (Blender rotation_euler.x, Unity localEulerAngles.x 도 같은 값 = {deg % 360:.1f}) 이면 발판이 바닥에 닿음. "
             "라이더 없음 — Socket_Seat(앉는 점), Grip_L/R, Foot, Exhaust. 약 12.6k tris (몸체 9.2k, 8k 예산 초과).")
    k3d.export(A, "Vehicles", [b], notes=notes)
    k3d.preview(A, [b])
    k3d.preview(A, [b], views=((65, 10),), lens=35, tag="fp")
    k3d.preview(A, [b], views=((180, 4),), tag="back")
    st.rotation_euler.x = deploy  # 내보낸 뒤: 주차 자세 확인용 렌더
    k3d.preview(A, [b], views=((90, 2),), tag="parked")
    print(f"STAND_DEPLOY_DEG {deg:.2f}")


main()

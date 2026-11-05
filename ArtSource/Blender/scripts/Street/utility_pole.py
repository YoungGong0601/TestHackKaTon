# StreetUtilityPole: 한국형 콘크리트 전신주(지상 9.8 m) + 완철·애자·주상변압기·통신 함체·발판볼트·전단지.
# StreetWires: 전주 사이 25 m 경간의 처진 전선 (같은 스크립트, 같은 부착 좌표).
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d, bpy
from mathutils import Vector, Matrix

R = random.Random(9)
A = "StreetUtilityPole"
H = 9.8                      # 지상 높이
RB, RT = 0.19, 0.12          # 밑동/꼭대기 반지름 (10 m 급 PC 전주)
Z1, Z2 = 9.35, 8.75          # 완철 높이 (고압 / 저압·중성선)
INS = 0.30                   # 애자 높이
SPAN = 25.0                  # StreetWires 경간


def pr(z):
    return RB + (RT - RB) * z / H


def bar(name, p1, p2, w, t, mat, bevel=0.002):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    return S.box(name, (w, t, d.length), (p1 + p2) / 2, d.to_track_quat('Z', 'Y').to_euler(), mat, bevel)


def rod(name, p1, p2, r, mat, seg=8, bevel=0.0):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    return S.cyl(name, r, d.length, p1, d.to_track_quat('Z', 'Y').to_euler(), mat, seg=seg, bevel=bevel)


def ring(name, z, h, mat, extra=0.008):
    """전주를 감는 밴드 (회전체)."""
    r0, r1 = pr(z) + 0.001, pr(z) + extra
    return S.lathe(name, [(r0, z - h / 2), (r1, z - h / 2), (r1, z + h / 2), (r0, z + h / 2)], seg=32, mat=mat,
                   close=False, smooth_ang=60)


ARM_X1 = -(pr(Z1) + 0.0375)
ARM_X2 = -(pr(Z2) + 0.0375)
# 전선 부착점 (전주 로컬 좌표, StreetWires 와 공유)
HV = [(ARM_X1, -1.0, Z1 + 0.0375 + INS), (ARM_X1, 1.0, Z1 + 0.0375 + INS), (0.0, 0.0, H + 0.07 + INS)]
LV = [(ARM_X2, -0.9, Z2 + 0.0375 + 0.2), (ARM_X2, 0.9, Z2 + 0.0375 + 0.2)]
TEL = [(0.0, pr(6.45) + 0.11, 6.47), (0.0, pr(6.45) + 0.11, 6.37), (0.0, pr(6.45) + 0.16, 6.42)]


def insulator(name, base, mat_p, mat_g, tall=INS):
    """라인포스트 애자: 아연 받침 + 갓 5단 자기 + 머리 홈."""
    x, y, z = base
    parts = [S.cyl(name + "_F", 0.034, 0.05, (x, y, z), mat=mat_g, seg=12, bevel=0.003)]
    prof = [(0.0, 0.05)]
    zz = 0.05
    for i in range(5):
        prof += [(0.028, zz), (0.064, zz + 0.012), (0.060, zz + 0.022), (0.028, zz + 0.03)]
        zz += 0.04
    prof += [(0.028, tall - 0.06), (0.032, tall - 0.05), (0.032, tall - 0.02), (0.022, tall - 0.012),
             (0.030, tall - 0.004), (0.0, tall)]
    parts.append(S.lathe(name + "_P", [(r, z + h) for r, h in prof], seg=14, loc=(x, y, 0), mat=mat_p, smooth_ang=55))
    return parts


def build_pole():
    tex_png, rect = S.atlas("T_StreetUtilityPole_Decals")
    conc_ph = k3d.polyhaven("concrete_floor_03", "1k")["diff"]
    conc = S.concrete("M_SUP_Conc", (0.40, 0.39, 0.37), streaks=0.75, streak_col=(0.13, 0.12, 0.10), bottom=1.0,
                      bottom_h=0.55, bottom_col=(0.11, 0.09, 0.07), ph=conc_ph, ph_scale=1.3, ph_mix=0.7, grime=0.5,
                      var=0.16, vscale=1.2, bump=0.4)
    steel = S.galv("M_SUP_Galv", 0.5, rust=0.45, rust_scale=12, streaks=0.4)
    sheet = S.wmat("M_SUP_Sheet", (0.55, 0.56, 0.54), 0.6, 0.0, var=0.1, grime=0.7, bump=0.9, bump_scale=55,
                   streaks=0.5, bottom=0.0)
    porc = S.wmat("M_SUP_Porcelain", (0.50, 0.52, 0.52), 0.18, 0.0, var=0.06, grime=0.9, grime_dist=0.03,
                  streaks=0.5, streak_col=(0.18, 0.16, 0.13), bump=0.03)
    tank = S.paint("M_SUP_Tank", (0.30, 0.32, 0.31), 0.55, edge=0.7, edge_col=(0.12, 0.06, 0.03), edge_metal=0.2,
                   rust=0.5, rust_scale=6, streaks=0.9, streak_col=(0.12, 0.06, 0.03), grime=0.6)
    pvc = S.wmat("M_SUP_Pvc", (0.33, 0.34, 0.33), 0.55, 0.0, var=0.08, grime=0.6, streaks=0.6, bottom=0.8,
                 bottom_h=0.4)
    blk = S.rubber("M_SUP_Cable")
    box_m = S.paint("M_SUP_Box", (0.36, 0.37, 0.36), 0.5, rust=0.3, rust_scale=10, streaks=0.6)
    decal = S.decal_mat("M_StreetUtilityPole_Decals", tex_png, 0.7, alpha_clip=True)

    P = []
    # 전주 몸통 (테이퍼 + 둥근 머리)
    prof = [(0.0, 0.0), (RB, 0.0)] + [(pr(z), z) for z in (0.02, 0.6, 1.2, 2.0, 3.0, 4.5, 6.0, 7.5, 8.6, 9.2, H - 0.02)]
    prof += [(RT * 0.92, H + 0.025), (RT * 0.6, H + 0.06), (0.0, H + 0.07)]
    P.append(S.lathe(A + "_Shaft", prof, seg=32, mat=conc, smooth_ang=60))

    # 광고물 부착방지 시트 (오돌토돌한 플라스틱) 1.15~2.45 m
    P.append(S.lathe(A + "_Sheet", [(pr(1.15) + 0.0045, 1.15), (pr(1.16) + 0.006, 1.16), (pr(2.44) + 0.006, 2.44),
                                    (pr(2.45) + 0.0045, 2.45)], seg=32, mat=sheet, close=False))
    for z in (1.17, 2.43):
        P.append(ring(A + "_SheetBand%.2f" % z, z, 0.022, steel, 0.009))

    # 발판볼트: 2.6 m 부터 0.45 m 간격, 좌우 번갈아
    z, i = 2.6, 0
    while z < 8.5:
        a = (math.pi / 2 if i % 2 else -math.pi / 2) + R.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        p1 = Vector((0, 0, z)) + d * (pr(z) - 0.02)
        p2 = Vector((0, 0, z)) + d * (pr(z) + 0.20)
        P.append(rod(A + "_Step%d" % i, p1, p2, 0.009, steel, seg=8))
        P.append(rod(A + "_StepTip%d" % i, p2 - d * 0.008, p2 - d * 0.008 + Vector((0, 0, 0.035)), 0.008, steel, 8))
        P.append(S.cyl(A + "_StepNut%d" % i, 0.016, 0.012, p1 + d * 0.02, d.to_track_quat('Z', 'Y').to_euler(),
                       steel, seg=6, bevel=0.001))
        z += 0.45
        i += 1

    # 완철 2단 + 밴드 + 암타이
    for k, (zz, ax, half) in enumerate(((Z1, ARM_X1, 1.15), (Z2, ARM_X2, 1.05))):
        P.append(S.box(A + "_Arm%d" % k, (0.075, half * 2, 0.075), (ax, 0, zz), mat=steel, bevel=0.004))
        P.append(ring(A + "_ArmBand%d" % k, zz, 0.06, steel, 0.012))
        P.append(S.box(A + "_ArmBolt%d" % k, (0.05, 0.06, 0.03), (ax + 0.05, 0, zz), mat=steel, bevel=0.003))
        for s in (-1, 1):
            P.append(bar(A + "_Brace%d%d" % (k, s), (ax, s * half * 0.55, zz - 0.04), (-pr(zz - 0.55) - 0.01, s * 0.05, zz - 0.55),
                         0.045, 0.007, steel))
        P.append(ring(A + "_BraceBand%d" % k, zz - 0.55, 0.05, steel, 0.011))
    # 애자: 고압 완철 양 끝 + 전주 머리, 저압 완철에는 작은 핀애자 2개
    for k, (x, y, zt) in enumerate(HV):
        P += insulator(A + "_InsHV%d" % k, (x, y, zt - INS), porc, steel)
    P.append(S.cyl(A + "_TopPin", 0.05, 0.03, (0, 0, H + 0.04), mat=steel, seg=12, bevel=0.003))
    for k, (x, y, zt) in enumerate(LV):
        P += insulator(A + "_InsLV%d" % k, (x, y, zt - 0.2), porc, steel, tall=0.2)

    # 주상변압기 (-X 쪽, 6.9~7.85 m) + 행거 + 부싱 + 리드선
    tx, tz = -(pr(7.4) + 0.34), 6.9
    P.append(S.cyl(A + "_Tank", 0.26, 0.82, (tx, 0, tz), mat=tank, seg=32, bevel=0.008))
    P.append(S.cyl(A + "_TankLid", 0.275, 0.05, (tx, 0, tz + 0.82), mat=tank, seg=32, bevel=0.01))
    P.append(S.cyl(A + "_TankBase", 0.24, 0.04, (tx, 0, tz - 0.03), mat=tank, seg=32, bevel=0.006))
    for k in range(12):  # 냉각 리브
        a = 2 * math.pi * k / 12
        if math.cos(a) > 0.8 or math.sin(a) < -0.8:
            continue  # 전주 쪽, 표시판 쪽은 비움
        P.append(S.box(A + "_Rib%d" % k, (0.05, 0.012, 0.62), (tx + math.cos(a) * 0.275, math.sin(a) * 0.275, tz + 0.41),
                       (0, 0, a), tank, 0.003))
    for k, zz in enumerate((tz + 0.2, tz + 0.65)):
        P.append(ring(A + "_TankBand%d" % k, zz, 0.06, steel, 0.012))
        P.append(S.box(A + "_Hanger%d" % k, (0.2, 0.08, 0.05), (-pr(zz) - 0.09, 0, zz), mat=steel, bevel=0.004))
    for s in (-1, 1):
        bx, by, bz = tx + 0.05, s * 0.12, tz + 0.87
        P.append(S.lathe(A + "_Bush%d" % s, [(0.0, bz), (0.04, bz), (0.042, bz + 0.02), (0.022, bz + 0.03),
                                             (0.04, bz + 0.05), (0.022, bz + 0.065), (0.036, bz + 0.085),
                                             (0.018, bz + 0.1), (0.012, bz + 0.14), (0.0, bz + 0.14)],
                         seg=12, loc=(bx, by, 0), mat=porc))
        hv = Vector(HV[0 if s < 0 else 1])
        top = Vector((bx, by, bz + 0.14))
        mid = (top + hv) / 2 + Vector((-0.15, 0, -0.25))
        P.append(S.tube(A + "_Lead%d" % s, [top, top + Vector((0, 0, 0.1)), mid, hv], 0.006, 6, blk))
    for k in range(3):  # 저압 부싱 + 인출선
        by = -0.12 + k * 0.12
        p0 = Vector((tx - 0.27, by, tz + 0.6))
        P.append(S.cyl(A + "_LvBush%d" % k, 0.022, 0.06, p0, (0, -math.pi / 2, 0), porc, seg=10))
        lv = Vector(LV[0 if by < 0 else 1])
        P.append(S.tube(A + "_LvLead%d" % k, [p0 + Vector((-0.06, 0, 0)), p0 + Vector((-0.2, 0, 0.3)),
                                              (p0 + lv) / 2 + Vector((-0.2, 0, 0.1)), lv], 0.007, 6, blk))

    # 통신 행거 (+Y 쪽 6.3~6.5 m) + 여장 케이블 코일 (5.0 m) + 단자함 (4.2 m) + 입상관
    tz2 = 6.42
    P.append(ring(A + "_TelBand", tz2, 0.05, steel, 0.012))
    P.append(S.box(A + "_TelHanger", (0.05, 0.2, 0.22), (0, pr(tz2) + 0.1, tz2), mat=steel, bevel=0.004))
    for k, (x, y, z) in enumerate(TEL):
        P.append(S.cyl(A + "_TelClamp%d" % k, 0.03, 0.06, (x - 0.03, y, z), (0, math.pi / 2, 0), blk, seg=10))
    coil_c = Vector((0.0, pr(5.0) + 0.05, 5.0))
    for t in range(3):
        pts = []
        for k in range(29):
            a = 2 * math.pi * k / 28
            pts.append(coil_c + Vector((math.cos(a) * (0.28 + t * 0.012), 0.02 + t * 0.018, -0.3 + math.sin(a) * 0.3)))
        P.append(S.tube(A + "_Coil%d" % t, pts, 0.008, 6, blk, caps=False))
    P.append(ring(A + "_CoilBand", 5.0, 0.04, steel, 0.01))
    P.append(S.tube(A + "_CoilUp", [coil_c + Vector((0, 0.03, 0.0)), coil_c + Vector((0.02, 0.06, 0.8)),
                                    Vector((0, pr(6.3) + 0.11, 6.3)), Vector(TEL[1])], 0.008, 6, blk))
    # 단자함 + 입상관은 전단지가 없는 뒤 오른쪽(135°, 도로 쪽)에 둔다 — 전단지·안내문을 가리지 않게
    ca = math.radians(135)
    rz = lambda v: Matrix.Rotation(ca, 3, 'Z') @ Vector(v)
    bxp = Vector((0, 0, 4.25)) + rz((0.0, -(pr(4.25) + 0.085), 0.0))   # 아래 발판볼트(3.95 m)와 겹치지 않게
    P.append(S.box(A + "_TermBox", (0.34, 0.15, 0.5), bxp, (0, 0, ca), mat=box_m, bevel=0.006))
    P.append(S.box(A + "_TermLid", (0.36, 0.02, 0.06), bxp + rz((0, -0.01, 0.27)), (0, 0, ca), mat=box_m, bevel=0.004))
    P.append(S.box(A + "_TermLatch", (0.03, 0.02, 0.05), bxp + rz((0.12, -0.085, 0.0)), (0, 0, ca), mat=steel, bevel=0.003))
    for zz in (4.05, 4.45):
        P.append(ring(A + "_TermBand%.2f" % zz, zz, 0.035, steel, 0.009))
    # 입상관 (단자함 아래 ~ 지면) + 고정 밴드
    cpos = lambda z: Vector((math.sin(ca) * (pr(z) + 0.03), -math.cos(ca) * (pr(z) + 0.03), z))
    P.append(S.tube(A + "_Conduit", [cpos(0.0), cpos(1.0), cpos(2.5), cpos(3.6), cpos(4.03)],
                    0.024, 10, pvc))
    for zz in (0.6, 2.6, 3.5):
        P.append(ring(A + "_CondBand%.1f" % zz, zz, 0.025, steel, 0.008))
        P.append(S.box(A + "_CondStrap%.1f" % zz, (0.07, 0.035, 0.026), cpos(zz) + rz((0, -0.006, 0)),
                       (0, 0, ca), steel, 0.004))

    # 데칼: 반사띠 4조각, 번호찰, 고압 경고, 광고물 금지, 전단지 4장, 스티커, 찢긴 자국, 변압기 표시
    def W(key, z0, h, ang0, ang1, off=0.006, frac=None, bulge=0.0, seg=10, center=(0, 0), radius=None):
        u0, v0, u1, v1 = rect[key]
        if frac:
            u1 = u0 + (u1 - u0) * frac[1]
            u0 = u0 + (rect[key][2] - rect[key][0]) * frac[0]
        rr = (radius if radius is not None else pr(z0 + h / 2)) + off
        P.append(S.wrap_decal(A + "_D_" + key + "%.2f" % z0, rr, z0, h, ang0, ang1, (u0, v0, u1, v1), decal, seg,
                              center, None, bulge))
    for q in range(4):
        W("hazard", 0.35, 0.32, q * math.pi / 2, (q + 1) * math.pi / 2, 0.002, (q * 0.24, q * 0.24 + 0.24), seg=8)
    W("plate", 2.75, 0.36, -0.68, 0.68, 0.003)
    W("hv", 3.25, 0.2, -0.85, 0.85, 0.003)
    W("notice", 2.12, 0.2, -1.0, 1.0, 0.009)
    W("flyer_room", 1.62, 0.3, -0.62, 0.58, 0.012, bulge=0.003)
    W("flyer_dog", 1.48, 0.3, 0.95, 2.15, 0.012, bulge=0.003)
    W("flyer_move", 1.7, 0.3, -2.3, -1.1, 0.012, bulge=0.003)
    W("flyer_academy", 1.42, 0.3, 2.55, 3.75, 0.012, bulge=0.003)
    W("residue", 1.25, 0.16, -0.7, 0.0, 0.010)
    W("st_loan", 3.55, 0.08, 0.4, 1.4, 0.003)
    W("st_key", 1.0, 0.09, -1.5, -0.8, 0.003)
    # 변압기 용량 표시 (탱크 정면 -Y 쪽)
    W("trans", tz + 0.25, 0.32, -0.5, 0.5, 0.0, center=(tx, 0), radius=0.262)

    body = S.join(P, A + "_Body")
    k3d.set_origin(body, (0, 0, 0))
    return body, decal


k3d.reset()
body, decal = build_pole()
k3d.bake(body, 2048, keep=("M_StreetUtilityPole_Decals",), samples=32)
socks = {"Flyers": (0, -(pr(1.7) + 0.02), 1.7), "WireHV": (ARM_X1, 0, Z1), "WireLV": (ARM_X2, 0, Z2),
         "WireTel": TEL[1], "Transformer": (-(pr(7.4) + 0.34), 0, 7.3)}
for k, v in socks.items():
    S.empty(A + "_Socket_" + k, v, parent=body)
notes = ("높이 9.8 m(+애자 0.37 m). 원점 = 지면 중앙. 정면 -Y(Unity +Z) = 보도 쪽: 테이프 전단지·'광고물 부착 금지' 안내·번호찰이 "
         "이쪽을 보므로 정면을 보도(걷는 사람) 쪽으로 돌려 놓는다. 단자함·입상관·통신 케이블은 뒤(도로 쪽)에 있다. "
         "완철은 Y 방향(Y 대칭), 전선은 X 방향으로 "
         "뻗는다: StreetWires 를 같은 위치/회전에 놓고 다음 전주를 로컬 +X 25 m 에 두면 애자에 정확히 붙는다. "
         "Socket: Flyers(전단지 보기 시선 대상 1.7 m), WireHV/WireLV/WireTel(전선 높이), Transformer. "
         "데칼(M_StreetUtilityPole_Decals, alpha clip 0.5): 전단지 4장·광고물 금지 안내·번호찰·고압 경고·반사띠·스티커.")
S.finish(A, [body], 9.0, notes, fp=dict(dist=2.6, look_h=1.9, az=15))

# ------------------------------------------------------------------ StreetWires
k3d.reset()
W_ = "StreetWires"
cond = S.flat("M_StreetWires_Conductor", (0.42, 0.43, 0.43), 0.42, 1.0)
cab = S.flat("M_StreetWires_Cable", (0.018, 0.018, 0.019), 0.55)
clo = S.wmat("M_StreetWires_Closure", (0.03, 0.03, 0.03), 0.6, 0.0, grime=0.5, streaks=0.6, bump=0.1)


def sag_pts(p0, p1, sag, n=28, sway=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for k in range(n + 1):
        t = k / n
        p = p0.lerp(p1, t)
        p.z -= 4 * sag * t * (1 - t)
        p.y += sway * math.sin(math.pi * t)
        out.append(p)
    return out


wires = []
for k, p in enumerate(HV):
    q = (p[0] + SPAN, p[1], p[2])
    wires.append(S.tube(W_ + "_HV%d" % k, sag_pts(p, q, 0.42 + 0.03 * k), 0.0075, 6, cond))
for k, p in enumerate(LV):
    q = (p[0] + SPAN, p[1], p[2])
    wires.append(S.tube(W_ + "_LV%d" % k, sag_pts(p, q, 0.5 + 0.04 * k), 0.009, 6, cab))
for k, p in enumerate(TEL):
    q = (p[0] + SPAN, p[1], p[2])
    wires.append(S.tube(W_ + "_Tel%d" % k, sag_pts(p, q, 0.75 + 0.08 * k, sway=0.03 * k), [0.012, 0.009, 0.016][k], 6, cab))
# 통신 접속함 (전주 옆 1.8 m 지점 케이블에 매달림) + 케이블 타이
t2 = sag_pts(TEL[2], (TEL[2][0] + SPAN, TEL[2][1], TEL[2][2]), 0.91)
cp = t2[2]
wires.append(S.cyl(W_ + "_Closure", 0.075, 0.58, cp - Vector((0.29, 0, 0.09)), (0, math.pi / 2, 0), clo, seg=16, bevel=0.01))
for dx in (-0.25, 0.25):
    wires.append(S.cyl(W_ + "_ClosureRing%+.2f" % dx, 0.079, 0.03, cp + Vector((dx - 0.015, 0, -0.09)), (0, math.pi / 2, 0),
                       clo, seg=16, bevel=0.004))
root = S.join(wires, W_ + "_Lines")
k3d.set_origin(root, (0, 0, 0))
k3d.bake(root, 256, keep=("M_StreetWires_Conductor", "M_StreetWires_Cable"), samples=8)
notes = ("경간 25 m 전선 묶음. 원점 = 시작 전주(StreetUtilityPole) 원점과 같은 지면 위치, 전선은 로컬 +X 로 25 m. "
         "고압 3가닥(처짐 0.42~0.48 m), 저압 2가닥, 통신 3가닥(처짐 0.75~0.91 m) + 통신 접속함. "
         "다른 경간 길이는 X 스케일로 맞춘다(가는 선이라 비균일 스케일 무방). 바닥(min_z)이 0 이 아닌 것은 의도(공중 전선).")
S.finish(W_, [root], None, notes, views=((20, 25), (100, 8)))

# 할아버지 지팡이 — 갈색 알루미늄 높이조절 지팡이 (오프셋 손잡이 + 고무 그립, 조절 구멍·푸시버튼, 잠금 링, 손목끈, 고무 팁)
import sys, math
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ik as ik, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "Cane"
MM = 0.001
R_LO, R_UP = 9.5 * MM, 11.0 * MM
ZG = 0.866            # 그립 축 높이


def outward(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o


def lathe(name, prof_mm, mat, n=40):
    return outward(ik.lathe(name, [(r * MM, h * MM) for r, h in prof_mm], n=n, mat=mat))


# ---------------------------------------------------------------- 머티리얼
def scratches(g, base, rough, obj):
    # 길이 방향 헤어라인 + 드문 가로 긁힘 (맨 알루미늄이 드러남)
    mp = g.n('ShaderNodeMapping')
    g.link(g.coord('Object'), mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (1.0, 1.0, 0.02)
    hair = g.noise(1800, 2, 0.5, mp.outputs[0])
    rough = g.math('ADD', rough, g.math('MULTIPLY', g.math('SUBTRACT', hair, 0.5), 0.12))
    sc = g.ramp(g.wave(160, g.coord('Object'), 'Z', 1.2, 1), 0.965, 1.0)
    sc = g.math('MULTIPLY', sc, g.ramp(g.noise(5, 3, 0.5, obj), 0.55, 0.72))
    base = g.mix(g.math('MULTIPLY', sc, 0.8), base, ik.srgb("#bdb6aa"))
    return base, g.lerp(sc, rough, 0.22)


alu = ik.P("M_tmp_alu", "#5e4a3a", rough=0.3, metal=1.0, var=0.03, vs=10, grime=0.45, gd=0.004, gcol="#2a2018",
           edge=0.5, ed=0.0012, ecol="#b5aa98", erough=0.25, smudge=0.25, dust=0.5, dz=0.28, dcol="#7a6f60",
           bump=0.03, bs=900, bd=0.00004, extra=scratches)
hole_m = ik.P("M_tmp_hole", "#0e0c0a", rough=0.6, var=0.0)
steel = ik.P("M_tmp_steel", "#b4b4b0", rough=0.22, metal=1.0, var=0.04, grime=0.5, gd=0.0015, gcol="#3a3a36")
plast = ik.P("M_tmp_plastic", "#1b1a19", rough=0.5, var=0.06, vs=30, grime=0.35, gd=0.003, edge=0.4, ed=0.0008,
             ecol="#4a4846", dust=0.25, dz=0.5, bump=0.05, bs=1600, bd=0.00003)


def palm(g, base, rough, obj):
    # 손바닥 닿는 윗면은 반들반들 (거칠기 낮고 살짝 밝음)
    up = g.ramp(g.sep(g.coord('Object'))[2], ZG + 0.004, ZG + 0.014)
    base = g.mix(g.math('MULTIPLY', up, 0.35), base, ik.srgb("#4a3c32"))
    return base, g.lerp(up, rough, 0.42)


grip_m = ik.P("M_tmp_grip", "#2b2420", rough=0.72, var=0.07, vs=20, grime=0.5, gd=0.003, gcol="#0c0a08",
              smudge=0.2, bump=0.25, bk='voronoi', bs=900, bd=0.00012, extra=palm)
rubber = ik.P("M_tmp_rubber", "#151414", rough=0.86, var=0.06, vs=25, grime=0.5, gd=0.003, edge=0.3, ed=0.001,
              ecol="#3a3734", dust=0.85, dz=0.012, dcol="#6a6152", bump=0.2, bs=700, bd=0.00008)
cord = ik.P("M_tmp_cord", "#1e1e22", rough=0.72, var=0.08, vs=60, grime=0.3, gd=0.002, bump=0.4, bk='cloth',
            bs=2600, bd=0.00006)

parts = []
# ---------------------------------------------------------------- 고무 팁 (바닥 오목, 링 3줄)
tip = lathe(A + "_Tip", [(0.0, 0.9), (6.0, 0.6), (11.5, 0.15), (13.0, 0.0), (13.8, 0.8), (14.1, 2.5), (14.0, 4.6),
                         (13.2, 5.6), (13.3, 7.2), (12.5, 9.0), (12.1, 12.0), (12.5, 13.2), (12.5, 14.2), (11.9, 15.2),
                         (11.7, 21.5), (12.1, 22.7), (12.1, 23.7), (11.6, 24.7), (11.4, 31.0), (11.8, 32.2),
                         (11.8, 33.2), (11.3, 34.2), (11.1, 39.8), (10.6, 41.2), (9.7, 41.7), (0.0, 41.7)], rubber, 40)
tip.data.set_sharp_from_angle(angle=math.radians(55))
parts.append(tip)

# 아래 관 (Ø19) + 조절 구멍 11개 (앞쪽) + 푸시버튼
lo = ik.cyl(A + "_Lower", R_LO, 0.47 - 0.03, loc=(0, 0, 0.03), mat=alu, n=32, bev=0.0003)
parts.append(lo)


def hole(zc, rad=2.0 * MM, n=12):
    """관 표면에 붙인 어두운 구멍 (곡면 따라)."""
    bm = bmesh.new()
    rr = R_LO + 0.05 * MM
    def on(dx, dz):
        ph = -math.pi / 2 + dx / R_LO
        return bm.verts.new((rr * math.cos(ph), rr * math.sin(ph), zc + dz))
    c = on(0, 0)
    ring = [on(rad * math.cos(2 * math.pi * k / n), rad * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        bm.faces.new((c, ring[k], ring[(k + 1) % n]))
    bm.normal_update()
    o = ik.mesh_obj(A + "_Hole", bm, hole_m)
    for f in o.data.polygons:
        if f.normal.y > 0:
            f.flip()
    return o


holes_z = [0.18 + 0.025 * k for k in range(11)]
for z in holes_z[:-1]:
    parts.append(hole(z))
btn = lathe(A + "_Button", [(0.0, 2.3), (1.0, 2.1), (1.7, 1.5), (2.05, 0.6), (2.1, -1.0), (0.0, -1.0)], steel, 20)
btn.rotation_euler = (math.pi / 2, 0, 0)
btn.location = (0, -R_LO, holes_z[-1])
parts.append(btn)

# 잠금 링 (검정 플라스틱, 홈 4줄)
col = lathe(A + "_Collar", [(9.6, 438), (11.9, 438), (12.6, 439.2), (12.6, 443), (12.25, 443.6), (12.6, 444.2),
                            (12.6, 447.4), (12.25, 448.0), (12.6, 448.6), (12.6, 451.8), (12.25, 452.4), (12.6, 453),
                            (12.6, 467), (12.1, 470.5), (11.6, 472.6), (11.15, 473.2)], plast, 40)
col.data.set_sharp_from_angle(angle=math.radians(45))
parts.append(col)


# ---------------------------------------------------------------- 위 관 (Ø22) + 오프셋 손잡이 굽힘
def hermite(p0, m0, p1, m1, n):
    out = []
    for i in range(n + 1):
        t = i / n
        h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        out.append(tuple(h00 * a + h10 * b + h01 * c + h11 * d for a, b, c, d in zip(p0, m0, p1, m1)))
    return out


yz = [(0.0, 0.462), (0.0, 0.60), (0.0, 0.70)]
yz += hermite((0.0, 0.74), (0.0, 0.11), (-0.045, 0.832), (0.0, 0.11), 12)
yz += hermite((-0.045, 0.832), (0.0, 0.05), (-0.020, ZG), (0.05, 0.0), 10)[1:]
yz += [(0.02, ZG - 0.0005), (0.05, ZG - 0.0012), (0.068, ZG - 0.0016)]
upper = ik.tube(A + "_Upper", [(0.0, y, z) for y, z in yz], R_UP, 24, alu)
parts.append(upper)

# 그립 (고무, 손바닥 쪽 불룩) — Z 회전체를 +Y 방향으로 눕힘
gp = lathe(A + "_Grip", [(0.0, -14.0), (11.6, -14.0), (12.8, -13.0), (13.4, -10.5), (13.6, 0.0), (14.6, 20.0),
                         (15.3, 38.0), (15.1, 56.0), (14.6, 70.0), (14.2, 78.5), (13.6, 81.5), (12.2, 84.6),
                         (9.0, 87.0), (4.5, 88.2), (0.0, 88.5)], grip_m, 40)
gp.rotation_euler = (-math.pi / 2, 0, 0)
gp.location = (0, -0.012, ZG)
parts.append(gp)

# 손목끈: 관에 끼운 클립 + 고리 끈 + 조임 구슬
clip = lathe(A + "_Clip", [(10.9, 728), (12.0, 728), (12.4, 729), (12.4, 741), (12.0, 742), (10.9, 742)], plast, 32)
lug = ik.box(A + "_Lug", (6.0 * MM, 9.0 * MM, 10.0 * MM), loc=(0, 0.0155, 0.735), mat=plast, bev=0.0008, seg=2)
parts += [clip, lug]
loop = [(0.0, 0.019, 0.733), (0.004, 0.024, 0.715), (0.007, 0.032, 0.69), (0.009, 0.040, 0.66),
        (0.008, 0.044, 0.635), (0.004, 0.043, 0.618), (0.0, 0.038, 0.612), (-0.004, 0.032, 0.617),
        (-0.007, 0.026, 0.632), (-0.007, 0.022, 0.66), (-0.005, 0.020, 0.69), (-0.002, 0.019, 0.715),
        (0.0, 0.019, 0.733)]
def catmull(pts, k=6):
    out = []
    n = len(pts) - 1
    for i in range(n):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
        if i == 0:
            p0 = pts[-2]
        if i + 2 > n:
            p3 = pts[1]
        for j in range(k):
            t = j / k
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t +
                                    (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    return out + [pts[-1]]


strap = ik.tube(A + "_Strap", catmull(loop), 2.0 * MM, 8, cord, cap=False)
bead = ik.cyl(A + "_Bead", 3.2 * MM, 7 * MM, loc=(0.0005, 0.0215, 0.709), rot=(0.12, 0, 0), mat=plast, n=16,
              bev=0.0008)
parts += [strap, bead]

for o in parts:
    if not any(m.type == 'WEIGHTED_NORMAL' for m in o.modifiers):
        o.modifiers.new("WN", 'WEIGHTED_NORMAL').keep_sharp = True

body = ik.join(parts, A + "_Body")
k3d.set_origin(body, Vector((0, 0, 0)))
k3d.bake(body, 1024, ao_distance=0.01, samples=24)

ik.socket(A + "_Socket_Grip", (0, 0.028, ZG), body)
ik.socket(A + "_Socket_Tip", (0, 0, 0), body)

notes = ("지팡이 0.03x0.15x0.882m (그립 윗면), 원점 = 고무 팁 바닥 중앙(땅 닿는 점), 정면(-Y)=손잡이 굽은 쪽(걷는 방향). "
         "갈색 아노다이징 알루미늄 높이조절형: 아래 관 Ø19 (조절 구멍 + 푸시버튼), 검정 잠금 링, 위 관 Ø22 오프셋 손잡이, "
         "고무 그립, 손목끈 클립/고리, 고무 팁(바닥 흙먼지). 정적 메시 1개 (Cane_Body, 1024 bake). "
         "Socket_Grip = 손바닥 중심 (프로토타입 gripCane 포즈), Socket_Tip = cane_tap 소리 낼 접지점.")
k3d.export(A, ik.CAT, [body], notes=notes)
k3d.preview(A, [body], res=(900, 1200))
k3d.preview(A, [body], views=((90, 10),), res=(900, 1200), tag='side')
L = (('SUN', (0, 0, 3), 3.0, (1, 0.97, 0.92), 0.5), ('POINT', (-0.4, -0.5, 1.2), 25.0, (0.8, 0.85, 1.0), 0.3))
ik.shot(ik.PREV + "/Cane_handle_0.png", (0.26, -0.34, 1.0), (0, 0.015, 0.84), lens=50, res=(1200, 900), lights=L, world=0.6)
ik.shot(ik.PREV + "/Cane_tip_0.png", (0.16, -0.22, 0.2), (0, 0, 0.08), lens=50, res=(1200, 900), lights=L, world=0.6)

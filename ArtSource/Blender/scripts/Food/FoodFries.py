# 감자튀김: 앞이 파인 브랜드 인쇄 종이 상자 + 낱개 감자튀김 (프로토타입 fries 높이 0.14m)
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

A = "FoodFries"
ZT = 0.112          # 상자 뒤판 높이
T = 0.0005          # 판지 두께
textures()
k3d.reset()
rnd = random.Random(21)


def hx(z): return 0.031 + 0.015 * z / ZT       # 반폭: 아래 6.2cm -> 위 9.2cm
def hy(z): return 0.0155 + 0.0105 * z / ZT     # 반깊이: 아래 3.1cm -> 위 5.2cm
def pw(z): return 7.0 - 3.6 * z / ZT           # 초타원 지수: 아래는 각지고 위는 둥글게


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def top(t):
    """둘레 각 t(0=+X 옆, -90도=앞) 의 윗단 높이: 앞판 가운데가 파이고 옆은 V 로 낮다."""
    c, s = math.cos(t), math.sin(t)
    zt = 0.083 + 0.024 * c * c if s < 0 else ZT - 0.004 * c * c
    d = min(abs(wrap(t)), abs(wrap(t - math.pi)))
    return zt - 0.011 * math.exp(-(d / 0.22) ** 2)


def se(t, z):
    c, s, p = math.cos(t), math.sin(t), pw(z)
    return hx(z) * math.copysign(abs(c) ** (2 / p), c), hy(z) * math.copysign(abs(s) ** (2 / p), s)


# ---------------------------------------------------------------- 머티리얼: 상자 겉 (인쇄)
s = Sh(f"M_{A}_Print", "#b5271c", .45)
x, y, z = s.xyz()
nx, ny, nzz = s.xyz(s.tc('Normal'))
w2 = s.math('MULTIPLY', s.math('ADD', .031, s.math('MULTIPLY', z, .015 / ZT)), 2)
v = s.math('DIVIDE', z, ZT)
cf = s.image(os.path.join(TEX, "fries_front.png"), s.comb(s.math('ADD', s.math('DIVIDE', x, w2), .5), v, 0), ext='EXTEND')
cb = s.image(os.path.join(TEX, "fries_back.png"), s.comb(s.math('SUBTRACT', .5, s.math('DIVIDE', x, w2)), v, 0), ext='EXTEND')
red = s.ramp(s.noise(40, 4, .55), [(.3, "#a8231a"), (.7, "#bb2b1f")])
band = s.math('MULTIPLY', s.math('GREATER_THAN', z, .00565), s.math('LESS_THAN', z, .00682))
col = s.mix(red, "#e2a72e", band)                                   # 옆판: 빨강 + 금색 띠
col = s.mix(col, cf, s.mr(ny, -.72, -.88))                          # 앞판 인쇄
col = s.mix(col, cb, s.mr(ny, .72, .88))                            # 뒷판 인쇄
scuff = s.math('MULTIPLY', s.mr(z, .0045, .0005), s.mr(s.noise(120, 3, .6), .45, .62))
col = s.mix(col, "#d9b3a4", s.math('MULTIPLY', scuff, .45))          # 바닥 모서리 긁혀 흰 속지
corner = s.mr(s.math('ABSOLUTE', s.math('MULTIPLY', nx, ny)), .25, .45)
col = s.mix(col, "#c98a7c", s.math('MULTIPLY', corner, s.mr(s.noise(300, 2, .6), .6, .72, 0, .3)))  # 접힌 모서리 닳음
grease = s.math('MULTIPLY', s.mr(s.noise(9, 3, .6, vec=s.vmath('ADD', s.tc(), (.2, .4, 0))), .6, .68), s.mr(z, .05, .09))
col = s.mix(col, "#6e1510", s.math('MULTIPLY', grease, .55))        # 위쪽 기름 스밈
col = s.mix(col, "#2a0806", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.01)), .45))
fold = s.math('MULTIPLY', s.mr(s.math('ABSOLUTE', y), .0012, 0), s.mr(s.math('ABSOLUTE', nx), .8, .95))  # 옆판 가운데 접힘선
smudge = s.mr(s.noise(22, 3, .6, dist=1.2), .56, .7)                 # 손자국 (광택)
rough = s.math('ADD', s.mr(s.noise(70, 2, .5), .3, .7, .38, .5), s.math('ADD', s.math('MULTIPLY', grease, -.18), s.math('MULTIPLY', smudge, .12)))
nrm = s.bump(s.math('ADD', s.math('MULTIPLY', s.noise(900, 2, .5), .35), s.math('MULTIPLY', fold, -1.5)), .25, .0004)
MP = s.out(col, rough, nrm)

# 상자 안쪽 (흰 판지 + 기름)
s = Sh(f"M_{A}_Inside", "#ece4d4", .8)
x, y, z = s.xyz()
col = s.mix("#e4dccb", "#cdbfa4", s.noise(30, 3, .5))
col = s.mix(col, "#c39a55", s.math('MULTIPLY', s.mr(s.noise(12, 3, .6), .56, .66), .6))
col = s.mix(col, "#4a3a28", s.mr(z, .02, .09, .55, 0))
MI = s.out(col, s.mr(s.noise(40, 2, .5), .3, .7, .55, .8), s.bump(s.noise(700, 2, .5), .15, .0003))

# 감자튀김
s = Sh(f"M_{A}_Fry", "#e2b04e", .45)
fr, fe, cap = s.attr("fr"), s.attr("fe"), s.attr("cap")
base = s.ramp(s.math('ADD', fr, s.math('MULTIPLY', s.math('SUBTRACT', s.noise(60, 3, .5), .5), .5)),
              [(0, "#f0cd73"), (.35, "#e8b44e"), (.7, "#d9973a"), (1, "#bf7a28")])
base = s.mix(base, "#ad6720", s.math('MULTIPLY', s.mr(s.noise(170, 4, .6), .6, .74), .3))       # 갈색 반점 (드물게)
base = s.mix(base, "#a35d1d", s.math('MULTIPLY', fe, s.mr(fr, 0, 1, .2, .7)))                   # 끝이 더 튀겨짐
base = s.mix(base, "#f2dc9e", s.math('MULTIPLY', cap, .85))                                     # 자른 단면
salt = s.math('MULTIPLY', s.math('LESS_THAN', s.voronoi(700), .075), s.mr(s.noise(25, 2, .5), .5, .62))
base = s.mix(base, "#fff6e0", s.math('MULTIPLY', salt, .55))                                     # 소금 알갱이
base = s.mix(base, "#5e3a14", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.006)), .22))
rough = s.math('ADD', s.mr(s.noise(90, 2, .5), .3, .7, .3, .48), s.math('MULTIPLY', salt, .3))
MF = s.out(base, rough, s.bump(s.math('ADD', s.noise(450, 3, .6), s.math('MULTIPLY', salt, .5)), .3, .0002))

# ---------------------------------------------------------------- 상자 (둘레 띠를 위로 쌓고 바닥을 막음)
NP, NL = 48, 12
ts = [-math.pi / 2 + 2 * math.pi * k / NP for k in range(NP)]
bm = bmesh.new()
rings = []
for j in range(NL + 1):
    f = j / NL
    ring = []
    for t in ts:
        zz = top(t) * f
        px, py = se(t, zz)
        dent = .0005 * nz(px * 60, py * 60, zz * 60) * min(1, zz / .01)
        rr = math.hypot(px, py)
        ring.append(bm.verts.new((px + px / rr * dent, py + py / rr * dent, zz)))
    rings.append(ring)
for a, b in zip(rings, rings[1:]):
    for k in range(NP):
        bm.faces.new((a[k], a[(k + 1) % NP], b[(k + 1) % NP], b[k]))
c0 = bm.verts.new((0, 0, 0))
for k in range(NP):
    bm.faces.new((rings[0][(k + 1) % NP], rings[0][k], c0))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.normal_update()
fr_face = min(bm.faces, key=lambda fc: (fc.calc_center_median() - Vector((0, -.03, .05))).length)
if fr_face.normal.y > 0:  # 바깥을 향하게
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
box = mesh_obj(f"{A}_Box", bm)
mats(box, MP, MI)
solidify(box, T, -1, 1, 1)
bevel(box, .0012, 2, 40)
smooth(box, 35)


# ---------------------------------------------------------------- 낱개 감자튀김
def inside(p, m):
    """p 가 상자 안쪽(벽에서 m 이상 떨어짐)인가. 윗단보다 높으면 검사 안 함."""
    if p.z > top(math.atan2(p.y / hy(max(p.z, 0)), p.x / hx(max(p.z, 0)))) + .002:
        return True
    if p.z < .004 + m:
        return False
    q = pw(p.z)
    return (abs(p.x) / (hx(p.z) - T - m)) ** q + (abs(p.y) / (hy(p.z) - T - m)) ** q < 1


def fry_mesh(bm, p0, p1, h, asp, bend, twist, fr):
    d = (p1 - p0)
    L = d.length
    tdir = d.normalized()
    ux = Vector((1, 0, 0))
    u = (ux - tdir * ux.dot(tdir)).normalized()
    u = Matrix.Rotation(twist, 3, tdir) @ u
    w = tdir.cross(u)
    q = .74
    sec = [(1, -q), (1, q), (q, 1), (-q, 1), (-1, q), (-1, -q), (-q, -1), (q, -1)]
    rows = [(0, .72, -.0004), (0, 1, 0), (.5, 1, 0), (1, 1, 0), (1, .72, .0004)]
    rings = []
    for (t, sc, ext) in rows:
        c = p0 + d * t + bend * math.sin(math.pi * t) + tdir * ext
        rings.append([bm.verts.new(c + (u * a * h * asp + w * b * h) * sc) for a, b in sec])
    for A_, B_ in zip(rings, rings[1:]):
        for k in range(8):
            bm.faces.new((A_[k], A_[(k + 1) % 8], B_[(k + 1) % 8], B_[k]))
    for ring, sgn in ((rings[0], -1), (rings[-1], 1)):
        cv = bm.verts.new(sum((vv.co for vv in ring), Vector()) / 8 + tdir * sgn * .0003)
        for k in range(8):
            bm.faces.new((ring[k], ring[(k + 1) % 8], cv) if sgn > 0 else (ring[(k + 1) % 8], ring[k], cv))
    return L


fries, samples = [], []
tries = 0
while len(fries) < 48 and tries < 150000:
    tries += 1
    z0 = rnd.uniform(.012, .05)
    p0 = Vector((rnd.uniform(-1, 1) * hx(z0), rnd.uniform(-1, 1) * hy(z0), z0))
    h = rnd.uniform(.0033, .0039)
    m = h * 1.25
    if not inside(p0, m):
        continue
    xn, yn = p0.x / hx(z0), p0.y / hy(z0)
    wild = .32 if rnd.random() < .2 else .14  # 몇 개는 크게 기울어짐
    dvec = Vector((xn * .34 + rnd.uniform(-wild, wild), yn * .28 - .05 + rnd.uniform(-wild, wild) * .8, 1)).normalized()  # 바깥으로 부채꼴
    L = rnd.uniform(.065, .1)
    p1 = p0 + dvec * L
    if not (.095 < p1.z < .145 - .012 * max(0, -yn)):  # 앞쪽은 조금 낮게
        continue
    perp = dvec.cross(Vector((0, 0, 1)))
    perp = (perp if perp.length > 1e-4 else Vector((1, 0, 0))).normalized()
    bend = Matrix.Rotation(rnd.uniform(0, 6.28), 3, dvec) @ perp * rnd.uniform(.004, .010)
    pts = [p0 + (p1 - p0) * (i / 15) + bend * math.sin(math.pi * i / 15) for i in range(16)]
    if not all(inside(p, m) for p in pts):
        continue
    vis = [p for p in pts if p.z > .074]
    if any((p - q).length < (h + qh) * .88 for p in vis for (q, qh) in samples):
        continue
    samples += [(p, h) for p in vis]
    fries.append((p0, p1, h, rnd.uniform(.88, 1.1), bend, rnd.uniform(0, 1.6), rnd.random()))
print(f"FoodFries: fries={len(fries)} tries={tries}")

bm = bmesh.new()
attr_rows = []
for (p0, p1, h, asp, bend, tw, frv) in fries:
    n0 = len(bm.verts)
    fry_mesh(bm, p0, p1, h, asp, bend, tw, frv)
    attr_rows.append((n0, len(bm.verts), frv, p0, p1))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
fo = mesh_obj(f"{A}_Sticks", bm)
me_ = fo.data
for nm in ("fr", "fe", "cap"):
    me_.attributes.new(nm, 'FLOAT', 'POINT')
for (a0, a1, frv, p0, p1) in attr_rows:
    d = p1 - p0
    for i in range(a0, a1):
        co = me_.vertices[i].co
        t = max(0.0, min(1.0, (co - p0).dot(d) / d.length_squared))
        me_.attributes["fr"].data[i].value = frv
        me_.attributes["fe"].data[i].value = max(0.0, (abs(t - .5) * 2 - .55) / .45) ** 1.5
    # 링 5개 x 8정점 + 캡 중심 2개: 끝 링 0.7, 캡 중심 1 -> 자른 단면만 연한 색
    for i in list(range(a0, a0 + 8)) + list(range(a0 + 32, a0 + 40)):
        me_.attributes["cap"].data[i].value = 0.7
    for i in (a1 - 2, a1 - 1):
        me_.attributes["cap"].data[i].value = 1.0
mats(fo, MF)
smooth(fo, 60)
fo.modifiers.new("WN", 'WEIGHTED_NORMAL').keep_sharp = True  # 넓은 면은 평평, 모서리만 둥글게
for o in (box,):
    for nm in ("fr", "fe", "cap"):
        const_attr(o, nm, 0.0)

me = join([box, fo], f"{A}_Mesh")
k3d.bake(me, size=2048, samples=48)
socket(me, A, "Grip", (0, 0, .045))
socket(me, A, "LookTarget", (0, 0, .11))
k3d.export(A, "Food", [me], notes={
    "desc": f"감자튀김 (버거대왕 빨간 종이 상자 + 낱개 감자튀김 {len(fries)}개). 상자 아래 6.2x3.1cm, 위 9.2x5.2cm, 뒤판 높이 0.112m, "
            "감자튀김 포함 높이 약 0.14m. 앞판(-Y) 가운데가 파여 있고 '프렌치 프라이' 인쇄, 뒷판 '사이드는 왕의 친구'. 원점 바닥 중앙.",
    "sockets": {f"{A}_Socket_Grip": "손으로 쥐는 중심", f"{A}_Socket_LookTarget": "감자튀김 윗부분 (시선 타깃)"}})
k3d.preview(A, [me])
k3d.preview(A, [me], views=((0, 30),), lens=35, tag='fp')

# 포장지에 싼 불고기 버거: 버거 모양 퍽(평평한 바닥 + 세로 띠 + 위 돔, 옆 주름) + 윗면 덮개 종이(경계 단차) + 접어 올린 덮개 3장 + 체크 패널('불고기' 펜 체크) + 기름 얼룩
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

A = "FoodBurgerWrapped"
RW, HW = 0.058, 0.0641
TILE = 0.09                                  # 포장지 무늬 1장 = 9cm (로고 한 칸 2.2cm)
NU = 4                                       # 옆면 둘레 = 정확히 4장 (이음매 없음, 옆에서 가로세로 비율 ~1)
RTOP = 0.041                                 # 윗면 덮개 종이 경계 반지름 (안쪽만 평면 투영)
FLAPS = [(math.radians(-98), .017, .9), (math.radians(30), .027, -.6), (math.radians(150), .026, .35)]  # (방향, 가장자리 거리, 무늬 회전)
PC, PW, PH, PR = (.002, .012), .052, .030, math.radians(6)   # 체크 패널 중심/크기/회전
textures()
k3d.reset()
rnd = random.Random(31)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


pleats = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(.03, .07), rnd.uniform(.5, 1.0)) for _ in range(13)]


def pleat(a):
    """옆 주름: 각도별 날카로운 능선 + 옆의 얕은 골."""
    v = 0.0
    for (a0, w, amp) in pleats:
        d = wrap(a - a0)
        v += amp * (math.exp(-(d / w) ** 2) - .5 * math.exp(-(d / (w * 2.2)) ** 2))
    return v


# ---------------------------------------------------------------- 종이 머티리얼
s = Sh(f"M_{A}_Paper", "#f5ecd8", .6)
x, y, z = s.xyz()
nx, ny, nzz = s.xyz(s.tc('Normal'))
r = s.vmath('LENGTH', s.comb(x, y, 0))
pat = os.path.join(TEX, "wrap_pattern.png")


def rot(vec, eul):
    nd = s.n('ShaderNodeVectorRotate', rotation_type='EULER_XYZ')
    s.put(nd.inputs['Vector'], vec)
    nd.inputs['Rotation'].default_value = eul
    return nd.outputs['Vector']


def edge(dist, w=.00025):
    """dist>0 쪽이 1 인 날카로운 경계 (반투명 겹침 없음)."""
    return s.mr(dist, -w, w)


# 옆면: 원통 투영, 세로는 단면 호 길이(mer 속성)라 어깨에서도 늘어나지 않음
uside = s.math('MULTIPLY', s.math('DIVIDE', s.math('ADD', s.math('ARCTAN2', y, x), math.pi), 2 * math.pi), NU)
cside = s.image(pat, s.comb(uside, s.math('DIVIDE', s.attr("mer"), TILE), 0))
# 윗면 덮개 종이: 평면 투영, 손으로 접은 6각 경계 (날카로운 단차)
ctop = s.image(pat, s.comb(s.math('DIVIDE', x, TILE), s.math('DIVIDE', y, TILE), 0))
wob = s.math('MULTIPLY', s.math('SUBTRACT', s.noise(9, 2, .5), .5), .005)
ext = None
for k in range(6):  # 윗면 덮개 종이 경계 = 손으로 접은 6각 (내접 반지름 RTOP, 각도 흔들림)
    th = math.radians(60 * k + 15 + rnd.uniform(-10, 10))
    d_ = s.math('ADD', s.math('MULTIPLY', x, math.cos(th)), s.math('MULTIPLY', y, math.sin(th)))
    ext = d_ if ext is None else s.math('MAXIMUM', ext, d_)
dtop = s.math('SUBTRACT', s.math('ADD', RTOP, wob), ext)
tm = s.math('MULTIPLY', edge(dtop), s.attr("pan"))
col = s.mix(cside, ctop, tm)
step = tm
shade = s.math('MULTIPLY', s.mr(dtop, -.003, 0), s.math('SUBTRACT', 1, tm))   # 덮개 종이 밖으로 지는 그림자
for (ang, c, rt) in FLAPS:  # 윗면에 접어 올린 덮개: 다른 각도로 놓인 무늬, 자른 가장자리 단차, 아래 종이에 지는 그림자
    dd = s.math('SUBTRACT', s.math('ADD', s.math('MULTIPLY', x, math.cos(ang)), s.math('MULTIPLY', y, math.sin(ang))), c)
    dd = s.math('ADD', dd, s.math('MULTIPLY', s.math('SUBTRACT', s.noise(30, 2, .5), .5), .0025))   # 손으로 접은 살짝 휜 가장자리
    m = s.math('MULTIPLY', edge(dd), tm)
    ru = s.math('ADD', s.math('MULTIPLY', x, math.cos(rt)), s.math('MULTIPLY', y, math.sin(rt)))
    rv = s.math('SUBTRACT', s.math('MULTIPLY', y, math.cos(rt)), s.math('MULTIPLY', x, math.sin(rt)))
    cf = s.image(pat, s.comb(s.math('DIVIDE', s.math('ADD', ru, .013), TILE), s.math('DIVIDE', s.math('ADD', rv, .029), TILE), 0))
    col = s.mix(col, cf, m)
    sh = s.math('MULTIPLY', s.math('MULTIPLY', s.mr(dd, -.003, 0), s.math('SUBTRACT', 1, m)), tm)
    shade = s.math('MAXIMUM', shade, sh)
    step = s.math('ADD', step, m)
col = s.mix(col, "#5a4a36", s.math('MULTIPLY', s.math('POWER', shade, 3), .45))
# 체크 패널 (몸통 윗면에만: pan 속성) — 맨 위 종이에 인쇄
dx, dy = s.math('SUBTRACT', x, PC[0]), s.math('SUBTRACT', y, PC[1])
pu = s.math('ADD', s.math('DIVIDE', s.math('ADD', s.math('MULTIPLY', dx, math.cos(PR)), s.math('MULTIPLY', dy, math.sin(PR))), PW), .5)
pv = s.math('ADD', s.math('DIVIDE', s.math('SUBTRACT', s.math('MULTIPLY', dy, math.cos(PR)), s.math('MULTIPLY', dx, math.sin(PR))), PH), .5)
pimg = os.path.join(TEX, "wrap_panel.png")
pcol = s.image(pimg, s.comb(pu, pv, 0), ext='CLIP')
pa = s.math('MULTIPLY', s.image(pimg, s.comb(pu, pv, 0), ext='CLIP', out='Alpha'), tm)
col = s.mix(col, pcol, pa)
step = s.math('MULTIPLY', step, s.math('SUBTRACT', 1, pa))
# 기름 스밈 (아래쪽 + 몇 군데), 종이 주름 사이 때
grease = s.math('MAXIMUM', s.math('MULTIPLY', s.mr(s.noise(7, 3, .6, vec=s.vmath('ADD', s.tc(), (.5, .2, 0))), .56, .64), s.mr(z, .03, .008)),
                s.math('MULTIPLY', s.mr(s.noise(11, 3, .6, vec=s.vmath('ADD', s.tc(), (.1, .7, 0))), .64, .7), .8))
col = s.mix(col, s.mix(col, "#b07c30", .7, 'MULTIPLY'), grease)
col = s.mix(col, "#6b5a40", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.006)), .45))
# 구김: 늘린 좌표의 능선 노이즈(|n-.5|) 두 겹 = 방향성 있는 긴 직선 주름 (닫힌 세포 무늬 없음)
wr = 0.0
for (eul, sc, w) in (((.4, 1.1, .2), 22, .035), ((1.3, -.5, 2.2), 30, .03)):
    v = s.vmath('MULTIPLY', rot(s.tc(), eul), (1, 1, 5))
    n = s.noise(sc, 2, .45, vec=v)
    rg = s.mr(s.math('ABSOLUTE', s.math('SUBTRACT', n, .5)), 0, w, 1, 0)
    wr = rg if isinstance(wr, float) else s.math('MAXIMUM', wr, rg)
# 옆 주름 능선을 따라 어깨에서 내려오는 굵은 접힘선 (가장 큰 주름 5개)
folds = 0.0
for (a0, w_, amp) in sorted(pleats, key=lambda p: -p[2])[:5]:
    perp = s.math('ABSOLUTE', s.math('SUBTRACT', s.math('MULTIPLY', x, math.sin(a0)), s.math('MULTIPLY', y, math.cos(a0))))
    fl = s.math('MULTIPLY', s.mr(perp, 0, .0009, 1, 0),
                s.math('GREATER_THAN', s.math('ADD', s.math('MULTIPLY', x, math.cos(a0)), s.math('MULTIPLY', y, math.sin(a0))), 0))
    folds = fl if isinstance(folds, float) else s.math('MAXIMUM', folds, fl)
folds = s.math('MULTIPLY', s.math('MULTIPLY', folds, s.mr(z, .018, .05)), s.math('SUBTRACT', 1, tm))
rough = s.math('ADD', s.mr(s.noise(60, 2, .5), .3, .7, .55, .68), s.math('MULTIPLY', grease, -.3))
nrm = s.bump(s.math('ADD', s.math('ADD', s.math('MULTIPLY', wr, .5), s.math('MULTIPLY', folds, .8)),
                    s.math('ADD', s.math('MULTIPLY', s.noise(600, 3, .5), .2), s.math('MULTIPLY', step, 1.5))), .3, .0004)
MP = s.out(col, rough, nrm)

# ---------------------------------------------------------------- 몸통 (평평한 바닥 + 세로 띠 + 위 돔, 주름)
prof = [(0, 0), (.046, 0), (.0525, .0004), (.0558, .0018), (.0574, .0045), (.058, .009), (.0582, .016), (.0583, .024),
        (.058, .031), (.0572, .037), (.0556, .0425), (.053, .0475), (.049, .052), (.0435, .0563), (.0365, .0597),
        (.028, .0621), (.019, .0634), (.0095, .064), (0, HW)]
SEG = 96
S = [0.0]
for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
    S.append(S[-1] + math.hypot(r1 - r0, z1 - z0))


def rf(a, i, r, z):
    amp = .02 * math.exp(-((z - .008) / .008) ** 2) + .014 * math.exp(-((z - .05) / .008) ** 2) + .004
    return 1 + .022 * math.cos(4 * (a - .3)) + amp * pleat(a) + .004 * nz(math.cos(a) * 3, math.sin(a) * 3, z * 40)


def zf(a, i, r, z):
    top = max(0.0, (z - .047) / .017)
    return top * (-.0014 * pleat(a + .2) * (r / RW) ** 2 + .0012 * nz(r * math.cos(a) * 50, r * math.sin(a) * 50, 3))


body = lathe(f"{A}_Body", prof, SEG, rf, zf)
nv = len(body.data.vertices)
mer = body.data.attributes.new("mer", 'FLOAT', 'POINT')
for v in body.data.vertices:  # 정점 번호 -> 단면 링 -> 호 길이
    ring = 0 if v.index == 0 else (len(prof) - 1 if v.index == nv - 1 else 1 + (v.index - 1) // SEG)
    mer.data[v.index].value = S[ring]
mats(body, MP)
smooth(body, 70)
vattr(body, "pan", lambda co: 1.0 if co.z > .035 else 0.0)  # 윗면만 덮개 종이/체크 패널 (바닥에 거울상으로 찍히지 않게)

me = join([body], f"{A}_Mesh")
k3d.bake(me, size=2048, samples=48)
socket(me, A, "Grip", (0, 0, .035))
socket(me, A, "LookTarget", (PC[0], PC[1], HW + .001))
k3d.export(A, "Food", [me], notes={
    "desc": "버거대왕 포장지에 싼 불고기 버거 (포장 주문/픽업대용). 지름 약 0.118m, 높이 약 0.065m, 원점 바닥 중앙, 정면 -Y. "
            "윗면 체크 패널에 '불고기' 펜 체크, 옆 주름과 접힘선, 윗면 덮개 종이 + 접어 올린 덮개 3장(텍스처 단차), 기름 얼룩.",
    "sockets": {f"{A}_Socket_Grip": "손으로 쥐는 중심", f"{A}_Socket_LookTarget": "윗면 체크 패널 (시선 타깃)"}})
k3d.preview(A, [me])
k3d.preview(A, [me], views=((0, 50),), lens=35, tag='fp')
k3d.preview(A, [me], views=((90, 30), (180, 30), (270, 30), (0, 12)), tag='review')

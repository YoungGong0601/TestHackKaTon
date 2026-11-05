# 진동벨(호출벨): 둥근 퍽 몸통 + 옆 LED 링(따로, 발광) + 윗면 번호 스티커(M_Dyn, 런타임 번호 교체) + 바닥 고무링/충전단자/나사
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

A = "FoodPager"
R, H = 0.048, 0.0243
SR, SZ = 0.025, 0.0236     # 스티커 반지름, 높이 (홈 바닥 0.0234 위 0.2mm)
textures()
k3d.reset()

# ---------------------------------------------------------------- 몸통 머티리얼 (굽기)
s = Sh(f"M_{A}_Shell", "#242629", .3)
x, y, z = s.xyz()
nx, ny, nzz = s.xyz(s.tc('Normal'))
r = s.vmath('LENGTH', s.comb(x, y, 0))
topm, botm = s.mr(nzz, .6, .9), s.mr(nzz, -.6, -.9)
col = s.mix("#2a2c30", "#1c1e21", s.noise(30, 3, .5))
pa = s.image(os.path.join(TEX, "pager_print.png"), s.comb(s.math('ADD', s.math('DIVIDE', x, 2 * R), .5),
                                                         s.math('ADD', s.math('DIVIDE', y, 2 * R), .5), 0), ext='CLIP', out='Alpha')
ink = s.math('MULTIPLY', s.math('MULTIPLY', pa, topm), s.mr(s.noise(220, 2, .5), .3, .7, .7, 1))   # 인쇄 살짝 닳음
col = s.mix(col, "#e9e0cf", ink)
wear = s.math('MULTIPLY', s.mr(s.geo('Pointiness'), .545, .6), s.mr(s.noise(90, 3, .6), .45, .6))
col = s.mix(col, "#5d6066", s.math('MULTIPLY', wear, .55))                               # 모서리 닳음
foot = s.math('MULTIPLY', s.math('MULTIPLY', s.math('GREATER_THAN', r, .0349), s.math('LESS_THAN', r, .0447)), s.math('LESS_THAN', z, .0011))
col = s.mix(col, "#121212", foot)                                                        # 고무 링
pad = s.math('ADD', *[s.math('LESS_THAN', s.vmath('DISTANCE', s.comb(x, y, 0), (sx, 0, 0)), .0032) for sx in (-.012, .012)])
pad = s.math('MULTIPLY', pad, botm)
screws = []
for k in range(3):  # 십자 나사 3개
    a = math.radians(90 + 120 * k)
    c = (.024 * math.cos(a), .024 * math.sin(a), 0)
    dv = s.vmath('SUBTRACT', s.comb(x, y, 0), c)
    dx, dy, _ = s.xyz(dv)
    head = s.math('LESS_THAN', s.vmath('LENGTH', dv), .0021)
    slot = s.math('MULTIPLY', s.math('MAXIMUM', s.math('LESS_THAN', s.math('ABSOLUTE', dx), .00028),
                                     s.math('LESS_THAN', s.math('ABSOLUTE', dy), .00028)), s.math('LESS_THAN', s.vmath('LENGTH', dv), .0014))
    screws.append((head, slot))
head = s.math('MULTIPLY', s.math('ADD', s.math('ADD', screws[0][0], screws[1][0]), screws[2][0]), botm)
slot = s.math('MULTIPLY', s.math('ADD', s.math('ADD', screws[0][1], screws[1][1]), screws[2][1]), botm)
col = s.mix(col, "#d6b25e", pad)                                                         # 금도금 충전 단자
col = s.mix(col, "#8b8e93", head)
col = s.mix(col, "#1a1a1a", slot)
col = s.mix(col, "#0c0d0e", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.004)), .6))   # 홈/틈 때
smudge = s.mr(s.noise(11, 3, .55, dist=1.5), .56, .7)                                   # 지문 얼룩 (적고 크게)
scr = s.mr(s.wave(500, 14, direction='DIAGONAL', detail=3), .95, 1)                      # 잔 흠집
rough = s.math('ADD', s.math('ADD', s.mr(nzz, .6, .9, .38, .28), s.math('MULTIPLY', smudge, .07)), s.math('MULTIPLY', scr, .05))
rough = s.math('ADD', rough, s.math('MULTIPLY', foot, .5))  # 고무는 무광
metal = s.math('ADD', pad, head)
nrm = s.bump(s.math('ADD', s.math('ADD', s.math('MULTIPLY', s.noise(2600, 1, .5), s.mr(nzz, .6, .9, .25, .02)),
                                  s.math('MULTIPLY', slot, -.6)), s.math('MULTIPLY', scr, .15)), .3, .0002)
MS_ = s.out(col, rough, nrm, metal)

# ---------------------------------------------------------------- 몸통 (선반)
prof = [(0, .0013), (.034, .0013), (.0345, .0009), (.0372, .0002), (.041, 0), (.0438, .0002), (.0449, .0009),
        (.0463, .0019), (.0473, .0034), (.0479, .0052), (R, .0076), (R, .0152), (.0478, .0155), (.0466, .0156),
        (.0466, .0194), (.0476, .0195), (.0478, .0199), (.0477, .0212), (.0471, .0224), (.0461, .0233), (.0447, .0239),
        (.043, .0242), (.036, H), (.0262, H), (.0258, .0240), (.0256, .0235), (.0252, .0234), (.012, .0234), (0, .0234)]
body = lathe(f"{A}_Body", prof, 72)
mats(body, MS_)
smooth(body, 40)

# ---------------------------------------------------------------- LED 링 (따로: 게임이 발광을 켜고 끔)
led = lathe(f"{A}_Led", [(.0466, .0157), (.0481, .0157), (.0485, .0166), (.0486, .0175), (.0485, .0184), (.0481, .0193),
                         (.0466, .0193), (.0466, .0157)], 72)
bm = bmesh.new()
bm.from_mesh(led.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(led.data)
bm.free()
ML = k3d.mat(f"M_{A}_Led", (.85, .85, .85), .22, emission=hexc("#ff3a22")[:3], strength=4.0)  # 꺼지면 우윳빛 확산판
mats(led, ML)
smooth(led, 50)

# ---------------------------------------------------------------- 번호 스티커 (M_Dyn: UV 0-1 = 스티커 지름 정사각형, U 오른쪽 V 뒤쪽)
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
cv = bm.verts.new((0, 0, SZ))
ring = [bm.verts.new((SR * math.cos(2 * math.pi * k / 64), SR * math.sin(2 * math.pi * k / 64), SZ)) for k in range(64)]
for k in range(64):
    f = bm.faces.new((cv, ring[k], ring[(k + 1) % 64]))
    for l in f.loops:
        l[uvl].uv = (l.vert.co.x / (2 * SR) + .5, l.vert.co.y / (2 * SR) + .5)
num = mesh_obj(f"{A}_Number", bm)
MN = k3d.mat(f"M_Dyn_{A}_Number", (1, 1, 1), .32)
k3d.image_node(MN, k3d.load_image(os.path.join(TEX, "pager_sticker.png")), k3d.principled(MN).inputs['Base Color'], uv="UVMap")
mats(num, MN)

k3d.bake(body, size=1024, samples=48)
for o in (led, num):
    o.parent = body
socket(body, A, "Grip", (0, 0, .012))
socket(body, A, "Number", (0, 0, SZ + .0005))
socket(body, A, "Led", (0, -.0487, .0175))
k3d.export(A, "Food", [body], notes={
    "desc": "식당 진동벨(호출벨). 지름 0.097m(LED 포함), 높이 0.0243m, 원점 바닥 중앙, 정면 -Y. 진동은 게임에서 흔들기로 연출.",
    "dynamic": {f"{A}_Number": f"M_Dyn_{A}_Number — 윗면 원형 번호 스티커, 지름 {2 * SR:.3f}m, 텍스처 1024x1024 (기본값 '274'), "
                               "UV 0-1 이 스티커 지름 정사각형(원 밖 모서리는 안 보임), U 오른쪽 V 뒤쪽(+Y) — 정면에서 똑바로 읽힘."},
    "led": f"{A}_Led (M_{A}_Led): 옆면 LED 링, 기본 발광 빨강 x4 (호출 상태). 대기 상태는 emission 을 0 으로, 호출 시 깜박이기.",
    "sockets": {f"{A}_Socket_Grip": "손으로 쥐는 중심", f"{A}_Socket_Number": "번호 스티커 (시선 타깃)",
                f"{A}_Socket_Led": "LED 빛/호출음(pager_call) 위치"}})
k3d.preview(A, [body])
k3d.preview(A, [body], views=((0, 55),), lens=35, tag='fp')
k3d.preview(A, [body], views=((180, -60),), ground=False, tag='bottom')

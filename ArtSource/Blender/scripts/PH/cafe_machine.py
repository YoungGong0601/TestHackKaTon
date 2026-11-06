"""PH_BackShelf__Machine: 스테인리스 2그룹 에스프레소 머신. 뒤 선반과 같은 프리팹 좌표로 내보낸다.
소스 좌표는 x = Unity x, y = Unity z(앞 -y), z = Unity y(높이). 부품은 머신 중심 x 0 으로 만들고 합친 뒤 X0 로 옮긴다."""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE] + [os.path.join(HERE, "..", d) for d in ("Store", "StoreProps", "Items", "Food")]
import ph, bpy
import storelib as S
import _common as C
import _ik as ik
from mathutils import Matrix, Vector
k3d = ph.k3d

k3d.reset()
A = "PH_BackShelf__Machine"
X0 = -0.9
Z0, ZF, ZT, ZB, ZP = 0.90, 0.93, 0.985, 1.11, 1.24   # 바닥, 다리 위, 트레이 윗면, 윗몸통 아래, 위
YF, YS, YB = -0.148, 0.02, 0.117                      # 트레이 앞, 작업 공간 뒷벽, 몸통 뒤
YP, SL = -0.12, 0.022 / 0.13                          # 윗몸통 앞면 아래쪽 y, 앞면 기울기
GX, GY = 0.135, -0.04                                 # 그룹헤드 중심
RZ = 1.27                                             # 컵 받침 난간 높이

steel = C.stainless("M_tmp_Steel", rough=0.3, smudge=0.5, grime=0.5)
# 단색 재질은 굽지 않습니다. 작은 조각들이 아틀라스를 다 먹어 몸통 해상도가 떨어지기 때문입니다.
chrome = k3d.mat(f"M_{A}_Chrome", (0.78, 0.78, 0.76), 0.2, metal=1.0)
black = C.plastic("M_tmp_Black", (0.018, 0.018, 0.019), rough=0.42, wear=0.2)
green = C.powder_coat("M_tmp_Green", (0.018, 0.075, 0.042), rough=0.42, wear=0.25, grime=0.4)
white = k3d.mat(f"M_{A}_Ceramic", (0.86, 0.85, 0.81), 0.22)
red = k3d.mat("M_tmp_Needle", (0.55, 0.05, 0.03), 0.4)

parts = []
add = parts.append


def rounded(pts, rad, steps=4):
    """닫힌 다각형의 모서리를 둥글게. pts[0] 은 곧은 변 위의 점이어야 한다."""
    return [tuple(v) for v in C.fillet(pts + [pts[0]], rad, steps)[:-1]]


def prism(name, pts, u0, u1, mat, bev=0.0015):
    """(y, z) 단면을 x 방향으로 민다."""
    return ik.poly_extrude(name, pts, u1 - u0, mat, (u0, 0, 0), (math.pi / 2, 0, math.pi / 2), bev)


def spin(name, prof, at, to, mat, segs=20):
    """회전체의 축을 to 방향으로 눕혀 at 에 둔다."""
    o = C.lathe(name, prof, segs, mat, at)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(to).to_track_quat('Z', 'Y')
    return o


def panel(objs, u, z):
    """판 좌표(x 오른쪽, y 위, z 바깥)로 만든 물건을 윗몸통 경사 앞면에 붙인다."""
    M = Matrix.Translation((u, YP + SL * (z - ZB), z)) @ Matrix.Rotation(math.pi / 2 - math.atan(SL), 4, 'X')
    for o in objs:
        o.matrix_basis = M @ o.matrix_basis
        add(o)


def grate(tag, u0, u1, y0, y1, z0, z1, n):
    p = (u1 - u0) / n
    for i in range(n):
        c = u0 + (i + 0.5) * p
        add(S.boxz(f"{tag}{i}", c - 0.31 * p, c + 0.31 * p, y0, y1, z0, z1, chrome, 0))


CUP = [(0, 0), (0.02, 0), (0.0215, 0.003), (0.03, 0.014), (0.0335, 0.028), (0.0345, 0.04),
       (0.0325, 0.04), (0.031, 0.028), (0.027, 0.014), (0, 0.008)]
CUP_H = [(0.0325, 0.031), (0.046, 0.03), (0.046, 0.016), (0.028, 0.012)]


def cup(name, at, ang, s=1.0):
    at, a = Vector(at), math.radians(ang)
    add(C.lathe(name, [(r * s, z * s) for r, z in CUP], 20, white, at, 60))
    add(C.tube(name + "H", [at + Vector((r * s * math.cos(a), r * s * math.sin(a), z * s)) for r, z in CUP_H],
               0.0032 * s, 0.006 * s, white, res=1, steps=3))


def gauge(i, u, z, needle):
    R = 0.03
    ps = [C.lathe(f"Bezel{i}", [(0, 0), (R + .004, 0), (R + .004, .003), (R + .002, .008), (R - .002, .008),
                                (R - .003, .004), (0, .004)], 32, chrome),
          C.lathe(f"Dial{i}", [(0, .003), (R - .0025, .003), (R - .0025, .0052), (0, .0052)], 32, white),
          C.lathe(f"Hub{i}", [(0, .0052), (.0035, .0052), (.0035, .0075), (0, .0075)], 12, black)]
    for k in range(9):  # 눈금만 있고 글자와 숫자는 없다
        a = math.radians(225 - k * 33.75)
        ps.append(S.quad(f"Tick{i}_{k}", .0014, .0055, (.0215 * math.cos(a), .0215 * math.sin(a), .0058),
                         black, rot=(0, 0, a - math.pi / 2)))
    a = math.radians(needle)
    ps.append(S.box(f"Needle{i}", (.0016, .024, .0012), (.008 * math.cos(a), .008 * math.sin(a), .0066),
                    red, 0, rot=(0, 0, a - math.pi / 2)))
    panel(ps, u, z)


# 몸통: 뒤 덩어리, 윗몸통, ㄷ자 옆판. 옆판은 몸통보다 4 mm 도드라진다.
add(S.boxz("Core", -0.30, 0.30, YS, YB, ZF, ZB, steel, 0))
add(prism("Head", rounded([(0, ZB), (YP, ZB), (YP + SL * (ZP - ZB), ZP), (YB, ZP), (YB, ZB)], 0.014), -0.30, 0.30, steel))
side = rounded([(YB, 1.05), (YB, ZF - 0.005), (YF - 0.002, ZF - 0.005), (YF - 0.002, ZT + 0.012), (YS, ZT + 0.012),
                (YS, ZB - 0.004), (YP - 0.004, ZB - 0.004), (YP + SL * (ZP - ZB) - 0.004, ZP + 0.004), (YB, ZP + 0.004)], 0.012)
add(prism("SideL", side, -0.31, -0.30, steel, 0.002))
add(prism("SideR", side, 0.30, 0.31, steel, 0.002))
add(S.boxz("Splash", -0.30, 0.30, YS - 0.004, YS, ZT, ZB, green, 0.001))
add(S.boxz("Trim", -0.30, 0.30, YP - 0.0035, 0.0, ZB - 0.006, ZB + 0.01, chrome, 0.001))

# 드립 트레이: 검정 바닥, 앞뒤 턱, 그레이트
add(S.boxz("Tray", -0.30, 0.30, YF + 0.006, YS, ZF, 0.955, black, 0))
add(S.boxz("TrayFront", -0.30, 0.30, YF, YF + 0.012, ZF, ZT, steel, 0.002))
add(S.boxz("TrayBack", -0.30, 0.30, YS - 0.012, YS, 0.955, ZT, steel, 0.0015))
grate("Grate", -0.30, 0.30, YF + 0.012, YS - 0.012, 0.975, ZT, 30)

# 다리
foot = [(0, Z0), (0.021, Z0), (0.021, Z0 + .006), (0.016, Z0 + .012), (0.016, ZF + .002), (0, ZF + .002)]
for i, (u, y) in enumerate(((-.25, -.12), (.25, -.12), (-.25, .09), (.25, .09))):
    add(C.lathe(f"Foot{i}", foot, 16, chrome, (u, y, 0)))

# 그룹헤드와 포터필터. 손잡이는 앞으로 나오고 잠긴 것처럼 살짝 오른쪽 아래로 튼다.
hd = Vector((0.16, -1, -0.12)).normalized()
for i, s in enumerate((-1, 1)):
    gx = s * GX
    g = (gx, GY, 0)
    add(C.lathe(f"Group{i}", [(0, 1.082), (.043, 1.082), (.044, 1.086), (.044, 1.098), (.05, 1.103), (.05, ZB + .002),
                              (0, ZB + .002)], 32, chrome, g))
    add(C.lathe(f"Seal{i}", [(0, 1.08), (.0415, 1.08), (.0415, 1.084), (0, 1.084)], 32, black, g))
    add(C.lathe(f"Basket{i}", [(0, 1.05), (.016, 1.05), (.03, 1.056), (.036, 1.068), (.04, 1.07), (.04, 1.082),
                               (0, 1.082)], 32, chrome, g))
    add(C.lathe(f"SpoutHub{i}", [(0, 1.04), (.009, 1.04), (.012, 1.046), (.012, 1.052), (0, 1.052)], 16, chrome, g))
    add(C.tube(f"Spout{i}", [(gx - .022, GY, 1.03), (gx - .02, GY, 1.04), (gx, GY, 1.046), (gx + .02, GY, 1.04),
                             (gx + .022, GY, 1.03)], .0045, .008, chrome, res=1, steps=3))
    p = Vector((gx, GY, 1.072)) + hd * 0.032
    add(spin(f"Neck{i}", [(0, 0), (.009, 0), (.0095, .025), (0, .025)], p, hd, chrome, 16))
    add(spin(f"Handle{i}", [(0, .02), (.0105, .02), (.012, .026), (.0135, .05), (.0155, .078), (.0145, .09), (.008, .096),
                            (0, .096)], p, hd, black))

# 스팀봉(오른쪽): 볼 조인트, 관, 고무 손잡이, 노즐
ball = [(.013 * math.sin(i * math.pi / 6), .013 * -math.cos(i * math.pi / 6)) for i in range(7)]
p0, p1, p2 = Vector((.245, -.075, 1.098)), Vector((.255, -.09, 1.07)), Vector((.283, -.122, 1.018))
wd = (p2 - p1).normalized()
add(C.lathe("SteamBall", ball, 16, chrome, (.245, -.075, 1.1)))
add(C.tube("SteamWand", [p0, p1, p2], .0055, .03, chrome))
add(spin("SteamGrip", [(0, 0), (.0072, 0), (.0078, .003), (.0078, .028), (.0072, .031), (0, .031)], p1 + wd * .004, wd, black, 14))
add(spin("SteamTip", [(0, 0), (.0056, 0), (.0072, .006), (.0072, .016), (.004, .022), (0, .022)], p2, wd, chrome, 14))

# 온수 꼭지(왼쪽)
q1, q2 = Vector((-.25, -.09, 1.066)), Vector((-.262, -.106, 1.04))
add(C.lathe("WaterNut", [(0, 1.098), (.014, 1.098), (.014, 1.112), (0, 1.112)], 16, chrome, (-.245, -.075, 0)))
add(C.tube("WaterPipe", [Vector((-.245, -.075, 1.1)), q1, q2], .0075, .02, chrome))
add(spin("WaterTip", [(0, 0), (.0078, 0), (.0095, .004), (.0095, .012), (0, .012)], q2, (q2 - q1), chrome, 14))

# 앞면: 압력계 2개, 버튼판 2개, 노브 2개
gauge(0, -.04, 1.175, 95)
gauge(1, .04, 1.175, 60)
for i, s in enumerate((-1, 1)):
    panel([S.box(f"Keys{i}", (.105, .03, .003), (0, 0, .0015), black, .001)] +
          [C.lathe(f"Key{i}_{k}", [(0, .0025), (.0082, .0025), (.0082, .0045), (.0065, .0062), (0, .0062)], 14, chrome,
                   ((k - 1.5) * .024, 0, 0)) for k in range(4)], s * GX, 1.175)
    panel([C.lathe(f"Knob{i}", [(0, 0), (.027, 0), (.027, .004), (.022, .008), (.02, .028), (.016, .033), (.008, .034), (0, .034)],
                   24, black),
           C.lathe(f"KnobCap{i}", [(0, .033), (.0075, .033), (.0075, .036), (0, .036)], 14, chrome)], s * .245, 1.175)

# 위쪽 컵 받침: 검정 바닥에 살대, 앞뒤 턱, 난간
YD0, YD1 = -0.085, 0.104
add(S.boxz("Deck", -.29, .29, YD0 + .002, YD1 - .002, ZP, ZP + .002, black, 0))
add(S.boxz("DeckFront", -.29, .29, YD0, YD0 + .008, ZP, ZP + .005, steel, .001))
add(S.boxz("DeckBack", -.29, .29, YD1 - .008, YD1, ZP, ZP + .005, steel, .001))
grate("DeckBar", -.29, .29, YD0 + .008, YD1 - .008, ZP + .002, ZP + .005, 26)
ya, yb = YD0 + .004, YD1 - .004
add(C.tube("Rail", [(-.285, ya, RZ), (.285, ya, RZ), (.285, yb, RZ), (-.285, yb, RZ)], .0045, .02, chrome, closed=True))
for i, (u, y) in enumerate(((-.262, ya), (0, ya), (.262, ya), (-.262, yb), (0, yb), (.262, yb), (-.285, .01), (.285, .01))):
    add(C.cyl(f"Post{i}", .0035, RZ - ZP, (u, y, ZP), 10, chrome, 0))

# 컵: 위에 2단 더미 몇 개, 트레이에 쓰다 둔 잔 하나
ZC = ZP + .005
for i, (u, y, n, a) in enumerate(((-.225, .035, 2, 35), (-.145, .045, 2, 150), (-.185, -.035, 1, 250),
                                  (.05, .04, 1, 120), (.145, .04, 2, 20), (.225, .03, 2, 200), (.19, -.04, 1, 300))):
    for k in range(n):
        cup(f"Cup{i}_{k}", (u, y, ZC + k * .013), a + k * 40)
cup("TrayCup", (-GX, GY - .002, ZT), 200, .75)

src = S.join(parts, A + "_src")                # 베벨을 여기서 적용합니다
src.location.x += X0
o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src, do_unlink=True)   # 원본이 씬에 남으면 AO 굽기가 오염됩니다

vs = [(-v.co.x, v.co.z, -v.co.y) for v in o.data.vertices]
lo = [min(v[k] for v in vs) for k in range(3)]
hi = [max(v[k] for v in vs) for k in range(3)]
print("CHECK 굽기 전 Unity 범위", [round(v, 4) for v in lo], [round(v, 4) for v in hi])
for k, (a, b) in enumerate(((-1.21, -0.59), (0.9, 1.3), (-0.17, 0.12))):
    assert a - 0.004 <= lo[k] and hi[k] <= b + 0.004, (k, lo[k], hi[k])

k3d.bake(o, 1024, keep=(chrome.name, white.name), ao_distance=0.05)
print("CHECK tris", len(o.data.polygons))
ph.finish(A, o, notes="원점은 PH_BackShelf 프리팹 원점이고 선반 좌표 그대로입니다. 앞면은 Unity -Z. "
                      "범위는 x -1.21~-0.59, y 0.9~1.3, z -0.17~0.12 입니다. 바닥이 Base 윗면 y 0.9 라서 validate 의 min_z 표시는 정상입니다.")
for m in bpy.data.materials:
    m.use_backface_culling = True              # Unity 처럼 뒷면을 안 그리고 봅니다
k3d.preview(A, [o], views=((180, 12), (215, 18), (0, 12)))   # 180 이 앞면입니다
L = [(ph.at_unity(-0.9, 3.0, -1.0), 150, 3.0, (1, 0.97, 0.92))]
S.shot(A + "_eye", ph.at_unity(0.6, 1.6, -1.7), ph.at_unity(-0.9, 1.1, 0), lens=40, lights=L)
S.shot(A + "_eye2", ph.at_unity(-0.9, 1.3, -0.8), ph.at_unity(-0.9, 1.1, 0), lens=35, lights=L)

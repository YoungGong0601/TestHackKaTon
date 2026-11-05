"""PH_CoffeeCups__Set: 2회차 픽업대의 커피 2잔과 크라프트 캐리어. 왼쪽 아아 샷 추가, 오른쪽 디샥 얼음 적게.
소스 좌표는 X 오른쪽, -Y 앞, Z 위, 원점 바닥 중앙이고 Unity (x, y, z) = 소스 (x, z, y) 다.
유리는 AO 를 구운 뒤에 합친다. 먼저 합치면 벽 1mm 안쪽의 액체와 얼음이 까맣게 구워진다."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Food")]
import ph, bpy, bmesh
from mathutils import Vector, Matrix, Euler
import _food as F
k3d = ph.k3d

A = "PH_CoffeeCups__Set"
M = "M_" + A
LOGO = os.path.join(k3d.REPO, "Assets", "UI", "Kiosk", "Art", "logo_cafe.png")

CX = .065                               # 컵 중심 x
Z0, ZR, ZF = .015, .165, .018           # 컵 바닥, 입구, 안쪽 바닥
RB, RT, T = .0305, .0398, .0012         # 바닥 반지름, 입구 반지름(턱 제외), 벽 두께
WALL = (.018, .030, .0375, .0388, .040, .075, .110, .146, .1475, .149, .158, ZR - .0028)
LEVEL_L, LEVEL_R = .136, .143           # 액면 높이
ZTOP = .1585                            # 얼음 윗면 한계 (뚜껑 아래)
HX, HY, RC = .13, .07, .032             # 캐리어 반폭, 반깊이, 모서리 반지름
SEGS = 64
STICK_D, STICK_Z = .026, .066            # 컵 앞 스티커 지름, 높이


def ss(a, b, x):
    t = min(1, max(0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def outer_r(z):
    """컵 바깥 반지름. 발 위와 입구 아래에 턱이 하나씩 있어 투명해도 윤곽이 잡힌다."""
    return RB + (RT - RB) * (z - Z0) / (ZR - Z0) + .0007 * ss(.0375, .040, z) + .0007 * ss(.146, .149, z)


def inner_r(z):
    return outer_r(z) - T


def liquid_r(z):
    return inner_r(z) - .0011


def assert_inside(o):
    """액체와 얼음이 벽을 뚫으면 투명 컵이라 그대로 보인다."""
    for v in o.data.vertices:
        assert math.hypot(v.co.x, v.co.y) <= inner_r(v.co.z) - .0005 + 1e-6 and ZF < v.co.z <= ZTOP + 1e-6, (o.name, v.co[:])


def shell(prof, t):
    """윤곽선을 왼쪽(안쪽)으로 t 밀어 두께 있는 닫힌 윤곽을 만든다."""
    inn = []
    for i, p in enumerate(prof):
        a, b = prof[max(i - 1, 0)], prof[min(i + 1, len(prof) - 1)]
        dr, dz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dr, dz)
        inn.append((max(p[0] - dz / l * t, 0), p[1] + dr / l * t))
    return prof + inn[::-1] + prof[:1]


# ---------------------------------------------------------------- 재질
def coords(s):
    """part 가 180도 돌린 뒤에 구우므로 x, y 를 소스 방향으로 되돌린다."""
    x, y, z = s.xyz()
    return s.math('MULTIPLY', x, -1), s.math('MULTIPLY', y, -1), z


def kraft():
    s = F.Sh(M + "_Kraft", "#b98f5f", .85)
    x, y, z = coords(s)
    col = s.ramp(s.noise(60, 4, .5), [(.4, "#ae885c"), (.6, "#ba9568")])
    col = s.mix(col, "#7d5c3a", s.math('MULTIPLY', s.mr(s.noise(900, 2, .5), .62, .68), .35))  # 재생지 티
    size = .034
    uv = s.comb(s.math('ADD', s.math('DIVIDE', x, size), .5), s.math('ADD', s.math('DIVIDE', y, size), .5), 0)
    ink = s.math('MULTIPLY', s.image(LOGO, uv, ext='CLIP', out='Alpha'), s.math('SUBTRACT', 1, s.xyz(s.image(LOGO, uv, ext='CLIP'))[0]))
    col = s.mix(col, "#1f5b45", s.math('MULTIPLY', ink, s.mr(z, .012, .016)))                  # 가운데 도장
    return s.out(col, .9, s.bump(s.noise(700, 3, .5), .15, .0003))


def americano():
    s = F.Sh(M + "_Americano", "#140a05", .1)
    z = s.xyz()[2]
    col = s.mix("#100704", "#1c0e07", s.mr(z, LEVEL_L - .05, LEVEL_L))
    col = s.mix(col, "#6b4022", s.mr(z, LEVEL_L + .0002, LEVEL_L + .0008))                     # 벽을 탄 얇은 테두리
    return s.out(col, .1)


def latte():
    s = F.Sh(M + "_Latte", "#c99e6e", .2)
    x, y, z = s.xyz()
    cloud = s.noise(22, 3, .45, vec=s.comb(x, y, s.math('MULTIPLY', z, .5)), dist=.8)
    col = s.ramp(cloud, [(.35, "#c28f57"), (.65, "#d6ae80")])
    col = s.mix(col, "#e6cda9", s.mr(z, .07, .02, 0, .7))                                      # 아래쪽 우유
    col = s.mix(col, "#b37a42", s.mr(z, LEVEL_R - .03, LEVEL_R, 0, .5))                        # 위쪽 커피
    return s.out(col, .2)


def ice_mat(name, level, drink, rim, core):
    """액면 위는 맑은 얼음이다. 아래는 커피가 비쳐 가운데가 어둡고 가장자리가 밝다. wall 은 벽에 닿은 정도다."""
    s = F.Sh(M + name, "#dde9ee", .14)
    z = s.xyz()[2]
    clear = s.ramp(s.noise(170, 4, .55, dist=.6), [(.3, "#c6dbe2"), (.55, "#e6f0f3"), (.75, "#fbfdfd")])
    under = s.ramp(s.attr("wall"), [(.03, drink), (.2, rim), (.6, core)])
    under = s.mix(under, rim, s.math('MULTIPLY', s.mr(s.noise(90, 3, .5, dist=1.5), .5, .75), .35))   # 얼음 속 뿌연 결
    under = s.mix(drink, under, s.mr(z, level - .1, level - .02, .4, 1))                              # 깊을수록 커피에 묻힌다
    col = s.mix(clear, under, s.mr(z, level + .002, level - .001))
    return s.out(col, s.mr(s.noise(60, 3, .5), .3, .7, .08, .2), s.bump(s.noise(120, 3, .5), .25, .0006))


def sticker_mat(cx):
    s = F.Sh(f"{M}_Sticker{'L' if cx < 0 else 'R'}", "#f1e4c8", .45)
    x, y, z = coords(s)
    dx, dz = s.math('SUBTRACT', x, cx), s.math('SUBTRACT', z, STICK_Z)
    size = STICK_D * 1.25                                                                      # 원두는 그림의 56% 다
    uv = s.comb(s.math('ADD', s.math('DIVIDE', dx, size), .5), s.math('ADD', s.math('DIVIDE', dz, size), .5), 0)
    col = s.mix("#f1e4c8", s.image(LOGO, uv, ext='CLIP'), s.image(LOGO, uv, ext='CLIP', out='Alpha'))
    return s.out(col, .45)


# ---------------------------------------------------------------- 메시 (모디파이어 없음: ph.part 가 버린다)
def rrect(e, k=8):
    """캐리어 외곽을 e 만큼 안으로 줄인 둥근 사각형."""
    hx, hy, rc = HX - e, HY - e, RC - e
    out = []
    for cx, cy, a0 in ((hx - rc, hy - rc, 0), (rc - hx, hy - rc, 90), (rc - hx, rc - hy, 180), (hx - rc, rc - hy, 270)):
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            out.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return out


EDGE = ((.0012, 0), (.0003, .0004), (0, .0012), (.0008, .012), (.0016, .021), (.0024, .0245), (.0036, .0262), (.0052, .0268),
        (.0068, .0262), (.008, .0245), (.009, .0215), (.01, .0194), (.0112, .0184), (.0125, .018), (.0135, .018))
SOCKET = ((.0345, .0125), (.0358, .0131), (.0364, .0145), (.0365, .02), (.0366, .0262), (.0372, .0285), (.0385, .0298), (.0398, .03),
          (.0412, .0295), (.0424, .0277), (.0436, .0228), (.0448, .0197), (.0462, .0184), (.0472, .018), (.048, .018))


def grip(a, z):
    """구멍 벽 네 곳이 안으로 눌려 컵을 잡는다."""
    return 1 - .09 * max(0, math.cos(4 * (a - math.pi / 4))) ** 6 * ss(.014, .02, z) * (1 - ss(.027, .0295, z))


def carrier(m):
    bm = bmesh.new()

    def loft(rings):
        rings = [[bm.verts.new(p) for p in r] for r in rings]
        for a, b in zip(rings, rings[1:]):
            n = len(a)
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        bm.faces.new(rings[0])
        return rings[-1]

    angs = [2 * math.pi * i / SEGS for i in range(SEGS)]
    tops = [loft([[(x, y, z) for x, y in rrect(e)] for e, z in EDGE])]
    for cx in (-CX, CX):
        tops.append(loft([[(cx + r * grip(a, z) * math.cos(a), r * grip(a, z) * math.sin(a), z) for a in angs] for r, z in SOCKET]))
    edges = [bm.edges.get((r[i], r[(i + 1) % len(r)])) for r in tops for i in range(len(r))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0, 0, 1))   # 구멍 둘 난 평평한 판
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = F.mesh_obj("Carrier", bm)
    F.mats(o, m)
    k3d.smooth(o, 50)
    return o


def cup(cx, m, m_rim):
    prof = [(0, Z0 + .0018), (RB - .009, Z0 + .0018), (RB - .0065, Z0 + .0004), (RB - .004, Z0), (RB - .0015, Z0 + .0003), (RB - .0003, Z0 + .0014)]
    prof += [(outer_r(z), z) for z in WALL]
    cr, rr = outer_r(WALL[-1]), .0014
    prof += [(cr + rr * math.cos(a), ZR - rr + rr * math.sin(a)) for a in (-math.pi / 2 + 1.7 * math.pi * i / 9 for i in range(1, 10))]   # 말린 입구
    prof += [(inner_r(z), z) for z in reversed(WALL[1:-1])]
    prof += [(inner_r(.0205), .0205), (inner_r(.0205) - .0008, .0187), (inner_r(.0205) - .0024, ZF), (0, ZF)]
    o = F.lathe("Cup", prof, SEGS)
    F.mats(o, m, m_rim)
    F.set_mat_by(o, lambda c, n: int(c.z > ZR - .0032))    # 입구 띠는 뚜껑 재질로 진하게 해 컵 윤곽을 잡는다
    k3d.smooth(o, 50)
    o.location.x = cx
    return o


def lid(cx, m):
    prof = [(.0444, .1622), (.045, .163), (.045, .1672), (.0445, .1686), (.0428, .1693), (.0414, .1702), (.0402, .1735), (.0385, .1758),
            (.036, .1772), (.032, .1779), (.0245, .178), (.023, .1774), (.0215, .1771), (0, .1771)]
    o = F.lathe("Lid", shell(prof, .0009), SEGS)
    F.mats(o, m)
    k3d.smooth(o, 50)
    o.location.x = cx
    return o


def coffee(cx, level, m):
    a = liquid_r(.021)
    prof = [(0, ZF + .0004), (a - .0026, ZF + .0004), (a - .0009, ZF + .0009), (a, .021)]
    prof += [(liquid_r(z), z) for z in (.03, .0375, .0388, .04, .075, .11, level - .004)]
    b = liquid_r(level)
    prof += [(liquid_r(level + .0008), level + .0008), (b - .0005, level + .0003), (b - .0016, level), (0, level)]   # 벽을 타는 액면
    o = F.lathe("Coffee", prof, SEGS)
    F.mats(o, m)
    k3d.smooth(o, 60)
    assert_inside(o)
    o.location.x = cx
    return o


def ice(cx, c, size, rot, level, m):
    """둥근 상자를 벽 안쪽으로 눌러 넣는다. 액체 밖으로 조금 나온 면이 옆에서 보이는 얼음이고, 안에 묻힌 면은 버린다."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=7, use_grid_fill=True)
    h = Vector(size) / 2
    rc = .25 * min(size)
    for v in bm.verts:
        p = Vector([v.co[i] * h[i] for i in range(3)])
        q = Vector([max(rc - h[i], min(h[i] - rc, p[i])) for i in range(3)])
        p = q + (p - q).normalized() * rc
        p *= 1 + .05 * F.nz(p.x * 60 + c[0] * 50, p.y * 60 + c[1] * 50, p.z * 60 + c[2] * 80)   # 녹은 표면
        p = rot @ p + Vector(c)
        p.z = max(ZF + .0006, min(ZTOP, p.z))
        r, lim, span = math.hypot(p.x, p.y), inner_r(p.z) - .0006, .0025
        if r > lim - span:                                  # 벽에 가까울수록 눌려서 살짝 볼록한 자국이 된다
            k = (lim - span * math.exp((lim - span - r) / span)) / r
            p.x, p.y = p.x * k, p.y * k
        v.co = p
    hidden = [f for f in bm.faces if all(v.co.z < level - .0003 and math.hypot(v.co.x, v.co.y) < liquid_r(v.co.z) - .0002 for v in f.verts)]
    bmesh.ops.delete(bm, geom=hidden, context='FACES')
    if not bm.faces:
        bm.free()
        return None
    o = F.mesh_obj("Ice", bm)
    F.mats(o, m)
    F.vattr(o, "wall", lambda c: (math.hypot(c.x, c.y) - liquid_r(c.z)) / (inner_r(c.z) - .0006 - liquid_r(c.z)))   # 자르지 않아야 면 안에서 선형으로 흐른다
    k3d.smooth(o, 89)
    assert_inside(o)
    o.location.x = cx
    return o


def ice_americano(cx, m):
    rng, out = random.Random(7), []
    for i, (z, n) in enumerate(((.038, 3), (.059, 4), (.08, 4), (.101, 4), (.122, 5), (.147, 3))):
        for j in range(n):
            a = 2 * math.pi * (j + .37 * i) / n + rng.uniform(-.25, .25)
            r = inner_r(z) - rng.uniform(.006, .0095)
            size = [rng.uniform(.022, .026) for _ in range(3)]
            rot = Euler((rng.uniform(-.3, .3), rng.uniform(-.3, .3), a + rng.uniform(-.4, .4))).to_matrix()
            out.append(ice(cx, (r * math.cos(a), r * math.sin(a), z), size, rot, LEVEL_L, m))
    return out


def ice_latte(cx, m):
    rng, out = random.Random(11), []
    for deg in (100, 215, 330):
        a = math.radians(deg)
        size = [rng.uniform(.023, .026) for _ in range(3)]
        rot = Euler((rng.uniform(-.25, .25), rng.uniform(-.25, .25), a + rng.uniform(-.5, .5))).to_matrix()
        out.append(ice(cx, (.0225 * math.cos(a), .0225 * math.sin(a), .146), size, rot, LEVEL_R, m))
    return out


def straw(cx, phi, m, m_in):
    """녹색 빨대. 윗끝은 컵 중심 +1cm, 높이 0.26 이고 아래는 액체에 잠긴다. 반환: 물체, 뚜껑을 지나는 점."""
    ro, ri, ln, t = .004, .0034, .15, math.radians(3.2)
    d = Vector((math.sin(t) * math.cos(phi), math.sin(t) * math.sin(phi), math.cos(t)))
    top = Vector((cx + .01, 0, .26 - ro * math.sin(t)))
    o = F.lathe("Straw", [(ri, .001), (ro, 0), (ro, ln), (ri + .0002, ln + .0001), (ri, ln - .004), (ri, .02)], 16)
    F.mats(o, m, m_in)
    F.set_mat_by(o, lambda c, n: int(math.hypot(c.x, c.y) < ri + 1e-4))
    k3d.smooth(o, 50)
    o.matrix_world = Matrix.Translation(top) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4() @ Matrix.Translation((0, 0, -ln - .0001))
    return o, top - d * ((top.z - .178) / d.z)


def grommet(p, m):
    o = F.lathe("Grommet", shell([(.0064, .1771), (.0058, .1786), (.005, .179), (.0043, .1786), (.0043, .1771)], .0004), 32)
    F.mats(o, m)
    k3d.smooth(o, 60)
    o.location = (p.x, p.y, 0)
    return o


def sticker(cx, m):
    """앞면(-Y) 벽에 붙은 둥근 스티커. 평평한 원판을 벽 곡면으로 감는다."""
    o = F.lathe("Sticker", [(0, 0)] + [(STICK_D / 2 * i / 5, 0) for i in range(1, 6)], 32)
    me = o.data
    for v in me.vertices:
        z = STICK_Z + v.co.y
        r, a = outer_r(z) + .0003, -math.pi / 2 + v.co.x / (outer_r(z) + .0003)
        v.co = (r * math.cos(a), r * math.sin(a), z)
    me.update()
    p = me.polygons[0]
    if p.normal.y > 0:
        me.flip_normals()
    F.mats(o, m)
    k3d.smooth(o, 80)
    o.location.x = cx
    return o


def consume(parts, name, **kw):
    """ph.part 는 원본을 남긴다. 남겨 두면 AO 를 가리고 미리보기에 겹쳐 나오므로 지운다."""
    o = ph.part(name, parts, ph.turn(180), **kw)
    for p in parts:
        bpy.data.objects.remove(p, do_unlink=True)
    return o


def extent(o):
    vs = [v.co for v in o.data.vertices]
    mn, mx = [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
    return [mx[i] - mn[i] for i in (0, 2, 1)], mn, mx      # Unity x, y, z 크기


# ---------------------------------------------------------------- 조립
k3d.reset()
m_straw = F.Sh(M + "_Straw", "#1f8a5e", .28).out("#1f8a5e", .28)
m_straw_in = F.Sh(M + "_StrawIn", "#0c3a28", .5).out("#0c3a28", .5)
ice_l = ice_mat("_IceL", LEVEL_L, "#160b06", "#553623", "#2a170c")   # 대비가 크면 브라우니처럼 보인다
ice_r = ice_mat("_IceR", LEVEL_R, "#c99e6e", "#e4c9a4", "#d3ad80")

straw_l, hole_l = straw(-CX, math.radians(20), m_straw, m_straw_in)
straw_r, hole_r = straw(CX, math.radians(-25), m_straw, m_straw_in)
opaque = [carrier(kraft()), coffee(-CX, LEVEL_L, americano()), coffee(CX, LEVEL_R, latte()), straw_l, straw_r,
          sticker(-CX, sticker_mat(-CX)), sticker(CX, sticker_mat(CX))]
opaque += [o for o in ice_americano(-CX, ice_l) + ice_latte(CX, ice_r) if o]
o = consume(opaque, A)
size = extent(o)[0]
print("cafe_cups: 불투명 크기 Unity xyz", [round(v, 4) for v in size])
assert abs(size[0] - .26) < .001 and abs(size[1] - .26) < .001 and abs(size[2] - .14) < .001, size
k3d.bake(o, size=2048, samples=48, ao_distance=.03)

def glass(name, col, alpha):
    """밝은 유리는 분산광이 어두운 커피를 회색으로 띄운다. Unity 처럼 보이도록 미리보기도 뒷면을 빼고 섞는다."""
    m = k3d.flag(k3d.mat(name, col, .06, alpha=alpha), transparent=True)
    m.surface_render_method, m.use_backface_culling = 'BLENDED', True
    return m


wall = glass("M_Glass_PH_CoffeeCups", (.15, .17, .17), .12)
cover = glass("M_Glass_PH_CoffeeCups_Lid", (.28, .31, .31), .14)
g = consume([cup(-CX, wall, cover), cup(CX, wall, cover), lid(-CX, cover), lid(CX, cover), grommet(hole_l, cover), grommet(hole_r, cover)], A + "_Glass", mark=False)
o = k3d.join([o, g], A)
size, mn, mx = extent(o)
print("cafe_cups: 최종 크기 Unity xyz", [round(v, 4) for v in size], "min", [round(v, 4) for v in mn], "max", [round(v, 4) for v in mx])

ph.finish(A, o, notes="커피 2잔과 크라프트 캐리어. 앞 -Z, 원점 바닥 중앙. 왼쪽(-X) 아이스 아메리카노 샷 추가, 오른쪽(+X) 디지털 샥그라인 얼음 적게. "
                      "슬롯 0 은 구운 불투명(액체, 얼음, 빨대, 캐리어, 스티커), 슬롯 1 은 M_Glass_PH_CoffeeCups(컵 몸통), 슬롯 2 는 M_Glass_PH_CoffeeCups_Lid(뚜껑, 컵 입구 띠).")
k3d.preview(A, [o])
k3d.preview(A, [o], views=((180, 4),), lens=85, tag="side")
k3d.preview(A, [o], views=((180, 58),), tag="top")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, .115))  # 위쪽 근접 렌더용 틀 (렌더 안 됨)
frame = bpy.context.object
frame.scale, frame.hide_render = (.2, .09, .11), True
bpy.context.view_layer.update()
k3d.preview(A, [frame], views=((180, 8),), ground=False, tag="close")

"""뒤 선반 PH_BackShelf__Body (CAFE_SPLIT 6번). 숲길 커피의 바 뒤 벽에 붙는 오크 판 + 검정 철제 틀 선반.
소스 좌표: x = Unity x, y = Unity z(앞면 -y), z = Unity y(높이). 원점은 프리팹 원점(바닥 중앙).
기계 자리(x -1.25~-0.55, 높이 0.9~1.3)는 뒤판 말고 비운다. PH_BackShelf__Machine 이 같은 좌표로 들어온다."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE] + [os.path.join(HERE, "..", d) for d in ("Store", "StoreProps", "Items", "Food")]
import ph, bpy, bmesh
import storelib as S      # box, boxz, cyl, pbr, join, shot
import _common as C       # wood, powder_coat, plastic, lathe, tube
from mathutils import Vector, noise
k3d = ph.k3d

k3d.reset()
A = "PH_BackShelf__Body"
KEEP = tuple("M_" + A + n for n in ("_Dark", "_Door", "_Steel"))   # 굽지 않는 단색. 4.4 m 물건이라 아틀라스를 판과 소품에 쓴다
parts = []
add = parts.append


# ---------------------------------------------------------------- 재질
def wood(name, tint, scale=1.2, rot=None, loc=None):
    m = C.wood(name, scale, tint)
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            mp = n.inputs['Vector'].links[0].from_node
            if rot:
                mp.inputs['Rotation'].default_value = rot
            if loc:
                mp.inputs['Location'].default_value = loc
    return m


def beans(name, col):
    """병 벽에 붙은 원두: 보로노이 칸. 유리처럼 매끈하게 두어 반사로 병을 읽히게 한다."""
    m, nt, p = C.new_mat(name)
    v = C.coord(nt)
    bean = C.mix(nt, C.voronoi(nt, 60, v, out='Color'), col, tuple(c * 1.8 for c in col))
    gap = C.mrange(nt, C.voronoi(nt, 60, v, feature='DISTANCE_TO_EDGE'), .02, .12)
    nt.links.new(C.mix(nt, gap, tuple(c * .2 for c in col), bean), p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = .2
    return m


oak = wood("M_tmp_Oak", (1, .93, .82))
oak_e = wood("M_tmp_OakEdge", (.88, .78, .66), rot=(0, math.pi / 2, 0))  # 앞을 보는 면은 박스 투영 결이 세로라 돌린다
walnut = [wood("M_tmp_Walnut%d" % i, t, 1.0, loc=l) for i, (t, l) in enumerate((
    ((.40, .33, .33), (0, 0, 0)), ((.34, .28, .29), (.31, 0, .4)), ((.46, .37, .35), (.57, 0, .7))))]
kraft = S.pbr("M_tmp_Kraft", (.40, .26, .135), .78, var=.16, vscale=30, grime=.25, bump=.25, bscale=240)
gbag = S.pbr("M_tmp_GreenBag", (.018, .07, .044), .48, var=.08, grime=.25, bump=.15, bscale=200)
label = S.pbr("M_tmp_Label", (.74, .69, .58), .7, var=.03, grime=0, bump=0)
paper = S.pbr("M_tmp_Paper", (.80, .78, .72), .6, var=.03, grime=.2, bump=.04)
amber = S.pbr("M_tmp_Amber", (.22, .08, .012), .12, var=.05, grime=0, bump=0)
amber2 = S.pbr("M_tmp_Amber2", (.10, .032, .008), .12, var=.05, grime=0, bump=0)
pump = C.plastic("M_tmp_Pump", (.016, .016, .018), .4)
cream = S.pbr("M_tmp_MugCream", (.78, .72, .6), .22, var=.05, grime=.2, bump=0)
mgreen = S.pbr("M_tmp_MugGreen", (.02, .085, .055), .2, var=.05, grime=.2, bump=0)
mchar = S.pbr("M_tmp_MugChar", (.035, .035, .038), .3, var=.05, grime=.2, bump=0)
bean_d = beans("M_tmp_BeanDark", (.055, .025, .012))
bean_m = beans("M_tmp_BeanMed", (.16, .075, .03))
glass = k3d.mat("M_Glass_PH_BackShelf", (.9, .95, .95), .05, alpha=.15)
dark = k3d.mat(KEEP[0], (.012, .01, .008), .85)
green = k3d.mat(KEEP[1], (.022, .075, .048), .45)
steel = k3d.mat(KEEP[2], (.02, .02, .022), .5)


# ---------------------------------------------------------------- 구조
def skin(o, side, axis):
    """axis 를 보는 면은 원래 재질, 나머지 면은 side 재질."""
    o.data.materials.append(side)
    for p in o.data.polygons:
        p.material_index = int(abs(p.normal[axis]) < .5)
    add(o)


def slab(name, x0, x1, y0, y1, z0, z1):
    """오크 판. 위아래 면은 긴 결, 나머지 면은 결을 돌린 재질."""
    skin(S.boxz(name, x0, x1, y0, y1, z0, z1, oak, .004, 2), oak_e, 2)


T0, T1, T2 = 1.22, 1.67, 2.12  # 선반 판 윗면

# 하부장: 바에 가려 윗부분만 보이니 문과 손잡이만 둔다
add(S.boxz("kick", -2.2, 2.2, -.12, .16, 0, .1, dark, 0))
add(S.boxz("carcass", -2.2, 2.2, -.14, .16, .1, .86, dark, 0))
slab("top", -2.2, 2.2, -.16, .16, .86, .9)
for i in range(8):
    x0 = -2.2 + i * .55
    add(S.boxz("door", x0 + .002, x0 + .548, -.155, -.14, .104, .856, green, .003, 2))
    add(S.boxz("pull", x0 + .205, x0 + .345, -.165, -.155, .79, .802, steel, .003, 1))

# 뒤판: 호두나무 세로 널. 문서는 y 2.0 까지지만 맨 윗판 뒤가 비어 2.36 까지 올린다
add(S.boxz("back_plate", -2.2, 2.2, .128, .16, .9, 2.36, dark, 0))
rnd = random.Random(7)
x, k = -2.2, 0
while x < 2.2 - 1e-6:
    x1 = x + rnd.choice((.13, .145, .16, .175))
    if 2.2 - x1 < .07:
        x1 = 2.2
    skin(S.boxz("back_plank", x + .002, x1 - .002, .12, .128, .9, 2.36, walnut[k], .003, 1), dark, 1)
    x, k = x1, (k + rnd.choice((1, 2))) % 3

# 선반 판: Board0 은 기계 자리에서 끊긴다
slab("board0a", -2.2, -1.25, -.15, .125, T0 - .04, T0)
slab("board0b", -.55, 2.2, -.15, .125, T0 - .04, T0)
slab("board1", -2.2, 2.2, -.15, .125, T1 - .04, T1)
slab("board2", -2.2, 2.2, -.15, .125, T2 - .04, T2)

# 철제 사다리 틀: 소품 열 사이에만 세운다. 기계 칸은 -1.585 와 -0.325 사이다
for x in (-2.17, -1.585, -.325, .935, 2.17):
    for y in (-.125, .1075):
        add(S.boxz("post", x - .0125, x + .0125, y - .0125, y + .0125, .9, 2.36, steel, .002, 1))
    for z in (T0 - .06, T1 - .06, T2 - .06, 2.34):
        add(S.boxz("rung", x - .0125, x + .0125, -.1125, .095, z, z + .02, steel, .002, 1))
for y in (-.125, .1075):
    add(S.boxz("rail", -2.1825, 2.1825, y - .0125, y + .0125, 2.335, 2.36, steel, .002, 1))


# ---------------------------------------------------------------- 소품 (z0 = 놓이는 면)
def bag(x, y, z0, w, d, h, mat, lab, rot=0.0, seed=0.0):
    """옆 주름 원두 봉지: 초타원 단면을 쌓아 위로 갈수록 납작하고 윗단이 접혔다. 라벨은 무지."""
    def P(t, f):
        a = w / 2 * (.9 + .1 * min(1, f / .08)) * (1 - .04 * f)
        b = d / 2 * (.92 + .08 * min(1, f / .08)) * (1 if f < .55 else max(.05, 1 - .95 * ((f - .55) / .45) ** 1.5))
        e = 2 / (3.2 - 1.2 * f)
        c, s = math.cos(t), math.sin(t)
        px, py = a * math.copysign(abs(c) ** e, c), b * math.copysign(abs(s) ** e, s)
        k = 1 + .05 * noise.noise(Vector((px * 16 + seed, py * 16, f * h * 11)))
        return Vector((px * k, py * k, f * h))

    def patch(span, rows, mi):
        """앞면을 따라 띄운 판. rows = [(높이 비율, 띄움 m), ...]"""
        g = [[bm.verts.new(P(-math.pi / 2 + span * (i / 3 - 1), f) - Vector((0, off, 0))) for i in range(7)] for f, off in rows]
        for r0, r1 in zip(g, g[1:]):
            for i in range(6):
                bm.faces.new((r0[i], r0[i + 1], r1[i + 1], r1[i])).material_index = mi

    n, m = 24, 11
    bm = bmesh.new()
    rings = [[bm.verts.new(P(2 * math.pi * i / n, j / (m - 1))) for i in range(n)] for j in range(m)]
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    patch(1.45, ((.84, 0), (.84, .005), (.92, .005), (1, .005), (1, 0)), 0)
    patch(.6, ((.24, 0), (.24, .002), (.34, .002), (.44, .002), (.54, .002), (.54, 0)), 1)
    o = S.obj_from_bm("bag", bm, (x, y, z0), (0, 0, rot), mat)
    o.data.materials.append(lab)
    k3d.smooth(o, 60)
    add(o)


def jar(x, y, z0, r, h, fill, lid):
    """원두가 든 유리병. 투명 유리를 원두 앞에 겹치면 뿌옇게 떠서 원두 위 빈 곳만 유리로 둔다."""
    add(C.lathe("fill", [(0, 0), (r * .9, 0), (r, .01), (r, h * .7), (r * .6, h * .75), (0, h * .77)], 24, fill, (x, y, z0), 50))
    add(C.lathe("jar", [(0, h * .7), (r, h * .7), (r, h * .84), (r * .84, h * .93), (r * .8, h * .94), (r * .8, h), (0, h)],
                24, glass, (x, y, z0), 50))
    add(S.cyl("lid", r * .86, .022, (x, y, z0 + h + .007), lid, 24, .002))


def syrup(x, y, z0, m, ang, r=.036, hb=.15):
    """펌프 달린 시럽병. 어두운 호박색은 불투명으로 굽고 무지 띠만 두른다."""
    add(C.lathe("syrup", [(0, 0), (r * .92, 0), (r, .007), (r, hb * .66), (r * .93, hb * .76), (r * .42, hb * .88),
                          (r * .36, hb * .92), (r * .36, hb), (0, hb)], 24, m, (x, y, z0), 50))
    add(C.lathe("band", [(0, hb * .16), (r + .0012, hb * .16), (r + .0012, hb * .5), (0, hb * .5)], 24, label, (x, y, z0), 50))
    zt = z0 + hb + .05
    add(S.cyl("collar", r * .46, .018, (x, y, z0 + hb + .004), pump, 20, .002))
    add(S.cyl("stem", .0055, .04, (x, y, z0 + hb + .03), pump, 10, 0))
    add(S.cyl("pad", .015, .008, (x, y, zt + .005), pump, 16, .002))
    c, s = math.cos(ang), math.sin(ang)
    add(C.tube("spout", [(x, y, zt), (x + c * .05, y + s * .05, zt + .001), (x + c * .062, y + s * .062, zt - .014)],
               .0062, .012, pump, res=1))


def mug(x, y, z0, m, ang, r=.041, h=.098):
    t = .0042
    add(C.lathe("mug", [(0, 0), (r * .84, 0), (r * .97, .003), (r, .012), (r, h - .002), (r - .0012, h), (r - t + .0012, h),
                        (r - t, h - .002), (r - t, .012), (r * .78, t + .002), (0, t + .002)], 24, m, (x, y, z0), 50))
    c, s = math.cos(ang), math.sin(ang)
    pt = lambda d, z: (x + c * (r + d), y + s * (r + d), z0 + z)
    add(C.tube("handle", [pt(-.002, h * .8), pt(.03, h * .76), pt(.03, h * .3), pt(-.002, h * .26)], .005, .018, m, res=1))


def cups(x, y, z0, r, n, mat, step=.0135, hc=.098):
    """입이 아래로 가게 포갠 종이컵 묶음: 아래 컵의 말린 입구가 층층이 보인다."""
    p = [(0, 0)]
    for i in range(n):
        z = i * step
        p += [(r + .0016, z), (r + .0016, z + .0032), (r - .0004, z + .0042)]
    zt = (n - 1) * step + .0042
    p += [(r * .74, zt + hc), (r * .71, zt + hc + .002), (0, zt + hc + .002)]
    add(C.lathe("cups", p, 20, mat, (x, y, z0), 70))


X = (-1.9, -1.27, -.64, -.01, .62, 1.25, 1.88)   # 소품 열. 같은 물건이 줄지어 보이지 않게 칸마다 섞는다
R, L = -.7, math.pi + .7                          # 손잡이와 펌프 주둥이 방향 (앞 오른쪽, 앞 왼쪽)

# 맨 위 칸: 재고
bag(X[0] - .065, -.01, T2, .125, .08, .215, kraft, gbag, .07, 1.3)
bag(X[0] + .07, -.035, T2, .10, .065, .155, gbag, label, -.12, 2.1)
cups(X[1] - .05, -.01, T2, .04, 10, paper)
cups(X[1] + .05, -.02, T2, .04, 6, kraft)
jar(X[2] - .055, -.01, T2, .046, .19, bean_d, steel)
jar(X[2] + .052, -.03, T2, .042, .125, bean_m, oak)
bag(X[3] - .045, -.01, T2, .13, .085, .22, gbag, label, -.05, 3.7)
bag(X[3] + .085, -.03, T2, .095, .06, .15, kraft, label, .14, 4.4)
mug(X[4] - .06, -.02, T2, cream, R)
mug(X[4] - .057, -.02, T2 + .098, cream, -.2)
mug(X[4] + .055, -.03, T2, mgreen, R)
jar(X[5] - .092, -.02, T2, .04, .13, bean_m, oak)
jar(X[5], -.005, T2, .046, .195, bean_d, oak)
jar(X[5] + .09, -.025, T2, .04, .15, bean_m, steel)
cups(X[6] - .045, -.015, T2, .04, 7, paper)
cups(X[6] + .05, -.01, T2, .04, 10, paper)

# 가운데 칸: 눈높이
jar(X[0] - .05, -.02, T1, .042, .14, bean_m, steel)
jar(X[0] + .05, -.01, T1, .046, .17, bean_d, steel)
syrup(X[1] - .09, -.02, T1, amber, L)
syrup(X[1], -.005, T1, amber2, R)
syrup(X[1] + .09, -.025, T1, amber, R)
bag(X[2] - .05, -.01, T1, .13, .085, .21, kraft, gbag, .05, 5.2)
bag(X[2] + .075, -.035, T1, .10, .065, .16, kraft, label, -.1, 6.6)
bag(X[2] - .165, -.03, T1, .09, .06, .13, gbag, label, .15, 11.3)
mug(X[3] - .1, -.02, T1, mchar, L)
mug(X[3], -.03, T1, cream, R)
mug(X[3] + .1, -.015, T1, mgreen, R)
syrup(X[4] - .05, -.02, T1, amber2, L)
syrup(X[4] + .05, -.01, T1, amber, R)
bag(X[5] - .06, -.01, T1, .125, .08, .215, gbag, label, .06, 7.9)
bag(X[5] + .065, -.025, T1, .12, .08, .19, kraft, gbag, -.08, 8.3)
bag(X[5] + .175, -.035, T1, .09, .06, .135, kraft, label, -.14, 12.2)
jar(X[6] - .055, -.015, T1, .046, .19, bean_m, oak)
jar(X[6] + .05, -.03, T1, .042, .125, bean_d, oak)

# 아래 칸: 기계 옆에서 바로 쓰는 것
mug(X[0] - .055, -.02, T0, cream, L)
mug(X[0] - .053, -.02, T0 + .098, cream, math.pi - .2)
mug(X[0] + .055, -.03, T0, mchar, R)
mug(X[0] + .057, -.03, T0 + .098, mgreen, -.2)
syrup(X[3] - .09, -.025, T0, amber2, L)
syrup(X[3], -.01, T0, amber, R)
syrup(X[3] + .09, -.02, T0, amber2, R)
cups(X[4] - .05, -.015, T0, .04, 10, kraft)
cups(X[4] + .05, -.01, T0, .04, 8, paper)
jar(X[5] - .05, -.01, T0, .046, .17, bean_d, oak)
jar(X[5] + .05, -.03, T0, .042, .14, bean_m, steel)
jar(X[5] + .145, -.02, T0, .038, .12, bean_d, oak)
bag(X[6] - .06, -.015, T0, .125, .08, .2, gbag, label, -.06, 9.4)
bag(X[6] + .07, -.03, T0, .10, .065, .15, kraft, gbag, .12, 10.7)
bag(X[6] + .175, -.035, T0, .085, .055, .125, gbag, label, -.15, 13.1)

# ---------------------------------------------------------------- 범위와 기계 자리 검사 (굽기 전)
bpy.context.view_layer.update()
e = 1e-4
GAP = ((-1.25, -.55), (-.17, .12), (.9, 1.3))
for p in parts:
    ps = [p.matrix_world @ v.co for v in p.data.vertices]
    lo = [min(q[i] for q in ps) for i in range(3)]
    hi = [max(q[i] for q in ps) for i in range(3)]
    assert -2.2 - e <= lo[0] and hi[0] <= 2.2 + e and -.165 - e <= lo[1] and hi[1] <= .165 + e \
        and lo[2] >= -e and hi[2] <= 2.36 + e, (p.name, lo, hi)
    if not p.name.startswith("back"):
        assert not all(lo[i] < GAP[i][1] - e and hi[i] > GAP[i][0] + e for i in range(3)), ("기계 자리", p.name)

src = S.join(parts, A + "_src")

# 앞에서만 보는 물건이라 뒤를 보는 평면과 상판 밑면은 아틀라스만 먹는다. 단색 면은 남겨 뒤가 뚫려 보이지 않게 한다
baked = [m.name.startswith("M_tmp_") for m in src.data.materials]
bm = bmesh.new()
bm.from_mesh(src.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if baked[f.material_index] and (
    f.normal.y > .999 or f.normal.z < -.2 and f.calc_center_median().z < .87)], context='FACES')
bm.to_mesh(src.data)
bm.free()

o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src, do_unlink=True)  # 원본이 씬에 남으면 AO 굽기가 오염된다
k3d.bake(o, 2048, keep=KEEP, ao_distance=.12, samples=32, margin=2)  # 기본 여백 16 px 는 섬이 많으면 아틀라스 대부분을 먹는다
ph.finish(A, o, notes="원점 프리팹 원점(바닥 중앙), 앞면 Unity -Z. 뒤판은 y 2.36 까지. "
                      "소품 19자리. 기계 자리 x -1.25~-0.55, y 0.9~1.3 은 뒤판 말고 비움. 벽 쪽을 보는 평면은 지웠음. "
                      "문과 철제는 굽지 않는 단색")

for m in bpy.data.materials:
    m.use_backface_culling = True             # Unity 처럼 뒷면을 안 그리고 본다
glass.surface_render_method = 'BLENDED'       # 미리보기 유리가 디더링으로 뿌옇게 나오지 않게 한다
k3d.preview(A, [o], views=((180, 12), (215, 18), (0, 12)))   # 180 이 앞면이다
lamp = [(ph.at_unity(0, 3.0, -1.0), 150, 3.0, (1, .97, .92))]
S.shot(A + "_eye", ph.at_unity(0, 1.6, -1.72), ph.at_unity(0, 1.5, 0), lens=16, lights=lamp)
S.shot(A + "_eye2", ph.at_unity(-1.2, 1.6, -1.72), ph.at_unity(-1.2, 1.6, 0), lens=30, lights=lamp)

"""숲길 커피 진열장 PH_Showcase__Body. 유리 진열장 안에 케이크 4종과 빵 4종이 들어 있습니다.
소스 좌표는 x = Unity x, y = Unity z(앞면 -y), z = Unity y(높이) 입니다. 원점은 바닥 중앙입니다."""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE] + [os.path.join(HERE, "..", d) for d in ("Store", "StoreProps", "Items", "Food")]
import ph, bpy, bmesh
import storelib as S
import _common as C
import _food as F
from _food import Sh, nz
k3d = ph.k3d

k3d.reset()
A = "PH_Showcase__Body"
rad = math.radians
TOP, SHELF = .08, .31            # 받침 윗면, 중간판 윗면
CX = (-.54, -.18, .18, .54)      # 케이크와 빵 자리
PLATE, TRAY = .006, .005         # 접시, 쟁반 위에서 음식이 놓이는 높이
SPONGE, CRM = "#f0cb7c", "#fbf2e0"


# ---------------------------------------------------------------- 재질
def m_wood(name, dark, mid, light, rough=.42):
    """결이 X 로 가는 나무입니다. 늘린 노이즈라 어느 면에서도 결이 판 길이 방향입니다."""
    s = Sh(name, mid, rough)
    mp = s.n('ShaderNodeMapping')
    s.put(mp.inputs['Vector'], s.tc())
    mp.inputs['Scale'].default_value = (1.5, 34, 34)
    v = mp.outputs[0]
    wide, fine = s.noise(1.6, 4, .55, vec=v, dist=1.2), s.noise(9, 3, .6, vec=v)
    col = s.ramp(s.math('ADD', s.math('MULTIPLY', wide, .7), s.math('MULTIPLY', fine, .3)),
                 [(.36, dark), (.5, mid), (.64, light)])
    wear = s.math('MULTIPLY', C.edge_mask(s.nt, .004), s.mr(s.noise(40, 4, .6), .4, .62))
    col = s.mix(col, light, s.math('MULTIPLY', wear, .6))
    return s.out(col, s.mr(fine, .35, .65, rough - .06, rough + .08), s.bump(fine, .12, .0008))


def m_glaze(name, a, b, rough=.16):
    """유약 바른 도자기입니다."""
    s = Sh(name, a, rough)
    col = s.mix(a, b, s.mr(s.noise(14, 4, .55), .35, .7))
    return s.out(col, s.mr(s.noise(30, 3, .5), .3, .7, rough, rough + .1), s.bump(s.noise(180, 2, .5), .03, .0004))


def m_paper(name, a, b):
    s = Sh(name, a, .75)
    col = s.mix(a, b, s.mr(s.noise(18, 4, .6), .3, .7))
    return s.out(col, .72, s.bump(s.noise(70, 5, .65, dist=1.5), .35, .0012))


def m_cream(name, a, b, rough=.42):
    s = Sh(name, a, rough)
    col = s.mix(a, b, s.mr(s.noise(22, 3, .5), .35, .7))
    return s.out(col, s.mr(s.noise(140, 3, .5), .3, .7, rough - .06, rough + .08), s.bump(s.noise(60, 3, .5), .12, .0006))


def m_dust(name, a, b):
    """코코아, 말차 가루를 뿌린 윗면입니다."""
    s = Sh(name, a, .88)
    col = s.mix(a, b, s.mr(s.noise(220, 4, .6), .35, .65))
    return s.out(col, .85, s.bump(s.noise(420, 3, .6), .5, .0006))


def m_brown(name, stops, amp=.35, rough=(.38, .55), lines=0.0, dots=None):
    """구운 겉면입니다. 정점 속성 h 가 구운 정도입니다. lines 는 겹 줄무늬, dots 는 건포도 색입니다."""
    s = Sh(name, stops[1][1], rough[0])
    lo, hi = s.noise(55, 5, .55), s.noise(320, 3, .5)
    col = s.ramp(s.math('ADD', s.attr("h"), s.math('MULTIPLY', s.math('SUBTRACT', lo, .5), amp)), stops)
    col = s.mix(col, s.ramp(hi, [(.3, "#ffffff"), (.7, "#d8bd94")]), .5, 'MULTIPLY')
    hgt = s.math('ADD', hi, s.math('MULTIPLY', lo, 2))
    if lines:
        ln = s.math('SINE', s.math('MULTIPLY', s.attr("l"), 1800))
        col = s.mix(col, "#f0d49a", s.math('MULTIPLY', s.mr(ln, .3, 1), lines))
        hgt = s.math('ADD', hgt, s.math('MULTIPLY', ln, .8))
    if dots:
        d = s.math('MULTIPLY', s.mr(s.voronoi(42), .09, .15, 1, 0), s.mr(s.noise(35, 2, .5), .46, .54))
        col = s.mix(col, dots, d)
        hgt = s.math('ADD', hgt, s.math('MULTIPLY', d, -3))
    return s.out(col, s.mr(lo, .3, .7, *rough), s.bump(hgt, .25, .0007))


def m_layers(name, z0, z1, stops, wob=.06, c=None, R=0.0, fruit=False):
    """케이크 단면입니다. stops 는 (높이 비율, 색, 크림 여부) 입니다. c 를 주면 바깥 크림 코팅을 그립니다."""
    s = Sh(name, stops[0][1], .6)
    x, y, z = s.xyz()
    t = s.math('ADD', s.mr(z, z0, z1), s.math('MULTIPLY', s.math('SUBTRACT', s.noise(90, 3, .5), .5), wob))
    col = s.ramp(t, [(p, k) for p, k, _ in stops], 'CONSTANT')
    cr = s.ramp(t, [(p, "#ffffff" if q else "#000000") for p, _, q in stops], 'CONSTANT')
    pores = s.voronoi(560)
    col = s.mix(s.mix(col, "#8a6236", s.mr(pores, 0, .3, .55, 0)), col, cr)  # 기공은 시트에만
    if fruit:
        col = s.mix(col, "#c5202e", s.math('MULTIPLY', cr, s.mr(s.voronoi(46), .2, .3, 1, 0)))
    if c is not None:  # 오브젝트 x 는 소스 x 의 반대입니다
        col = s.mix(col, CRM, s.mr(s.vmath('LENGTH', s.comb(s.math('ADD', x, c), y, 0)), R - .0055, R - .0045))
    rough = s.math('ADD', .75, s.math('MULTIPLY', cr, -.33))
    return s.out(col, rough, s.bump(s.math('MULTIPLY', s.mr(pores, 0, .35), s.math('SUBTRACT', 1, cr)), .4, .0005))


def m_cheese_cut(z0, z1):
    s = Sh("M_tmp_CheeseCut", "#f6e3a8", .45)
    x, y, z = s.xyz()
    col = s.ramp(s.mr(z, z0, z1), [(0, "#e9c97e"), (.12, "#f5e0a2"), (.7, "#f9ebbd"), (.93, "#efcf86"), (1, "#8a4f1c")])
    return s.out(col, .42, s.bump(s.noise(120, 3, .5), .08, .0005))


def m_berry():
    s = Sh("M_tmp_Berry", "#b4141f", .22)
    seed = s.mr(s.voronoi(170), .05, .13, 1, 0)
    col = s.ramp(s.attr("h"), [(0, "#c4141f"), (.5, "#b3101c"), (1, "#d63a36")])
    col = s.mix(col, "#e8c05a", seed)
    return s.out(col, s.mr(seed, 0, 1, .2, .45), s.bump(s.math('MULTIPLY', seed, -1), .5, .001))


def m_ganache():
    s = Sh("M_tmp_Ganache", "#25100a", .1)
    col = s.mix("#1e0c06", "#3a1a0d", s.noise(30, 3, .5))
    return s.out(col, s.mr(s.noise(25, 2, .5), .3, .7, .08, .18), s.bump(s.noise(35, 2, .5), .06, .0008))


def m_sponge(name, a, b):
    s = Sh(name, a, .75)
    pores = s.voronoi(560)
    return s.out(s.mix(a, b, s.mr(pores, 0, .3, 1, 0)), .78, s.bump(s.mr(pores, 0, .35), .4, .0005))


def m_crumb():
    s = Sh("M_tmp_Crumb", "#f7eed8", .8)
    pores = s.voronoi(420)
    col = s.mix("#f8f0dc", "#d9c08e", s.math('MULTIPLY', s.mr(pores, 0, .28, 1, 0), s.mr(s.noise(60, 3, .5), .35, .6)))
    return s.out(col, .82, s.bump(s.mr(pores, 0, .35), .5, .0006))


LED_NAME = f"M_{A}_LED"
GLASS = k3d.mat("M_Glass_PH_Showcase", (.9, .95, .95), .05, alpha=.15)
LED = k3d.mat(LED_NAME, (1, 1, 1), .3, emission=(1, .95, .85), strength=3.0)
WALNUT = m_wood("M_tmp_Walnut", "#2e1a10", "#4d2f1d", "#6e4a30")
STEEL = C.powder_coat("M_tmp_Steel", (.03, .03, .032), .5, wear=.4, scratch=.25)
SS = C.stainless("M_tmp_SS", .3, 'X', smudge=.4)
CASE = {"M_tmp_Walnut", "M_tmp_Steel", "M_tmp_SS"}   # smart_project 를 쓰는 상자 재질
UV_SCALE = {"M_tmp_Walnut": .4, "M_tmp_Steel": .4, "M_tmp_SS": .4, "M_tmp_Oak": .55, "M_tmp_Board": .55,
            "M_tmp_White": .55, "M_tmp_Green": .55, "M_tmp_Plate": .55}
OAK = m_wood("M_tmp_Oak", "#8f6636", "#b58a52", "#d0a970", .46)
BOARD = m_wood("M_tmp_Board", "#3a2214", "#5a3822", "#7a5436", .45)
SS2 = C.stainless("M_tmp_Plate", .24, 'X', smudge=.3)
WHITE = m_glaze("M_tmp_White", "#f5f1e8", "#e9e2d2")
GREEN = m_glaze("M_tmp_Green", "#1b3a29", "#2c5a3e", .2)
KRAFT = m_paper("M_tmp_Kraft", "#b58f5e", "#9c7648")
PARCH = m_paper("M_tmp_Parch", "#e2d0ae", "#c9b188")
CREAM = m_cream("M_tmp_Cream", "#fdf7ec", "#f1e3c8")
CHOCREAM = m_cream("M_tmp_ChoCream", "#6a3f26", "#4f2c19", .35)
BERRY = m_berry()
GANACHE = m_ganache()
CHOSP = m_sponge("M_tmp_ChoSponge", "#47281a", "#22100a")
CHODARK = m_cream("M_tmp_ChoDark", "#2c150c", "#1c0c06", .22)
BLUE = m_cream("M_tmp_Blueberry", "#1c2140", "#3a4366", .36)
COCOA = m_dust("M_tmp_Cocoa", "#7a5233", "#553620")
MATCHA = m_dust("M_tmp_Matcha", "#7f9a48", "#5f7d33")
CHEESE = m_brown("M_tmp_Cheese", [(0, "#f1d896"), (.35, "#e2aa55"), (.6, "#b9722a"), (.8, "#6f3a15"), (1, "#2e170b")], .7, (.3, .45))
CROISS = m_brown("M_tmp_Croissant", [(0, "#f3dca6"), (.3, "#e4b261"), (.55, "#c98332"), (.8, "#a55e1e"), (1, "#703a12")], .3, (.3, .42), lines=.35)
SCONE = m_brown("M_tmp_Scone", [(0, "#f0dcae"), (.35, "#e3bf7c"), (.6, "#cc9347"), (.85, "#a96a28"), (1, "#7d4a1a")], .4, (.55, .72), dots="#2c140c")
CRUST = m_brown("M_tmp_Crust", [(0, "#e8c48a"), (.35, "#d19a55"), (.6, "#b9752f"), (.85, "#96561f"), (1, "#6e3d15")], .25, (.42, .58))
MUFFIN = m_brown("M_tmp_Muffin", [(0, "#ecd096"), (.4, "#d6a050"), (.7, "#b5782f"), (1, "#7f4c1a")], .35, (.5, .66))
CRUMB = m_crumb()
Z0 = TOP + PLATE
CUT0 = m_layers("M_tmp_Cut0", Z0, Z0 + .07, [(0, SPONGE, 0), (.24, CRM, 1), (.37, SPONGE, 0), (.61, CRM, 1), (.74, SPONGE, 0), (.92, CRM, 1)],
                c=CX[0], R=.086, fruit=True)
CUTM = m_layers("M_tmp_CutMatcha", Z0, Z0 + .066, [(i / 13, "#f3ecd6" if i % 2 else "#7f9c46", i % 2) for i in range(13)], wob=.02)
CUTT = m_layers("M_tmp_CutTira", Z0, Z0 + .066, [(0, "#9a6b3f", 0), (.3, "#f2e6cc", 1), (.48, "#8f6238", 0), (.76, "#f2e6cc", 1)])
CHEESECUT = m_cheese_cut(TOP + .0132, TOP + .074)


# ---------------------------------------------------------------- 메시 도구
def put(o, x, y, z, rot=0.0):
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, rot)
    return o


def attr(o, name, vals):
    o.data.attributes.new(name, 'FLOAT', 'POINT').data.foreach_set("value", vals)
    return o


def ring_noise(seed, k=3, amp=.006):
    return lambda a, i, r, z: 1 + amp * nz(math.cos(a) * k, math.sin(a) * k, z * 30 + seed)


def drum(R, h, b=.005, rings=3):
    """둥근 모서리 원통 프로필입니다. 바닥 중심에서 옆을 지나 윗면 중심으로 갑니다."""
    p = [(0, 0), (R * .7, 0), (R - .0015, 0), (R, .0015)]
    p += [(R, .0015 + (h - b - .0015) * (i + 1) / rings) for i in range(rings)]
    return p + [(R - b * .3, h - b * .3), (R - b, h), (R * .66, h), (R * .33, h), (0, h)]


def skin(bm, uvl, rows, uv, closed, slot=0):
    """격자 정점 rows[j][i] 에 면을 붙입니다. uv(j, i) 는 미터 단위이고 closed 면 i 방향으로 한 바퀴 닫습니다.
    한 격자가 UV 섬 하나가 됩니다. 곡면을 smart_project 에 맡기면 섬이 수천 개로 쪼개져 아틀라스를 못 채웁니다."""
    for j in range(len(rows) - 1):
        n = max(len(rows[j]), len(rows[j + 1]))
        for i in range(n if closed else n - 1):
            vs, cs = [], []
            for a, b in ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)):
                v = rows[a][b % len(rows[a])]
                if v not in vs:
                    vs.append(v)
                    cs.append(uv(a, b))
            if len(vs) > 2:
                f = bm.faces.new(vs)
                f.material_index = slot
                for l, c in zip(f.loops, cs):
                    l[uvl].uv = c


def flat_cap(bm, uvl, verts, slot, ax=0):
    """닫는 면입니다. UV 는 평면 투영입니다. ax=0 이면 (x, z), 1 이면 (회전 반지름, z) 입니다."""
    f = bm.faces.new(verts)
    f.material_index = slot
    for l in f.loops:
        p = l.vert.co
        l[uvl].uv = (math.hypot(p.x, p.y) if ax else p.x, p.z)


def spin(name, prof, segs, outer, cut=None, rfn=None, zfn=None, a0=0.0, a1=None, sharp=40):
    """prof=[(r, z), ...] 를 Z 축으로 돌립니다. a1 을 주면 a0~a1 만 돌리고 잘린 두 면을 cut 재질로 막습니다."""
    full = a1 is None
    span = 2 * math.pi if full else a1 - a0
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = []
    for j, (r, z) in enumerate(prof):
        if r < 1e-6:
            rows.append([bm.verts.new((0, 0, z + (zfn(0.0, j, 0.0, z) if zfn else 0)))])
            continue
        ring = []
        for k in range(segs if full else segs + 1):
            a = a0 + span * k / segs
            rr = r * (rfn(a, j, r, z) if rfn else 1)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z + (zfn(a, j, r, z) if zfn else 0))))
        rows.append(ring)
    vs, rmax = [0.0], max(r for r, z in prof)
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        vs.append(vs[-1] + math.hypot(r1 - r0, z1 - z0))
    skin(bm, uvl, rows, lambda j, i: (span * rmax * i / segs, vs[j]), full)
    if not full:
        flat_cap(bm, uvl, [row[0] for row in rows], 1, 1)
        flat_cap(bm, uvl, [row[-1] for row in rows][::-1], 1, 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return F.smooth(F.mats(F.mesh_obj(name, bm), *((outer, cut) if cut else (outer,))), sharp)


def plate(name, R, mat, rfn=None):
    prof = [(0, .0005), (R * .5, .0005), (R * .56, 0), (R * .66, 0), (R * .72, .003), (R * .94, .0085), (R, .0105),
            (R * .995, .0125), (R * .93, .0112), (R * .72, .0068), (R * .6, PLATE), (0, PLATE)]
    return spin(name, prof, 56, mat, rfn=rfn, sharp=45)


def squircle(n):
    return lambda a, i, r, z: 1 / (abs(math.cos(a)) ** n + abs(math.sin(a)) ** n) ** (1 / n)


def tray(name, w, d, mat):
    """둥근 네모 쟁반입니다."""
    R = w / 2
    prof = [(0, 0), (R * .97, 0), (R, .002), (R, .011), (R - .0012, .012), (R - .0045, .012), (R - .0058, .006), (R - .008, TRAY), (0, TRAY)]
    o = spin(name, prof, 72, mat, rfn=squircle(6))
    o.scale = (1, d / w, 1)
    return o


def rosette(name, r, h, mat, seed=0.0):
    """별깍지로 짠 크림입니다."""
    prof = [(0, 0), (r * .8, 0), (r, h * .14), (r * .98, h * .3), (r * .78, h * .52), (r * .5, h * .72), (r * .2, h * .92), (0, h)]
    return spin(name, prof, 24, mat, rfn=lambda a, i, rr, z: 1 + .17 * math.cos(6 * a + 5 * z / h + seed), sharp=70)


def strawberry(name, R, H):
    prof = [(0, 0), (R * .55, 0), (R * .9, H * .06), (R, H * .2), (R * .96, H * .38), (R * .8, H * .58), (R * .55, H * .78), (R * .28, H * .93), (0, H)]
    o = spin(name, prof, 20, BERRY, rfn=lambda a, i, r, z: 1 + .05 * nz(math.cos(a) * 2, math.sin(a) * 2, z * 60), sharp=70)
    return F.vattr(o, "h", lambda co: 1 - co.z / H)


# ---------------------------------------------------------------- 케이스
def case():
    b = S.boxz
    P = [b("Kick", -.742, .742, -.272, .272, 0, .012, STEEL, .001, 1),
         b("Base", -.75, .75, -.28, .28, .012, TOP, WALNUT, .0025, 2),
         b("Roof", -.77, .77, -.3, .3, .555, .585, WALNUT, .003, 2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            xs, ys = sorted((sx * .75, sx * .736)), sorted((sy * .28, sy * .266))
            P.append(b("Post", *xs, *ys, TOP, .555, STEEL, .001, 1))
    for z0, z1 in ((TOP, .09), (.545, .555)):     # 위아래 레일. 뒤는 미닫이 두 장이 다니는 넓은 레일입니다
        P += [b("RailF", -.736, .736, -.28, -.266, z0, z1, STEEL, .001, 1),
              b("RailB", -.736, .736, .257, .28, z0, z1, STEEL, .001, 1),
              b("RailL", -.75, -.738, -.266, .266, z0, z1, STEEL, .001, 1),
              b("RailR", .738, .75, -.266, .266, z0, z1, STEEL, .001, 1)]
    P += [b("GlassF", -.736, .736, -.2745, -.2695, .09, .545, GLASS, 0),
          b("GlassL", -.7455, -.7405, -.266, .266, .09, .545, GLASS, 0),
          b("GlassR", .7405, .7455, -.266, .266, .09, .545, GLASS, 0),
          b("Door0", -.736, .012, .2615, .2665, .09, .545, GLASS, 0),
          b("Door1", -.012, .736, .2705, .2755, .09, .545, GLASS, 0),
          b("Stile0", .004, .012, .2595, .2685, .09, .545, STEEL, .0008, 1),
          b("Stile1", -.012, -.004, .2685, .2775, .09, .545, STEEL, .0008, 1)]
    # 중간판: 스테인리스 테두리 유리판. 위에서 아래 칸 케이크가 보이게 유리로 합니다
    z0 = SHELF - .016
    P += [b("ShelfF", -.72, .72, -.25, -.24, z0, SHELF, SS, .0012, 1),
          b("ShelfB", -.72, .72, .24, .25, z0, SHELF, SS, .0012, 1),
          b("ShelfL", -.72, -.71, -.24, .24, z0, SHELF, SS, .0012, 1),
          b("ShelfR", .71, .72, -.24, .24, z0, SHELF, SS, .0012, 1),
          b("ShelfG", -.71, .71, -.24, .24, SHELF - .007, SHELF, GLASS, 0)]
    for x, y in ((-.715, -.245), (.715, -.245), (-.715, .245), (.715, .245), (0, .245)):
        P.append(S.cyl("Rod", .004, z0 - TOP, (x, y, (z0 + TOP) / 2), SS, 12, .0006, 1))
    P.append(b("Led", -.7, .7, -.222, -.21, .546, .555, LED, 0))
    return P


# ---------------------------------------------------------------- 케이크
def cake_strawberry(cx):
    """딸기 생크림 홀케이크입니다. 한 조각을 잘라 층이 보입니다."""
    z, R, h = Z0, .086, .07
    P = [put(plate("C0Plate", .11, WHITE), cx, 0, TOP),
         put(spin("C0", drum(R, h), 56, CREAM, CUT0, ring_noise(1), a0=rad(-45), a1=rad(255)), cx, 0, z)]
    for k in range(10):
        a = rad(-37 + k * 284 / 9)
        P.append(put(rosette("C0Rose", .0125, .02, CREAM, k), cx + .071 * math.cos(a), .071 * math.sin(a), z + h - .001, a))
    for a in (-15, 45, 105, 165, 225):
        a = rad(a)
        P.append(put(strawberry("C0Berry", .0135, .027), cx + .037 * math.cos(a), .037 * math.sin(a), z + h - .0015, a))
    P.append(put(strawberry("C0Berry", .0145, .03), cx - .004, .014, z + h - .0015))
    return P


def cake_cheese(cx):
    """바스크 치즈케이크입니다. 유산지에 담겨 윗면이 진하게 구워졌고 한 조각이 비어 있습니다."""
    z = TOP + .012
    R, h = .0875, .062
    board = [(0, 0), (.105, 0), (.108, .003), (.108, .009), (.105, .012), (0, .012)]
    P = [put(spin("C1Board", board, 56, OAK), cx, 0, TOP)]
    wall = [(.0885 + .0055 * i / 5, .075 * i / 5) for i in range(6)]
    prof = [(0, 0), (.06, 0)] + wall + [(r - .0012, zz) for r, zz in wall[::-1][:-1]] + [(.0872, .0012), (.06, .0012), (0, .0012)]
    fr = lambda a, i, r, zz: 1 + (zz / .075) ** 2 * (.03 * math.sin(13 * a + 2 * nz(math.cos(a) * 2, math.sin(a) * 2, 3)) + .02 * nz(math.cos(a) * 9, math.sin(a) * 9, 1))
    fz = lambda a, i, r, zz: (zz / .075) ** 3 * .008 * nz(math.cos(a) * 5, math.sin(a) * 5, 2)
    a0, a1 = rad(-95), rad(225)
    P.append(put(spin("C1Paper", prof, 72, PARCH, PARCH, fr, fz, a0, a1), cx, 0, z))
    top = [(R - .003, .0605), (R - .009, .062)] + [(R * k, .0595 - .0035 * (.8 - k)) for k in (.8, .68, .56, .44, .32, .2, .1)] + [(0, .0555)]
    prof = [(0, .0012), (.06, .0012), (R - .001, .0012), (R, .0032), (R, .02), (R, .04), (R - .0005, .055)] + top
    fz = lambda a, i, r, zz: .0018 * nz(r * math.cos(a) * 70, r * math.sin(a) * 70, 4) if zz > .05 else 0
    body = spin("C1", prof, 64, CHEESE, CHEESECUT, ring_noise(2, 4, .004), fz, a0, a1)
    F.vattr(body, "h", lambda co: .2 + .6 * (co.z / h) ** 3 + .2 * (math.hypot(co.x, co.y) / R) ** 4 * (co.z > .05))
    P.append(put(body, cx, 0, z))
    return P


def ganache(R, zt):
    """윗면을 덮고 옆으로 흘러내린 가나슈입니다. 고리 번호로 흘러내린 길이를 줍니다."""
    rnd = random.Random(5)
    drips = [(rnd.uniform(0, 6.283), rnd.uniform(.012, .036), rnd.uniform(.05, .085)) for _ in range(20)]

    def length(a):
        return max([.006] + [l * math.exp(-(((a - a0 + math.pi) % (2 * math.pi) - math.pi) / w) ** 2) for a0, l, w in drips])
    side = zt - .004
    prof = [(0, zt + .0034), (R * .5, zt + .0034), (R * .85, zt + .003), (R * .97, zt + .002), (R + .0012, zt - .0005), (R + .0024, side)]
    first = len(prof)
    prof += [(R + .0026, side), (R + .0028, side), (R + .0031, side), (R + .0033, side), (R + .0012, side), (R - .001, side), (R - .001, zt - .002), (0, zt - .002)]
    ts = (.25, .5, .75, .95, 1, 1)
    fz = lambda a, i, r, z: -ts[i - first] * length(a) if first <= i < first + 6 else 0
    return spin("C2Ganache", prof, 160, GANACHE, zfn=fz, sharp=80)


def cake_choco(cx):
    """초코 케이크입니다. 광택 가나슈가 흘러내리고 윗면에 크림, 초콜릿 롤, 판을 얹었습니다."""
    z, R, h = Z0, .083, .062
    zt = z + h
    P = [put(plate("C2Plate", .108, SS2), cx, 0, TOP),
         put(spin("C2", drum(R, h, .002), 56, CHOSP), cx, 0, z),
         put(ganache(R, h), cx, 0, z)]
    for k in range(9):
        a = rad(k * 40 + 10)
        P.append(put(rosette("C2Rose", .0115, .019, CHOCREAM, k), cx + .067 * math.cos(a), .067 * math.sin(a), zt + .002, a))
    for k, (dx, dy, yaw, m) in enumerate(((-.012, .012, .5, CHODARK), (.01, .016, -.3, CHOCREAM), (-.003, -.004, .15, CHODARK), (.014, -.012, 1.3, CHOCREAM), (-.018, -.016, -.9, CHODARK))):
        r, l = .0036, .029
        o = spin("C2Roll", [(0, -l), (r * .8, -l), (r, -l + .001), (r, l - .001), (r * .8, l), (0, l)], 10, m)
        o.location, o.rotation_euler = (cx + dx, dy, zt + .0075 + .004 * (k % 2)), (math.pi / 2, 0, yaw)
        P.append(o)
    for k in range(4):
        a = rad(k * 90 + 40)
        o = spin("C2Disc", [(0, -.0011), (.0204, -.0011), (.021, 0), (.0204, .0011), (0, .0011)], 20, CHODARK)
        o.location, o.rotation_euler = (cx + .03 * math.cos(a), .03 * math.sin(a), zt + .0165), (1.05, 0, a + math.pi / 2)
        P.append(o)
    return P


def cake_slices(cx):
    """초록 접시의 두 조각입니다. 말차 크레이프와 티라미수이고 꼭짓점이 앞을 봅니다."""
    z, h = Z0, .066
    P = [put(plate("C3Plate", .105, GREEN, squircle(4)), cx, 0, TOP)]
    for name, dx, yaw, top, cut, cream in (("C3M", -.047, .1, MATCHA, CUTM, CREAM), ("C3T", .047, -.09, COCOA, CUTT, CREAM)):
        P.append(put(spin(name, drum(.125, h), 12, top, cut, a0=rad(69), a1=rad(111)), cx + dx, -.062, z, yaw))
        P.append(put(rosette(name + "Rose", .012, .019, cream, 2), cx + dx - .085 * math.sin(yaw), -.062 + .085 * math.cos(yaw), z + h - .001))
    return P


# ---------------------------------------------------------------- 빵
def croissant(name, L=.125, W=.056, H=.047, bend=1.0, seed=1.0):
    """초승달 모양으로 훑은 크루아상입니다. 말린 겹 자리는 갈매기 모양 홈입니다."""
    n, m = 64, 14
    R = L / 2 / math.sin(bend)
    y0 = R * (1 - math.cos(bend)) / 2
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    hs, ls, rings = [], [], []
    for i in range(1, n):
        t = i / n
        p = (t - .5) * 2 * bend
        px, py, nx, ny = R * math.sin(p), R * (math.cos(p) - math.cos(bend)) - y0, math.sin(p), math.cos(p)
        f = math.sin(math.pi * t) ** .62
        ring = []
        for j in range(m):
            th = 2 * math.pi * j / m
            band = .5 + .5 * math.cos(2 * math.pi * 5 * (t - .5) + 1.6 * abs(math.cos(th)))
            k = 1 - .3 * (1 - band) ** 2
            a, b = W / 2 * f * k, H / 2 * f * k
            z = max(b * (.85 + math.sin(th)), 0)
            q = .0012 * nz(px * 60, py * 60, z * 60 + seed)
            ring.append(bm.verts.new((px + nx * (a * math.cos(th) + q), py + ny * (a * math.cos(th) + q), z)))
            hs.append(.15 + .45 * z / H + .3 * band)
            ls.append(t * L)
        rings.append(ring)
    tips = [bm.verts.new((s_ * L / 2, -y0, .007)) for s_ in (-1, 1)]
    hs += [.8, .8]
    ls += [0, L]
    skin(bm, uvl, [[tips[0]]] + rings + [[tips[1]]], lambda j, i: (.16 * i / m, L * j / n), True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = F.mats(F.mesh_obj(name, bm), CROISS)
    return F.smooth(attr(attr(o, "h", hs), "l", ls), 70)


def scone(name, seed):
    """둥근 삼각형 스콘입니다."""
    R, H = .05, .041
    prof = [(0, 0), (R * .75, 0), (R * .97, .002), (R, .006), (R * 1.01, .016), (R * .99, .027), (R * .95, .034), (R * .82, .0385), (R * .55, .0405), (R * .25, H), (0, H)]

    def fr(a, i, r, z):
        tri = .5 / math.cos((a + seed) % (2 * math.pi / 3) - math.pi / 3)   # 변 가운데 .5, 모서리 1
        return (.62 * tri + .266) * (1 + .05 * nz(math.cos(a) * 3, math.sin(a) * 3, z * 45 + seed) + .025 * nz(math.cos(a) * 10, math.sin(a) * 10, z * 120 + seed))
    fz = lambda a, i, r, z: 0 if z < .002 else .0028 * nz(r * math.cos(a) * 55, r * math.sin(a) * 55, seed)
    return F.vattr(spin(name, prof, 48, SCONE, rfn=fr, zfn=fz, sharp=60), "h", lambda co: .18 + .62 * max(co.z / H, 0) ** 1.5)


def loaf(name, w, h, L, K, seed):
    """식빵입니다. 단면은 아래가 네모이고 위가 버섯처럼 부풉니다. 양 끝은 속살입니다."""
    m = 28
    sec = []
    for j in range(m):
        th = 2 * math.pi * j / m
        c, s_ = math.cos(th), math.sin(th)
        z = h / 2 + h / 2 * math.copysign(abs(s_) ** .55, s_)
        k = max(0.0, (z - h * .58) / (h * .42))
        sec.append((w / 2 * math.copysign(abs(c) ** .55, c) * (1 + .15 * math.sin(k * math.pi * .75)), z))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i in range(K + 1):
        y = -L / 2 + L * i / K
        q = 1 + .012 * nz(y * 30, seed) + .02 * math.sin(math.pi * i / K)
        rings.append([bm.verts.new((x * q, y, z * (1 + .5 * (q - 1)))) for x, z in sec])
    per = 2 * (w + h)
    skin(bm, uvl, rings, lambda j, i: (per * i / m, L * j / K), True)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        inner = [bm.verts.new((v.co.x * .93, v.co.y, h / 2 + (v.co.z - h / 2) * .93)) for v in ring]
        skin(bm, uvl, [ring, inner], lambda j, i: (per * i / m, .004 * j), True)
        flat_cap(bm, uvl, inner[::-1] if flip else inner, 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = F.mats(F.mesh_obj(name, bm), CRUST, CRUMB)
    return F.smooth(F.vattr(o, "h", lambda co: .3 + .62 * max(co.z / h, 0) ** 2), 50)


def muffin(name, seed):
    """크래프트 주름 컵에 담긴 블루베리 머핀입니다."""
    cup = [(0, 0), (.0245, 0), (.026, .001), (.0325, .04), (.0315, .0408), (.0262, .0028), (0, .0025)]
    dome = [(.0405, .0445), (.0418, .05), (.039, .06), (.031, .068), (.0165, .0745), (0, .076)]
    prof = [(0, .003), (.026, .003), (.0305, .034), (.037, .0405)] + dome
    fr = lambda a, i, r, z: 1 + .04 * nz(math.cos(a) * 3, math.sin(a) * 3, seed) + .02 * nz(math.cos(a) * 9, math.sin(a) * 9, z * 80 + seed)
    fz = lambda a, i, r, z: .0018 * nz(r * math.cos(a) * 90, r * math.sin(a) * 90, seed) if z > .045 else 0
    top = F.vattr(spin(name, prof, 48, MUFFIN, rfn=fr, zfn=fz, sharp=60), "h", lambda co: .15 + .75 * min(max((co.z - .04) / .036, 0), 1))
    P = [spin(name + "Cup", cup, 72, KRAFT, rfn=lambda a, i, r, z: 1 + .03 * math.cos(18 * a), sharp=80), top]
    rnd = random.Random(seed)
    ball = [(.0062 * math.sin(t * math.pi / 6), -.0052 * math.cos(t * math.pi / 6)) for t in range(7)]
    for _ in range(6):
        k = rnd.randrange(1, len(dome) - 1)
        t, a = rnd.random(), rnd.uniform(0, 6.283)
        r = dome[k][0] + (dome[k + 1][0] - dome[k][0]) * t
        z = dome[k][1] + (dome[k + 1][1] - dome[k][1]) * t
        o = spin(name + "Blue", ball, 10, BLUE, sharp=80)
        o.data.transform(F.Matrix.Translation((r * .96 * math.cos(a), r * .96 * math.sin(a), z)))
        P.append(o)
    return P


def bread_croissant(cx):
    P = [put(tray("B0Tray", .24, .16, OAK), cx, 0, SHELF)]
    for k, dx in enumerate((-.072, 0, .072)):
        P.append(put(croissant("B0", seed=k * 3.1), cx + dx, .004 * (k - 1), SHELF + TRAY, rad(90 + 5 * (k - 1))))
    return P


def bread_scone(cx):
    z = SHELF + TRAY
    P = [put(tray("B1Tray", .24, .16, OAK), cx, 0, SHELF),
         put(spin("B1Paper", [(0, 0), (.1, 0), (.1, .0012), (0, .0012)], 40, KRAFT, rfn=squircle(10)), cx, 0, z, rad(4))]
    P[1].scale = (1, .62, 1)
    for k, (dx, dy) in enumerate(((-.077, -.012), (0, .014), (.077, -.01))):
        P.append(put(scone("B1", 1.3 + k * 2.2), cx + dx, dy, z + .0012))
    return P


def bread_loaf(cx):
    z, w, h = SHELF + TRAY, .085, .08
    P = [put(tray("B2Tray", .24, .16, BOARD), cx, 0, SHELF),
         put(loaf("B2", w, h, .125, 10, 1.7), cx - .062, 0, z)]
    for k, (dx, dy, yaw, dz, tilt) in enumerate(((.054, -.012, .12, 0, 0), (.064, .004, -.05, .012, .05))):
        o = loaf("B2Slice", w, h, .012, 1, 3.1 + k)
        o.location = (cx + dx, dy - h / 2, z + dz + .006)
        o.rotation_euler = (-math.pi / 2 + tilt, 0, yaw)
        P.append(o)
    return P


def bread_muffin(cx):
    P = [put(tray("B3Tray", .24, .16, OAK), cx, 0, SHELF)]
    for k, (dx, dy) in enumerate(((-.076, .01), (0, -.012), (.076, .012))):
        for o in muffin("B3", 2.3 + k * 1.9):
            P.append(put(o, cx + dx, dy, SHELF + TRAY, k))
    return P


# ---------------------------------------------------------------- 아틀라스
_smart = k3d.uv_smart


def uv_atlas(obj, faces=None, margin=.004, layer=None):
    """케이스 상자만 smart_project 를 쓰고 음식은 만들 때 준 미터 단위 격자 UV 를 씁니다.
    바닥을 보는 면은 눈(y 0.54)에서 안 보이므로 한 점으로 접어 아틀라스에서 뺍니다.
    재질별 UV_SCALE 로 케이스, 접시, 쟁반을 줄여 코앞에서 보는 음식에 해상도를 몰아 줍니다."""
    me = obj.data
    scale = [UV_SCALE.get(m.name, 1.0) for m in me.materials]
    case = {i for i, m in enumerate(me.materials) if m.name in CASE}
    ids = [p.index for p in me.polygons if p.material_index in case]
    _smart(obj, ids, margin, layer)
    atlas, grid = me.uv_layers[layer].data, me.uv_layers[0].data
    uv_area = 0.0
    for i in ids:
        a, b, c = me.polygons[i].loop_indices
        uv_area += abs((atlas[b].uv - atlas[a].uv).cross(atlas[c].uv - atlas[a].uv)) / 2
    meter = math.sqrt(sum(me.polygons[i].area for i in ids) / uv_area)
    seen = set()
    for i in faces:
        p = me.polygons[i]
        hidden = p.normal.z < -.85 and p.center.z < .5
        if not hidden:
            seen.add(i)
        k = scale[p.material_index]
        for l in p.loop_indices:
            if hidden:
                atlas[l].uv = (.0005, .0005)
            elif p.material_index in case:
                atlas[l].uv = atlas[l].uv * meter * k
            else:
                atlas[l].uv = grid[l].uv * k
    bpy.context.scene.tool_settings.use_uv_select_sync = True   # 고른 면만 패킹합니다. 유리 UV 가 끼면 아틀라스 절반이 빕니다
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    for f in bm.faces:
        f.select = f.index in seen
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.pack_islands(margin=.002, rotate=True, scale=False, shape_method='AABB', margin_method='ADD')
    bpy.ops.object.mode_set(mode='OBJECT')
    atlas = me.uv_layers[layer].data
    ls = [l for i in seen for l in me.polygons[i].loop_indices]
    x0, y0 = min(atlas[l].uv.x for l in ls), min(atlas[l].uv.y for l in ls)
    k = .998 / max(max(atlas[l].uv.x for l in ls) - x0, max(atlas[l].uv.y for l in ls) - y0)
    for l in ls:
        atlas[l].uv = ((atlas[l].uv.x - x0) * k + .001, (atlas[l].uv.y - y0) * k + .001)
    print("k3d: 아틀라스 배율", round(k * 2048), "px/m")


k3d.uv_smart = uv_atlas

# ---------------------------------------------------------------- 합치고 굽기
parts = case() + cake_strawberry(CX[0]) + cake_cheese(CX[1]) + cake_choco(CX[2]) + cake_slices(CX[3])
parts += bread_croissant(CX[0]) + bread_scone(CX[1]) + bread_loaf(CX[2]) + bread_muffin(CX[3])
for p in parts:
    for nm in ("h", "l"):
        if nm not in p.data.attributes:
            F.const_attr(p, nm, 0.0)
src = S.join(parts, A + "_src")
o = ph.part(A, [src], ph.turn(180))
bpy.data.objects.remove(src, do_unlink=True)
k3d.bake(o, 2048, keep=(LED_NAME,), ao_distance=.05, margin=6)
ph.finish(A, o, notes="원점 바닥 중앙, 앞면 -Z 가 플레이어 쪽, 바 위 y 1.06. 유리 M_Glass_PH_Showcase, 조명 띠는 굽지 않음. 케이크 4종, 빵 4종 포함.")
for m in bpy.data.materials:
    m.use_backface_culling = True
GLASS.surface_render_method = 'BLENDED'   # 미리보기를 Unity 의 알파 혼합처럼 봅니다
k3d.preview(A, [o], views=((180, 12), (215, 18), (0, 12)))
L = [(ph.at_unity(0, 2.0, -1.0), 60, 2.0, (1, .97, .92))]
S.shot(A + "_eye", ph.at_unity(0, .54, -.6), ph.at_unity(0, .2, 0), lens=24, lights=L)
S.shot(A + "_eye2", ph.at_unity(-.6, .54, -.5), ph.at_unity(-.36, .2, 0), lens=35, lights=L)
S.shot(A + "_eye3", ph.at_unity(.6, .54, -.5), ph.at_unity(.36, .2, 0), lens=35, lights=L)

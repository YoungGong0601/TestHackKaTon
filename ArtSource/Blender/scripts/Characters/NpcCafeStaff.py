"""NpcCafeStaff — 2회차 카페 "숲길 커피" 직원, 20대 (매장 알바생 스크립트 복사, npc_worker1 리그 기반).
안전모·콧수염 제거 -> 모자 없이 숱을 늘린 머리와 앞머리 다발. 짙은 초록 폴로(잎 로고), 진한 갈색 허리 앞치마(주머니·펜·끈), 카페 명찰, 스마트폰.
로고 PNG 는 이 파일이 k3d.PY(Pillow)로 자기를 다시 불러 _cache/npcb/cafe_*.png 로 그린다.
실행: K3D_ROOT=... blender -b --factory-startup --python NpcCafeStaff.py
"""
import sys, os, math, subprocess


def draw_decals(out, fonts):
    """숲길 커피 데칼. 동그란 테두리 없이 잎과 글자만 쓴다 (실존 커피 상표와 닮지 않게)."""
    from PIL import Image, ImageDraw, ImageFont
    from npcb_decals import worn
    GREEN, CREAM = "#1e4a3f", "#f3ead7"
    font = lambda name, size: ImageFont.truetype(os.path.join(fonts, name), size)

    def leaf(d, base, ang, L, W, col):
        """base 에서 ang 도(0 = 위) 쪽으로 뻗은 잎 하나. 잎맥은 투명이라 옷 색이 비친다."""
        a = math.radians(ang)
        ux, uy, nx, ny = math.sin(a), -math.cos(a), math.cos(a), math.sin(a)
        P = lambda t, s: (base[0] + ux * L * t + nx * s, base[1] + uy * L * t + ny * s)
        half = lambda t: W / 2 * math.sin(math.pi * t ** 0.75)
        ts = [i / 40 for i in range(41)]
        d.polygon([P(t, half(t)) for t in ts] + [P(t, -half(t)) for t in reversed(ts)], fill=col)
        lw = max(2, int(L * 0.03))
        d.line([P(0, 0), P(0.9, 0)], fill=(0, 0, 0, 0), width=lw)
        for t in (0.22, 0.40, 0.58):
            for sd in (1, -1):
                d.line([P(t, 0), P(t + 0.17, sd * half(t + 0.17) * 0.75)], fill=(0, 0, 0, 0), width=lw)

    def logo(col, size=1024, text=True):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        k = size / 1024 * (1.0 if text else 1.45)
        base = (size * 0.47, size * (0.60 if text else 0.90))
        d.line([base, (base[0] - 26 * k, base[1] + 62 * k)], fill=col, width=int(22 * k))
        leaf(d, base, -48, 300 * k, 150 * k, col)
        leaf(d, base, 16, 480 * k, 240 * k, col)
        if text:
            d.text((size / 2, size * 0.80), "숲길 커피", font=font("NanumSquareEB.ttf", size * 190 // 1024), fill=col, anchor="mm")
        return im

    def nametag():
        """명찰 7.0 x 2.4 cm -> 840 x 288."""
        W, H = 840, 288
        im = Image.new("RGBA", (W, H), "#f4f1ea")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 54], fill=GREEN)
        d.text((24, 27), "숲길 커피", font=font("NanumSquareEB.ttf", 34), fill=CREAM, anchor="lm")
        im.alpha_composite(logo(GREEN, 360, text=False).resize((190, 190), Image.LANCZOS), (14, 72))
        d.text((222, 150), "바리스타", font=font("NanumSquareB.ttf", 38), fill="#6d6259", anchor="lm")
        d.text((400, 156), "이서준", font=font("NanumSquareEB.ttf", 92), fill="#231d18", anchor="lm")
        d.text((W - 24, H - 22), "BARISTA", font=font("NanumSquareB.ttf", 28), fill="#9b8f84", anchor="rs")
        return im

    logo(CREAM).save(os.path.join(out, "cafe_logo.png"))
    worn(logo(CREAM), 0.16, 2).save(os.path.join(out, "cafe_logo_worn.png"))
    nametag().save(os.path.join(out, "cafe_nametag.png"))


try:
    import bpy, bmesh
except ImportError:      # k3d.PY 로 불렸을 때: 데칼만 그리고 끝낸다
    draw_decals(*sys.argv[1:3])
    sys.exit()
from mathutils import Vector, Matrix, kdtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npcb_common as C
from npcb_common import k3d

A, H = "NpcCafeStaff", 1.72
C.decals()      # 입, 폰 화면 (공용)
subprocess.check_call([k3d.PY, os.path.abspath(__file__), C.DEC, os.path.join(k3d.CACHE, "fonts")])   # 매번 다시 그린다
# extra_top: 모자는 없지만 매장 알바생과 같은 배율로 둔다 (PH/npc.py 의 NECK 값을 같이 쓴다). 머리 꼭대기는 1.71m.
arm, ms = C.load("npc_worker1", A, H, drop={"Head": ["Worker_Yellow", "Moustache"]}, extra_top=0.012)
head = ms["Head"]
mouth = C.face(head, push=0.7)    # 코를 더 줄여 어려 보이게
C.CLIPS += (("SitPointScreen", 80, C.prog_sitpoint, True),)   # 앉은 채 가리키기
C.author_clips(arm)
for m in ms.values():
    C.upgrade(m)

# ---------------------------------------------------------------- 재질
GREEN = (0.012, 0.070, 0.050)      # 짙은 초록 (후드티 카키와 겹치지 않게 푸른 쪽)
BROWN = (0.075, 0.034, 0.016)      # 진한 갈색
skin = C.skin(A + "_skin", (0.62, 0.43, 0.33), mouth=mouth)
hair = C.hair(A + "_hair", (0.035, 0.021, 0.014))
eye = C.flat(A + "_eye", (0.010, 0.008, 0.007), 0.12)
body, legs = ms["Body"], ms["Legs"]
ZC = arm.data.bones["Chest"].head_local.z - 0.025          # 가슴 로고·명찰 높이
hit = C.ray(body, (0.085, -1, ZC), (0, 1, 0))
chest_y = hit[0].y if hit else -0.16
polo = C.fabric(A + "_polo", GREEN, rough=0.86, grain=0.25, grain_scale=1400, folds=0.2,
                decals=[("cafe_logo.png", (0.085, chest_y, ZC), (0.075, 0.075))])
pants = C.fabric(A + "_pants", (0.032, 0.031, 0.034), rough=0.8, twill=0.12, wear=0.25, folds=0.06)
shoe = C.leather(A + "_shoe", (0.030, 0.016, 0.010), 0.38, scuff=0.25)
sole = C.flat(A + "_sole", (0.028, 0.027, 0.026), 0.9)
C.set_mats(head, {"Skin": skin, "Eye": eye, "*": hair})
C.set_mats(body, {"Skin": skin, "*": polo})
C.set_mats(legs, {"*": pants})
C.set_mats(ms["Feet"], {"Black": sole, "*": shoe})

# ---------------------------------------------------------------- 머리 (모자 대신 정수리 숱 + 앞머리 다발)
eye_lo, eye_hi = C.mat_bounds(head, [eye.name])
eye_z = (eye_lo[2] + eye_hi[2]) / 2
z_hl = eye_z + 0.056                       # 원래 이마선. 일자라서 앞머리로 덮는다
hair_i = [i for i, s_ in enumerate(head.material_slots) if s_.material == hair]
crown = Vector((0, -0.05, eye_z))
for i in {v for p in head.data.polygons if p.material_index in hair_i for v in p.vertices}:
    v = head.data.vertices[i]
    v.co += (v.co - crown).normalized() * 0.008 * C.ease((v.co.z - z_hl) / 0.035)
head.data.update()
bpy.context.view_layer.update()


def lock(bm, a0, tip, lean=-0.13, hw=0.145, nv=8):
    """이마를 따라 내려오는 머리 다발 하나 (a0, lean, hw 는 정면에서 잰 각도). 다발마다 섬이 달라야 hair_flow 가 결을 세로로 잡는다."""
    rows = []
    for j in range(nv + 1):
        t = j / nv
        z = z_hl + 0.024 + (tip - z_hl - 0.024) * t
        row = []
        for sd in (-1, 0, 1):
            a = a0 + lean * t * t + sd * hw * (1 - 0.92 * t ** 3)
            d = Vector((math.sin(a), -math.cos(a), 0))
            h = C.ray(head, Vector((0, crown.y, z)) + d * 0.3, -d)
            lift = -0.004 + (0.0085 if sd == 0 else 0.0055) * math.sin(math.pi * (0.1 + 0.62 * t))   # 윗끝은 머리 속에 묻힌다
            row.append(bm.verts.new(h[0] + h[1] * lift))
        rows.append(row)
    for j in range(nv):
        for c in range(2):
            bm.faces.new((rows[j][c], rows[j + 1][c], rows[j + 1][c + 1], rows[j][c + 1]))


bm = bmesh.new()
for k in range(8):
    u = -1 + 2 * k / 7                     # 오른쪽 관자놀이부터 왼쪽 가르마까지: 왼쪽으로 갈수록 짧다
    lock(bm, 0.6 * u, z_hl - 0.034 + 0.012 * (1 + u) + 0.004 * (-1) ** k + 0.010 * u ** 4)
fringe = C.new_obj(A + "_Fringe", bm, [hair])
k3d.smooth(fringe, 180)
C.rigid(fringe, "Head", arm)
head = C.join([head, fringe], A + "_Head")
C.hair_flow(head, [hair])

# ---------------------------------------------------------------- 앞치마 (허리 앞치마 + 끈 + 주머니 + 펜)
lv = [v.co for v in legs.data.vertices]
z_w = max(v.z for v in lv) - 0.028
band = [v for v in lv if abs(v.z - z_w) < 0.02]
ex = max(abs(v.x) for v in band) + 0.010
ey0, ey1 = min(v.y for v in band) - 0.010, max(v.y for v in band) + 0.010
ecy, ery = (ey0 + ey1) / 2, (ey1 - ey0) / 2
LEN = 0.43


def arc(bm, t0, t1, zt_, zb_, off, nu=28, nv=10, flare=0.10):
    rows = []
    for i in range(nu + 1):
        t = t0 + (t1 - t0) * i / nu
        col = []
        for j in range(nv + 1):
            d = j / nv
            z = zt_ + (zb_ - zt_) * d
            dz = max(0.0, (z_w - z) / LEN)
            k = 1 + flare * dz ** 1.5
            fwd = 0.06 * dz * math.cos(t) ** 2 if flare else 0.0     # 아래로 갈수록 허벅지에서 떨어짐 (자세에서 뚫림 방지)
            col.append(bm.verts.new(((ex + off) * k * math.sin(t), ecy - ((ery + off) * k + fwd) * math.cos(t), z)))
        rows.append(col)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))


bm = bmesh.new()
arc(bm, -1.72, 1.72, z_w - 0.01, z_w - LEN, 0.0, nu=20, nv=7)                     # 앞판
apron = C.new_obj(A + "_Apron", bm)
bm = bmesh.new()
arc(bm, -0.62, 0.62, z_w - 0.17, z_w - 0.31, 0.0035, nu=14, nv=4)                 # 주머니
pocket = C.new_obj(A + "_Pocket", bm)
bm = bmesh.new()
arc(bm, 0.0, 2 * math.pi, z_w + 0.012, z_w - 0.022, 0.0045, nu=40, nv=2, flare=0)  # 허리끈
bm.verts.ensure_lookup_table()
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
for s in (-1, 1):                                                                  # 뒤 매듭 꼬리
    x0 = 0.022 * s
    v = [bm.verts.new((x0 - 0.014, ey1 + 0.003, z_w - 0.01)), bm.verts.new((x0 + 0.014, ey1 + 0.003, z_w - 0.01)),
         bm.verts.new((x0 + 0.02 * s + 0.012, ey1 + 0.012, z_w - 0.26)), bm.verts.new((x0 + 0.02 * s - 0.012, ey1 + 0.012, z_w - 0.26))]
    bm.faces.new(v)
bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.018,
                          matrix=Matrix.Translation((0, ey1 + 0.006, z_w - 0.005)) @ Matrix.Diagonal((1.3, 0.5, 0.8, 1)))
belt = C.new_obj(A + "_Belt", bm)
for o in (apron, pocket, belt):
    sol = o.modifiers.new("Sol", 'SOLIDIFY')
    sol.thickness, sol.offset = 0.0022, 1.0
    sub = o.modifiers.new("Sub", 'SUBSURF')
    sub.levels = 1
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier="Sol")
    bpy.ops.object.modifier_apply(modifier="Sub")
    k3d.smooth(o, 180)
# 펜 두 자루 (주머니에 꽂힘)
bm = bmesh.new()
for tx, col in ((-0.55, 0), (-0.47, 1)):   # 로고를 가리지 않게 주머니 오른쪽 끝
    dz = 0.19 / LEN                                                   # 앞치마 arc() 와 같은 곡면 + 1.1cm 앞
    k = 1 + 0.10 * dz ** 1.5
    x, y = (ex + 0.011) * k * math.sin(tx), ecy - ((ery + 0.011) * k + 0.06 * dz * math.cos(tx) ** 2) * math.cos(tx)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0048, radius2=0.0048, depth=0.10,
                          matrix=Matrix.Translation((x, y, z_w - 0.195)) @ Matrix.Rotation(0.08 * (1 if col else -1), 4, 'Y'))
pens = C.new_obj(A + "_Pens", bm)
k3d.smooth(pens, 40)
apronm = C.fabric(A + "_apron", BROWN, rough=0.88, twill=0.3, wear=0.5, folds=0.12, cavity=0.55,
                  decals=[("cafe_logo_worn.png", (0.0, ecy - ery - 0.02, z_w - 0.105), (0.13, 0.13))])
penm = C.flat(A + "_pen", (0.05, 0.05, 0.06), 0.3, 0.0)
for o in (apron, pocket, belt):
    o.data.materials.append(apronm)
pens.data.materials.append(penm)
# 웨이트: 위쪽은 바지 허리 웨이트 복사, 아래로 갈수록 허벅지(좌/우)
kd = kdtree.KDTree(len(legs.data.vertices))
for v in legs.data.vertices:
    kd.insert(v.co, v.index)
kd.balance()
gname = {g.index: g.name for g in legs.vertex_groups}
for o in (apron, pocket, belt):
    groups = {}
    for v in o.data.vertices:
        _, idx, _ = kd.find(v.co)
        base = {gname[g.group]: g.weight for g in legs.data.vertices[idx].groups}
        if o is belt and v.co.z < z_w - 0.03:      # 뒤 매듭 꼬리: 허벅지를 따라가면 앉을 때 다리 사이로 뚫고 나온다
            base = {"Hips": 1.0}
        wl = 0.0 if o is belt else C.ease((z_w - 0.03 - v.co.z) / 0.11)   # 로고 높이부터 허벅지를 따라감
        sl = C.ease((v.co.x + 0.05) / 0.10)
        w = {k: x * (1 - wl) for k, x in base.items()}
        w["UpperLeg.L"] = w.get("UpperLeg.L", 0) + wl * sl
        w["UpperLeg.R"] = w.get("UpperLeg.R", 0) + wl * (1 - sl)
        tot = sum(w.values()) or 1.0
        for k, x in w.items():
            if x > 1e-4:
                if k not in groups:
                    groups[k] = o.vertex_groups.new(name=k)
                groups[k].add([v.index], x / tot, 'REPLACE')
    C.add_armature(o, arm)

C.rigid(pens, "UpperLeg.R", arm)   # 주머니(오른쪽 허벅지 100%)와 함께 움직임

# ---------------------------------------------------------------- 폴로 칼라·플라켓·소매 밴드·밑단
colm = C.fabric(A + "_collar", C.sc(GREEN, 0.82), rough=0.88, grain=0.2, grain_scale=1400, folds=0.04, cavity=0.55)
rib = colm.node_tree.nodes.new('ShaderNodeTexWave')            # 립 결 (세로 골)
rib.bands_direction = 'X'
rib.inputs['Scale'].default_value = 700.0
colm.node_tree.links.new(next(n for n in colm.node_tree.nodes if n.type == 'TEX_COORD').outputs['Object'], rib.inputs['Vector'])
bmp = colm.node_tree.nodes.new('ShaderNodeBump')
bmp.inputs['Strength'].default_value, bmp.inputs['Distance'].default_value = 0.35, 0.0005
colm.node_tree.links.new(rib.outputs['Fac'], bmp.inputs['Height'])
pr = C.k3d.principled(colm)
old = pr.inputs['Normal'].links[0].from_socket if pr.inputs['Normal'].links else None
if old:
    colm.node_tree.links.new(old, bmp.inputs['Normal'])
colm.node_tree.links.new(bmp.outputs['Normal'], pr.inputs['Normal'])
nk = arm.data.bones["Neck"].head_local
UP = Vector((0, 0, 1))


def hit2(objs, o_, d_):
    best = None
    for ob in objs:
        r = C.ray(ob, o_, d_)
        if r and (best is None or (r[0] - Vector(o_)).length < (best[0] - Vector(o_)).length):
            best = r
    return best


# 칼라: 목(머리 메시) 바로 밖 6mm 에서 몸 윗면까지 -> 스탠드(위로) -> 폴(바깥 아래로 덮음). 앞은 플라켓 폭만큼 열림.
T0, NS = 0.36, 34
rows = []
for i in range(NS + 1):
    th = T0 + (2 * math.pi - 2 * T0) * i / NS
    d = Vector((math.sin(th), -math.cos(th), 0))
    nh = C.ray(head, Vector((0, nk.y, nk.z + 0.03)) + d * 0.3, -d)
    if not nh:
        continue
    q = nh[0] + d * 0.006
    bh = C.ray(body, (q.x, q.y, q.z + 0.25), (0, 0, -1))
    if not bh:
        continue
    zb = bh[0].z
    front = 1 - C.ease((min(th, 2 * math.pi - th) - T0) / 0.55)          # 1 = 앞 끝 (깃끝)
    stand = 0.016 - 0.004 * front
    p0 = Vector((q.x, q.y, zb - 0.004))
    p1 = Vector((q.x, q.y, zb + stand)) + d * 0.002
    tgt = p1 + d * (0.026 + 0.012 * front) - UP * (0.016 + 0.03 * front)
    oh = hit2([body], tgt + d * 0.08 + UP * 0.05, -(d * 0.08 + UP * 0.05))
    p2 = (oh[0] + oh[1] * 0.0035) if oh else tgt
    rows.append((p0, p1, p2))
bm = bmesh.new()
vv = [[bm.verts.new(p) for p in r] for r in rows]
for i in range(len(vv) - 1):
    for j in range(2):
        bm.faces.new((vv[i][j], vv[i + 1][j], vv[i + 1][j + 1], vv[i][j + 1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
collar = C.new_obj(A + "_Collar", bm, [colm])
zc_front = rows[0][0].z + 0.004 if rows else nk.z - 0.03
# 플라켓 3 x 12cm (몸 표면 따라) + 단추 2개
bm = bmesh.new()
grid = []
for j in range(9):
    z = zc_front - 0.12 * j / 8
    grid.append([])
    for i in range(3):
        x = -0.015 + 0.015 * i
        h = C.ray(body, (x, -1, z), (0, 1, 0))
        grid[-1].append(bm.verts.new(h[0] + h[1] * 0.0018 if h else Vector((x, -0.15, z))))
for j in range(8):
    for i in range(2):
        bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
plk = C.new_obj(A + "_Placket", bm, [polo])
bm = bmesh.new()
for z in (zc_front - 0.03, zc_front - 0.075):
    h = C.ray(body, (0, -1, z), (0, 1, 0))
    if h:
        rot = Vector((0, 0, 1)).rotation_difference(-h[1]).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0052, radius2=0.0048, depth=0.0018,
                              matrix=Matrix.Translation(h[0] + h[1] * 0.0042) @ rot)
btn = C.new_obj(A + "_PoloButtons", bm, [C.flat(A + "_button", (0.78, 0.74, 0.66), 0.35)])
# 소매 밴드: 피부/폴로 경계(톱니)를 덮는 립 밴드
sk_i = [i for i, s_ in enumerate(body.material_slots) if s_.material == skin]
edge_x = {1: [], -1: []}
bmb = bmesh.new()
bmb.from_mesh(body.data)
for e in bmb.edges:
    f_ = e.link_faces
    if len(f_) == 2 and (f_[0].material_index in sk_i) != (f_[1].material_index in sk_i):
        for v in e.verts:
            if abs(v.co.x) > 0.2:
                edge_x[1 if v.co.x > 0 else -1].append(abs(v.co.x))
bmb.free()
bm = bmesh.new()
for sd in (1, -1):
    xs_ = edge_x[sd]
    if not xs_:
        continue
    ua = arm.data.bones["UpperArm." + ("L" if sd > 0 else "R")].head_local
    xa, xb = min(xs_) - 0.004, max(xs_) + 0.004
    ring = []
    for x in (xa, (xa + xb) / 2, xb):
        row = []
        for k in range(24):
            ph = 2 * math.pi * k / 24
            d = Vector((0, math.cos(ph), math.sin(ph)))
            c_ = Vector((sd * x, ua.y, ua.z))
            h = C.ray(body, c_ + d * 0.15, -d)
            row.append(bm.verts.new((h[0] + d * 0.003) if h else c_ + d * 0.05))
        ring.append(row)
    for r in range(2):
        for k in range(24):
            bm.faces.new((ring[r][k], ring[r][(k + 1) % 24], ring[r + 1][(k + 1) % 24], ring[r + 1][k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
cuffs = C.new_obj(A + "_Cuffs", bm, [colm])
# 밑단: 폴로/바지 교차선(톱니)을 덮는 밑단 띠 (앞치마 허리끈 바로 위)
hp = arm.data.bones["Hips"].head_local
bm = bmesh.new()
ring = []
for z in (z_w + 0.010, z_w + 0.022, z_w + 0.034):
    row = []
    for k in range(32):
        th = 2 * math.pi * k / 32
        d = Vector((math.sin(th), -math.cos(th), 0))
        c_ = Vector((0, hp.y, z))
        h = hit2([body, legs], c_ + d * 0.4, -d)
        row.append(bm.verts.new((h[0] + d * 0.003) if h else c_ + d * 0.15))
    ring.append(row)
for r in range(2):
    for k in range(32):
        bm.faces.new((ring[r][k], ring[r][(k + 1) % 32], ring[r + 1][(k + 1) % 32], ring[r + 1][k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
hem = C.new_obj(A + "_Hem", bm, [polo])
for o, t in ((collar, 0.0025), (plk, 0.002), (cuffs, 0.002), (hem, 0.002)):
    sol = o.modifiers.new("Sol", 'SOLIDIFY')
    sol.thickness, sol.offset = t, -1.0
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier="Sol")
    C.bevel_obj(o, 0.0007, 1)
    k3d.smooth(o, 180)
C.bevel_obj(btn, 0.0006, 1)
C.copy_weights(body, [collar, plk, btn, cuffs, hem])

# ---------------------------------------------------------------- 명찰 (오른쪽 가슴)
hit = C.ray(body, (-0.088, -1, ZC + 0.006), (0, 1, 0))
p0, n0 = hit
bm = bmesh.new()
C.bm_box(bm, (0.070, 0.0035, 0.024))
uvl = bm.loops.layers.uv.verify()
for f in bm.faces:
    if f.normal.y < -0.9:
        for l in f.loops:
            l[uvl].uv = (l.vert.co.x / 0.070 + 0.5, l.vert.co.z / 0.024 + 0.5)
tag = C.new_obj(A + "_NameTag", bm)
C.bevel_obj(tag, 0.0012, 2)
rot = Vector((0, -1, 0)).rotation_difference(n0).to_matrix().to_4x4()
tag.data.transform(Matrix.Translation(p0 + n0 * 0.0022) @ rot)
tb = C.NB(A + "_tag", (0.9, 0.9, 0.9), 0.3)
ti = tb.node('ShaderNodeTexImage')
ti.image = k3d.load_image(os.path.join(C.DEC, "cafe_nametag.png"))
uvn = tb.node('ShaderNodeUVMap', uv_map="UVMap")
tb.L(uvn.outputs[0], ti.inputs['Vector'])
edge = tb.math('LESS_THAN', tb.math('ABSOLUTE', tb.NY), 0.5)
tb.done(tb.mixc(edge, ti.outputs['Color'], (0.75, 0.74, 0.72)), 0.28)
tag.data.materials.append(tb.m)
C.rigid(tag, "Chest", arm)

# ---------------------------------------------------------------- 합치기 · 폰 · 베이크
phone = C.phone(A, arm)
body_o = C.join([body, legs, ms["Feet"], apron, pocket, belt, pens, tag, collar, plk, btn, cuffs, hem], A + "_Body")
assert "HairUV" in head.data.uv_layers, "HairUV 없음 -> 머리카락 결이 단색으로 구워짐"
C.bake_all(arm, [(body_o, 2048, 0.05), (head, 1024, 0.03), (phone, 512, 0.01)])

# ---------------------------------------------------------------- 소켓
bones = arm.data.bones
eye_c = (Vector(eye_lo) + Vector(eye_hi)) / 2
palm_r = (bones["Wrist.R"].head_local + bones["Middle2.R"].head_local) / 2
palm_l = (bones["Wrist.L"].head_local + bones["Middle2.L"].head_local) / 2
hip = bones["UpperLeg.L"].head_local
C.socket(A + "_Socket_Head", arm, "Head", (0, eye_c.y + 0.07, eye_c.z))
C.socket(A + "_Socket_HandR", arm, "Wrist.R", palm_r)
C.socket(A + "_Socket_HandL", arm, "Wrist.L", palm_l)
C.socket(A + "_Socket_Seat", arm, None, (0, hip.y + 0.09, C.SEAT))

notes = {
    "replaces": "없음 (새 인물). 2회차 카페 '숲길 커피' 직원, PH_NPC look 10 자리",
    "look": "20대: 모자 없음, 앞머리 있는 갈색 머리, 짙은 초록 폴로(왼가슴 잎 로고, 오른가슴 카페 명찰), 진한 갈색 허리 앞치마(잎과 '숲길 커피' 로고, 주머니, 펜), 짙은 회색 바지, 짙은 갈색 구두. 머리 꼭대기 1.71m.",
    "rig": "Quaternius CharacterArmature 62본 유지 (Foot.L/R·PT 는 Root 자식). Generic 리그로 쓸 것 (Humanoid 는 발 계층 때문에 불가).",
    "clips": "Idle, Idle_Neutral, Walk, Run, Wave, Interact (원본) + SitPhone(120f 루프, 좌판 0.65m), "
             "SitPointScreen(80f: 앉은 채 폰은 오른손에 두고 왼손 검지로 정면 키오스크를 가리킴 — 0/80 프레임 = SitPhone 0프레임), "
             "Phone(80f 루프), Impatient(80f 루프: 팔짱+발끝 까딱+한숨), PointScreen(80f: 선 자세 오른손 검지 가리킴, 0/80 프레임은 Idle), "
             "LookBack(80f: 오른쪽 어깨 너머 돌아봄 후 복귀). 24fps.",
    "objects": "NpcCafeStaff_Body(몸·폴로(칼라·플라켓·단추·소매 립 밴드·밑단)·앞치마·명찰), NpcCafeStaff_Head(머리), NpcCafeStaff_Phone(오른손 폰, Phone/SitPhone/SitPointScreen 때만 켤 것)",
    "sockets": "NpcCafeStaff_Socket_Head(Head 본, 시선/자막 기준), _HandR/_HandL(손바닥 중심, 소품 부착), "
               "_Socket_Seat(SitPhone 때 의자 좌판 윗면 중심이 올 위치, 아마추어 기준)",
    "dynamic": "없음",
    "clips_dropped": "원본 24 클립 중 버림: Death, Gun_Shoot, HitRecieve, HitRecieve_2, Idle_Gun, Idle_Gun_Pointing, Idle_Gun_Shoot, "
                     "Idle_Sword, Kick_Left, Kick_Right, Punch_Left, Punch_Right, Roll, Run_Back, Run_Left, Run_Right, Run_Shoot, Sword_Slash",
    "phone": "Phone/SitPhone 은 한 손 파지(손가락이 폰 왼쪽 모서리를 감쌈), 화면이 눈을 향함. 다른 클립에서는 NpcCafeStaff_Phone 을 끌 것.",
}
k3d.export(A, "Characters", [arm], rigged=True, anim=True, notes=notes)
C.previews(A, arm, clip_frames={"SitPhone": 30, "SitPointScreen": 34, "PointScreen": 30, "Impatient": 6, "LookBack": 36, "Phone": 20})
C.play(arm, "SitPhone", 30)
C.shot(A, "fp", (0.0, -1.45, 1.55), (0.0, 0.0, 1.12), lens=35)
bpy.context.view_layer.update()
pv = phone.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().vertices
pc = sum((v.co for v in pv), Vector()) / len(pv)      # 폰 중심 (아마추어 항등 변환)
C.shot(A, "fp_hand", (0.0, -1.2, 1.5), pc, lens=60, res=(1000, 750))
C.play(arm, "SitPointScreen", 34)
C.shot(A, "fp_sitpoint", (0.7, -1.4, 1.55), (0.0, 0.0, 1.1), lens=35)
C.play(arm, "PointScreen", 30)
C.shot(A, "fp_point", (0.25, -1.3, 1.55), (0.0, 0.0, 1.3), lens=35)
C.play(arm, "Idle", 10)
C.shot(A, "face", (0.15, -0.75, 1.62), (0.0, 0.0, 1.55), lens=50)
C.play(arm, "Idle_Neutral", 0)      # PH_NPC 가 쓰는 정적 자세
C.shot(A, "3m", (0.4, -3.0, 1.55), (0.0, 0.0, 0.95), lens=35)
C.validate(os.path.join(k3d.ART, "Models", "Characters", A + ".fbx"), H)

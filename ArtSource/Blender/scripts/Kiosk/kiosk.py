"""셀프 주문 키오스크 (HERO).  blender -b --factory-startup --python kiosk.py [-- B]
A = 매장 주문 키오스크 'Kiosk' (프로토 pe.KX), B = 옆의 '점검 중' 키오스크 'Kiosk_B' (pe.K2X).
배치 좌표는 kiosk_tex.LAYOUT 과 공유. 블렌더: 미터, Z 위, 정면 = -Y, 원점 = 바닥 중앙."""
import bpy, bmesh, math, os, sys, json, subprocess
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "Store"))
sys.path.insert(0, HERE)
import k3d  # noqa: E402
import storelib as S  # noqa: E402  베벨 박스·절차 PBR 공용 도우미 (매장 그룹)
from kiosk_tex import LAYOUT as L  # noqa: E402

VAR = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv[:-1] else "A"
N = "Kiosk" if VAR == "A" else "Kiosk_B"
TEXD = os.path.join(k3d.ART, "Textures", "Kiosk")
SRC = os.path.join(k3d.CACHE, "kiosk_src")
need = [os.path.join(TEXD, f) for f in ("T_Kiosk_Panel.png", "T_Kiosk_Paper_BaseColor.jpg", "T_Kiosk_Screen_Off.png")]
if not all(map(os.path.exists, need + [os.path.join(SRC, "src_smudge.png")])):
    subprocess.run([k3d.PY, os.path.join(HERE, "kiosk_tex.py"), k3d.REPO, k3d.CACHE], check=True)
ATL = json.load(open(os.path.join(SRC, "paper_atlas.json")))

k3d.reset()
W, D, Z0, Z1 = L['W'], L['D'], L['Z0'], L['Z1']
ZC = (Z0 + Z1) / 2
FY = L['FY']            # 전면 브러시드 판 앞면 (-0.057)
PY = -0.0590            # 조작부 판 앞면
SX, SZ, SW, SH = L['SCR']
HZ = 1.849              # 상단 간판 중심


# ---------------------------------------------------------------- 형상 도우미
def rrect(w, h, r, seg=6):
    """XZ 둥근 사각형 (정면에서 반시계)."""
    r = max(0.0004, min(r, w / 2 - 1e-4, h / 2 - 1e-4))
    pts = []
    for cx, cz, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def prism(name, w, h, r, y0, y1, loc=(0, 0, 0), mat=None, bev=0.002, seg=6, hole=None, bseg=2):
    """정면 둥근 사각 판 (y0 앞면 -> y1 뒷면). hole=(w, h, r): 가운데가 뚫린 틀."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    o = [bm.verts.new((x, y0, z)) for x, z in rrect(w, h, r, seg)]
    if hole:
        i = [bm.verts.new((x, y0, z)) for x, z in rrect(*hole, seg)]
        n = len(o)
        for k in range(n):
            bm.faces.new((o[k], o[(k + 1) % n], i[(k + 1) % n], i[k]))
    else:
        bm.faces.new(o)
    ext = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces), use_keep_orig=True)
    bmesh.ops.translate(bm, verts=[g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)], vec=(0, y1 - y0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = S.obj_from_bm(name, bm, loc, None, mat)
    if bev:
        S.bevel(ob, bev, bseg)
    return ob


def slab(name, w, d, r, z0, z1, mat, bev=0.003):
    """바닥에 눕힌 둥근 사각 판."""
    ob = prism(name, w, d, r, 0, z1 - z0, mat=mat, bev=0)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    S.apply_tf(ob)
    ob.location.z = z0
    if bev:
        S.bevel(ob, bev, 2)
    return ob


def ycyl(name, r, y0, y1, x, z, mat, n=24, bev=0.0008):
    """정면을 보는 원통 (y0 앞 -> y1 뒤)."""
    return S.cyl(name, r, abs(y1 - y0), (x, (y0 + y1) / 2, z), mat, n, bev, rot=(math.pi / 2, 0, 0))


def uv_planar(o, x0, x1, z0, z1, vk=2):
    """로컬 평면 투영 UV (데칼용). vk = V 로 쓸 로컬 축 (2=Z, 원통은 1=Y)."""
    me = o.data
    uvl = me.uv_layers[0]
    for lp in me.loops:
        c = me.vertices[lp.vertex_index].co
        uvl.data[lp.index].uv = ((c.x - x0) / (x1 - x0), (c[vk] - z0) / (z1 - z0))


def grid(name, w, h, nx, nz, fn, uv, mat, back_uv=None, mirror_back=True, gap=0.0003):
    """XZ 격자 종이 (정면 -Y). fn(u, v) = 앞(-Y)으로 띄우는 양. uv=(u0,v0,u1,v1) 아틀라스. back_uv: 뒷면."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    layers = [(uv, 0.0, False)] + ([(back_uv, gap, True)] if back_uv else [])
    for (u0, v0, u1, v1), off, flip in layers:
        vs = [[bm.verts.new(((i / nx - .5) * w, -fn(i / nx, j / nz) + off, (j / nz - .5) * h)) for i in range(nx + 1)] for j in range(nz + 1)]
        for j in range(nz):
            for i in range(nx):
                q = (vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i])
                f = bm.faces.new(q[::-1] if flip else q)
                for lp in f.loops:
                    c = lp.vert.co
                    uu, vv = c.x / w + .5, c.z / h + .5
                    if flip and mirror_back:
                        uu = 1 - uu
                    lp[uvl].uv = (u0 + (u1 - u0) * uu, v0 + (v1 - v0) * vv)
    ob = S.obj_from_bm(name, bm, mat=mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ---------------------------------------------------------------- 머티리얼 (굽기용 절차)
def decal(m, path, uv="UVMap"):
    """굽는 머티리얼 위에 RGBA 인쇄 데칼을 알파로 섞는다 (UVMap 평면 투영)."""
    nt, p = m.node_tree, k3d.principled(m)
    bc = p.inputs['Base Color']
    src = bc.links[0].from_socket if bc.is_linked else tuple(bc.default_value)
    t = k3d.image_node(m, k3d.load_image(path), None, uv=uv)
    t.extension = 'CLIP'
    nt.links.new(S._mix(nt, src, t.outputs['Color'], t.outputs['Alpha']), bc)
    return m


def smudge(m, amt=1.0, tile=0.45):
    """손 닿는 높이(0.5~1.3m)에 몰린 지문/문지름(R)·잔흠집(G) 마스크 (src_smudge.png 박스 투영)."""
    nt, p = m.node_tree, k3d.principled(m)
    tc = S._n(nt, 'ShaderNodeTexCoord').outputs['Object']
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / tile,) * 3
    nt.links.new(tc, mp.inputs['Vector'])
    ti = nt.nodes.new('ShaderNodeTexImage')
    ti.image = k3d.load_image(os.path.join(SRC, "src_smudge.png"), non_color=True)
    ti.projection, ti.projection_blend = 'BOX', 0.2
    nt.links.new(mp.outputs[0], ti.inputs['Vector'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(ti.outputs['Color'], sep.inputs['Color'])
    xyz = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc, xyz.inputs[0])
    zone = S._math(nt, 'MULTIPLY', S._ramp(nt, xyz.outputs['Z'], 0.35, 0.7), S._ramp(nt, xyz.outputs['Z'], 1.5, 1.1))
    sm = S._math(nt, 'MULTIPLY', sep.outputs['Red'], S._math(nt, 'MULTIPLY', S._math(nt, 'ADD', 0.25, zone, False), amt, False))
    bc, rg = p.inputs['Base Color'], p.inputs['Roughness']
    b0 = bc.links[0].from_socket
    b1 = S._mix(nt, b0, S._mix(nt, b0, (0.0, 0.0, 0.0), 0.25), sm)
    b2 = S._mix(nt, b1, (0.8, 0.8, 0.78), S._math(nt, 'MULTIPLY', sep.outputs['Green'], 0.18 * amt))
    nt.links.new(b2, bc)
    r0 = rg.links[0].from_socket
    nt.links.new(S._math(nt, 'ADD', S._math(nt, 'ADD', r0, S._math(nt, 'MULTIPLY', sm, 0.45)),
                         S._math(nt, 'MULTIPLY', sep.outputs['Green'], 0.12 * amt)), rg)
    return m


m_powder = S.pbr("kPowder", (0.068, 0.072, 0.08), 0.48, 0.0, var=0.05, grime=0.5, gdist=0.03, edge=0.6,
                 edge_col=(0.2, 0.2, 0.21), bump=0.06, bscale=520, scratch=0.25, smudge=0.25, streak=0.15)
m_brushed = smudge(S.pbr("kBrushed", (0.5, 0.49, 0.47), 0.3, 1.0, var=0.04, grime=0.35, gdist=0.015, brush=0.35,
                         scratch=0.25, bump=0.015, rvar=0.1))
m_brushed2 = S.pbr("kBrushed2", (0.42, 0.415, 0.4), 0.34, 1.0, var=0.05, grime=0.45, gdist=0.01, brush=0.3, scratch=0.35, edge=0.3)
m_alu = S.pbr("kAlu", (0.1, 0.1, 0.105), 0.38, 1.0, var=0.05, grime=0.4, gdist=0.02, edge=0.5, edge_col=(0.55, 0.55, 0.56), scratch=0.35)
m_bglass = S.pbr("kBGlass", (0.004, 0.004, 0.005), 0.05, 0.0, var=0.0, grime=0.15, gdist=0.004, bump=0, rvar=0.02, coat=1.0)
m_black = S.pbr("kBlack", (0.005, 0.005, 0.005), 0.75, 0.0, var=0.0, grime=0.0, bump=0)
m_term = decal(S.pbr("kTerm", (0.011, 0.011, 0.012), 0.42, 0.0, var=0.05, grime=0.5, gdist=0.006, edge=0.4,
                     edge_col=(0.07, 0.07, 0.07), smudge=0.35, bump=0.03, bscale=300), os.path.join(SRC, "src_terminal.png"))
m_key = decal(S.pbr("kKey", (0.04, 0.037, 0.034), 0.62, 0.0, var=0.05, grime=0.4, gdist=0.003, edge=0.5,
                    edge_col=(0.09, 0.085, 0.08), smudge=0.4, bump=0.02), os.path.join(SRC, "src_terminal.png"))
m_fn = [decal(S.pbr("kFn%d" % i, c, 0.45, 0.0, var=0.05, grime=0.3, gdist=0.003, edge=0.4, smudge=0.3, bump=0.02),
              os.path.join(SRC, "src_terminal.png")) for i, c in enumerate(((0.45, 0.028, 0.018), (0.58, 0.36, 0.035), (0.03, 0.24, 0.05)))]
m_red = decal(S.pbr("kCall", (0.26, 0.012, 0.008), 0.3, 0.0, var=0.06, grime=0.3, gdist=0.004, edge=0.5, smudge=0.5, bump=0.02),
              os.path.join(SRC, "src_bell.png"))
m_nfc = decal(S.pbr("kNfc", (0.008, 0.008, 0.009), 0.12, 0.0, var=0.0, grime=0.3, gdist=0.004, smudge=0.6, bump=0, coat=0.6),
              os.path.join(SRC, "src_nfc.png"))
m_chrome = S.pbr("kChrome", (0.75, 0.75, 0.74), 0.16, 1.0, var=0.02, grime=0.4, gdist=0.004, scratch=0.3, bump=0)
m_rubber = S.pbr("kRubber", (0.018, 0.018, 0.018), 0.85, 0.0, var=0.08, grime=0.5, gdist=0.01, bump=0.08, bscale=200)
m_cable = S.pbr("kCable", (0.014, 0.014, 0.015), 0.55, 0.0, var=0.06, grime=0.3, bump=0.03)
m_lan = S.pbr("kLan", (0.16, 0.2, 0.26), 0.5, 0.0, var=0.06, grime=0.3, bump=0.02)
m_steel = S.pbr("kSteel", (0.3, 0.3, 0.29), 0.45, 1.0, var=0.08, grime=0.7, gdist=0.04, edge=0.7, edge_col=(0.6, 0.6, 0.58),
                scratch=0.7, streak=0.2, bump=0.05)
m_post = S.pbr("kPost", (0.55, 0.54, 0.52), 0.25, 1.0, var=0.04, grime=0.5, gdist=0.03, scratch=0.5, smudge=0.4, bump=0.01)
m_screw = S.pbr("kScrew", (0.42, 0.42, 0.43), 0.35, 1.0, var=0.05, grime=0.6, gdist=0.002, bump=0)
m_board = S.pbr("kBoard", (0.012, 0.012, 0.013), 0.22, 0.0, var=0.03, grime=0.4, gdist=0.01, edge=0.5, edge_col=(0.12, 0.12, 0.12),
                scratch=0.4, bump=0, coat=0.5)
m_clip = S.pbr("kClip", (0.035, 0.035, 0.037), 0.5, 0.0, var=0.05, grime=0.5, gdist=0.005, edge=0.4, bump=0.03)
m_redglass = S.pbr("kRedGlass", (0.06, 0.003, 0.002), 0.04, 0.0, var=0.0, grime=0.2, gdist=0.003, bump=0, coat=1.0)
m_laser = k3d.mat("kLaser", (0.6, 0.02, 0.01), 0.3, emission=(1.0, 0.04, 0.02), strength=4.0)
m_led = k3d.mat("kLed", (0.05, 0.5, 0.15), 0.3, emission=(0.12, 1.0, 0.3), strength=4.0)
m_lens = S.pbr("kLens", (0.002, 0.002, 0.003), 0.03, 0.0, var=0.0, grime=0.0, bump=0, coat=1.0)
m_rating = decal(S.pbr("kRating", (0.55, 0.56, 0.57), 0.5, 0.0, var=0.03, grime=0.4, bump=0.02), os.path.join(SRC, "src_rating.png"))

parts, cparts = [], []          # 본체(2048) / 조작부 부품(1024: 작은 인쇄 글자가 선명하도록 따로 굽기)
add, cadd = parts.append, cparts.append

# ---------------------------------------------------------------- 받침 (수평 조절 발 + 판 + 기둥 2)
add(slab("p_base", 0.66, 0.46, 0.05, 0.012, 0.032, m_steel, 0.004))
for x in (-0.29, 0.29):
    for y in (-0.19, 0.19):
        add(S.cyl("p_pad", 0.022, 0.006, (x, y, 0.003), m_rubber, 24, 0.0015))
        add(S.cyl("p_stem", 0.006, 0.012, (x, y, 0.012), m_screw, 12, 0.0005))
        add(S.cyl("p_nut", 0.011, 0.006, (x, y, 0.035), m_screw, 6, 0.0008))
        add(S.cyl("p_rod", 0.0055, 0.008, (x, y, 0.042), m_screw, 12, 0.0006))
for x in (-0.13, 0.13):
    add(S.cyl("p_post", 0.03, Z0 - 0.032 + 0.01, (x, 0.015, (0.032 + Z0) / 2), m_post, 32, 0.0015))
    add(S.cyl("p_flange", 0.052, 0.012, (x, 0.015, 0.038), m_alu, 32, 0.003))
    add(S.cyl("p_flange_t", 0.046, 0.01, (x, 0.015, Z0 - 0.005), m_alu, 32, 0.0025))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        add(S.cyl("p_bolt", 0.0065, 0.004, (x + math.cos(a) * 0.04, 0.015 + math.sin(a) * 0.04, 0.046), m_screw, 6, 0.0006))

# ---------------------------------------------------------------- 본체
add(prism("b_body", W, Z1 - Z0, 0.03, -D / 2, D / 2, (0, 0, ZC), m_powder, 0.006, 8, bseg=3))
for sx in (-1, 1):  # 옆면 알루미늄 몰딩
    add(S.box("b_rail", (0.02, D + 0.016, Z1 - Z0 - 0.07), (sx * 0.302, 0, ZC), m_alu, 0.0065, 3))
add(prism("b_front", W - 0.012, Z1 - Z0 - 0.012, 0.024, FY, -D / 2 + 0.0004, (0, 0, ZC), m_brushed, 0.0012, 8))
# 상단 라이트박스 간판 하우징 + 앞 테두리
add(prism("b_head", W + 0.03, 0.098, 0.012, -0.058, 0.058, (0, 0, HZ), m_powder, 0.004))
add(prism("b_headlip", W + 0.03, 0.098, 0.012, -0.061, -0.0575, (0, 0, HZ), m_alu, 0.0012, hole=(0.612, 0.088, 0.006)))
for x in (-0.24, -0.08, 0.08, 0.24):  # 위쪽 방열 슬롯
    add(S.box("b_hvent", (0.11, 0.008, 0.0012), (x, 0.0, HZ + 0.0492), m_black, 0.0003, 1))
# 화면 베젤 (검은 유리 틀, 화면은 5mm 안쪽)
add(prism("b_bezel", L['BEZ'][0], L['BEZ'][1], 0.012, -0.065, FY + 0.0004, (SX, 0, SZ), m_bglass, 0.0012,
          hole=(SW + 0.002, SH + 0.002, 0.0015)))
cz = SZ + SH / 2 + 0.0145
add(ycyl("b_cam_ring", 0.0052, -0.0652, -0.064, 0.0, cz, m_alu, 20, 0.0003))
add(ycyl("b_cam_lens", 0.0034, -0.0656, -0.0645, 0.0, cz, m_lens, 20, 0.0003))
add(ycyl("b_cam_led", 0.0011, -0.0653, -0.064, 0.012, cz, m_led, 10, 0))
# 조작부 판 테두리 (판 자체는 동적 텍스처 Kiosk_Panel)
pcx, pcz, pw, ph = L['PANEL']
add(prism("b_pframe", pw + 0.014, ph + 0.014, 0.012, PY, FY + 0.0004, (pcx, 0, pcz), m_brushed2, 0.001))
for x in (-1, 1):
    for z in (-1, 1):
        add(ycyl("b_pscrew", 0.0028, PY - 0.0012, PY + 0.0002, x * (pw / 2 + 0.0035), pcz + z * (ph / 2 + 0.0035), m_screw, 12, 0.0004))

# ---------------------------------------------------------------- 슬롯 모듈 4개 (모양이 거의 같아 헷갈리게)
mw, mh, mt = L['MOD']
MY0, MY1 = PY + 0.0002, PY - mt          # 모듈 뒤/앞 y
HOLES = {'barcode': (0.104, 0.016, 0.002), 'receipt': (0.092, 0.0068, 0.001), 'ic': (0.09, 0.0052, 0.001), 'member': (0.09, 0.0052, 0.001)}
for k, (x, z) in L['MODS'].items():
    hw, hh, hr = HOLES[k]
    cadd(prism("m_bezel_" + k, mw, mh, 0.008, MY1, MY0, (x, 0, z), m_brushed2, 0.0014, hole=(hw, hh, hr)))
    cadd(prism("m_well_" + k, hw + 0.002, hh + 0.002, hr, MY1 + 0.006, MY0 + 0.0001, (x, 0, z), m_black, 0))
    for sx in (-1, 1):
        cadd(ycyl("m_screw", 0.0019, MY1 - 0.0005, MY1 + 0.001, x + sx * (mw / 2 - 0.0045), z, m_screw, 10, 0.0003))
    if k == 'barcode':
        cadd(prism("m_window", hw + 0.001, hh + 0.001, 0.0015, MY1 + 0.0025, MY1 + 0.0045, (x, 0, z), m_redglass, 0.0004))
        cadd(S.box("m_laser", (0.086, 0.0004, 0.0024), (x, MY1 + 0.0024, z), m_laser, 0))
    if k == 'receipt':  # 톱니 커터 날
        bm = bmesh.new()
        bm.loops.layers.uv.new("UVMap")
        n = 30
        pts = [(-0.045 + 0.09 * i / n, 0.0 if i % 2 == 0 else 0.0016) for i in range(n + 1)]
        top = [bm.verts.new((px, 0, -0.0034 + pz)) for px, pz in pts]
        bot = [bm.verts.new((px, 0, -0.0062)) for px, _ in pts]
        for i in range(n):
            bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        ext = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces), use_keep_orig=True)
        bmesh.ops.translate(bm, verts=[g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0.0012, 0))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        cadd(S.obj_from_bm("m_cutter", bm, (x, MY1 - 0.0004, z), None, m_chrome))
    if k in ('ic', 'member'):
        cadd(ycyl("m_led_" + k, 0.0024, MY1 - 0.0006, MY1 + 0.001, x + 0.05, z + 0.0135, m_led if k == 'ic' else m_lens, 12, 0.0003))
# NFC 패드
nx, nz, nw, nh = L['NFC']
o = prism("m_nfc", nw, nh, 0.008, PY - 0.004, PY + 0.0002, (nx, 0, nz), m_nfc, 0.0012)
uv_planar(o, -nw / 2, nw / 2, -nh / 2, nh / 2)
cadd(o)
# 직원 호출 버튼
cx, cz2 = L['CALL']
cadd(ycyl("m_call_ring", 0.021, PY - 0.003, PY + 0.0002, cx, cz2, m_chrome, 32, 0.0008))
o = ycyl("m_call_cap", 0.0165, PY - 0.0075, PY - 0.002, cx, cz2, m_red, 32, 0.0012)
uv_planar(o, -0.0165, 0.0165, -0.0165, 0.0165, vk=1)
cadd(o)
# 스피커 그릴 (타공판 + 구멍 26)
gx, gz = L['GRILLE']
cadd(prism("m_grille", 0.162, 0.034, 0.004, PY - 0.0015, PY + 0.0002, (gx, 0, gz), m_alu, 0.0006))
for i in range(26):
    cadd(ycyl("m_hole", 0.0022, PY - 0.0017, PY - 0.0013, -0.235 + (i % 13) * 0.0115, 0.405 + (i // 13) * 0.012, m_black, 10, 0))

# ---------------------------------------------------------------- 카드 단말기 (기울어진 가짜 투입구 포함)
tx, tz, tw, th, td, tilt = L['TERM']
TY = -0.112
term = [prism("t_body", tw, th, 0.012, -td / 2, td / 2, mat=m_term, bev=0.004)]
for i in range(12):
    kx, kz = (-28 + (i % 3) * 28) / 1000, (20 - (i // 3) * 18.5) / 1000
    term.append(prism("t_key", 0.022, 0.0135, 0.003, -td / 2 - 0.0026, -td / 2 + 0.0004, (kx, 0, kz), m_key, 0.0009))
for j, kx in enumerate((-0.028, 0.0, 0.028)):
    term.append(prism("t_fn", 0.022, 0.011, 0.003, -td / 2 - 0.0026, -td / 2 + 0.0004, (kx, 0, -0.056), m_fn[j], 0.0009))
term.append(prism("t_lcdwin", 0.076, 0.044, 0.002, -td / 2 - 0.001, -td / 2 + 0.0004, (0, 0, 0.055), m_bglass, 0.0005))
term.append(prism("t_slot", 0.1, 0.012, 0.004, -td / 2 - 0.006, -td / 2 + 0.0004, (0, 0, -0.088), m_term, 0.0015, hole=(0.088, 0.0026, 0.0008)))
term.append(prism("t_slotwell", 0.09, 0.0034, 0.0008, -td / 2 - 0.003, -td / 2 + 0.0002, (0, 0, -0.088), m_black, 0))
for o in term:
    for v in o.data.vertices:
        v.co += o.location
    o.location = (0, 0, 0)
    uv_planar(o, -tw / 2, tw / 2, -th / 2, th / 2)
TM = Matrix.Translation((tx, TY, tz)) @ Matrix.Rotation(tilt, 4, 'X')
for o in term:
    o.matrix_world = TM
    cadd(o)
# 단말기 받침 (패널까지 이어지는 쐐기형 브래킷)
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
fr = [TM @ Vector((sx * 0.05, td / 2 - 0.001, sz * 0.085)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
bk = [Vector((p.x, PY + 0.0002, p.z)) for p in fr]
v = [bm.verts.new(p) for p in fr + bk]
for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
    bm.faces.new([v[i] for i in f])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
o = S.obj_from_bm("t_bracket", bm, mat=m_powder)
S.bevel(o, 0.003, 2)
cadd(o)

# ---------------------------------------------------------------- 뒷면: 점검 도어, 나사, 잠금, 통풍구, 정격 라벨, 케이블
BY = D / 2
add(prism("r_door", 0.5, 1.12, 0.012, BY - 0.0004, BY + 0.0016, (0, 0, 0.96), m_powder, 0.0008))
for x in (-0.235, 0.235):
    for z in (0.43, 0.75, 1.17, 1.49):
        add(ycyl("r_screw", 0.0042, BY + 0.0024, BY + 0.0012, x, z, m_screw, 12, 0.0006))
add(ycyl("r_lock", 0.0095, BY + 0.0056, BY + 0.0012, 0.2, 1.3, m_chrome, 24, 0.001))
add(S.box("r_keyway", (0.0016, 0.001, 0.009), (0.2, BY + 0.0058, 1.3), m_black, 0))
for i in range(10):
    add(S.box("r_vent", (0.12, 0.0012, 0.005), (0.0, BY + 0.0018, 1.6 + i * 0.011), m_black, 0.0004, 1))
o = S.quad("r_label", 0.08, 0.046, (-0.15, BY + 0.0021, 0.6), m_rating, rot=(math.pi / 2, 0, math.pi))
add(o)
add(ycyl("r_grommet", 0.012, BY + 0.004, BY - 0.001, 0.12, 0.42, m_rubber, 24, 0.0012))


def tube(name, pts, r, mat):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = r, 3, 8
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    ob = S.link(bpy.data.objects.new(name, cu))
    cu.materials.append(mat)
    k3d.select([ob])
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    if not ob.data.uv_layers:
        ob.data.uv_layers.new(name="UVMap")
    return ob


add(tube("r_power", [(0.12, BY + 0.003, 0.42), (0.125, BY + 0.03, 0.39), (0.13, 0.12, 0.2), (0.135, 0.17, 0.045),
                     (0.15, 0.225, 0.037), (0.16, 0.26, 0.0045), (0.18, 0.37, 0.0045)], 0.0042, m_cable))
add(tube("r_lan", [(0.105, BY + 0.003, 0.415), (0.108, BY + 0.03, 0.385), (0.112, 0.115, 0.2), (0.118, 0.165, 0.042),
                   (0.13, 0.226, 0.0352), (0.14, 0.255, 0.003), (0.15, 0.37, 0.003)], 0.0028, m_lan))

# ---------------------------------------------------------------- 날개 포스터 받침판 + 클램프 (종이는 아래 Labels)
POPM = Matrix.Translation((-0.41, -0.111, 1.73)) @ Matrix.Rotation(0.35, 4, 'Z') @ Matrix.Rotation(0.12, 4, 'Y')  # NEW 흔들이 원판
POSTERS = {"A": [("festa", -1, 1.3, .25, .56, .42, .024), ("triple", 1, 1.54, .2, .3, .5, .02), ("refill", 1, 1.19, .17, .24, .3, .03)],
           "B": [("triple", -1, 1.48, .2, .3, .45, .02), ("refill", 1, 1.22, .17, .24, .35, .03)]}[VAR]
labels = []
m_paper = S.img_mat(f"M_{N}_Paper", os.path.join(TEXD, "T_Kiosk_Paper_BaseColor.jpg"), rough=0.55)
k3d.image_node(m_paper, k3d.load_image(os.path.join(TEXD, "T_Kiosk_Paper_Normal.jpg"), non_color=True), None)
nmap = m_paper.node_tree.nodes.new('ShaderNodeNormalMap')
nmap.inputs['Strength'].default_value = 0.6
m_paper.node_tree.links.new([n for n in m_paper.node_tree.nodes if n.type == 'TEX_IMAGE'][-1].outputs['Color'], nmap.inputs['Color'])
m_paper.node_tree.links.new(nmap.outputs['Normal'], k3d.principled(m_paper).inputs['Normal'])
m_tape = k3d.mat(f"M_Glass_{N}_Tape", (0.86, 0.84, 0.74), 0.3, alpha=0.42)
k3d.flag(m_tape, transparent=True, double_sided=True)
m_tape.surface_render_method = 'BLENDED'  # 미리보기용 (Unity 는 JSON transparent)


def pivot_mat(x, z, ang):
    return Matrix.Translation((x, -0.03, z)) @ Matrix.Rotation(ang, 4, 'Z')


for name, side, z, w, h, ang, curl in POSTERS:
    PM = pivot_mat(side * 0.312, z, ang if side < 0 else -ang)
    bd = prism("w_board", w + 0.006, h + 0.006, 0.004, 0.0, 0.004, (side * (w / 2 + 0.008), 0, 0), m_board, 0.0012)
    bd.matrix_world = PM @ bd.matrix_basis
    add(bd)
    for zz in (-0.32, 0.32):
        cl = S.box("w_clamp", (0.034, 0.016, 0.03), (side * 0.004, 0.006, zz * h), m_clip, 0.003, 2)
        cl.matrix_world = PM @ cl.matrix_basis
        add(cl)
        sc = ycyl("w_screw", 0.0026, -0.0024, -0.0008, side * 0.012, zz * h, m_screw, 10, 0.0003)
        sc.matrix_world = PM @ sc.matrix_basis
        add(sc)

    def fn(u, v, side=side, curl=curl):
        uo = 1 - u if side < 0 else u
        return uo ** 2 * (1 - v) ** 3 * curl * 2.2 + math.sin(v * 7 + u * 3) * 0.0012 + 0.0012
    pp = grid("l_poster", w, h, 10, 14, fn, ATL[name], m_paper)
    pp.matrix_world = PM @ Matrix.Translation((side * (w / 2 + 0.008), 0, 0))
    labels.append(pp)
    for k, lx in enumerate((side * 0.02, side * (w - 0.004))):  # 위쪽 두 귀퉁이 테이프 (아래 바깥 귀퉁이는 떨어져 말려 있음)
        tq = S.quad("l_tape", 0.045, 0.016, (0, 0, 0), m_tape, rot=(math.pi / 2, (0.7 if k else -0.7) * side, 0))
        tq.matrix_world = PM @ Matrix.Translation((lx, -0.0028, h / 2 - 0.006)) @ tq.matrix_basis
        labels.append(tq)

# 간판 면 (발광), 카드 전용 스티커 (유리 아래 테두리 위)
m_head = S.img_mat(f"M_{N}_Header", os.path.join(TEXD, "T_Kiosk_Header.png"), rough=0.35, emit=0.9)
labels.append(S.quad("l_header", 0.61, 0.086, (0, -0.0586, HZ), m_head))
u0, v0, u1, v1 = ATL["cardonly"]
labels.append(S.quad("l_cardonly", 0.2, 0.2 * 0.026 / 0.24, (0, -0.0659, SZ - SH / 2 - 0.0145), m_paper, uv=(u0, v0, u1, v1)))
if VAR == "B":  # '점검 중' A4 (3단 접힘 자국), 화면 위 테이프 2장
    def fold(u, v):
        t = (v * 3) % 1.0
        return 0.0003 + 0.0014 * (1 - abs(t - 0.5) * 2) + (1 - v) ** 2 * 0.004
    sg = grid("l_jumgum", 0.297, 0.21, 12, 18, fold, ATL["jumgum"], m_paper)
    sg.matrix_world = Matrix.Translation((0, -0.0662, 1.32)) @ Matrix.Rotation(-0.04, 4, 'Y')
    labels.append(sg)
    for px_, pz_, r_ in ((-0.16, 0.11, 0.6), (0.16, 0.11, -0.6)):
        tq = S.quad("l_tape", 0.09, 0.028, (0, 0, 0), m_tape)
        tq.matrix_world = Matrix.Translation((px_, -0.0668, 1.32 + pz_)) @ Matrix.Rotation(r_, 4, 'Y') @ tq.matrix_basis
        labels.append(tq)
else:  # 왕관페이 덮개 경첩 테이프 (덮개 종이 -> 옆 몰딩 앞면으로 꺾임)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    xs = [(0.284, -0.0691), (0.298, -0.0691), (0.303, -0.0634), (0.313, -0.0634)]
    vv = [[bm.verts.new((x, y, 0.838 + s * 0.075)) for x, y in xs] for s in (-1, 1)]
    for i in range(3):
        f = bm.faces.new((vv[0][i], vv[0][i + 1], vv[1][i + 1], vv[1][i]))
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 20, lp.vert.co.z * 20)
    labels.append(S.obj_from_bm("l_hingetape", bm, mat=m_tape))
    # 'NEW 행사 중' 흔들이 POP 받침 (투명 PET 띠 + 클립)
    add(S.box("w_popclip", (0.014, 0.012, 0.022), (-0.302, -0.067, 1.68), m_clip, 0.002, 2))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    path = [Vector((-0.302, -0.073, 1.68)).lerp(POPM @ Vector((0.03, 0.002, -0.012)), t) + Vector((0, -0.012 * math.sin(t * math.pi), 0.01 * math.sin(t * math.pi))) for t in [i / 8 for i in range(9)]]
    row = [[bm.verts.new(p + Vector((0, 0, s * 0.004))) for p in path] for s in (-1, 1)]
    for i in range(8):
        f = bm.faces.new((row[0][i], row[0][i + 1], row[1][i + 1], row[1][i]))
        for lp in f.loops:
            lp[uvl].uv = (i / 8, 0.0)
    labels.append(S.obj_from_bm("l_popstalk", bm, mat=m_tape))

# ---------------------------------------------------------------- 합치기 + 굽기
body = S.join(parts, f"{N}_Body")
ctrl = S.join(cparts, f"{N}_Controls")
lab = S.join(labels, f"{N}_Labels")
for o in (body, ctrl, lab):
    S.set_origin(o, (0, 0, 0))
for o in (body, ctrl):
    for sl in o.material_slots:  # k3d.bake 는 Emission Color 를 세기와 곱하지 않고 굽는다 -> 발광 안 하는 재질은 검정으로
        pr = k3d.principled(sl.material)
        if pr and pr.inputs['Emission Strength'].default_value <= 0 and not pr.inputs['Emission Color'].is_linked:
            pr.inputs['Emission Color'].default_value = (0, 0, 0, 1)
k3d.bake(body, 2048, samples=32, ao_distance=0.05)
k3d.bake(ctrl, 1024, samples=32, ao_distance=0.02)

# ---------------------------------------------------------------- 굽지 않는 면: 화면, 유리, 조작부 판, 단말기 LCD
m_scr = S.img_mat(f"M_Dyn_{N}_Screen", os.path.join(TEXD, "T_Kiosk_Screen_Attract.png" if VAR == "A" else "T_Kiosk_Screen_Off.png"),
                  rough=0.2, emit=1.0 if VAR == "A" else 0.7)
scr = S.quad(f"{N}_Screen", SW, SH, (SX, -0.0605, SZ), m_scr)
m_gl = S.img_mat(f"M_Glass_{N}_Cover", os.path.join(TEXD, "T_Kiosk_Glass.png"), rough=0.05)
gp = k3d.principled(m_gl)
gk = 0.8 if VAR == "A" else 0.45  # 지문 농도 (꺼진 화면 위에서는 더 옅게). JSON 은 baseColor 알파로 전달
m_gl.node_tree.links.new(S._math(m_gl.node_tree, 'MULTIPLY', [n for n in m_gl.node_tree.nodes if n.type == 'TEX_IMAGE'][0].outputs['Alpha'], gk), gp.inputs['Alpha'])
gp.inputs['Alpha'].default_value = gk
k3d.flag(m_gl, transparent=True)
m_gl.surface_render_method = 'BLENDED'
glass = S.quad(f"{N}_Glass", L['BEZ'][0] - 0.002, L['BEZ'][1] - 0.002, (SX, -0.0655, SZ), m_gl)
m_pan = S.img_mat(f"M_Dyn_{N}_Panel", os.path.join(TEXD, "T_Kiosk_Panel.png"), rough=0.55)
panel = S.quad(f"{N}_Panel", pw, ph, (pcx, PY - 0.0002, pcz), m_pan)
if VAR == "A":
    m_lcd = S.img_mat(f"M_Dyn_{N}_TerminalLcd", os.path.join(TEXD, "T_Kiosk_TerminalLcd.png"), rough=0.15, emit=0.8)
else:
    m_lcd = k3d.mat(f"M_{N}_LcdOff", (0.008, 0.01, 0.012), 0.08)
lcd = S.quad(f"{N}_TerminalLcd", 0.07, 0.04, (0, -td / 2 - 0.0013, 0.055), m_lcd)
lcd.matrix_world = TM @ lcd.matrix_basis
dyn = [scr, glass, panel, lcd]

# ---------------------------------------------------------------- 움직이는 부품 (A): 왕관페이 덮개 (경첩), NEW 흔들이
moving = []
if VAR == "A":
    def cfn(u, v):
        return (1 - u) ** 2 * (0.012 + (1 - v) ** 3 * 0.022) + (math.sin(u * 8 + v * 5) * 0.0009 + 0.001) * (1 - u)
    cv = grid(f"{N}_PayCover", 0.205, 0.17, 14, 12, cfn, ATL["cover_f"], m_paper, back_uv=ATL["cover_b"], mirror_back=False)
    cv.location = (0.30 - 0.205 / 2, -0.0688, 0.838)
    S.set_origin(cv, (0.30, -0.0688, 0.838))  # 경첩 = 오른쪽 세로 테이프 선
    moving.append(cv)
    # 별 모양 POP (앞 = NEW 행사 중, 뒤 = 흰 종이)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    R = 0.065
    for (u0, v0, u1, v1), off, flip in ((ATL["pop"], 0.0, False), (ATL["back"], 0.0004, True)):
        c = bm.verts.new((0, off, 0))
        ring = []
        for i in range(24):
            a = i / 24 * math.tau
            rr = R * (1.0 if i % 2 == 0 else 0.84)
            ring.append(bm.verts.new((math.cos(a) * rr, off, math.sin(a) * rr)))
        for i in range(24):
            q = (c, ring[(i + 1) % 24], ring[i])
            f = bm.faces.new(q[::-1] if flip else q)
            for lp in f.loops:
                uu, vv2 = lp.vert.co.x / (2 * R) + 0.5, lp.vert.co.z / (2 * R) + 0.5
                lp[uvl].uv = (u0 + (u1 - u0) * (1 - uu if flip else uu), v0 + (v1 - v0) * vv2)
    pop = S.obj_from_bm(f"{N}_PopWobbler", bm, mat=m_paper)
    pop.matrix_world = POPM
    moving.append(pop)

# ---------------------------------------------------------------- 계층 / 소켓
root = body
for o in [ctrl, lab] + dyn + moving:
    S.reparent(o, root)
MF = MY1 - 0.0005
socks = {"CardSlot": (*L['MODS']['ic'][:1], MF, L['MODS']['ic'][1]), "ReceiptOut": (L['MODS']['receipt'][0], MF, L['MODS']['receipt'][1]),
         "Barcode": (L['MODS']['barcode'][0], MF, L['MODS']['barcode'][1]), "Member": (L['MODS']['member'][0], MF, L['MODS']['member'][1]),
         "ScreenCenter": (SX, -0.0656, SZ), "UserStand": (0, -0.5, 0), "Nfc": (nx, PY - 0.0045, nz), "Call": (cx, PY - 0.008, cz2),
         "Speaker": (gx, PY - 0.002, gz), "Terminal": tuple(TM @ Vector((0, -td / 2 - 0.006, -0.088)))}
for k, p in socks.items():
    S.empty(f"{N}_Socket_{k}", p, root, 0.03)

notes = (f"{'매장 주문 키오스크 (프로토 pe.KX)' if VAR == 'A' else '점검 중 키오스크 (프로토 pe.K2X, 주문 불가: 화면 누르면 할아버지 대사)'}. "
         "높이 1.898m (간판 포함), 본체 0.60 x 0.11m, 받침판 0.66 x 0.46m. 정면 = Unity +Z. 원점 = 바닥 중앙. "
         "런타임 화면 교체 시 _BaseMap 과 _EmissionMap 을 둘 다 바꿀 것 (M_Dyn 화면은 같은 이미지로 발광). "
         f"{N}_Controls = 조작부 슬롯 모듈·단말기·NFC·호출 버튼·스피커 (따로 1024 굽기). "
         f"동적 면: {N}_Screen (M_Dyn_{N}_Screen, 0.42 x 0.7467m, 1080x1920px, UV 0-1 U=오른쪽 V=위, 유리보다 5mm 안쪽, 발광). "
         f"{N}_Panel (M_Dyn_{N}_Panel, 하단 조작부 0.54 x 0.585m, 1890x2048px, UV 0-1 정방향; 돋보기 상태는 T_Kiosk_Panel_Lens.png 로 교체). "
         + (f"{N}_TerminalLcd (M_Dyn_{N}_TerminalLcd, 단말기 LCD 0.07 x 0.04m, 512x292px, UV 0-1 정방향, 단말기와 같이 -0.24rad 기울어짐). " if VAR == "A" else f"{N}_TerminalLcd 는 꺼진 화면(단색). ")
         + f"{N}_Glass (M_Glass_{N}_Cover, 0.468 x 0.803m 투명 지문 유리, 화면 앞). {N}_Labels = 포스터·스티커·간판(M_{N}_Paper 아틀라스, M_{N}_Header 발광) + 테이프(M_Glass_{N}_Tape). "
         + ("움직이는 부품: Kiosk_PayCover = IC 카드 투입구를 가린 '왕관페이 30% 할인' 종이 덮개 (유리 M_Glass_Kiosk_Cover 와 다름), 원점 = 오른쪽 세로 경첩(테이프), "
            "Unity 로컬 Y 회전 0 -> -146도(-2.55rad) 로 열림 (자유단이 손님 기준 오른쪽 앞으로 펼쳐짐, 프로토 openCover). "
            "Kiosk_PopWobbler = 'NEW 행사 중' 흔들이 POP, 원점 = 원판 중심 (프로토 nudge: 로컬 X/Z 로 +-0.1~0.2rad 흔들기). "
            if VAR == "A" else "Kiosk_B 는 '점검 중' A4 종이가 화면 위에 테이프로 붙어 있고 덮개/흔들이는 없음. ")
         + f"소켓: CardSlot(진짜 IC 투입구, 덮개 뒤), ReceiptOut(영수증 출구, KioskReceipt 원점을 여기에), Barcode(쿠폰 스캐너 창), "
         "Member(가짜 멤버십 슬롯), Terminal(단말기 아래 가짜 투입구), Nfc(탭 패드), Call(직원 호출), Speaker(음성 안내 위치), "
         "ScreenCenter(화면 중심, 터치 판정), UserStand(손님이 서는 곳, 정면 0.5m). 슬롯 4개는 일부러 비슷하게 생김.")
k3d.export(N, "Kiosk", [root], notes=notes)
k3d.preview(N, [root], views=((28, 10), (205, 12)))
k3d.preview(N, [root], views=((0, 8),), lens=35, tag="fp")
S.shot(f"{N}_eye", (0.06, -0.62, 1.55), (0.0, 0.0, 1.02), lens=24, res=(1280, 900),
       lights=[((0.6, -1.6, 2.9), 260, 1.6, (1.0, 0.96, 0.9)), ((-1.4, -0.7, 2.6), 120, 2.0, (1, 1, 1))])
S.shot(f"{N}_detail", (0.1, -0.42, 1.12), (0.0, -0.06, 0.74), lens=35, res=(1280, 900),
       lights=[((0.6, -1.6, 2.9), 260, 1.6, (1.0, 0.96, 0.9)), ((-1.4, -0.7, 2.6), 120, 2.0, (1, 1, 1))])

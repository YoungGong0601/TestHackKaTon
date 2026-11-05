# 아파트 철제 현관문 (문짝). 원점 = 경첩 축(바깥면 모서리) 바닥, 문짝은 -X 방향으로 0.92m.
# -Y = 복도(바깥) 면: 도어락 키패드 / +Y = 집 안쪽 면: 레버, 도어락 실내기, 체인, 도어클로저, 전단지 자석.
# Z 축 + 회전 = 바깥(복도)으로 열림.
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "HomeDoor"
W, T, Z0, Z1 = 0.912, 0.05, 0.022, 2.035   # 문짝 폭/두께/아래/위
X0, X1 = -0.004 - W, -0.004                 # 문짝 x 범위
XC = (X0 + X1) / 2
YI = T                                      # 안쪽 면 y
HX = -0.83                                  # 손잡이/도어락 x
XP = -0.43                                  # 엠보 패널 중심 x
d2r = math.radians



def handwear(g, base, r, obj):
    # 손이 닿는 레버·도어락 주변: 손때로 어둡고 반들반들
    v = g.n('ShaderNodeVectorMath', operation='DISTANCE')
    g.link(obj, v.inputs[0])
    v.inputs[1].default_value = (HX + 0.04, YI, 1.17)
    m = g.math('SUBTRACT', 1.0, g.ramp(v.outputs['Value'], 0.04, 0.26))
    m = g.math('MULTIPLY', m, g.ramp(g.noise(28, 4, 0.6, obj), 0.3, 0.75))
    base = g.mix(g.math('MULTIPLY', m, 0.45), base, (0.075, 0.06, 0.05))
    r = g.lerp(g.math('MULTIPLY', m, 0.8), r, 0.22)
    return base, r


paint = hk.P("M_tmp_paint", "#6b5a4d", 0.42, var=0.06, vs=2.5, rv=0.06, grime=0.6, gd=0.025, gcol="#2a221c",
             edge=0.45, ed=0.002, ecol="#9c9284", erough=0.65, bump=0.05, bs=140, bd=0.0015, dust=0.6, dz=0.25,
             dcol="#3d342b", smudge=0.25, extra=handwear)
brass = hk.P("M_tmp_brass", "#a88a52", 0.28, 1.0, var=0.12, vs=20, rv=0.08, grime=0.8, gd=0.012, gcol="#3b2e1a",
             edge=0.6, ed=0.002, ecol="#e0c690", erough=0.15, smudge=0.25)
steel = hk.P("M_tmp_steel", "#b4b4b6", 0.3, 1.0, var=0.05, vs=30, grime=0.6, gd=0.01, gcol="#3a3a3a", smudge=0.2)
lockb = hk.P("M_tmp_lock", "#2d2d30", 0.35, 0.3, var=0.04, vs=10, grime=0.4, gd=0.008, edge=0.6, ed=0.0015,
             ecol="#6a6a70", smudge=0.4)
btn = hk.P("M_tmp_btn", "#8f9298", 0.35, 0.6, var=0.04, grime=0.5, gd=0.004, smudge=0.4)
rubber = hk.P("M_tmp_rubber", "#141414", 0.75, var=0.08, vs=20, dust=0.4, dz=0.05)
closer = hk.P("M_tmp_closer", "#9a9a98", 0.45, 0.5, var=0.05, vs=10, grime=0.6, gd=0.015, gcol="#2e2c28",
              edge=0.5, ed=0.002, ecol="#d0d0cc", dust=0.0)
flymat = hk.flat_img("M_HomeDoor_Flyers", hk.tex("door_flyers.png"), 0.45)

parts = []
# 문짝 본체 (접힌 철판 느낌: 큰 모서리 베벨)
parts.append(hk.box(A + "_Leaf", (W, T, Z1 - Z0), (XC, T / 2, (Z0 + Z1) / 2), mat=paint, bev=0.004, seg=3))


# 엠보 패널 (양면): 경사 테두리 + 평평한 윗면
def emboss(w, h, zc, face):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, 0.009, h), verts=bm.verts)
    top = [v for v in bm.verts if v.co.y * face > 0]
    for v in top:  # 경사(챔퍼)
        v.co.x *= (w - 0.05) / w
        v.co.z *= (h - 0.05) / h
    o = hk.mesh_obj(A + "_Panel", bm, paint)
    o.location = (XP, (YI + 0.0015) if face > 0 else -0.0015, zc)
    return hk.finish(o, 0.004, 3, angle=10)


for f in (1, -1):
    parts += [emboss(0.62, 0.82, 1.42, f), emboss(0.62, 0.72, 0.52, f)]

# 경첩 (문짝 쪽 너클)
for z in (0.25, 1.0, 1.75):
    parts.append(hk.cyl(A + "_Hinge", 0.0095, 0.09, (0, 0, z), mat=steel, n=20, bev=0.0015))
    parts.append(hk.box(A + "_HingeLeaf", (0.03, 0.003, 0.09), (-0.017, -0.0015, z + 0.045), mat=steel, bev=0.001))
# 래치면 (자물쇠 면판 + 데드볼트)
parts.append(hk.box(A + "_Face", (0.003, 0.024, 0.32), (X0 - 0.0005, T / 2, 1.16), mat=steel, bev=0.0008))
parts.append(hk.box(A + "_Latch", (0.012, 0.012, 0.02), (X0 - 0.005, T / 2, 1.03), mat=steel, bev=0.002))
# 하단 고무 실링
parts.append(hk.box(A + "_Sweep", (W - 0.04, 0.008, 0.014), (XC, YI + 0.004, Z0 + 0.012), mat=rubber, bev=0.002))


# --- 안쪽 레버 손잡이 (자식: 스핀들 축 회전)
def lever(name, y, face):
    r = hk.cyl(name + "_Rose", 0.03, 0.009, (HX, y, 1.03), rot=(d2r(-90 * face), 0, 0), mat=brass, n=32, bev=0.002, seg=3)
    neck = hk.cyl(name + "_Neck", 0.011, 0.03, (HX, y + face * 0.008, 1.03), rot=(d2r(-90 * face), 0, 0), mat=brass,
                  n=20, bev=0.002)
    pts = [(HX, y + face * 0.035, 1.03), (HX + 0.06, y + face * 0.037, 1.03), (HX + 0.11, y + face * 0.036, 1.026),
           (HX + 0.128, y + face * 0.03, 1.016)]
    bar = hk.tube(name + "_Bar", pts, 0.0095, 12, brass, rfun=lambda t: 1.0 - 0.15 * t)
    bar.scale = (1, 1, 1)
    o = hk.join([r, neck, bar], name)
    hk.vgroup(o, name)
    return o


parts.append(lever(A + "_LeverIn", YI, 1))
parts.append(lever(A + "_LeverOut", 0.0, -1))

# --- 디지털 도어락 실내기 (+Y) / 키패드 실외기 (-Y)
LZ = 1.33
parts.append(hk.box(A + "_LockIn", (0.072, 0.034, 0.19), (HX, YI + 0.017, LZ), mat=lockb, bev=0.006, seg=3))
parts.append(hk.box(A + "_LockSeam", (0.064, 0.002, 0.004), (HX, YI + 0.0345, LZ - 0.02), mat=rubber, bev=0.0005))
parts.append(hk.box(A + "_OpenBtn", (0.044, 0.006, 0.05), (HX, YI + 0.035, LZ - 0.055), mat=btn, bev=0.004, seg=3))
parts.append(hk.cyl(A + "_Turn", 0.014, 0.008, (HX, YI + 0.034, LZ + 0.05), rot=(d2r(-90), 0, 0), mat=btn, n=24, bev=0.002))
parts.append(hk.box(A + "_TurnBar", (0.007, 0.012, 0.03), (HX, YI + 0.046, LZ + 0.05), mat=btn, bev=0.003))
parts.append(hk.cyl(A + "_Led", 0.002, 0.002, (HX + 0.024, YI + 0.034, LZ + 0.082), rot=(d2r(-90), 0, 0), mat=btn, n=8, bev=0))
parts.append(hk.box(A + "_LockOut", (0.07, 0.026, 0.2), (HX, -0.013, LZ), mat=lockb, bev=0.006, seg=3))
parts.append(hk.box(A + "_KeyGlass", (0.05, 0.003, 0.11), (HX, -0.0262, LZ + 0.02), mat=lockb, bev=0.002))
for i in range(12):
    cx, cz = HX + (i % 3 - 1) * 0.014, LZ + 0.06 - (i // 3) * 0.022
    parts.append(hk.cyl(A + "_Key", 0.0045, 0.0015, (cx, -0.0275, cz), rot=(d2r(90), 0, 0), mat=btn, n=12, bev=0.0004, seg=1))
parts.append(hk.box(A + "_KeyCover", (0.058, 0.004, 0.05), (HX, -0.027, LZ - 0.07), mat=btn, bev=0.003))

# --- 도어뷰 (외시경): 실내 = 크롬 원형 접안부(Ø28, 돌출 8mm) + 렌즈 + 위쪽 핀에 매달린 회전 덮개(살짝 열림)
lensm = hk.P("M_tmp_peeplens", "#0b0e12", 0.05, var=0.02, smudge=0.8)
parts.append(hk.cyl(A + "_PeepIn", 0.014, 0.008, (XP, YI + 0.004, 1.5), rot=(d2r(-90), 0, 0), mat=steel, n=32, bev=0.002, seg=3))
parts.append(hk.cyl(A + "_PeepLens", 0.0075, 0.0015, (XP, YI + 0.0085, 1.5), rot=(d2r(-90), 0, 0), mat=lensm, n=24, bev=0.0005))
parts.append(hk.cyl(A + "_PeepOut", 0.012, 0.004, (XP, -0.0055, 1.5), rot=(d2r(90), 0, 0), mat=steel, n=24, bev=0.0015))
th = d2r(35)
parts.append(hk.cyl(A + "_PeepCover", 0.012, 0.002, (XP - 0.02 * math.sin(th), YI + 0.0105, 1.52 - 0.02 * math.cos(th)),
                    rot=(d2r(-90), 0, 0), mat=steel, n=28, bev=0.0008))
parts.append(hk.box(A + "_PeepArm", (0.004, 0.002, 0.02), (XP - 0.01 * math.sin(th), YI + 0.0105, 1.52 - 0.01 * math.cos(th)),
                    rot=(0, th, 0), mat=steel, bev=0.0006))
parts.append(hk.cyl(A + "_PeepPin", 0.0025, 0.004, (XP, YI + 0.009, 1.52), rot=(d2r(-90), 0, 0), mat=steel, n=12, bev=0.0006))

# --- 도어 가드(체인): 홈레일 + 고정판 + 늘어진 체인 (도어락 위)
CZ = 1.575
parts.append(hk.box(A + "_ChainTrack", (0.085, 0.008, 0.018), (-0.785, YI + 0.004, CZ), mat=steel, bev=0.002))
parts.append(hk.box(A + "_ChainSlot", (0.07, 0.002, 0.004), (-0.785, YI + 0.0085, CZ), mat=rubber, bev=0.0005))
parts.append(hk.box(A + "_ChainBase", (0.024, 0.008, 0.05), (-0.885, YI + 0.004, CZ), mat=steel, bev=0.002))
N = 13
for i in range(N):
    t = i / (N - 1)
    x = -0.88 + t * 0.15
    z = CZ - 0.005 - math.sin(t * math.pi) * 0.05
    dzdx = -0.05 * math.pi * math.cos(t * math.pi) / 0.15
    ry = -math.atan(dzdx)
    rot = (d2r(90), ry, 0) if i % 2 else (0, ry, 0)
    parts.append(hk.torus(A + "_Link", 0.0052, 0.0015, (x, YI + 0.012, z), rot, steel, nu=12, nv=6, sx=1.5))
parts.append(hk.cyl(A + "_ChainKnob", 0.007, 0.012, (-0.735, YI + 0.012, CZ - 0.005), rot=(0, d2r(90), 0), mat=steel, n=16, bev=0.002))

# --- 도어클로저 (본체 고정, 암/전완 = 자식)
parts.append(hk.box(A + "_Closer", (0.27, 0.045, 0.055), (-0.225, YI + 0.0225, 1.962), mat=closer, bev=0.008, seg=3))
for sx in (-0.355, -0.095):
    parts.append(hk.box(A + "_CloserCap", (0.012, 0.04, 0.05), (sx, YI + 0.0225, 1.962), mat=lockb, bev=0.004))
parts.append(hk.box(A + "_CloserPlate", (0.3, 0.004, 0.06), (-0.225, YI + 0.002, 1.962), mat=closer, bev=0.001))
for sx in (-0.368, -0.082):
    for sz in (1.942, 1.982):
        parts.append(hk.cyl(A + "_Screw", 0.003, 0.002, (sx, YI + 0.004, sz), rot=(d2r(-90), 0, 0), mat=steel, n=10, bev=0.0005))
sp = hk.cyl(A + "_Spindle", 0.007, 0.012, (-0.32, YI + 0.026, 1.99), mat=steel, n=16, bev=0.001)
parts.append(sp)
arm = hk.join([hk.box(A + "_ArmBar", (0.2, 0.016, 0.007), (-0.22, YI + 0.026, 2.005), mat=lockb, bev=0.003),
               hk.cyl(A + "_ArmHub", 0.011, 0.01, (-0.32, YI + 0.026, 2.0), mat=lockb, n=20, bev=0.002)], A + "_CloserArm")
hk.vgroup(arm, A + "_CloserArm")
fore = hk.join([hk.tube(A + "_ForeRod", [(-0.12, YI + 0.026, 2.012), (-0.2, YI + 0.04, 2.012)], 0.0045, 10, steel),
                hk.cyl(A + "_Elbow", 0.008, 0.012, (-0.12, YI + 0.026, 2.006), mat=steel, n=16, bev=0.0015)],
               A + "_CloserForearm")
hk.vgroup(fore, A + "_CloserForearm")
parts += [arm, fore]

# --- 전단지 자석 4장 + 손글씨 메모 + 테이프 (굽지 않는 인쇄 머티리얼)
V0 = 1 - 630 / 2048
regions = [(0, V0, 0.5, 1), (0.5, V0, 1, 1), (0, V0 - 630 / 2048, 0.5, V0), (0.5, V0 - 630 / 2048, 1, V0)]


def magnet(i, w, h, x, z, rot, th=0.0012, torn=False):
    u0, v0, u1, v1 = regions[i]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    r = 0.006 if not torn else 0.0008
    pts = []
    for (cx, cz, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                         (w / 2 - r, -h / 2 + r, 270)):
        for k in range(5):
            a = d2r(a0 + k * 22.5)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    if torn:  # 오른쪽 아래 모서리가 찢겨 나간 종이 스티커
        import random
        rnd = random.Random(7)
        pts = [p for p in pts if not (p[0] > -w * 0.05 and p[1] < h * 0.05)]
        top_right = [p for p in pts if p[0] > 0]
        rest = [p for p in pts if p[0] <= 0]
        cut = []
        for k in range(1, 12):
            t = k / 12
            cut.append((-w * 0.05 + t * (w / 2 + w * 0.05) + rnd.uniform(-0.0015, 0.0015),
                        -h / 2 + t ** 1.4 * (h / 2 + h * 0.05) + rnd.uniform(-0.002, 0.002)))
        pts = top_right + rest + [(-w * 0.05, -h / 2)] + cut
    vs = [bm.verts.new((px, 0.0, pz)) for px, pz in pts]
    f = bm.faces.new(vs)
    for l in f.loops:  # +Y 쪽에서 볼 때 U 가 오른쪽(-X)
        l[uvl].uv = (u0 + (0.5 - l.vert.co.x / w) * (u1 - u0), v0 + (l.vert.co.z / h + 0.5) * (v1 - v0))
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, th, 0), verts=[e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    o = hk.mesh_obj(A + "_Flyer", bm, flymat)
    o.location = (x, YI + 0.0062, z)
    o.rotation_euler = (0, rot, 0)
    return o


fly = []
for i in range(4):
    x = -(0.22 + (i % 2) * 0.17)
    z = 1.15 + (i // 2) * 0.11
    fly.append(magnet(i, 0.13, 0.08, x, z, (i - 1.5) * 0.05, th=0.0012 if i < 3 else 0.0003, torn=(i == 3)))
# 손글씨 메모 (아래가 살짝 들뜸) + 테이프
# (Z 180도 회전 = 앞면이 +Y, 글자가 바로 읽힘)
memo = hk.quad(A + "_Memo", 0.09, 0.108, flymat, loc=(-0.6, YI + 0.0068, 1.62), rot=(0, d2r(3), math.pi),
               uv=(0, 0, 640 / 2048, 768 / 2048), nx=4, ny=6, bend=lambda u, v: -0.004 * (1 - v) ** 2)
tape = hk.quad(A + "_Tape", 0.042, 0.013, flymat, loc=(-0.6, YI + 0.0074, 1.672), rot=(0, d2r(6), math.pi),
               uv=(700 / 2048, 1 - 1420 / 2048, 1100 / 2048, 1 - 1300 / 2048))
fly += [memo, tape]

# --- 합치기 / 굽기
leaf = hk.join(parts + fly, A)
k3d.set_origin(leaf, (0, 0, 0))
for p in leaf.data.polygons:  # 인쇄물은 평면 셰이딩
    if leaf.material_slots[p.material_index].material == flymat:
        p.use_smooth = False
k3d.bake(leaf, 2048, keep=("M_HomeDoor_Flyers",), ao_distance=0.06)
# 움직이는 부품 분리 (같은 텍스처 세트)
lv_in = hk.split_vgroup(leaf, A + "_LeverIn", A + "_LeverIn", (HX, YI, 1.03), leaf)
lv_out = hk.split_vgroup(leaf, A + "_LeverOut", A + "_LeverOut", (HX, 0, 1.03), leaf)
armo = hk.split_vgroup(leaf, A + "_CloserArm", A + "_CloserArm", (-0.32, YI + 0.026, 2.0), leaf)
# FBX(bake_space_transform) 가 손자 계층 변환을 깨뜨려서 전완도 문짝의 직접 자식으로 둔다
foreo = hk.split_vgroup(leaf, A + "_CloserForearm", A + "_CloserForearm", (-0.12, YI + 0.026, 2.006), leaf)
for o in (leaf, lv_in, lv_out, armo, foreo):
    o.vertex_groups.clear()

S = lambda n, p: hk.socket(A + "_Socket_" + n, p, leaf)
S("Handle", (HX + 0.07, YI + 0.04, 1.03))
S("HandleOut", (HX + 0.07, -0.04, 1.03))
S("LockButton", (HX, YI + 0.04, LZ - 0.055))
S("Keypad", (HX, -0.03, LZ + 0.02))
S("Peephole", (XP, YI + 0.015, 1.5))
S("Memo", (-0.6, YI + 0.01, 1.62))
S("LookTarget", (XC + 0.1, YI, 1.1))

notes = (
    "현관 철제문 문짝 0.912x2.013x0.05m. 원점 = 경첩 축(바깥면 모서리) 바닥 높이, 문짝은 원점에서 -X 쪽으로 뻗음. "
    "-Y = 복도(바깥) 면(키패드), +Y = 집 안쪽 면(레버, 도어락, 체인, 도어클로저, 전단지). "
    "HomeEntry/HomeDoorFrame 좌표계 그대로 쓰면 회전 없이 맞음: HomeDoorFrame_Socket_DoorHinge 위치에 원점을 둔다. "
    "로컬 Z(Blender)=Unity 로컬 Y 축 + 회전으로 복도 쪽(바깥)으로 열림 (프로토타입 K.rotation.y = doorT*1.5 에 해당, 부호는 Unity 축 변환 후 확인). "
    "자식: HomeDoor_LeverIn / HomeDoor_LeverOut (원점=스핀들, 문 면 법선(Y) 축으로 눌림), "
    "HomeDoor_CloserArm (원점=클로저 스핀들, Z 축 회전), HomeDoor_CloserForearm (원점=팔꿈치, FBX 손자 계층 문제로 문짝 직속 자식). "
    "문짝 아래는 문턱 위 0.022m 띄움(min_z=0.022 정상, 원점은 경첩 축 바닥). "
    "전단지 자석 4장(24시 열쇠/중화 반점/치킨 배달/가스 점검-찢김) + 손글씨 메모는 M_HomeDoor_Flyers(2048 인쇄 텍스처, 굽지 않음). "
    "소켓: Handle(안쪽 레버 잡는 점), HandleOut, LockButton(실내기 열림 버튼), Keypad, Peephole, Memo, LookTarget.")
k3d.export(A, hk.CAT, [leaf], notes=notes)
k3d.preview(A, [leaf], views=((180, 10), (150, 25), (20, 12)))
k3d.preview(A, [leaf], views=((180, 4),), lens=35, tag='fp')
# 손잡이/전단지 근접
hk.shot(hk.PREV + "/HomeDoor_detail.png", (-0.55, 0.75, 1.3), (-0.55, 0.0, 1.28), lens=40, res=(1200, 900),
        lights=[('AREA', (-0.4, 1.2, 2.0), 60, (1, 0.92, 0.8), 1.0), ('POINT', (0.3, 0.8, 1.0), 15, (1, 1, 1), 0.3)],
        world=0.35)

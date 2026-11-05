"""NpcSuitMan — 양복 입은 직장인 30대 남 (점심시간 손님/행인). 원본 npc_man3 리그·웨이트·애니 유지.
감청 울 수트(능직), 하늘빛 흰 셔츠, 버건디 레지멘탈 넥타이, 목줄+사원증(대한물산), 재킷 단추 2개, 검정 구두(가죽 밑창), 스마트폰.
실행: K3D_ROOT=... blender -b --factory-startup --python NpcSuitMan.py
"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npcb_common as C
from npcb_common import k3d

A, H = "NpcSuitMan", 1.76
C.decals()
arm, ms = C.load("npc_man3", A, H)
mouth = C.face(ms["Head"])
C.author_clips(arm)
for m in ms.values():
    C.upgrade(m)
body, legs, feet, head = ms["Body"], ms["Legs"], ms["Feet"], ms["Head"]
bones = arm.data.bones


def tie(name):
    """버건디 실크 넥타이 + 사선 감청 줄(양옆 가는 금색 줄)."""
    col = (0.17, 0.020, 0.028)
    b = C.NB(name, col, 0.36)
    w = b.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL')
    w.inputs['Scale'].default_value = 8.0      # 굵은 줄: 2048 아틀라스에서 계단 현상 줄임
    w.inputs['Distortion'].default_value = 0.0
    b.L(b.obj, w.inputs['Vector'])
    f = w.outputs['Fac']
    gold = b.math('SUBTRACT', b.ramp(f, 0.66, 0.69), b.ramp(f, 0.74, 0.77), clamp=True)
    navy = b.ramp(f, 0.78, 0.81)
    c = b.mixc(b.noise(30.0, 2), C.sc(col, 0.9), C.sc(col, 1.1))
    c = b.mixc(gold, c, (0.30, 0.22, 0.09))
    c = b.mixc(navy, c, (0.018, 0.026, 0.075))
    c = b.mixc(b.ao(0.02), C.sc(col, 0.45), c)
    b.bump(b.noise(1800.0, 2, 0.6), 0.10, 0.0003)
    b.bump(navy, 0.08, 0.0004)
    return b.done(c, b.math('MULTIPLY_ADD', b.noise(20.0, 2), 0.08, 0.32))


# ---------------------------------------------------------------- 재질
NAVY = (0.017, 0.021, 0.034)
skin = C.skin(A + "_skin", (0.58, 0.39, 0.28), mouth=mouth)
hair = C.hair(A + "_hair", (0.012, 0.010, 0.009))
eye = C.flat(A + "_eye", (0.010, 0.008, 0.007), 0.12)
wool = C.fabric(A + "_wool", NAVY, rough=0.8, grain=0.2, grain_scale=1500, folds=0.06, twill=0.12, wear=0.18, cavity=0.5)
shirt = C.fabric(A + "_shirt", (0.66, 0.70, 0.76), rough=0.75, grain=0.15, grain_scale=1800, folds=0.12, cavity=0.35)
tiem = tie(A + "_tie")
shoe = C.leather(A + "_shoe", (0.010, 0.009, 0.009), 0.2, sole=(0.035, 0.022, 0.014), sole_h=0.016, sole_rough=0.7, scuff=0.12)
C.set_mats(head, {"Skin": skin, "Eye": eye, "*": hair})
C.hair_flow(head, [hair])
C.set_mats(body, {"Skin": skin, "White": shirt, "Tie": tiem, "*": wool})
C.set_mats(legs, {"*": wool})
C.set_mats(feet, {"*": shoe})
eye_lo, eye_hi = C.mat_bounds(head, [eye.name])


def front(x, z):
    """정면(-Y)에서 몸에 쏜 레이 -> (위치, 노멀, 재질)."""
    ok, loc, nor, idx = body.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)))
    return (loc, nor, body.material_slots[body.data.polygons[idx].material_index].material) if ok else None


# ---------------------------------------------------------------- 재킷 단추 2개 (V 깃이 닫히는 곳 아래)
zs = [bones["Chest"].head_local.z - 0.01 * i for i in range(40)]
zv = next((z for z in zs if (h := front(0.0, z)) and h[2] == wool), None)
bm = bmesh.new()
nb = 0
if zv:
    for z in (zv - 0.025, zv - 0.125):
        h = front(0.0, z)
        if h and h[2] == wool:
            rot = Vector((0, 0, 1)).rotation_difference(h[1]).to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.0095, radius2=0.0085, depth=0.004,
                                  matrix=Matrix.Translation(h[0] + h[1] * 0.0015) @ rot)
            nb += 1
print("npcb: buttons", nb, "zv", zv)
buttons = C.new_obj(A + "_Buttons", bm, [C.flat(A + "_button", (0.018, 0.014, 0.012), 0.3, 0.0, var=0.15)]) if nb else None
if buttons:
    C.bevel_obj(buttons, 0.0008, 2)
    C.copy_weights(body, [buttons])

# ---------------------------------------------------------------- 노치드 라펠 · 셔츠 깃끝 · 넥타이 매듭 · 포켓


def sheet(name, rows, mat, thick):
    """점 행렬(행 x 열) -> 면 -> 바깥(-Y)을 보게 -> 두께(몸 쪽) + 모서리 베벨."""
    bm = bmesh.new()
    vv = [[bm.verts.new(p) for p in r] for r in rows]
    for i in range(len(vv) - 1):
        for j in range(len(vv[i]) - 1):
            bm.faces.new((vv[i][j], vv[i + 1][j], vv[i + 1][j + 1], vv[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    o = C.new_obj(name, bm, [mat])
    sol = o.modifiers.new("Sol", 'SOLIDIFY')
    sol.thickness, sol.offset = thick, -1.0
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier="Sol")
    C.bevel_obj(o, 0.0008, 1)
    k3d.smooth(o, 180)
    return o


def on(x, z, off, objs=None):
    """정면 레이 -> 표면 + 노멀*off."""
    h = front(x, z) if objs is None else front2(x, z, objs)
    return (h[0] + h[1] * off) if h else Vector((x, -0.17, z))


def front2(x, z, objs):
    best = None
    for o in objs:
        ok, loc, nor, _ = o.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)))
        if ok and (best is None or loc.y < best[0].y):
            best = (loc, nor)
    return best


nk = bones["Neck"].head_local
parts_extra = []
if zv:
    for sd in (1, -1):
        edge = []
        z = zv + 0.004
        while z < nk.z:
            xe = next((sd * 0.0015 * i for i in range(80) if (h := front(sd * 0.0015 * i, z)) and h[2] == wool), None)
            if xe is None or (edge and abs(xe) - abs(edge[-1][0]) > 0.025):
                break
            edge.append((xe, z))
            z += 0.008
        if len(edge) < 6:
            continue
        K = len(edge)
        rows = []
        for k, (xe, z) in enumerate(edge):
            t = k / (K - 1)
            a, b_ = edge[max(k - 1, 0)], edge[min(k + 1, K - 1)]
            tx, tz = b_[0] - a[0], b_[1] - a[1]
            ln = math.hypot(tx, tz) or 1.0
            ox, oz = sd * abs(tz) / ln, -abs(tx) / ln                       # V 가장자리에 수직, 바깥 아래
            w = 0.010 + 0.060 * C.ease(t / 0.70) if t <= 0.70 else (0.030 if t <= 0.80 else 0.034)   # 노치
            rows.append([on(xe, z, 0.0042), on(xe + ox * w * 0.5, z + oz * w * 0.5, 0.0035),
                         on(xe + ox * w, z + oz * w, 0.0026)])
        parts_extra.append(sheet(A + "_Lapel" + ("L" if sd > 0 else "R"), rows, wool, 0.0025))
lapels = list(parts_extra)
# 셔츠 깃끝: 넥타이 매듭 양옆으로 내려오는 삼각 깃
tlo, thi = C.mat_bounds(body, [tiem.name])
zt = thi[2]
for sd in (1, -1):
    A_, B_, C_ = (sd * 0.009, zt + 0.003), (sd * 0.040, zt - 0.002), (sd * 0.024, zt - 0.046)
    rows = [[on(*A_, 0.0022), on(*B_, 0.0022)],
            [on((A_[0] + C_[0]) / 2, (A_[1] + C_[1]) / 2, 0.0022), on((B_[0] + C_[0]) / 2, (B_[1] + C_[1]) / 2, 0.0022)],
            [on(*C_, 0.0022), on(C_[0] + sd * 0.0005, C_[1], 0.0022)]]
    parts_extra.append(sheet(A + "_CollarPt" + ("L" if sd > 0 else "R"), rows, shirt, 0.0015))
# 넥타이 매듭 (사다리꼴)
kp = on(0.0, zt - 0.014, 0.004)
bm = bmesh.new()
for v in C.bm_box(bm, (0.034, 0.012, 0.026)):
    if v.co.z < 0:
        v.co.x *= 0.62
bm.transform(Matrix.Translation(kp))
knot = C.new_obj(A + "_TieKnot", bm, [tiem])
C.bevel_obj(knot, 0.003, 2)
parts_extra.append(knot)
# 포켓: 왼쪽 가슴 웰트 + 허리 플랩 2개
zc = bones["Chest"].head_local.z - 0.015
rows = [[on(0.078 + 0.055 * i / 4, zc + 0.0065 + 0.004 * i / 4, 0.0022) for i in range(5)],   # 겨드랑이 전에서 끝
        [on(0.078 + 0.055 * i / 4, zc - 0.0065 + 0.004 * i / 4, 0.0022) for i in range(5)]]
parts_extra.append(sheet(A + "_Welt", rows, wool, 0.002))
zh = min(v.co.z for v in body.data.vertices)
for sd in (1, -1):
    rows = [[on(sd * (0.03 + 0.085 * i / 5), zh + 0.115 - 0.045 * j / 2, 0.0028) for i in range(6)] for j in range(3)]   # 옆구리 밖으로 나가지 않게
    parts_extra.append(sheet(A + "_Flap" + ("L" if sd > 0 else "R"), rows, wool, 0.0025))
C.copy_weights(body, parts_extra)
print("npcb: lapels", len(lapels), "extra", len(parts_extra))

# ---------------------------------------------------------------- 사원증 + 목줄
zcard = bones["Chest"].head_local.z - 0.045
CW, CH, CT = 0.056, 0.088, 0.003
yf = min(h[0].y for h in (front(x, z) for x in (-0.028, -0.014, 0, 0.014, 0.028)
                            for z in (zcard - 0.044, zcard - 0.02, zcard, zcard + 0.02, zcard + 0.044)) if h)
cy = yf - CT / 2 - 0.002
bm = bmesh.new()
C.bm_box(bm, (CW, CT, CH), (0, cy, zcard))
uvl = bm.loops.layers.uv.verify()
for f_ in bm.faces:
    for l in f_.loops:
        l[uvl].uv = ((l.vert.co.x / CW + 0.5), (l.vert.co.z - zcard) / CH + 0.5) if f_.normal.y < -0.9 else (0.02, 0.02)
card = C.new_obj(A + "_IdCard", bm)
C.bevel_obj(card, 0.0009, 2)
cb = C.NB(A + "_idcard", (0.9, 0.9, 0.9), 0.22)
ti = cb.node('ShaderNodeTexImage')
ti.image = k3d.load_image(os.path.join(C.DEC, "idcard.png"))
cb.L(cb.node('ShaderNodeUVMap', uv_map="UVMap").outputs[0], ti.inputs['Vector'])
edge = cb.math('LESS_THAN', cb.math('ABSOLUTE', cb.NY), 0.5)
cb.done(cb.mixc(edge, ti.outputs['Color'], (0.80, 0.81, 0.82)), 0.2)
card.data.materials.append(cb.m)
# 클립 (금속)
bm = bmesh.new()
C.bm_box(bm, (0.012, 0.004, 0.016), (0, cy - 0.0005, zcard + CH / 2 + 0.004))
clip = C.new_obj(A + "_Clip", bm, [C.flat(A + "_clip", (0.62, 0.62, 0.64), 0.28, 1.0)])
C.bevel_obj(clip, 0.0008, 2)
# 목줄: 카드 위 -> 앞가슴을 따라 목 옆 -> 목 뒤를 돌아 반대쪽 (표면에 3mm 띄워 리본)
nk = bones["Neck"].head_local
zn = nk.z + 0.012
pl = []
for i in range(13):                       # 왼쪽 앞: 카드 위 -> 목 옆
    t = i / 12
    x, z = 0.005 + (0.036 - 0.005) * t, zcard + CH / 2 + 0.01 + (zn - (zcard + CH / 2 + 0.01)) * t ** 0.8   # 셔츠 위 (V 가장자리를 따라가지 않게)
    h = front2(x, z, [body] + lapels)
    pl.append((h[0] + h[1] * 0.0025, h[1]) if h else None)
ring = []
for i in range(1, 16):                    # 목 뒤 (왼쪽 -> 뒤 -> 오른쪽)
    a = math.pi * i / 16
    d = Vector((math.cos(a), math.sin(a), 0))
    ok, loc, nor, _ = body.ray_cast(Vector((nk.x, nk.y, zn)) + d * 0.3, -d)
    if ok:
        ring.append((loc + nor * 0.003, nor))
pr = []
for i in range(13):                       # 오른쪽 앞: 목 옆 -> 카드 위
    t = 1 - i / 12
    x, z = -(0.005 + (0.036 - 0.005) * t), zcard + CH / 2 + 0.01 + (zn - (zcard + CH / 2 + 0.01)) * t ** 0.8
    h = front2(x, z, [body] + lapels)
    pr.append((h[0] + h[1] * 0.0025, h[1]) if h else None)
pts = [p for p in pl if p] + ring + [p for p in pr if p]
bm = bmesh.new()
prev = None
W = 0.0075
for i, (p, n) in enumerate(pts):
    t = (pts[min(i + 1, len(pts) - 1)][0] - pts[max(i - 1, 0)][0]).normalized()
    side = t.cross(n).normalized() * W
    cur = (bm.verts.new(p - side), bm.verts.new(p + side))
    if prev:
        bm.faces.new((prev[0], prev[1], cur[1], cur[0]))
    prev = cur
lan = C.new_obj(A + "_Lanyard", bm)
sol = lan.modifiers.new("Sol", 'SOLIDIFY')
sol.thickness, sol.offset = 0.0012, 0.0
k3d.select([lan])
bpy.ops.object.modifier_apply(modifier="Sol")
k3d.smooth(lan, 60)
lb = C.NB(A + "_lanyard", (0.02, 0.045, 0.12), 0.7)
lw = lb.wave(260.0, 'Z', 0.0, 0.0)
lb.bump(lw, 0.25, 0.0004)
lan.data.materials.append(lb.done(lb.mixc(lb.math('MULTIPLY', lw, 0.3), (0.02, 0.045, 0.12), (0.035, 0.07, 0.17)), 0.7))
C.copy_weights(body, [lan])
C.rigid(card, "Chest", arm)
C.rigid(clip, "Chest", arm)

# ---------------------------------------------------------------- 합치기 · 폰 · 베이크
phone = C.phone(A, arm)
parts = [body, legs, feet, card, clip, lan] + ([buttons] if buttons else []) + parts_extra
body_o = C.join(parts, A + "_Body")
head_o = C.join([head], A + "_Head")
assert "HairUV" in head_o.data.uv_layers, "HairUV 없음 -> 머리카락 결이 단색으로 구워짐"
C.bake_all(arm, [(body_o, 2048, 0.05), (head_o, 1024, 0.03), (phone, 512, 0.01)])

# ---------------------------------------------------------------- 소켓
eye_c = (Vector(eye_lo) + Vector(eye_hi)) / 2
palm_r = (bones["Wrist.R"].head_local + bones["Middle2.R"].head_local) / 2
palm_l = (bones["Wrist.L"].head_local + bones["Middle2.L"].head_local) / 2
hip = bones["UpperLeg.L"].head_local
C.socket(A + "_Socket_Head", arm, "Head", (0, eye_c.y + 0.07, eye_c.z))
C.socket(A + "_Socket_HandR", arm, "Wrist.R", palm_r)
C.socket(A + "_Socket_HandL", arm, "Wrist.L", palm_l)
C.socket(A + "_Socket_Seat", arm, None, (0, hip.y + 0.09, C.SEAT))

notes = {
    "replaces": "npc_man3 (프로토타입 거리/매장의 양복 남)",
    "look": "30대 직장인: 감청 울 수트(노치드 라펠·왼가슴 웰트 포켓·허리 플랩 포켓 2개, 능직 결·닳은 모서리), 하늘빛 흰 셔츠(깃끝), 버건디 레지멘탈 넥타이(매듭, 감청+금색 사선), "
            "감청 목줄+사원증('대한물산 박정훈 영업2팀 과장'), 재킷 단추 2개, 검정 구두(갈색 가죽 밑창). 키 1.76m.",
    "rig": "Quaternius CharacterArmature 62본 유지 (Foot.L/R·PT 는 Root 자식). Generic 리그로 쓸 것.",
    "clips": "Idle, Idle_Neutral, Walk, Run, Wave, Interact (원본) + SitPhone(120f 루프, 좌판 0.65m), Phone(80f 루프, 한 손 파지·화면이 눈을 향함), "
             "Impatient(80f 루프: 팔짱+발끝 까딱+한숨), PointScreen(80f: 오른손 검지로 화면 가리킴, 0/80 프레임은 Idle), "
             "LookBack(80f: 오른쪽 어깨 너머 돌아봄 후 복귀). 24fps.",
    "clips_dropped": "원본 24 클립 중 버림: Death, Gun_Shoot, HitRecieve, HitRecieve_2, Idle_Gun, Idle_Gun_Pointing, Idle_Gun_Shoot, "
                     "Idle_Sword, Kick_Left, Kick_Right, Punch_Left, Punch_Right, Roll, Run_Back, Run_Left, Run_Right, Run_Shoot, Sword_Slash",
    "objects": "NpcSuitMan_Body(몸·수트·셔츠·넥타이·사원증·목줄·단추·구두), NpcSuitMan_Head(머리), NpcSuitMan_Phone(오른손 폰, Phone/SitPhone 때만 켤 것)",
    "sockets": "NpcSuitMan_Socket_Head(Head 본, 시선/자막 기준), _HandR/_HandL(손바닥 중심), _Socket_Seat(SitPhone 때 의자 좌판 윗면 중심, 아마추어 기준)",
    "dynamic": "없음",
}
k3d.export(A, "Characters", [arm], rigged=True, anim=True, notes=notes)
C.previews(A, arm, clip_frames={"Impatient": 6, "Phone": 20, "LookBack": 36, "PointScreen": 30, "SitPhone": 30})
C.play(arm, "Phone", 20)
C.shot(A, "fp", (0.2, -1.3, 1.55), (0.0, 0.0, 1.35), lens=35)
C.play(arm, "Idle", 10)
C.shot(A, "chest", (0.15, -0.8, 1.5), (0.0, 0.0, 1.35), lens=50)
C.validate(os.path.join(k3d.ART, "Models", "Characters", A + ".fbx"), H)

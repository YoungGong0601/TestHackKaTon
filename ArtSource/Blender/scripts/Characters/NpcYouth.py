"""NpcYouth — 뒤 손님 20대 남 (yM: 재촉·"비켜보세요, 제가 먼저 할게요."). 원본 npc_youth1 리그·웨이트·애니 유지.
카키 후드티(가슴 프린트·후드 끈), 검정 나일론 반바지(옆선 흰 두 줄), 흰 양말, 오프화이트 운동화, 흰 무선이어폰, 스마트폰.
실행: K3D_ROOT=... blender -b --factory-startup --python NpcYouth.py
"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import npcb_common as C
from npcb_common import k3d

A, H = "NpcYouth", 1.72
C.decals()
arm, ms = C.load("npc_youth1", A, H)
mouth = C.face(ms["Head"])
C.author_clips(arm)
for m in ms.values():
    C.upgrade(m)
body, legs, feet, head = ms["Body"], ms["Legs"], ms["Feet"], ms["Head"]
bones = arm.data.bones


def shorts(name, col):
    """나일론 반바지: 옅은 광택 + 바깥 옆선 흰 두 줄(노멀 각 3°~9° 띠)."""
    b = C.NB(name, col, 0.7)
    c = b.mixc(b.noise(5.0, 3, 0.55), C.sc(col, 0.88), C.sc(col, 1.15))
    hn = b.math('SQRT', b.math('ADD', b.math('MULTIPLY', b.NX, b.NX), b.math('MULTIPLY_ADD', b.NY, b.NY, 1e-4)))
    side = b.math('DIVIDE', b.math('MULTIPLY', b.NX, b.math('SIGN', b.X)), hn)   # 수평 노멀만: 줄이 고리로 닫히지 않고 세로로
    st = b.math('SUBTRACT', b.ramp(side, 0.9870, 0.9884), b.ramp(side, 0.9963, 0.9975), clamp=True)
    c = b.mixc(st, c, (0.60, 0.60, 0.58))
    c = b.mixc(b.ao(0.035), C.sc(col, 0.45), c)
    b.bump(b.noise(1300.0, 2, 0.6), 0.10, 0.0004)
    b.bump(b.wave(9.0, 'Z', 9.0, 2.0), 0.10, 0.006)
    b.bump(b.noise(7.0, 3, 0.6, dist=1.0), 0.14, 0.008)
    r = b.math('MULTIPLY_ADD', b.noise(18.0, 2), 0.10, 0.65)      # 무광 나일론 (비닐처럼 번들거리지 않게)
    return b.done(c, b.math('MULTIPLY_ADD', st, 0.3, r))


# ---------------------------------------------------------------- 재질
KHAKI = (0.098, 0.094, 0.046)
skin = C.skin(A + "_skin", (0.62, 0.42, 0.31), mouth=mouth)
hair = C.hair(A + "_hair", (0.020, 0.013, 0.010))
eye = C.flat(A + "_eye", (0.010, 0.008, 0.007), 0.12)
ZP = bones["Chest"].head_local.z + 0.005                      # 가슴 프린트 높이
hit = C.ray(body, (0, -1, ZP), (0, 1, 0))
hood = C.fabric(A + "_hoodie", KHAKI, rough=0.93, grain=0.22, grain_scale=900, folds=0.18, wear=0.22, cavity=0.55,
                decals=[("hoodie_print.png", (0.0, hit[0].y if hit else -0.15, ZP), (0.24, 0.09))], emb=0.15)
short = shorts(A + "_shorts", (0.016, 0.016, 0.018))
sock = C.fabric(A + "_socks", (0.74, 0.73, 0.70), rough=0.95, grain=0.3, grain_scale=700, folds=0.08, cavity=0.35)
shoe = C.leather(A + "_sneaker", (0.70, 0.69, 0.66), 0.55, sole=(0.80, 0.79, 0.75), sole_h=0.034, scuff=0.3)
C.set_mats(head, {"Skin": skin, "Eye": eye, "*": hair})
C.hair_flow(head, [hair])
C.set_mats(body, {"Skin": skin, "*": hood})
C.set_mats(legs, {"Skin": skin, "*": short})
C.set_mats(feet, {"White": sock, "*": shoe})

# ---------------------------------------------------------------- 후드 끈 (목 앞 구멍에서 가슴 위로 늘어짐, 끝은 금속 팁)


def tube(bm, pts, r, seg=7, tip=0):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(Vector((1, 0, 0))).normalized()
        b_ = t.cross(a)
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / seg) + b_ * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for i in range(len(rings) - 1):
        for k in range(seg):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
            f.material_index = 1 if i >= len(rings) - 1 - tip else 0
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1]).material_index = 1


zc = bones["Neck"].head_local.z - 0.035
bm = bmesh.new()
for s in (1, -1):
    pts = []
    for i in range(15):
        z = zc - 0.165 * i / 14
        x = s * (0.040 + 0.004 * i / 14)
        h = C.ray(body, (x, -1, z), (0, 1, 0))
        pts.append(Vector((x, (h[0].y if h else -0.14) - 0.0042, z)))
    pts.append(pts[-1] + Vector((0, -0.0006, -0.022)))           # 금속 팁 2.2cm
    tube(bm, pts, 0.0032, tip=1)
cords = C.new_obj(A + "_Cords", bm, [C.fabric(A + "_cord", (0.66, 0.62, 0.53), rough=0.9, grain=0.4, folds=0.0, cavity=0.2),
                                      C.flat(A + "_aglet", (0.55, 0.55, 0.56), 0.3, 1.0)])
k3d.smooth(cords, 50)
C.copy_weights(body, [cords])

# ---------------------------------------------------------------- 무선 이어폰 (양쪽 귀, 흰 유광 플라스틱)
eye_lo, eye_hi = C.mat_bounds(head, [eye.name])
eye_z = (eye_lo[2] + eye_hi[2]) / 2
skin_i = [i for i, s_ in enumerate(head.material_slots) if s_.material == skin]
sv = [head.data.vertices[v].co.copy() for p in head.data.polygons if p.material_index in skin_i for v in p.vertices]
bm = bmesh.new()
for s in (1, -1):
    ear = max((v for v in sv if eye_z - 0.05 < v.z < eye_z + 0.01 and v.x * s > 0), key=lambda v: v.x * s)
    c = Vector((ear.x - s * 0.002, ear.y - 0.004, ear.z - 0.006))
    print("npcb: ear", s, tuple(round(x, 3) for x in ear))
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=1.0,
                              matrix=Matrix.Translation(c) @ Matrix.Diagonal((0.0075, 0.0090, 0.0085, 1)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0030, radius2=0.0027, depth=0.026,
                          matrix=Matrix.Translation(c + Vector((0, -0.004, -0.014))) @ Matrix.Rotation(-0.30, 4, 'X'))
buds = C.new_obj(A + "_Earbuds", bm, [C.flat(A + "_earbud", (0.82, 0.82, 0.80), 0.22)])
k3d.smooth(buds, 60)
C.rigid(buds, "Head", arm)

# ---------------------------------------------------------------- 합치기 · 폰 · 베이크
phone = C.phone(A, arm)
body_o = C.join([body, legs, feet, cords], A + "_Body")
head_o = C.join([head, buds], A + "_Head")
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
    "replaces": "npc_youth1 (프로토타입 줄 선 '뒤 손님' yM: y_hurry1/2/5/7 재촉, y_takeover '비켜보세요, 제가 먼저 할게요.')",
    "look": "20대 남: 카키 후드티(가슴 'ordinary days' 크림 프린트, 후드 끈+금속 팁), 검정 나일론 반바지(옆선 흰 두 줄), 흰 양말, 오프화이트 운동화, 흰 무선이어폰. 키 1.72m.",
    "rig": "Quaternius CharacterArmature 62본 유지 (Foot.L/R·PT 는 Root 자식). Generic 리그로 쓸 것.",
    "clips": "Idle, Idle_Neutral, Walk, Run, Wave, Interact (원본) + SitPhone(120f 루프, 좌판 0.65m), Phone(80f 루프, 한 손 파지·화면이 눈을 향함), "
             "Impatient(80f 루프: 팔짱+발끝 까딱+한숨 — 재촉 대사와 함께), PointScreen(80f: 오른손 검지로 키오스크 화면 가리킴 '어르신, 그거 아니에요.', 0/80 프레임은 Idle), "
             "LookBack(80f: 오른쪽 어깨 너머 돌아봄 후 복귀). 24fps.",
    "clips_dropped": "원본 24 클립 중 버림: Death, Gun_Shoot, HitRecieve, HitRecieve_2, Idle_Gun, Idle_Gun_Pointing, Idle_Gun_Shoot, "
                     "Idle_Sword, Kick_Left, Kick_Right, Punch_Left, Punch_Right, Roll, Run_Back, Run_Left, Run_Right, Run_Shoot, Sword_Slash",
    "objects": "NpcYouth_Body(몸·후드티·끈·반바지·신발), NpcYouth_Head(머리·이어폰), NpcYouth_Phone(오른손 폰, Phone/SitPhone 때만 켤 것)",
    "sockets": "NpcYouth_Socket_Head(Head 본, 시선/자막 기준), _HandR/_HandL(손바닥 중심), _Socket_Seat(SitPhone 때 의자 좌판 윗면 중심, 아마추어 기준)",
    "dynamic": "없음",
}
k3d.export(A, "Characters", [arm], rigged=True, anim=True, notes=notes)
C.previews(A, arm, clip_frames={"Impatient": 6, "PointScreen": 30, "Phone": 20, "LookBack": 36, "SitPhone": 30})
C.play(arm, "Impatient", 10)
C.shot(A, "fp", (0.15, -1.3, 1.55), (0.0, 0.0, 1.3), lens=35)
C.play(arm, "Idle", 10)
C.shot(A, "face", (0.2, -0.7, 1.6), (0.0, 0.0, 1.53), lens=50)
C.validate(os.path.join(k3d.ART, "Models", "Characters", A + ".fbx"), H)

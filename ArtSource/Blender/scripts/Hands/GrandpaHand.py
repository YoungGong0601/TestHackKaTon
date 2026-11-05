"""할아버지 1인칭 손 (GrandpaHand_R / GrandpaHand_L). MakeHuman hm08 기본 메시(CC0) 오른팔 + 기본 리그 가중치로 만든다 (본 이름은 WebXR 25관절).

실행: K3D_HAND_SIDE=R|L blender -b --factory-startup --python GrandpaHand.py   (K3D_FAST=1 이면 저해상도·굽기/내보내기 생략 시험)
원점 = 손목 관절 (1인칭 리그 예외). 손가락 -Y, 손등 +Z. R 엄지 +X, L 엄지 -X.
"""
import sys, os, json, math, subprocess, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
import k3d

SIDE = os.environ.get('K3D_HAND_SIDE', 'R')
FAST = os.environ.get('K3D_FAST') == '1'
A = f'GrandpaHand_{SIDE}'
MIR = 1 if SIDE == 'R' else -1
HERE = os.path.dirname(os.path.abspath(__file__))
PY = k3d.PY
WORK = os.path.join(k3d.CACHE, 'hands_work', SIDE + ('_fast' if FAST else ''))
MH = os.path.join(k3d.CACHE, 'makehuman_dl')  # MakeHuman base.obj · default.mhskel · default_weights.mhw (CC0)
MH_URL = 'https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/'
HAND_L = 0.192  # 손목 관절 ~ 중지 끝 (성인 남성 손 길이 ~19cm)
PALM_W = 0.088  # 손바닥 너비 (너클 높이, 피부 포함 ~9cm)
FING = ['index', 'middle', 'ring', 'pinky']
Y_CUFF = 0.058 if SIDE == 'L' else 0.036  # 소매 시작 (손목 뒤, +Y). L 은 시계가 보이게 뒤로
Y_WATCH = 0.034
TEX_N = 512 if FAST else 2048
BAKE = 512 if FAST else 2048


def chain(f):
    if f == 'thumb':
        return ['thumb-metacarpal', 'thumb-phalanx-proximal', 'thumb-phalanx-distal', 'thumb-tip']
    return [f'{f}-finger-{p}' for p in ('metacarpal', 'phalanx-proximal', 'phalanx-intermediate', 'phalanx-distal', 'tip')]


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ 원본: MakeHuman hm08 기본 메시 오른팔 + 기본 리그 가중치 (둘 다 CC0)
# 관절 위치 = 기본 리그 관절 큐브 중심. MH 본 -> WebXR 이름. lowerarm -> forearm.
MAP = {'wrist.R': 'wrist', 'lowerarm01.R': 'forearm', 'lowerarm02.R': 'forearm',
       'finger1-1.R': 'thumb-metacarpal', 'finger1-2.R': 'thumb-phalanx-proximal', 'finger1-3.R': 'thumb-phalanx-distal'}
for k_, f_ in enumerate(FING):
    MAP[f'metacarpal{k_ + 1}.R'] = f'{f_}-finger-metacarpal'
    for j_, p_ in enumerate(('phalanx-proximal', 'phalanx-intermediate', 'phalanx-distal')):
        MAP[f'finger{k_ + 2}-{j_ + 1}.R'] = f'{f_}-finger-{p_}'
INV = {}
for k_, v_ in MAP.items():
    INV.setdefault(v_, k_)

k3d.reset()
os.makedirs(MH, exist_ok=True)
for rel in ('3dobjs/base.obj', 'rigs/default.mhskel', 'rigs/default_weights.mhw'):
    if not os.path.exists(os.path.join(MH, os.path.basename(rel))):
        urllib.request.urlretrieve(MH_URL + rel, os.path.join(MH, os.path.basename(rel)))
V0, F0, grp = [], [], None
for ln in open(os.path.join(MH, 'base.obj')):
    if ln.startswith('v '):
        V0.append([float(x) for x in ln.split()[1:4]])
    elif ln.startswith('g '):
        grp = ln.split()[1]
    elif ln.startswith('f ') and grp == 'body':
        F0.append([int(t.split('/')[0]) - 1 for t in ln.split()[1:]])
V0 = np.array(V0)
SK = json.load(open(os.path.join(MH, 'default.mhskel')))
MW = json.load(open(os.path.join(MH, 'default_weights.mhw')))['weights']


def mj(key):
    return Vector(V0[SK['joints'][key]].mean(0))


J0 = {'wrist': mj('wrist.R____head')}
for f in FING + ['thumb']:
    c = chain(f)
    for n in c[:-1]:
        J0[n] = mj(INV[n] + '____head')
    J0[c[-1]] = mj(INV[c[-2]] + '____tail')
for f in FING:  # MH 손허리뼈 머리는 손목 한 점에 모여 있다 -> MCP 쪽으로 30%
    J0[f'{f}-finger-metacarpal'] = J0[f'{f}-finger-metacarpal'].lerp(J0[f'{f}-finger-phalanx-proximal'], 0.3)

# 손 좌표계: 손가락 -Y, 손등 +Z, 손목 = 원점, R 엄지 +X
W0 = J0['wrist']
ax = (J0['middle-finger-phalanx-proximal'] - W0).normalized()


def frame(dor):
    dor = (dor - ax * dor.dot(ax)).normalized()
    Rs = Matrix((ax, dor, ax.cross(dor))).transposed()
    Rt = Matrix(((0, -1, 0), (0, 0, 1), (-1, 0, 0))).transposed()
    return Rt @ Rs.inverted()


dor = ax.cross(J0['index-finger-phalanx-proximal'] - J0['pinky-finger-phalanx-proximal'])
R3 = frame(dor)
if (R3 @ (J0['thumb-tip'] - W0)).x < 0:
    R3 = frame(-dor)
Q = (np.array(R3) @ (V0 - np.array(W0)).T).T
s_ = HAND_L / -Q[[i for i, w in MW['finger3-3.R'] if w > 0.5], 1].min()  # 손목 관절 ~ 중지 끝 정점
pal = [i for k in range(1, 5) for i, w in MW[f'metacarpal{k}.R'] if w > 0.5]
sx_ = min(1.15, max(0.95, PALM_W / (s_ * np.ptp(Q[pal, 0]))))  # 남성 손바닥 너비로 가로만 보정
L3 = Matrix.Diagonal((MIR * sx_ * s_, s_, s_)) @ R3
P0 = (np.array(L3) @ (V0 - np.array(W0)).T).T
JP = {k: L3 @ (v - W0) for k, v in J0.items()}
print('scale', round(s_, 4), 'sx', round(sx_, 3), 'middle tip', JP['middle-finger-tip'], 'thumb tip', JP['thumb-tip'])
wsum = np.zeros(len(V0))  # 팔·손 본 가중치 합
for k in MAP:
    for i, w in MW[k]:
        wsum[i] += w
# 팔뚝을 +Y 로 곧게 (MH 손목은 꺾여 있어 소매를 뚫는다): 손목 뒤로 갈수록 팔꿈치 방향 -> +Y
fa = (L3 @ (mj('lowerarm01.R____head') - W0)).normalized()
k_ = fa.cross(Vector((0, 1, 0)))
th_ = math.asin(min(1.0, k_.length))
k_ = np.array(k_.normalized())
ang = th_ * sstep(-0.005, 0.05, P0[:, 1])[:, None]
P0 = P0 * np.cos(ang) + np.cross(k_, P0) * np.sin(ang) + np.outer(P0 @ k_, k_) * (1 - np.cos(ang))
# 손목·팔뚝은 남성 굵기로 (+12%)
ring = P0[(wsum > 0.5) & (np.abs(P0[:, 1] - 0.012) < 0.004)]
cx, cz = ring[:, 0].mean(), ring[:, 2].mean()
print('forearm bend deg', round(math.degrees(th_), 1), 'wrist section cm', round(np.ptp(ring[:, 0]) * 100, 1), round(np.ptp(ring[:, 2]) * 100, 1))
k_ = 1 + 0.12 * sstep(-0.02, 0.01, P0[:, 1])
P0[:, 0] = cx + (P0[:, 0] - cx) * k_
P0[:, 2] = cz + (P0[:, 2] - cz) * k_
# 소매 속 팔뚝은 소매 입구 단면(x0.95) 원통으로 눌러 넣는다 (MH 팔뚝 근육이 소매를 뚫지 않게)
ring = P0[(wsum > 0.5) & (np.abs(P0[:, 1] - Y_CUFF - 0.01) < 0.004)]
cx, cz, hx, hz = ring[:, 0].mean(), ring[:, 2].mean(), np.ptp(ring[:, 0]) / 2 * 0.95, np.ptp(ring[:, 2]) / 2 * 0.95
b_ = sstep(Y_CUFF + 0.012, Y_CUFF + 0.05, P0[:, 1])
t_ = np.arctan2((P0[:, 2] - cz) / hz, (P0[:, 0] - cx) / hx)
P0[:, 0] += b_ * (cx + np.cos(t_) * hx - P0[:, 0])
P0[:, 2] += b_ * (cz + np.sin(t_) * hz - P0[:, 2])

# 손등 방향: 손가락 = 손등(+Z)을 본에 직교화. 엄지 = MH 회전면(엄지 끝·IP·손목)의 면 안, 손바닥 반대쪽
JD = {'wrist': Vector((0, 0, 1))}
nrm = (JP['thumb-phalanx-distal'] - JP['wrist']).cross(JP['thumb-tip'] - JP['wrist']).normalized()
for f in FING + ['thumb']:
    c = chain(f)
    for i, n in enumerate(c):
        a = (JP[c[i + 1]] - JP[n]) if i + 1 < len(c) else (JP[n] - JP[c[i - 1]])
        a.normalize()
        if f == 'thumb':
            d = nrm.cross(a).normalized()
            if d.dot(JP['middle-finger-phalanx-proximal'] - JP['thumb-phalanx-distal']) > 0:
                d = -d
        else:
            d = Vector((0, 0, 1))
            d = (d - a * d.dot(a)).normalized()
        JD[n] = d

# 팔 면만: 팔·손 본 가중치 합 > 0.5, 손목 뒤 16cm 까지 (소매 속에서 열린 끝)
faces = [f for f in F0 if all(wsum[i] > 0.5 and P0[i, 1] < 0.16 for i in f)]
used = sorted({i for f in faces for i in f})
rm = {o: n for n, o in enumerate(used)}
me = bpy.data.meshes.new(A + '_Skin')
me.from_pydata(P0[used].tolist(), [], [[rm[i] for i in (f if MIR > 0 else f[::-1])] for f in faces])
skin = bpy.data.objects.new(me.name, me)
bpy.context.scene.collection.objects.link(skin)
for k, v in MAP.items():
    vg = skin.vertex_groups.get(v) or skin.vertex_groups.new(name=v)
    for i, w in MW[k]:
        if i in rm:
            vg.add([rm[i]], w, 'ADD')
print('faces', len(me.polygons))

sub = skin.modifiers.new('sub', 'SUBSURF')
sub.levels = sub.render_levels = 1
k3d.apply_all(skin)
for p in me.polygons:
    p.use_smooth = True

# ------------------------------------------------------------------ 가중치 정규화, 노인 손 굴곡 (마디·힘줄·손허리뼈 사이 골)
names = [g.name for g in skin.vertex_groups]
gi = {n: i for i, n in enumerate(names)}
nV = len(me.vertices)
Wt = np.zeros((nV, len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        Wt[v.index, g.group] = g.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-6)
P = np.array([v.co for v in me.vertices], np.float64)
Nn = np.array([v.normal for v in me.vertices], np.float64)
thw = np.clip(sum(Wt[:, gi[n]] for n in ('thumb-metacarpal', 'thumb-phalanx-proximal', 'thumb-phalanx-distal')), 0, 1)


def bulge(j_name, prev_name, amp, sig, dorsal_only):
    J = np.array(JP[j_name]); ch = None
    for f in FING + ['thumb']:
        c = chain(f)
        if j_name in c:
            ch = c
    i = ch.index(j_name)
    a = np.array((JP[ch[i + 1]] - JP[j_name]).normalized())
    d = np.array(JD[j_name])
    t = (P - J) @ a
    w = np.clip(Wt[:, gi[j_name]] + Wt[:, gi[prev_name]], 0, 1)
    g = np.exp(-t * t / (2 * sig * sig)) * w
    nd = Nn @ d
    fac = np.clip(nd, 0, 1) ** 1.3 if dorsal_only else np.clip(0.45 + 0.55 * nd, 0, 1)
    return Nn * (amp * g * fac)[:, None]


def ridge(p0, p1, amp, sig, t0=0.0, t1=1.0):
    """손등 선(p0->p1, 위에서 본 XY) 따라 법선 방향 융기(amp>0) 또는 골(amp<0). 엄지·손바닥 제외."""
    p0, p1 = np.array(p0[:2]), np.array(p1[:2])
    a = p1 - p0; L = np.linalg.norm(a); a /= L
    q = P[:, :2] - p0
    t = q @ a / L
    d = q - np.outer(np.clip(t, 0, 1) * L, a)
    g = np.exp(-(d ** 2).sum(1) / (2 * sig * sig)) * sstep(t0, t0 + 0.25, t) * (1 - sstep(t1 - 0.2, t1, t))
    return Nn * (amp * g * np.clip(Nn[:, 2], 0, 1) ** 1.5 * (1 - thw))[:, None]


off = np.zeros_like(P)
for f in FING:
    c = chain(f)
    off += bulge(c[1], c[0], 0.0026, 0.0065, True)   # 너클 (MCP)
    off += bulge(c[2], c[1], 0.0016, 0.0040, False)  # PIP (관절염으로 부은 마디)
    off += bulge(c[3], c[2], 0.0009, 0.0030, False)  # DIP
off += bulge('thumb-phalanx-distal', 'thumb-phalanx-proximal', 0.0013, 0.0038, False)
off += bulge('thumb-phalanx-proximal', 'thumb-metacarpal', 0.0018, 0.0055, True)
TEND = {f: (Vector((JP[f'{f}-finger-phalanx-proximal'].x * 0.3, 0.004, 0)), JP[f'{f}-finger-phalanx-proximal']) for f in FING}
for f in FING:  # 펴는 힘줄 (손목 -> 너클)
    off += ridge(*TEND[f], 0.0018, 0.0024, 0.1, 1.05)
for f, g in zip(FING, FING[1:]):  # 손허리뼈 사이 골
    off += ridge((TEND[f][0] + TEND[g][0]) / 2, (TEND[f][1] + TEND[g][1]) / 2, -0.0011, 0.0035, 0.15, 0.9)
P += off
me.vertices.foreach_set('co', P.astype(np.float32).ravel())
for g in skin.vertex_groups:
    col = Wt[:, g.index]
    idx = np.nonzero(col > 1e-4)[0]
    g.remove(list(range(nV)))
    for i in idx:
        g.add([int(i)], float(col[i]), 'REPLACE')


# ------------------------------------------------------------------ 리그 (계층 재구성, 이름은 WebXR 그대로)
ad = bpy.data.armatures.new(A + '_Rig')
arm = bpy.data.objects.new(A + '_Rig', ad)
bpy.context.scene.collection.objects.link(arm)
k3d.select([arm])
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
b = eb.new('forearm'); b.head = (0, 0, 0); b.tail = (0, 0.07, 0); b.align_roll(Vector((0, 0, 1)))
b = eb.new('wrist'); b.head = (0, 0, 0); b.tail = JP['middle-finger-metacarpal'] * 0.999 + Vector((0, -0.02, 0))
b.align_roll(JD['wrist']); b.parent = eb['forearm']
for f in FING + ['thumb']:
    c = chain(f)
    par = eb['wrist']
    for i, n in enumerate(c):
        b = eb.new(n)
        b.head = JP[n]
        b.tail = JP[c[i + 1]] if i + 1 < len(c) else JP[n] + (JP[n] - JP[c[i - 1]]).normalized() * 0.008
        b.align_roll(JD[n] if i + 1 < len(c) else JD[c[i - 1]])
        b.parent = par
        par = b
bpy.ops.object.mode_set(mode='OBJECT')


def skin_to(o, groups=None):
    """o 를 리그에 붙인다 (groups=None 이면 forearm 100%)."""
    o.parent = arm
    if groups is None:
        vg = o.vertex_groups.new(name='forearm')
        vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    m = o.modifiers.new('Armature', 'ARMATURE')
    m.object = arm


skin_to(skin, groups=True)

# ------------------------------------------------------------------ 투영 좌표 (텍스처 스크립트와 같은 함수)
TOP = dict(N=TEX_N, S=0.30, x0=-0.15, y0=-0.215)
O_t = JP['thumb-phalanx-proximal']
e_v = (JP['thumb-tip'] - O_t).normalized()
n_t = JD['thumb-phalanx-distal']
n_t = (n_t - e_v * n_t.dot(e_v)).normalized()
e_u = e_v.cross(n_t)
THB = dict(N=TEX_N // 2, S=0.10, x0=-0.05, y0=-0.03)


def p_top(p):
    return [float(p.x), float(p.y)]


def p_thumb(p):
    q = p - O_t
    return [float(q.dot(e_u)), float(q.dot(e_v))]


cfg = {'out': WORK, 'side': SIDE, 'seed': 11 if SIDE == 'R' else 23, 'rs': MIR, 'knit': True, 'dial': SIDE == 'L',
       'maps': {'top': dict(TOP, j={k: p_top(v) for k, v in JP.items()}),
                'bot': dict(TOP, j={k: p_top(v) for k, v in JP.items()}),
                'thumb': dict(THB, j={k: p_thumb(v) for k, v in JP.items()})}}
os.makedirs(WORK, exist_ok=True)
cp = os.path.join(WORK, 'cfg.json')
json.dump(cfg, open(cp, 'w'))
subprocess.run([PY, '-I', os.path.join(HERE, 'GrandpaHand_tex.py'), cp], check=True)


def img(n, nc=True):
    return k3d.load_image(os.path.join(WORK, n), name=f'{A}_{n}', non_color=nc)


# UV 레이어: UV_top (손등·손바닥 공용), UV_thumb + 색 속성 PJ (R 손등 가중, G 엄지 가중, B 측면 페이드)
def set_proj_uv(o, name, fn, mp):
    me = o.data
    uv = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    co = [o.data.vertices[l.vertex_index].co for l in me.loops]
    a = np.array([fn(c) for c in co], np.float64)
    a[:, 0] = (a[:, 0] - mp['x0']) / mp['S']
    a[:, 1] = (a[:, 1] - mp['y0']) / mp['S']
    uv.data.foreach_set('uv', a.astype(np.float32).ravel())


def set_pj(o):
    me = o.data
    th = np.zeros(len(me.vertices), np.float32)
    for v in me.vertices:
        for g in v.groups:
            nm = o.vertex_groups[g.group].name
            if nm in ('thumb-phalanx-proximal', 'thumb-phalanx-distal', 'thumb-tip'):
                th[v.index] += g.weight
            elif nm == 'thumb-metacarpal':
                th[v.index] += 0.4 * g.weight
    N = np.array([v.normal for v in me.vertices])
    wt = sstep(-0.3, 0.3, N[:, 2])
    wth = np.clip(th, 0, 1) * sstep(-0.2, 0.35, N @ np.array(n_t))
    fade = sstep(0.12, 0.5, np.abs(N[:, 2]))
    fade = np.maximum(fade, wth)
    at = me.color_attributes.new('PJ', 'FLOAT_COLOR', 'POINT')
    at.data.foreach_set('color', np.stack([wt, wth, fade, np.ones_like(wt)], 1).astype(np.float32).ravel())


set_proj_uv(skin, 'UV_top', p_top, TOP)
set_proj_uv(skin, 'UV_thumb', p_thumb, THB)
set_pj(skin)

# ------------------------------------------------------------------ 손톱 (두껍고 누런 노인 손톱): 원위 마디 본 좌표계에서 만든 곡면 판
bvh = BVHTree.FromObject(skin, bpy.context.evaluated_depsgraph_get())
NAIL = {'thumb': (0.0118, 0.0112, 0.0026), 'index': (0.0106, 0.0108, 0.002), 'middle': (0.0112, 0.0114, 0.002),
        'ring': (0.0103, 0.0106, 0.002), 'pinky': (0.0085, 0.0088, 0.0018)}  # (폭, 길이, 손끝에서 뒤로 m)


def nail(f):
    """본 로컬 Y = 손가락 축, 로컬 Z = 손등. 판을 손등 쪽에서 -Z 로 투사(Shrinkwrap 투사와 같음)하고,
    끝 30% 는 피부가 떨어져도 완만하게 이어 가 손끝을 덮지 않게 한다. 가장자리는 피부 속으로 살짝 묻는다(손톱 주름)."""
    c = chain(f)
    M = arm.matrix_world @ arm.data.bones[c[-2]].matrix_local
    D = M.translation.copy()
    a, n = M.col[1].xyz.normalized(), M.col[2].xyz.normalized()
    b = a.cross(n)
    Wn, Ln, back = NAIL[f]
    hit = bvh.ray_cast(D + a * 0.06 + n * 0.001, -a)
    s_tip = (hit[0] - D).dot(a) if hit[0] else (JP[c[-1]] - D).dot(a) + 0.006
    s_free = s_tip - back
    nu, nv = 13, 15
    zs = {}
    for i in range(nu):
        u = i / (nu - 1) * 2 - 1
        prev = None
        for j in range(nv):
            v = j / (nv - 1)
            s = (s_free - Ln * (1 - 0.30 * u * u)) * (1 - v) + (s_free - Ln * 0.07 * u * u) * v  # 둥근 큐티클 호 / 둥근 끝
            hw = Wn / 2 * (0.86 + 0.14 * math.sin(min(1.0, v * 1.6) * math.pi / 2))
            p0 = D + a * s + b * (u * hw)
            h = bvh.ray_cast(p0 + n * 0.03, -n)
            z = (h[0] - D).dot(n) if h[0] else (prev[0] if prev else 0.004)
            if prev is not None and v > 0.55:  # 손끝 곡면을 따라 내려가지 않음 (자유연이 살짝 떠 있음)
                z = max(z, prev[0] - 0.12 * (s - prev[1]))
            prev = (z, s)
            lift = 0.0007 * (1 - u * u) ** 0.8 * sstep(0.0, 0.2, v) - 0.00014  # 가로 곡률, 가장자리는 피부 속
            zs[i, j] = (D + a * s + b * (u * hw) + n * (z + lift), ((u + 1) / 2, v))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    vs = {k: (bm.verts.new(p), uv) for k, (p, uv) in zs.items()}
    for j in range(nv - 1):
        for i in range(nu - 1):
            q = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
            fc = bm.faces.new([x[0] for x in q])
            for l, x in zip(fc.loops, q):
                l[uvl].uv = x[1]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fm = bpy.data.meshes.new(f'{A}_Nail_{f}')
    bm.to_mesh(fm); bm.free()
    o = bpy.data.objects.new(fm.name, fm)
    bpy.context.scene.collection.objects.link(o)
    if sum((p.normal for p in fm.polygons), Vector()).dot(n) < 0:
        for p in fm.polygons:
            p.flip()
    s_ = o.modifiers.new('sol', 'SOLIDIFY')
    s_.thickness, s_.offset, s_.use_rim = 0.0007, -1, True
    bv = o.modifiers.new('bev', 'BEVEL')
    bv.width, bv.segments, bv.limit_method = 0.00016, 2, 'ANGLE'
    vg = o.vertex_groups.new(name=c[-2])
    vg.add(list(range(len(fm.vertices))), 1.0, 'REPLACE')
    for p in fm.polygons:
        p.use_smooth = True
    print('nail', f, 'tip', round(s_tip, 4), 'free', round(s_free, 4))
    return o


nails = [nail(f) for f in FING + ['thumb']]

# ------------------------------------------------------------------ 머티리얼


class NT:
    """노드 트리 도우미."""

    def __init__(s, m):
        s.m, s.nt = m, m.node_tree
        s.p = k3d.principled(m)

    def n(s, t, **kw):
        x = s.nt.nodes.new(t)
        for k, v in kw.items():
            setattr(x, k, v)
        return x

    def link(s, a, b):
        s.nt.links.new(a, b)

    def img(s, im, uv):
        t = s.n('ShaderNodeTexImage', image=im, extension='EXTEND', interpolation='Cubic')
        u = s.n('ShaderNodeUVMap', uv_map=uv)
        s.link(u.outputs[0], t.inputs[0])
        return t

    def sep(s, sock):
        x = s.n('ShaderNodeSeparateColor')
        s.link(sock, x.inputs[0])
        return x.outputs

    def math(s, op, a, b=None, clamp=False):
        x = s.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                x.inputs[i].default_value = v
            else:
                s.link(v, x.inputs[i])
        return x.outputs[0]

    def mix(s, fac, a, b, kind='RGBA', blend='MIX'):
        x = s.n('ShaderNodeMix', data_type=kind, blend_type=blend) if kind == 'RGBA' else s.n('ShaderNodeMix', data_type=kind)
        ins = {'RGBA': (6, 7), 'FLOAT': (2, 3)}[kind]
        for sock, v in ((x.inputs[0], fac), (x.inputs[ins[0]], a), (x.inputs[ins[1]], b)):
            if isinstance(v, (int, float)):
                sock.default_value = v
            elif isinstance(v, tuple):
                sock.default_value = (*v[:3], 1) if kind == 'RGBA' else v
            else:
                s.link(v, sock)
        return x.outputs[2] if kind == 'RGBA' else x.outputs[0]

    def noise(s, scale, detail=4, rough=0.55, vec=None):
        x = s.n('ShaderNodeTexNoise')
        x.inputs['Scale'].default_value = scale
        x.inputs['Detail'].default_value = detail
        x.inputs['Roughness'].default_value = rough
        if vec is not None:
            s.link(vec, x.inputs['Vector'])
        return x.outputs['Fac']

    def coord(s, kind='Object'):
        return s.n('ShaderNodeTexCoord').outputs[kind]


def skin_mat():
    m = k3d.mat(f'M_{A}_SkinSrc', (0.42, 0.25, 0.165), 0.52)
    t = NT(m)
    th = t.img(img(f'{SIDE}_top_h.png'), 'UV_top')
    tm = t.sep(t.img(img(f'{SIDE}_top_m.png'), 'UV_top').outputs[0])
    tn = t.sep(t.img(img(f'{SIDE}_top_n.png'), 'UV_top').outputs[0])
    bh = t.img(img(f'{SIDE}_bot_h.png'), 'UV_top')
    bmk = t.sep(t.img(img(f'{SIDE}_bot_m.png'), 'UV_top').outputs[0])
    hh = t.img(img(f'{SIDE}_thumb_h.png'), 'UV_thumb')
    hm = t.sep(t.img(img(f'{SIDE}_thumb_m.png'), 'UV_thumb').outputs[0])
    hn = t.sep(t.img(img(f'{SIDE}_thumb_n.png'), 'UV_thumb').outputs[0])
    at = t.n('ShaderNodeAttribute', attribute_name='PJ', attribute_type='GEOMETRY')
    pj = t.sep(at.outputs['Color'])
    wtop, wth, fade = pj[0], pj[1], pj[2]
    wbot = t.math('SUBTRACT', 1.0, wtop)
    # 높이 합성
    H = t.mix(wtop, bh.outputs[0], th.outputs[0], 'FLOAT')
    H = t.mix(wth, H, hh.outputs[0], 'FLOAT')
    H = t.math('MULTIPLY', t.math('SUBTRACT', H, 0.5), fade)
    ob = t.coord()
    # 건조한 피부: 마름모 잔금(보로노이 경계) + 모공
    vo = t.n('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE')
    vo.inputs['Scale'].default_value = 700
    vo.inputs['Randomness'].default_value = 0.85
    t.link(ob, vo.inputs['Vector'])
    crack = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', vo.outputs['Distance'], 9.0, True))
    pores = t.noise(2600, 2, 0.5, ob)
    fine = t.math('ADD', t.math('MULTIPLY', crack, -0.007), t.math('MULTIPLY', pores, 0.005))
    bump = t.n('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.004
    t.link(H, bump.inputs['Height'])
    bump2 = t.n('ShaderNodeBump')
    bump2.inputs['Distance'].default_value = 0.004
    bump2.inputs['Strength'].default_value = 0.6
    t.link(fine, bump2.inputs['Height'])
    t.link(bump.outputs['Normal'], bump2.inputs['Normal'])
    t.link(bump2.outputs['Normal'], t.p.inputs['Normal'])
    # 색
    big = t.noise(28, 3, 0.5, ob)
    mid = t.noise(140, 4, 0.6, ob)
    c = t.mix(big, (0.40, 0.24, 0.16), (0.47, 0.30, 0.18))
    c = t.mix(t.math('MULTIPLY', mid, 0.35), c, (0.46, 0.22, 0.16))
    f_top = t.math('MULTIPLY', wtop, fade)
    f_th = wth
    # 손등: 붉은기, 정맥(청보라 multiply), 검버섯(15~25% 어두운 황갈색 multiply), 털, 흉터
    red = t.math('MAXIMUM', t.math('MULTIPLY', tm[2], f_top), t.math('MULTIPLY', hm[2], f_th))
    c = t.mix(t.math('MULTIPLY', red, 0.38), c, (0.50, 0.17, 0.13))
    c = t.mix(t.math('MULTIPLY', tm[0], t.math('MULTIPLY', f_top, 0.3)), c, (0.58, 0.68, 0.95), blend='MULTIPLY')
    spot = t.math('MAXIMUM', t.math('MULTIPLY', tm[1], f_top), t.math('MULTIPLY', hm[1], f_th))
    c = t.mix(spot, c, (0.82, 0.74, 0.62), blend='MULTIPLY')
    c = t.mix(t.math('MULTIPLY', tn[2], t.math('MULTIPLY', f_top, 0.35)), c, (0.30, 0.17, 0.11))
    hair_w = t.math('MAXIMUM', t.math('MULTIPLY', tn[0], f_top), t.math('MULTIPLY', hn[0], f_th))
    c = t.mix(t.math('MULTIPLY', hair_w, 0.22), c, (0.62, 0.60, 0.56))
    c = t.mix(t.math('MULTIPLY', tn[1], t.math('MULTIPLY', f_top, 0.3)), c, (0.04, 0.03, 0.025))
    # 손바닥: 밝고 분홍, 굳은살, 손금 어둡게
    fb = t.math('MULTIPLY', wbot, t.math('SUBTRACT', 1.0, wth))
    palm = t.mix(mid, (0.50, 0.29, 0.21), (0.54, 0.27, 0.21))
    palm = t.mix(t.math('MULTIPLY', bmk[1], 0.6), palm, (0.56, 0.23, 0.19))
    palm = t.mix(t.math('MULTIPLY', bmk[2], 0.55), palm, (0.52, 0.38, 0.24))
    palm = t.mix(t.math('MULTIPLY', bmk[0], 0.6), palm, (0.28, 0.14, 0.10))
    c = t.mix(fb, c, palm)
    # 주름 골 어둡게 (높이 음수)
    cav = t.math('MULTIPLY', t.math('MAXIMUM', t.math('MULTIPLY', H, -10.0), 0.0), 1.0, True)
    c = t.mix(t.math('MULTIPLY', cav, 0.38), c, (0.24, 0.13, 0.09))
    ao = t.n('ShaderNodeAmbientOcclusion', samples=16, only_local=True)
    ao.inputs['Distance'].default_value = 0.004
    c = t.mix(t.math('MULTIPLY', t.math('SUBTRACT', 1.0, ao.outputs['AO']), 0.6), c, (0.20, 0.10, 0.07))
    t.link(c, t.p.inputs['Base Color'])
    # 거칠기: 기본 0.52, 주름·손바닥 거칠게, 손끝 약간 번들
    r = t.math('ADD', 0.50, t.math('MULTIPLY', mid, 0.08))
    r = t.math('ADD', r, t.math('MULTIPLY', cav, 0.15))
    r = t.math('ADD', r, t.math('MULTIPLY', fb, 0.06))
    r = t.math('SUBTRACT', r, t.math('MULTIPLY', bmk[1], t.math('MULTIPLY', fb, 0.1)))
    t.link(r, t.p.inputs['Roughness'])
    return m


def nail_mat():
    """누렇게 두꺼워진 노인 손톱. UV: u = 폭(0..1), v = 큐티클 0 -> 자유연 1.
    세로 골 명도차 ~6%, 끝은 부드러운 아이보리 1~1.5mm 띠, 반달·옆 홈·큐티클은 약하게."""
    m = k3d.mat(f'M_{A}_NailSrc', (0.55, 0.42, 0.31), 0.34)
    t = NT(m)
    sp = t.sep(t.n('ShaderNodeUVMap', uv_map='UVMap').outputs[0])
    u, v = sp[0], sp[1]
    ob = t.coord()
    n1 = t.noise(700, 3, 0.55, ob)
    n2 = t.noise(120, 2, 0.5, ob)
    rid = t.math('ADD', t.math('MULTIPLY', t.math('SINE', t.math('ADD', t.math('MULTIPLY', u, 40.0), t.math('MULTIPLY', n2, 5.0))), 0.5), 0.5)
    c = t.mix(n2, (0.47, 0.31, 0.23), (0.51, 0.36, 0.26))  # 비치는 분홍 손톱바닥 + 누런 판 (피부보다 약간 밝게)
    c = t.mix(rid, c, (0.935, 0.935, 0.935), blend='MULTIPLY')  # 세로 골
    st = t.math('MULTIPLY', t.math('SUBTRACT', t.noise(55, 2, 0.5, ob), 0.58, True), 2.5)
    c = t.mix(t.math('MULTIPLY', st, 0.3), c, (0.45, 0.32, 0.17))  # 누런 세로 얼룩 (부드럽게)
    lun = t.math('SUBTRACT', 1.0, t.math('MULTIPLY', v, 6.0), True)
    c = t.mix(t.math('MULTIPLY', lun, 0.25), c, (0.56, 0.44, 0.37))  # 반달
    side = t.math('MULTIPLY', t.math('SUBTRACT', t.math('MULTIPLY', t.math('ABSOLUTE', t.math('SUBTRACT', u, 0.5)), 2.0), 0.8), 5.0, True)
    c = t.mix(t.math('MULTIPLY', side, 0.3), c, (0.40, 0.25, 0.19))  # 옆 홈
    fe = t.math('MULTIPLY', t.math('SUBTRACT', v, 0.875), 22.0, True)
    c = t.mix(t.math('MULTIPLY', fe, 0.75), c, (0.60, 0.52, 0.40))  # 자유연 아이보리 (~1.3mm)
    c = t.mix(t.math('SUBTRACT', 1.0, t.math('MULTIPLY', v, 18.0), True), c, (0.36, 0.21, 0.15))  # 큐티클
    t.link(c, t.p.inputs['Base Color'])
    bump = t.n('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.00012
    bump.inputs['Strength'].default_value = 0.18
    t.link(t.math('ADD', t.math('MULTIPLY', n1, 0.6), t.math('MULTIPLY', rid, 0.4)), bump.inputs['Height'])
    t.link(bump.outputs['Normal'], t.p.inputs['Normal'])
    t.link(t.math('ADD', t.math('ADD', t.math('MULTIPLY', n1, 0.12), 0.30), t.math('MULTIPLY', fe, 0.15)), t.p.inputs['Roughness'])
    return m


sk_m = skin_mat()
skin.data.materials.append(sk_m)
hid_m = k3d.mat(f'M_{A}_ForearmHidden', (0.40, 0.24, 0.16), 0.6)
skin.data.materials.append(hid_m)
for p in skin.data.polygons:  # 소매 속 팔뚝은 아틀라스를 쓰지 않는다
    if p.center.y > Y_CUFF + 0.018:
        p.material_index = 1
nm_ = nail_mat()
for o in nails:
    o.data.materials.append(nm_)
    k3d.apply_all(o)
# 손톱 합치기 (UV_top/UV_thumb/PJ 는 손톱 쪽 값이 0 이어도 무방)
k3d.select([skin] + nails, skin)
bpy.ops.object.join()
skin = bpy.context.view_layer.objects.active

# ------------------------------------------------------------------ 소매 (뜨개 카디건: 고무단 + 몸판, 주름)


def cross_section(y, pad):
    me = skin.data
    pts = np.array([v.co for v in me.vertices if abs(v.co.y - y) < 0.006 and v.co.y > 0.005])
    c = pts.mean(0)
    return c[0], c[2], (pts[:, 0].max() - pts[:, 0].min()) / 2 + pad, (pts[:, 2].max() - pts[:, 2].min()) / 2 + pad


def sleeve():
    cxs, czs, rx0, rz0 = cross_section(Y_CUFF + 0.01, 0.0075)
    rx0, rz0 = max(rx0, 0.031), max(rz0, 0.025)
    NA, L = 72, 0.34  # 프로토타입 소매 길이 0.34m, 뒤끝은 열린 튜브
    ys = [0.0, 0.002, 0.006] + list(np.linspace(0.012, 0.05, 9)) + list(np.linspace(0.056, L, 32))
    rng = np.random.default_rng(5 if SIDE == 'R' else 9)
    ph = rng.uniform(0, 6.28, 6)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    reps = 8
    for k, yy in enumerate(ys):
        grow = 1 + 0.4 * sstep(0.05, L, yy) ** 0.8
        lip = 0.0 if yy > 0.006 else -0.0025 * (1 - yy / 0.006)  # 접힌 끝단 둥글게
        row = []
        for i in range(NA):
            t = i / NA * 2 * math.pi
            r = 1.0
            if yy > 0.05:  # 소매 주름 (손목 쪽에 몰림)
                bunch = math.exp(-((yy - 0.09) / 0.05) ** 2)
                r += 0.05 + (0.07 * bunch + 0.025) * math.sin(yy * 95 + 3 * t + ph[0]) * (0.6 + 0.4 * math.sin(2 * t + ph[1]))
                r += 0.03 * math.sin(yy * 23 + t * 2 + ph[2]) + 0.015 * math.sin(yy * 51 - t + ph[3])
                r += 0.06 * max(0, -math.sin(t)) * sstep(0.1, 0.3, yy)  # 아래로 처짐
            x = cxs + math.cos(t) * (rx0 * grow * r + lip)
            z = czs + math.sin(t) * (rz0 * grow * r + lip) - 0.01 * sstep(0.08, L, yy)
            row.append(bm.verts.new((x, Y_CUFF + yy - (0.004 if k == 0 else 0), z)))
        rows.append(row)
    for k in range(len(rows) - 1):
        for i in range(NA):
            q = [rows[k][i], rows[k][(i + 1) % NA], rows[k + 1][(i + 1) % NA], rows[k + 1][i]]
            fc = bm.faces.new(q)
            fc.material_index = 0 if ys[k] < 0.05 else 1
            for l, (ii, kk) in zip(fc.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                l[uvl].uv = (ii / NA * reps, (ys[kk]) / 0.04)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sm = bpy.data.meshes.new(A + '_Sleeve')
    bm.to_mesh(sm); bm.free()
    o = bpy.data.objects.new(sm.name, sm)
    bpy.context.scene.collection.objects.link(o)
    # 법선이 바깥을 향하게
    c0 = Vector((cxs, Y_CUFF + 0.1, czs))
    if sum(((p.center - Vector((cxs, p.center.y, czs))).dot(p.normal) for p in sm.polygons)) < 0:
        for p in sm.polygons:
            p.flip()
    so = o.modifiers.new('sol', 'SOLIDIFY')
    so.thickness, so.offset = 0.004, -1
    so.use_rim = True
    k3d.apply_all(o)
    for p in sm.polygons:
        p.use_smooth = True
    # k3d.tile 의 PNG->JPG 변환이 지연 로딩 이미지에서 실패하므로 JPG 로 미리 변환 (k3d 수정 금지)
    subprocess.run([PY, '-I', '-c', 'import sys;from PIL import Image\nfor p in sys.argv[1:]: Image.open(p).convert("RGB").save(p[:-4]+".jpg", quality=93)']
                   + [os.path.join(WORK, f'{k}_{m}.png') for k in ('rib', 'knit') for m in ('diff', 'nor')], check=True)
    J_ = lambda n: os.path.join(WORK, n)
    sk = k3d.tile('Hands_Rib', maps={'diff': J_('rib_diff.jpg'), 'nor': J_('rib_nor.jpg'), 'rough': J_('rib_rough.png')})
    kn = k3d.tile('Hands_Knit', maps={'diff': J_('knit_diff.jpg'), 'nor': J_('knit_nor.jpg'), 'rough': J_('knit_rough.png')})
    sm.materials.append(sk)
    sm.materials.append(kn)
    skin_to(o)
    return o


slv = sleeve()

# ------------------------------------------------------------------ 시계 (L): 스틸 케이스·가죽 줄·문자판·유리


def watch():
    cxw, czw, hx, hz = cross_section(Y_WATCH, 0.0)
    top = czw + hz
    parts = []

    def obj_from_bm(bm, name, mat):
        mm = bpy.data.meshes.new(name)
        bm.to_mesh(mm); bm.free()
        o = bpy.data.objects.new(name, mm)
        bpy.context.scene.collection.objects.link(o)
        mm.materials.append(mat)
        for p in mm.polygons:
            p.use_smooth = True
        parts.append(o)
        return o

    steel = k3d.mat(f'M_{A}_WatchSteelSrc', (0.60, 0.58, 0.55), 0.26, 1.0)
    t = NT(steel)
    ob = t.coord()
    stretch = t.n('ShaderNodeMapping')
    stretch.inputs['Scale'].default_value = (1.0, 1.0, 60.0)
    t.link(ob, stretch.inputs['Vector'])
    br = t.noise(1600, 2, 0.5, stretch.outputs[0])
    smap = t.n('ShaderNodeMapping')  # 가늘고 긴 잔 스크래치 (셀 무늬 없음)
    smap.inputs['Scale'].default_value = (45.0, 1.0, 1.0)
    smap.inputs['Rotation'].default_value = (0.4, 0.7, 1.1)
    t.link(ob, smap.inputs['Vector'])
    scr = t.math('MULTIPLY', t.math('SUBTRACT', t.noise(700, 2, 0.5, smap.outputs[0]), 0.66, True), 6.0, True)
    ao = t.n('ShaderNodeAmbientOcclusion', samples=16, only_local=True)
    ao.inputs['Distance'].default_value = 0.002
    grime = t.math('SUBTRACT', 1.0, ao.outputs['AO'])
    t.link(t.mix(grime, (0.60, 0.58, 0.55), (0.10, 0.09, 0.07)), t.p.inputs['Base Color'])
    t.link(t.math('SUBTRACT', 1.0, t.math('MULTIPLY', grime, 0.9)), t.p.inputs['Metallic'])
    t.link(t.math('ADD', t.math('ADD', 0.2, t.math('MULTIPLY', br, 0.1)), t.math('ADD', t.math('MULTIPLY', scr, 0.14), t.math('MULTIPLY', grime, 0.5))), t.p.inputs['Roughness'])

    leather = k3d.mat(f'M_{A}_WatchStrapSrc', (0.07, 0.035, 0.018), 0.5)
    t = NT(leather)
    ob = t.coord()
    vo = t.n('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 2200
    t.link(ob, vo.inputs['Vector'])
    sp = t.sep(t.n('ShaderNodeUVMap', uv_map='UVMap').outputs[0])
    u, v = sp[0], sp[1]
    edge = t.math('MAXIMUM', t.math('SUBTRACT', t.math('MULTIPLY', t.math('ABSOLUTE', t.math('SUBTRACT', v, 0.5)), 2.0), 0.85), 0.0)
    wear = t.math('MULTIPLY', edge, 6.0, True)
    stitch_band = t.math('LESS_THAN', t.math('ABSOLUTE', t.math('SUBTRACT', t.math('ABSOLUTE', t.math('SUBTRACT', v, 0.5)), 0.38)), 0.017)
    dash = t.math('GREATER_THAN', t.math('SINE', t.math('MULTIPLY', u, 2 * math.pi / 0.0018)), -0.5)
    stitch = t.math('MULTIPLY', stitch_band, dash)
    n1 = t.noise(300, 3, 0.6, ob)
    c = t.mix(n1, (0.055, 0.028, 0.014), (0.09, 0.048, 0.024))
    c = t.mix(wear, c, (0.20, 0.12, 0.07))
    c = t.mix(t.math('MULTIPLY', stitch, 0.75), c, (0.22, 0.14, 0.07))  # 황갈색 실
    t.link(c, t.p.inputs['Base Color'])
    bp = t.n('ShaderNodeBump')
    bp.inputs['Distance'].default_value = 0.0003
    t.link(t.math('ADD', vo.outputs['Distance'], t.math('MULTIPLY', stitch, 0.35)), bp.inputs['Height'])
    t.link(bp.outputs['Normal'], t.p.inputs['Normal'])
    t.link(t.math('ADD', 0.42, t.math('MULTIPLY', wear, 0.25)), t.p.inputs['Roughness'])

    hands_m = k3d.mat(f'M_{A}_WatchHandsSrc', (0.75, 0.74, 0.70), 0.12, 1.0)
    dial_m = k3d.mat(f'M_{A}_WatchDial', (1, 1, 1), 0.45)
    t = NT(dial_m)
    di = t.n('ShaderNodeTexImage', image=k3d.load_image(os.path.join(WORK, 'dial.png'), name=f'T_{A}_WatchDial_BaseColor'))
    t.link(di.outputs[0], t.p.inputs['Base Color'])
    glass = k3d.flag(k3d.mat(f'M_Glass_{A}_Crystal', (0.92, 0.94, 0.96), 0.05, alpha=0.14), transparent=True)

    # 줄: 손목 둘레 타원 고리 (사각 단면, 너비 18mm 두께 2.6mm)
    NA = 96
    rx, rz = hx + 0.0012, hz + 0.0012
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    ring = []
    circ = 0
    prev = None
    for i in range(NA + 1):
        tt = i / NA * 2 * math.pi
        p = Vector((cxw + math.cos(tt) * rx, 0, czw + math.sin(tt) * rz))
        if prev:
            circ += (p - prev).length
        prev = p
        nrm = Vector((math.cos(tt) / rx, 0, math.sin(tt) / rz)).normalized()
        q = []
        for dyy, dn in ((-0.0088, 0), (0.0088, 0), (0.0088, 0.0026), (-0.0088, 0.0026)):
            q.append(bm.verts.new((p.x + nrm.x * dn, Y_WATCH + dyy, p.z + nrm.z * dn)))
        ring.append((q, circ))
    for i in range(NA):
        (a, ua), (b2, ub) = ring[i], ring[i + 1]
        for k in range(4):
            f = bm.faces.new([a[k], a[(k + 1) % 4], b2[(k + 1) % 4], b2[k]])
            for l, (uu, vq) in zip(f.loops, ((ua, k / 4), (ua, (k + 1) / 4), (ub, (k + 1) / 4), (ub, k / 4))):
                l[uvl].uv = (uu, vq)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    st = obj_from_bm(bm, A + '_WStrap', leather)
    bv = st.modifiers.new('bev', 'BEVEL')
    bv.width, bv.segments, bv.limit_method = 0.0007, 2, 'ANGLE'
    # 줄 UV: u = 둘레 길이(m), v = 너비 0..1 (윗면 기준)
    me_ = st.data
    uvd = me_.uv_layers[0]
    for poly in me_.polygons:
        for li in poly.loop_indices:
            co = me_.vertices[me_.loops[li].vertex_index].co
            ang = math.atan2((co.z - czw) / rz, (co.x - cxw) / rx) % (2 * math.pi)
            uvd.data[li].uv = (ang / (2 * math.pi) * circ, (co.y - Y_WATCH + 0.0088) / 0.0176)
    # 케이스 (회전체): 반지름 17mm, 높이 8.5mm
    base_z = top + 0.0012  # 케이스 뒷면이 손목에 가깝게 (줄은 케이스 속을 지나 러그 사이로 나온다)
    prof = [(0.0, 0.0), (0.0150, 0.0), (0.0164, 0.0006), (0.0170, 0.0030), (0.0168, 0.0056), (0.0160, 0.0068),
            (0.0156, 0.0072), (0.0152, 0.0078), (0.0146, 0.0080), (0.0142, 0.0077), (0.0140, 0.0062)]
    bm = bmesh.new()
    NS = 72
    rings = []
    for i in range(NS):
        tt = i / NS * 2 * math.pi
        rings.append([bm.verts.new((math.cos(tt) * r, math.sin(tt) * r, z)) for r, z in prof])
    for i in range(NS):
        a, b2 = rings[i], rings[(i + 1) % NS]
        for k in range(len(prof) - 1):
            vs = [a[k], a[k + 1], b2[k + 1], b2[k]]
            if len(set(vs)) == 4:
                bm.faces.new(vs)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    case = obj_from_bm(bm, A + '_WCase', steel)
    # 러그 4개 (줄 방향 = 12-6 축 = X): 케이스 옆면에서 나와 손목 쪽으로 휘며 가늘어지는 판(끝 두께 ~2mm)
    # 스프링바는 줄 두께 중심을 지나므로 줄 끝이 바를 감싼 모양이 된다
    xb = 0.0195
    zb = czw + rz * math.sqrt(max(0.0, 1 - (xb / rx) ** 2)) + 0.0013 - base_z
    print('watch lug bar z (case local)', round(zb, 4))
    for sx in (1, -1):
        for sy in (1, -1):
            bm = bmesh.new()
            secs = []
            for k in range(9):
                tk = k / 8
                x_ = 0.0125 + tk * (xb + 0.0017 - 0.0125)
                tz = min(1.0, (x_ - 0.0125) / (xb - 0.0125)) ** 1.5  # 스프링바 위치에서 끝 높이 도달 (바가 러그 속에 묻힘)
                zt_ = 0.0058 + (zb + 0.0012 - 0.0058) * tz
                zb_ = 0.0016 + (zb - 0.0010 - 0.0016) * tz
                y0_, y1_ = 0.0090, 0.0113 - 0.0004 * tk
                secs.append([bm.verts.new((sx * x_, sy * yy, zz)) for yy, zz in ((y0_, zt_), (y1_, zt_), (y1_, zb_), (y0_, zb_))])
            for k in range(8):
                for e in range(4):
                    bm.faces.new([secs[k][e], secs[k][(e + 1) % 4], secs[k + 1][(e + 1) % 4], secs[k + 1][e]])
            bm.faces.new(secs[0])
            bm.faces.new(secs[-1][::-1])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            lo = obj_from_bm(bm, A + f'_WLug{sx}{sy}', steel)
            b_ = lo.modifiers.new('bev', 'BEVEL')
            b_.width, b_.segments, b_.limit_method = 0.0004, 2, 'ANGLE'
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0007, depth=0.0192, location=(sx * xb, 0, zb),
                                            rotation=(math.pi / 2, 0, 0))
        bar = bpy.context.active_object
        bar.name = A + f'_WLugBar{sx}'
        bar.data.materials.append(steel)
        for p_ in bar.data.polygons:
            p_.use_smooth = True
        parts.append(bar)
    # 용두 (3시 = 손가락 쪽 -Y)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0026, depth=0.0028, location=(0, -0.0182, 0.0034),
                                        rotation=(math.pi / 2, 0, 0))
    cr = bpy.context.active_object
    cr.name = A + '_WCrown'
    cr.data.materials.append(steel)
    b_ = cr.modifiers.new('bev', 'BEVEL')
    b_.width, b_.segments = 0.0004, 2
    parts.append(cr)
    # 문자판 (UV: 12시 = +X, 3시 = -Y)
    R_d = 0.0141
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    ctr = bm.verts.new((0, 0, 0.0063))
    rim = [bm.verts.new((math.cos(i / 64 * 2 * math.pi) * R_d, math.sin(i / 64 * 2 * math.pi) * R_d, 0.0063)) for i in range(64)]
    for i in range(64):
        f = bm.faces.new([ctr, rim[i], rim[(i + 1) % 64]])
        for l in f.loops:
            co = l.vert.co
            l[uvl].uv = (0.5 + (-co.y) / (2 * R_d), 0.5 + co.x / (2 * R_d))
    dial = obj_from_bm(bm, A + '_WDial', dial_m)
    # 바늘 10:08:35
    e12, e3 = Vector((1, 0, 0)), Vector((0, -1, 0))
    for ang, ln, w, z in ((304.0, 0.0085, 0.0011, 0.0064), (51.5, 0.0123, 0.0008, 0.00655), (210.0, 0.0128, 0.00022, 0.0067)):
        th_ = math.radians(ang)
        d = e12 * math.cos(th_) + e3 * math.sin(th_)
        sd = d.cross(Vector((0, 0, 1)))
        bm = bmesh.new()
        pts = [-d * 0.0025 + sd * w * 0.4, d * ln * 0.25 + sd * w, d * ln, d * ln * 0.25 - sd * w, -d * 0.0025 - sd * w * 0.4]
        vb = [bm.verts.new((p.x, p.y, z)) for p in pts]
        f = bm.faces.new(vb)
        ret = bmesh.ops.extrude_face_region(bm, geom=[f])
        for vtx in [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]:
            vtx.co.z += 0.00022
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj_from_bm(bm, A + f'_WHand{int(ang)}', hands_m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0007, depth=0.0008, location=(0, 0, 0.0068))
    pin = bpy.context.active_object
    pin.data.materials.append(hands_m)
    parts.append(pin)
    # 유리 (돔)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=16, radius=0.045, location=(0, 0, 0.0086 - 0.045))
    gl = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(gl.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.045 - 0.0016 - 1e-5], context='VERTS')
    bm.to_mesh(gl.data); bm.free()
    for vtx in gl.data.vertices:  # 반지름 14.4mm 로 맞춤
        rr = math.hypot(vtx.co.x, vtx.co.y)
        if rr > 1e-6:
            s_ = 0.0144 / 0.0119
            vtx.co.x *= s_; vtx.co.y *= s_
    gl.data.materials.append(glass)
    for p in gl.data.polygons:
        p.use_smooth = True
    gl.name = gl.data.name = A + '_Crystal'
    # 케이스를 손목 위로 (줄 윗면 중앙)
    for o in [case, dial, cr, pin] + [p for p in parts if '_WLug' in p.name or '_WHand' in p.name] + [gl]:
        o.location = (o.location.x + cxw, o.location.y + Y_WATCH, o.location.z + base_z)
    body = k3d.join([p for p in parts if p != dial], A + '_Watch')
    body = k3d.join([body, dial], A + '_Watch')
    skin_to(body)
    k3d.apply_all(gl)
    skin_to(gl)
    return body, gl, Vector((cxw, Y_WATCH, base_z + 0.0063))


watch_o = None
if SIDE == 'L' and not FAST:
    watch_o, crystal, watch_c = watch()

# ------------------------------------------------------------------ 굽기 (휴식 자세). K3D_FAST 는 절차 머티리얼 그대로 미리보기만
if not FAST:
    ad.pose_position = 'REST'
    k3d.bake(skin, BAKE, keep=(hid_m.name,), samples=24)
    if watch_o:
        k3d.bake(watch_o, 1024, keep=(f'M_{A}_WatchDial',), samples=24)
    ad.pose_position = 'POSE'

# ------------------------------------------------------------------ 포즈: 곧게 편 손가락 = 0 기준 굽힘(rad) [MCP, PIP, DIP, (벌림 +엄지쪽)],
# 엄지 [손허리 굽힘, 벌림, 비틀림, 근위 굽힘, 원위 굽힘] (손허리는 MH 휴식 자세 기준)
POSES = {
    'Idle': {'index': [.22, .3, .18, .05], 'middle': [.3, .4, .22, 0], 'ring': [.38, .48, .26, -.05],
             'pinky': [.46, .55, .3, -.1], 'thumb': [.05, .05, 0, .15, .2]},
    # 키오스크 누르기: 검지만 곧게, 나머지는 말아 쥐고 엄지는 중지 중간마디 위
    'Point': {'index': [.16, 0, -.04, -.3], 'middle': [1.5, 1.7, 1.0, -.05], 'ring': [1.55, 1.7, 1.0, -.08],
              'pinky': [1.6, 1.65, .95, -.1], 'thumb': [.55, -.1, .45, .5, .35]},
    'HoldMemo': {'index': [.8, .75, .38], 'middle': [.85, .8, .42], 'ring': [.92, .85, .45], 'pinky': [1.0, .9, .48],
                 'thumb': [.4, 0, .3, .2, .25]},
    'GripMagnifier': {'index': [1.15, 1.45, .9], 'middle': [1.25, 1.5, .95], 'ring': [1.3, 1.55, .95],
                      'pinky': [1.35, 1.5, .9], 'thumb': [.55, -.05, .45, .45, .4]},
    'HoldCard': {'index': [.75, .7, .35], 'middle': [1.0, 1.1, .6], 'ring': [1.15, 1.25, .7], 'pinky': [1.25, 1.3, .72],
                 'thumb': [.4, 0, .3, .2, .25]},
    'Fist': {'index': [1.55, 1.8, 1.2], 'middle': [1.6, 1.85, 1.2], 'ring': [1.65, 1.85, 1.15], 'pinky': [1.7, 1.8, 1.1],
             'thumb': [.8, -.1, .5, .8, .6]},
    # 지팡이 손잡이: 손바닥을 가로지르는 파워 그립
    'GripCane': {'index': [1.0, 1.35, .8], 'middle': [1.1, 1.4, .85], 'ring': [1.2, 1.45, .85], 'pinky': [1.3, 1.45, .85],
                 'thumb': [.5, -.05, .4, .45, .45]},
}
# MH 휴식 자세의 굽힘·벌림 (부모 본 기준). 포즈 값에서 빼서 '곧게 편 손가락 = 0' 이 되게 한다
REST = {}
for b in ad.bones:
    if b.parent and b.parent.name not in ('forearm', 'wrist'):
        d = b.parent.matrix_local.to_3x3().inverted() @ b.matrix_local.col[1].xyz
        REST[b.name] = (math.atan2(-d.z, d.y), math.atan2(d.x, d.y))
print('rest flex/spread', {k: (round(v[0], 2), round(v[1], 2)) for k, v in REST.items() if 'tip' not in k})


def q_of(flex, n=0.0, s=0.0, rest=(0.0, 0.0)):
    return Quaternion((0, 0, 1), n * MIR + rest[1]) @ Quaternion((1, 0, 0), rest[0] - flex) @ Quaternion((0, 1, 0), -s * MIR)


def apply_pose(ps):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for f in FING:
        v = ps[f]
        c = chain(f)
        for k in range(3):
            arm.pose.bones[c[k + 1]].rotation_quaternion = q_of(v[k], v[3] if k == 0 and len(v) > 3 else 0, 0, REST[c[k + 1]])
    t = ps['thumb']
    arm.pose.bones['thumb-metacarpal'].rotation_quaternion = q_of(t[0], t[1], t[2])
    arm.pose.bones['thumb-phalanx-proximal'].rotation_quaternion = q_of(t[3], 0, 0, REST['thumb-phalanx-proximal'])
    arm.pose.bones['thumb-phalanx-distal'].rotation_quaternion = q_of(t[4], 0, 0, REST['thumb-phalanx-distal'])
    bpy.context.view_layer.update()


def bone_head(n, tail=False):
    pb = arm.pose.bones[n]
    return arm.matrix_world @ (pb.tail if tail else pb.head)


def bone_pad(n, d=0.005):
    pb = arm.pose.bones[n]
    return arm.matrix_world @ (pb.head - pb.matrix.to_3x3() @ Vector((0, 0, 1)) * d)


def checks(nm):
    """숫자 확인: Point 검지 꺾임 < 10°, 집기 패드 간격 ~1cm, 주먹 손끝-손바닥 < ~2.5cm."""
    out = {}
    palm = sum((bone_head(f'{f}-finger-metacarpal') + bone_head(f'{f}-finger-metacarpal', True) for f in FING), Vector()) / 8
    palm -= Vector((0, 0, 0.013))
    if nm == 'Point':
        a = bone_head('index-finger-metacarpal', True) - bone_head('index-finger-metacarpal')
        b = bone_head('index-finger-phalanx-distal', True) - bone_head('index-finger-phalanx-distal')
        out['index_bend_deg'] = round(math.degrees(a.angle(b)), 1)
        out['index_aim_deg'] = round(math.degrees(b.angle(Vector((0, -1, 0)))), 1)  # 손 축(-Y)과 검지 방향
        out['thumb_to_middle_pip_cm'] = round((bone_head('thumb-tip') - bone_head('middle-finger-phalanx-intermediate')).length * 100, 1)
    if nm in ('HoldCard', 'HoldMemo'):
        out['pinch_cm'] = round((bone_pad('thumb-tip', 0.004) - bone_pad('index-finger-tip', 0.004)).length * 100, 1)
    out['tips_to_palm_cm'] = [round((bone_head(chain(f)[-1]) - palm).length * 100, 1) for f in FING + ['thumb']]
    print('CHECK', nm, out)


arm.animation_data_create()
acts = {}
sock_pts = {}
for nm, ps in POSES.items():
    act = bpy.data.actions.new(f'{A}_{nm}')
    act.use_fake_user = True
    arm.animation_data.action = act
    apply_pose(ps)
    checks(nm)
    for fr in (1, 30):
        for pb in arm.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=fr, group=pb.name)
    acts[nm] = act
    if nm == 'HoldCard':
        sock_pts['Pinch'] = (bone_pad('thumb-tip', 0.004) + bone_pad('index-finger-tip', 0.004)) / 2
    if nm == 'HoldMemo':
        sock_pts['Memo'] = (bone_pad('thumb-tip', 0.004) + bone_pad('index-finger-tip', 0.004)) / 2
    if nm in ('GripMagnifier', 'GripCane'):  # 쥔 손가락 안쪽 = 손잡이 중심
        sock_pts['Grip' if nm == 'GripMagnifier' else 'Cane'] = (
            bone_head('middle-finger-phalanx-proximal') * 0.5 + bone_head('middle-finger-phalanx-intermediate') * 0.5
            - Vector((0, 0, 0.017)))
arm.animation_data.action = acts['Idle']
apply_pose(POSES['Idle'])


def socket(name, loc, bone, rot=None):
    e = bpy.data.objects.new(f'{A}_Socket_{name}', None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', 0.02
    bpy.context.scene.collection.objects.link(e)
    e.parent = arm
    e.parent_type = 'BONE'
    e.parent_bone = bone
    bpy.context.view_layer.update()
    e.matrix_world = Matrix.Translation(loc) @ (rot or Matrix.Identity(4))
    return e


socks = [socket('Grip', sock_pts['Grip'], 'wrist', Matrix.Rotation(math.pi / 2, 4, 'Y')),
         socket('Pinch', sock_pts['Pinch'], 'wrist'),
         socket('Cane', sock_pts['Cane'], 'wrist', Matrix.Rotation(math.pi / 2, 4, 'Y'))]
apply_pose({f: [0, 0, 0] for f in FING} | {'thumb': [0] * 5})
socks.append(socket('Tip', bone_pad('index-finger-tip', 0.0045), 'index-finger-tip'))
if SIDE == 'L':
    socks.append(socket('Memo', sock_pts['Memo'], 'wrist'))
if watch_o:
    socks.append(socket('Watch', watch_c, 'forearm'))
arm.animation_data.action = acts['Idle']
bpy.context.scene.frame_set(1)
for e in socks:
    print('socket', e.name, tuple(round(x, 4) for x in e.matrix_world.translation))

# ------------------------------------------------------------------ 내보내기
notes = {
    'origin': '손목 관절(wrist 본 머리) = 원점. 1인칭 손 리그라 바닥 중앙 규칙의 예외. 손가락 = Unity +Z, 손등 = +Y.',
    'rig': f'{A}_Rig: forearm(루트, 팔뚝·소매·시계) > wrist > WebXR 25관절 이름 그대로 (예: index-finger-phalanx-proximal). '
           '굽힘 = 각 본 로컬 X 축 회전, 벌림 = 로컬 Z. 메시·가중치 = MakeHuman hm08 기본 메시 + 기본 리그 가중치 (CC0).',
    # Blender FBX take 이름 = '<아마추어>|<액션>' (Unity 기본 클립 이름도 이것). 1~30프레임 정지 포즈, loop 는 Unity 에서 켤 것
    'clips': {a.name.replace(A + '_', ''): f'{A}_Rig|{a.name}' for a in acts.values()},
    'sockets': {e.name: f'parent bone {e.parent_bone}' for e in socks},
    'socket_notes': 'Grip: GripMagnifier 자세의 돋보기 손잡이 중심 (로컬 Z = 손잡이 축 = 가로). Cane: GripCane 자세의 지팡이 손잡이 중심 '
                    '(로컬 Z = 손잡이 축). Pinch: HoldCard 자세에서 엄지·검지 패드 사이. Tip: 검지 끝 패드 (키오스크 터치 판정). '
                    'Memo(L): HoldMemo 자세 집는 점. Watch(L): 시계 문자판 중심 (볼 때 시선 대상).',
    'materials': '피부 2048 아틀라스(손톱 포함), 소매 = M_Tile_Hands_Rib/Knit (원통 UV, 4cm 반복), 소매 속 팔뚝 = 단색.',
}
if SIDE == 'L':
    notes['watch'] = '왼 손목 아날로그 시계 (가상 브랜드 ARIRANG, 10:08, 요일창 토 15). 문자판은 M_GrandpaHand_L_WatchDial 1024 단독 텍스처, 유리 M_Glass.'
fbx = None
if not FAST:
    fbx = k3d.export(A, 'Hands', [arm], rigged=True, anim=True, notes=notes)
    # ------------------------------------------------------------------ 미리보기 (턴테이블)
    k3d.preview(A, [skin], views=((35, 25), (215, 20), (90, 60)), ground=False, res=(1400, 1050))
    for nm in ('Point', 'Fist', 'HoldCard', 'GripMagnifier', 'GripCane'):
        arm.animation_data.action = acts[nm]
        bpy.context.scene.frame_set(1)
        k3d.preview(A, [skin], views=((25, 30), (110, 15)), ground=False, tag=nm.lower(), res=(1200, 900))
arm.animation_data.action = acts['Idle']
bpy.context.scene.frame_set(1)


def fp_shot(tag, cam_loc, look, lens=30):
    """눈높이 1.55m 시점 근사: 손을 몸 앞 40cm·눈 아래 35cm 에 든 모습."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = (960, 720) if FAST else (1600, 1200)
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('fp'); sc.world = w
    if w.node_tree is None:
        w.use_nodes = True
    wn = w.node_tree.nodes
    bg = next((n for n in wn if n.type == 'BACKGROUND'), None)
    if bg is None:
        bg = wn.new('ShaderNodeBackground')
        wo = next((n for n in wn if n.type == 'OUTPUT_WORLD'), None) or wn.new('ShaderNodeOutputWorld')
        w.node_tree.links.new(bg.outputs[0], wo.inputs['Surface'])
    bg.inputs['Color'].default_value = (0.55, 0.52, 0.48, 1); bg.inputs['Strength'].default_value = 0.6
    tmp = []
    for kind, en, loc in (('SUN', 2.2, (0.4, -0.6, 1.2)), ('AREA', 6.0, (-0.4, 0.2, 0.5))):
        ld = bpy.data.lights.new('fpl', kind); ld.energy = en
        if kind == 'AREA':
            ld.size = 0.6
        lo = bpy.data.objects.new('fpl', ld); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, -0.08, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); tmp.append(lo)
    cd = bpy.data.cameras.new('fpc'); cd.lens = lens; cd.clip_start = 0.05  # 게임 카메라 near 0.05
    cam = bpy.data.objects.new('fpc', cd); sc.collection.objects.link(cam); tmp.append(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(look) - Vector(cam_loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(k3d.SRC, 'Previews', f'{A}_{tag}_0.png')
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)


def prop(kind):
    """미리보기 전용 소품 (내보낸 뒤라 FBX 에 안 들어감): grip = 돋보기 손잡이 원통(소켓 로컬 Z), card = 카드(엄지->검지 패드 법선)."""
    if kind == 'grip':
        M = bpy.data.objects[f'{A}_Socket_Grip'].matrix_world
        bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=0.12, location=M.translation, rotation=M.to_euler())
        m = k3d.mat('M_PropPreview', (0.05, 0.04, 0.035), 0.4)
    else:
        n = (bone_pad('index-finger-tip', 0.004) - bone_pad('thumb-tip', 0.004)).normalized()
        u = Vector((0, -1, 0)); u = (u - n * u.dot(n)).normalized()
        R = Matrix((u.cross(n), u, n)).transposed()
        bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects[f'{A}_Socket_Pinch'].matrix_world.translation + u * 0.03,
                                        rotation=R.to_euler(), scale=(0.054, 0.086, 0.0008))
        m = k3d.mat('M_PropPreviewCard', (0.75, 0.75, 0.72), 0.3)
    o = bpy.context.active_object
    o.data.materials.append(m)
    return o


def fp(tag, pose, dirv, dist=0.46, lens=32, props=()):
    """1인칭 근사: 눈 = 손 중심에서 dirv(R 기준, 손 좌표) 쪽 dist. 시선을 3.5cm 위로 -> 손이 화면 중앙 약간 아래."""
    arm.animation_data.action = acts[pose]
    bpy.context.scene.frame_set(1)
    ps = [prop(k) for k in props]
    tgt = Vector((0, -0.075, 0))
    fp_shot(tag, tgt + Vector((dirv[0] * MIR, dirv[1], dirv[2])).normalized() * dist, tgt + Vector((0, 0, 0.035)), lens)
    for o in ps:
        bpy.data.objects.remove(o, do_unlink=True)


# 팔뚝이 +Y 로 뻗으므로 눈은 팔꿈치 쪽 위, 몸 중심 쪽(엄지 쪽)
fp('fp', 'Idle', (0.45, 0.6, 0.62))
fp('fpgrip', 'GripMagnifier', (0.45, 0.6, 0.62), props=('grip',))
fp('fpcard', 'HoldCard', (0.55, 0.45, 0.62), props=('card',))
fp('fppoint', 'Point', (0.75, 0.22, 0.62), dist=0.55)  # 옆에서: 시선과 검지 사이 ~75°
fp('fppoint2', 'Point', (0.4, 0.62, 0.62))  # 어깨 너머 1인칭
if SIDE == 'L':
    fp('fpmemo', 'HoldMemo', (0.45, 0.6, 0.62))
arm.animation_data.action = acts['Point']
bpy.context.scene.frame_set(1)
# 팔을 들어 키오스크를 누를 때: 카메라가 팔뚝 축에 가깝고 광각 -> 소매 뒤끝이 화면에 들어오지 않는지 확인
fp_shot('fpraise', (0.12 * MIR, 0.40, 0.17), (0.0, -0.08, 0.0), lens=22)
if watch_o:  # 시계 근접 (러그·스프링바·스티치 확인)
    for k, off in enumerate(((0.0, 0.01, 0.13), (0.085, 0.03, 0.055), (-0.02, -0.09, 0.05))):
        fp_shot(f'watch{k}', watch_c + Vector(off), watch_c, lens=60)
# 엄지 손톱 근접 (HoldCard, 엄지 쪽)
arm.animation_data.action = acts['HoldCard']
bpy.context.scene.frame_set(1)
pb_ = arm.pose.bones['thumb-phalanx-distal']
tip_ = arm.matrix_world @ pb_.tail
n_, a_ = (pb_.matrix.to_3x3() @ Vector((0, 0, 1))).normalized(), (pb_.matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
fp_shot('thumbnail', tip_ + n_ * 0.09 + a_ * 0.04, tip_ - a_ * 0.008, lens=70)  # 손톱 정면 (손등 쪽)
if not FAST:
    fp_shot('thumbside', tip_ + (n_ * 0.5 + a_.cross(n_) * 0.8 + a_ * 0.4).normalized() * 0.1, tip_ - a_ * 0.008, lens=70)
print('DONE', fbx)

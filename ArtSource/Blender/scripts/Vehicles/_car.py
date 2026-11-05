"""승용차 공용 생성기. CarSedan.py / CarHatch.py 가 설정 dict(C) 로 build(C) 를 부른다.
차체 = 매개 곡면 (길이 t 프로파일 × 단면 7점 PCHIP) + 휠아치(단면 바닥을 원호로 올림) + 창 인셋(pgrid region).
램프·그릴·거울·와이퍼는 별도 메시로 붙여 차체와 함께 한 번에 굽는다. 바퀴 4개는 차축 원점 자식."""
import math, os, json, copy
from functools import lru_cache
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import _vlib as V

k3d = V.k3d
KN = (0.0, 0.10, 0.15, 0.40, 0.52, 0.74, 1.0)  # 단면 v: 바닥중앙·바닥끝·록커·숄더·벨트·루프레일·지붕중앙
FAST = bool(os.environ.get("CAR_FAST"))  # 굽기 생략 (형태 확인용)
E = 3.0  # 굽는 발광 세기 (하나만 쓰이므로 색 밝기로 조절)


# ---------------------------------------------------------------- 메시 도우미
def beam(name, p0, p1, w, h, mat, up=(0, 0, 1)):
    """p0->p1 직육면체 (단면 w x h, h 방향 = up)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    s = d.cross(Vector(up))
    if s.length < 1e-6:
        s = d.cross(Vector((1, 0, 0)))
    s.normalize()
    u = s.cross(d).normalized()
    bm = bmesh.new()
    vs = [bm.verts.new(p + s * a * w / 2 + u * b * h / 2) for p in (p0, p1)
          for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return V.mesh_obj(name, bm, [mat])


def gbox(name, size, loc, mat, cuts=6, bev=0.005, rot=(0, 0, 0)):
    """x 방향으로 잘게 나눈 상자 (곡면에 맞춰 휠 수 있게)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    xe = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 1e-6]
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=xe, cuts=cuts, use_grid_fill=True)
    o = V.mesh_obj(name, bm, [mat])
    o.location, o.rotation_euler = loc, rot
    if bev:
        V.bevel_mod(o, bev, 2, angle=40)
    return o


def conform(o, f):
    """월드 기준으로 정점 y 를 f(x, z) 만큼 옮긴다 (앞·뒷면 곡률 따라가기)."""
    V.apply_tf(o)
    for v in o.data.vertices:
        v.co.y += f(v.co.x, v.co.z)
    return o


# ---------------------------------------------------------------- 머티리얼
def m_gloss_black(name, rough=0.1):
    g = V.NB(name)
    sm = g.maprange(g.noise(7, 4, 0.6), 0.45, 0.75, 0, 1)
    return g.out((0.008, 0.008, 0.009), g.add(rough, g.mul(sm, 0.25)), 0.0, g.bump(g.noise(400, 2, 0.5), 0.05, 0.001))


def m_emit(name, color, emis, rough=0.2):
    g = V.NB(name)
    return g.out(color, rough, 0.0, None, emis, E)


def m_honeycomb(name, scale=55, frame=(0.03, 0.03, 0.032)):
    """그릴 벌집 망: 칸은 깊고 어둡게, 살은 반무광."""
    g = V.NB(name)
    x, y, z = g.xyz()
    n = g.n('ShaderNodeCombineXYZ')
    g.link(x, n.inputs[0])
    g.link(z, n.inputs[1])
    e = g.voronoi(scale, n.outputs[0], feature='DISTANCE_TO_EDGE')
    rib = g.maprange(e, 0.04, 0.09, 1, 0)
    col = g.mix(rib, (0.002, 0.002, 0.002), frame)
    return g.out(col, g.mixf(rib, 0.8, 0.35), 0.0, g.bump(rib, 0.8, 0.004))


def m_tail(name):
    """미등 렌즈: 붉은 렌즈 안 격자 반사 + 아주 약한 발광 (낮에 브레이크 밟은 것처럼 보이지 않게 DRL 의 약 1/3)."""
    g = V.NB(name)
    x, y, z = g.xyz()
    ribs = g.maprange(g.absf(g.sub(g.math('FRACT', g.mul(x, 60)), 0.5)), 0.3, 0.5, 0, 1)
    col = g.mix(ribs, (0.30, 0.008, 0.01), (0.55, 0.03, 0.03))
    return g.out(col, 0.12, 0.0, g.bump(ribs, 0.3, 0.002), g.mix(ribs, (0.04, 0.0, 0.0), (0.085, 0.003, 0.003)), E)


def m_fabric(name, color=(0.028, 0.028, 0.03)):
    g = V.NB(name)
    c = g.mix(g.mul(g.noise(30, 3, 0.6), 0.5), color, [k * 1.6 for k in color])
    return g.out(c, 0.92, 0.0, g.bump(g.noise(700, 2, 0.6), 0.3, 0.001))


def m_tire(name, R, hw, ring_img):
    """타이어: 트레드 홈(원주 홈 + 가로 사이프) + 옆면 글자(양각 이미지) + 먼지."""
    g = V.NB(name)
    x, y, z = g.xyz()
    r = g.n('ShaderNodeVectorMath', operation='LENGTH')
    cmb = g.n('ShaderNodeCombineXYZ')
    g.link(y, cmb.inputs[1])
    g.link(z, cmb.inputs[2])
    g.link(cmb.outputs[0], r.inputs[0])
    rad = r.outputs['Value']
    tread = g.maprange(rad, R - 0.018, R - 0.008, 0, 1)
    ax = g.absf(x)
    grooves = g.maxf(g.line(ax, hw * 0.22, 0.007), g.line(ax, hw * 0.62, 0.006))
    ang = g.math('ARCTAN2', z, y)
    sip = g.line(g.math('FRACT', g.mul(ang, 64 / (2 * math.pi))), 0.5, 0.07)
    sip = g.mul(sip, g.maprange(ax, hw * 0.25, hw * 0.3, 0, 1))
    hole = g.mul(tread, g.maxf(grooves, sip))
    # 옆면 글자 (바깥쪽 +x 만)
    mp = g.n('ShaderNodeMapping')
    g.link(g.obj(), mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (0, 1 / (2 * R), 1 / (2 * R))
    mp.inputs['Location'].default_value = (0, 0.5, 0.5)
    sw = g.n('ShaderNodeSeparateXYZ')
    g.link(mp.outputs[0], sw.inputs[0])
    uvv = g.n('ShaderNodeCombineXYZ')
    g.link(sw.outputs['Y'], uvv.inputs[0])
    g.link(sw.outputs['Z'], uvv.inputs[1])
    letters = g.image(ring_img, uvv.outputs[0], non_color=True)
    side = g.maprange(x, hw * 0.55, hw * 0.75, 0, 1)
    let = g.mul(g.mul(letters, side), g.sub(1, tread))
    dust = g.mul(g.maprange(g.noise(6, 5, 0.6), 0.35, 0.75, 0, 1), 0.6)
    col = g.mix(dust, (0.018, 0.018, 0.019), (0.075, 0.068, 0.058))
    col = g.mix(g.mul(hole, 0.8), col, (0.006, 0.006, 0.006))
    col = g.mix(g.mul(let, 0.35), col, (0.05, 0.05, 0.05))
    h = g.sub(g.add(g.mul(let, 0.6), g.mul(g.noise(600, 2, 0.5), 0.05)), g.mul(hole, 1.0))
    return g.out(col, g.add(0.8, g.mul(let, -0.25)), 0.0, g.bump(h, 0.6, 0.004))


def m_alloy(name, color=(0.55, 0.56, 0.58)):
    """알로이 휠: 은색 도장 금속 + 브레이크 분진(틈새·안쪽)."""
    g = V.NB(name)
    x, y, z = g.xyz()
    dust = g.add(g.mul(g.maprange(g.ao(0.05), 1.0, 0.5, 0, 1), 0.8), g.maprange(x, 0.02, -0.04, 0, 0.7))
    dust = g.minf(g.mul(dust, g.maprange(g.noise(25, 4, 0.6), 0.2, 0.8, 0.6, 1.0)), 1.0)
    col = g.mix(dust, color, (0.07, 0.055, 0.04))
    return g.out(col, g.add(0.25, g.mul(dust, 0.5)), g.mixf(dust, 1.0, 0.3), g.bump(g.noise(300, 2, 0.5), 0.05, 0.001))


# ---------------------------------------------------------------- 차체 곡면
class Body:
    def __init__(s, C):
        s.C = C
        s.L = C["L"]
        s.f = {k: V.pchip(C[k]) for k in ("top", "belt", "bot", "half", "sh")}
        s.uc = 0.035
        s.rr = C.get("round", (0.07, 0.06))
        s.crown = C.get("crown", 0.03)
        s.sec = lru_cache(maxsize=None)(s._sec)

    def zbot(s, t):
        C = s.C
        z = s.f["bot"](t)
        for ta in C["axles"]:
            d = abs(t - ta)
            if d < C["arch_r"]:
                z = max(z, C["tire_r"] + C.get("arch_dz", 0.0) + math.sqrt(C["arch_r"] ** 2 - d * d))
        return z

    def ctrl(s, t):
        f = s.f
        w, zt, zb = f["half"](t), f["top"](t), s.zbot(t)
        zs = max(f["sh"](t), zb + 0.08)
        zrail = zt - s.crown
        zbl = f["belt"](t)
        gh = max(0.0, zrail - zbl)
        g = V.smooth01(gh / 0.10)
        xb = w - s.C.get("belt_in", 0.035)
        b4 = (xb, min(zbl, zrail))
        hood = (xb - 0.09, zrail + 0.006)
        gre = (xb - s.C.get("lean", 0.40) * gh, zrail)
        b5 = (hood[0] + (gre[0] - hood[0]) * g, hood[1] + (gre[1] - hood[1]) * g)
        return [(0.0, zb), (w - 0.13, zb), (w - 0.02, zb + 0.045), (w, zs), b4, b5, (0.0, zt)]

    def _sec(s, t):
        p = s.ctrl(t)
        fx = V.pchip([(KN[i], p[i][0]) for i in range(7)])
        fz = V.pchip([(KN[i], p[i][1]) for i in range(7)])
        cz = 0.5 * (p[0][1] + p[6][1])
        ins = 0.0
        a, b = s.rr
        if t < a:
            d = a - t
            ins = a - math.sqrt(max(a * a - d * d, 0.0))
        if t > s.L - b:
            d = t - (s.L - b)
            ins = b - math.sqrt(max(b * b - d * d, 0.0))
        return fx, fz, cz, ins

    def yoff(s, t, x, z):
        C, L = s.C, s.L
        y = -L / 2 + t
        w = s.f["half"](t)
        xx = min(abs(x) / max(w, 1e-3), 1.0)
        ff = max(0.0, 1 - t / 0.45) ** 2
        fr = max(0.0, 1 - (L - t) / 0.45) ** 2
        if ff > 0:
            zb, zt = s.zbot(0), s.f["top"](0)
            zz = min(max((z - zb) / (zt - zb), 0.0), 1.0)
            y += (C["sweep"][0] * zz * zz - C["bulge"][0] * (1 - xx * xx)) * ff
        if fr > 0:
            zb, zt = s.zbot(L), s.f["top"](L)
            zz = min(max((z - zb) / (zt - zb), 0.0), 1.0)
            y -= (C["sweep"][1] * zz * zz - C["bulge"][1] * (1 - xx * xx)) * fr
        return y

    def t_of(s, u):
        return (u - s.uc) / (1 - 2 * s.uc) * s.L

    def u_of(s, t):
        return s.uc + (1 - 2 * s.uc) * t / s.L

    def xz(s, t, v, sc=1.0):
        fx, fz, cz, ins = s.sec(round(t, 6))
        x, z = fx(v), fz(v)
        if ins > 0 or sc < 1:
            dx, dz = x, z - cz
            l = math.hypot(dx, dz)
            k = (max(l - ins, 0.0) / l if l > 1e-9 else 0.0) * sc
            x, z = dx * k, cz + dz * k
        return x, z

    def S(s, u, v):
        if u <= s.uc:
            sc, t = u / s.uc, 0.0
        elif u >= 1 - s.uc:
            sc, t = (1 - u) / s.uc, s.L
        else:
            sc, t = 1.0, s.t_of(u)
        x, z = s.xz(t, v, sc)
        return (x, s.yoff(t, x, z), z)

    def side_x(s, t, z):
        """옆면에서 높이 z 의 x (숄더~벨트 구간 이분 탐색)."""
        lo, hi = KN[2], KN[4]
        for _ in range(30):
            m = (lo + hi) / 2
            if s.xz(t, m)[1] < z:
                lo = m
            else:
                hi = m
        return s.xz(t, lo)[0]

    def face_y(s, end, x, z):
        """앞(end=0)/뒤(end=1) 면의 y."""
        return s.yoff(0.0 if end == 0 else s.L, x, z)

    def top_z(s, t, v=1.0):
        return s.xz(t, v)[1]


# ---------------------------------------------------------------- 바퀴
def wheel(A, C, M):
    R, Rr, hw = C["tire_r"], C["rim_r"], C["tire_w"] / 2
    seg = 24
    tp = [(-hw * 0.80, Rr + 0.004), (-hw * 0.94, Rr + 0.03), (-hw, Rr + 0.45 * (R - Rr)), (-hw * 0.97, R - 0.026),
          (-hw * 0.86, R - 0.007), (-hw * 0.6, R), (0, R + 0.001), (hw * 0.6, R), (hw * 0.86, R - 0.007),
          (hw * 0.97, R - 0.026), (hw, Rr + 0.45 * (R - Rr)), (hw * 0.94, Rr + 0.03), (hw * 0.80, Rr + 0.004),
          (hw * 0.5, Rr - 0.002), (-hw * 0.5, Rr - 0.002), (-hw * 0.80, Rr + 0.004)]
    tire = V.lathe(A + "_tire", tp, seg, mats=[M["tire"]])
    rp = [(-hw * 0.78, Rr - 0.012), (-hw * 0.82, Rr + 0.006), (-hw * 0.70, Rr - 0.008), (hw * 0.55, Rr - 0.012),
          (hw * 0.78, Rr + 0.004), (hw * 0.86, Rr + 0.010), (hw * 0.90, Rr - 0.004), (hw * 0.80, Rr - 0.018),
          (hw * 0.62, Rr - 0.026)]
    rim = V.lathe(A + "_rim", rp, seg, mats=[M["alloy"]])
    hub = V.lathe(A + "_hub", [(hw * 0.10, Rr - 0.03), (hw * 0.30, 0.10), (hw * 0.42, 0.075), (hw * 0.44, 0.03),
                               (hw * 0.47, 0.0)], 24, mats=[M["alloy"]])
    disc = V.lathe(A + "_disc", [(-0.012, 0.09), (-0.012, Rr - 0.04), (0.012, Rr - 0.04), (0.012, 0.09),
                                 (-0.012, 0.09)], 32, mats=[M["steel"]])
    disc.location.x = -hw * 0.15
    parts = [tire, rim, hub, disc]
    n = C.get("spokes", 5)
    for k in range(n):
        for da in ((-0.07, 0.07) if C.get("double_spoke", True) else (0.0,)):
            a = 2 * math.pi * k / n + da
            ca, sa = math.cos(a), math.sin(a)
            p0 = (hw * 0.40, ca * 0.085, sa * 0.085)
            p1 = (hw * 0.78, ca * (Rr - 0.02), sa * (Rr - 0.02))
            parts.append(beam(A + "_sp", p0, p1, 0.026, 0.020, M["alloy"], up=(1, 0, 0)))
    for k in range(5):
        a = 2 * math.pi * (k + 0.5) / 5
        parts.append(V.cyl(A + "_nut", 0.009, 0.02, (hw * 0.45, math.cos(a) * 0.052, math.sin(a) * 0.052),
                           (0, math.pi / 2, 0), M["steel"], segs=6))
    parts.append(V.cyl(A + "_cap", 0.032, 0.012, (hw * 0.47, 0, 0), (0, math.pi / 2, 0), M["cap"], segs=20, bevel=0.003))
    w = V.join(parts, A)
    V.shade(w, 40)
    return w


# ---------------------------------------------------------------- 조립
def fix_emission():
    """k3d 우회: 발광 세기 0 인 재질의 기본 Emission Color(흰색)가 굽혀 전체가 빛나는 문제 -> 검정으로."""
    for m in bpy.data.materials:
        p = k3d.principled(m) if m.node_tree else None
        if p and p.inputs['Emission Strength'].default_value <= 0 and not p.inputs['Emission Color'].is_linked:
            p.inputs['Emission Color'].default_value = (0, 0, 0, 1)


def paint_variants(A, C, paint):
    """k3d 우회 (몽키패치): 차체 BaseColor 를 구운 직후 같은 UV 로 도장색만 바꾼 BaseColor 를 더 굽는다.
    -> Textures/<A>_Body/T_<A>_Body_BaseColor_<변형>.jpg. 머티리얼 항목은 export() 가 JSON 에 붙인다."""
    orig = k3d._bake_pass
    nodes = paint.node_tree.nodes

    def patched(obj, mats, image, kind, uv, margin, socket=None):
        orig(obj, mats, image, kind, uv, margin, socket)
        if not (kind == 'EMIT' and socket == 'Base Color' and image.name == f"T_{A}_Body_BaseColor"):
            return
        rgb, fd = nodes["paint_rgb"].outputs[0], nodes["paint_faded"].outputs[0]
        for vn, (col, faded) in C["variants"].items():
            rgb.default_value, fd.default_value = (*col, 1), (*faded, 1)
            im = k3d._new_image(f"{image.name}_{vn}", image.size[0], False)
            orig(obj, mats, im, kind, uv, margin, socket)
            k3d._save(im, os.path.join(k3d.ART, "Textures", f"{A}_Body", f"{im.name}.jpg"))
            bpy.data.images.remove(im)
    k3d._bake_pass = patched


def export(C, body, notes):
    """k3d.export + 도장 변형 머티리얼 M_<A>_Body_<변형> (BaseColor 만 다름) 을 JSON 에 추가."""
    A = C["name"]
    jp = os.path.splitext(k3d.export(A, "Vehicles", [body], notes=notes))[0] + ".json"
    d = json.load(open(jp))
    base = next(m for m in d["materials"] if m["name"] == f"M_{A}_Body")
    for vn in C["variants"]:
        v = copy.deepcopy(base)
        v["name"] = f"M_{A}_Body_{vn}"
        v["maps"]["BaseColor"] = base["maps"]["BaseColor"].replace("_BaseColor.jpg", f"_BaseColor_{vn}.jpg")
        d["materials"].append(v)
    json.dump(d, open(jp, "w"), ensure_ascii=False, indent=1)


def build(C):
    A = C["name"]
    L = C["L"]
    B = Body(C)
    k3d.reset()
    V.make_textures()

    # 머티리얼
    gaps = make_gaps(B)
    M = {
        "paint": V.mat_paint(f"{A}_paint", C["paint"], C.get("paint_rough", 0.2), C.get("paint_metal", 0.0),
                             faded=C.get("faded"), gaps=gaps, dirt=C.get("dirt", 1.0)),
        "under": V.mat_plastic(f"{A}_under", (0.012, 0.012, 0.012), 0.9, (0.03, 0.03, 0.028), dirt=1.2),
        "trim": V.mat_plastic(f"{A}_trim"),
        "gloss": m_gloss_black(f"{A}_gloss"),
        "rubber": V.mat_rubber(f"{A}_rubber"),
        "chrome": V.mat_metal(f"{A}_chrome", (0.85, 0.85, 0.86), 0.08, 0.1),
        "steel": V.mat_metal(f"{A}_steel", (0.45, 0.44, 0.43), 0.45, 0.2, rust=0.6),
        "reflector": V.mat_metal(f"{A}_refl", (0.9, 0.9, 0.92), 0.12, 0.05),
        "housing": V.mat_metal(f"{A}_housing", (0.12, 0.12, 0.13), 0.35, 0.1),
        "drl": m_emit(f"{A}_drl", (0.9, 0.92, 0.95), (0.85, 0.9, 1.0)),
        "amber": m_emit(f"{A}_amber", (0.7, 0.25, 0.02), (0.08, 0.025, 0.0), 0.15),
        "tail": m_tail(f"{A}_tail"),
        "redrefl": m_emit(f"{A}_redrefl", (0.4, 0.01, 0.01), (0.03, 0.0, 0.0), 0.2),
        "honey": m_honeycomb(f"{A}_honey"),
        "mirror": V.mat_metal(f"{A}_mirror", (0.6, 0.62, 0.64), 0.04, 0.05),
        "fabric": m_fabric(f"{A}_fabric"),
        "dash": V.mat_plastic(f"{A}_dash", (0.02, 0.02, 0.021), 0.7, (0.03, 0.03, 0.03), dirt=0.3),
        "seat": m_fabric(f"{A}_seat", C.get("seat", (0.035, 0.033, 0.03))),
        "glass": V.glass(f"M_Glass_{A}_Window", (1, 1, 1), 0.35, 0.05, V.tex("glass_front.png")),
        "tint": V.glass(f"M_Glass_{A}_Tint", (1, 1, 1), 0.85, 0.05, V.tex("glass_tint.png")),
        "lens": V.glass(f"M_Glass_{A}_Lens", (0.9, 0.92, 0.95), 0.22, 0.02),
        "tire": m_tire(f"{A}_tiremat", C["tire_r"], C["tire_w"] / 2, V.tex(C["tire_img"])),
        "alloy": m_alloy(f"{A}_alloy", C.get("alloy", (0.55, 0.56, 0.58))),
        "cap": m_gloss_black(f"{A}_capmat", 0.2),
    }
    paint_variants(A, C, M["paint"])

    # 1) 차체 곡면
    us = set()
    for sc in (0.0, 0.3, 0.55, 0.75, 0.88, 0.96):
        us.add(B.uc * sc)
        us.add(1 - B.uc * sc)
    ts = set(np.linspace(0, L, C.get("nu", 34)))
    for k in range(7):
        th = k / 6 * math.pi / 2
        ts.add(B.rr[0] * (1 - math.cos(th)))
        ts.add(L - B.rr[1] * (1 - math.cos(th)))
    for ta in C["axles"]:
        ts |= set(np.linspace(ta - C["arch_r"] - 0.03, ta + C["arch_r"] + 0.03, 16))
        z0 = B.f["bot"](ta) - C["tire_r"] - C.get("arch_dz", 0.0)
        if abs(z0) < C["arch_r"]:
            hc = math.sqrt(C["arch_r"] ** 2 - z0 * z0)
            ts |= {ta - hc, ta + hc}
    us |= {B.u_of(min(max(t, 0.0), L)) for t in ts}
    vs = set(np.linspace(0, 1, C.get("nv", 18))) | set(KN)
    vs |= set(np.linspace(0.10, 0.17, 4)) | set(np.linspace(0.70, 0.78, 3))

    regions = []
    for r in C["regions"]:
        d = dict(r)
        d["u0"], d["u1"] = B.u_of(r["t0"]), B.u_of(r["t1"])
        for k in ("mat", "seal", "band_mat"):
            if k in d and isinstance(d[k], str):
                d[k] = M[d[k]]
        regions.append(d)
    U = V.params(sorted(us), regions, "u")
    Vv = V.params(sorted(vs), regions, "v")

    def base_mat(u, v):
        if B.uc < u < 1 - B.uc and v < KN[1] - 1e-6:
            return M["under"]
        return M["paint"]

    body = V.pgrid(A + "_Body", B.S, U, Vv, regions, base_mat)
    V.mirror_x(body)
    V.shade(body, 38)
    V.bevel_mod(body, 0.004, 2, angle=55)

    parts = [body]
    parts += details(A, C, B, M)
    body = V.join(parts, A + "_Body")
    V.shade(body, 38)
    k3d.uv_world(body, 1.0)  # 유리 면 UV (굽지 않는 면)

    # 2) 실내
    intr = interior(A, C, B, M)

    # 3) 번호판·스티커 (굽지 않는 이미지)
    extras = plates(A, C, B)

    # 4) 바퀴
    w0 = wheel(A + "_Wheel_FR", C, M)
    fix_emission()
    if not FAST:
        k3d.bake(w0, 1024, samples=16, ao_distance=0.1)
    wheels = []
    xw = C["track"] / 2
    for nm, t, sx in (("FL", C["axles"][0], -1), ("FR", C["axles"][0], 1), ("RL", C["axles"][1], -1), ("RR", C["axles"][1], 1)):
        o = w0 if nm == "FR" else w0.copy()
        if o is not w0:
            o.data = w0.data.copy()
            bpy.context.scene.collection.objects.link(o)
        o.name = f"{A}_Wheel_{nm}"
        if sx < 0:
            o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
            o.data.update()
        o.location = (sx * xw, -L / 2 + t, C["tire_r"])
        wheels.append(o)

    if not FAST:
        k3d.bake(body, 2048, samples=16, ao_distance=0.35)
        k3d.bake(intr, 512, samples=12, ao_distance=0.2)

    for o in [intr] + extras + wheels:
        o.parent = body
    for o in sockets(A, C, B):
        o.parent = body
    return body, wheels


# ---------------------------------------------------------------- 패널 틈 (도장 머티리얼 안 절차 선)
def make_gaps(B):
    C, L = B.C, B.L

    def Y(t):
        return -L / 2 + t

    def gaps(g):
        x, y, z = g.xyz()
        ax = g.absf(x)
        w = 0.0035
        side = g.maprange(ax, C["W"] / 2 - 0.16, C["W"] / 2 - 0.10, 0, 1)
        acc = None

        def add(m):
            nonlocal acc
            acc = m if acc is None else g.maxf(acc, m)

        for (t, z0, z1) in C["cuts"]:  # 문 세로 틈
            add(g.mul(g.mul(g.line(y, Y(t), w), g.band(z, z0, z1)), side))
        d0, d1, dz = C["door_bottom"]  # 문 아래 틈
        add(g.mul(g.mul(g.line(z, dz, w), g.band(y, Y(d0), Y(d1))), side))
        h0, h1, hx = C["hood"]  # 후드
        top = g.maprange(z, C["hood_z"], C["hood_z"] + 0.05, 0, 1)
        add(g.mul(g.mul(g.line(ax, hx, w), g.band(y, Y(h0) - 0.2, Y(h1))), top))
        add(g.mul(g.mul(g.line(y, Y(h1), w), g.band(ax, -1, hx)), top))
        for (t, zz) in C.get("bumper_seams", ()):  # 범퍼-펜더 이음
            add(g.mul(g.mul(g.line(y, Y(t), w), g.band(z, C["sill_z"], zz)), side))
        k0, kx, kz = C["trunk"]  # 트렁크/해치
        rear = g.maprange(y, Y(L) - 0.35, Y(L) - 0.25, 0, 1)
        add(g.mul(g.mul(g.line(z, kz, w), g.band(ax, -1, kx)), rear))
        add(g.mul(g.mul(g.line(ax, kx, w), g.band(z, kz, 3.0)), g.maprange(y, Y(k0) - 0.01, Y(k0) + 0.01, 0, 1)))
        if C.get("trunk_front"):
            add(g.mul(g.mul(g.line(y, Y(k0), w), g.band(ax, -1, kx)), g.maprange(z, C["trunk_front"], C["trunk_front"] + 0.03, 0, 1)))
        fy, fz = C["fuel"]  # 주유구 (오른쪽 뒤)
        fd = g.maxf(g.absf(g.sub(y, Y(fy))), g.absf(g.sub(z, fz)))
        add(g.mul(g.line(fd, 0.075, w), g.maprange(x, C["W"] / 2 - 0.16, C["W"] / 2 - 0.10, 0, 1)))
        return acc

    return gaps


# ---------------------------------------------------------------- 외장 부품
def details(A, C, B, M):
    L = B.L
    P = []
    yf = lambda x, z: B.face_y(0, x, z)
    yr = lambda x, z: B.face_y(1, x, z)
    D = C["front"]

    def front_box(nm, x0, x1, z0, z1, depth, mat, proud=0.006, bev=0.005, mirror=True, shear=0.0):
        """shear: 바깥쪽 끝이 올라가는 기울기 (dz/dx)."""
        out = []
        for sx in ((1, -1) if mirror else (1,)):
            xc = sx * (x0 + x1) / 2 if mirror else (x0 + x1) / 2
            o = gbox(A + nm, (abs(x1 - x0), depth, z1 - z0), (xc, 0, (z0 + z1) / 2), M[mat] if isinstance(mat, str) else mat,
                     cuts=4, bev=bev)
            for v in o.data.vertices:
                v.co.z += shear * v.co.x * sx
            conform(o, lambda x, z: yf(x, z) - proud + depth / 2)
            out.append(o)
        return out

    def rear_box(nm, x0, x1, z0, z1, depth, mat, proud=0.006, bev=0.005, mirror=True):
        out = []
        for sx in ((1, -1) if mirror else (1,)):
            xc = sx * (x0 + x1) / 2 if mirror else (x0 + x1) / 2
            o = gbox(A + nm, (abs(x1 - x0), depth, z1 - z0), (xc, 0, (z0 + z1) / 2), M[mat] if isinstance(mat, str) else mat,
                     cuts=4, bev=bev)
            conform(o, lambda x, z: yr(x, z) + proud - depth / 2)
            out.append(o)
        return out

    # 전조등: 하우징 + 프로젝터 2 + DRL 띠 + 투명 렌즈
    hx0, hx1, hz0, hz1 = D["lamp"]
    sh, hm = D.get("lamp_shear", 0.0), (hx0 + hx1) / 2
    P += front_box("_lampHouse", hx0, hx1, hz0, hz1, 0.05, "housing", 0.004, D.get("lamp_bev", 0.005), shear=sh)
    if D.get("round_lamp"):  # 경차: 큰 둥근 반사경 1 + 크롬 링 + 아래쪽 DRL 띠
        P += front_box("_drl", hx0 + 0.03, hx1 - 0.02, hz0 + 0.012, hz0 + 0.026, 0.02, "drl", 0.007, 0.004, shear=sh)
        for sx in (1, -1):
            x = sx * (hx0 + (hx1 - hx0) * 0.56)
            zc = (hz0 + hz1) / 2 + 0.012 + sh * (abs(x) - hm)
            r = (hz1 - hz0) * 0.34
            P.append(V.cyl(A + "_proj", r, 0.03, (x, yf(x, zc) - 0.010, zc), (math.pi / 2, 0, 0), M["reflector"], segs=28, bevel=0.004))
            ring = V.tube(A + "_projRing", [(x + r * 1.06 * math.cos(a), 0, zc + r * 1.06 * math.sin(a))
                                            for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)], 0.004, 4, M["chrome"], cap=False, closed=True)
            conform(ring, lambda xx, zz: yf(xx, zz) - 0.024)
            P.append(ring)
            P.append(V.cyl(A + "_projLens", r * 0.42, 0.012, (x, yf(x, zc) - 0.022, zc), (math.pi / 2, 0, 0), M["gloss"], segs=20))
    else:
        P += front_box("_drl", hx0 + 0.01, hx1 - 0.01, hz1 - 0.022, hz1 - 0.01, 0.02, "drl", 0.007, 0.002)
        for sx in (1, -1):
            for k, fx in enumerate((0.35, 0.68)):
                x = sx * (hx0 + (hx1 - hx0) * fx)
                zc = (hz0 + hz1) / 2 - 0.008
                r = min(0.032, (hz1 - hz0) * 0.32)
                c = V.cyl(A + "_proj", r, 0.03, (x, yf(x, zc) - 0.012, zc), (math.pi / 2, 0, 0), M["reflector"], segs=20, bevel=0.003)
                P.append(c)
                c2 = V.cyl(A + "_projLens", r * 0.62, 0.01, (x, yf(x, zc) - 0.026, zc), (math.pi / 2, 0, 0), M["gloss"], segs=20)
                P.append(c2)
    P += front_box("_lens", hx0 - 0.004, hx1 + 0.004, hz0 - 0.004, hz1 + 0.004, 0.02, "lens", 0.032, D.get("lamp_bev", 0.006), shear=sh)
    # 그릴 + 크롬 띠
    gx, gz0, gz1 = D["grille"]
    P += front_box("_grille", -gx, gx, gz0, gz1, 0.05, D.get("grille_mat", "honey"), 0.004, 0.01, mirror=False)
    P += front_box("_grilleTrim", -gx - 0.012, gx + 0.012, gz1 - 0.004, gz1 + 0.012, 0.03, D.get("grille_trim", "chrome"), 0.010, 0.004, mirror=False)
    P += front_box("_grilleTrimB", -gx - 0.012, gx + 0.012, gz0 - 0.012, gz0 + 0.004, 0.03, "gloss", 0.010, 0.004, mirror=False)
    # 아래 흡기구 + 방향지시/안개등
    ix, iz0, iz1 = D["intake"]
    P += front_box("_intake", -ix, ix, iz0, iz1, 0.05, "honey", 0.003, 0.01, mirror=False)
    fx0, fx1, fz0, fz1 = D["fog"]
    P += front_box("_fogHouse", fx0, fx1, fz0, fz1, 0.05, "trim", 0.004)
    P += front_box("_fog", fx0 + 0.015, fx1 - 0.015, fz0 + 0.012, fz1 - 0.012, 0.03, "amber", 0.008, 0.003)
    # 번호판 받침
    pz = D["plate_z"]
    P += front_box("_plateBase", -0.28, 0.28, pz - 0.065, pz + 0.065, 0.03, "trim", 0.006, 0.004, mirror=False)

    # 후면
    R = C["rear"]
    tx0, tx1, tz0, tz1 = R["lamp"]
    P += rear_box("_tailHouse", tx0, tx1, tz0, tz1, 0.05, "tail", 0.012, 0.008)
    P += rear_box("_tailInner", tx0 + 0.03, tx1 - 0.03, tz0 + 0.02, tz0 + 0.04, 0.02, "reflector", 0.016, 0.002)
    if R.get("bar"):
        P += rear_box("_tailBar", -tx0, tx0, tz1 - 0.035, tz1 - 0.012, 0.03, "tail", 0.010, 0.003, mirror=False)
    dz0, dz1 = R["diffuser"]
    P += rear_box("_diffuser", -R["diff_x"], R["diff_x"], dz0, dz1, 0.05, "trim", 0.006, 0.008, mirror=False)
    P += rear_box("_refl", R["diff_x"] - 0.12, R["diff_x"] - 0.02, dz1 + 0.01, dz1 + 0.035, 0.02, "redrefl", 0.008, 0.002)
    pz = R["plate_z"]
    P += rear_box("_plateRecess", -0.29, 0.29, pz - 0.075, pz + 0.075, 0.03, "trim", 0.003, 0.006, mirror=False)
    ex = R.get("exhaust")
    if ex:
        for sx in ex[1]:
            x = sx * ex[0]
            z = dz0 + 0.03
            P.append(V.cyl(A + "_exh", 0.032, 0.12, (x, yr(x, z) - 0.03, z), (math.pi / 2, 0, 0), M["steel"], segs=16, bevel=0.004))

    # 사이드 미러
    mt, mz = C["mirror"]
    for sx in (1, -1):
        xb = B.side_x(mt, mz - 0.06)
        y = -L / 2 + mt
        base = beam(A + "_mirBase", (sx * (xb - 0.02), y - 0.06, mz - 0.05), (sx * (xb - 0.02), y + 0.08, mz - 0.03), 0.05, 0.06, M["trim"])
        V.bevel_mod(base, 0.008, 2, angle=None, weighted=False)
        arm = beam(A + "_mirArm", (sx * (xb + 0.005), y + 0.01, mz - 0.03), (sx * (xb + 0.07), y + 0.03, mz - 0.01), 0.05, 0.03, M["trim"])
        V.bevel_mod(arm, 0.006, 2, angle=None, weighted=False)
        hx = sx * (xb + 0.12)
        head = V.box(A + "_mirHead", (0.18, 0.10, 0.13), (hx, y + 0.05, mz + 0.01), M["paint"], bevel=0.03, segs=3)
        glass = V.box(A + "_mirGlass", (0.15, 0.01, 0.10), (hx, y + 0.101, mz + 0.012), M["mirror"], bevel=0.004)
        rep = V.box(A + "_mirRep", (0.12, 0.02, 0.012), (hx, y + 0.0, mz - 0.045), M["amber"], bevel=0.004)
        P += [base, arm, head, glass, rep]
    # 문 손잡이
    for t in C["handles"]:
        for sx in (1, -1):
            zh = C["handle_z"]
            xs = B.side_x(t, zh)
            hnd = V.box(A + "_handle", (0.03, 0.19, 0.035), (sx * (xs + 0.004), -L / 2 + t, zh), M[C.get("handle_mat", "paint")], bevel=0.012, segs=3)
            P.append(hnd)
            P.append(V.box(A + "_handleCup", (0.012, 0.16, 0.05), (sx * (xs - 0.001), -L / 2 + t, zh - 0.004), M["gloss"], bevel=0.005))
    # 와이퍼 (카울 위)
    wt = C["wiper_t"]
    zc = B.top_z(wt) + 0.012
    for x0, x1 in ((-0.62, 0.02), (0.05, 0.62)):
        b = beam(A + "_wiper", (x0, -L / 2 + wt, zc + 0.002), (x1, -L / 2 + wt + 0.03, zc + 0.012), 0.022, 0.014, M["trim"], up=(0, -0.3, 1))
        V.bevel_mod(b, 0.004, 2, angle=None, weighted=False)
        P.append(b)
    # 샤크핀 안테나
    at = C["antenna_t"]
    za = B.top_z(at)
    ant = beam(A + "_antenna", (0, -L / 2 + at - 0.09, za - 0.01), (0, -L / 2 + at + 0.07, za - 0.01), 0.06, 0.12, M["gloss"])
    for v in ant.data.vertices:  # 뒤로 갈수록 높게 (상어 지느러미)
        if v.co.z > za + 0.02:
            v.co.z = za + 0.015 + 0.045 * (v.co.y - (-L / 2 + at - 0.09)) / 0.16
            v.co.x *= 0.6
    V.bevel_mod(ant, 0.015, 3, angle=None, weighted=False)
    P.append(ant)
    # 휠하우스 안쪽 검은 라이너 판 (구멍 너머가 안 보이게)
    for ta in C["axles"]:
        for sx in (1, -1):
            x = sx * (C["track"] / 2 - C["tire_w"] / 2 - 0.05)
            lin = V.box(A + "_liner", (0.02, C["arch_r"] * 2, C["arch_r"] * 1.0), (x, -L / 2 + ta, C["tire_r"] + C["arch_r"] * 0.45), M["under"])
            P.append(lin)
    return P


def plates(A, C, B):
    L = B.L
    out = []
    pm = V.flat_image(f"M_{A}_Plate", V.tex(C["plate_img"]), 0.45, metal=0.0)
    pz = C["front"]["plate_z"]
    q = V.quad(A + "_PlateFront", 0.52, 0.11, pm, (0, B.face_y(0, 0, pz) - 0.022, pz))
    out.append(q)
    pz = C["rear"]["plate_z"]
    q = V.quad(A + "_PlateRear", 0.52, 0.11, pm, (0, B.face_y(1, 0, pz) + 0.014, pz), (0, 0, math.pi))
    out.append(q)
    for st in C.get("stickers", ()):
        sm = V.flat_image(f"M_{A}_Sticker_{st['id']}", V.tex(st["img"]), 0.6, alpha_clip=0.5)
        loc, rot = st["fn"](B)
        o = V.quad(f"{A}_Sticker_{st['id']}", st["w"], st["h"], sm, loc, rot)
        out.append(o)
    return out


def interior(A, C, B, M):
    L = B.L
    I = C["cabin"]
    P = []
    Y = lambda t: -L / 2 + t
    wi = C["W"] / 2 - 0.12
    # 바닥, 문 안쪽 판
    P.append(V.box(A + "_floor", (wi * 2, I["t1"] - I["t0"], 0.06), (0, Y((I["t0"] + I["t1"]) / 2), 0.30), M["fabric"]))
    for sx in (1, -1):
        tm = (I["t0"] + I["t1"]) / 2
        xs = B.side_x(tm, 0.7) - 0.07
        P.append(V.box(A + "_doorIn", (0.04, I["t1"] - I["t0"] - 0.1, I["belt"] - 0.34), (sx * xs, Y(tm), (I["belt"] + 0.30) / 2), M["dash"], bevel=0.015))
        P.append(V.box(A + "_armrest", (0.07, 0.5, 0.05), (sx * (xs - 0.04), Y(I["seat_f"] - 0.05), 0.68), M["dash"], bevel=0.015))
    # 대시보드
    td = I["dash"]
    P.append(V.box(A + "_dash", (wi * 2 - 0.02, 0.50, 0.24), (0, Y(td + 0.25), I["dash_z"] - 0.12), M["dash"], bevel=0.05, segs=3))
    P.append(V.box(A + "_cluster", (0.32, 0.12, 0.08), (0.37, Y(td + 0.42), I["dash_z"] + 0.01), M["dash"], bevel=0.03))
    P.append(V.box(A + "_screen", (0.26, 0.02, 0.15), (0.0, Y(td + 0.44), I["dash_z"] + 0.04), M["gloss"], bevel=0.008, rot=(-0.25, 0, 0)))
    P.append(V.box(A + "_console", (0.22, 0.75, 0.22), (0, Y(td + 0.85), 0.42), M["dash"], bevel=0.03))
    # 핸들 (좌핸들: 운전석 +x)
    sw = V.tube(A + "_steer", [(0.18 * math.cos(a), 0, 0.18 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)],
                0.016, 8, M["dash"], cap=False, closed=True)
    sw.location = (0.37, Y(td + 0.64), I["dash_z"] - 0.06)
    sw.rotation_euler = (-0.45, 0, 0)
    P.append(sw)
    P.append(beam(A + "_steerHub", (0.37, Y(td + 0.64), I["dash_z"] - 0.06), (0.37, Y(td + 0.40), I["dash_z"] - 0.02), 0.07, 0.07, M["dash"]))
    # 앞좌석 2, 뒷좌석
    def seat(x, t, wdt, nm):
        c = V.box(A + nm + "C", (wdt, 0.50, 0.13), (x, Y(t), 0.44), M["seat"], bevel=0.04, segs=3)
        b = V.box(A + nm + "B", (wdt, 0.12, 0.60), (x, Y(t + 0.27), 0.76), M["seat"], bevel=0.045, segs=3, rot=(-0.22, 0, 0))
        return [c, b]
    for sx in (1, -1):
        P += seat(sx * 0.36, I["seat_f"], 0.50, "_seatF")
        P.append(V.box(A + "_headrest", (0.26, 0.10, 0.17), (sx * 0.36, Y(I["seat_f"] + 0.36), 1.14), M["seat"], bevel=0.035, segs=3))
    P += seat(0, I["seat_r"], wi * 2 - 0.12, "_seatR")
    for sx in (1, -1):
        P.append(V.box(A + "_headrestR", (0.24, 0.09, 0.14), (sx * 0.40, Y(I["seat_r"] + 0.36), 1.10), M["seat"], bevel=0.03, segs=3))
    pt = I.get("shelf")
    if pt:
        P.append(V.box(A + "_shelf", (wi * 2, pt[1] - pt[0], 0.03), (0, Y((pt[0] + pt[1]) / 2), pt[2]), M["dash"]))
    o = V.join(P, A + "_Interior")
    V.shade(o, 40)
    return o


def sockets(A, C, B):
    L = B.L
    out = []
    for nm, loc in C["sockets"].items():
        out.append(V.empty(f"{A}_Socket_{nm}", (loc[0], -L / 2 + loc[1], loc[2])))
    return out


def sticker_loc(t, v, depth=0.015):
    """유리 안쪽 스티커 위치·회전 (차체 곡면 법선 기준)."""
    def f(B):
        from mathutils import Vector, Matrix
        u = B.u_of(t)
        p = Vector(B.S(u, v))
        a = Vector(B.S(u + 1e-3, v)) - Vector(B.S(u - 1e-3, v))
        b = Vector(B.S(u, v + 1e-3)) - Vector(B.S(u, v - 1e-3))
        n = a.cross(b).normalized()
        up = (Vector((0, 0, 1)) - n * n.z).normalized()
        y = -n
        x = y.cross(up).normalized()
        m = Matrix((x, y, up)).transposed()
        return p - n * depth, m.to_euler()
    return f

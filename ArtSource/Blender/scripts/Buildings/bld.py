"""건물 그룹 공용 도우미 (Blender 5.2, k3d 위에서 동작).

- Mesh: 파트를 bmesh 하나에 모으는 빌더 (상자/원기둥/사각면/구멍 뚫린 벽). 월드 좌표(m), Z-up, 정면 -Y.
- 절차 머티리얼 pm(): 색 변화 + 모서리 마모 + 틈새 때 + 세로 빗물 자국 -> k3d.bake 로 굽는다.
- Atlas: 간판/명판/포스터/실내 카드를 tex2d.py(Pillow)로 한 장에 그리고 UV 를 맞춘다.
- 부품: 창문, 난간, 실외기, 가스배관, 선홈통, CCTV, 간판, 셔터, 차양.
"""
import bpy, bmesh, math, os, sys, json, subprocess, random
from mathutils import Vector, Matrix, Euler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import k3d

HERE = os.path.dirname(os.path.abspath(__file__))
VPY = k3d.PY
TILE_M = {}          # 타일 머티리얼 이름 -> 타일 크기(m)
rnd = random.Random(7)


# ---------------------------------------------------------------- 머티리얼

def tile(name, ph_id, tile_m, res="2k", tint=None, rough_mul=1.0):
    """M_Tile_Buildings_<name> (Poly Haven CC0)."""
    m = k3d.tile("Buildings_" + name, polyhaven_id=ph_id, res=res, tint=tint, rough_mul=rough_mul)
    TILE_M[m.name] = tile_m
    return m


def glass(asset, part="Window", col=(0.05, 0.065, 0.07), alpha=0.32, rough=0.04):
    m = k3d.mat(f"M_Glass_{asset}_{part}", col, rough, 0.0, alpha=alpha)
    return m


def _n(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k.startswith("i_"):
            n.inputs[k[2:]].default_value = v
        else:
            setattr(n, k, v)
    return n


def _mixc(nt, fac, a, b):
    """RGBA 섞기 (a,b: 소켓 또는 색 튜플)."""
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    ins = {i.identifier: i for i in m.inputs}
    for sock, v in ((ins["A_Color"], a), (ins["B_Color"], b)):
        if isinstance(v, tuple):
            sock.default_value = (*v[:3], 1)
        else:
            nt.links.new(v, sock)
    if isinstance(fac, float):
        ins["Factor_Float"].default_value = fac
    else:
        nt.links.new(fac, ins["Factor_Float"])
    return next(o for o in m.outputs if o.identifier == "Result_Color")


def _range(nt, v, a, b, c=0.0, d=1.0):
    r = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(v, r.inputs["Value"])
    r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = a, b
    r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = c, d
    return r.outputs["Result"]


def _math(nt, op, a, b):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for s, v in ((m.inputs[0], a), (m.inputs[1], b)):
        if isinstance(v, (int, float)):
            s.default_value = v
        else:
            nt.links.new(v, s)
    return m.outputs[0]


def pm(name, col, rough=0.5, metal=0.0, edge=None, edge_amt=0.7, grime=0.35, streak=0.0,
       bump=0.25, scale=5.0, var=0.12, spots=None, spot_amt=0.0, emit=None, emit_s=0.0,
       grime_col=(0.09, 0.075, 0.06)):
    """굽기용 절차 머티리얼 P_<name> (Principled 하나 -> 출력)."""
    nm = "P_" + name
    if nm in bpy.data.materials:
        return bpy.data.materials[nm]
    m = k3d.mat(nm, col, rough, metal)
    nt = m.node_tree
    p = k3d.principled(m)
    L = nt.links.new
    tc = _n(nt, "ShaderNodeTexCoord")
    geo = _n(nt, "ShaderNodeNewGeometry")
    n1 = _n(nt, "ShaderNodeTexNoise", i_Scale=scale, i_Detail=6.0, i_Roughness=0.6)
    L(tc.outputs["Object"], n1.inputs["Vector"])
    v1 = _range(nt, n1.outputs["Fac"], 0.3, 0.7)
    c = _mixc(nt, v1, tuple(x * (1 - var) for x in col), tuple(min(1, x * (1 + var)) for x in col))
    n2 = _n(nt, "ShaderNodeTexNoise", i_Scale=scale * 9, i_Detail=4.0, i_Roughness=0.7)
    L(tc.outputs["Object"], n2.inputs["Vector"])
    wear = None
    if edge is not None:
        bev = _n(nt, "ShaderNodeBevel", i_Radius=0.006)
        bev.samples = 8
        dot = _n(nt, "ShaderNodeVectorMath", operation="DOT_PRODUCT")
        L(bev.outputs["Normal"], dot.inputs[0])
        L(geo.outputs["Normal"], dot.inputs[1])
        e = _range(nt, dot.outputs["Value"], 0.995, 0.93)
        br = _range(nt, n2.outputs["Fac"], 0.42, 0.62)
        wear = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", e, br), edge_amt)
        c = _mixc(nt, wear, c, edge)
    if spots is not None and spot_amt > 0:
        n3 = _n(nt, "ShaderNodeTexNoise", i_Scale=scale * 3, i_Detail=8.0, i_Roughness=0.7)
        L(tc.outputs["Object"], n3.inputs["Vector"])
        s = _math(nt, "MULTIPLY", _range(nt, n3.outputs["Fac"], 0.62, 0.72), spot_amt)
        c = _mixc(nt, s, c, spots)
    ao = _n(nt, "ShaderNodeAmbientOcclusion", i_Distance=0.1)
    ao.samples = 8
    cav = _math(nt, "MULTIPLY", _range(nt, ao.outputs["AO"], 0.95, 0.35), grime)
    g = cav
    if streak > 0:
        mp = _n(nt, "ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (9, 9, 0.5)
        L(tc.outputs["Object"], mp.inputs["Vector"])
        n4 = _n(nt, "ShaderNodeTexNoise", i_Scale=3.0, i_Detail=6.0, i_Roughness=0.65)
        n4.inputs["Distortion"].default_value = 0.6
        L(mp.outputs["Vector"], n4.inputs["Vector"])
        st = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", _range(nt, n4.outputs["Fac"], 0.55, 0.75), v1), streak)
        g = _math(nt, "MAXIMUM", g, st)
    c = _mixc(nt, g, c, grime_col)
    L(c, p.inputs["Base Color"])
    r = _math(nt, "ADD", _math(nt, "MULTIPLY", _range(nt, n1.outputs["Fac"], 0, 1, -0.08, 0.08), 1.0), rough)
    r = _math(nt, "ADD", r, _math(nt, "MULTIPLY", g, 0.25))
    if wear is not None and metal < 0.5:
        r = _math(nt, "SUBTRACT", r, _math(nt, "MULTIPLY", wear, 0.15))
    L(r, p.inputs["Roughness"])
    if bump:
        n5 = _n(nt, "ShaderNodeTexNoise", i_Scale=scale * 25, i_Detail=4.0)
        L(tc.outputs["Object"], n5.inputs["Vector"])
        b = _n(nt, "ShaderNodeBump", i_Strength=bump, i_Distance=0.002)
        L(n5.outputs["Fac"], b.inputs["Height"])
        L(b.outputs["Normal"], p.inputs["Normal"])
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = emit_s
    else:   # Principled 기본 발광색은 흰색 -> 같은 오브젝트에 발광 재질이 있으면 k3d.bake 가 전부 흰색으로 굽는다
        p.inputs["Emission Color"].default_value = (0, 0, 0, 1)
    return m


def palette():
    """자주 쓰는 굽기 머티리얼 묶음."""
    return dict(
        pvc=pm("PvcWhite", (0.78, 0.77, 0.73), 0.42, edge=(0.6, 0.58, 0.52), edge_amt=0.4, grime=0.5, streak=0.25),
        alu=pm("AluSilver", (0.6, 0.61, 0.6), 0.38, 1.0, edge=(0.8, 0.8, 0.78), edge_amt=0.5, grime=0.45, streak=0.2,
               spots=(0.75, 0.75, 0.72), spot_amt=0.3),
        bronze=pm("AluBronze", (0.12, 0.085, 0.06), 0.4, 0.75, edge=(0.3, 0.24, 0.17), grime=0.4, streak=0.25),
        sus=pm("Stainless", (0.58, 0.58, 0.57), 0.28, 1.0, grime=0.35, streak=0.15, spots=(0.4, 0.33, 0.25), spot_amt=0.25),
        steel=pm("SteelPaint", (0.07, 0.075, 0.08), 0.5, 0.3, edge=(0.32, 0.31, 0.29), grime=0.3, streak=0.3,
                 spots=(0.25, 0.1, 0.04), spot_amt=0.35),
        galv=pm("Galvanized", (0.48, 0.49, 0.47), 0.5, 0.85, grime=0.5, streak=0.35, spots=(0.33, 0.16, 0.07), spot_amt=0.5),
        gas=pm("GasYellow", (0.62, 0.42, 0.04), 0.45, edge=(0.3, 0.27, 0.22), edge_amt=0.6, grime=0.5, streak=0.3),
        pipe=pm("PvcGrey", (0.36, 0.36, 0.34), 0.55, grime=0.5, streak=0.45),
        ivory=pm("PlasticIvory", (0.72, 0.7, 0.63), 0.45, edge=(0.55, 0.52, 0.45), edge_amt=0.3, grime=0.55, streak=0.22, bump=0.06),
        rubber=pm("Rubber", (0.025, 0.025, 0.025), 0.85, grime=0.2, bump=0.4),
        black=pm("PlasticBlack", (0.03, 0.03, 0.032), 0.45, edge=(0.12, 0.12, 0.12), edge_amt=0.4, grime=0.2),
        conc=pm("ConcreteCast", (0.5, 0.49, 0.46), 0.88, grime=0.6, streak=0.4, bump=0.6, scale=3.0, var=0.18),
        paintw=pm("PaintWhiteConc", (0.72, 0.71, 0.67), 0.75, edge=(0.45, 0.44, 0.41), edge_amt=0.5, grime=0.6,
                  streak=0.55, bump=0.4, scale=3.0),
        granite=pm("GraniteSill", (0.5, 0.47, 0.45), 0.45, grime=0.45, streak=0.3, scale=60.0, var=0.35, bump=0.2),
        tape=pm("InsulTape", (0.82, 0.8, 0.74), 0.6, grime=0.6, streak=0.4, bump=0.5, scale=12.0),
        rust=pm("RustySteel", (0.2, 0.09, 0.04), 0.8, 0.4, grime=0.3, spots=(0.08, 0.06, 0.05), spot_amt=0.6, bump=0.6),
        brass=pm("LetterBrass", (0.75, 0.55, 0.22), 0.32, 1.0, grime=0.5, streak=0.3, spots=(0.25, 0.3, 0.2), spot_amt=0.3),
        light=pm("TubeLight", (0.9, 0.9, 0.86), 0.3, emit=(1.0, 0.98, 0.92), emit_s=3.0, grime=0.0, bump=0),
        copper=pm("Copper", (0.55, 0.3, 0.18), 0.4, 1.0, grime=0.4, spots=(0.2, 0.4, 0.3), spot_amt=0.4),
    )


_LATE = []


def flat_img(name, path, rough=0.6, emit=0.0, alpha_clip=None, transparent=False, double_sided=False):
    """이미지 하나를 쓰는 비굽기 머티리얼 (M_<Asset>_<Part>). 이미지는 draw() 뒤에 읽는다."""
    m = k3d.mat(name, (1, 1, 1), rough, double_sided=double_sided)
    nt = m.node_tree
    p = k3d.principled(m)
    im = bpy.data.images.get(os.path.basename(path))
    if im is None:
        im = bpy.data.images.new(os.path.basename(path), 4, 4, alpha=True)
        im.source = "FILE"
        im.filepath = path
        _LATE.append(im)
    t = k3d.image_node(m, im, p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
    if alpha_clip is not None or transparent:
        nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    if alpha_clip is not None:
        k3d.flag(m, alpha_clip=alpha_clip)
    if transparent:
        k3d.flag(m, transparent=True)
    return m


# ---------------------------------------------------------------- 메시 빌더

class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.bm.loops.layers.uv.new("UVMap")
        self.mats = []
        self.fixed = []       # (face, atlas_item 또는 uv 사각형)
        self.T = Matrix.Identity(4)
        self.extras = []      # 따로 만든 오브젝트 (글자 등) -> 마지막에 합침

    def mi(self, m):
        if m.name not in self.mats:
            self.mats.append(m.name)
        return self.mats.index(m.name)

    def at(self, loc=(0, 0, 0), rz=0.0, rx=0.0):
        """이후 파트를 이 좌표계(위치+Z 회전)로 둔다. 반환값으로 되돌린다."""
        old = self.T
        self.T = old @ Matrix.Translation(Vector(loc)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X")
        return old

    def box(self, m, c, s, bev=0.008, seg=2, rot=None):
        s = [max(1e-4, abs(v)) for v in s]
        M = self.T @ Matrix.Translation(Vector(c))
        if rot:
            M = M @ Euler(rot).to_matrix().to_4x4()
        M = M @ Matrix.Diagonal((s[0], s[1], s[2], 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        vs = r["verts"]
        idx = self.mi(m)
        fs = {f for v in vs for f in v.link_faces}
        for f in fs:
            f.material_index = idx
        b = min(bev, 0.3 * min(s)) if bev else 0
        if b > 0.0004:
            es = list({e for v in vs for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=vs + es, offset=b, offset_type="OFFSET", segments=seg,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        return fs

    def boxa(self, m, a, b, bev=0.008, seg=2):
        """두 꼭짓점(최소, 최대)으로 상자."""
        c = [(a[i] + b[i]) / 2 for i in range(3)]
        s = [b[i] - a[i] for i in range(3)]
        return self.box(m, c, s, bev, seg)

    def cyl(self, m, p0, p1, r, seg=12, cap=True, r2=None):
        p0, p1 = self.T @ Vector(p0), self.T @ Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-5:
            return
        q = d.normalized().to_track_quat("Z", "Y")
        M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4()
        r_ = bmesh.ops.create_cone(self.bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                                   radius2=r if r2 is None else r2, depth=L, matrix=M)
        idx = self.mi(m)
        for f in {f for v in r_["verts"] for f in v.link_faces}:
            f.material_index = idx

    def path(self, m, pts, r, seg=10, joint=True):
        """꺾인 관 (구간마다 원기둥 + 관절 구)."""
        for a, b in zip(pts, pts[1:]):
            self.cyl(m, a, b, r, seg)
        if joint:
            for p in pts[1:-1]:
                self.sphere(m, p, r * 1.02, 8)

    def sphere(self, m, c, r, seg=10):
        M = self.T @ Matrix.Translation(Vector(c))
        r_ = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(4, seg // 2), radius=r, matrix=M)
        idx = self.mi(m)
        for f in {f for v in r_["verts"] for f in v.link_faces}:
            f.material_index = idx

    def torus(self, m, c, axis, R, r, seg=24, rs=6):
        c = Vector(c)
        z = Vector(axis).normalized()
        x = z.orthogonal().normalized()
        y = z.cross(x)
        rings = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            d = x * math.cos(a) + y * math.sin(a)
            ring = []
            for j in range(rs):
                b = 2 * math.pi * j / rs
                p = c + d * (R + r * math.cos(b)) + z * (r * math.sin(b))
                ring.append(self.bm.verts.new(self.T @ p))
            rings.append(ring)
        idx = self.mi(m)
        for i in range(seg):
            for j in range(rs):
                a, b = rings[i], rings[(i + 1) % seg]
                f = self.bm.faces.new((a[j], b[j], b[(j + 1) % rs], a[(j + 1) % rs]))
                f.material_index = idx

    def quad(self, m, c, right, up, w, h, uv=None, item=None):
        """c 중심, right/up 방향 사각면 (법선 = right x up). uv=(u0,v0,u1,v1) 또는 item=Atlas 항목."""
        c, R, U = Vector(c), Vector(right).normalized(), Vector(up).normalized()
        ps = [c - R * w / 2 - U * h / 2, c + R * w / 2 - U * h / 2, c + R * w / 2 + U * h / 2, c - R * w / 2 + U * h / 2]
        vs = [self.bm.verts.new(self.T @ p) for p in ps]
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(m)
        if uv or item:
            self.fixed.append((f, item if item else uv))
        return f

    def poly(self, m, pts):
        vs = [self.bm.verts.new(self.T @ Vector(p)) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(m)
        return f

    def wall(self, m, O, R, U, W, H, holes=(), thick=0.2, reveal=None, reveal_m=None):
        """구멍 뚫린 벽면 (O=왼쪽 아래, R=오른쪽, U=위, 법선 R x U 가 바깥).
        holes=[(u0,u1,v0,v1)], 개구부 안쪽 면(reveal) 깊이 thick."""
        O, R, U = Vector(O), Vector(R).normalized(), Vector(U).normalized()
        N = R.cross(U)
        us = sorted({0.0, W, *[h[0] for h in holes], *[h[1] for h in holes]})
        vs = sorted({0.0, H, *[h[2] for h in holes], *[h[3] for h in holes]})
        us = [u for u in us if 0 <= u <= W]
        vs = [v for v in vs if 0 <= v <= H]
        grid = {}
        def V(i, j):
            if (i, j) not in grid:
                grid[i, j] = self.bm.verts.new(self.T @ (O + R * us[i] + U * vs[j]))
            return grid[i, j]
        idx = self.mi(m)
        for i in range(len(us) - 1):
            for j in range(len(vs) - 1):
                uc, vc = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
                if any(h[0] < uc < h[1] and h[2] < vc < h[3] for h in holes):
                    continue
                f = self.bm.faces.new((V(i, j), V(i + 1, j), V(i + 1, j + 1), V(i, j + 1)))
                f.material_index = idx
        rm = reveal_m or m
        for (u0, u1, v0, v1) in holes:
            P = lambda u, v, d=0.0: O + R * u + U * v - N * d
            d = thick
            sides = [((u0, v0), (u1, v0), U), ((u1, v1), (u0, v1), -U), ((u0, v1), (u0, v0), R), ((u1, v0), (u1, v1), -R)]
            for k, (a, b, nrm) in enumerate(sides):
                if k == 0 and v0 <= 0.001:
                    continue   # 바닥까지 내려온 문 구멍은 아랫면 없음
                pa, pb = P(*a), P(*b)
                self.poly(rm, [pa, pb, pb - N * d, pa - N * d])   # 법선이 구멍 안쪽을 본다
        return N

    def to_object(self, name):
        # 고정 UV 와 타일 UV
        uvl = self.bm.loops.layers.uv.active
        self.bm.normal_update()
        fixed = {f for f, _ in self.fixed}
        for f, it in self.fixed:
            if not f.is_valid:
                continue
            u0, v0, u1, v1 = it.uv() if hasattr(it, "uv") else it
            for l, (u, v) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                l[uvl].uv = (u, v)
        tile_idx = {i: TILE_M[n] for i, n in enumerate(self.mats) if n in TILE_M}
        for f in self.bm.faces:
            if f in fixed or f.material_index not in tile_idx:
                continue
            t = tile_idx[f.material_index]
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            for l in f.loops:
                w = l.vert.co
                if ax == 0:
                    u, v = (w.y if n.x > 0 else -w.y), w.z
                elif ax == 1:
                    u, v = (-w.x if n.y > 0 else w.x), w.z
                else:
                    u, v = w.x, (w.y if n.z > 0 else -w.y)
                l[uvl].uv = (u / t, v / t)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        for n in self.mats:
            me.materials.append(bpy.data.materials[n])
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if self.extras:
            for e in self.extras:
                k3d.apply_all(e)
            ob = k3d.join([ob] + self.extras, name)
        return ob

    def letters(self, text, font, size, m, c, depth=0.03, right=(1, 0, 0), up=(0, 0, 1), align="CENTER", spacing=1.0):
        """3D 글자 (폰트 곡선 -> 메시). c = 글자 바닥 중앙, 앞면이 right x up 방향을 본다."""
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body = text
        cu.font = bpy.data.fonts.load(font, check_existing=True)
        cu.size = size
        cu.extrude = depth / 2
        cu.bevel_depth = min(0.004, depth * 0.15)
        cu.bevel_resolution = 1
        cu.resolution_u = 3
        cu.align_x = align
        cu.space_character = spacing
        ob = bpy.data.objects.new("txt", cu)
        bpy.context.scene.collection.objects.link(ob)
        R, U = Vector(right).normalized(), Vector(up).normalized()
        N = R.cross(U)
        rot = Matrix((R, U, N)).transposed().to_4x4()   # 글자 로컬 X->R, Y->U, Z->N
        ob.matrix_world = self.T @ Matrix.Translation(Vector(c) + N * depth / 2) @ rot
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        mo = bpy.data.objects.new("txtm", me)
        bpy.context.scene.collection.objects.link(mo)
        mo.matrix_world = ob.matrix_world
        bpy.data.objects.remove(ob)
        me.materials.clear()
        me.materials.append(m)
        # 바닥선 맞추기: 글자 최저점을 c 높이에
        self.extras.append(mo)
        return mo


# ---------------------------------------------------------------- 2D 텍스처 아틀라스

class Item:
    def __init__(self, atlas, w, h, spec):
        self.atlas, self.w, self.h, self.spec = atlas, w, h, spec
        self.rect = None

    def uv(self):
        x, y, w, h = self.rect
        W, H = self.atlas.size
        e = 1.5  # 테두리 번짐 방지
        return ((x + e) / W, 1 - (y + h - e) / H, (x + w - e) / W, 1 - (y + e) / H)


class Atlas:
    def __init__(self, asset, part, size=(2048, 2048), mode="RGB"):
        self.asset, self.part, self.size, self.mode = asset, part, size, mode
        ext = ".png" if mode == "RGBA" else ".jpg"
        self.path = os.path.join(k3d.ART, "Textures", asset, f"T_{asset}_{part}{ext}")
        self.items = []

    def add(self, w_px, h_px, **spec):
        it = Item(self, int(w_px), int(h_px), spec)
        self.items.append(it)
        return it

    def pack(self):
        W, H = self.size
        s = 1.0
        while True:
            x = y = row = 0
            ok = True
            for it in sorted(self.items, key=lambda i: -i.h):
                w, h = max(4, int(it.w * s)), max(4, int(it.h * s))
                if w > W:
                    ok = False
                    break
                if x + w > W:
                    x, y, row = 0, y + row + 2, 0
                if y + h > H:
                    ok = False
                    break
                it.rect = (x, y, w, h)
                x += w + 2
                row = max(row, h)
            if ok:
                return s
            s *= 0.92

    def job(self):
        s = self.pack()
        print(f"bld: atlas {self.part} scale={s:.2f} items={len(self.items)}")
        return {"out": self.path, "size": list(self.size), "mode": self.mode,
                "items": [dict(it.spec, rect=list(it.rect)) for it in self.items]}


def draw(atlases):
    """아틀라스들을 Pillow 로 그린다 (venv 파이썬)."""
    jobs = [a.job() for a in atlases if a.items]
    jp = os.path.join(k3d.CACHE, f"bld_job_{os.getpid()}.json")
    json.dump(jobs, open(jp, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([VPY, "-I", os.path.join(HERE, "tex2d.py"), jp], capture_output=True, encoding="utf-8", errors="replace")
    print(r.stdout, r.stderr)
    if r.returncode:
        raise RuntimeError("tex2d 실패")
    for im in _LATE:
        im.reload()


# ---------------------------------------------------------------- 부품

def window(M, P, G, O, R, U, u0, u1, v0, v1, *, frame="pvc", depth=0.12, sashes=2, grille=False,
           screen_m=None, interior=None, interior_m=None, sill=True, glass_m=None, slide=0.0, thick=0.3):
    """벽 구멍 안 창호. O,R,U = 벽 좌표계 (법선 R x U 바깥). P=palette."""
    O, R, U = Vector(O), Vector(R).normalized(), Vector(U).normalized()
    N = R.cross(U)
    fm = P[frame]
    def at(u, v, d):
        return O + R * u + U * v - N * d
    w, h = u1 - u0, v1 - v0
    fp, fd = 0.055, 0.09
    def bar(ua, ub, va, vb, da, db, m, bev=0.006, seg=2):
        c = (at(ua, va, da) + at(ub, vb, db)) / 2
        # 축 정렬 크기 (R,U,N 이 월드 축과 나란하다고 가정)
        s = at(ub, vb, db) - at(ua, va, da)
        M.box(m, c, (abs(s.x), abs(s.y), abs(s.z)), bev, seg)
    d0 = depth
    # 바깥 틀
    bar(u0, u1, v0, v0 + fp, d0, d0 + fd, fm)
    bar(u0, u1, v1 - fp, v1, d0, d0 + fd, fm)
    bar(u0, u0 + fp, v0 + fp, v1 - fp, d0, d0 + fd, fm)
    bar(u1 - fp, u1, v0 + fp, v1 - fp, d0, d0 + fd, fm)
    gm = glass_m
    sp = 0.045
    iw = w - 2 * fp
    if sashes >= 2:
        sw = iw / sashes + 0.03
        for k in range(sashes):
            a = u0 + fp + k * (iw / sashes) - (0.015 if k else 0)
            if k == sashes - 1:
                a -= slide * sw
            b = a + sw
            dd = d0 + 0.012 + (k % 2) * 0.035
            bar(a, b, v0 + fp, v0 + fp + sp, dd, dd + 0.03, fm, 0.004, 1)
            bar(a, b, v1 - fp - sp, v1 - fp, dd, dd + 0.03, fm, 0.004, 1)
            bar(a, a + sp, v0 + fp + sp, v1 - fp - sp, dd, dd + 0.03, fm, 0.004, 1)
            bar(b - sp, b, v0 + fp + sp, v1 - fp - sp, dd, dd + 0.03, fm, 0.004, 1)
            M.quad(gm, at((a + b) / 2, (v0 + v1) / 2, dd + 0.015), R, U, sw - 2 * sp, h - 2 * fp - 2 * sp)
        if screen_m is not None:
            M.quad(screen_m, at(u0 + fp + iw * 0.75, (v0 + v1) / 2, d0 + 0.075), R, U, iw / 2 - 0.01, h - 2 * fp - 0.01)
    else:
        M.quad(gm, at((u0 + u1) / 2, (v0 + v1) / 2, d0 + 0.04), R, U, iw, h - 2 * fp)
    if interior is not None:
        M.quad(interior_m, at((u0 + u1) / 2, (v0 + v1) / 2, thick), R, U, w + 0.1, h + 0.1, item=interior)
    if sill:
        sm = P["granite"]
        c = at((u0 + u1) / 2, v0 - 0.02, (d0 - 0.07) / 2)
        s = at(u1 + 0.05, v0, d0) - at(u0 - 0.05, v0 - 0.045, -0.07)
        M.box(sm, c, (abs(s.x), abs(s.y), abs(s.z)), 0.008)
    if grille:
        gm2 = P["sus"]
        n = max(3, int(round(w / 0.11)))
        for k in range(n + 1):
            u = u0 - 0.03 + (w + 0.06) * k / n
            M.cyl(gm2, at(u, v0 - 0.04, -0.09), at(u, v1 + 0.04, -0.09), 0.008, 6)
        for v in (v0 - 0.02, v0 + h * 0.35, v0 + h * 0.7, v1 + 0.02):
            c = at((u0 + u1) / 2, v, -0.09)
            M.box(gm2, c, tuple(abs(x) for x in (R * (w + 0.1) + U * 0.025 + N * 0.006)), 0.002)
        for (u, v) in ((u0 - 0.04, v0 - 0.02), (u1 + 0.04, v0 - 0.02), (u0 - 0.04, v1 + 0.02), (u1 + 0.04, v1 + 0.02)):
            c = at(u, v, -0.045)
            M.box(gm2, c, tuple(abs(x) for x in (R * 0.02 + U * 0.02 + N * 0.09)), 0.003)


def railing(M, m, a, b, z0, h=1.05, post=1.2, bal=0.11, top_r=0.024, bal_r=0.009):
    """a,b = (x,y) 바닥선 양 끝. 철제 난간 (상부 레일 + 하부 레일 + 기둥 + 살)."""
    a, b = Vector((a[0], a[1], z0)), Vector((b[0], b[1], z0))
    d = b - a
    L = d.length
    t = d.normalized()
    M.cyl(m, a + Vector((0, 0, h)) - t * 0.03, b + Vector((0, 0, h)) + t * 0.03, top_r, 12)
    M.cyl(m, a + Vector((0, 0, 0.12)), b + Vector((0, 0, 0.12)), bal_r * 1.6, 8)
    n = max(1, int(round(L / post)))
    for k in range(n + 1):
        p = a + t * (L * k / n)
        M.box(m, p + Vector((0, 0, h / 2)), (0.035 if abs(t.x) > 0.5 else 0.035, 0.035, h), 0.004)
    nb = max(2, int(L / bal))
    for k in range(1, nb):
        p = a + t * (L * k / nb)
        M.cyl(m, p + Vector((0, 0, 0.12)), p + Vector((0, 0, h)), bal_r, 6, cap=False)


def ac_unit(M, P, loc, rz=0.0, wall_gap=0.12, bracket=True, pipe_up=0.9, pipe_side=0.35, decal=None, decal_m=None):
    """벽걸이 실외기 + ㄱ자 앵글 거치대 + 냉매관/배수호스. loc = 벽면 위 거치대 바닥 중앙, rz 로 벽 방향.
    로컬 좌표: -Y 가 바깥(정면), +Y 가 벽."""
    old = M.at(loc, rz)
    W, D, H = 0.84, 0.3, 0.62
    y0 = -wall_gap - D / 2                # 본체 중심 y
    z0 = 0.05
    iv, bk = P["ivory"], P["black"]
    M.box(iv, (0, y0, z0 + H / 2), (W, D, H), 0.018, 3)
    # 팬 그릴: 둥근 테 + 동심원 + 살
    fx, fz, fr = -0.12, z0 + H / 2, 0.24
    yf = y0 - D / 2
    M.cyl(bk, (fx, yf + 0.03, fz), (fx, yf - 0.004, fz), fr * 0.98, 32)
    M.torus(iv, (fx, yf - 0.006, fz), (0, 1, 0), fr, 0.014, 32, 6)
    for k, rr in enumerate((0.07, 0.12, 0.17, 0.215)):
        M.torus(bk, (fx, yf - 0.012, fz), (0, 1, 0), rr, 0.004, 20, 3)
    for k in range(4):
        a = k * math.pi / 4
        M.box(bk, (fx, yf - 0.012, fz), (fr * 2 * abs(math.cos(a)) + 0.008, 0.006, fr * 2 * abs(math.sin(a)) + 0.008), 0)
    for k in range(3):  # 팬 날개 (그릴 뒤)
        M.box(P["pipe"], (fx, yf + 0.022, fz), (0.36, 0.008, 0.07), 0.003, 1, rot=(0, k * 2.094 + 0.4, 0))
    M.cyl(bk, (fx, yf + 0.03, fz), (fx, yf + 0.0, fz), 0.045, 16)
    # 오른쪽 루버
    for k in range(9):
        M.box(iv, (0.26, yf - 0.006, z0 + 0.1 + k * 0.05), (0.26, 0.018, 0.012), 0.003, 1, rot=(0.5, 0, 0))
    # 상판 이음선, 서비스 커버, 받침
    M.box(iv, (0, y0, z0 + H + 0.004), (W - 0.04, D - 0.04, 0.012), 0.003, 1)
    M.box(iv, (W / 2 + 0.01, y0 + 0.05, z0 + 0.22), (0.03, 0.16, 0.26), 0.006)
    for sx in (-0.33, 0.33):
        M.box(bk, (sx, y0, z0 - 0.015), (0.08, D - 0.02, 0.03), 0.004)
    if decal is not None:
        M.quad(decal_m, (0.27, yf - 0.002, z0 + H - 0.08), (1, 0, 0), (0, 0, 1), 0.14, 0.07, item=decal)
    if bracket:
        g = P["galv"]
        for sx in (-0.3, 0.3):
            M.box(g, (sx, -0.26, 0.0), (0.04, 0.52, 0.04), 0.003)            # 수평 앵글
            M.box(g, (sx, -0.005, -0.18), (0.05, 0.01, 0.42), 0.002)          # 벽판
            M.cyl(g, (sx, -0.44, -0.015), (sx, -0.012, -0.35), 0.017, 4)  # 사선 버팀 (팔 끝 -> 벽판)
            for bz in (-0.33, -0.05):
                M.cyl(P["rust"], (sx, -0.006, bz), (sx, -0.02, bz), 0.009, 6)
    # 냉매관 2줄 (보온 테이프) + 배수 호스
    tp = P["tape"]
    px = W / 2 + 0.03
    for k, r in enumerate((0.021, 0.016)):
        yy = y0 + 0.06 - k * 0.05
        pts = [(px - 0.02, yy, z0 + 0.2 + k * 0.04), (px + 0.08, yy, z0 + 0.2 + k * 0.04),
               (px + 0.08 + k * 0.05, yy, z0 + 0.2 + pipe_up), (px + 0.08 + k * 0.05 + pipe_side, -0.03, z0 + 0.2 + pipe_up),
               (px + 0.08 + k * 0.05 + pipe_side, 0.04, z0 + 0.2 + pipe_up)]
        M.path(tp, pts, r, 8)
    M.box(P["paintw"], (px + 0.1 + pipe_side, -0.004, z0 + 0.2 + pipe_up), (0.16, 0.012, 0.14), 0.004)  # 관통부 마감
    M.path(bk, [(-W / 2 + 0.05, y0 + 0.05, z0), (-W / 2 + 0.05, y0 + 0.05, z0 - 0.15), (-W / 2 + 0.12, y0 + 0.02, z0 - 0.45)], 0.009, 6)
    M.T = old


def gas_line(M, P, pts, meters=(), r=0.017):
    """노란 가스관 + 클램프 + 계량기 (meters = 계량기 위치 목록)."""
    g = P["gas"]
    M.path(g, pts, r, 10)
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        n = int(L / 1.0)
        for k in range(1, n + 1):
            p = a + (b - a) * (k / (n + 1))
            M.box(P["galv"], p, (0.03 if abs(b.x - a.x) < 0.01 else 0.025, 0.03, 0.03 if abs(b.z - a.z) < 0.01 else 0.025), 0.003)
    for (x, y, z) in meters:
        M.box(P["ivory"], (x, y - 0.02, z), (0.22, 0.14, 0.27), 0.012)
        M.box(P["black"], (x, y - 0.092, z + 0.05), (0.12, 0.006, 0.06), 0.002)
        M.cyl(g, (x - 0.06, y - 0.02, z + 0.135), (x - 0.06, y - 0.02, z + 0.3), r * 0.8, 8)
        M.cyl(g, (x + 0.06, y - 0.02, z + 0.135), (x + 0.06, y - 0.02, z + 0.3), r * 0.8, 8)


def downpipe(M, P, x, y, z_top, z_bot=0.08, r=0.05, out=(0, -1)):
    """선홈통: 벽 따라 내려오는 회색 PVC + 브래킷 + 아래 꺾임."""
    m = P["pipe"]
    M.cyl(m, (x, y, z_bot + 0.25), (x, y, z_top), r, 14)
    M.sphere(m, (x, y, z_bot + 0.25), r * 1.02, 12)
    M.cyl(m, (x, y, z_bot + 0.25), (x + out[0] * 0.18, y + out[1] * 0.18, z_bot), r, 14)
    M.cyl(m, (x, y, z_top - 0.02), (x, y, z_top + 0.12), r * 1.25, 14)
    z = z_bot + 0.9
    while z < z_top - 0.3:
        M.torus(P["galv"], (x, y, z), (0, 0, 1), r + 0.006, 0.006, 16, 4)
        M.box(P["galv"], (x, y + r + 0.02, z), (0.025, 0.05, 0.02), 0.002)
        z += 1.8


def cctv(M, P, loc, rz=0.0):
    old = M.at(loc, rz)
    w, b = P["pvc"], P["black"]
    M.box(w, (0, -0.02, 0), (0.12, 0.04, 0.16), 0.01)
    M.cyl(w, (0, -0.04, 0.0), (0, -0.16, -0.04), 0.018, 10)
    M.box(w, (0, -0.24, -0.06), (0.09, 0.22, 0.085), 0.02, 3, rot=(0.25, 0, 0))
    M.box(w, (0, -0.26, -0.02), (0.11, 0.26, 0.01), 0.004, 1, rot=(0.25, 0, 0))
    M.cyl(b, (0, -0.35, -0.085), (0, -0.37, -0.09), 0.03, 16)
    M.T = old


def signbox(M, P, frame_m, face_m, item, c, w, h, depth=0.22, lit=True):
    """돌출 없는 정면 간판 (갈바 프레임 + 앞면 그림). c = 앞면 중심, 정면 -Y."""
    x, y, z = c
    M.box(frame_m, (x, y + depth / 2, z), (w + 0.06, depth, h + 0.06), 0.012)
    M.quad(face_m, (x, y - 0.004, z), (1, 0, 0), (0, 0, 1), w, h, item=item)
    for sx in (-w / 2 + 0.25, w / 2 - 0.25):
        M.box(P["steel"], (sx, y + depth + 0.03, z + h / 2 + 0.04), (0.04, 0.08, 0.04), 0.003)


def shutter(M, P, shut_m, x0, x1, y, z_top, z_down, box_h=0.38):
    """롤 셔터: 셔터 박스 + 가이드 레일 + (내려온 만큼) 셔터 판 + 하부 바."""
    w = x1 - x0
    M.box(P["galv"], ((x0 + x1) / 2, y + 0.12, z_top + box_h / 2), (w + 0.1, 0.34, box_h), 0.01)
    M.box(P["galv"], ((x0 + x1) / 2, y - 0.045, z_top + box_h - 0.02), (w + 0.12, 0.03, 0.04), 0.004)
    for x in (x0 - 0.03, x1 + 0.03):
        M.box(P["galv"], (x, y + 0.06, z_top / 2), (0.06, 0.1, z_top), 0.004)
        M.box(P["steel"], (x, y + 0.015, z_top / 2), (0.075, 0.012, z_top), 0.002)
    if z_down < z_top - 0.05:
        f = M.quad(shut_m, ((x0 + x1) / 2, y + 0.06, (z_top + z_down) / 2), (1, 0, 0), (0, 0, 1), w, z_top - z_down)
        M.box(P["galv"], ((x0 + x1) / 2, y + 0.06, z_down + 0.04), (w, 0.07, 0.08), 0.008)
        for hx in ((x0 + x1) / 2 - 0.3, (x0 + x1) / 2 + 0.3):
            M.box(P["sus"], (hx, y + 0.01, z_down + 0.05), (0.12, 0.03, 0.025), 0.004)
            M.box(P["rust"], (hx + 0.08, y + 0.015, z_down + 0.045), (0.03, 0.03, 0.05), 0.004)


def awning(M, P, item, gm, x0, x1, z_top, y, proj=1.1, drop=0.7, valance=0.22):
    """차양막: 비스듬한 천 + 앞 드림 + 접이식 팔. item = 줄무늬 아틀라스 항목."""
    w = x1 - x0
    a = Vector(((x0 + x1) / 2, y, z_top))
    f = a + Vector((0, -proj, -drop))
    mid = (a + f) / 2
    up = (a - f).normalized()
    M.quad(gm, mid, (1, 0, 0), up, w, (a - f).length, item=item[0])
    M.quad(gm, f + Vector((0, 0, -valance / 2)), (1, 0, 0), (0, 0, 1), w, valance, item=item[1])
    M.box(P["alu"], (a.x, y + 0.04, z_top + 0.02), (w + 0.06, 0.08, 0.08), 0.01)
    M.cyl(P["alu"], (x0, f.y, f.z), (x1, f.y, f.z), 0.02, 10)
    for x in (x0 + 0.15, x1 - 0.15):
        M.path(P["alu"], [(x, y, z_top - 0.55), (x, (y + f.y) / 2, (z_top - 0.55 + f.z) / 2 - 0.05), (x, f.y + 0.02, f.z)], 0.014, 8)


# ---------------------------------------------------------------- 마무리

def finish(asset, M, *, atlases=(), bake_size=2048, notes="", children=(), sockets=(), fp=None, ao=0.25, samples=48):
    """아틀라스 그리기 -> 오브젝트 생성 -> 스무스/가중 노멀 -> 굽기 -> 내보내기 -> 미리보기."""
    draw(atlases)
    ob = M.to_object(asset)
    kids = []
    for (cname, CM, loc) in children:
        c = CM.to_object(cname)
        c.location = loc
        for p in c.data.polygons:
            p.use_smooth = True
        c.data.set_sharp_from_angle(angle=math.radians(46))
        c.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True
        kids.append(c)
    children = kids
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.set_sharp_from_angle(angle=math.radians(46))
    wn = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
    wn.weight = 50
    keep = tuple(m.name for m in ob.data.materials if m and m.name.startswith(f"M_{asset}_"))
    for c in children:
        c.parent = ob
    for name, loc, rot in sockets:
        e = bpy.data.objects.new(f"{asset}_Socket_{name}", None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.2
        e.location = loc
        e.rotation_euler = rot
        bpy.context.scene.collection.objects.link(e)
        e.parent = ob
    k3d.bake(ob, size=bake_size, keep=keep, ao_distance=ao, samples=samples)
    for c in children:
        if c.type == "MESH" and any(s.material and not s.material.name.startswith(("M_Glass", "M_Dyn", "M_Tile", f"M_{asset}_"))
                                    for s in c.material_slots):
            k3d.bake(c, size=512, keep=tuple(s.material.name for s in c.material_slots if s.material and s.material.name.startswith(f"M_{asset}_")),
                     ao_distance=0.05, samples=32)
    k3d.export(asset, "Buildings", [ob], notes=notes)
    paths = k3d.preview(asset, [ob])
    if fp:
        paths += shot(asset, [ob], *fp)
    return ob, paths


def shot(asset, objs, cam_loc, target, lens=24, tag="fp", res=(1600, 1000)):
    """사람 눈높이 카메라 한 장 (k3d.preview 조명과 비슷하게)."""
    sc = bpy.context.scene
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("bld_shot")
    if w.node_tree is None:
        w.use_nodes = True
    wn = w.node_tree.nodes
    bg = next((n for n in wn if n.type == "BACKGROUND"), None)
    if bg is None:
        bg = wn.new("ShaderNodeBackground")
        wo = next((n for n in wn if n.type == "OUTPUT_WORLD"), None) or wn.new("ShaderNodeOutputWorld")
        w.node_tree.links.new(bg.outputs[0], wo.inputs["Surface"])
    bg.inputs["Color"].default_value = (0.62, 0.68, 0.76, 1)
    bg.inputs["Strength"].default_value = 0.7
    old = sc.world
    sc.world = w
    tmp = []
    ld = bpy.data.lights.new("bld_sun", "SUN")
    ld.energy = 3.2
    ld.angle = 0.05
    lo = bpy.data.objects.new("bld_sun", ld)
    lo.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(lo)
    tmp.append(lo)
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.002))
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("bld_ground", (0.3, 0.3, 0.31), 0.85))
    tmp.append(g)
    cd = bpy.data.cameras.new("bld_cam")
    cd.lens = lens
    cd.clip_start, cd.clip_end = 0.05, 400
    cam = bpy.data.objects.new("bld_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    tmp.append(cam)
    p = os.path.join(k3d.SRC, "Previews", f"{asset}_{tag}_0.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.world = old
    return [p]


# ================================================================ 건물 공통 (2차 추가: 껍데기·점포·간판)
# 좌표: 원점 = 도로 쪽 정면 벽 아래 중앙 (x 가운데, y=0 이 정면 벽면, 건물은 +Y 로 깊어진다).

TILES = {   # 이름: (Poly Haven id, 타일 크기 m (API dimensions), 해상도, tint)
    "RedBrick": ("red_brick", 1.4, "2k", None),
    "FacadeGrey": ("rectangular_facade_tiles", 2.0, "1k", None),
    "FacadeBrown": ("rectangular_facade_tiles_02", 2.105, "2k", None),
    "LongTileCream": ("long_white_tiles", 1.27, "2k", None),
    "Plaster": ("painted_plaster_wall", 2.0, "1k", None),
    "Concrete": ("dirty_concrete", 3.0, "1k", None),
    "Shutter": ("painted_metal_shutter", 2.0, "2k", None),
}


def T(name):
    ph, tm, res, tint = TILES[name]
    return tile(name, ph, tm, res=res, tint=tint)


def shell(M, W, D, H, front, side=None, back=None, roof=None, reveal=None, coping=None, par=0.8,
          holes=(), lholes=(), rholes=(), thick=0.3, t=0.2):
    """닫힌 상자 건물: 앞(-Y)/옆/뒤 벽 + 옥상 + 파라펫 안쪽 + 두겁. holes 는 앞벽 (u = x + W/2, v = z).
    lholes = 왼쪽 벽 (u = D - y), rholes = 오른쪽 벽 (u = y). 반환: 파라펫 위 높이."""
    side = side or front
    back = back or side
    roof = roof or back
    reveal = reveal or back
    coping = coping or reveal
    HT = H + par
    M.wall(front, (-W / 2, 0, 0), (1, 0, 0), (0, 0, 1), W, HT, holes, thick, reveal_m=reveal)
    M.wall(side, (-W / 2, D, 0), (0, -1, 0), (0, 0, 1), D, HT, lholes, thick, reveal_m=reveal)
    M.wall(side, (W / 2, 0, 0), (0, 1, 0), (0, 0, 1), D, HT, rholes, thick, reveal_m=reveal)
    M.wall(back, (W / 2, D, 0), (-1, 0, 0), (0, 0, 1), W, HT, (), thick)
    if par > 0.05:
        M.quad(roof, (0, D / 2, H), (1, 0, 0), (0, 1, 0), W - 2 * t, D - 2 * t)
        for c, r, w in (((0, t, H + par / 2), (-1, 0, 0), W - 2 * t), ((0, D - t, H + par / 2), (1, 0, 0), W - 2 * t),
                        ((-W / 2 + t, D / 2, H + par / 2), (0, 1, 0), D - 2 * t), ((W / 2 - t, D / 2, H + par / 2), (0, -1, 0), D - 2 * t)):
            M.quad(reveal, c, r, (0, 0, 1), w, par)
        for c, s in (((0, t / 2, HT + 0.03), (W + 0.07, t + 0.07, 0.06)), ((0, D - t / 2, HT + 0.03), (W + 0.07, t + 0.07, 0.06)),
                     ((-W / 2 + t / 2, D / 2, HT + 0.03), (t + 0.07, D - t - 0.07, 0.06)),
                     ((W / 2 - t / 2, D / 2, HT + 0.03), (t + 0.07, D - t - 0.07, 0.06))):
            M.box(coping, c, s, 0.012, 2)
    else:
        M.quad(roof, (0, D / 2, HT), (1, 0, 0), (0, 1, 0), W, D)
    return HT


def bands(M, m, W, zs, h=0.16, proj=0.09, x0=None, x1=None):
    """층 슬래브 띠 (정면)."""
    x0 = -W / 2 - 0.02 if x0 is None else x0
    x1 = W / 2 + 0.02 if x1 is None else x1
    for z in zs:
        M.box(m, ((x0 + x1) / 2, -proj / 2, z), (x1 - x0, proj, h), 0.012, 2)


def fwin(M, P, W, x, z, w, h, **kw):
    """정면 벽 창 (x = 창 중심, z = 창 아래). shell 의 holes 와 같은 값을 쓴다."""
    u0 = x - w / 2 + W / 2
    window(M, P, None, (-W / 2, 0, 0), (1, 0, 0), (0, 0, 1), u0, u0 + w, z, z + h, **kw)


def fhole(W, x, z, w, h):
    u0 = x - w / 2 + W / 2
    return (u0, u0 + w, z, z + h)


def grime_spec(W, HT, holes, drips=(), strength=0.8, seed=1):
    """정면 덮개 때 텍스처 항목 (개구부 투명, 창대 아래 빗물 자국)."""
    hs = [(u0 / W, 1 - v1 / HT, u1 / W, 1 - v0 / HT) for (u0, u1, v0, v1) in holes]
    sills = [(u0 / W - 0.005, u1 / W + 0.005, 1 - v0 / HT + 0.004, 0.07 + 0.05 * rnd.random()) for (u0, u1, v0, v1) in holes if v0 > 0.5]
    return dict(kind="grime", holes=hs, sills=sills, drips=list(drips), strength=strength, seed=seed)


class SubUV:
    """아틀라스 항목 안의 부분 사각형 (a,b,c,d = 항목 기준 0..1, 아래 왼쪽 원점). pack 뒤에 계산."""
    def __init__(self, item, a, b, c, d):
        self.item, self.r = item, (a, b, c, d)

    def uv(self):
        u0, v0, u1, v1 = self.item.uv()
        a, b, c, d = self.r
        return (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b, u0 + (u1 - u0) * c, v0 + (v1 - v0) * d)


def grime_wall(M, m, item, W, HT, holes, y=-0.012):
    """정면 때 덮개: 개구부를 잘라낸 띠들 (투명 면이 창·점포 안에 그림자를 드리우지 않게).
    holes = grime_spec 에 넘긴 목록 (u = x + W/2, v = z). 벽에서 12mm 띄운다."""
    us = sorted({0.0, W, *[min(max(v, 0.0), W) for h in holes for v in h[:2]]})
    vs = sorted({0.0, HT, *[min(max(v, 0.0), HT) for h in holes for v in h[2:]]})
    for c, d in zip(vs, vs[1:]):
        if d - c < 1e-4:
            continue
        vc = (c + d) / 2
        runs = []
        for a, b in zip(us, us[1:]):
            if b - a < 1e-4 or any(h[0] < (a + b) / 2 < h[1] and h[2] < vc < h[3] for h in holes):
                continue
            if runs and abs(runs[-1][1] - a) < 1e-6:
                runs[-1][1] = b      # 이웃 칸은 한 띠로 합친다
            else:
                runs.append([a, b])
        for a, b in runs:
            M.quad(m, (-W / 2 + (a + b) / 2, y, vc), (1, 0, 0), (0, 0, 1), b - a, d - c,
                   item=SubUV(item, a / W, c / HT, b / W, d / HT))


def stripe_cyl(M, m, c, r, h, seg=24):
    """UV 가 둘러 감긴 원기둥 옆면 (이발소 회전등). 면마다 고정 UV (u 0..1 둘레, v 0..1 높이)."""
    x, y, z = c
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        # 바깥에서 볼 때 왼쪽 아래 -> 오른쪽 아래 -> 오른쪽 위 -> 왼쪽 위 (법선 바깥)
        p = [(x + r * math.cos(a0), y + r * math.sin(a0), z), (x + r * math.cos(a1), y + r * math.sin(a1), z),
             (x + r * math.cos(a1), y + r * math.sin(a1), z + h), (x + r * math.cos(a0), y + r * math.sin(a0), z + h)]
        f = M.poly(m, p)
        M.fixed.append((f, (i / seg, 0.0, (i + 1) / seg, 1.0)))


def shopfront(M, P, x0, x1, *, glass_m, room_m, floor_m, inner=None, inner_m=None, door=0.5, z_open=2.4,
              room_d=3.2, frame="alu", shut_m=None, shut_down=None, door_item=None, decal_m=None,
              posters=(), lights=True):
    """1층 점포 앞면 (벽 구멍 x0..x1, 0..z_open 은 shell 이 뚫는다): 얕은 실내 + 유리 커튼월 + 여닫이문 + 셔터."""
    fm = P[frame]
    w = x1 - x0
    xc = (x0 + x1) / 2
    yg = 0.14                                   # 유리면
    # 실내: 바닥, 천장, 옆벽, 뒤 카드
    M.quad(floor_m, (xc, room_d / 2, 0.004), (1, 0, 0), (0, 1, 0), w, room_d)
    M.quad(room_m, (xc, (0.3 + room_d) / 2, z_open), (1, 0, 0), (0, -1, 0), w, room_d - 0.3)
    M.quad(room_m, (x0, (0.3 + room_d) / 2, z_open / 2), (0, 1, 0), (0, 0, 1), room_d - 0.3, z_open)
    M.quad(room_m, (x1, (0.3 + room_d) / 2, z_open / 2), (0, -1, 0), (0, 0, 1), room_d - 0.3, z_open)
    if inner is not None:
        M.quad(inner_m, (xc, room_d, z_open / 2), (1, 0, 0), (0, 0, 1), w, z_open, item=inner)
    if lights:
        n = max(1, int(round(w / 2.0)))
        for k in range(n):
            lx = x0 + (k + 0.5) * w / n
            for ly in (1.0, 2.3):
                M.box(P["pvc"], (lx, ly, z_open - 0.02), (1.25, 0.1, 0.04), 0.008)
                M.box(P["light"], (lx, ly, z_open - 0.045), (1.18, 0.05, 0.012), 0.003, 1)
    # 하부 걸레받이(화강석) + 상부 가로대 + 세로 멀리언
    M.box(P["granite"], (xc, yg + 0.02, 0.2), (w, 0.16, 0.4), 0.01)
    M.box(fm, (xc, yg, z_open - 0.04), (w, 0.1, 0.08), 0.006)
    M.box(fm, (xc, yg, 0.43), (w, 0.1, 0.06), 0.006)
    dw = 0.95
    xd = x0 + w * door
    xd = min(max(xd, x0 + dw / 2 + 0.05), x1 - dw / 2 - 0.05)
    nm = max(1, int(round((w - dw) / 1.6)))
    cuts = sorted({x0, x1, xd - dw / 2, xd + dw / 2} | {x0 + (w) * k / (nm + 1) for k in range(1, nm + 1)})
    cuts = [c for c in cuts if not (xd - dw / 2 + 0.05 < c < xd + dw / 2 - 0.05)]
    for c in cuts:
        M.box(fm, (min(max(c, x0 + 0.035), x1 - 0.035), yg, z_open / 2), (0.07, 0.11, z_open), 0.006)
    for a, b in zip(cuts, cuts[1:]):
        if b - a < 0.1 or (a >= xd - dw / 2 - 0.01 and b <= xd + dw / 2 + 0.01):
            continue
        M.quad(glass_m, ((a + b) / 2, yg, (0.46 + z_open - 0.08) / 2), (1, 0, 0), (0, 0, 1), b - a - 0.07, z_open - 0.54)
    # 문: 틀 + 유리 + 손잡이 + 바닥 힌지
    dz = 2.15
    M.box(fm, (xd, yg - 0.01, dz - 0.04), (dw, 0.06, 0.08), 0.005)
    M.box(fm, (xd, yg - 0.01, 0.06), (dw, 0.06, 0.12), 0.005)
    for sx in (-1, 1):
        M.box(fm, (xd + sx * (dw / 2 - 0.035), yg - 0.01, dz / 2), (0.07, 0.06, dz), 0.005)
    M.box(fm, (xd, yg + 0.02, (dz + z_open) / 2), (dw, 0.08, z_open - dz), 0.004)
    M.quad(glass_m, (xd, yg - 0.01, (0.12 + dz - 0.08) / 2), (1, 0, 0), (0, 0, 1), dw - 0.14, dz - 0.2)
    hx = xd + dw / 2 - 0.14
    for sy in (-0.07, 0.05):
        M.cyl(P["sus"], (hx, yg - 0.01 + sy, 0.75), (hx, yg - 0.01 + sy, 1.35), 0.014, 10)
        for hz in (0.8, 1.3):
            M.cyl(P["sus"], (hx, yg - 0.01, hz), (hx, yg - 0.01 + sy, hz), 0.009, 6)
    M.box(P["black"], (xd - dw / 2 + 0.1, yg - 0.01, dz + 0.02), (0.3, 0.06, 0.05), 0.006)   # 도어클로저
    if door_item is not None:
        M.quad(decal_m, (xd + 0.12, yg - 0.045, 1.18), (1, 0, 0), (0, 0, 1), 0.3, 0.1, item=door_item)
    for (it, px, pz, pw, ph) in posters:    # 유리 안쪽에 붙인 종이/시트 (유리 2cm 뒤)
        M.quad(decal_m, (px, yg + 0.02, pz), (1, 0, 0), (0, 0, 1), pw, ph, item=it)
    if shut_m is not None:
        shutter(M, P, shut_m, x0, x1, -0.05, z_open, z_open if shut_down is None else shut_down)
    return xd


def vsign(M, P, frame_m, face_m, item, x, z0, proj=0.62, h=5.2, th=0.2, gap=0.12):
    """벽에서 튀어나온 세로 돌출 간판 (양면). x = 간판 중심 x, z0 = 아래 끝. 정면 벽(y=0)에 붙는다."""
    yc = -(gap + proj / 2)
    M.box(frame_m, (x, yc, z0 + h / 2), (th, proj + 0.05, h + 0.05), 0.012)
    M.quad(face_m, (x + th / 2 + 0.004, yc, z0 + h / 2), (0, 1, 0), (0, 0, 1), proj, h, item=item)
    M.quad(face_m, (x - th / 2 - 0.004, yc, z0 + h / 2), (0, -1, 0), (0, 0, 1), proj, h, item=item)
    for z in (z0 + 0.4, z0 + h - 0.4):
        M.box(P["steel"], (x, -gap / 2 - 0.01, z), (0.06, gap + 0.04, 0.06), 0.004)
        M.box(P["steel"], (x, -0.006, z), (0.14, 0.012, 0.14), 0.002)


def address_plate(M, P, m, item, x, z, y=0.0, w=0.45, h=0.15, normal=(0, -1, 0)):
    """도로명주소 건물번호판 (얇은 판 + 앞면)."""
    if normal[1] < 0:
        M.box(P["alu"], (x, y - 0.008, z), (w + 0.01, 0.014, h + 0.01), 0.003, 1)
        M.quad(m, (x, y - 0.0155, z), (1, 0, 0), (0, 0, 1), w, h, item=item)
    else:   # 왼쪽 옆 벽 (-X)
        M.box(P["alu"], (x - 0.008, y, z), (0.014, w + 0.01, h + 0.01), 0.003, 1)
        M.quad(m, (x - 0.0155, y, z), (0, -1, 0), (0, 0, 1), w, h, item=item)


def mats(asset, sign_atlas=None, decal_atlas=None, inner_atlas=None, grime_atlas=None, inner_emit=0.25, sign_emit=0.12):
    """에셋 전용 비굽기 머티리얼 묶음."""
    d = dict(glass=glass(asset, "Window", (0.045, 0.055, 0.06), 0.42, 0.04),
             shopglass=glass(asset, "Shop", (0.10, 0.12, 0.12), 0.16, 0.03),
             screen=glass(asset, "Screen", (0.05, 0.05, 0.05), 0.55, 0.6))
    if sign_atlas:
        d["sign"] = flat_img(f"M_{asset}_Sign", sign_atlas.path, 0.45, emit=sign_emit)
    if decal_atlas:
        d["decal"] = flat_img(f"M_{asset}_Decal", decal_atlas.path, 0.5, alpha_clip=0.5)
        d["decal2"] = flat_img(f"M_{asset}_DecalDS", decal_atlas.path, 0.8, alpha_clip=0.5, double_sided=True)
    if inner_atlas:
        d["inner"] = flat_img(f"M_{asset}_Interior", inner_atlas.path, 0.8, emit=inner_emit)
    if grime_atlas:
        d["grime"] = flat_img(f"M_{asset}_Grime", grime_atlas.path, 0.9, transparent=True)
    return d


def tex2d_font(k):
    """3D 글자용 폰트 경로 (tex2d.FONT 와 같은 파일)."""
    return {"black": os.path.join(k3d.CACHE, "fonts", "Pretendard-Black.otf")}[k]

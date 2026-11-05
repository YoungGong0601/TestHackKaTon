"""행인/뒤 손님 NPC 공용 빌더 (그룹 npc_a).

원본 Quaternius GLB 의 리그·스킨 웨이트·애니메이션을 그대로 쓰고
메시 정리(병합·서브디비전) + 옷/소품 + 절차 머티리얼(구워서 1세트) + 새 루프 클립을 만든다.
에셋 스크립트(NpcOfficeMan.py 등)가 build(설정) 을 부른다.
"""
import bpy, bmesh, math, os, sys, subprocess
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import k3d

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # ArtSource
GLB = os.path.join(ROOT, "_ref", "models")
DECAL = os.path.join(ROOT, "_cache", "npca")
VENV_PY = k3d.PY
KEEP_CLIPS = ("Idle", "Walk", "Run", "Sitting", "Clapping")
FPS = 24


def decals():
    if not os.path.exists(os.path.join(DECAL, "T_NpcSmartphone_Screen.png")):
        subprocess.run([VENV_PY, os.path.join(HERE, "npc_decals.py"), DECAL], check=True)
    return DECAL


# ---------------------------------------------------------------- 리그/메시 불러오기

def fcurves(act):
    out = []
    for l in act.layers:
        for s in l.strips:
            for cb in s.channelbags:
                out += list(cb.fcurves)
    return out


def load(glb, asset):
    """GLB -> (arm, body). 루트/잔여 오브젝트 제거, 필요 없는 클립 삭제, 클립 이름 정리."""
    k3d.reset()
    bpy.context.scene.render.fps = FPS
    objs = k3d.import_glb(os.path.join(GLB, glb + ".glb"))
    arm = next(o for o in objs if o.type == 'ARMATURE')
    body = next(o for o in objs if o.type == 'MESH' and o.parent == arm)
    # 임포트 직후 포즈 = glTF 노드 기본값. 클립에 키가 없는 본은 원래 이 값을 쓴다 (three.js 와 동일)
    raw = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones}
    mw = arm.matrix_world.copy()
    for o in objs:
        if o not in (arm, body):
            bpy.data.objects.remove(o)
    arm.matrix_world = mw
    ad = arm.animation_data
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    ad.action = None
    for a in list(bpy.data.actions):
        short = a.name.split("|")[-1].split("_", 1)[-1]          # HumanArmature|Man_Idle -> Idle
        if short in KEEP_CLIPS:
            a.name = short
            a.use_fake_user = False
        else:
            bpy.data.actions.remove(a)
    complete_actions(arm, raw)
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix()
    arm.name = arm.data.name = asset + "_Rig"
    body.name = body.data.name = asset + "_Body"
    return arm, body


def complete_actions(arm, raw):
    """클립마다 키 없는 본 채널을 기본 포즈 값으로 채운다 (FBX/Unity 에서 T포즈로 튀는 것 방지)."""
    ad = arm.animation_data
    for a in bpy.data.actions:
        ad.action = a
        ad.action_slot = a.slots[0]
        f0, f1 = a.frame_range
        have = {(fc.data_path, fc.array_index) for fc in fcurves(a)}
        for name, (loc, rot) in raw.items():
            for prop, vals in (("location", loc), ("rotation_quaternion", rot)):
                dp = f'pose.bones["{name}"].{prop}'
                for i, v in enumerate(vals):
                    if (dp, i) not in have:
                        fc = a.fcurve_ensure_for_datablock(arm, dp, index=i, group_name=name)
                        fc.keyframe_points.insert(f0, v)
                        fc.keyframe_points.insert(f1, v)
    ad.action = None


def xform_rig(arm, body, M):
    """리그+메시에 월드 변환 M(균일 스케일 포함)을 '적용'한다. 위치 키는 스케일 비율만큼 곱해 애니메이션을 유지."""
    Wa, Wb = arm.matrix_world.copy(), body.matrix_world.copy()
    k = (M @ Wa).to_scale()[0]
    body.parent = None
    body.data.transform(M @ Wb)
    arm.data.transform(M @ Wa)
    arm.matrix_world = Matrix()
    body.matrix_world = Matrix()
    body.parent = arm
    body.matrix_parent_inverse = Matrix()
    if abs(k - 1) > 1e-6:
        for a in bpy.data.actions:
            for fc in fcurves(a):
                if fc.data_path.endswith(".location"):
                    for kp in fc.keyframe_points:
                        kp.co.y *= k
                        kp.handle_left.y *= k
                        kp.handle_right.y *= k
    return k


def rest_bounds(arm, body):
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    vs = [v.co for v in body.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx


def bone_head(arm, name):
    return arm.data.bones[name].head_local.copy()


def clean_mesh(body):
    """평면 셰이딩용으로 쪼개진 정점 병합, 커스텀 노멀/샤프 제거, 삼각형 -> 사각형."""
    k3d.select([body])
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception as e:
        print("npc: custom normal clear 생략", e)
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)
    bmesh.ops.join_triangles(bm, faces=bm.faces, angle_face_threshold=math.radians(40),
                             angle_shape_threshold=math.radians(40), cmp_materials=True)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    for a in ("sharp_edge", "sharp_face"):
        if a in me.attributes:
            me.attributes.remove(me.attributes[a])


def subdivide(body, levels=1):
    """Subdivision 을 Armature 앞에 두고 적용 -> 웨이트 보간 유지."""
    m = body.modifiers.new("Subd", 'SUBSURF')
    m.levels = m.render_levels = levels
    m.boundary_smooth = 'ALL'
    k3d.select([body])
    bpy.ops.object.modifier_move_to_index(modifier="Subd", index=0)
    bpy.ops.object.modifier_apply(modifier="Subd")
    for p in body.data.polygons:
        p.use_smooth = True


# ---------------------------------------------------------------- 면/재질 도우미

def slot(body, mat):
    names = [m.name if m else None for m in body.data.materials]
    if mat.name not in names:
        body.data.materials.append(mat)
        names.append(mat.name)
    return names.index(mat.name)


def faces(body, pred):
    """pred(center, normal, matname) 이 참인 면 인덱스."""
    mats = [m.name if m else "" for m in body.data.materials]
    return [p.index for p in body.data.polygons if pred(p.center, p.normal, mats[p.material_index])]


def set_mat(body, idx, mat):
    i = slot(body, mat)
    for f in idx:
        body.data.polygons[f].material_index = i


def push(body, idx, dist):
    """면 묶음의 정점을 노멀 방향으로 밀어 옷 두께/패딩을 만든다."""
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.faces.ensure_lookup_table()
    vs = {v for f in idx for v in bm.faces[f].verts}
    for v in vs:
        v.co += v.normal * dist
    bm.to_mesh(body.data)
    bm.free()


# ---------------------------------------------------------------- 절차 머티리얼

class G:
    """노드 그래프 짧게 쓰기."""

    def __init__(self, name):
        m = bpy.data.materials.get(name)
        if m:
            m.name = name + "_old"
        self.m = bpy.data.materials.new(name)
        self.nt = k3d._nodes(self.m)
        self.p = k3d.principled(self.m)
        self.co = self.n('ShaderNodeTexCoord').outputs['Object']

    def n(self, typ, props=None, **ins):
        nd = self.nt.nodes.new(typ)
        for k, v in (props or {}).items():
            setattr(nd, k, v)
        for k, v in ins.items():
            self.set(nd.inputs[k.replace("_", " ")], v)
        return nd

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
        elif isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], sock)
        elif sock.type == 'RGBA':
            sock.default_value = (*v[:3], 1)
        elif sock.type == 'VECTOR':
            sock.default_value = v
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0, clamp=False):
        nd = self.nt.nodes.new('ShaderNodeMath')
        nd.operation = op
        nd.use_clamp = clamp
        self.set(nd.inputs[0], a)
        self.set(nd.inputs[1], b)
        return nd.outputs[0]

    def mix(self, fac, a, b, blend='MIX'):
        nd = self.nt.nodes.new('ShaderNodeMix')
        nd.data_type, nd.blend_type = 'RGBA', blend
        ins = [s for s in nd.inputs if s.enabled]
        self.set(ins[0], fac)
        self.set(ins[1], a)
        self.set(ins[2], b)
        return next(s for s in nd.outputs if s.enabled)

    def vmap(self, scale=(1, 1, 1), rot=(0, 0, 0), vec=None):
        nd = self.nt.nodes.new('ShaderNodeMapping')
        self.set(nd.inputs['Vector'], vec or self.co)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Rotation'].default_value = rot
        return nd.outputs[0]

    def noise(self, scale, detail=2.0, rough=0.5, vec=None, distort=0.0):
        nd = self.n('ShaderNodeTexNoise', Scale=scale, Detail=detail, Roughness=rough, Distortion=distort)
        self.set(nd.inputs['Vector'], vec or self.co)
        return nd.outputs['Fac']

    def wave(self, period, axis='X', vec=None, distort=0.0, profile='SIN', detail=0.0):
        nd = self.n('ShaderNodeTexWave', {"wave_type": 'BANDS', "bands_direction": axis, "wave_profile": profile},
                    Scale=0.3183 / period, Distortion=distort, Detail=detail)
        self.set(nd.inputs['Vector'], vec or self.co)
        return nd.outputs['Fac']

    def voronoi(self, scale, feature='F1', vec=None):
        nd = self.n('ShaderNodeTexVoronoi', {"feature": feature}, Scale=scale)
        self.set(nd.inputs['Vector'], vec or self.co)
        return nd.outputs['Distance']

    def ramp(self, fac, stops):
        nd = self.nt.nodes.new('ShaderNodeValToRGB')
        self.set(nd.inputs[0], fac)
        el = nd.color_ramp.elements
        while len(el) > len(stops):
            el.remove(el[-1])
        while len(el) < len(stops):
            el.new(0.5)
        for e, (pos, col) in zip(el, stops):
            e.position = pos
            e.color = (*col, 1) if len(col) == 3 else ((col[0],) * 3 + (1,) if len(col) == 1 else col)
        return nd.outputs['Color']

    def xyz(self, vec=None):
        nd = self.n('ShaderNodeSeparateXYZ')
        self.set(nd.inputs[0], vec or self.co)
        return nd.outputs

    def band(self, v, lo, hi, soft=0.002):
        """lo<v<hi 이면 1 (부드러운 경계)."""
        a = self.n('ShaderNodeMapRange', {"interpolation_type": 'SMOOTHSTEP'}, From_Min=lo - soft, From_Max=lo + soft)
        self.set(a.inputs['Value'], v)
        b = self.n('ShaderNodeMapRange', {"interpolation_type": 'SMOOTHSTEP'}, From_Min=hi + soft, From_Max=hi - soft)
        self.set(b.inputs['Value'], v)
        return self.math('MULTIPLY', a.outputs[0], b.outputs[0])

    def ao(self, dist=0.05):
        nd = self.n('ShaderNodeAmbientOcclusion', {"samples": 16}, Distance=dist)
        return nd.outputs['AO']

    def bump(self, height, strength, dist, normal=None):
        nd = self.n('ShaderNodeBump', Strength=strength, Distance=dist)
        self.set(nd.inputs['Height'], height)
        if normal is not None:
            self.set(nd.inputs['Normal'], normal)
        return nd.outputs['Normal']

    def image(self, path):
        # UV 입력을 비워 두면 메시의 첫 UV 를 씀 (GLB 메시 UV 이름이 'Float2' 라 'UVMap' 지정 시 (0,0) 만 읽혔음)
        im = bpy.data.images.load(path, check_existing=True)
        nd = self.n('ShaderNodeTexImage')
        nd.image = im
        return nd.outputs['Color']

    def out(self, color, rough, normal=None, metal=0.0, sheen=0.0, spec=0.5):
        self.set(self.p.inputs['Base Color'], color)
        self.set(self.p.inputs['Roughness'], rough)
        self.set(self.p.inputs['Metallic'], metal)
        if normal is not None:
            self.set(self.p.inputs['Normal'], normal)
        return self.m


def _shade(c, f):
    return tuple(max(0.0, min(1.0, x * f)) for x in c)


def grime(g, col, amount=0.45, dist=0.05, floor_dust=0.0):
    """AO 로 주름/틈 어둡게 + 바닥 근처 먼지."""
    a = g.ramp(g.ao(dist), [(0.0, _shade(col, 1 - amount)), (0.85, col)])
    if floor_dust:
        z = g.xyz()[2]
        d = g.math('MULTIPLY', g.n('ShaderNodeMapRange', From_Min=0.12, From_Max=0.0, Value=z).outputs[0],
                   g.noise(60, 3, 0.6))
        a = g.mix(g.math('MULTIPLY', d, floor_dust), a, (0.36, 0.33, 0.29))
    return a


def cloth(name, col, kind="cotton", rough=0.82, col2=None, wrinkle=1.0, dust=0.0, extra=None, sleeve_x=None):
    """옷감 머티리얼. kind: cotton/fleece/denim/knit/wool/nylon/quilt/plaid/stripe/floral/twill.
    sleeve_x: stripe 에서 |x| 가 이 값(진동 둘레, rest T포즈) 넘는 소매는 팔 둘레 방향 줄무늬."""
    g = G(name)
    co = g.co
    var = g.ramp(g.noise(3.0, 3, 0.55), [(0.35, (0,)), (0.65, (1,))])   # 노이즈 Fac 이 0.5 근처에 몰려 있어 대비를 늘림
    base = g.mix(var, _shade(col, 0.9), _shade(col, 1.1))    # 큰 색 얼룩 ±10%
    mott = g.ramp(g.noise(16, 3, 0.6), [(0.3, (0.94,)), (0.7, (1.05,))])
    base = g.mix(1.0, base, mott, 'MULTIPLY')                # 중간 얼룩 ±5%
    h_fine, s_fine, d_fine = None, 0.0, 0.0
    if kind == "cotton":
        h_fine = g.noise(380, 4, 0.7)
        s_fine, d_fine = 0.25, 0.0006
    elif kind == "fleece":
        mel = g.noise(420, 3, 0.8)
        base = g.mix(g.ramp(mel, [(0.35, (0,)), (0.65, (1,))]), base, _shade(col, 1.25))
        h_fine = g.noise(300, 5, 0.8)
        s_fine, d_fine = 0.3, 0.0008
    elif kind == "denim":
        tw = g.wave(0.0028, 'X', vec=g.vmap(rot=(0, math.radians(40), 0)), distort=0.6)
        fade = g.noise(5.0, 4, 0.6)
        lite = g.ramp(fade, [(0.45, (0,)), (0.75, (1,))])
        base = g.mix(g.math('MULTIPLY', lite, 0.55), base, col2 or _shade(col, 2.1))
        base = g.mix(g.math('MULTIPLY', tw, 0.18), base, (0.7, 0.72, 0.75))
        h_fine = tw
        s_fine, d_fine = 0.35, 0.0006
    elif kind == "knit":
        rib = g.wave(0.0042, 'X', distort=0.3)
        base = g.mix(g.math('MULTIPLY', rib, 0.25), _shade(col, 0.95), base, 'MULTIPLY')
        h_fine = g.math('ADD', rib, g.math('MULTIPLY', g.noise(500, 2), 0.3))
        s_fine, d_fine = 0.55, 0.0012
    elif kind == "wool":
        tw = g.wave(0.0026, 'X', vec=g.vmap(rot=(0, math.radians(-45), 0)), distort=1.0)
        base = g.mix(g.math('MULTIPLY', g.noise(350, 3), 0.25), base, _shade(col, 1.3))
        h_fine = tw
        s_fine, d_fine = 0.25, 0.0005
    elif kind == "nylon":
        # 립스톱: 5mm 격자 굵은 실 + 잔 직조
        grid = g.math('MAXIMUM', g.wave(0.005, 'X', profile='TRI'), g.wave(0.005, 'Z', profile='TRI'))
        h_fine = g.math('ADD', g.ramp(grid, [(0.82, (0,)), (1.0, (1,))]), g.math('MULTIPLY', g.noise(700, 2), 0.25))
        s_fine, d_fine = 0.3, 0.0005
    elif kind == "quilt":
        ch = g.wave(0.075, 'Z', vec=g.vmap(vec=co), profile='SIN')            # 가로 누빔 칸
        seam = g.ramp(ch, [(0.0, (0,)), (0.12, (1,))])
        base = g.mix(g.math('SUBTRACT', 1.0, seam), base, _shade(col, 0.45))
        h_fine = g.math('ADD', g.math('POWER', ch, 0.5), g.math('MULTIPLY', g.noise(90, 3, 0.6), 0.15))
        s_fine, d_fine = 0.6, 0.008
    elif kind == "plaid":
        a = g.wave(0.032, 'X', profile='TRI')
        b = g.wave(0.032, 'Z', profile='TRI')
        la = g.ramp(a, [(0.62, (0,)), (0.68, (1,))])
        lb = g.ramp(b, [(0.62, (0,)), (0.68, (1,))])
        base = g.mix(g.math('MULTIPLY', g.math('ADD', la, lb), 0.5), base, col2)
        thin = g.ramp(g.wave(0.032, 'X', vec=g.vmap(vec=co, scale=(1, 1, 1)), profile='TRI'), [(0.95, (0,)), (0.97, (1,))])
        base = g.mix(g.math('MULTIPLY', thin, 0.6), base, (0.8, 0.75, 0.6))
        h_fine = g.noise(380, 3)
        s_fine, d_fine = 0.2, 0.0005
    elif kind == "stripe":
        sv = None
        if sleeve_x:
            x, y, z = g.xyz()
            ax = g.math('ABSOLUTE', x)
            sm = g.math('GREATER_THAN', ax, sleeve_x)                   # 소매 = 1 (진동 솔기에서 방향이 바뀜)
            t = g.math('ADD', g.math('MULTIPLY', g.math('SUBTRACT', 1.0, sm), z), g.math('MULTIPLY', sm, ax))
            sv = g.n('ShaderNodeCombineXYZ', Z=t).outputs[0]
        st = g.ramp(g.wave(0.016, 'Z', profile='TRI', vec=sv), [(0.48, (0,)), (0.52, (1,))])
        base = g.mix(st, base, col2)
        h_fine = g.noise(380, 3)
        s_fine, d_fine = 0.25, 0.0006
    elif kind == "floral":
        v = g.voronoi(55)
        petal = g.ramp(v, [(0.0, (1,)), (0.22, (1,)), (0.3, (0,))])
        sel = g.noise(55, 0)
        c2 = g.mix(g.ramp(sel, [(0.45, (0,)), (0.55, (1,))]), col2, (0.85, 0.82, 0.75))
        base = g.mix(petal, base, c2)
        h_fine = g.noise(380, 3)
        s_fine, d_fine = 0.2, 0.0005
    elif kind == "poly":
        bw = g.math('MAXIMUM', g.wave(0.0014, 'X', profile='TRI'), g.wave(0.0014, 'Z', profile='TRI'))
        h_fine = g.math('ADD', bw, g.math('MULTIPLY', g.noise(600, 2), 0.3))
        s_fine, d_fine = 0.3, 0.0004
    elif kind == "mesh":
        holes = g.ramp(g.voronoi(260, 'F1'), [(0.0, (0,)), (0.35, (0,)), (0.45, (1,))])
        base = g.mix(g.math('SUBTRACT', 1.0, holes), base, (0.004, 0.004, 0.005))
        h_fine = holes
        s_fine, d_fine = 0.6, 0.001
    elif kind == "twill":
        tw = g.wave(0.003, 'X', vec=g.vmap(rot=(0, math.radians(45), 0)), distort=0.3)
        h_fine = tw
        s_fine, d_fine = 0.3, 0.0005
    if extra:
        base = extra(g, base)
    # 튀어나온 모서리(솔기·밑단 끝)는 닳아 밝게, 오목한 곳은 AO 로 때
    wear = g.ramp(g.n('ShaderNodeNewGeometry').outputs['Pointiness'], [(0.53, (0,)), (0.62, (1,))])
    base = g.mix(g.math('MULTIPLY', wear, 0.3), base, _shade(col, 1.35))
    col_out = g.mix(1.0, base, g.ramp(g.ao(0.06), [(0.0, (0.5,)), (0.9, (1,))]), 'MULTIPLY')
    if dust:
        z = g.xyz()[2]
        d = g.math('MULTIPLY', g.n('ShaderNodeMapRange', From_Min=0.14, From_Max=0.0, Value=z).outputs[0], g.noise(40, 3))
        col_out = g.mix(g.math('MULTIPLY', d, dust), col_out, (0.42, 0.39, 0.34))
    # 주름 (큰 노이즈, 세로로 길게) + 잔결
    wr = g.noise(9, 3, 0.5, vec=g.vmap(scale=(1, 1, 0.45)), distort=0.4)
    nrm = g.bump(wr, 0.35 * wrinkle, 0.012)
    if h_fine is not None:
        nrm = g.bump(h_fine, s_fine, d_fine, nrm)
    r = g.math('ADD', rough - 0.05, g.math('MULTIPLY', g.noise(12, 2), 0.1))
    return g.out(col_out, r, nrm)


def skin(name, tone, face=None):
    g = G(name)
    var = g.ramp(g.noise(18, 3, 0.5), [(0.35, (0,)), (0.65, (1,))])
    base = g.mix(var, _shade(tone, 0.92), (tone[0] * 1.05, tone[1] * 0.96, tone[2] * 0.93))
    blot = g.ramp(g.noise(4, 2, 0.5), [(0.35, (0.95,)), (0.65, (1.04,))])
    base = g.mix(1.0, base, blot, 'MULTIPLY')
    # 귀·코끝·손마디(뾰족한 곳) 붉게
    pt = g.n('ShaderNodeNewGeometry').outputs['Pointiness']
    red = g.ramp(pt, [(0.5, (0,)), (0.6, (1,))])
    base = g.mix(g.math('MULTIPLY', red, 0.6), base, (tone[0] * 0.95, tone[1] * 0.6, tone[2] * 0.58))
    if face:
        base = face(g, base)
    base = g.mix(1.0, base, g.ramp(g.ao(0.03), [(0.0, (0.6,)), (0.9, (1,))]), 'MULTIPLY')
    nrm = g.bump(g.noise(700, 3, 0.7), 0.12, 0.0003)
    r = g.math('ADD', 0.48, g.math('MULTIPLY', g.noise(25, 2), 0.14))
    return g.out(base, r, nrm)


def hair(name, col, style="straight", grey=0.0, grey_top=None):
    """grey_top=z 이면 그 높이 위(정수리)에 흰머리를 섞는다 (염색 뿌리)."""
    g = G(name)
    if style == "curly":
        # 뽀글 파마: 1.5~2cm 컬 덩어리(Voronoi F1 돔) + 덩어리 안 잔 컬 + 덩어리 사이 깊게
        clump = g.voronoi(55, 'F1')
        small = g.voronoi(170, 'F1')
        h = g.math('ADD', g.ramp(clump, [(0.0, (1,)), (0.6, (0,))]),
                   g.math('MULTIPLY', g.ramp(small, [(0.0, (1,)), (0.6, (0,))]), 0.35))
        s, d = 1.0, 0.006
    elif style == "fine":
        # 가는 결: 세로로 늘인 고주파 노이즈 + 약한 덩어리 (굵은 밧줄 무늬 방지)
        h = g.math('ADD', g.noise(900, 3, 0.6, vec=g.vmap(scale=(1, 1, 0.05))),
                   g.math('MULTIPLY', g.noise(70, 2, 0.5, vec=g.vmap(scale=(1, 1, 0.2))), 0.4))
        s, d = 0.3, 0.0005
    else:
        h = g.wave(0.0016, 'X', distort=6.0, detail=3.0, vec=g.vmap(scale=(1, 1, 0.25)))
        s, d = 0.6, 0.0008
    strand = g.noise(260, 4, 0.7, vec=g.vmap(scale=(1, 1, 0.12)))
    base = g.mix(g.ramp(strand, [(0.3, (0,)), (0.7, (1,))]), _shade(col, 0.7), _shade(col, 1.35))
    if style == "curly":
        base = g.mix(1.0, base, g.ramp(clump, [(0.25, (1,)), (0.75, (0.35,))]), 'MULTIPLY')   # 덩어리 사이 그늘
    if grey:
        salt = g.ramp(g.noise(700, 2, 0.5, vec=g.vmap(scale=(1, 1, 0.2))), [(0.5 - grey * 0.3, (0,)), (0.56 - grey * 0.3, (1,))])
        base = g.mix(salt, base, (0.55, 0.55, 0.56))
    if grey_top is not None:
        top = g.n('ShaderNodeMapRange', From_Min=grey_top, From_Max=grey_top + 0.03, Value=g.xyz()[2]).outputs[0]
        salt = g.ramp(g.noise(600, 2, 0.5), [(0.6, (0,)), (0.64, (1,))])
        base = g.mix(g.math('MULTIPLY', top, salt), base, (0.42, 0.4, 0.38))
    base = g.mix(1.0, base, g.ramp(g.ao(0.04), [(0.0, (0.35,)), (0.9, (1,))]), 'MULTIPLY')
    nrm = g.bump(h, s, d)
    r = g.math('ADD', 0.42, g.math('MULTIPLY', strand, 0.15))
    return g.out(base, r, nrm)


def leather(name, col, rough=0.38, sole=None, sole_h=0.022, canvas=False):
    """구두/운동화. sole=(색) 이면 바닥 높이 아래를 고무 밑창으로."""
    g = G(name)
    base = g.mix(g.noise(30, 3), _shade(col, 0.85), _shade(col, 1.12))
    if canvas:
        h = g.math('ADD', g.wave(0.0035, 'X', profile='TRI'), g.wave(0.0035, 'Z', profile='TRI'))
        s, d = 0.25, 0.0005
    else:
        h = g.noise(900, 4, 0.7)
        s, d = 0.18, 0.0003
    crease = g.noise(40, 3, 0.6, vec=g.vmap(scale=(1, 0.3, 1)), distort=0.5)
    r = g.math('ADD', rough, g.math('MULTIPLY', crease, 0.18))
    if sole:
        z = g.xyz()[2]
        so = g.n('ShaderNodeMapRange', From_Min=sole_h + 0.002, From_Max=sole_h - 0.002, Value=z).outputs[0]
        base = g.mix(so, base, sole)
        r = g.math('ADD', g.math('MULTIPLY', r, g.math('SUBTRACT', 1.0, so)), g.math('MULTIPLY', so, 0.85))
    base = g.mix(1.0, base, g.ramp(g.ao(0.03), [(0.0, (0.45,)), (0.9, (1,))]), 'MULTIPLY')
    z = g.xyz()[2]
    dust = g.math('MULTIPLY', g.n('ShaderNodeMapRange', From_Min=0.05, From_Max=0.0, Value=z).outputs[0], g.noise(60, 3))
    base = g.mix(g.math('MULTIPLY', dust, 0.5), base, (0.4, 0.37, 0.33))
    nrm = g.bump(crease, 0.3, 0.002, g.bump(h, s, d))
    return g.out(base, r, nrm)


def flat(name, col, rough=0.5, metal=0.0, brushed=False, img=None):
    g = G(name)
    base = g.image(img) if img else g.mix(g.noise(40, 2), _shade(col, 0.92), _shade(col, 1.06))
    nrm = None
    r = rough
    if brushed:
        st = g.noise(800, 2, 0.5, vec=g.vmap(scale=(1, 0.02, 0.02)))
        r = g.math('ADD', rough, g.math('MULTIPLY', st, 0.12))
        nrm = g.bump(st, 0.08, 0.0002)
    return g.out(base, r, nrm, metal)


def eyes(name):
    g = G(name)
    return g.out((0.012, 0.007, 0.005), 0.12)


# ---------------------------------------------------------------- 소품 메시 (모두 rest 포즈 좌표)

def new_obj(name, bm, mat, group, uv=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    vg = o.vertex_groups.new(name=group)
    vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    return o


def ring(bm, center, axis, up, r_in, r_out, width, n=28):
    """axis 를 감싸는 납작한 링 (시계줄)."""
    axis = axis.normalized()
    up = (up - axis * up.dot(axis)).normalized()
    side = axis.cross(up)
    rows = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = up * math.cos(a) + side * math.sin(a)
        rows.append([bm.verts.new(center + d * r + axis * w) for r, w in
                     ((r_in, -width / 2), (r_out, -width / 2), (r_out, width / 2), (r_in, width / 2))])
    for i in range(n):
        a, b = rows[i], rows[(i + 1) % n]
        for j in range(4):
            bm.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))


def cyl(bm, center, axis, r, h, n=24, uv_top=None):
    """뚜껑 있는 원기둥. uv_top 이면 윗면 UV 를 0..1 원으로."""
    axis = axis.normalized()
    t = Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))
    u = (t - axis * t.dot(axis)).normalized()
    v = axis.cross(u)
    bot = [bm.verts.new(center + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * r) for i in range(n)]
    top = [bm.verts.new(x.co + axis * h) for x in bot]
    for i in range(n):
        bm.faces.new((bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]))
    bm.faces.new(list(reversed(bot)))
    f = bm.faces.new(top)
    if uv_top:
        uvl = bm.loops.layers.uv.verify()
        for l in f.loops:
            i = top.index(l.vert)
            l[uvl].uv = (0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 + 0.5 * math.sin(2 * math.pi * i / n))
    return f


def box(bm, c, size, uv_front=False):
    """축 정렬 상자. uv_front 이면 -Y 면 UV 0..1."""
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r['verts']
    for x in vs:
        x.co = Vector((c.x + x.co.x * size[0], c.y + x.co.y * size[1], c.z + x.co.z * size[2]))
    if uv_front:
        uvl = bm.loops.layers.uv.verify()
        ymin = c.y - size[1] / 2
        for f in bm.faces:
            if all(v in vs and abs(v.co.y - ymin) < 1e-6 for v in f.verts):
                for l in f.loops:
                    l[uvl].uv = ((l.vert.co.x - (c.x - size[0] / 2)) / size[0], (l.vert.co.z - (c.z - size[2] / 2)) / size[2])
    return vs


def bvh(body):
    bm = bmesh.new()
    bm.from_mesh(body.data)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def surface_path(tree, x, center, angles, off):
    """x 평면에서 center 를 중심으로 각도(0=위, +=앞(-Y))마다 몸 표면에 붙는 점."""
    pts = []
    for a in angles:
        d = Vector((0, -math.sin(a), math.cos(a)))
        start = Vector((x, center.y, center.z)) + d * 0.6
        hit = tree.ray_cast(start, -d, 0.7)
        if hit[0] is not None:
            pts.append(hit[0] + hit[1] * off)
    return pts


def strip(bm, pts, width, thick, side=Vector((1, 0, 0))):
    """점 열을 따라 납작한 끈(사각 단면)."""
    rows = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = t.cross(side).normalized()
        sd = nrm.cross(t).normalized()
        rows.append([bm.verts.new(p + sd * sx * width / 2 + nrm * nz * thick / 2)
                     for sx, nz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rows, rows[1:]):
        for j in range(4):
            bm.faces.new((a[j], b[j], b[(j + 1) % 4], a[(j + 1) % 4]))
    bm.faces.new(rows[0][::-1])
    bm.faces.new(rows[-1])


def arm_radius(body, c, axis, rmax=0.07):
    axis = axis.normalized()
    best = 0.0
    for v in body.data.vertices:
        d = v.co - c
        along = d.dot(axis)
        if abs(along) < 0.008:
            rad = (d - axis * along).length
            if rad < rmax:
                best = max(best, rad)
    return best or 0.03


def watch(arm, body, asset, style="white", strap=(0.04, 0.03, 0.025), metal=False, size=0.017):
    """왼손목 시계 (LowerArm.L 100%)."""
    a0, a1 = bone_head(arm, "LowerArm.L"), bone_head(arm, "Palm.L")
    axis = (a1 - a0).normalized()
    c = a1 - axis * 0.035
    r = arm_radius(body, c, axis)
    up = Vector((0, 0, 1))
    bm = bmesh.new()
    ring(bm, c, axis, up, r + 0.0005, r + 0.0035, 0.018 if size > 0.015 else 0.013)
    o_band = new_obj(asset + "_WatchBand", bm,
                     flat(f"M_{asset}_WatchBand", strap, 0.3 if metal else 0.55, 1.0 if metal else 0.0, brushed=metal),
                     "LowerArm.L")
    bm = bmesh.new()
    upn = (up - axis * up.dot(axis)).normalized()
    cyl(bm, c + upn * (r + 0.002), upn, size, 0.008, n=28)
    o_case = new_obj(asset + "_WatchCase", bm, flat(f"M_{asset}_WatchCase", (0.75, 0.74, 0.72) if style != "gold" else (0.8, 0.6, 0.3),
                                                    0.22, 1.0, brushed=True), "LowerArm.L")
    bm = bmesh.new()
    cyl(bm, c + upn * (r + 0.0101), upn, size * 0.86, 0.0004, n=28, uv_top=True)
    o_dial = new_obj(asset + "_WatchDial", bm, flat(f"M_{asset}_WatchDial", (1, 1, 1), 0.15,
                                                    img=os.path.join(decals(), f"npc_dial_{style}.png")), "LowerArm.L")
    return [o_band, o_case, o_dial], c + upn * (r + 0.01)


def lanyard_card(arm, body, asset):
    """사원증 + 목줄 (Torso 100%)."""
    tree = bvh(body)
    tz = bone_head(arm, "Torso").z
    nz = bone_head(arm, "Neck").z
    out = []
    # 카드: 가슴 중앙 앞
    cz = tz + 0.085
    hit = tree.ray_cast(Vector((0, -0.6, cz)), Vector((0, 1, 0)), 1.0)
    fy = hit[0].y if hit[0] else -0.12
    bm = bmesh.new()
    box(bm, Vector((0, fy - 0.006, cz)), (0.058, 0.004, 0.09), uv_front=True)
    out.append(new_obj(asset + "_IdCard", bm, flat(f"M_{asset}_IdCard", (1, 1, 1), 0.32,
                                                   img=os.path.join(decals(), "npc_idcard.png")), "Torso"))
    # 목줄: 카드 위 -> 목 양옆 -> 목 뒤
    bm = bmesh.new()
    for sx in (-1, 1):
        pts = []
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            x = sx * (0.012 + 0.05 * t)
            z = cz + 0.045 + (nz - 0.01 - cz - 0.045) * t
            h = tree.ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)), 1.0)
            if h[0]:
                pts.append(h[0] + h[1] * 0.004)
        h = tree.ray_cast(Vector((sx * 0.062, 0.6, nz - 0.01)), Vector((0, -1, 0)), 1.0)
        if h[0]:
            top = Vector((sx * 0.066, (pts[-1].y + h[0].y) / 2, nz + 0.01))
            pts += [top, h[0] + h[1] * 0.004]
        strip(bm, pts, 0.014, 0.0015, side=Vector((0, 0, 1)))
    out.append(new_obj(asset + "_Lanyard", bm, flat(f"M_{asset}_Lanyard", (0.02, 0.05, 0.16), 0.6), "Torso"))
    return out


def bvh_multi(objs):
    """여러 메시(월드 = 로컬)를 한 BVH 로 (끈이 후드 위로 지나가게 할 때)."""
    verts, polys = [], []
    for o in objs:
        off = len(verts)
        verts += [v.co.copy() for v in o.data.vertices]
        polys += [[off + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def copy_weights(o, body):
    """body 스킨 웨이트를 가장 가까운 면에서 보간해 o 에 복사 (rest 포즈). 칼라·후드처럼 몸에 붙는 셸용."""
    for vg in body.vertex_groups:
        if vg.name not in o.vertex_groups:
            o.vertex_groups.new(name=vg.name)
    m = o.modifiers.new("DT", 'DATA_TRANSFER')
    m.object = body
    m.use_vert_data = True
    m.data_types_verts = {'VGROUP_WEIGHTS'}
    m.vert_mapping = 'POLYINTERP_NEAREST'
    m.layers_vgroup_select_src = 'ALL'
    m.layers_vgroup_select_dst = 'NAME'
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier=m.name)


def shell_obj(name, bm, mat, body, thick=0.002, subd=1, bevel=0.0, group=None):
    """bmesh -> 오브젝트 (두께·베벨·서브디비전 적용). group 이 없으면 body 웨이트 복사."""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    if thick:
        m = o.modifiers.new("Sol", 'SOLIDIFY')
        m.thickness, m.offset, m.use_even_offset = thick, 0.0, True
    if bevel:
        m = o.modifiers.new("Bev", 'BEVEL')
        m.width, m.segments, m.limit_method = bevel, 2, 'ANGLE'
    if subd:
        m = o.modifiers.new("Sub", 'SUBSURF')
        m.levels = subd
    k3d.apply_all(o)
    for p in me.polygons:
        p.use_smooth = True
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    if group:
        vg = o.vertex_groups.new(name=group)
        vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    else:
        copy_weights(o, body)
    return o


def neckline(body, cloth_mats, skin_mat):
    """옷 목선 높이(뒤, 앞)와 목 중심 (x, y)."""
    me = body.data
    mats = [m.name if m else "" for m in me.materials]
    cs = [p.center for p in me.polygons if mats[p.material_index] in cloth_mats and abs(p.center.x) < 0.03]
    zb = max(c.z for c in cs if c.y > 0) + 0.004
    zf = max((c.z for c in cs if c.y < 0), default=zb - 0.026) + 0.004     # 앞이 열린 옷이면 뒤보다 3cm 낮게
    nk = [p.center for p in me.polygons if mats[p.material_index] == skin_mat and zb + 0.008 < p.center.z < zb + 0.035
          and abs(p.center.x) < 0.09]
    cx = sum(c.x for c in nk) / len(nk)
    cy = (max(c.y for c in nk) + min(c.y for c in nk)) / 2
    return zb, zf, Vector((cx, cy, 0))


def neck_loft(tree, rows, phi0, phi1, zb, zf, center, n=40, slope=0.75):
    """목 둘레를 따라 행을 이어 붙인 면 (bmesh). φ: 0=뒤(+Y), ±180=앞(-Y).
    rows = [(dz(f), off(f), k)]: dz = 목선 기준 높이, off = 몸 표면에서 띄움, k = φ 배율(깃 끝 벌림).
    f = (1+cosφ)/2 (뒤 1, 앞 0). 목선 높이는 뒤 zb ~ 앞 zf 를 f 로 보간."""
    bm = bmesh.new()
    grid = []
    for dzf, offf, k in rows:
        row = []
        for i in range(n + 1):
            ph = math.radians(phi0 + (phi1 - phi0) * i / n) * k
            f = (1 + math.cos(ph)) / 2
            zl = zf + (zb - zf) * f
            dz = dzf(f)
            d = Vector((math.sin(ph), math.cos(ph), 0))
            o = Vector((center.x, center.y, zl + max(dz, 0.005)))
            hit = tree.ray_cast(o, d, 0.4)                 # 목 축에서 바깥으로 = 목 표면
            p = hit[0] if hit[0] is not None else o + d * 0.07
            nrm = d
            if dz < 0:
                # 목선 아래는 T포즈 팔 높이와 겹쳐 수평 레이가 팔에 맞음 -> 어깨·가슴 경사로 내려간 추측점의 가장 가까운 몸 표면
                g = Vector((p.x, p.y, zl)) + d * (-dz * slope) + Vector((0, 0, dz))
                loc, n_, _, _ = tree.find_nearest(g)
                if loc is not None:
                    p, nrm = loc, n_
            row.append(bm.verts.new(p + nrm * offf(f)))
        grid.append(row)
    for a, b in zip(grid, grid[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    return bm


def backpack(arm, body, asset, col=(0.03, 0.032, 0.036), tree=None):
    """백팩 (Torso 100%): 윗면 둥근 본체 + 앞주머니 + 옆 물병 메시 주머니 + 윗 손잡이 고리 + 패치,
    패드 어깨끈 -> 사다리 버클 -> 웨빙이 겨드랑이 밑으로 가방 아래 모서리까지, 가슴 스트랩."""
    tree = tree or bvh(body)
    tz = bone_head(arm, "Torso").z
    out = []
    hit = tree.ray_cast(Vector((0, 0.6, tz - 0.05)), Vector((0, -1, 0)), 1.0)
    by = hit[0].y if hit[0] else 0.12
    W, D, H = 0.30, 0.15, 0.42
    c = Vector((0, by + 0.085, tz - 0.1))
    bm = bmesh.new()
    for v in box(bm, c, (W, D, H)):
        if v.co.z > c.z:                                   # 윗면 좁혀 둥근 돔
            v.co.y = c.y + (v.co.y - c.y) * 0.6
            v.co.x *= 0.93
    me_tmp = bpy.data.meshes.new("tmp")
    bm.to_mesh(me_tmp)
    bm.free()
    o = bpy.data.objects.new(asset + "_Backpack", me_tmp)
    bpy.context.scene.collection.objects.link(o)
    bv = o.modifiers.new("Bevel", 'BEVEL')
    bv.width, bv.segments, bv.limit_method = 0.04, 3, 'NONE'
    sd = o.modifiers.new("Sub", 'SUBSURF')
    sd.levels = 2
    k3d.apply_all(o)
    # 앞주머니 (본체 바깥 +Y 면)
    bm = bmesh.new()
    box(bm, Vector((0, c.y + D / 2 + 0.012, c.z - 0.085)), (0.24, 0.05, 0.19))
    pk = bpy.data.meshes.new("tmp2")
    bm.to_mesh(pk)
    bm.free()
    po = bpy.data.objects.new(asset + "_BackpackPocket", pk)
    bpy.context.scene.collection.objects.link(po)
    bv = po.modifiers.new("Bevel", 'BEVEL')
    bv.width, bv.segments, bv.limit_method = 0.02, 3, 'NONE'
    k3d.apply_all(po)
    k3d.select([o, po], o)
    bpy.ops.object.join()
    pocket_face = c.y + D / 2 + 0.037

    def zips(g, base):
        x, y, z = g.xyz()
        # 메인 지퍼 트랙 (윗면·옆면 둘레) + 앞주머니 둘레 지퍼, 이빨 무늬
        main = g.math('MULTIPLY', g.band(y, c.y + 0.012, c.y + 0.024, 0.0008), g.math('GREATER_THAN', z, c.z - 0.06))
        pkt = g.math('MULTIPLY', g.math('MULTIPLY', g.band(y, c.y + D / 2 + 0.008, c.y + D / 2 + 0.018, 0.0008),
                                        g.math('GREATER_THAN', z, c.z - 0.17)), g.math('LESS_THAN', g.math('ABSOLUTE', x), 0.125))
        m = g.math('MAXIMUM', main, pkt)
        teeth = g.ramp(g.wave(0.003, 'X', profile='TRI'), [(0.4, (0,)), (0.6, (1,))])
        teeth = g.math('MAXIMUM', teeth, g.ramp(g.wave(0.003, 'Z', profile='TRI'), [(0.4, (0,)), (0.6, (1,))]))
        base = g.mix(m, base, g.mix(teeth, (0.012, 0.012, 0.013), (0.09, 0.09, 0.095)))
        # 앞주머니 테두리 박음질 + 아래 가장자리 닳음
        edge = g.math('MULTIPLY', g.band(y, pocket_face - 0.003, pocket_face + 0.01, 0.0008),
                      g.band(g.math('ABSOLUTE', x), 0.105, 0.11, 0.0006))
        base = g.mix(g.math('MULTIPLY', edge, 0.6), base, (0.12, 0.12, 0.13))
        low = g.n('ShaderNodeMapRange', From_Min=c.z - H / 2 + 0.05, From_Max=c.z - H / 2, Value=z).outputs[0]
        return g.mix(g.math('MULTIPLY', low, 0.45), base, (0.16, 0.15, 0.14))
    o.data.materials.append(cloth(f"M_{asset}_Backpack", col, "poly", rough=0.7, wrinkle=0.5, extra=zips))
    for p in o.data.polygons:
        p.use_smooth = True
    vg = o.vertex_groups.new(name="Torso")
    vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    o.data.uv_layers.new(name="UVMap")
    out.append(o)
    # 옆 물병 메시 주머니 (왼쪽 +X), 윗 손잡이 고리, 패치, 지퍼 손잡이
    bm = bmesh.new()
    box(bm, Vector((W / 2 + 0.006, c.y + 0.005, c.z - 0.12)), (0.035, 0.115, 0.16))
    out.append(shell_obj(asset + "_BottlePocket", bm, cloth(f"M_{asset}_Mesh", (0.02, 0.022, 0.025), "mesh", 0.8, wrinkle=0.4),
                         body, thick=0, subd=1, bevel=0.012, group="Torso"))
    bm = bmesh.new()
    top = c.z + H / 2
    pts = [Vector((0.045 * math.cos(a), c.y + 0.0, top - 0.004 + 0.04 * math.sin(a)))
           for a in [math.radians(x) for x in range(0, 181, 15)]]
    strip(bm, pts, 0.026, 0.005, side=Vector((0, 1, 0)))
    box(bm, Vector((0.0, pocket_face + 0.0012, c.z - 0.035)), (0.06, 0.003, 0.024))
    box(bm, Vector((0.095, pocket_face + 0.004, c.z + 0.0)), (0.012, 0.004, 0.032))
    out.append(shell_obj(asset + "_BagTrim", bm, flat(f"M_{asset}_BagTrim", (0.07, 0.07, 0.075), 0.45),
                         body, thick=0, subd=0, group="Torso"))
    # 패드 어깨끈 (뒤 위 -> 어깨 위 -> 가슴 앞)
    sz = bone_head(arm, "UpperArm.L").z
    bm = bmesh.new()
    web = bmesh.new()
    buck = bmesh.new()
    ends = {}
    for sx in (-1, 1):
        pts = surface_path(tree, sx * 0.095, Vector((0, 0.0, sz - 0.12)),
                           [math.radians(a) for a in range(-55, 125, 10)], 0.008)
        pts = [Vector((sx * 0.085, c.y - 0.06, c.z + 0.16))] + pts
        strip(bm, pts, 0.05, 0.01)
        p0 = pts[-1]
        ends[sx] = p0
        # 사다리 버클
        box(buck, p0 + Vector((0, -0.007, -0.012)), (0.034, 0.006, 0.02))
        # 웨빙: 패드 끝 -> 몸 옆(겨드랑이 밑) -> 등 -> 가방 아래 바깥 모서리
        wp = [p0 + Vector((0, -0.004, -0.02))]
        z0, z1 = p0.z - 0.04, c.z - H / 2 + 0.06
        for i, al in enumerate(range(30, 151, 15)):
            z = z0 + (z1 - z0) * i / 8
            yf = tree.ray_cast(Vector((0, -0.6, z)), Vector((0, 1, 0)), 1.0)[0]
            yb = tree.ray_cast(Vector((0, 0.6, z)), Vector((0, -1, 0)), 1.0)[0]
            cy = (yf.y + yb.y) / 2 if (yf and yb) else 0.0
            a = math.radians(al)
            d = Vector((sx * math.sin(a), -math.cos(a), 0))
            h = tree.ray_cast(Vector((0, cy, z)) + d * 0.5, -d, 0.6)
            if h[0] is not None and (h[0] - Vector((0, cy, z))).length > 0.05:
                wp.append(h[0] + d * 0.006)
        wp.append(Vector((sx * (W / 2 - 0.03), c.y - D / 2 + 0.02, c.z - H / 2 + 0.035)))
        strip(web, wp, 0.025, 0.003, side=Vector((0, 0, 1)))
    # 가슴 스트랩 + 가운데 버클
    zc = (ends[-1].z + ends[1].z) / 2 + 0.07
    cp = []
    for i in range(9):
        x = -0.1 + 0.2 * i / 8
        h = tree.ray_cast(Vector((x, -0.6, zc)), Vector((0, 1, 0)), 1.0)
        if h[0] is not None:
            cp.append(h[0] + Vector((0, -0.016, 0)))
    if len(cp) > 2:
        strip(web, cp, 0.02, 0.003, side=Vector((0, 0, 1)))
        box(buck, cp[len(cp) // 2] + Vector((0, -0.004, 0)), (0.04, 0.009, 0.024))
    out.append(new_obj(asset + "_Straps", bm, cloth(f"M_{asset}_Straps", (0.025, 0.026, 0.03), "poly", 0.6, wrinkle=0.3), "Torso"))
    out.append(new_obj(asset + "_Webbing", web, cloth(f"M_{asset}_Webbing", (0.02, 0.02, 0.022), "twill", 0.55, wrinkle=0.1), "Torso"))
    out.append(new_obj(asset + "_Buckles", buck, flat(f"M_{asset}_Buckles", (0.012, 0.012, 0.013), 0.35), "Torso"))
    return out


def glasses(arm, body, asset, eye_l, eye_r, col=(0.03, 0.018, 0.01)):
    """뿔테 안경 (Head 100%)."""
    tree = bvh(body)
    bm = bmesh.new()
    fy = min(eye_l.y, eye_r.y) - 0.012
    for e in (eye_l, eye_r):
        cc = Vector((e.x, fy, e.z))
        ring(bm, cc, Vector((0, 1, 0)), Vector((0, 0, 1)), 0.017, 0.020, 0.004, n=24)
    box(bm, Vector((0, fy, eye_l.z + 0.004)), (abs(eye_l.x - eye_r.x) - 0.036, 0.004, 0.004))
    for e in (eye_l, eye_r):
        sx = 1 if e.x > 0 else -1
        h = tree.ray_cast(Vector((sx * 0.5, fy + 0.04, e.z)), Vector((-sx, 0, 0)), 1.0)
        hx = h[0].x + sx * 0.004 if h[0] else e.x + sx * 0.04
        x0 = e.x + sx * 0.019
        box(bm, Vector(((x0 + hx) / 2, fy, e.z + 0.002)), (abs(hx - x0), 0.004, 0.004))
        box(bm, Vector((hx, fy + 0.05, e.z + 0.002)), (0.004, 0.1, 0.004))
    return [new_obj(asset + "_Glasses", bm, flat(f"M_{asset}_Glasses", col, 0.25), "Head")]


HAND = ("Palm", "MiddleHand", "Fingers", "Thumb1", "Thumb2")


def shrink_hands(arm, body, f=0.84):
    """손 메시와 손 본을 손목 기준으로 줄인다 (웨이트 비율만큼 -> 손목 이음새 연속)."""
    k3d.select([arm])
    bpy.ops.object.mode_set(mode='EDIT')
    for side in ("L", "R"):
        names = [f"{b}.{side}" for b in HAND]
        piv = arm.data.edit_bones[f"Palm.{side}"].head.copy()
        idx = {body.vertex_groups[n].index for n in names if n in body.vertex_groups}
        for v in body.data.vertices:
            w = min(1.0, sum(g.weight for g in v.groups if g.group in idx))
            if w > 0:
                v.co = v.co + w * ((piv + (v.co - piv) * f) - v.co)
        for n in names:
            eb = arm.data.edit_bones[n]
            eb.head, eb.tail = piv + (eb.head - piv) * f, piv + (eb.tail - piv) * f
    bpy.ops.object.mode_set(mode='OBJECT')


def join_body(body, parts):
    for p in parts:
        p.parent = body.parent
    objs = [body] + parts
    k3d.select(objs, body)
    bpy.ops.object.join()
    return body


# ---------------------------------------------------------------- 스마트폰 메시 (NpcSmartphone 과 미리보기 공용)

PHONE = (0.0715, 0.0078, 0.147)   # 가로, 두께, 세로 (m)


def build_phone(prefix="NpcSmartphone", with_screen=True):
    """원점 = 뒷면 중앙 아래 1/3 (손에 쥐는 점). 화면 = -Y, 위 = +Z."""
    w, t, h = PHONE
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0)), (w, t, h))
    me = bpy.data.meshes.new(prefix + "_Body")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(prefix + "_Body", me)
    bpy.context.scene.collection.objects.link(o)
    bv = o.modifiers.new("Bevel", 'BEVEL')
    bv.width, bv.segments, bv.limit_method = 0.0034, 3, 'NONE'
    k3d.apply_all(o)
    # 카메라 섬 (뒤에서 볼 때 왼쪽 위 = +X) + 크롬 렌즈 테 + 버튼
    bm = bmesh.new()
    box(bm, Vector((0.016, t / 2 + 0.0008, h / 2 - 0.024)), (0.03, 0.0018, 0.034))
    lens = [Vector((0.0215, t / 2 + 0.0017, h / 2 - 0.0165)), Vector((0.0215, t / 2 + 0.0017, h / 2 - 0.0315))]
    for p in lens:
        cyl(bm, p, Vector((0, 1, 0)), 0.0055, 0.0008)
    box(bm, Vector((w / 2 + 0.0004, 0, 0.03)), (0.0012, 0.0035, 0.022))
    box(bm, Vector((w / 2 + 0.0004, 0, -0.002)), (0.0012, 0.0035, 0.012))
    cam = bpy.data.meshes.new("tmp")
    bm.to_mesh(cam)
    bm.free()
    co = bpy.data.objects.new(prefix + "_Cam", cam)
    bpy.context.scene.collection.objects.link(co)
    # 렌즈 유리 (검은 유리, 테 안쪽 0.8mm 돌출) + 플래시
    bm = bmesh.new()
    for p in lens:
        cyl(bm, p + Vector((0, 0.0004, 0)), Vector((0, 1, 0)), 0.0042, 0.0008)
    gl = bpy.data.meshes.new("tmp3")
    bm.to_mesh(gl)
    bm.free()
    go = bpy.data.objects.new(prefix + "_Lens", gl)
    bpy.context.scene.collection.objects.link(go)
    bm = bmesh.new()
    cyl(bm, Vector((0.0085, t / 2 + 0.0017, h / 2 - 0.016)), Vector((0, 1, 0)), 0.0022, 0.0003)
    fl = bpy.data.meshes.new("tmp4")
    bm.to_mesh(fl)
    bm.free()
    fo = bpy.data.objects.new(prefix + "_Flash", fl)
    bpy.context.scene.collection.objects.link(fo)
    body_mat = flat(f"M_{prefix}_Case", (0.05, 0.06, 0.08), 0.35, 0.0)
    cam_mat = flat(f"M_{prefix}_Trim", (0.55, 0.56, 0.58), 0.25, 1.0, brushed=True)
    glass_mat = flat(f"M_{prefix}_Bezel", (0.004, 0.004, 0.005), 0.08)
    o.data.materials.append(body_mat)
    co.data.materials.append(cam_mat)
    go.data.materials.append(glass_mat)
    fo.data.materials.append(flat(f"M_{prefix}_Flash", (0.85, 0.78, 0.6), 0.3))
    # 앞면(화면 쪽) 면은 검은 유리 테두리로
    gi = slot(o, glass_mat)
    for p in o.data.polygons:
        if p.normal.y < -0.7:
            p.material_index = gi
    k3d.select([o, co, go, fo], o)
    bpy.ops.object.join()
    for p in o.data.polygons:
        p.use_smooth = True
    k3d.smooth(o, 40)
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    scr = None
    if with_screen:
        sw, sh = w - 0.0055, h - 0.0045
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        y = -t / 2 - 0.0004
        vs = [bm.verts.new(Vector(p)) for p in ((-sw / 2, y, -sh / 2), (sw / 2, y, -sh / 2), (sw / 2, y, sh / 2), (-sw / 2, y, sh / 2))]
        f = bm.faces.new(vs)
        for l, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            l[uvl].uv = uv
        if f.normal.y > 0:
            f.normal_flip()
        sme = bpy.data.meshes.new(prefix + "_Screen")
        bm.to_mesh(sme)
        bm.free()
        scr = bpy.data.objects.new(prefix + "_Screen", sme)
        bpy.context.scene.collection.objects.link(scr)
        sm = bpy.data.materials.get(f"M_Dyn_{prefix}_Screen") or bpy.data.materials.new(f"M_Dyn_{prefix}_Screen")
        nt = k3d._nodes(sm)
        p = k3d.principled(sm)
        im = k3d.load_image(os.path.join(decals(), "T_NpcSmartphone_Screen.png"), "T_NpcSmartphone_Screen")
        n = k3d.image_node(sm, im, p.inputs['Base Color'])
        nt.links.new(n.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = 1.2
        p.inputs['Roughness'].default_value = 0.08
        k3d.flag(sm, dynamic=True)
        scr.data.materials.append(sm)
        scr.parent = o
    # 원점: 뒷면, 아래에서 1/3
    grip = Vector((0, t / 2, -h / 2 + h / 3))
    o.data.transform(Matrix.Translation(-grip))
    if scr:
        scr.data.transform(Matrix.Translation(-grip))
    return o, scr


# ---------------------------------------------------------------- 포즈/클립

def upd():
    bpy.context.view_layer.update()


def take_pose(arm, act, frame):
    """act 의 frame(소수 가능) 포즈를 읽어 액션 없이 본에 그대로 둔다."""
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    if act.slots:
        ad.action_slot = act.slots[0]
    fi = math.floor(frame)
    bpy.context.scene.frame_set(int(fi), subframe=float(frame - fi))
    pose = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones}
    ad.action = None
    for pb in arm.pose.bones:
        pb.location, pb.rotation_quaternion = pose[pb.name]
    upd()
    return pose


def set_pose(arm, pose):
    for pb in arm.pose.bones:
        pb.location, pb.rotation_quaternion = pose[pb.name][0].copy(), pose[pb.name][1].copy()
    upd()


def rot_about(arm, bone, q, pivot=None):
    """armature 공간 회전 q 를 본 머리(또는 pivot) 기준으로 적용."""
    pb = arm.pose.bones[bone]
    upd()
    m = pb.matrix.copy()
    t = pivot if pivot is not None else m.translation.copy()
    pb.matrix = Matrix.Translation(t) @ q.to_matrix().to_4x4() @ Matrix.Translation(-t) @ m
    upd()


def shift(arm, bone, d):
    """본을 armature 공간에서 d 만큼 옮긴다."""
    pb = arm.pose.bones[bone]
    upd()
    pb.matrix = Matrix.Translation(Vector(d)) @ pb.matrix
    upd()


def aim(arm, bone, child, d, w=1.0):
    """bone 머리 -> child 머리 방향을 d 로 (프로토타입 mr() 과 같은 방식)."""
    upd()
    pb, pc = arm.pose.bones[bone], arm.pose.bones[child]
    v = pc.head - pb.head
    q = v.rotation_difference(Vector(d).normalized())
    rot_about(arm, bone, Quaternion().slerp(q, w))


def turn(arm, bone, axis, ang):
    rot_about(arm, bone, Quaternion(Vector(axis).normalized(), ang))


def bone_vec(arm, bone, v_rest):
    """rest 기준 벡터 v_rest 가 지금 포즈에서 향하는 방향 (armature 공간)."""
    pb = arm.pose.bones[bone]
    d = pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()
    return (d @ Vector(v_rest)).normalized()


def bone_pt(arm, bone, p_rest):
    pb = arm.pose.bones[bone]
    return pb.matrix @ pb.bone.matrix_local.inverted() @ Vector(p_rest)


def roll_to(arm, bone, child, v_rest, target):
    """bone 을 자기 축(bone->child)으로 돌려 v_rest 가 target 쪽을 보게."""
    upd()
    pb, pc = arm.pose.bones[bone], arm.pose.bones[child]
    ax = (pc.head - pb.head).normalized()
    v = bone_vec(arm, bone, v_rest)
    t = Vector(target).normalized()
    v -= ax * v.dot(ax)
    t -= ax * t.dot(ax)
    if v.length < 1e-6 or t.length < 1e-6:
        return
    v.normalize(); t.normalize()
    ang = math.atan2(ax.dot(v.cross(t)), v.dot(t))
    turn(arm, bone, ax, ang)


def ik2(arm, b1, b2, tip_rest, target, pole=None):
    """2본 IK: b1(어깨/엉덩이)·b2(팔꿈치/무릎)를 돌려 b2 의 rest 점 tip_rest 를 target 에 둔다.
    pole 이 없으면 지금 무릎/팔꿈치 쪽으로 굽힌다."""
    upd()
    p1, p2 = arm.pose.bones[b1], arm.pose.bones[b2]
    H, K = p1.head.copy(), p2.head.copy()
    A = bone_pt(arm, b2, tip_rest)
    l1, l2 = (K - H).length, (A - K).length
    T = Vector(target)
    u = T - H
    d = max(abs(l1 - l2) + 1e-4, min(u.length, l1 + l2 - 1e-4))
    u.normalize()
    side = (Vector(pole) if pole is not None else K) - H
    side -= u * side.dot(u)
    if side.length < 1e-6:
        return
    side.normalize()
    a = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    Kn = H + (u * math.cos(a) + side * math.sin(a)) * l1
    rot_about(arm, b1, (K - H).rotation_difference(Kn - H))
    upd()
    K = p2.head.copy()
    A = bone_pt(arm, b2, tip_rest)
    rot_about(arm, b2, (A - K).rotation_difference(T - K))


def ankles_now(arm):
    """발(Foot 본은 루트 자식이라 골반을 옮겨도 그대로)에 맞춰야 할 정강이 끝 위치."""
    upd()
    return {s: bone_pt(arm, f"LowerLeg.{s}", arm.data.bones[f"Foot.{s}"].head_local) for s in "LR"}


def plant_legs(arm, ankles):
    for s in "LR":
        ik2(arm, f"UpperLeg.{s}", f"LowerLeg.{s}", arm.data.bones[f"Foot.{s}"].head_local, ankles[s])


def look(arm, target, w_neck=0.35, w_head=0.65, eye=None):
    """머리 정면(-Y)을 target 쪽으로 (목·머리 나눠서)."""
    for b, w in (("Neck", w_neck), ("Head", w_head)):
        upd()
        e = eye if eye is not None else arm.pose.bones["Head"].head
        f = bone_vec(arm, "Head", (0, -1, 0))
        q = f.rotation_difference((Vector(target) - e).normalized())
        rot_about(arm, b, Quaternion().slerp(q, w))


def bell(t, k=1):
    """0 -> 1(중간) -> 0. 루프 시작=끝, 리뷰 측정(처음/중간/끝)에도 움직임이 잡힌다."""
    return (1 - math.cos(2 * math.pi * k * t)) / 2


IDLE_PP = 40     # Idle 왕복 프레임 수 (숨쉬기·무게 이동은 원본 Idle 에서 가져옴)


def idle_at(arm, t):
    """Idle 을 0 -> IDLE_PP -> 0 으로 왕복한 포즈. 루프 이음매가 없고 발 접지는 Idle 그대로."""
    a = bpy.data.actions["Idle"]
    f0, f1 = a.frame_range
    return take_pose(arm, a, f0 + min(IDLE_PP, f1 - f0) * bell(t))


def new_clip(arm, name, frames, pose_fn):
    """pose_fn(arm, t) 로 프레임마다 포즈를 만들고 fcurve 에 직접 키 (t = 0..1, 마지막 = 처음 = 루프).
    포즈 계산 중에는 액션을 떼어 두어 평가가 포즈를 덮어쓰지 않게 한다."""
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions.new(name)
    keys, prev = [], {}
    for f in frames:
        ad.action = None
        pose_fn(arm, f / frames[-1])
        snap = {}
        for pb in arm.pose.bones:
            q = pb.rotation_quaternion.copy()
            if pb.name in prev:
                q.make_compatible(prev[pb.name])
            prev[pb.name] = q
            snap[pb.name] = (pb.location.copy(), q)
        keys.append((f, snap))
    ad.action = act
    fcs = {}
    for f, snap in keys:
        for bn, (loc, q) in snap.items():
            for prop, vals in (("location", loc), ("rotation_quaternion", q)):
                dp = f'pose.bones["{bn}"].{prop}'
                for i, v in enumerate(vals):
                    fc = fcs.get((dp, i))
                    if fc is None:
                        fc = fcs[(dp, i)] = act.fcurve_ensure_for_datablock(arm, dp, index=i, group_name=bn)
                    fc.keyframe_points.insert(f, v, options={'FAST'})
    for fc in fcs.values():
        fc.update()
    if act.slots:
        ad.action_slot = act.slots[0]
    ad.action = None
    return act


def eye_point(arm):
    return bone_pt(arm, "Head", arm.data.bones["Head"].head_local + Vector((0, -0.06, 0.07)))


def open_hand(arm, side, w_mid, w_fing):
    """Idle 의 주먹을 rest(편 손) 쪽으로 편다."""
    for bn, w in ((f"MiddleHand.{side}", w_mid), (f"Fingers.{side}", w_fing)):
        pb = arm.pose.bones[bn]
        pb.rotation_quaternion = pb.rotation_quaternion.slerp(Quaternion(), w)
    upd()


def phone_pose(arm, t, info):
    """오른손 손바닥에 폰을 얹고 고개 숙여 봄. 엄지 스크롤 3번, 읽으며 끄덕임, 숨쉬기(Idle 왕복)."""
    idle_at(arm, t)
    b = bell(t)
    turn(arm, "Torso", (1, 0, 0), 0.05 + 0.02 * b)
    aim(arm, "UpperArm.R", "LowerArm.R", (-0.1, -0.12, -0.99))
    aim(arm, "LowerArm.R", "Palm.R", (0.36, -0.9, 0.24 + 0.06 * b))           # 숨에 맞춰 폰을 살짝 들어 올림
    look(arm, bone_pt(arm, "Palm.R", arm.data.bones["Palm.R"].head_local), 0.25, 0.45)
    turn(arm, "Head", (1, 0, 0), 0.05 * b + 0.02 * math.sin(2 * math.pi * 3 * t))   # 글 읽으며 끄덕
    turn(arm, "Head", (0, 0, 1), 0.04 * math.sin(2 * math.pi * t))
    # 손바닥(rest -Z)이 눈 쪽을 보게
    upd()
    palm = arm.pose.bones["Palm.R"].head
    roll_to(arm, "LowerArm.R", "Palm.R", (0, 0, -1), eye_point(arm) - palm)
    aim(arm, "Palm.R", "Fingers.R", (0.2, -0.72, 0.66))
    open_hand(arm, "R", 1.0, 0.9)                                               # 주먹 -> 폰 받치는 편 손 (폰이 주먹을 뚫던 것)
    # 엄지: 화면 위로 올리고 3번 스크롤 (12~15°)
    upd()
    th = (arm.pose.bones["Thumb2.R"].head - arm.pose.bones["Thumb1.R"].head).normalized()
    nrm = bone_vec(arm, "Palm.R", (0, 0, -1))
    turn(arm, "Thumb1.R", th.cross(nrm), 0.3 + 0.25 * bell(t, 3))
    # 왼팔: 편하게 내림 + 살짝 굽힘
    aim(arm, "UpperArm.L", "LowerArm.L", (0.12, -0.05, -1.0))
    aim(arm, "LowerArm.L", "Palm.L", (0.05, -0.35, -0.94))


def watch_pose(arm, t, info):
    """왼손목 시계 확인: 손목 비틀어 보기(2번) + 중간에 앞(키오스크)을 흘끗."""
    idle_at(arm, t)
    b = bell(t)
    aim(arm, "UpperArm.L", "LowerArm.L", (0.22, -0.4, -0.89))
    aim(arm, "LowerArm.L", "Palm.L", (-0.84, -0.42, 0.34 + 0.08 * bell(t, 2)))
    upd()
    wpos = bone_pt(arm, "LowerArm.L", info["watch_rest"])
    roll_to(arm, "LowerArm.L", "Palm.L", (0, 0, 1), eye_point(arm) - wpos)
    upd()
    ax = (arm.pose.bones["MiddleHand.L"].head - arm.pose.bones["Palm.L"].head).normalized()
    turn(arm, "Palm.L", ax, 0.24 * bell(t, 2) - 0.08)                          # 손목 돌림 ~14°
    upd()
    wpos = bone_pt(arm, "LowerArm.L", info["watch_rest"])
    look(arm, wpos, 0.22, 0.4)
    turn(arm, "Head", (0, 0, 1), -0.14 * b)                                     # 흘끗 (8°)
    turn(arm, "Head", (1, 0, 0), -0.12 * b)                                     # 고개 들어 앞을 봄
    aim(arm, "UpperArm.R", "LowerArm.R", (-0.1, -0.03, -1.0))


def impatient_pose(arm, t, info):
    """체중 이동(왼다리, 2.5cm) + 한숨(1초에 가슴 들썩) + 고개 갸웃 + 오른발 톡톡. 팔짱."""
    idle_at(arm, t)
    b = bell(t)
    an = ankles_now(arm)
    shift(arm, "Body", (0.025 * b, 0, -0.008 * b))
    turn(arm, "Body", (0, -1, 0), 0.05 * b)                 # 오른쪽 골반이 내려감 (콘트라포스토)
    plant_legs(arm, an)
    turn(arm, "Abdomen", (0, -1, 0), -0.07 * b)             # 상체는 반대로 세움
    # 팔짱
    aim(arm, "UpperArm.R", "LowerArm.R", (-0.25, -0.42, -0.87))
    aim(arm, "LowerArm.R", "Palm.R", (0.93, -0.33, 0.12))
    aim(arm, "UpperArm.L", "LowerArm.L", (0.25, -0.38, -0.89))
    aim(arm, "LowerArm.L", "Palm.L", (-0.93, -0.36, 0.02))
    # 한숨: 0.25~0.75 구간, 1초(중간)에 가슴 들고 어깨 올렸다 툭
    sig = math.sin(math.pi * (t - 0.25) / 0.5) if 0.25 < t < 0.75 else 0.0
    turn(arm, "Torso", (1, 0, 0), -0.08 * sig)
    for bn, sx in (("Shoulder.L", 1), ("Shoulder.R", -1)):
        turn(arm, bn, (0, sx, 0), -0.12 * sig)
    turn(arm, "Head", (1, 0, 0), 0.06 - 0.16 * sig)          # 한숨 때 고개를 뒤로 젖힘
    turn(arm, "Head", (0, -1, 0), 0.04 + 0.1 * b)            # 갸웃 2~8°
    # 오른발 앞꿈치 톡톡 (2초에 4번)
    tap = max(0.0, math.sin(2 * math.pi * t * 4))
    upd()
    fb = arm.pose.bones["Foot.R"]
    heel = fb.head + Vector((0, 0.03, 0))
    rot_about(arm, "Foot.R", Quaternion(Vector((1, 0, 0)), -0.28 * tap), pivot=heel)


def lookat_pose(arm, t, info, side=-1):
    """옆(side=-1 오른쪽, +1 왼쪽)을 돌아본 채 유지하는 루프. 돌아보는 전환은 Animator 크로스페이드(0.3초)로."""
    idle_at(arm, t)
    b = bell(t)
    turn(arm, "Abdomen", (0, 0, 1), side * 0.12)
    turn(arm, "Torso", (0, 0, 1), side * 0.2)
    turn(arm, "Neck", (0, 0, 1), side * 0.3)
    turn(arm, "Head", (0, 0, 1), side * (0.38 + 0.08 * b))                    # 중간에 더 돌아봄
    turn(arm, "Head", (1, 0, 0), -0.04 + 0.05 * b + 0.025 * math.sin(2 * math.pi * 2 * t))   # 훑어봄


def tap_pose(arm, t, info):
    """키오스크 화면 두드리기 (프로토타입 pose='tap'): 오른손 끝 바닥 1.3m·몸 앞 45cm, 3.5Hz 톡톡, 고개 숙여 봄."""
    idle_at(arm, t)
    turn(arm, "Torso", (1, 0, 0), 0.06)
    upd()
    tip = Vector((-0.1, -0.45, 1.3))
    hand = (Vector((0.08, -0.8, -0.45))).normalized()
    plen = (bone_head(arm, "Fingers.R") - bone_head(arm, "Palm.R")).length * 1.35
    wrist = tip - hand * plen
    sh = arm.pose.bones["UpperArm.R"].head
    ik2(arm, "UpperArm.R", "LowerArm.R", arm.data.bones["Palm.R"].head_local, wrist,
        pole=sh + Vector((-0.3, 0.1, -0.4)))
    upd()
    roll_to(arm, "LowerArm.R", "Palm.R", (0, 0, -1), Vector((0, 0, -1)))        # 손바닥 아래
    aim(arm, "Palm.R", "Fingers.R", hand)
    open_hand(arm, "R", 0.9, 0.85)
    upd()
    ax = hand.cross(Vector((0, 0, 1))).normalized()
    turn(arm, "Palm.R", ax, 0.16 * bell(t, 7))                                  # 손끝 1.5cm 들었다 톡
    look(arm, tip, 0.3, 0.55)
    turn(arm, "Head", (1, 0, 0), 0.03 * bell(t))


def sitidle_pose(arm, t, info, sit):
    """Sitting 마지막 프레임(앉은 상태) + 숨쉬기 + 고개 미세 움직임."""
    set_pose(arm, sit)
    b = bell(t)
    turn(arm, "Abdomen", (1, 0, 0), 0.012 * b)
    turn(arm, "Torso", (1, 0, 0), -0.035 * b)
    for bn, sx in (("Shoulder.L", 1), ("Shoulder.R", -1)):
        turn(arm, bn, (0, sx, 0), -0.04 * b)
    turn(arm, "Head", (1, 0, 0), 0.035 * b)
    turn(arm, "Head", (0, 0, 1), 0.06 * math.sin(2 * math.pi * t))


def author_clips(arm, info):
    FR = list(range(0, 49, 2))
    acts = [
        new_clip(arm, "Phone", FR, lambda a, t: phone_pose(a, t, info)),
        new_clip(arm, "Watch", FR, lambda a, t: watch_pose(a, t, info)),
        new_clip(arm, "Impatient", FR, lambda a, t: impatient_pose(a, t, info)),
        new_clip(arm, "LookAt", FR, lambda a, t: lookat_pose(a, t, info, -1)),
        new_clip(arm, "LookAtLeft", FR, lambda a, t: lookat_pose(a, t, info, +1)),
        new_clip(arm, "Tap", list(range(0, 49)), lambda a, t: tap_pose(a, t, info)),
    ]
    sit = bpy.data.actions.get("Sitting")
    if sit:
        sp = take_pose(arm, sit, sit.frame_range[1])
        acts.append(new_clip(arm, "SitIdle", FR, lambda a, t: sitidle_pose(a, t, info, sp)))
    set_pose(arm, idle_at(arm, 0.0))
    return acts


def palm_offset(arm, body):
    """rest(T포즈, 손바닥 -Z)에서 오른손 가운데 뼈 축부터 손바닥 피부까지 거리."""
    p, f = bone_head(arm, "Palm.R"), bone_head(arm, "Fingers.R")
    c = p + (f - p) * 0.5
    hit = bvh(body).ray_cast(c - Vector((0, 0, 0.1)), Vector((0, 0, 1)), 0.2)
    return (c.z - hit[0].z) if hit[0] is not None else 0.015


def socket(arm, name, bone, world):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', 0.05
    bpy.context.scene.collection.objects.link(e)
    e.parent = arm
    e.parent_type = 'BONE'
    e.parent_bone = bone
    upd()
    e.matrix_world = world
    upd()
    return e


def phone_grip_matrix(arm, palm_off=0.015):
    """Phone 클립 0프레임의 오른손 쥐는 점 (폰 원점과 같은 규칙: 화면 -Y, 위 +Z)."""
    upd()
    palm = arm.pose.bones["Palm.R"].head
    fing = arm.pose.bones["Fingers.R"].head
    nrm = bone_vec(arm, "Palm.R", (0, 0, -1))            # 손바닥이 보는 쪽
    up = (fing - palm).normalized()
    eye = eye_point(arm)
    scr = (eye - palm).normalized()                      # 화면이 눈을 봄 -> 폰 -Y = scr
    up = (up - scr * up.dot(scr)).normalized()
    x = (-scr).cross(up)                                # 오른손 좌표계 (det +1)
    m = Matrix((x, -scr, up)).transposed().to_4x4()
    grip = palm + (fing - palm) * 0.5 + nrm * (palm_off + 0.005)      # 손바닥 피부 위 5mm
    m.translation = grip
    return m


# ---------------------------------------------------------------- 전체 빌드

def run(cfg):
    """에셋 스크립트 진입점. NPC_FAST=1 이면 굽기/내보내기 없이 미리보기만."""
    fast = bool(os.environ.get("NPC_FAST"))
    arm, body, socks, phone = build(cfg, bake=not fast)
    if fast:
        shots(cfg["asset"], arm, body, phone, tag="wip")
    else:
        finish(cfg, arm, body, socks, phone)


def build(cfg, bake=True):
    asset = cfg["asset"]
    arm, body = load(cfg["glb"], asset)
    xform_rig(arm, body, Matrix())                      # x100 스케일·회전 적용
    clean_mesh(body)
    mn, mx = rest_bounds(arm, body)
    s0 = cfg["height"] / (mx.z - mn.z)                  # prep 은 최종 미터 기준으로 판단 (좌표 * s0)
    if cfg.get("prep"):
        cfg["prep"](arm, body, s0)                       # 옷 재질 나누기·두께
    subdivide(body, 1)
    mn, mx = rest_bounds(arm, body)
    s = cfg["height"] / (mx.z - mn.z)
    xform_rig(arm, body, Matrix.Translation((0, 0, -mn.z * s)) @ Matrix.Scale(s, 4))
    shrink_hands(arm, body, cfg.get("hand", 0.84))
    # 재질 교체 (원본 재질별 rest 높이 범위를 넘겨 줌: 벨트·넥타이 위치 등)
    zr = {}
    for p in body.data.polygons:
        n = body.data.materials[p.material_index].name
        a, b = zr.get(n, (9.0, -9.0))
        zr[n] = (min(a, p.center.z), max(b, p.center.z))
    ec = [p.center.copy() for p in body.data.polygons
          if body.data.materials[p.material_index].name == "Eyes" and p.center.z > 1.0]
    if ec:                                                # 눈 높이·얼굴 앞면 y·눈 간격 (립·볼 홍조 위치용)
        zr["_face"] = (sum(c.z for c in ec) / len(ec), min(c.y for c in ec), max(abs(c.x) for c in ec))
    mats = cfg["mats"]
    for i, m in enumerate(body.data.materials):
        if m and m.name in mats:
            body.data.materials[i] = mats[m.name](arm, zr)
    extra = cfg["extra"](arm, body) if cfg.get("extra") else []
    parts, watch_top = watch(arm, body, asset, **cfg.get("watch", {}))
    extra += parts
    eyes_ = [p.center.copy() for p in body.data.polygons
             if body.data.materials[p.material_index].name.startswith(f"M_{asset}_Eyes")]
    info = {"watch_rest": arm.data.bones["LowerArm.L"].matrix_local.inverted() @ watch_top}
    if cfg.get("glasses") and eyes_:
        L = [c for c in eyes_ if c.x > 0]
        R = [c for c in eyes_ if c.x < 0]
        avg = lambda cs: sum(cs, Vector()) / len(cs)
        extra += glasses(arm, body, asset, avg(L), avg(R))
    palm_off = palm_offset(arm, body)
    join_body(body, extra)
    for p in body.data.polygons:
        p.use_smooth = True
    arm.data.pose_position = 'POSE'
    defo = [m for m in body.modifiers if m.type == 'ARMATURE']
    for m in defo:                                       # 클립 계산 중엔 메시 변형 생략 (속도)
        m.show_viewport = False
    acts = author_clips(arm, info)
    # 소켓
    set_pose(arm, take_pose(arm, bpy.data.actions["Phone"], 0))
    grip = phone_grip_matrix(arm, palm_off)
    socks = [socket(arm, asset + "_Socket_PhoneGrip", "Palm.R", grip)]
    upd()
    socks.append(socket(arm, asset + "_Socket_Head", "Head", Matrix.Translation(eye_point(arm))))
    phone_preview = None
    if cfg.get("preview_phone", True):
        po, ps = build_phone(asset + "PrvPhone")
        po.matrix_world = grip
        phone_preview = [po, ps]
    for m in defo:
        m.show_viewport = True
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix()
    upd()
    if bake:
        arm.data.pose_position = 'REST'
        upd()
        k3d.bake(body, size=cfg.get("tex", 2048), samples=24, ao_distance=0.08, keep=cfg.get("keep", ()))
        arm.data.pose_position = 'POSE'
    return arm, body, socks, phone_preview


def shots(asset, arm, body, phone, tag=""):
    """클립별 미리보기: Idle 정면/뒤 + Phone/Watch/Impatient/LookAt."""
    paths = []
    objs = [arm, body]
    set_pose(arm, take_pose(arm, bpy.data.actions["Idle"], 0))
    if phone:
        for o in phone:
            o.hide_render = True
    paths += k3d.preview(asset, objs, views=((20, 6), (200, 6)), res=(900, 1200), tag=tag or "")
    for clip, fr in (("Phone", 24), ("Watch", 24), ("Impatient", 24), ("LookAt", 24), ("Tap", 24), ("SitIdle", 24)):
        if clip not in bpy.data.actions:
            continue
        set_pose(arm, take_pose(arm, bpy.data.actions[clip], fr))
        if phone:
            for o in phone:
                o.hide_render = clip != "Phone"
            if clip == "Phone":
                upd()
                phone[0].matrix_world = bpy.data.objects[asset + "_Socket_PhoneGrip"].matrix_world
        paths += k3d.preview(asset, objs, views=((25, 4),), res=(700, 1000), tag=(tag + "_" if tag else "") + clip)
    # 1인칭 거리 (뒤 손님을 돌아볼 때: 1.55m 눈높이, 1.3m 거리)
    set_pose(arm, take_pose(arm, bpy.data.actions["Phone"], 24))
    if phone:
        for o in phone:
            o.hide_render = False
        upd()
        phone[0].matrix_world = bpy.data.objects[asset + "_Socket_PhoneGrip"].matrix_world
    paths.append(fp_shot(asset, objs + (phone or []), tag))
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix()
    if phone:
        for o in phone:
            o.hide_render = True
    upd()
    return paths


def fp_shot(asset, objs, tag=""):
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("fp")
    cd.lens = 35
    cam = bpy.data.objects.new("fp", cd)
    sc.collection.objects.link(cam)
    cam.location = (0.25, -1.3, 1.55)
    cam.rotation_euler = (Vector((0, 0, 1.25)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    old = sc.camera
    p = os.path.join(k3d.SRC, "Previews", f"{asset}{('_' + tag) if tag else ''}_fp.png")
    # k3d.preview 의 조명/바닥을 쓰기 위해 카메라만 바꿔 렌더하는 대신 간단 조명 직접 구성
    sc.render.engine = k3d._engine_eevee()
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new("fpw")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.62, 0.64, 0.68, 1)
    bg.inputs['Strength'].default_value = 0.6
    oldw = sc.world
    sc.world = w
    tmp = [cam]
    for kind, en, loc, rot in (('SUN', 2.2, (2, -3, 5), (0.7, 0.2, 0.5)), ('AREA', 120, (-1.5, -1.5, 2.5), None)):
        ld = bpy.data.lights.new("fpl", kind)
        ld.energy = en
        if kind == 'AREA':
            ld.size = 2
        lo = bpy.data.objects.new("fpl", ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        tmp.append(lo)
    bpy.ops.mesh.primitive_plane_add(size=20)
    gpl = bpy.context.active_object
    gpl.data.materials.append(k3d.mat("k3d_ground", (0.35, 0.35, 0.36), 0.8))
    tmp.append(gpl)
    sc.camera = cam
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.world = oldw
    sc.camera = old
    return p


def finish(cfg, arm, body, socks, phone):
    asset = cfg["asset"]
    paths = shots(asset, arm, body, phone)
    if phone:
        for o in phone:
            bpy.data.objects.remove(o, do_unlink=True)
    ad = arm.animation_data
    ad.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix()
    upd()
    clips = [a.name for a in bpy.data.actions]
    notes = cfg["notes"] + (
        f" | 리그: {asset}_Rig (Quaternius HumanArmature 31본 그대로, Generic 권장). 스킨드 메시 1개 {asset}_Body,"
        f" 머티리얼 {len(body.data.materials)}개: " + ", ".join(m.name for m in body.data.materials) + "."
        f" | 클립(FBX take = '{asset}_Rig|<이름>'): " + ", ".join(clips) +
        ". Phone/Watch/Impatient/LookAt/LookAtLeft/Tap/SitIdle 은 새로 만든 2초 루프(48f@24fps, 첫=끝 프레임, Idle 왕복 숨쉬기 포함):"
        " Phone=오른손 폰 보기(엄지 스크롤·끄덕), Watch=왼손목 시계 보기(손목 돌림·앞을 흘끗), Impatient=체중 이동·한숨·발 구르기·팔짱,"
        " LookAt/LookAtLeft=오른쪽/왼쪽 돌아본 채 유지(돌아보는 동작은 Animator 크로스페이드 0.3초로), Tap=키오스크 화면 두드리기(손끝 1.3m·몸 앞 45cm)."
        " Sitting=선 자세에서 앉는 전환(1회 재생 후 마지막 프레임 유지), SitIdle=앉은 상태 루프(매장 앉은 손님은 SitIdle 로 시작)."
        " 루프 설정 필요: Idle/Walk/Run/Phone/Watch/Impatient/LookAt/LookAtLeft/Tap/SitIdle 은 loopTime=on, Sitting/Clapping 은 off."
        " 앉은 상태에서 Phone 을 쓰려면 상체 Avatar Mask 레이어로 SitIdle 위에 얹을 것."
        f" | 소켓: {asset}_Socket_PhoneGrip (Palm.R 자식, NpcSmartphone 을 localPosition/Rotation 0 으로 붙이면 Phone 클립 손에 맞음),"
        f" {asset}_Socket_Head (Head 자식, 눈 위치: 시선/말풍선/목소리 위치)."
    )
    k3d.export(asset, "Characters", [arm], rigged=True, anim=True, notes=notes)
    return paths

"""npc_b 그룹 공용: 쿼터니우스 CharacterArmature NPC 를 고품질로 다시 만든다.
리그(62 본)·웨이트·기본 애니는 유지하고 메시(병합·서브디비전·머리 비율)·재질(천/피부/머리카락 베이크)·소품·새 클립을 더한다.
에셋 스크립트(NpcStaff.py, NpcYouth.py, NpcSuitMan.py)가 이 모듈을 부른다.

좌표: 미터, Z-up, 정면 -Y, 캐릭터 왼쪽 = +X. 레스트 = T 포즈(손바닥 아래, 엄지 앞).
"""
import bpy, bmesh, math, os, sys, subprocess
from mathutils import Vector, Matrix, Quaternion, kdtree
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import k3d

ARTSRC = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REF = os.path.join(ARTSRC, "_ref")
DEC = os.path.join(k3d.CACHE, "npcb")
KEEP_CLIPS = ("Idle", "Idle_Neutral", "Walk", "Run", "Wave", "Interact")  # 총·사망·피격·펀치·킥·칼·구르기는 버림
SEAT = 0.65   # SitPhone 의자 좌판 높이(m)


# ---------------------------------------------------------------- 불러오기

def decals():
    """Pillow 데칼이 없으면 만든다."""
    if not os.path.exists(os.path.join(DEC, "mouth.png")):
        py = os.path.join(ARTSRC, "_cache", "venv", "bin", "python")
        subprocess.check_call([py, os.path.join(HERE, "npcb_decals.py"), DEC])
    return DEC


def fcurves(act):
    out = []
    for L in act.layers:
        for st in L.strips:
            for cb in st.channelbags:
                out += list(cb.fcurves)
    return out


def rest_pose(arm):
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def _apply(arm, key_scale):
    """아마추어+자식의 트랜스폼 적용. 본 로컬 이동 키는 아마추어 단위가 바뀐 만큼 곱한다."""
    kids = [o for o in arm.children]
    k3d.select([arm] + kids, arm)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for a in bpy.data.actions:
        for fc in fcurves(a):
            if fc.data_path.endswith(".location"):
                for kp in fc.keyframe_points:
                    kp.co[1] *= key_scale
                    kp.handle_left[1] *= key_scale
                    kp.handle_right[1] *= key_scale


def load(glb, asset, height, drop=None, head_scale=(0.86, 0.95, 0.96), extra_top=0.0):
    """GLB -> 정리된 리그 + 메시(dict). drop={메시이름일부: [머티리얼..]} 면 삭제. 높이 = height."""
    k3d.reset()
    bpy.context.scene.render.fps = 24
    objs = k3d.import_glb(os.path.join(REF, "models", glb + ".glb"))
    arm = next(o for o in objs if o.type == 'ARMATURE')
    meshes = [o for o in objs if o.type == 'MESH' and o.parent == arm]
    for o in objs:
        if o is not arm and o not in meshes:
            bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions):
        n = a.name.split("|")[-1]
        if n in KEEP_CLIPS:
            a.name = n
        else:
            bpy.data.actions.remove(a)
    arm.animation_data.action = None
    rest_pose(arm)
    arm.name = arm.data.name = asset + "_Armature"
    arm.data.pose_position = 'REST'
    _apply(arm, arm.matrix_world.to_scale().x)          # x100 -> 미터
    for m in meshes:
        for key, mats in (drop or {}).items():
            if key in m.name:
                _drop_faces(m, mats)
    # 머리 비율: 쿼터니우스 머리는 너무 넓다 -> Head 웨이트만큼 머리 피벗 기준으로 줄인다
    piv = arm.data.bones["Head"].head_local.copy()
    for m in meshes:
        g = m.vertex_groups.get("Head")
        if not g:
            continue
        for v in m.data.vertices:
            w = next((x.weight for x in v.groups if x.group == g.index), 0.0)
            if w > 0:
                d = v.co - piv
                v.co = piv + Vector((d.x * (1 + (head_scale[0] - 1) * w), d.y * (1 + (head_scale[1] - 1) * w),
                                     d.z * (1 + (head_scale[2] - 1) * w)))
    top = max(v.co.z for m in meshes for v in m.data.vertices)
    s = height / (top + extra_top)
    arm.scale = (s, s, s)
    _apply(arm, s)
    arm.data.pose_position = 'POSE'
    return arm, {m.name.split("_")[-1]: m for m in meshes}


def face(head, push=0.5):
    """쿼터니우스 긴 코를 얼굴면 쪽으로 눌러 줄이고(돌출량의 push 배), 입 데칼 (중심, 크기)를 돌려준다. upgrade 전에 부른다."""
    mats = [s.material.name if s.material else "" for s in head.material_slots]
    co = np.array([tuple(v.co) for v in head.data.vertices])
    def ids(pred):
        return sorted({v for p in head.data.polygons if pred(mats[p.material_index]) for v in p.vertices})
    E = co[ids(lambda n: n == "Eye")]
    E = E[E[:, 1] < -0.06]
    ez = (E[:, 2].min() + E[:, 2].max()) / 2
    sk = ids(lambda n: "Skin" in n)
    S = co[sk]
    mid = S[(np.abs(S[:, 0]) < 0.008) & (S[:, 1] < -0.08) & (S[:, 2] > ez - 0.09) & (S[:, 2] < ez - 0.06)]   # 앞면만
    ref = float(np.median(mid[:, 1]))                  # 입 높이 얼굴 앞면 y (코를 뺀 얼굴면)
    sm = lambda x, a, b: min(1.0, max(0.0, (x - a) / (b - a))) ** 2 * (3 - 2 * min(1.0, max(0.0, (x - a) / (b - a))))
    n = 0
    for i in sk:
        v = head.data.vertices[i]
        x, y, z = v.co
        pr = ref - y
        if pr <= 0 or abs(x) > 0.032 or not (ez - 0.06 < z < ez + 0.015):
            continue
        k = push * (1 - sm(abs(x), 0.012, 0.032)) * sm(z, ez - 0.06, ez - 0.045) * (1 - sm(z, ez, ez + 0.015))
        v.co.y += pr * k
        n += 1
    print("npcb: nose verts", n, "face y", round(ref, 4), "eye z", round(ez, 4))
    return ((0.0, ref, ez - 0.066), (0.055, 0.05))


def _drop_faces(o, mat_names):
    ids = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name in mat_names]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in ids], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()


# ---------------------------------------------------------------- 메시 업그레이드

def upgrade(o, levels=1, merge=None):
    """겹친 점 병합 -> 사각형화 -> 서브디비전(아마추어 앞에서 적용, 웨이트 보간) -> 스무스."""
    if merge is None:   # 바지 옆선 이음매는 틈이 커서 1.5mm, 눈·눈썹·손가락이 있는 머리·몸은 0.6mm
        merge = 0.0015 if o.name.endswith("Legs") else 0.0006
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    print("npcb: open edges", o.name, sum(1 for e in bm.edges if len(e.link_faces) == 1))
    bmesh.ops.join_triangles(bm, faces=bm.faces, cmp_materials=True, cmp_seam=False, cmp_sharp=False,
                             cmp_uvs=False, angle_face_threshold=math.radians(40),
                             angle_shape_threshold=math.radians(40))
    bm.to_mesh(o.data)
    bm.free()
    arm_mod = [(m.object) for m in o.modifiers if m.type == 'ARMATURE']
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    sub = o.modifiers.new("Sub", 'SUBSURF')
    sub.levels = sub.render_levels = levels
    sub.quality = 3
    sub.uv_smooth = 'PRESERVE_CORNERS'
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier="Sub")
    for a in arm_mod:
        add_armature(o, a)
    k3d.smooth(o, 180)
    for e in o.data.edges:
        e.use_edge_sharp = False


def add_armature(o, arm):
    o.parent = arm
    m = o.modifiers.new("Armature", 'ARMATURE')
    m.object = arm
    return m


def rigid(o, bone, arm):
    """오브젝트 전체를 한 본에 100% 붙인다."""
    g = o.vertex_groups.new(name=bone)
    g.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
    add_armature(o, arm)
    return o


def copy_weights(src, objs):
    """옷 위 소품(끈·명찰줄): 가장 가까운 src 점의 웨이트를 복사하고 아마추어를 붙인다."""
    kd = kdtree.KDTree(len(src.data.vertices))
    for v in src.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    names = {g.index: g.name for g in src.vertex_groups}
    for o in objs:
        groups = {}
        for v in o.data.vertices:
            for g in src.data.vertices[kd.find(v.co)[1]].groups:
                if g.weight > 1e-4:
                    n = names[g.group]
                    if n not in groups:
                        groups[n] = o.vertex_groups.new(name=n)
                    groups[n].add([v.index], g.weight, 'REPLACE')
        add_armature(o, src.parent)


def new_obj(name, bm, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if me.uv_layers:   # bmesh verify() 는 'Float2' 로 만든다 -> 합칠 때 몸의 UVMap 과 같은 층이 되게
        me.uv_layers[0].name = "UVMap"
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for m in mats:
        me.materials.append(m)
    return o


def set_mats(o, mapping):
    """원래 머티리얼 이름 -> 새 머티리얼 (중복 슬롯 없이 면 인덱스 재배치)."""
    old = [s.material.name if s.material else None for s in o.material_slots]
    new, idx = [], {}
    for i, n in enumerate(old):
        m = mapping.get(n) or mapping["*"]
        if m not in new:
            new.append(m)
        idx[i] = new.index(m)
    mi = np.empty(len(o.data.polygons), np.int32)
    o.data.polygons.foreach_get("material_index", mi)
    mi = np.array([idx.get(int(i), 0) for i in mi], np.int32)
    o.data.materials.clear()
    for m in new:
        o.data.materials.append(m)
    o.data.polygons.foreach_set("material_index", mi)


def join(objs, name):
    """메시 합치기 (아마추어 모디파이어 하나만 남김)."""
    arm = objs[0].parent
    for o in objs:
        for m in list(o.modifiers):
            o.modifiers.remove(m)
    k3d.select(objs, objs[0])
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    add_armature(o, arm)
    return o


def ray(o, origin, direction):
    """오브젝트(항등 변환) 표면 레이캐스트 -> (위치, 노멀) 또는 None."""
    ok, loc, nor, _ = o.ray_cast(Vector(origin), Vector(direction).normalized())
    return (loc, nor) if ok else None


def mat_bounds(o, names):
    ids = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name in names]
    vs = [o.data.vertices[v].co for p in o.data.polygons if p.material_index in ids for v in p.vertices]
    a = np.array([tuple(v) for v in vs])
    return a.min(0), a.max(0)


# ---------------------------------------------------------------- 재질 노드 도우미

def _sock(socks, ident):
    return next(s for s in socks if s.identifier == ident)


class NB:
    """절차 머티리얼 빌더 (Principled 하나 -> k3d.bake 대상)."""

    def __init__(self, name, base=(0.5, 0.5, 0.5), rough=0.5, metal=0.0):
        self.m = k3d.mat(name, base, rough, metal)
        self.nt = self.m.node_tree
        self.p = k3d.principled(self.m)
        self.tc = self.nt.nodes.new('ShaderNodeTexCoord')
        self.geo = self.nt.nodes.new('ShaderNodeNewGeometry')
        self.obj = self.tc.outputs['Object']
        sep = self.nt.nodes.new('ShaderNodeSeparateXYZ')
        self.L(self.obj, sep.inputs[0])
        self.X, self.Y, self.Z = sep.outputs
        nsep = self.nt.nodes.new('ShaderNodeSeparateXYZ')
        self.L(self.geo.outputs['Normal'], nsep.inputs[0])
        self.NX, self.NY, self.NZ = nsep.outputs
        self.bumps = []

    def L(self, a, b):
        self.nt.links.new(a, b)

    def _in(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.L(v, sock)
        elif isinstance(v, (tuple, list)) and len(v) == 3 and sock.type == 'RGBA':
            sock.default_value = (*v, 1)
        else:
            sock.default_value = v

    def node(self, t, **kw):
        n = self.nt.nodes.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def math(self, op, a, b=0.0, c=0.0, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        self._in(n.inputs[2], c)
        return n.outputs[0]

    def ramp(self, v, a, b):
        """v 를 a..b 에서 0..1 로 (클램프, 부드럽게)."""
        n = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP', clamp=True)
        self._in(n.inputs['Value'], v)
        n.inputs['From Min'].default_value, n.inputs['From Max'].default_value = a, b
        return n.outputs['Result']

    def noise(self, scale, detail=3.0, rough=0.5, dist=0.0, vec=None):
        n = self.node('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist
        self.L(vec or self.obj, n.inputs['Vector'])
        return n.outputs['Fac']

    def wave(self, scale, direction='X', dist=6.0, detail=3.0, kind='BANDS'):
        n = self.node('ShaderNodeTexWave', wave_type=kind)
        if kind == 'BANDS':
            n.bands_direction = direction
        else:
            n.rings_direction = direction
        n.inputs['Scale'].default_value = scale
        n.inputs['Distortion'].default_value = dist
        n.inputs['Detail'].default_value = detail
        self.L(self.obj, n.inputs['Vector'])
        return n.outputs['Fac']

    def voronoi(self, scale, feature='F1', out='Distance'):
        n = self.node('ShaderNodeTexVoronoi', feature=feature)
        n.inputs['Scale'].default_value = scale
        self.L(self.obj, n.inputs['Vector'])
        return n.outputs[out]

    def mixc(self, fac, a, b, blend='MIX'):
        n = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_result=True)
        self._in(_sock(n.inputs, 'Factor_Float'), fac)
        self._in(_sock(n.inputs, 'A_Color'), a)
        self._in(_sock(n.inputs, 'B_Color'), b)
        return _sock(n.outputs, 'Result_Color')

    def ao(self, dist):
        n = self.node('ShaderNodeAmbientOcclusion', only_local=True, samples=16)
        n.inputs['Distance'].default_value = dist
        return n.outputs['AO']

    def bump(self, h, strength, dist):
        n = self.node('ShaderNodeBump')
        self._in(n.inputs['Height'], h)
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = dist
        if self.bumps:
            self.L(self.bumps[-1].outputs['Normal'], n.inputs['Normal'])
        self.bumps.append(n)

    def decal(self, color, img, center, size, depth=0.05, face=0.25):
        """정면(-Y) 평면 투영 데칼. 반환 (색, 알파)."""
        cx, cy, cz = center
        w, h = size
        u = self.math('MULTIPLY_ADD', self.X, 1.0 / w, 0.5 - cx / w)
        v = self.math('MULTIPLY_ADD', self.Z, 1.0 / h, 0.5 - cz / h)
        comb = self.node('ShaderNodeCombineXYZ')
        self.L(u, comb.inputs[0])
        self.L(v, comb.inputs[1])
        t = self.node('ShaderNodeTexImage', extension='CLIP', interpolation='Cubic')
        t.image = k3d.load_image(os.path.join(DEC, img))
        self.L(comb.outputs[0], t.inputs['Vector'])
        facing = self.ramp(self.math('MULTIPLY', self.NY, -1.0), face, face + 0.25)
        near = self.math('SUBTRACT', 1.0, self.ramp(self.math('ABSOLUTE', self.math('SUBTRACT', self.Y, cy)),
                                                      depth * 0.6, depth))
        a = self.math('MULTIPLY', self.math('MULTIPLY', t.outputs['Alpha'], facing), near)
        return self.mixc(a, color, t.outputs['Color']), a

    def done(self, color, rough):
        self._in(self.p.inputs['Base Color'], color)
        self._in(self.p.inputs['Roughness'], rough)
        if self.bumps:
            self.L(self.bumps[-1].outputs['Normal'], self.p.inputs['Normal'])
        return self.m


def sc(c, k):
    return tuple(min(1.0, x * k) for x in c[:3])


def fabric(name, col, rough=0.82, var=0.10, grain=0.18, grain_scale=1100.0, folds=0.22, cavity=0.5,
           decals=(), twill=0.0, wear=0.0, emb=0.25, sheen_var=0.0):
    """천: 색 얼룩 + 주름(물결 왜곡) + 올 결 + 틈 때(AO) + 닳은 모서리 + 데칼(프린트/자수)."""
    b = NB(name, col, rough)
    c = b.mixc(b.noise(5.0, 3, 0.55), sc(col, 1 - var), sc(col, 1 + var))
    c = b.mixc(b.math('MULTIPLY', b.noise(40.0, 2, 0.6), 0.35), c, sc(col, 1.12))  # 보풀/멜란지
    if wear:  # 튀어나온 모서리가 바래고 닳음
        pm = b.math('MULTIPLY', b.ramp(b.geo.outputs['Pointiness'], 0.52, 0.62), b.noise(25.0, 3))
        c = b.mixc(b.math('MULTIPLY', pm, wear * 2), c, sc(col, 1.8))
    c = b.mixc(b.ao(0.035), sc(col, 1 - cavity), c)
    for img, center, size in decals:
        c, a = b.decal(c, img, center, size)
        b.bump(a, emb, 0.0008)
    if twill:
        tw = b.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL')
        tw.inputs['Scale'].default_value = 520.0
        tw.inputs['Distortion'].default_value = 0.6
        b.L(b.obj, tw.inputs['Vector'])
        b.bump(tw.outputs['Fac'], twill, 0.0005)
        c = b.mixc(b.math('MULTIPLY', tw.outputs['Fac'], 0.35), c, sc(col, 1.25))
    b.bump(b.noise(grain_scale, 2, 0.6), grain, 0.0006)
    b.bump(b.wave(9.0, 'Z', 9.0, 2.0), folds, 0.006)        # 가로 주름
    b.bump(b.noise(7.0, 3, 0.6, dist=1.0), folds * 0.8, 0.008)
    r = b.math('MULTIPLY_ADD', b.noise(18.0, 2), 0.14, rough - 0.07)
    return b.done(c, r)


def skin(name, tone, mouth=None):
    """mouth=(중심, 크기): face() 결과. 입선·입술·인중 음영 데칼."""
    b = NB(name, tone, 0.5)
    c = b.mixc(b.noise(16.0, 3, 0.5), sc(tone, 0.92), sc(tone, 1.05))
    red = (tone[0] * 1.06, tone[1] * 0.80, tone[2] * 0.78)
    c = b.mixc(b.math('MULTIPLY', b.noise(4.0, 2, 0.5), 0.45), c, red)          # 홍조 얼룩
    c = b.mixc(b.math('MULTIPLY', b.noise(160.0, 2), 0.18), c, sc(tone, 0.85))  # 잡티
    c = b.mixc(b.ao(0.02), (tone[0] * 0.45, tone[1] * 0.34, tone[2] * 0.31), c)     # 틈 그늘 (채도 낮게: 양말 위 붉은 띠 방지)
    if mouth:
        c, _ = b.decal(c, "mouth.png", mouth[0], mouth[1], depth=0.03)
    b.bump(b.voronoi(1100.0), 0.07, 0.00025)                                    # 모공
    b.bump(b.noise(300.0, 2), 0.05, 0.0003)
    r = b.math('MULTIPLY_ADD', b.noise(25.0, 2), 0.16, 0.42)
    return b.done(c, r)


def hair(name, col, rough=0.45):
    """머리카락: hair_flow() 가 만든 HairUV(U=가로, V=결 방향, 미터)로 결이 덩어리를 따라 흐른다.
    대비는 색·거칠기로 주고 범프는 약하게 (직물·밧줄 무늬 방지)."""
    b = NB(name, col, rough)
    sep = b.node('ShaderNodeSeparateXYZ')
    b.L(b.node('ShaderNodeUVMap', uv_map="HairUV").outputs[0], sep.inputs[0])
    vec = b.node('ShaderNodeCombineXYZ')
    b.L(sep.outputs[0], vec.inputs[0])
    b.L(b.math('MULTIPLY', sep.outputs[1], 0.06), vec.inputs[1])        # 결 방향으로 16배 늘임
    s = b.math('ADD', b.math('MULTIPLY', b.noise(500.0, 3, 0.6, vec=vec.outputs[0]), 0.6),     # 가닥 ~2mm (1024 아틀라스에서 보이게)
               b.math('MULTIPLY', b.noise(120.0, 2, 0.5, vec=vec.outputs[0]), 0.4))
    c = b.mixc(b.ramp(s, 0.3, 0.7), sc(col, 0.65), sc(col, 1.8))
    c = b.mixc(b.math('MULTIPLY', b.noise(10.0, 2), 0.4), c, sc(col, 1.2))
    c = b.mixc(b.ao(0.02), sc(col, 0.4), c)
    b.bump(s, 0.12, 0.0006)
    r = b.math('MULTIPLY_ADD', s, 0.2, rough - 0.1)
    return b.done(c, r)


def hair_flow(o, mats, tuck=0.008):
    """머리카락 섬마다 주축(PCA) = 결 방향으로 HairUV 를 만든다. 이마 위 섬은 아래 끝을 tuck 만큼 뒤로 넣어 톱니 헤어라인을 줄인다."""
    me = o.data
    ids = {i for i, s_ in enumerate(o.material_slots) if s_.material in mats}
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = np.zeros((len(me.vertices), 2))
    seen, n = set(), 0
    for f in bm.faces:
        if f.material_index not in ids or f.index in seen:
            continue
        st, vs, ns = [f], set(), []
        seen.add(f.index)
        while st:
            g = st.pop()
            vs.update(v.index for v in g.verts)
            ns.append(tuple(g.normal))
            for e in g.edges:
                for q in e.link_faces:
                    if q.material_index in ids and q.index not in seen:
                        seen.add(q.index)
                        st.append(q)
        vs = list(vs)
        P = np.array([tuple(me.vertices[i].co) for i in vs])
        c = P.mean(0)
        ax = np.linalg.svd(P - c, full_matrices=False)[2][0]
        ac = np.cross(ax, np.mean(ns, 0))
        ac /= np.linalg.norm(ac) + 1e-9
        uv[vs, 0] = (P - c) @ ac + n * 0.37
        uv[vs, 1] = (P - c) @ ax
        F = P[:, 1] < -0.10                              # 이마 위 앞쪽 점 (눈썹처럼 납작한 섬은 제외)
        if F.any() and np.ptp(P[:, 2]) > 0.02:
            lo = P[F, 2].min()
            for i, p, fr in zip(vs, P, F):
                if fr and p[2] < lo + 0.015:
                    me.vertices[i].co.y += tuck * (1 - (p[2] - lo) / 0.015)
        n += 1
    bm.free()
    lay = me.uv_layers.new(name="HairUV")
    li = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", li)
    lay.data.foreach_set("uv", uv[li].astype(np.float32).ravel())
    print("npcb: hair islands", n)


def leather(name, col, rough=0.32, sole=None, sole_h=0.028, sole_rough=0.85, scuff=0.35):
    """구두/운동화: 주름 + 앞코 스크래치(Pointiness) + 밑창(높이 마스크) + 바닥 먼지."""
    b = NB(name, col, rough)
    c = b.mixc(b.noise(30.0, 3), sc(col, 0.85), sc(col, 1.15))
    pm = b.math('MULTIPLY', b.ramp(b.geo.outputs['Pointiness'], 0.52, 0.6), b.noise(60.0, 3))
    c = b.mixc(b.math('MULTIPLY', pm, scuff * 2.5), c, sc(col, 2.2) if max(col) < 0.2 else sc(col, 0.7))
    r = b.math('MULTIPLY_ADD', pm, 0.3, rough)
    if sole:
        m = b.math('SUBTRACT', 1.0, b.ramp(b.Z, sole_h, sole_h + 0.004))
        c = b.mixc(m, c, sole)
        r = b.mixc(m, (rough, rough, rough), (sole_rough,) * 3)
    dust = b.math('SUBTRACT', 1.0, b.ramp(b.Z, 0.0, 0.035))
    c = b.mixc(b.math('MULTIPLY', dust, 0.5), c, (0.18, 0.16, 0.14))
    c = b.mixc(b.ao(0.015), sc(col, 0.5), c)
    b.bump(b.wave(55.0, 'Y', 5.0, 2.0), 0.05, 0.0012)    # 앞코 주름 (약하게: 줄무늬로 보이지 않게)
    b.bump(b.noise(500.0, 2), 0.08, 0.0003)
    return b.done(c, r)


def flat(name, col, rough=0.5, metal=0.0, var=0.05):
    b = NB(name, col, rough, metal)
    c = b.mixc(b.noise(60.0, 2), sc(col, 1 - var), sc(col, 1 + var))
    b.bump(b.noise(400.0, 2), 0.05, 0.0003)
    return b.done(c, rough)


# ---------------------------------------------------------------- 소품 지오메트리

def bm_box(bm, size, center=(0, 0, 0), mat=0):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
    return r["verts"]


def bevel_obj(o, w=0.002, seg=2):
    m = o.modifiers.new("Bev", 'BEVEL')
    m.width, m.segments, m.limit_method = w, seg, 'ANGLE'
    m.harden_normals = False
    k3d.select([o])
    bpy.ops.object.modifier_apply(modifier="Bev")
    k3d.smooth(o, 35)


def phone(asset, arm):
    """오른손 손바닥에 쥔 스마트폰 (레스트 T 포즈 기준, Wrist.R 100%). 화면은 손바닥 반대(-Z)."""
    W, H, T = 0.071, 0.147, 0.0082
    bm = bmesh.new()
    bm_box(bm, (W, H, T), mat=0)
    bm_box(bm, (0.026, 0.03, 0.0016), (-0.016, 0.052, T / 2 + 0.0007), mat=0)      # 카메라 섬
    o = new_obj(asset + "_Phone", bm)
    bevel_obj(o, 0.0028, 3)
    # 화면 면: -Z 를 보는 면 중 가장 바깥 -> 살짝 안쪽 인셋해서 유리 베젤
    bm = bmesh.new()
    bm.from_mesh(o.data)
    top = [f for f in bm.faces if f.normal.z < -0.99 and f.calc_center_median().z < -T / 2 + 0.0005]
    r = bmesh.ops.inset_region(bm, faces=top, thickness=0.0022, depth=0.0)
    uvl = bm.loops.layers.uv.verify()
    for f in top:
        f.material_index = 1
        for l in f.loops:
            l[uvl].uv = (0.5 - l.vert.co.x / (W - 0.0044), l.vert.co.y / (H - 0.0044) + 0.5)
    bm.to_mesh(o.data)
    bm.free()
    o.data.uv_layers[0].name = "UVMap"   # verify() 가 만든 'Float2' -> 화면 UVMap 노드가 읽게
    body = flat(asset + "_phone_body", (0.030, 0.031, 0.035), 0.32, 0.0)   # 유리 뒷면(비금속): 하늘 반사로 하얗게 뜨지 않게
    k3d.principled(body).inputs['Emission Color'].default_value = (0, 0, 0, 1)  # 기본 흰색이 발광맵에 구워지지 않게
    scr = NB(asset + "_phone_screen", (0.0, 0.0, 0.0), 0.05)
    t = scr.node('ShaderNodeTexImage')
    t.image = k3d.load_image(os.path.join(DEC, "phone_screen.png"))
    uvn = scr.node('ShaderNodeUVMap', uv_map="UVMap")
    scr.L(uvn.outputs[0], t.inputs['Vector'])
    scr.L(t.outputs['Color'], scr.p.inputs['Emission Color'])
    scr.p.inputs['Emission Strength'].default_value = 1.6
    scr.done(scr.mixc(0.15, (0.01, 0.01, 0.012), t.outputs['Color']), 0.08)
    o.data.materials.append(body)
    o.data.materials.append(scr.m)
    # 실제 한 손 파지: 폭 = 손바닥 두덩~손가락 둘째마디(X), 길이 = 앞뒤(위 = 엄지 쪽 -Y), 뒷면이 손바닥, 화면 = -Z
    bones = arm.data.bones
    mid, pin = bones["Middle2.R"].head_local, bones["Pinky2.R"].head_local
    c = Vector((mid.x - 0.004 + PHONE_DX, pin.y + 0.014 - H / 2, mid.z - 0.017))
    o.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.pi, 4, 'Z'))
    return rigid(o, "Wrist.R", arm)


GRIP = ((2, 0.30), (3, 1.25), (4, 0.85))   # 손가락 관절별 굽힘(rad): 폰 뒷면 -> 먼 쪽 모서리를 감쌈
PHONE_DX = 0.018                            # 폰을 손바닥 중심 쪽(+X)으로 옮긴 거리


def grip(P, w):
    """오른손 폰 쥐기: 손가락은 폰 뒷면을 받치고 먼 쪽 모서리를 감싸며, 엄지는 화면 쪽 옆면에 붙는다."""
    for fn, k in (("Index", 0.92), ("Middle", 1.0), ("Ring", 1.06), ("Pinky", 1.12)):
        for i, a in GRIP:
            P.local(f"{fn}{i}.R", (0, -1, 0), a * k * w)
    P.local("Thumb1.R", (1, 0, 0), 0.30 * w)
    P.local("Thumb1.R", (0, 0, 1), -0.30 * w)


def face_screen(P, w):
    """폰 화면(손바닥 반대 -Z)이 눈을 보게: 아래팔 비틀기(팔 축) + 남는 각은 손목."""
    pb, b = P.pb["Wrist.R"], P.arm.data.bones["Wrist.R"]

    def nrm():
        P.upd()
        return ((pb.matrix @ b.matrix_local.inverted()).to_3x3() @ Vector((0, 0, -1))).normalized()
    P.upd()
    want = (P.p("Head") + Vector((0, -0.08, 0.07)) - P.p("Wrist.R")).normalized()
    ax = (P.p("Wrist.R") - P.p("LowerArm.R")).normalized()
    a = nrm()
    pa, pw = (a - ax * a.dot(ax)).normalized(), (want - ax * want.dot(ax)).normalized()
    P.turn("LowerArm.R", ax, math.atan2(ax.dot(pa.cross(pw)), pa.dot(pw)) * w)
    P.aim_dir("Wrist.R", nrm(), want, w)


def socket(name, arm, bone, world):
    """본에 붙는 소켓 엠프티 (레스트 기준 월드 위치)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', 0.05
    bpy.context.scene.collection.objects.link(e)
    e.parent = arm
    if bone:
        e.parent_type, e.parent_bone = 'BONE', bone
    bpy.context.view_layer.update()
    e.matrix_world = Matrix.Translation(Vector(world))
    return e


# ---------------------------------------------------------------- 포즈 저작 (프로토타입 mr()/Xr() 와 같은 방식)

def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def env(f, a, b, c, d):
    if f <= a or f >= d:
        return 0.0
    if f < b:
        return ease((f - a) / (b - a))
    if f <= c:
        return 1.0
    return ease((d - f) / (d - c))


class Poser:
    def __init__(self, arm):
        self.arm, self.pb = arm, arm.pose.bones

    def upd(self):
        bpy.context.view_layer.update()

    def p(self, b):
        return self.pb[b].matrix.translation.copy()

    def _rot(self, b, R, pivot=None):
        self.upd()
        pb = self.pb[b]
        M = pb.matrix.copy()
        t = M.translation.copy() if pivot is None else Vector(pivot)
        pb.matrix = Matrix.Translation(t) @ R.to_4x4() @ Matrix.Translation(-t) @ M
        self.upd()

    def turn(self, b, axis, ang, pivot=None):
        """아마추어 공간 축으로 회전 (본 머리 기준)."""
        if abs(ang) > 1e-5:
            self._rot(b, Matrix.Rotation(ang, 3, Vector(axis)), pivot)

    def aim(self, a, b, d, w=1.0):
        """본 a 를 돌려 a->b 방향을 d 로."""
        self.upd()
        self.aim_dir(a, self.p(b) - self.p(a), d, w)

    def aim_dir(self, a, cur, d, w=1.0):
        q = cur.normalized().rotation_difference(Vector(d).normalized())
        if w < 1:
            q = Quaternion().slerp(q, max(0.0, w))
        self._rot(a, q.to_matrix())

    def local(self, b, axis, ang):
        """레스트 기준 축 회전 (손가락 굽힘·손목 비틀기). 업데이트는 다음 읽기 때."""
        if abs(ang) < 1e-5:
            return
        pb = self.pb[b]
        ax = (pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis)).normalized()
        pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(ax, ang)

    def move(self, b, delta):
        self.upd()
        pb = self.pb[b]
        M = pb.matrix.copy()
        M.translation += Vector(delta)
        pb.matrix = M
        self.upd()


def curl(P, side, a, index=None, thumb=0.0):
    """손가락 굽힘 (손바닥 쪽). side 'R'/'L'."""
    ax = (0, -1, 0) if side == 'R' else (0, 1, 0)
    for fn in ("Index", "Middle", "Ring", "Pinky"):
        aa = a if (fn != "Index" or index is None) else index
        for i, k in ((2, 1.0), (3, 0.9), (4, 0.7)):   # 1 번은 손바닥뼈(손목에서 시작)
            P.local(f"{fn}{i}.{side}", ax, aa * k)
    if thumb:
        for i in (2, 3):
            P.local(f"Thumb{i}.{side}", (0, 0, 1) if side == 'R' else (0, 0, -1), thumb * 0.5)


def leg(P, side, thigh, shin, w=1.0):
    """허벅지·정강이 방향 지정 + 발(Root 자식, 원래 IK 목표)을 정강이 끝으로 옮긴다."""
    ul, ll, ft = "UpperLeg." + side, "LowerLeg." + side, "Foot." + side
    bones = P.arm.data.bones
    P.aim(ul, ll, thigh, w)
    rel = bones[ll].matrix_local.inverted() @ bones[ft].matrix_local
    P.upd()
    P.aim_dir(ll, (P.pb[ll].matrix @ rel).translation - P.p(ll), shin, w)
    tgt = P.pb[ll].matrix @ rel
    pf = P.pb[ft]
    pf.matrix = pf.matrix.lerp(tgt, w)
    P.upd()


def hold_phone(P, w, f, scroll_period=40, sit=False):
    """한 손 폰 보기: 위팔 아래-앞, 아래팔 앞-위-안쪽(뒤침), 머리 숙임 + 엄지 스크롤. 왼팔은 내림/허벅지 위."""
    P.aim("UpperArm.R", "LowerArm.R", (-0.10, -0.30, -0.95), w)
    P.aim("LowerArm.R", "Wrist.R", (0.40, -0.86, 0.32), w)
    P.local("LowerArm.R", (1, 0, 0), -1.5 * w)      # 뒤침(손바닥이 얼굴 쪽): 아래팔+손목에 나눠 총 -pi
    P.local("Wrist.R", (1, 0, 0), -1.6 * w)
    P.local("Wrist.R", (0, 1, 0), 0.2 * w)
    if sit:  # 왼팔: 아래팔을 왼쪽 허벅지 위에 걸침
        P.aim("UpperArm.L", "LowerArm.L", (0.16, -0.30, -0.94), w)
        P.aim("LowerArm.L", "Wrist.L", (0.05, -0.62, -0.78), w)
        curl(P, "L", 0.6 * w, thumb=0.2 * w)
    else:    # 왼팔: 몸 옆에 느슨하게
        P.aim("UpperArm.L", "LowerArm.L", (0.20, 0.02, -0.98), w * 0.8)
        P.aim("LowerArm.L", "Wrist.L", (0.10, -0.25, -0.96), w * 0.8)
        curl(P, "L", 0.3 * w, thumb=0.1 * w)
    grip(P, w)
    ph = (f % scroll_period) / scroll_period
    flick = math.sin(ph / 0.25 * math.pi) if ph < 0.25 else 0.0
    P.local("Thumb2.R", (0, 0, 1), (-0.10 + 0.25 * flick) * w)
    P.upd()
    P.turn("Neck", (1, 0, 0), 0.20 * w)
    P.turn("Head", (1, 0, 0), (0.36 + 0.03 * math.sin(f * 0.11)) * w)
    face_screen(P, w)


def prog_phone(P, f, N):
    hold_phone(P, 1.0, f)


def prog_sitphone(P, f, N):
    P.upd()
    hz = P.p("UpperLeg.L").z
    P.move("Body", (0, 0.03, SEAT + 0.085 - hz))
    P.turn("Hips", (1, 0, 0), -0.14)
    P.turn("Abdomen", (1, 0, 0), 0.10)
    P.turn("Torso", (1, 0, 0), 0.09)
    P.turn("Chest", (1, 0, 0), 0.10 + 0.012 * math.sin(2 * math.pi * f / 60))
    leg(P, "L", (0.16, -0.98, -0.05), (0.05, 0.12, -0.99))
    leg(P, "R", (-0.12, -0.99, -0.03), (-0.02, 0.20, -0.98))
    hold_phone(P, 1.0, f, scroll_period=60, sit=True)


def prog_impatient(P, f, N):
    P.aim("UpperArm.R", "LowerArm.R", (-0.20, -0.42, -0.89))
    P.aim("LowerArm.R", "Wrist.R", (0.90, -0.40, 0.18))
    P.aim("UpperArm.L", "LowerArm.L", (0.20, -0.30, -0.93))
    P.aim("LowerArm.L", "Wrist.L", (-0.92, -0.28, 0.26))
    P.local("LowerArm.R", (1, 0, 0), -0.6)
    P.local("LowerArm.L", (1, 0, 0), 0.4)
    curl(P, "R", 0.5, thumb=0.2)
    curl(P, "L", 0.5, thumb=0.2)
    # 오른발 발끝 까딱 (뒤꿈치 기준)
    ph = (f % 20) / 20
    lift = math.sin(ph / 0.45 * math.pi) if ph < 0.45 else 0.0
    P.upd()
    piv = P.p("Foot.R") + Vector((0, 0.05, -0.02))
    P.turn("Foot.R", (1, 0, 0), -0.32 * lift, pivot=piv)
    P.turn("Head", (0, 0, 1), 0.26 * math.sin(2 * math.pi * f / N))
    sigh = env(f, 44, 52, 56, 68)
    P.turn("Chest", (1, 0, 0), -0.06 * sigh)
    P.turn("Head", (1, 0, 0), -0.14 * sigh + 0.06)


def prog_point(P, f, N):
    w = env(f, 0, 12, 58, 78)
    jab = 0.10 * (env(f, 20, 24, 24, 30) + env(f, 36, 40, 40, 46))
    P.turn("Chest", (0, 0, 1), -0.14 * w)
    P.aim("UpperArm.R", "LowerArm.R", (-0.55, -0.60, -0.58), w)
    P.aim("LowerArm.R", "Wrist.R", (-0.42, -0.88, -0.22 - jab), w)
    P.local("LowerArm.R", (1, 0, 0), -0.5 * w)
    curl(P, "R", 1.25 * w, index=0.0, thumb=0.5 * w)
    P.upd()
    P.turn("Head", (0, 0, 1), -0.32 * w)
    P.turn("Head", (1, 0, 0), (0.10 + jab * 0.5) * w)


def prog_sitpoint(P, f, N):
    """SitPhone 0프레임 자세(고정) 위에 왼손 검지로 정면(±10°) 키오스크를 귀찮게 가리킴. 0/N 프레임 = SitPhone 0프레임."""
    prog_sitphone(P, 0, 120)
    w = env(f, 0, 12, 58, 78)
    jab = 0.08 * (env(f, 22, 26, 26, 32) + env(f, 38, 42, 42, 48))
    P.aim("UpperArm.L", "LowerArm.L", (0.18, -0.72, -0.67), w)
    P.aim("LowerArm.L", "Wrist.L", (-0.08, -0.86, 0.50 - jab), w)       # 아래팔을 들어 화면 높이를 가리킴
    curl(P, "L", 0.75 * w, index=-0.6 * w, thumb=0.35 * w)
    P.upd()
    P.turn("Head", (1, 0, 0), -0.14 * w)                 # 폰에서 잠깐 눈을 듦
    P.turn("Head", (0, 0, 1), 0.06 * w)


def prog_lookback(P, f, N):
    w = env(f, 0, 18, 52, 74)
    for b, a in (("Hips", -0.10), ("Abdomen", -0.12), ("Torso", -0.16), ("Chest", -0.22), ("Neck", -0.40),
                 ("Head", -0.62)):
        P.turn(b, (0, 0, 1), a * w)
    P.turn("Head", (1, 0, 0), -0.05 * w)
    P.aim("UpperArm.R", "LowerArm.R", (-0.25, 0.05, -0.97), w * 0.5)


CLIPS = (("SitPhone", 120, prog_sitphone), ("Phone", 80, prog_phone), ("Impatient", 80, prog_impatient),
         ("PointScreen", 80, prog_point), ("LookBack", 80, prog_lookback))


def author_clips(arm):
    """Idle 위에 포즈를 얹어 새 클립을 굽는다 (매 프레임 키, 쿼터니언 부호 연속)."""
    sc_ = bpy.context.scene
    ad = arm.animation_data or arm.animation_data_create()
    base = bpy.data.actions["Idle"]
    blen = int(round(base.frame_range[1]))
    P = Poser(arm)
    for name, N, prog, *frozen in CLIPS:
        snaps = []
        for f in range(N + 1):
            rest_pose(arm)          # Idle 에 키가 없는 본(손가락·발 등)이 누적되지 않게
            ad.action = base
            if ad.action_slot is None:
                ad.action_slot = base.slots[0]
            sc_.frame_set(0 if frozen else f % blen)    # frozen: 바탕 Idle 을 0프레임에 고정 (앞뒤 클립과 이음매 없게)
            ad.action = None
            prog(P, f, N)
            P.upd()
            snaps.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in arm.pose.bones})
        act = bpy.data.actions.new(name)
        act.use_fake_user = True    # 저장 시 사용자 0 이라 .blend 에서 빠지지 않게
        ad.action = act
        prev = {}
        for f, snap in enumerate(snaps):
            for pb in arm.pose.bones:
                loc, q = snap[pb.name]
                if pb.name in prev and prev[pb.name].dot(q) < 0:
                    q = -q
                prev[pb.name] = q
                pb.location, pb.rotation_quaternion = loc, q
                pb.keyframe_insert("location", frame=f, group=pb.name)
                pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        ad.action = None
    rest_pose(arm)


def play(arm, clip, frame):
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions[clip]
    ad.action = act
    if ad.action_slot is None and act.slots:
        ad.action_slot = act.slots[0]
    bpy.context.scene.frame_set(frame)


# ---------------------------------------------------------------- 마무리

def bake_all(arm, parts):
    """parts=[(obj, size, ao_dist)] — 레스트 포즈로 굽는다 (폰은 몸 AO 에서 빠짐)."""
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    allm = [o for o, *_ in parts]
    for o, size, aod in parts:
        solo = o.name.endswith("_Phone")
        for x in allm:
            x.hide_render = (x is not o) and (solo or x.name.endswith("_Phone"))
        k3d.bake(o, size, ao_distance=aod, samples=16)
    for x in allm:
        x.hide_render = False
    arm.data.pose_position = 'POSE'


def shot(asset, tag, cam, target, lens=35, res=(1200, 900)):
    """1인칭 확인용 카메라 (눈높이 등)."""
    sc_ = bpy.context.scene
    sc_.render.engine = k3d._engine_eevee()
    sc_.render.resolution_x, sc_.render.resolution_y = res
    sc_.view_settings.view_transform, sc_.view_settings.look = 'Standard', 'None'
    tmp = []
    w = bpy.data.worlds.new("npcb_shot")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.62, 0.66, 0.72, 1)
    bg.inputs['Strength'].default_value = 0.45
    old = sc_.world
    sc_.world = w
    tgt = Vector(target)
    for kind, energy, loc, size in (('SUN', 1.6, (-2, -3, 4), 1), ('AREA', 60, (2.5, -2, 2.2), 2), ('AREA', 80, (-2, 3, 2.5), 2)):
        ld = bpy.data.lights.new("npcb_l", kind)
        ld.energy = energy
        if kind == 'AREA':
            ld.size = size
        lo = bpy.data.objects.new("npcb_l", ld)
        sc_.collection.objects.link(lo)
        lo.location = tgt + Vector(loc)
        lo.rotation_euler = (tgt - lo.location).to_track_quat('-Z', 'Y').to_euler()
        tmp.append(lo)
    bpy.ops.mesh.primitive_plane_add(size=30)
    g = bpy.context.active_object
    g.data.materials.append(k3d.mat("npcb_ground", (0.35, 0.35, 0.36), 0.8))
    tmp.append(g)
    cd = bpy.data.cameras.new("npcb_cam")
    cd.lens = lens
    c = bpy.data.objects.new("npcb_cam", cd)
    sc_.collection.objects.link(c)
    c.location = Vector(cam)
    c.rotation_euler = (tgt - c.location).to_track_quat('-Z', 'Y').to_euler()
    sc_.camera = c
    tmp.append(c)
    p = os.path.join(k3d.SRC, "Previews", f"{asset}_{tag}.png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    sc_.render.filepath = p
    bpy.ops.render.render(write_still=True)
    for o in tmp:
        bpy.data.objects.remove(o, do_unlink=True)
    sc_.world = old
    print("npcb: shot", p)
    return p


def previews(asset, arm, pose_clip="Idle", pose_frame=10, clip_frames=None):
    out = []
    play(arm, pose_clip, pose_frame)
    out += k3d.preview(asset, [arm])
    for clip, fr in (clip_frames or {}).items():
        play(arm, clip, fr)
        out += k3d.preview(asset, [arm], views=((28, 6),), res=(900, 1000), tag=clip)
    return out


def validate(fbx, h):
    """k3d 검증을 새 Blender 로 돌려 문제 목록을 출력한다."""
    env_ = dict(os.environ)
    r = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", "--python", k3d.__file__, "--",
                        "validate", fbx, str(h)], capture_output=True, text=True, env=env_)
    line = next((l for l in r.stdout.splitlines() if l.startswith("K3D_VALIDATE")), "K3D_VALIDATE ?")
    print(line[:3000])
    return line

# 음식 그룹 공통 도구: 인쇄 텍스처 생성, 셰이더 노드 빌더, 메시 생성기, 소켓
import sys, os, math, random, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, bmesh, k3d
from mathutils import Vector, Matrix, noise as mnoise

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("K3D_CACHE") or os.path.abspath(os.path.join(HERE, "..", "..", "..", "_cache"))
TEX = os.path.join(CACHE, "food_tex")


def textures():
    """Pillow 인쇄 텍스처(_tex.py)를 다시 만든다."""
    subprocess.run([k3d.PY, os.path.join(HERE, "_tex.py")],
                   check=True, env=dict(os.environ, K3D_CACHE=CACHE))


def hexc(h, a=1.0):
    """'#rrggbb' -> linear RGBA."""
    h = h.lstrip('#')
    s = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in s) + (a,)


# ---------------------------------------------------------------- 셰이더
class Sh:
    """Principled 하나에 절차 노드를 붙이는 빌더 (bake 가 텍스처로 굽는다)."""

    def __init__(self, name, color="#cccccc", rough=0.5, metal=0.0):
        old = bpy.data.materials.get(name)
        if old:
            bpy.data.materials.remove(old)
        self.m = k3d.mat(name, hexc(color)[:3], rough, metal)
        self.nt = self.m.node_tree
        self.p = k3d.principled(self.m)
        self._tc = None
        self._geo = None

    def n(self, kind, **props):
        nd = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def put(self, sock, v):
        if v is None:
            return
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
        elif isinstance(v, str):
            sock.default_value = hexc(v)
        else:
            sock.default_value = v

    def tc(self, out='Object'):
        if self._tc is None:
            self._tc = self.n('ShaderNodeTexCoord')
        return self._tc.outputs[out]

    def geo(self, out):
        if self._geo is None:
            self._geo = self.n('ShaderNodeNewGeometry')
        return self._geo.outputs[out]

    def sock(self, nd, name, kind=None, out=False):
        for s in (nd.outputs if out else nd.inputs):
            if (s.name == name or s.identifier == name) and (kind is None or s.type == kind) and s.enabled:
                return s
        for s in (nd.outputs if out else nd.inputs):
            if s.name == name or s.identifier == name:
                return s
        raise KeyError(name)

    def noise(self, scale=5.0, detail=4.0, rough=0.5, vec=None, dist=0.0, out='Fac'):
        nd = self.n('ShaderNodeTexNoise')
        self.put(nd.inputs['Vector'], vec or self.tc())
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = dist
        return nd.outputs[out]

    def voronoi(self, scale=5.0, vec=None, feature='F1', out='Distance', rand=1.0):
        nd = self.n('ShaderNodeTexVoronoi', feature=feature)
        self.put(nd.inputs['Vector'], vec or self.tc())
        nd.inputs['Scale'].default_value = scale
        if 'Randomness' in nd.inputs:
            nd.inputs['Randomness'].default_value = rand
        return nd.outputs[out]

    def wave(self, scale=5.0, distortion=4.0, vec=None, wave_type='BANDS', direction='Z', detail=2.0):
        nd = self.n('ShaderNodeTexWave', wave_type=wave_type)
        if wave_type == 'BANDS':
            nd.bands_direction = direction
        self.put(nd.inputs['Vector'], vec or self.tc())
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Distortion'].default_value = distortion
        nd.inputs['Detail'].default_value = detail
        return nd.outputs['Fac']

    def ramp(self, fac, stops, interp='LINEAR'):
        """stops: [(pos, '#hex' 또는 (r,g,b,a) linear), ...] -> Color 소켓."""
        nd = self.n('ShaderNodeValToRGB')
        cr = nd.color_ramp
        cr.interpolation = interp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for e, (pos, col) in zip(cr.elements, stops):
            e.position = pos
            e.color = hexc(col) if isinstance(col, str) else (col if len(col) == 4 else (*col, 1))
        self.put(nd.inputs['Fac'], fac)
        return nd.outputs['Color']

    def mix(self, a, b, fac, blend='MIX', clamp=True):
        nd = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_result=clamp)
        self.put(self.sock(nd, 'Factor', 'VALUE'), fac)
        self.put(self.sock(nd, 'A', 'RGBA'), a)
        self.put(self.sock(nd, 'B', 'RGBA'), b)
        return self.sock(nd, 'Result', 'RGBA', out=True)

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def mr(self, v, a, b, c=0.0, d=1.0, clamp=True):
        """map range: v 의 [a,b] -> [c,d]."""
        nd = self.n('ShaderNodeMapRange', clamp=clamp)
        self.put(nd.inputs['Value'], v)
        nd.inputs['From Min'].default_value, nd.inputs['From Max'].default_value = a, b
        nd.inputs['To Min'].default_value, nd.inputs['To Max'].default_value = c, d
        return nd.outputs['Result']

    def xyz(self, vec=None):
        nd = self.n('ShaderNodeSeparateXYZ')
        self.put(nd.inputs[0], vec or self.tc())
        return nd.outputs

    def comb(self, x=0.0, y=0.0, z=0.0):
        nd = self.n('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.put(nd.inputs[i], v)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        nd = self.n('ShaderNodeVectorMath', operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if scale is not None:
            self.put(self.sock(nd, 'Scale'), scale)
        return nd.outputs['Value'] if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else nd.outputs['Vector']

    def attr(self, name, out='Fac'):
        return self.n('ShaderNodeAttribute', attribute_name=name).outputs[out]

    def ao(self, dist=0.01, inside=False):
        nd = self.n('ShaderNodeAmbientOcclusion', samples=16, inside=inside)
        nd.inputs['Distance'].default_value = dist
        return nd.outputs['AO']

    def image(self, path, vec, ext='REPEAT', non_color=False, out='Color'):
        nd = self.n('ShaderNodeTexImage')
        nd.image = k3d.load_image(path, non_color=non_color)
        nd.extension = ext
        nd.interpolation = 'Cubic'
        self.put(nd.inputs['Vector'], vec)
        return nd.outputs[out]

    def bump(self, height, strength=0.3, dist=0.001, normal=None):
        nd = self.n('ShaderNodeBump')
        self.put(nd.inputs['Height'], height)
        nd.inputs['Strength'].default_value = strength
        nd.inputs['Distance'].default_value = dist
        if normal is not None:
            self.put(nd.inputs['Normal'], normal)
        return nd.outputs['Normal']

    def out(self, base=None, rough=None, normal=None, metal=None, coat=None):
        self.put(self.p.inputs['Base Color'], base)
        self.put(self.p.inputs['Roughness'], rough)
        self.put(self.p.inputs['Normal'], normal)
        self.put(self.p.inputs['Metallic'], metal)
        if coat is not None:
            self.put(self.p.inputs['Coat Weight'], coat)
        return self.m


# ---------------------------------------------------------------- 메시
def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    return o


def lathe(name, prof, segs=48, rfn=None, zfn=None):
    """prof=[(r,z),...] 를 Z 축으로 회전. r==0 은 극점. rfn(a,i,r,z)->r 배율, zfn(a,i,r,z)->z 오프셋."""
    bm = bmesh.new()
    rings = []
    for i, (r, z) in enumerate(prof):
        if r <= 1e-6:
            zz = z + (zfn(0.0, i, 0.0, z) if zfn else 0.0)
            rings.append([bm.verts.new((0, 0, zz))])
            continue
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            rr = r * (rfn(a, i, r, z) if rfn else 1.0)
            zz = z + (zfn(a, i, r, z) if zfn else 0.0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        if len(A) == 1:
            for k in range(segs):
                bm.faces.new((A[0], B[k], B[(k + 1) % segs]))
        elif len(B) == 1:
            for k in range(segs):
                bm.faces.new((A[k], A[(k + 1) % segs], B[0]))
        else:
            for k in range(segs):
                bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


def smooth(o, angle=40):
    k3d.smooth(o, angle)
    return o


def bevel(o, width, segs=2, angle=30, wn=True):
    m = o.modifiers.new("Bevel", 'BEVEL')
    m.width, m.segments, m.limit_method = width, segs, 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.use_clamp_overlap = True
    if wn:
        w = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
        w.keep_sharp = True
    return o


def solidify(o, t, offset=-1.0, mat_off=0, rim_off=0):
    m = o.modifiers.new("Solid", 'SOLIDIFY')
    m.thickness, m.offset = t, offset
    m.material_offset, m.material_offset_rim = mat_off, rim_off
    m.use_even_offset = True
    return o


def mats(o, *ms):
    for m in ms:
        o.data.materials.append(m)
    return o


def set_mat_by(o, fn):
    """fn(face_center, normal) -> 머티리얼 슬롯 번호."""
    for p in o.data.polygons:
        p.material_index = fn(p.center, p.normal)


def vattr(o, name, fn, domain='POINT'):
    """정점별 float 속성 (셰이더 Attribute 노드로 읽음). fn(co) -> float."""
    me = o.data
    a = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', domain)
    if domain == 'POINT':
        for v in me.vertices:
            a.data[v.index].value = fn(v.co)
    else:
        for p in me.polygons:
            a.data[p.index].value = fn(p.center)
    return o


def const_attr(o, name, val):
    me = o.data
    a = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', 'POINT')
    for d in a.data:
        d.value = val


def nz(x, y=0.0, z=0.0):
    return mnoise.noise(Vector((x, y, z)))


def join(objs, name):
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    return k3d.join(objs, name)


def socket(parent, asset, purpose, loc, rot=(0, 0, 0), size=0.02):
    e = bpy.data.objects.new(f"{asset}_Socket_{purpose}", None)
    e.empty_display_type, e.empty_display_size = 'ARROWS', size
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    e.location, e.rotation_euler = loc, rot
    return e

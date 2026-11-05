# 돋보기 (손잡이형 독서용 확대경) — 황동 테 + 양볼록 유리 렌즈 + 고정 블록/나사 + 황동 페룰 + 호두나무 손잡이
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Items')
import _ik as ik, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "Magnifier"
MM = 0.001
ZC = 0.210            # 렌즈 중심 높이 (원점 = 손잡이 끝 바닥)
R_IN, R_OUT = 48.0, 56.25   # 테 안/바깥 반지름 (mm), 보이는 렌즈 지름 96mm
R_GLASS = 49.6        # 유리 반지름 (테 홈 속으로 1.6mm 숨음)


def outward(o):
    """닫힌 회전체 노멀을 바깥으로."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return o


def lathe_y(name, prof_mm, mat, n, z=ZC):
    """Z축 회전체를 만든 뒤 +Z -> -Y(정면) 로 눕혀 렌즈 축을 Y 로."""
    o = outward(ik.lathe(name, [(r * MM, h * MM) for r, h in prof_mm], n=n, mat=mat))
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.location = (0, 0, z)
    k3d.select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def lathe_z(name, prof_mm, mat, n):
    return outward(ik.lathe(name, [(r * MM, h * MM) for r, h in prof_mm], n=n, mat=mat))


# ---------------------------------------------------------------- 머티리얼
def tarnish(g, base, rough, obj):
    # 큰 얼룩 변색 (손 안 닿는 곳이 갈색으로 산화)
    blot = g.ramp(g.noise(9, 4, 0.6, obj, dist=0.8), 0.42, 0.7)
    base = g.mix(g.math('MULTIPLY', blot, 0.8), base, ik.srgb("#4e3d26"))
    rough = g.lerp(g.math('MULTIPLY', blot, 0.6), rough, 0.5)
    # 가는 헤어라인 스크래치
    sc = g.ramp(g.wave(260, g.coord('Object'), 'Z', 14, 2), 0.86, 0.98)
    rough = g.lerp(g.math('MULTIPLY', sc, 0.5), rough, 0.12)
    return base, rough


brass = ik.P("M_tmp_brass", "#a8875a", rough=0.27, metal=1.0, var=0.08, vs=14, rv=0.06,
             grime=1.0, gd=0.005, gcol="#231b0f", edge=0.8, ed=0.0012, ecol="#e6c389", erough=0.14,
             smudge=0.22, bump=0.04, bs=1400, bd=0.00006, extra=tarnish)


def woodgrain(g, base, rough, obj):
    mp = g.n('ShaderNodeMapping')
    g.link(g.coord('Object'), mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (1.0, 1.0, 0.07)   # 결은 손잡이 축(Z) 방향으로 길게
    grain = g.wave(60, mp.outputs[0], 'X', 14, 5)
    pores = g.ramp(g.noise(900, 2, 0.5, mp.outputs[0]), 0.62, 0.8)
    dark = g.math('ADD', g.math('MULTIPLY', g.ramp(grain, 0.35, 0.95), 0.6), g.math('MULTIPLY', pores, 0.4))
    base = g.mix(g.math('MULTIPLY', dark, 0.5), base, ik.srgb("#1c110a"))
    # 손이 쥐는 곳 (z 0.03~0.10): 바니시가 벗겨져 맨나무(밝고 거침, 결은 남음)
    xyz = g.sep(g.coord('Object'))
    z = xyz[2]
    grip = g.math('MULTIPLY', g.ramp(z, 0.026, 0.045), g.math('SUBTRACT', 1.0, g.ramp(z, 0.092, 0.11)))
    wear = g.math('MULTIPLY', grip, g.ramp(g.noise(24, 4, 0.6, obj), 0.3, 0.6))
    # 엄지(앞 -Y)·검지(뒤 +Y) 닿는 자리는 더 많이 닳음
    side = g.ramp(g.math('ABSOLUTE', xyz[1]), 0.004, 0.0095)
    wear = g.math('ADD', wear, g.math('MULTIPLY', g.math('MULTIPLY', grip, side), 0.55), clamp=True)
    bare = g.mix(g.math('MULTIPLY', dark, 0.6), ik.srgb("#9a7754"), ik.srgb("#5c3f29"))
    base = g.mix(g.math('MULTIPLY', wear, 0.85), base, bare)
    rough = g.lerp(wear, rough, 0.72)
    return base, rough


wood = ik.P("M_tmp_wood", "#4a3222", rough=0.36, metal=0.0, var=0.18, vs=8, rv=0.05,
            grime=0.6, gd=0.004, gcol="#120a05", edge=0.35, ed=0.0015, ecol="#7a5a3e",
            smudge=0.18, bump=0.08, bs=500, bd=0.00012, extra=woodgrain)

# ---------------------------------------------------------------- 테 (림)
front = [(48.0, 0.0), (48.0, 2.0), (48.3, 2.7), (49.1, 3.05), (50.6, 3.15), (51.3, 3.55), (52.3, 3.8),
         (53.3, 3.55), (53.9, 3.2), (54.35, 3.1), (54.6, 2.85), (54.95, 3.0), (55.6, 2.7), (56.0, 2.0),
         (56.2, 1.0), (56.25, 0.0)]
prof = front + [(r, -h) for r, h in reversed(front[:-1])]
rim = lathe_y(A + "_Rim", prof, brass, 128)
rim.data.polygons.foreach_set("use_smooth", [True] * len(rim.data.polygons))

# 고정 블록 (테 아래를 감싸는 클램프) + 일자 나사 (양쪽)
zb = ZC - 54.0 * MM
block = ik.box(A + "_Block", (15.5 * MM, 9.6 * MM, 8.5 * MM), loc=(0, 0, zb), mat=brass, bev=0.0009, seg=3)


def half_dome(name, y_face, sgn, keep_pos):
    """나사 머리 반쪽 (가운데 홈 0.45mm)."""
    bm = bmesh.new()
    prof_s = [(1.75, 0.0), (1.7, 0.25), (1.5, 0.5), (1.05, 0.72), (0.0, 0.82)]
    n = 24
    rings = []
    for i in range(n):
        th = 2 * math.pi * i / n
        rings.append([bm.verts.new((r * math.cos(th) * MM, sgn * h * MM, r * math.sin(th) * MM)) for r, h in prof_s])
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(len(prof_s) - 1):
            bm.faces.new((a[k], b[k], b[k + 1], a[k + 1]) if sgn > 0 else (a[k + 1], b[k + 1], b[k], a[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    g = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0.225 * MM if keep_pos else -0.225 * MM, 0, 0),
                           plane_no=(1, 0, 0), clear_inner=keep_pos, clear_outer=not keep_pos)
    bnd = [e for e in bm.edges if e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = ik.mesh_obj(name, bm, brass)
    o.location = (0, y_face, zb + 0.6 * MM)
    o.rotation_euler = (0, math.radians(18 if y_face < 0 else -24), 0)  # 홈 방향이 살짝 비스듬
    for p in o.data.polygons:
        p.use_smooth = True
    o.data.set_sharp_from_angle(angle=math.radians(40))
    return o


screws = []
for y_face, sgn in ((-4.8 * MM, -1), (4.8 * MM, 1)):
    for kp in (True, False):
        screws.append(half_dome(A + "_Screw", y_face, sgn, kp))

# 목 + 장식 링 + 페룰 (황동, 세로 회전체)
z0 = (zb - 4.25 * MM) / MM   # 블록 아래면 (mm)
neck = [(0.0, z0 + 1.0), (4.2, z0 + 1.0), (4.2, z0), (4.7, z0 - 0.9), (4.3, z0 - 2.0), (3.6, z0 - 3.6),
        (3.55, z0 - 6.6), (4.4, z0 - 7.6), (6.3, z0 - 8.6), (7.9, z0 - 9.4), (8.9, z0 - 10.4), (9.45, z0 - 11.4),
        (9.5, z0 - 12.6), (9.05, z0 - 13.1), (9.05, z0 - 13.7), (9.55, z0 - 14.2), (9.6, z0 - 23.6),
        (9.15, z0 - 24.1), (9.15, z0 - 24.6), (9.65, z0 - 25.1), (9.7, z0 - 26.8), (9.35, z0 - 27.4),
        (8.95, z0 - 27.6), (0.0, z0 - 27.6)]
stem = lathe_z(A + "_Stem", neck, brass, 56)
stem.data.set_sharp_from_angle(angle=math.radians(50))

# 나무 손잡이 (볼록-허리-볼록, 장식 홈 2줄)
zt = z0 - 27.3
wp = [(0.0, zt), (8.95, zt), (9.15, zt - 2.5), (8.7, zt - 3.1), (9.25, zt - 3.7), (9.4, zt - 6.0), (9.0, zt - 6.6),
      (9.5, zt - 7.2), (10.1, zt - 14), (10.6, zt - 26), (10.4, zt - 36), (9.9, zt - 46), (9.8, zt - 56),
      (10.3, zt - 68), (11.0, zt - 82), (11.25, zt - 94), (11.0, zt - 104), (10.3, zt - 110.5), (9.4, zt - 114.0),
      (9.0, 7.6), (0.0, 7.6)]
wood_o = lathe_z(A + "_Wood", wp, wood, 56)
wood_o.data.set_sharp_from_angle(angle=math.radians(50))

# 끝 마개 (황동 돔)
cap = lathe_z(A + "_Cap", [(0.0, 0.0), (3.0, 0.08), (5.6, 0.45), (7.6, 1.25), (8.8, 2.4), (9.35, 3.6),
                            (9.4, 6.8), (9.05, 7.4), (9.0, 8.4), (0.0, 8.4)], brass, 56)
cap.data.set_sharp_from_angle(angle=math.radians(50))

for o in [rim, stem, wood_o, cap] + screws:
    w = o.modifiers.new("WN", 'WEIGHTED_NORMAL')
    w.keep_sharp = True

body = ik.join([rim, block, stem, wood_o, cap] + screws, A + "_Body")
k3d.bake(body, 2048, ao_distance=0.006, samples=24)

# ---------------------------------------------------------------- 렌즈 (양볼록, UV 0..1 원판)
lens_m = bpy.data.materials.new("M_Glass_Magnifier_Lens")
lens_m.use_nodes = True
nt = lens_m.node_tree
p = k3d.principled(lens_m)
p.inputs['Roughness'].default_value = 0.04
p.inputs['IOR'].default_value = 1.52
p.inputs['Alpha'].default_value = 1.0
tn = k3d.image_node(lens_m, k3d.load_image(ik.tex("lens", "lens_smudge.png")), p.inputs['Base Color'])
nt.links.new(tn.outputs['Alpha'], p.inputs['Alpha'])
k3d.flag(lens_m, transparent=True)
try:
    lens_m.surface_render_method = 'BLENDED'
except Exception:
    pass
lens_m.use_backface_culling = False

edge_t, sag = 1.0, 1.7
cap_pts = [(R_GLASS * t, edge_t + sag * (1 - t * t)) for t in [i / 16 for i in range(17)]]
lprof = [(r, -h) for r, h in cap_pts] + [(R_GLASS + 0.15, 0.0)] + cap_pts[::-1]   # 뒤 극 -> 가장자리 -> 앞 극
lens = lathe_y(A + "_Lens", lprof, lens_m, 96)
lens.data.polygons.foreach_set("use_smooth", [True] * len(lens.data.polygons))
me = lens.data
uvl = me.uv_layers[0]
for poly in me.polygons:
    for li in poly.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        uvl.data[li].uv = (0.5 + v.x / (2 * R_IN * MM), 0.5 + (v.z - ZC) / (2 * R_IN * MM))
k3d.set_origin(lens, Vector((0, 0, ZC)))
ik.parent_keep(lens, body)

# ---------------------------------------------------------------- 소켓
ik.socket(A + "_Socket_Grip", (0, 0, 0.062), body)
ik.socket(A + "_Socket_LensCenter", (0, 0, ZC), body)

notes = ("돋보기 0.112x0.0076x0.267m (렌즈 보이는 지름 96mm, 테 바깥 112.5mm), 원점 = 손잡이 끝 바닥 중앙, 정면(-Y)=렌즈면. "
         "Magnifier_Body(황동 테·클램프 블록·일자나사·페룰·호두나무 손잡이·마개, 2048 bake) 루트, "
         "자식 Magnifier_Lens: 원점 = 렌즈 중심(0,0,0.210), M_Glass_Magnifier_Lens(투명, BaseMap 알파 = 지문/얼룩), "
         "UV 0..1 = 보이는 원판(반지름 48mm)을 정면에서 본 평면 투영 (U 오른쪽 +X, V 위 +Z; 뒷면은 좌우 반전으로 같은 UV), "
         "테 속에 숨은 유리 가장자리는 UV 0..1 밖(최대 1.017). 줌 렌더 텍스처를 렌즈에 바로 매핑 가능. "
         "Socket_Grip = 손잡이 쥐는 점(z 0.062, 축 +Z = 손잡이 방향), Socket_LensCenter = 렌즈 중심(정면 -Y). "
         "프로토타입: lensRadius 0.05, 손잡이 길이 0.16, 손에 쥐고 화면 중앙 0.34m 앞. "
         "Unity: Magnifier_Lens 렌더러는 Cast Shadows = Off 로 둘 것 (투명 Lit 은 꽉 찬 원판 그림자를 만듦).")
k3d.export(A, ik.CAT, [body], notes=notes)
# 세로로 긴 물건이라 세로 해상도로 찍어 테 전체가 들어오게
k3d.preview(A, [body], res=(900, 1200))
k3d.preview(A, [body], views=((90, 10),), res=(900, 1200), tag='side')
k3d.preview(A, [body], views=((0, 8),), lens=35, res=(900, 1200), tag='fp')
k3d.preview(A, [body], views=((20, 10),), lens=90, tag='rim')
L = (('SUN', (0, 0, 3), 3.0, (1, 0.97, 0.92), 0.5), ('POINT', (-0.25, -0.3, 0.35), 12.0, (0.8, 0.85, 1.0), 0.2))
ik.shot(ik.PREV + "/Magnifier_grip_0.png", (0.09, -0.2, 0.12), (0, 0, 0.075), lens=50, res=(900, 1200), lights=L, world=0.6)

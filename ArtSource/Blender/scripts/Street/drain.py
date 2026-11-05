# StreetManhole: 주철 하수 맨홀(뚜껑 Ø0.644 m, 테 Ø0.80 m, 양각 '하수'·격자·둘레 글자, 보수 아스팔트 고리)
# StreetDrain: 빗물받이 강철 격자 뚜껑 0.64 x 0.34 m (격자 사이 어두운 구덩이, 담배꽁초).
# 실행: blender -b --factory-startup --python drain.py [-- StreetManhole StreetDrain]
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _street as S
import k3d, bpy, bmesh
from mathutils import Vector

R_COVER = 0.322


def orient(o, want):
    """열린 회전체 면 방향 맞춤: want(면 중심) = 바라야 할 방향."""
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        if f.normal.dot(want(f.calc_center_median())) < 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    return o


UP = lambda c: Vector((0, 0, 1))
OUT = lambda c: Vector((c.x, c.y, 0))


def cover_mat():
    """높이맵 하나로 범프 + 마스크: 솟은 곳은 바퀴·발에 닳아 반짝, 파인 곳은 흙때·녹."""
    S.ensure_ground_tex()
    m = bpy.data.materials.new("M_StreetManhole_Cover")
    k3d._nodes(m)
    nb = S.NB(m)
    p = k3d.principled(m)
    uvn = nb.n('ShaderNodeUVMap', uv_map="UVMap")
    t = nb.n('ShaderNodeTexImage')
    t.image = k3d.load_image(os.path.join(S.TEX, "manhole_height.png"), non_color=True)
    nb.ln(uvn.outputs['UV'], t.inputs['Vector'])
    H = t.outputs['Color']
    bw = nb.n('ShaderNodeRGBToBW')
    nb.ln(H, bw.inputs['Color'])
    h = bw.outputs[0]
    obj = nb.n('ShaderNodeTexCoord').outputs['Object']
    raised = nb.mr(h, 0.55, 0.85)
    recess = nb.mr(h, 0.42, 0.15)
    n1 = nb.noise(obj, 18, 6, 0.6)
    n2 = nb.noise(obj, 7, 10, 0.7, 0.3)
    wear = nb.math('MULTIPLY', raised, nb.mr(n1, 0.25, 0.6, 0.55, 1.0), clamp=True)
    col = nb.mixc(nb.mr(n1, 0.3, 0.7), (0.040, 0.038, 0.035), (0.060, 0.056, 0.050))
    rust = nb.math('MULTIPLY', nb.mr(n2, 0.5, 0.62), nb.math('ADD', recess, 0.35), clamp=True)
    col = nb.mixc(rust, col, (0.13, 0.055, 0.022))
    col = nb.mixc(nb.math('MULTIPLY', recess, 0.85), col, (0.028, 0.024, 0.018))
    col = nb.mixc(wear, col, (0.30, 0.29, 0.27))
    nb.ln(col, p.inputs['Base Color'])
    met = nb.mixf(wear, nb.mixf(nb.math('MAXIMUM', rust, recess), 0.55, 0.0), 0.92)
    nb.ln(met, p.inputs['Metallic'])
    rgh = nb.mixf(wear, nb.mixf(nb.math('MAXIMUM', rust, recess), 0.68, 0.95), 0.30)
    nb.ln(rgh, p.inputs['Roughness'])
    b = nb.n('ShaderNodeBump')
    b.inputs['Strength'].default_value = 1.0
    b.inputs['Distance'].default_value = 0.004
    fine = nb.noise(obj, 260, 6, 0.6)
    nb.ln(nb.math('ADD', h, nb.math('MULTIPLY', fine, 0.03)), b.inputs['Height'])
    nb.ln(b.outputs['Normal'], p.inputs['Normal'])
    return m


def build_manhole():
    A = "StreetManhole"
    k3d.reset()
    frame_m = S.wmat("M_StreetManhole_Frame", (0.055, 0.052, 0.048), 0.55, 0.6, rust=0.22, rust_scale=14,
                     edge=0.9, edge_col=(0.30, 0.29, 0.27), edge_metal=1.0, edge_rough=0.3, grime=0.7,
                     scratches=0.6, bump=0.15, bump_scale=200)
    frame = S.lathe(A + "_Frame", [(0.326, -0.035), (0.326, 0.003), (0.329, 0.006), (0.386, 0.006),
                                    (0.396, 0.003), (0.401, -0.002), (0.401, -0.035), (0.326, -0.035)], seg=64, mat=frame_m,
                    smooth_ang=35)
    cmat = cover_mat()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ret = bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=True, segments=72, radius=R_COVER - 0.0015)
    for v in bm.verts:
        v.co.z = 0.0055
    for f in bm.faces:
        for l in f.loops:
            l[uv].uv = (0.5 + l.vert.co.x / (2 * R_COVER), 0.5 + l.vert.co.y / (2 * R_COVER))
    top = S.from_bm(A + "_CoverTop", bm, cmat)
    side = S.lathe(A + "_CoverSide", [(R_COVER - 0.0015, 0.0055), (R_COVER, 0.004), (R_COVER, -0.02)], seg=72,
                   mat=cmat, close=False, smooth_ang=60)
    orient(side, OUT)
    for d in side.data.uv_layers[0].data:
        d.uv = (0.02, 0.5)   # 테두리 바깥 링(솟은 면) 색
    body = S.join([frame, top, side], A + "_Body")
    k3d.bake(body, 1024, samples=24, ao_distance=0.03)
    # 둘레 보수 아스팔트 고리 + 타르 실링 (굽지 않는 M_Tile)
    collar = S.lathe(A + "_Collar", [(0.40, 0.0012), (0.60, 0.0012)], seg=64, mat=S.tile_patch(), close=False)
    k3d.uv_world(collar, S.TILE_PATCH)
    seal = S.lathe(A + "_Seal", [(0.597, 0.002), (0.625, 0.002)], seg=64,
                   mat=k3d.mat("M_StreetManhole_Tar", (0.016, 0.016, 0.017), 0.55), close=False)
    orient(collar, UP)
    orient(seal, UP)
    collar = S.join([collar, seal], A + "_Collar")
    for p_ in collar.data.polygons:
        p_.use_smooth = False
    S.parent(collar, body)
    notes = ("하수 맨홀. 원점 = 노면 위 중앙(z=0 = 놓일 바닥면), 뚜껑 윗면 +5.5 mm. 뚜껑 Ø0.644 m(양각 '하수'·'은행골구'·격자 미끄럼 방지·"
             "둘레 글자, 들어올림 홈 2개), 주철 테 Ø0.80 m. 자식 StreetManhole_Collar = 둘레 보수 아스팔트 고리(Ø1.25 m, "
             "M_Tile_Street_AsphaltPatch, +1.2 mm) + 타르 실링 — 보도/골목 바닥에 놓을 때는 끈다. "
             "min_z -0.035 = 노면 속에 묻히는 테 아래쪽(의도). 프로토타입 위치: 골목 (0.7, -6.2), (-1, -24.4), 큰길 (8, -37.6).")
    return [body], notes


def build_drain():
    A = "StreetDrain"
    k3d.reset()
    LX, LY, FW, TOP = 0.64, 0.34, 0.025, 0.009
    steel = S.galv("M_StreetDrain_Steel", 0.55, base=(0.30, 0.295, 0.28), rust=0.75, rust_scale=11, grime=0.85,
                   grime_dist=0.02, edge=0.6, edge_col=(0.45, 0.45, 0.44), scratches=0.5, streaks=0.0)
    parts = []
    # 테 (앵글)
    for i, (sx, sy, cx, cy) in enumerate(((LX, FW, 0, -(LY - FW) / 2), (LX, FW, 0, (LY - FW) / 2),
                                          (FW, LY - 2 * FW, -(LX - FW) / 2, 0), (FW, LY - 2 * FW, (LX - FW) / 2, 0))):
        parts.append(S.box(f"{A}_F{i}", (sx, sy, TOP), (cx, cy, TOP / 2), mat=steel, bevel=0.0018))
    # 받침 철근 (Y 방향 평강, 30 mm 간격) + 가로 연결봉 3줄
    inner_x = LX - 2 * FW
    n = int(inner_x / 0.03)
    for i in range(n):
        x = -inner_x / 2 + (i + 0.5) * inner_x / n
        parts.append(S.box(f"{A}_B{i}", (0.006, LY - 2 * FW + 0.004, TOP - 0.0015), (x, 0, 0.0015 + (TOP - 0.0015) / 2),
                           mat=steel, bevel=0.0012))
    for j, y in enumerate((-0.075, 0.0, 0.075)):
        parts.append(S.box(f"{A}_R{j}", (inner_x + 0.004, 0.005, 0.005), (0, y, TOP - 0.0028), mat=steel,
                           bevel=0.0012))
    # 구덩이 바닥 (젖은 흙·낙엽 부스러기, 아주 어둡게)
    pit_m = S.wmat("M_StreetDrain_Pit", (0.012, 0.011, 0.010), 0.45, 0.0, var=0.5, vscale=14, grime=0.0,
                   rust=0.6, rust_scale=16, bump=0.3, bump_scale=60)
    pit = S.box(A + "_Pit", (inner_x + 0.004, LY - 2 * FW + 0.004, 0.0008), (0, 0, 0.0004), mat=pit_m, bevel=0.0)
    parts.append(pit)
    # 담배꽁초 3개 (필터 + 종이)
    rng = random.Random(5)
    filt = S.wmat("M_StreetDrain_Filter", (0.55, 0.30, 0.10), 0.7, 0.0, var=0.3, grime=0.3, bump=0.2)
    paper = S.wmat("M_StreetDrain_Paper", (0.62, 0.60, 0.55), 0.75, 0.0, var=0.2, grime=0.5, bottom=1.0,
                   bottom_h=0.012, bottom_col=(0.2, 0.17, 0.12), bump=0.1)
    for k, (x, y, a) in enumerate(((-0.12, 0.05, 0.4), (0.07, -0.09, 1.9), (0.18, 0.06, -0.7))):
        z = TOP + 0.0036
        parts.append(S.cyl(f"{A}_CF{k}", 0.0038, 0.012, (x, y, z), (math.pi / 2, 0, a), mat=filt, seg=10,
                           bevel=0.0006))
        dx, dy = -math.sin(a) * 0.012, math.cos(a) * 0.012
        parts.append(S.cyl(f"{A}_CP{k}", 0.0036, rng.uniform(0.008, 0.016), (x + dx, y + dy, z),
                           (math.pi / 2, 0, a), mat=paper, seg=10, bevel=0.0006))
    body = S.join(parts, A + "_Body")
    k3d.origin_bottom(body)
    k3d.bake(body, 1024, samples=24, ao_distance=0.02)
    notes = ("빗물받이 강철 격자 뚜껑 0.64(X) x 0.34(Y) m, 높이 9 mm. 원점 = 바닥 중앙(놓일 면 z=0). 평강 30 mm 간격(Y 방향) + "
             "연결봉 3줄, 격자 사이로 보이는 어두운 구덩이 판이 뚜껑 안에 포함(아래 바닥이 비치지 않음). 담배꽁초 3개. "
             "StreetRoadAlley_Socket_Drain 에 회전 없이, 큰길은 경계석 앞(노면) 에 긴 변을 경계석과 나란히.")
    return [body], notes


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for A in argv or ["StreetManhole", "StreetDrain"]:
        roots, notes = build_manhole() if A == "StreetManhole" else build_drain()
        S.finish(A, roots, None, notes, views=((20, 50), (200, 30)),
                 extra=[dict(dist=1.3, eye=1.55, look_h=0.0, az=-25, lens=35)])

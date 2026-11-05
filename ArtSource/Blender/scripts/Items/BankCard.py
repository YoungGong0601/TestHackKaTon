# 시장은행 체크카드 (ISO ID-1 85.60x53.98x0.76mm, 모서리 R3.18) — 앞/뒤 고해상도 인쇄면 + IC칩 인레이 + 흰 코어 옆면
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Items')
import _ik as ik, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "BankCard"
MM = 0.001
W, H, T, R = 85.60 * MM, 53.98 * MM, 0.76 * MM, 3.18 * MM


def rrect(w, h, r, seg=8):
    """둥근 사각형 외곽 (XZ, 중심 0, 반시계)."""
    pts = []
    for cx, cz, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def slab(name, w, h, r, y0, y1, mats, uv_front=None, uv_back=None, zoff=0.0, xoff=0.0):
    """y0(앞) ~ y1(뒤) 두께의 둥근 판. mats=(앞, 뒤, 옆) 슬롯 인덱스, uv_*(x,z)->(u,v)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    out = rrect(w, h, r)
    fv = [bm.verts.new((xoff + x, y0, zoff + z)) for x, z in out]
    bv = [bm.verts.new((xoff + x, y1, zoff + z)) for x, z in out]
    ff = bm.faces.new(fv[::-1])          # 앞면 노멀 -Y
    bf = bm.faces.new(bv)
    ff.material_index, bf.material_index = mats[0], mats[1]
    n = len(out)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((fv[i], fv[j], bv[j], bv[i]))
        f.material_index = mats[2]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f, fn in ((ff, uv_front), (bf, uv_back)):
        if fn:
            for l in f.loops:
                l[uvl].uv = fn(l.vert.co.x - xoff, l.vert.co.z - zoff)
    return bm


def face_mat(name, side):
    """인쇄면 (굽지 않음): BaseColor + Normal + MS(스무스니스 마모).
    unity_baked 표시 → k3d JSON 이 이미지 이름 끝(_BaseColor/_Normal/_MS)으로 맵 3장을 모두 내보냄 (MS 있으면 금속·스무스 1.0 배율)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = k3d.principled(m)
    pf = f"T_{A}_card_{side}_"
    k3d.image_node(m, k3d.load_image(ik.tex("card", f"card_{side}.png"), pf + "BaseColor"), p.inputs['Base Color'])
    tn = k3d.image_node(m, k3d.load_image(ik.tex("card", f"card_{side}_Normal.png"), pf + "Normal", True), None, non_color=True)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    mn = k3d.image_node(m, k3d.load_image(ik.tex("card", f"card_{side}_MS.png"), pf + "MS", True), None, non_color=True)
    inv = nt.nodes.new('ShaderNodeMath')   # Blender 미리보기: roughness = 1 - MS.a (k3d bake 와 같은 연결)
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(mn.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], p.inputs['Roughness'])
    m["unity_baked"] = 1
    return m


front_m = face_mat("M_BankCard_Front", "front")
back_m = face_mat("M_BankCard_Back", "back")


def core(g, base, rough, obj):
    # 옆면: 흰 PVC 코어 + 앞뒤 얇은 녹색 인쇄층, 지갑 속 때
    y = g.math('ABSOLUTE', g.sep(g.coord('Object'))[1])
    lay = g.ramp(y, 0.00027, 0.00033)
    base = g.mix(lay, base, ik.srgb("#4d6358"))
    return base, rough


edge_m = ik.P("M_tmp_card_edge", "#e9e6dc", rough=0.5, var=0.06, vs=400, grime=0.4, gd=0.0006, gcol="#7d776a",
              extra=core, bump=0.05, bs=3000, bd=0.00002)
chip_m = ik.P("M_tmp_chip", (1, 1, 1), rough=0.24, metal=1.0, var=0.04, vs=600, img=ik.tex("chip", "chip.png"),
              imode='base', smudge=0.35, bump=0.05, bs=4000, bd=0.00001)

# 카드 본체: 앞 UV 0..1 그대로, 뒤 UV 좌우 반전 (뒤에서 볼 때 바로 읽힘)
bm = slab(A, W, H, R, -T / 2, T / 2, (0, 1, 2),
          uv_front=lambda x, z: (x / W + 0.5, z / H + 0.5),
          uv_back=lambda x, z: (0.5 - x / W, z / H + 0.5), zoff=H / 2)
card = ik.mesh_obj(A + "_Body", bm)
for m in (front_m, back_m, edge_m):
    card.data.materials.append(m)
bv = card.modifiers.new("Bevel", 'BEVEL')
bv.width, bv.segments, bv.limit_method = 0.14 * MM, 2, 'ANGLE'
bv.angle_limit = math.radians(40)
bv.harden_normals = False
card.modifiers.new("WN", 'WEIGHTED_NORMAL').keep_sharp = True
for p in card.data.polygons:
    p.use_smooth = True

# IC 칩 (인쇄 홈 위치와 같게: 왼쪽 9.6mm, 위 19.2mm, 11.6x9.4mm), 0.05mm 솟음
cw, chh = 11.6 * MM, 9.4 * MM
cx = -W / 2 + 9.6 * MM + cw / 2
cz = H - 19.2 * MM - chh / 2
bmc = slab(A + "_Chip", cw, chh, 1.1 * MM, -T / 2 - 0.05 * MM, -T / 2 + 0.2 * MM, (0, 0, 0),
           uv_front=lambda x, z: (x / cw + 0.5, z / chh + 0.5), zoff=cz, xoff=cx)
chip = ik.mesh_obj(A + "_Chip", bmc, chip_m)
cb = chip.modifiers.new("Bevel", 'BEVEL')
cb.width, cb.segments, cb.limit_method = 0.04 * MM, 2, 'ANGLE'
chip.modifiers.new("WN", 'WEIGHTED_NORMAL').keep_sharp = True
for p in chip.data.polygons:
    p.use_smooth = True

body = ik.join([card, chip], A + "_Body")
k3d.bake(body, 512, keep=("M_BankCard_Front", "M_BankCard_Back"), ao_distance=0.0015, samples=24)

ik.socket(A + "_Socket_Grip", (0.026, 0, 0.009), body)
ik.socket(A + "_Socket_InsertTip", (-W / 2, 0, cz), body)

notes = ("시장은행 체크카드 0.0856x0.00076x0.054m (ISO ID-1), 원점 = 아래 긴 변 중앙(세워 둔 상태), 정면(-Y)=앞면(칩·엠보 번호 9420 1183 5507 2841). "
         "M_BankCard_Front / M_BankCard_Back: 2048x1292 인쇄면 (BaseColor + _Normal(엠보·뒷면 눌린 자국) + _MS(스무스니스 0.3~0.85: "
         "잔기스·지문·모서리 쓸림·자기띠 긁힘·서명란 무광·은박/홀로그램 광택), 굽지 않음), UV 0..1 = 면 전체 "
         "(앞: U 오른쪽 V 위, 뒤: 뒤에서 볼 때 U 오른쪽). 옆면+IC칩은 M_BankCard_Body (512 bake). "
         "Socket_Grip = 엄지·검지로 집는 점(프로토타입 holdCard at), Socket_InsertTip = 칩 쪽 짧은 변 중앙 (IC 단말기에 -X 방향으로 꽂음, 칩 면 위). "
         "키오스크 화면 문구 '시장은행 **** 2841' 과 끝번호 일치.")
k3d.export(A, ik.CAT, [body], notes=notes)
k3d.preview(A, [body])
k3d.preview(A, [body], views=((0, 0),), lens=80, tag='front')
k3d.preview(A, [body], views=((180, 0),), lens=80, tag='back')

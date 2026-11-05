"""PH_Door_Glass__Leaf, PH_Storefront (+ 규격 밖 선택 PH_StorefrontUpper). 모두 turn(180): Unity x = 원본 x, 앞 -Z.

간판 띠는 원본 M_StorefrontFacade_Sign 을 쓰지 않고 새로 굽는다: 그 아틀라스의 AO·색에 버거대왕 글자 자국이 박혀 있어서
글자 메시만 지우면 친구 Sign 뒤에 유령 글자가 남는다.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "Storefront")]
import bpy, bmesh
from mathutils import Matrix, Vector
import ph, sf
from sf import k3d, box2, cyl

A = "StorefrontFacade"
LEAF = "PH_Door_Glass__Leaf"
X0, X1 = -6.035, 5.535           # 친구 범위 = 양 끝 멀리언 바깥 면
# 문짝 제작 좌표(문틀 면 x=0, 문 두께 중심 z=0)로 되돌린다. 프로토타입 pivot·회색 문과 같은 자리라 닫힌 문이 유리선에
# 맞고 Sticker_Pull(z -0.03) 이 문틀 면 5mm 앞에 온다. 원본 원점(너클 축)을 쓰면 문이 2.6cm 안으로 밀려 멈춤대를 뚫는다.
LEAF_M = ph.turn(180) @ Matrix.Translation((sf.DOOR_AX, sf.DOOR_AY, 0))


def only(objs):
    """베이크(AO)와 렌더에 objs 메시만 보이게 하고, 렌더도 Unity 처럼 단면 머티리얼의 뒷면을 그리지 않는다."""
    for o in bpy.data.objects:
        o.hide_render = o.type == 'MESH' and o not in objs
    for m in bpy.data.materials:
        m.use_backface_culling = "unity_double_sided" not in m


def crop(src, name, keep):
    """src 의 연결 덩어리 중 keep(최소점, 최대점) 이 참인 것만 남긴 복사본."""
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, drop = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        seen.add(v)
        isl = [v]
        for a in isl:  # 도는 동안 늘어난다
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b)
                    isl.append(b)
        lo = Vector([min(u.co[i] for u in isl) for i in range(3)])
        hi = Vector([max(u.co[i] for u in isl) for i in range(3)])
        if not keep(lo, hi):
            drop += isl
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    return o


def clean(o):
    """잘라내고 남은 빈 머티리얼 슬롯을 지운다 (JSON·FBX 에 안 쓰는 머티리얼이 남지 않게)."""
    k3d.select([o])
    bpy.ops.object.material_slot_remove_unused()
    return o


def band():
    """간판 띠 + 얕은 처마. 치수만 규격에 맞추고 머티리얼·구성은 facade.py 그대로다."""
    m = bpy.data.materials
    red, alud, cream, steel, ret, soffit = (m["SF_" + n] for n in ("RedACP", "AluDark", "CreamPaint", "Steel", "LetterReturn", "Soffit"))
    logo = {k: m[f"M_{A}_Logo{k}"] for k in ("Crown", "Bun", "Patty", "Seed")}
    light = m[f"M_{A}_Downlight"]
    H = 3.1
    SZ0, SZ1 = 3.195, 4.288      # 판 아래·위. 위 마감 포함 높이 4.30
    SYF = -0.275                 # 판 앞면. 로고 앞면이 -0.331 이라 Sign(-0.345) 보다 뒤, 글자는 판에서 7cm 뜬 채널 글자처럼 보인다
    CY = -0.25                   # 처마 앞선 (원본 -1.0 은 깊이 규격 0.39 를 넘는다)
    S = [box2((X0, SYF, SZ0), (X1, -0.01, SZ1), red, 0.006, 3),
         box2((X0 - 0.012, SYF - 0.012, SZ1 - 0.035), (X1 + 0.012, -0.01, SZ1 + 0.012), alud, 0.004, 2),
         box2((X0 - 0.012, SYF - 0.012, SZ0 - 0.012), (X1 + 0.012, -0.01, SZ0 + 0.035), alud, 0.004, 2),
         box2((X0, SYF - 0.002, SZ1 - 0.11), (X1, SYF + 0.01, SZ1 - 0.085), cream, 0.001, 1),
         box2((X0, SYF - 0.002, SZ0 + 0.085), (X1, SYF + 0.01, SZ0 + 0.11), cream, 0.001, 1),
         # 처마: 헤더까지 닫는 하부판 + 빨강 앞띠 + 크림 선 + 양 끝 마구리
         box2((X0, CY, H + 0.02), (X1, -0.06, H + 0.09), soffit, 0.004, 2),
         box2((X0, CY - 0.03, H - 0.1), (X1, CY, H + 0.1), red, 0.004, 2),
         box2((X0, CY - 0.034, H - 0.06), (X1, CY - 0.029, H - 0.045), cream, 0.001, 1),
         box2((X0 - 0.012, CY - 0.03, H - 0.1), (X0 + 0.018, -0.06, H + 0.1), red, 0.004, 2),
         box2((X1 - 0.018, CY - 0.03, H - 0.1), (X1 + 0.012, -0.06, H + 0.1), red, 0.004, 2)]
    for x in [X0 + 0.3 + i * (X1 - X0 - 0.6) / 7 for i in range(8)]:   # 패널 이음 리벳
        for z in (SZ0 + 0.06, SZ1 - 0.06):
            S.append(cyl(A + "_Rivet", 0.005, 0.003, (x, SYF - 0.0015, z), steel, rot=(math.pi / 2, 0, 0), n=10, bev=0.001, seg=1))
    for x in (-5.2, -3.0, -0.8, 1.4, 3.6):                             # 다운라이트
        S.append(cyl(A + "_DLRing", 0.07, 0.008, (x, -0.155, H + 0.016), steel, n=28, bev=0.002))
        S.append(cyl(A + "_DL", 0.055, 0.004, (x, -0.155, H + 0.0105), light, n=28, bev=0))
    # 로고: 프로토타입 Rn() 좌표. 판이 낮아진 만큼 줄여서 z 3.33..4.24 에 넣는다
    LX, U = -3.32, 0.91 / 124
    LZ = 3.33 + 34 * U
    lp = lambda pts: [(LX + x * U, LZ - y * U) for x, y in pts]
    parts = [("Crown", [(-30, -48), (-34, -82), (-14, -62), (0, -90), (14, -62), (34, -82), (30, -48)]),
             ("Bun", [(62 * math.cos(a), -8 - 44 * math.sin(a)) for a in [math.pi * i / 24 for i in range(25)]]),
             ("Patty", [(-60, -6), (60, -6), (60, 10), (-60, 10)]),
             ("Bun", sf.rrect_pts(-58, 12, 58, 34, 8))]
    seeds = [sf.ellipse_pts(-40 + i * 13, -30 + (i % 2) * 9, 3.2, 1.8, n=8)[:-1] for i in range(7)]
    for k, pts, depth in [(k, p, 0.05) for k, p in parts] + [("Seed", p, 0.056) for p in seeds]:
        o = sf.poly_extrude(A + "_Logo" + k, lp(pts), depth)
        sf.mat_by_normal(o, logo[k], ret)
        o.location.y = SYF
        S.append(o)
    o = sf.join(S, "PH_Storefront_Band")
    k3d.set_origin(o, (0, 0, 0))
    only([o])
    k3d.bake(o, 2048, keep=tuple(x.name for x in o.data.materials if x.name.startswith("M_")), ao_distance=0.08, samples=32)
    return o


# ================================================================ 유리문 문짝
ph.load("Storefront", "StoreGlassDoor")
door = ph.part(LEAF, [bpy.data.objects["StoreGlassDoor_Leaf"]], LEAF_M)   # 클로저 암·당기세요 스티커는 별도 오브젝트라 빠진다
ph.finish(LEAF, door, notes={
    "pivot": "원점 = 문틀 쪽 끝, 문 두께 중심, 바닥. 문짝은 경첩에서 +X 로 0.927m. 앞(거리, 손잡이·클로저 본체 쪽) -Z.",
    "sticker": "당기세요 스티커는 넣지 않았다. 유리 z 0, 문틀 면 z -0.025 라 Sticker_Pull(z -0.03) 이 앞에 온다. 매장 쪽 미세요 스티커는 z +0.0025.",
    "closer": "클로저 암은 뺐다: 닫힌 상태에서 z -0.244 까지 나와 깊이 규격을 넘고, 헤더에 붙은 채 움직이려면 2링크 계산이 필요하다.",
})
only([door])
k3d.preview(LEAF, [door], views=((180, 6), (150, 12), (0, 6)), tag="ph")

# ================================================================ 1층 매장 면
ph.load("Storefront", "StorefrontFacade")
ob = bpy.data.objects
frame, sign = ob[A + "_Frame"], ob[A + "_Sign"]
# 깊이 밖(처마·발매트·도어스토퍼)과 양옆 가게, 암이 없어 쓸모없어진 클로저 슈 받침을 뺀다
store = crop(frame, "PH_Storefront_Frame", lambda a, b: a.y > -0.08 and a.x > -6.1 and b.x < 5.6
             and not (a.x > 1.2 and b.x < 1.3 and a.z > 2.29 and b.y < -0.04))
for v in store.data.vertices:   # 헤더만 양 끝이 2.5cm 더 나와 있다
    v.co.x += 0.025 if v.co.x < X0 else -0.025 if v.co.x > X1 else 0
fascia = band()
sto = clean(ph.part("PH_Storefront", [store, fascia], ph.turn(180)))
ph.finish("PH_Storefront", sto, notes={
    "pivot": "원점 = 매장 x=0 유리선 바닥. 범위 x -6.047..5.547, 높이 4.30, z -0.331..+0.07. 유리 z 0.",
    "door": "문 개구 x 0.935..1.865, 높이 2.29. 양옆 문설주(멀리언)와 문 위 유리, 바닥 7mm 문턱은 남겼다.",
    "sign": "글자(버거대왕, 시장입구점)는 없다. 판 앞면 z -0.275, 로고 앞면 z -0.331 로 모두 Sign(z -0.345) 뒤다.",
    "canopy": "원본 1m 처마는 깊이 규격을 넘어 z -0.28 까지의 얕은 처마로 줄였다. 원본 M_StorefrontFacade_Sign 은 글자 자국이 구워져 있어 쓰지 않는다.",
})
only([sto])
k3d.preview("PH_Storefront", [sto], views=((180, 6), (150, 12), (0, 6)), tag="ph")

# ================================================================ 선택: 위층과 양옆 가게 (PH_Storefront 와 같은 원점에 두면 건물 전체)
up = clean(ph.part("PH_StorefrontUpper", [crop(frame, "Neighbours", lambda a, b: b.x < -6.4 or a.x > 5.9),
                                          crop(sign, "UpperSigns", lambda a, b: a.z > 4.44),
                                          ob[A + "_Windows"], ob[A + "_WallTile"], ob[A + "_WallGranite"]], ph.turn(180)))
ph.finish("PH_StorefrontUpper", up, notes={"pivot": "PH_Storefront 와 같은 원점. 규격표에 없는 선택 모델이다. 처마·발매트는 포함하지 않는다."})
only([up])
k3d.preview("PH_StorefrontUpper", [up], views=((165, 10),), tag="ph")

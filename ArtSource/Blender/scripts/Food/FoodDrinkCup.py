# 종이컵 + 플라스틱 뚜껑 + 빨대. 콜라/사이다 두 변형 (인쇄 텍스처만 다름) — 엔딩 펀치라인용 '사이다/콜라' 라벨
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _food import *

RB, RT, H = 0.032, 0.0455, 0.148      # 바닥 반지름, 윗 반지름, 컵 몸통 높이 (16oz)
ZP0, ZP1 = 0.004, H                   # 인쇄 영역 높이 범위
LID_S, LID_BTN = 0.06, (("콜라", -126), ("사이다", -90), ("기타", -54))  # 뚜껑 버튼 (_tex.py 와 같은 값)
textures()


def wall_r(z):
    return RB + (RT - RB) * z / H


def build(kind):
    A = f"FoodDrinkCup_{kind}"
    k3d.reset()
    straw_col = {"Cola": "#c8291f", "Cider": "#79b24a"}[kind]
    name = {"Cola": "콜라", "Cider": "사이다"}[kind]

    # ---------------- 머티리얼
    s = Sh(f"M_{A}_Print", "#f4ead6", .42)
    x, y, z = s.xyz()
    u = s.math('ADD', s.math('DIVIDE', s.math('ARCTAN2', x, s.math('MULTIPLY', y, -1)), 2 * math.pi), .5)
    v = s.mr(z, ZP0, ZP1, 0, 1, clamp=False)
    col = s.image(os.path.join(TEX, f"cup_{kind.lower()}.png"), s.comb(u, v, 0), ext='EXTEND')
    col = s.mix(col, s.ramp(s.noise(260, 3, .5), [(0, "#ffffff"), (1, "#e6ddcc")]), .3, 'MULTIPLY')
    col = s.mix(col, "#7d6a52", s.math('MULTIPLY', s.mr(z, 0, .025, 1, 0), s.mr(s.noise(40, 3, .5), .3, .7, .1, .35)))  # 바닥 쪽 때
    smudge = s.mr(s.noise(18, 3, .6, dist=1.5), .55, .7, 0, 1)  # 손자국: 광택만 살짝
    rough = s.math('ADD', s.mr(s.noise(90, 3, .5), .3, .7, .36, .48), s.math('MULTIPLY', smudge, -.1))
    wet = s.math('MULTIPLY', s.mr(z, .1, .04), s.mr(s.noise(7, 2, .5), .38, .58))           # 찬 음료: 아래쪽 습기
    drop = s.math('MULTIPLY', s.mr(s.voronoi(700), .3, .08), wet)                              # 물방울
    rough = s.math('MULTIPLY', rough, s.math('SUBTRACT', 1, s.math('ADD', s.math('MULTIPLY', wet, .35), s.math('MULTIPLY', drop, .5))))
    col = s.mix(col, s.mix(col, "#c9c2b6", .5, 'MULTIPLY'), s.math('MULTIPLY', drop, .25))
    pm = s.out(col, rough, s.bump(s.math('ADD', s.math('ADD', s.noise(900, 2, .5), s.math('MULTIPLY', s.wave(30, 6, direction='Z'), .3)),
                                      s.math('MULTIPLY', s.math('SQRT', drop), 3)), .06, .0002))

    s = Sh(f"M_{A}_Lid", "#f2f1ec", .3)
    x, y, z = s.xyz()
    nz_ = s.xyz(s.tc('Normal'))[2]
    r = s.vmath('LENGTH', s.comb(x, y, 0))
    slit = s.math('MULTIPLY', s.math('LESS_THAN', s.math('MINIMUM', s.math('ABSOLUTE', s.math('ADD', x, y)),
                                                                  s.math('ABSOLUTE', s.math('SUBTRACT', x, y))), .00045),
                  s.math('LESS_THAN', r, .0062))
    col = s.mix("#e6ebe9", "#c9d1cf", s.noise(120, 3, .5))  # 반투명 PP (살짝 차갑고 비치는 흰색)
    col = s.mix(col, {"Cola": "#4a3428", "Cider": "#dfe8da"}[kind], s.math('MULTIPLY', s.mr(r, RT - .001, RT - .004), .35))  # 안의 음료가 비침
    col = s.mix(col, "#8f8a80", s.math('MULTIPLY', s.math('SUBTRACT', 1, s.ao(.004)), .6))
    luv = s.comb(s.math('ADD', s.math('DIVIDE', x, LID_S), .5), s.math('ADD', s.math('DIVIDE', y, LID_S), .5), 0)
    limg = os.path.join(TEX, f"lid_{kind.lower()}.png")
    col = s.mix(col, s.image(limg, luv, ext='CLIP'), s.math('MULTIPLY', s.image(limg, luv, ext='CLIP', out='Alpha'), s.mr(nz_, .8, .95)))
    col = s.mix(col, "#3b3833", slit)
    dome = 0.0
    for nm, deg in LID_BTN:  # 음료 표시 버튼: 볼록, 주문한 음료는 눌려서 오목
        a = math.radians(deg)
        d2 = s.math('DIVIDE', s.vmath('LENGTH', s.comb(s.math('SUBTRACT', x, .0195 * math.cos(a)), s.math('SUBTRACT', y, .0195 * math.sin(a)), 0)), .0042)
        h = s.math('MULTIPLY', s.math('SQRT', s.math('MAXIMUM', s.math('SUBTRACT', 1, s.math('MULTIPLY', d2, d2)), 0)), -.6 if nm == name else 1)
        dome = h if isinstance(dome, float) else s.math('ADD', dome, h)
    scratch = s.mr(s.wave(400, 12, wave_type='BANDS', direction='X'), .93, 1, 0, 1)
    lr = s.math('ADD', s.mr(s.noise(60, 3, .5), .3, .7, .05, .1), s.math('MULTIPLY', scratch, .12))
    lm = s.out(col, lr, s.bump(s.math('ADD', slit, s.math('MULTIPLY', scratch, .3)), .2, .0003, normal=s.bump(dome, .9, .0009)))

    s = Sh(f"M_{A}_Straw", straw_col, .3)
    x, y, z = s.xyz()
    col = s.mix(straw_col, "#1e0a06", s.math('MULTIPLY', s.attr("inner"), .8))
    col = s.mix(col, "#ffffff", s.mr(s.noise(40, 2, .5), .6, .75, 0, .12))
    sm = s.out(col, .28, s.bump(s.noise(300, 2, .5), .05, .0002))

    # ---------------- 컵 몸통 (말린 입구 + 바닥 스커트)
    prof = [(0, .0072), (RB - .0024, .0072), (RB - .0016, .0064), (RB - .0012, .0012), (RB - .0006, .0001), (RB, .0007)]
    for k in range(1, 13):
        zz = .0012 + (H - .0032) * k / 12
        prof.append((wall_r(zz), zz))
    for k in range(9):  # 말린 입구 비드 (반지름 1.6mm)
        a = -math.pi / 2 + math.pi * 1.25 * k / 8
        prof.append((RT + .0003 + .0016 * math.cos(a) * .9, H - .0003 + .0016 * (1 + math.sin(a))))
    prof += [(RT - .002, H + .0012), (RT - .0035, H + .0004), (0, H + .0004)]
    seam = lambda a, i, r, z: 1 + (.006 if math.pi / 2 - .05 < a < math.pi / 2 + .05 and 5 < i < 18 else 0) \
        + .0025 * nz(math.cos(a) * 3, math.sin(a) * 3, z * 25 + 7)  # 이음매 겹침 + 살짝 찌그러짐
    body = lathe(f"{A}_Body", prof, 64, seam)
    mats(body, pm)

    # ---------------- 뚜껑
    lp = [(wall_r(H - .0034), H - .0034), (RT + .0013, H - .0038), (RT + .0021, H - .0036), (RT + .0024, H - .0008),
          (RT + .0024, H + .0027), (RT + .0021, H + .0034), (RT + .0004, H + .0039), (RT - .0035, H + .0058),
          (.039, H + .0072), (.035, H + .0076), (.0325, H + .0071), (.0305, H + .0052), (.028, H + .0041),
          (.012, H + .0039), (.0085, H + .0043), (.0068, H + .0058), (.004, H + .0063), (0, H + .0064)]
    lid = lathe(f"{A}_Lid", lp, 64)
    mats(lid, lm)

    # ---------------- 빨대 (속이 빈 관, 6도 기울임)
    ro, ri, z0, z1 = .0036, .0032, H - .05, H + .082
    st = lathe(f"{A}_Straw", [(ri, z0 + .001), (ro, z0), (ro, z1), (ri + .0002, z1 + .0002), (ri, z1 - .004), (ri, z0 + .03)], 16)
    vattr(st, "inner", lambda co: 1.0 if (math.hypot(co.x, co.y) < ri + 1e-4 and co.z < z1 - .001) else 0.0)
    st.rotation_euler = (0, math.radians(6), 0)
    sx = -(H + .0064) * math.tan(math.radians(6))  # 뚜껑 가운데 십자 칼집을 지나도록
    st.location = (sx, 0, 0)
    bpy.context.view_layer.update()
    mats(st, sm)

    parts = [body, lid, st]
    for o in parts:
        smooth(o, 50)
        if "inner" not in o.data.attributes:
            const_attr(o, "inner", 0.0)
    me = join(parts, f"{A}_Mesh")
    k3d.select([me])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    k3d.bake(me, size=2048, samples=48)
    tip = Vector((0, 0, z1))
    tip = Matrix.Rotation(math.radians(6), 3, 'Y') @ tip + Vector((sx, 0, 0))
    socket(me, A, "Grip", (0, 0, .085))
    socket(me, A, "StrawTip", tuple(tip))
    socket(me, A, "Label", (0, -wall_r(.022) - .001, .022))
    k3d.export(A, "Food", [me], notes={
        "desc": f"16oz 종이컵 + 뚜껑 + 빨대 ({name}). 컵 인쇄의 띠 색/글씨와 앞쪽 주문 스티커('주문 274 · {name}(M)')로 음료를 구분. "
                "뚜껑은 반투명 PP(안의 음료가 비침)에 음료 표시 버튼 3개(콜라/사이다/기타, 주문한 음료 버튼이 눌림). 정면 -Y(로고), 원점 바닥 중앙, 빨대 포함 높이 약 0.229m. FoodDrinkCup_Cola/Cider 는 메시 동일·텍스처만 다름.",
        "sockets": {f"{A}_Socket_Grip": "손으로 쥐는 중심", f"{A}_Socket_StrawTip": "빨대 끝(마실 때 입 위치)",
                    f"{A}_Socket_Label": "앞쪽 주문 스티커 (확대해 보기용 시선 타깃)"}})
    k3d.preview(A, [me])
    k3d.preview(A, [me], views=((0, 8),), lens=35, tag='fp')
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -.01, H + .004))  # 뚜껑 근접 렌더용 프레이밍 상자 (렌더/내보내기 안 됨)
    fr = bpy.context.object
    fr.scale, fr.hide_render = (.07, .05, .006), True
    bpy.context.view_layer.update()
    k3d.preview(A, [fr], views=((0, 50),), ground=False, res=(900, 600), tag='lid')


for kind in ("Cola", "Cider"):
    build(kind)

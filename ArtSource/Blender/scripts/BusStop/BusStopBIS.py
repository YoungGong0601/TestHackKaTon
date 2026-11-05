"""BusStopBIS: 기둥형 양면 LED 버스도착안내기.
프로토타입(Kd): 기둥 3.1 m, 함체 1.6 x 0.72 m, 표시부 1.5 x 0.62 m 양면, 중심 높이 2.72 m.
정면 = -Y (뒷면 표시부는 +Y), 원점 = 기둥 바닥 중심."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bs as B
from _bs import k3d

A = "BusStopBIS"
k3d.reset()
tdir, lay = B.textures(A)

paint = B.m_paint("P_BIS_Paint", (0.042, 0.047, 0.052), rough=0.42, wear=0.35, grime=0.55, rust=0.3)
dark = B.m_plastic("P_BIS_Dark", (0.012, 0.012, 0.013), rough=0.55, grime=0.3)
steel = B.m_metal("P_BIS_Steel", (0.56, 0.56, 0.57), rough=0.35, grime=0.4, brushed=False)
rubber = B.m_rubber("P_BIS_Rubber")
disp = B.m_image("M_Dyn_BusStopBIS_Display", os.path.join(tdir, "T_BusStopBIS_Display.png"), rough=0.3, emit=1.6)
dec = B.m_image("M_BusStopBIS_Decals", os.path.join(tdir, "T_BusStopBIS_Decals.png"), rough=0.5, clip=0.5)

P = []
# 기둥 Ø114 + 바닥 덮개 + 점검구
R = 0.0572
P.append(B.cyl("p", R, 2.33, (0, 0, 0), paint, n=32))
P.append(B.cyl("p", 0.13, 0.045, (0, 0, 0), paint, n=32, bevel=0.008, r2=0.112))
P.append(B.cyl("p", 0.085, 0.03, (0, 0, 0.045), paint, n=32, bevel=0.004))
for a in range(6):                                                    # 덮개 볼트
    t = a / 6 * B.TAU
    P.append(B.cyl("p", 0.011, 0.012, (math.cos(t) * 0.1, math.sin(t) * 0.1, 0.038), steel, n=6, bevel=0.001))
P.append(B.box("p", (0.07, 0.022, 0.26), (0, -0.051, 0.5), paint, bevel=0.003))
for z in (0.39, 0.61):
    P.append(B.cyl("p", 0.006, 0.004, (0, -0.062, z), steel, n=8, bevel=0.001, rot=(math.pi / 2, 0, 0)))
P.append(B.cyl("p", 0.062, 0.02, (0, 0, 1.0), paint, n=32, bevel=0.003))   # 기둥 이음 띠

# 브래킷 (기둥 -> 함체)
P.append(B.box("p", (0.36, 0.13, 0.04), (0, 0, 2.33), paint, bevel=0.004))
for s in (-1, 1):
    P.append(B.prism("p", [(s * R * 0.9, 2.16), (s * 0.17, 2.31), (s * R * 0.9, 2.31)][::s], 0.012, paint, axis='Y',
                     bevel=0.002))
    for y in (-0.04, 0.04):
        P.append(B.cyl("p", 0.012, 0.012, (s * 0.14, y, 2.298), steel, n=6, bevel=0.001))
P.append(B.pipe("p", B.bend([(0.05, 0.035, 2.08), (0.05, 0.035, 2.2), (0.24, 0.035, 2.25), (0.24, 0.035, 2.36)], 0.05),
                0.012, rubber))

# 함체: 평면이 경기장 모양 (곧은 면 1.62 m + 둥근 끝 r 0.08)
def stadium(half, r, n=10):
    pts = [(half + math.cos(math.radians(-90 + 180 * i / n)) * r, math.sin(math.radians(-90 + 180 * i / n)) * r)
           for i in range(n + 1)]
    return pts + [(-x, -y) for x, y in pts]

P.append(B.prism("p", stadium(0.81, 0.08), 0.74, paint, axis='Z', loc=(0, 0, 2.72), bevel=0.004))
P.append(B.prism("p", stadium(0.83, 0.105), 0.03, paint, axis='Z', loc=(0, 0, 3.105), bevel=0.006))   # 비 가림 갓
P.append(B.prism("p", stadium(0.812, 0.084), 0.012, dark, axis='Z', loc=(0, 0, 2.346), bevel=0.002))
for i in range(9):                                                    # 바닥 통풍구
    P.append(B.box("p", (0.08, 0.014, 0.004), (-0.6 + i * 0.15, 0, 2.339), dark, bevel=0.001))
for s in (-1, 1):                                                     # 양면 베젤 + 나사
    y = s * 0.086
    P.append(B.box("p", (1.6, 0.012, 0.04), (0, y, 3.04), dark, bevel=0.003))
    P.append(B.box("p", (1.6, 0.012, 0.04), (0, y, 2.38), dark, bevel=0.003))
    for x in (-0.77, 0.77):
        P.append(B.box("p", (0.04, 0.011, 0.7), (x, y, 2.71), dark, bevel=0.003))
    for x in (-0.77, 0, 0.77):
        for z in (2.38, 3.04):
            P.append(B.cyl("p", 0.0045, 0.003, (x, s * 0.092, z), steel, n=8, bevel=0.0008, segs=1,
                           rot=(math.pi / 2 * (1 if s < 0 else -1), 0, 0)))
body = B.join(P, A + "_Body")
k3d.uv_world(body, 1.0)  # 합친 메시의 빈(0) UV 면 -> 굽기 탄젠트가 깨져 노멀맵 얼룩. 전부 유효 UV 로

# 표시부 (M_Dyn, 양면 같은 머티리얼 / 뒷면은 U 가 -X 로)
dq = [B.quad("d", 1.5, 0.62, disp, (0, -0.0812, 2.71)), B.quad("d", 1.5, 0.62, disp, (0, 0.0812, 2.71), (0, 0, math.pi))]
display = B.join(dq, A + "_Display")

# 데칼: 상단 인쇄 글자, 기둥 스티커
L = []
for s in (-1, 1):
    L.append(B.decal("l", lay, "bezel_label", dec, (-0.42 * -s, s * 0.0812, 3.075), (0, 0, 0 if s < 0 else math.pi),
                     w=0.52))
d = lay["decals"]
for key, z, ang in (("pole_sticker", 1.55, 0.0), ("pole_sticker", 1.55, math.pi), ("danger", 0.72, 0.0),
                    ("maker_plate", 1.28, 0.5)):
    L.append(B.wrap("l", R + 0.0008, d[key]["w"], d[key]["h"], dec, z, ang, d[key]["uv"]))
decals = B.join(L, A + "_Decals")
B.parent([display, decals], body)

B.bake_hidden(body, 1024, hide=(display, decals), samples=48, ao_distance=0.25)
B.socket(A + "_Socket_LookTarget", (0, -0.085, 2.71), body)
B.socket(A + "_Socket_LookTarget_Back", (0, 0.085, 2.71), body, (0, 0, math.pi))

notes = {
    "pivot": "기둥 바닥 중심. 정면(-Y→Unity +Z)과 뒷면 모두 표시부. 프로토타입처럼 도로와 직각으로 세우면 양쪽 보행자가 본다.",
    "dynamic": [{"object": A + "_Display", "material": "M_Dyn_BusStopBIS_Display", "size_m": [1.5, 0.62],
                 "texture_px": [2048, 846], "uv": "면마다 UV 0..1, U→오른쪽 V→위 (각 면을 정면에서 볼 때). 앞뒤 2장이 같은 머티리얼",
                 "placeholder": "Textures/BusStopBIS/T_BusStopBIS_Display.png (버스 놓치기 전: 2413 곧 도착 / 112 6분 / 7 11분)",
                 "alt": "Textures/BusStopBIS/T_BusStopBIS_Display_After.png (놓친 뒤: 112 곧 도착 / 7 9분 / 2413 14분)",
                 "emission": "발광 1.6 (주황 LED 도트 224x92)",
                 "base_lens": [{"base": "Textures/BusStopBIS/T_BusStopBIS_Display_Base.png",
                                "lens": "Textures/BusStopBIS/T_BusStopBIS_Display.png"},
                               {"base": "Textures/BusStopBIS/T_BusStopBIS_Display_After_Base.png",
                                "lens": "Textures/BusStopBIS/T_BusStopBIS_Display_After.png"}],
                 "readable": "base = 돋보기 밖(글자 대신 막대 + 흐림, 프로토타입 tBase), lens = 돋보기 안(선명, tLens). "
                             "머티리얼 기본 텍스처는 lens. 런타임에 base 를 깔고 돋보기 원 안만 lens 로 바꾼다"}],
    "sockets": {A + "_Socket_LookTarget": "앞 표시부 중심 (높이 2.71 m, 돋보기/시선 판정)",
                A + "_Socket_LookTarget_Back": "뒷 표시부 중심"},
    "collider": "기둥 원기둥 r0.06 h2.33 + 함체 박스 1.78x0.18x0.77 (중심 높이 2.72)",
}
fbx = k3d.export(A, "BusStop", [body], notes=notes)
k3d.preview(A, [body])
B.shot(A, (-1.4, -5.2, 1.55), (0, 0, 2.6), 35, "fp")
B.shot(A, (-0.25, -1.6, 1.55), (0, 0, 2.71), 40, "close")

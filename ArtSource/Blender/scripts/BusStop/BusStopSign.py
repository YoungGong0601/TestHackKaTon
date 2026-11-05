"""BusStopSign: 버스정류소 표지판 (기둥 + 머리판 + 노선 안내판).
머리판 0.50 x 0.56 m (정류장 이름·번호), 노선판 0.50 x 0.86 m (작은 글씨 노선 목록, M_Dyn, 돋보기용).
정면 = -Y (뒷면도 같은 그림), 원점 = 기둥 바닥 중심."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bs as B
from _bs import k3d

A = "BusStopSign"
k3d.reset()
tdir, lay = B.textures(A)

paint = B.m_paint("P_Sign_Paint", (0.15, 0.16, 0.17), rough=0.45, wear=0.4, grime=0.55, rust=0.35, fade=0.45)
frame = B.m_paint("P_Sign_Frame", (0.62, 0.63, 0.64), rough=0.38, wear=0.25, grime=0.6, rust=0.12, fade=0.2,
                  bare=(0.7, 0.7, 0.71))
steel = B.m_metal("P_Sign_Steel", (0.56, 0.56, 0.57), rough=0.35, grime=0.5, brushed=False)
dark = B.m_plastic("P_Sign_Gasket", (0.015, 0.015, 0.016), rough=0.7, grime=0.3)
head = B.m_image("M_BusStopSign_Head", os.path.join(tdir, "T_BusStopSign_Head.png"), rough=0.32)
routes = B.m_image("M_Dyn_BusStopSign_Routes", os.path.join(tdir, "T_BusStopSign_Routes.png"), rough=0.3)
dec = B.m_image("M_BusStopSign_Decals", os.path.join(tdir, "T_BusStopSign_Decals.png"), rough=0.6, clip=0.5)

R = 0.0381                                   # 기둥 Ø76.3
HD = 0.09                                    # 판 함체 두께 (기둥이 안으로 들어감)
P = []
# 기둥 + 바닥 덮개 + 볼트 + 꼭대기 마개
P.append(B.cyl("p", R, 2.38, (0, 0, 0), paint, n=28))
P.append(B.cyl("p", 0.1, 0.035, (0, 0, 0), paint, n=28, bevel=0.006, r2=0.085))
P.append(B.cyl("p", 0.052, 0.03, (0, 0, 0.035), paint, n=28, bevel=0.004))
for a in range(4):
    t = a / 4 * B.TAU + math.pi / 4
    P.append(B.cyl("p", 0.01, 0.012, (math.cos(t) * 0.074, math.sin(t) * 0.074, 0.03), steel, n=6, bevel=0.001))


def panel(w, h, zc, r=0.03):
    """판 함체: 둥근 사각 몸통 + 앞뒤 베젤 4변 + 고무 가스켓 + 모서리 나사."""
    P.append(B.prism("p", B.rrect(w, h, r, 5), HD - 0.01, frame, axis='Y', loc=(0, 0, zc), bevel=0.004))
    fw, fh = w - 0.06, h - 0.06
    for s in (-1, 1):
        y = s * (HD / 2 - 0.002)
        P.append(B.box("p", (w - 0.004, 0.012, 0.032), (0, y, zc + h / 2 - 0.016), frame, bevel=0.004))
        P.append(B.box("p", (w - 0.004, 0.012, 0.032), (0, y, zc - h / 2 + 0.016), frame, bevel=0.004))
        for x in (-1, 1):
            P.append(B.box("p", (0.032, 0.011, h - 0.004), (x * (w / 2 - 0.016), y, zc), frame, bevel=0.004))
        for x in (-1, 1):                                              # 가스켓 띠
            P.append(B.box("p", (0.006, 0.004, fh + 0.006), (x * (fw / 2 + 0.003), s * (HD / 2 - 0.004), zc), dark,
                           bevel=0.001, segs=1))
        for z in (-1, 1):
            P.append(B.box("p", (fw + 0.012, 0.004, 0.006), (0, s * (HD / 2 - 0.004), zc + z * (fh / 2 + 0.003)), dark,
                           bevel=0.001, segs=1))
        for x in (-1, 1):                                              # 모서리 나사
            for z in (-1, 1):
                P.append(B.cyl("p", 0.0055, 0.003, (x * (w / 2 - 0.016), s * (HD / 2 + 0.004), zc + z * (h / 2 - 0.016)),
                               steel, n=8, bevel=0.0008, segs=1, rot=(-s * math.pi / 2, 0, 0)))   # 삼각형 예산: segs 1
    P.append(B.box("p", (w * 0.6, 0.03, 0.006), (0, 0, zc - h / 2 - 0.002), dark, bevel=0.001))   # 아래 물빠짐 틈


panel(0.56, 0.62, 2.62)                       # 머리판
panel(0.56, 0.92, 1.46)                       # 노선판
P.append(B.prism("p", B.rrect(0.6, 0.11, 0.05, 6), 0.026, frame, axis='Z', loc=(0, 0, 2.944), bevel=0.006))  # 빗물 갓
for z in (2.25, 0.955, 1.965):                                         # 기둥 밴드 클램프 + 볼트
    P.append(B.cyl("p", R + 0.006, 0.032, (0, 0, z), steel, n=28, bevel=0.002))
    P.append(B.box("p", (0.03, 0.03, 0.026), (R + 0.012, 0, z + 0.016), steel, bevel=0.002))
    P.append(B.cyl("p", 0.006, 0.05, (R + 0.012, -0.025, z + 0.016), steel, n=6, bevel=0.001, rot=(math.pi / 2, 0, 0)))
body = B.join(P, A + "_Body")
k3d.uv_world(body, 1.0)  # 합친 메시의 빈(0) UV 면 -> 굽기 탄젠트가 깨져 노멀맵 얼룩. 전부 유효 UV 로

# 머리판 그림 (앞뒤, 같은 머티리얼 / 뒷면은 U 가 -X)
fy = HD / 2 - 0.0035
hq = [B.quad("h", 0.5, 0.56, head, (0, -fy, 2.62)), B.quad("h", 0.5, 0.56, head, (0, fy, 2.62), (0, 0, math.pi))]
headf = B.join(hq, A + "_Head")
rq = [B.quad("r", 0.5, 0.86, routes, (0, -fy, 1.46)), B.quad("r", 0.5, 0.86, routes, (0, fy, 1.46), (0, 0, math.pi))]
routef = B.join(rq, A + "_Routes")

# 데칼: 기둥 전단지·테이프 자국·관리번호
d = lay["decals"]
L = []
for key, z, ang in (("flyer_room", 0.74, 0.25), ("flyer_job", 0.7, math.pi + 0.4), ("tape", 2.1, 0.1),
                    ("tape", 0.5, math.pi * 0.6), ("pole_plate", 0.32, 0.0)):
    w = min(d[key]["w"], R * 2 * math.pi * 0.45)
    s = w / d[key]["w"]
    L.append(B.wrap("l", R + 0.0009 + 0.0004 * len(L), w, d[key]["h"] * s, dec, z, ang, d[key]["uv"]))
decals = B.join(L, A + "_Decals")
B.parent([headf, routef, decals], body)

B.bake_hidden(body, 1024, hide=(headf, routef, decals), samples=48, ao_distance=0.2)
B.socket(A + "_Socket_LookTarget_Routes", (0, -fy, 1.46), body)
B.socket(A + "_Socket_LookTarget_Head", (0, -fy, 2.62), body)

notes = {
    "pivot": "기둥 바닥 중심. 앞(-Y→Unity +Z)·뒤 모두 같은 그림. 승차대 옆 보도에 세운다.",
    "dynamic": [{"object": A + "_Routes", "material": "M_Dyn_BusStopSign_Routes", "size_m": [0.5, 0.86],
                 "texture_px": [1190, 2048], "uv": "면마다 UV 0..1, U→오른쪽 V→위 (각 면을 정면에서 볼 때), 앞뒤 2장 같은 머티리얼",
                 "placeholder": "Textures/BusStopSign/T_BusStopSign_Routes.png (112/2413/7 노선 정류장 목록, 실제 크기 약 11 mm 글씨 — 돋보기 없이는 못 읽게)",
                 "center_height_m": 1.46,
                 "base_lens": [{"base": "Textures/BusStopSign/T_BusStopSign_Routes_Base.png",
                                "lens": "Textures/BusStopSign/T_BusStopSign_Routes.png"}],
                 "readable": "base = 돋보기 밖(흐림 9 px, 작은 글씨 못 읽음), lens = 돋보기 안(선명). 머티리얼 기본 텍스처는 lens"}],
    "static_image": {"object": A + "_Head", "material": "M_BusStopSign_Head", "size_m": [0.5, 0.56],
                     "content": "BUS STOP 은행골 입구 / 정류소 번호 14-208"},
    "sockets": {A + "_Socket_LookTarget_Routes": "노선판 중심 (높이 1.46 m, 돋보기/시선 판정)",
                A + "_Socket_LookTarget_Head": "머리판 중심 (높이 2.62 m)"},
    "collider": "기둥 원기둥 r0.04 h2.97 + 판 박스 0.56x0.09x(0.62@2.62, 0.92@1.46)",
}
fbx = k3d.export(A, "BusStop", [body], notes=notes)
k3d.preview(A, [body])
B.shot(A, (-0.9, -3.2, 1.55), (0, 0, 1.9), 35, "fp")
B.shot(A, (-0.15, -0.75, 1.55), (0, 0, 1.46), 40, "close")

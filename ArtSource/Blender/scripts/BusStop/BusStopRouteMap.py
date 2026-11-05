"""BusStopRouteMap: 승차대 뒷유리에 붙는 노선도 액자 (알루미늄 스냅 프레임 + 아크릴 덮개).
프로토타입(Kd): 노선도 1.00 x 1.36 m, 중심 높이 1.32 m, 뒷유리 앞면에 붙어 거리 쪽을 본다.
정면 = -Y, 원점 = 바닥(뒷면 고정쇠가 유리에 닿는 면, y=0). BusShelter_Socket_RouteMap 에 놓으면 맞는다."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bs as B
from _bs import k3d

A = "BusStopRouteMap"
k3d.reset()
tdir, lay = B.textures(A)

alu = B.m_paint("P_RM_Alu", (0.6, 0.61, 0.62), rough=0.34, wear=0.2, grime=0.65, rust=0.05, fade=0.15,
                bare=(0.75, 0.75, 0.76), ground=0.0)
cap = B.m_plastic("P_RM_Cap", (0.05, 0.052, 0.055), rough=0.55, grime=0.5)
steel = B.m_metal("P_RM_Steel", (0.62, 0.62, 0.63), rough=0.25, grime=0.4)
back = B.m_metal("P_RM_Back", (0.5, 0.5, 0.5), rough=0.5, grime=0.6, brushed=False, metal=0.6)
mp = B.m_image("M_Dyn_BusStopRouteMap_Map", os.path.join(tdir, "T_BusStopRouteMap_Map.png"), rough=0.55)
dec = B.m_image("M_BusStopRouteMap_Decals", os.path.join(tdir, "T_BusStopRouteMap_Decals.png"), rough=0.6, clip=0.5)
gl = B.m_glass("M_Glass_BusStopRouteMap_Cover",
               os.path.join(k3d.ART, "Textures", "BusShelter", "T_BusShelter_Glass.png"), rough=0.06)

ZC, W, H = 1.32, 1.0, 1.36
FW, FD = 0.04, 0.045                      # 프레임 폭·두께
Y0 = -0.03                                # 프레임 뒷면 (고정쇠 30 mm)
YC = Y0 - FD / 2
OW, OH = W + 2 * FW - 0.01, H + 2 * FW - 0.01
P = []
# 뒷판 (알루미늄 복합판) + 프레임 4변 (앞쪽이 둥근 스냅 프로파일) + 안쪽 립
P.append(B.box("p", (OW - 0.02, 0.006, OH - 0.02), (0, Y0 - 0.004, ZC), back, bevel=0.002))
for s in (-1, 1):
    P.append(B.box("p", (OW, FD, FW), (0, YC, ZC + s * (OH / 2 - FW / 2)), alu, bevel=0.009, segs=3))
    P.append(B.box("p", (FW, FD - 0.001, OH - 2 * FW + 0.004), (s * (OW / 2 - FW / 2), YC, ZC), alu, bevel=0.009,
                   segs=3))
    P.append(B.box("p", (OW - 2 * FW + 0.01, 0.01, 0.008), (0, Y0 - FD + 0.008, ZC + s * (OH / 2 - FW - 0.002)), alu,
                   bevel=0.002))
    P.append(B.box("p", (0.008, 0.01, OH - 2 * FW + 0.01), (s * (OW / 2 - FW - 0.002), Y0 - FD + 0.008, ZC), alu,
                   bevel=0.002))
for sx in (-1, 1):                         # 모서리 플라스틱 캡 + 뒤 고정쇠(유리 관통 볼트)
    for sz in (-1, 1):
        x, z = sx * (OW / 2 - 0.022), ZC + sz * (OH / 2 - 0.022)
        P.append(B.box("p", (0.05, FD + 0.004, 0.05), (x, YC, z), cap, bevel=0.008, segs=3))
        P.append(B.cyl("p", 0.013, -Y0 + 0.003, (sx * 0.42, 0, ZC + sz * 0.58), steel, n=16, bevel=0.002,
                       rot=(math.pi / 2, 0, 0)))
        P.append(B.cyl("p", 0.02, 0.004, (sx * 0.42, 0, ZC + sz * 0.58), steel, n=16, bevel=0.001,
                       rot=(math.pi / 2, 0, 0)))
for sx in (-1, 1):                         # 프레임 여는 스냅 홈 표시 (측면)
    for z in (-0.4, 0.0, 0.4):
        P.append(B.box("p", (0.004, 0.016, 0.03), (sx * (OW / 2 + 0.001), YC, ZC + z), cap, bevel=0.001))
body = B.join(P, A + "_Body")
k3d.uv_world(body, 1.0)  # 합친 메시의 빈(0) UV 면 -> 굽기 탄젠트가 깨져 노멀맵 얼룩. 전부 유효 UV 로
k3d.set_origin(body, (0, 0, 0))                    # 원점 = 바닥 (절차 재질의 높이 마스크도 이 기준)

# 노선도 면 (M_Dyn) + 아크릴 덮개 (월드 UV 2.5 m → 손자국은 0.9~1.6 m 높이)
mapf = B.quad("m", W, H, mp, (0, Y0 - 0.008, ZC))
mapf.name = A + "_Map"
cover = B.quad("c", W + 0.02, H + 0.02, gl, (0, Y0 - FD + 0.014, ZC))
cover.name = A + "_Cover"
k3d.uv_world(cover, 2.5)
d = lay["decals"]
L = [B.decal("l", lay, "frame_label", dec, (0.34, Y0 - FD - 0.0012, ZC - OH / 2 + FW / 2), w=0.1),
     B.decal("l", lay, "residue", dec, (-0.3, Y0 - FD + 0.0125, ZC - 0.47))]
decals = B.join(L, A + "_Decals")
B.parent([mapf, cover, decals], body)

B.bake_hidden(body, 1024, hide=(mapf, cover, decals), samples=48, ao_distance=0.15)
B.socket(A + "_Socket_LookTarget", (0, Y0 - FD, ZC), body)

notes = {
    "pivot": "바닥점, y=0 = 뒷면 고정쇠가 유리 앞면에 닿는 면. BusShelter_Socket_RouteMap 위치·회전에 그대로 놓는다.",
    "dynamic": [{"object": A + "_Map", "material": "M_Dyn_BusStopRouteMap_Map", "size_m": [W, H],
                 "texture_px": [1506, 2048], "uv": "UV 0..1, U→오른쪽 V→위 (정면 -Y 에서 볼 때)",
                 "placeholder": "Textures/BusStopRouteMap/T_BusStopRouteMap_Map.png (112/2413/7 노선선·정류장 이름 24 px≈16 mm, 주변 지도, 운행 시간, 요금 — 돋보기용 작은 글씨)",
                 "center_height_m": ZC,
                 "base_lens": [{"base": "Textures/BusStopRouteMap/T_BusStopRouteMap_Map_Base.png",
                                "lens": "Textures/BusStopRouteMap/T_BusStopRouteMap_Map.png"}],
                 "readable": "base = 돋보기 밖(흐림 9 px, 정류장 이름 못 읽음), lens = 돋보기 안(선명). 머티리얼 기본 텍스처는 lens"}],
    "shadows": {A + "_Cover": "Cast Shadows Off (투명 아크릴)"},
    "glass": "M_Glass_BusStopRouteMap_Cover: 아크릴 덮개 (먼지·손자국 = 텍스처 알파, 텍스처는 BusShelter 유리 공용)",
    "sockets": {A + "_Socket_LookTarget": "노선도 중심 (높이 1.32 m, 돋보기/시선 판정)"},
    "collider": "박스 1.07x0.075x1.43 (중심 높이 1.32, y -0.0375)",
}
fbx = k3d.export(A, "BusStop", [body], notes=notes)
k3d.preview(A, [body], views=((30, 10), (200, 10)))
B.shot(A, (-0.6, -2.6, 1.55), (0, 0, 1.3), 35, "fp")
B.shot(A, (-0.12, -0.7, 1.55), (0, 0, 1.45), 40, "close")

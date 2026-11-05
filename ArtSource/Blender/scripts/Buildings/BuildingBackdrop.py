"""BuildingBackdrop: 먼 배경용 15층 아파트 동 ('은행골 푸른마을 101동'). 정면/옆 그림 텍스처 + 얕은 슬래브 띠 + 옥탑.
프로토타입 Km 모듈 끝부분 (Jt 34~46 x 42~62 x 14 상자 + 아파트 정면 캔버스) 대체. 싸게: 굽기 없음."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bld, k3d

A = "BuildingBackdrop"
k3d.reset()
PL, CO = bld.T("Plaster"), bld.T("Concrete")
fac = bld.Atlas(A, "Facade", (2048, 2048))
NF, TOP, BASE = 15, 0.04, 0.06
front = fac.add(1400, 1700, kind="aptfront", floors=NF, bays=12, top=TOP, base=BASE, seed=4)
side = fac.add(505, 1700, kind="aptside", floors=NF, top=TOP, base=BASE, num="101", seed=9)
fm = bld.flat_img(f"M_{A}_Facade", fac.path, 0.85)

W, D, HT = 36.0, 13.0, 43.8
M = bld.Mesh()
M.quad(fm, (0, 0, HT / 2), (1, 0, 0), (0, 0, 1), W, HT, item=front)                 # 정면 (-Y)
M.quad(fm, (0, D, HT / 2), (-1, 0, 0), (0, 0, 1), W, HT, item=front)                # 뒤
M.quad(fm, (-W / 2, D / 2, HT / 2), (0, -1, 0), (0, 0, 1), D, HT, item=side)        # 왼쪽
M.quad(fm, (W / 2, D / 2, HT / 2), (0, 1, 0), (0, 0, 1), D, HT, item=side)          # 오른쪽
M.quad(CO, (0, D / 2, HT - 1.0), (1, 0, 0), (0, 1, 0), W - 0.4, D - 0.4)           # 옥상 (파라펫 1m 아래)
for c, r, w in (((0, 0.2, HT - 0.5), (-1, 0, 0), W - 0.4), ((0, D - 0.2, HT - 0.5), (1, 0, 0), W - 0.4),
                ((-W / 2 + 0.2, D / 2, HT - 0.5), (0, 1, 0), D - 0.4), ((W / 2 - 0.2, D / 2, HT - 0.5), (0, -1, 0), D - 0.4)):
    M.quad(PL, c, r, (0, 0, 1), w, 1.0)
for c, s in (((0, 0.1, HT + 0.04), (W + 0.1, 0.3, 0.08)), ((0, D - 0.1, HT + 0.04), (W + 0.1, 0.3, 0.08)),
             ((-W / 2 + 0.1, D / 2, HT + 0.04), (0.3, D - 0.5, 0.08)), ((W / 2 - 0.1, D / 2, HT + 0.04), (0.3, D - 0.5, 0.08))):
    M.box(PL, c, s, 0.01, 1)
# 층 슬래브 띠 (그림의 띠 위치와 맞춤): 정면만 15cm 돌출
fhn = (1 - TOP - BASE) / NF
for f in range(NF):
    z = HT * (1 - (TOP + (f + 0.91) * fhn))
    M.box(PL, (0, -0.075, z), (W + 0.04, 0.15, HT * fhn * 0.14), 0.01, 1)
M.box(PL, (0, -0.2, HT * BASE), (W + 0.1, 0.4, 0.25), 0.01, 1)                    # 1층 캐노피 띠
# 옥탑: 엘리베이터 기계실 2동 + 물탱크실
for x in (-9.0, 9.0):
    M.box(PL, (x, D / 2, HT - 1.0 + 1.9), (4.2, 4.6, 3.8), 0.02, 1)
    M.box(PL, (x, D / 2, HT - 1.0 + 3.86), (4.4, 4.8, 0.12), 0.01, 1)
M.box(PL, (0, D / 2 + 1.0, HT - 1.0 + 1.3), (7.0, 4.0, 2.6), 0.02, 1)

notes = ("먼 배경 아파트 동 (15층, 폭 36m 깊이 13m, 높이 43.8m + 옥탑 2.8m). 원점 = 정면 벽 아래 중앙, 정면 = Unity +Z. "
         "굽기 없음: 벽 = M_BuildingBackdrop_Facade (그림 1장, 정면/뒤 같은 그림, 옆 = '101 푸른마을'), 옥상·띠 = M_Tile_Buildings_*. "
         "60m 이상 떨어진 곳에 여러 개 두고 Y 회전/좌우 반전으로 변화를 줄 것.")
bld.draw([fac])
ob = M.to_object(A)
for p in ob.data.polygons:
    p.use_smooth = True
ob.data.set_sharp_from_angle(angle=0.8)
k3d.export(A, "Buildings", [ob], notes=notes)
paths = k3d.preview(A, [ob]) + bld.shot(A, [ob], (-20.0, -70.0, 1.55), (0.0, 0.0, 18.0), 35)
print("PREVIEWS", paths)

"""StoreOrderBoard: 주문번호 안내 모니터 ("준비 중 | 호출"). 정면 = -Y, 원점 = 베젤 하단 중앙.
화면은 M_Dyn (게임이 런타임에 텍스처 교체). 매장 배치: 블렌더 매장좌표 (-2.575, -0.9, 2.31) + Z회전 +90° / Unity (2.575, 2.31, 0.9), yaw -90°."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
k3d = S.k3d
k3d.reset()
S.textures()

SW, SH = 1.25, 0.56          # 화면 (프로토타입 크기)
B = 0.02                     # 베젤
OW, OH = SW + 2 * B, SH + 2 * B

m_bez = S.pbr("M_tmp_OBBezel", (0.018, 0.018, 0.02), 0.35, 0.0, var=0.05, grime=0.4, gdist=0.02, smudge=0.35,
              edge=0.5, edge_col=(0.12, 0.12, 0.12), bump=0.02, bscale=300)
m_back = S.pbr("M_tmp_OBBack", (0.03, 0.03, 0.032), 0.6, grime=0.5, bump=0.08, bscale=150)
m_steel = S.pbr("M_tmp_OBMount", (0.08, 0.08, 0.085), 0.45, 0.8, grime=0.5, edge=0.6, edge_col=(0.5, 0.5, 0.5))
m_led = S.pbr("M_tmp_OBLed", (0.02, 0.4, 0.05), 0.3, grime=0, bump=0, emission=(0.1, 1.0, 0.2), estr=3.0)

p = []
p.append(S.boxz("body", -OW / 2 + 0.004, OW / 2 - 0.004, -0.040, -0.008, 0.004, OH - 0.004, m_back, 0.006, 2))
y0, y1 = -0.045, -0.038
p.append(S.boxz("bt", -OW / 2, OW / 2, y0, y1, OH - B, OH, m_bez, 0.004, 2))
p.append(S.boxz("bb", -OW / 2, OW / 2, y0, y1, 0, B + 0.004, m_bez, 0.004, 2))
p.append(S.boxz("bl", -OW / 2, -OW / 2 + B, y0, y1, B, OH - B, m_bez, 0.004, 2))
p.append(S.boxz("br", OW / 2 - B, OW / 2, y0, y1, B, OH - B, m_bez, 0.004, 2))
p.append(S.boxz("rear", -0.42, 0.42, -0.008, 0.015, 0.1, OH - 0.1, m_back, 0.01, 2))
for x in (-0.2, 0.2):  # VESA 레일
    p.append(S.boxz("rail", x - 0.02, x + 0.02, 0.015, 0.03, 0.12, OH - 0.12, m_steel, 0.003, 2))
p.append(S.boxz("plate", -0.26, 0.26, 0.03, 0.045, 0.16, OH - 0.16, m_steel, 0.004, 2))
p.append(S.boxz("led", OW / 2 - 0.07, OW / 2 - 0.064, y0 - 0.0005, y0 + 0.002, 0.008, 0.012, m_led, 0, 0))
# 케이블 (아래로 늘어진 전원선 → 소핏 안으로)
p.append(S.cyl("cable", 0.004, 0.12, (0.3, 0.02, 0.06), m_back, 8, 0))
body = S.join(p, "StoreOrderBoard_Body")
S.set_origin(body, (0, 0, 0))
k3d.bake(body, 1024, samples=48, ao_distance=0.04)

# 무광(안티글레어) LCD. BaseColor 맵은 런타임 텍스처 교체(_BaseMap)를 위해 그대로 둔다
m_scr = S.img_mat("M_Dyn_StoreOrderBoard_Screen", S.tex("orderboard.png"), rough=0.75, emit=1.3)
scr = S.quad("StoreOrderBoard_Screen", SW, SH, (0, -0.0405, OH / 2), m_scr)
S.reparent(scr, body)
S.empty("StoreOrderBoard_Socket_LookTarget", (0, -0.05, OH / 2), body)

notes = ("주문번호 모니터. 정면=-Y, 원점=베젤 하단 중앙, 외곽 1.29x0.60x0.09m. "
         "매장 배치: Unity 위치 (2.575, 2.31, 0.9), Y회전 -90 (블렌더 매장좌표 (-2.575, -0.9, 2.31), Z회전 +90; 픽업대 위 소핏 앞면에 벽걸이). "
         "동적 화면: 오브젝트 StoreOrderBoard_Screen, 머티리얼 M_Dyn_StoreOrderBoard_Screen(무광 smoothness 0.25, BaseColor·Emission 같은 맵), 실제 크기 1.25x0.56m, "
         "기본 텍스처 2000x896px (왼쪽 '준비 중' 269/271/272/274, 오른쪽 '호출' 268), UV 0-1 이 화면 전체, U=오른쪽 V=위 (정면에서 볼 때). "
         "소켓 StoreOrderBoard_Socket_LookTarget = 화면 중앙 (NPC 가 바라보는 지점, 프로토 BOARD).")
k3d.export("StoreOrderBoard", "Store", [body], notes=notes)
k3d.preview("StoreOrderBoard", [body], views=((0, 5), (35, 15)))

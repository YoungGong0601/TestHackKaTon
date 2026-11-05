"""StoreMenuBoard: 카운터 위 백라이트 메뉴판 3장 (라이트박스). 정면 = -Y, 원점 = 프레임 하단 중앙.
매장 배치: 블렌더 매장좌표 (-2.575, 1.98, 2.28) + Z회전 +90° / Unity (2.575, 2.28, -1.98), yaw -90° (소핏 정면에 부착)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storelib as S
k3d = S.k3d
k3d.reset()
S.textures()

FW, FH, DEP = 1.32, 0.80, 0.09        # 프레임 외곽
VW, VH = 1.25, 0.72                    # 보이는 인쇄면 (프로토타입 크기)
BAR = (FW - VW) / 2
XS = (-1.4, 0.0, 1.4)

m_alu = S.pbr("M_tmp_MBAlu", (0.09, 0.09, 0.095), 0.35, 0.9, var=0.06, grime=0.5, gdist=0.03, edge=0.9,
              edge_col=(0.55, 0.55, 0.56), scratch=0.6, brush=0.12, bump=0.02)
m_house = S.pbr("M_tmp_MBHousing", (0.16, 0.16, 0.165), 0.55, 0.3, grime=0.6, streak=0.3, edge=0.4,
                edge_col=(0.4, 0.4, 0.4), bump=0.05)
m_screw = S.pbr("M_tmp_MBScrew", (0.6, 0.6, 0.6), 0.3, 1.0, grime=0.5)

parts = []
for i, cx in enumerate(XS):
    parts.append(S.boxz("h", cx - FW / 2 + 0.01, cx + FW / 2 - 0.01, -0.02, DEP / 2, 0.01, FH - 0.01, m_house, 0.006, 2))
    y0, y1 = -DEP / 2, -DEP / 2 + 0.03
    parts.append(S.boxz("ft", cx - FW / 2, cx + FW / 2, y0, y1, FH - BAR, FH, m_alu, 0.008, 3))
    parts.append(S.boxz("fb", cx - FW / 2, cx + FW / 2, y0, y1, 0, BAR, m_alu, 0.008, 3))
    parts.append(S.boxz("fl", cx - FW / 2, cx - FW / 2 + BAR, y0, y1, BAR, FH - BAR, m_alu, 0.008, 3))
    parts.append(S.boxz("fr", cx + FW / 2 - BAR, cx + FW / 2, y0, y1, BAR, FH - BAR, m_alu, 0.008, 3))
    for sx in (-1, 1):  # 고정 나사 (프레임 아래쪽)
        parts.append(S.cyl("sc", 0.006, 0.004, (cx + sx * (FW / 2 - 0.12), y0 + 0.012, -0.001), m_screw, 12, 0.001))
    # 전원선 (상단 → 천장)
    parts.append(S.cyl("cb", 0.0045, 0.03, (cx + FW / 2 - 0.08, 0.02, FH + 0.012), m_house, 8, 0))
frame = S.join(parts, "StoreMenuBoard_Frame")
S.set_origin(frame, (0, 0, 0))
k3d.bake(frame, 1024, samples=48, ao_distance=0.05)

# 인쇄면 (발광, 굽지 않음). 아크릴 커버는 천장등 반사가 메뉴를 하얗게 덮어 뺐다 (트랜스라이트 필름이 프레임 안에 바로 보이는 형태)
faces = []
for i, (cx, nm) in enumerate(zip(XS, ("menu_a.png", "menu_b.png", "menu_c.png"))):
    m = S.img_mat("M_StoreMenuBoard_Panel" + "ABC"[i], S.tex(nm), rough=0.75, emit=1.0)
    # 확산 필름: Base Color 를 검정으로 두고 발광만으로 보이게 (반사광이 인쇄면을 하얗게 덮지 않게)
    p = k3d.principled(m)
    m.node_tree.links.remove(p.inputs['Base Color'].links[0])
    p.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    q = S.quad("StoreMenuBoard_Panel" + "ABC"[i], VW, VH, (cx, -DEP / 2 + 0.024, FH / 2), m)
    faces.append(q)
for o in faces:
    S.reparent(o, frame)
S.empty("StoreMenuBoard_Socket_LookTarget", (0, -DEP / 2, FH / 2), frame)

notes = ("카운터 위 라이트박스 메뉴판 3장 (각 인쇄면 1.25x0.72m, 프레임 1.32x0.80x0.09m, 간격 1.4m). 정면=-Y, 원점=프레임 하단 중앙. "
         "매장 배치: Unity 위치 (2.575, 2.28, -1.98), Y회전 -90 (블렌더 매장좌표 (-2.575, 1.98, 2.28), Z회전 +90; 소핏 앞면 x=-2.62 에 등을 붙임). "
         "왼쪽(픽업 쪽)부터 A 대표 메뉴 / B 버거(불고기 = K-BBQ 스모키 비프 포함) / C 사이드·음료·디저트. "
         "인쇄면 머티리얼 M_StoreMenuBoard_PanelA/B/C = 2048x1180 발광 텍스처(정적, 굽지 않음, 발광 1.0, BaseColor 검정·smoothness 0.25 확산 필름). "
         "유리 커버는 없음(천장등 반사로 메뉴가 안 읽혀서 뺌). "
         "이름·가격은 프로토타입 키오스크 메뉴 데이터와 동일 (세트 = 단품 +2,000원).")
k3d.export("StoreMenuBoard", "Store", [frame], notes=notes)
k3d.preview("StoreMenuBoard", [frame], views=((0, 5), (30, 15)))

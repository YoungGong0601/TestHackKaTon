"""CarHatch: 한국 경차 해치백 (전장 3.595 / 전폭 1.595 / 전고 1.485 m, 휠베이스 2.40). 바랜 하늘색, 상표 없음.
뒷유리에 '초보운전' 스티커. 바퀴 4개는 차축 원점 자식 (로컬 X 축으로 회전)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _car
from _car import KN, V, k3d

A = "CarHatch"
L = 3.595

C = dict(
    name=A, L=L, W=1.595, nu=26,
    axles=(0.70, 3.10), tire_r=0.277, rim_r=0.178, tire_w=0.165, track=1.40, arch_r=0.315,
    tire_img="tire_hatch.png", plate_img="plate_hatch.png", spokes=8, double_spoke=False, alloy=(0.36, 0.37, 0.39),
    top=[(0.00, 0.66), (0.08, 0.73), (0.30, 0.79), (0.55, 0.835), (0.78, 0.88), (0.95, 0.975), (1.20, 1.16),
         (1.45, 1.335), (1.65, 1.44), (1.90, 1.48), (2.40, 1.487), (2.90, 1.478), (3.18, 1.462), (3.28, 1.44),
         (3.38, 1.29), (3.47, 1.07), (3.53, 1.01), (3.595, 0.96)],
    belt=[(0.0, 0.80), (0.78, 0.90), (2.0, 0.955), (3.2, 1.0), (3.595, 1.0)],
    bot=[(0.0, 0.20), (0.4, 0.19), (1.8, 0.18), (3.2, 0.21), (3.595, 0.33)],
    half=[(0.0, 0.70), (0.08, 0.75), (0.25, 0.785), (0.6, 0.797), (2.0, 0.7975), (3.2, 0.795), (3.45, 0.78),
          (3.595, 0.74)],
    sh=[(0.0, 0.48), (0.35, 0.60), (1.0, 0.68), (3.0, 0.72), (3.595, 0.66)],
    sweep=(0.08, 0.03), bulge=(0.05, 0.03), round=(0.07, 0.06), crown=0.03, lean=0.34,
    paint=(0.171, 0.274, 0.367), paint_rough=0.24, faded=(0.25, 0.33, 0.40), dirt=1.2,
    regions=[
        dict(t0=0.73, t1=0.82, v0=KN[5], v1=1.01, depth=0.005, mat="trim", seal="trim"),  # 카울 (9 cm)
        dict(t0=0.82, t1=1.63, v0=KN[5] + 0.022, v1=1.01, depth=0.010, mat="glass", seal="rubber",
             band_mat="gloss", band=(0.005, 0.018)),  # 앞유리
        dict(t0=3.30, t1=3.465, v0=KN[5] + 0.022, v1=1.01, depth=0.010, mat="tint", seal="rubber",
             band_mat="gloss", band=(0.004, 0.02)),  # 해치 유리
        dict(t0=1.05, t1=1.95, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="glass", seal="rubber",
             band_mat="gloss", band=(0.003, 0.008)),  # 앞문 유리
        dict(t0=1.95, t1=2.05, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="gloss", seal="rubber"),  # B필러
        dict(t0=2.05, t1=2.78, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="tint", seal="rubber",
             band_mat="gloss", band=(0.003, 0.008)),  # 뒷문 유리
        dict(t0=2.86, t1=3.14, v0=KN[4] + 0.03, v1=KN[5] - 0.03, depth=0.010, mat="tint", seal="rubber"),  # 쪽유리
        dict(t0=1.05, t1=2.78, v0=KN[4] + 0.003, v1=KN[4] + 0.014, mat="trim"),  # 벨트 고무 몰딩
    ],
    cuts=[(1.04, 0.24, 0.93), (2.00, 0.24, 0.96), (2.76, 0.30, 0.98)],
    door_bottom=(1.04, 2.76, 0.255),
    hood=(0.0, 0.73, 0.60), hood_z=0.66,
    bumper_seams=[(0.25, 0.60), (3.40, 0.70)], sill_z=0.20,
    trunk=(3.27, 0.66, 0.62), trunk_front=1.40,
    fuel=(2.95, 0.80),
    # 세단과 다른 얼굴: 바깥이 올라간 둥근 모서리 램프 + 큰 원형 반사경, 얇은 위 그릴 슬롯, 큰 아래 흡기구
    front=dict(lamp=(0.30, 0.60, 0.45, 0.585), lamp_shear=0.15, lamp_bev=0.02, round_lamp=True,
               grille=(0.25, 0.50, 0.54), grille_mat="gloss", grille_trim="gloss",
               intake=(0.46, 0.25, 0.40), fog=(0.50, 0.61, 0.27, 0.32), plate_z=0.37),
    rear=dict(lamp=(0.50, 0.69, 0.62, 0.88), bar=False, diffuser=(0.40, 0.46), diff_x=0.55, plate_z=0.72,
              exhaust=(0.40, (-1,))),
    mirror=(1.06, 0.97), handles=(1.80, 2.58), handle_z=0.86, handle_mat="paint",
    wiper_t=0.76, antenna_t=3.10,
    cabin=dict(t0=0.80, t1=3.35, belt=0.93, dash=0.90, dash_z=0.86, seat_f=1.75, seat_r=2.65, shelf=(3.05, 3.40, 0.95)),
    stickers=[dict(id="Beginner", img="sticker_beginner.png", w=0.30, h=0.15, fn=_car.sticker_loc(3.40, KN[5] + 0.12))],
    sockets={"Driver": (0.36, 1.77, 0.55), "Exhaust": (-0.40, 3.64, 0.42), "Front": (0, -0.05, 0.5),
             "Rear": (0, 3.64, 0.7)},
    variants={"White": ((0.78, 0.78, 0.76), (0.80, 0.78, 0.72)), "Gray": ((0.16, 0.165, 0.17), (0.22, 0.22, 0.215))},
)

if __name__ == "__main__":
    body, wheels = _car.build(C)
    if _car.FAST:
        k3d.preview(A, [body], views=((35, 18), (215, 12), (90, 0)), tag="wip")
        raise SystemExit
    notes = ("경차 해치백. 정면 -Y(Unity +Z). 원점 바닥 중앙. 바퀴 CarHatch_Wheel_FL/FR/RL/RR: 원점=차축, 로컬 X 축 회전 "
             "(좌측 바퀴는 메시가 180° 돌려져 있어 축은 동일). M_Glass_CarHatch_Window/Tint/Lens. "
             "뒷유리 안쪽 '초보운전' 스티커(M_CarHatch_Sticker_Beginner, 알파 클립). 번호판 '45나 7019'(가상). "
             "미등은 아주 약한 발광. 도장 변형 머티리얼: M_CarHatch_Body_White / M_CarHatch_Body_Gray "
             "(T_CarHatch_Body_BaseColor_<변형>.jpg, 나머지 맵 공유) -> CarHatch_Body 0번 슬롯 교체. "
             "소켓: Driver, Exhaust, Front, Rear.")
    _car.export(C, body, notes)
    k3d.preview(A, [body])
    k3d.preview(A, [body], views=((62, 9),), lens=35, tag="fp")

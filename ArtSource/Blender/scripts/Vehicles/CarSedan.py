"""CarSedan: 한국 준중형 세단 (전장 4.65 / 전폭 1.825 / 전고 1.42 m, 휠베이스 2.72). 펄 화이트, 상표 없음.
지나가는 차량·주차 차량용. 바퀴 4개는 차축 원점 자식 (로컬 X 축으로 회전)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _car
from _car import KN, V, k3d

A = "CarSedan"
L = 4.65


C = dict(
    name=A, L=L, W=1.825,
    axles=(0.92, 3.64), tire_r=0.316, rim_r=0.203, tire_w=0.205, track=1.56, arch_r=0.36,
    tire_img="tire_sedan.png", plate_img="plate_sedan.png", spokes=5, double_spoke=True,
    top=[(0.00, 0.70), (0.10, 0.765), (0.40, 0.81), (0.80, 0.855), (1.15, 0.895), (1.28, 0.925), (1.45, 1.01),
         (1.70, 1.155), (1.95, 1.29), (2.20, 1.385), (2.50, 1.42), (2.85, 1.415), (3.10, 1.38), (3.35, 1.29),
         (3.60, 1.17), (3.85, 1.075), (4.00, 1.06), (4.35, 1.055), (4.55, 1.035), (4.65, 0.97)],
    belt=[(0.0, 0.86), (1.28, 0.94), (2.4, 0.975), (3.6, 1.02), (4.0, 1.04), (4.65, 1.04)],
    bot=[(0.0, 0.22), (0.5, 0.20), (2.3, 0.19), (4.1, 0.21), (4.65, 0.31)],
    half=[(0.0, 0.79), (0.10, 0.855), (0.30, 0.895), (0.70, 0.91), (2.3, 0.9125), (3.9, 0.91), (4.35, 0.895),
          (4.55, 0.86), (4.65, 0.80)],
    sh=[(0.0, 0.50), (0.4, 0.64), (1.3, 0.72), (3.3, 0.74), (4.3, 0.74), (4.65, 0.62)],
    sweep=(0.15, 0.06), bulge=(0.06, 0.04), round=(0.07, 0.06), crown=0.03, lean=0.40,
    paint=(0.80, 0.80, 0.78), paint_rough=0.16, faded=(0.80, 0.78, 0.72), dirt=1.0,
    regions=[
        dict(t0=1.21, t1=1.31, v0=KN[5], v1=1.01, depth=0.005, mat="trim", seal="trim"),  # 카울 (10 cm)
        dict(t0=1.31, t1=2.17, v0=KN[5] + 0.022, v1=1.01, depth=0.010, mat="glass", seal="rubber",
             band_mat="gloss", band=(0.004, 0.018)),  # 앞유리 (검은 세라믹 띠)
        dict(t0=3.08, t1=3.84, v0=KN[5] + 0.022, v1=1.01, depth=0.010, mat="tint", seal="rubber",
             band_mat="gloss", band=(0.004, 0.02)),  # 뒷유리
        dict(t0=1.50, t1=2.45, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="glass", seal="rubber",
             band_mat="gloss", band=(0.003, 0.008)),  # 앞문 유리
        dict(t0=2.45, t1=2.56, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="gloss", seal="rubber"),  # B필러
        dict(t0=2.56, t1=3.30, v0=KN[4] + 0.014, v1=KN[5] - 0.018, depth=0.012, mat="tint", seal="rubber",
             band_mat="gloss", band=(0.003, 0.008)),  # 뒷문 유리
        dict(t0=1.50, t1=3.30, v0=KN[4] + 0.003, v1=KN[4] + 0.014, mat="chrome"),  # 벨트 크롬 몰딩
    ],
    cuts=[(1.38, 0.24, 0.985), (2.50, 0.24, 0.99), (3.22, 0.40, 1.0)],
    door_bottom=(1.38, 3.22, 0.27),
    hood=(0.0, 1.21, 0.70), hood_z=0.70,
    bumper_seams=[(0.30, 0.66), (4.35, 0.78)], sill_z=0.22,
    trunk=(3.90, 0.70, 0.72), trunk_front=1.0,
    fuel=(3.95, 0.88),
    front=dict(lamp=(0.36, 0.70, 0.52, 0.615), grille=(0.36, 0.47, 0.60), intake=(0.48, 0.255, 0.345),
               fog=(0.55, 0.66, 0.29, 0.345), plate_z=0.39),
    rear=dict(lamp=(0.42, 0.72, 0.745, 0.87), bar=True, diffuser=(0.37, 0.43), diff_x=0.62, plate_z=0.60,
              exhaust=(0.45, (-1,))),
    mirror=(1.52, 1.00), handles=(2.25, 3.02), handle_z=0.885, handle_mat="chrome",
    wiper_t=1.25, antenna_t=3.02,
    cabin=dict(t0=1.30, t1=3.85, belt=0.95, dash=1.38, dash_z=0.92, seat_f=2.30, seat_r=3.15, shelf=(3.55, 3.85, 0.99)),
    stickers=[dict(id="Parking", img="sticker_parking.png", w=0.10, h=0.075, fn=_car.sticker_loc(1.45, KN[5] + 0.09))],
    sockets={"Driver": (0.36, 2.32, 0.55), "Exhaust": (-0.45, 4.70, 0.37), "Front": (0, -0.05, 0.55),
             "Rear": (0, 4.70, 0.65)},
    # 도장 변형 (같은 UV 로 BaseColor 만 다시 굽는다): (색, 햇빛 바랜 색) linear
    variants={"Silver": ((0.40, 0.41, 0.42), (0.47, 0.47, 0.46)), "DarkGray": ((0.035, 0.037, 0.04), (0.075, 0.075, 0.074))},
)

if __name__ == "__main__":
    body, wheels = _car.build(C)
    notes = ("세단. 정면 -Y(Unity +Z). 원점 바닥 중앙. 바퀴 CarSedan_Wheel_FL/FR/RL/RR: 원점=차축, 로컬 X 축 회전 "
             "(전진 시 +X 기준 같은 부호, 좌측 바퀴는 메시가 180° 돌려져 있어 축은 동일). "
             "M_Glass_CarSedan_Window(앞·앞문, 반투명)/Tint(뒷유리·뒷문 진한 썬팅)/Lens(전조등 렌즈). "
             "전조등 DRL 은 구운 Emission, 미등은 아주 약하게(꺼진 상태에 가깝게). 번호판 '123가 4568'(가상) M_CarSedan_Plate. "
             "도장 변형 머티리얼: M_CarSedan_Body_Silver / M_CarSedan_Body_DarkGray (T_CarSedan_Body_BaseColor_<변형>.jpg, 나머지 맵 공유) "
             "-> 인스턴스의 CarSedan_Body 0번 슬롯을 바꾸면 은색·짙은 회색 차. "
             "소켓: Driver(운전석 앉는 점), Exhaust(배기 연기), Front/Rear(소리·충돌 기준).")
    if _car.FAST:
        k3d.preview(A, [body], views=((35, 18), (215, 12), (90, 0)), tag="wip")
        raise SystemExit
    _car.export(C, body, notes)
    k3d.preview(A, [body])
    k3d.preview(A, [body], views=((62, 9),), lens=35, tag="fp")

"""모델링목록.md 표를 옮긴 합격 기준. 좌표는 친구 프리팹의 Unity 로컬 (x, y, z).

- 친구 프레임 = 프로토타입 three 좌표에서 z 만 뒤집은 것: (x3, y3, -z3).
- size: 가로x세로x깊이(m). tol: 축별 허용 비율(기본 0.10), None 이면 그 축은 검사하지 않음.
- pivot: bottom(바닥 중앙) · center(범위 중심) · none(range 로 직접 지정).
- range: {'x': (min, max)} 실제 메시 범위. front: 앞면이 향하는 축 (FrontMark 로 확인).
- target: 프리팹 안에서 모델을 넣을 자리.
"""
LOOKS = ["OfficeMan", "Ajumma", "StudentWoman", "StudentMan", "YoungWoman", "OldMan", "SuitMan", "Youth", "Staff"]

ROWS = {
    # 손에 든 물건 (원점 = 물건 중심)
    "PH_Hand__Memo":    dict(prefab="PH_Hand", target="Hand_Memo/Visual", size=(0.165, 0.21, 0.002), tol={"z": 4.0}, pivot="center", front="-Z"),
    # 돋보기 원점은 렌즈 중심이다 (HandRig: lens.position, Lens_Radius 0.06)
    "PH_Hand__Lens":    dict(prefab="PH_Hand", target="Hand_Lens/Visual", size=(0.13, None, 0.03), tol={"z": 0.5}, pivot="none", front="-Z", range={"x": (-0.075, 0.075), "y": (-0.235, 0.075), "z": (-0.02, 0.02)}),
    "PH_Hand__Card":    dict(prefab="PH_Hand", target="Hand_Card/Visual", size=(0.085, 0.054, 0.002), tol={"z": 1.0}, pivot="center", front="-Z"),
    "PH_Hand__Pointer": dict(prefab="PH_Hand", target="Hand_Pointer/Visual", size=(0.07, 0.175, 0.03), tol={"x": 0.7, "z": 2.0}, pivot="center", front="-Z",
                             range={"y": (-0.09, 0.095)}),
    "PH_ReceiptSheet":  dict(prefab=None, target="Store 씬 Receipt_View/Sheet", size=(0.105, 0.2, 0.002), tol={"z": 1.5}, pivot="center", front="-Z"),
    # 집
    "PH_ShoeRack__Shoes": dict(prefab="PH_ShoeRack", target="Shoes/Visual", size=(0.24, 0.09, 0.27), pivot="bottom"),
    "PH_Cane":            dict(prefab="PH_Cane", target="Visual", size=(0.03, 0.92, 0.03), tol={"x": None, "z": None}, pivot="none", range={"y": (-0.01, 0.95)}),
    "PH_Door_Home__Frame": dict(prefab="PH_Door_Home", target="Visual", size=(1.08, 2.12, 0.12), pivot="bottom", front="-Z"),
    "PH_Door_Home__Leaf":  dict(prefab="PH_Door_Home", target="Hinge/Visual", size=(0.92, None, None), pivot="none", front="-Z", range={"x": (-0.03, 0.95), "y": (-0.01, 2.12)}),
    "PH_ShoeCabinet":     dict(prefab="PH_ShoeCabinet", target="Visual", size=(0.36, 1.06, 1.58), pivot="bottom"),
    "PH_Bulb":            dict(prefab="PH_Bulb", target="Visual", size=(0.08, 0.38, 0.08), pivot="none", range={"y": (-0.01, 0.4)}),
    # 거리
    "PH_BusShelter":  dict(prefab="PH_BusShelter", target="Visual", size=(7.1, 2.765, 2.85), pivot="bottom", front="+Z"),
    "PH_BIS":         dict(prefab="PH_BIS", target="Visual", size=(0.16, 3.125, 1.66), pivot="bottom"),
    "PH_BusStopSign": dict(prefab="PH_BusStopSign", target="Visual", size=(0.62, 3.07, 0.07), tol={"z": 2.0}, pivot="bottom"),
    "PH_Bus__Body":   dict(prefab="PH_Bus", target="Visual", size=(10.9, 3.05, 2.57), pivot="bottom", front="+X"),
    "PH_Bus__DoorA":  dict(prefab="PH_Bus", target="DoorLeafA/Visual", size=(None, None, None), pivot="none", range={"x": (-0.33, 0.33), "y": (-1.2, 1.15), "z": (-0.05, 0.09)}),
    "PH_Bus__DoorB":  dict(prefab="PH_Bus", target="DoorLeafB/Visual", size=(None, None, None), pivot="none", range={"x": (-0.33, 0.33), "y": (-1.2, 1.15), "z": (-0.05, 0.09)}),
    # 원점 = 프리팹 원점이라 실내 바닥이 y 0.32 이다. 크기는 회색 메시 전체 범위
    "PH_BusInterior": dict(prefab="PH_BusInterior", target="Visual", size=(10.98, 2.53, 2.5), pivot="none", front="+X", range={"x": (-5.5, 5.5), "y": (0.21, 2.76), "z": (-1.26, 1.26)}),
    "PH_Rail":        dict(prefab="PH_Rail", target="Visual", size=(85.4, 0.92, 0.06), tol={"z": 1.0}, pivot="bottom"),
    "PH_Curb":        dict(prefab="PH_Curb", target="Visual", size=(120.0, 0.16, 0.26), pivot="bottom"),
    # 매장 앞
    "PH_Storefront":  dict(prefab="PH_Storefront", target="Visual", size=(11.57, 4.3, 0.39), pivot="none", front="-Z", range={"x": (-6.05, 5.55), "y": (-0.01, 4.35)}),
    "PH_Door_Glass__Leaf": dict(prefab="PH_Door_Glass", target="DoorPivot/Visual", size=(0.93, 2.28, 0.2), tol={"z": 0.5}, pivot="none", front="-Z", range={"x": (-0.01, 0.94), "y": (-0.01, 2.32), "z": (-0.11, 0.11)}),
    # 매장 안
    "PH_Kiosk__Body":   dict(prefab="PH_Kiosk", target="Visual", size=(None, 1.9, 0.16), tol={"z": 0.25}, pivot="none", front="-Z", range={"x": (-0.6, 0.35), "y": (-0.01, 1.95), "z": (-0.14, 0.075)}),
    # Cover 는 Z 로 180도 돌아 있다. 로컬 +X 가 프리팹 -X 이고 경첩이 원점이다
    "PH_Kiosk__Cover":  dict(prefab="PH_Kiosk", target="Cover/Hinge/Visual", size=(0.231, 0.17, None), pivot="none", range={"x": (-0.01, 0.245), "y": (-0.095, 0.095), "z": (-0.03, 0.012)}),
    "PH_Kiosk__WingL":  dict(prefab="PH_Kiosk", target="Wing_L/Visual", size=(0.25, 0.56, None), pivot="center"),
    "PH_Kiosk__WingR":  dict(prefab="PH_Kiosk", target="Wing_R/Visual", size=(0.2, 0.3, None), pivot="center"),
    "PH_Kiosk__Card":   dict(prefab="PH_Kiosk", target="Card/Visual", size=(0.085, 0.054, 0.002), tol={"z": 1.0}, pivot="center"),
    "PH_Kiosk_Broken":  dict(prefab="PH_Kiosk_Broken", target="Visual", size=(0.63, 1.9, 0.16), tol={"z": 0.25}, pivot="bottom", front="-Z"),
    "PH_Table":       dict(prefab="PH_Table", target="Visual", size=(0.72, 0.74, 0.72), pivot="bottom"),
    "PH_Seat":        dict(prefab="PH_Seat", target="Visual", size=(0.42, 0.46, 0.42), tol={"y": None, "x": 0.2, "z": 0.2}, pivot="bottom"),
    "PH_Booth":       dict(prefab="PH_Booth", target="Visual", size=(1.18, 0.74, 2.2), pivot="bottom"),
    "PH_Counter":     dict(prefab="PH_Counter", target="Visual", size=(0.76, 0.99, 5.94), pivot="none", front="+X", range={"x": (-0.8, 0.03), "y": (-0.01, 1.05), "z": (-3.0, 3.0)}),
    "PH_Bulkhead":    dict(prefab="PH_Bulkhead", target="Visual", size=(0.24, 0.9, 5.9), pivot="bottom"),
    "PH_KitchenBench": dict(prefab="PH_KitchenBench", target="Visual", size=(0.75, 0.92, 5.3), pivot="bottom"),
    "PH_Fryer":       dict(prefab="PH_Fryer", target="Visual", size=(0.64, 0.96, 1.3), pivot="bottom"),
    "PH_Hood":        dict(prefab="PH_Hood", target="Visual", size=(1.05, 0.42, 2.6), pivot="bottom"),
    "PH_PickupBoard": dict(prefab="PH_PickupBoard", target="Visual", size=(0.08, 0.62, 1.31), tol={"x": 0.3}, pivot="center", front="+X"),
    "PH_PickupStand": dict(prefab="PH_PickupStand", target="Visual", size=(0.5, 0.1, 0.7), pivot="bottom"),
    "PH_Bag":         dict(prefab="PH_Bag", target="Visual", size=(0.25, 0.3, 0.14), pivot="bottom"),
    "PH_Bag__Cup":    dict(prefab="PH_Bag", target="Cup/Visual", size=(0.08, None, 0.08), tol={"x": 0.25, "z": 0.25}, pivot="none", range={"y": (-0.08, 0.2)}),
    "PH_NPC__Bag":    dict(prefab="PH_NPC", target="BagAnchor/Visual", size=(0.25, 0.3, 0.14), pivot="center"),
    "PH_Car":         dict(prefab="PH_Car", target="Visual", size=(4.4, 1.45, 1.85), pivot="bottom", front="+X"),
    "PH_Scooter":     dict(prefab="PH_Scooter", target="Visual", size=(1.75, 1.72, 0.6), tol={"z": 0.4}, pivot="bottom", front="+X"),
}
# 모델 없이 회색 메시만 지우는 자리. 우리 모델이 그 자리를 이미 그린다.
CLEAR = [("PH_Kiosk", "Spot_Call/Visual"), ("PH_Kiosk", "Slot_ic/Visual"), ("PH_Kiosk", "Slot_receipt/Visual"), ("PH_Kiosk", "Slot_barcode/Visual")]

for _l in LOOKS:  # 14명이 한 프리팹을 쓴다. 모습마다 몸과 머리를 나눈다.
    ROWS[f"PH_NPC__{_l}_Body"] = dict(prefab="PH_NPC", target="ReactPivot/Visual", size=(0.46, 1.71, 0.34), tol={"x": 0.45, "z": 0.45}, pivot="bottom", front="+Z", look=_l)
    ROWS[f"PH_NPC__{_l}_Head"] = dict(prefab="PH_NPC", target="HeadPivot/Visual", size=(None, None, None), pivot="none", range={"y": (-0.2, 0.2)}, look=_l)

# 검은 장우산 (접혀서 끈으로 묶임). 원점 = 꼭지(땅에 닿는 끝) 바닥, 손잡이 갈고리는 +X 쪽.
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh
from mathutils import Vector

A = "HomeUmbrella"
d2r = math.radians


def build(asset, fab_col, handle_col, H=0.86, seed=0):
    k3d.reset()
    fabric = hk.P("M_tmp_fabric", fab_col, 0.5, var=0.08, vs=8, rv=0.1, grime=0.7, gd=0.012,
                  gcol=tuple(c * 0.3 for c in hk.srgb(fab_col)), bump=0.35, bs=2200, bk='cloth', bd=0.0002,
                  dust=0.5, dz=0.12, dcol="#4a4640", smudge=0.15)
    wood = hk.P("M_tmp_handle", handle_col, 0.28, var=0.12, vs=14, rv=0.08, grime=0.5, gd=0.006, gcol="#120a06",
                edge=0.6, ed=0.003, ecol="#7a5236", erough=0.45, bump=0.08, bs=300, smudge=0.35,
                extra=lambda g, b, r, o: (g.mix(g.math('MULTIPLY', g.ramp(g.wave(260, o, 'X', 7, 3), 0.5, 0.95), 0.45), b,
                                                tuple(c * 0.45 for c in hk.srgb(handle_col))), r))
    steel = hk.P("M_tmp_shaft", "#2a2a2c", 0.32, 0.8, var=0.05, vs=40, grime=0.5, gd=0.005, edge=0.5, ed=0.0015,
                 ecol="#8a8a8c", smudge=0.2)
    chrome = hk.P("M_tmp_chrome", "#c8c8c8", 0.18, 1.0, var=0.05, grime=0.6, gd=0.004, gcol="#3a3530")
    plastic = hk.P("M_tmp_plastic", "#111112", 0.45, var=0.05, vs=30, grime=0.4, gd=0.004, edge=0.4, ed=0.0012,
                   ecol="#4a4a4c", dust=0.5, dz=0.05)
    sc = H / 0.86
    parts = []
    # 꼭지 (쇠 + 플라스틱 캡)
    parts.append(hk.lathe(asset + "_Tip", [(0, 0), (0.0035, 0.0005), (0.0042, 0.006), (0.0052, 0.03), (0.0085, 0.032),
                                           (0.0092, 0.042), (0.0075, 0.05), (0.004, 0.052)], 20, chrome))
    # 접힌 천: 8폭 주름 + 살짝 비틀림, 끈 자리는 조여짐
    prof = [(0.004, 0.048), (0.0085, 0.056), (0.013, 0.08), (0.018, 0.12), (0.023, 0.18), (0.027, 0.25), (0.03, 0.32),
            (0.0315, 0.37), (0.027, 0.395), (0.027, 0.42), (0.032, 0.445), (0.0345, 0.5), (0.0355, 0.55), (0.034, 0.585),
            (0.031, 0.605), (0.026, 0.618), (0.017, 0.626), (0.008, 0.63)]
    prof = [(r * 1.0, z * sc) for r, z in prof]
    import random
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]

    def fold(th, z, r):
        tw = 2.2 * z + 0.25 * math.sin(z * 9 + ph[0])
        f = 0.5 + 0.5 * math.cos(8 * th + tw)
        lob = 0.8 + 0.2 * f ** 0.45
        if z > 0.59 * sc:  # 끝단: 폭 사이 천이 삐져나옴
            lob += 0.12 * f ** 2
        wob = 1 + 0.03 * math.sin(th * 3 + ph[1] + z * 5) + 0.02 * math.sin(th * 5 + ph[2])
        return r * lob * wob
    can = hk.lathe(asset + "_Canopy", prof, 64, fabric, rmod=fold)
    parts.append(can)
    # 묶음 끈 + 똑딱이
    zs = 0.407 * sc
    band = hk.lathe(asset + "_Strap", [(0.0285, zs - 0.012), (0.0305, zs - 0.0115), (0.0308, zs + 0.0115), (0.0288, zs + 0.012)],
                    40, fabric)
    hk.finish(band, 0.0008, 1, smooth=True)
    parts.append(band)
    flap = hk.box(asset + "_StrapTab", (0.022, 0.003, 0.024), (0.0, -0.0315, zs), mat=fabric, bev=0.0012)
    parts.append(flap)
    parts.append(hk.cyl(asset + "_Snap", 0.0045, 0.002, (0.0, -0.033, zs), rot=(d2r(90), 0, 0), mat=chrome, n=16, bev=0.0006))
    # 살 끝 (8개, 천 끝단 안쪽)
    for k in range(8):
        a = (k + 0.5) * math.pi / 4 + 2.2 * 0.62
        r = 0.022
        parts.append(hk.cyl(asset + "_RibTip", 0.0022, 0.008, (r * math.cos(a), r * math.sin(a), 0.613 * sc), mat=chrome,
                            n=8, r2=0.0016, bev=0.0004))
    # 대 (쇠) + 런너 + 스프링 버튼
    z_top = 0.765 * sc
    parts.append(hk.cyl(asset + "_Shaft", 0.0052, z_top - 0.6 * sc, (0, 0, 0.6 * sc), mat=steel, n=16, bev=0))
    parts.append(hk.lathe(asset + "_Runner", [(0.0052, 0.632 * sc), (0.0105, 0.636 * sc), (0.0115, 0.66 * sc),
                                              (0.0085, 0.69 * sc), (0.0056, 0.694 * sc)], 24, plastic))
    parts.append(hk.box(asset + "_Button", (0.004, 0.006, 0.01), (0.0, -0.0058, 0.72 * sc), mat=chrome, bev=0.0015))
    # 손잡이: 쇠 고리 + 나무 갈고리
    parts.append(hk.cyl(asset + "_Ferrule", 0.0105, 0.012, (0, 0, z_top - 0.004), mat=chrome, n=24, bev=0.001))
    R = 0.032
    zc = H - R - 0.0125
    pts = [(0, 0, z_top)]
    for k in range(6):
        pts.append((0, 0, z_top + (zc - z_top) * (k + 1) / 6))
    for k in range(1, 19):
        a = math.pi * k / 18
        pts.append((R - R * math.cos(a), 0, zc + R * math.sin(a)))
    for k in range(1, 4):
        pts.append((2 * R + 0.0015 * k, 0, zc - 0.012 * k))
    hd = hk.tube(asset + "_Handle", pts, 0.0122, 14, wood, rfun=lambda t: 1.0 if t < 0.82 else 1.0 - (t - 0.82) * 1.2)
    parts.append(hd)
    parts.append(hk.cyl(asset + "_HandleCap", 0.0098, 0.004, (2 * R + 0.0045, 0, zc - 0.038), rot=(0, d2r(8), 0),
                        mat=plastic, n=16, bev=0.0012))
    obj = hk.join(parts, asset)
    k3d.set_origin(obj, (0, 0, 0))
    k3d.bake(obj, 1024, ao_distance=0.02)
    hk.socket(asset + "_Socket_Grip", (R, 0, H - 0.01), obj)
    hk.socket(asset + "_Socket_Tip", (0, 0, 0), obj)
    return obj


obj = build(A, "#151517", "#3a2216", 0.86, 0)
notes = ("검은 장우산(접힘, 끈 묶음) 높이 0.86m. 원점 = 꼭지 끝(바닥), 갈고리 손잡이는 +X 쪽으로 휨. "
         "프로토타입: 우산꽂이 안 three(S-.13, A+.02, R+.22) 기울임 → HomeEntry_Socket_UmbrellaBlack 에 원점을 맞춤(회전 포함). "
         "Socket_Grip = 갈고리 잡는 점, Socket_Tip = 꼭지.")
k3d.export(A, hk.CAT, [obj], notes=notes)
k3d.preview(A, [obj])
L_ = [('AREA', (0.6, -0.8, 1.6), 120, (1, 0.95, 0.9), 1.5), ('POINT', (-0.8, -0.5, 0.6), 20, (0.9, 0.95, 1), 0.3)]
hk.shot(hk.PREV + "/HomeUmbrella_full.png", (1.0, -1.7, 0.55), (0.02, 0, 0.44), lens=40, res=(900, 1200), lights=L_, world=0.4)
hk.shot(hk.PREV + "/HomeUmbrella_grip.png", (0.2, -0.3, 0.86), (0.02, 0, 0.75), lens=50, lights=L_, world=0.4)
# 두 번째 우산 (팥죽색, 약간 짧음) — 프로토타입의 두 번째 우산
B = "HomeUmbrellaRed"
obj = build(B, "#5e1f1d", "#2a2420", 0.84, 3)
k3d.export(B, hk.CAT, [obj], notes="팥죽색 장우산 0.84m (우산꽂이 두 번째 우산, 꼭지 끝 높이 three A+.02). 원점 = 꼭지 끝. "
                                    "HomeEntry_Socket_UmbrellaRed 에 원점을 맞춤(회전 포함, 손잡이 -X). Socket_Grip, Socket_Tip.")
k3d.preview(B, [obj])

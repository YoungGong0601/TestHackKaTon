# 현관 철제 문틀 + 화강석 문턱 + 경첩(틀 쪽) + 스트라이크 + 고무 개스킷 + 도어클로저 브래킷
# 원점 = 문틀 바닥 중앙(현관 바닥 높이), -Y = 복도(바깥), +Y = 집 안쪽. 벽 두께 0.12 중앙에 놓인다.
import sys, math
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh

k3d.reset()
A = "HomeDoorFrame"
d2r = math.radians
OW, OH = 0.46, 2.04          # 열린 폭 절반, 높이 (턱 기준)
FW, D = 0.06, 0.16           # 문틀 면 폭, 깊이
YS = -0.015                  # 문닫힘 턱(스톱) 바깥면 y
paint = hk.P("M_tmp_fpaint", "#685749", 0.45, var=0.05, vs=3, rv=0.05, grime=0.6, gd=0.03, gcol="#2a221c",
             edge=0.8, ed=0.003, ecol="#a39a8c", erough=0.65, bump=0.04, bs=140, bd=0.0015, dust=0.6, dz=0.3,
             dcol="#3b332b", smudge=0.15)
stone = hk.P("M_tmp_granite", "#5c5a58", 0.35, var=0.25, vs=60, rv=0.1, grime=0.5, gd=0.02, gcol="#2a2826",
             edge=0.5, ed=0.003, ecol="#8a8682", erough=0.5, bump=0.03, bs=400, bd=0.0005, smudge=0.2,
             extra=lambda g, base, r, obj: (g.mix(g.ramp(g.voronoi(180, obj, out='Distance'), 0.0, 0.12),
                                                  (0.02, 0.02, 0.02), base), r))
steel = hk.P("M_tmp_fsteel", "#b8b8ba", 0.3, 1.0, var=0.05, vs=30, grime=0.6, gd=0.01, gcol="#3a3a3a")
rubber = hk.P("M_tmp_frubber", "#121212", 0.8, var=0.06, vs=30, dust=0.3, dz=0.2)

parts = []
# 기둥 2개: L 단면 (바깥쪽 = 문짝이 들어가는 홈, 안쪽 = 스톱)
for sx in (1, -1):
    prof = [(OW, -D / 2), (OW + FW, -D / 2), (OW + FW, D / 2), (OW - 0.015, D / 2), (OW - 0.015, YS), (OW, YS)]
    prof = [(sx * x, y) for x, y in prof]
    if sx < 0:
        prof = prof[::-1]
    parts.append(hk.poly_extrude(A + "_Jamb", prof, OH + FW, paint, loc=(0, 0, 0), bev=0.003, seg=2))
# 상부 틀 (같은 L 단면을 가로로)
prof = [(OH, -D / 2), (OH + FW, -D / 2), (OH + FW, D / 2), (OH - 0.015, D / 2), (OH - 0.015, YS), (OH, YS)]
head = hk.poly_extrude(A + "_Head", [(y, z) for z, y in prof][::-1], 2 * (OW + FW) - 0.002, paint, bev=0.003)
head.rotation_euler = (d2r(90), 0, d2r(90))
head.location = (-(OW + FW) + 0.001, 0, 0)
parts.append(head)
# 안쪽 몰딩(케이싱) 날개
for sx in (1, -1):
    parts.append(hk.box(A + "_Casing", (0.035, 0.012, OH + FW + 0.035), (sx * (OW + FW + 0.0175), D / 2 - 0.006,
                                                                        (OH + FW + 0.035) / 2), mat=paint, bev=0.003))
parts.append(hk.box(A + "_CasingTop", (2 * (OW + FW + 0.035), 0.012, 0.035), (0, D / 2 - 0.006, OH + FW + 0.0175),
                    mat=paint, bev=0.003))
# 문턱 (화강석, 앞 모서리 둥글게)
parts.append(hk.box(A + "_Sill", (2 * (OW + FW), D + 0.02, 0.02), (0, 0, 0.01), mat=stone, bev=0.004, seg=3))
# 고무 개스킷 (스톱 바깥면 둘레)
for sx in (1, -1):
    parts.append(hk.box(A + "_Gasket", (0.009, 0.005, OH - 0.03), (sx * (OW - 0.006), YS - 0.0025, OH / 2 + 0.012),
                        mat=rubber, bev=0.0015))
parts.append(hk.box(A + "_GasketTop", (2 * OW - 0.02, 0.005, 0.009), (0, YS - 0.0025, OH - 0.006), mat=rubber, bev=0.0015))
# 경첩 (틀 쪽 너클 + 판) — 문짝 경첩 축 x=+0.46, y=-0.065
HY = -0.065
for z in (0.25, 1.0, 1.75):
    for dz in (-0.1, 0.092):
        parts.append(hk.cyl(A + "_Hinge", 0.0095, 0.008 if dz < 0 else 0.008, (OW, HY, z + (0.09 if dz > 0 else -0.008)),
                            mat=steel, n=20, bev=0.0012))
    parts.append(hk.cyl(A + "_HingePin", 0.0098, 0.012, (OW, HY, z + 0.098), mat=steel, n=20, bev=0.002))
    parts.append(hk.box(A + "_HingePlate", (0.004, 0.035, 0.09), (OW + 0.002, HY + 0.02, z + 0.045), mat=steel, bev=0.001))
# 스트라이크 판 (래치 쪽 x=-0.46)
parts.append(hk.box(A + "_Strike", (0.003, 0.03, 0.26), (-OW + 0.0005, -0.04, 1.17), mat=steel, bev=0.001))
for z in (1.03, 1.3):
    parts.append(hk.box(A + "_StrikeHole", (0.004, 0.014, 0.024), (-OW + 0.0002, -0.04, z), mat=rubber, bev=0.001))
for z in (1.06, 1.27):
    parts.append(hk.cyl(A + "_Screw", 0.0028, 0.002, (-OW + 0.001, -0.04, z), rot=(0, d2r(-90), 0), mat=steel, n=10, bev=0.0004))
# 도어클로저 슈(브래킷): 상부 스톱 아래면
parts.append(hk.box(A + "_CloserShoe", (0.06, 0.022, 0.02), (0.25, 0.03, OH - 0.015 - 0.01), mat=steel, bev=0.003))
parts.append(hk.cyl(A + "_CloserPin", 0.005, 0.01, (0.25, 0.03, OH - 0.045), mat=steel, n=12, bev=0.001))

frame = hk.join(parts, A)
k3d.set_origin(frame, (0, 0, 0))
k3d.bake(frame, 1024, ao_distance=0.08)
hk.socket(A + "_Socket_DoorHinge", (OW, HY, 0.0), frame)
notes = ("현관 철제 문틀 (외곽 1.04x2.10x0.16m, 열린 폭 0.92, 높이 2.04) + 화강석 문턱 0.02m. 원점 = 바닥 중앙. "
         "-Y = 복도(바깥), +Y = 집 안쪽. 벽(두께 0.12) 중앙에 놓는다: HomeEntry_Socket_DoorFrame 위치. "
         "HomeDoor 원점은 HomeDoorFrame_Socket_DoorHinge (x=+0.46, y=-0.065, z=0) 에 회전 없이 둔다.")
k3d.export(A, hk.CAT, [frame], notes=notes)
k3d.preview(A, [frame], views=((180, 10), (30, 15)))

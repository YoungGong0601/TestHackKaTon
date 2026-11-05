# 할아버지 아파트 현관 (게임 시작 장소). 프로토타입 three 좌표 -> Blender: (bx, by, bz) = (-x3, z3, y3).
# 원점 = 거실 마루 바닥(three 원점). 현관 타일은 한 단 아래(z=-0.13), 현관문은 -Y 쪽 (Unity +Z = 정면).
# 벽/바닥/천장 = M_Tile_* (월드 UV), 가구/소품 = 굽기, 인쇄물 = M_HomeEntry_Prints (굽지 않음).
import sys, math, os, subprocess, random
sys.path.insert(0, '/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/Blender/scripts/Home')
import hk, k3d, bpy, bmesh
from mathutils import Vector

k3d.reset()
A = "HomeEntry"
d2r = math.radians
S, R, T, E, W0, AZ = 0.98, -2.35, 2.9, 2.32, -0.70, -0.13   # 반폭, 문쪽 벽, 뒤 벽, 천장, 단 경계, 현관 바닥
VY = R - 0.06                                               # 문틀 중심 y
rnd = random.Random(11)


def jpg(name):
    """큰 PNG 인쇄 아틀라스를 JPG 로 (저장소 무게)."""
    src = hk.tex(name)
    dst = os.path.splitext(src)[0] + ".jpg"
    if not os.path.exists(dst):
        subprocess.run([hk.PY, "-c", f"from PIL import Image; Image.open({src!r}).convert('RGB').save({dst!r}, quality=90)"],
                       check=True)
    return dst


# ---------------------------------------------------------------- 타일 머티리얼 (벽/바닥/천장)
hk.tex("wallpaper", "wallpaper_diff.jpg")
D2 = hk.OUT2D
# (k3d._copy_as_jpg 가 PNG 원본을 못 저장해서 미리 JPG 로 변환)
def pj(name):
    src = D2 + "/" + name
    dst = os.path.splitext(src)[0] + ".jpg"
    if not os.path.exists(dst):
        subprocess.run([hk.PY, "-c", f"from PIL import Image; Image.open({src!r}).convert('RGB').save({dst!r}, quality=92)"],
                       check=True)
    return dst


t_wall = k3d.tile("Home_Wallpaper", maps={"diff": D2 + "/wallpaper_diff.jpg", "nor": pj("wallpaper_nor.png"),
                                           "rough": pj("wallpaper_rough.png")})
hk.tex("ceilpaper", "ceilpaper_diff.jpg")
t_ceil = k3d.tile("Home_Ceiling", maps={"diff": D2 + "/ceilpaper_diff.jpg", "nor": pj("ceilpaper_nor.png"),
                                         "rough": pj("ceilpaper_rough.png")})
t_tile = k3d.tile("Home_EntryTile", polyhaven_id="granite_tile")
t_wood = k3d.tile("Home_WoodFloor", polyhaven_id="laminate_floor_02", tint=(0.95, 0.86, 0.74))

shell = []


def sbox(name, x0, x1, y0, y1, z0, z1, mat, tm):
    o = hk.box(A + "_" + name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), mat=mat, bev=0)
    o.modifiers.clear()
    for p in o.data.polygons:
        p.use_smooth = False
    k3d.select([o])
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    k3d.uv_world(o, tm)
    shell.append(o)
    return o


sbox("FloorTile", -S, S, R, W0 - 0.06, AZ - 0.08, AZ, t_tile, 2.3)
sbox("FloorWood", -S, S, W0, T, AZ, 0.0, t_wood, 1.7)
WT = 0.12
WY, WZ = -1.75, 1.86                                        # 복도 쪽 작은 창 (-X 벽) 개구부 중심
walls = [sbox("WallL", S, S + WT, R - WT, T + WT, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallR", -S - WT, -S, WY + 0.27, T + WT, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallRDoor", -S - WT, -S, R - WT, WY - 0.27, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallRSill", -S - WT, -S, WY - 0.27, WY + 0.27, AZ - 0.08, WZ - 0.16, t_wall, 1.06),
         sbox("WallRHead", -S - WT, -S, WY - 0.27, WY + 0.27, WZ + 0.16, E + 0.08, t_wall, 1.06),
         sbox("WallBack", -S, S, T, T + WT, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallDoorL", 0.52, S, R - WT, R, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallDoorR", -S, -0.52, R - WT, R, AZ - 0.08, E + 0.08, t_wall, 1.06),
         sbox("WallDoorTop", -0.52, 0.52, R - WT, R, AZ + 2.10, E + 0.08, t_wall, 1.06)]
ceil = sbox("Ceiling", -S, S, R - WT, T + WT, E, E + 0.08, t_ceil, 1.06)
# 현관 타일 걸레받이 (벽 아래 타일 띠)
sbox("TileSkirtR", -S, -S + 0.008, R, W0 - 0.06, AZ, AZ + 0.09, t_tile, 2.3)
sbox("TileSkirtD1", 0.52, S, R, R + 0.008, AZ, AZ + 0.09, t_tile, 2.3)
sbox("TileSkirtD2", -S, -0.52, R, R + 0.008, AZ, AZ + 0.09, t_tile, 2.3)
wl_ = [o for o in shell if "Wall" in o.name]
fl_ = [o for o in shell if "Floor" in o.name or "Skirt" in o.name]
walls_o = k3d.join(wl_, A + "_Walls")
floor_o = k3d.join(fl_, A + "_Floor")
shell = [walls_o, floor_o, ceil]

# ---------------------------------------------------------------- 절차 머티리얼 (굽기용)
def woodfilm(name, tint, scale=1.6, rough=0.45, grime=0.6, edge=0.5):
    """오크 무늬목 필름 (박스 투영) + 손때/모서리 닳음."""
    ph = k3d.polyhaven("oak_veneer_01", "1k")
    def ex(g, b, r, o):
        im = g.img(ph["diff"], vec=g.coord('Object', scale), proj='BOX')
        b2 = g.mix(1.0, im.outputs['Color'], tint, 'MULTIPLY')
        return g.mix(0.75, b, b2), r
    return hk.P(name, tint, rough, var=0.06, vs=4, rv=0.06, grime=grime, gd=0.02, gcol="#1e140c", edge=edge, ed=0.002,
                ecol="#b89a78", erough=0.7, bump=0.04, bs=200, dust=0.4, dz=0.06, dcol="#4a4036", smudge=0.2, extra=ex)


cab_w = woodfilm("M_tmp_cabwood", hk.srgb("#7a5034"))
door_w = woodfilm("M_tmp_doorwood", hk.srgb("#9a6c48"), 1.3)
trim_w = woodfilm("M_tmp_trimwood", hk.srgb("#6a4a2e"), 2.0, grime=0.8, edge=0.8)
brass = hk.P("M_tmp_brass", "#a08048", 0.3, 1.0, var=0.12, vs=20, grime=0.8, gd=0.006, gcol="#3a2c18", edge=0.6, ed=0.0015,
             ecol="#e0c690", erough=0.15, smudge=0.3)
steel = hk.P("M_tmp_steel", "#b0b0b2", 0.32, 1.0, var=0.05, vs=30, grime=0.6, gd=0.006, gcol="#3a3a3a", smudge=0.2)
alu = hk.P("M_tmp_alu", "#a9aaa6", 0.4, 0.9, var=0.06, vs=10, grime=0.8, gd=0.01, gcol="#4a463e", dust=0.0)
plast = hk.P("M_tmp_plastic", "#e3ddcc", 0.45, var=0.05, vs=6, grime=0.7, gd=0.006, gcol="#7a705a", edge=0.3, ed=0.0015,
             ecol="#f4f0e4", smudge=0.4,
             extra=lambda g, b, r, o: (g.mix(g.ramp(g.noise(3, 2, 0.5, o), 0.3, 0.8), b, hk.srgb("#d6c9a6")), r))
dark = hk.P("M_tmp_dark", "#2a2826", 0.4, var=0.05, vs=20, grime=0.4, gd=0.004, smudge=0.5)
screen = hk.P("M_tmp_screen", "#0d0f10", 0.08, var=0.02, smudge=1.0)
crown = hk.P("M_tmp_crown", "#cfc8b4", 0.6, var=0.05, vs=5, grime=0.7, gd=0.02, gcol="#7a705a", dust=0.0)
glow = hk.P("M_tmp_frost", "#d8dde0", 0.5, var=0.04, emis="#b8c8d8", estr=1.6,
            extra=lambda g, b, r, o: (g.mix(g.math('MULTIPLY', g.ramp(g.wave(28, o, 'Y', 0.5, 1), 0.75, 1.0), 0.6), b,
                                            (0.25, 0.26, 0.27)), r))
fabric = hk.P("M_tmp_jacket", "#4f4a3c", 0.75, var=0.08, vs=6, rv=0.06, grime=0.9, gd=0.03, gcol="#1e1c16", bump=0.25,
              bs=1600, bk='cloth', bd=0.0002, dust=0.0, smudge=0.0,
              extra=lambda g, b, r, o: (g.mix(g.math('MULTIPLY', g.ramp(g.wave(14.3, o, 'Z', 0.0, 0.0, 'BANDS', 'SAW'),
                                                                          0.93, 1.0), 0.6), b, hk.srgb("#25221a")), r))
felt = hk.P("M_tmp_felt", "#5a5246", 0.9, var=0.1, vs=12, grime=0.7, gd=0.01, gcol="#2a251e", bump=0.3, bs=900, bd=0.0003)
rubber = hk.P("M_tmp_rubber", "#1a1a1a", 0.8, var=0.06, vs=20, grime=0.3, gd=0.003, dust=0.6, dz=0.03)
slip_m = hk.P("M_tmp_slipper", "#3c4a5a", 0.85, var=0.1, vs=20, grime=0.8, gd=0.008, gcol="#161a20", bump=0.3, bs=1200,
              bk='cloth')
slip_sole = hk.P("M_tmp_slipsole", "#8a7a66", 0.8, var=0.08, grime=0.6, gd=0.004, dust=0.5, dz=0.01)
standm = hk.P("M_tmp_stand", "#3f4240", 0.5, 0.6, var=0.08, vs=6, grime=0.8, gd=0.02, gcol="#151514", edge=0.7, ed=0.002,
              ecol="#9a9c98", erough=0.35, dust=0.8, dz=0.1, dcol="#5a5448", smudge=0.3)
ceram = hk.P("M_tmp_ceramic", "#7b6a52", 0.25, var=0.1, vs=8, grime=0.5, gd=0.005, edge=0.4, ed=0.0015, ecol="#c8b898")
paper = hk.P("M_tmp_paper", "#dcd7c6", 0.85, var=0.06, vs=20, grime=0.5, gd=0.003, gcol="#8a8270", bump=0.1, bs=800)
radio_b = hk.P("M_tmp_radio", "#54483a", 0.45, var=0.08, vs=8, grime=0.6, gd=0.006, gcol="#1e1812", edge=0.6, ed=0.0015,
               ecol="#8a7a64", erough=0.6, dust=0.3, dz=0.17, smudge=0.4)
key_m = hk.P("M_tmp_keys", "#b8a878", 0.3, 1.0, var=0.12, grime=0.6, gd=0.002, gcol="#3a3020")

PR = hk.flat_img("M_HomeEntry_Prints", jpg("entry_prints.png"), 0.55)
FL = hk.flat_img("M_HomeEntry_Paper", jpg("door_flyers.png"), 0.7)
MI = hk.flat_img("M_HomeEntry_Labels", hk.tex("intercom.png"), 0.5)
RD = hk.flat_img("M_HomeEntry_RadioFace", hk.tex("radio.png"), 0.5)
MT = hk.flat_img("M_HomeEntry_Doormat", hk.tex("doormat.jpg"), 0.95)
GL = hk.glass("M_Glass_HomeEntry_Cup", (0.86, 0.9, 0.88), 0.25, 0.05)
LG = k3d.mat("M_HomeEntry_LightGlow", (0.95, 0.93, 0.88), 0.4, 0.0, emission=(1.0, 0.86, 0.62), strength=4.0)
GLF = hk.glass("M_Glass_HomeEntry_Frame", (0.9, 0.92, 0.92), 0.06, 0.03)        # 액자 유리 (smoothness 0.97)
MIR = k3d.mat("M_HomeEntry_Mirror", (0.92, 0.93, 0.93), 0.04, 1.0)                # 거울 (굽지 않음, Reflection Probe 필요)
FG = hk.flat_img("M_HomeEntry_FloorGrime", hk.tex("floor_grime.png"), 0.8)        # 현관 타일 얼룩/밑창 자국 데칼 (투명)
FG.node_tree.links.new(next(n for n in FG.node_tree.nodes if n.type == 'TEX_IMAGE').outputs['Alpha'],
                       k3d.principled(FG).inputs['Alpha'])
k3d.flag(FG, transparent=True)
for _m in (GL, GLF):                       # Blender 미리보기용: 디더링 노이즈 대신 블렌딩 (Unity 는 json transparent)
    _m.surface_render_method = 'BLENDED'
KEEP = ("M_HomeEntry_Prints", "M_HomeEntry_Paper", "M_HomeEntry_Labels", "M_HomeEntry_RadioFace", "M_HomeEntry_Doormat",
        "M_HomeEntry_FloorGrime", "M_HomeEntry_Mirror")

def bake_tf(o):
    """위치/회전/크기를 메시에 적용 (join 시 첫 오브젝트 변환이 남지 않게)."""
    k3d.select([o])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


RZ = (0, 0, d2r(90))     # -X 벽(오른쪽 벽)에 붙어 +X 를 봄
LZ = (0, 0, d2r(-90))    # +X 벽(왼쪽 벽)에 붙어 -X 를 봄


def uvr(px0, py0, px1, py1, n=2048):
    """아틀라스 픽셀 박스 -> uv (u0,v0,u1,v1)."""
    return (px0 / n, 1 - py1 / n, px1 / n, 1 - py0 / n)


# ================================================================ 1) 고정 마감재 (Trim): 걸레받이/몰딩/문턱/방문/분전반/스위치/인터폰/창/센서등
trim = []
# 마루 귀틀 (단 앞면) + 황동 논슬립
trim.append(hk.box(A + "_StepBoard", (2 * S, 0.06, 0.15), (0, W0 - 0.03, AZ + 0.075), mat=trim_w, bev=0.004, seg=3))
trim.append(hk.box(A + "_StepNosing", (2 * S - 0.01, 0.075, 0.008), (0, W0 - 0.0225, 0.0 + 0.004 + 0.016), mat=brass,
                   bev=0.002))
for k in range(5):
    trim.append(hk.box(A + "_NosingGroove", (2 * S - 0.03, 0.004, 0.002), (0, W0 - 0.05 + k * 0.012, 0.0285), mat=dark,
                       bev=0.0005))
# 거실 걸레받이 (양 옆 + 뒤)
for sx in (1, -1):
    trim.append(hk.box(A + "_Base", (0.014, T - W0, 0.09), (sx * (S - 0.007), (T + W0) / 2, 0.045), mat=trim_w, bev=0.003))
trim.append(hk.box(A + "_BaseBack", (2 * S, 0.014, 0.09), (0, T - 0.007, 0.045), mat=trim_w, bev=0.003))
# 천장 몰딩 (네 벽)
for sx in (1, -1):
    trim.append(hk.box(A + "_Crown", (0.03, T - R, 0.05), (sx * (S - 0.015), (T + R) / 2, E - 0.025), mat=crown, bev=0.006, seg=3))
for yy in (T - 0.015, R + 0.015):
    trim.append(hk.box(A + "_Crown", (2 * S, 0.03, 0.05), (0, yy, E - 0.025), mat=crown, bev=0.006, seg=3))

# 뒤 벽 방문 (안방 문) + 문틀 + 레버
DX = -0.25
trim.append(hk.box(A + "_RoomDoor", (0.82, 0.04, 2.02), (DX, T - 0.02, 1.01), mat=door_w, bev=0.004, seg=3))
for (pz, ph) in ((1.42, 0.7), (0.52, 0.72)):
    trim.append(hk.box(A + "_RoomDoorPanel", (0.6, 0.008, ph), (DX, T - 0.042, pz), mat=door_w, bev=0.006, seg=3))
for sx in (-1, 1):
    trim.append(hk.box(A + "_RoomCasing", (0.06, 0.02, 2.08), (DX + sx * 0.44, T - 0.01, 1.04), mat=trim_w, bev=0.004))
trim.append(hk.box(A + "_RoomCasingTop", (0.94, 0.02, 0.06), (DX, T - 0.01, 2.07), mat=trim_w, bev=0.004))
trim.append(hk.cyl(A + "_RoomRose", 0.026, 0.008, (DX - 0.33, T - 0.04, 0.98), rot=(d2r(90), 0, 0), mat=brass, n=24, bev=0.002))
trim.append(hk.tube(A + "_RoomLever", [(DX - 0.33, T - 0.045, 0.98), (DX - 0.33, T - 0.07, 0.98), (DX - 0.25, T - 0.072, 0.978),
                                         (DX - 0.235, T - 0.066, 0.97)], 0.008, 10, brass))

trim_o = hk.join(trim, A + "_Trim")
trim = []
# 분전반 (+X 벽, 2.0m)
BX, BY, BZ = S - 0.04, 0.35, 2.0
trim.append(hk.box(A + "_Breaker", (0.06, 0.26, 0.34), (BX + 0.01, BY, BZ), mat=plast, bev=0.005, seg=3))
trim.append(hk.box(A + "_BreakerSeam", (0.004, 0.002, 0.3), (BX - 0.021, BY, BZ), mat=dark, bev=0.0005))
trim.append(hk.box(A + "_BreakerLatch", (0.01, 0.03, 0.012), (BX - 0.023, BY - 0.07, BZ - 0.1), mat=plast, bev=0.003))
trim.append(hk.quad(A + "_BreakerLabel", 0.105, 0.036, MI, loc=(BX - 0.021, BY + 0.066, BZ + 0.1), rot=LZ,
                    uv=uvr(120, 740, 904, 980, 1024)))
# 스위치 (+X 벽, 1.2m) — 2구
SX_, SY_, SZ_ = S - 0.005, 0.55, 1.2
trim.append(hk.box(A + "_SwitchPlate", (0.01, 0.075, 0.12), (SX_, SY_, SZ_), mat=plast, bev=0.003, seg=3))
for k in (-1, 1):
    trim.append(hk.box(A + "_SwitchKey", (0.006, 0.026, 0.07), (SX_ - 0.007, SY_ + k * 0.0145, SZ_), rot=(0, d2r(4 * k), 0),
                       mat=plast, bev=0.002))
trim.append(hk.quad(A + "_SwitchLabel", 0.05, 0.016, MI, loc=(SX_ - 0.006, SY_, SZ_ + 0.048), rot=LZ,
                    uv=uvr(160, 540, 860, 700, 1024)))
# 인터폰 / 월패드 (-X 벽, 단 옆)
IX, IY, IZ = -S + 0.016, -0.38, 1.42
trim.append(hk.box(A + "_Intercom", (0.032, 0.2, 0.26), (IX, IY, IZ), mat=plast, bev=0.008, seg=3))
trim.append(hk.box(A + "_IntercomScreen", (0.004, 0.12, 0.09), (IX + 0.016, IY + 0.02, IZ + 0.05), mat=screen, bev=0.002))
trim.append(hk.box(A + "_IntercomBezel", (0.003, 0.136, 0.106), (IX + 0.0148, IY + 0.02, IZ + 0.05), mat=dark, bev=0.002))
for k in range(4):
    trim.append(hk.box(A + "_IntercomBtn", (0.006, 0.034, 0.018), (IX + 0.018, IY - 0.055 + (k % 2) * 0.05, IZ - 0.045 - (k // 2) * 0.03),
                       mat=plast, bev=0.003))
trim.append(hk.quad(A + "_IntercomLabels", 0.084, 0.05, MI, loc=(IX + 0.0222, IY - 0.03, IZ - 0.06), rot=RZ,
                    uv=uvr(0, 0, 1024, 512, 1024)))
for k in range(5):
    trim.append(hk.box(A + "_Speaker", (0.004, 0.06, 0.003), (IX + 0.016, IY + 0.02, IZ - 0.098 - k * 0.007), mat=dark, bev=0.0008))
trim.append(hk.cyl(A + "_IntercomLed", 0.0025, 0.002, (IX + 0.016, IY + 0.085, IZ + 0.1), rot=(0, d2r(90), 0), mat=screen, n=8, bev=0))
# 복도 쪽 작은 창 (-X 벽, 젖빛 유리 + 알루미늄 틀 + 방범창)
trim.append(hk.box(A + "_WinGlass", (0.006, 0.54, 0.32), (-S - 0.03, WY, WZ), mat=glow, bev=0.001))
_g, _p = hk.G(glow), k3d.principled(glow)
_o = _g.coord('Object')
_dz = _g.math('ABSOLUTE', _g.math('SUBTRACT', _g.sep(_o)[2], WZ))
_bar = _g.math('MAXIMUM', _g.ramp(_g.wave(3.1416, _o, 'Y', 0.0, 0.0), 0.86, 0.97),
               _g.math('MULTIPLY', _g.ramp(_dz, 0.105, 0.115), _g.math('SUBTRACT', 1.0, _g.ramp(_dz, 0.135, 0.145))))
_bar = _g.math('MULTIPLY', _bar, 0.85)
_g.link(_g.mix(_bar, _p.inputs['Base Color'].links[0].from_socket, (0.12, 0.12, 0.13)), _p.inputs['Base Color'])
_g.link(_g.mix(_bar, tuple(_p.inputs['Emission Color'].default_value[:3]), (0.04, 0.045, 0.05)), _p.inputs['Emission Color'])
for (dy, dz, sy, sz) in ((0, 0.175, 0.6, 0.03), (0, -0.175, 0.6, 0.03), (-0.285, 0, 0.03, 0.38), (0.285, 0, 0.03, 0.38),
                         (0, 0, 0.022, 0.32)):
    trim.append(hk.box(A + "_WinFrame", (0.05, sy, sz), (-S - 0.01, WY + dy, WZ + dz), mat=alu, bev=0.003))
trim.append(hk.box(A + "_WinSill", (0.06, 0.64, 0.02), (-S + 0.01, WY, WZ - 0.2), mat=alu, bev=0.004))
trim.append(hk.box(A + "_WinLatch", (0.012, 0.02, 0.04), (-S + 0.02, WY - 0.012, WZ), mat=alu, bev=0.003))
# 센서등 (천장, 현관 가운데) — 발광 덮개는 따로 (Glow)
LY = -1.25
trim.append(hk.cyl(A + "_LightBase", 0.135, 0.018, (0, LY, E - 0.018), mat=plast, n=48, bev=0.004, seg=3))
trim.append(hk.lathe(A + "_PirDome", [(0.018, 0), (0.017, -0.006), (0.012, -0.013), (0.0, -0.016)], 20, plast,
                     loc=(0.0, LY - 0.095, E - 0.018)))
# 코트 걸이 (+X 벽, 1.76m) + 고리 3
CY, CZ = 1.9, 1.76
trim.append(hk.box(A + "_CoatRail", (0.02, 0.8, 0.09), (S - 0.01, CY, CZ), mat=trim_w, bev=0.004, seg=3))
for k in (-1, 0, 1):
    y = CY + k * 0.28
    trim.append(hk.tube(A + "_Hook", [(S - 0.02, y, CZ + 0.01), (S - 0.06, y, CZ + 0.012), (S - 0.075, y, CZ + 0.035),
                                      (S - 0.07, y, CZ + 0.05)], 0.0045, 10, brass))
    trim.append(hk.cyl(A + "_HookBase", 0.012, 0.006, (S - 0.02, y, CZ + 0.01), rot=(0, d2r(-90), 0), mat=brass, n=16, bev=0.0015))
# 달력 못 + 액자/시계 (인쇄 부분은 Prints)
trim.append(hk.cyl(A + "_Nail", 0.0025, 0.012, (-S, -1.05, 1.775), rot=(0, d2r(90), 0), mat=steel, n=8, bev=0.0005))


def frame(name, w, h, y, z, uv, tilt):
    fw = 0.03
    parts = []
    for (dy, dz, sy, sz) in ((0, (h + fw) / 2, w + 2 * fw, fw), (0, -(h + fw) / 2, w + 2 * fw, fw),
                             (-(w + fw) / 2, 0, fw, h), ((w + fw) / 2, 0, fw, h)):
        parts.append(hk.box(name + "_F", (0.024, sy, sz), (0, dy, dz), mat=trim_w, bev=0.004, seg=2))
    parts.append(hk.box(name + "_Mat", (0.004, w + 0.004, h + 0.004), (-0.008, 0, 0), mat=paper, bev=0.0005))
    q = hk.quad(name + "_Photo", w - 0.04, h - 0.04, PR, loc=(0.0, 0, 0), rot=RZ, uv=uv)
    q.location = (-0.0055, 0, 0)
    parts.append(q)
    parts.append(hk.quad(name + "_Glass", w + 0.01, h + 0.01, GLF, loc=(0.006, 0, 0), rot=RZ))
    o = hk.join(parts, name)
    k3d.set_origin(o, (0, 0, 0))
    o.location = (-S + 0.013, y, z)
    o.rotation_euler = (tilt, 0, 0)
    return o


trim.append(frame(A + "_Photo1", 0.52, 0.38, 1.12, 1.56, uvr(0, 0, 1024, 725), 0.012))
trim.append(frame(A + "_Photo2", 0.22, 0.28, 0.58, 1.42, uvr(1040, 0, 1552, 683), -0.01))
trim.append(frame(A + "_Photo3", 0.24, 0.30, 1.72, 1.40, uvr(1568, 0, 2040, 614), 0.02))
# 달력 (살짝 말린 종이, 못에 걸림)
cal = hk.quad(A + "_Calendar", 0.36, 0.52, PR, loc=(-S + 0.004, -1.05, 1.5), rot=RZ, uv=uvr(1240, 1024, 1948, 2046), nx=6, ny=8,
              bend=lambda u, v: -0.004 * (1 - v) ** 2 - 0.002 * math.sin(u * math.pi))
trim.append(cal)
# 벽시계 (-X 벽) 테두리 + 문자판, 바늘은 자식
CKY, CKZ = 0.1, 1.86
trim.append(hk.cyl(A + "_ClockRim", 0.17, 0.04, (-S, CKY, CKZ), rot=(0, d2r(90), 0), mat=trim_w, n=48, bev=0.008, seg=3))
bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
u0, v0, u1, v1 = uvr(12, 1036, 1012, 2036)
vs = [bm.verts.new((0, 0.15 * math.cos(a), 0.15 * math.sin(a))) for a in [k / 48 * 2 * math.pi for k in range(48)]]
f = bm.faces.new(vs)
for l in f.loops:
    l[uvl].uv = (u0 + (0.5 + l.vert.co.y / 0.3) * (u1 - u0), v0 + (0.5 + l.vert.co.z / 0.3) * (v1 - v0))
f.normal_update()
if f.normal.x < 0:
    f.normal_flip()
dial = hk.mesh_obj(A + "_ClockDial", bm, PR)
dial.location = (-S + 0.041, CKY, CKZ)
trim.append(dial)
trim.append(hk.cyl(A + "_ClockGlass", 0.152, 0.003, (-S + 0.049, CKY, CKZ), rot=(0, d2r(90), 0), mat=GL, n=48, bev=0.001))
trim.append(hk.torus(A + "_ClockBezel", 0.158, 0.009, (-S + 0.047, CKY, CKZ), (0, d2r(90), 0), trim_w, nu=48, nv=8))
trim.append(hk.cyl(A + "_ClockPin", 0.005, 0.008, (-S + 0.041, CKY, CKZ), rot=(0, d2r(90), 0), mat=brass, n=12, bev=0.001))
# 현관 매트 (거실 마루 위) + 실내 슬리퍼 2짝
mat_o = hk.box(A + "_Doormat", (0.72, 0.42, 0.008), (-0.2, -0.34, 0.004), mat=rubber, bev=0.003)
top = hk.quad(A + "_DoormatTop", 0.70, 0.40, MT, loc=(-0.2, -0.34, 0.0088), rot=(d2r(-90), 0, 0))
trim += [mat_o, top]
trim.append(hk.quad(A + "_FloorGrime", 2 * S - 0.01, (W0 - 0.06) - R - 0.01, FG, loc=(0, (R + W0 - 0.06) / 2, AZ + 0.002),
                    rot=(d2r(-90), 0, 0)))


def slipper(x, y, rz):
    sole = hk.poly_extrude(A + "_SlipSole", [(0.045 * math.sin(a) * (1.1 if math.cos(a) > 0 else 0.9),
                                              0.125 * math.cos(a)) for a in [k / 24 * 2 * math.pi for k in range(24)]],
                           0.018, slip_sole, bev=0.004, seg=2)
    up = hk.lathe(A + "_SlipStrap", [(0.051, 0.0), (0.053, 0.03), (0.051, 0.06), (0.048, 0.09)], 24, slip_m,
                  loc=(0, 0.01, 0.018), rot=(d2r(-90), 0, 0))
    k3d.select([up])
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bmu = bmesh.new()
    bmu.from_mesh(up.data)
    bmesh.ops.delete(bmu, geom=[v for v in bmu.verts if v.co.z < 0.016], context='VERTS')
    bmu.to_mesh(up.data)
    bmu.free()
    so = up.modifiers.new("Sol", 'SOLIDIFY')
    so.thickness = 0.006
    o = hk.join([sole, up], A + "_Slipper")
    k3d.set_origin(o, (0, 0, 0))
    o.location, o.rotation_euler = (x, y, 0.0), (0, 0, rz)
    return o


trim += [slipper(-0.1, -0.32, 0.1), slipper(-0.27, -0.30, -0.08)]

# 우산꽂이 (문 옆 구석)
stand = hk.lathe(A + "_UmbStand", [(0.0, 0.004), (0.094, 0.004), (0.097, 0.012), (0.11, 0.5), (0.114, 0.502), (0.114, 0.508),
                                   (0.106, 0.508), (0.103, 0.5), (0.09, 0.02), (0.0, 0.02)], 40, standm,
                 loc=(-(S - 0.15), R + 0.22, AZ))
trim.append(stand)
for k in range(10):
    a = k / 10 * 2 * math.pi
    trim.append(hk.box(A + "_StandSlot", (0.004, 0.026, 0.28), (-(S - 0.15) + 0.103 * math.cos(a), R + 0.22 + 0.103 * math.sin(a),
                                                                 AZ + 0.26), rot=(0, 0, a), mat=dark, bev=0.001))

k3d.set_origin(trim_o, (0, 0, 0))
k3d.bake(trim_o, 2048, ao_distance=0.06)
fix_o = hk.join(trim, A + "_Fixtures")
k3d.set_origin(fix_o, (0, 0, 0))
for p in fix_o.data.polygons:
    if fix_o.material_slots[p.material_index].material.name in KEEP:
        p.use_smooth = False
# k3d 는 발광 머티리얼이 하나라도 있으면 모든 머티리얼의 Emission Color 를 굽는다 -> 비발광은 검정으로
for s_ in fix_o.material_slots:
    p_ = k3d.principled(s_.material)
    if p_ and p_.inputs['Emission Strength'].default_value <= 0:
        p_.inputs['Emission Color'].default_value = (0, 0, 0, 1)
k3d.bake(fix_o, 2048, keep=KEEP, ao_distance=0.04)

# ================================================================ 2) 신발장 (+X 벽, 문 3짝 = 자식, 가운데 거울)
CB = []
G0, G1, CW, CH = R + 0.02, W0 - 0.05, 0.36, 1.06
CXc = S - CW / 2
CB.append(hk.box(A + "_CabBody", (CW - 0.02, G1 - G0, CH - 0.12), (CXc + 0.01, (G0 + G1) / 2, AZ + 0.12 + (CH - 0.12) / 2), mat=cab_w,
                 bev=0.003))
CB.append(hk.box(A + "_CabKick", (CW - 0.08, G1 - G0 - 0.02, 0.11), (CXc + 0.03, (G0 + G1) / 2, AZ + 0.055), mat=dark, bev=0.002))
CB.append(hk.box(A + "_CabTop", (CW + 0.03, G1 - G0 + 0.03, 0.03), (CXc - 0.005, (G0 + G1) / 2, AZ + CH + 0.015), mat=trim_w,
                 bev=0.005, seg=3))
for yy in (G0, G1):
    CB.append(hk.box(A + "_CabSide", (CW, 0.018, CH), (CXc, yy + (0.009 if yy == G0 else -0.009), AZ + CH / 2), mat=cab_w, bev=0.003))
NDOOR = 3
gw = (G1 - G0) / NDOOR
doors = []
for i in range(NDOOR):
    y0 = G0 + gw * i + 0.002
    y1 = y0 + gw - 0.004
    dz0, dz1 = AZ + 0.11, AZ + CH - 0.02
    dparts = [hk.box(A + "_CabDoor%d_Leaf" % i, (0.02, y1 - y0, dz1 - dz0), (S - CW - 0.01, (y0 + y1) / 2, (dz0 + dz1) / 2),
                     mat=door_w, bev=0.003, seg=3)]
    hy = y1 - 0.045
    dparts.append(hk.box(A + "_CabDoor%d_Handle" % i, (0.016, 0.018, 0.1), (S - CW - 0.03, hy, AZ + CH * 0.62), mat=brass, bev=0.004, seg=3))
    for dz in (-0.04, 0.04):
        dparts.append(hk.cyl(A + "_CabDoor%d_Post" % i, 0.004, 0.012, (S - CW - 0.02, hy, AZ + CH * 0.62 + dz), rot=(0, d2r(-90), 0),
                             mat=brass, n=10, bev=0.0008))
    if i == NDOOR - 1:  # 거울 문
        my, mw_, mh = (y0 + y1) / 2 - 0.005, y1 - y0 - 0.07, 0.62
        dparts.append(hk.box(A + "_CabMirror", (0.004, mw_, mh), (S - CW - 0.021, my, AZ + 0.55), mat=MIR, bev=0.0015))
        for (dy, dz, sy, sz) in ((0, mh / 2, mw_ + 0.008, 0.005), (0, -mh / 2, mw_ + 0.008, 0.005),
                                 (mw_ / 2, 0, 0.005, mh), (-mw_ / 2, 0, 0.005, mh)):
            dparts.append(hk.box(A + "_CabMirrorTrim", (0.006, sy, sz), (S - CW - 0.022, my + dy, AZ + 0.55 + dz), mat=steel,
                                 bev=0.0015))
    d = hk.join(dparts, A + "_CabDoor%d" % i)
    hk.vgroup(d, d.name)
    doors.append((d, y0))
    CB.append(d)
cab = hk.join(CB, A + "_ShoeCabinet")
k3d.set_origin(cab, (CXc, (G0 + G1) / 2, AZ))
k3d.bake(cab, 2048, keep=("M_HomeEntry_Mirror",), ao_distance=0.05)
door_objs = []
for i in range(NDOOR):
    y0 = G0 + gw * i + 0.002
    # (FBX 손자 계층 변환이 깨져서 문짝은 루트 직속 자식으로 둔다)
    door_objs.append(hk.split_vgroup(cab, A + "_CabDoor%d" % i, A + "_CabDoor%d" % i, (S - CW - 0.02, y0 + 0.004, AZ + 0.11)))
for o in [cab] + door_objs:
    o.vertex_groups.clear()

# ================================================================ 3) 신발장 위 잡동사니 (라디오, 전단지 더미, 열쇠 그릇, 물컵)
CL = []
UZ = AZ + CH + 0.03
# 라디오
rp = []
rp.append(hk.box(A + "_Radio", (0.3, 0.09, 0.17), (0, 0, 0.085), mat=radio_b, bev=0.01, seg=3))
rp.append(hk.quad(A + "_RadioFace", 0.28, 0.15, RD, loc=(0, -0.0455, 0.085)))
rp.append(hk.cyl(A + "_RadioKnob", 0.016, 0.014, (0.1, -0.045, 0.045), rot=(d2r(90), 0, 0), mat=dark, n=24, bev=0.002))
rp.append(hk.cyl(A + "_RadioKnob2", 0.016, 0.014, (0.04, -0.045, 0.045), rot=(d2r(90), 0, 0), mat=dark, n=24, bev=0.002))
rp.append(hk.box(A + "_RadioHandle", (0.22, 0.016, 0.012), (0, 0, 0.176), mat=dark, bev=0.005))
for sx in (-0.11, 0.11):
    rp.append(hk.box(A + "_RadioHandlePost", (0.014, 0.016, 0.02), (sx, 0, 0.168), mat=dark, bev=0.004))
rp.append(hk.cyl(A + "_RadioAntenna", 0.0025, 0.32, (0.13, 0.02, 0.17), rot=(0, d2r(-12), 0), mat=steel, n=8, r2=0.0015, bev=0))
for sx in (-0.13, 0.13):
    for sy in (-0.03, 0.03):
        rp.append(hk.cyl(A + "_RadioFoot", 0.008, 0.004, (sx, sy, -0.002), mat=rubber, n=10, bev=0.001))
radio = hk.join(rp, A + "_RadioJ")
k3d.set_origin(radio, (0, 0, 0))
radio.location, radio.rotation_euler = (S - 0.16, -1.85, UZ + 0.004), (0, 0, d2r(-90 - 7))
bake_tf(radio)
CL.append(radio)
# 전단지/고지서 더미 (맨 위 = 중화 반점 전단지)
for i in range(6):
    sh = hk.box(A + "_Papers", (0.14, 0.1, 0.0015), (0, 0, 0), mat=paper, bev=0.0004, seg=1)
    sh.location = (S - 0.2 + (i % 2) * 0.012, -1.26 + (i % 3) * 0.008, UZ + 0.001 + i * 0.0018)
    sh.rotation_euler = (0, 0, d2r(90) + (i - 2) * 0.12)
    CL.append(sh)
topf = hk.quad(A + "_PaperTop", 0.14, 0.1 * 0.94, FL, loc=(S - 0.188, -1.244, UZ + 0.0115), rot=(d2r(-90), 0, d2r(90) + 0.36),
               uv=uvr(1024, 0, 2048, 630))
CL.append(topf)
# 열쇠 그릇 + 열쇠 꾸러미
CL.append(hk.lathe(A + "_KeyDish", [(0.0, 0.0), (0.05, 0.0), (0.055, 0.004), (0.07, 0.024), (0.068, 0.026), (0.052, 0.008),
                                    (0.0, 0.008)], 32, ceram, loc=(S - 0.2, -0.93, UZ)))
CL.append(hk.torus(A + "_KeyRing", 0.012, 0.0012, (S - 0.2, -0.935, UZ + 0.011), (d2r(10), 0, 0), key_m, nu=16, nv=6))
for k, (a, ln) in enumerate(((0.3, 0.05), (1.4, 0.045), (2.6, 0.04))):
    kk = hk.box(A + "_Key", (ln, 0.012, 0.002), (S - 0.2 + math.cos(a) * 0.03, -0.935 + math.sin(a) * 0.03, UZ + 0.0115 + k * 0.0022),
                rot=(0, 0, a), mat=key_m, bev=0.0006)
    CL.append(kk)
CL.append(hk.box(A + "_KeyTag", (0.03, 0.02, 0.004), (S - 0.17, -0.95, UZ + 0.012), rot=(0, 0, 0.4), mat=hk.P("M_tmp_tag", "#a33a2e", 0.5),
                 bev=0.0015))
# 물컵 (유리)
CL.append(hk.lathe(A + "_Cup", [(0.0, 0.0), (0.028, 0.0), (0.03, 0.004), (0.033, 0.09), (0.031, 0.09), (0.028, 0.006),
                                (0.0, 0.006)], 32, GL, loc=(S - 0.23, -1.08, UZ)))
clutter = hk.join(CL, A + "_Clutter")
k3d.set_origin(clutter, (S - 0.18, -1.4, UZ))
for p in clutter.data.polygons:
    if clutter.material_slots[p.material_index].material.name in KEEP:
        p.use_smooth = False
k3d.bake(clutter, 1024, keep=KEEP, ao_distance=0.03)

# ================================================================ 4) 걸린 점퍼 + 중절모 (코트 걸이)
def jacket():
    NZ, NT = 36, 40
    H, Wd, Dp = 0.82, 0.25, 0.06
    bm = bmesh.new()
    rings = []
    for i in range(NZ + 1):
        t = i / NZ                     # 0 아래단, 1 목
        z = -H * (1 - t)
        sh = 1.0 if t < 0.82 else max(0.0, 1 - ((t - 0.82) / 0.18) ** 1.6) * 0.82 + 0.18
        a = Wd * (0.95 + 0.06 * (1 - t)) * sh
        b = Dp * (0.9 + 0.4 * math.sin(math.pi * min(1, t * 1.15))) * (0.5 + 0.5 * sh)
        puff = 1 + 0.035 * abs(math.sin(math.pi * z / 0.07)) ** 0.5 * (1 if t < 0.85 else 0)
        ring = []
        for k in range(NT):
            th = 2 * math.pi * k / NT
            fold = 1 + (0.06 + 0.06 * (1 - t)) * math.sin(5 * th + 1.3 * t + 0.5) * (1 - t) ** 0.7
            x = a * math.cos(th) * fold * puff
            y = b * math.sin(th) * puff
            if y > 0:                  # 벽 쪽(뒤)은 납작
                y *= 0.35
            ring.append(bm.verts.new((x, y - 0.0, z)))
        rings.append(ring)
    for i in range(NZ):
        for k in range(NT):
            a_, b_ = rings[i], rings[i + 1]
            bm.faces.new((a_[k], a_[(k + 1) % NT], b_[(k + 1) % NT], b_[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = hk.mesh_obj(A + "_Jacket", bm, fabric)
    for p in o.data.polygons:
        p.use_smooth = True
    parts = [o]
    # 소매 (어깨에서 앞쪽으로 늘어짐)
    for sx in (-1, 1):
        pts = [(sx * 0.2, -0.03, -0.12), (sx * 0.235, -0.05, -0.3), (sx * 0.23, -0.06, -0.5), (sx * 0.215, -0.055, -0.68)]
        sl = hk.tube(A + "_Sleeve", pts, 0.055, 16, fabric, rfun=lambda t: 1.0 - 0.25 * t)
        parts.append(sl)
        parts.append(hk.cyl(A + "_Cuff", 0.044, 0.04, (sx * 0.215, -0.055, -0.72), mat=hk.P("M_tmp_cuff", "#2e2b24", 0.8,
                                                                                               bump=0.4, bs=900, bk='cloth'), n=16, bev=0.004))
    # 지퍼 + 깃
    parts.append(hk.box(A + "_Zipper", (0.008, 0.004, H - 0.12), (0, -Dp * 1.2 - 0.002, -H / 2 - 0.02), mat=dark, bev=0.001))
    parts.append(hk.box(A + "_ZipPull", (0.01, 0.004, 0.03), (0, -Dp * 1.2 - 0.006, -0.14), mat=steel, bev=0.002))
    parts.append(hk.torus(A + "_Collar", 0.07, 0.022, (0, -0.0, -0.04), (d2r(80), 0, 0), fabric, nu=20, nv=8, sx=1.3))
    parts.append(hk.tube(A + "_HangLoop", [(-0.008, 0.0, -0.02), (-0.004, 0.0, 0.01), (0.004, 0.0, 0.01), (0.008, 0.0, -0.02)],
                         0.002, 6, dark))
    j = hk.join(parts, A + "_JacketJ")
    return j


jk = jacket()
jk.location, jk.rotation_euler = (S - 0.075, CY - 0.28, CZ + 0.045), (0, 0, d2r(-90))
bake_tf(jk)
hat_p = []
hat_p.append(hk.lathe(A + "_HatBrim", [(0.06, 0.0), (0.13, -0.004), (0.142, 0.004), (0.14, 0.009), (0.128, 0.004), (0.06, 0.008)], 40,
                      felt))
hat_p.append(hk.lathe(A + "_HatCrown", [(0.088, 0.004), (0.09, 0.03), (0.086, 0.08), (0.075, 0.1), (0.04, 0.094), (0.0, 0.085)], 40,
                      felt, rmod=lambda th, z, r: r * (1 - 0.12 * max(0.0, math.cos(th)) ** 3 * (z / 0.1)) * (1 + 0.06 * math.sin(th) ** 2),
                      close_top=False))
hat_p.append(hk.lathe(A + "_HatBand", [(0.0905, 0.008), (0.092, 0.012), (0.0912, 0.026), (0.0895, 0.03)], 40,
                      hk.P("M_tmp_band", "#24211c", 0.5, var=0.05, bump=0.2, bs=1500, bk='cloth')))
hat = hk.join(hat_p, A + "_HatJ")
hat.location, hat.rotation_euler = (S - 0.035, CY + 0.28, CZ + 0.01), (d2r(-6), d2r(-80), 0)
bake_tf(hat)
coat = hk.join([jk, hat], A + "_Coat")
k3d.set_origin(coat, (S - 0.06, CY, CZ - 0.8))
k3d.bake(coat, 1024, ao_distance=0.05)

# ================================================================ 5) 센서등 발광 덮개 + 시계 바늘 (자식, 굽지 않음)
glow_o = hk.lathe(A + "_LightGlow", [(0.118, 0.0), (0.112, -0.016), (0.085, -0.03), (0.04, -0.037), (0.0, -0.038)], 40, LG,
                  loc=(0, LY, E - 0.018))
k3d.set_origin(glow_o, (0, LY, E - 0.018))
hands = []
handm = k3d.mat("M_HomeEntry_ClockHands", (0.03, 0.03, 0.03), 0.4)
secm = k3d.mat("M_HomeEntry_ClockSecond", (0.5, 0.06, 0.04), 0.4)
for nm, ln, wd, off, m in (("ClockHour", 0.075, 0.009, 0.0425, handm), ("ClockMinute", 0.115, 0.006, 0.0443, handm),
                           ("ClockSecond", 0.13, 0.0022, 0.046, secm)):
    h = hk.box(A + "_" + nm, (0.0015, wd, ln + 0.02), (-S + off, CKY, CKZ + ln / 2 - 0.01), mat=m, bev=0)
    h.modifiers.clear()
    k3d.set_origin(h, (-S + off, CKY, CKZ))
    hands.append(h)
hands[0].rotation_euler = (-2 * math.pi * (9.4 / 12), 0, 0)
hands[1].rotation_euler = (-2 * math.pi * 0.4, 0, 0)

# ================================================================ 루트 + 소켓
root = trim_o
bpy.context.view_layer.update()
for o in shell + [fix_o, cab, clutter, coat, glow_o] + door_objs + hands:
    hk.parent_keep(o, root)
SK = lambda n, p, rot=(0, 0, 0): hk.socket(A + "_Socket_" + n, p, root, rot=rot)
SK("Spawn", (0, 1.15, 0))
SK("DoorFrame", (0, VY, AZ))
SK("Shoes", (-0.18, -1.28, AZ), (0, 0, 0.16))
SK("Cane", (-(S - 0.2), R + 0.62, AZ + 0.0015), (0, -0.115, 0))              # 갈고리 등이 -X 벽에 닿게 기울임 (간격 2mm)
SK("UmbrellaBlack", (-(S - 0.13), R + 0.20, AZ + 0.02), (0.05, -0.06, 0))     # 꽂이 안, 구석 쪽으로 기움
SK("UmbrellaRed", (-(S - 0.17), R + 0.24, AZ + 0.02), (0.06, -0.05, math.pi))  # 손잡이 -X, 방 쪽으로 기움
# 약 봉투: 앞면이 위, 봉투 윗변이 +X(벽) -> 통로에서 글자가 바로 읽힘. 원점(봉투 아래 변) = 중심 (S-0.14, -1.45) 에서 -X 로 0.085
SK("MedicineBag", (S - 0.14 - 0.085, -1.45 - 0.01, UZ + 0.0145), (-math.pi / 2, 0, -math.pi / 2 + 0.12))
SK("Light", (0, LY, E - 0.07))
SK("WindowLight", (-S + 0.25, WY, WZ))
SK("StepEdge", (0, W0, 0))
SK("Memo", (0, 0.6, 1.1))
SK("DoorOutside", (0, R - 0.9, 1.0))
notes = (
    "현관 환경 모듈 (폭 1.96 x 길이 5.25 x 높이 2.32m). 좌표 = 프로토타입 three 좌표 그대로: Unity(x,y,z) = three(x,y,-z) "
    "→ Blender(bx,by,bz) = (-x3, z3, y3). 원점 = 거실 마루 바닥(three 원점), 현관 타일 바닥 z=-0.13 (y < -0.70 에서 한 단 내려감, "
    "Socket_StepEdge). validate 의 min_z=-0.21 은 바닥/벽 슬래브 두께라 의도한 값. 현관문은 -Y(Unity +Z) 쪽. "
    "벽/바닥/천장 = M_Tile_Home_* (월드 UV, 벽지 엠보 노멀 약하게), 나머지는 HomeEntry_Trim(루트: 걸레받이/몰딩/문턱/방문, 2048 굽기). "
    "자식: HomeEntry_Walls / _Floor / _Ceiling (타일), _Fixtures(분전반/스위치/인터폰/방범창 그림자가 비치는 복도 창/센서등 받침/코트 걸이/액자 3/달력/시계/매트/슬리퍼/우산꽂이 "
    "+ 현관 타일 얼룩 데칼 M_HomeEntry_FloorGrime(투명, 바닥 2mm 위), 2048), _ShoeCabinet(+X 벽 신발장, 2048), "
    "_CabDoor0..2 (신발장 문, 루트 직속 자식, 원점=경첩 축, Z 축 회전; _CabDoor2 는 거울 문: M_HomeEntry_Mirror 는 굽지 않은 metallic 1 / "
    "smoothness 0.96 → 현관 가운데에 Box Projection Reflection Probe(범위 = 현관 크기)를 두어야 거울로 보임), "
    "_Clutter (라디오/전단지/열쇠 그릇/물컵 M_Glass), _Coat (코트 걸이의 점퍼+중절모), "
    "_LightGlow (센서등 발광 덮개 M_HomeEntry_LightGlow: 깜빡임은 이 머티리얼 Emission 조절), "
    "_ClockHour/_ClockMinute/_ClockSecond (원점 = 시계 중심, 로컬 X 축 회전. 회전 0 = 12시 방향. 기본 자세는 9시 24분으로 돌려 둠. "
    "시간을 맞추려면 로컬 X 축 각도를 시침 h/12·360°, 분침 m/60·360°, 초침 s/60·360° 로 설정 — 방향은 현재 9:24 자세를 기준으로 확인; "
    "프로토타입 ve.rotation.z = -floor(t)*PI/30 에 해당). "
    "액자: 큰 것 = 바랜 운해 일출 사진('98 5 5 날짜 각인, Poly Haven CC0 사진), 작은 것 = 가훈 家和萬事成(한지), 표창장(A4). "
    "액자마다 유리 M_Glass_HomeEntry_Frame. 인쇄물(액자, 달력 11월 시장은행, 시계판, 라벨, 라디오 판, 매트)은 굽지 않는 M_HomeEntry_* 텍스처. "
    "M_Dyn 면 없음. "
    "소켓: Spawn(three 0,0,1.15 문 쪽 -Y 바라봄), DoorFrame(HomeDoorFrame 원점, 회전 없음), Shoes(HomeShoes, rotZ 0.16), "
    "Cane(HomeCane 원점을 그대로 맞추면 갈고리가 -X 벽에 기댐), UmbrellaBlack(HomeUmbrella), UmbrellaRed(HomeUmbrellaRed) — 두 우산 끝이 "
    "우산꽂이 바닥(AZ+0.02)에 닿고 서로 반대쪽으로 기울어 겹치지 않음, MedicineBag(HomeMedicineBag 원점을 그대로 맞추면 앞면이 위로 누워 "
    "봉투 윗변이 벽 쪽: 통로에서 '약 봉투 / 아침 저녁 식후 30분 / 새봄 약국'이 바로 읽힘), "
    "Light(센서등 Light 위치), WindowLight(복도 창 빛), StepEdge, Memo, DoorOutside(문 밖 밝은 면/조명 위치).")
k3d.export(A, hk.CAT, [root], notes=notes)
# ---------------------------------------------------------------- 미리보기 (실내 1인칭 + 외부 3/4)
L_ = [('POINT', (0, LY, E - 0.15), 60, (1, 0.86, 0.66), 0.2), ('POINT', (0, 0.6, 2.1), 45, (1, 0.9, 0.75), 0.3),
      ('POINT', (-0.6, -1.75, 1.8), 12, (0.75, 0.85, 1.0), 0.2)]
hk.shot(hk.PREV + "/HomeEntry_fp_door.png", (0.0, 1.15, 1.55), (0.0, -2.35, 0.75), lens=24, lights=L_, world=0.15)
hk.shot(hk.PREV + "/HomeEntry_fp_cabinet.png", (-0.2, -0.3, 1.45), (0.75, -1.5, 0.8), lens=24, lights=L_, world=0.15)
hk.shot(hk.PREV + "/HomeEntry_fp_back.png", (0.2, -1.6, 1.55), (-0.3, 2.9, 1.2), lens=24, lights=L_, world=0.15)
hk.shot(hk.PREV + "/HomeEntry_fp_right.png", (0.6, -0.2, 1.55), (-0.98, -0.8, 1.45), lens=24, lights=L_, world=0.15)

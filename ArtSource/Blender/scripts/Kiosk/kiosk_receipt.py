"""키오스크 영수증 (감열지 80 x 250mm, 출구에서 말려 나와 늘어진 모양).  blender -b --factory-startup --python kiosk_receipt.py
원점 = 영수증 출구(슬롯) 지점. Kiosk_Socket_ReceiptOut 에 붙인다."""
import bmesh, math, os, sys, subprocess
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "Store"))
import k3d  # noqa: E402
import storelib as S  # noqa: E402

N = "KioskReceipt"
TEX = os.path.join(k3d.ART, "Textures", N, f"T_{N}_Paper.png")
if not os.path.exists(TEX):
    subprocess.run([k3d.PY, os.path.join(HERE, "kiosk_tex.py"), k3d.REPO, k3d.CACHE, "receipt"], check=True)

k3d.reset()
W, LR, R, A0 = 0.08, 0.25, 0.034, 1.45   # 폭, 길이, 처음 말림 반지름/각도 (프로토 printReceipt 곡선)
NX, NS = 16, 60


def prof(s):
    """출구에서 s(m) 떨어진 곳의 (y, z) 와 앞면(인쇄면) 법선."""
    s0 = R * A0
    if s <= 0:
        p, t = Vector((-s, 0)), Vector((-1, 0))
    elif s < s0:
        a = s / R
        p, t = Vector((-R * math.sin(a), -R * (1 - math.cos(a)))), Vector((-math.cos(a), -math.sin(a)))
    else:
        e = s - s0
        p = Vector((-R * math.sin(A0) - e * math.cos(A0) - math.sin(s * 22) * 0.0035,
                    -R * (1 - math.cos(A0)) - e * math.sin(A0) - math.sin(s * 40) * 0.0008))
        t = Vector((-math.cos(A0) - 22 * math.cos(s * 22) * 0.0035, -math.sin(A0))).normalized()
    return p, Vector((t.y, -t.x))


bm = bmesh.new()
uvl = bm.loops.layers.uv.new("UVMap")
for layer in (0, 1):  # 0 = 인쇄면(앞), 1 = 뒷면
    rows = []
    for j in range(NS + 1):
        s = -0.006 + (LR + 0.006) * j / NS
        row = []
        for i in range(NX + 1):
            x = (i / NX - 0.5) * W
            ss = s - (0.0016 if (j == NS and i % 2) else 0.0)  # 찢은 끝 톱니
            p, n = prof(ss)
            cup = 0.0028 * (2 * x / W) ** 2 + 0.0009 * math.sin(i * 0.9 + j * 0.4) * (j / NS)  # 감열지 가로 말림
            off = cup - (0.00012 if layer else 0.0)
            row.append((bm.verts.new((x, p.x + n.x * off, p.y + n.y * off)), i / NX, 1 - max(ss, 0) / LR))
        rows.append(row)
    for j in range(NS):
        for i in range(NX):
            q = (rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i])
            f = bm.faces.new([c[0] for c in (q if layer else q[::-1])])
            f.material_index = layer
            for lp, c in zip(f.loops, (q if layer else q[::-1])):
                lp[uvl].uv = (c[1], c[2])
m_front = S.img_mat(f"M_Dyn_{N}_Paper", TEX, rough=0.45)
m_back = k3d.mat(f"M_{N}_Back", (0.84, 0.83, 0.79), 0.7)
rc = S.obj_from_bm(f"{N}_Paper", bm, mat=m_front)
rc.data.materials.append(m_back)
k3d.smooth(rc, 60)
grip = prof(LR - 0.02)[0]
S.empty(f"{N}_Socket_Grip", (0, grip.x, grip.y), rc, 0.02)
notes = ("감열지 영수증 80 x 250mm, 출구에서 3.4cm 반지름으로 말려 나와 아래로 늘어진 모양. 원점 = 영수증 출구 지점 "
         "(바닥 기준이 아님: Kiosk_Socket_ReceiptOut 에 붙이는 부품이라 원점이 슬롯에 있다). 정면 = Unity +Z (인쇄면이 손님 쪽). "
         f"동적 면: {N}_Paper 의 M_Dyn_{N}_Paper (인쇄면, 0.08 x 0.25m, 640x2000px, UV 0-1, U=오른쪽, V=위 = 출구 쪽이 V1, "
         "찢긴 끝이 V0; 프로토 Rg() 내용: 버거대왕 시장입구점 / 주문번호 274 / 메뉴 / 신용카드 승인). 뒷면 = M_KioskReceipt_Back(무지). "
         "출력 애니메이션은 게임에서 메시를 V 방향으로 잘라 보이거나 스케일로 처리. 소켓: KioskReceipt_Socket_Grip(뜯을 때 잡는 곳, 끝에서 2cm).")
k3d.export(N, "Kiosk", [rc], notes=notes)
k3d.preview(N, [rc], views=((25, 8), (205, 10)))
k3d.preview(N, [rc], views=((0, 4),), lens=35, tag="front")

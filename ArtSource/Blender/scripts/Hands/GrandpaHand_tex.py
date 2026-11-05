"""할아버지 손 2D 텍스처 (Pillow + numpy). GrandpaHand.py 가 _cache/venv/bin/python 으로 호출한다.

입력 JSON(argv[1]):
  {"out": 폴더, "side": "R"|"L", "seed": int, "rs": +1(엄지 +X)|-1,
   "maps": {"top"|"bot"|"thumb": {"N": px, "S": m, "x0": m, "y0": m, "j": {관절: [x, y]}}},
   "knit": bool, "dial": bool, "wrinkle": 0|1 (게임 거리에서 보이는 주름과 얼룩, 1 = 80대)}
출력(out 폴더):
  <side>_<map>_h.png  16bit 높이 (0.5 = 0, 1 단위 = 4mm)
  <side>_<map>_m.png  RGB 마스크 (top: R 정맥 G 검버섯 B 붉은기 / bot: R 주름 G 분홍 B 굳은살 / thumb: top 과 같음)
  <side>_<map>_n.png  RGB 마스크2 (R 흰 털 G 검은 털 B 흉터·각질)
  knit_*.png, rib_*.png (뜨개 타일), dial.png (시계 문자판)
"""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SS = 2  # 슈퍼샘플


class Canvas:
    """미터 단위 평면 -> 픽셀. 레이어는 'L' 8bit 로 그리고 float 로 합친다."""

    def __init__(s, N, S, x0, y0):
        s.N, s.S, s.x0, s.y0, s.W = N, S, x0, y0, N * SS

    def px(s, p):
        return ((p[0] - s.x0) / s.S * s.W, (1 - (p[1] - s.y0) / s.S) * s.W)

    def m(s, v):
        return v / s.S * s.W

    def layer(s):
        im = Image.new('L', (s.W, s.W), 0)
        return im, ImageDraw.Draw(im)

    def done(s, im, blur=0.0):
        if blur > 0:
            im = im.filter(ImageFilter.GaussianBlur(max(0.3, s.m(blur))))
        im = im.resize((s.N, s.N), Image.BOX)
        return np.asarray(im, np.float32) / 255.0


def v2(a):
    return np.array(a, np.float64)


def unit(a):
    a = v2(a)
    return a / (np.linalg.norm(a) + 1e-12)


def perp(a):
    return np.array([-a[1], a[0]])


def spline(pts, n=24):
    """Catmull-Rom 곡선 (끝점 통과)."""
    P = [v2(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def wobble(pts, rng, amp, wl):
    """곡선에 수직 방향 사인 흔들림 (구불구불한 정맥)."""
    d = np.gradient(pts, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    ph1, ph2 = rng.uniform(0, 6.28, 2)
    off = amp * (np.sin(s / wl * 6.28 + ph1) * 0.7 + np.sin(s / (wl * 0.43) * 6.28 + ph2) * 0.3)
    off *= np.minimum(1, np.minimum(s, s[-1] - s) / (wl * 0.5) + 0.2)
    return pts + n * off[:, None]


def stroke(c, dr, pts, width_m, val=255, taper=False):
    """폴리라인 (폭 m). taper=True 면 양 끝이 가늘어진다."""
    P = [c.px(p) for p in pts]
    n = len(P)
    for i in range(n - 1):
        t = i / max(1, n - 2)
        w = width_m * (math.sin(math.pi * min(1, max(0, t))) ** 0.5 if taper else 1)
        wp = max(1, int(round(c.m(w))))
        dr.line([P[i], P[i + 1]], fill=val, width=wp)
        r = wp / 2
        dr.ellipse([P[i + 1][0] - r, P[i + 1][1] - r, P[i + 1][0] + r, P[i + 1][1] + r], fill=val)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def grid_xy(c):
    """출력 해상도 픽셀 중심의 미터 좌표 (X, Y)."""
    N = c.N
    ys, xs = np.mgrid[0:N, 0:N].astype(np.float32)
    return c.x0 + (xs + 0.5) / N * c.S, c.y0 + (1 - (ys + 0.5) / N) * c.S


def spots(c, rng, pts):
    """검버섯: pts=[(중심, 반지름m, 진하기)]. 노이즈로 비튼 윤곽 + 크기 비례 가우시안 페더 + 속 얼룩 -> float."""
    acc = np.zeros((c.W, c.W), np.float32)
    for p, r, val in pts:
        th = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        ph = rng.uniform(0, 6.28, 4)
        rr = r * (1 + 0.17 * np.sin(2 * th + ph[0]) + 0.1 * np.sin(3 * th + ph[1]) + 0.06 * np.sin(5 * th + ph[2])
                  + 0.04 * np.sin(8 * th + ph[3]))
        asp, rot = rng.uniform(0.65, 1.0), rng.uniform(0, math.pi)
        cr, sr = math.cos(rot), math.sin(rot)
        poly = [c.px(v2(p) + v2((cr * x - sr * y, sr * x + cr * y)))
                for x, y in zip(rr * np.cos(th), rr * np.sin(th) * asp)]
        fe = max(1.0, c.m(r * rng.uniform(0.2, 0.38)))  # 가장자리 페더 (작은 점은 좁게)
        pad = int(fe * 3) + 2
        x0, y0 = int(min(q[0] for q in poly)) - pad, int(min(q[1] for q in poly)) - pad
        x1, y1 = int(max(q[0] for q in poly)) + pad, int(max(q[1] for q in poly)) + pad
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).polygon([(q[0] - x0, q[1] - y0) for q in poly], fill=255)
        a = np.asarray(im.filter(ImageFilter.GaussianBlur(fe)), np.float32) / 255
        mot = np.asarray(Image.fromarray((rng.random((6, 6)) * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC),
                         np.float32) / 255
        a *= val * (0.82 + 0.18 * mot)  # 속이 고르지 않은 얼룩
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(c.W, x1), min(c.W, y1)
        if xa < xb and ya < yb:
            acc[ya:yb, xa:xb] = np.maximum(acc[ya:yb, xa:xb], a[ya - y0:yb - y0, xa - x0:xb - x0])
    return c.done(Image.fromarray((acc * 255).astype(np.uint8)))


def place_spots(rng, zones, n, taken=()):
    """무작위(포아송 디스크) 배치. zones=[(가중치, 샘플함수)]. 지름 2~15mm 로그정규."""
    out = list(taken)
    ws = np.array([z[0] for z in zones], np.float64)
    tries = 0
    while len(out) < n + len(taken) and tries < 4000:
        tries += 1
        fn = zones[rng.choice(len(zones), p=ws / ws.sum())][1]
        p = fn()
        r = float(np.clip(np.exp(rng.normal(math.log(0.0055), 0.6)), 0.002, 0.015)) / 2
        if all(np.linalg.norm(p - q) > (r + rq) * 1.15 + 0.004 for q, rq, _ in out):
            out.append((p, r, rng.uniform(0.7, 1.0)))
    return out[len(taken):]


def gauss(c, centers, sig_m):
    """가우시안 덩어리 합 (붉은기 등) -> float."""
    N = c.N
    X, Y = grid_xy(c)
    out = np.zeros((N, N), np.float32)
    for p, s, w in centers:
        out = np.maximum(out, w * np.exp(-((X - p[0]) ** 2 + (Y - p[1]) ** 2) / (2 * (s * sig_m) ** 2)))
    return out


def wrinkles(c, dr, ctr, axis, n, spacing, hw, rng, width=0.00018, bow=0.45):
    """관절 주위 동심 주름 (괄호 모양 호). axis = 손가락 방향 2D."""
    a = unit(axis)
    b = perp(a)
    for k in range(-n, n + 1):
        ak = k * spacing * rng.uniform(0.8, 1.2)
        env = math.sqrt(max(0.05, 1 - (k / (n + 0.8)) ** 2))
        h = hw * env * rng.uniform(0.75, 1.05)
        ts = np.linspace(-1, 1, 28)
        # 선 일부를 끊어 자연스럽게
        cut = rng.uniform(-0.6, 0.6) if rng.random() < 0.45 else None
        seg = []
        for t in ts:
            if cut is not None and abs(t - cut) < 0.09:
                if len(seg) > 1:
                    stroke(c, dr, seg, width * rng.uniform(0.8, 1.3), taper=True)
                seg = []
                continue
            bb = t * h
            aa = ak * (1 - bow * t * t) + rng.normal(0, spacing * 0.06)
            seg.append(v2(ctr) + a * aa + b * bb)
        if len(seg) > 1:
            stroke(c, dr, seg, width * rng.uniform(0.8, 1.3), taper=True)


def fbm(rng, N, cells):
    return (_value_noise(rng, N, cells) + 0.5 * _value_noise(rng, N, cells * 2) + 0.25 * _value_noise(rng, N, cells * 4)) / 1.75


def creases(c, rng, ang, spacing, width, warp=1.0, gaps=0.42):
    """ang(rad) 쪽으로 쌓이는 주름 결 -> float. 등치선을 잡음으로 휘고, 줄마다 세기를 달리 하고, 군데군데 끊는다."""
    X, Y = grid_xy(c)
    u = (X * math.sin(ang) + Y * math.cos(ang)) / spacing + warp * (4 * (fbm(rng, c.N, 14) - 0.5) + 0.7 * (fbm(rng, c.N, 44) - 0.5))
    k = np.round(u)
    d = np.abs(u - k) * spacing
    w = width * (0.55 + 0.9 * fbm(rng, c.N, 26))
    power = rng.uniform(0.35, 1.0, 1024).astype(np.float32)[k.astype(np.int64) % 1024]
    return np.exp(-(d / w) ** 2) * power * sstep(gaps - 0.08, gaps + 0.08, fbm(rng, c.N, 34))


def save16(arr, path):
    a = np.clip(arr, 0, 1)
    Image.fromarray((a * 65535).astype(np.uint16)).save(path)


def save_rgb(chs, path):
    a = np.stack([np.clip(x, 0, 1) for x in chs], -1)
    Image.fromarray((a * 255).astype(np.uint8), 'RGB').save(path)


# ------------------------------------------------------------------ 손등 (top)

def paint_top(cfg, mp, rng, out, tag):
    c = Canvas(mp['N'], mp['S'], mp['x0'], mp['y0'])
    J = {k: v2(v) for k, v in mp['j'].items()}
    rs = cfg['rs']
    F = ['index', 'middle', 'ring', 'pinky']
    K = {f: J[f + '-finger-phalanx-proximal'] for f in F}  # MCP (너클)
    P = {f: J[f + '-finger-phalanx-intermediate'] for f in F}  # PIP
    D = {f: J[f + '-finger-phalanx-distal'] for f in F}  # DIP
    T = {f: J[f + '-finger-tip'] for f in F}
    T1 = J['thumb-phalanx-proximal']
    X = lambda x, y: v2((rs * x, y))
    mid = lambda a, b: (a + b) / 2
    W = cfg['wrinkle']

    # 정맥 (손등 정맥망)
    veins = [
        ([mid(K['index'], T1) + v2((0, 0.012)), X(0.027, -0.036), X(0.024, -0.006), X(0.020, 0.03)], 0.0017),
        ([mid(K['index'], K['middle']) + v2((0, 0.011)), X(0.012, -0.052), X(0.022, -0.034)], 0.0014),
        ([mid(K['middle'], K['ring']) + v2((0, 0.011)), X(-0.003, -0.056), X(-0.009, -0.041)], 0.0013),
        ([mid(K['ring'], K['pinky']) + v2((0, 0.009)), X(-0.022, -0.052), X(-0.026, -0.02), X(-0.022, 0.03)], 0.0016),
        ([X(-0.024, -0.043), X(-0.009, -0.040), X(0.007, -0.045), X(0.023, -0.033)] if not W else
         [X(-0.026, -0.034), X(-0.012, -0.044), X(0.003, -0.038), X(0.015, -0.044), X(0.026, -0.03)], 0.0015),  # 일직선이면 고무줄 자국처럼 보인다
    ]
    twigs = [
        [X(-0.004, -0.058), K['middle'] + v2((0, 0.017))],
        [X(0.013, -0.054), mid(K['index'], T1) + v2((rs * -0.004, 0.02))],
        [X(-0.018, -0.047), X(-0.016, -0.03), X(-0.012, -0.012)],
        [X(0.006, -0.044), X(0.004, -0.025), X(0.008, -0.004)],
    ]
    GY = grid_xy(c)[1]
    ky = float(np.mean([K[f][1] for f in F]))
    vfade = sstep(ky + 0.008, ky + 0.03, GY)  # 정맥은 너클 앞에서 사라진다
    vh, vd = c.layer()
    vt, vtd = c.layer()
    for pts, r in veins:
        sp = wobble(spline(pts), rng, 0.0016, 0.022)
        stroke(c, vd, sp, 2 * r * 1.1)
        stroke(c, vtd, sp, 2 * r * 1.5)
    vH = c.done(vh, 0.0022) * vfade  # 넓고 낮은 둥근 단면 (흰 줄 반사 방지)
    th, thd = c.layer()
    for pts in twigs:
        sp = wobble(spline(pts), rng, 0.001, 0.014)
        stroke(c, thd, sp, 0.0014, taper=True)
        stroke(c, vtd, sp, 0.002, val=130, taper=True)
    tH = c.done(th, 0.0012) * vfade
    vM = c.done(vt, 0.0016) * vfade  # 색 마스크: 부드럽게 블러

    # 힘줄 (손목 -> 너클): 한 획으로 그리고 양끝은 가늘게 (구슬 모양 마디 방지)
    tdh, tdd = c.layer()
    for i, f in enumerate(F):
        a = X(0.004 - i * 0.004, 0.006)
        b = K[f] + v2((0, 0.013))
        stroke(c, tdd, [a + (b - a) * t for t in np.linspace(0.08, 1, 14)], 0.0032, taper=True)
    tdH = c.done(tdh, 0.0022)

    # 관절 주름 (경계는 가우시안·노이즈 엔벨로프로 흐린다)
    wh, wd = c.layer()
    for f in F:
        ax = P[f] - K[f]
        wrinkles(c, wd, P[f] + unit(ax) * -0.001, ax, 4, 0.00115, 0.0068, rng)
        wrinkles(c, wd, D[f] + unit(T[f] - D[f]) * -0.0005, T[f] - D[f], 3, 0.00085, 0.0054, rng, width=0.00015)
        wrinkles(c, wd, K[f] + unit(ax) * 0.003, ax, 2, 0.0019, 0.0072, rng, width=0.00022, bow=0.3)
    env = gauss(c, [(P[f] - unit(P[f] - K[f]) * 0.001, 1.0, 1.0) for f in F] + [(D[f], 0.75, 0.9) for f in F]
                + [(K[f] + unit(P[f] - K[f]) * 0.003, 1.05, 0.8) for f in F], 0.0034)
    env = np.clip(env * (0.45 + 1.0 * _value_noise(rng, c.N, 60)), 0, 1)
    wJ = c.done(wh, 0.00006) * env
    wh, wd = c.layer()
    # 손등 잔주름 (가로 방향 짧은 선)
    for _ in range(1300):
        y = rng.uniform(-0.105, 0.03)
        x = rng.uniform(-0.04, 0.042) * rs
        p = v2((x, y))
        # 손가락 위라면 손가락 축 기준, 아니면 손 축 기준
        ang = math.pi / 2 + rng.normal(0, 0.28)
        L = rng.uniform(0.0018, 0.0055)
        d = v2((math.cos(ang), math.sin(ang)))  # 가로 = 손가락에 수직
        d = perp(d)
        pts = [p + d * L * t + perp(d) * 0.0003 * math.sin(t * 3.1) for t in np.linspace(-0.5, 0.5, 6)]
        stroke(c, wd, pts, rng.uniform(0.00009, 0.00016), val=int(rng.uniform(90, 200)), taper=True)
    wH = wJ + 0.7 * c.done(wh, 0.00006) * (0.5 + 0.5 * _value_noise(rng, c.N, 30))

    # 검버섯 (노인성 흑자): 9~13개, 손등 중수골·손목에 몰리고 손가락엔 0~2개, 포아송 배치
    xs = sorted(K[f][0] for f in F)
    xa, xb = xs[0] - 0.002, xs[-1] + 0.002
    zones = [(0.62, lambda: v2((rng.uniform(xa, xb), rng.uniform(ky + 0.016, -0.004)))),  # 손등 중수골
             (0.30, lambda: v2((rng.uniform(xa + 0.006, xb - 0.006), rng.uniform(-0.004, 0.03))))]  # 손목
    big = place_spots(rng, zones[:1], 1)
    big = [(p, rng.uniform(0.0045, 0.0065), rng.uniform(0.9, 1.0)) for p, _, _ in big]  # 큰 일광흑자 1개
    pts = big + place_spots(rng, zones, int(rng.integers(8, 12)), big)
    for _ in range(int(rng.integers(0, 3))):  # 손가락 기절: 중심선에서 비켜서
        f = F[rng.integers(0, 4)]
        a_ = unit(P[f] - K[f])
        pts.append((K[f] + a_ * rng.uniform(0.25, 0.75) * np.linalg.norm(P[f] - K[f]) + perp(a_) * rng.uniform(0.0015, 0.0035)
                    * rng.choice([-1, 1]), rng.uniform(0.001, 0.0018), rng.uniform(0.5, 0.8)))
    sM = spots(c, rng, pts)
    # 지루각화 1개 (약간 솟은 갈색 각질)
    p = v2((rng.uniform(xa + 0.01, xb - 0.01), rng.uniform(ky + 0.03, -0.02)))
    kM = spots(c, rng, [(p, rng.uniform(0.0016, 0.0022), 0.9)])

    # 붉은기 (너클, 관절, 손톱 주위)
    red = gauss(c, [(K[f], 1.0, 0.6) for f in F] + [(P[f], 0.75, 0.75) for f in F] + [(D[f], 0.6, 0.55) for f in F]
                + [(D[f] + (T[f] - D[f]) * 0.42, 0.45, 0.5) for f in F], 0.0055)

    # 털 (흰 털 위주, 손목·손등 근위부 + 손가락 기절)
    hl, hld = c.layer()
    hd, hdd = c.layer()
    for i in range(520):
        if rng.random() < 0.75:
            p = v2((rs * rng.uniform(-0.03, 0.03), rng.uniform(-0.05, 0.06)))
            base = math.atan2(-0.9, -rs * 0.42)
        else:
            f = F[rng.integers(0, 4)]
            p = K[f] + (P[f] - K[f]) * rng.uniform(0.15, 0.6) + perp(unit(P[f] - K[f])) * rng.normal(0, 0.002)
            ax = unit(P[f] - K[f])
            base = math.atan2(ax[1], ax[0])
        ang = base + rng.normal(0, 0.3)
        d = v2((math.cos(ang), math.sin(ang)))
        L = rng.uniform(0.002, 0.0055)
        bend = rng.normal(0, 0.0006)
        pts = [p + d * L * t + perp(d) * bend * t * t for t in np.linspace(0, 1, 5)]
        if rng.random() < 0.72:
            stroke(c, hld, pts, 0.00009, val=int(rng.uniform(150, 255)))
        else:
            stroke(c, hdd, pts, 0.00008, val=int(rng.uniform(120, 220)))
    hL = c.done(hl)
    hD = c.done(hd)

    # 오래된 흉터 하나 (작은 베인 자국)
    sc, scd = c.layer()
    p = v2((rs * rng.uniform(0.005, 0.02), rng.uniform(-0.07, -0.05)))
    ang = rng.uniform(0.3, 1.2)
    d = v2((math.cos(ang), math.sin(ang)))
    stroke(c, scd, [p + d * t for t in np.linspace(0, 0.009, 8)], 0.0006, taper=True)
    scM = c.done(sc, 0.0002)

    H = (0.5 + 0.11 * vH + 0.035 * tH + 0.06 * tdH - 0.035 * wH + 0.004 * sM + 0.04 * kM + 0.01 * (hL + hD) + 0.012 * scM)

    # 게임 거리(1픽셀 약 0.55mm)에서 남는 주름과 얼룩. 위 잔주름은 0.2mm 이하라 밉맵에서 사라진다
    if W:
        q = np.random.default_rng(cfg['seed'] + 500)  # 위의 정맥과 점 자리를 바꾸지 않는다
        jh, jd = c.layer()
        for f in F:
            ax = P[f] - K[f]
            wrinkles(c, jd, P[f] - unit(ax) * 0.0008, ax, 4, 0.0022, 0.0082, q, width=0.00072)
            wrinkles(c, jd, D[f] - unit(T[f] - D[f]) * 0.0005, T[f] - D[f], 3, 0.0018, 0.0068, q, width=0.0006)
            wrinkles(c, jd, K[f] + unit(ax) * 0.004, ax, 3, 0.003, 0.009, q, width=0.0008, bow=0.3)
        jenv = gauss(c, [(P[f], 1.0, 1.0) for f in F] + [(D[f], 0.75, 0.9) for f in F]
                     + [(K[f] + unit(P[f] - K[f]) * 0.004, 1.1, 0.85) for f in F], 0.0062)
        joints = c.done(jh, 0.00016) * np.clip(jenv * (0.7 + 0.7 * fbm(q, c.N, 40)), 0, 1)
        folds = creases(c, q, 0.2 * rs, 0.0052, 0.00068, gaps=0.46)  # 손등 가로 큰 결
        cross = np.maximum(creases(c, q, 0.95 * rs, 0.0018, 0.00022, warp=1.6, gaps=0.5), creases(c, q, -0.85 * rs, 0.002, 0.00022, warp=1.6, gaps=0.5))  # 마름모 잔결
        wrist = creases(c, q, 0.03 * rs, 0.0062, 0.0007, warp=0.3, gaps=0.3) * sstep(-0.01, 0.002, GY) * (1 - sstep(0.02, 0.032, GY))  # 깊은 주름 몇 줄
        crepe = np.maximum(0.8 * folds, 0.3 * cross) * (0.55 + 0.9 * fbm(q, c.N, 10))
        crepe *= 1 - 0.55 * (1 - sstep(ky - 0.008, ky + 0.004, GY)) - 0.25 * sstep(-0.012, 0.006, GY)  # 손가락과 손목은 약하게: 줄무늬처럼 보인다
        H -= 0.06 * joints + 0.055 * np.clip(crepe, 0, 1) + 0.05 * wrist
        H += 0.12 * vH + 0.05 * tdH  # 살이 빠져 정맥과 힘줄이 도드라진다
        # 검버섯은 새로 찍는다. 비슷한 점이 고르게 흩어지면 때처럼 보여 크기를 섞고 세 곳에 몰고 윤곽을 살린다
        hub = [X(0.017, -0.032), X(-0.019, -0.058), X(-0.002, -0.004)]
        sM = (0.6 + 0.4 * sstep(0.35, 0.6, fbm(q, c.N, 70))) * sstep(0.05, 0.7, spots(c, q, [(hub[i % 3] + q.normal(0, 0.01, 2), q.uniform(0.005, 0.0085) if i < 4 else q.uniform(0.0015, 0.0035),
                                                                                   q.uniform(0.85, 1.0)) for i in range(11)]))
        red = np.maximum(red, 0.25 * sstep(0.48, 0.66, fbm(q, c.N, 16)))
        vM = sstep(0.1, 0.9, c.done(vh, 0.0012)) * vfade  # 넓은 색 번짐 대신 정맥 위로만
    save16(H, os.path.join(out, f'{tag}_top_h.png'))
    save_rgb([vM if W else np.maximum(vM, vH * 0.8), np.maximum(sM, kM * 0.7), red], os.path.join(out, f'{tag}_top_m.png'))
    save_rgb([hL, hD, np.maximum(scM, kM * 0.8)], os.path.join(out, f'{tag}_top_n.png'))


# ------------------------------------------------------------------ 손바닥 (bot)

def paint_bot(cfg, mp, rng, out, tag):
    c = Canvas(mp['N'], mp['S'], mp['x0'], mp['y0'])
    J = {k: v2(v) for k, v in mp['j'].items()}
    rs = cfg['rs']
    F = ['index', 'middle', 'ring', 'pinky']
    K = {f: J[f + '-finger-phalanx-proximal'] for f in F}
    P = {f: J[f + '-finger-phalanx-intermediate'] for f in F}
    D = {f: J[f + '-finger-phalanx-distal'] for f in F}
    T = {f: J[f + '-finger-tip'] for f in F}
    T1 = J['thumb-phalanx-proximal']
    X = lambda x, y: v2((rs * x, y))
    ch, cd = c.layer()
    S0 = K['index'] + (T1 - K['index']) * 0.35 + v2((0, 0.012))
    major = [
        [S0, X(0.011, -0.05), X(0.006, -0.028), X(0.004, -0.008), X(0.006, 0.004)],  # 생명선
        [S0, X(0.016, -0.067), X(-0.002, -0.063), X(-0.024, -0.055)],  # 두뇌선
        [X(-0.042, -0.064), X(-0.018, -0.073), X(0.004, -0.079), X(0.011, -0.087)],  # 감정선
        [X(-0.024, 0.004), X(0.0, 0.006), X(0.024, 0.004)],  # 손목 주름
        [X(-0.022, 0.011), X(0.0, 0.0125), X(0.022, 0.011)],
    ]
    for pts in major:
        stroke(c, cd, wobble(spline(pts), rng, 0.0006, 0.012), 0.00042, taper=True)
    for _ in range(170):  # 잔금
        p = v2((rs * rng.uniform(-0.035, 0.03), rng.uniform(-0.085, 0.005)))
        ang = rng.uniform(0, math.pi)
        d = v2((math.cos(ang), math.sin(ang)))
        L = rng.uniform(0.002, 0.008)
        stroke(c, cd, [p + d * L * t for t in np.linspace(-0.5, 0.5, 5)], 0.00016, val=int(rng.uniform(90, 200)), taper=True)
    # 손가락 마디 주름
    for f in F:
        a = unit(P[f] - K[f])
        b = perp(a)
        hw = 0.0078 if f != 'pinky' else 0.0064
        for ctr, w in [(K[f] + a * 0.02, hw), (P[f] - a * 0.0012, hw * 0.92), (P[f] + a * 0.0016, hw * 0.92)]:
            pts = [ctr + b * t * w + a * 0.0012 * t * t for t in np.linspace(-1, 1, 12)]
            stroke(c, cd, pts, 0.00045, taper=True)
        a2 = unit(T[f] - D[f])
        b2 = perp(a2)
        pts = [D[f] + b2 * t * hw * 0.82 + a2 * 0.001 * t * t for t in np.linspace(-1, 1, 12)]
        stroke(c, cd, pts, 0.0004, taper=True)
    cH = c.done(ch, 0.00012)
    cM = c.done(ch, 0.0005)
    # 지문 (손끝 동심 타원)
    fh, fd = c.layer()
    pads = []
    for f in F:
        a = unit(T[f] - D[f])
        b = perp(a)
        L = np.linalg.norm(T[f] - D[f])
        ctr = D[f] + a * (0.62 * L)
        pads.append(ctr)
        for k in range(1, 15):
            r = k * 0.00046
            pts = [ctr + a * math.cos(t) * r * 1.25 + b * math.sin(t) * r for t in np.linspace(0, 6.3, 40)]
            stroke(c, fd, pts, 0.00011)
    fH = c.done(fh, 0.00004)
    padm = gauss(c, [(p, 1.0, 0.8) for p in pads] + [(K[f] - unit(P[f] - K[f]) * 0.004, 1.2, 0.35) for f in F], 0.0055)
    calm = gauss(c, [(K[f] - unit(P[f] - K[f]) * 0.006, 0.8, 0.7) for f in ('index', 'middle', 'ring')], 0.005)
    H = 0.5 - 0.09 * cH - 0.012 * fH + 0.02 * calm
    save16(H, os.path.join(out, f'{tag}_bot_h.png'))
    save_rgb([cM, padm, calm], os.path.join(out, f'{tag}_bot_m.png'))


# ------------------------------------------------------------------ 엄지 등 (thumb)

def paint_thumb(cfg, mp, rng, out, tag):
    c = Canvas(mp['N'], mp['S'], mp['x0'], mp['y0'])
    J = {k: v2(v) for k, v in mp['j'].items()}
    M, I, T = J['thumb-phalanx-proximal'], J['thumb-phalanx-distal'], J['thumb-tip']
    wh, wd = c.layer()
    wrinkles(c, wd, I - unit(T - I) * 0.0008, T - I, 4, 0.0012, 0.0075, rng)
    wrinkles(c, wd, M + unit(I - M) * 0.002, I - M, 2, 0.0018, 0.008, rng, width=0.0002, bow=0.3)
    for _ in range(160):
        p = M + (I - M) * rng.uniform(-0.6, 1.0) + v2(rng.normal(0, 0.004, 2))
        a = unit(I - M)
        d = perp(a)
        rot = rng.normal(0, 0.25)
        d = v2((d[0] * math.cos(rot) - d[1] * math.sin(rot), d[0] * math.sin(rot) + d[1] * math.cos(rot)))
        L = rng.uniform(0.002, 0.005)
        stroke(c, wd, [p + d * L * t for t in np.linspace(-0.5, 0.5, 5)], 0.00012, val=int(rng.uniform(90, 190)), taper=True)
    env = gauss(c, [(I - unit(T - I) * 0.0008, 1.0, 1.0), (M + unit(I - M) * 0.002, 1.0, 0.8)], 0.0038)
    wH = c.done(wh, 0.00006) * np.clip(env * (0.45 + 1.0 * _value_noise(rng, c.N, 30)) + 0.35, 0, 1)
    pts = [] if rng.random() < 0.4 else [(M + (I - M) * rng.uniform(-0.6, -0.1) + v2(rng.normal(0, 0.002, 2)),
                                          rng.uniform(0.0012, 0.0022), rng.uniform(0.5, 0.8))]
    sM = spots(c, rng, pts)
    red = gauss(c, [(I, 0.8, 0.75), (M, 1.0, 0.5), (I + (T - I) * 0.4, 0.5, 0.5)], 0.0055)
    hl, hld = c.layer()
    for _ in range(40):
        p = M + (I - M) * rng.uniform(-0.7, 0.3) + v2(rng.normal(0, 0.003, 2))
        a = unit(I - M)
        ang = math.atan2(a[1], a[0]) + rng.normal(0, 0.3)
        d = v2((math.cos(ang), math.sin(ang)))
        stroke(c, hld, [p + d * rng.uniform(0.002, 0.004) * t for t in np.linspace(0, 1, 4)], 0.00009,
               val=int(rng.uniform(150, 255)))
    hL = c.done(hl)
    H = 0.5 - 0.035 * wH + 0.004 * sM + 0.01 * hL
    if cfg['wrinkle']:  # paint_top 과 같은 굵기
        q = np.random.default_rng(cfg['seed'] + 501)
        jh, jd = c.layer()
        wrinkles(c, jd, I - unit(T - I) * 0.0008, T - I, 6, 0.0017, 0.009, q, width=0.00062)
        wrinkles(c, jd, M + unit(I - M) * 0.002, I - M, 4, 0.0026, 0.0095, q, width=0.0007, bow=0.3)
        jenv = gauss(c, [(I, 1.0, 1.0), (M + unit(I - M) * 0.002, 1.1, 0.85)], 0.0062)
        ang = math.atan2((I - M)[0], (I - M)[1])
        H -= (0.085 * c.done(jh, 0.00016) * np.clip(jenv * (0.7 + 0.7 * fbm(q, c.N, 20)), 0, 1)
              + 0.04 * creases(c, q, ang, 0.0028, 0.00034))
    save16(H, os.path.join(out, f'{tag}_thumb_h.png'))
    save_rgb([np.zeros_like(H), sM, red], os.path.join(out, f'{tag}_thumb_m.png'))
    save_rgb([hL, np.zeros_like(H), np.zeros_like(H)], os.path.join(out, f'{tag}_thumb_n.png'))


# ------------------------------------------------------------------ 뜨개 타일

def _value_noise(rng, N, cells):
    g = rng.random((cells + 1, cells + 1)).astype(np.float32)
    g[-1, :], g[:, -1] = g[0, :], g[:, 0]
    t = np.linspace(0, cells, N, endpoint=False)
    i = t.astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    a = g[i][:, i] * (1 - f)[None, :] + g[i][:, i + 1] * f[None, :]
    b = g[i + 1][:, i] * (1 - f)[None, :] + g[i + 1][:, i + 1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def knit_tile(out, rng, N=1024, cols=16, rows=20, rib=False):
    """메리야스(knit) / 2x2 고무단(rib) 타일. 높이 -> 노멀(OpenGL), 색(헤더 원사), 거칠기. (주기 경계 이음매 없음)"""
    w, h = N / cols, N / rows
    H = np.zeros((N, N), np.float32)
    fib = np.zeros((N, N), np.float32)

    def put(x0, y0, x1, y1, rad, hmax, purl):
        xa, xb = int(math.floor(min(x0, x1) - rad)), int(math.ceil(max(x0, x1) + rad))
        ya, yb = int(math.floor(min(y0, y1) - rad)), int(math.ceil(max(y0, y1) + rad))
        ix, iy = np.arange(xa, xb + 1), np.arange(ya, yb + 1)
        X, Y = np.meshgrid(ix.astype(np.float32), iy.astype(np.float32))
        vx, vy = x1 - x0, y1 - y0
        L2 = max(1e-6, vx * vx + vy * vy)
        t = np.clip(((X - x0) * vx + (Y - y0) * vy) / L2, 0, 1)
        px, py = x0 + t * vx - X, y0 + t * vy - Y
        d = np.sqrt(px * px + py * py) / rad
        prof = hmax * np.sqrt(np.clip(1 - d * d, 0, 1)) * (0.8 + 0.2 * np.sin(t * math.pi))
        tw = 0.5 + 0.5 * np.sin((t * (3 if purl else 9) + (px * vy - py * vx) / math.sqrt(L2) / rad * 1.5) * math.pi)
        sel = np.ix_(iy % N, ix % N)
        cur = H[sel]
        m = prof > cur
        H[sel] = np.where(m, prof, cur)
        fib[sel] = np.where(m, tw, fib[sel])

    for j in range(-1, rows + 1):
        for i in range(cols):
            cx = (i + 0.5) * w
            if rib and (i % 4) >= 2:  # 안뜨기 = 가로 혹
                cy = (j + 0.5) * h
                put(cx - 0.32 * w, cy, cx + 0.32 * w, cy, 0.36 * h, 0.55, True)
                continue
            for s in (-1, 1):
                put(cx + s * 0.44 * w, (j - 0.15) * h, cx + s * 0.04 * w, (j + 1.05) * h, 0.27 * w, 1.0, False)
    if rib:  # 고무단: 겉뜨기 열을 높게
        col = ((np.arange(N) / w).astype(int) % 4) < 2
        H = np.where(col[None, :], H + 0.25, H * 0.75)
    fuzz = _value_noise(rng, N, 128) * 0.5 + _value_noise(rng, N, 256) * 0.5
    H = H * (0.88 + 0.12 * fib) + 0.04 * fuzz
    H = (H - H.min()) / (H.max() - H.min())
    # 노멀 (OpenGL: G = +Y 위)
    k = 5.0
    gx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) * 0.5 * k
    gy = (np.roll(H, 1, 0) - np.roll(H, -1, 0)) * 0.5 * k  # 이미지 행은 아래로 증가
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    nor = np.stack([-gx * nz, -gy * nz, nz], -1) * 0.5 + 0.5
    # 색: 따뜻한 회갈색 헤더(멜란지) 원사
    heather = _value_noise(rng, N, 64)
    fl = rng.random((N, N)).astype(np.float32)
    fl = np.asarray(Image.fromarray((fl * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    base = np.array([96, 85, 76], np.float32)
    light = np.array([150, 138, 122], np.float32)
    dark = np.array([52, 45, 40], np.float32)
    C = base[None, None] * np.ones((N, N, 1), np.float32)
    lm = np.clip((fl - 0.53) * 9, 0, 1)[..., None] * (0.55 + 0.45 * heather[..., None])
    dm = np.clip((0.47 - fl) * 9, 0, 1)[..., None] * 0.6
    C = C * (1 - lm) + light * lm
    C = C * (1 - dm) + dark * dm
    # 고무단: 골·마루 명도차 10% 이하 (입체감은 노멀/AO 로), 몸판은 기존 대비
    ao = ((0.93 + 0.07 * H) if rib else (0.55 + 0.45 * H))[..., None]
    C = C * ao * ((0.98 + 0.03 * fib[..., None]) if rib else (0.94 + 0.12 * fib[..., None]))
    R = np.clip(0.97 - 0.07 * H, 0, 1)
    nm = 'rib' if rib else 'knit'
    Image.fromarray(np.clip(C, 0, 255).astype(np.uint8), 'RGB').save(os.path.join(out, f'{nm}_diff.png'))
    Image.fromarray((nor * 255).astype(np.uint8), 'RGB').save(os.path.join(out, f'{nm}_nor.png'))
    Image.fromarray((R * 255).astype(np.uint8), 'L').save(os.path.join(out, f'{nm}_rough.png'))
    save16(H, os.path.join(out, f'{nm}_h.png'))


# ------------------------------------------------------------------ 시계 문자판

def dial(out, rng, N=1024):
    """샴페인 실버 선버스트 문자판, 바 인덱스, 로고(가상 브랜드), 요일·날짜 창(토 15)."""
    S = N * 2
    cx = cy = S / 2
    R = S / 2
    ys, xs = np.mgrid[0:S, 0:S].astype(np.float32)
    dx, dy = xs - cx, ys - cy
    r = np.sqrt(dx * dx + dy * dy) / R
    ang = np.arctan2(dy, dx)
    burst = 0.5 + 0.5 * np.sin(ang * 360 + np.sin(ang * 7) * 2)
    burst = burst * 0.5 + 0.5 * (0.5 + 0.5 * np.sin(ang * 1800 + r * 3))
    shade = 0.92 + 0.08 * np.cos(ang - 0.9)  # 선버스트 빛 방향
    base = np.array([214, 204, 182], np.float32)
    C = base[None, None] * (shade * (0.94 + 0.06 * burst))[..., None]
    C *= (1 - 0.18 * np.clip((r - 0.86) / 0.14, 0, 1) ** 2)[..., None]  # 가장자리 어둡게
    im = Image.fromarray(np.clip(C, 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(im)
    P = lambda a, rr: (cx + math.sin(a) * rr * R, cy - math.cos(a) * rr * R)
    # 분 눈금
    for k in range(60):
        a = k / 60 * 2 * math.pi
        if k % 5:
            d.line([P(a, 0.90), P(a, 0.955)], fill=(70, 66, 60), width=max(2, S // 420))
    # 아플라이드 바 인덱스 (그림자 + 금속 + 하이라이트)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        if k == 3:
            continue
        ws = [-0.018, 0.018] if k == 0 else [0]
        for wo in ws:
            w = 0.022 * R
            r0, r1 = 0.66, 0.86
            for sh, col in ((0.007, (120, 112, 98)), (0, (60, 58, 56)), (-0.003, (235, 235, 232))):
                q = [P(a, r0), P(a, r1)]
                off = (math.cos(a) * (wo * R) + sh * R, math.sin(a) * (wo * R) + sh * R)
                d.line([(q[0][0] + off[0], q[0][1] + off[1]), (q[1][0] + off[0], q[1][1] + off[1])],
                       fill=col, width=int(w if col != (235, 235, 232) else w * 0.45))
    # 요일·날짜 창 (3시)
    wx0, wx1 = cx + 0.56 * R, cx + 0.86 * R
    wy0, wy1 = cy - 0.075 * R, cy + 0.075 * R
    d.rectangle([wx0 - 6, wy0 - 6, wx1 + 6, wy1 + 6], fill=(150, 140, 120))
    d.rectangle([wx0, wy0, wx1, wy1], fill=(246, 244, 236))
    d.line([(wx0 + (wx1 - wx0) * 0.46, wy0), (wx0 + (wx1 - wx0) * 0.46, wy1)], fill=(150, 140, 120), width=5)
    kf = ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc', int(0.105 * R), index=6)
    nf = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', int(0.115 * R)) \
        if os.path.exists('/System/Library/Fonts/Supplemental/Arial Bold.ttf') else kf
    d.text((wx0 + (wx1 - wx0) * 0.23, cy), '토', font=kf, fill=(190, 30, 30), anchor='mm')
    d.text((wx0 + (wx1 - wx0) * 0.73, cy + 2), '15', font=nf, fill=(20, 20, 20), anchor='mm')
    # 로고·문구 (가상 브랜드)
    lf = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf', int(0.115 * R)) \
        if os.path.exists('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf') else kf
    sf = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', int(0.055 * R)) \
        if os.path.exists('/System/Library/Fonts/Supplemental/Arial.ttf') else kf
    d.text((cx, cy - 0.40 * R), 'ARIRANG', font=lf, fill=(40, 38, 36), anchor='mm')
    d.text((cx, cy - 0.29 * R), 'AUTOMATIC  21 JEWELS', font=sf, fill=(70, 66, 60), anchor='mm')
    d.text((cx, cy + 0.36 * R), 'WATER RESIST', font=sf, fill=(70, 66, 60), anchor='mm')
    d.text((cx, cy + 0.93 * R), 'MADE IN KOREA', font=ImageFont.truetype(sf.path, int(0.03 * R)) if hasattr(sf, 'path') else sf,
           fill=(90, 86, 80), anchor='mm')
    # 세월: 누런 얼룩, 먼지
    a = np.asarray(im, np.float32)
    stain = _value_noise(rng, S, 12)
    a *= (1 - 0.08 * np.clip(stain - 0.55, 0, 1) * 3)[..., None]
    a[..., 2] *= 0.97
    for _ in range(90):
        x, y = rng.uniform(0, S, 2)
        rr = rng.uniform(1, 3.5)
        yy, xx = int(y), int(x)
        a[max(0, yy - 2):yy + 2, max(0, xx - 2):xx + 2] *= rng.uniform(0.7, 0.9)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGB').resize((N, N), Image.LANCZOS)
    im.save(os.path.join(out, 'dial.png'))


def main():
    cfg = json.load(open(sys.argv[1]))
    out = cfg['out']
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(cfg['seed'])
    tag = cfg['side']
    mp = cfg['maps']
    paint_top(cfg, mp['top'], rng, out, tag)
    paint_bot(cfg, mp['bot'], rng, out, tag)
    paint_thumb(cfg, mp['thumb'], rng, out, tag)
    if cfg.get('knit'):
        knit_tile(out, np.random.default_rng(7))
        knit_tile(out, np.random.default_rng(8), rib=True)
    if cfg.get('dial'):
        dial(out, np.random.default_rng(9))
    print('tex done', tag)


if __name__ == '__main__':
    main()

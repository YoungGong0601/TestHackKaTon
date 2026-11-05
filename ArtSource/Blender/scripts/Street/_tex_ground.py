"""Street 바닥류 2D 텍스처 (점자블록·노랑 도료·맨홀 양각). venv python:  python -I _tex_ground.py <출력폴더>"""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _textures as T  # noise / font (OUT 은 argv[1])

OUT = T.OUT
CACHE = T.CACHE


def save_rgb(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, name))


def normal_from_height(h, px_m, height_m, name):
    """높이(0..1) -> OpenGL 노멀 PNG. px_m = 픽셀 크기(m), height_m = h=1 의 실제 높이."""
    hh = h * height_m
    gy, gx = np.gradient(hh, px_m)  # gy: 행(아래) 방향
    n = np.dstack([-gx, gy, np.ones_like(hh)])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    save_rgb(n * 0.5 + 0.5, name)


def blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255


# ------------------------------------------------------------------ 점자블록 (300 mm 블록 2x2 = 0.6 m 타일)
def tactile(kind, S=1024, seed=1):
    B = S // 2                      # 블록 1장 = 512 px = 300 mm
    mm = B / 300.0
    hm = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(hm)
    for by in range(2):
        for bx in range(2):
            x0, y0 = bx * B, by * B
            if kind == "line":      # 선형: 돌기 4줄 (폭 35 mm, 길이 270 mm, 간격 75 mm), U 방향
                for k in range(4):
                    cy = y0 + (37.5 + 75 * k) * mm
                    d.rounded_rectangle([x0 + 15 * mm, cy - 15 * mm, x0 + 285 * mm, cy + 15 * mm], radius=15 * mm,
                                        fill=255)
            else:                   # 점형: 6x6 돌기 (피치 50 mm, 지름 30 mm)
                for j in range(6):
                    for i in range(6):
                        cx, cy = x0 + (25 + 50 * i) * mm, y0 + (25 + 50 * j) * mm
                        d.ellipse([cx - 15 * mm, cy - 15 * mm, cx + 15 * mm, cy + 15 * mm], fill=255)
    h = np.asarray(hm, np.float32) / 255
    h = blur(h, 3.2 * mm) * 0.6 + blur(h, 1.2 * mm) * 0.4   # 돌기 옆면 경사
    # 블록 사이 줄눈 (폭 4 mm, 깊이)
    j = np.ones((S, S), np.float32)
    for k in range(3):
        lo, hi = max(0, int(k * B - 2.5 * mm)), min(S, int(k * B + 2.5 * mm))
        j[lo:hi, :] = 0
        j[:, lo:hi] = 0
    j = blur(j, 1.5 * mm)
    grain = T.noise(S, S, 6, seed + 3, 3)
    h_all = 0.25 + 0.75 * h - (1 - j) * 0.22 + (grain - 0.5) * 0.03
    normal_from_height(h_all, 0.6 / S, 0.006, f"tactile_{kind}_nor.png")
    # 색: 바랜 노랑 + 블록별 색차 + 돌기 사이 흙때 + 줄눈 검정 + 신발 자국
    rng = np.random.default_rng(seed)
    blk = np.zeros((S, S, 1), np.float32)
    for by in range(2):
        for bx in range(2):
            blk[by * B:(by + 1) * B, bx * B:(bx + 1) * B] = rng.uniform(-0.06, 0.06)
    base = np.array([0.86, 0.62, 0.10]) * (1 + blk)
    n1 = T.noise(S, S, 140, seed + 5, 5)[..., None]
    n2 = T.noise(S, S, 30, seed + 6, 4)[..., None]
    col = base * (0.86 + 0.2 * n1) * (0.94 + 0.08 * n2)
    cav = np.clip((0.55 - h)[..., None] * 1.6, 0, 1) * np.clip(n1 * 1.4 - 0.1, 0, 1)   # 돌기 사이 먼지
    dirt = np.array([0.30, 0.26, 0.19])
    col = col * (1 - cav * 0.55) + dirt * cav * 0.55
    top = np.clip((h - 0.6) * 2.5, 0, 1)[..., None]                                     # 닳은 돌기 윗면
    col = col * (1 - top * 0.25) + np.array([0.92, 0.80, 0.52]) * top * 0.25
    jm = (1 - j)[..., None]
    col = col * (1 - jm * 0.8) + np.array([0.10, 0.09, 0.08]) * jm * 0.8
    scuff = np.clip((T.noise(S, S, 90, seed + 9, 4) - 0.62) * 3, 0, 1)[..., None]      # 고무 신발/타이어 자국
    col = col * (1 - scuff * 0.45) + np.array([0.12, 0.11, 0.10]) * scuff * 0.45
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im, "RGBA")
    rr = random.Random(seed)
    for _ in range(7):   # 껌 자국
        x, y, r = rr.random() * S, rr.random() * S, rr.uniform(4, 9)
        dr.ellipse([x - r, y - r, x + r, y + r * 0.8], fill=(70, 66, 60, 170))
    for _ in range(3):   # 가는 금
        x, y = rr.random() * S, rr.random() * S
        pts = [(x, y)]
        a = rr.random() * 6.28
        for _ in range(18):
            a += rr.uniform(-0.6, 0.6)
            x, y = x + math.cos(a) * 9, y + math.sin(a) * 9
            pts.append((x, y))
        dr.line(pts, fill=(40, 34, 24, 200), width=2)
    im.save(os.path.join(OUT, f"tactile_{kind}_diff.png"))
    rough = 0.78 - top[..., 0] * 0.18 + jm[..., 0] * 0.15 - scuff[..., 0] * 0.1
    save_rgb(np.dstack([rough] * 3), f"tactile_{kind}_rough.png")
    print("tex tactile", kind)


# ------------------------------------------------------------------ 노랑 도료 (흰 도료와 같은 기본 노면 clean_asphalt 결)
def paint_yellow():
    diff = np.asarray(Image.open(os.path.join(OUT, "asphalt_base_diff.jpg")).convert("RGB").resize((1024, 1024),
                      Image.LANCZOS), np.float32) / 255
    lum = diff.mean(-1)
    lum_n = (lum - lum.mean()) / (lum.std() + 1e-6)
    big = T.noise(1024, 1024, 220, 61, 5)
    mid = T.noise(1024, 1024, 40, 62, 4)
    wear = np.clip((-lum_n - 0.9) * 0.6, 0, 1) + np.clip((big - 0.62) * 4.0, 0, 1) * np.clip((mid - 0.35) * 3, 0, 1)
    wear = np.clip(wear, 0, 1)[..., None]
    paint = np.array([0.84, 0.58, 0.07]) * (0.86 + 0.14 * mid[..., None]) * (0.92 + 0.04 * np.clip(lum_n, -2, 2)[..., None])
    grime = np.clip(T.noise(1024, 1024, 120, 63, 4) - 0.45, 0, 1)[..., None] * 0.4
    paint = paint * (1 - grime) + np.array([0.40, 0.34, 0.22]) * grime
    col = paint * (1 - wear) + diff * 1.05 * wear
    save_rgb(col, "roadpaint_yellow_diff.png")
    print("tex roadpaint yellow")


# ------------------------------------------------------------------ 맨홀 뚜껑 양각 높이맵 (원판 = 이미지 전체)
def manhole(S=1024):
    c = S / 2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.hypot(xx - c, yy - c) / c
    h = np.full((S, S), 0.45, np.float32)
    h[r > 0.905] = 1.0                                  # 바깥 테두리
    h[(r > 0.87) & (r <= 0.905)] = 0.12                 # 홈
    # 바깥 띠(0.74~0.87): 둘레 글자만 양각
    h[(r > 0.70) & (r <= 0.74)] = 0.95                  # 안쪽 링
    # 안쪽 마당: 격자 돌기 (프로토타입의 격자 무늬)
    field = r < 0.70
    g = 0.072 * c
    gx = np.mod(xx - c + g / 2, g) / g
    gy = np.mod(yy - c + g / 2, g) / g
    cell = (np.abs(gx - 0.5) < 0.30) & (np.abs(gy - 0.5) < 0.30)
    h[field & cell] = 0.85
    h[field & ~cell] = 0.30
    # 가운데 메달: 링 + 양각 '하수'
    med = r < 0.36
    h[med] = 0.42
    h[(r > 0.33) & (r < 0.37)] = 0.95
    im = Image.fromarray((h * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = T.font("han", S * 0.2)
    d.text((c, c - S * 0.035), "하수", font=f, fill=242, anchor="mm")
    f2 = T.font("eb", S * 0.045)
    d.text((c, c + S * 0.115), "은행골구", font=f2, fill=235, anchor="mm")
    # 둘레 글자 (원을 따라 하나씩 돌려 붙인다)
    s = "은행골구 하수도  ·  오수 우수 겸용  ·  2019  ·  KS D 4302  ·  "
    fs = T.font("eb", S * 0.038)
    n = len(s)
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        a = -math.pi / 2 + 2 * math.pi * i / n
        g_im = Image.new("L", (int(S * 0.07), int(S * 0.07)), 0)
        ImageDraw.Draw(g_im).text((g_im.width / 2, g_im.height / 2), ch, font=fs, fill=255, anchor="mm")
        g_im = g_im.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        rr_ = 0.795 * c
        px, py = c + math.cos(a) * rr_, c + math.sin(a) * rr_
        im.paste(Image.new("L", g_im.size, 240), (int(px - g_im.width / 2), int(py - g_im.height / 2)), g_im)
    h = np.asarray(im, np.float32) / 255
    # 글자 밑 바탕은 돌기를 지운다
    # 들어올리는 구멍 2개 (홈)
    for sx in (-1, 1):
        hx, hy = c + sx * 0.6 * c, c
        m = ((xx - hx) / (0.06 * c)) ** 2 + ((yy - hy) / (0.022 * c)) ** 2 < 1
        h[m] = 0.0
    h = blur(h, 1.4)
    h[r > 1.0] = 1.0
    save_rgb(np.dstack([h] * 3), "manhole_height.png")
    print("tex manhole")


if __name__ == "__main__":
    tactile("line", seed=71)
    tactile("dot", seed=72)
    paint_yellow()
    manhole()
    # k3d.tile 은 PNG 원본을 JPG 로 바꿀 때 실패하므로(_copy_as_jpg) 미리 JPG 로 둔다
    for n in ("roadpaint_diff", "roadpaint_nor", "roadpaint_yellow_diff", "tactile_line_diff", "tactile_line_nor",
              "tactile_dot_diff", "tactile_dot_nor"):
        Image.open(os.path.join(OUT, n + ".png")).convert("RGB").save(os.path.join(OUT, n + ".jpg"), quality=93)
    open(os.path.join(OUT, ".ground_done"), "w").write("ok")

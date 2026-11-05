"""npc_b 그룹 데칼 텍스처 (Pillow). 실행: _cache/venv/bin/python npcb_decals.py <출력폴더>
버거대왕 로고(프로토타입 캔버스 로고와 같은 모양·색), 명찰, 폰 화면, 후드 프린트, 사원증."""
import sys, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
HOME = os.path.expanduser("~")
F_EB = HOME + "/Library/Fonts/NanumSquareEB.ttf"
F_B = HOME + "/Library/Fonts/NanumSquareB.ttf"
F_R = HOME + "/Library/Fonts/NanumSquareR.ttf"
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

RED, CROWN, BUN, PATTY, CREAM, BROWN = "#c8291f", "#f0c63a", "#d98a2b", "#6b3a1e", "#fff3d6", "#3a2416"


def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def logo(text_color, size=1024, text=True, outline=None):
    """프로토타입 로고: 왕관 + 버거 + '버거대왕' (캔버스 좌표 x8)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size / 240.0
    cx, cy = size / 2, size * (0.44 if text else 0.55)
    P = lambda x, y: (cx + x * s, cy + y * s)
    if outline:  # 패치 테두리 (자수 패치)
        d.rounded_rectangle([P(-110, -100), P(110, 105 if text else 45)], radius=22 * s, fill=outline)
    d.pieslice([P(-62, -52), P(62, 36)], 180, 360, fill=BUN)               # 윗번
    for sx, sy in [(-30, -30), (-8, -38), (16, -32), (36, -22), (-44, -18), (2, -22), (24, -16), (-20, -20)]:
        d.ellipse([P(sx - 3, sy - 1.6), P(sx + 3, sy + 1.6)], fill="#f7e6c0")  # 깨
    d.polygon([P(-64, -8), P(-50, -2), P(-36, -9), P(-22, -2), P(-8, -9), P(6, -2), P(20, -9), P(34, -2),
               P(48, -9), P(64, -8), P(64, -4), P(-64, -4)], fill="#7fae3a")    # 양상추
    d.rectangle([P(-60, -6), P(60, 10)], fill=PATTY)                          # 패티
    d.rounded_rectangle([P(-58, 12), P(58, 34)], radius=8 * s, fill=BUN)      # 아랫번
    d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill=CROWN)
    for x, y in [(-34, -82), (0, -90), (34, -82)]:
        d.ellipse([P(x - 4, y - 4), P(x + 4, y + 4)], fill=CROWN)
    if text:
        f = font(F_EB, int(50 * s))
        d.text(P(0, 72), "버거대왕", font=f, fill=text_color, anchor="mm")
    return im


def worn(im, amount=0.18, seed=1):
    """세탁으로 갈라진 프린트 느낌: 알파에 잔 노이즈 구멍."""
    rng = np.random.default_rng(seed)
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    n = rng.random((h // 4, w // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)) / 255.0
    fine = rng.random((h, w))
    hole = (n < amount) & (fine < 0.7)
    a[..., 3] *= np.where(hole, 0.25, 1.0)
    return Image.fromarray(a.astype(np.uint8))


def nametag():
    """명찰 7.0 x 2.4 cm -> 840 x 288."""
    W, H = 840, 288
    im = Image.new("RGBA", (W, H), "#f4f1ea")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 54], fill=RED)
    d.text((24, 27), "버거대왕  시장입구점", font=font(F_EB, 34), fill=CREAM, anchor="lm")
    lg = logo(RED, 360, text=False).resize((190, 190), Image.LANCZOS)
    im.alpha_composite(lg, (14, 70))
    d.text((222, 150), "크루", font=font(F_B, 38), fill="#6d6259", anchor="lm")
    d.text((320, 156), "김민준", font=font(F_EB, 92), fill="#231d18", anchor="lm")
    d.text((W - 24, H - 22), "CREW", font=font(F_B, 28), fill="#9b8f84", anchor="rs")
    return im


def phone_screen():
    """세로 영상 앱 화면 (상표 없음) 9:19.5."""
    W, H = 540, 1170
    im = Image.new("RGB", (W, H), "#0b0b0d")
    rng = np.random.default_rng(3)
    # 흐릿한 먹방 영상 프레임
    v = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(14):
        cx, cy, r = rng.uniform(0, W), rng.uniform(H * 0.15, H * 0.8), rng.uniform(60, 240)
        col = rng.choice([[0.85, 0.45, 0.15], [0.95, 0.75, 0.35], [0.4, 0.22, 0.1], [0.9, 0.9, 0.85], [0.3, 0.5, 0.2]])
        m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
        v += m[..., None] * np.array(col) * rng.uniform(0.4, 0.9)
    v = (1 - np.exp(-v * 1.1)) * 0.78 + 0.03  # 톤매핑 (밝은 덩어리 방지)
    im = Image.fromarray((v * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 70), "팔로잉   |   추천", font=font(SD, 30), fill="#ffffff", anchor="mm")
    for i, (ic, n) in enumerate([("♥", "3.1만"), ("●", "812"), ("➤", "공유")]):
        y = 640 + i * 120
        d.ellipse([W - 92, y - 34, W - 28, y + 30], fill=(255, 255, 255, 60), outline="#ffffff", width=3)
        d.text((W - 60, y + 58), n, font=font(SD, 22), fill="#ffffff", anchor="mm")
    d.text((28, 980), "@맛집탐방러", font=font(F_EB, 32), fill="#ffffff")
    d.text((28, 1028), "불고기버거 세트 솔직후기 #먹방 #버거", font=font(SD, 26), fill="#e8e8e8")
    d.rectangle([28, 1090, W - 28, 1094], fill="#5a5a5a")
    d.rectangle([28, 1090, 300, 1094], fill="#ffffff")
    d.text((40, 24), "11:42", font=font(SD, 24), fill="#ffffff")
    d.text((W - 40, 24), "5G  76%", font=font(SD, 22), fill="#ffffff", anchor="ra")
    return im


def hoodie_print():
    W, H = 1024, 384
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 150), "ordinary days", font=font(F_EB, 120), fill="#f1ede4", anchor="mm")
    d.text((W / 2, 285), "SEOUL · EST. 2019", font=font(F_B, 54), fill="#f1ede4", anchor="mm")
    return worn(im, 0.22, 5)


def idcard():
    """사원증 5.4 x 8.6 cm -> 432 x 688."""
    W, H = 432, 688
    im = Image.new("RGBA", (W, H), "#fbfbf8")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 120], fill="#1f4e8c")
    d.text((W / 2, 62), "대한물산", font=font(F_EB, 62), fill="#ffffff", anchor="mm")
    d.rectangle([116, 160, 316, 410], fill="#c9d3dc")
    d.ellipse([166, 196, 266, 306], fill="#7b6a5e")                  # 증명사진 실루엣
    d.pieslice([126, 300, 306, 500], 180, 360, fill="#2d3540")
    d.text((W / 2, 470), "박정훈", font=font(F_EB, 64), fill="#1a1a1a", anchor="mm")
    d.text((W / 2, 540), "영업2팀 · 과장", font=font(F_B, 34), fill="#444444", anchor="mm")
    d.rectangle([40, 600, W - 40, 640], fill="#e5e5e0")
    for i in range(40):
        x = 48 + i * 8.6
        d.rectangle([x, 604, x + (3 if i % 3 else 5), 636], fill="#222222")
    return im


def mouth():
    """입 데칼 5.5 x 5 cm -> 550 x 500 (아래쪽 입선, 아랫입술 음영, 위쪽 인중 음영). 피부 위에 알파로 얹는다."""
    W, H = 550, 500
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([W / 2 - 22, 120, W / 2 + 22, 300], fill=(90, 45, 38, 40))            # 인중 홈
    d.ellipse([W / 2 - 115, 318, W / 2 + 115, 372], fill=(150, 72, 62, 95))         # 아랫입술
    d.ellipse([W / 2 - 120, 286, W / 2 + 120, 316], fill=(140, 66, 58, 70))         # 윗입술
    im = Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(10)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = [(W / 2 + x, 312 + 0.0009 * x * x) for x in range(-150, 151, 6)]         # 입선: 끝이 살짝 처진 무표정
    d.line(pts, fill=(70, 30, 26, 225), width=9, joint="curve")
    for sx in (-1, 1):
        d.ellipse([W / 2 + sx * 150 - 6, 332 - 6, W / 2 + sx * 150 + 6, 332 + 6], fill=(80, 36, 30, 110))
    return Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(2.2)))


if __name__ == "__main__":
    logo(RED).save(os.path.join(OUT, "logo_red.png"))
    logo(CREAM).save(os.path.join(OUT, "logo_cream.png"))
    worn(logo(CREAM), 0.16, 2).save(os.path.join(OUT, "logo_cream_worn.png"))
    logo(CREAM, outline="#2a1a12").save(os.path.join(OUT, "logo_patch.png"))
    logo(RED, text=False).save(os.path.join(OUT, "logo_icon.png"))
    nametag().save(os.path.join(OUT, "nametag.png"))
    phone_screen().save(os.path.join(OUT, "phone_screen.png"))
    hoodie_print().save(os.path.join(OUT, "hoodie_print.png"))
    idcard().save(os.path.join(OUT, "idcard.png"))
    mouth().save(os.path.join(OUT, "mouth.png"))
    # 자가 점검: 모두 만들어졌는지
    for n in ["logo_red", "logo_cream", "logo_cream_worn", "logo_patch", "logo_icon", "nametag", "phone_screen", "hoodie_print", "idcard", "mouth"]:
        assert os.path.getsize(os.path.join(OUT, n + ".png")) > 1000, n
    print("npcb_decals ok", OUT)

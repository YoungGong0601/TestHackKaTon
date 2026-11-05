"""NPC 데칼/화면 텍스처 (Pillow). venv 파이썬으로 실행: python npc_decals.py <출력폴더>
시계 문자판, 사원증, 스마트폰 화면(뉴스 피드) PNG 를 만든다. 굽기 입력용(사원증·문자판)과 M_Dyn 기본 화면용."""
import sys, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
FD = os.path.expanduser("~/Library/Fonts/")
def F(w, size):
    return ImageFont.truetype(FD + {"R": "NanumSquareR.ttf", "B": "NanumSquareB.ttf", "EB": "NanumSquareEB.ttf", "L": "NanumSquareL.ttf"}[w], size)


def dial(name, face, ink, accent):
    # 아날로그 시계 문자판 (512)
    S = 512
    im = Image.new("RGB", (S, S), face)
    d = ImageDraw.Draw(im)
    c = S / 2
    d.ellipse((6, 6, S - 6, S - 6), outline=(90, 90, 92), width=14)  # 베젤 안쪽 그림자
    import math
    for i in range(60):
        a = math.radians(i * 6)
        r0, r1 = (c - 40, c - 78) if i % 5 == 0 else (c - 40, c - 54)
        w = 12 if i % 15 == 0 else (7 if i % 5 == 0 else 3)
        d.line((c + r0 * math.sin(a), c - r0 * math.cos(a), c + r1 * math.sin(a), c - r1 * math.cos(a)), fill=ink, width=w)
    d.text((c, c - 120), "SEOWON", font=F("B", 30), fill=ink, anchor="mm")
    d.text((c, c + 110), "QUARTZ", font=F("R", 20), fill=ink, anchor="mm")
    for ang, ln, w in ((-35, 120, 14), (75, 175, 9)):  # 시침·분침 (10:12)
        a = math.radians(ang)
        d.line((c, c, c + ln * math.sin(a), c - ln * math.cos(a)), fill=ink, width=w)
    a = math.radians(200)
    d.line((c, c, c + 190 * math.sin(a), c - 190 * math.cos(a)), fill=accent, width=4)
    d.ellipse((c - 14, c - 14, c + 14, c + 14), fill=ink)
    im.save(os.path.join(OUT, name))


def id_card():
    # 사원증 (세로 54x86mm, 640x1024): 파란 머리띠+로고, 증명사진, 큰 이름/직급 (1~2m 에서 형태가 읽히게)
    W, H = 640, 1024
    im = Image.new("RGB", (W, H), (246, 246, 242))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 230), fill=(18, 64, 140))
    d.ellipse((36, 52, 156, 172), fill=(255, 255, 255))
    d.polygon([(70, 140), (96, 76), (122, 140)], fill=(18, 64, 140))          # 가상 로고 (산 모양)
    d.polygon([(100, 140), (118, 100), (136, 140)], fill=(230, 120, 40))
    d.text((176, 62), "한빛물산", font=F("EB", 78), fill=(255, 255, 255))
    d.text((180, 160), "HANBIT TRADING", font=F("B", 28), fill=(200, 215, 240))
    # 증명사진: 하늘색 배경, 남색 정장, 흰 셔츠, 얼굴, 검은 머리
    ph = Image.new("RGB", (320, 400), (196, 218, 236))
    pd = ImageDraw.Draw(ph)
    pd.ellipse((-20, 270, 340, 560), fill=(28, 36, 62))
    pd.polygon([(120, 285), (200, 285), (160, 380)], fill=(240, 240, 238))
    pd.polygon([(150, 300), (170, 300), (166, 380), (154, 380)], fill=(40, 50, 110))
    pd.rectangle((132, 230, 188, 300), fill=(214, 168, 136))
    pd.ellipse((86, 66, 234, 205), fill=(28, 22, 20))                          # 옆머리
    pd.ellipse((98, 100, 222, 265), fill=(222, 178, 146))                      # 얼굴
    pd.chord((94, 74, 226, 166), 180, 360, fill=(28, 22, 20))                  # 앞머리
    for ex in (135, 185):
        pd.ellipse((ex - 8, 172, ex + 8, 184), fill=(30, 24, 22))
    pd.arc((138, 205, 182, 235), 20, 160, fill=(150, 90, 80), width=4)
    im.paste(ph, (160, 262))
    d.rectangle((160, 262, 480, 662), outline=(170, 170, 170), width=3)
    d.text((W / 2, 745), "김민수", font=F("EB", 104), fill=(20, 20, 26), anchor="mm")
    d.text((W / 2, 838), "영업2팀  대리", font=F("B", 50), fill=(60, 60, 72), anchor="mm")
    rnd = random.Random(7)
    x = 130
    while x < 510:  # 바코드
        w = rnd.choice((3, 4, 6, 9))
        d.rectangle((x, 892, x + w, 968), fill=(20, 20, 20))
        x += w + rnd.choice((3, 4, 6))
    d.text((W / 2, 995), "2019-0412", font=F("R", 22), fill=(90, 90, 90), anchor="mm")
    im.save(os.path.join(OUT, "npc_idcard.png"))


def phone_screen():
    # 스마트폰 화면 기본값: 뉴스 피드 앱 (물리 66x143mm -> 945x2048 로 그리고 1024x2048 로 늘려 UV 0-1 에 맞춤)
    W, H = 945, 2048
    im = Image.new("RGB", (W, H), (246, 247, 249))
    d = ImageDraw.Draw(im)
    d.text((48, 38), "12:47", font=F("B", 40), fill=(20, 20, 20))
    d.text((W - 48, 38), "LTE  82%", font=F("B", 34), fill=(20, 20, 20), anchor="ra")
    d.rectangle((0, 110, W, 250), fill=(255, 255, 255))
    d.text((48, 150), "오늘의 소식", font=F("EB", 58), fill=(17, 120, 90))
    d.line((0, 250, W, 250), fill=(225, 225, 228), width=3)
    tabs = ["주요", "사회", "경제", "생활", "연예"]
    for i, t in enumerate(tabs):
        d.text((60 + i * 170, 285), t, font=F("B" if i == 1 else "R", 38), fill=(17, 120, 90) if i == 1 else (110, 110, 115))
    d.rectangle((48, 340, 150, 346), fill=(17, 120, 90))
    items = [
        ("키오스크 앞에서 멈춘 어르신들…\n'디지털 소외' 여전", "사회 · 12분 전", (200, 170, 140)),
        ("버거대왕, 가을 한정\n'불고기 세트' 출시", "생활 · 35분 전", (190, 120, 70)),
        ("내일 아침 기온 뚝… 서울 4도\n출근길 옷차림 단단히", "날씨 · 1시간 전", (120, 150, 190)),
        ("버스 도착 안내 앱, 고령층은\n'글씨 작아 못 봐요'", "사회 · 2시간 전", (150, 160, 140)),
        ("점심값 또 올랐다… 직장인\n'런치플레이션' 한숨", "경제 · 3시간 전", (170, 150, 170)),
    ]
    y = 390
    for title, meta, col in items:
        d.rectangle((40, y, W - 40, y + 300), fill=(255, 255, 255))
        d.rounded_rectangle((W - 330, y + 30, W - 70, y + 270), radius=18, fill=col)
        d.multiline_text((70, y + 40), title, font=F("B", 40), fill=(25, 25, 28), spacing=14)
        d.text((70, y + 230), meta, font=F("R", 30), fill=(140, 140, 146))
        y += 330
    d.rectangle((0, H - 140, W, H), fill=(255, 255, 255))
    for i, t in enumerate(["홈", "검색", "구독", "MY"]):
        d.text((120 + i * 235, H - 85), t, font=F("B", 34), fill=(90, 90, 96), anchor="mm")
    d.rounded_rectangle((W / 2 - 140, H - 30, W / 2 + 140, H - 20), radius=5, fill=(30, 30, 30))
    d.ellipse((W / 2 - 22, 30, W / 2 + 22, 74), fill=(6, 6, 8))     # 펀치홀 카메라 (지름 3mm)
    im = im.resize((1024, 2048), Image.LANCZOS)
    im.save(os.path.join(OUT, "T_NpcSmartphone_Screen.png"))


dial("npc_dial_white.png", (236, 233, 224), (30, 30, 34), (190, 40, 30))
dial("npc_dial_black.png", (22, 24, 28), (225, 225, 225), (230, 120, 40))
dial("npc_dial_gold.png", (238, 226, 196), (60, 45, 25), (150, 110, 40))
id_card()
phone_screen()
print("decals ok", OUT)

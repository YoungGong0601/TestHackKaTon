"""PH_Bus 2D 텍스처 (Pillow): 노선 번호가 읽히지 않는 데칼 아틀라스 + 꺼진 LED 판.

실행: <venv>/bin/python -I bus_tex.py <출력폴더>   (bus.py 가 자동으로 부른다)
원본 아틀라스에서 세 칸만 바꾼다: 번호판(3112), 대시보드 카드(112), 회사명 옆 차량번호(112-07).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Vehicles"))
import CityBus_tex as T
from PIL import Image, ImageDraw

out = sys.argv[1]
os.makedirs(out, exist_ok=True)

_text, _fit = T.text, T.fit   # plate() 는 번호가 글자 그대로 박혀 있어 숫자만 바꿔 다시 그린다
T.text = lambda d, xy, s, *a, **k: _text(d, xy, s.replace("3112", "3086"), *a, **k)
T.fit = lambda s, *a, **k: _fit(s.replace("3112", "3086"), *a, **k)
plate = T.plate()

card = Image.new("RGBA", (512, 256), (240, 236, 222, 255))   # 안내판 틀에 끼운 빈 종이
ImageDraw.Draw(card).rectangle((0, 0, 511, 255), outline=(150, 146, 134, 255), width=6)
card = T.grain(T.fade(card, 0.25, (255, 230, 170)), 6, 5)

company = T.company()
company.paste((0, 0, 0, 0), (700, 0, 1024, 256))             # 구분선과 112-07 지움, 시민교통(주) 만 남김

at = Image.open(os.path.join(HERE, "..", "..", "..", "..", "Assets", "Art3D", "Textures", "CityBus", "T_CityBus_Decals.png")).convert("RGBA")
for k, im in (("plate", plate), ("placard", card), ("company", company)):
    at.paste(im, T.REGIONS[k][:2])
at.save(os.path.join(out, "T_PH_Bus_Decals.png"), optimize=True)
T.route_sign(os.path.join(out, "T_PH_Bus_SignBlank.png"), "", "", "")
print("bus_tex: ok", out)

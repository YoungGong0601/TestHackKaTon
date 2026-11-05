"""새 컴퓨터에서 처음 한 번 돌린다: blender -b --factory-startup --python setup.py

텍스처를 그리는 Pillow 파이썬을 K3D_CACHE/venv 에 만들고, Blender 버전과 베이크 장치, 폰트를 점검한다.
텍스처 스크립트 15개가 이 프로젝트를 처음 만든 Mac 의 폰트 경로를 쓴다. 그 폰트가 없는 컴퓨터에서도 돌도록
venv 의 sitecustomize.py 가 없는 폰트를 K3D_CACHE/fonts 의 같은 이름으로, 그것도 없으면 GothicA1-Bold 로 바꾼다.
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, k3d

FONT_FIX = """import os
from PIL import ImageFont
FONTS = {fonts!r}
_real = ImageFont.truetype
def truetype(font=None, size=10, index=0, **kw):
    if isinstance(font, str) and not os.path.exists(font):
        same = os.path.join(FONTS, os.path.basename(font))
        font, index = (same if os.path.exists(same) else os.path.join(FONTS, "GothicA1-Bold.ttf")), 0
    return _real(font, size, index=index, **kw)
ImageFont.truetype = truetype
"""

if not os.path.exists(k3d.PY):
    subprocess.run([sys.executable, "-m", "venv", os.path.dirname(os.path.dirname(k3d.PY))], check=True)
subprocess.run([k3d.PY, "-m", "pip", "install", "-q", "pillow==13.0.0", "numpy==2.5.4"], check=True)
subprocess.run([k3d.PY, "-c", "import PIL, numpy; print('k3d: Pillow', PIL.__version__, 'numpy', numpy.__version__)"], check=True)
site = subprocess.run([k3d.PY, "-c", "import site; print(site.getsitepackages()[0])"],
                      capture_output=True, text=True, check=True).stdout.strip()
with open(os.path.join(site, "sitecustomize.py"), "w", encoding="utf-8") as f:
    f.write(FONT_FIX.format(fonts=os.path.join(k3d.CACHE, "fonts")))

k3d._cycles(1)
print("k3d: 베이크 장치", bpy.context.scene.cycles.device,
      [d.name for d in bpy.context.preferences.addons['cycles'].preferences.devices if d.use])
fonts = os.path.join(k3d.CACHE, "fonts")
print("k3d: 폰트", sorted(os.listdir(fonts)) if os.path.isdir(fonts) else "없음 (git pull 을 확인합니다)")
print("k3d: Blender", bpy.app.version_string, "OK" if bpy.app.version[:2] == (5, 2) else "경고: 5.2 계열이 아닙니다")

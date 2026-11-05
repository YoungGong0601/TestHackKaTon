"""새 컴퓨터에서 처음 한 번 돌린다: blender -b --factory-startup --python setup.py

텍스처를 그리는 Pillow 파이썬을 K3D_CACHE/venv 에 만들고, Blender 버전과 베이크 장치, 폰트를 점검한다.
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, k3d

if not os.path.exists(k3d.PY):
    subprocess.run([sys.executable, "-m", "venv", os.path.dirname(os.path.dirname(k3d.PY))], check=True)
subprocess.run([k3d.PY, "-m", "pip", "install", "-q", "pillow", "numpy"], check=True)
subprocess.run([k3d.PY, "-c", "import PIL, numpy; print('k3d: Pillow', PIL.__version__, 'numpy', numpy.__version__)"], check=True)

k3d._cycles(1)
print("k3d: 베이크 장치", bpy.context.scene.cycles.device,
      [d.name for d in bpy.context.preferences.addons['cycles'].preferences.devices if d.use])
fonts = os.path.join(k3d.CACHE, "fonts")
print("k3d: 폰트", sorted(os.listdir(fonts)) if os.path.isdir(fonts) else "없음 (git pull 을 확인합니다)")
print("k3d: Blender", bpy.app.version_string, "OK" if bpy.app.version[:2] == (5, 2) else "경고: 5.2 계열이 아닙니다")

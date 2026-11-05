"""NpcSmartphone: NPC 손에 붙이는 스마트폰 (71.5x147x7.8mm). 화면은 M_Dyn (게임이 텍스처 교체).
원점 = 뒷면 중앙, 아래에서 1/3 (손에 쥐는 점). 화면 = -Y(Unity +Z 반대쪽이 아니라 transform.forward 쪽), 위 = +Z."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import npc_common as N
from npc_common import k3d

A = "NpcSmartphone"
k3d.reset()
body, screen = N.build_phone(A)
k3d.bake(body, size=512, samples=24)
notes = ("NPC 소품 스마트폰 71.5x147x7.8mm. 원점은 바닥이 아니라 손에 쥐는 점(뒷면 중앙, 아래에서 1/3)이라 min_z 가 음수다."
         " 붙이는 법: 캐릭터의 <Npc>_Socket_PhoneGrip (Palm.R 자식) 아래에 두고 localPosition=0, localRotation=identity."
         " 동적 화면: NpcSmartphone_Screen, 66.0x142.5mm 쿼드, M_Dyn_NpcSmartphone_Screen, 기본 텍스처 1024x2048"
         " (뉴스 피드 '오늘의 소식'), UV 0..1 = 화면 전체, U->오른쪽 V->위 (화면 쪽에서 볼 때). 발광 1.2.")
k3d.export(A, "Characters", [body], notes=notes)
k3d.preview(A, [body], views=((20, 15), (200, 15)), res=(900, 900))
k3d.preview(A, [body], views=((0, 0),), res=(700, 900), tag="front")

# -*- coding: utf-8 -*-
"""뒷사람과 행인 음성의 성별 점검. 음높이와 씬 데이터만 본다.
사용: python tools/check_vo_gender.py (numpy, imageio_ffmpeg 필요)
- NunchiLines.Hurry 화자 값과 파일 음높이가 같은 성별인가
- R4_Stop 학생, 직장인 모델과 pass_1, pass_2가 같은 성별인가
- 가게 줄의 먼저 오는 두 손님에 남녀가 다 있는가 (한쪽뿐이면 그 성별 대사가 빠진다)
"""
import re, subprocess, sys
from pathlib import Path
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
VO, SCENES = ROOT / "Assets/Resources/Audio/vo", ROOT / "Assets/Scenes"
SR, FEMALE_HZ = 16000, 165  # 지금 파일은 남자 100~150Hz, 여자 205Hz 이상
errors = []


def female_voice(key):
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(VO / f"{key}.mp3"), "-ac", "1",
                          "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n, lo, hi, f0 = int(.04 * SR), SR // 400, SR // 70, []
    for i in range(0, len(x) - n, SR // 100):
        f = x[i:i + n] * np.hanning(n)
        if np.sqrt((f * f).mean()) < .02:
            continue
        c = np.correlate(f, f, "full")[n - 1:]
        k = lo + int(np.argmax(c[lo:hi]))
        if c[k] > .5 * c[0]:
            f0.append(SR / k)
    return float(np.median(f0)) > FEMALE_HZ


def models():
    """PH_NPC의 look 번호 순서대로 모델 이름"""
    t = (ROOT / "Assets/Graybox/PH/PH_NPC.prefab").read_text(encoding="utf8")
    docs = {m[1]: m[2] for m in re.finditer(r"^--- !u!\d+ &(\d+).*?\n(.*?)(?=^--- |\Z)", t, re.M | re.S)}
    visual = re.search(r"visuals:\n  - \{fileID: (\d+)\}", t)[1]
    names = []
    for child in re.findall(r"- \{fileID: (\d+)\}", re.search(r"m_Children:\n((?:  - .*\n)*)", docs[visual])[1]):
        inst = docs[re.search(r"m_PrefabInstance: \{fileID: (\d+)\}", docs[child])[1]]
        names.append(re.search(r"propertyPath: m_Name\s+value: (.+)", inst)[1].strip())
    return names


def female_model(name):  # NpcPose.Bind와 같은 규칙
    return "Woman" in name or "Ajumma" in name


def looks(scene):
    """오브젝트 이름 -> look 번호"""
    t = (SCENES / f"{scene}.unity").read_text(encoding="utf8")
    out = {}
    for b in re.findall(r"PrefabInstance:.*?m_SourcePrefab", t, re.S):
        name, look = re.search(r"propertyPath: m_Name\s+value: (.+)", b), re.search(r"propertyPath: look\s+value: (\d+)", b)
        if name and look:
            out[name[1].strip()] = int(look[1])
    return out


def main():
    src = (ROOT / "Assets/Scripts/Kiosk/Nunchi/NunchiLines.cs").read_text(encoding="utf8")
    for key, who in re.findall(r'\{ "(y_hurry\d+)", "(\w+)",', src):
        if female_voice(key) != (who != "yM"):
            errors.append(f"{key}: 화자 {who}와 음높이가 다름")
    names = models()
    stop = looks("R4_Stop")
    for key, npc in (("pass_1", "Student"), ("pass_2", "Worker")):
        if female_voice(key) != female_model(names[stop[npc]]):
            errors.append(f"{key}: {npc} 모델 {names[stop[npc]]}과 성별이 다름")
    for scene in ("R1_Store", "R2_Cafe", "R4_Store"):
        first = [female_model(names[looks(scene)[f"NPC_Queue{i}"]]) for i in (0, 1)]
        if first[0] == first[1]:
            errors.append(f"{scene}: NPC_Queue0, 1이 같은 성별")
    print("\n".join(errors) or "OK")
    sys.exit(1 if errors else 0)


main()

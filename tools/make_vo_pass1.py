# -*- coding: utf-8 -*-
"""정류장 첫 학생 대사 pass_1 음성 생성기. edge-tts + ffmpeg.
화자 설정과 후처리는 ../kiosk-game/tools/make_vo.py 의 pass 화자와 같다.
사용: python tools/make_vo_pass1.py
출력: Assets/Resources/Audio/vo/pass_1.mp3, Assets/Resources/Audio/VO_LINES.csv 의 pass_1 줄
"""
import asyncio, csv, subprocess, tempfile
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "Assets" / "Resources" / "Audio"
KEY = "pass_1"
TEXT = "아, 저도 잘 모르겠어요."
VOICE, RATE, PITCH = "ko-KR-HyunsuMultilingualNeural", "+5%", "+12Hz"
FILTER, VOL = "highpass=f=250,lowpass=f=5000", -3


def post(raw, dst):
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
            "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    chain = f"{trim},{FILTER},loudnorm=I=-18:TP=-2:LRA=11,volume={VOL}dB"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", chain,
                    "-ac", "1", "-ar", "24000", "-b:a", "96k", str(dst)], check=True)


def update_csv():
    path = AUDIO / "VO_LINES.csv"
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    for row in rows:
        if row and row[0] == KEY:
            row[2] = TEXT
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / f"{KEY}.mp3"
        await edge_tts.Communicate(TEXT, VOICE, rate=RATE, pitch=PITCH).save(str(raw))
        post(raw, AUDIO / "vo" / f"{KEY}.mp3")
    update_csv()
    print("ok", KEY)


asyncio.run(main())

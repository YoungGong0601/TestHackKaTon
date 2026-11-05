# -*- coding: utf-8 -*-
"""플레이 피드백으로 추가한 음성 생성기. edge-tts + ffmpeg. 화자 값은 kiosk-game/tools/make_vo.py와 같다.
사용: python tools/make_vo.py [key ...]
출력: Assets/Resources/Audio/vo/<key>.mp3, Assets/Resources/Audio/VO_LINES.csv에 없는 줄 추가
"""
import asyncio, csv, subprocess, sys, tempfile
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Assets" / "Resources" / "Audio" / "vo"
CSV = ROOT / "Assets" / "Resources" / "Audio" / "VO_LINES.csv"

HS = "ko-KR-HyunsuMultilingualNeural"
# 화자: (음성, rate, pitch, ffmpeg 필터(라우드니스 전), 라우드니스 후 볼륨 dB)
SPK = {
 "yM":    (HS, "+5%", "+0Hz", "aecho=0.8:0.6:70|110:0.22|0.12", 0),
 "staff": (HS, "-5%", "-8Hz", "lowpass=f=5000", -1),
}
ROWS = [
 ("y_move1", "yM", "할아버지 뭐 해요."),
 ("y_move2", "yM", "비키세요."),
 ("staff_call3", "staff", "이백칠십사번 고객님, 메뉴 가져가세요."),
]

def post(raw, dst, flt, vol):
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
            "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    chain = f"{trim},{flt},loudnorm=I=-18:TP=-2:LRA=11" + (f",volume={vol}dB" if vol else "")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", chain,
                        "-ac", "1", "-ar", "24000", "-b:a", "96k", str(dst)],
                       capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr)

async def main():
    keys = sys.argv[1:]
    rows = [r for r in ROWS if not keys or r[0] in keys]
    with tempfile.TemporaryDirectory() as tmp:
        for key, spk, text in rows:
            voice, rate, pitch, flt, vol = SPK[spk]
            raw = Path(tmp) / f"{key}.mp3"
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(raw))
            post(raw, OUT / f"{key}.mp3", flt, vol)
            print("ok", key, flush=True)
    with open(CSV, encoding="utf-8-sig") as f:
        have = {r[0] for r in csv.reader(f) if r}
    with open(CSV, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for key, spk, text in ROWS:
            if key not in have: w.writerow([key, spk, text, SPK[spk][0]])

asyncio.run(main())

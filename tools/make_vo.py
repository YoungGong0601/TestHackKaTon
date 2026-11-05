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

HS = "ko-KR-HyunsuMultilingualNeural"; IJ = "ko-KR-InJoonNeural"; SH = "ko-KR-SunHiNeural"
# 화자: (음성, rate, pitch, ffmpeg 필터(라우드니스 전), 라우드니스 후 볼륨 dB)
SPK = {
 "yM":    (HS, "+5%", "+0Hz", "aecho=0.8:0.6:70|110:0.22|0.12", 0),
 "staff": (HS, "-5%", "-8Hz", "lowpass=f=5000", -1),
 "gp":    (IJ, "-20%", "-15Hz", "lowpass=f=4000", 0),
 "yF":    (SH, "+8%", "+3Hz", "aecho=0.8:0.6:60:0.15", -5),
 "pass":  (HS, "+5%", "+12Hz", "highpass=f=250,lowpass=f=5000", -3),
 "kiosk": (SH, "+5%", "+5Hz", "highpass=f=300,lowpass=f=6000", 0),
 "busann": (SH, "-5%", "-5Hz", "highpass=f=200,lowpass=f=7000,aecho=0.8:0.7:90:0.25", 0),
 # 회차 인물과 기사. 4회차 뒷사람은 a20 그대로다
 "a20":   (HS, "+5%", "+0Hz", "lowpass=f=6500", -1),
 "a40":   (IJ, "+0%", "+0Hz", "lowpass=f=6000", 0),
 "a60":   (IJ, "-10%", "-8Hz", "lowpass=f=4500", 0),
 "drv":   (HS, "-8%", "-14Hz", "lowpass=f=4500", -1),
}
ROWS = [
 ("y_move1", "yM", "할아버지 뭐 해요."),
 ("y_move2", "yM", "비키세요."),
 ("staff_call3", "staff", "이백칠십사번 고객님, 메뉴 가져가세요."),
 ("a20_nobill", "a20", "그거 지폐 안 받아요."),
 ("gp_giveup", "gp", "그려? 어쩔 수 없구만..."),
 ("gp_note", "gp", "뭐라고 썼더라."),
 ("gp_money", "gp", "돈을 어디다 넣으라는 거야."),
 ("gp_notthis", "gp", "아이고, 아니구먼."),
 ("gp_watch", "gp", "벌써 이렇게 됐구먼."),
 ("gp_notice", "gp", "현금 없는 버스 운행 안내."),
 ("pass_3", "pass", "백십이번 타시면 돼요. 곧 와요."),
 ("bus_take", "busann", "백십이번 버스를 타세요."),
 ("staff_hello", "staff", "어서 오세요!"),
 ("staff_help", "staff", "여기 누르시면 돼요. 제가 도와드릴게요."),
 ("staff_wait", "staff", "아직입니다."),
 ("staff_cafe", "staff", "아, 그거 여기 누르시면 돼요."),
 ("staff_cinema", "staff", "거기 다 나와 있어요."),
 ("staff_call5", "staff", "이백칠십오번 고객님."),
 ("k_home", "kiosk", "처음 화면으로 돌아갑니다."),
 ("k_again", "kiosk", "죄송합니다. 다시 말씀해 주세요."),
 ("drv_117", "drv", "백십칠번이요."),
 ("drv_172", "drv", "백칠십이번이요."),
 ("drv_112", "drv", "백십이번이요."),
 ("drv_nocash", "drv", "현금은 안 받아요."),
 ("drv_there", "drv", "거기 써 있잖아요."),
 ("drv_card", "drv", "카드 찍으세요."),
 ("drv_app", "drv", "앱에서 하세요."),
 ("gp_wherecash", "gp", "현금은 어디에 넣어요?"),
 ("gp_notice2", "gp", "현금 없는 버스 운행 안내. 이 버스는 현금을 받지 않습니다."),
 ("gp_onlycash", "gp", "현금밖에 없는데요."),
 ("drv_cardonly", "drv", "저희는 카드밖에 받지 않습니다."),
 ("y_hurry8", "yM", "아, 좀 빨리요."),
 ("y_hurry9", "yF", "영화 시작하는데요."),
 ("a20_why1", "a20", "왜 안 되지?"),
 ("a20_why2", "a20", "이게 왜 안 돼."),
 ("a20_why3", "a20", "이건 또 뭐야."),
 ("a20_what1", "a20", "이게 무슨 말이야."),
 ("a20_read1", "a20", "글씨가 왜 이렇게 작아."),
 ("a40_why1", "a40", "왜 안 되지?"),
 ("a40_why2", "a40", "이게 왜 안 돼."),
 ("a40_why3", "a40", "이건 또 뭐야."),
 ("a40_what1", "a40", "이게 무슨 말이야."),
 ("a40_read1", "a40", "글씨가 왜 이렇게 작아."),
 ("a60_why1", "a60", "왜 안 되지?"),
 ("a60_why2", "a60", "이게 왜 안 돼."),
 ("a60_why3", "a60", "이건 또 뭐야."),
 ("a60_what1", "a60", "이게 무슨 말이야."),
 ("a60_read1", "a60", "글씨가 왜 이렇게 작아."),
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

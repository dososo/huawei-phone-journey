"""用用户显式提供的真实样本重演乐谱，不读取系统音库或网络。

样本库：samples=[{instrument,file,rootMidi,velocity,f0Hz(可选)}]，
drums=[{file},{file},{file}]；file相对样本库JSON且不能越出其目录。
五类instrument为钢琴、电钢琴、暖垫、晶体、弦乐。鼓为三个已准备片段。
合成低音和气流是艺术声效；重演不是原音色母带的逐字节复刻。
"""
import argparse
import json
import math
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

INSTRUMENTS = {"钢琴", "电钢琴", "暖垫", "晶体", "弦乐"}
DEFAULT_SCORE = Path(__file__).resolve().parents[1] / "data/score.json"


def load_bank(path, rate):
    """只读JSON明确列出的目录内文件，拒绝绝对路径和链接越界。"""
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    banks = {name: [] for name in INSTRUMENTS}
    files = set()

    def read(row):
        relative = Path(row["file"])
        target = (path.parent / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(path.parent):
            raise ValueError("样本路径未授权：必须位于样本库JSON目录内")
        x, original_rate = sf.read(target, dtype="float32", always_2d=True)
        if not len(x) or x.shape[1] not in (1, 2) or not np.isfinite(x).all():
            raise ValueError("样本须为非空、有限的单声道或双声道音频")
        if original_rate != rate:
            x = resample_poly(x, rate, original_rate, axis=0).astype("float32")
        if x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1)
        peak = float(np.max(np.abs(x)))
        if peak <= 1e-8:
            raise ValueError("样本没有可用声音")
        files.add(target)
        return x / max(peak, .2)

    for row in data["samples"]:
        name, root, velocity = row["instrument"], row["rootMidi"], row["velocity"]
        if name not in banks or type(root) is not int or not 0 <= root <= 127:
            raise ValueError("乐器名称或根MIDI无效")
        if type(velocity) is not int or not 0 <= velocity <= 127:
            raise ValueError("采样力度须为0至127的整数")
        f0 = row.get("f0Hz")
        if f0 is not None and (not isinstance(f0, (int, float)) or not math.isfinite(f0) or f0 <= 0):
            raise ValueError("实测基频须为正的有限数值")
        banks[name].append((root, velocity, read(row), f0))
    if any(not rows for rows in banks.values()) or len(data["drums"]) != 3:
        raise ValueError("完整重演需要五类乐器各至少一份样本和三个鼓片段")
    return banks, [read(row) for row in data["drums"]], files


def fade(x, rate, attack, release):
    a, r = min(len(x), max(2, round(attack * rate))), min(len(x), max(2, round(release * rate)))
    x[:a] *= np.sin(np.linspace(0, np.pi / 2, a, dtype="float32"))[:, None] ** 2
    x[-r:] *= np.cos(np.linspace(0, np.pi / 2, r, dtype="float32"))[:, None] ** 2
    return x


def render(score, bank_path, out, seconds=None):
    rate = score["sampleRate"]
    duration = score["duration"] if seconds is None else seconds
    if rate != 48000 or not math.isfinite(duration) or not 0 < duration <= score["duration"]:
        raise ValueError("乐谱须为48000Hz，试听长度须在完整时长以内")
    banks, drums, files = load_bank(bank_path, rate)
    out = Path(out).resolve()
    if out in files or out == Path(bank_path).resolve():
        raise ValueError("输出路径不能覆盖样本或样本库JSON")
    count = round(duration * rate)
    if count < 1:
        raise ValueError("输出长度不足一个采样帧")
    mix = np.zeros((count, 2), dtype="float32")
    chapters = {c["index"] + 1: c for c in score["chapters"]}
    rng = np.random.default_rng(2026100675)

    @lru_cache(maxsize=64)
    def voice(kind, note, length, velocity):
        root, _, x, f0 = min(banks[kind], key=lambda row: abs(row[0] - note) * 3 + abs(row[1] - velocity) / 18)
        ratio = Fraction(440 * 2 ** ((note - 69) / 12) / f0 if f0 else 2 ** ((note - root) / 12)).limit_denominator(300)
        x = resample_poly(x, ratio.denominator, ratio.numerator, axis=0).astype("float32")
        n = round(length * rate)
        if len(x) < n and kind in ("暖垫", "弦乐") and len(x) >= 8:
            # 自选中段交叉延续持续音色，不声称使用厂家原延音环。
            loop = x[round(len(x) * .25):round(len(x) * .8)].copy()
            overlap = min(round(.15 * rate), len(loop) // 5)
            ramp = np.linspace(0, 1, overlap, dtype="float32")[:, None]
            while len(x) < n:
                x[-overlap:] = x[-overlap:] * (1 - ramp) + loop[:overlap] * ramp
                x = np.concatenate((x, loop[overlap:]))
        x = np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n].copy()
        fade(x, rate, .3 if kind in ("暖垫", "弦乐") else .005, min(.35, length * .27))
        if kind in ("暖垫", "晶体"):
            x = sosfilt(butter(2, 2000 if kind == "暖垫" else 4800, fs=rate, output="sos"), x, axis=0).astype("float32")
        return x

    def put(x, time, gain, pan=0, chapter=0, rhythmic=False):
        at = round(time * rate)
        if at < 0:
            x, at = x[-at:], 0
        n = min(len(x), count - at)
        if n <= 0:
            return
        x = x[:n]
        envelope = 1
        if chapter:
            c = chapters[chapter]
            times = (at + np.arange(n, dtype="float32")) / rate
            smooth = lambda v: np.sin(np.clip(v, 0, 1) * np.pi / 2) ** 2
            envelope = (smooth((times - c["journeyStart"]) / 3) * smooth((c["end"] - times) / 6)
                        if rhythmic else smooth((times - c["start"] + 3) / 6) * smooth((c["end"] + 3 - times) / 6))[:, None]
        mix[at:at + n] += x * envelope * gain * np.array([math.sqrt(1 - pan), math.sqrt(1 + pan)], dtype="float32")

    for event in score["events"]:
        t, kind = event["时间"], event["类型"]
        if t >= duration:
            continue
        chapter, gain = event.get("章节", 0), event["增益"]
        if kind == "采样音符":
            instrument = event["音轨"]
            length = min(event["长度"], duration - t)
            x = voice(instrument, event["MIDI"], length, event["力度"])
            put(x, t, gain * (event["力度"] / 80) ** 1.35, event.get("声像", 0), chapter, instrument == "弦乐")
        elif kind == "合成低音":
            tt = np.arange(round(min(event["长度"], duration - t) * rate), dtype="float32") / rate
            hz = 440 * 2 ** ((event["MIDI"] - 69) / 12)
            x = (np.sin(2 * np.pi * hz * tt) + .1 * np.sin(4 * np.pi * hz * tt)) * np.exp(-tt * 3.3)
            put(fade(np.repeat(x[:, None], 2, axis=1), rate, .025, .22), t, gain, chapter=chapter, rhythmic=True)
        elif kind == "采样节奏片段":
            put(drums[event["片段"]], t, gain, chapter=chapter, rhythmic=True)
        else:
            raise ValueError("未知乐谱事件：" + str(kind))

    for cue in score["cues"]:
        start, peak, end = cue["开始"], cue["峰值"], cue["结束"]
        if start >= duration:
            continue
        tt = np.arange(round((min(end, duration) - start) * rate), dtype="float32") / rate
        cutoff = 1600 if "XT" in cue["名称"] or "RS" in cue["名称"] else 3000 if cue["类型"] == "年代门" else 4300
        x = sosfilt(butter(3, [250, cutoff], fs=rate, btype="band", output="sos"), rng.normal(size=(len(tt), 2)), axis=0).astype("float32")
        x *= np.exp(-((tt - (peak - start)) / max(.06, (end - start) * .2)) ** 2)[:, None]
        put(fade(x, rate, .08, .18), start, .012 if cue["类型"] == "重点过界" else .005, .06)
    for i, air in enumerate(score["air"]):
        if air["开始"] >= duration:
            continue
        length = min(air["长度"], duration - air["开始"])
        tt = np.arange(round(length * rate), dtype="float32") / rate
        x = sosfilt(butter(2, [600, 2000 if air["新材质"] == "leather" else 2800], fs=rate, btype="band", output="sos"), rng.normal(size=(len(tt), 2)), axis=0).astype("float32")
        x *= np.sin(np.pi * tt / air["长度"])[:, None] ** 2
        put(x, air["开始"], .0045, .12 if i % 2 else -.12)
    peak = float(np.max(np.abs(mix)))
    gain = min(1, .9 / peak) if peak else 1
    mix *= gain
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, mix, rate, subtype="PCM_24")
    return {"采样率": rate, "采样帧": count, "时长秒": count / rate, "统一增益": gain,
            "采样峰值": float(np.max(np.abs(mix))), "样本文件数": len(files),
            "边界": "用户样本演奏原乐谱；合成低音与艺术气流不是实录乐器或手机机械声，尚未做最终母带。"}


def main():
    parser = argparse.ArgumentParser(description="用用户提供的样本库重演九章音轨")
    parser.add_argument("--bank", type=Path, help="显式授权的样本库JSON")
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, help="只生成从零开始的短试听")
    args = parser.parse_args()
    if args.bank is None:
        parser.error("没有--bank，不能重建真实采样音轨；不会隐式读取系统音源或网络")
    try:
        print(json.dumps(render(json.loads(args.score.read_text()), args.bank, args.out, args.seconds), ensure_ascii=False))
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

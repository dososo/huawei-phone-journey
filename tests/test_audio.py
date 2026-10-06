"""测试音源为临时自产波形，只检验采样演奏，不冒充真实乐器音色。"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

SCRIPT = Path(__file__).resolve().parents[1] / "skills/huawei-phone-journey/scripts/audio.py"
spec = importlib.util.spec_from_file_location("公开音轨演奏", SCRIPT)
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class AudioTests(unittest.TestCase):
    def fixture(self, root):
        samples = root / "samples"
        samples.mkdir()
        tt = np.arange(2205) / 22050
        # 明确的测试波形；换采样率、单双声道并实际读回文件。
        x = (.4 * np.sin(2 * np.pi * 261.625565 * tt)).astype("float32")
        sf.write(samples / "测试音.wav", x, 22050, subtype="PCM_16")
        bank = {"samples": [{"instrument": name, "file": "samples/测试音.wav", "rootMidi": 60,
                             "velocity": 65, "f0Hz": 261.625565} for name in sorted(audio.INSTRUMENTS)],
                "drums": [{"file": "samples/测试音.wav"} for _ in range(3)]}
        bank_path = root / "bank.json"
        bank_path.write_text(json.dumps(bank, ensure_ascii=False))
        events = [{"类型": "采样音符", "音轨": name, "时间": .05 + i * .08, "长度": .22,
                   "MIDI": 64, "力度": 65, "增益": 3.0, "声像": 0, "章节": 0}
                  for i, name in enumerate(sorted(audio.INSTRUMENTS))]
        events += [{"类型": "合成低音", "时间": .1, "长度": .25, "MIDI": 36, "增益": .3},
                   {"类型": "采样节奏片段", "时间": .2, "片段": 1, "增益": .2}]
        score = {"sampleRate": 48000, "duration": .8, "bpm": 75, "chapters": [], "events": events,
                 "cues": [{"名称": "测试年代门", "类型": "年代门", "开始": .3, "峰值": .4, "结束": .5}],
                 "air": [{"开始": .5, "长度": .2, "新材质": "glass"}]}
        return bank, bank_path, score

    def test_real_wav_full_and_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, bank_path, score = self.fixture(root)
            for seconds in (None, .37):
                out = root / ("完整.wav" if seconds is None else "试听.wav")
                result = audio.render(score, bank_path, out, seconds)
                x, rate = sf.read(out, always_2d=True)
                self.assertEqual(rate, 48000)
                self.assertEqual(x.shape, (round((seconds or .8) * rate), 2))
                self.assertEqual(result["采样帧"], len(x))
                self.assertTrue(np.isfinite(x).all())
                self.assertGreater(float(np.max(np.abs(x))), .001)
                self.assertLessEqual(float(np.max(np.abs(x))), .900001)
                self.assertEqual(sf.info(out).subtype, "PCM_24")
            self.assertLess(result["统一增益"], 1)

    def test_rejects_unauthorized_paths_and_missing_instrument(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bank, bank_path, _ = self.fixture(root)
            for filename in (str((root / "samples/测试音.wav").resolve()), "../未授权.wav"):
                bank["samples"][0]["file"] = filename
                bank_path.write_text(json.dumps(bank, ensure_ascii=False))
                with self.assertRaisesRegex(ValueError, "未授权"):
                    audio.load_bank(bank_path, 48000)
            bank["samples"][0]["file"] = "samples/测试音.wav"
            bank["samples"].pop()
            bank_path.write_text(json.dumps(bank, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, "五类"):
                audio.load_bank(bank_path, 48000)

    def test_rejects_symlink_escape_and_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            root = parent / "bank"
            root.mkdir()
            bank, bank_path, score = self.fixture(root)
            outside = parent / "外部.wav"
            sf.write(outside, np.ones(16, dtype="float32") * .1, 48000)
            (root / "samples/越界.wav").symlink_to(outside)
            bank["drums"][0]["file"] = "samples/越界.wav"
            bank_path.write_text(json.dumps(bank, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, "未授权"):
                audio.load_bank(bank_path, 48000)
            bank["drums"][0]["file"] = "samples/测试音.wav"
            bank_path.write_text(json.dumps(bank, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, "不能覆盖"):
                audio.render(score, bank_path, root / "samples/测试音.wav")

    def test_pitch_and_chapter_rhythm_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, bank_path, score = self.fixture(root)
            score.update(events=[{"类型": "采样音符", "音轨": "钢琴", "时间": 0,
                                  "长度": .3, "MIDI": 64, "力度": 65, "增益": .1}],
                         cues=[], air=[])
            out = root / "音高.wav"
            audio.render(score, bank_path, out)
            x, rate = sf.read(out)
            spectrum = np.abs(np.fft.rfft(x[:4800, 0], 32768))
            peak_hz = np.argmax(spectrum) * rate / 32768
            self.assertTrue(320 < peak_hz < 340, peak_hz)
            # 原始鼓片段确有声音，但章节机型起点前节奏必须留空。
            score.update(chapters=[{"index": 0, "start": .1, "journeyStart": .4, "end": .7}],
                         events=[{"类型": "采样节奏片段", "时间": .1, "片段": 0,
                                  "增益": .5, "章节": 1}])
            out = root / "节奏撤层.wav"
            audio.render(score, bank_path, out)
            self.assertEqual(float(np.max(np.abs(sf.read(out)[0]))), 0)

    def test_cli_requires_bank_and_writes_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, bank_path, score = self.fixture(root)
            score_path, out = root / "score.json", root / "CLI.wav"
            score_path.write_text(json.dumps(score, ensure_ascii=False))
            args = [sys.executable, str(SCRIPT), "--score", str(score_path), "--out", str(out)]
            missing = subprocess.run(args, text=True, capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("不能重建", missing.stderr)
            self.assertFalse(out.exists())
            good = subprocess.run(args + ["--bank", str(bank_path), "--seconds", ".125"], text=True, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(good.stdout)["采样帧"], 6000)
            self.assertEqual(sf.info(out).frames, 6000)


if __name__ == "__main__":
    unittest.main()

"""临时虚构仓库验证发布边界；不读取制作目录或真实凭据。"""
import importlib.util
import json
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_check.py"
spec = importlib.util.spec_from_file_location("发布守卫", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def png_chunk(kind, payload=b""):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def clean_png(extra=b""):
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + extra + png_chunk(b"IDAT", zlib.compress(b"\0\xff\xff\xff")) + png_chunk(b"IEND")


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "public"
        self.root.mkdir()
        self.put("README.md", "公开项目说明\n")

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else text.encode())
        return p

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.DEVNULL)

    def init(self):
        self.git("init", "-q")
        self.git("add", "README.md")

    def categories(self, result):
        return {s for x in result["阻断项"] for s in x["类别"]}

    def test_candidate_ignores_local_media_but_blocks_text_outside_allowlist(self):
        self.put("skills/huawei-phone-journey/assets/phones/local.jpg", b"\0local")
        self.put("output/render.bin", b"\0local")
        self.put("node_modules/local.txt", "本地产物")
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.put("private-note.md", "未授权文件")
        self.assertIn("不在公开文件白名单", self.categories(guard.check(self.root, [])))

    def test_staged_private_content_cannot_be_hidden_by_clean_worktree(self):
        self.init()
        p = self.put("docs/example.md", "/" + "Users" + "/fictional/person.txt")
        self.git("add", "docs/example.md")
        p.write_text("工作树已改干净\n")
        self.assertIn("个人绝对路径", self.categories(guard.check(self.root, [])))

    def test_tracked_worktree_change_is_checked_but_untracked_media_is_not(self):
        self.init()
        self.put("README.md", "访问凭据：" + "gh" + "p_" + "A" * 40)
        self.put("assets/phones/private.jpg", b"\0local")
        self.assertIn("凭据或私钥", self.categories(guard.check(self.root, [])))
        self.put("README.md", "公开项目说明\n")
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")

    def test_git_init_preserves_clean_scope_and_tracked_media_is_blocked(self):
        self.put("assets/audio/local.wav", b"\0local")
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.init()
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.git("add", "assets/audio/local.wav")
        categories = self.categories(guard.check(self.root, []))
        self.assertIn("不在公开文件白名单", categories)
        self.assertIn("二进制或私有媒体", categories)

    def test_email_allowlist_and_other_email_block(self):
        self.put("README.md", guard.CONTACT)
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.put("README.md", "fictional" + "@" + "example.org")
        self.assertIn("未授权邮箱", self.categories(guard.check(self.root, [])))

    def test_json_escape_cannot_hide_personal_path(self):
        p = self.put("skills/huawei-phone-journey/data/catalog.json", json.dumps({"path": "/" + "Users" + "/fictional/file"}))
        p.write_text(p.read_text().replace("Users", "\\u0055sers"))
        self.assertIn("个人绝对路径", self.categories(guard.check(self.root, [])))

    def test_literal_secret_and_tracked_screenshot_folder_are_blocked(self):
        self.put("README.md", "refresh" + "_token = \"" + "Z" * 24 + "\"")
        self.assertIn("明文凭据赋值", self.categories(guard.check(self.root, [])))
        self.put("README.md", "公开说明\n")
        self.init()
        self.put("docs/截图/note.md", "本地截图注释")
        self.git("add", "docs/截图/note.md")
        self.assertIn("不在公开文件白名单", self.categories(guard.check(self.root, [])))

    def test_generic_reference_and_stage_and_private_key_are_blocked(self):
        samples = [("https://" + "claude.ai" + "/artifact/fake", "私有参考链接"),
                   ("https://" + "x.com" + "/fictional/status/123", "私有参考链接"),
                   ("proto" + "type-" + "20260101", "阶段或私有目录"),
                   ("-----BEGIN " + "PRIVATE KEY-----", "凭据或私钥")]
        for text, category in samples:
            with self.subTest(category=category):
                self.put("README.md", text)
                self.assertIn(category, self.categories(guard.check(self.root, [])))

    def test_local_extra_words_never_appear_in_cli_report(self):
        hidden = "fictional-sensitive-marker"
        table = Path(self.temp.name) / "local-only.json"
        table.write_text(json.dumps({"本地分类": [hidden]}))
        self.put("README.md", hidden)
        result = subprocess.run(["python3", str(SCRIPT), "--root", str(self.root), "--deny-file", str(table)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["附加禁词数量"], 1)
        self.assertNotIn(hidden, result.stdout)
        self.assertNotIn(str(table), result.stdout)

    def test_large_file_and_symlink_are_blocked(self):
        self.put("docs/large.txt", b"x" * (guard.LIMIT + 1))
        self.assertIn("超过5MiB", self.categories(guard.check(self.root, [])))
        (self.root / "scripts").mkdir()
        (self.root / "scripts/link.py").symlink_to(SCRIPT)
        self.assertIn("符号链接", self.categories(guard.check(self.root, [])))

    def test_extra_word_in_filename_is_hidden_and_invalid_table_is_rejected(self):
        hidden = "fictional-sensitive-marker"
        self.put("docs/" + hidden + ".md", "文本")
        result = guard.check(self.root, [hidden])
        self.assertNotIn(hidden, json.dumps(result))
        self.assertIn("本地附加禁词", self.categories(result))
        table = Path(self.temp.name) / "local-only.json"
        table.write_text(json.dumps({"本地分类": hidden}))
        with self.assertRaises(ValueError):
            guard.extra_words(table)

    def test_exact_cover_paths_accept_clean_png_before_and_after_git_init(self):
        for name in sorted(guard.PNG_FILES):
            self.put(name, clean_png())
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.init()
        self.git("add", "site")
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        for name in {"site/assets/other.png", "site/cover-3x4.png", "docs/cover-3x4.png", "site/assets/cover-3x4.jpg"}:
            with self.subTest(name=name):
                self.assertFalse(guard.allowed(name))
        self.put("site/assets/other.png", clean_png())
        self.git("add", "site/assets/other.png")
        self.assertIn("不在公开文件白名单", self.categories(guard.check(self.root, [])))

    def test_png_metadata_c2pa_and_unknown_chunks_are_rejected(self):
        for kind in {b"eXIf", b"tEXt", b"iTXt", b"zTXt", b"caBX", b"abcd"}:
            with self.subTest(kind=kind):
                self.put("site/assets/cover-3x4.png", clean_png(png_chunk(kind, b"fictional")))
                self.assertIn("PNG含禁用或未知块", self.categories(guard.check(self.root, [])))

    def test_png_staged_bytes_and_worktree_are_both_checked(self):
        self.init()
        name = "site/assets/cover-4x3.png"
        path = self.put(name, clean_png(png_chunk(b"tEXt", b"fictional")))
        self.git("add", name)
        path.write_bytes(clean_png())
        self.assertIn("PNG含禁用或未知块", self.categories(guard.check(self.root, [])))
        self.git("add", name)
        path.write_bytes(clean_png(png_chunk(b"caBX", b"fictional")))
        self.assertIn("PNG含禁用或未知块", self.categories(guard.check(self.root, [])))

    def test_png_fake_trailing_and_oversized_bytes_are_rejected(self):
        name = "site/assets/cover-16x9.png"
        samples = [(b"fictional image", "PNG签名无效"),
                   (b"\x89PNG\r\n\x1a\n", "PNG缺少结束块"),
                   (clean_png() + b"extra", "PNG尾随数据"),
                   (clean_png() + b"x" * guard.LIMIT, "超过5MiB")]
        for data, category in samples:
            with self.subTest(category=category):
                self.put(name, data)
                self.assertIn(category, self.categories(guard.check(self.root, [])))
        self.init()
        self.git("add", name)
        self.put(name, clean_png())
        self.assertIn("超过5MiB", self.categories(guard.check(self.root, [])))

    def test_png_truncated_crc_missing_image_and_duplicate_header_are_rejected(self):
        data = clean_png()
        samples = [(data[:-1], "PNG块截断"),
                   (data[:-1] + bytes([data[-1] ^ 1]), "PNG块CRC错误"),
                   (data[:33] + png_chunk(b"IEND"), "PNG图像数据缺失或结构无效"),
                   (clean_png(data[8:33]), "PNG类型或结构无效")]
        for raw, category in samples:
            with self.subTest(category=category):
                self.assertIn(category, guard.png_issues(raw))

    def test_png_whitelisted_color_chunks_are_accepted(self):
        chunks = [png_chunk(b"sRGB", b"\0"), png_chunk(b"gAMA", struct.pack(">I", 45455)),
                  png_chunk(b"cHRM", bytes(32)), png_chunk(b"pHYs", struct.pack(">IIB", 100, 100, 1)),
                  png_chunk(b"iCCP", b"fictional\0\0" + zlib.compress(b"profile"))]
        for extra in chunks:
            with self.subTest(extra=extra[:8]):
                self.assertEqual(guard.png_issues(clean_png(extra)), set())

    def test_english_readme_and_four_site_pages_are_exact_and_still_private_checked(self):
        self.put("README.en.md", "Public description")
        for name in sorted(guard.SITE_HTML):
            self.put(name, '<html lang="zh"><button>中文 / English</button></html>')
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        for name in {"README.fr.md", "docs/README.en.png", "site/other.html", "site/assets/index.html"}:
            with self.subTest(name=name):
                self.assertFalse(guard.allowed(name))
        self.init()
        self.git("add", "README.en.md", "site")
        for name in sorted(guard.SITE_HTML):
            with self.subTest(name=name):
                self.put(name, "/" + "Users" + "/fictional/person.txt")
                self.assertIn("个人绝对路径", self.categories(guard.check(self.root, [])))
                self.put(name, "公开页面")
        self.put("README.en.md", "fictional" + "@" + "example.org")
        self.assertIn("未授权邮箱", self.categories(guard.check(self.root, [])))


if __name__ == "__main__":
    unittest.main()

"""临时虚构仓库验证发布边界；不读取制作目录或真实凭据。"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_check.py"
spec = importlib.util.spec_from_file_location("发布守卫", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


PREVIEW_BYTES = (SCRIPT.parent.parent / "site/assets/film-preview.jpg").read_bytes()


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

    def test_private_publishing_paths_are_denied_before_and_after_git_init(self):
        for name in sorted(guard.PRIVATE_FILES):
            with self.subTest(name=name):
                self.assertFalse(guard.allowed(name))
        self.put("docs/发布文案.md", "仅供私用的虚构发布资料")
        self.assertIn("不在公开文件白名单", self.categories(guard.check(self.root, [])))
        self.init()
        self.git("add", "docs/发布文案.md")
        self.assertIn("不在公开文件白名单", self.categories(guard.check(self.root, [])))

    def test_only_exact_approved_film_preview_is_accepted(self):
        self.put(guard.PREVIEW_FILE, PREVIEW_BYTES)
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        self.init()
        self.git("add", guard.PREVIEW_FILE)
        self.assertEqual(guard.check(self.root, [])["状态"], "通过")
        for name in {"site/assets/other.jpg", "site/film-preview.jpg", "docs/film-preview.jpg", "site/assets/film-preview.png"}:
            with self.subTest(name=name):
                self.assertFalse(guard.allowed(name))

    def test_preview_metadata_and_trailing_changes_are_rejected(self):
        samples = [PREVIEW_BYTES[:2] + b"\xff\xfe\x00\x0bfictional" + PREVIEW_BYTES[2:],
                   PREVIEW_BYTES + b"fictional metadata"]
        for raw in samples:
            with self.subTest(size=len(raw)):
                self.put(guard.PREVIEW_FILE, raw)
                self.assertIn("预览图与已核验影片帧不符", self.categories(guard.check(self.root, [])))

    def test_preview_staged_bytes_and_worktree_are_both_checked(self):
        self.init()
        path = self.put(guard.PREVIEW_FILE, PREVIEW_BYTES + b"fictional")
        self.git("add", guard.PREVIEW_FILE)
        path.write_bytes(PREVIEW_BYTES)
        self.assertIn("预览图与已核验影片帧不符", self.categories(guard.check(self.root, [])))
        self.git("add", guard.PREVIEW_FILE)
        path.write_bytes(PREVIEW_BYTES + b"fictional")
        self.assertIn("预览图与已核验影片帧不符", self.categories(guard.check(self.root, [])))

    def test_preview_fake_and_oversized_bytes_are_rejected(self):
        for raw, category in [(b"fictional image", "预览图与已核验影片帧不符"),
                              (PREVIEW_BYTES + b"x" * guard.LIMIT, "超过5MiB")]:
            with self.subTest(category=category):
                self.put(guard.PREVIEW_FILE, raw)
                self.assertIn(category, self.categories(guard.check(self.root, [])))
        self.init()
        self.git("add", guard.PREVIEW_FILE)
        self.put(guard.PREVIEW_FILE, PREVIEW_BYTES)
        self.assertIn("超过5MiB", self.categories(guard.check(self.root, [])))

    def test_english_readme_and_three_site_pages_are_exact_and_still_private_checked(self):
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

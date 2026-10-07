"""核验公开构建边界、成品页面导航与章节数据的一致性。"""
import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts/build_site.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.ids = [], set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src", "poster"):
            if key in attrs:
                self.links.append(attrs[key])


class SiteTest(unittest.TestCase):
    def test_build_refuses_extra_files_without_deleting_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            extra = out / "unexpected.txt"
            extra.write_text("保留")
            with self.assertRaises(ValueError):
                module.build(out)
            self.assertEqual(extra.read_text(), "保留")

    def test_deployment_contains_only_public_allowlist_and_resolves_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            module.build(out)
            expected = set(module.SITE_FILES) | {"data/catalog.json"}
            self.assertEqual({p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}, expected)
            for name in (name for name in module.SITE_FILES if name.endswith(".html")):
                page = Page((out / name).read_text())
                for address in page.links:
                    url = urlsplit(address)
                    if url.scheme:
                        self.assertEqual(url.scheme, "https")
                        continue
                    target = out / unquote(url.path or name)
                    self.assertTrue(target.is_file(), (name, address))
                    if url.fragment:
                        self.assertIn(url.fragment, Page(target.read_text()).ids)

    def test_watch_chapters_match_public_timeline_and_full_release(self):
        text = (ROOT / "site/watch.html").read_text()
        data = json.loads(text.split('<script id="chapter-data" type="application/json">')[1].split("</script>")[0])
        timeline = json.loads((ROOT / "skills/huawei-phone-journey/data/timeline.json").read_text())
        self.assertEqual(data, {k: timeline[k] for k in ("duration", "chapters")})
        self.assertEqual(len(data["chapters"]), 9)
        self.assertEqual(data["duration"], 684.9)
        self.assertEqual(sum(c["count"] for c in data["chapters"]), 556)
        page = Page(text)
        self.assertIn("skip-card", page.ids)
        self.assertIn("pause-clear", page.ids)
        self.assertIn("resume", page.ids)
        self.assertIn("https://github.com/dososo/huawei-phone-journey/releases/download/v2.0.0/huawei-honor-phone-journey-full.mp4", page.links)
        edition = json.loads((ROOT / "site/edition.json").read_text())
        self.assertEqual(edition["videoSHA256"], "98e1a642751208151234c8404d60573874f1af7b5c4452ed34a09e90fdddac94")
        self.assertEqual(edition["displayEntries"], 556)
        self.assertEqual(edition["fps"], 60)
        self.assertTrue(all(c["video"] in page.links for c in edition["chapters"]))

    def test_private_publishing_materials_are_not_deployed_or_linked(self):
        private = {"promotion.html", "copy.md", "发布文案.md", "social-copy.md",
                   "cover-3x4.png", "cover-4x3.png", "cover-16x9.png"}
        public_text = ["README.md", "README.en.md", "ASSET-LICENSE.md", "NOTICE",
                       "CHANGELOG.md", "docs/使用与复现.md", "docs/新版说明.md"]
        public_text += ["site/" + name for name in module.SITE_FILES if name.endswith(".html")]
        for name in public_text:
            with self.subTest(name=name):
                text = (ROOT / name).read_text()
                self.assertFalse(any(part in text for part in private))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            module.build(out)
            self.assertEqual(len([p for p in out.rglob("*") if p.is_file()]), 6)
            self.assertFalse(any(p.name in private for p in out.rglob("*")))
        for name in ("site/index.html", "site/watch.html"):
            self.assertIn("assets/film-preview.jpg", Page((ROOT / name).read_text()).links)


if __name__ == "__main__":
    unittest.main()

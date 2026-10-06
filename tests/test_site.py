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
        self.links, self.ids, self.copies = [], set(), []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if "data-copy" in attrs:
            self.copies.append(attrs["data-copy"])
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
            expected = set(module.SITE_FILES) | {"data/catalog.json", "copy.md"}
            self.assertEqual({p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}, expected)
            for name in module.SITE_FILES[:4]:
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
        self.assertEqual(data["duration"], 772.7)
        page = Page(text)
        self.assertIn("skip-card", page.ids)
        self.assertIn("preview", page.ids)
        self.assertIn("https://github.com/dososo/huawei-phone-journey/releases/download/v1.0.0/huawei-phone-journey-full.mp4", page.links)

    def test_six_platform_copy_targets_and_creative_intent_are_preserved(self):
        text = (ROOT / "site/promotion.html").read_text()
        page = Page(text)
        self.assertEqual(len(page.copies), 16)
        self.assertEqual(len(set(page.copies)), 16)
        self.assertTrue(set(page.copies) <= page.ids)
        self.assertEqual(text.count("初衷不是追逐流量"), 5)
        self.assertEqual(text.count("not to chase views"), 2)


if __name__ == "__main__":
    unittest.main()

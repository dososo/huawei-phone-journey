"""仅复制明确的公开成品文件，构建 GitHub Pages 目录。"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_FILES = [
    "index.html", "watch.html", "promotion.html", "catalog.html", "edition.json",
    "assets/cover-3x4.png", "assets/cover-4x3.png", "assets/cover-16x9.png",
]


def build(destination):
    expected = set(SITE_FILES) | {"data/catalog.json", "copy.md"}
    if destination.exists():
        if any(p.is_symlink() or (p.is_file() and p.relative_to(destination).as_posix() not in expected) for p in destination.rglob("*")):
            raise ValueError("目标目录含非公开文件或符号链接；请另选空目录。")
    for name in SITE_FILES:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "site" / name, target)
    (destination / "data").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "skills/huawei-phone-journey/data/catalog.json", destination / "data/catalog.json")
    shutil.copyfile(ROOT / "docs/发布文案.md", destination / "copy.md")
    print("已构建10个公开文件；没有复制原图库、音源库或阶段目录。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output/site")
    build(parser.parse_args().out.resolve())

"""只读发布守卫：精确文件白名单、敏感信息与 Git 索引/跟踪文件双检。"""
import argparse
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

LIMIT = 5 * 1024 * 1024
CONTACT = "blteam2026@outlook.com"
ROOT_NAMES = {"README", "LICENSE", "NOTICE", "ASSET-LICENSE", "CONTRIBUTING", "CHANGELOG"}
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".yml", ".yaml", ".toml", ".sh", ".command"}
LOCAL_DIRS = {".git", "node_modules", "output", "输出", ".hyperframes", ".thumbnails", ".waveform-cache", "__pycache__", "snapshots", "screenshots", "cache", "logs", "log", "截图", "截屏", "核验", "修订前"}
PRIVATE_PARTS = {"reference", "references", "private", "cache", "logs", "log", "snapshots", "screenshots", "media", "截图", "截屏", "核验", "修订前"}
PRIVATE_FILES = {"site/promotion.html", "docs/发布文案.md", "site/copy.md",
                 "site/assets/cover-3x4.png", "site/assets/cover-4x3.png", "site/assets/cover-16x9.png"}
PREVIEW_FILE = "site/assets/film-preview.jpg"
# 只接受已实看、移除附加元数据的成片实帧；更换预览需重新核验此摘要。
PREVIEW_SHA256 = "bc8c76aff65476ff01a6316369782164d2bd1f6abec55cd96b954312771c3b26"
SITE_HTML = {"site/index.html", "site/watch.html", "site/catalog.html"}
RULES = {
    "个人绝对路径": r"(?:/|\\/)(?:Users|home|private[/]var|var[/]folders|Volumes)(?:/|\\/)|[A-Za-z]:[\\/]+(?:Users|Documents and Settings)[\\/]+|file[:][/][/]|~[/]",
    "凭据或私钥": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})\b|-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----|\bBearer[ \t]+[A-Za-z0-9._~+/-]{16,}|\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b",
    "私有参考链接": r"https?://(?:www\.)?(?:claude\.ai/(?:artifact|share)/|(?:x|twitter)\.com/[^/\s]+/status/)",
    "阶段或私有目录": r"\b(?:research|prototype|full|audio|compact|promotion)-\d{8}\b|(?:research|reference|private|cache|logs?|snapshots?|screenshots?|核验|修订前)[\\/]+",
    "会话或追踪标识": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|(?:thread|session|cell|providerTab|tab)[_-]?id[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_-]{4,}",
    "嵌入媒体": r"data:(?:image|audio|video)/",
}
EMAIL = re.compile(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+", re.I)
LITERAL_SECRET = re.compile(r"(?:^|[,{;\n])\s*[\"']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|password|client[_-]?secret|secret[_-]?key|private[_-]?key)[\"']?\s*[:=]\s*[\"']([^\"'\r\n]{8,})[\"']", re.I)


def allowed(name):
    p = PurePosixPath(name)
    if name in PRIVATE_FILES or p.is_absolute() or ".." in p.parts or any(x.lower() in PRIVATE_PARTS for x in p.parts):
        return False
    if name in {"README.en.md", "site/edition.json", PREVIEW_FILE} or name in SITE_HTML:
        return True
    if len(p.parts) == 1:
        return name == ".gitignore" or (p.stem in ROOT_NAMES and p.suffix in {"", ".md", ".txt"})
    if p.suffix not in TEXT_SUFFIXES:
        return False
    if p.parts[0] in {".github", "docs", "tests", "scripts"}:
        return True
    prefix = ("skills", "huawei-phone-journey")
    if p.parts[:2] != prefix:
        return False
    tail = p.parts[2:]
    if len(tail) == 1:
        return tail[0] in {"index.html", "package.json", "package-lock.json", "hyperframes.json", "SKILL.md"}
    if tail[0] in {"src", "scripts"}:
        return True
    return tail in {("data", "catalog.json"), ("data", "timeline.json"), ("data", "score.json"), ("examples", "catalog.json"), ("examples", "audio-bank.json")}


def extra_words(path):
    if path is None:
        return []
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        if isinstance(data, dict):
            if not all(isinstance(group, list) for group in data.values()):
                raise ValueError("附加禁词分类值需为数组")
            data = [word for group in data.values() for word in group]
        if not isinstance(data, list) or not all(isinstance(word, str) for word in data):
            raise ValueError("附加禁词表需为字符串数组或分类数组对象")
    else:
        data = [s.strip() for s in raw.splitlines() if s.strip() and not s.lstrip().startswith("#")]
    return sorted({s.casefold() for s in data if s})


def sensitive(text, words):
    text = html.unescape(unquote(unquote(text)))
    result = {name for name, pattern in RULES.items() if re.search(pattern, text, re.I)}
    if any(x.casefold() != CONTACT for x in EMAIL.findall(text)):
        result.add("未授权邮箱")
    if LITERAL_SECRET.search(text):
        result.add("明文凭据赋值")
    if any(word in text.casefold() for word in words):
        result.add("本地附加禁词")
    return result


def text_issues(data, suffix, words):
    if len(data) > LIMIT:
        return {"超过5MiB"}
    if b"\0" in data:
        return {"二进制或私有媒体"}
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {"非UTF8文本"}
    found = sensitive(text, words)
    if suffix == ".json":
        try:
            value = json.loads(text)
        except ValueError:
            return found | {"JSON格式错误"}
        # 检查解码后的字符串，防止 Unicode 转义隐藏敏感内容。
        def visit(item):
            if isinstance(item, str):
                found.update(sensitive(item, words))
            elif isinstance(item, dict):
                for key, v in item.items():
                    visit(key)
                    visit(v)
            elif isinstance(item, list):
                for v in item:
                    visit(v)
        visit(value)
    return found


def preview_issues(data):
    """精确核验已批准实帧，不开放任意图片或附加元数据。"""
    if len(data) > LIMIT:
        return {"超过5MiB"}
    if hashlib.sha256(data).hexdigest() != PREVIEW_SHA256:
        return {"预览图与已核验影片帧不符"}
    return set()


def file_issues(data, name, words):
    return preview_issues(data) if name == PREVIEW_FILE else text_issues(data, PurePosixPath(name).suffix, words)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def candidates(root):
    for p in root.rglob("*"):
        parts = p.relative_to(root).parts
        if any(x in LOCAL_DIRS for x in parts) or any(parts[i:i + 2] in {("assets", "phones"), ("assets", "audio")} for i in range(len(parts) - 1)):
            continue
        if p.name == ".DS_Store":
            continue
        if p.is_file() or p.is_symlink():
            yield p.relative_to(root).as_posix(), None, None


def check(root, words):
    tracked = git(root, "ls-files", "--stage", "-z", "--", ".")
    indexed = tracked.returncode == 0
    entries = []
    if indexed:
        for raw in tracked.stdout.split(b"\0"):
            if not raw:
                continue
            meta, name = raw.split(b"\t", 1)
            mode, oid, stage = meta.decode("ascii").split()
            entries.append((name.decode("utf-8", "surrogateescape"), (mode, stage), oid))
    else:
        entries = list(candidates(root))
    failures = []
    for name, mode_stage, oid in sorted(entries):
        issues = sensitive(name, words)
        if not allowed(name):
            issues.add("不在公开文件白名单")
        path = root / name
        if mode_stage is not None:
            mode, stage = mode_stage
            if mode not in {"100644", "100755"} or stage != "0":
                issues.add("符号链接、子模块或冲突索引")
            size = git(root, "cat-file", "-s", oid)
            if size.returncode:
                issues.add("索引字节不可读取")
            elif int(size.stdout) > LIMIT:
                issues.add("超过5MiB")
            else:
                blob = git(root, "cat-file", "blob", oid)
                if blob.returncode:
                    issues.add("索引字节不可读取")
                else:
                    issues.update(file_issues(blob.stdout, name, words))
        if path.is_symlink():
            issues.add("符号链接")
        elif path.is_file():
            if path.stat().st_size > LIMIT:
                issues.add("超过5MiB")
            else:
                issues.update(file_issues(path.read_bytes(), name, words))
        if issues:
            failures.append({"文件": "[敏感路径已隐藏]" if sensitive(name, words) else name, "类别": sorted(issues)})
    if not entries:
        failures.append({"文件": "[清单]", "类别": ["没有可核验的公开源文件"]})
    return {"状态": "阻断" if failures else "通过", "扫描口径": "Git索引清单；索引字节和工作树跟踪文件双检" if indexed else "候选公共目录；自动排除本地产物", "文件数": len(entries), "附加禁词数量": len(words), "阻断项": failures, "边界": "未跟踪文件及Git历史未审查；本轮不替代素材许可、媒体脱敏或上传验收。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--deny-file", type=Path, help="本地附加禁词表，不输出内容或表路径")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        if not root.is_dir():
            raise ValueError("公开目录不存在")
        result = check(root, extra_words(args.deny_file))
    except (OSError, ValueError, RecursionError):
        print(json.dumps({"状态": "阻断", "类别": "目录或附加禁词表读取失败", "秘密内容": "未回显"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["阻断项"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

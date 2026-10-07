#!/usr/bin/env python3
"""资料检查、真实图片导入、本地播放和可导出工程构建。"""
import argparse
import json
import re
import shutil
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate():
    catalog, plan, score = read('data/catalog.json'), read('data/timeline.json'), read('data/score.json')
    models = {m['id']: m for m in catalog['models']}
    ids = catalog['journeyIds']
    if len(models) != len(catalog['models']) or len(ids) != len(set(ids)):
        raise ValueError('资料ID或游历ID重复')
    if [e['id'] for e in plan['entries']] != ids:
        raise ValueError('时间线与游历节点不一致')
    dates = [(models[i]['year'], models[i]['month']) for i in ids]
    if dates != sorted(dates) or any(not 1 <= month <= 12 for _, month in dates):
        raise ValueError('年月排序或月份范围错误')
    if len(plan['chapters']) != 9 or plan['chapterCount'] != 9:
        raise ValueError('九章数量不正确')
    spans = [(0, plan['introEnd']), (plan['outroStart'], plan['duration'])]
    spans += [(c['cardStart'], c['cardEnd']) for c in plan['chapters']]
    spans += [(e['start'], e['end']) for e in plan['entries']]
    spans.sort()
    if spans[0][0] != 0 or spans[-1][1] != plan['duration']:
        raise ValueError('时间线头尾不完整')
    if any(end <= start or any(abs(t * plan['fps'] - round(t * plan['fps'])) > 1e-6 for t in (start, end)) for start, end in spans):
        raise ValueError('时间段长度或帧边界错误')
    if any(abs(a[1] - b[0]) > 1e-7 for a, b in zip(spans, spans[1:])):
        raise ValueError('时间线存在间隙或重叠')
    if any((models[i]['release']['year'], models[i]['release']['month']) != (models[i]['year'], models[i]['month']) for i in ids):
        raise ValueError('展示年月与资料年月不一致')
    if abs(plan['totalFrames'] / plan['fps'] - plan['duration']) > 1e-7 or score['duration'] != plan['duration']:
        raise ValueError('音画总时长不一致')
    result = {'资料记录': len(models), '游历节点': len(ids), '章节': 9, '秒': plan['duration'], '帧率': plan['fps'], '帧': plan['totalFrames'], '乐谱事件': len(score['events'])}
    print(json.dumps(result, ensure_ascii=False))
    return result


def inventory():
    result = {m['id']: m['image']['path'] for m in read('data/catalog.json')['models'] if (ROOT / m['image']['path']).is_file()}
    save(ROOT / 'assets/inventory.json', result)
    return result


def write_image(content, dest):
    from io import BytesIO
    from PIL import Image, ImageOps
    with Image.open(BytesIO(content)) as image:
        image.load()
        result = ImageOps.exif_transpose(image).convert('RGBA' if 'A' in image.getbands() else 'RGB')
        clean = Image.new(result.mode, result.size)
        clean.paste(result)
        dest.parent.mkdir(parents=True, exist_ok=True)
        clean.save(dest, format='PNG')


def fetch_images(args):
    if not args.yes:
        raise ValueError('下载会访问图片原来源；请显式提供--yes')
    catalog = read('data/catalog.json')
    chosen = set(catalog['journeyIds']) if args.all else set((args.ids or '').split(','))
    if chosen == {''} or not chosen:
        raise ValueError('请选择--ids或--all')
    models = {m['id']: m for m in catalog['models']}
    if chosen - models.keys():
        raise ValueError('包含不存在的机型ID')
    completed, failed = 0, []
    for id in sorted(chosen):
        m = models[id]
        dest = ROOT / m['image']['path']
        if dest.is_file():
            completed += 1
            continue
        url = m['image']['url']
        if not url.startswith(('https://', 'http://')):
            failed.append({'ID': id, '原因': '缺少公开图片网址'})
            continue
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'HuaweiPhoneJourney/1.0', 'Referer': m['image']['pageUrl'] or url})
            with urllib.request.urlopen(request, timeout=25) as response:
                content = response.read(30 * 1024 * 1024 + 1)
            if len(content) > 30 * 1024 * 1024:
                raise ValueError('单图超过30MB')
            write_image(content, dest)
            completed += 1
        except Exception as error:
            failed.append({'ID': id, '原因': type(error).__name__})
    inventory()
    print(json.dumps({'已存在或下载': completed, '失败': failed}, ensure_ascii=False))
    return bool(failed)


def import_images(args):
    source = Path(args.source).resolve()
    mapping = json.loads(Path(args.map).read_text()) if args.map else {}
    models = read('data/catalog.json')['models']
    count = 0
    for m in models:
        name = mapping.get(m['id'])
        candidates = [source / name] if name else [source / (m['id'] + ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']]
        file = next((p for p in candidates if p.is_file()), None)
        if file is None:
            continue
        if not file.resolve().is_relative_to(source):
            raise ValueError('映射文件必须位于提供的图片目录内')
        dest = ROOT / m['image']['path']
        if dest.resolve() == file.resolve():
            raise ValueError('请使用独立输入目录，避免覆盖原图')
        write_image(file.read_bytes(), dest)
        count += 1
    inventory()
    print(json.dumps({'导入真实图片': count, '元数据': '导入副本只保留像素，原文件不改'}, ensure_ascii=False))


def serve(args):
    inventory()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
    print(f'打开 http://127.0.0.1:{args.port}/index.html', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def build(args):
    validate()
    source = ROOT / 'node_modules/gsap/dist/gsap.min.js'
    if not source.is_file():
        raise ValueError('导出依赖尚未安装，请在技能目录运行npm install')
    dest = Path(args.out).resolve()
    if dest == ROOT or dest in ROOT.parents:
        raise ValueError('构建输出必须为独立子目录')
    plan = read('data/timeline.json')
    duration, fps = plan['duration'], plan['fps']
    length = args.seconds if args.seconds is not None else duration - args.start
    if args.start < 0 or length <= 0 or args.start + length > duration + 1e-7:
        raise ValueError('导出时间段越界')
    if any(abs(t * fps - round(t * fps)) > 1e-6 for t in (args.start, length)):
        raise ValueError('导出秒数须与时间线帧边界对齐')
    dest.mkdir(parents=True, exist_ok=True)
    for directory in ['src', 'data']:
        shutil.copytree(ROOT / directory, dest / directory, dirs_exist_ok=True)
    (dest / 'vendor').mkdir(exist_ok=True)
    shutil.copy2(source, dest / 'vendor/gsap.min.js')
    registered = inventory()
    for file in set(registered.values()):
        target = dest / file
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / file, target)
    save(dest / 'assets/inventory.json', registered)
    page = (ROOT / 'index.html').read_text()
    page = page.replace('<!--RENDER_LIBRARY-->', '<script src="vendor/gsap.min.js"></script><script>window.RenderSettings=' + json.dumps({'start': args.start, 'duration': length}) + ';</script>')
    page = re.sub(r'data-duration="[^"]+"', f'data-duration="{length}"', page.replace('<body>', '<body class="render">'))
    page = page.replace('<main>', f'<main data-composition-id="phone-journey" data-start="0" data-width="1920" data-height="1080" data-duration="{length}" data-fps="{fps}">')
    page = page.replace(f'id="root" data-composition-id="phone-journey" data-width="1920" data-height="1080" data-duration="{length}" data-fps="{fps}"', 'id="root"')
    page = page.replace('<script src="src/app.js"></script>', '<script>' + (ROOT / 'src/app.js').read_text() + '</script>')
    page = page.replace('<script src="src/player.js"></script>', '')
    if args.audio:
        if args.start:
            raise ValueError('带声音的构建目前从00:00开始；选段音频请先自行裁好并从0构建')
        sound = Path(args.audio)
        if sound.suffix.lower() not in ['.wav', '.mp3', '.m4a']:
            raise ValueError('音轨格式须为wav、mp3或m4a')
        target = dest / 'assets' / ('soundtrack' + sound.suffix.lower())
        shutil.copy2(sound, target)
        audio = f'<audio id="journey-audio" class="clip" src="assets/{target.name}" data-start="0" data-duration="{length}" data-track-index="10" data-volume="1"></audio>'
        page = page.replace('<!--RENDER_AUDIO-->', audio)
    (dest / 'index.html').write_text(page)
    shutil.copy2(ROOT / 'hyperframes.json', dest / 'hyperframes.json')
    save(dest / 'build.json', {'start': args.start, 'duration': length, 'fps': fps, 'frames': round(length * fps), 'loadedImages': len(registered), 'imageFilesIncludedInRepository': False})
    print(json.dumps({'工程': dest.name, '秒': length, '帧率': fps, '帧': round(length * fps), '真实图片': len(registered)}, ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='检查资料和时间线')
    p = sub.add_parser('serve', help='仅在本机打开网页'); p.add_argument('--port', type=int, default=8780)
    p = sub.add_parser('fetch', help='显式下载图片到本地忽略目录'); p.add_argument('--ids'); p.add_argument('--all', action='store_true'); p.add_argument('--yes', action='store_true')
    p = sub.add_parser('import-images', help='复制真实图片并移除副本元数据'); p.add_argument('--from', dest='source', required=True); p.add_argument('--map', help='ID到输入文件相对位置的JSON')
    p = sub.add_parser('build', help='生成独立HyperFrames工程'); p.add_argument('--out', default=str(ROOT / 'output/project')); p.add_argument('--start', type=float, default=0); p.add_argument('--seconds', type=float); p.add_argument('--audio')
    args = parser.parse_args(argv)
    try:
        if args.command == 'check': validate()
        elif args.command == 'serve': serve(args)
        elif args.command == 'fetch': return int(fetch_images(args))
        elif args.command == 'import-images': import_images(args)
        elif args.command == 'build': build(args)
    except (ValueError, OSError) as error:
        parser.exit(1, '错误：' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

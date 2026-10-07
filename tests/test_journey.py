"""核查全量节点、年月与图片副本的隐私边界。"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / 'skills/huawei-phone-journey'
spec = importlib.util.spec_from_file_location('journey', SKILL / 'scripts/journey.py')
journey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(journey)


class JourneyTests(unittest.TestCase):
    def test_all_nodes_and_frames(self):
        result = journey.validate()
        self.assertEqual(result['游历节点'], 556)
        self.assertEqual(result['帧率'], 60)
        self.assertEqual(result['帧'], 41094)
        self.assertEqual(result['乐谱事件'], 2427)

    def test_new_film_has_all_brands_and_corrected_variants(self):
        catalog = journey.read('data/catalog.json')
        by_id = {m['id']: m for m in catalog['models']}
        entries = [by_id[i] for i in catalog['journeyIds']]
        self.assertEqual(sum(m['brand'] == '华为' for m in entries), 451)
        self.assertEqual(sum(m['brand'] == '荣耀' for m in entries), 105)
        self.assertEqual(by_id['honor-honorplay8c-03071288']['release']['year'], 2018)
        self.assertEqual(by_id['honor-honor9x-62859e36']['release']['month'], 7)
        self.assertEqual(by_id['honor-honor6apro-fc41a996']['name'], 'Honor 6A（Pro来源称谓）')
        self.assertTrue(all(m['nativeSize'][0] > 0 and m['nativeSize'][1] > 0 for m in entries))

    def test_rejects_timeline_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); shutil.copytree(SKILL / 'data', base / 'data')
            plan = json.loads((base / 'data/timeline.json').read_text())
            plan['entries'][1]['start'] += 1 / 60
            (base / 'data/timeline.json').write_text(json.dumps(plan))
            original_root = journey.ROOT; journey.ROOT = base
            try:
                with self.assertRaisesRegex(ValueError, '间隙或重叠'):
                    journey.validate()
            finally:
                journey.ROOT = original_root

    def test_build_uses_60fps_and_only_render_clock(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for directory in ['data', 'src']:
                shutil.copytree(SKILL / directory, base / directory)
            for name in ['index.html', 'hyperframes.json']:
                shutil.copy2(SKILL / name, base / name)
            vendor = base / 'node_modules/gsap/dist'; vendor.mkdir(parents=True)
            (vendor / 'gsap.min.js').write_text('/* 测试依赖占位，只检查构建内容 */')
            original_root = journey.ROOT; journey.ROOT = base
            try:
                out = base / 'output/project'
                journey.build(SimpleNamespace(out=str(out), start=0, seconds=1 / 60, audio=None))
                build = json.loads((out / 'build.json').read_text())
                self.assertEqual((build['fps'], build['frames']), (60, 1))
                page = (out / 'index.html').read_text()
                self.assertIn('data-fps="60"', page)
                self.assertIn('src/focus.js', page)
                self.assertNotIn('src/player.js', page)
                self.assertNotIn('src/compact.js', page)
                self.assertEqual(page.count('data-composition-id="phone-journey"'), 1)
                with self.assertRaisesRegex(ValueError, '帧边界'):
                    journey.build(SimpleNamespace(out=str(out), start=1 / 120, seconds=1 / 60, audio=None))
            finally:
                journey.ROOT = original_root

    def test_month_order_and_inferred_labels(self):
        catalog = journey.read('data/catalog.json')
        models = {m['id']: m for m in catalog['models']}
        entries = [models[id] for id in catalog['journeyIds']]
        self.assertEqual([(m['year'], m['month']) for m in entries], sorted((m['year'], m['month']) for m in entries))
        inferred = [m for m in entries if m['release']['inferredYear'] or m['release']['inferredMonth']]
        self.assertTrue(inferred)
        self.assertTrue(all('推断' in m['release']['displayLabel'] for m in inferred))
        nova = next(i for i, m in enumerate(entries) if m['name'] == 'nova 16')
        mate = next(i for i, m in enumerate(entries) if m['name'] == 'Mate 90 RS 非凡大师')
        self.assertLess(nova, mate)

    def test_import_removes_metadata_preserves_pixels_and_original(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'input.png'
            image = Image.new('RGB', (27, 19), (90, 120, 160))
            exif = Image.Exif(); exif[315] = '测试作者'; exif[270] = '测试隐私字段'
            image.save(source, exif=exif)
            original = source.read_bytes()
            target = base / 'output.png'
            journey.write_image(original, target)
            with Image.open(target) as copy:
                self.assertEqual(copy.tobytes(), image.tobytes())
                self.assertFalse(copy.getexif())
                self.assertFalse(copy.info)
            self.assertEqual(source.read_bytes(), original)

    def test_import_mapping_cannot_leave_input_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); (base / 'data').mkdir(); (base / 'input').mkdir()
            Image.new('RGB', (2, 2)).save(base / 'outside.png')
            (base / 'data/catalog.json').write_text(json.dumps({'models': [{'id': 'test-phone', 'image': {'path': 'assets/phones/test-phone.png'}}]}))
            mapping = base / 'map.json'; mapping.write_text(json.dumps({'test-phone': '../outside.png'}))
            original_root = journey.ROOT; journey.ROOT = base
            try:
                with self.assertRaises(ValueError):
                    journey.import_images(SimpleNamespace(source=str(base / 'input'), map=str(mapping)))
            finally:
                journey.ROOT = original_root


if __name__ == '__main__':
    unittest.main()

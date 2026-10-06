"""核查全量节点、年月与图片副本的隐私边界。"""
import importlib.util
import json
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
        self.assertEqual(result['游历节点'], 451)
        self.assertEqual(result['帧'], 23181)
        self.assertEqual(result['乐谱事件'], 2446)

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

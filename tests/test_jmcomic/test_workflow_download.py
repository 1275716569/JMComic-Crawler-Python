import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from jmcomic import DirRule, JmAlbumDetail, JmOption, JmPhotoDetail

project_dir = str(Path(__file__).resolve().parents[2])
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from usage.workflow_download import (
    WorkflowCompressionStats,
    WorkflowImageCompressPlugin,
    WorkflowImageCompressSummaryPlugin,
    compress_image_in_place,
    cover_option_config,
)


class TestWorkflowImageCompression(unittest.TestCase):

    def test_stats_are_thread_safe(self):
        stats = WorkflowCompressionStats()

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(lambda _: stats.record(100, 40), range(100)))

        self.assertEqual((100, 10000, 4000), stats.snapshot())

    def test_image_and_summary_logs_include_compression_metrics(self):
        stats = WorkflowCompressionStats()
        image = type('ImageDetail', (), {'save_path': '/tmp/page.webp'})()
        image_logs = []
        image_plugin = WorkflowImageCompressPlugin(None)
        image_plugin.log = image_logs.append

        with patch(
            'usage.workflow_download.compress_image_in_place',
            return_value=('JPEG', 2048, 512, True, '/tmp/page.jpg', None),
        ):
            image_plugin.invoke(image=image, quality=80, stats=stats, convert_to_jpeg=True)

        self.assertEqual('/tmp/page.jpg', image.save_path)
        self.assertEqual((1, 2048, 512), stats.snapshot())
        self.assertIn('压缩比 4.00:1', image_logs[0])

        summary_logs = []
        summary_plugin = WorkflowImageCompressSummaryPlugin(None)
        summary_plugin.log = summary_logs.append
        summary_plugin.invoke(stats=stats)

        self.assertIn('总压缩比 4.00:1', summary_logs[0])
        self.assertIn('总压缩率 75.0%', summary_logs[0])

    def test_multi_frame_webp_is_preserved(self):
        with TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / 'animated.webp'
            frames = [
                Image.new('RGB', (32, 32), color)
                for color in ('red', 'green', 'blue')
            ]
            frames[0].save(
                image_path,
                format='WEBP',
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0,
            )
            original_content = image_path.read_bytes()

            result = compress_image_in_place(str(image_path), quality=50, convert_to_jpeg=True)

            self.assertEqual('multi_frame', result[-1])
            self.assertEqual(original_content, image_path.read_bytes())
            with Image.open(image_path) as image:
                self.assertEqual(3, image.n_frames)


class TestWorkflowExport(unittest.TestCase):

    def make_option(self, directory):
        option = JmOption.default()
        option.dir_rule = DirRule('Bd_Pid', base_dir=directory)
        cover_option_config(option)
        return option

    def test_default_exports_separate_chapters_in_page_order(self):
        with TemporaryDirectory() as temp_dir, patch.dict('os.environ', {}, clear=True):
            option = self.make_option(temp_dir)
            album = JmAlbumDetail(
                '123', '', '测试本子', [], 4, '', '', 0, 0, 0, [], [], [], [],
            )
            for index, photo_id in enumerate(('456', '789'), start=1):
                photo = JmPhotoDetail(photo_id, '测试章节', '123', index, from_album=album)
                page_dir = Path(option.decide_image_save_dir(photo))
                page_dir.mkdir(parents=True, exist_ok=True)
                # 故意先写第二页，同时验证不同页宽会等比例缩放。
                Image.new('RGB', (20, 40), 'blue').save(page_dir / '00002.png')
                Image.new('RGB', (10, 10), 'red').save(page_dir / '00001.png')
                option.call_all_plugin('after_photo', photo=photo)

                output_path = Path(temp_dir) / 'long_img' / (
                    f'[JM123] 第{index}章-JM{photo_id}-测试章节.png'
                )
                with Image.open(output_path) as image:
                    self.assertEqual('PNG', image.format)
                    self.assertEqual((10, 30), image.size)
                    self.assertEqual((255, 0, 0), image.getpixel((0, 0)))
                    self.assertEqual((0, 0, 255), image.getpixel((0, 10)))
                self.assertEqual([], list(page_dir.glob('*.png')))

            self.assertEqual(2, len(list(Path(temp_dir).rglob('*.png'))))
            self.assertEqual([], list(Path(temp_dir).rglob('*.pdf')))

    def test_keep_pages_disables_export(self):
        with TemporaryDirectory() as temp_dir, patch.dict('os.environ', {'PDF_OPTION': '否'}, clear=True):
            option = self.make_option(temp_dir)
            self.assertFalse(option.plugins.get('after_photo'))
            self.assertFalse(option.plugins.get('after_album'))

    def test_pdf_modes_still_export_at_requested_level(self):
        for level, label in (('after_photo', '章节'), ('after_album', '本子')):
            with self.subTest(level=level), TemporaryDirectory() as temp_dir, patch.dict(
                'os.environ', {'PDF_OPTION': f'是 | {label}维度合并pdf'}, clear=True,
            ):
                option = self.make_option(temp_dir)
                self.assertEqual('img2pdf', option.plugins[level][0]['plugin'])
                self.assertTrue(option.plugins[level][0]['kwargs']['delete_original_file'])


if __name__ == '__main__':
    unittest.main()

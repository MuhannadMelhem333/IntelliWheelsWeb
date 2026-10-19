import copy
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('video_validation', Path(__file__).parent / 'app/video_validation.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VideoValidationTest(unittest.TestCase):
    def setUp(self):
        self.config = {'FFPROBE_PATH': 'ffprobe', 'VIDEO_UPLOAD_MAX_SECONDS': 120}
        self.metadata = {'format': {'duration': '12.5'}, 'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'width': 1920, 'height': 1080}]}

    def test_valid_metadata(self):
        with patch.object(module, 'probe_video', return_value=self.metadata):
            module.validate_video(io.BytesIO(), self.config)

    def test_invalid_duration_dimensions_audio_only_and_attached_picture(self):
        invalid = []
        for duration in ('NaN', 'Infinity', '0', '-1', '121', 'N/A'):
            item = copy.deepcopy(self.metadata); item['format']['duration'] = duration; invalid.append(item)
        for change in ({'width': 0}, {'height': 10001}, {'width': True}, {'codec_name': 'unknown'},
                       {'codec_type': 'audio'}, {'disposition': {'attached_pic': 1}}, {'duration': '121'}):
            item = copy.deepcopy(self.metadata); item['streams'][0].update(change); invalid.append(item)
        invalid.extend([{}, None, {'format': {'duration': 1}, 'streams': []}])
        for item in invalid:
            with self.subTest(metadata=item), patch.object(module, 'probe_video', return_value=item):
                with self.assertRaises(module.VideoRejected):
                    module.validate_video(io.BytesIO(), self.config)

    def test_missing_tool_is_unavailable_not_valid(self):
        with patch.object(module.shutil, 'which', return_value=None):
            with self.assertRaises(module.VideoValidatorUnavailable):
                module.probe_video(io.BytesIO(b'fixture'), 'missing')

    def test_subprocess_is_bounded_and_tempfile_removed_on_timeout(self):
        seen = []
        def timeout(command, **options):
            path = Path(command[-1]); seen.append(path)
            self.assertEqual(path.read_bytes(), b'fixture')
            self.assertFalse(options['shell']); self.assertEqual(options['timeout'], 15)
            self.assertEqual(command[command.index('-protocol_whitelist') + 1], 'file')
            raise subprocess.TimeoutExpired(command, 15)
        stream = io.BytesIO(b'fixture')
        with patch.object(module.shutil, 'which', return_value='fixture-probe'), patch.object(module.subprocess, 'run', side_effect=timeout):
            with self.assertRaises(module.VideoRejected): module.probe_video(stream, 'ffprobe')
        self.assertEqual(stream.tell(), 0); self.assertFalse(seen[0].exists())

    def test_real_ffprobe_accepts_generated_video_and_rejects_header_only(self):
        probe = os.environ.get('FFPROBE_PATH') or shutil.which('ffprobe')
        encoder = os.environ.get('FFMPEG_PATH') or shutil.which('ffmpeg')
        if not probe or not encoder:
            if os.environ.get('REQUIRE_VIDEO_TOOLS') == '1':
                self.fail('FFmpeg/ffprobe missing from required validation environment')
            self.skipTest('FFmpeg/ffprobe required for real-media acceptance')
        with tempfile.TemporaryDirectory(prefix='intelliwheels-video-test-') as directory:
            path = Path(directory) / 'fixture.mp4'
            subprocess.run([encoder, '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=32x32:r=10',
                            '-t', '1', '-c:v', 'mpeg4', '-threads', '1', str(path)],
                           check=True, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            stream = io.BytesIO(path.read_bytes())
            module.validate_video(stream, {**self.config, 'FFPROBE_PATH': probe})
            self.assertEqual(stream.tell(), 0)
            with self.assertRaises(module.VideoRejected):
                module.validate_video(io.BytesIO(b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isommp42'), {**self.config, 'FFPROBE_PATH': probe})


if __name__ == '__main__':
    unittest.main()

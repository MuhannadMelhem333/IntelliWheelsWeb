"""Bounded ffprobe metadata inspection. Not a complete decode or malware scan."""
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile


class VideoRejected(ValueError):
    pass


class VideoValidatorUnavailable(RuntimeError):
    pass


def probe_video(stream, executable):
    resolved = shutil.which(executable)
    if not resolved:
        raise VideoValidatorUnavailable('Video verification is temporarily unavailable')
    try:
        with tempfile.TemporaryDirectory(prefix='intelliwheels-video-') as directory:
            path = Path(directory) / 'upload.bin'
            stream.seek(0)
            with path.open('wb') as output:
                shutil.copyfileobj(stream, output, length=1024 * 1024)
            result = subprocess.run([
                resolved, '-v', 'error', '-max_alloc', '67108864',
                '-protocol_whitelist', 'file', '-format_whitelist', 'mov,avi,matroska,webm',
                '-probesize', '10485760', '-analyzeduration', '10000000', '-max_streams', '32',
                '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,duration:stream_disposition=attached_pic',
                '-of', 'json', str(path),
            ], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=15, check=False, shell=False)
            if result.returncode or len(result.stdout) > 65536:
                raise VideoRejected('Invalid or unsupported video')
            return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise VideoRejected('Video verification timed out; use a shorter or simpler video') from None
    except (OSError, PermissionError):
        raise VideoValidatorUnavailable('Video verification is temporarily unavailable') from None
    except (ValueError, UnicodeError):
        raise VideoRejected('Invalid or unsupported video') from None
    finally:
        stream.seek(0)


def validate_video(stream, config):
    data = probe_video(stream, config['FFPROBE_PATH'])
    try:
        if isinstance(data['format']['duration'], bool):
            raise ValueError()
        duration = float(data['format']['duration'])
        if not math.isfinite(duration) or not 0 < duration <= config['VIDEO_UPLOAD_MAX_SECONDS']:
            raise ValueError()
        streams = data['streams']
        if not isinstance(streams, list) or not 1 <= len(streams) <= 32:
            raise ValueError()
        videos = [item for item in streams if item.get('codec_type') == 'video' and not item.get('disposition', {}).get('attached_pic')]
        if not videos:
            raise ValueError()
        for video in videos:
            width, height = video['width'], video['height']
            if (type(width) is not int or type(height) is not int or min(width, height) <= 0 or
                    max(width, height) > 10000 or width * height > 25000000 or
                    not video.get('codec_name') or video['codec_name'] == 'unknown'):
                raise ValueError()
        # Reject long secondary/audio streams too when stream duration is supplied.
        for item in streams:
            if item.get('duration') not in (None, 'N/A'):
                value = float(item['duration'])
                if not math.isfinite(value) or not 0 <= value <= config['VIDEO_UPLOAD_MAX_SECONDS']:
                    raise ValueError()
    except (KeyError, TypeError, ValueError, AttributeError):
        raise VideoRejected('Video must contain a valid video stream, supported dimensions, and be at most 120 seconds') from None

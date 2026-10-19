"""Bounded media validation before any cloud call or local persistence."""
from PIL import Image, UnidentifiedImageError
from .video_validation import validate_video, VideoRejected, VideoValidatorUnavailable


class UploadRejected(ValueError):
    pass


def validate_upload(file, kind, config):
    stream = file.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    maximum = config['IMAGE_UPLOAD_MAX_BYTES' if kind == 'image' else 'VIDEO_UPLOAD_MAX_BYTES']
    if not size or size > maximum:
        raise UploadRejected(f'File must be nonempty and at most {maximum // (1024 * 1024)}MB')
    extension = file.filename.rsplit('.', 1)[-1].lower()
    if kind == 'image':
        formats = {'png': 'PNG', 'jpg': 'JPEG', 'jpeg': 'JPEG', 'gif': 'GIF', 'webp': 'WEBP'}
        mime = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'GIF': 'image/gif', 'WEBP': 'image/webp'}
        try:
            with Image.open(stream, formats=list(mime)) as image:
                if image.format != formats.get(extension):
                    raise UploadRejected('Image contents do not match the file extension')
                if file.mimetype not in ('', 'application/octet-stream', mime[image.format]):
                    raise UploadRejected('Image content type does not match its contents')
                width, height = image.size
                frames = getattr(image, 'n_frames', 1)
                if (max(width, height) > 10000 or width * height > 25000000 or
                        frames > 100 or width * height * frames > 50000000):
                    raise UploadRejected('Image dimensions or animation are too large')
                image.verify()
            stream.seek(0)
            with Image.open(stream, formats=list(mime)) as image:
                decoded_pixels = 0
                for frame in range(getattr(image, 'n_frames', 1)):
                    image.seek(frame)
                    width, height = image.size
                    decoded_pixels += width * height
                    if max(width, height) > 10000 or width * height > 25000000 or decoded_pixels > 50000000:
                        raise UploadRejected('Image dimensions or animation are too large')
                    image.load()
        except UploadRejected:
            raise
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError, EOFError, Image.DecompressionBombError):
            raise UploadRejected('Invalid or damaged image') from None
        finally:
            stream.seek(0)
    else:
        # Cheap signature screening precedes bounded ffprobe metadata validation.
        header = stream.read(4096)
        stream.seek(0)
        valid = False
        if extension in ('mp4', 'mov'):
            valid = len(header) >= 16 and header[4:8] == b'ftyp' and 16 <= int.from_bytes(header[:4], 'big') <= size
        elif extension == 'avi':
            valid = len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'AVI '
        elif extension in ('webm', 'mkv'):
            doctype = b'webm' if extension == 'webm' else b'matroska'
            valid = header.startswith(b'\x1a\x45\xdf\xa3') and doctype in header
        mimes = {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'avi': 'video/x-msvideo',
                 'webm': 'video/webm', 'mkv': 'video/x-matroska'}
        if not valid or file.mimetype not in ('', 'application/octet-stream', mimes.get(extension)):
            raise UploadRejected('Video container or content type does not match the file extension')
        try:
            validate_video(stream, config)
        except VideoRejected as error:
            raise UploadRejected(str(error)) from None
    return size

"""Validate listing media references; URLs are not proof of asset ownership."""
import json
import re
from urllib.parse import urlsplit

IMAGE_LIMIT = 12
VIDEO_LIMIT = 2
MEDIA_FIELDS = ('image', 'videoUrl', 'galleryImages', 'mediaGallery')


class InvalidListingMedia(ValueError):
    pass


def _url(value, *, optional=False):
    if optional and value in (None, ''):
        return ''
    if not isinstance(value, str) or not value or len(value) > 500:
        raise InvalidListingMedia('Media URLs must be nonempty strings of at most 500 characters')
    # Do not HTML-escape URLs: that corrupts signed/query-string URLs.
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or '\\' in value:
        raise InvalidListingMedia('Media URLs must not contain whitespace or backslashes')
    try:
        parsed = urlsplit(value)
        if value.startswith('/') and not value.startswith('//'):
            return value
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname:
            raise ValueError
        if parsed.username is not None or parsed.password is not None:
            raise ValueError
        _ = parsed.port
    except ValueError:
        raise InvalidListingMedia('Use an HTTP(S) or root-relative media URL without credentials') from None
    return value


def _normalize(field, value):
    if field in ('image', 'videoUrl'):
        return _url(value, optional=True)
    limit = IMAGE_LIMIT if field == 'galleryImages' else IMAGE_LIMIT + VIDEO_LIMIT
    if not isinstance(value, list) or len(value) > limit:
        raise InvalidListingMedia(f'{field} must be an array with at most {limit} entries')
    if field == 'galleryImages':
        return [_url(item) for item in value]
    result = []
    for item in value:
        if not isinstance(item, dict) or item.get('type') not in ('image', 'video'):
            raise InvalidListingMedia('Each mediaGallery entry needs an image or video type and URL')
        if set(item) - {'type', 'url', 'label', 'thumbnail', 'assetId'}:
            raise InvalidListingMedia('Unsupported mediaGallery metadata')
        entry = {'type': item['type'], 'url': _url(item.get('url'))}
        if 'assetId' in item:
            if not isinstance(item['assetId'], str) or not re.fullmatch(r'[0-9a-f]{32}', item['assetId']):
                raise InvalidListingMedia('Invalid media asset ID')
            entry['assetId'] = item['assetId']
        if 'label' in item:
            if not isinstance(item['label'], str) or len(item['label']) > 200:
                raise InvalidListingMedia('Media labels must be strings of at most 200 characters')
            entry['label'] = item['label']
        if 'thumbnail' in item:
            entry['thumbnail'] = _url(item['thumbnail'], optional=True)
        result.append(entry)
    return result


def validate_listing_media(data, existing=None):
    """Return supplied normalized fields; check merged media on partial updates.

    Non-media edits bypass historical media validation. Media edits must bring
    the resulting media into compliance, without rewriting omitted columns.
    """
    supplied = {key: _normalize(key, data[key]) for key in MEDIA_FIELDS if key in data}
    if existing is not None and not supplied:
        return supplied
    state = {'image': '', 'videoUrl': '', 'galleryImages': [], 'mediaGallery': []}
    if existing is not None:
        row = dict(existing)
        for key, column in (('image', 'image_url'), ('videoUrl', 'video_url'),
                            ('galleryImages', 'gallery_images'), ('mediaGallery', 'media_gallery')):
            if key in supplied:
                continue
            value = row.get(column)
            if value is None or value == '':
                continue
            if key in ('galleryImages', 'mediaGallery') and isinstance(value, str):
                try:
                    value = json.loads(value)
                except ValueError:
                    raise InvalidListingMedia('Replace the invalid saved media gallery before editing media') from None
            state[key] = _normalize(key, value)
    state.update(supplied)
    images = set(state['galleryImages'])
    videos = set()
    if state['image']:
        images.add(state['image'])
    if state['videoUrl']:
        videos.add(state['videoUrl'])
    for item in state['mediaGallery']:
        (images if item['type'] == 'image' else videos).add(item['url'])
    if images & videos:
        raise InvalidListingMedia('A media URL cannot be both an image and a video')
    if len(images) > IMAGE_LIMIT or len(videos) > VIDEO_LIMIT:
        raise InvalidListingMedia(f'A listing supports at most {IMAGE_LIMIT} images and {VIDEO_LIMIT} videos')
    return supplied

import type { Car } from './types';

/** Explicit empty primary URLs clear old values on PATCH instead of omitting them. */
export function listingMediaPayload(form: { image: string; galleryImages: string[]; videoUrls: string[]; assetIds?: Record<string, string> }): Pick<Car, 'image' | 'galleryImages' | 'videoUrl' | 'mediaGallery'> {
  const cleanImages = form.galleryImages.map((url) => url.trim()).filter(Boolean);
  const images = [...new Set(cleanImages.length ? cleanImages : form.image.trim() ? [form.image.trim()] : [])];
  const videos = [...new Set(form.videoUrls.map((url) => url.trim()).filter(Boolean))];
  return {
    image: form.image.trim() || images[0] || '',
    galleryImages: images,
    videoUrl: videos[0] || '',
    mediaGallery: [...images.map((url) => ({ type: 'image' as const, url })), ...videos.map((url) => ({ type: 'video' as const, url }))]
      .map((item) => form.assetIds?.[item.url] ? { ...item, assetId: form.assetIds[item.url] } : item),
  };
}

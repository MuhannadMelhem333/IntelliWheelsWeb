interface MediaForm {
  image: string; galleryImages: string[]; videoUrls: string[]; assetIds: Record<string, string>;
}

export function addRecoveredMedia<T extends MediaForm>(form: T, kind: 'image' | 'video', url: string, assetId: string): T {
  if (!url || !assetId) return form;
  return addUploadedMedia(form, kind, url, assetId);
}

export function addUploadedMedia<T extends MediaForm>(form: T, kind: 'image' | 'video', url: string, assetId?: string): T {
  if (!url) return form;
  const current = kind === 'image' ? [...new Set([form.image, ...form.galleryImages].filter(Boolean))] : form.videoUrls;
  if (!current.includes(url) && current.length >= (kind === 'image' ? 12 : 2)) return form;
  return {
    ...form, assetIds: assetId ? { ...form.assetIds, [url]: assetId } : form.assetIds,
    ...(kind === 'image' ? { image: form.image || url, galleryImages: [...new Set([...current, url])] }
      : { videoUrls: [...new Set([...current, url])] }),
  };
}

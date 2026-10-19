import type { UploadResult } from './directUpload';

/** Preserve each successful upload; a sibling failure must not hide stored media. */
export async function uploadListingBatch(files: File[], upload: (file: File) => Promise<UploadResult>) {
  const settled = await Promise.allSettled(files.map((file) => Promise.resolve().then(() => upload(file))));
  const uploads: UploadResult[] = [];
  let failed = 0;
  for (const result of settled) {
    if (result.status === 'fulfilled' && result.value?.success === true && typeof result.value.url === 'string' && result.value.url) uploads.push(result.value);
    else failed++;
  }
  return { uploads, failed };
}

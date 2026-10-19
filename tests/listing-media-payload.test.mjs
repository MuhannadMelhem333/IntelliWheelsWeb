import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/listingMediaPayload.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { listingMediaPayload } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('removing all media explicitly clears primary URLs after JSON serialization', () => {
  assert.deepEqual(JSON.parse(JSON.stringify(listingMediaPayload({ image: '', galleryImages: [], videoUrls: [] }))), {
    image: '', videoUrl: '', galleryImages: [], mediaGallery: [],
  });
});
test('gallery and video aliases preserve order and exact URL query strings', () => {
  const url = 'https://example.test/image?a=1&b=2';
  const form = { image: '', galleryImages: [url, url, ' /second.png ', ''], videoUrls: ['/one.mp4', '/two.mp4', '/one.mp4'] };
  const before = structuredClone(form);
  assert.deepEqual(listingMediaPayload(form), {
    image: url, galleryImages: [url, '/second.png'], videoUrl: '/one.mp4',
    mediaGallery: [{ type: 'image', url }, { type: 'image', url: '/second.png' }, { type: 'video', url: '/one.mp4' }, { type: 'video', url: '/two.mp4' }],
  });
  assert.deepEqual(form, before);
});
test('cover-only listings remain supported without inventing videos', () => {
  const payload = listingMediaPayload({ image: '/cover.png', galleryImages: [], videoUrls: [] });
  assert.equal(payload.image, '/cover.png');
  assert.deepEqual(payload.galleryImages, ['/cover.png']);
  assert.equal(payload.videoUrl, '');
});

test('uploaded IDs survive save and removed media IDs are not serialized', () => {
  const id = 'a'.repeat(32);
  const payload = listingMediaPayload({ image: '/one.png', galleryImages: ['/one.png'], videoUrls: [],
    assetIds: { '/one.png': id, '/removed.png': 'b'.repeat(32) } });
  assert.deepEqual(payload.mediaGallery, [{ type: 'image', url: '/one.png', assetId: id }]);
  assert.deepEqual(listingMediaPayload({ image: '', galleryImages: [], videoUrls: [], assetIds: { '/one.png': id } }).mediaGallery, []);
});

test('legacy URLs and uploaded video IDs coexist without assigning legacy ownership', () => {
  const id = 'c'.repeat(32);
  const payload = listingMediaPayload({ image: '/legacy.png', galleryImages: ['/legacy.png'],
    videoUrls: ['/owned.mp4'], assetIds: { '/owned.mp4': id } });
  assert.deepEqual(payload.mediaGallery, [{ type: 'image', url: '/legacy.png' }, { type: 'video', url: '/owned.mp4', assetId: id }]);
});

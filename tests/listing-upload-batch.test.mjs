import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

async function load(name) {
  const source = await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
}
const { uploadListingBatch } = await load('listingUploadBatch');
const { addUploadedMedia, addRecoveredMedia } = await load('recoveredListingMedia');
const files = () => ['first', 'second', 'third'].map(name => new File([name], name));
const empty = () => ({ image: '', galleryImages: [], videoUrls: [], assetIds: {}, make: 'Toyota' });

test('partial upload failure retains successes and owned IDs in selection order without retry', async () => {
  const calls = [];
  const result = await uploadListingBatch(files(), async file => {
    calls.push(file.name);
    if (file.name === 'second') throw new Error('provider unavailable');
    return { success: true, url: file.name, assetId: file.name + '-id' };
  });
  assert.equal(result.failed, 1);
  assert.deepEqual(calls, ['first', 'second', 'third']);
  const draft = result.uploads.reduce((form, item) => addUploadedMedia(form, 'image', item.url, item.assetId), empty());
  assert.deepEqual(draft.galleryImages, ['first', 'third']);
  assert.deepEqual(draft.assetIds, { first: 'first-id', third: 'third-id' });
  assert.equal(draft.image, 'first'); assert.equal(draft.make, 'Toyota');
});
test('one fast rejection does not finish the batch before other uploads settle', async () => {
  let resolve;
  const pending = new Promise(done => { resolve = done; });
  let settled = false;
  const result = uploadListingBatch(files().slice(0, 2), file => file.name === 'first' ? Promise.reject(new Error('failed')) : pending).then(value => { settled = true; return value; });
  await new Promise(done => setImmediate(done)); assert.equal(settled, false);
  resolve({ success: true, url: 'saved', assetId: 'asset' });
  assert.equal((await result).uploads.length, 1);
});
test('false success, empty URL, malformed response and synchronous errors count as failures', async () => {
  for (const response of [{ success: false, url: 'bad' }, { success: true, url: '' }, undefined]) {
    assert.deepEqual(await uploadListingBatch(files(), async () => response), { uploads: [], failed: 3 });
  }
  assert.equal((await uploadListingBatch(files(), () => { throw new Error('sync'); })).failed, 3);
});
test('legacy uploads without IDs remain supported; recovery still requires an ID', () => {
  const form = empty();
  const result = addUploadedMedia(form, 'video', 'legacy');
  assert.deepEqual(result.videoUrls, ['legacy']); assert.deepEqual(result.assetIds, {});
  assert.equal(addRecoveredMedia(form, 'image', 'url', ''), form);
});
test('primary image is counted, gallery never exceeds capacity, existing IDs are retained', () => {
  const form = { ...empty(), image: 'primary', galleryImages: Array.from({ length: 11 }, (_, i) => `image-${i}`), assetIds: { primary: 'old-id' } };
  assert.equal(addUploadedMedia(form, 'image', 'extra', 'new-id'), form);
  const duplicate = addUploadedMedia(form, 'image', 'primary');
  assert.equal(duplicate.galleryImages.length, 12);
  assert.equal(duplicate.assetIds.primary, 'old-id');
});

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import ts from 'typescript';

const url = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
async function compile(path) {
  return ts.transpileModule(await readFile(new URL(`../src/${path}`, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX }, fileName: path,
  }).outputText;
}
const mockUrl = url(`export const state={revision:0}; export const getCookieSessionRevision=()=>state.revision;
export const fetchRecoverableUploads=(...args)=>state.load(...args); export const completeRecoveredUpload=(...args)=>state.complete(...args);`);
const { state } = await import(mockUrl);
let source = await compile('components/listings/UploadRecovery.tsx');
source = source.replaceAll("'@/lib/api'", JSON.stringify(mockUrl)).replaceAll("'@/lib/cookieSession'", JSON.stringify(mockUrl))
  .replaceAll("'react'", JSON.stringify(import.meta.resolve('react'))).replaceAll('"react/jsx-runtime"', JSON.stringify(import.meta.resolve('react/jsx-runtime')))
  .replaceAll("'next/image'", JSON.stringify(url('export default function Image(){return null}')));
const { UploadRecovery } = await import(url(source));
const { addRecoveredMedia } = await import(url(await compile('lib/recoveredListingMedia.ts')));
const entry = { intentId: 'fixture', kind: 'image', state: 'pending', signatureExpired: true, quotaHeld: true, assetId: null };

test('recovery media merge preserves fields, deduplicates and enforces limits', () => {
  const initial = { image: '', galleryImages: [], videoUrls: [], assetIds: {}, make: 'Toyota' };
  const added = addRecoveredMedia(initial, 'image', 'https://fixture/image', 'asset');
  assert.equal(added.make, 'Toyota'); assert.equal(added.image, 'https://fixture/image');
  assert.equal(added.assetIds[added.image], 'asset'); assert.deepEqual(initial.galleryImages, []);
  assert.equal(addRecoveredMedia(added, 'image', added.image, 'asset').galleryImages.length, 1);
  const full = { ...initial, image: 'primary', galleryImages: Array.from({ length: 11 }, (_, i) => `image-${i}`), videoUrls: ['one', 'two'] };
  assert.equal(addRecoveredMedia(full, 'image', 'extra', 'asset'), full);
  assert.equal(addRecoveredMedia(full, 'video', 'extra', 'asset'), full);
  assert.equal(addRecoveredMedia(initial, 'image', 'url', ''), initial);
});

test('mounted recovery interactions', async t => {
  async function mount(t, overrides = {}) {
    const dom = new JSDOM('<div id="root"></div>');
    const descriptors = new Map();
    for (const [name, value] of Object.entries({ window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true })) {
      descriptors.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
      Object.defineProperty(globalThis, name, { configurable: true, writable: true, value });
    }
    state.revision = 0;
    const adds = []; const calls = [];
    state.load = async (...args) => { calls.push(args); return { uploads: [entry], nextCursor: 'next' }; };
    state.complete = async () => ({ success: true, url: 'https://res.cloudinary.com/fixture/image', assetId: 'asset' });
    const root = createRoot(document.getElementById('root'));
    await act(async () => root.render(createElement(UploadRecovery, { token: 'fixture-token', language: 'en', dark: true, disabled: false, imageCount: 0, videoCount: 0, onAdd: (...args) => adds.push(args), ...overrides })));
    t.after(async () => { await act(async () => root.unmount()); dom.window.close(); for (const [name, descriptor] of descriptors) { if (descriptor) Object.defineProperty(globalThis, name, descriptor); else delete globalThis[name]; } });
    const button = text => [...document.querySelectorAll('button')].find(node => node.textContent === text);
    const click = async text => { assert.ok(button(text), text); await act(async () => button(text).click()); };
    return { root, calls, adds, button, click };
  }
  await t.test('no mount request, paginated discovery, preview before explicit add', async t => {
    const h = await mount(t);
    assert.equal(h.calls.length, 0);
    await h.click('Recover previous uploads'); assert.equal(h.adds.length, 0);
    await h.click('Next uploads'); assert.deepEqual(h.calls[1], ['fixture-token', 'next']);
    await h.click('Verify and preview'); assert.equal(h.adds.length, 0);
    await h.click('Add to listing'); assert.equal(h.adds.length, 1);
    assert.deepEqual(h.adds[0], ['image', 'https://res.cloudinary.com/fixture/image', 'asset']);
  });
  await t.test('capacity prevents adding and failures expose retry message', async t => {
    const h = await mount(t, { imageCount: 12 });
    await h.click('Recover previous uploads'); await h.click('Verify and preview');
    assert.equal(h.button('Add to listing').disabled, true); assert.equal(h.adds.length, 0);
    state.load = async () => { throw new Error('private failure'); };
    await h.click('Recover previous uploads');
    assert.match(document.body.textContent, /Recovery is unavailable/);
    assert.doesNotMatch(document.body.textContent, /private failure/);
  });
  await t.test('session change discards delayed completion', async t => {
    const h = await mount(t); await h.click('Recover previous uploads');
    let resolve; state.complete = () => new Promise(done => { resolve = done; });
    await h.click('Verify and preview'); state.revision++;
    await act(async () => resolve({ success: true, url: 'https://fixture', assetId: 'asset' }));
    assert.equal(h.button('Add to listing'), undefined); assert.equal(h.adds.length, 0);
  });
  await t.test('Arabic recovery uses RTL and translated controls', async t => {
    const h = await mount(t, { language: 'ar' });
    assert.equal(document.querySelector('section').dir, 'rtl');
    await h.click('استعادة ملفات مرفوعة سابقاً'); await h.click('تحقق ومعاينة');
    assert.ok(h.button('إضافة إلى الإعلان'));
  });
});

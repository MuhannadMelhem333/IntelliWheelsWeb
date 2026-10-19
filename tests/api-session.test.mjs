import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

async function compiled(name) {
  const source = await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), 'utf8');
  return ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
}
const moduleUrl = (code) => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
const configUrl = moduleUrl(await compiled('config'));
const sessionUrl = moduleUrl(await compiled('sessionEvents'));
const uploadUrl = moduleUrl(await compiled('uploadUrl'));
const cookieUrl = moduleUrl((await compiled('cookieSession')).replace(/(['"])\.\/config\1/g, JSON.stringify(configUrl)));
const apiSource = (await compiled('api'))
  .replace(/(['"])\.\/directUpload\1/g, JSON.stringify(moduleUrl(await compiled('directUpload'))))
  .replace(/(['"])\.\/config\1/g, JSON.stringify(configUrl))
  .replace(/(['"])\.\/sessionEvents\1/g, JSON.stringify(sessionUrl))
  .replace(/(['"])\.\/uploadUrl\1/g, JSON.stringify(uploadUrl))
  .replace(/(['"])\.\/cookieSession\1/g, JSON.stringify(cookieUrl));
const api = await import(moduleUrl(apiSource));
const { STORAGE_KEYS } = await import(configUrl);
const { subscribeToSessionRejection } = await import(sessionUrl);

test('real API client session and cache contracts (mocked network)', async (t) => {
  const windowDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'window');
  const storageDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage');
  const storage = new Map();
  const rejected = [];
  Object.defineProperty(globalThis, 'window', { configurable: true, value: new EventTarget() });
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: {
    getItem: (key) => storage.get(key) ?? null,
  } });
  const unsubscribe = subscribeToSessionRejection((token) => rejected.push(token));
  t.after(() => {
    unsubscribe();
    if (windowDescriptor) Object.defineProperty(globalThis, 'window', windowDescriptor);
    else delete globalThis.window;
    if (storageDescriptor) Object.defineProperty(globalThis, 'localStorage', storageDescriptor);
    else delete globalThis.localStorage;
  });
  t.beforeEach(() => { storage.clear(); rejected.length = 0; });

  await t.test('anonymous reference data retains its explicit public cache policy', async (t) => {
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      assert.equal(options.cache, 'force-cache');
      assert.equal(options.headers.has('Authorization'), false);
      return Response.json({ success: true, makes: ['Toyota'] });
    });
    assert.deepEqual((await api.fetchMakes()).makes, ['Toyota']);
    assert.deepEqual(rejected, []);
  });

  await t.test('stored token forces no-store even for public reference calls', async (t) => {
    storage.set(STORAGE_KEYS.token, 'fixture-current');
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      assert.equal(options.cache, 'no-store');
      assert.equal(options.headers.get('Authorization'), 'Bearer fixture-current');
      return Response.json({ success: true, makes: [] });
    });
    await api.fetchMakes();
  });

  await t.test('explicit token wins over storage and identifies the rejected request', async (t) => {
    storage.set(STORAGE_KEYS.token, 'fixture-new');
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      assert.equal(options.headers.get('Authorization'), 'Bearer fixture-old');
      return Response.json({ error: 'Expired' }, { status: 401 });
    });
    await assert.rejects(api.fetchCarById(1, 'fixture-old'), /Expired/);
    assert.deepEqual(rejected, ['fixture-old']);
  });

  await t.test('401 reports the resolved storage token when caller omitted it', async (t) => {
    storage.set(STORAGE_KEYS.token, 'fixture-stored');
    t.mock.method(globalThis, 'fetch', async () => Response.json({ error: 'Expired' }, { status: 401 }));
    await assert.rejects(api.fetchMakes(), /Expired/);
    assert.deepEqual(rejected, ['fixture-stored']);
  });

  await t.test('403 does not invalidate a valid session', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => Response.json({ error: 'Forbidden' }, { status: 403 }));
    await assert.rejects(api.fetchCarById(1, 'fixture-current'), /Forbidden/);
    assert.deepEqual(rejected, []);
  });

  await t.test('anonymous 401 does not emit session rejection', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('', { status: 401, statusText: 'Unauthorized' }));
    await assert.rejects(api.fetchMakes(), /Unauthorized/);
    assert.deepEqual(rejected, []);
  });

  await t.test('authenticated non-JSON 401 still emits session rejection', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('Unauthorized', { status: 401, statusText: 'Unauthorized' }));
    await assert.rejects(api.fetchCarById(1, 'fixture-current'), /Unauthorized/);
    assert.deepEqual(rejected, ['fixture-current']);
  });

  await t.test('network failures do not masquerade as session rejection', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Network unavailable'); });
    await assert.rejects(api.fetchCarById(1, 'fixture-current'), /Network unavailable/);
    assert.deepEqual(rejected, []);
  });

  await t.test('abort signal reaches fetch and cancellation remains an AbortError', async (t) => {
    const controller = new AbortController();
    controller.abort();
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      assert.equal(options.signal, controller.signal);
      throw new DOMException('Cancelled', 'AbortError');
    });
    await assert.rejects(api.verifySession('fixture-current', controller.signal), { name: 'AbortError' });
    assert.deepEqual(rejected, []);
  });

  await t.test('image and video API uploads negotiate proxy mode before existing multipart upload', async (t) => {
    const calls = [];
    t.mock.method(globalThis, 'fetch', async (url, options) => {
      calls.push(url);
      assert.equal(options.headers.get('Authorization'), 'Bearer fixture-current');
      if (url.endsWith('/uploads/prepare')) return Response.json({ mode: 'proxy' });
      assert.ok(options.body instanceof FormData);
      return Response.json({ success: true, url: '/api/uploads/fixture.png', assetId: 'fixture' });
    });
    for (const upload of [api.uploadListingImage, api.uploadListingVideo]) {
      const result = await upload(new File(['fixture'], 'fixture.png'), 'fixture-current');
      assert.equal(result.assetId, 'fixture');
      assert.match(result.url, /^http/);
    }
    assert.ok(calls[0].endsWith('/uploads/prepare'));
    assert.ok(calls[1].endsWith('/uploads/images'));
    assert.ok(calls[2].endsWith('/uploads/prepare'));
    assert.ok(calls[3].endsWith('/uploads/videos'));
  });

  await t.test('image API integrates direct preparation, unauthenticated provider POST, and authenticated completion', async (t) => {
    const calls = [];
    t.mock.method(globalThis, 'fetch', async (url, options) => {
      calls.push(url);
      if (url.startsWith('https://api.cloudinary.com/')) {
        assert.equal(options.headers, undefined);
        assert.equal(options.credentials, 'omit');
        return new Response('ignored');
      }
      assert.equal(options.headers.get('Authorization'), 'Bearer fixture-current');
      if (url.endsWith('/uploads/prepare')) return Response.json({ mode: 'direct', intentId: 'fixture', uploadUrl: 'https://api.cloudinary.com/v1_1/fixture/image/upload', parameters: { signature: 'fixture' } });
      assert.ok(url.endsWith('/uploads/complete/fixture'));
      return Response.json({ success: true, url: 'https://res.cloudinary.com/fixture/verified.png', assetId: 'fixture' });
    });
    assert.equal((await api.uploadListingImage(new File(['fixture'], 'fixture.png'), 'fixture-current')).assetId, 'fixture');
    assert.equal(calls.length, 3);
  });

  await t.test('recovery API uses private reads and explicit authenticated completion', async (t) => {
    const calls = [];
    t.mock.method(globalThis, 'fetch', async (url, options) => {
      calls.push({ url, options });
      assert.equal(options.headers.get('Authorization'), 'Bearer fixture-current');
      assert.equal(options.cache, 'no-store');
      return Response.json(url.includes('/recovery') ? { success: true, uploads: [], nextCursor: null } : { success: true, url: 'https://fixture', assetId: 'asset' });
    });
    await api.fetchRecoverableUploads('fixture-current', 'cursor/value');
    await api.completeRecoveredUpload('intent/value', 'fixture-current');
    assert.ok(calls[0].url.endsWith('/uploads/recovery?after=cursor%2Fvalue'));
    assert.ok(calls[1].url.endsWith('/uploads/complete/intent%2Fvalue'));
    assert.equal(calls[1].options.method, 'POST');
    assert.equal(calls.length, 2);
  });
});

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const url = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
async function compile(name) {
  return ts.transpileModule(await readFile(new URL(`../src/lib/${name}.ts`, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 },
  }).outputText;
}
const config = url((await compile('config')).replace('COOKIE_AUTH_ENABLED = false', 'COOKIE_AUTH_ENABLED = true'));
const cookies = url((await compile('cookieSession')).replace(/(['"])\.\/config\1/g, JSON.stringify(config)));
const events = url(await compile('sessionEvents'));
const uploads = url(await compile('uploadUrl'));
let source = await compile('api');
for (const [name, value] of Object.entries({ config, cookieSession: cookies, sessionEvents: events, uploadUrl: uploads, directUpload: url(await compile('directUpload')) })) {
  source = source.replaceAll(`'./${name}'`, JSON.stringify(value));
}
const api = await import(url(source));
const state = await import(cookies);
const sessionEvents = await import(events);

function installGlobal(t, name, value) {
  const original = Object.getOwnPropertyDescriptor(globalThis, name);
  Object.defineProperty(globalThis, name, { configurable: true, value });
  t.after(() => {
    if (original) Object.defineProperty(globalThis, name, original);
    else delete globalThis[name];
  });
}

test('cookie API transport with mocked network', async t => {
  t.beforeEach(() => state.setCookieSessionVersion(null));

  await t.test('public reads include cookies and disable shared caching', async t => {
    t.mock.method(globalThis, 'fetch', async (_url, options) => {
      assert.equal(options.credentials, 'include');
      assert.equal(options.cache, 'no-store');
      assert.equal(options.headers.has('Authorization'), false);
      return Response.json({ success: true, makes: [] });
    });
    await api.fetchMakes();
  });

  await t.test('startup verification works without a JS bearer token', async t => {
    t.mock.method(globalThis, 'fetch', async endpoint => {
      assert.ok(endpoint.endsWith('/auth/verify'));
      return Response.json({ success: true, authenticated: true, sessionVersion: 'version-one' });
    });
    assert.equal((await api.verifySession(null)).sessionVersion, 'version-one');
  });

  await t.test('mutations bootstrap CSRF and send only a session version', async t => {
    state.setCookieSessionVersion('version-one');
    const calls = [];
    t.mock.method(globalThis, 'fetch', async (endpoint, options) => {
      calls.push(endpoint);
      assert.equal(options.credentials, 'include');
      if (endpoint.endsWith('/auth/csrf')) return Response.json({ csrfToken: 'fixture-csrf' });
      assert.equal(options.headers.get('X-CSRF-Token'), 'fixture-csrf');
      assert.equal(options.headers.get('X-Session-Version'), 'version-one');
      assert.equal(options.headers.has('Authorization'), false);
      return Response.json({ success: true });
    });
    await api.addFavorite(1, 'version-one');
    assert.equal(calls.length, 2);
  });

  await t.test('failed CSRF bootstrap never sends the mutation', async t => {
    let calls = 0;
    t.mock.method(globalThis, 'fetch', async endpoint => {
      calls += 1;
      assert.ok(endpoint.endsWith('/auth/csrf'));
      return Response.json({ error: 'Forbidden' }, { status: 403 });
    });
    await assert.rejects(api.loginUser('fixture', 'fixture'), /prepare secure request/);
    assert.equal(calls, 1);
  });

  await t.test('concurrent mutations share one bootstrap', async t => {
    let bootstrapCount = 0;
    t.mock.method(globalThis, 'fetch', async endpoint => {
      if (endpoint.endsWith('/auth/csrf')) {
        bootstrapCount += 1;
        return Response.json({ csrfToken: 'fixture-csrf' });
      }
      return Response.json({ success: true });
    });
    await Promise.all([api.addFavorite(1, null), api.addFavorite(2, null)]);
    assert.equal(bootstrapCount, 1);
  });

  await t.test('session change during bootstrap prevents a stale mutation', async t => {
    state.setCookieSessionVersion('old-version');
    t.mock.method(globalThis, 'fetch', async endpoint => {
      assert.ok(endpoint.endsWith('/auth/csrf'));
      state.setCookieSessionVersion('new-version');
      return Response.json({ csrfToken: 'fixture-csrf' });
    });
    await assert.rejects(api.addFavorite(1, 'old-version'), /Session changed/);
  });

  await t.test('logout body contains no bearer credential', async t => {
    t.mock.method(globalThis, 'fetch', async (endpoint, options) => {
      if (endpoint.endsWith('/auth/csrf')) return Response.json({ csrfToken: 'fixture-csrf' });
      assert.equal(options.body, '{}');
      return Response.json({ success: true });
    });
    await api.logoutUser(null);
  });

  await t.test('malformed CSRF responses fail closed and can recover', async t => {
    const invalidResponses = [null, {}, { csrfToken: '' }, { csrfToken: 42 }];
    let mutations = 0;
    t.mock.method(globalThis, 'fetch', async endpoint => {
      if (endpoint.endsWith('/auth/csrf')) {
        return Response.json(invalidResponses.length ? invalidResponses.shift() : { csrfToken: 'fixture-csrf' });
      }
      mutations += 1;
      return Response.json({ success: true });
    });
    for (let i = 0; i < 4; i += 1) {
      await assert.rejects(api.addFavorite(1, null), /Invalid security response/);
    }
    assert.equal(mutations, 0);
    await api.addFavorite(1, null);
    assert.equal(mutations, 1);
  });

  await t.test('failed shared bootstrap rejects all callers and next attempt recovers', async t => {
    let bootstraps = 0;
    let mutations = 0;
    t.mock.method(globalThis, 'fetch', async endpoint => {
      if (endpoint.endsWith('/auth/csrf')) {
        bootstraps += 1;
        if (bootstraps === 1) throw new TypeError('Fixture offline');
        return Response.json({ csrfToken: 'fixture-csrf' });
      }
      mutations += 1;
      return Response.json({ success: true });
    });
    const results = await Promise.allSettled([api.addFavorite(1, null), api.addFavorite(2, null)]);
    assert.ok(results.every(result => result.status === 'rejected'));
    assert.equal(bootstraps, 1);
    assert.equal(mutations, 0);
    await api.addFavorite(1, null);
    assert.equal(bootstraps, 2);
    assert.equal(mutations, 1);
  });

  await t.test('already aborted request never starts CSRF bootstrap', async t => {
    const controller = new AbortController();
    controller.abort();
    const fetchMock = t.mock.method(globalThis, 'fetch', async () => {
      throw new Error('Unexpected network request');
    });
    await assert.rejects(state.prepareCookieHeaders(new Headers(), 'POST', null, controller.signal), { name: 'AbortError' });
    assert.equal(fetchMock.mock.callCount(), 0);
  });

  await t.test('one cancelled caller does not cancel another shared-bootstrap caller', async t => {
    const controller = new AbortController();
    let release;
    t.mock.method(globalThis, 'fetch', () => new Promise(resolve => { release = resolve; }));
    const cancelledHeaders = new Headers();
    const activeHeaders = new Headers();
    const cancelled = state.prepareCookieHeaders(cancelledHeaders, 'POST', null, controller.signal);
    const active = state.prepareCookieHeaders(activeHeaders, 'POST', null);
    const rejection = assert.rejects(cancelled, { name: 'AbortError' });
    controller.abort();
    release(Response.json({ csrfToken: 'fixture-csrf' }));
    await Promise.all([rejection, active]);
    assert.equal(cancelledHeaders.has('X-CSRF-Token'), false);
    assert.equal(activeHeaders.get('X-CSRF-Token'), 'fixture-csrf');
  });

  await t.test('returning to the same session identity still invalidates pending work', async t => {
    state.setCookieSessionVersion('version-one');
    t.mock.method(globalThis, 'fetch', async endpoint => {
      assert.ok(endpoint.endsWith('/auth/csrf'));
      state.setCookieSessionVersion(null);
      state.setCookieSessionVersion('version-one');
      return Response.json({ csrfToken: 'fixture-csrf' });
    });
    await assert.rejects(api.addFavorite(1, 'version-one'), /Session changed/);
  });

  await t.test('server rejection does not automatically retry a mutation', async t => {
    let mutations = 0;
    t.mock.method(globalThis, 'fetch', async endpoint => {
      if (endpoint.endsWith('/auth/csrf')) return Response.json({ csrfToken: 'fixture-csrf' });
      mutations += 1;
      return Response.json({ error: 'Fixture rejected' }, { status: 403 });
    });
    await assert.rejects(api.addFavorite(1, null), /Fixture rejected/);
    assert.equal(mutations, 1);
  });

  await t.test('verification omits stale version so it can discover the current cookie', async t => {
    state.setCookieSessionVersion('old-version');
    t.mock.method(globalThis, 'fetch', async (endpoint, options) => {
      assert.ok(endpoint.endsWith('/auth/verify'));
      assert.equal(options.headers.has('X-Session-Version'), false);
      return Response.json({ success: true, authenticated: true, sessionVersion: 'new-version' });
    });
    assert.equal((await api.verifySession('old-version')).sessionVersion, 'new-version');
    // Only the provider may adopt the verified identity after its stale-response check.
    assert.equal(state.getCookieSessionVersion(), 'old-version');
  });

  await t.test('cookie requests never consult browser bearer storage', async t => {
    installGlobal(t, 'window', new EventTarget());
    installGlobal(t, 'localStorage', {
      getItem() { assert.fail('Cookie transport must not read localStorage'); },
    });
    t.mock.method(globalThis, 'fetch', async (_endpoint, options) => {
      assert.equal(options.headers.has('Authorization'), false);
      return Response.json({ success: true, cars: [] });
    });
    await api.fetchFavorites(null);
  });

  await t.test('bad login credentials do not reject an existing session but protected 401 does', async t => {
    let unsubscribe = () => {};
    t.after(() => unsubscribe());
    installGlobal(t, 'window', new EventTarget());
    state.setCookieSessionVersion('version-one');
    const rejected = [];
    unsubscribe = sessionEvents.subscribeToSessionRejection(version => rejected.push(version));
    t.mock.method(globalThis, 'fetch', async endpoint => {
      if (endpoint.endsWith('/auth/csrf')) return Response.json({ csrfToken: 'fixture-csrf' });
      return Response.json({ error: 'Fixture unauthorized' }, { status: 401 });
    });
    await assert.rejects(api.loginUser('fixture', 'fixture'), /Fixture unauthorized/);
    assert.deepEqual(rejected, []);
    await assert.rejects(api.fetchFavorites('version-one'), /Fixture unauthorized/);
    assert.deepEqual(rejected, ['version-one']);
  });

  await t.test('legacy thread GET is CSRF-protected because it marks messages read', async t => {
    let bootstrapped = false;
    t.mock.method(globalThis, 'fetch', async (endpoint, options) => {
      if (endpoint.endsWith('/auth/csrf')) {
        bootstrapped = true;
        return Response.json({ csrfToken: 'fixture-csrf' });
      }
      assert.equal(options.method, 'GET');
      assert.equal(options.headers.get('X-CSRF-Token'), 'fixture-csrf');
      return Response.json({ success: true, messages: [] });
    });
    await api.fetchMessages(1, null);
    assert.equal(bootstrapped, true);
  });
});

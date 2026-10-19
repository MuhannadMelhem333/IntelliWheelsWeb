import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { JSDOM } from 'jsdom';
import { act, createElement, StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import ts from 'typescript';

// Mount the real provider and API client. Only the network and browser DOM are
// simulated; the checked-in rollout gate remains disabled.
const url = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
async function compile(path) {
  return ts.transpileModule(await readFile(new URL(`../src/${path}`, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX },
    fileName: path,
  }).outputText;
}
const config = url((await compile('lib/config.ts')).replace('COOKIE_AUTH_ENABLED = false', 'COOKIE_AUTH_ENABLED = true'));
const modules = {
  config,
  cookieSession: url((await compile('lib/cookieSession.ts')).replaceAll("'./config'", JSON.stringify(config))),
  sessionEvents: url(await compile('lib/sessionEvents.ts')),
  uploadUrl: url(await compile('lib/uploadUrl.ts')),
  directUpload: url(await compile('lib/directUpload.ts')),
  logoutSession: url(await compile('lib/logoutSession.ts')),
};
let api = await compile('lib/api.ts');
for (const [name, value] of Object.entries(modules)) api = api.replaceAll(`'./${name}'`, JSON.stringify(value));
modules.api = url(api);
let provider = await compile('context/AuthContext.tsx');
for (const [name, value] of Object.entries(modules)) provider = provider.replaceAll(`'@/lib/${name}'`, JSON.stringify(value));
provider = provider.replaceAll("'react'", JSON.stringify(import.meta.resolve('react')))
  .replaceAll('"react/jsx-runtime"', JSON.stringify(import.meta.resolve('react/jsx-runtime')));
const { AuthProvider, useAuth } = await import(url(provider));
const cookies = await import(modules.cookieSession);
const { STORAGE_KEYS } = await import(config);
const user = { id: 1, username: 'fixture-one', email: 'one@example.test' };
const verified = (version = 'version-one', profile = user) => ({ success: true, authenticated: true, sessionVersion: version, user: profile });
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

async function harness(t, respond, { strict = false, stored = {} } = {}) {
  const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost:3000/account' });
  const originals = new Map();
  for (const [name, value] of Object.entries({ window: dom.window, document: dom.window.document,
    localStorage: dom.window.localStorage, CustomEvent: dom.window.CustomEvent, IS_REACT_ACT_ENVIRONMENT: true })) {
    originals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
    Object.defineProperty(globalThis, name, { configurable: true, writable: true, value });
  }
  cookies.setCookieSessionVersion(null);
  for (const [key, value] of Object.entries(stored)) localStorage.setItem(key, value);
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (endpoint, options) => {
    const path = new URL(endpoint).pathname;
    calls.push(path);
    if (path === '/api/auth/csrf') return Response.json({ csrfToken: 'fixture-csrf' });
    return respond(path, options);
  });
  let current;
  function Probe() {
    current = useAuth();
    return createElement('output', null, current.sessionValidated ? current.user?.username : 'guest');
  }
  const root = createRoot(document.getElementById('root'));
  t.after(async () => {
    await act(async () => root.unmount());
    dom.window.close();
    for (const [name, descriptor] of originals) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor);
      else delete globalThis[name];
    }
  });
  await act(async () => root.render(createElement(strict ? StrictMode : AuthProvider, null,
    strict ? createElement(AuthProvider, null, createElement(Probe)) : createElement(Probe))));
  return { get auth() { return current; }, calls, dom };
}

test('mounted cookie AuthProvider lifecycle', async t => {
  await t.test('startup restores verified identity and removes credentials but retains preferences', async t => {
    const h = await harness(t, async path => {
      assert.equal(path, '/api/auth/verify');
      return Response.json(verified());
    }, { stored: { [STORAGE_KEYS.token]: 'fixture-old', [STORAGE_KEYS.user]: '{}', token: 'fixture-old',
      authToken: 'fixture-old', [STORAGE_KEYS.currency]: 'USD' } });
    assert.equal(h.auth.user.username, user.username);
    assert.equal(h.auth.sessionValidated, true);
    assert.equal(h.auth.loading, false);
    assert.equal(h.auth.currency, 'USD');
    for (const key of [STORAGE_KEYS.token, STORAGE_KEYS.user, 'token', 'authToken']) assert.equal(localStorage.getItem(key), null);
    assert.equal(h.calls.length, 1);
  });

  await t.test('guest startup and StrictMode settle without repeated verification', async t => {
    const h = await harness(t, async () => Response.json({ success: true, authenticated: false }), { strict: true });
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.loading, false);
    assert.equal(h.auth.sessionValidated, false);
    assert.ok(h.calls.length <= 2);
  });

  await t.test('login and successful logout update mounted UI without storing credentials', async t => {
    const h = await harness(t, async path => Response.json(path === '/api/auth/login'
      ? verified() : { success: true, authenticated: false }));
    await act(async () => { assert.equal(await h.auth.login('fixture', 'fixture'), true); });
    assert.equal(h.auth.sessionValidated, true);
    assert.equal(localStorage.getItem(STORAGE_KEYS.token), null);
    await act(async () => h.auth.logout());
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.sessionValidated, false);
    assert.ok(h.calls.includes('/api/auth/logout'));
  });

  await t.test('failed logout keeps verified user and displays retry error', async t => {
    const h = await harness(t, async path => path === '/api/auth/logout'
      ? Response.json({ error: 'Fixture failure' }, { status: 500 }) : Response.json(verified()));
    await act(async () => h.auth.logout());
    assert.equal(h.auth.sessionValidated, true);
    assert.equal(h.auth.user.username, user.username);
    assert.match(h.auth.error, /Sign out failed/);
  });

  await t.test('focus removes private UI until server verification resolves', async t => {
    const pending = deferred();
    let checks = 0;
    const h = await harness(t, async () => ++checks === 1 ? Response.json(verified()) : pending.promise);
    await act(async () => window.dispatchEvent(new h.dom.window.Event('focus')));
    assert.equal(h.auth.sessionValidated, false);
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.loading, true);
    await act(async () => pending.resolve(Response.json(verified('version-two', { ...user, username: 'fixture-two' }))));
    assert.equal(h.auth.user.username, 'fixture-two');
    assert.equal(h.auth.loading, false);
    assert.equal(checks, 2);
  });

  await t.test('cross-tab notification rechecks and ignores old in-flight verification', async t => {
    const old = deferred();
    let checks = 0;
    const h = await harness(t, async () => ++checks === 1 ? old.promise : Response.json(verified('version-two')));
    await act(async () => window.dispatchEvent(new h.dom.window.StorageEvent('storage', { key: cookies.cookieSessionChangeKey })));
    await act(async () => old.resolve(Response.json(verified('old-version', { ...user, username: 'stale-user' }))));
    assert.equal(h.auth.token, 'version-two');
    assert.equal(h.auth.user.username, user.username);
    assert.equal(h.auth.loading, false);
    assert.equal(checks, 2);
  });

  await t.test('verification network failure never enables a cached user', async t => {
    t.mock.method(console, 'error', () => {});
    const h = await harness(t, async () => { throw new TypeError('Fixture offline'); },
      { stored: { [STORAGE_KEYS.user]: JSON.stringify(user) } });
    assert.equal(h.auth.loading, false);
    assert.equal(h.auth.sessionValidated, false);
    assert.equal(h.auth.user, null);
    assert.equal(h.calls.length, 1);
  });

  for (const fails of [false, true]) {
    await t.test(`delayed logout ${fails ? 'failure' : 'success'} leaves newer login intact`, async t => {
      const oldLogout = deferred();
      const h = await harness(t, async path => {
        if (path === '/api/auth/logout') return oldLogout.promise;
        if (path === '/api/auth/login') return Response.json(verified('version-two', { ...user, username: 'fixture-two' }));
        return Response.json(verified());
      });
      let loggingOut;
      await act(async () => { loggingOut = h.auth.logout(); });
      await act(async () => h.auth.login('fixture-two', 'fixture'));
      await act(async () => {
        oldLogout.resolve(fails ? Response.json({ error: 'Fixture failure' }, { status: 500 }) : Response.json({ success: true }));
        await loggingOut;
      });
      assert.equal(h.auth.user.username, 'fixture-two');
      assert.equal(h.auth.sessionValidated, true);
      assert.equal(h.auth.error, null);
    });
  }

  await t.test('logout during pending startup reaches server without an in-memory identity', async t => {
    const startup = deferred();
    const h = await harness(t, async path => path === '/api/auth/verify'
      ? startup.promise : Response.json({ success: true }));
    assert.equal(h.auth.token, null);
    await act(async () => h.auth.logout());
    assert.ok(h.calls.includes('/api/auth/logout'));
    await act(async () => startup.resolve(Response.json(verified())));
    assert.equal(h.auth.sessionValidated, false);
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.loading, false);
  });

  await t.test('password rotation adopts the new session and updated profile', async t => {
    const rotatedUser = { ...user, username: 'updated-fixture' };
    const h = await harness(t, async (_path, options) => options.method === 'PATCH'
      ? Response.json({ success: true, sessionVersion: 'rotated-version', user: rotatedUser })
      : Response.json(verified()));
    await act(async () => {
      assert.equal(await h.auth.updateMyProfile({ current_password: 'fixture-old', password: 'fixture-new' }), true);
    });
    assert.equal(h.auth.token, 'rotated-version');
    assert.equal(cookies.getCookieSessionVersion(), 'rotated-version');
    assert.equal(h.auth.user.username, rotatedUser.username);
    assert.equal(h.auth.sessionValidated, true);
    assert.equal(localStorage.getItem(STORAGE_KEYS.token), null);
    assert.ok(localStorage.getItem(cookies.cookieSessionChangeKey));
  });

  await t.test('password reset clears current UI and broadcasts the session change', async t => {
    let reset = false;
    const h = await harness(t, async path => {
      if (path === '/api/auth/verify') return Response.json(reset ? { success: true, authenticated: false } : verified());
      assert.equal(path, '/api/auth/reset-password');
      reset = true;
      return Response.json({ success: true });
    });
    await act(async () => {
      assert.equal((await h.auth.resetUserPassword('fixture-reset', 'fixture-password')).success, true);
    });
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.token, null);
    assert.equal(h.auth.sessionValidated, false);
    assert.ok(localStorage.getItem(cookies.cookieSessionChangeKey));
  });

  await t.test('verification timeout aborts fetch and settles as an unverified guest', async t => {
    t.mock.method(console, 'error', () => {});
    t.mock.timers.enable({ apis: ['setTimeout'] });
    let aborted = false;
    const h = await harness(t, async (_path, options) => new Promise((_resolve, reject) => {
      options.signal.addEventListener('abort', () => {
        aborted = true;
        reject(new DOMException('Fixture aborted', 'AbortError'));
      }, { once: true });
    }));
    assert.equal(h.auth.loading, true);
    await act(async () => t.mock.timers.tick(15000));
    assert.equal(aborted, true);
    assert.equal(h.auth.loading, false);
    assert.equal(h.auth.user, null);
    assert.equal(h.auth.sessionValidated, false);
  });
});

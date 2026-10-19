import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/uploadUrl.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { resolveUploadUrl } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('local image and video paths resolve against backend origin', () => {
  for (const path of ['/api/uploads/images/car.webp', '/api/uploads/videos/car.mp4']) {
    assert.equal(resolveUploadUrl(path, 'http://localhost:5000/api'), `http://localhost:5000${path}`);
  }
});
test('hosted backend media uses its configured origin', () => {
  assert.equal(resolveUploadUrl('/api/uploads/images/car.jpg', 'https://api.example.test/api'), 'https://api.example.test/api/uploads/images/car.jpg');
});
test('absolute cloud URLs and unrelated frontend paths are preserved', () => {
  for (const url of ['https://res.cloudinary.com/example/image/upload/car.jpg', '/placeholder-car.svg', '']) {
    assert.equal(resolveUploadUrl(url, 'http://localhost:5000/api'), url);
  }
});

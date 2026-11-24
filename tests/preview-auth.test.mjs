import { test } from 'node:test';
import assert from 'node:assert/strict';
import { previewGuard } from '../infrastructure/cloudflare/preview-auth.mjs';

const token = 't'.repeat(40); // synthetic test fixture, not a real secret
const env = { STUDIO_PREVIEW_TOKEN: token };
const req = (headers = {}, pathname = '/mcp') => new Request('https://example.invalid' + pathname, { method: 'POST', headers });
const auth = { Authorization: 'Bearer ' + token };

test('only authenticated machine traffic reaches the preview', async () => {
  assert.equal(await previewGuard(req(auth), env), null);
  assert.equal((await previewGuard(req(auth, '/other'), env)).status, 404);
  const cases = [
    [req(), env], [req(auth), {}], [req(auth), undefined],
    [req(auth), { STUDIO_PREVIEW_TOKEN: 'short' }],
    [req(auth), { STUDIO_PREVIEW_TOKEN: 'x '.repeat(32) }],
    [req({ Authorization: 'Bearer ' + 'x'.repeat(40) }), env],
    [req({ Authorization: 'Basic ' + token }), env],
    [req({ Authorization: 'Bearer ' + 'x'.repeat(513) }), env],
    [req({ ...auth, Origin: 'https://example.invalid' }), env],
  ];
  for (const [request, bindings] of cases) {
    const rejected = await previewGuard(request, bindings);
    assert.equal(rejected.status, 401);
    assert.equal(rejected.headers.get('Cache-Control'), 'no-store');
    assert.equal(rejected.headers.get('WWW-Authenticate'), 'Bearer');
    assert.equal(await rejected.text(), 'Unauthorized');
  }
});

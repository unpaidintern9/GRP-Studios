// Machine-only preview gate. This is not OAuth or team authorization.
function deny(status, text) {
  return new Response(text, {
    status,
    headers: { 'Cache-Control': 'no-store', ...(status === 401 ? { 'WWW-Authenticate': 'Bearer' } : {}) },
  });
}
export async function previewGuard(request, env) {
  if (new URL(request.url).pathname !== '/mcp') return deny(404, 'Not found');
  if (request.headers.has('Origin')) return deny(401, 'Unauthorized');
  const expected = env?.STUDIO_PREVIEW_TOKEN;
  if (typeof expected !== 'string' || !/^[\x21-\x7e]{32,512}$/.test(expected)) return deny(401, 'Unauthorized');
  const match = /^Bearer ([\x21-\x7e]{1,512})$/.exec(request.headers.get('Authorization') || '');
  if (!match) return deny(401, 'Unauthorized');
  const digest = async value => new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)));
  const [a, b] = await Promise.all([digest(match[1]), digest(expected)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0 ? null : deny(401, 'Unauthorized');
}

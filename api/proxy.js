// Vercel Edge Function: HTTPS proxy for China Radio / CNR HLS streams
// Keeps the proxy closed to known radio hosts and rewrites HLS playlists so
// every child playlist / media segment also travels through HTTPS.

export const config = { runtime: 'edge' };

const ALLOWED = new Set([
  'ngcdn001.cnr.cn','ngcdn002.cnr.cn','ngcdn003.cnr.cn','ngcdn004.cnr.cn',
  'ngcdn005.cnr.cn','ngcdn006.cnr.cn','ngcdn007.cnr.cn','ngcdn008.cnr.cn',
  'ngcdn009.cnr.cn','ngcdn010.cnr.cn','ngcdn011.cnr.cn','ngcdn012.cnr.cn',
  'ngcdn013.cnr.cn','ngcdn014.cnr.cn','ngcdn016.cnr.cn','ngcdn017.cnr.cn',
  'satellitepull.cnr.cn'
]);

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,HEAD,OPTIONS',
  'Access-Control-Allow-Headers': 'Range,Content-Type',
  'Access-Control-Expose-Headers': 'Content-Length,Content-Range,Accept-Ranges,Content-Type',
  'Cache-Control': 'no-store'
};

function proxied(requestUrl, target) {
  const incoming = new URL(requestUrl);
  return `${incoming.origin}/api/proxy?url=${encodeURIComponent(target)}`;
}

function rewriteUriAttributes(line, base, requestUrl) {
  return line.replace(/URI="([^"]+)"/g, (_, value) => {
    try {
      const absolute = new URL(value, base).toString();
      return `URI="${proxied(requestUrl, absolute)}"`;
    } catch {
      return `URI="${value}"`;
    }
  });
}

export default async function handler(request) {
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
  if (!['GET','HEAD'].includes(request.method)) return new Response('Method not allowed', { status: 405, headers: CORS });

  const incoming = new URL(request.url);
  const raw = incoming.searchParams.get('url');
  if (!raw) return Response.json({ ok: true, service: 'china-radio-proxy', runtime: 'vercel-edge' }, { headers: CORS });

  let target;
  try { target = new URL(raw); }
  catch { return new Response('Bad url', { status: 400, headers: CORS }); }

  if (!['http:','https:'].includes(target.protocol) || !ALLOWED.has(target.hostname)) {
    return new Response('Host not allowed', { status: 403, headers: CORS });
  }

  const headers = new Headers();
  const range = request.headers.get('range');
  if (range) headers.set('range', range);
  headers.set('user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1');
  headers.set('accept', '*/*');

  let upstream;
  try {
    upstream = await fetch(target.toString(), { method: request.method, headers, redirect: 'follow', cache: 'no-store' });
  } catch {
    return new Response('Upstream unavailable', { status: 502, headers: CORS });
  }

  const outHeaders = new Headers(upstream.headers);
  for (const [k,v] of Object.entries(CORS)) outHeaders.set(k,v);
  outHeaders.delete('content-security-policy');
  outHeaders.delete('content-security-policy-report-only');

  const type = (outHeaders.get('content-type') || '').toLowerCase();
  const isPlaylist = target.pathname.toLowerCase().endsWith('.m3u8') || type.includes('mpegurl');

  if (request.method === 'GET' && isPlaylist) {
    const text = await upstream.text();
    const base = new URL('.', target);
    const rewritten = text.split(/\r?\n/).map(line => {
      const trimmed = line.trim();
      if (!trimmed) return line;
      if (trimmed.startsWith('#')) return rewriteUriAttributes(line, base, request.url);
      try { return proxied(request.url, new URL(trimmed, base).toString()); }
      catch { return line; }
    }).join('\n');
    outHeaders.set('content-type', 'application/vnd.apple.mpegurl; charset=utf-8');
    outHeaders.delete('content-length');
    return new Response(rewritten, { status: upstream.status, headers: outHeaders });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders
  });
}

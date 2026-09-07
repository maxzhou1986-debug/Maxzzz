// China Radio HTTPS proxy for Cloudflare Workers
// Deploy this file as a Module Worker, then set PROXY_BASE in index.html.
// Only allow known radio hosts to avoid becoming an open proxy.
const ALLOWED = new Set([
  'ngcdn001.cnr.cn','ngcdn002.cnr.cn','ngcdn003.cnr.cn','ngcdn004.cnr.cn',
  'ngcdn005.cnr.cn','ngcdn006.cnr.cn','ngcdn007.cnr.cn','ngcdn008.cnr.cn',
  'ngcdn009.cnr.cn','ngcdn010.cnr.cn','ngcdn011.cnr.cn','ngcdn012.cnr.cn',
  'ngcdn013.cnr.cn','ngcdn014.cnr.cn','ngcdn016.cnr.cn','ngcdn017.cnr.cn'
]);
const cors={
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Methods':'GET,HEAD,OPTIONS',
  'Access-Control-Allow-Headers':'Range,Content-Type',
  'Access-Control-Expose-Headers':'Content-Length,Content-Range,Accept-Ranges,Content-Type',
  'Cache-Control':'no-store'
};
function proxyUrl(workerUrl,target){return workerUrl.origin+'/proxy?url='+encodeURIComponent(target)}
export default {
  async fetch(request){
    if(request.method==='OPTIONS') return new Response(null,{status:204,headers:cors});
    if(!['GET','HEAD'].includes(request.method)) return new Response('Method not allowed',{status:405,headers:cors});
    const incoming=new URL(request.url);
    if(incoming.pathname==='/health') return Response.json({ok:true,service:'china-radio-proxy'},{headers:cors});
    if(incoming.pathname!=='/proxy') return new Response('China Radio Proxy',{headers:cors});
    const raw=incoming.searchParams.get('url');
    if(!raw) return new Response('Missing url',{status:400,headers:cors});
    let target; try{target=new URL(raw)}catch{return new Response('Bad url',{status:400,headers:cors})}
    if(!['http:','https:'].includes(target.protocol)||!ALLOWED.has(target.hostname)) return new Response('Host not allowed',{status:403,headers:cors});
    const headers=new Headers();
    const range=request.headers.get('Range'); if(range) headers.set('Range',range);
    headers.set('User-Agent','Mozilla/5.0 AppleWebKit/605.1.15 Safari/605.1.15');
    let upstream;
    try{upstream=await fetch(target.toString(),{method:request.method,headers,redirect:'follow',cache:'no-store'})}
    catch(e){return new Response('Upstream unavailable',{status:502,headers:cors})}
    const outHeaders=new Headers(upstream.headers); Object.entries(cors).forEach(([k,v])=>outHeaders.set(k,v));
    const type=(outHeaders.get('content-type')||'').toLowerCase();
    if(request.method==='GET' && (type.includes('mpegurl')||target.pathname.endsWith('.m3u8'))){
      let text=await upstream.text();
      const base=new URL('.',target);
      text=text.split(/\r?\n/).map(line=>{
        const t=line.trim(); if(!t||t.startsWith('#')) return line;
        try{return proxyUrl(incoming,new URL(t,base).toString())}catch{return line}
      }).join('\n');
      outHeaders.set('Content-Type','application/vnd.apple.mpegurl');
      outHeaders.delete('Content-Length');
      return new Response(text,{status:upstream.status,headers:outHeaders});
    }
    return new Response(upstream.body,{status:upstream.status,statusText:upstream.statusText,headers:outHeaders});
  }
};

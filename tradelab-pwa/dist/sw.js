const CACHE='tradelab-pwa-1.0.0';
const ASSETS=['./','./index.html','./app.js','./reports.js','./styles.css','./project.json','./manifest.webmanifest','./icons/icon.svg','./icons/icon-192.png','./icons/icon-512.png','./icons/icon-maskable-512.png'];
const ALLOWED=new Set(ASSETS.map(p=>new URL(p,self.registration.scope).pathname));
self.addEventListener('install',event=>event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);
  for(const path of ASSETS){
    const url=new URL(path,self.registration.scope);
    const response=await fetch(new Request(url,{credentials:'same-origin',cache:'reload'}));
    if(!response.ok||response.redirected||new URL(response.url).origin!==self.location.origin)throw new Error('Conteúdo não disponível para uso offline.');
    await cache.put(url,response);
  }
  await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  for(const key of await caches.keys())if(key.startsWith('tradelab-pwa-')&&key!==CACHE)await caches.delete(key);
  await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==self.location.origin||!ALLOWED.has(url.pathname))return;
  event.respondWith((async()=>{
    try{
      const response=await fetch(request);
      if(response.ok&&!response.redirected){
        const cache=await caches.open(CACHE);await cache.put(request,response.clone());
      }
      return response;
    }catch{
      return (await caches.match(request,{ignoreSearch:true}))||Response.error();
    }
  })());
});

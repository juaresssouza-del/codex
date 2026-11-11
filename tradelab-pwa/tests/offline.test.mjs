import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

function harness(){
  const handlers={},stores=new Map();let offline=false,status=200,redirected=false;
  const origin='https://example.test',scope=origin+'/app/';
  const key=x=>(typeof x==='string'?x:x.url||x.href).split('?')[0];
  const caches={
    async open(name){if(!stores.has(name))stores.set(name,new Map());return {put:async(r,s)=>stores.get(name).set(key(r),s)};},
    async keys(){return [...stores.keys()];},async delete(name){return stores.delete(name);},
    async match(request){for(const m of stores.values())if(m.has(key(request)))return m.get(key(request));}
  };
  const context={URL,Request,Response,caches,self:{registration:{scope},location:{origin},addEventListener:(type,fn)=>handlers[type]=fn,skipWaiting:async()=>{},clients:{claim:async()=>{}}},fetch:async request=>{
    if(offline)throw new Error('offline');
    const response=new Response('app shell',{status});Object.defineProperty(response,'url',{value:request.url||request.href});Object.defineProperty(response,'redirected',{value:redirected});return response;
  }};
  vm.runInNewContext(fs.readFileSync(new URL('../dist/sw.js',import.meta.url),'utf8'),context);
  return {stores,setOffline:v=>offline=v,setStatus:v=>status=v,setRedirect:v=>redirected=v,
    async event(type){let result;handlers[type]({waitUntil:p=>result=p});await result;},
    async request(url,method='GET'){let result;handlers.fetch({request:new Request(url,{method}),respondWith:p=>result=p});return result===undefined?undefined:await result;},scope};
}
test('offline shell is available after successful install',async()=>{
  const h=harness();await h.event('install');h.setOffline(true);const response=await h.request(h.scope+'index.html');assert.equal(await response.text(),'app shell');
});
test('service worker does not intercept third-party requests or non-shell actions',async()=>{
  const h=harness();assert.equal(await h.request('https://other.test/'),undefined);assert.equal(await h.request(h.scope+'broker'),undefined);assert.equal(await h.request(h.scope+'index.html','POST'),undefined);
});
test('offline support does not bypass an online authentication rejection',async()=>{
  const h=harness();await h.event('install');h.setStatus(401);assert.equal((await h.request(h.scope+'index.html')).status,401);
});
test('install refuses redirected authentication content',async()=>{
  const h=harness();h.setRedirect(true);await assert.rejects(()=>h.event('install'),/offline/);assert.equal([...h.stores.values()][0].size,0);
});
test('activation removes only the old TradeLab caches',async()=>{
  const h=harness();h.stores.set('tradelab-pwa-old',new Map());h.stores.set('another-app',new Map());await h.event('activate');assert.equal(h.stores.has('tradelab-pwa-old'),false);assert.equal(h.stores.has('another-app'),true);
});

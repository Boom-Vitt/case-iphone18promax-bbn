import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { once } from 'node:events';
import http from 'node:http';
import vm from 'node:vm';
import { createApp, clientIp } from '../server/app.mjs';

test('preorder lifecycle, private slips, validation, persistence, and retryable Google sync', async () => {
  const dataDir = mkdtempSync(join(tmpdir(), 'bbn-test-'));
  let acceptSync = false, received;
  const google = http.createServer(async (req, res) => {
    const parts = []; for await (const chunk of req) parts.push(chunk);
    received = JSON.parse(Buffer.concat(parts));
    res.setHeader('Content-Type','application/json');
    res.end(JSON.stringify({ok:acceptSync,driveUrl:'https://drive.google.com/file/d/test/view'}));
  });
  google.listen(0,'127.0.0.1'); await once(google,'listening');
  const origin = 'http://localhost:4320';
  const options = {dataDir,username:'TestAdmin',password:'test-only-password',origin,googleUrl:`http://127.0.0.1:${google.address().port}`,googleSecret:'x'.repeat(64)};
  let app = createApp(options);
  app.server.listen(0,'127.0.0.1'); await once(app.server,'listening');
  let base = `http://127.0.0.1:${app.server.address().port}`, cookie='';
  async function request(path,method='GET',input,extra={}) {
    return fetch(base+path,{method,headers:{Origin:origin,'X-Requested-With':'BBN',...(cookie?{Cookie:cookie}:{}),...(input && !(input instanceof FormData)?{'Content-Type':'application/json'}:{}),...extra},body:input instanceof FormData?input:input?JSON.stringify(input):undefined});
  }
  const form = (overrides={},bytes=Buffer.from('89504e470d0a1a0a00000000','hex'),filename='slip.png') => {
    const f=new FormData();
    for(const [key,value] of Object.entries({product:'cognac',model:'iPhone 18 Pro Max',quantity:'2',name:'Test Customer',phone:'0800000000',address:'TEST ONLY address no delivery',postal:'10100',consent:'yes',quotedTotal:'2180',...overrides}))f.set(key,value);
    f.set('slip',new Blob([bytes]),filename);return f;
  };
  const settle = async () => { for(let i=0;i<100;i++){await new Promise(r=>setTimeout(r,10)); if(!app.isSyncing())return;}throw new Error('Sync did not finish'); };
  try {
    assert.equal((await request('/api/admin/dashboard')).status,401);
    assert.equal((await request('/.env')).status,404);
    assert.equal((await request('/api/login','POST',{username:'TestAdmin',password:'test-only-password'},{Origin:'https://evil.test'})).status,403);
    assert.equal((await request('/api/login','POST',{username:'TestAdmin',password:'wrong'})).status,401);
    const login=await request('/api/login','POST',{username:'TestAdmin',password:'test-only-password'});
    assert.equal(login.status,200); cookie=login.headers.get('set-cookie').split(';')[0];
    assert.match(login.headers.get('set-cookie'),/HttpOnly; SameSite=Strict/);
    const settings=(await (await request('/api/catalog')).json()).settings;
    assert.equal(settings.price,1090); assert.equal(settings.shipping,0); assert.equal(settings.open,true);
    assert.equal((await request('/api/admin/settings','PUT',{...settings,open:false})).status,200);
    assert.equal((await request('/api/orders','POST',form())).status,409);
    assert.equal((await request('/api/admin/settings','PUT',{...settings,open:true})).status,200);
    assert.equal((await request('/api/admin/settings','PUT',{...settings,open:true,recipient:'TEST ONLY',shippingNote:'TEST ONLY',contact:'TEST ONLY'})).status,200);
    assert.equal((await request('/api/orders','POST',form({quotedTotal:'1'}))).status,409);
    assert.equal((await request('/api/orders','POST',form({},Buffer.from('<script>bad</script>'),'slip.png'))).status,400);
    const created=await request('/api/orders','POST',form());
    assert.equal(created.status,201);const order=await created.json();assert.equal(order.total,2180);
    await settle();
    assert.equal(app.db.prepare('SELECT synced_revision FROM orders').get().synced_revision,0);
    assert.equal((await request('/api/admin/sync','POST',{})).status,502);
    assert.match((await (await request('/api/admin/dashboard')).json()).syncError,/Google/);
    assert.equal(received.order.lookup,undefined);assert.equal(received.order.slip_path,undefined);
    assert.equal((await request('/api/orders','POST',form())).status,409);
    assert.equal((await request('/api/order-status','POST',{id:order.id,token:'wrong'})).status,404);
    let tracked=await (await request('/api/order-status','POST',{id:order.id,token:order.token})).json();
    assert.equal(tracked.status,'pending');assert.equal(tracked.address,undefined);
    const adminCookie=cookie;cookie='';assert.equal((await request(`/api/admin/slips/${order.id}`)).status,401);cookie=adminCookie;
    assert.equal((await request(`/api/admin/slips/${order.id}`)).headers.get('content-type'),'image/png');
    assert.equal((await request(`/api/admin/orders/${order.id}`,'PATCH',{status:'rejected',revision:1,note:''})).status,400);
    assert.equal((await request(`/api/admin/orders/${order.id}`,'PATCH',{status:'approved',revision:1,note:'TEST verified'})).status,200);
    await settle();
    assert.equal((await request(`/api/admin/orders/${order.id}`,'PATCH',{status:'rejected',revision:1,note:'stale'})).status,409);
    acceptSync=true;await app.syncOrders();
    assert.equal(app.db.prepare('SELECT synced_revision FROM orders').get().synced_revision,2);
    assert.equal(received.order.status,'approved');
    const sync=await (await request('/api/admin/sync','POST',{})).json();assert.equal(sync.ok,true);assert.equal(sync.pending,0);
    const dashboard=await (await request('/api/admin/dashboard')).json();assert.equal(dashboard.totals.approvedRevenue,2180);assert.equal(dashboard.totals.unsynced,0);
    await new Promise(r=>app.server.close(r));
    app=createApp(options);app.server.listen(0,'127.0.0.1');await once(app.server,'listening');base=`http://127.0.0.1:${app.server.address().port}`;
    tracked=await (await request('/api/order-status','POST',{id:order.id,token:order.token})).json();assert.equal(tracked.status,'approved');
    assert.equal((await request('/api/logout','POST',{})).status,200);
    assert.equal((await request('/api/admin/dashboard')).status,401);
  } finally {await settle();await new Promise(r=>app.server.close(r));await new Promise(r=>google.close(r));rmSync(dataDir,{recursive:true,force:true});}
});

test('Apps Script refuses unauthenticated writes and escapes spreadsheet formulas', () => {
  const ctx=vm.createContext({PropertiesService:{getScriptProperties:()=>({getProperty:()=> 'x'.repeat(64)})},ContentService:{MimeType:{JSON:'json'},createTextOutput:value=>({setMimeType:()=>JSON.parse(value)})}});
  vm.runInContext(readFileSync(new URL('../google-apps-script/Code.gs',import.meta.url),'utf8'),ctx);
  assert.equal(ctx.doPost({postData:{contents:JSON.stringify({secret:'wrong'})}}).error,'unauthorized');
  assert.equal(ctx.doPost({postData:{contents:JSON.stringify({secret:'x'.repeat(64),action:'ping'})}}).ok,true);
  assert.equal(ctx.doPost({postData:{contents:JSON.stringify({secret:'x'.repeat(64),action:'upsert',order:{id:'bad'}})}}).error,'invalid_order');
  assert.equal(ctx.safeCell('=IMPORTXML("bad")'),"'=IMPORTXML(\"bad\")");
  assert.equal(ctx.safeCell('0800000000'),'0800000000');
});

 test('proxy IP trust is opt-in, loopback-only, and ignores spoofed prefixes', () => {
  const request = (remote, forwarded) => ({socket:{remoteAddress:remote},headers:{'x-forwarded-for':forwarded}});
  assert.equal(clientIp(request('127.0.0.1','198.51.100.7'),''),'127.0.0.1');
  assert.equal(clientIp(request('203.0.113.4','198.51.100.7'),'loopback'),'203.0.113.4');
  assert.equal(clientIp(request('127.0.0.1','spoof, 198.51.100.7'),'loopback'),'198.51.100.7');
  assert.equal(clientIp(request('::1','invalid'),'loopback'),'::1');
});

test('20 per design: concurrent reservations, rejection release, reapproval guard, and restart preservation', async () => {
  const dataDir=mkdtempSync(join(tmpdir(),'bbn-stock-'));
  const origin='http://localhost:4320';
  const options={dataDir,origin,username:'TestAdmin',password:'test-only-password',googleUrl:'',googleSecret:'',trustProxy:'loopback'};
  let app=createApp(options),base,cookie='',serial=0;
  const start=async()=>{app.server.listen(0,'127.0.0.1');await once(app.server,'listening');base=`http://127.0.0.1:${app.server.address().port}`;};
  const req=(path,method='GET',body)=>fetch(base+path,{method,headers:{Origin:origin,'X-Requested-With':'BBN','X-Forwarded-For':`198.51.100.${++serial}`,Cookie:cookie,...(body && !(body instanceof FormData)?{'Content-Type':'application/json'}:{})},body:body instanceof FormData?body:body?JSON.stringify(body):undefined});
  const buy=(product,quantity,model='iPhone 18 Pro Max')=>{
    const form=new FormData();
    for(const [k,v] of Object.entries({product,quantity,model,name:'Stock Test',phone:'0800000000',address:'TEST ONLY address no delivery',postal:'10100',consent:'yes',quotedTotal:1090*quantity}))form.set(k,String(v));
    form.set('slip',new Blob([Buffer.from('89504e470d0a1a0a','hex'),String(serial)]),'slip.png');
    return req('/api/orders','POST',form);
  };
  const catalog=async()=> (await (await req('/api/catalog')).json());
  const stock=async id=>(await catalog()).products.find(p=>p.id===id).stock;
  const review=(id,status,revision)=>req(`/api/admin/orders/${id}`,'PATCH',{status,revision,note:'Test review'});
  try {
    await start();
    const initial=await catalog(); assert.equal(initial.products.length,12);assert.ok(initial.products.every(p=>p.stock===20));
    const login=await req('/api/login','POST',{username:'TestAdmin',password:'test-only-password'});cookie=login.headers.get('set-cookie').split(';')[0];
    assert.equal((await req('/api/admin/sync','POST',{})).status,503);
    for(const p of initial.products){const r=await buy(p.id,1);assert.equal(r.status,201);assert.equal(await stock(p.id),19);}
    const competing=await Promise.all([buy('cognac',19),buy('cognac',19,'iPhone 18 Pro')]);
    assert.deepEqual(competing.map(r=>r.status).sort(),[201,409]);
    const order=await competing.find(r=>r.status===201).json();assert.equal(await stock('cognac'),0);
    assert.equal((await review(order.id,'approved',1)).status,200);assert.equal(await stock('cognac'),0);
    assert.equal((await review(order.id,'rejected',2)).status,200);assert.equal(await stock('cognac'),19);
    assert.equal((await buy('cognac',19)).status,201);
    assert.equal((await review(order.id,'approved',3)).status,409);assert.equal(await stock('cognac'),0);
    assert.equal((await review(order.id,'pending',3)).status,409);
    assert.equal(app.db.prepare('SELECT status,revision FROM orders WHERE id=?').get(order.id).revision,3);
    assert.equal(app.db.prepare('SELECT count(*) AS n FROM orders').get().n,14);
    const {readdirSync}=await import('node:fs');assert.equal(readdirSync(join(dataDir,'slips')).length,14);
    await req('/api/admin/settings','PUT',{...initial.settings,open:false});
    await new Promise(r=>app.server.close(r));app=createApp(options);await start();
    assert.equal(await stock('cognac'),0);assert.equal((await catalog()).settings.open,false);
    assert.equal((await buy('midnight',1)).status,409);
  } finally {await new Promise(r=>app.server.close(r));rmSync(dataDir,{recursive:true,force:true});}
});

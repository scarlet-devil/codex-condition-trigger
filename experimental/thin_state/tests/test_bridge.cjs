"use strict";
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {kelanThinNative, kelanThinFollower, kelanThinHandlers} = require('../thin_bridge.js');
const method = 'kelan/thread/read-status';
const issuedAtMs = Date.now();
const params = {threadId:'synthetic-thread',budgetMs:9000,issuedAtMs,expiresAtMs:issuedAtMs+9000};
function native(status='idle') {
  const requests=[];
  const thread={id:params.threadId,cwd:'C:\\fixture',status:{type:status}};
  Object.defineProperty(thread,'turns',{get(){throw Error('history accessed');}});
  const c={options:{hostId:'local',transport:{kind:'stdio'}},connection:{},
    initialized:true,initializationGeneration:7,disposed:false,isAppQuitting:false,isStoppingConnection:false,
    getConnectionState:()=> 'connected',captureRequestLifetime:()=>()=>{},
    registerInternalConnectionStateHandler(fn){c.event=fn; return()=>{c.unsubscribed=true;};},
    async sendInternalRequest(r,o){requests.push([r,o]);return {id:r.id,result:{thread}};},
    ensureReady(){throw Error('ensureReady forbidden');},
    messageDelivery:{sendClientResponse(w,r){c.response=r;},sendErrorResponse(){throw Error('raw errors forbidden');}}};
  return {c,requests,thread};
}
function manager(result) {
  const e={hostId:'local',disposed:false,role:'owner',calls:[],assertActive(){assert.equal(this.disposed,false);},
    assertThreadFollowerOwner(id){assert.equal(id,params.threadId);assert.equal(this.role,'owner');},
    addStreamRoleCallback(id,fn){assert.equal(id,params.threadId);this.event=fn;return()=>{this.unsubscribed=true;};},
    requestClient:{async sendRequest(m,p,o){e.calls.push([m,p,o]);return result;}}};
  return e;
}
for(const status of ['idle','active','notLoaded','systemError']) test('native summary '+status,async()=>{
  const {c,requests}=native(status);const r=await kelanThinNative(c,params,'one');
  assert.deepEqual(r,{schema:1,hostId:'local',threadId:params.threadId,cwd:'C:\\fixture',status,connectionGeneration:7});
  assert.equal(requests.length,1);assert.equal(requests[0][0].method,'thread/read');
  assert.deepEqual(requests[0][0].params,{threadId:params.threadId,includeTurns:false});
  assert.equal(requests[0][1].timeoutMs<=9000,true);assert.equal(c.unsubscribed,true);
});
for(const change of ['connection','generation','lifetime','event','dispose','stopping']) test('reject native retirement '+change,async()=>{
  const {c}=native();const original=c.sendInternalRequest;
  let retired=false;c.captureRequestLifetime=()=>()=>{if(retired)throw Error('retired');};
  c.sendInternalRequest=async(...args)=>{const r=await original(...args);
    if(change==='connection')c.connection={};if(change==='generation')c.initializationGeneration++;
    if(change==='lifetime')retired=true;if(change==='event')c.event('connecting');
    if(change==='dispose')c.disposed=true;if(change==='stopping')c.isStoppingConnection=true;return r;};
  await assert.rejects(kelanThinNative(c,params,'one'));assert.equal(c.unsubscribed,true);
});
for(const field of ['id','cwd','status','long-cwd']) test('reject malformed native '+field,async()=>{
  const {c,thread}=native();if(field==='id')thread.id='wrong';if(field==='cwd')delete thread.cwd;
  if(field==='status')thread.status={};if(field==='long-cwd')thread.cwd='界'.repeat(70000);
  await assert.rejects(kelanThinNative(c,params,'one'));
});
for(const mode of ['not-initialized','no-connection','remote','wrong-transport','disconnected']) test('reject unavailable '+mode,async()=>{
  const {c,requests}=native();if(mode==='not-initialized')c.initialized=false;if(mode==='no-connection')c.connection=null;
  if(mode==='remote')c.options.hostId='remote';if(mode==='wrong-transport')c.options.transport.kind='websocket';
  if(mode==='disconnected')c.getConnectionState=()=> 'disconnected';
  await assert.rejects(kelanThinNative(c,params,'one'));assert.equal(requests.length,0);
});
test('owner path has one narrow call and does not read stored conversation',async()=>{
  const {c}=native();const result=await kelanThinNative(c,params,'one');const e=manager(result);
  e.getConversation=()=>{throw Error('snapshot forbidden');};
  assert.deepEqual(await kelanThinFollower(e,{conversationId:params.threadId,budgetMs:9000}),result);
  assert.equal(e.calls.length,1);assert.equal(e.calls[0][0],method);assert.equal(e.unsubscribed,true);
});
for(const mode of ['lost','aba','client','disposed','wrong-result']) test('owner change '+mode,async()=>{
  const {c}=native();const result=await kelanThinNative(c,params,'one');const e=manager(result);
  e.requestClient.sendRequest=async()=>{if(mode==='lost')e.role='follower';if(mode==='aba'){e.event('follower');e.event('owner');}
    if(mode==='client')e.requestClient={};if(mode==='disposed')e.disposed=true;
    if(mode==='wrong-result')return {...result,threadId:'wrong'};return result;};
  await assert.rejects(kelanThinFollower(e,{conversationId:params.threadId,budgetMs:9000}));assert.equal(e.unsubscribed,true);
});
test('legacy handler arguments and return identity stay unchanged',async()=>{
  const calls=[];const oldClient=(...a)=>{calls.push(a);return 'old-client';};const oldHost=(...a)=>{calls.push(a);return 'old-host';};
  const {c}=native();const [client,host]=kelanThinHandlers(c,oldClient,oldHost);
  const a=[{}, {method:'thread/read',params:{includeTurns:true}},1,2,3];assert.equal(client(...a),'old-client');
  const b=[{method:'thread/resume'},1,2,3,4];assert.equal(host(...b),'old-host');assert.deepEqual(calls,[a,b]);
});
test('narrow client bridge replies to existing recipient only',async()=>{
  const {c}=native();const [client]=kelanThinHandlers(c,()=>{throw Error('queue forbidden');},()=>{});
  await client({isDestroyed:()=>false},{id:'one',method,params});
  assert.equal(c.response.id,'one');assert.equal(c.response.result.status,'idle');
});
test('destroyed renderer is not broadcast to other windows',async()=>{
  const {c,requests}=native();const [client]=kelanThinHandlers(c,()=>{},()=>{});
  await client({isDestroyed:()=>true},{id:'one',method,params});assert.equal(c.response,undefined);assert.equal(requests.length,0);
});
test('host bridge uses beforeSend guard and supports abandon',async()=>{
  const {c}=native();const [,host]=kelanThinHandlers(c,()=>{},()=>{});let guards=0;
  const handle=host({id:'one',method,params},null,null,null,()=>{guards++;});
  const r=await handle.promise;assert.equal(r.result.status,'idle');assert.ok(guards>=2);
  const stopped=host({id:'two',method,params});stopped.abandon();await assert.rejects(stopped.promise);
});
test('native errors are fixed codes, no private server message',async()=>{
  const {c}=native();c.sendInternalRequest=async()=>{throw Error('PRIVATE SENTINEL');};
  const [client]=kelanThinHandlers(c,()=>{},()=>{});await client({isDestroyed:()=>false},{id:'one',method,params});
  assert.equal(c.response.error.message,'thin-state-unavailable');assert.doesNotMatch(JSON.stringify(c.response),/PRIVATE/);
});
test('delayed queued private query is rejected before native read',async()=>{
  const {c,requests}=native();const now=Date.now();
  await assert.rejects(kelanThinNative(c,{...params,issuedAtMs:now-10000,expiresAtMs:now-1000},'late'),/expired/);
  assert.equal(requests.length,0);
});
test('future timestamp and extended expiration are rejected',async()=>{
  const {c,requests}=native();const now=Date.now();
  await assert.rejects(kelanThinNative(c,{...params,issuedAtMs:now+10000,expiresAtMs:now+19000},'future'),/expired/);
  await assert.rejects(kelanThinNative(c,{...params,expiresAtMs:params.expiresAtMs+1000},'extend'),/expired/);
  assert.equal(requests.length,0);
});
test('host bridge also redacts native error messages',async()=>{
  const {c}=native();c.sendInternalRequest=async()=>{throw Error('PRIVATE SENTINEL');};
  const [,host]=kelanThinHandlers(c,()=>{},()=>{});
  await assert.rejects(host({id:'private',method,params}).promise,
    error=>error.message==='thin-state-unavailable');
});

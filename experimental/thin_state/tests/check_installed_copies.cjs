"use strict";
// Module-slice tests only. Never require/import an installed Desktop bundle.
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict');
const acorn=require(process.argv[3]);
const root=process.argv[2];
const helper=fs.readFileSync(path.join(__dirname,'../thin_bridge.js'),'utf8').split('// EXPORTS_START')[0];
const names=['.vite__build__src-CsH31EEu.js','webview__assets__app-initial-ad16eaadf81f.js',
  '.vite__build__application-network-startup-BG13czUt.js'];
let checks=0;
function parse(source){return acorn.parse(source,{ecmaVersion:'latest',sourceType:'module'});}
function find(ast, predicate){const pending=[ast];while(pending.length){const n=pending.pop();if(!n||typeof n!=='object')continue;
  if(predicate(n))return n;for(const v of Object.values(n)){if(Array.isArray(v))pending.push(...v);else if(v&&typeof v==='object')pending.push(v);}}
  throw Error('expected AST node absent');}
function scope(){return vm.createContext({performance,TextEncoder,setTimeout,clearTimeout,Buffer,_0:10000,y0:10000,Io:()=>false});}
function loadFunction(source,ast,needle,context){const i=source.indexOf(needle);assert.ok(i>=0);
  const n=find(ast,n=>n.type==='FunctionDeclaration'&&n.start<=i&&n.end>i);
  return vm.runInContext('('+source.slice(n.start,n.end)+')',context);}
function clean(v){return JSON.parse(JSON.stringify(v));}
(async()=>{
 for(const name of names){
  const old=fs.readFileSync(path.join(root,'original__'+name),'utf8');
  const current=fs.readFileSync(path.join(root,'patched__'+name),'utf8');
  const a=parse(old),b=parse(current);checks+=2;
  if(name===names[2]){
    const context=scope();
    const before=loadFunction(old,a,'function Wc(',context),after=loadFunction(current,b,'function Wc(',context);
    vm.runInContext('function Uc(s){const d=Buffer.from(s);const h=Buffer.alloc(4);h.writeUInt32LE(d.length);return Buffer.concat([h,d]);}',context);
    const legacy={type:'broadcast',method:'thread-stream-state-changed',params:{revision:17,turns:['x'.repeat(70000)]}};
    assert.deepEqual(after(legacy),before(legacy));checks++;
    assert.throws(()=>after({type:'response',method:'thread-follower-read-thread-status',result:'界'.repeat(30000)}),/oversize/);checks++;
    const bounded={type:'response',method:'thread-follower-read-thread-status',result:{status:'idle'}};
    assert.deepEqual(after(bounded),before(bounded));checks++;continue;
  }
  const context=scope();vm.runInContext(helper,context);
  const dispatch=loadFunction(current,b,'case`thread-follower-read-model-settings`',context);
  const prior=loadFunction(old,a,'case`thread-follower-read-model-settings`',scope());
  const native={schema:1,hostId:'local',threadId:'fixture',cwd:'C:\\fixture',status:'idle',connectionGeneration:1};
  const calls=[];const manager={hostId:'local',disposed:false,assertActive(){},assertThreadFollowerOwner(id){assert.equal(id,'fixture');},
    addStreamRoleCallback(){return()=>{};},requestClient:{async sendRequest(m,p){calls.push([m,p]);return native;}},
    getConversation(){return null;},getConversationStreamRevision(){return 17;},
    async getCompleteConversationTurns(id){assert.equal(id,'fixture');},broadcastConversationSnapshot(){return 17;}};
  const thin=await dispatch(manager,{method:'thread-follower-read-thread-status',params:{conversationId:'fixture',budgetMs:9000}});
  assert.deepEqual(clean(thin),{method:'thread-follower-read-thread-status',result:native});assert.equal(calls.length,1);checks++;
  const req={method:'thread-follower-load-complete-history',params:{conversationId:'fixture'}};
  assert.deepEqual(clean(await dispatch(manager,req)),clean(await prior(manager,req)));checks++;
  if(name===names[0]){
    const regOld=loadFunction(old,a,'function T0(',scope()),regNew=loadFunction(current,b,'function T0(',scope());
    function registrations(fn){const methods=[];fn({hostId:'local',ipcClient:{addRequestHandler(m){methods.push(m);return()=>{};}},canHandle:()=>true});return methods;}
    const priorMethods=registrations(regOld), newMethods=registrations(regNew);
    assert.deepEqual(newMethods.filter(m=>m!=='thread-follower-read-thread-status'),priorMethods);
    assert.equal(newMethods.filter(m=>m==='thread-follower-read-thread-status').length,1);checks++;
    // Table extraction is anchored to the existing method entry, independent of variable spelling.
    const entry=old.indexOf('"thread-follower-read-model-settings":1,');
    const start=old.lastIndexOf('{',entry),end=old.indexOf('}',entry)+1;
    const originalTable=vm.runInNewContext('('+old.slice(start,end)+')');
    const entryNew=current.indexOf('"thread-follower-read-model-settings":1,');
    const startNew=current.lastIndexOf('{',entryNew),endNew=current.indexOf('}',entryNew)+1;
    const table=vm.runInNewContext('('+current.slice(startNew,endNew)+')');
    assert.equal(table['thread-follower-read-thread-status'],1);delete table['thread-follower-read-thread-status'];
    assert.deepEqual(clean(table),clean(originalTable));checks++;
    const protocolScope=scope();protocolScope.ke={...table,'thread-follower-read-thread-status':1};
    const nativeVersion=loadFunction(current,b,'function je(',protocolScope);
    assert.equal(nativeVersion('thread-follower-read-thread-status',{},undefined),1);
    assert.equal(nativeVersion('thread-follower-read-thread-status',{},'local'),2);checks++;
    const anchor='[this.handleClientRequest,this.handleHostRequest]=kelanThinHandlers(this,r.handleClientRequest,r.handleHostRequest)';
    assert.equal(current.split(anchor).length,2);
    const install=vm.runInContext('(function(r){'+anchor+';return this;})',context);
    const fixture={};install.call(fixture,{handleClientRequest:()=> 'old',handleHostRequest:()=> 'legacy'});
    assert.equal(fixture.handleClientRequest(null,{method:'unrelated'}),'old');checks++;
    const nativeClass=find(a,n=>n.type==='ClassExpression'&&n.body.body.some(m=>m.key?.name==='captureRequestLifetime'));
    const nativeFixture={options:{hostId:'local',transport:{kind:'stdio'}},connection:{},initialized:true,
      initializationGeneration:3,connectionState:'connected',connectionStateHandlers:new Set(),
      catalogRequestGeneration:2,authTokenGeneration:4,disposed:false,
      async sendInternalRequest(request){assert.equal(request.method,'thread/read');
        return {id:request.id,result:{thread:{id:'fixture',cwd:'C:\\fixture',status:{type:'idle'}}}};}};
    for(const method of ['captureRequestLifetime','registerInternalConnectionStateHandler','getConnectionState']){
      const node=nativeClass.body.body.find(m=>m.key?.name===method);assert.ok(node,'missing actual native API '+method);
      nativeFixture[method]=vm.runInContext('({'+old.slice(node.start,node.end)+'})',context)[method];
    }
    const issuedAtMs=Date.now();
    const actualNative=await context.kelanThinNative(nativeFixture,
      {threadId:'fixture',budgetMs:9000,issuedAtMs,expiresAtMs:issuedAtMs+9000},'shape-check');
    assert.equal(actualNative.status,'idle');assert.equal(nativeFixture.connectionStateHandlers.size,0);checks++;
  }
 }
 console.log(JSON.stringify({checks,syntax_modules:6,full_desktop_started:false,
   scope:'AST parse + extracted real patched dispatch/registration/framing functions in synthetic VM'},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});

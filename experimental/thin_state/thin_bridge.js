"use strict";
// Experimental copy-only helpers. No timers, transport or registration at load.
function kelanThinString(value, max) {
  if (typeof value !== 'string' || !value || value.length > max || [...value].some(c => c.charCodeAt(0) < 32)) {
    throw Error('thin-state-invalid');
  }
  return value;
}
function kelanThinBudget(value) {
  if (!Number.isInteger(value) || value < 1 || value > 9000) throw Error('thin-state-budget');
  return value;
}
function kelanThinProject(value, threadId) {
  if (!value || value.schema !== 1 || value.hostId !== 'local' || value.threadId !== threadId ||
      !Number.isSafeInteger(value.connectionGeneration) || value.connectionGeneration < 0 ||
      !['idle','active','notLoaded','systemError'].includes(value.status)) throw Error('thin-state-invalid');
  const result = {schema:1,hostId:'local',threadId:kelanThinString(value.threadId,256),
    cwd:kelanThinString(value.cwd,8192),status:value.status,connectionGeneration:value.connectionGeneration};
  if (new TextEncoder().encode(JSON.stringify(result)).length > 60000) throw Error('thin-state-oversize');
  return result;
}
async function kelanThinNative(connection, params, requestId) {
  if (!params || Object.keys(params).sort().join(',') !== 'budgetMs,expiresAtMs,issuedAtMs,threadId') throw Error('thin-state-invalid');
  const threadId = kelanThinString(params.threadId,256);
  const budget = kelanThinBudget(params.budgetMs);
  const now = Date.now();
  if (!Number.isSafeInteger(params.issuedAtMs) || !Number.isSafeInteger(params.expiresAtMs) ||
      params.expiresAtMs-params.issuedAtMs !== budget || now < params.issuedAtMs || now >= params.expiresAtMs) {
    throw Error('thin-state-expired');
  }
  kelanThinString(requestId,256);
  const original = connection.connection, generation = connection.initializationGeneration;
  const lifetime = connection.captureRequestLifetime();
  let changed = false;
  const deadline = performance.now() + Math.min(budget,params.expiresAtMs-now);
  const check = () => {
    lifetime();
    if (changed || performance.now() >= deadline || connection.disposed || connection.isAppQuitting ||
        connection.isStoppingConnection || !connection.initialized || !original ||
        connection.connection !== original || connection.initializationGeneration !== generation ||
        connection.options.hostId !== 'local' || connection.options.transport.kind !== 'stdio' ||
        connection.getConnectionState() !== 'connected') throw Error('thin-state-unavailable');
  };
  check();
  const unsubscribe = connection.registerInternalConnectionStateHandler(() => { changed = true; });
  try {
    check();
    const id = 'kelan-thin:' + requestId;
    const response = await connection.sendInternalRequest({id,method:'thread/read',params:{threadId,includeTurns:false}},
      {timeoutMs:Math.max(1,Math.floor(deadline-performance.now()))});
    check();
    if (!response || response.id !== id || response.error != null) throw Error('thin-state-unavailable');
    const thread = response.result?.thread;
    // Deliberately name fields; never clone, enumerate or stringify native thread/history.
    return kelanThinProject({schema:1,hostId:connection.options.hostId,threadId:thread?.id,
      cwd:thread?.cwd,status:thread?.status?.type,connectionGeneration:generation},threadId);
  } finally { unsubscribe(); }
}
async function kelanThinFollower(manager, params) {
  if (!params || Object.keys(params).sort().join(',') !== 'budgetMs,conversationId') throw Error('thin-state-invalid');
  const threadId = kelanThinString(params.conversationId,256), budget = kelanThinBudget(params.budgetMs);
  const client = manager.requestClient, deadline = performance.now() + budget;
  let changed = false, timer;
  const check = () => {
    manager.assertActive(); manager.assertThreadFollowerOwner(threadId);
    if (manager.hostId !== 'local' || manager.disposed || manager.requestClient !== client || changed ||
        performance.now() >= deadline) throw Error('thin-state-owner-changed');
  };
  check();
  const unsubscribe = manager.addStreamRoleCallback(threadId,() => { changed = true; });
  try {
    check();
    const remaining = Math.max(1,Math.floor(deadline-performance.now()));
    const issuedAtMs = Date.now();
    const result = await Promise.race([
      client.sendRequest('kelan/thread/read-status',
        {threadId,budgetMs:remaining,issuedAtMs,expiresAtMs:issuedAtMs+remaining},{timeoutMs:remaining}),
      new Promise((_,reject) => { timer=setTimeout(() => reject(Error('thin-state-timeout')),remaining); })
    ]);
    check();
    return kelanThinProject(result,threadId);
  } finally { clearTimeout(timer); unsubscribe(); }
}
function kelanThinHandlers(connection, oldClient, oldHost) {
  const method = 'kelan/thread/read-status';
  function client(...args) {
    const [window,request] = args;
    if (request?.method !== method) return oldClient(...args);
    return (async () => {
      if (!window || window.isDestroyed()) return;
      let response;
      try { response={id:request.id,result:await kelanThinNative(connection,request.params,request.id)}; }
      catch { response={id:request.id,error:{code:-32000,message:'thin-state-unavailable'}}; }
      // Existing sendClientResponse broadcasts when a recipient dies: prevent that fallback.
      if (!window.isDestroyed()) connection.messageDelivery.sendClientResponse(window,response,method);
    })();
  }
  function host(...args) {
    const [request,,,,beforeSend] = args;
    if (request?.method !== method) return oldHost(...args);
    let abandoned = false;
    const check = () => { if (abandoned) throw Error('thin-state-abandoned'); beforeSend?.(); };
    const promise = Promise.resolve().then(async () => {
      check();
      const result = await kelanThinNative(connection,request.params,request.id);
      check();
      return {id:request.id,result};
    }).catch(() => { throw Error('thin-state-unavailable'); });
    return {promise,abandon:() => { abandoned=true; }};
  }
  return [client,host];
}
// EXPORTS_START (excluded from installed-source copy patches)
module.exports = { kelanThinNative, kelanThinFollower, kelanThinHandlers };

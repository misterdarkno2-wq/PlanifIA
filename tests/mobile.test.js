import {test} from 'node:test';
import assert from 'node:assert/strict';

test('el navegador conserva cookies y protección de peticiones',async()=>{
 let received;
 globalThis.fetch=async(url,options)=>{received={url,options};return {status:200,json:async()=>({id:7})};};
 const {request,isNative}=await import('../frontend/js/connection.js?web');
 assert.equal(isNative,false);
 assert.deepEqual(await request('/tareas',{method:'POST',body:{titulo:'Estudiar'}}),{status:200,data:{id:7}});
 assert.equal(received.url,'/api/tareas');
 assert.equal(received.options.credentials,'same-origin');
 assert.equal(received.options.headers['X-Planifia-Request'],'1');
 assert.equal(received.options.body,'{"titulo":"Estudiar"}');
 globalThis.fetch=async()=>({status:204});
 assert.deepEqual(await request('/auth/logout',{method:'POST'}),{status:204,data:null});
 globalThis.fetch=async()=>{throw new TypeError('offline');};
 await assert.rejects(request('/dashboard'),/No pudimos conectar/);
});

test('la app usa el puente nativo y conserva los errores del servidor',async()=>{
 let received;
 globalThis.__TAURI__={core:{invoke:async(command,args)=>{received={command,args};return {status:401,data:{detail:'Sesión vencida'}};}}};
 const {request,isNative}=await import('../frontend/js/connection.js?native');
 assert.equal(isNative,true);
 assert.deepEqual(await request('/auth/me'),{status:401,data:{detail:'Sesión vencida'}});
 assert.deepEqual(received,{command:'api_request',args:{path:'/auth/me',method:'GET',body:null}});
 await request('/tareas/1/estado',{method:'patch',body:{estado:'completada'}});
 assert.deepEqual(received.args,{path:'/tareas/1/estado',method:'PATCH',body:{estado:'completada'}});
 globalThis.__TAURI__.core.invoke=async()=>{throw 'El túnel no responde.';};
 await assert.rejects(request('/dashboard'),/El túnel no responde/);
 delete globalThis.__TAURI__;
});

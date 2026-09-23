import {test} from 'node:test';
import assert from 'node:assert/strict';
import {remoteConnection,httpsOrigin} from '../frontend/js/remote.js';

function storage(){const data=new Map();return {getItem:key=>data.get(key)||null,setItem:(key,value)=>data.set(key,value),removeItem:key=>data.delete(key)};}

test('Pages conserva la sesión al recargar, sin cookies de terceros, y la revoca al salir',async()=>{
 const session=storage(),settings=storage(),calls=[];let status=200,data={id:7,sessionToken:'a'.repeat(43)};
 const fetcher=async(url,options)=>{calls.push({url,options});return {status,json:async()=>({...data})};};
 let client=remoteConnection('https://api.example.com',{fetcher,session,settings});
 assert.deepEqual(await client.request('/auth/login',{method:'POST',body:{correo:'test@example.com'}}),{status:200,data:{id:7}});
 client=remoteConnection('https://api.example.com',{fetcher,session,settings});data={id:7};
 await client.request('/auth/me');
 assert.equal(calls.at(-1).options.headers.Authorization,'Bearer '+'a'.repeat(43));
 assert.equal(calls.at(-1).options.credentials,'omit');
 status=204;await client.request('/auth/logout',{method:'POST'});status=401;await client.request('/auth/me');
 assert.equal(calls.at(-1).options.headers.Authorization,undefined);
});

test('cambiar de servidor no transfiere sesiones y un servidor fallido conserva la conexión',async()=>{
 const session=storage(),settings=storage();let ok=true;
 session.setItem('planifia-session:https://old.example.com','a'.repeat(43));
 const fetcher=async()=>({ok,json:async()=>({estado:'ok',conexion:'PyMySQL'})});
 const client=remoteConnection('https://old.example.com',{fetcher,session,settings});
 ok=false;await assert.rejects(client.setServer('https://new.example.com'));
 assert.equal(client.server(),'https://old.example.com');
 assert(session.getItem('planifia-session:https://old.example.com'));
 ok=true;await client.setServer('https://new.example.com');
 assert.equal(client.server(),'https://new.example.com');
 assert.equal(session.getItem('planifia-session:https://old.example.com'),null);
 for(const value of ['http://example.com','https://user:secret@example.com','https://example.com/app','https://example.com?x=1'])assert.throws(()=>httpsOrigin(value));
});

test('un 401 antiguo no elimina una sesión nueva',async()=>{
 const session=storage(),settings=storage(),key='planifia-session:https://api.example.com';session.setItem(key,'old');
 let release;
 const client=remoteConnection('https://api.example.com',{session,settings,fetcher:()=>new Promise(resolve=>{release=resolve;})});
 const pending=client.request('/auth/me');session.setItem(key,'new');release({status:401,json:async()=>({detail:'Vencida'})});await pending;
 assert.equal(session.getItem(key),'new');
});

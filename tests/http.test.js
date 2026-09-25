import {test} from 'node:test';
import assert from 'node:assert/strict';
import {fetchJSON,requestTimeout} from '../frontend/js/http.js';

const untilAborted=signal=>new Promise((resolve,reject)=>{
 signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true});
});

test('una conexión sin respuesta se cancela y permite informar del tiempo agotado',async()=>{
 let signal;
 const fetcher=async(url,options)=>{signal=options.signal;return untilAborted(signal);};
 await assert.rejects(fetchJSON('/api/auth/login',{}, {fetcher,timeoutMs:20}),/tardando demasiado/);
 assert.equal(signal.aborted,true);
});

test('el límite también cubre un cuerpo de respuesta que no termina de llegar',async()=>{
 const fetcher=async(url,{signal})=>({status:200,json:()=>untilAborted(signal)});
 await assert.rejects(fetchJSON('/api/auth/login',{}, {fetcher,timeoutMs:20}),/tardando demasiado/);
});

test('conserva los errores HTTP y da tiempo suficiente a la generación con IA',async()=>{
 const fetcher=async()=>({status:401,json:async()=>({detail:'Correo o contraseña incorrectos.'})});
 assert.deepEqual(await fetchJSON('/api/auth/login',{}, {fetcher}),{status:401,data:{detail:'Correo o contraseña incorrectos.'}});
 assert.equal(requestTimeout('/auth/login'),20000);
 assert.ok(requestTimeout('/planes/generar')>180000);
});

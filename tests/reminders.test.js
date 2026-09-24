import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createReminderController} from '../frontend/js/reminder-controller.js';

const now=Date.parse('2026-09-24T12:00:00Z');
const item={key:'tarea:1:2026-09-25',title:'Entrega mañana',body:'Historia',at:'2026-09-25T12:00:00+00:00'};
function fixture(){
 const pending=new Map(),saved=new Map(),calls=[];
 let granted=true,response={status:200,data:{items:[item]}},fetcher=async()=>response;
 const storage={getItem:key=>saved.get(key),setItem:(key,value)=>saved.set(key,value)};
 const bridge=async(command,args)=>{
  command=command.split('|')[1];calls.push(command);
  if(command==='is_permission_granted')return granted;
  if(command==='request_permission')return granted?'granted':'denied';
  if(command==='get_pending')return [...pending.values()];
  if(command==='cancel')for(const id of args.notifications)pending.delete(id);
  if(command==='batch')for(const notification of args.notifications){
   // Igual que NotificationStorage: las alarmas deben poder reconstruirse desde sourceJson.
   const stored=JSON.parse(notification.sourceJson);
   assert.equal(stored.id,notification.id);pending.set(stored.id,stored);
  }
 };
 const controller=()=>createReminderController({bridge,storage,request:()=>fetcher(),now:()=>now});
 return {controller,pending,calls,setGranted:value=>granted=value,setResponse:value=>response=value,setFetcher:value=>fetcher=value};
}

test('permiso explícito, sincronización idempotente y eliminación de tareas completadas',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');
 assert.equal(f.pending.size,0);assert.ok(!f.calls.includes('request_permission'));
 await c.enable();await Promise.all([c.sync(),c.sync()]);
 assert.equal(f.pending.size,1);
 const alarm=[...f.pending.values()][0];
 assert.equal(alarm.schedule.at.date,'2026-09-25T12:00:00.000Z');
 assert.equal(alarm.visibility,0);
 f.setResponse({status:200,data:{items:[]}});await c.sync();assert.equal(f.pending.size,0);
});
test('denegar permiso no programa alarmas ni activa la preferencia',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');f.setGranted(false);
 await assert.rejects(c.enable(),/permiso/);assert.equal(c.status().enabled,false);assert.equal(f.pending.size,0);
});
test('un fallo de conexión o feed inválido conserva las alarmas existentes',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');await c.enable();
 f.setResponse({status:503});await assert.rejects(c.sync(),/conservan/);assert.equal(f.pending.size,1);
 f.setResponse({status:200,data:{items:[{...item,at:'invalid'}]}});
 await assert.rejects(c.sync(),/no válidos/);assert.equal(f.pending.size,1);
});
test('cerrar sesión invalida una sincronización en vuelo y borra todas las alarmas',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');await c.enable();
 let release,started;const waiting=new Promise(resolve=>started=resolve);
 f.setFetcher(()=>{started();return new Promise(resolve=>release=resolve);});
 const sync=c.sync();await waiting;const stop=c.stop();
 release({status:200,data:{items:[item]}});await Promise.all([sync,stop]);
 assert.equal(f.pending.size,0);assert.equal(c.status().enabled,false);assert.ok(f.calls.includes('remove_active'));
});
test('preferencia persistente y aislamiento al cambiar cuenta o servidor',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');await c.enable();
 const reopened=f.controller();await reopened.attach('server#1');assert.equal(reopened.status().enabled,true);
 await reopened.attach('other-server#1');assert.equal(reopened.status().enabled,false);assert.equal(f.pending.size,0);
 await reopened.enable();await reopened.attach('other-server#2');assert.equal(f.pending.size,0);
});
test('sesión vencida y revocación del permiso cancelan los avisos',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');await c.enable();
 f.setResponse({status:401});await assert.rejects(c.sync(),/sesión/);assert.equal(f.pending.size,0);
 f.setResponse({status:200,data:{items:[item]}});await c.attach('server#1');await c.enable();
 f.setGranted(false);await assert.rejects(c.sync(),/bloqueados/);assert.equal(f.pending.size,0);
});
test('prueba en diez segundos, sin duplicados y cancelable',async()=>{
 const f=fixture(),c=f.controller();await c.attach('server#1');await c.enable();
 await c.test();await c.test();await c.sync();assert.equal(f.pending.size,2);
 assert.ok([...f.pending.values()].some(n=>Date.parse(n.schedule.at.date)===now+10000));
 await c.stop();assert.equal(f.pending.size,0);
});

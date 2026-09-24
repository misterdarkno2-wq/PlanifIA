// El puente nativo conserva las alarmas; este estado solo guarda la preferencia del usuario.
const STORAGE_KEY='planifia-android-reminders';
const TEST_ID=2147483646;
export function createReminderController({bridge,request,storage,now=Date.now,onChange=()=>{}}){
 let state;
 try{state=JSON.parse(storage.getItem(STORAGE_KEY)||'null');}catch{}
 state={owner:'',enabled:false,count:0,lastSync:null,...state,error:''};
 let queue=Promise.resolve(),generation=0;
 const publish=()=>onChange({...state});
 const save=()=>{storage.setItem(STORAGE_KEY,JSON.stringify(state));publish();};
 const native=(command,args={})=>bridge('plugin:notification|'+command,args);
 const serial=operation=>{
  const result=queue.then(operation);
  queue=result.catch(error=>{state.error=String(error?.message||error);publish();});
  return result;
 };
 async function cancel(includeTest=true){
  const pending=await native('get_pending');
  const ids=pending.map(item=>item.id).filter(id=>includeTest||id!==TEST_ID);
  if(ids.length)await native('cancel',{notifications:ids});
 }
 async function clear(){await cancel();await native('remove_active',{notifications:[]});}
 function notification(id,title,body,at){
  const value={id,title,body,icon:'ic_notification',iconColor:'#10796c',visibility:0,
   autoCancel:true,schedule:{at:{date:new Date(at).toISOString(),repeating:false,allowWhileIdle:true}}};
  // Android 2.4 guarda sourceJson para listar, cancelar y restaurar tras un reinicio.
  return {...value,sourceJson:JSON.stringify(value)};
 }
 function prepare(items){
  if(!Array.isArray(items)||items.length>64)throw new Error('El servidor devolvió recordatorios no válidos.');
  const used=new Set([TEST_ID]);
  return items.map(item=>{
   if(typeof item.key!=='string'||typeof item.title!=='string'||typeof item.body!=='string'||!Number.isFinite(Date.parse(item.at)))throw new Error('El servidor devolvió recordatorios no válidos.');
   let id=2166136261;
   for(const character of item.key)id=Math.imul(id^character.charCodeAt(0),16777619);
   id=(id>>>0)%2147483645+1;
   while(used.has(id))id=id%2147483645+1;
   used.add(id);
   return notification(id,item.title,item.body,item.at);
  }).filter(item=>Date.parse(item.schedule.at.date)>now()+2000);
 }
 async function refresh(ticket){
  if(ticket!==generation||!state.enabled||!state.owner)return;
  if(!await native('is_permission_granted')){
   await clear();state.enabled=false;state.count=0;save();
   throw new Error('Los avisos están bloqueados. Actívalos en Ajustes de Android → Aplicaciones → PlanifIA → Notificaciones.');
  }
  const response=await request('/notificaciones/programadas');
  if(ticket!==generation)return;
  if(response.status===401){await clear();state={owner:'',enabled:false,count:0,lastSync:null,error:''};save();throw new Error('Inicia sesión para actualizar los avisos.');}
  if(response.status!==200)throw new Error('No se pudieron actualizar los avisos. Se conservan los últimos sincronizados.');
  const notifications=prepare(response.data?.items);
  await cancel(false);
  if(ticket!==generation)return;
  if(notifications.length)await native('batch',{notifications});
  if(ticket!==generation)return;
  state.count=notifications.length;state.lastSync=new Date(now()).toISOString();state.error='';save();
 }
 return {
  status:()=>({...state}),
  attach(owner){
   const ticket=++generation;
   return serial(async()=>{
    if(ticket!==generation)return;
    if(state.owner!==owner||!state.enabled){
     await clear();state={owner,enabled:false,count:0,lastSync:null,error:''};save();
    }
    await refresh(ticket);
   });
  },
  enable(){
   const ticket=generation;
   return serial(async()=>{
    if(!state.owner)throw new Error('Inicia sesión antes de activar los avisos.');
    const granted=await native('is_permission_granted')||await native('request_permission')==='granted';
    if(ticket!==generation)return;
    if(!granted)throw new Error('No se dio permiso. Puedes activarlo en los ajustes de notificaciones de PlanifIA en Android.');
    state.enabled=true;state.error='';save();await refresh(ticket);
   });
  },
  sync(){const ticket=generation;return serial(()=>refresh(ticket));},
  stop(){
   ++generation;
   // Guardar primero impide reactivar alarmas tras un cierre durante la cancelación.
   state.enabled=false;state.count=0;state.lastSync=null;state.error='';save();
   return serial(async()=>{await clear();state.error='';save();});
  },
  test(){
   const ticket=generation;
   return serial(async()=>{
    if(!state.enabled||!await native('is_permission_granted'))throw new Error('Activa los avisos antes de probarlos.');
    if(ticket!==generation)return;
    await native('batch',{notifications:[notification(TEST_ID,'¡Tus avisos están listos!','PlanifIA te acompañará con recordatorios de tus actividades.',now()+10000)]});
   });
  }
 };
}

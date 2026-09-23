export const isNative=Boolean(globalThis.__TAURI__?.core?.invoke);
export const invoke=(command,args={})=>globalThis.__TAURI__.core.invoke(command,args);

export async function request(path,options={}) {
 if(isNative){
  try{return await invoke('api_request',{path,method:(options.method||'GET').toUpperCase(),body:options.body??null});}
  catch(error){throw new Error(typeof error==='string'?error:'No pudimos conectar con PlanifIA.');}
 }
 let response;
 try{response=await fetch('/api'+path,{...options,credentials:'same-origin',headers:{'Content-Type':'application/json','X-Planifia-Request':'1',...options.headers},body:options.body===undefined?undefined:JSON.stringify(options.body)});}
 catch{throw new Error('No pudimos conectar con PlanifIA. Revisa que el servidor esté iniciado.');}
 return {status:response.status,data:response.status===204?null:await response.json().catch(()=>null)};
}

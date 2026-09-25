export const requestTimeout=path=>path==='/planes/generar'?190000:20000;

export async function fetchJSON(url,options={}, {fetcher=globalThis.fetch,timeoutMs=20000}={}){
 const controller=new AbortController();
 const abort=()=>controller.abort();
 if(options.signal?.aborted)abort();
 else options.signal?.addEventListener('abort',abort,{once:true});
 let timedOut=false;
 const timer=setTimeout(()=>{timedOut=true;abort();},timeoutMs);
 try{
  const response=await fetcher(url,{...options,signal:controller.signal});
  const data=response.status===204?null:await response.json().catch(error=>{
   if(controller.signal.aborted)throw error;
   return null;
  });
  return {status:response.status,data};
 }catch(error){
  if(timedOut)throw new Error('El servidor está tardando demasiado en responder. Vuelve a intentarlo en unos momentos.');
  if(options.signal?.aborted)throw error;
  throw new Error('No pudimos conectar con PlanifIA. Revisa Internet y comprueba que el servidor esté iniciado.');
 }finally{
  clearTimeout(timer);
  options.signal?.removeEventListener('abort',abort);
 }
}

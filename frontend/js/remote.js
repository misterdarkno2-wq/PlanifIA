export function httpsOrigin(value){
 const url=new URL(value.trim());
 if(url.protocol!=='https:'||url.username||url.password||url.pathname!=='/'||url.search||url.hash)throw new Error('Usa solo la dirección HTTPS del servidor, sin /app ni contraseñas.');
 return url.origin;
}

export function remoteConnection(defaultOrigin,{fetcher=globalThis.fetch,session=globalThis.sessionStorage}={}){
 const origin=httpsOrigin(defaultOrigin),key=origin=>'planifia-session:'+origin;
 const server=()=>origin;
 return {
  server,
  async request(path,options={}){
   const origin=server(),token=session.getItem(key(origin));
   const headers={...options.headers,'Content-Type':'application/json','X-Planifia-Request':'1','X-Planifia-Client':'pages'};
   if(token)headers.Authorization='Bearer '+token;
   let response;
   try{response=await fetcher(origin+'/api'+path,{...options,credentials:'omit',headers,body:options.body===undefined?undefined:JSON.stringify(options.body)});}
   catch{throw new Error('No pudimos conectar con PlanifIA. Revisa Internet o vuelve a intentarlo en unos minutos.');}
   const data=response.status===204?null:await response.json().catch(()=>null);
   if(path==='/auth/login'&&response.status===200){
    if(typeof data?.sessionToken!=='string'||!/^[\w-]{32,128}$/.test(data.sessionToken))throw new Error('Actualiza el servidor para habilitar el acceso desde GitHub Pages.');
    session.setItem(key(origin),data.sessionToken);delete data.sessionToken;
   }else if((response.status===401||(path==='/auth/logout'&&response.status===204))&&session.getItem(key(origin))===token){session.removeItem(key(origin));}
   return {status:response.status,data};
  }
 };
}

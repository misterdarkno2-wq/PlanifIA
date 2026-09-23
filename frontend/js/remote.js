export function httpsOrigin(value){
 const url=new URL(value.trim());
 if(url.protocol!=='https:'||url.username||url.password||url.pathname!=='/'||url.search||url.hash)throw new Error('Usa solo la dirección HTTPS del servidor, sin /app ni contraseñas.');
 return url.origin;
}

export function remoteConnection(defaultOrigin,{fetcher=globalThis.fetch,session=globalThis.sessionStorage,settings=globalThis.localStorage}={}){
 const setting='planifia-server',key=origin=>'planifia-session:'+origin;
 const server=()=>httpsOrigin(settings.getItem(setting)||defaultOrigin);
 return {
  server,
  async setServer(value){
   const origin=httpsOrigin(value),response=await fetcher(origin+'/api/health',{credentials:'omit',signal:AbortSignal.timeout(15000)});
   const data=await response.json();
   if(!response.ok||data.estado!=='ok'||data.conexion!=='PyMySQL')throw new Error('El servidor no está listo. Revisa FastAPI y MySQL.');
   const previous=server();
   if(previous!==origin){settings.setItem(setting,origin);session.removeItem(key(previous));session.removeItem(key(origin));}
  },
  async request(path,options={}){
   const origin=server(),token=session.getItem(key(origin));
   const headers={...options.headers,'Content-Type':'application/json','X-Planifia-Request':'1','X-Planifia-Client':'pages'};
   if(token)headers.Authorization='Bearer '+token;
   let response;
   try{response=await fetcher(origin+'/api'+path,{...options,credentials:'omit',headers,body:options.body===undefined?undefined:JSON.stringify(options.body)});}
   catch{throw new Error('No pudimos conectar con tu servidor. Comprueba que el PC y el túnel estén encendidos, o actualiza la dirección en Conexión.');}
   const data=response.status===204?null:await response.json().catch(()=>null);
   if(server()!==origin)throw new Error('El servidor cambió. Vuelve a abrir esta pantalla.');
   if(path==='/auth/login'&&response.status===200){
    if(typeof data?.sessionToken!=='string'||!/^[\w-]{32,128}$/.test(data.sessionToken))throw new Error('Actualiza el servidor para habilitar el acceso desde GitHub Pages.');
    session.setItem(key(origin),data.sessionToken);delete data.sessionToken;
   }else if((response.status===401||(path==='/auth/logout'&&response.status===204))&&session.getItem(key(origin))===token){session.removeItem(key(origin));}
   return {status:response.status,data};
  }
 };
}

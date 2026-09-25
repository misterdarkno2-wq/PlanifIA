import {fetchJSON,requestTimeout} from './http.js';

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
   const {status,data}=await fetchJSON(origin+'/api'+path,{...options,credentials:'omit',headers,body:options.body===undefined?undefined:JSON.stringify(options.body)},{fetcher,timeoutMs:requestTimeout(path)});
   if(path==='/auth/login'&&status===200){
    if(typeof data?.sessionToken!=='string'||!/^[\w-]{32,128}$/.test(data.sessionToken))throw new Error('Actualiza el servidor para habilitar el acceso desde GitHub Pages.');
    session.setItem(key(origin),data.sessionToken);delete data.sessionToken;
   }else if((status===401||(path==='/auth/logout'&&status===204))&&session.getItem(key(origin))===token){session.removeItem(key(origin));}
   return {status,data};
  }
 };
}


"""Inicia FastAPI, crea datos reales, lo reinicia y verifica MySQL y la sesión."""
import sys,subprocess,time,socket,uuid
from pathlib import Path
from datetime import timedelta
import httpx
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.config import local_now
from backend.database import execute

with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
url=f'http://127.0.0.1:{port}'
log=ROOT/'tests'/'reinicio.log'
process=None;uid=None

def start(handle):
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=handle,stderr=handle,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for attempt in range(40):
        try:
            if httpx.get(url+'/api/health',timeout=3).status_code==200:return proc
        except httpx.HTTPError:pass
        if proc.poll() is not None:raise RuntimeError('FastAPI no inició; consulta reinicio.log')
        time.sleep(.5)
    proc.terminate();proc.wait();raise RuntimeError('Tiempo de inicio agotado')

with log.open('w',encoding='utf8') as handle, httpx.Client(base_url=url,headers={'X-Planifia-Request':'1'},timeout=20) as client:
    try:
        process=start(handle)
        account={'nombre':'Prueba de reinicio','correo':f'restart-{uuid.uuid4().hex}@example.com','password':'Prueba-reinicio-123'}
        response=client.post('/api/auth/registro',json=account);response.raise_for_status();uid=response.json()['id']
        client.post('/api/auth/login',json={k:account[k] for k in ('correo','password')}).raise_for_status()
        task={'titulo':'Persistencia tras reiniciar','asignatura':'Historia','fecha_entrega':str(local_now().date()),'tiempo_estimado':60}
        response=client.post('/api/tareas',json=task);response.raise_for_status();tid=response.json()['id']
        exam={'nombre':'Prueba persistente','asignatura':'Matemática','fecha':str(local_now().date()+timedelta(days=1))}
        client.post('/api/evaluaciones',json=exam).raise_for_status()
        ns=client.get('/api/notificaciones').json();nid=ns['items'][0]['id']
        client.patch(f'/api/notificaciones/{nid}/leer').raise_for_status()
        av={'dias':[0,1,2,3,4,5,6],'llegada':'17:00','hasta':'20:00','minutos_diarios':120,'descansos':True}
        client.put('/api/disponibilidad',json=av).raise_for_status()
        process.terminate();process.wait(timeout=15)
        print('FastAPI detenido después de guardar tareas, prueba, disponibilidad y notificaciones.',flush=True)
        process=start(handle)
        assert client.get('/api/auth/me').json()['id']==uid
        assert any(x['id']==tid for x in client.get('/api/tareas').json())
        assert len(client.get('/api/evaluaciones').json())==1
        assert client.get('/api/disponibilidad').json()['minutos_diarios']==120
        assert any(x['id']==nid and x['leida'] for x in client.get('/api/notificaciones').json()['items'])
        print('OK: sesión y datos recuperados desde MySQL después del reinicio.',flush=True)
    finally:
        if process and process.poll() is None:process.terminate();process.wait(timeout=15)
        if uid:execute('DELETE FROM usuarios WHERE id=%s',(uid,))

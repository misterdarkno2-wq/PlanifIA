"""Comprueba Ollama y MySQL con actividades ficticias y elimina su usuario temporal."""
import sys,uuid
from pathlib import Path
from datetime import timedelta
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import httpx
from backend.config import local_now
from backend.database import execute
uid=None
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=200,headers={'X-Planifia-Request':'1'}) as client:
    try:
        data={'nombre':'Prueba IA','correo':f'ollama-{uuid.uuid4().hex}@example.com','password':'Prueba-temporal-123'}
        response=client.post('/api/auth/registro',json=data);response.raise_for_status();uid=response.json()['id']
        client.post('/api/auth/login',json={k:data[k] for k in ('correo','password')}).raise_for_status()
        deadline=str(local_now().date()+timedelta(days=5))
        client.post('/api/tareas',json={'titulo':'Resolver ecuaciones','asignatura':'Matemática','fecha_entrega':deadline,'prioridad':'alta','dificultad':4,'tiempo_estimado':90}).raise_for_status()
        client.post('/api/evaluaciones',json={'nombre':'Prueba de células','asignatura':'Biología','fecha':deadline,'tiempo_estimado':60}).raise_for_status()
        client.put('/api/disponibilidad',json={'dias':list(range(7)),'llegada':'17:00','hasta':'20:00','minutos_diarios':120,'descansos':True}).raise_for_status()
        response=client.post('/api/planes/generar')
        if response.status_code!=201:raise SystemExit('Ollama: '+str(response.json().get('detail')))
        plan=response.json();pid=plan['id']
        client.post(f'/api/planes/{pid}/guardar').raise_for_status()
        stored=client.get(f'/api/planes/{pid}').json()
        assert stored['contenido']==plan['contenido'] and stored['guardado']
        assert any(p['id']==pid for p in client.get('/api/planes').json())
        print(f"OK: {plan['modelo']} genero {len(plan['contenido']['bloques'])} bloques; validacion, guardado e historial comprobados en MySQL.")
    finally:
        if uid:execute('DELETE FROM usuarios WHERE id=%s',(uid,))

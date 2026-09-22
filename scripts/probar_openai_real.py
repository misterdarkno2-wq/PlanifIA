"""Prueba opcional REAL; envía exclusivamente actividades ficticias de prueba a OpenAI.
Puede consumir cuota de tu cuenta. No fabrica un plan si la API falla.
"""
import sys,uuid
from pathlib import Path
from datetime import timedelta
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import local_now
from backend.database import execute
from backend.services.openai_service import credentials
if not credentials()[0]:raise SystemExit('PENDIENTE: configura OPENAI_API_KEY en .env.')
uid=None
with TestClient(app,headers={'X-Planifia-Request':'1'}) as client:
    try:
        data={'nombre':'Prueba IA','correo':f'openai-{uuid.uuid4().hex}@example.com','password':'Prueba-temporal-123'}
        response=client.post('/api/auth/registro',json=data);response.raise_for_status();uid=response.json()['id']
        client.post('/api/auth/login',json={k:data[k] for k in ('correo','password')}).raise_for_status()
        deadline=str(local_now().date()+timedelta(days=5))
        client.post('/api/tareas',json={'titulo':'Resolver ecuaciones','asignatura':'Matemática','fecha_entrega':deadline,'prioridad':'alta','dificultad':4,'tiempo_estimado':90}).raise_for_status()
        client.post('/api/evaluaciones',json={'nombre':'Prueba de células','asignatura':'Biología','fecha':deadline,'tiempo_estimado':60}).raise_for_status()
        client.put('/api/disponibilidad',json={'dias':list(range(7)),'llegada':'17:00','hasta':'20:00','minutos_diarios':120,'descansos':True}).raise_for_status()
        response=client.post('/api/planes/generar')
        if response.status_code!=201:raise SystemExit('OpenAI: '+str(response.json().get('detail')))
        plan=response.json();pid=plan['id']
        client.post(f'/api/planes/{pid}/guardar').raise_for_status()
        stored=client.get(f'/api/planes/{pid}').json()
        assert stored['contenido']==plan['contenido'] and stored['guardado']
        assert any(p['id']==pid for p in client.get('/api/planes').json())
        out=ROOT/'docs'/'PRUEBA_OPENAI_REAL.md'
        out.write_text('# Prueba real de OpenAI\n\nEstado: APROBADA\n\nFecha: '+str(local_now())+'\n\nModelo: '+plan['modelo']+'\n\nGeneración, validación, guardado y recuperación comprobados con MySQL real.\n\n```json\n'+__import__('json').dumps(plan['contenido'],ensure_ascii=False,indent=2)+'\n```\n',encoding='utf8')
        print('OK: OpenAI generó el plan; se validó, guardó y recuperó desde MySQL.')
        print('Evidencia: docs/PRUEBA_OPENAI_REAL.md')
    finally:
        if uid:execute('DELETE FROM usuarios WHERE id=%s',(uid,))


"""Pruebas contra MySQL real configurado en .env; solo elimina usuarios creados por esta prueba."""
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import local_now
from backend.database import query,execute
HEADERS={'X-Planifia-Request':'1','Origin':'http://127.0.0.1:8000'}

@pytest.fixture
def clients():
    a=TestClient(app,headers=HEADERS);b=TestClient(app,headers=HEADERS)
    accounts=[]
    try:
        for client in (a,b):
            payload={'nombre':'Estudiante de prueba','correo':f'test-{uuid.uuid4().hex}@example.com','password':'Prueba-segura-123'}
            response=client.post('/api/auth/registro',json=payload)
            assert response.status_code==201,response.text
            accounts.append((response.json()['id'],payload))
            assert client.post('/api/auth/login',json={k:payload[k] for k in ('correo','password')}).status_code==200
        yield a,b,accounts
    finally:
        try:
            for uid,_ in accounts: execute('DELETE FROM usuarios WHERE id=%s',(uid,))
        finally:
            a.close();b.close()

def test_flujo_mysql_completo(clients):
    a,b,accounts=clients
    health=a.get('/api/health')
    assert health.status_code==200,health.text
    assert health.json()['estado']=='ok'
    assert a.post('/api/auth/registro',json=accounts[0][1]).status_code==409
    assert a.post('/api/auth/login',json={'correo':accounts[0][1]['correo'],'password':'incorrecta'}).status_code==401
    stored=query('SELECT password_hash FROM usuarios WHERE id=%s',(accounts[0][0],),one=True)
    assert stored['password_hash'].startswith('$argon2id$')
    assert 'HttpOnly' in a.post('/api/auth/login',json={k:accounts[0][1][k] for k in ('correo','password')}).headers['set-cookie']
    task={'titulo':"Historia ' OR 1=1 --",'asignatura':'Historia','descripcion':'Trabajo','fecha_entrega':str(local_now().date()),'prioridad':'alta','dificultad':4,'tiempo_estimado':90}
    created=a.post('/api/tareas',json=task); assert created.status_code==201,created.text
    tid=created.json()['id']
    assert b.get('/api/tareas').json()==[]
    assert b.put(f'/api/tareas/{tid}',json=task).status_code==404
    assert b.delete(f'/api/tareas/{tid}').status_code==404
    assert b.patch(f'/api/tareas/{tid}/estado',json={'estado':'completada'}).status_code==404
    task['titulo']='Historia editada'
    assert a.put(f'/api/tareas/{tid}',json=task).status_code==200
    assert query('SELECT titulo FROM tareas WHERE id=%s',(tid,),one=True)['titulo']=='Historia editada'
    ns=a.get('/api/notificaciones').json(); assert ns['no_leidas']==1
    nid=ns['items'][0]['id']
    assert a.get('/api/notificaciones').json()['no_leidas']==1
    assert b.get('/api/notificaciones').json()['items']==[]
    assert b.patch(f'/api/notificaciones/{nid}/leer').status_code==404
    assert a.patch(f'/api/notificaciones/{nid}/leer').status_code==200
    assert a.get('/api/notificaciones').json()['no_leidas']==0
    assert a.patch(f'/api/tareas/{tid}/estado',json={'estado':'completada'}).status_code==200
    assert a.get('/api/dashboard').json()['pendientes']==0
    assert a.get('/api/notificaciones').json()['items']==[]
    exam={'nombre':'Prueba álgebra','asignatura':'Matemática','fecha':str(local_now().date()+timedelta(days=1)),'prioridad':'alta','dificultad':5,'descripcion':'Ecuaciones','tiempo_estimado':120}
    er=a.post('/api/evaluaciones',json=exam);assert er.status_code==201,er.text
    eid=er.json()['id'];exam['nombre']='Prueba editada'
    assert a.put(f'/api/evaluaciones/{eid}',json=exam).status_code==200
    assert b.put(f'/api/evaluaciones/{eid}',json=exam).status_code==404
    assert b.delete(f'/api/evaluaciones/{eid}').status_code==404
    assert b.get('/api/evaluaciones').json()==[]
    assert a.get('/api/dashboard').json()['pruebas_semana']==1
    assert a.get('/api/notificaciones').json()['no_leidas']==1
    assert a.post('/api/tareas',json={}).status_code==422
    assert a.post('/api/tareas',json={**task,'fecha_entrega':'2026-02-30'}).status_code==422
    assert a.post('/api/evaluaciones',json={**exam,'fecha':'no-fecha'}).status_code==422
    assert a.post('/api/tareas',json={**task,'tiempo_estimado':-1}).status_code==422
    assert a.post('/api/tareas',json=task,headers={'Origin':'https://otro-sitio.com'}).status_code==403
    assert a.delete(f'/api/evaluaciones/{eid}').status_code==204
    assert a.delete(f'/api/tareas/{tid}').status_code==204
    assert a.get('/api/tareas').json()==[]
    assert a.post('/api/auth/logout').status_code==204
    assert a.get('/api/auth/me').status_code==401

def test_mysql_falla_sin_exponer_credenciales(monkeypatch):
    from backend.config import DB
    monkeypatch.setitem(DB,'port',1)
    with TestClient(app) as client:
        response=client.get('/api/health')
        assert response.status_code==503
        assert 'password' not in response.text.lower()


def test_disponibilidad_planes_y_aislamiento(clients,monkeypatch):
    # Fixture sintética para probar el contrato de persistencia, no generación Ollama.
    import json
    from backend.services import ollama_service
    a,b,accounts=clients
    av={'dias':list(range(7)),'llegada':'17:00','hasta':'20:00','minutos_diarios':120,'descansos':True,'asignaturas_dificiles':'Matemática'}
    assert a.put('/api/disponibilidad',json={**av,'dias':[]}).status_code==422
    assert a.put('/api/disponibilidad',json={**av,'hasta':'16:00'}).status_code==422
    assert a.put('/api/disponibilidad',json={**av,'dias':[1,1]}).status_code==422
    assert a.put('/api/disponibilidad',json=av).status_code==200
    assert a.get('/api/disponibilidad').json()['minutos_diarios']==120
    assert b.get('/api/disponibilidad').json() is None
    from fastapi import HTTPException
    def unavailable(*args): raise HTTPException(503,'Ollama no disponible')
    monkeypatch.setattr(ollama_service,'generate',unavailable)
    assert a.post('/api/planes/generar').status_code==503
    assert a.get('/api/planes').json()==[]
    today=str(local_now().date())
    content={'resumen':'Fixture de prueba de almacenamiento','bloques':[{'fecha':today,'inicio':'00:00:00','fin':'00:30:00','tipo':'tarea','actividad_id':1,'asignatura':'Prueba','actividad':'Fixture'}],'advertencias':[]}
    pid=execute('INSERT INTO planes_estudio (usuario_id,contenido,modelo) VALUES (%s,%s,%s)',(accounts[0][0],json.dumps(content),'fixture-sin-generacion'))
    assert b.get(f'/api/planes/{pid}').status_code==404
    assert b.post(f'/api/planes/{pid}/guardar').status_code==404
    assert a.post(f'/api/planes/{pid}/guardar').status_code==200
    assert a.get(f'/api/planes/{pid}').json()['contenido']==content
    assert a.get('/api/planes').json()[0]['id']==pid
    assert b.get('/api/planes').json()==[]
    notifications=a.get('/api/notificaciones').json()
    assert any(n['tipo']=='plan' for n in notifications['items'])
    assert a.post(f'/api/planes/{pid}/guardar').status_code==200
    assert len(a.get('/api/notificaciones').json()['items'])==len(notifications['items'])

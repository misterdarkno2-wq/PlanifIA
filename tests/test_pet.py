from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import uuid

import pymysql
import pytest
from fastapi.testclient import TestClient
from backend import pet_config
from backend.config import local_now
from backend.database import execute, query
from backend.main import app
from backend.models.schemas import Estado
from backend.routes import tareas
from backend.services.pet_service import progression, reward


@pytest.mark.parametrize('priority,base',[('baja',10),('media',20),('alta',35)])
@pytest.mark.parametrize('offset,bonus',[(-1,0),(0,0),(1,5)])
def test_reward(priority,base,offset,bonus):
    today=date(2026,9,22)
    assert reward(priority,today+timedelta(days=offset),today)==base+bonus


def test_all_level_boundaries_and_evolutions():
    threshold=0
    for level in range(1,21):
        p=progression(threshold)
        assert p['currentLevel']==level
        assert p['levelXp']==0
        assert p['evolutionStage']==sum(level>=minimum for minimum,_ in pet_config.STAGES)
        if level>1:assert progression(threshold-1)['currentLevel']==level-1
        if level<20:
            assert p['nextLevelXp']==50+15*(level-1)
            threshold+=p['nextLevelXp']
    assert progression(100000)['currentLevel']==20
    assert progression(100000)['nextLevelXp'] is None


@pytest.fixture
def account():
    # Sesión temporal real, sin consumir el límite de intentos de registro.
    from backend.security import token_hash
    token=uuid.uuid4().hex
    uid=execute('INSERT INTO usuarios (nombre,correo,password_hash) VALUES (%s,%s,%s)',
                ('Prueba mascota',f'pet-{uuid.uuid4().hex}@example.com','test-no-login'))
    try:
        execute('INSERT INTO sesiones (token_hash,usuario_id,expira) VALUES (%s,%s,DATE_ADD(UTC_TIMESTAMP(),INTERVAL 1 HOUR))',(token_hash(token),uid))
        with TestClient(app,headers={'X-Planifia-Request':'1','Origin':'http://127.0.0.1:8000'}) as client:
            client.cookies.set('planifia_session',token)
            yield client,uid
    finally:
        execute('DELETE FROM usuarios WHERE id=%s',(uid,))


def task(client,**changes):
    data={'titulo':'Practicar álgebra','asignatura':'Matemática','fecha_entrega':str(local_now().date()+timedelta(days=2)),
          'prioridad':'alta','dificultad':3,'tiempo_estimado':30,**changes}
    response=client.post('/api/tareas',json=data)
    assert response.status_code==201,response.text
    return response.json()['id'],data


def toggle(client,tid,state):
    response=client.patch(f'/api/tareas/{tid}/estado',json={'estado':state})
    assert response.status_code==200,response.text
    return response.json()


def test_reward_reopen_retry_and_frozen_amount(account):
    client,uid=account
    assert client.get('/api/mascota').json()['totalXp']==0
    tid,data=task(client)
    first=toggle(client,tid,'completada')
    assert first['xpDelta']==40 and first['pet']['totalXp']==40
    assert toggle(client,tid,'completada')['xpDelta']==0
    assert toggle(client,tid,'pendiente')['xpDelta']==-40
    row=query('SELECT * FROM tareas WHERE id=%s',(tid,),one=True)
    assert row['xp_otorgada']==40 and not row['xp_activa']
    assert row['xp_otorgada_en'] and row['xp_revocada_en']
    assert toggle(client,tid,'pendiente')['xpDelta']==0
    assert client.put(f'/api/tareas/{tid}',json={**data,'prioridad':'baja','estado':'pendiente'}).status_code==200
    assert toggle(client,tid,'completada')['xpDelta']==40
    assert client.get('/api/mascota').json()['totalXp']==40
    assert client.delete(f'/api/tareas/{tid}').status_code==204
    assert client.get('/api/mascota').json()['totalXp']==0


def test_put_creation_and_client_cannot_grant_xp(account):
    client,uid=account
    tid,data=task(client,estado='completada')
    assert client.get('/api/mascota').json()['totalXp']==0
    assert toggle(client,tid,'completada')['xpDelta']==0
    toggle(client,tid,'pendiente')
    result=client.put(f'/api/tareas/{tid}',json={**data,'estado':'completada'}).json()
    assert result['xpDelta']==40
    assert client.put(f'/api/tareas/{tid}',json=data).json()['xpDelta']==0
    assert client.patch(f'/api/tareas/{tid}/estado',json={'estado':'completada','xp_otorgada':9000}).status_code==422
    result=client.put(f'/api/tareas/{tid}',json={**data,'estado':'pendiente'}).json()
    assert result['xpDelta']==-40
    with TestClient(app) as anonymous:
        assert anonymous.get('/api/mascota').status_code==401


def test_concurrent_requests_same_and_different_tasks(account):
    client,uid=account
    tid,_=task(client)
    other,_=task(client,prioridad='media')
    def complete(item):return tareas.estado(item,Estado(estado='completada'),user={'id':uid})
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(complete,[tid,tid,other,other]))
    assert sorted(r['xpDelta'] for r in results)==[0,0,25,40]
    assert client.get('/api/mascota').json()['totalXp']==65
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:tareas.estado(tid,Estado(estado='pendiente'),user={'id':uid}),range(2)))
    assert sorted(r['xpDelta'] for r in results)==[-40,0]
    assert client.get('/api/mascota').json()['totalXp']==25


def test_failure_rolls_back_task_and_xp(account,monkeypatch):
    client,uid=account
    tid,_=task(client)
    original=tareas.apply_transition
    def fail(*args):
        original(*args)
        raise pymysql.err.OperationalError(2013,'fallo de prueba')
    monkeypatch.setattr(tareas,'apply_transition',fail)
    assert client.patch(f'/api/tareas/{tid}/estado',json={'estado':'completada'}).status_code==503
    row=query('SELECT * FROM tareas WHERE id=%s',(tid,),one=True)
    assert row['estado']=='pendiente' and row['xp_otorgada']==0 and not row['xp_activa']
    assert client.get('/api/mascota').json()['totalXp']==0


def test_many_levels_and_stages_in_one_transition(account,monkeypatch):
    client,uid=account
    monkeypatch.setitem(pet_config.BASE_XP,'alta',10000)
    tid,_=task(client)
    result=toggle(client,tid,'completada')
    assert result['levelsGained']==list(range(2,21))
    assert result['stagesGained']==[2,3,4,5]
    assert result['pet']['currentLevel']==20 and result['pet']['evolutionStage']==5
    assert client.get('/api/mascota').json()['totalXp']==10005
    assert toggle(client,tid,'pendiente')['pet']['currentLevel']==1

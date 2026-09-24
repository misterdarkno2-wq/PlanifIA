
"""Contratos y fallos controlados. No sustituyen la prueba real contra Ollama."""
import copy
import json as jsonlib
from datetime import datetime,date
import httpx
import pytest
from fastapi import HTTPException
from backend.models.schemas import Disponibilidad
from backend.services import ollama_service as service

AV=Disponibilidad(dias=list(range(7)),llegada='17:00',hasta='20:00',minutos_diarios=120,descansos=True)
NOW=datetime(2026,9,11,10)
TASKS=[{'id':1,'titulo':'Ecuaciones','asignatura':'Matemática','fecha_entrega':date(2026,9,15),'dificultad':4,'prioridad':'alta','tiempo_estimado':90}]
VALID={'resumen':'Plan de prueba del contrato','bloques':[{'fecha':'2026-09-11','inicio':'17:00','fin':'17:45','tipo':'tarea','actividad_id':1,'asignatura':'Matemática','actividad':'Resolver ejercicios'}],'advertencias':[]}

def test_contrato_valido_y_carga_pendiente():
    result=service.validate_plan(VALID,AV,TASKS,[],NOW)
    assert len(result['bloques'])==1
    assert 'pendiente' in result['advertencias'][0]

@pytest.mark.parametrize('patch',[
    {'inicio':'16:00'},{'fin':'20:30'},{'fecha':'2026-09-10'},{'fecha':'2026-09-17'},
    {'actividad_id':999},{'fin':'17:00'},{'fin':'18:00'},{'asignatura':'Otra'},
    {'inicio':'17:00:30'},{'inicio':'17:00:00-03:00'},{'tipo':'descanso','actividad_id':1}])
def test_rechaza_plan_invalido(patch):
    bad=copy.deepcopy(VALID);bad['bloques'][0].update(patch)
    with pytest.raises(ValueError):service.validate_plan(bad,AV,TASKS,[],NOW)

def test_rechaza_solapamiento_y_pausas_cortas():
    bad=copy.deepcopy(VALID);bad['bloques'].append({**bad['bloques'][0],'inicio':'17:30','fin':'18:00'})
    with pytest.raises(ValueError):service.validate_plan(bad,AV,TASKS,[],NOW)
    bad['bloques'][1].update(inicio='17:50',fin='18:20')
    with pytest.raises(ValueError):service.validate_plan(bad,AV,TASKS,[],NOW)


def test_descansos_validos_entre_tres_bloques():
    plan=copy.deepcopy(VALID)
    plan['bloques']=[
        {**VALID['bloques'][0],'inicio':'17:00','fin':'17:30'},
        {'fecha':'2026-09-11','inicio':'17:30','fin':'17:40','tipo':'descanso','actividad_id':None,'asignatura':'','actividad':'Pausa'},
        {**VALID['bloques'][0],'inicio':'17:40','fin':'18:10'},
        {'fecha':'2026-09-11','inicio':'18:10','fin':'18:20','tipo':'descanso','actividad_id':None,'asignatura':'','actividad':'Pausa'},
        {**VALID['bloques'][0],'inicio':'18:20','fin':'18:50'},
    ]
    assert len(service.validate_plan(plan,AV,TASKS,[],NOW)['bloques'])==5

@pytest.fixture
def local_model(monkeypatch):
    monkeypatch.setattr(service,'MODEL','qwen3.5:9b')
    monkeypatch.setattr(service,'local_now',lambda:NOW)


def test_api_local_y_plan_valido(monkeypatch,local_model):
    def post(self,url,json):
        assert url=='http://127.0.0.1:11434/api/chat'
        assert json['model']=='qwen3.5:9b'
        assert json['stream'] is False and json['think'] is False
        assert json['format']['properties']['objetivos']['minItems']==2
        assert json['options']['num_ctx']==16384
        assert 'Ecuaciones' in json['messages'][1]['content']
        payload={'done':True,'done_reason':'stop','message':{'content':jsonlib.dumps({'resumen':'Plan local','objetivos':['Resolver ecuaciones','Corregir ejercicios']})}}
        return httpx.Response(200,json=payload,request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client,'post',post)
    plan,model=service.generate(AV,TASKS,[])
    assert model=='qwen3.5:9b'
    assert plan['bloques'][0]['actividad_id']==1


@pytest.mark.parametrize('status',[400,404,429,500])
def test_errores_http_controlados(monkeypatch,local_model,status):
    def post(*args,**kwargs):return httpx.Response(status,request=httpx.Request('POST',service.ENDPOINT))
    monkeypatch.setattr(httpx.Client,'post',post)
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==503
    if status==404:assert 'ollama pull qwen3.5:9b' in error.value.detail


@pytest.mark.parametrize('payload',[None,[],{},
    {'done':False,'message':{'content':jsonlib.dumps(VALID)}},
    {'done':True,'done_reason':'length','message':{'content':jsonlib.dumps(VALID)}},
    {'done':True,'done_reason':'stop','message':{'content':''}},
    {'done':True,'done_reason':'stop','message':{'content':None}},
    {'done':True,'done_reason':'stop','message':{'content':'no es JSON'}},
    {'done':True,'done_reason':'stop','message':{'content':jsonlib.dumps({**VALID,'bloques':[]})}},
])
def test_respuesta_inesperada(monkeypatch,local_model,payload):
    monkeypatch.setattr(httpx.Client,'post',lambda *a,**kw:httpx.Response(200,json=payload,request=httpx.Request('POST',service.ENDPOINT)))
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==502


@pytest.mark.parametrize('exception,expected',[(httpx.ReadTimeout,504),(httpx.ConnectError,503)])
def test_timeout_y_sin_conexion(monkeypatch,local_model,exception,expected):
    def fail(*a,**kw):raise exception('fallo inducido')
    monkeypatch.setattr(httpx.Client,'post',fail)
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==expected


def test_sin_actividades_no_llama_al_modelo(monkeypatch,local_model):
    def unexpected(*a,**kw):pytest.fail('No debe llamar a Ollama')
    monkeypatch.setattr(httpx.Client,'post',unexpected)
    with pytest.raises(HTTPException) as error:service.generate(AV,[],[])
    assert error.value.status_code==422


@pytest.mark.parametrize('rests',[True,False])
def test_horarios_respetan_presupuesto_plazos_y_duracion(rests):
    av=AV.model_copy(update={'descansos':rests})
    exam={'id':1,'nombre':'Celulas','asignatura':'Biología','fecha':date(2026,9,15),'tiempo_estimado':60}
    blocks=service.schedule(av,TASKS,[exam],NOW)
    plan=service.validate_plan({'resumen':'Plan','bloques':blocks,'advertencias':[]},av,TASKS,[exam],NOW)
    assert plan['advertencias']==[]
    totals={}
    for b in blocks:
        if b['tipo']=='descanso':continue
        duration=service.minute(datetime.strptime(b['fin'],'%H:%M').time())-service.minute(datetime.strptime(b['inicio'],'%H:%M').time())
        key=(b['tipo'],b['actividad_id'])
        totals[key]=totals.get(key,0)+duration
    assert totals=={('tarea',1):90,('evaluacion',1):60}
    for day in {b['fecha'] for b in blocks}:
        assert [b for b in blocks if b['fecha']==day][-1]['tipo']!='descanso'


def test_no_planifica_en_el_pasado_y_avisa_carga_pendiente():
    now=NOW.replace(hour=19,minute=55)
    task={**TASKS[0],'fecha_entrega':NOW.date()}
    blocks=service.schedule(AV,[task],[],now)
    plan=service.validate_plan({'resumen':'Plan','bloques':blocks,'advertencias':[]},AV,[task],[],now)
    assert blocks[0]['inicio']=='19:56'
    assert 'pendiente' in plan['advertencias'][0]
    with pytest.raises(HTTPException) as error:service.schedule(AV,[task],[],now.replace(hour=20))
    assert error.value.status_code==422


def test_exceso_de_texto_no_llama_a_ollama(monkeypatch,local_model):
    def unexpected(*a,**kw):pytest.fail('No debe llamar a Ollama')
    monkeypatch.setattr(httpx.Client,'post',unexpected)
    tasks=[{**TASKS[0],'descripcion':'a'*12000}]
    with pytest.raises(HTTPException) as error:service.generate(AV,tasks,[])
    assert error.value.status_code==422


"""Contratos y fallos controlados. No sustituyen la prueba real contra OpenAI."""
import copy
import json as jsonlib
from datetime import datetime,date
import httpx
import pytest
from fastapi import HTTPException
from backend.models.schemas import Disponibilidad
from backend.services import openai_service as service

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
    {'inicio':'17:00:30'},{'tipo':'descanso','actividad_id':1}])
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

def test_sin_clave(monkeypatch):
    monkeypatch.setattr(service,'credentials',lambda:('','modelo-de-prueba'))
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==503
    assert 'OPENAI_API_KEY' in error.value.detail


def test_responses_api_y_plan_valido(monkeypatch):
    monkeypatch.setattr(service,'credentials',lambda:('clave-ficticia-solo-test','gpt-4o-mini'))
    monkeypatch.setattr(service,'local_now',lambda:NOW)
    def post(self,url,headers,json):
        assert url==service.ENDPOINT
        assert headers['Authorization']=='Bearer clave-ficticia-solo-test'
        assert json['store'] is False
        assert json['text']['format']['type']=='json_schema'
        assert json['text']['format']['strict'] is True
        assert json['model']=='gpt-4o-mini'
        assert 'Ecuaciones' in json['input']
        payload={'status':'completed','output':[{'type':'reasoning'},
            {'type':'message','content':[{'type':'output_text','text':jsonlib.dumps(VALID)}]}]}
        return httpx.Response(200,json=payload,request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client,'post',post)
    plan,model=service.generate(AV,TASKS,[])
    assert model=='gpt-4o-mini'
    assert plan['bloques'][0]['actividad_id']==1

@pytest.mark.parametrize('status,expected',[(401,502),(403,502),(402,503),(429,503),(404,502),(422,502),(500,503)])
def test_errores_http_controlados(monkeypatch,status,expected):
    monkeypatch.setattr(service,'credentials',lambda:('clave-ficticia-solo-test','modelo-de-prueba'))
    monkeypatch.setattr(service,'local_now',lambda:NOW)
    def post(*args,**kwargs):return httpx.Response(status,request=httpx.Request('POST',service.ENDPOINT))
    monkeypatch.setattr(httpx.Client,'post',post)
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==expected
    assert 'clave-ficticia' not in error.value.detail

@pytest.mark.parametrize('payload',[{}, {'status':'incomplete','output':[]},
    {'status':'completed','output':[]},
    {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'No'}]}]},
    {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'esto no es JSON'}]}]}])
def test_respuesta_inesperada(monkeypatch,payload):
    monkeypatch.setattr(service,'credentials',lambda:('clave-ficticia-solo-test','modelo-de-prueba'))
    monkeypatch.setattr(service,'local_now',lambda:NOW)
    monkeypatch.setattr(httpx.Client,'post',lambda *a,**kw:httpx.Response(200,json=payload,request=httpx.Request('POST',service.ENDPOINT)))
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==502

@pytest.mark.parametrize('exception,expected',[(httpx.ReadTimeout,504),(httpx.ConnectError,503)])
def test_timeout_y_sin_conexion(monkeypatch,exception,expected):
    monkeypatch.setattr(service,'credentials',lambda:('clave-ficticia-solo-test','modelo-de-prueba'))
    monkeypatch.setattr(service,'local_now',lambda:NOW)
    def fail(*a,**kw):raise exception('fallo inducido')
    monkeypatch.setattr(httpx.Client,'post',fail)
    with pytest.raises(HTTPException) as error:service.generate(AV,TASKS,[])
    assert error.value.status_code==expected

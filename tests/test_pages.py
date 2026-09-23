import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from backend import main
from backend.routes import auth
from backend.database import execute, query
from backend.security import token_hash

ORIGIN = 'https://pages.example.com'

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, 'WEB_ORIGINS', (ORIGIN,))
    monkeypatch.setattr(auth, 'WEB_ORIGINS', (ORIGIN,))
    app = CORSMiddleware(main.app, allow_origins=[ORIGIN],
        allow_methods=['GET','POST','PUT','PATCH','DELETE'],
        allow_headers=['Content-Type','Authorization','X-Planifia-Request','X-Planifia-Client'])
    with TestClient(app, headers={'Origin': ORIGIN, 'X-Planifia-Request':'1', 'X-Planifia-Client':'pages'}) as client:
        yield client

def test_pages_token_session_and_revocation(client):
    payload = {'nombre':'Prueba Pages', 'correo':f'pages-{uuid.uuid4().hex}@example.com', 'password':'Temporal-Pages-123'}
    response = client.post('/api/auth/registro', json=payload)
    assert response.status_code == 201
    uid = response.json()['id']
    try:
        response = client.post('/api/auth/login', json={k:payload[k] for k in ('correo','password')})
        assert response.status_code == 200
        assert response.headers['access-control-allow-origin'] == ORIGIN
        assert 'set-cookie' not in response.headers
        token = response.json()['sessionToken']
        assert query('SELECT token_hash FROM sesiones WHERE usuario_id=%s', (uid,), one=True)['token_hash'] == token_hash(token)
        assert client.get('/api/auth/me').status_code == 401
        client.headers['Authorization'] = 'Bearer '+token
        assert client.get('/api/auth/me').json()['id'] == uid
        assert client.get('/api/mascota').json()['totalXp'] == 0
        assert client.post('/api/auth/logout').status_code == 204
        assert client.get('/api/auth/me').status_code == 401
        assert not query('SELECT token_hash FROM sesiones WHERE usuario_id=%s', (uid,))
    finally:
        execute('DELETE FROM usuarios WHERE id=%s', (uid,))

def test_pages_cors_and_origin_validation(client):
    headers = {'Access-Control-Request-Method':'POST',
        'Access-Control-Request-Headers':'content-type,x-planifia-request,x-planifia-client,authorization'}
    response = client.options('/api/auth/login', headers=headers)
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == ORIGIN
    assert 'access-control-allow-credentials' not in response.headers
    bad = client.options('/api/auth/login', headers={**headers,'Origin':'https://attacker.example'})
    assert bad.status_code == 400
    assert 'access-control-allow-origin' not in bad.headers
    login = {'correo':'test@example.com','password':'Password123'}
    assert client.post('/api/auth/login', json=login, headers={'Origin':'https://attacker.example'}).status_code == 403
    client.headers.pop('Origin')
    assert client.post('/api/auth/login', json=login).status_code == 403

def test_malformed_bearer_is_not_accepted(client):
    for value in ['Basic secret', 'Bearer ', 'Bearer '+'x'*129]:
        assert client.get('/api/auth/me', headers={'Authorization':value}).status_code == 401

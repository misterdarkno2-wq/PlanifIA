import hashlib
from fastapi import Request, HTTPException
from argon2 import PasswordHasher
from backend.database import query
hasher = PasswordHasher()
DUMMY_HASH = hasher.hash('password-no-existente-aleatoria')

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def session_token(request: Request):
    authorization = request.headers.get('Authorization', '')
    if authorization:
        scheme, _, token = authorization.partition(' ')
        if scheme.lower() != 'bearer' or not token or len(token) > 128:
            raise HTTPException(401, 'Sesión no válida.')
        return token
    return request.cookies.get('planifia_session', '')

def usuario_actual(request: Request):
    token = session_token(request)
    if not token: raise HTTPException(401, 'Inicia sesión para continuar.')
    user = query('SELECT u.id,u.nombre,u.correo FROM sesiones s JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=%s AND s.expira>UTC_TIMESTAMP()', (token_hash(token),), one=True)
    if not user: raise HTTPException(401, 'Tu sesión terminó. Vuelve a ingresar.')
    return user

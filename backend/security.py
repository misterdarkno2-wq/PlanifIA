import hashlib
from fastapi import Request, HTTPException
from argon2 import PasswordHasher
from backend.database import query
hasher = PasswordHasher()
DUMMY_HASH = hasher.hash('password-no-existente-aleatoria')

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def usuario_actual(request: Request):
    token = request.cookies.get('planifia_session', '')
    if not token: raise HTTPException(401, 'Inicia sesión para continuar.')
    user = query('SELECT u.id,u.nombre,u.correo FROM sesiones s JOIN usuarios u ON u.id=s.usuario_id WHERE s.token_hash=%s AND s.expira>UTC_TIMESTAMP()', (token_hash(token),), one=True)
    if not user: raise HTTPException(401, 'Tu sesión terminó. Vuelve a ingresar.')
    return user

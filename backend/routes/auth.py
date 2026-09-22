import secrets
from datetime import datetime, timedelta, timezone
import pymysql
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from backend.models.schemas import Registro, Login
from backend.database import execute, query, transaction
from backend.security import hasher, DUMMY_HASH, token_hash, usuario_actual
from backend.config import COOKIE_SECURE
router=APIRouter(prefix='/api/auth', tags=['Autenticación'])

@router.post('/registro', status_code=201)
def registro(data: Registro):
    try:
        uid=execute('INSERT INTO usuarios (nombre,correo,password_hash) VALUES (%s,%s,%s)',
            (data.nombre,str(data.correo).lower(),hasher.hash(data.password)))
    except pymysql.err.IntegrityError as error:
        if error.args[0] == 1062: raise HTTPException(409,'Este correo ya está registrado.')
        raise
    return {'id':uid,'mensaje':'Cuenta creada. Ya puedes iniciar sesión.'}

@router.post('/login')
def login(data: Login, request: Request, response: Response):
    user=query('SELECT id,nombre,correo,password_hash FROM usuarios WHERE correo=%s',(str(data.correo).lower(),),one=True)
    try: hasher.verify(user['password_hash'] if user else DUMMY_HASH, data.password)
    except VerificationError: raise HTTPException(401,'Correo o contraseña incorrectos.')
    if not user: raise HTTPException(401,'Correo o contraseña incorrectos.')
    token=secrets.token_urlsafe(32)
    expiry=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(days=7)
    with transaction() as cur:
        cur.execute('DELETE FROM sesiones WHERE expira<UTC_TIMESTAMP() OR token_hash=%s',(token_hash(request.cookies.get('planifia_session','')),))
        cur.execute('INSERT INTO sesiones (token_hash,usuario_id,expira) VALUES (%s,%s,%s)',(token_hash(token),user['id'],expiry))
    response.set_cookie('planifia_session',token,httponly=True,secure=COOKIE_SECURE,samesite='strict',max_age=604800,path='/')
    return {k:user[k] for k in ('id','nombre','correo')}

@router.get('/me')
def me(user=Depends(usuario_actual)): return user

@router.post('/logout',status_code=204)
def logout(request: Request,response: Response):
    execute('DELETE FROM sesiones WHERE token_hash=%s',(token_hash(request.cookies.get('planifia_session','')),))
    response.delete_cookie('planifia_session',path='/',secure=COOKIE_SECURE,httponly=True,samesite='strict')

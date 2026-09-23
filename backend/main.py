import logging
import time
from collections import defaultdict, deque
from threading import Lock
import pymysql
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from backend.config import ROOT, ORIGIN
from backend.database import transaction, check_schema
from backend.routes import auth, tareas, evaluaciones, dashboard, notificaciones, planificacion, mascota
app=FastAPI(title='PlanifIA',version='1.0.0')
log=logging.getLogger('planifia')
_attempts=defaultdict(deque)
_lock=Lock()

@app.middleware('http')
async def protections(request:Request, call_next):
    if request.url.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE'):
        if request.headers.get('Origin') not in (None,ORIGIN):
            return JSONResponse({'detail':'Origen no permitido.'},status_code=403)
        if request.headers.get('X-Planifia-Request') != '1':
            return JSONResponse({'detail':'Solicitud no válida.'},status_code=403)
    if request.url.path in ('/api/auth/login','/api/auth/registro') and request.method=='POST':
        key=request.client.host if request.client else 'unknown'
        now=time.monotonic()
        with _lock:
            # Limpieza acotada para no conservar direcciones indefinidamente.
            for old_key in list(_attempts):
                if not _attempts[old_key] or _attempts[old_key][-1] < now-60: del _attempts[old_key]
            q=_attempts[key]
            while q and q[0]<now-60: q.popleft()
            if len(q)>=20: return JSONResponse({'detail':'Demasiados intentos. Espera un minuto.'},status_code=429)
            q.append(now)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path not in ('/docs','/redoc'):
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api/'): response.headers['Cache-Control']='no-store'
    return response

@app.exception_handler(pymysql.MySQLError)
async def db_error(request,error):
    code=error.args[0] if error.args else None
    log.error('Error MySQL: %s, código %s',type(error).__name__,code)
    status=503
    if code==1146:
        detail='La conexión con MySQL funciona, pero faltan tablas de PlanifIA. Ejecuta python scripts/crear_base.py desde la carpeta del proyecto.'
    elif code==1054:
        detail='La estructura de las tablas no coincide con PlanifIA. Revisa el esquema database/planifia.sql.'
    elif code in (1044,1045,1142,1143):
        detail='MySQL rechazó el acceso. Revisa el usuario, la contraseña y sus permisos sobre la base configurada.'
    elif code==1049:
        detail='La base indicada en DB_NAME no existe. Revisa su nombre en .env.'
    elif code in (2002,2003,2006,2013):
        detail='No pudimos conectar con la base de datos. Revisa que MySQL esté iniciado.'
    else:
        status=500
        detail='No pudimos completar la operación en MySQL. Revisa el código de error en la consola del servidor.'
    return JSONResponse({'detail':detail},status_code=status)

@app.exception_handler(RequestValidationError)
async def invalid(request,error):
    return JSONResponse({'detail':'Revisa los campos: completa los obligatorios y usa fechas y horarios válidos.',
        'campos':['.'.join(str(x) for x in e['loc'][1:]) for e in error.errors()]},status_code=422)

@app.get('/api/health',tags=['Estado'])
def health():
    with transaction() as cursor:
        check_schema(cursor)
        cursor.execute('SELECT VERSION() AS version')
        row=cursor.fetchone()
    return {'estado':'ok','conexion':'PyMySQL','mysql':row['version']}

@app.get('/',include_in_schema=False)
def index(): return RedirectResponse('/app/login.html')

for router in (auth.router,tareas.router,evaluaciones.router,dashboard.router,notificaciones.router,planificacion.router,mascota.router): app.include_router(router)
app.mount('/app',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')

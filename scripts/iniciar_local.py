"""Comprueba MySQL y arranca la aplicación local."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import pymysql
import httpx
from backend.database import transaction, check_schema

try:
    response=httpx.get('http://127.0.0.1:8000/api/health',timeout=3)
    if response.status_code==200 and response.json().get('conexion')=='PyMySQL':
        print('PlanifIA ya está funcionando: http://127.0.0.1:8000');sys.exit(0)
except (httpx.HTTPError,ValueError):pass

def database_ready():
    try:
        with transaction() as cursor:
            check_schema(cursor)
        return True
    except pymysql.MySQLError as error:
        if error.args and error.args[0]==1146:
            print('MySQL conectado, pero faltan tablas. Ejecuta: python scripts/crear_base.py')
        else:
            print('No se pudo comprobar MySQL. Revisa .env y los permisos de la cuenta.')
        return False

if not database_ready():
    sys.exit(1)
print('PlanifIA: http://127.0.0.1:8000')
print('Documentación: http://127.0.0.1:8000/docs')
print('Mantén esta ventana abierta. Para detener FastAPI, presiona Ctrl+C.')
import uvicorn
uvicorn.run('backend.main:app',host='127.0.0.1',port=8000,app_dir=str(ROOT))

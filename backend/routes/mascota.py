from fastapi import APIRouter, Depends
from backend.database import transaction
from backend.security import usuario_actual
from backend.services.pet_service import lock_pet, public_pet

router = APIRouter(prefix='/api/mascota', tags=['Mascota'])


@router.get('')
def obtener(user=Depends(usuario_actual)):
    with transaction() as cursor:
        return public_pet(lock_pet(cursor, user['id']))

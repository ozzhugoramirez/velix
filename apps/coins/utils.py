from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from .models import CoinTransaction
# Importamos el modelo Perfil directamente
from apps.perfil.models import Perfil

def gestion_coins(user, amount, tipo, descripcion):
    """
    Función ATÓMICA para gestionar monedas.
    Garantiza que el historial y el saldo siempre coincidan.
    
    Args:
        user: Instancia de User (django.contrib.auth.models.User)
        amount: Cantidad (positivo para sumar, negativo para restar)
        tipo: String de las opciones (COMPRA, REFERIDO, etc)
        descripcion: Texto descriptivo
    """
    try:
        # INICIO DE TRANSACCIÓN BLINDADA
        with transaction.atomic():
            # 1. Obtenemos el perfil y BLOQUEAMOS la fila en la DB (Lock)
            # Esto impide que otro proceso modifique el saldo simultáneamente.
            perfil = Perfil.objects.select_for_update().get(usuario=user)
            
            # 2. Creamos el registro en el historial
            CoinTransaction.objects.create(
                user=user,
                amount=amount,
                transaction_type=tipo,
                description=descripcion
            )
            
            # 3. Actualizamos el saldo del perfil de forma incremental
            # Convertimos a Decimal para evitar errores de coma flotante
            perfil.coins += Decimal(str(amount))
            perfil.save()
            
            return True, perfil.coins

    except ObjectDoesNotExist:
        print(f"Error: El usuario {user} no tiene perfil creado.")
        return False, 0
        
    except Exception as e:
        # Si algo falla dentro del 'with', Django hace ROLLBACK automático.
        # Es decir, deshace el historial y no toca el saldo.
        print(f"Error en transacción de coins: {e}")
        return False, 0
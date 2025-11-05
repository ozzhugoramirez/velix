from .models import Reclamo

def reclamos_pendientes_count(request):
    if request.user.is_authenticated:  # Solo para usuarios autenticados
        count = Reclamo.objects.filter(estado='pendiente').count()
        return {'reclamos_pendientes_count': count}
    return {'reclamos_pendientes_count': 0}

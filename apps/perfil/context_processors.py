from .models import *
from django.db.models import Q


def perfiles_pendientes_count(request):
    if request.user.is_authenticated:  # Solo para usuarios autenticados
        count = Perfil.objects.filter(estado_verificacion='pendiente').count()
        return {'perfiles_pendientes_count': count}
    return {'perfiles_pendientes_count': 0}



def ordenes_pendientes_count(request):
    if request.user.is_authenticated:  # Solo para usuarios autenticados
        count = Order.objects.filter(status='pending').count()
        return {'ordenes_pendientes_count': count}
    return {'ordenes_pendientes_count': 0}





def unread_notifications(request):
    """Devuelve la cantidad de notificaciones NO leídas para el usuario actual, incluyendo las de grupo."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            Q(recipient=request.user) | Q(group__users=request.user)
        ).exclude(
            notificationreadstatus__user=request.user, notificationreadstatus__is_read=True
        ).distinct().count()

        return {"unread_notifications_count": unread_count}
    
    return {"unread_notifications_count": 0}



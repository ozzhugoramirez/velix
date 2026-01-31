
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from .models import *
from django.contrib import messages

class HomeProfileView(LoginRequiredMixin, View):
    def get(self, request):
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)

        perfil_parcial = perfil.es_parcialmente_completo()
        ordenes = Order.objects.filter(user=request.user).order_by('-created_at')

        productos_favoritos = request.user.liked_products.all()

        context = {
            "perfil": perfil,
            "perfil_parcial": perfil_parcial,
            'ordenes': ordenes,
            "coins_balance": perfil.coins,
            'productos_favoritos': productos_favoritos,
        }

        return render(request, "components/web/perfil/inicioperfil.html", context)

#compartidos
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum

from .models import Perfil, Order 
from apps.shops.models import ProductShare # <--- Importa tu modelo aquí

class compartidosProfileView(LoginRequiredMixin, View):
    def get(self, request):
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)
        perfil_parcial = perfil.es_parcialmente_completo()
        ordenes = Order.objects.filter(user=request.user).order_by('-created_at')
        productos_favoritos = request.user.liked_products.all()

        # --- LÓGICA NUEVA ---
        # 1. Obtener todos los enlaces que este usuario ha generado
        mis_compartidos = ProductShare.objects.filter(user=request.user).order_by('-created_at')
        
        # 2. Calcular total de vistas (opcional, para estadística)
        total_vistas = mis_compartidos.aggregate(total=Sum('views_count'))['total'] or 0

        context = {
            "perfil": perfil,
            "perfil_parcial": perfil_parcial,
            'ordenes': ordenes,
            'productos_favoritos': productos_favoritos,
            
            # Pasamos los datos a la plantilla
            "compartidos": mis_compartidos,
            "total_links": mis_compartidos.count(),
            "total_vistas": total_vistas,
        }

        return render(request, "components/web/perfil/compartidos.html", context)


#miscompras
class miscomprasProfileView(LoginRequiredMixin, View):
    def get(self, request):
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)

        perfil_parcial = perfil.es_parcialmente_completo()
        ordenes = Order.objects.filter(user=request.user).order_by('-created_at')

        productos_favoritos = request.user.liked_products.all()

        context = {
            "perfil": perfil,
            "perfil_parcial": perfil_parcial,
            'ordenes': ordenes,
            'productos_favoritos': productos_favoritos,
        }

        return render(request, "components/web/perfil/miscompras.html", context)


from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

# --- CORRECCIÓN DE IMPORTS ---
# Como 'Order' está en tu archivo apps/perfil/models.py, lo importamos desde .models
from .models import Perfil, Order 

# Importamos el modelo de historial de la app 'coins'
from apps.coins.models import CoinTransaction 

class coinsProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # 1. Obtener Perfil
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)

        # 2. Datos existentes
        perfil_parcial = perfil.es_parcialmente_completo()
        
        # 3. Órdenes (Ahora funcionará porque Order viene de .models)
        ordenes = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # 4. Favoritos
        productos_favoritos = request.user.liked_products.all()

        # 5. Historial de Coins (Usando el modelo de la app 'coins')
        historial = CoinTransaction.objects.filter(user=request.user).order_by('-created_at')

        context = {
            "perfil": perfil,
            "perfil_parcial": perfil_parcial,
            'ordenes': ordenes,
            'productos_favoritos': productos_favoritos,
            
            # Datos para la Billetera
            "coins_balance": perfil.coins, 
            "historial": historial,
        }

        return render(request, "components/web/perfil/coins.html", context)
#favoritos


class favoritosProfileView(LoginRequiredMixin, View):
    def get(self, request):
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)

        perfil_parcial = perfil.es_parcialmente_completo()
        ordenes = Order.objects.filter(user=request.user).order_by('-created_at')

        productos_favoritos = request.user.liked_products.all()

        context = {
            "perfil": perfil,
            "perfil_parcial": perfil_parcial,
            'ordenes': ordenes,
            'productos_favoritos': productos_favoritos,
        }

        return render(request, "components/web/perfil/favoritos.html", context)



class DetalleMiscompraView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        # Obtén la orden específica asegurándote que pertenece al usuario
        try:
            ordenes = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return redirect('profile')
        
        # Obtén los items relacionados con la orden
        order_items = ordenes.orderitem_set.all()
        
        # Obtén la primera URL de comentario relacionada con la orden (si existe)
        first_comment_url = ordenes.comment_urls.first()
        
        # Contexto que pasaremos al template
        context = {
            'ordenes': ordenes,
            'order_items': order_items,
            'first_comment_url': first_comment_url,
        }
        return render(request, 'pages/web/detalle_compra.html', context)








class PostProfileView(LoginRequiredMixin, View):
    def get(self, request):
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)
        address = Address.objects.filter(user=request.user, is_default=True).first()

        perfil_data = {
            'numero_telefono': perfil.numero_telefono or '',
            'fecha_nacimiento': perfil.fecha_nacimiento or '',
            'genero': perfil.genero or '',
            'foto_perfil': perfil.foto_perfil or '',
        }

        address_data = {
            'localidad': address.localidad if address else '',
            'postal_code': address.postal_code if address else '',
            'barrio': address.barrio if address else '',
            'whatsapp_number': address.whatsapp_number if address else '',
            'email': address.email if address else '',
            'main_street': address.main_street if address else '',
            'secondary_street': address.secondary_street if address else '',
            'house_number': address.house_number if address else '',
            'description': address.description if address else '',
        }

        next_url = request.GET.get('next', '')
        return render(request, "pages/web/dataperfil.html", {
            "perfil": perfil_data,
            "address": address_data,
            "next": next_url
        })

    def post(self, request):
        # Actualización del perfil
        perfil = Perfil.objects.get(usuario=request.user)
        perfil.numero_telefono = request.POST.get("numero_telefono")
        perfil.fecha_nacimiento = request.POST.get("fecha_nacimiento")
        perfil.genero = request.POST.get("genero")

        if 'foto_perfil' in request.FILES:
            perfil.foto_perfil = request.FILES["foto_perfil"]

        perfil.estado_verificacion = 'aprobado'
        perfil.comentario_rechazo = None  # Limpia cualquier comentario previo de rechazo
        perfil.cuenta_verificada = False
        perfil.save()

        # Manejo de la dirección
        address_data = {
            'localidad': request.POST.get("localidad"),
            'postal_code': request.POST.get("postal_code"),
            'barrio': request.POST.get("barrio"),
            'whatsapp_number': request.POST.get("whatsapp_number"),
            'email': request.POST.get("email"),
            'main_street': request.POST.get("main_street"),
            'secondary_street': request.POST.get("secondary_street"),
            'house_number': request.POST.get("house_number"),
            'description': request.POST.get("description"),
        }

        # Validar campos obligatorios
        required_fields = ['localidad', 'main_street', 'house_number']
        missing_fields = [field for field in required_fields if not address_data[field]]

        if missing_fields:
            messages.error(request, f"Faltan los siguientes campos obligatorios: {', '.join(missing_fields)}")
            return redirect(request.path)

        # Crear o actualizar dirección
        address, created = Address.objects.get_or_create(
            user=request.user,
            is_default=True,
            defaults=address_data
        )
        if not created:
            for field, value in address_data.items():
                setattr(address, field, value)
            address.save()

        # Redirección
        next_url = request.POST.get('next', reverse('profile'))
        return redirect(next_url)






from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta
from apps.shops.models import *
from django.contrib import messages
from apps.dasboard.models import *
from apps.perfil.models import *
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from django.http import HttpResponseRedirect
from django.utils.translation import activate
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth import logout





class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("home")  





def change_language(request):
    if request.method == "POST":
        lang_code = request.POST.get('language')
        if lang_code in dict(settings.LANGUAGES):
            activate(lang_code)
            request.session[settings.LANGUAGE_COOKIE_NAME] = lang_code
            print(f"Idioma cambiado a: {lang_code}")  # Agrega esta línea para verificar
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))




class HomeView(View):
    def get(self, request):
        hora_actual = timezone.now()  # Manejo de zona horaria
        
        
        # Promociones destacadas
        promotional_products = Product.objects.filter(
            is_promotional=True,
            is_featured=True,
            promotion_start_date__lte=hora_actual,
            promotion_end_date__gte=hora_actual
        )

        # Ofertas destacadas del día
        daily_offers = Product.objects.filter(
            is_daily_offer=True,
            is_featured=True,
            offer_start_date__lte=hora_actual,
            offer_end_date__gte=hora_actual
        )

        # Vistas recientes
        recent_views = []
        views = ProductView.objects.filter(
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key if not request.user.is_authenticated else None
        ).order_by('-timestamp')

        seen_products = set()
        for view in views:
            if view.product.id not in seen_products:
                recent_views.append(view)
                seen_products.add(view.product.id)
            if len(recent_views) >= 3:  # Limitar a 5 productos únicos
                break

        liked_products = Product.objects.filter(likes=request.user) if request.user.is_authenticated else []

        context = {
            "promotional_products": promotional_products,
            "daily_offers": daily_offers,
            "recent_views": recent_views,
            "liked_products": liked_products,
        }

        return render(request, "pages/web/index.html", context)

class SearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip().lower()  # Normalizamos la consulta a minúsculas
        exact_matches = Product.objects.none()
        other_matches = Product.objects.none()

        if query:
            STOP_WORDS = {'de', 'para', 'el', 'la', 'los', 'las', 'un', 'una', 'y', 'en', 'con', 'por', 'a', 'que'}

            # Normalizamos las palabras clave y filtramos irrelevantes
            search_terms = [
                term.strip().lower()
                for term in query.split()
                if term.lower() not in STOP_WORDS
            ]

            # **Filtrar coincidencias exactas**
            exact_query = Q()
            for term in search_terms:
                exact_query &= (Q(title__icontains=term) | Q(description__icontains=term))  # Todas las palabras clave deben coincidir
            exact_matches = Product.objects.filter(exact_query)

            # **Filtrar coincidencias parciales**
            related_query = Q()
            for term in search_terms:
                related_query |= (Q(title__icontains=term) | Q(description__icontains=term))  # Al menos una palabra clave debe coincidir
            other_matches = Product.objects.filter(related_query).exclude(id__in=exact_matches.values_list('id', flat=True))

            # **Registrar la búsqueda completa**
            search_query, created = SearchQuery.objects.get_or_create(term=query)
            if not created:
                search_query.count += 1  # Incrementamos correctamente
            search_query.has_results = exact_matches.exists() or other_matches.exists()
            if created and request.user.is_authenticated:
                search_query.usuario = request.user
            search_query.save()

            # **Registrar palabras individuales**
            seen_terms = set()
            for term in search_terms:
                if term not in seen_terms:
                    seen_terms.add(term)
                    # Incrementar el contador de cada palabra individual
                    keyword_query, created = SearchQuery.objects.get_or_create(term=term)
                    if not created:
                        keyword_query.count += 1
                    if created and request.user.is_authenticated:
                        keyword_query.usuario = request.user
                    keyword_query.save()

        # Contexto para la plantilla
        context = {
            'exact_matches': exact_matches,
            'other_matches': other_matches,
            'query': query
        }
        return render(request, 'pages/web/search.html', context)




class SearchSuggestionsView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        
        if query:
            products = Product.objects.filter(title__icontains=query)[:4]  # Limitar a 5 sugerencias
            suggestions = [product.title for product in products]
        else:
            suggestions = []

        return JsonResponse({'suggestions': suggestions})

class ReclamoCreateView(View):
    def get(self, request):
        reclamo_opciones = Reclamo.NOMBRE_OPCIONES
        return render(request, 'pages/web/reclamo_form.html', {'reclamo_opciones': reclamo_opciones})

    def post(self, request):
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        correo = request.POST.get('correo')
        celular = request.POST.get('celular')
        tipo_reclamo = request.POST.get('tipo_reclamo')
        descripcion = request.POST.get('descripcion')

        reclamo = Reclamo(
            usuario=request.user if request.user.is_authenticated else None,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            celular=celular,
            tipo_reclamo=tipo_reclamo,
            descripcion=descripcion
        )
        
        reclamo.save()
        messages.success(request, 'Reclamo registrado con éxito.')
        return redirect('reclamo_success')

class ReclamoSuccesView(View):
    def get(self, request):
        return render(request, 'pages/web/reclamo_success.html')
    



class InvitationBienvenidoView(View):
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        valid_platforms = ["ksls", "nsd", "nxc", "tcc", "azz"]
        # qr  ksls
        # facebook nsd
        # instagram nxc
        # whatsapp tcc
        # tiktok azz

        if user_id in valid_platforms:
            # Incrementar el contador o crear un registro nuevo
            social_click, created = SocialMediaClick.objects.get_or_create(
                platform=user_id,
                timestamp__date=localtime(now()).date(),  # Agrupar por fecha
                defaults={'click_count': 1}
            )
            if not created:
                social_click.click_count += 1
                social_click.save()

            # Contexto para renderizar
            contexto = {
                "Invitationdata": True,
                "modalInvitation": user_id,
            }
            return render(request, 'pages/web/index.html', contexto)

        # Redirigir al home si la plataforma no es válida
        return redirect('home')



def page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)




def info_page(request, section):
    context = {'section': section}
    return render(request, 'pages/web/info_page.html', context)

def info_page_sobremi(request, section):
    context = {'section': section}
    return render(request, 'pages/web/info_sobre_mi.html', context)

def info_page_ayuda(request, section):
    context = {'section': section}
    return render(request, 'pages/web/info_page_ayuda.html', context)

def info_page_cuenta(request, section):
    context = {'section': section}
    return render(request, 'pages/web/info_page_cuenta.html', context)

def info_page_recursos(request, section):
    context = {'section': section}
    return render(request, 'pages/web/info_page_recursos.html', context)





class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        
        

        Notification.objects.filter(created_at__lt=now() - timedelta(days=30)).delete()

        notifications = Notification.objects.filter(
            Q(recipient=request.user) | Q(group__users=request.user)
        ).order_by("-created_at")

        # Crear una lista de notificaciones con su estado de lectura
        notification_data = []
        for notification in notifications:
            read_status = NotificationReadStatus.objects.filter(user=request.user, notification=notification).first()
            notification_data.append({
                "notification": notification,
                "is_read": read_status.is_read if read_status else False
            })

        context = {"notification_data": notification_data}
        return render(request, "pages/web/notification_list.html", context)







class NotificationDetailView(LoginRequiredMixin, View):
    def get(self, request, notification_id):
        """Muestra el detalle de una notificación y la marca como leída SOLO para el usuario actual."""
        notification = get_object_or_404(Notification, id=notification_id)  # Ahora usa UUID

        # Verificar si el usuario tiene acceso a la notificación
        if notification.recipient != request.user and (notification.group is None or request.user not in notification.group.users.all()):
            return render(request, "pages/web/access_denied.html")

        # Marcar SOLO para este usuario como leído
        read_status, created = NotificationReadStatus.objects.get_or_create(user=request.user, notification=notification)
        if not read_status.is_read:
            read_status.is_read = True
            read_status.save()

        context = {"notification": notification}
        return render(request, "pages/web/notification_detail.html", context)




# views.py

from django.views import View
from django.http import HttpResponseRedirect
from urllib.parse import quote
from decimal import Decimal
from django.utils import timezone

class GrupoWhatsappView(View):
    def get(self, request, *args, **kwargs):
        producto_id = request.GET.get('id')
        titulo = request.GET.get('titulo', '')
        precio_raw = request.GET.get('precio', '0').replace(',', '.')
        prioridad = int(request.GET.get('prioridad', '1'))

        try:
            precio = Decimal(precio_raw)
        except:
            precio = Decimal('0.00')

        ip = self.get_client_ip(request)

        # Selección round-robin por última asignación
        empleados = Empleado.objects.filter(activo=True).order_by('ultima_asignacion')
        empleado = None
        for e in empleados:
            if e.consultas_activas() < e.max_consultas:
                empleado = e
                break

        if empleado:
            empleado.ultima_asignacion = timezone.now()
            empleado.save()
            ClienteConsulta.objects.create(
                empleado=empleado,
                producto_id=producto_id,
                titulo_producto=titulo,
                precio_producto=precio,
                prioridad=prioridad,
                ip_cliente=ip
            )
            numero = empleado.telefono
        else:
            numero = '+5491150183148'  # Número general

        mensaje = f"Hola, estoy interesado en el producto: {titulo} (ID: {producto_id}) Precio: ${precio}"
        whatsapp_url = f"https://wa.me/{numero}?text={quote(mensaje)}"
        return HttpResponseRedirect(whatsapp_url)

    def get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0]
        return request.META.get('REMOTE_ADDR')


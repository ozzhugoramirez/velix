
from datetime import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Q 
from django.utils.timezone import localtime
from django.urls import reverse
from django.db.models import Case, When, Value, IntegerField, Q
from apps.perfil.models import *
from django.utils import timezone
from collections import defaultdict 
from django.http import JsonResponse
from django.views.generic.edit import *
from django.urls import reverse_lazy
from django.views.generic import ListView
from apps.dasboard.models import *
from apps.perfil.models import Coupon, Order, Perfil
from apps.shops.models import *
from apps.user.models import *
from django.utils.timezone import now, timedelta
from .forms import CouponForm, ProductEditForm, ProductForm, UserEditForm
from django.db.models import Sum

def admin_required(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)



from django.db.models import Sum, F

@method_decorator(user_passes_test(admin_required), name='dispatch')
class HomeAdminView(View):
    def get(self, request):
        # Redes sociales válidas
        valid_platforms = ["ksls", "nsd", "nxc", "tcc", "azz"]
        platform_names = {
            "ksls": "QR",
            "nsd": "Facebook",
            "nxc": "Instagram",
            "tcc": "WhatsApp",
            "azz": "TikTok"
        }

        # Generar datos para cada plataforma
        social_links = []
        for platform in valid_platforms:
            total_clicks = SocialMediaClick.objects.filter(platform=platform).count()
            url = request.build_absolute_uri(reverse('invitation_bienvenido', args=[platform]))
            social_links.append({
                "platform": platform_names[platform],
                "url": url,
                "total_clicks": total_clicks
            })

        # Calcular valores directamente en la base de datos
        total_valor_stock = Product.objects.aggregate(total=Sum(F('price') * F('stock')))['total'] or 0
        total_valor_propios = Product.objects.filter(is_own_product=True).aggregate(
            total=Sum(F('price') * F('stock'))
        )['total'] or 0
        total_valor_terceros = Product.objects.filter(is_own_product=False).aggregate(
            total=Sum(F('price') * F('stock'))
        )['total'] or 0

        # Contexto
        context = {
            "social_links": social_links,
            "total_valor_stock": total_valor_stock,
            "total_valor_propios": total_valor_propios,
            "total_valor_terceros": total_valor_terceros
        }
        return render(request, "pages/admin/index.html", context)





from django.utils.timezone import now, localdate
from datetime import timedelta
from django.db.models import Sum

class VisitasCombinadasView(View):
    def get(self, request):
        # Obtener el filtro seleccionado, 'hoy' por defecto
        filtro_fecha = request.GET.get('filtro', 'hoy')
        hoy = localdate()  # Usar la fecha local, considerando la zona horaria

        # Determinar el rango de fechas según el filtro
        if filtro_fecha == 'semana':
            fecha_inicio = hoy - timedelta(days=6)  # Últimos 7 días, incluyendo hoy
            fecha_fin = hoy
        elif filtro_fecha == 'mes':
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
        elif filtro_fecha == 'año':
            fecha_inicio = hoy.replace(month=1, day=1)
            fecha_fin = hoy
        else:  # Default a hoy
            fecha_inicio = fecha_fin = hoy

        # Filtrar visitas diarias dentro del rango de fechas
        if filtro_fecha == 'hoy':
            visitas_diarias = VisitaDiaria.objects.filter(fecha=hoy)  # Filtro exacto para hoy
        else:
            visitas_diarias = VisitaDiaria.objects.filter(fecha__range=(fecha_inicio, fecha_fin))

        # Depuración
        print("Visitas diarias SQL query:", visitas_diarias.query)
        print("Fecha Inicio:", fecha_inicio, "Fecha Fin:", fecha_fin)

        # Total de visitas global
        totales_visi = Visita.objects.count()

        # Agregar visitas detalladas para cada "VisitaDiaria"
        for visita_diaria in visitas_diarias:
            visitas_detalladas = Visita.objects.filter(
                marca_tiempo__date=visita_diaria.fecha,
                usuario=visita_diaria.usuario
            ).order_by('marca_tiempo')
            visita_diaria.visitas_detalladas = visitas_detalladas

        # Contar visitas totales en el rango
        total_visitas = Visita.objects.filter(marca_tiempo__date__range=(fecha_inicio, fecha_fin)).count()
        total_visitas_diarias = visitas_diarias.aggregate(Sum('conteo_visitas'))['conteo_visitas__sum'] or 0

        # Contexto para el template
        context = {
            'visitas_diarias': visitas_diarias,
            'filtro_fecha': filtro_fecha,
            'total_visitas': total_visitas,
            'total_visitas_diarias': total_visitas_diarias,
            "totales_visi": totales_visi,
        }
        return render(request, "pages/admin/visitas_combinadas.html", context)




@method_decorator(user_passes_test(admin_required), name='dispatch')
class PaginasVisitadasSesionView(View):
    def get(self, request, visita_id):
        # Obtener la visita específica
        visita = get_object_or_404(Visita, id=visita_id)
        
        # Filtrar las páginas visitadas asociadas a esta visita
        paginas_visitadas = PaginaVisitada.objects.filter(visita=visita).order_by('-marca_tiempo')

        context = {
            'visita': visita,
            'paginas_visitadas': paginas_visitadas,
        }
        return render(request, "pages/admin/paginas_visitadas_sesion.html", context)


"""
 vista de clientes lista de usuarios editar y ver perfil
"""
@method_decorator(user_passes_test(admin_required), name='dispatch')
class ClientesAdminView(View):
    def get(self, request):
        usuarios = UserAccount.objects.all()

        # Cálculos de estadísticas
        total_usuarios = usuarios.count()
        total_activos = usuarios.filter(is_active=True).count()
        total_verificados = usuarios.filter(is_verified=True).count()
        total_no_verificados = usuarios.filter(is_verified=False).count()

        # Filtro de búsqueda
        query = request.GET.get('q')
        if query:
            usuarios = usuarios.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(whatsapp_number__icontains=query)
            )

        # Procesar la última actividad
        for usuario in usuarios:
            if usuario.last_activity:
                time_diff = (now() - usuario.last_activity).total_seconds()
                if time_diff < 60:
                    usuario.last_activity_display = "Conectado hace menos de un minuto"
                elif time_diff < 3600:
                    usuario.last_activity_display = f"Conectado hace {int(time_diff // 60)} minutos"
                elif time_diff < 86400:
                    usuario.last_activity_display = f"Conectado hace {int(time_diff // 3600)} horas"
                else:
                    usuario.last_activity_display = f"Desconectado hace {int(time_diff // 86400)} días"
            else:
                usuario.last_activity_display = "Desconectado"

        context = {
            'usuarios': usuarios,
            'total_usuarios': total_usuarios,
            'total_activos': total_activos,
            'total_verificados': total_verificados,
            'total_no_verificados': total_no_verificados,
        }
        return render(request, "pages/admin/clientes.html", context)


@method_decorator(user_passes_test(admin_required), name='dispatch')
class EditarUsuarioView(View):
    def get(self, request, usuario_id):
        usuario = get_object_or_404(UserAccount, id=usuario_id)
        form = UserEditForm(instance=usuario)
        return render(request, "pages/admin/editar_usuario.html", {'form': form, 'usuario': usuario})

    def post(self, request, usuario_id):
        usuario = get_object_or_404(UserAccount, id=usuario_id)
        form = UserEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save(commit=False)
            # Evita tocar la contraseña si no se modifica explícitamente.
            usuario.save()
            form.save_m2m()  # Guardar relaciones many-to-many.
            messages.success(request, "Usuario actualizado con éxito.")
            return redirect('clintes_admin')
        else:
            messages.error(request, "Por favor, corrige los errores a continuación.")
        return render(request, "pages/admin/editar_usuario.html", {'form': form, 'usuario': usuario})


@method_decorator(user_passes_test(admin_required), name='dispatch')
class VerPerfilView(View):
    def get(self, request, usuario_id):
        perfil = get_object_or_404(Perfil, usuario__id=usuario_id)
        return render(request, "pages/admin/perfil.html", {"perfil": perfil})

@method_decorator(user_passes_test(admin_required), name='dispatch')
class ItemProfileCompra(View):
    def get(self, request, usuario_id):
        perfil = get_object_or_404(Perfil, usuario__id=usuario_id)
        context = {"perfil": perfil }
        return render(request, "components/admin/itemperfil/productocomprado.html", context)

@method_decorator(user_passes_test(admin_required), name='dispatch')
class ItemProfileLink(View):
    def get(self, request, usuario_id):
        perfil = get_object_or_404(Perfil, usuario__id=usuario_id)
        context = {"perfil": perfil }
        return render(request, "components/admin/itemperfil/linkcompartidos.html", context)

@method_decorator(user_passes_test(admin_required), name='dispatch')
class ItemProfileVisitas(View):
    def get(self, request, usuario_id):
        perfil = get_object_or_404(Perfil, usuario__id=usuario_id)
        visitas = Visita.objects.filter(usuario__id=usuario_id).order_by('-marca_tiempo')  # Obtener las visitas del usuario
        print(f"Visitas encontradas: {visitas}")  # Depuración
        context = {
            "perfil": perfil,
            "visitas": visitas,
        }
        return render(request, "components/admin/itemperfil/visitasalaweb.html", context)


@method_decorator(user_passes_test(admin_required), name='dispatch')
class PaginasVisitadas(View):
    def get(self, request, visita_id):
        visita = get_object_or_404(Visita, id=visita_id)  # Obtener la visita específica
        paginas = visita.paginas.all()  # Obtener todas las páginas asociadas a la visita

        context = {
            'visita': visita,
            'paginas': paginas,  # Mostrar todas las visitas
        }
        return render(request, "components/admin/itemperfil/paginas_visitadas.html", context)






"""
    fin de vista de perfil 

"""
@method_decorator(user_passes_test(admin_required), name='dispatch')
class ReclamosView(View):
    def get(self, request):
        estado_filtro = request.GET.get('estado')
        
        # Filtrar por estado si se especifica
        if estado_filtro:
            reclamos = Reclamo.objects.filter(estado=estado_filtro).order_by('-fecha_creacion')
        else:
            reclamos = Reclamo.objects.all().order_by('-fecha_creacion')

        # Contadores
        total_reclamos = Reclamo.objects.count()
        pendientes = Reclamo.objects.filter(estado='pendiente').count()
        en_proceso = Reclamo.objects.filter(estado='en_proceso').count()
        resueltos = Reclamo.objects.filter(estado='resuelto').count()
        rechazados = Reclamo.objects.filter(estado='rechazado').count()

        context = {
            'reclamos': reclamos,
            'total_reclamos': total_reclamos,
            'pendientes': pendientes,
            'en_proceso': en_proceso,
            'resueltos': resueltos,
            'rechazados': rechazados,
        }
        return render(request, "pages/admin/reclamos.html", context)
    



@method_decorator(user_passes_test(admin_required), name='dispatch')
class AtenderReclamoView(View):
    def get(self, request, reclamo_id):
        # Obtiene el reclamo específico
        reclamo = get_object_or_404(Reclamo, id=reclamo_id)
        return render(request, "pages/admin/atender_reclamo.html", {'reclamo': reclamo})

    def post(self, request, reclamo_id):
        reclamo = get_object_or_404(Reclamo, id=reclamo_id)

        # Actualizar el estado del reclamo y notas internas
        nuevo_estado = request.POST.get('estado')
        notas = request.POST.get('notas_internas', '')

        if nuevo_estado:
            reclamo.estado = nuevo_estado
            reclamo.notas_internas = notas
            reclamo.save()
            messages.success(request, "El reclamo ha sido actualizado con éxito.")
        else:
            messages.error(request, "Debe seleccionar un estado para el reclamo.")

        return redirect('Reclamos_admin')


@method_decorator(user_passes_test(admin_required), name='dispatch')
class SearchQuerySummaryView(View):
    def get(self, request):
        # Obtener el rango seleccionado (default: 'all')
        rango = request.GET.get('rango', 'all')

        # Definir el rango de fechas según la opción seleccionada
        hoy = timezone.now().date()
        if rango == 'last_week':
            fecha_inicio = hoy - timezone.timedelta(days=7)
            fecha_fin = hoy
        elif rango == 'last_month':
            fecha_inicio = hoy - timezone.timedelta(days=30)
            fecha_fin = hoy
        elif rango == 'last_year':
            fecha_inicio = hoy - timezone.timedelta(days=365)
            fecha_fin = hoy
        else:  # Mostrar todos los datos
            fecha_inicio = None
            fecha_fin = None

        # Filtrar los términos de búsqueda según el rango
        if fecha_inicio and fecha_fin:
            search_queries = (
                SearchQuery.objects.filter(created_at__date__range=[fecha_inicio, fecha_fin])
                .values("id", "term")
                .annotate(total_count=Sum("count"))
                .order_by("-total_count", "term")
            )
        else:  # Sin rango de fechas
            search_queries = (
                SearchQuery.objects.all()
                .values("id", "term")
                .annotate(total_count=Sum("count"))
                .order_by("-total_count", "term")
            )

        context = {
            "search_queries": search_queries,
            "rango": rango,
        }
        return render(request, "pages/admin/search_queries_summary.html", context)

@method_decorator(user_passes_test(admin_required), name='dispatch')
class ConfirmDeleteSearchQueriesView(View):
    def post(self, request):
        selected_queries = request.POST.getlist('queries')
        queries = SearchQuery.objects.filter(id__in=selected_queries)

        context = {
            "queries": queries,
        }
        return render(request, "pages/admin/confirm_delete_search_queries.html", context)


@method_decorator(user_passes_test(admin_required), name='dispatch')
class DeleteSelectedSearchQueriesView(View):
    def post(self, request):
        selected_queries = request.POST.getlist('queries')
        SearchQuery.objects.filter(id__in=selected_queries).delete()
        return redirect('search_queries')




@method_decorator(user_passes_test(admin_required), name='dispatch')
class ProductoAdminView(View):
    def get(self, request):
        query = request.GET.get('q', '')  # Obtener la consulta de búsqueda
        categoria_id = request.GET.get('categoria', '')  # Obtener la categoría seleccionada 
        tipo_producto = request.GET.get('tipo_producto', '')  # Obtener el tipo de producto (propio o de terceros)
        proveedor_id = request.GET.get('proveedor', '')  # Obtener el proveedor seleccionado
        vendedor_id = request.GET.get('vendedor_externo', '')  # Obtener el vendedor externo seleccionado

        productos = Product.objects.all().order_by('-created_at')

        # Filtrar productos por la consulta de búsqueda
        if query:
            productos = productos.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )

        # Filtrar por categoría
        if categoria_id:
            productos = productos.filter(category_id=categoria_id)

        # Filtrar por tipo de producto (propio o de terceros)
        if tipo_producto:
            if tipo_producto == 'propio':
                productos = productos.filter(is_own_product=True)
            elif tipo_producto == 'terceros':
                productos = productos.filter(is_own_product=False)

        # Filtrar por proveedor
        if proveedor_id:
            productos = productos.filter(supplier_id=proveedor_id)

        # Filtrar por vendedor externo
        if vendedor_id:
            productos = productos.filter(external_seller_id=vendedor_id)

        # Contar productos totales, propios y de terceros
        productos_reposicion = productos.filter(stock__lte=2)
        total_productos = productos.count()
        total_propios = productos.filter(is_own_product=True).count()
        total_terceros = productos.filter(is_own_product=False).count()

        # Obtener todas las categorías, proveedores y vendedores externos
        categorias = Category.objects.all()
        proveedores = Proveedor.objects.all()
        vendedores_externos = VendedorExterno.objects.all()

        context = {
            'productos': productos,
            'query': query,
            'categorias': categorias,
            'categoria_id': categoria_id,  # Mantener la selección de categoría
            'total_productos': total_productos,  # Total de productos
            'total_propios': total_propios,  # Total de productos propios
            'total_terceros': total_terceros,  # Total de productos de terceros
            'proveedores': proveedores,
            'vendedores_externos': vendedores_externos,
            'tipo_producto': tipo_producto,
            'proveedor_id': proveedor_id,
            'vendedor_id': vendedor_id,
            'productos_reposicion': productos_reposicion,
        }

        return render(request, "pages/admin/productos.html", context)


       


class CrearProductoView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'pages/admin/crear_producto.html'
    success_url = reverse_lazy('ProductoAdminView')

class CrearCategoriaView(CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'pages/admin/crear_categoria.html'
    success_url = reverse_lazy('crear_producto') 

class EditarProductoView(UpdateView):
    model = Product
    form_class = ProductEditForm
    template_name = 'pages/admin/editar_producto.html'
    success_url = reverse_lazy('ProductoAdminView')  # Cambia al nombre correcto

    def form_valid(self, form):
        # Incrementar el stock si se añadió nuevo stock
        nuevo_stock = form.cleaned_data.get('nuevo_stock')
        if nuevo_stock:
            self.object.stock += nuevo_stock
            self.object.save()

        # Manejar las imágenes adicionales
        images = self.request.FILES.getlist('additional_images')  # Recoger múltiples imágenes
        for image in images:
            ProductImage.objects.create(product=self.object, image=image)

        return super().form_valid(form)


class EliminarProductoView(DeleteView):
    model = Product
    template_name = 'pages/admin/eliminar_producto.html'
    success_url = reverse_lazy('ProductoAdminView')




class AnalizarProductoView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        # Total de vistas del producto
        total_vistas = product.product_views.count()

        # Total de compartidos y vistas desde enlaces compartidos
        total_compartidos = product.shared_products.count()
        total_vistas_compartidos = product.shared_products.aggregate(
            total_views=Sum('views_count')
        )['total_views'] or 0

        # Total de likes
        total_likes = product.total_likes

        # Total de comentarios
        total_comentarios = product.comment_set.count()

        context = {
            'product': product,
            'total_vistas': total_vistas,
            'total_compartidos': total_compartidos,
            'total_vistas_compartidos': total_vistas_compartidos,
            'total_likes': total_likes,
            'total_comentarios': total_comentarios,  # Añadimos al contexto
        }
        return render(request, 'pages/admin/analizar_producto.html', context)


class DetalleComentariosProductoView(ListView):
    model = Comment
    template_name = 'pages/admin/detalle_comentarios_producto.html'
    context_object_name = 'comentarios'

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        return Comment.objects.filter(product=product).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, id=self.kwargs.get('product_id'))
        return context


class DetalleCompartidosProductoView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        # Obtener todos los registros de compartidos
        compartidos = product.shared_products.all().order_by('-created_at')

        context = {
            'product': product,
            'compartidos': compartidos,
        }
        return render(request, 'pages/admin/detalle_compartidos_producto.html', context)




class ShareVisitDetailView(ListView):
    model = ShareVisit
    template_name = 'pages/admin/detalle_visitas_enlace.html'
    context_object_name = 'visitas'

    def get_queryset(self):
        # Obtener el enlace compartido desde el ID proporcionado
        share_id = self.kwargs.get('share_id')
        enlace_compartido = get_object_or_404(ProductShare, id=share_id)

        # Filtrar visitas relacionadas con este enlace compartido
        return ShareVisit.objects.filter(share=enlace_compartido).order_by('-visit_time')

    def get_context_data(self, **kwargs):
        # Agregar información del enlace compartido al contexto
        context = super().get_context_data(**kwargs)
        share_id = self.kwargs.get('share_id')
        context['enlace_compartido'] = get_object_or_404(ProductShare, id=share_id)
        return context





class DetalleVistasProductoView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        periodo = request.GET.get('periodo', 'dia')  # Filtro seleccionado

        # Definir el rango de fechas basado en el filtro
        if periodo == 'dia':
            inicio = now().replace(hour=0, minute=0, second=0)
        elif periodo == 'semana':
            inicio = now() - timedelta(days=7)
        elif periodo == 'mes':
            inicio = now() - timedelta(days=30)
        else:
            inicio = None  # Si no hay filtro, no limitar

        # Filtrar vistas según el rango de tiempo
        if inicio:
            vistas = product.product_views.filter(timestamp__gte=inicio).order_by('-timestamp')
        else:
            vistas = product.product_views.all().order_by('-timestamp')

        # Contar el total de vistas filtradas
        total_vistas_periodo = vistas.count()

        context = {
            'product': product,
            'vistas': vistas,
            'total_vistas_periodo': total_vistas_periodo,
        }
        return render(request, 'pages/admin/detalle_vistas_producto.html', context)



class CouponListView(View):
    def get(self, request):
        cupones = Coupon.objects.all().order_by('expiration_date')
        form = CouponForm()

        # Contar cupones activos e inactivos
        total_activos = Coupon.objects.filter(active=True).count()
        total_inactivos = Coupon.objects.filter(active=False).count()

        # Contar tipos de descuento
        total_porcentaje = Coupon.objects.filter(discount_type='percent').count()
        total_monto_fijo = Coupon.objects.filter(discount_type='fixed').count()

        context = {
            'cupones': cupones,
            'form': form,
            'total_activos': total_activos,
            'total_inactivos': total_inactivos,
            'total_porcentaje': total_porcentaje,
            'total_monto_fijo': total_monto_fijo,
        }
        return render(request, 'pages/admin/coupon_list.html', context)

    def post(self, request):
        if 'delete_selected' in request.POST:
            selected_ids = request.POST.getlist('selected_coupons')
            if selected_ids:
                return redirect('coupon_confirm_delete', selected_ids=",".join(selected_ids))
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
        cupones = Coupon.objects.all().order_by('expiration_date')
        return render(request, 'pages/admin/coupon_list.html', {'cupones': cupones, 'form': form})


class CouponDeleteConfirmView(View):
    def get(self, request, selected_ids):
        # Convertir la lista de IDs en objetos
        ids = selected_ids.split(',')
        cupones = Coupon.objects.filter(id__in=ids)
        return render(request, 'pages/admin/coupon_confirm_delete.html', {'cupones': cupones})

    def post(self, request, selected_ids):
        # Borrar los cupones seleccionados
        ids = selected_ids.split(',')
        Coupon.objects.filter(id__in=ids).delete()
        return redirect('coupon_list')





class OrderListView(View):
    def get(self, request):
        # Obtener parámetros de búsqueda y filtro
        search_query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')  # Por defecto ''

        # Diccionario para traducir los estados, incluyendo "Todos"
        estado_traducciones = {
            '': 'Todos',  # Opción adicional para mostrar todas las órdenes
            'pending': 'Pendiente',
            'approved': 'Pedido Aprobado',
            'dispatching': 'En Despacho',
            'shipped': 'Pedido Enviado',
            'delivered': 'Pedido Entregado',
            'completed': 'Completado',
            'cancelled': 'Cancelado',
        }

        # Base de la consulta de órdenes
        ordenes = Order.objects.all()

        # Aplicar búsqueda por número de orden o nombre de cliente
        if search_query:
            ordenes = ordenes.filter(
                Q(numero_orden__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        # Aplicar filtro por estado, si no es "Todos"
        if status_filter:
            ordenes = ordenes.filter(status=status_filter)

        # Ordenar por estado de pago confirmado y luego por fecha de creación
        ordenes = ordenes.order_by(
            Case(
                When(estado_pago='confirmed', then=Value(0)),  # Confirmados primero
                default=Value(1),
                output_field=IntegerField(),
            ),
            '-created_at'
        )

        # Totales por estado (incluyendo la opción "Todos")
        estado_totales = [
            (estado_traducciones[estado], Order.objects.filter(status=estado).count())
            for estado in estado_traducciones if estado  # Excluye la opción "Todos"
        ]

        # Opciones del filtro de estado traducidas
        status_choices = [(key, estado_traducciones[key]) for key in estado_traducciones]

        context = {
            'ordenes': ordenes,
            'search_query': search_query,
            'status_filter': status_filter,
            'estado_totales': estado_totales,
            'status_choices': status_choices,
        }
        return render(request, 'pages/admin/order_list.html', context)







class OrderDetailClienteView(View):
    def get(self, request, order_id):
        # Obtener la orden y los detalles de los productos
        orden = get_object_or_404(Order, id=order_id)
        items = orden.orderitem_set.all()

        context = {
            'orden': orden,
            'items': items,
            'direccion': orden.address,
            'cupon': orden.coupon,
        }
        return render(request, 'pages/admin/cliente_ordenes.html', context)






# Vista para listar perfiles pendientes
class PerfilesPendientesView(View):
    def get(self, request):
        perfiles_pendientes = Perfil.objects.filter(estado_verificacion='pendiente')
        return render(request, "pages/admin/perfiles_pendientes.html", {
            'perfiles_pendientes': perfiles_pendientes
        })

class RevisarPerfilView(View):
    def get(self, request, perfil_id):
        perfil = get_object_or_404(Perfil, id=perfil_id)
        direcciones = Address.objects.filter(user=perfil.usuario)
        return render(request, "pages/admin/revisar_perfil.html", {
            'perfil': perfil,
            'direcciones': direcciones,
        })

    def post(self, request, perfil_id):
        perfil = get_object_or_404(Perfil, id=perfil_id)
        estado = request.POST.get("estado_verificacion")
        comentario_rechazo = request.POST.get("comentario_rechazo", "")
        cuenta_verificada = request.POST.get("cuenta_verificada") == "on"

        perfil.estado_verificacion = estado
        perfil.cuenta_verificada = cuenta_verificada

        if estado == 'rechazado':
            perfil.comentario_rechazo = comentario_rechazo
        else:
            perfil.comentario_rechazo = None  # Limpiar comentario de rechazo si se aprueba

        perfil.save()

        return redirect("perfiles_pendientes")  # Redirigir a la lista de pendientes después de actualizar






class LoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'pages/admin/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "¡Bienvenido de nuevo!")
                return redirect('dasboard')
            else:
                messages.error(request, "Las credenciales son incorrectas.")
        else:
            messages.error(request, "Por favor, rellene todos los campos correctamente.")
        return render(request, 'pages/admin/login.html', {'form': form})

    



class AdminNotificationDashboardView(View):
    """Panel de control del administrador para gestionar notificaciones."""
    
    def get(self, request):
        groups = NotificationGroup.objects.all()  # Todos los grupos
        notifications = Notification.objects.all().order_by("-created_at")  # Todas las notificaciones

        notification_data = []
        for notification in notifications:
            read_count = NotificationReadStatus.objects.filter(notification=notification, is_read=True).count()
            total_users = notification.group.users.count() if notification.group else 1
            notification_data.append({
                "notification": notification,
                "read_count": read_count,
                "total_users": total_users,
            })

        context = {
            "groups": groups,
            "notification_data": notification_data,
        }
        return render(request, "pages/admin/notification_dashboard.html", context)

    def post(self, request, notification_id):
        """Marcar una notificación como leída o eliminarla."""
        action = request.POST.get("action")

        notification = get_object_or_404(Notification, id=notification_id)

        if action == "mark_as_read":
            # Marcar como leída para todos los usuarios
            NotificationReadStatus.objects.filter(notification=notification).update(is_read=True)
            messages.success(request, "Notificación marcada como leída.")
        elif action == "delete":
            notification.delete()
            messages.success(request, "Notificación eliminada correctamente.")
        
        return redirect("admin_notification_dashboard")



from datetime import datetime
from django.http import HttpResponseRedirect
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.edit import CreateView
from django.utils.timezone import now 
from django.contrib import messages
from django.utils.http import urlencode
from uuid import uuid4
from django.conf import settings 
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
import mercadopago
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from apps.coins.utils import gestion_coins 
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from apps.perfil.models import *
from apps.perfil.forms import *
from apps.shops.forms import *
from .models import *


#Crea una notificación interna para el usuario apuntando a 'detalle_compra'.
def create_order_notification(order):
 
    try:
        
        target_link = reverse('detalle_compra', args=[order.id])
        
        Notification.objects.create(
            recipient=order.user,
            title=f"¡Pago Aprobado! Orden #{order.id}",
            message=f"Tu compra de ${order.monto_total} fue confirmada exitosamente. Toca aquí para ver el detalle en tu historial.",
            link=target_link,
            notification_type='general' # O el tipo que prefieras de tu lista
        )
        
        
    except Exception as e:
        print(f"❌ Error creando notificación interna: {e}")


#   enviar correo de confirmación de orden con mensaje personalizado
def send_order_confirmation_email(order, request):
    try:
        subject = f'📦 Orden #{order.id} Confirmada - Silo'
        domain = "https://dcollet-katelynn-trinal.ngrok-free.dev" # <--- TU NGROK
        
        order_url = f"{domain}{reverse('order_detail', args=[order.id])}"
        
       
        custom_message = None
        
        # EJEMPLO 1: Si es un usuario específico (Tú)
        if order.user.email == "tu_email@ejemplo.com":
            custom_message = "¡Hola Admin! Gracias por probar el sistema. Todo funciona de 10."
            
        # EJEMPLO 2: Si gastó mucho dinero (Estrategia de Fidelización)
        elif order.monto_total > 50000:
            custom_message = "🎁 ¡Eres un cliente VIP! Por esta compra ganaste un Cupón de 10% OFF para la próxima: SILO-VIP-10"
            
        # EJEMPLO 3: Mensaje estándar aleatorio o vacío
        # else:
        #    custom_message = "Esperamos que disfrutes tu compra."

        # Preparar ítems
        order_items = []
        for item in order.orderitem_set.all():
            img_url = ""
            if item.product.image:
                img_url = f"{domain}{item.product.image.url}"
            
            order_items.append({
                'title': item.product.title,
                'quantity': item.quantity,
                'price': item.price,
                'image': img_url
            })

        html_message = render_to_string('emails/email_order_success.html', {
            'order': order,
            'user': order.user,
            'order_items': order_items,
            'order_url': order_url,
            'domain': domain,
            'year': timezone.now().year,
            'custom_message': custom_message # <--- Pasamos el mensaje a la vista
        })
        
        plain_message = strip_tags(html_message)
        from_email = 'Silo Tienda <ventas@silo.com>'
        to_email = order.user.email

        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
        print(f"📧 Email enviado a {to_email}")
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")



class HomeShopView(View):
    def get(self, request):
        # 1. Obtener parámetros de la URL
        category_param = request.GET.get('category')
        sort_param = request.GET.get('sort')
        
        # 2. Filtrado base: Productos con stock
        products = Product.objects.filter(stock__gt=0)
        
        # 3. Lógica de Filtrado por Categoría u Ofertas
        now = timezone.now()

        if category_param == 'ofertas':
            # Filtro especial para Ofertas Flash
            products = products.filter(
                is_daily_offer=True,
                offer_start_date__lte=now,
                offer_end_date__gte=now
            )
        elif category_param and category_param != 'all':
            # Intenta filtrar por nombre de categoría (ya que tu HTML envía texto como 'tecnologia')
            # Si tus links enviaran ID, usarías category_id=category_param
            products = products.filter(category__name__iexact=category_param)

        # 4. Lógica de Ordenamiento (Sorting)
        if sort_param == 'price_asc':
            products = products.order_by('price')
        elif sort_param == 'price_desc':
            products = products.order_by('-price')
        elif sort_param == 'newest':
            products = products.order_by('-created_at')
        else:
            # Orden aleatorio por defecto si no se elige nada
            products = products.order_by('?')

        # 5. Paginación
        paginator = Paginator(products, 5) # 5 productos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        categories = Category.objects.all()

        # 6. Determinar estado (Promoción, Oferta, Normal) para el frontend
        # Nota: Usamos la fecha 'now' que definimos arriba
        products_with_status = []
        for product in page_obj:
            status = "Normal"
            
            # Chequeo de Promoción
            if product.is_currently_promotional:
                status = "Promoción"
            # Chequeo de Oferta Diaria
            elif (product.is_daily_offer and 
                  product.offer_start_date and 
                  product.offer_end_date and 
                  product.offer_start_date <= now <= product.offer_end_date):
                status = "Oferta"
            
            products_with_status.append({
                "product": product,
                "status": status
            })

        context = {
            'products': products_with_status,
            'categories': categories,
            'selected_category': category_param, # Para mantener el botón activo en el HTML
            'selected_sort': sort_param,         # Para saber qué orden está activo (opcional)
            'page_obj': page_obj,
        }
        return render(request, "pages/web/shop.html", context)


class HomeShoptCategoriaView(View):
    def get(self, request, *args, **kwargs):
        category_name = kwargs.get('category_name')

        products = Product.objects.filter(stock__gt=0)

        if category_name:
            try:
                category = Category.objects.get(name__iexact=category_name)
                products = products.filter(category=category)
            except Category.DoesNotExist:
                products = Product.objects.none()
        # Ordenar aleatoriamente
        products = products.order_by('?')  # Cambiar el orden cada vez que se carga la página

        # Paginación
        paginator = Paginator(products, 5)  # Mostrar 5 productos por página
        page_number = request.GET.get('page')  # Obtiene el número de la página actual
        page_obj = paginator.get_page(page_number)

        categories = Category.objects.all()

        # Obtener la fecha y hora actual como naive
        now = datetime.now()

        # Determinar el estado de cada producto
        products_with_status = [
            {
                "product": product,
                "status": (
                    "Promoción" if product.is_currently_promotional else
                    "Oferta" if product.is_daily_offer and product.offer_start_date and product.offer_end_date and product.offer_start_date.replace(tzinfo=None) <= now <= product.offer_end_date.replace(tzinfo=None) else
                    "Normal"
                )
            }
            for product in page_obj
        ]

        context = {
            'products': products_with_status,
            'categories': categories,
            'selected_category': category_name,
            'page_obj': page_obj,  # Agregar page_obj para la navegación
        }
        return render(request, "pages/web/shop.html", context)

class DetalleShotView(View):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # Verificar si el producto tiene stock
        if product.stock <= 0:
            # El producto no tiene stock, redirigir con mensaje
            messages.error(request, "Este producto no está disponible actualmente o ha sido eliminado.")
            return redirect('shop')

        # Obtener la IP del cliente
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Registrar vista del producto
        if request.user.is_authenticated:
            ProductView.objects.create(product=product, user=request.user, ip_address=ip_address)
        else:
            if not request.session.session_key:
                request.session.create()
            ProductView.objects.create(product=product, session_id=request.session.session_key, ip_address=ip_address)

        # Determinar el estado del producto
        if product.is_currently_promotional:
            status = "Promoción"
        elif product.is_daily_offer and product.offer_start_date and product.offer_end_date and product.offer_start_date <= now() <= product.offer_end_date:
            status = "Oferta"
        else:
            status = "Normal"

        # Obtener productos relacionados por categoría, pero solo si hay suficientes
        related_products = Product.objects.filter(category=product.category).exclude(id=product_id)  # Filtrar por la misma categoría
        total_related = related_products.count()

        if total_related > 0:
            # Asegurarse de que no pidamos más productos de los que hay disponibles
            num_related_products = 3  # Puedes ajustar este número
            num_to_sample = min(num_related_products, total_related)
            related_products = related_products[:num_to_sample]  # Tomar los primeros productos relacionados disponibles
        else:
            related_products = []

        context = {
            'product': product,
            'images': product.images.all(),
            'status': status,  # Agregar estado al contexto
            'related_products': related_products,
        }
        return render(request, 'pages/web/shops_detalle.html', context)

  
class GenerateShareLinkView(View):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # Genera un identificador único para el enlace
        share_id = uuid4().hex
        share_link = f"{request.build_absolute_uri('/share/')}{product_id}?share_id={share_id}"

        # Obtener la IP del cliente
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0]

        # Guarda el evento de compartir
        ProductShare.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            session_id=request.session.session_key,
            ip_address=ip_address,
            share_link=share_link
        )

        # Incrementa el contador de compartidos
        product.share_count += 1
        product.save()

        # Retornar el enlace generado como JSON
        return JsonResponse({'share_link': share_link})



class ShareProductView(View):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        share_id = request.GET.get('share_id')
        
        product = get_object_or_404(Product, id=product_id)
        # Traemos al usuario dueño del link
        product_share = ProductShare.objects.select_related('user').filter(
            share_link__contains=share_id, 
            product=product
        ).first()
        
        if not product_share:
            return redirect('product_detail', product_id=product.id)

        # 1. Identificar al visitante
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0]
            
        visitor_user = request.user if request.user.is_authenticated else None
        
        # 2. Verificar si es una visita nueva
        es_dueno = (visitor_user == product_share.user)
        ya_visitado = ShareVisit.objects.filter(share=product_share, ip_address=ip_address).exists()
        if visitor_user and not ya_visitado:
            ya_visitado = ShareVisit.objects.filter(share=product_share, user=visitor_user).exists()

        # 3. Procesar contador solo si es visita válida (No dueño, No repetida)
        if not ya_visitado and not es_dueno:
            try:
                with transaction.atomic():
                    ShareVisit.objects.create(
                        share=product_share,
                        product=product,
                        user=visitor_user,
                        ip_address=ip_address
                    )
                    product_share.views_count += 1
                    product_share.save()
                    
                    product.views_count += 1
                    product.save()
            except Exception as e:
                print(f"Error al registrar visita: {e}")

        # 4. VERIFICACIÓN DE PAGO (Fuera del IF de visita para que sea redundante)
        # Si las vistas llegaron a la meta y NO ha cobrado el premio
        if product_share.views_count >= product_share.META_VISTAS and not product_share.reward_claimed:
            try:
                with transaction.atomic():
                    # Bloqueamos la fila para evitar pagos dobles en milisegundos
                    ps_to_pay = ProductShare.objects.select_for_update().get(pk=product_share.pk)
                    
                    if not ps_to_pay.reward_claimed:
                        exito, nuevo_saldo = gestion_coins(
                            user=ps_to_pay.user,
                            amount=ps_to_pay.PREMIO_COINS,
                            tipo='BONUS', 
                            descripcion=f"Meta {ps_to_pay.META_VISTAS} vistas: {product.title}"
                        )
                        
                        if exito:
                            ps_to_pay.reward_claimed = True
                            ps_to_pay.save()
                            print(f"✅ Pago realizado a {ps_to_pay.user.username}")
            except Exception as e:
                print(f"Error en proceso de pago: {e}")

        return redirect('product_detail', product_id=product.id)


#vista para añadir producto que le gusta al usuarios
class LikeProductView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # Si el usuario ya le ha dado "like", se quita (toggle)
        if request.user in product.likes.all():
            product.likes.remove(request.user)  # Elimina el "like"
        else:
            product.likes.add(request.user)  # Añade el "like"

        # Redirigir a la página anterior (donde se hizo la acción)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class CarritoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product')  # Optimiza las consultas
        coupon_form = CouponForm()  # Formulario para cupones

        # Calcula el subtotal sin descuento
        subtotal_original = sum(item.total_price() for item in cart.items.all())
        
        context = {
            'cart': cart,
            'items': items,
            'total_count': cart.count_products(),
            'total_price': cart.total_price(),  # Total con descuento aplicado
            'subtotal_original': subtotal_original,  # Total original sin descuento
            'coupon_form': coupon_form,
        }
        return render(request, 'pages/web/carrito.html', context)


    def post(self, request, *args, **kwargs):
        cart = get_object_or_404(Cart, user=request.user)
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code=code, active=True)
                if not coupon.is_valid():
                    messages.error(request, "El cupón no es válido o ya ha sido utilizado.")
                else:
                    cart.coupon = coupon
                    cart.save()
                    coupon.used = True  # Marcar el cupón como utilizado
                    coupon.save()
                    messages.success(request, "¡Cupón aplicado exitosamente!")
            except Coupon.DoesNotExist:
                messages.error(request, "El código de cupón no existe.")
        return redirect('cart')


class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        cart.add_product(product, quantity)
        return redirect('cart')


class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart = get_object_or_404(Cart, user=request.user)
        cart.remove_product(product)
        return redirect('cart')


class DecreaseQuantityView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart.remove_product(product)
        return redirect('cart')


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)

        try:
            perfil = request.user.perfil
        except Perfil.DoesNotExist:
            messages.error(request, "No tienes un perfil configurado.")
            return redirect('data_profile')

        other_addresses = request.user.address.filter(is_default=False)
        default_address = None
        if perfil.estado_verificacion == 'aprobado':
            default_address = request.user.address.filter(is_default=True).first()

        context = {
            'cart': cart,
            'default_address': default_address,
            'other_addresses': other_addresses,
            'perfil': perfil,
        }
        return render(request, 'pages/web/checkout.html', context)

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method')

        if not address_id or not payment_method:
            messages.error(request, "Por favor selecciona dirección y método de pago.")
            return redirect('checkout')

        perfil = request.user.perfil
        default_address = request.user.address.filter(is_default=True).first()

        # 1. Efectivo / Transferencia
        if perfil.estado_verificacion == 'aprobado' and payment_method in ['cash', 'transfer']:
            if str(address_id) != str(default_address.id):
                messages.error(request, "Solo puedes usar tu dirección predeterminada para pagar con efectivo.")
                return redirect('checkout')

            order = Order.objects.create(
                user=request.user, cart=cart, address_id=address_id,
                payment_method=payment_method, confirm_token=uuid.uuid4(),
                estado_pago='pending', status='pending', is_paid=False, monto_total=cart.total_price()
            )
            for item in cart.items.all():
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
            cart.items.all().delete()
            cart.clear_coupon()
            return redirect('payment_transfer_cash')

        # 2. Tarjeta (Brick API Interno)
        if payment_method == 'card_manual':
            request.session['address_id'] = address_id
            return redirect('payment_card')

        # 3. Mercado Pago Link (Redirección Externa)
        elif payment_method == 'mp_redirect':
            request.session['address_id'] = address_id
            return redirect('payment_mercadopago')

        # 4. QR MODAL (Server Side Render con Auto-Open)
        elif payment_method == 'qr_modal':
            # A. Crear la Orden
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user, cart=cart, address_id=address_id, coupon=cart.coupon,
                        payment_method='qr', status='pending', estado_pago='pending',
                        monto_total=cart.total_price(), fecha_entrega_estimada=timezone.now() + timedelta(days=5)
                    )
                    for item in cart.items.all():
                        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
            except Exception as e:
                messages.error(request, f"Error al generar orden: {e}")
                return redirect('checkout')

            # B. Generar Preferencia MP
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            
            # --- ACTUALIZA TU NGROK AQUÍ ---
            domain = "https://dcollet-katelynn-trinal.ngrok-free.dev" 
            
            items_mp = [{"title": i.product.title, "quantity": i.quantity, "currency_id": "ARS", "unit_price": float(i.price)} for i in order.orderitem_set.all()]

            # --- CORRECCIÓN DE RUTAS CON REVERSE ---
            # Esto genera '/shops/webhooks/mercadopago/' automáticamente
            webhook_path = reverse('mp_webhook') 
            success_path = reverse('order_detail', args=[order.id])
            failure_path = reverse('checkout')

            expiration_minutes = 15
            expiration_date = (timezone.now() + timedelta(minutes=expiration_minutes)).isoformat()

            preference_data = {
                "items": items_mp,
                "payer": { "email": request.user.email },
                "back_urls": {
                    "success": f"{domain}{success_path}",
                    "failure": f"{domain}{failure_path}",
                    "pending": f"{domain}{failure_path}"
                },
                "auto_return": "approved",
                "external_reference": str(order.id),
                "notification_url": f"{domain}{webhook_path}", # <--- URL CORRECTA
                "binary_mode": True,
                "expires": True, 
                "date_of_expiration": expiration_date
            }
            
            pref = sdk.preference().create(preference_data)["response"]
            
            TransaccionMercadoPago.objects.create(orden=order, preference_id=pref["id"], status='qr_generated', raw_response=pref)

            # C. Datos para el Modal (Incluimos la URL del checker)
            # reverse genera: '/shops/order/check-status/44/'
            check_url_relative = reverse('check_order_status', args=[order.id])

            qr_data = {
                'url': pref["init_point"],
                'order_id': order.id,
                'total': float(cart.total_price()),
                'minutes': expiration_minutes,
                'check_url': check_url_relative # <--- URL CORRECTA PARA JS
            }

            # D. Renderizamos la misma página pero con el modal activo
            context = {
                'cart': cart,
                'default_address': default_address,
              
                'perfil': perfil,
                'qr_data_active': True,  # Bandera para abrir modal
                'qr_data': json.dumps(qr_data)
            }
            return render(request, 'pages/web/checkout.html', context)

        messages.error(request, "Método de pago no válido.")
        return redirect('checkout')

class PaymentCardView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return redirect('shop')

        address_id = request.session.get('address_id')
        if not address_id:
            return redirect('checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        context = {
            'address': address,
            'cart': cart,
            'mp_public_key': settings.MERCADOPAGO_PUBLIC_KEY 
        }
        return render(request, 'pages/web/payment_card.html', context)

    def post(self, request):
        try:
            payment_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)

        cart = Cart.objects.filter(user=request.user).first()
        address_id = request.session.get('address_id')
        
        # 1. CREAMOS LA ORDEN PRIMERO (Estado: Pendiente)
        # Esto nos permite guardar el registro del intento fallido si ocurre.
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    cart=cart,
                    address_id=address_id,
                    coupon=cart.coupon,
                    estado_pago='pending', # Empieza pendiente
                    status='pending',
                    payment_method='card',
                    is_paid=False,
                    monto_total=cart.total_price(),
                    fecha_entrega_estimada=timezone.now() + timedelta(days=5)
                )

                # Guardamos los items inmediatamente para que la orden tenga contenido
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price
                    )
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Error creando orden inicial'}, status=500)

        # 2. PROCESAR PAGO CON MERCADO PAGO
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        payment_request = {
            "transaction_amount": float(cart.total_price()),
            "token": payment_data.get('token'),
            "description": f"Pedido #{order.numero_orden} - {request.user.username}",
            "installments": int(payment_data.get('installments', 1)),
            "payment_method_id": payment_data.get('payment_method_id'),
            "payer": {
                "email": payment_data.get('payer').get('email'),
                "identification": {
                    "type": payment_data.get('payer').get('identification').get('type'),
                    "number": payment_data.get('payer').get('identification').get('number')
                }
            },
            # Vinculamos el pago a la orden que acabamos de crear
            "external_reference": str(order.id) 
        }

        payment_response = sdk.payment().create(payment_request)
        payment = payment_response.get("response", {})
        status = payment.get("status")
        status_detail = payment.get("status_detail")

        # 3. GUARDAR EL LOG (Sea éxito o fracaso, ahora SÍ se guarda)
        TransaccionMercadoPago.objects.create(
            orden=order,
            payment_id=str(payment.get("id")),
            status=status,
            status_detail=status_detail,
            raw_response=payment
        )

        # 4. DECIDIR QUÉ HACER SEGÚN EL RESULTADO
        if status == 'approved':
            # Actualizamos la orden a Pagada
            order.is_paid = True
            order.estado_pago = 'confirmed'
            order.status = 'approved'
            order.save()

            # Vaciamos el carrito
            cart.items.all().delete()
            cart.clear_coupon()
            send_order_confirmation_email(order, request)
            create_order_notification(order)

            return JsonResponse({
                'status': 'approved', 
                'order_id': order.id,
                'redirect_url': reverse('order_detail', args=[order.id])
            })
        
        else:
            # Si falló, marcamos la orden como fallida (opcional, o la dejamos pendiente)
            order.status = 'failed' 
            order.estado_pago = 'failed'
            order.save()
            
            # Devolvemos el error al frontend para mostrar la alerta bonita
            return JsonResponse({
                'status': 'rejected', 
                'status_detail': status_detail, # Ej: cc_rejected_insufficient_amount
                'message': 'El pago no pudo ser procesado.'
            })

class PaymentMercadoPagoView(LoginRequiredMixin, View):
    def get(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            messages.warning(request, "Tu carrito está vacío.")
            return redirect('shop')

        address_id = request.session.get('address_id')
        if not address_id:
            messages.error(request, "Falta dirección de envío.")
            return redirect('checkout')
        
        shipping_address = get_object_or_404(Address, id=address_id, user=request.user)

        # 1. Crear Orden
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    cart=cart,
                    address_id=address_id,
                    coupon=cart.coupon,
                    payment_method='mercadopago', # Link / Checkout Pro
                    status='pending',
                    estado_pago='pending',
                    monto_total=cart.total_price(),
                    fecha_entrega_estimada=timezone.now() + timedelta(days=5)
                )
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order, product=item.product, quantity=item.quantity, price=item.product.price
                    )
        except Exception as e:
            messages.error(request, f"Error iniciando pago: {e}")
            return redirect('checkout')

        # 2. Configurar SDK
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        items_mp = []
        for item in order.orderitem_set.all():
            img_url = request.build_absolute_uri(item.product.image.url) if item.product.image else ""
            items_mp.append({
                "id": str(item.product.id),
                "title": item.product.title,
                "description": item.product.description[:200] if item.product.description else "Producto de la tienda",
                "picture_url": img_url,
                "quantity": item.quantity,
                "currency_id": "ARS",
                "unit_price": float(item.price)
            })

        # --- URL NGROK ---
        domain = "https://dcollet-katelynn-trinal.ngrok-free.dev" # <--- ¡VERIFICA QUE SEA LA ACTUAL!
        
        # --- CORRECCIÓN CLAVE AQUÍ ---
        # Usamos reverse para que Django ponga el prefijo correcto (/shops/...)
        webhook_path = reverse('mp_webhook') 
        success_path = reverse('order_detail', args=[order.id])
        failure_path = reverse('checkout')

        payer_info = { 
            "name": request.user.first_name or "Usuario",
            "surname": request.user.last_name or "Prueba",
            "email": request.user.email,
        }

        if hasattr(request.user, 'perfil') and request.user.perfil.numero_telefono:
            payer_info["phone"] = {
                "area_code": "",
                "number": request.user.perfil.numero_telefono
            }

        preference_data = {
            "items": items_mp,
            "payer": payer_info,
            "back_urls": {
                "success": f"{domain}{success_path}",
                "failure": f"{domain}{failure_path}",
                "pending": f"{domain}{failure_path}"
            },
            "auto_return": "approved", 
            "external_reference": str(order.id),
            
            # AQUÍ ESTABA EL ERROR: Ahora usamos la ruta generada dinámicamente
            "notification_url": f"{domain}{webhook_path}",
            
            "binary_mode": True,
            "statement_descriptor": "MI ECOMMERCE",
            "expires": True,
            "date_of_expiration": (timezone.now() + timedelta(hours=24)).isoformat()
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        TransaccionMercadoPago.objects.create(
            orden=order,
            preference_id=preference["id"],
            status='preference_created',
            raw_response=preference
        )

        url_pago = preference["sandbox_init_point"] if settings.DEBUG else preference["init_point"]
        return redirect(url_pago)


@method_decorator(csrf_exempt, name='dispatch')
class MercadoPagoWebhookView(View):
    def post(self, request):
        topic = request.GET.get('topic') or request.GET.get('type')
        p_id = request.GET.get('id') or request.GET.get('data.id')

        print(f"🔔 WEBHOOK: Topic={topic} | ID={p_id}")

        if not p_id:
            return HttpResponse(status=400)

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Variables para guardar lo que encontremos
        payment_status = None
        external_reference = None
        payment_data = {}

        # ESTRATEGIA 1: Buscar como PAGO (Payment)
        if topic == 'payment':
            payment_info = sdk.payment().get(p_id)
            if payment_info["status"] == 200:
                payment_data = payment_info["response"]
                payment_status = payment_data.get('status')
                external_reference = payment_data.get('external_reference')
                print(f"✅ PAGO ENCONTRADO: Status={payment_status} | Ref={external_reference}")
            else:
                print(f"⚠️ Error buscando pago: {payment_info}")

        # ESTRATEGIA 2: Buscar como ORDEN COMERCIAL (Merchant Order)
        # Los pagos QR a veces llegan primero como merchant_order
        elif topic == 'merchant_order':
            mo_info = sdk.merchant_order().get(p_id)
            if mo_info["status"] == 200:
                mo_data = mo_info["response"]
                # Buscamos si hay pagos dentro de la orden comercial
                payments = mo_data.get('payments', [])
                if payments:
                    last_payment = payments[-1] # Tomamos el último
                    payment_status = last_payment.get('status')
                    external_reference = mo_data.get('external_reference')
                    payment_data = last_payment
                    print(f"✅ MERCHANT ORDER: Status={payment_status} | Ref={external_reference}")

        # --- PROCESAMIENTO ---
        if external_reference and payment_status:
            try:
                order = Order.objects.get(id=external_reference)
                
                # Guardar Log (Evitamos duplicados si ya existe el mismo payment_id)
                if not TransaccionMercadoPago.objects.filter(payment_id=str(p_id)).exists():
                    TransaccionMercadoPago.objects.create(
                        orden=order,
                        payment_id=str(p_id),
                        status=payment_status,
                        status_detail=payment_data.get('status_detail', 'via_webhook'),
                        raw_response=payment_data
                    )

                # APROBAR ORDEN
                if payment_status == 'approved':
                    if not order.is_paid:
                        order.is_paid = True
                        order.estado_pago = 'confirmed'
                        order.status = 'approved'
                        order.save()
                        
                        # Limpiar carrito
                        order.cart.items.all().delete()
                        order.cart.clear_coupon()
                        print(f"🎉 ORDEN {order.id} APROBADA CORRECTAMENTE")
                        send_order_confirmation_email(order, request)
                        create_order_notification(order)
                    else:
                        print(f"ℹ️ La orden {order.id} ya estaba pagada.")
            
            except Order.DoesNotExist:
                print(f"❌ Error: La orden ID {external_reference} no existe en la base de datos.")
            except Exception as e:
                print(f"❌ Error procesando orden: {e}")

        return HttpResponse(status=200)



def check_order_status(request, order_id):
    """
    Esta vista es consultada por Javascript cada 3 segundos.
    Verifica si el Webhook ya marcó la orden como pagada.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=403)
        
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        if order.is_paid or order.status == 'approved':
             # Si ya se pagó, le damos la URL de éxito
             return JsonResponse({
                 'status': 'approved', 
                 'redirect_url': reverse('order_detail', args=[order.id])
             })
        
        return JsonResponse({'status': 'pending'})
    
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


  
class PaymentTransferCashView(LoginRequiredMixin, View):
    def get(self, request):
    
        return render(request, 'pages/web/payment_transfer_cash.html')
    
class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order_items = order.orderitem_set.all()
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'pages/web/order_detail.html', context)
    

# Vista CREAR
class AddAddressView(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'pages/web/add_address.html'
    success_url = reverse_lazy('checkout')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Dirección creada correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context

# Vista EDITAR
class EditAddressView(LoginRequiredMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'pages/web/add_address.html'
    success_url = reverse_lazy('checkout')

    def get_queryset(self):
        # Solo permite editar direcciones del propio usuario
        return Address.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'edit'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Dirección actualizada correctamente.")
        return super().form_valid(form)
    
    # Esto ayuda a depurar: si falla, imprime errores en la consola del servidor
    def form_invalid(self, form):
        print("Errores del formulario:", form.errors)
        return super().form_invalid(form)

# Vista ELIMINAR
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Dirección eliminada.")
    return redirect('checkout')


class ShopOfertasView(View):
    def get(self, request):
        hora_actual = now()  # Hora actual para manejar las zonas horarias

        # Productos promocionales
        promotional_products = Product.objects.filter(
            is_promotional=True,
            promotion_start_date__lte=hora_actual,
            promotion_end_date__gte=hora_actual
        )

        # Ofertas del día
        daily_offers = Product.objects.filter(
            is_daily_offer=True,
            offer_start_date__lte=hora_actual,
            offer_end_date__gte=hora_actual
        )

        context = {
            "promotional_products": promotional_products,
            "daily_offers": daily_offers,
        }

        return render(request, "pages/web/ofertas.html", context)



class CommentCreateView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'pages/web/leave_comment.html'

    def dispatch(self, request, *args, **kwargs):
        # Validamos que el producto exista
        self.product = get_object_or_404(Product, id=self.kwargs['product_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product  # Añadimos el producto al contexto
        # Verificamos si el usuario ya ha comentado este producto
        if Comment.objects.filter(user=self.request.user, product=self.product).exists():
            context['already_commented'] = True
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['product'] = self.product
        return kwargs

    def form_valid(self, form):
        # Guardar el comentario y redirigir al mismo formulario con un mensaje de éxito
        form.instance.user = self.request.user
        form.instance.product = self.product
        form.save()
        messages.success(self.request, "Tu comentario ha sido agregado con éxito.")
        return redirect(self.request.path_info)  # Redirige a la misma vista

    def form_invalid(self, form):
        messages.error(self.request, "Hubo un error con tu comentario.")
        return super().form_invalid(form)












from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.utils.html import strip_tags
from django.template.loader import render_to_string



from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.urls import reverse
from apps.perfil.forms import AddressForm, CouponForm
from apps.shops.forms import CommentForm
from django.views.generic.edit import CreateView
from .models import *
from django.utils.timezone import now  # Importa timezone
from apps.perfil.models import *
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode
from uuid import uuid4
from django.conf import settings 
from django.http import HttpResponse

class HomeShopView(View):
    def get(self, request):
        category_id = request.GET.get('category')
        
        # Filtrar productos con stock mayor a 0
        products = Product.objects.filter(stock__gt=0)

        # Si hay una categoría seleccionada, filtrar también por categoría
        if category_id:
            products = products.filter(category_id=category_id)

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
            'selected_category': category_id,
            'page_obj': page_obj,  # Agregar page_obj para la navegación
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
        product = get_object_or_404(Product, id=product_id)

        # Obtenemos el share_id de la URL
        share_id = request.GET.get('share_id')
        user = request.user if request.user.is_authenticated else None

        # Si el share_id está presente, encontrar el objeto ProductShare
        product_share = ProductShare.objects.filter(share_link__contains=share_id, product=product).first()
        
        if product_share:
            # Crear un registro de la visita
            ShareVisit.objects.create(
                share=product_share,
                product=product,
                user=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            # Incrementar el contador de vistas solo si no existe un registro previo para esta IP o usuario
            if not ShareVisit.objects.filter(
                share=product_share,
                product=product,
                ip_address=request.META.get('REMOTE_ADDR'),
                user=user
            ).exists():
                product.views_count += 1
                product.save()

            # Incrementar el contador de vistas del enlace compartido
            product_share.views_count += 1
            product_share.save()

        # Redirigir a la página de detalles del producto
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

        # Verifica si el perfil del usuario existe
        try:
            perfil = request.user.perfil
        except Perfil.DoesNotExist:
            messages.error(request, "No tienes un perfil configurado.")
            return redirect('data_profile')

        # Direcciones adicionales siempre visibles
        other_addresses = request.user.address.filter(is_default=False)

        # Dirección predeterminada solo visible si el perfil está aprobado
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

        if perfil.estado_verificacion == 'aprobado' and payment_method in ['cash', 'transfer']:
            if str(address_id) != str(default_address.id):
                messages.error(request, "Solo puedes usar tu dirección predeterminada para pagar con efectivo o transferencia.")
                return redirect('checkout')

            # Crear Order
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                address_id=address_id,
                payment_method=payment_method,
                confirm_token=uuid.uuid4(),
                estado_pago='pending',
                status='pending',
                is_paid=False
            )

            # Copiar ítems del carrito al pedido
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Mostrar el link en consola (simula envío por correo)
            link = request.build_absolute_uri(
                reverse('confirmar_pedido') + f'?token={order.confirm_token}'
            )
            
            # Enviar correo al usuario
            html_message = render_to_string("emails/confirmar_pedido.html", {
                "user": request.user,
                "link": link
            })

            send_mail(
                subject='Confirma tu pedido',
                message=strip_tags(html_message),
                from_email='OA Ecommerce <hugor8819@gmail.com>',
                recipient_list=[request.user.email],
                html_message=html_message,
                fail_silently=False,
            )

            return redirect('payment_transfer_cash')  # Vista que dice "revisa tu correo"

        # Para tarjeta, lógica normal
        request.session['address_id'] = address_id
        request.session['payment_method'] = payment_method
        return redirect('payment_card')



class PaymentCardView(LoginRequiredMixin, View):
    def get(self, request):
        address_id = request.session.get('address_id')
        if not address_id:
            messages.error(request, "No se ha seleccionado dirección.")
            return redirect('checkout')

        address = get_object_or_404(Address, id=address_id, user=request.user)
        context = {
            'address': address,
        }
        return render(request, 'pages/web/payment_card.html', context)

    def post(self, request):
        # Obtener datos y validar tarjeta
        card_number = request.POST.get('card_number')
        expiration_date = request.POST.get('expiration_date')
        cvv = request.POST.get('cvv')

        if not all([card_number, expiration_date, cvv]):
            messages.error(request, "Por favor completa todos los campos de la tarjeta.")
            return redirect('payment_card')

        # Crear la orden
        address_id = request.session.get('address_id')
        address = get_object_or_404(Address, id=address_id, user=request.user)
        cart = get_object_or_404(Cart, user=request.user)
        

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                address=address,
                coupon=cart.coupon,
                estado_pago='confirmed',
                payment_method='card',
                monto_total=cart.total_price(),
                fecha_entrega_estimada=timezone.now() + timedelta(hours=12)
            )
            
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price * item.quantity
                )

        # Procesar productos del carrito
        cart_items = cart.items.all()
        
        comment_urls = []
        for item in cart_items:
            product = item.product
            comment_url = CommentURL.objects.create(
                order=order,
                product=product,
                user=request.user,
                url=f"{settings.SITE_URL}{reverse('leave_comment', args=[product.id])}"
            )
            print(f"URL para comentar sobre {product.title}: {comment_url.url}")

        words = ["tienda", "perro", "azul", "cielo", "montaña", "fresa", "lago", "árbol", "sol", "estrella"]
        order.delivery_code = random.choice(words)
        order.save()

        # Vaciar el carrito
        cart.items.all().delete()
        cart.clear_coupon()
        messages.success(request, "Tu pedido ha sido creado exitosamente.")
        return redirect('order_detail', order_id=order.id)




    
class PaymentTransferCashView(LoginRequiredMixin, View):
    def get(self, request):
    
        return render(request, 'pages/web/payment_transfer_cash.html')
    



class ConfirmarPedidoTokenView(LoginRequiredMixin, View):
    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponse("Token inválido.", status=400)

        try:
            order = Order.objects.get(confirm_token=token, confirmado_por_token=False)
        except Order.DoesNotExist:
            return HttpResponse("Este enlace ya fue usado o no es válido.")

        # Validar que el usuario autenticado es el dueño del pedido
        if request.user != order.user:
            return HttpResponseForbidden("No tienes permiso para confirmar este pedido.")

        # Confirmar pedido
        order.confirmado_por_token = True
        order.status = 'pending'
        order.save()

        # Vaciar el carrito
        order.cart.items.all().delete()
        order.cart.clear_coupon()

        return render(request, 'pages/web/pedido_confirmado.html', {
            "pedido": order,
            "codigo_retiro": str(order.confirm_token).split("-")[0].upper()
        })

        



class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order_items = order.orderitem_set.all()  # Accede a los productos de la orden
        context = {
            'order': order,
            'order_items': order_items,
        }
        return render(request, 'pages/web/order_detail.html', context)



class AddAddressView(LoginRequiredMixin, View):
    def get(self, request):
        form = AddressForm()
        return render(request, 'pages/web/add_address.html', {'form': form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('checkout')  # Redirigir a la página de checkout
        return render(request, 'pages/web/add_address.html', {'form': form})







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












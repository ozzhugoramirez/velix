import random
import string
import uuid
from django.db import models
from django.conf import settings
from apps.shops.models import Product
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings
from django.urls import reverse


class Perfil(models.Model):
    ESTADOS_VERIFICACION = [
        ('verificar', 'Verificar'),
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    estado_verificacion = models.CharField(
        max_length=10,
        choices=ESTADOS_VERIFICACION,
        default='verificar'
    )
    comentario_rechazo = models.TextField(null=True, blank=True) 

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    numero_telefono = models.CharField(max_length=15, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=10, choices=[('masculino', 'Masculino'), ('femenino', 'Femenino'), ('otro', 'Otro')], null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    ultimo_inicio_sesion = models.DateTimeField(auto_now=True)
    suscripcion_boletin = models.BooleanField(default=False)
    cuenta_verificada = models.BooleanField(default=False)
    puntos_fidelidad = models.PositiveIntegerField(default=0)
    codigo_referido = models.CharField(max_length=10, null=True, blank=True, unique=True)
    coins = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def es_parcialmente_completo(self):
        # Verifica si todos los campos requeridos están completos
        return all([
            self.numero_telefono,
    
            self.fecha_nacimiento,
            self.genero,
        ])


    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"


class Invoice(models.Model):
    emitido_en = models.DateTimeField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    numero_factura = models.CharField(max_length=20, unique=True)  # Número único de la factura
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Impuestos aplicados
    descuento_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Descuento aplicado
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)  # Fecha límite de pago
    metodo_pago = models.CharField(max_length=50, choices=[('cash', 'Efectivo'), ('transfer', 'Transferencia'), ('card', 'Tarjeta')], blank=True, null=True)
    estado_pago = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('paid', 'Pagado'), ('failed', 'Fallido')], default='pending')
    notas = models.TextField(blank=True, null=True)  # Notas adicionales de la factura
    archivo_factura = models.FileField(upload_to='facturas/', null=True, blank=True)  # Campo para subir el archivo de la factura

    def __str__(self):
        return f"Factura #{self.numero_factura} para la Orden #{self.orden.id}"

    def total_factura(self):
        """Calcula el total de la factura considerando impuestos y descuentos."""
        return self.monto_total + self.impuestos - self.descuento_total









class Coupon(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=True)  # Solo números
    discount_type = models.CharField(max_length=10, choices=[('percent', 'Porcentaje'), ('fixed', 'Monto Fijo')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateTimeField()
    active = models.BooleanField(default=True)
    used = models.BooleanField(default=False)  # Para cupones individuales
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)  # Usuarios que pueden usar el cupón
    max_uses = models.PositiveIntegerField(default=1)  # Número máximo de usos permitidos
    used_count = models.PositiveIntegerField(default=0)  # Contador de usos

    def is_valid(self, user):
        """Verifica si el cupón es válido para un usuario específico."""
        return (
            self.active
            and self.expiration_date > now()
            and (self.max_uses > self.used_count)  # Verifica el límite de usos
            and (not self.allowed_users.exists() or user in self.allowed_users.all())  # Verifica si el usuario está permitido
        )

    def use_coupon(self, user):
        """Marca el cupón como usado para el usuario si es válido."""
        if self.is_valid(user):
            self.used_count += 1
            if self.used_count >= self.max_uses:
                self.active = False  # Desactiva el cupón cuando llega al límite de usos
            self.save()
            return True
        return False

    def save(self, *args, **kwargs):
        """Genera un código único si no se proporciona."""
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self, length=6):
        """Genera un código único con solo números."""
        while True:
            code = ''.join(random.choices('0123456789', k=length))
            if not Coupon.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f"Cupón {self.code} ({self.get_discount_type_display()})"





class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"Cart for {self.user.username}"

    def add_product(self, product, quantity=1):
        cart_item, created = CartItem.objects.get_or_create(cart=self, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()


    def clear_coupon(self):
        """Elimina el cupón aplicado al carrito."""
        self.coupon = None
        self.save()

    def total_price(self):
        total = sum(item.total_price() for item in self.items.all())
        if self.coupon:
            if self.coupon.discount_type == 'percent':
                discount = total * (self.coupon.discount_value / 100)
            elif self.coupon.discount_type == 'fixed':
                discount = self.coupon.discount_value
            total -= discount
        return max(total, 0)
    
    

    def remove_product(self, product):
        CartItem.objects.filter(cart=self, product=product).delete()

    def count_products(self):
        return sum(item.quantity for item in self.items.all())

   
    def clear_cart(self):
        self.items.all().delete()  # Elimina todos los items del carrito
        self.is_active = False  # Marca el carrito como inactivo
        self.save()




class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} of {self.product.title} in {self.cart.user.username}'s cart"

    def total_price(self):
        return self.quantity * self.product.price

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        





class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='address')
    
    # Ubicación Geográfica (Para el mapa)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Dirección Física
    localidad = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    
    main_street = models.CharField("Calle principal", max_length=255, null=True, blank=True)
    secondary_street = models.CharField("Calle secundaria", max_length=255, null=True, blank=True) # Intersección
    house_number = models.CharField("Número de casa", max_length=10, null=True, blank=True)
    
    # Nuevos campos útiles
    floor = models.CharField("Piso", max_length=10, null=True, blank=True)
    apartment = models.CharField("Departamento/Puerta", max_length=10, null=True, blank=True)

    description = models.TextField("Instrucciones de entrega", null=True, blank=True)
    
    # Contacto
    whatsapp_number = models.CharField("Número de WhatsApp", max_length=15, null=True, blank=True)
    email = models.EmailField("Correo electrónico", null=True, blank=True)
    
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.main_street} {self.house_number}, {self.localidad}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)






class Order(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
        ('card', 'Tarjeta'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Pedido Aprobado'),
        ('dispatching', 'En Despacho'),
        ('shipped', 'Pedido Enviado'),
        ('delivered', 'Pedido Entregado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_code = models.CharField(max_length=50, blank=True, null=True)
    
    #borrar despues
    verification_code = models.CharField(max_length=8, blank=True, null=True)
    verification_code_expires_at = models.DateTimeField(blank=True, null=True)
    #borrar despues

    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    

    confirm_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)
    confirmado_por_token = models.BooleanField(default=False)




    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_envio = models.CharField(
        max_length=50,
        choices=[('standard', 'Estándar'), ('express', 'Exprés')],
        default='standard'  # Valor predeterminado
    )
    is_paid = models.BooleanField(default=False)

    fecha_entrega_estimada = models.DateTimeField(blank=True, null=True)
    estado_pago = models.CharField(
        max_length=20,
        choices=[('pending', 'Pendiente'), ('confirmed', 'Confirmado'), ('failed', 'Fallido')],
        default='pending'  # Asignar un valor por defecto
    )

    enviado_en = models.DateTimeField(blank=True, null=True)
    factura = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    notas_internas = models.TextField(blank=True, null=True)
    

    numero_orden = models.CharField(max_length=13, unique=True, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} for {self.user.username}"
    
    def generate_order_number(self):
        """Genera un número de orden único de 13 dígitos."""
        order_number = ''.join(random.choices(string.digits, k=13))
        while Order.objects.filter(numero_orden=order_number).exists():
            order_number = ''.join(random.choices(string.digits, k=13))
        return order_number

    def save(self, *args, **kwargs):
        # Solo generar un número de orden si está vacío
        if not self.numero_orden:
            self.numero_orden = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def has_product(self, product_id):
        return self.items.filter(product_id=product_id).exists()
   

    def complete_order(self):
        self.status = 'completed'
        self.cart.clear_cart()  # Agregar esta línea para vaciar el carrito
        self.save()





class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} (x{self.quantity})"

    @property
    def total_price(self):
        return self.quantity * self.price



   

class CommentURL(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='comment_urls')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comment_urls')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_url(self):
        """Genera dinámicamente la URL para comentar."""
        return f"{settings.SITE_URL}{reverse('leave_comment', args=[self.product.id])}"











class NotificationGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="notification_groups")

    def __str__(self):
        return self.name


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("general", "General"),
        ("coupon", "Cupón de Descuento"),
        ("catalog", "Catálogo de Productos"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    group = models.ForeignKey(NotificationGroup, on_delete=models.SET_NULL, null=True, blank=True)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)  # Cupón opcional
    file = models.FileField(upload_to="notifications/files/", blank=True, null=True)  # Archivo adjunto
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="general")  # Tipo de notificación
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.recipient:
            return f"Notification for {self.recipient.username} - {self.title}"
        elif self.group:
            return f"Notification for group {self.group.name} - {self.title}"
        return f"Notification: {self.title}"

class NotificationReadStatus(models.Model):
    """Registra si un usuario ha leído una notificación."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'notification')  # Evitar duplicados

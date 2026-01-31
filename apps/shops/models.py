from datetime import timezone
from django.utils import timezone
from django.db import models
import uuid
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from apps.perfil.models import *

from django.core.cache import cache

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Proveedor(models.Model):  # Proveedores de productos propios
    nombre = models.CharField(max_length=200)
    informacion_contacto = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class VendedorExterno(models.Model):  # Vendedores externos cuyos productos vendemos
    nombre = models.CharField(max_length=200)
    informacion_contacto = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Comisión ganada
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Product(models.Model):
    # Campos originales (no modificados)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    share_count = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_products', blank=True)

    is_daily_offer = models.BooleanField(default=False)
    offer_start_date = models.DateTimeField(null=True, blank=True)
    offer_end_date = models.DateTimeField(null=True, blank=True)

    is_promotional = models.BooleanField(default=False)
    promotion_start_date = models.DateTimeField(null=True, blank=True)
    promotion_end_date = models.DateTimeField(null=True, blank=True)

    is_featured = models.BooleanField(default=False)

    # Nuevos campos agregados
    is_own_product = models.BooleanField(default=True)  # Indica si el producto es propio o de un tercero
    supplier = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")  # Proveedor (si es propio)
    external_seller = models.ForeignKey(VendedorExterno, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")  # Vendedor externo (si no es propio)

    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Costo de compra (si es propio)
    commission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Comisión (si es de un tercero)

    units_sold = models.PositiveIntegerField(default=0)  # Cantidad de unidades vendidas
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Ingresos totales por ventas

    def __str__(self):
        return self.title

    @property
    def total_likes(self):
        return self.likes.count()

    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])

    @property
    def is_currently_promotional(self):
        if self.is_promotional and self.promotion_start_date and self.promotion_end_date:
            return self.promotion_start_date <= timezone.now() <= self.promotion_end_date
        return False

    @property
    def profit_margin(self):
        """Calcula la ganancia por unidad vendida"""
        if self.is_own_product:
            return self.price - self.purchase_cost  # Ganancia para productos propios
        elif self.external_seller:
            return self.price * (self.external_seller.commission_percentage / 100)  # Comisión para productos de terceros
        return 0.00

    @property
    def total_profit(self):
        """Calcula la ganancia total basada en unidades vendidas"""
        return self.profit_margin * self.units_sold


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.title}"

#este tabla de models sirve para llevar registro de que es lo que a visto el usuario anonimo o registrado que producto le gusta y que vio
class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # Si quieres saber qué usuario vio el producto
    session_id = models.CharField(max_length=40, null=True, blank=True)  # Si no quieres vincular las vistas a usuarios
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"View of {self.product.title} on {self.timestamp} anonimas {self.ip_address}"


class ProductRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    reason = models.TextField()  # Razón de la recomendación
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user} - {self.product.title}"




class UserPoints(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.points} points"




# --- 1. NUEVO MODELO DE CONFIGURACIÓN ---
class ConfiguracionCompartir(models.Model):
    meta_vistas = models.PositiveIntegerField(
        default=30, 
        verbose_name="Meta de Vistas",
        help_text="Cantidad de vistas únicas necesarias para ganar el premio."
    )
    premio_coins = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=500.00,
        verbose_name="Premio en Coins",
        help_text="Cantidad de Coins a otorgar al cumplir la meta."
    )

    class Meta:
        verbose_name = "Configuración de Referidos"
        verbose_name_plural = "Configuración de Referidos"

    def save(self, *args, **kwargs):
        # Esto asegura que solo exista UN registro (ID=1)
        self.pk = 1
        super().save(*args, **kwargs)
        # Limpiamos caché si usaras, para que se actualice al instante
        cache.delete('share_config')

    @classmethod
    def load(cls):
        # Método mágico para obtener la config desde cualquier lado
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración del Sistema de Referidos"
    


class ProductShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='shared_products')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # Usuario registrado
    session_id = models.CharField(max_length=40, null=True, blank=True)  # Para usuarios anónimos
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    share_link = models.URLField()  # Enlace generado
    created_at = models.DateTimeField(auto_now_add=True)
    reward_claimed = models.BooleanField(default=False)

    views_count = models.PositiveIntegerField(default=0)  # Vistas desde el enlace compartido
   
    @property
    def META_VISTAS(self):
        return ConfiguracionCompartir.load().meta_vistas

    @property
    def PREMIO_COINS(self):
        return ConfiguracionCompartir.load().premio_coins

    # --- AGREGA ESTO ---
    @property
    def vistas_restantes(self):
        """Calcula cuántas faltan para llegar a la meta"""
        restantes = self.META_VISTAS - self.views_count
        return max(restantes, 0) # Para que nunca devuelva negativo
    
    def __str__(self):
        return f"{self.user or 'Anonymous'} shared {self.product.title} at {self.created_at}"




class ShareVisit(models.Model):
    share = models.ForeignKey(ProductShare, on_delete=models.CASCADE, related_name='visits', null=True)  # Permitir nulos temporalmente
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField()
    visit_time = models.DateTimeField(default=timezone.now)



class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Evita comentarios duplicados



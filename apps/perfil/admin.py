from django.contrib import admin
from django.utils.html import format_html
import json

from .models import (
    Perfil, Notification, NotificationGroup, NotificationReadStatus,
    TransaccionMercadoPago, CartItem, Coupon, Cart, CommentURL,
    Address, Order, Invoice, OrderItem
)

# --- INLINE DE PRODUCTOS (Corregido para evitar Error 500) ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total_price_display')
    can_delete = False

    def total_price_display(self, obj):
        # PROTECCIÓN: Si falta cantidad o precio, mostramos $0 en vez de explotar
        if not obj.quantity or not obj.price:
            return "$0.00"
        try:
            total = obj.quantity * obj.price
            return f"${total}"
        except Exception:
            return "Error Calc"
    total_price_display.short_description = "Total Línea"

# --- INLINE DE MERCADO PAGO ---
class TransaccionMPInline(admin.StackedInline):
    model = TransaccionMercadoPago
    readonly_fields = ('payment_id', 'status', 'status_detail', 'preference_id', 'created_at', 'raw_response_pretty')
    can_delete = False
    extra = 0
    classes = ('collapse',) 
    verbose_name = "Detalle de Pago Mercado Pago"
    verbose_name_plural = "Historial de Mercado Pago"

    def raw_response_pretty(self, obj):
        if obj.raw_response:
            # PROTECCIÓN: Si el JSON es inválido, mostramos texto plano
            try:
                data = json.dumps(obj.raw_response, indent=4)
                return format_html('<pre style="font-size: 10px; background: #f5f5f5; padding: 10px;">{}</pre>', data)
            except:
                return str(obj.raw_response)
        return "-"
    raw_response_pretty.short_description = "Respuesta Técnica (JSON)"

# --- ADMIN DE ORDENES ---
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, TransaccionMPInline]
    
    list_display = ('id', 'user_info', 'monto_total', 'payment_method_badge', 'status_badge', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('created_at', 'monto_total', 'confirm_token')

    fieldsets = (
        ('Resumen', {
            'fields': ('user', 'status', 'is_paid', 'payment_method', 'monto_total')
        }),
        ('Logística', {
            'fields': ('address', 'fecha_entrega_estimada')
        }),
        ('Sistema', {
            'fields': ('created_at',)
        }),
    )

    # --- PERSONALIZACIÓN VISUAL ---
    def user_info(self, obj):
        return obj.user.username if obj.user else "Invitado"
    user_info.short_description = "Usuario"

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 5px;">{}</span>',
            color, obj.get_status_display() or obj.status
        )
    status_badge.short_description = "Estado"

    def payment_method_badge(self, obj):
        # Esto soluciona que no veas los nombres bonitos
        return obj.get_payment_method_display() or obj.payment_method
    payment_method_badge.short_description = "Medio de Pago"

# --- OTROS REGISTROS ---
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'main_street', 'localidad')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    pass

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'active')

# Si tienes otros modelos como Perfil, déjalos como los tenías arriba
# (He omitido Perfil para resumir, pero mantenlo si lo tenías bien)
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum  # Importante para sumar
from .models import CoinTransaction

@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'colored_amount', 'transaction_type', 'description', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def colored_amount(self, obj):
        if obj.amount > 0:
            color = 'green'
            signo = '+'
        else:
            color = 'red'
            signo = ''
        
        monto_texto = f"{obj.amount:.2f}"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color,
            signo,
            monto_texto
        )
    
    colored_amount.short_description = 'Monto'

    # --- AQUÍ ESTÁ LA SOLUCIÓN MÁGICA ---
    # Sobrescribimos los métodos de guardado del Admin para que recalculen el saldo

    def save_model(self, request, obj, form, change):
        """Se ejecuta cuando AGREGAS o EDITAS una transacción"""
        super().save_model(request, obj, form, change)
        self.recalcular_saldo(obj.user)

    def delete_model(self, request, obj):
        """Se ejecuta cuando BORRAS una transacción"""
        user = obj.user # Guardamos el usuario antes de borrar
        super().delete_model(request, obj)
        self.recalcular_saldo(user)

    def delete_queryset(self, request, queryset):
        """Se ejecuta cuando borras VARIAS transacciones a la vez"""
        # Identificamos los usuarios afectados
        users = set(obj.user for obj in queryset)
        super().delete_queryset(request, queryset)
        # Recalculamos saldo a cada uno
        for user in users:
            self.recalcular_saldo(user)

    def recalcular_saldo(self, user):
        """Suma todo el historial real y actualiza el perfil"""
        total = CoinTransaction.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
        
        if total is None:
            total = 0
            
        if hasattr(user, 'perfil'):
            user.perfil.coins = total
            user.perfil.save()
from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductView)
admin.site.register(ProductRecommendation)
admin.site.register(UserPoints)

admin.site.register(ProductShare)
admin.site.register(ShareVisit)
admin.site.register(Comment)

admin.site.register(Proveedor)
admin.site.register(VendedorExterno)


@admin.register(ConfiguracionCompartir)
class ConfiguracionCompartirAdmin(admin.ModelAdmin):
    # Bloqueamos agregar/borrar para que siempre sea uno solo
    def has_add_permission(self, request):
        # Solo permite agregar si no existe ninguno
        return not ConfiguracionCompartir.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False # No permitir borrar la config

    list_display = ('meta_vistas', 'premio_coins')



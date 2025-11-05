from django.contrib import admin
from .models import (
    Reclamo, VisitaDiaria, SearchQuery, SocialMediaClick,
    ClienteConsulta, Empleado, Visita, PaginaVisitada
)

admin.site.register(Reclamo)
admin.site.register(VisitaDiaria)
admin.site.register(SearchQuery)
admin.site.register(SocialMediaClick)


@admin.register(ClienteConsulta)
class ClienteConsultaAdmin(admin.ModelAdmin):
    list_display = ('titulo_producto', 'producto_id', 'empleado', 'estado', 'fecha', 'prioridad')
    list_filter = ('estado', 'empleado', 'prioridad')
    search_fields = (
        'titulo_producto',
        'producto_id',
        'empleado__usuario__email',
        'empleado__usuario__first_name',
        'empleado__usuario__last_name',
    )
    ordering = ('-fecha',)
    actions = ['marcar_como_resuelta']
    list_select_related = ('empleado', 'empleado__usuario')
    autocomplete_fields = ('empleado',)  # <- requiere search_fields en EmpleadoAdmin

    @admin.action(description="Marcar como resueltas")
    def marcar_como_resuelta(self, request, queryset):
        updated = queryset.update(estado='resuelta')
        self.message_user(request, f"{updated} consultas marcadas como resueltas.")


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefono', 'activo', 'max_consultas', 'ultima_asignacion')
    list_filter = ('activo',)
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name', 'telefono')  # <- necesario
    autocomplete_fields = ('usuario',)  # <- requiere search_fields en el admin de UserAccount
    list_select_related = ('usuario',)


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'direccion_ip', 'marca_tiempo', 'marca_tiempo_fin', 'duracion_legible', 'dispositivo')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name', 'direccion_ip', 'navegador', 'session_id')
    list_filter = ('dispositivo', 'navegador')
    list_select_related = ('usuario',)


@admin.register(PaginaVisitada)
class PaginaVisitadaAdmin(admin.ModelAdmin):
    list_display = ('visita', 'url', 'marca_tiempo')
    search_fields = ('url', 'visita__usuario__email', 'visita__usuario__first_name', 'visita__usuario__last_name')
    list_select_related = ('visita', 'visita__usuario')

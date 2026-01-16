from django.contrib import admin
from .models import BotConfig, BotKnowledge, BotOffer, ChatMessage, ChatIncident

@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display = ('name',)
    # Evita crear más de una configuración
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(BotKnowledge)
class BotKnowledgeAdmin(admin.ModelAdmin):
    list_display = ('topic', 'content')

@admin.register(BotOffer)
class BotOfferAdmin(admin.ModelAdmin):
    list_display = ('product', 'promotion_text', 'is_active')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('role', 'user', 'short_content', 'timestamp')
    list_filter = ('role', 'timestamp', 'user')
    
    def short_content(self, obj):
        return obj.content[:50]

@admin.register(ChatIncident)
class ChatIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_type', 'user', 'created_at', 'is_resolved')
    list_filter = ('incident_type', 'is_resolved')
    readonly_fields = ('message_content',)
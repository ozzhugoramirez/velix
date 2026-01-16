from django.db import models
from apps.shops.models import Product  # Asumiendo que tu modelo de productos se llama Product
from django.db import models
from django.conf import settings # Para acceder al User model
from apps.shops.models import Product



class BotConfig(models.Model):
    """Configura la personalidad y las restricciones estrictas del bot"""
    name = models.CharField(max_length=50, default="Asis")
    personality = models.TextField(
        default="Eres un vendedor profesional, amable y divertido de la tienda NextGen. "
                "Tu objetivo es ayudar a comprar y resolver dudas sobre la tienda."
    )
    restrictions = models.TextField(
        default="SOLO respondes sobre productos de la tienda, envíos, contacto y ofertas. "
                "Si te preguntan sobre programación, código, política o temas ajenos, "
                "responde amablemente que solo eres un asistente de compras y no puedes hablar de eso."
    )
    
    # Singleton: Para asegurar que solo haya una configuración activa
    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Configuración: {self.name}"

class BotKnowledge(models.Model):
    """Información general: Contacto, Horarios, Envíos, etc."""
    topic = models.CharField(max_length=100, help_text="Ej: Horarios, Contacto, Devoluciones")
    content = models.TextField(help_text="La respuesta que el bot debe saber sobre este tema.")

    def __str__(self):
        return self.topic

class BotOffer(models.Model):
    """Ofertas específicas que el bot debe priorizar"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bot_promotions')
    promotion_text = models.TextField(help_text="Texto de venta: Ej: '¡Este monitor está al 20% off solo por hoy!'")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Promo: {self.product}"
    



class ChatMessage(models.Model):
    """Guarda cada burbuja de chat (User y Bot)"""
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'IA (Asis)'),
        ('system', 'Sistema'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True, help_text="Para usuarios anónimos")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} - {self.timestamp}"

class ChatIncident(models.Model):
    """Para registrar insultos, reclamos fuertes o leads específicos"""
    TYPE_CHOICES = [
        ('INSULT', 'Insulto/Comportamiento Ofensivo'),
        ('CLAIM', 'Reclamo/Queja'),
        ('LEAD', 'Pide Producto Específico'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    message_content = models.TextField()
    incident_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.incident_type} - {self.created_at}"
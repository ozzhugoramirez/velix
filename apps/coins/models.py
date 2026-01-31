from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class CoinTransaction(models.Model):
    TIPO_CHOICES = [
        ('COMPRA', 'Compra en Tienda'),     # Gana puntos por comprar
        ('REFERIDO', 'Referido Exitoso'),   # Gana por invitar
        ('CANJE', 'Canje de Productos'),    # Gasta puntos
        ('BONUS', 'Bono Promocional'),      # Regalos del sistema
        ('ENVIO', 'Canje Envío Gratis'),    # Gasta puntos
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coin_history')
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Positivo (gana) o Negativo (gasta)
    transaction_type = models.CharField(max_length=20, choices=TIPO_CHOICES)
    description = models.CharField(max_length=255, blank=True) # Ej: "Compra orden #12345"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Ordenar del más reciente al más antiguo

    def __str__(self):
        signo = "+" if self.amount > 0 else ""
        return f"{self.user.username}: {signo}{self.amount} ({self.transaction_type})"
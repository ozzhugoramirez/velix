from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.db import models
from django.utils.timezone import now, localtime

from uuid import uuid4
from decimal import Decimal
from django.utils import timezone

class Reclamo(models.Model):
    # Opciones de tipo de reclamo
    NOMBRE_OPCIONES = [
        ('no_llego', 'No me llegó el envío'),
        ('producto_roto', 'Producto roto'),
        ('producto_incorrecto', 'Producto incorrecto'),
        ('falta_producto', 'Faltó un producto en mi pedido'),
        ('demora_envio', 'Demora en el envío'),
        ('defectuoso', 'Producto defectuoso'),
        ('mala_atencion', 'Mala atención al cliente'),
        ('error_cobro', 'Error en el cobro'),
        ('cancelacion', 'Quiero cancelar mi pedido'),
        ('otro', 'Otro'),
    ]

    # Estado del reclamo
    ESTADO_OPCIONES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('resuelto', 'Resuelto'),
        ('rechazado', 'Rechazado'),
    ]

    # Datos básicos
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField()
    celular = models.CharField(max_length=15)
    tipo_reclamo = models.CharField(max_length=20, choices=NOMBRE_OPCIONES)
    descripcion = models.TextField()

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    # Información avanzada
    estado = models.CharField(max_length=20, choices=ESTADO_OPCIONES, default='pendiente')
    fecha_creacion = models.DateTimeField(default=now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Última actualización del reclamo
    prioridad = models.IntegerField(default=1)  # Nivel de prioridad (1: Baja, 5: Alta)
    referencia_pedido = models.CharField(max_length=50, blank=True, null=True)  # ID del pedido relacionado
    departamento_asignado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('logistica', 'Logística'),
            ('soporte', 'Soporte Técnico'),
            ('facturacion', 'Facturación'),
            ('atencion_cliente', 'Atención al Cliente'),
        ],
    )  # Área que atenderá el reclamo
    notas_internas = models.TextField(blank=True, null=True)  # Espacio para notas internas de los empleados

    def __str__(self):
        return f'{self.nombre} {self.apellido} - {self.tipo_reclamo} ({self.estado})'

    class Meta:
        verbose_name = "Reclamo"
        verbose_name_plural = "Reclamos"


class Visita(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    direccion_ip = models.GenericIPAddressField()
    marca_tiempo = models.DateTimeField(auto_now_add=True)
    marca_tiempo_fin = models.DateTimeField(null=True, blank=True)
    agente_usuario = models.CharField(max_length=255, null=True, blank=True)
    navegador = models.CharField(max_length=50, null=True, blank=True)
    session_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    
    dispositivo = models.CharField(max_length=20, null=True, blank=True) 

    def __str__(self):
        u = str(self.usuario) if self.usuario else 'Anónimo'   # str(user) => email por tu __str__
        return f"{u} - {self.direccion_ip} - {self.marca_tiempo:%Y-%m-%d %H:%M:%S}"

    def duracion_legible(self):
        if self.marca_tiempo_fin:
            duracion = self.marca_tiempo_fin - self.marca_tiempo
            total_segundos = int(duracion.total_seconds())
            minutos, segundos = divmod(total_segundos, 60)
            horas, minutos = divmod(minutos, 60)
            return f"{horas}h {minutos}m {segundos}s"
        return "En curso"


class PaginaVisitada(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='paginas')
    url = models.URLField()
    marca_tiempo = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        u = str(self.visita.usuario) if self.visita and self.visita.usuario else 'Anónimo'
        return f"{u} - {self.url} - {self.marca_tiempo:%Y-%m-%d %H:%M:%S}"



class VisitaDiaria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    conteo_visitas = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('usuario', 'fecha')  # Garantiza que no haya duplicados

    def __str__(self):
        u = str(self.usuario) if self.usuario else 'Anónimo'
        return f"{u} - {self.fecha} - {self.conteo_visitas} visitas"


class SearchQuery(models.Model):
    term = models.CharField(max_length=255, unique=True)
    count = models.IntegerField(default=1)
    has_results = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Fecha de registro
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)  # Usuario logueado
  
    def __str__(self):
        u = str(self.usuario) if self.usuario else 'Sin usuario'
        return f"{self.term} - {u}"



class SocialMediaClick(models.Model):
    platform = models.CharField(max_length=50)  # Nombre de la red social
    timestamp = models.DateTimeField(default=now)  # Fecha y hora del clic
    user_id = models.CharField(max_length=100, null=True, blank=True)  # Identificador de usuario opcional
    click_count = models.PositiveIntegerField(default=0)  # Contador de clics

    def __str__(self):
        return f"{self.platform} - {self.timestamp}"

    def clicks_today(self):
        """Calcula cuántos clics se han registrado hoy."""
        today = localtime(now()).date()
        return SocialMediaClick.objects.filter(platform=self.platform, timestamp__date=today).count()

    def clicks_this_week(self):
        """Calcula cuántos clics se han registrado esta semana."""
        start_of_week = localtime(now()).date() - timedelta(days=localtime(now()).weekday())
        return SocialMediaClick.objects.filter(platform=self.platform, timestamp__date__gte=start_of_week).count()







class Empleado(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    max_consultas = models.IntegerField(default=5)
    ultima_asignacion = models.DateTimeField(default=timezone.now)

    def consultas_activas(self):
        return self.consultas.filter(estado='pendiente').count()

    def __str__(self):
        return self.usuario.get_full_name() or str(self.usuario)


class ClienteConsulta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('resuelta', 'Resuelta'),
        ('no_atendida', 'No atendida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultas')
    ip_cliente = models.GenericIPAddressField(null=True, blank=True)
    producto_id = models.UUIDField()
    titulo_producto = models.CharField(max_length=255)
    precio_producto = models.DecimalField(max_digits=10, decimal_places=2)
    prioridad = models.IntegerField(default=1)  # 1 = normal, 2 = urgente
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"{self.titulo_producto} ({self.estado}) - {self.empleado}"


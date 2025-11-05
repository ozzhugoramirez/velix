from datetime import date
from django.utils.timezone import now
from apps.dasboard.models import Visita, PaginaVisitada, VisitaDiaria
from user_agents import parse
from django.db.models import F

class RastrearVisitasMiddleware:
    excluded_paths = ['/admin/', '/api/', '/rt/']  # Rutas excluidas

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Excluir rutas específicas
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)

        if not request.user.is_anonymous or True:  # Procesar tanto usuarios autenticados como anónimos
            ip = self.get_client_ip(request)
            agente_usuario = request.META.get('HTTP_USER_AGENT', '')
            navegador = agente_usuario[:50]
            session_id = request.session.session_key

            # Identificar el dispositivo
            user_agent = parse(agente_usuario)
            dispositivo = "Móvil" if user_agent.is_mobile else "Tablet" if user_agent.is_tablet else "Escritorio"

            # Crear o actualizar la visita
            visita, created = Visita.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'usuario': request.user if request.user.is_authenticated else None,
                    'direccion_ip': ip,
                    'agente_usuario': agente_usuario,
                    'navegador': navegador,
                    'dispositivo': dispositivo,  # Nuevo campo (añádelo al modelo si lo deseas)
                }
            )

            # Incrementar el total de visitas del usuario si es autenticado y la visita es nueva
            if created and request.user.is_authenticated:
                request.user.total_visitas = F('total_visitas') + 1
                request.user.save(update_fields=['total_visitas'])

            # Registrar la página visitada solo si es nueva en la sesión
            if not PaginaVisitada.objects.filter(visita=visita, url=request.path).exists():
                PaginaVisitada.objects.create(visita=visita, url=request.path)

            # Incrementar el conteo de visitas diarias
            if created:  # Solo cuenta una vez por sesión nueva
                fecha_hoy = date.today()
                visita_diaria, _ = VisitaDiaria.objects.get_or_create(
                    usuario=request.user if request.user.is_authenticated else None,
                    fecha=fecha_hoy,
                    defaults={'conteo_visitas': 0}
                )
                visita_diaria.conteo_visitas += 1
                visita_diaria.save()

            # Marcar el inicio de la visita
            request.visita = visita

        response = self.get_response(request)

        # Actualizar marca_tiempo_fin cuando termine la solicitud
        if hasattr(request, 'visita'):
            request.visita.marca_tiempo_fin = now()
            tiempo_en_pagina = (request.visita.marca_tiempo_fin - request.visita.marca_tiempo).total_seconds()
            request.visita.save()

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

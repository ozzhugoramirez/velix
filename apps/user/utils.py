# accounts/utils.py
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from .models import EmailVerificationCode

def generate_numeric_code(n=6):
    return f"{random.randint(0, 10**n - 1):0{n}d}"

def create_and_send_code(email, purpose='signup'):
    # anti-spam simple: si hay un código creado hace < 60s, no enviar otro
    recent = EmailVerificationCode.objects.filter(
        email=email, used=False, expires_at__gt=timezone.now()
    ).order_by("-created_at").first()

    if recent and (timezone.now() - recent.created_at).total_seconds() < 60:
        return recent  # reusar

    code = generate_numeric_code(6)
    ev = EmailVerificationCode.objects.create(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    send_mail(
        subject="Tu código de verificación",
        message=f"Tu código es: {code}. Vence en 10 minutos.",
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[email],
        fail_silently=False,
    )
    return ev

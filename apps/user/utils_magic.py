# accounts/utils_magic.py
import secrets
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from .models import MagicLoginLink, UserAccount

MAGIC_TTL_MINUTES = 10
MAX_PER_EMAIL_WINDOW = 5  # anti-abuso simple (5 por hora)

def _too_many_recent_links(email: str) -> bool:
    one_hour_ago = timezone.now() - timedelta(hours=1)
    return MagicLoginLink.objects.filter(
        email=email, created_at__gte=one_hour_ago
    ).count() >= MAX_PER_EMAIL_WINDOW

def build_magic_url(request, link: MagicLoginLink, next_url: str = "") -> str:
    url = reverse("magic_login_consume", args=[str(link.id), link.token])
    if next_url:
        return f"{request.build_absolute_uri(url)}?next={next_url}"
    return request.build_absolute_uri(url)

def _send_magic_email(to_email: str, magic_url: str):
    site_name = getattr(settings, "SITE_NAME", "Tu Cuenta")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    support_email = getattr(settings, "SUPPORT_EMAIL", None)

    context = {
        "site_name": site_name,
        "magic_url": magic_url,
        "ttl": MAGIC_TTL_MINUTES,
        "support_email": support_email,
        "year": timezone.now().year,
    }

    subject = f"{site_name}: tu enlace para iniciar sesión"
    html_body = render_to_string("emails/magic_login.html", context)
    # si no creás magic_login.txt, usamos strip_tags del HTML
    try:
        text_body = render_to_string("emails/magic_login.txt", context)
    except Exception:
        text_body = strip_tags(html_body)

    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")

    # Opcional: cabeceras de seguridad/ux
    msg.extra_headers = {
        "List-Unsubscribe": f"<mailto:{support_email}>" if support_email else "",
    }

    msg.send()

@transaction.atomic
def issue_magic_link(request, email: str, next_url: str = "") -> str | None:
    # invalidar enlaces previos no usados del mismo correo (opcional)
    MagicLoginLink.objects.filter(email=email, used=False).update(used=True, used_at=timezone.now())

    if _too_many_recent_links(email):
        return None

    token = secrets.token_urlsafe(32)  # seguro e impredecible
    link = MagicLoginLink.objects.create(
        email=email,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=MAGIC_TTL_MINUTES),
        ip_issued=(request.META.get("REMOTE_ADDR") or None),
        ua_issued=request.META.get("HTTP_USER_AGENT", "")[:500],
    )
    magic_url = build_magic_url(request, link, next_url)

    _send_magic_email(email, magic_url)
    return magic_url

def user_exists(email: str) -> bool:
    return UserAccount.objects.filter(email=email).exists()

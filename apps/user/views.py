# apps/user/views.py  (ajusta el path a tu app)
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from django.shortcuts import render, redirect
from django.views import View
from urllib.parse import urlencode

from .forms import EmailForm, PasswordForm, CodeForm, RegisterForm
from .models import UserAccount, EmailVerificationCode
from .utils import create_and_send_code

STEP_EMAIL = "email"
STEP_PASSWORD = "password"
STEP_CODE = "code"
STEP_REGISTER = "register"


def _safe_next(request):
    """Obtiene un 'next' seguro (mismo host) desde POST/GET/Session."""
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.session.get("auth_next")
    )
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


def _redirect_to_login(next_url_name: str, next_url: str | None):
    """Redirige a la página de login, preservando ?next= si existe."""
    login_url = reverse(next_url_name)
    if next_url:
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")
    return redirect(login_url)


class AuthFlowView(View):
    """
    Flujo:
      - email -> si existe: password | si no existe: código
      - code -> si ok: register
      - register -> crear usuario y loguear
    Name de URL recomendado: 'login'
    """

    template_name = "accounts/auth_flow.html"  # usa tu ruta real de template
    login_url_name = "login"                   # nombre de URL que usarás en {% url 'login' %}

    def get(self, request):
        # Guardamos un next seguro para todo el flujo
        next_url = _safe_next(request)
        if next_url:
            request.session["auth_next"] = next_url

        step = request.session.get("auth_step", STEP_EMAIL)
        email = request.session.get("auth_email")

        if step == STEP_PASSWORD and email:
            ctx = {"step": STEP_PASSWORD, "email": email, "password_form": PasswordForm(), "next": next_url or request.session.get("auth_next")}
            return render(request, self.template_name, ctx)

        if step == STEP_CODE and email:
            ctx = {"step": STEP_CODE, "email": email, "code_form": CodeForm(), "next": next_url or request.session.get("auth_next")}
            return render(request, self.template_name, ctx)

        if step == STEP_REGISTER and email and request.session.get("auth_verified"):
            ctx = {"step": STEP_REGISTER, "email": email, "register_form": RegisterForm(), "next": next_url or request.session.get("auth_next")}
            return render(request, self.template_name, ctx)

        # default: primer paso
        request.session["auth_step"] = STEP_EMAIL
        ctx = {"step": STEP_EMAIL, "email_form": EmailForm(), "next": next_url or request.session.get("auth_next")}
        return render(request, self.template_name, ctx)

    def post(self, request):
        action = request.POST.get("action")
        session = request.session
        step = session.get("auth_step", STEP_EMAIL)
        email = session.get("auth_email")
        next_url = _safe_next(request)

        # si vino un next, refrescamos en sesión
        if next_url:
            session["auth_next"] = next_url

        # ========= Paso 1: Email =========
        if action == "submit_email":
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                email = email_form.cleaned_data["email"].strip().lower()
                session["auth_email"] = email

                if UserAccount.objects.filter(email__iexact=email).exists():
                    session["auth_step"] = STEP_PASSWORD
                    messages.info(request, "Correo encontrado. Ingresá tu contraseña.")
                    return _redirect_to_login(self.login_url_name, session.get("auth_next"))
                else:
                    create_and_send_code(email, purpose="signup")
                    session["auth_step"] = STEP_CODE
                    messages.info(request, "Te enviamos un código a tu correo. Ingrésalo para continuar.")
                    return _redirect_to_login(self.login_url_name, session.get("auth_next"))

            # inválido → mostrar form email
            ctx = {"step": STEP_EMAIL, "email_form": email_form, "next": session.get("auth_next")}
            return render(request, self.template_name, ctx)

        # ========= Paso 2: Password =========
        if action == "submit_password":
            if not email:
                session["auth_step"] = STEP_EMAIL
                return _redirect_to_login(self.login_url_name, session.get("auth_next"))

            pwd_form = PasswordForm(request.POST)
            if pwd_form.is_valid():
                user = authenticate(request, username=email, password=pwd_form.cleaned_data["password"])
                if user is not None and user.is_active:
                    login(request, user)  # authenticate() setea user.backend
                    # limpiar estado del flujo
                    for k in ("auth_step", "auth_email", "auth_verified"):
                        session.pop(k, None)
                    messages.success(request, "¡Bienvenido!")
                    # redirigir a next o a home
                    target = session.pop("auth_next", None) or "/"
                    return redirect(target)
                else:
                    messages.error(request, "Contraseña incorrecta.")

            ctx = {"step": STEP_PASSWORD, "email": email, "password_form": pwd_form, "next": session.get("auth_next")}
            return render(request, self.template_name, ctx)

        # ========= Paso 3: Código =========
        if action == "submit_code":
            if not email:
                session["auth_step"] = STEP_EMAIL
                return _redirect_to_login(self.login_url_name, session.get("auth_next"))

            code_form = CodeForm(request.POST)
            if code_form.is_valid():
                code = code_form.cleaned_data["code"]
                ev = EmailVerificationCode.objects.filter(
                    email=email, used=False, expires_at__gt=timezone.now()
                ).order_by("-created_at").first()

                if not ev:
                    messages.error(request, "No hay un código válido. Pedí uno nuevo.")
                else:
                    ev.attempts += 1
                    if ev.is_valid() and ev.code == code:
                        ev.used = True
                        ev.save(update_fields=["attempts", "used"])
                        session["auth_verified"] = True
                        session["auth_step"] = STEP_REGISTER
                        messages.success(request, "Código verificado. Completá tu registro.")
                        return _redirect_to_login(self.login_url_name, session.get("auth_next"))
                    else:
                        ev.save(update_fields=["attempts"])
                        messages.error(request, "Código incorrecto o expirado.")

            ctx = {"step": STEP_CODE, "email": email, "code_form": code_form, "next": session.get("auth_next")}
            return render(request, self.template_name, ctx)

        # ========= Paso 4: Registro =========
        if action == "submit_register":
            if not (email and session.get("auth_verified")):
                session["auth_step"] = STEP_EMAIL
                return _redirect_to_login(self.login_url_name, session.get("auth_next"))

            reg_form = RegisterForm(request.POST)
            if reg_form.is_valid():
                with transaction.atomic():
                    if UserAccount.objects.filter(email__iexact=email).exists():
                        messages.error(request, "Ese email ya existe. Probá iniciar sesión.")
                        session["auth_step"] = STEP_PASSWORD
                        return _redirect_to_login(self.login_url_name, session.get("auth_next"))

                    # Crear usuario
                    UserAccount.objects.create_user(
                        email=email,
                        password=reg_form.cleaned_data["password1"],
                        first_name=reg_form.cleaned_data["first_name"],
                        last_name=reg_form.cleaned_data["last_name"],
                    )

                # autenticar y loguear (arreglo recomendado)
                user = authenticate(request, username=email, password=reg_form.cleaned_data["password1"])
                if user is not None and user.is_active:
                    login(request, user)
                    for k in ("auth_step", "auth_email", "auth_verified"):
                        session.pop(k, None)
                    messages.success(request, "Cuenta creada y sesión iniciada.")
                    target = session.pop("auth_next", None) or "/"
                    return redirect(target)
                else:
                    messages.warning(request, "Cuenta creada. Ingresá tu contraseña para entrar.")
                    session["auth_step"] = STEP_PASSWORD
                    return _redirect_to_login(self.login_url_name, session.get("auth_next"))

            ctx = {"step": STEP_REGISTER, "email": email, "register_form": reg_form, "next": session.get("auth_next")}
            return render(request, self.template_name, ctx)

        # Si acción desconocida → volver al email
        session["auth_step"] = STEP_EMAIL
        ctx = {"step": STEP_EMAIL, "email_form": EmailForm(), "next": session.get("auth_next")}
        return render(request, self.template_name, ctx)


class LogoutView(View):
    """Logout simple; respeta ?next= si viene y es seguro."""
    def get(self, request):
        target = _safe_next(request) or "/"
        logout(request)
        return redirect(target)

    def post(self, request):
        return self.get(request)






# accounts/views_magic.py
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import F
from django.contrib.auth import login as auth_login
from django.http import Http404
from .forms import MagicEmailForm
from .models import MagicLoginLink, UserAccount
from .utils_magic import issue_magic_link, user_exists, MAGIC_TTL_MINUTES

class MagicStartView(TemplateView):
    template_name = "accounts/magic_start.html"

    def get(self, request, *args, **kwargs):
        form = MagicEmailForm(initial={"next": request.GET.get("next", "")})
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = MagicEmailForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].lower()
        next_url = form.cleaned_data.get("next") or ""

        # Solo para correos existentes (según tu requerimiento)
        if not user_exists(email):
            messages.error(request, "Este correo no está registrado. Probá con otro o usá el ingreso clásico.")
            return render(request, self.template_name, {"form": form})

        url = issue_magic_link(request, email, next_url)
        if url is None:
            messages.warning(request, "Demasiados intentos recientes. Probá nuevamente en unos minutos.")
            return render(request, self.template_name, {"form": form})

        messages.success(request, "Te enviamos un enlace de acceso. Revisá tu correo (también spam).")
        return redirect("magic_check_email")

class MagicCheckEmailView(TemplateView):
    template_name = "accounts/magic_check_email.html"

class MagicConsumeView(View):
    def get(self, request, uid: str, token: str):
        next_url = request.GET.get("next") or "/"
        try:
            link = MagicLoginLink.objects.get(pk=uid)
        except MagicLoginLink.DoesNotExist:
            raise Http404()

        # Validaciones
        if link.used or link.token != token or timezone.now() > link.expires_at:
            messages.error(request, "Enlace inválido o vencido. Pedí uno nuevo.")
            return redirect("magic_start")

        # Buscar usuario
        try:
            user = UserAccount.objects.get(email=link.email)
        except UserAccount.DoesNotExist:
            messages.error(request, "No encontramos una cuenta para este correo.")
            return redirect("magic_start")

        if not user.is_active:
            messages.error(request, "Tu cuenta está desactivada.")
            return redirect("magic_start")

        # Marcar usado y loguear
        link.used = True
        link.used_at = timezone.now()
        link.save(update_fields=["used", "used_at"])

        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        user.total_visitas = F("total_visitas") + 1
        user.save(update_fields=["total_visitas"])

        return redirect(next_url)

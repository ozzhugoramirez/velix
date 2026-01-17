from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from uuid import uuid4
import os

def user_avatar_upload_path(instance, filename):
    base, ext = os.path.splitext(filename)
    ext = (ext or ".jpg").lower()
    user_id = instance.pk or "tmp"
    return f"avatars/{user_id}/{uuid4().hex}{ext}"

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user._sync_flags_with_role()
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", UserAccount.Roles.ADMIN)
        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        MANAGER = "MGR", "Manager"
        EMPLOYEE = "EMP", "Empleado"
        CUSTOMER = "CUS", "Cliente"

    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    avatar = models.ImageField(
        upload_to=user_avatar_upload_path,
        blank=True,
        null=True,
        default="avatars/default.jpeg",  # asegúrate de tener este archivo
    )

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
        db_index=True,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    total_visitas = models.PositiveIntegerField(default=0)

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]

    def __str__(self):
        return self.email

    # Compatibilidad con .username (para evitar errores en admin o código viejo)
    @property
    def username(self):
        return self.email

    # ==== helpers de rol ====
    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN

    @property
    def is_manager(self):
        return self.role == self.Roles.MANAGER

    @property
    def is_employee(self):
        return self.role == self.Roles.EMPLOYEE

    @property
    def is_customer(self):
        return self.role == self.Roles.CUSTOMER

    @property
    def avatar_url(self):
        if self.avatar:
            try:
                return self.avatar.url
            except ValueError:
                return "/media/avatars/default.jpeg"
        return "/media/avatars/default.jpeg"

    def _sync_flags_with_role(self):
        if self.role in (self.Roles.ADMIN, self.Roles.MANAGER):
            self.is_staff = True
        elif self.role in (self.Roles.EMPLOYEE, self.Roles.CUSTOMER):
            self.is_staff = False

    def save(self, *args, **kwargs):
        if not self.is_superuser:
            self._sync_flags_with_role()
        super().save(*args, **kwargs)





# =======================
# Modelo para códigos de verificación
# =======================
class EmailVerificationCode(models.Model):
    PURPOSE_LOGIN = 'login'
    PURPOSE_SIGNUP = 'signup'
    PURPOSE_CHOICES = [
        (PURPOSE_LOGIN, 'Login'),
        (PURPOSE_SIGNUP, 'Signup'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    code = models.CharField(max_length=6)  # p.ej. "284193"
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default=PURPOSE_SIGNUP)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['expires_at']),
        ]

    def is_valid(self):
        return (not self.used) and timezone.now() <= self.expires_at and self.attempts < 5






class MagicLoginLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()                # email destino
    token = models.CharField(max_length=64)    # secreto aleatorio (no predecible)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    ip_issued = models.GenericIPAddressField(null=True, blank=True)
    ua_issued = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['expires_at']),
        ]

    def is_valid(self):
        return (not self.used) and timezone.now() <= self.expires_at

# apps/user/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import UserAccount, EmailVerificationCode, MagicLoginLink

from django.utils.html import format_html

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_active", "avatar_mini")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("avatar_preview",)

    fieldsets = (
        ("Credenciales", {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "avatar", "avatar_preview")}),
        ("Rol y estado", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Otros", {"fields": ("total_visitas",)}),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:60px;border-radius:8px;">', obj.avatar.url)
        return "—"
    avatar_preview.short_description = "Avatar"

    def avatar_mini(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:28px;border-radius:50%;">', obj.avatar.url)
        return "—"
    avatar_mini.short_description = "Foto"



@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "code", "created_at", "expires_at", "used", "attempts")
    list_filter = ("purpose", "used")
    search_fields = ("email",)

@admin.register(MagicLoginLink)
class MagicLoginLinkAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "expires_at", "used")
    list_filter = ("used",)
    search_fields = ("email",)

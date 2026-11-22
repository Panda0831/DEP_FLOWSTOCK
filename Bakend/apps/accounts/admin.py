from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "nom_complet", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "nom_complet", "public_id")
    ordering = ("email",)
    readonly_fields = (
        "public_id",
        "created_at",
        "updated_at",
        "last_password_change",
        "last_login",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("nom_complet", "role")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Audit",
            {
                "fields": (
                    "public_id",
                    "created_at",
                    "updated_at",
                    "last_password_change",
                    "last_login",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nom_complet",
                    "password1",
                    "password2",
                    "role",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

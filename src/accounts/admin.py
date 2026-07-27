from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import TaiKhoan


@admin.register(TaiKhoan)
class TaiKhoanAdmin(UserAdmin):
    readonly_fields = ("ma_tk",)
    list_display = (
        "ma_tk",
        "username",
        "vai_tro",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    list_filter = (
        "vai_tro",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "ma_tk",
        "username",
    )

    ordering = ("ma_tk",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Thông tin hệ thống Gym",
            {
                "fields": (
                    "ma_tk",
                    "vai_tro",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Thông tin hệ thống Gym",
            {
                "fields": (
                    "vai_tro",
                )
            },
        ),
    )
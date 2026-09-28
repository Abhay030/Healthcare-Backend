from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Doctor, Patient, PatientDoctorMapping, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "name", "is_staff", "is_active"]
    search_fields = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2")}),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["name", "age", "gender", "created_by", "created_at"]
    list_filter = ["gender", "created_at"]
    search_fields = ["name", "phone"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["name", "specialization", "created_by", "created_at"]
    list_filter = ["specialization", "created_at"]
    search_fields = ["name", "specialization", "email"]


@admin.register(PatientDoctorMapping)
class PatientDoctorMappingAdmin(admin.ModelAdmin):
    list_display = ["patient", "doctor", "assigned_at"]
    list_filter = ["assigned_at"]

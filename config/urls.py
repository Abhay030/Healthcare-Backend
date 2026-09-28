"""
URL configuration for the healthcare backend project.
"""

from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def home(request):
    """Interactive API playground served at / — the API itself lives under /api/."""
    return render(request, "api/index.html")


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

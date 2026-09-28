from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    # Authentication
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Patients
    path(
        "patients/",
        views.PatientViewSet.as_view({"get": "list", "post": "create"}),
        name="patient-list",
    ),
    path(
        "patients/<int:pk>/",
        views.PatientViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="patient-detail",
    ),
    # Doctors
    path(
        "doctors/",
        views.DoctorViewSet.as_view({"get": "list", "post": "create"}),
        name="doctor-list",
    ),
    path(
        "doctors/<int:pk>/",
        views.DoctorViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="doctor-detail",
    ),
    # Patient-Doctor mappings
    path("mappings/", views.MappingListCreateView.as_view(), name="mapping-list"),
    path("mappings/<int:pk>/", views.MappingDetailView.as_view(), name="mapping-detail"),
]

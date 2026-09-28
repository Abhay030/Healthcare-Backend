from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.generics import CreateAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Doctor, Patient, PatientDoctorMapping
from .permissions import IsDoctorOwnerOrReadOnly
from .serializers import (
    DoctorSerializer,
    MappingSerializer,
    PatientSerializer,
    RegisterSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class RegisterView(CreateAPIView):
    """POST /api/auth/register/ — create a new user with name, email and password."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# Login and token refresh are provided by djangorestframework-simplejwt
# (TokenObtainPairView / TokenRefreshView, wired up in api/urls.py).


# ---------------------------------------------------------------------------
# Patients (scoped to the authenticated user)
# ---------------------------------------------------------------------------


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Each user only ever sees their own patients.
        return Patient.objects.filter(created_by=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ---------------------------------------------------------------------------
# Doctors (shared directory; only the creator can update/delete)
# ---------------------------------------------------------------------------


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorOwnerOrReadOnly]

    def get_queryset(self):
        return Doctor.objects.all().order_by("name")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ---------------------------------------------------------------------------
# Patient-Doctor mappings
# ---------------------------------------------------------------------------


class MappingListCreateView(ListCreateAPIView):
    """GET/POST /api/mappings/ — list or create patient-doctor mappings (own patients only)."""

    serializer_class = MappingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            PatientDoctorMapping.objects.filter(patient__created_by=self.request.user)
            .select_related("patient", "doctor")
            .order_by("-assigned_at")
        )


class MappingDetailView(APIView):
    """
    /api/mappings/<pk>/ handles two operations on the same pattern (as per the assignment):

    GET    — pk is a PATIENT id: list all doctors assigned to that patient.
    DELETE — pk is a MAPPING id: remove that patient-doctor mapping.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk, created_by=request.user)
        mappings = patient.doctor_mappings.select_related("doctor").order_by("-assigned_at")
        return Response(MappingSerializer(mappings, many=True, context={"request": request}).data)

    def delete(self, request, pk):
        mapping = get_object_or_404(PatientDoctorMapping, pk=pk, patient__created_by=request.user)
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

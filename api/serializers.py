from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Doctor, Patient, PatientDoctorMapping

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "name",
            "age",
            "gender",
            "phone",
            "address",
            "medical_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_age(self, value):
        if value > 150:
            raise serializers.ValidationError("Age cannot be greater than 150.")
        return value

    def validate_phone(self, value):
        if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError("Phone can only contain digits, spaces, + and -.")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ["id", "name", "specialization", "phone", "email", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_phone(self, value):
        if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            raise serializers.ValidationError("Phone can only contain digits, spaces, + and -.")
        return value


class MappingSerializer(serializers.ModelSerializer):
    # For writes the patient must belong to the authenticated user (set in __init__).
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(source="doctor.specialization", read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = [
            "id",
            "patient",
            "doctor",
            "patient_name",
            "doctor_name",
            "doctor_specialization",
            "assigned_at",
        ]
        read_only_fields = ["id", "assigned_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A user may only map their own patients.
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["patient"].queryset = Patient.objects.filter(created_by=request.user)

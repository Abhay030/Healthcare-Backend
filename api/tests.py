from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Doctor, Patient

User = get_user_model()


class AuthTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            reverse("register"),
            {"name": "Test User", "email": "test@example.com", "password": "strongpass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertNotIn("password", response.data)

        response = self.client.post(
            reverse("login"),
            {"email": "test@example.com", "password": "strongpass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_register_rejects_duplicate_email_and_weak_password(self):
        payload = {"name": "Test User", "email": "test@example.com", "password": "strongpass123"}
        self.client.post(reverse("register"), payload)
        response = self.client.post(reverse("register"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

        response = self.client.post(
            reverse("register"),
            {"name": "Short", "email": "other@example.com", "password": "short"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)


class PatientTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@example.com", name="Alice", password="alicepass123")
        self.bob = User.objects.create_user(email="bob@example.com", name="Bob", password="bobpass123")
        self.client.force_authenticate(self.alice)

    def patient_payload(self, **overrides):
        payload = {"name": "John Doe", "age": 30, "gender": "male", "phone": "9876543210"}
        payload.update(overrides)
        return payload

    def test_patient_crud(self):
        # Create
        response = self.client.post(reverse("patient-list"), self.patient_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        patient_id = response.data["id"]
        self.assertEqual(Patient.objects.get(pk=patient_id).created_by, self.alice)

        # List
        response = self.client.get(reverse("patient-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Retrieve / update / delete
        url = reverse("patient-detail", args=[patient_id])
        response = self.client.get(url)
        self.assertEqual(response.data["name"], "John Doe")

        response = self.client.put(url, self.patient_payload(name="John Updated"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "John Updated")

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(pk=patient_id).exists())

    def test_patients_are_scoped_to_the_owner(self):
        self.client.post(reverse("patient-list"), self.patient_payload())
        self.client.force_authenticate(self.bob)
        response = self.client.get(reverse("patient-list"))
        self.assertEqual(response.data, [])


class MappingTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(email="alice@example.com", name="Alice", password="alicepass123")
        self.client.force_authenticate(self.alice)
        self.patient = Patient.objects.create(created_by=self.alice, name="John", age=30, gender="male")
        self.doctor = Doctor.objects.create(created_by=self.alice, name="Dr. Smith", specialization="Cardiology")

    def test_mapping_flow(self):
        # Assign a doctor to a patient
        response = self.client.post(
            reverse("mapping-list"), {"patient": self.patient.pk, "doctor": self.doctor.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mapping_id = response.data["id"]

        # Duplicate assignment is rejected
        response = self.client.post(
            reverse("mapping-list"), {"patient": self.patient.pk, "doctor": self.doctor.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # List all mappings
        response = self.client.get(reverse("mapping-list"))
        self.assertEqual(len(response.data), 1)

        # Doctors assigned to a specific patient
        response = self.client.get(reverse("mapping-detail", args=[self.patient.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["doctor_name"], "Dr. Smith")

        # Remove the mapping
        response = self.client.delete(reverse("mapping-detail", args=[mapping_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(reverse("mapping-detail", args=[self.patient.pk]))
        self.assertEqual(response.data, [])

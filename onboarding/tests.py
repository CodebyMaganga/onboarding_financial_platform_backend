from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from onboarding.models import Forms, ClientSubmission

User = get_user_model()

class OnboardingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="newUser", password="Passcode123"
        )
        self.client.force_authenticate(user=self.user)

    def test_register_user(self):
        url = reverse("register")
        data = {
            "username": "newuser",
            "password": "secure123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_form(self):
        url = reverse("forms") 
        data = {"name": "Test Form", "description": "Form for testing"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Forms.objects.count(), 1)

    def test_submission_creation(self):
        form = Forms.objects.create(name="Form A", created_by=self.user)
        url = reverse("submissions")
        data = {"form": form.id, "data": {"field1": "value"}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClientSubmission.objects.count(), 1)

    def test_unauthorized_access(self):
        self.client.logout()
        url = reverse("forms")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



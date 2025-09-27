from django.shortcuts import render
from rest_framework import viewsets,generics
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings,FormField
from .serializers import FormsSerializer, FormVersionSerializer, ClientSubmissionSerializer, NotificationSettingsSerializer,RegisterSerializer
from rest_framework.permissions import DjangoModelPermissions
from django.contrib.auth.models import User



# Create your views here.

class FormsViewSet(viewsets.ModelViewSet):
    queryset = Forms.objects.all()
    serializer_class = FormsSerializer
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        # Save the form
        form = serializer.save(created_by=self.request.user)

        # Create initial version
        version = FormVersion.objects.create(
            form=form,
            version=1,
            schema=form.schema,
            is_active=True
        )

        # Create fields for this version only
        for field in form.schema.get("fields", []):
            FormField.objects.create(
                form_version=version,
                name=field["name"],
                field_type=field["type"],
                required=field.get("required", False)
            )

    def perform_update(self, serializer):
        # Save form update
        form = serializer.save()

        # Get latest version number
        last_version = FormVersion.objects.filter(form=form).order_by('-version').first()
        new_version_number = (last_version.version + 1) if last_version else 1

        # Deactivate old versions
        FormVersion.objects.filter(form=form).update(is_active=False)

        # Create new version
        version = FormVersion.objects.create(
            form=form,
            version=new_version_number,
            schema=form.schema,
            is_active=True
        )

        form.version = new_version_number
        form.save(update_fields=['version'])

        # Create fields for this new version only
        for field in form.schema.get("fields", []):
            FormField.objects.create(
                form_version=version,
                name=field["name"],
                field_type=field["type"],
                required=field.get("required", False)
            )

class FormVersionViewSet(viewsets.ModelViewSet):
    queryset = FormVersion.objects.all()
    serializer_class = FormVersionSerializer
    permission_classes = [DjangoModelPermissions]

class ClientSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ClientSubmission.objects.all()
    serializer_class = ClientSubmissionSerializer
    permission_classes = [DjangoModelPermissions]

class NotificationSettingsViewSet(viewsets.ModelViewSet):
    queryset = NotificationSettings.objects.all()
    serializer_class = NotificationSettingsSerializer
    permission_classes = [DjangoModelPermissions]

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []
from django.shortcuts import render
from rest_framework import viewsets,generics
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings,FormField,SystemLogs
from .serializers import FormsSerializer, FormVersionSerializer, ClientSubmissionSerializer, NotificationSettingsSerializer,RegisterSerializer,SystemLogsSerializer,CustomTokenObtainPairSerializer
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView


User = get_user_model()




# Create your views here.

def log_action(user, action, obj, message=""):
    SystemLogs.objects.create(
        user=user,
        action=action,
        object_type=obj.__class__.__name__.upper(),
        object_id=str(obj.id),
        message=message or f"{action} {obj.__class__.__name__} {obj}"
    )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
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
        for section in form.schema:  
            for field in section.get("fields", []):
                FormField.objects.create(
                form_version=version,
                name=field.get("label"),  
                field_type=field.get("type"),
                required=field.get("required", False)
            )
        
        log_action(self.request.user, "CREATE", form, message=f"Created form {form.name}")
        
       

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
        for section in form.schema:  
            for field in section.get("fields", []):
                FormField.objects.create(
                form_version=version,
                name=field.get("label"),  
                field_type=field.get("type"),
                required=field.get("required", False)
            )
        
        log_action(self.request.user, "UPDATE", form, message=f"Updated form {form.name}")
                
        

    
    def perform_destroy(self, instance):
        log_action(self.request.user, "DELETE", instance, message=f"Deleted form {instance.name}")
        instance.delete()


class FormVersionViewSet(viewsets.ModelViewSet):
    queryset = FormVersion.objects.all()
    serializer_class = FormVersionSerializer
    permission_classes = [DjangoModelPermissions]

class ClientSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ClientSubmission.objects.all()
    serializer_class = ClientSubmissionSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        submission = serializer.save(created_by=self.request.user)
        log_action(self.request.user, "SUBMIT", submission, message=f" Client Submitted: {submission.form.name}")
    
    def perform_destroy(self, instance):
        log_action(self.request.user, "NOTIFY", instance, message=f"Client Deleted: {instance.form.name}")
        instance.delete()
    

class NotificationSettingsViewSet(viewsets.ModelViewSet):
    queryset = NotificationSettings.objects.all()
    serializer_class = NotificationSettingsSerializer
    permission_classes = [DjangoModelPermissions]

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []

class SystemLogsViewSet(viewsets.ModelViewSet):
    queryset = SystemLogs.objects.all()
    serializer_class = SystemLogsSerializer
    permission_classes = [DjangoModelPermissions]   


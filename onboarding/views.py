from django.shortcuts import render
from rest_framework import viewsets,generics
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings,FormField,SystemLogs
from .serializers import FormsSerializer, FormVersionSerializer, ClientSubmissionSerializer, NotificationSettingsSerializer,RegisterSerializer,SystemLogsSerializer,CustomTokenObtainPairSerializer
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from .tasks import send_log_notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync




User = get_user_model()




# Create your views here.

def log_action(user, action, obj, message=""):
    log = SystemLogs.objects.create(
        user=user,
        action=action,
        object_type=obj.__class__.__name__.upper(),
        object_id=str(obj.id),
        message=message or f"{action} {obj.__class__.__name__} {obj}"
    )
    send_log_notification.delay(
        user.id,
        "New Log Entry",
        log.message,
        str(log.created_at)
    )

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
from rest_framework.decorators import action
from rest_framework.response import Response

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
        
        # REMOVED THESE TWO LINES - they were causing the error:
        # form.version = new_version_number
        # form.save(update_fields=['version'])
        
        # Create fields for this new version only
        for section in form.schema:
            for field in section.get("fields", []):
                FormField.objects.create(
                    form_version=version,
                    name=field.get("label"),
                    field_type=field.get("type"),
                    required=field.get("required", False)
                )
        
        log_action(self.request.user, "UPDATE", form, message=f"Updated form {form.name} to version {new_version_number}")
    
    def perform_destroy(self, instance):
        log_action(self.request.user, "DELETE", instance, message=f"Deleted form {instance.name}")
        instance.delete()
    
    # Optional: Add these endpoints to view version history
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of a specific form
        GET /api/forms/{id}/versions/
        """
        form = self.get_object()
        versions = form.versions.order_by('-version')
        
        data = [{
            'version': v.version,
            'is_active': v.is_active,
            'created_at': v.created_at,
            'schema': v.schema
        } for v in versions]
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def version_detail(self, request, pk=None):
        """Get a specific version
        GET /api/forms/{id}/version_detail/?version=2
        """
        form = self.get_object()
        version_number = request.query_params.get('version')
        
        if not version_number:
            return Response({'error': 'version parameter required'}, status=400)
        
        try:
            version = form.versions.get(version=version_number)
            return Response({
                'version': version.version,
                'is_active': version.is_active,
                'created_at': version.created_at,
                'schema': version.schema
            })
        except FormVersion.DoesNotExist:
            return Response({'error': 'Version not found'}, status=404)
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
    permission_classes = [AllowAny]

class SystemLogsViewSet(viewsets.ModelViewSet):
    queryset = SystemLogs.objects.all()
    serializer_class = SystemLogsSerializer
    permission_classes = [DjangoModelPermissions]   


from rest_framework import serializers
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings,ClientSubmissionData, SystemLogs,FormField
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
 def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom user data
        data['user'] = {
            "id": self.user.id,
            "username": self.user.username,
            "role": self.user.role,
        }

        return data




class FormsSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()

    class Meta:
        model = Forms
        fields = '__all__'
    
    def get_latest_version(self, obj):
        version = obj.versions.order_by("-version").first()
        return version.version if version else None
    
    def get_version(self, obj):
        version = obj.versions.filter(is_active=True).order_by("-created_at").first()
        return version.version if version else None

class FormVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormVersion
        fields = '__all__'


class ClientSubmissionDataSerializer(serializers.ModelSerializer):
    field = serializers.SlugRelatedField(
        slug_field="id",
        queryset=FormField.objects.all()
    )
    class Meta:
        model = ClientSubmissionData
        fields = ["field", "value"]


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = '__all__'

class ClientSubmissionSerializer(serializers.ModelSerializer):
    submission_data = ClientSubmissionDataSerializer(many=True)

    class Meta:
        model = ClientSubmission
        fields = ['id', 'form', 'form_version', 'submission_data', 'created_at', 'created_by']
       

    def create(self, validated_data):
        
        submission_data = validated_data.pop('submission_data', [])
        submission = ClientSubmission.objects.create(**validated_data)

        for data in submission_data:
            ClientSubmissionData.objects.create(submission=submission, **data)

        return submission
    
    

    
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    


class SystemLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemLogs
        fields = ['id', 'action', 'object_type', 'object_id', 'message', 'created_at']

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        return SystemLogs.objects.create(user=user, **validated_data)

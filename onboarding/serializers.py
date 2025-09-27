from rest_framework import serializers
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings,ClientSubmissionData
from django.contrib.auth.models import User

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
    field_id = serializers.PrimaryKeyRelatedField(
        source="field", queryset=Forms.objects.all()
    )

    class Meta:
        model = ClientSubmissionData
        fields = ["field_id", "value"]


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = '__all__'

class ClientSubmissionSerializer(serializers.ModelSerializer):
    submission_data = ClientSubmissionDataSerializer(many=True)

    class Meta:
        model = ClientSubmission
        fields = ["id", "form", "form_version", "created_by", "submission_data"]

    def validate(self, data):
        form_version = data["form_version"]
        submission_data = data["submission_data"]

        # Collect submitted field IDs
        submitted_field_ids = [item["field"].id for item in submission_data]

        # Get required fields for this form_version
        required_fields = form_version.fields.filter(required=True)

        # Check missing required fields
        missing = [
            f.name for f in required_fields if f.id not in submitted_field_ids
        ]
        if missing:
            raise serializers.ValidationError(
                {"missing_fields": f"Required fields missing: {', '.join(missing)}"}
            )

        # Validate field types
        for item in submission_data:
            field = item["field"]
            value = item["value"]

            if field.field_type == "number":
                try:
                    float(value)
                except ValueError:
                    raise serializers.ValidationError(
                        {field.name: "Expected a number"}
                    )
            elif field.field_type == "date":
                from datetime import datetime

                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise serializers.ValidationError(
                        {field.name: "Expected a date in YYYY-MM-DD format"}
                    )

        return data

    def create(self, validated_data):
        submission_data = validated_data.pop("submission_data")
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
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('client', 'Client'),
    )

    role = models.CharField(max_length=100, choices=ROLE_CHOICES, default='client')

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role == 'client':
            self.role = 'admin'
        super().save(*args, **kwargs)

class Forms(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    schema = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=100)
    notification_emails = models.JSONField(
        default=list, 
        help_text="List of emails to notify on submission"
    )

    class Meta:
        ordering = ['-created_at']
      

    def __str__(self):
        latest_version = self.versions.order_by('-version').first()
        version_num = latest_version.version if latest_version else 'No version'
        return f"{self.name} - Version: {version_num}"
    

class FormVersion(models.Model):
    form = models.ForeignKey(Forms, related_name='versions', on_delete=models.CASCADE)
    version = models.IntegerField()
    schema = models.JSONField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['form', 'version'], name='unique_form_version')
        ]


class ClientSubmission(models.Model):
    form = models.ForeignKey(Forms, related_name='submissions', on_delete=models.PROTECT)
    form_version = models.ForeignKey(FormVersion, related_name='submissions', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"Submission {self.id} for {self.form}"
    

class FormField(models.Model):
    form_version = models.ForeignKey(FormVersion, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50)  # 'string', 'date', 'number', etc.
    required = models.BooleanField(default=False)

    

    def __str__(self):
        return f"{self.name} ({self.field_type})"


class ClientSubmissionData(models.Model):
    submission = models.ForeignKey(ClientSubmission, related_name="submission_data", on_delete=models.CASCADE)
    field = models.ForeignKey(FormField, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"{self.field.name}: {self.value}"

class NotificationSettings(models.Model):
    form = models.ForeignKey(Forms,related_name='notifications', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=(('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'Whatsapp')))
    config = models.JSONField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class SystemLogs(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("SUBMIT", "Submit"),
        ("NOTIFY", "Notify"),
        ("OTHER", "Other"),
    ]

    OBJECT_TYPE_CHOICES = [
        ("FORM", "Form"),
        ("FORM_VERSION", "Form Version"),
        ("SUBMISSION", "Submission"),
        ("FIELD", "Field"),
        ("NOTIFICATION_SETTINGS", "Notification Settings"),
        ("SYSTEM_LOGS", "System Logs"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=100, choices=ACTION_CHOICES) 
    object_type = models.CharField(max_length=100, choices=OBJECT_TYPE_CHOICES) 
    object_id = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.object_type} - {self.object_id}"

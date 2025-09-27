from django.contrib import admin
from .models import Forms, FormVersion, ClientSubmission, NotificationSettings

# Register your models here.
admin.site.register(Forms)
admin.site.register(FormVersion)
admin.site.register(ClientSubmission)
admin.site.register(NotificationSettings)

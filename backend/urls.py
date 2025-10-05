"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from onboarding.views import (
    FormsViewSet, FormVersionViewSet,
    ClientSubmissionViewSet, NotificationSettingsViewSet,RegisterView,SystemLogsViewSet,CustomTokenObtainPairView
)

router = DefaultRouter()
router.register(r'forms', FormsViewSet)
router.register(r'form-versions', FormVersionViewSet)
router.register(r'submissions', ClientSubmissionViewSet)
router.register(r'notifications', NotificationSettingsViewSet)
router.register(r'system-logs', SystemLogsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path("api/auth/logout/", TokenBlacklistView.as_view(), name="logout"),
]


from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthCheckViewSet

# Initialize the DRF router
router = DefaultRouter()
router.register(r'healthcheck', HealthCheckViewSet, basename='healthcheck')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('tours/', include('tours.urls')),
    path('wholesale/', include('wholesale.urls')),
]

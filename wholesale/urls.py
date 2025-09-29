from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ExternalApiCallViewSet, ProviderSyncViewSet, ProgramTourViewSet # Import the new ViewSets

app_name = 'wholesale' # Optional: good practice for namespacing URLs

# Initialize the router
router = DefaultRouter()

# Register the ViewSet
# The r'call-external-api' is the URL prefix for this ViewSet.
# The basename is used for generating URL names, e.g., 'call_wholesale_external_api-detail'.
router.register(r'call-external-api', ExternalApiCallViewSet, basename='call_wholesale_external_api')

# Register the new ProviderSyncViewSet
# This will create URLs like /providers/ and /providers/{name}/sync-countries/
router.register(r'providers', ProviderSyncViewSet, basename='provider-sync')
# Register the ProgramTourViewSet
router.register(r'program-tours', ProgramTourViewSet, basename='programtour')

urlpatterns = router.urls
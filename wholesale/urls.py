from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExternalApiCallViewSet, ProviderSyncViewSet, ProgramTourViewSet
from . import evaluation_views

app_name = 'wholesale'

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

urlpatterns = [
    path('', include(router.urls)),

    # Evaluation tool URLs
    path('evaluation/', evaluation_views.evaluation_home, name='evaluation_home'),
    path('evaluation/create/', evaluation_views.create_session, name='evaluation_create'),
    path('evaluation/<uuid:session_id>/upload/', evaluation_views.upload_samples, name='evaluation_upload_samples'),
    path('evaluation/<uuid:session_id>/analyze/', evaluation_views.analyze_session, name='evaluation_analyze'),
    path('evaluation/<uuid:session_id>/generate/', evaluation_views.generate_code, name='evaluation_generate'),
    path('evaluation/<uuid:session_id>/download/<str:code_type>/', evaluation_views.download_code, name='evaluation_download'),
    path('evaluation/<uuid:session_id>/ai-prompt/', evaluation_views.get_ai_prompt, name='evaluation_ai_prompt'),
    path('evaluation/ajax/load-db-samples/', evaluation_views.ajax_load_database_samples, name='evaluation_ajax_load_db_samples'),
    path('evaluation/compare/', evaluation_views.compare_providers, name='provider_compare'),
]
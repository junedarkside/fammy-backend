import requests
from rest_framework.response import Response
from rest_framework import status, viewsets  # Import viewsets
from decouple import config
import logging
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action  # For custom actions
# Import Provider and ProgramTour models
from .models import Provider, ProgramTour
from .data_sync_service import DataSyncService  # Import DataSyncService
from .serializers import ProgramTourSerializer  # Import the new serializer

# Create your views here.

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Changed from APIView to ViewSet
class ExternalApiCallViewSet(viewsets.ViewSet):
    """
    A ViewSet that calls an external API endpoint for a specific provider.
    The provider is identified by a 'company_name' slug in the URL.
    """
    lookup_field = 'company_name'  # This tells DRF to use 'company_name' from URL for lookup

    def retrieve(self, request, company_name=None):  # Changed from get to retrieve
        # company_name is the slug captured from the URL, e.g., "zego"
        logger.debug(
            f"Received request for company: {company_name}. Full request: {request}")

        # Fetch the provider based on the company_name slug
        # Ensure your Provider model has a 'name' field that matches the slug
        # or consider adding a dedicated 'slug' field to the Provider model.
        provider = get_object_or_404(
            Provider, name__iexact=company_name)  # Case-insensitive match

        api_url_base = provider.base_url
        api_token = provider.token
        if not api_url_base:
            logger.error(
                f"API endpoint URL not configured for provider '{provider.name}'.")
            return Response(
                {"error": f"API endpoint URL not configured for provider '{provider.name}'."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        if not api_token:
            logger.error(
                f"API token not configured for provider '{provider.name}'.")
            return Response(
                {"error": f"API token not configured for provider '{provider.name}'."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",  # Tell the server you expect JSON
            "auth-token": api_token
        }

        # Construct the full API URL for countries endpoint
        external_api_path = "/countries"  # Default to countries endpoint
        api_url_to_call = f"{api_url_base.rstrip('/')}{external_api_path}"

        logger.info(
            f"Requesting URL for provider '{provider.name}': {api_url_to_call}")
        logger.debug(f"Headers for external API call: {headers}")

        response_obj = None  # Initialize to ensure it's available in except blocks if needed
        try:
            # Make the GET request with a timeout
            response_obj = requests.get(
                api_url_to_call, headers=headers, timeout=10)  # 10-second timeout
            logger.info(
                f"External API response status: {response_obj.status_code}")

            # Raise an HTTPError for bad responses (4XX or 5XX)
            response_obj.raise_for_status()

            # Parse the JSON response from the external API
            data = response_obj.json()

            return Response(data, status=status.HTTP_200_OK)

        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred while calling external API for '{provider.name}': {http_err}"
            error_details = {"raw_response": "Failed to retrieve response text."}
            current_response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            if response_obj is not None:
                error_details["raw_response"] = response_obj.text
                current_response_status = response_obj.status_code

            logger.error(f"{error_message}, Details: {error_details}, Status Code: {current_response_status}")
            return Response({"error": error_message, "details": error_details}, status=current_response_status)

        except requests.exceptions.JSONDecodeError as json_decode_err:
            error_message = f"Failed to decode JSON response from external API for '{provider.name}'."
            raw_text = response_obj.text if response_obj else "No response object available."
            status_code = response_obj.status_code if response_obj else "N/A"
            logger.error(f"{error_message} Status: {status_code}. Error: {json_decode_err}")
            return Response(
                {"error": error_message, "details": f"Non-JSON response. Status: {status_code}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Error connecting to external API for '{provider.name}': {conn_err}")
            return Response(
                {"error": f"Error connecting to external API for '{provider.name}': {conn_err}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Request to external API for '{provider.name}' timed out: {timeout_err}")
            return Response(
                {"error": f"Request to external API for '{provider.name}' timed out: {timeout_err}"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except requests.exceptions.RequestException as req_err:
            logger.error(f"An error occurred during the request to external API for '{provider.name}': {req_err}")
            return Response(
                {"error": f"An error occurred during the request to external API for '{provider.name}': {req_err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProviderSyncViewSet(viewsets.ViewSet):
    """
    A ViewSet for triggering data synchronization tasks for a Provider.
    The provider is identified by its 'name' in the URL.
    """
    lookup_field = 'name'  # Use provider's name for lookup

    @action(detail=True, methods=['post'], url_path='sync-countries', url_name='sync-countries')
    def sync_countries_for_provider(self, request, name=None):
        """
        Triggers the synchronization of countries for the specified provider.
        Expects a POST request to /providers/{provider_name}/sync-countries/
        """
        logger.info(
            f"Received request to sync countries for provider: {name}")

        # Retrieve the provider by name (case-insensitive)
        provider = get_object_or_404(Provider, name__iexact=name)
        logger.debug(f"Provider object retrieved for sync: {provider}")

        try:
            sync_service = DataSyncService(provider)
            # This method handles its own logging and transaction
            result = sync_service.sync_countries()
            # DataSyncService.sync_countries() returns 'errors': 1 if the API call failed or returned no data.
            if result.get('errors', 0) > 0:
                logger.error(
                    f"Country sync failed for {provider.name} due to API/data issue: {result.get('message')}")
                # HTTP 502 Bad Gateway if the upstream API failed or returned no data
                return Response(result, status=status.HTTP_502_BAD_GATEWAY)

            logger.info(
                f"Country sync for {provider.name} completed: {result}")
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during country sync for provider '{name}': {str(e)}")
            return Response(
                {"error": "An unexpected server error occurred during the sync process.",
                    "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='sync-program-tours', url_name='sync-program-tours')
    def sync_program_tours_for_provider(self, request, name=None):
        """
        Triggers the synchronization of program tours for the specified provider.
        Expects a POST request to /providers/{provider_name}/sync-program-tours/
        """
        logger.info(
            f"Received request to sync program tours for provider: {name}")

        provider = get_object_or_404(Provider, name__iexact=name)
        logger.debug(
            f"Provider object retrieved for program tour sync: {provider}")

        try:
            sync_service = DataSyncService(provider)
            logger.info(f"Starting program tour sync for {provider.name}")
            # This method handles its own logging and transaction
            result = sync_service.sync_program_tours()

            # Check if the error is due to the initial API call failing to fetch tours
            if result.get('errors', 0) > 0 and "API request to fetch program tours" in result.get('message', "") and "failed" in result.get('message', ""):
                logger.error(
                    f"Program tour sync failed for {provider.name} due to API/data issue: {result.get('message')}")
                return Response(result, status=status.HTTP_502_BAD_GATEWAY)

            logger.info(
                f"Program tour sync for {provider.name} completed/attempted: {result}")
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during program tour sync for provider '{name}': {str(e)}")
            return Response(
                {"error": "An unexpected server error occurred during the program tour sync process.",
                    "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#     @action(detail=True, methods=['post'], url_path='sync-single-program-tour/(?P<product_code_url>[^/.]+)', url_name='sync-single-program-tour')
#     def sync_single_program_tour_for_wholesaler(self, request, name=None, product_code_url=None):
#         """
#         Triggers the synchronization of a single program tour, identified by product_id,
#         for the specified wholesaler.
#         Expects a POST request to /wholesalers/{wholesaler_name}/sync-single-program-tour/{product_code_from_url}/
#         """
#         logger.info(
#             f"Received request to sync single program tour (Code from URL: {product_code_url}) for wholesaler: {name}")

#         wholesaler = get_object_or_404(Wholesaler, name__iexact=name)
#         logger.debug(
#             f"Wholesaler object retrieved for single program tour sync: {wholesaler}")

#         if not product_code_url:
#             return Response({"error": "Product Code must be provided in the URL."}, status=status.HTTP_400_BAD_REQUEST)

#         # Find the local ProgramTour by product_code and wholesaler to get its numerical product_id
#         try:
#             local_program_tour = ProgramTour.objects.get(
#                 wholesaler=wholesaler,
#                 product_code__iexact=product_code_url  # Case-insensitive match for product_code
#             )
#             product_code = local_program_tour.product_code
#             logger.info(
#                 f"Found local tour. ProductCode: {product_code_url}, Numerical ProductID: {product_code}")
#         except ProgramTour.DoesNotExist:
#             logger.error(
#                 f"ProgramTour with ProductCode '{product_code_url}' not found locally for wholesaler '{wholesaler.name}'. Cannot sync.")
#             return Response({"error": f"ProgramTour with ProductCode '{product_code_url}' not found locally for this wholesaler."}, status=status.HTTP_404_NOT_FOUND)

#         if not wholesaler.is_active:
#             logger.warning(
#                 f"Wholesaler '{wholesaler.name}' is not active. Single program tour sync aborted.")
#             return Response(
#                 {"error": f"Wholesaler '{wholesaler.name}' is not active and cannot be synced."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             sync_service = DataSyncService(wholesaler)
#             result = sync_service.sync_single_program_tour_by_id(product_code)
#             print('result', result)
#             if result.get('errors', 0) > 0:
#                 error_message_from_service = result.get('message', "")
#                 logger.debug(
#                     f"Single tour sync service for Wholesaler '{name}', ProductID '{product_code}' returned error. Message: '{error_message_from_service}'")

#                 status_code = status.HTTP_500_INTERNAL_SERVER_ERROR  # Default for processing errors

#                 # Check for specific error messages from the service to set appropriate HTTP status
#                 # The message "No valid tour data dictionary found..." implies the API didn't find/return the specific resource.
#                 if "not found by API" in error_message_from_service or "No valid tour data dictionary found" in error_message_from_service:
#                     status_code = status.HTTP_404_NOT_FOUND
#                 # This condition checks if the initial API call itself failed (e.g., network error, auth error before getting data)
#                 elif "API request for program tour" in error_message_from_service and "failed" in error_message_from_service:
#                     status_code = status.HTTP_502_BAD_GATEWAY
#                 logger.info(
#                     f"Returning status {status_code} for single tour sync error (Wholesaler: '{name}', ProductID: '{numerical_product_id}'): {error_message_from_service}")
#                 return Response(result, status=status_code)

#             return Response(result, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(
#                 f"An unexpected error occurred during single program tour sync for wholesaler '{name}', ProductCode from URL '{product_code_url}', Numerical ProductID '{numerical_product_id}': {str(e)}")
#             return Response({"error": "An unexpected server error occurred during the sync process.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProgramTourViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows ProgramTours to be viewed.
    Supports filtering by provider name via the 'provider' query parameter.
    Example: /api/wholesale/program-tours/?provider=Zego
    """
    serializer_class = ProgramTourSerializer
    lookup_field = 'code'  # Use code for detail view lookups

    def get_queryset(self):
        """
        Optionally restricts the returned program tours to a given provider,
        by filtering against a `provider` query parameter in the URL.
        """
        queryset = ProgramTour.objects.select_related(
            'provider', 'country'
        ).prefetch_related(
            'periods', 'periods__flights', 'itineraries'
        ).all()

        provider_name = self.request.query_params.get('provider')
        if provider_name is not None:
            # Case-insensitive filtering for provider name
            queryset = queryset.filter(
                provider__name__iexact=provider_name)
        return queryset

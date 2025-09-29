from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

class HealthCheckViewSet(viewsets.ViewSet):
    """
    A simple health check endpoint.
    """
    
    def list(self, request):
        """
        Handle the GET request to the health check endpoint.
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

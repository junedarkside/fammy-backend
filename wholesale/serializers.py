from rest_framework import serializers
from .models import ProgramTour, Country, Provider, Period, Flight, Itinerary


class ProviderNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ['name', 'code']


class CountryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name', 'provider_code']


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        exclude = ['provider', 'period', 'program'] # Exclude the direct links to avoid circularity


class PeriodSerializer(serializers.ModelSerializer):
    flights = FlightSerializer(many=True, read_only=True)

    class Meta:
        model = Period
        exclude = ['provider', 'program'] # Exclude the direct link back to program tour


class ItinerarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        exclude = ['provider', 'program'] # Exclude the direct link back to program tour


class ProgramTourSerializer(serializers.ModelSerializer):
    provider = ProviderNameSerializer(read_only=True) # Nested representation
    country = CountryNameSerializer(read_only=True) # Nested representation

    # Add nested serializers for related models
    periods = PeriodSerializer(many=True, read_only=True)
    itineraries = ItinerarySerializer(many=True, read_only=True)
    # Locations are stored as JSON field
    # Images are handled as single image_url field

    class Meta:
        model = ProgramTour
        fields = '__all__' # Or list specific fields you want to expose
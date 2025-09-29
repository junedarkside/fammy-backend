from rest_framework import serializers
from .models import Tour, Operator, Airline, Country, Location, TravelDate
from datetime import timedelta


class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = "__all__"


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = "__all__"


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class LocationSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = Location
        fields = "__all__"


class TravelDateSerializer(serializers.ModelSerializer):
    date_range = serializers.SerializerMethodField()

    class Meta:
        model = TravelDate
        fields = "__all__"

    def get_date_range(self, obj):
        if obj.date_start and obj.date_end:
            return (obj.date_end - obj.date_start).days+1
        return None


class TourSerializer(serializers.ModelSerializer):
    operator = OperatorSerializer(read_only=True)
    airline = AirlineSerializer(read_only=True)
    countries = CountrySerializer(many=True, read_only=True)
    locations = LocationSerializer(many=True, read_only=True)
    travel_dates = TravelDateSerializer(many=True, read_only=True)

    class Meta:
        model = Tour
        fields = "__all__"

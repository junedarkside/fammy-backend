from django.contrib import admin
from .models import Provider, Country, ProgramTour, Period, Flight, Itinerary, ProviderMeta

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'base_url', 'api_version', 'tour_count')
    search_fields = ('name', 'code')

    def tour_count(self, obj):
        return obj.program_tours.count()
    tour_count.short_description = 'Tours'

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_code', 'provider', 'normalized_name', 'iso_code')
    search_fields = ('name', 'provider_code', 'normalized_name', 'iso_code')
    list_filter = ('provider', 'iso_code')
    readonly_fields = ('normalized_name', 'iso_code')

class PeriodInline(admin.TabularInline):
    model = Period
    extra = 0
    readonly_fields = ('external_id', 'code', 'start_date', 'end_date', 'status', 'base_prices', 'end_prices')

class ItineraryInline(admin.StackedInline):
    model = Itinerary
    extra = 0
    readonly_fields = ('external_id', 'day', 'description', 'hotel', 'hotel_star', 'breakfast', 'lunch', 'dinner')

@admin.register(ProgramTour)
class ProgramTourAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'provider', 'country_name', 'days', 'nights', 'last_synced')
    search_fields = ('name', 'code', 'provider__name', 'country_name')
    list_filter = ('provider', 'country', 'last_synced')
    inlines = [PeriodInline, ItineraryInline]
    readonly_fields = ('external_id', 'last_synced')

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('code', 'program', 'start_date', 'end_date', 'status', 'seats_available')
    search_fields = ('code', 'program__name', 'program__code')
    list_filter = ('status', 'provider', 'start_date')
    readonly_fields = ('external_id', 'update_date')

    def seats_available(self, obj):
        if obj.seats and obj.booked:
            return obj.seats - obj.booked
        return obj.seats or 0
    seats_available.short_description = 'Available'

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_no', 'airline_name', 'route', 'schedule', 'program', 'period')
    search_fields = ('flight_no', 'airline_name', 'route')
    list_filter = ('airline_name', 'provider')

    def schedule(self, obj):
        if obj.departure_time and obj.arrival_time:
            return f"{obj.departure_time} - {obj.arrival_time}"
        return "N/A"
    schedule.short_description = 'Schedule'

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('program', 'day', 'hotel', 'meal_info')
    search_fields = ('program__name', 'program__code', 'hotel')
    list_filter = ('program__provider',)

    def meal_info(self, obj):
        meals = []
        if obj.breakfast:
            meals.append('B')
        if obj.lunch:
            meals.append('L')
        if obj.dinner:
            meals.append('D')
        return '/'.join(meals) if meals else 'No meals'
    meal_info.short_description = 'Meals'

@admin.register(ProviderMeta)
class ProviderMetaAdmin(admin.ModelAdmin):
    list_display = ('provider', 'last_period_update', 'fetched_at')
    list_filter = ('provider',)

from django.contrib import admin
from .models import Country, Airline, Tour, Location, TravelDate, Operator, FlashSale

# Register your models here


class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_code')
    search_fields = ('name', 'country_code')


class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo')
    search_fields = ('name',)


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ("id", "get_travel_dates", "discount_amount", "start_time", "end_time", "is_active")
    list_filter = ("is_active", "start_time", "end_time")
    search_fields = ("travel_dates__tour__name",)

    def get_travel_dates(self, obj):
        return ", ".join(
            [f"{td.tour.name}: {td.date_start} to {td.date_end}" for td in obj.travel_dates.all()]
        )
    get_travel_dates.short_description = "Tour & Travel Dates"

    filter_horizontal = ("travel_dates",)


class TravelDateInline(admin.TabularInline):
    model = TravelDate
    extra = 1


class TourAdmin(admin.ModelAdmin):
    list_display = ('name', 'operator', 'slug', 'price',
                    'duration', 'hotel_stars', 'airline')
    search_fields = ('name', 'operator__name', 'slug', 'price',
                     'duration', 'hotel_stars', 'airline__name')
    list_filter = ('airline', 'countries', 'locations', 'operator')
    filter_horizontal = ('countries', 'locations')
    inlines = [TravelDateInline]

    def get_queryset(self, request):
        """Customize the queryset to display relevant fields in the admin list."""
        queryset = super().get_queryset(request)
        # Prefetch related data to optimize query performance
        queryset = queryset.prefetch_related('countries', 'locations',)
        return queryset


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)


class TravelDateAdmin(admin.ModelAdmin):
    list_display = ('tour', 'rate', 'availability',
                    'date_start', 'date_end', 'calculate_date_range')
    list_filter = ('tour',)

    def calculate_date_range(self, obj):
        return obj.calculate_date_range()
    calculate_date_range.short_description = "Date Range (days)"


class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'description')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('name', 'email')
    
@admin.register(TravelDate)
class TravelDateAdmin(admin.ModelAdmin):
    list_display = ("tour", "date_start", "date_end", "rate", "availability", "get_flash_sale")
    list_filter = ("tour", "date_start", "date_end")
    search_fields = ("tour__name",)

    def get_flash_sale(self, obj):
        flash_sales = obj.flash_sales.filter(is_active=True)
        return ", ".join([f"{fs.discount_amount} THB off (until {fs.end_time})" for fs in flash_sales]) if flash_sales else "No Active Sale"
    get_flash_sale.short_description = "Active Flash Sale"


# Register models with custom admin configurations
admin.site.register(Country, CountryAdmin)
admin.site.register(Airline, AirlineAdmin)
admin.site.register(Tour, TourAdmin)
admin.site.register(Operator, OperatorAdmin)

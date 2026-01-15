from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from .models import Provider, Country, ProgramTour, Period, Flight, Itinerary, ProviderCategory, RawVendorData
from .data_sync_service import DataSyncService

def sync_data_for_provider(modeladmin, request, queryset):
    for provider in queryset:
        if not provider.is_active:
            modeladmin.message_user(request, f"Provider '{provider.name}' is not active. Skipping.", messages.WARNING)
            continue
        try:
            sync_service = DataSyncService(provider)
            
            # Sync countries
            countries_result = sync_service.sync_countries()
            country_message = (
                f"Countries - Created: {countries_result.get('created', 0)}, "
                f"Updated: {countries_result.get('updated', 0)}, "
                f"Errors: {countries_result.get('errors', 0)}"
            )

            # Sync program tours
            tours_result = sync_service.sync_program_tours()
            tour_message = (
                f"Tours - Created: {tours_result.get('created', 0)}, "
                f"Updated: {tours_result.get('updated', 0)}, "
                f"Errors: {tours_result.get('errors', 0)}"
            )

            # Combine messages
            full_message = (
                f"Sync for '{provider.name}' completed. "
                f"{country_message}. {tour_message}."
            )
            
            # Report API errors as warnings if some data was processed
            if countries_result.get('errors', 0) > 0 or tours_result.get('errors', 0) > 0:
                 modeladmin.message_user(request, f"Sync for '{provider.name}' had issues. {country_message}. {tour_message}", messages.WARNING)
            else:
                modeladmin.message_user(request, full_message, messages.SUCCESS)

        except Exception as e:
            modeladmin.message_user(request, f"An unexpected error occurred while syncing data for {provider.name}: {e}", messages.ERROR)

sync_data_for_provider.short_description = "Sync data for selected providers"


def sync_unique_inter_data(modeladmin, request, queryset):
    """Sync data for Unique Inter providers via categories"""
    for provider in queryset:
        if provider.code != 'unique_inter':
            modeladmin.message_user(
                request,
                f"'{provider.name}' is not Unique Inter. Use 'Sync data' action instead.",
                messages.WARNING
            )
            continue

        if not provider.is_active:
            modeladmin.message_user(
                request,
                f"Provider '{provider.name}' is not active.",
                messages.WARNING
            )
            continue

        # Import here to avoid circular imports
        from .management.commands.sync_unique_inter import Command as SyncCommand

        try:
            cmd = SyncCommand()
            # Run sync (fetches categories and syncs tours)
            cmd.handle(provider_code=provider.code, fetch_only=False, process_only=False, category=None)

            modeladmin.message_user(
                request,
                f"Unique Inter sync completed for '{provider.name}'. Check RawVendorData for results.",
                messages.SUCCESS
            )
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error syncing '{provider.name}': {str(e)}",
                messages.ERROR
            )

sync_unique_inter_data.short_description = "Sync Unique Inter data (category-based)"


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'base_url', 'api_version', 'tour_count', 'sync_button')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)
    actions = [sync_data_for_provider, sync_unique_inter_data]

    def get_queryset(self, request):
        """Optimize queryset with tour count annotation."""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            tours_count=Count('program_tours')
        )
        return queryset

    def tour_count(self, obj):
        """Display number of tours for this provider."""
        return obj.tours_count
    tour_count.short_description = 'Tours'
    tour_count.admin_order_field = 'tours_count'

    def sync_button(self, obj):
        """Display sync button for active providers."""
        if not obj.is_active:
            return format_html('<span style="color: #999;">Inactive</span>')

        url = reverse('admin:sync-provider', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background: #417690; color: white; text-decoration: none; border-radius: 4px;">Sync Now</a>',
            url
        )
    sync_button.short_description = 'Quick Sync'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:provider_id>/sync/', self.admin_site.admin_view(self.sync_provider_view), name='sync-provider'),
        ]
        return custom_urls + urls

    def sync_provider_view(self, request, provider_id):
        """
        Custom admin view for syncing a single provider.

        Handles both standard providers (via DataSyncService) and
        Unique Inter providers (via management command).

        Args:
            request: Django HttpRequest
            provider_id: Primary key of Provider to sync

        Returns:
            HttpResponse redirect to provider changelist
        """
        provider = get_object_or_404(Provider, pk=provider_id)

        if not provider.is_active:
            messages.warning(request, f"Provider '{provider.name}' is not active.")
            return redirect('admin:wholesale_provider_changelist')

        try:
            if provider.code == 'unique_inter':
                # Use Unique Inter sync
                from .management.commands.sync_unique_inter import Command as SyncCommand
                cmd = SyncCommand()
                cmd.handle(provider_code=provider.code, fetch_only=False, process_only=False, category=None)
                messages.success(request, f"Unique Inter sync completed for '{provider.name}'. Check RawVendorData for results.")
            else:
                # Use standard DataSyncService for Zego and others
                sync_service = DataSyncService(provider)

                countries_result = sync_service.sync_countries()
                tours_result = sync_service.sync_program_tours()

                country_msg = f"Countries: {countries_result.get('created', 0)} created, {countries_result.get('updated', 0)} updated"
                tour_msg = f"Tours: {tours_result.get('created', 0)} created, {tours_result.get('updated', 0)} updated"

                if countries_result.get('errors', 0) > 0 or tours_result.get('errors', 0) > 0:
                    messages.warning(request, f"Sync completed with issues. {country_msg}. {tour_msg}")
                else:
                    messages.success(request, f"Sync completed for '{provider.name}'. {country_msg}. {tour_msg}")
        except Exception as e:
            messages.error(request, f"Error syncing '{provider.name}': {str(e)}")

        return redirect('admin:wholesale_provider_changelist')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_code', 'provider', 'normalized_name', 'iso_code')
    search_fields = ('name', 'provider_code', 'normalized_name', 'iso_code')
    list_filter = ('provider', 'iso_code')
    list_select_related = ('provider',)
    readonly_fields = ('normalized_name', 'iso_code')

class PeriodInline(admin.TabularInline):
    model = Period
    extra = 0
    readonly_fields = ('external_id', 'code', 'start_date', 'end_date', 'status', 'base_prices', 'end_prices')

class ItineraryInline(admin.StackedInline):
    model = Itinerary
    extra = 0
    readonly_fields = ('external_id', 'day', 'description', 'hotel', 'hotel_star', 'breakfast', 'lunch', 'dinner')

class CountryStatusFilter(admin.SimpleListFilter):
    """Custom filter to show tours by country validation status"""
    title = 'country status'
    parameter_name = 'country_status'

    def lookups(self, request, model_admin):
        return (
            ('valid', 'Valid (has Country FK)'),
            ('needs_review', 'Needs Review (extracted but no FK)'),
            ('missing', 'Missing (no data)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'valid':
            return queryset.filter(country__isnull=False)
        elif self.value() == 'needs_review':
            return queryset.filter(country__isnull=True).exclude(country_name='')
        elif self.value() == 'missing':
            return queryset.filter(country__isnull=True, country_name='')


class ISOCountryFilter(admin.SimpleListFilter):
    """Filter tours by ISO country code (standardized across providers)"""
    title = 'ISO country code'
    parameter_name = 'iso_country'

    def lookups(self, request, model_admin):
        # Get distinct ISO codes from countries that have program tours
        iso_codes = Country.objects.filter(
            programtour__isnull=False
        ).exclude(
            iso_code=''
        ).values_list('iso_code', 'name').distinct().order_by('iso_code')

        # Build choices with format "VNM - Vietnam"
        # Group by ISO code and pick first country name as representative
        iso_dict = {}
        for iso_code, country_name in iso_codes:
            if iso_code not in iso_dict:
                iso_dict[iso_code] = country_name

        choices = [
            (iso, f"{iso} - {name}")
            for iso, name in sorted(iso_dict.items())
        ]

        # Add option for tours without country
        choices.append(('__none__', '(No Country)'))

        return choices

    def queryset(self, request, queryset):
        if self.value() == '__none__':
            return queryset.filter(country__isnull=True)
        elif self.value():
            return queryset.filter(country__iso_code=self.value())
        return queryset


class ItineraryStatusFilter(admin.SimpleListFilter):
    """Filter tours by itinerary availability"""
    title = 'itinerary status'
    parameter_name = 'itinerary_status'

    def lookups(self, request, model_admin):
        return (
            ('has_itinerary', 'Has Itinerary'),
            ('has_documents', 'Has Documents Only'),
            ('needs_manual', 'Needs Manual Entry'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'has_itinerary':
            return queryset.prefetch_related('itineraries').filter(
                itineraries__isnull=False
            ).distinct()
        elif self.value() == 'has_documents':
            return queryset.filter(
                itineraries__isnull=True
            ).filter(
                Q(file_pdf__isnull=False) | Q(file_word__isnull=False)
            ).exclude(
                Q(file_pdf='') & Q(file_word='')
            )
        elif self.value() == 'needs_manual':
            return queryset.filter(
                itineraries__isnull=True
            ).filter(
                Q(file_pdf__isnull=True) | Q(file_pdf='')
            ).filter(
                Q(file_word__isnull=True) | Q(file_word='')
            )
        return queryset


@admin.register(ProgramTour)
class ProgramTourAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'provider', 'country_display', 'itinerary_status', 'days', 'nights', 'last_synced')
    search_fields = ('name', 'code', 'provider__name', 'country_name')
    list_filter = ('provider', 'country', ISOCountryFilter, CountryStatusFilter, ItineraryStatusFilter, 'last_synced')
    inlines = [PeriodInline, ItineraryInline]
    readonly_fields = ('external_id', 'last_synced')
    list_per_page = 50
    ordering = ('-last_synced', 'name')

    def get_queryset(self, request):
        """Optimize queryset with select_related and annotations."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('country', 'provider')
        queryset = queryset.prefetch_related('itineraries')
        queryset = queryset.annotate(
            itinerary_count=Count('itineraries')
        )
        return queryset

    def country_display(self, obj):
        """
        Display country validation status with visual indicators.

        - Green ✓: Valid Country FK relationship
        - Orange ⚠: Extracted country_name but no FK (needs review)
        - Red ✗: No country data

        Used in ProgramTourAdmin list_display for data quality assessment.
        """
        if obj.country:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.country.name
            )
        elif obj.country_name:
            return format_html(
                '<span style="color: orange;">⚠ {} (needs review)</span>',
                obj.country_name
            )
        else:
            return format_html('<span style="color: red;">✗ No country</span>')

    country_display.short_description = 'Country Status'
    country_display.admin_order_field = 'country'

    def itinerary_status(self, obj):
        """
        Display itinerary availability with visual indicators.

        - Green ✓: Has complete day-by-day itinerary
        - Orange ⚠: Has PDF/Word documents only
        - Red ✗: Needs manual entry (no itinerary or documents)
        """
        itinerary_count = obj.itinerary_count
        has_pdf = bool(obj.file_pdf)
        has_word = bool(obj.file_word)

        if itinerary_count > 0:
            return format_html(
                '<span style="color: green;">✓ {} days</span>',
                itinerary_count
            )
        elif has_pdf or has_word:
            docs = []
            if has_pdf:
                docs.append('PDF')
            if has_word:
                docs.append('Word')
            return format_html(
                '<span style="color: orange;">⚠ {} only</span>',
                '/'.join(docs)
            )
        else:
            return format_html('<span style="color: red;">✗ Needs manual entry</span>')

    itinerary_status.short_description = 'Itinerary'

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('code', 'program', 'start_date', 'end_date', 'status', 'seats_available')
    search_fields = ('code', 'program__name', 'program__code')
    list_filter = ('status', 'provider', 'start_date')
    list_select_related = ('program', 'provider')
    readonly_fields = ('external_id', 'update_date')
    ordering = ('start_date', 'program')

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('program', 'provider')
        return queryset

    def seats_available(self, obj):
        """Calculate available seats (total - booked)."""
        if obj.seats and obj.booked:
            return obj.seats - obj.booked
        return obj.seats or 0
    seats_available.short_description = 'Available'

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_no', 'airline_name', 'route', 'schedule', 'program', 'period')
    search_fields = ('flight_no', 'airline_name', 'route')
    list_filter = ('airline_name', 'provider')
    list_select_related = ('program', 'period', 'provider')

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('program', 'period', 'provider')
        return queryset

    def schedule(self, obj):
        """Display flight schedule (departure - arrival)."""
        if obj.departure_time and obj.arrival_time:
            return f"{obj.departure_time} - {obj.arrival_time}"
        return "N/A"
    schedule.short_description = 'Schedule'

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('program', 'day', 'hotel', 'meal_info')
    search_fields = ('program__name', 'program__code', 'hotel')
    list_filter = ('program__provider',)

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('program', 'program__provider')
        return queryset

    def meal_info(self, obj):
        """Display abbreviated meal information (B/L/D)."""
        meals = []
        if obj.breakfast:
            meals.append('B')
        if obj.lunch:
            meals.append('L')
        if obj.dinner:
            meals.append('D')
        return '/'.join(meals) if meals else 'No meals'
    meal_info.short_description = 'Meals'

@admin.register(ProviderCategory)
class ProviderCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_id', 'provider', 'is_active', 'priority', 'total_tours', 'last_synced')
    search_fields = ('name', 'category_id', 'name_local')
    list_filter = ('provider', 'is_active')
    list_editable = ('is_active', 'priority')
    readonly_fields = ('last_synced', 'total_tours')
    ordering = ('provider', '-priority', 'name')

def process_raw_data(modeladmin, request, queryset):
    """
    Process selected raw vendor data records (Unique Inter format).

    Groups raw records by mainid (tour program ID), creates/updates
    ProgramTour and Period models, and tracks processing status.
    """
    from .data_sync_service import map_unique_inter_tour_data, map_unique_inter_period_data
    import logging

    logger = logging.getLogger(__name__)

    # Group by mainid (tour program) - Unique Inter specific
    tours_by_mainid = {}
    for raw_record in queryset.filter(provider__code='unique_inter'):
        mainid = raw_record.raw_json.get('mainid')
        if not mainid:
            logger.warning(f"Skipping raw record {raw_record.id} with no mainid")
            raw_record.error_message = 'No mainid in raw data'
            raw_record.save()
            continue

        if mainid not in tours_by_mainid:
            tours_by_mainid[mainid] = []
        tours_by_mainid[mainid].append(raw_record)

    tours_processed = 0
    periods_processed = 0
    errors = 0

    # Process each tour and its periods
    for mainid, raw_records in tours_by_mainid.items():
        try:
            # Create/update tour from first record
            first_raw = raw_records[0].raw_json
            tour_data = map_unique_inter_tour_data(first_raw)
            external_id = tour_data.pop('external_id')

            tour, tour_created = ProgramTour.objects.update_or_create(
                provider=raw_records[0].provider,
                external_id=external_id,
                defaults=tour_data
            )
            tours_processed += 1

            # Process each period (departure)
            for raw_record in raw_records:
                try:
                    period_data = map_unique_inter_period_data(raw_record.raw_json)
                    period_external_id = period_data.pop('external_id')

                    Period.objects.update_or_create(
                        provider=raw_record.provider,
                        external_id=period_external_id,
                        program=tour,
                        defaults=period_data
                    )
                    periods_processed += 1

                    # Mark as processed
                    raw_record.processed = True
                    raw_record.processed_at = timezone.now()
                    raw_record.error_message = ''
                    raw_record.save()

                except Exception as e:
                    raw_record.error_message = str(e)
                    raw_record.save()
                    errors += 1

        except Exception as e:
            # Mark all records for this tour as failed
            for raw_record in raw_records:
                raw_record.error_message = str(e)
                raw_record.save()
            errors += 1

    # Success message
    msg = f"Processed {tours_processed} tours, {periods_processed} periods"
    if errors:
        modeladmin.message_user(request, f"{msg}, {errors} errors", messages.WARNING)
    else:
        modeladmin.message_user(request, msg, messages.SUCCESS)

process_raw_data.short_description = "Process selected raw data into tours"


@admin.register(RawVendorData)
class RawVendorDataAdmin(admin.ModelAdmin):
    list_display = ('external_id', 'provider', 'category', 'endpoint_type', 'processed', 'fetched_at', 'has_error')
    search_fields = ('external_id', 'category')
    list_filter = ('provider', 'processed', 'endpoint_type', 'category', 'fetched_at')
    list_select_related = ('provider',)
    readonly_fields = ('fetched_at', 'processed_at', 'raw_json')
    list_per_page = 50
    ordering = ('-fetched_at', 'provider')
    actions = [process_raw_data]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('provider')
        return queryset

    def has_error(self, obj):
        """Check if raw data has processing errors."""
        return bool(obj.error_message)
    has_error.boolean = True
    has_error.short_description = 'Error'
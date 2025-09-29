# from django.db import models


# class Provider(models.Model):
#     name = models.CharField(max_length=255)
#     api_url = models.URLField()
#     api_token = models.CharField(max_length=512, blank=True, null=True, help_text="API token for the provider, if required. Store securely.")
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name

# class Product(models.Model):
#     provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
#     external_id = models.CharField(max_length=255, unique=True)
#     name = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     contract_start = models.DateField()
#     contract_end = models.DateField()


# class SeatAvailability(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     date = models.DateField()
#     seats_total = models.IntegerField()
#     seats_available = models.IntegerField()
   
    
# class Wholesaler(models.Model):
#     name = models.CharField(max_length=255)
#     api_base_url = models.URLField()
#     token = models.CharField(max_length=512, blank=True, null=True, help_text="API token for the wholesaler, if required.")
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name

#     class Meta:
#         verbose_name_plural = "Wholesalers"


# class Country(models.Model):
#     wholesaler = models.ForeignKey(Wholesaler, on_delete=models.CASCADE, related_name='countries')
#     country_code = models.CharField(max_length=10, primary_key=True, help_text="e.g., 'FRA', 'EX1'. Primary Key.") # unique=True is implied by primary_key=True
#     country_name = models.CharField(max_length=100, unique=True) # e.g., 'FRANCE', 'EXAMPLE COUNTRY01'
#     country_content = models.TextField(blank=True, null=True, help_text="Additional content or description for the country (used in admin).")

#     def __str__(self):
#         return f"{self.country_name} ({self.country_code})"

#     class Meta:
#         verbose_name = "Country"
#         verbose_name_plural = "Countries"
#         ordering = ['country_name']

# class ProgramTour(models.Model):
#     wholesaler = models.ForeignKey('Wholesaler', on_delete=models.CASCADE, related_name='program_tours')
    
#     # Core fields
#     product_id = models.CharField(max_length=50, unique=True)  # e.g., "1"
#     product_code = models.CharField(max_length=50)  # e.g., "ZGHKG-2413CX"
#     product_name = models.CharField(max_length=255)  # ชื่อโปรแกรมทัวร์
#     days = models.IntegerField()  # จำนวนวัน
#     nights = models.IntegerField()  # จำนวนคืน

#     # Country relationship
#     country = models.ForeignKey(
#         'Country',
#         on_delete=models.SET_NULL, # Or models.PROTECT if a tour must always have a country
#         null=True,
#         blank=True,
#         related_name='program_tours',
#         help_text="The primary country this tour is associated with."
#     )
    
#     # Airline fields
#     airline_code = models.CharField(max_length=10, help_text="Denormalized airline code from wholesaler")
#     airline_name = models.CharField(max_length=255, help_text="Denormalized airline name from wholesaler")

#     # Files and images
#     file_word = models.URLField(blank=True, null=True, help_text="URL to the .docx program file.")  # .docx
#     file_pdf = models.URLField(blank=True, null=True, help_text="URL to the .pdf program file.")   # .pdf
#     url_image = models.URLField(blank=True, null=True, help_text="URL for the main banner image.")  # banner.jpg

#     # Optional
#     highlight = models.TextField(blank=True, null=True, help_text="Tour highlights or key selling points.")

#     # Hotel stars
#     max_hotel_stars = models.IntegerField()
#     min_hotel_stars = models.IntegerField()

#     # Meals
#     plane_meals = models.CharField(max_length=1, choices=[('Y', 'Yes'), ('N', 'No')], blank=True, null=True, help_text="Are meals provided on the plane?")
#     total_meals = models.IntegerField(help_text="Total number of meals included in the tour package (excluding plane meals).")

#     # Locations relationship
#     visited_locations = models.ManyToManyField(
#         'Location',
#         related_name='program_tours',
#         blank=True,
#         help_text="Specific locations visited during this tour."
#     )

#     # Metadata
#     update_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.product_code} - {self.product_name}"

#     class Meta:
#         verbose_name_plural = "Program Tours"
#         ordering = ['product_name']

# class Period(models.Model):
#     # Note: For price fields (price, price_child, etc.), consider using models.DecimalField
#     # if you need to store monetary values with decimal precision (e.g., for cents).
#     # Example: price = models.DecimalField(max_digits=10, decimal_places=2)
#     period_id = models.AutoField(primary_key=True)
#     period_code = models.CharField(max_length=100)
#     bus = models.CharField(max_length=10)

#     period_start_date = models.DateField()
#     period_end_date = models.DateField()

#     country_code = models.CharField(max_length=10, help_text="Denormalized country code for this specific period/leg.")
#     country_name = models.CharField(max_length=100, help_text="Denormalized country name for this specific period/leg.")
#     airline_code = models.CharField(max_length=10, help_text="Denormalized airline code for this specific period/leg.")
#     airline_name = models.CharField(max_length=100, help_text="Denormalized airline name for this specific period/leg.")
#     airport = models.CharField(max_length=100, blank=True, null=True, help_text="Airport for this period, if applicable.")

#     groupsize = models.PositiveIntegerField()
#     book = models.PositiveIntegerField(null=True, blank=True)
#     seat = models.PositiveIntegerField()

#     period_status = models.CharField(
#         max_length=20, # Consider making this longer if status names can be longer
#         choices=[('Soldout', 'Soldout'), ('Book', 'Book'), ('Close Group', 'Close Group'), ('Waitlist', 'Waitlist')],
#         blank=True, null=True, help_text="Current booking status of the period."
#     )

#     # Pricing fields
#     price = models.IntegerField()
#     price_child = models.IntegerField()
#     price_child_nb = models.IntegerField()
#     price_infant = models.IntegerField()
#     price_joinland = models.IntegerField()
#     price_single_bed = models.IntegerField()
#     price_twin_bed = models.IntegerField()
#     price_double_bed = models.IntegerField()
#     price_triple_bed = models.IntegerField()
#     price_single_visa = models.IntegerField()
#     price_group_visa = models.IntegerField()
#     price_express_visa = models.IntegerField()

#     deposit = models.IntegerField()
#     com_agent = models.IntegerField()
#     com_sale = models.IntegerField()

#     # Adjusted (end) pricing fields
#     price_end = models.IntegerField()
#     price_child_end = models.IntegerField()
#     price_child_nb_end = models.IntegerField()
#     price_infant_end = models.IntegerField()
#     price_joinland_end = models.IntegerField()
#     price_single_bed_end = models.IntegerField()
#     price_twin_bed_end = models.IntegerField()
#     price_double_bed_end = models.IntegerField()
#     price_triple_bed_end = models.IntegerField()
#     price_single_visa_end = models.IntegerField()
#     price_group_visa_end = models.IntegerField()
#     price_express_visa_end = models.IntegerField()

#     deposit_end = models.IntegerField()
#     com_agent_end = models.IntegerField()
#     com_sale_end = models.IntegerField()

#     update_date = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the last update from the wholesaler for this period.")

#     # Foreign Key to ProgramTour or Product
#     product = models.ForeignKey("ProgramTour", on_delete=models.CASCADE, related_name="periods")

#     def __str__(self):
#         return f"{self.period_code} ({self.period_start_date})"

#     class Meta:
#         verbose_name_plural = "Periods"
#         unique_together = (('product', 'period_code'),) # Ensures a period code is unique per tour
#         ordering = ['product', 'period_start_date', 'period_code']



# class Flight(models.Model):
#     airline_code = models.CharField(max_length=10)
#     airline_name = models.CharField(max_length=100)
#     flight_no = models.CharField(max_length=20)
#     route = models.CharField(max_length=50)

#     departure_time = models.TimeField()
#     arrival_time = models.TimeField()

#     # ForeignKey to Period
#     period = models.ForeignKey("Period", on_delete=models.CASCADE, related_name="flights")

#     def __str__(self):
#         return f"{self.flight_no} ({self.route})"

#     class Meta:
#         ordering = ['period', 'departure_time']


# MEAL_CHOICES = [
#     ('Y', 'Yes (Included)'),
#     ('N', 'No (Not Included)'),
#     ('P', 'Provided (e.g., on plane)'), # Or use for 'Packed'
#     ('O', 'Optional / Own Expense'), # Or use 'C' for 'Customer expense'
#     # Add more choices as needed, e.g. ('S', 'Special Meal')
# ]

# class Itinerary(models.Model):
#     itin_day = models.PositiveIntegerField()
#     itin_description = models.TextField(blank=True, null=True)
#     itin_hotel = models.CharField(max_length=255, blank=True, null=True)
#     itin_hotel_star = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., '3', '4.5', 'Luxury', 'Boutique'")

#     # Meal fields (Y, N, P, C or blank)
#     itin_bfast = models.CharField(max_length=1, choices=MEAL_CHOICES, blank=True, null=True)
#     itin_bfast_description = models.TextField(blank=True, null=True)

#     itin_lunch = models.CharField(max_length=1, choices=MEAL_CHOICES, blank=True, null=True)
#     itin_lunch_description = models.TextField(blank=True, null=True)

#     itin_dinner = models.CharField(max_length=1, choices=MEAL_CHOICES, blank=True, null=True)
#     itin_dinner_description = models.TextField(blank=True, null=True)

#     # Changed ForeignKey to ProgramTour as it's more specific and relevant
#     program_tour = models.ForeignKey("ProgramTour", on_delete=models.CASCADE, related_name="itineraries")

#     def __str__(self):
#         return f"Day {self.itin_day} for {self.program_tour.product_code} - {self.itin_hotel or 'Activity Day'}"

#     class Meta:
#         verbose_name = "Itinerary"
#         verbose_name_plural = "Itineraries"
#         ordering = ['program_tour', 'itin_day']


# class ImageGallery(models.Model):
#     program_tour = models.ForeignKey(ProgramTour, on_delete=models.CASCADE, related_name='images')
#     image_url = models.URLField()
#     caption = models.CharField(max_length=255, blank=True)

#     def __str__(self):
#         return self.image_url

#     class Meta:
#         verbose_name = "Image Gallery"
#         verbose_name_plural = "Image Galleries"

# class Location(models.Model):
#     """
#     Represents a travel location/destination within a country.
#     Based on actual API data structure from wholesalers.
#     """
#     # Primary identification
#     location_id = models.AutoField(primary_key=True)
    
#     # Basic information (matching API data)
#     location_name = models.CharField(
#         max_length=255, 
#         help_text="Location name as provided by API, e.g., 'โตเกียว', 'ฮ่องกง ดิสนีย์แลนด์'"
#     )
    
#     # Relationship to country
#     country = models.ForeignKey(
#         'Country', 
#         on_delete=models.CASCADE, 
#         related_name='locations',
#         help_text="Country this location belongs to"
#     )
    
#     # Denormalized fields for quick access (following your existing pattern)
#     country_code = models.CharField(
#         max_length=10, 
#         help_text="Country code, e.g., 'JPN', 'HKG'"
#     )
    
#     # Wholesaler relationship (following your existing pattern)
#     wholesaler = models.ForeignKey(
#         'Wholesaler', 
#         on_delete=models.CASCADE, 
#         related_name='locations',
#         help_text="Wholesaler that provides this location"
#     )
    
#     # Status
#     is_active = models.BooleanField(
#         default=True,
#         help_text="Whether this location is currently available"
#     )
    
#     # Timestamps
#     created_date = models.DateTimeField(auto_now_add=True)
#     update_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.location_name} ({self.country_code})"

#     class Meta:
#         verbose_name = "Location"
#         verbose_name_plural = "Locations"
#         ordering = ['country_code', 'location_name']
#         unique_together = [
#             ('wholesaler', 'country_code', 'location_name'),  # Unique per wholesaler-country combination
#         ]
#         indexes = [
#             models.Index(fields=['country_code']),
#             models.Index(fields=['wholesaler', 'country_code']),
#         ]

"""------------------------- new models -------------------------"""
from django.db import models


class Provider(models.Model):
    """
    Travel providers (Zego, Expedia, Amadeus, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)  # e.g., 'zego', 'expedia'
    base_url = models.URLField(blank=True, null=True)
    token = models.CharField(max_length=512, blank=True, null=True, help_text="API token for the provider, if required. Store securely.")
    api_version = models.CharField(max_length=20, blank=True, null=True)
    extra = models.JSONField(blank=True, null=True)  # store provider-specific config

    def __str__(self):
        return self.name


class Country(models.Model):
    """
    Country information from each provider.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="countries")
    provider_code = models.CharField(max_length=50)  # provider's CountryCode
    name = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    locations = models.JSONField(blank=True, null=True)

    # Normalized fields for deduplication
    normalized_name = models.CharField(max_length=255, db_index=True, blank=True, help_text="Normalized country name for deduplication (lowercase, trimmed)")
    iso_code = models.CharField(max_length=3, blank=True, help_text="ISO 3166-1 alpha-3 country code (e.g., JOR, ESP, RUS)")

    class Meta:
        unique_together = ("provider", "provider_code")
        indexes = [
            models.Index(fields=['normalized_name']),
            models.Index(fields=['iso_code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider.code})"


class ProgramTour(models.Model):
    """
    High-level tour product, unique per provider.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="program_tours")
    external_id = models.CharField(max_length=100)  # e.g., Zego's ProductID
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    # Durations
    days = models.PositiveIntegerField(blank=True, null=True)
    nights = models.PositiveIntegerField(blank=True, null=True)

    # Country
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    country_name = models.CharField(max_length=255, blank=True)  # snapshot

    # Airline info (provider specific)
    airline_code = models.CharField(max_length=50, blank=True, null=True)
    airline_name = models.CharField(max_length=255, blank=True, null=True)

    # Media
    file_pdf = models.URLField(blank=True, null=True)
    file_word = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    # Other attributes
    highlight = models.TextField(blank=True, null=True)
    max_hotel_stars = models.IntegerField(blank=True, null=True)
    min_hotel_stars = models.IntegerField(blank=True, null=True)
    plane_meals = models.BooleanField(default=False)
    total_meals = models.PositiveIntegerField(blank=True, null=True)
    locations = models.JSONField(blank=True, null=True)

    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("provider", "external_id")

    def __str__(self):
        return f"{self.code} - {self.name} ({self.provider.code})"


class Period(models.Model):
    """
    Departure periods per provider/program tour.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="periods")
    external_id = models.CharField(max_length=100)  # e.g., Zego's PeriodID
    program = models.ForeignKey(ProgramTour, related_name="periods", on_delete=models.CASCADE)
    code = models.CharField(max_length=100)

    # Dates
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Transport
    bus = models.CharField(max_length=20, blank=True, null=True)
    country_name = models.CharField(max_length=255, blank=True, null=True)
    airline_code = models.CharField(max_length=50, blank=True, null=True)
    airline_name = models.CharField(max_length=255, blank=True, null=True)
    airport = models.CharField(max_length=255, blank=True, null=True)

    # Booking
    group_size = models.IntegerField(blank=True, null=True)
    booked = models.IntegerField(blank=True, null=True)
    seats = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    promotion = models.CharField(max_length=10, blank=True, null=True)

    # Prices
    base_prices = models.JSONField(blank=True, null=True)  # {"adult": 1000, "child": 800, ...}
    end_prices = models.JSONField(blank=True, null=True)

    # Commissions & deposit
    deposit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    deposit_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_agent = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_agent_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_sale = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    com_sale_end = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("provider", "external_id")

    def __str__(self):
        return f"{self.code} ({self.provider.code})"


class Flight(models.Model):
    """
    Flight information per provider.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="flights")
    program = models.ForeignKey(ProgramTour, related_name="flights", on_delete=models.CASCADE, blank=True, null=True)
    period = models.ForeignKey(Period, related_name="flights", on_delete=models.CASCADE, blank=True, null=True)

    airline_code = models.CharField(max_length=50)
    airline_name = models.CharField(max_length=255)
    flight_no = models.CharField(max_length=50)
    route = models.CharField(max_length=255)
    departure_time = models.TimeField(blank=True, null=True)
    arrival_time = models.TimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.flight_no} ({self.provider.code})"


class Itinerary(models.Model):
    """
    Itinerary per provider/program tour.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="itineraries")
    external_id = models.CharField(max_length=100)  # e.g., Zego's ItinID
    program = models.ForeignKey(ProgramTour, related_name="itineraries", on_delete=models.CASCADE)

    day = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    hotel = models.CharField(max_length=255, blank=True, null=True)
    hotel_star = models.CharField(max_length=10, blank=True, null=True)

    # Meals
    breakfast = models.BooleanField(default=False)
    breakfast_desc = models.TextField(blank=True, null=True)
    lunch = models.BooleanField(default=False)
    lunch_desc = models.TextField(blank=True, null=True)
    dinner = models.BooleanField(default=False)
    dinner_desc = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("provider", "external_id")

    def __str__(self):
        return f"{self.program.code} - Day {self.day} ({self.provider.code})"


class ProviderMeta(models.Model):
    """
    Metadata for API sync (provider specific).
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="metadata")
    last_period_update = models.DateTimeField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider.name} meta ({self.fetched_at})"
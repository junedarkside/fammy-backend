from django.db import models
from django.db.models.signals import pre_save, post_save
from django.contrib.auth import get_user_model
from .utils import unique_slug, random_string_generator
from django.core.exceptions import ValidationError
from django.utils import timezone

class Category(models.TextChoices):
    DOMESTIC = "DOMESTIC", "Domestic Travel"
    INTERNATIONAL = "INTERNATIONAL", "International Travel"
    ADVENTURE = "ADVENTURE", "Adventure & Outdoor"
    CRUISE = "CRUISE", "Cruise & Yacht"
    BUSINESS = "BUSINESS", "Business & MICE"
    WELLNESS = "WELLNESS", "Wellness & Medical"
    CULTURAL = "CULTURAL", "Cultural & Heritage"
    LUXURY = "LUXURY", "Luxury Travel"
    FAMILY = "FAMILY", "Family & Theme Parks"

class Type(models.TextChoices):
    FLIGHT_ONLY = "FLIGHT_ONLY", "Flight Only"
    HOTEL_ONLY = "HOTEL_ONLY", "Hotel Only"
    PACKAGE_TOUR = "PACKAGE_TOUR", "Package Tour"
    PRIVATE_TOUR = "PRIVATE_TOUR", "Private Tour"
    GROUP_TOUR = "GROUP_TOUR", "Group Tour"
    BACKPACKING = "BACKPACKING", "Backpacking"
    CRUISE_TOUR = "CRUISE_TOUR", "Cruise Tour"
    SELF_DRIVE = "SELF_DRIVE", "Self-Drive"
    HONEYMOON = "HONEYMOON", "Honeymoon Package"
    PILGRIMAGE = "PILGRIMAGE", "Religious & Pilgrimage"
    FESTIVAL = "FESTIVAL", "Festival & Events"
    SPORTS_TOUR = "SPORTS_TOUR", "Sports & Adventure"

class Promotion(models.TextChoices):
    FLASH_SALE = "FLASH_SALE", "Flash Sale"
    EARLY_BIRD = "EARLY_BIRD", "Early Bird Discount"
    LAST_MINUTE = "LAST_MINUTE", "Last Minute Deal"
    GROUP_DISCOUNT = "GROUP_DISCOUNT", "Group Discount"
    INSTALLMENT_0_PERCENT = "INSTALLMENT_0_PERCENT", "0% Installment Plan"
    CREDIT_CARD_FEE_WAIVER = "CREDIT_CARD_FEE_WAIVER", "0% Credit Card Fee"
    FREE_EXTRA_NIGHT = "FREE_EXTRA_NIGHT", "Free Extra Night"
    BUY_ONE_GET_ONE = "BUY_ONE_GET_ONE", "Buy One Get One"
    NONE = "NONE", "No Promotion"

class Operator(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Airline(models.Model):
    name = models.CharField(max_length=100)
    logo = models.URLField()

    def __str__(self):
        return self.name
    


class Tour(models.Model):
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(unique=True,blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    highlight = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField()
    duration = models.CharField(max_length=50)
    hotel_stars = models.CharField(max_length=10)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE)
    countries = models.ManyToManyField(Country)
    locations = models.ManyToManyField("Location")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.DOMESTIC
    )
    tour_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PACKAGE_TOUR
    )
    def __str__(self):
        return self.name

def pre_save_slug_field(sender, instance, *args, **kwargs):
    if not instance.slug or instance.slug.strip() == "":
        instance.slug = unique_slug(instance)

pre_save.connect(pre_save_slug_field, sender=Tour)

class Location(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="locations", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class TravelDate(models.Model):
    tour = models.ForeignKey(Tour, related_name="travel_dates", on_delete=models.CASCADE)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.IntegerField()
    
    def get_discounted_price(self):
        active_flash_sale = self.flash_sales.filter(
            is_active=True,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        
        if active_flash_sale:
            return max(self.rate - active_flash_sale.discount_amount, 0)  # Ensure price doesn't go negative
        
        return self.rate

    def __str__(self):
        return f"{self.tour.slug} | {self.date_start} to {self.date_end} - {self.rate} THB"
    

class FlashSale(models.Model):
    travel_dates = models.ManyToManyField(TravelDate, related_name="flash_sales")  
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discount applied to each TravelDate rate")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def clean(self):
        # Validate end_time is after start_time
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")
        
        
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_valid_now(self):
        now = timezone.now()
        return (
            self.is_active and 
            self.start_time <= now <= self.end_time
        )

    def __str__(self):
        return f"Flash Sale: Discount {self.discount_amount} THB (Active: {self.is_active})"
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['is_active']),
        ]

# Travel Industry Django Model

## Overview
This Django model covers various aspects of the travel industry, including categories, types, and promotions. It is designed to be scalable and adaptable to different travel services.

## Features
- **Categories**: Covers different travel sectors like adventure, wellness, business, and more.
- **Types**: Supports various travel packages, tours, flights, and accommodations.
- **Promotions**: Includes discount types such as flash sales, early bird deals, and 0% installment plans.

## Installation & Usage
### 1. Add the Model to Your Django App
```python
from django.db import models

class Tour(models.Model):
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

    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=15,
        choices=Category.choices,
        default=Category.DOMESTIC
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PACKAGE_TOUR
    )
    promotion = models.CharField(
        max_length=30,
        choices=Promotion.choices,
        default=Promotion.NONE
    )
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name
```

### 2. Apply Migrations
```sh
python manage.py makemigrations
python manage.py migrate
```

### 3. Register in Django Admin (Optional)
```python
from django.contrib import admin
from .models import Tour

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'type', 'promotion')
    prepopulated_fields = {"slug": ("name",)}
```

### 4. Usage Example
```python
Tour.objects.create(
    name="Thailand Adventure",
    category=Tour.Category.ADVENTURE,
    type=Tour.Type.BACKPACKING,
    promotion=Tour.Promotion.FLASH_SALE
)
```

## Data Examples
| Name               | Category   | Type          | Promotion       |
|--------------------|-----------|--------------|----------------|
| Thailand Getaway  | DOMESTIC   | PACKAGE_TOUR | FLASH_SALE     |
| Japan Cruise      | INTERNATIONAL | CRUISE_TOUR | NONE           |
| Business Retreat  | BUSINESS   | HOTEL_ONLY   | EARLY_BIRD     |
| Safari Adventure | ADVENTURE  | BACKPACKING  | LAST_MINUTE    |

## License
This project is licensed under the MIT License.



update all product progran tours: http://localhost:8000/wholesale/wholesalers/zego/sync-program-tours/
update single programtour: http://localhost:8000/wholesale/wholesalers/zego/sync-single-program-tour/ZGARN-2504TK/


eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2ODJjMDIyNDllNjkwNTA4N2JjMDliZWYiLCJpYXQiOjE3NTkxMDc1MDR9.2N2-1IAncKyPqABKEaqXh7rftB0wcoq6BnCgKAhoJB8


echo "# fammy-backend" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:junedarkside/fammy-backend.git
git push -u origin main
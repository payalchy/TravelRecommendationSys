import math
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.db.models import Max, Avg, Count
from django.conf import settings
import googlemaps

class Destination(models.Model):
    pName = models.CharField(max_length=255, null=True, blank=True, verbose_name="Place Name")
    province = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    culture = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    adventure = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    wildlife = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    sightseeing = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    history = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    tags = models.TextField(null=True, blank=True)

    image = models.URLField(blank=True, null=True)
    
    # NEW: Constraint fields for recommendations
    avg_package_price = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Average package price in NPR for this destination"
    )
    recommended_visit_days = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Recommended number of days to spend at this destination"
    )
    best_season = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="Best season(s) to visit (e.g., 'spring,autumn' or 'winter')"
    )



    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('pName'),
                Lower('province'),
                name='unique_destination_case_insensitive'
            )
        ]
    
    def _fetch_coordinates_from_nominatim(self):
        """Fetch the most relevant coordinates for a destination using a Nepal-focused geocoding query."""
        if not self.pName:
            return None

        parts = [str(self.pName).strip()]
        province = str(self.province).strip() if self.province is not None else ''
        if province and not province.isdigit():
            parts.append(province)
        if self.city:
            parts.append(str(self.city).strip())
        parts.append("Nepal")

        query = ", ".join(part for part in parts if part)

        try:
            params = urlencode({
                "q": query,
                "format": "json",
                "limit": 5,
                "addressdetails": 1,
            })
            url = f"https://nominatim.openstreetmap.org/search?{params}"
            request_obj = Request(url, headers={"User-Agent": "Django-TravelRecommendation/1.0"})

            with urlopen(request_obj, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if payload:
                preferred = None
                for item in payload:
                    display_name = str(item.get("display_name", "")).lower()
                    if "nepal" not in display_name:
                        continue

                    importance = float(item.get("importance", 0) or 0)
                    class_type = str(item.get("class", "")).lower()
                    type_name = str(item.get("type", "")).lower()

                    is_place_like = class_type in {"place", "boundary", "administrative"} or type_name in {"city", "town", "village", "administrative", "administrative_area_level_1"}
                    if not is_place_like:
                        continue

                    if preferred is None or importance > float(preferred.get("importance", 0) or 0):
                        preferred = item

                if preferred is None:
                    preferred = payload[0]

                return float(preferred.get("lat")), float(preferred.get("lon"))
        except Exception as e:
            print(f"[Nominatim Error] Failed for {self.pName}: {str(e)}")

        return None
    
    def save(self, *args, **kwargs):
        """Auto-fill coordinates if not provided"""
        # Only fetch if coordinates are missing
        if (self.latitude is None or self.longitude is None) and self.pName:
            coords = self._fetch_coordinates_from_nominatim()
            if coords:
                self.latitude, self.longitude = coords
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pName} ({self.province})"


class StartLocation(models.Model):
    pName = models.CharField(max_length=255, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    def __str__(self):
        return f"{self.pName} ({self.province})"

def validate_image(image):
    if image.size > 2 * 1024 * 1024:  
        raise ValidationError("Image size should not exceed 2MB")
class TravelPackage(models.Model):
    TRANSPORT_CHOICES = [
        ('car', 'Car'),
        ('jeep', 'Jeep'),
        ('bus', 'Bus'),
        ('flight', 'Flight'),
        ('bike', 'Bike'),
    ]

    PACKAGE_TYPE_CHOICES = [
        ('tour', 'Tour'),
        ('hiking', 'Hiking'),
        ('sightseeing', 'Sightseeing'),
        ('adventure', 'Adventure'),
    ]
    name = models.CharField(max_length=200,default="")

    transport_mode = models.CharField(
        max_length=20,
        choices=TRANSPORT_CHOICES,
        default='bus'
    )

    package_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        default='tour'
    )

    
    start_location = models.ForeignKey('StartLocation', on_delete=models.SET_NULL, null=True, related_name='start_packages')
    end_location = models.ForeignKey('Destination',on_delete=models.SET_NULL,null=True,related_name='end_packages')
    budget = models.FloatField(validators=[MinValueValidator(0)])
    distance_km = models.FloatField(validators=[MinValueValidator(0)], default=0)
    number_of_travelers = models.IntegerField(validators=[MinValueValidator(1)],default=1)
    average_rating = models.FloatField(default=0.0)
    rating_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='packages/', validators=[validate_image],null=True, blank=True)
    description = models.TextField(default="")
    days = models.IntegerField(validators=[MinValueValidator(1)],default=1)
    includes = models.TextField(default="", blank=True, help_text="Enter items included in the package, one per line")
    excludes = models.TextField(default="", blank=True, help_text="Enter items excluded from the package, one per line")

    @staticmethod
    def _haversine_distance_km(lat1, lon1, lat2, lon2):
        try:
            lat1 = math.radians(float(lat1))
            lon1 = math.radians(float(lon1))
            lat2 = math.radians(float(lat2))
            lon2 = math.radians(float(lon2))
        except (TypeError, ValueError):
            return 0.0

        if lat1 == lat2 and lon1 == lon2:
            return 0.0

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c

    def calculate_distance_km(self):
        start_location = self.start_location
        itinerary = list(
            self.itinerary.select_related("destination").order_by("day_number", "id")
        )
        total_distance = 0.0

        start_lat = getattr(start_location, "latitude", None)
        start_lon = getattr(start_location, "longitude", None)
        previous_coords = None

        for stop in itinerary:
            destination = stop.destination
            if destination is None:
                continue

            dest_lat = getattr(destination, "latitude", None)
            dest_lon = getattr(destination, "longitude", None)
            if dest_lat is None or dest_lon is None:
                continue

            if previous_coords is None and start_lat is not None and start_lon is not None:
                total_distance += self._haversine_distance_km(
                    start_lat,
                    start_lon,
                    dest_lat,
                    dest_lon,
                )

            if previous_coords is not None:
                total_distance += self._haversine_distance_km(
                    previous_coords[0],
                    previous_coords[1],
                    dest_lat,
                    dest_lon,
                )

            previous_coords = (dest_lat, dest_lon)

        if total_distance == 0 and start_lat is not None and start_lon is not None and self.end_location:
            end_lat = getattr(self.end_location, "latitude", None)
            end_lon = getattr(self.end_location, "longitude", None)
            if end_lat is not None and end_lon is not None:
                total_distance = self._haversine_distance_km(
                    start_lat,
                    start_lon,
                    end_lat,
                    end_lon,
                )

        return round(total_distance, 2)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            self.distance_km = self.calculate_distance_km()
        else:
            self.distance_km = 0.0
        super().save(*args, **kwargs)

    def update_rating_stats(self):
        stats = self.ratings.aggregate(
            average=models.Avg("score"),
            count=models.Count("id"),
        )
        self.average_rating = stats["average"] or 0.0
        self.rating_count = stats["count"] or 0
        self.save(update_fields=["average_rating", "rating_count"])

    def __str__(self):
        return self.name

class PackageRating(models.Model):
    package = models.ForeignKey(
        TravelPackage,
        related_name="ratings",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="package_ratings",
        on_delete=models.CASCADE,
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("package", "user")
        indexes = [models.Index(fields=["package", "user"])]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.package.update_rating_stats()

    def delete(self, *args, **kwargs):
        package = self.package
        super().delete(*args, **kwargs)
        package.update_rating_stats()

    def __str__(self):
        return f"{self.user.username} rating for {self.package.name}: {self.score}"

class PackageItinerary(models.Model):
    package = models.ForeignKey(TravelPackage,on_delete=models.CASCADE,related_name='itinerary')
    day_number = models.IntegerField()
    destination = models.ForeignKey('Destination', on_delete=models.CASCADE)
    description = models.TextField(default="")

    def save(self, *args, **kwargs):
        # Auto-fill day_number if not provided
        if not self.day_number:
            max_day = self.package.itinerary.aggregate(Max('day_number'))['day_number__max'] or 0
            self.day_number = max_day + 1
        super().save(*args, **kwargs)

    def clean(self):
        if self.day_number > self.package.days:
            raise ValidationError(
                f"Day number ({self.day_number}) cannot exceed package duration ({self.package.days} days)"
            )
        if self.day_number < 1:
            raise ValidationError("Day number must be at least 1")

    class Meta:
        unique_together = ('package', 'day_number','destination')
        ordering = ['day_number']

    def __str__(self):
        return f"{self.package.name} - Day {self.day_number}"


class Booking(models.Model):

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_NOT_AVAILABLE = "not_available"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_NOT_AVAILABLE, "Not Available"),
    ]


    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_REFUNDED = "refunded"


    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
        (PAYMENT_REFUNDED, "Refunded"),
    ]


    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )

    package = models.ForeignKey(
        TravelPackage,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    full_name = models.CharField(max_length=255)

    contact_no = models.CharField(max_length=50)

    email = models.EmailField()


    payment_method = models.CharField(
        max_length=50,
        default="Cash"
    )


    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING
    )


    # Stripe fields
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    paid_amount = models.PositiveIntegerField(
        default=0
    )


    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )


    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )


    notice = models.TextField(
        default="You will receive a call for booking confirmation."
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.full_name} - {self.package.name}"

class Recommendation(models.Model):
    """
    Stores travel recommendations for users based on their preferences and destinations
    """
    from django.contrib.auth.models import User
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Recommendation score (0-5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
        unique_together = ('user', 'destination')
    
    def __str__(self):
        return f"{self.user.username} -> {self.destination.pName} ({self.score})"


class CostComparison(models.Model):
    """
    Evaluates and stores cost comparison and distance metrics for recommendations
    Related to Recommendation through a OneToOne or ForeignKey relationship
    """
    recommendation = models.OneToOneField(
        Recommendation, 
        on_delete=models.CASCADE, 
        related_name='cost_comparison'
    )
    distance = models.FloatField(
        validators=[MinValueValidator(0)],  
        help_text="Distance in kilometers"
    )
    estimate_cost = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Estimated cost for the recommendation in NPR"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cost Comparison - {self.recommendation.user.username} -> {self.recommendation.destination.pName}"



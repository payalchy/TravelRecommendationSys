from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower
from django.db.models import Max
from django.conf import settings
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import googlemaps

class Destination(models.Model):
    pName = models.CharField(max_length=255, null=True, blank=True)
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
        """Fetch coordinates from Google Maps API (primary) or OpenStreetMap Nominatim API (fallback)"""
        if not self.pName:
            return None
        
        # Try Google Maps API first
        google_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if google_api_key:
            try:
                gmaps = googlemaps.Client(key=google_api_key)
                
                # Build query - include province if available
                query = self.pName
                province = str(self.province).strip() if self.province is not None else ''
                if province and not province.isdigit():
                    query = f"{self.pName}, {province}"
                query = f"{query}, Nepal"
                
                geocode_result = gmaps.geocode(query)
                
                if geocode_result and len(geocode_result) > 0:
                    location = geocode_result[0]['geometry']['location']
                    return float(location['lat']), float(location['lng'])
            except Exception as e:
                print(f"[Google Maps Error] Failed for {self.pName}: {str(e)}")
        
        # Fallback to Nominatim if Google Maps fails or no API key
        try:
            # Build query - skip province if it's just a number
            query = self.pName
            province = str(self.province).strip() if self.province is not None else ''
            if province and not province.isdigit():
                query = f"{self.pName}, {province}"
            query = f"{query}, Nepal"
            
            params = urlencode({"q": query, "format": "json", "limit": 1})
            url = f"https://nominatim.openstreetmap.org/search?{params}"
            request_obj = Request(url, headers={"User-Agent": "Django-TravelRecommendation/1.0"})
            
            with urlopen(request_obj, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            
            if payload and len(payload) > 0:
                first = payload[0]
                return float(first.get("lat")), float(first.get("lon"))
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
    image = models.ImageField(upload_to='packages/', validators=[validate_image],null=True, blank=True)
    description = models.TextField(default="")
    days = models.IntegerField(validators=[MinValueValidator(1)],default=1)
    includes = models.TextField(default="", blank=True, help_text="Enter items included in the package, one per line")
    excludes = models.TextField(default="", blank=True, help_text="Enter items excluded from the package, one per line")

    def __str__(self):
        return self.name

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



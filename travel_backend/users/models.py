from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class TravelStyle(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class UserProfile(models.Model):

    SEASON_CHOICES = [
        ("summer", "Summer"),
        ("rainy", "Rainy"),
        ("spring", "Spring"),
        ("autumn", "Autumn"),
        ("winter", "Winter"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #  MUST BE POSITIVE (>0)
    budget = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.01)]
    )

    #  MULTI-SELECT
    preferred_travel_style = models.ManyToManyField(TravelStyle)

    #  ONLY POSITIVE VALUES
    preferred_duration = models.PositiveIntegerField(default=1)

    #  DROPDOWN (NO RANDOM INPUT)
    preferred_season = models.CharField(
        max_length=20,
        choices=SEASON_CHOICES,
        default="summer",
    )

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    

    def __str__(self):
        return self.user.username
    
# Profile History

class UserProfileHistory(models.Model):
    """
    Stores snapshot whenever user updates profile
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    budget = models.FloatField()
    preferred_duration = models.PositiveIntegerField()
    preferred_season = models.CharField(max_length=20)

    travel_styles = models.TextField()  # store names as string

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


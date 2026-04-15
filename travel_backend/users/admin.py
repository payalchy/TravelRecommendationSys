from django.contrib import admin
from .models import UserProfile, TravelStyle

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    exclude = (
        "culture_weight",
        "adventure_weight",
        "wildlife_weight",
        "sightseeing_weight",
        "history_weight",
    )

    filter_horizontal = ('preferred_travel_style',)

admin.site.register(TravelStyle)
from django.contrib import admin
from django.contrib import messages
from django.apps import apps
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from django.utils.text import Truncator
from django.core.exceptions import ValidationError
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Destination, TravelPackage, PackageItinerary

admin.site.site_header = "Travel Management Admin"
admin.site.site_title = "Travel Admin"
admin.site.index_title = "Dashboard"

_default_each_context = admin.site.each_context


def _dashboard_each_context(request):
    context = _default_each_context(request)
    user_model = get_user_model()
    booking_model = next(
        (model for model in apps.get_models() if model.__name__.lower() == "booking"),
        None,
    )

    module_cards = [
        {
            "title": "Destinations",
            "count": Destination.objects.count(),
            "url": reverse("admin:recommendation_destination_changelist"),
            "add_url": reverse("admin:recommendation_destination_add"),
        },
        {
            "title": "Packages",
            "count": TravelPackage.objects.count(),
            "url": reverse("admin:recommendation_travelpackage_changelist"),
            "add_url": reverse("admin:recommendation_travelpackage_add"),
        },
        {
            "title": "Users",
            "count": user_model.objects.count(),
            "url": reverse("admin:auth_user_changelist"),
            "add_url": reverse("admin:auth_user_add"),
        },
    ]

    recent_activities = []
    for destination in Destination.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "Destination added",
                "detail": f"{destination.pName} ({destination.province or 'N/A'})",
                "url": reverse("admin:recommendation_destination_change", args=[destination.id]),
            }
        )

    for package in TravelPackage.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "Package added",
                "detail": package.name,
                "url": reverse("admin:recommendation_travelpackage_change", args=[package.id]),
            }
        )

    for account in user_model.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "User signup",
                "detail": account.get_username(),
                "url": reverse("admin:auth_user_change", args=[account.id]),
            }
        )

    context.update(
        {
            "total_destinations": Destination.objects.count(),
            "total_packages": TravelPackage.objects.count(),
            "total_users": user_model.objects.count(),
            "total_bookings": booking_model.objects.count() if booking_model else 0,
            "module_cards": module_cards,
            "recent_activities": recent_activities[:12],
        }
    )
    return context


admin.site.each_context = _dashboard_each_context


class DestinationMapPickerWidget(forms.Widget):
    class Media:
        css = {
            "all": (
                "admin/css/package_location_map.css",
            )
        }
        js = ()  # Removed external js - using inline script instead

    def __init__(self, destinations=None, create_pin_url=None, attrs=None):
        self.destinations = destinations or []
        self.create_pin_url = create_pin_url
        super().__init__(attrs)

    def format_value(self, value):
        if value in (None, ""):
            return ""
        return str(value)

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        final_attrs = self.build_attrs(self.attrs, attrs)
        input_id = final_attrs.get("id", f"id_{name}")
        selected_value = self.format_value(value)

        destinations_payload = [
            {
                "id": destination.id,
                "name": destination.pName,
                "province": destination.province or "",
                "latitude": destination.latitude,
                "longitude": destination.longitude,
            }
            for destination in self.destinations
            if destination.latitude is not None and destination.longitude is not None
        ]
        selected_destination = next(
            (destination for destination in self.destinations if str(destination.id) == selected_value),
            None,
        )
        selected_label = "No start location selected"
        if selected_destination is not None:
            selected_label = f"{selected_destination.pName} ({selected_destination.province or 'N/A'})"

        hidden_input = forms.HiddenInput().render(name, selected_value, {"id": input_id})
        return format_html(
            '{}<div class="tm-map-picker" data-map-picker data-input-id="{}" data-selected-id="{}" data-selected-label="{}" data-destinations="{}" data-google-api-key="{}" data-create-pin-url="{}">'
            '<div class="tm-map-picker__search-section">'
            '<input type="text" class="tm-map-picker__search-input" placeholder="Search location (e.g., Kathmandu, Pokhara)..." data-search-input />'
            '<div class="tm-map-picker__search-results" data-search-results></div>'
            '</div>'
            '<div class="tm-map-picker__hint">Search for a location or click on the map to view it. The selected coordinates will be displayed below.</div>'
            '<div class="tm-map-picker__map" id="{}_map"></div>'
            '<div class="tm-map-picker__footer">'
            '<div class="tm-map-picker__summary">'
            '<span class="tm-map-picker__label">Selected start location</span>'
            '<strong data-selected-name>{}</strong>'
            '</div>'
            '<button type="button" class="button" data-clear-selection>Clear selection</button>'
            '</div>'
            '</div>',
            hidden_input,
            input_id,
            selected_value,
            selected_label,
            json.dumps(destinations_payload),
            settings.GOOGLE_MAPS_API_KEY or "",
            self.create_pin_url or "",
            input_id,
            selected_label,
        )

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "destination_summary",
        "province_badge",
        "city_badge",
        "culture_score",
        "adventure_score",
        "wildlife_score",
        "sightseeing_score",
        "history_score",
        "ratings_summary",
        "tags_summary",
        "quick_edit",
    )
    list_display_links = ("id", "destination_summary")
    search_fields = ("pName", "province", "city", "tags")
    list_filter = ("province",)
    ordering = ("pName",)
    list_per_page = 50
    readonly_fields = ("coordinate_tools",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("pName", "province", "city")
        }),
        ("Coordinates", {
            "fields": ("latitude", "longitude", "coordinate_tools"),
            "description": "Coordinates are automatically fetched from OpenStreetMap when you save. Click the button below to manually refetch."
        }),
        ("Travel Attributes", {
            "fields": ("culture", "adventure", "wildlife", "sightseeing", "history")
        }),
        ("Additional Info", {
            "fields": ("tags", "image")
        }),
    )

    def _fetch_coordinates(self, destination):
        if not destination.pName:
            return None

        # Skip province if it's just a number (likely an ID, not a real name)
        query = destination.pName
        if destination.province and not str(destination.province).isdigit():
            query = f"{destination.pName}, {destination.province}"
        query = f"{query}, Nepal"

        params = urlencode({"q": query, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        request_obj = Request(url, headers={"User-Agent": "travel-backend-admin/1.0"})

        try:
            with urlopen(request_obj, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        if not payload:
            return None

        first = payload[0]
        try:
            return float(first.get("lat")), float(first.get("lon"))
        except (TypeError, ValueError):
            return None

    def _find_saved_coordinates(self, destination):
        if not destination.pName:
            return None

        queryset = Destination.objects.exclude(pk=destination.pk).filter(
            pName__iexact=destination.pName,
            latitude__isnull=False,
            longitude__isnull=False,
        )

        if destination.province:
            same_province = queryset.filter(province__iexact=destination.province).first()
            if same_province:
                return same_province.latitude, same_province.longitude

        match = queryset.first()
        if match:
            return match.latitude, match.longitude
        return None

    def _resolve_coordinates(self, destination):
        saved_coords = self._find_saved_coordinates(destination)
        if saved_coords:
            return saved_coords, "saved"

        fetched_coords = self._fetch_coordinates(destination)
        if fetched_coords:
            return fetched_coords, "geocoded"

        return None, None

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:destination_id>/autofill-coordinates/",
                self.admin_site.admin_view(self.autofill_coordinates_view),
                name="recommendation_destination_autofill_coordinates",
            ),
        ]
        return custom_urls + urls

    def autofill_coordinates_view(self, request, destination_id):
        destination = self.get_object(request, str(destination_id))
        if destination is None:
            self.message_user(request, "Destination not found.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_changelist"))

        if not destination.pName:
            self.message_user(request, "Destination name is required for geocoding.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        if destination.latitude is not None and destination.longitude is not None:
            self.message_user(request, "Coordinates are already saved for this destination.", level=messages.INFO)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        resolved_coordinates, source = self._resolve_coordinates(destination)
        if not resolved_coordinates:
            self.message_user(request, "Could not fetch coordinates right now.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        latitude, longitude = resolved_coordinates
        destination.latitude = latitude
        destination.longitude = longitude
        destination.save(update_fields=["latitude", "longitude"])

        if source == "saved":
            self.message_user(request, "Saved coordinates reused successfully.", level=messages.SUCCESS)
        else:
            self.message_user(request, "Coordinates updated successfully.", level=messages.SUCCESS)
        return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

    def save_model(self, request, obj, form, change):
        latitude_missing = obj.latitude is None
        longitude_missing = obj.longitude is None

        if obj.pName and (latitude_missing or longitude_missing):
            resolved_coordinates, source = self._resolve_coordinates(obj)
            if resolved_coordinates:
                latitude, longitude = resolved_coordinates
                if latitude_missing:
                    obj.latitude = latitude
                if longitude_missing:
                    obj.longitude = longitude

                if source == "saved":
                    self.message_user(
                        request,
                        "Existing saved coordinates were reused automatically.",
                        level=messages.INFO,
                    )
                else:
                    self.message_user(
                        request,
                        "Coordinates were auto-filled and saved.",
                        level=messages.INFO,
                    )

        super().save_model(request, obj, form, change)

    @admin.display(description="Coordinate Tools")
    def coordinate_tools(self, obj):
        if obj is None or obj.id is None:
            return "Save destination first, then use auto-fill."
        url = reverse("admin:recommendation_destination_autofill_coordinates", args=[obj.id])
        return format_html('<a class="button" href="{}">Auto Fill Coordinates</a>', url)

    @admin.display(description="Destination", ordering="pName")
    def destination_summary(self, obj):
        return format_html(
            '<div class="tm-admin-title">{}</div>'
            '<div class="tm-admin-sub">ID #{}</div>',
            obj.pName,
            obj.id,
        )

    @admin.display(description="Province", ordering="province")
    def province_badge(self, obj):
        label = obj.province or "N/A"
        return format_html('<span class="tm-admin-badge">{}</span>', label)

    @admin.display(description="City", ordering="city")
    def city_badge(self, obj):
        label = obj.city or "N/A"
        return format_html('<span class="tm-admin-badge">{}</span>', label)

    @admin.display(description="Rating")
    def ratings_summary(self, obj):
        values = [obj.culture, obj.adventure, obj.wildlife, obj.sightseeing, obj.history]
        filtered = [float(value) for value in values if value is not None]
        average = round(sum(filtered) / len(filtered), 1) if filtered else 0
        return format_html('<span class="tm-admin-rating">{}/5</span>', average)

    @admin.display(description="Culture", ordering="culture")
    def culture_score(self, obj):
        return f"{obj.culture:.1f}" if obj.culture is not None else "-"

    @admin.display(description="Adventure", ordering="adventure")
    def adventure_score(self, obj):
        return f"{obj.adventure:.1f}" if obj.adventure is not None else "-"

    @admin.display(description="Wildlife", ordering="wildlife")
    def wildlife_score(self, obj):
        return f"{obj.wildlife:.1f}" if obj.wildlife is not None else "-"

    @admin.display(description="Sightseeing", ordering="sightseeing")
    def sightseeing_score(self, obj):
        return f"{obj.sightseeing:.1f}" if obj.sightseeing is not None else "-"

    @admin.display(description="History", ordering="history")
    def history_score(self, obj):
        return f"{obj.history:.1f}" if obj.history is not None else "-"

    @admin.display(description="Tags")
    def tags_summary(self, obj):
        if not obj.tags:
            return "-"
        return Truncator(obj.tags).chars(36)

    @admin.display(description="Actions")
    def quick_edit(self, obj):
        url = reverse("admin:recommendation_destination_change", args=[obj.id])
        return format_html('<a class="tm-admin-edit-btn" href="{}">Edit</a>', url)

class PackageItineraryInline(admin.TabularInline):
    model = PackageItinerary
    extra = 0
    autocomplete_fields = ["destination"]
    can_delete = True
    ordering = ("day_number",)
    fields = ('day_number', 'destination', 'description', 'image')
    
    def get_extra(self, request, obj=None, **kwargs):
        """Allow extra rows based on package duration"""
        if obj:
            # Number of extra rows = remaining days not yet assigned
            assigned_days = obj.itinerary.count()
            remaining = max(0, obj.days - assigned_days)
            return min(1, remaining)  # Show 1 extra row if days remain
        return 0
    
    def formset_valid(self, formset):
        """Validate that day count doesn't exceed package duration"""
        package = formset.instance
        day_numbers = []
        
        for form in formset.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                day_num = form.cleaned_data.get('day_number')
                if day_num:
                    day_numbers.append(day_num)
        
        # Check if any day exceeds package duration
        if day_numbers and max(day_numbers) > package.days:
            raise ValidationError(
                f"Cannot add itinerary beyond package duration of {package.days} days. "
                f"Maximum day number allowed: {package.days}"
            )
        
        return super().formset_valid(formset)

@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "package_summary",
        "package_type_badge",
        "budget_display",
        "duration_display",
        "route_summary",
        "quick_edit",
    )
    list_display_links = ("package_summary",)
    search_fields = ("name", "package_type", "transport_mode")
    list_filter = ("package_type", "transport_mode")
    autocomplete_fields = ["end_location"]
    list_select_related = ("start_location", "end_location")
    inlines = [PackageItineraryInline]
    save_on_top = True
    change_form_template = "admin/recommendation/travelpackage_change_form.html"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "start_location":
            # Return a form field directly so Django does not wrap it with
            # RelatedFieldWidgetWrapper (which adds the green plus icon).
            create_pin_url = reverse('admin:recommendation_travelpackage_create_pin_destination')
            return db_field.formfield(
                widget=DestinationMapPickerWidget(
                    destinations=Destination.objects.filter(
                        latitude__isnull=False,
                        longitude__isnull=False,
                    ).order_by("pName"),
                    create_pin_url=create_pin_url,
                )
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('create-pin-destination/', self.admin_site.admin_view(self.create_pin_destination), name='recommendation_travelpackage_create_pin_destination'),
        ]
        return custom + urls

    def create_pin_destination(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden('Forbidden')

        if request.method != 'POST':
            return HttpResponseBadRequest('POST required')

        try:
            payload = json.loads(request.body.decode('utf-8'))
            lat = float(payload.get('latitude'))
            lng = float(payload.get('longitude'))
            name = payload.get('name') or f'Pinned location {lat:.5f},{lng:.5f}'
        except Exception:
            return HttpResponseBadRequest('Invalid payload')

        dest = Destination.objects.create(pName=name, province='', latitude=lat, longitude=lng)
        return JsonResponse({'id': dest.id, 'name': dest.pName, 'province': dest.province or '', 'latitude': dest.latitude, 'longitude': dest.longitude})

    def get_exclude(self, request, obj=None):
        # Hide distance_km only on the add form.
        if obj is None:
            return ("distance_km",)
        return super().get_exclude(request, obj)

    @admin.display(description="Package")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" alt="{}" class="tm-admin-thumb" style="width: 84px; height: 52px; max-width: 84px; max-height: 52px; object-fit: cover;"/>',
                obj.image.url,
                obj.name,
            )
        return format_html('<div class="tm-admin-thumb tm-admin-thumb-empty">{}</div>', "No Image")

    @admin.display(description="Details", ordering="name")
    def package_summary(self, obj):
        transport = obj.get_transport_mode_display() if obj.transport_mode else "-"
        return format_html(
            '<div class="tm-admin-title">{}</div>'
            '<div class="tm-admin-sub">{}</div>',
            obj.name,
            transport,
        )

    @admin.display(description="Type", ordering="package_type")
    def package_type_badge(self, obj):
        return format_html('<span class="tm-admin-badge">{}</span>', obj.get_package_type_display())

    @admin.display(description="Budget", ordering="budget")
    def budget_display(self, obj):
        value = float(obj.budget or 0)
        return f"NPR {value:,.0f}"

    @admin.display(description="Duration", ordering="days")
    def duration_display(self, obj):
        return f"{obj.days} day{'s' if obj.days != 1 else ''}"

    @admin.display(description="Route")
    def route_summary(self, obj):
        start = obj.start_location.pName if obj.start_location else "-"
        end = obj.end_location.pName if obj.end_location else "-"
        return format_html(
            '<div class="tm-admin-sub">{}</div>'
            '<div class="tm-admin-sub">{}</div>',
            start,
            end,
        )

    @admin.display(description="Actions")
    def quick_edit(self, obj):
        url = reverse("admin:recommendation_travelpackage_change", args=[obj.id])
        return format_html('<a class="tm-admin-edit-btn" href="{}">Edit</a>', url)
import re

from rest_framework import serializers

from .models import Booking, TravelPackage


class BookingSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source='package.name', read_only=True)
    destination_name = serializers.CharField(source='package.end_location.pName', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'package',
            'package_name',
            'destination_name',
            'full_name',
            'contact_no',
            'email',
            'payment_method',
            'payment_status',
            'stripe_checkout_session_id',
            'stripe_payment_intent_id',
            'transaction_id',
            'paid_amount',
            'paid_at',
            'status',
            'notice',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'package_name', 'destination_name', 'status', 'created_at', 'notice', 'payment_status', 'stripe_checkout_session_id', 'stripe_payment_intent_id', 'transaction_id', 'paid_amount', 'paid_at']

    def validate_package(self, value):
        if not isinstance(value, TravelPackage):
            raise serializers.ValidationError('Invalid package selected.')
        return value

    def validate_contact_no(self, value):
        cleaned = re.sub(r'\s+', '', str(value).strip())
        if not re.fullmatch(r'(?:\+977|977)?9[78][0-9]{8}', cleaned):
            raise serializers.ValidationError(
                'Enter a valid Nepal mobile number (e.g. 98xxxxxxxx or +97798xxxxxxxx).'
            )
        return cleaned

from rest_framework import serializers
from .models import Address

# Serializer for Address model
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['state', 'local_gov', 'area', 'landmark', 'user_address']
        read_only_fields = []

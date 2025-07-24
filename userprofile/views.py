from rest_framework import generics, permissions
from .models import Address
from .serializers import AddressSerializer

# Create your views here.
## Permissions
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_admin


# Address Update View Endpoint
class AddressUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        return Address.objects.get(user=self.request.user)

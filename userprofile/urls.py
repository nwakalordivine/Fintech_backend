from django.urls import path
from .views import AddressUpdateView

urlpatterns = [
    path('address/', AddressUpdateView.as_view(), name='address-update'),
]

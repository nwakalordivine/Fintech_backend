from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.RegisterCreateView.as_view(), name='register'),
    path('auth/password/reset-code/', views.PasswordResetView.as_view(), name='email_reset_code'),
    path('auth/password-reset/', views.PasswordResetConfirmView.as_view(), name='password_reset'),
    path('profile/update/', views.UserUpdateView.as_view(), name='profile-update'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/wallet/', views.WalletView.as_view(), name="user_wallet_details")
]

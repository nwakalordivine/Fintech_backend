from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# url paths
urlpatterns = [
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', views.RegisterCreateView.as_view(), name='register'),
    path('api/auth/password/reset-code/', views.PasswordResetView.as_view(), name='email_reset_code'),
    path('api/auth/password-reset/', views.PasswordResetConfirmView.as_view(), name='password_reset'),
    path('api/profile/update/', views.UserUpdateView.as_view(), name='profile-update'),
    path('api/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('api/user/wallet/', views.WalletView.as_view(), name="user_wallet_details"),
    path('', views.HomeView.as_view(), name='home-view'),
]

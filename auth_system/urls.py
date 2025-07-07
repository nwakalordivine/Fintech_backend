from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterCreateView.as_view(), name='register'),
    path('password/reset-code/', views.PasswordResetView.as_view(), name='email_reset_code'),
    path('password-reset/', views.PasswordResetConfirmView.as_view(), name='password_reset'),
    path('send/verifictaion-code/', views.SendEmailListCreateView.as_view(), name='send_email'),
    path('verify-code/', views.CodeVerificationView.as_view(), name='verify_code'),
]

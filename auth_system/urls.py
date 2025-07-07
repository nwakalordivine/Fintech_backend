from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('send-email/', views.SendEmailListCreateView.as_view(), name='send_email'),
    path('verify-code/', views.CodeVerificationView.as_view(), name='verify_code'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterCreateView.as_view(), name='register'),
    path('verify/email/', views.CheckEmailView.as_view(), name='check_email'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

from rest_framework import generics, status
from rest_framework.views import APIView
from .models import SendEmail, User as CustomUser
from .serializers import (
    SendEmailSerializer, UserSerializer, CodeVerificationSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from . import services
from drf_spectacular.utils import extend_schema, OpenApiParameter


class SendEmailListCreateView(generics.GenericAPIView):
    queryset = SendEmail.objects.all()
    serializer_class = SendEmailSerializer

    @extend_schema(
        request=SendEmailSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_429_TOO_MANY_REQUESTS: None,
            status.HTTP_400_BAD_REQUEST: None,
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        random_code = services.generate_verification_code()
        existing = SendEmail.objects.filter(email=email).first()
        if existing and not existing.is_expired():
            return Response(
                {"message": "A verification code has already been sent. Please wait before requesting a new one."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        services.send_email(email=email, code=random_code)
        return Response({"message": "Verification code sent successfully."}, status=status.HTTP_200_OK)
    
    
class CheckEmailView(APIView):
    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name='email',
                location=OpenApiParameter.QUERY,
                type=str,
                required=True,
                description='Email address to check if user exists'
            )
        ],
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    )
    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email query param is required."}, status=status.HTTP_400_BAD_REQUEST)
        return services.check_users(email=email)


class CodeVerificationView(generics.GenericAPIView):
    queryset = SendEmail.objects.all()
    serializer_class = CodeVerificationSerializer

    @extend_schema(
        request=CodeVerificationSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        checker = services.confirm_code(email=email, code=code)
        messages = {
            "required": "Email and code are required.", 
            "expired": "Verification code has expired.", 
            "invalid": "Invalid verification code.", 
            "success": "Code verified successfully.", 
            "error": "Invalid email or code."
        }
        return Response(
            {"message": messages[checker]},
            status=status.HTTP_200_OK if checker == "success" else status.HTTP_400_BAD_REQUEST
        )
        

class RegisterCreateView(generics.GenericAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        request=UserSerializer,
        responses={
            status.HTTP_201_CREATED: None,
            status.HTTP_400_BAD_REQUEST: None,
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        record = SendEmail.objects.filter(email=email, is_verified=True).first()
        if not record:
            return Response({"error": "Email not verified."}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        SendEmail.objects.filter(email=user.email).delete()
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    

class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer

    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_500_INTERNAL_SERVER_ERROR: None,
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            services.password_reset(email=email)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        parameters=[
            OpenApiParameter('email', location=OpenApiParameter.PATH, type=str, description="User email"),
            OpenApiParameter('token', location=OpenApiParameter.PATH, type=str, description="Password reset token"),
        ],
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
        }
    )
    def post(self, request, email, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]

        if not email or not token or not new_password:
            return Response(
                {"error": "Email, token, and new password are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            password_changer = services.password_reset_confirm(email=email, token=token, new_password=new_password)
            if password_changer == "success":
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            elif password_changer == "invalid":
                return Response({"message": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

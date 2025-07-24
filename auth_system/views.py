from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from .models import User as CustomUser, Wallet
from .serializers import UserSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, UserUpdateSerializer, WalletSerializer, ErrorResponseSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from utilities import services
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.permissions import IsAuthenticated

# Permissions
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_admin
    
# Home
class HomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Fintech API!"}, status=status.HTTP_200_OK)

@extend_schema(
    summary="Register a new user",
    description="Creates a new user account. Returns user details and JWT tokens.",
    request=UserSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=UserSerializer,
            examples=[OpenApiExample(
                "User registration response",
                value={
                    "id": 1,
                    "firstname": "John",
                    "lastname": "Doe",
                    "nickname": "johnd",
                    "email": "john@example.com",
                    "phone_number": "08012345678",
                    "image": "https://res.cloudinary.com/yourimageurl.jpg",
                    "is_admin": False,
                    "date_of_birth": "2000-01-01",
                    "tokens": {
                        "refresh": "<refresh_token>",
                        "access": "<access_token>"
                    }
                },
                summary="Successful registration"
            )]
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Validation error",
            examples=[OpenApiExample(
                "Validation error",
                value={"error": "Email already exists."},
                summary="Email already exists"
            )]
        ),
    },
)
# Sign up Endpoint
class RegisterCreateView(generics.GenericAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        request=UserSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=UserSerializer,
                examples=[OpenApiExample(
                    "User registration response",
                    value={
                        "id": 1,
                        "firstname": "John",
                        "lastname": "Doe",
                        "nickname": "johnd",
                        "email": "john@example.com",
                        "phone_number": "08012345678",
                        "image": "https://res.cloudinary.com/yourimageurl.jpg",
                        "is_admin": False,
                        "date_of_birth": "2000-01-01",
                        "tokens": {
                            "refresh": "<refresh_token>",
                            "access": "<access_token>"
                        }
                    },
                    summary="Successful registration"
                )]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation error",
                examples=[OpenApiExample(
                    "Validation error",
                    value={"error": "Email already exists."},
                    summary="Email already exists"
                )]
            ),
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        return Response({
            **user_data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
@extend_schema(
    summary="Request password reset",
    description="Sends a password reset code to the user's email.",
    request=PasswordResetSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=None,
            description="Password reset code sent.",
            examples=[OpenApiExample(
                "Password reset sent",
                value={"message": "Password reset code sent."},
                summary="Success"
            )]
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Server error",
            examples=[OpenApiExample(
                "Server error",
                value={"error": "Internal server error."},
                summary="Error"
            )]
        ),
    },
)

# Password Reset Endpoint
class PasswordResetView(APIView):
    serializer_class = PasswordResetSerializer

    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=None,
                description="Password reset code sent.",
                examples=[OpenApiExample(
                    "Password reset sent",
                    value={"message": "Password reset code sent."},
                    summary="Success"
                )]
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Server error",
                examples=[OpenApiExample(
                    "Server error",
                    value={"error": "Internal server error."},
                    summary="Error"
                )]
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            services.password_reset(email=email)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "Password reset code sent."}, status=status.HTTP_200_OK)

@extend_schema(
    summary="Confirm password reset",
    description="Confirms password reset using code and sets new password.",
    request=PasswordResetConfirmSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=None,
            description="Password reset successful.",
            examples=[OpenApiExample(
                "Password reset successful",
                value={"message": "Password reset successful."},
                summary="Success"
            )]
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Bad request or invalid code.",
            examples=[OpenApiExample(
                "Invalid code",
                value={"error": "Invalid reset code."},
                summary="Invalid code"
            )]
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="User not found.",
            examples=[OpenApiExample(
                "User not found",
                value={"error": "User not found."},
                summary="User not found"
            )]
        ),
    },
)

# Password Reset Confirm Endpoint
class PasswordResetConfirmView(APIView):
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=None,
                description="Password reset successful.",
                examples=[OpenApiExample(
                    "Password reset successful",
                    value={"message": "Password reset successful."},
                    summary="Success"
                )]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Bad request or invalid code.",
                examples=[OpenApiExample(
                    "Invalid code",
                    value={"error": "Invalid reset code."},
                    summary="Invalid code"
                )]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="User not found.",
                examples=[OpenApiExample(
                    "User not found",
                    value={"error": "User not found."},
                    summary="User not found"
                )]
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]
        email = serializer.validated_data.get("email")
        code = serializer.validated_data.get("code")

        if not email or not code or not new_password:
            return Response(
                {"error": "email, code, and new password are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            password_changer = services.password_reset_confirm(email=email, code=code, new_password=new_password)
            if password_changer == "success":
                 return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            elif password_changer == "invalid":
                return Response({"error": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)
            elif password_changer == "expired":
                return Response({"error": "Reset code expired or not found."}, status=status.HTTP_400_BAD_REQUEST)
            elif password_changer == "not_found":
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            elif password_changer == "invalid_id":
                return Response({"error": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

@extend_schema(
    summary="Update user profile",
    description="Update nickname, image, or phone number for the authenticated user.",
    request=UserUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserUpdateSerializer,
            description="Profile updated successfully.",
            examples=[OpenApiExample(
                "Profile updated",
                value={"nickname": "newnick", "image": "https://res.cloudinary.com/yourimageurl.jpg", "phone_number": "08012345678"},
                summary="Success"
            )]
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Validation error.",
            examples=[OpenApiExample(
                "Validation error",
                value={"error": "Phone number already in use."},
                summary="Phone number exists"
            )]
        ),
    },
)

# Userprofile Update Endpoint
class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

@extend_schema(
    summary="Get user profile",
    description="Retrieve the authenticated user's profile information.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserSerializer,
            description="User profile details.",
            examples=[OpenApiExample(
                "User profile",
                value={
                    "id": 1,
                    "firstname": "John",
                    "lastname": "Doe",
                    "nickname": "johnd",
                    "email": "john@example.com",
                    "phone_number": "08012345678",
                    "image": "https://res.cloudinary.com/yourimageurl.jpg",
                    "is_admin": False,
                    "date_of_birth": "2000-01-01"
                },
                summary="Profile"
            )]
        ),
    },
)

# UserProfile View Endpoint
class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        return self.request.user
    
@extend_schema(
    summary="Get wallet details",
    description="Retrieve the authenticated user's wallet information.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=WalletSerializer,
            description="Wallet details.",
            examples=[OpenApiExample(
                "Wallet details",
                value={
                    "id": 1,
                    "user": 1,
                    "balance": "10000.00",
                    "monnify_account_number": "1234567890",
                    "monnify_bank_name": "Monnify Bank",
                    "bank_user_name": "John Doe",
                    "tier": "basic",
                    "accountreference": "ref123"
                },
                summary="Wallet"
            )]
        ),
    },
)

# WalletView Endpoint
class WalletView(generics.RetrieveAPIView):
    queryset = Wallet
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.wallet

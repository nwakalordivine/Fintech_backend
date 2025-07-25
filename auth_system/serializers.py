from rest_framework import serializers
from django.contrib.auth import get_user_model
from utilities.cloudinary_helper import upload_to_cloudinary
from datetime import date
from .models import Wallet

CustomUser = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    date_of_birth = serializers.DateField(required=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'firstname', 'lastname', 'nickname', 'email', 'password', 'phone_number', 'image', 'is_admin', 'date_of_birth']
        read_only_fields = ['id', 'is_staff', 'is_admin']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email field cannot be empty.")
        return value
    
    def validate_date_of_birth(self, value):
        if value is None:
            raise serializers.ValidationError("Date of birth is required.")
        
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 17:
            raise serializers.ValidationError("You must be at least 17 years old to register.")
        
        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password field cannot be empty.")
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate_phone_number(self, value):
        if value and len(value) != 11:
            raise serializers.ValidationError("Phone number must be 11 digits.")
        user_qs = CustomUser.objects.filter(phone_number=value)
        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise serializers.ValidationError("User with this phone number already exists.")
        return value
    
    def create(self, validated_data):
        image_file = validated_data.get('image', None)
        if image_file:
            image_url = upload_to_cloudinary(image_file, folder_name="fintechapp_user_images")
            validated_data['image'] = image_url
        customuser = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            firstname=validated_data.get('firstname').title(),
            lastname=validated_data.get('lastname').title(),
            phone_number=validated_data.get('phone_number'),
            image=validated_data.get('image'),
            date_of_birth=validated_data.get('date_of_birth'),
        )

        from .models import Wallet
        if not hasattr(customuser, 'wallet'):
            Wallet.objects.create(user=customuser)
        return customuser

    def get_wallet_balance(self, obj):
        wallet = getattr(obj, 'wallet', None)
        if wallet:
            return "{:.2f}".format(wallet.balance)
        return "0.00"
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        wallet = getattr(instance, 'wallet', None)
        if wallet:
            rep["image"] = instance.image
            rep["account_details"] = {
                "monnify_account_number": wallet.monnify_account_number if wallet else None,
                "monnify_bank_name": wallet.monnify_bank_name if wallet else None,
                "bank_user_name": wallet.bank_user_name if wallet else None,
                "account_reference": wallet.accountreference if wallet else None,
                "tier": wallet.tier if wallet else None,
                "wallet_balance": "{:.2f}".format(wallet.balance) if wallet else "0.00"
            }
            return rep


class UserUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    phone_number = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['nickname', 'image', 'phone_number']

    def validate_phone_number(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(phone_number=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Phone number already in use.")
        return value

    def update(self, instance, validated_data):
        image_file = validated_data.get('image')
        if image_file:
            from utilities.cloudinary_helper import upload_to_cloudinary
            image_url = upload_to_cloudinary(image_file, folder_name="fintechapp_user_images")
            instance.image = image_url

        instance.nickname = validated_data.get('nickname', instance.nickname)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        return instance

    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True)
    code = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs['new_password']
        confirm_password = attrs['confirm_password']
        code = attrs['code']
        if not new_password or not confirm_password:
            raise serializers.ValidationError("Both password fields are required.")

        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match.")

        if len(new_password) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")
        if not code.isdigit() or len(code) != 5:
            raise serializers.ValidationError("Code must be a 5-digit number.")
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class TokenResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            "id", "user", "balance", "monnify_account_number", "monnify_bank_name", "bank_user_name", "tier", "accountreference"
        ]
        read_only_fields = ["id", "user", "balance", "monnify_account_number", "monnify_bank_name", "bank_user_name", "tier", "accountreference"]

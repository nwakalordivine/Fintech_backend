from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.timezone import now, timedelta
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
# Create your models here.

class SendEmail(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    code = models.CharField(max_length=10, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.created_at + timedelta(hours=1)

    def __str__(self):
        return self.email


class CustomUserManager(BaseUserManager):
    def create_user(self, email, firstname=None, lastname=None, password=None, phone_number=None, image=None, is_staff=False, is_admin=False, is_superuser=False, is_verified=False):
        if not email:
            raise ValueError('Users must have an email address')
        if not firstname or not lastname:
            raise ValueError('Users must have a first and last name')

        user = self.model(
            firstname=firstname,
            lastname=lastname,
            email=self.normalize_email(email),
            phone_number=phone_number,
            is_staff=is_staff,
            is_admin=is_admin,
            is_superuser=is_superuser,
            image=image,
            is_verified=is_verified
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, firstname, lastname, email, image=None, password=None, phone_number=None):
        return self.create_user(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password=password,
            phone_number=phone_number,
            is_verified=True,
            is_staff=True,
            is_admin=True,
            is_superuser=True,
            image=image
        )


class User(AbstractBaseUser):
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=11, unique=True, null=True, blank=True)
    image = CloudinaryField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'phone_number']

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.email})"

    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_admin or self.is_superuser

    def save(self, *args, **kwargs):
        if self.phone_number and len(self.phone_number) != 11:
            raise ValidationError("Phone number must be 11 digits")
        super(User, self).save(*args, **kwargs)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email} Wallet - ₦{self.balance}"

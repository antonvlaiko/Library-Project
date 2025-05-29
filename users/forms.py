from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from library.models import UserProfile

# class RegisterForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class CustomUserCreationForm(UserCreationForm):
    # email = forms.EmailField(required=True)
    # first_name = forms.CharField(required=False, max_length=30)
    # last_name = forms.CharField(required=False, max_length=150)
    phone = forms.CharField(required=True, max_length=20)
    address = forms.CharField(required=True, max_length=255)
    patronymic = forms.CharField(required=False, max_length=100)
    is_staff = forms.BooleanField(
        label="Я є бібліотекарем",  # "I am a librarian"
        required=False
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2", "is_staff", "phone", "address", "patronymic")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        phone = self.cleaned_data['phone']
        address = self.cleaned_data['address']
        patronymic = self.cleaned_data.get('patronymic', '')

        # Delete any existing profile for safety (optional)
        UserProfile.objects.filter(user=user).delete()

        # Create new profile
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=address,
            patronymic=patronymic
        )

        return user

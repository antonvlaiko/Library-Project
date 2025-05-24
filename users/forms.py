from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(
        label="Я є бібліотекарем",  # "I am a librarian"
        required=False
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "is_staff")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_staff = self.cleaned_data["is_staff"]
        if commit:
            user.save()
        return user

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from library.models import UserProfile
from django.utils.translation import gettext_lazy as _
# class RegisterForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(label=_("Phone"), max_length=20, required=False)
    address = forms.CharField(label=_("Address"), max_length=255, required=False)
    patronymic = forms.CharField(label=_("Patronymic"), max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'patronymic', 'phone', 'address', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            # Save UserProfile here
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone'),
                address=self.cleaned_data.get('address'),
                patronymic=self.cleaned_data.get('patronymic'),
            )
        return user
    # email = forms.EmailField(required=True)
    # phone = forms.CharField(max_length=20, required=True)
    # address = forms.CharField(max_length=255, required=True)
    # patronymic = forms.CharField(max_length=100, required=False)
    #
    # class Meta:
    #     model = User
    #     fields = ("username", "email", "first_name", "last_name", "patronymic", "phone", "address", "password1", "password2")
    #
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.email = self.cleaned_data['email']
    #     if commit:
    #         user.save()
    #         profile, created = UserProfile.objects.get_or_create(
    #             user=user,
    #             defaults={
    #                 'phone': self.cleaned_data['phone'],
    #                 'address': self.cleaned_data['address'],
    #                 'patronymic': self.cleaned_data['patronymic'],
    #             }
    #         )
    #     return user
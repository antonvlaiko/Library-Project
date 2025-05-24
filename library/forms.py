from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': _("Username"),
            'email': _("Email"),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("This username is already taken."))
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("This email is already in use."))
        return email

from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')
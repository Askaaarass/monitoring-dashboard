from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserRole

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        required=False, 
        label="Телефон"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'phone_number')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.ENGINEER
        if commit:
            user.save()
        return user
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserRole

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=UserRole.choices,
        initial=UserRole.ENGINEER,
        required=False,
        label="Роль в системе"
    )
    phone_number = forms.CharField(
        required=False, 
        label="Телефон"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'role', 'phone_number')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Если роль не выбрана явно, назначаем Инженера
        user.role = self.cleaned_data.get('role') or UserRole.ENGINEER
        if commit:
            user.save()
        return user
# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
# forms.py (añadir estas clases)

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

from .models import Usuario
import re

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = [
            "username", "nombre", "apellido", "rut",
            "direccion", "email", "password1", "password2"
        ]
        labels = {
            "username": "Nombre de usuario",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "rut": "RUT",
            "direccion": "Dirección",
            "email": "Correo electrónico",
            "password1": "Contraseña",
            "password2": "Confirmar contraseña",
        }

    def clean_rut(self):
        rut = self.cleaned_data.get("rut")
        if not re.match(r"^\d{7,8}-[0-9Kk]$", rut):
            raise forms.ValidationError("El RUT debe tener el formato 12345678-9 o 12345678-K.")
        return rut

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email


class UserUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar campos básicos del User.
    """
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@ejemplo.com'}),
        }

class SimplePasswordChangeForm(PasswordChangeForm):
    """
    Hereda del PasswordChangeForm para poder aplicar clases bootstrap a los campos.
    """
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña actual'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar nueva contraseña'}))
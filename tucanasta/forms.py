# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
        
from django import forms
from .models import Pyme, Producto

from .models import Usuario
from .models import Producto, Supermercado
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
    
    
class PymeRegistrationForm(forms.ModelForm):
    class Meta:
        model = Pyme
        fields = ['nombre', 'telefono', 'web', 'direccion', 'descripcion', 'documento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'web': forms.URLInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    documento = forms.FileField(required=True, help_text="Adjunta documento (rut, escritura, permiso municipal, etc.)", widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

class PymeProductForm(forms.ModelForm):
    # keep precio field explicit so we can clean commas / currency symbols easily
    precio = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1290 o 1.290,50'}),
        label='Precio'
    )
    moneda = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}), initial='CLP')

    class Meta:
        model = Producto
        # no 'supermercado' (se asigna desde la pyme), y no tocar fecha_actualizacion
        exclude = ['supermercado', 'fecha_actualizacion']

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen_url': forms.URLInput(attrs={'class': 'form-control'}),
            'producto_url': forms.URLInput(attrs={'class': 'form-control'}),
            'codigo_interno': forms.TextInput(attrs={'class': 'form-control'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_precio(self):
        raw = self.cleaned_data.get('precio', '')
        if raw is None:
            raise forms.ValidationError("Ingrese un precio válido.")
        # remover símbolos, espacios y puntos de miles; reemplazar coma decimal por punto
        cleaned = str(raw).strip().replace('$', '').replace(' ', '')
        # si usan puntos para miles y coma para decimales: "1.234,56" -> "1234.56"
        if ',' in cleaned and '.' in cleaned:
            # asumir formato 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # sólo comas -> reemplazar coma por punto; sólo puntos -> mantener
            cleaned = cleaned.replace(',', '.').replace('.', '.', 1)
        try:
            # convertir a Decimal-compatible string
            value = float(cleaned)
        except Exception:
            raise forms.ValidationError("Precio inválido. Usa sólo números, punto o coma decimal.")
        if value < 0:
            raise forms.ValidationError("El precio debe ser positivo.")
        # retornamos Decimal string/float que Django aceptará en el campo DecimalField al guardar
        return value

    def clean_moneda(self):
        m = (self.cleaned_data.get('moneda') or 'CLP').strip().upper()
        return m
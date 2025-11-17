from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Supermercado, Producto, Cotizacion, CotizacionItem, Usuario

@admin.register(Supermercado)
class SupermercadoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "url_principal")

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marca", "supermercado", "precio", "tipo", "fecha_actualizacion", "disponible")
    list_filter = ("supermercado", "tipo", "disponible")
    search_fields = ("nombre", "marca", "descripcion")

# Register your models here.

class CotizacionItemInline(admin.TabularInline):
    model = CotizacionItem
    extra = 0
    readonly_fields = ('precio_unidad',)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos adicionales", {"fields": ("nombre", "apellido", "rut", "direccion")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Datos adicionales", {"fields": ("nombre", "apellido", "rut", "direccion", "email")}),
    )
    list_display = ("username", "email", "nombre", "apellido", "rut")
    
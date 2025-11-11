from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class Supermercado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    url_principal = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.nombre} {self.apellido})"

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True, null=True)
    tipo = models.CharField(max_length=100, help_text="Categoría o tipo de producto, ej: pasta, arroz, aceite")
    descripcion = models.TextField(blank=True, null=True)

    # Relación con supermercado
    supermercado = models.ForeignKey(Supermercado, on_delete=models.CASCADE, related_name="productos")

    # Datos económicos
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=10, default="CLP")

    # Links e imagen
    imagen_url = models.URLField(blank=True, null=True)
    producto_url = models.URLField(blank=True, null=True)

    # Campos útiles para comparaciones y estadísticas
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    disponible = models.BooleanField(default=True)

    # Opcional: identificador interno o externo (para APIs o scraping)
    codigo_interno = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["tipo", "supermercado", "precio"]

    def __str__(self):
        return f"{self.nombre} ({self.supermercado.nombre}) - ${self.precio}"

# Create your models here.



class Cotizacion(models.Model):
    STATUS_CHOICES = (
        ('open', 'Abierta'),
        ('saved', 'Guardada'),
        ('sent', 'Enviada'),
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cotizaciones')
    nombre = models.CharField(max_length=200, blank=True)  # opcional: nombre de la cotización
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'Cotización #{self.pk} - {self.usuario} - {self.status}'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unidad = models.DecimalField(max_digits=10, decimal_places=2)  # precio al momento de agregar

    class Meta:
        unique_together = ('cotizacion', 'producto')

    @property
    def subtotal(self):
        return float(self.precio_unidad) * int(self.cantidad)

    def __str__(self):
        return f'{self.producto.nombre} x{self.cantidad} en cot #{self.cotizacion.pk}'
    
    
class Pyme(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pyme')
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    web = models.URLField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    supermercado = models.OneToOneField(Supermercado, on_delete=models.CASCADE, related_name='pyme', null=True, blank=True)
    approved = models.BooleanField(default=False)  # para revisión/admin
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # NUEVO: documento adjunto para verificación
    documento = models.FileField(upload_to='pyme_docs/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.user.username})"
    
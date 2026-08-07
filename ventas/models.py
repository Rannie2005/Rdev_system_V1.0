from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from almacen.models import ProductoVariante
from decimal import Decimal

class Venta(models.Model):
    """Modelo principal de venta"""
    ESTADO_CHOICES = (
        ('completada', 'Completada'),
        ('anulada', 'Anulada'),
        ('devuelta', 'Devuelta'),
    )
    
    folio = models.CharField(max_length=20, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ventas')
    cliente = models.CharField(max_length=200, blank=True, null=True)  # Nombre del cliente
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada')
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta {self.folio} - {self.cliente or 'Cliente sin nombre'}"

    def calcular_total(self):
        """Calcula el total de la venta sumando todos los detalles"""
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save()
        return total

    @property
    def numero_articulos(self):
        """Número total de artículos vendidos"""
        return sum(detalle.cantidad for detalle in self.detalles.all())


class DetalleVenta(models.Model):
    """Detalle de cada producto en la venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto_variante = models.ForeignKey(ProductoVariante, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Ventas"

    def __str__(self):
        return f"{self.venta.folio} - {self.producto_variante.producto.nombre} x{self.cantidad}"

    def save(self, *args, **kwargs):
        """Calcula el subtotal automáticamente"""
        if not self.subtotal:
            self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class Devolucion(models.Model):
    """Registro de devoluciones"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='devoluciones')
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField()
    total_devuelto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Devolución"
        verbose_name_plural = "Devoluciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"Devolución de {self.venta.folio}"


class DetalleDevolucion(models.Model):
    """Detalle de productos devueltos"""
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='detalles')
    producto_variante = models.ForeignKey(ProductoVariante, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Precio al que se vendió
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de Devolución"
        verbose_name_plural = "Detalles de Devoluciones"

    def __str__(self):
        return f"{self.devolucion.venta.folio} - {self.producto_variante.producto.nombre} x{self.cantidad}"

    def save(self, *args, **kwargs):
        """Calcula el subtotal automáticamente"""
        if not self.subtotal:
            self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
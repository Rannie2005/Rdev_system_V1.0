from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Categoria(models.Model):
    """Categorías de productos (ej. Camisas, Pantalones, Tenis, Accesorios)"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """Proveedores de productos"""
    nombre = models.CharField(max_length=200)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    """Tallas globales (creadas por el usuario)"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Producto base"""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    marca = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, related_name='productos')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.marca or 'Sin marca'}"


class ProductoVariante(models.Model):
    """Variante de producto (talla, precio, stock, color)"""
    ESTADO_STOCK = (
        ('disponible', 'Disponible'),
        ('poco_stock', 'Casi Agotado'),
        ('agotado', 'Agotado'),
    )
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    talla = models.ForeignKey(Talla, on_delete=models.PROTECT, related_name='variantes')
    color = models.CharField(max_length=50, blank=True, null=True)  # Opcional
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Productos"
        unique_together = ['producto', 'talla']  # Un producto no puede tener dos veces la misma talla
        ordering = ['producto__nombre', 'talla__nombre']

    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla.nombre}"

    @property
    def estado_stock(self):
        """Determina el estado del stock según la cantidad"""
        if self.stock <= 0:
            return 'agotado'
        elif self.stock <= 5:
            return 'poco_stock'
        else:
            return 'disponible'

    @property
    def estado_stock_display(self):
        """Devuelve el estado del stock en texto legible"""
        estados = {
            'disponible': 'Disponible',
            'poco_stock': '¡Casi Agotado!',
            'agotado': 'Agotado'
        }
        return estados.get(self.estado_stock, 'Desconocido')

    @property
    def ganancia_unidad(self):
        """Calcula la ganancia por unidad"""
        return self.precio_venta - self.producto.precio_compra

    def reducir_stock(self, cantidad):
        """Reduce el stock de la variante"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            self.save()
            return True
        return False

    def aumentar_stock(self, cantidad):
        """Aumenta el stock de la variante"""
        self.stock += cantidad
        self.save()
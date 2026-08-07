from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class AnalisisSemanal(models.Model):
    """Análisis de ventas semanal"""
    semana = models.PositiveIntegerField()
    anio = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Métricas principales
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ganancias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_productos_vendidos = models.PositiveIntegerField(default=0)
    numero_ventas = models.PositiveIntegerField(default=0)
    
    # Métricas adicionales
    promedio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    venta_mas_alta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    venta_mas_baja = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Top productos
    top_productos = models.TextField(default='[]')
    productos_menos_vendidos = models.TextField(default='[]')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Análisis Semanal"
        verbose_name_plural = "Análisis Semanales"
        unique_together = ['semana', 'anio']
        ordering = ['-anio', '-semana']

    def __str__(self):
        return f"Semana {self.semana} - {self.anio}"


class AnalisisMensual(models.Model):
    """Análisis de ventas mensual"""
    mes = models.PositiveIntegerField()
    anio = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Métricas principales
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ganancias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_productos_vendidos = models.PositiveIntegerField(default=0)
    numero_ventas = models.PositiveIntegerField(default=0)
    
    # Métricas adicionales
    promedio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    venta_mas_alta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    venta_mas_baja = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Top productos
    top_productos = models.TextField(default='[]')
    productos_menos_vendidos = models.TextField(default='[]')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Análisis Mensual"
        verbose_name_plural = "Análisis Mensuales"
        unique_together = ['mes', 'anio']
        ordering = ['-anio', '-mes']

    def __str__(self):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[self.mes]} {self.anio}"


class ReporteStockBajo(models.Model):
    """Reporte de productos con stock bajo"""
    producto_variante = models.ForeignKey('almacen.ProductoVariante', on_delete=models.CASCADE)
    stock_actual = models.PositiveIntegerField()
    fecha_reporte = models.DateField(auto_now_add=True)
    notificado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Reporte de Stock Bajo"
        verbose_name_plural = "Reportes de Stock Bajo"
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f"{self.producto_variante.producto.nombre} - Stock: {self.stock_actual}"
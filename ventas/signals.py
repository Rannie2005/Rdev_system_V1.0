from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Venta, Devolucion, DetalleVenta, DetalleDevolucion
from analisis.models import AnalisisSemanal, AnalisisMensual


def actualizar_analisis_venta(venta):
    """Actualizar análisis semanal y mensual después de una venta"""
    if venta.estado != 'completada':
        return
    
    fecha = venta.fecha
    año = fecha.year
    
    # --- Semanal ---
    semana = fecha.isocalendar()[1]
    analisis_semanal, _ = AnalisisSemanal.objects.get_or_create(
        semana=semana,
        anio=año,
        defaults={
            'fecha_inicio': fecha - timedelta(days=fecha.weekday()),
            'fecha_fin': fecha - timedelta(days=fecha.weekday()) + timedelta(days=6),
        }
    )
    recalcular_analisis_semanal(analisis_semanal)
    
    # --- Mensual ---
    mes = fecha.month
    analisis_mensual, _ = AnalisisMensual.objects.get_or_create(
        mes=mes,
        anio=año,
        defaults={
            'fecha_inicio': fecha.replace(day=1),
            'fecha_fin': fecha.replace(day=1) + timedelta(days=32),
        }
    )
    recalcular_analisis_mensual(analisis_mensual)


def recalcular_analisis_semanal(analisis):
    """Recalcular todos los datos de un análisis semanal"""
    from django.db.models import Sum
    from decimal import Decimal
    import json
    
    ventas = Venta.objects.filter(
        fecha__date__gte=analisis.fecha_inicio,
        fecha__date__lte=analisis.fecha_fin,
        estado='completada'
    )
    
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas = ventas.count()
    
    # Calcular ganancias y productos vendidos
    detalles = DetalleVenta.objects.filter(venta__in=ventas)
    total_ganancias = Decimal('0.00')
    total_productos = 0
    
    for detalle in detalles.select_related('producto_variante__producto'):
        ganancia = (detalle.precio_unitario - detalle.producto_variante.producto.precio_compra) * detalle.cantidad
        total_ganancias += ganancia
        total_productos += detalle.cantidad
    
    # Top productos
    top_productos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    analisis.total_ventas = total_ventas
    analisis.total_ganancias = total_ganancias
    analisis.total_productos_vendidos = total_productos
    analisis.numero_ventas = num_ventas
    analisis.top_productos = json.dumps(list(top_productos))
    analisis.save()


def recalcular_analisis_mensual(analisis):
    """Recalcular todos los datos de un análisis mensual"""
    from django.db.models import Sum
    from decimal import Decimal
    import json
    
    ventas = Venta.objects.filter(
        fecha__date__gte=analisis.fecha_inicio,
        fecha__date__lte=analisis.fecha_fin,
        estado='completada'
    )
    
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas = ventas.count()
    
    detalles = DetalleVenta.objects.filter(venta__in=ventas)
    total_ganancias = Decimal('0.00')
    total_productos = 0
    
    for detalle in detalles.select_related('producto_variante__producto'):
        ganancia = (detalle.precio_unitario - detalle.producto_variante.producto.precio_compra) * detalle.cantidad
        total_ganancias += ganancia
        total_productos += detalle.cantidad
    
    top_productos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    analisis.total_ventas = total_ventas
    analisis.total_ganancias = total_ganancias
    analisis.total_productos_vendidos = total_productos
    analisis.numero_ventas = num_ventas
    analisis.top_productos = json.dumps(list(top_productos))
    analisis.save()


# --- SEÑALES ---

@receiver(post_save, sender=Venta)
def venta_creada_actualizar_analisis(sender, instance, created, **kwargs):
    """Cuando se crea o actualiza una venta, actualizar análisis"""
    if instance.estado == 'completada':
        actualizar_analisis_venta(instance)


@receiver(post_save, sender=Devolucion)
def devolucion_creada_actualizar_analisis(sender, instance, created, **kwargs):
    """Cuando se crea una devolución, recalcular análisis"""
    if created:
        # La venta cambió a 'devuelta' o se actualizó su total
        actualizar_analisis_venta(instance.venta)


@receiver(post_save, sender=Venta)
def venta_estado_cambiado(sender, instance, **kwargs):
    """Cuando una venta cambia de estado (anulada, devuelta)"""
    if instance.estado in ['anulada', 'devuelta']:
        actualizar_analisis_venta(instance)
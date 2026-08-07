from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal

from ventas.models import Venta, DetalleVenta
from almacen.models import ProductoVariante
from .models import AnalisisSemanal, AnalisisMensual, ReporteStockBajo


@login_required
def dashboard_analisis(request):
    """Dashboard principal de análisis"""
    hoy = timezone.now()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    inicio_mes = hoy.replace(day=1)
    
    # Ventas de la semana
    ventas_semana = Venta.objects.filter(
        fecha__date__gte=inicio_semana.date(),
        fecha__date__lte=fin_semana.date(),
        estado='completada'
    )
    
    total_semana = ventas_semana.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas_semana = ventas_semana.count()
    
    # Ventas del mes
    ventas_mes = Venta.objects.filter(
        fecha__date__gte=inicio_mes.date(),
        estado='completada'
    )
    
    total_mes = ventas_mes.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas_mes = ventas_mes.count()
    
    # Productos más vendidos (últimos 30 días)
    fecha_limite = hoy - timedelta(days=30)
    top_productos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=fecha_limite.date(),
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    # Productos menos vendidos (últimos 30 días)
    menos_vendidos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=fecha_limite.date(),
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('total_vendido')[:5]
    
    # Stock bajo
    stock_bajo = ProductoVariante.objects.filter(stock__lte=5, stock__gt=0).count()
    agotados = ProductoVariante.objects.filter(stock=0).count()
    
    # Análisis semanal guardado
    analisis_semanal = AnalisisSemanal.objects.filter(
        anio=hoy.year,
        semana=hoy.isocalendar()[1]
    ).first()
    
    # Análisis mensual guardado
    analisis_mensual = AnalisisMensual.objects.filter(
        anio=hoy.year,
        mes=hoy.month
    ).first()
    
    # Total de ventas general
    total_general = Venta.objects.filter(estado='completada').aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas_general = Venta.objects.filter(estado='completada').count()
    
    context = {
        'total_semana': total_semana,
        'num_ventas_semana': num_ventas_semana,
        'total_mes': total_mes,
        'num_ventas_mes': num_ventas_mes,
        'total_general': total_general,
        'num_ventas_general': num_ventas_general,
        'top_productos': top_productos,
        'menos_vendidos': menos_vendidos,
        'stock_bajo': stock_bajo,
        'agotados': agotados,
        'analisis_semanal': analisis_semanal,
        'analisis_mensual': analisis_mensual,
        'fecha_inicio_semana': inicio_semana,
        'fecha_fin_semana': fin_semana,
        'fecha_inicio_mes': inicio_mes,
    }
    return render(request, 'analisis/dashboard.html', context)


@login_required
def analisis_semanal(request):
    """Vista detallada de análisis semanal"""
    hoy = timezone.now()
    semana_actual = hoy.isocalendar()[1]
    anio_actual = hoy.year
    
    # Obtener o crear análisis de la semana actual
    analisis, created = AnalisisSemanal.objects.get_or_create(
        semana=semana_actual,
        anio=anio_actual,
        defaults={
            'fecha_inicio': hoy - timedelta(days=hoy.weekday()),
            'fecha_fin': hoy - timedelta(days=hoy.weekday()) + timedelta(days=6),
        }
    )
    
    if created:
        actualizar_analisis_semanal(analisis)
    
    # Obtener análisis de semanas anteriores
    semanas_anteriores = AnalisisSemanal.objects.filter(
        Q(anio=anio_actual, semana__lt=semana_actual) |
        Q(anio__lt=anio_actual)
    ).order_by('-anio', '-semana')[:12]
    
    # Productos más vendidos de la semana
    top_productos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=analisis.fecha_inicio,
        venta__fecha__date__lte=analisis.fecha_fin,
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre',
        'producto_variante__talla__nombre',
        'producto_variante__color',
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('subtotal')
    ).order_by('-total_vendido')[:20]
    
    # Productos menos vendidos de la semana
    menos_vendidos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=analisis.fecha_inicio,
        venta__fecha__date__lte=analisis.fecha_fin,
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre',
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('total_vendido')[:10]
    
    context = {
        'analisis': analisis,
        'semanas_anteriores': semanas_anteriores,
        'top_productos': top_productos,
        'menos_vendidos': menos_vendidos,
    }
    return render(request, 'analisis/analisis_semanal.html', context)


@login_required
def analisis_mensual(request):
    """Vista detallada de análisis mensual"""
    hoy = timezone.now()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Obtener o crear análisis del mes actual
    analisis, created = AnalisisMensual.objects.get_or_create(
        mes=mes_actual,
        anio=anio_actual,
        defaults={
            'fecha_inicio': hoy.replace(day=1),
            'fecha_fin': hoy.replace(day=1) + timedelta(days=32),
        }
    )
    
    if created:
        actualizar_analisis_mensual(analisis)
    
    # Obtener análisis de meses anteriores
    meses_anteriores = AnalisisMensual.objects.filter(
        Q(anio=anio_actual, mes__lt=mes_actual) |
        Q(anio__lt=anio_actual)
    ).order_by('-anio', '-mes')[:12]
    
    # Productos más vendidos del mes
    top_productos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=analisis.fecha_inicio,
        venta__fecha__date__lte=analisis.fecha_fin,
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre',
        'producto_variante__talla__nombre',
        'producto_variante__color',
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum('subtotal')
    ).order_by('-total_vendido')[:20]
    
    # Productos menos vendidos del mes
    menos_vendidos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=analisis.fecha_inicio,
        venta__fecha__date__lte=analisis.fecha_fin,
        venta__estado='completada'
    ).values(
        'producto_variante__producto__nombre',
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('total_vendido')[:10]
    
    context = {
        'analisis': analisis,
        'meses_anteriores': meses_anteriores,
        'top_productos': top_productos,
        'menos_vendidos': menos_vendidos,
    }
    return render(request, 'analisis/analisis_mensual.html', context)


@login_required
def reporte_stock_bajo(request):
    """Reporte de productos con stock bajo"""
    productos_bajo_stock = ProductoVariante.objects.filter(
        stock__lte=5,
        stock__gt=0
    ).select_related('producto', 'talla').order_by('stock')
    
    productos_agotados = ProductoVariante.objects.filter(
        stock=0
    ).select_related('producto', 'talla').order_by('producto__nombre')
    
    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'productos_agotados': productos_agotados,
        'total_bajo_stock': productos_bajo_stock.count(),
        'total_agotados': productos_agotados.count(),
    }
    return render(request, 'analisis/reporte_stock_bajo.html', context)


@login_required
def generar_reportes(request):
    """Generar reportes manualmente"""
    if request.method == 'POST':
        try:
            hoy = timezone.now()
            semana_actual = hoy.isocalendar()[1]
            mes_actual = hoy.month
            anio_actual = hoy.year
            
            # Actualizar análisis semanal
            analisis_semanal, _ = AnalisisSemanal.objects.get_or_create(
                semana=semana_actual,
                anio=anio_actual,
                defaults={
                    'fecha_inicio': hoy - timedelta(days=hoy.weekday()),
                    'fecha_fin': hoy - timedelta(days=hoy.weekday()) + timedelta(days=6),
                }
            )
            actualizar_analisis_semanal(analisis_semanal)
            
            # Actualizar análisis mensual
            analisis_mensual, _ = AnalisisMensual.objects.get_or_create(
                mes=mes_actual,
                anio=anio_actual,
                defaults={
                    'fecha_inicio': hoy.replace(day=1),
                    'fecha_fin': hoy.replace(day=1) + timedelta(days=32),
                }
            )
            actualizar_analisis_mensual(analisis_mensual)
            
            messages.success(request, '✅ Reportes generados exitosamente.')
        except Exception as e:
            messages.error(request, f'❌ Error al generar reportes: {str(e)}')
        
        return redirect('analisis:dashboard')
    
    return render(request, 'analisis/generar_reportes.html')


def actualizar_analisis_semanal(analisis):
    """Actualizar los datos de un análisis semanal"""
    from django.db.models import Sum, Avg, Max, Min
    
    ventas = Venta.objects.filter(
        fecha__date__gte=analisis.fecha_inicio,
        fecha__date__lte=analisis.fecha_fin,
        estado='completada'
    )
    
    # Métricas principales
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas = ventas.count()
    
    # Métricas adicionales
    promedio_venta = ventas.aggregate(promedio=Avg('total'))['promedio'] or Decimal('0.00')
    venta_mas_alta = ventas.aggregate(maximo=Max('total'))['maximo'] or Decimal('0.00')
    venta_mas_baja = ventas.aggregate(minimo=Min('total'))['minimo'] or Decimal('0.00')
    
    # Calcular ganancias y productos vendidos
    detalles = DetalleVenta.objects.filter(
        venta__in=ventas
    ).select_related('producto_variante__producto')
    
    total_ganancias = Decimal('0.00')
    total_productos = 0
    
    for detalle in detalles:
        ganancia = (detalle.precio_unitario - detalle.producto_variante.producto.precio_compra) * detalle.cantidad
        total_ganancias += ganancia
        total_productos += detalle.cantidad
    
    # Top productos más vendidos
    top_productos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    # Productos menos vendidos
    menos_vendidos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('total_vendido')[:10]
    
    # Actualizar análisis
    analisis.total_ventas = total_ventas
    analisis.total_ganancias = total_ganancias
    analisis.total_productos_vendidos = total_productos
    analisis.numero_ventas = num_ventas
    analisis.promedio_venta = promedio_venta
    analisis.venta_mas_alta = venta_mas_alta
    analisis.venta_mas_baja = venta_mas_baja
    analisis.top_productos = json.dumps(list(top_productos))
    analisis.productos_menos_vendidos = json.dumps(list(menos_vendidos))
    analisis.save()


def actualizar_analisis_mensual(analisis):
    """Actualizar los datos de un análisis mensual"""
    from django.db.models import Sum, Avg, Max, Min
    
    ventas = Venta.objects.filter(
        fecha__date__gte=analisis.fecha_inicio,
        fecha__date__lte=analisis.fecha_fin,
        estado='completada'
    )
    
    # Métricas principales
    total_ventas = ventas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    num_ventas = ventas.count()
    
    # Métricas adicionales
    promedio_venta = ventas.aggregate(promedio=Avg('total'))['promedio'] or Decimal('0.00')
    venta_mas_alta = ventas.aggregate(maximo=Max('total'))['maximo'] or Decimal('0.00')
    venta_mas_baja = ventas.aggregate(minimo=Min('total'))['minimo'] or Decimal('0.00')
    
    # Calcular ganancias
    detalles = DetalleVenta.objects.filter(
        venta__in=ventas
    ).select_related('producto_variante__producto')
    
    total_ganancias = Decimal('0.00')
    total_productos = 0
    
    for detalle in detalles:
        ganancia = (detalle.precio_unitario - detalle.producto_variante.producto.precio_compra) * detalle.cantidad
        total_ganancias += ganancia
        total_productos += detalle.cantidad
    
    # Top productos más vendidos
    top_productos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    # Productos menos vendidos
    menos_vendidos = DetalleVenta.objects.filter(
        venta__in=ventas
    ).values(
        'producto_variante__producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('total_vendido')[:10]
    
    # Actualizar análisis
    analisis.total_ventas = total_ventas
    analisis.total_ganancias = total_ganancias
    analisis.total_productos_vendidos = total_productos
    analisis.numero_ventas = num_ventas
    analisis.promedio_venta = promedio_venta
    analisis.venta_mas_alta = venta_mas_alta
    analisis.venta_mas_baja = venta_mas_baja
    analisis.top_productos = json.dumps(list(top_productos))
    analisis.productos_menos_vendidos = json.dumps(list(menos_vendidos))
    analisis.save()
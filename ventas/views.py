from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import json
from datetime import datetime

from almacen.models import Producto, ProductoVariante, Talla
from .models import Venta, DetalleVenta, Devolucion, DetalleDevolucion
from .forms import VentaForm, DetalleVentaForm, DevolucionForm


@login_required
def lista_ventas(request):
    """Lista de todas las ventas con filtros"""
    ventas = Venta.objects.all().select_related('vendedor')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    cliente = request.GET.get('cliente', '')
    folio = request.GET.get('folio', '')
    estado = request.GET.get('estado', '')
    
    if fecha_inicio:
        ventas = ventas.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(fecha__date__lte=fecha_fin)
    if cliente:
        ventas = ventas.filter(cliente__icontains=cliente)
    if folio:
        ventas = ventas.filter(folio__icontains=folio)
    if estado:
        ventas = ventas.filter(estado=estado)
    
    paginator = Paginator(ventas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'cliente': cliente,
        'folio': folio,
        'estado_seleccionado': estado,
        'estados': Venta.ESTADO_CHOICES,
        'total_ventas': ventas.count(),
        'total_monto': ventas.aggregate(total=Sum('total'))['total'] or 0,
    }
    return render(request, 'ventas/lista_ventas.html', context)


@login_required
def nueva_venta(request):
    """Crear una nueva venta con carrito"""
    tallas = Talla.objects.all()
    marcas = Producto.objects.values_list('marca', flat=True).distinct()
    colores = ProductoVariante.objects.values_list('color', flat=True).distinct()
    
    carrito = request.session.get('carrito', [])
    total_carrito = sum(item.get('subtotal', 0) for item in carrito)
    
    if request.method == 'POST':
        cliente = request.POST.get('cliente', '')
        observaciones = request.POST.get('observaciones', '')
        
        if not carrito:
            messages.error(request, 'El carrito está vacío. Agrega productos primero.')
            return redirect('ventas:nueva_venta')
        
        folio = generar_folio()
        venta = Venta.objects.create(
            folio=folio,
            vendedor=request.user,
            cliente=cliente,
            total=total_carrito,
            observaciones=observaciones,
            estado='completada'
        )
        
        for item in carrito:
            variante_id = item.get('variante_id')
            cantidad = item.get('cantidad', 0)
            precio_unitario = item.get('precio_unitario', 0)
            
            if variante_id and cantidad > 0:
                variante = ProductoVariante.objects.get(id=variante_id)
                
                DetalleVenta.objects.create(
                    venta=venta,
                    producto_variante=variante,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=cantidad * precio_unitario
                )
                
                variante.reducir_stock(cantidad)
        
        request.session['carrito'] = []
        request.session.modified = True
        
        messages.success(request, f'Venta #{folio} creada exitosamente.')
        return redirect('ventas:detalle_venta', pk=venta.pk)
    
    context = {
        'carrito': carrito,
        'total_carrito': total_carrito,
        'tallas': tallas,
        'marcas': marcas,
        'colores': colores,
    }
    return render(request, 'ventas/nueva_venta.html', context)


@login_required
def buscar_productos(request):
    """API para buscar productos en tiempo real"""
    query = request.GET.get('q', '')
    talla_id = request.GET.get('talla', '')
    marca = request.GET.get('marca', '')
    color = request.GET.get('color', '')
    
    variantes = ProductoVariante.objects.select_related('producto', 'talla')
    
    if query:
        variantes = variantes.filter(
            Q(producto__nombre__icontains=query) |
            Q(producto__marca__icontains=query) |
            Q(producto__descripcion__icontains=query)
        )
    
    if talla_id:
        variantes = variantes.filter(talla_id=talla_id)
    
    if marca:
        variantes = variantes.filter(producto__marca__icontains=marca)
    
    if color:
        variantes = variantes.filter(color__icontains=color)
    
    # Mostrar solo productos con stock > 0
    variantes = variantes.filter(stock__gt=0)
    
    resultados = []
    for v in variantes[:50]:
        if v.stock <= 0:
            estado = 'agotado'
        elif v.stock <= 5:
            estado = 'poco_stock'
        else:
            estado = 'disponible'
            
        resultados.append({
            'id': v.id,
            'nombre': v.producto.nombre,
            'marca': v.producto.marca or 'Sin marca',
            'talla': v.talla.nombre,
            'color': v.color or 'Sin color',
            'precio': float(v.precio_venta),
            'stock': v.stock,
            'estado_stock': estado,
        })
    
    return JsonResponse({'resultados': resultados})


@login_required
def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all().select_related('producto_variante__producto', 'producto_variante__talla')
    
    context = {
        'venta': venta,
        'detalles': detalles,
    }
    return render(request, 'ventas/detalle_venta.html', context)


@login_required
def anular_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    
    if venta.estado != 'completada':
        messages.error(request, 'Esta venta no puede ser anulada.')
        return redirect('ventas:detalle_venta', pk=pk)
    
    if request.method == 'POST':
        for detalle in venta.detalles.all():
            variante = detalle.producto_variante
            variante.aumentar_stock(detalle.cantidad)
        
        venta.estado = 'anulada'
        venta.save()
        
        messages.success(request, f'Venta #{venta.folio} anulada exitosamente.')
        return redirect('ventas:lista_ventas')
    
    return render(request, 'ventas/anular_venta.html', {'venta': venta})


@login_required
def factura_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all().select_related('producto_variante__producto', 'producto_variante__talla')
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
        'empresa': {
            'nombre': 'KEMA CONSTRUCTORA',
            'telefono': '809-555-1234',
            'direccion': 'Calle Principal #123, Santo Domingo',
        }
    }
    return render(request, 'ventas/factura.html', context)


@login_required
def lista_devoluciones(request):
    devoluciones = Devolucion.objects.all().select_related('venta')
    context = {'devoluciones': devoluciones}
    return render(request, 'ventas/lista_devoluciones.html', context)


@login_required
def nueva_devolucion(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    
    if venta.estado == 'devuelta':
        messages.error(request, 'Esta venta ya fue devuelta completamente.')
        return redirect('ventas:detalle_venta', pk=venta_id)
    
    if venta.estado == 'anulada':
        messages.error(request, 'No se puede devolver una venta anulada.')
        return redirect('ventas:detalle_venta', pk=venta_id)
    
    # Obtener detalles de la venta
    detalles_venta = venta.detalles.all().select_related('producto_variante__producto', 'producto_variante__talla')
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        detalles_seleccionados = request.POST.getlist('detalles[]')
        
        if not detalles_seleccionados:
            messages.error(request, 'Debes seleccionar al menos un producto para devolver.')
            return redirect('ventas:nueva_devolucion', venta_id=venta_id)
        
        # Crear la devolución
        devolucion = Devolucion.objects.create(
            venta=venta,
            motivo=motivo
        )
        
        total_devuelto = Decimal('0.00')
        detalles_a_eliminar = []
        detalles_a_actualizar = []
        
        for detalle_id in detalles_seleccionados:
            detalle = DetalleVenta.objects.get(id=detalle_id)
            cantidad_a_devolver = int(request.POST.get(f'cantidad_{detalle_id}', 0))
            
            # Validar que no se devuelva más de lo que tiene
            if cantidad_a_devolver > 0 and cantidad_a_devolver <= detalle.cantidad:
                # Guardar en la devolución
                DetalleDevolucion.objects.create(
                    devolucion=devolucion,
                    producto_variante=detalle.producto_variante,
                    cantidad=cantidad_a_devolver,
                    precio_unitario=detalle.precio_unitario,
                    subtotal=cantidad_a_devolver * detalle.precio_unitario
                )
                
                # Restaurar stock
                detalle.producto_variante.aumentar_stock(cantidad_a_devolver)
                total_devuelto += cantidad_a_devolver * detalle.precio_unitario
                
                # Decidir qué hacer con el detalle de la venta
                if cantidad_a_devolver >= detalle.cantidad:
                    # Si devuelve TODO, marcar para eliminar
                    detalles_a_eliminar.append(detalle)
                else:
                    # Si devuelve parcial, actualizar cantidad
                    detalle.cantidad -= cantidad_a_devolver
                    detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                    detalles_a_actualizar.append(detalle)
        
        # --- ACTUALIZAR LA VENTA ---
        
        # 1. Eliminar los detalles que se devolvieron completos
        for detalle in detalles_a_eliminar:
            detalle.delete()
        
        # 2. Actualizar los detalles que se devolvieron parcialmente
        for detalle in detalles_a_actualizar:
            detalle.save()
        
        # 3. Guardar total de la devolución
        devolucion.total_devuelto = total_devuelto
        devolucion.save()
        
        # 4. Verificar qué quedó en la venta
        detalles_restantes = venta.detalles.all()
        
        if not detalles_restantes.exists():
            # No quedan productos → venta completamente devuelta
            venta.estado = 'devuelta'
            venta.total = Decimal('0.00')
            venta.save()
            messages.success(request, f'✅ Venta #{venta.folio} devuelta completamente.')
        else:
            # Quedan productos → recalcular total
            nuevo_total = sum(detalle.subtotal for detalle in detalles_restantes)
            venta.total = nuevo_total
            venta.save()
            messages.success(
                request, 
                f'✅ Devolución creada. Total devuelto: ${total_devuelto:.2f}. '
                f'Nuevo total de venta: ${venta.total:.2f}'
            )
        
        return redirect('ventas:detalle_devolucion', pk=devolucion.pk)
    
    context = {
        'venta': venta,
        'detalles_venta': detalles_venta,
    }
    return render(request, 'ventas/nueva_devolucion.html', context)


@login_required
def detalle_devolucion(request, pk):
    devolucion = get_object_or_404(Devolucion, pk=pk)
    detalles = devolucion.detalles.all().select_related('producto_variante__producto', 'producto_variante__talla')
    
    context = {
        'devolucion': devolucion,
        'detalles': detalles,
    }
    return render(request, 'ventas/detalle_devolucion.html', context)


def generar_folio():
    """Generar folio único para la venta"""
    from datetime import datetime
    import random
    
    fecha = datetime.now()
    fecha_str = fecha.strftime('%Y%m%d')
    
    # Buscar la última venta del día
    ultima_venta = Venta.objects.filter(
        folio__startswith=f'V-{fecha_str}-'
    ).order_by('-folio').first()
    
    if ultima_venta:
        try:
            # Extraer el número del folio
            partes = ultima_venta.folio.split('-')
            if len(partes) == 3:
                numero = int(partes[2]) + 1
            else:
                numero = 1
        except (ValueError, IndexError):
            numero = 1
    else:
        numero = 1
    
    # Asegurar que el número tenga 4 dígitos
    return f"V-{fecha_str}-{str(numero).zfill(4)}"


@login_required
def obtener_carrito(request):
    """Obtener el carrito actual de la sesión"""
    carrito = request.session.get('carrito', [])
    return JsonResponse({'carrito': carrito})


@login_required
def agregar_al_carrito(request):
    """Agregar producto al carrito (AJAX)"""
    if request.method == 'POST':
        variante_id = request.POST.get('variante_id')
        cantidad = int(request.POST.get('cantidad', 1))
        precio_editable = request.POST.get('precio_editable', '')
        
        try:
            variante = ProductoVariante.objects.get(id=variante_id)
            
            if variante.stock < cantidad:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente. Disponible: {variante.stock}'
                })
            
            carrito = request.session.get('carrito', [])
            
            # Verificar si ya existe
            encontrado = False
            for item in carrito:
                if item['variante_id'] == int(variante_id):
                    nueva_cantidad = item['cantidad'] + cantidad
                    if variante.stock < nueva_cantidad:
                        return JsonResponse({
                            'success': False,
                            'error': f'Stock insuficiente. Disponible: {variante.stock}'
                        })
                    item['cantidad'] = nueva_cantidad
                    item['subtotal'] = item['cantidad'] * item['precio_unitario']
                    encontrado = True
                    break
            
            if not encontrado:
                precio = float(precio_editable) if precio_editable else float(variante.precio_venta)
                carrito.append({
                    'variante_id': variante.id,
                    'nombre': variante.producto.nombre,
                    'marca': variante.producto.marca or 'Sin marca',
                    'talla': variante.talla.nombre,
                    'color': variante.color or 'Sin color',
                    'cantidad': cantidad,
                    'precio_unitario': precio,
                    'subtotal': cantidad * precio,
                    'stock': variante.stock,
                })
            
            request.session['carrito'] = carrito
            request.session.modified = True
            
            total = sum(item['subtotal'] for item in carrito)
            
            return JsonResponse({
                'success': True,
                'total': total,
                'carrito_count': len(carrito),
                'mensaje': 'Producto agregado al carrito'
            })
            
        except ProductoVariante.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def eliminar_del_carrito(request):
    """Eliminar producto del carrito (AJAX)"""
    if request.method == 'POST':
        variante_id = request.POST.get('variante_id')
        
        carrito = request.session.get('carrito', [])
        carrito = [item for item in carrito if item['variante_id'] != int(variante_id)]
        
        request.session['carrito'] = carrito
        request.session.modified = True
        
        total = sum(item['subtotal'] for item in carrito)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'carrito_count': len(carrito)
        })
    
    return JsonResponse({'success': False})


@login_required
def actualizar_carrito(request):
    """Actualizar cantidad o precio de un producto en el carrito (AJAX)"""
    if request.method == 'POST':
        variante_id = request.POST.get('variante_id')
        cantidad = int(request.POST.get('cantidad', 0))
        precio = request.POST.get('precio', '')
        
        carrito = request.session.get('carrito', [])
        
        for item in carrito:
            if item['variante_id'] == int(variante_id):
                if cantidad > 0:
                    if cantidad > item['stock']:
                        return JsonResponse({
                            'success': False,
                            'error': f'Stock insuficiente. Disponible: {item["stock"]}'
                        })
                    item['cantidad'] = cantidad
                
                if precio:
                    item['precio_unitario'] = float(precio)
                
                item['subtotal'] = item['cantidad'] * item['precio_unitario']
                break
        
        request.session['carrito'] = carrito
        request.session.modified = True
        
        total = sum(item['subtotal'] for item in carrito)
        
        return JsonResponse({
            'success': True,
            'total': total
        })
    
    return JsonResponse({'success': False})
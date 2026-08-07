from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from .models import Categoria, Proveedor, Talla, Producto, ProductoVariante
from .forms import (
    CategoriaForm, ProveedorForm, TallaForm, 
    ProductoForm, ProductoVarianteForm
)
from decimal import Decimal

@login_required
def almacen_dashboard(request):
    """Dashboard del almacén con estadísticas"""
    total_productos = Producto.objects.count()
    total_variantes = ProductoVariante.objects.count()
    stock_bajo = ProductoVariante.objects.filter(stock__lte=5, stock__gt=0).count()
    agotados = ProductoVariante.objects.filter(stock=0).count()
    
    # Productos con poco stock
    productos_poco_stock = ProductoVariante.objects.filter(stock__lte=5).order_by('stock')[:10]
    
    context = {
        'total_productos': total_productos,
        'total_variantes': total_variantes,
        'stock_bajo': stock_bajo,
        'agotados': agotados,
        'productos_poco_stock': productos_poco_stock,
    }
    return render(request, 'almacen/dashboard.html', context)


@login_required
def lista_productos(request):
    """Lista de productos con filtros"""
    productos = Producto.objects.all().prefetch_related('variantes')
    
    # Filtros
    search = request.GET.get('search', '')
    categoria = request.GET.get('categoria', '')
    proveedor = request.GET.get('proveedor', '')
    marca = request.GET.get('marca', '')
    estado_stock = request.GET.get('estado_stock', '')
    
    if search:
        productos = productos.filter(
            Q(nombre__icontains=search) | 
            Q(marca__icontains=search) |
            Q(descripcion__icontains=search)
        )
    
    if categoria:
        productos = productos.filter(categoria_id=categoria)
    
    if proveedor:
        productos = productos.filter(proveedor_id=proveedor)
    
    if marca:
        productos = productos.filter(marca__icontains=marca)
    
    # Calcular stock total para cada producto
    for producto in productos:
        total_stock = producto.variantes.aggregate(total=Sum('stock'))['total'] or 0
        producto.stock_total = total_stock
    
    # Filtrar por estado de stock
    if estado_stock:
        if estado_stock == 'disponible':
            productos = [p for p in productos if p.stock_total > 5]
        elif estado_stock == 'poco_stock':
            productos = [p for p in productos if 0 < p.stock_total <= 5]
        elif estado_stock == 'agotado':
            productos = [p for p in productos if p.stock_total == 0]
    
    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos para filtros
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    marcas = Producto.objects.values_list('marca', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'proveedores': proveedores,
        'marcas': marcas,
        'search': search,
        'categoria_seleccionada': categoria,
        'proveedor_seleccionado': proveedor,
        'marca_seleccionada': marca,
        'estado_stock_seleccionado': estado_stock,
    }
    return render(request, 'almacen/lista_productos.html', context)

@login_required
def crear_producto(request):
    """Crear un nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('almacen:editar_producto', pk=producto.pk)
    else:
        form = ProductoForm()
    
    return render(request, 'almacen/form_producto.html', {'form': form, 'titulo': 'Crear Producto'})

@login_required
def editar_producto(request, pk):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('almacen:lista_productos')
    else:
        form = ProductoForm(instance=producto)
    
    # Obtener variantes del producto
    variantes = producto.variantes.all()
    
    context = {
        'form': form,
        'producto': producto,
        'variantes': variantes,
        'titulo': 'Editar Producto'
    }
    return render(request, 'almacen/editar_producto.html', context)

@login_required
def eliminar_producto(request, pk):
    """Eliminar un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado exitosamente.')
        return redirect('almacen:lista_productos')
    
    return render(request, 'almacen/eliminar_producto.html', {'producto': producto})

@login_required
def detalle_producto(request, pk):
    """Detalle de un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    variantes = producto.variantes.all()
    
    # Estadísticas de stock
    total_stock = variantes.aggregate(total=Sum('stock'))['total'] or 0
    valor_inventario = sum(v.stock * v.precio_venta for v in variantes)
    
    context = {
        'producto': producto,
        'variantes': variantes,
        'total_stock': total_stock,
        'valor_inventario': valor_inventario,
    }
    return render(request, 'almacen/detalle_producto.html', context)

@login_required
def crear_variante(request, producto_id):
    """Crear una variante para un producto"""
    producto = get_object_or_404(Producto, pk=producto_id)
    
    if request.method == 'POST':
        form = ProductoVarianteForm(request.POST)
        if form.is_valid():
            variante = form.save(commit=False)
            variante.producto = producto
            variante.save()
            messages.success(request, f'Variante para "{producto.nombre}" creada exitosamente.')
            return redirect('almacen:editar_producto', pk=producto.pk)
    else:
        form = ProductoVarianteForm()
    
    return render(request, 'almacen/form_variante.html', {
        'form': form,
        'producto': producto,
        'titulo': 'Agregar Variante'
    })

@login_required
def editar_variante(request, pk):
    """Editar una variante"""
    variante = get_object_or_404(ProductoVariante, pk=pk)
    
    if request.method == 'POST':
        form = ProductoVarianteForm(request.POST, instance=variante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variante actualizada exitosamente.')
            return redirect('almacen:editar_producto', pk=variante.producto.pk)
    else:
        form = ProductoVarianteForm(instance=variante)
    
    return render(request, 'almacen/form_variante.html', {
        'form': form,
        'variante': variante,
        'producto': variante.producto,
        'titulo': 'Editar Variante'
    })

@login_required
def eliminar_variante(request, pk):
    """Eliminar una variante"""
    variante = get_object_or_404(ProductoVariante, pk=pk)
    producto_id = variante.producto.pk
    
    if request.method == 'POST':
        variante.delete()
        messages.success(request, 'Variante eliminada exitosamente.')
        return redirect('almacen:editar_producto', pk=producto_id)
    
    return render(request, 'almacen/eliminar_variante.html', {'variante': variante})

# Vistas similares para Categorías, Proveedores y Tallas
@login_required
def lista_categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'almacen/lista_categorias.html', {'categorias': categorias})

@login_required
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('almacen:lista_categorias')
    else:
        form = CategoriaForm()
    return render(request, 'almacen/form_categoria.html', {'form': form, 'titulo': 'Crear Categoría'})

@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('almacen:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'almacen/form_categoria.html', {'form': form, 'titulo': 'Editar Categoría'})

@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('almacen:lista_categorias')
    return render(request, 'almacen/eliminar_categoria.html', {'categoria': categoria})

# Añadir a almacen/views.py

@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'almacen/lista_proveedores.html', {'proveedores': proveedores})

@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('almacen:lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'almacen/form_proveedor.html', {'form': form, 'titulo': 'Crear Proveedor'})

@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('almacen:lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'almacen/form_proveedor.html', {'form': form, 'titulo': 'Editar Proveedor'})

@login_required
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado exitosamente.')
        return redirect('almacen:lista_proveedores')
    return render(request, 'almacen/eliminar_proveedor.html', {'proveedor': proveedor})

@login_required
def lista_tallas(request):
    tallas = Talla.objects.all()
    return render(request, 'almacen/lista_tallas.html', {'tallas': tallas})

@login_required
def crear_talla(request):
    if request.method == 'POST':
        form = TallaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Talla creada exitosamente.')
            return redirect('almacen:lista_tallas')
    else:
        form = TallaForm()
    return render(request, 'almacen/form_talla.html', {'form': form, 'titulo': 'Crear Talla'})

@login_required
def editar_talla(request, pk):
    talla = get_object_or_404(Talla, pk=pk)
    if request.method == 'POST':
        form = TallaForm(request.POST, instance=talla)
        if form.is_valid():
            form.save()
            messages.success(request, 'Talla actualizada exitosamente.')
            return redirect('almacen:lista_tallas')
    else:
        form = TallaForm(instance=talla)
    return render(request, 'almacen/form_talla.html', {'form': form, 'titulo': 'Editar Talla'})

@login_required
def eliminar_talla(request, pk):
    talla = get_object_or_404(Talla, pk=pk)
    if request.method == 'POST':
        talla.delete()
        messages.success(request, 'Talla eliminada exitosamente.')
        return redirect('almacen:lista_tallas')
    return render(request, 'almacen/eliminar_talla.html', {'talla': talla})
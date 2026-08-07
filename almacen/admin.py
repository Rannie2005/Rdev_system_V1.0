from django.contrib import admin
from .models import Categoria, Proveedor, Talla, Producto, ProductoVariante

class ProductoVarianteInline(admin.TabularInline):
    model = ProductoVariante
    extra = 1
    fields = ['talla', 'color', 'precio_venta', 'stock']
    raw_id_fields = ['talla']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'created_at']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'contacto', 'telefono', 'email']
    search_fields = ['nombre', 'contacto']
    list_filter = ['created_at']

@admin.register(Talla)
class TallaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'created_at']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'categoria', 'proveedor', 'precio_compra']
    search_fields = ['nombre', 'marca']
    list_filter = ['categoria', 'proveedor', 'marca']
    inlines = [ProductoVarianteInline]

@admin.register(ProductoVariante)
class ProductoVarianteAdmin(admin.ModelAdmin):
    list_display = ['producto', 'talla', 'color', 'precio_venta', 'stock', 'estado_stock_display']
    list_filter = ['talla', 'producto__categoria']
    search_fields = ['producto__nombre', 'color']
    readonly_fields = ['estado_stock_display']
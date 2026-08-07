from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # Ventas
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),
    path('ventas/detalle/<int:pk>/', views.detalle_venta, name='detalle_venta'),
    path('ventas/anular/<int:pk>/', views.anular_venta, name='anular_venta'),
    path('ventas/factura/<int:pk>/', views.factura_venta, name='factura_venta'),
    
    # API para buscar productos
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'),
    
    # API para el carrito - ¡AGREGAR ESTAS!
    path('agregar-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar-carrito/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar-carrito/', views.actualizar_carrito, name='actualizar_carrito'),
    path('obtener-carrito/', views.obtener_carrito, name='obtener_carrito'), 
    
    # Devoluciones
    path('devoluciones/', views.lista_devoluciones, name='lista_devoluciones'),
    path('devoluciones/nueva/<int:venta_id>/', views.nueva_devolucion, name='nueva_devolucion'),
    path('devoluciones/detalle/<int:pk>/', views.detalle_devolucion, name='detalle_devolucion'),
]
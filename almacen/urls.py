from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'almacen'

urlpatterns = [
    # Dashboard / Inicio
    path('', views.almacen_dashboard, name='dashboard'),
    
    # Categorías
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # Tallas
    path('tallas/', views.lista_tallas, name='lista_tallas'),
    path('tallas/crear/', views.crear_talla, name='crear_talla'),
    path('tallas/editar/<int:pk>/', views.editar_talla, name='editar_talla'),
    path('tallas/eliminar/<int:pk>/', views.eliminar_talla, name='eliminar_talla'),
    
    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/detalle/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    
    # Variantes
    path('variantes/crear/<int:producto_id>/', views.crear_variante, name='crear_variante'),
    path('variantes/editar/<int:pk>/', views.editar_variante, name='editar_variante'),
    path('variantes/eliminar/<int:pk>/', views.eliminar_variante, name='eliminar_variante'),

    path('login/', auth_views.LoginView.as_view(
            template_name='login.html',
            redirect_authenticated_user=True
        ), name='login'),

        path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
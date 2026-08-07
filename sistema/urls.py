from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps
    path('', include('almacen.urls')),
    path('', include('ventas.urls')),
    path('', include('analisis.urls')),
    path('', include('usuarios.urls')),  # ESTA YA INCLUYE LOGIN/LOGOUT
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from .models import Venta, DetalleVenta, Devolucion, DetalleDevolucion

admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Devolucion)
admin.site.register(DetalleDevolucion)

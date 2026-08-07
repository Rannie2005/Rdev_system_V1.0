from django.urls import path
from . import views

app_name = 'analisis'

urlpatterns = [
    path('', views.dashboard_analisis, name='dashboard'),
    path('semanal/', views.analisis_semanal, name='analisis_semanal'),
    path('mensual/', views.analisis_mensual, name='analisis_mensual'),
    path('stock-bajo/', views.reporte_stock_bajo, name='reporte_stock_bajo'),
    path('generar-reportes/', views.generar_reportes, name='generar_reportes'),
]
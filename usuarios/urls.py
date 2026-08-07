from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Opcional: Perfil de usuario
    path('perfil/', views.perfil_view, name='perfil'),
]
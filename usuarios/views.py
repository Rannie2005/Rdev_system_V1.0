from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    """Vista personalizada para iniciar sesión"""
    # Si el usuario ya está autenticado, redirigir al dashboard de almacén
    if request.user.is_authenticated:
        return redirect('almacen:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'almacen:dashboard')  # ← CAMBIADO a almacen:dashboard
        
        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Por favor, intente nuevamente.')
            return render(request, 'login.html', {'next': next_url})
    
    # GET request - mostrar formulario de login
    return render(request, 'login.html')


def logout_view(request):
    """Vista personalizada para cerrar sesión"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('usuarios:login')  # ← CAMBIADO a usuarios:login


# Vista opcional: Perfil de usuario (para futuras mejoras)
@login_required
def perfil_view(request):
    """Vista del perfil de usuario"""
    return render(request, 'usuarios/perfil.html', {'user': request.user})
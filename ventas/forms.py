from django import forms
from .models import Venta, DetalleVenta, Devolucion

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'observaciones']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones'}),
        }

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ['motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motivo de la devolución'}),
        }
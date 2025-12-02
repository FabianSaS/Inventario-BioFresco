from django import forms
from .models import Producto, Movimiento, Lote, Lugar, Contenedor
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'unidad_medida', 'tipo_origen', 'precio_costo', 'precio_venta', 'stock_minimo', 'gestiona_lotes', 'imagen']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 78000123'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'tipo_origen': forms.Select(attrs={'class': 'form-select'}),
            'precio_costo': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'gestiona_lotes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

class MovimientoForm(forms.ModelForm):
    codigo_barra = forms.CharField(
        max_length=50, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Opción A: Escanear código...', 
            'autofocus': 'autofocus',
            'id': 'id_codigo_barra'
        })
    )

    producto_manual = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False, 
        label="Opción B: Buscar Manualmente",
        widget=forms.Select(attrs={'class': 'form-select select2-producto'})
    )

    numero_lote_entrada = forms.CharField(
        max_length=50, 
        required=False, 
        label="N° Lote Proveedor",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: L-2025-001'})
    )

    fecha_vencimiento = forms.DateField(
        required=False,
        label="Fecha de Vencimiento",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    lugar_filtro = forms.ModelChoiceField(
        queryset=Lugar.objects.all(),
        required=False,
        label="1. Zona / Lugar",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_lugar_filtro'})
    )

    contenedor_destino = forms.ModelChoiceField(
        queryset=Contenedor.objects.all().order_by('lugar__nombre', 'nombre'),
        required=False,
        label="2. Contenedor Específico",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_contenedor_destino'})
    )

    class Meta:
        model = Movimiento
        fields = ['tipo', 'cantidad', 'observacion'] 
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_observacion'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        observacion = cleaned_data.get("observacion")
        fecha_venc = cleaned_data.get("fecha_vencimiento")
        lote_input = cleaned_data.get("numero_lote_entrada")
        contenedor = cleaned_data.get("contenedor_destino")
        
        codigo = cleaned_data.get("codigo_barra")
        manual = cleaned_data.get("producto_manual")
        producto = None

        if codigo:
            try:
                producto = Producto.objects.get(codigo=codigo)
            except Producto.DoesNotExist:
                pass 
        elif manual:
            producto = manual

        if not producto:
            raise forms.ValidationError("❌ Debe seleccionar un producto válido.")

        if tipo == 'MERMA':
            if not observacion or not observacion.strip():
                self.add_error('observacion', "⚠️ ES OBLIGATORIO escribir la razón de la merma.")

        if tipo == 'ENTRADA':
            if producto.gestiona_lotes:
                if not fecha_venc:
                    self.add_error('fecha_vencimiento', "⚠️ Fecha requerida.")
                
                if producto.tipo_origen == 'COMPRA':
                    if not lote_input or not lote_input.strip():
                        self.add_error('numero_lote_entrada', "⚠️ Lote requerido para productos de compra.")
                
                if not contenedor:
                    self.add_error('contenedor_destino', "⚠️ Ubicación requerida.")

        return cleaned_data

class LugarForm(forms.ModelForm):
    class Meta:
        model = Lugar
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ContenedorForm(forms.ModelForm):
    class Meta:
        model = Contenedor
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bin 10'}),
            'lugar': forms.Select(attrs={'class': 'form-select'}),
        }

class RegistroEmpleadoForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellido", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol / Cargo",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email'] 
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678-9'}),
        }

class EditarEmpleadoForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellido", required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo", required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(label="¿Usuario Activo?", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Rol / Cargo",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
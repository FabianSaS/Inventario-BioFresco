from django.contrib import admin
from .models import Producto, Lote, Movimiento, Lugar, Contenedor

class LoteInline(admin.TabularInline):
    model = Lote
    extra = 0

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'unidad_medida', 'stock_actual', 'gestiona_lotes')
    search_fields = ('nombre', 'codigo')
    inlines = [LoteInline]

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('producto', 'numero_lote', 'contenedor', 'cantidad', 'fecha_vencimiento')
    list_filter = ('fecha_vencimiento', 'contenedor__lugar') 

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'tipo', 'producto', 'cantidad', 'total_movimiento', 'usuario')
    list_filter = ('tipo', 'fecha')

@admin.register(Lugar)
class LugarAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(Contenedor)
class ContenedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'lugar')
    list_filter = ('lugar',)
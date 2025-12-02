from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Producto(models.Model):
    UNIDADES = (
        ('KG', 'Kilogramos'),
        ('UN', 'Unidades'),
        ('CJ', 'Cajas'),
        ('AT', 'Atados'),
        ('MA', 'Mallas'),
        ('BD', 'Bandejas'),
        ('LT', 'Litros'),
    )
    
    ORIGENES = (
        ('COMPRA', 'Compra / Reventa'),
        ('PROPIO', 'Elaboración Propia'),
    )

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código (Barra/Manual)")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Producto")
    unidad_medida = models.CharField(max_length=2, choices=UNIDADES, default='KG', verbose_name="Formato")
    tipo_origen = models.CharField(max_length=10, choices=ORIGENES, default='COMPRA', verbose_name="Origen")
    descripcion = models.TextField(blank=True, null=True)
    
    precio_costo = models.IntegerField(verbose_name="Precio Costo (Compra)")
    precio_venta = models.IntegerField(verbose_name="Precio Venta (Público)")
    stock_minimo = models.PositiveIntegerField(default=10, verbose_name="Alerta Stock Mínimo")
    gestiona_lotes = models.BooleanField(default=True, verbose_name="¿Requiere Lotes y Vencimiento?")

    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def stock_actual(self):
        if not self.gestiona_lotes:
            entradas = self.movimiento_set.filter(tipo='ENTRADA').aggregate(total=models.Sum('cantidad'))['total'] or 0
            salidas = self.movimiento_set.filter(tipo__in=['VENTA', 'MERMA']).aggregate(total=models.Sum('cantidad'))['total'] or 0
            
            return entradas - salidas
        
        return self.lote_set.aggregate(total=models.Sum('cantidad'))['total'] or 0

    @property
    def proximo_vencimiento(self):
        if not self.gestiona_lotes:
            return None
        lote_mas_cercano = self.lote_set.filter(cantidad__gt=0).order_by('fecha_vencimiento').first()
        if lote_mas_cercano:
            return lote_mas_cercano.fecha_vencimiento
        return None

class Lugar(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Lugar")
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Contenedor(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Identificador del Contenedor")
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE, related_name='contenedores', verbose_name="Ubicado en")
    
    class Meta:
        unique_together = ('nombre', 'lugar')

    def __str__(self):
        return f"{self.nombre} ({self.lugar.nombre})"

class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    numero_lote = models.CharField(max_length=50, blank=True, null=True, verbose_name="# Lote Proveedor")
    fecha_vencimiento = models.DateField(verbose_name="Fecha Vencimiento")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Actual")
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    
    contenedor = models.ForeignKey(Contenedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ubicación Física")

    class Meta:
        ordering = ['fecha_vencimiento']

    def __str__(self):
        ubicacion = self.contenedor.nombre if self.contenedor else "Sin Asignar"
        return f"Lote {self.numero_lote} - {self.producto.nombre} en {ubicacion}"
    
    @property
    def estado_alerta(self):
        hoy = timezone.localdate()
        if self.fecha_vencimiento < hoy: return 'VENCIDO'
        if self.fecha_vencimiento == hoy: return 'HOY'
        delta = self.fecha_vencimiento - hoy
        if delta.days <= 7: return 'CRITICO'
        return 'OK'

class Movimiento(models.Model):
    TIPOS = (
        ('ENTRADA', 'Entrada de Stock'),
        ('VENTA', 'Venta (Salida)'),
        ('MERMA', 'Merma (Pérdida)'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    
    tipo = models.CharField(max_length=20, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    precio_unitario_snapshot = models.IntegerField(verbose_name="Precio al momento")
    total_movimiento = models.IntegerField(editable=False, verbose_name="Total ($)")

    observacion = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_movimiento = self.cantidad * self.precio_unitario_snapshot
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre}"
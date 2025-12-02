from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, ProtectedError, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Producto, Lote, Movimiento, Lugar, Contenedor
from .forms import (
    MovimientoForm, ProductoForm, RegistroEmpleadoForm, 
    EditarEmpleadoForm, LugarForm, ContenedorForm
)
import csv
from django.http import HttpResponse
from datetime import timedelta

def es_bodeguero(user):
    return user.groups.filter(name='Bodeguero').exists() or user.is_superuser

def es_admin_bodega(user):
    return user.groups.filter(name='Administrador').exists() or user.groups.filter(name='Gerente').exists() or user.is_superuser

def es_gerente(user):
    return user.groups.filter(name='Gerente').exists() or user.is_superuser

@login_required
def home_redirect(request):
    user = request.user
    if es_bodeguero(user) and not es_admin_bodega(user):
        return redirect('dashboard_bodega')
    elif user.groups.filter(name='Administrador').exists():
        return redirect('dashboard_operativo')
    elif es_gerente(user):
        return redirect('dashboard_gerencia')
    return redirect('dashboard_operativo')

@login_required
def dashboard_bodega(request):
    if not (request.user.groups.filter(name='Bodeguero').exists() or request.user.is_superuser):
        return redirect('home')
    return render(request, 'bodega/dashboard.html')

@login_required
@user_passes_test(es_gerente, login_url='home')
def dashboard_gerencia(request):
    productos = Producto.objects.all()
    productos_bajo_stock = [p for p in productos if p.stock_actual <= p.stock_minimo]
    total_ventas = Movimiento.objects.filter(tipo='VENTA').aggregate(Sum('total_movimiento'))['total_movimiento__sum'] or 0
    total_mermas = Movimiento.objects.filter(tipo='MERMA').aggregate(Sum('total_movimiento'))['total_movimiento__sum'] or 0
    ganancia_neta = total_ventas - total_mermas
    ultimos_colaboradores = User.objects.filter(is_superuser=False).order_by('-date_joined')[:5]

    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'total_ventas': total_ventas,
        'total_mermas': total_mermas,
        'ganancia_neta': ganancia_neta,
        'ultimos_colaboradores': ultimos_colaboradores,
    }
    return render(request, 'gerencia/dashboard.html', context)

@login_required
@user_passes_test(es_gerente, login_url='home')
def historial_movimientos(request):
    movimientos = Movimiento.objects.all().order_by('-fecha')
    busqueda = request.GET.get('buscar')
    if busqueda:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=busqueda) |
            Q(producto__codigo__icontains=busqueda) |
            Q(tipo__icontains=busqueda)
        )
    return render(request, 'gerencia/historial.html', {'movimientos': movimientos})

@login_required
@user_passes_test(es_gerente, login_url='home')
def exportar_historial_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="historial_movimientos.csv"'
    response.write(u'\ufeff'.encode('utf8')) 
    writer = csv.writer(response, delimiter=';') 
    writer.writerow(['ID', 'Fecha', 'Hora', 'Tipo', 'Producto', 'SKU', 'Cantidad', 'Unidad', 'Usuario', 'Total ($)', 'Observación', 'Lote', 'Vencimiento'])
    movimientos = Movimiento.objects.all().order_by('-fecha')
    for m in movimientos:
        fecha_str = m.fecha.strftime("%d/%m/%Y")
        hora_str = m.fecha.strftime("%H:%M")
        lote_str = m.lote.numero_lote if m.lote else "N/A"
        venc_str = m.lote.fecha_vencimiento.strftime("%d/%m/%Y") if m.lote else "N/A"
        writer.writerow([m.id, fecha_str, hora_str, m.tipo, m.producto.nombre, m.producto.codigo, m.cantidad, m.producto.get_unidad_medida_display(), m.usuario.username, m.total_movimiento, m.observacion, lote_str, venc_str])
    return response

@login_required
@user_passes_test(es_gerente, login_url='home')
def lista_colaboradores(request):
    colaboradores = User.objects.filter(is_superuser=False)
    return render(request, 'gerencia/colaboradores.html', {'colaboradores': colaboradores})

@login_required
def crear_colaborador(request):
    if request.method == 'POST':
        form = RegistroEmpleadoForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.groups.add(form.cleaned_data['grupo'])
            if form.cleaned_data['grupo'].name == 'Gerente':
                user.is_staff = True
                user.save()
            messages.success(request, "Colaborador creado.")
            return redirect('lista_colaboradores')
    else:
        form = RegistroEmpleadoForm()
    return render(request, 'gerencia/crear_colaborador.html', {'form': form})

@login_required
def editar_colaborador(request, pk):
    colaborador = get_object_or_404(User, pk=pk)
    grupo_actual = colaborador.groups.first()
    if request.method == 'POST':
        form = EditarEmpleadoForm(request.POST, instance=colaborador)
        if form.is_valid():
            user = form.save()
            ng = form.cleaned_data['grupo']
            if grupo_actual != ng:
                user.groups.clear(); user.groups.add(ng)
                user.is_staff = (ng.name == 'Gerente')
                user.save()
            messages.success(request, "Actualizado.")
            return redirect('lista_colaboradores')
    else:
        form = EditarEmpleadoForm(instance=colaborador, initial={'grupo': grupo_actual})
    return render(request, 'gerencia/crear_colaborador.html', {'form': form, 'es_edicion': True})

@login_required
def eliminar_colaborador(request, pk):
    colaborador = get_object_or_404(User, pk=pk)
    if colaborador == request.user: return redirect('lista_colaboradores')
    if request.method == 'POST':
        try:
            colaborador.delete()
            messages.success(request, "Eliminado.")
        except ProtectedError:
            messages.error(request, "No se puede eliminar (tiene historial).")
        return redirect('lista_colaboradores')
    return render(request, 'gerencia/confirmar_eliminar_usuario.html', {'colaborador': colaborador})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def dashboard_operativo(request):
    lotes_vencidos = Lote.objects.filter(cantidad__gt=0, fecha_vencimiento__lte=timezone.now().date()).count()
    lotes_por_vencer = Lote.objects.filter(cantidad__gt=0, fecha_vencimiento__lte=timezone.now().date() + timezone.timedelta(days=7)).count()
    total_contenedores = Contenedor.objects.count()
    contenedores_usados = Lote.objects.filter(cantidad__gt=0).values('contenedor').distinct().count()
    ocupacion = int((contenedores_usados / total_contenedores * 100)) if total_contenedores > 0 else 0
    movimientos_hoy = Movimiento.objects.filter(fecha__date=timezone.now().date()).count()

    context = {
        'lotes_vencidos': lotes_vencidos,
        'lotes_por_vencer': lotes_por_vencer,
        'ocupacion': ocupacion,
        'movimientos_hoy': movimientos_hoy,
    }
    return render(request, 'administracion/dashboard.html', context)

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def procesar_vencimientos(request):
    manana = timezone.now().date() + timezone.timedelta(days=1)
    lotes_vencidos = Lote.objects.filter(fecha_vencimiento__lt=manana, cantidad__gt=0)
    cantidad_procesada = 0
    if not lotes_vencidos.exists():
        messages.info(request, "No hay lotes vencidos pendientes de baja.")
        return redirect('dashboard_operativo')

    for lote in lotes_vencidos:
        cantidad_a_bajar = lote.cantidad
        producto = lote.producto
        Movimiento.objects.create(
            producto=producto, lote=lote, usuario=request.user, tipo='MERMA',
            cantidad=cantidad_a_bajar, precio_unitario_snapshot=producto.precio_costo,
            observacion=f"BAJA AUTOMÁTICA POR VENCIMIENTO (Venció el {lote.fecha_vencimiento})"
        )
        lote.cantidad = 0
        lote.save()
        cantidad_procesada += 1

    messages.warning(request, f"¡Listo! Se dieron de baja {cantidad_procesada} lotes.")
    return redirect('dashboard_operativo')

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def lista_productos(request):
    busqueda = request.GET.get('buscar')
    productos = Producto.objects.all().order_by('nombre')
    if busqueda:
        productos = productos.filter(Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda))
    return render(request, 'administracion/catalogo.html', {'productos': productos})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado.")
            return redirect('catalogo')
    else:
        form = ProductoForm()
    return render(request, 'administracion/producto_form.html', {'form': form})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if not request.user.is_staff: return redirect('catalogo')
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Actualizado.")
            return redirect('catalogo')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'administracion/producto_form.html', {'form': form, 'es_edicion': True})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if not request.user.is_staff: return redirect('catalogo')
    if request.method == 'POST':
        try:
            producto.delete()
            messages.success(request, "Eliminado.")
            return redirect('catalogo')
        except ProtectedError:
            messages.error(request, "Tiene historial, no se puede borrar.")
            return redirect('catalogo')
    return render(request, 'administracion/confirmar_eliminar_producto.html', {'producto': producto})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def gestion_bodega(request):
    lugares = Lugar.objects.all()
    if request.method == 'POST':
        form = LugarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lugar creado.")
            return redirect('gestion_bodega')
    else:
        form = LugarForm()
    return render(request, 'mapa/mapa_gestion.html', {'lugares': lugares, 'form': form})

@login_required
@user_passes_test(es_admin_bodega, login_url='home')
def detalle_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, pk=lugar_id)
    contenedores = lugar.contenedores.all()
    proximo_lote_vencer = Lote.objects.filter(contenedor__lugar=lugar, cantidad__gt=0).order_by('fecha_vencimiento').first()
    if request.method == 'POST':
        form = ContenedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contenedor agregado.")
            return redirect('detalle_lugar', lugar_id=lugar.id)
    else:
        form = ContenedorForm(initial={'lugar': lugar})
    return render(request, 'mapa/detalle_lugar.html', {'lugar': lugar, 'contenedores': contenedores, 'form': form, 'proximo_lote_vencer': proximo_lote_vencer})

@login_required
def inventario_contenedor(request, contenedor_id):
    contenedor = get_object_or_404(Contenedor, pk=contenedor_id)
    lotes_en_contenedor = Lote.objects.filter(contenedor=contenedor, cantidad__gt=0).order_by('fecha_vencimiento')
    return render(request, 'mapa/inventario_contenedor.html', {'contenedor': contenedor, 'lotes': lotes_en_contenedor, 'today': timezone.now().date()})
@login_required
def reporte_ubicaciones(request):
    if not (request.user.is_staff or 
            request.user.groups.filter(name='Bodeguero').exists() or 
            request.user.groups.filter(name='Administrador').exists()): 
        return redirect('home')
    
    lotes_activos = Lote.objects.filter(cantidad__gt=0).order_by('producto__nombre', 'fecha_vencimiento')
    
    busqueda = request.GET.get('buscar')
    if busqueda:
        lotes_activos = lotes_activos.filter(
            Q(producto__nombre__icontains=busqueda) |
            Q(numero_lote__icontains=busqueda) |
            Q(contenedor__nombre__icontains=busqueda) |
            Q(contenedor__lugar__nombre__icontains=busqueda)
        )

    hoy = timezone.now().date()
    proxima_semana = hoy + timedelta(days=7)

    return render(request, 'administracion/reporte_ubicaciones.html', {
        'lotes': lotes_activos, 
        'hoy': hoy,
        'proxima_semana': proxima_semana
    })

@login_required
def exportar_ubicaciones_csv(request):
    if not (request.user.is_staff or 
            request.user.groups.filter(name='Bodeguero').exists() or 
            request.user.groups.filter(name='Administrador').exists()): 
        return redirect('home')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_stock_ubicaciones.csv"'
    response.write(u'\ufeff'.encode('utf8')) 

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Producto', 'Código SKU', 'N° Lote', 'Vencimiento', 'Cantidad', 'Unidad', 'Ubicación (Contenedor)', 'Zona (Lugar)'])

    lotes = Lote.objects.filter(cantidad__gt=0).order_by('producto__nombre')

    for lote in lotes:
        ubicacion = lote.contenedor.nombre if lote.contenedor else "Sin Asignar"
        zona = lote.contenedor.lugar.nombre if lote.contenedor and lote.contenedor.lugar else "-"
        
        writer.writerow([
            lote.producto.nombre,
            lote.producto.codigo,
            lote.numero_lote,
            lote.fecha_vencimiento.strftime("%d/%m/%Y"),
            lote.cantidad,
            lote.producto.get_unidad_medida_display(),
            ubicacion,
            zona
        ])

    return response
@login_required
def registrar_movimiento(request):
    initial_data = {}
    if request.method == 'GET':
        codigo_pre = request.GET.get('codigo')
        accion_pre = request.GET.get('accion')
        if codigo_pre: initial_data['codigo_barra'] = codigo_pre
        if accion_pre: initial_data['tipo'] = accion_pre

    if request.method == 'POST':
        form = MovimientoForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data.get('codigo_barra')
            producto_manual = form.cleaned_data.get('producto_manual')
            tipo = form.cleaned_data['tipo']
            cantidad = form.cleaned_data['cantidad']
            observacion = form.cleaned_data.get('observacion') or ""
            numero_lote_input = form.cleaned_data.get('numero_lote_entrada')
            fecha_vencimiento_input = form.cleaned_data.get('fecha_vencimiento')
            contenedor_destino = form.cleaned_data.get('contenedor_destino')

            if tipo == 'MERMA' and len(observacion.strip()) < 5:
                messages.error(request, "⛔ Escriba razón de merma obligatoria.")
                return redirect('registrar_movimiento')

            producto = None
            if codigo:
                try: producto = Producto.objects.get(codigo=codigo)
                except Producto.DoesNotExist:
                    messages.error(request, "No existe producto.")
                    return redirect('registrar_movimiento')
            elif producto_manual: producto = producto_manual

            precio_snapshot = producto.precio_venta if tipo == 'VENTA' else producto.precio_costo

            if tipo == 'ENTRADA':
                if producto.gestiona_lotes:
                    Lote.objects.create(
                        producto=producto, cantidad=cantidad, numero_lote=numero_lote_input,
                        fecha_vencimiento=fecha_vencimiento_input, contenedor=contenedor_destino
                    )
                    ubicacion_str = f"en {contenedor_destino}" if contenedor_destino else ""
                else:
                    ubicacion_str = "(Flujo Rápido)"

                Movimiento.objects.create(
                    producto=producto, usuario=request.user, tipo=tipo, cantidad=cantidad,
                    precio_unitario_snapshot=precio_snapshot, observacion=observacion
                )
                messages.success(request, f"Entrada OK: {cantidad} {producto.get_unidad_medida_display()} {ubicacion_str}.")

            else:
                if producto.stock_actual < cantidad:
                    messages.error(request, "Stock insuficiente.")
                    return redirect('registrar_movimiento')

                cantidad_pendiente = cantidad
                lotes_activos = Lote.objects.filter(producto=producto, cantidad__gt=0).order_by('fecha_vencimiento')
                
                if not lotes_activos.exists() and producto.gestiona_lotes:
                     messages.error(request, "Error crítico: Sin lotes físicos.")
                     return redirect('registrar_movimiento')

                for lote in lotes_activos:
                    if cantidad_pendiente == 0: break
                    if lote.cantidad >= cantidad_pendiente:
                        lote.cantidad -= cantidad_pendiente
                        lote.save()
                        Movimiento.objects.create(
                            producto=producto, lote=lote, usuario=request.user, tipo=tipo,
                            cantidad=cantidad_pendiente, precio_unitario_snapshot=precio_snapshot, observacion=observacion
                        )
                        cantidad_pendiente = 0
                    else:
                        consumido = lote.cantidad
                        lote.cantidad = 0
                        lote.save()
                        Movimiento.objects.create(
                            producto=producto, lote=lote, usuario=request.user, tipo=tipo,
                            cantidad=consumido, precio_unitario_snapshot=precio_snapshot, observacion=observacion
                        )
                        cantidad_pendiente -= consumido
                
                if not producto.gestiona_lotes:
                     Movimiento.objects.create(
                         producto=producto, usuario=request.user, tipo=tipo, 
                         cantidad=cantidad, precio_unitario_snapshot=precio_snapshot, observacion=observacion
                     )

                messages.success(request, f"{tipo} registrada correctamente.")
            return redirect('registrar_movimiento')
    else:
        form = MovimientoForm(initial=initial_data)
    return render(request, 'bodega/movimiento.html', {'form': form})
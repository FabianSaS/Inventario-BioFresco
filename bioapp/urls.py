from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('gerencia/dashboard/', views.dashboard_gerencia, name='dashboard_gerencia'),
    path('gerencia/historial/', views.historial_movimientos, name='historial_movimientos'),
    path('gerencia/exportar/', views.exportar_historial_csv, name='exportar_historial'),
    path('gerencia/equipo/', views.lista_colaboradores, name='lista_colaboradores'),
    path('gerencia/equipo/nuevo/', views.crear_colaborador, name='crear_colaborador'),
    path('gerencia/equipo/editar/<int:pk>/', views.editar_colaborador, name='editar_colaborador'),
    path('gerencia/equipo/eliminar/<int:pk>/', views.eliminar_colaborador, name='eliminar_colaborador'),
    path('administracion/dashboard/', views.dashboard_operativo, name='dashboard_operativo'),
    path('administracion/procesar-vencidos/', views.procesar_vencimientos, name='procesar_vencimientos'),
    path('administracion/catalogo/', views.lista_productos, name='catalogo'),
    path('administracion/producto/nuevo/', views.crear_producto, name='gestionar_productos'),
    path('administracion/producto/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('administracion/producto/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('administracion/reporte-ubicaciones/', views.reporte_ubicaciones, name='reporte_ubicaciones'),
    path('administracion/reporte-ubicaciones/exportar/', views.exportar_ubicaciones_csv, name='exportar_ubicaciones'),
    path('mapa/', views.gestion_bodega, name='gestion_bodega'),
    path('mapa/lugar/<int:lugar_id>/', views.detalle_lugar, name='detalle_lugar'),
    path('mapa/contenedor/<int:contenedor_id>/', views.inventario_contenedor, name='inventario_contenedor'),
    path('bodega/dashboard/', views.dashboard_bodega, name='dashboard_bodega'),
    path('bodega/movimiento/', views.registrar_movimiento, name='registrar_movimiento'),
    path('salir/', auth_views.LogoutView.as_view(), name='exit'),
]
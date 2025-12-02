# BioFresco - Sistema de Gestión de Bodega (WMS)

Sistema integral de gestión de inventario y trazabilidad desarrollado en **Django**, diseñado para optimizar el flujo de productos perecederos con control de caducidad y ubicaciones dinámicas.

## Características Principales

### Gestión de Inventario Avanzada
- **Control FIFO (First In, First Out):** El sistema prioriza automáticamente la salida de lotes más antiguos (regla esencial para perecederos).
- **Control de Lotes Dinámico:** La ubicación (Contenedor/Lugar) se asigna en la entrada del stock, permitiendo que el mismo producto esté en múltiples ubicaciones.
- **Flujos Simplificados:** El sistema diferencia entre productos de Compra/Reventa (exige lote de proveedor) y Elaboración Propia (genera lote interno automático).
- **Manejo de Errores:** Validación estricta en mermas (razón obligatoria) y bloqueo de stock negativo/lotes inexistentes.

### Mapeo WMS (Warehouse Management System)
- **Estructura Escalable:** Gestión dinámica de **Lugares** (Zonas) y **Contenedores** (Bins), lo que permite la expansión futura de la bodega.
- **Trazabilidad Lote/Ubicación:** Informe que muestra exactamente qué lote está en qué contenedor.

### Automatización y Alertas
- **Proceso de Baja Automática:** Botón de pánico para dar de baja masivamente productos vencidos (cierra el ciclo de Merma financiera).
- **Dashboards Ejecutivos:** Separación de KPIs financieros (Gerencia) y operativos (Administrador).
- **Reportes:** Exportación de historial y reportes de stock a **Excel/CSV**.

### Arquitectura de Roles (RBAC)
- **Gerente:** Finanzas, RRHH y Reportes Estratégicos.
- **Administrador de Bodega:** Gestión de Catálogo, Precios, y Configuración del Mapa WMS.
- **Bodeguero:** Interfaz simplificada para operación de entrada/salida/merma.

## Stack Tecnológico

- **Backend:** Python, Django 5.
- **Base de Datos:** MariaDB (MySQL).
- **Frontend:** HTML5, Bootstrap 5, JavaScript (Select2, Chart.js).


## Instalación y Uso

1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`.
3. Crear la base de datos `BIOFRESCO` en MariaDB y configurar las credenciales.
4. Ejecutar migraciones (`python manage.py migrate`).
5. Crear superusuario y asignar roles a usuarios de prueba.
6. Iniciar servidor: `python manage.py runserver`.

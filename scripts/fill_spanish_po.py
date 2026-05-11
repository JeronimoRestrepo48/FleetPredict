#!/usr/bin/env python3
"""
Fill Spanish msgstr entries in locale/es/LC_MESSAGES/django.po (stdlib only).
Run from repo dev/:  python scripts/fill_spanish_po.py
"""
from __future__ import annotations

import pathlib
import re

import polib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PO_PATH = ROOT / "locale" / "es" / "LC_MESSAGES" / "django.po"

# msgid -> msgstr (Spanish). Multiline msgids are handled separately below.
ES: dict[str, str] = {
    "Maintenance due within (days)": "Mantenimiento próximo a vencer (días)",
    "Maintenance overdue alert": "Alerta de mantenimiento vencido",
    "Compliance expiring within (days)": "Cumplimiento por vencer (días)",
    "Work orders due within (days)": "Órdenes de trabajo por vencer (días)",
    "Engine temperature (°C)": "Temperatura del motor (°C)",
    "Fuel level (%)": "Nivel de combustible (%)",
    "Speed (km/h)": "Velocidad (km/h)",
    "Engine RPM": "RPM del motor",
    "Mileage (km)": "Kilometraje (km)",
    "Battery voltage (V)": "Voltaje de batería (V)",
    "Throttle position (%)": "Posición del acelerador (%)",
    "≥ (greater or equal)": "≥ (mayor o igual)",
    "≤ (less or equal)": "≤ (menor o igual)",
    "> (greater)": "> (mayor)",
    "< (less)": "< (menor)",
    "Low": "Bajo",
    "Medium": "Medio",
    "High": "Alto",
    "Critical": "Crítico",
    "Create": "Crear",
    "Update": "Actualizar",
    "Delete": "Eliminar",
    "Login": "Iniciar sesión",
    "Logout": "Cerrar sesión",
    "Export": "Exportar",
    "Override": "Anular",
    "System event": "Evento del sistema",
    "Vehicle Count": "Cantidad de vehículos",
    "Status Summary": "Resumen por estado",
    "Recent Alerts": "Alertas recientes",
    "Upcoming Maintenance": "Mantenimiento próximo",
    "Health Overview": "Resumen de salud",
    "Cost Summary": "Resumen de costos",
    "Maintenance Trend Chart": "Gráfico de tendencia de mantenimiento",
    "Alerts by Type Chart": "Gráfico de alertas por tipo",
    "Compliance Status": "Estado de cumplimiento",
    "Task Priority": "Prioridad de tareas",
    "Small (4 cols)": "Pequeño (4 columnas)",
    "Medium (6 cols)": "Mediano (6 columnas)",
    "Large (12 cols)": "Grande (12 columnas)",
    "Unknown": "Desconocido",
    "No vehicles in the fleet yet. Add vehicles to start tracking.": "Aún no hay vehículos en la flota. Agrega vehículos para comenzar a monitorear.",
    "{available} of {total} vehicles active": "{available} de {total} vehículos activos",
    "{pct:.0f}% availability": "{pct:.0f}% de disponibilidad",
    "{count} upcoming in 7 days": "{count} próximos en 7 días",
    "{count} tasks need attention": "{count} tareas requieren atención",
    "Missing alert or runbook.": "Falta la alerta o el runbook.",
    "You do not have access to this alert.": "No tienes acceso a esta alerta.",
    "This runbook does not apply to this alert type.": "Este runbook no aplica a este tipo de alerta.",
    "Action failed.": "La acción falló.",
    "Invalid criticality level.": "Nivel de criticidad no válido.",
    "A reason is required to override criticality.": "Se requiere un motivo para anular la criticidad.",
    "Criticality updated and audited.": "Criticidad actualizada y auditada.",
    "Missing alert.": "Falta la alerta.",
    "Not allowed.": "No permitido.",
    "Suggestion already handled.": "La sugerencia ya fue gestionada.",
    "Dismissed maintenance suggestion": "Sugerencia de mantenimiento descartada",
    "Suggestion dismissed.": "Sugerencia descartada.",
    "Rule not found.": "Regla no encontrada.",
    "Alert rule created.": "Regla de alerta creada.",
    "All alert rule types are already configured.": "Todos los tipos de reglas de alerta ya están configurados.",
    "Alert rule updated.": "Regla de alerta actualizada.",
    "Threshold created.": "Umbral creado.",
    "Threshold updated.": "Umbral actualizado.",
    "Threshold deleted.": "Umbral eliminado.",
    "Invalid JSON": "JSON no válido",
    "Dashboard reset to default layout.": "Panel restablecido al diseño predeterminado.",
    "Engine": "Motor",
    "Brakes": "Frenos",
    "Tires": "Neumáticos",
    "Electrical": "Eléctrico",
    "Transmission": "Transmisión",
    "Suspension": "Suspensión",
    "Fluids & Filters": "Fluidos y filtros",
    "Body & Exterior": "Carrocería y exterior",
    "Other": "Otro",
    "Stock In": "Entrada de stock",
    "Stock Out": "Salida de stock",
    "Adjustment": "Ajuste",
    "Spare part created.": "Repuesto creado.",
    "Spare part updated.": "Repuesto actualizado.",
    "Supplier review saved.": "Reseña del proveedor guardada.",
    "Please provide a valid rating between 1 and 5.": "Indica una calificación válida entre 1 y 5.",
    "Supplier created.": "Proveedor creado.",
    "Supplier updated.": "Proveedor actualizado.",
    "Preventive": "Preventivo",
    "Corrective": "Correctivo",
    "Inspection": "Inspección",
    "Emergency": "Emergencia",
    "Scheduled": "Programado",
    "In Progress": "En curso",
    "Completed": "Completado",
    "Cancelled": "Cancelado",
    "Overdue": "Vencido",
    "Open": "Abierto",
    "Maintenance task created successfully.": "Tarea de mantenimiento creada correctamente.",
    "Cannot modify completed or cancelled tasks.": "No se pueden modificar tareas completadas o canceladas.",
    "Maintenance task updated successfully.": "Tarea de mantenimiento actualizada correctamente.",
    "Cannot delete completed tasks.": "No se pueden eliminar tareas completadas.",
    "Maintenance task deleted successfully.": "Tarea de mantenimiento eliminada correctamente.",
    "Task is already completed.": "La tarea ya está completada.",
    "Maintenance task completed successfully.": "Tarea de mantenimiento completada correctamente.",
    "No file provided.": "No se proporcionó ningún archivo.",
    "File size exceeds 10MB limit.": "El archivo supera el límite de 10 MB.",
    "Document uploaded successfully.": "Documento subido correctamente.",
    "Maintenance template created successfully.": "Plantilla de mantenimiento creada correctamente.",
    "Template updated successfully.": "Plantilla actualizada correctamente.",
    "Template deleted.": "Plantilla eliminada.",
    "Work order created successfully.": "Orden de trabajo creada correctamente.",
    "Completed work orders cannot be modified.": "Las órdenes de trabajo completadas no se pueden modificar.",
    "Work order updated.": "Orden de trabajo actualizada.",
    "Report schedule requires a name and report type.": "El programa de reportes requiere un nombre y un tipo de reporte.",
    "Report schedule saved.": "Programa de reportes guardado.",
    "Invalid export dataset.": "Conjunto de exportación no válido.",
    "Planning": "Planificación",
    "Selected": "Seleccionado",
    "Shortest distance": "Distancia más corta",
    "Fastest time": "Menor tiempo",
    "Lowest fuel cost": "Menor costo de combustible",
    "Administrator": "Administrador",
    "Fleet Manager": "Gestor de flota",
    "Mechanic": "Mecánico",
    "Driver": "Conductor",
    "Registration successful. You can now log in.": "Registro exitoso. Ya puedes iniciar sesión.",
    "Active": "Activo",
    "Inactive": "Inactivo",
    "Under Maintenance": "En mantenimiento",
    "Retired": "Retirado",
    "High engine temperature": "Temperatura alta del motor",
    "Anomalous fuel consumption": "Consumo anómalo de combustible",
    "Harsh driving": "Conducción brusca",
    "Prolonged idling": "Ralentí prolongado",
    "Maintenance due by mileage": "Mantenimiento por kilometraje",
    "Maintenance due by time": "Mantenimiento por tiempo",
    "Statistical anomaly": "Anomalía estadística",
    "Custom threshold exceeded": "Umbral personalizado superado",
    "Pending": "Pendiente",
    "Accepted": "Aceptado",
    "Dismissed": "Descartado",
    "Mark alert as read": "Marcar alerta como leída",
    "Create maintenance task": "Crear tarea de mantenimiento",
    "Dismiss alert": "Descartar alerta",
    "Alert marked as read.": "Alerta marcada como leída.",
    "Alert dismissed.": "Alerta descartada.",
    "Unknown action type.": "Tipo de acción desconocido.",
    "Certification": "Certificación",
    "License": "Licencia",
    "Registration": "Matriculación",
    "Insurance": "Seguro",
    "Temperature (C)": "Temperatura (C)",
    "Vibration (mm/s)": "Vibración (mm/s)",
    "Pressure (PSI)": "Presión (PSI)",
    "Oil Level (%)": "Nivel de aceite (%)",
    "Battery Voltage (V)": "Voltaje de batería (V)",
    "Tire Pressure (PSI)": "Presión de neumáticos (PSI)",
    "API": "API",
    "CSV Upload": "Carga CSV",
    "Manual Entry": "Entrada manual",
    "Vehicle created successfully.": "Vehículo creado correctamente.",
    "Vehicle updated successfully.": "Vehículo actualizado correctamente.",
    "Vehicle deleted successfully.": "Vehículo eliminado correctamente.",
    "Vehicle type created successfully.": "Tipo de vehículo creado correctamente.",
    "Vehicle type updated successfully.": "Tipo de vehículo actualizado correctamente.",
    "Cannot delete: some vehicles use this type. Reassign them first.": "No se puede eliminar: algunos vehículos usan este tipo. Reasígnalos primero.",
    "Vehicle type deleted.": "Tipo de vehículo eliminado.",
    "Compliance requirement added.": "Requisito de cumplimiento agregado.",
    "Compliance requirement updated.": "Requisito de cumplimiento actualizado.",
    "Compliance requirement removed.": "Requisito de cumplimiento eliminado.",
    "Sensor reading added.": "Lectura de sensor agregada.",
    "English": "Inglés",
    "Spanish": "Español",
    "FleetPredict Pro": "FleetPredict Pro",
    "FleetPredict Pro – Predictive fleet maintenance and vehicle management.": "FleetPredict Pro: mantenimiento predictivo de flotas y gestión de vehículos.",
    "Toggle navigation": "Alternar navegación",
    "Dashboard": "Panel",
    "Dashboard - FleetPredict Pro": "Panel - FleetPredict Pro",
    "Alerts": "Alertas",
    "Help": "Ayuda",
    "Fleet": "Flota",
    "Vehicles": "Vehículos",
    "Compliance": "Cumplimiento",
    "Route planner": "Planificador de rutas",
    "Maintenance": "Mantenimiento",
    "Tasks": "Tareas",
    "Maintenance templates": "Plantillas de mantenimiento",
    "Work orders": "Órdenes de trabajo",
    "Spare parts": "Repuestos",
    "Suppliers": "Proveedores",
    "Reports & predictions": "Reportes y predicciones",
    "Failure predictions": "Predicción de fallas",
    "Suggested maintenance": "Mantenimiento sugerido",
    "Reports": "Reportes",
    "Export center": "Centro de exportación",
    "Settings": "Configuración",
    "Alert rules": "Reglas de alerta",
    "Telemetry thresholds": "Umbrales de telemetría",
    "Users": "Usuarios",
    "Vehicle types": "Tipos de vehículo",
    "Audit log": "Registro de auditoría",
    "Notifications": "Notificaciones",
    "new": "nuevo",
    "View all alerts": "Ver todas las alertas",
    "No notifications": "Sin notificaciones",
    "Language": "Idioma",
    "Use English": "Usar inglés",
    "Use Spanish": "Usar español",
    "Profile": "Perfil",
    "Help center": "Centro de ayuda",
    "Register": "Registrarse",
    "Quick actions": "Acciones rápidas",
    "Go back": "Volver",
    "Go to dashboard": "Ir al panel",
    "Tip: Use breadcrumbs and quick actions to avoid getting lost.": "Consejo: usa las migas de pan y las acciones rápidas para no perderte.",
    "Close": "Cerrar",
    "Are you sure you want to continue? This action may be hard to undo.": "¿Seguro que deseas continuar? Esta acción puede ser difícil de deshacer.",
    "Fleet overview, vehicle status, maintenance tasks and key metrics.": "Resumen de la flota, estado de vehículos, tareas de mantenimiento e indicadores clave.",
    "breadcrumb": "migas de pan",
    "Customize": "Personalizar",
    "expired": "vencidos",
    "expiring in": "por vencer en",
    "days": "días",
    "View compliance": "Ver cumplimiento",
    "Charts period:": "Período de gráficos:",
    "7 days": "7 días",
    "30 days": "30 días",
    "This month": "Este mes",
    "Total Vehicles": "Total de vehículos",
    "Fleet Availability": "Disponibilidad de la flota",
    "Need Attention": "Requieren atención",
    "Monthly Costs": "Costos mensuales",
    "Fleet health": "Salud de la flota",
    "Good": "Bueno",
    "Caution": "Precaución",
    "Vehicle": "Vehículo",
    "Health": "Salud",
    "Engine": "Motor",
    "On": "Encendido",
    "Off": "Apagado",
    "Vehicles by Status": "Vehículos por estado",
    "Maintenance Tasks by Status": "Tareas de mantenimiento por estado",
    "Tasks by Priority (open)": "Tareas por prioridad (abiertas)",
    "Operations center (SOC) – High and critical alerts": "Centro de operaciones (SOC): alertas altas y críticas",
    "Time": "Tiempo",
    "Last 24h": "Últimas 24 h",
    "Last 7 days": "Últimos 7 días",
    "Last 30 days": "Últimos 30 días",
    "Reason": "Motivo",
    "All": "Todos",
    "Place": "Ubicación",
    "Contains": "Contiene",
    "Message text": "Texto del mensaje",
    "Show": "Mostrar",
    "Apply": "Aplicar",
    "Filtered alerts:": "Alertas filtradas:",
    "Clear filters": "Limpiar filtros",
    "Suggested actions (playbooks) and runnable runbooks for each alert.": "Acciones sugeridas (playbooks) y runbooks ejecutables para cada alerta.",
    "Playbook – Suggested steps:": "Playbook – Pasos sugeridos:",
    "Runbooks – Actions:": "Runbooks – Acciones:",
    "No high or critical alerts at this time.": "No hay alertas altas o críticas en este momento.",
    "Upcoming Maintenance (Next 7 Days)": "Mantenimiento próximo (próximos 7 días)",
    "Task": "Tarea",
    "Date": "Fecha",
    "Priority": "Prioridad",
    "No upcoming maintenance.": "Sin mantenimiento próximo.",
    "Recent Completed Tasks": "Tareas completadas recientes",
    "Cost": "Costo",
    "No recent completed tasks.": "Sin tareas completadas recientes.",
    "Completed tasks": "Tareas completadas",
    "Cost ($)": "Costo ($)",
    "Completed Tasks & Cost (%(p)s)": "Tareas completadas y costo (%(p)s)",
    # Auth & vehicle list
    "Login - FleetPredict Pro": "Iniciar sesión - FleetPredict Pro",
    "Sign in to FleetPredict Pro.": "Inicia sesión en FleetPredict Pro.",
    "Forgot password?": "¿Olvidaste tu contraseña?",
    "Don't have an account?": "¿No tienes una cuenta?",
    "Email": "Correo electrónico",
    "Password": "Contraseña",
    "Register - FleetPredict Pro": "Registrarse - FleetPredict Pro",
    "Create a FleetPredict Pro account.": "Crea una cuenta en FleetPredict Pro.",
    "First name": "Nombre",
    "Last name": "Apellido",
    "Role": "Rol",
    "Confirm password": "Confirmar contraseña",
    "Already have an account?": "¿Ya tienes una cuenta?",
    "Vehicles - FleetPredict Pro": "Vehículos - FleetPredict Pro",
    "List and manage fleet vehicles. Search and filter by status.": (
        "Lista y gestiona los vehículos de la flota. Busca y filtra por estado."
    ),
    "Add Vehicle": "Agregar vehículo",
    "Export CSV": "Exportar CSV",
    "Search": "Buscar",
    "Search (plate, VIN, make, model)": "Buscar (placa, VIN, marca, modelo)",
    "Filter by status": "Filtrar por estado",
    "All statuses": "Todos los estados",
    "Filter by health": "Filtrar por salud",
    "All health": "Todos los niveles",
    "Per page": "Por página",
    "Results per page": "Resultados por página",
    "Filter": "Filtrar",
    "Clear": "Limpiar",
    "License Plate": "Placa",
    "Mileage": "Kilometraje",
    "View": "Ver",
    "Edit": "Editar",
    "History": "Historial",
    "No vehicles found.": "No se encontraron vehículos.",
    "Previous": "Anterior",
    "Next": "Siguiente",
    "Status": "Estado",
    "If you requested this, follow the link below to set a new password:": (
        "Si solicitaste esto, sigue el enlace de abajo para establecer una nueva contraseña:"
    ),
    "If you didn't request this, you can ignore this email. Your password will remain unchanged.": (
        "Si no lo solicitaste, puedes ignorar este correo. Tu contraseña no cambiará."
    ),
    "FleetPredict Pro – Password reset": "FleetPredict Pro – Restablecimiento de contraseña",
    "Page %(num)s of %(npages)s (%(ntotal)s total)": (
        "Página %(num)s de %(npages)s (%(ntotal)s en total)"
    ),
    # Password reset flow
    "Reset password - FleetPredict Pro": "Restablecer contraseña - FleetPredict Pro",
    "Request a password reset link by email.": (
        "Solicita un enlace de restablecimiento de contraseña por correo."
    ),
    "Reset password": "Restablecer contraseña",
    "Enter your email address and we'll send you a link to reset your password.": (
        "Ingresa tu correo y te enviaremos un enlace para restablecer tu contraseña."
    ),
    "Send reset link": "Enviar enlace",
    "Back to login": "Volver al inicio de sesión",
    "Reset email sent - FleetPredict Pro": "Correo de restablecimiento enviado - FleetPredict Pro",
    "Password reset instructions sent.": "Se enviaron las instrucciones para restablecer la contraseña.",
    "Check your email": "Revisa tu correo",
    "If an account exists for the email you entered, we've sent you a link to reset your password.": (
        "Si existe una cuenta con el correo que ingresaste, te enviamos un enlace para restablecer la contraseña."
    ),
    "If you don't see the email, check your spam folder.": (
        "Si no ves el correo, revisa la carpeta de spam."
    ),
    "Set new password - FleetPredict Pro": "Establecer nueva contraseña - FleetPredict Pro",
    "Choose a new password.": "Elige una nueva contraseña.",
    "Set new password": "Establecer nueva contraseña",
    "New password": "Nueva contraseña",
    "Confirm new password": "Confirmar nueva contraseña",
    "This reset link is invalid or has expired. Please request a new one.": (
        "Este enlace no es válido o expiró. Solicita uno nuevo."
    ),
    "Request new link": "Solicitar nuevo enlace",
    "Password reset complete - FleetPredict Pro": (
        "Contraseña restablecida - FleetPredict Pro"
    ),
    "Your password has been reset.": "Tu contraseña fue restablecida.",
    "Password reset complete": "Contraseña restablecida",
    "Your password has been set. You can now log in with your new password.": (
        "Tu contraseña quedó configurada. Ya puedes iniciar sesión con la nueva contraseña."
    ),
    "Log in": "Iniciar sesión",
    "Change Password - FleetPredict Pro": "Cambiar contraseña - FleetPredict Pro",
    "Change your FleetPredict Pro password.": "Cambia tu contraseña de FleetPredict Pro.",
    "Change Password": "Cambiar contraseña",
    "Back to Profile": "Volver al perfil",
    # Maintenance
    "Maintenance - FleetPredict Pro": "Mantenimiento - FleetPredict Pro",
    "List and manage maintenance tasks. Filter by status.": (
        "Lista y gestiona las tareas de mantenimiento. Filtra por estado."
    ),
    "Maintenance Tasks": "Tareas de mantenimiento",
    "Add Task": "Agregar tarea",
    "Scheduled": "Programada",
    "Complete": "Completar",
    "No maintenance tasks found.": "No se encontraron tareas de mantenimiento.",
    "Edit Maintenance Task - FleetPredict Pro": "Editar tarea de mantenimiento - FleetPredict Pro",
    "Add Maintenance Task - FleetPredict Pro": "Agregar tarea de mantenimiento - FleetPredict Pro",
    "Edit maintenance task.": "Editar tarea de mantenimiento.",
    "Create a new maintenance task.": "Crear una nueva tarea de mantenimiento.",
    "Edit Maintenance Task": "Editar tarea de mantenimiento",
    "Add Maintenance Task": "Agregar tarea de mantenimiento",
    "Apply template:": "Aplicar plantilla:",
    "— None —": "— Ninguna —",
    "Back to list": "Volver al listado",
    "Assignee": "Asignado a",
    "Title": "Título",
    "Name": "Nombre",
    "Type": "Tipo",
    "Scheduled Date": "Fecha programada",
    "Duration (min)": "Duración (min)",
    "Estimated Cost": "Costo estimado",
    "Save": "Guardar",
    "Cancel": "Cancelar",
    "Description": "Descripción",
    "Maintenance task details and documents.": (
        "Detalle de la tarea de mantenimiento y documentos."
    ),
    "Delete task": "Eliminar tarea",
    "Are you sure you want to delete this maintenance task?": (
        "¿Seguro que deseas eliminar esta tarea de mantenimiento?"
    ),
    "Task Details": "Detalle de la tarea",
    "Actual Cost": "Costo real",
    "Completed": "Completada",
    "Completion Notes": "Notas de cierre",
    "Work order": "Orden de trabajo",
    "Create work order": "Crear orden de trabajo",
    "Documents": "Documentos",
    "Document": "Documento",
    "Choose document file to upload": "Elegir archivo de documento para subir",
    "Description (optional)": "Descripción (opcional)",
    "Optional description for the document": "Descripción opcional del documento",
    "Upload": "Subir",
    "No documents attached.": "No hay documentos adjuntos.",
    "Delete Maintenance Task - FleetPredict Pro": (
        "Eliminar tarea de mantenimiento - FleetPredict Pro"
    ),
    "Delete Maintenance Task": "Eliminar tarea de mantenimiento",
    "Cannot delete completed tasks.": "No se pueden eliminar tareas completadas.",
    "Back": "Volver",
    "Mark Complete": "Marcar como completada",
    "Mileage at Maintenance": "Kilometraje en el mantenimiento",
    "Work Orders - FleetPredict Pro": "Órdenes de trabajo - FleetPredict Pro",
    "Work orders for maintenance tasks.": "Órdenes de trabajo para tareas de mantenimiento.",
    "Work orders": "Órdenes de trabajo",
    "Work Orders": "Órdenes de trabajo",
    "Due from": "Vence desde",
    "Due to": "Vence hasta",
    "Number": "Número",
    "Due date": "Fecha de vencimiento",
    "No work orders. Create one from a maintenance task.": (
        "No hay órdenes de trabajo. Crea una desde una tarea de mantenimiento."
    ),
    "Edit Work Order - FleetPredict Pro": "Editar orden de trabajo - FleetPredict Pro",
    "Create Work Order - FleetPredict Pro": "Crear orden de trabajo - FleetPredict Pro",
    "Edit Work Order": "Editar orden de trabajo",
    "Create Work Order": "Crear orden de trabajo",
    "Maintenance task": "Tarea de mantenimiento",
    "Notes": "Notas",
    "Completion date": "Fecha de finalización",
    "Created": "Creado",
    "Maintenance Templates - FleetPredict Pro": "Plantillas de mantenimiento - FleetPredict Pro",
    "Manage maintenance templates. Apply when creating tasks.": (
        "Gestiona plantillas de mantenimiento. Aplícalas al crear tareas."
    ),
    "Templates": "Plantillas",
    "Maintenance Templates": "Plantillas de mantenimiento",
    "Add template": "Agregar plantilla",
    "Back to Maintenance": "Volver a mantenimiento",
    "Steps": "Pasos",
    "Use": "Usar",
    "No templates. Create one to prefill tasks.": (
        "No hay plantillas. Crea una para prellenar tareas."
    ),
    "Edit Maintenance Template - FleetPredict Pro": (
        "Editar plantilla de mantenimiento - FleetPredict Pro"
    ),
    "Add Maintenance Template - FleetPredict Pro": (
        "Agregar plantilla de mantenimiento - FleetPredict Pro"
    ),
    "Edit maintenance template.": "Editar plantilla de mantenimiento.",
    "Create a maintenance template.": "Crear una plantilla de mantenimiento.",
    "Edit Template": "Editar plantilla",
    "Back to templates": "Volver a plantillas",
    "Estimated duration (minutes)": "Duración estimada (minutos)",
    "Steps (checklist)": "Pasos (lista de verificación)",
    "Delete Maintenance Template - FleetPredict Pro": (
        "Eliminar plantilla de mantenimiento - FleetPredict Pro"
    ),
    "Delete template": "Eliminar plantilla",
    "Are you sure you want to delete the following maintenance template?": (
        "¿Seguro que deseas eliminar la siguiente plantilla de mantenimiento?"
    ),
    # Inventory
    "Inventory": "Inventario",
    "Spare Parts - FleetPredict Pro": "Repuestos - FleetPredict Pro",
    "Browse spare parts inventory, search, filter by category, and export.": (
        "Explora el inventario de repuestos, busca, filtra por categoría y exporta."
    ),
    "Spare parts": "Repuestos",
    "Create new": "Crear nuevo",
    "Low stock": "Stock bajo",
    "Reorder": "Reordenar",
    "Reorder point": "Punto de reorden",
    "Search name or part #": "Buscar por nombre o n.º de pieza",
    "Category": "Categoría",
    "All categories": "Todas las categorías",
    "Low stock only": "Solo stock bajo",
    "Part#": "N.º pieza",
    "Stock": "Stock",
    "Part details": "Detalle del repuesto",
    "Part number": "Número de pieza",
    "Unit cost": "Costo unitario",
    "Current stock": "Stock actual",
    "OK": "OK",
    "No data.": "Sin datos.",
    "Edit Spare Part - FleetPredict Pro": "Editar repuesto - FleetPredict Pro",
    "Create Spare Part - FleetPredict Pro": "Crear repuesto - FleetPredict Pro",
    "Edit spare part": "Editar repuesto",
    "Create spare part": "Crear repuesto",
    "Edit Spare Part": "Editar repuesto",
    "Create Spare Part": "Crear repuesto",
    "Adjust stock": "Ajustar stock",
    "Stock movements": "Movimientos de stock",
    "Quantity": "Cantidad",
    "User": "Usuario",
    "Updated": "Actualizado",
    "Created by": "Creado por",
    "Delete spare part - FleetPredict Pro": "Eliminar repuesto - FleetPredict Pro",
    "Delete spare part": "Eliminar repuesto",
    "Are you sure you want to delete this spare part?": (
        "¿Seguro que deseas eliminar este repuesto?"
    ),
    "This action cannot be undone.": "Esta acción no se puede deshacer.",
    "Suppliers - FleetPredict Pro": "Proveedores - FleetPredict Pro",
    "Create": "Crear",
    "Compare": "Comparar",
    "Contact": "Contacto",
    "Phone": "Teléfono",
    "Rating": "Valoración",
    "reviews": "reseñas",
    "Edit Supplier - FleetPredict Pro": "Editar proveedor - FleetPredict Pro",
    "Create Supplier - FleetPredict Pro": "Crear proveedor - FleetPredict Pro",
    "Edit Supplier": "Editar proveedor",
    "Create Supplier": "Crear proveedor",
    "Supplier information": "Información del proveedor",
    "Address": "Dirección",
    "Delivery terms": "Condiciones de entrega",
    "Rate after delivery": "Valorar tras la entrega",
    "Stars": "Estrellas",
    "Comment": "Comentario",
    "Save review": "Guardar reseña",
    "Recent reviews": "Reseñas recientes",
    "By": "Por",
    "Supplied parts": "Piezas suministradas",
    "Spare part": "Repuesto",
    "Price": "Precio",
    "Lead time": "Plazo de entrega",
    "Delete supplier - FleetPredict Pro": "Eliminar proveedor - FleetPredict Pro",
    "Delete supplier": "Eliminar proveedor",
    "Are you sure you want to delete this supplier?": (
        "¿Seguro que deseas eliminar este proveedor?"
    ),
    "Supplier Comparison - FleetPredict Pro": "Comparación de proveedores - FleetPredict Pro",
    "Supplier comparison": "Comparación de proveedores",
    "Supplier Comparison": "Comparación de proveedores",
    "— Select a part —": "— Selecciona una pieza —",
    "Stock Adjustment - FleetPredict Pro": "Ajuste de stock - FleetPredict Pro",
    "Stock adjustment": "Ajuste de stock",
    "Post-delivery supplier rating (optional for Stock In)": (
        "Valoración del proveedor tras la entrega (opcional para entrada de stock)"
    ),
    "Select supplier": "Seleccionar proveedor",
    "Optional feedback about this delivery": (
        "Comentario opcional sobre esta entrega"
    ),
    "This review is only saved when movement type is Stock In.": (
        "Esta reseña solo se guarda cuando el movimiento es Entrada de stock."
    ),
    "Save movement": "Guardar movimiento",
    "Reorder Suggestions - FleetPredict Pro": "Sugerencias de reorden - FleetPredict Pro",
    "Reorder suggestions": "Sugerencias de reorden",
    "Reorder Suggestions": "Sugerencias de reorden",
    "Suggested (reorder − stock)": "Sugerido (punto de reorden − stock)",
    "Suggested order quantity = reorder point minus current stock (values shown separately).": (
        "Cantidad sugerida = punto de reorden menos stock actual (valores mostrados por separado)."
    ),
    "Back to spare parts": "Volver a repuestos",
    "Low Stock Alert - FleetPredict Pro": "Alerta de stock bajo - FleetPredict Pro",
    "Low stock alert": "Alerta de stock bajo",
    "Low Stock Alert": "Alerta de stock bajo",
    "My alerts - FleetPredict Pro": "Mis alertas - FleetPredict Pro",
    "Notification center.": "Centro de notificaciones.",
    "My alerts": "Mis alertas",
    "Severity": "Gravedad",
    "All severities": "Todas las gravedades",
    "Unread": "No leídas",
    "Read": "Leídas",
    "Message": "Mensaje",
    "Actions": "Acciones",
    "No alerts.": "No hay alertas.",
    "Help center - FleetPredict Pro": "Centro de ayuda - FleetPredict Pro",
    "1. Quick navigation": "1. Navegación rápida",
    "Use breadcrumbs on each page to know where you are.": (
        "Usa las migas de pan en cada página para saber dónde estás."
    ),
    "Use the quick bar buttons: <strong>Go back</strong>, <strong>Go to dashboard</strong>, and <strong>Help center</strong>.": (
        "Usa los botones de la barra rápida: <strong>Volver</strong>, <strong>Ir al panel</strong> y "
        "<strong>Centro de ayuda</strong>."
    ),
    "Fleet features are under <strong>Fleet</strong>, maintenance and stock under <strong>Maintenance</strong>.": (
        "Las funciones de flota están en <strong>Flota</strong>; el mantenimiento y el stock, en "
        "<strong>Mantenimiento</strong>."
    ),
    "2. Preventing mistakes": "2. Evitar errores",
    "Dangerous actions ask for confirmation before continuing.": (
        "Las acciones peligrosas piden confirmación antes de continuar."
    ),
    "Forms validate fields and highlight invalid values.": (
        "Los formularios validan los campos y resaltan los valores no válidos."
    ),
    "If you edit a form and try to leave, the app warns about unsaved changes.": (
        "Si editas un formulario e intentas salir, la aplicación avisa sobre cambios sin guardar."
    ),
    "3. Error recovery": "3. Recuperación ante errores",
    "System messages (top-right) explain successful or failed actions.": (
        "Los mensajes del sistema (arriba a la derecha) explican si las acciones tuvieron éxito o fallaron."
    ),
    "On permission errors, check your role or try a route available to your profile.": (
        "Si hay errores de permisos, revisa tu rol o prueba una ruta disponible para tu perfil."
    ),
    "If telemetry pages look empty, verify live telemetry is running and date filters are correct.": (
        "Si las páginas de telemetría se ven vacías, comprueba que la telemetría en vivo esté activa y que los "
        "filtros de fecha sean correctos."
    ),
    "Recommended user flows": "Flujos de usuario recomendados",
    "Fleet manager flow": "Flujo del gestor de flota",
    "Open <strong>Fleet → Vehicles</strong> and select a vehicle.": (
        "Abre <strong>Flota → Vehículos</strong> y selecciona un vehículo."
    ),
    "Review Sensors, GPS, Driving and Mileage panels.": (
        "Revisa los paneles de sensores, GPS, conducción y kilometraje."
    ),
    "Open <strong>Maintenance → Tasks</strong> to schedule work.": (
        "Abre <strong>Mantenimiento → Tareas</strong> para programar trabajos."
    ),
    "Use <strong>Maintenance → Spare parts</strong> to adjust stock if needed.": (
        "Usa <strong>Mantenimiento → Repuestos</strong> para ajustar el stock si hace falta."
    ),
    "Reports and decisions flow": "Flujo de informes y decisiones",
    "Open <strong>Reports &amp; predictions</strong>.": (
        "Abre <strong>Informes y predicciones</strong>."
    ),
    "Check failure predictions, review criticality reasons, and override only with a clear reason.": (
        "Revisa predicciones de fallo, los motivos de criticidad y anula solo con un motivo claro."
    ),
    "Review suggested maintenance, adjust the proposed date/priority, then create the task.": (
        "Revisa el mantenimiento sugerido, ajusta la fecha o prioridad propuesta y crea la tarea."
    ),
    "Download PDF reports or use <strong>Export Center</strong> for spreadsheet-ready data.": (
        "Descarga informes PDF o usa el <strong>Centro de exportación</strong> para datos listos para hojas de cálculo."
    ),
    "Administrators should review <strong>Settings → Audit log</strong> after critical operations.": (
        "Los administradores deberían revisar <strong>Configuración → Registro de auditoría</strong> tras operaciones "
        "críticas."
    ),
    "Comparison Report - FleetPredict Pro": "Informe comparativo - FleetPredict Pro",
    "FR14/15: Compare vehicles by maintenance count and cost.": (
        "FR14/15: compara vehículos por número de mantenimientos y costo."
    ),
    "Comparison Report (FR14/15)": "Informe comparativo (FR14/15)",
    "Back to Reports": "Volver a informes",
    "Vehicles compared by number of completed tasks and total cost.": (
        "Vehículos comparados por tareas completadas y costo total."
    ),
    "All vehicles": "Todos los vehículos",
    "Apply filters": "Aplicar filtros",
    "Total cost": "Costo total",
    "Cost Report - FleetPredict Pro": "Informe de costos - FleetPredict Pro",
    "FR13: Maintenance cost by vehicle.": "FR13: costo de mantenimiento por vehículo.",
    "Cost Report": "Informe de costos",
    "Actual cost of completed maintenance by vehicle.": (
        "Costo real del mantenimiento completado por vehículo."
    ),
    "Grand total (all vehicles):": "Total general (todos los vehículos):",
    "No completed maintenance with cost data.": (
        "No hay mantenimiento completado con datos de costo."
    ),
    "Export Center - FleetPredict Pro": "Centro de exportación - FleetPredict Pro",
    "Export Center": "Centro de exportación",
    "Back to reports": "Volver a informes",
    "Export operational data with role-aware visibility. Files are CSV and open directly in Excel or Google Sheets.": (
        "Exporta datos operativos según visibilidad por rol. Los archivos son CSV y se abren en Excel o Google Sheets."
    ),
    "Dataset": "Conjunto de datos",
    "Format": "Formato",
    "Vehicle filter": "Filtro de vehículo",
    "All visible vehicles": "Todos los vehículos visibles",
    "Start": "Inicio",
    "End": "Fin",
    "Generate export": "Generar exportación",
    "Recent export history": "Historial reciente de exportaciones",
    "Rows": "Filas",
    "Expires": "Caduca",
    "No exports yet.": "Aún no hay exportaciones.",
    "Reports - FleetPredict Pro": "Informes - FleetPredict Pro",
    "Export PDF reports per vehicle or fleet.": (
        "Exporta informes PDF por vehículo o de toda la flota."
    ),
    "Fleet report": "Informe de flota",
    "Download a PDF summary of all visible vehicles (health, latest alert, upcoming maintenance, mileage).": (
        "Descarga un PDF resumido de todos los vehículos visibles (salud, última alerta, mantenimiento próximo, "
        "kilometraje)."
    ),
    "Download fleet report (PDF)": "Descargar informe de flota (PDF)",
    "Per-vehicle report": "Informe por vehículo",
    "For a detailed vehicle report (maintenance history, recent alerts, telemetry), open the vehicle detail and use the \"Export PDF report\" button.": (
        "Para un informe detallado del vehículo (historial de mantenimiento, alertas recientes, telemetría), abre el "
        "detalle del vehículo y usa el botón «Exportar informe PDF»."
    ),
    "Go to vehicle list": "Ir a la lista de vehículos",
    "Analytics reports (FR12–15)": "Informes analíticos (FR12–15)",
    "Maintenance trends, cost by vehicle, and comparison.": (
        "Tendencias de mantenimiento, costo por vehículo y comparación."
    ),
    "Trends": "Tendencias",
    "Comparison": "Comparación",
    "Commercial report schedule": "Programación de informes comerciales",
    "Save report delivery metadata for weekly or monthly operational reviews.": (
        "Guarda metadatos de entrega de informes para revisiones operativas semanales o mensuales."
    ),
    "Schedule name": "Nombre del programa",
    "Weekly": "Semanal",
    "Monthly": "Mensual",
    "ops@example.com": "ops@example.com",
    "Frequency": "Frecuencia",
    "Recipients": "Destinatarios",
    "Maintenance Trends - FleetPredict Pro": "Tendencias de mantenimiento - FleetPredict Pro",
    "FR12: Maintenance completion trends.": "FR12: tendencias de mantenimiento completado.",
    "Maintenance Trends": "Tendencias de mantenimiento",
    "Completed maintenance tasks in the last 90 days by month.": (
        "Tareas de mantenimiento completadas en los últimos 90 días por mes."
    ),
    "Total completed (90 days):": "Total completado (90 días):",
    "Year": "Año",
    "Month": "Mes",
    "No completed tasks in the last 90 days.": (
        "No hay tareas completadas en los últimos 90 días."
    ),
    "Route History - FleetPredict Pro": "Historial de rutas - FleetPredict Pro",
    "Route History": "Historial de rutas",
    "Plan route": "Planificar ruta",
    "Origin": "Origen",
    "Destination": "Destino",
    "No routes planned yet.": "Aún no hay rutas planificadas.",
    "Route Planner - FleetPredict Pro": "Planificador de rutas - FleetPredict Pro",
    "Route Planner": "Planificador de rutas",
    "Enter origin, destination, and select a vehicle. The system will suggest 3 route alternatives based on vehicle health and your optimization priority.": (
        "Indica origen, destino y selecciona un vehículo. El sistema sugerirá 3 alternativas de ruta según la salud "
        "del vehículo y tu prioridad de optimización."
    ),
    "Get suggestions": "Obtener sugerencias",
    "Route history": "Historial de rutas",
    "Route Suggestions - FleetPredict Pro": "Sugerencias de ruta - FleetPredict Pro",
    "Suggestions": "Sugerencias",
    "Route Suggestions": "Sugerencias de ruta",
    "Recommended": "Recomendada",
    "Distance:": "Distancia:",
    "Time:": "Tiempo:",
    "Fuel cost:": "Costo de combustible:",
    "Select this route": "Seleccionar esta ruta",
    "Plan another route": "Planificar otra ruta",
    "Profile - FleetPredict Pro": "Perfil - FleetPredict Pro",
    "Your FleetPredict Pro profile and notification preferences.": (
        "Tu perfil de FleetPredict Pro y preferencias de notificación."
    ),
    "Notification preferences": "Preferencias de notificación",
    "Email notifications": "Notificaciones por correo",
    "Maintenance due alerts": "Alertas de mantenimiento próximo",
    "Overdue maintenance alerts": "Alertas de mantenimiento vencido",
    "Critical alerts": "Alertas críticas",
    "Yes": "Sí",
    "No": "No",
    "Date joined": "Fecha de registro",
    "Users - FleetPredict Pro": "Usuarios - FleetPredict Pro",
    "Manage users and roles.": "Gestiona usuarios y roles.",
    "Search by name or email": "Buscar por nombre o correo",
    "Filter by role": "Filtrar por rol",
    "All roles": "Todos los roles",
    "No users found.": "No se encontraron usuarios.",
    "Vehicle details and maintenance history.": (
        "Detalle del vehículo e historial de mantenimiento."
    ),
    "Sensors": "Sensores",
    "GPS": "GPS",
    "Driving": "Conducción",
    "Export PDF report": "Exportar informe PDF",
    "Delete vehicle": "Eliminar vehículo",
    "This will mark the vehicle as retired. Historical data will be preserved.": (
        "Esto marcará el vehículo como retirado. Los datos históricos se conservarán."
    ),
    "Health indicator": "Indicador de salud",
    "This vehicle has status": "Este vehículo tiene estado",
    "because:": "porque:",
    "Vehicle Information": "Información del vehículo",
    "VIN": "VIN",
    "Make / Model": "Marca / modelo",
    "Color": "Color",
    "Why this health status?": "¿Por qué este estado de salud?",
    "Current Mileage": "Kilometraje actual",
    "km": "km",
    "Fuel Type": "Tipo de combustible",
    "Assigned Driver": "Conductor asignado",
    "Total maintenance tasks:": "Total de tareas de mantenimiento:",
    "Last maintenance:": "Último mantenimiento:",
    "Never": "Nunca",
    "View History": "Ver historial",
    "Add requirement": "Agregar requisito",
    "Requirement": "Requisito",
    "Expiration": "Vencimiento",
    "Expired": "Vencido",
    "No compliance requirements.": "No hay requisitos de cumplimiento.",
    "Add one to track inspections, licenses, etc.": (
        "Agrega uno para seguir inspecciones, licencias, etc."
    ),
    "Live telemetry": "Telemetría en vivo",
    "Connecting…": "Conectando…",
    "Speed": "Velocidad",
    "—": "—",
    "Fuel %%": "Combustible %%",
    "Engine temp °C": "Temp. motor °C",
    "RPM": "RPM",
    "Odometer km": "Odómetro km",
    "Voltage": "Voltaje",
    "Position": "Posición",
    "Last reading": "Última lectura",
    "Connected. Waiting for live data…": "Conectado. Esperando datos en tiempo real…",
    "Disconnected. Reconnecting in 3 s…": "Desconectado. Reconectando en 3 s…",
    "km/h": "km/h",
    "%%": "%%",
    "°C": "°C",
    "V": "V",
    "Edit Vehicle": "Editar vehículo",
    "Edit vehicle details.": "Editar datos del vehículo.",
    "Add a new vehicle to the fleet.": "Agregar un vehículo nuevo a la flota.",
    "Make": "Marca",
    "Model": "Modelo",
    "Vehicle Type": "Tipo de vehículo",
    "Current Mileage (km)": "Kilometraje actual (km)",
    "Fuel Capacity (L)": "Capacidad de combustible (L)",
    "Create alert rule - FleetPredict Pro": "Crear regla de alerta - FleetPredict Pro",
    "Create alert rule": "Crear regla de alerta",
    "Back to rules": "Volver a reglas",
    "Add a new alert rule. Select the rule type, set the value, and enable it.": (
        "Agrega una regla de alerta nueva. Elige el tipo, ajusta el valor y actívala."
    ),
    "Create rule": "Crear regla",
    "Edit alert rule - FleetPredict Pro": "Editar regla de alerta - FleetPredict Pro",
    "Edit alert rule": "Editar regla de alerta",
    "Alert rules - FleetPredict Pro": "Reglas de alerta - FleetPredict Pro",
    "Alert rules": "Reglas de alerta",
    "Add rule": "Agregar regla",
    "Back to dashboard": "Volver al panel",
    "Configure when alerts are triggered.": "Configura cuándo se generan las alertas.",
    "Add new rules with <strong>Add rule</strong>, or": (
        "Agrega reglas nuevas con <strong>Agregar regla</strong>, o"
    ),
    "adjust the values below and click <strong>Save</strong> to apply changes.": (
        "ajusta los valores siguientes y pulsa <strong>Guardar</strong> para aplicar los cambios."
    ),
    "Rule": "Regla",
    "Value": "Valor",
    "Action": "Acción",
    "Maintenance: alert when a task is due within N days": (
        "Mantenimiento: alerta cuando una tarea vence en N días"
    ),
    "Maintenance: alert when a task is overdue": (
        "Mantenimiento: alerta cuando una tarea está vencida"
    ),
    "Compliance: show banner when requirements expire within N days": (
        "Cumplimiento: aviso cuando los requisitos vencen en N días"
    ),
    "Work orders: (reserved) due within N days window": (
        "Órdenes de trabajo: (reservado) ventana de vencimiento en N días"
    ),
    "No rules. Default rules are created on first load.": (
        "No hay reglas. Se crean reglas predeterminadas en la primera carga."
    ),
    "Delete threshold - FleetPredict Pro": "Eliminar umbral - FleetPredict Pro",
    "Delete threshold": "Eliminar umbral",
    "Are you sure you want to delete this threshold?": (
        "¿Seguro que deseas eliminar este umbral?"
    ),
    "Edit threshold - FleetPredict Pro": "Editar umbral - FleetPredict Pro",
    "Create threshold - FleetPredict Pro": "Crear umbral - FleetPredict Pro",
    "Edit threshold": "Editar umbral",
    "Create threshold": "Crear umbral",
    "Back to thresholds": "Volver a umbrales",
    "Define a trigger: select the telemetry attribute, comparison operator, threshold value, and severity. When the attribute crosses the threshold, an alert is created.": (
        "Define un disparador: elige el atributo de telemetría, el operador, el valor umbral y la gravedad. "
        "Cuando el atributo cruza el umbral, se crea una alerta."
    ),
    "Attribute": "Atributo",
    "Operator": "Operador",
    "Threshold value": "Valor umbral",
    "Label (optional)": "Etiqueta (opcional)",
    "Enabled": "Activado",
    "Telemetry thresholds - FleetPredict Pro": "Umbrales de telemetría - FleetPredict Pro",
    "Telemetry thresholds": "Umbrales de telemetría",
    "Add threshold": "Agregar umbral",
    "Create triggers and thresholds for telemetry attributes. When a value crosses the threshold, an alert is generated (e.g. engine temperature ≥ 105 °C, fuel level ≤ 15%).": (
        "Crea disparadores y umbrales para atributos de telemetría. Cuando un valor cruza el umbral, se genera una "
        "alerta (p. ej. temperatura del motor ≥ 105 °C, nivel de combustible ≤ 15 %)."
    ),
    "Condition": "Condición",
    "Label": "Etiqueta",
    "No thresholds yet. Click <strong>Add threshold</strong> to create one.": (
        "Aún no hay umbrales. Pulsa <strong>Agregar umbral</strong> para crear uno."
    ),
    "Audit Log - FleetPredict Pro": "Registro de auditoría - FleetPredict Pro",
    "FR27: User action audit log.": "FR27: registro de auditoría de acciones.",
    "Audit Log": "Registro de auditoría",
    "Back to Dashboard": "Volver al panel",
    "Export CSV": "Exportar CSV",
    "All actions": "Todas las acciones",
    "Model name": "Nombre del modelo",
    "User email/name": "Correo o nombre de usuario",
    "Search message/object": "Buscar en mensaje/objeto",
    "Object ID": "ID de objeto",
    "Changes": "Cambios",
    "IP": "IP",
    "No audit log entries.": "No hay entradas en el registro de auditoría.",
    "View": "Ver",
    "Customize Dashboard - FleetPredict Pro": "Personalizar panel - FleetPredict Pro",
    "Customize Dashboard": "Personalizar panel",
    "Save layout": "Guardar diseño",
    "Reset to default": "Restablecer predeterminado",
    "Available Widgets": "Widgets disponibles",
    "Widget Size": "Tamaño del widget",
    "Current Layout": "Diseño actual",
    "Max 20 widgets.": "Máximo 20 widgets.",
    "Layout saved.": "Diseño guardado.",
    "widgets": "widgets",
    "Error:": "Error:",
    "unknown": "desconocido",
    "Platform overview: users, vehicle types, audit activity.": (
        "Resumen de la plataforma: usuarios, tipos de vehículo y actividad de auditoría."
    ),
    "Platform Overview": "Resumen de la plataforma",
    "Total Users": "Usuarios totales",
    "Fleet Vehicles": "Vehículos de la flota",
    "Users by Role": "Usuarios por rol",
    "Quick Links": "Enlaces rápidos",
    "Manage Users": "Gestionar usuarios",
    "Django Admin": "Administración Django",
    "Recent Audit Activity": "Actividad reciente de auditoría",
    "View full audit log": "Ver registro completo",
    "No audit entries yet.": "Aún no hay entradas de auditoría.",
    "Your assigned maintenance tasks and workload.": (
        "Tareas de mantenimiento asignadas y carga de trabajo."
    ),
    "My Workload": "Mi carga de trabajo",
    "Assigned to Me": "Asignadas a mí",
    "Unassigned": "Sin asignar",
    "Tasks by Status": "Tareas por estado",
    "Recent Completions (Mine)": "Completadas recientes (mías)",
    "No recent completions.": "No hay completadas recientes.",
    "View all maintenance tasks": "Ver todas las tareas de mantenimiento",
    "Failure predictions - FleetPredict Pro": "Predicciones de fallo - FleetPredict Pro",
    "Failure predictions": "Predicciones de fallo",
    "Failure recommendations per vehicle.": "Recomendaciones de fallo por vehículo.",
    "Vehicle, type, confidence, timeframe and explainable criticality. FR10 is now actionable and auditable.": (
        "Vehículo, tipo, confianza, plazo y criticidad explicable. FR10 es accionable y auditable."
    ),
    "Newest first": "Más recientes primero",
    "Criticality first": "Criticidad primero",
    "Why": "Motivo",
    "Confidence": "Confianza",
    "Timeframe": "Plazo",
    "Reason required": "Motivo obligatorio",
    "Save override": "Guardar anulación",
    "No prediction alerts.": "No hay alertas de predicción.",
    "Suggested Maintenance - FleetPredict Pro": "Mantenimiento sugerido - FleetPredict Pro",
    "Suggested Maintenance": "Mantenimiento sugerido",
    "Suggested maintenance": "Mantenimiento sugerido",
    "Accept or dismiss suggested maintenance from predictions.": (
        "Acepta o descarta el mantenimiento sugerido a partir de predicciones."
    ),
    "Recommendations from predictions. Review the evidence, adjust the plan, then accept or dismiss with a reason.": (
        "Recomendaciones desde predicciones. Revisa la evidencia, ajusta el plan y acepta o descarta con un motivo."
    ),
    "Reasoning": "Razonamiento",
    "Review and accept": "Revisar y aceptar",
    "Suggested": "Sugerido",
    "Create task": "Crear tarea",
    "Dismiss reason": "Motivo del descarte",
    "Dismiss": "Descartar",
    "No pending suggestions. Accepted and dismissed items no longer appear here.": (
        "No hay sugerencias pendientes. Las aceptadas o descartadas ya no aparecen aquí."
    ),
    "Delete Compliance - FleetPredict Pro": "Eliminar cumplimiento - FleetPredict Pro",
    "Delete compliance requirement": "Eliminar requisito de cumplimiento",
    "Edit Compliance - FleetPredict Pro": "Editar cumplimiento - FleetPredict Pro",
    "Add Compliance - FleetPredict Pro": "Agregar cumplimiento - FleetPredict Pro",
    "Edit Compliance Requirement": "Editar requisito de cumplimiento",
    "Add Compliance Requirement": "Agregar requisito de cumplimiento",
    "Expiration date": "Fecha de vencimiento",
    "Issuing authority": "Autoridad emisora",
    "Document reference": "Referencia del documento",
    "Regulatory compliance requirements.": "Requisitos regulatorios de cumplimiento.",
    "Compliance - FleetPredict Pro": "Cumplimiento - FleetPredict Pro",
    "Compliance Requirements": "Requisitos de cumplimiento",
    "Expiring (30 days)": "Por vencer (30 días)",
    "Expiring": "Por vencer",
    "No compliance requirements. Add one from Vehicles or here.": (
        "No hay requisitos de cumplimiento. Agrega uno desde Vehículos o aquí."
    ),
    "Driving Analysis": "Análisis de conducción",
    "Driving analysis": "Análisis de conducción",
    "Total km": "Km totales",
    "Avg speed": "Velocidad prom.",
    "Driving hours": "Horas de conducción",
    "Aggressive events": "Eventos agresivos",
    "Recent Driving Patterns": "Patrones recientes de conducción",
    "Period": "Período",
    "Km": "Km",
    "Driving h": "h conducción",
    "Idle h": "h ralentí",
    "Max speed": "Velocidad máx.",
    "Aggressive": "Agresivo",
    "No driving pattern data yet.": "Aún no hay datos de patrones de conducción.",
    "GPS Map": "Mapa GPS",
    "N/A": "N/D",
    "Track summary:": "Resumen del recorrido:",
    "points": "puntos",
    "km approx.": "km aprox.",
    "Last update:": "Última actualización:",
    "No GPS data for this period.": "No hay datos GPS en este período.",
    "Start": "Inicio",
    "Latest": "Último",
    "Speed:": "Velocidad:",
    "Mileage Report": "Informe de kilometraje",
    "Mileage report": "Informe de kilometraje",
    "Current odometer": "Odómetro actual",
    "Daily Mileage": "Kilometraje diario",
    "Sensor Dashboard": "Panel de sensores",
    "Add reading": "Agregar lectura",
    "Upload CSV": "Subir CSV",
    "1 day": "1 día",
    "90 days": "90 días",
    "Sensor type": "Tipo de sensor",
    "No sensor readings for the selected period.": (
        "No hay lecturas de sensores en el período seleccionado."
    ),
    "Add Sensor Reading - FleetPredict Pro": "Agregar lectura de sensor - FleetPredict Pro",
    "Add sensor reading": "Agregar lectura de sensor",
    "Add Sensor Reading": "Agregar lectura de sensor",
    "Save reading": "Guardar lectura",
    "Upload Sensor CSV": "Subir CSV de sensores",
    "Upload Sensor Readings": "Subir lecturas de sensores",
    "Import": "Importar",
    "Delete Vehicle - FleetPredict Pro": "Eliminar vehículo - FleetPredict Pro",
    "Delete Vehicle": "Eliminar vehículo",
    "Maintenance History": "Historial de mantenimiento",
    "Back to Vehicle": "Volver al vehículo",
    "No maintenance history.": "No hay historial de mantenimiento.",
    "Delete Vehicle Type - FleetPredict Pro": "Eliminar tipo de vehículo - FleetPredict Pro",
    "Delete vehicle type": "Eliminar tipo de vehículo",
    "Are you sure you want to delete <strong>%(name)s</strong>?": (
        "¿Seguro que deseas eliminar <strong>%(name)s</strong>?"
    ),
    "This type is used by one vehicle. Reassign it before deleting.": (
        "Este tipo está asignado a un vehículo. Reasígnalo antes de eliminar."
    ),
    "This type is used by %(c)s vehicles. Reassign them before deleting.": (
        "Este tipo está asignado a %(c)s vehículos. Reasígnalos antes de eliminar."
    ),
    "Edit Vehicle Type - FleetPredict Pro": "Editar tipo de vehículo - FleetPredict Pro",
    "Add Vehicle Type - FleetPredict Pro": "Agregar tipo de vehículo - FleetPredict Pro",
    "Edit Vehicle Type": "Editar tipo de vehículo",
    "Add Vehicle Type": "Agregar tipo de vehículo",
    "Maintenance interval (days)": "Intervalo de mantenimiento (días)",
    "Maintenance interval (km)": "Intervalo de mantenimiento (km)",
    "Vehicle Types - FleetPredict Pro": "Tipos de vehículo - FleetPredict Pro",
    "Vehicle Types": "Tipos de vehículo",
    "Manage vehicle types and maintenance intervals.": (
        "Gestiona tipos de vehículo e intervalos de mantenimiento."
    ),
    "Add type": "Agregar tipo",
    "Back to vehicles": "Volver a vehículos",
    "Back to types": "Volver a tipos",
    "Interval (days)": "Intervalo (días)",
    "Interval (km)": "Intervalo (km)",
    "No vehicle types. Add one to use in vehicles.": (
        "No hay tipos de vehículo. Agrega uno para usarlo en vehículos."
    ),
    "Add": "Agregar",
}

MULTI_ES = {
    (
        "Platform overview: {total_users} users, {vehicle_types_count} vehicle types, "
        "{total_vehicles} vehicles ({fleet_availability:.0f}% availability)."
    ): (
        "Resumen de la plataforma: {total_users} usuarios, {vehicle_types_count} tipos de vehículo, "
        "{total_vehicles} vehículos ({fleet_availability:.0f}% de disponibilidad)."
    ),
    (
        "{assigned} tasks assigned to you, {unassigned} unassigned. {attention} need "
        "attention."
    ): (
        "{assigned} tareas asignadas a ti, {unassigned} sin asignar. {attention} requieren "
        "atención."
    ),
}


def fill_multiline_header(text: str) -> str:
    """Fix Language and Plural-Forms in PO header."""
    text = text.replace('"Language: \\n"', '"Language: es\\n"')
    text = text.replace(
        '"Plural-Forms: nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? '
        '1 : 2;\\n"',
        '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"',
    )
    text = text.replace("#, fuzzy\n", "")
    return text


def fill_simple_msgstrs(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        mid = m.group(1)
        esc = mid.replace("\\n", "\n")
        if esc == "":
            return m.group(0)
        mstr = ES.get(esc)
        if mstr is None:
            raise KeyError(f"Missing Spanish for msgid: {esc!r}")
        out = mstr.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'msgid "{mid}"\nmsgstr "{out}"'

    return re.sub(
        r'^msgid "((?:[^"\\]|\\.)*)"\s*\nmsgstr ""\s*$',
        repl,
        text,
        flags=re.M,
    )


def fill_multiline_entries(text: str) -> str:
    for en, es in MULTI_ES.items():
        en_esc = en.replace("\n", "\\n")
        # match block msgid ""\n"line"\nmsgstr ""
        pat = (
            r'(msgid ""\s*\n"'
            + re.escape(en.replace("\n", '"\n"'))  # wrong
        )
    # simpler: string replace known blocks
    old1 = (
        'msgid ""\n'
        '"Platform overview: {total_users} users, {vehicle_types_count} vehicle types, "\n'
        '"{total_vehicles} vehicles ({fleet_availability:.0f}% availability)."\n'
        'msgstr ""\n'
    )
    new1 = (
        'msgid ""\n'
        '"Platform overview: {total_users} users, {vehicle_types_count} vehicle types, "\n'
        '"{total_vehicles} vehicles ({fleet_availability:.0f}% availability)."\n'
        'msgstr ""\n'
        '"Resumen de la plataforma: {total_users} usuarios, {vehicle_types_count} tipos de vehículo, "\n'
        '"{total_vehicles} vehículos ({fleet_availability:.0f}% de disponibilidad)."\n'
    )
    text = text.replace(old1, new1)
    old2 = (
        'msgid ""\n'
        '"{assigned} tasks assigned to you, {unassigned} unassigned. {attention} need "\n'
        '"attention."\n'
        'msgstr ""\n'
    )
    new2 = (
        'msgid ""\n'
        '"{assigned} tasks assigned to you, {unassigned} unassigned. {attention} need "\n'
        '"attention."\n'
        'msgstr ""\n'
        '"{assigned} tareas asignadas a ti, {unassigned} sin asignar. {attention} requieren "\n'
        '"atención."\n'
    )
    text = text.replace(old2, new2)
    pwd_req = (
        '#, python-format\n'
        'msgid ""\n'
        '"Someone requested a password reset for your FleetPredict Pro account "\n'
        '"(%(email_addr)s)."\n'
        'msgstr ""\n'
    )
    pwd_req_es = (
        '#, python-format\n'
        'msgid ""\n'
        '"Someone requested a password reset for your FleetPredict Pro account "\n'
        '"(%(email_addr)s)."\n'
        'msgstr ""\n'
        '"Alguien solicitó un restablecimiento de contraseña para tu cuenta "\n'
        '"FleetPredict Pro (%(email_addr)s)."\n'
    )
    text = text.replace(pwd_req, pwd_req_es)
    pwd_ignore = (
        'msgid ""\n'
        '"If you didn\'t request this, you can ignore this email. Your password will "\n'
        '"remain unchanged."\n'
        'msgstr ""\n'
    )
    pwd_ignore_es = (
        'msgid ""\n'
        '"If you didn\'t request this, you can ignore this email. Your password will "\n'
        '"remain unchanged."\n'
        'msgstr ""\n'
        '"Si no lo solicitaste, puedes ignorar este correo. Tu contraseña no "\n'
        '"cambiará."\n'
    )
    text = text.replace(pwd_ignore, pwd_ignore_es)
    # Corrupt duplicate msgstr (from bad fuzzy merge) for dashboard meta_description
    bad_fleet = (
        'msgid "Fleet overview, vehicle status, maintenance tasks and key metrics."\n'
        'msgstr ""\n'
        '"Resumen de la flota, estado de vehículos, tareas de mantenimiento e "\n'
        '"indicadores clave.Resumen de la flota, estado de vehículos, tareas de "\n'
        '"mantenimiento e indicadores clave.Resumen de la flota, estado de vehículos, "\n'
        '"tareas de mantenimiento e indicadores clave.Resumen de la flota, estado de "\n'
        '"vehículos, tareas de mantenimiento e indicadores clave."\n'
    )
    good_fleet = (
        'msgid "Fleet overview, vehicle status, maintenance tasks and key metrics."\n'
        'msgstr ""\n'
        '"Resumen de la flota, estado de vehículos, tareas de mantenimiento e "\n'
        '"indicadores clave."\n'
    )
    text = text.replace(bad_fleet, good_fleet)
    retired_old = (
        'msgid ""\n'
        '"This will mark the vehicle as retired. Historical data will be preserved."\n'
        'msgstr ""\n'
    )
    retired_new = (
        'msgid ""\n'
        '"This will mark the vehicle as retired. Historical data will be preserved."\n'
        'msgstr ""\n'
        '"Esto marcará el vehículo como retirado. Los datos históricos se conservarán."\n'
    )
    text = text.replace(retired_old, retired_new)
    thresh_help_old = (
        'msgid ""\n'
        '"Create triggers and thresholds for telemetry attributes. When a value "\n'
        '"crosses the threshold, an alert is generated (e.g. engine temperature ≥ 105 "\n'
        '"°C, fuel level ≤ 15%%)."\n'
        'msgstr ""\n'
    )
    thresh_help_new = (
        'msgid ""\n'
        '"Create triggers and thresholds for telemetry attributes. When a value "\n'
        '"crosses the threshold, an alert is generated (e.g. engine temperature ≥ 105 "\n'
        '"°C, fuel level ≤ 15%%)."\n'
        'msgstr ""\n'
        '"Crea disparadores y umbrales para atributos de telemetría. Cuando un valor "\n'
        '"cruza el umbral, se genera una alerta (p. ej. temperatura del motor ≥ 105 °C, "\n'
        '"nivel de combustible ≤ 15 %%)."\n'
    )
    text = text.replace(thresh_help_old, thresh_help_new)
    compliance_remove_old = (
        '#, python-format\n'
        'msgid ""\n'
        '"Are you sure you want to remove <strong>%(name)s</strong> (%(rtype)s) for "\n'
        '"%(vehicle)s?"\n'
        'msgstr ""\n'
    )
    compliance_remove_new = (
        '#, python-format\n'
        'msgid ""\n'
        '"Are you sure you want to remove <strong>%(name)s</strong> (%(rtype)s) for "\n'
        '"%(vehicle)s?"\n'
        'msgstr ""\n'
        '"¿Seguro que deseas quitar <strong>%(name)s</strong> (%(rtype)s) de %(vehicle)s?"\n'
    )
    text = text.replace(compliance_remove_old, compliance_remove_new)
    return text


def apply_es_dict_to_po_file(po_path: pathlib.Path, es: dict[str, str]) -> None:
    """Overwrite msgstr for every entry whose msgid exists in es (fixes multiline msgids and stale merges)."""
    po = polib.pofile(str(po_path))
    for entry in po:
        if entry.msgid in es:
            entry.msgstr = es[entry.msgid]
            if "fuzzy" in entry.flags:
                entry.flags.remove("fuzzy")
            if hasattr(entry, "previous_msgid"):
                entry.previous_msgid = None
            if hasattr(entry, "previous_msgctxt"):
                entry.previous_msgctxt = None
    po.save()


def clear_fuzzy_entries(po_path: pathlib.Path) -> None:
    """Remove fuzzy flags and empty msgstr so fill_simple_msgstrs can refill."""
    po = polib.pofile(str(po_path))
    for entry in po:
        if "fuzzy" in entry.flags:
            entry.msgstr = ""
            entry.flags.remove("fuzzy")
        for attr in ("previous_msgid", "previous_msgctxt", "previous_msgid_plural"):
            if hasattr(entry, attr):
                setattr(entry, attr, None)
    po.save()


def fill_python_format_msgstrs(text: str) -> str:
    pairs = [
        (
            'msgid "Overridden by %(user)s: %(reason)s"\nmsgstr ""',
            'msgid "Overridden by %(user)s: %(reason)s"\nmsgstr "Anulado por %(user)s: %(reason)s"',
        ),
        (
            'msgid "Criticality overridden for %(vehicle)s"\nmsgstr ""',
            'msgid "Criticality overridden for %(vehicle)s"\nmsgstr "Criticidad anulada para %(vehicle)s"',
        ),
        (
            'msgid "Suggested: %(atype)s"\nmsgstr ""',
            'msgid "Suggested: %(atype)s"\nmsgstr "Sugerido: %(atype)s"',
        ),
        (
            'msgid "Accepted suggestion from alert %(pk)s"\nmsgstr ""',
            'msgid "Accepted suggestion from alert %(pk)s"\nmsgstr "Sugerencia aceptada desde la alerta %(pk)s"',
        ),
        (
            'msgid "Maintenance task created: %(title)s"\nmsgstr ""',
            'msgid "Maintenance task created: %(title)s"\nmsgstr "Tarea de mantenimiento creada: %(title)s"',
        ),
        (
            'msgid "Alert rule \\"%(name)s\\" updated."\nmsgstr ""',
            'msgid "Alert rule \\"%(name)s\\" updated."\nmsgstr "Regla de alerta \\"%(name)s\\" actualizada."',
        ),
        (
            'msgid "Stock updated: %(name)s -> %(stock)s"\nmsgstr ""',
            'msgid "Stock updated: %(name)s -> %(stock)s"\nmsgstr "Stock actualizado: %(name)s -> %(stock)s"',
        ),
        (
            'msgid "Route alternative %(n)s selected."\nmsgstr ""',
            'msgid "Route alternative %(n)s selected."\nmsgstr "Ruta alternativa %(n)s seleccionada."',
        ),
        (
            'msgid "%(count)s sensor readings imported."\nmsgstr ""',
            'msgid "%(count)s sensor readings imported."\nmsgstr "Se importaron %(count)s lecturas de sensores."',
        ),
        (
            '#, python-format\nmsgid "Page %(num)s of %(npages)s (%(ntotal)s total)"\nmsgstr ""',
            '#, python-format\nmsgid "Page %(num)s of %(npages)s (%(ntotal)s total)"\n'
            'msgstr "Página %(num)s de %(npages)s (%(ntotal)s en total)"',
        ),
        (
            '#, python-format\nmsgid "Page %(num)s of %(npages)s"\nmsgstr ""',
            '#, python-format\nmsgid "Page %(num)s of %(npages)s"\n'
            'msgstr "Página %(num)s de %(npages)s"',
        ),
        (
            'msgid "Complete Task: %(t)s"\nmsgstr ""',
            'msgid "Complete Task: %(t)s"\nmsgstr "Completar tarea: %(t)s"',
        ),
        (
            'msgid "%(n)s step(s)"\nmsgstr ""',
            'msgid "%(n)s step(s)"\nmsgstr "%(n)s paso(s)"',
        ),
        (
            'msgid "%(d)s days"\nmsgstr ""',
            'msgid "%(d)s days"\nmsgstr "%(d)s días"',
        ),
        (
            'msgid "Work Order %(num)s - FleetPredict Pro"\nmsgstr ""',
            'msgid "Work Order %(num)s - FleetPredict Pro"\n'
            'msgstr "Orden de trabajo %(num)s - FleetPredict Pro"',
        ),
        (
            'msgid "Work Order %(num)s"\nmsgstr ""',
            'msgid "Work Order %(num)s"\nmsgstr "Orden de trabajo %(num)s"',
        ),
        (
            '#, python-format\nmsgid "Alternative %(n)s"\nmsgstr ""',
            '#, python-format\nmsgid "Alternative %(n)s"\nmsgstr "Alternativa %(n)s"',
        ),
        (
            '#, python-format\nmsgid "Expiring in %(d)s days"\nmsgstr ""',
            '#, python-format\nmsgid "Expiring in %(d)s days"\nmsgstr "Vence en %(d)s días"',
        ),
        (
            '#, python-format\nmsgid "%(d)s days"\nmsgstr ""',
            '#, python-format\nmsgid "%(d)s days"\nmsgstr "%(d)s días"',
        ),
        (
            '#, python-format\n'
            'msgid "Are you sure you want to delete <strong>%(name)s</strong> (%(plate)s)?"\n'
            'msgstr ""',
            '#, python-format\n'
            'msgid "Are you sure you want to delete <strong>%(name)s</strong> (%(plate)s)?"\n'
            'msgstr "¿Seguro que deseas eliminar <strong>%(name)s</strong> (%(plate)s)?"',
        ),
        (
            '#, python-format\nmsgid "Are you sure you want to delete <strong>%(name)s</strong>?"\nmsgstr ""',
            '#, python-format\nmsgid "Are you sure you want to delete <strong>%(name)s</strong>?"\n'
            'msgstr "¿Seguro que deseas eliminar <strong>%(name)s</strong>?"',
        ),
        (
            '#, python-format\nmsgid "Maintenance history for %(name)s."\nmsgstr ""',
            '#, python-format\nmsgid "Maintenance history for %(name)s."\n'
            'msgstr "Historial de mantenimiento de %(name)s."',
        ),
        (
            '#, python-format\nmsgid "Maintenance History: %(name)s"\nmsgstr ""',
            '#, python-format\nmsgid "Maintenance History: %(name)s"\n'
            'msgstr "Historial de mantenimiento: %(name)s"',
        ),
        (
            '#, python-format\nmsgid "This type is used by %(c)s vehicles. Reassign them before deleting."\nmsgstr ""',
            '#, python-format\nmsgid "This type is used by %(c)s vehicles. Reassign them before deleting."\n'
            'msgstr "Este tipo está asignado a %(c)s vehículos. Reasígnalos antes de eliminar."',
        ),
    ]
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
    return text


def main() -> None:
    clear_fuzzy_entries(PO_PATH)
    raw = PO_PATH.read_text(encoding="utf-8")
    text = fill_multiline_header(raw)
    text = fill_multiline_entries(text)
    text = fill_python_format_msgstrs(text)
    text = fill_simple_msgstrs(text)
    PO_PATH.write_text(text, encoding="utf-8")
    apply_es_dict_to_po_file(PO_PATH, ES)
    print("Updated", PO_PATH)


if __name__ == "__main__":
    main()

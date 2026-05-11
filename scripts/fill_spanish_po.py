#!/usr/bin/env python3
"""
Fill Spanish msgstr entries in locale/es/LC_MESSAGES/django.po (stdlib only).
Run from repo dev/:  python scripts/fill_spanish_po.py
"""
from __future__ import annotations

import pathlib
import re

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
    return text


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
    ]
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
    return text


def main() -> None:
    raw = PO_PATH.read_text(encoding="utf-8")
    text = fill_multiline_header(raw)
    text = fill_multiline_entries(text)
    text = fill_python_format_msgstrs(text)
    text = fill_simple_msgstrs(text)
    PO_PATH.write_text(text, encoding="utf-8")
    print("Updated", PO_PATH)


if __name__ == "__main__":
    main()

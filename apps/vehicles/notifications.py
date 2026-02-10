"""
FR7: Email notifications for high/critical alerts.
Recipients: users with can_view_reports, respecting UserProfile.notification_settings.
"""

from django.core.mail import send_mail
from django.conf import settings


def send_alert_notification_emails(alert):
    """
    Send email to users who can view reports and have email/critical_alerts enabled.
    Call when a high or critical VehicleAlert is created.
    """
    if alert.severity not in ('high', 'critical'):
        return
    from apps.users.models import User

    recipients = []
    for u in User.objects.filter(is_active=True).select_related('profile'):
        if not u.can_view_reports():
            continue
        try:
            profile = u.profile
        except Exception:
            profile = None
        ns = (profile.notification_settings or {}) if profile else {}
        if not ns.get('email_enabled', True):
            continue
        if not ns.get('critical_alerts', True):
            continue
        if u.email:
            recipients.append(u.email)

    if not recipients:
        return

    subject = f'[FleetPredict] Alerta {alert.get_severity_display()}: {alert.vehicle.display_name}'
    message = (
        f'Vehículo: {alert.vehicle.display_name}\n'
        f'Tipo: {alert.get_alert_type_display()}\n'
        f'Severidad: {alert.get_severity_display()}\n'
        f'Mensaje: {alert.message}\n'
        f'Fecha: {alert.created_at}\n'
        '\nAccede a la aplicación para más detalles y acciones.'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.SERVER_EMAIL or 'noreply@fleetpredict.local'
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=True,
    )

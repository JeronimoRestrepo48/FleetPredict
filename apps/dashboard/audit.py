"""
FR27: Audit logging helper.
Call log_audit() from views after create/update/delete.
"""

from .models import AuditLog


def log_audit(request, action, model_name='', object_id='', message=''):
    """Record an audit log entry. request can be None (e.g. management command)."""
    user = request.user if request and hasattr(request, 'user') else None
    ip = None
    if request and hasattr(request, 'META'):
        raw = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
        if raw:
            ip = raw.split(',')[0].strip() if isinstance(raw, str) else str(raw)
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        message=message[:500] if message else '',
        ip_address=ip,
    )

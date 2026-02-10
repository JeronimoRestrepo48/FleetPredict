"""
PDF report generation using LaTeX (FR5 reportes).
Escapes user data for safe LaTeX injection (ciberseguridad).
"""

import os
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from jinja2 import Environment, select_autoescape


# Characters that must be escaped in LaTeX text
_LATEX_ESCAPE_MAP = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '^': r'\textasciicircum{}',
    '~': r'\textasciitilde{}',
}


def escape_latex(value):
    """Escape a string for safe inclusion in LaTeX. Prevents command injection."""
    if value is None:
        return ''
    s = str(value)
    for char, replacement in _LATEX_ESCAPE_MAP.items():
        s = s.replace(char, replacement)
    return s


def build_vehicle_report_context(vehicle, alerts_limit=10, tasks_limit=50):
    """Build context dict for vehicle maintenance report template."""
    from apps.maintenance.models import MaintenanceTask
    from apps.vehicles.models import VehicleAlert

    tasks = list(
        vehicle.maintenance_tasks.all()
        .order_by('-scheduled_date')[:tasks_limit]
    )
    alerts = list(
        VehicleAlert.objects.filter(vehicle=vehicle)
        .order_by('-created_at')[:alerts_limit]
    )
    last_telem = vehicle.telemetry_readings.order_by('-timestamp').first()

    return {
        'vehicle_name': escape_latex(vehicle.display_name),
        'license_plate': escape_latex(vehicle.license_plate),
        'vin': escape_latex(vehicle.vin),
        'vehicle_type': escape_latex(vehicle.vehicle_type.name if vehicle.vehicle_type else '—'),
        'current_mileage': vehicle.current_mileage or 0,
        'tasks': tasks,
        'alerts': alerts,
        'last_telemetry': last_telem,
        'escape': escape_latex,
    }


def build_fleet_report_context(vehicles_with_health, alerts_limit=5):
    """Build context for fleet summary report (optional)."""
    from apps.vehicles.models import VehicleAlert
    rows = []
    for v in vehicles_with_health:
        health = getattr(v, 'health_status', v.get_health_status() if hasattr(v, 'get_health_status') else 'green')
        next_task = v.maintenance_tasks.filter(status__in=['scheduled', 'overdue']).order_by('scheduled_date').first()
        last_alert = VehicleAlert.objects.filter(vehicle=v).order_by('-created_at').first()
        rows.append({
            'vehicle_name': escape_latex(v.display_name),
            'health': health,
            'last_alert': last_alert,
            'next_maintenance': next_task,
            'current_mileage': v.current_mileage or 0,
            'escape': escape_latex,
        })
    return {'rows': rows, 'escape': escape_latex}


def render_tex(template_name, context):
    """Render a .tex template with Jinja2. Template should be in templates/reports/."""
    template_path = Path(settings.BASE_DIR) / 'templates' / 'reports' / template_name
    if not template_path.exists():
        raise FileNotFoundError(f'Template not found: {template_path}')
    env = Environment(
        autoescape=select_autoescape(default_for_string=False),
        variable_start_string='{{',
        variable_end_string='}}',
        block_start_string='{%',
        block_end_string='%}',
    )
    env.filters['escape_latex'] = escape_latex
    with open(template_path, 'r', encoding='utf-8') as f:
        template = env.from_string(f.read())
    return template.render(**context)


def run_pdflatex(tex_content, out_basename='report'):
    """Run pdflatex on tex_content in a temp dir; return path to generated PDF or None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, f'{out_basename}.tex')
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        try:
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', out_basename],
                cwd=tmpdir,
                capture_output=True,
                timeout=30,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None
        pdf_path = os.path.join(tmpdir, f'{out_basename}.pdf')
        if not os.path.isfile(pdf_path):
            return None
        # Copy to a new temp file so we can return path after tmpdir is gone - actually we need to read bytes and return
        with open(pdf_path, 'rb') as f:
            return f.read()


def generate_vehicle_pdf(vehicle):
    """Generate PDF bytes for vehicle maintenance report, or None on failure."""
    context = build_vehicle_report_context(vehicle)
    tex = render_tex('maintenance_report_vehicle.tex.j2', context)
    return run_pdflatex(tex, 'vehicle_report')


def generate_fleet_pdf(vehicles_with_health):
    """Generate PDF bytes for fleet report, or None on failure."""
    context = build_fleet_report_context(vehicles_with_health)
    tex = render_tex('maintenance_report_fleet.tex.j2', context)
    return run_pdflatex(tex, 'fleet_report')

"""
PDF report generation using LaTeX.
Escapes user data for safe LaTeX injection.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import date

from django.conf import settings
from jinja2 import Environment, select_autoescape


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
    """Escape a string for safe inclusion in LaTeX."""
    if value is None:
        return ''
    s = str(value)
    for char, replacement in _LATEX_ESCAPE_MAP.items():
        s = s.replace(char, replacement)
    return s


def _get_logo_path():
    """Return absolute path to the logo PNG if it exists."""
    logo = Path(settings.BASE_DIR) / 'static' / 'img' / 'logo.png'
    if logo.exists():
        return str(logo)
    return ''


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
    health = vehicle.get_health_status()

    driver = vehicle.assigned_driver
    driver_name = driver.get_full_name() if driver else 'Not assigned'

    return {
        'vehicle_name': escape_latex(vehicle.display_name),
        'license_plate': escape_latex(vehicle.license_plate),
        'vin': escape_latex(vehicle.vin),
        'vehicle_type': escape_latex(vehicle.vehicle_type.name if vehicle.vehicle_type else 'N/A'),
        'vehicle_status': escape_latex(vehicle.get_status_display()),
        'current_mileage': vehicle.current_mileage or 0,
        'assigned_driver': escape_latex(driver_name),
        'health_status': health,
        'tasks': tasks,
        'alerts': alerts,
        'last_telemetry': last_telem,
        'report_date': date.today().strftime('%B %d, %Y'),
        'logo_path': _get_logo_path(),
        'escape': escape_latex,
    }


def build_fleet_report_context(vehicles_with_health, alerts_limit=5):
    """Build context for fleet summary report."""
    from apps.vehicles.models import VehicleAlert
    rows = []
    health_counts = {'green': 0, 'yellow': 0, 'red': 0}
    status_counts = {'active': 0, 'under_maintenance': 0, 'inactive': 0}

    for v in vehicles_with_health:
        health = v.get_health_status()
        health_counts[health] = health_counts.get(health, 0) + 1

        if v.status == 'active':
            status_counts['active'] += 1
        elif v.status == 'under_maintenance':
            status_counts['under_maintenance'] += 1
        else:
            status_counts['inactive'] += 1

        next_task = v.maintenance_tasks.filter(
            status__in=['scheduled', 'overdue']
        ).order_by('scheduled_date').first()
        last_alert = VehicleAlert.objects.filter(vehicle=v).order_by('-created_at').first()
        rows.append({
            'vehicle_name': escape_latex(v.display_name),
            'license_plate': escape_latex(v.license_plate),
            'health': health,
            'last_alert': last_alert,
            'next_maintenance': next_task,
            'current_mileage': v.current_mileage or 0,
        })

    total = len(vehicles_with_health)
    availability = round(status_counts['active'] / total * 100, 1) if total > 0 else 0

    return {
        'rows': rows,
        'total_vehicles': total,
        'active_count': status_counts['active'],
        'maintenance_count': status_counts['under_maintenance'],
        'inactive_count': status_counts['inactive'],
        'availability': availability,
        'health_green': health_counts.get('green', 0),
        'health_yellow': health_counts.get('yellow', 0),
        'health_red': health_counts.get('red', 0),
        'report_date': date.today().strftime('%B %d, %Y'),
        'logo_path': _get_logo_path(),
        'escape': escape_latex,
    }


def render_tex(template_name, context):
    """Render a .tex template with Jinja2."""
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
    """Run pdflatex on tex_content; return PDF bytes or None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, f'{out_basename}.tex')
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)

        logo_src = _get_logo_path()
        if logo_src:
            logo_dest = os.path.join(tmpdir, 'logo.png')
            shutil.copy2(logo_src, logo_dest)

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
        with open(pdf_path, 'rb') as f:
            return f.read()


def generate_vehicle_pdf(vehicle):
    """Generate PDF bytes for vehicle maintenance report."""
    context = build_vehicle_report_context(vehicle)
    if context.get('logo_path'):
        context['logo_path'] = 'logo.png'
    tex = render_tex('maintenance_report_vehicle.tex.j2', context)
    return run_pdflatex(tex, 'vehicle_report')


def generate_fleet_pdf(vehicles_with_health):
    """Generate PDF bytes for fleet report."""
    context = build_fleet_report_context(vehicles_with_health)
    if context.get('logo_path'):
        context['logo_path'] = 'logo.png'
    tex = render_tex('maintenance_report_fleet.tex.j2', context)
    return run_pdflatex(tex, 'fleet_report')

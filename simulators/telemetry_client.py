"""
Fleet telemetry simulator: 10 WebSocket clients sending real-time telemetry to the backend.
Each vehicle has a type-specific profile (speed, fuel, temperature, rpm, behavior).

Usage (from dev/):
  python -m simulators.telemetry_client [--url ws://127.0.0.1:8000/ws/telemetry/] [--interval 2] [--token TOKEN]

Requires: backend running with ASGI (e.g. daphne fleetpredict.asgi:application) and seed_simulated_fleet.
"""

import argparse
import asyncio
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent so we can use Django ORM to resolve vehicle IDs (optional)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Vehicle identifier and type profile name (must match seed_simulated_fleet)
VEHICLES = [
    ('SIM-001', 'Sedan'),
    ('SIM-002', 'Van'),
    ('SIM-003', 'Pickup'),
    ('SIM-004', 'Box Truck'),
    ('SIM-005', 'Bus'),
    ('SIM-006', 'Cargo Truck'),
    ('SIM-007', 'Motorcycle'),
    ('SIM-008', 'Taxi'),
    ('SIM-009', 'Delivery Van'),
    ('SIM-010', 'Ambulance'),
]

# Profile: speed_kmh (min, max), fuel_drain_per_tick, engine_temp (min, max), rpm (idle, driving), idle_prob
PROFILES = {
    'Sedan': {'speed': (20, 100), 'fuel_drain': 0.02, 'temp': (85, 98), 'rpm_idle': 800, 'rpm_drive': (1500, 3500), 'idle_prob': 0.1},
    'Van': {'speed': (15, 85), 'fuel_drain': 0.03, 'temp': (88, 100), 'rpm_idle': 750, 'rpm_drive': (1400, 3200), 'idle_prob': 0.15},
    'Pickup': {'speed': (10, 95), 'fuel_drain': 0.035, 'temp': (87, 102), 'rpm_idle': 700, 'rpm_drive': (1600, 3800), 'idle_prob': 0.12},
    'Box Truck': {'speed': (0, 70), 'fuel_drain': 0.04, 'temp': (90, 105), 'rpm_idle': 650, 'rpm_drive': (1800, 3000), 'idle_prob': 0.2},
    'Bus': {'speed': (0, 60), 'fuel_drain': 0.05, 'temp': (88, 102), 'rpm_idle': 600, 'rpm_drive': (1200, 2500), 'idle_prob': 0.25},
    'Cargo Truck': {'speed': (0, 80), 'fuel_drain': 0.06, 'temp': (92, 108), 'rpm_idle': 550, 'rpm_drive': (1400, 2800), 'idle_prob': 0.18},
    'Motorcycle': {'speed': (0, 120), 'fuel_drain': 0.025, 'temp': (80, 95), 'rpm_idle': 1200, 'rpm_drive': (3000, 6000), 'idle_prob': 0.08},
    'Taxi': {'speed': (0, 50), 'fuel_drain': 0.03, 'temp': (86, 98), 'rpm_idle': 750, 'rpm_drive': (1500, 3000), 'idle_prob': 0.4},
    'Delivery Van': {'speed': (5, 70), 'fuel_drain': 0.035, 'temp': (87, 100), 'rpm_idle': 700, 'rpm_drive': (1400, 3200), 'idle_prob': 0.3},
    'Ambulance': {'speed': (0, 110), 'fuel_drain': 0.055, 'temp': (90, 104), 'rpm_idle': 650, 'rpm_drive': (1600, 3500), 'idle_prob': 0.2},
}

# Base coordinates (Bogotá area) - each vehicle drifts slightly
BASE_LAT, BASE_LNG = 4.7110, -74.0721


def get_state(license_plate: str, profile_name: str, state: dict) -> dict:
    """Compute next telemetry state for this vehicle from its profile and previous state."""
    profile = PROFILES.get(profile_name, PROFILES['Sedan'])
    speed_min, speed_max = profile['speed']
    temp_min, temp_max = profile['temp']
    rpm_drive = profile['rpm_drive']

    # Initialize or advance state
    if 'fuel' not in state:
        state['fuel'] = round(random.uniform(30, 95), 2)
    if 'mileage' not in state:
        state['mileage'] = random.randint(5000, 80000)
    if 'lat' not in state:
        state['lat'] = BASE_LAT + random.uniform(-0.01, 0.01)
    if 'lng' not in state:
        state['lng'] = BASE_LNG + random.uniform(-0.01, 0.01)

    # Idle vs driving (taxi/bus have high idle_prob)
    is_idle = random.random() < profile['idle_prob']
    if is_idle:
        speed = 0
        rpm = profile['rpm_idle']
        temp = round(random.uniform(temp_min, (temp_min + temp_max) / 2), 2)
    else:
        speed = round(random.uniform(speed_min, speed_max), 2)
        rpm = random.randint(rpm_drive[0], rpm_drive[1])
        temp = round(random.uniform(temp_min, temp_max), 2)

    # Fuel drain
    state['fuel'] = max(5, state['fuel'] - profile['fuel_drain'] * (1 + speed / 80))
    state['mileage'] += max(0, int(speed * 0.001))  # tiny increment per tick
    # Slight position drift
    state['lat'] += random.uniform(-0.0001, 0.0001)
    state['lng'] += random.uniform(-0.0001, 0.0001)

    return {
        'license_plate': license_plate,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'speed_kmh': round(speed, 2),
        'fuel_level_pct': round(state['fuel'], 2),
        'engine_temperature_c': temp,
        'latitude': round(state['lat'], 6),
        'longitude': round(state['lng'], 6),
        'rpm': rpm,
        'mileage': state['mileage'],
        'voltage': round(12.0 + random.uniform(-0.3, 0.5), 2),
        'throttle_pct': round(0 if is_idle else random.uniform(15, 70), 2),
        'brake_status': is_idle or (speed < 5 and random.random() < 0.3),
    }


async def run_vehicle_client(license_plate: str, profile_name: str, url: str, interval: float, token: str | None):
    """Single vehicle loop: connect, then send telemetry every `interval` seconds."""
    try:
        import websockets
    except ImportError:
        print('Install websockets: pip install websockets', file=sys.stderr)
        return
    full_url = url if not token else f"{url}?token={token}"
    state = {}
    while True:
        try:
            async with websockets.connect(full_url, ping_interval=20, ping_timeout=10) as ws:
                print(f'[{license_plate}] connected', flush=True)
                while True:
                    payload = get_state(license_plate, profile_name, state)
                    await ws.send(json.dumps(payload))
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    try:
                        resp = json.loads(msg)
                        if not resp.get('ok'):
                            print(f'[{license_plate}] server error: {resp}', flush=True)
                    except Exception:
                        pass
                    await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f'[{license_plate}] connection error: {e}', flush=True)
            await asyncio.sleep(5)


async def main():
    parser = argparse.ArgumentParser(description='Fleet telemetry WebSocket simulators')
    parser.add_argument('--url', default='ws://127.0.0.1:8000/ws/telemetry/', help='WebSocket URL')
    parser.add_argument('--interval', type=float, default=2.0, help='Seconds between telemetry messages')
    parser.add_argument('--token', default=None, help='Optional token for ?token=')
    args = parser.parse_args()

    tasks = [
        asyncio.create_task(run_vehicle_client(plate, profile, args.url, args.interval, args.token))
        for plate, profile in VEHICLES
    ]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    print('Stopped.', flush=True)


if __name__ == '__main__':
    asyncio.run(main())

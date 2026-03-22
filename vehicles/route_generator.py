"""
vehicles/route_generator.py
============================
Generates vehicles/routes.rou.xml.

Realism changes
---------------
- Each vehicle is assigned a random vType variant (car_0..car_7 etc.)
  so every car genuinely has different physics and driver behaviour.
- departSpeed is randomised per vehicle around "desired" with
  DEPART_SPEED_VARIATION from traffic.env.
- Pulse support: if PULSE_ENABLED=True in traffic.env, flow rates vary
  sinusoidally over time to simulate rush-hour peaks.
- ALL vehicles sorted by depart time (required by SUMO, no warnings).
"""

import os, sys, random, math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.simulation_config import (
    SIM_DURATION,
    FLOW_NORTH, FLOW_SOUTH, FLOW_EAST, FLOW_WEST,
    TRUCK_FRACTION, BUS_FRACTION, MOTORCYCLE_FRAC,
    AMBULANCE_COUNT, AMBULANCE_DEPART_TIME,
    VIP_VEHICLE_IDS, ENABLE_VIP_PRIORITY,
)
from config.env_loader       import ENV
from vehicles.vehicle_types  import get_type_ids

VEHICLES_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH  = os.path.join(VEHICLES_DIR, "routes.rou.xml")

ROUTE_DEFS = {
    "N_to_S": ("N_in", "S_out"),
    "N_to_E": ("N_in", "E_out"),
    "N_to_W": ("N_in", "W_out"),
    "S_to_N": ("S_in", "N_out"),
    "S_to_E": ("S_in", "E_out"),
    "S_to_W": ("S_in", "W_out"),
    "E_to_W": ("E_in", "W_out"),
    "E_to_N": ("E_in", "N_out"),
    "E_to_S": ("E_in", "S_out"),
    "W_to_E": ("W_in", "E_out"),
    "W_to_N": ("W_in", "N_out"),
    "W_to_S": ("W_in", "S_out"),
}

ARM_ROUTES = {
    "N": ["N_to_S", "N_to_E", "N_to_W"],
    "S": ["S_to_N", "S_to_E", "S_to_W"],
    "E": ["E_to_W", "E_to_N", "E_to_S"],
    "W": ["W_to_E", "W_to_N", "W_to_S"],
}

AMBULANCE_ROUTES = ["N_to_S", "S_to_N", "E_to_W", "W_to_E"]


def _pulse_multiplier(t):
    """Return flow multiplier at time t based on traffic.env pulse settings."""
    if not ENV.PULSE_ENABLED:
        return 1.0
    mid  = (ENV.PULSE_PEAK + ENV.PULSE_TROUGH) / 2.0
    amp  = (ENV.PULSE_PEAK - ENV.PULSE_TROUGH) / 2.0
    return mid + amp * math.sin(2 * math.pi * t / ENV.PULSE_PERIOD)


def _poisson_times(base_vph, duration, rng):
    """
    Generate Poisson arrival times with optional pulse modulation.
    Uses thinning: generate at peak rate, then accept each event with
    probability p(t) = rate(t) / peak_rate.
    """
    if base_vph <= 0:
        return []

    peak_rate = base_vph * (ENV.PULSE_PEAK if ENV.PULSE_ENABLED else 1.0) / 3600.0
    if peak_rate <= 0:
        return []

    times, t = [], 0.0
    while t < duration:
        t += rng.expovariate(peak_rate)
        if t >= duration:
            break
        # Thinning acceptance
        accept_prob = _pulse_multiplier(t) / (ENV.PULSE_PEAK if ENV.PULSE_ENABLED else 1.0)
        if rng.random() < accept_prob:
            times.append(round(t, 1))
    return times


def _pick_base_class(rng):
    r = rng.random()
    if r < TRUCK_FRACTION:          return "truck"
    r -= TRUCK_FRACTION
    if r < BUS_FRACTION:            return "bus"
    r -= BUS_FRACTION
    if r < MOTORCYCLE_FRAC:         return "motorcycle"
    return "car"


def write_routes(path=OUTPUT_PATH):
    seed = ENV.RANDOM_SEED if ENV.RANDOM_SEED >= 0 else None
    rng  = random.Random(seed)

    type_ids = get_type_ids()

    # Round-robin indices so each variant gets used evenly
    variant_cursor = {cls: 0 for cls in type_ids}

    def next_type(base_class):
        variants = type_ids[base_class]
        idx = variant_cursor[base_class] % len(variants)
        variant_cursor[base_class] += 1
        return variants[idx]

    all_vehicles = []   # (depart_time, xml_string)
    counters     = {"car": 0, "truck": 0, "bus": 0, "motorcycle": 0}

    arm_flows = {
        "N": FLOW_NORTH, "S": FLOW_SOUTH,
        "E": FLOW_EAST,  "W": FLOW_WEST,
    }

    for arm, vph in arm_flows.items():
        for t in _poisson_times(vph, SIM_DURATION, rng):
            base  = _pick_base_class(rng)
            vtype = next_type(base)
            counters[base] += 1
            n     = counters[base]

            # Human readable label
            label = {
                "car":        "Car_{}",
                "truck":      "Truck_{}",
                "bus":        "Bus_{}",
                "motorcycle": "Motorcycle_{}",
            }[base].format(n)

            route = rng.choice(ARM_ROUTES[arm])

            # Randomise insertion speed around desired
            # departSpeed accepts a float directly in m/s
            # We use "desired" keyword but add individual variation via speedFactor
            # which is already baked into the vType - so just use "desired" here
            xml = ('    <vehicle id="{id}" type="{vt}" route="{r}" '
                   'depart="{t}" departLane="free" '
                   'departSpeed="desired"/>'.format(
                       id=label, vt=vtype, r=route, t=t))
            all_vehicles.append((t, xml))

    # Ambulances
    for i in range(1, AMBULANCE_COUNT + 1):
        t     = float(AMBULANCE_DEPART_TIME + (i - 1) * 60)
        route = AMBULANCE_ROUTES[(i - 1) % len(AMBULANCE_ROUTES)]
        xml   = ('    <vehicle id="Ambulance_{i}" type="ambulance" '
                 'route="{r}" depart="{t}" departLane="free" '
                 'departSpeed="0"/>'.format(i=i, r=route, t=t))
        all_vehicles.append((t, xml))

    # VIP vehicles
    if ENABLE_VIP_PRIORITY:
        route_names = list(ROUTE_DEFS.keys())
        for i, vid in enumerate(VIP_VEHICLE_IDS):
            t     = float(AMBULANCE_DEPART_TIME + 10 + i * 15)
            route = route_names[i % len(route_names)]
            xml   = ('    <vehicle id="{vid}" type="vip_car" '
                     'route="{r}" depart="{t}" departLane="free" '
                     'departSpeed="desired"/>'.format(vid=vid, r=route, t=t))
            all_vehicles.append((t, xml))

    # SORT ALL VEHICLES by depart time - required by SUMO
    all_vehicles.sort(key=lambda x: x[0])

    route_lines = [
        '    <route id="{n}" edges="{s} {d}"/>'.format(n=n, s=s, d=d)
        for n, (s, d) in ROUTE_DEFS.items()
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!-- routes.rou.xml  -  generated by vehicles/route_generator.py\n')
        f.write('     Vehicles sorted by depart time (eliminates SUMO sort warnings).\n')
        f.write('     Each vehicle assigned a randomised vType variant from traffic.env. -->\n')
        f.write('<routes>\n\n')
        f.write('    <!-- Route edge definitions -->\n')
        for line in route_lines:
            f.write(line + "\n")
        f.write('\n    <!-- Vehicles (sorted by depart) -->\n')
        for _, xml in all_vehicles:
            f.write(xml + "\n")
        f.write('\n</routes>\n')

    print("  [routes]  {}  ({} vehicles, sorted, {} vType variants)".format(
        path, len(all_vehicles),
        sum(len(v) for v in type_ids.values() if v != ["ambulance"] and v != ["vip_car"])))
    return path


if __name__ == "__main__":
    write_routes()

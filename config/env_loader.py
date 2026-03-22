"""
config/env_loader.py
====================
Parses traffic.env and exposes all realism variables as Python attributes.

Usage in any module:
    from config.env_loader import ENV
    sigma = ENV.CAR_SIGMA_MIN

The .env file format is:
    KEY = VALUE    # optional inline comment
    # full-line comment

All values are cast to float or bool automatically.
String values (True/False) become Python bools.
"""

import os

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "traffic.env")

# Defaults (used if traffic.env is missing or a key is absent)
_DEFAULTS = {
    "RANDOM_SEED":                42,
    "SPEED_FACTOR_MEAN":          1.00,
    "SPEED_FACTOR_STD":           0.12,
    "MIN_SPEED_FACTOR_CAR":       0.70,
    "MAX_SPEED_FACTOR_CAR":       1.30,
    "MIN_SPEED_FACTOR_HGV":       0.65,
    "MAX_SPEED_FACTOR_HGV":       1.05,
    "CAR_SIGMA_MIN":              0.20,
    "CAR_SIGMA_MAX":              0.70,
    "TRUCK_SIGMA_MIN":            0.10,
    "TRUCK_SIGMA_MAX":            0.40,
    "BUS_SIGMA_MIN":              0.05,
    "BUS_SIGMA_MAX":              0.25,
    "MOTO_SIGMA_MIN":             0.40,
    "MOTO_SIGMA_MAX":             0.90,
    "TAU_MIN":                    0.60,
    "TAU_MAX":                    1.80,
    "MIN_GAP_MIN":                1.20,
    "MIN_GAP_MAX":                4.50,
    "LC_STRATEGIC":               1.00,
    "LC_COOPERATIVE":             0.80,
    "LC_SPEED_GAIN":              0.10,
    "LC_KEEP_RIGHT":              0.80,
    "LC_LOOK_AHEAD":              3,
    "LC_IMPATIENCE":              0.30,
    "JUNCTION_MODEL_IGNORE_FPS":  0.00,
    "JUNCTION_MODEL_SIGMA_MINOR": 0.40,
    "ANTICIPATION_DIST":          80.0,
    "ACCEL_VARIATION":            0.20,
    "DECEL_VARIATION":            0.15,
    "DEPART_SPEED_VARIATION":     0.20,
    "OTHER_DRIVER_YIELD_PROB":    0.75,
    "YIELD_AWARENESS_DIST":       50.0,
    "PULSE_ENABLED":              False,
    "PULSE_PEAK":                 1.80,
    "PULSE_TROUGH":               0.40,
    "PULSE_PERIOD":               120.0,
}


def _cast(value_str):
    v = value_str.strip()
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v   # keep as string


def _load(path):
    result = dict(_DEFAULTS)
    if not os.path.exists(path):
        print("WARNING: traffic.env not found - using defaults")
        return result
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline comments
            if "#" in line:
                line = line[:line.index("#")].strip()
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            result[key.strip()] = _cast(val.strip())
    return result


class _Env:
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def __repr__(self):
        lines = ["traffic.env settings:"]
        for k, v in sorted(vars(self).items()):
            lines.append("  {:35s} = {}".format(k, v))
        return "\n".join(lines)


ENV = _Env(_load(_ENV_PATH))

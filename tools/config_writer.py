"""
tools/config_writer.py
======================
Writes two files that SUMO needs at launch:

  crossroads.sumocfg        (project root)
  network/detectors.add.xml (network sub-folder)

Path resolution rules
---------------------
SUMO resolves every path inside a file RELATIVE TO THAT FILE'S LOCATION.

  crossroads.sumocfg lives at project root, so:
    "network/crossroads.net.xml"  -> project_root/network/crossroads.net.xml  OK
    "output/trip_info.xml"        -> project_root/output/trip_info.xml         OK

  detectors.add.xml lives at project_root/network/, so:
    "../output/detectors.xml"     -> project_root/output/detectors.xml         OK
    "output/detectors.xml"        -> project_root/network/output/...           WRONG

This module is always called by run_simulation.py on every run, so the
sumocfg is always up-to-date with the latest simulation_config.py values.
"""

import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.simulation_config import (
    SIM_DURATION, SIM_STEP_LENGTH,
    TRIP_INFO_FILE, SUMMARY_FILE, OUTPUT_DIR,
)

PROJECT_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SUMOCFG_PATH  = os.path.join(PROJECT_ROOT, "crossroads.sumocfg")
DETECTOR_PATH = os.path.join(PROJECT_ROOT, "network", "detectors.add.xml")


def write_detectors(path=DETECTOR_PATH):
    """
    Four E1 induction-loop detectors, one per inbound arm, 50m before junction.
    These count vehicles and measure speed every 60 simulation seconds.
    Output is written to ../output/detectors.xml (relative to network/).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<additional>\n')
        for arm in ["N", "S", "E", "W"]:
            f.write('    <e1Detector id="det_{a}" lane="{a}_in_0" pos="-50" '
                    'freq="60" file="../output/detectors.xml" '
                    'friendlyPos="true"/>\n'.format(a=arm))
        f.write('</additional>\n')
    print("  [detectors] " + path)


def write_sumocfg(path=SUMOCFG_PATH):
    """
    Master SUMO configuration file.
    All paths here are relative to this file's location (project root).
    Re-generated on every run so it always reflects simulation_config.py.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<configuration>\n\n')

        f.write('    <input>\n')
        f.write('        <net-file         value="network/crossroads.net.xml"/>\n')
        f.write('        <route-files      value="vehicles/routes.rou.xml"/>\n')
        f.write('        <additional-files value="vehicles/vehicle_types.add.xml,'
                'network/detectors.add.xml"/>\n')
        f.write('    </input>\n\n')

        f.write('    <time>\n')
        f.write('        <begin       value="0"/>\n')
        f.write('        <end         value="{}"/>\n'.format(SIM_DURATION))
        f.write('        <step-length value="{}"/>\n'.format(SIM_STEP_LENGTH))
        f.write('    </time>\n\n')

        f.write('    <o>\n')
        f.write('        <tripinfo-output value="{}"/>\n'.format(TRIP_INFO_FILE))
        f.write('        <summary-output  value="{}"/>\n'.format(SUMMARY_FILE))
        f.write('    </o>\n\n')

        f.write('    <processing>\n')
        f.write('        <ignore-route-errors value="true"/>\n')
        f.write('        <time-to-teleport    value="-1"/>\n')
        f.write('    </processing>\n\n')

        f.write('    <report>\n')
        f.write('        <verbose     value="true"/>\n')
        f.write('        <no-step-log value="false"/>\n')
        f.write('    </report>\n\n')

        f.write('</configuration>\n')
    print("  [sumocfg]   " + path)


def write_all(tl_dur_path=None):
    write_detectors()
    write_sumocfg()


if __name__ == "__main__":
    write_all()

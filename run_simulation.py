"""
run_simulation.py
=================
Main entry point. Run this script to start the simulation.

What happens when you run this
-------------------------------
1. prepare()  - builds/loads all required files:
     - network:  nodes + edges -> netconvert -> crossroads.net.xml
     - vehicles: vehicle_types.add.xml, routes.rou.xml
     - config:   crossroads.sumocfg, detectors.add.xml
2. run()  - launches sumo or sumo-gui, connects via TraCI, then steps
     the simulation loop calling:
     - priority_manager.step()  each tick (ambulance/VIP/bus logic)
     - stats_collector.collect() each tick
3. On finish: stats_collector.save() writes output/stats.csv

Usage
------
  python run_simulation.py             # GUI mode (uses USE_GUI from config)
  python run_simulation.py --nogui     # force headless
  python run_simulation.py --rebuild   # delete and rebuild the road network

Prerequisites
-------------
  1. Install SUMO  https://sumo.dlr.de/docs/Installing/index.html
  2. set SUMO_HOME=C:\\path\\to\\sumo        (Windows)
     export SUMO_HOME=/path/to/sumo         (Linux / Mac)
  3. pip install traci
"""

import argparse, os, sys, subprocess

# --- SUMO_HOME ---------------------------------------------------------------
SUMO_HOME = os.environ.get("SUMO_HOME", "")
if SUMO_HOME:
    sys.path.append(os.path.join(SUMO_HOME, "tools"))
else:
    print("WARNING: SUMO_HOME is not set.")
    print("  Windows: set SUMO_HOME=C:\\Program Files (x86)\\Eclipse\\Sumo")
    print("  Linux:   export SUMO_HOME=/usr/share/sumo\n")

try:
    import traci
    import traci.exceptions
    _TRACI_OK = True
except ImportError:
    _TRACI_OK = False
    print("WARNING: traci not found. Run:  pip install traci\n")

# --- project imports ---------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.simulation_config import (
    SIM_DURATION, SIM_STEP_LENGTH, USE_GUI, GUI_DELAY, OUTPUT_DIR,
)
from network.build_network    import build as build_network
from vehicles.vehicle_types   import write_vehicle_types
from vehicles.route_generator import write_routes
from tools.config_writer      import write_all as write_config
from tools.priority_manager   import PriorityManager
from tools.stats_collector    import StatsCollector

NET_FILE = os.path.join(PROJECT_ROOT, "network", "crossroads.net.xml")
SUMOCFG  = os.path.join(PROJECT_ROOT, "crossroads.sumocfg")


# -----------------------------------------------------------------------------
def prepare(force_rebuild=False):
    print("=" * 55)
    print("  SUMO Crossroads - Preparing files")
    print("=" * 55)

    if force_rebuild or not os.path.exists(NET_FILE):
        ok = build_network()
        if not ok:
            sys.exit("Network build failed. Is netconvert on your PATH?")
    else:
        print("  [network]   Already built (--rebuild to force rebuild)")

    write_vehicle_types()
    write_routes()
    write_config()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\nAll files ready.\n")


# -----------------------------------------------------------------------------
def run(use_gui):
    if not _TRACI_OK:
        sys.exit("Cannot run: traci not available. Run:  pip install traci")

    binary = "sumo-gui" if use_gui else "sumo"
    try:
        subprocess.run([binary, "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit("ERROR: '{}' not found. Is SUMO installed and on PATH?".format(binary))

    cmd = [binary, "-c", SUMOCFG]
    if use_gui:
        cmd += ["--delay", str(GUI_DELAY)]

    print("  Launching: " + " ".join(cmd))
    traci.start(cmd)

    priority = PriorityManager()
    stats    = StatsCollector()
    total    = int(SIM_DURATION / SIM_STEP_LENGTH)
    step     = 0

    print("  Running {}s simulation ({} steps)...\n".format(SIM_DURATION, total))

    try:
        while traci.simulation.getMinExpectedNumber() > 0 or step < total:
            traci.simulationStep()
            priority.step()
            stats.collect()
            step += 1
            if step % 500 == 0:
                t = traci.simulation.getTime()
                n = len(traci.vehicle.getIDList())
                print("    t={:6.1f}s  vehicles in network: {}".format(t, n))
    except traci.exceptions.FatalTraCIError:
        print("  TraCI closed (GUI closed or simulation ended normally).")
    finally:
        try:
            traci.close()
        except Exception:
            pass
        stats.save()

    print("\nSimulation complete.")


# -----------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(
        description="SUMO 4-lane crossroads simulation")
    p.add_argument("--nogui",   action="store_true",
                   help="Run without GUI (headless)")
    p.add_argument("--rebuild", action="store_true",
                   help="Rebuild road network before running")
    args = p.parse_args()

    prepare(force_rebuild=args.rebuild)
    run(use_gui=USE_GUI and not args.nogui)


if __name__ == "__main__":
    main()

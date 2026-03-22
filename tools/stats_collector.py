"""
tools/stats_collector.py
=========================
Collects per-step network statistics via TraCI and saves them to CSV.
Called once per step from run_simulation.py after the step executes.

Output: output/stats.csv
Columns:
  step              simulation time in seconds
  vehicles_total    number of vehicles currently in the network
  vehicles_waiting  vehicles with speed < 0.1 m/s (effectively stopped)
  mean_speed_ms     average speed across all vehicles in m/s
  tl_phase          current traffic light phase index at junction J
  ambulances_active semicolon-separated IDs of ambulances currently in network
"""

import csv, os, sys
from collections import defaultdict

try:
    import traci
    _TRACI = True
except ImportError:
    _TRACI = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.simulation_config import (
    COLLECT_STATISTICS, STATS_CSV, OUTPUT_DIR, WARMUP_STEPS,
)

JUNCTION_ID = "J"


class StatsCollector:

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._rows  = []
        self._step  = 0
        self._sums  = defaultdict(list)

    def collect(self):
        if not _TRACI or not COLLECT_STATISTICS:
            return
        self._step += 1
        if self._step < WARMUP_STEPS:
            return

        t   = traci.simulation.getTime()
        ids = traci.vehicle.getIDList()
        n   = len(ids)

        speeds  = [traci.vehicle.getSpeed(v) for v in ids]
        waiting = sum(1 for s in speeds if s < 0.1)
        mean_s  = round(sum(speeds) / n, 3) if n > 0 else 0.0

        try:
            phase = traci.trafficlight.getPhase(JUNCTION_ID)
        except Exception:
            phase = -1

        ambs = [v for v in ids if traci.vehicle.getTypeID(v) == "ambulance"]

        self._rows.append({
            "step":              t,
            "vehicles_total":    n,
            "vehicles_waiting":  waiting,
            "mean_speed_ms":     mean_s,
            "tl_phase":          phase,
            "ambulances_active": ";".join(ambs),
        })
        self._sums["speed"].append(mean_s)
        self._sums["wait"].append(waiting)

    def save(self):
        if not COLLECT_STATISTICS or not self._rows:
            return
        with open(STATS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self._rows[0].keys()))
            writer.writeheader()
            writer.writerows(self._rows)
        print("  [stats]  {} ({} rows)".format(STATS_CSV, len(self._rows)))

        speeds = self._sums["speed"]
        waits  = self._sums["wait"]
        if speeds:
            avg_s = sum(speeds) / len(speeds)
            avg_w = sum(waits)  / len(waits)
            print("\n" + "-" * 50)
            print("  Simulation summary")
            print("-" * 50)
            print("  Avg speed  : {:.2f} m/s  ({:.1f} km/h)".format(
                avg_s, avg_s * 3.6))
            print("  Avg waiting: {:.1f} vehicles".format(avg_w))
            print("-" * 50)

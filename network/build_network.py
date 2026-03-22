"""
network/build_network.py
========================
Responsible for creating all road geometry files and compiling them
into a SUMO network via the netconvert tool.

What it produces
----------------
  network/crossroads.nod.xml  - the 5 junction nodes (J, N, S, E, W)
  network/crossroads.edg.xml  - 8 road edges (inbound + outbound per arm)
  network/crossroads.net.xml  - the compiled SUMO network (binary-like XML)

Traffic light strategy
----------------------
Traffic light state strings (e.g. "GrGr...") depend on the exact number
of internal junction links, which netconvert calculates automatically.
We pass --tls.green.time / --tls.yellow.time / --tls.red.time directly
to netconvert so it bakes the correct durations in without us needing to
guess state string lengths.
"""

import os, sys, subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.simulation_config import (
    ROAD_LENGTH, LANE_WIDTH, LANES_PER_ROAD, SPEED_LIMIT_MS,
    TL_GREEN_DURATION, TL_YELLOW_DURATION, TL_RED_DURATION,
)

NETWORK_DIR    = os.path.dirname(os.path.abspath(__file__))
LANES_EACH_WAY = max(1, LANES_PER_ROAD // 2)


def write_nodes(path):
    """
    Five nodes:
      J - the central junction (traffic-light controlled)
      N, S, E, W - the far ends of each road arm (simple priority nodes)
    Coordinates place J at the origin; arms extend by ROAD_LENGTH in each direction.
    """
    h = ROAD_LENGTH
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<nodes>\n')
        f.write('    <node id="J" x="0"    y="0"    type="traffic_light"/>\n')
        f.write('    <node id="N" x="0"    y="{}"   type="priority"/>\n'.format(h))
        f.write('    <node id="S" x="0"    y="-{}"  type="priority"/>\n'.format(h))
        f.write('    <node id="E" x="{}"   y="0"    type="priority"/>\n'.format(h))
        f.write('    <node id="W" x="-{}"  y="0"    type="priority"/>\n'.format(h))
        f.write('</nodes>\n')
    print("  [nodes]  " + path)


def write_edges(path):
    """
    Eight directed edges - one inbound and one outbound per arm.
      N_in  : North endpoint -> Junction   (vehicles entering from North)
      N_out : Junction -> North endpoint   (vehicles leaving toward North)
      (same pattern for S, E, W)
    numLanes = LANES_EACH_WAY (half of LANES_PER_ROAD per direction).
    """
    n, s, w = LANES_EACH_WAY, SPEED_LIMIT_MS, LANE_WIDTH
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<edges>\n')
        for arm in ["N", "S", "E", "W"]:
            f.write('    <edge id="{a}_in"  from="{a}" to="J"  '
                    'numLanes="{n}" speed="{s}" width="{w}" '
                    'spreadType="center"/>\n'.format(a=arm, n=n, s=s, w=w))
            f.write('    <edge id="{a}_out" from="J"  to="{a}" '
                    'numLanes="{n}" speed="{s}" width="{w}" '
                    'spreadType="center"/>\n'.format(a=arm, n=n, s=s, w=w))
        f.write('</edges>\n')
    print("  [edges]  " + path)


def run_netconvert(nod, edg, out):
    """
    Calls the SUMO netconvert tool to compile nodes + edges into a full
    network file. Traffic light programmes are auto-generated with the
    timing values from simulation_config.py.
    """
    cmd = [
        "netconvert",
        "--node-files",              nod,
        "--edge-files",              edg,
        "--output-file",             out,
        "--no-turnarounds",          "true",
        "--junctions.corner-detail", "5",
        "--tls.default-type",        "static",
        "--tls.green.time",          str(TL_GREEN_DURATION),
        "--tls.yellow.time",         str(TL_YELLOW_DURATION),
        "--tls.red.time",            str(TL_RED_DURATION),
    ]
    print("  [netconvert] running ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("  [netconvert] FAILED:\n" + r.stderr)
        return False
    print("  [netconvert] OK -> " + out)
    return True


def build():
    """Entry point called by run_simulation.py."""
    nod = os.path.join(NETWORK_DIR, "crossroads.nod.xml")
    edg = os.path.join(NETWORK_DIR, "crossroads.edg.xml")
    net = os.path.join(NETWORK_DIR, "crossroads.net.xml")

    print("Building network ...")
    write_nodes(nod)
    write_edges(edg)
    ok = run_netconvert(nod, edg, net)
    if ok:
        print("Network build complete.\n")
    return ok


if __name__ == "__main__":
    build()

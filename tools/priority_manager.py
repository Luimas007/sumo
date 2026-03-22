"""
tools/priority_manager.py
==========================
Applies real-time priority rules each simulation step via TraCI.

Three independent modes (toggle in simulation_config.py):
  AMBULANCE PRIORITY  : all signals go green when ambulance is near
  BUS PRIORITY        : extends green for approaching bus
  VIP PRIORITY        : switches phase to green for VIP approach arm

Yielding behaviour (controlled by traffic.env):
  OTHER_DRIVER_YIELD_PROB  : probability a nearby vehicle yields to ambulance
  YIELD_AWARENESS_DIST     : metres at which drivers notice the siren

Tunable constants (edit here):
  DETECT_DIST  : metres from junction centre to scan for priority vehicles
  BUS_EXTEND   : extra green seconds granted to a bus
"""

import os, sys

try:
    import traci, traci.exceptions
    _TRACI = True
except ImportError:
    _TRACI = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.simulation_config import (
    ENABLE_AMBULANCE_PRIORITY,
    ENABLE_BUS_PRIORITY,
    ENABLE_VIP_PRIORITY,
    VIP_VEHICLE_IDS,
)
from config.env_loader import ENV

JUNCTION_ID  = "J"
DETECT_DIST  = 60.0
BUS_EXTEND   = 10

ARM_TO_PHASE = {"N": 0, "S": 0, "E": 2, "W": 2}
ARM_TO_EDGE  = {"N": "N_in", "S": "S_in", "E": "E_in", "W": "W_in"}


class PriorityManager:

    def __init__(self):
        self._amb_active    = False
        self._bus_ext_rem   = 0
        self._original_prog = "0"
        self._yielding      = set()   # vehicle IDs currently yielding

    def step(self):
        if not _TRACI:
            return
        if ENABLE_AMBULANCE_PRIORITY:
            self._handle_ambulance()
        if ENABLE_BUS_PRIORITY:
            self._handle_bus()
        if ENABLE_VIP_PRIORITY:
            self._handle_vip()

    def _handle_ambulance(self):
        nearby = self._nearby_of_type("ambulance")
        if nearby and not self._amb_active:
            try:
                self._original_prog = traci.trafficlight.getProgram(JUNCTION_ID)
                state     = traci.trafficlight.getRedYellowGreenState(JUNCTION_ID)
                all_green = "G" * len(state)
                traci.trafficlight.setRedYellowGreenState(JUNCTION_ID, all_green)
                self._amb_active = True
                print("    [PRIORITY] {} approaching - ALL GREEN".format(nearby[0]))
                self._make_vehicles_yield(nearby[0])
            except Exception as e:
                print("    [PRIORITY] Ambulance override error: " + str(e))
        elif not nearby and self._amb_active:
            try:
                traci.trafficlight.setProgram(JUNCTION_ID, self._original_prog)
                self._amb_active = False
                self._restore_yielding()
                print("    [PRIORITY] Ambulance cleared - normal signals resumed")
            except Exception as e:
                print("    [PRIORITY] Signal restore error: " + str(e))

    def _make_vehicles_yield(self, amb_id):
        """
        With probability OTHER_DRIVER_YIELD_PROB, slow down vehicles
        within YIELD_AWARENESS_DIST of the ambulance to simulate yielding.
        """
        import random
        rng = random.Random()
        try:
            ax, ay = traci.vehicle.getPosition(amb_id)
        except Exception:
            return
        for vid in traci.vehicle.getIDList():
            if vid == amb_id:
                continue
            try:
                x, y = traci.vehicle.getPosition(vid)
                dist = ((x - ax)**2 + (y - ay)**2) ** 0.5
                if dist < ENV.YIELD_AWARENESS_DIST:
                    if rng.random() < ENV.OTHER_DRIVER_YIELD_PROB:
                        traci.vehicle.setMaxSpeed(vid, 1.0)
                        self._yielding.add(vid)
            except Exception:
                pass

    def _restore_yielding(self):
        for vid in list(self._yielding):
            try:
                traci.vehicle.setMaxSpeed(vid, -1)   # -1 = restore type default
            except Exception:
                pass
        self._yielding.clear()

    def _handle_bus(self):
        nearby = self._nearby_of_type("bus")
        if nearby and self._bus_ext_rem == 0:
            try:
                phase = traci.trafficlight.getPhase(JUNCTION_ID)
                if phase in (0, 2):
                    remaining = (traci.trafficlight.getNextSwitch(JUNCTION_ID)
                                 - traci.simulation.getTime())
                    traci.trafficlight.setPhaseDuration(
                        JUNCTION_ID, remaining + BUS_EXTEND)
                    self._bus_ext_rem = int(BUS_EXTEND / 0.1)
                    print("    [PRIORITY] Bus {} - green extended {}s".format(
                        nearby[0], BUS_EXTEND))
            except Exception:
                pass
        if self._bus_ext_rem > 0:
            self._bus_ext_rem -= 1

    def _handle_vip(self):
        try:
            active = set(traci.vehicle.getIDList())
        except Exception:
            return
        for vid in VIP_VEHICLE_IDS:
            if vid not in active:
                continue
            arm  = self._arm_of(vid)
            dist = self._dist_to_junction(vid)
            if arm and dist is not None and dist < DETECT_DIST:
                target = ARM_TO_PHASE.get(arm)
                try:
                    if (target is not None
                            and traci.trafficlight.getPhase(JUNCTION_ID) != target):
                        traci.trafficlight.setPhase(JUNCTION_ID, target)
                        print("    [PRIORITY] VIP {} on {} arm -> phase {}".format(
                            vid, arm, target))
                except Exception:
                    pass

    def _nearby_of_type(self, vtype):
        result = []
        try:
            for vid in traci.vehicle.getIDList():
                if traci.vehicle.getTypeID(vid) == vtype:
                    d = self._dist_to_junction(vid)
                    if d is not None and d < DETECT_DIST:
                        result.append(vid)
        except Exception:
            pass
        return result

    def _dist_to_junction(self, vid):
        try:
            x, y = traci.vehicle.getPosition(vid)
            return (x * x + y * y) ** 0.5
        except Exception:
            return None

    def _arm_of(self, vid):
        try:
            edge = traci.vehicle.getRoadID(vid)
            for arm, inbound in ARM_TO_EDGE.items():
                if edge == inbound:
                    return arm
        except Exception:
            pass
        return None

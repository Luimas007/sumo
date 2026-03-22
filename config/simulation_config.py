# =============================================================================
#  config/simulation_config.py
#
#  THE ONLY FILE YOU NEED TO EDIT to change simulation behaviour.
#  Every variable here is read by the other modules at runtime.
#  After changing anything, just re-run:  python run_simulation.py --rebuild
# =============================================================================

# -----------------------------------------------------------------------------
#  SIMULATION TIMING
#  SIM_DURATION      : how many real-world seconds the simulation covers
#  SIM_STEP_LENGTH   : time resolution - smaller = smoother but slower
#  WARMUP_STEPS      : steps discarded before stats collection begins
# -----------------------------------------------------------------------------
SIM_DURATION      = 300    # seconds
SIM_STEP_LENGTH   = 0.1    # seconds per step
WARMUP_STEPS      = 50     # steps

# -----------------------------------------------------------------------------
#  ROAD GEOMETRY
#  LANES_PER_ROAD    : total lanes on each road arm (must be even, min 2)
#                      e.g. 4 = 2 lanes inbound + 2 lanes outbound
#  LANE_WIDTH        : width of a single lane in metres
#  ROAD_LENGTH       : distance from the junction centre to each arm end
#  SPEED_LIMIT_MS    : speed limit in metres/second (13.89 m/s = 50 km/h)
# -----------------------------------------------------------------------------
LANES_PER_ROAD    = 4
LANE_WIDTH        = 3.2
ROAD_LENGTH       = 200
SPEED_LIMIT_MS    = 13.89

# -----------------------------------------------------------------------------
#  TRAFFIC FLOW  (vehicles per hour entering from each direction)
#  Increase to model congestion.  Decrease for light traffic.
#  Flows use a Poisson process so arrivals are random but average to these.
# -----------------------------------------------------------------------------
FLOW_NORTH        = 400
FLOW_SOUTH        = 400
FLOW_EAST         = 300
FLOW_WEST         = 300

# -----------------------------------------------------------------------------
#  VEHICLE MIX  (fractions of total flow - must sum to <= 1.0)
#  The remainder automatically becomes standard cars.
#  Example: 0.10 + 0.05 + 0.08 = 0.23, so 77% of vehicles are cars.
# -----------------------------------------------------------------------------
TRUCK_FRACTION    = 0.10
BUS_FRACTION      = 0.05
MOTORCYCLE_FRAC   = 0.08

# -----------------------------------------------------------------------------
#  AMBULANCE SETTINGS
#  AMBULANCE_COUNT       : total ambulances injected during the simulation
#  AMBULANCE_SPEED_MS    : top speed (22.22 m/s = 80 km/h)
#  AMBULANCE_DEPART_TIME : simulation second when Ambulance_1 enters;
#                          each subsequent ambulance is spaced 60s later
# -----------------------------------------------------------------------------
AMBULANCE_COUNT       = 2
AMBULANCE_SPEED_MS    = 22.22
AMBULANCE_DEPART_TIME = 30

# -----------------------------------------------------------------------------
#  PRIORITY TOGGLES
#  These are the key experiment switches.
#
#  ENABLE_AMBULANCE_PRIORITY : when True, as an ambulance approaches the
#    junction all signals switch to green clearing its path, then return
#    to normal once it clears. Set False to observe unassisted ambulance travel.
#
#  ENABLE_BUS_PRIORITY : when True, an approaching bus extends the current
#    green phase by BUS_EXTEND seconds (defined in priority_manager.py).
#
#  ENABLE_VIP_PRIORITY : when True, vehicles whose IDs are in VIP_VEHICLE_IDS
#    get a green wave on their approach arm.
#
#  VIP_VEHICLE_IDS : list of vehicle IDs to treat as VIP. These vehicles
#    are gold-coloured in the GUI. Only active when ENABLE_VIP_PRIORITY=True.
# -----------------------------------------------------------------------------
ENABLE_AMBULANCE_PRIORITY = True
ENABLE_BUS_PRIORITY       = False
ENABLE_VIP_PRIORITY       = False

VIP_VEHICLE_IDS = ["VIP_Car_1", "VIP_Car_2"]

# -----------------------------------------------------------------------------
#  TRAFFIC LIGHT TIMING (seconds)
#  These are passed directly to netconvert when building the network.
#  Run  python run_simulation.py --rebuild  after changing these.
# -----------------------------------------------------------------------------
TL_GREEN_DURATION  = 30
TL_YELLOW_DURATION = 4
TL_RED_DURATION    = 30

# -----------------------------------------------------------------------------
#  DRIVER BEHAVIOUR  (per vehicle class)
#  MAX_SPEED  : top speed in m/s
#  ACCEL      : acceleration in m/s^2
#  DECEL      : braking deceleration in m/s^2
#  SIGMA      : driver imperfection 0.0 (robot) to 1.0 (very erratic)
#  TAU        : reaction time in seconds
#  MIN_GAP    : minimum gap to vehicle ahead in metres (cars only)
# -----------------------------------------------------------------------------
CAR_MAX_SPEED   = 13.89;  CAR_ACCEL  = 2.6;  CAR_DECEL  = 4.5
CAR_SIGMA       = 0.5;    CAR_TAU    = 1.0;  CAR_MIN_GAP = 2.5

TRUCK_MAX_SPEED = 9.72;   TRUCK_ACCEL = 1.2; TRUCK_DECEL = 3.5; TRUCK_SIGMA = 0.3
BUS_MAX_SPEED   = 11.11;  BUS_ACCEL   = 1.5; BUS_DECEL   = 4.0; BUS_SIGMA   = 0.2
MOTO_MAX_SPEED  = 15.28;  MOTO_ACCEL  = 3.5; MOTO_DECEL  = 6.0; MOTO_SIGMA  = 0.8

# -----------------------------------------------------------------------------
#  OUTPUT SETTINGS
#  All output files are written to OUTPUT_DIR (relative to project root).
#  COLLECT_STATISTICS : set False to skip CSV writing (faster headless runs)
# -----------------------------------------------------------------------------
COLLECT_STATISTICS = True
OUTPUT_DIR         = "output"
STATS_CSV          = "output/stats.csv"
TRIP_INFO_FILE     = "output/trip_info.xml"
SUMMARY_FILE       = "output/summary.xml"

# -----------------------------------------------------------------------------
#  GUI SETTINGS
#  USE_GUI    : True = launch sumo-gui (visual), False = headless sumo
#  GUI_DELAY  : milliseconds between rendered frames (increase to slow down)
# -----------------------------------------------------------------------------
USE_GUI    = True
GUI_DELAY  = 50

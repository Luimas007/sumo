# SUMO 4-Lane Crossroads Simulation

A fully randomised, real-world traffic simulation of a 4-arm cross-junction.
Every driver behaves differently. Speeds vary. Lane changes are probabilistic.
Ambulances clear corridors. Everything is tweakable without touching Python.

---

## Quick Start

```
1. Install SUMO        https://sumo.dlr.de/docs/Installing/index.html
2. Set SUMO_HOME:
     Windows:  set SUMO_HOME=C:\Program Files (x86)\Eclipse\Sumo
     Linux:    export SUMO_HOME=/usr/share/sumo
3. pip install traci
4. python run_simulation.py
```

---

## Project Layout

```
sumo_crossroads/
|
+-- run_simulation.py          ENTRY POINT - run this
+-- traffic.env                REALISM SETTINGS - edit for real-world feel
+-- crossroads.sumocfg         Auto-generated SUMO master config
+-- requirements.txt
+-- README.md
|
+-- config/
|   +-- simulation_config.py  Geometry, flows, TL timing, toggles
|   +-- env_loader.py         Parses traffic.env into Python attributes
|
+-- network/
|   +-- build_network.py      Generates road geometry, calls netconvert
|   +-- crossroads.nod.xml    Auto-generated: junction nodes
|   +-- crossroads.edg.xml    Auto-generated: road edges
|   +-- crossroads.net.xml    Auto-generated: compiled SUMO network
|   +-- detectors.add.xml     Auto-generated: induction-loop sensors
|
+-- vehicles/
|   +-- vehicle_types.py      Generates 8 randomised driver profiles per class
|   +-- vehicle_types.add.xml Auto-generated: all vType definitions
|   +-- route_generator.py    Creates vehicle schedules with random assignment
|   +-- routes.rou.xml        Auto-generated: every vehicle sorted by depart
|
+-- tools/
|   +-- config_writer.py      Writes crossroads.sumocfg + detectors file
|   +-- priority_manager.py   Ambulance/VIP/bus priority + yielding logic
|   +-- stats_collector.py    Per-step metrics -> output/stats.csv
|
+-- output/
    +-- stats.csv             Step-by-step: speed, waiting, TL phase
    +-- trip_info.xml         Per-vehicle journey data
    +-- summary.xml           SUMO per-step network summary
    +-- detectors.xml         Induction-loop counts per minute
```

---

## Two Config Files - What Goes Where

### simulation_config.py  (road structure + experiment toggles)
Edit this for: lane counts, road length, speed limits, traffic volumes,
vehicle mix fractions, ambulance settings, priority on/off, TL timing.
After changing geometry or TL timing: re-run with --rebuild.

### traffic.env  (driver realism + randomness)
Edit this for: how erratic drivers are, lane-change aggressiveness,
speed variation, reaction times, following gaps, yielding to ambulances,
rush-hour pulses, junction behaviour. No --rebuild needed.

---

## File-by-File Reference

### run_simulation.py
Single entry point. Calls prepare() then run().
  prepare() - builds/regenerates all XML files
  run()     - launches sumo-gui, TraCI loop, priority + stats each step

```
python run_simulation.py             # GUI (default)
python run_simulation.py --nogui     # headless
python run_simulation.py --rebuild   # force rebuild road network
```

---

### config/simulation_config.py

| Variable              | Default  | Notes                                  |
|-----------------------|----------|----------------------------------------|
| SIM_DURATION          | 300 s    | Total simulated seconds                |
| SIM_STEP_LENGTH       | 0.1 s    | Step size - lower = smoother           |
| LANES_PER_ROAD        | 4        | Total per arm (2 in + 2 out). --rebuild|
| ROAD_LENGTH           | 200 m    | Arm length. --rebuild to apply         |
| SPEED_LIMIT_MS        | 13.89    | 50 km/h. --rebuild to apply            |
| FLOW_NORTH/S/E/W      | 300-400  | Vehicles/hour per arm                  |
| TRUCK_FRACTION        | 0.10     | Fraction of flow that is trucks        |
| BUS_FRACTION          | 0.05     | Fraction that is buses                 |
| MOTORCYCLE_FRAC       | 0.08     | Fraction that is motorcycles           |
| AMBULANCE_COUNT       | 2        | Ambulances in simulation               |
| AMBULANCE_DEPART_TIME | 30 s     | When first ambulance enters            |
| ENABLE_AMBULANCE_PRIORITY | True | All-green when ambulance approaches    |
| ENABLE_BUS_PRIORITY   | False    | Extend green for approaching bus       |
| ENABLE_VIP_PRIORITY   | False    | Green wave for VIP_Car_N vehicles      |
| TL_GREEN_DURATION     | 30 s     | --rebuild to apply                     |
| TL_YELLOW_DURATION    | 4 s      | --rebuild to apply                     |
| TL_RED_DURATION       | 30 s     | --rebuild to apply                     |
| USE_GUI               | True     | False = headless                       |

---

### traffic.env  (the realism control panel)

#### Randomness
| Variable        | Default | Effect                                           |
|-----------------|---------|--------------------------------------------------|
| RANDOM_SEED     | 42      | Change integer for different pattern. -1 = new seed every run |

#### Speed Variation
Real drivers don't all drive at the speed limit. Each vehicle gets a
personal speed multiplier drawn from a normal distribution.

| Variable             | Default | Effect                                      |
|----------------------|---------|---------------------------------------------|
| SPEED_FACTOR_MEAN    | 1.00    | Average speed as fraction of limit          |
| SPEED_FACTOR_STD     | 0.12    | Spread - higher = more variation            |
| MIN_SPEED_FACTOR_CAR | 0.70    | No car will go below 70% of limit           |
| MAX_SPEED_FACTOR_CAR | 1.30    | No car will go above 130% of limit          |
| MIN/MAX_SPEED_FACTOR_HGV | 0.65/1.05 | Trucks and buses are more constrained |

Example: set SPEED_FACTOR_MEAN=1.08, SPEED_FACTOR_STD=0.18 to simulate
an aggressive arterial road where most drivers slightly exceed the limit.

#### Driver Imperfection (sigma)
Controls random speed fluctuations within the car-following model.
0.0 = robot. 1.0 = very erratic. Each vehicle draws from a range.

| Variable        | Default    | Effect                             |
|-----------------|------------|------------------------------------|
| CAR_SIGMA_MIN   | 0.20       | Most careful car driver            |
| CAR_SIGMA_MAX   | 0.70       | Most erratic car driver            |
| TRUCK_SIGMA_MIN | 0.10       | Professional drivers are steadier  |
| MOTO_SIGMA_MAX  | 0.90       | Motorcyclists are most erratic     |

#### Reaction Time (tau) - seconds
| Variable | Default | Effect                                              |
|----------|---------|-----------------------------------------------------|
| TAU_MIN  | 0.60 s  | Alertest driver - reacts in 0.6s                    |
| TAU_MAX  | 1.80 s  | Slowest driver - reacts in 1.8s                     |

Set TAU_MAX=2.5 to model distracted/fatigued drivers.

#### Following Distance (minGap) - metres
| Variable    | Default | Effect                                          |
|-------------|---------|----------------------------------------------- |
| MIN_GAP_MIN | 1.20 m  | Closest tailgater                               |
| MIN_GAP_MAX | 4.50 m  | Most cautious driver                            |

#### Lane Change Behaviour
These are the most impactful variables for road realism.

| Variable        | Default | Effect                                              |
|-----------------|---------|-----------------------------------------------------|
| LC_STRATEGIC    | 1.00    | Willingness to change for a better route (0-1)      |
| LC_COOPERATIVE  | 0.80    | Willingness to let others change lanes (0-1)        |
| LC_SPEED_GAIN   | 0.10    | Min speed gain needed to trigger overtake (0-1)     |
| LC_KEEP_RIGHT   | 0.80    | Desire to return to right lane after overtaking (0-1)|
| LC_IMPATIENCE   | 0.30    | How quickly impatience grows at red lights (0-1)    |

To simulate aggressive urban driving:
  LC_SPEED_GAIN = 0.02   (change for tiny speed advantage)
  LC_COOPERATIVE = 0.40  (less yielding to others)
  LC_KEEP_RIGHT  = 0.30  (hogging the fast lane)

To simulate polite motorway driving:
  LC_COOPERATIVE = 0.95
  LC_KEEP_RIGHT  = 0.95
  LC_SPEED_GAIN  = 0.20

#### Junction Behaviour
| Variable                    | Default | Effect                                |
|-----------------------------|---------|---------------------------------------|
| JUNCTION_MODEL_IGNORE_FPS   | 0.00    | Probability of running a red (0=never)|
| JUNCTION_MODEL_SIGMA_MINOR  | 0.40    | Imperfection at yield junctions       |
| ANTICIPATION_DIST           | 80.0 m  | How far ahead drivers anticipate red  |

Set JUNCTION_MODEL_IGNORE_FPS=0.03 to model 3% red-light running.

#### Acceleration / Deceleration Variation
| Variable        | Default | Effect                                          |
|-----------------|---------|--------------------------------------------------|
| ACCEL_VARIATION | 0.20    | +/-20% variation on base accel per vehicle       |
| DECEL_VARIATION | 0.15    | +/-15% variation on base decel per vehicle       |

#### Emergency Vehicle Yielding
| Variable                | Default | Effect                                      |
|-------------------------|---------|---------------------------------------------|
| OTHER_DRIVER_YIELD_PROB | 0.75    | Probability a vehicle yields to ambulance   |
| YIELD_AWARENESS_DIST    | 50.0 m  | Metres at which drivers hear the siren      |

Set OTHER_DRIVER_YIELD_PROB=0.0 to test pure signal-priority ambulances.
Set to 0.95 for a very compliant road.

#### Traffic Density Pulse (rush-hour simulation)
| Variable      | Default | Effect                                            |
|---------------|---------|---------------------------------------------------|
| PULSE_ENABLED | False   | Set True to enable rush-hour peaks                |
| PULSE_PEAK    | 1.80    | Flow multiplier at peak (1.8 = 80% more vehicles) |
| PULSE_TROUGH  | 0.40    | Flow multiplier at trough (40% of base flow)      |
| PULSE_PERIOD  | 120.0 s | Seconds for one full peak-trough-peak cycle       |

---

### vehicles/vehicle_types.py
Generates 8 distinct driver profiles per vehicle class (32 total + ambulance + VIP).
Each profile has randomised: sigma, tau, minGap, speedFactor, accel, decel,
and all lane-change parameters. This is why no two cars behave the same.

Cars also get a slight blue hue shift per profile so you can see different
driver types in the GUI even within the same vehicle class.

To increase diversity: raise VARIANTS_PER_TYPE (line ~20 in this file).

---

### vehicles/route_generator.py
Assigns each vehicle a random profile variant from vehicle_types.py.
Uses round-robin to ensure all profiles get used evenly, then adds
Poisson-distributed randomness for arrival timing.

If PULSE_ENABLED=True: uses a thinning algorithm to modulate arrival
rates sinusoidally, simulating rush-hour peaks without producing
un-sorted departure times.

---

### tools/priority_manager.py
Called every simulation step. Key behaviours:

Ambulance:
  1. Detects ambulance within DETECT_DIST (60m) of junction
  2. Reads current TL state string length (varies by lane count)
  3. Replaces all signals with G (all green)
  4. Randomly selects OTHER_DRIVER_YIELD_PROB fraction of nearby
     vehicles and slows them to 1 m/s (yielding)
  5. Restores normal programme + vehicle speeds when ambulance clears

Bus: Reads current phase, extends green if in green phase by BUS_EXTEND seconds.
VIP: Reads vehicle edge, maps to phase index, sets TL to that phase.

Edit DETECT_DIST and BUS_EXTEND at the top of this file.

---

## Vehicle Colours

| Class      | Colour        | ID prefix    |
|------------|---------------|--------------|
| Car        | Blue shades   | Car_N        |
| Truck      | Grey shades   | Truck_N      |
| Bus        | Green shades  | Bus_N        |
| Motorcycle | Orange shades | Motorcycle_N |
| Ambulance  | Bright red    | Ambulance_N  |
| VIP Car    | Gold          | VIP_Car_N    |

Cars and trucks have slight colour variation per driver profile.

---

## Suggested Experiments

**Compare ambulance priority vs none:**
Run once with ENABLE_AMBULANCE_PRIORITY=True, once False.
Compare Ambulance_N tripinfo duration in output/trip_info.xml.

**Rush-hour simulation:**
Set PULSE_ENABLED=True, PULSE_PERIOD=120, SIM_DURATION=600.
Watch density waves in the GUI.

**Aggressive vs polite driving:**
Set LC_SPEED_GAIN=0.02, LC_COOPERATIVE=0.4 for aggressive.
Set LC_SPEED_GAIN=0.25, LC_COOPERATIVE=0.9 for polite.
Compare vehicles_waiting column in output/stats.csv.

**Red light running:**
Set JUNCTION_MODEL_IGNORE_FPS=0.05 (5% chance per vehicle).
Watch for collisions in output/trip_info.xml (collision entries).

**Distracted drivers:**
Set TAU_MAX=2.8, CAR_SIGMA_MAX=0.9.
Average network speed will drop noticeably.

---

## Output Files

| File                  | Contents                                              |
|-----------------------|-------------------------------------------------------|
| output/stats.csv      | step, total_vehicles, waiting, mean_speed, tl_phase   |
| output/trip_info.xml  | per-vehicle: depart, arrive, duration, waitingTime    |
| output/summary.xml    | per-step SUMO summary                                 |
| output/detectors.xml  | flow counts from 4 induction loops every 60s          |

```python
import pandas as pd
df = pd.read_csv("output/stats.csv")
df.plot(x="step", y=["mean_speed_ms", "vehicles_waiting"])
```

---

## Troubleshooting

| Problem                       | Fix                                                    |
|-------------------------------|--------------------------------------------------------|
| netconvert not found          | Add SUMO bin/ to PATH                                  |
| SUMO_HOME not set             | See Quick Start                                        |
| traci ImportError             | pip install traci                                      |
| GUI closes immediately        | Run --nogui to see error in console                    |
| Geometry looks wrong          | python run_simulation.py --rebuild                     |
| Want different traffic pattern| Change RANDOM_SEED in traffic.env                      |

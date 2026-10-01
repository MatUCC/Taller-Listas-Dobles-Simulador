# Starling Flock — Advanced Boids Simulation

A modular 3-D flocking simulation built in Python + Ursina. It combines Craig Reynolds-style Boids steering, a forward-cone sensory system, predator/obstacle avoidance, attraction to a feeding area, procedural wind, dynamic lighting, rolling terrain, procedural bird geometry, and an in-game control panel.

## Physics model

The simulated starling is parameterized around a measured European starling: 78 g body mass, 38.2 cm maximum wingspan, 6 cm mean wing chord, and 13.3 Hz mean wingbeat frequency in the cited wind-tunnel study. The code uses these as baseline values rather than pretending that a rigid-body game approximation is a full CFD model.

The aerodynamic update computes dynamic pressure `q = 0.5 * rho * V^2`, lift and drag from coefficient/area terms, flap-phase-dependent lift, procedural thrust, gravity, and wind-relative airspeed. This is an advanced game-scale aerodynamic approximation.

## Project structure

```text
starling_boids_sim/
├── main.py                 # Ursina entry point and input handling
├── config.py               # Central simulation parameters
├── boid.py                 # Starling entity, sensor model, Boids + aerodynamics
├── flock.py                # Population manager + spatial hash + statistics
├── environment.py          # Terrain, trees, rocks, feeding point, predator, wind
├── camera_controller.py    # Orbit/follow camera modes
├── ui.py                   # Sliders, telemetry and interaction controls
├── utils.py                # Shared vector/math helpers
├── requirements.txt        # Python dependency pin
└── assets/                 # Optional future meshes/textures; current birds are procedural
```

## Features mapped to the specification

- 100 initial starlings.
- Separation, alignment and cohesion sliders.
- Predator avoidance and obstacle avoidance.
- Feeding-area attraction.
- Forward-facing field of view and finite perception radius.
- Dynamic wind field with gust/cross-flow components.
- Lift, drag, gravity, flap-phase propulsion and energy budget.
- Procedural wing flapping at the starling baseline wingbeat frequency.
- Rolling terrain generated from analytic height functions.
- Low-poly procedural trees and rocks; additional obstacles can be spawned live.
- Day/night light cycle.
- Telemetry for population, average speed, average energy and nearest predator distance.
- Boids-vector visualization for separation/alignment/cohesion.
- Add/remove birds in real time.
- Orbit camera and individual-bird follow camera.

## Controls

| Key | Action |
|---|---|
| `TAB` | Show/hide UI |
| `C` | Toggle orbit/follow camera |
| `N` | Follow next bird |
| `V` | Toggle Boids vectors |
| `Q / E` | Orbit yaw |
| `R / F` | Orbit pitch |
| Mouse/UI | Adjust sliders and spawn/remove birds |

## Setup — Windows / VS Code

1. Install Python 3.10 or newer.
2. Open the project folder in VS Code.
3. Create a virtual environment:

```powershell
py -3 -m venv .venv
```

4. Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run the project through the Python executable directly or adjust the local execution policy according to your Windows setup.

5. Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

6. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

7. Start the simulation:

```powershell
python main.py
```

## Performance notes

The flock uses a uniform-grid spatial hash rather than comparing every bird against all 99 other birds. With 100 birds this is inexpensive on typical desktop hardware, while preserving headroom for experimentation. The Boids vector visualization intentionally rebuilds its short line objects only while the visualization is enabled.

## Important modeling caveat

This is an interactive simulation, not a scientific validation model. Real starling aerodynamics are unsteady and include wake interactions and detailed wing morphology that require much more sophisticated fluid/rigid-body methods. The implementation keeps the requested aerodynamic variables explicit while remaining practical for a Python/Ursina real-time demonstration.

"""Global simulation configuration.

The values are deliberately centralized so the project can be tuned without
rewriting the simulation systems.
"""
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    # Population / world
    initial_birds: int = 100
    world_size: float = 260.0
    min_altitude: float = 8.0
    max_altitude: float = 70.0

    # Starling physical model (SI units)
    mass_kg: float = 0.078
    wingspan_m: float = 0.382
    wing_area_m2: float = 0.0228
    air_density: float = 1.225
    gravity: float = 9.81
    max_speed: float = 20.0
    min_speed: float = 6.0

    # Aerodynamics
    # Tuned around a cruise condition near 12 m/s; flap phase increases instantaneous CL.
    base_lift_coefficient: float = 0.26
    base_drag_coefficient: float = 0.035
    induced_drag_factor: float = 0.08
    flap_frequency_hz: float = 13.3
    flap_amplitude: float = 0.52
    flap_lift_gain: float = 0.75
    propulsion_gain: float = 0.018
    energy_capacity: float = 100.0
    base_energy_drain: float = 1.15

    # Boids steering weights
    separation_weight: float = 1.65
    alignment_weight: float = 0.75
    cohesion_weight: float = 0.55
    predator_weight: float = 3.4
    obstacle_weight: float = 2.6
    seek_weight: float = 0.45
    wind_weight: float = 0.30

    # Sensory model
    perception_radius: float = 18.0
    vision_fov_deg: float = 220.0
    obstacle_radius: float = 24.0
    predator_radius: float = 75.0

    # Steering / stability
    max_acceleration: float = 7.5
    turn_gain: float = 1.5
    altitude_gain: float = 2.8
    terrain_clearance: float = 7.0

    # Environment
    wind_strength: float = 4.0
    time_scale: float = 0.35
    day_length_seconds: float = 180.0
    fog_density: float = 0.005


DEFAULT_CONFIG = SimulationConfig()

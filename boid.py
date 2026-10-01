"""Starling boid: sensory model, Reynolds steering and aerodynamic flight."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable

from ursina import Entity, Vec3, color, destroy

from config import SimulationConfig
from utils import clamp_vec_length, flatten, safe_normalize, lerp_vec, horizontal_distance


@dataclass
class BoidForces:
    separation: Vec3 = Vec3(0, 0, 0)
    alignment: Vec3 = Vec3(0, 0, 0)
    cohesion: Vec3 = Vec3(0, 0, 0)
    predator: Vec3 = Vec3(0, 0, 0)
    obstacle: Vec3 = Vec3(0, 0, 0)
    seek: Vec3 = Vec3(0, 0, 0)

    @property
    def weighted_debug(self) -> dict[str, Vec3]:
        return {
            "separation": self.separation,
            "alignment": self.alignment,
            "cohesion": self.cohesion,
        }


class StarlingBoid:
    """One simulated starling.

    The flight model is intentionally a game/simulation approximation, but it
    preserves the important aerodynamic relationships: lift and drag scale
    with dynamic pressure and wing area, flap phase changes effective lift and
    thrust, and wind is subtracted from the bird velocity to obtain airspeed.
    """

    def __init__(self, index: int, position: Vec3, config: SimulationConfig):
        self.id = index
        self.cfg = config
        self.position = position
        self.velocity = Vec3(random.uniform(-4, 4), random.uniform(-1, 1), random.uniform(6, 11))
        self.acceleration = Vec3(0, 0, 0)
        self.energy = random.uniform(78, 96)
        self.phase = random.random() * math.tau
        self.alive = True
        self.age = random.random() * 100.0
        self.nearest_predator_distance = 999.0
        self.last_forces = BoidForces()

        self.entity = Entity(model="sphere", scale=(0.35, 0.22, 0.65), color=color.rgb(42, 45, 43), position=position)
        self.left_wing = Entity(parent=self.entity, model="cube", scale=(0.58, 0.035, 0.22), x=-0.30, y=0.02, color=color.rgb(54, 56, 53))
        self.right_wing = Entity(parent=self.entity, model="cube", scale=(0.58, 0.035, 0.22), x=0.30, y=0.02, color=color.rgb(54, 56, 53))
        self.head = Entity(parent=self.entity, model="sphere", scale=0.34, z=0.31, color=color.rgb(47, 49, 46))
        self.beak = Entity(parent=self.head, model="cone", scale=(0.10, 0.24, 0.10), z=0.22, rotation_x=90, color=color.rgb(207, 184, 75))

    def destroy(self) -> None:
        self.alive = False
        destroy(self.entity)

    def sense(self, neighbors: Iterable["StarlingBoid"], predator: Entity, obstacles, feeding_point: Vec3) -> BoidForces:
        forward = safe_normalize(self.velocity)
        separation = Vec3(0, 0, 0)
        alignment_sum = Vec3(0, 0, 0)
        center_sum = Vec3(0, 0, 0)
        count = 0

        cos_half_fov = math.cos(math.radians(self.cfg.vision_fov_deg) * 0.5)
        for other in neighbors:
            if other is self or not other.alive:
                continue
            offset = other.position - self.position
            d = offset.length()
            if d < 1e-5 or d > self.cfg.perception_radius:
                continue
            direction = offset / d
            if forward.dot(direction) < cos_half_fov:
                continue
            count += 1
            separation += (-direction) / max(d, 0.8)
            alignment_sum += safe_normalize(other.velocity)
            center_sum += other.position

        if count:
            avg_velocity = alignment_sum / count
            avg_center = center_sum / count
            alignment = safe_normalize(avg_velocity) - forward
            cohesion = safe_normalize(avg_center - self.position) - forward
        else:
            alignment = Vec3(0, 0, 0)
            cohesion = Vec3(0, 0, 0)

        # Predator sensor uses the same forward-cone principle, with a slightly
        # longer range because escape reactions benefit from early detection.
        predator_force = Vec3(0, 0, 0)
        p_offset = predator.position - self.position
        p_dist = p_offset.length()
        self.nearest_predator_distance = p_dist
        if 0.001 < p_dist < self.cfg.predator_radius:
            p_dir = p_offset / p_dist
            if forward.dot(p_dir) >= cos_half_fov:
                strength = (1.0 - p_dist / self.cfg.predator_radius) ** 2
                predator_force = -p_dir * strength

        obstacle_force = Vec3(0, 0, 0)
        for obstacle in obstacles:
            offset = self.position - obstacle.position
            d = flatten(offset).length()
            if d < self.cfg.obstacle_radius and d > 0.001:
                dir_xz = safe_normalize(flatten(offset), Vec3(1, 0, 0))
                vertical = 0.0
                if self.position.y < obstacle.position.y + obstacle.height + 4:
                    vertical = 1.0
                proximity = (1.0 - d / self.cfg.obstacle_radius) ** 2
                # Obstacles are only relevant when they lie inside the visual cone.
                if forward.dot(safe_normalize(offset, forward)) > math.cos(math.radians(125)):
                    obstacle_force += (dir_xz + Vec3(0, vertical, 0)).normalized() * proximity

        seek_direction = safe_normalize(feeding_point - self.position) - forward
        return BoidForces(separation, alignment, cohesion, predator_force, obstacle_force, seek_direction)

    def integrate(self, dt: float, forces: BoidForces, flock, environment) -> None:
        cfg = self.cfg
        wind = environment.wind.sample(self.position)
        air_velocity = self.velocity - wind
        air_speed = max(0.1, air_velocity.length())
        air_dir = safe_normalize(air_velocity, Vec3(0, 0, 1))
        forward = safe_normalize(self.velocity, Vec3(0, 0, 1))

        # Reynolds-style steering acceleration.
        steering = (
            forces.separation * cfg.separation_weight
            + forces.alignment * cfg.alignment_weight
            + forces.cohesion * cfg.cohesion_weight
            + forces.predator * cfg.predator_weight
            + forces.obstacle * cfg.obstacle_weight
            + forces.seek * cfg.seek_weight
        )

        # Boundary pressure keeps the flock inside the large terrain volume.
        half = cfg.world_size * 0.5
        if self.position.x < -half + 18:
            steering += Vec3(1, 0, 0) * 1.8
        elif self.position.x > half - 18:
            steering += Vec3(-1, 0, 0) * 1.8
        if self.position.z < -half + 18:
            steering += Vec3(0, 0, 1) * 1.8
        elif self.position.z > half - 18:
            steering += Vec3(0, 0, -1) * 1.8

        ground = environment.terrain_height(self.position.x, self.position.z)
        altitude_error = max(0.0, ground + cfg.terrain_clearance - self.position.y)
        if altitude_error > 0:
            steering += Vec3(0, min(3.5, altitude_error * cfg.altitude_gain), 0)
        steering += Vec3(0, (35 - self.position.y) * 0.015, 0)
        steering += wind * cfg.wind_weight * 0.05
        steering = clamp_vec_length(steering, cfg.max_acceleration)

        # Aerodynamics: dynamic pressure q = .5 rho V^2, then lift and drag.
        q = 0.5 * cfg.air_density * air_speed * air_speed
        phase = (self.phase + self.age * cfg.flap_frequency_hz * math.tau) % math.tau
        flap = math.sin(phase)
        downstroke = max(0.0, math.sin(phase))
        cl = cfg.base_lift_coefficient * (1.0 + cfg.flap_lift_gain * downstroke)
        lift_mag = q * cfg.wing_area_m2 * cl
        drag_coeff = cfg.base_drag_coefficient + cfg.induced_drag_factor * (cl * cl)
        drag_mag = q * cfg.wing_area_m2 * drag_coeff

        # World-up lift with a small forward-flow component. Thrust oscillates with flap phase.
        lift_acc = Vec3(0, lift_mag / cfg.mass_kg, 0)
        drag_acc = -air_dir * (drag_mag / cfg.mass_kg)
        # Sustained-flight thrust approximately balances profile/induced drag,
        # while the flap cycle adds a small extra propulsive pulse.
        thrust_mag = drag_mag * 1.10 + cfg.mass_kg * cfg.gravity * cfg.propulsion_gain * downstroke
        thrust_acc = forward * (thrust_mag / cfg.mass_kg)
        gravity_acc = Vec3(0, -cfg.gravity, 0)

        # Energy budget: flap effort costs more at high frequency and when pulling up hard.
        energy_cost = cfg.base_energy_drain + 0.018 * abs(flap) + 0.010 * steering.length() + 0.0015 * air_speed**2
        recovery = 0.08 if air_speed < 11 and downstroke < 0.2 else 0.0
        self.energy += (recovery - energy_cost) * dt
        self.energy = max(0.0, min(cfg.energy_capacity, self.energy))
        fatigue_factor = 0.82 if self.energy < 12 else 1.0

        total_acc = steering * fatigue_factor + lift_acc + drag_acc + thrust_acc + gravity_acc
        self.acceleration = total_acc
        self.velocity += self.acceleration * dt

        speed = self.velocity.length()
        if speed > cfg.max_speed:
            self.velocity = self.velocity.normalized() * cfg.max_speed
        elif speed < cfg.min_speed:
            self.velocity = safe_normalize(self.velocity, Vec3(0, 0, 1)) * cfg.min_speed

        self.position += self.velocity * dt
        self.age += dt
        self._update_visual(dt, flap)

    def _update_visual(self, dt: float, flap: float) -> None:
        self.entity.position = self.position
        speed = max(0.1, self.velocity.length())
        target_forward = safe_normalize(self.velocity)
        self.entity.look_at(self.entity.position + target_forward)
        self.entity.rotation_x = math.degrees(math.atan2(self.velocity.y, max(0.1, flatten(self.velocity).length()))) * -0.28
        self.entity.rotation_z = math.degrees(math.sin(self.age * 3.0) * 0.05)
        wing_angle = 30 + flap * 42
        self.left_wing.rotation_z = wing_angle
        self.right_wing.rotation_z = -wing_angle
        self.left_wing.rotation_x = 8 + flap * 12
        self.right_wing.rotation_x = 8 - flap * 12
        scale = 0.90 + min(0.22, speed / 60)
        self.entity.scale = (0.35 * scale, 0.22 * scale, 0.65 * scale)

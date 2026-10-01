"""Procedural 3-D environment, terrain, obstacles, feeding point and wind."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List

from ursina import Entity, Mesh, Vec3, color, Sky, AmbientLight, DirectionalLight, scene

from config import SimulationConfig
from utils import horizontal_distance


@dataclass
class Obstacle:
    position: Vec3
    radius: float
    height: float
    entity: Entity
    kind: str = "tree"


class WindField:
    """Analytic, time-varying wind field.

    The field combines a base wind direction with smooth spatial oscillations,
    producing gusts and cross-flow without requiring a costly fluid solver.
    """

    def __init__(self, strength: float = 4.0):
        self.strength = strength
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt

    def sample(self, p: Vec3) -> Vec3:
        t = self.time
        gust = math.sin(p.x * 0.018 + t * 0.55) + 0.6 * math.sin(p.z * 0.031 - t * 0.41)
        cross = math.sin((p.x + p.z) * 0.012 + t * 0.32)
        vertical = 0.35 * math.sin(p.x * 0.027 + t * 0.80) * math.cos(p.z * 0.017)
        base = Vec3(0.75, 0.0, 0.25).normalized()
        return base * self.strength + Vec3(cross * self.strength * 0.42, vertical, gust * self.strength * 0.32)


class Environment:
    """Owns terrain geometry, procedural obstacles, lighting and world queries."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.obstacles: List[Obstacle] = []
        self.wind = WindField(config.wind_strength)
        self.clock = 0.35
        self._build_sky_lights()
        scene.fog_color = color.rgb(135, 155, 170)
        scene.fog_density = (45, 220)
        self._build_terrain()
        self._build_landmarks()
        self._spawn_forest(58)
        self._spawn_rocks(22)

    def terrain_height(self, x: float, z: float) -> float:
        """Return smooth rolling-hill terrain elevation."""
        return (
            2.5 * math.sin(x * 0.045) * math.cos(z * 0.037)
            + 1.7 * math.sin((x + z) * 0.072)
            + 0.8 * math.sin(z * 0.15 + 0.8)
        )

    def _build_terrain(self) -> None:
        n = 45
        size = self.config.world_size
        vertices = []
        triangles = []
        for iz in range(n):
            z = -size / 2 + size * iz / (n - 1)
            for ix in range(n):
                x = -size / 2 + size * ix / (n - 1)
                y = self.terrain_height(x, z) - 2.0
                vertices.append((x, y, z))
        for iz in range(n - 1):
            for ix in range(n - 1):
                i = iz * n + ix
                triangles += [(i, i + 1, i + n), (i + 1, i + n + 1, i + n)]
        self.terrain = Entity(
            model=Mesh(vertices=vertices, triangles=triangles),
            color=color.rgb(73, 107, 61),
            scale=1,
        )

    def _build_sky_lights(self) -> None:
        self.sky = Sky()
        self.sun = DirectionalLight(shadows=False)
        self.sun.look_at(Vec3(1, -1, -0.6))
        self.ambient = AmbientLight(color=color.rgba(170, 180, 200, 0.55))

    def _build_landmarks(self) -> None:
        self.feeding_point = Vec3(38, self.terrain_height(38, -15) + 3.0, -15)
        Entity(model="cylinder", scale=(4, 0.15, 4), position=self.feeding_point, color=color.gold)
        Entity(model="cylinder", scale=(2.7, 0.18, 2.7), position=self.feeding_point + Vec3(0, 0.12, 0), color=color.rgba(245, 220, 80, 150))
        self.predator = Entity(model="sphere", scale=1.7, position=(0, 38, -32), color=color.rgb(150, 55, 45))
        Entity(parent=self.predator, model="cone", rotation_x=90, scale=(0.8, 1.2, 0.8), y=0.2, color=color.dark_gray)

    def _spawn_forest(self, count: int) -> None:
        for _ in range(count):
            x = random.uniform(-self.config.world_size / 2 + 10, self.config.world_size / 2 - 10)
            z = random.uniform(-self.config.world_size / 2 + 10, self.config.world_size / 2 - 10)
            if horizontal_distance(Vec3(x, 0, z), self.feeding_point) < 16:
                continue
            y = self.terrain_height(x, z) - 0.5
            h = random.uniform(5.0, 11.0)
            trunk = Entity(model="cube", position=(x, y + h * 0.35, z), scale=(0.7, h * 0.7, 0.7), color=color.rgb(83, 62, 45))
            canopy = Entity(model="sphere", position=(x, y + h * 0.86, z), scale=(3.0, 3.8, 3.0), color=color.rgb(48, 84, 52))
            root = Vec3(x, y, z)
            self.obstacles.append(Obstacle(root, 2.3, h, canopy, "tree"))

    def _spawn_rocks(self, count: int) -> None:
        for _ in range(count):
            x = random.uniform(-self.config.world_size / 2 + 8, self.config.world_size / 2 - 8)
            z = random.uniform(-self.config.world_size / 2 + 8, self.config.world_size / 2 - 8)
            y = self.terrain_height(x, z) + 0.2
            radius = random.uniform(2.0, 5.0)
            e = Entity(model="sphere", position=(x, y + radius * 0.42, z), scale=(radius * 1.6, radius, radius * 1.2), color=color.rgb(92, 91, 82))
            self.obstacles.append(Obstacle(Vec3(x, y, z), radius, radius, e, "rock"))

    def spawn_obstacle(self, position: Vec3 | None = None) -> None:
        if position is None:
            x = random.uniform(-40, 40)
            z = random.uniform(-40, 40)
            position = Vec3(x, self.terrain_height(x, z), z)
        h = random.uniform(5, 10)
        e = Entity(model="sphere", position=position + Vec3(0, h * 0.45, 0), scale=(4, h, 4), color=color.rgb(90, 80, 65))
        self.obstacles.append(Obstacle(position, 3.2, h, e, "spawned"))

    def update(self, dt: float) -> None:
        self.clock = (self.clock + dt * self.config.time_scale / self.config.day_length_seconds) % 1.0
        self.wind.update(dt)
        # A moving raptor-like predator gives the avoidance behavior a live stimulus.
        angle = self.wind.time * 0.10
        self.predator.position = Vec3(42 * math.cos(angle), 38 + 7 * math.sin(angle * 1.7), 42 * math.sin(angle) - 25)
        # Smooth day/night cycle. Avoid hard discontinuities in light intensity.
        sun_angle = self.clock * math.tau
        self.sun.rotation = (35 + 55 * math.sin(sun_angle), -25 + 35 * math.cos(sun_angle), 0)
        intensity = 0.5 + 0.5 * max(0.0, math.sin(sun_angle))
        self.ambient.color = color.rgba(int(95 + 105 * intensity), int(105 + 100 * intensity), int(125 + 90 * intensity), 0.55)

    def nearest_obstacle(self, position: Vec3, radius: float) -> tuple[Obstacle | None, float]:
        best = None
        best_distance = radius
        for obstacle in self.obstacles:
            d = horizontal_distance(position, obstacle.position) - obstacle.radius
            if d < best_distance:
                best, best_distance = obstacle, d
        return best, best_distance

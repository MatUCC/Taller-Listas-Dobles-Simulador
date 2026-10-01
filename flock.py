"""Flock manager with spatial partitioning, population control and statistics."""
from __future__ import annotations

import random
from collections import defaultdict

from ursina import Vec3

from boid import StarlingBoid
from config import SimulationConfig


class SpatialHash:
    """Uniform-grid spatial index reducing neighbor search from O(N²) to local cells."""

    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.cells = defaultdict(list)

    def clear(self) -> None:
        self.cells.clear()

    def _key(self, p: Vec3) -> tuple[int, int, int]:
        s = self.cell_size
        return int(p.x // s), int(p.y // s), int(p.z // s)

    def insert(self, boid: StarlingBoid) -> None:
        self.cells[self._key(boid.position)].append(boid)

    def nearby(self, p: Vec3, radius: float):
        s = self.cell_size
        cx, cy, cz = self._key(p)
        r = int(radius // s) + 1
        result = []
        for x in range(cx - r, cx + r + 1):
            for y in range(cy - r, cy + r + 1):
                for z in range(cz - r, cz + r + 1):
                    result.extend(self.cells.get((x, y, z), ()))
        return result


class FlockManager:
    """Owns all starlings and computes collective state each simulation step."""

    def __init__(self, config: SimulationConfig, environment):
        self.cfg = config
        self.environment = environment
        self.birds: list[StarlingBoid] = []
        self.spatial = SpatialHash(config.perception_radius)
        self.show_vectors = False
        self.vector_entities = []
        self._spawn_initial(config.initial_birds)

    def _spawn_initial(self, count: int) -> None:
        for _ in range(count):
            self.add_bird()

    def add_bird(self) -> StarlingBoid:
        angle = random.random() * 6.2831853
        radius = random.uniform(8, 34)
        pos = Vec3(
            math_cos(angle) * radius,
            random.uniform(22, 42),
            math_sin(angle) * radius,
        )
        boid = StarlingBoid(len(self.birds), pos, self.cfg)
        self.birds.append(boid)
        return boid

    def remove_bird(self) -> None:
        if self.birds:
            boid = self.birds.pop()
            boid.destroy()

    def update(self, dt: float) -> None:
        self.spatial.clear()
        for bird in self.birds:
            if bird.alive:
                self.spatial.insert(bird)

        for bird in list(self.birds):
            if not bird.alive:
                continue
            neighbors = self.spatial.nearby(bird.position, self.cfg.perception_radius)
            forces = bird.sense(neighbors, self.environment.predator, self.environment.obstacles, self.environment.feeding_point)
            bird.last_forces = forces
            bird.integrate(dt, forces, self, self.environment)

    def average_speed(self) -> float:
        if not self.birds:
            return 0.0
        return sum(b.velocity.length() for b in self.birds) / len(self.birds)

    def average_energy(self) -> float:
        if not self.birds:
            return 0.0
        return sum(b.energy for b in self.birds) / len(self.birds)

    def nearest_predator_distance(self) -> float:
        if not self.birds:
            return 0.0
        return min(b.nearest_predator_distance for b in self.birds)

    def center(self) -> Vec3:
        if not self.birds:
            return Vec3(0, 30, 0)
        result = Vec3(0, 0, 0)
        for bird in self.birds:
            result += bird.position
        return result / len(self.birds)


def math_cos(angle: float) -> float:
    import math
    return math.cos(angle)


def math_sin(angle: float) -> float:
    import math
    return math.sin(angle)

"""Orbital and bird-follow camera controller."""
from __future__ import annotations

import math

from ursina import camera, Vec3, held_keys, mouse

from utils import lerp_vec


class CameraController:
    def __init__(self, flock):
        self.flock = flock
        self.mode = "orbit"
        self.target_bird = 0
        self.yaw = -35.0
        self.pitch = 28.0
        self.distance = 62.0
        self.follow_distance = 8.0
        self.follow_height = 3.0

    def toggle_mode(self) -> None:
        self.mode = "follow" if self.mode == "orbit" else "orbit"

    def cycle_target(self) -> None:
        if self.flock.birds:
            self.target_bird = (self.target_bird + 1) % len(self.flock.birds)

    def input(self, key: str) -> None:
        if self.mode == "orbit":
            if key == "scroll up":
                self.distance = max(20, self.distance - 5)
            elif key == "scroll down":
                self.distance = min(110, self.distance + 5)

    def update(self, dt: float) -> None:
        if not self.flock.birds:
            return
        if self.mode == "orbit":
            target = self.flock.center()
            camera.position = lerp_vec(camera.position, target + self._orbit_offset(), min(1, dt * 4))
            camera.look_at(target)
            if held_keys["q"]:
                self.yaw -= 35 * dt
            if held_keys["e"]:
                self.yaw += 35 * dt
            if held_keys["r"]:
                self.pitch = max(8, self.pitch - 25 * dt)
            if held_keys["f"]:
                self.pitch = min(70, self.pitch + 25 * dt)
        else:
            bird = self.flock.birds[self.target_bird % len(self.flock.birds)]
            forward = bird.velocity.normalized() if bird.velocity.length() else Vec3(0, 0, 1)
            desired = bird.position - forward * self.follow_distance + Vec3(0, self.follow_height, 0)
            camera.position = lerp_vec(camera.position, desired, min(1, dt * 7))
            camera.look_at(bird.position + forward * 2.5)

    def _orbit_offset(self) -> Vec3:
        y = math.radians(self.pitch)
        a = math.radians(self.yaw)
        return Vec3(math.sin(a) * math.cos(y), math.sin(y), math.cos(a) * math.cos(y)) * self.distance

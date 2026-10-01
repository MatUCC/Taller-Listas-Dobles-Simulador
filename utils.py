"""Small mathematical helpers shared by simulation systems."""
from __future__ import annotations

import math
import random
from ursina import Vec3, clamp


def clamp_vec_length(v: Vec3, max_length: float) -> Vec3:
    length = v.length()
    if length > max_length and length > 1e-8:
        return v.normalized() * max_length
    return v


def safe_normalize(v: Vec3, fallback: Vec3 = Vec3(0, 0, 1)) -> Vec3:
    if v.length() < 1e-8:
        return fallback
    return v.normalized()


def lerp_vec(a: Vec3, b: Vec3, t: float) -> Vec3:
    t = clamp(t, 0, 1)
    return a + (b - a) * t


def random_unit_3d() -> Vec3:
    v = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
    return safe_normalize(v)


def flatten(v: Vec3) -> Vec3:
    return Vec3(v.x, 0, v.z)


def horizontal_distance(a: Vec3, b: Vec3) -> float:
    return flatten(a - b).length()


def gaussian_noise(seed: float) -> float:
    # Cheap deterministic pseudo-noise used for procedural environmental motion.
    return math.sin(seed * 12.9898) * 0.5 + math.sin(seed * 78.233) * 0.5

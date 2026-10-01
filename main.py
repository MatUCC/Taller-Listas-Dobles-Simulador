"""Entry point for the Starling Flock simulation.

Run with: python main.py
"""
from ursina import Ursina, window, color, held_keys, application, time, Entity, Vec3

from camera_controller import CameraController
from config import DEFAULT_CONFIG
from environment import Environment
from flock import FlockManager
from ui import ControlPanel


app = Ursina(title="Starling Flock — Advanced Boids & Aerodynamics", vsync=True, borderless=False)
window.color = color.rgb(80, 110, 130)
window.fps_counter.enabled = True

config = DEFAULT_CONFIG
environment = Environment(config)
flock = FlockManager(config, environment)
camera_controller = CameraController(flock)
ui = ControlPanel(config, flock, environment, camera_controller)


# Vector visualization uses short line-like cube segments created on demand.
vector_entities = []


def clear_vector_entities():
    global vector_entities
    for e in vector_entities:
        e.enabled = False
    vector_entities.clear()


def draw_vectors():
    clear_vector_entities()
    if not flock.show_vectors:
        return
    # Showing every bird keeps the visualization useful but avoids hundreds of
    # persistent line objects when the toggle is off.
    for bird in flock.birds:
        start = bird.position
        for label, vec, tint in (
            ("separation", bird.last_forces.separation, color.rgb(245, 90, 90)),
            ("alignment", bird.last_forces.alignment, color.rgb(90, 210, 255)),
            ("cohesion", bird.last_forces.cohesion, color.rgb(105, 235, 120)),
        ):
            if vec.length() < 0.01:
                continue
            end = start + vec.normalized() * 4.0
            midpoint = (start + end) * 0.5
            line = Entity(model="cube", color=tint, position=midpoint, scale=(0.035, 0.035, max(0.05, (end - start).length())))
            line.look_at(end, axis="z")
            vector_entities.append(line)


_vector_timer = 0.0
_stats_timer = 0.0


def update():
    global _vector_timer, _stats_timer
    dt = min(0.05, time.dt)
    environment.update(dt)
    flock.update(dt)
    camera_controller.update(dt)

    _stats_timer += dt
    if _stats_timer > 0.10:
        ui.update()
        _stats_timer = 0.0

    if _vector_timer > 0.10:
        if flock.show_vectors:
            draw_vectors()
        else:
            clear_vector_entities()
        _vector_timer = 0.0
    _vector_timer += dt


def input(key):
    camera_controller.input(key)
    if key == "tab":
        ui.toggle()
    elif key == "c":
        camera_controller.toggle_mode()
        ui.follow_button.text = f"Camera: {camera_controller.mode.upper()}"
    elif key == "n":
        camera_controller.cycle_target()
    elif key == "v":
        flock.show_vectors = not flock.show_vectors
        ui.toggle_vectors_button.text = f"Vectors: {'ON' if flock.show_vectors else 'OFF'}"
    elif key == "f1":
        window.fps_counter.enabled = not window.fps_counter.enabled


app.run()
